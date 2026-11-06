# JavaScript 的 `new` 如何构造对象？

执行 `new` 时，JavaScript 先要求目标可构造，再调用目标的 `[[Construct]]` 内部方法。下面流程图只概括普通基类构造器：它创建 receiver（接收者）并运行函数体，通常依据 `newTarget.prototype` 选择新接收者的原型；显式返回对象或函数可以替换它，返回原始值则保留新接收者。派生 `class` 构造器有额外规则，后文单独说明。

~~~mermaid
flowchart TD
  A["确认目标可构造"] --> B["按 new.target 选择原型"]
  B --> C["创建并初始化接收者"]
  C --> D["运行构造函数体"]
  D --> E{"是否返回对象或函数？"}
  E -- "是" --> F["采用显式返回值"]
  E -- "否：原始值或 undefined" --> G["采用新建的接收者"]
~~~

派生 `class` 构造器可以不调用 `super()` 而直接返回对象；显式返回除 `undefined` 外的原始值会抛出 `TypeError`。

## 报表服务使用构造出的接收者

案例背景：下面在本页定义新的构造器、实例字段和原型方法。新实例的 `prefix` 与 `onReport` 是自有属性；`format` 在原型上共享，处理器则捕获独立的 `tag` 和 `calls`：

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

const service = new ReportService("Sales");
Object.getPrototypeOf(service) === ReportService.prototype; // true
service.prefix; // "Sales"
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
~~~

`new ReportService("Sales")` 会依据 `ReportService.prototype` 建立接收者，再以该接收者执行构造器。处理器由本页新建，因此第一次成功调用的计数从 1 开始；原型方法从实例接收者读取 `prefix`。

## 构造器返回值可能替换接收者

返回原始值不会替换实例，返回对象或函数则会替换。此规则适用于普通构造器；`class` 对派生构造器的返回值另有约束。

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive().created; // true

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }

function ReturnsFunction() {
  return function replacement() {};
}
typeof new ReturnsFunction(); // "function"

class FactoryReport extends ReportService {
  constructor(prefix) {
    return new ReportService(prefix); // 可直接返回对象，不必调用 super()
  }
}
new FactoryReport("North").prefix; // "North"

class InvalidDerivedReport extends ReportService {
  constructor() {
    return 1; // 派生构造器不能返回非 undefined 原始值
  }
}
try {
  new InvalidDerivedReport();
} catch (error) {
  error.name; // "TypeError"
}

function Parent() {}
function Child() {}
Child.prototype = Parent; // 函数本身也是对象，可用作原型
Object.getPrototypeOf(new Child()) === Parent; // true
~~~

## `new.target` 标识本次构造目标

普通调用中 `new.target` 为 `undefined`；构造调用中它标识本次 `new` 的目标。派生 class 的基类构造器会看到派生构造器作为 `new.target`。派生 class 必须先调用 `super()` 才能访问 `this`，因为基类构造过程负责建立接收者。

~~~javascript
class RegionalReportService extends ReportService {
  constructor(prefix) {
    super(prefix);
    this.createdBy = new.target;
  }
}

const regional = new RegionalReportService("Sales");
regional.createdBy === RegionalReportService; // true
Object.getPrototypeOf(regional) === RegionalReportService.prototype; // true
regional.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
~~~

`class` 构造器不能脱离 `new` 调用；箭头函数和简洁方法完全不可构造。若目标函数可构造，绑定函数也可构造；构造时忽略绑定的 `this`，但保留绑定的前置参数。

## 简化的 `new` 模型有有限输入范围

下面的教学模型只覆盖当前 `Realm`（执行域）的普通构造函数。它不实现 class、绑定函数、内置构造器、Proxy 的 `construct` trap、跨 realm 回退或全部 `new.target` 规则。标准构造在无效 `newTarget.prototype` 时会回退到该 `newTarget` 所属 realm 的内建原型；此模型限定在当前 realm，因而使用当前的 `Object.prototype`。应用代码应使用 `new`、class 语法或 `Reflect.construct`。

~~~javascript
function emulateNew(fn, ...args) {
  const candidate = fn.prototype;
  const prototype =
    candidate !== null &&
    (typeof candidate === "object" || typeof candidate === "function")
      ? candidate
      : Object.prototype;
  const instance = Object.create(prototype);
  const result = fn.apply(instance, args);
  const isObject =
    result !== null &&
    (typeof result === "object" || typeof result === "function");
  return isObject ? result : instance;
}
~~~

该模型接受函数类型的 prototype，因为函数是对象；它也保留原始值与对象返回值的区别，但 `fn.apply` 无法调用 class 构造器。

**相关机制：** [Proxy 代理对象](./proxy.md) 说明目标可构造时代理如何保留这项能力，以及 `construct` trap 的返回值边界。


> [!info]- 来源
> - new 表达式转入目标的 `[[Construct]]`：[ECMAScript 2026 EvaluateNew](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatenew)（§13.3.5.1.1）。
> - 普通函数的构造流程和返回值：[ECMAScript Function Objects Construct](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects-construct-argumentslist-newtarget)（§10.2.2）；原型及 realm 回退：[GetPrototypeFromConstructor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor)（§10.1.14）。
> - class 和派生构造器：[ECMAScript Class Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)（§15.7）。
