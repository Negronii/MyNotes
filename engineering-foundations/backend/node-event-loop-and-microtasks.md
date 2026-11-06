# Node.js 事件循环阶段与微任务队列如何交互？

一个报表请求先排定定时器，再等数据库读回调；两者何时运行取决于当前 JavaScript 操作、event loop（事件循环）阶段和队列。不要只记一个跨所有上下文的“异步先后顺序”：CommonJS 与 ES module 顶层执行中的 nextTick 和 Promise 排序不同，定时器也只承诺最早可运行时间，不是精确截止时刻。

~~~mermaid
flowchart TD
    subgraph loop[libuv 事件循环阶段]
        Timers[Timers：到期定时器] --> Pending[Pending callbacks]
        Pending --> Poll[Poll：I/O 事件]
        Poll --> Check[Check：setImmediate]
        Check --> Close[Close callbacks]
        Close --> Timers
    end
    Operation[CJS 普通 JavaScript 调用返回] --> Tick[清空 nextTick 队列]
    Tick --> Micro[清空 Promise / queueMicrotask 队列]
    Micro --> LoopNext[事件循环继续]
~~~

这张图概括普通 CommonJS JavaScript 操作返回到 Node 调度点后的处理顺序：idle、prepare 是内部阶段；nextTick 和微任务不属于 libuv 的阶段。ES module 求值和正在排空的微任务队列有不同上下文，不能用图中的一条箭头替代后面的条件说明。

## I/O 回调、定时器和 setImmediate() 何时推进？

Node 使用 libuv（Node.js 的跨平台事件循环与异步 I/O 库）管理计时器和 I/O 回调。常见阶段包括 timers、pending callbacks、poll、check 和 close callbacks。poll 取回 I/O 事件并执行相关回调；setImmediate() 在 check 阶段运行；定时器只在给定延迟门槛之后变为可运行，繁忙的回调仍会让它晚于门槛才得到执行。

从 Node.js 20 所用的 libuv 1.45.0 起，定时器在每轮 poll 后运行；较早版本还会在 poll 前运行。不要依赖主模块中 setTimeout(fn, 0) 和 setImmediate(fn) 的固定顺序。在 I/O 回调里排定两者时，setImmediate() 在 check 阶段先运行。

~~~javascript
// save as timers.cjs; output order for the first pair may vary
const fs = require('node:fs');

setTimeout(() => console.log('top-level timeout'), 0);
setImmediate(() => console.log('top-level immediate'));

fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer after I/O'), 0);
  setImmediate(() => console.log('immediate after I/O'));
});
~~~

上例中两条带 top-level 的输出允许不同顺序；I/O 回调中则先输出 immediate after I/O。如果一次同步回调执行 120 ms，即使 setTimeout(..., 100) 已到门槛，它也要等该回调结束才能运行。给 API 设服务端截止时间时，应使用明确的 deadline（截止时间）和可取消操作，不把定时器当作严格准点机制。

## nextTick 与 Promise 微任务的顺序为何会变？

nextTick 队列是 Node 管理的队列；Promise reaction 和 queueMicrotask() 使用 microtask（微任务）队列。在普通 CommonJS 顶层或 callback 返回到 Node 的调度点时，当前 JavaScript 操作先完成，Node 随后处理 nextTick，再排空微任务。ES module 顶层求值本身处于微任务处理中，所以顶层排入的 Promise 和 queueMicrotask 先于 nextTick。

| 代码所在上下文 | 下面三个回调的输出顺序 |
| --- | --- |
| CommonJS 顶层 | nextTick → promise → microtask |
| ES module 顶层 | promise → microtask → nextTick |

保存并分别运行：

~~~javascript
// queues.cjs — Node.js v26.11.1
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

~~~javascript
// queues.mjs — Node.js v26.11.1
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

本机依次运行得到 CommonJS：nextTick, promise, microtask；ES module：promise, microtask, nextTick。Promise 与 queueMicrotask 同属微任务队列，在本例中按排队顺序运行。若代码已经在执行微任务时才排入 nextTick，该 callback 不会插队中断本轮微任务队列；Node 会等当前队列排空后再处理它：

~~~javascript
Promise.resolve().then(() => {
  console.log('microtask A');
  process.nextTick(() => console.log('nextTick from microtask'));
  Promise.resolve().then(() => console.log('microtask B'));
  queueMicrotask(() => console.log('queueMicrotask from microtask'));
});
~~~

Node.js v26.11.1 的本机输出是 microtask A、microtask B、queueMicrotask from microtask、nextTick from microtask。当前 Node 文档把 process.nextTick() 标为 Legacy，多数用户代码应优先选 queueMicrotask()；只有兼容现有 nextTick 排序契约时才保留 nextTick。递归排入 nextTick 会不断清空该队列，令循环迟迟进不了 poll，从而饿死 I/O。

nextTick 曾用于让 callback API 的验证错误也延后到当前调用栈退栈后交付，或者让构造器返回后才发出 readiness 事件，好让调用方先注册 listener：

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

该例运行输出 ready；普通的可移植延后优先使用 queueMicrotask。上述顺序是 Node 宿主的调度契约，不是 JavaScript Promise 语言本身的跨宿主规则。浏览器事件循环见[浏览器事件循环](../../frontend/runtime/event-loop.md)；Node 主线程与 CPU worker 的选择见[Node.js 调度与 worker 选择](node-js-fundamentals.md)。

> [!info]- 来源
> - 阶段、计时器门槛、poll 与 setImmediate()：[Node.js Event Loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)，核对于 2026-11-06；Node.js 20 起的阶段变更对应 libuv 1.45.0。
> - nextTick 队列、CommonJS/ES module 顺序和 Legacy 状态：[Node.js v26.11.1, process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)，三个队列例子于该版本重放。
