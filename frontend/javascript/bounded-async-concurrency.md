# 怎样限制异步任务的并发并收尾失败？

上一章的三项基础报表数据已通过校验，权限结果允许读取行。分页继续使用同一个报表 `id="42"`、排序 `sort="recent"` 和页面已有的 `pageSignal`。现在要按页补齐五个结果，并把同时在途的 Fetch 数限制为 2。

## 先把任务保持为惰性，再填满空槽位

`fetch(url)` 调用时请求就开始；把五个 Fetch Promise 放进 `Promise.all` 仍会启动五个请求。要控制启动时机，输入必须是任务工厂（task factory）：函数被调用时才创建工作。下面的工厂先定义五个请求，池每次只调用有空位的任务：

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

这里的 `map` 只创建函数；尚未请求任何一页。池消费同步 iterable（同步可迭代对象），其中每项都是任务函数；上限是正整数。池把 `{ signal, index }` 交给工厂，工厂再把同一个 `AbortSignal` 交给 Fetch。只有任务被调用后才有 Promise 和网络请求，所以 Promise 集合本身不能冒充限流器。

下面的状态图展示池如何填槽、等待和收尾。一次填槽过程会启动任务，直到达到上限、迭代器耗尽或停止条件触发；等待时只需等一项活动任务结算，随后为每个空槽位各补一项：

~~~mermaid
flowchart TD
  A["填空槽位：调用惰性任务工厂"] --> B{"达到上限、耗尽，或停止？"}
  B -->|未达到且仍有任务| A
  B -->|达到上限| C["等待任务结算或停止通知"]
  C -->|结算后仍可调度| A
  C -->|stop 失败或外部 abort| F
  B -->|迭代器耗尽| D["等待剩余活动任务收尾"]
  D -->|已排空且未停止| E["返回按输入位置排列的结果与峰值"]
  D -->|已停止| H["排空后按首次停止原因拒绝"]
  B -->|stop 失败或 abort| F["立即关闭未耗尽的输入迭代器"]
  F --> G["不再取新项"]
  G --> D
~~~

池主要跟踪三个状态：`nextIndex` 是下一个输入位置，`active` 是仍占调度槽位的任务，`peakActive` 记录执行中任务数的最高值。每项完成后从 `active` 移除；若尚未停止，则每个空槽位最多启动一项，因此一项结束时可能一次补满多个空位。`results[index]` 固定写回输入位置，不按完成顺序排列。

## 用同一条时间线推算成功、失败和继续收集

以下例子把任务缩成三页，便于逐步计算；每页仍是惰性工厂，上限仍为 2。页 1 在 30 ms 后成功返回 `"A"`；页 2 在 10 ms 后以 `"B failed"` 拒绝；页 3 在启动后 20 ms 成功返回 `"C"`。下表的时间是合成输入，不是实测网络延迟：

| 时刻 | 运行状态 | `failure: "stop"` | `failure: "collect"` |
| --- | --- | --- | --- |
| 0 ms | 页 1、页 2 启动，活动数 2 | 两个槽位填满；`peakActive = 2` | 两个槽位填满；`peakActive = 2` |
| 10 ms | 页 2 失败，页 1 仍在运行 | 停止取项并关闭迭代器，页 3 不启动 | 保存页 2 的拒绝记录，空出的槽位启动页 3 |
| 30 ms | 页 1 成功；collect 中页 3 也已成功 | 活动任务排空，池以 `"B failed"` 拒绝 | 返回 `[fulfilled("A"), rejected("B failed"), fulfilled("C")]`，峰值仍为 2 |

`stop` 是默认策略：第一个被观察到的任务拒绝就停止取新项，关闭尚未耗尽的迭代器，再等待已经启动的任务结算，最后拒绝整个池。排空很重要：池不会把“拒绝已返回”伪装成“其他工作已停止”。`collect` 只收集实际运行过的任务工厂的成败，失败释放的槽位会继续填入后续任务；结果仍按输入顺序排列。工厂抛错与返回拒绝 Promise 都算该项失败。

| 情况 | 池的结果 |
| --- | --- |
| 所有任务成功 | 等迭代器耗尽并排空活动任务，返回结果与 `peakActive` |
| `stop` 下某项失败 | 关闭未耗尽迭代器，排空已启动任务，然后以首次观察到的失败原因拒绝 |
| `collect` 下某项失败 | 保存该项的拒绝记录，继续调度；任务失败本身不会拒绝池 |
| 外部 `abort` | 停止取项并立即关闭未耗尽迭代器；把 signal 交给活动任务，排空后以 abort reason 拒绝 |
| 坏任务、迭代器步骤或 abort 出错 | 即使策略为 `collect`，也拒绝整个池；惰性输入中从未取到的元素不会被检查 |

这些状态足以复算“第 2 页先失败”的结局：stop 在 10 ms 关掉输入，页 3 从未启动；collect 在 10 ms 腾出一个槽位来运行页 3，最后三格分别对应页 1、页 2、页 3。若输入有五页，collect 会继续以相同规则启动页 4、页 5。

## Abort 会停止调度，不会强行终止任意 Promise

当 `AbortSignal` 发出事件时，池会立刻停止取项、调用未耗尽同步迭代器的 `return()`，并唤醒正在等待活动任务的调度器。池同时把同一个 signal 交给活动工厂；Fetch 会按 Fetch 的中止协议响应它，通用 Promise 则没有强制停止方法。若任务忽略 signal 或永远不结算，池仍要等它，因此迭代器已经关闭，但池调用还不能结束。

| 时间 | 池与迭代器 | 活动任务 |
| --- | --- | --- |
| 0 ms | 启动任务 1、2 | 两项持有同一个 `pageSignal` |
| 5 ms：页面 abort | 关闭尚未耗尽的任务迭代器，不启动任务 3；等待被唤醒 | Fetch 等参与者按 signal 退出；忽略 signal 的任务继续运行 |
| 所有活动任务结算 | 以 abort reason 拒绝池 | 不会启动新任务 |

`collect` 只影响单项任务失败；abort 仍然拒绝整个池。页面取消与失败时取消兄弟请求也是两个策略：本章把页面已有 signal 传给任务，但任务失败不会自动调用 `abort()`。若产品要求一个任务失败就中止其他请求，应由调用方定义新的控制器和失败传播规则。

~~~javascript
// pageSignal 来自页面已经持有的 AbortController；权限检查已通过。
const pageTasks = createPageTasks("42", "recent");

const { results, peakActive } = await runBounded(pageTasks, 2, {
  failure: "collect",
  signal: pageSignal,
});
// 每个请求使用 /api/reports/42/rows?page=N&sort=recent。
// 页面离开时，既有生命周期代码会调用 pageController.abort()。
~~~

## 可折叠查看：有限范围的教学实现

下面实现面向普通内建 Promise、同步 iterable 和遵守 `AbortSignal` 约定的输入。它不是通用队列：不支持异步迭代器、重试、跨进程配额或持久化。stop、abort、坏任务和迭代器错误都会关闭尚未耗尽的迭代器；调用 `return()` 的清理异常不会覆盖已经确定的停止原因。

关键细节是 `stopSignal`：调度器等待时会同时等待“任一活动任务结算”或“池已停止”。因此外部 abort 能立即唤醒 `Promise.race`，在途任务不必先完成，池就可以关闭输入。若 abort 在同步 `iterator.next()` 内部重入，`pulling` 标记会把关闭延后到这次 `next()` 返回后，并在调用任务工厂前检查停止状态。

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
>   let closeAfterNext = false;
>   let iteratorClosed = false;
>   let stopped = false;
>   let stopReason;
>   let wakeStop;
>   const stopSignal = new Promise(resolve => {
>     wakeStop = resolve;
>   });
>
>   function closeIterator() {
>     if (iteratorClosed || exhausted) return;
>     iteratorClosed = true;
>     const close = iterator.return;
>     if (close == null) return;
>     if (typeof close !== "function") {
>       throw new TypeError("iterator.return 必须是函数");
>     }
>     const result = close.call(iterator);
>     if (result === null ||
>         (typeof result !== "object" && typeof result !== "function")) {
>       throw new TypeError("iterator.return 必须返回对象");
>     }
>   }
>
>   function closeSafely() {
>     try {
>       closeIterator();
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
>     if (pulling) closeAfterNext = true;
>     else closeSafely();
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
>           if (closeAfterNext) {
>             closeAfterNext = false;
>             closeSafely();
>           }
>         }
>
>         if (step === null ||
>             (typeof step !== "object" && typeof step !== "function")) {
>           throw new TypeError("iterator.next 必须返回对象");
>         }
>         if (step.done) {
>           exhausted = true;
>           break;
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
>   if (stopped && !exhausted) closeSafely();
>   await Promise.all(active);
>   if (signal) signal.removeEventListener("abort", onAbort);
>   if (stopped) throw stopReason;
>   return { results, peakActive };
> }
> ~~~
>
> `runTask` 把每项任务的拒绝吸收到自己的结果记录中，因此活动任务都能被最终 `Promise.all(active)` 观察。默认 stop 的拒绝会设置首次 `stopReason`；collect 则按该输入位置写入拒绝记录。迭代器的 `next()`、元素形状或调度错误进入外层 catch，仍会停止整个池。对同步 iterable，`return()` 的调用是同步清理；它不等待正在运行的任务，排空活动任务由后续的 `Promise.all` 完成。

> [!info]- 来源
> - 同步迭代步骤、迭代器关闭、Promise 组合器对同步迭代错误的处理：[ECMAScript 2027 草案，2026-11-03](https://tc39.es/ecma262/) §7.4.6–7.4.11、§27.5.4.1–27.5.4.5；访问于 2026-11-09。本文的池另定义提前停止时调用 `return()` 并排空活动任务的应用层契约。
> - `AbortController` 与 `AbortSignal` 的 abort reason、事件通知和 API 响应约定：[DOM Standard](https://dom.spec.whatwg.org/#aborting-ongoing-activities)，Living Standard 2026-11-04；访问于 2026-11-09。信号观察者按各自 API 契约响应或忽略中止。
> - Fetch 接收 `AbortSignal` 及取消 fetch 处理：[Fetch Standard](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard；访问于 2026-11-09。
> - 本章 `runBounded` 在 Node.js v26.13.0 / V8 14.6.202.34-node.40 运行，2026-11-09。

