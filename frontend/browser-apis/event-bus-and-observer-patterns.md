# JavaScript 事件总线在监听器中重入时怎样保持顺序？

报表 42 的进度事件会通知摘要、旧界面和恢复模块。下面用一个合成的同步事件总线示例：监听器在处理事件时可以增删订阅并再次发布同名事件。要读懂最终顺序，先区分“当前分发开始时复制的快照”与“事件总线现在保存的监听器集合”。

这里的 event bus（事件总线）是应用层 publish–subscribe（发布订阅）实现，不是浏览器的文档对象模型（DOM）事件分发。示例用 Map（映射）按事件名索引一个 Set（集合）；对同一事件调用 `on` 重复注册同一个函数对象只占一个成员，Set 按插入顺序迭代。每次 emit 都先复制该事件当前的成员，再同步逐个调用快照中的函数。

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

`once(type, listener)` 每次注册都会创建新的包装函数和独立的 `fired` 状态；因此对同一事件两次调用 `once`，Set 中会有两个包装器，原回调最多分别调用一次。

当一次 emit 开始时，表达式 `[...(this.events.get(type) ?? [])]` 立即建立数组快照。此后本次循环只沿该数组继续：

- 监听器从 Set 删除后，若它已在本次快照中，当前这次仍可能调用它。
- 新监听器不会进入已经建立的快照，但下一个 emit（包括同步嵌套的 emit）会从更新后的 Set 建立新快照。
- 若删除的是最后一个成员，off 也删除 Map 中该事件名；旧数组快照仍独立存在。

所以，“注销成功”表示后续快照不再包含该监听器，不等同于把所有已经创建的分发快照都改写。

## 逐层跟踪 v10、v11 与 v12

开始时顺序为 `summary`、一次性监听器 `once`、`legacy`。处理 `v10` 时，`summary` 移除 `legacy`、加入 `recovery`，然后同步发布 `v11`。处理 `v11` 时，`once` 先注销包装器，再运行用户回调；回调同步发布 `v12`。

> [!example] 三层同步调用怎样返回
> 报表 42 的服务端流可能报告 `version: 11` 已到 `ready` 终态；消费者仍须按业务版本拒绝旧状态，事件总线不会排序业务版本。这里的 `v10`、`v11`、`v12` 是区分三次合成本地发布的标签，不是服务端事件序列；本例只观察同步调用顺序。
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
> 在本例中，先注销包装器会让之后的 `v12` 快照不再包含它；`fired` 则保护仍持有该包装器的 `v10` 旧快照，阻止它再次进入用户函数。若用户回调抛错，本实现仍把该次 `once` 视为已消费，因为 `fired` 和注销都发生在调用用户代码之前。

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

Observer（观察者模式）通常由拥有状态的对象直接保存并通知观察者；事件总线则让发布者和订阅者通过事件名及中间总线通信。前者容易沿对象找到订阅关系，后者减少模块间直接引用，却更依赖明确的事件名、载荷契约和追踪工具。本节比较的是同一浏览上下文中的两种内存实现；跨标签页消息还需要浏览上下文间通信机制。

示例保留几项实现边界：

- 分发是同步的；嵌套 `emit` 会先完成，再回到外层监听器。
- 监听器抛出的同步异常会沿调用栈传播并停止当前循环中的后续监听器。
- 返回 Promise 的监听器不会被等待；Promise 的拒绝也不会由这个 `emit` 自动收集或处理。
- 移除或新增订阅不会撤销其他地方已保存的旧快照。若生产实现选择直接遍历实时集合、异步队列或隔离监听器异常，结果顺序和错误契约都会不同。

此页的插入顺序由 ECMAScript Set 保证；快照复制时机、同步重入和 `once` 的注销规则是这份应用实现自行选择的策略，不是所有事件总线的通用保证。文档对象模型（DOM）的事件传播、默认动作和取消规则由浏览器平台另行定义，不能从这个类推导。

**延伸阅读：** [修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](./dom-collections.md) 跟踪状态通知后的节点增删；[同一报表在多个标签页中怎样交换变化？](./browser-context-communication.md) 介绍跨标签页消息；[DOM 事件传播如何经过节点？](./dom-manipulation-and-events.md) 介绍浏览器自身的事件阶段和取消规则。

> [!info]- 来源
> - Set 至多保存每个不同值一次；`add` 不会重复加入相同值，`values`/`forEach` 按值的插入顺序遍历，这支持示例中快照的初始顺序：[ECMAScript 2026 §24.2、§24.2.4.1、§24.2.4.7、§24.2.4.17](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-objects)，核验于 2026-11-12。复制快照、`once` 包装器及异常传播是本文代码的可观察结果，不是该规范规定的事件总线语义。
> - 浏览器 `EventTarget` 的事件分发、传播路径、监听器移除和取消机制：[WHATWG DOM Living Standard §2.9–2.11 Events](https://dom.spec.whatwg.org/#events)，核验于 2026-11-12。它是平台事件系统，与本页自建 `EventBus` 分开。
