# JavaScript 作用域与闭包如何保留状态？

**案例背景。** 网页用 `attachLogger(elementId, label)` 给按钮注册点击日志。注册函数早已返回，用户之后点击按钮时，callback（回调）为什么仍能读到当时传入的 `label`？答案涉及两个概念：scope（作用域）决定一个名称在哪里可见，closure（闭包）让函数在以后仍能访问它定义处的变量绑定。本章依次讲名称查找、声明何时初始化，再看几个延后执行的回调。

闭包只保留变量绑定，不保留 `this`。ordinary function（普通函数）的 `this` 由每次的调用形式提供；arrow function（箭头函数）没有自己的 `this`，读取定义处外层环境的 `this`。报表处理器和防抖包装函数两节会用到这条规则，完整规则见[JavaScript 函数的 `this` 值由什么决定？](./this-and-function-binding.md)。

以下代码块彼此独立。标为 HTML 的代码需要浏览器；计时器例子使用浏览器或 Node.js 提供的计时 API。

## 名称查找沿函数的定义位置进行

代码读取一个标识符时，JavaScript 先在当前 lexical environment（词法环境）里找对应的 binding（绑定，即名称与值的关联）；找不到才去外层环境，逐层向外。关键在于“外层”指函数**定义**时所在的环境，而不是调用它的地方。用下面的代码走一遍：

1. 每次调用 `outer`，函数体执行前会先做声明实例化：建立 `inner` 的绑定并创建函数对象，函数对象的内部槽 `[[Environment]]` 记下这次 `outer` 调用的词法环境。
2. 然后函数体执行，初始化 `label = "outer"`，返回 `inner`。`outer` 调用结束了，但返回的函数仍引用着那份环境，所以它不会被回收。
3. `callFromElsewhere` 调用这个返回值时，才为 `inner` 新建本次调用的局部环境，其外层指向第 1 步记下的环境。

调用者 `callFromElsewhere` 自己的局部环境（其中也有一个 `label`）不会插进这条查找链。调用者能影响的只有实参，以及普通函数的 `this`。

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

图中的环境节点是语言规范描述名称查找用的抽象，不代表引擎真的按这个形状分配对象。规范里还有两个相关概念：execution context（执行上下文）描述正在执行的脚本或函数及其状态，environment record（环境记录）保存绑定并提供查找操作。调用栈回答“哪些调用还没返回”，词法链回答“名称按什么顺序解析”；两者相关，但不是同一条链，上例中调用栈里有 `callFromElsewhere`，词法链里却没有。

## 声明方式决定绑定范围与初始化时机

上一节的查找过程假设绑定已经存在且有值。但绑定建在哪个环境、何时被初始化，取决于声明方式。`var`、`let`、`const` 的差异不只是“函数级还是块级”，初始化时机同样决定读取结果。

| 声明 | 绑定范围 | 初始化时机 | 重复声明与重新赋值 |
| --- | --- | --- | --- |
| `var` | 所在函数的作用域；在脚本或模块顶层声明时属于各自的顶层范围 | 进入作用域时（声明实例化）就初始化为 `undefined`（与形参同名时沿用形参值）；`= 值` 部分要等执行到声明那一行才运行 | 兼容的 `var` 声明可重复；可重新赋值 |
| `let` | 所在词法作用域，如代码块或脚本、模块顶层 | 进入作用域先建立未初始化绑定；从进入作用域到声明初始化完成是 temporal dead zone（暂时性死区）；无初始化式时到声明处初始化为 `undefined` | 同一词法作用域不能重复声明；可重新赋值 |
| `const` | 所在词法作用域，如代码块或脚本、模块顶层 | 与 `let` 一样先建立未初始化绑定；从进入作用域到声明初始化完成是暂时性死区；通常必须写初始化式，`for...in` / `for...of` 头部例外 | 同一词法作用域不能重复声明；初始化后不能重新绑定 |

`if` 代码块不会为 `var` 创建新绑定，所以即使声明写在条件块里，下例函数开头读到的也是已初始化为 `undefined` 的同一个 `status`。`let` 和 `const` 则在进入代码块时就有了绑定，但初始化前读取会抛出 `ReferenceError`。下例块内的 `let count` 从块开头起就遮蔽了外层 `count`；查找遇到这个尚未初始化的内层绑定就抛错，不会跳过它去读外层的 `0`。离开代码块后，外层 `count` 仍是 `0`。最后，`const` 只禁止给变量名重新赋值，不会冻结它指向的对象。

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

表中说的“脚本或模块顶层”在不同宿主里含义不同。浏览器经典脚本、浏览器模块、Node.js CommonJS 和 Node.js ESM 都能声明顶层变量，但外层环境各不相同；top-level `this`（顶层 `this`）也不总是全局对象。要在这些环境里统一拿到当前 Realm（执行域）的全局对象，标准写法是 `globalThis`。

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

有了名称查找和绑定初始化，就能准确地说闭包保留的是什么：函数以后仍能访问它定义处可见的**绑定**，而绑定的值可以继续变化。每次调用 `makeCounter(start)` 都会建立参数 `start` 和独立的局部 `value` 绑定。执行到 `let value = start` 时，用 `start` 的值初始化 `value`。返回的函数保留对这份 `value` 的访问。`value++` 先读取旧值，再把加一后的值写回原绑定，然后以旧值作为表达式结果交给调用者。因此第一次调用将 `value` 从 `10` 写成 `11` 并返回 `10`；第二次读取同一绑定时从 `11` 开始。它不是创建时复制下来的快照。

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

实际代码常把闭包状态和 `this` 混在一起用。下面的报表服务用工厂函数 `makeReportHandler(tag)` 创建处理器：返回的普通函数通过闭包继续访问 `tag` 和计数器 `calls`，每次调用都更新同一份 `calls`；但闭包不会顺带捕获 `this`。先看 `service.onReport(...)`：成员调用以 `service` 为接收者，所以 `onReport` 里的 `this` 是 `service`。函数体又执行 `this.format(...)` 这个成员调用，于是 `format` 里的 `this` 仍是 `service`。

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

既然闭包保留的是绑定而不是值，在循环里保存回调、稍后再调用时，关键就在于各个回调读的是同一份绑定，还是每轮各自的一份。`var` 声明的循环变量在整个函数（顶层代码中则是脚本或模块）里只有一份绑定，每轮只是给它重新赋值。带 `let` 的 `for` 循环则为每一轮提供新绑定：第一轮体读取 `j = 0`，回调记住这份绑定；循环体结束后，语言先把当前值复制到下一轮的新绑定，再在新绑定上执行 `j++`。因此下一轮体是 `1`，第一份回调仍读旧的 `0`。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

[fromVar.map(fn => fn()), fromLet.map(fn => fn())];
// [[3, 3, 3], [0, 1, 2]]
~~~

在没有 `let` 的旧代码里，常用 Immediately Invoked Function Expression（IIFE，立即调用函数表达式）每轮调用一次函数，借函数参数为每轮新建一份绑定。回调读取各自的 `capturedIndex`，所以得到和 `let` 循环相同的结果。

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

工厂函数可以把一次调用的参数绑定留在闭包里，返回一个更专用的函数。下例 `add(5)` 返回后，`x` 绑定仍可读；它之后不再被赋值，所以看起来像“捕获了值 5”——这只是因为没人改它。同一机制也让延后执行的回调读到注册时的参数，这正是开头 `attachLogger` 问题的答案。

~~~javascript
function add(x) {
  return function (y) {
    return x + y;
  };
}

const addFive = add(5);
addFive(3); // 8
~~~

下面两段 DOM 代码都要在页面 `<body>` 已存在后运行。`attachLogger` 注册监听器后就返回了；真实场景中用户稍后点击，这里用 `dispatchEvent` 模拟一次点击，它同步派发事件，监听器在 `dispatchEvent` 返回前运行。箭头回调读取的是 `attachLogger` 那次调用的 `label` 参数绑定，该绑定之后没有被重新赋值。

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

`requestAnimationFrame` 的 animation frame（动画帧）回调同样延后运行。每次调用 `animate` 都会建立 `element`、`from`、`to`、`duration` 和 `start` 绑定，之后都不再赋值。`performance.now()` 返回毫秒时间戳，所以 `duration` 也以毫秒计。之后每一帧的 `update` 都读取同一次 `animate` 调用的这些绑定，算出当前位置，再决定是否请求下一帧。

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

上面的回调只读取不变的绑定。闭包也能保存需要跨调用更新的状态，典型例子是 debounce（防抖）和 throttle（节流）：防抖在连续调用停下、静默一段时间后，只执行最后一次；节流限制执行频率。两者都由返回的包装函数通过闭包保存状态，但保存的内容和更新时机不同。执行时机可以选 leading edge（首沿，一串调用的开头）、trailing edge（尾沿，一串调用结束后）或两者都要；下面分别实现仅尾沿的防抖和仅首沿的节流。示例中 `wait` 和 `interval` 都是正整数毫秒数。

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

`timer` 属于某一次 `debounce(fn, wait)` 调用，被返回的 `debounced` 在多次调用之间共享。每次调用 `debounced(...args)` 都新建本次的 `args` 和 `receiver` 绑定；旧计时器被清除后，新计时器的箭头回调读到的就是本次的接收者和参数，所以静默期结束时只执行最后一组输入。`.cancel()` 只撤销尚未触发的计时器。`throttleLeading` 用 `performance.now()` 这一单调时钟计算间隔，系统校时不会影响差值；`lastCallAt` 初值用 `null` 表示“还没有执行过”，这样即使时钟读数恰好是 `0`，第一次调用也会立即执行；差值正好等于 `interval` 时也放行。

下面用一条合成时间线对比两者：防抖等待时间和节流间隔都是 `100ms`；`debouncedSearch`、`throttledSearch` 分别包装同一个搜索函数，该函数记下接收者（`pageA`、`pageB`、`pageC` 代表不同接收者）和搜索词。每一行把相同输入同时交给两个包装函数。表中时刻是按理想时钟推演的逻辑时间，不是实测结果。

| 理想时刻 | 防抖包装函数收到的输入与状态 | 首沿节流包装函数收到的输入与结果 |
| ---: | --- | --- |
| `0ms` | `debouncedSearch.call(pageA, "A")`：设置 `100ms` 等待 | `throttledSearch.call(pageA, "A")`：立即以 `pageA` 和 `"A"` 执行，记录上次通过时刻 `0` |
| `40ms` | `debouncedSearch.call(pageB, "B")`：取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageB, "B")`：丢弃，距离上次通过 `40ms` |
| `110ms` | `debouncedSearch.call(pageC, "C")`：再次取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageC, "C")`：执行，距上次通过 `110ms`，超过间隔 |
| 自 `210ms` 起 | 若无新调用，timer 以 `pageC` 和 `"C"` 执行 | 没有新调用 |

真实时间会偏离上表。`setTimeout` 的 delay（延迟）只是交给宿主去安排计时任务，不保证回调在精确时刻触发：在 Node.js 26.13.0 中用高分辨率时钟实测，有时会观察到比传入值略短的等待。Node.js 还会把小于 `1ms` 或大于 `2147483647ms` 的 delay 当作 `1ms`，并截掉非整数的小数部分（Node.js 26.13 文档）；这是 Node 的规则，不能套用到所有宿主。控件销毁时应移除事件监听器并调用 `.cancel()`，它只能撤销尚未触发的防抖回调。如果回调已经发出 `fetch`，还可以调用该请求所用 AbortController（中止控制器）的 `abort()`；这会取消客户端这一侧的请求，但撤不回服务端已经收到并开始处理的工作。

节流实现先写入 `lastCallAt` 再调用目标函数，所以目标同步重入时会看到这次调用的时间：若重入时仍未经过间隔，会被挡下；若目标同步耗时已达到或超过间隔才重入，重入会通过。`interval` 为 `0` 时该判断不会限制同步重入；本节的节流结论限于正间隔。

## 闭包生命周期取决于可达性

前面反复提到“绑定在外层调用返回后仍可访问”，这会不会造成内存泄漏？语言保证的只是行为：返回的函数仍能读到它用到的绑定；引擎不必把所有局部变量永久留在一个环境对象里，通常只保留闭包实际可能用到的部分。数据能否被回收取决于可达性：长期存在的事件监听器会让它的闭包和闭包引用的数据一直可达，所以控件销毁时要移除监听器和其他引用。循环引用本身不等于泄漏，要看运行中的程序是否还能沿引用到达这些数据。

**相关机制：** [JavaScript 对象如何查找属性并组织成员？](./objects-functions-and-prototypes.md) 将同一报表处理器放入服务实例，并说明 `format` 如何从原型查找；[JavaScript 函数的 `this` 值由什么决定？](./this-and-function-binding.md) 解释调用形式怎样提供接收者。

> [!info]- 来源
> - 词法环境、环境记录和标识符查找：[ECMAScript 2026 Execution Contexts](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-execution-contexts)、[Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)、[GetIdentifierReference](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getidentifierreference)、[NewFunctionEnvironment](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-newfunctionenvironment)。
> - `var`、`let`、`const` 的绑定建立、初始化和声明限制：[ECMAScript 2026 FunctionDeclarationInstantiation](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-functiondeclarationinstantiation)、[Source Text Module Record InitializeEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html#sec-source-text-module-record-initialize-environment)、[Let and Const Declarations](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-let-and-const-declarations)、[Variable Statement](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-variable-statement)。
> - 函数对象保留定义处环境，以及普通函数调用与箭头函数 `this` 的区别：[ECMAScript 2026 Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)、[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)、[EvaluateCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatecall)、[OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)。
> - `for (let...)` 的每轮绑定复制与更新顺序：[ECMAScript 2026 ForBodyEvaluation](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-forbodyevaluation)、[CreatePerIterationEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-createperiterationenvironment)。
> - 浏览器经典脚本、模块脚本、DOM 点击与 Web Worker 全局环境：[WHATWG HTML The `script` element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)、[Document.body](https://html.spec.whatwg.org/multipage/dom.html#dom-document-body)、[dispatchEvent](https://dom.spec.whatwg.org/#dom-eventtarget-dispatchevent)、[The global scope](https://html.spec.whatwg.org/multipage/workers.html#the-global-scope)（Living Standard，核对日期 2026-11-12）；Node.js [CommonJS module wrapper](https://nodejs.org/api/modules.html#the-module-wrapper) 与 [ECMAScript modules](https://nodejs.org/api/esm.html)（官方文档 26.13.1，实际回放 Node.js 26.13.0）。
> - 动画帧、计时器时限和延迟任务：[WHATWG HTML `requestAnimationFrame`](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#dom-animationframeprovider-requestanimationframe)、[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)（Living Standard，核对日期 2026-11-12）、[Node.js Timers: `setTimeout`](https://nodejs.org/api/timers.html#settimeoutcallback-delay-args)（官方文档 26.13.1）；单调时间戳：[W3C High Resolution Time `performance.now()`](https://www.w3.org/TR/hr-time-3/#dom-performance-now)（Level 3，核对日期 2026-11-12）；`position: relative` 的偏移语义：[CSS Positioned Layout Level 3](https://drafts.csswg.org/css-position-3/#valdef-position-relative)（Editor’s Draft，2026-05-14）。
> - 监听器注册与请求取消边界：[WHATWG DOM `addEventListener`](https://dom.spec.whatwg.org/#dom-eventtarget-addeventlistener)、[Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)、[Fetch Standard Aborting a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，核对日期 2026-11-12。
