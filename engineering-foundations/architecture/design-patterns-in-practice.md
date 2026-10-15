# Design Patterns in Practice / 设计模式实践

A design pattern names a recurring design choice and its trade-offs. **设计模式是可复用的设计思路，不是必须套用的模板。** Choose one when it clarifies a real variation or dependency; extra indirection also has a cost.

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

## How would you design the data model for a low-code editor?

A page builder can model a document as a component tree, with each node carrying an ID, type, properties, style, and children. The editor can derive its canvas and side panels from that model, then serialize it for persistence.

~~~javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
~~~

Keep document order and visual stacking as explicit concepts. Child order can be one input to rendering, but CSS stacking contexts mean it is not universally equivalent to the final z-order; each stacking context is painted as a unit within its parent context ([CSS 2.2 visual formatting model](https://www.w3.org/TR/CSS22/zindex.html)).

- **Component registry / 组件注册表**: map a validated component type to its renderer and schema.
- **Layer order / 图层顺序**: define how siblings are ordered and translate that order into the chosen rendering model.
- **Undo and redo / 撤销与重做**: store inverse commands or immutable document snapshots; choose based on history size and operation complexity.
- **Collaboration / 协作**: a WebSocket transports updates, but does not resolve concurrent edits. A server-authoritative order, locks, operational transformation, or a CRDT may fit different conflict and offline requirements.

---

## How does Role-Based Access Control (RBAC) work?

**基于角色的访问控制 / Role-Based Access Control** associates permissions with roles and assigns users to roles. It is one authorization model; it does not determine whether a particular user may access every object of a type.

A relational model commonly includes:

- **User / 用户**: identity and credential reference.
- **Role / 角色**: named job or application role.
- **Permission / 权限**: action on a resource or capability.
- **UserRole / 用户角色**: many-to-many user-to-role assignment.
- **RolePermission / 角色权限**: many-to-many role-to-permission assignment.

A request is authenticated first, then the server checks whether the resulting subject may perform the requested action on the requested object. Check every protected operation and resource; hiding a button or trusting a client-supplied role is not authorization. Role changes simplify policy administration only when the application's permission model fits roles.

See [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) for authorization boundaries and [Design Patterns: Elements of Reusable Object-Oriented Software](https://www.informit.com/store/design-patterns-elements-of-reusable-object-oriented-software-9780201633610) for the original GoF catalog.
