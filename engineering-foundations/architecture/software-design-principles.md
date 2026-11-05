# How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？

Design principles help identify where a likely change would force unrelated code to change. Use a principle when it points to a concrete coupling cost and a boundary that reduces it; adding interfaces, classes, or extension points without a real source of variation merely moves complexity around. **设计原则用于判断一次可能的变化会不会迫使无关代码跟着修改。只有当原则指出了具体耦合成本，并能据此建立有价值的边界时才应用；没有真实变化点却增加接口、类或扩展点，只会把复杂度挪到别处。**

## What are the SOLID principles, and what does each mean?

**SOLID / 面向对象设计原则** is a mnemonic for five related guidelines:

- **S — Single Responsibility Principle / 单一职责原则**: keep a module cohesive around one responsibility or axis of change.
- **O — Open/Closed Principle / 开闭原则**: make a stable part of the design extensible at expected variation points, rather than editing that core for every new case.
- **L — Liskov Substitution Principle / 里氏替换原则**: a subtype must preserve the behavioral expectations clients rely on from its base type.
- **I — Interface Segregation Principle / 接口隔离原则**: clients should depend only on the operations they need.
- **D — Dependency Inversion Principle / 依赖倒置原则**: high-level policy should not depend directly on low-level details; both should depend on abstractions where that boundary pays for itself.

These guidelines can help isolate changes, but applying all of them mechanically can produce needless interfaces and indirection.

### Single Responsibility Principle (SRP)

A module should group behavior that changes for the same reason. This is not a rule that every method or data field needs a separate class.

~~~javascript
class UserRepository {
  async findById(id) { /* persistence details */ }
}

class UserPage {
  render(user) { /* presentation */ }
}
~~~

Separating persistence from presentation can help when those concerns change independently. A small component that performs a request and renders a result may still be cohesive if the application has no independent reason to change those pieces.

### Open/Closed Principle (OCP)

An extension point is useful when a kind of variation is known and likely; it is not practical to close a system against every future change.

~~~javascript
class ShippingCalculator {
  constructor(strategy) {
    this.strategy = strategy;
  }

  calculate(pkg) {
    return this.strategy.calculate(pkg);
  }
}

class ExpressShipping {
  calculate(pkg) { return pkg.weight * 10; }
}

class StandardShipping {
  calculate(pkg) { return pkg.weight * 5; }
}
~~~

A new shipping policy can be supplied without changing the calculator, while the selection and shared contract still need maintenance. See [Strategy in practice](./design-patterns-in-practice.md).

### Liskov Substitution Principle (LSP)

A subtype should preserve the behavioral contract clients expect. For example, if a base type promises that every value can fly, a penguin subtype that throws from `fly` breaks that contract. A narrower abstraction such as `Bird` for shared bird behavior and `FlyingBird` for birds that can fly may model the domain more accurately.

### Interface Segregation Principle (ISP)

Clients should not be forced to depend on operations they never use. In TypeScript, this can mean separating unrelated capabilities into small interfaces and composing them where needed; there is no universal field-count threshold.

### Dependency Inversion Principle (DIP)

High-level policy and low-level details depend on an abstraction when that boundary reduces coupling. Constructor injection is one way to supply an implementation; **dependency injection is a technique, not the definition of DIP**.

~~~javascript
class NotificationService {
  constructor(sender) {
    this.sender = sender;
  }

  notify(message) {
    this.sender.send(message);
  }
}

class EmailSender {
  send(message) { /* send email */ }
}

class SmsSender {
  send(message) { /* send SMS */ }
}

const notifications = new NotificationService(new EmailSender());
~~~

The service can use another implementation or a test double through the same contract. Add an abstraction when the variation or test boundary is real.

---

## What are DRY, KISS, and YAGNI?

**DRY, KISS, and YAGNI / 不重复、保持简单、暂不实现未需功能** are practical heuristics. They help manage complexity but should not be interpreted as absolute prohibitions.

### DRY (Don't Repeat Yourself)

Avoid duplicating the same rule or knowledge in places that must stay synchronized. Similar-looking code can represent different concepts, though; extracting it into one abstraction may couple changes that should remain independent.

### KISS (Keep It Simple)

Prefer the simplest design that satisfies current requirements. A simple implementation is easier to explain and change; complexity should have a concrete payoff.

### YAGNI (You Aren't Gonna Need It)

Do not build speculative features before a need is established. Keep the option to add an extension point when a real use case appears, and avoid confusing “not yet needed” with “never needed.”

---

See [frontend architecture boundaries](frontend-architecture-boundaries.md) for presentation and deployment ownership examples.

Sources: [Robert C. Martin, The Open-Closed Principle](https://objectmentor.com/resources/articles/ocp.pdf), [Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf), and [Liskov and Wing, A Behavioral Notion of Subtyping](https://doi.org/10.1145/197320.197383).
