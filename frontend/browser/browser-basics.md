# 浏览器如何把 URL 变成第一帧？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，需要看到最近报表；随后点击“最早优先”，期望列表更新。先沿初次导航走到可见页面，再从同一页跟进点击。

~~~mermaid
flowchart TD
    A[地址栏输入报表 URL] --> B[首次访问：跨文档导航]
    B --> C[浏览器取得响应并创建新 Document（文档对象）]
    C --> D[HTML 字节逐步到达，HTML parser（解析器）边解析边建立 DOM（Document Object Model，文档对象模型）]
    D --> P[继续接收和解析后续 HTML]
    D --> CSS[发现并获取 reports.css]
    D --> JS[发现并获取 reports.js 模块图]
    D --> IMG[发现并获取报表图片]
    P --> STYLE[已有内容且当前渲染所需样式可用]
    CSS -->|当前渲染所需的阻塞样式表就绪| STYLE
    STYLE --> FRAME[渲染机会：计算样式、布局并生成绘制结果]
    FRAME --> PRESENT[浏览器引擎栅格化、合成并显示画面]
    P --> MODULE[HTML 解析结束]
    JS --> GRAPH[模块图获取完成]
    MODULE --> GATE[普通模块执行条件检查]
    GRAPH --> GATE
    CSS -->|当前无阻塞脚本的样式表| GATE
    GATE --> RUN[普通模块开始求值]
    RUN --> HANDLER[reports.js 注册筛选处理器]
    IMG --> LATER[图片到达后填入预留区域]
    PRESENT --> VISIBLE[标题、筛选按钮和预渲染行可见]
    HANDLER --> ACTIVE[筛选按钮已可交互]
    VISIBLE --> ACTIVE
    ACTIVE --> CLICK[点击“最早优先”]
    CLICK --> UPDATE[处理器更新 URL、aria-pressed 和行顺序]
    UPDATE --> NEXT[浏览器在后续渲染机会显示新顺序]
~~~

图中 CSS、模块脚本、图片获取与后续 HTML 解析分别推进；不必等所有资源都到齐才有首帧。模块图获取完成只表示依赖资源已就绪；普通模块还要等 HTML 解析结束，并满足脚本阻塞样式表状态，才开始求值。图片若晚到，可以填入预留空间而不必挪动已有内容。图是帮助跟踪这条报表路线的模型，不是每个引擎都必须遵循的逐步流水线。浏览器负责导航、资源协调与画面呈现，JavaScript engine（JavaScript 引擎，如 V8、JavaScriptCore 或 SpiderMonkey）负责执行脚本；各自的进程和线程边界属于实现选择。

## 先确定浏览器要打开什么

地址栏文本先被判定为搜索词还是 URL；这里已给出 URL，因此例子从跨文档导航开始。路径 `/reports` 和查询 `sort=recent` 会参与请求；片段 `#summary` 留在浏览器端，不会随 HTTP 请求发给服务器。匹配范围的 Service Worker（服务工作线程）或可用缓存可能直接提供响应；若走网络，缓存也可能需要验证。对本例的 HTTPS URL，协议、主机和端口共同确定 origin（源）；有匹配的活动连接时浏览器可以复用，需要新建连接且没有可用主机地址时才查询 Domain Name System（域名系统，DNS）。Transport Layer Security（传输层安全协议，TLS）可保护传输；HTTP/2 常运行在 TCP/TLS 上，HTTP/3 使用 QUIC。浏览器随后发送带 `/reports?sort=recent` 的请求并收到响应头和响应体，再将响应体按到达情况交给新 `Document` 的 HTML parser。协议协商、重定向、缓存与连接复用等细节见[HTTP、DNS 与连接建立](../../engineering-foundations/networking/http-protocols-and-websockets.md)。

`#summary` 指向当前文档里的位置。后续应用也能用 History API 改变当前 URL，而不获取该 URL 对应的新文档。浏览器后退时，浏览器可能直接恢复符合条件的既有页面状态（back/forward cache，前进/后退缓存）；这与从 HTTP 缓存重新使用响应不是一回事。见[每次 URL 变化都会加载新文档吗？](./browser-navigation-and-history.md)和[HTTP、DNS 与连接建立](../../engineering-foundations/networking/http-protocols-and-websockets.md)。

## 响应到达时，解析和资源获取可以交叠

假设 `/reports` 返回如下 HTML。服务端已经把报表标题和初始行放进响应，浏览器可在客户端代码完成之前显示它们。

~~~html
<!doctype html>
<link rel="stylesheet" href="/reports.css">
<script type="module" src="/reports.js"></script>
<main>
  <h1 id="summary">Recent reports</h1>
  <img src="/report-summary.png" width="320" height="180" alt="Report summary">
  <div id="sort-controls">
    <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
    <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
  </div>
  <ol id="reports"><li data-id="may">May report</li><li data-id="april">April report</li></ol>
</main>
~~~

浏览器不必等完整响应下载完才开始解析；随着标记到达，HTML parser 建立 DOM，并发现样式表、模块脚本和图片等资源。浏览器通常能并行获取独立资源，也可能用实现特有的预扫描提前发现资源。适用于当前媒体环境的外部样式表可能阻止首次显示；没有 `async` 或 `defer` 的解析器插入经典脚本会阻塞 HTML 解析。这里的普通模块脚本会并行获取，等解析完成、模块依赖图就绪且阻塞脚本的样式表条件满足后运行。具体脚本依赖关系见[脚本如何影响 HTML 解析与文档就绪？](../html-css/browser-html-and-css.md)。

DOM 表示文档节点，CSS 规则决定这些节点如何呈现。浏览器按需计算样式和布局：例如标题文字的换行取决于字体和可用宽度，图片的宽高属性则让图片数据到达前也能先分配画面空间。后到的字体仍可能改变文字宽度或换行。渲染引擎（如 Blink、WebKit、Gecko）据此准备绘制结果，再把内容转换为像素并组合成待显示画面；JavaScript 引擎（如 V8、JavaScriptCore、SpiderMonkey）负责执行脚本。Blink/Chromium 的 RenderingNG 是一种实现实例，不是所有浏览器的强制结构。

## 从首帧交接到筛选更新

首帧可能先于 `load` 事件和客户端代码可交互的时点出现。比如 HTML 已显示报表，但模块脚本尚未完成下载、运行或注册点击处理器。若报表由 React 服务端输出，hydration（客户端水合）还要在已有 DOM 上运行客户端代码并接入组件行为，见[Next.js 中的 hydration 与流式渲染](../frameworks/next-js.md#How%20do%20hydration%20and%20streaming%20fit%20together%3F%20/%20Hydration%20%E4%B8%8E%E6%B5%81%E5%BC%8F%E6%B8%B2%E6%9F%93%E5%A6%82%E4%BD%95%E8%A1%94%E6%8E%A5%EF%BC%9F)。若点击没有反馈，先确认处理器何时可用；若处理器已经注册，则查看事件是否被主线程上其他工作挡住。

当用户点击“最早优先”，`/reports.js` 的 DOM 事件处理器可以把 `sort=oldest` 写入 URL，设置按钮的 `aria-pressed` 状态，并改动列表节点。节点修改立即改变 DOM；样式、布局、绘制和之后的画面呈现则由浏览器在后续工作中按需完成。异步处理器与画面更新之间的关系见[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)，点击如何到达处理器见[DOM 事件如何传播，何时适合事件委托？](../browser-apis/dom-manipulation-and-events.md)，更新后可能需要的布局和绘制见[为什么一次 DOM 改动会增加布局或绘制工作？](../html-css/rendering-pipeline-and-forced-layout.md)。

| 现象 | 优先检查的阶段 |
|---|---|
| 首个 HTML 字节迟迟不到 | 重定向、缓存命中、连接建立、服务端响应和网络瀑布 |
| HTML 已到，主要内容仍迟 | 关键 CSS/脚本的阻塞关系、LCP 资源发现与渲染时机 |
| 页面可见，筛选点击迟迟没有反馈 | 点击前主线程工作、处理器运行时间、处理后的渲染工作 |
| 内容出现后位置跳动 | 图片或字体的尺寸和到达时机、后插入内容及布局偏移记录 |

先沿测得的依赖关系定位，再决定要改请求、脚本、布局还是绘制。相同的“首屏慢”现象可能来自服务器响应、资源发现或内容渲染，单独改 CSS 选择器无法同时解释这些原因。见[如何测量并诊断网页性能问题？](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - URL 片段及导航后文档状态： [WHATWG HTML：导航与会话历史](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，持续更新规范，导航、同文档导航与历史遍历章节；[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，请求 URL 处理章节。核对日期：2026-11-06。
> - HTTPS origin、DNS 与本例网络协议： [WHATWG URL Standard：Origin](https://url.spec.whatwg.org/#origin)；[RFC 1034：DNS concepts and facilities](https://www.rfc-editor.org/rfc/rfc1034)、[RFC 1035：DNS implementation and specification](https://www.rfc-editor.org/rfc/rfc1035)；[RFC 8446：TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)；[RFC 9113：HTTP/2](https://www.rfc-editor.org/rfc/rfc9113)、[RFC 9000：QUIC](https://www.rfc-editor.org/rfc/rfc9000) 与 [RFC 9114：HTTP/3](https://www.rfc-editor.org/rfc/rfc9114)。核对日期：2026-11-06。
> - HTML 解析和浏览器渲染在 Chromium 中的一种实现： [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)，架构概览。核对日期：2026-11-06。
> - 浏览器渲染引擎名称： [Blink](https://www.chromium.org/blink/)，Chromium rendering engine；[WebKit](https://webkit.org/)，WebKit browser engine；[Gecko](https://firefox-source-docs.mozilla.org/overview/gecko.html)，Firefox rendering engine。JavaScript 引擎名称： [V8](https://v8.dev/)、[JavaScriptCore](https://docs.webkit.org/Deep%20Dive/JSC/JavaScriptCore.html)、[SpiderMonkey](https://firefox-source-docs.mozilla.org/js/)。核对日期：2026-11-06。
