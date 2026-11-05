# How does XGBoost’s regularized objective relate to its parameters? / XGBoost 的正则化目标与参数有什么关系？

Each boosting round approximately optimizes a second-order loss expansion with penalties on leaf count and leaf scores. Parameters act on task/loss, step size, depth, row and feature sampling, and leaf regularization. `n_estimators` is a round limit, not generally a tree count. / 每轮提升近似优化损失的二阶展开，并惩罚叶数与叶得分。参数分别作用于任务/损失、步长、深度、行/特征采样与叶正则化；`n_estimators` 是轮数上限，一般不等于树总数。

## XGBoost / 极端梯度提升

XGBoost is a scalable system for regularized tree boosting. At round `t`, it adds a tree `f_t` and approximately minimizes a second-order expansion of the training objective:

```text
Obj^(t) ≈ Σ_i [g_i f_t(x_i) + 1/2 h_i f_t(x_i)²]
          + γT + 1/2 reg_lambda Σ_j w_j² + reg_alpha Σ_j |w_j|
```

Here `g_i` and `h_i` are the first and second derivatives of the loss at the current prediction; `T` is the number of leaves and `w_j` is a leaf score. The complexity terms penalize additional leaves and large leaf scores. This is more precise than saying every new tree simply fits raw residuals: that description is exact only for particular losses and updates.

The original system paper describes sparsity-aware split finding for sparse inputs, approximate split search, and parallel work over features. Missing values are handled through learned default split directions; this is not general-purpose imputation, and data meaning still determines whether a missing value is informative.

Important parameters change different parts of the model; the meanings below follow XGBoost 3.4.2 documentation, not fixed tuning advice:

| Parameter | Meaning |
| --- | --- |
| `objective` | Selects the learning task and loss, such as squared-error regression or a classification objective. |
| `learning_rate` (`eta`) | Shrinks each boosting update, making additions more conservative; smaller steps often need more rounds. |
| `max_depth` | Limits tree depth; deeper trees are more complex and can overfit. |
| `n_estimators` | For `XGBClassifier` and `XGBRegressor`, the maximum number of boosting rounds. A round can add multiple trees depending on `num_parallel_tree` and the objective/output strategy, so this is not generally the total tree count. Early stopping may end training before the configured limit. |
| `subsample` | Fraction of training rows sampled for each boosting iteration. |
| `colsample_bytree` | Fraction of feature columns sampled when constructing each tree. |
| `reg_lambda` (`lambda`) | L2 penalty on leaf weights in tree boosting. |
| `reg_alpha` (`alpha`) | L1 penalty on leaf weights in tree boosting. |

These effects interact, so the meanings are not a recipe for choosing values. Feature-importance summaries describe model use under a chosen metric; they do not show causal impact.

Tree boosting is useful to evaluate when tabular data may contain nonlinear effects or interactions. Compare it with a simple baseline on an appropriate validation set; speed and accuracy depend on dataset, features, hardware, objective, and tuning.

## Sources / 参考资料

- Breiman, Friedman, Olshen, and Stone, *Classification and Regression Trees* (1984), the foundational CART treatment of impurity-based tree splitting.
- Freund and Schapire (1997), [A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting](https://doi.org/10.1006/jcss.1997.1504).
- Friedman (2001), [Greedy Function Approximation: A Gradient Boosting Machine](https://doi.org/10.1214/aos/1013203451).
- Hoerl and Kennard (1970), [Ridge Regression: Biased Estimation for Nonorthogonal Problems](https://doi.org/10.1080/00401706.1970.10488634); Tibshirani (1996), [Regression Shrinkage and Selection via the Lasso](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x); Zou and Hastie (2005), [Regularization and Variable Selection via the Elastic Net](https://doi.org/10.1111/j.1467-9868.2005.00503.x).
- Chen and Guestrin (2016), [XGBoost: A Scalable Tree Boosting System](https://doi.org/10.1145/2939672.2939785), for the second-order tree objective. For API parameter meanings, see the [XGBoost 3.4.2 parameter reference](https://xgboost.readthedocs.io/en/stable/parameter.html) and its [scikit-learn API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

Source checks: the cited original papers and author/publisher records were reviewed 2026-10-15. General algorithm descriptions above do not claim a result for any particular dataset or implementation version.
