# How can a JavaScript event bus handle reentrancy? / JavaScript 事件总线如何处理重入？

An event bus keeps listeners by event name and emits to a snapshot so that listener additions or removals during dispatch affect the next emission. A one-time wrapper should mark itself fired and unregister before calling user code; this keeps recursive emits and reentrant snapshots from invoking it twice. Observer and publish-subscribe are different coupling patterns: an observer subject knows its listeners, while a bus mediates between publishers and subscribers. / 事件总线按事件名保存监听器，触发时遍历快照，因此分发期间新增或删除监听器影响下一次触发。一次性包装器应先标记已触发并注销，再调用用户代码；这能避免递归触发和重入快照造成重复调用。观察者与发布订阅的耦合方式不同：观察者主体直接知道监听者，事件总线则位于发布者和订阅者之间。

~~~javascript
class EventBus {
  events = new Map();

  on(event, listener) {
    if (!this.events.has(event)) this.events.set(event, new Set());
    this.events.get(event).add(listener);
  }

  once(event, listener) {
    let fired = false;
    const wrapper = (...args) => {
      if (fired) return;
      fired = true;
      this.off(event, wrapper); // unregister before user code can recurse
      listener(...args);
    };
    this.on(event, wrapper);
  }

  emit(event, ...args) {
    // Mutations during dispatch affect the next emission.
    for (const listener of [...(this.events.get(event) ?? [])]) listener(...args);
  }

  off(event, listener) {
    const listeners = this.events.get(event);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(event);
  }
}
~~~

A reentrant case explains why both the snapshot and the `fired` guard matter:

~~~javascript
const bus = new EventBus();
let firstCalls = 0;
let laterCalls = 0;
bus.once("x", () => { firstCalls += 1; bus.emit("x"); });
bus.once("x", () => { laterCalls += 1; });
bus.emit("x");
console.assert(firstCalls === 1 && laterCalls === 1);
~~~

The outer emission still has its original snapshot after the nested emission removes the later one-time listener. Its wrapper remains present in the outer snapshot, but the `fired` guard makes the second entry a no-op. This small implementation propagates a thrown listener error and documents snapshot mutation; production emitters should define their own error, removal, and async-listener policies.

Use **Observer** when there is a natural subject that owns its subscribers, such as a DOM node or data model. Use **publish-subscribe** when a broker should decouple modules, accepting the indirect path's debugging cost.

**See also:** [How do DOM events propagate?](./dom-manipulation-and-events.md) covers platform event dispatch, which has different phases and cancellation rules.

**Terminology note:** this is an application-level pattern, not the browser DOM event system.
