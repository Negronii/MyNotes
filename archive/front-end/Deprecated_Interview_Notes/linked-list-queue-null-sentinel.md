# How does this linked-list queue represent an empty state? / 这个链表队列如何表示空状态？

This TypeScript queue is restricted to numbers, so it can return null for an empty poll without confusing that sentinel with a stored number. It keeps both head and tail references, making enqueue and dequeue O(1); removing the final node clears both references. / 此 TypeScript 队列只存数字，因此空队列可返回 null，不会与数字混淆。队列同时维护头尾引用，使入队和出队均为 O(1)；移除最后一个节点时会清空两个引用。

~~~typescript
interface Node {
  val: number;
  next: Node | null;
}

class Queue {
  private head: Node | null = null;
  private tail: Node | null = null;
  private length = 0;

  offer(val: number): void {
    const node: Node = { val, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }

  poll(): number | null {
    if (this.head === null) return null;
    const value = this.head.val;
    this.head = this.head.next;
    if (this.head === null) this.tail = null;
    this.length--;
    return value;
  }

  get size(): number { return this.length; }
}
~~~

If the queue must store arbitrary values including null or undefined, use an explicit isEmpty/exception contract instead. The maintained [queue implementation](../../../engineering-foundations/algorithms/practical-data-structure-implementations.md) throws on an empty read so every value remains representable.
