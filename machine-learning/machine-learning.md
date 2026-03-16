## Decision Tree

A flowchart-like model that splits data into subgroups using **decision nodes** (conditional statements) and ends with **leaf nodes** (final predictions).

### Key Components:

- **Root Node**: Topmost node representing the entire dataset.
- **Decision Node**: Splits data based on a condition (e.g., "Age > 30?").
- **Leaf Node**: Final prediction (classification) or value (regression).

### Splitting Data with Gini Impurity

**Gini Impurity** measures how "mixed" a group of data is. It answers: _“What’s the probability of misclassifying a random data point?”_

#### Formula:

$$
\text{Gini} = 1 - \sum\_{i=1}^{n} (p_i)^2
$$

- \( p_i \): Fraction of data points in class \( i \).
- **Lower Gini** = More homogeneity → Better split.

#### Example:

- 3 red marbles, 1 blue marble:
  $$
  \text{Gini} = 1 - \left(\frac{3}{4}\right)^2 - \left(\frac{1}{4}\right)^2 = 0.375
  $$

---

## Forest of Stumps

A collection of **stumps** (1-level decision trees). Stumps are "weak learners" (slightly better than random guessing).

---

## AdaBoost

- **Key Idea**: Combine multiple weak learners (stumps) into a strong model.
- **Process**:
  1. Assign equal weights to all data points.
  2. Train a stump; increase weights for misclassified points.
  3. Repeat, focusing on errors from previous stumps.
  4. Final prediction: Weighted vote of all stumps.

---

## Regression Trees

Predicts **continuous values** (e.g., house prices).

- **Splitting Criteria**: Minimize **Mean Squared Error (MSE)**.
  $$
  \text{MSE} = \frac{1}{n} \sum\_{i=1}^{n} (y_i - \hat{y}\_i)^2
  $$
- **Avoid Overfitting**:
  - Set minimum samples to split (e.g., 20 observations).
  - Limit tree depth.

---

## Gradient Boosting

**Gradient Boosting** builds an ensemble of **weak learners** (usually shallow trees) sequentially, where each new tree corrects errors from the previous ones using gradient descent.

### How It Works:

1. **Initial Prediction**:

   - Start with a simple guess (e.g., mean of target values for regression).

2. **Calculate Residuals**:

   - For each data point:
     $$
     \text{Residual} = \text{Actual Value} - \text{Predicted Value}
     $$

3. **Train a Weak Learner**:

   - Fit a tree to predict the residuals (errors).

4. **Update Predictions**:

   - Add the new tree’s predictions to the previous model’s output, scaled by a **learning rate** (e.g., 0.1).
     $$
     \text{New Prediction} = \text{Old Prediction} + \lambda \times \text{Tree Prediction}
     $$

5. **Repeat**:
   - Iterate steps 2–4 for a fixed number of trees or until errors stop improving.

### Key Features:

- **Loss Function**: Minimized via gradient descent (e.g., MSE for regression, log-loss for classification).
- **Learning Rate (\(\lambda\))**: Controls step size to prevent overfitting (smaller \(\lambda\) = more trees needed).
- **Tree Depth**: Typically shallow (3–6 levels) to avoid overfitting.

### Example:

Predict house prices:

1. Initial prediction: Average price = $300k.
2. Residuals: Actual prices - $300k.
3. Train a tree to predict residuals (e.g., houses with >3 bedrooms have +$50k residuals).
4. Update predictions: $300k + (0.1 × $50k) = $305k.
5. Repeat with new residuals.

### Advantages:

- Handles complex patterns.
- Flexible (works with any differentiable loss function).
- Often achieves high accuracy.

### vs. AdaBoost:

- AdaBoost adjusts weights of misclassified points; Gradient Boosting fits trees to residuals.
- Gradient Boosting uses **arbitrary loss functions**; AdaBoost uses exponential loss.

---

## Regularization: Ridge vs. Lasso

**Regularization** prevents overfitting in regression models by adding a penalty term to the loss function. This shrinks coefficients (slopes) toward zero, trading slight bias for lower variance.

---

## 1. **Ridge Regression (L2 Regularization)**

- **Goal**: Reduce overfitting by shrinking coefficients, but not to zero.
- **Penalty Term**: Adds the **squared magnitude** of coefficients to the loss function.
  $$
  \text{Loss} = \text{MSE} + \lambda \sum\_{i=1}^{n} \beta_i^2
  $$
  - \(\lambda\) (lambda): Controls regularization strength (higher \(\lambda\) → more shrinkage).
  - \(\beta_i\): Coefficients of the model.

### Key Features:

- **All features stay in the model** (no feature selection).
- Works well when predictors are **correlated** (multicollinearity).
- Sensitive to feature scaling—**standardize data first**.

### Use Case:

Predict house prices using all features (e.g., size, bedrooms, age) where all variables are relevant.

---

## 2. **Lasso Regression (L1 Regularization)**

- **Goal**: Reduce overfitting + **automatically select important features** by shrinking some coefficients to zero.
- **Penalty Term**: Adds the **absolute magnitude** of coefficients to the loss function.
  $$
  \text{Loss} = \text{MSE} + \lambda \sum\_{i=1}^{n} |\beta_i|
  $$

### Key Features:

- **Sparsity**: Forces some coefficients to **exactly zero**, performing feature selection.
- Useful for high-dimensional data (many features, few observations).
- Also requires **standardization**.

### Use Case:

Predicting disease risk using 100+ genetic markers; Lasso identifies the 5 most impactful markers.

---

## Comparison

| **Aspect**           | **Ridge (L2)**                          | **Lasso (L1)**                           |
| -------------------- | --------------------------------------- | ---------------------------------------- |
| **Coefficients**     | Shrinks, but never zero                 | Shrinks some to zero (sparse model)      |
| **Use Case**         | Multicollinearity, all features matter  | Feature selection, high-dimensional data |
| **Interpretability** | Less interpretable (keeps all features) | More interpretable (selects features)    |

---

## Choosing \(\lambda\)

- **Cross-validation** (e.g., grid search) is used to find the optimal \(\lambda\).
- Too high \(\lambda\) → **underfitting** (overshrinking coefficients).
- Too low \(\lambda\) → **overfitting**.

---

## Intuition with Analogy

Imagine fitting a model with a "budget" for coefficients:

- **Ridge**: Spreads the budget evenly, keeping all features but making them smaller.
- **Lasso**: Spends the budget on the most important features, ignoring the rest.

---

## Elastic Net (Bonus)

Combines **L1 + L2 penalties** for a balance between Ridge and Lasso. Useful when features are correlated _and_ some need to be eliminated.

---

## XGBoost (Extreme Gradient Boosting)

**XGBoost** is a powerful, optimized version of gradient boosting designed for speed and performance. It’s widely used in competitions (like Kaggle) and industry for structured data problems.

---

### Key Ideas

1. **Boosting**: Builds trees **sequentially**; each new tree corrects errors from previous trees.
2. **Regularization**: Adds penalties (L1/L2) to avoid overfitting.
3. **Efficiency**: Handles missing data, parallel processing, and smart tree-building.

---

### How It Works

1. **Start Simple**: Begin with an initial prediction (e.g., mean value for regression).
2. **Calculate Residuals**: Compute errors (actual – predicted) for each data point.
3. **Build Trees**:
   - Train a weak tree to predict residuals (errors).
   - Trees are shallow (e.g., depth 3–6) to prevent overfitting.
4. **Update Model**:
   - Combine the new tree’s predictions with previous ones, scaled by a **learning rate** (e.g., 0.1).
   - Formula:
     $$
     \text{New Prediction} = \text{Old Prediction} + \lambda \times \text{Tree Prediction}
     $$
5. **Repeat**: Keep adding trees until no improvement (or set number of rounds).

---

### Key Features

- **Regularization**:
  - **L1 (Lasso)** and **L2 (Ridge)** penalties shrink coefficients.
  - Loss Function Example (Simplified):
    $$
    \text{Loss} = \text{MSE} + \lambda \sum \beta^2 + \alpha \sum |\beta|
    $$
- **Handles Missing Data**: Automatically learns to impute missing values.
- **Parallel Processing**: Builds trees faster using multiple CPU cores.
- **Early Stopping**: Stops training if validation score doesn’t improve.
- **Custom Objectives**: Works for regression, classification, ranking, etc.

---

### Important Hyperparameters

| **Parameter**      | **What It Does**                               | **Typical Value** |
| ------------------ | ---------------------------------------------- | ----------------- |
| `learning_rate`    | Scales tree contributions (small = more trees) | 0.01–0.3          |
| `max_depth`        | Maximum tree depth                             | 3–6               |
| `n_estimators`     | Number of trees                                | 100–1000          |
| `subsample`        | % of data used per tree (prevents overfitting) | 0.8–1.0           |
| `colsample_bytree` | % of features used per tree                    | 0.8–1.0           |
| `lambda` (L2)      | Shrinks coefficients                           | 0–1               |
| `alpha` (L1)       | Forces sparsity (some coefficients to zero)    | 0–1               |

---

## Advantages Over Classic Gradient Boosting

1. **Faster Training**: Optimized code + parallel processing.
2. **Built-in Regularization**: Less prone to overfitting.
3. **Handles Missing Data**: No need to preprocess gaps.
4. **Flexible**: Custom objectives (e.g., tweak for rare classes).

---

### When to Use XGBoost

- **Structured Data**: Tables with rows (samples) and columns (features).
- **Medium/Large Datasets**: Efficient even with 100k+ rows.
- **Need for Speed**: Faster than most other boosting tools.
- **Interpretability**: Feature importance scores show which variables matter.

---

### Example Analogy

Think of XGBoost as a **team of experts** solving a puzzle:

1. The first expert makes a guess.
2. The next expert focuses on the mistakes the first one made.
3. Repeat, with each expert correcting residual errors.
4. The final answer combines all experts’ opinions, but each contributes a small amount (learning rate).

---
