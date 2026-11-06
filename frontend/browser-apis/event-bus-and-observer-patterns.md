# JavaScript 事件总线在监听器中重入时怎样保持顺序？

案例背景：报表 42 的页面收到进度更新后，会让多个界面模块同步响应。event bus (事件总线) 把发布者和订阅者隔开，但监听器也可能在分发过程中增删订阅，甚至再次发布同名事件。实现必须规定当前这次分发看哪些监听器，以及一次性监听器何时注销。

下面的总线是应用层的 publish–subscribe (发布订阅) 模式，不是浏览器的 DOM 事件系统。它在 `emit()` 开始时复制监听器集合；分发途中发生的增删只影响之后开始的分发。`once()` 在调用用户函数前先标记并注销，因此递归 `emit()` 也不能再次执行同一个一次性监听器。

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

> [!example] 跟踪一次重入分发
> 初始顺序是 `summary`、一次性 `once`、旧的 `legacy`。处理版本 10 时，`summary` 移除 `legacy`、加入 `recovery`，随后同步发布版本 11。版本 11 的分发会取一份新快照；其中的 `once` 监听器注销自己后又发布版本 12。
>
> `v10`、`v11`、`v12` 是展示重入顺序的合成输入，不是报表 42 的服务端版本序列；SSE 示例中服务端版本 11 已是 `ready` 终态。真实报表消费者只把已接受的服务端状态交给界面，并继续按业务 `version` 拒绝旧更新。
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
> console.log(trace);
> ~~~
>
> 输出顺序是 `summary v10 → summary v11 → once v11 → summary v12 → recovery v12 → recovery v11 → legacy v10`。版本 10 开始的旧快照仍含 `legacy`，所以即使它已注销，最后仍会执行一次；新加入的 `recovery` 不在版本 10 的快照中，但会出现在后续的快照中。`once` 先注销，避免后续新快照再次包含它；外层版本 10 的快照仍持有包装器，真正阻止它第二次调用用户函数的是 `fired` 检查。

这个行为来自本实现的快照策略，不是所有事件总线的通用保证。同步监听器抛错时，此实现会让错误向 `emit()` 调用者传播，并停止后续监听器；异步监听器返回的 Promise 不会被等待。生产实现应按需要另行定义错误隔离、异步处理和监听器移除语义。

若一个对象自然拥有订阅者，例如数据模型通知观察者，Observer (观察者模式) 让对象直接管理订阅关系。若多个模块只通过主题名沟通，事件总线用代理降低直接耦合，但会增加追踪事件来源的成本。两者都可把流式报表状态更新送到本地界面；跨标签页则需使用浏览上下文间的通信机制。

**延伸阅读：** [修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](./dom-collections.md) 跟踪状态通知后的节点增删；[同一报表在多个标签页中怎样交换变化？](./browser-context-communication.md) 介绍跨标签页消息；[DOM 事件传播如何经过节点？](./dom-manipulation-and-events.md) 介绍浏览器自身的事件阶段和取消规则。

> [!info]- 来源
> - `Set` 保存不同监听函数并按插入顺序迭代；`emit()` 的快照和 `once()` 的注销策略是本文这份应用实现明确采用的规则：[ECMAScript Language Specification，Keyed Collections](https://tc39.es/ecma262/multipage/keyed-collections.html#sec-set-objects)，2026-11-06 核对。
> - DOM 事件的分发规则由浏览器平台定义，与上述应用层事件总线不同：[WHATWG DOM Standard，Events](https://dom.spec.whatwg.org/#events)。
