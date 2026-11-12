# XGBoost 每轮怎样用正则化目标选择树结构？

预测表格中的一个数值时，当前模型已经给出每行的分数；下一轮要决定两件事：哪些记录应由同一叶节点处理，以及每片叶要给当前分数加多少。XGBoost（Extreme Gradient Boosting，极端梯度提升）用所选 objective（目标函数）的损失对当前分数的一阶、二阶信息，估算候选树对目标的影响，再把叶数和叶分数惩罚纳入比较。

本文追踪一个单输出回归例子：三行记录的当前预测都是 2，目标值是 4、3、1；唯一特征分别为 0、1、2。问题是，按特征条件 $x\le1.5$ 分成两片叶是否值得，以及新树会怎样改变预测。例中的数字是为教学手算而设，不是数据集训练结果。本文先解释这轮计算，再把它接到常见参数、实际切分搜索和缺失值处理。

下图以默认 CPU `hist` 的一轮建树为例。新子叶仍须重新汇总和评分；没有可扩展叶时，本轮输出更新后的分数，下一轮再以新分数计算导数。

~~~mermaid
flowchart TD
    A["当前分数 Fₜ₋₁(xᵢ)"] --> B["目标函数给出逐行 gᵢ、hᵢ"]
    B --> C["候选分区汇总各叶 Gⱼ、Hⱼ"]
    C --> D["二阶近似与正则项估计叶值和分裂分数"]
    D --> E{"有候选通过约束和分数门槛？"}
    E -- 有 --> G["按生长策略选切分，生成待评估子叶"]
    G --> C
    E -- 没有 --> F["本轮建树停止<br/>叶值乘 η 后加到当前分数"]
~~~

这里聚焦普通树提升器 **gbtree** 的单输出标量情形，并设每轮只构造一棵树，即 **num_parallel_tree=1**；**dart** 的树丢弃更新、线性提升器、多输出树及类别型切分不属于这条推导。训练数据有 $n$ 行、$p$ 个数值特征；每行输入 $x_i\in\mathbb R^p$，目标 $y_i\in\mathbb R$，当前分数 $F_{t-1}(x_i)\in\mathbb R$。后文所有逐行求和均对 $i=1,\ldots,n$ 进行。单输出加法模型可写为

$$
F_{t-1}(x)=F_0(x)+\sum_{s=1}^{t-1}\eta f_s(x)
$$

$F_0$ 是初始分数，$f_s(x)$ 是第 $s$ 轮树给出的、尚未乘学习率的叶值，$\eta$ 是无量纲学习率。本文从已知的当前分数开始，暂不展开初始分数怎样估计。分类输出依目标函数而异；后文以 **binary:logistic** 说明 sigmoid（逻辑函数）如何把原始分数转成概率，并指出 **binary:logitraw** 保留变换前的分数。

## 从损失导数得到叶节点增量

令 $F_{t-1}(x_i)$ 表示第 $t$ 轮开始前，模型对第 $i$ 行的当前标量输出。它来自初始分数与前面各轮树的累加。树提升会给当前值加一个新函数 $f_t(x_i)$，所以本轮尚未乘学习率的候选输出是 $F_{t-1}(x_i)+f_t(x_i)$。

对每行损失在当前分数附近作二阶 Taylor expansion（泰勒展开）：

$$
\ell\bigl(y_i,F_{t-1}(x_i)+f_t(x_i)\bigr)
\approx
\ell\bigl(y_i,F_{t-1}(x_i)\bigr)
+g_i f_t(x_i)
+\frac12 h_i f_t(x_i)^2
$$

其中

$$
g_i=\left.\frac{\partial\ell(y_i,F)}{\partial F}\right|_{F=F_{t-1}(x_i)},
\qquad
h_i=\left.\frac{\partial^2\ell(y_i,F)}{\partial F^2}\right|_{F=F_{t-1}(x_i)}
$$

$g_i$ 是 gradient（梯度），描述当前分数处损失随分数增加的斜率；$h_i$ 是 Hessian（海森矩阵；本例标量输出时就是二阶导数），描述局部曲率。它们是由当前分数、标签和所选损失算出的训练统计量，不是输入特征。目标值和分数是标量；本例的 $g_i,h_i$ 也都是标量。若损失带样本权重，相应权重会进入导数统计量。下文按直接使用损失一、二阶导数的情形推导；实现也可能为特定目标提供近似梯度或曲率。

> [!info] 两阶导数怎样估计改动的效果？
> 沿用第一行 $y=4,F=2$，半平方损失为 $2$，当前 $g=-2,h=1$。若给预测加 $\delta=0.1$，一阶项估计损失变化 $-2\times0.1=-0.2$，二阶项补上 $\frac12\times1\times0.1^2=0.005$，合计新损失 $2-0.2+0.005=1.805$。本例损失恰为二次式，结果与直接代入 $\frac12(4-2.1)^2$ 一致；一般损失这里只是局部近似。

> [!info]- 哪些目标会使用近似曲率？
> 例如 3.4.2 的 **reg:absoluteerror** 使用 pseudo-Huber（伪 Huber）平滑近似，并把 majorization curvature（主化曲率）作为 Hessian 输入；该曲率既不是绝对误差目标的精确二阶导数，也不是相应伪 Huber 目标的精确 Hessian。

将与新树无关的第一项略去后，树要降低的近似目标为

$$
\widetilde{\mathcal L}^{(t)}
=
\sum_i\left[g_i f_t(x_i)+\frac12h_i f_t(x_i)^2\right]
+\Omega(f_t)
$$

这只是当前分数附近的局部二阶近似；它不表示后续轮次的完整损失都恰好是二次函数。若当前树把输入分到 $T$ 个叶，$q(x_i)$ 表示记录 $i$ 被分到的叶编号，$w_j$ 是叶 $j$ 给分数增加的标量值，则

$$
f_t(x_i)=w_{q(x_i)},
\qquad
\Omega(f_t)=\gamma T+\frac12\lambda\sum_{j=1}^{T}w_j^2+\alpha\sum_{j=1}^{T}|w_j|
$$

$\Omega$ 是树的复杂度惩罚：$\gamma$ 按叶数收费，$\lambda$ 是 L2 regularization（L2 正则化）系数，惩罚叶值的平方；$\alpha$ 是 L1 regularization（L1 正则化）系数，惩罚叶值的绝对值。令 $I_j=\{i:q(x_i)=j\}$，把同一叶中的导数相加为

$$
G_j=\sum_{i\in I_j}g_i,
\qquad
H_j=\sum_{i\in I_j}h_i
$$

$G_j,H_j$ 分别是叶 $j$ 的梯度和与 Hessian 和，二者均为标量。固定树的分区后，本轮目标就能按叶拆开：

$$
\widetilde{\mathcal L}^{(t)}
=
\sum_{j=1}^{T}
\left[
G_jw_j+\frac12(H_j+\lambda)w_j^2+\alpha|w_j|
\right]+\gamma T
$$

因此，给定一个分区后，每片叶可分别求使局部目标最小的输出。先令 $\alpha=0$，并假设 $H_j+\lambda>0$。对关于 $w_j$ 的二次式求导并令结果为零：

$$
\frac{\partial}{\partial w_j}
\left[G_jw_j+\frac12(H_j+\lambda)w_j^2\right]
=G_j+(H_j+\lambda)w_j=0
$$

得到最优叶增量

$$
w_j^*=-\frac{G_j}{H_j+\lambda}
$$

若 $G_j<0$，增量为正；若 $G_j>0$，增量为负。L2 惩罚 $\lambda$ 增大分母，因而会收缩叶值。把 $w_j^*$ 代回目标，叶带来的最优局部目标下降为 $\frac12G_j^2/(H_j+\lambda)$。有 L1 惩罚时，用 soft-thresholding（软阈值处理）函数

$$
S_\alpha(G)=\operatorname{sign}(G)\max(|G|-\alpha,0)
$$

替换梯度和，得到 $w_j^*=-S_\alpha(G_j)/(H_j+\lambda)$。当 $|G_j|\le\alpha$ 时，这片叶的最优增量为零。

## 比较一次候选分裂

在当前分区下，若一个父叶被分成左右两个子叶，父叶和子叶各自都能选择自己的最优增量。把两子叶相对父叶多得到的局部目标下降，再扣掉新添的一个叶所付的 $\gamma$，就是论文目标的分裂增益：

$$
\operatorname{Gain}
=
\frac12\left[
\frac{G_L^2}{H_L+\lambda}
+\frac{G_R^2}{H_R+\lambda}
-\frac{(G_L+G_R)^2}{H_L+H_R+\lambda}
\right]-\gamma
$$

此式适用于 $\alpha=0$、$H+\lambda>0$，且叶权重不受额外约束的情形：实现中对应 **max_delta_step=0**，并且没有单调约束。若使用 L1 惩罚，三个分子分别换成对应梯度和的 $S_\alpha(\cdot)^2$。正增益意味着这次分裂在该局部近似目标和参数下值得考虑；它不是验证集准确率，也不保证样本外误差下降。正的 max_delta_step 会截限叶值，单调约束也可能限制叶值或使候选切分无效，因此这两种设置下实现的评分不能直接套用此闭式式子。

现在沿开头的合成例子复算。单行损失取 $\ell=\frac12(y-F)^2$，当前分数 $F=2$。因此 $g=F-y$、$h=1$。候选条件 $x\le1.5$ 将前两行放入左叶，第三行放入右叶。手算参数取 $\lambda=1,\gamma=0.2,\alpha=0$。

> [!example] 三行记录从梯度走到新预测
> | 行 | 特征 $x$ | 当前分数 $F$ | 目标 $y$ | $g=F-y$ | $h$ | 候选叶 |
> | --- | ---: | ---: | ---: | ---: | ---: | --- |
> | 1 | 0 | 2 | 4 | $-2$ | 1 | 左 |
> | 2 | 1 | 2 | 3 | $-1$ | 1 | 左 |
> | 3 | 2 | 2 | 1 | $+1$ | 1 | 右 |
>
> 汇总得左叶 $G_L=-3,H_L=2$，右叶 $G_R=1,H_R=1$，父叶 $G_P=-2,H_P=3$。三个叶增量候选为
>
> $$
> w_L^*=-\frac{-3}{2+1}=1,\qquad
> w_R^*=-\frac{1}{1+1}=-0.5,\qquad
> w_P^*=-\frac{-2}{3+1}=0.5
> $$
>
> 论文尺度下的分裂增益是
>
> $$
> \frac12\left(\frac{9}{3}+\frac{1}{2}-\frac{4}{4}\right)-0.2
> =\frac12(3+0.5-1)-0.2
> =1.05
> $$
>
> 为说明建树如何继续，根节点上另一个候选是 $x\le0.5$，它把 $x=0$ 与 $x=1,2$ 分开。下表列出两种根切分及已选切分的左叶再分一次的结果：
>
> | 所在节点 | 教学分区 | 论文目标净增益 | 3.4.2 实现候选分数 `loss_chg` |
> | --- | --- | ---: | ---: |
> | 根 | $x\le0.5$：$\{0\}\mid\{1,2\}$ | $0.30$ | $1.0$ |
> | 根 | $x\le1.5$：$\{0,1\}\mid\{2\}$ | $1.05$ | $2.5$ |
> | 左叶 $\{0,1\}$ | $x\le0.5$：$\{0\}\mid\{1\}$ | $-0.45$ | $-0.5$ |
>
> 根节点在两种口径下都选择第二刀，因为它的增益或候选分数更高。表中论文净增益按 $\tfrac12[\text{子叶收益和}-\text{父叶收益}]-\gamma$ 计算；实现候选分数按“子叶收益和减父叶收益”计算，还要与最低分门槛 **min_split_loss** 比较。因此两列的数值不直接比较。选定根切分后，左叶再切的分数为负，不再扩展；右叶只有 $x=2$ 一行，没有可用的不同特征值切点。至此教学树停在两片叶。若 **min_child_weight=2**，两个根候选都因有一侧 $H=1$ 而不合格。
>
> 这里的 $x\le0.5$ 和 $x\le1.5$ 是为了说明行如何分组的数学条件，不代表模型必定保存相同数值的阈值。3.4.2 的数值节点按 $\text{feature}<\text{split\_condition}$ 路由，特征值等于阈值时走右分支；缺失值走节点记录的默认子节点。直方图方法使用分箱边界形成候选阈值。
>
> 根节点所选切分为正，所以按这组教学参数，它优于不分裂。若 learning rate（学习率）$\eta=0.1$，实际加入模型的叶增量是 $+0.1$ 和 $-0.05$，不是完整的 $+1$ 和 $-0.5$。新分数分别为左侧两行 $2.1$、右侧一行 $1.95$。半平方损失从 $3$ 个目标单位平方降到
>
> $$
> \frac12\left[(4-2.1)^2+(3-2.1)^2+(1-1.95)^2\right]=2.66125
> $$
>
> 这是本例更新后按定义算出的训练损失，不是树增益，也不是库运行值。$F,y,w$ 都用目标单位；本例的 $g,G$ 也用目标单位，$h,H,\lambda$ 无量纲，$\alpha$ 用目标单位，$\gamma$ 用目标单位的平方，因此目标函数各项量纲一致。

论文公式中的二分之一容易与库实际使用的切分分数混淆。XGBoost 3.4.2 在默认的 **max_delta_step=0**、$\alpha=0$ 、无单调约束且 $H>0$ 时，树源码的无约束叶收益计算为 $G^2/(H+\lambda)$，没有论文公式前面的 $1/2$；切分候选分数将两个子叶收益相加，再减去父叶收益。沿用上例的 $G,H,\lambda$，源码尺度的候选分数为 $3+0.5-1=2.5$。论文手算净增益 $1.05$ 解释推导，候选分数 $2.5$ 用于说明实现门槛；两套数值不能直接混比。实现对 $H\le0$ 的叶收益直接返回零；候选左右子叶也都必须有正的 $H$，并分别达到 `min_child_weight`，才能继续比较切分分数。

在 3.4.2 默认 **tree_method=auto** 的 CPU 路径中，**auto** 选择 **hist**。直方图建树会在扩展候选时检查 **min_split_loss**（别名 $\gamma$）：低于门槛的切分不会长成节点；本例所选候选分数 $2.5$ 高于 $\gamma=0.2$。这条路径不应概括成“先长出树再剪枝”。若选择 **exact**，其更新器（updater）序列是 `grow_colmaker,prune`；后续 `prune` 在子节点均为叶时检查已长出的切分，并移除低于最低分门槛的切分。若 $\alpha>0$、使用叶值上限或单调约束，候选收益及可行性也会相应改变。

## 公式中的量怎样映射到参数？

同一分裂公式说明了常见参数各自控制哪一环。结构限制和目标惩罚不是一回事：树的深度或叶数限制允许搜索到的形状；$\gamma,\lambda,\alpha$ 则直接出现在局部目标或其实现的分裂准则中。

| 参数 | 作用在本轮的哪一步 | 阅读结果时要看什么 |
| --- | --- | --- |
| **booster** | 选择模型类型；本文推导针对树提升器 **gbtree** | **dart** 会丢弃并重新缩放部分旧树；线性提升器 **gblinear** 使用不同机制，3.4.2 文档已将它标为弃用 |
| **objective** | 由任务损失产生每行 $g_i,h_i$，也决定预测分数如何变成任务输出 | 损失是否符合目标和输出语义；**binary:logistic** 在原始分数上逐树相加，再经 sigmoid（逻辑函数）转成概率 |
| **learning_rate / eta** | 将选定树的叶值乘以步长后加到当前分数 | 较小步长使每轮更新更小，往往需要更多轮；用验证集检查效果 |
| **n_estimators** | Python 的 XGBRegressor / XGBClassifier 包装器请求的提升轮数 | 这是轮数，不等于任何配置下的总树数；early stopping（提前停止）会提前结束训练 |
| **max_depth、max_leaves、grow_policy** | 限定单棵树形状和扩展节点的次序 | 深度和叶数增加表达能力，也增加过拟合与资源消耗风险。**grow_policy** 只用于 **hist**、**approx**；**exact** 要求 **max_depth>0**，且不使用 **max_leaves** |
| **min_child_weight** | 要求候选子节点的 Hessian 总和至少达到阈值 | 大值会抑制低曲率统计量的细分；平方损失且无样本权重时 $h_i=1$，这时 $H$ 才等于行数。本例若设为 2，任一根候选都有一侧 $H=1$，因此都会被拒绝 |
| **gamma / min_split_loss** | 设定继续切分所需的最小增益 | 越大越保守；它的数值要按目标函数与实现的增益尺度解释 |
| **reg_lambda / lambda** | 叶值的 L2 惩罚，出现在 $H+\lambda$ 中 | 增大后叶值收缩 |
| **reg_alpha / alpha** | 叶值的 L1 惩罚，通过软阈值处理梯度和 | 足够大的 $\alpha$ 可把叶增量压到零 |
| **max_delta_step** | 限制每个叶估计的分数更新幅度 | 默认 0 表示不施加这个上限；正值使叶更新更保守 |
| **subsample、colsample_bytree / colsample_bylevel / colsample_bynode** | 对建树所见的样本行或特征列作抽样 | 可以改变计算量与树间相关性，也会引入随机性；需在验证数据上判断。**colsample_bynode** 不支持 **exact** |
| **tree_method、max_bin** | 选择如何生成并评估候选切点 | 更细的分箱可能增加切分候选精度和计算成本，实际取舍依数据而定 |

XGBoost 提供不同 booster（提升器）和输出策略。在常见单输出、每类单独建树的多分类配置中，一个提升轮次可包含多棵树；**num_parallel_tree** 也可在每轮构造多棵树。因此计数应按提升器、输出策略和并行树配置理解，而不是把轮数直接当树数。

这些参数的数值不是跨目标通用的阈值：换损失会改变导数；改变目标计量单位也会改变导数和增益尺度。比如本例里 $\lambda$ 与 Hessian 同量纲，$\alpha$ 与梯度同量纲，$\gamma$ 与目标函数同量纲。调参时先确认目标函数及输出含义，再用符合数据生成过程的验证切分比较目标损失、稳定性和资源使用；训练增益不能替代样本外检验。feature importance（特征重要性）中的 gain、weight、cover 等是模型按相应统计口径使用特征的摘要，不能单独作为特征具有因果作用的证据。

## 候选切点、稀疏数据与缺失值

上述推导告诉我们如何给一个候选分区打分，但实际树不是一次枚举所有整棵树后选全局最优。以下搜索次序与建树前门槛以 3.4.2 默认 CPU **hist** 为例：对每片待扩展叶，XGBoost 比较可用的特征与切点，在约束允许的候选中选择评分最高者；应用为节点前，先检查 Hessian、最低切分分数、深度和叶数限制。通过的切分产生子叶，子叶重新汇总梯度与 Hessian 后，再按 **grow_policy** 继续搜索。没有可扩展候选时停止。**exact** 的 `min_split_loss` 检查发生在建树后的 `prune` 阶段，前文已单独说明。候选集合如何生成取决于树方法。

XGBoost 3.4.2 的文档列出 **exact**、**approx** 和 **hist** 三种 tree method（树构造方法）。**exact** 在当前数据条目上枚举可用切分点，计算更慢，且不支持所有近似方法可用的分布式和外存能力；**approx** 对每棵树用 Hessian 加权的分位数草图生成候选，再构建梯度直方图；**hist** 先以用户提供的样本权重作全局草图，再为节点建直方图，通常更快。**max_bin** 限制直方图或近似方法中连续特征可分入的离散箱数。精确和近似描述的是候选搜索方式，二阶目标的叶值推导仍适用。

原始 XGBoost 论文还把可扩展训练系统作为贡献：sparsity-aware split finding（稀疏感知切分搜索）只扫描非缺失条目，并为缺失值比较左右默认方向；weighted quantile sketch（加权分位数草图）支持近似切分点；column block layout（列块布局）、cache access optimization（缓存访问优化）、compression（压缩）和 sharding（分片）则服务于并行、分布式或外存训练。这些是算法与系统设计，不等于在任意数据上都能提高精度。

树提升器可以在训练时为切分学习缺失值默认方向。这是让缺失记录走一条已选的分支，不是替它填入了一个观测值；默认缺失标记是 NaN，也可以通过 **missing** 指定其他标记。稀疏矩阵中未存储的条目对树提升器按缺失处理，因此在默认设置下，稠密矩阵里的数值 0 仍是有效特征值。线性提升器 **gblinear** 对缺失值按零处理；XGBoost 3.4.2 文档已将该 booster 标为弃用，不能把这条规则推广到树模型。

对于二分类，树的叶值仍然是加到当前原始分数上的增量。以输出概率的 **binary:logistic** 为例，若当前原始分数是 $F_t(x)$，概率为

$$
p_t(x)=\sigma(F_t(x))=\frac{1}{1+\exp(-F_t(x))}
$$

所以该目标不是让每棵树投一个类别票；它逐轮改变 logit（对数几率）分数，再由 sigmoid 给出概率。**binary:logitraw** 使用逻辑损失但输出逻辑变换前的分数。对于平方损失回归，输出通常直接处于目标单位。

> [!info]- 来源
> - **二阶目标、叶值闭式解与分裂增益。** Chen 与 Guestrin，*XGBoost: A Scalable Tree Boosting System*（KDD 2016；arXiv v3 于 2016-06-10 修订），[论文原文](https://arxiv.org/pdf/1603.02754)，§2、§3.1–3.4。论文给出当前损失的二阶近似、树复杂度惩罚、叶值解、分裂增益和稀疏感知切分算法；本文算例使用相同的二阶目标形式。
> - **教学算例采用的平方损失导数。** XGBoost 3.4.2 固定版本源码 [reg:squarederror 的梯度与 Hessian](https://github.com/dmlc/xgboost/blob/v3.4.2/src/objective/regression_loss.h#L13-L28) 为 $g=F-y,h=1$，与正文所用半平方损失一致。算例的特征、目标和参数为合成教学值，梯度、叶增量、分裂增益、学习率更新及新损失均由正文公式独立手算；没有运行 XGBoost 拟合。
> - **叶值、实现收益与约束。** XGBoost 3.4.2 [子叶有效性、CalcWeight、CalcGain 与 L1 阈值](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/param.h#L216-L280)核对正 Hessian、子叶门槛、叶值和无约束收益；[分裂评估器](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/split_evaluator.h#L186-L212)核对子叶收益相加、单调约束下的可行性与评分；[直方图候选评分](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/hist/evaluate_splits.h#L236-L258)核对减去父叶收益。固定标签源码 v3.4.2。
> - **最低切分分数的两条实现路径。** `gamma` 是 `min_split_loss` 的别名，见 [参数声明与 NeedPrune](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/param.h#L178-L188)。默认 **auto** 映射到直方图建树、**exact** 映射到 `grow_colmaker,prune`，见 [树方法映射](https://github.com/dmlc/xgboost/blob/v3.4.2/src/gbm/gbtree.cc#L44-L63)；hist 扩展入口的 [候选有效性检查](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/driver.h#L30-L46) 和 [逐轮生成并评估子叶](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/updater_quantile_hist.cc#L99-L145)；exact 的 [后续剪枝条件](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/updater_prune.cc#L56-L74)。固定标签源码 v3.4.2。
> - **树约束边界与实际路由。** [树提升器参数文档](https://xgboost.readthedocs.io/en/stable/parameter.html#parameters-for-tree-booster)说明 grow_policy、max_leaves、colsample_bynode 的适用范围；固定版本的 [exact 生长器](https://github.com/dmlc/xgboost/blob/v3.4.2/src/tree/updater_colmaker.cc#L174-L182)要求正的 max_depth；[数值特征路由](https://github.com/dmlc/xgboost/blob/v3.4.2/src/predictor/predict_fn.h#L16-L34)按 `feature < split_condition` 判定。稳定版文档于 2026-11-12 核对，文档版本为 XGBoost 3.4.2。
> - **近似曲率的目标例外。** [reg:absoluteerror 的平滑上界梯度与曲率](https://github.com/dmlc/xgboost/blob/v3.4.2/src/objective/regression_obj.cu#L854-L865)注明其 Hessian 使用 majorization curvature，而非 pseudo-Huber 精确 Hessian。固定标签源码 v3.4.2。
> - **Python 包装器的轮数和早停。** 3.4.2 稳定版 [XGBRegressor API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor)与 [XGBClassifier API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier)核对 `n_estimators` 的提升轮数语义及 `early_stopping_rounds` 的验证集条件。于 2026-11-12 查阅。
> - **切分候选算法。** XGBoost 3.4.2 [Tree Methods](https://xgboost.readthedocs.io/en/stable/treemethod.html) 中 exact、approx、hist 的算法描述和适用边界；[参数说明](https://xgboost.readthedocs.io/en/stable/parameter.html) 中 max_bin 定义。于 2026-11-12 核对。
> - **缺失和稀疏输入。** XGBoost 3.4.2 [FAQ：缺失值](https://xgboost.readthedocs.io/en/stable/faq.html#how-to-deal-with-missing-values)说明树学习缺失方向、默认 NaN 与 gblinear 规则；[FAQ：稀疏与稠密输入差别](https://xgboost.readthedocs.io/en/stable/faq.html#why-do-i-see-different-results-between-sparse-and-dense-data)说明稀疏树输入的未存储元素按缺失处理。于 2026-11-12 核对。
> - **原始分数到概率。** 同版 [目标参数](https://xgboost.readthedocs.io/en/stable/parameter.html#learning-task-parameters)区分 binary:logistic（输出概率）与 binary:logitraw（输出逻辑变换前分数）；3.4.2 [逻辑目标源码](https://github.com/dmlc/xgboost/blob/v3.4.2/src/objective/regression_loss.h#L55-L90)核对 sigmoid 预测变换。于 2026-11-12 按稳定版 XGBoost 3.4.2 核对。
> - **特征重要性字段。** [XGBRegressor API 的 feature_importances_ 属性](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor.feature_importances_)说明值随 importance_type 而变化。正文将 gain、weight、cover 视作拟合模型的使用摘要，并据此说明它们本身不提供因果证据。
