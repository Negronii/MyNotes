# JavaScript 函数的 `this` 值由什么决定？

调用 ordinary function（普通函数）时，调用形式提供 receiver（接收者），而被调用函数自身的严格性决定是否转换它：strict function（严格函数）的普通裸调用收到 `undefined`，sloppy function（非严格函数）会把它换成全局对象。方法调用使用点号前的对象，`call` 和 `apply` 可以立即指定接收者，`bind` 会创建保存接收者的新函数。arrow function（箭头函数）没有自己的 `this` 绑定，而是读取定义位置的外层值。

## 严格模式会改变部分调用行为

Strict mode（严格模式）会把部分历史代码中的错误转为异常，并改变普通函数调用收到 `this` 的方式。严格函数的普通裸调用中 `this` 为 `undefined`；非严格函数会把 `null` 或 `undefined` 替换为全局对象，并将原始值接收者装箱，即使调用它的代码本身是严格代码。ES 模块和 class 函数体自动采用严格模式。严格模式不是安全沙箱，也不会让 `eval` 变安全。

~~~javascript
function strictPlainCall() {
  "use strict";
  return this;
}

strictPlainCall(); // undefined

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

`"use strict"` 指令可以写在经典脚本或函数体开头。严格代码中给未声明名称赋值会抛出 `ReferenceError`；给不可写属性赋值会抛出 `TypeError`，而不是静默忽略。其他差异包括禁止 `with`、旧式八进制字面量和严格函数中的重复形参。

## 调用形式为报表处理器提供接收者

案例背景：本章在本地建立一份新的报表服务和新的处理器，避免依赖前一页的调用状态。处理器先递增闭包计数，再通过调用时的 `this` 查找 `format`：

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

service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"

const detached = service.onReport;
let detachedError;
try {
  detached({ title: "Q4" });
} catch (error) {
  detachedError = error.name;
}
detachedError; // "TypeError"

service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #3"
~~~

`service.onReport` 作为方法调用时，`service` 是接收者。赋给 `detached` 后，函数值不再带有点号前的对象，严格模式下 `this` 为 `undefined`。失败调用仍先执行 `calls += 1`，所以闭包计数已经从 1 变为 2；下一次成功调用返回 `#3`。词法状态与调用接收者分别由闭包和调用形式决定。

## `call`、`apply` 与 `bind` 的调用时机不同

`call` 立即调用并接收分开的实参；`apply` 立即调用并接收类数组实参列表；`bind` 返回一个供以后调用的新函数。

~~~javascript
function describe(prefix, report) {
  "use strict";
  return this.prefix + ": " + prefix + " " + report.title;
}

const report = { title: "Q4" };
describe.call(service, "Ready", report);          // "Sales: Ready Q4"
describe.apply(service, ["Ready", report]);       // "Sales: Ready Q4"
const boundDescribe = describe.bind(service, "Ready");
boundDescribe(report);                            // "Sales: Ready Q4"
~~~

`call`、`apply` 会把指定的 `thisArg` 传给函数调用；接收者是否转换取决于函数自身是否严格。`bind` 把接收者和前置参数保存在绑定函数中。绑定函数通过 `new` 调用时会忽略已保存的接收者，但仍使用前置参数。只拼接实参与 `apply` 的普通包装函数不会自动具备原生绑定函数的构造行为或 `name`、`length` 等元数据。

## 箭头函数与宿主回调遵循不同规则

箭头函数没有自己的 `this` 绑定、`arguments` 对象或 `prototype` 属性，也不能用 `new` 构造。它的 `this` 来自外层词法环境；`call`、`apply`、`bind` 都不能替换它。希望接收对象成为 `this` 时使用普通方法；确实需要词法捕获时使用箭头函数。

~~~javascript
const panel = {
  title: "Q4",
  read() { return this.title; },
  readArrow: () => this.title, // 读取外层 this；panel 不会成为接收者
};

panel.read(); // "Q4"
panel.readArrow(); // 结果取决于外层 this；panel 不会提供它
~~~

宿主调用回调时也能指定接收者。DOM 事件监听器算法会让普通监听器的 `this` 指向 `event.currentTarget`；箭头函数仍使用外层 `this`，因此应从事件对象显式读取目标。

~~~javascript
const button = document.createElement("button");
document.body.append(button);

button.addEventListener("click", function (event) {
  this === event.currentTarget; // true
});
button.addEventListener("click", event => {
  event.currentTarget === button; // true
});
~~~

## 临时属性调用辅助函数只覆盖有限契约

临时 Symbol 属性可用来演示 `object.method()` 为何会把对象作为 `this`。它无法复现内置方法对原始值、不可扩展接收者、代理、所有访问器或所有异常路径的处理。向 `Function.prototype` 添加自定义方法还会修改共享内置对象，因此这只是练习，不是应用代码。

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
~~~

即使被调用函数抛错，`finally` 仍会清理临时键。归档中的 `myApply` 练习用 `Array.prototype.slice.call` 转换类数组，把 `null`、`undefined` 当成空列表，再委托给范围受限的 `myCall`；因此对没有实参的 `arguments` 调用会得到 `0`。

<details>
<summary>归档练习：范围受限的 myCall 与 myApply</summary>

这个练习用临时 Symbol 属性制造方法调用语法，只接受对象或函数接收者。apply 版本把 nullish 实参列表当作空列表，并复制其他类数组输入；它不模拟原始值接收者转换，也不覆盖所有 Proxy 和异质对象行为。

~~~javascript
Function.prototype.myCall = function (context, ...args) {
  if (context === null ||
      (typeof context !== "object" && typeof context !== "function")) {
    throw new TypeError("This exercise requires an object receiver");
  }
  const key = Symbol("temporary call");
  Object.defineProperty(context, key, { value: this, configurable: true });
  try {
    return context[key](...args);
  } finally {
    delete context[key];
  }
};

Function.prototype.myApply = function (context, args) {
  const list = args == null ? [] : Array.prototype.slice.call(args);
  return this.myCall(context, ...list);
};

const receiver = { base: 10 };
function sum(a, b) { return this.base + a + b; }

sum.myCall(receiver, 1, 2); // 13
(function () { return arguments.length; }).myApply(receiver, []); // 0
~~~

唯一 Symbol 可避免与字符串键冲突；即使目标抛错，`finally` 也会清理临时属性。修改 `Function.prototype` 只用于练习，应用代码应使用内置方法。

</details>


**相关机制：** [JavaScript 对象如何查找属性？](./objects-functions-and-prototypes.md) 解释属性查找和 getter；[使用 `new` 构造对象](./construction-and-new.md) 说明绑定函数构造时为何忽略已绑定的 `this`。


> [!info]- 来源
> - 严格模式和普通调用的 this 绑定：[ECMAScript 2026 Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)、[Function Calls](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-function-calls) 和 [OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)（§10.2.1.2）。
> - 显式接收者与绑定函数：[ECMAScript Function.prototype.call](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.call)、[Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply) 和 [Function.prototype.bind](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.bind)；箭头函数：[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)。
> - DOM 普通事件监听器的接收者：[WHATWG DOM Event Listener Invocation](https://dom.spec.whatwg.org/#concept-event-listener-invoke)。
