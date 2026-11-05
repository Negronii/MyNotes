# How do AdaBoost and gradient boosting build a sequence of learners? / AdaBoost 与梯度提升如何逐轮建立学习器？

AdaBoost reweights examples so mistakes gain influence; gradient boosting fits each new learner to the negative gradient of a chosen loss. Their updates differ, and ordinary residuals match pseudo-residuals only for losses such as squared error. / AdaBoost 重加权样本，使误分类样本影响增大；梯度提升让新学习器拟合选定损失的负梯度。两种更新不同；普通残差只有在平方误差等特定损失下才对应伪残差。

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

## Sources / 参考资料

- Breiman, Friedman, Olshen, and Stone, *Classification and Regression Trees* (1984), the foundational CART treatment of impurity-based tree splitting.
- Freund and Schapire (1997), [A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting](https://doi.org/10.1006/jcss.1997.1504).
- Friedman (2001), [Greedy Function Approximation: A Gradient Boosting Machine](https://doi.org/10.1214/aos/1013203451).
- Hoerl and Kennard (1970), [Ridge Regression: Biased Estimation for Nonorthogonal Problems](https://doi.org/10.1080/00401706.1970.10488634); Tibshirani (1996), [Regression Shrinkage and Selection via the Lasso](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x); Zou and Hastie (2005), [Regularization and Variable Selection via the Elastic Net](https://doi.org/10.1111/j.1467-9868.2005.00503.x).
- Chen and Guestrin (2016), [XGBoost: A Scalable Tree Boosting System](https://doi.org/10.1145/2939672.2939785), for the second-order tree objective. For API parameter meanings, see the [XGBoost 3.4.2 parameter reference](https://xgboost.readthedocs.io/en/stable/parameter.html) and its [scikit-learn API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

Source checks: the cited original papers and author/publisher records were reviewed 2026-10-15. General algorithm descriptions above do not claim a result for any particular dataset or implementation version.
