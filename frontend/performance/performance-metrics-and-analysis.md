# Performance Metrics and Analysis / 性能指标与分析

## What are the Core Web Vitals? / 什么是Core Web Vitals？

**Core answer / 核心回答：** The current Core Web Vitals are LCP for loading, INP for responsiveness, and CLS for visual stability. “Good” thresholds are LCP at or below 2.5 seconds, INP at or below 200 ms, and CLS at or below 0.1, evaluated at the 75th percentile of real page visits, segmented by mobile and desktop. / 当前 Core Web Vitals 包括衡量加载的 LCP、衡量响应性的 INP，以及衡量视觉稳定性的 CLS。“良好”阈值为 LCP 不超过 2.5 秒、INP 不超过 200 毫秒、CLS 不超过 0.1，并按真实访问数据的第 75 百分位评估。

| Metric | What it measures | Good threshold |
|---|---|---:|
| **LCP** | When the largest image or text block in the viewport is rendered. | ≤ 2.5 s |
| **INP** | A latency intended to represent all or nearly all interactions during a page visit. | ≤ 200 ms |
| **CLS** | Unexpected visual instability from layout shifts. | ≤ 0.1 |

### Other render and navigation milestones / 其他渲染与导航里程碑

| Milestone | Meaning |
|---|---|
| **FCP** | First Contentful Paint: the first text or image content is rendered. |
| **DOMContentLoaded (DCL)** | The HTML is parsed and deferred/module scripts have executed; it does not wait for images or async scripts. |
| **load** | The document and dependent resources such as scripts, stylesheets, frames, and non-lazy images have loaded. |

These milestones have different scopes; do not treat them as a fixed sequence with LCP. DCL is useful when DOM readiness matters, while load waits for dependent resources.

FID was retired as a Core Web Vital in March 2024 and replaced by INP. FCP, TTFB, long tasks, and TBT remain useful diagnostic metrics, but they are not Core Web Vitals.

### Field data and lab data / 真实用户数据与实验室数据

Core Web Vitals are primarily field metrics. Real-user monitoring shows the experience across actual devices, networks, routes, and interactions. Lab tools such as Lighthouse and DevTools help reproduce and diagnose issues before release, but their results do not equal field results.

Lighthouse cannot measure a page's real INP without user interactions; Total Blocking Time is a lab proxy, not the same metric. A load-only lab run may also miss layout shifts caused later by interaction. Compare field data at the same percentile and device segment when checking whether users improved.

## How do you profile a page? / 如何分析页面性能？

Use tools that answer a specific question:

- **Performance panel:** inspect main-thread tasks, rendering, layout, and interaction traces.
- **Network panel:** inspect request timing, blocking, transfer size, and cache behavior.
- **React Profiler:** inspect which components render during a recorded interaction.
- **Lighthouse:** collect a repeatable lab trace and diagnostic opportunities.

Record the route, device and network conditions, browser, and whether the measurement is field or lab. A score is a signal; inspect the trace and user impact before choosing a fix.

## How do you diagnose a slow page? / 如何诊断页面变慢？

**Core answer / 核心回答：** Separate slow initial display from slow interaction, then identify the dominant cost before changing code. The cause may be server response, network transfer, JavaScript execution, layout, rendering, or a specific event handler. / 先区分首屏显示慢和交互响应慢，再找出主要成本后修改代码。原因可能是服务端响应、网络传输、JavaScript 执行、布局、绘制或特定事件处理器。

| Symptom | Inspect first |
|---|---|
| Main content appears late | TTFB, redirects, critical requests, LCP resource discovery and render delay. |
| Input feels delayed | Long main-thread tasks, event-handler work, and work scheduled after input. |
| Content jumps | Missing image or embed dimensions, late injected content, and font swaps. |
| Route bundle is large | Emitted chunk composition and whether deferred code is actually split. |

Potential changes include caching immutable assets, reducing unnecessary JavaScript, splitting rarely used routes, reserving image space, and virtualizing a measured long list. Re-measure the same user-visible interaction after the change.

## How does HTTP caching help? / HTTP缓存如何帮助性能？

A fresh cached response can be reused according to its freshness policy. After it becomes stale, validators such as ETag can let a client ask whether the representation changed; the server can answer that the stored response remains valid. Content-hashed assets can use a long freshness lifetime because a changed file receives a different URL.

- **Cache-Control: max-age=N** sets a freshness lifetime.
- **Cache-Control: no-cache** permits storage but requires validation before reuse.
- **Cache-Control: no-store** instructs caches not to store the response.
- **ETag** is a validator used with conditional requests; it is not itself a cache lifetime.

Choose policy by resource and user-data sensitivity. Do not apply one cache rule to both versioned static assets and personalized responses.

## What is the difference between debounce and throttle? / debounce和throttle有什么区别？

**Core answer / 核心回答：** Debounce waits until calls pause for a chosen interval; throttle limits how often work runs while calls continue. Both have leading and trailing variants, so state which edge runs and whether a final call is retained. / debounce 等调用停止一段指定时间后再执行；throttle 在调用持续发生时限制执行频率。两者都有 leading 和 trailing 变体，因此要说明在哪个边缘执行，以及是否保留最后一次调用。

This minimal implementation is trailing-only debounce. It does not include leading behavior or maxWait; a library utility is easier to use when those options or cancellation are needed.

~~~javascript
function debounceTrailing(fn, wait) {
  let timer;

  function debounced(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  }

  debounced.cancel = () => clearTimeout(timer);
  return debounced;
}
~~~

Use debounce when only the settled value matters, such as a search query. Use throttle when periodic updates matter, such as pointer position during scrolling. If a component removes the listener, also cancel any pending trailing call.

## How do you improve first-screen rendering? / 如何改善首屏呈现？

Start with the actual LCP element and critical path. Make that resource discoverable promptly, avoid lazy-loading the LCP image, and reserve dimensions for images or embeds to prevent layout shifts. Defer below-the-fold images and non-critical code when the measurement shows they compete with critical work. SSR or static output can help in some routes, but does not by itself guarantee a good LCP or INP.

## How can an analytics SDK limit work during navigation? / 如何降低分析SDK对页面的影响？

Batch events in a bounded in-memory queue, flush a small batch at a threshold or on a timer, and try a final flush when the document becomes hidden. The limits below are example configuration, not recommended universal thresholds.

~~~javascript
const MAX_PENDING = 200;
const BATCH_SIZE = 50;
const queue = [];
let flushScheduled = false;

function report(url, events) {
  const body = new Blob([JSON.stringify(events)], { type: "application/json" });
  if (navigator.sendBeacon && navigator.sendBeacon(url, body)) return;
  void fetch(url, { method: "POST", body, keepalive: true }).catch(() => {});
}

function trackEvent(event) {
  if (queue.length === MAX_PENDING) queue.shift(); // Drop the oldest item to stay bounded.
  queue.push({ event, ts: Date.now() });
  if (queue.length >= BATCH_SIZE) scheduleFlush();
}

function scheduleFlush() {
  if (flushScheduled) return;
  flushScheduled = true;
  setTimeout(() => {
    flushScheduled = false;
    flushEvents();
    if (queue.length >= BATCH_SIZE) scheduleFlush();
  }, 0);
}

function flushEvents() {
  if (queue.length === 0) return;
  const batch = queue.splice(0, BATCH_SIZE);
  report("/analytics", batch); // Best effort; report does not mean server acknowledgement.
}

setInterval(flushEvents, 10_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushEvents();
});
~~~

The report helper above uses sendBeacon when the browser accepts the payload for queuing, then falls back to fetch with keepalive when Beacon is unavailable or declines it. Neither path guarantees server receipt. A bounded queue also needs an explicit overflow policy; this example drops the oldest pending event. Avoid blocking navigation or making application correctness depend on analytics delivery.

**See also:** [Image Lazy Loading / 图片懒加载](../browser-apis/image-lazy-loading.md) for image loading choices; [Rendering and Computation Optimization / 渲染与计算优化](./rendering-and-computation-optimization.md) for React and long-list work.

**Sources checked 2026-10-15:** [PerformancePaintTiming (FP/FCP)](https://developer.mozilla.org/en-US/docs/Web/API/PerformancePaintTiming), [DOMContentLoaded event](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event), [Window load event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event), [Web Vitals](https://web.dev/articles/vitals), [INP](https://web.dev/articles/inp), [LCP](https://web.dev/articles/lcp), [CLS](https://web.dev/articles/cls), [Lab and Field Data Differences](https://web.dev/articles/lab-and-field-data-differences), [HTTP Caching (RFC 9111)](https://www.rfc-editor.org/rfc/rfc9111.html), [ETag (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html#name-etag), [Beacon specification](https://w3c.github.io/beacon/).
