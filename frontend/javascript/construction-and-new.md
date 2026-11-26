# new 一个对象时发生了什么？

沿用主线一的报表页：页面创建一个报表服务 `new ReportService("Sales")`，新对象要保存自己的前缀和带独立计数的处理器，格式化方法则放在原型上共享。本章跟着这次 `new` 走完：目标能不能构造，新对象的原型从哪来，构造器里的 `this` 是谁，最后为什么可能拿到另一个对象。普通函数的 `this` 规则见[函数里的变量和 this 从哪来？](./scope-closures-and-this.md)，本章只讲构造调用。

## 一次 new 的全过程

先看案例。`makeReportHandler` 用闭包保存计数，`format` 放在 `ReportService.prototype` 上：

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
service.prefix;                    // "Sales"
service.onReport({ title: "May" }); // "Sales/daily: May #1"
~~~

`new C(a, b)` 对普通基类构造器依次做五件事：

1. 求值构造器表达式 `C` 和实参 `a`、`b`。
2. 检查 `C` 能否构造，不能就抛 `TypeError`。
3. 读 `newTarget.prototype` 选定原型，创建新对象，即 receiver（接收者）。直接 `new C(...)` 时，`newTarget` 就是 `C`。
4. 以接收者为 `this` 初始化实例字段（若有），再运行构造器函数体。
5. 看函数体的返回值：是对象就用它，否则用接收者。

本例中 `ReportService.prototype` 是对象，函数体运行前接收者就已连上它；函数体把 `prefix` 和 `onReport` 写在接收者上；没有显式 `return`，所以 `service` 就是这个接收者。之后 `service.onReport(...)` 以 `service` 为 `this`，处理器沿原型找到 `format`，再从接收者读 `prefix`。共享方法怎样被找到，见[读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](./objects-properties-and-prototypes.md)。

任一步抛错，本次构造就中断，不会正常返回。下面几节逐步展开，派生 `class`、`new.target` 和绑定函数各自改变其中某一步。

## 目标必须可构造

能被普通调用不等于能 `new`。语言用 `IsConstructor` 检查目标有没有 `[[Construct]]` internal method（内部构造方法）——这是语言定义的构造操作，不是对象上叫 `Construct` 的属性。

有没有 `prototype` 属性不能证明能否构造。下表检查的是语法刚创建、尚未手动增删属性的函数：

| 函数形式 | 自有 `prototype` | 能否作为构造目标 |
|---|---|---|
| 普通 `function F() {}` | 有 | 能 |
| `class C {}` | 有 | 能；但直接调用 `C()` 报错 |
| 箭头函数 | 无 | 不能 |
| 普通（非生成器、非异步）简洁方法，如 `{ m() {} }` 的 `m` | 无 | 不能 |
| 生成器函数或生成器简洁方法 | 有 | 不能 |
| 异步函数或异步简洁方法 | 无 | 不能 |
| 异步生成器函数或方法 | 有 | 不能 |

class 构造器有构造能力：可以 `new`，可以作 `Reflect.construct` 的目标，可以经派生类的 `super()` 调用，只是不能普通调用。

构造能力检查发生在实参求值**之后**。下面的目标不可构造，但计数已经加一，所以 `new` 抛 `TypeError` 不代表什么都没发生：

~~~javascript
const notAConstructor = () => {};
let argumentCount = 0;
let constructionError;
try {
  new notAConstructor(++argumentCount);
} catch (error) {
  constructionError = error.name;
}
[constructionError, argumentCount]; // ["TypeError", 1]
~~~

## 原型取自 newTarget.prototype

通过检查后，普通基类构造先读 `newTarget.prototype`，再创建接收者：

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  P["读取 newTarget.prototype"] --> T{"读到的值是对象？"}
  T -->|是，函数也算| V["用这个对象作原型"]
  T -->|否，包括 null| R["用 newTarget 所属 Realm 的<br/>Object.prototype"]
  V --> I["创建接收者，绑定为 this<br/>初始化实例字段（若有）"]
  R --> I
~~~

两条分支都能直接验证：

~~~javascript
function Parent() {}
function Child() {}
Child.prototype = Parent; // 函数也是对象，可以作原型
Object.getPrototypeOf(new Child()) === Parent; // true

function FallbackDemo() {}
FallbackDemo.prototype = null;
Object.getPrototypeOf(new FallbackDemo()) === Object.prototype; // true（同一 Realm）
~~~

右支的回退值取自 `newTarget` 所属的 Realm（执行域）。每个 Realm（例如一个 iframe）有自己的一套内建对象，所以跨 Realm 构造时，回退得到的不一定是当前代码所在 Realm 的 `Object.prototype`。

## 构造器的返回值可能替换接收者

接收者建好后，构造器带着实参运行函数体。函数体对 `this` 的修改都留在接收者上，但 `new` 表达式最终得到什么，要看返回值：

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  I["接收者作为 this<br/>运行构造器函数体"] --> T{"返回值是对象？"}
  T -->|是，函数也算| O["返回这个对象<br/>新建的接收者被丢弃"]
  T -->|否，包括 null 和 undefined| N["返回新建的接收者"]
~~~

数字、字符串、布尔值、Symbol、BigInt、`null`、`undefined` 都是 primitive value（原始值），不会替换接收者。没有 `return` 相当于返回 `undefined`，报表案例走的就是右支。

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive().created; // true：数字被忽略

function ReturnsNull() {
  this.created = true;
  return null;
}
new ReturnsNull().created; // true：null 不是对象

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }

function ReturnsFunction() {
  return function replacement() {};
}
typeof new ReturnsFunction(); // "function"
~~~

## 派生 class 的 this 由 super() 初始化

派生 `class` 的构造器（derived constructor）不自己创建接收者，第 3 步换成了 `super()`：它用**同一个** `newTarget` 调用基类构造器，把基类的构造结果绑定为派生构造器的 `this`，再初始化派生类自己的实例字段。调用 `super()` 之前不能读写 `this`。

派生构造器的返回规则也比基类严格：

| 派生构造器的结局 | 结果 |
|---|---|
| 调用过 `super()`，返回 `undefined`（或没有 `return`） | 采用已初始化的 `this` |
| 返回对象或函数（调用过 `super()` 与否都行） | 用返回值替换 |
| 没调用 `super()`，返回 `undefined` | `ReferenceError`：没有接收者 |
| 返回 `null` 或其他非 `undefined` 原始值 | `TypeError` |

下面的例子沿用上文的 `ReportService`：

~~~javascript
class FactoryReport extends ReportService {
  constructor(prefix) {
    return new ReportService(prefix); // 返回对象，可以不调用 super()
  }
}
const factoryResult = new FactoryReport("North");
factoryResult.prefix;                                          // "North"
Object.getPrototypeOf(factoryResult) === ReportService.prototype; // true
factoryResult instanceof FactoryReport;                        // false：结果是替换对象

class InvalidDerivedReport extends ReportService {
  constructor() {
    return 1;
  }
}
try { new InvalidDerivedReport(); } catch (error) { error.name; } // "TypeError"

class UninitializedReport extends ReportService {
  constructor() {
    return undefined; // 没有 super()，this 从未初始化
  }
}
try { new UninitializedReport(); } catch (error) { error.name; } // "ReferenceError"
~~~

基类显式返回对象时，`super()` 把这个对象绑定为派生层的 `this`，派生层接着往它身上写。三层例子里，每一层都在基类返回的那个普通对象上继续初始化：

~~~javascript
class ReplacementBase {
  constructor() {
    return { fromBase: true, seenByBase: new.target };
  }
}
class MiddleLayer extends ReplacementBase {
  constructor() {
    super();
    this.fromMiddle = true;
  }
}
class LeafLayer extends MiddleLayer {
  constructor() {
    super();
    this.seenByLeaf = new.target;
  }
}
const leaf = new LeafLayer();
[
  leaf.fromBase,
  leaf.fromMiddle,
  leaf.seenByBase === LeafLayer,
  leaf.seenByLeaf === LeafLayer,
  leaf instanceof LeafLayer,
];
// [true, true, true, true, false]
~~~

`leaf` 是基类返回的普通对象，原型是 `Object.prototype`，所以不是 `LeafLayer` 的实例。`seenByBase` 也是 `LeafLayer`，原因见下一节。

## new.target 是沿一次构造传递的目标

`new.target` 读的是本次构造的 `newTarget`。普通 `new C()` 中它是 `C`；普通调用时是 `undefined`。派生类每次 `super()` 都把同一个 `newTarget` 传给基类，所以多层继承里每一层看到的都是最初那次 `new` 的目标——上例基类里的 `new.target` 是 `LeafLayer`，不是“当前正在执行的构造器”。

这也是派生类实例能连上派生类原型的原因：基类按 `newTarget.prototype` 选原型。

~~~javascript
class RegionalReportService extends ReportService {
  constructor(prefix) {
    super(prefix);
    this.createdBy = new.target;
  }
}

const regional = new RegionalReportService("Sales");
regional.createdBy === RegionalReportService;                          // true
Object.getPrototypeOf(regional) === RegionalReportService.prototype;   // true
regional.onReport({ title: "May" });                                    // "Sales/daily: May #1"
~~~

箭头函数没有自己的 `new.target`，沿词法环境读外层那次调用收到的值：

~~~javascript
function TargetReader() {
  return () => new.target;
}

const arrowFromCall = TargetReader();
const arrowFromConstruction = new TargetReader();
[arrowFromCall() === undefined, arrowFromConstruction() === TargetReader];
// [true, true]
~~~

`Reflect.construct(C, args, D)` 把“执行谁”和“按谁选原型”分开：运行的是 `C` 的函数体，但 `D` 成为 `newTarget`，普通基类改从 `D.prototype` 选原型。省略第三个参数时 `newTarget` 仍为 `C`。

~~~javascript
function BaseReader() {
  this.seenTarget = new.target;
}
function AlternateTarget() {}
AlternateTarget.prototype = { source: "alternate" };

const reflected = Reflect.construct(BaseReader, [], AlternateTarget);
[
  reflected.seenTarget === AlternateTarget,
  Object.getPrototypeOf(reflected) === AlternateTarget.prototype,
];
// [true, true]
~~~

> [!info] `Reflect.construct` 的检查顺序
> 它是普通函数调用，先求值三个实参表达式。进入后先检查 `C` 可构造；显式给出 `D` 时再检查 `D` 可构造（所以 `Reflect.construct(function C() {}, [], () => {})` 抛 `TypeError`，不进入 `C` 的函数体）；然后要求 `args` 是对象，按 `length` 和索引读出实参列表；最后启动构造。任一步抛错就不再继续——目标不可构造时，连 `args.length` 都不会读。

## 绑定函数构造时丢弃保存的 this

bound function（绑定函数）能否构造取决于目标：目标可构造，`bind` 返回的函数也可构造。用 `new` 调用它时：

- 已保存的 `this` 被忽略，接收者照常新建；
- 保存的前置参数仍放在实参列表前面；
- 若 `newTarget` 就是绑定函数本身（如直接 `new boundFn()`），改用原目标函数作 `newTarget`，所以新对象的原型取自原函数的 `prototype`。绑定函数自己没有 `prototype` 属性。

~~~javascript
function BuildReport(prefix, title) {
  this.prefix = prefix;
  this.title = title;
  this.seenTarget = new.target;
}

const boundBuildReport = BuildReport.bind({ prefix: "ignored" }, "North");
const builtReport = new boundBuildReport("May");
[
  builtReport.prefix,
  builtReport.title,
  builtReport.seenTarget === BuildReport,
  Object.getPrototypeOf(builtReport) === BuildReport.prototype,
];
// ["North", "May", true, true]
~~~

## 把步骤串成一个简化模型

把原型选择、接收者绑定和返回值替换串起来，可以写一个教学模型。它只覆盖当前 Realm 中直接使用的普通基类函数构造器，并假设：目标已知可构造；函数体不依赖 `new.target`；`fn.prototype` 和返回值都不是浏览器的历史遗留对象 `document.all`（它的 `typeof` 是 `"undefined"`，语言却把它当对象，模型会判错）。

~~~javascript
function emulateNew(fn, ...args) {
  const candidate = fn.prototype;
  const prototype =
    candidate !== null &&
    (typeof candidate === "object" || typeof candidate === "function")
      ? candidate
      : Object.prototype;
  const receiver = Object.create(prototype);
  const result = Reflect.apply(fn, receiver, args);
  const isObject =
    result !== null &&
    (typeof result === "object" || typeof result === "function");
  return isObject ? result : receiver;
}

function SimpleReport(prefix) {
  this.prefix = prefix;
}
SimpleReport.prototype.describe = function () { return this.prefix; };

const simple = emulateNew(SimpleReport, "West");
[Object.getPrototypeOf(simple) === SimpleReport.prototype, simple.describe()];
// [true, "West"]
~~~

用 `Reflect.apply` 而不是 `fn.apply(...)`，是为了不被函数自己的 `apply` 属性遮住内建方法。模型仍替代不了 `[[Construct]]`：

- 没有 `newTarget`，所以没有 `new.target`，也做不了 `Reflect.construct` 式的原型改选；
- 会把不可构造的箭头函数当普通函数调用，遇到 class 构造器则因不能普通调用而抛错；`typeof fn === "function"` 不足以判断能否构造；
- 不实现派生构造器、绑定函数、内置构造器、Proxy 的 `construct` trap 和跨 Realm 回退。

应用代码直接用 `new`、class 语法或 `Reflect.construct`。

## 构造完成后，谁接手这个对象

一次 `new` 交出的是：一个原型取自 `newTarget.prototype` 的接收者（或构造器显式返回的对象），上面带着函数体写入的自有属性。派生类改由 `super()` 提供接收者，`new.target` 沿整次构造传递，绑定函数构造时丢弃保存的 `this`。

之后对这个对象的每次读写，按原型链和属性描述符进行，见[读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](./objects-properties-and-prototypes.md)。若要拦截构造本身——代理一个构造器、在 `construct` trap 里转发 `newTarget`——见[Proxy 能拦截什么，又在哪里拦不住？](./proxy-and-reflect.md#函数代理保留调用与构造能力)。

> [!info]- 来源
> - `new` 先求值实参、再检查构造能力（“一次 new 的全过程”“目标必须可构造”）：[ECMAScript 2026 EvaluateNew](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatenew)（§13.3.5.1.1）。
> - 普通函数 `[[Construct]]`：接收者创建、实例字段初始化、基类与派生类的返回规则（“构造器的返回值可能替换接收者”“派生 class 的 this 由 super() 初始化”）：[ECMAScript 2026 `[[Construct]]`](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects-construct-argumentslist-newtarget)（§10.2.2）。
> - 从 `newTarget.prototype` 选原型及非对象回退到所属 Realm（“原型取自 newTarget.prototype”）：[ECMAScript 2026 GetPrototypeFromConstructor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor)（§10.1.14）。
> - 派生 class 构造器与 `super()` 沿用同一 `newTarget`、绑定基类结果为 `this`：[ECMAScript 2026 Class Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)（§15.7）、[SuperCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-super-keyword)（§13.3.7.1）。
> - `new.target` 取当前函数环境的 `NewTarget`，箭头函数沿词法环境解析（“new.target 是沿一次构造传递的目标”）：[ECMAScript 2026 GetNewTarget](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getnewtarget)（§9.4.5）、[Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)（§9.1.1.3）、[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)（§15.3）。
> - `Reflect.construct` 的检查顺序（同节 callout）：[ECMAScript 2026 Reflect.construct](https://tc39.es/ecma262/2026/multipage/reflection.html#sec-reflect.construct)（§28.1.2）。
> - 绑定函数仅在目标可构造时有 `[[Construct]]`，构造时合并前置实参并替换 `newTarget`（“绑定函数构造时丢弃保存的 this”）：[ECMAScript 2026 Bound Function Exotic Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-bound-function-exotic-objects)（§10.4.1）。
> - `document.all` 带 `[[IsHTMLDDA]]`，`typeof` 返回 `"undefined"`（“把步骤串成一个简化模型”）：[WHATWG HTML HTMLAllCollection](https://html.spec.whatwg.org/multipage/common-dom-interfaces.html#the-htmlallcollection-interface)（§2.6.4.1）。
> - 本章各代码块的结果在 Node.js 26.13.1 上复跑核对。
