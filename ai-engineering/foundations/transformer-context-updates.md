# How does a Transformer block update a token using context? / Transformer block 怎样利用上下文更新词元表示？

Each token enters a block as a vector from the embedding stage or previous block. Self-attention uses learned query, key, and value projections to decide how much information to take from permitted positions. A position-wise feed-forward layer transforms each updated vector. Residual paths and normalization connect the sublayers, with the exact ordering depending on the model. / 每个词元进入 block 时都是一个向量，来自嵌入阶段或上一层。自注意力用训练得到的 Q、K、V 投影计算应从可见位置取多少信息，再由逐位置的前馈层变换每个向量。残差连接和归一化连接这些子层，具体顺序取决于模型。

**Key terms / 关键术语** · hidden representation / 隐层表示 · query, key, value / 查询、键、值 · causal mask / 因果掩码 · feed-forward layer / 前馈层

## What happens inside a Transformer block? / Transformer block 内部如何工作？

In the original Transformer, an attention sublayer forms queries, keys, and values from the token representations. A scaled dot product between a query and keys becomes weights after softmax; the model uses those weights to combine the corresponding values. A decoder's causal mask prevents a position from attending to later tokens.

Multi-head attention repeats attention with distinct learned projections, concatenates the head outputs, then projects the combined representation. This lets the block combine information from different learned representation subspaces; a head should not automatically be read as a human-defined concept.

Attention mixes information across positions. Position encodings supply order information. A position-wise feed-forward sublayer then transforms each position separately with shared weights. In the original architecture, residual connections wrap each sublayer and layer normalization follows it. Later Transformer variants change these details, so this is a common mechanism, not a specification for every model. See [Attention Is All You Need, §§3.1–3.5](https://arxiv.org/html/1706.03762v7).

For one position, its query scores the permitted keys, and the resulting weights combine the corresponding values. A head is a learned computation whose role can be investigated through behavior. The representation passed onward still has one vector for each position. Stacked blocks pass these vectors to the next block, and the final position supplies the scores used in [next-token generation / 逐词元生成](how-llms-work.md).

For standard dense self-attention, forming pairwise attention scores over a sequence of length \(n\) has quadratic dependence on \(n\). This describes that operation. Total serving cost also depends on feed-forward work, attention variants, hardware, batching, and caching. [Original Transformer, §§3.1–3.5](https://arxiv.org/html/1706.03762v7)
