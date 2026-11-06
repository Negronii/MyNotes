# JavaScript 的 `Proxy` 如何拦截对象操作？

Proxy（代理对象）把 target（目标对象）与 handler（处理器）配对。经代理执行读取、赋值等操作时，对应 trap（拦截方法）可以观察或改变操作；未定义 trap 时默认按目标对象执行。Reflect（反射 API）转发操作并保留 receiver 语义，但 trap 仍须遵守固定属性的不变量。

## 报表处理器只观察经过代理的操作

案例背景：本页新建一个构造器、实例和处理器。先用直接读取 `target[property]` 的代理观察继承 getter，再用 `Reflect.get` 显示 receiver（接收者）为何会改变 getter 内部读取是否经过代理；最后追踪方法调用的日志来源：

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

function ReportService(prefix) {
  this.prefix = prefix;
  this.onReport = makeReportHandler("daily");
}

ReportService.prototype.format = function (report, tag, sequence) {
  return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
};

Object.defineProperty(ReportService.prototype, "label", {
  configurable: true,
  get() {
    return this.prefix + " reports";
  },
});

const service = new ReportService("Sales");
const direct = new Proxy(service, {
  get(target, property) {
    console.log("direct get", String(property));
    return target[property];
  },
});

const observed = new Proxy(service, {
  get(target, property, receiver) {
    console.log("get", String(property));
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("set", String(property));
    if (property === "prefix" && typeof value !== "string") {
      throw new TypeError("prefix must be a string");
    }
    return Reflect.set(target, property, value, receiver);
  },
});

direct.label;
// 记录 direct get label；返回 "Sales reports"，getter 的 this 是 target

observed.label;
// 记录 get label、get prefix；getter 的 this 是 observed

observed.onReport({ title: "Q4" });
// 记录 get onReport、get format、get prefix
// 返回 "Sales/daily: Q4 #1"

observed.prefix = "Ops"; // 记录 set prefix
observed.onReport({ title: "Q4" }); // "Ops/daily: Q4 #2"
~~~

直接代理的 `direct.label` 只触发 `direct get label`：求值 `target[property]` 时，继承 getter 的 `this` 是原始 target，所以 getter 读取 `this.prefix` 不再经过代理。`Reflect.get(target, property, receiver)` 显式把代理作为 getter 的接收者，因此 `observed.label` 还会触发 `get prefix`。

方法日志则来自另一个机制。`observed.onReport(...)` 是方法调用，返回的处理器以 `observed` 为 `this`；它读取 `this.format` 时触发 `get format`，`format` 再读取 `this.prefix` 时触发 `get prefix`。即使 trap 用直接的 `target[property]` 返回这个方法，调用表达式仍会把 `observed` 作为 `this`。若代码保留原始 `service` 引用，就能绕过代理。代理也有独立身份：`observed !== service`。Proxy 是 JavaScript 运行时对象特性，不是 TypeScript 类型特性。

## trap 必须保留属性操作的可观察语义

getter 会在读取时执行代码，不是被动存储的值。若 trap 直接求值 `target[property]`，继承的 getter 会以 `target` 为 `this`。使用 `Reflect.get(target, property, receiver)` 转发会保留 `receiver`，因此 getter 对其他属性的读取也能经过代理观察。`Reflect.set` 同样接收 `receiver`，并返回布尔值。

若 `set` trap 返回 `false`，非严格赋值可能静默失败，严格赋值会抛出 `TypeError`。返回 `true` 也不能让 trap 违背 `target` 的某些固定属性。

~~~javascript
const rejected = new Proxy({ prefix: "Sales" }, {
  set() { return false; },
});

Reflect.set(rejected, "prefix", "Ops"); // false
rejected.prefix; // "Sales"
(function () {
  "use strict";
  rejected.prefix = "Ops"; // TypeError：set trap 报告写入失败
})();
~~~

Proxy invariant（代理不变量）禁止 trap 对不可配置的 `target` 属性报告矛盾结果。例如，`get` trap 不能为不可配置且不可写的自有数据属性返回其他值；对应的不可配置访问器若没有 getter，则必须返回 `undefined`。`set` trap 不能谎报对固定不可写属性的修改成功，也不能谎报对不可配置且没有 setter 的访问器写入成功。违反约束会抛出 `TypeError`。

~~~javascript
const fixed = Object.freeze({ id: 7 });
const inconsistent = new Proxy(fixed, {
  get(target, property, receiver) {
    if (property === "id") return 8;
    return Reflect.get(target, property, receiver);
  },
});

inconsistent.id; // TypeError：不能用 8 代替固定值 7
~~~

一个高层操作可能触发多个 trap。例如 `array.push(value)` 会写入数组索引，并更新 `length`。校验或记录写入时，应覆盖需要观察的每个操作。

归档中的校验示例用数字属性演示读写：读取和写入都会被记录，无效写入则在转发前抛错。因此 Proxy 会改变可观察行为，不是透明的性能优化。

~~~javascript
const product = new Proxy({ price: 10 }, {
  get(target, property, receiver) {
    console.log("read", String(property));
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("write", String(property));
    if (property === "price" && (!Number.isFinite(value) || value < 0)) {
      throw new RangeError("price must be a non-negative finite number");
    }
    return Reflect.set(target, property, value, receiver);
  },
});

product.price = 12; // 记录 write price 并更新目标对象
product.price;      // 12；触发 get trap
// product.price = -1; // 在转发写入前抛出 RangeError
~~~


## 可调用和可构造 target 保留相应能力

Proxy 的 `target` 必须是对象。若 `target` 可调用或可构造，代理也具有相应能力；`construct` trap 必须返回对象。`Reflect.construct` 会连同参数一起转发 `newTarget`。

~~~javascript
function ReportFactory(prefix) {
  this.prefix = prefix;
}

const tracedFactory = new Proxy(ReportFactory, {
  construct(target, args, newTarget) {
    console.log("construct", args[0]);
    return Reflect.construct(target, args, newTarget);
  },
});

const created = new tracedFactory("Finance"); // 记录 construct Finance
created instanceof ReportFactory; // true
~~~

Vue 2 用访问器实现响应式属性，Vue 3 则对响应式对象使用 Proxy；这是框架选择的例子，不代表所有应用都必须采用其中一种。

已知属性有稳定读写契约时使用访问器；需要拦截对象上的操作时再用 Proxy，例如校验之后新增的键或记录一组属性访问。Proxy 无法观察通过另行保留的 `target` 引用执行的操作。

**相关机制：** [对象与原型](./objects-functions-and-prototypes.md) 解释属性描述符和 getter；[使用 `new` 构造对象](./construction-and-new.md) 说明代理构造和 `construct` 的边界。


> [!info]- 来源
> - Proxy 的 target/handler 分发、get/set 和 construct：[ECMAScript 2026 Proxy Object Internal Methods](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-proxy-object-internal-methods-and-internal-slots)（§10.5）。
> - Proxy trap 必须遵守的对象内部方法不变量：[ECMAScript Invariants of the Essential Internal Methods](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-invariants-of-the-essential-internal-methods)（§6.1.7.3）。
> - getter 的 receiver 语义：[ECMAScript OrdinaryGet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryget)（§10.1.8.1）；对应转发 API：[ECMAScript Reflect](https://tc39.es/ecma262/2026/multipage/reflection.html)（§28）。
> - Vue 2 与 Vue 3 响应式机制的实现选择：[Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html)。
