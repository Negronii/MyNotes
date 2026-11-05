# How can an LRU cache work without Map or Record? / 不使用 Map 或 Record 时如何实现 LRU 缓存？

A doubly linked list keeps entries in recency order while a null-prototype object indexes numeric keys to nodes. A hit moves its node to the head; insertion at capacity removes the tail. This is a constrained interview variant, not the default production design. / 双向链表维护最近使用顺序，无原型对象按数字键索引节点；命中时将节点移到头部，满容量插入时移除尾节点。这是受限的面试变体，不是默认生产方案。

The exercise uses -1 for misses, so cached values cannot use -1; capacity must be a non-negative integer. Its expected fast property lookup is an engine behavior, not a language-level O(1) guarantee.

~~~typescript
class ListNode {
  prev: ListNode | null = null;
  next: ListNode | null = null;
  constructor(readonly key: number, public value: number) {}
}

class LRUCache {
  private readonly index: { [key: string]: ListNode } = Object.create(null);
  private head: ListNode | null = null;
  private tail: ListNode | null = null;
  private size = 0;

  constructor(private readonly capacity: number) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
  }

  get(key: number): number {
    const node = this.index[key];
    if (!node) return -1;
    this.moveToHead(node);
    return node.value;
  }

  put(key: number, value: number): void {
    if (this.capacity === 0) return;
    const existing = this.index[key];
    if (existing) {
      existing.value = value;
      this.moveToHead(existing);
      return;
    }
    if (this.size >= this.capacity) this.removeTail();
    const node = new ListNode(key, value);
    this.index[key] = node;
    this.addHead(node);
    this.size++;
  }

  private addHead(node: ListNode): void {
    node.prev = null;
    node.next = this.head;
    if (this.head) this.head.prev = node;
    this.head = node;
    if (!this.tail) this.tail = node;
  }

  private remove(node: ListNode): void {
    if (node.prev) node.prev.next = node.next;
    else this.head = node.next;
    if (node.next) node.next.prev = node.prev;
    else this.tail = node.prev;
    node.prev = null;
    node.next = null;
  }

  private moveToHead(node: ListNode): void {
    if (this.head === node) return;
    this.remove(node);
    this.addHead(node);
  }

  private removeTail(): void {
    if (!this.tail) return;
    const oldest = this.tail;
    this.remove(oldest);
    delete this.index[oldest.key];
    this.size--;
  }
}
~~~

The maintained [Practical Data Structure Implementations](../../../engineering-foundations/algorithms/practical-data-structure-implementations.md) note explains Map and linked-list-plus-Map versions, including their broader key/value contract.
