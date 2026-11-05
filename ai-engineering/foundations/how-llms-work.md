# How does a language model turn a prompt into text? / 语言模型怎样把一段 prompt 变成文本？

A causal language model turns the prompt into token IDs and repeatedly predicts scores for the next token. The model uses the available prefix to form a representation for the next prediction. A decoding rule chooses one token, extends the prefix, and repeats until a stopping rule fires. The generated token sequence is decoded into text for the caller. / 因果语言模型先把提示词转成 token ID，再反复计算下一个词元的分数。模型利用已经可见的前缀构造用于预测的表示，解码规则每次选出一个词元并追加，直到满足停止条件。生成出的词元序列最终解码成文本交给调用方。

**Key terms / 关键术语** · token / 词元 · embedding / 嵌入 · hidden representation / 隐层表示 · logit / 未归一化分数 · decoding / 解码

## Turn the prompt into model inputs / 把提示词转成模型输入

The tokenizer maps text to vocabulary IDs. A learned embedding table supplies an initial vector for each ID. The model also incorporates position information, so it can distinguish the order in which tokens appear. The resulting vectors are the first representations the model processes. [How tokenization works / 分词如何工作](llm-tokenization.md) explains how the vocabulary and IDs are formed. The original Transformer describes its embeddings and positional encoding in [§§3.4–3.5](https://arxiv.org/html/1706.03762v7).

## Use the visible prefix to make a prediction / 用可见前缀做预测

In a typical decoder-only Transformer, causal attention lets a position draw information from the prefix it can see. Each block mixes information across positions with attention, then transforms each position with its feed-forward layer. The last position's final vector goes to an output projection, which produces a logit for each vocabulary entry. [How a Transformer block updates context / Transformer block 怎样更新上下文表示](transformer-context-updates.md) follows the intermediate vectors, attention projections, and residual paths.

## Choose a token and continue / 选出词元并继续生成

A [decoding rule / 解码规则](next-token-decoding.md) chooses a token by score or sampling. If the run is still active, the chosen ID becomes part of the next prediction's prefix. In a model that supports a KV cache, attention can reuse stored keys and values from previous positions instead of recomputing them for every decode step. The caller can receive text incrementally as output is decoded. Generation stops on the configured end condition, such as an end token or output limit. [Transformers cache explanation](https://huggingface.co/docs/transformers/main/en/cache_explanation)

~~~mermaid
flowchart LR
    P[Prompt text] --> T[Token IDs]
    T --> E[Embeddings and position information]
    E --> B[Transformer blocks update representations]
    B --> L[Output projection gives next-token logits]
    L --> D[Decoding rule selects a token]
    D --> N[Extend the generated sequence]
    N --> X[Decode available output into text]
    N --> S{Stop condition reached?}
    S -->|keep generating| B
    S -->|stop| F[Return the final output]
~~~

This example follows causal text generation. Model families differ in architecture, position methods, decoding constraints, and how they process images or audio. [What training asks a model to predict / 训练目标要求模型预测什么](language-model-training-objectives.md) explains the difference between causal and masked objectives. [Context engineering / 上下文工程](../context/context-engineering-principles.md) explains which information the application supplies. [Model selection / 模型选择](./model-selection-and-ecosystem.md) compares models against task requirements.
