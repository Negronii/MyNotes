# JavaScript 错误应在哪一层恢复、传播或上报？

## 案例背景

报表筛选触发三项并发 Fetch API（浏览器的应用程序编程接口）请求，分别取报表、摘要和权限；三者都校验成功后，同一报表 ID、排序和取消信号还可驱动迭代章节的分页行流。任一网络失败、HTTP（超文本传输协议）404、JSON（JavaScript 对象表示法）解析失败或结构错误，都由服务函数拒绝给页面；即使数据请求成功，组件渲染也仍可能出错。每个错误都要交给一个能决定下一步的层级：页面选择提示、保留旧数据或重试，渲染边界负责限定范围内的 user interface（用户界面，UI）兜底，全局处理器只记录遗漏。

## 报表请求的错误由谁接手？

异步章节的 loadReport(id, sort, signal) 并发取得并校验报表、摘要和权限；这个页面处理层接收它的三个结果或拒绝，而不是再定义一个只取报表的单请求。AbortController（中止控制器）提供 AbortSignal（中止信号），调用 abort() 向支持取消的请求发出中止。页面还可能快速切换筛选，因此每一代请求要有自己的中止控制器和序号：中止旧网络工作，并只允许最新一代更新报表、错误和 loading（加载）状态。

~~~javascript
let latestReportRequest = 0; // 页面级状态
let activeController = null;

async function onRefreshClick(sort) {
  const requestId = ++latestReportRequest;
  activeController?.abort();
  const controller = new AbortController();
  activeController = controller;
  setLoading(true);
  // 每代使用自己的 tbody；切换时立即移除旧行，旧异步写入只触碰旧容器。
  const rowTarget = document.createElement("tbody");
  const oldBody = rowsTable.tBodies[0];
  if (oldBody) oldBody.replaceWith(rowTarget);
  else rowsTable.append(rowTarget);
  const appendRow = async row => {
    const element = await prepareReportRow(row);
    rowTarget.append(element);
  };

  try {
    const { report, summary, permissions } =
      await loadReport(42, sort, controller.signal);
    if (requestId !== latestReportRequest) return;
    setReport(report);
    setSummary(summary);
    setPermissions(permissions);
    clearError();

    // validatePermissions 已验证 canReadRows 为布尔值；无权时不启动行流。
    if (permissions.canReadRows === true) {
      await appendReportRows(42, sort, null, controller.signal, appendRow);
    }
  } catch (error) {
    // 仅静默与本 signal.reason 完全相同的取消；独立错误即使已过期也记录。
    if (controller.signal.aborted && error === controller.signal.reason) return;
    if (!controller.signal.aborted) controller.abort(); // 停止仍在运行的同组请求
    reportError(error);
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
~~~

`rowsTable` 是页面拥有的表格元素，假定只有一份动态 tbody，替换它会保留静态 thead/tfoot，`prepareReportRow` 只准备一个本行 DOM 节点，不写共享界面。每次刷新先换上一个空 tbody，当前请求无行权限或失败时也不会继续暴露旧筛选的行。传入分页函数的 appendRow 闭包只持有本代 tbody；旧追加即使晚完成，也写入已经脱离当前页面的旧容器，不会混进新列表。

`loadReport` 来自[异步请求章节](./asynchronous-javascript.md#报表请求何时并发何时顺序等待)，返回已校验的三项基础数据；`appendReportRows` 来自[分页迭代章节](./iterators-and-generators.md#报表行怎样按页异步读取)，沿用这次的 sort 和 signal。Promise.all 自身不会取消同组请求；这里在处理非取消失败时显式中止共享 signal，停止仍支持取消的兄弟 Fetch 和行流。实际页面可把基础数据与行列表的 loading 拆开；这里用一个状态聚焦最新请求的错误归属。序号检查和 abort 各有作用：signal 尽力停止支持取消的 Fetch；若旧结果仍完成，序号阻止它覆盖当前筛选或清掉新请求的 loading。

> [!example] 两次筛选交错返回
> recent 请求先启动，随后 oldest 请求启动并使 recent 的 signal 中止。序号保护本节的报表、摘要、权限、用户可见错误和 loading 状态；旧请求的 finally 不会关闭 oldest 的 loading。真正的取消原因被静默；若旧请求恰好产生独立错误，仍会交给 reportError 记录，但不会覆盖当前筛选的提示。分页章节说明，每行追加前还会检查同一个 signal；若 append 已开始且不支持取消，它仍可能完成，但只写本代容器；容器已被新请求替换时，旧写入不会显示，也不会再开始下一行。只有最新一代完成、失败或被用户取消时，页面才清理这次 loading。

检查 response.ok 把“服务器给了一个 HTTP 响应”与“这个响应可供页面使用”分开。Fetch Promise 在响应可用时给出 Response；正文还需由 json() 读取，解析或运行时校验都可能失败。此例在权限字段允许后才调用分页函数，rows 接口仍必须在服务端重新验证权限。Fetch、JSON 和 Promise 的行为见异步章节。

> [!example] HTTP 404 如何走到界面提示？
> Fetch 成功拿到状态为 404 的 Response，所以不会因状态码自动拒绝；loadReport 检查 response.ok 后拒绝，把失败交给 onRefreshClick 的 catch。页面仍掌握当前筛选交互，于是更新错误提示并上报；finally 则关闭最新请求的 loading 状态。

页面能显示可恢复的错误，所以它可以在 catch 中更新界面。若一个底层 helper 只记录日志后正常返回，调用方会误以为 Promise 已成功；若当前层没有恢复决定，就把错误继续抛给知道页面上下文的上层。

## try/catch/finally 覆盖哪段控制流？

try/catch 捕获同步执行期间抛出的错误，也能捕获在 try 内 await 的 Promise 拒绝。语言中的 finally 代码块会在成功、拒绝或 return 离开时执行；若它自己 return 或 throw，就会用新的控制流完成替换原结果。清理代码通常只做清理，不要无意中覆盖业务结果。

~~~javascript
try {
  const data = await loadReport(42, currentSort, controller.signal);
  renderReport(data);
} catch (error) {
  showError(error);
  throw error; // 如果此层没有完成恢复，继续传播
} finally {
  setLoading(false);
}
~~~

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

Promise.finally() 方法不同：回调返回的普通成功值会被忽略，原 Promise 的成功值或拒绝原因继续传递；若回调返回 Promise 或 thenable（带 then 方法、会被 Promise 采用的值），会等待它完成。清理最终履行时保留原结果，清理抛错或最终拒绝才会让新 Promise 改为拒绝。

~~~javascript
Promise.resolve("报表值")
  .finally(() => Promise.resolve("清理结果"))
  .then(console.log); // 等清理 Promise 履行后，仍输出“报表值”

Promise.resolve("报表值")
  .finally(() => { throw new Error("清理失败"); })
  .catch(error => console.log(error.message)); // 清理失败
~~~

语言级 finally 和 Promise.finally 的时间边界也不同：`try { return pendingPromise; } finally { ... }` 会先退出 try 并运行 finally，async 函数随后才采用 pendingPromise 的结果；若要让同一 try/catch 捕获它的拒绝，或让 finally 等到它完成后再运行，应写 `return await pendingPromise`。

~~~javascript
async function returnBeforePromiseSettles(pendingPromise) {
  try {
    return pendingPromise;
  } finally {
    console.log("return pendingPromise 时 finally 先运行");
  }
}

async function waitBeforeFinally(pendingPromise) {
  try {
    return await pendingPromise;
  } finally {
    console.log("await 结束后 finally 才运行");
  }
}
~~~

try/catch 不会捕获稍后由计时器或事件回调抛出的错误，因为回调在独立的调用栈上执行，其 throw 没有被转换为原 try 正在等待的 Promise 拒绝；即使原 try 仍挂起在 await 上，也不能捕获这个独立 throw。若异步 API 把失败表示为 Promise，应 await 它，或给返回的 Promise 明确安装拒绝处理器。

~~~javascript
try {
  setTimeout(() => {
    throw new Error("这次抛错发生在未来的回调中");
  }, 0);
} catch (error) {
  // 捕获不到定时器回调中的错误
}

try {
  await loadReport(42, currentSort, controller.signal);
} catch (error) {
  // 可以捕获 loadReport 返回 Promise 的拒绝
}
~~~

Promise 的 catch 与 then 的拒绝处理器遵循同一条结果规则：返回普通值或最终履行的 Promise/thenable 才会恢复为成功；抛错或返回最终拒绝的 Promise/thenable，链仍保持拒绝。若只上报但要继续传播，应重新抛出：

~~~javascript
loadReport(42, currentSort, controller.signal)
  .catch(error => {
    reportError(error);
    throw error; // 只上报，没有恢复，继续拒绝
  });
~~~

用 Error 的 cause 属性包装失败，可补充当前层的上下文而保留原错误；该属性标准化于 ES2022。需要稳定错误类别或结构化字段时可继承 Error。现代运行环境支持直接继承内置 Error；只有目标转译环境无法正确设置内置子类原型时，才考虑 Object.setPrototypeOf 兼容处理。跨 iframe 或 JavaScript realm（运行时领域）以及重复安装依赖的边界上，instanceof 可能因构造函数身份不同而失败；可把稳定 code 和字段作为更可靠的跨边界判断依据。JavaScript 允许 throw 任意值，因此错误处理器也不应假设收到的一定是 Error 实例。

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

## 浏览器全局处理器能兜住什么？

浏览器的 window.onerror 可报告未捕获的脚本运行错误；跨源脚本若未使用 crossorigin 属性，或其响应未通过 Cross-Origin Resource Sharing（跨源资源共享，CORS），错误详情可能被限制。unhandledrejection 可记录最终没有拒绝处理器的 Promise 拒绝，但这是遗漏的诊断信号，不替代请求调用链内的恢复或传播。用它追踪问题时，也不要默认所有宿主对未处理拒绝采取相同策略。

资源加载错误有另一个边界：例如图片元素派发的 error 事件不冒泡。若通过父节点统一采集，应监听捕获阶段。从 window.onerror 处理器返回 true 会抑制默认错误报告；下面改用事件监听器，展示如何捕获非冒泡资源错误：

~~~javascript
window.addEventListener("unhandledrejection", event => {
  reportError(event.reason);
  // 仅当明确要抑制浏览器默认报告时才调用：
  // event.preventDefault();
});

window.addEventListener("error", event => {
  if (event.target !== window) {
    reportResourceFailure(event.target);
  }
}, true);
~~~

全局处理器适合最后记录遗漏。预期 HTTP 失败、校验错误或用户取消应在仍知道报表 id、筛选条件和交互上下文的地方处理。

## React 错误边界覆盖哪个 UI 范围？

React Error Boundary（错误边界）为其后代组件渲染期间抛出的错误切换到备用界面；class component（类组件）通过 static getDerivedStateFromError 更新备用状态，可用 componentDidCatch 上报组件栈。它不是 Promise 的拒绝处理器。

~~~jsx
class ReportBoundary extends React.Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    reportError(error, info.componentStack);
  }

  render() {
    if (this.state.failed) return <p>报表暂时无法显示。</p>;
    return this.props.children;
  }
}
~~~

当前 React 文档说明，错误边界不会捕获事件处理器、普通异步回调、服务端渲染错误或边界自身的错误；文档列出由 useTransition Hook（React 钩子）返回的 startTransition 函数启动的 Transition（过渡更新）内抛错这一例外。按钮处理器中的 Fetch 失败仍应像本章的 onRefreshClick 一样显式处理。不同 React 版本和框架集成可能增加自己的边界，应用应按实际版本核对。

> [!info]- 来源
> - 语言级 try/catch/finally 控制流、async return/await、Promise 拒绝传播与作业机制：ECMAScript 2027 规范（2026-11-05 草案快照），[TryStatement 求值](https://tc39.es/ecma262/#sec-try-statement-runtime-semantics-evaluation)、[async 函数](https://tc39.es/ecma262/#sec-async-function-definitions)、[Promise 对象](https://tc39.es/ecma262/#sec-promise-objects)、[thenable 采用作业](https://tc39.es/ecma262/#sec-newpromiseresolvethenablejob)、[Promise.prototype.finally](https://tc39.es/ecma262/#sec-promise.prototype.finally)。
> - Fetch 对 HTTP 响应与网络错误的区分：[Fetch Standard，Living Standard 2026-10-19：fetch processing model](https://fetch.spec.whatwg.org/#main-fetch)；中止请求：[abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)。
> - 浏览器 window.onerror、未处理拒绝与 image error：[HTML Standard，Living Standard 2026-11-05：runtime script errors](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)、[image data update algorithm](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data)；事件传播：[DOM Standard，Living Standard 2026-11-04：dispatching events](https://dom.spec.whatwg.org/#concept-event-dispatch)。
> - React 错误边界范围与 useTransition 例外：[React Component reference](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，核对日期 2026-11-06。
> - Error options cause 与 instanceof 的构造函数/prototype 检查：[ECMAScript 2027 Error constructor](https://tc39.es/ecma262/#sec-error-constructor)、[OrdinaryHasInstance](https://tc39.es/ecma262/#sec-ordinaryhasinstance)。
