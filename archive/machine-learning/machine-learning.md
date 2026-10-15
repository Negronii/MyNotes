# Core Machine Learning Notes / 机器学习核心笔记

> Key terms / 关键词: decision tree 决策树, boosting 提升法, residual 残差, regularization 正则化, feature selection 特征选择. A model description is a mechanism, not a guarantee of accuracy or generalization.

模型要点：树分裂看加权子节点损失；AdaBoost 调整样本权重以关注误分，梯度提升沿选定损失的负梯度逐轮更新；Ridge、Lasso 和 Elastic Net 改变系数惩罚，而 XGBoost 参数还分别控制树结构、迭代步长、样本/特征采样和叶权重正则化。

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

## AdaBoost and Stumps / AdaBoost 与树桩

AdaBoost fits weak classifiers sequentially while changing the training weights: observations that the current classifier gets wrong receive more weight, and each classifier's vote depends on its weighted error. A stump is one possible base learner; a sequence of boosted stumps is not the same method as a random forest.

For the classic binary AdaBoost form with labels and predictions in `{-1, +1}`, let `w_i` be normalized example weights and `ε_t` the weighted error of learner `h_t`. When `0 < ε_t < 0.5`:

```text
α_t = 1/2 ln((1 - ε_t) / ε_t)
w_i ← w_i exp(-α_t y_i h_t(x_i))   # normalize the weights after the update
H(x) = sign(Σ_t α_t h_t(x))
```

The update emphasizes mistakes while the final prediction is a weighted vote. Multiclass and other AdaBoost variants use different formulas.

## Gradient Boosting / 梯度提升

Gradient boosting builds an additive model one learner at a time. At each round, the next learner approximates the negative gradient of the chosen loss with respect to the current predictions (often called **pseudo-residuals**). With squared-error loss, this is proportional to the ordinary residual `y - prediction`; for other losses it is generally not the raw residual.

```text
F_m(x) = F_(m-1)(x) + η · ρ_m · h_m(x)
```

`h_m` is the new learner, `η` is a shrinkage or learning-rate factor, and `ρ_m` is a step size chosen for the loss. A smaller `η` often requires more rounds, but neither setting guarantees better generalization.

Squared-error example for house prices: start with the training-set mean, `$300k`. If a house's actual price is `$350k`, its residual is `$50k`. If the fitted tree predicts `$50k` for that region and the step size is `0.1`, the updated prediction is `$300k + 0.1 × $50k = $305k`. Later rounds fit the remaining loss gradient.

Shallow trees are common base learners, but depth is a tuning choice. Validation, early stopping, and regularization can help control overfitting; a validation set should remain separate from final evaluation.

## Ridge, Lasso, and Elastic Net / Ridge、Lasso 与 Elastic Net

For linear regression with an intercept `β₀`, a common squared-error objective is:

```text
Ridge: min  (1/(2n)) Σ_i (y_i - β₀ - x_iᵀβ)² + λ Σ_j β_j²
Lasso: min  (1/(2n)) Σ_i (y_i - β₀ - x_iᵀβ)² + λ Σ_j |β_j|
```

The intercept is usually left unpenalized. `λ` controls the penalty; predictors are commonly standardized so the penalty treats their scales comparably.

- **Ridge / L2** shrinks coefficients and usually keeps them nonzero; it does not perform sparse feature selection. It can stabilize estimates when predictors are correlated.
- **Lasso / L1** can set coefficients exactly to zero, producing a sparse model. With correlated predictors, which variables remain can be unstable; a selected feature is not thereby shown to be causal or uniquely important.
- **Elastic Net** combines L1 and L2 penalties. It can retain groups of correlated predictors while also allowing sparsity.

Choose penalty strength using validation inside the training process, such as cross-validation. For temporal data, use a split that respects time. Too much regularization can underfit; too little can overfit, but the useful range depends on the data and objective. Lasso selection is a modeling result, not an automatic ranking of the most important variables.

| Aspect / 方面 | Ridge (L2) | Lasso (L1) |
| --- | --- | --- |
| Coefficients / 系数 | Shrinks coefficients; generally not sparse | May set some coefficients to zero |
| Correlated predictors / 相关特征 | Often distributes weight across them | May select one or a subset unstably |
| Scaling / 尺度 | Standardize predictors for comparable penalties | Standardize predictors for comparable penalties |

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
| `n_estimators` | In the scikit-learn wrapper, the number of boosted trees/rounds. |
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
