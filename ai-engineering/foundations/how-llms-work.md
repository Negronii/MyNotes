# How does a language model turn a prompt into text? / 语言模型怎样把一段 prompt 变成文本？

**Short answer / 简答** — A tokenizer maps text to IDs. Embedding lookup gives each ID an initial vector. A stack of causal Transformer blocks mixes information between positions with attention and transforms each position with an FFN. The final vector at the last position scores the vocabulary. A decoding rule chooses the next token, and the loop continues until a stop condition is met. / 分词器把文本转成 ID，嵌入表查找给每个 ID 一个初始向量。多层因果 Transformer 依次用注意力在位置之间传递信息，再用前馈网络变换每个位置的表示。最后一个位置的向量为整个词表打分，解码规则选出下一个词元，重复直到满足停止条件。

以下用一个简化的 **decoder-only Transformer / 仅解码器 Transformer** 跟踪同一批张量。它采用预归一化、因果自注意力和门控 FFN，形状用刻意缩小的例子展示。这是理解一类常见模型的计算图。聊天模板、检索、工具调用和界面流式显示由应用或运行时负责。[从一条消息到完整回答](../systems/from-message-to-answer.md)

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

## How does the tokenizer choose token boundaries? / 分词器怎样决定边界？

Token（词元）是特定词表中的编码单位。它可能是字节、标点、带空格的片段、词的一部分或完整词。下面跟踪 **byte-level BPE / 字节级字节对编码**。一种常见实现先按正则做预分词（pre-tokenization），再对每段的 UTF-8 字节独立做合并。训练分词器时统计相邻对的频率，合并最高频的对并重新统计。部署时词表和优先级已固定，编码器只应用已学到的合并规则。

用三段训练输入 `abab`、`ab`、`ac` 举例。初始词表有 256 个单字节。第一轮相邻对 `a+b` 出现三次，新增 `ab`。训练段变成 `[ab, ab]`、`[ab]`、`[a, c]`。第二轮 `ab+ab` 与 `a+c` 各出现一次，假设固定的同频规则选择先遇到的 `ab+ab`，新增 `abab`。

| 阶段 | 中间状态 |
| --- | --- |
| 已学合并表 | 先 `a+b → ab`，后 `ab+ab → abab` |
| 编码从未见过的 `ababca` | `[a,b,a,b,c,a] → [ab,a,b,c,a] → [ab,ab,c,a] → [abab,c,a]` |
| 查 toy 词表 | 若按合并顺序为新词元编号，结果是 `[257,99,97]` |

真实例子在 `tiktoken` 0.12.0 的 `cl100k_base` 上实测。输入 `The transformer architecture revolutionized NLP.` 得到八个词元 `["The", " transformer", " architecture", " revolution", "ized", " N", "LP", "."]`，ID 是 `[791,43678,18112,14110,1534,452,12852,13]`。空格是其中一些词元的组成部分。不同分词器会给同一段文本不同的切法。工程上要用部署模型的编码器和实际请求格式计数。聊天角色、工具定义、图片等还可能增加服务端处理的输入。字节级词元可以切在 Unicode 字符内部，流式输出要用增量解码或服务端的文本事件，避免把每个词元的字节单独当成完整字符串。

BPE 是一种实现选择。原始 Transformer 的翻译实验也分别使用了 BPE 和 word-piece 词表。子词 BPE 的早期方法见 [Sennrich et al., §3.2](https://aclanthology.org/P16-1162/)，字节级训练、编码和解码见 [tiktoken 0.12.0 教学实现](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken/_educational.py)，原始翻译训练数据见 [Transformer §5.1](https://arxiv.org/html/1706.03762v7#S5.SS1)。

## What enters the first block? / 第一层拿到什么？

令词表大小为 $V$，模型宽度为 $d$，输入长度为 $T$。一条样本的 ID 是长度 $T$ 的整数向量，嵌入表 $E$ 的形状是 $V \times d$。对于第 $i$ 个 ID $t_i$，直接取第 $t_i$ 行 $X_{0,i}=E[t_i,:]$。这在数学上等价于将 one-hot 行向量乘以 $E$，实际实现通常直接取行。$X_0$ 是 $T\times d$，每一行是一个位置的初始表示。把上节的 `[257,99,97]` 送入 toy 模型。它的词表有 256 个字节与两条合并结果，故 $V=258$、$T=3$、$d=8$，$E$ 是 $258\times8$，输入表示是 $3\times8$。批量运行再加上 batch 轴。

同一 token ID 的初始查表向量相同，后续表示还要依赖位置和上下文。原始 Transformer 把正弦位置编码加到输入表示。采用 **RoPE / 旋转位置编码** 的模型在注意力计算前按位置旋转 Q、K 的成对坐标，点积会包含相对位置信息。RoPE 是下面例子采用的路径，它不改变张量形状。 [Transformer §§3.4–3.5](https://arxiv.org/html/1706.03762v7#S3.SS4) · [RoFormer §3](https://arxiv.org/abs/2104.09864) · [Llama 3 论文 §3.2](https://arxiv.org/html/2407.21783v3#S3.SS2)

## How do Q, K, and V produce the attention update? / Q、K、V 怎样产生注意力更新？

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

## What does the FFN add, and how do blocks stack? / FFN 增加了什么，层怎样堆叠？

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

## How does the model choose a token and continue? / 模型怎样选词元并继续？

经过最后一个 block 和模型规定的最终归一化后，取最后一个有效输入位置的向量 $h_{\rm last}$，形状为 $1\times d$。语言模型头（LM head）把它乘以 $W_{\rm lm}$，形状为 $d\times V$，得到 $1\times V$ 个 **logits / 未归一化分数**。权重绑定（weight tying）的模型可用 $E^\top$ 作输出权重。每项分数对应一个词表 ID。这里 $V=258$，得到 258 个分数。训练时也可对每个位置分别投影。

采样时对 logits 应用温度 $\tau>0$，即 $p_i=\exp(z_i/\tau)/\sum_j\exp(z_j/\tau)$。低温度让分布更集中。贪心解码（greedy decoding）直接取最高分。top-k 只留下排名前 $k$ 的候选，top-p（nucleus sampling）保留概率和首次达到阈值 $p$ 的最小降序前缀，再归一化后采样。若约束后四个可选词元的概率为 $[0.50,0.30,0.15,0.05]$，top-p 为 $0.75$ 时留下前两个，重归一化为 $[0.625,0.375]$。采样策略控制输出分布，事实可靠性需要证据和评估。可用控制与组合规则因 API 和模型而异。 [Holtzman et al., §3](https://arxiv.org/abs/1904.09751) · [OpenAI Responses 参数参考](https://developers.openai.com/api/reference/resources/responses/methods/create)

**Prefill / 提示预填充** 处理提示序列，最后一个有效位置的 logits 选出第一个输出 token。之后每轮 **decode / 增量解码** 送入刚选出的 token，得到下一轮 logits。在带 KV cache 的因果模型中，过去位置看不到后来追加的 token，因此同一前缀下过去各层的 K、V 可复用。当前 query 需要给过去的 key 打分并读取对应的 value；过去的 query 已经完成对过去位置的更新，后面的注意力公式不需要它。每轮仍要产生新位置的 Q、K、V，并追加它的 K、V。序列按模型结束词元、应用约定的停止序列或输出长度上限等条件结束。应用层也可以停止转发或取消整个运行。 [Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation)

[GPU 推理服务的显存与调度](../systems/llm-serving-and-kv-cache.md) 延伸这个机制，说明缓存要占多少字节，以及何时需要改进内核、分配或调度。 [上下文工程](../context/context-engineering-principles.md) 说明哪些信息应当进入这段前缀。

## How does next-token training update these parameters? / 下一词元训练怎样更新这些参数？

自回归训练使用同一条前向路径和因果掩码，但目标来自训练数据。在一个训练片段 `[BOS, a, b, c]` 中，位置 `BOS` 的标签是 `a`，位置 `a` 的标签是 `b`，位置 `b` 的标签是 `c`。用当前位置的 logits 对齐下一位置的真实 ID。单次前向可并行计算这些 logits，每个位置仍只能看到自身及之前的 token。**Teacher forcing / 教师强制** 指这里使用真实前缀。推理时则把实际选出的 token 作为后续输入。

对于真实目标 ID $y_i$，每个参与监督的位置使用交叉熵 $-\log p(y_i)$，再按有效标签平均。例如两个目标概率分别为 $0.8$ 和 $0.25$，平均损失约为 $0.805$ nats。单个位置的 logits 梯度为 $p-\operatorname{onehot}(y_i)$。反向传播（backpropagation）用链式法则把这个误差信号传过输出头、每一层的 FFN、注意力投影和嵌入。优化器根据梯度更新可训练参数。冻结参数或只训练适配器是[微调策略](../fine-tuning/fine-tuning-strategies.md)的选择。

这个目标和 **masked language modeling / 掩码语言建模** 不同。BERT 一类双向模型在可见左右上下文中预测选中的缺口，其默认推理目标与逐 token 续写不同。研究可以为掩码模型构造迭代填充采样，但那是另一条生成程序。 [Llama 3 预训练 §3](https://arxiv.org/html/2407.21783#S3) · [PyTorch 交叉熵定义](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html) · [BERT §3.1](https://arxiv.org/abs/1810.04805) · [Wang and Cho, BERT as a Markov Random Field](https://arxiv.org/abs/1902.04094)
