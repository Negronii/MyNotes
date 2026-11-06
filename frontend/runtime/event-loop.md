# 浏览器 JavaScript 何时运行，画面何时更新？

案例背景：报表页已经显示 `sort=recent` 的行，`/reports.js` 也已注册 click 处理器，用户点击“最早优先”。如果浏览器正忙，处理器什么时候能运行？处理器改完 URL 和 DOM 后，用户又要等到什么时候才能看到新顺序？沿一次点击走完这两个时间边界。

> [!info] 任务和微任务
> **task（任务）**是宿主安排的工作单元，例如用户输入、计时器回调或网络事件处理。一个 task 中的同步 JavaScript 不会被另一个普通 task 插入执行。**microtask（微任务）**用于当前工作结束后的短小延续，例如 Promise reaction（Promise 处理器）；微任务检查点会清空队列，包括在运行中新增的微任务。ECMAScript 定义 Promise 的语言行为，浏览器宿主定义它们怎样接入事件循环。

~~~mermaid
flowchart TD
    A[执行包含 click 的 task（任务）] --> B[同步处理器运行到返回]
    B --> C[完成 microtask（微任务）检查点]
    C -->|仍有微任务| C
    C --> D[事件循环选择下一项可运行任务]
    D --> E{选中的是渲染更新任务?}
    E -->|是| F[运行该次渲染更新的 requestAnimationFrame 回调]
    F --> G[按需执行样式、布局等渲染步骤]
    G --> C
    E -->|否| H[运行所选任务]
    H --> C
~~~

渲染机会会使用户代理把更新任务排入单独的 rendering task source（渲染任务源）；事件循环随后从可运行任务中选择下一项，选择策略不意味着每个 click 后同步检查一次渲染。图只表示一次交互后可能经过的顺序，不保证每轮都绘制；浏览器也会因刷新率、页面可见性和资源状况推迟或跳过画面更新。

图把这次 click 中 `/reports.js` 的业务处理器简化成一个同步段；真实事件分发还可能调用其他监听器，它们不在这条示例时序里。

## 微任务的先后顺序与让出的边界

~~~javascript
console.log("start");
setTimeout(() => console.log("timer task"), 0);
Promise.resolve().then(() => console.log("Promise reaction"));
queueMicrotask(() => console.log("queued microtask"));
console.log("end");
~~~

当前同步脚本先输出 `start`、`end`。脚本返回时排队的 Promise reaction 和 `queueMicrotask()` 回调按入队顺序在微任务检查点执行；计时器回调是后续 task，只有达到计时器允许执行的时点后才有资格运行。`setTimeout(fn, 0)` 不表示立刻切走，也不承诺下一个画面会先出现。若当前处理器很长，用户点击会等它完成才开始处理；若处理器不断追加微任务，检查点会持续排空队列，浏览器也就迟迟不能处理后续任务或渲染。

`new Promise(executor)` 中的 `executor` 在构造时同步运行；由 `.then()` 注册的 reaction 才排入微任务。上面的例子使用 `Promise.resolve().then()`，所以 `Promise reaction` 出现在同步输出之后。Promise 的语言行为见[异步 JavaScript](../javascript/asynchronous-javascript.md)。

在报表页的例子里，点击发生时可能正有脚本任务占用主线程，这会增加输入延迟。处理器开始后，`pushState()` 和节点修改是同步的；处理器结束后，微任务仍可能继续安排工作，浏览器再看是否有机会更新报表画面。`await Promise.resolve()` 或把工作切成一串微任务并不会主动让浏览器绘制。若计算确实太重，应把有界工作切到后续 task、Web Worker 或适合的框架调度策略；需要确认是哪段时间占用主线程时，沿 [INP 的交互阶段](../performance/performance-metrics-and-analysis.md)看录制结果。

## `requestAnimationFrame` 把写入对齐到渲染更新

若动画或视觉写入需要按渲染更新同步，使用 `requestAnimationFrame(callback)`。回调会在该次渲染更新的常规样式与布局步骤之前运行，参数提供可用于时间计算的高精度时间戳。调用率取决于可用的渲染机会和页面状态；刷新率、后台限速都会影响它，所以它不是固定的 60 Hz 计时器。把变换属性的写入放入 rAF 可以让写入时机与画面同步，但不会让计算免费，也不保证浏览器只做合成工作。DOM/样式写入后读取几何值仍可能触发同步布局，详见[为什么一次 DOM 改动会增加布局或绘制工作？](../html-css/rendering-pipeline-and-forced-layout.md)。

## `requestIdleCallback` 只安排可推迟的小块工作

`requestIdleCallback(callback, { timeout })` 允许用户代理在空闲时段安排低优先级工作。`deadline.timeRemaining()` 是对剩余空闲时间的估计，不是硬性运行预算；每轮处理一个有界单元，剩余工作再排队。即使设置 `timeout`，回调被延迟到超时后也不应因此一次清空无界队列。该 API 并非所有浏览器都支持，需按目标环境检测；用 `setTimeout()` 代替时只能保证之后有一次计时器机会，不能保证当时空闲。

~~~javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift()); // 每次工作仍须有界
  }
  if (workQueue.length) requestIdleCallback(runIdleSlice, { timeout: 2000 });
}

requestIdleCallback(runIdleSlice, { timeout: 2000 });
~~~

React 等框架的 scheduler 是建立在宿主机制上的另一套排程策略，不是浏览器 HTML 规范中的 task source。使用分片调度也不能假定每两个代码块之间浏览器一定会绘制。

**延伸：** [脚本如何影响 HTML 解析与文档就绪？](../html-css/browser-html-and-css.md)说明解析阶段的脚本调度；[DOM 事件如何传播，何时适合事件委托？](../browser-apis/dom-manipulation-and-events.md)说明 click 处理器如何接收事件；[JavaScript 异步](../javascript/asynchronous-javascript.md)解释 Promise 本身的语言行为。Node 有不同的宿主调度边界，见[Node 运行时与调度](../../engineering-foundations/backend/node-event-loop-and-microtasks.md)。

> [!info]- 来源
> - 浏览器任务、微任务检查点、渲染机会和动画帧回调： [WHATWG HTML：Web 应用 API 与事件循环](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)，持续更新规范，事件循环、微任务与更新渲染章节。核对日期：2026-11-06。
> - 空闲回调和 `IdleDeadline`： [W3C `requestIdleCallback()`](https://www.w3.org/TR/requestidlecallback/)，Working Draft，2025-05-21，接口与处理算法章节；[Chrome `requestIdleCallback` guide](https://developer.chrome.com/blog/using-requestidlecallback)，使用建议。核对日期：2026-11-06。
> - Promise 构造器执行器的同步调用： [ECMAScript：Promise 构造器](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-promise-executor)，Living Standard，执行器调用算法。核对日期：2026-11-06。
