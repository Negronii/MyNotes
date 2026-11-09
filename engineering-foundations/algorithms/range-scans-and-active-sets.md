# 怎样在边界前进时维护一个有效窗口或活动区间？

合成报表 42 按到达时间记录事件。一个问题要找连续 k 条事件中净变化最大的窗口，另一个问题要找出处理耗时累计达到阈值时最短的连续事件段；资源预约表则要找同一时刻最多有多少任务占用资源。前两项是 fixed-size sliding window（固定宽度滑动窗口）和 variable-size sliding window（变长滑动窗口），第三项要用扫描线。三者都维护随边界变化的状态，但输入次序、状态不变量和移动理由各不相同。

本章统一把数组窗口写成半开区间 [left, right)：包含 left，不包含 right。长度因此是 right - left；相邻的 [a, b) 与 [b, c) 不共享端点。

## 固定宽度窗口：移出一项，再加入一项

假设按到达顺序记录每个事件对待处理任务数的净变化，完成任务可为负数。输入 [4, -2, 3, 5]，求任意连续 3 条事件的最大净变化。第一段 [0, 3) 的和是 4 - 2 + 3 = 5。右边界前进一格后，新段 [1, 4) 只需移出 4、加入 5，得到 -2 + 3 + 5 = 6。

| 窗口 | 本轮变化 | 和 |
|---|---|---:|
| [0, 3) | 4 - 2 + 3 | 5 |
| [1, 4) | 旧和 5 − 移出 4 + 加入 5 | 6 |

循环不变量是：每轮比较时，sum 恰好等于当前长度为 k 的 [left, right) 中所有值的和。固定宽度意味着每次右边界多含一项、左边界少含一项，所以只需增量更新这两项；不要求数据非负。每个输入项至多加入和移出一次，扫描为 O(n) 时间、O(1) 额外空间。这里按到达顺序计算；为了套用有序数组的双指针套路而先排序，会改变连续事件的含义。

~~~javascript
function maxFixedWindowSum(values, k) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(k) || k <= 0) throw new RangeError('k must be a positive safe integer');
  for (const value of values) {
    if (!Number.isSafeInteger(value)) throw new TypeError('values must contain safe integers');
  }
  if (values.length < k) return null;

  let sum = 0;
  for (let i = 0; i < k; i++) {
    sum += values[i];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
  }
  let best = sum;

  for (let right = k; right < values.length; right++) {
    sum -= values[right - k];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
    sum += values[right];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
    if (sum > best) best = sum;
  }
  return best;
}

console.log(maxFixedWindowSum([4, -2, 3, 5], 3)); // 6
console.log(maxFixedWindowSum([], 1));            // null
~~~

若 n < k（包括空输入），没有完整窗口，函数返回 null；k 必须是正整数。示例限定所有值与中间窗口和都在 JavaScript 安全整数范围内；业务值为小数时需改用相应的数值精度约定。

## 变长窗口：只在扩展和收缩都可证明时使用

另一项报表指标是：按事件顺序找到处理耗时总和至少达到 5 毫秒的最短连续区间。每条耗时是非负安全整数。输入 [2, 1, 3, 2] 的扫描如下：

| 新加入下标 | 当前 [left, right) | 和 | 决定 |
|---:|---|---:|---|
| 0 | [0, 1) | 2 | 未达 5，继续扩展 |
| 1 | [0, 2) | 3 | 未达 5，继续扩展 |
| 2 | [0, 3) | 6 | 记录长度 3；移除下标 0 后和为 4，停止收缩 |
| 3 | [1, 4) | 6 | 记录长度 3；移除下标 1 后 [2, 4) 和为 5，记录长度 2；再移除下标 2 后和为 2，停止收缩 |

扫描结束，最短区间是 [2, 4)，即耗时 3 和 2。保持的状态是当前区间总和；右边界每次加入一项。当总和达到阈值时，当前区间有效，尝试向右移 left 来缩短它。非负输入保证移除左项不会让和变大；若移除后低于阈值，再移左就不能从当前区间产生一个有效更短后缀，因此先扩展 right。left 和 right 都只向前，每项最多进入、离开一次，时间 O(n)、额外空间 O(1)。若整个扫描从未达到阈值，返回 null。

~~~javascript
function shortestWindowAtLeast(values, target) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(target) || target <= 0) {
    throw new RangeError('target must be a positive safe integer');
  }
  for (const value of values) {
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new TypeError('values must contain non-negative safe integers');
    }
  }

  let left = 0;
  let sum = 0;
  let best = null;
  for (let right = 0; right < values.length; right++) {
    sum += values[right];
    if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');

    while (sum >= target) {
      const candidate = { start: left, end: right + 1, length: right + 1 - left };
      if (best === null || candidate.length < best.length) best = candidate;
      sum -= values[left];
      if (!Number.isSafeInteger(sum)) throw new RangeError('window sum exceeds the safe integer range');
      left++;
    }
  }
  return best;
}

console.log(shortestWindowAtLeast([2, 1, 3, 2], 5)); // { start: 2, end: 4, length: 2 }
console.log(shortestWindowAtLeast([1, 2], 5));       // null
~~~

非负约束是这段代码正确性的前提，不是对输入的清洗偏好。若绕过入口的非负检查，把相同移动规则照搬到输入 [1, -1, 5]、阈值 5 上，算法先得到整段 [0, 3) 的和 5，记录长度 3；移除 1 后和变成 4，于是停止收缩并返回长度 3。但 [2, 3) 只含 5，长度为 1。负数让扩展可以降低总和、移除左项也可以提高总和；原来的移动理由失效，不能照搬这个窗口算法。

## sweep line（扫描线）：先排序端点，再维护活动集合大小

预约区间是另一类输入：它们不按开始时间排列，需先把端点排序。对同一批合成任务，预约为 A=[1,4)、B=[2,4)、C=[4,6)。区间采用半开约定，任务在结束时刻已释放，另一个任务可在该时刻开始而不与它重叠。

扫描线按时刻由小到大处理端点。在同一时刻，先结束 [a,t) 的任务，再开始 [t,b) 的任务；代码把同刻端点合成一组，先扣除结束数，再加开始数。这样不会把端点上并不同时活动的任务临时算成重叠。该例的活动数变化为：

| 时刻 | 结束 | 开始 | 处理后活动数 | 峰值 |
|---:|---|---|---:|---:|
| 1 | — | A | 1 | 1 |
| 2 | — | B | 2 | 2 |
| 4 | A、B | C | 1 | 2 |
| 6 | C | — | 0 | 2 |

峰值是 2。若在时刻 4 先加 C 再减 A、B，会短暂算出 3，虽然没有任何时刻三项区间同时包含在内。

~~~javascript
function maxConcurrentHalfOpen(intervals) {
  if (!Array.isArray(intervals)) throw new TypeError('intervals must be an array');
  const events = [];
  for (const interval of intervals) {
    if (!interval || !Number.isFinite(interval.start) || !Number.isFinite(interval.end)) {
      throw new TypeError('each interval needs finite start and end values');
    }
    if (interval.start >= interval.end) {
      throw new RangeError('each interval must satisfy start < end');
    }
    events.push({ time: interval.start, kind: 1 });
    events.push({ time: interval.end, kind: -1 });
  }

  events.sort((a, b) => a.time - b.time || a.kind - b.kind);
  let active = 0;
  let peak = 0;
  for (let i = 0; i < events.length;) {
    const time = events[i].time;
    let starts = 0;
    let ends = 0;
    while (i < events.length && events[i].time === time) {
      if (events[i].kind === -1) ends++;
      else starts++;
      i++;
    }
    active -= ends; // [start, time) 到此已结束
    active += starts; // [time, end) 从此开始
    peak = Math.max(peak, active);
  }
  return peak;
}

console.log(maxConcurrentHalfOpen([
  { name: 'A', start: 1, end: 4 },
  { name: 'B', start: 2, end: 4 },
  { name: 'C', start: 4, end: 6 }
])); // 2
console.log(maxConcurrentHalfOpen([])); // 0
~~~

每个区间必须满足 start < end；空区间不是资源预约，函数拒绝它。排序端点需 O(n log n)，线性分组需 O(n)，事件数组占 O(n) 空间。扫描线与保留到达顺序的窗口都维护局部状态，但前者先重排端点，后者不能改变原序列；两者的正确性分别来自半开端点规则和窗口的移动不变量。

> [!info]- 来源
> - 固定/变长窗口的双指针推进、每个元素有限次进入和离开：[Antti Laaksonen, Competitive Programmer’s Handbook, 2018 draft, §8.1 “Two pointers method” 与 §8.3 “Sliding window minimum”](https://cses.fi/book.pdf)。本页的求和窗口根据各自输入前提推导；带负值的失效例子由本页代码状态复算。
> - 端点排序后维护活动集合的扫描线思路：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §9.3 “Geometric Intersections”](https://algs4.cs.princeton.edu/93intersection/)，并参看作者实现 [IntervalIntersection.java](https://algs4.cs.princeton.edu/93intersection/IntervalIntersection.java.html)。本页使用半开预约区间，因此端点相等时结束项先退出、开始项再进入；示例峰值由代码复算。
