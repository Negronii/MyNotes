# 迭代器与生成器怎样按需产出并清理数据？

## 案例背景

报表页面已经取得并[校验了报表 42 的基础资料、摘要和权限](./asynchronous-javascript.md#报表请求何时并发、何时顺序等待？)，确认用户有权读取明细。接下来要用同一个报表 ID、当前排序方式和页面的 `AbortSignal`（中止信号，用于取消请求）读取表格行。行接口是分页的：每页返回若干行和下一页的 cursor（游标），下一页的地址要等当前响应给出游标后才知道。页面希望逐行追加到表格中，找到目标行或用户取消时就停止。本章所说的“清理”指关闭迭代器并释放它持有的资源，不是删除报表行。

这条链路有两层“按需”：浏览器 Fetch API 的 `fetch` 和 `response.json()` 先取得并解析**一整页**，异步生成器再把这一页的行逐个交给消费者。消费循环 `await appendRow(row)` 完成当前行后才要下一项；当前页的行交付完毕，生成器才请求下一页。所以它是按行、按页按需，而不是逐字节读取响应体。由于下一页 URL 依赖上一页返回的游标，页与页只能顺序请求；如果接口一开始就提供独立的页码或分片，才可以按顺序要求、失败策略和资源限制，在串行和[有界并发池](./bounded-async-concurrency.md)之间选择。

要实现这种逐项交付，先要了解 JavaScript 的迭代协议。

## 可迭代对象怎样交给消费者逐项读取？

iterable（可迭代对象）负责告诉消费者如何取得 iterator（迭代器），迭代器再一项一项地交出值。普通可迭代对象通过 `Symbol.iterator` 提供同步迭代器；异步可迭代对象通过 `Symbol.asyncIterator` 提供异步迭代器。同步迭代器的 `next()` 当场返回 `{ value, done }` 结果对象；异步迭代器的 `next()` 返回 Promise，兑现值才是这种结构。消费者拿到结果对象后，把 `done` 当作布尔值判断：为真表示结束，为假则消费 `value` 后继续要下一项。缺少 `done` 等同于假；表示结束的结果可以省略 `value`。

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

可迭代对象每次可以给出一个新迭代器，也可以总是返回自身，协议并不保证能重复遍历。下面的 `range` 和数组一样，每次都提供新迭代器；而生成器对象（下一节介绍）的迭代器就是它自己，只能遍历一次：

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

展开语法、`for...of`、数组解构等消费者各自按规则使用这个协议。迭代器只规定“怎样取得下一项”，并不保证生产者内部没有预取、缓存或副作用。

像 `range` 这样手写迭代器需要自己保存进度。生成器把进度保存在暂停的函数体里，写起来更直接。

## 生成器怎样暂停、接收值并委托工作？

`function*` 声明 generator function（生成器函数）。调用它会创建一个生成器对象：参数绑定和默认参数表达式在调用时就处理，但函数体要到第一次 `next()` 才开始执行。每次 `yield` 暂停函数体并产出一个值；之后调用 `next(value)` 恢复执行，暂停处的 `yield` 表达式求值为传入的 `value`。第一次 `next(value)` 时还没有暂停的 `yield` 来接收，所以参数被忽略。

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

`return` 的值放在最后结果的 `value` 中，但 `done: true` 表示序列已经结束，它不算一项普通产出（`for...of` 和展开语法都会忽略它）。下面验证调用时机：调用生成器时默认参数已经求值，函数体内的 `try`、日志等副作用还没有运行。对尚未启动的生成器调用 `return()`，它直接结束：

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

生成器已经启动并暂停在 `yield` 时，调用 `return(value)` 相当于在暂停点执行一次 `return`。若暂停点位于 `try` 中，`finally` 会运行；但 `finally` 里也可以再 `yield` 暂停：

~~~javascript
function* withCleanupYield() {
  try {
    yield "row";
  } finally {
    yield "cleanup step";
  }
}

const cleanupRows = withCleanupYield();
cleanupRows.next();             // { value: "row", done: false }
cleanupRows.return("finished"); // { value: "cleanup step", done: false }
cleanupRows.next();             // { value: "finished", done: true }
~~~

`cleanupRows.return()` 得到 `{ done: false }` 后，并不会自动继续推进；生成器停在 `finally` 里的 `yield` 处。`for...of` 的 `break` 也一样：它只调用一次 `return()`，确认返回值是对象后就退出，不会因为 `done: false` 再调用 `next()`。`for await...of` 会等待这一次异步 `return()` 完成，同样不会重复关闭。所以，如果清理代码在 `yield` 之后还要释放资源，`break` 后那部分会一直挂着不执行：

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

因此，若希望一次关闭就完成资源清理，就不要在清理路径中再 `yield`。`return()` 只是迭代器协议提供的关闭通知，不能强制中断任意工作或宿主资源。

生成器还能用 `yield*` 把一段迭代委托给另一个可迭代对象。委托期间，外部的 `next()` 请求转交给子迭代器的 `next()`（这是迭代器必须实现的方法）；`throw()` 和 `return()` 能否转交，取决于子迭代器有没有实现对应的可选方法。子迭代器自然耗尽时，它结束结果 `{ done: true, value }` 中的 `value` 成为 `yield*` 表达式的值，外层生成器从这里继续执行。借助它可以组合惰性序列，同时拿到子生成器的最终返回值。

委托期间若外部提前关闭，规则如下。对外层调用 `return(v)` 时：子迭代器没有 `return` 方法，外层直接在 `yield*` 处执行这次返回；子 `return()` 给出 `done: false`，外层原样交出这个结果并继续暂停；给出 `done: true`，外层以该结果的 `value` 执行返回，但外层自己的 `finally` 仍可能改写结果。对外层调用 `throw(e)` 而子迭代器没有 `throw` 方法时，委托先尝试调用子迭代器的 `return` 关闭它，然后抛出 `TypeError`（表示协议不匹配）；若关闭过程本身抛错，则传播关闭错误。不涉及委托时，直接对暂停的生成器调用 `throw(e)`，会在暂停处抛出 `e`，可被生成器的 `catch` 捕获，或在经过 `finally` 后向外传播：

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

同样的暂停与恢复机制可以按需生成无限序列。无限生成器不会自己结束，消费者必须在拿够数据后主动停止：

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

序号也可以按需生成，不必预先分配一个大数组。下面的 ID 只在同一个生成器实例内、计数不超过 JavaScript 安全整数范围时保证唯一；不同实例使用同一前缀会产生重复 ID：

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

前面已经看到 `break` 会调用 `return()`。更一般地说，循环体通过 `break`、`return` 或抛错提前离开时，`for...of` 会尝试调用迭代器的可选方法 `return()`。生成器把这次关闭请求变成暂停点处的 `return`，因此已进入 `try` 的生成器会运行 `finally`；生成器持有的资源应在这个 `finally` 中清理。下面的手写迭代器直接实现了 `return()`：

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

“关闭”只表示消费者不再要下一项，并不表示迭代器一定释放了所有外部资源。还要注意错误来自哪里：若同步迭代器的 `next()` 自己抛错，或原生异步迭代器的 `next()` 返回的 Promise 拒绝，循环直接传播该错误，不会调用 `return()`。若是循环体抛错，循环会请求关闭；关闭方法若也抛错，优先传播的仍是循环体的原错误。正常 `break` 时关闭方法抛错，则会传播关闭方法的错误。对需要可靠清理的资源，应把它放在生成器自己的 `try/finally` 中，并确认关闭路径没有挂起的 `yield`。

有一种异步情况例外。`for await...of` 遍历的对象没有异步迭代器时，会把同步迭代器包装成异步迭代器，包装器会等待每个 `{ done: false, value }` 中的 `value`。若这个 Promise 或 thenable 拒绝，按 ECMAScript 2026，包装器会先关闭底层的同步迭代器，再传播拒绝；在 Node.js v26.13.0 中用同步生成器实测，确实会进入它的 `finally`。这与 `next()` 自身抛错、或原生异步迭代器的 `next()` 拒绝时不调用 `return()` 不同。

> [!warning] 关闭请求不等于强制取消
> 调用 `return()` 只会执行迭代器自己定义的关闭步骤。若 `next()` 正在等待网络、文件或流，迭代器协议无法打断宿主 API；异步迭代器的关闭请求即使已经排队，也要等正在运行的步骤让出控制权。所以还要同时使用宿主资源自己的取消接口，例如把 `AbortSignal` 传给 Fetch。

异步生成器的 `next()`、`return()` 和 `throw()` 都返回 Promise，这些请求按调用顺序排队。若一个 `next()` 还停在函数体内的 `await` 上，随后调用的 `return()` 不会插队，要等前一个请求完成后才执行关闭路径。这个顺序保证生成器代码不会被并发重入，但不会取消它正在等待的 Fetch。

## 报表行怎样按页异步读取？

回到报表分页。消费分页生成器要用 `for await...of`，先看它怎样取值。它优先使用 `Symbol.asyncIterator`：等待异步迭代器 `next()` 返回的 Promise，然后把结果里的 `value` 原样交给循环体。若对象没有异步迭代方法，它把同步迭代器包装成异步迭代器，包装器还会等待每项的 Promise 或 thenable（带 `then` 方法、能被 Promise 采纳的对象）。异步生成器在 `yield` 时也会先等待被产出的值。因此，当 `value` 本身是 Promise 时，原生异步迭代器、同步包装器和异步生成器这三种来源的表现不同：

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

报表行接口每次返回一页 `items`（行数组）和 `nextCursor`（下一页游标，没有下一页时为 `null`）。分页生成器先等响应、检查 HTTP 状态、读取 JSON 并校验整页结构，再逐行 `yield`；当前页的行全部被消费后，才用游标发起下一次请求。下面沿用报表 42、当前排序和页面的中止信号；每页可以有任意多行。

用一组合成数据逐步展开：页 1 返回 `items: [r-101, r-102]` 和 `nextCursor: "c2"`；页 2 返回 `items: [r-201]` 和 `nextCursor: null`。第一次 `next()` 会取得并验证整页 1，然后停在 `yield r-101`，等待页面追加；下一次拉取才交付 `r-102`。若 `r-102` 是目标行，循环体 `break` 会调用一次异步迭代器的 `return()` 并等待生成器的 `finally` 完成；生成器不会走到更新游标那一步，因此不会请求 `c2`。若继续消费，之后的那次 `next()` 才会读到 `c2` 并请求页 2；页 2 的行交付后，再次拉取遇到 `nextCursor: null` 才自然结束。结构错误的页面在 `validateReportPage` 中、该页第一次 `yield` 之前就会拒绝；重复游标则要等当前页的行都交付后才检查。

| 消费者做什么 | 生成器推进到哪里 | 本次结果 / 是否请求下一页 |
|---|---|---|
| 第一次 `next()` | 请求并校验页 1，暂停在 `yield r-101` | 交付 `r-101`；页 1 还在内存里 |
| 追加完 `r-101` 后再 `next()` | 恢复当前页循环，暂停在 `yield r-102` | 交付 `r-102`；还没更新游标 |
| 目标是 `r-102`，追加后执行 `break` | 一次 `return()` 进入 `finally` | 关闭；不请求 `c2` |
| 若没有停止，追加完 `r-102` 后再 `next()` | 更新游标为 `c2`，请求并校验页 2 | 交付 `r-201` |
| 追加完 `r-201` 后再 `next()` | 发现页 2 的 `nextCursor: null`，结束并清理 | `done: true`；没有下一页 |

> [!example]- 分页生成器与逐行消费者的完整实现
> `appendRow` 返回当前行追加完成的 Promise，并写入本次筛选自己的输出容器；`currentSort`、`selectedRowId`、取消按钮和错误展示函数由页面提供。`appendReportRows` 中的两次信号检查分别守住“开始追加”和“再次拉取”两个边界。
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

内存方面：任一时刻内存里是当前页解析并校验后的 `page.items` 数组，生成器逐项交付这些行，不会把整份报表合并成一个大数组。消费者处理完一行才继续拉取，这形成了一种 backpressure（背压），但它只约束经由拉取产生的工作，生产者若自己在后台预取则不受约束。`seenCursors` 记录见过的游标，防止接口重复返回游标导致无限分页；它占用的空间与已读页数成正比。

取消方面：本例的 `finally` 只记录迭代已关闭，真正中止网络请求和响应体读取的是传给 Fetch 的信号。用户取消时，尚未收到响应的请求会被中止；若响应头已到达而 `response.json()` 还在读响应体，这次读取也会拒绝。若取消发生在 `appendRow` 等待期间，已开始的追加无法回滚，这一行仍可能写入当前筛选的 `tbody`。`appendReportRows` 在追加前检查一次信号，防止启动新的追加；追加完成后再检查一次，避免向迭代器要下一项或请求下一页。它只吞掉与当前 `signal.reason` 完全相同的取消原因，其他追加错误仍向上传播。由于取消时 `appendReportRows` 正常返回，页面的刷新处理器不会进入 `catch`，而是由 `finally` 关闭 loading。切换筛选时，页面先递增请求序号，再中止旧信号、替换旧 `tbody`；旧的追加即使完成，也只会写进已移除的旧容器。详情见[报表请求的错误由谁接手？](./error-handling.md#报表请求的错误由谁接手？)。

若需要并发处理行，也要另行规定顺序、背压和失败策略；本例的 `appendRow` 必须完成后才会拉取下一行。

## 同步 Promise 数组何时不等于并发收集？

前面提到，`for await...of` 也能消费包含 Promise 的同步可迭代对象，比如 Promise 数组。这时同步包装器按数组顺序逐个等待。这些 Promise 可能在循环开始前就已启动，它们实际完成的先后顺序与循环交付的顺序不一定相同：

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

`Promise.all` 和 `Promise.allSettled` 的结果数组同样按输入顺序排列；区别在于，它们一开始就给每个成员注册处理器。而 `for await...of` 只有轮到某一项时才开始监听它：若后面的 Promise 在前一项还未完成时就拒绝，这个拒绝暂时无人处理，宿主可能报告它为未处理拒绝；若前一项拒绝或一直不完成，循环可能永远走不到后面的项。所以用 `for await...of` 遍历已启动的 Promise 数组不是稳妥的并发收集方式。未处理拒绝的报告时机因宿主而异。

最后补充一段历史：在 async/await 标准化之前，`co` 等库用生成器表达异步流程。执行器（runner）读到 `yield promise` 后等待它，成功时用 `next(value)` 把结果送回生成器，失败时用 `throw(error)` 在暂停处抛出。了解这个模式有助于维护旧代码；现代的 `async function` 有自己的 Promise 语义，不会暴露生成器对象。

> [!info]- 来源
> - **迭代协议、关闭、生成器委托和异步适配：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，2026 年正式版。§7.4.11、§7.4.14 定义同步/异步 IteratorClose；§14.7.5.7 定义 `for...of` / `for await...of` 的遍历与关闭；§15.5.5 定义生成器函数和委托；§27.1.5.4 定义同步迭代器 Promise 值的异步适配与拒绝关闭；§27.5、§27.6 定义生成器状态和异步生成器请求排队。
> - **Promise 组合和输入顺序：**[ECMAScript 2026 §27.2.4](https://tc39.es/ecma262/2026/#sec-properties-of-the-promise-constructor)，正式版。§27.2.4.1 与 §27.2.4.2 分别定义 `Promise.all`、`Promise.allSettled` 对 iterable 的遍历和按输入位置收集结果。
> - **分页请求的取消、HTTP 响应与读取响应体：**[Fetch Standard：Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch) 与 [Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard，核对日期：2026-11-12（标准标注的最近更新为 2026-10-19）。HTTP 非成功状态仍是一个 Response；调用者要检查状态。取消 Fetch 与撤回服务端已经执行的业务副作用不是同一保证。
> - **异步工作未及时安装拒绝处理时的宿主报告：**[WHATWG HTML 8.1.4.7 Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)，Living Standard，核对日期：2026-11-12（标准标注的最近更新为 2026-11-11）。HTML 按报告时是否已被处理派发事件；Node.js 等其他宿主有各自的报告机制。
> - **Node 实际运行：**Node.js v26.13.0；检查生成器启动/关闭、`yield*` 方法缺失分支、异步关闭等待、异步生成器排队、原生异步迭代器与同步适配器的 Promise 值差异、拒绝处理观察及同步适配器关闭。loopback 分页只覆盖两个固定游标页、坏结构、重复游标、目标行提前停止、Fetch 等待期中止和响应体读取期中止，不代表真实网络时延。
