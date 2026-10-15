# Scope & Closure / 作用域与闭包

> **核心解释 / Core idea：** 作用域（scope）决定一个绑定（binding）可以在哪里被查找；闭包（closure）让函数继续访问其定义时外层词法环境中的绑定。  
> **Interview answer / 面试简答：** Scope is lexical: names are resolved from where a function is defined, not where it is called. A closure keeps access to captured bindings after the outer function returns, while those bindings can still change. / 作用域由代码定义位置决定，而非调用位置；外层函数返回后，闭包仍可访问捕获的绑定，且读取的是该绑定的当前值。

## 作用域与名称查找 / Scope and name resolution

作用域描述标识符在哪段代码中可见。JavaScript 按词法结构解析名称：先查当前环境，再沿外层环境逐层查找；到达最外层仍找不到时，读取会产生 `ReferenceError`。引擎用执行上下文与词法环境（lexical environment）描述这套关系；这是规范模型，不要求实现必须用同名的内存对象。[ECMAScript 规范的执行上下文与环境记录](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html)和 [MDN 闭包指南](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)提供了标准定义与示例。

### 全局作用域（global scope）

“全局”取决于宿主环境。跨环境代码可用 `globalThis` 指向当前全局对象；浏览器窗口通常是 `window`，Web Worker 使用自己的全局对象。在浏览器的经典非模块脚本顶层，`var` 和函数声明会成为全局对象属性；顶层 `let`、`const` 不会。

~~~html
<script>
  var scriptVar = 'global object property';
  let scriptBinding = 'global lexical binding';

  console.log(window.scriptVar);     // 'global object property'
  console.log(window.scriptBinding); // undefined
</script>
~~~

模块顶层是模块作用域，不会因为写在文件顶层就自动成为 `window` 属性。脚本和模块语义不同，阅读顶层声明时要先确认代码以哪种方式执行。

宿主对全局对象的提供方式有所不同；跨环境代码可用 `globalThis` 访问当前全局对象。关于[全局对象与脚本顶层声明](https://developer.mozilla.org/en-US/docs/Glossary/Global_object)及 [`let` 的作用域和暂时性死区](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)，可参见MDN说明。

### 函数作用域与块级作用域 / Function and block scope

`var` 的作用域是最近的函数；函数外声明时，它属于脚本的全局环境或模块环境。它不会因 `if`、`for` 或普通代码块而缩小范围。`let`、`const` 则属于最近的块，包括 `if`、`switch`、循环和独立的 `{}`；模块顶层的 `let`、`const` 属于该模块。

~~~javascript
function example() {
  if (true) {
    var functionScoped = 'visible in the function';
    let blockScoped = 'visible only in this block';
  }

  console.log(functionScoped); // 'visible in the function'
  console.log(blockScoped);    // ReferenceError
}
~~~

`let` 和 `const` 声明也会在进入作用域时建立绑定，但在执行到声明前处于暂时性死区（temporal dead zone）；此时读取会抛出 `ReferenceError`。因此，更准确的做法是“用 `let` / `const` 获得块级作用域和更早的错误检查”，而不是说它们完全没有提升。`const` 禁止重新给绑定赋值，但若绑定指向对象，对象内容仍可变。更完整的声明对比见 [JavaScript 基础](./javascript-basics.md)。

### 词法作用域（lexical scope）与作用域链（scope chain）

函数从定义它的位置取得外层作用域。调用者自己的局部变量不会插入被调用函数的词法作用域链。

~~~javascript
const label = 'global';

function outer() {
  const label = 'outer';

  function inner() {
    const detail = 'inner';
    return [label, detail];
  }

  return inner;
}

function callFromElsewhere() {
  const label = 'caller';
  return outer()();
}

console.log(callFromElsewhere()); // ['outer', 'inner']
~~~

这里 `inner` 先查自己的 `detail`，再查 `outer` 的 `label`，最后才可能查到全局环境；`callFromElsewhere` 的 `label` 不参与查找。

## 闭包（closure）：函数与其定义时的词法环境

<a id="what-is-a-closure"></a>
<a id="what-is-closure"></a>

闭包是函数与其定义时可访问的词法环境之间的关系。JavaScript 函数创建时就带有这种词法访问能力；当内层函数在外层函数返回后仍可被调用时，这种能力就特别明显。闭包访问的是变量绑定，不是创建函数那一刻复制出来的值。[MDN 的闭包说明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)展示了这一行为。

~~~javascript
function makeReader() {
  let state = 'before';
  const read = () => state;

  state = 'after';
  return read;
}

const readState = makeReader();
console.log(readState()); // 'after'
~~~

`readState` 读取同一个 `state` 绑定，所以外层函数返回前的赋值可被看到。若每次调用 `makeReader`，则每次都有独立的 `state`。

### 闭包的常见用途 / Common uses

**私有状态（private state）。** 返回多个共享同一环境的操作，可以让状态不作为对象属性暴露：

~~~javascript
function makeCounter() {
  let count = 0;

  return {
    increment() { count++; return count; },
    decrement() { count--; return count; },
    value() { return count; },
  };
}

const counter = makeCounter();
counter.increment(); // 1
counter.increment(); // 2
counter.count;       // undefined: count 不是对象属性
~~~

每次调用 `makeCounter` 都会创建一份独立状态。这是一种封装方式；现代 JavaScript 也提供 class 私有字段等其他机制。

**函数工厂与偏应用（function factory / partial application）。** 参数可被闭包固定下来，生成用途不同的函数：

~~~javascript
function multiplyBy(factor) {
  return (number) => number * factor;
}

const double = multiplyBy(2);
const triple = multiplyBy(3);

double(5); // 10
triple(5); // 15
~~~

**事件回调（event callback）。** 回调可访问注册时所在作用域里的变量：

~~~javascript
function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener('click', () => {
    console.log('Clicked: ' + label);
  });
}

attachLogger('btn1', 'primary');
attachLogger('btn2', 'secondary');
~~~

两个回调各自通过调用 `attachLogger` 时创建的环境读取自己的 `label`。

### 循环中的 `var` 与 `let` / Loop bindings

`var` 在循环外的函数作用域内只有一个绑定；循环结束后，延迟执行的回调会读到它的最终值。循环头使用 `let` 时，每次迭代有独立的绑定：

~~~javascript
const varCallbacks = [];
for (var i = 0; i < 5; i++) {
  varCallbacks.push(() => i);
}

const letCallbacks = [];
for (let j = 0; j < 5; j++) {
  letCallbacks.push(() => j);
}

console.log(varCallbacks.map((callback) => callback())); // [5, 5, 5, 5, 5]
console.log(letCallbacks.map((callback) => callback())); // [0, 1, 2, 3, 4]
~~~

若旧代码必须使用 `var`，IIFE（立即调用函数表达式）也可为每次迭代创建一份参数绑定：

~~~javascript
const callbacks = [];
for (var index = 0; index < 5; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}

console.log(callbacks.map((callback) => callback())); // [0, 1, 2, 3, 4]
~~~

现代代码通常直接用 `let` 或 `const` 表达每轮迭代的绑定，避免额外包装函数。

### 闭包与内存生命周期 / Closures and memory lifetime

函数返回并不意味着它创建的局部绑定立即失效：只要某个可达闭包仍能读取这些绑定，程序就必须保留可观察到的行为。但不能据此推断“整个外层作用域中的每个变量都必然一直占用内存”；引擎可以优化未被使用的内容，而垃圾回收器何时回收不可达对象也不由源码中的作用域结束时刻决定。

实际需要关注的是引用路径：长期保存的回调若读取大型对象，就可能让该对象继续可达。事件监听器会持有回调；不再需要时，移除监听器并释放其他回调引用，才可能让相关对象变为可回收。单纯存在循环引用不等于泄漏；关键是对象图是否仍从程序可达。关于闭包可能带来的性能和内存成本，参见 [MDN 性能说明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures#performance_considerations)。

## 复习要点 / Takeaways

- `var` 是函数级（或脚本/模块顶层）绑定；`let`、`const` 是块级绑定。
- 词法作用域按函数定义位置查找；调用位置不改变外层查找链。
- 闭包保留对绑定的访问，读到的可以是后续更新后的值。
- 生命周期由可达引用决定；函数离开词法作用域不等于相关数据立即释放。

**延伸阅读：** [JavaScript 基础](./javascript-basics.md)说明声明差异；[对象、函数与原型](./objects-functions-and-prototypes.md)解释 `this` 的调用规则为何不同于词法作用域。

