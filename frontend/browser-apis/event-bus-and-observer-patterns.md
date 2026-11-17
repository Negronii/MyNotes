# JavaScript 事件总线在监听器中重入时怎样保持顺序？

案例背景：报表页上，报表 42 每次更新都会发布一条 `report:updated` 事件，通知摘要、旧版界面和恢复模块三个本地模块。监听器在处理事件时可能增删订阅，甚至同步再发布一次同名事件，这时监听器按什么顺序运行就不再直观。本文用一个合成的同步事件总线追踪这种重入（reentrancy，回调尚未返回时又进入同一段分发逻辑），关键是区分两样东西：本次分发开始时复制的监听器快照，以及事件总线此刻保存的监听器集合。

这里的 event bus（事件总线）是应用层的 publish–subscribe（发布订阅）实现，与浏览器 Document Object Model（文档对象模型，DOM）的事件分发无关。示例用 Map（映射）按事件名找到一个 Set（集合）：同一个函数对象对同一事件重复调用 `on` 只占一个位置，Set 按插入顺序迭代。每次 `emit` 都先复制该事件当前的全部监听器，再同步地逐个调用快照中的函数。

## 当前分发使用自己的快照

> [!example]- 完整 EventBus 实现
>
> ~~~javascript
> class EventBus {
>   events = new Map();
>
>   on(type, listener) {
>     let listeners = this.events.get(type);
>     if (!listeners) this.events.set(type, listeners = new Set());
>     listeners.add(listener);
>     return () => this.off(type, listener);
>   }
>
>   once(type, listener) {
>     let fired = false;
>     const wrapper = (...args) => {
>       if (fired) return;
>       fired = true;
>       this.off(type, wrapper); // 在用户代码运行前注销
>       listener(...args);
>     };
>     return this.on(type, wrapper);
>   }
>
>   off(type, listener) {
>     const listeners = this.events.get(type);
>     if (!listeners) return;
>     listeners.delete(listener);
>     if (listeners.size === 0) this.events.delete(type);
>   }
>
>   emit(type, ...args) {
>     for (const listener of [...(this.events.get(type) ?? [])]) {
>       listener(...args);
>     }
>   }
> }
> ~~~

`once(type, listener)` 每次注册都会创建新的包装函数和独立的 `fired` 标记；所以对同一事件调用两次 `once`，Set 中会有两个包装器，每个包装器最多调用一次原回调。

一次 `emit` 开始时，表达式 `[...(this.events.get(type) ?? [])]` 立即复制出数组快照，此后本次循环只沿这个数组走：

- 监听器从 Set 中删除后，只要它已在本次快照里且还没轮到，本次分发仍会调用它。
- 新加的监听器不会进入已经建立的快照，但下一次 `emit`（包括同步嵌套的 `emit`）会从更新后的 Set 复制新快照。
- 删除的若是最后一个监听器，`off` 还会从 Map 中删掉该事件名；已有的数组快照不受影响。

所以“注销成功”只表示以后的快照不再包含该监听器，并不会改写已经建立的快照。

## 逐层跟踪 v10、v11 与 v12

下面把快照规则用到一次三层嵌套的分发上（完整代码见本节末尾）。初始注册顺序是 `summary`（摘要）、用 `once` 注册的一次性监听器（下称 `once`）、`legacy`（旧版界面）。处理 `v10` 时，`summary` 移除 `legacy`、加入 `recovery`（恢复模块），然后同步发布 `v11`。处理 `v11` 时，`once` 的包装器先注销自己，再运行用户回调；回调又同步发布 `v12`。

> [!example] 三层同步调用怎样返回
> `v10`、`v11`、`v12` 只是区分三次本地发布的合成标签，取自事件载荷中的 `version`，不是服务端的事件序列；本例只观察同步调用顺序。事件总线不会按业务版本排序或丢弃旧事件，真实消费者若要拒绝过时状态，需要自己比较版本。
>
> 每层快照和回调变化如下：
>
> | 当前分发 | 本层开始时的快照 | 本层发生的变化与返回顺序 |
> | --- | --- | --- |
> | `v10` | `[summary, once, legacy]` | `summary v10` 删除实时 Set 中的 `legacy`，加入 `recovery`，再进入 `v11`。外层旧快照不变。 |
> | `v11` | `[summary, once, recovery]` | `summary v11` 后执行 `once`。包装器先设 `fired = true` 并注销自己，再调用用户回调，进入 `v12`。 |
> | `v12` | `[summary, recovery]` | 实时 Set 已不含 `once`，依次记录 `summary v12`、`recovery v12`，然后返回 `v11`。 |
> | 返回 `v11`、`v10` | 各层仍继续原快照 | `v11` 接着记录 `recovery v11`。回到 `v10` 后，旧快照还会碰到 `once` 包装器，但 `fired` 使其直接返回；随后旧快照中的 `legacy` 仍记录 `legacy v10`。 |
>
> 日志的先后顺序如下；缩进表示嵌套调用深度，方便与上表对照：
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
>
> 这里两道保护各管一处：先注销包装器，使之后建立的 `v12` 快照不再包含它；`fired` 标记则拦住仍持有该包装器的 `v10` 旧快照，不让它再次进入用户函数。若用户回调抛错，本实现仍把这次 `once` 视为已消费，因为设置 `fired` 和注销都发生在调用用户代码之前。

> [!example]- 完整重入输入代码
>
> ~~~javascript
> const bus = new EventBus();
> const trace = [];
> let onceReentered = false;
> const legacy = e => trace.push(`legacy v${e.version}`);
> const recovery = e => trace.push(`recovery v${e.version}`);
>
> bus.on("report:updated", e => {
>   trace.push(`summary v${e.version}`);
>   if (e.version === 10) {
>     bus.off("report:updated", legacy);
>     bus.on("report:updated", recovery);
>     bus.emit("report:updated", { reportId: 42, version: 11 });
>   }
> });
> bus.once("report:updated", e => {
>   trace.push(`once v${e.version}`);
>   if (!onceReentered) {
>     onceReentered = true;
>     bus.emit("report:updated", { reportId: 42, version: 12 });
>   }
> });
> bus.on("report:updated", legacy);
> bus.emit("report:updated", { reportId: 42, version: 10 });
> console.log(trace.join(" → "));
> ~~~

## 选择事件总线还是观察者模式

上面的示例是事件总线；另一种常见做法是 Observer pattern（观察者模式）。观察者模式通常由拥有状态的对象自己保存观察者列表并直接通知它们；事件总线则让发布者和订阅者只通过事件名和中间的总线通信。前者顺着对象就能找到订阅关系；后者减少了模块之间的直接引用，代价是更依赖清楚的事件名、载荷约定和调试追踪工具。两者都只是同一浏览上下文（例如一个标签页）内的内存实现；跨标签页传消息要用浏览上下文间的通信机制。

无论选哪种，本文的实现都有以下行为边界，换成其他库时要逐项核对：

- 分发是同步的；嵌套 `emit` 会先完成，再回到外层监听器。
- 监听器抛出的同步异常会沿调用栈向外传播，本次循环中排在后面的监听器不再执行。
- 返回 Promise 的监听器不会被等待；Promise 的拒绝也不会由这个 `emit` 自动收集或处理。
- 移除或新增订阅不会影响已经建立的旧快照。如果生产实现改为直接遍历实时集合、使用异步队列或隔离监听器异常，调用顺序和错误处理约定都会不同。

本页依赖的插入顺序由 ECMAScript 对 Set 的定义保证；快照的复制时机、同步重入和 `once` 的注销顺序则是这份实现自己的选择，不是所有事件总线的通用保证。DOM 的事件传播、默认动作和取消规则由浏览器平台另行定义，不能从这个类推导。

**延伸阅读：** [修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](./dom-collections.md) 跟踪状态通知后的节点增删；[同一报表在多个标签页中怎样交换变化？](./browser-context-communication.md) 介绍跨标签页消息；[DOM 事件传播如何经过节点？](./dom-manipulation-and-events.md) 介绍浏览器自身的事件阶段和取消规则。

> [!info]- 来源
> - Set 至多保存每个不同值一次；`add` 不会重复加入相同值，`values`/`forEach` 按值的插入顺序遍历，这支持示例中快照的初始顺序：[ECMAScript 2026 §24.2、§24.2.4.1、§24.2.4.7、§24.2.4.17](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-objects)，核验于 2026-11-12。复制快照、`once` 包装器及异常传播是本文代码的可观察结果，不是该规范规定的事件总线语义。
> - 浏览器 `EventTarget` 的事件分发、传播路径、监听器移除和取消机制：[WHATWG DOM Living Standard §2.9–2.11 Events](https://dom.spec.whatwg.org/#events)，核验于 2026-11-12。它是平台事件系统，与本页自建 `EventBus` 分开。
