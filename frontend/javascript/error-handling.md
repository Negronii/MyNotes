# JavaScript 错误应在哪一层恢复、传播或上报？

## 案例背景

用户切换报表 42 的排序后，页面并发请求报表、摘要和权限。服务层校验响应；只有基础数据成功且权限允许，页面才继续读取游标分页的行。浏览器 Fetch API（网络请求接口）任一步都可能失败：网络中断、HTTP（超文本传输协议）404、响应 JSON（JavaScript 对象表示法）无法解析、数据结构不符合契约、分页重复游标，或行追加本身抛错。此时页面仍知道当前筛选、中止信号和 user interface（用户界面，UI）状态，适合决定显示提示、保留哪些旧数据或是否重试。错误边界处理另一类问题：组件树渲染失败时显示局部备用界面。全局事件可记录宿主报告到页面的异常或 Promise（表示异步结果的对象）拒绝，但事件可见范围不等同于应用内所有未恢复的错误，也不替代页面的恢复逻辑。

一条错误链要回答三个问题：**哪个操作失败、哪个层仍有足够上下文、该层选择恢复还是继续拒绝？** 错误在低层只记录日志后正常返回，会让上层误以为成功；页面若选择了可恢复状态，也应明确结束原拒绝链，而不是把原错误又变成一条未处理拒绝。

## 报表请求的错误由谁接手？

异步章节的 [`loadReport(id, sort, signal)`](./asynchronous-javascript.md#报表请求何时并发、何时顺序等待？) 并发取得并校验报表、摘要和权限；它返回这三项已校验数据，或者以失败原因拒绝。每个筛选请求有自己的 AbortController（中止控制器）、AbortSignal（中止信号）与请求序号。中止旧信号尽力停止支持取消的网络工作；序号则防止仍然完成的旧请求覆盖较新的界面状态和 loading（加载中）状态。两者解决不同问题。

下面代码假定页面已有表格、刷新/取消按钮、排序控件、状态更新函数和 `diagnostics.capture` 应用记录器；同步初始化、DOM 替换和状态更新函数按本例契约正常运行。`loadReport`、`appendReportRows` 的输入输出契约分别如上和[游标分页迭代](./iterators-and-generators.md#报表行怎样按页异步读取？)。表格只有一个动态 `tbody`；每次筛选换上新容器，因此迟到的旧行最多写进已经脱离文档的旧容器。`prepareReportRow` 只创建行节点，`appendReportRows` 收到的 `appendRow` 才把它加入这一代容器。

> [!example]- 页面请求处理器的完整实现
> 同一个请求序号负责提交界面状态，同一个 `rowTarget` 负责隔离本代追加；`try/catch/finally` 决定失败如何被页面接手。下面保留完整代码，后文分别跟踪换代、HTTP 失败和取消的结果。
>
> ~~~javascript
> let latestReportRequest = 0;
> let activeController = null;
>
> function logReportError(error, context) {
>   try {
>     Promise.resolve(diagnostics?.capture?.({ error, context })).catch(() => {});
>   } catch {
>     // 诊断出口自己的失败不替换原错误，也不再创建一条未处理拒绝。
>   }
> }
>
> async function onRefreshClick(sort) {
>   const requestId = ++latestReportRequest;
>   activeController?.abort();
>
>   const controller = new AbortController();
>   activeController = controller;
>   setLoading(true);
>
>   const rowTarget = document.createElement("tbody");
>   const oldBody = rowsTable.tBodies[0];
>   if (oldBody) oldBody.replaceWith(rowTarget);
>   else rowsTable.append(rowTarget);
>
>   const appendRow = async row => {
>     const element = await prepareReportRow(row);
>     rowTarget.append(element);
>   };
>
>   try {
>     const { report, summary, permissions } =
>       await loadReport(42, sort, controller.signal);
>     if (requestId !== latestReportRequest) return;
>
>     setReport(report);
>     setSummary(summary);
>     setPermissions(permissions);
>     clearError();
>
>     // 权限字段已由服务层校验为布尔值；无权时不发起行请求。
>     if (permissions.canReadRows === true) {
>       await appendReportRows(42, sort, null, controller.signal, appendRow);
>     }
>   } catch (error) {
>     // 只静默本请求的取消原因；其他错误仍留下诊断记录。
>     if (controller.signal.aborted &&
>         error === controller.signal.reason) return;
>
>     if (!controller.signal.aborted) controller.abort();
>     logReportError(error, { requestId, sort });
>     if (requestId !== latestReportRequest) return;
>     setError(toUserMessage(error));
>   } finally {
>     if (requestId === latestReportRequest) {
>       setLoading(false);
>       activeController = null;
>     }
>   }
> }
>
> cancelButton.addEventListener("click", () => activeController?.abort());
> refreshButton.addEventListener("click", () => {
>   void onRefreshClick(sortSelect.value)
>     .catch(error => logReportError(error, { source: "refresh handler" }));
> });
> ~~~

> [!example] 两次筛选交错返回
> `recent` 请求先启动，随后 `oldest` 请求启动。新一代先递增序号，再中止旧信号并换上新 `tbody`。请求序号保护报表、摘要、权限、用户可见错误和 loading 状态；旧请求的 `finally` 不会关闭新请求的 loading。旧追加若已开始且不支持取消，完成后最多写入已移除的旧容器；追加 helper 在完成后检查信号，不再拉取下一行。旧请求若产生独立错误，仍交给 `logReportError` 记录，但不会覆盖当前提示。

`fetch()` 在得到可用的 `Response`（响应对象）时履行；HTTP 404 仍是响应，需由 `response.ok` 检查变成应用错误。若响应还没交到调用方就中止，Fetch Promise 可因该 signal 拒绝；若 Fetch 已履行，之后的中止不会改写这项履行，但仍在读取的 `response.json()` 会因响应体被中止而拒绝。JSON 已经履行后再中止，也不会撤回该值。JSON 解析可能因无效格式或响应体读取失败而拒绝；运行时结构校验可能同步抛错。

当前 `loadReport` 先对三项 Fetch Promise 做第一轮 `Promise.all`，全部交付 `Response` 后才检查状态；如果一项 Fetch Promise 先拒绝，`loadReport` 会立即以该原因拒绝，尚未运行 404 状态检查。若三项都履行，即使报表的 404 先到，也要等另外两项 `Response` 到达后才检查。`Promise.all` 拒绝本身不会中止其他请求；页面 `catch` 中的 `controller.abort()` 才是本例选择的同组取消策略。

> [!example] HTTP 404 如何走到界面提示？
> 假设报表 Fetch 得到 404，而摘要与权限 Fetch 也都履行为 `Response`。第一轮 `Promise.all` 才履行，`loadReport` 随后检查 `response.ok` 并抛错；因为状态检查先于 `json()`，这条路径不读取三份响应体，也不提交新的报表/摘要/权限状态。`onRefreshClick` 的 `catch` 用 `logReportError` 记录原始值并显示当前请求的错误；它显式中止当前控制器，`finally` 关闭最新请求的 loading。上一次已提交的报表、摘要和权限状态仍在，但页面开始刷新时已换上空的 `tbody`，因此旧行不保留；错误处理完成后，`onRefreshClick` 的 Promise 履行 `undefined`。若摘要或权限 Fetch 先拒绝，则它自己的拒绝会让第一轮 `Promise.all` 先拒绝，404 检查不会运行。

权限校验通过后，`appendReportRows` 逐页追加行。它沿用当前排序和中止信号；下一页依赖上一页给出的游标，不能被当作五个已知页码并发发起。客户端权限结果只决定是否发起行请求，行接口仍必须在服务端验证访问权。当前 signal 的取消会在两处被接手：基础三项请求若以完全相同的 `signal.reason` 拒绝，`onRefreshClick` 的 `catch` 会静默；分页 helper 自己也捕获并吞掉匹配原因，再正常返回，因此分页取消不会进入页面 `catch`。分页的独立错误（包括与 signal reason 不同的追加错误）仍会到页面处理器，记录并为当前筛选显示提示。

如果用户在 `prepareReportRow(r-101)` 等待时取消，已经开始的 `appendRow` 不会因此被撤回。当前筛选的 `tbody` 仍在页面上，所以这行完成后仍可能出现；helper 随即复查 signal、关闭迭代器并正常返回，不拉取缓存中的 `r-102` 或下一页。页面的 `await appendReportRows(...)` 因而正常履行并跳过 `catch`，最新请求随后由 `finally` 关闭 loading。换筛选则是另一条轨迹：先递增新请求序号，再中止旧 signal、创建新 signal 并替换 `tbody`；旧行若在等待中完成，只能写进已脱离文档的旧容器，旧 `finally` 也不能关闭新请求的 loading。取消不能撤销已开始的 DOM 追加，序号和容器身份负责隔离换代结果。分页消费和游标依赖见[报表行怎样按页异步读取？](./iterators-and-generators.md#报表行怎样按页异步读取？)。

| 等待行追加时发生什么 | 已开始的 `r-101` 追加完成后写到哪里 | 接下来谁结束 loading？ |
|---|---|---|
| 当前筛选点“取消” | 当前 `tbody` 仍在页面上，行仍可能出现 | helper 追加后查到中止，关闭迭代器并正常返回；当前请求的 `finally` 关闭 loading |
| 改为新筛选 | 旧 `tbody` 已移除，晚到的旧行不会混入新表格 | 旧请求退出但不改新 loading；新请求自行完成、失败或取消后才关闭 |

请求序号保护 `loading`、报表和用户可见错误；signal 则请求协作式取消。已开始但不支持取消的工作仍会完成，所以必须以序号和每代容器隔离其 UI 副作用。记录器 `logReportError` 接收原始拒绝值，不读取 `message`；无论注入记录器同步抛错还是返回拒绝 Promise，记录路径都不会替换页面中的原始错误或留下新的未处理拒绝。记录器自己的失败若必须保留，需要独立的诊断出口，不能递归调用同一记录器。

## try/catch/finally 覆盖哪段控制流？

`try/catch` 捕获当前同步调用栈中 `try` 语句执行时抛出的值；在 `try` 内 `await` 的 Promise 若拒绝，拒绝会在该 `await` 表达式处重新表现为抛错，也会进入对应的 `catch`。捕获后要么明确恢复并返回可说明成功的新结果，要么继续抛出，让更上层拿到错误。JavaScript 的 `throw` 可以抛任意值，不只 `Error` 实例。

~~~javascript
try {
  const data = await loadReport(42, currentSort, controller.signal);
  renderReport(data);
} catch (error) {
  showError(toUserMessage(error));
  throw error; // 本层只更新了提示，若契约仍需拒绝，就继续传播
} finally {
  setLoading(false);
}
~~~

普通函数在当前调用栈同步 `throw` 时会进入包围它的 `catch`。`async function` 即使在第一个 `await` 前抛错，调用本身也会返回一个拒绝的 Promise，不会同步抛出；调用方仍需 `await` 或安装拒绝处理器。下面等待的 Promise 是同一个 `try` 里的异步操作，`catch` 能处理其拒绝；计时器回调的 `throw` 则稍后在独立调用栈发生，并不会被当成原 `try` 中 Promise 的拒绝：

~~~javascript
try {
  setTimeout(() => {
    throw new Error("未来计时器回调中的抛错");
  }, 0);
} catch (error) {
  // 捕获不到计时器回调中的抛错
}

try {
  await loadReport(42, currentSort, controller.signal);
} catch (error) {
  // 可以捕获 loadReport 返回 Promise 的拒绝
}
~~~

语言级 `finally` 会在 `try` 正常结束、抛错或执行 `return` 时运行。若 `finally` 自己抛错或 return，会替换原先的控制流结果，可能覆盖真正的业务失败：

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

对尚未完成的 Promise，`return pendingPromise` 会先运行 `finally`，之后 async 函数返回的 Promise 才采用它的结局；若它拒绝，拒绝不会回到已经离开的 `catch`。`return await pendingPromise` 则在 `await` 处等待结局，拒绝会进入本层 `catch`，随后才运行 `finally`：

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

`Promise.prototype.finally()` 是 Promise 链上的清理回调，并不等同于语法级 `finally`。它忽略回调返回的普通值，等回调返回的 Promise 或 thenable（带 `then` 方法、会被 Promise 接纳的对象）完成；若清理成功，原链的履行值或拒绝原因继续传递；若清理抛错或返回拒绝，链改为拒绝清理错误。

~~~javascript
Promise.resolve("报表值")
  .finally(() => Promise.resolve("清理结果"))
  .then(console.log); // 等清理 Promise 履行后，仍输出“报表值”

Promise.resolve("报表值")
  .finally(() => { throw new Error("清理失败"); })
  .catch(error => console.log(error.message)); // 清理失败
~~~

同理，`catch` / `then` 的拒绝处理器返回普通值或最终履行的 Promise，会把后续链恢复为履行；抛错或返回最终拒绝的 Promise，则继续拒绝。每次调用 `.catch()` 或 `.then()` 都会返回一个新的 Promise；若拒绝处理器记录后重抛，这个新 Promise 仍拒绝。要把它交回调用方，并由有上下文的页面接手：

~~~javascript
function loadReportWithDiagnostic(sort, signal) {
  return loadReport(42, sort, signal)
    .catch(error => {
      logReportError(error, { operation: "load report" });
      throw error; // 原 Promise 不变；这个 catch 返回的新 Promise 仍拒绝
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

## 错误值怎样补充上下文而保留根因？

在当前层能确认错误含义时，可给用户返回稳定且适合显示的消息，同时在诊断记录保留原始错误。不要假设服务端消息总适合直接显示：它可能含内部细节、用户数据或不稳定的实现文字。页面的 `toUserMessage` 应按已知错误类型或 code 映射到安全文案，未知值使用普通兜底消息。

`Error` 构造器自 ES2022 支持的 `cause`（原因）选项可在增加当前操作上下文时保留根因；`code` 等稳定字段可帮助调用方做类别分支。`instanceof` 适合同一构造函数身份的普通边界，但跨 iframe / realm（JavaScript 运行时领域）或重复加载不同构造函数副本时，对象可能继承另一份 `Error.prototype`，判断就会失败。跨边界契约可依赖明确的字段或序列化格式，而不是只依赖 `instanceof`。只有目标转译环境无法正确继承内置 `Error` 原型时，才考虑针对该环境用 `Object.setPrototypeOf` 修复继承链。

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

记录器也应接受任意抛出值（thrown value），例如字符串、`null` 或普通对象；保持原值交给诊断通道，不先读取 `error.message`，避免把原始拒绝改成新的 `TypeError`。示例的 `logReportError` 也隔离记录器同步抛错和返回 Promise 的拒绝，不让记录失败替换原始业务错误或产生未处理的派生 Promise。面向 UI 的 `toUserMessage` 则要对任意值给出安全兜底。

## 浏览器全局处理器能兜住什么？

浏览器的 `window.onerror` 和全局 `error` 事件可观察宿主报告的脚本异常，但并非只有未被应用接住的错误才可能出现。React 开发构建中，错误边界已经接住的渲染错误仍可能被 window 级错误监听看到；生产构建的报告方式不同。HTML 的“muted errors（静音错误）”规则会在某些跨源经典脚本（classic script）错误中隐藏细节：页面可能只看到通用的 `Script error.`，无法读取完整错误详情；静音脚本还可能完全跳过 Promise 拒绝追踪。若要把脚本运行错误详情交给页面处理，需用 `crossorigin` 启用 Cross-Origin Resource Sharing（跨源资源共享，CORS）检查，并由服务器允许该来源；若 CORS 检查失败，脚本本身不会成功加载，这与“脚本已运行但错误详情被静音”处于不同阶段。

`unhandledrejection` 只在宿主派发报告任务时该拒绝仍未处理的情况下触发。若页面在宿主派发任务前就给 Promise 加上拒绝处理器，事件可以不派发；若宿主已报告、之后才安装处理器，页面还可能收到 `rejectionhandled`。因此这个事件既不表示拒绝发生的原调用栈，也不能替代页面请求层的恢复。

资源元素的失败还要区分事件目标。图片元素自己的 `error` 事件不冒泡；若要在 Document Object Model（文档对象模型，DOM）父容器集中记录，应注册捕获阶段监听器。`window.onerror` 处理器返回 `true` 会抑制该运行时错误的默认报告；下面改用事件监听器，只展示如何捕获非冒泡资源错误，不会抑制默认脚本错误报告：

~~~javascript
window.addEventListener("unhandledrejection", event => {
  logReportError(event.reason, { source: "unhandledrejection" });
  // 只有明确要取消 unhandledrejection 的默认报告时才调用 event.preventDefault()
});

window.addEventListener("error", event => {
  if (event.target === window) {
    logReportError(event.error, { source: "window error" });
  } else {
    logReportError(undefined, { source: "resource error", target: event.target });
  }
}, true); // 同时记录全局脚本错误与捕获阶段的资源 error
~~~

全局事件是诊断信号，不是“所有应用未处理错误”的完整清单，也不是每个异步操作的兜底 catch。预期失败应该尽早回到最有上下文的层；全局监听不应把可恢复的请求错误静默掉。

## React 错误边界覆盖哪个 UI 范围？

React 错误边界为子组件在渲染期间抛出的错误提供局部备用界面。类组件可用 `static getDerivedStateFromError` 切换失败状态，再用 `componentDidCatch` 记录错误和组件栈。边界不能捕获事件处理器或普通异步回调中发生的错误，也捕获不了服务端渲染错误、边界自身抛出的错误。按钮中的 Fetch 仍要像本章 `onRefreshClick` 一样显式 await 并处理拒绝。

~~~jsx
class ReportBoundary extends React.Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    logReportError(error, { componentStack: info.componentStack });
  }

  render() {
    if (this.state.failed) return <p>报表暂时无法显示。</p>;
    return this.props.children;
  }
}
~~~

把边界包在要替换的表格子树外，边界外的排序控件仍然可用：

~~~jsx
<div>
  <ReportSortControl />
  <ReportBoundary>
    <ReportTable />
  </ReportBoundary>
</div>
~~~

`ReportTable` 渲染抛错后，边界状态变为 `failed: true`，它用备用段落替换表格；`ReportSortControl` 位于边界外，不会被这次失败替换。这个最小边界没有自动恢复动作；备用界面会一直保留，直到应用重置边界状态或重新挂载该边界。React 开发构建可能同时把已接住错误报告到 `window`；这不表示 boundary 没有接手。

React 当前文档列出一个范围例外：由 `useTransition` 钩子返回的 `startTransition` 函数启动的 transition（过渡）函数中抛出的错误可被错误边界处理。不要把这条限定扩大到普通事件处理器、任意 Promise 或任何宿主异步回调。需要依赖特定框架版本或框架集成时，再按项目实际版本核对边界行为。

> [!info]- 来源
> - **语言级异常、`await` 与 `return`、Promise 组合/拒绝传播和 `finally`：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，正式版，§14.15、§15.8、§27.2.4.1、§27.2.5.1 与 §27.2.5.3。规范规定 try/catch/finally 控制流完成的优先级、async/await、`Promise.all` 首个拒绝、Promise `catch` 与 `finally` 的结果传递。
> - **Fetch 响应、响应体和取消：**[Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch)、[Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch) 与 DOM [AbortSignal](https://dom.spec.whatwg.org/#interface-AbortSignal)，相关 Living Standards，核对日期：2026-11-12（Fetch 最近更新 2026-10-19，DOM 最近更新 2026-11-12）。HTTP 状态响应与网络错误/取消是不同结果；客户端取消不提供撤销服务端已发生副作用的保证。
> - **浏览器全局运行时错误与未处理拒绝：**[HTML runtime script errors](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections) 与 [HostPromiseRejectionTracker](https://html.spec.whatwg.org/multipage/webappapis.html#host-promise-rejection-tracker)，WHATWG HTML Living Standard，核对日期：2026-11-12（标准标注最近更新 2026-11-11）。后安装拒绝处理器可触发 `rejectionhandled`；静音经典脚本可能跳过拒绝追踪。
> - **资源元素错误事件：**[HTML 4.8.4.3.5 Updating the image data](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data) 与 [DOM event dispatch](https://dom.spec.whatwg.org/#concept-event-dispatch)，Living Standards，核对日期：2026-11-12。资源 `error` 在元素上触发且不冒泡，祖先监听要使用 capture。
> - **错误边界范围与 window 事件：**[React Component reference: `componentDidCatch`](https://react.dev/reference/react/Component#componentdidcatch) 与 [Catching rendering errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，官方文档当前显示 v19.3，核对日期：2026-11-12。列出边界捕获范围、开发构建下已接住错误向 `window` 冒泡、生产构建下被接住错误不冒泡，以及 `useTransition` Hook 返回的 `startTransition` 例外。
> - **Error 原因与跨构造函数边界：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，§20.5.1.1 与 §7.3.21。`Error` 支持 `cause`；`instanceof` 按右侧构造函数的 prototype 身份沿继承链检查。
> - **运行核对：**Node.js `v26.13.0`；实际检查 `return promise` / `return await promise`、Promise `finally` 和拒绝链、任意 thrown value、跨 realm Error、Promise.all 同组失败、计时器回调 throw 与后装拒绝处理器的 Node 宿主事件。Node 观测不外推为浏览器保证。
