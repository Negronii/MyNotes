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

The tool definition describes an available operation. The log itself enters the conversation only after the application retrieves it. The caller's identity is retained by the application for permission checks.

These inputs form the model's context (上下文) for this call. In a longer conversation, the application would also choose which earlier messages and evidence to include. That selection matters because the model can only condition its output on information actually supplied to it and knowledge encoded in its trained parameters. [Choosing the information for each model call](../context/context-engineering-principles.md)

## 2. Generate a request for the missing evidence

The model now has the question and a way to ask for logs. During inference (推理), it processes that input and generates an output one token (词元) at a time. In this run, the output specifies `read_build_log` with `build_id` set to `42`.

How can a sequence of numerical operations produce that request? We can follow the transformations inside a simplified decoder-only Transformer (仅解码器 Transformer). The small dimensions and numerical values below illustrate the computation. They are not measurements of a model responding to this question.

### Turn the input into token IDs and vectors

The inference service formats the messages and tool definition for the model. A tokenizer (分词器) converts that formatted input into integer IDs. For a concrete example, encoding just `Why did build 42 fail?` with `tiktoken 0.12.0`, using `cl100k_base`, gives the following pieces and IDs.

| Token pieces | Token IDs |
| --- | --- |
| `"Why", " did", " build", " ", "42", " fail", "?"` | `10445, 1550, 1977, 220, 2983, 3775, 30` |

This tokenizer applies byte pair encoding (字节对编码), or BPE, to byte sequences, repeatedly merging adjacent pieces according to learned merge priorities. A piece can include a leading space. The full model input also contains the instructions, tool description, and formatting markers. Let `T` be the length of that entire sequence. [How token boundaries are chosen](../foundations/how-llms-work.md#How%20does%20the%20tokenizer%20choose%20token%20boundaries%3F%20/%20%E5%88%86%E8%AF%8D%E5%99%A8%E6%80%8E%E6%A0%B7%E5%86%B3%E5%AE%9A%E8%BE%B9%E7%95%8C%EF%BC%9F)

An embedding table (嵌入表) maps each ID to a learned vector. With vocabulary size `N` and a deliberately small model width of `8`, the table has shape `N × 8`. ID `2983`, for example, selects row `2983`. Looking up every ID produces a `T × 8` hidden state (隐层状态), with one row per position. Later layers update these rows using the surrounding context.

### Let each position gather relevant information

Attention (注意力) lets a position gather information from other visible positions. In this example, each of two attention heads (注意力头) takes the normalized `T × 8` state and uses three learned `8 × 4` projection matrices to produce Query (查询), Key (键), and Value (值), abbreviated Q, K, and V. Each resulting matrix has shape `T × 4`.

With rotary position embedding (旋转位置编码), or RoPE, Q and K are first rotated according to position. For one position, its Q is compared with each position's K by taking their dot product and dividing by `√4`. A causal mask (因果掩码) excludes positions to the right of the query. Softmax converts the remaining scores into weights that sum to one, determining how much each visible V contributes to the result. [The QKV calculation](../foundations/how-llms-work.md#How%20do%20Q%2C%20K%2C%20and%20V%20produce%20the%20attention%20update%3F%20/%20Q%E3%80%81K%E3%80%81V%20%E6%80%8E%E6%A0%B7%E4%BA%A7%E7%94%9F%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F) · [Transformer §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2) · [RoFormer §3.2](https://arxiv.org/html/2104.09864v5#S3.SS2)

Take the row for the question mark in the user message. For this arithmetic illustration, keep only `build` and `42`, and assign them weights of `0.25` and `0.75`. If their V vectors are `(1, 0, 0, 0)` and `(0, 2, 0, 0)`, the result is `(0.25, 1.5, 0, 0)`.

Each head performs its own calculation. At each position, their two width-`4` results are concatenated into a width-`8` vector, then mixed by an `8 × 8` output projection. A residual connection (残差连接) adds this update to the input state. The result still has shape `T × 8`, now with information gathered across positions.

### Transform the information within each position

A feed-forward network (前馈网络), or FFN, then transforms each row independently using shared learned weights. Attention has brought contextual information into a row. The FFN can combine those features nonlinearly and write an update back into that row.

Using SwiGLU in our small model, two `8 × 16` projections of the normalized state produce candidate values and gate inputs. SiLU is applied to the gate inputs, and the two branches are multiplied element by element. For the question-mark row, suppose one candidate channel is `3` and its gate input is `1`. SiLU turns `1` into approximately `0.73`, so that channel becomes approximately `2.19`. A `16 × 8` down projection returns the result to the model width, and a residual connection adds it to the state produced by attention. The gate depends on the current row, allowing the same learned weights to produce different updates for different contexts. [FFNs and stacked layers](../foundations/how-llms-work.md#What%20does%20the%20FFN%20add%2C%20and%20how%20do%20blocks%20stack%3F%20/%20FFN%20%E5%A2%9E%E5%8A%A0%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B1%82%E6%80%8E%E6%A0%B7%E5%A0%86%E5%8F%A0%EF%BC%9F) · [GLU Variants §2](https://arxiv.org/html/2002.05202#S2)

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

### Convert the final state into output tokens

Processing the initial input is called prefill (预填充). After the last layer and final normalization in this example, the language model head, usually called the LM head, uses the vector at the last position of the complete formatted input to predict the first new token. Causal attention allows that position to attend to the whole supplied prefix. It may be an assistant-start marker added by the input template. [Chat templates and generation markers](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)

The LM head projects that width-`8` vector through an `8 × N` matrix to obtain logits (未归一化分数), one score for each vocabulary entry. Decoding (解码) selects an ID, either by taking the highest score or by sampling from a probability distribution derived from the scores. The selected ID is appended to the sequence, and the model predicts the next one from the new position.

A KV cache (键值缓存) retains K and V for previous positions in each layer. At the new position, the model computes Q, K, and V, then uses that Q to attend to both the cached K/V and the new position's own K/V. It appends the new K/V to the cache for subsequent steps. Previous positions' Q vectors have already served their calculations and are not needed for this step. [Decoding and KV cache](llm-serving-and-kv-cache.md) · [Transformers cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation)

For our build question, this generation produces the tool name and arguments in the model's tool-call format. The inference service interprets the generated tokens according to the model's tool-call protocol and exposes the completed tool name and arguments as a structured API item. In a simplified notation, the application receives `tool_call(c1, read_build_log, {build_id: 42})`. The ID `c1` will associate the tool's result with this particular request. The harness dispatches it to the tool handler, taking the tool branch in the overview. [OpenAI tool-calling flow](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) · [Claude application-managed tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools)

## 3. Execute the request and retrieve the log

The application checks that `read_build_log` is available, that `build_id` has the required integer type, and that the caller may read build `42`. Argument validation establishes that the request can be interpreted. Authorization (授权) establishes which resource the caller may access. The application reads the log only after these checks succeed. [Tool contracts and authorization](../agents/tool-design-and-function-calling.md)

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

This second input contains `unit-tests`, `reject_empty_name`, and the expected `400` versus observed `200`. Those details are formatted and encoded as part of the model's context. The same inference mechanism processes the expanded input using the same trained weights. The new evidence changes what the model can base its answer on. It does not require retraining the model.

If the evidence leaves a gap, the model can request another tool call, and the application repeats validation, execution, and result collection. In this case the log is enough to describe the observed failure, so the model generates an explanation. Determining the underlying code defect would require further evidence, such as the implementation and the intended behavior. [Actions, observations, and the next decision](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)

## 5. Return the explanation and complete the run

The answer can now state what the log establishes.

> Build 42 failed at the `unit-tests` step. The `reject_empty_name` test expected HTTP `400` for a request with an empty name, but received `200`. The test process exited with status `1`. To identify the underlying cause, check the request-validation logic against the test's expected behavior.

The first model call ended with a tool request, leaving the application with work to do. The second ends normally with an answer. In this example, the application saves that answer and marks the run complete before returning the result to the caller. If it streams text as it is generated, the application must still track whether generation ultimately completed or failed. [Run state and recovery](ai-application-architecture.md)
