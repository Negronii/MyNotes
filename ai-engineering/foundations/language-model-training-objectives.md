# What does a language model learn to predict during training? / 语言模型训练时学习预测什么？

The objective chooses a target and which input the model can see when predicting it. A causal model learns to score the next token from the preceding text. A masked model learns to fill selected gaps using surrounding context. This distinction explains why the two objectives support different default generation behavior. / 训练目标决定要预测什么，也决定预测时能看到哪些输入。因果模型学习根据已有文本预测下一个词元。掩码模型学习利用周围文本补全选中的空缺。这两个训练目标使模型具备不同的默认生成方式。

**Key terms / 关键术语** · training objective / 训练目标 · autoregressive / 自回归 · masked language modeling / 掩码语言建模

## Autoregressive generation and masked language models / 自回归生成与掩码语言模型

| Objective | What the model learns | Typical use |
|---|---|---|
| **Autoregressive / 自回归** | Predict the next token from preceding tokens, usually with a causal attention mask during training. | Left-to-right text generation and completion. |
| **Masked language modeling / 掩码语言建模** | Predict selected masked tokens using surrounding left and right context. | Bidirectional text representations and downstream understanding tasks. |

BERT is a well-known bidirectional masked-language model. It is not trained as a standard left-to-right next-token generator, but “cannot generate text” is too absolute: Wang and Cho formulate BERT as a Markov random field language model and describe a sampling procedure for generating sentences. That is an adapted procedure, not ordinary left-to-right decoding. Encoder-decoder models are another common design when input and output are distinct sequences, such as translation. [BERT](https://arxiv.org/abs/1810.04805); [Wang and Cho, BERT as a Markov random field language model](https://arxiv.org/abs/1902.04094); [Transformer](https://arxiv.org/abs/1706.03762).

In causal training, the target is the known next token from the training sequence. During [generation / 生成](how-llms-work.md), the model instead extends the sequence with a token chosen by the decoder. [Fine-tuning / 微调](../fine-tuning/fine-tuning-strategies.md) covers how to change a repeatable behavior after choosing a base model.
