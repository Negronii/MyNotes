# 两个后进先出的栈，怎样实现先进先出的队列？

**案例背景：** 任务 1、2 先后到达，必须依次出队；底层只有 stack（栈）的 push/pop。把新任务放入输入栈，只有输出栈空时才整批倒过去，倒序后最旧任务恰好位于输出栈顶。此页保留原 TypeScript 实现；更多表示与边界见[队列与栈怎样用数组或链表实现？](../../../../../engineering-foundations/algorithms/queue-and-stack-representations.md)。

## 为什么不能每次出队都倒栈？

下面数组右端是栈顶。

| 操作 | 输入栈 | 输出栈 | 返回 |
|---|---|---|---|
| 入队 1、2 | `[1,2]` | `[]` | — |
| 第一次出队，先整批倒栈 | `[]` | `[2]` | 1 |
| 入队 3 | `[3]` | `[2]` | — |
| 第二次出队，不倒栈 | `[3]` | `[]` | 2 |
| 第三次出队，再倒栈 | `[]` | `[]` | 3 |

输出栈仍有 2 时就把 3 放到它上面，会让 3 插队。因此“不空就先消耗输出栈”是顺序成立的关键，而不只是优化。

## 返回值怎样区分空队列和 undefined 元素？

直接返回 T 或 undefined 会把两个情况混在一起。下面成功时返回 `{value:T}`，空队列返回外层 undefined；调用方先检查包装是否存在，就能表达存入 undefined 的合法元素。原实现如下：

```ts
type PopResult<T> = { value: T } | undefined;

class Stack<T> {
  private container: T[] = [];

  push(item: T): void {
    this.container.push(item);
  }

  pop(): PopResult<T> {
    if (this.container.length === 0) return undefined;
    return { value: this.container.pop() as T };
  }

  isEmpty(): boolean {
    return this.container.length === 0;
  }
}

class QueueWithTwoStacks<T> {
  private stackIn = new Stack<T>();
  private stackOut = new Stack<T>();

  enqueue(item: T): void {
    this.stackIn.push(item);
  }

  dequeue(): PopResult<T> {
    if (this.stackOut.isEmpty()) {
      while (!this.stackIn.isEmpty()) {
        const item = this.stackIn.pop();
        if (item !== undefined) this.stackOut.push(item.value);
      }
    }
    return this.stackOut.pop();
  }

  isEmpty(): boolean {
    return this.stackIn.isEmpty() && this.stackOut.isEmpty();
  }
}

const queue = new QueueWithTwoStacks<number>();
queue.enqueue(1);
queue.enqueue(2);
console.log(queue.dequeue()?.value); // 1
console.log(queue.dequeue()?.value); // 2
console.log(queue.isEmpty()); // true
console.log(queue.dequeue()); // undefined: empty

const undefinedQueue = new QueueWithTwoStacks<undefined>();
undefinedQueue.enqueue(undefined);
console.log(undefinedQueue.dequeue()); // { value: undefined }
console.log(undefinedQueue.dequeue()); // undefined: empty
```

## 一次搬很多元素，为何仍能均摊常数成本？

假设数组栈 push/pop 是 amortized O(1)（均摊常数时间）。一个元素最多入输入栈一次、转移一次、出输出栈一次；m 次入队和出队的总栈操作数因此为 O(m)。单次出队仍可能搬 n 个元素而花 O(n)，这不是实时延迟保证；整个序列的均摊出队成本才是 O(1)。同时保存 n 个元素占 O(n) 空间。

> [!info]- 来源
> - 实现沿用此页原 TypeScript 解法；均摊结论由每个元素最多转移一次的操作计数推出。
> - 数组栈方法的可观察行为：[ECMAScript 2026 Array push/pop](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，不把具体引擎的复杂度保证归给语言规范。
