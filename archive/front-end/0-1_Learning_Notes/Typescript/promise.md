# Promises in TypeScript / TypeScript 中的 Promise

**Core idea / 核心概念：** A Promise is a JavaScript runtime object; TypeScript’s generic type parameter is erased and does not validate values at runtime. The Promise executor runs synchronously, while reactions run later as Promise jobs (microtasks in web hosts). / Promise 是 JavaScript 运行时对象；TypeScript 泛型参数会在编译后擦除，也不会在运行时验证值。Promise 执行器同步运行，后续处理函数作为 Promise 作业（Web 宿主中的微任务）稍后运行。 See [TypeScript’s handbook](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [asynchronous JavaScript](../../../../frontend/javascript/asynchronous-javascript.md), and the [ECMAScript Promise specification](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects).

**1. Introduction to Promises**

- Definition: Represents the eventual outcome of an asynchronous operation.
- States:
  - Pending: Initial state.
  - Fulfilled: Operation completed successfully.
  - Rejected: Operation failed.

**2. Creating a Promise**

- Use the Promise constructor.

```typescript
const promise = new Promise<string>((resolve, reject) => {
  setTimeout(() => {
    resolve("Promise is resolved!");
  }, 2000);
});
```

**3. Consuming a Promise**

- Use `.then()` for success and `.catch()` for errors.

```typescript
promise
  .then((value) => console.log(value))
  .catch((error) => console.error("Something went wrong:", error));
```

**4. Error Handling in Promises**

- Use "reject" for errors.

```typescript
const failingPromise = new Promise<string>((resolve, reject) => {
  setTimeout(() => reject(new Error("Promise failed!")), 2000);
});
failingPromise.catch((error) => console.error(error.message));
```

**5. Chaining Promises**

- Chain multiple `.then()`.

```typescript
function getNumber() {
  return Promise.resolve(21);
}

getNumber()
  .then((num) => num * 2)
  .then((result) => console.log(result));
```

**6. Promise Utility Functions**

- **6.1. `Promise.all()`**: Fulfills with values in input order when all inputs fulfill; rejects when an input first rejects. An empty input fulfills with `[]`. Rejection does not cancel the other operations.

```typescript
Promise.all([Promise.resolve(1), Promise.resolve(2), Promise.resolve(3)])
  .then((values) => console.log(values)); // [1, 2, 3]
```

- **6.2. `Promise.race()`**: Adopts the first input to settle (fulfill or reject); an empty input remains pending.

```typescript
Promise.race([Promise.resolve("first"), Promise.resolve("second")])
  .then((value) => console.log(value)); // "first"
```

**7. Async/Await**

- Syntactic sugar over Promises.

```typescript
async function fetchNumber(): Promise<number> {
  return 42;
}

async function main() {
  try {
    const number = await fetchNumber();
    console.log(number);
  } catch (error) {
    console.error("Error fetching number:", error);
  }
}
main();
```

**Intervals and Timeouts**

- Timer APIs are host-provided (browser and Node handle types differ). Pass a callback; cancellation clears the scheduled callback but does not stop work that has already started.

```typescript
const intervalId = setInterval(() => console.log("tick"), 1000);
clearInterval(intervalId);
```

`setInterval` is a host timer, not part of the ECMAScript Promise API. See the [WHATWG HTML timers section](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers) for browsers and [Node.js timers](https://nodejs.org/docs/latest-v24.x/api/timers.html) for Node.
