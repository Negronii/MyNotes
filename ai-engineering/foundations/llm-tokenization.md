# How does a tokenizer map text to token IDs? / 分词器怎样把文本变成 token ID？

A tokenizer applies its learned or configured splitting rules and vocabulary to the input. The resulting IDs address entries the model was trained to use. Byte pair encoding learns which pieces to merge, so even a word outside a fixed word list can be represented by multiple pieces. / 分词器按已有的切分规则和词表处理文本，产出的 ID 对应模型训练时使用的词元。字节对编码学习哪些片段要合并，因此词表里没有整词时，也能用多个片段表示。

**Key terms / 关键术语** · vocabulary / 词表 · token ID / 词元编号 · merge rank / 合并优先级

## What is a token? / 什么是 token？

A tokenizer converts text into a sequence of model-specific units and their IDs. A unit can correspond to a whole word, part of a word, bytes, or another learned piece; whitespace and punctuation may be included in a token. The model's input is not a universal word vocabulary, and different tokenizers can split the same text differently.

## How does BPE build subword tokens? / BPE 如何构建子词 token？

Byte pair encoding (BPE) is one family of subword tokenization methods, not a rule used by every tokenizer. In a common training procedure, text is represented as basic symbols, adjacent symbol pairs are counted, and frequent pairs are merged iteratively; the learned merge sequence builds a vocabulary that includes multi-symbol pieces. Exact variants differ, including whether the basic symbols are bytes or characters.

At encoding time, the tokenizer starts from the model's basic symbols and applies learned merge priorities to the input before mapping resulting pieces to IDs. A rare word can therefore be represented as several learned pieces rather than an unknown whole word. This is a model-specific encoding procedure; merge ranks, vocabulary, and token boundaries differ across tokenizers. See Sennrich et al. for a BPE-based subword method in machine translation.

**Concrete example / 具体例子.** With the cl100k_base encoding in tiktoken 0.12.0, the text “The transformer architecture revolutionized NLP.” becomes [“The”, “ transformer”, “ architecture”, “ revolution”, “ized”, “ N”, “LP”, “.”] (8 tokens). It is one encoding's result, not a promise about every model or the full serialized API request. Exact counts can also include message structure, tools, images, or other inputs; use the target model's tokenizer or token-counting API when the count matters. [OpenAI's token guide](https://developers.openai.com/api/docs/concepts) gives a rough English estimate, but it is not a substitute for counting the actual input.

The IDs are the first handoff in [how a model generates text / 模型怎样生成文本](how-llms-work.md). [Sennrich et al.](https://arxiv.org/abs/1508.07909) describes a BPE-based subword method. The exact eight-token example was reproduced with `tiktoken` 0.12.0 using `cl100k_base`.
