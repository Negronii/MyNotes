# 同步事件总线在分发途中增删监听器会怎样？

沿用主线一的报表页：报表 42 每次更新，页面都发布一条 `report:updated` 事件，通知摘要、旧版界面和恢复模块三个本地模块。监听器处理事件时可能增删订阅，甚至同步再发布一次同名事件，这时谁先谁后就不再直观。本章用一个自建的同步事件总线追踪这种 reentrancy（重入：回调还没返回，又进入了同一段分发逻辑），答案取决于区分两样东西：本次分发开始时复制的监听器快照，和总线此刻保存的监听器集合。

这里的 event bus（事件总线）是应用层的 publish–subscribe（发布订阅）实现，与浏览器 DOM 的事件分发无关；DOM 事件的传播与取消见[一次点击怎样传播到处理器，处理器该怎样注册和清理？](../browser/dom-events.md)。

## 一个用 Map 和 Set 实现的总线

总线用 Map（映射）按事件名找到一个 Set（集合）。同一个函数对同一事件重复 `on` 只占一个位置，Set 按插入顺序迭代。每次 `emit` 先把该事件当前的全部监听器复制成数组，再同步地逐个调用。Map、Set 的语义见[数组、Map、Set 和普通对象怎样选，空位和去重有哪些坑？](./arrays-maps-and-sets.md)。

~~~javascript
class EventBus {
  events = new Map();

  on(type, listener) {
    let listeners = this.events.get(type);
    if (!listeners) this.events.set(type, listeners = new Set());
    listeners.add(listener);
    return () => this.off(type, listener);
  }

  once(type, listener) {
    let fired = false;
    const wrapper = (...args) => {
      if (fired) return;
      fired = true;
      this.off(type, wrapper); // 在用户代码运行前注销
      listener(...args);
    };
    return this.on(type, wrapper);
  }

  off(type, listener) {
    const listeners = this.events.get(type);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(type);
  }

  emit(type, ...args) {
    for (const listener of [...(this.events.get(type) ?? [])]) {
      listener(...args);
    }
  }
}
~~~

`once` 每次注册都新建一个包装函数和独立的 `fired` 标记，所以对同一事件调用两次 `once`，Set 里有两个包装器，各自最多调用一次原回调。

## 当前分发只走自己的快照

`emit` 开始时，`[...(this.events.get(type) ?? [])]` 立即复制出数组快照，本次循环只沿这个数组走：

- 监听器从 Set 删除后，只要它已在本次快照里且还没轮到，本次分发**仍会调用它**。
- 新加的监听器不进入已建立的快照；下一次 `emit`（包括同步嵌套的 `emit`）从更新后的 Set 复制新快照。
- 删的若是最后一个监听器，`off` 还会从 Map 删掉这个事件名；已有的数组快照不受影响。

所以“注销成功”只表示以后的快照不再包含这个监听器，不会改写已经建立的快照。

## 跟踪一次三层嵌套分发

初始注册顺序是 `summary`（摘要）、用 `once` 注册的一次性监听器（下称 `once`）、`legacy`（旧版界面）。处理 `v10` 时，`summary` 移除 `legacy`、加入 `recovery`（恢复模块），然后同步发布 `v11`。处理 `v11` 时，`once` 的包装器先注销自己，再运行用户回调，回调又同步发布 `v12`。

`v10`、`v11`、`v12` 只是区分三次本地发布的合成标签，取自载荷里的 `version`，不是服务端的事件序列。总线不会按版本排序或丢弃旧事件；消费者要拒绝过时状态，得自己比较版本。

~~~javascript
const bus = new EventBus();
const trace = [];
let onceReentered = false;
const legacy = e => trace.push(`legacy v${e.version}`);
const recovery = e => trace.push(`recovery v${e.version}`);

bus.on("report:updated", e => {
  trace.push(`summary v${e.version}`);
  if (e.version === 10) {
    bus.off("report:updated", legacy);
    bus.on("report:updated", recovery);
    bus.emit("report:updated", { reportId: 42, version: 11 });
  }
});
bus.once("report:updated", e => {
  trace.push(`once v${e.version}`);
  if (!onceReentered) {
    onceReentered = true;
    bus.emit("report:updated", { reportId: 42, version: 12 });
  }
});
bus.on("report:updated", legacy);
bus.emit("report:updated", { reportId: 42, version: 10 });
trace.join(" → ");
// "summary v10 → summary v11 → once v11 → summary v12 → recovery v12 → recovery v11 → legacy v10"
~~~

> [!example] 每层快照怎样变化、怎样返回
>
> | 当前分发 | 本层开始时的快照 | 本层发生的事 |
> | --- | --- | --- |
> | `v10` | `[summary, once, legacy]` | `summary v10` 从 Set 删掉 `legacy`、加入 `recovery`，然后进入 `v11`。`v10` 的快照不变。 |
> | `v11` | `[summary, once, recovery]` | `summary v11` 之后轮到 `once`：包装器先设 `fired = true` 并注销自己，再调用用户回调，进入 `v12`。 |
> | `v12` | `[summary, recovery]` | Set 里已没有 `once`。依次记录 `summary v12`、`recovery v12`，返回 `v11`。 |
> | 回到 `v11`、`v10` | 各层继续原快照 | `v11` 接着记录 `recovery v11`。回到 `v10`，旧快照还会碰到 `once` 包装器，`fired` 让它直接返回；旧快照里的 `legacy` 仍记录 `legacy v10`。 |
>
> 按嵌套深度缩进的日志：
>
> ```text
> summary v10
>   summary v11
>   once v11
>     summary v12
>     recovery v12
>   recovery v11
> legacy v10
> ```

注意 `legacy` 在 `v10` 里就被删了，却仍记录了 `legacy v10`：删除发生时它已在 `v10` 的快照里。`recovery` 在 `v10` 中途才加入，所以不在 `v10` 里出现，却出现在之后的每一层。

`once` 靠两道保护才真正只运行一次，各管一处：

- **先注销包装器**，让之后建立的快照（`v12`）不再包含它；
- **`fired` 标记**拦住仍持有包装器的旧快照（`v10`），不让它再次进入用户函数。

设 `fired` 和注销都发生在调用用户代码之前，所以用户回调抛错时，这次 `once` 仍算已消费——和[包装函数一章的 `once`](./wrapping-functions.md#once：最多执行一次，失败也算一次) 是同一种“最多尝试一次”的策略。

## 这份实现的行为边界

快照的复制时机、同步重入和 `once` 的注销顺序，都是这份实现自己的选择；只有 Set 的插入顺序由 ECMAScript 保证。换成别的库时，逐项核对：

- **分发是同步的。** 嵌套 `emit` 先完成，再回到外层监听器。
- **同步异常向外传播。** 某个监听器抛错，异常沿调用栈传给 `emit` 的调用者，本次快照里排在后面的监听器不再执行。
- **不等待 Promise。** 返回 Promise 的监听器不会被等待，它的拒绝也不由 `emit` 收集或处理。
- **增删不影响已建立的快照。** 若实现改为直接遍历实时集合、改用异步队列或隔离监听器异常，调用顺序和错误约定都会不同。

## 事件总线还是观察者模式

另一种常见做法是 Observer pattern（观察者模式）：拥有状态的对象自己保存观察者列表，直接通知它们。事件总线则让发布者和订阅者只通过事件名和中间的总线通信。

| | 观察者模式 | 事件总线 |
| --- | --- | --- |
| 订阅关系在哪 | 在拥有状态的对象上，顺着对象就能找到 | 在总线上，按事件名查 |
| 模块间引用 | 订阅者要拿到被观察对象 | 只共享总线和事件名 |
| 主要代价 | 耦合到具体对象 | 依赖清楚的事件名、载荷约定和调试追踪 |

两者都只是同一浏览上下文（例如一个标签页）内的内存实现，快照与重入的问题同样存在。

## 跨出一个标签页之后

本章的结论：同步总线的每次分发只遍历开始时复制的快照，增删订阅只影响之后的分发；嵌套 `emit` 像普通函数调用一样先完成再返回；`once` 需要“先注销 + 标记”两道保护。这些顺序是实现选择，不是通用保证。

当通知要跨标签页或窗口传递时，内存里的总线就不够了：消息要经过浏览器提供的通道，而且收到通知后还要回到权威来源核实数据。见[浏览器能把状态存在哪里，标签页和窗口之间怎样互相通知？](../ui-state/browser-storage-and-cross-context-messaging.md)。

> [!info]- 来源
> - Set 对每个值至多保存一次、`add` 不重复加入、按插入顺序遍历，支持快照的初始顺序（“一个用 Map 和 Set 实现的总线”“这份实现的行为边界”）：[ECMAScript 2026 Set Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-objects)（§24.2、§24.2.4.1、§24.2.4.7、§24.2.4.17），核验于 2026-11-12。快照复制、`once` 包装器与异常传播是本章代码的可观察结果，不是规范规定的事件总线语义；三层嵌套日志在 Node.js 26.13.1 上复跑核对。
> - 浏览器 `EventTarget` 的分发、传播路径、监听器移除与取消属平台事件系统，与本章自建总线分开：[WHATWG DOM Living Standard §2.9–2.11 Events](https://dom.spec.whatwg.org/#events)，核验于 2026-11-12。
