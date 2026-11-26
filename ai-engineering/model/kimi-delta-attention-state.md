# Kimi Delta Attention 怎样用一张固定矩阵读写历史？

标准 full attention（全注意力）为每个历史位置保存一条 key（K）和 value（V），当前 query（Q）再对所有可见位置打分、混合 value，所以缓存随历史长度增长。Kimi Delta Attention（KDA）是 Kimi Linear 架构里的一种 linear attention（线性注意力）层：每个 attention head（注意力头）只维护一张固定形状的矩阵，新词元先用 key 检查矩阵已有的关联，按误差修正它，再由 query 从修正后的矩阵读出结果。本章沿着一个词元讲清这张矩阵怎样读、写、遗忘，它为什么能并行计算，以及它记住什么、丢掉什么。读者需要的输入是 Q/K/V 和 KV 缓存的基本概念（见[模型怎样把提示词算成下一个词元？](next-token-computation.md)）。

“固定大小”只描述单个 KDA 头的主状态矩阵不随历史变长。Kimi Linear 是混合架构，其中的 MLA 层仍逐位置保存缓存，KDA 层也还有 short convolution（短卷积）状态，prefill（提示预填充）的分块计算还会产生临时张量；这些在“[每步成本固定，整个模型的内存也固定吗？](#每步成本固定，整个模型的内存也固定吗？)”一节一起核算。本章沿用 Kimi 论文的列向量写法。

## 怎样把按位置读取换成一张矩阵？

全注意力的一个头在位置 $t$ 的输出是

$$
o_t=\sum_{s=1}^{t}\operatorname{softmax}_{s}
\left(\frac{q_t^\top k_s}{\sqrt{d_k}}\right)v_s .
$$

softmax（归一化指数函数）把各位置的分数变成和为 1 的权重，再用权重混合 value。每来一个新词元，就把它的 K、V 追加进缓存；旧条目留在原处，后来的 query 可以重新给每个位置打分。

现在去掉 softmax，假设位置 $s$ 的权重就是点积 $q_t^\top k_s$。求和就能换个次序：

$$
\sum_{s\le t}(q_t^\top k_s)\,v_s=\Bigl(\sum_{s\le t}k_s v_s^\top\Bigr)^{\!\top} q_t .
$$

> [!info] 外积和换序的小例子
> 外积 $k v^\top$ 是一个 $d_k\times d_v$ 矩阵，第 $(i,j)$ 项为 $k_iv_j$。等式成立是因为 $(k_sv_s^\top)^\top q=v_s(k_s^\top q)$，标量 $k_s^\top q$ 可以挪到向量前面。
>
> 取两个历史位置 $k_1=[1,0]^\top,v_1=[3,1]^\top$ 和 $k_2=[0,1]^\top,v_2=[0,2]^\top$，查询 $q=[1,1]^\top$。逐位置算：$1\cdot[3,1]+1\cdot[0,2]=[3,3]$。先累加矩阵：$M=k_1v_1^\top+k_2v_2^\top=\begin{bmatrix}3&1\\0&2\end{bmatrix}$，$M^\top q=[3,3]^\top$。结果相同，但第二种只需保存一张 $2\times2$ 矩阵。

括号里的矩阵与本次 query 无关。每来一个词元只要加上它的外积，下一个 query 就能直接从矩阵读出答案，不再回看各个位置。KDA 沿用“先更新矩阵、再用 query 读”的做法，但不是简单累加：它让新词元有选择地衰减旧关联，并只写入预测误差。

于是每层每个头只维护一张状态矩阵 $S_t\in\mathbb{R}^{d_k\times d_v}$。行对应 key 的特征坐标，列对应 value 的特征坐标；一个 key 向量乘这张矩阵，得到状态当前为这个 key 给出的 value。矩阵的形状由模型配置决定，与已处理多少词元无关。

## KDA 怎样读、写和遗忘？

每个新词元仍即时算出自己的 $q_t,k_t\in\mathbb{R}^{d_k}$ 和 $v_t\in\mathbb{R}^{d_v}$，来源是当前层 hidden state（隐藏状态）$h_t$ 的学习投影。在 Kimi Linear 的 Transformers 实现里，三个投影结果先各经过一个带 SiLU 激活的短卷积，递归 kernel 再对 query 和 key 做 L2 归一化；参考 kernel 默认还给归一化后的 query 乘 $d_k^{-1/2}$，下文把这个缩放并入 $q_t$。

$S_{t-1}$ 是处理当前词元之前的状态。一个头的更新分五步：

$$
\begin{aligned}
\widetilde S_t &= \operatorname{diag}(\alpha_t)\,S_{t-1} &&\text{遗忘：逐行衰减旧状态}\\
\widehat v_t &= \widetilde S_t^\top k_t &&\text{检查：状态对当前 key 预测出的 value}\\
e_t &= v_t-\widehat v_t &&\text{误差：预测差多少}\\
S_t &= \widetilde S_t+\beta_t\,k_t e_t^\top &&\text{写入：沿当前 key 方向修正}\\
o_t &= S_t^\top q_t &&\text{读取：query 从新状态读出}
\end{aligned}
$$

- $\alpha_t\in[0,1]^{d_k}$ 是按 key 通道生成的保留门。$\operatorname{diag}(\alpha_t)$ 把门值放到对角线上，逐行缩放旧状态：接近 1 的通道保留较多旧关联，小的值让对应行衰减更多。
- $\beta_t\in[0,1]$ 是当前头的写入强度。
- 外积 $k_te_t^\top$ 把修正写回与当前 key 相关的行。如果状态已经能为 $k_t$ 给出 $v_t$，误差为零，什么也不写；这就是 delta rule（增量规则）名字的来由。
- $o_t$ 是核心的每头输出。Kimi Linear 之后还会经过 RMSNorm、数据相关的输出门和输出投影，再合并进残差流。

$S_t$ 是留给下一位置的运行时状态。$h_t$、$o_t$ 都是前向激活，不是词表概率；要等最后一层经 LM head 产生 logits、再经 softmax，才得到下一词元的分布。完成这次更新后，当前的 key 和 value 不必作为一行追加到任何历史表里。

## 二维例子：一次写入怎样改变状态？

下面用两维 key 和两维 value 手算一次更新。数值是教学选择，不是模型参数或真实词元表示。

$$
S_0=\begin{bmatrix}2&0\\4&6\end{bmatrix},\quad
k=\begin{bmatrix}1\\0\end{bmatrix},\quad
v=\begin{bmatrix}3\\1\end{bmatrix},\quad
\alpha=\begin{bmatrix}0.5\\1\end{bmatrix},\quad
\beta=0.5.
$$

| 步骤 | 计算 | 结果 |
| --- | --- | --- |
| 衰减旧状态 | $\widetilde S=\operatorname{diag}(\alpha)S_0$ | $\begin{bmatrix}1&0\\4&6\end{bmatrix}$ |
| 用 key 预测 value | $\widehat v=\widetilde S^\top k$ | $\begin{bmatrix}1\\0\end{bmatrix}$ |
| 计算误差 | $e=v-\widehat v$ | $\begin{bmatrix}2\\1\end{bmatrix}$ |
| 形成本次写入 | $\beta k e^\top$ | $\begin{bmatrix}1&0.5\\0&0\end{bmatrix}$ |
| 得到新状态 | $S_1=\widetilde S+\beta k e^\top$ | $\begin{bmatrix}2&0.5\\4&6\end{bmatrix}$ |

本次 query 取 $q=[1,0]^\top$，读到 $o=S_1^\top q=[2,0.5]^\top$。

key 是单位向量、query 与 key 相同，所以读出的正是第一行。写入强度 $\beta=0.5$ 让预测沿误差方向走了一半：从 $[1,0]^\top$ 移到 $[2,0.5]^\top$，目标是 $[3,1]^\top$。换两个条件对比：

- $\beta=1$ 时写入 $ke^\top$，新状态第一行变成 $[3,1]$，重读恰好得到 $v$。
- 如果像前一节那样纯累加 $\widetilde S+kv^\top$，第一行变成 $[4,1]$，重读得到 $[4,1]^\top$，冲过了目标。delta rule 只写误差，避免同一个 key 反复写入时无限叠加。

第一行是“第一个 key 坐标对应的 value 关联”，不是第一个历史词元。状态里没有词元位置索引可以回查。

## 为什么这次写入像一步梯度下降？

把衰减后的状态看成一个待修正的 key→value 映射，对当前这一对 key、value 定义局部重建误差

$$
\ell(\widetilde S_t)=\frac12\bigl\|\widetilde S_t^\top k_t-v_t\bigr\|_2^2 .
$$

> [!info] 对矩阵求一次梯度
> 令残差 $r=\widetilde S_t^\top k_t-v_t\in\mathbb{R}^{d_v}$，它的第 $j$ 个分量是 $r_j=\sum_i \widetilde S_{ij}k_i-v_j$，损失 $\ell=\frac12\sum_j r_j^2$。矩阵元素 $\widetilde S_{ij}$ 只出现在 $r_j$ 里，且系数是 $k_i$，所以
>
> $$
> \frac{\partial \ell}{\partial \widetilde S_{ij}}=r_j\,k_i .
> $$
>
> 把所有 $(i,j)$ 排成矩阵，第 $(i,j)$ 项为 $k_ir_j$，正是外积 $k_tr^\top$。

因为 $r=-e_t$，梯度是

$$
\nabla_{\widetilde S_t}\ell=k_t\bigl(\widetilde S_t^\top k_t-v_t\bigr)^\top=-k_te_t^\top ,
$$

于是 $S_t=\widetilde S_t-\beta_t\nabla_{\widetilde S_t}\ell$：KDA 的写入就是以 $\beta_t$ 为步长、在局部误差上走一步梯度下降。用二维例子核对：$r=[1,0]^\top-[3,1]^\top=[-2,-1]^\top$，梯度 $kr^\top=\begin{bmatrix}-2&-1\\0&0\end{bmatrix}$，$\widetilde S-0.5\times$梯度$=\begin{bmatrix}2&0.5\\4&6\end{bmatrix}=S_1$。因为 $k$ 只有第一个坐标非零，梯度也只落在第一行。

这个类比只说明推理状态沿当前样本的误差方向做了一步在线修正。每步前向改变的是激活状态 $S_t$；训练好的投影矩阵不变，也没有对模型权重做反向传播。训练怎样更新权重是另一回事，见[训练怎样让这些参数变得更会预测？](how-training-updates-parameters.md)。

## 衰减和误差写入怎样组成可并行的 DPLR 结构？

逐词元 decode（增量解码）天然按顺序把 $S_{t-1}$ 更新成 $S_t$。但 prefill 有成千上万个位置，若每个都串行等上一个状态，GPU 的并行度会被浪费。能否把同一递归改写成矩阵运算，取决于状态转移的结构。

令 $D_t=\operatorname{diag}(\alpha_t)$，把误差 $e_t=v_t-(D_tS_{t-1})^\top k_t$ 代入写入式。因为 $D_t$ 是对角矩阵，$D_t^\top=D_t$：

$$
\begin{aligned}
S_t &= D_tS_{t-1}+\beta_t k_t\bigl(v_t-S_{t-1}^\top D_tk_t\bigr)^\top\\
&=\bigl[D_t-\beta_t k_t(D_tk_t)^\top\bigr]S_{t-1}+\beta_t k_tv_t^\top .
\end{aligned}
$$

状态转移矩阵是对角衰减 $D_t$ 加一个秩一项 $-\beta_tk_t(D_tk_t)^\top$，写入项 $\beta_tk_tv_t^\top$ 也是秩一外积。这种 diagonal-plus-low-rank（对角加低秩，DPLR）结构来自逐通道门控加 delta rule 写入。

Kimi 的 chunkwise（分块）KDA 利用这一结构，把一段位置切成若干 chunk，在块内把连续的状态转移组合成满足因果约束的矩阵运算，并行求出块内各位置的输出和块末状态：

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
S_{\text{next-before}} .
\end{aligned}
$$

块内每个位置只用入块状态和同块中不晚于它的位置，矩阵运算保持因果三角结构。$O_{\text{chunk}}$ 经归一化、门控、输出投影并进残差流，再经本层前馈子层，成为送往下一层的表示 $H_{\text{chunk}}^{(\ell+1)}$；传给下一块的只有 $S_{\text{after}}$。分块得到与逐步递归相同的结果，块内的 Q、K、V 和中间乘积只是临时工作区。Transformers 参考实现按本次调用的 query 长度选路径：不超过 64 时用融合的递归 kernel，更长时用分块 kernel。

## 这张矩阵能记住什么、会丢什么？

状态矩阵叠加了多次更新留下的 key–value 关联，后续 query 读到的是这些关联的线性组合。由此可以推出它的三种损失：

- **干扰**：几个 key 的方向相近时，它们的写入落在相近的行组合上，会互相覆盖。二维例子里，若下一个词元的 key 也是 $[1,0]^\top$ 而 value 不同，它会把第一行改向新 value。
- **衰减**：小于 1 的保留门持续缩小对应行，旧关联逐渐淡出。
- **容量**：$d_k\times d_v$ 个数要承载全部历史。$d_k$ 维空间里至多有 $d_k$ 个互相正交的 key，只有它们的写入彼此完全不干扰；历史词元远多于 $d_k$ 时，关联必然叠在一起。

误差 $e_t$ 只衡量当前这对 key、value 在当前状态下的预测差距；公式里没有一项能汇总“总共记住了多少”。

和其他历史表示比，取回的单位不同：全注意力按位置保留 K/V，query 可以对每个可见位置单独打分；压缩摘要和分段记忆把位置合并成条目或段，读取单位是被选中的条目；KDA 只有一张矩阵，query 读出的是组合后的关联，没有“回到第 $s$ 个词元”这种操作。它们各自能保留什么，取决于模型学到的表示和读取路径，最后一节并排对照。

## 每步成本固定，整个模型的内存也固定吗？

单头状态矩阵含 $d_kd_v$ 个数。每个词元的逐通道衰减、key 读出和外积写入都只和这张矩阵运算，所以递归路径的状态大小和单步计算量不随历史长度 $T$ 增长。全注意力每头要保留 $T(d_k+d_v)$ 个历史坐标，decode 时还要对所有可见位置打分。

以教学取值 $d_k=d_v=128$ 为例：KDA 一个头的矩阵是 16,384 个数；全注意力一个头存 $256T$ 个数，$T=64$ 时就与之持平，$T=8{,}192$ 时是它的 128 倍。真实服务容量还取决于层数、头数、精度、缓存实现和并发，核算方法见[KV 缓存怎样决定一台服务能接多少请求？](kv-cache-and-serving-capacity.md)。

但“单个 KDA 矩阵固定”不等于整个模型的内存固定：

- Kimi Linear 论文采用约 3:1 的 KDA 与 Multi-Head Latent Attention（多头潜注意力，MLA）层组合。MLA 层仍按历史位置保留缓存，引用的 Transformers 参考实现把展开后的 key 和 value 逐位置写入 `past_key_values`。MLA 的缓存形状见[DeepSeek 怎样压缩长上下文的注意力状态？](deepseek-compressed-attention.md)。
- KDA 层除了递归矩阵，还缓存短卷积的状态。
- prefill 的分块计算需要临时工作区。

所以混合模型的缓存仍随长度增长，只是增长的那部分只来自少数全局层。

## 门控和 NoPE 怎样理解？

这里的 feature（特征）是模型学出的向量坐标方向，不是预先定义的词义类别。单个头的门控路径在 Kimi Linear 论文里可以概括为

$$
g_t^\alpha=W_\alpha^\uparrow W_\alpha^\downarrow h_t,\qquad
\alpha_t=f_\alpha(g_t^\alpha),\qquad
\beta_t^h=\sigma\!\left((W_\beta^h)^\top h_t\right).
$$

$W_\alpha^\downarrow$ 先把当前层输入 $h_t$ 投影到较窄的中间表示，$W_\alpha^\uparrow$ 再映射到每个 key 通道的门控输入。$f_\alpha$ 是该版本的衰减变换，输出逐通道的 $\alpha_t$；参考代码还把对数步长参数和偏置送入这个变换。$W_\beta^h$ 为第 $h$ 个头产生门控 logit，经 sigmoid 成为该词元的标量 $\beta_t^h$。这些 $W$ 是训练得到的参数，每步的 $\alpha_t$、$\beta_t^h$ 是随输入变化的激活。

NoPE 指 No Positional Encoding（不显式加位置编码）。Kimi Linear 把 NoPE 用在混合架构的全局 MLA 层上。模型整体仍然感知顺序：KDA 按词元顺序递归更新，短卷积也读相邻位置，打乱输入顺序通常会改变递归状态。

### 实例：各版本的门控与层组合

门控生成方式和层组合随模型版本变化：

| 模型资料 | 门控与层组合 | 适用范围 |
| --- | --- | --- |
| Kimi Linear 论文 v2 | $\alpha$ 由低秩的 $W_\alpha^\downarrow$、$W_\alpha^\uparrow$ 路径生成；约 3 层 KDA 配 1 层 MLA | 论文中的 Kimi Linear 架构 |
| Kimi K3 技术报告 v2 | log-decay（对数衰减）下界 $g_{\min}=-5$；69 个 KDA 层与 24 个 Gated MLA 层 | K3 报告配置 |
| Kimi K3.1 Pro 模型卡与配置 | 69 个 KDA 层与 24 个 Gated DSA 层，Gated DSA 取代了 K3 的 Gated MLA；配置仍有 $\texttt{gate\_lower\_bound}=-5.0$ | 当前 Pro 发布快照，2026-11-25 核对 |

K3 报告的衰减门满足 $\alpha_t=\exp(g_t)$，所以 $g_{\min}=-5$ 对应的最低保留系数约为 $e^{-5}\approx0.0067$：每一步每个通道至少保留约 0.67% 的旧状态。实际保留多少，由当前输入算出的 $\alpha_t$ 决定。

## 全注意力、KDA、压缩摘要和分段记忆各保存什么形状的历史？

四种设计的差别在于长历史状态的形状和读取单位：

| 设计 | 长历史状态 | 当前 query 的读取单位 | 是否随输入增长 |
| --- | --- | --- | --- |
| 全注意力 KV cache | 每个位置一条 K、V | 可见的历史词元位置 | 随位置数增长 |
| KDA | 每层每头一张固定形状的 $S_t$ | 从矩阵读出与 query 匹配的关联，没有位置 ID | 矩阵本身不增长 |
| DeepSeek-V4 预览版的 Compressed Sparse Attention（压缩稀疏注意力，CSA）与 Heavily Compressed Attention（重度压缩注意力，HCA） | 每 4 或 128 个位置一条压缩摘要，另保留局部窗口 | CSA 选摘要 ID 后读取，HCA 读全部已完成摘要 | 摘要条数随输入增长 |
| MemOnce | 每 512 个输入词元保存一段 64 个末层 hidden states，记忆池可卸载到主机内存或 SSD（固态硬盘） | 每次新交互检索一次选中的段；各全注意力层从同一批状态分别生成自己的 K/V | 完整记忆池随历史增长；GPU 活动集受窗口和检索条数限制 |

CSA/HCA 的公式和容量核算见[DeepSeek 怎样压缩长上下文的注意力状态？](deepseek-compressed-attention.md)。

MemOnce 是一个研究原型。它为每个历史段保留末尾一组隐藏状态，并把最后一个状态投影成该段的索引向量。新输入先结合近期窗口算出自己的检索向量，与池中各段索引做内积，挑出相关的远端段，按原来的时间顺序接回近期窗口。这样第一次检索就有 query 可用，各全注意力层也能从同一批选中状态生成自己的 KV；代价是档案越大，索引和检索开销越高。

> [!example] MemOnce 的 GPU 活动集有多大？
> 论文 v1 的 Qwen3.5-4B 适配配置中，每 512 个原始词元取末层 64 个 hidden states（压缩率 $r=8$）。长期检索 top-K 为 64 时选中 64 段、每段 64 个状态，共 4,096 个向量；GPU 活动集另保留 1,024 个近期压缩状态。按每个状态 2,560 个坐标、每个数 2 字节：
>
> $$
> (4{,}096+1{,}024)\times2{,}560\times2=26{,}214{,}400\ \text{字节}=25\ \text{MiB}.
> $$
>
> 论文附录表 14 记为 25 MB 的活动记忆缓存，并报告 1M 词元场景下 640 MB 的 CPU/SSD 卸载记忆池；附录 B.1 另报告 4 MB 的索引矩阵常驻 GPU。模型权重、逐层解码的 KV、索引矩阵和临时工作区仍要另算。论文的从头预训练最大到 1B 参数，长时交互编程和多步工具使用尚待验证。

三者与全注意力相比的取舍可以这样概括：KDA 把历史压进每个头的固定映射，单步成本恒定，但不能按位置回查；CSA/HCA 保留可寻址的压缩条目，条数仍随长度增长；MemOnce 保留可检索的隐藏状态段，按需还原各层 KV。容量怎样随长度变化、能按什么粒度取回、怎样更新，是在它们之间选择时要比较的三件事。这些都是单次请求内的模型状态；应用是否跨运行保留记忆、保留什么，由上下文与记忆系统决定，见[什么时候值得把历史加工成 Agent 记忆？](../context/agent-memory-design-and-evaluation.md)。

> [!info]- 来源
> - **KDA 的状态更新、delta rule、DPLR、分块计算、门控参数化、混合层与 NoPE（“KDA 怎样读、写和遗忘？”“为什么这次写入像一步梯度下降？”“衰减和误差写入……”“门控和 NoPE……”）：** Kimi Team, *Kimi Linear: An Expressive, Efficient Attention Architecture*, arXiv v2（2025-11-01），§2.2 在线 delta rule，§3、§3.1 KDA 更新与 chunkwise 算法，§4 门控参数化、混合结构与 NoPE，§6.2 DPLR，Appendix B chunkwise 并行推导，Appendix C 伪代码，[原文](https://arxiv.org/html/2510.26692v2)。
> - **Q/K/V 短卷积、L2 归一化、递归与分块 kernel 的选择（`q_len ≤ 64`）、短卷积与递归状态缓存、MLA 层的 `past_key_values`（“KDA 怎样读、写和遗忘？”“衰减和误差写入……”“每步成本固定……”）：** Kimi Linear 官方 Transformers 文件 [modeling_kimi.py](https://huggingface.co/moonshotai/Kimi-Linear-48B-A3B-Instruct/blob/d64a5299ded33ab2609617e05f6bd2cf9b6eef35/modeling_kimi.py)，固定提交 d64a5299ded33ab2609617e05f6bd2cf9b6eef35，核对日期 2026-11-25。query 默认读出缩放 $d_k^{-1/2}$ 见 [FLA 的递归实现](https://github.com/fla-org/flash-linear-attention/blob/93734255a9e38a2ac1533132998d5b5ce9b160dc/fla/ops/kda/fused_recurrent.py#L465-L474)。
> - **Kimi K3 的衰减下界与层组合（“实例：各版本的门控与层组合”）：** Kimi Team, *Kimi K3: Open Frontier Intelligence*, arXiv v2（2026-08-07），§2.1.1 lower-bounded decay，§2.1.2 与 Figure 2 层组合，[原文](https://arxiv.org/html/2607.24653v2)。
> - **Kimi K3.1 Pro 的层组合与当前配置（同上）：** Moonshot AI, [Kimi K3.1 Pro model card](https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/80aff651e9b2d2f5b9f70f92a0a7a77054418e16/README.md) 与 [config.json](https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/80aff651e9b2d2f5b9f70f92a0a7a77054418e16/config.json)，Hub revision 80aff651e9b2d2f5b9f70f92a0a7a77054418e16，检查日期 2026-11-25。
> - **DeepSeek-V4 预览版的压缩率、可读摘要与局部窗口（最后一节对照表）：** DeepSeek Team, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*, arXiv v1（2026-04-26），§2.3，[原文](https://arxiv.org/html/2606.19348v1)。层配置与容量核算在 DeepSeek 一章。
> - **MemOnce 的分段、检索、按需生成 KV、存储核算与研究范围（最后一节）：** Nie et al., *MemOnce: A Scalable Memory Architecture for Large Language Models*, arXiv v1（2026-11-20），§3.1、§3.2、§4.1–4.2，Appendix B.1 记忆占用与索引矩阵，Appendix E.3 top-K 检索预算，Appendix F.4 Table 14 的 1M 词元活动缓存与卸载池，Limitations 研究范围，[原文](https://arxiv.org/html/2611.27973v1)。
