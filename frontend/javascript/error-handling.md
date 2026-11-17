# JavaScript 错误应在哪一层恢复、传播或上报？

## 案例背景

用户切换报表 42 的排序后，页面用浏览器的 Fetch API 并发请求报表、摘要和权限三项基础数据，由服务层函数校验响应；只有三项都成功且权限允许，页面才继续按游标逐页读取表格行。这条链路上任何一步都可能失败：网络中断、HTTP 404、响应 JSON 无法解析、数据结构不符合约定、分页接口重复返回游标，或者追加表格行时抛错。

这些错误该由谁处理？页面层知道当前筛选条件、中止信号和 user interface（用户界面，UI）状态，最适合决定显示什么提示、保留哪些旧数据、是否重试。React 的 error boundary（错误边界）负责另一类问题：组件树渲染失败时显示局部的备用界面。浏览器的全局错误事件可以记录宿主报告给页面的异常和未处理的 Promise 拒绝，但它们看到的并不是应用内全部未恢复的错误，也不能代替页面的恢复逻辑。本章按这三层依次展开。

一条错误链要回答三个问题：**哪个操作失败、哪个层仍有足够上下文、该层选择恢复还是继续拒绝？** 如果低层只记一条日志就正常返回，上层会误以为操作成功；反过来，页面若已决定恢复，也应明确结束原来的拒绝链，而不是让原错误又变成一条未处理的拒绝。

## 报表请求的错误由谁接手？

基础数据由异步章节的 [`loadReport(id, sort, signal)`](./asynchronous-javascript.md#报表请求何时并发、何时顺序等待？) 取得。它分两轮等待：第一轮 `Promise.all` 等三个 Fetch 都返回 `Response`，再逐一检查 HTTP 状态；状态都正常后，第二轮并发读取并解析三份 JSON，最后同步校验。它要么履行为三项已校验的数据，要么以失败原因拒绝。

页面为每次筛选创建自己的 AbortController（中止控制器）、AbortSignal（中止信号）和请求序号。两者解决不同问题：中止旧信号会尽力停止支持取消的网络工作；请求序号则防止没能取消、最终仍完成的旧请求覆盖较新的界面状态和 loading（加载中）状态。

下面的代码假定页面已有表格 `rowsTable`、刷新和取消按钮、排序控件、`setReport` 等状态更新函数，以及应用自己的诊断记录器 `diagnostics.capture`；同步初始化、DOM 替换和状态更新都按约定正常运行。`loadReport` 的契约如上；`appendReportRows(reportId, sort, stopAfterId, signal, appendRow)` 来自[游标分页迭代](./iterators-and-generators.md#报表行怎样按页异步读取？)，它逐页读取行，并对每一行等待 `appendRow(row)` 完成。表格只有一个动态 `tbody`，每次筛选都换上一个新的，因此迟到的旧行最多写进已经脱离文档的旧容器。`prepareReportRow` 只负责创建行节点，`appendRow` 再把节点加入本次筛选的容器。

> [!example]- 页面请求处理器的完整实现
> 请求序号决定能否提交界面状态，`rowTarget` 把本次筛选追加的行隔离在自己的容器里，`try/catch/finally` 决定页面怎样接手失败。后文分别跟踪换筛选、HTTP 失败和取消三种情况。
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
> 用户先按 `recent` 排序发起请求，随后改为 `oldest`。新请求先递增序号，再中止旧信号、换上新 `tbody`。请求序号保护报表、摘要、权限、用户可见的错误提示和 loading 状态，所以旧请求的 `finally` 不会关闭新请求的 loading。旧请求中已经开始、又无法取消的行追加，完成后最多写进已移除的旧容器；`appendReportRows` 在每次追加完成后检查信号，不会再拉取下一行。旧请求若出现其他错误，仍交给 `logReportError` 记录，但不会覆盖当前提示。

要判断错误从哪里来，先看每一步怎样失败。`fetch()` 拿到 `Response`（响应对象）就会履行；HTTP 404 也是一个正常的响应，需要代码检查 `response.ok` 后自己抛出应用错误。若在响应交给调用方之前中止，Fetch Promise 会以该信号的原因拒绝；若 Fetch 已经履行，之后的中止不会改变这个结果，但还在读取的 `response.json()` 会因响应体被中止而拒绝；`json()` 已经履行后再中止，也不会撤回解析出的值。JSON 解析可能因格式无效或响应体读取失败而拒绝；运行时结构校验则可能同步抛错。

回到 `loadReport` 的第一轮 `Promise.all`：只要有一个 Fetch Promise 先拒绝，`loadReport` 就立即以该原因拒绝，404 状态检查根本不会运行；若三项都履行，即使报表的 404 最先到达，也要等另外两项 `Response` 到齐后才被检查出来。`Promise.all` 拒绝本身不会中止其他请求；页面 `catch` 中的 `controller.abort()` 才是本例选择的同组取消策略。

> [!example] HTTP 404 如何走到界面提示？
> 假设报表 Fetch 得到 404，摘要和权限 Fetch 也都履行为 `Response`。第一轮 `Promise.all` 履行后，`loadReport` 检查 `response.ok` 并抛错；因为状态检查先于 `json()`，这条路径不读取三份响应体，也不提交新的报表/摘要/权限状态。`onRefreshClick` 的 `catch` 用 `logReportError` 记录原始值并显示当前请求的错误；它还显式中止当前控制器，随后 `finally` 关闭最新请求的 loading。上一次已提交的报表、摘要和权限状态仍然保留，但刷新开始时已换上空的 `tbody`，所以旧行不会保留；错误处理完成后，`onRefreshClick` 的 Promise 履行 `undefined`。若摘要或权限 Fetch 先拒绝，则它自己的拒绝会让第一轮 `Promise.all` 先拒绝，404 检查不会运行。

基础数据成功且权限允许后，`appendReportRows` 逐页追加行。它沿用当前排序和中止信号；每一页的游标要从上一页的响应中取得，所以不能预先当作已知页码并发请求。客户端的权限结果只决定是否发起行请求，行接口仍必须在服务端校验访问权限。

当前信号的取消会在两处被接住：基础三项请求若以与 `signal.reason` 完全相同的值拒绝，`onRefreshClick` 的 `catch` 直接静默返回；`appendReportRows` 自己也会捕获并吞掉这个原因，然后正常返回，因此分页阶段的取消不会进入页面的 `catch`。分页的其他错误（包括与 `signal.reason` 不同的追加错误）仍会传到页面处理器，被记录并为当前筛选显示提示。

以分页第一页的行 `r-101`、`r-102` 为例。如果用户在 `prepareReportRow(r-101)` 等待时点“取消”，已经开始的 `appendRow` 不会被撤回。当前筛选的 `tbody` 仍在页面上，所以这一行完成后仍可能出现；`appendReportRows` 随即复查信号、关闭迭代器并正常返回，不再交付同一页内存中的 `r-102`，也不请求下一页。页面的 `await appendReportRows(...)` 因而正常履行并跳过 `catch`，最新请求随后由 `finally` 关闭 loading。换筛选则走另一条路径：先递增请求序号，再中止旧信号、创建新信号并替换 `tbody`；旧行若在等待中完成，只能写进已脱离文档的旧容器，旧 `finally` 也不能关闭新请求的 loading。取消不能撤销已开始的 DOM 追加，序号和容器身份负责隔离换代结果。分页消费和游标依赖见[报表行怎样按页异步读取？](./iterators-and-generators.md#报表行怎样按页异步读取？)。

| 等待行追加时发生什么 | 已开始的 `r-101` 追加完成后写到哪里 | 接下来谁结束 loading？ |
|---|---|---|
| 当前筛选点“取消” | 当前 `tbody` 仍在页面上，行仍可能出现 | `appendReportRows` 追加后查到中止，关闭迭代器并正常返回；当前请求的 `finally` 关闭 loading |
| 改为新筛选 | 旧 `tbody` 已移除，晚到的旧行不会混入新表格 | 旧请求退出但不改新 loading；新请求自行完成、失败或取消后才关闭 |

总结一下分工：请求序号保护 loading、报表和用户可见的错误；信号只是请求协作式取消。已经开始又不支持取消的工作仍会完成，所以要靠请求序号和每次筛选独立的容器隔离它对 UI 的影响。记录器 `logReportError` 接收原始的拒绝值，不读取 `message`；无论 `diagnostics.capture` 同步抛错还是返回一个拒绝的 Promise，记录过程都不会替换页面中的原始错误，也不会留下新的未处理拒绝。如果记录器自己的失败也必须保存，需要另一个独立的诊断出口，不能递归调用同一个记录器。

## try/catch/finally 覆盖哪段控制流？

页面处理器的错误接手完全依赖语言的 `try/catch/finally`，下面看它到底覆盖哪些代码。`try/catch` 捕获的是 `try` 块执行期间、当前同步调用栈中抛出的值；在 `try` 块内 `await` 的 Promise 若拒绝，拒绝会在该 `await` 表达式处变成一次抛错，同样进入对应的 `catch`。捕获之后只有两条路：明确恢复，返回一个表示成功的新结果；或者继续抛出，让上层拿到错误。注意 JavaScript 的 `throw` 可以抛出任意值，不限于 `Error` 实例。

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

普通函数同步 `throw` 时，会进入调用栈上包围它的 `catch`。`async function` 则不同：即使在第一个 `await` 之前抛错，调用也只会返回一个拒绝的 Promise，不会同步抛出，调用方仍需 `await` 它或注册拒绝处理器。下面第二段代码在 `try` 中 `await` 了这个 Promise，`catch` 能处理它的拒绝；第一段代码中计时器回调的 `throw` 发生在稍后的另一个调用栈里，原来的 `try` 早已执行完毕：

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

语句级的 `finally` 在 `try` 正常结束、抛错或执行 `return` 时都会运行。若 `finally` 自己抛错或 `return`，就会替换原来的结果，可能把真正的业务失败掩盖掉：

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

在 async 函数中返回一个尚未完成的 Promise 时，写不写 `await` 有区别。`return pendingPromise` 会立即离开 `try` 并运行 `finally`，之后函数返回的 Promise 才跟随它的结局；即使它后来拒绝，也不会回到已经离开的 `catch`。`return await pendingPromise` 则在 `await` 处等待结局，拒绝会进入本层的 `catch`，然后才运行 `finally`：

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

`Promise.prototype.finally()` 是 Promise 链上的清理回调，与语句级 `finally` 不同：它忽略回调返回的普通值；若回调返回 Promise 或 thenable（带 `then` 方法、能被 Promise 采纳的对象），就等它完成。清理成功时，原链的履行值或拒绝原因原样继续传递；清理抛错或返回拒绝时，链改为以清理错误拒绝。

~~~javascript
Promise.resolve("报表值")
  .finally(() => Promise.resolve("清理结果"))
  .then(console.log); // 等清理 Promise 履行后，仍输出“报表值”

Promise.resolve("报表值")
  .finally(() => { throw new Error("清理失败"); })
  .catch(error => console.log(error.message)); // 清理失败
~~~

`.catch()` 和 `.then()` 的拒绝处理器也决定后续链的走向：返回普通值或最终履行的 Promise，后续链就恢复为履行；抛错或返回最终拒绝的 Promise，后续链就继续拒绝。每次调用 `.catch()` 或 `.then()` 都会返回一个新的 Promise。下面的诊断层记录后重新抛出，所以它返回的新 Promise 仍然拒绝；它把这个 Promise 交回调用方，由掌握上下文的页面层决定如何恢复：

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

错误一路向上传播时，每层可能要补充自己的上下文。当前层能确认错误含义时，可以给用户一条稳定、适合展示的消息，同时在诊断记录中保留原始错误。不要以为服务端返回的消息总能直接展示：它可能包含内部细节、用户数据或随实现变化的文字。页面的 `toUserMessage` 应按已知的错误类型或 `code` 映射到安全的文案，遇到未知值则用通用的兜底消息。

ES2022 起，`Error` 构造器支持 `cause`（原因）选项，可以在包装出带当前操作上下文的新错误时保留根因；`code` 这类稳定字段便于调用方按类别分支。`instanceof` 在构造函数只有一份的普通场景中可用，但跨 iframe 或 realm（执行环境），或同一个库被重复加载出多份构造函数时，错误对象继承的可能是另一份原型，判断就会失败。跨这类边界时，应依赖明确的字段或序列化格式，而不只靠 `instanceof`。只有当代码被转译到无法正确继承内置 `Error` 的旧目标（如 ES5）时，才需要针对该环境用 `Object.setPrototypeOf` 修复原型链。

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

由于 `throw` 可以抛出任意值，记录器也应能接受字符串、`null` 或普通对象。把原值直接交给诊断通道，不要先读取 `error.message`：抛出值是 `null` 时，读取 `message` 本身就会产生新的 `TypeError`，掩盖原来的拒绝。前面的 `logReportError` 正是这样做的，并且它也隔离了记录器自己的同步抛错和拒绝。面向 UI 的 `toUserMessage` 同样要对任意值给出安全的兜底文案。

## 浏览器全局处理器能兜住什么？

前几节都在页面内部处理错误。浏览器还提供全局入口：`window.onerror` 和全局 `error` 事件可以观察宿主报告的脚本异常，但出现在这里的并不都是应用没接住的错误。React 开发构建中，错误边界已经接住的渲染错误仍可能被 window 级错误监听看到；生产构建的报告方式不同。另外，HTML 的 muted errors（静音错误）规则会隐藏某些跨源 classic script（经典脚本）的错误细节：页面可能只看到通用的 `Script error.`，读不到完整信息；静音脚本中的 Promise 拒绝还可能根本不被追踪。要让页面拿到这类脚本的运行错误详情，需要在 `<script>` 上加 `crossorigin` 属性启用 Cross-Origin Resource Sharing（跨源资源共享，CORS）检查，并由服务器允许该来源。注意两种失败处在不同阶段：CORS 检查失败时脚本根本不会加载；静音则是脚本已经运行、只是错误细节被隐藏。

`unhandledrejection` 事件只在宿主准备报告时该拒绝仍无人处理才会触发。若页面在宿主报告前就给 Promise 加上了拒绝处理器，事件就不会派发；若宿主已经报告、之后才加上处理器，页面还会收到 `rejectionhandled`。因此这个事件发生时，拒绝发生时的调用栈早已结束，它也不能替代页面请求层的恢复。

图片、脚本等资源加载失败时，`error` 事件的目标是元素本身，而且不冒泡；若要在 Document Object Model（文档对象模型，DOM）的祖先节点或 `window` 上集中记录，必须注册捕获阶段的监听器。另外，`window.onerror` 处理器返回 `true` 会抑制该运行时错误的默认报告；下面改用 `addEventListener`，只记录而不抑制默认报告，同时用捕获阶段接住资源错误：

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

全局事件是诊断信号，既不是“应用中所有未处理错误”的完整清单，也不是每个异步操作的兜底 `catch`。可预期的失败应尽早回到掌握上下文的那一层处理；全局监听器不应把本可恢复的请求错误静默吞掉。

## React 错误边界覆盖哪个 UI 范围？

React 错误边界负责组件树渲染期间的错误：子组件渲染时抛错，边界显示局部的备用界面。错误边界目前只能写成类组件：用 `static getDerivedStateFromError` 切换到失败状态，再用 `componentDidCatch` 记录错误和组件栈。它捕获不到事件处理器和普通异步回调（如 `setTimeout`）中的错误，也捕获不到服务端渲染错误和边界自身抛出的错误。所以按钮触发的 Fetch 仍要像本章的 `onRefreshClick` 一样，自己 `await` 并处理拒绝。

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

`ReportTable` 渲染抛错后，边界状态变为 `failed: true`，它用备用段落替换表格；`ReportSortControl` 位于边界外，不会被这次失败替换。这个最小边界没有自动恢复动作；备用界面会一直保留，直到应用重置边界状态或重新挂载该边界。React 开发构建还可能把已被边界接住的错误同时报告到 `window`；这不代表边界没有接手。

React 当前文档列出一个例外：通过 `useTransition` Hook 返回的 `startTransition` 启动的 transition（过渡）函数中抛出的错误，可以被错误边界处理。不要把这个例外推广到普通事件处理器、任意 Promise 或其他宿主异步回调。若依赖特定 React 版本或框架集成的行为，应按项目实际使用的版本核对。

> [!info]- 来源
> - **语言级异常、`await` 与 `return`、Promise 组合/拒绝传播和 `finally`：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，正式版，§14.15、§15.8、§27.2.4.1、§27.2.5.1 与 §27.2.5.3。规范规定 try/catch/finally 控制流完成的优先级、async/await、`Promise.all` 首个拒绝、Promise `catch` 与 `finally` 的结果传递。
> - **Fetch 响应、响应体和取消：**[Response](https://fetch.spec.whatwg.org/#response-class)、[Body mixin](https://fetch.spec.whatwg.org/#body-mixin)、[Main fetch](https://fetch.spec.whatwg.org/#main-fetch)、[Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch) 与 DOM [AbortSignal](https://dom.spec.whatwg.org/#interface-AbortSignal)，相关 Living Standards，核对日期：2026-11-12（Fetch 最近更新 2026-10-19，DOM 最近更新 2026-11-12）。HTTP 状态响应与网络错误/取消是不同结果；客户端取消不提供撤销服务端已发生副作用的保证。
> - **浏览器全局运行时错误与未处理拒绝：**[HTML runtime script errors](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections) 与 [HostPromiseRejectionTracker](https://html.spec.whatwg.org/multipage/webappapis.html#host-promise-rejection-tracker)，WHATWG HTML Living Standard，核对日期：2026-11-12（标准标注最近更新 2026-11-11）。后安装拒绝处理器可触发 `rejectionhandled`；静音经典脚本可能跳过拒绝追踪。
> - **资源元素错误事件：**[HTML 4.8.4.3.5 Updating the image data](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data) 与 [DOM event dispatch](https://dom.spec.whatwg.org/#concept-event-dispatch)，Living Standards，核对日期：2026-11-12。资源 `error` 在元素上触发且不冒泡，祖先监听要使用 capture。
> - **错误边界范围与 window 事件：**[React Component reference: `componentDidCatch`](https://react.dev/reference/react/Component#componentdidcatch) 与 [Catching rendering errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，官方文档当前显示 v19.3，核对日期：2026-11-12。列出边界捕获范围、开发构建下已接住错误向 `window` 冒泡、生产构建下被接住错误不冒泡，以及 `useTransition` Hook 返回的 `startTransition` 例外。
> - **Error 原因与跨构造函数边界：**[ECMAScript 2026](https://tc39.es/ecma262/2026/)，§20.5.1.1 与 §7.3.21。`Error` 支持 `cause`；`instanceof` 按右侧构造函数的 prototype 身份沿继承链检查。
> - **运行核对：**Node.js `v26.13.0`；实际检查 `return promise` / `return await promise`、Promise `finally` 和拒绝链、任意 thrown value、跨 realm Error、Promise.all 同组失败、计时器回调 throw 与后装拒绝处理器的 Node 宿主事件。Node 观测不外推为浏览器保证。
