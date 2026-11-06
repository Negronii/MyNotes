# How does an AI service turn one message into a complete answer? / AI 服务怎样把一条消息变成完整回答？

AI 服务收到 `Why did build 42 fail?`。用户给出了构建编号，失败记录保存在日志服务里。应用把这次运行记为 `r1`。

~~~mermaid
flowchart TD
    Input["1 组装输入 / Prepare input<br/>问题 + 工具定义"]
    Model["2 模型推理 / Inference<br/>词元 → 隐层状态 → 生成输出"]
    Choice{"运行时收到工具请求？"}
    Tool["3 运行工具 / Execute tool<br/>授权并读取构建 42"]
    Context["4 更新上下文 / Add observation<br/>把 c1 的结果交回模型"]
    Answer["5 交付回答 / Return answer<br/>保存文本和运行结果"]
    Input --> Model --> Choice
    Choice -->|工具请求 c1| Tool
    Tool -->|结果或错误| Context
    Context -->|同一个 r1，下一轮推理| Model
    Choice -->|本轮正常结束并给出答案| Answer
~~~

## 1. Prepare the model input / 组装模型输入

应用运行时（harness）保存 `r1` 和调用者身份，再为第一轮推理选取信息。这个例子里没有需要带入的历史消息，模型先看到下面三样东西。

| 第一轮输入 | 在 `r1` 中的内容 |
| --- | --- |
| 应用指令 | 根据可用证据解释构建失败。 |
| 用户消息 | `Why did build 42 fail?` |
| 工具定义 | `read_build_log` 接收整数 `build_id`，返回构建日志中的失败记录。 |

工具定义告诉模型可以请求什么，实际日志要等应用查询后才会出现。应用保存的调用者身份用于工具授权。在更长的对话里，应用还需要选择哪些历史和证据值得放进下一轮。[每轮推理应该看到哪些信息](../context/context-engineering-principles.md)

## 2. Run inference and generate a tool request / 推理生成工具请求

推理服务按模型的输入格式组织消息和工具定义，再由分词器（tokenizer）转成一列整数 ID。用 `tiktoken 0.12.0` 的 `cl100k_base` 单独编码这句提问，得到 `["Why", " did", " build", " ", "42", " fail", "?"]`，对应 `[10445, 1550, 1977, 220, 2983, 3775, 30]`。这里的字节级 BPE 按训练得到的优先级反复合并相邻片段，所以一个词元可以包含前导空格。下面的 `T` 表示模型收到的整个序列的长度，包含角色、消息和工具说明。[分词算法与词表](../foundations/how-llms-work.md#How%20does%20the%20tokenizer%20choose%20token%20boundaries%3F%20/%20%E5%88%86%E8%AF%8D%E5%99%A8%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E8%BE%B9%E7%95%8C%EF%BC%9F)

用一个宽度为 `8` 的缩小版仅解码器 Transformer（decoder-only Transformer）看中间状态。假设词表有 `N` 项，嵌入表（embedding table）的形状是 `N × 8`。查表时，`42` 对应的 ID `2983` 取索引为 `2983` 的行。把序列里的每个 ID 都查一遍，得到 `T × 8` 的初始隐层状态（hidden state）。之后每层仍为每个位置保留一行向量，以下选用户消息中问号所在的一行演示层内计算。

~~~mermaid
flowchart TD
    X["构建 42 的输入状态<br/>T × 8，每个词元一行"]
    H1["注意力头 1 / Head 1<br/>Q、K、V 各 T × 4<br/>加权输出 T × 4"]
    H2["注意力头 2 / Head 2<br/>Q、K、V 各 T × 4<br/>加权输出 T × 4"]
    A["沿特征维拼接 → 投影<br/>T × 8，加回输入状态"]
    F["前馈网络 / FFN<br/>候选值和门控各 T × 16<br/>逐元素相乘"]
    Y["投影回 T × 8<br/>加回注意力更新后的状态"]
    X --> H1 & H2
    H1 & H2 --> A
    A --> F --> Y
~~~

**注意力（attention）先在位置之间传递信息。** 归一化后的 `T × 8` 输入，在每个头里分别乘三个 `8 × 4` 的矩阵，得到形状均为 `T × 4` 的查询（Q）、键（K）和值（V）。若采用旋转位置编码（RoPE），模型在算分前按位置旋转 Q 和 K。某一行用自己的 Q 与可见位置的 K 做点积，除以 `√4`，再用 softmax 得到权重。因果掩码先屏蔽未来位置，因此问号所在的行能读取前面的 `build` 和 `42`。[注意力的矩阵推导](../foundations/how-llms-work.md#How%20do%20Q%2C%20K%2C%20and%20V%20produce%20the%20attention%20update%3F%20/%20Q%E3%80%81K%E3%80%81V%20%E6%80%8E%E6%A0%B7%E4%BA%A7%E7%94%9F%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F) · [Transformer §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) · [RoFormer §3.2](https://arxiv.org/html/2104.09864v5#S3.SS2)

在问号这一行，简化成只对 `build` 和 `42` 两处求和。假设某个头给它们的权重是 `0.25`、`0.75`，两个 V 分别是 `(1, 0, 0, 0)` 和 `(0, 2, 0, 0)`，则该头在这一行的输出为 `(0.25, 1.5, 0, 0)`。两个头分别计算，每个位置得到两条宽度为 `4` 的结果。沿特征维拼成宽度 `8`，再用 `8 × 8` 的输出矩阵混合特征，最后把这次更新加回各位置的原向量。

**前馈网络（feed-forward network，FFN）接着在每一行内部变换特征。** 注意力已经把与构建和编号相关的信息写进问号的向量。以 SwiGLU 为例，归一化后的 `T × 8` 状态经过两个 `8 × 16` 投影，分别生成候选值和门控输入。对问号这一行，假设其中一个候选通道是 `3`，对应的门控输入是 `1`。SiLU 把 `1` 变成约 `0.73`，相乘后这一通道约为 `2.19`。门控由当前行里的特征共同决定，所以同一个 FFN 能根据上下文写回不同内容。用 `16 × 8` 的下投影把结果变回 `T × 8`，再加到注意力更新后的状态，交给下一个 Transformer 层。[FFN 与层堆叠](../foundations/how-llms-work.md#What%20does%20the%20FFN%20add%2C%20and%20how%20do%20blocks%20stack%3F%20/%20FFN%20%E5%A2%9E%E5%8A%A0%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B1%82%E6%80%8E%E6%A0%B7%E5%A0%86%E5%8F%A0%EF%BC%9F) · [GLU Variants §2](https://arxiv.org/html/2002.05202#S2)

第一遍处理整段输入叫预填充（prefill）。预测首个新词元时，语言模型输出头（LM head）取完整格式化输入最后一个位置的最终隐层向量。输入模板决定这个位置是什么，例如模板可能在消息后追加一个回复起始标记。输出头用 `8 × N` 的矩阵为词表里的每个 ID 打分，得到 logits。解码可以选最高分，也可以把分数转成概率后采样。[聊天模板的回复起始标记](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)

选出的 ID 追加到序列，再用新位置的输出预测下一枚词元。带因果掩码的模型可以缓存各层旧位置的 K、V，因为新位置仍要读取它们。旧位置的 Q 已完成各自的计算，这一步用的是新位置的 Q。[解码与 KV 缓存](llm-serving-and-kv-cache.md) · [Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation)

这次，模型按工具调用格式生成了工具名和参数。推理接口识别出完整调用，把它作为带有调用标识的结构化项交给运行时。应用收到的内容可以写成 `tool_call(c1, read_build_log, {build_id: 42})`。运行时看到这是一次工具请求，进入图中的工具分支。[OpenAI 工具调用流程](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) · [Claude 应用端工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools)

## 3. Execute the tool and collect evidence / 执行工具并取得证据

运行时接到 `c1`，确认工具可用且参数是整数，再按 `r1` 的调用者身份检查对构建 `42` 的读取权限。格式校验确认运行时能按工具定义解析请求，授权检查决定当前用户能读取哪些资源。即使是只读工具，日志也必须在授权通过后才取出。[工具契约与授权检查](../agents/tool-design-and-function-calling.md)

读取成功后，运行时把与问题相关的日志附在 `c1` 的结果里。`r1` 贯穿整次回答，`c1` 用来把这条观察对应到具体调用。

| `c1` 的工具结果 | 从构建 `42` 的日志读到的值 |
| --- | --- |
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 失败断言 | 空名称请求预期返回 `400`，实际返回 `200` |
| 退出状态 | `1` |

如果权限检查失败，运行时可以为 `c1` 返回读取失败的结果。下一轮模型便能说明证据为何不可用。这个例子按已知编号查一份日志。如果问题需要在一组文档里寻找相关段落，证据获取环节可以使用[检索增强生成（RAG）](../rag/rag-architecture-and-implementation.md)。

## 4. Feed the observation back to the model / 把观察交回模型

下一轮仍处理 `r1`。在原有输入的基础上，应用带入模型提出的 `tool_call(c1, …)` 和工具返回的 `tool_result(c1, …)`。前者记录要查什么，后者把该调用实际读到的 `unit-tests`、`400` 与 `200` 带入这次推理。日志内容这时才被编码成模型输入，模型使用相同的推理机制和已训练的权重生成回答。如果证据不足以回答，模型也可以再提出一次查询，由运行时重复校验、执行与回填。[动作、观察与下一步决策](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

如果用户一开始就贴出了足够的日志，证据可以直接进入第一轮输入，图里的工具循环可以省去。这个例子中，日志已经在第二轮提供了足够证据，模型给出最终文本。

## 5. Finish the run and return the answer / 结束运行并交付回答

> 第 42 次构建在 `unit-tests` 步骤失败。`reject_empty_name` 期望空名称请求返回 `400`，实际返回 `200`，测试进程以 `1` 退出。要进一步定位原因，需要核对请求校验逻辑和测试预期。

第一轮模型结束时，交出的是 `c1`，应用还有查询要做。第二轮正常结束并给出最终文本后，应用把答案和完成状态保存到 `r1`，再向调用方交付结果。若接口边生成边发送文本，运行记录仍要以应用确认的最终结果为准。[服务端的运行状态与恢复](ai-application-architecture.md)
