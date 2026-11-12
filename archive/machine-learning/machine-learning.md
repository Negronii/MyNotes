# 树模型、正则化与 XGBoost 资料入口

挂牌估价可以串起这里的三类问题：树怎样把房屋分到预测区域；提升怎样利用已有预测构造下一轮的调整；正则化怎样限制模型参数。下面的阅读顺序从分叶走到逐轮更新，再到 XGBoost 的树目标。各章用不同的合成数据，读者沿着概念和量的角色继续读，不需要把它们当成同一张训练表。合成算例说明计算机制；实际效果仍需用独立数据检验，模型使用了某个特征也不能单独建立因果关系。

## 房价回归主线：从叶预测到逐轮调整

1. 先读 [Decision tree（决策树）如何在分类与回归中选分裂？](decision-tree-split-criteria.md#%E5%9B%9E%E5%BD%92%E4%BB%BB%E5%8A%A1%EF%BC%9A%E6%AF%94%E8%BE%83%E8%8A%82%E7%82%B9%E5%86%85%E6%95%B0%E5%80%BC%E8%AF%AF%E5%B7%AE) 的“回归任务”段。它用四条记录的目标值 10、12、20、22 比较数值特征 B 的阈值。切在 $B\le2.5$ 时，根节点的 mean squared error（均方误差，MSE）从 26 降到按样本比例加权的子节点 MSE 1；新记录 $B=3$ 走到右叶，得到该叶的完整预测 21。B 可以对应面积这类连续数值特征。分类树也复用分叶过程；目标章节的分类例按叶内样本权重占比最大的类给出类别预测。

2. 再读 [AdaBoost 与 Gradient Boosting（梯度提升）怎样逐轮改变预测？](adaboost-and-gradient-boosting-updates.md#Gradient%20Boosting%EF%BC%9A%E4%B8%8B%E4%B8%80%E6%A3%B5%E6%A0%91%E8%AF%A5%E6%8B%9F%E5%90%88%E4%BB%80%E4%B9%88%EF%BC%9F) 的 Gradient Boosting 段。该章另用四条合成房价记录：特征 $x=0$ 的两条房价是 350,000 美元，$x=1$ 的两条是 250,000 美元；目标均值为 300,000 美元，作为初始预测。其中一条真实房价为 350,000 美元，当前预测低了 50,000 美元。半平方损失对当前预测的梯度是 $-50{,}000$ 美元，负梯度（伪残差，在半平方损失下等于真实值减当前预测）是 $+50{,}000$ 美元。拟合这组信号的树在对应叶给出 $+50{,}000$ 美元的调整；乘学习率 0.1 后，模型加上 $+5{,}000$，新预测为 305,000 美元。另一组记录得到 295,000 美元；下一轮这两组伪残差分别为 $+45{,}000$ 与 $-45{,}000$ 美元。

   单棵回归树的叶值是该区域的房价预测；提升树的叶值是加到当前预测上的调整。阅读顺序先建立分叶规则，提升模型每轮的当前预测则由初始值和已加入的学习器累加而来。

3. 最后读 [XGBoost 每轮怎样用正则化目标选择树结构？](xgboost-objective-and-parameters.md)。这篇另用三条易手算的记录：当前预测都是 2，目标值是 4、3、1。输入状态已知后，问题是哪些记录应进入同一叶、每片叶加多少。对每条记录，固定真实值 $y_i$，把损失看作当前标量预测 $F_i$ 的函数；一阶导数是损失随 $F_i$ 变化的斜率，二阶导数描述曲率。它们是对当前预测求导，不是对特征或树参数求导；单输出时每行的这两个量都是标量。给定候选分区后，L1/L2 叶值惩罚参与求各叶的调整，叶数惩罚参与比较切分；选定树结构后，再由学习率缩放叶值并更新预测。公式与三行计算见该章。

## 按需阅读的两条支线

- 想对照“下一轮学习器怎样获得关注重点”时，读 [AdaBoost 与 Gradient Boosting（梯度提升）怎样逐轮改变预测？](adaboost-and-gradient-boosting-updates.md#AdaBoost%EF%BC%9A%E9%94%99%E5%88%86%E6%A0%B7%E6%9C%AC%E5%A6%82%E4%BD%95%E5%8F%98%E9%87%8D%EF%BC%9F) 的 AdaBoost 段。该段以二分类和加权投票为例，适合与连续房价主线作机制对照。AdaBoost 也有回归扩展；scikit-learn 1.9.1 的 `AdaBoostRegressor` 实现 AdaBoost.R2。
- 需要线性基线，或要理解相关特征如何影响系数时，读 [Ridge regression（岭回归）、Lasso（套索回归）与 Elastic Net（弹性网络）怎样改变线性模型？](ridge-lasso-and-elastic-net.md#%E4%BB%8E%E4%B8%80%E4%B8%AA%E7%9B%AE%E6%A0%87%E5%87%BD%E6%95%B0%E7%9C%8B%E4%B8%89%E7%A7%8D%E6%83%A9%E7%BD%9A)。该章用楼宇能耗和相关特征说明普通最小二乘系数为何可能不稳定：Ridge 收缩系数，Lasso 可能把部分系数压到零，Elastic Net 结合两种惩罚。这里约束的是线性系数；XGBoost 另对树叶值和叶数施加惩罚。

> [!info]- 来源
> - **单棵树怎样分叶并给出区域预测。** Breiman、Friedman、Olshen 与 Stone，*Classification and Regression Trees*（1984），分类分裂 §2.3、回归树第 8 章，[出版社电子书预览](https://api.pageplace.de/preview/DT0400.9781351460491_A31471984/preview-9781351460491_A31471984.pdf)。本入口指向的候选阈值、误差和新记录预测，详见[决策树章节](decision-tree-split-criteria.md)，该章另列 scikit-learn 1.9.1 实现证据。
> - **提升怎样逐轮产生训练信号。** Freund 与 Schapire，*A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting*（1997），[论文 DOI](https://doi.org/10.1006/jcss.1997.1504)，§4.1–4.2；Friedman、Hastie 与 Tibshirani，*Additive Logistic Regression: A Statistical View of Boosting*（2000），[论文 DOI](https://doi.org/10.1214/aos/1016218223)，§4；Friedman，*Greedy Function Approximation: A Gradient Boosting Machine*（1999 论文稿），[全文](https://www.cse.iitb.ac.in/~soumen/readings/papers/Friedman1999GreedyFuncApprox.pdf)，§§3、4.1。AdaBoost 与房价残差的具体算例及其范围见[逐轮提升章节](adaboost-and-gradient-boosting-updates.md)。
> - **AdaBoost 分类与回归的边界。** scikit-learn 稳定版 1.9.1 [`AdaBoostClassifier`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.AdaBoostClassifier.html)和 [`AdaBoostRegressor`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.AdaBoostRegressor.html) 文档说明分类器与回归器的任务类型，并注明回归器实现 AdaBoost.R2。于 2026-11-12 查阅。
> - **线性模型的系数惩罚。** Hoerl 与 Kennard，*Ridge Regression: Biased Estimation for Nonorthogonal Problems*（1970），[论文 DOI](https://doi.org/10.1080/00401706.1970.10488634)；Tibshirani，*Regression Shrinkage and Selection via the Lasso*（1996），[论文 DOI](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x)；Zou 与 Hastie，*Regularization and Variable Selection via the Elastic Net*（2005），[论文 DOI](https://doi.org/10.1111/j.1467-9868.2005.00503.x)。系数惩罚和尺度条件见[线性正则化章节](ridge-lasso-and-elastic-net.md)。
> - **XGBoost 的树提升目标和当前参数。** Chen 与 Guestrin，*XGBoost: A Scalable Tree Boosting System*（KDD 2016；[arXiv v3](https://arxiv.org/abs/1603.02754v3) 于 2016-06-10 修订），§§2–3.4；XGBoost 稳定版 3.4.2 [参数说明](https://xgboost.readthedocs.io/en/stable/parameter.html)与[树构造方法](https://xgboost.readthedocs.io/en/stable/treemethod.html)，2026-11-12 查阅。三行示例、分裂排序和叶增量的证据见[XGBoost 章节](xgboost-objective-and-parameters.md)。
