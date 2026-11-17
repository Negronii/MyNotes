# JavaScript 函数的 `this` 值由什么决定？

**案例背景。** 报表服务要把 Q4 数据格式化成一行文本：`service.onReport(...)` 能正常格式化，但把同一个函数取出来单独调用（下文称“裸调”）却抛 `TypeError`。函数没变，变的是调用表达式。本页讲 ordinary function（普通函数）在普通调用和 `call` / `apply` / `bind` 中的 `this`，并与箭头函数、DOM 监听器对照；`new` 构造调用见[JavaScript 的 `new` 如何构造对象？](./construction-and-new.md)。

以下每个代码块都可独立运行，注释给出求值结果。含 sloppy function（非严格函数）的代码块要作为 classic script（经典脚本）运行，不能放进 ES module（ES 模块），因为模块代码总是严格模式；DOM（Document Object Model，文档对象模型）例子需要浏览器页面已有 `document.body`。

## 调用形式为报表处理器提供接收者

同一个处理器先以方法形式调用，再取出裸调，最后恢复为方法调用：

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

const service = {
  prefix: "Sales",
  format(report, tag, sequence) {
    return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
  },
  onReport: makeReportHandler("daily"),
};

const firstReport = service.onReport({ title: "Q4" });
const detached = service.onReport;
let detachedError;
try {
  detached({ title: "Q4" });
} catch (error) {
  detachedError = error.name;
}
const thirdReport = service.onReport({ title: "Q4" });
[firstReport, detachedError, thirdReport];
// ["Sales/daily: Q4 #1", "TypeError", "Sales/daily: Q4 #3"]
~~~

`service.onReport(...)` 是方法调用，属性访问 `service.onReport` 的基底对象 `service` 成为这次调用的 `this`。存入变量 `detached` 再调用时，调用表达式里没有基底对象；处理器开头有 `"use strict"`，是 strict function（严格函数），于是 `this` 为 `undefined`，读取 `this.format` 时抛出 `TypeError`。计数器 `calls` 存在 closure（闭包）里，而失败发生在递增之后，所以第三次调用返回 `#3`。

## 严格模式会改变部分调用行为

上例的裸调之所以得到 `undefined` 而不是全局对象，是因为处理器处于严格模式。普通函数的 `this` 分两步确定：先由调用表达式提供一个初值，即 receiver（接收者）；再由被调函数自己的模式决定怎样使用这个初值。点号或方括号形式的属性调用把属性访问的基底作为接收者，基底可以是对象，也可以是原始值（如 `"Q4".toString()`）。一般的变量裸调 `fn()` 提供 `undefined`；唯一的例外是非严格代码里的 `with` 语句块，它可以为这种调用提供对象接收者。

strict mode（严格模式）会把一些历史上静默出错的写法变成异常，也改变普通函数使用 `this` 初值的方式。经典脚本或函数体可以在开头写 `"use strict"` 指令启用它；ES 模块和 class（类）内的代码自动处于严格模式。strict function（严格函数）原样保留初值；sloppy function（非严格函数）把 `null` 或 `undefined` 换成函数所属 Realm（执行域）的全局 `this` 值，并把数字、字符串、布尔值、BigInt（大整数）或 Symbol（符号值）接收者装箱。即使调用表达式位于严格代码中，非严格被调函数仍会进行转换。严格模式不是安全沙箱，也不会让 `eval` 变安全。

| 被调函数模式 | 常见变量裸调用 `fn()` | `fn.call(null)` | `fn.call(7)` |
| --- | --- | --- | --- |
| strict function（严格函数） | `undefined` | `null` | 原始数字 `7` |
| sloppy function（非严格函数） | 所属 Realm 的全局 `this` 值 | 所属 Realm 的全局 `this` 值 | Number object（Number 包装对象） |

~~~javascript
function sloppyTarget() {
  return this;
}

function strictCaller() {
  "use strict";
  return sloppyTarget();
}
strictCaller() === globalThis; // true：被调函数仍按非严格模式绑定 this。

function writeUndeclaredName() {
  "use strict";
  undeclaredName = 1;
}

try {
  writeUndeclaredName();
} catch (error) {
  error.name; // "ReferenceError"
}
~~~

上例中 `strictCaller` 虽然是严格函数，它调用的 `sloppyTarget` 仍按非严格规则把 `undefined` 换成全局对象：起作用的是被调函数的模式。`writeUndeclaredName` 演示了另一类变化：严格代码给未声明的变量赋值会抛 `ReferenceError`，而不是悄悄创建全局变量。此外，严格代码给不可写属性赋值会抛出 `TypeError`，并禁止 `with`、旧式八进制字面量和重复形参。

## `call`、`apply` 与 `bind` 的调用时机不同

除了调用形式，还可以用函数自带的 `call`、`apply`、`bind` 显式指定接收者。三者的第一个参数都是 `thisArg`（要传给目标函数的 `this`），区别在于何时执行目标、实参从哪里来：

| 方法 | 目标执行时机 | 实参来源 | `thisArg` 怎样到达目标 |
| --- | --- | --- | --- |
| `call` | 立即 | 后续分开的参数 | 原样交给目标；strict function 保留，sloppy function 按上一节转换 |
| `apply` | 立即 | 空列表，或从对象的 `length` 和索引读取 | 原样交给目标；strict function 保留，sloppy function 按上一节转换 |
| `bind`（绑定） | 调用返回的新函数时 | 保存的前置参数，再加调用时参数 | 保存并交给目标；strict function 保留，sloppy function 按上一节转换 |

目标若是 arrow function（箭头函数）或 bound function（绑定函数）则会忽略传入的 `thisArg`；箭头函数稍后单独说明。`apply` 省略 argument list（实参列表）或传 `null`、`undefined` 时使用空列表；其他输入必须是对象，内置方法按其 `length` 与数字索引读取实参，不会遍历迭代器。

~~~javascript
function describe(prefix, report, punctuation) {
  "use strict";
  const message = this.prefix + ": " + prefix + " " + report.title;
  return message + (punctuation === undefined ? "" : punctuation);
}

const salesContext = { prefix: "Sales" };
const report = { title: "Q4" };
const boundDescribe = describe.bind(salesContext, "Ready");
const reboundDescribe = boundDescribe.bind(
  { prefix: "Ignored" }, report, "!",
);

const callResults = [
  describe.call(salesContext, "Ready", report),
  describe.apply(salesContext, ["Ready", report]),
  describe.apply(salesContext, { 0: "Ready", 1: report, length: 2 }),
  boundDescribe(report),
  reboundDescribe(),
];

function countArgs() {
  return arguments.length;
}
let primitiveListError;
try {
  countArgs.apply(salesContext, "Q4");
} catch (error) {
  primitiveListError = error.name;
}
const applyResults = [
  countArgs.apply(salesContext),
  countArgs.apply(salesContext, null),
  countArgs.apply(salesContext, undefined),
  countArgs.apply(salesContext, { 0: "one", length: 1 }),
  countArgs.apply(salesContext, new Set(["one"])),
  primitiveListError,
];
[callResults[0], callResults[4], applyResults];
// [
//   "Sales: Ready Q4",
//   "Sales: Ready Q4!",
//   [0, 0, 0, 1, 0, "TypeError"],
// ]
~~~

对已绑定的函数再调用 `bind`，不会替换最初保存的接收者，但新的前置实参会追加在原有前置实参之后；`reboundDescribe()` 因此在原报表结果后追加标点。`Set` 实例没有 `length`，而 `apply` 不读取它的迭代器，所以这里得到空实参列表；原始字符串不是对象，作为原生 `apply` 的参数列表会抛 `TypeError`。`new` 调用可构造的绑定函数时会忽略已保存的接收者，却保留前置参数；构造行为见[JavaScript 的 `new` 如何构造对象？](./construction-and-new.md)。若自己用包装函数模拟 `bind`、只负责拼接实参，就得不到原生绑定函数的构造行为，也得不到相同的 `name`、`length` 等元数据。

## 箭头函数与宿主回调遵循不同规则

前面几节讨论的都是普通函数。arrow function（箭头函数）没有自己的 `this`、`arguments`、`super` 和 `new.target` 绑定，不能用 `new` 构造，创建时也没有自有的 `prototype` 属性。后两点并非因果关系：可构造的绑定函数同样没有自有 `prototype`。箭头读取定义位置的 lexical `this`（词法 `this`）；`call`、`apply` 和 `bind` 可以传递实参或预填参数，但不能替换这个 `this`。需要让对象成为接收者时使用普通方法；需要词法 `this` 时才使用箭头函数。

~~~javascript
function makePanel(title) {
  return {
    title,
    read() { return this.title; },
    readArrow: label => this.title + ":" + label,
  };
}

const panel = makePanel.call({ title: "Outer" }, "Q4");
const arrowReader = panel.readArrow;
let arrowConstructError;
try {
  new arrowReader();
} catch (error) {
  arrowConstructError = error.name;
}
[
  panel.read(),
  panel.readArrow("direct"),
  panel.readArrow.call({ title: "Call" }, "call"),
  panel.readArrow.apply({ title: "Apply" }, ["apply"]),
  panel.readArrow.bind({ title: "Bind" }, "bind")(),
  Object.hasOwn(arrowReader, "prototype"),
  arrowConstructError,
];
// [
//   "Q4",
//   "Outer:direct", "Outer:call", "Outer:apply", "Outer:bind",
//   false, "TypeError",
// ]
~~~

`makePanel` 的这次调用通过 `call` 收到 `{ title: "Outer" }` 作为 `this`。`readArrow` 调用时访问的是 `makePanel` 这次调用的 `this`，其 `title` 值为 `"Outer"`，不是创建箭头时复制下来的一份值。之后的 `call`、`apply` 或 `bind` 都不能把箭头的 `this` 改成别的对象，但照常传入或预填 `"call"`、`"apply"`、`"bind"` 这些实参；`panel.read()` 是普通方法，才以 `panel` 为接收者。

除了调用表达式和 `call` 系列方法，host API（宿主 API）在调用回调时也会提供接收者，典型例子是 DOM event listener（事件监听器）。普通函数作监听器时，DOM 把注册该监听器的对象设为 `event.currentTarget`，并以它作为 `this`。事件冒泡时，它可能不同于真正被点击的 `event.target`：本例中前者是 `wrapper`，后者是按钮。`currentTarget` 只在监听器执行期间有值，派发结束后被重置为 `null`。箭头函数作监听器时仍保留外层 `this`，所以要通过事件对象显式读取：

~~~javascript
const button = document.createElement("button");
const wrapper = document.createElement("div");
wrapper.append(button);
document.body.append(wrapper);
const listenerResults = [];

wrapper.addEventListener("click", function (event) {
  const matches = this === event.currentTarget &&
    this === wrapper && event.target === button;
  listenerResults.push(matches);
});
wrapper.addEventListener("click", event => {
  const matches = event.currentTarget === wrapper &&
    event.target === button;
  listenerResults.push(matches);
});
button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
listenerResults;
// [true, true]
~~~

## 临时属性调用辅助函数只覆盖有限契约

理解了“方法调用以基底为 `this`”，就能自己实现一个简化版 `call`，这也是常见的练习题。思路是借用方法调用形式：先把函数放到接收者的一个临时 Symbol（符号值）键上，再以 `receiver[key](...)` 调用，最后删除这个键。箭头函数和 bound function 会忽略这个方法接收者；这个办法也只适合可扩展的普通对象或函数。辅助函数会拒绝非对象接收者；原生 `call`、`apply`、`bind` 则把给定值传给目标，再由目标按自身严格性决定是否转换。non-extensible object（不可扩展对象）、Proxy（代理对象）以及宿主对象可能让属性定义、读取或删除失败或产生额外行为。

~~~javascript
function callWithObjectReceiver(fn, receiver, ...args) {
  if (receiver === null ||
      (typeof receiver !== "object" && typeof receiver !== "function")) {
    throw new TypeError("This exercise requires an object receiver");
  }
  const key = Symbol("temporary call");
  Object.defineProperty(receiver, key, { value: fn, configurable: true });
  try {
    return receiver[key](...args);
  } finally {
    delete receiver[key];
  }
}

const receiver = { base: 10 };
function addToBase(amount) {
  "use strict";
  return this.base + amount;
}
const sum = callWithObjectReceiver(addToBase, receiver, 3);

function failAfterReceivingThis() {
  "use strict";
  if (this !== receiver) throw new TypeError("receiver was lost");
  throw new Error("target failed");
}
let failureName;
try {
  callWithObjectReceiver(failAfterReceivingThis, receiver);
} catch (error) {
  failureName = error.name;
}
[sum, failureName, Object.getOwnPropertySymbols(receiver).length];
// [13, "Error", 0]
~~~

即使目标抛错，`finally` 也会执行删除；最后一项结果为 `0`，说明临时 Symbol 已被清除。但若目标把临时键改成不可配置，非严格模式下删除返回 `false`，键会留下；严格模式下删除会抛 `TypeError`，并可能覆盖目标原先抛出的异常。下面归档的 `myApply` 练习用 `Array.prototype.slice.call` 复制类数组实参，遇到 `null` 或 `undefined` 时直接使用空列表，再委托给范围受限的 `myCall`；`countArgs.myApply(receiver, [])` 与 `countArgs.myApply(receiver, null)` 都令被调函数收到 0 个实参。

> [!info]- 归档练习：范围受限的 myCall 与 myApply
>
> 该练习用临时 Symbol 属性制造方法调用语法，只接受对象或函数接收者。apply 版本把 nullish（`null` 或 `undefined`）实参列表当作空列表，并复制其他 array-like（类数组）输入；它不模拟原始值接收者转换，也不完全复现原生 `apply` 对非对象实参列表的检查，且不能覆盖不可扩展对象和 Proxy 的所有行为。
>
> ~~~javascript
> Function.prototype.myCall = function (context, ...args) {
>   if (context === null ||
>       (typeof context !== "object" && typeof context !== "function")) {
>     throw new TypeError("This exercise requires an object receiver");
>   }
>   const key = Symbol("temporary call");
>   Object.defineProperty(context, key, {
>     value: this, configurable: true,
>   });
>   try {
>     return context[key](...args);
>   } finally {
>     delete context[key];
>   }
> };
>
> Function.prototype.myApply = function (context, args) {
>   const list = args === null || args === undefined
>     ? []
>     : Array.prototype.slice.call(args);
>   return this.myCall(context, ...list);
> };
>
> const receiver = { base: 10 };
> function sum(a, b) { return this.base + a + b; }
> function countArgs() { return arguments.length; }
>
> const zeroWithArray = countArgs.myApply(receiver, []);
> const zeroWithNull = countArgs.myApply(receiver, null);
> [sum.myCall(receiver, 1, 2), zeroWithArray, zeroWithNull];
> // [13, 0, 0]
> ~~~
>
> 唯一 Symbol 避免与既有字符串键冲突；`finally` 总会执行删除尝试，但目标若让临时键不可配置，属性就无法清除。向 `Function.prototype` 添加自定义方法会修改共享内置对象，因此这仅是机制练习，应用代码应使用内置方法。

**相关机制：** [JavaScript 对象如何查找属性？](./objects-functions-and-prototypes.md) 解释属性查找和 getter；[JavaScript 的 `new` 如何构造对象？](./construction-and-new.md) 说明绑定函数构造时为何忽略已绑定的 `this`。

> [!info]- 来源
>
> - 严格模式与普通调用的接收者绑定：[ECMAScript 2026 Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)、[Function Calls](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-function-calls) 和 [OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)（§10.2.1.2）。
>
> - 显式接收者与绑定函数：[ECMAScript Function.prototype.call](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.call)、[Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply) 和 [Function.prototype.bind](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.bind)；箭头函数：[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)。
>
> - DOM 普通事件监听器的接收者：[WHATWG DOM Event Listener Invocation](https://dom.spec.whatwg.org/#concept-event-listener-invoke)。
