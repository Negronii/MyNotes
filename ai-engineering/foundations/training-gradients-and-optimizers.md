# 模型怎样从训练损失得到每个权重的更新？

[语言模型前向篇](how-llms-work.md#下一个词元训练如何更新这些参数？)已经从训练文本得到各位置的 logits（未归一化分数），并用真实下一个词元算出一个标量损失。本章接着问：这个数怎样告诉共享矩阵里的每个参数该往哪边改？答案分为三步：前向计算得到中间表示和损失，backpropagation（反向传播）把损失的导数传回各参数与输入，optimizer（优化器）再结合梯度和自己的状态产生新参数。装载已有权重只是提供这次计算的起点；它本身不计算梯度，也不执行更新。

## 一个矩阵怎样把梯度传给参数和输入

先用一个只有两个输入特征、两个候选词的矩阵，把前向、损失和反向的形状连起来。沿用前一章的训练串 `ababcac → [abab, c, a, c]`，这里保留前两个监督目标 `[c, a]`。为方便手算，暂时只区分 `[a,c]` 两个类别，并人为指定输入特征与矩阵权重；这个例子只计算主 next-token 交叉熵，不含 MTP 等附加目标的损失。数值不是前一章 Transformer 的隐藏状态，也不是模型实测结果。

记 $X\in\mathbb{R}^{T\times d}$ 为输入表示，`T=2` 行对应两个受监督的位置，`d=2` 列对应两个特征；矩阵 $W\in\mathbb{R}^{d\times C}$ 有 `C=2` 列，分别给 `[a,c]` 打分。$W_{ij}$ 是一个可训练标量，框架通常把整张 $W$ 登记为 parameter tensor（参数张量）；反向得到的 $G_W\in\mathbb{R}^{d\times C}$ 与 $W$ 同形状，优化器再按所选规则处理这些坐标。按行向量右乘的约定，logits 是 $Y=XW$：

> [!info] 一个标量怎样沿链式法则得到梯度？
> 若 `w=2`，先算 `y=3w=6`，再算 `L=y²=36`。`L` 对 `y` 的局部斜率是 `2y=12`，`y` 对 `w` 的局部斜率是 `3`，所以 `dL/dw=(dL/dy)(dy/dw)=12×3=36`。如果损失有两条路径依赖同一个 `w`，两条路径各自传回的导数还要相加。矩阵反传只是把同一规则按坐标和使用位置排齐。

$$
X=\begin{bmatrix}1&0\\1&1\end{bmatrix},\qquad
W=\begin{bmatrix}\ln 2&0\\-\ln 2&0\end{bmatrix},\qquad
Y=XW=\begin{bmatrix}\ln 2&0\\0&0\end{bmatrix}.
$$

每行 logits 经 softmax 变成该位置对两个词的概率：

$$
P=\begin{bmatrix}2/3&1/3\\1/2&1/2\end{bmatrix}.
$$

第一行的正确答案是 `c`，概率为 `1/3`；第二行的正确答案是 `a`，概率为 `1/2`。两个位置的平均 cross-entropy（交叉熵）为

$$
L=\frac{-\ln(1/3)-\ln(1/2)}{2}=\frac{\ln 6}{2}\approx 0.895880.
$$

这个损失把两行预测压成一个数。对单行 logits `z`，交叉熵可写为 $\ell(z,y)=\log\left(\sum_j e^{z_j}\right)-z_y$：对数和指数项求导得到 softmax 概率 `p`，第二项只在正确类别减去 `1`，所以单位置梯度是 `p−onehot(y)`。对 `T` 个监督位置取平均后，`D=∂L/∂Y=(P−onehot(target))/T`；`onehot(target)` 是目标的独热矩阵，在正确类别的位置取 `1`，其他位置取 `0`。因此

$$
D=\begin{bmatrix}1/3&-1/3\\-1/4&1/4\end{bmatrix}.
$$

`D` 与 `Y` 形状相同，都是 `2×2`。它不是新的概率，而是每个 logit 微小变化会怎样改变平均损失的局部斜率。把同一个矩阵乘法写成坐标求和，

$$
Y_{tj}=\sum_i X_{ti}W_{ij},\qquad
(G_W)_{ij}=\frac{\partial L}{\partial W_{ij}}=\sum_t X_{ti}D_{tj},\qquad
G_W=X^TD,\qquad G_X=DW^T.
$$

`i` 是输入特征坐标，`j` 是输出类别，`t` 是位置。$G_W$ 与 $W$ 同为 $d\times C$，而 $G_X$ 与 $X$ 同为 $T\times d$。因此权重梯度能告诉优化器怎样改每个参数；输入梯度则把损失信号继续交给更早的层。矩阵乘法沿匹配的内侧维度求和，外侧维度决定结果的形状。

> [!example] 为什么一个共享权重会汇总多个位置？
> 看 $W_{11}$，它把第一个输入特征加到类别 `a` 的 logit。它在两行都被使用，所以改变它会同时改变两个位置的 $Y_{t1}$。其梯度是
> $$
> (G_W)_{11}=X_{11}D_{11}+X_{21}D_{21}=1\cdot\frac13+1\cdot\left(-\frac14\right)=\frac1{12}.
> $$
> 第一行单独带来的正梯度倾向于降低共享权重 $W_{11}$，从而降低这一行错误类别 `a` 的 logit；第二行的负梯度则倾向于提高这个权重，以提高第二行正确类别 `a` 的 logit。它们是各位置对同一共享参数的相反倾向，不是一次更新能分别对两行作反向调节。把贡献相加后，净梯度是 `+1/12`；单独按梯度下降更新 $W_{11}$ 会同时降低两行的 `a` logit，因为两行的第一个输入特征都为 `1`。模型的其他权重坐标也会更新，并共同影响最终 logits。这正是 $X^TD$ 沿位置轴求和的含义。其余元素由同一次矩阵乘法算出：
> $$
> G_W=\begin{bmatrix}1/12&-1/12\\-1/4&1/4\end{bmatrix},\qquad
> G_X=\begin{bmatrix}(\ln2)/3&-(\ln2)/3\\-(\ln2)/4&(\ln2)/4\end{bmatrix}.
> $$

批次中若有许多序列，`t` 也可以代表摊平后的有效监督位置。损失若对有效位置取平均，平均因子就已经包含在 `D` 中；被 padding 或任务规则排除的位置不会产生该位置的直接交叉熵梯度。不过，若该位置的表示仍作为上下文影响其他受监督位置，它仍可能经那些位置的损失收到梯度。

## 梯度怎样穿过 Attention、FFN 和 Embedding

实际模型把很多矩阵乘法、逐元素运算和分支串在一张计算图里。reverse-mode automatic differentiation（反向模式自动微分）从标量损失开始，初始导数是 `∂L/∂L=1`；每个算子把收到的上游梯度乘以自己的局部导数，再传给它的输入。标量损失对大量参数求梯度时，反向模式能在一次反向遍历里得到所有参数的梯度，不必为每个参数单独扰动权重、重跑一次完整前向，也不必显式存下一个“输出坐标 × 参数坐标”的完整 Jacobian（雅可比矩阵）。前向保存或重算的中间激活，供各算子计算这些局部导数。

~~~mermaid
flowchart TD
    Loss["标量损失 L"] --> LM["LM head<br/>预测头参数与最终状态"]
    LM --> FinalNorm["最终 Norm 的反向"] --> AddFFN["FFN 残差加法的反向"]
    AddFFN -->|旁路| Y["FFN 输入状态 Y<br/>梯度合流"]
    AddFFN -->|FFN 子层| Ffn["FFN<br/>线性层与门控分支"]
    Ffn --> Norm2["Norm2 反向"] --> Y
    Y --> AddAttn["Attention 残差加法的反向"]
    AddAttn -->|旁路| X["Attention 输入状态 X<br/>梯度合流"]
    AddAttn -->|注意力子层| Out["输出投影"]
    Out --> Q["Q 路径"]
    Out --> K["K 路径"]
    Out --> V["V 路径"]
    Q --> R["共同投影输入 R<br/>三路梯度相加"]
    K --> R
    V --> R
    R --> Norm1["Norm1 反向"] --> X
    X --> Earlier["按同样顺序继续经过更早的 block"]
    Earlier --> Emb["Embedding 表<br/>按 ID 累加到被查行"]
~~~

图中展开前向篇使用的 pre-norm decoder-only self-attention block 的反向路径，并示意继续经过更早的 block：残差处拆出的旁路梯度与子层梯度在同一状态合流，Q/K/V 的三条输入梯度在共同的投影输入合流。它省略了 attention 内部的分数与 softmax 运算，下面展开这些步骤；其他架构可能有不同的归一化顺序，cross-attention 的 Q 与 K/V 也可能来自不同输入。

回到缩放点积 attention（注意力）。前向篇先将 attention 输入归一化为 $U$，再投影为 Q/K/V，并对 Q/K 做 RoPE。本节为聚焦矩阵反传，简化前向为不使用 RoPE，因此下面的 Q/K 都是未经旋转的投影结果，分数和梯度也对应这个简化计算。若实际前向使用 RoPE，点积中的 Q/K 是各位置旋转后的量；先求对旋转后 Q/K 的梯度，再对每个位置应用其旋转矩阵的转置，映回投影输出后才能代入下面的权重梯度。按行向量记法，若 $q'=q\operatorname{Rot}_t$，则 $G_q=G_{q'}\operatorname{Rot}_t^T$，K 同理。用 $R$ 表示送入这些投影的共同表示；在前向篇记法中，它对应归一化后的 $U$。设这一头有 $T_q$ 个 query 位置，K/V 轴长度为 $T_k$，每头宽度为 $d_h$：$Q\in\mathbb{R}^{T_q\times d_h}$，$K,V\in\mathbb{R}^{T_k\times d_h}$。因果或 padding mask 决定每个 query 实际可读哪些 K/V 位置；一般情况下 $T_q$ 与 $T_k$ 是各自的轴长度，不必相同。令固定的加性掩码矩阵为 $M$，可读项加 `0`、屏蔽项加 $-\infty$，求导时将 $M$ 视为常量。分数矩阵 $S=QK^T/\sqrt{d_h}+M$ 与沿 key 轴逐行归一化得到的权重 $P=\operatorname{softmax}_{\rm keys}(S)$ 都是 $T_q\times T_k$；加权输出 $Z=PV$ 是 $T_q\times d_h$。若从后续层收到 $G_Z=\partial L/\partial Z$，其形状与 $Z$ 相同；沿值分支有 $G_V=P^TG_Z$，形状为 $T_k\times d_h$，沿权重分支有 $G_P=G_ZV^T$，形状与 $P$ 相同。对每一行的 softmax，

$$
(G_S)_{tj}=P_{tj}\left((G_P)_{tj}-\sum_kP_{tk}(G_P)_{tk}\right).
$$

同一行 softmax 共用分母，所以一个 logit 的变化会影响整行概率；导数要减去该行上游梯度的 $P$ 加权平均。例如 $P=(1/4,3/4)$、$G_P=(2,0)$ 时，加权平均为 $1/2$，于是 $G_S=(3/8,-3/8)$，两项之和为零。

接着，将掩码 $M$ 视为常量，分数梯度传回查询与键：

$$
G_Q=G_SK/\sqrt{d_h},\qquad G_K=G_S^TQ/\sqrt{d_h}.
$$

若是一次读取整段序列的 self-attention，三组表示来自同一段、同为 `T` 行的输入 `R`，即 $Q=RW_Q$、$K=RW_K$、$V=RW_V$ 且 $T_q=T_k=T$。三组投影权重的梯度分别为

$$
G_{W_Q}=R^TG_Q,\qquad G_{W_K}=R^TG_K,\qquad G_{W_V}=R^TG_V.
$$

在这个共用 `R` 的 self-attention 例子中，三条分支对同一个输入的梯度相加：

$$
G_R=G_QW_Q^T+G_KW_K^T+G_VW_V^T.
$$

缓存增量解码时，当前 query 可只有一行而 K/V 轴还包含整段前缀，所以 $T_q$ 与 $T_k$ 也可以不同，不能套用这里的单个 `R` 公式。Cross-attention（交叉注意力）同样可以让 Q 与 K/V 来自不同输入；这时 Q 支路和 K/V 支路的输入梯度分别回到各自来源，不使用上面把三支相加到单个 `R` 的公式。每个式子都沿用前一节的线性规则。$G_V$ 先由加权和回到 V；$G_P$ 经 softmax 变为 $G_S$ 后，才流向 Q 与 K。attention 权重 `P` 在前向中混合 V，反向则把输出变化传回 P 与 V；若模型另用 indexer 挑选位置，indexer 分数只决定候选 ID，不负责混合 V。因果掩码禁止读取的位置在该 query 的 softmax 中被屏蔽，其对应的 attention 分数梯度为零；这不同于屏蔽一个监督位置的 loss，作为上下文的该位置仍可从其他受监督 query 的 attention 路径收到梯度。

多头输出投影同样按线性规则反传。若有 `h` 个头，拼接矩阵 $H_{cat}=\operatorname{Concat}(Z_1,\ldots,Z_h)$ 的形状是 $T_q\times(hd_h)$，输出投影 $W_O$ 的形状是 $(hd_h)\times d_{model}$，因此 $O=H_{cat}W_O$ 的形状为 $T_q\times d_{model}$。令

$$
G_{H_{cat}}=G_O W_O^T,\qquad G_{W_O}=H_{cat}^T G_O.
$$

先把 $G_{H_{cat}}$ 沿拼接轴拆成各头的 $G_{Z_i}$，再分别沿 $Z_i=P_iV_i$ 传回各头的 Q/K/V。这样拆分发生在反传穿过输出投影之后。

FFN（前馈网络）的线性层也一样。令 $R_{ffn}=\operatorname{Norm}_2(Y)$ 表示 FFN 自己的归一化输入；若门控 FFN 依次计算 $R_{ffn}W_g$、$R_{ffn}W_u$、SiLU（Sigmoid Linear Unit）、逐元素乘法和降维投影 $W_d$，每个投影的权重梯度都把该投影的输入转置乘以上游梯度。反向再经过 SiLU 和逐元素乘法；门控支路与候选支路最后回到同一 $R_{ffn}$ 时，把梯度相加，再经 $\operatorname{Norm}_2$ 传回 $Y$。这里不必展开 SiLU 的逐坐标导数矩阵，关键是每个分支按自身局部运算回传，合流处对共享输入求和。

残差相加也是分支合流：若 `Y=X+F(X)`，收到 $G_Y$ 后，旁路直接送来 $G_Y$，变换分支再把它乘以 `F` 的局部导数传回来，两者相加。Manifold-Constrained Hyper-Connections（流形约束超连接，mHC）把旁路改为状态相关的流混合，并从状态生成 `A/B/C`；其映射与梯度边界见[模型前向篇的残差流与 mHC 说明](how-llms-work.md#把更新后的状态传给下一层)。无论结构多复杂，梯度都沿实际执行的前向边返回；一个分支若被切断或前向中根本没有经过，就不会从这条损失路径收到普通的反向梯度。

Embedding lookup（嵌入查表）可以看成从表 $E\in\mathbb{R}^{N\times d}$ 选择行，其中 $N$ 是词表大小。若位置 `t` 的 ID 是 `q`，前向取 $X_t=E_{q,:}$；反向把 $G_{X,t}$ 加回 $G_E$ 的第 `q` 行。若一个批次多次出现同一个 ID，这些位置的梯度会累加到同一行，未选中的行不会从这些查表路径获得梯度。若 embedding 和 language model head（语言模型头，LM head）绑定为同一参数矩阵，输出头路径也会给这个矩阵贡献梯度，两种来源相加。

这些路径决定了冻结和离散选择的含义。冻结某个权重 `W`，意思是训练步不更新它；常见实现会跳过该权重自身梯度的计算或保存。若前面的可训练层仍通过 `XW` 影响损失，反向仍可能需要用固定的 `W` 计算传回输入的梯度 $G_X=DW^T$。因此“参数不更新”不等于“梯度不能经过这个算子”。低秩微调（LoRA）中的有效权重可写为 `W'=W+BA`；基础矩阵 `W` 冻结、增量支路中的 `A` 和 `B` 可训练。它属于[微调策略](../fine-tuning/fine-tuning-strategies.md)；这里解释的是梯度能否继续沿输入路径传播。

相反，若前向使用 `detach`（停止梯度）将一个张量从计算图切开，梯度就不会从后续损失穿过该边返回被切断的上游计算。离散 `top-k`（取前 k 项）产出的整数 ID 也没有普通的连续导数来表达“改选另一个 ID”的影响；但被选中的值仍可沿后续连续运算收到梯度。[长上下文中的 V3.2 索引器例子](long-context-attention.md#DeepSeek-V3.2%20怎样训练离散选择之前的%20Indexer？)会展示 detach、索引选择和索引器自有损失如何具体限定梯度路径；不应从推理代码中的整数选择反推出 V4 未披露的训练损失。

## AdamW 和 Muon 怎样使用已经算好的梯度

截至这里，反向传播只回答“损失怎样依赖参数”：它产生 $G_W=\partial L/\partial W$，尚未改动 `W`。优化器回答另一个问题：根据这份梯度、学习率和历史状态，下一步参数取什么值。在这个单矩阵例中，按训练步记的 $G_t$ 就是当前 $W_{t-1}$ 上算出的 $G_W$。以下下标 `t` 表示训练步，不是前文的词元位置：第 `t` 次更新从当前参数 $W_{t-1}$ 开始，在这些参数上计算 $G_t$，再得到新参数 $W_t$。先看最简单的随机梯度下降（SGD）：

$$
W_t=W_{t-1}-\eta G_t,
$$

其中 `η` 是学习率，它把梯度的方向换算为本步的更新尺度。沿用前面的 $G_W$，取教学用 `η=0.01`，SGD 对整张矩阵做一步更新后，交叉熵从 `0.895880` 降到约 `0.894492`。这是这个人为选择的矩阵和步长的计算结果，不表示每个训练步的损失都必然下降。learning-rate scheduler（学习率调度器）可随训练步调整 `η`；它改变更新尺度，但不保证训练最终到达全局最优点。

### AdamW 怎样逐坐标使用梯度和历史？

AdamW 为每个可训练坐标维护两条指数滑动平均：$m_t$ 是梯度的一阶滑动平均，$v_t$ 是梯度平方的二阶滑动平均。$v_t$ 跟踪 $G_t^2$，不是先减去均值后的统计方差。先从全零状态开始时，公式为

$$
m_t=\beta_1m_{t-1}+(1-\beta_1)G_t,\qquad
v_t=\beta_2v_{t-1}+(1-\beta_2)(G_t\odot G_t),
$$

$$
\widehat m_t=\frac{m_t}{1-\beta_1^t},\qquad
\widehat v_t=\frac{v_t}{1-\beta_2^t},\qquad
W_t=(1-\eta\lambda)W_{t-1}-\eta\frac{\widehat m_t}{\sqrt{\widehat v_t}+\epsilon}.
$$

`⊙` 表示逐元素乘法；根号、除法与权重衰减也都按坐标执行。$\beta_1$、$\beta_2$ 控制新梯度替换旧历史的速度；偏差校正补偿初始零状态造成的低估。分母开根号后逐坐标缩放更新，`ε` 避免除以零；`λ` 的权重衰减则独立缩小参数，不进入 $m_t$ 或 $v_t$。AdamW 仍然只使用已经算出的梯度，它不负责生成 $G_t$。

> [!example] AdamW 第一步怎样更新一个权重？
> 沿用 $W_{11}=\ln 2$ 和 $G_{11}=1/12$，从 $m_0=v_0=0$ 开始，取教学用学习率 `η=0.01`、权重衰减 `λ=0.1`、$\beta_1=0.9$、$\beta_2=0.95$，并令 $\epsilon=10^{-20}$ 相对梯度可忽略。这两项 `β` 也与 V4 报告的 AdamW 设置相同。此时偏差校正后的 $\widehat m_1=1/12$、$\widehat v_1=(1/12)^2$，所以自适应梯度项约为 `1`。参数先按解耦衰减从 `ln2` 缩为 `0.999 ln2`，再减去 `0.01`，得到 $W_{11}'\approx0.682454$。参数值、损失梯度和优化器状态是三种不同的量。

### Muon 怎样把一个矩阵梯度变成方向？

Muon 是面向隐藏层二维权重矩阵的优化器，而不是新的反向传播方法；它收到的仍是 $G_t$。Muon 的原始说明把标量、向量和输入/输出层交给标准优化器。DeepSeek-V4 在大多数矩阵参数上使用 Muon，但把 embedding、prediction head（预测头）、mHC 静态偏置与门控因子，以及 RMSNorm 权重交给 AdamW。因此上面的词表预测头若采用 V4 的分工，就由 AdamW 更新；下述 Muon 矩阵方向是通用矩阵示例，不是同一个 prediction head 的更新。

在 V4 的具体配方中，Muon 先维护矩阵动量 $M_t=\mu M_{t-1}+G_t$，再用 $D_t=\mu M_t+G_t$ 形成 Nesterov 型方向。将 $D_t$ 按 Frobenius norm（弗罗贝尼乌斯范数，即矩阵元素平方和再开根）归一化后，V4 做 10 步 hybrid Newton–Schulz（混合 Newton–Schulz）迭代，近似把非零奇异方向的伸缩因子推向 `1`；Muon 的其他实现可以选用不同迭代步数。用紧致奇异值分解（compact singular value decomposition，SVD）写成 $D=U_r\Sigma_rV_r^\top$，其中 $r$ 是秩：$V_r$ 的列给出输入侧方向，$U_r$ 的列给出与之配对的输出侧方向，$\Sigma_r$ 的对角元素是沿这些方向的伸缩倍数。在列向量约定下，每对奇异向量满足 $Dv_i=\sigma_i u_i$；这个等式用列向量刻画线性变换，与前向篇输入行向量右乘权重是转置后的记号约定。理想参照统一写作 $U_rV_r^\top$，把每个非零方向的伸缩倍数变成 `1`；零方向仍为零。实际计算用矩阵乘法多项式逼近这个参照，而不是每步都显式做完整 SVD。

V4 报告中的更新为

$$
O'_t=\operatorname{HybridNewtonSchulz}(D_t),\qquad
O_t=\gamma\sqrt{\max(n,m)}\,O'_t,\qquad
W_t=(1-\eta\lambda_{wd})W_{t-1}-\eta O_t,
$$

其中 $W\in\mathbb{R}^{n\times m}$ 是数学上的逻辑矩阵，`γ` 调整更新的整体 RMS，$\lambda_{wd}$ 是解耦 weight decay（权重衰减）。满秩时，$O'_t$ 的约 `min(n,m)` 个非零奇异值经迭代接近 `1`，其 Frobenius norm 因而约为 $\sqrt{\min(n,m)}$；摊到 $nm$ 个矩阵元素上的 RMS 约为 $1/\sqrt{\max(n,m)}$。乘上 $\sqrt{\max(n,m)}$ 后 RMS 约为 `1`，再由 `γ` 设置整体尺度；秩不足时实际 RMS 会相应更小。这里的 $O'_t$ 与 $O_t$ 是 Muon 的更新方向矩阵，和前向篇 attention 输出的 `O` 用途不同。Muon 按矩阵的方向结构变换更新量，最终仍把更新加到原来的参数矩阵上；它不会把模型权重本身变成正交矩阵。

> [!example] 十步迭代把两个奇异方向推向单位长度
> 取教学用方向 `D=diag(9,1)`。其紧致 SVD 可写为 $D=U_2\Sigma_2V_2^\top$，其中 $U_2=V_2=I$、$\Sigma_2=diag(9,1)$；理想方向 $U_2V_2^\top=I$。Frobenius norm 为 `√82`，归一化后从 `D_0=diag(9/√82,1/√82)≈diag(0.993884,0.110432)` 开始。对这个对角矩阵，迭代多项式可以逐个处理两个对角值：`x'=a x+b x³+c x⁵`。前 8 步使用 `(a,b,c)=(3.4445,−4.7750,2.0315)`，后 2 步使用 `(2,−1.5,0.5)`。按普通浮点标量复算，第 1 步约为 `(0.705643,0.373984)`，第 8 步约为 `(1.094391,1.134267)`，第 10 步约为 `(1.000030,1.000190)`。有限步近似而非精确得到 `1`；若一个奇异值初始为零，它也保持为零。该计算说明多项式在简单矩阵上的作用，不是 BF16 内核或模型训练结果实测。

Muon 的矩阵多项式包含跨行列的乘积；若把权重分片后各自独立做 Newton–Schulz 迭代，结果就不等于对整张逻辑矩阵做同一迭代。分布式实现要协调这些矩阵乘积；“完整逻辑矩阵”说明数学对象及梯度的形状，不表示每块 GPU 都物理保存一份完整矩阵。

AdamW 和 Muon 的差别主要在梯度怎样被转换成更新：AdamW 按坐标累积梯度及其平方，再逐坐标缩放；Muon 按逻辑矩阵累积动量，再整体正交化方向并作形状缩放。两者都从反向传播已算出的梯度开始，具体采用哪一种及其参数组属于训练配方，不是通用的最优结论。

> [!info]- 来源
> 这些推导使用普通实数矩阵与链式法则；本页两类词、二维权重、学习率和奇异值都是教学示例。引用的模型结果与配置仅适用于所列报告版本。
>
> - **损失与反向模式自动微分。** [PyTorch CrossEntropyLoss 2.15](https://docs.pytorch.org/docs/2.15/generated/torch.nn.CrossEntropyLoss.html) 定义 logits、目标索引、忽略位置和平均损失；本页使用的是无类别权重、无 label smoothing 的简单情形。[Baydin et al., *Automatic Differentiation in Machine Learning: a Survey*, arXiv v4, 2018-02-05, §§3.2、4.2](https://arxiv.org/html/1502.05767v4#S3.SS2) 说明反向模式如何从标量目标起始，沿运算图在一次反向遍历中计算对大量输入的导数；[PyTorch 2.15 Autograd mechanics](https://docs.pytorch.org/docs/2.15/notes/autograd.html) 记录动态计算图和冻结参数时的梯度控制。Attention 的 `QK^T`、softmax 与 `PV` 前向来自[Attention Is All You Need, v7, §3.2](https://arxiv.org/html/1706.03762v7#S3.SS2)；前向篇注意力使用 RoPE 的 Q/K 旋转见 [RoFormer, v5, §3.2.2, equations 14–16](https://arxiv.org/html/2104.09864v5#S3.SS2)；本页相应反向式由链式法则推得。
> - **Adam 与解耦权重衰减。** [Kingma and Ba, *Adam: A Method for Stochastic Optimization*, arXiv v9, Algorithm 1](https://arxiv.org/abs/1412.6980v9) 给出一阶/二阶矩估计和偏差校正；[Loshchilov and Hutter, *Decoupled Weight Decay Regularization*, arXiv v3, 2019-01-04, §2](https://arxiv.org/html/1711.05101v3#S2) 解释 AdamW 将权重衰减与自适应梯度更新解耦；[PyTorch AdamW 2.15](https://docs.pytorch.org/docs/2.15/generated/torch.optim.AdamW.html) 给出公式及实现参数。DeepSeek-V4 使用 AdamW 的具体参数组见 [Technical Report v1, §4.2.2](https://arxiv.org/html/2606.19348v1#S4.SS2)。
> - **Muon。** [Jordan, *Muon: An optimizer for hidden layers in neural networks*, 2024-12-08](https://kellerjordan.github.io/posts/muon/) 介绍 Muon 的矩阵参数范围、Newton–Schulz 迭代和非隐藏层参数选择；[Liu et al., *Muon is Scalable for LLM Training*, arXiv v1, 2025-02-24, §§2.1–2.3](https://arxiv.org/html/2502.16982v1) 讨论权重衰减、更新缩放和分布式训练；DeepSeek-V4 Technical Report v1 的 [§2.4](https://arxiv.org/html/2606.19348v1#S2.SS4)、[§3.4.1](https://arxiv.org/html/2606.19348v1#S3.SS4.SSS1) 和 [§4.2.2](https://arxiv.org/html/2606.19348v1#S4.SS2) 分别给出混合 Newton–Schulz 算法、训练框架和参数分工。该报告还说明混合 ZeRO bucket、超出相应并行组时在额外数据并行组上冗余计算 Muon 更新，以及 Newton–Schulz 矩阵乘使用 BF16、MoE 梯度通信前随机舍入到 BF16 并在本地用 FP32 求和；报告没有完整列出 Muon 状态逐参数的数据类型或总字节数。截至 2026-11-11，核对到的公开报告版本为 v1。
