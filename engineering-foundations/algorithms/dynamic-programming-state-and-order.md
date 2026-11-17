# 动态规划如何定义状态并安排更新顺序？

dynamic programming（动态规划，DP）把问题拆成有限个状态，每个状态只记录后续转移需要的信息。做法是先写出递推关系和初始状态，再按依赖顺序逐个计算；如果为了省空间复用一个一维数组，还要清楚每个格子当前存的是哪一轮的值。本章用三个例子展开：Fibonacci 数列说明状态怎样消除重复计算，爬楼梯计数说明循环顺序怎样决定“算的是什么”，0/1 背包说明一维数组为什么要倒序更新。

## 状态如何消除重复计算？

如果多个递归分支会反复请求同一个子问题，有两种办法避免重算：memoization（记忆化）把算过的结果存起来复用；自底向上迭代则按依赖次序依次计算各状态。以 Fibonacci 数列为例：F(0)=0、F(1)=1、F(n)=F(n-1)+F(n-2)。朴素递归每次调用分成两支，同一个 F(k) 会被算很多次，时间上界为 O(2ⁿ)，调用栈深度 O(n)；迭代版每个 n 只算一次，共 O(n) 次加法，任何时刻只保留两个数。

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

迭代版的两个变量含义是：进入第 i 轮前，`previous=F(i-2)`、`current=F(i-1)`；这一轮把二者同时推进为 `F(i-1)`、`F(i)`。解构赋值先用旧值算出右侧两项，再一起赋给左侧两个变量，所以不会读到半更新的值：

| i | 进入本轮的 `(previous,current)` | 本轮之后 | 新的 `current` |
|---:|---|---|---:|
| 2 | (0, 1) | (1, 1) | F(2)=1 |
| 3 | (1, 1) | (1, 2) | F(3)=2 |
| 4 | (1, 2) | (2, 3) | F(4)=3 |
| 5 | (2, 3) | (3, 5) | F(5)=5 |

`n` 为 0 或 1 时直接返回初值，不进入循环。这里的 O(n) 指加法次数；只有每个数占固定宽度时，迭代时间才是 O(n)、额外空间 O(1)。如果换成 BigInt，F(n) 的位数随 n 线性增长，每次加法也越来越贵，O(n) 次加法不等于 O(n) 次位运算。

固定宽度的前提在 JavaScript 里有具体后果：Number 是双精度浮点数，只有每个中间结果都不超过安全整数上限 2⁵³−1（`Number.MAX_SAFE_INTEGER`）时，整数运算才保证精确。F(78)=8,944,394,323,791,464 仍可精确表示；F(79)=14,472,334,024,676,221 已经超过上限。同样的限制也适用于本章后面的两个例子：楼梯计数 `climbStairs(78,[1,2])` 的结果正是 F(79)；背包的价值相加也可能越界，两个有限的 `Number.MAX_VALUE` 相加甚至会得到 `Infinity`。需要精确的大整数时改用 BigInt，并相应调整初始值、返回类型和调用方；背包价值若含小数，Number 结果本来就是二进制浮点近似。按精确整数的约定，输入值应为安全整数，且所有候选和都不超过 `Number.MAX_SAFE_INTEGER`。

## 计数问题的状态和循环顺序是什么？

Fibonacci 的状态只有一个维度。爬楼梯问题再加一个选择：每步可以走 `steps` 中的任一步长，问恰好走到第 n 级有多少种走法。定义 `ways[total]` 为“依次选择步长、总和恰为 total 的序列数”。`ways[0]=1` 表示一步不走的空序列；对每个步长 `step`，以它结尾的序列数等于 `ways[total-step]`，把各步长的贡献相加即得 `ways[total]`。步长必须是互不相同的正整数，否则重复的步长会把同一种选择算两次。

下面的代码外层按目标总和、内层按步长转移。计算 `ways[total]` 时，所有更小的总和都已算完；把某个步长接到较小总和的每条序列末尾，恰好得到所有以该步长结尾的序列。

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

对应的序列是 1+1+1、1+2、2+1；这里顺序有意义，1+2 与 2+1 算两种方案。如果把两层循环对调，外层遍历步长、内层递增遍历总和，计算的就变成“不计顺序的步长组合数”：每个组合只按步长出现的固定次序计一次，本例得到 2 而不是 3。空步长数组也合法：`n=0` 返回 1（空序列），`n>0` 返回 0。含空槽的数组如 `[1,,2]` 会被按下标逐项校验拒绝；如果改用 `some` 之类的方法校验，空槽会被跳过而漏检。

设步长有 k 个。循环主体执行 n×k 次步长检查，`ways` 占 n+1 个槽位。去重还要建一个大小为 k 的 `Set`，在常见哈希实现下平均 O(k)；所以整段代码平均时间 O((n+1)(k+1))，辅助空间 O(n+k+1)。ECMAScript 只要求集合访问平均次线性，不保证每次访问严格 O(1)，因此这里把 DP 循环本身的成本与集合的平均成本分开说明。此外 n 不能大到当前运行时无法分配 `ways` 数组。

## 0/1 背包为何要从大容量向小容量更新？

爬楼梯中每个步长可以无限次使用；0/1 背包则要求每件物品最多选一次，这个限制正是靠更新顺序来保证的。先用带物品轮次的二维表定义状态：`dp[i][c]` 为只考虑前 i 件物品、总重量不超过容量 c 时的最大价值。空选择可行，所以 `dp[0][c]=0`；第 i 件物品重量 w、价值 v 的转移为 `dp[i][c]=dp[i-1][c]`，或在 `c>=w` 时取两者较大值 `max(dp[i-1][c], dp[i-1][c-w]+v)`。选当前物品后剩余容量的子问题只能使用之前的物品，这正是 0/1（每件最多一次）约束。

代码把上一行和当前行压进同一个 `best` 数组：处理完前 i 件物品后，`best[c]` 应等于 `dp[i][c]`。关键是转移读取的 `best[c-w]` 必须还是上一行的值：

- **容量从大到小**：若 w>0，来源 `c-w` 比 c 小，本轮还没轮到它，读到的仍是上一行，所以当前物品不会被重复选。
- **容量从小到大**：当 `c-w>=w` 时，来源槽 `c-w` 本轮已经更新过，可能已含当前物品。以下面例子中 w=2、价值 3 的物品为例：c=2、3 的来源 0、1 仍是旧值；到 c=4 时读到的 `best[2]=3` 已经装了这件物品，于是又装了一次。整轮按升序做完，得到的是“每件可无限次选”的完全背包转移。

w=0 时来源与目标是同一个槽；每个槽本轮只访问一次，右侧读到的是旧值，所以仍然每件最多选一次。

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

例子：容量 W=4，两件物品的（重量, 价值）分别为 (2,3)、(3,4)。表格的行表示已处理完的物品，列 c 表示容量上限；每格允许不装满：

| 已处理物品 | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---:|---:|---:|---:|---:|
| 0 件（初始行） | 0 | 0 | 0 | 0 | 0 |
| 只处理 (2,3) | 0 | 0 | 3 | 3 | 3 |
| 再处理 (3,4) | 0 | 0 | 3 | 4 | 4 |

对应的一维数组依次为 `[0,0,0,0,0]`、`[0,0,3,3,3]`、`[0,0,3,4,4]`，最优价值为 4（两件合重 5，装不下，只能选价值 4 的那件，留 1 单位空余）。如果处理第一件时按容量从小到大更新，会先写入 `best[2]=3`，再用这个已更新的值算出 `best[4]=6`，相当于把唯一一件物品用了两次。

复杂度：n 件物品、整数容量 W 时，时间 O((n+1)(W+1))，辅助数组空间 O(W+1)（不计输入），n=0 或 W=0 也适用。这是 pseudo-polynomial（伪多项式）复杂度：运行时间与 W 的数值成正比，而 W 只需约 log W 位就能写进输入，所以按输入长度衡量并不是多项式。

几个边界情况：

- W=0 时，零重量物品仍会各处理一次；倒序循环在容量 0 也只更新一次，所以正价值的零重量物品各取一次。
- 价值可以为负，但零初始化意味着“什么都不选”是合法方案，所以负价值物品不会改善答案。
- 若要求恰好装满，除 `best[0]=0` 外，其余状态应初始化为“不可达”哨兵，转移时跳过不可达的来源。
- 物品可无限次选且重量为正时，才能从小容量向大容量更新；如果零重量物品有正价值且可无限选，最优值没有有限上界。
- 换成 BigInt 后，比较与加法的成本还取决于价值的位数；W 也不能大到运行时无法分配容量数组。

> [!info]- 来源
> - 三类递推、初值和循环顺序按本页方程、表格及可运行代码逐项复算；动态规划时间只计状态转移/数值运算，状态数由容量 W 等数值参数决定，故背包为伪多项式。经典有限容量表格转移、计数递推见 [CSES Competitive Programmer’s Handbook, ch. 7 “Dynamic programming,” §7.4 “Knapsack problems”](https://cses.fi/book/book.pdf)，以及 §7.1 “Coin problem” 中计数解的基础状态和递推；本页将其状态和循环次序具体化到 JavaScript 一维数组。
> - Number 安全整数边界按 ECMAScript Number.MAX_SAFE_INTEGER=2⁵³−1 核对：[ECMAScript 2026 numbers](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。集合的平均访问要求见 [ECMAScript 2026 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-keyed-collections)。
