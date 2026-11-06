# How do Node.js event-loop phases and microtask queues interact? / Node.js 事件循环阶段与微任务队列如何交互？

Node runs JavaScript callbacks on an event-loop thread while libuv coordinates timers and I/O through phases. Node's next-tick queue and the Promise/queueMicrotask microtask queue are separate scheduling mechanisms; their order depends on where code runs. Give the Node version and execution context before stating an order. / Node 在事件循环线程上运行 JavaScript 回调，libuv 则通过多个阶段协调计时器和 I/O。Node 的 nextTick 队列与 Promise/queueMicrotask 微任务队列是不同的调度机制，执行上下文会影响它们的先后顺序。说明 Node 版本与执行位置后，再给出顺序规则。

**Key terms / 关键术语：** event-loop phase / 事件循环阶段；poll / 轮询阶段；microtask / 微任务；process.nextTick / nextTick 队列；CommonJS / CommonJS 模块；ES module / ES 模块；timer threshold / 计时器阈值。

~~~mermaid
flowchart TD
    subgraph loop[libuv event-loop phases]
        Timers[Timers] --> Pending[Pending callbacks]
        Pending --> Poll[Poll: I/O]
        Poll --> Check[Check: setImmediate]
        Check --> Close[Close callbacks]
        Close --> Timers
    end
    Operation[Current JavaScript operation completes] --> Tick[Node drains nextTick queue]
    Tick --> Micro[Node drains microtask queue]
    Micro --> LoopNext[Event loop continues]
~~~

The diagram is a simplified loop outline. The idle and prepare phases are internal. A JavaScript operation's completion handling occurs around the loop and is not itself another libuv phase. ES module evaluation already runs within microtask processing, which explains why the top-level CommonJS and ES module examples below differ.

## What the event-loop phases do / 事件循环阶段各自做什么

| Phase | Main role |
|---|---|
| Timers | Run timer callbacks once their minimum delay threshold has passed; the requested delay is not an exact deadline. |
| Pending callbacks | Run certain I/O callbacks deferred from an earlier loop iteration. |
| Poll | Retrieve and process I/O events; it may wait for I/O when appropriate. |
| Check | Run callbacks scheduled with setImmediate. |
| Close callbacks | Run selected close events, such as a socket close after abrupt destruction. |
| Idle and prepare | Internal libuv phases. |

In libuv 1.45.0, used by Node.js 20 and later, timers run after poll on each loop iteration; earlier versions also ran timers before poll. This changes some timer/immediate timing relationships. At top level, do not rely on a fixed order between setTimeout(fn, 0) and setImmediate(fn). Inside an I/O callback, setImmediate runs in the check phase after poll; the official guide describes it as running before the timer in that situation.

~~~javascript
const fs = require('node:fs');

// At top level, the order can vary.
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));

// Inside an I/O callback, setImmediate runs in the check phase.
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer after I/O'), 0);
  setImmediate(() => console.log('immediate after I/O'));
});
~~~

## How do nextTick and microtasks differ by module context? / nextTick 与微任务顺序如何受模块上下文影响？

The nextTick queue is drained after the current JavaScript operation finishes and before the event loop continues. Promise handlers and queueMicrotask callbacks use the microtask queue. In CommonJS top-level execution, nextTick callbacks run before Promise/queueMicrotask callbacks. ES module evaluation itself runs as microtask work, so its top-level Promise/queueMicrotask callbacks run before nextTick callbacks.

| Context | Ordering for the calls below |
|---|---|
| CommonJS top level | process.nextTick, Promise reaction, queueMicrotask |
| ES module top level | Promise reaction, queueMicrotask, process.nextTick |

~~~javascript
// Save as example.cjs
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// nextTick
// promise
// microtask
~~~

~~~javascript
// Save as example.mjs
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// promise
// microtask
// nextTick
~~~

Current Node.js documentation marks process.nextTick as Legacy and recommends queueMicrotask for most userland deferrals. A recursively replenished nextTick queue can starve I/O because the loop cannot reach poll until the queue drains. Keep nextTick only when its particular scheduling boundary is required by existing API behavior.

One historical use is making a callback-based API consistently asynchronous, including validation errors, so the caller can finish setting up state before the callback runs. Another is emitting a readiness event on the next tick so callers can register a listener after construction:

~~~javascript
const { EventEmitter } = require('node:events');

function createEmitter() {
  const emitter = new EventEmitter();
  process.nextTick(() => emitter.emit('ready'));
  return emitter;
}

const emitter = createEmitter();
emitter.on('ready', () => console.log('ready'));
~~~

Use queueMicrotask for ordinary portable deferral unless the API depends on nextTick-specific ordering. These rules describe Node's host queues; they do not define browser scheduling. [Asynchronous JavaScript / 异步 JavaScript](../../frontend/javascript/asynchronous-javascript.md) covers Promise behavior outside Node's host phases.

**Related notes / 相关笔记：** [Node.js scheduling and worker choices / Node.js 调度与 worker 选择](node-js-fundamentals.md) applies these host queues to server workloads; [Processes, Threads, and Concurrency / 进程、线程与并发](../operating-systems/processes-threads-and-concurrency.md) explains the execution resources used for CPU work.

**Sources / 来源：** [Node.js event-loop phases and timer behavior](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) and [Node.js v26 process.nextTick / queueMicrotask guidance](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), checked 2026-11-05. The CJS and ESM output examples were checked on Node.js v26.11.1; the libuv timer phase change is documented for libuv 1.45.0 (Node.js 20).
