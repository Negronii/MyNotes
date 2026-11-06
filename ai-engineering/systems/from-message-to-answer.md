# AI 服务如何将一条消息变成完整回答？

## 案例：解释一次构建失败

想象一位开发者正在使用一款接入构建系统的 AI assistant (AI 助手)。构建系统会对一次代码改动运行自动检查，而构建 `42` 失败了。开发者问：`Why did build 42 fail?` 失败详情保存在日志服务中，助手可以通过名为 `read_build_log` 的 tool (工具) 查询。

助手需要取回这些证据并解释日志说明了什么。我们将沿着这个问题走过整个服务流程，从准备模型输入，到返回一份以日志为依据的回答。应用负责管理日志服务的访问；模型先生成获取证据的请求，再利用证据生成说明。这是一个虚构的、由应用管理的 tool-call loop (工具调用循环) 示例。

下图展示成功完成的情形。本次运行包含两次模型调用：第一次生成工具请求；应用读取日志后，第二次生成回答。如果另一个问题本身已经包含足够证据，模型也可以在第一次调用时直接回答。

~~~mermaid
flowchart TD
    Input["1 准备输入<br/>问题 + 指令 + 工具定义"]
    Model["2 运行模型<br/>生成下一段输出"]
    Choice{"模型返回了什么？"}
    Tool["3 执行工具<br/>检查访问权限，然后读取构建 42"]
    Context["4 更新输入<br/>加入调用及其结果"]
    Answer["5 完成本次运行<br/>保存并返回说明"]
    Input --> Model --> Choice
    Choice -->|工具请求| Tool
    Tool -->|日志证据或错误| Context
    Context -->|下一次模型调用| Model
    Choice -->|最终回答| Answer
~~~

## 1. 准备模型可见的内容

harness 是负责协调模型与工具的应用代码。它记录调用者身份、为模型选择信息、执行工具，并决定应用何时有结果可返回。本例中的第一次模型调用有三项输入。

| 输入 | 本例中的内容 |
| --- | --- |
| 应用指令 | 根据现有证据解释构建失败。 |
| 用户消息 | `Why did build 42 fail?` |
| 工具定义 | `read_build_log` 接受整数 `build_id`，并返回构建日志中的失败记录。 |

> [!tip] 指令、对话与外部状态
> 每次模型调用都会收到经过选择的输入。模型不会自动看到日志服务、应用数据库，或用户此前说过的所有内容。应用必须提供这些信息，或执行能取回信息的工具。

工具定义描述了一个可用操作。只有应用取回日志后，日志内容才会进入对话。应用会保留调用者身份，用于权限检查。

这些输入构成了本次调用的模型 context (上下文)。在较长的对话中，应用还需要决定包含哪些较早的消息和证据。这个选择很重要，因为模型只能依据实际提供的信息，以及训练参数中编码的知识来生成输出。[如何为每次模型调用选择信息](../context/context-engineering-principles.md)

## 2. 生成请求以获取缺失证据

现在，模型拿到了问题，也有办法请求日志。在 inference (推理) 过程中，它处理这些输入，并一次生成一个 token (词元)。本次运行中，输出指定调用 `read_build_log`，并将 `build_id` 设为 `42`。

一系列数值运算如何生成这样的请求？我们可以沿着一个简化的 decoder-only Transformer (仅解码器 Transformer) 中的变换过程来观察。下面的小型维度和数值只用于说明计算过程，并非模型回答这个问题时的实测数据。

服务先格式化问题、指令和工具定义，再由 tokenizer (分词器) 将其转换为整数 ID。使用 `tiktoken 0.12.0` 和 `cl100k_base` 编码 `Why did build 42 fail?` 这句话，会得到七个片段 `["Why", " did", " build", " ", "42", " fail", "?"]`，对应 ID `[10445, 1550, 1977, 220, 2983, 3775, 30]`。完整输入还包含其他消息和格式标记。

embedding table (嵌入表) 会把每个 ID 映射为一个 vector (向量)。在连续的 Transformer 层中，attention (注意力) 从可见位置收集信息，而 feed-forward network (前馈网络，简称 FFN) 会变换每个位置上的特征。这些运算共同更新 hidden state (隐藏状态)，也就是模型对本次特定输入的数值表示。

> [!tip] 这里变换的是什么？
> vector 是一个有序数值列表。若有 `T` 个 token 位置，每个位置有八个特征，hidden state 的形状就是 `T × 8`。每一行对应一个位置。模型学到的权重会变换这些特征；信息在位置之间传递时，各行仍与原来的位置对应。

经过最后一层后，language model head (LM head，语言模型头) 使用最后一个输入位置的状态为词表条目打分。decoding (解码) 会选出一个 token，将其追加到输入中，再重复预测。KV cache (键值缓存) 让后续步骤复用先前位置的 Key 和 Value；attention 在收集信息时会读取这些表示。新位置仍然需要单独计算。这个循环可以生成普通文本，也可以生成编码结构化工具请求的 token。

如果模型提供 temperature (温度) 设置，它会改变 token 采样分布的集中程度，但不能证明结果正确。[应用应如何选择解码设置？](../foundations/how-llms-work.md#%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E8%A7%A3%E7%A0%81%E8%AE%BE%E7%BD%AE%EF%BC%9F) 会通过特定任务的评估来分析这个选择。下方可以查看模型调用背后的数值步骤，也可以在本次服务运行结束后，按顺序阅读模型章节。

> [!example]- 本次模型调用的内部过程：一个小型 tensor (张量) 示例
> **将输入转换为 token ID 和 vector**
>
> inference service (推理服务) 会为模型格式化消息和工具定义。tokenizer 会把格式化后的输入转换为整数 ID。具体来说，使用 `tiktoken 0.12.0` 和 `cl100k_base` 编码 `Why did build 42 fail?`，会得到以下片段和 ID。
>
> | Token 片段 | Token ID |
> | --- | --- |
> | `"Why", " did", " build", " ", "42", " fail", "?"` | `10445, 1550, 1977, 220, 2983, 3775, 30` |
>
> 这个 tokenizer 会对字节序列应用 byte pair encoding (字节对编码)，简称 BPE：它按照学到的合并优先级，反复合并相邻片段。一个片段可能以空格开头。完整模型输入还包含指令、工具说明和格式标记。令 `T` 表示整个序列的长度。[token 边界是如何确定的](../foundations/how-llms-work.md#%E5%88%86%E8%AF%8D%E5%99%A8%E5%A6%82%E4%BD%95%E5%88%92%E5%88%86%E8%AF%8D%E5%85%83%E8%BE%B9%E7%95%8C%EF%BC%9F)
>
> embedding table 会为每个 ID 查找一个学到的 vector。设词表大小为 `N`，并将模型宽度刻意设为较小的 `8`，那么该表的形状为 `N × 8`。例如，ID `2983` 会选中索引为 `2983` 的行。查找全部 ID 后，就会得到形状为 `T × 8` 的 hidden state，每个位置占一行。后续层会结合上下文更新这些行。每行的八个坐标都是学到的特征值，并非为某个词义预先标注的槽位。
>
> **提醒：如何阅读 `T × 8` 这样的形状**
> `T` 表示 token 位置数，`8` 表示每个位置的特征数。一行是一个 vector，也就是由八个数字组成的有序列表。将它变成 `T × 4`，表示保留相同的位置，并为每个位置计算四个新特征。
>
> **让每个位置收集相关信息**
>
> attention 让一个位置能够从其他可见位置收集信息。本例中的两个 attention head (注意力头) 各自接收经过 normalization (归一化) 的 `T × 8` 状态，并用三个学到的 `8 × 4` 投影矩阵生成 Query (查询)、Key (键) 和 Value (值)，简称 Q、K、V。每个结果矩阵的形状都是 `T × 4`。normalization 会在投影前缩放每一行，控制其数值大小，同时保持形状不变。
>
> **提醒：这里的矩阵乘法意味着什么**
> dot product (点积) 会将对应坐标相乘后求和，例如 `[2, 3] · [4, 5] = 23`。将一行宽度为 `8` 的 vector 乘以一个 `8 × 4` 矩阵，相当于对权重矩阵的每一列分别计算一个 dot product，最终得到四个数。每一列学到的权重都定义了对输入特征的不同加权组合。
>
> 使用 rotary position embedding (旋转位置编码)，简称 RoPE 时，Q 和 K 会先按照位置旋转。对于一个位置，用它的 Q 与各位置的 K 分别计算 dot product，再除以 `√4`。causal mask (因果掩码) 会排除位于当前查询位置右侧的位置。softmax 会对这些分数取指数，再用每个结果除以它们的总和。分数为 `[1, 0]` 时，结果约为 `[0.731, 0.269]`。这些权重之和为一，并决定各个可见 V 对结果的贡献比例。这里用 Q 与 K 比较得到的是一对位置之间的相关性分数；这与通过学到的权重矩阵投影特征时使用的 dot product 不同。[QKV 的计算过程](../foundations/how-llms-work.md#Q%E3%80%81K%E3%80%81V%20%E5%A6%82%E4%BD%95%E7%94%9F%E6%88%90%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F)
>
> 下面用一组独立的权重演示 V 的加权求和，不沿用上面的 softmax 数值。取用户消息中问号所在的那一行，只保留 `build` 和 `42`，并分别赋予权重 `0.25` 和 `0.75`。如果它们的 V vector 分别是 `(1, 0, 0, 0)` 和 `(0, 2, 0, 0)`，加权结果就是 `(0.25, 1.5, 0, 0)`。
>
> 每个 head 都会单独计算。在每个位置，将两个宽度为 `4` 的结果拼接成宽度为 `8` 的 vector，再通过一个 `8 × 8` 的输出投影进行混合。residual connection (残差连接) 会逐坐标将这个更新加到输入状态上。例如，`[1, 2]` 加上更新量 `[0.1, −0.2]`，结果是 `[1.1, 1.8]`。宽度相同，才能让每一层细化已有表示。结果仍为 `T × 8`，但现在已汇集了不同位置的信息。
>
> **在每个位置内变换信息**
>
> 接着，FFN 使用共享的学到的权重，独立变换每一行。attention 已将上下文信息带入某一行；FFN 可以用非线性方式组合这些特征，再将更新写回该行。
>
> 在这个小型模型中使用 SwiGLU 时，两个 `8 × 16` 投影会对 normalization 后的状态进行投影，分别产生候选值和门控输入。SiLU 会按照 `1 / (1 + exp(−x))` 平滑缩放门控输入 `x`。所得结果与对应的候选坐标相乘。这种 element-wise multiplication (逐元素乘法) 会保持 `T × 16` 的形状，不像 dot product 那样对坐标求和。假设问号所在行的一个候选通道为 `3`，门控输入为 `1`。SiLU 会将 `1` 转换为约 `0.73`，因此该通道的结果约为 `2.19`。接着，`16 × 8` 的降维投影会将结果还原到模型宽度，再通过 residual connection 将它加到 attention 生成的状态上。门控取决于当前行，因此相同的学到的权重会根据不同上下文产生不同更新。门控值是连续的，所以这里的“门”并不表示二元开关。[FFN 如何补充信息，以及层如何堆叠](../foundations/how-llms-work.md#FFN%20%E5%A2%9E%E5%8A%A0%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%8C%E5%A4%9A%E4%B8%AA%E5%9D%97%E5%A6%82%E4%BD%95%E5%A0%86%E5%8F%A0%EF%BC%9F)
>
> 一个 Transformer 层会将 attention 和 FFN 操作与 normalization、residual connection 组合起来。每一层会把形状为 `T × 8` 的输出传给下一层，下一层有自己学到的参数。下图沿着本例的一层追踪形状变化，包括每个子层之前的 normalization。
>
> ~~~mermaid
> flowchart TD
>     X["层输入<br/>T × 8，每个 token 一行"]
>     Norm["为 attention 归一化<br/>T × 8"]
>     H1["attention head 1<br/>Q、K、V 均为 T × 4<br/>加权输出 T × 4"]
>     H2["attention head 2<br/>Q、K、V 均为 T × 4<br/>加权输出 T × 4"]
>     A["拼接后投影<br/>T × 8"]
>     R["将 attention 更新加到层输入<br/>T × 8"]
>     F["经过 normalization 后执行 SwiGLU FFN<br/>两个 T × 16 分支<br/>门控、相乘，再投影为 T × 8"]
>     Y["加入 FFN 更新<br/>T × 8，传给下一层"]
>     X --> Norm
>     Norm --> H1 & H2
>     H1 & H2 --> A --> R
>     X -->|残差 Residual| R
>     R --> F --> Y
>     R -->|残差 Residual| Y
> ~~~
>
> **将最终状态转换为输出 token**
>
> 处理初始输入的过程称为 prefill (预填充)。在本例中，经过最后一层和最终 normalization 后，LM head 会取完整格式化输入最后一个位置的 vector，预测第一个新 token。causal attention (因果注意力) 允许这个位置关注整个已提供的前缀；该位置也可能是输入模板添加的 assistant 起始标记。
>
> LM head 会将这个宽度为 `8` 的 vector 乘以一个 `8 × N` 矩阵，得到 logits (未归一化分数)，每个词表条目对应一个分数。decoding 会选择一个 ID：可以取分数最高的 ID，也可以根据这些分数构造出的概率分布进行采样。对于提供 temperature 设置的模型，较低的值会让分布更集中，较高的值则会让它更分散。这些概率描述的是 token 的选择过程，并不表示最终回答的真实性。[应用应如何选择解码设置？](../foundations/how-llms-work.md#%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E8%A7%A3%E7%A0%81%E8%AE%BE%E7%BD%AE%EF%BC%9F) 会将这个机制与智能体行为的受控对比联系起来。选出的 ID 会被追加到序列中，模型再从新位置开始预测下一个 ID。
>
> KV cache 会在每一层保留先前位置的 K 和 V。在新位置，模型计算 Q、K、V，再用这个 Q 关注缓存中的 K/V 和新位置自己的 K/V。随后，新位置的 K/V 会追加到缓存中，供后续步骤使用。先前位置的 Q vector 已经用于各自的计算，本步骤不需要它们。[解码与 KV cache](llm-serving-and-kv-cache.md)

针对构建问题，这次生成会按照模型的 tool-call 格式 (工具调用格式) 产生工具名和参数。inference service 会根据模型的 tool-call protocol (工具调用协议) 解释生成的 token，并将完整的工具名和参数作为结构化 API 条目提供给应用。用简化记法表示，应用会收到 `tool_call(c1, read_build_log, {build_id: 42})`。ID `c1` 会把工具结果与这次特定请求关联起来。当有多个待处理调用时，这种对应关系很重要，模型才能知道哪条观察结果属于哪个请求。harness 会将拟议的调用交给校验流程，从而进入总览图中的工具分支。接下来的步骤会说明执行前的检查。

## 3. 执行请求并读取日志

应用会检查 `read_build_log` 是否可用、`build_id` 是否为所需的整数类型，以及调用者是否有权读取构建 `42`。参数校验确保请求可以被正确解释。authorization (授权) 则确定调用者可以访问哪个资源。只有这些检查全部通过后，应用才会读取日志。如果工具会改变外部状态，例如重启构建，那么重试时还需要考虑前一次尝试是否已经生效。[工具契约与授权](../agents/tool-design-and-function-calling.md)

取回的结果包含模型此前缺少的证据。

| `c1` 的结果字段 | 构建 `42` 的值 |
| --- | --- |
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 失败断言 | 空名称请求应返回 HTTP `400`，但实际返回了 `200`。 |
| 进程退出状态 | `1` |

如果 authorization 失败，应用可以为 `c1` 返回失败结果，让模型在下一次调用时说明无法获取证据。本例中，工具按照 ID 查询一条已知日志。如果问题需要在大量文档中查找相关段落，应用可以先检索这些段落，再提供给模型生成回答。这个检索与生成过程称为 retrieval-augmented generation (检索增强生成)，简称 RAG。[如何检索证据并据此生成回答](../rag/rag-architecture-and-implementation.md)

## 4. 让模型利用检索到的证据

应用现在发起另一次模型调用。除了原始问题和指令，还会包含模型的 `tool_call(c1, …)` 和与之匹配的 `tool_result(c1, …)`。调用记录了模型请求的内容，结果则提供工具实际观察到的信息。

第二次输入包含 `unit-tests`、`reject_empty_name`，以及预期的 `400` 与实际观察到的 `200`。这些细节会被格式化并编码为模型 context 的一部分。相同的推理机制会使用相同的训练权重处理扩展后的输入。新证据改变了模型可以据以回答的信息，不需要重新训练模型。权重是持久保存的学到的参数；输入和 hidden state 则是本次运行的数据。[训练如何改变模型参数](../foundations/how-llms-work.md#%E4%B8%8B%E4%B8%80%E4%B8%AA%E8%AF%8D%E5%85%83%E8%AE%AD%E7%BB%83%E5%A6%82%E4%BD%95%E6%9B%B4%E6%96%B0%E8%BF%99%E4%BA%9B%E5%8F%82%E6%95%B0%EF%BC%9F) 会介绍独立的学习过程。

如果证据仍有缺口，模型可以再请求一次工具调用；应用会在配置的调用次数、耗时和成本限制内，重复执行校验、工具操作和结果收集。如果达到限制，应用应根据目前取得的证据，返回未完成或失败的结果。本例中的日志足以说明观察到的失败，因此模型会生成解释。要判断底层代码缺陷，还需要更多证据，例如具体实现和预期行为。[行动、观察与下一步决策](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

## 5. 返回说明并完成本次运行

现在，回答可以陈述日志证实的内容。

> 构建 42 在 `unit-tests` 步骤失败。`reject_empty_name` 测试预期空名称请求返回 HTTP `400`，但实际收到 `200`。测试进程以状态 `1` 退出。若要确认底层原因，请对照测试的预期行为检查请求校验逻辑。

第一次模型调用以工具请求结束，因此应用还需要继续工作。第二次调用则正常地以回答结束。在本例中，应用会先保存回答并将本次运行标记为完成，再把结果返回给调用者。如果应用在生成过程中流式传输文本，仍须跟踪生成最终是成功完成还是失败。[运行状态与恢复](ai-application-architecture.md)

区分观察到的失败断言与其底层原因，也能帮助确定评估目标。改变提示词或解码设置后，系统仍应保留日志中的实际值，并避免臆造缺陷原因。评估时也应包含日志缺失或无法访问的情况。[如何判断 AI 系统是否满足任务契约？](../evaluation/llm-evaluation-methods.md) 会进一步说明验收标准和对比方法。

本次服务运行到此结束。若想进一步了解任一次模型调用中的计算过程，可以继续阅读[语言模型如何将提示转换为文本](../foundations/how-llms-work.md)。该章节会依次展开数学原理、训练过程和生成选择。

> [!info]- 来源
> 虚构的构建日志场景和小型数值示例用于说明下列来源支持的机制。
>
> - **Attention 与位置。** [Attention Is All You Need, v7, §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) 支持 scaled attention 与多个 head 的拼接。[RoFormer, v5, §3.2](https://arxiv.org/html/2104.09864v5#S3.SS2) 说明了 rotary position mechanism。本章的层示例采用 pre-normalization (前置归一化) 和仅解码器布局。
> - **FFN 门控与层布局。** [GLU Variants Improve Transformer, 2020, §2](https://arxiv.org/html/2002.05202#S2) 定义了 SwiGLU。[Llama 3 参考实现](https://github.com/meta-llama/llama-models/blob/main/models/llama3/model.py) 展示了 pre-normalization、residual update (残差更新) 和门控 FFN。
> - **输入格式化与生成。** [Transformers chat templates](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt) 说明了生成标记；其[缓存说明](https://huggingface.co/docs/transformers/main/en/cache_explanation) 介绍了如何复用先前的 K/V。token 片段使用 [tiktoken 0.12.0](https://github.com/openai/tiktoken/tree/0.12.0) 和 `cl100k_base` 重现。
> - **结构化请求与应用循环。** [OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) 和 [Claude tool-use guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools) 介绍了工具定义、模型请求、应用执行以及将结果反馈给模型的过程。此处的 `tool_call` 和 `tool_result` 记法仅供说明，并非 SDK schema。运行预算和针对构建日志提出的评估方式是本例中的工程选择。
>
> 查看 [AI 好文集](../../review/ai-literature-index.md) 中的相关论文。
