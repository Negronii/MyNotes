# How does a language model turn a prompt into text?

## Following a short input through the model

Imagine the build-log assistant has prepared a message for its model. The application can supply a question, tool descriptions, or retrieved logs, but the model needs to turn that input into numbers before it can generate anything. This chapter follows that numerical path, then explains how training produced the parameters used along the way. The surrounding application loop is covered in [how an AI service turns one message into a complete answer](../systems/from-message-to-answer.md).

We will use a tiny decoder-only Transformer (仅解码器 Transformer) so that its shapes and arithmetic fit on the page. It has a model width of `8`, two attention heads, and a gated feed-forward network. We first build a toy tokenizer for `ababca`, then carry its three token positions through the model. The text and numbers are teaching examples; they do not demonstrate a trained model understanding that string. For a real tokenizer comparison, we also inspect an ordinary English sentence.

~~~mermaid
flowchart TD
    Text["Format text, then tokenize<br/>Example: ababca → 3 IDs"] --> E["Look up embeddings<br/>3 positions × 8 features"]
    subgraph Pass["One pass through all Transformer layers"]
        A["Attention<br/>Gather information across visible positions"] --> F["FFN<br/>Transform features within each position"]
        F --> More{"More layers?"}
        More -->|Yes, next layer's weights| A
    end
    E -->|Start at layer 1| A
    More -->|No| L["Final normalization and LM head<br/>Score vocabulary from the last position"]
    L --> D["Select one token<br/>Append its ID to the prefix"]
    D --> Stop{"Stop condition?"}
    Stop -->|No| Next["Embed the new token"]
    Next -->|Restart at layer 1<br/>Reuse per-layer cached K/V| A
    Stop -->|Yes| Out["Return the generated sequence<br/>Decode token bytes into text"]
~~~

Text can also be decoded incrementally while generation continues. The important loop is that each selected token becomes part of the input for predicting the next one.

## How does the tokenizer choose token boundaries?

A token (词元) is an entry in a particular vocabulary. It may represent punctuation, a byte, part of a word, a whole word, or a piece with a leading space. A tokenizer (分词器) maps text to these entries' integer IDs. The IDs identify entries; a larger ID does not mean a stronger or more important word.

For byte-level byte pair encoding (字节级字节对编码), or BPE, training starts from byte-sized pieces and repeatedly merges frequent adjacent pairs. In a common implementation, a regular expression first divides the text into segments, and BPE operates within those segments. Encoding new text uses the already learned merge priorities.

Suppose the training segments are `abab`, `ab`, and `ac`. Begin with 256 single-byte entries, numbered `0` through `255`. The pair `a+b` occurs three times, so the first merge creates `ab`, with ID `256`. The segments become `[ab, ab]`, `[ab]`, and `[a, c]`. Next, `ab+ab` and `a+c` each occur once. Let our toy tie-breaking rule choose `ab+ab`, creating `abab` with ID `257`.

| Step | What happens to the previously unseen input `ababca` |
| --- | --- |
| Start with bytes | `[a, b, a, b, c, a]` |
| Apply the highest-priority available merge | `[ab, a, b, c, a]`, then `[ab, ab, c, a]` |
| Apply the next merge | `[abab, c, a]` |
| Look up the three IDs | `[257, 99, 97]` |

For a real example, `tiktoken 0.12.0` with `cl100k_base` encodes `The transformer architecture revolutionized NLP.` as eight pieces, `["The", " transformer", " architecture", " revolution", "ized", " N", "LP", "."]`, with IDs `[791, 43678, 18112, 14110, 1534, 452, 12852, 13]`. Spaces belong to some pieces. Another tokenizer can segment the same sentence differently.

> [!tip] A token boundary need not be a character boundary
> A Unicode character can occupy several UTF-8 bytes. Byte-level token pieces can split those bytes, so decoding one token at a time as a complete string can produce broken characters. Incremental text decoding keeps incomplete bytes until the rest arrive.

This matters when budgeting a request. Count the input using the deployed model's tokenizer and request format, including role markers and tool definitions. If the full conversation is too large, the next decision is [which information each model call should retain](../context/context-engineering-principles.md), rather than simply counting words. BPE is one tokenizer family, not a requirement of the Transformer computation below.

## What enters the first block?

An embedding table (嵌入表) contains one learned vector for each vocabulary entry. Let vocabulary size be `N`, model width be `d`, and input length be `T`. For our toy vocabulary, `N = 258`, `d = 8`, and `T = 3`. The table `E` has shape `258 × 8`.

ID `257` selects row `257` of `E`, and IDs `99` and `97` select their rows. Stacking the retrieved rows gives the initial hidden state (隐层状态), `X₀`, with shape `3 × 8`. Position one now holds a vector for `abab`, position two for `c`, and position three for `a`.

> [!tip] Read the axes before reading the numbers
> In `T × d`, rows are token positions and columns are learned feature coordinates. One row is a vector (向量), an ordered list of `d` numbers. A column tracks one coordinate across positions. Adding a batch axis would group several such sequences. A feature coordinate does not come with a fixed human-readable label such as “basketball.”

The same ID selects the same initial row, but later layers change its representation according to position and context. Mathematically, lookup is equivalent to multiplying a one-hot vector (独热向量), with a single `1` at the selected ID and zeros elsewhere, by `E`. An implementation normally retrieves the row directly.

Before an attention sublayer uses these vectors, our model applies normalization (归一化). For example, RMSNorm divides each row by the square root of its mean squared coordinates plus a small stability constant, then applies learned coordinate scales. Ignoring that tiny constant and taking learned scales as one, `[3, 4]` is divided by `√((9+16)/2) ≈ 3.536`, giving approximately `[0.849, 1.131]`. This keeps the numerical scale controlled without changing the row count or width. We call the normalized matrix `U`. Position information will enter through Q and K in the next step.

## How do Q, K, and V produce the attention update?

### Project each row into Q, K, and V

Attention (注意力) computes what information each position should gather from visible positions. It derives three representations from the current hidden state. Query (查询), or Q, participates in deciding what to match. Key (键), or K, participates in the matching score. Value (值), or V, supplies the content that will be combined using those scores. These roles describe how the vectors are used in the computation.

Each attention head (注意力头) has learned projections for Q, K, and V. In our example, a head has width `4`. Multiplying the `3 × 8` matrix `U` by that head's `8 × 4` Q matrix produces `3 × 4` Q values. K and V are produced the same way, using their own matrices.

> [!tip] What does a matrix product produce?
> Each output coordinate is a dot product (点积) of an input row and a weight column. For example, `[2, 3] · [4, 5] = 2×4 + 3×5 = 23`. With weight columns `[4, 5]` and `[1, −1]`, the same row becomes `[23, −1]`. Each column defines one weighted combination of the input features. Thus, `3 × 8` times `8 × 4` keeps three positions and produces four features per position. The matching inner dimensions specify which coordinates are multiplied and summed.

Computing both heads together is convenient. With `Hq = 2` heads and width `dh = 4`, each combined projection matrix has shape `d × (Hq·dh) = 8 × 8`. We compute `Q = UW_Q`, `K = UW_K`, and `V = UW_V`, then split the feature axis into two width-`4` heads. Each head receives its own `3 × 4` Q, K, and V. This notation uses row vectors multiplying weights on the right. A library may store the weight transposed; PyTorch `Linear`, for example, stores output features by input features.

Our model uses rotary position embedding (旋转位置编码), or RoPE. It rotates pairs of Q and K coordinates according to their positions before computing their dot products. The resulting scores can depend on relative position. The shapes remain unchanged.

### Turn pairwise scores into a weighted mixture

For a head, compute the score between every query position and every key position.

$$
S = \frac{QK^\top}{\sqrt{d_h}} + M,\qquad
P = \operatorname{softmax}_{\mathrm{keys}}(S),\qquad
Z = PV.
$$

Here `Kᵀ` denotes the transpose (转置), which swaps K's rows and columns. `Q` is `3 × 4`, while `Kᵀ` is `4 × 3`, so the product is `3 × 3`. Entry `(i, j)` is the dot product of position `i`'s Q and position `j`'s K. Each row now lists one position's scores for all positions. This product compares positions; the earlier `UW_Q` transformed features within each position.

Dividing by `√dh` controls the score scale as head width grows. Under the motivating approximation of independent, unit-variance coordinates, a sum of `dh` products has variance proportional to `dh`. Scaling helps avoid very large score differences that make softmax concentrate almost entirely on one entry.

The causal mask (因果掩码) `M` assigns `−∞` to positions to the right of the query and zero elsewhere. This prevents a position from reading future tokens. For the second position, token `c`, take an already position-rotated Q of `[2, 0, 0, 0]`. Let the rotated K rows for `abab`, `c`, and `a` be `[1, 0, 0, 0]`, `[0, 1, 0, 0]`, and `[2, 0, 0, 0]`. Their dot products with this Q are `[2, 0, 4]`. Dividing by `√4 = 2` gives `[1, 0, 2]`. The future token `a` scores highest, but the mask excludes it, leaving `[1, 0, −∞]`.

> [!tip] Softmax turns scores into relative weights
> Softmax exponentiates each score and divides by the sum of the exponentials. Here `e ≈ 2.718`. For `[1, 0, −∞]`, the weights are `[e/(e+1), 1/(e+1), 0] ≈ [0.731, 0.269, 0]`. They sum to one. These weights describe how this head mixes V vectors; they are not probabilities that the corresponding words are true.

Suppose the first two V vectors are `(1, 0, 0, 0)` and `(0, 2, 0, 0)`. The second position's weighted sum is

$$
0.731(1,0,0,0)+0.269(0,2,0,0)=(0.731,0.538,0,0).
$$

Across all three query positions, `P` is `3 × 3` and `V` is `3 × 4`, so `Z = PV` is `3 × 4`. Each output row now contains information gathered from the positions it could see.

### Combine heads and retain the previous state

The other head has its own projections and weighted sums. Concatenation (拼接) places the two width-`4` outputs side by side for each position, producing `3 × 8`. An `8 × 8` output projection `W_O` mixes those features. A residual connection (残差连接) adds the attention update back to the layer's original input, coordinate by coordinate.

If one original row were `[1, 2]` and its update `[0.1, −0.2]`, residual addition would produce `[1.1, 1.8]`. Both terms need the same shape. Each layer can preserve existing information while learning an update. The output still has one width-`8` row per token position.

Head behavior can vary across layers, tasks, and inputs. A head might often attend to the preceding position, but a weight map alone does not establish its complete function. Its V vectors, output projection, and later layers all affect the result.

### What changes when heads share K and V?

The calculation above uses multi-head attention (多头注意力), or MHA, with one K/V head for every Q head. Grouped-query attention (分组查询注意力), or GQA, shares a K/V head among a group of Q heads. Keeping two Q heads but only one K/V head makes `W_Q` remain `8 × 8`, while `W_K` and `W_V` become `8 × 4`. Both queries still generate their own width-`4` output, so concatenation and `W_O` retain their shapes.

MHA has `Hkv = Hq`; multi-query attention (多查询注意力), or MQA, is the case `Hkv = 1`. These choices affect learned weights and the amount of K/V stored during generation. Converting an MHA checkpoint changes its K/V weights and behavior; the GQA paper evaluates an averaging-based conversion and further training. With three cached positions, our MHA example stores `2 × 3 × 2 × 4 = 48` K/V values per layer. Sharing one K/V head reduces that to `2 × 3 × 1 × 4 = 24`, while both Q heads still calculate their own scores. To understand the serving consequence, continue with [how KV cache and scheduling determine inference capacity](../systems/llm-serving-and-kv-cache.md). Dense attention's pairwise work grows with `T²`, but actual latency also depends on kernels, other layers, and the hardware.

## What does the FFN add, and how do blocks stack?

### Transform each position's features

The attention update has brought contextual information into each row. A feed-forward network (前馈网络), or FFN, applies a nonlinear transformation within each row. It is also often called an MLP. The same FFN weights are used for all positions within a layer, while different layers normally have different weights. Without a nonlinear operation between its projections, several linear transformations would collapse into a single linear transformation; the nonlinearity lets the update depend more richly on combinations of input features.

For a SwiGLU FFN, first normalize the attention-updated state to obtain `R`, with shape `3 × 8`. Two projections, `W_g` and `W_u`, each of shape `8 × 16`, generate a gate input and a candidate branch. Apply SiLU to the gate input, multiply the branches element by element, then project back using `W_d`, with shape `16 × 8`.

$$
F(R)=\big[\operatorname{SiLU}(RW_g)\odot(RW_u)\big]W_d,
\qquad \operatorname{SiLU}(x)=x\sigma(x),
\qquad \sigma(x)=\frac{1}{1+e^{-x}}.
$$

The sigmoid `σ` lies between zero and one. SiLU multiplies its input by that factor, producing a smooth nonlinear transformation. In this use, the resulting gate values can be negative or greater than one. They scale candidate features continuously rather than acting as binary on/off switches.

> [!tip] Element-wise multiplication keeps the shape
> The symbol `⊙` multiplies matching coordinates without summing over them. For `[0, 0.731] ⊙ [2, 3]`, the result is `[0, 2.193]`. Two `3 × 16` branches therefore produce another `3 × 16` matrix. This differs from a dot product, which sums products to produce one number.

For example, gate inputs `[0, 1]` become approximately `[0, 0.731]` after SiLU. With candidate values `[2, 3]`, those two channels become `[0, 2.193]`. The down projection mixes the 16 channels into eight, and a residual connection adds the result to the attention-updated state. Because the gate and candidate branches both depend on the current row, the same weights can produce different updates for different contexts.

This helps explain why learned knowledge can affect a prediction. If a row represents a person's name in a basketball context, learned feature combinations can activate directions that influence related output tokens. Geva and colleagues found text-pattern associations and output effects in parts of the FFNs they studied. This is evidence about those models, not a literal fact database inside every FFN. A model's factual output also depends on attention, multiple layers, and the final vocabulary projection. When information must be current or verifiable, [retrieval and grounding](../rag/rag-architecture-and-implementation.md) explain how an application can supply external evidence.

### Pass the updated state through the next layer

Our block uses pre-normalization (预归一化), with normalization before attention and before the FFN. If `Xℓ` is layer `ℓ`'s input, the two updates are

$$
Y_\ell=X_\ell+\operatorname{Attention}_\ell(\operatorname{Norm}_{\ell,1}(X_\ell)),
$$
$$
X_{\ell+1}=Y_\ell+F_\ell(\operatorname{Norm}_{\ell,2}(Y_\ell)).
$$

~~~mermaid
flowchart TD
    X["Layer input X<br/>3 × 8"] --> N1["Normalize"] --> A["Attention<br/>Mix information across positions"]
    A --> Y["Add attention update<br/>Y is 3 × 8"]
    X -->|Residual| Y
    Y --> N2["Normalize"] --> F["SwiGLU FFN<br/>Expand to 3 × 16, gate, project to 3 × 8"]
    F --> Next["Add FFN update<br/>Next layer receives 3 × 8"]
    Y -->|Residual| Next
~~~

Each layer performs another transformation over the same positions. In this model, length and width do not shrink as layers accumulate. The familiar decoder-only design choices illustrated here include RMSNorm, RoPE, and a gated FFN; K/V sharing is a separate architectural choice. The 2017 Transformer established attention and position-wise FFNs in an encoder–decoder model for translation. Its decoder also used cross-attention, and its normalization and FFN choices differed. The equations here describe the chosen decoder-only example; a particular model's implementation determines its architecture.

### Which numbers are learned parameters?

A matrix's parameter count is its row count times its column count. With ordinary MHA and `Hq·dh = d`, the Q, K, V, and output projections total `4d²` parameters. At `d = 8`, that is `256`. The three SwiGLU projections total `3d·dff`; with `dff = 16`, that is `384`.

A complete model also includes the embedding table, normalization weights, and possibly a separate vocabulary projection. Repeat the per-layer count for each layer's own weights; count shared weights once. Hidden states and cached K/V are temporary data computed from those parameters. Consequently, parameter count alone does not determine how many concurrent requests fit on a GPU. That is another reason to follow the [inference memory and scheduling chapter](../systems/llm-serving-and-kv-cache.md).

## How does the model choose a token and continue?

### Score the vocabulary and select an ID

After the final layer and final normalization, the LM head takes the last input position's vector, `h_last`, with shape `1 × 8`. For `[abab, c, a]`, this is the updated row for `a`. Under causal attention, this position can attend to the whole supplied prefix. In a formatted chat, it might be an assistant-start marker rather than the last character of the user's question.

Multiplication by `W_lm`, with shape `8 × 258`, gives `1 × 258` logits (未归一化分数), one score for each vocabulary ID. Each column of `W_lm` produces one score by a dot product with `h_last`. Weight tying (权重绑定) uses the embedding table's transpose as this output weight, saving a separate parameter matrix. Some architectures use separate input and output weights.

For sampling (采样), temperature (温度) `τ > 0` rescales logits before softmax.

$$
p_i=\frac{\exp(z_i/\tau)}{\sum_j\exp(z_j/\tau)}.
$$

For a small illustration restricted to two eligible candidates, `c` (ID `99`) and `a` (ID `97`), suppose their logits are `[2, 1]`. Then temperature `1` gives probabilities about `[0.731, 0.269]`. At `0.5`, they become `[0.881, 0.119]`; at `2`, `[0.622, 0.378]`. Lower temperature concentrates probability on the higher-scoring candidate. Higher temperature gives lower-scoring candidates more chance. These are next-token probabilities, not confidence that an answer is factually correct.

Greedy decoding (贪心解码) directly chooses the highest-scoring token. An API's temperature-zero setting may request greedy behavior; the formula above cannot literally divide by zero. Top-k sampling keeps the `k` highest-scoring candidates. Top-p, or nucleus sampling (核采样), keeps the smallest descending-probability prefix whose total reaches the threshold, then renormalizes. For `[0.50, 0.30, 0.15, 0.05]` and top-p `0.75`, the first two remain, becoming `[0.625, 0.375]` after division by their sum `0.80`.

### How should an application choose decoding settings?

The practical choice starts with the deployed model and endpoint. Check which controls are supported and which combinations are allowed, then establish a baseline with the supported defaults. Sampling controls depend on the model and API version; some hosted interfaces restrict, fix, or omit them. There is no single temperature that is best for every model and task.

For the build-log assistant, try a supported lower-temperature candidate if repeated runs vary unnecessarily in tool arguments or evidence reporting. Compare it against the baseline on normal failures, missing logs, permission failures, and misleading log text. A lower setting can repeatedly favor an incorrect action, so repeatability alone is not a success criterion.

For a task that deliberately generates several candidate explanations or solutions for later verification, testing more sampling diversity can be useful. The cost is more weak or invalid candidates and more verification work. Higher temperature does not supply missing evidence or make unsupported claims acceptable. Whether diversity improves the final result depends on the candidate generator and the verifier together.

A controlled comparison holds the model version, instructions, tools, and case set fixed while changing the chosen decoding setting. For each candidate, repeat complete runs and measure correct tool selection and arguments, grounded explanations, appropriate failure handling, cost, and latency. Develop settings on one set and use a separate held-out set for acceptance. This is an engineering testing approach, not a reported result that lower or higher temperature wins. [How to build a comparable evaluation set](../evaluation/llm-evaluation-methods.md#Build%20a%20comparable%20regression%20set%20/%20%E5%BB%BA%E7%AB%8B%E5%8F%AF%E6%AF%94%E8%BE%83%E7%9A%84%E5%9B%9E%E5%BD%92%E9%9B%86) develops the evaluation method beyond this one setting.

### Reuse the prefix and predict the next token

Prefill (预填充) processes the initial sequence through the layers. The last position's logits select the first output token. Suppose we select `c`, ID `99`. The token sequence grows from `[257, 99, 97]` to `[257, 99, 97, 99]`. Decode (增量解码) embeds that new `c` position and processes it starting at layer one to predict the next token.

In a causal model, adding a new position cannot change earlier positions' hidden states for the same prefix and inference configuration. A KV cache (键值缓存) therefore stores each layer's earlier K and V. At a new position, that layer computes new Q, K, and V. Its Q attends to the cached K/V and its own K/V, and the new K/V are appended to the cache. Earlier Q vectors have already served their own positions' calculations and are not inputs to this new query's attention operation.

The cache is layer-specific because every layer has different input representations and projection weights. As output grows, so does the cache. Generation ends at a model end token, an application stop sequence, a length limit, or cancellation. A length limit can cut off an unfinished answer, so the application must interpret the completion reason. [Serving capacity](../systems/llm-serving-and-kv-cache.md) develops the memory consequence; [application run state and recovery](../systems/ai-application-architecture.md) develops what happens when generation ends or is interrupted.

## How does next-token training update these parameters?

### Set a target for each position

So far we have used already learned weights. Training adjusts them using examples of what should come next. In a training sequence `[BOS, a, b, c]`, `BOS` is a beginning-of-sequence marker. Its target is `a`, the target at `a` is `b`, and the target at `b` is `c`. The causal mask allows these predictions to be calculated in parallel while preventing each position from reading its target to the right.

Teacher forcing (教师强制) means that training uses the actual preceding tokens from the training example. During generation, subsequent input contains the tokens the model actually selected. This difference is why a mistake early in a generated sequence can alter later predictions.

### Measure error and propagate an update

For training here, `p` is ordinary softmax over the raw logits for the full vocabulary, without inference-time temperature or top-k/top-p filtering. For target ID `y_i`, cross-entropy (交叉熵) uses `−log p(y_i)` and averages over the positions included in training. Assigning the correct token probability `0.8` gives loss about `0.223`; probability `0.25` gives about `1.386`. Their average is approximately `0.805`, using natural logarithms, whose unit is called a nat. Low probability on the correct token incurs a larger penalty.

For one position, the derivative of this loss with respect to the logits is `p − onehot(y_i)`. This keeps every probability entry except the correct one, from which it subtracts `1`. If the probabilities are `[0.7, 0.2, 0.1]` and the second token is correct, that gradient is `[0.7, −0.8, 0.1]`.

> [!tip] A gradient tells us how the loss changes locally
> A positive derivative means increasing that quantity slightly would increase loss. Gradient descent therefore subtracts a small multiple of the derivative. In the example, an update applied directly to logits would lower the first and third and raise the second. Training actually updates the shared parameters that produced those logits, using the chain rule (链式法则) to propagate their effects through the computation.

Backpropagation (反向传播) carries derivatives through the LM head, residual additions, FFNs, attention, and embeddings. For a simple chain `z = wx` with a fixed `x`, `∂L/∂w = (∂L/∂z)x`. Matrix versions accumulate contributions from many coordinates and positions. An optimizer applies parameter updates, with its own rules for step size and accumulated statistics. Training is a new computation of derivatives through the forward operations; it does not run an inverse model backward from the answer.

The chosen training objective matters. Masked language modeling (掩码语言建模), as used in BERT, predicts selected missing positions using visible context on both sides. Its usual procedure differs from the left-to-right loop above. Research can build iterative generation procedures from masked models, but those require their own sampling process.

If an application repeatedly fails in a stable way, the next question is whether it lacks evidence, instructions, or learned behavior. [When to fine-tune](../fine-tuning/fine-tuning-strategies.md) develops that choice, including which parameters to update. Feeding new evidence into a prompt changes the current computation; training changes parameters that persist into later runs.

> [!info]- Sources
> Sources below support the named mechanisms. Small tensor dimensions, made-up vectors, and the build-log tuning scenario are teaching examples or engineering extensions.
>
> - **Tokenization.** [Sennrich et al., 2016, §3.2](https://aclanthology.org/P16-1162/) explains subword BPE. [tiktoken 0.12.0 educational implementation](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken/_educational.py) implements byte-level training, merge priorities, and decoding. The exact English token sequence in this chapter was reproduced with that package version and `cl100k_base`.
> - **Attention and the original architecture.** [Attention Is All You Need, v7, §§3.1–3.5 and §5.1](https://arxiv.org/html/1706.03762v7#S3) supports scaled dot products, masking, multi-head concatenation, position-wise FFNs, and the original encoder–decoder's scope. Its translation setup is not the decoder-only model illustrated here.
> - **Position and normalization.** [RoFormer, v5, §3](https://arxiv.org/html/2104.09864v5#S3) explains RoPE; [Root Mean Square Layer Normalization, 2019, §3](https://arxiv.org/abs/1910.07467) explains RMSNorm. [The Llama 3 Herd of Models, v3, §3.2](https://arxiv.org/html/2407.21783v3#S3.SS2) and the [Llama 3 reference implementation](https://github.com/meta-llama/llama-models/blob/main/models/llama3/model.py) ground the decoder-only design choices and normalization order. Model-specific implementations determine the exact configuration.
> - **Projection storage and K/V sharing.** [PyTorch Linear](https://docs.pytorch.org/docs/stable/generated/torch.nn.Linear.html) specifies the stored weight orientation. [GQA, EMNLP 2023, §2](https://aclanthology.org/2023.emnlp-main.298/) describes grouped K/V heads and converting models through uptraining.
> - **FFN gating and interpretation.** [GLU Variants Improve Transformer, 2020, §2](https://arxiv.org/html/2002.05202#S2) defines SwiGLU. [Geva et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.446/) studies pattern associations and output effects in FFN memories, with conclusions limited to its analyzed models.
> - **Sampling and deployment controls.** [The Curious Case of Neural Text Degeneration, v2, §3](https://arxiv.org/abs/1904.09751v2) introduces nucleus sampling. [Transformers generation configuration](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation) documents sampling controls. [OpenAI Responses parameters](https://developers.openai.com/api/reference/resources/responses/methods/create) documents a hosted API contract. [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model) and [Claude model migration guidance](https://platform.claude.com/docs/en/about-claude/model-deprecations), checked 2026-11-06, illustrate model- and API-version-specific restrictions. The proposed tuning comparison is an engineering application of these mechanisms, not a universal temperature recommendation.
> - **Cached generation.** [Transformers cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation) explains causal reuse, per-layer K/V, and the new token's attention over previous and current positions.
> - **Training.** [Llama 3, v3, §3](https://arxiv.org/html/2407.21783v3#S3) covers pretraining; [PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html) specifies the loss. [BERT, 2019, §3.1](https://arxiv.org/abs/1810.04805) supports the masked objective, and [Wang and Cho, 2019](https://arxiv.org/abs/1902.04094) explores a distinct iterative generation procedure.
>
> Browse related papers in the [AI literature collection](../../review/ai-literature-index.md).
