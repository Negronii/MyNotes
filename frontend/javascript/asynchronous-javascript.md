# How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？

**Core answer / 核心回答：** A callback gives an API a function to call later. A Promise represents one future fulfillment or rejection and composes with then and catch. An async function returns a Promise, while await writes the same control flow in sequential syntax. Promise combinators coordinate already-started work; they do not cancel it. / 回调把函数交给 API 供其稍后调用。Promise 表示未来的一次成功或拒绝，并可通过 then 和 catch 组合。async 函数返回 Promise，await 用顺序语法表达同一控制流。Promise 组合方法协调已经启动的任务，但不会取消它们。


## How callbacks express deferred work / 回调如何表达延后执行

A callback passes a function to an API to be called later. Dependent callback nesting can make control flow and error paths hard to follow; callbacks still fit event handlers and many host APIs. / 回调把函数交给 API，供其稍后调用。若任务相互依赖，层层嵌套会让控制流和错误路径难以跟踪；事件处理器和许多宿主 API 仍适合用回调。

~~~javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
~~~

Promises were standardized in ES2015, async functions and await in ES2017, and async iteration in ES2018. Asynchronous APIs allow a program to continue while work is pending; that does not by itself imply parallel JavaScript computation. / Promise 于 ES2015 标准化，async 函数与 await 于 ES2017 标准化，异步迭代于 ES2018 标准化。异步 API 让程序在等待任务时继续推进，但这本身不表示 JavaScript 计算并行执行。

## What a Promise state means / Promise 状态表示什么

A Promise begins pending and settles once, either fulfilled with a value or rejected with a reason. It cannot change state after settlement. The executor passed to new Promise runs immediately; registered reactions run later as Promise jobs. / Promise 初始处于 pending 状态，之后只会成功完成并带有值，或拒绝并带有原因；完成后状态不可改变。传给 new Promise 的 executor 立即运行；注册的处理器稍后作为 Promise job 运行。

~~~mermaid
stateDiagram-v2
  [*] --> pending
  pending --> fulfilled
  pending --> rejected
  fulfilled --> [*]
  rejected --> [*]
~~~

then returns a new Promise, so a returned value fulfills the next link, a thrown error rejects it, and a returned Promise is adopted. catch handles a rejection; returning normally recovers with its value, while throwing propagates a rejection. / then 会返回一个新 Promise：返回值让下一环节成功完成，抛错会使其拒绝，返回 Promise 时后续会采用其最终状态。catch 处理拒绝；正常返回即以返回值恢复，抛错则继续传播拒绝。

finally normally passes through the original fulfillment value or rejection reason. If its callback throws or returns a rejected Promise, the new chain rejects with that failure. / finally 通常保留原成功值或拒绝原因。若回调抛错或返回拒绝的 Promise，新链会以该错误拒绝。

~~~javascript
const result = getUser(userId)
  .then(user => getOrders(user.id))
  .then(renderOrders)
  .catch(handleError);
~~~

An async function always returns a Promise. Code before its first suspension point runs synchronously. await suspends the async function until its operand settles, then resumes with the value or throws the rejection into the surrounding control flow. / async 函数始终返回 Promise。第一个暂停点之前的代码同步运行。await 会暂停该函数，直到操作数完成，再以成功值继续，或把拒绝原因抛入当前控制流。

~~~javascript
async function loadOrders(userId) {
  try {
    const user = await getUser(userId);
    return await getOrders(user.id);
  } catch (error) {
    handleError(error);
    throw error; // returned Promise remains rejected
  }
}
~~~

For deciding where to recover or propagate a rejection, see [Error Handling / 错误处理](./error-handling.md).

## Which Promise combinator fits? / 应选择哪个 Promise 组合方法？

| Method / 方法 | Returned Promise fulfills when / 成功条件 | Returned Promise rejects when / 拒绝条件 |
|---|---|---|
| Promise.all | Every input fulfills; result values keep input order / 全部成功；结果按输入顺序排列 | An input rejects / 任一输入拒绝 |
| Promise.allSettled | All inputs settle; each outcome is returned / 全部结束并返回各项结果 | Not because an input rejects / 不会因某项输入拒绝 |
| Promise.any | First input fulfills / 首项成功 | All inputs reject with AggregateError / 全部拒绝并产生 AggregateError |
| Promise.race | First settlement is fulfillment / 首项完成为成功 | First settlement is rejection / 首项完成为拒绝 |

These methods coordinate inputs; they do not cancel losing operations. Passing promises usually means their underlying work has already started. If an API supports cancellation and abandoned work should stop, use its explicit mechanism, such as AbortController with Fetch. / 这些方法用于协调输入，不会取消未获胜的操作。传入 Promise 时，其底层任务通常已经启动。若 API 支持取消且不再需要的工作应停止，使用其显式机制，例如 Fetch 配合 AbortController。

The methods were added across editions: Promise.all and Promise.race in ES2015, Promise.allSettled in ES2020, and Promise.any in ES2021. Their normative completion behavior is in the [ECMAScript Promise combinator algorithms](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-combinator-objects). Promise.race installs both fulfillment and rejection reactions for each input in [PerformPromiseRace](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace).

## When should operations be awaited sequentially or concurrently? / 何时顺序等待，何时并发推进？

Await sequentially when a later operation depends on the earlier result. Start independent operations before awaiting either, then coordinate them with Promise.all when all results are required. This is concurrency, not necessarily parallel JavaScript CPU work: a host may overlap I/O while a JavaScript agent still runs one job at a time. / 后续操作依赖前项结果时顺序 await。操作彼此独立时，应先启动它们，再用 Promise.all 等待所需结果。这是并发，不一定是 JavaScript CPU 计算并行：宿主可重叠处理 I/O，而 JavaScript agent 仍一次执行一个 job。

~~~javascript
// Dependent: the second operation needs the first result.
const user = await fetchUser(id);
const orders = await fetchOrders(user.id);

// Independent: start both before awaiting either.
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts()
]);
~~~

for await...of consumes async iterables in order and can also adapt a synchronous iterable of Promises, awaiting each value before continuing. For independent operations, Promise.all is usually clearer. The protocol and sequential-consumption details belong to [Iterators and Generators / 迭代器与生成器](./iterators-and-generators.md).

## How Promise-job order is observed / 如何观察 Promise job 顺序

Promise reactions are queued as jobs. When one handler queues a later reaction, already-queued jobs run first. The host determines checkpoints, so keep browser task/rendering rules and Node scheduling rules in [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md), not in this language-level note. / Promise 处理器会排入 job 队列。某个处理器新增后续处理器时，已排队的 job 先运行。检查点由宿主决定；浏览器任务/渲染规则和 Node 调度规则见[事件循环与宿主调度](../runtime/event-loop.md)，不在此处混作语言保证。

~~~javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0, 2, 1, 3
~~~

Returning a Promise from a handler makes the next Promise adopt its eventual state. The following observed order is scoped to the tested context, not a portable count of “ticks.” / 处理器返回 Promise 时，后续 Promise 会采用它最终的状态。下例顺序限定于实际测试的上下文，不应转述为跨环境通用的“tick 数”。

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3));
// Node.js v26.11.1, CommonJS: 0, 1, 2, 3, 4
~~~

See [ECMAScript Promise jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) and the [browser event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops). Node queue ordering and CJS/ESM context are explained separately in the runtime note. The focused [Currying and Partial Application / 柯里化与部分应用](./currying-and-partial-application.md) and [Chainable Task Queue / 链式任务队列](./chainable-task-queue.md) articles preserve two code exercises from the original collection.
