# 迭代器与生成器怎样按需产出并清理数据？

## 案例背景

报表 42 的[基础资料、摘要和权限已校验](./asynchronous-javascript.md#报表请求何时并发、何时顺序等待？)；用户有权读取明细。页面要用同一个报表 ID、当前排序和页面的 `AbortSignal`（中止信号）读取行。接口每页返回若干行和下一个 `cursor`（游标），而下一页的地址要等当前响应给出游标后才知道。页面希望逐行追加；找到目标行或用户取消时停止。本章所说的“清理”是关闭迭代器并处理它持有的资源，不是删除报表行。

这一条链路包含两个不同的按需边界：浏览器 Fetch API（网络请求接口）的 `fetch` 和 `response.json()` 先取得并解析**一整页**，异步生成器再把该页的行逐项交给消费者。本例循环等待 `await appendRow(row)` 完成当前行后，才请求下一项；当前页的行交付完毕后，生成器才请求下一页。它不是逐字节读取响应体。由于本接口下一页 URL 必须依赖上一页返回的游标，页与页之间必须顺序请求；若接口一开始就提供了独立页码或分片，可再按顺序需求、失败策略和资源限制选择串行或[有界并发池](./bounded-async-concurrency.md)。

## 可迭代对象怎样交给消费者逐项读取？

iterable（可迭代对象）告诉消费者如何取得 iterator（迭代器）。普通可迭代对象通过 `Symbol.iterator` 提供同步迭代器；异步可迭代对象通过 `Symbol.asyncIterator` 提供异步迭代器。同步迭代器的 `next()` 当场返回 `{ value, done }` 结果对象；异步迭代器的 `next()` 返回 Promise，兑现值才是这种结构。消费者读取结果对象后，把 `done` 转成布尔值：真表示结束，假表示消费 `value` 后继续。缺少 `done` 等同于假；结束结果的 `value` 可以省略。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }
~~~

数组、字符串、`Map`、`Set`、类型化数组和 `arguments` 对象都能迭代；普通对象仅有 `length` 或数字键，并不会因此可迭代。Document Object Model（文档对象模型，DOM）的 `NodeList`（节点列表）也可迭代，但它是宿主接口，集合实时变化还是静态快照由具体接口决定，见[DOM 集合何时实时变化？](../browser-apis/dom-collections.md)。

~~~mermaid
flowchart TD
  A["同步 iterable<br/>Symbol.iterator()"] --> B["iterator.next() 返回 result"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["消费 result.value"]
  D --> B
  C -- "true" --> E["结束"]
~~~

`iterable` 每次可以给出一个新迭代器，也可以返回同一个自身；协议并不保证可重用。数组每次通常提供新迭代器，而生成器实例是一次性状态机：

~~~javascript
const range = {
  start: 1,
  end: 3,
  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) return { value: current++, done: false };
        return { value: undefined, done: true };
      }
    };
  }
};

[...range]; // [1, 2, 3]
[...range]; // [1, 2, 3]，每次创建新的迭代器

const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true
[...oneShot]; // [1]
[...oneShot]; // []
~~~

展开语法、`for...of`、数组解构等消费者会按各自的规则使用这个协议。迭代器描述的是“怎样取得下一项”，不保证生产者内部没有预取、缓存或副作用。

## 生成器怎样暂停、接收值并委托工作？

`function*` 声明 generator function（生成器函数）。调用它会创建一个生成器对象，参数绑定和默认参数表达式在调用时处理，但函数体要到第一次 `next()` 才开始执行。每次 `yield` 暂停函数体并产出值；后续的 `next(value)` 恢复它，暂停处 `yield` 表达式的值就是传入的 `value`。第一次 `next(value)` 没有已暂停的 `yield` 可接收，所以参数被忽略。

~~~javascript
function* conversation() {
  const name = yield "你叫什么名字？";
  const hobby = yield "你好，" + name + "！你喜欢做什么？";
  return name + "喜欢" + hobby;
}

const chat = conversation();
chat.next("这个参数无人接收"); // { value: "你叫什么名字？", done: false }
chat.next("Ada");              // { value: "你好，Ada！你喜欢做什么？", done: false }
chat.next("编程");             // { value: "Ada喜欢编程", done: true }
~~~

最后一个 `return` 值放在 `value` 中，但 `done: true` 表示序列已经结束；它不是又一项普通产出。调用生成器时参数默认值可以运行，函数体内的 `try`、日志或副作用则还没有运行：

~~~javascript
const events = [];
function* sample(label = (events.push("参数初始化"), "报表")) {
  events.push("函数体开始：" + label);
  try {
    yield "第一行";
  } finally {
    events.push("清理");
  }
}

const rows = sample();
events; // ["参数初始化"]
rows.return("未启动"); // { value: "未启动", done: true }
events; // ["参数初始化"]；未开始的函数体没有进入 try/finally
~~~

当生成器已经开始并暂停在 `yield` 时，调用 `return(value)` 会把一次 return 控制流送回暂停点。若暂停点位于 `try` 中，`finally` 会运行；但 `finally` 自己也可以暂停：

~~~javascript
function* withCleanupYield() {
  try {
    yield "row";
  } finally {
    yield "cleanup step";
  }
}

const rows = withCleanupYield();
rows.next();             // { value: "row", done: false }
rows.return("finished"); // { value: "cleanup step", done: false }
rows.next();             // { value: "finished", done: true }
~~~

`rows.return()` 收到 `{ done: false }` 后不会继续替调用者拉取；生成器还暂停在 `finally` 里的第二个 `yield`。同样，`for...of` 的 `break` 只调用一次 `return()`，检查返回值是对象后便退出，不会因 `done: false` 再请求 `next()`。异步循环会等待这一次异步 `return()` 完成，但也不会重复关闭；所以清理代码若在 `yield` 后还要释放资源，`break` 后那部分仍可能悬停：

~~~javascript
const cleanup = [];
function* rowsWithCleanupYield() {
  try {
    yield "row";
  } finally {
    cleanup.push("开始清理");
    yield "清理步骤";
    cleanup.push("完成清理");
  }
}

const rowsToStop = rowsWithCleanupYield();
for (const row of rowsToStop) break;
cleanup; // ["开始清理"]；循环只调用一次 return()
rowsToStop.next();
cleanup; // ["开始清理", "完成清理"]；必须显式再恢复才完成
~~~

因此资源清理若要求一次关闭就完成，不要在清理路径中再次 `yield`。`return()` 是迭代器协议提供的通知，不是对任意工作或宿主资源的强制中断。

生成器还能通过 `yield*` 把一段迭代委托给另一个可迭代对象。后续 `next` 请求交给子迭代器必需的 `next()`；`throw` 和 `return` 的转发则取决于子迭代器是否实现对应方法。自然耗尽时，子迭代器的结束结果 `{ done: true, value }` 中的 `value` 成为 `yield*` 表达式的值，外层从该表达式之后继续；这能组合惰性序列并保留子生成器的最终结果。

强制关闭时，外部对外层调用 `return(v)`：若子迭代器没有 `return`，外层继续处理这次返回；若子 `return()` 给出 `done: false`，外层还可继续暂停，若给出 `done: true`，外层以这个子结果的 `value` 继续返回，但自己的 `finally` 仍可能改写结果。外部调用 `throw(e)` 而子迭代器没有 `throw` 时，委托会先尝试调用它可选的 `return` 来关闭。无论有没有 `return`，之后都会抛出 `TypeError`；若关闭本身先抛错，则传播关闭错误。直接对暂停中的生成器调用 `throw(e)`，则会在暂停处表现为抛错，可被生成器的 `catch` 捕获或沿 `finally` 展开：

~~~javascript
function* flatten(items) {
  for (const item of items) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}

[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]

function* child() {
  yield "item";
  return 42;
}
function* parent() {
  return yield* child();
}
const delegated = parent();
delegated.next(); // { value: "item", done: false }
delegated.next(); // { value: 42, done: true }
~~~

同一状态方式可以按需生成无限序列。停止读取的一方必须明确结束遍历，否则无限生成器不会自然结束：

~~~javascript
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

const fib = fibonacci();
fib.next().value; // 0
fib.next().value; // 1
fib.next().value; // 1
fib.next().value; // 2
~~~

序号也能按需生成，不必预分配一个大数组。下面只在同一个生成器实例内、计数没有超过 JavaScript 安全整数范围时保持唯一；不同实例使用同一前缀仍可能产生相同 ID：

~~~javascript
function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}

const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
~~~

## 提前退出如何通知迭代器清理？

`for...of` 在循环体执行 `break`、`return` 或抛错等突然控制流离开时，会尝试调用迭代器可选的 `return()`。生成器把这次关闭请求变成暂停点处的 return 控制流，因此已进入 `try` 的生成器会运行 `finally`；需要清理生成器持有的资源时，应把清理放在该 `finally` 中：

~~~javascript
const source = {
  [Symbol.iterator]() {
    let value = 0;
    return {
      next() {
        return { value: value++, done: false };
      },
      return() {
        console.log("关闭迭代器");
        return { done: true };
      }
    };
  }
};

for (const value of source) {
  if (value === 2) break; // 退出时调用 return()
}
~~~

“关闭”表示消费者不再要下一项；它不表示迭代器一定释放了所有外部资源。同步 `for...of` 的 `next()` 自身抛错、或原生异步迭代器的 `next()` Promise 拒绝时，循环直接传播该错误，不能假定它还会调用 `return()`。循环体抛错则会请求关闭；若关闭钩子也抛错，原循环体错误仍优先传播，正常 `break` 时关闭钩子抛错则会传播。对需要可靠清理的资源，应把它放在生成器自己的 `try/finally` 中，并确认关闭路径没有挂起的 `yield`。

有一个不同的异步适配分支：`for await...of` 没有原生异步迭代器、改用同步迭代器时，适配器会等待每个 `{ done: false, value }` 的 `value`。若这个 Promise/thenable 拒绝，ECMAScript 2026 的同步转异步适配器会先关闭底层同步迭代器，再传播拒绝；本机 Node.js v26.13.0 对同步生成器实跑时确实进入其 `finally`。这与 `next()` 自身抛错或原生异步迭代器的 `next()` 拒绝不同。

> [!warning] 关闭请求不等于强制取消
> 调用 `return()` 只执行迭代器定义的关闭步骤。若 `next()` 正在等待网络、文件或流，普通同步迭代器协议不能抢占宿主 API；即使异步迭代器的关闭请求排队了，也要等正在运行的步骤让出控制权。应同时使用宿主资源提供的取消接口，例如把 `AbortSignal` 传给 Fetch。

异步生成器中的 `next()`、`return()` 和 `throw()` 都返回 Promise，恢复请求按顺序排队。若一个 `next()` 正等待 `await`，随后调用的 `return()` 不会跳到它前面；它要等当前请求推进后才执行关闭路径。这个次序保证生成器代码不被并发重入，却不取消它等待的 Fetch。

## 报表行怎样按页异步读取？

`for await...of` 优先使用 `Symbol.asyncIterator`：它等待异步迭代器 `next()` 返回的 Promise，但把兑现结果里的 `value` 原样交给循环体。若对象没有异步迭代方法，语法会把同步迭代器适配为异步迭代器；这个适配器还会等待每项的 Promise 或 thenable（带 `then` 方法、可被 Promise 接纳的对象）。异步生成器本身也会等待它的 `yield` 值，所以这三种入口在 `value` 本身是 Promise 时表现不同。`for await...of` 不只接受异步生成器：

~~~javascript
async function compareForAwaitValues() {
  const promiseValue = Promise.resolve("x");
  const nativeAsyncIterator = {
    [Symbol.asyncIterator]() { return this; },
    next() {
      return Promise.resolve({ value: promiseValue, done: false });
    }
  };
  const observed = [];

  for await (const value of nativeAsyncIterator) {
    observed.push(value === promiseValue); // true：原生 async iterator 的 value 未解包
    break;
  }
  for await (const value of [promiseValue]) observed.push(value); // "x"：同步适配器等待 value
  for await (const value of (async function* () { yield promiseValue; })()) {
    observed.push(value); // "x"：async generator 等待 yield 值
  }
  return observed;
}

compareForAwaitValues().then(console.log); // [true, "x", "x"]
~~~

报表接口返回一页 `items` 和 `nextCursor`。页面先等响应、检查 HTTP（超文本传输协议）状态、读取 JSON（JavaScript 对象表示法）并校验整页结构，再逐行 `yield`。只有当前页的行全部消费完毕，生成器才把游标放进下一次请求。下面沿用报表 42、当前排序和页面中止信号；每个响应可能包含任意数量的行，下一页只有非空游标可用时才存在。

把合成输入逐步展开：页 1 返回 `items: [r-101, r-102]` 和 `nextCursor: "c2"`；页 2 返回 `items: [r-201]` 和 `nextCursor: null`。第一次 `next()` 会取得并验证整页 1，然后停在 `yield r-101`，等待页面追加；下一次拉取才交付 `r-102`。若 `r-102` 是目标行，循环体 `break` 调用一次异步迭代器关闭，等待生成器 `finally`，不继续拉取到游标更新步骤，因此不会请求 `c2`。若继续消费，之后的那次 `next()` 才会读到 `c2` 并请求页 2；页 2 的行交付后，再次拉取遇到 `nextCursor: null` 才自然结束。坏结构在 `validateReportPage` 阶段、首次 `yield` 之前拒绝；重复游标则在当前页的行已经交付后检查。

| 消费者做什么 | 生成器推进到哪里 | 本次结果 / 是否请求下一页 |
|---|---|---|
| 第一次 `next()` | 请求并校验页 1，暂停在 `yield r-101` | 交付 `r-101`；页 1 还在内存里 |
| 追加完 `r-101` 后再 `next()` | 恢复当前页循环，暂停在 `yield r-102` | 交付 `r-102`；还没更新游标 |
| 目标是 `r-102`，追加后执行 `break` | 一次 `return()` 进入 `finally` | 关闭；不请求 `c2` |
| 若没有停止，追加完 `r-102` 后再 `next()` | 更新游标为 `c2`，请求并校验页 2 | 交付 `r-201` |
| 追加完 `r-201` 后再 `next()` | 发现页 2 的 `nextCursor: null`，结束并清理 | `done: true`；没有下一页 |

> [!example]- 分页生成器与逐行消费者的完整实现
> `appendRow` 返回当前行追加完成的 Promise，并绑定本次筛选自己的输出容器；`currentSort`、`selectedRowId`、取消按钮和错误展示函数由页面提供。两个信号检查分别守住“开始追加”和“再次拉取”的边界。
>
> ~~~javascript
> function validateReportRow(value) {
>   if (!value || typeof value !== "object" || Array.isArray(value) ||
>       typeof value.id !== "string") {
>     throw new Error("报表行缺少字符串 id");
>   }
>   return value;
> }
>
> function validateReportPage(value) {
>   if (!value || typeof value !== "object" || !Array.isArray(value.items)) {
>     throw new Error("报表分页响应缺少 items 数组");
>   }
>   if (value.nextCursor !== null &&
>       (typeof value.nextCursor !== "string" || value.nextCursor.length === 0)) {
>     throw new Error("nextCursor 必须是非空字符串或 null");
>   }
>   return {
>     items: value.items.map(validateReportRow),
>     nextCursor: value.nextCursor
>   };
> }
>
> async function* reportRows(reportId, sort, signal) {
>   let cursor = null;
>   const seenCursors = new Set();
>
>   try {
>     while (true) {
>       const query = new URLSearchParams({ sort });
>       if (cursor !== null) query.set("cursor", cursor);
>       const response = await fetch(
>         "/api/reports/" + encodeURIComponent(reportId) + "/rows?" + query,
>         { signal }
>       );
>       if (!response.ok) throw new Error("HTTP " + response.status);
>
>       const page = validateReportPage(await response.json());
>       for (const row of page.items) yield row;
>
>       if (page.nextCursor === null) return;
>       if (seenCursors.has(page.nextCursor)) {
>         throw new Error("报表接口重复返回分页游标");
>       }
>       seenCursors.add(page.nextCursor);
>       cursor = page.nextCursor;
>     }
>   } finally {
>     console.log("报表行迭代已关闭");
>   }
> }
>
> async function appendReportRows(reportId, sort, stopAfterId, signal, appendRow) {
>   try {
>     for await (const row of reportRows(reportId, sort, signal)) {
>       if (signal.aborted) throw signal.reason;
>       await appendRow(row);
>       if (signal.aborted) throw signal.reason;
>       if (row.id === stopAfterId) break;
>     }
>   } catch (error) {
>     if (signal.aborted && error === signal.reason) return;
>     throw error;
>   }
> }
>
> const controller = new AbortController();
> cancelButton.addEventListener("click", () => controller.abort(), { once: true });
> appendReportRows(42, currentSort, selectedRowId, controller.signal, appendRow)
>   .catch(showReportError);
> ~~~

每页的 JSON 已解析，验证后的 `page.items` 数组在内存中；生成器逐项交付这些已解析的行，不会把整份报表合成一个数组，也不保证宿主继续保留原始响应字节。消费者每处理完一行才继续拉取，但这种 backpressure（背压）只约束当前拉取、且生产者没有自行后台预取的部分。`seenCursors` 检查重复游标，防止错误响应令后续分页无休止；它占用与已读页数成正比的游标集合。

本例的 `finally` 只记录迭代已经关闭；网络和响应体读取的实际中止由传给 Fetch 的 signal 完成。用户取消时，信号传给 Fetch，可中止尚未收到响应的请求；若响应头已到达而 `response.json()` 仍在读响应体，中止仍可令这次读取拒绝。取消发生在 `appendRow` 等待中时，已开始的追加不能回滚，也仍可能写入当前筛选所显示的 tbody。这个 helper 在追加前检查一次 signal，防止启动新的追加；追加完成后再检查一次，避免向迭代器要下一项或尝试下一页；只有与当前 `signal.reason` 完全相同的取消拒绝会被吞掉，独立追加错误仍会向上传播。取消让分页 helper 正常返回，因此当前刷新处理器不会进入 `catch`，而会在分页返回后由 `finally` 关闭 loading。切换筛选则先递增代号、再中止旧信号、替换旧 tbody；旧追加即使完成，也只会写入已经移除的旧容器。详情见[报表请求的错误由谁接手？](./error-handling.md#报表请求的错误由谁接手？)。

页码预先已知时，页与页可以串行，也可按顺序要求和失败策略用有界并发；当前接口的 `c2` 只能由页 1 给出，因此不能提前请求。`appendRow` 每次须完成后才会拉取下一行；若需并发处理行，也要另行规定顺序、背压和失败策略。

## 同步 Promise 数组何时不等于并发收集？

`for await...of` 也可消费包含 Promise 的同步可迭代对象；同步适配器按输入顺序等待值。Promise 可以在迭代前就启动，实际结局先后与循环交付顺序并不相同。

~~~javascript
let resolveFirst;
let resolveSecond;
const first = new Promise(resolve => { resolveFirst = resolve; });
const second = new Promise(resolve => { resolveSecond = resolve; });

async function collectInInputOrder() {
  const values = [];
  for await (const value of [first, second]) values.push(value);
  return values;
}

const collected = collectInInputOrder();
resolveSecond("second"); // 第二项先履行
resolveFirst("first");
collected.then(values => console.log(JSON.stringify(values)));
// ["first","second"]：交付仍按数组输入顺序
~~~

`Promise.all` 和 `Promise.allSettled` 履行时的结果数组也按输入顺序排列；区别是它们遍历普通数组时就给每个成员安装处理器。若较后的 Promise 在前项仍待定时拒绝，`for await...of` 还没请求到它，宿主之后可能报告这项拒绝暂时未处理；若前项先拒绝或一直未完成，循环可能永远不会走到后项。轮到后项时才观察拒绝，不是稳妥的并发收集方式。未处理拒绝的报告时机因宿主而异。

在 async/await 标准化以前，`co` 等库常用生成器作为控制流接口：runner 读到 `yield promise` 后等待它，成功时把值交给 `next(value)`，失败时用 `throw(error)` 恢复。理解这个模式能帮助维护旧代码；现代 `async function` 有自己的 Promise 语义，并非用户可见的生成器实例。

> [!info]- 来源
> - **迭代协议、关闭、生成器委托和异步适配：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，2026 年正式版。§7.4.11、§7.4.14 定义同步/异步 IteratorClose；§14.7.5.7 定义 `for...of` / `for await...of` 的遍历与关闭；§15.5.5 定义生成器函数和委托；§27.1.5.4 定义同步迭代器 Promise 值的异步适配与拒绝关闭；§27.5、§27.6 定义生成器状态和异步生成器请求排队。
> - **Promise 组合和输入顺序：**[ECMAScript 2026 §27.2.4](https://tc39.es/ecma262/2026/#sec-properties-of-the-promise-constructor)，正式版。§27.2.4.1 与 §27.2.4.2 分别定义 `Promise.all`、`Promise.allSettled` 对 iterable 的遍历和按输入位置收集结果。
> - **分页请求的取消、HTTP 响应与读取响应体：**[Fetch Standard：Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch) 与 [Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard，核对日期：2026-11-12（标准标注的最近更新为 2026-10-19）。HTTP 非成功状态仍是一个 Response；调用者要检查状态。取消 Fetch 与撤回服务端已经执行的业务副作用不是同一保证。
> - **异步工作未及时安装拒绝处理时的宿主报告：**[WHATWG HTML 8.1.4.7 Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)，Living Standard，核对日期：2026-11-12（标准标注的最近更新为 2026-11-11）。HTML 按报告时是否已被处理派发事件；Node.js 等其他宿主有各自的报告机制。
> - **Node 实际运行：**Node.js v26.13.0；检查生成器启动/关闭、`yield*` 方法缺失分支、异步关闭等待、异步生成器排队、原生异步迭代器与同步适配器的 Promise 值差异、拒绝处理观察及同步适配器关闭。loopback 分页只覆盖两个固定游标页、坏结构、重复游标、目标行提前停止、Fetch 等待期中止和响应体读取期中止，不代表真实网络时延。
