# Ridge regression（岭回归）、Lasso（套索回归）与 Elastic Net（弹性网络）怎样改变线性模型？

估算房屋能耗时，面积、房间数和建筑体积可能彼此相关。ordinary least squares（普通最小二乘）会为每个特征拟合系数，但高度相关的特征容易使系数对样本变化敏感。Ridge、Lasso 和 Elastic Net 都在拟合误差之外惩罚系数；它们对系数的处理不同，因此适合回答不同的问题。

## 从一个目标函数看三种惩罚

先使用一个常见的平方误差归一化约定：

$$
J(\beta_0,\beta)=
\frac{1}{2n}\sum_{i=1}^n
(y_i-\beta_0-x_i^\top\beta)^2
+\lambda_1\lVert\beta\rVert_1
+\frac{\lambda_2}{2}\lVert\beta\rVert_2^2
$$

**截距** $\beta_0$ 不在惩罚项中。第一项衡量训练样本的拟合误差；L1 penalty（L1 惩罚）项是系数绝对值之和；L2 penalty（L2 惩罚）项是系数平方和。惩罚强度越大，模型越不愿意用很大的系数解释训练数据。

- **Ridge**：$\lambda_1=0,\lambda_2>0$。通常把系数连续缩小，但一般不会把系数精确压到零。
- **Lasso**：$\lambda_1>0,\lambda_2=0$。绝对值惩罚有尖点，可能把部分系数压到精确的零，形成稀疏模型。
- **Elastic Net**：两项都大于零。它结合稀疏选择和连续收缩；对强相关预测变量，L2 部分可促进成组选择，但不保证每个数据集都稳定。

> [!info] 为什么系数要先放到可比较的尺度？
> 惩罚直接作用于系数。若一个特征以米表示、另一个以毫米表示，同一实际变化对应的系数大小会差很多，惩罚便会受到计量单位影响。标准化通常在训练折中估算均值和标准差，再把相同变换用于验证折。若在全数据上先估算标准化参数，验证集的信息会提前进入训练流程。

## 用两条合成观测手算系数

取一个已经居中且标准化的特征，观测为 $x=(-1,+1)$，目标为 $y=(-3,+3)$。因此截距为 0；令系数为 $\beta$，上面的归一化损失可化为：

$$
J(\beta)=\frac12(3-\beta)^2
+\lambda_1|\beta|
+\frac{\lambda_2}{2}\beta^2
$$

| 方法 | 本例的惩罚强度 | 最优系数 |
| --- | --- | ---: |
| Ridge | $\lambda_1=0,\lambda_2=1$ | $\beta=1.5$ |
| Lasso | $\lambda_1=1,\lambda_2=0$ | $\beta=2$ |
| Elastic Net | $\lambda_1=1,\lambda_2=1$ | $\beta=1$ |

可以逐项复算：

- Ridge 在本例中对 $\beta$ 求导，令 $\beta-3+\beta=0$，得到 $1.5$。
- Lasso 的最优点为正，因此在正半轴令导数 $\beta-3+1=0$，得到 $2$。在这组数据上，未惩罚平方损失在 $\beta=0$ 处的导数为 $-3$，而 L1 项在零处允许的次梯度范围为 $[-\lambda_1,\lambda_1]$；当 $\lambda_1\ge3$ 时，该范围包含 $+3$，可以抵消平方损失的斜率，因此最优系数为 $\beta=0$。
- Elastic Net 的正半轴导数为 $\beta-3+1+\beta$，令它为零得到 $1$。

这组小数据只隔离了目标函数的作用，不是模型选择建议。实际效果要用样本外误差、变量相关结构和业务需要来判断。

## 把惩罚强度与 scikit-learn 参数对应

scikit-learn 1.9.1 的几个估计器采用的目标函数归一化方式不完全相同。因此不同类中的参数即使数字相同，也不代表相同的惩罚强度。

在上述目标记号下：

- Lasso 的 API 中 alpha 对应 $\lambda_1$。
- Elastic Net 中 alpha × l1_ratio 对应 $\lambda_1$；alpha × (1-l1_ratio) 对应 $\lambda_2$。
- Ridge API 写作未归一化平方误差 $\lVert y-X\beta\rVert^2+\text{alpha}\lVert\beta\rVert^2$。将它除以 $2n$ 后，和本页记号对应为 $\lambda_2=\text{alpha}/n$。

估计器默认会拟合截距，且截距不加入系数惩罚；若关闭 fit_intercept，输入应先按 API 约定居中。先明确目标函数，再比较不同类的参数，避免把不同尺度的 alpha 当作同一数值。

## 按数据结构选择验证方式

普通随机 cross-validation（交叉验证）会把样本打乱或分折。在预测未来销量、负载或价格时，这可能让训练折含有比验证折更晚的信息，造成不符合部署时间方向的评估。

交叉验证的具体流程应与预测时点相同：对时间序列按时间排序，每一折用过去训练、紧接着的未来验证；标准化器必须在每一折的训练数据上拟合，再转换该折的验证数据。scikit-learn 的 TimeSeriesSplit 用扩展的历史训练集验证后续区间；其文档要求样本等间隔，才能让各折验证区间长度可比。若业务时间戳不规则，应按实际日历窗口定义分折，而不要把行数相同误称为覆盖了相同时间。

调参时可比较多组 $\lambda$ 或 Elastic Net 的两项惩罚，检查各时间折的误差和系数稳定性，再用完全未参与调参的末段数据做最终检查。

| 数据与目标 | 可以从哪种惩罚开始比较 | 需要检查什么 |
| --- | --- | --- |
| 多数特征都有用，但相关性较高 | Ridge | 系数收缩后预测误差是否下降 |
| 需要稀疏表示或减少输入变量 | Lasso | 高相关特征间选择是否随训练折改变 |
| 相关特征可能共同携带信号，且也需要稀疏性 | Elastic Net | 成组效果是否在验证折中复现 |
| 目标来自未来时点 | 以上任一种都可比较，但用时间顺序验证 | 不让未来信息参与预处理或调参 |

Lasso 选中的变量不是因果因素，也不必然是唯一重要特征；当多个特征高度相关时，训练样本稍变就可能换一个变量代表同一信号。若选择会影响后续决策，应报告稳定性并用领域知识复核，而不是只读一份非零系数清单。

> [!info]- 来源
> - Ridge、Lasso、Elastic Net 的目标函数、截距和参数定义：scikit-learn 1.9.1 [Ridge API](https://scikit-learn.org/1.9/modules/generated/sklearn.linear_model.Ridge.html)、[Lasso API](https://scikit-learn.org/1.9/modules/generated/sklearn.linear_model.Lasso.html)、[ElasticNet API](https://scikit-learn.org/1.9/modules/generated/sklearn.linear_model.ElasticNet.html)，2026-11-06 核对目标函数与 fit_intercept。
> - 尺度和防止预处理泄漏：[StandardScaler API](https://scikit-learn.org/1.9/modules/generated/sklearn.preprocessing.StandardScaler.html) 与 [常见陷阱：数据泄漏](https://scikit-learn.org/1.9/common_pitfalls.html)，同日核对。
> - 时间顺序交叉验证的训练/验证次序及等间隔前提：[TimeSeriesSplit API](https://scikit-learn.org/1.9/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)，同日核对。
> - 原始方法依据：Hoerl 与 Kennard，*Ridge Regression: Biased Estimation for Nonorthogonal Problems*（1970），[DOI](https://doi.org/10.1080/00401706.1970.10488634)；Tibshirani，*Regression Shrinkage and Selection via the Lasso*（1996），[DOI](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x)；Zou 与 Hastie，*Regularization and Variable Selection via the Elastic Net*（2005），[DOI](https://doi.org/10.1111/j.1467-9868.2005.00503.x)。弹性网络的成组效应须在该论文的标准化设计和惩罚条件下理解。
> - 示例系数由目标函数独立求解并复算；未调用 scikit-learn 运行拟合，也未将手算值说成库输出。
