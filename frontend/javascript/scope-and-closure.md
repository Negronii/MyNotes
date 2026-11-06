# JavaScript 作用域与闭包如何保留状态？

标识符查找从当前 lexical environment（词法环境）开始，沿函数定义处的环境向外进行；调用者的局部变量不会插入这条链。closure（闭包）让函数在外层调用结束后仍可读取自己使用的 name binding（名称绑定）及其当前值。先看名称查找路径，再追踪闭包状态如何与调用时的 this 分开。

## 名称查找沿函数的定义位置进行

函数不会查找调用者的局部变量。它先查自己的词法环境，再查定义位置外层的环境。调用者仍可传入参数和 `this`，但不会因此成为被调用函数的词法外层作用域。

~~~javascript
const label = "global";

function outer() {
  const label = "outer";
  function inner() {
    const detail = "inner";
    return [label, detail];
  }
  return inner;
}

function callFromElsewhere() {
  const label = "caller";
  return outer()();
}

callFromElsewhere(); // ["outer", "inner"]
~~~

`inner` 先找到自己的 `detail`，再找到 `outer` 的 `label`；调用者的 `label` 不在这条查找链上。规范用 execution context（执行上下文）和 environment record（环境记录）描述这套行为，引擎不必创建名称和结构完全相同的对象。

## 声明方式决定绑定范围与初始化时机

`var` 是 function-scoped（函数作用域）。函数环境准备时，其绑定会初始化为 `undefined`；赋值表达式仍在声明出现的位置执行。`if` 等代码块不会为 `var` 创建独立绑定。

~~~javascript
function readBeforeAssignment() {
  console.log(status); // undefined
  if (true) {
    var status = "ready";
  }
  return status; // "ready"
}
~~~

`let` 和 `const` 是 block-scoped（块级作用域）。代码块环境创建时，绑定已经建立，但声明初始化前不可访问；这段时间称为 temporal dead zone（暂时性死区）。普通 `const` 声明必须带初始化式并禁止重新绑定；`for...in` 和 `for...of` 头部的 `const` 则由每轮取出的值初始化。`const` 不会冻结对象。
同一词法作用域中，`var` 名称可以重复声明；重复声明同名 `let` 或 `const` 会产生语法错误。`let` 可以不写初始化值，此时初始化为 `undefined`。

~~~javascript
{
  // console.log(count); // ReferenceError：仍处于暂时性死区
  let count = 1;
}

const options = { theme: "light" };
options.theme = "dark"; // 允许：对象仍可修改
// options = {};        // TypeError：const 绑定不能重新赋值
~~~

绑定本身不会重新赋值时用 `const`，会重新赋值时用 `let`；维护依赖函数作用域的旧代码时才需要 `var`。经典浏览器脚本与 ES 模块、Node.js 模块有不同的顶层环境：经典脚本的顶层 `var` 可以成为全局对象属性，顶层 `let`、`const` 则是全局词法绑定。跨宿主访问当前 Realm（执行域）的全局 `this` 值可用 `globalThis`。浏览器主线程提供 `window` 接口；worker 有自己的 `WorkerGlobalScope`，Node.js 模块也有自己的模块环境。不要把经典脚本规则套用到模块。

~~~html
<script>
  var scriptValue = "global object property";
  let scriptBinding = "global lexical binding";

  window.scriptValue; // "global object property"
  window.scriptBinding; // undefined
</script>
~~~

## 闭包保留绑定，而不是冻结快照

每次调用工厂函数都会创建自己的绑定。工厂返回后，返回函数仍可让这些绑定保持可达；之后读取时看到的是同一绑定上最新的值。

~~~javascript
function makeCounter(start) {
  let value = start;
  return () => value++;
}

const first = makeCounter(10);
const second = makeCounter(-2);
[first(), first(), first()];   // [10, 11, 12]
[second(), second(), second()]; // [-2, -1, 0]
~~~

同一次调用返回的多个闭包可以共享一个绑定。计数器对象中的 `increment`、`decrement` 和 `reset` 可以共同访问一个 `current` 值；`reset` 将同一绑定恢复到初始输入，而不是创建新计数器。

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

案例背景：报表服务创建处理器时捕获 `tag` 和 `calls`；每次调用都会更新同一个 `calls` 绑定。`this` 是另一种输入，由调用形式提供；[函数 this 与绑定](./this-and-function-binding.md) 继续说明它如何随方法调用和 `bind` 传递。

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

service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #2"
~~~

`tag` 和 `calls` 是词法状态；`this.prefix`、`this.format` 则通过调用时的接收者解析。处理器闭包保存前者，但它的 `this` 并未固定为某个 `service` 对象。

## 循环回调需要符合预期数量的绑定

`var` 循环复用一个函数作用域绑定，延后执行的回调都会读到最终值。`let` 循环每轮创建一个绑定，各回调就能读到各自迭代时的值。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

fromVar.map(fn => fn()); // [3, 3, 3]
fromLet.map(fn => fn()); // [0, 1, 2]
~~~

旧式 `var` 代码可用 Immediately Invoked Function Expression（IIFE，立即调用函数表达式）为每轮创建参数绑定；`let` 可以直接表达这种意图。

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

闭包也可以保留工厂参数，返回专门化后的函数。

~~~javascript
function add(x) {
  return function (y) {
    return x + y;
  };
}

const addFive = add(5);
addFive(3); // 8
~~~

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
~~~

延后调度的回调可以在多帧之间保留动画参数和计时状态。此例要求 `duration` 为正；每帧都会通过同一个闭包读取 `start`、`element`、`from` 和 `to`。

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
animate(animatedElement, 0, 100, 1000); // 约一秒内从 0px 移到 100px
~~~

`style.left` 对普通静态定位元素不起偏移作用。本例使用 `position: relative`，改变盒子的绘制位置，同时保留它原本在正常流中占据的位置。


## 闭包生命周期取决于可达性

外层调用返回后，返回函数仍能观察捕获的绑定。这是行为保证，不表示引擎会把所有局部变量永久存入环境对象。长期存在的事件监听器可能通过闭包让数据保持可达；生命周期结束时应移除监听器和其他引用。循环引用本身不足以造成泄漏，关键在于活动程序状态是否仍能到达这些数据。

**相关机制：** [对象与原型](./objects-functions-and-prototypes.md) 将同一报表处理器放入构造出的 service 实例，并说明它如何从原型取得 `format`。


> [!info]- 来源
> - var、let、const 的作用域和初始化时机：[ECMAScript 2026 Let and Const Declarations](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-let-and-const-declarations)（§14.3.1）；执行上下文与词法环境：[Execution Contexts](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-execution-contexts)（§9.4）。
> - 闭包对词法环境的引用：[ECMAScript Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)（§10.2）。
> - 全局 `this` 值与脚本、模块、worker 环境：[ECMAScript globalThis](https://tc39.es/ecma262/2026/multipage/global-object.html#sec-globalthis)、[WHATWG HTML script element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)、[WHATWG HTML worker global scope](https://html.spec.whatwg.org/multipage/workers.html#the-global-scope)、[Node.js CommonJS modules](https://nodejs.org/api/modules.html) 和 [Node.js ECMAScript modules](https://nodejs.org/api/esm.html)；浏览器事件回调：[WHATWG DOM addEventListener](https://dom.spec.whatwg.org/#dom-eventtarget-addeventlistener)；逐帧回调：[WHATWG HTML requestAnimationFrame](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#dom-animationframeprovider-requestanimationframe)；计时 API：[W3C High Resolution Time performance.now](https://www.w3.org/TR/hr-time-3/#dom-performance-now)。
