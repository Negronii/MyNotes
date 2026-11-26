# 分区怎样改变快速排序的时间和空间代价？

[有序查找章](ordered-search-and-two-pointers.md)的二分查找和相向双指针都假设数据已按同一比较器排好；数据无序时，要先付一笔排序成本。本章用 quicksort (快速排序) 说明这笔成本从哪里来：选一个 pivot (基准值)，把输入分成比它小、等于它、比它大的几部分，再递归处理两侧。每次分区后两侧的规模，决定了递归有多深、总共扫描多少元素、同时占用多少内存。

例子换成一组独立的小数组 `[5, 2, 4, 1, 3]`：事件页的复合键会让每一步都多出字段比较，看不清分区本身。

## 三路分区：小于、等于、大于各进一个桶

为了看清中间结果，下面写的是“构造版” quicksort：每次长度大于 1 的调用都新建 `lower`、`equal`、`higher` 三个数组，只递归处理 `lower` 与 `higher`，最后按三段顺序拼接。pivot 取当前数组中间下标处的值；这只是位置上的中间，不保证是数值上的中位数。

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

长度为 0 或 1 时直接返回原数组；更长时不修改输入，返回拼接出的新数组。

`[5, 2, 4, 1, 3]` 的中间下标是 2，pivot = 4。扫描过程中三个桶的变化：

| 扫描到 | lower（< 4） | equal（= 4） | higher（> 4） |
|---|---|---|---|
| 开始 | [] | [] | [] |
| 5 | [] | [] | [5] |
| 2 | [2] | [] | [5] |
| 4 | [2] | [4] | [5] |
| 1 | [2,1] | [4] | [5] |
| 3 | [2,1,3] | [4] | [5] |

pivot 自己一定进 `equal`，所以每次调用至少把一个元素移出子问题，两侧递归的输入严格变短，最终一定到达长度 0 或 1 的基例。接着递归处理两侧：

| 当前输入 | pivot（中间下标） | lower | equal | higher |
|---|---:|---|---|---|
| [2,1,3] | 1（下标 1） | [] | [1] | [2,3] |
| [2,3] | 3（下标 1） | [2] | [3] | [] |

自底向上拼接：`quickSort([2,3])` 得 `[2,3]`；`quickSort([2,1,3])` 得 `[...[], 1, ...[2,3]] = [1,2,3]`；回到第一层，`[...[1,2,3], 4, ...[5]] = [1,2,3,4,5]`。

## 分区要求输入构成一致的全序

`<` 和 `>` 能把每个值放进唯一正确的桶，前提是所有值之间有一致的全序。下面几种输入会悄悄破坏这一点：

- **`NaN`**：它与任何值做 `<`、`>` 都得 false，于是被放进 `equal`，混在 pivot 旁边输出；若 pivot 本身恰好是 `NaN`，所有值都进 `equal`，这一层原样输出、不再排序。
- **稀疏数组的空位**：`for...of` 把空位读成 `undefined`，比较时转成 `NaN`，结果同上。
- **混合类型**：数字与字符串等混在一起时会触发隐式转换，各桶不再对应一致的数值顺序。

`±Infinity` 能正常比较；`-0` 和 `+0` 互不小于也互不大于，会进同一个 `equal` 桶。所以这段代码要求输入是没有空位的普通数组，每项都是 `number` 且不是 `NaN`。

## 相等项多时，equal 桶省掉什么

上面的例子没有重复值。换成 `[4, 4, 4]`：一次扫描就把三项都放进 `equal`，两侧递归数组都为空，输出 `[4, 4, 4]`。相等项一旦进了 `equal` 就不再参与递归；数据中有大量相同值时，三路分区避免把同一批值反复送进下一层。

## 时间：看递推式，不只看递归深度

成本口径：统计读过的元素数、比较次数、数组槽位写入数和递归深度；一次数值比较按 O(1) 计，动态数组扩容按几何扩容的摊还模型计（口径见[首章](invariants-and-cost-models.md)）。长度为 n 的调用扫描 n 项，每项至多比较两次，分区写入 n 项，拼接再复制 n 项，所以一次调用自身的工作是 Θ(n)。

令 `L`、`E`、`R` 分别为三个桶的长度，`L + E + R = n`。只有 `L` 和 `R` 继续递归，于是

`T(n) = T(L) + T(R) + Θ(n)`

三种情形给出不同结论：

| 分区情形 | 每层合计扫描 | 递归深度 | 总扫描量 |
|---|---|---|---|
| 值互不相同（`E = 1`），两侧大致平分 | 至多 n | Θ(log n) | Θ(n log n) |
| 每层固定比例的项进 `equal`，其余两侧大致平衡 | 按几何级数递减 | Θ(log n) | Θ(n) |
| 持续偏斜：每层只少一个值 | n, n−1, n−2, … | Θ(n) | Θ(n²) |

第二行说明不能只凭“深度 Θ(log n)”推出 Θ(n log n)：深度相同，每层的工作量却在缩小。极端情况下，全相等的输入一轮 Θ(n) 扫描就结束。

中间下标并不能防止第三行。合成输入 `[7, 5, 3, 1, 2, 4, 6]` 会让这段实现每次都恰好选中当前最小值：

| 当前输入 | 中点 pivot | 下一轮 higher |
|---|---:|---|
| [7,5,3,1,2,4,6] | 1 | [7,5,3,2,4,6] |
| [7,5,3,2,4,6] | 2 | [7,5,3,4,6] |
| [7,5,3,4,6] | 3 | [7,5,4,6] |
| [7,5,4,6] | 4 | [7,5,6] |
| [7,5,6] | 5 | [7,6] |
| [7,6] | 6 | [7] |

结果依然正确，是 `[1,2,3,4,5,6,7]`；但递推变成 `T(n) = T(n−1) + Θ(n)`，总扫描量 `n + (n−1) + … + 2 = Θ(n²)`，递归深度 Θ(n)。输入很大时，这样的深度还可能超出引擎的调用栈上限。

## 空间：写入总量、峰值和栈深分开算

构造版不是原地排序。分析内存要分开问三件事：整个运行过程一共写了多少槽位；同一时刻最多有多少槽位仍然可达；调用栈有多深。下表假设每个尚未返回的调用帧都还持有它用到的数组：

| 计数口径 | 分区近似平衡 | 持续偏斜 |
|---|---|---|
| 累计槽位写入 | 每层子数组合计 O(n)，共 O(log n) 层：O(n log n) | n + (n−1) + …：Θ(n²) |
| 峰值同时可达槽位 | 活动路径上的数组约为 n、n/2、n/4…，几何和 O(n) | 约为 n、n−1、n−2…，算术和可达 O(n²) |
| 递归帧数 | O(log n) | Θ(n) |

“峰值”是按调用帧仍引用数组估算的槽位数，不是引擎里实测的字节数；变量何时不再被引用、何时回收、数组容量怎样增长，都由运行时决定。

原地实现不建新数组。Sedgewick 与 Wayne 的 `Quick3way` 先随机打乱输入，再在原数组上做三路分区，额外空间只剩递归栈；打乱是为了让依赖输入次序的持续偏斜难以出现。它的下标维护不在本章展开。

## 实际代码用内置排序

日常代码直接调用语言的内置排序。ECMAScript 规定了 `Array.prototype.sort` 的比较器约定和稳定性，但不规定排序算法、比较次数、时间界或额外空间，所以“O(n log n)”只是按某种比较排序估算的成本，不是语言保证（各种保证的口径见[首章](invariants-and-cost-models.md)）。`sort` 原地修改与 `toSorted` 返回副本的差别、省略比较器时按字符串比较的陷阱，见前端章节的[排序：默认按字符串比较](../../frontend/javascript/arrays-maps-and-sets.md#排序：默认按字符串比较)。

## 排序成本回到选型

本章产出一条判断：排序的时间和内存由每次分区的平衡程度决定，要分别报告总扫描量、峰值内存和栈深，而不是只写一个 O(n log n)。回到有序查找章，“先排序再二分”的总成本要把这一项算进去；数据只查一次时，线性扫描往往更便宜。主线接着读[边界向前推进时，怎样维护一个有效窗口或活动区间？](sliding-windows-and-sweep-lines.md)，其中扫描线也要先付一次端点排序的成本。

> [!info]- 来源
> - 三路快速排序把小于、等于、大于基准的项分开，不再递归处理相等项；`Quick3way` 先打乱输入再原地分区：[Robert Sedgewick 与 Kevin Wayne, *Algorithms*, 4th ed., §2.3 “Quicksort”](https://algs4.cs.princeton.edu/23quicksort/index.php)。本页保留数组构造版和中点下标 pivot，用它说明额外数组与偏斜输入的代价；分区表、偏斜表与三种情形的递推按本页代码复算。
> - 空位与非数值比较的行为：[ECMAScript 2026 `%ArrayIteratorPrototype%.next`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-%arrayiteratorprototype%.next)（按索引读取，空位读为 `undefined`）；[关系运算符](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-relational-operators-runtime-semantics-evaluation)（`undefined` 转为 `NaN` 后比较为 false）；[`Number::lessThan`](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-numeric-types-number-lessthan)（`NaN` 不形成小于关系）。
> - `Array.prototype.sort` 的比较器约定、稳定次序与由实现决定的比较调用序列，规范不规定时间界：[ECMAScript 2026 §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)；稳定性自 [ECMAScript 2019 §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort) 起要求。
