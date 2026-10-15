# Factor Research and Quantitative Trading / 因子研究与量化交易

> 核心概念 / Core idea: an empirical return pattern is a research question, not by itself a tradable edge or an explanation of why returns occurred. 因子研究先定义可检验的收益模式，再区分风险暴露、模型定价误差与可交易策略表现。

## Anomalies and Factors / 异象与因子

An **anomaly / 异象** is a return pattern that departs from a specified benchmark model under a stated sample and test design. Historical persistence can strengthen the evidence, but persistence by itself, without a benchmark and test, does not make a pattern an anomaly. The label does not establish a causal mechanism, future persistence, or net profitability. A pattern may reflect omitted risk, mispricing, data choices, or selection from many trials.

A **factor / 因子** is a modeled source of common return variation. Research often represents one with a factor-mimicking portfolio, while observable characteristics such as size, book-to-market, or past return can be used to sort assets or proxy for exposures. A characteristic is not automatically a factor return.

Examples studied in the literature include:

- **Momentum / 动量**: portfolios formed from past returns have shown return differences in particular markets and samples. A common construction goes long recent winners and short recent losers.
- **Size / 规模**: portfolios of smaller and larger firms have shown different average returns in some samples and models.
- **Value / 价值**: portfolios formed on measures such as book-to-market have shown different average returns in some samples and models.

These are empirical findings, not guarantees that the same spreads will persist or survive implementation costs. Factor definitions, breakpoints, weighting, holding periods, and samples matter.

## Exposure, Factor Return, and Alpha / 暴露、因子收益与 Alpha

For asset or test portfolio `i` in period `t`, a time-series factor model is commonly written as:

```text
R_it - R_ft = α_i + β_i1 F_1t + ... + β_ik F_kt + ε_it
```

- `R_it - R_ft` is the asset's or portfolio's excess return.
- `F_kt` is the realized return of factor `k` in period `t`.
- `β_ik` is the asset's exposure estimated from its return co-movement with that factor series.
- `α_i` is the regression intercept: average return left unexplained by this model over the fitted sample. In an asset-pricing test it is a model-conditional pricing error, not proof of skill, causality, or a repeatable opportunity.
- `ε_it` is the period-specific residual.

The terms **factor return** and **factor premium** are related but not interchangeable. `F_t` is a realized factor-portfolio return. A cross-sectional price of exposure, often written `λ_t`, is estimated by asking how returns vary with exposures across assets; it need not equal a factor portfolio's realized return in each period.

An exposure-based portfolio decomposition is useful for attribution, but it is an estimate under a chosen factor set. A long-short portfolio can reduce selected exposures by construction; it does not eliminate all market, sector, liquidity, or other risks.

## Portfolio Sorts / 排序组合

A sort ranks assets by a characteristic known at portfolio-formation time, groups them, and compares later returns. Examples include size, book-to-market, and past return. The characteristic and all portfolio rules must be defined without using information that would not have been available at formation.

A **double sort / 双重排序** uses two characteristics. In an **independent sort**, breakpoints for each characteristic are set on the full eligible universe and the resulting groups are intersected. In a **conditional sort**, assets are first grouped on one characteristic and then ranked on the second characteristic within each first-stage group. A 5-by-5 design creates 25 cells; a 2-by-3 design creates six.

Double sorts can test whether a return spread remains within groups formed on a known characteristic. If a candidate signal's spread disappears within those groups, the original spread may have overlapped with that characteristic. If it remains, the result is evidence of incremental association under that design, not proof that all confounding exposures were removed. Report the portfolios' realized factor exposures or use a regression/risk model as a complementary check.

Adding more sort variables creates more, smaller portfolios and can make estimates noisy. The number and construction of groups are design choices, not a universal recipe.

## Factor Regressions / 因子回归

For time-series regressions, estimate each test asset's exposure and intercept from its returns over time. A joint test of the intercepts asks whether the chosen model leaves pricing errors across the test assets; a failure to reject zero does not prove the model is true, and a significant intercept is conditional on the selected model, assets, and sample.

**Fama–MacBeth regression / Fama–MacBeth 回归** is a two-pass cross-sectional procedure:

1. Estimate assets' factor exposures from time-series returns.
2. At each date, regress the cross-section of asset returns on the estimated exposures (or specified characteristics), then average the date-specific coefficients to estimate prices of exposure.

This asks whether exposure helps explain differences in returns across assets. It is distinct from a time-series regression of one asset's return on factor returns, and it does not by itself demonstrate that a factor can be traded profitably.

When many candidate signals have been tried, ordinary significance cutoffs can overstate evidence because of multiple testing and data selection. Record the tested universe and use an appropriate multiple-testing or out-of-sample design.

## Summary / 小结

Factor research moves from a clearly specified characteristic or return pattern to portfolio construction, exposure measurement, and model-based tests. A positive historical spread or nonzero alpha is conditional evidence; it does not alone identify skill, causality, or a forecast of future returns.

## Sources / 参考文献

- Fama and French (1992), [The Cross-Section of Expected Stock Returns](https://doi.org/10.1111/j.1540-6261.1992.tb04398.x); and (1993), [Common Risk Factors in the Returns on Stocks and Bonds](https://doi.org/10.1016/0304-405X(93)90023-5).
- Fama and MacBeth (1973), [Risk, Return, and Equilibrium: Empirical Tests](https://doi.org/10.1086/260061).
- Gibbons, Ross, and Shanken (1989), [A Test of the Efficiency of a Given Portfolio](https://doi.org/10.2307/1913625).
- Carhart (1997), [On Persistence in Mutual Fund Performance](https://doi.org/10.1111/j.1540-6261.1997.tb03808.x); Harvey, Liu, and Zhu (2016), [...and the Cross-Section of Expected Returns](https://www.nber.org/papers/w20592).

Source checks: primary papers and author/publisher abstracts reviewed 2026-10-15. Historical samples in those papers support the concepts above, not current expected performance.
