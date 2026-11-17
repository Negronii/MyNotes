# 两个后进先出的栈，怎样实现先进先出的队列？

**案例背景：** 任务 1、2 先后到达，必须按到达顺序出队；手头只有栈，支持入栈 `push`、出栈 `pop`，并可用 `isEmpty()` 判空。做法是用两个栈：新任务压入输入栈；出队时，只有输出栈为空，才把输入栈的元素全部依次弹出、压入输出栈（下称“倒栈”）。倒一次顺序就反过来，最早到达的任务正好位于输出栈顶。此页保留原 TypeScript 实现；更多表示与边界见[队列与栈怎样用数组或链表实现？](../../../../../engineering-foundations/algorithms/queue-and-stack-representations.md)。

## 为什么不能每次出队都倒栈？

下面数组右端是栈顶；每行记录相应步骤完成后的状态。

| 操作 | 输入栈 | 输出栈 | 返回 |
|---|---|---|---|
| 入队 1、2 | `[1,2]` | `[]` | — |
| 第一次出队：先整批倒栈 | `[]` | `[2,1]` | — |
| 第一次出队：弹出输出栈顶 | `[]` | `[2]` | 1 |
| 入队 3 | `[3]` | `[2]` | — |
| 第二次出队，不倒栈 | `[3]` | `[]` | 2 |
| 第三次出队，再倒栈 | `[]` | `[]` | 3 |

第二次出队时，若不管输出栈里还有 2 就倒栈，3 会压在 2 上面，先于 2 出队。所以“输出栈不空就先用完它”是保证先进先出的必要条件，而不只是性能优化。

## 返回值怎样区分空队列和 undefined 元素？

如果出队直接返回 `T | undefined`，那么“队列为空”和“取到的元素本身就是 `undefined`”无法区分。下面的实现成功时返回包装对象 `{ value: T }`，队列为空时返回 `undefined`；调用方先检查包装是否存在，就能正确处理存入 `undefined` 的元素。原实现如下：

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

`Stack.pop` 先检查 `container.length`，再调用 `Array.pop()`。TypeScript 将该调用的静态返回类型推断为 `T | undefined`；在已确认数组非空的前提下，`as T` 只是让编译器把取出的值按 `T` 看待，不会在运行时检查，也不会创建包装对象。随后 `{ value: ... }` 才创建包装。返回类型 `{ value: T } | undefined` 的外层 `undefined` 表示没有元素，`{ value: undefined }` 则表示取到了值为 `undefined` 的合法元素。调用者应先检查外层包装；若 `T` 包含 `undefined`，直接写 `dequeue()?.value` 又会把空队列与取到 `undefined` 合并。搬运循环里的 `item !== undefined` 也检查外层包装，不会过滤 `item.value`。

## 一次搬很多元素，为何仍能均摊常数成本？

从空队列开始，任意执行共 `m` 次入队或出队操作。每个入队的元素先压入输入栈，之后至多从输入栈弹出一次并压入输出栈，最后至多从输出栈弹出一次，所以这段完整操作序列共做 `O(m)` 次栈操作。若底层数组栈的 `push` / `pop` 均摊为 `O(1)`，这段序列中每次队列操作的均摊时间为 `O(1)`。某次出队若触发 `n` 个元素的搬运，仍需 `O(n)` 次栈操作；当前保存 `n` 个元素占 `O(n)` 空间。

> [!info]- 来源
> - 实现沿用此页原 TypeScript 解法；均摊结论由每个元素最多转移一次的操作计数推出。
> - 数组入栈和出栈行为：[ECMAScript 2026 §23.1.3.23 `Array.prototype.push`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.push) 追加到数组末尾，[§23.1.3.22 `Array.prototype.pop`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.pop) 移除并返回末项。该快照日期为 2026-03-31，核对 2026-11-12；规范描述可观察行为，不提供实现复杂度保证。
