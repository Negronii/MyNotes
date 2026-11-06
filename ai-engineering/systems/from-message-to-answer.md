# How does an AI chat turn one message into a complete answer? / AI 聊天应用怎样把一条消息变成完整回答？

用户在聊天框里输入 `Why did build 42 fail?`，按下回车。对话里只有构建编号，能解释失败的日志还在另一个服务里。

## What reaches the model after Enter? / 按下回车后，哪些信息会交给模型？

浏览器先把用户消息放进对话，发出包含会话标识和新消息的请求。应用从当前登录会话识别调用者，为这次请求创建运行标识（run ID）`r1`，并随响应交给浏览器。之后即使换了一条连接，浏览器也可以用 `r1` 查询同一次运行的结果。

应用为第一轮推理组装输入。除了用户的问题，还有应用指令、相关的对话历史，以及本轮可用的工具定义。这里的 `read_build_log` 说明它可以按整数 `build_id` 查构建日志。模型现在知道有这个查询入口，日志内容仍由日志服务保管。组装输入时筛选什么信息、把哪些状态留在应用侧，决定了模型这轮实际能看见什么。[每轮推理的上下文](../context/context-engineering-principles.md)

## How does the first inference produce a tool request? / 第一轮推理怎样生成工具请求？

推理服务按模型的输入格式组织角色、消息和工具定义，再由分词器（tokenizer）转换成一列整数 ID。比如用 `tiktoken 0.12.0` 的 `cl100k_base` 单独编码这句提问，可以得到 `["Why", " did", " build", " ", "42", " fail", "?"]`，对应 `[10445, 1550, 1977, 220, 2983, 3775, 30]`。这个例子里的字节级 BPE 会先把文本划为可分别处理的片段，再按训练得到的优先级反复合并相邻字节片段。词元可以包含前导空格。整轮输入的长度 `T` 还要计入角色、历史和工具说明。[分词算法与词表](../foundations/how-llms-work.md#How%20does%20the%20tokenizer%20choose%20token%20boundaries%3F%20/%20%E5%88%86%E8%AF%8D%E5%99%A8%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E8%BE%B9%E7%95%8C%EF%BC%9F)

用一个缩小的仅解码器 Transformer（decoder-only Transformer）跟踪这些 ID。假设词表有 `N` 项，模型宽度为 `8`。嵌入表（embedding table）的形状是 `N × 8`。每个 ID 取表中的一行，`T` 个 ID 便成为 `T × 8` 的初始隐层状态（hidden state）。此后每层仍按位置保留一行向量，并用训练得到的权重更新这些向量。

**注意力（attention）先让位置之间交换信息。** 这层用两个宽度为 `4` 的注意力头。对归一化后的 `T × 8` 输入，每个头用三个 `8 × 4` 的矩阵分别投影出 `Q`、`K`、`V`，三个结果都是 `T × 4`。位置也参与匹配。例如旋转位置编码（RoPE）在打分前按词元位置旋转 Q 和 K。[Transformer §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) · [RoFormer §3](https://arxiv.org/abs/2104.09864)

因果掩码让一个位置只看到自身和更早的词元。当前位置的查询（query）跟各个可见位置的键（key）做点积，除以 `√4` 后沿键的位置做 softmax，再按所得权重对值（value）做加权求和。两个头可以在不同的特征空间里给前文不同权重，各得到一个 `T × 4` 的结果。沿特征维拼成 `T × 8`，乘 `8 × 8` 的输出投影混合各头的特征，再通过残差连接加回原状态。[多头注意力的矩阵推导](../foundations/how-llms-work.md#How%20do%20Q%2C%20K%2C%20and%20V%20produce%20the%20attention%20update%3F%20/%20Q%E3%80%81K%E3%80%81V%20%E6%80%8E%E6%A0%B7%E4%BA%A7%E7%94%9F%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F)

**前馈网络（feed-forward network，FFN）再变换每个位置里的特征。** 归一化后的输入仍是 `T × 8`。以 SwiGLU 为例，两个 `8 × 16` 的投影分别产生候选值和门控输入。门控一路经过 SiLU 后与候选值逐元素相乘，再用 `16 × 8` 的投影把结果变回 `T × 8`，加回残差状态。例如一个门控通道的输入是 `0`，这个通道对应的候选值这次就乘以 `0`。[Shazeer, GLU Variants §2](https://arxiv.org/html/2002.05202#S2)

注意力可以把 `build` 和 `42` 的线索汇到同一个位置，FFN 便可以根据这组特征的组合调整写回这一行的内容。每个位置使用同一组本层 FFN 权重，各自变换。注意力和 FFN 完成一个 Transformer 层的两次更新，后续层继续更新这份状态。这些更新最终会影响模型对接下来词元的打分。[FFN 与层堆叠](../foundations/how-llms-work.md#What%20does%20the%20FFN%20add%2C%20and%20how%20do%20blocks%20stack%3F%20/%20FFN%20%E5%A2%9E%E5%8A%A0%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B1%82%E6%80%8E%E6%A0%B7%E5%A0%86%E5%8F%A0%EF%BC%9F)

第一遍处理整段输入叫预填充（prefill）。模型用最后一个位置的输出向量预测第一个新词元。语言模型输出头（LM head）的 `8 × N` 投影给词表上每个候选 ID 打分，得到一行 logits。解码规则可以选最高分，也可以从分数导出的概率分布里采样。选出的 ID 追加到序列，成为下一步要处理的新位置。

进入增量解码（incremental decoding）后，每层的新查询仍要给旧位置打分并取它们的值，因此同一前缀各层的 K 和 V 可以复用。旧位置的查询早已用于计算各自的输出，后续新位置用的是自己的 Q。解码循环直到遇到结束信号或达到输出上限。这也适用于生成工具请求的第一轮。[解码与 KV 缓存](llm-serving-and-kv-cache.md) · [Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation)

这次生成结束时，模型接口交给应用一条结构化工具请求（tool request）。工具是 `read_build_log`，参数为 `build_id=42`，调用标识为 `c1`。`r1` 标识整次聊天运行，`c1` 只标识其中这一次工具调用。应用拿到的是一次要执行的查询，到了这一步才开始准备读取日志。[OpenAI 的工具调用生命周期](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) · [Claude 的应用端工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools)

## How does the tool request become evidence? / 工具请求怎样变成证据？

应用的运行时（harness）先确认 `read_build_log` 属于当前允许的工具，并检查参数确实是整数构建编号。随后根据应用已识别的用户检查能否读取构建 `42`。格式正确只说明运行时理解了这条请求。真正读取的是应用，访问权限按当前用户和目标资源判定，即使这个工具只有读操作。[工具契约与授权检查](../agents/tool-design-and-function-calling.md)

权限通过后，日志服务返回构建 `42` 的失败记录。运行时从中挑出与问题相关的片段，并把结果附到调用 `c1` 上。

| 来自同一条日志的字段 | 返回给模型的值 |
| --- | --- |
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 失败断言 | 空名称请求预期返回 `400`，实际返回 `200` |
| 测试进程退出状态 | `1` |

如果读取被拒绝，运行时可以把错误作为 `c1` 的结果送回，模型就能解释这次拿不到证据。若用户已经把同一段日志贴进消息，证据在第一轮就可用，可以省掉这次外部读取。证据若需要从一批文档中找，则可以在推理前或工具执行时先检索调用者有权使用的段落。[检索与证据的适用范围](../rag/rag-architecture-and-implementation.md)

## What changes in the second inference? / 第二轮推理多看到了什么？

运行时发起下一轮推理。这次输入需要保留原问题、模型此前提出的调用，以及标着 `c1` 的工具结果。调用标识把新证据与请求它的动作接起来。模型仍按相同方式逐词元解码，只是现在能根据日志解释测试为什么失败。如果结果还不足以回答，它可以提出下一次工具请求，由运行时继续同样的校验和执行流程。[动作、观察与下一步决策](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

~~~mermaid
sequenceDiagram
    participant Browser
    participant App as Chat application
    participant Model
    participant Logs as Build log store
    Browser->>App: Submit question about build 42
    App->>Model: Question and available tools
    Model-->>App: Tool request c1 for build 42
    App->>App: Validate c1 and authorize the read
    App->>Logs: Read build 42
    Logs-->>App: Test expected 400, got 200
    App->>Model: Question, previous call and result c1
    loop Answer text arrives
        Model-->>App: Answer text delta
        App-->>Browser: Text delta for r1
    end
    App-->>Browser: Complete r1
~~~

## When is the answer visible and complete? / 回答什么时候出现在屏幕上，什么时候算完成？

模型接口交付可用的文本增量（text delta）后，应用把它转成浏览器能识别的事件。一个应用事件可以包含多个词元解码后的文本。浏览器从 HTTP 响应里增量解码字节、拼出完整事件，再把文本追加到 `r1` 的回答。网络读到的块可以只覆盖半个事件。比如采用服务端发送事件（SSE）时，浏览器按空行识别事件边界。界面框架随后提交 DOM 更新，浏览器按需布局、绘制和合成，用户在某个新帧里看到增加的文字。[SSE 的事件解析](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream) · [界面更新怎样变成像素](../../frontend/html-css/rendering-pipeline-and-forced-layout.md)

这次运行的浏览器事件可以长成下面这样。应用在确认模型正常结束并保存最终回答后，发送自己的完成事件。

| `r1` 的事件顺序 | 浏览器拿到的内容 |
| --- | --- |
| `1 · delta` | 第 42 次构建在 `unit-tests` 步骤失败。 |
| `2 · delta` | `reject_empty_name` 期望空名称请求返回 `400`，实际返回 `200`，测试进程以 `1` 退出。 |
| `3 · complete` | 确认 `r1` 的回答已完成。 |

浏览器在收到第 2 个事件时就可以显示这段解释，在收到第 3 个事件时才把回答标记为完成。若连接恰好在两者之间断开，界面保留已显示的文本，并用 `r1` 查询服务端保存的状态和结果。这里最终能解释的是哪项测试失败以及它观察到的行为差异。进一步定位到实现还是测试预期，需要相应的代码或测试证据。[流式界面的终态与断线恢复](../../frontend/browser-apis/streaming-ux.md) · [服务端如何保存和恢复同一次运行](ai-application-architecture.md)
