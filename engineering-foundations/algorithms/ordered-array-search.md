# 有序数据怎样让二分查找和双指针安全排除候选？

案例背景：报表 42 已取回一页按 (occurred_at, event_id) 升序排列的事件。需要在页内定位记录、找出分页边界，并在其他已排序数组上找两数之和。本页用同一排序规则追踪每轮能排除什么；排序、比较器和返回结果约束必须一致。最后的零值压缩例子不依赖排序，它使用读写下标不变量。

## 二分查找如何缩小有序区间？

精确查找要求输入已按比较器定义的升序排列，目标也在同一键域里；比较器每次对同一对值给出相同符号，且这些比较结果能传递地定义顺序。下面的闭区间版本返回任意一个相等项的下标；空数组或找不到目标时返回 -1。若有重复项，命中不保证是第一个。

~~~javascript
function binarySearch(values, target, compare) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    const order = compare(values[middle], target);
    if (order === 0) return middle;
    if (order < 0) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

先用便于手算的数字输入 `[3, 7, 11, 15, 19, 23, 27]` 查找 19；对本例有限数值，可传入比较器 `(a, b) => a - b`，其符号表示数值顺序。循环不变量是：若目标存在，它仍在当前闭区间 `[left, right]` 中。

| 轮次 | 当前闭区间 | 中点下标和值 | 比较后的动作 |
|---|---|---|---|
| 1 | `[0,6]` | `3 → 15` | `15 < 19`，排除下标 0–3，令 `left=4` |
| 2 | `[4,6]` | `5 → 23` | `23 > 19`，排除下标 5–6，令 `right=4` |
| 3 | `[4,4]` | `4 → 19` | 命中并返回下标 4 |

若查找 20，前两次更新相同；第三次比较下标 4 的 19，令 `left=5`，闭区间 `[5,4]` 变空，返回 -1。若目标不在数组中，闭区间最终会变空。键序一致性还解释复杂度：中点小于目标时，从 `left` 到 `middle` 都更小；中点大于目标时，从 `middle` 到 `right` 都更大。一次比较因此舍弃至少一半候选，剩余候选每轮至多为原来的一半，最多比较 O(log n) 次键，额外空间 O(1)。中点写作 `left + floor((right-left)/2)`，在固定宽度整数语言中可避免先算 `left+right` 溢出；JavaScript 数组长度本身远低于 Number 的精确整数上限，但差值写法便于移植。若输入无序或比较器不匹配排序规则，不能按此方式排除。

**回到报表 42：复合键要逐字段比较。** 排序键先比较 `occurred_at`，时间相等时再比较 `event_id`。示例把时间存为统一 UTC、相同固定精度的 ISO 8601 字符串，因此字符串顺序与时间顺序一致；ID 用两位数字的固定宽度 `eNN` 字符串，因此字典序与示例编号顺序一致。生产比较器还须与数据库的字段类型、空值顺序和排序规则相同。

~~~javascript
function compareEvent(a, b) {
  if (a.occurred_at < b.occurred_at) return -1;
  if (a.occurred_at > b.occurred_at) return 1;
  if (a.event_id < b.event_id) return -1;
  if (a.event_id > b.event_id) return 1;
  return 0;
}
~~~

同一时刻时 ID 决定顺序；但时间优先于 ID。以下复用完整合成页：e07 在 09:00，e03、e11 在 09:02，e18 在 09:05。e03 的 ID 小于 e07，但时间更晚，所以仍排在 e07 后面。只按 `event_id` 搜索这份按时间和 ID 复合键排序的数组，并不满足二分所需的升序条件。

| 排序行 | `occurred_at` | `event_id` | 与游标 `(09:00, e07)` 的关系 |
|---|---|---|---|
| e07 | 09:00 | e07 | 相等 |
| e03 | 09:02 | e03 | 更大；时间更晚，即使 ID 字典序更小 |
| e11 | 09:02 | e11 | 更大；时间晚于游标。两条 09:02 记录中，e11 排在 e03 后 |
| e18 | 09:05 | e18 | 更大；时间更晚 |

`compareEvent` 可以用于精确查找，也可以求边界；生产用值应是完整时间戳，表格中的时分为简写。用于分页时，完整排序键 `(occurred_at, event_id)` 必须能区分每条记录；若仍有完整键相同的记录，才需增加一个同样用于排序和分页、能区分这些记录的 tie-breaker（平局裁决键）。

~~~javascript
const events = [
  { occurred_at: '2026-11-12T09:00:00.000Z', event_id: 'e07' },
  { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e03' },
  { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e11' },
  { occurred_at: '2026-11-12T09:05:00.000Z', event_id: 'e18' }
];

console.log(binarySearch(events, events[1], compareEvent)); // 1：精确找到 e03
~~~

**找边界时，元素范围与答案边界不是同一个区间。** 对已加载页的升序数组，`lower_bound` 返回首个键 `>= target` 的下标；所有键都小于目标时返回 `n`。设可能继续探测的元素下标为半开区间 `[lo, hi)`，可能的答案边界则在闭区间 `[lo, hi]`。初值 `lo=0, hi=n`，不变量是 `lo` 左侧的键都 `< target`，`hi` 起的键都 `>= target`。若中点小于目标，令 `lo=mid+1`；否则 `mid` 仍可能是答案，令 `hi=mid`。

~~~javascript
function bound(values, target, compare, afterEquals = false) {
  let lo = 0;
  let hi = values.length;
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    const order = compare(values[mid], target);
    if (order < 0 || (afterEquals && order === 0)) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

const target = { occurred_at: '2026-11-12T09:02:00.000Z', event_id: 'e08' };

console.log(bound(events, target, compareEvent)); // 2：首个 >= target
console.log(bound(events, events[1], compareEvent)); // 1：首个 >= (09:02,e03)
console.log(bound(events, events[1], compareEvent, true)); // 2：首个 > (09:02,e03)
~~~

查询键为 `(09:02,e08)`，两条同时间记录之间没有相等项。下表逐轮记录元素范围与边界候选：

| 当前状态 | 元素探测范围 | 候选边界 | 中点 | 比较与更新 |
|---|---|---|---:|---|
| 第 1 轮 | `[0,4)` | `[0,4]` | 2，`(09:02,e11)` | 大于目标，令 `hi=2`；下标 2 不再探测，但边界 2 保留 |
| 第 2 轮 | `[0,2)` | `[0,2]` | 1，`(09:02,e03)` | 小于目标，令 `lo=2` |
| 结束 | `[2,2)` | `[2,2]` | — | 探测范围为空，唯一边界为 2，首个符合项是 `(09:02,e11)` |

若要找第一条与目标相等的记录，先用 `lower_bound` 求 `pos`，再检查 `pos < n && compare(values[pos], target) === 0`；否则 `pos` 可能指向第一个更大项或等于数组长度 `n`，不能当作命中。分页读取下一页通常要求严格 `> cursor`，应找首个严格大于目标的边界，即 `upper_bound`。本代码将 `afterEquals` 设为 `true`，让相等项也被跳过；此时不变量改为 `lo` 左侧的键都 `<= target`、`hi` 起的键都 `> target`，循环结束时返回当前已加载数组中第一条严格大于游标的记录位置；若没有更大键则返回 `n`。已加载页的边界不是数据库下一页查询本身；查询仍需用相同查询范围、排序规则及严格游标条件继续取数。已有游标 `(09:02,e03)` 时，`lower_bound` 返回 1（游标自身），`upper_bound` 返回 2（当前页中下一条）。即使游标行已删除，只要继续使用同一完整排序键，严格边界仍可定位第一条更大的记录。两条记录若排序键完全相同，游标落在两者之间时严格 `>` 会跳过后一条，因此用于分页的键必须唯一或增加 tie-breaker。

两个边界版本都从 `[0,n)` 开始，每轮剩余的待探测项数至多为原来的一半，因此最多做 O(log n) 次键比较、使用 O(1) 额外空间。本例键字段是固定长度，故一次比较按 O(1) 计；若键长度随输入增长，应另计比较成本。无序数组没有由当前顺序定义的 lower/upper bound；若只查记录是否存在，可以线性扫描并返回匹配项或未找到。若要找有序边界，须先按同一比较器排序或换用满足该顺序不变量的数据结构，并计入建立有序表示的成本。

## 双指针何时能替代重复扫描？

双指针不是一般嵌套循环的替代品。下面的两数之和依赖数组升序；零值压缩则不要求排序，它按读写位置推进。两种做法都要给出每个指针能前进的理由。

### 有序数组两数之和

输入需按数值升序排列。为让这段 JavaScript `Number` 代码中的整数比较精确，本例把值、`target` 及每次计算的两端和都限在安全整数范围内；若业务数据超出该范围，应使用精确数值类型并匹配其比较器。若两端和小于 `target`，固定左端时它已经与剩余最大项相加，和仍不足，所以当前左端不可能参与答案；若两端和大于 `target`，固定右端时它已与剩余最小项相加，和仍过大，所以当前右端不可能参与答案。按本轮证明排除一端后，另一端无需回头。

~~~javascript
function twoSumSorted(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left < right) {
    const sum = values[left] + values[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return null;
}
~~~

本例输入 `[1, 2, 4, 7, 11]`，`target=9`；函数返回一对下标或 `null`，值和目标是可精确比较的小整数。下标必须不同，`left < right` 正是这一结果约束：

| 步骤 | `left` 与值 | `right` 与值 | 和 | 排除理由或结果 |
|---|---|---|---:|---|
| 1 | `0:1` | `4:11` | 12 | `12 > 9`；右端 11 与其余任一左值配对也会过大，`right=3` |
| 2 | `0:1` | `3:7` | 8 | `8 < 9`；左端 1 与其余任一右值配对也不足，`left=1` |
| 3 | `1:2` | `3:7` | 9 | 命中，返回下标 `[1,3]` |

循环不变量是：所有尚未排除的解都只能由当前 `left` 到 `right` 之间的两个不同下标组成。表中的每次移动都证明被删去的一端不可能再参与解；指针相遇或交错时，候选集合为空。每轮至少移动一个端点，因此总扫描 O(n) 时间、O(1) 额外空间。重复数值也可由不同下标组成解，例如 `[2,2]` 求 4；若目标不存在，循环结束后返回 `null`。数组未排序时，上述极值论证不成立，不能照搬这两个移动方向。例如未排序的 `[3,1,2]` 对目标 3 有下标 `[1,2]` 这一解，但这段代码会先将右指针左移两次并返回 `null`。若必须先排序，移动结果下标属于排序后的数组；需要原数组下标时还须保留位置映射并计入排序成本。

### 把零移到末尾并保留其他次序

这项双指针操作不靠排序。循环开始处理下标 `i` 时，`[0,next)` 保存已扫描的非零值且顺序与原输入相同，`[next,i)` 全是零，`[i,n)` 尚未扫描。若当前值是零，`next` 不动；若当前值是非零值且 `next<i`，`[next,i)` 已全为零，交换把该非零值写入 `next`，并把原来 `next` 处的零移到 `i`；若 `next===i`，数组已在正确位置，代码的自交换不改变它。处理完当前值并推进 `i` 后，相同不变量重新成立。

~~~javascript
function moveZeros(values) {
  let next = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== 0) {
      [values[next], values[i]] = [values[i], values[next]];
      next++;
    }
  }
  return values;
}
~~~

以 `[0,1,0,3,12]` 为例。每步处理前，`next` 都是下一个非零值的落点；扫描结束后剩余后缀全是零：

| 处理下标 `i` | 处理前 `next` | 操作 | 处理后的数组 | 新 `next` |
|---:|---:|---|---|---:|
| 0 | 0 | 值为 0，跳过 | `[0,1,0,3,12]` | 0 |
| 1 | 0 | 交换下标 0 与 1 | `[1,0,0,3,12]` | 1 |
| 2 | 1 | 值为 0，跳过 | `[1,0,0,3,12]` | 1 |
| 3 | 1 | 交换下标 1 与 3 | `[1,3,0,0,12]` | 2 |
| 4 | 2 | 交换下标 2 与 4 | `[1,3,12,0,0]` | 3 |

函数返回同一个数组，时间 O(n)、额外空间 O(1)。它适用于稠密数组，并把严格等于 0 的项（包括 -0）移到末尾，其他项保持扫描时的相对次序。若要把 null、空字符串或其他值也当作零，需改写判定条件；若输入含空槽，迭代会读到缺失值并把它当作非零值移动，需先定义所需语义。

> [!info]- 来源
> - 二分在升序数组中比较中点并缩小区间：[NIST Dictionary of Algorithms and Data Structures, “binary search”](https://xlinux.nist.gov/dads/HTML/binarySearch.html)。本页闭区间精确查找和半开边界查找按所列不变量分别推导。
> - 双指针只在端点单向移动且每步排除成立时为线性扫描：[Antti Laaksonen, *Competitive Programmer’s Handbook*, “Two pointers method”](https://cses.fi/book/book.pdf)。两数之和的排除证明与零值压缩状态按本页例子复算。
> - 时间字符串字典序与时间顺序一致的条件：[RFC 3339 §5.1 “Ordering”](https://www.rfc-editor.org/rfc/rfc3339.html#section-5.1)：时区、Z/偏移写法和小数位数需相同。
