# 回调、Promise 与 async 函数怎样组合异步工作？

## 案例背景

用户从 /reports?sort=recent#summary 打开报表页后切换筛选。页面用 Fetch API（浏览器的应用程序编程接口）请求报表 42、摘要和访问权限，检查 HTTP（超文本传输协议）响应并解析 JSON（JavaScript 对象表示法），再把可显示的数据交给界面。三项基础数据全部到达并通过结构校验后，页面再检查权限结果；若允许查看行，就用相同的报表 ID、排序和取消信号单独按页读取表格行。行不是第四项必须同时完成的基础请求。用户离开页面时，应用可能想停止仍可取消的网络工作。

Promise在这条流程中承接每个异步步骤的未来成功值或失败原因；组合与等待它们不等于取消或并行执行 JavaScript 代码。

下图从请求输入走到交付给界面的值。JavaScript 异步机制能组织等待和结果，不会自动取消输掉竞争的操作，也不保证 JavaScript CPU 代码并行运行。

~~~mermaid
flowchart TD
  A["报表筛选：id=42，sort=recent"] --> B["并发发出 3 个 Fetch 请求"]
  B -->|网络失败或中止：Fetch Promise 拒绝| G["拒绝 Promise，交给调用方"]
  B --> C["Promise.all 收到 3 个 Response"]
  C --> D{"检查 HTTP 状态"}
  D -->|有非成功状态| G
  D -->|均可用| E["并发读取响应体"]
  E -->|读取或解析失败| G
  E --> F["运行时校验 JSON 形状"]
  F -->|结构不符合预期| G
  F -->|均有效| H["交付报表、摘要、权限"]
~~~

这里把 Promise 和错误归属拆成两个问题：本章解释等待、组合与超时的机制；[JavaScript 错误应在哪一层恢复、传播或上报？](./error-handling.md#报表请求的错误由谁接手)继续说明哪个调用层有足够上下文处理失败。浏览器或 Node 何时执行回调属于宿主调度，见[浏览器事件循环](../runtime/event-loop.md)和[Node.js 事件循环](../../engineering-foundations/backend/node-event-loop-and-microtasks.md)。

## 回调如何表示延后的工作？

callback（回调）是交给 API（应用程序接口）的函数，API 决定在什么时机调用它：有些异步 API 在稍后调用，有些普通函数（如 map）会在当前调用栈中同步调用回调。事件处理器和计时器使用回调；当后续步骤依赖前一步的结果，层层嵌套会分散成功与失败路径。

~~~javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
~~~

Promise把“稍后成功得到一个值”或“稍后以某个原因失败”表示为可组合的对象。Promise 从 pending（待定）开始，只能完成一次，之后进入 fulfilled（成功）或 rejected（拒绝）状态。

~~~mermaid
stateDiagram-v2
  [*] --> pending
  pending --> fulfilled: 成功完成
  pending --> rejected: 拒绝
  fulfilled --> [*]
  rejected --> [*]
~~~

传给 new Promise 的 executor（执行器）会在构造时同步运行；传给 then 或 catch 的处理器则在 Promise job（Promise 作业）中稍后运行。下面先输出“执行器”，再输出“构造完成”；计时器回调只调用 resolve，最后输出“报表响应已到”的是 then 处理器：

~~~javascript
const pending = new Promise(resolve => {
  console.log("执行器");
  setTimeout(() => resolve("报表响应已到"), 20);
});

console.log("构造完成");
pending.then(value => console.log(value));
~~~

定时器请求一段延迟，不承诺正好在该毫秒执行。这个调度细节由宿主定义，不是 Promise 自己的功能。

## Promise 链怎样传递值和失败？

then 会返回一个新的 Promise，供下一个处理器接续。当前处理器正常返回普通值，下一环节就以该值成功；处理器抛错，下一环节就拒绝；处理器返回 Promise 或 thenable（带 then 方法、会被 Promise 采用的值），新环节会采用它最终的状态和值。

catch 是 then 的拒绝分支：处理器返回普通值或最终履行的 Promise/thenable，才会把后续链恢复为成功；抛错或返回最终拒绝的 Promise/thenable，后续仍是拒绝。Promise.prototype.finally 适合放两种结果都要执行的清理；它会等待回调返回的 Promise/thenable，若清理最终履行就保留原结果，若清理抛错或最终拒绝才替换结果。因此可以 return cleanupPromise 来等待异步清理，但不要靠它的成功值改写业务值。

~~~javascript
async function loadUserAndOrders(userId) {
  const user = await getUser(userId);
  const orders = await getOrders(user.id);
  return { user, orders };
}

loadUserAndOrders("u-42")
  .then(renderOrders)
  .catch(showRequestFailure);
~~~

async function（异步函数）调用时会立即同步执行函数体，直到第一个 await 挂起，或函数体结束；它始终返回 Promise。await（等待运算符）会暂停这个 async 函数，其他 JavaScript 可以继续运行；操作成功后，函数从下一行继续，操作拒绝时则像在该处抛错一样进入 try/catch 或向外传播。try 中的 return 会经过语言级 finally，throw 也可先由 catch 处理；finally 中新的 return/throw 可以替换原完成结果。

## TypeScript 的 Promise 类型能保证什么？

TypeScript 中的 Promise<T> 只是编译期类型信息。泛型在编译后擦除，不会验证服务端 JSON 确实符合 T。来自网络的值要作为不可信输入检查，再交给后续状态：

~~~typescript
async function parseReport(response: Response): Promise<Report> {
  if (!response.ok) {
    throw new Error("报表请求失败，HTTP " + response.status);
  }

  const value: unknown = await response.json();
  return validateReport(value);
}
~~~

validateReport 必须执行实际检查并在形状不符时抛错；仅写上 Promise<Report> 不会增加运行时检查。TypeScript 类型擦除见本页末尾来源。

## 报表请求何时并发、何时顺序等待？

请求本身彼此独立，先把三项工作都启动，再用 Promise.all 收集响应。Fetch Promise 履行时已有 Response 和响应头可供检查，不表示响应体已读取完成；正文要等后面的 json()。若网络失败或中止使其中一个 Fetch 拒绝，第一轮 Promise.all 会立即拒绝；Promise.all 本身不会取消其他已启动请求，但页面可以再中止共用的 signal。若三个 Fetch 都给出 Response，代码才检查状态；此时即使一个状态为 404，也要等这一轮所有 Fetch Promise 都履行后才进入状态检查。读取三个响应体也可以并发。currentSort 是筛选控件当前提交的值；signal 来自页面持有的 AbortController（中止控制器），调用 abort() 可向 Fetch 发出中止信号。validateReport、validateSummary 和 validatePermissions 是按各接口合约编写的运行时校验器：

~~~javascript
async function loadReport(id, sort, signal) {
  const paths = [
    "/api/reports/" + id + "?sort=" + encodeURIComponent(sort),
    "/api/reports/" + id + "/summary",
    "/api/reports/" + id + "/permissions"
  ];

  const responses = await Promise.all(
    paths.map(path => fetch(path, { signal }))
  );

  const failed = responses.find(response => !response.ok);
  if (failed) throw new Error("HTTP " + failed.status);

  const [rawReport, rawSummary, rawPermissions] = await Promise.all(
    responses.map(response => response.json())
  );

  return {
    report: validateReport(rawReport),
    summary: validateSummary(rawSummary),
    permissions: validatePermissions(rawPermissions)
  };
}
~~~

fetch 遇到网络失败会拒绝；HTTP 404 或 500 本身仍会以 Response 成功完成，所以要检查 response.ok。响应对象可在响应头可用后先到达，读取 JSON 正文仍可能等待，也可能因中止或无效 JSON 失败。解析或校验失败也会拒绝 async 函数返回的 Promise。调用方可以在有界面上下文的地方显示错误、选择旧数据或继续传播，具体由[错误处理章节](./error-handling.md#报表请求的错误由谁接手)展开。

Promise combinator（Promise 组合方法）按不同条件合并输入结果：

| 方法 | 组合 Promise 的完成条件 | 常见用途与边界 |
| --- | --- | --- |
| Promise.all | 全部成功后按输入顺序返回值；任一拒绝时拒绝 | 多个结果都必需。拒绝不会取消其他操作 |
| Promise.allSettled | 等全部输入完成，返回每项状态和值或原因 | 每项都需汇总，单项失败不提前结束 |
| Promise.any | 第一个成功时成功；全部拒绝时以 AggregateError 拒绝 | 多个备选中接受任一成功 |
| Promise.race | 第一个成功或拒绝决定结果 | 在结果与计时器之间竞速；输家继续运行，除非 API 另有取消机制 |

Promise.all 保留的是传入项的顺序，不是完成顺序。两个异步操作可各自已经启动；组合 Promise 只负责等待与汇总。

### 两个 Promise 结果怎样相加？

> [!example] 两个数字按输入顺序相加
> 输入 A 在 20 ms 后给出 2，输入 B 在 60 ms 后给出 5。尽管 A 先完成，Promise.all 的数组仍对应输入顺序 [2, 5]，相加为 7，组合结果要等 B 完成才成功。
>
> 若输入 A 是 50 ms 后的 10，输入 B 是 30 ms 后的 -12，数组仍为 [10, -12]，结果为 -2。两个运算都已经开始，Promise.all 的拒绝也不会取消另一个运算。

Promise.all([]) 和 Promise.allSettled([]) 会以空数组成功完成；Promise.race([]) 会一直保持 pending；Promise.any([]) 会以 AggregateError 拒绝。这些空输入行为来自 Promise 组合算法。

## 定时器和超时究竟能取消什么？

Promise 本身没有通用的取消方法。Promise.race 返回“谁先完成”的观察结果；它不会通知输掉的工作停止。为报表调用包一层超时，只能保证调用方在超时已触发时得到拒绝，不能保证底层函数停止运行。

### 怎样把定时器延迟包装成 Promise？

Sleep 练习把宿主计时器包成 Promise：resolve 只会在计时器回调运行时发生。100 ms 和 200 ms 是请求延迟，不是测得的实时保证。setTimeout 与 setInterval 是宿主 API：浏览器返回数值 id，Node.js 返回 Timeout 对象，TypeScript 的声明取决于所选宿主类型。

~~~javascript
function sleep(millis) {
  return new Promise(resolve => setTimeout(resolve, millis));
}

const start = Date.now();
sleep(100).then(() => console.log(Date.now() - start)); // 约 100 或更久
~~~

### 怎样让异步操作与计时器竞速？

~~~javascript
function timeLimit(fn, millis) {
  // 示例在 ES module 或 strict mode 中运行，调用方的 this 才会原样传递。
  return function (...args) {
    let timerId;
    const timeout = new Promise((_, reject) => {
      timerId = setTimeout(
        () => reject(new Error("Time Limit Exceeded")),
        millis
      );
    });

    let work;
    try {
      work = Promise.resolve(fn.apply(this, args));
    } catch (error) {
      work = Promise.reject(error);
    }

    return Promise.race([work, timeout])
      .finally(() => clearTimeout(timerId));
  };
}
~~~

包装函数以普通函数返回，因而保留调用者的 this 和参数；try/catch 把 fn 同步抛错转为拒绝。工作先完成时，finally 清除尚未触发的超时；超时先完成时，包装 Promise 拒绝，工作本身却仍可能继续并产生副作用。

> [!info] TypeScript 的 this 参数不改变运行时调用
> 可以用显式 this 参数保留包装函数的调用类型；它会在编译时擦除，不是实际传入的第一个参数。运行时仍要用普通 function 接住调用上下文，并像本例一样以 fn.apply(this, args) 调用原函数；箭头函数捕获外层 this，不适合此处。
>
> ~~~typescript
> type TimedFunction<This, Args extends unknown[], Result> =
>   (this: This, ...args: Args) => Promise<Result>;
> ~~~

> [!example] 50 ms 超时与 100 ms 网络等待
> 假设 fn 在 100 ms 后完成，timeLimit(fn, 50) 的调用方会在计时器获准执行时收到 Time Limit Exceeded。fn 并没有随之取消；它仍可能在之后完成。若改为 150 ms 限制，则工作可以在约 100 ms 后成功返回。
>
> 参数 [5, 10] 在 120 ms 后相加仍得到 15。若 fn 同步抛错，即使限制设为 1000 ms，调用方立即得到拒绝，并由 finally 清除定时器。这里的“约”重要：定时器可晚于请求时刻执行，当前同步代码也不能被定时器打断。

> [!info] 超过限制时间不一定先收到超时拒绝
> 若 fn 同步占用 80 ms 后返回一个已履行的 Promise，而 t 是 50 ms，计时器虽已到期，却要等当前调用栈结束才有机会运行；fn 的 Promise 反应可能先作为微任务执行，使包装结果成功。这是宿主调度下可能发生的结果，timeLimit 不是可抢占的硬截止时间。

真正停止支持取消的 API，需要使用它提供的取消接口。例如把 AbortSignal（中止信号）传给 Fetch，并在页面不再需要请求时调用 AbortController（中止控制器）的 abort()。这会让 Fetch 遵循中止协议，但不能撤销服务器已经收到并执行的请求，也不能逆转已发生的业务副作用。手动计时超时若要中止 Fetch，应让同一个计时器触发 controller.abort()，而不是只拒绝包装 Promise。

### 取消一次或重复定时器时，哪些调用还会发生？

一次性定时器保存返回的 id，取消函数调用 clearTimeout。以下三组输入说明调用时点怎样影响结果；取消时间与计时器都由宿主调度，表里的毫秒数是题目中的理想化示例。

~~~javascript
function cancellable(fn, args, millis) {
  const timerId = setTimeout(() => fn(...args), millis);
  return () => clearTimeout(timerId);
}
~~~

| 输入 | 预期结果 | 原因 |
| --- | --- | --- |
| fn(x)=x*5，args=[2]，t=20，cancelT=50 | 约 20 ms 调用一次，fn 算出 10 | 回调先开始，后续取消不能撤回它 |
| fn(x)=x²，args=[2]，t=100，cancelT=50 | 不调用 | clearTimeout 先移除仍待运行的回调 |
| fn(x,y)=x*y，args=[2,4]，t=30，cancelT=100 | 约 30 ms 调用一次，fn 算出 8 | 回调完成早于取消 |

题目约束是参数数组 1–10 项、t 为 20–1000 ms、cancelT 为 10–1000 ms。表中的 10 和 8 是定时器调用 fn 算出的值；cancellable 的返回值是取消函数，并不会把这些值交给调用者。上面的回调使用 fn(...args) 普通调用；若 fn 依赖 this，应先绑定或显式传入 receiver。

重复计时器的题目要求立即调用一次，再每隔 t 请求一次，cancel 函数清除未来的 interval 回调：

~~~javascript
function cancellableInterval(fn, args, millis) {
  fn(...args); // 第一次同步调用
  const intervalId = setInterval(() => fn(...args), millis);
  return () => clearInterval(intervalId);
}
~~~

| 参数与取消时间 | 题目中的理想调用时刻 | 每次返回值 |
| --- | --- | --- |
| fn(x)=2*x，args=[4]，t=35，cancelT=190 | 0、35、70、105、140、175 ms | 每次为 8 |
| fn(x,y)=x*y，args=[2,5]，t=30，cancelT=165 | 0、30、60、90、120、150 ms | 每次为 10 |
| fn(x,y,z)=x+y+z，args=[5,1,3]，t=50，cancelT=180 | 0、50、100、150 ms | 每次为 9 |

setInterval 不是精确时钟，回调可能晚于请求时刻；clearInterval 不会中断已经开始执行的回调，也不会撤销其副作用。若 fn 依赖 this，示例中的普通函数调用同样不会自动保留 receiver。

clearTimeout 只能清除仍在等待调用的 timeout；clearInterval 停止后续重复回调。二者都不能中断已经开始运行的 JavaScript 回调。Promise 处理器的排队顺序也不是“多等几个 tick 就有公平性”的承诺：规范定义处理器如何排入作业，宿主决定作业何时获得处理机会。

## Promise 处理器为什么会交错？

对多个链条，要从具体代码推导：当前运行的处理器结束后，把它新安排的后续处理器排到队列；已经排队的处理器先执行。返回一个已成功 Promise 时，解析程序还要采用它的最终状态，因此可能加入额外的 Promise 作业。第一段中，log0 返回 Promise.resolve(4)，于是采用作业排在已经安排好的 log1 后面；log1 输出后排入 log2。采用作业再给返回的 Promise 安装后续反应，此时 log2 已排队；log2 输出后排入 log3，后续反应才把输出 4 的处理器排到 log3 后面，所以先看到 3 再看到 4。不要把这次队列追踪换算成跨宿主通用的 tick 数。

先看两条只返回普通值的链：同步代码先把两个首处理器排好；运行第一个后，新排入的第二个处理器排在另一条链已排好的首处理器后面，所以输出交错为 0、2、1、3。

~~~javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// Node.js v26.11.1 CommonJS: 0, 2, 1, 3
~~~

以下三个例子来自原归档练习。它们在 Node.js v26.11.1 的 CommonJS 环境逐段执行，分别得到右侧注释的输出；浏览器宿主自己的事件循环细节另见[事件循环章节](../runtime/event-loop.md)。

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

~~~javascript
Promise.resolve().then(() => console.log(0))
  .then(() => console.log(1)).then(() => console.log(2));
Promise.resolve().then(() => console.log(3))
  .then(() => console.log(4)).then(() => console.log(5));
Promise.resolve().then(() => console.log(6))
  .then(() => console.log(7)).then(() => console.log(8));
// 0 3 6 1 4 7 2 5 8
~~~

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

老式 Promise 反应顺序练习已并入上述三个可重放程序，见[归档入口](../../archive/front-end/Deprecated_Interview_Notes/promise-reaction-order-exercises.md)。Promise、定时器与事件循环分别由 ECMAScript 和宿主规范规定，来源列在本章末尾。

> [!info]- 来源
> - Promise 状态、then/catch/finally、async 函数、迭代和组合方法：ECMAScript 2027 规范（2026-11-05 草案快照），[Promise 对象与作业](https://tc39.es/ecma262/#sec-promise-objects)、[Promise.prototype.finally](https://tc39.es/ecma262/#sec-promise.prototype.finally)、[thenable 采用作业](https://tc39.es/ecma262/#sec-newpromiseresolvethenablejob)、[Promise 组合方法](https://tc39.es/ecma262/#sec-promise.all)、[async 函数](https://tc39.es/ecma262/#sec-async-function-definitions)。处理器队列输出另按原样在 Node.js v26.11.1 CommonJS 重放。
> - 浏览器的 setTimeout/setInterval/clearTimeout：WHATWG HTML Living Standard，2026-11-05 版本，[定时器](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)；标准说明回调不保证精确按延迟执行。
> - Node.js 定时器的延迟与取消：Node.js v26.13.0 文档，[Timers](https://nodejs.org/api/timers.html#timers)。本机重放使用 v26.11.1。
> - Fetch 的 AbortSignal 中止行为：[Fetch Standard，Living Standard 2026-10-19：abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)。该机制可取消 Fetch 的请求/响应处理，不承诺撤回远端已经执行的业务副作用。
> - Promise<T> 类型擦除及类型注解不改变运行时行为：[TypeScript Handbook：Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)。
> - 显式 this 参数在编译时检查并在输出中擦除，且需普通 function 才能接收调用时 this：[TypeScript Handbook：this parameters](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)。
