# 最近最少使用缓存怎样按键查找并更新最近使用顺序？

报表界面最近访问 acct-17 的 report/42 游标页和 report/41 页面。容量已满时，Least Recently Used (LRU) cache（最近最少使用缓存）要淘汰最久未访问条目，因此同时需要按键查找和按新近顺序淘汰。若缓存受保护的报表数据，缓存键须隔离账户/授权范围、过滤器和游标；缓存命中不能代替授权检查。

## 用 Map 插入顺序表示新近程度

ECMAScript Map 保留键的插入顺序。命中时删后重设，把键移到最新端；迭代器按顺序返回键，首项是最旧键。实现支持任意键和值，has 可区分存入 undefined 与键缺失；对象键按对象身份比较，内容相同但新建的数组仍是另一个键；容量为非负整数，容量 0 时不留数据。

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
    this.capacity = capacity;
    this.cache = new Map();
  }
  has(key) { return this.cache.has(key); }
  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }
  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) this.cache.delete(key);
    else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

> [!example] 容量为 2 的淘汰过程
> put(A, 页面42)、put(B, 页面41) 后，A 最旧、B 最新。get(A) 命中后顺序变成 B、A。put(C, 首页) 淘汰 B，留下 A、C。更新已有键也把它移到最新端。
>
> | 操作 | 最旧 → 最新 |
> |---|---|
> | put(A) | A |
> | put(B) | A, B |
> | get(A) | B, A |
> | put(C) | A, C；B 被淘汰 |

ECMAScript 要求 Map 的平均访问复杂度为次线性，但不承诺精确 O(1)。更重要的是，Map 的键查找保证不能推出 `keys().next()` 找到首个仍存活键也为 O(1)：新迭代器可能略过此前删除的内部位置，反复删后重插的工作量还取决于实现如何维护迭代状态。此版顺序正确、代码较短，但不能仅凭 Map 键访问界给每次淘汰一个 O(1) 上界。

## 用双向链表加 Map 显式维护索引与顺序

Map 把键映射到节点，双向链表通过已知节点更新相邻链接、从尾部淘汰。头尾哨兵使插入头部和删除节点无需为真实边界写分支。

~~~javascript
class ListNode {
  constructor(key, value) { this.key = key; this.value = value; this.prev = null; this.next = null; }
}
class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }
  has(key) { return this.nodes.has(key); }
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

已知节点时，链表摘除、移到 head 和从 tail 取最旧项都只改固定数目的链接，因此是确定的 O(1)；完整 get/put 还包含 Map 查找或更新。若所选 Map 实现对键访问提供期望 O(1)，整项操作也可按期望 O(1) 分析；ECMAScript 对 Map 的最低保证只是平均次线性。Map 版适合展示紧凑实现，链表版把淘汰顺序变成显式首尾链接。

> [!example]- 可选：不使用 Map/Record 的数字键练习变体
> 旧练习用 Object.create(null) 建无原型索引，以数字键查节点；命中移至头部，满容量插入淘汰尾节点。get 返回 -1 表示未命中，因此调用契约须约定 -1 不属于有效缓存值（代码本身不拒绝写入 -1）；键和值沿用 number 契约，不限为有限整数；索引把键转成属性名，因此 +0/-0 共用 "0"，NaN 共用 "NaN"，正负无穷分别成为属性名。大于安全整数范围的不同文本 ID 不能先存成 Number 再指望区分。容量须为非负整数。对象属性访问的复杂度是引擎行为，不是 ECMAScript 的精确 O(1) 保证。
>
> ~~~typescript
> class ListNode {
>   prev: ListNode | null = null;
>   next: ListNode | null = null;
>   constructor(readonly key: number, public value: number) {}
> }
> class NumericLRUCache {
>   private readonly index: { [key: string]: ListNode } = Object.create(null);
>   private head: ListNode | null = null;
>   private tail: ListNode | null = null;
>   private size = 0;
>   constructor(private readonly capacity: number) {
>     if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
>   }
>   get(key: number): number {
>     const node = this.index[key];
>     if (!node) return -1;
>     this.moveToHead(node);
>     return node.value;
>   }
>   put(key: number, value: number): void {
>     if (this.capacity === 0) return;
>     const existing = this.index[key];
>     if (existing) {
>       existing.value = value;
>       this.moveToHead(existing);
>       return;
>     }
>     if (this.size >= this.capacity) this.removeTail();
>     const node = new ListNode(key, value);
>     this.index[key] = node;
>     this.addHead(node);
>     this.size++;
>   }
>   private addHead(node: ListNode): void {
>     node.prev = null;
>     node.next = this.head;
>     if (this.head) this.head.prev = node;
>     this.head = node;
>     if (!this.tail) this.tail = node;
>   }
>   private remove(node: ListNode): void {
>     if (node.prev) node.prev.next = node.next;
>     else this.head = node.next;
>     if (node.next) node.next.prev = node.prev;
>     else this.tail = node.prev;
>     node.prev = null;
>     node.next = null;
>   }
>   private moveToHead(node: ListNode): void {
>     if (this.head === node) return;
>     this.remove(node);
>     this.addHead(node);
>   }
>   private removeTail(): void {
>     if (!this.tail) return;
>     const oldest = this.tail;
>     this.remove(oldest);
>     delete this.index[oldest.key];
>     this.size--;
>   }
> }
> ~~~

> [!info]- 来源
> - Map 键值、插入顺序与平均访问复杂度：[ECMAScript 2026 keyed collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)，Map Objects；规范承诺平均次线性访问，不承诺精确 O(1)。
> - 容量 2 状态与链表指针更新按本页代码复算；无 Map 变体以 TypeScript 5.7.2 编译并运行。
