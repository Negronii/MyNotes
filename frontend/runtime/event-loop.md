# When does browser JavaScript run relative to a frame? / 浏览器 JavaScript 如何与每一帧交错？

A browser runs one task on a JavaScript agent to completion, then performs a microtask checkpoint that drains Promise reactions and other microtasks, including newly queued ones. A rendering opportunity is a separate user-agent decision: it may update rendering between tasks, but it need not produce a frame after every task or on a fixed 16 ms cadence. `requestAnimationFrame` is for work tied to a rendering update; `requestIdleCallback` is for deferrable work when an idle opportunity is available. / 浏览器中的一个 JavaScript agent 会把当前任务执行完，再进行微任务检查点，清空 Promise 处理器和其他微任务，包括期间新加入的微任务。渲染机会由用户代理单独决定：浏览器可在任务之间更新画面，但不必每个任务后都生成一帧，也不保证固定的 16 毫秒节奏。`requestAnimationFrame` 用于与渲染更新同步的工作；`requestIdleCallback` 用于有空闲机会时可延后的工作。

~~~mermaid
flowchart TD
    T[Run one task to completion] --> M[Microtask checkpoint]
    M -->|more microtasks queued| M
    M --> D{Rendering opportunity now?}
    D -->|no| I[Possible idle callback opportunity]
    D -->|yes| R[Run requestAnimationFrame callbacks]
    R --> U[Update rendering as needed]
    U --> I
    I --> N[Select another task]
    N --> T
~~~

This is a mental model, not a promise that every pass includes rendering or idle callbacks. A long task or endless microtask chain can keep the browser from reaching a rendering opportunity. A zero-delay timer is eligible after its minimum delay; it is not an immediate yield.

~~~javascript
console.log("start");
setTimeout(() => console.log("timer task"), 0);
Promise.resolve().then(() => console.log("Promise reaction"));
queueMicrotask(() => console.log("microtask"));
console.log("end");

// In a typical browser task:
// start
// end
// Promise reaction
// microtask
// timer task
~~~

The Promise executor runs synchronously. Promise reactions and `queueMicrotask` callbacks run as microtasks; the host later chooses when the timer task runs. A microtask added during a checkpoint is processed before the next task.

## Visual updates and `requestAnimationFrame` / 视觉更新与 rAF

Use `requestAnimationFrame(callback)` for an update that should be made before a browser rendering update. Its callback receives a high-resolution timestamp useful for time-based animation. The callback rate follows available rendering opportunities and can vary with refresh rate and page visibility; it is not a fixed 60 Hz timer. Updating a transform in rAF can coordinate a write with rendering, but does not make the work free or guarantee a compositor path.

## Deferrable work and `requestIdleCallback` / 可延后工作与 rIC

`requestIdleCallback(callback, {timeout})` lets the user agent schedule work during an idle period. `deadline.timeRemaining()` is an estimate, not a hard budget. Process a bounded unit and yield again; a timeout is not a reason to drain an unbounded queue. Support varies, so feature-detect it. A `setTimeout` fallback runs at a later timer opportunity but does not provide an idle-time guarantee.

~~~javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift()); // keep each unit bounded
  }
  if (workQueue.length) requestIdleCallback(runIdleSlice, { timeout: 2000 });
}
requestIdleCallback(runIdleSlice, { timeout: 2000 });
~~~

Framework schedulers such as React's scheduler are separate policies layered on host scheduling. Do not treat them as browser task queues or promise that rendering occurs between chunks.

**See also:** [How do scripts affect HTML parsing and document readiness?](../html-css/browser-html-and-css.md) describes parser scheduling; [Why can a CSS change trigger layout, paint, or compositing work?](../html-css/rendering-pipeline-and-forced-layout.md) describes rendering work after DOM changes; [Asynchronous JavaScript / 异步 JavaScript](../javascript/asynchronous-javascript.md) covers language-level Promise behavior.

**Standards / references:** [WHATWG HTML event loops and rendering opportunities](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops); [W3C requestIdleCallback](https://www.w3.org/TR/requestidlecallback/); [Chrome requestIdleCallback guide](https://developer.chrome.com/blog/using-requestidlecallback), checked 2026-11-05.


For the host-specific server contrast, see [Node runtime and scheduling / Node 运行时与调度](../../engineering-foundations/backend/node-js-fundamentals.md).
