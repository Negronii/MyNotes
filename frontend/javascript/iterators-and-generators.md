# Iterators and Generators / 迭代器与生成器

**Key terms / 关键词:** iterable 可迭代对象 · iterator 迭代器 · iterator result 迭代结果 · generator 生成器 · async iteration 异步迭代

The iterable/iterator protocols were standardized in ES2015. An iterable supplies an iterator through Symbol.iterator. An iterator supplies successive results through next(). This protocol powers for...of, array spread, and array destructuring; Array.from accepts either an iterable or an array-like input. An object is not iterable just because it has numeric keys or a length. / 可迭代对象/迭代器协议属于 ES2015。可迭代对象通过 Symbol.iterator 提供迭代器；迭代器通过 next() 提供后续结果。for...of、数组展开和数组解构都使用该协议；Array.from 接受可迭代对象或类数组输入。对象有数字键或 length 并不自动意味着它可迭代。

## Iterable and iterator protocols / 可迭代协议与迭代器协议

An iterator result is an object. The consumer converts its `done` property to Boolean; if that property is absent, it acts as `false`. `value` supplies the current item and may be absent when iteration is complete. For example, `{ value: 42 }` is a non-complete result. / 迭代结果是一个对象。消费者会把其 `done` 属性转换为布尔值；若属性缺失，则按 `false` 处理。`value` 提供当前项，迭代完成时可以省略。例如，`{ value: 42 }` 表示尚未完成的结果。

Arrays, strings, Maps, Sets, typed arrays, and arguments objects are language-provided iterables. NodeList is iterable in modern browser DOM implementations, but it is a host API rather than a JavaScript-language collection. Plain objects are not iterable by default. / 数组、字符串、Map、Set、类型化数组和 arguments 对象是语言提供的可迭代对象。现代浏览器 DOM 实现中的 NodeList 也可迭代，但它属于宿主 API，而非 JavaScript 语言集合。普通对象默认不可迭代。

```javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }

for (const [key, value] of new Map([["x", 1], ["y", 2]])) {
  console.log(key, value);
}
```

This reusable range iterable is designed to return a fresh iterator on each Symbol.iterator call. The protocol does not require that: iterator objects and generators often return themselves and are one-shot. The optional return method gives resource-owning iterators a cleanup hook; for...of closes an iterator when `break` or an abrupt completion of the loop body exits iteration. / 这个可重复使用的 range 可迭代对象设计为每次调用 Symbol.iterator 都返回新迭代器；协议并不要求如此：迭代器对象和生成器常常返回自身，因此只能消费一次。可选的 return 方法为持有资源的迭代器提供清理钩子；`break` 或循环体发生异常等控制流离开迭代时，for...of 会关闭迭代器。

```javascript
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
```

```javascript
const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true: the iterator is its own iterable
```

See the [ECMAScript iteration interfaces](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration), [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete), and [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose) algorithms. / 可迭代接口见 [ECMAScript 迭代规范](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration)，结果完成判断和迭代器关闭算法分别见 [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete) 与 [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose)。

## Generators / 生成器

A generator function returns an object that is both iterable and an iterator. yield pauses it and produces a value; the next() call resumes it. The first next(value) argument is ignored because execution has not paused at a yield yet; later values become the result of the suspended yield expression. / 生成器函数返回同时具备可迭代对象和迭代器特征的对象。yield 会暂停函数并产出值；下一次调用 next() 时继续执行。首次 next(value) 的参数会被忽略，因为函数尚未暂停在 yield 表达式上；之后传入的值会成为暂停处 yield 表达式的结果。

```javascript
function* conversation() {
  const name = yield "What is your name?";
  const hobby = yield "Hello, " + name + "! What do you enjoy?";
  return name + " likes " + hobby;
}

const chat = conversation();
chat.next();          // { value: "What is your name?", done: false }
chat.next("Ada");     // { value: "Hello, Ada! What do you enjoy?", done: false }
chat.next("coding");  // { value: "Ada likes coding", done: true }
```

yield* delegates iteration to another iterable or generator, including its completion result. It is useful for composing traversals. / yield* 把迭代委托给另一个可迭代对象或生成器，也会接收其完成结果，适合组合遍历逻辑。

```javascript
function* flatten(items) {
  for (const item of items) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}

[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]
```

## Lazy sequences and control flow / 惰性序列与控制流

Generators compute on demand, which can represent large or infinite sequences without storing every value. The consumer controls how many values to request. / 生成器按需计算，可表示很大或无限的序列，而不必预先保存所有值。消费者决定请求多少项。

```javascript
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
```

The same lazy state can produce identifiers without storing an unbounded array of them. / 同样的惰性状态也可逐个生成标识符，而无需预先保存一个不断增长的数组。

```javascript
function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}

const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
```

Before async/await, libraries such as co used a runner to yield Promises from generators and resume with their results. This is a historical control-flow pattern; async functions standardize a different syntax and runtime protocol, rather than literally exposing a generator implementation. / async/await 出现之前，co 等库会通过 runner 执行生成器：yield Promise，再用结果恢复执行。这是一种历史控制流模式；async 函数标准化了不同的语法和运行时协议，并非直接暴露生成器实现。

```javascript
function* legacyFlow() {
  const response = yield fetch("/api/user");
  return response.json();
}
// A runner must await each yielded value and resume the generator.
```

## Async iteration / 异步迭代

An async iterable (standardized in ES2018) supplies Symbol.asyncIterator; each next() call makes its iterator result available asynchronously. for await...of waits for each next result in sequence, which is useful for streams whose next value becomes available over time. For a synchronous array of independent Promises, Promise.all is usually simpler and handles all rejections together. / ES2018 标准化的异步可迭代对象通过 Symbol.asyncIterator 提供迭代器；每次调用 next() 都会异步提供迭代结果。for await...of 按顺序等待每次 next() 的结果，适用于后续值逐步到达的数据流。同步数组中相互独立的 Promise 通常用 Promise.all 更简单，也能统一处理拒绝。

See [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) for Promise aggregation and host scheduling.

**Interview answer / 面试回答:** An iterable returns an iterator from Symbol.iterator; an iterator’s next() returns value/done results. Generators implement both protocols and suspend at yield. Async iterables use Symbol.asyncIterator and are consumed with for await...of. / 可迭代对象通过 Symbol.iterator 返回迭代器；迭代器的 next() 返回 value/done 结果。生成器自动实现这两种协议，并在 yield 处暂停。异步迭代器使用 Symbol.asyncIterator，通过 for await...of 消费。
