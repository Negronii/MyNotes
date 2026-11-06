# AI Engineering

> Generated from the [ai-engineering reading map](../../ai-engineering/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. AI 服务如何将一条消息变成完整回答？

### 案例：解释一次构建失败

想象一位开发者正在使用一款接入构建系统的 AI 助手。构建系统会对一次代码改动运行自动检查，而构建 `42` 失败了。开发者问：`Why did build 42 fail?` 失败详情保存在日志服务中，助手可以通过名为 `read_build_log` 的 tool (工具) 查询。

助手需要取回这些证据并解释日志说明了什么。我们将沿着这个问题走过整个服务流程，从准备模型输入，到返回一份以日志为依据的回答。应用负责管理日志服务的访问；模型先生成获取证据的请求，再利用证据生成说明。这是一个虚构的、由应用管理的 tool-call loop (工具调用循环) 示例。

下图展示成功完成的情形。本次运行包含两次模型调用：第一次生成工具请求；应用读取日志后，第二次生成回答。如果另一个问题本身已经包含足够证据，模型也可以在第一次调用时直接回答。

~~~mermaid
flowchart TD
    Input["1 准备输入<br/>问题 + 指令 + 工具定义"]
    Model["2 运行模型<br/>生成下一段输出"]
    Choice{"模型返回了什么？"}
    Tool["3 执行调用 c1<br/>检查访问权限，再读取构建 42"]
    Context["4 更新输入<br/>加入调用及其结果"]
    Answer["5 完成本次运行<br/>保存并返回说明"]
    Input --> Model --> Choice
    Choice -->|工具请求| Tool
    Tool -->|日志证据或错误| Context
    Context -->|下一次模型调用| Model
    Choice -->|最终回答| Answer
~~~

### 1. 准备模型可见的内容

harness 是负责协调模型与工具的应用代码。它记录调用者身份、为模型选择信息、执行工具，并决定应用何时有结果可返回。本例中的第一次模型调用有三项输入。

| 输入 | 本例中的内容 |
| --- | --- |
| 应用指令 | 根据现有证据解释构建失败。 |
| 用户消息 | `Why did build 42 fail?` |
| 工具定义 | `read_build_log` 接受整数 `build_id`，并返回构建日志中的失败记录。 |

> [!info] 指令、对话与外部状态
> 每次模型调用都会收到经过选择的输入。模型不会自动看到日志服务、应用数据库，或用户此前说过的所有内容。应用必须提供这些信息，或执行能取回信息的工具。

工具定义描述了一个可用操作。只有应用取回日志后，日志内容才会进入对话。应用会保留调用者身份，用于权限检查。

这些输入构成了本次调用的模型 context (上下文)。在较长的对话中，应用还需要决定包含哪些较早的消息和证据。这个选择很重要，因为模型只能依据实际提供的信息，以及训练参数中编码的知识来生成输出。[如何为每次模型调用选择信息](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)

### 2. 生成请求以获取缺失证据

现在，模型拿到了问题，也有办法请求日志。在 inference (推理) 过程中，它处理输入并一次生成一个 token (词元)。本次运行中，输出指定调用 `read_build_log`，并将 `build_id` 设为 `42`。

服务侧先格式化应用指令、用户消息和工具定义，再由 tokenizer (分词器) 转换为整数 ID。使用 `tiktoken 0.12.0` 和 `cl100k_base` 单独编码用户消息 `Why did build 42 fail?`，会得到七个片段 `["Why", " did", " build", " ", "42", " fail", "?"]`，对应 ID `[10445, 1550, 1977, 220, 2983, 3775, 30]`。这七个片段只说明用户原句的切分。实际调用会将应用指令、工具定义和用户消息按模型模板格式化后再编码；有对话历史时，还可加入选定的消息。令本次完整输入共有 `T` 个位置，不能直接把用户原句的七个 ID 当成完整模型输入。

embedding table (嵌入表) 会把每个 ID 映射为一个 vector (向量)。为说明张量形状，令词表大小为 `N`，示意模型宽度取 `8`；这不是实际服务配置，因此示意嵌入表形状为 `N × 8`。以单独编码用户原句的结果为例，ID `2983` 会查到索引为 `2983` 的行。完整输入则按实际编码出的 ID 查表，形成 `T × 8` 的 hidden state (隐藏状态)，每个位置占一行。每个 Transformer 层的 attention (注意力) 都能让一个位置从它可见的其他位置收集信息；feed-forward network (前馈网络，FFN) 则独立变换每一行的特征。于是，包含 `build` 和 `42` 的位置表示可以为后续位置提供信息；这只是位置交互的直觉，不表示我们测得本次推理实际关注了这两个位置。

经过最后一层和最终归一化后，模型使用最后一个输入位置的 `1 × 8` 状态预测下一个 token；这个位置有时是模板附加的 assistant 起始标记，不一定是用户消息的末尾。language model head (语言模型头，LM head) 将它映射为 `1 × N` 的 logits (未归一化分数)，每个词表条目一个分数。decoding (解码) 根据这些分数选择 token，将它追加到序列中，再对新位置继续前向计算。KV cache (键值缓存) 保存各层先前位置的 Key (键) 和 Value (值)：前者供新位置计算匹配分数，后者提供要按这些分数汇集的信息。新位置仍需计算自己的状态，并使用缓存中的 K/V。这个循环可以生成普通文本，也可以生成编码结构化工具请求的词元。

如果模型提供 temperature (温度) 设置，它会改变 token 采样分布的集中程度，但不能证明结果正确。[应用应如何选择解码设置？](#%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E8%A7%A3%E7%A0%81%E8%AE%BE%E7%BD%AE%EF%BC%9F) 会通过特定任务的评估来分析这个选择。若要查看一条模型输入如何逐步经过数值运算，可继续阅读[语言模型如何将提示转换为文本](#2.%20%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%A6%82%E4%BD%95%E6%8A%8A%E6%8F%90%E7%A4%BA%E8%AF%8D%E5%8F%98%E6%88%90%E6%96%87%E6%9C%AC%EF%BC%9F)。

针对构建问题，这次生成会按照模型的 tool-call 格式 (工具调用格式) 产生工具名和参数。inference service (推理服务) 会按照模型的 tool-call protocol (工具调用协议) 解释这些词元，并将完整的工具名和参数作为结构化 API 条目提供给应用。用简化记法表示，应用会收到 `tool_call(c1, read_build_log, {build_id: 42})`。ID `c1` 会把工具结果与这次特定请求关联起来。当有多个待处理调用时，这种对应关系很重要，模型才能知道哪条观察结果属于哪个请求。服务侧协调代码会将拟议的调用交给校验流程，从而进入总览图中的工具分支。接下来的步骤会说明执行前的检查。

### 3. 执行请求并读取日志

应用会检查 `read_build_log` 是否可用、`build_id` 是否为所需的整数类型，以及调用者是否有权读取构建 `42`。参数校验确保请求可以被正确解释。authorization (授权) 则确定调用者可以访问哪个资源。只有这些检查全部通过后，应用才会读取日志。如果工具会改变外部状态，例如重启构建，那么重试时还需要考虑前一次尝试是否已经生效。[工具契约与授权](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)

取回的结果包含模型此前缺少的证据。

| `c1` 的结果字段 | 构建 `42` 的值 |
| --- | --- |
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 失败断言 | 空名称请求应返回 HTTP `400`，但实际返回了 `200`。 |
| 进程退出状态 | `1` |

如果 authorization 失败，应用可以为 `c1` 返回失败结果，让模型在下一次调用时说明无法获取证据。本例中，工具按照 ID 查询一条已知日志。如果问题需要在大量文档中查找相关段落，应用可以先检索这些段落，再提供给模型生成回答。这个检索与生成过程称为 retrieval-augmented generation (检索增强生成)，简称 RAG。[如何检索证据并据此生成回答](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)

### 4. 让模型利用检索到的证据

应用现在发起另一次模型调用。除了原始问题和指令，还会包含模型的 `tool_call(c1, …)` 和与之匹配的 `tool_result(c1, …)`。调用记录了模型请求的内容，结果则提供工具实际观察到的信息。

第二次输入包含 `unit-tests`、`reject_empty_name`，以及预期的 `400` 与实际观察到的 `200`。这些细节会被格式化并编码为模型 context 的一部分。相同的推理机制会使用相同的训练权重处理扩展后的输入。新证据改变了模型可以据以回答的信息，不需要重新训练模型。权重是持久保存的学到的参数；输入和 hidden state 则是本次运行的数据。[训练如何改变模型参数](#%E4%B8%8B%E4%B8%80%E4%B8%AA%E8%AF%8D%E5%85%83%E8%AE%AD%E7%BB%83%E5%A6%82%E4%BD%95%E6%9B%B4%E6%96%B0%E8%BF%99%E4%BA%9B%E5%8F%82%E6%95%B0%EF%BC%9F) 会介绍独立的学习过程。

如果证据仍有缺口，模型可以再请求一次工具调用；应用会在配置的调用次数、耗时和成本限制内，重复执行校验、工具操作和结果收集。如果达到限制，应用应根据目前取得的证据，返回未完成或失败的结果。本例中的日志足以说明观察到的失败，因此模型会生成解释。要判断底层代码缺陷，还需要更多证据，例如具体实现和预期行为。[行动、观察与下一步决策](#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

### 5. 返回说明并完成本次运行

现在，回答可以陈述日志证实的内容。

> [!example] 根据日志返回说明
> 构建 42 在 `unit-tests` 步骤失败。`reject_empty_name` 测试预期空名称请求返回 HTTP `400`，但实际收到 `200`。测试进程以状态 `1` 退出。若要确认底层原因，请对照测试的预期行为检查请求校验逻辑。

第一次模型调用以工具请求结束，因此应用还需要继续工作。第二次调用则正常地以回答结束。在本例中，应用会先保存回答并将本次运行标记为完成，再把结果返回给调用者。如果应用在生成过程中流式传输文本，仍须跟踪生成最终是成功完成还是失败。[运行状态与恢复](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F)

区分观察到的失败断言与其底层原因，也能帮助确定评估目标。改变提示词或解码设置后，系统仍应保留日志中的实际值，并避免臆造缺陷原因。评估时也应包含日志缺失或无法访问的情况。[如何判断 AI 系统是否满足任务契约？](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) 会进一步说明验收标准和对比方法。

本次服务运行到此结束。若想进一步了解任一次模型调用中的计算过程，可以继续阅读[语言模型如何将提示转换为文本](#2.%20%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%A6%82%E4%BD%95%E6%8A%8A%E6%8F%90%E7%A4%BA%E8%AF%8D%E5%8F%98%E6%88%90%E6%96%87%E6%9C%AC%EF%BC%9F)。该章节会依次展开前向计算、解码和训练。

> [!info]- 来源
> 虚构的构建日志场景用于说明下列来源支持的服务机制。
>
> - **Attention 与逐位置变换。** [Attention Is All You Need, v7, §§3.2–3.5](https://arxiv.org/html/1706.03762v7#S3) 支持注意力的跨位置聚合，以及 FFN 对每个位置分别变换的结构。
> - **输入格式化、分词与缓存生成。** [Transformers chat templates](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt) 说明了生成标记；其[缓存说明](https://huggingface.co/docs/transformers/main/en/cache_explanation) 介绍了如何复用先前的 K/V。用户消息的片段和 ID 使用 [tiktoken 0.12.0](https://github.com/openai/tiktoken/tree/0.12.0) 与 `cl100k_base` 复现。
> - **结构化请求与应用循环。** [OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) 和 [Claude tool-use guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools) 介绍了工具定义、模型请求、应用执行以及将结果反馈给模型的过程。此处的 `tool_call` 和 `tool_result` 记法仅供说明，并非 SDK schema。运行预算和针对构建日志提出的评估方式是本例中的工程选择。
>
> 查看 [AI 好文集](../ai-literature-index.md) 中的相关论文。
## 2. 语言模型如何把提示词变成文本？

### 沿着一段短输入追踪模型处理过程

[服务篇](#1.%20AI%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E5%B0%86%E4%B8%80%E6%9D%A1%E6%B6%88%E6%81%AF%E5%8F%98%E6%88%90%E5%AE%8C%E6%95%B4%E5%9B%9E%E7%AD%94%EF%BC%9F)的第 2 步中，构建日志助手已经把 `Why did build 42 fail?`、应用指令和工具定义格式化为模型输入。本章从这次调用的完整输入开始，解释它如何变成输出序列，以及训练如何得到其中使用的参数。

为了让运算能在纸上跟下来，我们用 `ababca` 代替这个完整输入前缀，构造独立的 tokenizer (分词器) 和 258 项词表。示意的 decoder-only Transformer (仅解码器 Transformer) 宽度为 `8`，有两个 attention head (注意力头)，使用 gated feed-forward network (门控前馈网络，FFN)。它会把三个 token (词元) 位置一起送入模型，逐层更新。后文为各步骤选取局部数值演算，不提供一整套可复现完整前向计算的权重；这些值与构建助手的实测状态无关。真实消息的分词只用于对照词元边界，不与玩具词表混用。

~~~mermaid
flowchart TD
    Text["整理文本并分词<br/>示例：ababca → 3 个 ID"] --> E["查找嵌入<br/>3 个位置 × 8 个特征"]
    subgraph Pass["依次通过全部 Transformer 层"]
        A["注意力 Attention<br/>汇集可见位置的信息"] --> F["FFN<br/>变换各位置内部的特征"]
        F --> More{"还有下一层吗？"}
        More -->|有，使用下一层的权重| A
    end
    E -->|从第 1 层开始| A
    More -->|没有| L["最终归一化和语言模型头 LM head<br/>根据最后一个位置为词表打分"]
    L --> D["选出一个词元<br/>将其 ID 添加到前缀"]
    D --> Stop{"满足停止条件吗？"}
    Stop -->|没有| Next["嵌入新词元"]
    Next -->|从第 1 层重新开始<br/>复用各层缓存的 K/V| A
    Stop -->|满足| Out["返回生成的序列<br/>把词元字节解码为文本"]
~~~

生成还在继续时，也可以逐步解码文本。关键的循环在于：每次选出的词元都会成为下一次预测的输入之一。

### 分词器如何划分词元边界？

token 是特定词表中的一个条目。它可以表示标点、一个字节、部分单词、整个单词，也可以是带前导空格的一段文本。tokenizer 把文本映射为这些条目的整数 ID。ID 用来标识条目；ID 数字更大，并不表示对应的词更重要或更有力量。

在 byte-level byte pair encoding (字节级字节对编码，BPE) 中，训练从单字节片段开始，反复合并相邻且频繁出现的片段对。常见实现会先用正则表达式把文本分成若干段，再在每段内部执行 BPE。编码新文本时，会使用已经学到的合并优先级。

假设训练片段是 `abab`、`ab` 和 `ac`。先建立 256 个单字节条目，编号为 `0` 到 `255`。`a+b` 这一对出现三次，因此第一次合并会创建 `ab`，ID 为 `256`。此时各段变为 `[ab, ab]`、`[ab]` 和 `[a, c]`。接下来，`ab+ab` 和 `a+c` 都各出现一次。假定这个玩具示例的平局规则选择 `ab+ab`，于是创建 ID 为 `257` 的 `abab`。

| 步骤 | 对此前未见的输入 `ababca` 所做的处理 |
| --- | --- |
| 从字节开始 | `[a, b, a, b, c, a]` |
| 应用优先级最高的可用合并 | `[ab, a, b, c, a]`，然后是 `[ab, ab, c, a]` |
| 应用下一次合并 | `[abab, c, a]` |
| 查找这三个 ID | `[257, 99, 97]` |

作为真实词表的对照，服务章节中的用户消息 `Why did build 42 fail?` 使用 `tiktoken 0.12.0` 和 `cl100k_base` 单独编码后是七个片段 `["Why", " did", " build", " ", "42", " fail", "?"]`，对应 ID `[10445, 1550, 1977, 220, 2983, 3775, 30]`。这只覆盖用户原句；实际调用把应用指令、工具定义和用户消息按模型模板格式化后再编码，有历史时还可加入选定的消息。它与上面 `ababca` 的玩具词表是两套独立的 ID，不能互换。同一版本对 `The transformer architecture revolutionized NLP.` 的分词也显示边界不等于词界：`revolutionized` 被切成 `revolution` 与 `ized`，`NLP` 被切成 `N` 与 `LP`。

> [!info] 词元边界不一定是字符边界
> 一个 Unicode 字符可能由多个 UTF-8 字节组成。字节级词元片段可能会拆开这些字节，因此逐个把词元当作完整字符串解码，可能得到损坏的字符。增量文本解码会暂存尚未完整的字节，直到后续字节到达。

这会影响请求的 token 预算。统计输入时，要使用已部署模型的 tokenizer，并计入请求格式中的角色标记和工具定义。如果完整对话太长，接下来要决定的是[每次模型调用应保留哪些信息](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)，而不是简单地数词。BPE 只是 tokenizer 的一种类型，并非后续 Transformer 计算的必需条件。

### 第一个 Transformer 块接收什么？

embedding table (嵌入表) 为词表中的每个条目保存一个已学习的 vector (向量)。设词表大小为 `N`、模型宽度为 `d`、输入长度为 `T`。在这个玩具模型中，`N = 258`、`d = 8`、`T = 3`，所以表 `E` 的形状是 `258 × 8`。

ID `257` 选出 `E` 中索引为 `257` 的行，ID `99` 和 `97` 则选出相应的行。把取出的行堆叠起来，就得到初始 hidden state (隐藏状态)`X₀`，形状为 `3 × 8`。此时第一个位置是 `abab` 的向量，第二个位置是 `c` 的向量，第三个位置是 `a` 的向量。

> [!info] 读数之前先看清各轴
> 在 `T × d` 中，行表示词元位置，列表示已学习的特征坐标。一行是一个 vector，也就是由 `d` 个数字按顺序组成的列表。一列则表示某个坐标在各个位置上的取值。如果添加一个 batch axis (批次维)，它就能把多个这样的序列放在一起。某个特征坐标并没有固定、可读作“篮球”之类的含义。

同一 ID 选出的初始行相同，但后续各层会根据位置和上下文改变它的表示。从数学上看，查表等价于用一个 one-hot vector (独热向量) 乘以 `E`：独热向量在对应 ID 的位置上是 `1`，其余位置都是 `0`。实际实现通常直接取出相应行。

attention sublayer (注意力子层) 使用这些向量之前，我们的模型会做 normalization (归一化)。例如，RMSNorm (均方根归一化) 会让每行除以其坐标均方值加上一个很小的稳定常数后所得的平方根，再乘上可学习的坐标缩放值。忽略这个很小的常数，并假定缩放值都为 `1`，`[3, 4]` 除以 `√((9+16)/2) ≈ 3.536` 后约为 `[0.849, 1.131]`。这能控制数值尺度，不会改变行数或列数。我们把归一化后的矩阵记为 `U`。接下来的步骤会在 Q 和 K 中引入位置信息。

### Q、K、V 如何生成注意力更新？

#### 将每一行投影为 Q、K、V

attention (注意力) 计算每个位置应从可见位置汇集哪些信息。它从当前 hidden state 推导出三种表示。query (查询，Q) 参与决定要匹配什么；key (键，K) 参与计算匹配分数；value (值，V) 提供将根据这些分数组合的内容。这些名称描述的是向量在计算中的用途。

每个 attention head 都有自己的 Q、K、V projection (投影)。在本例中，每个头的宽度为 `4`。将 `3 × 8` 的矩阵 `U` 乘以该头形状为 `8 × 4` 的查询投影权重，得到形状为 `3 × 4` 的 Q。K 和 V 也以相同方式计算，只是使用各自的矩阵。

> [!info] 矩阵乘法会得到什么？
> 每个输出坐标都是输入行与权重列的 dot product (点积)。例如，`[2, 3] · [4, 5] = 2×4 + 3×5 = 23`。如果权重的两列分别是 `[4, 5]` 和 `[1, −1]`，同一输入行就会变成 `[23, −1]`。每一列定义了输入特征的一种加权组合。因此，`3 × 8` 乘以 `8 × 4` 后仍有三个位置，每个位置产生四个特征。相乘的内侧维度相同，决定了哪些坐标会相乘并求和。

把两个头一起计算很方便。有 `Hq = 2` 个头、每个头宽度 `dh = 4` 时，每个合并投影矩阵的形状为 `d × (Hq·dh) = 8 × 8`。我们计算 `Q = UW_Q`、`K = UW_K` 和 `V = UW_V`，然后沿特征轴拆分为两个宽度为 `4` 的头。每个头各自得到一个 `3 × 4` 的 Q、K 和 V。这里使用行向量右乘权重的记法。库也可能按转置后的方向存储权重；例如 PyTorch `Linear` 会按输出特征数 × 输入特征数存储权重。

模型使用 rotary position embedding (旋转位置编码，RoPE)。它会根据 Q 和 K 所属的位置旋转其中成对的坐标，再计算点积。因此，所得分数可以受相对位置影响，但张量形状不变。

#### 把两两分数转换为加权混合

对一个头，计算每个 query 位置与每个 key 位置之间的分数。

$$
S = \frac{QK^\top}{\sqrt{d_h}} + M,\qquad
P = \operatorname{softmax}_{\mathrm{keys}}(S),\qquad
Z = PV.
$$

这里的 `Kᵀ` 表示 K 的 transpose (转置)，也就是交换 K 的行与列。`Q` 的形状是 `3 × 4`，`Kᵀ` 的形状是 `4 × 3`，所以乘积形状为 `3 × 3`。其中 `(i, j)` 项是位置 `i` 的 Q 与位置 `j` 的 K 的点积。现在每一行都列出一个位置对所有位置的分数。这次乘法比较的是各个位置；前面的 `UW_Q` 则是在每个位置内部变换特征。

随着头宽增大，除以 `√dh` 会控制分数的尺度。在一个用来解释这一做法的近似假设下，各坐标彼此独立、均值为 `0` 且方差为 `1`，那么 `dh` 个乘积之和的方差与 `dh` 成正比。缩放能抑制分数差异随头宽增大，降低 softmax 过度集中于单项的风险。

causal mask (因果掩码) `M` 在每个 query 行上，把未来 key 对应的分数加上 `−∞`，其他分数加 `0`。随后沿这一行的 key 维度做 softmax，再加权 V，因此当前位置无法读取未来 token。对第二个位置，也就是词元 `c`，假设已经按位置旋转的 Q 是 `[2, 0, 0, 0]`。设 `abab`、`c` 和 `a` 的旋转后 K 分别为 `[1, 0, 0, 0]`、`[0, 1, 0, 0]` 和 `[2, 0, 0, 0]`。这些 K 与 Q 的点积为 `[2, 0, 4]`。除以 `√4 = 2` 后得到 `[1, 0, 2]`。未来的词元 `a` 分数最高，但掩码会把它排除，结果是 `[1, 0, −∞]`。

> [!example] softmax 把分数变成相对权重
> softmax 对每个分数取指数，再除以所有指数之和。这里 `e ≈ 2.718`。`[1, 0, −∞]` 对应的权重为 `[e/(e+1), 1/(e+1), 0] ≈ [0.731, 0.269, 0]`，总和为 `1`。这些权重表示这个头如何混合 V 向量；它们不是对应词语为真的概率。

假设前两个 V 向量是 `(1, 0, 0, 0)` 和 `(0, 2, 0, 0)`。那么第二个位置的加权和为

$$
0.731(1,0,0,0)+0.269(0,2,0,0)=(0.731,0.538,0,0).
$$

对全部三个 query 位置而言，`P` 的形状是 `3 × 3`，`V` 的形状是 `3 × 4`，所以 `Z = PV` 的形状是 `3 × 4`。现在每个输出行都包含它能够看到的位置汇集来的信息。

#### 合并注意力头并保留已有状态

另一个头有自己的投影和加权和。concatenation (拼接) 会把两个宽度为 `4` 的输出逐个位置并排放好，得到 `3 × 8`。形状为 `8 × 8` 的输出投影 `W_O` 会混合这些特征。residual connection (残差连接) 会把注意力更新逐坐标加回该层原来的输入。

假设某一行原来是 `[1, 2]`，更新量是 `[0.1, −0.2]`，残差相加后得到 `[1.1, 1.8]`。两项的形状必须一致。每一层都能保留已有信息，同时计算一个更新。输出中每个词元位置仍有一行宽度为 `8` 的向量。

不同层、任务和输入中的 attention head 行为可能不同。某个头可能经常关注前一个位置，但仅凭权重图并不能确定它的完整功能。它的 V 向量、输出投影以及后续层也都会影响结果。

#### 注意力头共享 K 和 V 时会怎样？

上面的计算使用 multi-head attention (多头注意力，MHA)，每个 Q 头都有一个 K/V 头。grouped-query attention (分组查询注意力，GQA) 让一组 Q 头共享一个 K/V 头。如果仍保留两个 Q 头、但只使用一个 K/V 头，那么 `W_Q` 仍是 `8 × 8`，而 `W_K` 和 `W_V` 会变为 `8 × 4`。两个 Q 仍各自生成宽度为 `4` 的输出，所以拼接后的形状和 `W_O` 都不变。

`Hkv` 表示 K/V 头数。生成时会保留每层各位置的 K 和 V，供后续 token 复用。MHA 中 `Hkv = Hq`；multi-query attention (多查询注意力，MQA) 则是 `Hkv = 1` 的情况。这些选择会影响所学权重，以及生成过程中存储的 K/V 数量。把 MHA checkpoint 转为其他结构会改变 K/V 权重和模型行为；GQA 论文评估了基于权重平均的转换以及后续训练。在这个例子中，缓存了三个位置时，每层的 MHA 会存储 `2 × 3 × 2 × 4 = 48` 个 K/V 数值，依次对应 K/V 两种表示、三个位置、两个头和每头四个坐标。共享一个 K/V 头后，数量降为 `2 × 3 × 1 × 4 = 24`，而两个 Q 头仍各自计算分数。若想了解服务环节的影响，请继续阅读[KV cache 和调度如何决定推理容量](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F)。Dense attention 的两两计算量随 `T²` 增长，但实际时延还取决于 kernel (计算内核)、其他层和硬件。

### FFN 增加了什么，多个块如何堆叠？

#### 变换每个位置的特征

attention 更新已经把上下文信息带入每一行。FFN 会在每行内部应用非线性变换。它也常被称为 multilayer perceptron (多层感知机，MLP)。同一层内的所有位置共用一套 FFN 权重，不同层通常使用不同权重。如果投影之间没有非线性操作，多次线性变换会合并为一次线性变换；加入非线性后，更新就能更丰富地取决于输入特征的组合。

以 SwiGLU FFN 为例，先对经过 attention 更新的状态做归一化，得到形状为 `3 × 8` 的 `R`。两个投影 `W_g` 和 `W_u` 的形状都是 `8 × 16`，分别生成门控输入和候选分支。对门控输入应用 SiLU，用 `⊙` 表示逐元素相乘两个分支，最后通过 down projection (降维投影) `W_d` 投影回去；它的形状为 `16 × 8`。

$$
F(R)=\big[\operatorname{SiLU}(RW_g)\odot(RW_u)\big]W_d,
\qquad \operatorname{SiLU}(x)=x\sigma(x),
\qquad \sigma(x)=\frac{1}{1+e^{-x}}.
$$

sigmoid `σ` 的取值介于 `0` 和 `1` 之间。SiLU 将输入乘以这个比例，形成平滑的非线性变换。在这里，最后得到的门控值可能是负数，也可能大于 `1`。它们连续地缩放候选特征，而不是像二进制开关那样只有开或关。

> [!example] SiLU 如何门控候选特征
> 对某一行取两个门控输入 `[0, 1]` 和候选值 `[2, 3]`。SiLU 先把门控输入变为约 `[0, 0.731]`，再逐元素相乘，得到 `[0, 2.193]`。这只是 `3 × 16` 中两个通道的例子；`W_d` 随后把整行的 16 个通道混合为 8 个，再将这个更新加回 attention 状态。逐元素乘法保持宽度为 16，不会像点积那样求和为单个数字。

由于门控分支和候选分支都取决于当前行，同一套权重可以针对不同上下文产生不同更新。

这有助于解释学习到的知识为何会影响预测。如果某一行代表篮球语境中的人名，学到的特征组合就可能激活某些方向，从而影响相关的输出词元。Geva 等人发现，他们所研究的部分 FFN 中存在文本模式关联和输出影响。这一发现适用于那些模型，并不表示每个 FFN 都是字面意义上的事实数据库。模型输出事实的能力也取决于 attention、多层计算和最终词表投影。若信息必须保持最新或能够核验，[检索与依据构建](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) 介绍了应用如何提供外部证据。

#### 把更新后的状态传给下一层

这里的块使用 pre-normalization (预归一化)，也就是在 attention 和 FFN 之前分别做归一化。设 `Xℓ` 是第 `ℓ` 层的输入，两次更新为

$$
Y_\ell=X_\ell+\operatorname{Attention}_\ell(\operatorname{Norm}_{\ell,1}(X_\ell)),
$$
$$
X_{\ell+1}=Y_\ell+F_\ell(\operatorname{Norm}_{\ell,2}(Y_\ell)).
$$

~~~mermaid
flowchart TD
    X["层输入 X<br/>3 × 8"] --> N1["归一化"] --> A["Attention<br/>混合不同位置的信息"]
    A --> Y["加上 attention 更新<br/>Y 的形状为 3 × 8"]
    X -->|残差| Y
    Y --> N2["归一化"] --> F["SwiGLU FFN<br/>扩展至 3 × 16，门控，再投影至 3 × 8"]
    F --> Next["加上 FFN 更新<br/>下一层接收 3 × 8"]
    Y -->|残差| Next
~~~

每一层都会对相同位置再做一次变换。在这个模型中，随着层数增加，序列长度和宽度都不会缩短。这里示例的 decoder-only 架构选择包括 RMSNorm、RoPE 和门控 FFN；是否共享 K/V 则是另一项独立的架构选择。2017 年提出的 Transformer 在翻译任务的 encoder–decoder (编码器–解码器) 模型中使用 attention 和逐位置 FFN。它的 decoder 也使用了 cross-attention (交叉注意力)，归一化方式和 FFN 选择也与此不同。这里的公式描述所选的 decoder-only 示例；具体模型采用的架构由其实现决定。

#### 哪些数字属于可学习参数？

矩阵的参数数量等于行数乘以列数。在普通 MHA 且 `Hq·dh = d` 时，Q、K、V 和输出投影合计有 `4d²` 个参数。若 `d = 8`，则共有 `256` 个。三个 SwiGLU 投影合计有 `3d·dff` 个参数；若 `dff = 16`，则共有 `384` 个。

完整模型还包含 embedding table、归一化权重，有时还包含单独的词表投影。每一层都有自己权重时，逐层重复计算；共享权重只计一次。hidden state 和缓存的 K/V 是根据这些参数计算出来的临时数据。因此，参数数量本身无法决定 GPU 上能同时容纳多少请求。这也是继续阅读[推理内存与调度章节](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) 的原因之一。

### 模型如何选择词元并继续生成？

#### 为词表打分并选择一个 ID

生成下一个 token 时，模型在最后一层和最终归一化后，取最后一个输入位置的向量 `h_last` 交给 language model head (语言模型头，LM head)；这一行的形状是 `1 × 8`。对于 `[abab, c, a]`，它就是第三个位置 `a` 对应的更新后向量。前面的 attention 算例特意选了第二个位置来演示未来屏蔽；第三个位置也按同样规则计算，并继续经过所有层，才得到这里的 `h_last`。在 causal attention 中，这个位置可以关注整个输入前缀。格式化的对话中，它也可能是 assistant 起始标记，而不是用户问题的最后一个字符。

将 `h_last` 乘以形状为 `8 × 258` 的 `W_lm`，会得到形状为 `1 × 258` 的 logits (未归一化分数)，每个词表 ID 对应一个分数。`W_lm` 的每一列都会与 `h_last` 做点积，算出一个分数。weight tying (权重绑定) 会把 embedding table 的转置用作这个输出权重，从而省去一张单独的参数矩阵。有些架构会分别使用输入和输出权重。

做 sampling (采样) 时，temperature (温度)`τ > 0` 会在 softmax 之前缩放 logits。

$$
p_i=\frac{\exp(z_i/\tau)}{\sum_j\exp(z_j/\tau)}.
$$

为单独观察 temperature 的作用，下面只允许两个候选 token，其余词表项暂设为不参与采样。这个人为限制不代表完整词表的真实预测。两个候选是：`c` (ID `99`) 和 `a` (ID `97`)，为它们设定演算用的 logits `[2, 1]`，不由前面的局部 QKV 数字推导。温度为 `1` 时，概率约为 `[0.731, 0.269]`；温度为 `0.5` 时，概率变为 `[0.881, 0.119]`；温度为 `2` 时，则为 `[0.622, 0.378]`。温度越低，概率越集中于分数较高的候选项；温度越高，分数较低的候选项也越有机会被选中。这些是下一个词元的概率，并不代表答案在事实层面正确的置信度。

greedy decoding (贪心解码) 会直接选择分数最高的词元。API 的温度零设置可能表示请求采用贪心行为；上面的公式无法真的除以零。Top-k sampling 会保留分数最高的 `k` 个候选项。Top-p，也称 nucleus sampling (核采样)，会保留按概率降序排列、总和首次达到阈值的最短前缀，然后重新归一化。对于 `[0.50, 0.30, 0.15, 0.05]` 和 top-p `0.75`，保留前两个概率，除以它们的总和 `0.80` 后变为 `[0.625, 0.375]`。

#### 复用已有前缀并预测下一个词元

prefill (预填充) 会让初始序列通过各层。最后一个位置的 logits 选出第一个输出词元。假设我们选出 `c`，ID 为 `99`。词元序列由 `[257, 99, 97]` 增长为 `[257, 99, 97, 99]`。新生成的文本此时只有 `c`；前面的 `ababca` 是输入，仍留在模型上下文中。decode (增量解码) 会嵌入新位置上的 `c`，并从第一层开始处理它，以预测下一个词元。

在 causal model (因果模型) 中，对于相同的前缀和推理配置，添加新位置不会改变先前位置的 hidden state。因此，KV cache (键值缓存) 会存储每一层此前算出的 K 和 V。在新位置，该层会计算新的 Q、K 和 V。新位置上的 Q 会关注缓存中的 K/V 以及当前位置的 K/V，再把新的 K/V 追加到缓存中。更早位置的 Q 向量已经参与过各自位置的计算，不会作为输入再参与这个新 query 的 attention 运算。

每层的 cache 各自独立，因为每一层的输入表示和投影权重不同。输出变长时，cache 也会随之增大。生成会在模型结束词元、应用停止序列、长度上限或取消操作时结束。长度上限可能会截断尚未完成的回答，因此应用必须判断完成原因。[服务容量](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) 会进一步说明内存影响；[应用运行状态与恢复](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) 会展开生成结束或中断后的处理。

#### 应用应如何选择解码设置？

实际选择应从已部署的模型和 endpoint (端点) 入手。先确认支持哪些控制项、哪些组合可用，再以支持的默认值建立基线。采样控制取决于模型和 API 版本；一些托管接口会限制、固定或省略这些参数。不存在适用于所有模型和任务的最佳温度。

对于构建日志助手，如果多次运行的工具参数或证据报告不必要地发生变化，可以尝试一个受支持的较低温候选设置。将其与基线进行比较，覆盖常见故障、日志缺失、权限失败，以及带有误导性文字的日志。较低设置也可能反复偏向错误操作，所以结果稳定本身并不代表成功。

如果任务本来就需要生成多个候选解释或解法供后续核验，那么尝试更高的采样多样性可能有用。代价是出现更多质量较差或无效的候选结果，也需要更多核验工作。提高温度既不会补上缺失证据，也不会让没有依据的说法变得可接受。多样性是否能改善最终结果，取决于候选生成器与验证器的整体效果。

做受控比较时，应固定模型版本、指令、工具和案例集，只改变所选的解码设置。对每个候选设置重复完整运行，并衡量工具选择及参数是否正确、解释是否有依据、故障处理是否恰当，以及成本和时延。用一组数据开发设置，再用单独的留出集验收。这是一种工程测试方法，并非宣称较低或较高的温度必然更好。[如何构建可比较的评估集](#Build%20a%20comparable%20regression%20set%20/%20%E5%BB%BA%E7%AB%8B%E5%8F%AF%E6%AF%94%E8%BE%83%E7%9A%84%E5%9B%9E%E5%BD%92%E9%9B%86) 会进一步介绍评估方法，而不只关注这一项设置。

### 下一个词元训练如何更新这些参数？

#### 为每个位置设置目标

前面使用的都是已经学到的权重。训练会根据“接下来应该是什么”的示例来调整这些权重。沿用玩具 tokenizer，训练样本 `ababcac` 会被分成 `[abab, c, a, c]`，即 `[257, 99, 97, 99]`。用前三个位置预测后一个：`abab → c`、`c → a`、`a → c`。这里末尾的 `c` 是训练语料中的真实目标，不是刚才生成步骤采出的结果。causal mask 允许并行计算这些预测，同时阻止每个位置读取右侧的目标 token。某些模型的训练格式还会加入 beginning-of-sequence marker (序列起始标记，BOS) 等特殊 token；它们需要由相应词表和模板定义，本例不额外加入。

teacher forcing (教师强制) 指训练时使用训练样本中真实的前序词元。生成时，后续输入则包含模型实际选出的词元。这就是为什么生成序列开头的错误可能改变后续预测。

#### 计算误差并反向传播更新

在这里的训练过程中，`p` 是对完整词表的原始 logits 执行普通 softmax 的结果，没有使用推理时的温度或 top-k/top-p 过滤。对于目标 ID `y_i`，cross-entropy (交叉熵) 使用 `−log p(y_i)`，并对训练中包含的位置取平均。如果正确词元的概率是 `0.8`，损失约为 `0.223`；概率为 `0.25` 时，损失约为 `1.386`。两者的平均值约为 `0.805`，使用的是自然对数，其单位称为 nat。正确词元的概率越低，惩罚就越大。

对单个位置来说，该损失相对于 logits 的导数是 `p − onehot(y_i)`。这个结果保留了除正确项以外的所有概率项，并从正确项中减去 `1`。如果概率是 `[0.7, 0.2, 0.1]`，而第二个词元是正确答案，gradient (梯度) 就是 `[0.7, −0.8, 0.1]`。

> [!info] gradient 表示损失在局部如何变化
> 导数为正，表示稍微增大对应数值会使损失增大。因此 gradient descent (梯度下降) 会减去导数的一小部分。在这个例子中，如果直接更新 logits，就会降低第一个和第三个值，提高第二个值。实际训练更新的是产生这些 logits 的共享参数，并使用 chain rule (链式法则) 将它们的影响沿计算过程反向传播。

backpropagation (反向传播) 会把导数依次传过 LM head、残差相加、FFN、attention 和 embedding。对于简单的计算链 `z = wx`，若 `x` 固定，则 `∂L/∂w = (∂L/∂z)x`。矩阵形式会累加多个坐标和位置上的贡献。optimizer (优化器) 按照自己的步长和累积统计规则更新参数。训练利用前向计算的中间量，沿计算图反向求出各参数的梯度，再据此更新参数。

所选的训练目标也很重要。BERT 使用的 masked language modeling (掩码语言建模) 会根据左右两侧可见的上下文，预测选定的缺失位置。它的常规过程与上面从左向右的循环不同。研究者可以基于掩码模型构造迭代生成过程，但这需要另外的采样过程。

如果应用反复以稳定的方式失败，接下来要判断的是：它缺少证据、指令，还是已经学到的行为。[何时进行微调](#17.%20%E4%BD%95%E6%97%B6%E5%BA%94%E5%BE%AE%E8%B0%83%E6%9D%A5%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F) 会进一步说明这个选择，包括应更新哪些参数。把新证据加入 prompt (提示词) 会改变当前计算；训练则会改变能在后续运行中持续生效的参数。

> [!info]- 来源
> 下列来源为所列机制提供依据。较小的张量维度、虚构的向量和构建日志调参场景都是教学示例或工程扩展。
>
> - **词元化。** [Sennrich et al., 2016, §3.2](https://aclanthology.org/P16-1162/) 解释了子词 BPE。[tiktoken 0.12.0 educational implementation](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken/_educational.py) 实现了字节级训练、合并优先级和解码。文中给出的精确英文词元序列使用该版本软件包和 `cl100k_base` 复现。
> - **Attention 与原始架构。** [Attention Is All You Need, v7, §§3.1–3.5 and §5.1](https://arxiv.org/html/1706.03762v7#S3) 支持缩放点积、掩码、多头拼接、逐位置 FFN，以及原始 encoder–decoder 的适用范围。论文中的翻译任务设定与这里演示的 decoder-only 模型不同。
> - **位置与归一化。** [RoFormer, v5, §3](https://arxiv.org/html/2104.09864v5#S3) 解释 RoPE；[Root Mean Square Layer Normalization, 2019, §3](https://arxiv.org/abs/1910.07467) 解释 RMSNorm。[The Llama 3 Herd of Models, v3, §3.2](https://arxiv.org/html/2407.21783v3#S3.SS2) 和 [Llama 3 参考实现](https://github.com/meta-llama/llama-models/blob/main/models/llama3/model.py) 为 decoder-only 架构选择和归一化顺序提供依据。具体配置由特定模型的实现决定。
> - **投影权重存储与 K/V 共享。** [PyTorch Linear](https://docs.pytorch.org/docs/stable/generated/torch.nn.Linear.html) 说明了权重的存储方向。[GQA, EMNLP 2023, §2](https://aclanthology.org/2023.emnlp-main.298/) 介绍了分组 K/V 头，以及通过 uptraining 转换模型的方法。
> - **FFN 门控与解释。** [GLU Variants Improve Transformer, 2020, §2](https://arxiv.org/html/2002.05202#S2) 定义了 SwiGLU。[Geva et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.446/) 研究了 FFN memory 中的文本模式关联与输出影响；结论仅适用于其分析的模型。
> - **采样与部署控制。** [The Curious Case of Neural Text Degeneration, v2, §3](https://arxiv.org/abs/1904.09751v2) 介绍 nucleus sampling。[Transformers generation configuration](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation) 记录了采样控制项。[OpenAI Responses parameters](https://developers.openai.com/api/reference/resources/responses/methods/create) 记录了托管 API 的契约。[OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model) 和 [Claude model migration guidance](https://platform.claude.com/docs/en/about-claude/model-deprecations) (核对日期：2026-11-06) 展示了模型和 API 版本可能带来的限制。这里提出的调参比较是这些机制的一种工程应用，并非普遍适用的温度建议。
> - **缓存生成。** [Transformers cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation) 解释了因果复用、逐层 K/V，以及新词元如何关注此前和当前位置。
> - **训练。** [Llama 3, v3, §3](https://arxiv.org/html/2407.21783v3#S3) 涉及预训练；[PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html) 说明了损失函数。[BERT, 2019, §3.1](https://arxiv.org/abs/1810.04805) 支持掩码目标的描述；[Wang and Cho, 2019](https://arxiv.org/abs/1902.04094) 探索了一种不同的迭代生成过程。
>
> 浏览[AI 好文集](../ai-literature-index.md)，可按主题查找相关论文。
## 3. How do KV cache and scheduling determine LLM serving capacity? / KV 缓存与调度怎样决定模型推理容量？

**Short answer / 简答** — Prefill creates the prompt’s per-layer K/V state. Decode reuses it and appends new K/V, so active sequence length and concurrency drive memory. Use a tiled attention kernel to reduce GPU memory traffic, page the persistent cache to reduce allocation waste, and schedule prefill and decode under a latency target. Measure which limit dominates before tuning. / 预填充生成提示词在各层的 K/V。增量解码读取旧状态并追加新 K/V，因此活跃序列的长度和并发数决定显存用量。用分块计算内核减少显存读写，用分页管理持久缓存减少分配浪费，再按时延目标调度 prefill 与 decode。先测量瓶颈在哪一层，再选优化。

**Key terms / 关键术语** · prefill / 提示预填充 · decode / 增量解码 · HBM / 高带宽显存 · KV cache / 键值缓存 · continuous batching / 连续批处理 · TTFT / 首词元时延 · ITL / 词元间时延

### What stays on the GPU between decode steps? / 解码步之间哪些数据留在 GPU？

[生成机制](#2.%20%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%A6%82%E4%BD%95%E6%8A%8A%E6%8F%90%E7%A4%BA%E8%AF%8D%E5%8F%98%E6%88%90%E6%96%87%E6%9C%AC%EF%BC%9F)中的因果注意力解释了可缓存的条件。Prefill 把提示输入各层，写出全部提示位置的 K、V，并由最后一个位置的 logits 得到第一个输出 token。下一步把该 token 送进模型。每层为它计算新的 Q、K、V。新的 Q 对缓存里的旧 K 和当前 K 打分，再对对应 V 求加权和。在标准因果设置下，旧位置不受未来 token 影响，可以沿用旧 K/V。旧 Q 已经用于旧位置自己的更新；后续位置的 attention 不读取它。每层所需的投影来自该层自己的输入与权重，因此要存各层的 K/V。

| 阶段 | 注意力典型形状，单条请求 | 常见成本 |
| --- | --- | --- |
| Prefill $T$ 个提示 token | 每个 query 头处理 $T$ 个 query 和 $T$ 个 key，带因果掩码 | 大量投影与 FFN 矩阵乘法，长序列的全量注意力计算和内存流量 |
| 带缓存的单步 decode | 每个 query 头只有 1 个 query，对长度 $C+1$ 的历史加当前 key/value 做注意力 | 读取模型权重和历史 K/V，追加当前 token 的 K/V。长前缀增大读取量，并发改变权重摊销和硬件利用率 |

这里 $C$ 是这一轮之前已存的长度。对全量 dense attention，decode 单步在序列维上仍随历史长度增长。缓存避免重复为旧位置做投影和前向，不能免掉这一步对旧 K/V 的读取。Prefill 通常偏计算，低批量 decode 常受显存带宽限制，具体取决于模型、并发、长度、精度与硬件。 [Hugging Face Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation) · [Sarathi-Serve §§2–4](https://arxiv.org/abs/2403.02310)

### Estimate memory before admitting requests / 先估显存，再决定并发

对每层采用相同 K/V 形状、K 和 V 每元素占同样字节的普通全量注意力模型，单条序列的 KV 载荷约为

$$
\text{bytes} = 2 \cdot L \cdot T \cdot H_{kv} \cdot d_h \cdot b.
$$

$L$ 是层数，$T$ 是当前缓存长度，$H_{kv}$ 是实际存储的 KV 头数，$d_h$ 是头宽，$b$ 是每元素字节数。最前面的 2 对应 K 和 V。用 32 层、8 个 KV 头、头宽 128、BF16（2 bytes）的示例，得到 **128 KiB/token**。缓存到 8,192 token 时每条序列是 **1 GiB**，32 条同长度且没有前缀共享的序列就需要 **32 GiB** 的 KV 载荷。权重、临时激活、块尾空位和调度余量另算。张量并行可能拆分或复制部分状态，单卡预算应按实际分片和测量核对。

GQA 从模型结构上减少要存的 K/V 头。KV 量化从存储表示上减少每个元素的字节数，两者可以同时存在。KV 量化还涉及缩放参数、精度损失和内核支持，不能把存储比直接当吞吐比。滑动窗口、混合状态或潜变量注意力的持久状态不同，应按层核算。 [GQA §2](https://aclanthology.org/2023.emnlp-main.298/) · [KIVI §3](https://arxiv.org/abs/2402.02750) · [vLLM KV cache 配置](https://docs.vllm.ai/en/latest/api/vllm/config/cache/)

如果权重本身都放不进一张卡，分页只能减少缓存浪费。先比较能达到质量门槛的权重量化和多卡切分。**Tensor parallelism / 张量并行** 把同层的矩阵或注意力头分给多卡，层内需要交换或汇总结果。**Pipeline parallelism / 流水线并行** 把不同层放到不同卡上，阶段间传递激活，流水线未填满时会有空转。把模型装下以后，再按每卡的权重、KV 和临时缓冲预算接纳序列。分片策略要考虑互连带宽和 KV 头在各卡上的实际放置。 [vLLM 并行与扩展](https://docs.vllm.ai/en/latest/serving/parallelism_scaling/)

### Separate kernel work from cache allocation / 区分内核计算和缓存分配

**FlashAttention** 将 Q/K/V 分块，维护可增量合并的 softmax 统计量，避免把完整注意力分数矩阵写入 HBM。它针对一次 attention 运算的读写和临时显存，使用精确 dense attention 算法（浮点舍入可不同），也仍计算有效位置对。FlashAttention-4 进一步针对 Blackwell 的异步矩阵乘与流水线重叠优化，说明内核选择要看硬件和形状。 [FlashAttention §3](https://arxiv.org/abs/2205.14135) · [FlashAttention-4，2026](https://arxiv.org/abs/2603.05451)

**PagedAttention** 管理跨解码步骤持久存在的 KV 状态。借鉴操作系统分页，每个请求的逻辑 KV 块按 token 顺序增长，块表把它们映射到可不连续的显存物理块。支持这种布局的 attention 内核按表访问历史 K/V，服务端按需申请块。原论文 §4.3 的例子是每块四个 token，七个提示 token 分别使用物理块 7 和 1，后者还剩一格。下一次 decode 填这一格，再往后增长才需要申请新的块。请求完成后可归还块，共享前缀可引用同一份块；若两个分支要向同一个共享块写入不同内容，写时复制（copy-on-write）隔离这些修改。

~~~mermaid
flowchart LR
    L0["Logical block 0 · token 1–4"] --> P7["Physical block 7 · full"]
    L1["Logical block 1 · token 5–7"] --> P1["Physical block 1 · one free slot"]
    L2["Logical block 2 · when token 9 is processed"] -.-> P3["Another physical block"]
~~~

每个请求的最后一块仍可能有空位，块表与间接访问也有成本。好处是按实际长度增长，不必为每条请求预留连续的最大序列区。更多请求可以同时驻留并参与批处理。原论文报告的是其 2023 年工作负载和对照系统上的吞吐量与时延。其独立注意力内核的微基准也测到了额外延迟。现代引擎的分页思想仍可用，具体计算后端按模型、卡与引擎版本选择。vLLM 将原 CUDA 内核的设计页标为历史说明。 [Kwon et al., arXiv v1，§§4.2–4.5、§6](https://arxiv.org/html/2309.06180v1) · [§7.1、图 18(a)](https://arxiv.org/html/2309.06180v1#S7.SS1) · [vLLM 原 PagedAttention 内核说明](https://docs.vllm.ai/en/latest/design/paged_attention/)

### Tune the stage that misses its target / 优先调超出目标的阶段

| 观察到的限制 | 优先试什么 | 验证边界 |
| --- | --- | --- |
| 请求已到但 GPU 尚未开始工作 | 分开测排队、输入组装、分词和传输 | 只有分词确实占关键路径时，再换 tokenizer 后端或提高 CPU 处理能力。保持相同 token 序列和特殊词元规则。 |
| 冷请求的长 prompt 首 token 慢 | 用支持当前卡和模型的内核，减少无用输入，比较长 prefill 分块预算 | 记录 TTFT 和排队时间。把 prefill 切块可以让活跃 decode 插入，长 prompt 自己可能等更久。 |
| 重复的长 prompt 首 token 慢 | 让稳定的聊天模板或文档放在共同前缀，用引擎的 prefix cache | 检查复用 token 数和命中率。只复用语义上相同还不够，缓存要匹配实际 token 序列和模型状态。 |
| 活跃序列经常碰显存上限 | 先限制最大活跃长度和并发，再试支持的 KV 精度、合适的模型或更多设备 | 跟踪实际 KV 占用、抢占与重算。CPU offload 可用更慢的传输换容量，测长请求的尾部时延。 |
| 短请求吞吐低，GPU 利用不足 | 连续批处理在迭代之间补进新请求并移除已完成请求 | 同时观察排队和 p95 首 token，扩大批次也可能让单条请求等更久。 |
| Decode 的词元间隔过长 | 按输出长度、活跃序列数分桶。测带宽，再比较 KV 或权重量化、受支持的推测解码 | 推测解码先提议一批 token 再由目标模型验证。收益取决于接受率、批次和验证成本，需对质量与延迟共同回归。 |

vLLM V1 启用 chunked prefill 后把大 prefill 切成小块、与 decode 混合调度，并优先处理已排队的 decode。其 token 预算影响 TTFT 和词元间隔，参数应按服务流量测试。vLLM 的跨请求 prefix cache 用已完成块及其前缀身份做复用，适配器、多模态内容和租户隔离都要与部署一致。可使用独立缓存范围或引擎支持的租户盐值隔离共享。跨请求命中减少 prefill 工作，仍要生成新结果。应用层的响应缓存是另一种优化，命中后可能跳过整个模型调用。文档核对于 2026-11-06。 [vLLM Optimization and Tuning](https://docs.vllm.ai/en/stable/configuration/optimization/#chunked-prefill) · [vLLM v0.25.0 Prefix Caching](https://docs.vllm.ai/en/v0.25.0/design/prefix_caching/) · [vLLM Speculative Decoding](https://docs.vllm.ai/en/latest/features/speculative_decoding/)

若分块后长 prefill 仍影响 decode 时延，可以评估预填充与解码分池（prefill/decode disaggregation）。分池可以独立调整两边容量，但每条请求的 KV 状态要从 prefill worker 传给 decode worker。把传输与排队纳入 TTFT 和吞吐测试。DistServe 的收益来自论文测试的请求分布、互连与时延目标。 [DistServe](https://arxiv.org/abs/2401.09670)

做一组固定流量回放。记录模型版本、精度、GPU、输入和输出长度分布、并发与到达速率、冷暖缓存比例。比较 **TTFT**（请求到首词元）、**ITL**（输出词元之间的间隔）、端到端 p95、吞吐和满足时延目标的请求数。能处理更多请求但超出交互时延的批次没有解决交互负载的问题。测量由 [vLLM Benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/) 示例和[应用级时延与成本](#4.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F)分别覆盖服务内和端到端两层。
## 4. How do you reduce AI application latency and cost without weakening task quality? / 如何在不损害任务质量的前提下降低 AI 应用的时延与成本？

**Core explanation / 核心解释：** First measure where end-to-end time and cost accumulate, then change one layer at a time against a fixed task-quality bar. Queueing, context assembly, retrieval, model input/output, tools, retries, and operations have different costs; token price alone is not total cost, and faster partial output is not necessarily faster completion. / 先测量端到端时间和成本分别累积在哪些环节，再以固定任务质量门槛为准逐层调整。排队、上下文组装、检索、模型输入与输出、工具、重试和运维成本各不相同；token 单价不等于总成本，更快看到部分输出也不代表更快完成。

**Key terms / 关键术语：** time to first token (TTFT) / 首 token 时延；queue time / 排队时间；response cache / 响应缓存；prompt cache / 提示缓存；continuous batching / 连续批处理；quantization / 量化；distillation / 蒸馏。

### How can you reduce latency and cost? / 如何降低时延与成本？

Measure queueing, context assembly, retrieval, model input and output, tools, and retries separately. Track latency distributions and TTFT alongside throughput, queue time, and cost per completed task. Hold the task-quality bar constant: a cheaper route that fails more often may increase retries, escalations, and human review.

The application architecture owns run status, deadlines, and recovery; see [How can a production AI run survive disconnections and worker failures? / 生产运行如何经受断连与故障？](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F). Define the success measure before comparing optimizations with [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F).

#### Which optimization should you test? / 应先测试哪种优化？

- **Shorten or select context / 缩短或筛选上下文：** include relevant material and limit unnecessary history. Measure whether evidence or task quality is lost. See [Context Engineering Principles / 上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F).
- **Cache / 使用缓存：** exact-response or semantic response caches can avoid model work on a safe hit. Require compatible permissions, freshness, tenant, locale, and policy version. For example, “What is the refund policy in the US?” and “What is the refund policy in the EU?” can have similar embeddings but different correct answers. Similarity alone does not prove a response is reusable.
- **Route requests / 请求路由：** use a lower-cost candidate only for cases where it meets the measured quality bar. Include classifier errors, added latency, fallback frequency, and maintenance in the comparison. Candidate fit belongs to [Model Selection and Ecosystem / 模型选择与生态](#5.%20How%20should%20you%20choose%20a%20model%20for%20a%20task%20and%20its%20deployment%20constraints?%20/%20%E5%A6%82%E4%BD%95%E6%A0%B9%E6%8D%AE%E4%BB%BB%E5%8A%A1%E4%B8%8E%E9%83%A8%E7%BD%B2%E7%BA%A6%E6%9D%9F%E9%80%89%E6%8B%A9%E6%A8%A1%E5%9E%8B%EF%BC%9F).
- **Inference batching / 推理批处理** — A serving engine can admit and retire sequences between decoding steps. [GPU serving capacity / GPU 推理容量](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) explains how that affects memory, throughput, and per-request latency. A provider's asynchronous Batch API is a job interface for requests that tolerate delayed completion. It exposes no live inference scheduling contract.
- **Quantization / 量化：** represent weights, and in some methods activations, with fewer bits. This can reduce model memory and data movement, and may improve inference speed when the hardware and kernels support the chosen format. Quantization error can affect quality, and lower precision does not guarantee faster end-to-end service; evaluate the exact model, quantizer, hardware, and workload.
- **Distillation / 蒸馏：** train a smaller student on outputs or softened targets from a larger teacher over chosen inputs. A student may reduce serving cost or latency, but can lose capabilities or fail outside the distillation set. Include teacher/data generation and evaluation in the cost, and test on held-out tasks before replacement.
- **Stream responses / 流式返回：** streaming can improve perceived responsiveness and TTFT; it does not necessarily reduce total generation time or work. The browser's treatment of partial output is covered in [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md).

Provider features such as prompt caching, batch jobs, context limits, and prices vary by model and API and can change. Verify current documentation for the exact deployment. Compare total cost, including inference, retrieval, storage, engineering, evaluation, and operations.

#### A teaching calculation for cache cost / 缓存成本教学算例

Assume 1,000 model calls, each with 1,000 input tokens and 200 output tokens. For this arithmetic example only, assume uncached input costs $2 per million tokens, cached input costs $1 per million, and output costs $8 per million. These are invented teaching values, not current provider prices; ignore cache-write, storage, retrieval, and other fees.

Without caching, the token charge is:

$$
1{,}000 \times [(1{,}000 \times \$2) + (200 \times \$8)] / 1{,}000{,}000 = \$3.60.
$$

Suppose 400 calls share a 500-token prompt prefix and receive the assumed cached-input rate for that prefix. Prompt caching still processes the remaining input and generates all 200 output tokens. The assumed token charge becomes:

$$
600 \times \$0.0036 + 400 \times [\$0.0005 + \$0.001 + \$0.0016] = \$3.40.
$$

The $0.20 saving comes only from the lower rate on 400 × 500 cached input tokens. Output is still generated and billed.

An application-level response-cache hit is different: if 400 requests can safely reuse an exact, current response, those requests skip the model call, so the remaining 600 calls cost 600 × $0.0036 = $2.16 in token charges, before cache infrastructure costs. This assumes a valid exact hit; a semantic cache needs its own correctness and authorization checks.

OpenAI's [prompt caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching), checked 2026-10-15, likewise describes reuse of a prompt prefix while the model still generates a new response. Supported models, rates, and cache rules are provider-specific and change.

**Sources / 来源：** OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Frantar et al., [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323); Lin et al., [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978). Hinton et al., [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531). Yu et al., [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu), on iteration-level scheduling and selective batching. OpenAI, [Batch API](https://developers.openai.com/api/docs/guides/batch), checked 2026-10-15, documents its separate asynchronous job interface.
## 5. How should you choose a model for a task and its deployment constraints? / 如何根据任务与部署约束选择模型？

Choose from candidates that satisfy the task's hard constraints, then compare them on representative examples against an agreed quality bar. Measure latency, total cost, modality and format reliability, data handling, and operational fit. Model names, rankings, context limits, supported inputs, and prices change, so a public benchmark or provider label is a lead for investigation, not a lasting selection rule. / 先筛出符合任务硬性约束的候选模型，再用有代表性的样本和约定的质量门槛进行比较。测量任务效果、时延、总成本、模态与格式可靠性、数据处理和运维适配。模型名称、排名、上下文限制、输入能力和价格都会变化，因此公开基准或供应商标签只能帮助调查，不能作为长期固定的选择规则。

**Key terms / 关键术语：** task contract / 任务要求；held-out set / 保留集；hosted API / 托管 API；open-weight / 开放权重；hybrid deployment / 混合部署；routing / 路由。

### Start with the task contract / 从任务要求开始

Record what a successful result must do, what errors matter, and which operating conditions are fixed. Compare candidates on the same prompt, data, tools, and evaluation protocol where possible.

| Dimension | Questions to answer |
|---|---|
| **Task quality / 任务质量** | What counts as correct or useful? Which edge cases and refusal cases matter? |
| **Latency and availability / 时延与可用性** | Is the constraint about time to first response, full completion, or uptime? Which workload and region are representative? |
| **Cost / 成本** | Include input and output usage, retries, retrieval, hosting, support, and evaluation—not just one token rate. |
| **Inputs and outputs / 输入与输出** | Does the task require text, image, audio, or other modalities? Are schemas or tools supported for this exact model and API? |
| **Data handling / 数据处理** | What do the contract, configuration, retention policy, and deployment boundary allow? “Hosted” or “open-weight” alone does not answer this. |
| **Operations / 运维** | Who owns scaling, updates, monitoring, security patches, and incident response? |

Public benchmarks can help generate a shortlist when their task and protocol are relevant. They do not establish performance on a different prompt, data distribution, API configuration, or deployment. Keep an application-specific held-out set and report its sample scope and uncertainty. [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) explains how to choose task criteria and compare changes.

### Model tiers are shorthand, not a catalog / 模型档位只是简称，不是目录

Teams sometimes use labels such as **frontier**, **balanced**, and **fast** to describe rough cost, latency, and capability tradeoffs within a provider's current catalog. Those labels are not shared standards: a “fast” model can be the better choice on a narrow task, and a “frontier” label does not prove quality on yours. Avoid copying an undated model list or treating a prior ranking as a current fact. Verify the exact model ID, supported API features, context limit, and pricing in the provider's current documentation when making a real selection.

### Hosted API, open-weight, or hybrid? / 托管 API、开放权重还是混合部署？

| Approach | Potential advantages | Costs and constraints to compare |
|---|---|---|
| **Hosted API / 托管 API** | Quick access to managed inference and model updates; less serving infrastructure to operate. | Data flows and retention depend on provider terms and configuration; usage, rate limits, availability, and model lifecycle are provider-controlled. |
| **Open-weight deployment / 开放权重部署** | More control over serving location, model version, and infrastructure choices. | A weight license is not automatically an open-source license or permission for every use. The operator owns hardware, serving, security, scaling, and updates. |
| **Hybrid / 混合部署** | Different models or environments can serve distinct workload classes. | Adds routing, evaluation, observability, policy consistency, and failure paths across systems. |

This is an eligibility and trade-off comparison, not a universal deployment ranking. Edge, self-hosted capacity, and detailed operating responsibilities have their own constraints; see [AI Deployment Patterns / AI 部署模式](#6.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F).

Do not pick a hosting pattern from API spend alone. A useful estimate is:

$$
\text{total cost} \approx \text{inference usage} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and risk controls}
$$

Compare the same workload, quality target, peak traffic, and data constraints. A provider API may suit rapid iteration; self-hosting may suit a real data-control or workload need; edge deployment can help when offline operation or device constraints dominate. The break-even point depends on the actual workload and people costs.

### Route by measured need / 按实测需求路由

Routing can send simple, low-risk requests to a cheaper model and reserve a more capable option for cases that benefit from it. First measure whether the router's errors, added latency, and maintenance are outweighed by the savings. Use a task-relevant fallback when routing confidence is insufficient, and ensure high-impact operations still pass application-side authorization. Do not label “classification,” “reasoning,” or “extraction” as automatically easy or hard across all models.

Routing and other service optimizations need a fixed quality bar and end-to-end measurements; see [How to reduce AI application latency and cost / 如何降低 AI 应用时延与成本](#4.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F). To connect versioned results and user feedback to an improvement or rollback decision, see [Production observability and feedback / 生产可观测性与反馈](#20.%20How%20do%20you%20monitor%20a%20production%20AI%20feature%20and%20turn%20feedback%20into%20a%20safe%20improvement?%20/%20%E5%A6%82%E4%BD%95%E7%9B%91%E6%8E%A7%E7%94%9F%E4%BA%A7%E4%B8%AD%E7%9A%84%20AI%20%E5%8A%9F%E8%83%BD%E5%B9%B6%E5%AE%89%E5%85%A8%E5%9C%B0%E6%94%B9%E8%BF%9B%EF%BC%9F).

### Multimodal capability / 多模态能力

“Multimodal” does not specify which input or output a model supports or how well it handles a task. Test the actual modality and input shape—such as a chart, scanned document, spoken utterance, or video sample—under the target API. Check model documentation for supported formats, limits, and feature combinations at the time of deployment.

### Related notes / 相关笔记

- [AI Deployment Patterns / AI 部署模式](#6.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F) compares hosted, self-hosted, edge, and hybrid operating patterns.
- [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) defines run identity, persistence, and recovery behavior across request channels.
- [Context Engineering Principles / 上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) covers token budgets and provider-specific prompt caching.
- [Fine-tuning Strategies / 微调策略](#17.%20%E4%BD%95%E6%97%B6%E5%BA%94%E5%BE%AE%E8%B0%83%E6%9D%A5%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F) distinguishes behavior adaptation from maintained external knowledge.
- [RAG Architecture and Implementation / 检索增强生成](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers current or access-controlled external evidence.

### Sources / 来源

- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Its guidance treats prompting, context, fine-tuning, and evaluation as task-specific optimization levers rather than a universal linear ladder.
- For current OpenAI model IDs and feature support, consult the changing [Models documentation](https://developers.openai.com/api/docs/models), checked 2026-10-15.
## 6. When should an AI application use a hosted API, self-hosting, edge, or hybrid deployment? / AI 应用何时应选托管 API、自托管、端侧或混合部署？

**Core explanation / 核心解释：** Compare deployment patterns against the same workload, task-quality bar, data boundary, peak demand, and operational requirement. Hosted inference can reduce serving work; self-hosting increases control while transferring capacity and on-call responsibility to the team; edge and hybrid patterns answer distinct device or data-boundary needs. No deployment label by itself establishes lower total cost or better privacy. / 应在同一工作负载、任务质量门槛、数据边界、峰值需求和运维要求下比较部署方式。托管推理可以减少服务维护；自托管增加控制力，也把容量和 on-call 责任交给团队；端侧和混合部署分别回应设备或数据边界需求。仅凭部署名称不能证明总成本更低或隐私更好。

**Key terms / 关键术语：** hosted API / 托管 API；self-hosted / 自托管；edge / 端侧；hybrid / 混合部署；total cost of ownership / 总拥有成本。

### API, self-hosted, edge, or hybrid — how do you pick a deployment pattern? / 托管 API、自托管、端侧或混合部署——如何选择？

| Pattern | Useful when | Costs and constraints |
|---|---|---|
| **Hosted API / 托管 API** | Managed inference and quick iteration fit the task. | Review provider terms, model lifecycle, feature support, rate limits, availability, and per-use cost. |
| **Self-hosted / 自托管** | Control over serving location, model version, and infrastructure is a real requirement. | The team owns capacity, scaling, security updates, model serving, observability, and on-call response. |
| **Edge / 端侧** | Offline use, local latency, or device-level data handling matters. | Compute, battery, memory, device coverage, updates, and supported model size constrain the design. |
| **Hybrid / 混合部署** | Distinct workloads need different data or serving boundaries. | Routing and duplicated operations add complexity; define fallback and consistent policy behavior. |

### How should total cost and operational fit be compared? / 如何比较总成本和运维适配？

A useful estimate is:

$$
\text{total cost} = \text{inference} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and controls}
$$

There is no universal spend threshold for switching to self-hosting. Estimate with actual traffic, peak demand, staffing, quality requirements, and the full operating burden. Edge and hybrid choices likewise depend on device and data constraints, not just a latency label.

The choice also depends on which model candidates meet the task contract. See [Model Selection and Ecosystem / 模型选择与生态](#5.%20How%20should%20you%20choose%20a%20model%20for%20a%20task%20and%20its%20deployment%20constraints?%20/%20%E5%A6%82%E4%BD%95%E6%A0%B9%E6%8D%AE%E4%BB%BB%E5%8A%A1%E4%B8%8E%E9%83%A8%E7%BD%B2%E7%BA%A6%E6%9D%9F%E9%80%89%E6%8B%A9%E6%A8%A1%E5%9E%8B%EF%BC%9F) for comparing task quality, modality, deployment constraints, and measured routing. For the run identity and recovery behavior that should remain stable across deployment patterns, see [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F).

For self-hosting, estimate the peak number and length of active sequences and then measure fit on the intended hardware. [GPU serving capacity / GPU 推理容量](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) shows how to size KV memory and compare batching under a latency target.

**Source boundary / 来源边界：** This note summarizes the deployment comparison already present in the AI Application Architecture source. Provider features, terms, prices, capacity, and availability are time- and workload-specific; verify the exact provider or serving stack when making a current deployment decision. It does not make a universal cost or privacy ranking.
## 7. How do you write a prompt that makes a task clear and testable? / 如何编写清楚且可检验的任务提示词？

A useful prompt makes the task, necessary context, constraints, and expected output clear. Add examples or structure when they address a measured failure. Prompt text can guide model behavior, but it cannot enforce access control, guarantee factual accuracy, or replace application validation. / 有效提示词要清楚说明任务、必要背景、约束和输出要求。只有在示例或结构能解决实测问题时，才加入它们。提示词能引导模型，但不能执行访问控制、保证事实正确，也不能替代应用校验。

**Key terms / 关键术语：** instruction / 指令；context / 上下文；few-shot example / 少样本示例；output contract / 输出约定；structured output / 结构化输出；validation / 校验。

### The “capable intern” heuristic / “能干的实习生”启发式

Treat the model as capable of using the information and tools actually supplied, but unaware of unstated product rules, source freshness, user permissions, or the format expected by a downstream system. State those requirements explicitly when they matter.

| Vague request | More useful instruction |
|---|---|
| “Handle the refund.” | “Look up the sample order, check the current refund policy, and explain the next step. The application must authorize any refund action before execution.” |
| “Classify the ticket.” | “Choose billing, technical, or general. If the message does not contain enough evidence, return needs_review.” |
| “Summarize the document.” | “Return three bullets about the decisions and open questions. Do not add claims absent from the supplied document.” |

These examples illustrate clarity; they do not imply that a prompt can verify an order, authorize a refund, or make a summary factually correct. The runtime must perform those checks.

### A practical prompt checklist / 提示词检查清单

Include only what helps this task:

1. **Goal / 目标：** State the requested result and audience.
2. **Relevant context / 相关背景：** Supply rules, terminology, source material, or assumptions the model cannot infer.
3. **Inputs / 输入：** Identify the content to transform and delimit untrusted source text.
4. **Constraints / 约束：** Explain required coverage, exclusions, uncertainty handling, and what should trigger a question or handoff.
5. **Examples / 示例：** Add aligned positive, negative, or edge examples when they reduce ambiguity.
6. **Output contract / 输出约定：** Specify fields, format, length, language, and validation expectations.
7. **Tools and side effects / 工具与副作用：** Explain intended tool use, while the application independently enforces permissions and business conditions.

This list is an organizing aid, not a universal seven-layer prompt architecture. Some APIs distinguish system, developer, and user messages; use the roles and precedence defined by the exact API. Put dynamic data in the request context rather than hard-coding user records in reusable instructions.

### Make constraints and examples useful / 让约束和示例真正有用

“Be concise” may be sufficient for a simple chat. A downstream parser may need a precise schema, while a support response may need an uncertainty path. More text is not automatically better: conflicting examples, repeated rules, or irrelevant context can hurt.

Use an example that demonstrates the intended boundary, not only the easiest typical input. If examples and instructions disagree, the model may follow the wrong pattern. Keep examples synthetic and avoid real customer records or secrets.

### Structured output / 结构化输出

For machine-consumed output, prefer an API-supported schema-constrained mode when it fits the task. In the OpenAI API documentation checked on 2026-10-15, Structured Outputs supports schema adherence for supported schemas and models; JSON mode guarantees valid JSON syntax but not adherence to an application schema. Refusals, incomplete responses, unsupported schema features, and semantic errors still need handling. Schema conformance does not prove that a field is true, authorized, or safe to execute. If the chosen API cannot enforce the schema, parse, validate, and use a bounded retry or explicit failure path.

For human-readable output, headings, bullets, XML tags, or code fences can make sections easier to interpret. Delimiters help organize content; they are not a security boundary and do not guarantee valid machine output.

**Small output contract / 简单输出约定:**

~~~json
{
  "summary": "A short account of the supplied text",
  "category": "billing",
  "needs_review": false
}
~~~

Application code should check allowed categories and required fields, and verify any consequential claim against its source. For the broader distinction between task success, factual correctness, source support, and instruction adherence, see [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F).

### Optional organization pattern / 可选组织方式

Some teams group a long instruction by general-to-specific concerns. The following is a checklist, not a standard that every prompt needs:

| Section | What it contains |
|---|---|
| **Role and task context / 角色与任务背景** | Work setting and goal. |
| **Behavior / 行为** | Tone and response style. |
| **Tool guidance / 工具说明** | Intended use and limits of available tools. |
| **Procedure / 流程** | Steps that are useful to explain to the model. |
| **Output / 输出** | Format and length. |
| **Safety reminders / 安全提醒** | Human-readable reminders; code still enforces authorization and stop conditions. |
| **Request-specific context / 本轮背景** | Current task data and state, supplied only when needed. |

Do not put real names, ticket numbers, secrets, or private histories in a reusable prompt. Use a synthetic record when illustrating the format.

### Related notes / 相关笔记

- [Advanced Prompting Techniques / 高级提示技巧](#8.%20Which%20prompting%20technique%20should%20you%20try%20when%20a%20simple%20prompt%20fails?%20/%20%E7%AE%80%E5%8D%95%E6%8F%90%E7%A4%BA%E5%A4%B1%E8%B4%A5%E6%97%B6%E5%BA%94%E5%B0%9D%E8%AF%95%E5%93%AA%E7%A7%8D%E6%8F%90%E7%A4%BA%E6%8A%80%E5%B7%A7%EF%BC%9F) covers optional methods for failures that a clear baseline prompt does not resolve.
- [Context Engineering Principles / 上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains how to select and update the full information available to each inference.
- [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) explains why prompts cannot replace runtime authorization and stop controls.

### Sources / 来源

- OpenAI, [Model optimization: write effective prompts](https://developers.openai.com/api/docs/guides/model-optimization#write-effective-prompts), checked 2026-10-15.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. API behavior and supported schema features can change.
## 8. Which prompting technique should you try when a simple prompt fails? / 简单提示失败时应尝试哪种提示技巧？

Start with a clear, simple prompt, identify the failure on representative cases, and add only the method that addresses it. Few-shot examples, reasoning prompts, self-consistency, tool loops, prompt chains, and prompt generation can add tokens, calls, or control-flow complexity. Compare each change with the simpler baseline and application-side checks; published results support claims only for the tasks and setups actually evaluated. / 先用清楚、简单的提示词建立基线，再从有代表性的失败样本中定位问题，只增加能应对该问题的方法。少样本示例、推理提示、自一致性、工具循环、提示词链和提示词生成都会增加 token、调用或控制流复杂度。每种改动都应与简单基线及应用校验比较；论文结果只支持其实际评估过的任务和设置。

**Key terms / 关键术语：** zero-shot / 零样本；few-shot / 少样本；chain-of-thought (CoT) / 思维链；self-consistency / 自一致性；ReAct / 推理与行动；prompt chaining / 提示词链；meta-prompting / 元提示。

### When should you use few-shot vs. zero-shot prompting? / 何时使用少样本或零样本提示？

Start with a clear zero-shot instruction for a simple, well-defined task. Add a few examples when they resolve ambiguity, demonstrate a non-obvious label boundary, or show a required output format. Keep examples representative and include meaningful edge cases. More examples can consume context and can also bias the model toward an accidental pattern.

**Zero-shot / 零样本:**

~~~text
Classify the sentiment as positive, negative, or neutral.
Review: "The product arrived late, but the quality exceeded expectations."
Return one label.
~~~

**Few-shot / 少样本:**

~~~text
Classify each review as positive, negative, or neutral.
"Terrible experience, never buying again." → negative
"Exactly what I needed. Fast shipping." → positive
"It's okay. Nothing special." → neutral
"The product arrived late, but the quality exceeded expectations." →
~~~

For extraction, examples can demonstrate how a date or amount should be normalized. Keep them synthetic; validate required fields, allowed values, and source evidence in application code. Measure the example/no-example variants on the same held-out cases rather than assuming few-shot is more reliable.

### What is chain-of-thought, and when is it useful? / 什么是思维链，何时有用？

Chain-of-thought (CoT) prompting asks for intermediate reasoning text before a final answer, often through examples or an instruction. Research found gains on some multi-step arithmetic and reasoning benchmarks under particular model and prompt conditions. The result is task- and model-dependent: asking for step-by-step text does not guarantee correct reasoning, and a written rationale is not proof that it faithfully describes the model's internal computation.

A small arithmetic illustration is 4 × $2 + 2 × $3 = $8 + $6 = $14. A model may give a concise answer, a worked explanation, or an incorrect derivation. Verify consequential arithmetic with code or another trusted method.

OpenAI's reasoning-model guidance, checked 2026-10-15, recommends trying a straightforward prompt first; asking for step-by-step reasoning can be unnecessary or counterproductive for those models. API behavior differs by provider and model, so evaluate the actual target rather than carrying a prompt recipe across systems.

### What is self-consistency? / 什么是自一致性？

Self-consistency samples multiple candidate reasoning answers and aggregates their final answers, often by a majority vote. The research paper reported improvements on several tested reasoning benchmarks. It can help when the candidates make partly independent errors, but repeated samples can agree on the same wrong answer. Use a task-specific verifier for important results.

**Illustration, not model output / 示意，不是模型实测输出：** For 17 × 23, two valid decompositions are 17 × (20 + 3) = 340 + 51 = 391 and (10 + 7) × 23 = 230 + 161 = 391. If sampling several candidates, normalize equivalent answers before aggregation; voting does not replace checking.

Multiple samples increase token use and usually require more inference work. Exact cost and wall-clock impact depend on batching, provider behavior, and the selected model. Compare accuracy, latency, and cost with a single answer on the target task.

A model can also adapt its next action to a tool's observed result. See [the ReAct decision loop / ReAct 决策循环](#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF) for when that feedback loop is worth adding and how the runtime controls it.

### When should you chain prompts? / 何时串联提示词？

Use a fixed prompt chain when the task has separable steps and code can validate, branch, retry, or stop between them. If the sequence is known, developer-controlled stages can be easier to inspect than an open-ended agent loop. Each model call can still be wrong; validate intermediate outputs and test the whole chain. For broader workflow and delegation patterns, see [Orchestration Patterns / 编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F).

**Outline → validate → write / 大纲 → 校验 → 写作:**

1. Ask for an outline in a declared schema.
2. Parse it and check required sections and constraints in application code.
3. If valid, ask for a draft based on the outline; otherwise return an explicit failure or a bounded correction request.

~~~python
outline = call_model(make_outline_prompt(topic))
parsed = parse_schema(outline)
if not parsed.ok:
    return validation_error(parsed.issues)
if not deterministic_checks(parsed.value):
    return validation_error("outline violates required section rules")
return call_model(make_draft_prompt(parsed.value))
~~~

If five stages each succeed with probability 0.95 and failures are independent, the probability that all five succeed is 0.95⁵ ≈ 0.774. Real failures may be correlated, and retries or gates change the result; measure the actual workflow instead of treating this illustration as a reliability estimate.

### What is meta-prompting? / 什么是元提示？

Meta-prompting uses a model to generate candidate instructions or revise an existing prompt in response to concrete failures. Treat either output as a candidate. Evaluate variants on development examples, inspect failures, and keep a final held-out set untouched until selection; repeated tuning against the same set can overfit it.

Automatic Prompt Engineer (APE) is one research approach to generating and selecting instruction candidates for evaluated tasks. The templates here are a lightweight human-directed workflow, not a reproduction of that method or its reported results.

**Candidate generation / 生成候选提示词:**

~~~text
Task: Classify a support message as billing, technical, or general.
Success: Choose the supported category; return needs_review when evidence is insufficient.
Inputs: Only the supplied message and category definitions.
Output: Return the category and needs_review as JSON.
Generate three materially different candidate instructions. For each, state which ambiguity it addresses. Do not claim the candidates have been tested.
~~~

**Failure-driven revision / 根据失败样例修订:**

~~~text
Current prompt:
[insert the current synthetic prompt]

Observed failure:
[insert a synthetic input and the incorrect output]

Expected behavior:
[state the correct output and why]

Revise only the instruction needed to address this failure. Preserve the task, output contract, and other constraints. Return the revised prompt and a short change note. This candidate still requires evaluation on examples not used to write it.
~~~

A practical loop is to define success criteria, generate or revise candidates, compare them on the same development set, review regressions and edge cases, then confirm the selected version on an untouched held-out set before deployment. Keep the evaluation data appropriate for the sensitivity and policy of the task. [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation design and acceptance evidence.

### Related notes / 相关笔记

- [Prompt Engineering Fundamentals / 提示工程基础](#7.%20How%20do%20you%20write%20a%20prompt%20that%20makes%20a%20task%20clear%20and%20testable?%20/%20%E5%A6%82%E4%BD%95%E7%BC%96%E5%86%99%E6%B8%85%E6%A5%9A%E4%B8%94%E5%8F%AF%E6%A3%80%E9%AA%8C%E7%9A%84%E4%BB%BB%E5%8A%A1%E6%8F%90%E7%A4%BA%E8%AF%8D%EF%BC%9F) covers clear instructions, examples, and output contracts.
- [Context Engineering Principles / 上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) covers the information available to each inference.
- [Agent Fundamentals / 智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F), [Orchestration Patterns / 编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F), and [Tool Design and Function Calling / 工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F) cover runtime tool loops and control flow.

### Sources / 来源

- Wei et al., [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903).
- Kojima et al., [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916).
- Wang et al., [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171).
- Zhou et al., [Large Language Models Are Human-Level Prompt Engineers](https://arxiv.org/abs/2211.01910), for the APE instruction-generation and selection approach.
- OpenAI, [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices), checked 2026-10-15. These instructions describe OpenAI reasoning models and should not be generalized to other APIs.
- OpenAI, [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation), checked 2026-10-15. This is an OpenAI-specific example of generating or revising prompt text, not evidence that a generated prompt performs better without task evaluation.
## 9. What should each model inference see, and what should the application persist? / 每次模型推理应看到什么，应用应持久化什么？

**Core explanation / 核心解释：** Context engineering selects, orders, and updates the instructions, tool definitions, history, retrieved evidence, observations, and relevant task state available to one inference. The application should keep authoritative long-term state outside the prompt and load only the information needed for the next step. Measure usefulness on the task: more context can add evidence, but also cost, delay, noise, and lossy summaries. / 上下文工程是在一次推理中选择、排序和更新模型可用的指令、工具定义、历史、检索证据、观察结果及相关任务状态。应用应把权威长期状态保存在提示词之外，只为下一步加载所需信息。应根据任务结果衡量上下文是否有用：更多内容可能补充证据，也会增加成本、时延、噪声和有损摘要风险。

### 提示工程与上下文工程

**提示工程（prompt engineering）** 关注如何组织指令和示例。**上下文工程（context engineering）** 关注每次推理实际提供给模型的整套信息，包括系统与开发者指令、工具定义、历史消息、检索材料、工具观察和任务状态。两者相互依赖：好指令不能补救缺失证据，更多材料也不能替代清楚的指令。[Anthropic 的上下文工程文章](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)把上下文视为每次推理都需要重新整理的动态集合，并建议用任务结果评估信息配置。

### Why is context a finite resource, and what's "lost-in-the-middle"?

**上下文资源有限，长文本的效能也会变化 / Context is finite, and long-context performance varies.**

模型能接收较长输入，不等于能同样可靠地使用任意位置的所有信息。上下文还受模型支持的窗口、输入成本、预填充时延、检索噪声与目标相关性影响。随着上下文增大，效果并非必然以一个固定速度下降，也没有适用于所有模型和任务的“30 轮”或 token 数阈值。

**Lost in the middle（中间迷失）** 是位置敏感性的一种实证现象。[Liu 等人的研究](https://arxiv.org/abs/2307.03172)在多文档问答和键值检索任务中观察到，模型对位于输入中部的信息有时不如位于开头或末尾的信息利用充分。它说明应在实际任务中测试长上下文与位置变化；不能据此断言所有模型总是更注意首尾，或某个 RAG 分块位置必然失败。

有效做法是选取足以完成当前子任务的高信号信息，给关键证据附来源或标识，并对模型、任务与提示结构做长上下文评估。注意力机制的理论复杂度不能单独证明某个系统会在特定上下文长度失效。

### 管理持续增长的上下文

下面的“缩减、外置、隔离”是实用整理方法，不是必须采用的固定分类。多数长任务会组合使用：

| 方法 | 何时使用 | 需要保留什么 |
|---|---|---|
| **缩减（reduce）** | 重复历史、冗长工具输出挤占当前任务空间 | 目标、关键决定、未解决问题、失败状态、资源 ID 与可追溯来源 |
| **外置（offload）** | 原始资料太大或跨越多轮/会话 | 文件、数据库或其他持久状态中的原始内容；上下文只保留可再次读取的路径、查询或 ID |
| **隔离（isolate）** | 一个任务需要独立研究，或当前历史混杂多个职责 | 工作者的目标、权限、输入与输出契约；主流程接收结论、证据和不确定性 |

**摘要与压缩：** 摘要有损。先保留稍后可能影响决策的事实，再删去重复内容；“订单已退款”不一定足以支持追问，可能还要留下订单号、金额、状态依据与操作 ID。原始记录可通过外部引用重新读取时，摘要就不必承担永久记忆的职责。Anthropic 建议在长任务中用 compaction、持久笔记和子智能体，并提醒过度压缩会丢失之后才显得重要的信息。

**按需加载（just-in-time retrieval）：** 保留轻量引用，在需要时再读取文件、网页或数据库，而非预先加载全集。这减少无关 token，但每次探索需要额外工具调用，并依赖检索能力和可用权限。对经常需要的稳定资料，也可先加载摘要，再按需查原文。[Anthropic 对按需检索与混合策略有详细说明。](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

Skills 与工具搜索也可渐进载入程序或能力；并行工具调用可以留在同一主循环中，不必因此创建 subagent。[Anthropic 关于把 subagent 折回主循环的文章（2026-10-22，“Using an agent loop with progressive disclosure”）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)描述了这种按需暴露方式。

**隔离上下文：** 子智能体不会天然共享同一份记忆。清楚传递目标、必要背景和结果格式；需要一致决策时，明确由主 agent 汇总和核对。切分依据应是任务边界、权限或可验证的并行收益，而不是把完整历史复制给每个工作者。按问题类型交接时，若下一步仍依赖先前约束或发现，摘要可能丢失细节；可先尝试在主循环中保留共享状态并按需加载专业流程，再评估是否需要分拆。[Anthropic 的 folding 文章，“Combining domain agents”](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)；决策方法见[编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

### How should a request preserve a reusable prefix? / 请求怎样保留可复用的前缀？

**KV cache 与 prompt caching 是相关但不同的复用机制 / KV cache and prompt caching are related but distinct reuse mechanisms.**

本节处理应用能控制的前缀布局。逐层 KV 载荷、分页和批处理见 [GPU 推理容量](#3.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F)。

**KV cache** 是自回归模型生成时保存先前 token 的 key/value 表示，以供同一次生成后续 token 使用。**Prompt caching（提示缓存）** 通常指推理服务在后续请求中重用相同前缀的计算。后者可降低特定服务和配置下的输入成本或首 token 时延；两者都不是模型的长期记忆，也不意味着缓存 token 在所有供应商中都按同一价格收费。

缓存规则依供应商、模型和 API 而异。以 [OpenAI 当前 API 文档](https://developers.openai.com/api/docs/guides/prompt-caching)为例，缓存匹配依赖渲染后的请求前缀和可用的缓存断点；工具名、描述、schema 或顺序变化可能让变化之后的前缀无法复用。改变前缀不等于每种服务都把整段历史全部丢弃，实际匹配边界、最小长度与生命周期需查对应文档。

- 将稳定指令和可复用资料放前面，把每次请求都会变的用户信息、时间戳放后面。
- 在 API 支持的状态模型中，追加消息通常比重写早期内容更利于复用；压缩或改写历史可能改变匹配前缀。
- 只有实测缓存命中率、总 token 成本与行为结果都合适时，才为缓存调整上下文布局。
- 若工具列表因权限变化而变，先保证能力配置正确；缓存优化不能成为保留过期权限的理由。

Manus 的[上下文工程经验](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)展示了稳定前缀、追加式历史和确定性序列化对其部署缓存的价值。这些是实践经验；不能把其价格、命中率或框架实现直接当作其他 API 的现行保证。

### 长任务中的目标、计划与失败记录

**目标重述（recitation）**：长循环会不断加入操作和观察。把精简的当前目标、已完成事项、下一步与阻塞项放到模型本轮可见的位置，并将权威状态保存在持久任务记录中，可降低目标在历史中被淹没的风险。

例如，维护一个短任务清单：完成登录校验修复；定位导致失败的输入；运行对应测试；记录仍未验证的路径。[Manus 公开了在其长循环中把 todo 写到近期上下文的做法](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)，而 Anthropic 也描述了使用持久笔记追踪长任务进度。该模式是有用的设计启发，不意味着所有 agent 都需要每轮重写清单，也不支持一个通用的平均工具调用次数。

**保留有用的失败证据：** 若后续决策需要知道刚才做过什么，保留精简的“尝试动作 → 错误或观察 → 当前状态”。这能让模型看到重试为何失败，但不会更新模型参数；只有在下一次推理时实际提供的记录才可能影响决策。无关日志、敏感数据和巨大堆栈应按需外置，并保留查询引用。压缩历史时，不要把会影响安全重试或后续确认的失败状态删掉。

**历史会变成示例：** 上下文里重复的动作—观察模式可能影响模型下一步模仿什么。Manus 描述了在批量审核 20 份简历时观察到重复操作，并提出用结构化变体打破模式；这仍是该团队的实践假设，没有足够证据把“改变格式”当作普遍解决方案。保持规范、易解析的序列化通常更利于复现与缓存；若评测发现重复行为，先精简或组织历史，再用任务集比较不同表示，不要无依据地注入格式噪声。

### 何时保留状态，何时重启探索 / Retain state or reset exploration

**核心解释 / Core explanation：** 保留可复用资产，与把全部历史带入每轮上下文，是不同的选择。Keeping reusable assets and carrying all past history into every context are separate choices.

下表是跨源工程综合，用于比较信息可见性与持久化选择，不构成统一架构或共同实验结论。

| 情形 | 状态选择与证据边界 |
|---|---|
| **同一任务的后续步骤** | 保留目标、接口、权限、验收条件、操作状态和影响安全重试的失败事实；将原始记录外置并保留可查 ID。步骤依赖同一约束时，先考虑主循环或明确交接。 |
| **有外部评分的开放搜索停滞** | 可从同一候选比较重启与继续搜索，并明确各自保留/移除的信息；停滞不自动构成通用重置规则。 |
| **跨 worker 复用产物** | 将带版本与来源的代码、测试、实验记录外置；按当前任务读取相关产物，不载入完整历史。持久资产和每轮可见上下文是不同选择。[GitSwarm v1（2026-10-04，§§2.2、3.3–3.4、4）](https://arxiv.org/html/2610.04862v1) |
| **跨任务复用 harness 经验** | 保存可复用组件和经验；新任务从共同基线开始，再检索与适配。[Harness² v1（2026-10-09，§2.3）](https://arxiv.org/html/2610.14224v1) |
| **接受系统级变更** | 保留已验收配置及其证据；后续候选仍需[重新验收](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。 |

[*Scaling Discovery Requires Forgetting* v1（2026-10-14，§§3.1–4.3、Appendix B p. 13、§6）](https://arxiv.org/abs/2610.20563v1) 的 Forget 同时清空 session 与候选搜索历史，只保留最佳候选及分数，以相同首轮指令重启。证据来自四项外部评分的优化任务、一个 harness/model 配置；它没有建立适用于一般任务的重置规则。

GitSwarm 用可分支的共享 Git 仓库和原子提交（atomic commit）保存中间产物。Git 的物理父提交（physical parent）记录开始工作的树；强制字段 `informed_by=` 记录 worker 声明的语义来源，且必须包含 parent、可增加其他分支来源。这是来源追踪，不是因果证明。主要积累证据来自同题跨 episode；单独把已完成搜索的获胜提交作为种子，仍是同一 RMT 任务，不能外推成任意跨任务迁移。worker 使用的 LLM 在 run 中保持固定；架构搜索改进的是被研究的另一模型，不能写成 worker 权重自行学习。[GitSwarm v1（2026-10-04，§§2.2、3.3–3.4、4）](https://arxiv.org/html/2610.04862v1)

**工程建议 / Engineering advice：** 将代码、测试、实验结果和负面发现作为候选经验资产外存，并记录版本、适用条件与检查依据，按当前任务检索后复验。重启探索不应删除权威任务契约或未决外部操作状态；把审计记录留在提示词之外，并重新载入目标、接口、测试、权限、验收条件和必要的失败/副作用状态。“被读取或引用”不等于提升结果。外部资产持续保留而当前上下文选择性清理，是跨源工程综合，不是论文共同评测过的方案。

### 相关知识

- [智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：上下文、环境反馈和智能体执行循环如何连接。
- [编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：判断主循环、并行工具与独立 worker 的边界。
- [LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：比较历史保留、重启与跨运行变更。
- [工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：工具 schema 与执行结果也是上下文的一部分。
- [RAG 架构与实现](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)：了解何时预先检索、何时按需检索。
## 10. How do you retrieve and use authorized external evidence in a grounded answer? / 怎样检索并使用经过授权的外部证据生成有依据的回答？

**Short answer / 简答** — Define what sources the caller may use, retrieve from the eligible corpus, and give the model a small set of traceable passages. Validate each material claim against those passages and abstain when the evidence is missing or conflicting. Measure candidate recall, evidence selection, and final answers separately so you can fix the stage that failed. / 先确定调用者能使用哪些来源，再从有资格的文档中检索，把少量可追溯的证据交给模型。用原文核对关键主张，证据不足或冲突时说明无法确定。分别衡量候选召回、证据组装和最终回答，才能知道该修哪一层。

### When to use retrieval, long context, or fine-tuning / 如何选择检索、长上下文或微调

These techniques solve different constraints and can be combined:

| Approach | Useful when | Main tradeoff |
|---|---|---|
| **RAG / 检索增强** | The application needs to select evidence from a source that is larger than one prompt, changes over time, or has source-level access rules. | Adds ingestion/synchronization and retrieval work. Retrieval can miss, return stale or conflicting material, or select content the generator does not use well. |
| **Long context / 长上下文** | The relevant material can be supplied together and the task benefits from reasoning across that material without a separate search step. | The model must still find and use the relevant parts. Context length, position effects, and input-token cost depend on the model and workload. |
| **Fine-tuning / 微调** | Repeated examples can teach a desired response pattern, task behavior, or format. | It does not by itself provide a reliable, current source of external facts. Use retrieval as well when answers must cite or reflect a maintained corpus. |

There is no universal token-count cutoff. Compare the methods on representative questions, including required evidence, source updates and permissions, answer quality, end-to-end latency, and cost. In one EMNLP 2024 comparison, long-context models had higher average performance when sufficiently resourced, while RAG cost less in that evaluated setting; this result is not a general ranking of all systems. Long-context models can also be position-sensitive on tested tasks. [Li et al.](https://arxiv.org/abs/2407.16833), [Liu et al.](https://arxiv.org/abs/2307.03172)

### Pipeline / 检索增强生成的流程

Follow one synthetic question through the system. A caller asks “What is the cancellation window for a self-serve annual plan in the EU?” The authoritative current EU policy says 14 calendar days. The caller can read both the current EU and US policies. A withdrawn EU revision used 30 days, and another tenant’s contract is outside the caller’s scope.

~~~mermaid
flowchart LR
    Source["Source document and version"] --> Index["Parse sections and index eligible passages"]
    Caller["Caller and question"] --> Scope["Compute authorization and policy scope"]
    Index --> Candidates["Retrieve candidates"]
    Scope --> Candidates
    Candidates --> Evidence["Rank, verify and assemble evidence"]
    Evidence --> Model["Generate with passage IDs"]
    Model --> Check["Check claims and citations"]
    Check --> Output["Return supported answer or abstain"]
~~~

1. **Index / 建索引.** Parse by section, keeping text and structural context such as table headers, product scope, and exceptions. Store document ID, version or effective date, section or offsets, and policy metadata for each passage. Synchronize edits, deletions, and permission changes. If revocation must take effect before the index catches up, recheck access against the authoritative policy before releasing text.
2. **Retrieve / 召回.** Compute the caller's authorized scope in trusted code. Apply authorization and effective-date constraints in each retrieval branch. Test which of the returned policies actually applies to the requested region and plan. The withdrawn revision and other tenant’s contract cannot become evidence. Search the eligible passages with a lexical baseline, a dense index when paraphrase matters, or both if evaluation shows the methods complement one another.
3. **Rank and assemble / 重排与组装.** Fuse rankings if using multiple retrievers, then consider a cross-encoder if useful candidates are being ranked below less applicable ones and evaluation shows a gain. Keep the most relevant passages with their source IDs and exact scope. If a chunk points at a parent section, check the parent’s access and version before adding it. The EU section gets priority over a broadly related billing FAQ. Fit the evidence to the token budget and preserve the qualification “self-serve annual.”
4. **Generate and check / 生成与核对.** Ask for an answer and passage IDs, then confirm that the cited passage really supports “14 calendar days” for the stated region and plan. An ID copied from the prompt is not proof of support. If only the US policy is present, report insufficient applicable evidence. When trusted passages conflict, apply a predefined authority/version rule or surface the conflict.

A missing passage at step 2 cannot be recovered by reranking at step 3. A retrieved passage can still be dropped by context assembly. Evidence that reaches the model can still be misread. Keeping the authorized candidate IDs, selected passage IDs, and output claims distinct makes those failures diagnosable. Treat the passages as data. Their text grants no additional permissions or tool authority.

### Embeddings and similarity / 向量表示与相似度

An embedding maps text to a vector for retrieval. Query and document encodings must follow a **compatible encoding contract / 兼容的编码契约**: their vector dimensions and learned space must support comparison, and each model’s query/document input format must be respected. This does not require identical encoder weights. Dense Passage Retrieval (DPR), for example, uses separate question and passage encoders. [Karpukhin et al.](https://arxiv.org/abs/2004.04906)

Changing document-side encoding, output dimensions, normalization, or preprocessing may require re-embedding or migrating the affected document vectors if they no longer meet the query/document contract. A query-side change alone does not necessarily require rebuilding the document index, but its compatibility and retrieval quality must be re-evaluated. Model choice should account for the language and task, query/document format, deployment and privacy constraints, input limits, latency, price, and performance on the target corpus. Avoid treating a model list or benchmark ranking as a permanent recommendation.

Common similarity measures are:

| Measure | Formula | Interpretation |
|---|---|---|
| **Cosine similarity / 余弦相似度** | $\frac{A \cdot B}{\lVert A \rVert \lVert B \rVert}$ | Compares vector direction and is invariant to vector magnitude. |
| **Dot product / 点积** | $A \cdot B$ | Depends on both direction and magnitude unless vectors are normalized. |
| **Euclidean distance / 欧氏距离** | $\lVert A-B \rVert_2$ | Measures distance; smaller values indicate closer vectors. |

The metric must match the model’s representation and the vector index configuration. For OpenAI’s normalized embeddings, cosine similarity and dot product produce the same ranking, and Euclidean distance also produces identical rankings; this equivalence should not be assumed for arbitrary embeddings. [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)

### Chunking / 文档分块

A **chunk / 文档块** is a retrievable unit derived from a source document. Chunking trades retrieval precision against context completeness: small chunks can isolate evidence but lose nearby qualifications; large chunks preserve surrounding context but can include irrelevant material. The useful size depends on source structure, parser quality, query mix, embedding model, and the generator’s context budget. There is no generally optimal token size or overlap ratio; evaluate choices on representative queries. A 2025 ACL Findings study documents how segmentation choices affect RAG behavior, while a 2026 chunking preprint found different tradeoffs in one SPLADE/Mistral-8B/Natural Questions setup. [Wang et al.](https://aclanthology.org/2025.findings-acl.422/), [Bennani & Moslonka](https://arxiv.org/abs/2601.14123)

| Strategy | Mechanism | Useful when | Limitation |
|---|---|---|---|
| **Fixed-size / 定长分块** | Split at a character or tokenizer-token limit; optionally retain overlap at boundaries. | A simple, predictable baseline is needed. | May cut across a sentence, table, code block, or concept. State whether the limit is characters or tokens. |
| **Recursive / 递归分块** | Try separators in order (for example, section breaks, newlines, then spaces) until parts fit a target length. | Text has natural separators and a generic baseline is appropriate. | The resulting chunk sizes vary and the separator hierarchy may not match the source structure. |
| **Semantic / 语义分块** | Group nearby sentences or passages and split at a semantic boundary, often using embedding similarity. | Boundary coherence is a measured problem worth extra indexing work. | Similarity thresholds and model choice affect results; it is not automatically more accurate. |
| **Document-aware / 结构感知分块** | Split on source structure such as headings, pages, sections, tables, or code syntax. | Structure carries meaning or links evidence across a document. | Depends on successful parsing and may still need size limits or a fallback splitter. |

**Character-count example / 字符长度示例：** LangChain’s current Python documentation shows `RecursiveCharacterTextSplitter` from the separate `langchain_text_splitters` package. With its default length function, `chunk_size` and `chunk_overlap` count characters, not tokens. The values below mirror a documentation example and illustrate the API; they are not universal RAG settings. Use a tokenizer-aware length function if the target constraint is model tokens. [LangChain documentation](https://docs.langchain.com/oss/python/langchain/knowledge-base)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # characters with the default length function
    chunk_overlap=200,     # characters retained across adjacent chunks
    add_start_index=True,  # preserve the source character offset
)
chunks = splitter.split_documents(documents)
```

Overlap can retain context across boundaries, but it also duplicates text and increases indexed content. Treat overlap as an evaluation parameter, not a mandatory fix. The right chunking choice can also depend on the query’s evidence shape; “query-dependent” does not mean document structure is irrelevant.

For the parent-child chunking design and its trade-offs, see “Parent-child retrieval / 父子分块检索” under Retrieval upgrades below.

### Dense, sparse, and hybrid retrieval / 稠密、稀疏与混合检索

**Dense retrieval / 稠密检索** embeds the query and chunks, then ranks chunks by vector similarity. It can match related phrasing even when wording differs, depending on the model and task. It can still miss exact identifiers, rare names, or relevant evidence.

**Sparse retrieval / 稀疏检索** ranks using lexical features. BM25 is a common term-based retriever and can be useful for exact strings such as error codes, product identifiers, and names. It may miss paraphrases whose vocabulary differs from the document.

**Hybrid retrieval / 混合检索** combines dense and sparse candidates or rankings. The methods can complement one another, but hybrid retrieval is not a universal default. A heterogeneous retrieval benchmark found BM25 to be a robust baseline; it also found that reranking and late-interaction systems performed strongly on average at higher computational cost. Results vary across tasks, so compare retrieval methods on the application’s queries. [BEIR](https://arxiv.org/abs/2104.08663)

**Reciprocal rank fusion / 倒数排名融合（RRF）** combines ordered lists. For a candidate $d$ with rank $r_i(d)$ in list $i$,

$$
\operatorname{RRF}(d)=\sum_i \frac{1}{k+r_i(d)}.
$$

A candidate contributes only from the lists that return it. In the example, lexical retrieval returns US, EU, FAQ and dense retrieval returns EU, Billing, US. With an illustrative $k=60$, EU scores $1/62+1/61$, above US at $1/61+1/63$. Fusion uses positions without calibrating a raw BM25 score against a cosine score. It sees only the returned candidate windows. Tune candidate depth, fusion and reranking on the same queries. [Cormack, Clarke & Büttcher](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf) · [Elasticsearch RRF reference](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)

A 2026 financial QA preprint compared ten approaches on text and tables. Its hybrid retrieval with cross-encoder reranking led its retrieval comparison, and BM25 was stronger than the tested dense baseline. That makes a good reason to test hybrid retrieval on mixed text and numeric questions. The main comparison indexed whole documents, so it does not settle passage size or performance on another corpus. [From BM25 to Corrective RAG, v1, §§III–IV](https://arxiv.org/html/2604.01733v1)

### Reranking / 重排

A **bi-encoder / 双编码器** independently encodes a query and each document, allowing document vectors to be indexed and searched efficiently. A **cross-encoder / 交叉编码器** processes a query-document pair together and returns a relevance score. Joint input permits a richer pairwise comparison, but scoring many candidates costs more than a vector lookup. Retrieval-plus-reranking is therefore a **recall then precision** pattern: retrieval proposes candidates, and reranking changes their order.

For example, a synthetic question about a sample policy might retrieve a broad candidate set, rerank those chunks against the question, then pass only a few supported passages to generation. Candidate depth and final context size are workload parameters. If evidence is not among the retrieved candidates, the reranker cannot add it. If reranking keeps the entire candidate set (candidate count equals final returned count), reordering alone does not change set-based precision@k, though it can affect rank-sensitive metrics and the order in which evidence reaches generation. Compare quality and latency across candidate depths instead of assuming a particular top-k is best. BEIR found strong average zero-shot performance for reranking architectures in its evaluated benchmark, with higher computational cost. [BEIR](https://arxiv.org/abs/2104.08663)

### Retrieval upgrades / 检索增强策略

Use these techniques to address a diagnosed failure, and evaluate each on the affected query set before combining them.

#### Query transformation / 查询改写

Rewrite or expand a query when the user’s wording does not align with the corpus vocabulary or when a compound request needs clearer subqueries. Query expansion can run several variants and merge results. Rewriting can also alter the user’s intent, so retain the original query and compare retrieval outcomes.

#### HyDE (Hypothetical Document Embeddings) / 假设文档嵌入

HyDE asks a language model to generate a hypothetical document in response to a query, embeds that hypothetical text, and uses the vector to retrieve real corpus documents. The generated document is a **retrieval intermediary, not answer evidence**; the original paper notes it may contain false details. HyDE was proposed for zero-shot dense retrieval when relevance labels are unavailable. It is not based on a general rule that short queries embed poorly near long passages. [Gao et al.](https://arxiv.org/abs/2212.10496)

#### Parent-child retrieval / 父子分块检索

Embed and retrieve child passages, then return their parent section as context. This can recover nearby definitions or qualifications that are useful to interpret the child evidence. Deduplicate parent sections and keep the final context within a budget; evaluate whether the broader passages help the query set.

#### Multi-step retrieval / 多步检索

For a question whose answer requires evidence from more than one source, retrieve an initial set, identify the unresolved relation or sub-question, and retrieve again. This can support multi-hop questions, but it adds retrieval or generation work. Stop when the needed evidence is present or when the remaining uncertainty should be reported rather than hidden by another search.

### Operations, evaluation, and failure diagnosis / 运行边界、评估与故障定位

#### Access, freshness, and trust boundaries / 权限、新鲜度与信任边界

RAG does not make a corpus private. Compute the caller’s permissions in trusted application code and enforce them in the retrieval/data-access layer before evidence reaches the model. Metadata filters can express attributes such as tenant, region, source, or date, but correctness of the policy and its enforcement belongs to the application. Track document identity and version so updates, deletions, and permission revocations do not leave stale chunks available. The index is only as fresh as its synchronization and processing path. [OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/), [OpenAI retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)

A logical authorization filter and the search engine’s scan order are different concerns. In pgvector, a SQL `WHERE` condition still gates what rows can be returned, but approximate HNSW or IVFFlat may scan candidates before applying that filter. With selective filters, measure authorized recall and the count of eligible rows. If needed, test iterative scans, a scoped index or partition, or exact search over a small authorized subset. Never relax the policy to fill a candidate quota. [pgvector filtering and iterative scans](https://github.com/pgvector/pgvector#filtering)

Treat all retrieved text as untrusted content. A document can contain direct or indirect instructions that influence the model. Delimiters and prompts may reduce confusion, but they do not guarantee protection. Do not let a retrieved passage authorize a data access or tool action; enforce permissions and validate actions outside the model. [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). For more on prompt injection and application boundaries, see [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

#### Evaluation / 评估

Measure retrieval and generation separately, then compare the complete system:

- **Candidate recall / 候选召回.** Label the source passages needed for each question and identify the version and caller. Recall@K is the share of those passages found in the first K candidates. MRR describes the rank of the first relevant candidate and cannot establish that a multi-part answer has every necessary passage.
- **Evidence and generation / 证据与生成.** Track which needed passages survive assembly. Then assess factual correctness, support for each claim and citation, and whether the answer abstains when the passage is missing or conflicting. RAGChecker illustrates claim-level decomposition for retrieval and generation diagnosis. [RAGChecker §§3–4](https://arxiv.org/abs/2408.08067)
- **System / 系统.** Track end-to-end latency and cost along with revocation and tenant-isolation regressions. Keep cases where the relevant-looking passage is unauthorized, expired, or for the wrong plan. Re-run the same cases across the lexical baseline, dense retrieval, hybrid fusion and reranking. Change one stage and retain the simplest configuration that meets the acceptance bar.

RAGAS and ARES illustrate multi-dimensional evaluation, including context relevance, answer faithfulness, and answer relevance; they are evaluation frameworks, not a complete universal score. Automated judges are useful signals and should be checked against representative human-reviewed examples. See [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F). [RAGAS](https://arxiv.org/abs/2309.15217), [ARES](https://arxiv.org/abs/2311.09476)

#### Diagnose from evidence / 根据证据定位故障

| Symptom | Inspect | Possible next step |
|---|---|---|
| The source does not contain the needed fact, or the current version is missing. | Source coverage, parsing, synchronization, deletion/version state. | Fix source ingestion or freshness; if the evidence is unavailable, report that limitation. |
| The evidence exists but is absent from retrieved candidates. | Caller filters, query interpretation, chunk boundaries, embedding/lexical retrieval, candidate recall. | Correct scope or ingestion first; then compare retrieval and chunking choices on the failing queries. |
| A useful candidate is retrieved but absent from the prompt. | Reranker order, deduplication, context assembly, and truncation. | Adjust ranking or evidence selection and verify that citations still map to source passages. |
| Evidence is in the prompt, but the answer is unsupported or contradicts it. | Conflicting passages, prompt instructions, model output, citation support, and whether the question is answerable. | Test prompt/model/evidence changes against the same cases; do not infer a specific internal cause from the answer alone. |

A practical debugging loop is: inspect the source and authorized candidates; inspect what reached the model; check answer claims against those passages; then change one retrieval or generation factor and evaluate the same cases. More context can add missing evidence or add noise, so “retrieve more” is a hypothesis to test, not a universal fix. Long-context performance can also depend on where relevant information appears. [Liu et al.](https://arxiv.org/abs/2307.03172)

### What carries forward from the original RAG paper? / 原始 RAG 论文留下什么？

Lewis 等人的 RAG 把可更新的非参数记忆（non-parametric memory）与参数化生成器结合起来。论文使用 DPR 检索 Wikipedia 向量索引，以 BART 生成，把检索到的文档当作潜变量。**RAG-Sequence** 对每篇文档分别计算整条答案的概率，再按文档权重求和。**RAG-Token** 对每个输出位置先按文档求和，再沿序列相乘。每种方法都按输入做一次 top-K 检索。RAG-Token 在自己的候选窗口内逐位置计算，逐词元改变文档贡献不等于逐词元重新检索。论文在当时的三项开放域问答上报告了相对基线的提升。 [Lewis et al., arXiv v4, §§2.1–2.5、§4.1 与表 1](https://arxiv.org/html/2005.11401v4)

今天的应用通常可独立更换检索器与生成模型，在生成前按权限和问题组装证据，再单独评估回答。值得继承的是把可更新证据与模型参数分离，以及测量检索和生成如何互相影响。业务权限、文档版本、重排和逐条引用验收是生产系统要另外实现的边界。

### Related notes / 相关笔记

- [Context Engineering Principles / 上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains context budgets and how placement can affect use of evidence.
- [Fine-tuning Strategies / 微调策略](#17.%20%E4%BD%95%E6%97%B6%E5%BA%94%E5%BE%AE%E8%B0%83%E6%9D%A5%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F) discusses adapting model behavior and combining it with external knowledge.
- [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation datasets, metrics, and review methods.
- [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) covers prompt injection, permission boundaries, and runtime controls.
## 11. How should an application execute a model’s tool request? / 应用应如何执行模型的工具请求？

**Short answer / 简答：** A tool call is a structured request from the model, not code execution or permission. The application must parse and validate it, check the caller’s authorization and current business state, execute the function, then return a useful result. Design for dependencies, side effects, and uncertain outcomes so recovery does not repeat an action blindly.

工具调用只是模型发出的结构化请求，不等于代码已经执行或用户已获授权。应用需要解析并校验请求，检查调用者权限和当前业务状态，执行函数，再把有用结果返回模型。设计时还要处理依赖、副作用和结果未知，避免恢复时盲目重复动作。

### 函数调用的生命周期

以下按 provider-neutral 方式描述，具体消息格式、角色名称、工具选择模式和结构约束因 API 而异：

1. 应用将对话状态与本轮可用工具定义发送给模型。
2. 模型返回普通内容，或返回包含工具名称与参数的调用请求。
3. 应用解析请求，校验参数，并按当前用户和业务状态授权。
4. 应用执行函数，将成功、错误或部分结果返回模型。
5. 模型依据结果继续调用工具、交接，或生成答复。

[OpenAI 函数调用指南](https://developers.openai.com/api/docs/guides/function-calling)将工具调用描述为模型请求与应用端执行之间的多步流程。结构化调用或严格 schema 可以减少格式错误，但不证明用户意图正确、权限充分、业务动作合理或外部操作已经成功。动作循环与控制权的整体关系见[智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)。

### 工具选择模式：OpenAI API 示例

OpenAI API 的 tool_choice 可控制模型是否以及如何选择函数。下表描述的是该 API 的行为示例，参数名和语义不能直接假定适用于其他 provider：

| 模式 | 行为 |
|---|---|
| auto | 默认模式；模型可调用零个、一个或多个函数。 |
| required | 要求模型至少调用一个函数。 |
| 指定函数（forced function） | 要求调用某个具体函数，例如 {"type":"function","name":"get_weather"}。 |
| none | 模拟不提供函数时的行为，不调用函数。 |

并行工具调用是另一个维度：在 OpenAI API 中，parallel_tool_calls: false 可将单轮调用限制为零个或一个；支持的模型和组合仍以 API 文档为准。模型返回多个调用请求不等于应用必须并发执行，实际调度仍由运行时按依赖和副作用决定。工具选择也不授予业务权限，执行前仍要做授权检查。

### 设计工具契约 / Tool contract

不要要求每个工具都填固定数量的说明槽。先确保开发者和模型都能理解以下契约：

| 说明 | 设计问题 |
|---|---|
| **职责与边界** | 这项工具具体完成什么？相似工具的分界在哪里？ |
| **输入** | 每个字段代表什么，格式和单位如何，什么条件下必填？ |
| **结果** | 哪些信息足以支持后续动作？是否需要返回可继续查询的标识符？ |
| **约束与副作用** | 读还是写？执行对象和范围是什么？何时需要确认？ |
| **错误与恢复** | 未找到、权限不足、限流、超时或部分成功时，应返回什么可操作信息？ |

例如，按订单 ID 查看具体内容用 get_order，按客户或时间搜索一批订单用 list_orders。不要让两个工具的用途重叠到只能靠模型猜；在描述中写清何时选择哪一个。字段名应表达业务含义，如 order_id，而不是含糊的 value；示例用真实格式，但不要放入用户数据。

返回结果应只包含下一步决策需要的信息。对于大集合，支持筛选、分页或范围读取，避免把无关数据全部塞回上下文。工具错误应说明发生了什么、是否已产生副作用，以及可安全采取的下一步。[Anthropic 的工具设计经验](https://www.anthropic.com/engineering/writing-tools-for-agents)特别强调清晰用途、低重叠、易读输入输出，以及用任务评估迭代工具设计；命名效果也因模型而异。

### Schema、说明与业务校验

Schema 是输入输出的结构合同，说明文字则解释语义、格式、单位、相互依赖和操作边界。可以用 required、enum、数值范围、格式约束或提供商支持的严格结构化模式，减少格式错误。不要假设 schema 的 default 字段会由每个 runtime 自动填入；运行时需要明确实现默认值和业务验证。

以部分退款为例，refund_amount 的数值范围可以按订单状态和总额在服务端检查；refund_reason 可以有可选枚举；但“用户是否授权退款”并不是 JSON schema 能验证的。严格输出约束只解决结构层，仍需检查身份、资源归属、当前状态、业务规则和风险阈值。[生产环境 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)说明各运行控制的授权与隔离边界。

### 并发（concurrency）、依赖与副作用

并行有两个不同环节：模型或 API 可以在一个响应中提出多个工具调用；应用运行时决定哪些调用能同时执行。能力因模型和 API 参数而异。[OpenAI 函数调用指南](https://developers.openai.com/api/docs/guides/function-calling)提供并行函数调用及关闭该行为的选项，但这不意味着所有调用都适合并发。

- **可并行的只读工作：** 获取客户资料、列出订单、读取支持历史；这些调用互不依赖时可并行，结果齐备后再合并。
- **必须有序的动作：** 核实订单 → 计算退款 → 执行退款 → 确认结果。后一步依赖前一步结果。
- **并发写入：** 涉及同一订单、库存或账户时，要处理竞态、重复提交和部分失败，通常需服务端幂等性（idempotency）、版本条件或事务保护。

网络超时并不能证明写操作失败。给有副作用的动作使用操作 ID 或幂等键；对结果不明的调用先查询状态，再决定是否重试。模型提出的错误恢复建议只是提示，服务端必须定义安全重试策略。

### MCP 是什么 / Model Context Protocol

[Model Context Protocol（MCP）架构规范](https://modelcontextprotocol.io/docs/learn/architecture)定义了 host、client 与 server 如何发现彼此能力并通信。MCP 数据层基于 JSON-RPC，规范包含 tools、resources、prompts 等原语；传输层处理连接、消息与授权。它为应用发现和调用外部能力提供互操作协议，本身不负责模型推理、业务授权或工具执行质量。

MCP 减少每个 agent 平台都为每个服务单独定义连接协议的重复工作，但不会自动消除全部集成成本：每个 server 仍需实现、认证、授权、版本兼容和任务评估。Host 决定暴露哪些能力，运行时仍要控制每个实际调用。

### 相关知识

- [智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：工具属于动作空间，但授权必须由运行时执行。
- [编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：并行与串行编排取决于任务依赖和副作用。
- [上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：工具定义与结果也是模型上下文的一部分。
## 12. When should a model control the next step? / 何时应让模型决定下一步？

**Short answer / 简答：** Use an AI agent when the task needs the model to choose among next steps from intermediate observations, and that flexibility is worth the added cost, latency, and operational risk. Keep fixed steps in code where they already meet the task’s success criteria.

当任务需要模型根据中间观察选择下一步，且这种灵活性值得其额外成本、时延和运行风险时，才让模型充当智能体。若固定步骤已满足任务成功标准，就继续由代码控制流程。

### 智能体、工作流、聊天与 RAG

“智能体”的定义并不完全统一。[Anthropic 将 workflow 与 agent 都放在 agentic systems 范围内，并以控制流由代码预先定义还是由模型动态决定来区分；OpenAI 的定义也强调模型管理任务流程并按状态选择工具。](https://www.anthropic.com/engineering/building-effective-agents) [OpenAI agent 指南](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) 因而，是否调用过工具、调用几次，不是可靠的唯一判据。

| 概念 | 核心特征 |
|---|---|
| **工作流（workflow）** | 程序定义步骤、顺序和分支；模型在指定节点完成分类、抽取或生成。 |
| **智能体（agent）** | 模型根据目标与观察结果选择工具或下一步；运行时负责执行、限制和停止。 |
| **聊天界面（chat interface）** | 用户交互形态，可以只是问答，也可以包在工作流或智能体外。 |
| **检索增强生成（RAG）** | 把检索内容交给模型的一种架构能力；它可以是单次流程中的一步，也可以供智能体迭代调用。 |

一次工具调用后返回，不足以判断系统是否“真正是 agent”；应描述模型实际拥有多少流程控制权。例如，客服退款可以由固定工作流处理合规检查，只让模型分类用户意图；如果系统需要调查多种来源、根据发现决定后续步骤，才可能值得交给智能体控制。

### 选择工作流还是智能体

先用能够满足任务成功标准的最简单结构，再用实际任务评估是否需要更大自主性。Anthropic 将工作流的可预测性与智能体对开放式任务的适应性作了区分，也提醒智能体可能增加成本和累积错误；这是一种设计权衡，不是“分支超过某个数量就必须用 agent”的定律。

| 任务形状 | 较合适的起点 | 例子 |
|---|---|---|
| 步骤固定、输入类别有限、结果可验证 | 代码工作流 | 校验订单 → 计算退款金额 → 执行退款 → 发送回执 |
| 后续步骤依赖未知的中间发现 | 有预算与停止条件的智能体 | 调查复杂故障时，根据日志和测试结果决定继续查哪一处 |
| 大部分步骤固定，少数探索性任务开放 | 混合架构 | 固定工单流程中，允许智能体在“诊断”节点调查日志 |

评估时比较任务成功率、错误类型、总延迟、模型与工具成本、人工接管率。多轮运行可能更贵、更慢，但不存在固定的“每多一步就按同一倍数增长”的通用比例；缓存、工具耗时、输出长度和模型价格都会改变结果。

### ReAct and the decision loop / ReAct 与决策循环

ReAct 的关键是让外部观察改变下一步。论文在 PaLM 的少样本提示里交错放入推理文字、任务动作和环境观察。推理文字用于记录进度、分解问题和调整动作，环境只对实际动作返回新观察。以 HotpotQA 为例，模型先查实体，再根据返回的段落找第二条证据。表 1 中，ReAct 在 HotpotQA 与 FEVER 上优于仅行动基线，和仅 CoT 的比较则随任务而变。检索也可能不给有用信息，论文观察到重复查询和错误传播。结论适用于论文的模型、工具和任务设置。 [Yao et al., arXiv v3, §2、图 1、§3.3 与表 1](https://arxiv.org/html/2210.03629v3)

生产中的可复用机制是 **decide → act → observe / 决策 → 行动 → 观察**。系统可用结构化工具调用和简短计划摘要承接这条反馈环。对执行的解释与审计应依赖实际调用、参数、权限决定和观测结果。运行时无需索取或保存模型的内部推理。

| 运行中的环节 | 谁负责 | 给下一环节什么 |
| --- | --- | --- |
| 决策 | 模型看到当前任务、可用工具和已验证的观察 | 结构化动作、向用户提问，或提交结果供验收 |
| 授权与执行 | 运行时校验 schema、当前权限和业务前置条件 | 执行结果、明确错误、审批要求，或结果未知的状态 |
| 观察与更新 | 运行时核对来源与调用 ID，保存必要状态 | 新证据和剩余预算，供模型决定下一步 |
| 验收与停止 | 运行时按完成条件、预算和取消状态收尾 | 已完成、等待输入、转人工、失败或待确认的终态或暂停态 |

用一笔退款跟踪循环。订单查询返回“已付款”，但缺少优惠券是否退回的信息。下一步选读适用规则或询问用户补齐资料。资料齐备后，由应用计算金额并验证审批条件。如果退款服务超时，观察结果是 `outcome_unknown`。此时应用以操作 ID 查询权威状态，在确定安全之前阻止再次写入。允许 Agent 选择查哪条资料，仍可让程序固定退款的授权和执行。相反，若任务只是查同一日期、同一币种的航班报价，查询返回 189、210、175 美元后，固定代码即可给出此次查询的最低报价 175 美元。

每轮执行完检查完成条件、总调用数、时间与预算。持续收到同一无进展结果时，可以换一个已允许的查证动作，或停止并说明证据缺口。长任务将进度和真实结果持久化，恢复时读取原状态，不让模型靠对话回忆猜测写入是否发生。工具请求、幂等和错误语义见 [工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)，恢复与事件回放见 [持久化 AI 运行](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F)。

评估时，把同一组任务交给固定工作流和 Agent，比较完成率、写入结果、权限违规、重复动作、成本和延迟。τ-bench 同时检查任务结束后的数据库状态与必须告知用户的信息。后续 τ²-bench 的电信任务还让模拟用户与 Agent 使用不同工具操作同一个环境，暴露了只测试单方动作时看不到的协调失败。将这类变化变成自己的测试用例，例如用户改完设置后要重新读状态，再决定是否执行后续动作。 [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [τ-bench](https://arxiv.org/abs/2406.12045) · [τ²-bench](https://arxiv.org/abs/2506.07982)

An observation updates the current run. A change that should apply across later runs needs a baseline, external evidence, and a retained version. / 观察会更新当前运行。若变更要延续到后续运行，就需要基线、外部证据与可保留的版本。[How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](#19.%20How%20do%20you%20test%20and%20keep%20an%20improvement%20to%20an%20agent?%20/%20%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E4%BF%9D%E7%95%99%E5%AF%B9%20Agent%20%E7%9A%84%E6%94%B9%E8%BF%9B%EF%BC%9F)

### 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；命名空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

### 相关知识

- [编排模式](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：决定步骤、并行、路由或多智能体结构。
- [上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：管理长任务中的历史、外部状态与缓存。
- [工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：定义运行时如何执行模型请求。
- [LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：区分任务反馈、变更验收与持久版本。
## 13. How should a multi-step AI task be structured? / 怎样组织多阶段 AI 任务？

**Short answer / 简答：** Choose orchestration from the task’s dependencies, independence, and ownership. Use code for known steps, add model-driven decomposition only when the work cannot be specified in advance, and keep one main loop unless measured parallelism, isolation, or a real capability boundary justifies delegation.

编排应根据任务依赖、子任务独立性和控制权选择：已知步骤由代码安排；只有工作无法预先列清时才考虑模型动态拆分；先保留单一主循环，只有实测并行、隔离或真实能力边界收益足以抵偿委托成本时才拆分。

Anthropic 的模式目录区分固定路径的 workflow 与模型驱动的 agent，并指出模式可以组合，复杂度应由任务效果决定。[以下模式以其一手说明为依据。](https://www.anthropic.com/engineering/building-effective-agents) 本文回答“如何安排步骤和委托”，而[智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)回答“是否把下一步控制权交给模型”。

### 固定流程：由代码决定控制流

| 模式 | 适用任务 | 机制与例子 |
|---|---|---|
| **提示链（prompt chaining）** | 子任务能按固定顺序拆分 | 摘要 → 抽取实体 → 起草答复；在边界加程序校验，避免错误直接传到下一步。 |
| **路由（routing）** | 输入类别对应不同处理路径 | 分类为退款、售前或技术支持，再交给对应流程。分类不确定时设置兜底或澄清路径。 |
| **并行化（parallelization）** | 子任务彼此独立，或需要多个尝试 | **分片（sectioning）：** 同时总结文档不同章节。**投票（voting）：** 多次独立评审后按预定义规则汇总；它会增加调用成本，汇总规则也要针对错误类型评估。 |
| **评估器—优化器（evaluator–optimizer）** | 有清楚的质量标准，反馈确实能改进结果 | 生成代码 → 执行测试 → 根据测试失败修订。设定最大迭代数；若评估器与生成器共享偏差，增加测试或人工依据，不应假设换一个模型就能消除偏差。 |

这些名称表示常见结构，不是互斥的架构类别。路由可以进入提示链；并行工作可以由确定性代码派发；评估循环也可以嵌入较大的智能体任务。

### 开放式任务：Orchestrator–workers

**编排者—工作者（orchestrator–workers）**由一个编排者模型在运行时拆分不确定的子任务，派发给工作者，再综合结果。它适合无法事先列出完整子任务的工作，例如根据代码库和需求决定要检查哪些文件；若任务边界已知，固定并行调用通常更简单。

典型流程：

1. 编排者明确目标与可验证的交付标准。
2. 工作者各自接收范围、必要上下文、权限和结果格式。
3. 可并发的任务同时运行；有依赖的步骤按序等待。
4. 编排者核对结果、处理冲突与缺口，再交付结论。

将工作交给另一个 agent 不会自动带来上下文隔离。运行时要明确决定共享哪些会话状态、传递哪些证据、工作者可以访问哪些工具，以及主流程接收完整记录还是摘要。相关权衡见[上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 多智能体：委托工具还是交接所有权

不同 SDK 采用不同命名，但可按谁负责最终答复来理解：

| 结构 | 谁保留用户交互控制权 | 适合场景 |
|---|---|---|
| **智能体作为工具（agents as tools）／管理者模式（manager pattern）** | 管理者调用专家，把返回结果纳入自己的答复 | 专家做边界明确的研究、分类或摘要；主 agent 需要比较并综合多个结果。 |
| **交接（handoff）** | 专家接管后续流程或用户对话 | 识别到明确专业领域后，由该专家负责处理。 |

例如，客服分类 agent 可将技术问题交给技术支持 agent；若客服 agent 还必须比较订单状态、退款政策与支持历史，则可把这些调查工作委托为工具并保留最终答复权。[OpenAI 编排文档以“交接”与“智能体作为工具”说明了这一控制权区别。](https://developers.openai.com/api/docs/guides/agents/orchestration)

不论哪种结构，都要约定交接输入、输出契约、状态归属、最大交接深度和失败回退。否则专家之间可能反复转交、丢失客户或订单 ID，或对同一副作用重复执行。工具输入与执行契约见[工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)。

### 先尝试单主循环，再验证拆分 / Start with one loop, then test delegation

**核心建议：** 后续步骤仍依赖同一任务状态时，先尝试一个主循环；只有可独立并行、需要隔离验证或具备真实能力边界的子任务显示出收益时，再拆分。这个建议是结构选择的起点，不是固定 agent 数量或工具数量阈值。

拆分的理由应是具体任务边界：

- **独立工作可并行：** 各自读取不同资料，最终可以汇总；先确认没有共享写入冲突。
- **需要上下文隔离：** 专家只拿到完成子任务所需信息，主 agent 接收可核验摘要。
- **策略或权限应隔离：** 不同工作者拥有不同的知识范围、工具和访问权限；权限隔离只有在运行时真正限制能力时才成立。
- **单个上下文过于混杂：** 实测表明工具重叠、指令冲突或长历史降低了任务成功率。

[Anthropic / Diane Sarkis 的 fold-subagents 文章（2026-10-22，“Using an agent loop with progressive disclosure”“Task-completion evals”等章节）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)讨论何时把依赖共享上下文的 subagent 流程折入主循环：先建立端到端基线，再逐个折叠 subagent，检查任务成败、生产链路和必须遵守的规则，并以重复运行比较；合并后仍保留领域流程。其讨论也将独立研究、并行探索和验证列为可能适合独立 worker 的工作。文章给出的是评估方法与工程经验，不是折叠 subagent 会普遍提高表现的因果证明，也没有普适的工具数量分界线。

GitSwarm 提供了不同范围的例子：异步 worker 自主选择工作，在可分支的共享 Git 仓库中发布可组合产物；执行 harness 仍负责调度和发布验证，而该验证检查提交要求、不认证产物正确性。[GitSwarm v1（2026-10-04，§§2.1–2.3）](https://arxiv.org/html/2610.04862v1)没有中央“intellectual planner”替 workers 指派探索方向，但不因此取消执行协调。它支持把独立、可检查的产物作为拆分条件，不证明普通任务都应使用多 agent。状态取舍见[上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)，架构对照及其证据边界见[LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。

### 提示模板仍是单 agent 的选项

面对角色、领域或策略不同但结构相似的任务，可使用一个明确模板传入少量、语义一致的变量，代替维护多份近似提示。变量过多或互相矛盾仍会让提示难以理解；应通过代表性输入评估模板，而不是只检查文本形式。

### 运行与观测

对每个节点、工具调用、agent、重试与交接记录关联的任务 ID、输入输出引用、状态、延迟、错误与模型或工具用量。结果应能回答：任务是否完成，哪个步骤导致失败，实际执行了几次外部副作用，谁接管了用户流程。日志内容需符合数据保留和隐私要求。

### 相关知识

- [智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：工作流与 agent 的控制流边界及运行循环。
- [工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：定义被编排结构调用的能力与执行边界。
- [上下文工程原则](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：决定在交接中保留什么、何时按需载入或重启探索。
- [LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：用端到端任务证据比较主循环、委托和交接。
## 14. How can a production AI system contain model errors and manipulation? / 生产环境 AI 系统如何限制模型错误与受诱导带来的影响？

**Short answer / 简答：** Treat user and retrieved content as untrusted data and model outputs as proposals. The application enforces authorization, validates outputs for their next consumer, limits execution capabilities, and keeps a stop path outside the model loop. Test those boundaries against direct and indirect injection, review high-impact actions, and turn confirmed failures into regression cases.

把用户输入和检索内容视为不可信数据，把模型输出视为候选内容或动作。应用负责执行授权、按下游接收方校验输出、限制执行能力，并在模型循环之外保留停止路径。针对直接和间接注入测试这些边界，对高影响动作进行审查，并把确认的问题转成回归用例。

**Key terms / 关键术语**

| Term / 术语 | Meaning / 含义 |
|---|---|
| **Prompt injection / 提示注入** | Untrusted content changes model behavior against the intended task or data boundary. / 不可信内容使模型行为偏离预期任务或数据边界。 |
| **Direct / indirect injection / 直接 / 间接注入** | The instruction arrives in the user’s own input, or in supplied content such as a document or tool result. / 指令来自用户输入，或嵌在随后提供的文档、工具结果等内容中。 |
| **Trust boundary / 信任边界** | Where the application independently decides whether data, a request, or an action is trusted or authorized. / 应用独立判断数据、请求或动作是否可信或已获授权的位置。 |
| **Least privilege / 最小权限** | Give each tool and execution environment only the data and capabilities required for its task. / 只向工具和执行环境提供完成任务所需的数据与能力。 |
| **Human handoff / 人工接管** | Pause a task and provide only the evidence and decision needed for a person to continue safely. / 暂停任务，仅提供人工安全继续处理所需的证据和待决事项。 |
| **Red teaming / 红队测试** | Adversarial testing that probes this application’s data and action boundaries. / 针对本应用数据与动作边界进行的对抗性测试。 |

### Threats and failure modes / 威胁与失效方式

流畅回答仍可能错误或缺乏证据。检索可以提供有用依据，但不保证模型会正确使用；检索文本也不授予执行权限。本篇关注由此产生的运行安全边界；[LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)衡量事实性与支持度，[RAG 架构与实现](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)解释检索行为。NIST 将 confabulation 列为生成式 AI 风险；它没有把 grounding 视作正确性保证（[NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)）。

提示注入不要求成功“覆盖 system prompt”。只要不可信内容改变模型行为并违反预期任务或数据边界，就构成问题。OWASP LLM01:2026 涵盖直接与间接输入，包括用户内容、检索材料、工具输出、多模态内容和持久记忆（[LLM01:2026 Prompt Injection](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)）。

| Path / 路径 | Where the instruction comes from / 指令来源 | Example / 示例 |
|---|---|---|
| **Direct injection / 直接注入** | The user’s message. / 用户消息。 | 用户要求助手忽略原任务，并将报告发送到无关目的地。 |
| **Indirect injection / 间接注入** | A document, webpage, image, or tool result supplied as data. / 作为数据提供的文档、网页、图片或工具结果。 | 被检索的页面要求转发对话，而不是按要求总结。 |

把指令与引用或检索内容分开可以减少混淆，但提示词、字符串过滤器和分类器都不是可靠的授权或执行边界。过滤器可能检测部分攻击，却不能判断用户是否拥有某条记录，也不能约束进程对文件系统和网络的实际访问。

如果应用把用户或检索内容写入持久记忆，这些内容就可能影响后续会话。这是有持久记忆系统才适用的条件性风险，不是每个 LLM 应用都必然存在；OWASP 将持久记忆列为注入面和投毒风险（[LLM01:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)、[LLM05:2026 Data and Model Poisoning](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM05_DataModelPoisoning.md)）。测试部分因此只对确有持久记忆的系统列出跨会话用例。

### Trust boundaries and runtime controls / 信任边界与运行时控制

把工具调用视为模型提出的请求，而不是授权。任何副作用发生之前，应用都应检查已认证的调用者、目标资源、请求范围、当前业务状态和所需审批。每项操作都要重新检查，包括读取。使用范围最小的工具与凭据；白名单或有效 JSON 结构本身不能证明调用者有权执行动作。OWASP LLM03:2026 将最小权限、在用户上下文中执行和代码强制的中介控制列为应对 excessive agency 的措施（[LLM03:2026 Excessive Agency](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md)）。

| Control / 控制措施 | Role / 作用 | Boundary / 边界 |
|---|---|---|
| **Prompt, filter, or classifier (content guardrail) / 提示词、过滤器或分类器（内容护栏）** | Flags or reduces some risky inputs and outputs. / 标记或降低部分风险输入与输出。 | Does not authorize resource access or isolate execution. / 不负责资源授权或执行隔离。 |
| **Authorization / 授权** | Checks whether this caller may perform this action on this resource now; enforce it on every operation. / 逐次检查当前调用者能否对目标资源执行该动作。 | A model-selected tool or allowlist is not authorization. / 模型选择的工具或白名单本身不是授权。 |
| **Output validation / 输出校验** | Checks structure and business constraints, then encodes or sanitizes for the next consumer. / 校验结构与业务约束，并按下游接收方编码或净化。 | Does not prove factual truth or authorization, and does not isolate execution. / 不证明事实正确或授权成立，也不等于执行隔离。 |
| **Sandbox / 沙箱（执行隔离环境）** | When code runs, limits its actual filesystem, mounts, network, and credentials. / 代码运行时限制其实际文件系统、挂载、网络与可用凭据。 | Does not authorize business actions; its boundary depends on configuration. / 不负责业务授权，隔离范围取决于实际配置。 |

**Moderation / 内容审核**按应用内容策略审核内容；**data minimization or redaction / 数据最小化或脱敏**会从输入或输出中移除不必要的敏感字段。它们可以限制内容，但不授予访问权限，也不能替代针对下游语境的输出编码。NIST 讨论了生成式 AI 数据收集与处理的隐私风险（§2.4，[AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)）。

高影响或难以撤销的动作应暂停，等待与具体动作和目标绑定的审批。获批后，应用仍需在执行前重新检查授权与业务状态。尽可能将密钥放在模型可见内容和执行环境之外；沙箱保护取决于实际挂载、网络规则和凭据暴露情况（[OpenAI Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)、[Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)）。工具 schema 和执行契约见[工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)。

### Stop and hand off / 停止与人工接管

达到已配置的失败阈值、目标资源或范围不清、工具行为异常，或动作影响需要审批时，应暂停并交给人工。除非已针对具体用途验证，否则模型自报的置信度不是经过校准的信号。OpenAI agent 指南把重复失败和高风险动作列为人工介入的例子（[A Practical Guide to Building Agents, pp. 30–31](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)）。

交接只需包含人工继续处理所需的信息：用户请求、相关证据及其来源、已尝试的动作和结果、尚待决定的事项。不要包含凭据或无关敏感上下文。运行日志与 trace 也只保留调查动作及结果所需的信息，并限制访问；NIST 在 §2.4 说明了生成式 AI 数据处理的隐私风险。授权决定作出前，暂停任何待执行副作用。

应用需要位于模型循环之外的停止路径，能够停止新的工具调用与重试、取消活动运行，并撤销或禁用受影响能力。提示模型停止不是 kill switch。恢复前先核对已经完成的动作并确认当前状态。NIST AI 600-1 要求部署后监控、事件响应与恢复，并能在结果偏离预期用途时停止或停用系统（§§ MANAGE 2.3、2.4、4.1）。

### Test and monitor the boundaries / 测试与监控边界

红队测试探索攻击者可能如何突破本应用的数据和动作边界；评估测量已知案例；生产监控观察真实运行结果，三者不能互相替代。发布前，以及模型、提示、工具、数据源或权限发生实质变化后，都应测试；相关事件发生后也应测试。NIST AI 600-1 要求实证评估与持续监控；[评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)说明测量和回归设计。

回归用例应关联到应用实际能力：

- **直接注入：** 用户请求超出其授权范围的动作；即使模型提出调用，运行时也应拒绝。
- **间接注入：** 检索内容或工具结果要求模型超出任务；验证其不能授权副作用。
- **敏感输出和内容政策（无需工具）：** 在隔离测试上下文中放入合成的受保护字段并请求泄露；另外测试违反内容政策的提示，验证字段不会暴露且配置的审核行为生效。不要使用真实个人数据。
- **输出处理：** 对可能被下游接收方解释为标记语言或指令的内容，在该接收方处理时验证其安全性。OWASP LLM10:2026 建议在下游使用前验证与净化模型输出（[LLM10:2026 Improper Output Handling](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM10_ImproperOutputHandling.md)）。
- **持久记忆（仅在系统有持久记忆时）：** 向隔离测试记忆添加无害的注入指令；验证后续会话不能借此触发受限动作或超出预期范围，然后删除记录并确认其影响已消失。

红队结果应记录攻击路径、是否发生未授权动作或信息泄露，以及修复方式；适用时将最小化案例加入回归测试。生产中监控工具调用与拒绝、意外状态变化、重复失败、人工覆盖和伤害报告；将信号用于调查和更新测试，不把单个比率视为目标。

### 相关知识

- [工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：工具请求、schema 与副作用执行。
- [RAG 架构与实现](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)：外部证据的检索和访问控制。
- [LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：质量与安全用例的测量和回归。
## 15. How can a production AI run survive disconnections and worker failures? / 生产环境中的 AI 运行如何经受断连与 worker 故障？

**Core explanation / 核心解释：** A client connection is a delivery channel, not the identity or source of truth for an AI task. Give each logical submission a stable run ID, persist authoritative state and useful checkpoints, and let clients query or resume that run after a timeout. A disconnect leaves delivery incomplete; it does not establish whether the model call or an external side effect finished. / 客户端连接只是交付通道，不是 AI 任务的身份或事实依据。为每次逻辑提交分配稳定的运行 ID，持久化权威状态和有用检查点，并允许客户端在超时后查询或恢复同一次运行。断连只能说明交付不完整，无法证明模型调用或外部副作用是否完成。

**Key terms / 关键术语：** run ID / 运行标识；authoritative state / 权威状态；checkpoint / 检查点；resume / 恢复；idempotency key / 幂等键；unknown outcome / 结果未知；terminal state / 终态。

### What changes from prototype to production? / 从原型到生产会发生什么变化？

A prototype tests whether a model can help with a task. A production service must also authenticate and authorize the caller, assemble permitted context, handle model and tool failures, validate outputs, manage deadlines and cost, and expose a result that can be recovered after the original response channel ends.

~~~text
Request → authenticate and authorize → assemble permitted context
        → model and/or tools → validate result → respond or escalate
        ↘ persist run state, trace, and privacy-reviewed operational signals
~~~

Treat a model-proposed tool call as untrusted input. The application executes it only after its own argument checks and authorization; schema-constrained output does not establish that an action is valid or permitted. See [Tool Design and Function Calling / 工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F) and [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F). OpenAI’s [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, describe provider-specific request and schema behavior; application authorization and semantic validation remain separate.

Set explicit deadlines, bounded retries, idempotency for retryable writes, cancellation behavior, rate and budget limits, an error or escalation path, and a way to roll back a model or prompt version. Retry only when the operation contract makes a duplicate safe. A timeout says the caller did not receive a result in time; it does not say the server did no work.

These are separate design questions with deeper treatments: [how to reduce latency and cost](#4.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F), [how to choose a deployment pattern](#6.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F), and [how to monitor and improve a production feature](#20.%20How%20do%20you%20monitor%20a%20production%20AI%20feature%20and%20turn%20feedback%20into%20a%20safe%20improvement?%20/%20%E5%A6%82%E4%BD%95%E7%9B%91%E6%8E%A7%E7%94%9F%E4%BA%A7%E4%B8%AD%E7%9A%84%20AI%20%E5%8A%9F%E8%83%BD%E5%B9%B6%E5%AE%89%E5%85%A8%E5%9C%B0%E6%94%B9%E8%BF%9B%EF%BC%9F). The remainder of this note defines the durable run contract that those interfaces rely on.

### Durable runs, checkpoints, and recovery / 持久化运行、检查点与恢复

Use one stable `runId` for a logical submission, independent of HTTP requests, event streams, and worker attempts. Persist the run's current state and terminal result or error summary long enough for clients to resolve refreshes and retries. A response body or stream is a view of that run, not its authoritative record.

#### Choose a completion shape / 选择完成方式

All three shapes can expose the same run identity, but they make different promises about waiting, early output, and recovery:

| Shape | What the caller sees | Trade-off |
|---|---|---|
| **Direct response / 直接响应** | One request waits for a final response. Its `runId` can be correlated or queried if the service persists the run. | Few moving parts and a simple client; long waits are vulnerable to deadline and connection limits. Without retained state, a lost response leaves no status to recover. |
| **Provisional stream / 临时流式响应** | The same run emits partial text or progress before its terminal result. | Better perceived responsiveness, but text is provisional until a terminal frame and authoritative state agree. A disconnect can leave useful partial output and an unknown outcome. |
| **Queued/background completion / 排队或后台完成** | Submission returns a run identity and current state; a worker completes it later, and the client polls or reconnects for updates. | Fits longer work and bounded admission, but requires durable state, queue/worker operations, status handling, and retention. `202 Accepted` means processing was accepted, not completed. |

For example, a synthetic API can accept `POST /runs` with a stable idempotency key, return `202` and a `runId`, expose `GET /runs/{runId}` for current state, and stream events from `GET /runs/{runId}/events?after=12`. The run record is authoritative; event delivery is a view. The `after` cursor helps only while the server retains the corresponding event history. This is an application contract, not an HTTP requirement.

Model the server-side lifecycle explicitly. `accepted`, `queued`, and `running` are nonterminal states. `cancel_requested` records a request that still needs handling. `completed`, `failed`, and `canceled` are terminal states. A reconnect should fetch current run status before claiming success. Replay progress only when the service defines a cursor and retains the events needed to fill gaps. The diagram shows one path for queued work.

~~~mermaid
stateDiagram-v2
  [*] --> accepted
  accepted --> queued
  queued --> running
  running --> cancel_requested
  cancel_requested --> canceled
  running --> completed
  running --> failed
  cancel_requested --> completed: completion won the race
~~~

### What if submission times out or a side effect has an unknown outcome? / 提交超时或副作用结果未知时怎么办？

A timeout after `POST /runs` creates an **unknown submission outcome**. The server may have created the run even though its response never reached the client. The client can query by its stable submission key if the API supports that lookup, or repeat the same request under its same-key retry contract. The server binds a key to the same request parameters and returns the existing run for a duplicate. Reusing the key with different input requires explicit handling. Starting a new run with a fresh key can duplicate model cost or side effects.

Worker recovery has a second ambiguity around external effects. Checkpoints tell the application what it recorded; they cannot reveal whether an unrecorded remote effect committed:

1. A worker records that an export run is at `create-artifact`, then crashes **before** calling the artifact service. Recovery can retry that step with the same operation key.
2. The artifact service creates the file, but the worker crashes **before** saving the returned artifact ID as the next checkpoint. The run record cannot prove failure. Retry with the same key if the receiving service deduplicates it, or query that service by operation key and then save the result. If neither is supported, mark the outcome unknown and reconcile it; blindly repeating may create a duplicate.

Persist a local effect and its deduplication record in one transaction when both share a database. For another service, use its idempotency contract, a queryable operation key, or a compensation/reconciliation path. See [confirming request outcomes / 确认请求结果](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) for retry budgets, key scope, and deadlines. See [queue acknowledgements / 队列确认](../../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md) for what the broker confirms.

| Failure point | What is known | Safe next step |
|---|---|---|
| Request or stream disconnects before a terminal result | The caller's view is incomplete; the run may still be active or already terminal. | Query `GET /runs/{runId}`. Resume events only with a defined, retained cursor; do not resubmit under a new key. |
| Worker crashes before a side effect | The checkpoint says the step did not finish, but another worker can retry it. | Use the same stable operation key and persist the result before advancing the checkpoint. |
| Worker crashes after an external effect but before its result is recorded | The external outcome is unknown to the run record. | Deduplicate or query at the receiver, then reconcile the checkpoint; do not infer that the effect failed. |
| Cancel request races with completion | Either transition may win the authoritative state update. | Serialize the transition and return the state that actually won; treat a pending request as nonterminal. |

### What does cancellation mean for a durable run? / 持久化运行中的取消意味着什么？

Persist a `cancel_requested` transition and let the worker observe it at a safe point. Serialize the terminal updates so completion and confirmed cancellation compete to update the same run state. If completion commits first, report `completed`. Commit `canceled` only when the run can no longer perform its work. An endpoint acknowledgement can leave cancellation pending. Compensating for an already committed external action requires its own operation.

A browser abort, closed tab, or disconnected event stream ends a local delivery attempt. It does not prove that the server-side run stopped. The UI should query the run record or request server cancellation separately; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) covers the client view, incremental decoding, and teardown.

### When is event-history replay useful? / 事件历史重放何时有用？

Some workflow runtimes persist an ordered event history and replay deterministic orchestration code to rebuild in-memory state. In such a runtime, completed external activities can return their recorded results during replay; this mechanism does not make a model call deterministic. A model call still in flight before its result was recorded may be attempted again, cost more, or return different text. Decide whether that retry is acceptable and checkpoint the result when it completes. Deterministic event-history replay is a runtime-specific implementation option, not a requirement that an LLM recompute identical output after a crash.

**Representative answer / 代表性回答：** I give each logical AI run a stable ID and persist its state independently of the response connection. A direct request, provisional stream, or queued worker can expose that same run. On reconnect, the client checks status and resumes from a retained cursor only when the service supports it. A worker checkpoints completed steps, but retries a side effect only with a deduplication or reconciliation contract because a crash after the effect can hide its outcome. Cancellation is terminal only after authoritative state says the work stopped; a client disconnect or cancel acknowledgement is not enough. / 我会为每次逻辑 AI 运行分配稳定标识，并独立于响应连接持久化运行状态。直接响应、临时流式响应或排队 worker 都可以暴露同一次运行。重连时客户端先查询状态，只有服务端支持保留游标时才按游标续传。worker 为已完成步骤保存检查点；只有具备去重或结果对账契约时才重试副作用，因为副作用完成后发生崩溃会让结果变得未知。只有权威状态确认工作已停止，取消才是终态；客户端断线或收到取消请求确认都不足以证明这一点。

### Related notes / 相关笔记

- [Real-time web updates / 实时网页更新](../../engineering-foundations/networking/real-time-web-updates.md) explains transport selection, SSE framing, and wire behavior.
- [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) owns browser-side partial output, terminal events, and local cancellation.
- [Confirming request outcomes / 确认请求结果](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) explains deadlines, retry, and idempotency.
- [Database transactions and recovery / 数据库事务与恢复](../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md) explains the boundary for durable application state.
- [AI System Design Interview Questions / AI 系统设计面试题](#21.%20How%20do%20you%20turn%20an%20AI%20system%20design%20prompt%20into%20a%20defensible%20architecture?%20/%20%E5%A6%82%E4%BD%95%E6%8A%8A%20AI%20%E7%B3%BB%E7%BB%9F%E8%AE%BE%E8%AE%A1%E9%A2%98%E8%BD%AC%E5%8C%96%E4%B8%BA%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E6%9E%B6%E6%9E%84%EF%BC%9F) applies these production mechanisms to end-to-end design cases.

**Sources / 来源：** [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) defines idempotent HTTP method semantics, and [§15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) says `202 Accepted` does not mean processing is complete. Temporal's [Workflow replay guide](https://docs.temporal.io/workflows) and [Event History guide](https://docs.temporal.io/encyclopedia/event-history) describe one runtime's deterministic orchestration replay and recorded activity results. These sources support the mechanisms described here; the example API, states, and names are synthetic application choices.
## 16. How can you tell whether an AI system meets its task contract? / 如何判断 AI 系统是否满足任务契约？

**Core explanation / 核心解释：** Define success in observable terms, then evaluate representative cases at the layer where the behavior occurs—retrieval, generation, or an end-to-end agent. Use objective checks where there is a defensible answer, verify facts and source support separately, and use an explicit rubric or calibrated judge for open-ended quality. Keep a held-out regression set, report the denominator and uncertainty, and pair offline comparisons with production outcomes. No single score captures task success, truth, relevance, safety, and operating cost. / 先把成功定义为可观察的条件，再在行为实际发生的层级评估代表性案例：检索、生成或 agent 端到端。存在可辩护答案时使用客观检查；事实正确与来源支持分别核验；开放式质量使用明确 rubric 或经校准的 judge。保留独立回归集，报告分母与波动，并把离线比较与生产结果结合。单一分数无法同时代表任务成功、事实、相关性、安全和运行成本。

### Define each dimension / 分别定义各评估维度

Faithfulness 和 groundedness 在论文与工具中用法不完全一致。评分准则或评分量表（rubric）应明确评估维度和证据锚点；需要对照真值的任务还应说明 ground truth（参考真值，如外部事实或标注答案）。评估来源忠实度时要指定来源/上下文，评估指令遵循时要列明请求中的约束。RAG 研究常将上下文相关性、答案对上下文的忠实度、答案相关性分别评估；这是有用的拆分方式，不是普遍完整的指标清单。[RAGAS](https://arxiv.org/abs/2309.15217) 与 [ARES](https://aclanthology.org/2024.naacl-long.20/) 使用相近但不完全相同的评估设置。

| Dimension / 维度 | Definition / 定义 | Does not establish / 不能据此推出 |
|---|---|---|
| Task success / 任务成功 | **EN:** Did the result meet explicit acceptance criteria? **中：** 输出是否满足明确的任务验收条件？ | **EN:** That every claim is true or safe. **中：** 不能证明每个说法都真实或安全。 |
| Factual correctness / 事实正确性 | **EN:** Are claims true against an appropriate external reference at the relevant time? **中：** 说法对照适当的外部依据、在相关时间点上是否为真？ | **EN:** That the supplied context supports them. **中：** 不能证明给定上下文支持这些说法。 |
| Source faithfulness or groundedness / 来源忠实度或依据充分性 | **EN:** Are claims supported by the specified source/context, without material contradiction? **中：** 说法是否由指定来源/上下文支持，且没有实质冲突？ | **EN:** That the source is current or correct. **中：** 不能证明来源本身及时或正确。 |
| Relevance / 相关性 | **EN:** Does the answer address the question or requested information? **中：** 答案是否回应问题或所需信息？ | **EN:** That it is correct, supported, or complete. **中：** 不能证明答案正确、有依据或完整。 |
| Instruction adherence / 指令遵循 | **EN:** Did it follow applicable format, scope, and constraints? **中：** 是否遵守适用的格式、范围和约束？ | **EN:** That it is factual. **中：** 不能证明内容属实。 |
| Operational quality / 运行质量 | **EN:** Does it meet latency, availability, and cost requirements? **中：** 是否满足延迟、可用性和成本要求？ | **EN:** That user task goals were met. **中：** 不能证明用户任务目标已达成。 |

“Hallucination / 幻觉”没有统一且公认的分类法。不同综述对 factuality 与 faithfulness 的关系和子类划分并不相同；某篇论文的 taxonomy 不能当作普遍的三分法。评估时应标记可观察的失败及其依据，例如：对照外部依据为假、给定上下文不支持、与上下文冲突，或不遵守指令。指令失败应明确测量；某篇研究是否把它归到 faithfulness 子类，取决于该文定义。[Ji et al., *Survey of Hallucination in Natural Language Generation*](https://arxiv.org/abs/2202.03629)；[Huang et al., *A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions*](https://doi.org/10.1145/3703155)（[arXiv](https://arxiv.org/abs/2311.05232)）。

**合成示例 / Synthetic example。** 给定的服务日程写着 5 月 10 日闭店，但权威的当前通知已将日期改为 5 月 12 日。复述 5 月 10 日的答案忠于给定日程，却在当前事实上错误。回答 5 月 12 日可能符合当前事实，却没有得到该日程支持。应分别评估来源支持与当前事实，并记录参照日期。

### Choose metrics for the task / 按任务选择指标

| Metric family / 指标类型 | Good fit / 适用条件 | Boundary / 边界 |
|---|---|---|
| Accuracy, exact match, F1, executable tests / 准确率、精确匹配、F1、可执行测试 | 有明确标签、结构化输出或可辩护的预期结果时。代码通过率只说明指定测试集的结果。 | 标签或测试集可能遗漏其他质量维度或合理答案。 |
| BLEU, ROUGE / 参考文本重合度 | 翻译、摘要等任务中，参考文本重合度能作为有用的语料级信号时。BLEU 原用于机器翻译的快速、频繁评估；ROUGE 是一组参考摘要指标。[BLEU](https://research.ibm.com/publications/bleu-a-method-for-automatic-evaluation-of-machine-translation)、[ROUGE](https://aclanthology.org/W04-1013/)。 | 衡量词面重合，不是通用事实性或有用性指标。合理改写可能重合较少；仅有高重合分不能证明答案正确或相关。它们是特定任务工具，并非因历史较久就失效。 |
| Retrieval precision/recall and ranking measures / 检索精确率、召回率与排序指标 | 有相关文档或参考证据标注的检索阶段。Recall@k 可看所需证据是否出现在前 k 项；精确率/排序指标可看返回集合与顺序。 | 结果取决于候选集、相关性标注和 k。检索到相关内容不等于证据完整，也不等于最终答案有依据。 |
| Rubric or model-graded scores / rubric 或模型评审分数 | 没有唯一答案的开放任务，且评价标准可以明确写出并用例子校准时。 | judge 本身也是可能出错的模型；评分不是 ground truth（参考真值）。 |
| Latency, availability, and cost / 延迟、可用性与成本 | 作为运行约束，与任务结果一起报告，用于理解质量与成本的权衡。 | 不能替代任务质量。 |

不要把指标名称当成跨库统一标准。如果使用框架中的 faithfulness、context precision 或 answer relevance 分数，应固定框架版本并检查其输入和 rubric；名称相同的指标也未必可互换。本文不提供框架 API 用法。

### Evaluate the pipeline at the right level / 在正确层级评估链路

对检索增强系统分阶段评估，才便于定位故障：

1. **Retrieval / 检索：** 候选集合是否包含所需证据？排序是否把它放在系统可用的位置？有相关文档或证据标注时，可据此评估。
2. **Generation given context / 给定上下文后的生成：** 回答是否回应问题、遵守指令、在需要时正确引用，且说法得到上下文支持？如果任务要求事实正确，还要单独核验外部事实。
3. **End-to-end agent / Agent 端到端：** Agent 是否通过合适的动作达到要求的环境状态？评估目标完成、工具/动作是否正确、有无有害副作用，以及延迟或成本。组件分数有助于定位问题，但不能证明端到端成功。像 [AgentBench](https://arxiv.org/abs/2308.03688) 这样的交互式 agent 基准在环境任务中评估 agent，而不只是评分孤立文本回答。

**Offline / 离线评估**用固定样本做受控比较和回归，便于复现；但可能漏掉当前流量、变化中的来源和线上用户结果。**Online / 线上观察或实验**反映部署行为，但结果可能延迟、不完整，或受模型以外因素影响。条件允许时两者结合：用线上证据发现变化与候选案例，经审查并去标识化或合成为适当样例，再纳入有版本记录的离线集。公开教学示例不要包含私人或用户来源数据。

### LLM judges and human review / 模型评审与人工复核

Judge model 可按 rubric 评分、比较候选答案，或筛出待复核案例。提供问题、相关上下文或参考答案，以及带有可观察评分锚点的标准；要求评委给出评分依据。若要核对验收底线，使用逐项 pass/fail 检查或带明确锚点的评分准则；若问题是相对偏好，可用成对比较。成对比较只回答相对偏好，赢家未必满足验收底线。

研究发现的评委偏差包括位置、冗长偏好和自我偏好，但程度随任务和评委变化。[MT-Bench](https://arxiv.org/abs/2306.05685)、系统性的[位置偏差研究](https://arxiv.org/abs/2406.07791)和关于[自我偏好偏差的研究](https://arxiv.org/abs/2410.21819)说明应在目标评估任务上实际检验评委，不应假定某项缓解措施必然有效。可以随机或交换候选顺序并比较评分，按任务切片抽样复核；多评委或跨 provider 的增益仍需在校准集上验证。它们是诊断手段和可能的缓解措施，不保证评委彼此独立或判断正确。

当标准需要专业知识、任务主观或后果重大，或需要验证自动评委时，应安排人工复核。先用共同样例校准评审者、比较分歧；需要可靠参考结论时，对分歧案例进行裁定。一致性表示评审者在 rubric 下较一致，不代表 rubric 或标签正确。Judge 与单个人的分数一致，也不能单独证明 judge 准确。

需要外部事实时，尽可能对照适当、可信且及时的依据。评估来源忠实度时，应对照指定的上下文检查说法。NLI 分类器、再次检索和 self-consistency 可帮助筛选待检查内容，但都可能出错：多次回答一致不能证明为真，二次检索也可能返回过期或不相关来源。应报告检查了什么、依据何在，而不要把检测器分数写成事实已核实。

同样，提交被引用、标成依赖或获提名投票（nomination），只能说明来源声明或选择过程；不能代替任务结果的正确性检查。[GitSwarm v1（2026-10-04，§§2.2、2.5、3.4、4）](https://arxiv.org/html/2610.04862v1)将依赖声明、执行轨迹中的实际产物使用和最终候选的提交祖先链分开分析，并明确这些指标不单独证明因果收益。

### Build a comparable regression set / 建立可比较的回归集

- 定义符合条件的任务总体，并抽取常见样本、重要切片和已知失败类型。记录样例如何选择、标注和版本化；方便取得的样例集不一定有代表性。
- 将开发样例与用于最终比较的独立保留集分开，避免反复针对保留集调优。记录模型、提示词、检索语料/配置、评委和 rubric 的版本。
- 明确分母。例如，报告“所有符合条件的尝试中成功完成任务的比例”，并单独报告回答覆盖率。若任务要求拒答，正确拒答计为成功；未回答或不当拒答也应作为结果保留。如果 faithfulness 只在已回答样本上计算，应标明这是“已回答样本中的条件分数”，并同时报告回答覆盖率或任务完成率。
- 在相同协议下与基线比较。对于随机输出，重复足够次数以观察有实际意义的波动；报告样本数与不确定性，不要把微小分差说成确定结论。ARES 展示了一种将自动评委、人类标注样例与统计估计结合的方法，但不是每种评估都必须采用。[ARES](https://aclanthology.org/2024.naacl-long.20/)；另见 [Towards Reproducible LLM Evaluation](https://www.turing.ac.uk/sites/default/files/2025-11/towards_reproducible_llm_evaluation.pdf)。
- 只让快速检查拦截它有能力发现的问题；根据变更风险安排更完整的评估。线上失败在原因查明、数据适合保留后可进入回归集；盲目加入每起事件会造成重复、数据泄漏或隐私风险。

### 架构迁移与更新验收 / Architecture migration and update acceptance

**核心解释 / Core explanation：** 在固定任务与验收契约下比较端到端结果；行为变化、预测分数或复用记录都不能单独证明改进。Compare end-to-end outcomes under fixed task and acceptance contracts; behavioral changes, forecast scores, or reuse records alone do not establish improvement.

比较 agent loop、harness 或上下文策略时，覆盖完整生产链路、强制规则和发生变化的任务切片，并报告新增成功与回归的任务成败翻转（task flips）、成本及重复运行波动。先记录现有架构的端到端基线，再一次折叠一个 subagent 重复比较，单主循环是待评估的候选方案。这是工程建议，参照 [Anthropic 的 folding 文章（2026-10-22，“Task-completion evals”“Folding subagents into the main agent via skills and tools”）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)。

若更新策略（policy）与预测器（predictor），应分别检验各自效果和配对兼容性；配对门禁失败时保留已接受组合，并让开发/更新、门禁和最终审计数据承担不同用途。[RSI-Anything v1（2026-10-09，§2.5）](https://arxiv.org/html/2610.13912v1#S2.SS5)

若要测试清空历史是否有助于搜索，从同一候选检查点比较继续运行（continuation）与清空后重启（reset），同时报告候选质量、方案提案数（proposals）、实际 token/费用或时间及重复波动。[*Scaling Discovery Requires Forgetting* v1（2026-10-14，§4、§4.3 / Table 3）](https://arxiv.org/abs/2610.20563v1)的主实验固定三次重置；AHC014 对照按提案数匹配而非等花费或时长，且同时清除 session 和候选历史。该重置数只是实验设置；结果不能归因于其中一种记忆，也不建立通用重置周期。

Harness 的行为对照是执行证据而非正确性证明；[Harness² v1（2026-10-09，§2.2.1、Appendix F）](https://arxiv.org/html/2610.14224v1)也指出额外执行成本、随机性和共同偏差的影响。工程上仍需单独限制 Probe 的外部写入权限与副作用，不能把它当成无成本、无影响的预测。

**工程建议 / Engineering advice：** 若系统用预测器排序候选，应分别记录预测与随后实测的误差，以及所选 policy/version 在固定验收契约下的任务结果和成本。

### Use public benchmarks as evidence, not a deployment proxy / 公共基准是证据，不是上线代理

当任务、协议、模型访问方式和计分规则与问题相符时，公共基准可支持受控比较。像 [HELM](https://arxiv.org/abs/2211.09110) 这样的广泛评估也显示了多种场景与指标的价值；但它们不会自动代表某个具体部署任务。

检查基准覆盖范围、评估协议以及训练数据污染的可能性。污染测量及其影响取决于基准、模型和测量方法；分数提高或小幅上涨本身不能证明模型记住了测试集。[Sainz et al.](https://arxiv.org/abs/2310.18018)；[Singh et al.](https://arxiv.org/abs/2411.03923)。可用公开结果缩小候选范围，再用有代表性、记录版本且带独立保留集的任务样本比较入选系统。

### Related notes / 相关笔记

- [Agent improvement and version acceptance / Agent 改进与版本验收](#19.%20How%20do%20you%20test%20and%20keep%20an%20improvement%20to%20an%20agent?%20/%20%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E4%BF%9D%E7%95%99%E5%AF%B9%20Agent%20%E7%9A%84%E6%94%B9%E8%BF%9B%EF%BC%9F) — connect feedback on a task to a change that persists across runs.
- [Orchestration patterns](#13.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F) — compare the single-loop baseline with tested delegation or parallel work.
- [RAG architecture and implementation](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) — 了解检索、证据组装和生成机制，对应本文的 RAG 评估阶段。
- [AI safety in production](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) — 了解需要单独设计任务检查的安全边界和生产控制。

### Sources / 来源

关键定义与主张已在正文链接一手研究。补充来源：

- Liang et al., [*Holistic Evaluation of Language Models*](https://arxiv.org/abs/2211.09110).
- Zheng et al., [*Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*](https://arxiv.org/abs/2306.05685).
- Xia et al., [*Evaluation-Driven Development and Operations of LLM Agents: A Process Model and Reference Architecture*](https://arxiv.org/abs/2411.13768) — 提出连接离线与线上评估的流程模型，并不保证两者分数一致。
## 17. 何时应微调来弥补稳定的行为差距？

### 案例：日志助手反复给出错误标签

值班工程师希望构建日志助手，把失败日志归入稳定标签并用固定 JSON 结构输出，方便后续聚合。举例：输入 `Build 73 failed: connect ECONNREFUSED 10.0.0.8:5432`；团队约定的标签是 `database_connection_refused`，简短摘要是“构建进程无法连接数据库”。但模型有时把它标成 `database_timeout`，有时又在 JSON 前后附上说明文字。日志已包含分类所需的信号，错误在标签映射和输出行为，而不是少了当日外部事实。

先把指令、标签定义、示例、可用结构化输出和工作流改清楚，并在同一批代表性日志上建立基线。如果约束输出能解决 JSON 格式问题，就让应用用结构化输出保证格式；只有在标签误判等行为差距仍反复出现、且手头有经审查的正确示例时，才评估微调。按成因选择方法：

| 失败现象 | 先改变什么 | 何时进入微调评估 |
| --- | --- | --- |
| 缺少或变化中的服务事实 | 权威数据源、检索或 application programming interface（API，应用程序接口） | 微调不能代替数据刷新或权限检查；需要时把微调行为与检索组合。 |
| 指令、标签定义或流程不清 | 提示词、上下文、标签设计或工作流 | 只有这些因素稳定后还存在重复行为差距，训练样例也能表达正确行为时。 |
| 相同输入反复违反风格、分类或响应格式 | 先试更清楚的提示词与应用层结构约束 | 若特定任务行为仍稳定失败，可用代表性示范训练并用独立评估证明收益。 |

fine-tuning（微调）更新预训练模型的可训练参数，使目标示例所表达的行为在之后的调用中更常出现。权重并不是能按请求精确查询、保持实时或实施用户权限的数据库。外部证据仍需检索的来源时效和访问控制；可从[如何检索并使用经过授权的外部证据？](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)了解应用如何提供证据。训练前应比较提示词基线与相关检索或工作流基线；只有数据代表目标行为、差距可重复且预期收益覆盖训练、部署和维护成本时，才值得继续。

### 标签差距应该更新哪些参数？

日志助手案例里，目标不是重写基础模型的所有能力，而是在不改变底座的前提下，调整选定投影矩阵，使模型更常把 `ECONNREFUSED` 映射到正确标签。这可以用 low-rank adaptation（LoRA，低秩适配）说明。若采用列向量记法，基础投影 `W` 将 `k` 维输入映到 `d` 维输出；LoRA 冻结 `W`，只训练两个小矩阵组成的增量：

$$
W' = W + \Delta W,\qquad \Delta W = BA
$$

其中 `A` 的形状是 `r × k`，`B` 是 `d × r`，所以增量 `BA` 的形状与 `W` 相同；`r` 是中间瓶颈宽度，也是 `BA` 秩的上限。由于 `A` 或 `B` 本身可能秩不足，`BA` 的实际秩可以小于 `r`；增量至多沿 `B` 的 `r` 个列方向调整。看一个可手算的小矩阵：设输入 `x=[1,2]ᵀ`、基础权重 `W=I`（单位矩阵，因此 `Wx=x`）、`r=1`、`A=[1,1]`、`B=[0.1,−0.2]ᵀ`。那么 `Ax=3`，`B(Ax)=[0.3,−0.6]ᵀ`，也就是 `W'x=Wx+B(Ax)=[1.3,1.4]ᵀ`。输入先经一维瓶颈，再投影回两维；真实网络里这只是某层的局部表示增量，不是直接把最终类别标签改成目标值。

训练时，cross-entropy loss（交叉熵损失）经模型计算图反向传播到 `A` 和 `B`，优化器逐步修改它们；基础矩阵 `W` 保持冻结。常见实现还会乘缩放因子 `α/r`，并可能在适配路径加入 dropout（随机失活）；本例为了便于手算省略这些配置。若目标权重的方向或存储转置与这里不同，矩阵形状会随实现转置，但可训练参数仍是低秩增量。

在 `4096 × 4096` 的单个投影矩阵上取 `r=8`，LoRA 矩阵共有 `r(k+d)=8(4096+4096)=65,536` 个可训练数值；原稠密矩阵有 `dk=4096×4096=16,777,216` 个数值。这仅比较单个目标矩阵。全模型的训练参数量取决于目标层数和矩阵数，不能凭一个矩阵的比例预测整模型的质量或训练显存。

**rank（矩阵秩）**决定这个增量能表达多少方向：较低的 `r` 参数和显存更少，但可能表达不了复杂的行为差距；较高的 `r` 容量更大，训练和部署成本也增加。应从可运行的小秩实验开始，用相同数据与留出样例比较，不存在保证质量的通用秩。

其他方法改动模型的不同部分。full fine-tuning（全量微调）更新全部可训练基础权重，适应容量较大但算力、内存和模型产物成本也高；quantized LoRA（QLoRA，量化低秩适配）冻结量化基础权重并训练 LoRA，QLoRA 论文在其特定实验中使用 4-bit 量化，不能推定任一量化、模型或任务都适用。adapter（适配器）在 Transformer 块中加入小型可训练模块；prefix tuning（前缀微调）学连续向量，作为各层的前缀表示输入 Transformer；prompt tuning（软提示微调）则在输入嵌入前加少量连续向量。后两者不是普通可见文本 token（词元），也不同于编辑指令文字的提示词工程。

有些服务栈能把适配器合并进基础权重，有些会在推理时保留额外运算；训练器和服务端支持也不同。选方法时应把是否需保留底座、可用显存、预期行为复杂度、训练产物和服务路径放到同一比较中，并以任务评估确认，而不是假定某一种参数高效微调必然胜过其他方法。

### 案例中的标签如何变成训练损失？

若错误行为已被归因到稳定的标签映射，训练数据就要把“输入信号”和“期望输出”配对。日志助手的一个合成监督样例如下：

~~~json
{
  "messages": [
    {"role": "user", "content": "Classify this build log using one approved category and return JSON only: Build 73 failed: connect ECONNREFUSED 10.0.0.8:5432"},
    {"role": "assistant", "content": "{\"category\":\"database_connection_refused\",\"summary\":\"构建进程无法连接数据库。\"}"}
  ]
}
~~~

supervised fine-tuning（SFT，监督微调）将期望回答分成目标 token（词元）序列 `y₁,…,y_N`。计算第 `j` 个 token 的目标时，模型接收输入 `x` 和训练样本中已知的正确前缀 `y_{<j}`，再预测 `y_j`；逐步喂入这些标注前缀的方式称为 teacher forcing（教师强制），不是先让模型自由生成前缀。常见的 cross-entropy（交叉熵）目标可写为

$$
L(\theta)=-\frac{1}{N}\sum_{j=1}^{N}\log\pi_\theta(y_j\mid x,y_{<j}).
$$

这是对每个目标 token 的负对数概率取平均。假设只看标签位置的两个候选词元 `[database_timeout, database_connection_refused]`，玩具 logits（未归一化分数）为 `[2,0]`，模型把错误候选放在前面。softmax（归一化指数函数）概率为 `[e²,1]/(e²+1)≈[0.880797,0.119203]`，目标 one-hot（独热向量）是 `[0,1]`，正确标签对应的损失为 `−ln(1/(e²+1))=ln(e²+1)≈2.126928`。对这两个候选分数的梯度是 `p−onehot(y)≈[+0.880797,−0.880797]`；梯度下降会降低错误候选的相对分数、提高正确候选的相对分数。实际共享参数还受其他 token 位置与样本的梯度影响，所以不能由这一项推断模型更新后的具体概率。真实输出有许多 JSON 与摘要 token，损失会覆盖整段目标回答；这个二候选小算例只解释梯度方向，不是实测模型数字。

梯度再沿模型的共享计算图回传到被选参数：全量微调会更新全部可训练权重；LoRA 会更新 `A`、`B`，基础矩阵保持冻结。也就是说，SFT 不会把一条日志作为可查询记录附加到模型中，而是用许多输入—目标对让模型的参数逐渐偏向它们共同表达的映射。新日志分布若与训练样本不同，已学到的标签映射仍可能失效。

不存在能预测成功的通用样本数。小而干净的数据集可以先验证目标行为是否可学；更广泛或罕见的错误类型需要更多覆盖。针对本例，应覆盖 `ECONNREFUSED` 的不同措辞、日志前后缀、允许标签的边界案例与相邻的 `timeout` 标签，避免只把同一行复制很多遍。不要把样本量当成质量证据。

> [!example] 摘要也可以作为监督目标
> 这是一个合成输入—输出对，用来说明 SFT 也可教摘要措辞；它不是法律建议，也不是所有训练器的通用格式。
>
> ~~~json
> {
>   "messages": [
>     {"role": "user", "content": "Summarize this sample clause: The supplier will deliver the parts by June 1."},
>     {"role": "assistant", "content": "The supplier must deliver the parts by June 1."}
>   ]
> }
> ~~~

数据审查要检查事实与标签是否正确、输入类型和失败切片是否有代表性、标注口径是否一致、重复样本、敏感信息，以及使用权。按日志来源、事故类别或时间段切分训练和评估集；同一次事故里的近重复日志若随机分到两侧，会让测试集看似独立却实际泄漏。合成数据可以扩充覆盖，但仍需检查错误事实、标签偏差和模板重复。

### 怎样组织训练、调参并验收？

1. **界定重复失败。** 记录当前行为、目标行为、运行约束和不能接受的回归。例如记录日志助手把 `ECONNREFUSED` 误判成 timeout 的比例，以及合法标签全集和 JSON 契约。
2. **先立无训练基线。** 固定基础模型、提示词、结构约束、检索和工作流；在代表性样本上量出错误类型和分母。任务若允许在应用层保证 schema，应同时评估这项控制。
3. **构建并审查样例。** 去重，排除未经授权或敏感的数据，检查标签、覆盖范围及目标 token 格式。
4. **拆分数据。** 训练集用来算梯度，验证集用来选训练轮数和其他控制；选择固定后，最终独立测试集才用于比较候选与基线。记录如何切分和可能的泄漏风险。
5. **固定模型与训练方法。** 确认基础模型、全量或参数高效方法、训练器版本、数据格式、许可条款，以及产物能否由目标服务加载。
6. **跑小实验并记录配置。** 记录学习率和调度、训练轮数、每卡批次、梯度累积、有效批次、数据版本、LoRA 秩与目标模块、检查点和验证指标。
7. **冻结方案后做独立比较。** 用相同输入与运行设置比较微调前后模型；检查整体成功率、重要标签切片、非法 JSON、安全、成本和时延。
8. **谨慎部署并监控。** 对模型和回滚路径做版本管理，遵守数据保留与同意规则，并继续观察相同业务结果。

训练任务成功完成，只说明优化过程运行了，不代表模型泛化变好。不能只凭一次分数上升就声称模型发生了记忆或泛化；还要检查样本重叠、任务切片和独立证据。

learning rate（学习率）决定优化器更新的尺度；对某个设置来说过大可能使训练不稳定，过小则可能在既定预算内学不到目标行为。epoch（训练轮数）表示完整遍历训练样本的次数；多训练几轮可能改善拟合，也可能开始过拟合。batch size（批次大小）控制一次优化更新综合多少样本，影响显存和梯度波动。若每卡微批次为 `b`、设备数为 `D`、gradient accumulation（梯度累积）步数为 `K`，在各步样本等权的常见设置下，有效批次近似 `bDK`。梯度累积让多次较小的前向与反向计算先累积梯度，再进行一次参数更新；若固定有效批次，增加 `K` 只会增加两次更新之间的微步数，不会改变按样本计算的更新频率。若保持 `b` 和 `D` 不变而增大 `K`，有效批次也增大，每轮数据对应的优化器更新数就会减少。样本长度不等时，还要查看训练器如何按 token 聚合损失。

训练集用来拟合权重，验证集用来比较训练控制并支持提前停止，最终留出测试集要等所有选择固定后再用。反复根据最终测试集调参，会让它泄漏进开发过程。训练损失和验证损失有助于诊断，却不能替代目标行为指标；应将结果与未微调基线比较，并检查重要切片。

### SFT、偏好优化和奖励训练怎样取舍？

supervised fine-tuning（SFT，监督微调）用期望回答或演示训练模型。它能教会示例实际表达的响应模式，但不能保证模型在未见场景中遵循所有指令或保持安全；生产环境仍需运行时控制，可参阅[生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)。

InstructGPT 研究中的 reinforcement learning from human feedback（RLHF，基于人类反馈的强化学习）流程先用人工撰写的演示做 SFT，再用人类偏好比较训练奖励模型，最后让强化学习优化策略来获得更高奖励。这描述的是该论文的方法，不代表所有助手模型的训练过程。

direct preference optimization（DPO，直接偏好优化）从同一提示下被选中和被拒绝的回答优化模型，不像经典 RLHF 流程那样先训练一个单独的奖励模型。它仍依赖偏好数据、目标函数和建模假设，不能据此推断 DPO 一定比 proximal policy optimization（PPO，近端策略优化）更准确或更安全。应根据数据、基础设施和评估结果选择。

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）适用于存在可靠程序检查或其他独立结果检查的任务；它和 SFT、离线蒸馏承担不同作用。以推理任务为例，[可验证奖励如何训练推理能力？](#18.%20%E5%8F%AF%E9%AA%8C%E8%AF%81%E5%A5%96%E5%8A%B1%E5%A6%82%E4%BD%95%E8%AE%AD%E7%BB%83%E6%8E%A8%E7%90%86%E8%83%BD%E5%8A%9B%EF%BC%9F)沿一道题讲清采样、判分、组内优势、策略更新、零方差奖励组和长度截断，并比较最终验收方式。偏好标签仍可能互相矛盾，或只反映标注者与 rubric（评分准则）的选择；偏好训练完成后，仍要用目标任务及相关失败案例评估，不能仅凭偏好标签判断安全。

> [!info]- 来源
> 下列来源分别支持微调方法、偏好训练和平台可用性。LoRA 参数示例及训练流程中的建议为教学演算或工程实践。
>
> - **低秩与参数高效微调。** Hu et al., [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)；Dettmers et al., [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)；Houlsby et al., [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751)；Li and Liang, [Prefix-Tuning](https://arxiv.org/abs/2101.00190)；Lester et al., [The Power of Scale for Parameter-Efficient Prompt Tuning](https://arxiv.org/abs/2104.08691)。
> - **SFT 与 DPO。** Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)；Rafailov et al., [Direct Preference Optimization: Your Language Model Is Secretly a Reward Model](https://arxiv.org/abs/2305.18290)。
> - **OpenAI API 上的可用性。** [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization)、[Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning)、[Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization)、[Reinforcement fine-tuning](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning) 与 [Deprecations](https://developers.openai.com/api/docs/deprecations)，核对日期为 2026-11-06。OpenAI 正在逐步结束自助微调：2026-05-07 起，没有既往微调记录的组织不能创建训练任务；2026-07-02 起，过去 60 天未对微调模型运行推理的组织也不能创建新任务；现有合格用户可创建任务至 2027-01-06，或基础模型更早停服之日。微调模型推理会持续到其基础模型退役；先前训练文档仍在迁移，具体资格与模型时限应按官方页面核验。平台可用性仅适用于 OpenAI API，不是对通用微调方法的限制。
## 18. 可验证奖励如何训练推理能力？

给模型一道可复算的小题：“4 盒各装 3 个螺丝，另有 2 个散装螺丝，共有多少个？”答案是 `4×3+2=14`。若训练提示要求模型把推理和答案分别放进 `<think>...</think>`、`<answer>...</answer>`，一个运行器可以检查最终数值和标记格式。下面先沿四条回答算分，再追踪分数怎样改变模型的下一次输出概率。

若要判断这类训练是否适合稳定的行为差距，可先读[何时应微调来弥补稳定的行为差距？](#17.%20%E4%BD%95%E6%97%B6%E5%BA%94%E5%BE%AE%E8%B0%83%E6%9D%A5%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F)；要设计独立验收，再读[如何判断 AI 系统是否满足任务契约？](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。

### 检查器判的是什么，没判的又是什么？

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）要求 reward（奖励）来自能独立复核的目标，例如参考答案比较、结构约束或程序测试。模型评委即使能输出分数，若它只是估计开放式质量或是否符合参考答案，也属于带误差的近似奖励；过程评审器同理，不能仅凭“会评分”就称为可验证结果。RLVR 仍属于 reinforcement learning（RL，强化学习）；其训练循环如下：

~~~mermaid
flowchart TD
    Q[数学题 q] --> S[旧策略采样 G 个回答]
    S --> V[结果与格式检查器判分]
    V --> A[在同题组内计算优势]
    A --> U[按裁剪策略更新当前模型]
    U --> N[下一批题继续采样]
    U -. 可选 Kullback–Leibler（KL）散度正则 .-> R[参考策略]
~~~

检查器必须针对明确目标设计；不同类型的检查器能支持不同强度的结论：

- **规则型 verifier（规则检查器/程序检查器）。** 数学任务可解析最终答案并检查等价性；代码任务可编译并运行预先定义的测试；结构任务可检查 schema（结构模式）和必需字段。在规则覆盖范围内，结果可重复、成本较低。编译成功或通过现有单测只说明满足这些检查，不证明程序对所有输入正确；答案解析器也可能漏掉等价表达或容忍错误。
- **学得的 verifier、评审模型或 reward model（奖励模型，RM）。** 可以用成对偏好训练 RM，也可以让模型对照参考答案判断简短答案是否正确。它能覆盖难以写成规则的质量，但分数是代理信号，受评分准则（rubric）、评审偏差和训练数据影响；这类模型分数可用于 model-based RL（基于模型奖励的强化学习），但如果无法独立复核评分本身，就不属于可验证奖励。策略越会优化该分数，越可能找出评审器漏洞。
- **process reward model（PRM，过程奖励模型）。** 它对推理步骤分别给分，可提供比最终答案更多的过程信号，但要先定义步骤边界、收集可靠步骤标签并检查评审器是否被利用。步骤切分和标注质量可能成为新的误差来源。

“可验证”描述检查目标能否被独立执行或复核，不意味着 formal verification（形式化验证）证明了模型程序的全部行为。outcome reward（结果奖励）与 process reward（过程奖励）描述“检查整段结果还是给中间步骤打分”，并不决定“奖励是否可验证”：程序可判最终答案，也可有带误差的模型评委给整段回答打分；PRM 可逐步评分，但标注和评审仍可能出错。若结果检查器只看最终答案，它没有逐步核对 chain-of-thought（CoT，思维链）；即使最终答案由程序精确判定，也不能因此推断轨迹中的每个中间推理都正确。

### 同题采样怎样转成组内优势？

给定题目 `q`，old policy（旧策略）`π_old` 会按当前生成分布采样 `G` 条 rollout（采样轨迹）`o₁,…,o_G`。每条回答是若干 token（词元）组成的序列；检查器只根据结果与格式给整条回答 reward（奖励）`r_i`。在 DeepSeek-R1-Zero 的规则奖励中，答案准确性 `r_acc` 和格式 `r_format` 等权相加；下表用一个单独设计的教学检查器演算同类的两个信号，不声称复刻 R1 的解析器：教学检查器可从带或不带标记的输出摘录中提取末尾数值，准确性与标记格式分别判分。四条回答如下：

| 回答 | 输出摘录 | 最终答案正确 | 标记格式正确 | `r_acc+r_format` |
| --- | --- | ---: | ---: | ---: |
| A | `15`，没有指定标记 | 0 | 0 | 0 |
| B | `14`，没有指定标记 | 1 | 0 | 1 |
| C | `<think>4×3=12；加2仍是12</think><answer>12</answer>` | 0 | 1 | 1 |
| D | `<think>4×3=12；12+2=14</think><answer>14</answer>` | 1 | 1 | 2 |

C 的过程虽有算术错误，只要结果奖励的检查器只验证最终答案 `12` 与格式，仍可能得到格式分；这不是逐步正确性标签。

R1 论文 §2.2 对数学准确性奖励举的是指定格式中的最终答案；格式奖励则明确要求推理放在 `<think>` 标记中。上表为了分开演算两项信号，允许摘录不带标记仍被教学解析器读出数值；不要把这条玩具解析规则当成 R1 的实现细节。

Group Relative Policy Optimization（GRPO，组相对策略优化）用同题回答的平均奖励作 baseline（基线），并通常按同题奖励标准差缩放 advantage（优势）：

$$
\bar r=\frac{1}{G}\sum_{i=1}^{G}r_i,\qquad
\hat A_i=\frac{r_i-\bar r}{s_r},\qquad
\hat A_{i,t}=\hat A_i
$$

这里 `s_r` 是这 `G` 个奖励的 standard deviation（标准差），`t` 是回答中的 token 位置。对结果监督，算法把同一标量优势 `\hat A_i` 广播给回答中的每个生成 token；它告诉优化器“这条轨迹相对同题其他轨迹表现如何”，不告诉它“哪一行推理出错”。实现通常会在分母加一个与裁剪参数不同的小常数 `\epsilon_{std}`，避免 `s_r=0` 时除零，但这不会为零方差组创造新信号。

这组奖励为 `[0,1,1,2]`，均值为 `(0+1+1+2)/4=1`。为方便手算，假设用总体标准差：

$$
s_r=\sqrt{\frac{(0-1)^2+(1-1)^2+(1-1)^2+(2-1)^2}{4}}
=\sqrt{0.5}\approx0.707.
$$

于是 A、B、C、D 的优势依次约为 `−1.414、0、0、+1.414`。D 相对组平均奖励较好，得到提高其轨迹概率的信号；A 相对较差，得到降低其轨迹概率的信号；B 和 C 落在均值上，按这次组内比较没有优势信号。该教学演算不声称复刻某个框架的标准差定义、奖励组合、掩码或 loss reduction（损失聚合），实现细节要按锁定版本检查。

### 概率比、裁剪与 KL 怎样约束参数更新？

设题目 `q` 下，旧策略采样出回答 D；在其已生成前缀 `o_{i,<t}` 后，旧策略给这个已采样 token 概率 `0.20`。更新后，当前策略在同一个 `q`、同一个前缀和同一个 token 上重新打分，得到 `0.26`。这两个已算出的概率构成 importance ratio（概率比）：

$$
\rho_{i,t}(\theta)=
\frac{\pi_\theta(o_{i,t}\mid q,o_{i,<t})}
{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
=\frac{0.26}{0.20}=1.30.
$$

proximal policy optimization（PPO，近端策略优化）的 clipped surrogate（裁剪代理目标）限制这次更新能从该 token 的优势中获得多少收益。设裁剪宽度 `\epsilon_{clip}=0.2`，裁剪区间为 `[1-\epsilon_{clip},1+\epsilon_{clip}]=[0.8,1.2]`。D 的优势是 `+1.414`：未裁剪项为 `1.30×1.414≈1.838`，裁剪项为 `1.20×1.414≈1.697`，目标取较小值。因此，该 token 的实际新旧概率比仍是 `1.30`；达到上界后只是这一个正优势项进入平台，其他 token、共享参数上的梯度和 KL 项仍可能改变模型概率。

裁剪不会硬性限制实际的新旧概率比，也不会把答案裁成正确或错误；它只改变 surrogate 中特定优势项的梯度。若优势为负，低于下界时也会出现相应的平台。裁剪范围过窄可能削弱很多 token 的学习信号，过宽则可能允许不稳定的大更新，必须用目标任务验证。

参考策略与采样时的旧策略承担不同作用。旧策略 `\pi_{\theta_{old}}` 是产生本批回答的分布，出现在概率比的分母；参考策略 `\pi_{ref}` 是一个用于限制策略漂移的锚点。Kullback–Leibler divergence（KL 散度）衡量两个概率分布的差异，例如参考分布为 `[0.9,0.1]`、当前分布为 `[0.8,0.2]` 时，按当前分布对数值求和得到

$$
D_{KL}([0.8,0.2]\Vert[0.9,0.1])
=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}\approx0.044403\text{ nats}.
$$

`nats` 是使用自然对数得到的单位；此二元分布在单个前缀上枚举两种可能，因而这里是精确求和的 KL。实际 RL 目标通常对题目和旧策略 rollout 求期望，GRPO 会用采样响应或 token 上的概率项估计 KL；DeepSeekMath 给出采样估计，R1 也把 sampled response 上的 KL 项写进目标。因此，不能把“精确遍历每个上下文的完整词表”当作所有 GRPO 实现的前提。`β=0` 时 KL 项关闭；非零 `β` 会增加贴近参考策略的约束，也会带来额外计算。

现在各项已经有了对应量：组内奖励决定优势，概率比比较新旧策略，裁剪限制 surrogate，KL 项约束相对参考策略的漂移。一个常见的 token 级 GRPO 最大化目标写作

$$
\mathcal{J}(\theta)=\mathbb{E}\left[
\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}
\left[
\min\!\left(\rho_{i,t}\hat A_i,
\operatorname{clip}(\rho_{i,t},1-\epsilon_{clip},1+\epsilon_{clip})\hat A_i\right)
-\beta\widehat D_{i,t}
\right]
\right].
$$

`\widehat D_{i,t}` 是在回答 `i` 的位置 `t`、沿同一已采样前缀计算的 KL 惩罚估计；本式将它和 surrogate 一起按 token、回答和题目聚合。它不是上面枚举两个候选得到的精确 KL，也不自动保证在旧策略采样与当前策略已经偏离时仍无偏。

这里最大化 `\mathcal{J}`；若训练器定义的是最小化损失，则对应最小化 `-\mathcal{J}`。该教学目标先对每条回答的 token 项取长度平均，再对组内回答取均值；最外层期望对题目和旧策略采出的回答组求平均。这只是一个讲解用的 reduction。论文写法和框架目标并不完全相同：DeepSeekMath 的 GRPO 公式写逐 token 概率比并按每条回答长度取均值；DeepSeek-R1 正文把策略比写成整条输出的概率比；TRL 和 verl 又提供不同的损失聚合、奖励标准化与 KL 配置。公式相同处说明策略更新机制，具体归约和超参数仍须按所用实现核对。

> [!info] 为什么结果分数会影响整条序列？
> 一条回答的对数概率可分解为各个条件 token 对数概率之和：`log π(o_i|q) = Σ_t log π(o_{i,t}|q,o_{i,<t})`。策略梯度沿这条计算链反向传播，所以一个终局奖励可以提高或降低整条采样轨迹的概率。它没有把标准答案写进参数，也没有给轨迹中每一步单独贴上正确或错误标签。

#### GRPO 为什么不需要 critic（价值网络）？

PPO 常训练一个 critic（价值函数/价值网络）估计状态价值，再用它计算优势；对大语言模型来说，这通常需要额外模型和显存。GRPO 不拟合该价值网络，而是用同一道题的多条回答的奖励均值作基线，并可按组内标准差归一化。它省去了 critic，却需要为一道题生成多个回答、运行多次检查器；因此节省模型内存的代价是更多 rollout（采样轨迹）和判分开销。若检查器昂贵，或生成回答很长，这部分成本可能成为瓶颈。

### 哪些奖励组不给学习信号？

若同一道题的全部回答奖励都相同，例如 `[1,1,1,1]` 或 `[0,0,0,0]`，则每个 `r_i - \bar r = 0`，所以优势全为零。给标准差分母加 `\epsilon_{std}` 能避免除以零，却不会改变分子为零的事实；对这道题来说，policy gradient（策略梯度）没有区分候选答案的信号。

这通常出现在过容易的题（所有采样都答对）或当前策略很难攻克的题（所有采样都答错）。Decoupled Clip and Dynamic Sampling Policy Optimization（DAPO，解耦裁剪与动态采样策略优化）的 dynamic sampling（动态筛组）会保留有正确也有错误回答的组，以减少二元准确率任务中零优势组占用有效 batch 的情况；这会改变进入更新的题目分布，需要监控覆盖面，不是所有任务都该采用的通用规则。只用结果奖励时，组内差异来自试验回答；有格式、长度或偏好等额外奖励时，即使正确性相同，奖励也可能不同，但增加的信号是否对齐任务目标仍需单独检查。

### 为什么回答长度和截断会改写训练权重？

原始 GRPO 常先把每条回答的 token 损失按自身长度平均，再对组内回答平均。设某条回答有 20 个 token、另一条有 200 个 token，若两条每 token 的优势和损失大小相近，前者每个 token 会乘约 `1/20`，后者会乘约 `1/200`。因此，短的正优势回答可得到更大的单位 token 权重；长的负优势回答则可能被摊薄。这是某种损失 reduction（聚合方式）的长度加权效应，不是“GRPO 一定喜欢长思维链”或“总是惩罚长答案”。

后续改法针对的偏差不同，应按自己的目标与 token 分布比较：

- **DAPO** 改为按累积 batch 中的有效 token 数聚合，让长回答里的 token 不会仅因回答长就被样本级平均稀释；这也会让长回答贡献更多总 token 项。它另以分开的上下裁剪幅度提高探索 token 的上调空间，并在其二元准确率设置中动态筛除同奖组。论文的示例取 `epsilon_low=0.2`、`epsilon_high=0.28`。这些选择服务于该论文的长 CoT 训练设置。
- **Dr.GRPO（GRPO 的论文修正版）** 讨论样本长度平均和按组奖励标准差归一化带来的回答长度与题目难度加权，并提出移除这两项归一化、用固定生成预算作分母。它改变了每题和每 token 的权重；论文论证与实验限于其 R1-Zero-style 设置，不意味着对所有任务都是默认最佳。

硬生成上限会截断回答。若检查器将未完成答案一律判错，训练可能把超长但接近正确的轨迹当作完整错误来惩罚，给策略带来噪声。DAPO 论文用截断样本 loss mask（损失掩码）和预期长度之后的软惩罚来处理这种情况。另一种做法是为任务定义经过验证的长度成本；若任务确实要求短回答，不能简单把长度惩罚当噪声丢弃。要判断截断样本是否可公平计分，应同时观察长度、终止原因、奖励和通过率。

### DeepSeek-R1-Zero 与最终 R1 有什么不同？

DeepSeek-R1 没有发明强化学习或 GRPO。GRPO 已由 DeepSeekMath 于 2024 年提出，R1 将其用于大规模 reasoning post-training（推理后训练）。R1-Zero 展示的是一种特定训练结果：在 DeepSeek-V3-Base 上不先做 supervised fine-tuning（SFT，监督微调），直接用规则型准确性和格式奖励训练策略。论文观察到响应变长、出现反思和探索行为；这些是该实验中的行为变化，不是每条推理链经过验证或模型获得类人的自我意识的证据。

DeepSeek-R1 是多阶段流程，不等于 R1-Zero。论文描述的主线如下：

~~~mermaid
flowchart TD
    B[DeepSeek-V3-Base] --> Z[R1-Zero 分支<br/>不先做 SFT；规则正确性与格式奖励做 GRPO]
    B --> S[收集数千条冷启动推理示范<br/>先做 SFT]
    S --> R[第一阶段推理 RL<br/>规则奖励 + 语言一致性奖励]
    R --> RS[拒绝采样与筛选<br/>约 600K 推理样例]
    RS -.筛选后的训练数据.-> D[约 800K 样例做第二次 SFT]
    B -->|重新从 Base 权重开始| D
    D --> M[第二阶段多目标 RL<br/>推理规则奖励 + 通用偏好/安全模型奖励]
    M --> F[DeepSeek-R1]
~~~

第一阶段先收集数千条更易读、对话式的冷启动推理样本，再用规则奖励继续强化推理，并加语言一致性奖励降低混语。rejection sampling（拒绝采样）阶段从第一阶段 checkpoint（检查点）为每题生成多个回答，保留正确轨迹；部分难以写规则的样本由 DeepSeek-V3 对照参考答案辅助判断，再过滤混语、过长段落或代码块等难读样例，形成约 600K 推理样本。另加入约 200K 非推理样本，重新从 DeepSeek-V3-Base 权重做第二次 SFT。这里由第一阶段 RL 传过来的是筛选后的数据；第二次 SFT 不直接沿用该 RL checkpoint 的权重。

论文将两条训练线的配置分开报告：R1-Zero 每题采样 16 条、`β=0.001`、每 400 步刷新参考模型；最大回答长度在第 8.2K 步之前为 32,768 token，之后增至 65,536。最终 R1 第一阶段推理 RL 也报告每题 16 条、`β=0.001`、每 400 步刷新参考模型，最大长度 32,768 token，并设 GRPO clip ratio `\epsilon_{clip}=10`。这些是论文的阶段配置，尤其 `10` 不是通用 clip 默认值。

第二阶段 RL 对推理题仍用规则奖励；对通用帮助性与安全性问题使用模型奖励：帮助性评估主要看最终摘要，安全性则检查整条响应。模型奖励用在通用偏好任务，不代表 R1-Zero 的推理训练用神经奖励模型逐步判对错。R1 作者报告帮助性奖励模型分数上升时，Codeforces 表现却下降，作为 reward hacking（奖励投机）的例子；作者放弃在大规模推理 RL 中使用神经过程奖励模型的理由包括过程步骤难定义、标注难扩展和模型本身可能被利用，但仍提出它们可用于重排或引导搜索。

### 哪种训练信号符合手头目标？

| 目标与可用数据 | 适合先试什么 | 主要代价与边界 |
| --- | --- | --- |
| 已知期望输出，能写出稳定示范 | supervised fine-tuning（SFT，监督微调） | 训练信号来自示范实际表达的行为；未见输入上的泛化需要独立验证。 |
| 有可靠的程序化结果检查，希望模型通过尝试发现更好的解题轨迹 | 在线 RLVR，例如 GRPO | 需要多次采样、稳定可复现的检查器、足够算力和独立验收；奖励只覆盖检查器所定义的目标。 |
| 有更强教师模型生成并筛选过的轨迹，希望小模型学会这些解法 | offline distillation（离线蒸馏）或 rejection-sampling SFT（拒绝采样后的 SFT） | 学生从固定轨迹模仿，不需要每轮再按学生当前策略 rollout；效果受教师质量、样例覆盖和筛选器限制。 |
| 有成对偏好标签，目标偏主观且不易精确程序化 | direct preference optimization（DPO，直接偏好优化）或其他偏好优化 | 学到的是标注偏好与训练目标，不是外部事实真值，也不是结果正确性的证明。 |

R1 的蒸馏例子属于离线监督：教师先产生推理回答，筛选后的固定回答用于 SFT，学生训练时不会每轮自己采样再按 verifier 更新。论文 Appendix F 的一个受限比较中，Qwen2.5-32B-Base 做超过 10K 步 RL 后得到的 Qwen2.5-32B-Zero，和 DeepSeek-R1-Distill-Qwen-32B 在 AIME 2024 的 pass@1（单次采样通过率）分别为 47.0% 和 72.6%。这个实验显示该教师轨迹在该基线、数据和评估协议下很有效，不能推出蒸馏总胜过 RL。R1 自身也将 SFT 与 RL 组合使用。

### 多教师在策略蒸馏又提供了什么训练信号？

离线 SFT 把固定教师回答当作目标 token；在线 RLVR 让学生自己采样回答、再用一个标量 reward 给轨迹分配优势。还有一种目标是：学生先在自己的 rollout 中走到某个 prefix（生成前缀），教师在这个相同前缀上提供整个词表的下一 token 分布，学生再对齐该分布。这称为 on-policy distillation（OPD，在策略蒸馏）：训练前缀由学生当前策略产生，因此训练覆盖学生实际会走到的状态；软分布则让教师可以给未采样到的 token 也提供信息。

DeepSeek-V4 论文 v1 报告了一种多教师 OPD 流程。数学、代码、Agent、指令遵循等领域分别训练 specialist teacher（领域教师模型）：先用领域数据做 SFT，再用领域 prompt 与 GRPO 奖励做强化学习。之后，统一 student（学生模型）从自己的策略采样轨迹，按任务从相关教师的完整输出分布学习。十多个是整个训练系统的教师数量，不是每个前缀都要运行全部教师。该报告将这一阶段的 mixed RL 改为 OPD；它没有说 specialist 阶段也跳过 SFT/RL。

把来自不同任务的训练样本按适用教师分组，多教师目标可概括为

$$
\mathcal{L}_{OPD}(\theta)
=\sum_{j=1}^{M}w_j\,\mathbb{E}_{s\sim\mathcal{D}_j}\left[D_{KL}\!\left(
\pi_\theta(\cdot\mid s)\,\Vert\,\pi_{E_j}(\cdot\mid s)
\right)\right].
$$

`\mathcal{D}_j` 表示适用教师 `j` 的任务中，学生 rollout 实际走到的前缀分布；`π_θ` 是学生在该前缀的分布，`π_Ej` 是该教师在同一前缀上的分布，`w_j` 是教师权重。求和概括整个训练混合，不要求把每个前缀都交给所有教师。对每个学生前缀，目标先用学生和教师完整词表 logits 经 softmax（归一化指数函数）得到两张概率分布，再对全词表精确求和计算 reverse KL（反向 KL），方向为学生到教师；它不是只评估刚采样到的一个 token，也不是对最终回答打分后广播一个优势。DeepSeek-V4 报告认为，相较于只用学生刚采样的 token 估计 KL，全词表 logit 蒸馏在其系统中梯度方差更低、训练更稳定；这是该报告的方法选择，不能推为所有任务的通用结论。

看只有两个候选 token 的小分布：学生 `Q=(0.8,0.2)`，教师 `P=(0.9,0.1)`。学生到教师的方向是

$$
D_{KL}(Q\Vert P)=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}
\approx0.044403\text{ nats}.
$$

反过来则是 `D_KL(P∥Q)=0.9 ln(0.9/0.8)+0.1 ln(0.1/0.2)≈0.036690 nats`。结果不同，因为 KL 对求和式左侧分布中的概率质量加权；因此不能把 `D_KL(student∥teacher)` 和 `D_KL(teacher∥student)` 当作可互换的“相似度”。两分布演算说明方向，不代表报告中的实测 loss 或质量增益。

| 机制 | 训练时的输入状态 | 提供的信号 | 与其他机制的区别 |
| --- | --- | --- | --- |
| 在线 RLVR / GRPO | 学生自己采样的完整回答 | RLVR 用可独立复核的规则分数；一般 GRPO 也可用模型奖励，但评委分数不因此变成可验证结果 | 依赖 reward 与采样组，不直接给每个词的教师分布。 |
| 离线 SFT / 轨迹蒸馏 | 固定收集的教师回答 | 每个目标 token 的 cross-entropy（交叉熵） | 学生不必在每个训练步骤自己 rollout；不会自动覆盖学生独有的前缀。 |
| 多教师 OPD | 学生自己 rollout 到的前缀 | 各教师在同前缀上的全词表分布与反向 KL | 信号是分布对齐，不是结果 reward 或固定答案 token。 |
| mixture of experts（MoE，混合专家）路由 | 同一个模型的一次前向计算 | 路由器选择内部 expert 子网络参与计算 | 这是模型架构；DeepSeek-V4 报告的 specialist teacher 是独立完整模型权重，并非 MoE 层里的 FFN 子网。 |

全词表 logits 的缓存成本也很大。V4 报告的实现按样本对应的教师索引组织数据，缓存该教师的末层 hidden state，再在训练时加载相应输出头重建词表分布；它避免为所有训练位置长期保存完整 logits，但仍需教师推理和输出头计算。

OPD 的多位教师是训练时的来源；学生要吸收其能力进自己的参数，推理时不需要继续调用这十多个教师，也不等于部署一个 teacher 路由器。报告给出按教师重要性设权重的 full-vocabulary（全词表）方案，但没有给出可迁移到任意任务的通用权重或样本调度规则。它应作为独立的蒸馏选择与 RLVR、离线 SFT 对照，不应称为所有训练任务的最佳方案。

### 当前训练器提供哪些可用控制？

训练库的默认值是一个实现版本的起点，不是适用于所有任务的推荐答案。版本固定后，应检查奖励如何合并、优势是否除组内标准差、每个回答怎样聚合 token 损失、策略概率比如何裁剪、KL 项是否加载参考模型，以及到达长度上限时哪些 token 会参与 loss。

截至 2026-11-06，Hugging Face TRL 的 `v1.17.1` 发布版在 `GRPOConfig` 中提供下列控制。TRL 的 GRPO 指南也展示了用 `GRPOTrainer`、prompt（提示）数据集和数学准确性奖励函数训练的可执行入门样例；要复现行为，应依赖版本 tag 的配置与代码，不要仅靠无版本的网页说明。

| TRL `v1.17.1` 参数 | 发布版默认值 | 应按任务检查什么 |
| --- | --- | --- |
| `beta` | `0.0` | 默认不加载参考模型、不加 KL 项。若要限制偏离参考策略，显式设非零值并记录内存与质量代价。 |
| `epsilon` | `0.2` | PPO-style ratio clip 的基础幅度；低概率探索 token 是否能获得足够上调空间要单独观察。 |
| `loss_type` | `"dapo"` | 默认采用 DAPO 式 token 聚合。还提供 `"grpo"` 与 `"dr_grpo"` 等选项，reduction 会改变长短回答的权重。 |
| `scale_rewards` | `"group"` | 默认按组标准差缩放奖励。Dr.GRPO 风格配置还要考虑关闭这项缩放；只改 loss reduction 不等于复现论文算法。 |
| `mask_truncated_completions` | `False` | 默认仍将截断回答纳入损失。若任务不能公平评分未完成答案，可显式启用 mask，并监控丢弃比例和长度分布。 |

`epsilon_high` 可设置与下界不同的上裁剪幅度；DAPO 在其特定实验中用 `0.28`，不是 TRL 通用默认值。TRL 当前版本的字段组合应连同模型、奖励函数、数据划分、生成上限、随机种子和有效 batch 一起记入实验配置。

verl 的 `v0.9.1` 发布版也能做 GRPO，但其通用 `ppo_trainer.yaml` 默认 `algorithm.adv_estimator=gae`，即 generalized advantage estimation（GAE，广义优势估计），不是 GRPO；若要跑 GRPO，需显式设为 `grpo`。同一 tag 中 `algorithm.norm_adv_by_std_in_grpo=true`，而 `algorithm.use_kl_in_reward=false`、`actor.use_kl_loss=false`；actor 的 `loss_agg_mode` 默认是 `token-mean`。因此，verl 的基础 PPO 配置不能当作完整 GRPO 论文设置；要核对优势估计、奖励标准化、loss reduction 及两种 KL 路径各自的字段。`filter_groups.enable` 默认关闭，采用 DAPO 式筛组时还要显式配置及检查组筛选指标。

TRL `v1.17.1` 和 verl `v0.9.1` 是本节核对过的具体发布版；新版本可能改变默认值或实现。一个可复现的训练说明至少应记录库的 tag/commit、模型 checkpoint、reward 函数与聚合权重、`G`、优势标准化和 `epsilon`、clip、loss reduction、KL 两项设置、完成长度及截断 mask。不要用一个显示 `GRPO` 的命令行参数概括这些差异。

### 怎样独立验收训练结果？

训练样本上的 reward 上升只说明策略更会满足优化目标；不能据此证明泛化。把同一可靠评分规则应用在未参与训练、调参或筛选的新题上，仍是衡量该结果指标的有效方式。若 reward 只检查数学答案，最终验收还应覆盖解析边界、等价答案、错解侥幸答对、格式问题及未知题型；代码任务则要检查隐藏测试、边界输入、sandbox 隔离和副作用。通过现有 verifier 只说明通过该检查集，需检查 verifier 本身的覆盖和漏洞；一个分数也不能单独证明广义质量或安全性。

在方案确定前留出不参与训练、调参或筛选的独立任务集与隐藏测试。用相同提示词、模型推理设置和采样预算比较训练前后 checkpoint，按任务难度、长度、终止原因和失败类型报告分母与成功率，并一并看格式、重复、拒答、安全、时延和成本。若目标包含帮助性、风格或开放式质量，应在训练偏好集之外使用盲审人工样例或已校准评审器；模型评审器分数不能替代事实检查。发现候选用格式、措辞或可预测漏洞取得高训练分但任务质量下降时，应修复奖励或检查器，再从未参与优化的验收集重测。

训练前先小规模比较组大小、奖励组合、标准差缩放、clip、KL、loss reduction 和截断处理，固定并记录选择理由。DAPO、Dr.GRPO 或原始 GRPO 的效果取决于任务奖励是否可信、回答长度分布、题目难度及实现细节，没有一个只凭算法名称就能得出的跨任务最佳配置。

> [!info]- 来源
> 下列来源映射到正文中的机制与实验。数值推演是教学合成值；训练器参数来自标明版本的官方文档或代码。
>
> - **GRPO、同题组优势与 PPO 对照。** Shao et al., *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models*（2024，§4.1、Appendix A.1.6），[论文](https://arxiv.org/html/2402.03300)。原始算法、结果/过程监督和 token 级目标。
> - **R1-Zero 奖励与完整 R1 流程。** DeepSeek-AI, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*（arXiv:2501.12948v2，2026-01-04；§2.1–2.3、§3.1–3.2、Appendix B.3/B.4.2/B.5、F.1、G.2），[v2 HTML](https://arxiv.org/html/2501.12948v2)。支持准确性/格式奖励、奖励模型使用范围、训练阶段、reward hacking、过程奖励模型和蒸馏比较。
> - **DAPO。** Yu et al., *DAPO: An Open-Source LLM Reinforcement Learning System at Scale*（arXiv:2503.14476v2，2025-05-20；§3.1–3.4、§4），[v2 HTML](https://arxiv.org/html/2503.14476v2)。支持 Clip-Higher、动态筛组、token-level loss 和截断处理；结论限于该训练系统与实验。
> - **Dr.GRPO。** Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective*（arXiv:2503.20783v2，2025-10-06；§3.1–3.2），[v2 HTML](https://arxiv.org/html/2503.20783)。支持回答长度与题目难度加权分析及 Dr.GRPO 的固定预算分母方案。
> - **TRL 当前配置。** Hugging Face [TRL `v1.17.1` 发布记录](https://github.com/huggingface/trl/releases/tag/v1.17.1)（2026-10-30）、[该 tag 的 `grpo_config.py`](https://github.com/huggingface/trl/blob/v1.17.1/trl/trainer/grpo_config.py)和[当前 GRPOTrainer 文档](https://huggingface.co/docs/trl/grpo_trainer)，截至 2026-11-06 核对。版本配置支持 `beta=0`、`epsilon=0.2`、`loss_type="dapo"`、`scale_rewards="group"`、`mask_truncated_completions=False`；无版本文档可能晚于 tag 更新。
> - **verl 当前配置。** [verl `v0.9.1` 发布记录](https://github.com/verl-project/verl/releases/tag/v0.9.1)（2026-09-20）、[通用 PPO trainer 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/ppo_trainer.yaml)、[actor 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/actor/actor.yaml)、[GRPO 结果优势实现](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/ppo/core_algos.py)。配置说明默认优势估计是 GAE、组奖励标准差归一化打开、两种 KL 路径关闭，actor 聚合默认 `token-mean`；实际训练还须检查所用 recipe 的覆盖值。
> - **DeepSeek-V4 多教师 OPD。** DeepSeek-AI, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*（arXiv:2606.19348v1，2026-04-26；截至 2026-11-06 核对公开报告仍为 v1；§5.1.1–5.1.2、§5.2.2），[v1 HTML](https://arxiv.org/html/2606.19348v1)。支持 specialist 阶段 SFT+GRPO、student 前缀上的多教师 reverse KL 与全词表 logits 蒸馏。权重安排和通用路由规则不由该报告建立。
## 19. How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？

**Short answer / 简答：** Use predictions to rank candidates, then measure them on real tasks against a common baseline and a predefined acceptance rule. Keep the accepted workflow, predictor, or harness as a version that can be inspected and restored. / 先用预测给候选排序，再用真实任务、统一基线和预先定义的验收规则测量效果。验收通过后，把工作流、预测器或运行脚手架作为可追溯、可恢复的版本保留。

任务内反馈改变当前任务状态；持久改进则把经评估接受的策略、预测器或 harness 变更保留为后续系统版本。两者都不等于模型在一次运行中自行改变权重。

~~~mermaid
flowchart TD
    Baseline[Fix the task and baseline] --> Propose[Propose and rank changes]
    Propose --> Measure[Run candidates and collect real observations]
    Measure --> Accept{Meets the acceptance rule?}
    Accept -->|Yes| Save[Record evidence and retain the accepted version]
    Accept -->|No| Baseline
~~~

### Decide what will change / 确定改进对象

Specify the task, budget, success criteria, and stop condition before trying candidates. Record whether each candidate changes the task policy, the predictor that ranks proposals, or the harness that controls execution. When two components can interact, compare each change separately and then compare the pair before accepting it. Preserve the task inputs and baseline for that comparison. [Evaluation and paired acceptance / 评估与配对验收](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)

### Rank candidates, then observe the real result / 候选排序之后获取真实结果

[RSI-Anything v1（2026-10-09，§2.1）](https://arxiv.org/html/2610.13912v1#S2.SS1) 将任务规格、预算、验收和停止条件视为固定契约；积累经验本身不会修改策略或模型。其 JEPA-Anything/OPF 世界模型先预测潜变量表示，再由领域读出（readout）转换成任务结果预测，用来排序候选并交给外部测量；机制见[§2.2](https://arxiv.org/html/2610.13912v1#S2.SS2)与[§2.3](https://arxiv.org/html/2610.13912v1#S2.SS3)。因此要区分规则、模型预测、模拟器输出和实测结果。外部反馈可以促成策略或工作流更新；只有在已观察候选显示预测器不可靠、且数据与预算足够时，才考虑更新预测器。观测覆盖不足也不等于可靠性已经成立。[§2.4](https://arxiv.org/html/2610.13912v1#S2.SS4)与[§2.5](https://arxiv.org/html/2610.13912v1#S2.SS5)分别说明更新门槛和配对验收。[Table 4](https://arxiv.org/html/2610.13912v1#S6.T4)与[§5](https://arxiv.org/html/2610.13912v1#S5)中各应用的更新范围不同；持续互相改进仍需联合的多轮评估。

**工程建议：** 对有清楚任务指标的工作流，可以尝试用脚本、模拟器或范围受限的 agent 预测候选效果并据此预筛，再与后续实测比较、验收版本。语法检查仍是规则校验，agent 的文字预判仍是预测。这些是实现选项，尚无替代上述学习型 world model 的等价实证；单步排序也不证明多步状态模拟有效。

例如，优化一个有工具调用的文档问答 Agent 时，可以用脚本预估候选配置的调用次数，先筛出更值得测试的候选。再对同一组任务运行基线和候选，比较实际成本、证据是否支持答案、权限控制是否通过。记录任务集、基线版本、变更及结果，验收后保留可恢复的配置和证据。这个例子说明候选筛选与版本验收如何配合。

### Retain changes to the harness / 保留脚手架改进

另一类改进改变的是运行脚手架（harness），而非基础模型。[Harness²（v1，2026-10-09，§§2.1–2.3）](https://arxiv.org/html/2610.14224v1) 在同一任务上实际执行候选 harness，比较编辑前后的行为，再将采用的 harness 组件和有依据的经验存入库；新任务从共同的 H₀ 起步并按需检索。该研究保持 editor 模型、阶段指令和决策规则不变，因此展示的是任务级 harness 与经验库的演进，不是模型权重或 editor 自行改写。执行对照可支持针对性修改，但不单独证明答案正确；验收边界见[LLM 评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。

**Related questions / 相关问题** — [When should a model control the next step? / 何时应让模型决定下一步？](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F) explains the live execution loop. [Context engineering / 上下文工程](#9.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains what can be stored for retrieval on later tasks.
## 20. How do you monitor a production AI feature and turn feedback into a safe improvement? / 如何监控生产中的 AI 功能并安全地改进？

**Core explanation / 核心解释：** Pair technical service signals with task outcomes. Record enough version and trace context to locate a regression while minimizing sensitive payloads. Treat user feedback as a useful but biased signal: inspect failure modes, make a targeted change, compare it on held-out cases, and keep or roll it back against agreed criteria. / 将服务运行信号与任务结果一起观察。记录足以定位回归的版本与追踪信息，同时尽量减少敏感载荷。用户反馈有用但存在偏差：先检查失败类型，再做有针对性的变更，在留出案例上比较，最后按约定标准保留或回滚。

**Key terms / 关键术语：** observability / 可观测性；trace / 追踪；task outcome / 任务结果；feedback signal / 反馈信号；rollback / 回滚。

### How should an application monitor behavior? / 应用应监控哪些行为？

Track technical operation and task outcomes together. Useful measures include:

- latency distributions and time to first token (TTFT), throughput, and queue time;
- errors and timeouts by stage, input/output usage, and cost per completed task;
- tool success and authorization denials, cache-hit correctness, task completion, and escalation;
- explicit user feedback and whether the result was accepted or corrected.

Set thresholds from service requirements and a measured baseline; no universal error-rate or latency threshold fits every application. Record prompt, model, and relevant configuration versions so a change can be investigated. Keep logs proportionate: redact or avoid sensitive content and apply retention controls. Use sampled traces or derived metrics when full payload logging is unnecessary.

Model behavior, external data, prompts, and provider implementations can change. Re-run an evaluation set when a material component changes and compare results by important task slices. [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) owns task-quality definitions, dataset design, judge validation, and acceptance evidence. Keep a rollback or fallback path when a release misses the agreed quality bar.

### How can feedback improve the product? / 如何让反馈改进产品？

Collect explicit signals such as ratings or corrections and implicit signals such as task completion, accepted suggestions, repeated requests, and escalation. These signals are incomplete and biased: a rating reflects who chose to respond, while time spent can mean either engagement or confusion. Interpret them alongside representative task evaluation and user research.

A practical improvement loop is:

1. Capture feedback with relevant task and version context, subject to privacy and retention rules.
2. Review a sample and classify its failure mode.
3. Fix the appropriate layer: source data, retrieval, prompt, tool, model choice, interface, or policy.
4. Test the change on held-out cases and monitor the relevant production outcome.
5. Keep or roll back the change using the agreed criteria.

Preference data may inform fine-tuning or preference optimization, but a feedback button alone does not create a validated training signal. See [Fine-tuning Strategies / 微调策略](#17.%20%E4%BD%95%E6%97%B6%E5%BA%94%E5%BE%AE%E8%B0%83%E6%9D%A5%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F). For permission boundaries, human approval, and production stop paths, see [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

**Related note / 相关笔记：** [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) defines the durable run state and recovery contract that lets service metrics and task feedback remain attached to one logical operation.

**Source boundary / 来源边界：** These monitoring and feedback practices reorganize the existing architecture note. Thresholds, task metrics, and data-retention rules must come from the particular service's requirements and privacy constraints; this note does not prescribe universal numeric targets.
## 21. How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？

**Core explanation / 核心解释：** Clarify the user task and its success criteria, make workload and data-boundary assumptions explicit, then trace the request through retrieval, model or tool calls, validation, delivery, and operations. Deep-dive only on the risks that bind correctness, privacy, latency, cost, or safety; compare alternatives against evidence and include evaluation, rollout, and rollback. This capstone applies the canonical mechanisms to three illustrative designs. All traffic and latency figures below are hypothetical teaching assumptions, not production measurements or defaults. / 先澄清用户任务与成功标准，明确工作负载和数据边界假设，再沿着检索、模型或工具调用、校验、交付和运维梳理请求路径。只深入分析决定正确性、隐私、时延、成本或安全的关键风险；依据证据比较方案，并说明评估、发布和回滚。本文用三个示例设计应用各主题的规范机制。下方流量与时延数字均为教学假设，并非生产测量或默认值。

**Key terms / 关键术语：** requirements / 需求；data flow / 数据流；failure mode / 失败模式；trade-off / 权衡；evaluation / 评估；rollback / 回滚。

### How should you structure an AI system design answer? / 如何组织 AI 系统设计回答？

Use the following sequence as a set of discussion slots, not a fixed interview timetable:

1. **Clarify the task.** Identify users, inputs and outputs, success criteria, unacceptable errors, data sensitivity, freshness, and human review needs.
2. **Establish constraints.** Ask about expected workload and peaks, latency and availability goals, budget, deployment boundary, existing systems, and operational ownership. State assumptions when information is unavailable.
3. **Draw the end-to-end path.** Include ingestion if needed, request handling, model or retrieval calls, tools, validation, response or escalation, storage, and observability.
4. **Deep-dive on the binding risks.** Choose two or three components whose failure would most affect correctness, privacy, latency, cost, or safety. Explain alternatives and failure handling.
5. **Explain evaluation and rollout.** Define offline cases, production measures, staged release, rollback, and who responds to incidents.

Do not invent scale or latency targets to fill silence. Ask for them or label an assumption, then show how the design would change if it differs.

### Common trade-offs / 常见权衡

| Decision | Option A | Option B | What should drive it |
|---|---|---|---|
| Latency and cost | Smaller or fewer model calls | More capable model or additional checks | Measured task quality, workload, and response-time needs |
| Retrieval | Lower-cost candidate set | More recall or reranking work | Miss cost, corpus, and evaluation results |
| Autonomy | Model-directed tool loop | Fixed workflow or human review | Task variability, action risk, and control needs |
| Response mode | Immediate response | Queued or batch completion | User expectation and throughput |
| Deployment | Hosted service | Self-hosted or edge | Data boundary, operations, device, availability, and full cost |

Present each choice conditionally: explain when each option would fit, what evidence would change your decision, and how the alternative could be tested.

### Three cases, three binding risks / 三个案例，三个主要风险

Apply the same design sequence to different failure costs. For document QA, ask whether the evidence is authorized and current. For refunds, ask whether an irreversible write was authorized and actually completed. For code review, ask whether the finding is supported and worth a reviewer’s time.

### Document QA under an access and latency budget / 有权限与时延约束的文档问答

**Clarify first:** Which user groups and repositories are in scope? How often do documents change? What is the source of truth for permissions? What answer freshness and citation behavior are required? What happens when evidence is missing or conflicting?

**Illustrative request path / 请求路径示意:**

~~~text
Document sources → parse and version → chunk and index
User query → authenticate → permission-aware retrieval
            → rank evidence → generate answer with source references
            → validate and return, or abstain/escalate
~~~

**Deep-dive topics:**

- **Ingestion and freshness:** retain source identifiers and versions; reprocess changed or deleted material and make indexing status observable.
- **Retrieval:** compare keyword, vector, or hybrid retrieval on representative questions. Tune chunking and reranking against recall, relevance, latency, and cost; there is no universal chunk size or top-k.
- **Authorization:** derive the caller's access from the trusted identity system and enforce it during retrieval, before evidence reaches the model. A prompt is not an access-control boundary.
- **Grounded answers:** carry source identifiers alongside retrieved passages. Validate that citations refer to retrieved evidence and evaluate whether claims are supported; asking for citations alone does not prove correctness.
- **Failure paths:** stale or empty results, permission-service outage, conflicting documents, malformed output, and model timeout should have explicit behavior.

**Evaluation and operations:** test retrieval and answer quality separately; include permission-boundary cases, updates and deletions, unanswerable questions, and citation checks. Monitor latency by stage, indexing freshness, retrieval metrics, answer support, abstentions, and access-control failures.

The [RAG chapter](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) follows a concrete policy question from authorized candidate retrieval through claim verification. Here the extra constraint is an end-to-end latency budget.

#### One worked budget and design choice / 一组预算推导与方案选择

Assume a fictional enterprise team has a pre-indexed policy corpus; employee questions include both natural-language policy questions and exact policy IDs; peak load is 6 queries per second; the p95 end-to-end target is 4 seconds; a hosted model API is allowed; and the team has no capacity allocated to operating GPU inference for this workload. These are interview assumptions, not observed traffic or latency.

One proposed latency budget is 0.2 s for authentication and request setup + 0.6 s for permission-aware retrieval + 2.5 s for model generation + 0.2 s for validation and response handling + 0.5 s reserved for network and queueing = 4.0 s. These are allocations to validate, not measured stage percentiles; the sum of component p95s is not itself a statistical p95 guarantee. Instrument each stage and load-test the composed service.

For a rough capacity check, use Little's Law L = λW for the mean number of requests in a stable system ([Little](https://doi.org/10.1287/opre.9.3.383)). Suppose the explicit design assumption is an admitted 6 requests/s and 1.2 s mean time spent in the model stage, including any internal wait. Then L = 6 × 1.2 = 7.2, or about 8 requests in flight in that stage. This is an average, not 8 active model slots or a replica count; queueing, bursts, and service limits need load tests with the real model, request lengths, and latency target. Size executing slots from measured service demand and the target utilization.

For these mixed exact-ID and natural-language questions, I would test hybrid keyword and vector retrieval against a lexical baseline, enforce document permissions before context assembly, and evaluate retrieval and answer quality separately. Given the stated hosted-service permission and lack of capacity for operating GPU inference, I would put a hosted model behind that retrieval service, keep authorization outside the prompt, and bound queueing so overload does not silently consume the latency budget. If the data boundary changed, I would compare a private or self-hosted endpoint and include its operations cost; if retrieval or generation cannot fit the measured budget, I would revisit context selection, candidate ranking, and the model before relaxing answer-quality checks.

### Refunds with a verified side effect / 需要确认写入结果的退款

**Clarify first:** Which intents can be automated? Which actions change customer accounts or money? What policy and order systems are authoritative? Which requests require explicit consent or human review? What is the handoff path?

**Worked choice / 方案选择：** Suppose the supported flow is checking an order and requesting a refund, and policy disputes or tool failures need a person. I would use a fixed sequence: authenticate the customer; read the order and current policy; have application code check eligibility; show the proposed refund and ask for confirmation; call an idempotent refund operation; verify its result; then report the outcome or hand off. The sequence is predictable and changes financial state, so a fixed workflow makes authorization and stop points explicit. An agent loop would need evidence that dynamic tool choice materially helps before adding that control surface.

**Illustrative architecture / 架构示意:**

~~~text
Customer → intent and risk handling → assistant workflow
                                      ↙          ↘
                          read-only order/FAQ    bounded action tools
                                      ↘          ↙
                              validation → response or human handoff
~~~

**Tool and policy design:**

- Separate read-only lookup from actions that change state.
- Give the runtime—not the model—responsibility for identity, authorization, business limits, confirmation requirements, and final tool execution.
- Make retryable writes idempotent where the underlying system supports it; log the request outcome without exposing unnecessary personal data.
- Use a fixed workflow for a predictable sequence. Consider an agent loop only where dynamic tool selection adds value and can be bounded, observed, and stopped.
- Provide explicit handling for ambiguous intent, unavailable tools, policy conflicts, and user requests for a person.

**Evaluation and operations:** use reviewed examples for common intents, boundary cases, policy changes, tool failures, and escalation. Track task completion, human handoff, tool errors, unauthorized-action attempts, user feedback, and cost per resolved interaction. Treat the automation target as a product decision supported by evaluation, not a fixed percentage.

A tool-call schema can constrain the shape of a proposed call; the application must still check whether the user and action are permitted. OpenAI's [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, illustrates provider-specific behavior; it does not replace application-side validation and authorization. See [Agent Fundamentals / 智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F), [Tool Design and Function Calling / 工具设计与函数调用](#11.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F), and [AI Safety in Production / 生产环境中的 AI 安全](#14.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

### Code review with a limited false-positive budget / 有误报预算的代码审查

**Clarify first:** Which languages and review types are in scope? Should findings be advisory or posted automatically? How is repository context selected? What level of false positives will developers tolerate? Which code or metadata may leave the repository boundary?

**Worked choice / 方案选择：** Suppose the team has low tolerance for noisy comments and wants a human to retain review authority. I would begin with advisory draft comments, require each finding to point to changed lines and cite the relevant code evidence, and suppress weak findings rather than posting every possible concern. I would not auto-approve or block a pull request. This favors developer trust and gives the team dismissal data before considering more automation.

**Illustrative architecture / 架构示意:**

~~~text
Pull request event → diff and repository context
                   → one or more review passes
                   → schema and location validation
                   → deduplicate and rank findings
                   → draft comments for human review
                   → collect feedback and measure outcomes
~~~

**Deep-dive topics:**

- **Context selection:** include changed lines, nearby code, relevant callers, and repository guidance as available. Record what was omitted when size limits require truncation.
- **Review passes:** separate correctness, security, and style checks when that makes evaluation or prompts clearer. Keep each pass tied to a defined review rubric.
- **Output validation:** require a finding category, explanation, location within the diff, and actionable suggestion; reject locations or structures that do not match the submitted change.
- **Noise management:** rank or suppress uncertain findings, show evidence, and make dismissal easy. The acceptable precision/recall balance depends on developer workflow and risk.
- **Large or generated changes:** segment by file or coherent unit, avoid irrelevant generated content, then deduplicate before presenting results.

**Evaluation and operations:** build a held-out set of reviewed changes with known issues and clean examples. Measure issue detection by category, false positives, location validity, developer acceptance or dismissal, cost per review, and delay added to the workflow. Compare against a no-assistant baseline; do not claim to outperform human review without evidence.

### Practice / 练习

- Ask clarifying questions before fixing assumed scale or targets.
- Draw the request and data paths, including trust boundaries and failures.
- State assumptions and what evidence could change the design.
- Discuss quality, latency, cost, permissions, and operational ownership together.
- Explain how the system is evaluated, rolled out, monitored, and rolled back.

### Related notes / 相关笔记

- [Durable AI runs / 持久化 AI 运行](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) covers production run controls. [AI deployment choices / AI 部署选择](#6.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F) compares where to run the model.
- [RAG Architecture and Implementation / 检索增强生成](#10.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers retrieval implementation and grounding.
- [LLM Evaluation Methods / 大语言模型评估方法](#16.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation design.
- [Agent Fundamentals / 智能体基础](#12.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F) covers runtime agent patterns.
