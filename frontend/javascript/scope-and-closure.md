# JavaScript 作用域与闭包如何保留状态？

**案例背景。** 网页用 `attachLogger` 为按钮注册点击日志；注册函数返回后，用户再点击按钮，callback（回调）为什么仍能读到当时传入的 `label`？scope（作用域）决定一个名称在哪里可见，closure（闭包）让函数以后仍能访问它定义处的绑定。本章沿名称查找、声明初始化和几个延后执行的回调追踪这条路径。ordinary function（普通函数）的 `this` 由调用形式提供；arrow function（箭头函数）没有自己的 `this` 绑定，而是从定义处的外层环境读取。本章的接收者规则只针对普通函数；更多形式见[JavaScript 函数的 `this` 值由什么决定？](./this-and-function-binding.md)。

以下代码块彼此独立。标为 HTML 的代码需要浏览器；计时器例子使用浏览器或 Node.js 提供的计时 API。

## 名称查找沿函数的定义位置进行

当代码读取标识符时，JavaScript 从当前 lexical environment（词法环境）查找对应的 binding（绑定）；当前环境没有该名称才沿外层环境继续。每次调用 `outer` 时，函数体开始执行前的声明实例化会建立 `inner` 的绑定并创建函数对象；它的 `[[Environment]]` 指向这次 `outer` 调用的词法环境。接着函数体才执行，初始化 `label` 并返回这个函数。即使本次 `outer` 调用结束，返回的函数仍能让那份环境可达。`callFromElsewhere` 调用返回值时，才建立 `inner` 本次调用的局部环境。调用者的局部环境不会插入函数定义时建立的查找链；普通函数调用者能提供实参和接收者 `this`，箭头函数则从词法外层读取 `this`。

下面的图只展示 `outer` 已返回、`inner` 又被调用之后的名称查找。`inner` 的局部环境里有 `detail`，没有 `label`；因此查找沿函数对象保留的那次 `outer` 环境继续，而不是沿调用者 `callFromElsewhere` 的局部环境继续。

~~~mermaid
flowchart TB
  Q["inner 读取 label"] -->|先查当前环境| I["inner 的词法环境<br/>有 detail；没有 label"]
  I -->|未找到 label，沿定义时的外层环境查找| O["outer 本次调用的环境<br/>label = outer；命中并停止"]
~~~

~~~javascript
const label = "global";

function outer() {
  const read = inner;
  const label = "outer";
  function inner() {
    const detail = "inner";
    return [label, detail];
  }
  return read;
}

function callFromElsewhere() {
  const label = "caller";
  const read = outer();
  return read();
}

callFromElsewhere(); // ["outer", "inner"]
~~~

这里的环境节点是语言规范描述名称查找的抽象，不表示引擎必须按相同形状分配 JavaScript 对象。execution context（执行上下文）描述当前正在执行的脚本或函数及其状态；environment record（环境记录）描述绑定与名称查找操作。调用栈告诉我们哪些调用尚未返回，词法链告诉我们一个名称按什么顺序解析；两者相关，但不是同一条链。

## 声明方式决定绑定范围与初始化时机

`var`、`let`、`const` 的差异不只是“函数级或块级”：声明先在哪个环境建立绑定、什么时候初始化，也会决定读取结果。

| 声明 | 绑定范围 | 初始化时机 | 重复声明与重新赋值 |
| --- | --- | --- | --- |
| `var` | 普通函数作用域；脚本或模块的顶层也有各自范围 | 本节没有同名形参的例子里，声明实例化把新变量绑定初始化为 `undefined`；声明中的初始化式到代码执行至声明处才运行 | 兼容的 `var` 声明可重复；可重新赋值 |
| `let` | 所在词法作用域，如代码块或脚本、模块顶层 | 进入作用域先建立未初始化绑定；从进入作用域到声明初始化完成是 temporal dead zone（暂时性死区）；无初始化式时到声明处初始化为 `undefined` | 同一词法作用域不能重复声明；可重新赋值 |
| `const` | 所在词法作用域，如代码块或脚本、模块顶层 | 与 `let` 一样先建立未初始化绑定；从进入作用域到声明初始化完成是暂时性死区；通常必须写初始化式，`for...in` / `for...of` 头部例外 | 同一词法作用域不能重复声明；初始化后不能重新绑定 |

`if` 代码块不会为 `var` 创建新绑定，因此即使声明写在条件块里，函数开头读取的也是已初始化为 `undefined` 的同一个 `status`。`let` 和 `const` 进入代码块时已经有绑定，但初始化前读取会抛出 `ReferenceError`。下例的内层 `let count` 已经遮蔽外层 `count`；查找遇到这个尚未初始化的内层绑定就抛错，不会跳过它再去读外层的 `0`。离开代码块后，外层 `count` 仍为 `0`。`const` 限制变量名重新绑定，不会冻结它指向的对象。
`for...in` 和 `for...of` 头部的 `const` 由每轮枚举或迭代取出的值初始化；普通 `const` 声明则必须显式写初始化式。

~~~javascript
function readBeforeAssignment() {
  console.log(status); // undefined
  if (true) {
    var status = "ready";
  }
  return status; // "ready"
}

let count = 0;
let tdzError;
{
  try {
    count;
  } catch (error) {
    tdzError = error.name;
  }
  let count = 1;
}

const options = { theme: "light" };
options.theme = "dark";
let reassignmentError;
try {
  options = {};
} catch (error) {
  reassignmentError = error.name;
}
const statusAfterReturn = readBeforeAssignment();
[statusAfterReturn, tdzError, count, options.theme, reassignmentError];
// ["ready", "ReferenceError", 0, "dark", "TypeError"]
~~~

兼容的 `var` 名称可以在同一变量作用域重复声明，但不能与同一作用域内冲突的词法声明混用；重复声明同名 `let` 或 `const` 是语法错误。绑定不需要重新赋值时通常用 `const`，需要重新赋值时用 `let`；维护依赖函数作用域的旧代码时才需要 `var`。

### “顶层”取决于宿主怎样执行代码

浏览器经典脚本、浏览器模块、Node.js CommonJS 和 Node.js ESM 都能声明顶层变量，但它们处在不同的外层环境中。top-level `this`（顶层 `this`）也不总是全局对象；`globalThis` 才是跨这些调用位置访问当前 Realm（执行域）全局 `this` 值的标准入口。

| 运行方式 | 顶层声明 | 顶层 `this` | 宿主全局入口 |
| --- | --- | --- | --- |
| 浏览器 classic script（经典脚本，`<script>` 不写 `type="module"`） | `var` 通常成为 `window` 属性；`let` / `const` 是 global lexical binding（全局词法绑定） | 当前全局 `this` 值，即 `window` | `window`、`globalThis` |
| 浏览器 module script（模块脚本） | `var`、`let`、`const` 都是 module-local binding（模块局部绑定） | `undefined` | `globalThis`；窗口页面另有 `window` |
| Node.js CommonJS（Node.js 模块格式，简称 CJS） | `var`、`let`、`const` 都是 wrapper-local binding（包装函数内的局部绑定） | 包装函数收到的初始 `exports` 对象 | `globalThis` |
| Node.js ECMAScript module（ES 模块，简称 ESM） | `var`、`let`、`const` 都是 module-local binding | `undefined` | `globalThis` |

浏览器主线程的 `window` 代表窗口全局；Web Worker（Web 工作线程）有自己的全局环境，可用 `self` 或 `globalThis`，没有 `window`。模块规则与 Node.js 包格式及互操作的更多差异见[ECMAScript 模块与 CommonJS 在语法、加载和运行时有什么不同？](./modules-and-host-boundaries.md)。

~~~html
<script>
  var scriptValue = "global object property";
  let scriptBinding = "global lexical binding";

  const browserScriptResults = [
    window.scriptValue,
    window.scriptBinding,
    scriptBinding,
    this === globalThis,
  ];
  // ["global object property", undefined, "global lexical binding", true]
</script>
~~~

## 闭包保留绑定，而不是冻结快照

closure（闭包）使函数代码以后仍能访问它定义处可见的绑定。每次调用 `makeCounter(start)` 都会建立参数 `start` 和独立的局部 `value` 绑定。执行到 `let value = start` 时，用 `start` 的值初始化 `value`。返回的函数保留对这份 `value` 的访问。`value++` 先读取旧值，再把加一后的值写回原绑定，然后以旧值作为表达式结果交给调用者。因此第一次调用将 `value` 从 `10` 写成 `11` 并返回 `10`；第二次读取同一绑定时从 `11` 开始。它不是创建时复制下来的快照。

~~~javascript
function makeCounter(start) {
  let value = start;
  return () => value++;
}

const first = makeCounter(10);
const second = makeCounter(-2);
const firstResults = [first(), first(), first()];
const secondResults = [second(), second(), second()];
[firstResults, secondResults];
// [[10, 11, 12], [-2, -1, 0]]
~~~

同一次调用也可以返回多个共享状态的函数。`increment`、`decrement` 和 `reset` 都访问同一份 `current`；`reset` 把该绑定改回输入的初值，不会创建一个新的计数器。

~~~javascript
function createCounter(init) {
  let current = init;
  return {
    increment() { return ++current; },
    decrement() { return --current; },
    reset() { return current = init; },
  };
}

const counter = createCounter(5);
[counter.increment(), counter.reset(), counter.decrement()]; // [6, 5, 4]
~~~

## 报表处理器把闭包状态与调用时接收者结合起来

报表服务创建处理器时，工厂函数把 `tag` 和 `calls` 两个词法绑定交给返回的普通函数继续访问。每次方法调用都更新同一份 `calls`；闭包不会顺带捕获普通函数的 `this`。先看 `service.onReport(...)`：成员调用以 `service` 为接收者，所以 `onReport` 里的 `this` 是 `service`。函数体又执行 `this.format(...)` 这个成员调用，于是 `format` 里的 `this` 仍是 `service`。

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
    return `${this.prefix}/${tag}: ${report.title} #${sequence}`;
  },
  onReport: makeReportHandler("daily"),
};

const firstReport = service.onReport({ title: "Q4" });
const secondReport = service.onReport({ title: "Q4" });
const { onReport } = service;
let bareCallError;
try {
  onReport({ title: "Q4" });
} catch (error) {
  bareCallError = error.name;
}
const reportAfterBareCall = service.onReport({ title: "Q4" });
[firstReport, secondReport, bareCallError, reportAfterBareCall];
// [
//   "Sales/daily: Q4 #1",
//   "Sales/daily: Q4 #2",
//   "TypeError",
//   "Sales/daily: Q4 #4",
// ]
~~~

裸调时，`onReport` 的严格模式使 `this` 为 `undefined`。函数先执行 `calls += 1`，再读 `this.format` 才抛出 `TypeError`；因此下一次正常服务调用是 `#4`。`tag`、`calls` 来自函数定义时的词法环境；普通函数的 `this` 则由每次调用形式分别提供。箭头函数没有自己的 `this`；若此处把处理器改写成箭头，它会读定义它的外层 `this`，不再随 `service.onReport(...)` 改变。

## 循环回调需要符合预期数量的绑定

循环把回调保存起来、稍后才调用时，关键是每个回调最后读取的是同一份绑定，还是每轮各自的绑定。`var` 在循环里重复赋值同一份函数作用域绑定；顶层示例里的 `var` 归脚本/模块环境，放进普通函数时则归函数环境。带 `let` 的 `for` 循环会为每轮提供新的绑定：第一轮体读取 `j = 0`，回调记住这份绑定；循环体结束后，语言先把当前值复制到下一轮的新绑定，再在新绑定上执行 `j++`。因此下一轮体是 `1`，第一份回调仍读旧的 `0`。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

[fromVar.map(fn => fn()), fromLet.map(fn => fn())];
// [[3, 3, 3], [0, 1, 2]]
~~~

旧代码也能用 Immediately Invoked Function Expression（IIFE，立即调用函数表达式）为每轮新建一个函数调用参数绑定。回调读取各自的 `capturedIndex`，所以得到和 `let` 循环相同的结果。

~~~javascript
const callbacks = [];
for (var index = 0; index < 3; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}
callbacks.map(fn => fn()); // [0, 1, 2]
~~~

## 工厂函数专门化行为，回调保留捕获值

工厂可以把一次调用建立的参数绑定保存在闭包里，返回一个更专用的函数。本例的 `x` 绑定在工厂返回后仍可读，且后续不再赋值；这正是“捕获值”恰好保持不变的条件。同一机制也让延后执行的 callback（回调）读取注册时的参数绑定。

~~~javascript
function add(x) {
  return function (y) {
    return x + y;
  };
}

const addFive = add(5);
addFive(3); // 8
~~~

下面两段 DOM 代码都要在浏览器页面的 `<body>` 已经存在后运行。注册监听器后，`attachLogger` 已经返回；真实用户可以之后点击按钮。这里用 `dispatchEvent` 在注册函数返回后同步派发事件，监听器会在 `dispatchEvent` 返回前运行。箭头回调读取 `attachLogger` 那次调用创建的 `label` 参数绑定；该绑定之后不再赋值。

~~~javascript
function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener("click", () => {
    console.log("Clicked: " + label);
  });
}

const loggerButton = document.createElement("button");
loggerButton.id = "btn1";
document.body.append(loggerButton);
attachLogger("btn1", "primary");
loggerButton.dispatchEvent(new MouseEvent("click"));
// 控制台输出："Clicked: primary"
~~~

animation frame（动画帧）回调也会延后运行。`animate` 每次调用都会建立 `start`、`element`、`from`、`to` 和 `duration` 绑定；这些参数和 `start` 随后不再赋值。`performance.now()` 返回毫秒时间戳，因此 `duration` 也以毫秒计。后续每一帧的 `update` 都从同一次 `animate` 调用读取它们，算出当前位置，再决定是否请求下一帧。代码也必须等页面 `<body>` 已经存在后运行。

~~~javascript
function animate(element, from, to, duration) {
  const start = performance.now();

  function update() {
    const elapsed = performance.now() - start;
    const progress = Math.min(elapsed / duration, 1);
    const value = from + (to - from) * progress;
    element.style.left = value + "px";

    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

const animatedElement = document.createElement("div");
animatedElement.textContent = "报表已更新";
animatedElement.style.position = "relative";
document.body.append(animatedElement);
animate(animatedElement, 0, 100, 1000); // duration 必须大于 0
~~~

当进度到达 `1` 时，`style.left` 最终为 `100px`，并且不再请求下一帧。`left` 对普通静态定位元素不起偏移作用；本例设置 `position: relative`，只移动绘制位置，不移除元素在正常流中占据的空间。

## 定时回调怎样用闭包保留调度状态

debounce（防抖）在一段静默时间后运行最后一次调用；throttle（节流）则限制调用频率。两者都让返回函数通过闭包保存跨调用状态，但保存内容和更新时机不同。库和自定义包装函数可以选择 leading-edge（首沿）、trailing-edge（尾沿）或两者兼有；下面的实现分别是 trailing-only debounce（仅尾沿防抖）和 leading-only throttle（仅首沿节流）。示例把 `wait` 和 `interval` 设为正整数毫秒数；时间表采用理想时钟推演，不代表任一宿主的实际触发测量或保证。节流的推论只针对正间隔。

~~~javascript
function debounce(fn, wait) {
  let timer;

  function debounced(...args) {
    const receiver = this;
    clearTimeout(timer);
    timer = setTimeout(() => {
      timer = undefined;
      fn.apply(receiver, args);
    }, wait);
  }

  debounced.cancel = function () {
    clearTimeout(timer);
    timer = undefined;
  };

  return debounced;
}

function throttleLeading(fn, interval) {
  let lastCallAt = null;

  return function (...args) {
    const now = performance.now();
    if (lastCallAt !== null && now - lastCallAt < interval) return;

    lastCallAt = now;
    return fn.apply(this, args);
  };
}
~~~

`timer` 来自某一次 `debounce(fn, wait)` 调用，并由返回的 `debounced` 闭包跨调用共享。每次进入 `debounced(...args)` 时都会新建这一轮的 `args` 绑定与 `receiver` 绑定；旧计时器被清除后，新计时器的箭头回调访问的就是这次调用的接收者和参数。因而静默期结束时只执行最后一组输入。`.cancel()` 只撤销尚未触发的 timer。`throttleLeading` 用 `performance.now()` 的单调时钟计算间隔，系统校时不会改变这段差值；用 `null` 表示“尚无上次调用时间”，因此即使计时器初始读数为 `0`，第一次调用也会立即通过；到达间隔边界时，差值等于 `interval`，本次也会通过。

下面是理想时钟的合成时间线：等待值与节流间隔都设为 `100ms`，`pageA`、`pageB`、`pageC` 表示不同接收者，包装目标把接收者页面名和搜索词记下来。每一行同时把相同输入交给两个包装函数；这些时刻是便于推演的逻辑时间，不是宿主时钟的测量结果。

| 理想时刻 | 防抖包装函数收到的输入与状态 | 首沿节流包装函数收到的输入与结果 |
| ---: | --- | --- |
| `0ms` | `debouncedSearch.call(pageA, "A")`：设置 `100ms` 等待 | `throttledSearch.call(pageA, "A")`：立即以 `pageA` 和 `"A"` 执行，记录上次通过时刻 `0` |
| `40ms` | `debouncedSearch.call(pageB, "B")`：取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageB, "B")`：丢弃，距离上次通过 `40ms` |
| `110ms` | `debouncedSearch.call(pageC, "C")`：再次取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageC, "C")`：执行，距上次通过 `110ms`，超过间隔 |
| 自 `210ms` 起 | 若无新调用，timer 以 `pageC` 和 `"C"` 执行 | 没有新调用 |

`setTimeout` 接收 delay（延迟）并由宿主安排计时器任务；它不保证回调会在指定的精确时刻触发。隔离复现中，Node.js 26.13.0 的高分辨率时间实测有时观察到略短于传入值的等待，因此上表采用理想时钟，不把时间点当作实际保证。Node.js 26.13 将小于 `1ms` 或大于 `2147483647ms` 的 delay 改为 `1ms`，并截去非整数小数部分；这是 Node 的边界，不可套用为所有宿主的规则。控件销毁时应移除事件监听器并调用 `.cancel()`；它只移除尚未触发的防抖 callback。如果 callback 已经启动 `fetch`，还可以调用该请求 AbortController（中止控制器）的 `abort()`，这会取消客户端操作，但不会撤回服务端已经收到并开始处理的工作。

节流实现先写入 `lastCallAt` 再调用目标函数，所以目标同步重入时会看到这次调用的时间：若重入时仍未经过间隔，会被挡下；若目标同步耗时已达到或超过间隔才重入，重入会通过。`interval` 为 `0` 时该判断不会限制同步重入；本节的节流结论限于正间隔。

## 闭包生命周期取决于可达性

外层调用返回后，返回函数仍可观察它使用的绑定，这是行为保证；这不表示引擎必须把所有局部变量永久装进一个环境对象。长期存在的事件监听器可以让闭包与数据继续可达，控件销毁时应移除监听器和其他引用。循环引用本身不等于内存泄漏；需要判断的是活动程序仍能否沿引用到达这些数据。

**相关机制：** [JavaScript 对象如何查找属性并组织成员？](./objects-functions-and-prototypes.md) 将同一报表处理器放入服务实例，并说明 `format` 如何从原型查找；[JavaScript 函数的 `this` 值由什么决定？](./this-and-function-binding.md) 解释调用形式怎样提供接收者。

> [!info]- 来源
> - 词法环境、环境记录和标识符查找：[ECMAScript 2026 Execution Contexts](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-execution-contexts)、[Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)、[GetIdentifierReference](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getidentifierreference)、[NewFunctionEnvironment](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-newfunctionenvironment)。
> - `var`、`let`、`const` 的绑定建立、初始化和声明限制：[ECMAScript 2026 FunctionDeclarationInstantiation](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-functiondeclarationinstantiation)、[Source Text Module Record InitializeEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html#sec-source-text-module-record-initialize-environment)、[Let and Const Declarations](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-let-and-const-declarations)、[Variable Statement](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-variable-statement)。
> - 函数对象保留定义处环境，以及普通函数调用与箭头函数 `this` 的区别：[ECMAScript 2026 Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)、[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)、[EvaluateCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatecall)、[OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)。
> - `for (let...)` 的每轮绑定复制与更新顺序：[ECMAScript 2026 ForBodyEvaluation](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-forbodyevaluation)、[CreatePerIterationEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-createperiterationenvironment)。
> - 浏览器经典脚本、模块脚本、DOM 点击与 Web Worker 全局环境：[WHATWG HTML The `script` element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)、[Document.body](https://html.spec.whatwg.org/multipage/dom.html#dom-document-body)、[dispatchEvent](https://dom.spec.whatwg.org/#dom-eventtarget-dispatchevent)、[The global scope](https://html.spec.whatwg.org/multipage/workers.html#the-global-scope)（Living Standard，核对日期 2026-11-12）；Node.js [CommonJS module wrapper](https://nodejs.org/api/modules.html#the-module-wrapper) 与 [ECMAScript modules](https://nodejs.org/api/esm.html)（官方文档 26.13.1，实际回放 Node.js 26.13.0）。
> - 动画帧、计时器时限和延迟任务：[WHATWG HTML `requestAnimationFrame`](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#dom-animationframeprovider-requestanimationframe)、[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)（Living Standard，核对日期 2026-11-12）、[Node.js Timers: `setTimeout`](https://nodejs.org/api/timers.html#settimeoutcallback-delay-args)（官方文档 26.13.1）；单调时间戳：[W3C High Resolution Time `performance.now()`](https://www.w3.org/TR/hr-time-3/#dom-performance-now)（Level 3，核对日期 2026-11-12）；`position: relative` 的偏移语义：[CSS Positioned Layout Level 3](https://drafts.csswg.org/css-position-3/#valdef-position-relative)（Editor’s Draft，2026-05-14）。
> - 监听器注册与请求取消边界：[WHATWG DOM `addEventListener`](https://dom.spec.whatwg.org/#dom-eventtarget-addeventlistener)、[Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)、[Fetch Standard Aborting a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，核对日期 2026-11-12。
