# JavaScript 的 `new` 如何构造对象？

创建一个报表服务时，我们希望新对象保留自己的区域名称，同时复用共享的格式化方法。`new ReportService("Sales")` 怎样选定它的原型、让构造器里的 `this` 指向它，最后又为什么可能返回另一个对象？先跟完这个普通基类构造过程，再看派生 `class`、`new.target` 和绑定函数的变化。

## 报表服务使用构造出的接收者

案例背景：报表页面创建一个区域服务。新对象需要保留自己的 `prefix` 和带独立调用次数的处理器；格式化算法在构造函数的原型对象上共享：

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

**先选原型并建立接收者。** 在直接调用 `new C(a, b)` 时，语言先求值构造器表达式和实参，再检查 `C` 是否有 `[[Construct]]` internal method（内部构造方法）；没有就抛 `TypeError`。这里的内部方法是语言定义的构造操作，并非用户对象上名为 `Construct` 的属性。普通基类构造从 `newTarget.prototype` 选择新对象的内部原型 `[[Prototype]]`；直接 `new C(...)` 时，`newTarget` 就是 `C`。

下图从目标已通过构造能力检查后开始，只画普通基类构造；receiver（接收者）指新建并将交给构造器作为 `this` 的对象。

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  P["读取 newTarget.prototype"] --> T{"读取值是对象？"}
  T -->|是，包括函数| V["采用这个对象作为原型"]
  T -->|否，包括 null| R["采用 newTarget 所属 Realm 的<br/>Object.prototype"]
  V --> I["创建接收者，绑定 this<br/>初始化实例字段（若有）"]
  R --> I
~~~

本例的 `newTarget` 是 `ReportService`，它的 `.prototype` 是对象，因此走左支。构造函数还没运行，接收者已经连接到共享的原型对象；随后 `this.prefix` 和 `this.onReport` 写到这个接收者。这里的原型回退按 `newTarget` 所属 Realm（执行域）选择，该环境有自己的一套内建对象；不要默认总是当前代码所在环境的 `Object.prototype`。

构造器没有返回替换对象，所以 `service` 就是新接收者。接着 `service.onReport(...)` 使 `service` 成为处理器的 `this`；处理器沿实例原型找到 `format`，再从接收者读取 `prefix`。调用形式如何提供这个接收者，见[JavaScript 函数的 `this` 值由什么决定？](./this-and-function-binding.md)；共享方法如何被找到，见[JavaScript 对象如何查找属性并组织成员？](./objects-functions-and-prototypes.md)。

读取原型、初始化实例字段或执行构造器时若抛错，本次构造就中断，不会继续到正常返回。派生 `class` 的接收者初始化另有规则，下面接着说明。

只要 `newTarget.prototype` 的值是对象，它就可以作为新接收者的原型，函数本身也可以。普通 `new C()` 中 `newTarget` 就是 `C`；若普通函数构造器的 `prototype` 为 `null` 或其他原始值，构造过程会回退到 `newTarget` 所属 Realm 的 `Object.prototype`：

~~~javascript
function Parent() {}
function Child() {}
Child.prototype = Parent; // 函数也是对象，可以作为原型
Object.getPrototypeOf(new Child()) === Parent; // true

function FallbackDemo() {}
FallbackDemo.prototype = null;
// 同一 Realm：回退到当前 Object.prototype
Object.getPrototypeOf(new FallbackDemo()) === Object.prototype; // true
~~~

## 构造器返回值可能替换接收者

**再运行函数体并选择最终结果。** 沿用上一图已建立的接收者，普通基类构造器会把实参交给函数体。函数体对 `this` 的修改留在接收者上，但最终是否返回它，要看构造器的返回值：

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  I["已有接收者作为 this<br/>运行构造器函数体"] --> T{"返回值是对象？"}
  T -->|是，包括函数| O["返回显式对象<br/>它替换新建的接收者"]
  T -->|否，包括 null 和 undefined| N["返回新建的接收者"]
~~~

数字、字符串、布尔值、Symbol、BigInt、`null` 和 `undefined` 都是 primitive value（原始值），不用于替换接收者。没有显式 `return` 时相当于返回 `undefined`，所以报表案例走右支。以下四个例子分别改变返回值，其他构造规则不变：

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive().created; // true：数字返回值被忽略

function ReturnsNull() {
  this.created = true;
  return null;
}
new ReturnsNull().created; // true：null 也不是对象

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }：显式对象取代 this

function ReturnsFunction() {
  return function replacement() {};
}
typeof new ReturnsFunction(); // "function"
~~~

派生 `class` 构造器（derived constructor）必须先由 `super()` 初始化 `this`，才能读取或写入它。`super()` 用同一个 `newTarget` 调用基类构造器，并把基类构造结果绑定为派生构造器的 `this`；因此基类显式返回对象时，派生构造器接着初始化的是这个返回对象。如果派生构造器直接返回对象或函数，则可以不调用 `super()`。派生构造器的返回规则也不同于基类：调用 `super()` 后返回 `undefined` 会采用已初始化的 `this`，返回对象或函数会替换它；未调用 `super()` 却返回 `undefined` 会因没有接收者而抛出 `ReferenceError`，返回 `null` 或其他原始值会抛出 `TypeError`。

下面的派生类示例沿用上节已经定义的 `ReportService`；从头执行本文代码时先运行上节报表案例。

~~~javascript
class FactoryReport extends ReportService {
  constructor(prefix) {
    return new ReportService(prefix); // 返回对象，可以不调用 super()
  }
}

const factoryResult = new FactoryReport("North");
factoryResult.prefix; // "North"
Object.getPrototypeOf(factoryResult) === ReportService.prototype; // true
factoryResult instanceof FactoryReport; // false：结果是替换对象

class InvalidDerivedReport extends ReportService {
  constructor() {
    return 1; // 非 undefined 原始值不允许
  }
}
try {
  new InvalidDerivedReport();
} catch (error) {
  error.name; // "TypeError"
}

class UninitializedReport extends ReportService {
  constructor() {
    return undefined; // 没有 super()，也没有初始化 this
  }
}
try {
  new UninitializedReport();
} catch (error) {
  error.name; // "ReferenceError"
}
~~~

## `new.target` 标识本次构造目标

`new.target` 读取这次构造传入的 `newTarget`。普通 `new C()` 中它是 `C`；`Reflect.construct(C, args, D)` 运行的仍是 `C`，但让 `D` 成为 `newTarget`，于是普通基类创建接收者时改从 `D.prototype` 选原型。省略第三参数时 `newTarget` 仍为 `C`。相反，把不可构造的箭头函数传作第三参数，如 `Reflect.construct(function C() {}, [], () => {})`，会抛出 `TypeError`，不会进入目标构造器函数体。

> [!info] Reflect 的检查顺序
> `Reflect.construct` 是函数调用，先求值 `C`、`args` 和 `D` 的实参表达式。进入它后先检查 `C`、显式提供时再检查 `D`，两者都必须可构造；随后要求 `args` 是对象，从它读取数组状的实参列表，最后启动构造。任一步抛错就不再继续。这个顺序不同于“先读取参数列表，再判断能不能构造”。

派生 class 每次调用 `super()` 都把同一个 `newTarget` 传给基类，因此多层继承中每一层构造器都看到同一次构造传入的目标。`super()` 把基类的构造结果（包括基类显式返回的对象）绑定为派生构造器的 `this`，再初始化派生类自己的实例字段。

下面的派生类代码沿用前面报表案例中已经定义的 `makeReportHandler` 和 `ReportService`；请按本文顺序执行。

~~~javascript
class RegionalReportService extends ReportService {
  constructor(prefix) {
    super(prefix);
    this.createdBy = new.target;
  }
}

const regional = new RegionalReportService("Sales");
regional.createdBy === RegionalReportService; // true
Object.getPrototypeOf(regional) ===
  RegionalReportService.prototype; // true
regional.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
~~~

**箭头读取外层收到的目标。** 下面让同一个函数分别被普通调用和构造调用；它返回一个箭头函数，稍后再读出那次调用的 `new.target`：

~~~javascript
function TargetReader() {
  return () => new.target;
}

const arrowFromCall = TargetReader();
const arrowFromConstruction = new TargetReader();
[
  arrowFromCall() === undefined,
  arrowFromConstruction() === TargetReader,
]; // [true, true]
~~~

**Reflect 可以分开“执行谁”和“按谁选原型”。** `BaseReader` 执行函数体，而 `AlternateTarget` 提供本次 `newTarget`：

~~~javascript
function BaseReader() {
  this.seenTarget = new.target;
}
function AlternateTarget() {}
AlternateTarget.prototype = { source: "alternate" };
const reflected = Reflect.construct(BaseReader, [], AlternateTarget);
const reflectedResults = [
  reflected.seenTarget === AlternateTarget,
  Object.getPrototypeOf(reflected) === AlternateTarget.prototype,
]; // [true, true]
reflectedResults; // [true, true]
~~~

**基类返回的对象沿 `super()` 传给派生层。** 这个三层例子里的基类返回新对象，每一层接着使用它；`new.target` 始终是 `LeafLayer`：

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
const leafResults = [
  leaf.fromBase,
  leaf.fromMiddle,
  leaf.seenByBase === LeafLayer,
  leaf.seenByLeaf === LeafLayer,
];
leafResults; // [true, true, true, true]
~~~

`new.target` 不是等价于构造器函数体的局部名称：它是沿这次构造传递的目标。箭头函数自身不建立这个绑定。在本例的函数内嵌套中，它沿词法环境读取 `TargetReader` 那次调用收到的 `newTarget`。`TargetReader()` 直接调用时该值是 `undefined`，`new TargetReader()` 时是 `TargetReader`；通过 `new LeafLayer()` 逐层执行 `super()` 进入基类时，基类中的 `new.target` 仍是 `LeafLayer`，不是当前执行的基类构造器名称。

## 可调用的函数未必可以用 `new`

构造器表达式与实参求值完毕后，`new` 按 `IsConstructor`（构造能力检查）判断目标是否具有构造能力；仅能被普通调用不够。普通函数声明通常可构造。class 构造器也有构造能力，可以作为 `Reflect.construct` 的目标或通过派生类的 `super()` 调用；直接写 `C()` 则会抛出 `TypeError`。箭头函数、普通非生成器简洁方法、生成器函数、async function（异步函数）和 async generator（异步生成器）都不可构造；生成器与异步生成器简洁方法也不可构造。函数上是否有名为 `prototype` 的属性不能单独证明它可构造，例如生成器函数及生成器简洁方法可以有这个属性但仍不支持 `new`。

这两项能力可以直接并排看。下表检查语法刚创建的函数，尚未手动添加、删除或替换其属性：

| 函数形式 | 自有 `prototype` | 能否作为构造目标 |
|---|---|---|
| 普通 `function F() {}` | 有 | 能 |
| `class C {}` | 有 | 能；直接 `C()` 仍报错 |
| 箭头函数 | 无 | 不能 |
| 普通非生成器简洁方法 | 无 | 不能 |
| 生成器函数或生成器简洁方法 | 有 | 不能 |
| 异步函数或普通异步简洁方法 | 无 | 不能 |
| 异步生成器函数或方法 | 有 | 不能 |

能力检查不阻止更早的实参求值。下面目标不可构造，但计数已经增加；因此不能把 `new` 的错误理解成“什么都没发生”：

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

绑定函数（bound function）是否能构造取决于目标函数：目标可构造时，`bind` 返回的绑定函数也可构造。使用 `new` 调用它时，已经绑定的 `this` 会被忽略，但绑定的前置参数仍会加入实参列表；当 `newTarget` 正是这个绑定函数时，构造会改用原目标函数作为 `newTarget`。

~~~javascript
function BuildReport(prefix, title) {
  this.prefix = prefix;
  this.title = title;
  this.seenTarget = new.target;
}

const boundBuildReport = BuildReport.bind({ prefix: "ignored" }, "North");
const builtReport = new boundBuildReport("Q4");
[
  builtReport.prefix,
  builtReport.title,
  builtReport.seenTarget === BuildReport,
  Object.getPrototypeOf(builtReport) === BuildReport.prototype,
];
// ["North", "Q4", true, true]
~~~

## 简化的 `new` 模型有有限输入范围

下面的教学模型只模拟当前 Realm 中直接使用的普通基类函数构造器：目标须已知可构造，函数体不依赖 `new.target`，而 `fn.prototype` 的值和构造器的直接返回值均不能是浏览器历史特殊对象 `document.all`。该对象虽然 `typeof` 返回 `"undefined"`，语言仍将它视为对象；模型用 `typeof` 判断这两个直接值时无法识别它。模型展示原型选择、接收者绑定和显式返回对象替换规则；不实现 class、派生构造器、绑定函数、内置构造器、Proxy 的 `construct` trap 或跨 Realm 回退。应用代码应直接使用 `new`、class 语法或 `Reflect.construct`。

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
[
  Object.getPrototypeOf(simple) === SimpleReport.prototype,
  simple.describe(),
];
// [true, "West"]
~~~

改用 `Reflect.apply` 可避免函数自有的 `apply` 属性遮住内建调用方法，但这个模型依旧不能替代 `[[Construct]]`：它没有 `newTarget`，会把箭头函数当作普通函数调用，也不能调用 class 构造器。不能仅凭 `typeof fn === "function"` 就判断它可构造，class 也不能被这个模型当作普通函数执行。

**相关机制：** [Proxy 如何拦截构造操作？](./proxy.md)说明可构造代理和 `construct` trap 必须返回对象的条件；[JavaScript 对象如何查找属性并组织成员？](./objects-functions-and-prototypes.md)解释新实例连接原型后怎样找到共享成员。

> [!info]- 来源
> - `new` 表达式先检查目标是否具有构造能力，再调用 `Construct`：[ECMAScript 2026 EvaluateNew](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatenew)（§13.3.5.1.1）。
> - 普通函数的接收者创建、实例字段初始化与基类/派生构造返回规则：[ECMAScript 2026 Function Objects `[[Construct]]`](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects-construct-argumentslist-newtarget)（§10.2.2）。
> - 从 `newTarget.prototype` 选原型及非对象回退：[ECMAScript 2026 GetPrototypeFromConstructor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor)（§10.1.14）。
> - 派生 class 的构造器和 `super()` 语义：[ECMAScript 2026 Class Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)（§15.7）。
> - `new.target` 取得当前函数环境中的 `NewTarget`：[ECMAScript 2026 GetNewTarget](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getnewtarget)（§9.4.5），以及 [Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)（§9.1.1.3）。
> - `Reflect.construct` 先检查 `target` 和 `newTarget` 的构造能力，再把 `argumentsList` 转成实参列表：[ECMAScript 2026 Reflect.construct](https://tc39.es/ecma262/2026/multipage/reflection.html#sec-reflect.construct)（§28.1.2）。派生类执行 `super()` 时沿用同一个 `newTarget`，并把基类构造结果绑定为 `this`：[SuperCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-super-keyword)（§13.3.7.1）。
> - 绑定函数只有在目标可构造时才有 `[[Construct]]`，构造时合并前置实参并处理 `newTarget`：[ECMAScript 2026 Bound Function Exotic Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-bound-function-exotic-objects)（§10.4.1）。
> - 箭头函数没有本地 `new.target` 绑定，`new.target` 会沿词法环境解析：[ECMAScript 2026 Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)（§15.3）。
> - 浏览器的 `document.all` 是带 `[[IsHTMLDDA]]` 的 `HTMLAllCollection` 对象，因此 `typeof` 会返回 `"undefined"`：[WHATWG HTML Standard HTMLAllCollection](https://html.spec.whatwg.org/multipage/common-dom-interfaces.html#the-htmlallcollection-interface)（§2.6.4.1）。
