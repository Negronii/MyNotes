# How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？

Define a state with all the information its transitions need, establish base cases, then compute prerequisites before dependent states. When an update reuses the same storage, its order determines which version a transition reads. / 状态要包含转移所需的信息，先确定初始条件，再按依赖顺序计算。复用同一份存储时，更新顺序决定转移读到哪个版本。

## Dynamic programming

**动态规划 / Dynamic programming** stores results for overlapping subproblems. Top-down memoization follows the recursive definition; bottom-up iteration computes states in dependency order and can often retain only the state still needed.

### Fibonacci

For non-negative integer n, naive recursion repeats subproblems and takes O(2^n) time with O(n) call-stack space. The iterative form takes O(n) time and O(1) auxiliary space. These examples use Number; use BigInt when exact results beyond Number's safe-integer range are needed.

~~~javascript
function fibRecursive(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

### Climbing stairs (frog jump)

Count ordered sequences of allowed positive step sizes that sum to n. The empty sequence is one way to reach step 0. Require distinct positive integer steps; repeated entries would count the same step size more than once.

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (!Array.isArray(steps) || steps.some(step => !Number.isInteger(step) || step <= 0)) {
    throw new TypeError('steps must contain positive integers');
  }
  if (new Set(steps).size !== steps.length) throw new RangeError('steps must be distinct');

  const ways = new Array(n + 1).fill(0);
  ways[0] = 1;
  for (let total = 1; total <= n; total++) {
    for (const step of steps) {
      if (total >= step) ways[total] += ways[total - step];
    }
  }
  return ways[n];
}
~~~

This counts order as meaningful: with steps [1, 2], reaching 3 has three sequences: 1+1+1, 1+2, and 2+1. Time is O(nk), where k is the number of allowed steps; space is O(n).

### 0/1 Knapsack

Choose each item at most once to maximize value within a weight capacity. Iterate capacities downward so the current item cannot be selected again during the same pass.

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  if (weights.some(weight => !Number.isInteger(weight) || weight < 0)) {
    throw new RangeError('weights must be non-negative integers');
  }

  const best = new Array(capacity + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let remaining = capacity; remaining >= weights[i]; remaining--) {
      best[remaining] = Math.max(best[remaining], best[remaining - weights[i]] + values[i]);
    }
  }
  return best[capacity];
}
~~~

Time is O(nW) and space O(W), for n items and integer capacity W. The zero-filled state means the result may leave capacity unused; it assumes there is no required minimum value or exact-fill constraint.

---

[Back to the main question / 返回主问题](algorithms-and-complexity.md).
