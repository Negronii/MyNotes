# How do Ridge, Lasso, and Elastic Net change a linear model? / Ridge、Lasso 与 Elastic Net 如何改变线性模型？

Ridge penalizes squared coefficients and usually shrinks without setting them to zero; Lasso’s absolute-value penalty can produce sparse coefficients; Elastic Net combines both. These penalties change estimation and selection, not causal meaning. / Ridge 惩罚系数平方，通常缩小系数但不将其置零；Lasso 的绝对值惩罚可以产生稀疏系数；Elastic Net 结合两者。惩罚会改变估计和选择行为，但不会赋予因果含义。

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

## Sources / 参考资料

- Breiman, Friedman, Olshen, and Stone, *Classification and Regression Trees* (1984), the foundational CART treatment of impurity-based tree splitting.
- Freund and Schapire (1997), [A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting](https://doi.org/10.1006/jcss.1997.1504).
- Friedman (2001), [Greedy Function Approximation: A Gradient Boosting Machine](https://doi.org/10.1214/aos/1013203451).
- Hoerl and Kennard (1970), [Ridge Regression: Biased Estimation for Nonorthogonal Problems](https://doi.org/10.1080/00401706.1970.10488634); Tibshirani (1996), [Regression Shrinkage and Selection via the Lasso](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x); Zou and Hastie (2005), [Regularization and Variable Selection via the Elastic Net](https://doi.org/10.1111/j.1467-9868.2005.00503.x).
- Chen and Guestrin (2016), [XGBoost: A Scalable Tree Boosting System](https://doi.org/10.1145/2939672.2939785), for the second-order tree objective. For API parameter meanings, see the [XGBoost 3.4.2 parameter reference](https://xgboost.readthedocs.io/en/stable/parameter.html) and its [scikit-learn API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

Source checks: the cited original papers and author/publisher records were reviewed 2026-10-15. General algorithm descriptions above do not claim a result for any particular dataset or implementation version.
