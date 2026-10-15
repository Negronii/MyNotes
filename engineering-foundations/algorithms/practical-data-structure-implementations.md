# Practical Data Structure Implementations / 常用数据结构实现

These examples make the empty and capacity cases explicit. Built-in collections are usually the simplest production choice; implement the underlying links when the data structure itself is what you need to understand.

选用内建集合还是手写结构取决于需求；实现需要明确容量、空状态与错误行为，并用存在性检查保留 `undefined` 等有效数据。

## LRU Cache

**最近最少使用缓存 / Least Recently Used cache** evicts the least recently accessed entry when full.

### Using `Map`

`Map` preserves insertion order. Deleting and reinserting a hit moves it to the newest position. This API supports arbitrary keys and values; use `has` to distinguish a stored `undefined` from a missing key. A zero-capacity cache remains empty.

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.cache = new Map();
  }

  has(key) {
    return this.cache.has(key);
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

Map operations are commonly treated as expected constant-time in application analysis, but the ECMAScript specification requires average access to be sublinear rather than promising a precise O(1) bound. This version is concise and avoids maintaining a second ordering structure.

### Doubly linked list plus map

A linked list makes moving an existing entry to the front and evicting the tail a pointer update. The map locates each node. Both structures are needed to keep the operations efficient; using an ordinary object for arbitrary cache keys can collide with inherited property names.

~~~javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  has(key) {
    return this.nodes.has(key);
  }

  get(key) {
    const node = this.nodes.get(key);
    if (!node) return undefined;
    this._remove(node);
    this._addToFront(node);
    return node.value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    const existing = this.nodes.get(key);
    if (existing) {
      existing.value = value;
      this._remove(existing);
      this._addToFront(existing);
      return;
    }

    if (this.nodes.size === this.capacity) {
      const oldest = this.tail.prev;
      this._remove(oldest);
      this.nodes.delete(oldest.key);
    }
    const node = new ListNode(key, value);
    this.nodes.set(key, node);
    this._addToFront(node);
  }

  _addToFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
~~~

With a map that provides expected constant-time lookup, the linked-list version has expected O(1) get and put operations. Use the simpler map-based version when the linked-list mechanics are not part of the requirement.

---

## Queue (FIFO)

**队列 / Queue** processes values in first-in, first-out order. This linked-list version throws on an empty read so every value, including `null` and `undefined`, remains distinguishable from the empty state.

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  get isEmpty() {
    return this.length === 0;
  }

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

Enqueue, dequeue, and peek take O(1) time. Array `shift` removes the first element but may move the remaining indexed elements, so a linked queue or a head index is preferable for a queue that grows large. Breadth-first traversal with a head index appears in [Core Data Structures](./core-data-structures.md).

---

## Stack (LIFO)

**栈 / Stack** processes values in last-in, first-out order. An array provides a compact stack; this version also throws on empty `pop` or `peek` so stored `undefined` is not confused with an empty stack.

~~~javascript
class Stack {
  constructor() {
    this.items = [];
  }

  get isEmpty() {
    return this.items.length === 0;
  }

  push(value) {
    this.items.push(value);
  }

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

Array `push` and `pop` are the natural stack operations. Their exact growth costs are runtime implementation details; a dynamic array may occasionally resize.

---

## Linked structure in React Fiber

React represents its work tree with Fiber nodes linked through fields such as `child`, `sibling`, and `return`. The nodes still form a tree; sibling pointers encode the ordered children. This structure lets the reconciler keep work units and progress between scheduling steps.

**Concurrent rendering is conditional.** React can pause or restart render work for updates using concurrent features such as transitions. An update rendered without such features can remain synchronous. React applies DOM mutations during commit after rendering work is ready, so do not describe every render or commit as freely interruptible. Fiber is an implementation detail; use React's public APIs rather than depending on its internal node layout.

**See also:** [Algorithms and Complexity](./algorithms-and-complexity.md) for complexity patterns, [Core Data Structures](./core-data-structures.md) for traversals, and [Virtual DOM and Framework Selection](../../frontend/frameworks/virtual-dom-and-framework-selection.md) for reconciliation context.

Sources: [ECMAScript 2020 Map objects](https://tc39.es/ecma262/2020/#sec-map-objects), [React 18: What is Concurrent React?](https://react.dev/blog/2022/03/29/react-v18), and the [React reconciler Fiber types](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js).
