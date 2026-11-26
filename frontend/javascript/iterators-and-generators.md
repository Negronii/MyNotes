# 迭代器和生成器怎样按需产出值，提前退出时怎样清理？

本章讲 JavaScript 的迭代协议怎样让消费者一项一项地取值，生成器怎样把取值进度保存在暂停的函数里，以及消费者提前退出时迭代器怎样得到清理机会。读者手上有[上一章的 `loadReport`](./promises-and-async-functions.md#三项请求一起等：loadReport) 交出的已校验权限 `canReadRows === true`，以及[取消一章](./cancellation-timeouts-and-concurrency.md)里 `AbortSignal` 能停住什么的结论。本章沿用主线一的报表页，用一个按游标分页的异步生成器读取报表 42 的行。

## 报表行要按游标逐页读取

行接口是分页的：每页返回若干行和下一页的 cursor (游标)，下一页的地址要等当前响应给出游标后才知道。页面希望逐行追加到列表 `ol#reports`，找到目标行或用户取消时就停止。

这里有两层“按需”。Fetch 和 `response.json()` 先取得并解析**一整页**；异步生成器再把这一页的行逐个交给消费者。消费循环追加完当前行才要下一项，当前页交付完毕生成器才请求下一页。所以它是按行、按页按需，不是逐字节读取响应体。因为下一页 URL 依赖上一页的游标，页与页只能顺序请求；如果接口事先给出独立页码，才可以改用[有界并发池](./cancellation-timeouts-and-concurrency.md#有界并发池：五页明细，同时最多两页)。

本章说的“清理”指关闭迭代器、释放它持有的资源，不是删除报表行。要写出这个生成器，先看迭代协议。

## 迭代协议：iterable 给出 iterator，iterator 逐项交出

iterable (可迭代对象) 负责告诉消费者怎样取得 iterator (迭代器)，迭代器再逐项交出值：

- 同步可迭代对象通过 `Symbol.iterator` 方法给出同步迭代器，它的 `next()` 当场返回结果对象 `{ value, done }`；
- 异步可迭代对象通过 `Symbol.asyncIterator` 给出异步迭代器，它的 `next()` 返回 Promise，履行值才是结果对象。

消费者把 `done` 当布尔值判断：为真表示结束，为假则消费 `value` 再要下一项。缺少 `done` 等同于假；表示结束的结果可以省略 `value`。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }
~~~

~~~mermaid
flowchart TD
  A["同步 iterable<br/>Symbol.iterator()"] --> B["iterator.next() 返回 result"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["消费 result.value"]
  D --> B
  C -- "true" --> E["结束"]
~~~

数组、字符串、`Map`、`Set`、类型化数组和 `arguments` 对象都可迭代；普通对象只有 `length` 或数字键，不会因此可迭代。DOM 的 `NodeList` 也可迭代，但它是宿主接口，实时变化还是静态快照由具体接口决定，见[怎样查询和修改 DOM，才拿到并改到预期的节点？](../browser/dom-queries-and-updates.md)。

协议不保证能重复遍历：可迭代对象每次可以给出新迭代器，也可以总返回自身。下面的 `range` 和数组一样每次给出新迭代器；生成器对象（下一节）的迭代器就是它自己，只能遍历一次：

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

展开语法、`for...of`、数组解构等消费者各自按规则使用这个协议。协议只规定“怎样取得下一项”，不保证生产者内部没有预取、缓存或副作用。

## 生成器把进度保存在暂停的函数体里

手写迭代器要自己保存进度，像 `range` 里的 `current`。生成器把进度保存在暂停的函数体里，写起来更直接。

`function*` 声明 generator function (生成器函数)。调用它会创建生成器对象：参数绑定和默认参数表达式在调用时就处理，函数体要到第一次 `next()` 才开始执行。每次 `yield` 暂停函数体并产出一个值；之后调用 `next(value)` 恢复执行，暂停处的 `yield` 表达式求值为传入的 `value`。第一次 `next(value)` 时还没有暂停的 `yield` 接收，参数被忽略：

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

`return` 的值放在最后结果的 `value` 里，但 `done: true` 表示序列已结束，它不算一项产出，`for...of` 和展开语法都会忽略它。

下面验证调用时机：调用生成器时默认参数已经求值，函数体里的日志和 `try` 都还没运行。对尚未启动的生成器调用 `return()`，它直接结束，`finally` 不会运行：

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
events; // ["参数初始化"]；函数体没进入过 try/finally
~~~

## yield* 委托与无限序列

`yield*` 把一段迭代委托给另一个可迭代对象。委托期间，外部的 `next()` 转交给子迭代器的 `next()`；`throw()` 和 `return()` 能否转交，取决于子迭代器有没有实现这两个可选方法。子迭代器自然结束时，它最后结果里的 `value` 成为 `yield*` 表达式的值，外层从这里继续：

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

委托期间外部提前关闭，规则如下：

- 对外层调用 `return(v)`：子迭代器没有 `return` 方法，外层直接在 `yield*` 处执行这次返回；子 `return()` 给出 `done: false`，外层原样交出这个结果并继续暂停；给出 `done: true`，外层以其 `value` 执行返回，但外层自己的 `finally` 仍可能改写结果。
- 对外层调用 `throw(e)`，而子迭代器没有 `throw` 方法：委托先尝试调用子迭代器的 `return` 关闭它，然后抛出 `TypeError` 表示协议不匹配；关闭过程本身抛错时，传播关闭错误。
- 不涉及委托时，对暂停的生成器调用 `throw(e)`，会在暂停处抛出 `e`，可被生成器内的 `catch` 捕获，或经过 `finally` 后向外传播。

同样的暂停与恢复可以按需产出无限序列。无限生成器不会自己结束，消费者拿够数据后必须主动停止：

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

序号也可以按需生成，不必预先分配大数组。下面的 ID 只在同一个生成器实例内、计数不超过安全整数范围时唯一；不同实例用同一前缀会产生重复 ID：

~~~javascript
function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}

const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
~~~

## 提前退出怎样通知迭代器清理

循环体通过 `break`、`return` 或抛错提前离开时，`for...of` 会调用迭代器的可选方法 `return()`。生成器把这次调用变成暂停点处的一次 `return`，所以已经进入 `try` 的生成器会运行 `finally`；生成器持有的资源应在这个 `finally` 里清理。手写迭代器则直接实现 `return()`：

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

错误来自哪里，决定会不会关闭：

- 同步迭代器的 `next()` 自己抛错，或原生异步迭代器的 `next()` 返回的 Promise 拒绝：循环直接传播该错误，不调用 `return()`。
- 循环体抛错：循环请求关闭；`return()` 也抛错时，传播的仍是循环体的原错误。
- 正常 `break` 时 `return()` 抛错：传播 `return()` 的错误。

### 清理路径上不要再 yield

生成器暂停在 `try` 里时，`return(value)` 让 `finally` 运行；但 `finally` 里也可以再 `yield` 暂停：

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

`return()` 得到 `{ done: false }` 后不会自动继续推进。`for...of` 的 `break` 只调用一次 `return()`，确认返回值是对象就退出，不会因为 `done: false` 再调用 `next()`；`for await...of` 等待这一次异步 `return()` 完成，同样不重复关闭。于是 `yield` 之后的清理代码会一直挂着：

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

希望一次关闭就完成清理，清理路径上就不要再 `yield`。

> [!warning] 关闭请求不等于强制取消
> `return()` 只执行迭代器自己定义的关闭步骤。`next()` 正在等待网络、文件或流时，迭代器协议无法打断宿主 API。异步生成器的 `next()`、`return()` 和 `throw()` 都返回 Promise，并按调用顺序排队：一个 `next()` 还停在函数体内的 `await` 上时，随后调用的 `return()` 不会插队，要等前一个请求完成才执行关闭路径。这保证生成器代码不会被并发重入，但不会取消它正在等的 Fetch。所以还要同时使用宿主资源自己的取消接口，例如把 `AbortSignal` 交给 Fetch。

## for await...of 怎样取值

消费分页生成器要用 `for await...of`。它优先调用 `Symbol.asyncIterator`，等待 `next()` 返回的 Promise，再把结果里的 `value` 原样交给循环体。对象没有异步迭代方法时，它把同步迭代器包装成异步迭代器，包装器还会等待每项 `value` 中的 Promise 或 thenable。异步生成器在 `yield` 时也会先等待被产出的值。所以 `value` 本身是 Promise 时，三种来源表现不同：

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
    observed.push(value === promiseValue); // true：原生异步迭代器的 value 不解包
    break;
  }
  for await (const value of [promiseValue]) observed.push(value); // "x"：同步包装器等待 value
  for await (const value of (async function* () { yield promiseValue; })()) {
    observed.push(value); // "x"：异步生成器等待 yield 的值
  }
  return observed;
}

compareForAwaitValues().then(console.log); // [true, "x", "x"]
~~~

同步包装器还有一条关闭规则：它等待的某个 `value` 拒绝时，会先关闭底层的同步迭代器，再传播拒绝。这与上一节“`next()` 自身出错不关闭”不同；在 Node.js 中用同步生成器验证，确实会进入它的 `finally`。

## 游标分页的异步生成器

报表行接口每次返回一页 `items`（行数组）和 `nextCursor`（没有下一页时为 `null`）。分页生成器先等响应、检查 HTTP 状态、读取 JSON 并校验整页结构，再逐行 `yield`；当前页的行全部被消费后，才用游标请求下一页。Fetch 各步的履行和拒绝条件见 [fetch 履行不等于请求成功](./promises-and-async-functions.md#fetch%20履行不等于请求成功)。

下面用一组合成数据走一遍：页 1 按 `sort=recent` 返回主线一的 May 行和 April 行，`items: [r-104, r-103]`，以及 `nextCursor: "c2"`；页 2 返回更早的 `items: [r-102]` 和 `nextCursor: null`。消费者的目标行是 April 行 `r-103`。

| 消费者做什么 | 生成器推进到哪里 | 本次结果 / 是否请求下一页 |
|---|---|---|
| 第一次 `next()` | 请求并校验页 1，暂停在 `yield r-104` | 交付 `r-104`；页 1 留在内存里 |
| 追加完 `r-104` 后再 `next()` | 恢复页内循环，暂停在 `yield r-103` | 交付 `r-103`；还没更新游标 |
| `r-103` 是目标，追加后 `break` | 一次 `return()` 进入 `finally` | 关闭；不请求 `c2` |
| 若不停止，追加完 `r-103` 后再 `next()` | 把游标更新为 `c2`，请求并校验页 2 | 交付 `r-102` |
| 追加完 `r-102` 后再 `next()` | 读到 `nextCursor: null`，结束并清理 | `done: true`；没有下一页 |

`break` 会调用一次异步迭代器的 `return()`，并等待生成器的 `finally` 完成；生成器没走到更新游标那一步，所以不请求 `c2`。两类坏数据在不同时点暴露：结构错误的页在 `validateReportPage` 里、该页第一次 `yield` 之前就拒绝；重复游标要等当前页的行都交付后才检查。

> [!example]- 分页生成器与逐行消费者的完整实现
> `appendRow` 返回“当前行追加完成”的 Promise，写入本次筛选自己的报表列表；`currentSort`、`selectedRowId`、取消按钮和错误展示函数由页面提供。`appendReportRows` 的两次信号检查分别守住“开始追加”和“再次拉取”两个边界。
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
> appendReportRows("42", currentSort, selectedRowId, controller.signal, appendRow)
>   .catch(showReportError);
> ~~~

**内存。** 任一时刻内存里是当前页解析并校验后的 `page.items`，生成器逐项交付，不把整份报表合并成一个大数组。消费者处理完一行才继续拉取，这形成了一种 backpressure (背压)，但只约束经由拉取产生的工作；生产者若在后台自己预取，就不受约束。`seenCursors` 防止接口重复返回游标导致无限分页，占用空间与已读页数成正比。

**取消。** 本例的 `finally` 只记录迭代已关闭，真正中止网络请求和正文读取的是传给 Fetch 的 signal：还没收到响应的请求被中止，`response.json()` 还在读正文时这次读取拒绝。取消若发生在 `appendRow` 等待期间，已经开始的追加无法回滚，这一行仍可能写进列表。`appendReportRows` 在追加前查一次信号，避免启动新的追加；追加后再查一次，避免向迭代器要下一项或请求下一页。它只吞掉与当前 `signal.reason` 完全相同的取消原因，其他错误照常向上传播。

若需要并发处理行，要另行规定顺序、背压和失败策略；本例的 `appendRow` 完成后才拉取下一行。

## 已启动的 Promise 数组不适合用 for await 收集

`for await...of` 也能消费包含 Promise 的同步可迭代对象，比如 Promise 数组。同步包装器按数组顺序逐个等待；这些 Promise 可能在循环开始前就已启动，完成先后与交付顺序不一定相同：

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
// ["first","second"]：交付仍按数组顺序
~~~

`Promise.all` 和 `Promise.allSettled` 的结果也按输入顺序排列，区别在于它们一开始就给每个成员注册处理器。`for await...of` 轮到某一项才开始监听它：后面的 Promise 在前一项完成前就拒绝时，这个拒绝暂时无人处理，宿主可能把它报告为未处理拒绝；前一项拒绝或一直不完成时，循环可能永远走不到后面的项。所以遍历已启动的 Promise 数组时，应改用组合器。未处理拒绝的报告时机因宿主而异。

## 历史：co 用生成器写异步流程

在 async/await 标准化之前，`co` 等库用生成器表达异步流程：runner (执行器) 读到 `yield promise` 后等待它，成功时用 `next(value)` 把结果送回生成器，失败时用 `throw(error)` 在暂停处抛出。这正是前面 `next(value)` 和 `throw(e)` 两条规则的组合。了解这个模式有助于维护旧代码；现代 `async function` 有自己的 Promise 语义，不暴露生成器对象。

## appendReportRows 交给页面的契约

本章交出 `appendReportRows(reportId, sort, stopAfterId, signal, appendRow)`：逐页逐行读取，每行等 `appendRow` 完成才继续；找到目标行时关闭迭代器、不请求下一页；当前 signal 的取消使它**正常返回**；HTTP 失败、坏结构、重复游标和其他追加错误使它拒绝。页面点击处理器怎样同时调用 `loadReport` 和它、怎样用请求序号和每次筛选独立的列表挡住换筛选后迟到的旧行，见[一次失败该由哪一层处理？](./error-handling-across-layers.md#完整例子：刷新报表的页面处理器)。

> [!info]- 来源
> - **迭代协议、生成器、委托、关闭与异步适配（全章）。** [ECMAScript 2026](https://tc39.es/ecma262/2026/)，正式版。§7.4.11、§7.4.14 同步/异步 IteratorClose；§14.7.5.7 `for...of` / `for await...of` 的遍历与关闭；§15.5.5 生成器函数与委托；§27.1.5.4 同步迭代器 Promise 值的异步适配与拒绝时关闭；§27.5、§27.6 生成器状态与异步生成器请求排队。
> - **“已启动的 Promise 数组”中组合器按输入位置收集。** [ECMAScript 2026 §27.2.4](https://tc39.es/ecma262/2026/#sec-properties-of-the-promise-constructor)，§27.2.4.1 `Promise.all`、§27.2.4.2 `Promise.allSettled`。
> - **“游标分页的异步生成器”中的 HTTP 响应、正文读取与取消。** [Fetch Standard：Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch)、[Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard（最近更新 2026-10-19），核对日期 2026-11-12。HTTP 非成功状态仍是 Response；取消 Fetch 不撤回服务端已执行的副作用。
> - **未处理拒绝的宿主报告。** [WHATWG HTML 8.1.4.7 Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)，Living Standard（最近更新 2026-11-11），核对日期 2026-11-12。Node.js 等宿主有各自的报告机制。
> - **运行核对。** 原稿在 Node.js v26.13.0 检查生成器启动/关闭、`yield*` 缺方法分支、异步关闭等待、异步生成器排队、原生异步迭代器与同步包装器的 Promise 值差异、拒绝处理和同步包装器关闭，并用 loopback 服务覆盖两页固定游标、坏结构、重复游标、目标行提前停止、Fetch 等待期中止和正文读取期中止（不代表真实网络时延）。本次在 Node.js v26.13.1 重跑 `conversation`、`sample`、`withCleanupYield`、`rowsWithCleanupYield`、`parent/child`、`yield*` 缺 `throw` 时先调用子 `return` 再抛 `TypeError`、`compareForAwaitValues`、`collectInInputOrder`、同步包装器拒绝时进入 `finally`、循环体错误优先于 `return()` 错误，结果与正文一致。
