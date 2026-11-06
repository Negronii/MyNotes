# 树模型、正则化与 XGBoost 资料入口

对表格预测，树分裂定义局部预测区域，提升法组合学习器以降低选定损失，线性惩罚则约束系数估计。XGBoost 在带正则项的树提升上使用二阶目标。这些机制描述模型本身，不保证准确率、泛化能力或因果解释。

## 问题地图

- [Decision tree（决策树）如何在分类与回归中选分裂？](decision-tree-split-criteria.md)
- [AdaBoost 与 Gradient Boosting（梯度提升）怎样逐轮改变预测？](adaboost-and-gradient-boosting-updates.md)
- [Ridge regression（岭回归）、Lasso（套索回归）与 Elastic Net（弹性网络）怎样改变线性模型？](ridge-lasso-and-elastic-net.md)
- [XGBoost 每轮怎样用正则化目标选择树结构？](xgboost-objective-and-parameters.md)
