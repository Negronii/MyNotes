# Queue with Two Stacks / 用两个栈实现队列

**Key terms / 关键词:** A stack is LIFO (last in, first out) / 栈是后进先出; a queue is FIFO (first in, first out) / 队列是先进先出.

## Core idea / 核心思路

Use one stack for incoming items and one for outgoing items. When the outgoing stack is empty, move all incoming items to it; reversing their order makes the oldest item the next to leave. The tagged return distinguishes an empty queue from a queued `undefined`. / 一个栈接收新元素，另一个栈提供出队元素。出队栈为空时，把入队栈中的元素全部移入；顺序反转后，最早进入的元素会最先离开。带标签的返回值可以区分空队列与队列中实际存放的 `undefined`。

See [practical data-structure implementations / 实用数据结构实现](../../../../../engineering-foundations/algorithms/practical-data-structure-implementations.md) for related stack and queue tradeoffs.

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

**Complexity / 复杂度:** Assuming array-backed stack `push` and `pop` are amortized `O(1)`, `enqueue` and `isEmpty` are `O(1)`. A single `dequeue` can take `O(n)` when it transfers `n` items, but each item moves between stacks at most once, so dequeue is `O(1)` amortized across a sequence of operations. Space is `O(n)`. / 假设基于数组的栈操作 `push` 和 `pop` 均摊为 `O(1)`，则 `enqueue` 和 `isEmpty` 为 `O(1)`。一次 `dequeue` 搬运 `n` 个元素时最坏为 `O(n)`；但每个元素最多在两个栈之间移动一次，因此一系列操作中的出队均摊为 `O(1)`。空间为 `O(n)`。
