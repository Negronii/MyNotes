# Event Loop and Host Scheduling / 事件循环与宿主调度

**Key terms / 关键词:** JavaScript agent JavaScript 执行代理 · task 任务 · microtask 微任务 · event loop 事件循环 · libuv libuv

ECMAScript defines language execution and Promise jobs; the host defines event loops, timers, I/O, and rendering. A JavaScript agent executes its jobs one at a time, but browsers and Node can create additional workers or agents. Asynchronous I/O may be handled by the host or operating system; “async” does not mean all work runs on one thread. / ECMAScript 定义语言执行和 Promise job；宿主定义事件循环、计时器、I/O 和渲染。单个 JavaScript agent 一次执行一个 job，但浏览器和 Node 可以创建其他 worker 或 agent。异步 I/O 可能由宿主或操作系统处理；“异步”不表示所有工作都在同一线程运行。

## Browser event loop / 浏览器事件循环

In the HTML event loop, a task such as a script or timer callback runs to completion. A microtask checkpoint then drains queued microtasks, including newly queued microtasks, before the loop proceeds. Promise reactions and queueMicrotask use this queue. Rendering is a separate opportunity controlled by the browser; it is not guaranteed after every task or at a fixed frame boundary. / 在 HTML 事件循环中，脚本或计时器回调等任务会执行到完成。随后进行微任务检查点，清空队列中的微任务（包括执行过程中新增的微任务），再继续循环。Promise 处理器和 queueMicrotask 使用该队列。渲染由浏览器在独立机会中处理；不保证每个任务后立即渲染，也不保证固定帧边界。

```javascript
console.log("start");

setTimeout(() => console.log("timer task"), 0);

new Promise(resolve => {
  console.log("Promise executor runs synchronously");
  resolve();
}).then(() => console.log("Promise reaction"));

console.log("end");

// Typical browser ordering:
// start
// Promise executor runs synchronously
// end
// Promise reaction
// timer task
```

A zero-delay timer is eligible only after its minimum delay and when the host schedules its timer task; it does not mean “run immediately.” The Promise-versus-timer ordering above describes the browser task and microtask model, not the precise timing of rendering. / 零延迟计时器要等到最小延迟满足且宿主调度相应计时器任务后才可运行，并不表示“立即执行”。上例中 Promise 与计时器的先后关系描述浏览器任务和微任务模型，不代表渲染时机。

The [WHATWG HTML event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) defines browser tasks, microtask checkpoints, and rendering opportunities. These browser rules should not be inferred from a Node run. / [WHATWG HTML 事件循环标准](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) 定义浏览器任务、微任务检查点和渲染机会。不能通过 Node 执行结果推断浏览器规则。

## Node.js event loop / Node.js 事件循环

Node uses libuv phases to coordinate timers and I/O callbacks. A useful simplified outline is timers, pending callbacks, poll, check, and close callbacks; idle/prepare are internal phases. The poll phase handles I/O, and setImmediate callbacks run in the check phase. Timer callbacks become eligible after their threshold, not at an exact deadline. / Node 使用 libuv 阶段协调计时器和 I/O 回调。简化来看包括 timers、pending callbacks、poll、check 和 close callbacks；idle/prepare 是内部阶段。poll 阶段处理 I/O，setImmediate 回调在 check 阶段运行。计时器达到阈值后才具备运行资格，并不保证精确截止时间执行。

Since libuv 1.45.0 (Node.js 20), timers run after the poll phase in each loop iteration; earlier versions also ran timers before poll. This affects some timer/setImmediate interactions. At top level, do not rely on a fixed order between setTimeout(fn, 0) and setImmediate(fn); context and timing matter. / 从 libuv 1.45.0（Node.js 20）开始，每轮事件循环中计时器在 poll 阶段之后运行；较早版本还会在 poll 前运行计时器。这会影响部分 timer/setImmediate 交互。在顶层不要依赖 setTimeout(fn, 0) 和 setImmediate(fn) 的固定顺序；上下文和时序都会影响结果。

## Node nextTick and Promise jobs / Node nextTick 与 Promise job

Node has a next-tick queue in addition to the Promise/queueMicrotask queue. Current Node documentation specifies different top-level ordering for CommonJS and ES modules: in CommonJS, nextTick callbacks run before Promise and queueMicrotask callbacks; during ES module evaluation, Promise reactions and queueMicrotask callbacks run before nextTick callbacks. Do not state a module-independent ordering. / 除 Promise/queueMicrotask 队列外，Node 还有 nextTick 队列。当前 Node 文档明确说明 CommonJS 与 ES 模块顶层顺序不同：CommonJS 中 nextTick 回调先于 Promise 和 queueMicrotask 回调；ES 模块求值期间，Promise 和 queueMicrotask 回调先于 nextTick 回调。不能写成与模块类型无关的固定顺序。

```javascript
// CommonJS top level (for example, a .cjs file)
Promise.resolve().then(() => console.log("promise"));
queueMicrotask(() => console.log("microtask"));
process.nextTick(() => console.log("nextTick"));
// Node.js v26.11.1: nextTick, promise, microtask
```

```javascript
// ES module top level (for example, a .mjs file)
Promise.resolve().then(() => console.log("promise"));
queueMicrotask(() => console.log("microtask"));
process.nextTick(() => console.log("nextTick"));
// Node.js v26.11.1: promise, microtask, nextTick
```

Node marks process.nextTick as Legacy starting in Node v20.18.0 and v22.7.0; for most userland deferrals, its current docs recommend queueMicrotask unless nextTick-specific behavior is required. Recursively scheduling nextTick can starve I/O. These are Node runtime rules, not browser behavior. / Node 从 v20.18.0 和 v22.7.0 开始把 process.nextTick 标为 Legacy；当前文档建议大多数用户态延迟场景使用 queueMicrotask，除非确实需要 nextTick 的专有行为。递归调度 nextTick 可能饿死 I/O。这些属于 Node 运行时规则，不是浏览器行为。

The queue examples were run with Node v26.11.1. Current official Node v26 documentation was checked on 2026-10-15: [process.nextTick and queueMicrotask](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), [event-loop phases and the Node 20 timer change](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick). / 队列示例在 Node v26.11.1 中执行。2026-10-15 核对了当前官方 Node v26 文档：[process.nextTick 与 queueMicrotask](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)、[事件循环阶段与 Node 20 计时器变更](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)。

## Garbage collection and retained objects / 垃圾回收与对象保留

ECMAScript does not specify whether an engine uses mark-and-sweep, reference counting, a stack, or a heap, and programs cannot rely on collection at a chosen time. An object that remains reachable through a long-lived reference cannot be reclaimed; cycles alone do not imply a leak. / ECMAScript 不规定引擎必须使用标记清除、引用计数、栈或堆，程序也不能依赖在指定时刻完成回收。对象若仍能从长期存活的引用到达，就不能回收；仅有循环引用并不意味着泄漏。

One implementation model traces from roots such as the global object and active execution state, marks reachable objects, and reclaims unreachable ones; an unreachable cycle can therefore be collected. V8's Orinoco overview describes generations and parallel, incremental, and concurrent GC work. These are engine mechanisms that may change, not ECMAScript requirements. / 一种引擎实现模型是从全局对象、活动执行状态等根开始追踪，标记可达对象并回收不可达对象；因此不可达的循环引用也可回收。V8 的 Orinoco 说明介绍了分代回收，以及并行、增量和并发 GC 工作。这些是可能演进的引擎机制，不是 ECMAScript 要求。

See V8's [Orinoco garbage collector overview](https://v8.dev/blog/trash-talk) for this implementation example. / 这一实现示例见 V8 的 [Orinoco 垃圾回收器说明](https://v8.dev/blog/trash-talk)。

Common retention paths include an uncleared interval, a listener attached to a long-lived object, a detached DOM node still referenced by application code, or a closure retained with values it actually captures. These are investigation leads, not proof that a leak exists. In browser tools, compare heap snapshots around a repeatable action and inspect retained paths. / 常见保留路径包括未清除的 interval、挂在长期存活对象上的监听器、仍被应用代码引用的脱离 DOM 树节点，或闭包实际捕获并长期持有的值。这些只是排查线索，并不能证明已发生泄漏。浏览器工具中可围绕可重复操作比较堆快照，并检查保留路径。

If a subscription, listener, or timer should end before the owning object does, keep its handle and release it at that lifetime boundary. For weak references and their nondeterministic cleanup behavior, see [JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef](../javascript/javascript-memory-weakmap-and-weakset.md). / 若订阅、监听器或计时器应早于所属对象结束，就保存其句柄并在生命周期边界释放。弱引用及其不确定的清理时机见[JavaScript 内存、WeakMap、WeakSet 与 WeakRef](../javascript/javascript-memory-weakmap-and-weakset.md)。

**Interview answer / 面试回答:** The event loop is host-defined. In browsers, tasks run to completion and a microtask checkpoint drains Promise reactions before the host continues; rendering is scheduled separately. Node uses libuv phases and adds nextTick scheduling, whose order relative to Promise jobs differs between top-level CJS and ESM. Always state the host and module context. / 事件循环由宿主定义。浏览器任务执行到完成后会进行微任务检查点，清空 Promise 处理器，再由宿主继续调度；渲染单独安排。Node 使用 libuv 阶段并增加 nextTick 调度，其与 Promise job 的相对顺序在 CJS 和 ESM 顶层不同。说明结论时应给出宿主和模块上下文。

Related: [Asynchronous JavaScript / 异步 JavaScript](../javascript/asynchronous-javascript.md); [Memory, WeakMap and WeakSet / JavaScript 内存、WeakMap 与 WeakSet](../javascript/javascript-memory-weakmap-and-weakset.md).
