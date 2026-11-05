# How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？

**Core answer / 核心回答：** An iterable provides an iterator through Symbol.iterator; each iterator next() call returns an object whose done value tells the consumer whether to stop. A generator implements this protocol by pausing at yield. Async iterables provide next results asynchronously and are consumed in order with for await...of. / 可迭代对象通过 Symbol.iterator 提供迭代器；每次调用 next() 返回带 done 值的对象，用于告知消费者是否停止。生成器在 yield 处暂停，以此实现该协议。异步可迭代对象异步提供 next 结果，并由 for await...of 按序消费。

## How iterable and iterator protocols work / 可迭代与迭代器协议如何工作

The iterable protocol exposes Symbol.iterator, which returns an iterator. The iterator’s next() method returns an object. The consumer converts its done property to Boolean; if done is missing, it acts as false. value supplies the current item and can be absent on completion. An object is not iterable just because it has numeric keys or a length. / 可迭代协议通过 Symbol.iterator 返回迭代器。迭代器的 next() 返回对象。消费者把 done 转为布尔值；若缺少 done，按 false 处理。value 提供当前项，完成时可以省略。有数字键或 length 的对象不会自动变成可迭代对象。

The protocol is defined by the [ECMAScript iteration interfaces](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration). / 协议定义见 [ECMAScript 迭代接口](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration)。

Arrays, strings, Maps, Sets, typed arrays, and arguments objects are language-provided iterables. NodeList is iterable in modern browser DOM implementations, but it is a host API rather than a JavaScript-language collection. Plain objects are not iterable by default. / 数组、字符串、Map、Set、类型化数组和 arguments 对象由语言提供迭代能力。现代浏览器 DOM 实现中的 NodeList 也可迭代，但它是宿主 API，不是 JavaScript 语言集合。普通对象默认不可迭代。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }

for (const [key, value] of new Map([["x", 1], ["y", 2]])) {
  console.log(key, value);
}
~~~

~~~mermaid
flowchart LR
  A["Iterable: Symbol.iterator()"] --> B["Iterator: next()"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["Use result.value"]
  D --> B
  C -- "true" --> E["Stop"]
~~~

An iterable can return a fresh iterator each time, but the protocol does not require that. Iterator objects and generators often return themselves and are one-shot. / 可迭代对象可以每次都返回新迭代器，但协议不要求如此。迭代器对象和生成器通常返回自身，因此只能消费一次。

~~~javascript
const range = {
  start: 1,
  end: 3,
  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) return { value: current++, done: false };
        return { value: undefined, done: true };
      }
    };
  }
};
[...range]; // [1, 2, 3]

const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true
~~~

## How early exit closes an iterator / 提前退出如何关闭迭代器

An iterator may expose return() as a cleanup hook. for...of closes the iterator when break or an abrupt completion such as an exception exits the loop. / 迭代器可提供 return() 清理钩子。break 或异常等 abrupt completion 离开 for...of 时，循环会关闭迭代器。

~~~javascript
const source = {
  [Symbol.iterator]() {
    let value = 0;
    return {
      next() {
        return { value: value++, done: false };
      },
      return() {
        console.log("release iterator resource");
        return { done: true };
      }
    };
  }
};

for (const value of source) {
  if (value === 2) break; // calls return() before leaving
}
~~~

The specification’s [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose) algorithm defines this cleanup behavior. It also defines how the consumer interprets iterator results in [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete).

## What yield and next(value) exchange / yield 与 next(value) 交换什么

A generator function returns an object that is both iterable and an iterator. yield pauses execution and produces a value; the next() call resumes it. The first next(value) argument is ignored because execution has not paused at a yield yet. Later arguments become the result of the suspended yield expression. / 生成器函数返回同时是可迭代对象和迭代器的对象。yield 暂停执行并产出值；调用 next() 时恢复。第一次 next(value) 的参数会被忽略，因为函数尚未暂停在 yield；之后传入的值会成为暂停处 yield 表达式的结果。

~~~javascript
function* conversation() {
  const name = yield "What is your name?";
  const hobby = yield "Hello, " + name + "! What do you enjoy?";
  return name + " likes " + hobby;
}

const chat = conversation();
chat.next();          // { value: "What is your name?", done: false }
chat.next("Ada");     // { value: "Hello, Ada! What do you enjoy?", done: false }
chat.next("coding");  // { value: "Ada likes coding", done: true }
~~~

yield* delegates iteration to another iterable or generator and receives its completion result. It can compose recursive traversals. / yield* 把迭代委托给另一个可迭代对象或生成器，并接收其完成结果，可用于组合递归遍历。

~~~javascript
function* flatten(items) {
  for (const item of items) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}
[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]

function* child() {
  yield "item";
  return 42;
}
function* parent() {
  const completion = yield* child();
  return completion;
}
const delegated = parent();
delegated.next(); // { value: "item", done: false }
delegated.next(); // { value: 42, done: true }
~~~

## Why generators are useful for lazy sequences / 生成器为何适合惰性序列

Generators compute on demand, so the consumer controls how many values to request. This can represent large or infinite sequences without storing every value in an array. / 生成器按需计算，由消费者决定请求多少项，因此可表示大型或无限序列，而不必预存所有值。

~~~javascript
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}
const fib = fibonacci();
fib.next().value; // 0
fib.next().value; // 1
fib.next().value; // 1
fib.next().value; // 2

function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}
const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
~~~

Before async/await, libraries such as co used a runner to yield Promises from generators and resume with their results. This is a historical pattern; async functions standardize another syntax and runtime protocol, rather than exposing a generator implementation. / async/await 出现以前，co 等库通过 runner 让生成器 yield Promise，再根据结果恢复执行。这是历史模式；async 函数标准化的是另一种语法与运行时协议，并非直接暴露生成器实现。

## How async iteration differs / 异步迭代有何不同

An async iterable (standardized in ES2018) supplies Symbol.asyncIterator. Each next() call makes its iterator result available asynchronously; for await...of waits for each result in sequence. This suits streams whose next value becomes available over time. A synchronous array of independent Promises is usually clearer with Promise.all. / 异步可迭代对象（ES2018 标准化）通过 Symbol.asyncIterator 提供迭代器，每次 next() 异步提供迭代结果；for await...of 按顺序等待各项，适合后续值逐渐到达的流。同步数组中相互独立的 Promise 通常用 Promise.all 更清晰。

`for await...of` can also consume a synchronous iterable of Promises, awaiting each yielded value before requesting the next one. If the Promises have already started, this preserves input order rather than yielding whichever finishes first. / `for await...of` 也能消费由 Promise 组成的同步可迭代对象；每项完成后才继续请求下一项。即使 Promise 已经启动，结果仍按输入顺序处理，而非按最快完成顺序产出。

~~~javascript
async function collectInOrder(tasks) {
  const values = [];
  for await (const value of tasks) values.push(value);
  return values;
}

collectInOrder([Promise.resolve("first"), Promise.resolve("second")])
  .then(values => console.log(values)); // ["first", "second"]
~~~

See [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) for Promise aggregation and host scheduling. Browser and Node event-loop details remain in [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md).
