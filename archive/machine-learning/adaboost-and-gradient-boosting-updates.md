# AdaBoost 与 Gradient Boosting（梯度提升）怎样逐轮改变预测？

当分类器把四条记录分对三条、分错一条，下一轮怎样把学习重点转向错分记录？当房价预测比真实值少了 50,000 美元，下一棵树应拟合哪个数？AdaBoost 与梯度提升都会依次加入学习器，但它们构造下一轮训练信号的方式不同：前者调整样本权重，后者拟合当前损失对预测值的负梯度。

| 方法 | 新学习器收到的训练信号 | 加入集成的方式 |
| --- | --- | --- |
| AdaBoost（Adaptive Boosting，自适应提升） | 依当前分类结果更新的样本权重 | 按分类器权重加总投票分数 |
| Gradient boosting（梯度提升） | 依当前预测和损失计算的负梯度（伪残差） | 把树的叶节点数值增量加到当前预测 |

因此，“提升”都意味着按顺序修正已有集成；AdaBoost 让错分样本在下一轮训练中占更大影响，梯度提升让新树近似当前预测应下降损失的方向。下面分别沿一轮完整重放，再说明多轮时哪些量会更新。

## AdaBoost：错分样本如何变重？

AdaBoost（Adaptive Boosting，自适应提升）把多个 weak learner（弱学习器）按轮次训练。分类时，每轮学习器的加权错误率决定它在最终分类投票中的分量；更新样本权重后，下一轮会更关注本轮错分的记录。决策树桩常作弱分类器，但权重机制也可交给其它支持样本权重的分类算法。每一轮都依赖上一轮结果，不同于随机森林中独立训练后再汇总的树。

这里先推导经典二分类 AdaBoost。训练集有 $n$ 条记录，$i=1,\ldots,n$ 标记一条记录，$x_i$ 是它的特征；第 $t$ 轮把标签和分类器输出编码为 $y_i,h_t(x_i)\in\{-1,+1\}$。令前 $t-1$ 轮的加权分数为 $S_{t-1}$，训练集的指数损失为 $L$：

$$
\begin{aligned}
S_{t-1}(x)&=\sum_{s=1}^{t-1}\alpha_s h_s(x),\\
L(S)&=\sum_{i=1}^{n}\exp[-y_iS(x_i)],\\
w_i^{(t)}&=\frac{\exp[-y_iS_{t-1}(x_i)]}{L(S_{t-1})}
\end{aligned}
$$

第一轮从 $S_0(x)=0$ 开始，所以 $w_i^{(1)}=1/n$；之后每条记录的当前权重就是它在这份指数损失中所占的比例。第 $t$ 轮分类器根据 $(x_i,y_i)$ 和 $w_i^{(t)}$ 训练。它在当前分布上的加权错误率是错分样本的权重之和：

$$
\epsilon_t=\sum_i w_i^{(t)}\,\mathbf{1}[y_i\ne h_t(x_i)]
$$

当 $0<\epsilon_t<0.5$ 时，分类器投票权及样本权重更新为

$$
\alpha_t=\frac12\ln\frac{1-\epsilon_t}{\epsilon_t},
\qquad
w_i^{(t+1)}=\frac{w_i^{(t)}\exp[-\alpha_t y_i h_t(x_i)]}{Z_t}
$$

这里 $\mathbf{1}[\cdot]$ 是指示函数，在条件为真时取 1，否则取 0；$\alpha_t$ 与权重皆无量纲，$Z_t$ 是使新权重和为 1 的归一化因子。若样本分对，$y_i h_t(x_i)=+1$，其权重乘 $e^{-\alpha_t}$；若分错，乘 $e^{\alpha_t}$。所以错分样本相对正确样本的权重会上升，而不是只把错分样本权重加上一个固定数。

固定本轮分类器 $h_t$ 后，将新分数 $S_{t-1}+\alpha h_t$ 代入指数损失；当前损失 $L(S_{t-1})$ 与候选 $\alpha$ 无关：

$$
L(S_{t-1}+\alpha h_t)=L(S_{t-1})\left[(1-\epsilon_t)e^{-\alpha}+\epsilon_t e^{\alpha}\right]
$$

因此只需最小化括号里的因子 $Z_t(\alpha)$，它正是本轮更新式中归一化前的权重总和。当前正确样本权重合计 $1-\epsilon_t$，错分样本合计 $\epsilon_t$，故

$$
Z_t(\alpha)=(1-\epsilon_t)e^{-\alpha}+\epsilon_t e^{\alpha},
\qquad
\frac{dZ_t}{d\alpha}=-(1-\epsilon_t)e^{-\alpha}+\epsilon_t e^{\alpha}=0
$$

令导数为 0，得 $e^{2\alpha}=(1-\epsilon_t)/\epsilon_t$，于是得到上式的 $\alpha_t$。二阶导数 $Z_t''(\alpha)=(1-\epsilon_t)e^{-\alpha}+\epsilon_t e^{\alpha}>0$，所以该驻点是唯一最小值。固定前轮分数及当前分类器后，按此公式计算的加权错误率 $\epsilon_t$ 越小，这轮的指数损失最优投票系数越大；再按同一分数更新权重，后续弱学习器就会把更多训练注意力放在指数损失较大的记录上。

> [!example] 四个等权样本中错分一个
> 假设本轮有四个等权样本，每个初始权重为 $1/4$；三条分对、一条分错，所以 $\epsilon=1/4$。这轮分类器的投票权为 $\alpha=\frac12\ln 3\approx0.5493$，正确样本的更新乘数为 $e^{-\alpha}=1/\sqrt3\approx0.5774$，错分样本为 $e^\alpha=\sqrt3\approx1.7321$。
>
> | 样本 | 本轮分类 | 更新前权重 | 未归一化权重 | 归一化后权重 |
> | --- | --- | ---: | ---: | ---: |
> | 1 | 正确 | 0.25 | $0.25/\sqrt3\approx0.1443$ | $1/6$ |
> | 2 | 正确 | 0.25 | $0.25/\sqrt3\approx0.1443$ | $1/6$ |
> | 3 | 正确 | 0.25 | $0.25/\sqrt3\approx0.1443$ | $1/6$ |
> | 4 | 错误 | 0.25 | $0.25\sqrt3\approx0.4330$ | $1/2$ |
>
> 未归一化权重的精确总和为 $Z=3/(4\sqrt3)+\sqrt3/4=\sqrt3/2\approx0.8660$。用这个未舍入总和归一化后，错分样本占 $1/2$，其余三个各占 $1/6$。因此下一轮分类器的训练目标中，这条记录贡献一半样本权重。

训练若继续进行，每轮都用当前权重训练分类器，再计算它的加权错误、投票权和下一轮权重。完成 $T$ 轮后，对一个新输入 $x$，经典二分类形式先累加各轮带正负号的票，再按总分符号分类：

$$
S_T(x)=\sum_{t=1}^{T}\alpha_t h_t(x),
\qquad
H(x)=\operatorname{sign}(S_T(x))
$$

正分数投向 $+1$，负分数投向 $-1$；各轮的 $\alpha_t$ 决定分类器的投票分量。若 $S_T(x)=0$，须按预先设定的平票规则选类。$\epsilon=0$ 时经典公式的 $\alpha$ 趋于无穷；$\epsilon=0.5$ 时 $\alpha=0$，该轮没有投票贡献；$\epsilon>0.5$ 时分类器不满足经典弱学习条件，在二分类中若允许反转输出，可先翻转预测再计算错误率。

> [!example] 第二轮错误怎样影响最终投票
> 延续上一例，假设第二轮分类器只分错记录 1；它在上一轮得到的权重为 $w_1^{(2)}=1/6$，所以 $\epsilon_2=1/6$、$\alpha_2=\frac12\ln5\approx0.8047$。再假设一个新输入 $x$ 的两轮预测分别为 $h_1(x)=+1$、$h_2(x)=-1$：
>
> | 轮次 | $h_t(x)$ | 投票权 $\alpha_t$ | 加权票 $\alpha_t h_t(x)$ |
> | ---: | ---: | ---: | ---: |
> | 1 | $+1$ | $0.5493$ | $+0.5493$ |
> | 2 | $-1$ | $0.8047$ | $-0.8047$ |
> | 合计 |  |  | $S_2(x)=-0.2554$ |
>
> 因为总分为负，集成预测 $-1$。这个例子中权重 $w_i^{(t)}$ 控制分类器训练时关注哪些记录；$\alpha_t$ 控制训练好的第 $t$ 个分类器在新输入上的票有多大。两者相关，但用途不同；上面的第二轮错误和新输入预测都是明确的教学假设。

**scikit-learn 1.9.1 的实现边界。** `AdaBoostClassifier` 使用离散 SAMME（Stagewise Additive Modeling using a Multi-class Exponential loss function，多分类指数损失逐步加法建模）；默认基学习器是 `DecisionTreeClassifier(max_depth=1)`，且基学习器必须支持 `sample_weight`。有 $K$ 类时，若当前加权错误率 $\epsilon_t\ge1-1/K$，实现丢弃这一轮；若首轮就达到此阈值则报错。若错误率为 0，则保留该完美分类器并提前停止。实现每轮开始时把当前样本权重的下限设为对应浮点类型的机器精度 epsilon（machine epsilon；`np.finfo(dtype).eps`）；低于这个值的权重会被抬高，但初始权重为 0 的记录仍保持为 0；预测分数会除以分类器权重总和。

**SAMME 与对称二分类更新的关系。** 当 $K=2$ 且 $0<\epsilon_t<0.5$ 时，SAMME 系数为 $\lambda\ln((1-\epsilon_t)/\epsilon_t)$，其中 $\lambda>0$ 是 API 参数 `learning_rate`。若经典对称式也用同一个 $\lambda$ 缩放，令 $\tilde\alpha_t=\lambda\alpha_t$，则 SAMME 系数为 $2\tilde\alpha_t$。对称式把正确/错分样本分别乘 $e^{-\tilde\alpha_t}$ 与 $e^{\tilde\alpha_t}$；将所有更新权重再乘公共因子 $e^{\tilde\alpha_t}$ 后，就变成正确样本不变、错分样本乘 $e^{2\tilde\alpha_t}$，恰好是 SAMME 更新。归一化后两种公式给出相同样本分布；若固定同一组二分类器，最终加权投票的符号也相同。实现的浮点截断、提前停止和分数归一化属于 API 行为；这项代数关系不能据此推广成多分类算法只替换标签编码。

## Gradient Boosting：下一棵树该拟合什么？

梯度提升先用一个常数预测 $F_0$ 开始，再逐轮加入回归树。训练集有 $n$ 条记录；令 $v_i\ge0$ 为样本权重，且总权重为正（不传权重时 $v_i=1$），$F_i=F(x_i)$ 表示模型对第 $i$ 条记录的原始输出分数。初始常数选择为使训练损失最小的值：

$$
F_0=\arg\min_c\sum_{i=1}^{n}v_i\ell(y_i,c)
$$

> [!info] $\arg\min$ 返回什么？
> $\min_c$ 问的是“最小损失是多少”，$\arg\min_c$ 问的是“哪个 $c$ 使损失最小”。这里要初始化一个预测值，所以取后者。例如两个等权目标为 2 和 4 时，半平方损失在 $c=3$ 处最小，$F_0=3$，而最小损失为 1。

平方损失下，$F_0$ 是加权目标均值；绝对误差下是加权中位数。二分类对数损失下，只有当正类和负类各自的样本权重总和都为正时，$0<\pi<1$，且 $F_0=\ln(\pi/(1-\pi))$，其中 $\pi=\sum_i v_i\mathbf{1}[y_i=1]/\sum_i v_i$ 是加权正类比例。此时模型输出是 raw score（原始分数）logit（对数几率），不是概率。

第 $m$ 轮开始时，训练行上的当前输出可以看作向量 $(F_{m-1}(x_1),\ldots,F_{m-1}(x_n))$。令 $g_{im}$ 是损失对第 $i$ 条预测值的导数；对应的负梯度，也叫 pseudo-residual（伪残差），为：

$$
r_{im}=-\left.\frac{\partial\ell(y_i,F(x_i))}{\partial F(x_i)}\right|_{F(x_i)=F_{m-1}(x_i)}
$$

若每条训练记录的预测都能独立移动一个小量 $\delta_i=-\tau g_{im}$（$\tau>0$），一阶损失变化为：

$$
\Delta\mathcal{L}\approx\sum_{i=1}^{n}v_i g_{im}\delta_i=-\tau\sum_{i=1}^{n}v_i g_{im}^{2}\le0,
\qquad
\mathcal{L}=\sum_{i=1}^{n}v_i\ell(y_i,F(x_i))
$$

这说明沿各行各自的负导数方向，总损失在一阶近似下不会增大；只有至少一条正权重记录的梯度非零时，才会严格下降。真实模型不能给每条训练行任意设一个独立更新值：一棵树用特征切分，把落入同一叶节点的记录放在一起并共享叶值。它因此用特征规则近似这列负梯度目标，也能把同一分叶规则应用到新输入。样本权重 $v_i$ 同时用于拟合树和计算加权损失。

平方损失 $\ell=\frac12(y-F)^2$ 下，$g_{im}=F_{m-1}(x_i)-y_i$，所以 $r_{im}=y_i-F_{m-1}(x_i)$，就是普通残差，单位与回归目标相同。二分类对数损失中，标签 $y_i\in\{0,1\}$、概率 $p_i=\sigma(F_{m-1}(x_i))$，其中 $\sigma$ 是 sigmoid（逻辑函数）；$F$ 与 $p$ 的关系是 logit。对损失

$$
\ell(y_i,F_i)=-y_i\ln p_i-(1-y_i)\ln(1-p_i)
$$

链式求导可分两步看：

$$
\frac{\partial\ell}{\partial p_i}=-\frac{y_i}{p_i}+\frac{1-y_i}{1-p_i}=\frac{p_i-y_i}{p_i(1-p_i)},
\qquad
\frac{\partial p_i}{\partial F_i}=p_i(1-p_i)
$$

因此 $\partial\ell/\partial F_i=p_i-y_i$，伪残差为 $r_{im}=y_i-p_i$。标签 $y_i$、概率 $p_i$ 和伪残差 $r_{im}$ 都是无量纲；树的最终增量加到原始分数 $F$，所以二分类时叶增量 $\gamma_{jm}$ 也处在 logit 尺度，之后才用 $\sigma(F_m(x))$ 得到新概率。回归时，$F$ 和叶增量则使用目标单位，例如美元。

拟合伪残差的树按特征把输入空间划成叶区域 $R_{jm}$：$R_{jm}$ 是第 $m$ 棵树的第 $j$ 个叶，$J$ 是该树的叶数，每个训练行和新输入都落入一片叶。树先用这些分叶区域近似负梯度，再按原损失给每片叶选更新值。若有限最优值存在，下面的理论式给出使叶内损失最小的更新量：

$$
\gamma_{jm}^{*}=\arg\min_{\gamma}\sum_{i:x_i\in R_{jm}}v_i\ell\bigl(y_i,F_{m-1}(x_i)+\gamma\bigr)
$$

$$
F_m(x)=F_{m-1}(x)+\eta\sum_{j=1}^{J}\gamma_{jm}^{*}\mathbf{1}[x\in R_{jm}]
$$

其中 learning rate（学习率）$\eta$ 无量纲；只有 $0<\eta<1$ 时才是在缩小这些叶增量。平方损失的精确叶值是叶内残差的加权均值；绝对误差的精确叶值是使叶内绝对误差最小的加权中位数。对绝对误差，负梯度在非零残差处是残差符号，零点不可微，具体实现需采用次梯度约定。有限最优值并非对每种损失和每个叶都存在：二分类对数损失中，若一个叶内所有正权重记录都属正类，损失会随 $\gamma\to+\infty$ 持续下降，没有有限的最小值；所有正权重记录都属负类时同理，下降方向是 $\gamma\to-\infty$。

**scikit-learn 1.9.1 的叶更新。** `GradientBoostingRegressor(loss="squared_error")` 中，树叶均值正好是该叶残差均值，平方损失的叶更新是恒等操作，随后乘学习率。`GradientBoostingClassifier(loss="log_loss")` 的二分类叶增量则不是直接把 $y_i-p_i$ 当作 logit 更新：实现对每片叶做一次 Newton–Raphson（牛顿–拉夫森）近似，分子为加权平均伪残差，分母为加权平均二阶导数 Hessian（海森矩阵；本例是标量）$p_i(1-p_i)$：

$$
\gamma_{jm}^{\text{Newton}}=\frac{\sum_{i:x_i\in R_{jm}}v_i(y_i-p_i)}{\sum_{i:x_i\in R_{jm}}v_i p_i(1-p_i)}
$$

这是一轮曲率修正；若有限的叶内最优更新量存在，可以把它理解为对该 $\arg\min$ 的近似。实现还对接近零的加权平均 Hessian 作数值保护，将该叶增量置为 0，避免除法失控。上式按全样本拟合一轮来写；若启用 `subsample < 1`，本轮叶更新的求和只包括被抽中的叶内记录。学习率随后再缩放叶增量。加完叶值后，新输入的分类概率由 $p_m(x)=\sigma(F_m(x))$ 得到。

函数空间梯度下降的一般写法还可把整棵已拟合树视为一个未缩放方向 $h_m$，若该方向上存在有限的最优步长，就沿它做一次全局 line search（线搜索）：

$$
\begin{aligned}
\rho_m&=\arg\min_{\rho}\sum_{i=1}^{n}v_i\ell\bigl(y_i,F_{m-1}(x_i)+\rho h_m(x_i)\bigr),\\
F_m(x)&=F_{m-1}(x)+\eta\rho_m h_m(x)
\end{aligned}
$$

$\eta$ 无量纲，且乘积 $\rho_m h_m(x)$ 必须与 $F$ 同尺度；因此一般损失下 $\rho_m$ 的量纲取决于方向 $h_m$ 的刻度。比如绝对误差回归的负梯度可能只有无量纲的 $\pm1$，而房价预测仍用美元，此时 $\rho_m$ 必须带美元单位。平方损失房价例中 $h_m$ 也以美元计，所以 $\rho_m$ 无量纲。全树线搜索与固定分叶后逐叶求 $\gamma_{jm}^{*}$ 是两种更新选择，不要求同时求两种步长。scikit-learn 1.9.1 二分类 log-loss 实际对每片叶各做一次 Newton 近似，并不先解全树共用的 $\rho_m$；平方损失的房价例则会使全局最优 $\rho_m=1$。减小 $\eta$ 通常需要更多树才能达到类似训练拟合程度，但样本外效果须按数据验证。

> [!example] 从 300,000 美元更新到 305,000 美元
> 下面构造四条合成房价记录，使初始均值、树叶更新和单条预测能完整复算。特征 $x$ 只有两种分组值；目标均以美元计：
>
> | 记录 | 合成特征 $x$ | 房价 $y_i$ | 初始预测 $F_0$ | 平方损失伪残差 $y_i-F_0$ |
> | --- | ---: | ---: | ---: | ---: |
> | A | 0 | 350,000 | 300,000 | +50,000 |
> | B | 0 | 350,000 | 300,000 | +50,000 |
> | C | 1 | 250,000 | 300,000 | −50,000 |
> | D | 1 | 250,000 | 300,000 | −50,000 |
>
> **先确定树怎么分组。** $F_0$ 取目标均值：$(350{,}000+350{,}000+250{,}000+250{,}000)/4=300{,}000$ 美元。深度为 1 的树按 $x\le0.5$ 切分后，A、B 进入左叶，C、D 进入右叶。同一叶内的伪残差都相等，因此两个叶值分别为 $+50{,}000$ 和 $-50{,}000$，叶内残差拟合误差为 0。
>
> **再缩放叶值，更新预测。** 取 $\eta=0.1$；下表金额都以美元计。“下一轮目标”由真实值减去更新后的预测重新计算：
>
> | 叶内记录 | 叶值 $\gamma$ | 实际增量 $0.1\gamma$ | 新预测 $F_1=F_0+0.1\gamma$ | 下一轮目标 $y-F_1$ |
> | --- | ---: | ---: | ---: | ---: |
> | A、B，$x=0$ | +50,000 | +5,000 | 305,000 | +45,000 |
> | C、D，$x=1$ | −50,000 | −5,000 | 295,000 | −45,000 |
>
> 新输入也按同一特征规则落入叶：$x=0$ 得到 305,000，$x=1$ 得到 295,000。树输出的是要加的量，而非新的完整房价。
>
> **最后检查损失，并交给下一轮。** 初始半平方损失为 $4\times\frac12(50{,}000)^2=5.0\times10^9$ 美元平方；更新后残差为 $\pm45{,}000$，损失降为 $4\times\frac12(45{,}000)^2=4.05\times10^9$ 美元平方。因此下一轮拟合的是 $(45{,}000,45{,}000,-45{,}000,-45{,}000)$，不能重复用旧的 $50{,}000$。若将本例整棵树视作方向 $h_m(x)\in\{+50{,}000,-50{,}000\}$，全树平方损失线搜索的最优 $\rho_m=1$，也会得到这组更新值。

二分类梯度提升的树同样输出连续增量：叶值加到 logit 分数 $F_m(x)$，再经 sigmoid 转成概率 $p_m(x)$；它不是把各轮树的类别标签作多数投票。

树深度会改变梯度提升基学习器的表达能力；树数 `n_estimators` 与学习率 `learning_rate` 相互作用。若设置 `subsample < 1`，每轮树只使用一部分训练记录，这通常降低方差但会增加偏差，实际收益要在验证数据上检查。AdaBoost 1.9.1 提供学习率缩放与轮数上限，并在完美拟合时提前停止；`GradientBoostingClassifier` 与 `GradientBoostingRegressor` 还可用 `n_iter_no_change`、`validation_fraction` 配置验证早停。最终应使用符合数据生成过程的验证划分选模型复杂度和轮数，再以独立数据检查泛化误差，训练误差本身不能证明模型对新样本有效。

> [!info]- 来源
> - **经典二分类 AdaBoost 推导与加权投票。** Freund 与 Schapire，*A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting*（1997），[原论文 DOI](https://doi.org/10.1006/jcss.1997.1504)，§4.1 的 AdaBoost 算法及 §4.2 的分析。原文使用 0/1 标签与 beta 更新；本节以 $y,h\in\{-1,+1\}$ 对称编码重写，得到 $\alpha=\frac12\ln((1-\epsilon)/\epsilon)$ 和指数权重更新。
> - **指数损失视角与 SAMME。** Friedman、Hastie 与 Tibshirani，*Additive Logistic Regression: A Statistical View of Boosting*（2000），[原论文 DOI](https://doi.org/10.1214/aos/1016218223)，§4.1–4.2，特别是 Result 1，将离散 AdaBoost 联系到指数损失的加法优化；Zhu 等，*Multi-class AdaBoost*（2009），[作者论文 PDF](https://web.stanford.edu/~hastie/Papers/SII-2-3-A8-Zhu.pdf)，Algorithm 2 给出 SAMME 更新。
> - **当前 AdaBoost API 版本边界。** scikit-learn 1.9.1 [Ensembles 用户指南](https://scikit-learn.org/1.9/modules/ensemble.html#adaboost)，§1.11.7，说明多分类 `AdaBoostClassifier` 实现 SAMME，AdaBoost 按样本权重反复拟合弱学习器并作加权投票；[API 文档](https://scikit-learn.org/1.9/modules/generated/sklearn.ensemble.AdaBoostClassifier.html) 的 `estimator` 与 `n_estimators` 参数说明默认深度 1 的分类树、基分类器须支持样本权重并在完美拟合时停止；固定版本 [`_weight_boosting.py` `_boost`](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_weight_boosting.py#L526-L570) 核对错误阈值 $1-1/K$、首轮阈值错误、完美拟合与 SAMME 权重更新；[`fit` 权重截断与早停](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_weight_boosting.py#L156-L200) 核对每轮机器 epsilon 截断和完美拟合停止；[`decision_function` 分数归一化](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_weight_boosting.py#L658-L671)。核对日期：2026-11-12。
> - **梯度提升通用过程与树叶更新。** Friedman，*Greedy Function Approximation: A Gradient Boosting Machine*（2001），[原论文 DOI / IMS 出版页](https://projecteuclid.org/journals/annals-of-statistics/volume-29/issue-5/Greedy-function-approximation-A-gradient-boosting-machine/10.1214/aos/1013203451.full)，§2 “Numerical optimization in function space” 的泛函梯度和固定方向线搜索、§3 “Finite data” 与 Algorithm 1 的伪响应与逐轮更新、§4.1 “Least-squares regression” 的平方损失残差、§4.3 “Regression trees” 的终端区域逐叶更新、§5 “Regularization” 的学习率与迭代数关系。负梯度用于拟合树方向；固定整树方向作一次线搜索，或固定树叶区域后分别优化各叶增量，是两种更新选择。
> - **当前梯度提升行为。** scikit-learn 1.9.1 [Ensembles 用户指南](https://scikit-learn.org/1.9/modules/ensemble.html#gradient-boosted-trees)，§§1.11.1.2.3–1.11.1.2.6，说明初始常数、负梯度拟合、部分损失的叶值再优化、分类链接函数、学习率缩放与树数相互作用，以及不放回子采样带来的偏差/方差权衡。[`GradientBoostingRegressor` API](https://scikit-learn.org/1.9/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html) 与 [`GradientBoostingClassifier` API](https://scikit-learn.org/1.9/modules/generated/sklearn.ensemble.GradientBoostingClassifier.html) 核对损失、树深度、迭代数与 `n_iter_no_change` / `validation_fraction` 早停参数；固定版本 [`_gb.py` 终端更新](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_gb.py#L190-L271) 核对平方误差叶值恒等更新、入样叶成员选择及二分类 `HalfBinomialLoss` 的逐叶单次 Newton–Raphson 曲率修正；同文件 [`_safe_divide`](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_gb.py#L73-L91) 在分母绝对值低于 $10^{-150}$ 时返回 0；[`_fit_stage`](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/ensemble/_gb.py#L438-L522) 核对负梯度拟合树、调用叶更新与按学习率更新原始预测。理论全树线搜索与逐叶更新是两种实现路线；该版本源码的二分类叶更新不是全树线搜索。核对日期：2026-11-12。
>
> 四个样本的 AdaBoost 权重、初始房价均值、残差、叶节点增量与预测均由正文公式手算复核；没有运行集成器，因此这些数值不是库训练日志。
