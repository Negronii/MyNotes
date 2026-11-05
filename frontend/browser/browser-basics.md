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

The network lane is conditional. A service worker or HTTP cache can satisfy a request; a redirect can change the target; DNS and connection setup are needed only when the chosen fetch path lacks a usable result or reusable connection. Resource hints request early work, but do not guarantee it. See [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) for DNS, HTTP versions, caching, CORS, and resource hints.

The document lane is incremental, not a queue of stages that each finish once. The parser can discover stylesheets, scripts, images, and other resources before reaching the end of the response. A parser-inserted classic script may pause parsing; `async`, `defer`, and module scripts have distinct schedules. See [How do scripts affect HTML parsing and readiness?](../html-css/browser-html-and-css.md).

Layout produces geometry; paint produces drawing output, not a bitmap. Rasterization makes pixel content from drawing records, and compositing arranges content into a frame. Engines may reuse existing work, run parts in parallel, or use different stage names. Chromium's RenderingNG documentation is one implementation example, not a requirement for WebKit, Gecko, or the web platform. See [Why can a CSS change trigger layout, paint, or compositing work?](../html-css/rendering-pipeline-and-forced-layout.md).

A URL change is not always a new document. Same-document fragment navigation and History API updates have their own behavior; see [Does every URL change load a new document?](./browser-navigation-and-history.md). To investigate a slow or unstable page, use measurements and traces rather than assuming a stage name identifies the cause; see [How should browser performance be measured and diagnosed?](../performance/performance-metrics-and-analysis.md).

**Evidence / 资料：** [WHATWG HTML: navigation and session history](https://html.spec.whatwg.org/multipage/nav-history-apis.html); [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/); [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), checked 2026-11-05.
