# 怎样在不断加入任务时持续取出最高优先级？

合成报表 42 有多个待处理任务，系统一边接收新任务，一边要取出当前最紧急的一项。若每次都重新排序整个集合，就会重复整理旧任务。priority queue（优先队列）只要求快速插入和取出当前最高优先级项；binary heap（二叉堆）用一条父子顺序约束支持这两项操作。

## 堆序只规定父子关系，不会把数组排好序

以下用最大堆，优先级较大的任务靠近根。把完全二叉树（最后一层从左向右填充）按层从左到右放入数组，使用 0 起始下标时，只有 i > 0 的位置才有父节点，父节点下标是 floor((i - 1) / 2)，子节点是 2i + 1 与 2i + 2。堆序要求任一父项不低于它的孩子；除根以外，数组并不保证整体有序。

~~~mermaid
flowchart TD
    i0["下标 0：根"]
    i1["下标 1：左子，2i+1"]
    i2["下标 2：右子，2i+2"]
    i0 --> i1
    i0 --> i2
~~~

本例约定同优先级按先到先出，因此入堆时另带递增序号。表中任务 A 和 B 优先级同为 5，A 先到；C 优先级为 8。

| 操作 | 堆数组（从根到叶） | 发生的修复 |
|---|---|---|
| 插入 A(5) | [A(5)] | 根无需调整 |
| 插入 B(5) | [A(5), B(5)] | 同优先级时 A 序号较早，不交换 |
| 插入 C(8) | [C(8), B(5), A(5)] | C 从下标 2 上浮到根 |
| 取出 | [A(5), B(5)] | 返回 C；末项 A 移到根，与同优先级且较晚的 B 保持先后次序 |

插入时先放数组末尾，再沿父节点上浮；删除根时以末项填根，再沿更高优先级的孩子下沉。堆高为 O(log n)，所以 push 和 pop 各需 O(log n)，peek 为 O(1)，额外存储 O(n)。如果所有元素一开始都已知，可以从最后一个非叶节点向根逐层下沉来建堆，整体 O(n)；若元素逐个到达，则用 push，累计为 O(n log n)。线性 heapify（自底向上建堆）的前提是能同时访问整批初始元素。

普通堆若只比较 priority，并不保证并列项稳定；稳定行为来自代码中的 sequence 次级键。此实现用 BigInt 序号，优先级必须是有限数；进入队列的优先级与序号保持不变。空堆的 peek 和 pop 都返回 null，实际任务包装在对象中，所以任务 value 本身即使是 null，也不与空队列混淆。

> [!example]- 可运行：稳定最大优先队列
> ~~~javascript
> class BinaryHeap {
>   constructor(higher) {
>     if (typeof higher !== 'function') throw new TypeError('higher must be a function');
>     this.higher = higher;
>     this.items = [];
>   }
>
>   get size() { return this.items.length; }
>   peek() { return this.items.length === 0 ? null : this.items[0]; }
>
>   push(value) {
>     const items = this.items;
>     items.push(value);
>     let i = items.length - 1;
>     while (i > 0) {
>       const parent = Math.floor((i - 1) / 2);
>       if (!this.higher(items[i], items[parent])) break;
>       [items[i], items[parent]] = [items[parent], items[i]];
>       i = parent;
>     }
>   }
>
>   pop() {
>     const items = this.items;
>     if (items.length === 0) return null;
>     const root = items[0];
>     const last = items.pop();
>     if (items.length > 0) {
>       items[0] = last;
>       let i = 0;
>       while (true) {
>         const left = 2 * i + 1;
>         const right = left + 1;
>         let best = i;
>         if (left < items.length && this.higher(items[left], items[best])) best = left;
>         if (right < items.length && this.higher(items[right], items[best])) best = right;
>         if (best === i) break;
>         [items[i], items[best]] = [items[best], items[i]];
>         i = best;
>       }
>     }
>     return root;
>   }
>
>   toArray() { return this.items.slice(); }
> }
>
> class StableMaxPriorityQueue {
>   constructor() {
>     this.sequence = 0n;
>     this.heap = new BinaryHeap((a, b) =>
>       a.priority > b.priority ||
>       (a.priority === b.priority && a.sequence < b.sequence)
>     );
>   }
>   get size() { return this.heap.size; }
>   peek() { return this.heap.peek(); }
>   push(priority, value) {
>     if (!Number.isFinite(priority)) throw new TypeError('priority must be finite');
>     this.heap.push(Object.freeze({ priority, sequence: this.sequence, value }));
>     this.sequence += 1n;
>   }
>   pop() { return this.heap.pop(); }
> }
>
> const tasks = new StableMaxPriorityQueue();
> tasks.push(5, 'A');
> tasks.push(5, 'B');
> tasks.push(8, 'C');
> console.log(tasks.pop().value); // C
> console.log(tasks.pop().value); // A
> console.log(tasks.pop().value); // B
> console.log(tasks.pop());       // null
> ~~~

上浮或下沉每一步都沿堆的一层前进；每层最多比较两个孩子，因此不会扫描整堆。若输入量一次性已知而且需要取出全部排序结果，直接排序可能更简单；堆的优势出现在不断插入、只需当前极值，或只保留少量 Top K 的时候。

## 只保留 Top K 时，根节点代表淘汰线

一次性读入 n 个带分数的任务，只保留最大的 K 个时，维护一个最多 K 项的最小堆。下方短代码复用前面折叠示例中的 BinaryHeap。根是当前保留集合里最差的一项：分数不高于它的输入直接丢弃，分数更高的输入弹出根，再插入新项。同分时较早项优先保留，根在同分项中是较晚到达的那个。依次读入 A(8)、B(5)、C(5)、D(7)、E(1)，K=3：

| 已读分数 | 保留集合 | 根（当前淘汰线） | 动作 |
|---|---|---|---|
| A、B、C | A(8)、B(5)、C(5) | C(5) | 堆已满 |
| 再读 D | A(8)、D(7)、B(5) | B(5) | D 淘汰同分项里较晚的 C |
| 再读 E | 不变 | B(5) | E(1) 低于根，丢弃 |

令 k' = min(K, n)。K 为正且 n 非零时，扫描需 O(n log(k' + 1)) 时间，最终按排名排序另需 O(k' log(k' + 1))；额外堆空间为 O(k')。这样 K=1 时扫描仍是 O(n)，K>n 时堆最多只有 n 项。K=0 时仍先校验输入的 n 项，之后返回空数组；n=0 时也返回空数组。代码中的 tie-breaker（平局裁决键）保证选择较早的并列分数。

~~~javascript
function topK(values, k) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isSafeInteger(k) || k < 0) throw new RangeError('k must be a non-negative safe integer');
  for (const item of values) {
    if (!item || !Number.isFinite(item.score)) {
      throw new TypeError('values must contain items with finite scores');
    }
  }
  if (k === 0 || values.length === 0) return [];

  const worstFirst = (a, b) =>
    a.score < b.score ||
    (a.score === b.score && a.sequence > b.sequence);
  const heap = new BinaryHeap(worstFirst);

  for (let i = 0; i < values.length; i++) {
    const candidate = { score: values[i].score, sequence: BigInt(i), value: values[i] };
    if (heap.size < k) {
      heap.push(candidate);
    } else if (candidate.score > heap.peek().score) {
      heap.pop();
      heap.push(candidate);
    }
  }

  return heap.toArray()
    .sort((a, b) => {
      if (a.score > b.score) return -1;
      if (a.score < b.score) return 1;
      if (a.sequence < b.sequence) return -1;
      if (a.sequence > b.sequence) return 1;
      return 0;
    })
    .map(item => item.value);
}

const scoredTasks = [
  { id: 'A', score: 8 }, { id: 'B', score: 5 }, { id: 'C', score: 5 },
  { id: 'D', score: 7 }, { id: 'E', score: 1 }
];
console.log(topK(scoredTasks, 3).map(task => task.id)); // ['A', 'D', 'B']
console.log(topK(scoredTasks, 0));                     // []
~~~

若只需处理一条已完整到达的短数组且最终要所有项有序，排序一次是 O(n log n)，代码更直接；若 n 很大而 K 很小，Top K 堆把保留空间降到 O(K)，也允许数据流逐项到达。优先队列可用于任务调度；固定大小堆适合流式候选筛选。二者共享堆操作，但取舍目标不同。

> [!info]- 来源
> - 完全二叉树数组表示、上浮/下沉、插入/删除极值、线性 bottom-up heapify：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §2.4 “Priority Queues”](https://algs4.cs.princeton.edu/24pq/)。本页以 0 起始数组实现同一堆序；操作结果由 Node.js 运行复算。
> - 并列键稳定处理的作者实现样本：[Algorithms, 4th ed., StableMinPQ.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/StableMinPQ.java.html)。本页显式把到达序号作为次级比较键，稳定性因此属于本页 API 合约。
