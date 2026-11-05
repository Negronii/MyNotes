# How do decision trees choose classification and regression splits? / 决策树如何选择分类与回归分裂？

A tree chooses feature-based splits that reduce weighted child-node loss. Gini impurity measures class mixing; regression trees commonly reduce within-node squared error. Depth, leaf size, and pruning control complexity and must be evaluated with the data. / 决策树选择能够降低加权子节点损失的特征分裂。Gini 不纯度衡量类别混杂；回归树通常降低节点内平方误差。深度、叶节点大小和剪枝控制复杂度，需结合数据评估。

## Decision Trees / 决策树

A **decision tree** repeatedly splits observations by feature conditions. Internal nodes apply conditions; leaf nodes return a class or a numeric prediction. A shallow one-split tree is a **decision stump** and can serve as a base learner in an ensemble.

For a classification node with class proportions `p_k`, Gini impurity is:

```text
Gini = 1 - Σ_k p_k²
```

This equals the probability that two labels sampled independently from the node's class distribution differ. It is zero for a pure node and, for two equally common classes, 0.5. A split is evaluated by the weighted impurity of its child nodes relative to the parent; comparing an unweighted child Gini alone can favor an unhelpful split.

Example: with three red and one blue observation, `Gini = 1 - (3/4)² - (1/4)² = 0.375`.

For **regression trees**, a common criterion is within-node squared error. For observations `y_i` in a node with mean prediction `ȳ`, the mean squared error is:

```text
MSE = (1/n) Σ_i (y_i - ȳ)²
```

Candidate splits reduce the weighted sum of child errors. Depth limits, minimum leaf sizes, and pruning can control model complexity; their settings depend on the data and validation design.

## Sources / 参考资料

- Breiman, Friedman, Olshen, and Stone, *Classification and Regression Trees* (1984), the foundational CART treatment of impurity-based tree splitting.
- Freund and Schapire (1997), [A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting](https://doi.org/10.1006/jcss.1997.1504).
- Friedman (2001), [Greedy Function Approximation: A Gradient Boosting Machine](https://doi.org/10.1214/aos/1013203451).
- Hoerl and Kennard (1970), [Ridge Regression: Biased Estimation for Nonorthogonal Problems](https://doi.org/10.1080/00401706.1970.10488634); Tibshirani (1996), [Regression Shrinkage and Selection via the Lasso](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x); Zou and Hastie (2005), [Regularization and Variable Selection via the Elastic Net](https://doi.org/10.1111/j.1467-9868.2005.00503.x).
- Chen and Guestrin (2016), [XGBoost: A Scalable Tree Boosting System](https://doi.org/10.1145/2939672.2939785), for the second-order tree objective. For API parameter meanings, see the [XGBoost 3.4.2 parameter reference](https://xgboost.readthedocs.io/en/stable/parameter.html) and its [scikit-learn API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

Source checks: the cited original papers and author/publisher records were reviewed 2026-10-15. General algorithm descriptions above do not claim a result for any particular dataset or implementation version.
