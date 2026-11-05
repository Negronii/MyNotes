# Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？

**Core answer / 核心回答：** Handle a failure at the layer with enough context to recover, add information, or report it. If the current layer cannot decide what recovery means, propagate the error. A catch that only logs and returns can silently turn failure into success; browser-global and React handlers cover specific last-resort scopes. / 应在拥有足够上下文进行恢复、补充信息或上报的层级处理错误。当前层无法决定如何恢复时，应继续传播。只记录日志后正常返回的 catch 会悄悄把失败转成成功；浏览器全局处理器和 React 边界只覆盖特定的兜底范围。

## What try/catch/finally cover / try/catch/finally 能处理什么

try/catch handles an exception thrown while protected code runs. finally runs when control leaves the block, including return or throw, unless finally itself overrides the completion. Avoid returning or throwing from finally because it replaces an earlier result or error. / try/catch 处理受保护代码执行期间抛出的异常。控制流离开代码块时 finally 会运行，包括 return 或 throw；但 finally 自己可以覆盖原结果。不要在 finally 中 return 或 throw，以免替换之前的结果或错误。

~~~javascript
try {
  riskyOperation();
} catch (error) {
  throw error; // keep propagating the same error
} finally {
  releaseResource();
}
~~~

Use finally for cleanup required on either outcome. To add context while propagating, preserve the original with Error options cause (standardized in ES2022): new Error("Request failed", { cause: error }). / finally 适合放置成功、失败都必须执行的清理。若需补充上下文并继续传播，可通过 Error options 的 cause 保留原始错误（ES2022 标准化）：new Error("Request failed", { cause: error })。

## When to define a custom Error / 何时定义自定义 Error

Extend Error when callers need a stable category or structured context. Modern JavaScript engines support built-in Error subclassing directly; Object.setPrototypeOf workarounds are for particular legacy transpilation targets. instanceof depends on realm and constructor identity, so stable codes or fields may be more reliable when errors cross package or realm boundaries. / 调用方需要稳定错误类别或结构化上下文时可继承 Error。现代 JavaScript 引擎支持直接继承内置 Error；Object.setPrototypeOf 补丁只适用于特定旧转译目标。instanceof 依赖 realm 和构造函数身份，因此错误跨包或跨 realm 时，稳定的 code 或字段可能更可靠。

~~~javascript
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
    throw error; // unexpected failure still propagates
  }
}
~~~

A try/catch does not catch a throw that happens later inside a timer or another callback. It does catch a rejected Promise when the code awaits that Promise inside the try block. / try/catch 不会捕获稍后在计时器或其他回调中发生的抛错；若在 try 块中 await 被拒绝的 Promise，则可捕获该拒绝。

## How to propagate or recover a Promise rejection / 如何传播或恢复 Promise 拒绝

A catch handler recovers when it returns normally; the next then receives that value. Throwing or returning Promise.reject keeps the chain rejected. Around await, catch the rejection and choose deliberately whether to recover or rethrow. / catch 处理器正常返回即表示恢复，后续 then 收到该返回值。再次抛错或返回 Promise.reject 会让链保持拒绝。await 周围捕获拒绝后，应明确选择恢复还是继续抛出。

Fetch rejects for network-level failures, but an HTTP 404 or 500 still fulfills with a Response. Check response.ok or response.status when HTTP success is required. / Fetch 遇到网络层失败时会拒绝，但 HTTP 404 或 500 仍会以 Response 成功完成。需要 HTTP 成功状态时检查 response.ok 或 response.status。

~~~javascript
async function loadData() {
  const response = await fetch("/api/data");
  if (!response.ok) {
    throw new Error("HTTP " + response.status);
  }
  return response.json();
}

loadData().catch(reportFailure);
~~~

Every rejection needs an owner somewhere in the call chain. The browser’s unhandledrejection event is useful for diagnostics, but it is a late signal, not a substitute for local recovery or deliberate propagation. Host reporting and process behavior differ. See [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) for Promise chain mechanics. / 每个拒绝都应由调用链某处明确负责。浏览器的 unhandledrejection 事件可用于诊断，但只是较晚的信号，不能替代本地恢复或明确传播。宿主上报和进程行为有所不同。Promise 链机制见 [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md)。

## What browser-global handlers cover / 浏览器全局处理器覆盖什么

These are browser APIs, not JavaScript-language or Node guarantees. Use them for last-resort reporting rather than handling expected failures far from their source. / 以下是浏览器 API，不是 JavaScript 语言或 Node 的保证。它们适合最后兜底上报，不应用来远距离处理预期失败。

- window.onerror reports uncaught script errors; returning true suppresses default browser reporting. Cross-origin scripts may expose limited details unless crossorigin="anonymous" is used and the response grants access with CORS.
- unhandledrejection exposes an unhandled Promise rejection; preventDefault suppresses its default browser reporting.
- Image load failure fires error on the image element. The event does not bubble, so a capturing listener may be needed.

The [HTML image algorithm](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data) dispatches the failure event at the image element; the [DOM event rules](https://dom.spec.whatwg.org/#concept-event-dispatch) explain capture behavior for non-bubbling events. See the HTML Standard’s [runtime-error](https://html.spec.whatwg.org/multipage/webappapis.html#runtime-script-errors) and [unhandled-rejection](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections) sections.

~~~javascript
function reportRejection(reason) { console.error(reason); }
function reportResourceFailure(target) { console.error(target); }

window.addEventListener("unhandledrejection", event => {
  reportRejection(event.reason);
  // event.preventDefault(); // only when suppressing default reporting is intended
});

window.addEventListener("error", event => {
  if (event.target !== window) {
    reportResourceFailure(event.target); // resource element is the event target
  }
}, true); // capture non-bubbling resource error events
~~~

## What React error boundaries cover / React 错误边界覆盖什么

A React error boundary displays fallback UI for errors thrown while rendering its descendant tree. The documented API uses a class component with static getDerivedStateFromError and optionally componentDidCatch for reporting. / React 错误边界会为后代组件树渲染期间抛出的错误显示备用界面。官方 API 使用 class 组件实现 static getDerivedStateFromError，可选用 componentDidCatch 上报。

~~~jsx
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
~~~

React documentation says boundaries do not catch errors from event handlers, ordinary asynchronous callbacks, server-side rendering, or the boundary itself. Current React documentation describes an exception for errors thrown inside a transition started with the function returned by useTransition. Check the app’s React version and framework behavior. See [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary). / React 文档说明，边界不会捕获事件处理器、普通异步回调、服务端渲染或边界自身抛出的错误。当前 React 文档列出由 useTransition 返回函数启动的 transition 中抛错的例外情况。应核对应用使用的 React 版本和框架行为，详见 [React 错误边界](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)。
