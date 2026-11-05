# How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？

**Core answer / 核心回答：** An ordinary function gets its this value from the call form: obj.method() supplies obj, call/apply supply an explicit receiver, and bind creates a bound function. A plain strict-function call uses undefined. An arrow function instead captures this from its surrounding lexical environment and cannot be rebound. / 普通函数的 this 由调用方式决定：obj.method() 以 obj 为接收者，call/apply 显式提供接收者，bind 创建绑定函数；严格函数的普通调用中 this 为 undefined。箭头函数从外层词法环境捕获 this，不能重新绑定。

## Ordinary calls supply the receiver / 普通调用形式提供接收者

~~~javascript
const service = {
  url: "/data",
  fetch() { return this.url; }
};

service.fetch(); // "/data"
const detached = service.fetch;
detached(); // TypeError in strict code; it no longer has service as its receiver
~~~

In sloppy code, a plain call substitutes the host’s global this value. In a browser classic script that is generally window; Node module wrappers have their own top-level conventions. Strict mode, ES modules, and class bodies use strict semantics. / 非严格代码中的普通调用会把 this 替换为宿主全局值；浏览器经典脚本中通常为 window，Node 模块包装器另有顶层约定。严格模式、ES 模块和 class 函数体使用严格语义。

## Explicit receiver methods / 显式接收者方法

call invokes immediately with separate arguments; apply invokes immediately with an argument list; bind creates a new function with a bound receiver and leading arguments. / call 使用分开的参数立即调用；apply 使用参数列表立即调用；bind 创建一个绑定接收者和前置参数的新函数。

~~~javascript
function describe(prefix, name) {
  return prefix + " " + name + " (" + this.role + ")";
}

describe.call({ role: "admin" }, "Hello", "Ada");
describe.apply({ role: "admin" }, ["Hello", "Ada"]);
const greetAdmin = describe.bind({ role: "admin" }, "Hello");
greetAdmin("Ada"); // "Hello Ada (admin)"
~~~

If a bound function is called with new, its bound receiver is ignored, but its leading arguments remain in effect. Arrow functions have no own this or arguments, are not constructible with new, and do not have an own prototype property. call, apply, or bind cannot replace an arrow’s lexical this. Use method syntax when the method needs its object as this; use an arrow when lexical capture is intentional. / 绑定函数通过 new 调用时会忽略已绑定的接收者，但保留前置参数。箭头函数没有自己的 this 或 arguments，不能通过 new 构造，也没有自有 prototype 属性。call、apply 和 bind 都不能替换箭头函数捕获的 this。方法需要对象作为 this 时使用方法语法；确实需要词法捕获时使用箭头函数。

~~~javascript
const counter = {
  value: 1,
  read() { return this.value; },
  readArrow: () => this.value // captures surrounding this, not counter
};
~~~

A host API can supply a receiver when it invokes a callback. The DOM calls an ordinary event listener with this set to event.currentTarget; an arrow keeps its surrounding this, so use the event property explicitly. See the [WHATWG DOM listener-invocation algorithm](https://dom.spec.whatwg.org/#concept-event-listener-invoke) and [DOM event propagation / DOM 事件传播](../browser-apis/dom-manipulation-and-events.md) for the surrounding event contract. / 宿主 API 调用回调时也可提供接收者。DOM 调用普通事件监听器时会把 this 设为 event.currentTarget；箭头函数保留外层 this，因此应显式读取事件属性。详见 [WHATWG DOM 监听器调用算法](https://dom.spec.whatwg.org/#concept-event-listener-invoke)及 [DOM 事件传播](../browser-apis/dom-manipulation-and-events.md)中的相关契约。

~~~javascript
const button = document.querySelector("button"); // assume a button exists
button.addEventListener("click", function (event) {
  this === event.currentTarget; // true
});
button.addEventListener("click", event => {
  event.currentTarget === button; // true: arrow this is not the listener receiver
});
~~~

Lexical name lookup and lexical this are separate ideas: closures capture outer bindings, while an ordinary function’s this depends on its invocation. See [Scope and Closure / 作用域与闭包](./scope-and-closure.md).

## Why a small bind helper is not a polyfill / 简化 bind 模型为何不是 polyfill

This helper illustrates partial application for an object receiver. Native bind also handles constructor calls, constructibility, and function metadata. / 这个辅助函数演示对象接收者上的部分应用；原生 bind 还处理构造调用、可构造性和函数元数据。

~~~javascript
function bindForObjectReceiver(fn, receiver, ...leadingArgs) {
  return function (...laterArgs) {
    return fn.apply(receiver, [...leadingArgs, ...laterArgs]);
  };
}
~~~

A temporary property can also show how method-call syntax supplies this. This limited example only accepts an extensible object receiver; it does not model primitive receivers, proxies, strict/sloppy conversion, or every exceptional case. Use the built-ins in application code. / 临时属性也能展示方法调用如何提供 this。这个有限示例只接受可扩展对象接收者，不能模拟原始值接收者、代理、严格/非严格转换或所有异常情况。应用代码应使用内置方法。

~~~javascript
function callWithObjectReceiver(fn, receiver, ...args) {
  if (receiver === null ||
      (typeof receiver !== "object" && typeof receiver !== "function")) {
    throw new TypeError("This example requires an object receiver");
  }
  const key = Symbol("temporary method");
  Object.defineProperty(receiver, key, { value: fn, configurable: true });
  try {
    return receiver[key](...args);
  } finally {
    delete receiver[key];
  }
}
~~~

Ordinary function call behavior is specified by ECMAScript’s [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call), [Function.prototype.apply](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.apply), [Function.prototype.bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind), and [arrow-function definitions](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions). / 普通函数调用行为见 ECMAScript 的 [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call)、[Function.prototype.apply](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.apply)、[Function.prototype.bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind) 和[箭头函数定义](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)。
