# 队列和栈怎样表示待处理工作？

处理报表 42 的事件流时，通知消费者应先处理最早到达的事件；解析嵌套表达式时，应先返回最近进入的未完成分支。前者是 first-in, first-out (FIFO，先进先出) 队列，后者是 last-in, first-out (LIFO，后进先出) 栈。选好顺序后，还要让空状态和可存储值之间没有歧义。

## 队列怎样同时维护头、尾和空状态？

链表队列维护 head、tail、length：空时头尾均为 null 且长度为 0；非空时 head 指向最早项，tail 指向最新项且 tail.next 为 null。删除最后一项要同时清空头尾。空读抛错，因此 null 和 undefined 都可以是队列值。

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }
  get isEmpty() { return this.length === 0; }
  enqueue(value) {
    const node = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }
  dequeue() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return value;
  }
  peek() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    return this.head.value;
  }
}
~~~

enqueue、dequeue、peek 都是 O(1)，但每个节点需要分配并维护链接。容量有上限时可用环形缓冲区；一次性的 BFS 扫描可用数组与递增 head 下标。长期 FIFO 若只增加 head，会保留尚未清理的已消费引用并让数组持续增长；可清空已消费槽并定期压缩，或改用环形缓冲区。Array.shift 的可观察语义不承诺某引擎的搬移成本，但常见数组实现会调整剩余索引，连续出队可能累积平方级工作。

用 head 而不是槽值表示空状态时，队列可以安全保存 null 和 undefined。下面两项出队后 head 递增；即使第 2 项本身是 undefined，head 仍小于长度，所以它是已存值而非“空”的信号。实际长期队列还应把消费槽设为 undefined 释放引用，并配合压缩或环形缓冲区控制数组增长。

| 操作 | 数组状态 | head | 结果 / 空状态 |
|---|---|---:|---|
| 初始 | [null, undefined] | 0 | 还有 2 项 |
| dequeue | [undefined, undefined] | 1 | 取出 null；还有 1 项 |
| dequeue | [undefined, undefined] | 2 | 取出已存的 undefined；此时 head 等于长度，队列为空 |

旧数值队列以 null 表示空：仅因为值域是 number，null 不会与有效值混淆；若要允许 null/undefined，须改为显式 isEmpty、带状态的返回值或异常。其受限实现保留如下。

> [!example]- 可选：数值专用 TypeScript 空值哨兵
> ~~~typescript
> interface QueueNode { val: number; next: QueueNode | null; }
> class NullableNumberQueue {
>   private head: QueueNode | null = null;
>   private tail: QueueNode | null = null;
>   private length = 0;
>   offer(val: number): void {
>     const node: QueueNode = { val, next: null };
>     if (this.tail) this.tail.next = node;
>     else this.head = node;
>     this.tail = node;
>     this.length++;
>   }
>   poll(): number | null {
>     if (!this.head) return null;
>     const value = this.head.val;
>     this.head = this.head.next;
>     if (!this.head) this.tail = null;
>     this.length--;
>     return value;
>   }
>   get size(): number { return this.length; }
> }
> ~~~

## 栈怎样保留最近未完成的工作？

数组末尾 push/pop 表达栈的入栈和出栈；显式空检查可避免把已存的 undefined 当作空栈。

~~~javascript
class Stack {
  constructor() { this.items = []; }
  get isEmpty() { return this.items.length === 0; }
  push(value) { this.items.push(value); }
  pop() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items.pop();
  }
  peek() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items[this.items.length - 1];
  }
}
~~~

push/pop 是末端操作；动态数组扩容时可能分配并复制，因此单次耗时会变化，通常按摊还常数时间分析。未知输入深度的递归还受运行时栈大小限制，可改用显式栈。

> [!info]- 来源
> - 数组末端和首端操作的规范行为：[ECMAScript 2026 indexed collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，Array.prototype.shift/push/pop。标准描述可观察效果，不规定某引擎的数组搬移算法。
