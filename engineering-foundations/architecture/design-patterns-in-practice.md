# When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？

A design pattern names a recurring choice about construction, variation, notification, or ownership. Use it when the named boundary makes an actual change easier to localize or explain; then account for the added indirection and lifetime rules. A pattern does not remove a need to define scope, contracts, or authorization. **设计模式概括对象创建、行为变化、通知或所有权中的常见选择。只有当它能把真实变化收拢到更清晰的边界时才使用，并同时考虑新增的间接层和生命周期规则。模式不会替代对作用范围、契约和授权边界的定义。**

## When do you use the Factory pattern?

**工厂 / Factory** centralizes object creation when construction rules or the concrete type should not be repeated at call sites. A simple factory function is useful in JavaScript, but it is not automatically the GoF Factory Method or Abstract Factory pattern.

~~~javascript
function createButton(type) {
  if (type === 'primary') return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
~~~

Use this when the creation decision belongs in one place or construction has meaningful setup. If construction is already a single uncomplicated expression, a factory can add little value.

---

## When do you use the Singleton pattern?

**单例 / Singleton** constrains access to one instance within a chosen scope. A class-level static instance, for example, is one per loaded class in a JavaScript realm; it is not automatically one instance across workers, processes, duplicated module copies, or machines.

~~~javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) Store.instance = new Store();
    return Store.instance;
  }
}
~~~

Repeated calls to `getInstance()` share one instance through that accessor; because `Store` has a public constructor, `new Store()` can still create additional instances.

A shared cache, event bus, or connection pool may need one instance per process or module. Consider whether explicit dependency injection or a scoped shared instance is easier to test and reason about. A singleton's global access can hide dependencies and couple tests.

---

## When do you use the Strategy pattern?

**策略 / Strategy** puts interchangeable behavior behind a common contract. It is useful when callers must choose among algorithms or policies; a small conditional is often clearer when there is only one simple branch.

~~~javascript
const strategies = new Map([
  ['express', pkg => pkg.weight * 10],
  ['standard', pkg => pkg.weight * 5],
  ['overnight', pkg => pkg.weight * 20],
]);

function calculateShipping(name, pkg) {
  const strategy = strategies.get(name);
  if (!strategy) throw new RangeError('unknown shipping strategy');
  return strategy(pkg);
}
~~~

Adding a strategy can avoid changing the dispatcher, but the strategy contract and selection rules still need to be maintained. This can support the Open/Closed Principle when the variation is real; it does not make a design closed to every future change. See [Software Design Principles](./software-design-principles.md).

---

## What's the difference between Observer and Publish-Subscribe?

**观察者 / Observer** and **发布订阅 / Publish-Subscribe** both route notifications. In the common distinction, an observer subject knows its observers and notifies them directly; a publish-subscribe broker routes messages by topic, so publishers and subscribers need not know each other. Real libraries can combine these arrangements, so use the concrete API's contract rather than relying on the label.

### Observer

~~~javascript
class Subject {
  constructor() {
    this.observers = new Set();
  }

  subscribe(observer) {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  notify(data) {
    for (const observer of this.observers) observer.update(data);
  }
}
~~~

The subject owns the subscriptions. Returning an unsubscribe function makes the lifetime of a listener explicit.

### Publish-Subscribe

~~~javascript
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(topic, listener) {
    const subscribers = this.listeners.get(topic) ?? new Set();
    subscribers.add(listener);
    this.listeners.set(topic, subscribers);
    return () => subscribers.delete(listener);
  }

  emit(topic, data) {
    for (const listener of this.listeners.get(topic) ?? []) listener(data);
  }
}

const eventBus = new EventBus();
eventBus.on('user:login', user => { /* update the UI with user data */ });
eventBus.emit('user:login', { name: 'Alice' });
~~~

A broker can reduce direct coupling, but distributed or global event buses can make the flow harder to trace. DOM `EventTarget` is observer-like: listeners register on a target that dispatches events.

See [DOM Manipulation and Events](../../frontend/browser-apis/dom-manipulation-and-events.md) for browser event APIs.

---

See [how to model an editable component tree](low-code-editor-data-model.md) for a system-design example and [how roles control feature access](../security/web-security-and-authentication.md#%E8%A7%92%E8%89%B2%E8%83%BD%E6%8E%88%E4%BA%88%E4%BB%80%E4%B9%88%E5%8A%A8%E4%BD%9C%EF%BC%8C%E8%B5%84%E6%BA%90%E6%A3%80%E6%9F%A5%E8%BF%98%E8%A6%81%E5%81%9A%E4%BB%80%E4%B9%88%EF%BC%9F) for a distinct authorization decision.
