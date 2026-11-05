# In what order do chained Promise reactions run? / Promise 链的反应处理器按什么顺序运行？

A then reaction runs as a Promise job after settlement; its returned value settles the next Promise and may queue later reactions among other chains. Derive the order from the jobs created by the exact program rather than assuming fairness between chains. / then 处理器会在 Promise 敲定后作为 Promise job 运行；其返回值会决定下一 Promise 的状态，也可能使后续反应任务与其他链交错。应按程序实际创建的任务推导顺序，不要假设不同链之间有公平调度。

Returning an already-fulfilled Promise adds adoption work and shifts later reactions in this exact example:

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3))
  .then(() => console.log(5))
  .then(() => console.log(6));

// 0 1 2 3 4 5 6
~~~

Three independently chained handlers interleave as each handler queues the next one:

~~~javascript
Promise.resolve().then(() => console.log(0))
  .then(() => console.log(1)).then(() => console.log(2));
Promise.resolve().then(() => console.log(3))
  .then(() => console.log(4)).then(() => console.log(5));
Promise.resolve().then(() => console.log(6))
  .then(() => console.log(7)).then(() => console.log(8));
// 0 3 6 1 4 7 2 5 8
~~~

Nested Promise returns give this output for the complete program:

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(1);
}).then(() => console.log(2)).then(() => console.log(3));

Promise.resolve().then(() => {
  console.log(4);
  return Promise.resolve(5);
}).then(() => console.log(6)).then(() => console.log(7));
// 0 4 2 6 3 7
~~~

The output belongs to each exact snippet. See [Asynchronous JavaScript](../../../frontend/javascript/asynchronous-javascript.md) for Promise chaining and [Event Loop and Host Scheduling](../../../frontend/runtime/event-loop.md) for the host boundary.

**Specification / 规范:** [ECMAScript 2025 Promise objects and jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects).
