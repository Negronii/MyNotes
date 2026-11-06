# How does an AI service turn one message into a complete answer?

## Case study — explaining a failed build

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

## 1. Prepare what the model can see

The harness is the application code that coordinates the model and its tools. It records the caller's identity, selects the information for the model, executes tools, and decides when the application has a result to return. Here, the first model call has three inputs.

| Input | Content in this example |
| --- | --- |
| Application instruction | Explain the build failure using available evidence. |
| User message | `Why did build 42 fail?` |
| Tool definition | `read_build_log` accepts an integer `build_id` and returns failure records from the build log. |

> [!tip] Instructions, conversation, and external state
> A model call receives a selected input. It does not automatically see the log service, the application's database, or everything a user previously said. The application must supply that information or execute a tool that retrieves it.

The tool definition describes an available operation. The log itself enters the conversation only after the application retrieves it. The caller's identity is retained by the application for permission checks.

These inputs form the model's context (上下文) for this call. In a longer conversation, the application would also choose which earlier messages and evidence to include. That selection matters because the model can only condition its output on information actually supplied to it and knowledge encoded in its trained parameters. [Choosing the information for each model call](../context/context-engineering-principles.md)

## 2. Generate a request for the missing evidence

The model now has the question and a way to ask for logs. During inference (推理), it processes that input and generates an output one token (词元) at a time. In this run, the output specifies `read_build_log` with `build_id` set to `42`.

How can a sequence of numerical operations produce that request? We can follow the transformations inside a simplified decoder-only Transformer (仅解码器 Transformer). The small dimensions and numerical values below illustrate the computation. They are not measurements of a model responding to this question.

The service first formats the question, instructions, and tool definition, then a tokenizer (分词器) turns them into integer IDs. Encoding just `Why did build 42 fail?` with `tiktoken 0.12.0` and `cl100k_base` gives seven pieces, `["Why", " did", " build", " ", "42", " fail", "?"]`, and IDs `[10445, 1550, 1977, 220, 2983, 3775, 30]`. The complete input also includes the other messages and formatting markers.

An embedding table (嵌入表) maps each ID to a vector. Across successive Transformer layers, attention (注意力) gathers information from visible positions, while a feed-forward network (前馈网络), or FFN, transforms the features within each position. These operations update the hidden state (隐层状态), the model's numerical representation of this particular input.

> [!tip] What is being transformed?
> A vector (向量) is an ordered list of numbers. With `T` token positions and eight features per position, the hidden state has shape `T × 8`. Each row belongs to one position. The model's learned weights transform those features; the rows remain associated with the positions as information flows between them.

After the last layer, the LM head uses the state at the final input position to score vocabulary entries. Decoding (解码) selects a token, appends it, and repeats the prediction. A KV cache (键值缓存) lets later steps reuse earlier positions' keys and values, the representations attention reads when gathering information. The next position still needs its own computation. This loop can produce ordinary text or tokens encoding a structured tool request.

When the model exposes temperature (温度), that setting changes how concentrated token sampling is. It does not establish whether the result is correct. [How should an application choose decoding settings?](../foundations/how-llms-work.md#How%20should%20an%20application%20choose%20decoding%20settings%3F) follows this choice through task-specific evaluation. The numerical steps behind the model call can be inspected below, or read in sequence in the model chapter after this service run finishes.

> [!example]- Inside this model call — a small tensor example
> **Turn the input into token IDs and vectors**
>
> The inference service formats the messages and tool definition for the model. A tokenizer converts that formatted input into integer IDs. For a concrete example, encoding just `Why did build 42 fail?` with `tiktoken 0.12.0`, using `cl100k_base`, gives the following pieces and IDs.
>
> | Token pieces | Token IDs |
> | --- | --- |
> | `"Why", " did", " build", " ", "42", " fail", "?"` | `10445, 1550, 1977, 220, 2983, 3775, 30` |
>
> This tokenizer applies byte pair encoding (字节对编码), or BPE, to byte sequences, repeatedly merging adjacent pieces according to learned merge priorities. A piece can include a leading space. The full model input also contains the instructions, tool description, and formatting markers. Let `T` be the length of that entire sequence. [How token boundaries are chosen](../foundations/how-llms-work.md#How%20does%20the%20tokenizer%20choose%20token%20boundaries%3F)
>
> An embedding table maps each ID to a learned vector. With vocabulary size `N` and a deliberately small model width of `8`, the table has shape `N × 8`. ID `2983`, for example, selects row `2983`. Looking up every ID produces a `T × 8` hidden state, with one row per position. Later layers update these rows using the surrounding context. Each of the eight coordinates is a learned feature value, not a labeled slot for a particular word meaning.
>
> **Reminder — Reading a shape such as `T × 8`**
> `T` counts token positions; `8` counts features per position. One row is a vector, an ordered list of eight numbers. Transforming this into `T × 4` keeps the same positions and computes four new features for each one.
>
> **Let each position gather relevant information**
>
> Attention lets a position gather information from other visible positions. In this example, each of two attention heads (注意力头) takes the normalized `T × 8` state and uses three learned `8 × 4` projection matrices to produce Query (查询), Key (键), and Value (值), abbreviated Q, K, and V. Each resulting matrix has shape `T × 4`. The normalization rescales each row before projection, keeping its magnitude controlled while preserving its shape.
>
> **Reminder — What multiplication means here**
> A dot product (点积) multiplies corresponding coordinates and adds them, such as `[2, 3] · [4, 5] = 23`. Multiplying one width-`8` row by an `8 × 4` matrix computes one dot product per weight column, yielding four numbers. Each learned column defines a different weighted combination of the row's features.
>
> With rotary position embedding (旋转位置编码), or RoPE, Q and K are first rotated according to position. For one position, its Q is compared with each position's K by taking their dot product and dividing by `√4`. A causal mask (因果掩码) excludes positions to the right of the query. Softmax exponentiates those scores and divides each result by their sum. For scores `[1, 0]`, it gives approximately `[0.731, 0.269]`. The weights sum to one and determine how much each visible V contributes to the result. Here, comparing Q with K gives a relevance score for a pair of positions; it is a different use of the dot product from projecting features with a learned weight matrix. [The QKV calculation](../foundations/how-llms-work.md#How%20do%20Q%2C%20K%2C%20and%20V%20produce%20the%20attention%20update%3F)
>
> Take the row for the question mark in the user message. For this arithmetic illustration, keep only `build` and `42`, and assign them weights of `0.25` and `0.75`. If their V vectors are `(1, 0, 0, 0)` and `(0, 2, 0, 0)`, the result is `(0.25, 1.5, 0, 0)`.
>
> Each head performs its own calculation. At each position, their two width-`4` results are concatenated into a width-`8` vector, then mixed by an `8 × 8` output projection. A residual connection (残差连接) adds this update to the input state, coordinate by coordinate. For example, `[1, 2]` plus an update `[0.1, −0.2]` becomes `[1.1, 1.8]`. Matching the width lets each layer refine the existing representation. The result still has shape `T × 8`, now with information gathered across positions.
>
> **Transform the information within each position**
>
> A feed-forward network, or FFN, then transforms each row independently using shared learned weights. Attention has brought contextual information into a row. The FFN can combine those features nonlinearly and write an update back into that row.
>
> Using SwiGLU in our small model, two `8 × 16` projections of the normalized state produce candidate values and gate inputs. SiLU smoothly scales a gate input `x` by `1 / (1 + exp(−x))`. The result multiplies the corresponding candidate coordinate. This element-wise multiplication (逐元素乘法) keeps the `T × 16` shape, without summing across coordinates as a dot product does. For the question-mark row, suppose one candidate channel is `3` and its gate input is `1`. SiLU turns `1` into approximately `0.73`, so that channel becomes approximately `2.19`. A `16 × 8` down projection returns the result to the model width, and a residual connection adds it to the state produced by attention. The gate depends on the current row, allowing the same learned weights to produce different updates for different contexts. Those gates are continuous values, so “gate” here does not mean a binary switch. [FFNs and stacked layers](../foundations/how-llms-work.md#What%20does%20the%20FFN%20add%2C%20and%20how%20do%20blocks%20stack%3F)
>
> One Transformer layer combines these attention and FFN operations with normalization and residual connections. Each layer passes its `T × 8` output to the next layer, which has its own learned parameters. The diagram tracks the shapes through one layer of our example, including normalization before each sublayer.
>
> ~~~mermaid
> flowchart TD
>     X["Layer input<br/>T × 8, one row per token"]
>     Norm["Normalize for attention<br/>T × 8"]
>     H1["Head 1<br/>Q, K, V each T × 4<br/>Weighted output T × 4"]
>     H2["Head 2<br/>Q, K, V each T × 4<br/>Weighted output T × 4"]
>     A["Concatenate, then project<br/>T × 8"]
>     R["Add attention update to layer input<br/>T × 8"]
>     F["Normalize, then SwiGLU FFN<br/>Two T × 16 branches<br/>Gate, multiply, project to T × 8"]
>     Y["Add FFN update<br/>T × 8 for the next layer"]
>     X --> Norm
>     Norm --> H1 & H2
>     H1 & H2 --> A --> R
>     X -->|Residual| R
>     R --> F --> Y
>     R -->|Residual| Y
> ~~~
>
> **Convert the final state into output tokens**
>
> Processing the initial input is called prefill (预填充). After the last layer and final normalization in this example, the language model head, usually called the LM head, uses the vector at the last position of the complete formatted input to predict the first new token. Causal attention allows that position to attend to the whole supplied prefix. It may be an assistant-start marker added by the input template.
>
> The LM head projects that width-`8` vector through an `8 × N` matrix to obtain logits (未归一化分数), one score for each vocabulary entry. Decoding selects an ID, either by taking the highest score or by sampling from a probability distribution derived from the scores. For models that expose temperature, a lower value concentrates that distribution and a higher value spreads it out. These probabilities describe token selection, not the truth of the eventual answer. [How should an application choose decoding settings?](../foundations/how-llms-work.md#How%20should%20an%20application%20choose%20decoding%20settings%3F) connects this mechanism to a controlled comparison of agent behavior. The selected ID is appended to the sequence, and the model predicts the next one from the new position.
>
> A KV cache retains K and V for previous positions in each layer. At the new position, the model computes Q, K, and V, then uses that Q to attend to both the cached K/V and the new position's own K/V. It appends the new K/V to the cache for subsequent steps. Previous positions' Q vectors have already served their calculations and are not needed for this step. [Decoding and KV cache](llm-serving-and-kv-cache.md)

For our build question, this generation produces the tool name and arguments in the model's tool-call format. The inference service interprets the generated tokens according to the model's tool-call protocol and exposes the completed tool name and arguments as a structured API item. In a simplified notation, the application receives `tool_call(c1, read_build_log, {build_id: 42})`. The ID `c1` will associate the tool's result with this particular request. This correspondence matters when there are several pending calls, so the model can see which observation belongs to which request. The harness passes the proposed call to validation, taking the tool branch in the overview. Execution follows the checks in the next step.

## 3. Execute the request and retrieve the log

The application checks that `read_build_log` is available, that `build_id` has the required integer type, and that the caller may read build `42`. Argument validation establishes that the request can be interpreted. Authorization (授权) establishes which resource the caller may access. The application reads the log only after these checks succeed. If the tool instead changed external state, such as restarting a build, retries would also need to account for whether the previous attempt already took effect. [Tool contracts and authorization](../agents/tool-design-and-function-calling.md)

The retrieved result contains the evidence the model was missing.

| Field in the result for `c1` | Value from build `42` |
| --- | --- |
| Failed step | `unit-tests` |
| Failed test | `reject_empty_name` |
| Failed assertion | A request with an empty name should return HTTP `400`, but returned `200`. |
| Process exit status | `1` |

If authorization fails, the application can return a failure result for `c1`, allowing the next model call to explain that the evidence is unavailable. Here the tool retrieves one known log by ID. When a question requires finding relevant passages across many documents, the application can retrieve them and supply them to the model to generate an answer. This retrieval-and-generation process is called retrieval-augmented generation (检索增强生成), or RAG. [Retrieving and grounding an answer](../rag/rag-architecture-and-implementation.md)

## 4. Let the model use the retrieved evidence

The application now makes another model call. Alongside the original question and instructions, it includes the model's `tool_call(c1, …)` and the matching `tool_result(c1, …)`. The call records what was requested. The result supplies what the tool actually observed.

This second input contains `unit-tests`, `reject_empty_name`, and the expected `400` versus observed `200`. Those details are formatted and encoded as part of the model's context. The same inference mechanism processes the expanded input using the same trained weights. The new evidence changes what the model can base its answer on. It does not require retraining the model. The weights are persistent learned parameters; the input and hidden states are data for this run. [How training changes model parameters](../foundations/how-llms-work.md#How%20does%20next-token%20training%20update%20these%20parameters%3F) follows the separate learning process.

If the evidence leaves a gap, the model can request another tool call, and the application repeats validation, execution, and result collection within its configured limits on calls, elapsed time, and cost. If it reaches a limit, it should return an incomplete or failed outcome with the evidence obtained so far. In this case the log is enough to describe the observed failure, so the model generates an explanation. Determining the underlying code defect would require further evidence, such as the implementation and the intended behavior. [Actions, observations, and the next decision](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

## 5. Return the explanation and complete the run

The answer can now state what the log establishes.

> Build 42 failed at the `unit-tests` step. The `reject_empty_name` test expected HTTP `400` for a request with an empty name, but received `200`. The test process exited with status `1`. To identify the underlying cause, check the request-validation logic against the test's expected behavior.

The first model call ended with a tool request, leaving the application with work to do. The second ends normally with an answer. In this example, the application saves that answer and marks the run complete before returning the result to the caller. If it streams text as it is generated, the application must still track whether generation ultimately completed or failed. [Run state and recovery](ai-application-architecture.md)

The distinction between an observed failed assertion and its underlying cause also gives us an evaluation target. A changed prompt or decoding setting should preserve the log's actual values and avoid inventing an explanation for the defect. Include missing or inaccessible logs when checking that behavior. [How can you tell whether an AI system meets its task contract?](../evaluation/llm-evaluation-methods.md) develops those acceptance criteria and comparisons.

The service run is now complete. To follow the calculation inside either model call in more depth, continue with [how a language model turns a prompt into text](../foundations/how-llms-work.md). That chapter develops the mathematics, training, and generation choices in order.

> [!info]- Sources
> The fictional build-log scenario and small numerical examples illustrate the mechanisms supported below.
>
> - **Attention and position.** [Attention Is All You Need, v7, §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) supports scaled attention and head concatenation. [RoFormer, v5, §3.2](https://arxiv.org/html/2104.09864v5#S3.SS2) explains the rotary position mechanism. The layer example here uses pre-normalization and a decoder-only layout.
> - **FFN gating and the layer layout.** [GLU Variants Improve Transformer, 2020, §2](https://arxiv.org/html/2002.05202#S2) defines SwiGLU. The [Llama 3 reference implementation](https://github.com/meta-llama/llama-models/blob/main/models/llama3/model.py) shows pre-normalization, residual updates, and a gated FFN.
> - **Input formatting and generation.** [Transformers chat templates](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt) explains generation markers; its [cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation) describes reuse of previous K/V. The token pieces were reproduced with [tiktoken 0.12.0](https://github.com/openai/tiktoken/tree/0.12.0), using `cl100k_base`.
> - **Structured requests and the application loop.** The [OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) and [Claude tool-use guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools) describe tool definitions, model requests, application execution, and feeding results back. The `tool_call` and `tool_result` notation here is illustrative rather than an SDK schema. Run budgets and the proposed build-log evaluation are engineering choices for this example.
>
> Browse related papers in the [AI literature collection](../../review/ai-literature-index.md).
