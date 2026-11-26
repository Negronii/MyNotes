# 一次失败该由哪一层处理？

本章讲一个失败从产生到被处理要经过哪些层，每层该恢复、继续传播还是只记录。读者手上有三份契约：[`loadReport`](./promises-and-async-functions.md#三项请求一起等：loadReport) 要么交出三份已校验数据、要么拒绝；[`AbortSignal`](./cancellation-timeouts-and-concurrency.md) 只请求协作式取消；[`appendReportRows`](./iterators-and-generators.md#appendReportRows%20交给页面的契约) 在当前 signal 取消时正常返回，其他错误时拒绝。本章沿用主线一的报表页，最后把它们装进一个刷新报表的页面处理器。

## 每个失败先回答三个问题

一条错误链要回答三个问题：**哪个操作失败了？哪一层还有足够的上下文？这一层选择恢复，还是继续拒绝？**

在报表页里，服务层的 `loadReport` 知道哪个接口、哪一步失败，但不知道该显示什么；页面处理器知道当前排序、中止信号和界面状态，最适合决定显示什么提示、保留哪些旧数据、要不要重试。两种做法会弄错层次：

- 低层记一条日志就正常返回，上层会以为操作成功；
- 页面已经决定恢复，却没有结束原来的拒绝链，原错误又变成一条未处理拒绝。

页面之外还有两个入口，但职责不同。React 的 error boundary (错误边界) 处理组件树渲染时的失败；浏览器的全局错误事件只给出诊断信号。下文先看失败从哪里来，再看语言怎样传递它，最后看各层入口。

## 报表链路上的失败点

从点击刷新到报表行出现，每一步都可能失败，失败的形态也不同：

| 步骤 | 怎样失败 | 失败以什么形式出现 |
| --- | --- | --- |
| 三个 `fetch()` | 网络错误；`Response` 交出之前被中止 | Fetch Promise 拒绝 |
| 检查 `response.ok` | HTTP 404、500 | Fetch 正常履行，由 `loadReport` 自己抛错 |
| `response.json()` | 正文读取失败、读取期间被中止、无效 JSON | `json()` 拒绝 |
| 运行时校验 | 结构不符 | 校验器同步抛错 |
| 分页生成器 | 某页 HTTP 失败、坏结构、重复游标 | `appendReportRows` 拒绝 |
| 追加行 | `prepareReportRow` 或 DOM 操作抛错 | `appendRow` 拒绝，经 `appendReportRows` 传出 |

前四步的履行和拒绝条件在[“fetch 履行不等于请求成功”](./promises-and-async-functions.md#fetch%20履行不等于请求成功)有完整说明。和错误处理相关的是 `loadReport` 第一轮 `Promise.all` 的时序：任一 Fetch Promise 先拒绝，`loadReport` 立即以该原因拒绝，状态检查根本不运行；三项都履行时，即使报表的 404 最先到达，也要等另外两份 `Response` 到齐才被发现。`Promise.all` 拒绝本身不中止其他请求；本章页面处理器在 `catch` 里调用 `controller.abort()`，那是页面选择的同组取消策略。

## try 语句覆盖哪段控制流

`try/catch` 捕获的是 `try` 块执行期间、当前同步调用栈上抛出的值。在 `try` 里 `await` 的 Promise 拒绝时，拒绝在 `await` 处变成一次抛错，同样进入 `catch`。捕获之后只有两条路：明确恢复，返回一个表示成功的结果；或继续抛出，让上层拿到错误。JavaScript 的 `throw` 可以抛出任意值，不限于 `Error` 实例。

~~~javascript
try {
  const data = await loadReport("42", currentSort, controller.signal);
  renderReport(data);
} catch (error) {
  showError(toUserMessage(error));
  throw error; // 本层只更新了提示；契约仍要求拒绝时继续传播
} finally {
  setLoading(false);
}
~~~

`try` 看不到“稍后另一个调用栈”里的抛错。计时器回调运行时，原来的 `try` 早已结束；而 `async` 函数即使在第一个 `await` 之前就抛错，调用方得到的也只是一个拒绝的 Promise，必须 `await` 它或注册拒绝处理器：

~~~javascript
try {
  setTimeout(() => {
    throw new Error("未来计时器回调中的抛错");
  }, 0);
} catch (error) {
  // 捕获不到计时器回调里的抛错
}

try {
  await loadReport("42", currentSort, controller.signal);
} catch (error) {
  // 能捕获 loadReport 返回的 Promise 的拒绝
}
~~~

### finally 会替换结果

语句级 `finally` 在 `try` 正常结束、抛错或 `return` 时都会运行。`finally` 自己 `return` 或抛错时，会替换原来的结果，可能把真正的业务失败掩盖掉：

~~~javascript
async function languageFinally() {
  try {
    return "报表值";
  } finally {
    return "被 finally 替换的值";
  }
}

languageFinally().then(console.log); // 被 finally 替换的值
~~~

`Promise.prototype.finally()` 不同：回调的普通返回值被忽略，原值或原拒绝原样传下去，只有清理自己失败才取代结果，见[上一章 then 链一节](./promises-and-async-functions.md#then%20链怎样决定下一个%20Promise)。

### return p 与 return await p

在 `async` 函数里返回一个尚未结算的 Promise，写不写 `await` 决定本层的 `catch` 能不能看到它的拒绝：

~~~javascript
async function returnWithoutAwait(pendingPromise) {
  try {
    return pendingPromise;
  } catch (error) {
    console.log("此 catch 看不到返回 Promise 的拒绝");
    throw error;
  } finally {
    console.log("return Promise 后先运行 finally");
  }
}

async function catchAfterAwait(pendingPromise) {
  try {
    return await pendingPromise;
  } catch (error) {
    logReportError(error, { operation: "pending report" });
    throw error;
  } finally {
    console.log("await 结束后 finally 才运行");
  }
}
~~~

`return pendingPromise` 立即离开 `try` 并运行 `finally`，函数返回的 Promise 之后才跟随它的结局；它后来拒绝，也不会回到已经离开的 `catch`。`return await pendingPromise` 在 `await` 处等待，拒绝先进入本层 `catch`，然后才运行 `finally`。需要本层处理或记录时，写 `return await`。

### 拒绝处理器决定链恢复还是继续拒绝

`.catch()` 和 `.then()` 的拒绝处理器返回普通值或最终履行的 Promise，后续链就恢复为履行；抛错或返回最终拒绝的 Promise，后续链继续拒绝。下面的诊断层记录后重新抛出，把拒绝交回掌握上下文的页面层：

~~~javascript
function loadReportWithDiagnostic(sort, signal) {
  return loadReport("42", sort, signal)
    .catch(error => {
      logReportError(error, { operation: "load report" });
      throw error; // 这个 catch 返回的新 Promise 仍然拒绝
    });
}

async function refreshAndRecover(sort, signal) {
  try {
    return await loadReportWithDiagnostic(sort, signal);
  } catch (error) {
    setError(toUserMessage(error));
    return undefined; // 页面已恢复，调用方收到履行
  }
}

void refreshAndRecover(currentSort, controller.signal)
  .catch(error => logReportError(error, { operation: "refresh handler" }));
~~~

## 错误值怎样补上下文又不丢根因

错误向上传播时，每层可能要补上自己的上下文。ES2022 起，`Error` 构造器支持 `cause` 选项：包装出带当前操作语义的新错误，同时保留根因。再加一个稳定的 `code` 字段，调用方可以按类别分支，不必解析消息文字：

~~~javascript
class ReportDecodeError extends Error {
  constructor(message, cause) {
    super(message, { cause });
    this.name = "ReportDecodeError";
    this.code = "REPORT_DECODE_FAILED";
  }
}

function decodeReport(raw) {
  try {
    return validateReport(raw);
  } catch (cause) {
    throw new ReportDecodeError("报表数据无法读取", cause);
  }
}
~~~

给用户看的文字另外映射。服务端返回的消息可能含内部细节、用户数据或随实现变化的措辞，不应直接展示。页面的 `toUserMessage` 按已知的错误类型或 `code` 映射到安全文案，遇到未知值——包括 `null`、字符串这类非 `Error` 的抛出值——给出通用兜底消息。

按类别判断时，`instanceof` 只在构造函数只有一份时可靠。它沿对象的原型链查找右侧构造函数的 `prototype`；跨 iframe 或 realm (执行环境)，或同一个库被重复加载出多份构造函数时，错误对象继承的是另一份原型，判断就会失败。跨这类边界时应依赖 `code` 这类明确字段或序列化格式。只有代码被转译到无法正确继承内置 `Error` 的旧目标（如 ES5）时，才需要用 `Object.setPrototypeOf` 修复原型链。

## 记录器自己不能再抛

诊断记录器处在错误路径上，它自己出错会造成两种伤害：替换掉原来的错误，或者制造一条新的未处理拒绝。所以记录器要满足三条：

- 接受任意抛出值，直接把原值交给诊断通道，不先读取 `error.message`：抛出值是 `null` 时，读 `message` 本身就会产生新的 `TypeError`；
- 隔离诊断出口的同步抛错；
- 隔离诊断出口返回的拒绝。

~~~javascript
function logReportError(error, context) {
  try {
    Promise.resolve(diagnostics?.capture?.({ error, context })).catch(() => {});
  } catch {
    // 诊断出口自己的失败不替换原错误，也不再产生未处理拒绝。
  }
}
~~~

`diagnostics.capture` 是应用自己的诊断出口。记录器自身的失败若也必须保存，要走另一个独立的诊断出口，不能递归调用同一个记录器。

## 全局 error 和 unhandledrejection 只是诊断信号

浏览器还提供全局入口，但它们看到的既不是“应用里所有未恢复的错误”，也不能代替页面的恢复逻辑：

- **`window.onerror` 和全局 `error` 事件**观察宿主报告的脚本异常。HTML 的 muted errors (静音错误) 规则会隐藏某些跨源 classic script (经典脚本) 的错误细节，页面只看到通用的 `Script error.`；静音脚本里的 Promise 拒绝还可能根本不被追踪。要拿到这类脚本的错误详情，`<script>` 要加 `crossorigin` 属性启用 CORS 检查，并由服务器允许该来源。两种失败处在不同阶段：CORS 检查失败时脚本根本不加载；静音是脚本已经运行，只是错误细节被隐藏。
- **`unhandledrejection`** 只在宿主准备报告时该拒绝仍无人处理才触发。宿主报告前就补上拒绝处理器，事件不派发；报告之后才补上，页面还会收到 `rejectionhandled`。事件发生时，拒绝产生时的调用栈早已结束。
- **资源加载失败**（图片、脚本等）的 `error` 事件以元素本身为目标，而且不冒泡；要在祖先节点或 `window` 上集中记录，必须注册捕获阶段的监听器，捕获与冒泡见[一次点击怎样传播到处理器？](../browser/dom-events.md)。

`window.onerror` 处理器返回 `true` 会抑制该运行时错误的默认报告；下面改用 `addEventListener`，只记录不抑制，同时用捕获阶段接住资源错误：

~~~javascript
window.addEventListener("unhandledrejection", event => {
  logReportError(event.reason, { source: "unhandledrejection" });
  // 只有明确要取消默认报告时才调用 event.preventDefault()
});

window.addEventListener("error", event => {
  if (event.target === window) {
    logReportError(event.error, { source: "window error" });
  } else {
    logReportError(undefined, { source: "resource error", target: event.target });
  }
}, true); // 捕获阶段：同时记录全局脚本错误与资源 error
~~~

可预期的失败应尽早回到掌握上下文的那一层处理；全局监听器只用来发现漏网的错误，不应把本可恢复的请求错误静默吞掉。

## React 错误边界只接住渲染错误

React 错误边界在子组件渲染抛错时显示局部备用界面，但接不住事件处理器和 `setTimeout` 这类普通异步回调里的错误。所以按钮触发的 Fetch 仍要像下面的 `onRefreshClick` 一样，自己 `await` 并处理拒绝。边界的分类、粒度和重置见 [错误发生在哪里，决定了谁能接住它？](../ui-state/react-error-boundaries.md)。

## 完整例子：刷新报表的页面处理器

用户点击刷新或改排序时，页面要做四件事：发起新请求，让旧请求停下，挡住没能停下的旧结果，并为本次请求显示唯一的错误提示和 loading 状态。三个工具各管一部分：

- **请求序号 `requestId`**：只有最新请求才能提交报表、摘要、权限、错误提示和 loading。它是一种按身份归属的守卫，共同原理见[异步结果按身份归属](../ui-state/server-state-and-optimistic-updates.md)。
- **每次请求自己的 `AbortController`**：尽力停止支持取消的网络工作。
- **每次筛选一个新的 `ol#reports`**：没能取消、又在之后完成的旧行追加，最多写进已经脱离文档的旧列表。

下面的代码假定页面已有主线一的报表列表 `ol#reports`、刷新和取消按钮、排序控件，以及 `setReport`、`setLoading`、`setError` 等状态更新函数；这些同步初始化与 DOM 替换都按约定正常运行。`prepareReportRow` 只创建 `li` 行节点，`appendRow` 再把它加进本次筛选的列表。

~~~javascript
let latestReportRequest = 0;
let activeController = null;

async function onRefreshClick(sort) {
  const requestId = ++latestReportRequest;
  activeController?.abort();

  const controller = new AbortController();
  activeController = controller;
  setLoading(true);

  const rowTarget = document.createElement("ol");
  document.getElementById("reports").replaceWith(rowTarget); // 换下旧列表
  rowTarget.id = "reports";

  const appendRow = async row => {
    const element = await prepareReportRow(row);
    rowTarget.append(element);
  };

  try {
    const { report, summary, permissions } =
      await loadReport("42", sort, controller.signal);
    if (requestId !== latestReportRequest) return;

    setReport(report);
    setSummary(summary);
    setPermissions(permissions);
    clearError();

    // 权限字段已由服务层校验为布尔值；无权时不发起行请求。
    if (permissions.canReadRows === true) {
      await appendReportRows("42", sort, null, controller.signal, appendRow);
    }
  } catch (error) {
    // 只静默本请求自己的取消原因；其他错误都留下诊断记录。
    if (controller.signal.aborted &&
        error === controller.signal.reason) return;

    if (!controller.signal.aborted) controller.abort();
    logReportError(error, { requestId, sort });
    if (requestId !== latestReportRequest) return;
    setError(toUserMessage(error));
  } finally {
    if (requestId === latestReportRequest) {
      setLoading(false);
      activeController = null;
    }
  }
}

cancelButton.addEventListener("click", () => activeController?.abort());
refreshButton.addEventListener("click", () => {
  void onRefreshClick(sortSelect.value)
    .catch(error => logReportError(error, { source: "refresh handler" }));
});
~~~

当前请求的取消在两处被接住：基础三项请求以与 `signal.reason` 完全相同的值拒绝时，`catch` 直接静默返回；分页阶段的取消已由 `appendReportRows` 吞掉并正常返回，根本不进 `catch`。其他错误——包括与 `signal.reason` 不同的追加错误——都会被记录，并为当前请求显示提示。最外层的 `.catch` 只防止处理器本身意外抛错变成未处理拒绝。

下面用三种情况检验这段代码。

> [!example] HTTP 404 怎样走到界面提示
> 报表 Fetch 得到 404，摘要和权限 Fetch 也都履行为 `Response`。第一轮 `Promise.all` 履行后，`loadReport` 检查 `response.ok` 并抛错；状态检查先于 `json()`，三份正文都不读，也不提交新的报表、摘要和权限。`catch` 记录原始错误，中止当前控制器，显示错误提示；`finally` 关闭 loading。上一次已提交的报表、摘要和权限仍然保留，但刷新开始时已换上空列表，旧行不会保留。错误处理完成后，`onRefreshClick` 的 Promise 履行 `undefined`。若摘要或权限的 Fetch 先拒绝，第一轮 `Promise.all` 以它的原因拒绝，404 检查不会运行。

第二种情况是两次筛选交错：用户先按 `recent` 发起调用 1，随后改为 `oldest` 发起调用 2。下图画出调用 2 开始后，调用 1 停在不同位置时各自怎样收场：

~~~mermaid
%%{init: {"sequence": {"actorMargin": 70}}}%%
sequenceDiagram
  participant R1 as 调用 1（recent）
  participant R2 as 调用 2（oldest）
  participant P as 页面状态
  participant L1 as 列表 L1
  participant L2 as 列表 L2
  R1->>P: latestReportRequest = 1<br/>activeController = c1，loading 开
  R1->>L1: 用新的 L1 换下旧列表
  Note over R1: 等基础三项<br/>或已提交并在追加行
  R2->>P: latestReportRequest = 2，中止 c1<br/>activeController = c2，loading 开
  R2->>L2: 用新的 L2 换下 L1，L1 脱离文档
  alt 调用 1 还在等基础三项，请求被取消
    Note over R1: 以 c1.signal.reason 拒绝<br/>catch 静默返回
  else 没能停下，迟到成功
    Note over R1: requestId 1 ≠ 2<br/>不提交，直接返回
  else 迟到失败（不是取消原因）
    R1->>P: 只 logReportError，1 ≠ 2：不 setError
  else 调用 1 已在追加行
    R1->>L1: 已开始的行追加完成，只写进脱离文档的 L1
    Note over R1: 追加后复查信号<br/>appendReportRows 正常返回，不再拉取
  end
  Note over R1: finally：1 ≠ 2<br/>不关 loading，不动 activeController
  R2->>P: 2 是最新：提交报表、摘要、权限，清除错误
  R2->>L2: appendReportRows 追加 oldest 的行
  R2->>P: finally：关闭 loading，activeController = null
~~~

四条分支的共同结果是：调用 2 开始之后，调用 1 不再提交任何状态、不覆盖当前提示，也不关闭调用 2 的 loading，只有非取消错误仍被记录。

> [!example] 追加 r-104 时点了取消
> 分页第一页是 `r-104`、`r-103`。用户在 `prepareReportRow(r-104)` 等待时点“取消”，已经开始的追加撤不回来；当前列表仍在页面上，这一行完成后照样出现。`appendReportRows` 随即复查信号、关闭迭代器并正常返回，不再交付内存里的 `r-103`，也不请求下一页。页面的 `await appendReportRows(...)` 正常履行，跳过 `catch`，由 `finally` 关闭 loading。

分工归结为一句：信号只请求停止；已经开始、又不支持取消的工作照样会完成，它对界面的影响由请求序号和每次筛选独立的列表隔离。

## 页面接住失败之后

本章交出的是一套分工：服务层只把失败变成带上下文的拒绝；页面处理器用序号、信号和独立列表决定提交什么、显示什么，并把自己的取消与真正的错误分开；记录器接受任意值且自身不抛；全局事件只做诊断。请求序号背后“异步结果按身份落到对的界面上”的一般原理，以及它在 Effect、Redux 和查询缓存里的对应物，由[服务端状态与乐观更新一章](../ui-state/server-state-and-optimistic-updates.md)接手；渲染期的失败交给[错误边界一章](../ui-state/react-error-boundaries.md)。

主线三的“函数与异步”一组到这里结束。下一组转向程序与运行时：代码拆成多个文件后，`import` 写下的依赖由谁找到、链接和执行？见[import 写下后，谁负责找到、链接和执行文件？](./modules-and-host-boundaries.md)。

> [!info]- 来源
> - **“try 语句覆盖哪段控制流”：try/catch/finally 完成值优先级、async/await、`return` 与 `await`、Promise `catch` / `finally` 的结果传递、`Promise.all` 首个拒绝。** [ECMAScript 2026](https://tc39.es/ecma262/2026/)，正式版，§14.15、§15.8、§27.2.4.1、§27.2.5.1、§27.2.5.3。
> - **“报表链路上的失败点”：Fetch 响应、正文与取消。** [Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch)、[Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch) 与 DOM [AbortSignal](https://dom.spec.whatwg.org/#interface-AbortSignal)，Living Standards，核对日期 2026-11-12（Fetch 最近更新 2026-10-19，DOM 最近更新 2026-11-12）。HTTP 状态响应与网络错误、取消是不同结果；客户端取消不撤销服务端已发生的副作用。
> - **“错误值怎样补上下文又不丢根因”：`cause` 与 `instanceof`。** [ECMAScript 2026](https://tc39.es/ecma262/2026/)，§20.5.1.1（`Error` 的 `cause` 选项）与 §7.3.21（`instanceof` 按右侧构造函数的 `prototype` 身份沿原型链检查）。
> - **“全局 error 和 unhandledrejection 只是诊断信号”。** [HTML runtime script errors](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)、[HostPromiseRejectionTracker](https://html.spec.whatwg.org/multipage/webappapis.html#host-promise-rejection-tracker)，WHATWG HTML Living Standard（最近更新 2026-11-11），核对日期 2026-11-12：后补的拒绝处理器触发 `rejectionhandled`，静音经典脚本可跳过拒绝追踪。资源错误事件在元素上触发且不冒泡：[HTML 4.8.4.3.5 Updating the image data](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data)、[DOM event dispatch](https://dom.spec.whatwg.org/#concept-event-dispatch)。
> - **“React 错误边界只接住渲染错误”。** [React Component reference：`componentDidCatch`](https://react.dev/reference/react/Component#componentdidcatch) 与 [Catching rendering errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，官方文档 v19.3，核对日期 2026-11-12。
> - **运行核对。** 原稿在 Node.js v26.13.0 检查 `return promise` / `return await promise`、Promise `finally` 与拒绝链、任意抛出值、跨 realm Error、`Promise.all` 同组失败、计时器回调抛错与后补拒绝处理器的宿主事件；本次在 Node.js v26.13.1 重跑 `languageFinally`、两种 `return` 写法与 Promise `finally`，结果一致。Node 观测不外推为浏览器保证。
