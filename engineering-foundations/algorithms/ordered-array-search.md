# 有序数据怎样让二分查找和双指针安全排除候选？

报表 42 的事件页按 (occurred_at, event_id) 升序排列。若目标游标与这组键使用同一比较规则，binary search（二分查找）可以丢弃一半候选；若数组无序或只按 event_id 比较，就不能从时间顺序推断安全的排除范围。two pointers（双指针）也依赖同样的证明：每次移动前要说明为何被排除的一整批组合不可能成为答案。

## 二分查找如何缩小有序区间？

binary search（二分查找）在升序数组中维持闭区间 [left, right]。比较中点后，若中点小于目标，则它及左侧元素都不可能匹配，令 left=middle+1；若大于目标，右侧同理。下例返回任意一个匹配下标；空数组或找不到目标时返回 -1。

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

标量示例可传入 `(a, b) => a - b`。以 [3, 7, 11, 15, 19, 23, 27] 查找 19：循环不变式是“若目标存在，它仍在当前闭区间”。

| 轮次 | 当前区间 | 中点和值 | 更新 |
|---|---|---|---|
| 1 | [0,6] | 3 → 15 | 目标更大，left=4 |
| 2 | [4,6] | 5 → 23 | 目标更小，right=4 |
| 3 | [4,4] | 4 → 19 | 命中 |

若改查 20，前两轮后比较 19 并令 left=5，区间变空，返回 -1。

固定宽度整数语言中用 left + floor((right-left)/2) 避免 left+right 溢出。JavaScript 数组索引本身远小于 Number 精确整数上限，但差值写法便于移植。若要找重复值的第一个位置，应改用 lower bound：命中时仍收缩右半边，而非立刻返回。

报表 42 的游标按 `(occurred_at, event_id)` 字典序比较：先比 occurred_at，只有时间相同才比 event_id。下面假设时间使用统一 UTC、固定精度的 ISO 8601 字符串，且字典序与时间顺序一致，event_id 是安全整数；生产代码的比较器还必须与数据库的类型、空值顺序和排序规则一致。

~~~javascript
function compareEvent(a, b) {
  if (a.occurred_at < b.occurred_at) return -1;
  if (a.occurred_at > b.occurred_at) return 1;
  return a.event_id < b.event_id ? -1 : a.event_id > b.event_id ? 1 : 0;
}
~~~

| 排序行 | occurred_at | event_id | 与游标 (09:00, 41) 的顺序 |
|---|---|---:|---|
| A | 09:00 | 41 | 相等，确切命中游标 |
| B | 09:00 | 42 | 大于游标，下一页边界候选 |
| C | 09:01 | 13 | 也大于游标，但排在 B 后 |

比较器必须对同一排序域稳定地返回负数、零或正数。`binarySearch` 用 `compareEvent` 可以查确切游标；分页取下一页时通常要找第一个比较结果严格大于零的行（upper bound，上界），不能要求游标行仍存在。若行 A 已删除，B 仍是正确边界；这依赖相同排序规则、有效游标及相同数据范围，并要求 `(occurred_at,event_id)` 在该范围内唯一。若两个记录排序键完全相同，而页尾停在两者之间，严格 `>` 会跳过后一条；应加上唯一的 tie-breaker（平局裁决键）。表中时间为完整时间戳的简写，C 的 ID 虽更小，仍因时间更晚而排在 B 后。

## 双指针何时能替代重复扫描？

双指针仅在排序或移动不变量能证明安全时减少搜索空间；它不是一般嵌套循环的替代品。

### 有序数组两数之和

数组升序时，若两端和小于 target，左端值与任何剩余右端相加都不会更大，因此 left 可以前进；若和过大，right 可后退。下例返回两个不同位置的下标或 null；重复值可被不同下标选中。输入假设为有限安全整数，避免 Number 精度和溢出语义影响比较。

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

### 把零移到末尾并保留其他次序

next 表示下一个非零值应该写入的位置。每遇到非零值就与该位置交换，因此非零元素相对顺序不变，函数原地修改并返回同一数组。

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

> [!example] 两个指针怎样缩小候选集合
> 对 [1, 2, 4, 7, 11] 求和为 9：两端 1+11=12 太大，排除 11 与当前或更大左端值的组合，右指针左移；1+7=8 太小，排除 1 与当前/更小右项的组合，左指针右移；2+7=9，返回 [1,3]。排序是这项证明的前提。

> [!info]- 来源
> - 二分与双指针不变量按本页闭区间/升序数组逐步复算；事件页复合游标必须使用与来源排序相同的字典序比较。
