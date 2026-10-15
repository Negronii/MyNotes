# Asynchronous JavaScript / 异步 JavaScript

**Key terms / 关键词:** callback 回调 · Promise Promise 对象 · microtask 微任务 · async iterable 异步可迭代对象 · concurrency 并发

Asynchronous APIs let a program continue while work is pending, but “async” does not itself mean that JavaScript executes CPU work in parallel or that the host uses one thread. Promises were standardized in ES2015, async functions/await in ES2017, and async iteration in ES2018. Callbacks, Promises, and async/await express deferred control flow with different composition and error-handling styles. / 异步 API 让程序在等待任务时继续推进，但“异步”本身不表示 JavaScript 会并行执行 CPU 计算，也不表示宿主只有一个线程。Promise 属于 ES2015，async 函数/await 属于 ES2017，异步迭代属于 ES2018。回调、Promise 和 async/await 是表达延后控制流的不同方式，在组合能力和错误处理上各有特点。

## Callbacks, Promises, and async/await / 回调、Promise 与 async/await

A callback passes a function to an API to be called later. Dependent callback nesting can make control flow and error paths hard to follow; callbacks are still appropriate for event handlers and many host APIs. / 回调把函数传给 API，供其稍后调用。依赖关系层层嵌套时，控制流和错误路径会难以跟踪；事件处理器和许多宿主 API 仍适合使用回调。

```javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
```

A Promise represents a future fulfillment or rejection. Once settled, its state does not change. then returns another Promise, so success and failure can be composed; catch handles a rejection by recovering with a value or propagating with a throw. / Promise 表示未来的成功结果或拒绝原因。状态一旦确定就不会改变。then 返回新的 Promise，因此成功和失败流程可以组合；catch 可以通过返回值恢复，也可以通过再次抛出错误继续传播。

```javascript
const result = getUser(userId)
  .then(user => getOrders(user.id))
  .then(renderOrders)
  .catch(handleError);
```

An async function always returns a Promise. await suspends that function until its operand settles, then resumes with the fulfillment value or throws the rejection into the surrounding control flow. Code before the first suspension runs synchronously. / async 函数始终返回 Promise。await 会暂停该函数，直到操作数完成，再以成功值继续或把拒绝原因抛入当前控制流。第一个暂停点之前的代码仍同步执行。

```javascript
async function loadOrders(userId) {
  try {
    const user = await getUser(userId);
    return await getOrders(user.id);
  } catch (error) {
    handleError(error);
    throw error; // the returned Promise remains rejected
  }
}
```

## Promise states and combinators / Promise 状态与组合方法

A Promise executor runs immediately when new Promise(executor) is called; reactions registered through then run asynchronously as Promise jobs. finally normally passes the original outcome through; if its callback throws or returns a rejected Promise, the resulting chain rejects with that new failure. / 调用 new Promise(executor) 时，executor 会立即运行；通过 then 注册的处理器则作为 Promise job 异步执行。finally 通常保留原结果；若回调抛错或返回拒绝的 Promise，后续链会以新错误拒绝。

| Method / 方法 | Returned Promise fulfills when / 成功条件 | Returned Promise rejects when / 拒绝条件 |
|---|---|---|
| Promise.all | Every input fulfills; values keep input order / 全部成功，值按输入顺序排列 | An input rejects / 任一输入拒绝 |
| Promise.allSettled | All inputs settle; each outcome is returned / 全部完成并返回每项状态 | Not because an input rejects / 不会因某项输入拒绝 |
| Promise.any | First input fulfills / 首个输入成功 | All inputs reject; AggregateError is returned / 全部拒绝时返回 AggregateError |
| Promise.race | First settlement is fulfillment / 首个完成项成功 | First settlement is rejection / 首个完成项拒绝 |

The specification installs both fulfillment and rejection reactions for each input in [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace). / 规范中的 [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace) 会为每项输入同时安装成功和拒绝处理器。

These methods coordinate already-created work; they do not cancel losing operations. If an API supports cancellation and abandoned work should stop, use its explicit mechanism, such as AbortController with Fetch. / 这些方法只协调已经创建的任务，不会取消未获胜的操作。若 API 支持取消且希望停止无用任务，应使用显式取消机制，例如 Fetch 配合 AbortController。

## Sequential and concurrent work / 顺序执行与并发启动

Await independent operations together when they may proceed concurrently. This is concurrency, not necessarily parallel JavaScript computation: the host may overlap I/O while each JavaScript agent still runs one job at a time. / 相互独立且可同时推进的操作可一起等待。这是并发，不一定是 JavaScript 计算并行：宿主可以重叠处理 I/O，而每个 JavaScript agent 仍一次执行一个 job。

```javascript
// Dependent: the second operation needs the first result.
const user = await fetchUser(id);
const orders = await fetchOrders(user.id);

// Independent: start both before awaiting either.
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts()
]);
```

for await...of awaits values from an async iterable in iteration order. It can also adapt a synchronous iterable of Promises, but awaits each yielded value before continuing. If all operations are independent, Promise.all usually expresses both concurrency and rejection handling more directly. / for await...of 按迭代顺序等待异步可迭代对象产出的值。它也能适配由 Promise 组成的同步可迭代对象，但会在继续前等待当前值。若操作彼此独立，Promise.all 通常更直接地表达并发启动和拒绝处理。

## Promise-job order / Promise job 顺序

Promise reactions are queued as jobs; when one handler queues another reaction, already-queued jobs run first. This explains the interleaving below. Exact checkpoints are provided by the host, so keep browser event-loop and Node scheduling rules separate. / Promise 处理器会排入 job 队列；某个处理器新增后续处理器时，队列中已存在的 job 会先运行。下面的交错顺序由此产生。具体检查点由宿主提供，因此应区分浏览器事件循环和 Node 调度规则。

```javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0, 2, 1, 3
```

Returning a Promise from a handler makes the next Promise adopt its eventual state. The timing of visible reactions follows the job queue, not a portable count of “ticks”; use a runnable example only for the runtime and context tested. / 处理器返回 Promise 时，后续 Promise 会采用它最终的状态。可观察到的处理顺序取决于 job 队列，不宜用跨环境固定的“tick 数”描述；具体示例只代表实际测试过的运行时和上下文。

```javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3));
// Node.js v26.11.1, CommonJS: 0, 1, 2, 3, 4
```

The returned Promise is adopted by the chained Promise; its reactions join the same job queue as the second chain. Do not model this as one universal “extra tick.” / 后续 Promise 会采用处理器返回的 Promise 状态；其处理器也会进入第二条链所在的 job 队列。不要把它概括为跨宿主通用的“多一个 tick”。

See [ECMAScript Promise jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) and the [browser event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops). Node queue ordering is documented separately in [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md). / 详见 [ECMAScript Promise job 规范](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) 与 [浏览器事件循环规范](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)。Node 队列顺序在 [事件循环与宿主调度](../runtime/event-loop.md) 中单独说明。

## Currying / 柯里化

Currying adapts a multi-argument function into a sequence of calls, allowing partial application. This compact implementation uses fn.length as the arity and supports ordinary positional functions; defaults, rest parameters, placeholders, and other arity rules need a different contract. / 柯里化把多参数函数改造成一系列调用，以支持部分应用。以下简化实现用 fn.length 作为元数，适用于普通位置参数函数；默认参数、剩余参数、占位符及其他元数规则需要另行设计。

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return function (...next) {
      return curried.apply(this, [...args, ...next]);
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);
curriedSum(1)(2)(3); // 6
curriedSum(1, 2)(3); // 6
```

## A chainable task queue / 链式异步任务队列

This LazyMan example queues actions and defers the first step so the synchronous method chain is built before execution begins. Each action calls next() only when its work is complete. Time is in milliseconds. / 这个 LazyMan 示例把操作加入队列，并延后首步执行，以便先完成同步方法链。每个任务只在自身完成后调用 next()。时间单位为毫秒。

```javascript
class LazyMan {
  constructor(name) {
    this.name = name;
    this.tasks = [];
    setTimeout(() => this.next(), 0);
  }

  eat(food) {
    this.tasks.push(() => {
      console.log("eat " + food);
      this.next();
    });
    return this;
  }

  sleep(ms) {
    this.tasks.push(() => {
      setTimeout(() => {
        console.log("wake up after " + ms + "ms");
        this.next();
      }, ms);
    });
    return this;
  }

  next() {
    const task = this.tasks.shift();
    if (task) task();
  }
}

new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
// eat fruit → wake up after 10ms → eat bread
```

This is a teaching example, not a cancellation-aware production queue. A production design should define failure handling, cancellation, and what happens when a task never completes. / 这是讲解示例，不是带取消能力的生产队列。生产实现还需定义失败处理、取消方式，以及任务永不完成时的行为。

## Arrow functions / 箭头函数

Arrow functions capture this lexically; they do not have their own this or arguments, are not constructible with new, and do not have a prototype property. Use method syntax when a method needs its receiver as this; use rest parameters for a local argument list. / 箭头函数从外层词法作用域捕获 this；它没有自己的 this 或 arguments，不能用 new 构造，也没有 prototype 属性。方法需要把接收者作为 this 时使用方法语法；需要函数自己的参数列表时使用剩余参数。

```javascript
const counter = {
  value: 1,
  read() { return this.value; },
  readArrow: () => this.value // captures surrounding this, not counter
};
```

An arrow function can still be useful as an instance field when lexical capture is intentional; call, apply, and bind cannot replace its captured this. / 若确实需要词法捕获，箭头函数也可作为实例字段；call、apply 和 bind 无法替换捕获到的 this。

## Callback arity gotcha / 回调参数个数陷阱

The `Array.prototype.map` callback receives the value, index, and array. `parseInt` interprets its second parameter as a radix, so passing it directly to `map` changes the radix for later items. / `Array.prototype.map` 的回调会收到值、索引和数组。`parseInt` 把第二个参数解释为基数，因此直接传给 `map` 会让后续元素使用不同基数。

See the [ECMAScript `Array.prototype.map` algorithm](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map). / 详见 [ECMAScript `Array.prototype.map` 规范算法](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map)。

```javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
```

**Interview answer / 面试回答:** Promises compose asynchronous outcomes and provide a rejection channel; async/await expresses that control flow in sequential syntax. Use Promise.all for independent operations that must all succeed, but remember it does not cancel sibling work. Promise reactions are jobs; host event-loop ordering depends on the environment. / Promise 可组合异步结果并提供拒绝传播通道；async/await 用顺序语法表达这种控制流。多个独立操作都必须成功时可用 Promise.all，但它不会取消其他任务。Promise 处理器以 job 执行，宿主事件循环顺序因环境而异。

Related: [Error Handling / JavaScript 错误处理](./error-handling.md); [Iterators and Generators / 迭代器与生成器](./iterators-and-generators.md); [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md).
