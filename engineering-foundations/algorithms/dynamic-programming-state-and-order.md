# 动态规划如何定义状态并安排更新顺序？

dynamic programming（动态规划，DP）把问题拆为有限状态；每个状态只保留后续转移需要的信息。先写递推关系和初始状态，再按依赖顺序计算，复用一维数组时还要追踪每个格子属于哪一轮。

## 状态如何消除重复计算？

若多个递归分支会请求同一个子问题，记忆化将结果保存后复用；自底向上迭代则按依赖次序计算状态。以 Fibonacci 数列为例：F(0)=0、F(1)=1、F(n)=F(n-1)+F(n-2)。朴素递归每层分叉，O(2ⁿ) 是一个时间上界，调用栈 O(n)；迭代每个 n 只更新一次，执行 O(n) 次加法并同时保留两个数。

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

迭代状态的含义是：进入第 i 轮前，`previous=F(i-2)`、`current=F(i-1)`；一轮同时把二者移到 `F(i-1)`、`F(i)`。右侧先读取旧状态，再一次赋给两个变量：

| i | 进入本轮的 `(previous,current)` | 本轮之后 | 新的 `current` |
|---:|---|---|---:|
| 2 | (0, 1) | (1, 1) | F(2)=1 |
| 3 | (1, 1) | (1, 2) | F(3)=2 |
| 4 | (1, 2) | (2, 3) | F(4)=3 |
| 5 | (2, 3) | (3, 5) | F(5)=5 |

`n` 为 0 或 1 时直接返回初值，不进入循环。这里的 O(n) 指加法次数；若每个数占固定宽度，迭代时间为 O(n)、额外空间为 O(1)。若换成 BigInt，整数位数随 n 增长，每次加法也会变贵，不能把 O(n) 次加法直接称为 O(n) 位运算。

JavaScript Number 的整数运算只有在每个中间结果都落在安全整数范围内时才保证精确。F(78)=8,944,394,323,791,464 仍可精确表示；F(79)=14,472,334,024,676,221 已超过 2⁵³−1。相同限制也作用于楼梯方案计数，例如 climbStairs(78,[1,2]) 计算 F(79)；背包有限值相加也可能越界，甚至把两个有限 Number.MAX_VALUE 加成 Infinity。若要求大整数精确，用 BigInt 并调整初始值、返回类型和调用方；若背包值含小数，Number 结果本来就是二进制浮点近似。按精确整数契约时，输入值应为安全整数且所有候选和不超过 Number.MAX_SAFE_INTEGER。

## 计数问题的状态和循环顺序是什么？

爬楼梯示例定义 `ways[total]` 为按顺序选择合法步长、总和恰为 total 的方案数。`ways[0]=1` 表示空序列；每个合法正整数步长 `step` 贡献 `ways[total-step]`。输入要求步长为互异正整数，否则重复步长会重复计算同一选择。下面按目标总和再按步长转移。计算 `ways[total]` 时，所有更小的总和已经完成；把新步长接到较小总和的每条序列末尾，恰好得到以该步长结尾的序列。

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

当 `steps=[1,2]`、`n=3` 时，循环状态如下。`total` 是外层循环，因此每条有序序列只会在其最后一步被加进一次：

| total | 已有状态 | 各步长贡献 | 更新后 `ways[total]` |
|---:|---|---|---:|
| 0 | `ways[0]=1` | 空序列作为基底 | 1 |
| 1 | `ways[0]=1` | step 1: 1 | 1 |
| 2 | `ways[1]=1, ways[0]=1` | step 1: 1；step 2: 1 | 2 |
| 3 | `ways[2]=2, ways[1]=1` | step 1: 2；step 2: 1 | 3 |

对应序列是 1+1+1、1+2、2+1；顺序有意义，1+2 与 2+1 是不同方案。若改成先遍历步长、再递增遍历总和，仍会更新较小总和，但每种步长组合只计一次；本例会得到 2，而不是这里定义的 3。空步长数组也有效：`n=0` 返回空序列方案 1，`n>0` 返回 0；`[1,,2]` 会在按下标校验时拒绝，避免 `some` 跳过数组洞。

循环主体执行 n×k 次步长检查，分配 `ways` 需要 n+1 个槽位。去重还会建立一个大小为 k 的 `Set`；常见哈希实现下，插入和查重平均 O(k)，所以整段代码平均时间为 O((n+1)(k+1))、辅助空间为 O(n+k+1)。ECMAScript 只要求集合访问平均为次线性，不保证每种引擎的每次访问严格 O(1)；这里把动态规划循环成本与集合实现的平均成本分开说明。数组长度仍须能在当前运行时分配。

## 0/1 背包为何要从大容量向小容量更新？

先保留物品轮次，定义 `dp[i][c]` 为只看前 i 件物品、总重量不超过容量 c 时的最大价值。空选择可行，所以 `dp[0][c]=0`；第 i 件物品重量 w、价值 v 的转移为 `dp[i][c]=dp[i-1][c]`，或在 `c>=w` 时取两者较大值 `max(dp[i-1][c], dp[i-1][c-w]+v)`。选当前物品后剩余容量的子问题只能使用之前的物品，这正是 0/1（每件最多一次）约束。

代码把上一行和当前行压进同一个 `best` 数组：处理完前 i 件物品时，`best[c]` 应等于 `dp[i][c]`。容量从大到小时，若 w>0，来源 `c-w` 比 c 小，尚未在本轮更新，所以读到的是上一行；因此不能重复拿当前物品。若容量从小到大，只有 `c-w>=w` 时，来源槽 `c-w` 已在本轮访问过，才可能含当前物品；对 w=2，c=2、3 的来源 0、1 仍是旧行，走到 c=4 时读取的 `best[2]=3` 已含当前物品，因而可再取一次。所有容量都按升序完成后，结果满足无限次取用的转移。w=0 时来源与目标是同一槽，每个容量槽在本轮只访问一次，右侧只读旧值，仍是每件最多取一次。

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

假设容量 W=4，有两件物品 (重量,价值)=(2,3)、(3,4)。表格的行表示已经处理完的物品数，列 c 表示容量上限；每格允许未装满：

| 已处理物品 | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---:|---:|---:|---:|---:|
| 0 件（初始行） | 0 | 0 | 0 | 0 | 0 |
| 只处理 (2,3) | 0 | 0 | 3 | 3 | 3 |
| 再处理 (3,4) | 0 | 0 | 3 | 4 | 4 |

因此一维状态依次为 `[0,0,0,0,0]`、`[0,0,3,3,3]`、`[0,0,3,4,4]`，最优价值 4，可留下未用容量。若只处理第一件且按容量从小到大更新，会先写 `best[2]=3`，再用已更新的 `best[2]` 算出 `best[4]=6`；这一步把唯一一件物品用成了两件。

0/1 背包对 n 件物品、整数容量 W 的动态规划时间为 O((n+1)(W+1))，数组辅助空间为 O(W+1)，不计输入数组。它覆盖 n=0 或 W=0；这是伪多项式复杂度，因为 W 的数值可比其输入编码位数大得多。W=0 时仍会处理每件零重量物品一次；倒序循环在容量 0 也只更新一次，所以正价值零重量物品可各取一次。有限价值允许为负，但零初始化表示可以不选任何物品，因此负价值项不会改善答案。若要恰好装满，除 `best[0]=0` 外其余状态应初始化为不可达哨兵，并在转移时跳过不可达状态。若物品允许无限次且重量为正，才可从小容量向大容量更新；若零重量物品有正价值且可无限选，最优值没有有限上界。若把数值改成 BigInt，比较与加法成本还取决于价值的位数。容量数组也必须能在当前运行时分配。

> [!info]- 来源
> - 三类递推、初值和循环顺序按本页方程、表格及可运行代码逐项复算；动态规划时间只计状态转移/数值运算，状态数由容量 W 等数值参数决定，故背包为伪多项式。经典有限容量表格转移、计数递推见 [CSES Competitive Programmer’s Handbook, ch. 7 “Dynamic programming,” §7.4 “Knapsack problems”](https://cses.fi/book/book.pdf)，以及 §7.1 “Coin problem” 中计数解的基础状态和递推；本页将其状态和循环次序具体化到 JavaScript 一维数组。
> - Number 安全整数边界按 ECMAScript Number.MAX_SAFE_INTEGER=2⁵³−1 核对：[ECMAScript 2026 numbers](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。集合的平均访问要求见 [ECMAScript 2026 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-keyed-collections)。
