# How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？

**Core answer / 核心回答：** JavaScript resolves a name from the function’s definition environment outward, not from its caller. A closure is a function that keeps access to bindings from that lexical environment. It reads the binding’s current value, so state can remain observable after the outer call returns. / JavaScript 按函数的定义环境向外查找名称，不按调用者的位置查找。闭包让函数继续访问定义时外层词法环境中的绑定；它读取绑定的当前值，因此外层函数返回后状态仍可被观察。

## How name lookup follows lexical structure / 名称查找如何沿词法结构进行

An identifier lookup starts in the current lexical environment and continues through its enclosing environments. The caller’s local variables are not inserted into a function’s lookup chain. Execution contexts and lexical environment records are the specification model for this behavior; engines need not allocate objects with those exact names or shapes. / 标识符先在当前词法环境中查找，再逐层向外查找。调用者的局部变量不会插入被调用函数的查找链。执行上下文和词法环境记录是规范描述这种行为的模型；引擎不必创建名称和结构完全相同的对象。

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

inner finds its own detail, then outer’s label, and only then could reach the global environment. The caller’s label is irrelevant. / inner 先找到自己的 detail，再找到 outer 的 label，之后才可能到达全局环境；caller 的 label 不参与查找。

~~~mermaid
flowchart LR
  inner["inner environment: detail"] --> outer["outer environment: label"]
  outer --> global["global environment"]
  caller["caller environment: label"] -. "not part of lookup chain" .-> inner
~~~

## What a closure retains / 闭包保留了什么

A closure is a function together with its access to the lexical bindings it uses. It does not copy the value present when the function was created. / 闭包是函数及其对所用词法绑定的访问能力；创建函数时的值不会被定格为一份副本。

~~~javascript
function makeReader() {
  let state = "before";
  const read = () => state;
  state = "after";
  return read;
}

const readState = makeReader();
readState(); // "after"
~~~

Each call to makeReader creates a distinct state binding. Several returned functions can intentionally share one binding, which is useful for private state. / 每次调用 makeReader 都会创建独立的 state 绑定。多个返回函数也可以有意共享一个绑定，从而形成私有状态。

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
counter.count;       // undefined: count is not an object property
~~~

A function factory can retain a parameter to specialize later calls. Event callbacks similarly retain values from the registration call. / 函数工厂可以保留参数，让后续调用使用专门化的函数。事件回调也会保留注册回调时所在环境中的值。

~~~javascript
function multiplyBy(factor) {
  return number => number * factor;
}
const double = multiplyBy(2);
double(5); // 10

function attachLogger(element, label) {
  element.addEventListener("click", () => console.log("Clicked: " + label));
}
~~~

## Why loop callbacks differ / 循环回调为什么读到不同值

A var loop has one function-scoped binding, so deferred callbacks read its final value. A let loop creates a per-iteration binding, so each callback retains the value for its iteration. / var 循环使用一个函数级绑定，延后执行的回调会读到它的最终值。let 循环为每次迭代创建绑定，因此回调保留各自迭代中的值。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

fromVar.map(fn => fn()); // [3, 3, 3]
fromLet.map(fn => fn()); // [0, 1, 2]
~~~

An IIFE can introduce a separate parameter binding in legacy var code, but modern code normally expresses the intended per-iteration binding directly with let. / 旧式 var 代码可用 IIFE 为每轮引入独立参数绑定；现代代码通常直接用 let 表达每轮独立绑定的意图。

~~~javascript
const callbacks = [];
for (var index = 0; index < 3; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}
callbacks.map(fn => fn()); // [0, 1, 2]
~~~

## How closure lifetime relates to memory / 闭包生命周期与内存有何关系

An outer call returning does not make a captured binding immediately unusable. As long as a reachable closure can observe it, the program must preserve the behavior. This does not mean every variable in the entire outer scope must occupy memory forever; implementations can optimize unobservable values. / 外层调用返回并不意味着捕获的绑定立即失效。只要可达闭包仍能观察它，程序就必须保留可观察行为；但这不表示外层作用域中的所有变量都必然永久占用内存，引擎可以优化不可观察的值。

Think in terms of reachability: a long-lived listener that closes over a large object can keep that object reachable. Remove the listener and other references when their lifetime ends. A cycle alone is not a leak; the important question is whether a path from live program state still reaches the objects. For garbage-collection models and diagnostics, see [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md). / 从可达性判断更实用：长期保存的监听器若闭包捕获大型对象，就可能让对象继续可达。生命周期结束时移除监听器及其他引用。循环引用本身不等于泄漏，关键是活动程序状态是否仍有到这些对象的引用路径。垃圾回收模型与排查见[事件循环与宿主调度](../runtime/event-loop.md)。

**See also:** [JavaScript Basics / JavaScript 基础](./javascript-basics.md) explains the binding and temporal-dead-zone rules that determine which environment a closure can capture. Ordinary function this is determined by call form, not lexical name lookup; see [Function this and Binding / 函数 this 与绑定](./this-and-function-binding.md).
