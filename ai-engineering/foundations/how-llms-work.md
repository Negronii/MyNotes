# How LLMs Work / 大语言模型如何工作

**Core explanation / 核心解释：** An autoregressive text-generating language model processes token IDs and repeatedly predicts a distribution for the next token. Many widely used generators use a Transformer decoder with causal self-attention, but model families differ in architecture, tokenizer, training, and decoding API. / 自回归文本生成模型把文本转换为 token ID，并反复预测下一个 token 的概率分布。许多常见生成模型使用带因果自注意力的 Transformer 解码器，但不同模型的结构、分词器、训练方式和解码接口各不相同。

**30-second answer / 30 秒回答**

- **English:** A tokenizer maps text to model-specific tokens. A causal language model uses the prompt and generated prefix to produce next-token scores; a decoding rule selects the next token, which is appended and processed again. The Transformer is a common architecture, while its exact blocks, position method, and serving optimizations vary.
- **中文：** 分词器把文本映射为特定模型的 token。因果语言模型根据提示和已生成前缀计算下一个 token 的分数，再由解码策略选出 token 并追加到序列中。Transformer 是常见架构，但具体模块、位置编码和服务端优化会因模型而异。

**Key terms / 关键术语：** token / 词元；tokenizer / 分词器；autoregressive / 自回归；causal mask / 因果掩码；logit / 未归一化分数；decoding / 解码；context window / 上下文窗口。

## What is a token? / 什么是 token？

A tokenizer converts text into a sequence of model-specific units and their IDs. A unit can correspond to a whole word, part of a word, bytes, or another learned piece; whitespace and punctuation may be included in a token. The model's input is not a universal word vocabulary, and different tokenizers can split the same text differently.

## How does BPE build subword tokens? / BPE 如何构建子词 token？

Byte pair encoding (BPE) is one family of subword tokenization methods, not a rule used by every tokenizer. In a common training procedure, text is represented as basic symbols, adjacent symbol pairs are counted, and frequent pairs are merged iteratively; the learned merge sequence builds a vocabulary that includes multi-symbol pieces. Exact variants differ, including whether the basic symbols are bytes or characters.

At encoding time, the tokenizer starts from the model's basic symbols and applies learned merge priorities to the input before mapping resulting pieces to IDs. A rare word can therefore be represented as several learned pieces rather than an unknown whole word. This is a model-specific encoding procedure; merge ranks, vocabulary, and token boundaries differ across tokenizers. See Sennrich et al. for a BPE-based subword method in machine translation.

**Concrete example / 具体例子。** With the cl100k_base encoding in tiktoken 0.12.0, the text “The transformer architecture revolutionized NLP.” becomes the token sequence [“The”, “ transformer”, “ architecture”, “ revolution”, “ized”, “ N”, “LP”, “.”] (8 tokens). This is one encoding's result, not a promise about every current model or the full serialized API request. Exact counts can also include message structure, tools, images, or other inputs; use the target model's tokenizer or token-counting API when the count matters. [OpenAI's token guide](https://developers.openai.com/api/docs/concepts) gives a rough English estimate, but it is not a substitute for counting the actual input.

## Autoregressive generation and masked language models / 自回归生成与掩码语言模型

| Objective | What the model learns | Typical use |
|---|---|---|
| **Autoregressive / 自回归** | Predict the next token from preceding tokens, usually with a causal attention mask during training. | Left-to-right text generation and completion. |
| **Masked language modeling / 掩码语言建模** | Predict selected masked tokens using surrounding left and right context. | Bidirectional text representations and downstream understanding tasks. |

BERT is a well-known bidirectional masked-language model. It is not trained as a standard left-to-right next-token generator, but “cannot generate text” is too absolute: Wang and Cho formulate BERT as a Markov random field language model and describe a sampling procedure for generating sentences. That is an adapted procedure, not ordinary left-to-right decoding. Encoder-decoder models are another common design when input and output are distinct sequences, such as translation. [BERT](https://arxiv.org/abs/1810.04805); [Wang and Cho, BERT as a Markov random field language model](https://arxiv.org/abs/1902.04094); [Transformer](https://arxiv.org/abs/1706.03762).

## What happens inside a Transformer block? / Transformer block 内部如何工作？

In the original Transformer, an attention sublayer forms queries, keys, and values from the token representations. A scaled dot product between a query and keys becomes weights after softmax; the model uses those weights to combine the corresponding values. A decoder's causal mask prevents a position from attending to later tokens.

Multi-head attention repeats attention with distinct learned projections, concatenates the head outputs, then projects the combined representation. This lets the block combine information from different learned representation subspaces; a head should not automatically be read as a human-defined concept.

Attention mixes information across positions. Position encodings supply order information. A position-wise feed-forward sublayer then transforms each position separately with shared weights. In the original architecture, residual connections wrap each sublayer and layer normalization follows it. Later Transformer variants change these details, so this is a common mechanism, not a specification for every model. See [Attention Is All You Need, §§3.1–3.5](https://arxiv.org/html/1706.03762v7).

## How one generated token is produced / 如何生成一个 token

A simplified decoder-only generation pass is:

1. Encode the prompt as token IDs and map them to representations.
2. Process the sequence through attention and feed-forward blocks. Position information and a causal mask let each position use permitted context.
3. Project the final-position representation to **logits**, one score per candidate next token.
4. Convert scores into a distribution and select a token, for example by greedy selection or sampling.
5. Append the token and repeat until a stop condition, output limit, or another runtime condition is reached.

This is an explanatory sketch, not a specification of every model. Implementations may use different attention layouts, position schemes, normalization, output constraints, caching, or non-text input paths. A text token sequence also does not imply that images or audio are handled as ordinary words.

For standard dense self-attention, forming pairwise attention scores over a sequence of length n has quadratic dependence on n. This describes that operation, not necessarily the total latency or cost of a deployed model: feed-forward work, attention variants, hardware, batching, and caching also matter.

## Temperature, top-k, and top-p / 温度、top-k 与 top-p

Given next-token logits z_i, temperature T > 0 changes their sharpness before softmax:

$$
P(i) = \frac{\exp(z_i/T)}{\sum_j \exp(z_j/T)}
$$

Lower T concentrates probability on high-scoring tokens; higher T flattens it. In the idealized limit as T approaches zero, selection approaches argmax, but API support and reproducibility behavior are provider- and model-specific.

- **Top-k / 前 k 项：** keep only the k highest-probability candidates, then decode from them.
- **Top-p / nucleus sampling / 核采样：** keep the smallest ranked set whose cumulative probability reaches p, then decode from that set.
- **Greedy decoding / 贪心解码：** choose the highest-scoring candidate instead of sampling.

These controls change decoding behavior; none makes an answer more factual. Parameter availability and interactions vary. For example, the OpenAI Responses API reference checked on 2026-10-15 documents temperature and top_p and recommends changing one rather than both for that API; do not assume another provider exposes the same parameters. [Nucleus sampling paper](https://arxiv.org/abs/1904.09751), [OpenAI Responses API reference](https://developers.openai.com/api/reference/resources/responses/methods/create).

## Related notes / 相关笔记

- [Model Selection and Ecosystem / 模型选择与生态](./model-selection-and-ecosystem.md) compares candidates against task requirements.
- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) explains context limits, token cost, and prompt caching.

## Sources / 来源

- Vaswani et al., [Attention Is All You Need](https://arxiv.org/abs/1706.03762).
- Devlin et al., [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805).
- Wang and Cho, [BERT has a Mouth, and It Must Speak: BERT as a Markov Random Field Language Model](https://arxiv.org/abs/1902.04094).
- Sennrich et al., [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909).
- OpenAI, [Key concepts: Tokens](https://developers.openai.com/api/docs/concepts), checked 2026-10-15. The tokenization above was reproduced locally with Python 3.11.13 and tiktoken 0.12.0 using cl100k_base.
