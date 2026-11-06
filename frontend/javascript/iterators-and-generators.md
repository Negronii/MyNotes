# 迭代器与生成器怎样按需产出并清理数据？

## 案例背景

报表 42 有很多行，页面通过 Fetch API（浏览器的应用程序编程接口）逐页请求并逐行追加结果，不必先把所有页合成一个大数组。它检查 HTTP（超文本传输协议）状态并读取 JSON（JavaScript 对象表示法）。调用方希望处理一行后再取下一行，也可能在找到目标行或用户取消时提前停止。迭代协议规定生产者怎样交付下一项、怎样表示结束；生成器可把暂停和清理逻辑写在产出值的代码旁边。

## 可迭代对象怎样交给消费者逐项读取？

iterable（可迭代对象）通过 Symbol.iterator 提供 iterator（迭代器）。迭代器的 next() 返回一个对象：消费者把 done 转成布尔值，false 表示继续使用 value，true 表示结束。done 缺省时按 false 处理；结束时 value 可以省略。有 length 或数字键并不会自动让普通对象可迭代。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }
~~~

数组、字符串、Map、Set、类型化数组和 arguments 对象都能迭代。Document Object Model（文档对象模型，DOM）的 NodeList（节点列表）也支持迭代，但它是宿主 API；集合是否实时变化取决于返回它的具体 API，DOM 集合的实时/静态差异见[HTMLCollection 与 NodeList 如何处理集合变化？](../browser-apis/dom-collections.md)。

~~~mermaid
flowchart LR
  A["iterable：调用 Symbol.iterator"] --> B["iterator：调用 next()"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["消费 result.value"]
  D --> B
  C -- "true" --> E["结束"]
~~~

一个 iterable 每次可以返回新的 iterator，但协议不要求如此。很多内置迭代器和 generator 会把自身作为 iterator 返回，所以那种对象消费一次后已经结束；自定义 iterator 是否可迭代、是否可重用由它自己的协议实现决定：

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

const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true
~~~

## 生成器怎样暂停、接收值并委托工作？

generator（生成器）函数调用时只创建一个同时实现可迭代协议和迭代器协议的对象，函数体尚未执行。首次调用 next() 才开始运行函数体，直到第一个 yield 暂停并把当前值交给调用方；下一次 next() 才恢复。第一次 next(value) 的参数会被忽略，因为还没有暂停在 yield；后续参数会成为当前暂停处 yield 表达式的值。

~~~javascript
function* conversation() {
  const name = yield "你叫什么名字？";
  const hobby = yield "你好，" + name + "！你喜欢做什么？";
  return name + "喜欢" + hobby;
}

const chat = conversation();
chat.next();          // { value: "你叫什么名字？", done: false }
chat.next("Ada");     // { value: "你好，Ada！你喜欢做什么？", done: false }
chat.next("编程");    // { value: "Ada喜欢编程", done: true }
~~~

yield* 把读取委托给另一个 iterable 或 generator，并把子生成器的 return 值交回当前生成器。它能把递归遍历组合成一个惰性输出序列：

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

生成器按调用方需求才计算后续值。它可以表达大序列或无限序列，而不把所有结果预先放进数组：

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

同一状态思路也可按需产生序号，不需要提前分配全部 id。下面只在同一个生成器实例内、计数尚未超过 Number 精确整数范围时保证不重复；不同实例使用同一前缀仍会生成相同 ID：

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

迭代器可以实现 return()，作为调用者不再请求下一项时的清理钩子。for...of 因循环体中的 break、throw 或其他突然控制流离开时会调用该钩子；若生成器使用 try/finally，关闭时会执行 finally。

~~~javascript
const source = {
  [Symbol.iterator]() {
    let value = 0;
    return {
      next() {
        return { value: value++, done: false };
      },
      return() {
        console.log("释放迭代器资源");
        return { done: true };
      }
    };
  }
};

for (const value of source) {
  if (value === 2) break; // 退出时调用 return()
}
~~~

这是一种协议层的“不会再向你要值”通知，不等于中断任意底层工作。若 iterator 的 next() 已在等待网络、文件或流，return() 本身不会替这些宿主 API 实现取消；要停止它们，还需其显式取消机制，例如把 AbortSignal 传给 Fetch。

对异步生成器，若一次 next() 仍在等待，之后调用 return() 不会抢占那次挂起的 next；它要等该次操作完成后才有机会关闭。正在执行的 Fetch 仍需单独通过 AbortSignal 中止。

> [!warning] 关闭钩子由消费者的退出路径触发
> 上述保证针对循环体执行 break、throw 等情况。若 iterator 自己的 next() 抛错，不能据此假定消费者会再调用它的 return() 清理；需要可靠释放资源时，应把清理放进生成器自己的 finally 或使用宿主 API 的显式关闭协议。

## 报表行怎样按页异步读取？

async iterable（异步可迭代对象）通过 Symbol.asyncIterator 提供 async iterator（异步迭代器）。每次 next() 返回一个稍后完成的 Promise；for await...of（异步迭代循环）等待当前一项并处理完循环体，再请求下一项。这样消费者的处理速度自然限制下一次读取，形成逐项 backpressure（背压）。

表格行是第二阶段：三项基础请求的响应已通过状态和结构校验，页面也依据权限结果决定可以读取行后，把 loadReport(42, sort, signal) 使用的同一报表 ID、排序和请求信号交给独立分页接口。客户端权限判断只控制是否发起交互，服务端仍须独立验证访问权。行请求不属于基础 Promise.all，也不必先把所有行读进内存；若基础请求失败或用户切换筛选，页面不会继续交付这条旧行流。下面假设行记录至少有字符串 id；validateReportPage 在响应边界检查分页形状，appendRow 作为参数注入，返回当前行追加完成的 Promise；它必须绑定本次筛选独立拥有的输出容器。currentSort、selectedRowId 和取消按钮来自同一个报表界面。

~~~javascript
function validateReportRow(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      typeof value.id !== "string") {
    throw new Error("报表行缺少字符串 id");
  }
  return value;
}

function validateReportPage(value) {
  if (!value || typeof value !== "object" || !Array.isArray(value.items)) {
    throw new Error("报表分页响应缺少 items 数组");
  }
  if (value.nextCursor !== null &&
      (typeof value.nextCursor !== "string" || value.nextCursor.length === 0)) {
    throw new Error("nextCursor 必须是非空字符串或 null");
  }
  return {
    items: value.items.map(validateReportRow),
    nextCursor: value.nextCursor
  };
}

async function* reportRows(reportId, sort, signal) {
  let cursor = null;
  const seenCursors = new Set();

  try {
    while (true) {
      const query = new URLSearchParams({ sort });
      if (cursor !== null) query.set("cursor", cursor);
      const response = await fetch(
        "/api/reports/" + reportId + "/rows?" + query,
        { signal }
      );
      if (!response.ok) throw new Error("HTTP " + response.status);

      const page = validateReportPage(await response.json());
      for (const row of page.items) yield row;
      if (page.nextCursor === null) return;
      if (seenCursors.has(page.nextCursor)) {
        throw new Error("报表接口重复返回分页游标");
      }
      seenCursors.add(page.nextCursor);
      cursor = page.nextCursor;
    }
  } finally {
    console.log("报表行迭代已关闭");
  }
}

async function appendReportRows(reportId, sort, stopAfterId, signal, appendRow) {
  try {
    for await (const row of reportRows(reportId, sort, signal)) {
      if (signal.aborted) throw signal.reason;
      await appendRow(row);
      if (row.id === stopAfterId) break;
    }
  } catch (error) {
    if (signal.aborted && error === signal.reason) return;
    throw error;
  }
}

const controller = new AbortController(); // 用户取消时向正在运行的 Fetch 发信号
cancelButton.addEventListener("click", () => controller.abort(), { once: true });
appendReportRows(42, currentSort, selectedRowId, controller.signal, appendRow)
  .catch(showReportError);
~~~

找到目标行后 break 会关闭 async iterator，因此生成器的 finally 会执行；未请求的后续页不会再读取。若用户在 fetch 等待期间按“取消”，外层需通过 AbortController（中止控制器）调用 abort()，Fetch 才会收到 AbortSignal（中止信号）。若取消发生在 appendRow 等待期间，该行追加已开始且本例没有把 signal 交给 appendRow，不能撤回；如果它直接写共享当前列表，旧行就可能混入新筛选。因此调用方应像[错误处理章节](./error-handling.md#报表请求的错误由谁接手)那样为每一代创建独立容器，切换时替换当前容器；已开始的旧追加只能写脱离页面的旧容器。追加完成后，循环在开始下一行前检查 signal，不会再追加缓存的后续行。catch 只吞掉与该 signal.reason 相同的取消原因；恰好同时发生的独立校验或追加错误仍会向上传播。异步迭代协议不会自动取消正在进行的网络请求，也不能撤销远端已经完成的写操作。此例在每页响应后检查 items、行结构和 nextCursor，并拒绝重复游标；它逐页持有一个响应体并逐行交付，没有把整个报表预存为数组。

> [!example] 在当前页停止后不会请求下一页
> 假设当前页交付行 r-101、r-102，并带有 nextCursor。若 r-102 是 stopAfterId，循环在消费 r-102 后执行 break；生成器关闭并运行 finally，停在该页，不会更新 cursor 或发出下一页请求。

for await...of（异步迭代循环）也能读取同步 iterable 中的 Promise，但按输入顺序等待，而非按最快完成顺序产出。下面两个计时器在数组构造时同时启动，第二项先完成；迭代结果仍为 first、second：

~~~javascript
const slow = new Promise(resolve => setTimeout(() => resolve("first"), 20));
const fast = new Promise(resolve => setTimeout(() => resolve("second"), 0));

async function collectInInputOrder() {
  const values = [];
  for await (const value of [slow, fast]) values.push(value);
  return values;
}

collectInInputOrder().then(values => console.log(JSON.stringify(values)));
// ["first","second"]
~~~

> [!warning] 并行 Promise 不要只按序等待
> 若第二个 Promise 在第一个仍 pending 时先拒绝，for await...of 仍等待第一个；宿主可能在循环读取到第二项前先报告这个拒绝未处理。若多项工作彼此独立并且都需要观察成功或失败，先用 Promise.all 或 Promise.allSettled 安装统一处理路径。

若目标是汇总独立操作，通常用 Promise.all；异步迭代适合逐项到达、逐项消费的数据。Promise 组合的输入顺序与取消边界见[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md#报表请求何时并发何时顺序等待)。

在 async/await 标准化以前，co 等库曾运行生成器：生成器 yield 一个 Promise，runner（驱动器）在 Promise 完成后把值传给 next()，拒绝时把错误传给 throw()。这是历史控制流模式；async 函数有自己的 Promise 语义，并不是由用户可见的 generator 实例实现。

> [!info]- 来源
> - iterable、iterator、generator、async iterator、yield* 与迭代关闭：ECMAScript 2027 规范（2026-11-05 草案快照），[迭代协议](https://tc39.es/ecma262/#sec-iteration)、[IteratorClose](https://tc39.es/ecma262/#sec-iteratorclose)、[AsyncIteratorClose](https://tc39.es/ecma262/#sec-asynciteratorclose)、[异步生成器请求队列](https://tc39.es/ecma262/#sec-asyncgeneratordrainqueue)、[for-of 与 for-await-of](https://tc39.es/ecma262/#sec-for-in-and-for-of-statements-runtime-semantics-labelledevaluation)。
> - Fetch 中止与响应体清理：[Fetch Standard，Living Standard 2026-10-19：abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)。中止请求与回滚远端业务副作用是不同保证。
> - DOM NodeList 的可迭代与集合实时性：由相应 DOM API 定义，见[DOM Standard，Living Standard 2026-11-04：NodeList](https://dom.spec.whatwg.org/#interface-nodelist)与本仓库的[DOM 集合章节](../browser-apis/dom-collections.md)。
> - 宿主计时器不保证精确触发时间，拒绝处理器的安装时机也可能触发全局未处理拒绝报告：WHATWG HTML Living Standard（2026-11-05），[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)。
