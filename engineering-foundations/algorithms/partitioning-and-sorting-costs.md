# 分区如何改变快速排序的时间和空间代价？

报表 42 的页面可能要按数值指标排序。quicksort（快速排序）先选 pivot（基准值）再分区，分区大小决定递归树的高度；连续偏斜时，即使每层都正确排序，也会反复处理接近原规模的子数组。选择分区方式时还要看算法是否修改输入、是否复制数据以及递归深度。

## 三路分区怎样处理小于、等于和大于基准的值？

下面是易检查的数组构造版：每轮把值放入 lower、equal、higher 三个新数组，递归只处理两侧。例子以数组中间位置的值为所选 pivot；这不保证它是中位数。输入应是同一可比较域中的有限数字，否则 NaN 或混合类型会破坏比较的分区含义。

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

以 [5,2,4,1,3] 为例，pivot=4：

| 阶段 | 中间结果 |
|---|---|
| 分区 | lower=[2,1,3]，equal=[4]，higher=[5] |
| 递归 | quickSort(lower)=[1,2,3]，quickSort(higher)=[5] |
| 拼接返回 | [1,2,3]+[4]+[5]=[1,2,3,4,5] |

所有与 pivot 相等的值一次归入 equal，不再递归；因此大量相同值时三路分区可减少后续工作。

## 为什么分区平衡决定递归深度？

每次分区本身扫描 n 个值，成本 Θ(n)。若每次约分成两半，递推式 T(n)=2T(n/2)+Θ(n)：每层合计处理约 n 项，约有 log₂n 层，所以总时间 Θ(n log n)、递归深度 O(log n)。若一侧为空、另一侧含 n−1 项，递推式 T(n)=T(n−1)+Θ(n)，各层工作是 n+(n−1)+…+1=n(n+1)/2，因此总时间 Θ(n²)、栈深 O(n)。取数组中间下标作为 pivot 并不保证分区平衡。例如 [7,5,3,1,2,4,6] 的中点值先是 1；递归较大侧后，下一个中点又是 2，再接着是 3，连续成为当前最小值，产生这种偏斜切分。

这段数组构造实现不是原地排序。每个递归调用为 lower、equal、higher 分配新数组，随后还分配拼接结果；不能只把递归栈当作空间成本。若切分平衡，每层处理的元素总量为 O(n)，累计数组分配为 O(n log n)，沿一条递归路径同时保留的分区规模按 n+n/2+n/4+… 增长为 O(n)；若反复偏斜，递归栈深 O(n)，沿栈仍可引用长度约为 n、n−1、n−2… 的分区数组，累计分配及保留数组总量可达 O(n²)。这里的累计分配不是峰值存活内存；实际回收时机由运行时决定。若目标是生产排序，通常优先用内置排序并明确比较器。

## 内置排序何时修改数组，何时保留副本？

~~~javascript
const values = [80, 9, 12];
const sortedInPlace = values.sort((a, b) => a - b);

const copyInput = [80, 9, 12];
const sortedCopy = copyInput.toSorted((a, b) => a - b);
~~~

sort 会把 values 原地改为 [9,12,80]；toSorted 则让 copyInput 保持 [80,9,12] 并返回一个新数组，要求运行环境支持该方法。长度为 n 的返回副本至少要写出 n 个元素；排序本身的工作和副本存储要分开算。省略比较器时，元素按字符串比较，例如 80 会排在 9 之前。数值排序要显式给出比较器。ECMAScript 2019 及之后要求排序稳定：比较器判定相等的元素保留原相对顺序；具体采用何种排序算法是引擎实现细节。

> [!example] 数值排序比较器
> [80, 9, 12].sort() 会按字符串顺序得到 [12, 80, 9]；使用 (a,b)=>a-b 才按数值递增得到 [9, 12, 80]。若排序对象数组，比较器返回 0 的对象在稳定排序后保持输入中的相对次序。

> [!info]- 来源
> - 内置排序稳定性、比较器和原地 sort 语义：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)，ECMAScript 2026。
> - 返回副本的 toSorted 语义：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)，ECMAScript 2026；Node.js v26.11.1 本地复算示例。
