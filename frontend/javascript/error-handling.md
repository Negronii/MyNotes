# Error Handling in JavaScript / JavaScript 错误处理

**Key terms / 关键词:** throw 抛出 · rejection Promise 拒绝 · error boundary 错误边界 · error cause 错误原因 · uncaught error 未捕获错误

Handle an error at the layer that owns enough context to recover, add information, or report it. A catch handler that only logs and then returns can silently convert failure into success; propagate failures when the caller must decide what to do. Browser globals, Node process handlers, and React boundaries have different scopes. / 应在拥有足够上下文进行恢复、补充信息或上报的层级处理错误。若 catch 只记录日志后正常返回，就可能把失败悄悄转换成成功；调用方仍需决策时应继续传播错误。浏览器全局处理器、Node 进程处理器和 React 错误边界的作用范围不同。

## Synchronous code and cleanup / 同步代码与清理

try/catch handles exceptions thrown while its protected code runs. finally runs when control leaves the block, including return or throw, unless control flow is overridden by finally itself. Avoid returning or throwing from finally because it replaces an earlier completion. / try/catch 处理受保护代码执行期间抛出的异常。控制流离开代码块时 finally 会运行，包括 return 或 throw；但 finally 自己也可以覆盖原控制流。应避免在 finally 中 return 或 throw，以免替换之前的结果。

```javascript
try {
  riskyOperation();
} catch (error) {
  throw error; // rethrow the same error
} finally {
  releaseResource();
}
```

Use finally for cleanup that must happen on either outcome. If adding context while propagating, preserve the original as cause with Error options supported in current runtimes (standardized in ES2022): new Error("Request failed", { cause: error }). / finally 适合用于无论成功或失败都必须执行的清理。若需补充上下文并继续传播，可使用当前运行时支持的 Error options（ES2022 标准化）保留 cause：new Error("Request failed", { cause: error })。

A try/catch does not catch a throw that happens later in a timer or other callback. It does catch a rejected Promise when the code awaits it inside the try block. / try/catch 不会捕获稍后在计时器或其他回调中抛出的错误；若在 try 块中 await 被拒绝的 Promise，则可以捕获该拒绝。

## Custom errors / 自定义错误

Extend Error when callers need a stable category or structured context. Modern JavaScript engines support built-in Error subclassing directly; Object.setPrototypeOf workarounds belong only to specific legacy transpilation targets. instanceof is realm- and constructor-dependent, so use stable error codes or fields when errors cross package or realm boundaries. / 调用方需要稳定错误类别或结构化上下文时可继承 Error。现代 JavaScript 引擎可直接继承内置 Error；只有特定旧转译目标才需要 Object.setPrototypeOf 补丁。instanceof 依赖 realm 和构造函数身份，错误跨包或跨 realm 时可改用稳定错误代码或字段。

```javascript
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = "ValidationError";
    this.field = field;
  }
}

try {
  validate(input);
} catch (error) {
  if (error instanceof ValidationError) {
    showFieldError(error.field, error.message);
  } else {
    throw error; // do not swallow an unexpected failure
  }
}
```

## Promise rejections and Fetch / Promise 拒绝与 Fetch

A catch handler recovers if it returns normally; the next then receives that value. Throwing or returning Promise.reject keeps the chain rejected. Around await, use try/catch and decide whether to recover or rethrow. / catch 处理器正常返回时会恢复，后续 then 收到它返回的值。再次抛错或返回 Promise.reject 会使链保持拒绝状态。await 周围可用 try/catch，再决定恢复还是继续抛出。

Fetch rejects for network-level failures, but an HTTP 404 or 500 is still a fulfilled Response. Check response.ok or status when HTTP success is required. / Fetch 遇到网络层失败时会拒绝，但 HTTP 404 或 500 仍会得到成功完成的 Response。需要 HTTP 成功状态时应检查 response.ok 或 status。

```javascript
async function loadData() {
  const response = await fetch("/api/data");
  if (!response.ok) {
    throw new Error("HTTP " + response.status);
  }
  return response.json();
}

loadData().catch(reportFailure);
```

Every rejection needs an owner somewhere in the call chain. A global unhandled-rejection event is useful for diagnostics, but it is a late signal and should not replace local recovery or deliberate propagation. The host controls its reporting and process behavior. / 每个拒绝都应在调用链某处由明确责任方处理。全局未处理拒绝事件可用于诊断，但它只是较晚的信号，不能替代局部恢复或明确传播。具体上报和进程行为由宿主决定。

## Browser-global reporting / 浏览器全局上报

These are browser APIs, not JavaScript-language or Node guarantees. Use them for last-resort reporting, not as a substitute for handling expected errors near the operation. / 以下是浏览器 API，不是 JavaScript 语言或 Node 的通用保证。它们适合最后兜底上报，不应代替在操作附近处理预期错误。

- window.onerror reports uncaught script errors; returning true suppresses the browser’s default error reporting. Cross-origin scripts may expose limited details unless the script uses `crossorigin="anonymous"` and the response grants the requesting origin access with CORS. / window.onerror 上报未捕获脚本错误；返回 true 会抑制浏览器默认错误报告。跨域脚本可能只暴露有限信息；需添加 `crossorigin="anonymous"`，并由响应通过 CORS 授权请求来源。
- The unhandledrejection event exposes an unhandled Promise rejection; preventDefault suppresses its default browser reporting behavior. / unhandledrejection 事件暴露未处理的 Promise 拒绝；preventDefault 可抑制浏览器默认报告行为。
- Image load failures fire an `error` event at the image element. These events do not bubble, so a capturing listener may be needed. / 图片加载失败时会在图片元素上触发 `error` 事件。该事件不会冒泡，因此可能需要捕获阶段监听器。

The [HTML image algorithm](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data) fires the failure event at the image element; the [DOM event rules](https://dom.spec.whatwg.org/#concept-event-dispatch) make capture listeners useful even when an event does not bubble. See also the HTML Standard’s [runtime-error](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors) and [unhandled-rejection](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections) sections. / [HTML 图片算法](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data) 会在图片元素上触发失败事件；根据 [DOM 事件规则](https://dom.spec.whatwg.org/#concept-event-dispatch)，即使事件不冒泡，捕获阶段监听器仍可观察到它。另见 HTML 标准的[运行时错误](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors)与[未处理 Promise 拒绝](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)章节。

These browser listeners show two reporting paths. The reporting functions below are illustrative placeholders; replace them with application-owned handling. / 以下浏览器监听器展示两种上报路径。示例中的上报函数仅用于说明，应替换为应用自己的处理。

```javascript
function reportRejection(reason) { console.error(reason); }
function reportResourceFailure(target) { console.error(target); }

window.addEventListener("unhandledrejection", event => {
  reportRejection(event.reason);
  // event.preventDefault(); // use only when suppressing default browser reporting
});

window.addEventListener("error", event => {
  if (event.target !== window) {
    reportResourceFailure(event.target); // resource element is the event target
  }
}, true); // capture non-bubbling resource error events
```

## React error boundaries / React 错误边界

A React error boundary displays fallback UI for errors thrown while rendering its descendant tree. The documented API uses a class component with static getDerivedStateFromError and optionally componentDidCatch for reporting. / React 错误边界可在后代组件树渲染抛错时显示备用 UI。官方 API 使用 class 组件实现 static getDerivedStateFromError，并可选用 componentDidCatch 上报。

```jsx
class ErrorBoundary extends React.Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    reportError(error, info.componentStack);
  }

  render() {
    if (this.state.failed) return <p>Something went wrong.</p>;
    return this.props.children;
  }
}
```

React documents that boundaries do not catch errors from event handlers, ordinary asynchronous callbacks, server-side rendering, or the boundary itself. Current React documentation describes an exception for errors thrown inside a transition started with the function returned by useTransition. Verify the React version and framework behavior for the application in question. / React 文档说明，错误边界不会捕获事件处理器、普通异步回调、服务端渲染或边界自身的错误。当前 React 文档对 useTransition 返回函数启动的 transition 中抛出的错误说明了例外情况。应按应用所用 React 版本和框架行为核实。

See [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary) for current behavior and limitations. / 当前行为和限制见 [React 错误边界文档](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)。

**Interview answer / 面试回答:** try/catch handles synchronous throws and awaited Promise rejections; Promise catch handles a chain’s rejection; global handlers provide host-specific diagnostics; React boundaries handle render failures in descendant components. Recover only when the current layer can decide what recovery means, and otherwise propagate the failure. / try/catch 处理同步抛错和 await 的 Promise 拒绝；Promise catch 处理链式拒绝；全局处理器提供宿主级诊断；React 错误边界处理后代组件渲染失败。只有当前层能决定恢复含义时才恢复，否则应继续传播错误。

Related: [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md); [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md).
