# 动态规划如何定义状态并安排更新顺序？

报表汇总里某些查询可能复用之前算过的子结果，但本篇用三个更小、可完整复算的例子说明一般机制。dynamic programming（动态规划，DP）把问题拆为有限状态；每个状态只保留后续转移需要的信息。先写递推关系和初始状态，再按依赖顺序计算，复用一维数组时还要追踪每个格子属于哪一轮。

## 状态如何消除重复计算？

若多个递归分支会请求同一个子问题，记忆化将结果保存后复用；自底向上迭代则按依赖次序计算状态。以 Fibonacci 数列为例：F(0)=0、F(1)=1、F(n)=F(n-1)+F(n-2)。朴素递归每层分叉，O(2ⁿ) 是一个时间上界，调用栈 O(n)；迭代每个 n 只更新一次，时间 O(n)、辅助空间 O(1)。

~~~javascript
function fibRecursive(n) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

JavaScript Number 的整数运算只有在每个中间结果都落在安全整数范围内时才保证精确。F(78)=8,944,394,323,791,464 仍可精确表示；F(79)=14,472,334,024,676,221 已超过 2⁵³−1。相同限制也作用于楼梯方案计数，例如 climbStairs(78,[1,2]) 计算 F(79)；背包有限值相加也可能越界，甚至把两个有限 Number.MAX_VALUE 加成 Infinity。若要求大整数精确，用 BigInt 并调整初始值、返回类型和调用方；若背包值含小数，Number 结果本来就是二进制浮点近似。按精确整数契约时，输入值应为安全整数且所有候选和不超过 Number.MAX_SAFE_INTEGER。

## 计数问题的状态和循环顺序是什么？

爬楼梯示例定义 ways[total] 为按顺序选择合法步长、总和恰为 total 的方案数。ways[0]=1 表示空序列；每个合法正整数步长 step 贡献 ways[total-step]。输入要求步长为互异正整数，否则重复步长会重复计算同一选择。下面按目标总和再按步长转移。

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError('n must be a non-negative safe integer');
  if (!Array.isArray(steps)) throw new TypeError('steps must be an array');
  for (let i = 0; i < steps.length; i++) {
    if (!Number.isSafeInteger(steps[i]) || steps[i] <= 0) {
      throw new TypeError('steps must contain positive safe integers without holes');
    }
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

steps=[1,2]、n=3 的计算是：ways[0]=1；ways[1]=ways[0]=1；ways[2]=ways[1]+ways[0]=2；ways[3]=ways[2]+ways[1]=3，对应 1+1+1、1+2、2+1。顺序有意义，1+2 与 2+1 是不同方案。空步长数组也有效：n=0 返回空序列方案 1，n>0 返回 0；`[1,,2]` 会在按下标校验时拒绝，避免 `some` 跳过数组洞。若 n 个台阶、k 种步长，含初始化和空边界的时间为 O((n+1)(k+1))，空间 O(n+1)。数组长度仍须能在当前运行时分配。

## 0/1 背包为何要从大容量向小容量更新？

定义 best[c] 为已处理物品中、总重量不超过 c 时可取得的最大价值。处理重量 w、价值 v 的物品时，转移为 max(best[c], best[c-w]+v)。每件物品只能用一次，所以 c 必须从 W 向 w 递减；若从小到大，best[c-w] 可能已包含当前物品，造成重复使用。

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isSafeInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative safe integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  for (let i = 0; i < weights.length; i++) {
    if (!Number.isSafeInteger(weights[i]) || weights[i] < 0) {
      throw new RangeError('weights must contain non-negative safe integers without holes');
    }
    if (!Number.isFinite(values[i])) throw new TypeError('values must contain finite numbers without holes');
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

假设容量 W=4，有两件物品 (重量,价值)=(2,3)、(3,4)。初始 best=[0,0,0,0,0]。处理第一件后得到 [0,0,3,3,3]；第二件从容量 4 向下更新，得到 [0,0,3,4,4]，最优价值 4，可留下未用容量。若第一件按容量从小到大更新，best[2]=3 后又会用该值算出 best[4]=6，相当于把同一件物品用两次。

0/1 背包对 n 件、整数容量 W 的时间为 O((n+1)(W+1))，空间 O(W+1)，覆盖 n=0 或 W=0；这是伪多项式复杂度，因为 W 的数值可比其输入编码位数大得多。W=0 时仍会处理每件零重量物品一次；倒序循环在容量 0 也只更新一次，所以正价值零重量物品可各取一次。代码以零初始化，表示允许不装满且不要求最低价值；若要恰好装满，除 best[0]=0 外其余状态应初始化为不可达哨兵，并在转移时跳过不可达状态。若物品允许无限次且重量为正，才可从小容量向大容量更新；若零重量物品有正价值且可无限选，最优值没有有限上界。容量数组也必须能在当前运行时分配。

> [!info]- 来源
> - 动态规划状态、递推与更新顺序按三段代码的输入/输出和中间数组手工复算；Number 安全整数边界按 ECMAScript Number.MAX_SAFE_INTEGER=2⁵³−1 核对：[ECMAScript 2026 numbers](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。
