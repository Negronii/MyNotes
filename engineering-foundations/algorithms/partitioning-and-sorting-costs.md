# 分区如何改变快速排序的时间和空间代价？

案例背景：合成报表 42 要按数值指标升序展示。为了只看排序过程，先把每行其他字段省略，改用一组教学指标 `[5,2,4,1,3]`。quicksort（快速排序）选择 pivot（基准值），把输入分到基准值前后，再递归排序两侧；每轮分区后的左右规模决定递归树有多深。

## 三路分区怎样处理小于、等于和大于基准的值？

下面是便于观察中间数组的构造版 quicksort：它为每次非基例调用新建 lower、equal、higher 三个数组，分别放小于、等于、大于基准值的项；只递归处理 lower 与 higher，最后按这三段顺序拼接。这里的 pivot 取当前数组的中间下标，不保证是数值中位数。

调用者需传入无空槽的普通数组；每个迭代到的值都必须是 JavaScript `number` 且不是 `NaN`。在未篡改原型的普通稀疏数组中，空槽会由 `for...of` 读作 `undefined`；`undefined` 和 `NaN` 与基准值的 `<`、`>` 都会得到 false，因而被放进 `equal`，破坏数值分区。正负 `Infinity` 仍能按数值比较；`-0` 和 `+0` 在这段代码里会进入同一个 equal 桶。混合类型还可能触发 JavaScript 的类型转换，不能再把桶当作一致的数值顺序。

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

长度为 0 或 1 时直接返回原数组。长度大于 1 时函数不改写输入数组，而是用分区数组和拼接结果生成新数组。

输入 `[5,2,4,1,3]` 的中间下标是 2，所以 pivot=4。下表逐项展示扫描怎样改变三个桶：

| 扫描到 | lower（小于 4） | equal（等于 4） | higher（大于 4） |
|---|---|---|---|
| 开始 | [] | [] | [] |
| 5 | [] | [] | [5] |
| 2 | [2] | [] | [5] |
| 4 | [2] | [4] | [5] |
| 1 | [2,1] | [4] | [5] |
| 3 | [2,1,3] | [4] | [5] |

所选 pivot 本身会进入 `equal`，所以每个长度大于 1 的调用至少从子问题中移走 pivot；两侧递归输入都严格短于当前数组，最终会到达长度 0 或 1 的基例。lower `[2,1,3]` 的中点下标为 1、pivot=1；其 higher `[2,3]` 再以中点下标 1 的 3 为 pivot。各子调用分区后的桶如下：

| 当前输入 | pivot | lower | equal | higher |
|---|---:|---|---|---|
| [2,1,3] | 1 | [] | [1] | [2,3] |
| [2,3] | 3 | [2] | [3] | [] |

空数组和单项数组都到达递归基。自底向上拼接：`quickSort([2,3])` 得 `[2,3]`；`quickSort([2,1,3]) → [...[], ...[1], ...[2,3]] → [1,2,3]`。回到第一轮后，`[...[1,2,3], ...[4], ...[5]]` 得 `[1,2,3,4,5]`。

为单独看重复值的分支，换成更小的合成输入 `[4,4,4]`：一次扫描就把三项都放进 equal，两个递归数组为空，不会再递归处理这些相等项；返回时拼接两个空结果和 `[4,4,4]`，输出仍是 `[4,4,4]`。大量相同值时，这能避免把同一批值反复切进递归。

## 为什么分区平衡决定递归深度？

复杂度按当前调用读过的元素数、数值比较、数组槽位写入和递归深度计算；假设单次数值比较为 O(1)，普通动态数组按几何扩容的摊还模型计算。长度为 n 的调用会扫描 n 项，每项最多做两次数值比较，向分区桶摊还写入 n 项，再在拼接时复制 n 项，所以本层工作为 Θ(n)；一次 `push` 仍可能因扩容复制 O(n) 个槽位。令 `L`、`E`、`R` 分别为 lower、equal、higher 的长度，满足 `L + E + R = n`；只有 L 与 R 会递归，E 已经归位。一般递推为 `T(n) = T(L) + T(R) + Θ(n)`。

若输入值在这段比较下互异（每次 `E=1`），且每个非基例调用的 `L`、`R` 近似均分其余项，那么每层至多扫描 n 项，其中靠近根的 Θ(log n) 层各扫描 Θ(n) 项；递归总深度为 Θ(log n)，因此总扫描为 Θ(n log n)。如果每个调用都有固定正比例的项进入 `E`，且剩余两侧持续近似平衡，各层待扫描规模会按几何比例递减，总扫描为 Θ(n)，即使递归深度仍是 Θ(log n)。因此不能只凭树深度推出 Θ(n log n)；全相等输入只需一轮 Θ(n) 扫描。

中点下标不保证 pivot 接近数值中位数。例如合成输入 `[7,5,3,1,2,4,6]` 中，这段实现每次都选出当前最小项。下表的每轮 lower 都为空、equal 只有 pivot；higher 是下一次非空调用：

| 当前输入 | 中点 pivot | 下一轮 higher |
|---|---:|---|
| [7,5,3,1,2,4,6] | 1 | [7,5,3,2,4,6] |
| [7,5,3,2,4,6] | 2 | [7,5,3,4,6] |
| [7,5,3,4,6] | 3 | [7,5,4,6] |
| [7,5,4,6] | 4 | [7,5,6] |
| [7,5,6] | 5 | [7,6] |
| [7,6] | 6 | [7] |

每轮把当前最小值放在结果前，完整递归仍返回 `[1,2,3,4,5,6,7]`；只是每层只少处理一个值，递推成为 `T(n)=T(n−1)+Θ(n)`，也就是 `n+(n−1)+…+2=Θ(n²)`；递归深度为 Θ(n)。大型输入的实际最大深度还受 JavaScript 引擎调用栈限制。

本实现并非原地排序。要读空间成本，先分开三个问题：整个运行总共写过多少数组槽位、某一时刻有多少数组槽位同时可达、递归调用栈有多深。按代码所需数组都由未返回的调用帧保留来估算：

| 计数口径 | 分区近似平衡 | 连续偏斜 |
|---|---|---|
| 累计槽位写入 | 每个非基例调用分区与拼接共写 Θ(n) 槽位；每层子数组总长 O(n)，共 O(log n) 层，合计 O(n log n) | 依次处理 n、n−1、n−2… 项，算术和为 Θ(n²) |
| 峰值同时可达槽位 | 活动路径上未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n/2、n/4…；几何和为 O(n) | 未返回帧引用的输入、分区桶和拼接进度，随子问题规模约为 n、n−1、n−2…；算术和可达 O(n²) |
| 递归帧数量 | O(log n) | Θ(n) |

这里的峰值是调用帧仍引用数组时的槽位模型，不等于引擎实测字节数；变量回收、垃圾回收时机和容量增长由运行时决定。

## 内置排序何时修改数组，何时保留副本？

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

省略比较器时，`sort()` 将元素转成字符串再按字符串顺序比较，因此 `[80,9,12].sort()` 得到 `[12,80,9]`；数值升序要显式给出 `(a,b)=>a-b` 这样的比较器，并让比较器对输入给出一致顺序。`toSorted()` 只有在运行环境支持该方法时才可用。对 n 项，它会返回一个存放 n 个结果的新数组；这份 O(n) 输出空间应与排序本身分开计算。

自 ECMAScript 2019 起，`sort()` 要求稳定；`toSorted()` 也使用稳定排序。对给出一致顺序的比较器，比较结果为 0 的项保留输入中的相对次序。例如 `[A(5), B(5), C(3)]` 按分数升序后为 `[C(3), A(5), B(5)]`。但“原地修改并返回同一数组”是 `sort()` 的接口行为，不保证实现内部排序时使用 O(1) 额外空间；`toSorted()` 还需为结果创建 O(n) 个输出槽位。ECMAScript 也没有规定排序算法或可移植的比较次数/时间界；实际比较调用序列由运行时实现决定。因此这里不把某个引擎的 O(n log n) 实现细节写成语言保证。

> [!info]- 来源
> - 三路快速排序将小于、等于、大于基准的项分开，并避免递归处理已相等项：[Robert Sedgewick 与 Kevin Wayne, *Algorithms*, 4th ed., §2.3 “Quicksort”](https://algs4.cs.princeton.edu/23quicksort/index.php)。其 `Quick3way.java` 先打乱输入再原地分区；本页保留数组构造版和中点下标 pivot，用它解释额外数组及偏斜输入的代价，不把两种实现混为一谈。
> - 输入约束中空槽及非数值比较的行为：[ECMAScript 2026 `%ArrayIteratorPrototype%.next`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-%arrayiteratorprototype%.next) 按索引读取值；空槽读为 `undefined`。[关系运算符](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-relational-operators-runtime-semantics-evaluation) 规定 `undefined` 转为 `NaN` 后比较结果为 false；[`Number::lessThan`](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-numeric-types-number-lessthan) 规定 NaN 不形成小于关系。
> - `Array.prototype.sort` 的比较器约定、稳定次序、字符串默认比较和由实现决定的比较调用序列：[ECMAScript 2019 §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort)、[ECMAScript 2026 §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `toSorted()` 创建新数组、逐项写入排序结果并使用稳定排序：[ECMAScript 2026 §23.1.3.34](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)。示例由 Node.js v26.13.0 本地复算。
