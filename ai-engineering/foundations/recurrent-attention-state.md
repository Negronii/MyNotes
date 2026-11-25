# Kimi Delta Attention（KDA）怎样用固定状态读写历史？

标准 full attention（全注意力）按历史位置保存 key（键，K）和 value（值，V）表示，当前 query（查询，Q）再对可见位置打分并混合 value。为说明一次位置级读取，先看一个 attention head（注意力头）。Kimi Delta Attention（KDA）改用 linear attention（线性注意力）的递归状态：每个头维护一张固定形状的矩阵，让当前 key 检查已有的 key–value 关联，再按当前 value 修正状态，最后由 query 从更新后的矩阵读出结果。

本章沿着一个词元解释状态矩阵的读、写和遗忘，也说明它与按块保留可检索摘要的区别。“固定大小”只描述单个 KDA 头的主要矩阵不随历史长度增加。Kimi Linear 是混合架构，其他 MLA 层仍保留逐位置状态，KDA 层也有 short convolution（短卷积）状态。prefill（提示预填充）的分块计算还会产生临时张量。

## 逐位置 KV 缓存与递归状态保存的历史不同

对全注意力，一个头在处理位置 $t$ 时要读取前缀中所有可见的 K、V。因果可见范围 $s\le t$ 已写入求和上下限。使用标准的 $1/\sqrt{d_k}$ 缩放，输出可写为

$$
o_t=\sum_{s=1}^{t}\operatorname{softmax}_{s}
\left(\frac{q_t^\top k_s}{\sqrt{d_k}}\right)v_s.
$$

softmax（归一化指数函数）把各位置的分数变成和为 $1$ 的权重，再用这些权重混合 value。推理时，每来一个新词元，就把本层投影算出的 K、V 追加到缓存。旧位置的条目仍在原处，后来的 query 可以重新给每个位置打分。Q、K、V 的来源和注意力加权过程见[语言模型如何把提示词变成文本？](how-llms-work.md#Q%E3%80%81K%E3%80%81V%20%E5%A6%82%E4%BD%95%E7%94%9F%E6%88%90%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9B%B4%E6%96%B0%EF%BC%9F)。

怎样把这种按位置读取改成固定大小的状态？先看一个更简单的线性例子。假设不用 softmax，位置 $s$ 的权重就是点积 $q_t^\top k_s$，那么求和可以换个次序：$\sum_{s\le t}(q_t^\top k_s)v_s=(\sum_{s\le t}k_s v_s^\top)^\top q_t$。括号里的矩阵与这次的 query 无关，每来一个词元只需加上它的外积，下次就能直接用矩阵回答新的 query。KDA 沿用“先更新矩阵、再用 query 读”的思路，并让新词元有选择地衰减和修正旧关联。

KDA 不为每个历史位置保留完整 K、V 序列。每个层、每个头分别维护一张状态矩阵 $S_t\in\mathbb{R}^{d_k\times d_v}$。它的行对应 key 特征坐标，列对应 value 特征坐标。用一个 key 向量乘这张矩阵，可以得到状态当前会为这个 key 产生的 value 向量。矩阵维度由模型配置决定，和已经处理了多少词元无关。

每个新词元仍会即时算出自己的 query、key 和 value。它们由当前层的 hidden state（隐藏状态）按模型学到的投影产生。在引用的 Kimi Transformers 实现中，三个投影结果先分别经过带 SiLU 激活的短卷积，递归 kernel 再对 query 与 key 做 L2 归一化。下文把读出时的缩放系数并入 $q_t$；二维算例直接指定这个有效 query。参考 kernel 对归一化后的 query 默认再乘 $d_k^{-1/2}$。KDA 用 key 更新历史状态，用 query 读取结果。完成递归更新后，当前 key 和 value 无须作为一整行长期追加到 KDA 的历史 KV 表中。

## 当前 key 怎样检查并修正状态？

先看单个头。令当前 key、query 和 value 分别为 $k_t,q_t\in\mathbb{R}^{d_k}$ 与 $v_t\in\mathbb{R}^{d_v}$。$d_k$ 和 $d_v$ 分别是一个 key 向量和 value 向量的坐标数。状态 $S_{t-1}$ 表示处理当前词元之前的历史关联。KDA 按以下顺序更新：

$$
\begin{aligned}
\widetilde S_t &= \operatorname{diag}(\alpha_t)S_{t-1},\\
\widehat v_t &= \widetilde S_t^\top k_t,\\
e_t &= v_t-\widehat v_t,\\
S_t &= \widetilde S_t+\beta_t k_t e_t^\top,\\
o_t &= S_t^\top q_t.
\end{aligned}
$$

$\alpha_t\in[0,1]^{d_k}$ 是按 key 通道生成的保留门。$\operatorname{diag}(\alpha_t)$ 把每个通道的门值放到对角线上，逐行缩放旧状态。接近 $1$ 的通道保留较多旧关联，较小的值让对应通道衰减得更多。$\beta_t\in[0,1]$ 是当前头的写入强度。$k_t$ 用来检查状态对当前输入会预测出什么 value，误差 $e_t$ 指出要修正的方向。外积 $k_t e_t^\top$ 把这次修正写回与当前 key 相关的状态方向。最后，query $q_t$ 从更新后的状态读出核心每头结果 $o_t$。Kimi Linear 的完整输出在此之后还会经过 RMSNorm、数据相关门控与输出投影。

这里的 $S_t$ 是当前词元处理后留给下一位置的 KDA 运行时状态。$h_t$ 是当前层接收、用于产生注意力投影的词元表示。FFN 接收注意力更新后的残差表示。$o_t$ 是 KDA 产生的每头表示。它们都属于前向激活，不是词表概率。模型要等到最后一层和 language model head（语言模型头，LM head）产生词表 logits，再经 softmax 才得到下一词元的概率分布。

## 二维例子怎样经过一次写入？

下例选择两维 key 和两维 value，手算状态变化。它只为演示矩阵运算，不是模型参数或实测词元表示。设旧状态、当前向量和两个门值为

$$
S_0=\begin{bmatrix}2&0\\4&6\end{bmatrix},\quad
k=\begin{bmatrix}1\\0\end{bmatrix},\quad
v=\begin{bmatrix}3\\1\end{bmatrix},\quad
\alpha=\begin{bmatrix}0.5\\1\end{bmatrix},\quad
\beta=0.5.
$$

逐步计算如下。

| 步骤 | 计算 | 结果 |
| --- | --- | --- |
| 衰减旧状态 | $\widetilde S=\operatorname{diag}(\alpha)S_0$ | $\begin{bmatrix}1&0\\4&6\end{bmatrix}$ |
| 用 key 预测 value | $\widehat v=\widetilde S^\top k$ | $\begin{bmatrix}1\\0\end{bmatrix}$ |
| 计算误差 | $e=v-\widehat v$ | $\begin{bmatrix}2\\1\end{bmatrix}$ |
| 形成本次写入 | $\beta k e^\top$ | $\begin{bmatrix}1&0.5\\0&0\end{bmatrix}$ |
| 得到新状态 | $S_1=\widetilde S+\beta k e^\top$ | $\begin{bmatrix}2&0.5\\4&6\end{bmatrix}$ |

若本次 query 取 $q=[1,0]^\top$，从更新后的状态读到

$$
o=S_1^\top q=\begin{bmatrix}2\\0.5\end{bmatrix}.
$$

本例的 key 是单位向量，且 query 与 key 相同。写入强度 $\beta=0.5$ 使同一 key 重读时把预测沿误差方向修正一半，从 $[1,0]^\top$ 移到 $[2,0.5]^\top$。这里第一行是第一个 key 坐标对应的 value 关联，不代表第一个历史词元。状态中没有 token 位置索引可供回查。

## 为什么它像一步梯度更新？

把衰减后的状态看成一组待修正的 key–value 映射。对当前 key 和 value 定义局部重建误差

$$
\ell(\widetilde S_t)=\frac12\left\|\widetilde S_t^\top k_t-v_t\right\|_2^2.
$$

对 $\widetilde S_t$ 求梯度可得

$$
\nabla_{\widetilde S_t}\ell
=k_t(\widetilde S_t^\top k_t-v_t)^\top
=-k_t e_t^\top.
$$

因此 $S_t=\widetilde S_t-\beta_t\nabla_{\widetilde S_t}\ell$，正好得到上面的状态更新。这个类比只说明推理状态沿当前样本的误差方向做了一步在线修正。每步前向时改变的是激活状态 $S_t$，训练好的投影矩阵保持不变，也没有对模型权重执行反向传播。

## 衰减与秩一写入怎样形成 DPLR 结构？

令 $D_t=\operatorname{diag}(\alpha_t)$。将误差 $e_t=v_t-(D_tS_{t-1})^\top k_t$ 代入写入式，并利用 $D_t$ 为对角矩阵，可改写为

$$
\begin{aligned}
S_t &= D_tS_{t-1}+\beta_t k_t\bigl(v_t-S_{t-1}^\top D_tk_t\bigr)^\top\\
&=\bigl[D_t-\beta_t k_t(D_tk_t)^\top\bigr]S_{t-1}+\beta_t k_tv_t^\top.
\end{aligned}
$$

状态转移矩阵由对角衰减 $D_t$ 与一个秩一项 $-\beta_t k_t(D_tk_t)^\top$ 组成，写入项 $\beta_t k_tv_t^\top$ 也采用秩一外积形式。这种 diagonal-plus-low-rank（对角加低秩，DPLR）结构来自逐通道门控与 delta-rule 误差写入，chunkwise kernel 利用它把同一递归展开为并行矩阵运算。

## 这张矩阵能保留什么？

状态矩阵叠加了多次更新形成的 key–value 关联。后续 query 可以读取这些关联的线性组合。若几个 key 的表示方向相近，它们的更新可能互相干扰。新的写入会改变有限维状态，小于 $1$ 的保留门也会衰减相应行。误差 $e_t$ 衡量当前 key–value 配对在当前状态下的预测差距，公式没有定义一项跨所有 key 汇总的“已记住多少”指标。

全注意力按位置保留 K/V，query 可以对每个可见位置分别打分。CSA/HCA 与 MemOnce 将历史位置合并成压缩条目或记忆段，读取单位是摘要条目或被选中的段。KDA 把历史关联写入固定矩阵，query 读出其中的组合表示。三种表示能保留和取回的信息取决于模型表示与读取路径，见下文对照。

## 固定状态怎样改变每步成本？

单头状态矩阵含 $d_kd_v$ 个数值。每个 token 的逐通道衰减、key 读出和外积写入都与这张固定矩阵计算，因此递归路径的状态容量和单步算量不随历史长度 $T$ 增长。作为对照，全注意力每头要保留 $T(d_k+d_v)$ 个历史 K、V 坐标，decode（增量解码）时还要对可见位置重新打分并混合 value。具体服务容量还会受层数、头数、精度、缓存实现和并发请求影响，工程容量计算见[KV 缓存与调度怎样决定大语言模型的服务容量？](../systems/llm-serving-and-kv-cache.md)。

Kimi Linear 论文采用约 3:1 的 KDA 与 Multi-Head Latent Attention（多头潜注意力，MLA）层组合。KDA 层除递归矩阵外仍有短卷积状态，MLA 层仍按历史位置保留注意力缓存。引用的 Transformers 参考实现把展开后的 key 与 value 逐位置写入 `past_key_values`。因此，单个 KDA 矩阵固定大小，不代表整个混合模型的全部缓存与运行时内存固定。

## 分块怎样加速同一递归计算？

逐 token 解码天然按顺序把 $S_{t-1}$ 更新为 $S_t$。提示预填充包含许多位置，若每个位置都串行等待上一状态，会限制图形处理器（GPU）的并行度。Kimi 的 chunkwise（分块）KDA 将一段位置拆成 chunk，把前述状态转移组合成满足因果约束的矩阵运算，并行求出块内各位置的输出以及块末状态：

$$
\begin{aligned}
(S_{\text{before}},Q,K,V,\alpha,\beta)_{\text{本块}}
&\xrightarrow{\text{chunkwise 因果计算}}
(O_{\text{chunk}},S_{\text{after}}),\\
O_{\text{chunk}}
&\xrightarrow{\text{第 }\ell\text{ 层后续计算}}
H_{\text{chunk}}^{(\ell+1)},\\
S_{\text{after}}
&\xrightarrow{\text{下一 chunk}}
S_{\text{next-before}}.
\end{aligned}
$$

块内每个位置只使用入块状态和同块中不晚于它的位置，矩阵运算遵守因果三角结构。$O_{\text{chunk}}$ 是递归 kernel 的每头输出，经过归一化、门控和输出投影合并进残差流，再经该层的前馈子层更新，形成送给下一层的词元表示 $H_{\text{chunk}}^{(\ell+1)}$。对递归 kernel，传给下一块的是 $S_{\text{after}}$。分块保留了同一递归的结果，同时允许 GPU 并行计算块内多个位置。块内的 Q、K、V 和中间乘积属于临时工作区。该 Transformers 参考实现按本次调用的 query 长度选择路径，长度不超过 64 时使用融合递归 kernel，更长时使用分块 kernel。

## 门控坐标与 NoPE 怎样理解？

这里的 feature（特征）是模型学出的向量坐标方向，不是预先定义的词义类别。对单个头，可把 Kimi Linear 论文的门控路径概括为

$$
g_t^\alpha=W_\alpha^\uparrow W_\alpha^\downarrow h_t,\qquad
\alpha_t=f_\alpha(g_t^\alpha),\qquad
\beta_t^h=\sigma\!\left((W_\beta^h)^\top h_t\right).
$$

$h_t$ 是当前层输入。训练参数 $W_\alpha^\downarrow$ 先把它投影到较窄的中间表示，$W_\alpha^\uparrow$ 再把该表示映射到每个 key 通道的门控输入。$f_\alpha$ 使用该版本的衰减变换，输出逐 key 通道的 $\alpha_t$。Kimi Linear 的论文以低秩双投影表示该门控路径，参考代码还把对数步长参数和偏置送入衰减变换。$W_\beta^h$ 对当前隐藏状态产生第 $h$ 个头的门控 logit，经 sigmoid 后成为该 token 的标量 $\beta_t^h$。这些 $W$ 是训练得到的模型参数。每步产生的 $\alpha_t$ 和 $\beta_t^h$ 是随输入变化的运行时激活。

NoPE 是 No Positional Encoding（不显式加位置编码）。Kimi Linear 论文把 NoPE 用于混合架构中的全局 MLA 层，描述该支路怎样处理显式位置编码。模型整体仍利用顺序信息，因为 KDA 按 token 顺序递归更新，短卷积也读取相邻位置。改变输入顺序通常会改变递归状态。

具体门控生成方式与层组合要按模型版本阅读。

| 模型资料 | 门控与层组合 | 适用范围 |
| --- | --- | --- |
| Kimi Linear 论文 v2 | $\alpha$ 的每通道门控由低秩的 $W_\alpha^\downarrow$ 与 $W_\alpha^\uparrow$ 路径生成，整体采用约 3 层 KDA 配 1 层 MLA | 论文中的 Kimi Linear 架构 |
| Kimi K3 技术报告 v2 | 报告给出 log-decay（对数衰减）下界 $g_{\min}=-5$，层组合为 69 个 KDA 与 24 个 Gated MLA | K3 报告配置 |
| Kimi K3.1 Pro 当前模型卡与配置 | 卡片写明 69 个 KDA 与 24 个 Gated DSA，配置仍有 $\texttt{gate\_lower\_bound}=-5.0$，模型卡说明 Gated DSA 取代 K3 中的 Gated MLA | 当前 Pro 发布快照，2026-11-25 核对 |

K3 报告的衰减门满足 $\alpha_t=\exp(g_t)$，因此 $g_{\min}=-5$ 对应的最低保留系数约为 $e^{-5}\approx0.0067$。每个通道实际保留多少，取决于当前输入算出的 $\alpha_t$；状态更新用的是这个实际值。

## KDA、CSA/HCA 与 MemOnce 怎样保存不同的历史状态？

下表比较的是长历史状态的形状和读取方式。DeepSeek-V4 的公式与容量核算见[长上下文 Attention 怎样节省存储与读取？](long-context-attention.md)。

| 设计 | 长历史状态 | 当前 query 的读取单位 | 长历史状态是否随输入增长 |
| --- | --- | --- | --- |
| 全注意力 KV cache | 每个位置保存 K、V | 可见的历史 token 位置 | 随位置数增长 |
| KDA | 每层、每头一张固定形状的 $S_t$ 矩阵 | 从矩阵读出与 query 匹配的关联，没有 token 位置 ID | 矩阵本身不随位置数增长 |
| DeepSeek-V4 预览版 Compressed Sparse Attention（压缩稀疏注意力，CSA）与 Heavily Compressed Attention（重度压缩注意力，HCA） | 每 4 或 128 个位置产生一条压缩 KV 摘要，另保留局部窗口 | CSA 选摘要 ID 后读取，HCA 读取所有已完成摘要 | 摘要条目数随输入增长 |
| MemOnce | 每 512 个输入 token 保存一段 64 个末层 hidden states，完整记忆池随历史增长并可卸载到主机内存或 SSD（固态硬盘） | 每次新交互检索一次。各全注意力层用同一批选中状态分别生成自己的 K/V，后续生成复用各层的缓存 | 全量记忆池随历史增长，GPU 活动集受窗口与检索条数限制 |

MemOnce 为每个历史段保留末尾一组隐状态，把最后一个状态投影成一个索引向量。新输入先结合近期窗口算出自己的检索向量，与池中各段索引做内积，挑出相关的远端段，按原有时间顺序接回近期窗口。这样，第一次检索就有 query 可用，各全注意力层也能从同一批选中状态生成自己的 KV。随着档案变大，索引和检索开销仍会增长。

MemOnce 论文 v1 在 Qwen3.5-4B 适配配置中，每 512 个原始 token 取末层的 64 个 hidden states，也就是压缩率 $r=8$。长期检索的 top-K（取相似度最高的 K 段）为 64 时，选中的是 64 段记忆，每段含 64 个状态向量，共 4,096 个向量。GPU 活动集还保留 1,024 个近期压缩状态。以每个状态 2,560 个坐标、每个数 2 字节计算，活动状态占用 $(4{,}096+1{,}024)\times2{,}560\times2=26{,}214{,}400$ 字节，即 25 MiB。论文附录表 14 将它记为 25 MB 的活动记忆缓存，另报告 1M token 场景有 640 MB 的 CPU/SSD 卸载记忆池。附录 B.1 另报告 4 MB 的索引向量矩阵常驻 GPU。这是作者报告的研究原型结果。论文的从头预训练最高到 1B 参数，长时交互编程、多步工具使用仍待验证。模型权重、逐层解码的 KV、索引矩阵与临时工作区仍按各自口径纳入运行内存核算。

KDA 把历史压进每个头的固定映射状态。CSA/HCA 保留可寻址的压缩条目，MemOnce 保留可检索的隐藏状态段并按需还原层级 KV。三者的容量随长度变化规律、可检索粒度和更新方式不同。应用是否保留跨运行记忆仍由上下文与记忆系统决定，见[什么时候值得把历史加工成 Agent 记忆？](../context/agent-memory-design-and-evaluation.md)。

> [!info]- 来源
> - **KDA 的状态更新、分块计算与混合层。** Kimi Team, *Kimi Linear: An Expressive, Efficient Attention Architecture*, arXiv v2（2025-11-01），§2.2 介绍在线 delta rule，§3、§3.1 给出 KDA 更新与 chunkwise 算法，§4 给出门控参数化、混合结构与 NoPE，§6.2 讨论 DPLR，Appendix B 推导 chunkwise 并行形式，Appendix C 给出伪代码，[原文](https://arxiv.org/html/2510.26692v2)。
> - **Q/K/V 短卷积、L2 归一化与计算路径。** Kimi Linear 官方 Transformers 文件 [modeling_kimi.py](https://huggingface.co/moonshotai/Kimi-Linear-48B-A3B-Instruct/blob/d64a5299ded33ab2609617e05f6bd2cf9b6eef35/modeling_kimi.py)，固定提交 d64a5299ded33ab2609617e05f6bd2cf9b6eef35，核对日期 2026-11-25。该文件按本次调用的 $q\_len$ 选择递归或分块 kernel，并在 cache 中保存短卷积与递归状态。[FLA 的递归实现](https://github.com/fla-org/flash-linear-attention/blob/93734255a9e38a2ac1533132998d5b5ce9b160dc/fla/ops/kda/fused_recurrent.py#L465-L474)给出 query 默认读出缩放。
> - **Kimi K3 的衰减门与层数。** Kimi Team, *Kimi K3: Open Frontier Intelligence*, arXiv v2（2026-08-07），§2.1.1 的 lower-bounded decay，§2.1.2 与 Figure 2 的层组合，[原文](https://arxiv.org/html/2607.24653v2)。
> - **Kimi K3.1 Pro 的层组合与当前配置。** Moonshot AI, [Kimi K3.1 Pro model card](https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/80aff651e9b2d2f5b9f70f92a0a7a77054418e16/README.md) 与 [config.json](https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/80aff651e9b2d2f5b9f70f92a0a7a77054418e16/config.json)，固定 Hub revision 80aff651e9b2d2f5b9f70f92a0a7a77054418e16，检查日期 2026-11-25。
> - **DeepSeek-V4 预览版的压缩率、可读摘要与局部窗口。** DeepSeek Team, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*, arXiv v1（2026-04-26），§2.3，[原文](https://arxiv.org/html/2606.19348v1)。本章的层配置和容量核算见[长上下文 Attention 章节](long-context-attention.md)。
> - **MemOnce 的分段、按需解码、存储核算与实验范围。** Nie et al., *MemOnce: A Scalable Memory Architecture for Large Language Models*, arXiv v1（2026-11-20），§3.1、§3.2、§4.1–4.2，Appendix B.1 的记忆占用与索引矩阵、Appendix E.3 的 top-K 检索预算，Appendix F.4 Table 14 的 1M-token 活动缓存和卸载池数据，以及 Limitations 中的研究范围，[原文](https://arxiv.org/html/2611.27973v1)。
