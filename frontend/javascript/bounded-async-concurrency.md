# 怎样限制异步任务的并发并收尾失败？

本章接着[上一章的报表案例](./asynchronous-javascript.md)：页面已经拿到 `reportId="42"`、`sort="recent"` 的报表、摘要和权限三项数据，并通过了运行时校验；权限结果是 `canReadRows === true`，所以现在可以读取报表明细行。明细共五页，页码事先已知。

五页可以同时请求，但服务端或浏览器资源可能有限，本例要求同时进行的任务不超过两个。`2` 只是本案例给定的资源限制，不是所有服务的通用最佳值。页面还持有一个 `AbortController`（中止控制器），用户离开页面时调用 `controller.abort()`；本章把它的 `controller.signal`（`AbortSignal`，中止信号）称为 `pageSignal`。

## 先把任务保持为惰性，再填满空槽位

调用 `fetch(url)` 时，请求立即开始，然后返回一个 Promise。如果先创建五个 Fetch Promise 再交给 `Promise.all`，五个请求在创建时就已全部发出，组合器只能等待结果，无法控制启动时机。

要控制何时启动，就把每项工作写成 task factory (任务工厂)：一个函数，被调用时才发起请求。下面的 `map` 只生成五个 `async` 函数，此时还没有请求任何一页：

~~~javascript
function createPageTasks(reportId, sort) {
  return [1, 2, 3, 4, 5].map(page => async ({ signal }) => {
    const query = new URLSearchParams({
      page: String(page),
      sort,
    });
    const url =
      "/api/reports/" + encodeURIComponent(reportId) + "/rows?" + query;
    const response = await fetch(url, { signal });
    if (!response.ok) throw new Error("页 " + page + " 请求失败");
    return response.json();
  });
}
~~~

接下来由任务池（下文完整代码中的 `runBounded`）调用这些工厂。任务池接收一个同步 iterable (可迭代对象)，其中每一项都必须是函数。它同时最多运行两个工厂调用，调用时传入 `{ signal, index }`，并等待工厂返回的 Promise 结算（履行或拒绝）后才释放这个槽位。池只能看到工厂返回的 Promise：如果工厂启动了其他工作却提前返回，池会释放槽位，而那项工作仍在继续；工厂内部自己并发发起多项工作，池也无法分别限流。

本例的工厂就有这样的情况。Fetch 收到非 2xx 的 HTTP 状态时仍会履行，给出 `Response` 响应对象；工厂检查 `response.ok` 后立即抛错，把它变成任务拒绝，但没有读取或取消这条响应的正文流。于是工厂的 Promise 已经结算、槽位已经释放，正文流却可能还开着。状态成功时，`response.json()` 会继续读取并解析正文，工厂的 Promise 要等这一步结算才释放槽位。因此，`limit` 限制的是池正在等待的任务数，不是实际的 HTTP 请求、连接或响应体流的数量。池只接收每个工厂最终的成功值或失败原因，HTTP 状态和 JSON 格式由工厂自己处理。

池的关键问题是：某个任务失败后怎么办。为了看清过程，下图和后面的时间线把五页缩小成三页合成输入：页 1、页 2 先占满两个槽位，页 2 随后失败，页 3 在等待空出的槽位。

![三项合成分页任务输入任务池：页 1 与页 2 在 t=0ms 占满两个活动槽；页 2 在 t=10ms 以 new Error("B failed") 拒绝，页 1 仍在运行，页 3 尚未启动](resources/bounded-pool-input-failure.svg)

第一张图固定了输入、起始状态和失败时刻：页 1 用 30 ms 得到 `"A"`，页 2 用 10 ms 以 `new Error("B failed")` 失败，页 3 启动后用 20 ms 得到 `"C"`。池支持两种失败策略：`stop` 遇到失败就停止，`collect` 收集每项结果后继续。第二张图展示这个 Error 在两种策略下的不同结局：

![页 2 的 new Error("B failed") 分成 stop 与 collect 两条路径：stop 停止取项、尝试 return 一次、排空页 1 后拒绝；collect 把拒绝写入索引 1，启动页 3，并按输入位置返回 A、错误记录和 C](resources/bounded-pool-outcomes.svg)

页码从 1 开始，工厂的 `index` 从 0 开始，所以页 2 对应 `results[1]`。`collect` 把履行值和拒绝原因分别存进 `value` 与 `reason` 字段，结果按输入位置排列。

池内部的调度过程如下：用 `nextIndex` 记录下一个输入位置，用 `active` 集合保存正在运行的任务（每个任务占一个槽位），用 `peakActive` 记录同时运行任务数的峰值。有空槽位时，它不断取出下一项并启动；槽位填满后，用 `Promise.race` 等待“某个任务结算”或“池收到停止通知”二者中先发生的一个。任务结算会腾出槽位，调度器再把空位填满。每项结果写入 `results[index]`，所以完成先后不会改变结果的位置。

## 用同一条时间线推算成功、失败和继续收集

下面按时间推演两种策略，仍用图中的三个任务工厂，`limit` 为 2。页 1 在启动 30 ms 后履行并给出 `"A"`；页 2 在 10 ms 后以 `new Error("B failed")` 拒绝；页 3 在启动 20 ms 后履行并给出 `"C"`。这些延迟是合成输入，不是网络测量。

| 时刻 | 活动状态 | `failure: "stop"` | `failure: "collect"` |
| --- | --- | --- | --- |
| `0 ms` | 页 1、页 2 启动，活动数 `2` | `peakActive = 2` | `peakActive = 2` |
| `10 ms` | 页 2 拒绝，页 1 仍在运行 | 记录首次失败、停止取项，尝试调用 `return()` 一次；页 3 不启动 | 在结果位置 `1` 记录拒绝，腾出的槽位启动页 3 |
| `30 ms` | 页 1 完成；`collect` 中页 3 也已完成 | 排空后以 `new Error("B failed")` 拒绝池调用 | 按输入位置履行 A、Error 和 C 的三项状态记录，峰值仍是 `2` |

`stop`（停止）是默认策略：池观察到第一个任务失败后，就不再调用新的任务工厂。它停止从输入中取项，并对尚未取完的输入迭代器调用一次 `return()`（如果迭代器提供了这个可选方法，用来通知它提前结束，例如让生成器执行清理），然后等已经启动的任务全部结算（称为“排空”），最后以第一个停止原因拒绝。调用一次 `return()` 不保证迭代器已完成自己的清理。排空只表示池不再有在等的任务，既不会回滚已完成的写入，也不会强行终止忽略 signal 的工作。

`collect`（收集）为每个实际启动的任务保存一条状态记录：`status: "fulfilled"` 表示成功，值在 `value` 字段；`status: "rejected"` 表示失败，原因在 `reason` 字段。它在失败后继续填充空槽位，直到输入取完、活动任务全部结算。没有启动的任务不会有记录。

## Abort 会停止调度，不会强行终止任意 Promise

除了任务失败，用户离开页面也会让池停下。`pageSignal` 收到 `abort` 事件时，池停止取项，对未取完的迭代器尝试调用一次 `return()`，并唤醒正在等待任务结算的调度器。池把同一个信号传给了正在运行的工厂；Fetch 会按自己的中止规则停止请求，但普通 Promise 本身无法被强制终止。如果某个任务忽略信号或永远不结算，池就一直等下去，不会提前结束。

| 时刻 | 池和输入 | 已启动任务 |
| --- | --- | --- |
| `0 ms` | 从页 1、页 2 开始，活动数为 `2` | 两个工厂都收到同一个 `pageSignal` |
| `5 ms`：页面调用 `controller.abort()` | 停止取项，尝试调用迭代器 `return()` 一次，不启动页 3，并立即唤醒调度器 | 支持中止的 Fetch 收到信号；忽略它的工作仍运行 |
| 已启动任务全部结算后 | 用选定的首个停止原因拒绝池调用 | 不会再启动任务；一次 `return()` 不保证迭代器清理已完成 |

任务失败和 abort 都会调用池内部的 `stop(reason)`，停止原因以最先调用的那次为准。比如 stop 策略下若页 2 的失败先被池观察到，后来到达的外部 abort 不会替换这个失败；若 abort 先被观察到，随后到达的任务失败也不会替换中止原因。`collect` 不会因单项任务失败调用 `stop`，但外部 abort 仍会停止整池并拒绝。

页面取消与“任一任务失败就取消兄弟请求”是两项独立策略。本例只把页面生命周期已有的中止信号传给任务，任务失败不会自动调用控制器的 `abort()`。若调用方要求失败时中止仍在途的 Fetch，应定义相应控制器和失败策略。即使 Fetch 中止，也不能撤回服务器已经收到并执行的写操作。

回到报表案例。调用方只在权限校验通过后创建任务，并选用 `collect` 策略，让单页失败不影响其他页：

~~~javascript
const pageSignal = controller.signal;
const pageTasks = createPageTasks("42", "recent");
const { results, peakActive } = await runBounded(pageTasks, 2, {
  failure: "collect",
  signal: pageSignal,
});

for (const [index, result] of results.entries()) {
  if (result.status === "fulfilled") {
    console.log(index, result.value);
  } else {
    console.error(index, result.reason);
  }
}
~~~

若外部 abort、输入迭代器错误或非法任务项使池整体拒绝，`await runBounded(...)` 会抛出原因，不会返回这份 `results`。

如果事先不知道页码，而是每一页都要等上一页返回 `nextCursor` 才能确定，就无法提前构造这组任务，只能从第一页开始顺序读取，[报表行怎样按页异步读取？](./iterators-and-generators.md#报表行怎样按页异步读取？)解释了这种依赖。

## 可折叠查看：有限范围的教学实现

- `limit` 必须是大于 0 的安全整数；`failure` 只能是 `"stop"` 或 `"collect"`。
- 输入是同步可迭代对象，逐项产出的值必须是函数；池只在有槽位时调用它，并以 `{ signal, index }` 调用。
- 池仍在等待的活动任务数不会超过 `limit`；它等待工厂调用返回值的结算，不限制工厂启动但未纳入返回值的底层工作。成功时履行 `{ results, peakActive }`；`stop` 时以首次停止原因拒绝；`collect` 时履行已运行项目的状态和值或原因。
- 外部 abort、同步输入错误和非法任务项都会拒绝整个池，即使 `failure` 是 `"collect"`。输入中尚未取到的项目不会被检查。
- 停止或 abort 后停止取项，并尝试对未耗尽迭代器（iterator）调用一次可选的 `return()`；一次调用不保证迭代器完成自己的清理。清理异常不会覆盖已确定的首个停止原因。池会等待已启动任务的返回值结算。
- 只支持同步可迭代对象；不提供重试、异步迭代、持久配额或持久化。它限制调用工厂的并发，不限制工厂内部额外发起的工作。

还有一种边界情况：池调用 `iterator.next()` 时会运行输入方的代码，这段代码可能同步触发 abort。本实现只处理 `next()` 函数体内同步触发 abort、且返回普通数据属性结果的情况：若返回 `{ done: true }`，池记录输入已取完，不再调用 `return()`；若返回 `{ done: false, value: task }`，池调用一次 `return()`，确认已停止后不启动刚取到的任务。如果结果对象的 `done` 或 `value` 是自定义 getter，读取属性时还会运行其他代码，这种重入情况不在本实现的说明范围内。

> [!example]- 完整代码：runBounded
>
> ~~~javascript
> async function runBounded(tasks, limit, { failure = "stop", signal } = {}) {
>   if (!Number.isSafeInteger(limit) || limit < 1) {
>     throw new RangeError("limit 必须是正整数");
>   }
>   if (failure !== "stop" && failure !== "collect") {
>     throw new TypeError('failure 必须是 "stop" 或 "collect"');
>   }
>   if (tasks == null || typeof tasks[Symbol.iterator] !== "function") {
>     throw new TypeError("tasks 必须是同步 iterable");
>   }
>
>   const iterator = tasks[Symbol.iterator]();
>   if (iterator == null || typeof iterator.next !== "function") {
>     throw new TypeError("tasks 必须产生 iterator");
>   }
>
>   const results = [];
>   const active = new Set();
>   let nextIndex = 0;
>   let activeCount = 0;
>   let peakActive = 0;
>   let exhausted = false;
>   let pulling = false;
>   let returnAfterNext = false;
>   let iteratorReturnAttempted = false;
>   let stopped = false;
>   let stopReason;
>   let wakeStop;
>   const stopSignal = new Promise(resolve => {
>     wakeStop = resolve;
>   });
>
>   function attemptIteratorReturn() {
>     if (iteratorReturnAttempted || exhausted) return;
>     iteratorReturnAttempted = true;
>     const returnMethod = iterator.return;
>     if (returnMethod == null) return;
>     if (typeof returnMethod !== "function") {
>       throw new TypeError("iterator.return 必须是函数");
>     }
>     const result = returnMethod.call(iterator);
>     if (result === null ||
>         (typeof result !== "object" && typeof result !== "function")) {
>       throw new TypeError("iterator.return 必须返回对象");
>     }
>   }
>
>   function attemptIteratorReturnSafely() {
>     try {
>       attemptIteratorReturn();
>     } catch {
>       // 清理错误不覆盖原先确定的失败或 abort reason。
>     }
>   }
>
>   function stop(reason) {
>     if (!stopped) {
>       stopped = true;
>       stopReason = reason;
>     }
>     if (pulling) returnAfterNext = true;
>     else attemptIteratorReturnSafely();
>     wakeStop();
>   }
>
>   const onAbort = () => stop(signal.reason);
>   if (signal) {
>     if (signal.aborted) onAbort();
>     else signal.addEventListener("abort", onAbort, { once: true });
>   }
>
>   async function runTask(task, index) {
>     activeCount++;
>     peakActive = Math.max(peakActive, activeCount);
>     try {
>       const value = await task({ signal, index });
>       results[index] = failure === "collect"
>         ? { status: "fulfilled", value }
>         : value;
>     } catch (reason) {
>       if (failure === "collect") {
>         results[index] = { status: "rejected", reason };
>       } else {
>         stop(reason);
>       }
>     } finally {
>       activeCount--;
>     }
>   }
>
>   try {
>     while (!stopped && !exhausted) {
>       while (!stopped && !exhausted && active.size < limit) {
>         if (signal?.aborted) {
>           stop(signal.reason);
>           break;
>         }
>
>         pulling = true;
>         let step;
>         try {
>           step = iterator.next();
>         } finally {
>           pulling = false;
>         }
>
>         if (step === null ||
>             (typeof step !== "object" && typeof step !== "function")) {
>           throw new TypeError("iterator.next 必须返回对象");
>         }
>         if (step.done) {
>           exhausted = true;
>           returnAfterNext = false;
>           break;
>         }
>         if (returnAfterNext) {
>           returnAfterNext = false;
>           attemptIteratorReturnSafely();
>         }
>         if (stopped || signal?.aborted) {
>           if (!stopped) stop(signal.reason);
>           break;
>         }
>
>         const task = step.value;
>         if (stopped || signal?.aborted) {
>           if (!stopped) stop(signal.reason);
>           break;
>         }
>         if (typeof task !== "function") {
>           throw new TypeError("第 " + nextIndex + " 项不是任务函数");
>         }
>
>         const index = nextIndex++;
>         let tracked;
>         tracked = runTask(task, index).finally(() => active.delete(tracked));
>         active.add(tracked);
>       }
>
>       if (!stopped && active.size > 0) {
>         await Promise.race([...active, stopSignal]);
>       }
>     }
>   } catch (error) {
>     stop(error);
>   }
>
>   if (stopped && !exhausted) attemptIteratorReturnSafely();
>   await Promise.all(active);
>   if (signal) signal.removeEventListener("abort", onAbort);
>   if (stopped) throw stopReason;
>   return { results, peakActive };
> }
> ~~~

`runTask` 在每项任务内部捕获抛错和拒绝，所以 `active` 中的 Promise 都不会拒绝，池可以统一等待它们。`stop` 把首次停止原因留在 `stopReason`；`collect` 则把项的状态写回 `results[index]`。`Promise.race([...active, stopSignal])` 只用于“任一活动任务结算”与“池已停止”之间唤醒调度器；它本身不取消输掉的 Promise。最后的 `Promise.all(active)` 负责排空已启动任务。

首个停止原因优先、尝试调用未耗尽迭代器的 `return()`、以及 abort 后等待活动任务 Promise，是这份 `runBounded` 的应用层契约；ECMAScript 规定同步迭代步骤怎样读取和调用迭代器的 `return()`，DOM/Fetch 规定哪些活动能响应 AbortSignal，但这些标准并没有定义这个教学池的 stop/collect 策略。

> [!info]- 来源
> - **同步迭代器步骤与关闭。** [ECMAScript 2027 草案（2026-11-08）§7.4.4、§7.4.10–7.4.11、§27.8.1.3](https://tc39.es/ecma262/#sec-iteratorclose)，核对日期：2026-11-12。`GetIterator`、`IteratorStepValue`、`IteratorClose` 和生成器的 `return()` 支持同步输入与关闭方法语义；一次生成器 `return()` 可以返回 `done: false`，因此池的单次尝试不保证生成器清理完毕。
> - **Promise 竞速。** [ECMAScript 2027 草案 §27.5.4.5 `Promise.race`](https://tc39.es/ecma262/#sec-promise.race)，核对日期：2026-11-12。它按首个结算输入决定组合 Promise；此处只拿它唤醒调度器，不把它当作活动任务取消机制。
> - **Fetch 响应与正文。** [WHATWG Fetch §2.2.3 Statuses、§5.3 Body mixin、§5.5 Response](https://fetch.spec.whatwg.org/)，Living Standard 更新时间：2026-10-19。`ok` 对应 200–299 状态；`json()` 消费并解析正文，解析可拒绝；Fetch 只有遇到网络错误等失败时才拒绝，HTTP 非成功状态仍可产生 Response。
> - **AbortSignal。** [WHATWG DOM §3 Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)，Living Standard 更新时间：2026-11-11；Promise 本身没有内建 abort，API 可以选择接受、响应或忽略 `AbortSignal`。
> - **Fetch 中止。** [WHATWG Fetch §5.6 Fetch methods — Abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard 更新时间：2026-10-19。Fetch 可响应 signal 并中止 Fetch/响应体处理；这不能撤销远端已发生的副作用。
> - **隔离执行范围。** 使用 Node.js `v26.13.0` / V8 `14.6.202.34-node.40` 实测顺序、`stop` / `collect`、abort、iterator `return()` 和本地 loopback HTTP 响应体场景。图和时间表的 10/20/30 ms 是合成延迟，只表达完成先后，不是网络测量或其他宿主的时间保证。
