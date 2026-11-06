# How does a browser turn a URL into pixels? / 浏览器如何把 URL 变成屏幕像素？

A URL entry is first interpreted as an input or navigation request; only a cross-document navigation switches documents, and only some paths need a network fetch. For a document navigation, fetching and parsing can overlap, discovered resources can load in parallel, and scripts can pause selected parsing work. The browser computes styles and geometry, produces paint output, rasterizes content, composites a frame, and hands it to the platform for display. Rendering engines such as Blink, WebKit, and Gecko and JavaScript engines such as V8, JavaScriptCore, and SpiderMonkey occupy different implementation boundaries. The broad path is useful for diagnosis, but its exact stages and process architecture are implementation details. / 输入 URL 后，浏览器先判断它是搜索还是导航；只有跨文档导航才需要新文档，也只有部分路径需要网络。文档导航中的获取与解析可以交叠，解析会发现并行加载的资源，脚本可暂停特定解析工作。浏览器随后计算样式与几何、生成绘制输出、栅格化内容、合成画面并交给平台显示。这个概览适合定位问题，但具体阶段和进程架构属于实现。

~~~mermaid
flowchart TD
    A[Address input] --> B{Search or URL?}
    B -->|search terms| S[Search provider]
    B -->|URL| C{Same document or new document?}
    C -->|fragment or History API update| H[Update URL and session history]
    C -->|cross-document navigation| F["Fetch path: service worker, cache, or network"]
    F --> P[Stream and parse HTML]
    P --> R[Discover and fetch subresources]
    P --> J{Parser-blocking script?}
    J -->|yes| W[Wait for required fetch/style conditions and run script]
    W --> P
    J -->|no| D[Build document and style data incrementally]
    R --> D
    D --> L[Compute style and layout as needed]
    L --> O[Paint output / drawing records]
    O --> T["Rasterize paint output into pixels (engine-specific)"]
    T --> K["Composite and submit frame (engine-specific)"]
    K --> X[Platform displays at a suitable presentation time]
    H --> U[Same document UI may update]
    U --> L
~~~

## Resolve a navigation before fetching / 先决定导航，再获取文档

Follow `https://example.test/reports?sort=recent#summary` from the address bar. Once the browser treats the input as a URL, the scheme and authority identify the origin and connection requirements. The path and query select the requested resource. The fragment identifies a location in the resulting document and stays on the browser side. An application can also change a URL with the History API without replacing its current document. Back/Forward can restore an existing document from a history entry, including the back/forward cache when eligible. That cache preserves document state, while an HTTP cache reuses an eligible response.

For this example, assume it is a fresh document navigation. A service worker controlling the target scope may respond. Otherwise the fetch path can use a fresh cached response, revalidate a stored response, or obtain a new response. For a new connection, resolve the host when no suitable address is available, then establish the transport and secure session. A typical HTTP/2 path uses TCP and TLS, while HTTP/3 uses QUIC. A reused connection skips new setup. If the fetch goes to the network, the origin receives `/reports?sort=recent` without `#summary`, and may redirect. The browser handles the fragment locally when the target element is available. [HTTP, DNS, and connection setup](../../engineering-foundations/networking/http-protocols-and-websockets.md) explains the network choices. [Navigation and history](./browser-navigation-and-history.md) explains same-document updates.

## Parse and render while resources arrive / 资源到达时就开始解析与渲染

Assume the response starts with this document:

~~~html
<!doctype html>
<link rel="stylesheet" href="/reports.css">
<script type="module" src="/reports.js"></script>
<main>
  <h1 id="summary">Recent reports</h1>
  <img src="/report-summary.png" width="320" height="180" alt="Report summary">
</main>
~~~

HTML bytes can be decoded and parsed before the full response arrives. The parser creates DOM nodes as markup becomes available. Discovering the stylesheet, module, and image starts separate resource work. Browsers can discover some resources speculatively. An applicable stylesheet can delay rendering, and a parser-inserted classic script without `async` or `defer` can pause parsing. The module shown here is fetched as parsing proceeds and is deferred by default. The image can arrive later. Its dimensions give layout an initial size or aspect ratio before the pixel data is ready. [Script scheduling and document readiness](../html-css/browser-html-and-css.md) explains which scripts can change the order and when readiness events fire.

The browser combines the DOM and applicable styles to compute used geometry. The heading takes space according to its computed font and available width, then layout positions the image box. Paint records how to draw the result, including text, borders, backgrounds, and images. Rasterization produces pixel content from those records and decoded resources. Compositing positions and combines the content for a frame, which is submitted for display. Chromium's RenderingNG uses paint records, raster tiles, compositor frames, and a display compositor. The boundaries of work, threads, and GPU participation depend on the engine. [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)

The first visible frame can precede `load` and, in a server-rendered app, client interactivity. The app may still need to download JavaScript and attach its behavior. An image or font that arrives later can change paint or geometry and produce another frame. [React and Next.js hydration](../frameworks/next-js.md) connects this path to application code. For an interaction after the initial frame, follow [when the event handler can run](../runtime/event-loop.md) and [what rendering work its update can trigger](../html-css/rendering-pipeline-and-forced-layout.md).

## Find the stage that is slow / 定位真正慢的环节

| What you observe | What to inspect next |
| --- | --- |
| Long before the first HTML byte | Redirects, cache status, connection timing, and backend latency in the network trace |
| HTML arrives early but useful content is late | Discovery of the critical resource, blocking CSS or JavaScript, then paint and image decoding |
| Content appears but the first interaction is slow | Main-thread tasks, script execution or hydration, and the next presentation |
| The layout jumps after content appears | Late image or font geometry, inserted content, and the nodes shown in the layout-shift trace |

Follow the measured event to its dependency. A slow largest-content paint can come from a late request, a slow response, or delayed rendering after the bytes arrived. Changing a CSS selector alone would miss two of those causes. [Chrome DevTools Performance reference](https://developer.chrome.com/docs/devtools/performance/reference) · [Web performance diagnosis](../performance/performance-metrics-and-analysis.md)

**Evidence / 资料：** [WHATWG HTML: navigation and session history](https://html.spec.whatwg.org/multipage/nav-history-apis.html); [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/); [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), checked 2026-11-05.

## Check your understanding / 闭卷自测

- **Retell / 复述。** Starting with the address bar, trace how `Recent reports` first appears. Which work can overlap, and why can the heading appear before the image finishes loading? / 从地址栏按回车开始，讲到 `Recent reports` 标题首次可见。哪些工作能交叠？为什么图片尚未加载完，标题已经能出现？
- **Change one condition / 变式。** Suppose the page has a filter initialized by `/reports.js`. The heading is already visible, but the first click gives no prompt feedback. What would you look for in the Network panel and in a Performance recording to distinguish a handler that has yet to be attached from a main thread occupied by a long task? / 假设页面的筛选功能由 `/reports.js` 初始化。标题已经可见，第一次点击却迟迟没有反馈。你会在网络记录和性能录制里找哪些证据，区分事件处理器还没注册和主线程正被长任务占用？
