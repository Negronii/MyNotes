# AI Engineering

> Generated from the [ai-engineering reading map](../../ai-engineering/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. How does an AI service turn one message into a complete answer?

### Case study — explaining a failed build

Imagine a developer using an AI assistant connected to a build system. A build runs automated checks against a code change, and build `42` has failed. The developer asks, `Why did build 42 fail?` The failure details are stored in a log service that the assistant can query through a tool named `read_build_log`.

The assistant needs to retrieve that evidence and explain what it shows. We will follow this one question through the service, from preparing the model's input to returning an answer grounded in the log. The application manages access to the log service, while the model generates a request for the evidence and then an explanation using it. This is a fictional example of an application-managed tool loop.

The flow below follows the successful case. There are two model calls in this run. The first produces a tool request. After the application reads the log, the second produces the answer. If another question already contains enough evidence, the model can answer on its first call.

~~~mermaid
flowchart TD
    Input["1 Prepare input<br/>Question + instructions + tool definition"]
    Model["2 Run the model<br/>Generate the next output"]
    Choice{"What did the model return?"}
    Tool["3 Execute the tool<br/>Check access, then read build 42"]
    Context["4 Update the input<br/>Include the call and its result"]
    Answer["5 Complete the run<br/>Save and return the explanation"]
    Input --> Model --> Choice
    Choice -->|Tool request| Tool
    Tool -->|Log evidence or an error| Context
    Context -->|Next model call| Model
    Choice -->|Final answer| Answer
~~~

### 1. Prepare what the model can see

The harness is the application code that coordinates the model and its tools. It records the caller's identity, selects the information for the model, executes tools, and decides when the application has a result to return. Here, the first model call has three inputs.

| Input | Content in this example |
| --- | --- |
| Application instruction | Explain the build failure using available evidence. |
| User message | `Why did build 42 fail?` |
| Tool definition | `read_build_log` accepts an integer `build_id` and returns failure records from the build log. |

The tool definition describes an available operation. The log itself enters the conversation only after the application retrieves it. The caller's identity is retained by the application for permission checks.

These inputs form the model's context (上下文) for this call. In a longer conversation, the application would also choose which earlier messages and evidence to include. That selection matters because the model can only condition its output on information actually supplied to it and knowledge encoded in its trained parameters. [Choosing the information for each model call](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)

### 2. Generate a request for the missing evidence

The model now has the question and a way to ask for logs. During inference (推理), it processes that input and generates an output one token (词元) at a time. In this run, the output specifies `read_build_log` with `build_id` set to `42`.

How can a sequence of numerical operations produce that request? We can follow the transformations inside a simplified decoder-only Transformer (仅解码器 Transformer). The small dimensions and numerical values below illustrate the computation. They are not measurements of a model responding to this question.

#### Turn the input into token IDs and vectors

The inference service formats the messages and tool definition for the model. A tokenizer (分词器) converts that formatted input into integer IDs. For a concrete example, encoding just `Why did build 42 fail?` with `tiktoken 0.12.0`, using `cl100k_base`, gives the following pieces and IDs.

| Token pieces | Token IDs |
| --- | --- |
| `"Why", " did", " build", " ", "42", " fail", "?"` | `10445, 1550, 1977, 220, 2983, 3775, 30` |

This tokenizer applies byte pair encoding (字节对编码), or BPE, to byte sequences, repeatedly merging adjacent pieces according to learned merge priorities. A piece can include a leading space. The full model input also contains the instructions, tool description, and formatting markers. Let `T` be the length of that entire sequence. [How token boundaries are chosen](#How%20does%20the%20tokenizer%20choose%20token%20boundaries?%20/%20%E5%88%86%E8%AF%8D%E5%99%A8%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E8%BE%B9%E7%95%8C%EF%BC%9F)

An embedding table (嵌入表) maps each ID to a learned vector. With vocabulary size `N` and a deliberately small model width of `8`, the table has shape `N × 8`. ID `2983`, for example, selects row `2983`. Looking up every ID produces a `T × 8` hidden state (隐层状态), with one row per position. Later layers update these rows using the surrounding context.

#### Let each position gather relevant information

Attention (注意力) lets a position gather information from other visible positions. In this example, each of two attention heads (注意力头) takes the normalized `T × 8` state and uses three learned `8 × 4` projection matrices to produce Query (查询), Key (键), and Value (值), abbreviated Q, K, and V. Each resulting matrix has shape `T × 4`.

With rotary position embedding (旋转位置编码), or RoPE, Q and K are first rotated according to position. For one position, its Q is compared with each position's K by taking their dot product and dividing by `√4`. A causal mask (因果掩码) excludes positions to the right of the query. Softmax converts the remaining scores into weights that sum to one, determining how much each visible V contributes to the result. [The QKV calculation](#How%20do%20Q,%20K,%20and%20V%20produce%20the%20attention%20update?%20/%20Q%E3%80%81K%E3%80%81V%20%E6%80%8E%E6%A0%B7%E4%BA%A7%E7%94%9F%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F) · [Transformer §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) · [RoFormer §3.2](https://arxiv.org/html/2104.09864v5#S3.SS2)

Take the row for the question mark in the user message. For this arithmetic illustration, keep only `build` and `42`, and assign them weights of `0.25` and `0.75`. If their V vectors are `(1, 0, 0, 0)` and `(0, 2, 0, 0)`, the result is `(0.25, 1.5, 0, 0)`.

Each head performs its own calculation. At each position, their two width-`4` results are concatenated into a width-`8` vector, then mixed by an `8 × 8` output projection. A residual connection (残差连接) adds this update to the input state. The result still has shape `T × 8`, now with information gathered across positions.

#### Transform the information within each position

A feed-forward network (前馈网络), or FFN, then transforms each row independently using shared learned weights. Attention has brought contextual information into a row. The FFN can combine those features nonlinearly and write an update back into that row.

Using SwiGLU in our small model, two `8 × 16` projections of the normalized state produce candidate values and gate inputs. SiLU is applied to the gate inputs, and the two branches are multiplied element by element. For the question-mark row, suppose one candidate channel is `3` and its gate input is `1`. SiLU turns `1` into approximately `0.73`, so that channel becomes approximately `2.19`. A `16 × 8` down projection returns the result to the model width, and a residual connection adds it to the state produced by attention. The gate depends on the current row, allowing the same learned weights to produce different updates for different contexts. [FFNs and stacked layers](#What%20does%20the%20FFN%20add,%20and%20how%20do%20blocks%20stack?%20/%20FFN%20%E5%A2%9E%E5%8A%A0%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B1%82%E6%80%8E%E6%A0%B7%E5%A0%86%E5%8F%A0%EF%BC%9F) · [GLU Variants §2](https://arxiv.org/html/2002.05202#S2)

One Transformer layer combines these attention and FFN operations with normalization and residual connections. Each layer passes its `T × 8` output to the next layer, which has its own learned parameters. The diagram tracks the shapes through one layer of our example, including normalization before each sublayer.

~~~mermaid
flowchart TD
    X["Layer input<br/>T × 8, one row per token"]
    Norm["Normalize for attention<br/>T × 8"]
    H1["Head 1<br/>Q, K, V each T × 4<br/>Weighted output T × 4"]
    H2["Head 2<br/>Q, K, V each T × 4<br/>Weighted output T × 4"]
    A["Concatenate, then project<br/>T × 8"]
    R["Add attention update to layer input<br/>T × 8"]
    F["Normalize, then SwiGLU FFN<br/>Two T × 16 branches<br/>Gate, multiply, project to T × 8"]
    Y["Add FFN update<br/>T × 8 for the next layer"]
    X --> Norm
    Norm --> H1 & H2
    H1 & H2 --> A --> R
    X -->|Residual| R
    R --> F --> Y
    R -->|Residual| Y
~~~

#### Convert the final state into output tokens

Processing the initial input is called prefill (预填充). After the last layer and final normalization in this example, the language model head, usually called the LM head, uses the vector at the last position of the complete formatted input to predict the first new token. Causal attention allows that position to attend to the whole supplied prefix. It may be an assistant-start marker added by the input template. [Chat templates and generation markers](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)

The LM head projects that width-`8` vector through an `8 × N` matrix to obtain logits (未归一化分数), one score for each vocabulary entry. Decoding (解码) selects an ID, either by taking the highest score or by sampling from a probability distribution derived from the scores. The selected ID is appended to the sequence, and the model predicts the next one from the new position.

A KV cache (键值缓存) retains K and V for previous positions in each layer. At the new position, the model computes Q, K, and V, then uses that Q to attend to both the cached K/V and the new position's own K/V. It appends the new K/V to the cache for subsequent steps. Previous positions' Q vectors have already served their calculations and are not needed for this step. [Decoding and KV cache](#17.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) · [Transformers cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation)

For our build question, this generation produces the tool name and arguments in the model's tool-call format. The inference service interprets the generated tokens according to the model's tool-call protocol and exposes the completed tool name and arguments as a structured API item. In a simplified notation, the application receives `tool_call(c1, read_build_log, {build_id: 42})`. The ID `c1` will associate the tool's result with this particular request. The harness dispatches it to the tool handler, taking the tool branch in the overview. [OpenAI tool-calling flow](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) · [Claude application-managed tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools)

### 3. Execute the request and retrieve the log

The application checks that `read_build_log` is available, that `build_id` has the required integer type, and that the caller may read build `42`. Argument validation establishes that the request can be interpreted. Authorization (授权) establishes which resource the caller may access. The application reads the log only after these checks succeed. [Tool contracts and authorization](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)

The retrieved result contains the evidence the model was missing.

| Field in the result for `c1` | Value from build `42` |
| --- | --- |
| Failed step | `unit-tests` |
| Failed test | `reject_empty_name` |
| Failed assertion | A request with an empty name should return HTTP `400`, but returned `200`. |
| Process exit status | `1` |

If authorization fails, the application can return a failure result for `c1`, allowing the next model call to explain that the evidence is unavailable. Here the tool retrieves one known log by ID. When a question requires finding relevant passages across many documents, the application can retrieve them and supply them to the model to generate an answer. This retrieval-and-generation process is called retrieval-augmented generation (检索增强生成), or RAG. [Retrieving and grounding an answer](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)

### 4. Let the model use the retrieved evidence

The application now makes another model call. Alongside the original question and instructions, it includes the model's `tool_call(c1, …)` and the matching `tool_result(c1, …)`. The call records what was requested. The result supplies what the tool actually observed.

This second input contains `unit-tests`, `reject_empty_name`, and the expected `400` versus observed `200`. Those details are formatted and encoded as part of the model's context. The same inference mechanism processes the expanded input using the same trained weights. The new evidence changes what the model can base its answer on. It does not require retraining the model.

If the evidence leaves a gap, the model can request another tool call, and the application repeats validation, execution, and result collection. In this case the log is enough to describe the observed failure, so the model generates an explanation. Determining the underlying code defect would require further evidence, such as the implementation and the intended behavior. [Actions, observations, and the next decision](#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

### 5. Return the explanation and complete the run

The answer can now state what the log establishes.

> Build 42 failed at the `unit-tests` step. The `reject_empty_name` test expected HTTP `400` for a request with an empty name, but received `200`. The test process exited with status `1`. To identify the underlying cause, check the request-validation logic against the test's expected behavior.

The first model call ended with a tool request, leaving the application with work to do. The second ends normally with an answer. In this example, the application saves that answer and marks the run complete before returning the result to the caller. If it streams text as it is generated, the application must still track whether generation ultimately completed or failed. [Run state and recovery](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F)
## 2. How does a language model turn a prompt into text? / 语言模型怎样把一段 prompt 变成文本？

**Short answer / 简答** — A tokenizer maps text to IDs. Embedding lookup gives each ID an initial vector. A stack of causal Transformer blocks mixes information between positions with attention and transforms each position with an FFN. The final vector at the last position scores the vocabulary. A decoding rule chooses the next token, and the loop continues until a stop condition is met. / 分词器把文本转成 ID，嵌入表查找给每个 ID 一个初始向量。多层因果 Transformer 依次用注意力在位置之间传递信息，再用前馈网络变换每个位置的表示。最后一个位置的向量为整个词表打分，解码规则选出下一个词元，重复直到满足停止条件。

以下用一个简化的 **decoder-only Transformer / 仅解码器 Transformer** 跟踪同一批张量。它采用预归一化、因果自注意力和门控 FFN，形状用刻意缩小的例子展示。这是理解一类常见模型的计算图。消息组装、工具执行和最终答复的交付由 AI 应用的运行时负责。[How an AI service turns one message into a complete answer](#1.%20How%20does%20an%20AI%20service%20turn%20one%20message%20into%20a%20complete%20answer?)

~~~mermaid
flowchart LR
    Text["Text and chat template"] --> IDs["Token IDs"]
    IDs --> E["Embedding lookup"]
    E --> A["Causal attention mixes positions"]
    A --> F["FFN transforms each position"]
    F -->|next block| A
    F -->|after the last block| L["Vocabulary logits"]
    L --> D["Choose one token"]
    D --> Out["Decode available text"]
    D -->|continue with new token and stored K/V| E
~~~

### How does the tokenizer choose token boundaries? / 分词器怎样决定边界？

Token（词元）是特定词表中的编码单位。它可能是字节、标点、带空格的片段、词的一部分或完整词。下面跟踪 **byte-level BPE / 字节级字节对编码**。一种常见实现先按正则做预分词（pre-tokenization），再对每段的 UTF-8 字节独立做合并。训练分词器时统计相邻对的频率，合并最高频的对并重新统计。部署时词表和优先级已固定，编码器只应用已学到的合并规则。

用三段训练输入 `abab`、`ab`、`ac` 举例。初始词表有 256 个单字节。第一轮相邻对 `a+b` 出现三次，新增 `ab`。训练段变成 `[ab, ab]`、`[ab]`、`[a, c]`。第二轮 `ab+ab` 与 `a+c` 各出现一次，假设固定的同频规则选择先遇到的 `ab+ab`，新增 `abab`。

| 阶段 | 中间状态 |
| --- | --- |
| 已学合并表 | 先 `a+b → ab`，后 `ab+ab → abab` |
| 编码从未见过的 `ababca` | `[a,b,a,b,c,a] → [ab,a,b,c,a] → [ab,ab,c,a] → [abab,c,a]` |
| 查 toy 词表 | 若按合并顺序为新词元编号，结果是 `[257,99,97]` |

真实例子在 `tiktoken` 0.12.0 的 `cl100k_base` 上实测。输入 `The transformer architecture revolutionized NLP.` 得到八个词元 `["The", " transformer", " architecture", " revolution", "ized", " N", "LP", "."]`，ID 是 `[791,43678,18112,14110,1534,452,12852,13]`。空格是其中一些词元的组成部分。不同分词器会给同一段文本不同的切法。工程上要用部署模型的编码器和实际请求格式计数。聊天角色、工具定义、图片等还可能增加服务端处理的输入。字节级词元可以切在 Unicode 字符内部，流式输出要用增量解码或服务端的文本事件，避免把每个词元的字节单独当成完整字符串。

BPE 是一种实现选择。原始 Transformer 的翻译实验也分别使用了 BPE 和 word-piece 词表。子词 BPE 的早期方法见 [Sennrich et al., §3.2](https://aclanthology.org/P16-1162/)，字节级训练、编码和解码见 [tiktoken 0.12.0 教学实现](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken/_educational.py)，原始翻译训练数据见 [Transformer §5.1](https://arxiv.org/html/1706.03762v7#S5.SS1)。

### What enters the first block? / 第一层拿到什么？

令词表大小为 $V$，模型宽度为 $d$，输入长度为 $T$。一条样本的 ID 是长度 $T$ 的整数向量，嵌入表 $E$ 的形状是 $V \times d$。对于第 $i$ 个 ID $t_i$，直接取第 $t_i$ 行 $X_{0,i}=E[t_i,:]$。这在数学上等价于将 one-hot 行向量乘以 $E$，实际实现通常直接取行。$X_0$ 是 $T\times d$，每一行是一个位置的初始表示。把上节的 `[257,99,97]` 送入 toy 模型。它的词表有 256 个字节与两条合并结果，故 $V=258$、$T=3$、$d=8$，$E$ 是 $258\times8$，输入表示是 $3\times8$。批量运行再加上 batch 轴。

同一 token ID 的初始查表向量相同，后续表示还要依赖位置和上下文。原始 Transformer 把正弦位置编码加到输入表示。采用 **RoPE / 旋转位置编码** 的模型在注意力计算前按位置旋转 Q、K 的成对坐标，点积会包含相对位置信息。RoPE 是下面例子采用的路径，它不改变张量形状。 [Transformer §§3.4–3.5](https://arxiv.org/html/1706.03762v7#S3.SS4) · [RoFormer §3](https://arxiv.org/abs/2104.09864) · [Llama 3 论文 §3.2](https://arxiv.org/html/2407.21783v3#S3.SS2)

### How do Q, K, and V produce the attention update? / Q、K、V 怎样产生注意力更新？

**Query / 查询** 决定当前这行要匹配什么特征，**key / 键** 参与匹配打分，**value / 值** 提供按分数加权后传递的内容。它们是当前层对 token 表示做线性投影后的向量。以下把归一化后的输入写成 $U$，把当前层的注意力头数写成 $H_q$，每头宽度写成 $d_h$。先按普通多头注意力（MHA）计算，$H_q=2$、$d_h=4$。

| 运算 | 通用形状，不含 batch | 例子 |
| --- | --- | --- |
| $Q=UW_Q$，$K=UW_K$，$V_a=UW_V$ | 每个权重 $d\times (H_q d_h)$，每个投影 $T\times(H_q d_h)$ | $3\times8$ 乘 $8\times8$ |
| 拆头 | 每个头的 $Q_h,K_h,V_h$ 分别为 $T\times d_h$ | 每个头有三个 $3\times4$ 张量 |
| $S_h=Q_hK_h^\top/\sqrt{d_h}+M$ | $T\times T$，行是查询位置，列是键位置 | $3\times3$ |
| $Z_h=\operatorname{softmax}_{\rm keys}(S_h)V_h$ | 每头 $T\times d_h$ | $3\times4$ |
| $A=\operatorname{Concat}(Z_1,\ldots,Z_{H_q})W_O$ | 拼接沿特征轴，$W_O$ 为 $(H_qd_h)\times d$，输出为 $T\times d$ | 两个 $3\times4$ 拼成 $3\times8$，再乘 $8\times8$ |

上表按行向量右乘书写，所以权重形状是「输入宽度 × 输出宽度」。PyTorch `nn.Linear.weight` 存成「输出宽度 × 输入宽度」，前向用它的转置相乘。Q、K 在投影拆头后、计算分数前应用 RoPE。 [PyTorch Linear](https://docs.pytorch.org/docs/stable/generated/torch.nn.Linear.html)

因果掩码 $M_{ij}$ 在 $j>i$ 时为 $-\infty$，其余为零，所以 softmax 沿 key 位置把未来位置的权重变成零。全量 dense attention 在 prefill 中要为每个头处理随 $T^2$ 增长的位置对，实际时延还取决于内核、其他层和硬件。缩放项 $\sqrt{d_h}$ 让点积的量级随头宽增长时仍可控，避免 softmax 太容易饱和。若第二个位置的某个头在缩放后对前两个 key 的分数是 $[1,0]$，完整行就是 $[1,0,-\infty]$，softmax 约为 $[0.731,0.269,0]$。若对应两个 value 为 $(1,0,0,0)$ 和 $(0,2,0,0)$，这个头对第二个位置的输出就是 $(0.731,0.538,0,0)$。另一个头有自己的投影和加权结果。拼接后，$W_O$ 学会把各头特征混合成模型宽度，残差才可以把这次更新加回该位置的原向量。每个位置仍对应一行 hidden state（隐层状态）。 [Transformer §§3.2.1–3.2.3](https://arxiv.org/html/1706.03762v7#S3.SS2)

头在不同层和任务上可能形成不同的可观察行为，例如更重视前一个位置。这样的观察需要数据和干预支持。权重图只显示该头这次如何加权，其输出还取决于 value、$W_O$ 和之后的层。

**Grouped-query attention / 分组查询注意力（GQA）** 保留 $H_q$ 个查询头，把它们分成 $H_{kv}$ 组，每组查询头共享该组对应的一个 K 头和一个 V 头。若 toy 模型改成 $H_q=2,H_{kv}=1$，$W_Q$ 仍是 $8\times8$，$W_K,W_V$ 分别缩为 $8\times4$。两个 query 仍各自产生一个 $3\times4$ 的头输出，因此拼接和 $W_O$ 的形状维持原样。MHA 是 $H_{kv}=H_q$，multi-query attention（MQA）是 $H_{kv}=1$。改变的是模型学习和缓存的 K/V 头数，已有 MHA 权重不能直接删头当成 GQA。 [Ainslie et al., GQA §2](https://aclanthology.org/2023.emnlp-main.298/) · [Llama 3 §3.2](https://arxiv.org/html/2407.21783v3#S3.SS2)

### What does the FFN add, and how do blocks stack? / FFN 增加了什么，层怎样堆叠？

**Feed-forward network / 前馈网络（FFN，也常称 MLP）** 把已经吸收上下文的向量做非线性变换。注意力跨位置搬运信息，FFN 在每一行内部混合通道。各位置使用同一组 FFN 权重，每层通常拥有自己的权重。以 **SwiGLU / SiLU 门控前馈网络** 为例，令 $R$ 是注意力后的状态经归一化得到的 $T\times d$ 矩阵。忽略偏置，计算是

$$
F(R)=\big[\operatorname{SiLU}(RW_g)\odot(RW_u)\big]W_d,\qquad
\operatorname{SiLU}(x)=x\,\sigma(x).
$$

$W_g$ 和 $W_u$ 分别是 $d\times d_{ff}$ 的门控与上投影矩阵，产生两个 $T\times d_{ff}$ 张量。$\odot$ 在同一位置、同一通道相乘。$W_d$ 是 $d_{ff}\times d$ 的下投影矩阵，输出回到 $T\times d$。例如 $d_{ff}=16$ 时，两个 $3\times16$ 中间结果经门控再回到 $3\times8$。若某行的两个门控输入为 $[0,1]$，对应上投影值为 $[2,3]$，相乘后的两个通道约是 $[0,2.19]$。门控随上下文表示改变，是连续的特征变换。 [Shazeer, GLU Variants, §1](https://arxiv.org/html/2002.05202#S1)

为什么这对知识有用？例如注意力让某个位置的表示结合了人名和“篮球”语境，FFN 可以对这些特征组合产生不同响应，再把若干方向写回该位置。Geva 等在所分析的模型里观察到，FFN 的一部分激活与文本模式相关，值方向能影响预测分布。这是理解训练知识如何影响计算的一种解释。模型对某个事实的输出还依赖注意力、多个层的组合与输出投影，FFN 的权重无法像数据库记录那样按人名查出一条事实。 [Geva et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.446/)

在这个 **pre-norm / 预归一化** 的 block 里，注意力和 FFN 串行更新同一份残差流（residual stream）。给定上一层输出 $X_\ell$，

$$
Y_\ell=X_\ell+\operatorname{Attention}_\ell(\operatorname{Norm}_{\ell,1}(X_\ell)),\qquad
X_{\ell+1}=Y_\ell+F_\ell(\operatorname{Norm}_{\ell,2}(Y_\ell)).
$$

输出 $X_{\ell+1}$ 仍是 $T\times d$，再作为下一层输入。层叠加的是对同样一组位置的多轮变换，长度和宽度在这个例子里不逐层缩小。2017 年论文的 §3.3 已包含逐位置 FFN，使用两个线性层与 ReLU。论文当时是做翻译的 encoder–decoder，decoder 还有对 encoder 的交叉注意力，并在子层残差相加后做 LayerNorm。今天常见的 decoder-only 设计可使用预归一化、RMSNorm、RoPE、GQA 和门控 FFN。上述计算图以这些选择构成一个一致的例子，具体架构以模型实现为准。 [Transformer §§3.1–3.5](https://arxiv.org/html/1706.03762v7#S3) · [Meta Llama 3 参考实现](https://github.com/meta-llama/llama3/blob/main/llama/model.py)

**参数量 / Parameter count.** 忽略偏置和归一化参数，常规 MHA 且 $H_qd_h=d$ 时，Q、K、V、输出投影共 $4d^2$ 个参数。上述门控 FFN 有 $3dd_{ff}$ 个。在 toy 模型中分别是 $256$ 和 $384$。GQA 改的是 K/V 两个投影的宽度。总参数还包括嵌入表、每层归一化、最终归一化和可能独立的输出投影。层数乘的是每层自己的权重，权重共享时只计一次。推理时产生的 hidden state 和 KV cache 是运行时数据。

### How does the model choose a token and continue? / 模型怎样选词元并继续？

经过最后一个 block 和模型规定的最终归一化后，取最后一个有效输入位置的向量 $h_{\rm last}$，形状为 $1\times d$。语言模型头（LM head）把它乘以 $W_{\rm lm}$，形状为 $d\times V$，得到 $1\times V$ 个 **logits / 未归一化分数**。权重绑定（weight tying）的模型可用 $E^\top$ 作输出权重。每项分数对应一个词表 ID。这里 $V=258$，得到 258 个分数。训练时也可对每个位置分别投影。

采样时对 logits 应用温度 $\tau>0$，即 $p_i=\exp(z_i/\tau)/\sum_j\exp(z_j/\tau)$。低温度让分布更集中。贪心解码（greedy decoding）直接取最高分。top-k 只留下排名前 $k$ 的候选，top-p（nucleus sampling）保留概率和首次达到阈值 $p$ 的最小降序前缀，再归一化后采样。若约束后四个可选词元的概率为 $[0.50,0.30,0.15,0.05]$，top-p 为 $0.75$ 时留下前两个，重归一化为 $[0.625,0.375]$。采样策略控制输出分布，事实可靠性需要证据和评估。可用控制与组合规则因 API 和模型而异。 [Holtzman et al., §3](https://arxiv.org/abs/1904.09751) · [OpenAI Responses 参数参考](https://developers.openai.com/api/reference/resources/responses/methods/create)

**Prefill / 提示预填充** 处理提示序列，最后一个有效位置的 logits 选出第一个输出 token。之后每轮 **decode / 增量解码** 送入刚选出的 token，得到下一轮 logits。在带 KV cache 的因果模型中，过去位置看不到后来追加的 token，因此同一前缀下过去各层的 K、V 可复用。当前 query 需要给过去的 key 打分并读取对应的 value；过去的 query 已经完成对过去位置的更新，后面的注意力公式不需要它。每轮仍要产生新位置的 Q、K、V，并追加它的 K、V。序列按模型结束词元、应用约定的停止序列或输出长度上限等条件结束。应用层也可以停止转发或取消整个运行。 [Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation)

[GPU 推理服务的显存与调度](#17.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) 延伸这个机制，说明缓存要占多少字节，以及何时需要改进内核、分配或调度。 [上下文工程](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) 说明哪些信息应当进入这段前缀。

### How does next-token training update these parameters? / 下一词元训练怎样更新这些参数？

自回归训练使用同一条前向路径和因果掩码，但目标来自训练数据。在一个训练片段 `[BOS, a, b, c]` 中，位置 `BOS` 的标签是 `a`，位置 `a` 的标签是 `b`，位置 `b` 的标签是 `c`。用当前位置的 logits 对齐下一位置的真实 ID。单次前向可并行计算这些 logits，每个位置仍只能看到自身及之前的 token。**Teacher forcing / 教师强制** 指这里使用真实前缀。推理时则把实际选出的 token 作为后续输入。

对于真实目标 ID $y_i$，每个参与监督的位置使用交叉熵 $-\log p(y_i)$，再按有效标签平均。例如两个目标概率分别为 $0.8$ 和 $0.25$，平均损失约为 $0.805$ nats。单个位置的 logits 梯度为 $p-\operatorname{onehot}(y_i)$。反向传播（backpropagation）用链式法则把这个误差信号传过输出头、每一层的 FFN、注意力投影和嵌入。优化器根据梯度更新可训练参数。冻结参数或只训练适配器是[微调策略](#14.%20When%20should%20you%20fine-tune%20to%20close%20a%20repeatable%20behavior%20gap?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%9A%E8%BF%87%E5%BE%AE%E8%B0%83%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F)的选择。

这个目标和 **masked language modeling / 掩码语言建模** 不同。BERT 一类双向模型在可见左右上下文中预测选中的缺口，其默认推理目标与逐 token 续写不同。研究可以为掩码模型构造迭代填充采样，但那是另一条生成程序。 [Llama 3 预训练 §3](https://arxiv.org/html/2407.21783#S3) · [PyTorch 交叉熵定义](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html) · [BERT §3.1](https://arxiv.org/abs/1810.04805) · [Wang and Cho, BERT as a Markov Random Field](https://arxiv.org/abs/1902.04094)
## 3. How should you choose a model for a task and its deployment constraints? / 如何根据任务与部署约束选择模型？

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

Public benchmarks can help generate a shortlist when their task and protocol are relevant. They do not establish performance on a different prompt, data distribution, API configuration, or deployment. Keep an application-specific held-out set and report its sample scope and uncertainty. [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) explains how to choose task criteria and compare changes.

### Model tiers are shorthand, not a catalog / 模型档位只是简称，不是目录

Teams sometimes use labels such as **frontier**, **balanced**, and **fast** to describe rough cost, latency, and capability tradeoffs within a provider's current catalog. Those labels are not shared standards: a “fast” model can be the better choice on a narrow task, and a “frontier” label does not prove quality on yours. Avoid copying an undated model list or treating a prior ranking as a current fact. Verify the exact model ID, supported API features, context limit, and pricing in the provider's current documentation when making a real selection.

### Hosted API, open-weight, or hybrid? / 托管 API、开放权重还是混合部署？

| Approach | Potential advantages | Costs and constraints to compare |
|---|---|---|
| **Hosted API / 托管 API** | Quick access to managed inference and model updates; less serving infrastructure to operate. | Data flows and retention depend on provider terms and configuration; usage, rate limits, availability, and model lifecycle are provider-controlled. |
| **Open-weight deployment / 开放权重部署** | More control over serving location, model version, and infrastructure choices. | A weight license is not automatically an open-source license or permission for every use. The operator owns hardware, serving, security, scaling, and updates. |
| **Hybrid / 混合部署** | Different models or environments can serve distinct workload classes. | Adds routing, evaluation, observability, policy consistency, and failure paths across systems. |

This is an eligibility and trade-off comparison, not a universal deployment ranking. Edge, self-hosted capacity, and detailed operating responsibilities have their own constraints; see [AI Deployment Patterns / AI 部署模式](#18.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F).

Do not pick a hosting pattern from API spend alone. A useful estimate is:

$$
\text{total cost} \approx \text{inference usage} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and risk controls}
$$

Compare the same workload, quality target, peak traffic, and data constraints. A provider API may suit rapid iteration; self-hosting may suit a real data-control or workload need; edge deployment can help when offline operation or device constraints dominate. The break-even point depends on the actual workload and people costs.

### Route by measured need / 按实测需求路由

Routing can send simple, low-risk requests to a cheaper model and reserve a more capable option for cases that benefit from it. First measure whether the router's errors, added latency, and maintenance are outweighed by the savings. Use a task-relevant fallback when routing confidence is insufficient, and ensure high-impact operations still pass application-side authorization. Do not label “classification,” “reasoning,” or “extraction” as automatically easy or hard across all models.

Routing and other service optimizations need a fixed quality bar and end-to-end measurements; see [How to reduce AI application latency and cost / 如何降低 AI 应用时延与成本](#16.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F). To connect versioned results and user feedback to an improvement or rollback decision, see [Production observability and feedback / 生产可观测性与反馈](#19.%20How%20do%20you%20monitor%20a%20production%20AI%20feature%20and%20turn%20feedback%20into%20a%20safe%20improvement?%20/%20%E5%A6%82%E4%BD%95%E7%9B%91%E6%8E%A7%E7%94%9F%E4%BA%A7%E4%B8%AD%E7%9A%84%20AI%20%E5%8A%9F%E8%83%BD%E5%B9%B6%E5%AE%89%E5%85%A8%E5%9C%B0%E6%94%B9%E8%BF%9B%EF%BC%9F).

### Multimodal capability / 多模态能力

“Multimodal” does not specify which input or output a model supports or how well it handles a task. Test the actual modality and input shape—such as a chart, scanned document, spoken utterance, or video sample—under the target API. Check model documentation for supported formats, limits, and feature combinations at the time of deployment.

### Related notes / 相关笔记

- [AI Deployment Patterns / AI 部署模式](#18.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F) compares hosted, self-hosted, edge, and hybrid operating patterns.
- [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) defines run identity, persistence, and recovery behavior across request channels.
- [Context Engineering Principles / 上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) covers token budgets and provider-specific prompt caching.
- [Fine-tuning Strategies / 微调策略](#14.%20When%20should%20you%20fine-tune%20to%20close%20a%20repeatable%20behavior%20gap?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%9A%E8%BF%87%E5%BE%AE%E8%B0%83%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F) distinguishes behavior adaptation from maintained external knowledge.
- [RAG Architecture and Implementation / 检索增强生成](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers current or access-controlled external evidence.

### Sources / 来源

- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Its guidance treats prompting, context, fine-tuning, and evaluation as task-specific optimization levers rather than a universal linear ladder.
- For current OpenAI model IDs and feature support, consult the changing [Models documentation](https://developers.openai.com/api/docs/models), checked 2026-10-15.
## 4. How do you write a prompt that makes a task clear and testable? / 如何编写清楚且可检验的任务提示词？

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

Application code should check allowed categories and required fields, and verify any consequential claim against its source. For the broader distinction between task success, factual correctness, source support, and instruction adherence, see [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F).

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

- [Advanced Prompting Techniques / 高级提示技巧](#5.%20Which%20prompting%20technique%20should%20you%20try%20when%20a%20simple%20prompt%20fails?%20/%20%E7%AE%80%E5%8D%95%E6%8F%90%E7%A4%BA%E5%A4%B1%E8%B4%A5%E6%97%B6%E5%BA%94%E5%B0%9D%E8%AF%95%E5%93%AA%E7%A7%8D%E6%8F%90%E7%A4%BA%E6%8A%80%E5%B7%A7%EF%BC%9F) covers optional methods for failures that a clear baseline prompt does not resolve.
- [Context Engineering Principles / 上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains how to select and update the full information available to each inference.
- [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) explains why prompts cannot replace runtime authorization and stop controls.

### Sources / 来源

- OpenAI, [Model optimization: write effective prompts](https://developers.openai.com/api/docs/guides/model-optimization#write-effective-prompts), checked 2026-10-15.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. API behavior and supported schema features can change.
## 5. Which prompting technique should you try when a simple prompt fails? / 简单提示失败时应尝试哪种提示技巧？

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

Use a fixed prompt chain when the task has separable steps and code can validate, branch, retry, or stop between them. If the sequence is known, developer-controlled stages can be easier to inspect than an open-ended agent loop. Each model call can still be wrong; validate intermediate outputs and test the whole chain. For broader workflow and delegation patterns, see [Orchestration Patterns / 编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F).

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

A practical loop is to define success criteria, generate or revise candidates, compare them on the same development set, review regressions and edge cases, then confirm the selected version on an untouched held-out set before deployment. Keep the evaluation data appropriate for the sensitivity and policy of the task. [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation design and acceptance evidence.

### Related notes / 相关笔记

- [Prompt Engineering Fundamentals / 提示工程基础](#4.%20How%20do%20you%20write%20a%20prompt%20that%20makes%20a%20task%20clear%20and%20testable?%20/%20%E5%A6%82%E4%BD%95%E7%BC%96%E5%86%99%E6%B8%85%E6%A5%9A%E4%B8%94%E5%8F%AF%E6%A3%80%E9%AA%8C%E7%9A%84%E4%BB%BB%E5%8A%A1%E6%8F%90%E7%A4%BA%E8%AF%8D%EF%BC%9F) covers clear instructions, examples, and output contracts.
- [Context Engineering Principles / 上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) covers the information available to each inference.
- [Agent Fundamentals / 智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F), [Orchestration Patterns / 编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F), and [Tool Design and Function Calling / 工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F) cover runtime tool loops and control flow.

### Sources / 来源

- Wei et al., [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903).
- Kojima et al., [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916).
- Wang et al., [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171).
- Zhou et al., [Large Language Models Are Human-Level Prompt Engineers](https://arxiv.org/abs/2211.01910), for the APE instruction-generation and selection approach.
- OpenAI, [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices), checked 2026-10-15. These instructions describe OpenAI reasoning models and should not be generalized to other APIs.
- OpenAI, [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation), checked 2026-10-15. This is an OpenAI-specific example of generating or revising prompt text, not evidence that a generated prompt performs better without task evaluation.
## 6. What should each model inference see, and what should the application persist? / 每次模型推理应看到什么，应用应持久化什么？

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

**隔离上下文：** 子智能体不会天然共享同一份记忆。清楚传递目标、必要背景和结果格式；需要一致决策时，明确由主 agent 汇总和核对。切分依据应是任务边界、权限或可验证的并行收益，而不是把完整历史复制给每个工作者。按问题类型交接时，若下一步仍依赖先前约束或发现，摘要可能丢失细节；可先尝试在主循环中保留共享状态并按需加载专业流程，再评估是否需要分拆。[Anthropic 的 folding 文章，“Combining domain agents”](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)；决策方法见[编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

### How should a request preserve a reusable prefix? / 请求怎样保留可复用的前缀？

**KV cache 与 prompt caching 是相关但不同的复用机制 / KV cache and prompt caching are related but distinct reuse mechanisms.**

本节处理应用能控制的前缀布局。逐层 KV 载荷、分页和批处理见 [GPU 推理容量](#17.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F)。

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
| **接受系统级变更** | 保留已验收配置及其证据；后续候选仍需[重新验收](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。 |

[*Scaling Discovery Requires Forgetting* v1（2026-10-14，§§3.1–4.3、Appendix B p. 13、§6）](https://arxiv.org/abs/2610.20563v1) 的 Forget 同时清空 session 与候选搜索历史，只保留最佳候选及分数，以相同首轮指令重启。证据来自四项外部评分的优化任务、一个 harness/model 配置；它没有建立适用于一般任务的重置规则。

GitSwarm 用可分支的共享 Git 仓库和原子提交（atomic commit）保存中间产物。Git 的物理父提交（physical parent）记录开始工作的树；强制字段 `informed_by=` 记录 worker 声明的语义来源，且必须包含 parent、可增加其他分支来源。这是来源追踪，不是因果证明。主要积累证据来自同题跨 episode；单独把已完成搜索的获胜提交作为种子，仍是同一 RMT 任务，不能外推成任意跨任务迁移。worker 使用的 LLM 在 run 中保持固定；架构搜索改进的是被研究的另一模型，不能写成 worker 权重自行学习。[GitSwarm v1（2026-10-04，§§2.2、3.3–3.4、4）](https://arxiv.org/html/2610.04862v1)

**工程建议 / Engineering advice：** 将代码、测试、实验结果和负面发现作为候选经验资产外存，并记录版本、适用条件与检查依据，按当前任务检索后复验。重启探索不应删除权威任务契约或未决外部操作状态；把审计记录留在提示词之外，并重新载入目标、接口、测试、权限、验收条件和必要的失败/副作用状态。“被读取或引用”不等于提升结果。外部资产持续保留而当前上下文选择性清理，是跨源工程综合，不是论文共同评测过的方案。

### 相关知识

- [智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：上下文、环境反馈和智能体执行循环如何连接。
- [编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：判断主循环、并行工具与独立 worker 的边界。
- [LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：比较历史保留、重启与跨运行变更。
- [工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：工具 schema 与执行结果也是上下文的一部分。
- [RAG 架构与实现](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)：了解何时预先检索、何时按需检索。
## 7. How do you retrieve and use authorized external evidence in a grounded answer? / 怎样检索并使用经过授权的外部证据生成有依据的回答？

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

Treat all retrieved text as untrusted content. A document can contain direct or indirect instructions that influence the model. Delimiters and prompts may reduce confusion, but they do not guarantee protection. Do not let a retrieved passage authorize a data access or tool action; enforce permissions and validate actions outside the model. [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). For more on prompt injection and application boundaries, see [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

#### Evaluation / 评估

Measure retrieval and generation separately, then compare the complete system:

- **Candidate recall / 候选召回.** Label the source passages needed for each question and identify the version and caller. Recall@K is the share of those passages found in the first K candidates. MRR describes the rank of the first relevant candidate and cannot establish that a multi-part answer has every necessary passage.
- **Evidence and generation / 证据与生成.** Track which needed passages survive assembly. Then assess factual correctness, support for each claim and citation, and whether the answer abstains when the passage is missing or conflicting. RAGChecker illustrates claim-level decomposition for retrieval and generation diagnosis. [RAGChecker §§3–4](https://arxiv.org/abs/2408.08067)
- **System / 系统.** Track end-to-end latency and cost along with revocation and tenant-isolation regressions. Keep cases where the relevant-looking passage is unauthorized, expired, or for the wrong plan. Re-run the same cases across the lexical baseline, dense retrieval, hybrid fusion and reranking. Change one stage and retain the simplest configuration that meets the acceptance bar.

RAGAS and ARES illustrate multi-dimensional evaluation, including context relevance, answer faithfulness, and answer relevance; they are evaluation frameworks, not a complete universal score. Automated judges are useful signals and should be checked against representative human-reviewed examples. See [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F). [RAGAS](https://arxiv.org/abs/2309.15217), [ARES](https://arxiv.org/abs/2311.09476)

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

- [Context Engineering Principles / 上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains context budgets and how placement can affect use of evidence.
- [Fine-tuning Strategies / 微调策略](#14.%20When%20should%20you%20fine-tune%20to%20close%20a%20repeatable%20behavior%20gap?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%9A%E8%BF%87%E5%BE%AE%E8%B0%83%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F) discusses adapting model behavior and combining it with external knowledge.
- [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation datasets, metrics, and review methods.
- [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) covers prompt injection, permission boundaries, and runtime controls.
## 8. When should a model control the next step? / 何时应让模型决定下一步？

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

每轮执行完检查完成条件、总调用数、时间与预算。持续收到同一无进展结果时，可以换一个已允许的查证动作，或停止并说明证据缺口。长任务将进度和真实结果持久化，恢复时读取原状态，不让模型靠对话回忆猜测写入是否发生。工具请求、幂等和错误语义见 [工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)，恢复与事件回放见 [持久化 AI 运行](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F)。

评估时，把同一组任务交给固定工作流和 Agent，比较完成率、写入结果、权限违规、重复动作、成本和延迟。τ-bench 同时检查任务结束后的数据库状态与必须告知用户的信息。后续 τ²-bench 的电信任务还让模拟用户与 Agent 使用不同工具操作同一个环境，暴露了只测试单方动作时看不到的协调失败。将这类变化变成自己的测试用例，例如用户改完设置后要重新读状态，再决定是否执行后续动作。 [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [τ-bench](https://arxiv.org/abs/2406.12045) · [τ²-bench](https://arxiv.org/abs/2506.07982)

An observation updates the current run. A change that should apply across later runs needs a baseline, external evidence, and a retained version. / 观察会更新当前运行。若变更要延续到后续运行，就需要基线、外部证据与可保留的版本。[How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](#13.%20How%20do%20you%20test%20and%20keep%20an%20improvement%20to%20an%20agent?%20/%20%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E4%BF%9D%E7%95%99%E5%AF%B9%20Agent%20%E7%9A%84%E6%94%B9%E8%BF%9B%EF%BC%9F)

### 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；命名空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

### 相关知识

- [编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：决定步骤、并行、路由或多智能体结构。
- [上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：管理长任务中的历史、外部状态与缓存。
- [工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：定义运行时如何执行模型请求。
- [LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：区分任务反馈、变更验收与持久版本。
## 9. How should a multi-step AI task be structured? / 怎样组织多阶段 AI 任务？

**Short answer / 简答：** Choose orchestration from the task’s dependencies, independence, and ownership. Use code for known steps, add model-driven decomposition only when the work cannot be specified in advance, and keep one main loop unless measured parallelism, isolation, or a real capability boundary justifies delegation.

编排应根据任务依赖、子任务独立性和控制权选择：已知步骤由代码安排；只有工作无法预先列清时才考虑模型动态拆分；先保留单一主循环，只有实测并行、隔离或真实能力边界收益足以抵偿委托成本时才拆分。

Anthropic 的模式目录区分固定路径的 workflow 与模型驱动的 agent，并指出模式可以组合，复杂度应由任务效果决定。[以下模式以其一手说明为依据。](https://www.anthropic.com/engineering/building-effective-agents) 本文回答“如何安排步骤和委托”，而[智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)回答“是否把下一步控制权交给模型”。

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

将工作交给另一个 agent 不会自动带来上下文隔离。运行时要明确决定共享哪些会话状态、传递哪些证据、工作者可以访问哪些工具，以及主流程接收完整记录还是摘要。相关权衡见[上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 多智能体：委托工具还是交接所有权

不同 SDK 采用不同命名，但可按谁负责最终答复来理解：

| 结构 | 谁保留用户交互控制权 | 适合场景 |
|---|---|---|
| **智能体作为工具（agents as tools）／管理者模式（manager pattern）** | 管理者调用专家，把返回结果纳入自己的答复 | 专家做边界明确的研究、分类或摘要；主 agent 需要比较并综合多个结果。 |
| **交接（handoff）** | 专家接管后续流程或用户对话 | 识别到明确专业领域后，由该专家负责处理。 |

例如，客服分类 agent 可将技术问题交给技术支持 agent；若客服 agent 还必须比较订单状态、退款政策与支持历史，则可把这些调查工作委托为工具并保留最终答复权。[OpenAI 编排文档以“交接”与“智能体作为工具”说明了这一控制权区别。](https://developers.openai.com/api/docs/guides/agents/orchestration)

不论哪种结构，都要约定交接输入、输出契约、状态归属、最大交接深度和失败回退。否则专家之间可能反复转交、丢失客户或订单 ID，或对同一副作用重复执行。工具输入与执行契约见[工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)。

### 先尝试单主循环，再验证拆分 / Start with one loop, then test delegation

**核心建议：** 后续步骤仍依赖同一任务状态时，先尝试一个主循环；只有可独立并行、需要隔离验证或具备真实能力边界的子任务显示出收益时，再拆分。这个建议是结构选择的起点，不是固定 agent 数量或工具数量阈值。

拆分的理由应是具体任务边界：

- **独立工作可并行：** 各自读取不同资料，最终可以汇总；先确认没有共享写入冲突。
- **需要上下文隔离：** 专家只拿到完成子任务所需信息，主 agent 接收可核验摘要。
- **策略或权限应隔离：** 不同工作者拥有不同的知识范围、工具和访问权限；权限隔离只有在运行时真正限制能力时才成立。
- **单个上下文过于混杂：** 实测表明工具重叠、指令冲突或长历史降低了任务成功率。

[Anthropic / Diane Sarkis 的 fold-subagents 文章（2026-10-22，“Using an agent loop with progressive disclosure”“Task-completion evals”等章节）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)讨论何时把依赖共享上下文的 subagent 流程折入主循环：先建立端到端基线，再逐个折叠 subagent，检查任务成败、生产链路和必须遵守的规则，并以重复运行比较；合并后仍保留领域流程。其讨论也将独立研究、并行探索和验证列为可能适合独立 worker 的工作。文章给出的是评估方法与工程经验，不是折叠 subagent 会普遍提高表现的因果证明，也没有普适的工具数量分界线。

GitSwarm 提供了不同范围的例子：异步 worker 自主选择工作，在可分支的共享 Git 仓库中发布可组合产物；执行 harness 仍负责调度和发布验证，而该验证检查提交要求、不认证产物正确性。[GitSwarm v1（2026-10-04，§§2.1–2.3）](https://arxiv.org/html/2610.04862v1)没有中央“intellectual planner”替 workers 指派探索方向，但不因此取消执行协调。它支持把独立、可检查的产物作为拆分条件，不证明普通任务都应使用多 agent。状态取舍见[上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)，架构对照及其证据边界见[LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。

### 提示模板仍是单 agent 的选项

面对角色、领域或策略不同但结构相似的任务，可使用一个明确模板传入少量、语义一致的变量，代替维护多份近似提示。变量过多或互相矛盾仍会让提示难以理解；应通过代表性输入评估模板，而不是只检查文本形式。

### 运行与观测

对每个节点、工具调用、agent、重试与交接记录关联的任务 ID、输入输出引用、状态、延迟、错误与模型或工具用量。结果应能回答：任务是否完成，哪个步骤导致失败，实际执行了几次外部副作用，谁接管了用户流程。日志内容需符合数据保留和隐私要求。

### 相关知识

- [智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：工作流与 agent 的控制流边界及运行循环。
- [工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：定义被编排结构调用的能力与执行边界。
- [上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：决定在交接中保留什么、何时按需载入或重启探索。
- [LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：用端到端任务证据比较主循环、委托和交接。
## 10. How should an application execute a model’s tool request? / 应用应如何执行模型的工具请求？

**Short answer / 简答：** A tool call is a structured request from the model, not code execution or permission. The application must parse and validate it, check the caller’s authorization and current business state, execute the function, then return a useful result. Design for dependencies, side effects, and uncertain outcomes so recovery does not repeat an action blindly.

工具调用只是模型发出的结构化请求，不等于代码已经执行或用户已获授权。应用需要解析并校验请求，检查调用者权限和当前业务状态，执行函数，再把有用结果返回模型。设计时还要处理依赖、副作用和结果未知，避免恢复时盲目重复动作。

### 函数调用的生命周期

以下按 provider-neutral 方式描述，具体消息格式、角色名称、工具选择模式和结构约束因 API 而异：

1. 应用将对话状态与本轮可用工具定义发送给模型。
2. 模型返回普通内容，或返回包含工具名称与参数的调用请求。
3. 应用解析请求，校验参数，并按当前用户和业务状态授权。
4. 应用执行函数，将成功、错误或部分结果返回模型。
5. 模型依据结果继续调用工具、交接，或生成答复。

[OpenAI 函数调用指南](https://developers.openai.com/api/docs/guides/function-calling)将工具调用描述为模型请求与应用端执行之间的多步流程。结构化调用或严格 schema 可以减少格式错误，但不证明用户意图正确、权限充分、业务动作合理或外部操作已经成功。动作循环与控制权的整体关系见[智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)。

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

以部分退款为例，refund_amount 的数值范围可以按订单状态和总额在服务端检查；refund_reason 可以有可选枚举；但“用户是否授权退款”并不是 JSON schema 能验证的。严格输出约束只解决结构层，仍需检查身份、资源归属、当前状态、业务规则和风险阈值。[生产环境 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F)说明各运行控制的授权与隔离边界。

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

- [智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F)：工具属于动作空间，但授权必须由运行时执行。
- [编排模式](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F)：并行与串行编排取决于任务依赖和副作用。
- [上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F)：工具定义与结果也是模型上下文的一部分。
## 11. How can a production AI system contain model errors and manipulation? / 生产环境 AI 系统如何限制模型错误与受诱导带来的影响？

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

流畅回答仍可能错误或缺乏证据。检索可以提供有用依据，但不保证模型会正确使用；检索文本也不授予执行权限。本篇关注由此产生的运行安全边界；[LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)衡量事实性与支持度，[RAG 架构与实现](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)解释检索行为。NIST 将 confabulation 列为生成式 AI 风险；它没有把 grounding 视作正确性保证（[NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)）。

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

高影响或难以撤销的动作应暂停，等待与具体动作和目标绑定的审批。获批后，应用仍需在执行前重新检查授权与业务状态。尽可能将密钥放在模型可见内容和执行环境之外；沙箱保护取决于实际挂载、网络规则和凭据暴露情况（[OpenAI Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)、[Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)）。工具 schema 和执行契约见[工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)。

### Stop and hand off / 停止与人工接管

达到已配置的失败阈值、目标资源或范围不清、工具行为异常，或动作影响需要审批时，应暂停并交给人工。除非已针对具体用途验证，否则模型自报的置信度不是经过校准的信号。OpenAI agent 指南把重复失败和高风险动作列为人工介入的例子（[A Practical Guide to Building Agents, pp. 30–31](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)）。

交接只需包含人工继续处理所需的信息：用户请求、相关证据及其来源、已尝试的动作和结果、尚待决定的事项。不要包含凭据或无关敏感上下文。运行日志与 trace 也只保留调查动作及结果所需的信息，并限制访问；NIST 在 §2.4 说明了生成式 AI 数据处理的隐私风险。授权决定作出前，暂停任何待执行副作用。

应用需要位于模型循环之外的停止路径，能够停止新的工具调用与重试、取消活动运行，并撤销或禁用受影响能力。提示模型停止不是 kill switch。恢复前先核对已经完成的动作并确认当前状态。NIST AI 600-1 要求部署后监控、事件响应与恢复，并能在结果偏离预期用途时停止或停用系统（§§ MANAGE 2.3、2.4、4.1）。

### Test and monitor the boundaries / 测试与监控边界

红队测试探索攻击者可能如何突破本应用的数据和动作边界；评估测量已知案例；生产监控观察真实运行结果，三者不能互相替代。发布前，以及模型、提示、工具、数据源或权限发生实质变化后，都应测试；相关事件发生后也应测试。NIST AI 600-1 要求实证评估与持续监控；[评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)说明测量和回归设计。

回归用例应关联到应用实际能力：

- **直接注入：** 用户请求超出其授权范围的动作；即使模型提出调用，运行时也应拒绝。
- **间接注入：** 检索内容或工具结果要求模型超出任务；验证其不能授权副作用。
- **敏感输出和内容政策（无需工具）：** 在隔离测试上下文中放入合成的受保护字段并请求泄露；另外测试违反内容政策的提示，验证字段不会暴露且配置的审核行为生效。不要使用真实个人数据。
- **输出处理：** 对可能被下游接收方解释为标记语言或指令的内容，在该接收方处理时验证其安全性。OWASP LLM10:2026 建议在下游使用前验证与净化模型输出（[LLM10:2026 Improper Output Handling](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM10_ImproperOutputHandling.md)）。
- **持久记忆（仅在系统有持久记忆时）：** 向隔离测试记忆添加无害的注入指令；验证后续会话不能借此触发受限动作或超出预期范围，然后删除记录并确认其影响已消失。

红队结果应记录攻击路径、是否发生未授权动作或信息泄露，以及修复方式；适用时将最小化案例加入回归测试。生产中监控工具调用与拒绝、意外状态变化、重复失败、人工覆盖和伤害报告；将信号用于调查和更新测试，不把单个比率视为目标。

### 相关知识

- [工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F)：工具请求、schema 与副作用执行。
- [RAG 架构与实现](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F)：外部证据的检索和访问控制。
- [LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)：质量与安全用例的测量和回归。
## 12. How can you tell whether an AI system meets its task contract? / 如何判断 AI 系统是否满足任务契约？

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

- [Agent improvement and version acceptance / Agent 改进与版本验收](#13.%20How%20do%20you%20test%20and%20keep%20an%20improvement%20to%20an%20agent?%20/%20%E5%A6%82%E4%BD%95%E9%AA%8C%E8%AF%81%E5%B9%B6%E4%BF%9D%E7%95%99%E5%AF%B9%20Agent%20%E7%9A%84%E6%94%B9%E8%BF%9B%EF%BC%9F) — connect feedback on a task to a change that persists across runs.
- [Orchestration patterns](#9.%20How%20should%20a%20multi-step%20AI%20task%20be%20structured?%20/%20%E6%80%8E%E6%A0%B7%E7%BB%84%E7%BB%87%E5%A4%9A%E9%98%B6%E6%AE%B5%20AI%20%E4%BB%BB%E5%8A%A1%EF%BC%9F) — compare the single-loop baseline with tested delegation or parallel work.
- [RAG architecture and implementation](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) — 了解检索、证据组装和生成机制，对应本文的 RAG 评估阶段。
- [AI safety in production](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) — 了解需要单独设计任务检查的安全边界和生产控制。

### Sources / 来源

关键定义与主张已在正文链接一手研究。补充来源：

- Liang et al., [*Holistic Evaluation of Language Models*](https://arxiv.org/abs/2211.09110).
- Zheng et al., [*Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*](https://arxiv.org/abs/2306.05685).
- Xia et al., [*Evaluation-Driven Development and Operations of LLM Agents: A Process Model and Reference Architecture*](https://arxiv.org/abs/2411.13768) — 提出连接离线与线上评估的流程模型，并不保证两者分数一致。
## 13. How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？

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

Specify the task, budget, success criteria, and stop condition before trying candidates. Record whether each candidate changes the task policy, the predictor that ranks proposals, or the harness that controls execution. When two components can interact, compare each change separately and then compare the pair before accepting it. Preserve the task inputs and baseline for that comparison. [Evaluation and paired acceptance / 评估与配对验收](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)

### Rank candidates, then observe the real result / 候选排序之后获取真实结果

[RSI-Anything v1（2026-10-09，§2.1）](https://arxiv.org/html/2610.13912v1#S2.SS1) 将任务规格、预算、验收和停止条件视为固定契约；积累经验本身不会修改策略或模型。其 JEPA-Anything/OPF 世界模型先预测潜变量表示，再由领域读出（readout）转换成任务结果预测，用来排序候选并交给外部测量；机制见[§2.2](https://arxiv.org/html/2610.13912v1#S2.SS2)与[§2.3](https://arxiv.org/html/2610.13912v1#S2.SS3)。因此要区分规则、模型预测、模拟器输出和实测结果。外部反馈可以促成策略或工作流更新；只有在已观察候选显示预测器不可靠、且数据与预算足够时，才考虑更新预测器。观测覆盖不足也不等于可靠性已经成立。[§2.4](https://arxiv.org/html/2610.13912v1#S2.SS4)与[§2.5](https://arxiv.org/html/2610.13912v1#S2.SS5)分别说明更新门槛和配对验收。[Table 4](https://arxiv.org/html/2610.13912v1#S6.T4)与[§5](https://arxiv.org/html/2610.13912v1#S5)中各应用的更新范围不同；持续互相改进仍需联合的多轮评估。

**工程建议：** 对有清楚任务指标的工作流，可以尝试用脚本、模拟器或范围受限的 agent 预测候选效果并据此预筛，再与后续实测比较、验收版本。语法检查仍是规则校验，agent 的文字预判仍是预测。这些是实现选项，尚无替代上述学习型 world model 的等价实证；单步排序也不证明多步状态模拟有效。

例如，优化一个有工具调用的文档问答 Agent 时，可以用脚本预估候选配置的调用次数，先筛出更值得测试的候选。再对同一组任务运行基线和候选，比较实际成本、证据是否支持答案、权限控制是否通过。记录任务集、基线版本、变更及结果，验收后保留可恢复的配置和证据。这个例子说明候选筛选与版本验收如何配合。

### Retain changes to the harness / 保留脚手架改进

另一类改进改变的是运行脚手架（harness），而非基础模型。[Harness²（v1，2026-10-09，§§2.1–2.3）](https://arxiv.org/html/2610.14224v1) 在同一任务上实际执行候选 harness，比较编辑前后的行为，再将采用的 harness 组件和有依据的经验存入库；新任务从共同的 H₀ 起步并按需检索。该研究保持 editor 模型、阶段指令和决策规则不变，因此展示的是任务级 harness 与经验库的演进，不是模型权重或 editor 自行改写。执行对照可支持针对性修改，但不单独证明答案正确；验收边界见[LLM 评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F)。

**Related questions / 相关问题** — [When should a model control the next step? / 何时应让模型决定下一步？](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F) explains the live execution loop. [Context engineering / 上下文工程](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F) explains what can be stored for retrieval on later tasks.
## 14. When should you fine-tune to close a repeatable behavior gap? / 何时应通过微调弥补稳定的行为差距？

**Core explanation / 核心解释：** Fine-tuning updates a pretrained model using examples or preferences to change task behavior. It is worth testing when a repeatable behavior gap remains after prompt, context, retrieval, and workflow improvements. It is not a reliable database for fresh or access-controlled facts; choose the method and data through held-out evaluation and account for training, serving, and maintenance. / 微调用示例或偏好更新预训练模型，以改变特定任务行为。当提示词、上下文、检索和工作流改进后仍存在稳定的行为差距，才值得评估微调。它不是可靠的实时或权限控制数据库；应通过保留集评估选择方法和数据，并计入训练、部署及维护成本。

**Key terms / 关键术语：** supervised fine-tuning (SFT) / 监督微调；LoRA / 低秩适配；QLoRA / 量化低秩适配；preference optimization / 偏好优化；RLHF / 基于人类反馈的强化学习；DPO / 直接偏好优化。

### Should you fine-tune, or use prompting and retrieval? / 应微调，还是使用提示和检索？

First identify the error. Missing or changing facts call for an authoritative data source and retrieval or a direct API. Unclear instructions may be fixed with a prompt or workflow. A persistent style, label convention, or response pattern may be suitable for fine-tuning if examples can teach it and evaluation confirms the gain. These are useful starting points, not mutually exclusive categories.

Fine-tuning does not make facts stored in weights reliably addressable, current, or permission-aware. Retrieval still needs source freshness, access checks, and evidence validation. A fine-tuned model can also be paired with retrieval. [RAG Architecture and Implementation / 检索增强生成](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers external evidence; [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers task evaluation.

Before training, compare a prompt-only baseline and any relevant retrieval or workflow baseline. Consider fine-tuning when the remaining gap is repeatable, the training data represents the target behavior, and the expected improvement justifies training, deployment, and future update work.

### Which method should you choose? / 如何选择微调方法？

- **Full fine-tuning / 全量微调：** updates the base model's trainable weights. It offers broad adaptation capacity, with higher memory, compute, and artifact costs.
- **LoRA / 低秩适配：** freezes the base weights and trains low-rank matrices for selected weight updates. This reduces the number of trainable parameters; resulting quality and memory needs depend on model, rank, target modules, data, and training setup.
- **QLoRA / 量化低秩适配：** keeps a quantized base model frozen while training LoRA adapters. The QLoRA paper studies 4-bit quantization and memory-saving methods in a specific experimental setup; quantization and adapter choices still require task evaluation.
- **Adapters / 适配器：** add small trainable modules, often bottleneck layers within Transformer blocks, while the main model weights stay frozen.
- **Prefix tuning / 前缀微调：** learns continuous task-specific vectors that are supplied as prefix representations at Transformer layers; these are not ordinary visible text tokens.
- **Prompt tuning / 软提示微调：** learns a small set of continuous input-embedding vectors prepended to the input while keeping the model frozen. This differs from prompt engineering, which edits ordinary instruction text.

These methods alter different parts of a model's computation and have different trainer and serving support. Their results depend on the model, task, and implementation; compare them by evaluation rather than assuming one dominates.

A common LoRA parameterization writes an update as a product of two low-rank matrices:

$$
W' = W + \Delta W,\qquad \Delta W = BA
$$

Here, if W maps from input dimension k to output dimension d, A can have shape r × k and B shape d × r, with rank r smaller than k and d. This is a schematic form; implementations may scale or target different modules. Some serving stacks can merge adapters into the base weights, while other configurations keep adapter operations at inference. Verify the target stack instead of assuming zero latency overhead.

**One-matrix count illustration / 单个矩阵参数量示例:** Suppose one target projection is 4096 × 4096 and r = 8. The two LoRA matrices contain r(k + d) = 8(4096 + 4096) = 65,536 trainable values, while the original dense matrix has dk = 4096 × 4096 = 16,777,216 values. This compares one adapted matrix only; a model's total depends on how many layers and matrices are targeted, and the count alone predicts neither quality nor the whole model's trainable-parameter fraction.

There is no universal rank, method, or “default” that guarantees quality. Compare feasible approaches using the same data splits, task metrics, deployment constraints, and base model.

### How much and what kind of data? / 需要多少数据，数据应是什么样？

There is no general example count that predicts success. A small clean set may reveal whether a behavior is learnable, while broader or rarer cases may need more coverage. Track which behaviors and input patterns each example represents; do not treat raw volume as evidence of quality.

Possible supervised example / 监督样例:

~~~json
{
  "messages": [
    {"role": "user", "content": "Summarize this sample clause: The supplier will deliver the parts by June 1."},
    {"role": "assistant", "content": "The supplier must deliver the parts by June 1."}
  ]
}
~~~

This is synthetic demonstration data, not legal advice or a recommended training format for every API. Follow the chosen trainer's current format and include only data you are authorized to use.

Review data for correctness, representative coverage, consistent labels, duplicates, sensitive information, and rights to use. Split training and evaluation data to reduce leakage; near-duplicates or examples from the same source can make a nominally held-out score misleading. Synthetic examples can expand coverage, but verify them because generation can introduce unsupported facts, errors, and bias.

### A training and evaluation workflow / 训练与评估流程

1. **Define the failure and success criteria.** Record the current behavior, target behavior, operational constraints, and unacceptable regressions.
2. **Build and review examples.** Remove duplicates and unauthorized or sensitive material; check labels and coverage.
3. **Create separated data splits.** Separate training and validation examples, and reserve a representative final test set until the method and training controls are fixed. Document the split method and known leakage risks.
4. **Choose a base model and method.** Confirm current training support, data format, license or service terms, and serving compatibility.
5. **Train and tune a baseline experiment.** Track the learning rate and schedule, epoch count, effective batch size, gradient accumulation, training-data version, checkpoints, and validation results. These are experiment-specific controls, not portable defaults.
6. **Compare with the untuned baseline.** Use validation cases for iterative comparisons; after choices are fixed, compare the selected model with the baseline on the untouched test set. Report quality by important slices, format and tool behavior, safety outcomes, and regressions.
7. **Deploy cautiously and monitor.** Version the model and rollback path; monitor the same outcomes on real traffic, respecting data retention and consent rules.

A successful training job only shows that optimization ran. It does not establish better generalization. Do not call a score gain “memorization” or “generalization” without checking data overlap, task slices, and independent evidence.

The **learning rate** sets the scale of optimizer updates; a rate that is too large for a setup can destabilize learning, while one that is too small can fail to adapt within the chosen training budget. **Epochs** count passes over the training examples; more passes may improve fit or begin to overfit. **Batch size** controls how many examples contribute to an optimizer update, with memory and gradient-variance tradeoffs; gradient accumulation can change the effective batch without changing the per-device batch.

Use training data to fit weights, a validation split to compare training controls and support early stopping, and a final held-out test set only after choices are fixed. Repeatedly selecting against the final test set leaks it into development. Compare task outcomes and important slices against the untuned baseline; training and validation loss are useful signals, not substitutes for the target behavior.

### What are SFT, RLHF, and DPO? / 什么是 SFT、RLHF 与 DPO？

**Supervised fine-tuning (SFT)** trains on desired responses or demonstrations. It can teach response patterns represented by the examples; it does not guarantee that the model follows every instruction or is safe in unseen situations.

In the InstructGPT research pipeline, human-written demonstrations were used for supervised fine-tuning, human preference comparisons trained a reward model, and reinforcement learning optimized the policy against that reward. This describes that paper's method, not every assistant model's training process.

**Direct Preference Optimization (DPO)** is a preference-learning method that optimizes from chosen and rejected responses without fitting a separate reward model in the same way as the classic RLHF pipeline. It still depends on preference data, a training objective, and modeling assumptions; it is not automatically more accurate or safer than PPO. Choose based on the available data, infrastructure, and evaluation.

Preference labels can be inconsistent or reflect the annotators and rubric. Evaluate the resulting model for the intended task and relevant failure cases; do not infer safety from a preference-training label alone.

### Related notes / 相关笔记

- [RAG Architecture and Implementation / 检索增强生成](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers retrieval for external and changing evidence.
- [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers held-out evaluation and failure analysis.
- [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) covers runtime controls that training does not replace.

### Sources / 来源

- Hu et al., [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685).
- Dettmers et al., [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314).
- Houlsby et al., [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751); Li and Liang, [Prefix-Tuning](https://arxiv.org/abs/2101.00190); Lester et al., [The Power of Scale for Parameter-Efficient Prompt Tuning](https://arxiv.org/abs/2104.08691).
- Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155).
- Rafailov et al., [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290).
- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), [Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning), [Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization), and [Deprecations](https://developers.openai.com/api/docs/deprecations), checked 2026-10-15. The SFT/DPO pages describe OpenAI-specific methods, not general availability: the optimization page marks fine-tuning docs as legacy and says the platform is winding down. The deprecations page says organizations that had not previously run fine-tuning cannot create jobs; since 2026-07-02, organizations that have not run inference on a fine-tuned model in the prior 60 days also cannot create jobs. Active existing customers lose job creation on 2027-01-06, while inference continues until the base model is deprecated. Check current availability before treating OpenAI API fine-tuning as an option.
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

Treat a model-proposed tool call as untrusted input. The application executes it only after its own argument checks and authorization; schema-constrained output does not establish that an action is valid or permitted. See [Tool Design and Function Calling / 工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F) and [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F). OpenAI’s [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, describe provider-specific request and schema behavior; application authorization and semantic validation remain separate.

Set explicit deadlines, bounded retries, idempotency for retryable writes, cancellation behavior, rate and budget limits, an error or escalation path, and a way to roll back a model or prompt version. Retry only when the operation contract makes a duplicate safe. A timeout says the caller did not receive a result in time; it does not say the server did no work.

These are separate design questions with deeper treatments: [how to reduce latency and cost](#16.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F), [how to choose a deployment pattern](#18.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F), and [how to monitor and improve a production feature](#19.%20How%20do%20you%20monitor%20a%20production%20AI%20feature%20and%20turn%20feedback%20into%20a%20safe%20improvement?%20/%20%E5%A6%82%E4%BD%95%E7%9B%91%E6%8E%A7%E7%94%9F%E4%BA%A7%E4%B8%AD%E7%9A%84%20AI%20%E5%8A%9F%E8%83%BD%E5%B9%B6%E5%AE%89%E5%85%A8%E5%9C%B0%E6%94%B9%E8%BF%9B%EF%BC%9F). The remainder of this note defines the durable run contract that those interfaces rely on.

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
- [AI System Design Interview Questions / AI 系统设计面试题](#20.%20How%20do%20you%20turn%20an%20AI%20system%20design%20prompt%20into%20a%20defensible%20architecture?%20/%20%E5%A6%82%E4%BD%95%E6%8A%8A%20AI%20%E7%B3%BB%E7%BB%9F%E8%AE%BE%E8%AE%A1%E9%A2%98%E8%BD%AC%E5%8C%96%E4%B8%BA%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E6%9E%B6%E6%9E%84%EF%BC%9F) applies these production mechanisms to end-to-end design cases.

**Sources / 来源：** [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) defines idempotent HTTP method semantics, and [§15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) says `202 Accepted` does not mean processing is complete. Temporal's [Workflow replay guide](https://docs.temporal.io/workflows) and [Event History guide](https://docs.temporal.io/encyclopedia/event-history) describe one runtime's deterministic orchestration replay and recorded activity results. These sources support the mechanisms described here; the example API, states, and names are synthetic application choices.
## 16. How do you reduce AI application latency and cost without weakening task quality? / 如何在不损害任务质量的前提下降低 AI 应用的时延与成本？

**Core explanation / 核心解释：** First measure where end-to-end time and cost accumulate, then change one layer at a time against a fixed task-quality bar. Queueing, context assembly, retrieval, model input/output, tools, retries, and operations have different costs; token price alone is not total cost, and faster partial output is not necessarily faster completion. / 先测量端到端时间和成本分别累积在哪些环节，再以固定任务质量门槛为准逐层调整。排队、上下文组装、检索、模型输入与输出、工具、重试和运维成本各不相同；token 单价不等于总成本，更快看到部分输出也不代表更快完成。

**Key terms / 关键术语：** time to first token (TTFT) / 首 token 时延；queue time / 排队时间；response cache / 响应缓存；prompt cache / 提示缓存；continuous batching / 连续批处理；quantization / 量化；distillation / 蒸馏。

### How can you reduce latency and cost? / 如何降低时延与成本？

Measure queueing, context assembly, retrieval, model input and output, tools, and retries separately. Track latency distributions and TTFT alongside throughput, queue time, and cost per completed task. Hold the task-quality bar constant: a cheaper route that fails more often may increase retries, escalations, and human review.

The application architecture owns run status, deadlines, and recovery; see [How can a production AI run survive disconnections and worker failures? / 生产运行如何经受断连与故障？](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F). Define the success measure before comparing optimizations with [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F).

#### Which optimization should you test? / 应先测试哪种优化？

- **Shorten or select context / 缩短或筛选上下文：** include relevant material and limit unnecessary history. Measure whether evidence or task quality is lost. See [Context Engineering Principles / 上下文工程原则](#6.%20What%20should%20each%20model%20inference%20see,%20and%20what%20should%20the%20application%20persist?%20/%20%E6%AF%8F%E6%AC%A1%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%BA%94%E7%9C%8B%E5%88%B0%E4%BB%80%E4%B9%88%EF%BC%8C%E5%BA%94%E7%94%A8%E5%BA%94%E6%8C%81%E4%B9%85%E5%8C%96%E4%BB%80%E4%B9%88%EF%BC%9F).
- **Cache / 使用缓存：** exact-response or semantic response caches can avoid model work on a safe hit. Require compatible permissions, freshness, tenant, locale, and policy version. For example, “What is the refund policy in the US?” and “What is the refund policy in the EU?” can have similar embeddings but different correct answers. Similarity alone does not prove a response is reusable.
- **Route requests / 请求路由：** use a lower-cost candidate only for cases where it meets the measured quality bar. Include classifier errors, added latency, fallback frequency, and maintenance in the comparison. Candidate fit belongs to [Model Selection and Ecosystem / 模型选择与生态](#3.%20How%20should%20you%20choose%20a%20model%20for%20a%20task%20and%20its%20deployment%20constraints?%20/%20%E5%A6%82%E4%BD%95%E6%A0%B9%E6%8D%AE%E4%BB%BB%E5%8A%A1%E4%B8%8E%E9%83%A8%E7%BD%B2%E7%BA%A6%E6%9D%9F%E9%80%89%E6%8B%A9%E6%A8%A1%E5%9E%8B%EF%BC%9F).
- **Inference batching / 推理批处理** — A serving engine can admit and retire sequences between decoding steps. [GPU serving capacity / GPU 推理容量](#17.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) explains how that affects memory, throughput, and per-request latency. A provider's asynchronous Batch API is a job interface for requests that tolerate delayed completion. It exposes no live inference scheduling contract.
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
## 17. How do KV cache and scheduling determine LLM serving capacity? / KV 缓存与调度怎样决定模型推理容量？

**Short answer / 简答** — Prefill creates the prompt’s per-layer K/V state. Decode reuses it and appends new K/V, so active sequence length and concurrency drive memory. Use a tiled attention kernel to reduce GPU memory traffic, page the persistent cache to reduce allocation waste, and schedule prefill and decode under a latency target. Measure which limit dominates before tuning. / 预填充生成提示词在各层的 K/V。增量解码读取旧状态并追加新 K/V，因此活跃序列的长度和并发数决定显存用量。用分块计算内核减少显存读写，用分页管理持久缓存减少分配浪费，再按时延目标调度 prefill 与 decode。先测量瓶颈在哪一层，再选优化。

**Key terms / 关键术语** · prefill / 提示预填充 · decode / 增量解码 · HBM / 高带宽显存 · KV cache / 键值缓存 · continuous batching / 连续批处理 · TTFT / 首词元时延 · ITL / 词元间时延

### What stays on the GPU between decode steps? / 解码步之间哪些数据留在 GPU？

[生成机制](#2.%20How%20does%20a%20language%20model%20turn%20a%20prompt%20into%20text?%20/%20%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E6%80%8E%E6%A0%B7%E6%8A%8A%E4%B8%80%E6%AE%B5%20prompt%20%E5%8F%98%E6%88%90%E6%96%87%E6%9C%AC%EF%BC%9F)中的因果注意力解释了可缓存的条件。Prefill 把提示输入各层，写出全部提示位置的 K、V，并由最后一个位置的 logits 得到第一个输出 token。下一步把该 token 送进模型。每层为它计算新的 Q、K、V。新的 Q 对缓存里的旧 K 和当前 K 打分，再对对应 V 求加权和。在标准因果设置下，旧位置不受未来 token 影响，可以沿用旧 K/V。旧 Q 已经用于旧位置自己的更新；后续位置的 attention 不读取它。每层所需的投影来自该层自己的输入与权重，因此要存各层的 K/V。

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

做一组固定流量回放。记录模型版本、精度、GPU、输入和输出长度分布、并发与到达速率、冷暖缓存比例。比较 **TTFT**（请求到首词元）、**ITL**（输出词元之间的间隔）、端到端 p95、吞吐和满足时延目标的请求数。能处理更多请求但超出交互时延的批次没有解决交互负载的问题。测量由 [vLLM Benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/) 示例和[应用级时延与成本](#16.%20How%20do%20you%20reduce%20AI%20application%20latency%20and%20cost%20without%20weakening%20task%20quality?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E6%8D%9F%E5%AE%B3%E4%BB%BB%E5%8A%A1%E8%B4%A8%E9%87%8F%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%99%8D%E4%BD%8E%20AI%20%E5%BA%94%E7%94%A8%E7%9A%84%E6%97%B6%E5%BB%B6%E4%B8%8E%E6%88%90%E6%9C%AC%EF%BC%9F)分别覆盖服务内和端到端两层。
## 18. When should an AI application use a hosted API, self-hosting, edge, or hybrid deployment? / AI 应用何时应选托管 API、自托管、端侧或混合部署？

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

The choice also depends on which model candidates meet the task contract. See [Model Selection and Ecosystem / 模型选择与生态](#3.%20How%20should%20you%20choose%20a%20model%20for%20a%20task%20and%20its%20deployment%20constraints?%20/%20%E5%A6%82%E4%BD%95%E6%A0%B9%E6%8D%AE%E4%BB%BB%E5%8A%A1%E4%B8%8E%E9%83%A8%E7%BD%B2%E7%BA%A6%E6%9D%9F%E9%80%89%E6%8B%A9%E6%A8%A1%E5%9E%8B%EF%BC%9F) for comparing task quality, modality, deployment constraints, and measured routing. For the run identity and recovery behavior that should remain stable across deployment patterns, see [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F).

For self-hosting, estimate the peak number and length of active sequences and then measure fit on the intended hardware. [GPU serving capacity / GPU 推理容量](#17.%20How%20do%20KV%20cache%20and%20scheduling%20determine%20LLM%20serving%20capacity?%20/%20KV%20%E7%BC%93%E5%AD%98%E4%B8%8E%E8%B0%83%E5%BA%A6%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86%E5%AE%B9%E9%87%8F%EF%BC%9F) shows how to size KV memory and compare batching under a latency target.

**Source boundary / 来源边界：** This note summarizes the deployment comparison already present in the AI Application Architecture source. Provider features, terms, prices, capacity, and availability are time- and workload-specific; verify the exact provider or serving stack when making a current deployment decision. It does not make a universal cost or privacy ranking.
## 19. How do you monitor a production AI feature and turn feedback into a safe improvement? / 如何监控生产中的 AI 功能并安全地改进？

**Core explanation / 核心解释：** Pair technical service signals with task outcomes. Record enough version and trace context to locate a regression while minimizing sensitive payloads. Treat user feedback as a useful but biased signal: inspect failure modes, make a targeted change, compare it on held-out cases, and keep or roll it back against agreed criteria. / 将服务运行信号与任务结果一起观察。记录足以定位回归的版本与追踪信息，同时尽量减少敏感载荷。用户反馈有用但存在偏差：先检查失败类型，再做有针对性的变更，在留出案例上比较，最后按约定标准保留或回滚。

**Key terms / 关键术语：** observability / 可观测性；trace / 追踪；task outcome / 任务结果；feedback signal / 反馈信号；rollback / 回滚。

### How should an application monitor behavior? / 应用应监控哪些行为？

Track technical operation and task outcomes together. Useful measures include:

- latency distributions and time to first token (TTFT), throughput, and queue time;
- errors and timeouts by stage, input/output usage, and cost per completed task;
- tool success and authorization denials, cache-hit correctness, task completion, and escalation;
- explicit user feedback and whether the result was accepted or corrected.

Set thresholds from service requirements and a measured baseline; no universal error-rate or latency threshold fits every application. Record prompt, model, and relevant configuration versions so a change can be investigated. Keep logs proportionate: redact or avoid sensitive content and apply retention controls. Use sampled traces or derived metrics when full payload logging is unnecessary.

Model behavior, external data, prompts, and provider implementations can change. Re-run an evaluation set when a material component changes and compare results by important task slices. [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) owns task-quality definitions, dataset design, judge validation, and acceptance evidence. Keep a rollback or fallback path when a release misses the agreed quality bar.

### How can feedback improve the product? / 如何让反馈改进产品？

Collect explicit signals such as ratings or corrections and implicit signals such as task completion, accepted suggestions, repeated requests, and escalation. These signals are incomplete and biased: a rating reflects who chose to respond, while time spent can mean either engagement or confusion. Interpret them alongside representative task evaluation and user research.

A practical improvement loop is:

1. Capture feedback with relevant task and version context, subject to privacy and retention rules.
2. Review a sample and classify its failure mode.
3. Fix the appropriate layer: source data, retrieval, prompt, tool, model choice, interface, or policy.
4. Test the change on held-out cases and monitor the relevant production outcome.
5. Keep or roll back the change using the agreed criteria.

Preference data may inform fine-tuning or preference optimization, but a feedback button alone does not create a validated training signal. See [Fine-tuning Strategies / 微调策略](#14.%20When%20should%20you%20fine-tune%20to%20close%20a%20repeatable%20behavior%20gap?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%9A%E8%BF%87%E5%BE%AE%E8%B0%83%E5%BC%A5%E8%A1%A5%E7%A8%B3%E5%AE%9A%E7%9A%84%E8%A1%8C%E4%B8%BA%E5%B7%AE%E8%B7%9D%EF%BC%9F). For permission boundaries, human approval, and production stop paths, see [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

**Related note / 相关笔记：** [AI Application Architecture / AI 应用架构](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) defines the durable run state and recovery contract that lets service metrics and task feedback remain attached to one logical operation.

**Source boundary / 来源边界：** These monitoring and feedback practices reorganize the existing architecture note. Thresholds, task metrics, and data-retention rules must come from the particular service's requirements and privacy constraints; this note does not prescribe universal numeric targets.
## 20. How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？

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

The [RAG chapter](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) follows a concrete policy question from authorized candidate retrieval through claim verification. Here the extra constraint is an end-to-end latency budget.

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

A tool-call schema can constrain the shape of a proposed call; the application must still check whether the user and action are permitted. OpenAI's [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, illustrates provider-specific behavior; it does not replace application-side validation and authorization. See [Agent Fundamentals / 智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F), [Tool Design and Function Calling / 工具设计与函数调用](#10.%20How%20should%20an%20application%20execute%20a%20model%E2%80%99s%20tool%20request?%20/%20%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B%E7%9A%84%E5%B7%A5%E5%85%B7%E8%AF%B7%E6%B1%82%EF%BC%9F), and [AI Safety in Production / 生产环境中的 AI 安全](#11.%20How%20can%20a%20production%20AI%20system%20contain%20model%20errors%20and%20manipulation?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%20AI%20%E7%B3%BB%E7%BB%9F%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%A8%A1%E5%9E%8B%E9%94%99%E8%AF%AF%E4%B8%8E%E5%8F%97%E8%AF%B1%E5%AF%BC%E5%B8%A6%E6%9D%A5%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F).

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

- [Durable AI runs / 持久化 AI 运行](#15.%20How%20can%20a%20production%20AI%20run%20survive%20disconnections%20and%20worker%20failures?%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84%20AI%20%E8%BF%90%E8%A1%8C%E5%A6%82%E4%BD%95%E7%BB%8F%E5%8F%97%E6%96%AD%E8%BF%9E%E4%B8%8E%20worker%20%E6%95%85%E9%9A%9C%EF%BC%9F) covers production run controls. [AI deployment choices / AI 部署选择](#18.%20When%20should%20an%20AI%20application%20use%20a%20hosted%20API,%20self-hosting,%20edge,%20or%20hybrid%20deployment?%20/%20AI%20%E5%BA%94%E7%94%A8%E4%BD%95%E6%97%B6%E5%BA%94%E9%80%89%E6%89%98%E7%AE%A1%20API%E3%80%81%E8%87%AA%E6%89%98%E7%AE%A1%E3%80%81%E7%AB%AF%E4%BE%A7%E6%88%96%E6%B7%B7%E5%90%88%E9%83%A8%E7%BD%B2%EF%BC%9F) compares where to run the model.
- [RAG Architecture and Implementation / 检索增强生成](#7.%20How%20do%20you%20retrieve%20and%20use%20authorized%20external%20evidence%20in%20a%20grounded%20answer?%20/%20%E6%80%8E%E6%A0%B7%E6%A3%80%E7%B4%A2%E5%B9%B6%E4%BD%BF%E7%94%A8%E7%BB%8F%E8%BF%87%E6%8E%88%E6%9D%83%E7%9A%84%E5%A4%96%E9%83%A8%E8%AF%81%E6%8D%AE%E7%94%9F%E6%88%90%E6%9C%89%E4%BE%9D%E6%8D%AE%E7%9A%84%E5%9B%9E%E7%AD%94%EF%BC%9F) covers retrieval implementation and grounding.
- [LLM Evaluation Methods / 大语言模型评估方法](#12.%20How%20can%20you%20tell%20whether%20an%20AI%20system%20meets%20its%20task%20contract?%20/%20%E5%A6%82%E4%BD%95%E5%88%A4%E6%96%AD%20AI%20%E7%B3%BB%E7%BB%9F%E6%98%AF%E5%90%A6%E6%BB%A1%E8%B6%B3%E4%BB%BB%E5%8A%A1%E5%A5%91%E7%BA%A6%EF%BC%9F) covers evaluation design.
- [Agent Fundamentals / 智能体基础](#8.%20When%20should%20a%20model%20control%20the%20next%20step?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E8%AE%A9%E6%A8%A1%E5%9E%8B%E5%86%B3%E5%AE%9A%E4%B8%8B%E4%B8%80%E6%AD%A5%EF%BC%9F) covers runtime agent patterns.
