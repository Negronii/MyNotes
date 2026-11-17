# 分区如何改变快速排序的时间和空间代价？

案例背景：合成报表 42 要按某个数值指标升序展示各行。为了只看排序过程，先省略每行的其他字段，只用一组教学用的指标值 `[5,2,4,1,3]`。quicksort（快速排序）先选一个 pivot（基准值），把输入分成比它小和比它大的两部分，再递归排序两侧。每次分区后两侧的规模决定了递归有多深，进而决定时间和空间代价。

## 三路分区怎样处理小于、等于和大于基准的值？

为了方便观察中间结果，下面写的是“构造版” quicksort：每次长度大于 1 的调用都新建 `lower`、`equal`、`higher` 三个数组，分别放小于、等于、大于基准值的项；只递归处理 `lower` 与 `higher`，最后按这三段的顺序拼接。pivot 取当前数组中间下标处的值，这只是位置上的中间，不保证是数值上的中位数。

输入约束：调用者需传入没有空槽的普通数组，每个值都是 JavaScript `number` 且不是 `NaN`。原因是：`for...of` 会把稀疏数组的空槽读成 `undefined`，而 `undefined` 和 `NaN` 与基准值做 `<`、`>` 比较都得到 false，会被错误地放进 `equal`，破坏分区。正负 `Infinity` 仍能正常比较；`-0` 和 `+0` 会进入同一个 `equal` 桶。混入其他类型还可能触发 JavaScript 的隐式类型转换，各桶就不再对应一致的数值顺序。

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

长度为 0 或 1 时直接返回原数组；长度大于 1 时不修改输入数组，而是由分区数组拼接出一个新数组返回。

输入 `[5,2,4,1,3]` 的中间下标是 2，所以 pivot=4。下表逐项展示扫描怎样改变三个桶：

| 扫描到 | lower（小于 4） | equal（等于 4） | higher（大于 4） |
|---|---|---|---|
| 开始 | [] | [] | [] |
| 5 | [] | [] | [5] |
| 2 | [2] | [] | [5] |
| 4 | [2] | [4] | [5] |
| 1 | [2,1] | [4] | [5] |
| 3 | [2,1,3] | [4] | [5] |

pivot 自身一定进入 `equal`，所以每次调用至少把 pivot 移出子问题，两侧递归的输入都严格变短，最终一定到达长度 0 或 1 的基例。接着递归处理 lower `[2,1,3]`：中间下标为 1，pivot=1；它的 higher `[2,3]` 再以下标 1 处的 3 为 pivot。各子调用的分区结果如下：

| 当前输入 | pivot | lower | equal | higher |
|---|---:|---|---|---|
| [2,1,3] | 1 | [] | [1] | [2,3] |
| [2,3] | 3 | [2] | [3] | [] |

空数组和单项数组直接返回。再自底向上拼接：`quickSort([2,3])` 得 `[2,3]`；`quickSort([2,1,3]) → [...[], ...[1], ...[2,3]] → [1,2,3]`。回到第一轮后，`[...[1,2,3], ...[4], ...[5]]` 得 `[1,2,3,4,5]`。

上面的例子没有重复值。为了单独看 `equal` 桶的作用，换一个合成输入 `[4,4,4]`：一次扫描就把三项都放进 `equal`，两侧递归数组都为空，这些相等项不再参与递归；拼接后输出 `[4,4,4]`。数据中有大量相同值时，三路分区能避免把同一批值反复送进递归。

## 为什么分区平衡决定递归深度？

成本口径：统计读过的元素数、数值比较次数、数组槽位写入数和递归深度；单次数值比较按 O(1) 计，动态数组的扩容按几何扩容的摊还模型计。长度为 n 的调用扫描 n 项，每项最多比较两次，摊还写入分区桶 n 项，拼接时再复制 n 项，所以这一次调用自身的工作是 Θ(n)（其中某一次 `push` 仍可能因扩容复制 O(n) 个槽位）。令 `L`、`E`、`R` 分别为 lower、equal、higher 的长度，`L + E + R = n`；只有 L 和 R 两部分继续递归，E 已经到位。于是递推式为 `T(n) = T(L) + T(R) + Θ(n)`。

若输入值互不相同（每次 `E=1`），且每次 `L`、`R` 大致平分其余项，那么递归树每层的子数组合计至多 n 项，共 Θ(log n) 层，总扫描量为 Θ(n log n)。如果每次都有固定比例的项进入 `E`、其余两侧仍大致平衡，那么每层的待扫描总量按几何级数递减，总扫描量只有 Θ(n)，尽管递归深度仍是 Θ(log n)。所以不能只凭递归深度推出 Θ(n log n)；极端情况下，全相等的输入只需一轮 Θ(n) 扫描。

反过来，分区一旦持续偏斜，代价就会恶化。中间下标并不保证选出接近中位数的 pivot：对合成输入 `[7,5,3,1,2,4,6]`，这段实现每次选中的恰好都是当前最小值。下表每轮的 lower 都为空、equal 只有 pivot，higher 就是下一轮的输入：

| 当前输入 | 中点 pivot | 下一轮 higher |
|---|---:|---|
| [7,5,3,1,2,4,6] | 1 | [7,5,3,2,4,6] |
| [7,5,3,2,4,6] | 2 | [7,5,3,4,6] |
| [7,5,3,4,6] | 3 | [7,5,4,6] |
| [7,5,4,6] | 4 | [7,5,6] |
| [7,5,6] | 5 | [7,6] |
| [7,6] | 6 | [7] |

结果依然正确，返回 `[1,2,3,4,5,6,7]`；但每层只少处理一个值，递推变成 `T(n)=T(n−1)+Θ(n)`，总扫描量 `n+(n−1)+…+2=Θ(n²)`，递归深度 Θ(n)。输入很大时，这样的深度还可能超出 JavaScript 引擎的调用栈限制。

空间方面，本实现不是原地排序。分析空间要分开三个问题：整个运行过程总共写了多少数组槽位；同一时刻最多有多少槽位仍可达（未被回收）；递归调用栈有多深。下表假设每个尚未返回的调用帧都还持有它用到的数组：

| 计数口径 | 分区近似平衡 | 连续偏斜 |
|---|---|---|
| 累计槽位写入 | 每个非基例调用分区与拼接共写 Θ(n) 槽位；每层子数组总长 O(n)，共 O(log n) 层，合计 O(n log n) | 依次处理 n、n−1、n−2… 项，算术和为 Θ(n²) |
| 峰值同时可达槽位 | 活动路径上未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n/2、n/4…；几何和为 O(n) | 未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n−1、n−2…；算术和可达 O(n²) |
| 递归帧数量 | O(log n) | Θ(n) |

这里的“峰值”是按调用帧仍引用数组来估算的槽位数，不等于引擎中实测的字节数；变量何时不再被引用、垃圾回收何时发生、数组容量怎样增长，都由运行时决定。

## 内置排序何时修改数组，何时保留副本？

实际代码通常直接调用内置排序。JavaScript 数组有两个排序方法：`sort()` 原地修改并返回原数组，`toSorted()`（ECMAScript 2023 引入）保留原数组、返回排好序的新数组。

~~~javascript
const values = [80, 9, 12];
const sortedInPlace = values.sort((a, b) => a - b);

const copyInput = [80, 9, 12];
const sortedCopy = copyInput.toSorted((a, b) => a - b);
~~~

| 方法 | 调用后的原数组 | 返回值 |
|---|---|---|
| `sort()` | `[9,12,80]` | 同一个数组 `[9,12,80]` |
| `toSorted()` | `[80,9,12]` | 新数组 `[9,12,80]` |

省略比较器时，`sort()` 会把元素转成字符串、按字符串顺序比较，所以 `[80,9,12].sort()` 得到 `[12,80,9]`。要按数值升序，必须显式传入 `(a,b)=>a-b` 这样的比较器，且比较器对输入要给出一致的顺序。`toSorted()` 需要运行环境支持 ES2023（如 Node.js 20 及以上和 2023 年中以后的主流浏览器）；对 n 项，它返回一个含 n 个结果的新数组，这份 O(n) 输出空间应与排序本身的开销分开计算。

自 ECMAScript 2019 起，`sort()` 必须是稳定排序，`toSorted()` 同样稳定：只要比较器给出一致的顺序，比较结果为 0 的项会保留输入中的相对次序。例如 `[A(5), B(5), C(3)]` 按分数升序后为 `[C(3), A(5), B(5)]`。不过，“原地修改并返回同一数组”只是 `sort()` 的接口行为，并不保证引擎内部排序只用 O(1) 额外空间；`toSorted()` 则另需 O(n) 个输出槽位。ECMAScript 也没有规定排序算法、比较次数或时间界，实际的比较调用序列由引擎决定。因此本文不把某个引擎实现的 O(n log n) 写成语言保证。

> [!info]- 来源
> - 三路快速排序将小于、等于、大于基准的项分开，并避免递归处理已相等项：[Robert Sedgewick 与 Kevin Wayne, *Algorithms*, 4th ed., §2.3 “Quicksort”](https://algs4.cs.princeton.edu/23quicksort/index.php)。其 `Quick3way.java` 先打乱输入再原地分区；本页保留数组构造版和中点下标 pivot，用它解释额外数组及偏斜输入的代价，不把两种实现混为一谈。
> - 输入约束中空槽及非数值比较的行为：[ECMAScript 2026 `%ArrayIteratorPrototype%.next`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-%arrayiteratorprototype%.next) 按索引读取值；空槽读为 `undefined`。[关系运算符](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-relational-operators-runtime-semantics-evaluation) 规定 `undefined` 转为 `NaN` 后比较结果为 false；[`Number::lessThan`](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-numeric-types-number-lessthan) 规定 NaN 不形成小于关系。
> - `Array.prototype.sort` 的比较器约定、稳定次序、字符串默认比较和由实现决定的比较调用序列：[ECMAScript 2019 §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort)、[ECMAScript 2026 §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `toSorted()` 创建新数组、逐项写入排序结果并使用稳定排序：[ECMAScript 2026 §23.1.3.34](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)。示例由 Node.js v26.13.0 本地复算。
> - `toSorted()` 的运行环境支持（Chrome 110、Firefox 115、Safari 16、Node.js 20 起）：[MDN `Array.prototype.toSorted()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/toSorted) 浏览器兼容性表，2026-11-17 核对。
