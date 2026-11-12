# Frontend

> Generated from the [frontend reading map](../../frontend/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. 浏览器如何把 URL 变成第一帧？

案例背景：用户打开 Uniform Resource Locator (URL，统一资源定位符)`https://example.test/reports?sort=recent#summary`，需要看到最近报表；随后点击“最早优先”，期望列表更新。先沿初次导航走到可见页面，再从同一页跟进点击。

~~~mermaid
flowchart TD
    A[输入报表 URL] --> B[导航取得 HTML 响应]
    B --> C[逐步解析 HTML<br/>建立 DOM 并发现资源]
    C --> D[已有可显示内容<br/>当前渲染所需 CSS 就绪]
    C --> E[HTML 解析结束、模块图就绪<br/>样式不再阻塞脚本]
    D --> F[渲染机会：样式、布局、绘制<br/>栅格化与合成后显示首帧]
    E --> G[reports.js 模块求值<br/>注册筛选处理器]
    F --> H[画面可见且处理器已就绪]
    G --> H
    H --> I[点击最早优先<br/>更新 URL、选中态与行顺序]
    I --> J[后续渲染机会显示新顺序]
~~~

这张图跟踪两种不同的就绪条件：浏览器已有足够的超文本标记语言（HyperText Markup Language，HTML）和当前可显示内容所需的层叠样式表（Cascading Style Sheets，CSS）规则，可以先给出一帧；`/reports.js` 的模块依赖下载完成、HTML 解析结束且阻塞它的样式表处理完后，才注册点击处理器。两条线可以交叠推进：HTML 流还在解析时，浏览器就能获取 CSS、模块及图片；图片也可在 Document Object Model (DOM，文档对象模型) 构建和布局工作继续时下载、解码。图表示这条报表路线上的依赖，不表示所有浏览器必有同一组线程或逐步流水线。下文的成功点击假设发生在两个条件汇合之后；若用户在静态首帧出现、监听器尚未注册时就点按钮，这份 HTML 没有原生提交或其他后备动作，因此不会排序。模块或依赖获取失败、注册前脚本报错，也可能留下可见却不能筛选的页面。

### 先确定浏览器要打开什么

地址栏文本先被判定为搜索词还是 URL；这里已给出 URL，因此例子从跨文档导航开始。浏览器拆分 URL：`https`、主机和端口共同确定 origin（源）；`/reports` 与 `?sort=recent` 是请求所针对的资源，`#summary` 是文档内的位置标识，不会发给服务器。`sort=recent` 因而可以影响服务端返回的初始行序，片段则在文档中定位到 `id="summary"` 的标题。

若活动且匹配的 Service Worker（服务工作线程）正在控制此导航，它的 fetch 事件处理器（fetch handler）可以返回合成响应，也可以自己继续取网络资源；这可以让页面不必重新向源站取 HTML。Hypertext Transfer Protocol (HTTP，超文本传输协议) 响应缓存若有新鲜且匹配的响应，可以直接复用；若响应需要验证，浏览器会带条件请求确认它是否仍有效。需要走网络时，浏览器可以复用一条适用于这次请求的活动连接；若需新建连接，且系统没有可用的主机地址记录，才需要查询 Domain Name System (DNS，域名系统)。对本例的新 HTTPS 连接，浏览器按 Transport Layer Security (TLS，传输层安全协议) 验证服务端证书并保护传输，然后发送请求。若中间响应要求重定向，浏览器按 `Location` 继续导航；如果目标改变了主机或协议，后续连接条件也可能改变。实际发送的请求路径和返回的资源最终由这条导航链决定。

取得最终 HTML 响应后，浏览器不必等整个响应体下载完才开始工作。HTML 字节可以持续交给 parser（解析器）；解析器按到达的内容逐步建出新 `Document` 的 DOM，并发现外部样式表、模块和图片。完整 HTTP、DNS 与连接建立过程见[HTTP、DNS 与连接建立](../../engineering-foundations/networking/http-protocols-and-websockets.md)。

`#summary` 指向当前文档里的位置。后续应用也能用 History API 改变当前 URL，而不获取该 URL 对应的新文档。浏览器后退时，浏览器可能直接恢复符合条件的既有页面状态（back/forward cache，前进/后退缓存）；这与从 HTTP 缓存重新使用响应不是一回事。见[每次 URL 变化都会加载新文档吗？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)和[HTTP、DNS 与连接建立](../../engineering-foundations/networking/http-protocols-and-websockets.md)。

### 响应到达时，解析和资源获取可以交叠

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

浏览器可随着响应体到达开始解析，不必等完整文件。HTML parser 建立 DOM，并发现样式表、模块脚本和图片；这些独立资源可以在解析继续时并行获取，一些浏览器还会用预扫描提前发现资源。适用于当前环境的外部样式表可能阻止首次渲染。这里的普通模块脚本及其依赖在解析期间下载，但模块不会像未标记的经典同步脚本那样卡住 parser；模块要等 HTML 解析结束、依赖就绪，并且阻塞脚本的样式表不再等待，才开始求值。模块图下载就绪与处理器注册是不同的时点。JavaScript 引擎执行 `/reports.js`；渲染引擎负责把 DOM/CSS 转成可显示内容，浏览器将二者接在同一页面生命周期里。Chromium 常见组合是 V8 与 Blink，Firefox 使用 SpiderMonkey 与 Gecko，Safari 使用 JavaScriptCore 与 WebKit；这些名称说明不同组件的职责，不规定它们必须用同一进程或线程安排。具体脚本依赖关系见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)。

**这段 HTML 中 `<main>` 的 DOM 子树**

![报表示例中的 DOM 父子节点；main 的四个直接子元素各自连接到自己的后代](../../frontend/browser/resources/browser-basics-dom-tree.svg)

#### DOM 与 CSS 怎样变成布局用的几何？

`/reports.css` 到达后，CSS parser（CSS 解析器）会将文本解析成样式表及规则；对网页脚本可见的 CSS Object Model (CSSOM，CSS 对象模型) 用 `CSSStyleSheet`、`CSSRule` 等对象表示这些内容。CSS 规则仍不是 DOM 节点；渲染时浏览器让选择器匹配 DOM，再按级联与继承挑出适用声明。引擎内部用于匹配规则的数据结构可以各自不同。

DOM 记录节点和文本如何嵌套；CSS 规则描述这些节点怎样呈现。浏览器将两者结合，按级联和继承为元素解析 computed style（计算样式），例如标题的字号、行高和颜色。计算样式不等于最终几何：像 `width: auto` 这样的值还要结合可用空间、字体度量和相邻内容，布局算法才能算出 used value（使用值）和位置。

CSS 的 `display` 等规则会从 DOM 生成用于布局的盒结构，但二者不是一对一：`display: none` 的元素不生成盒；一个文本节点若换行，可能对应多个空间片段。布局继续根据父容器约束和前面内容的尺寸，确定每个盒或片段的宽高、坐标与顺序。Blink 将其中一种布局结果组织为 fragment tree（片段树）；Gecko 使用 frame tree（帧树），而且一个节点可能对应多个 frame。共同要点是这些中间结构携带布局结果，不是 DOM 原样的复制品。

**从节点与规则到布局片段**

![DOM 节点和 CSS 规则经过匹配、计算样式、盒生成和布局约束，形成片段结构](../../frontend/browser/resources/browser-basics-rules-to-layout.svg)

案例没有提供 `/reports.css`，所以接下来的 CSS 只定义一份可复算的局部教学布局，不代表真实站点样式。为消除浏览器默认样式对坐标的影响，这份规则显式清掉 `h1` 的上外边距、图片的 inline baseline 行盒间隙、按钮默认内边距和列表缩进；全局使用 `border-box`，按钮声明的宽高因此包含边框。

```css
*, *::before, *::after { box-sizing: border-box; }
html, body { display: block; margin: 0; padding: 0; }
body { font: 16px Arial, sans-serif; }
main { display: block; width: 100%; padding: 24px; }
h1 { display: block; margin: 0 0 12px; font-size: 24px; line-height: 30px; font-weight: 700; }
img { display: block; width: 320px; height: 180px; margin: 0 0 12px; }
#sort-controls { display: flex; gap: 8px; margin: 0 0 12px; }
button { display: inline-flex; width: 128px; height: 36px; margin: 0; padding: 0; border: 1px solid; font: inherit; }
button svg { display: block; width: 16px; height: 16px; flex: none; }
#reports { display: block; margin: 0; padding: 0; list-style: none; }
#reports li { display: block; height: 34px; margin: 0; padding: 0; line-height: 34px; }
```

在本机 headless Chrome `157.0.8103.50` 中，把上方 `<main>` 子树放入测量页并应用这段 CSS；图片用本地 `data:` 占位替代外部文件，只核对布局几何，不访问站点。测得 `innerWidth=720 CSS px`、`innerHeight=433 CSS px`、`devicePixelRatio=1`。关键 `getBoundingClientRect()` 结果如下；坐标以视口左上为原点，单位均为 CSS px。

| 元素 | x, y | width × height | 推出的边缘 |
|---|---:|---:|---:|
| `main` | `0, 0` | `720 × 398` | 内容盒起点 `(24, 24)`，宽 `672` |
| `h1#summary` | `24, 24` | `672 × 30` | 下边 `54` |
| `img` | `24, 66` | `320 × 180` | 下边 `246` |
| `#sort-controls` | `24, 258` | `672 × 36` | 下边 `294`；按钮实际覆盖 `x=24…152`、`160…288` |
| `ol#reports` | `24, 306` | `672 × 68` | 下边 `374` |
| May 行 / April 行 | `24, 306` / `24, 340` | each `672 × 34` | 行边界 `306–340`、`340–374` |

可复算的纵向链是 `24 + 30 + 12 + 180 + 12 + 36 + 12 = 306`：标题、图片、按钮组是向下排列的块；只有两个按钮在 flex 行内横排。图片设为块级后，`img` 的盒直接高 `180px`，不会再受 inline 基线间隙影响；`ol` 的上下 margin 与 padding 均为零，第一行从实测的 `y=306` 开始。指定图片尺寸后，即使实际图片字节尚未解码，布局也可先按 `320×180px` 留位；晚到的字体则可能改变文字宽度并让后续内容重排。

**同一页面的实测盒位置**

![720 CSS 像素视口中报表标题、图片、按钮行与两条列表项的纵向位置](../../frontend/browser/resources/browser-basics-layout-geometry.svg)

#### 布局结果怎样变成可以显示的像素？

布局给出了盒子与文字片段的几何，却没有画出字形或按钮背景。绘制阶段按 CSS 绘制顺序把这些几何、颜色、图片等内容转成有顺序的绘制项；一个元素可能产生多个绘制项，例如背景和文字是不同的项。图片若尚未下载或解码，它的框可以已经参与布局，但对应图像内容要等资源可用。

下面按 Chromium 的 RenderingNG 公开实现串起中间表示。Pre-paint 计算 transform、clip、effect、scroll 属性树，并标记失效的显示项或 GPU 图块。Paint 消费这份属性状态，按绘制顺序生成 display items（显示项），再把共享同一属性状态的显示项分组为 paint chunks（绘制块）。Commit 把显示列表和属性树交给合成器；layerize 再按可独立合成的视觉关系，把绘制块组织成一层或多层。接着可见空间被分成相邻 tile 区域；栅格任务为某个矩形 tile 处理覆盖到它的绘制项，互不依赖的区域可以并行栅格。同一个绘制项也可能跨过多个 tile，例如这张图的图片框横跨格子边界，各区域只需得到对应的像素部分。长页面可以复用已栅格的 tile，并在滚动时补画刚进入视口的空间范围。激活阶段产生描述 tile 摆放与视觉效果的 compositor frame（合成帧）。Viz 再把可见表面的合成帧汇总为全局合成帧，由 GPU 执行 Draw 绘出屏幕像素；下图只放大报表表面的空间关系。

**绘制块、连续 tile 区域与本页合成帧描述的画面**

![同一报表从已提交的绘制数据与图层进入相邻 tile 栅格区域，再由合成帧描述标题、图片、按钮和两条列表项](../../frontend/browser/resources/browser-basics-tiles-to-frame.svg)

图中的 `3×4` 网格只是说明空间划分的教学假设，单格为连续的 `240×100 CSS px` 矩形，最下排高 `98px`；不是对 Chromium 实际 tile 尺寸或 layer 数量的断言。为聚焦空间关系，图把可见内容投影到一个示意 layer surface；真实 layerize 可能把绘制块组织成一层或多层。上图网格取实测 `main` 外框 `720×398 CSS px`，完整位于 `720×433 CSS px` 的视口内，余下 `35px` 是页面下方空白，所以十二格都在当前画面范围内。真实引擎会按 viewport、失效范围、图层属性和设备条件选择需要更新的 tile；同一绘制项可以贡献给它覆盖到的多个 tile，空间范围决定 tile 输入，而不是把一条显示列表任意拆成不相邻的片段。网格线与控制盒虚线只是定位参考，不是页面边框；合成帧描述的画面省略这些参考线，但保留同一个标题、图片、按钮和 May、April 两行。

这些阶段和中间结构是 Chromium 的实现例，不是网页标准规定的固定线程流水线。Firefox 的公开实现说明也从 DOM/CSS 得到布局 frame，再产生 WebRender 显示列表、场景和帧，具体表示与进程安排不同。某些变化（例如只需合成器处理的滚动或视觉动画）可以跳过重新布局和绘制；报表列表顺序变化则会改变 DOM 和内容位置，浏览器需要在后续渲染机会更新受影响的布局或绘制工作。HTML 解析、资源获取与图像解码可以交叠；同一流式内容里后面的块位置仍依赖前面内容的布局结果，因此不能把整页简化成互不相关的并行方框。

### 从首帧交接到筛选更新

首帧可能先于 `load` 事件和客户端代码可交互的时点出现。比如 HTML 已显示报表，但模块脚本尚未完成下载、运行或注册点击处理器。此刻初始 HTML 已有 `sort=recent` 对应的顺序：按钮 `aria-pressed` 为 `true/false`，列表是 May 在前、April 在后。若报表由 React 服务端输出，hydration（客户端水合）还要在已有 DOM 上运行客户端代码并接入组件行为，见[Next.js 中的 hydration 与流式渲染](#%E6%9C%8D%E5%8A%A1%E7%AB%AF%E4%B8%8E%E5%AE%A2%E6%88%B7%E7%AB%AF%E7%BB%84%E4%BB%B6%E5%9C%A8%E5%93%AA%E6%9D%A1%E7%BA%BF%E4%BA%A4%E6%8E%A5)。若点击没有反馈，先确认处理器何时可用；若处理器已经注册，则查看事件是否被主线程上其他工作挡住。

当用户点击“最早优先”，`/reports.js` 的处理器先用 History API（例如 `history.pushState`）把当前 URL 从 `https://example.test/reports?sort=recent#summary` 改为 `https://example.test/reports?sort=oldest#summary`。`pushState` 会新增一条同文档 history entry 并更新地址栏；它本身既不请求新 HTML，也不按查询参数替报表排序。随后仍由这个 click handler 分别把两个按钮的 `aria-pressed` 改为 `false/true`，并将列表节点顺序改成 April、May。DOM 改动立即生效；浏览器会在后续渲染机会按需重新计算样式、布局或绘制，再把新的像素送去合成。异步处理器与画面更新之间的关系见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)，点击如何到达处理器见[DOM 事件如何传播，何时适合事件委托？](#4.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E6%80%8E%E6%A0%B7%E6%9F%A5%E8%AF%A2%E3%80%81%E6%9B%B4%E6%96%B0%20DOM%20%E5%B9%B6%E5%93%8D%E5%BA%94%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9F)，更新后可能需要的布局和绘制见[为什么一次 DOM 改动会增加布局或绘制工作？](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

| 现象 | 优先检查的阶段 |
|---|---|
| 首个 HTML 字节迟迟不到 | 重定向、缓存命中、连接建立、服务端响应和网络瀑布 |
| HTML 已到，主要内容仍迟 | 关键 CSS/脚本的阻塞关系、Largest Contentful Paint（最大内容绘制，LCP）资源发现与渲染时机 |
| 页面可见，筛选点击没有反馈 | 首先确认 `/reports.js` 已求值且按钮处理器已注册；再查主线程阻塞、处理器运行时间和后续渲染工作 |
| 内容出现后位置跳动 | 图片或字体的尺寸和到达时机、后插入内容及布局偏移记录 |

先沿测得的依赖关系定位，再决定要改请求、脚本、布局还是绘制。相同的“首屏慢”现象可能来自服务器响应、资源发现或内容渲染，单独改 CSS 选择器无法同时解释这些原因。见[如何测量并诊断网页性能问题？](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - **URL、片段、History API 与导航请求。** [RFC 3986 §3.5 Fragment](https://www.rfc-editor.org/rfc/rfc3986.html#section-3.5) 说明片段用于标识主资源中的次级内容；[HTML Standard §7.2.5，History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface) 规定 `pushState` 添加 history entry 并更新其 URL，Living Standard，核对日期：2026-11-11；[WHATWG Fetch Standard，HTTP-network-or-cache fetch 与 URL 处理](https://fetch.spec.whatwg.org/#http-network-or-cache-fetch)，Living Standard，核对日期：2026-11-11；[WHATWG URL Standard，origin](https://url.spec.whatwg.org/#origin)，核对日期：2026-11-11。
> - **缓存、重定向、DNS 与 HTTPS。** [RFC 9111 §4.2 新鲜度](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.2) 与 [§4.3 验证](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.3) 支持新鲜缓存复用与验证；[RFC 9110 §15.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4) 定义重定向响应；[RFC 1034 §§3.1–3.2](https://www.rfc-editor.org/rfc/rfc1034.html#section-3.1) 与 [RFC 1035](https://www.rfc-editor.org/rfc/rfc1035.html) 描述域名解析；[RFC 9113 §9.1.1](https://www.rfc-editor.org/rfc/rfc9113.html#section-9.1.1) 说明 HTTP/2 的连接复用；[RFC 8446 §§2、4.4.2–4.4.3](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.3) 描述 TLS 1.3 握手、证书认证和安全属性。活动 Service Worker 的 fetch 处理见 [Service Workers Editor’s Draft（2026-10-29），Handle Fetch 算法](https://w3c.github.io/ServiceWorker/#handle-fetch)。核对日期：2026-11-11。
> - **HTML、资源与脚本时机。** [WHATWG HTML，Parsing HTML documents](https://html.spec.whatwg.org/multipage/parsing.html) 与 [Speculative HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html#speculative-html-parsing) 说明渐进解析及实现可采用的推测式资源发现；[Scripting，script processing model](https://html.spec.whatwg.org/multipage/scripting.html#script-processing-model) 规定模块及其依赖的获取和求值时机。Living Standard，核对日期：2026-11-11。
> - **从样式表到布局结构。** [CSS Syntax Level 3 §8.1，W3C Candidate Recommendation Draft（2026-10-01）](https://www.w3.org/TR/css-syntax-3/#style-rules) 说明样式表中的规则如何解析；[CSS Object Model §6.1、§6.4，W3C Working Draft（2021-08-26）](https://www.w3.org/TR/cssom-1/#css-rules) 定义 `CSSStyleSheet` 与规则对象；[CSS Cascading and Inheritance Level 5 §§4.4–4.5](https://www.w3.org/TR/css-cascade-5/#computed-values) 区分 computed value 与 used value；[CSS Display Level 3 §2.5](https://www.w3.org/TR/css-display-3/#box-generation) 说明元素与 CSS 盒并非一一对应及 `display:none` / `display:contents` 的盒生成边界。CSS Cascading and Inheritance Level 5 为 W3C Candidate Recommendation Snapshot（2022-01-13），CSS Display Level 3 为 W3C Candidate Recommendation Draft（2026-06-05）；核对日期：2026-11-11。
> - **脚本引擎与渲染引擎的例子。** [V8](https://v8.dev/)，[JavaScriptCore](https://docs.webkit.org/Deep%20Dive/JSC/JavaScriptCore.html)，[SpiderMonkey](https://firefox-source-docs.mozilla.org/js/) 描述 JavaScript 实现；[Blink](https://www.chromium.org/blink/)，[WebKit](https://webkit.org/)，[Gecko](https://firefox-source-docs.mozilla.org/overview/gecko.html) 描述渲染引擎。核对日期：2026-11-11。
> - **从布局、绘制块到 tile 合成的实现例子。** [Chromium RenderingNG architecture，Rendering pipeline structure，stages 2–12（style 至 draw；尤其 pre-paint、paint、commit、layerize、raster、activate、aggregate）](https://developer.chrome.com/docs/chromium/renderingng-architecture#rendering-pipeline-structure)；[Chromium RenderingNG data structures，The immutable fragment tree、Property trees、Display lists and paint chunks、Compositor frames: surfaces, render surfaces and GPU texture tiles §§Tiles、Quads and surfaces](https://developer.chrome.com/docs/chromium/renderingng-data-structures)；[Firefox Rendering Overview，Frame Tree、Display List 与 WebRender](https://firefox-source-docs.mozilla.org/gfx/RenderingOverview.html) 和 [Gecko Layout Overview，frame tree 与片段](https://firefox-source-docs.mozilla.org/layout/LayoutOverview.html)。这些是公开引擎实现说明，不是统一浏览器线程规范；核对日期：2026-11-11。
>
> 查看[前端专题索引](../../frontend/index.md)中相关章节。
## 2. 每次 URL 变化都会加载新文档吗？

案例背景：用户先打开 `https://example.test/reports?sort=recent#summary`，随后点“最早优先”并可能按浏览器后退。要让这三个时点显示正确的报表，先判断浏览器是在换文档、跳转片段，还是只更新当前文档的历史地址。

### URL 分量怎样对应到浏览器导航？

以本例地址为例，`https:` 是 scheme (方案)，`example.test` 是 host (主机)，`/reports` 是 path (路径)，`?sort=recent` 是 query (查询)，`#summary` 是 fragment (片段)。本例 HTTPS 地址的 origin (源) 由 scheme、host 和 port 标识。不是所有 URL 都有 `//authority`：`mailto:reports@example.test` 就没有 HTTP(S) 式主机与路径结构。

`location.href` 读取完整 URL，赋值会导航；`protocol` 带结尾冒号，`host` 包含非默认端口，`hostname` 不含端口，`port` 是非默认端口或空字符串，`pathname` 是路径，`search` 保留开头的 `?`，`hash` 保留开头的 `#`。用 `URL` 和 `URLSearchParams` 解析，不要手动切分字符串；查询参数缺失时 `get()` 返回 `null`，已存在的值是字符串，例如 `"2026"` 不是数字。`getAll()` 可读同名多值，`set()` 替换同名值，`append()` 则追加一项；序列化时按 URL 查询参数规则编码。

浏览器历史栈可以包含不同 origin（源）的文档，因此 `history.back()`、`forward()` 和 `go()` 可能遍历到跨源页面。`history.go(n)` 按偏移量移动历史项：正数向前、负数向后、零会重新载入当前页；超出范围则不动作。History API 对 `pushState()` / `replaceState()` 新 URL 的同源要求，不等于浏览器只能在同源历史项之间后退。

### 用 URL 参数表达排序状态

本例只接受 `sort=recent` 和 `sort=oldest`；`sortFromUrl()` 将缺失或未知值按 `recent` 渲染，直到用户选择另一种排序才写入 URL。写回时从 `location.href` 解析现有地址，再更新 `sort`，所以路径、其他查询参数的值和 `#summary` 片段仍在；`URLSearchParams` 会重新序列化查询，空格可能从 `%20` 写成 `+`。查询参数来自地址栏或外部链接，必须按业务允许值校验，也不要把口令或访问令牌放进 URL。

| 操作 | 当前地址、文档与历史的结果 |
|---|---|
| 打开另一个地址：`<a>`、设置 `location.href`、调用 `location.assign()` | 通常加载另一个 `Document` 并留下新历史项；若目标含 fragment，且目标与当前 URL 除 fragment 外相同，则沿用当前 `Document` 并定位片段 |
| `location.replace(url)` | 替换当前历史项；是否沿用当前 `Document` 适用上一行的片段条件 |
| `location.reload()` | 重新加载当前文档，即使地址不变；不增加历史项，资源仍可能来自缓存 |
| `pushState(...)` | 保留当前 `Document` 并新增一项历史状态；调用本身不请求新文档 |
| `replaceState(...)` | 保留当前 `Document` 并修改当前历史项；调用本身不请求新文档 |

History API 的目标 URL 必须符合当前文档可改写 URL 的规则。对本例的 HTTPS 页面，可以改路径、查询和片段；scheme、username、password、host、port 要保持相同。`pushState()` 和 `replaceState()` 都不会发起该地址的网络请求，也不会因调用本身派发 `popstate` 或 `hashchange`。应用若要显示与新 URL 对应的内容，仍须自己同步界面；目标是别的服务器资源时，应正常导航或显式发出请求。

### 让排序状态跟随地址栏与前进后退

报表页面初始地址是 `/reports?sort=recent#summary`。浏览器用收到的 HTML 创建 `Document`，其中已有 `h1#summary`、两个排序按钮以及 May、April 两行；下面 HTML 示例中的普通模块脚本由 `<script type="module" src="/reports.js"></script>` 引用。本例把行数据放进客户端 `records` 数组，让 `renderReports()` 每次从 URL 状态重建行。若数据由服务器提供，更新 URL 后还需按该状态请求新结果，并处理加载、错误和过期响应。

~~~html
<!-- /reports?sort=recent 的服务端 HTML 初始状态 -->
<!-- 页面 head 中的客户端模块引用 -->
<script type="module" src="/reports.js"></script>
<h1 id="summary">Recent reports</h1>
<img src="/report-summary.png" width="320" height="180" alt="Report summary">
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false">
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M8 13V3m-4 4 4-4 4 4" fill="none" stroke="currentColor"
            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span>Oldest first</span>
  </button>
</div>
<ol id="reports">
  <li data-id="may">May report</li>
  <li data-id="april">April report</li>
</ol>
~~~

以下是 `/reports.js` 中的代码，不是 HTML 里的内联脚本：

~~~javascript
const records = [
  { id: "may", date: "2026-05-01", label: "May report" },
  { id: "april", date: "2026-04-01", label: "April report" },
];
const list = document.querySelector("#reports");
const controls = document.querySelector("#sort-controls");

function sortFromUrl() {
  return new URL(location.href).searchParams.get("sort") === "oldest"
    ? "oldest"
    : "recent";
}

function renderReports(sort) {
  const rows = [...records].sort((a, b) =>
    sort === "oldest" ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date)
  );
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.setAttribute("aria-pressed", String(button.dataset.sort === sort));
  }
  list.replaceChildren(...rows.map(({ id, label }) => {
    const item = document.createElement("li");
    item.dataset.id = id;
    item.textContent = label;
    return item;
  }));
}

function chooseSort(sort) {
  if (sort !== "recent" && sort !== "oldest") return;
  if (sort === sortFromUrl()) return;
  const url = new URL(location.href);
  url.searchParams.set("sort", sort);
  history.pushState(null, "", url.href);
  renderReports(sort);
}

controls.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-sort]");
  if (!button || !controls.contains(button)) return;
  chooseSort(button.dataset.sort);
});
window.addEventListener("popstate", () => renderReports(sortFromUrl()));
renderReports(sortFromUrl());
~~~

`renderReports()` 先按 URL 状态选顺序，再同步两个按钮的 `aria-pressed`，最后用 `replaceChildren()` 写入行。初始服务器 HTML 已显示 May → April；用户点“最早优先”后，新地址是 `/reports?sort=oldest#summary`，按钮切成 `false/true`，行变为 April → May。这里创建的是新 `li` 节点；DOM 章将同一结果与移动既有行节点的做法对照。若用户分享一条 `sort=oldest` 深链，`reports.js` 的初次运行会按 URL 修正列表；要让首批 HTML 本身就显示正确顺序，服务器也应按查询参数生成行和按钮状态。若地址是未知值，例如 `sort=other`，本例只按 `recent` 显示；点已经选中的 “Most recent” 会提前返回，只有选另一种排序才会改写地址。

委托监听器用 `event.target.closest("button[data-sort]")` 从点击目标向上找按钮，因此点按钮内的文字或 SVG 图标都会进入同一处理器；`controls.contains(button)` 再确认匹配到的按钮属于这组控件。

| 时点 | 历史项、文档与事件 | 地址与报表 UI |
|---|---|---|
| 初次打开 | 浏览器用收到的 HTML 创建一个 `Document`；模块初次运行读取 URL。 | `sort=recent`；按钮为 `true/false`，列表为 May → April。 |
| 点击 **Oldest first** | `pushState()` 新增同一 `Document` 的历史项；不请求新 HTML，也不派发 `popstate` / `hashchange`。点击处理器自己调用 `renderReports()`。 | 地址变为 `sort=oldest`；按钮为 `false/true`，列表为 April → May。 |
| 浏览器 Back | 激活先前的同文档历史项并派发 `popstate`；`#summary` 没变，本例不涉及 `hashchange`。 | 监听器读取当前 URL，恢复 `sort=recent`、`true/false` 与 May → April。 |
| 浏览器 Forward | 再激活 `sort=oldest` 历史项并派发 `popstate`。 | 监听器再次从 URL 得到 oldest，恢复 `false/true` 与 April → May。 |

本例用 `pushState(null, "", url.href)` 添加新历史项并记录 URL，不把排序状态另存进 `history.state`；点击处理器再主动调用 `renderReports()`。因此本例 `popstate` 的 `event.state` 为 `null`，排序仍从当前 URL 读取。`pushState()` 也可在第一个参数中保存应用状态，其他应用可在 `popstate` 的事件对象中读取。若用户再后退离开这个文档，当前 listener 不接管另一文档的恢复或重新加载；浏览器处理的是另一条历史项及其页面状态。

只有目标 URL 与当前 URL 除 fragment 外完全相同，且目标含 fragment 时，普通导航才走同文档片段路径。以已有的 `ol#reports` 为例，从 `/reports?sort=oldest#summary` 执行 `location.hash = "#reports"` 会沿用当前 `Document`、增加一项历史记录并滚到列表。片段定位和滚动由浏览器完成，但本例的 `popstate` 监听器仍会从 URL 重读排序并重建列表，显示顺序不变。本机 Chrome 157 在该路径先派发 `popstate`（`state` 为 `null`），再派发 `hashchange`。反过来，从 `/reports?sort=recent#summary` 用 `location.assign("?sort=oldest#summary")` 改查询，即使保留 `#summary` 也会导航到另一个 `Document`。History API 调用 `pushState()` 改成另一个片段不会自动滚动，也不会因调用本身派发 `popstate` 或 `hashchange`；若用户稍后遍历该历史项，才按历史遍历步骤处理。本例的排序历史项只改 query、保留 `#summary`，Back/Forward 由 `popstate` 同步排序而不触发 `hashchange`。客户端路由器可以复用这些历史项，但 URL 变化与视图绘制是两项不同工作。

浏览器首次收到 `.../reports?sort=recent#summary` 时，`#summary` 是浏览器用来定位的片段，服务器只处理路径与查询。排序点击改成 `sort=oldest` 后，仍是同一个 `Document`：浏览器不重新解析 `/reports`，应用继续负责产生新列表节点。这个边界让地址可复制、可返回，同时不把 History API 误解成网络导航。

### 定时导航怎样用文本更新并允许取消？

这个倒计时为普通文档导航留下等待和取消窗口。`setInterval(..., 1000)` 中的 1000 毫秒是请求间隔，不承诺每秒准时执行；主线程繁忙或浏览器对后台页面的计时器节流会让回调变晚。此代码按回调次数减秒，延迟会把实际跳转推迟；若需要按真实截止时刻倒数，应每次用当前时间重算剩余量。只有最后一次回调开始导航前点取消，清除定时器才能阻止跳转。一旦归零回调开始 `location.assign()`，取消按钮会先禁用并显示“正在跳转…”，`clearInterval()` 不能撤销已经开始的导航。

~~~html
<p id="countdown" role="status">5 秒后打开 example.com。</p>
<button id="cancel-navigation" type="button">取消</button>
~~~

~~~javascript
const message = document.querySelector("#countdown");
const cancel = document.querySelector("#cancel-navigation");
let seconds = 5;

const timer = setInterval(() => {
  seconds -= 1;
  if (seconds === 0) {
    clearInterval(timer);
    cancel.disabled = true;
    message.textContent = "正在跳转…";
    location.assign("https://example.com/");
    return;
  }
  message.textContent = seconds + " 秒后打开 example.com。";
}, 1000);

cancel.addEventListener("click", () => {
  clearInterval(timer);
  message.textContent = "已取消跳转。";
  cancel.disabled = true;
});
~~~

**延伸：** [DOM 事件如何传播，何时适合事件委托？](#4.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E6%80%8E%E6%A0%B7%E6%9F%A5%E8%AF%A2%E3%80%81%E6%9B%B4%E6%96%B0%20DOM%20%E5%B9%B6%E5%93%8D%E5%BA%94%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9F)解释点击处理器如何收到按钮事件；如果路由切换还要等待数据加载器并显示 pending/error 状态，见[React 路由怎样把地址映射到界面并加载数据？](#62.%20React%20%E8%B7%AF%E7%94%B1%E6%80%8E%E6%A0%B7%E6%8A%8A%E5%9C%B0%E5%9D%80%E6%98%A0%E5%B0%84%E5%88%B0%E7%95%8C%E9%9D%A2%E5%B9%B6%E5%8A%A0%E8%BD%BD%E6%95%B0%E6%8D%AE%EF%BC%9F)中的 Data Mode（数据模式）；组件状态更新见[React 如何把用户操作变成更新后的界面？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)。

> [!info]- 来源
> - URL 分量和序列化：[WHATWG URL Standard：URL representation](https://url.spec.whatwg.org/#url-representation)，Living Standard（2026-10-19 更新），URL record 组成。核对日期：2026-11-12。
> - 地址栏分量与 `assign()` / `replace()` / `reload()`：[WHATWG HTML：Location interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-location-interface)，Living Standard（2026-11-11 更新），`Location` API。核对日期：2026-11-12。
> - 普通导航、片段导航、URL/history 更新、历史步骤应用与刷新：[WHATWG HTML：Navigation and session history](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate)，Living Standard（2026-11-11 更新），[fragment navigations](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate-fragid)、[URL and history update steps](https://html.spec.whatwg.org/multipage/browsing-the-web.html#url-and-history-update-steps)、[updating the document for a history step](https://html.spec.whatwg.org/multipage/browsing-the-web.html#update-document-for-history-step-application)、[reloading](https://html.spec.whatwg.org/multipage/browsing-the-web.html#apply-the-reload-history-step)。核对日期：2026-11-12。
> - History API 可改写 URL 的组成条件、`pushState()` / `replaceState()` 与遍历：[WHATWG HTML：History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，Living Standard（2026-11-11 更新），同文档 URL 改写规则、state 与 delta traversal。核对日期：2026-11-12。
> - `popstate` / `hashchange` 的事件对象及相关事件步骤：[WHATWG HTML：Event interfaces](https://html.spec.whatwg.org/multipage/nav-history-apis.html#event-interfaces) 和上述 navigation / history-step 算法，Living Standard（2026-11-11 更新）；事件发生时机另以本机 Chrome 157 回放为准。核对日期：2026-11-12。
> - URL 查询参数的读取、重复值和序列化：[WHATWG URL Standard：URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，Living Standard（2026-10-19 更新），`get()`、`getAll()`、`set()`、`append()` 与 form-urlencoded 序列化。核对日期：2026-11-12。
> - 倒计时的文本更新与计时器初始化/取消：[WHATWG DOM：Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[WHATWG HTML：Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，Living Standard（2026-11-11 更新）。超时表示最早可运行时间，实际回调还要等待事件循环调度。核对日期：2026-11-12。
## 3. 脚本如何影响 HTML 解析与文档就绪？

案例背景：报表服务器已返回标题、排序按钮和初始行，浏览器还在解析 HTML，并同时获取 `/reports.css` 与 `/reports.js`。用户想先看到正文；排序按钮应在处理器安装后才可用。下面按脚本获取、执行和文档就绪的先后关系判断哪些工作会挡住哪一步。

### 不同脚本属性怎样改变解析顺序？

表格说的是 HTML parser（HTML 解析器）插入的脚本；动态插入的脚本有不同默认调度，不能把它们混为一谈。

| 脚本形式 | 下载与解析的关系 | 运行时机与顺序 |
|---|---|---|
| 外部经典脚本，不带 `async` / `defer` | 主 parser 处理到脚本时可开始请求；浏览器也可能由推测解析更早请求资源。主 parser 到达该元素后转而处理脚本；资源或阻塞样式表尚未就绪时先等待 | 脚本同步执行完后 parser 才继续解析，保持文档顺序 |
| 外部经典脚本 `defer` | 与解析并行获取 | 解析完成后、`DOMContentLoaded` 前执行；多个 defer 脚本按文档顺序 |
| 外部经典脚本 `async` | 与解析并行获取 | 下载就绪后尽快执行；若解析还在进行，会暂时打断解析；不保证多个 async 脚本的顺序 |
| 普通模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 默认在解析完成后按文档顺序开始求值；各模块依赖按依赖关系处理 |
| `async` 模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 模块及其依赖就绪后尽快执行，不保证相对其他异步脚本的顺序 |
| 内联经典脚本，有无 `defer` | 没有外部文件要获取 | parser 到达该元素且没有待等的阻塞样式表时执行；没有 `src` 时 `defer` 不起延后作用 |

`defer` 适合依赖已解析文档、且需要保持外部经典脚本文档顺序的代码。`async` 适合执行不依赖解析结果或其他脚本的独立工作。模块脚本默认延后执行，给模块加 `async` 会改变这个选择。

### 为什么解析器有时必须停下来？

解析 HTML 就像按顺序读取标记并逐个建立节点。经典脚本能在节点还没建完时查询、修改文档，甚至用 `document.write()` 改变后续解析结果；浏览器不能一概把这种脚本当作与文档无关的文件而继续前进。因此，脚本获取可以和其他资源获取重叠，但脚本执行本身可能成为解析的依赖点。

样式表对脚本的影响不是浏览器先分析某段 JavaScript 是否调用了 `getComputedStyle()`。HTML 定义了脚本阻塞样式表集合：由 parser 创建、作为启用样式表处理、media 条件匹配且仍在等待中的 `style` / stylesheet `link`，可以进入该集合。后续要执行的同步 parser 脚本或延后脚本，会按这个集合判断是否等待；即便 `/reports.js` 只给按钮注册事件，也可能先等 `/reports.css`。

本例中由 parser 在 `<head>` 创建、已启用且 `media` 匹配的 stylesheet link 可能阻塞渲染，因此资源尚未就绪时首帧可能推迟。不是“所有 CSS 必须全部下载后才能开始任何绘制”，而是具体资源是否阻塞由渲染与脚本各自的条件决定。

以下 HTML 是报表页的初始结构。本节只跟踪 head 中的 CSS 与模块，以及正文排序控件和图片；标题片段锚点与图标形状不改变这段加载时序。

~~~html
<head>
  <link rel="stylesheet" href="/reports.css">
  <script type="module" src="/reports.js"></script>
</head>
<main>
  <h1 id="summary">Recent reports</h1>
  <img src="/report-summary.png" width="320" height="180" alt="Report summary">
  <div id="sort-controls">
    <button
      type="button"
      data-sort="recent"
      aria-pressed="true"
      disabled
    >
      <span>Most recent</span>
    </button>
    <button
      type="button"
      data-sort="oldest"
      aria-pressed="false"
      disabled
    >
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 13V3m-4 4 4-4 4 4" fill="none" stroke="currentColor"
              stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <span>Oldest first</span>
    </button>
  </div>
  <ol id="reports">
    <li data-id="may">May report</li>
    <li data-id="april">April report</li>
  </ol>
</main>
~~~

服务器已经输出 May → April 的初始顺序；外部模块 `/reports.js` 在 parser 完成后运行。两个按钮先以原生 `disabled` 状态输出，避免模块尚未安装处理器时把用户的点击静默丢掉。本例模块默认延后到解析结束才执行，因此 guard 走 `interactive` 分支，直接安装处理器；`loading` 分支适用于其他入口在文档仍解析时运行的脚本。

以下是外部 `/reports.js` 的最小实现。本例只展示处理器何时安装、如何同步列表和按钮状态，不在这里重放 URL 与浏览器历史逻辑。

~~~javascript
const records = [
  { id: "may", date: "2026-05-01", label: "May report" },
  { id: "april", date: "2026-04-01", label: "April report" },
];

function renderReports(list, controls, sort) {
  const rows = [...records].sort((a, b) =>
    sort === "oldest" ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date)
  );
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.setAttribute("aria-pressed", String(button.dataset.sort === sort));
  }
  list.replaceChildren(...rows.map(({ id, label }) => {
    const item = document.createElement("li");
    item.dataset.id = id;
    item.textContent = label;
    return item;
  }));
}

function initializeReportControls() {
  const controls = document.querySelector("#sort-controls");
  const list = document.querySelector("#reports");
  if (!controls || !list) return;

  controls.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest("button[data-sort]");
    if (!button || !controls.contains(button)) return;
    const sort = button.dataset.sort;
    if (sort !== "recent" && sort !== "oldest") return;
    renderReports(list, controls, sort);
  });

  renderReports(list, controls, "recent");
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.disabled = false;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeReportControls, { once: true });
} else {
  initializeReportControls();
}
~~~

下面前两行对照两种资源返回顺序：CSS 先完成、模块后到；或模块先到、CSS 仍在等待。两者都汇合到 parser 已结束、脚本可运行的阶段。

| 此刻的资源状态 | parser、DOM 与首帧 | 排序处理器与就绪事件 |
|---|---|---|
| 正文已解析为 DOM（此时 `readyState=interactive`），`/reports.css` 已就绪，`/reports.js` 或其 `import` 依赖仍在下载，图片未完成 | 浏览器可能先绘出标题和 May → April；图片的 320×180 尺寸先占位；按钮仍为 disabled | 排序监听器尚未安装，按钮不能触发；`DOMContentLoaded` 仍等待 deferred 模块 |
| 模块响应先返回，但 CSS 仍是阻塞脚本的样式表 | parser 仍可继续补全正文；完成解析后 `readyState` 变为 `interactive`，模块执行仍要等 CSS 解除阻塞 | 按钮继续 disabled；模块未运行，`DOMContentLoaded` 尚未触发 |
| parser 已结束（`readyState=interactive`），模块及其依赖已可执行，CSS 已解除阻塞 | 模块同步调用初始化函数，保留 May → April 初始顺序，随后启用两个按钮 | 排序监听器和初始 `aria-pressed=true/false` 已就绪；普通同步模块执行结束后才派发 `DOMContentLoaded` |
| 用户点已启用的 **Oldest first** | 不再解析 HTML；处理器按日期重建列表行 | `aria-pressed` 变为 `false/true`，顺序变为 April → May |

这条链把“有 DOM”“可绘制”和“处理器已绑定”分开：模块未运行时按钮仍不可用；同步绑定和初始渲染完成后才启用。若图片较晚到，预留的宽高减少它到达后挤动文字的机会。

### `DOMContentLoaded` 和 `load` 分别说明什么？

`DOMContentLoaded` 在 HTML parser 完成解析并处理延后脚本后派发到 `Document`。`document.readyState` 在 parser 停止时先变为 `interactive`，此时延后脚本仍可能等待模块脚本、其依赖或阻塞脚本的样式表。普通 `defer` 脚本在该流程同步执行；默认模块也在解析后开始求值。模块及其依赖均同步求值时，模块代码会在事件前执行完；模块遇到顶层 `await` 时，后续代码可在事件后继续，依赖含顶层 `await` 的模块也可能推迟导入方的代码。若初始化把后续工作放进 Promise 回调或异步请求，也可能晚于该事件。因此它不表示所有应用初始化已完成，也不等图片或 `async` 脚本完成。延后脚本可能等待脚本阻塞样式表，所以样式表也能间接推迟 `DOMContentLoaded`。

`load` 事件由 `Window` 的监听器接收；HTML 使用历史兼容的 target override，因此回调中 `event.currentTarget` 是 `window`，而 `event.target` 是 `document`。触发前，文档转入 `complete`，所有仍会延迟 `load` 的资源都已完成；普通图片、样式表、脚本和子框架可能在其中，懒加载资源通常不必挡住它。精确范围由 HTML 的加载算法决定。

| 检查点与 `readyState` | 事件与监听位置 | 此时可依赖的条件 |
|---|---|---|
| parser 停止（`interactive`） | `readystatechange` 在 `Document` 上触发 | HTML 已解析完；延后脚本仍可能在执行或等待 |
| DOM 内容加载完（`interactive`） | `DOMContentLoaded` 在 `Document` 上触发 | parser 延后脚本已处理；图片和 `async` 脚本不作为此事件的等待条件，模块的异步延续仍可能继续 |
| `load`（`complete`） | 监听器在 `Window` 上运行；`event.target` 为 `Document` | 会延迟 load 的资源已完成；应用 API、hydration 或其他 Promise 仍可能未完成 |

这些事件和状态本身不报告首帧，也不追踪应用自己的初始化结果。本例正常执行同步初始化时，排序按钮确实在 `DOMContentLoaded` 前启用；异步初始化的应用则需要自己的就绪信号。

### 脚本晚到时，怎样避免错过 `DOMContentLoaded`？

`DOMContentLoaded` 是一次事件，不是以后可订阅的完成状态。若代码通过动态导入或延迟执行，在事件之后才注册监听器，处理器不会补发。前面 `/reports.js` 末尾的 guard 读取 `document.readyState`：仍是 `loading` 时订阅事件并一次性调用已完整定义的 `initializeReportControls()`；否则文档解析已结束，就立即初始化。同步执行的 JavaScript 不会被浏览器事件打断，因此状态检查和注册之间不会插入一次 `DOMContentLoaded` 派发。

`readyState` 的 `loading` 表示 HTML parser 仍在解析；`interactive` 表示解析已结束但延后脚本与子资源流程可能尚未完成；`complete` 表示文档已进入加载完成阶段。这个 guard 只保证 DOM 已可查询：若初始化依赖尚未执行的 defer/module 脚本副作用，应等待该脚本自己的就绪信号。文档状态也不代表报表 API 请求、React hydration 或其他应用异步初始化已经完成；若初始化包含这类异步工作，仍需单独表示并等待。

判断主要内容何时出现，要观察绘制；判断排序按钮是否可用，要看其初始化状态。首帧可以早于 `load`，而报表内容也可能已显示、模块脚本还没注册排序处理器。反过来，`DOMContentLoaded` 触发后，一次长脚本任务仍会让点击处理器排队等待。可见时点和就绪事件的区别见[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)；用户侧的加载与交互数据见[如何测量并诊断网页性能问题？](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - 解析器插入的经典脚本、`async`、`defer` 与模块调度：[WHATWG HTML：script processing model](https://html.spec.whatwg.org/multipage/scripting.html#script-processing-model)，Living Standard（2026-11-11 更新），外部/内联脚本、defer 模块列表与 async 集合。核对日期：2026-11-12。
> - parser 等待时允许浏览器推测获取后续资源：[WHATWG HTML：Speculative HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html#speculative-html-parsing)，Living Standard（2026-11-11 更新）；这项预取优化的具体时机依实现而异。核对日期：2026-11-12。
> - 脚本阻塞样式表的条件：[WHATWG HTML：interactions of styling and scripting](https://html.spec.whatwg.org/multipage/semantics.html#interactions-of-styling-and-scripting)，Living Standard（2026-11-11 更新），parser 创建、样式表有效状态、media 匹配及阻塞集合。核对日期：2026-11-12。
> - 样式表链接可能阻塞渲染的条件：[WHATWG HTML：link type stylesheet](https://html.spec.whatwg.org/multipage/links.html#link-type-stylesheet) 与 [render-blocking mechanism](https://html.spec.whatwg.org/multipage/dom.html#render-blocking-mechanism)，Living Standard（2026-11-11 更新），parser 创建的 stylesheet link 可能 render-blocking；外链资源处理步骤检查 `media` 匹配与 render-blocking 状态。核对日期：2026-11-12。
> - 解析结束时的 `interactive`、延后脚本、`DOMContentLoaded` 与 `load` 派发：[WHATWG HTML：The end](https://html.spec.whatwg.org/multipage/parsing.html#the-end)，Living Standard（2026-11-11 更新），parser 结束、deferred script 队列、DOM content loaded 与窗口 load event。核对日期：2026-11-12。
> - `document.readyState` 的 `loading`、`interactive`、`complete` 及 `readystatechange`：[WHATWG HTML：Reporting document loading status](https://html.spec.whatwg.org/multipage/dom.html#reporting-document-loading-status)，Living Standard（2026-11-11 更新）。核对日期：2026-11-12。
> - 顶层 `await` 与模块依赖的异步求值：[ECMAScript 2027：Module evaluation](https://tc39.es/ecma262/#sec-moduleevaluation)，异步模块求值及其依赖关系。DOMContentLoaded / load 的触发顺序由上述 HTML 算法决定。核对日期：2026-11-12。
## 4. 浏览器怎样查询、更新 DOM 并响应用户输入？

案例背景：报表页从 `https://example.test/reports?sort=recent#summary` 打开，列表先显示 May、April 两行。用户点“最早优先”按钮里的文字或图标后，原生示例要找到所属按钮，从 `data-sort` 读出 `oldest`，再把现有行节点排成 April、May，并更新按钮状态。这里把 History API 处理 URL、React 管理状态作为相邻交接；本页先走通普通文档树中的查询、内容更新和事件处理。Document Object Model (文档对象模型，DOM) 把 HTML 文档表示为节点树，JavaScript 可以查询这些节点、改写其状态，并响应输入事件。

本章各示例在独立页面或作用域中运行，避免把不同示例的顶层代码拼成同一脚本（重复声明 `const controls` 会报错）。同一示例中的 HTML、交互和清理代码要一起使用。建表和拖动示例使用各自的 HTML；查询、事件、克隆、排序与尺寸观察示例使用后文委托节提供的 `#sort-controls` / `#reports` 初始 HTML。

### DOM 树里有哪些节点？

文档节点包含元素节点、文本节点和注释等；元素的 attribute（属性）描述元素状态，但 attribute 不是元素的子节点。常用的 `nodeType` 值如下：

| `nodeType` | 节点 | 报表页中的例子 |
|---:|---|---|
| 1 | Element（元素） | `<ol>`、`<li>`、`<button>` |
| 2 | Attr（属性） | `id="reports"`（有 `Attr` 对象，但不是树的子节点） |
| 3 | Text（文本） | `May report` |

向上找父级时，`parentNode` 可返回任意节点父级：`<html>` 的 `parentNode` 是 Document，而 `parentElement` 只返回元素父级，所以 `<html>.parentElement` 为 `null`。`nodeName` 命名任意节点，`tagName` 只属于元素；`nodeValue` 读取单个 Text 节点的值，在 Element 上则为 `null`，读取元素后代文字应使用 `textContent`。若要查某行的下一个元素，使用 `nextElementSibling`；`nextSibling` 可能先遇到 HTML 换行空白对应的文本节点。同理，`firstChild` 与 `firstElementChild` 可能不是同一项。`childNodes` 包含文本、注释等节点，`children` 只包含元素；它们的集合更新规则见[修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F)。

查询 DOM 使用 CSS 选择器。`querySelector()` 返回第一个匹配元素；没有匹配项时返回 `null`，所以后续读取前要先处理找不到的情况。`querySelectorAll()` 返回匹配项组成的静态 `NodeList`，创建后不会因之后插入的新按钮而自动增加成员。

下面的查询、事件日志和委托代码使用后面“什么时候用父级监听器处理子控件？”一节中的报表初始 HTML；先载入该 HTML，再在独立运行上下文中执行所需的代码块。

~~~javascript
const controls = document.querySelector("#sort-controls");
if (controls) {
  const oldest = controls.querySelector('button[data-sort="oldest"]');
  const buttons = controls.querySelectorAll("button[data-sort]");
  // oldest 是第一个匹配项或 null；buttons 是当前匹配项的静态列表。
}
~~~

`#sort-controls` 按 ID 找工具栏；`button[data-sort="oldest"]` 同时匹配元素名和 attribute 值。选到控件后，再决定修改文字、HTML 内容属性、DOM 对象属性还是节点顺序。

### 修改内容、HTML 属性和 DOM 对象属性有何区别？

文本和标记要用不同接口。`textContent` 读取后代文本，赋值会用一个文本内容替换子树；`innerText` 读写渲染文本：读取时元素若未渲染，会退回到后代文本；若已渲染，结果会受显示状态影响；赋值中的换行会成为可见换行。`innerHTML` 读取或解析 HTML 字符串。把纯文字放入 DOM 时使用 `textContent`；只有受信任或已净化的标记才作为 HTML 解析。

| 写法 | 控制什么 | 报表页上的用途 |
|---|---|---|
| `row.textContent = label` | 文字，不解析 HTML | 写入报表名称 |
| `row.innerText` | 渲染后的文字语义；未渲染时退回后代文本 | 读取或写入可见文本 |
| `row.innerHTML = markup` | 子树的 HTML 标记 | 只有模板可信或已净化时才插入标记 |
| `element.setAttribute(name, value)` | HTML content attribute（HTML 内容属性） | 设置 `data-id`、`alt`、`title` 等声明 |
| `element.classList`、`element.style` | class 集合与内联样式 | 切换状态 class，或写入必要的单次样式 |

HTML 内容属性是元素当前的标记属性；许多 DOM property（DOM 对象属性）会反射对应 attribute。文本输入框的 `value` 属性提供了一个重要区别：`value` 内容属性给出默认值，`input.value` 则表示当前值。当前值一旦变成 dirty（已修改），再改 attribute 只更新默认值，直到表单重置。

~~~html
<form id="sort-form">
  <label>排序关键词 <input id="sort-query" value="recent"></label>
</form>
~~~

~~~javascript
const query = document.querySelector("#sort-query");
query.setAttribute("value", "april"); // 尚未修改：当前值也变为 april
const beforeEdit = [query.value, query.defaultValue];

query.value = "oldest"; // 改当前值，并标记为 dirty
query.setAttribute("value", "recent"); // dirty 后只改默认值
const afterEdit = [query.value, query.defaultValue];
query.form.reset(); // 当前值回到默认值，并清除 dirty 标记
const afterReset = [query.value, query.defaultValue];
console.log(JSON.stringify({ beforeEdit, afterEdit, afterReset }));
~~~

HTML 的 dirty value flag（值已修改标记）区分当前输入值和可变默认值；`reset()` 会恢复默认值。对 boolean attribute（布尔属性），例如 `disabled`，只看元素自己的 attribute 是否存在：`setAttribute("disabled", "false")` 仍会设置它。`button.disabled = false` 会移除按钮自己的禁用属性，但不一定让它脱离 HTML 禁用状态：若它位于禁用的 `fieldset` 中，仍会匹配 `:disabled`；该 fieldset 的第一个 `legend` 元素子节点内的后代控件有例外。

~~~html
<fieldset disabled>
  <legend>
    <button id="legend-button" type="button">例外位置</button>
  </legend>
  <button id="inherited-button" type="button">受 fieldset 禁用</button>
</fieldset>
<button id="own-button" type="button">自己的 disabled 属性</button>
~~~

~~~javascript
const inherited = document.querySelector("#inherited-button");
inherited.disabled = false;
const own = document.querySelector("#own-button");
own.setAttribute("disabled", "false");
const setToFalse = [own.disabled, own.matches(":disabled")];
own.disabled = false;
const afterClearingOwn = [own.disabled, own.matches(":disabled")];

const states = {
  ownAttribute: setToFalse,
  afterClearingOwn,
  inherited: [inherited.disabled, inherited.matches(":disabled")],
  firstLegend: [
    document.querySelector("#legend-button").disabled,
    document.querySelector("#legend-button").matches(":disabled"),
  ],
};
console.log(JSON.stringify(states));
// ownAttribute: [true, true]; afterClearingOwn: [false, false]
// inherited: [false, true]; firstLegend: [false, false]
~~~

| 控件状态 | `button.disabled` | `matches(":disabled")` | 原因 |
| --- | --- | --- | --- |
| 给自身 `setAttribute("disabled", "false")` 后 | `true` | `true` | 布尔属性只看是否存在。 |
| 再设自身 `disabled = false` 后 | `false` | `false` | 移除了自身的禁用属性。 |
| 禁用 fieldset 的普通后代 | `false` | `true` | 控件自身未禁用，但祖先 fieldset 生效。 |
| fieldset 的第一个 `legend` 元素子节点内的后代 | `false` | `false` | 该位置不继承 fieldset 的禁用。 |

若要检查 HTML 表单禁用状态（包含 `fieldset` 继承），用 `button.matches(":disabled")`；若只想读写元素自己的禁用属性，用 `button.disabled`。

要更新筛选行的外观，`className = "selected"` 会整体替换 class 字符串；`classList.add()`、`remove()` 和 `toggle()` 改单个类。`element.style.backgroundColor` 只读写行内的声明；样式表计算出的生效值要用 `getComputedStyle(element)` 读取。CSS property 在 JavaScript 里通常使用 camelCase（小驼峰）。`data-id="may"` 可通过 `row.dataset.id` 读取与设置，`dataset` 中已存在的值是字符串，缺少的 data 属性读到 `undefined`。多段名称会转为小驼峰，例如 `data-report-id` 对应 `dataset.reportId`。图片的 `src` 选择资源，`alt` 提供替代文本（装饰图可用空值），`title` 是补充信息，不能替代 `alt`。

~~~javascript
const textDemo = document.createElement("div");
document.body.append(textDemo); // 附加到页面后，innerText 按渲染文本处理
textDemo.textContent = "<b>May</b>";
const literal = [textDemo.textContent, textDemo.children.length];
textDemo.innerText = "May\nReport";
const visibleLines = [textDemo.innerHTML, textDemo.innerText];
console.log(JSON.stringify({ literal, visibleLines }));
// literal: ["<b>May</b>", 0]
// visibleLines: ["May<br>Report", "May\nReport"]
~~~

### 怎样生成、移动或克隆一组节点？

为单独演示如何从结构化数据建表，设一张学校成绩表固定按 Name、Subject、Grade 排列。对象字段顺序不是表格的列定义；三条记录应分别显示 Ron—Math—100、Jack—Calculus—70、Mar—Business—90：

~~~html
<table>
  <thead><tr><th>Name</th><th>Subject</th><th>Grade</th></tr></thead>
  <tbody id="students"></tbody>
</table>
~~~

~~~javascript
const students = [
  { name: "Ron", subject: "Math", grade: "100" },
  { name: "Jack", subject: "Calculus", grade: "70" },
  { name: "Mar", subject: "Business", grade: "90" },
];
const columns = ["name", "subject", "grade"];
const body = document.querySelector("#students");

for (const student of students) {
  const row = document.createElement("tr");
  for (const column of columns) {
    const cell = document.createElement("td");
    cell.textContent = student[column];
    row.append(cell);
  }
  body.append(row);
}
~~~

每个记录依照同一份 `columns` 产生三格，输入值只进入文本节点。`append()` 会把新节点追加到末尾；若传入已经在文档中的节点，它会将该节点移动到新位置。`insertBefore(node, reference)` 把节点放到参考节点前，`remove()` 将节点从树上移除。

`cloneNode(true)` 会复制节点、后代结构和 HTML attribute。写在 `onclick="..."` 中的内容属性会随节点复制；通过 `element.onclick = handler` 设置的 DOM 对象属性和 `addEventListener()` 注册的监听器不会复制。若副本及其后代有 `id`，插入同一文档前应改成不冲突的 ID，并同步更新指向它们的引用。需要复制行为时，在新节点上重新注册监听器：

本例从后文委托节的两行初始列表单独运行：May 源行带 `data-id="may"` 和 `data-date="2026-05-01"`，自身没有 DOM `id` attribute，后代也没有带 ID 的节点。深克隆会保留这两个 data 属性；代码给副本新增一个文档内唯一的 DOM `id`。运行后列表会多一行 May 副本，因此不要把它与后面的两行排序表串成同一轮状态。

~~~javascript
function handleReportClick(event) {
  console.log(event.currentTarget.dataset.id);
}

const source = document.querySelector('#reports [data-id="may"]');
const copy = source.cloneNode(true);
copy.id = "may-row-copy"; // 新增 DOM id；data-id 仍标识 May 报表
copy.addEventListener("click", handleReportClick);
document.querySelector("#reports").append(copy);
~~~

对同一元素给 `onclick` 属性赋新函数会替换先前的函数；多处代码都需监听时，用 `addEventListener()` 可以各自注册和移除 listener（监听器）。只需响应一次时可设 `{ once: true }`；若要提前移除，保留原函数引用，并使用相同 capture（捕获阶段）选项调用 `removeEventListener()`。也可把同一 `AbortSignal`（中止信号）交给多个监听器，结束该页面区域时调用 `abort()` 一并清理。

### 一次点击沿哪些节点传播？

浏览器为事件确定传播路径（event path）后，监听器可在 capture phase（捕获阶段）、target phase（目标阶段）和 bubble phase（冒泡阶段）运行。下面限定在普通 DOM 树中的 click：点标签文字时 `target` 是 `span`；点 SVG 箭头的可见描边时 `target` 是 `<path>`，点图标留白时则可能是 `svg`。这段代码只记录事件顺序；图展示标签文字分支经过的节点，并在工具栏层带出下一节的委托处理器。

~~~javascript
const controls = document.querySelector("#sort-controls");
const button = controls.querySelector('button[data-sort="oldest"]');
const label = button.querySelector(".sort-label");

document.body.addEventListener("click", () => console.log("body capture"), {
  capture: true,
});
label.addEventListener("click", () => console.log("span target"));
button.addEventListener("click", () => console.log("button bubble"));
controls.addEventListener("click", () => console.log("controls bubble"));
document.body.addEventListener("click", () => console.log("body bubble"));
~~~

点标签文字时，上面日志按 body 捕获、span 目标、button 冒泡、controls 冒泡、body 冒泡的顺序运行：

![普通 DOM 树中 click 的监听器顺序，以及 target 与 currentTarget 的变化](../../frontend/browser-apis/resources/dom-manipulation-and-events-event-path.svg)

图对应上面的点文字日志；工具栏框展示同一传播路径到达 `#sort-controls` 后，由下一节注册的委托监听器继续处理，这不是上面只打印日志的 `controls bubble` 回调。点箭头描边时，路径为 `path → svg → button → #sort-controls → body`；点图标留白时从 `svg` 开始，随后经过同样的祖先。委托器从实际命中的 `event.target` 向上找到按钮，两条路径都不经过 `.sort-label` span。

`event.target` 在一次普通 DOM 派发中保持为最初命中的节点；`event.currentTarget` 则是当前监听器绑定的节点。图中的文字分支依次以 `body`、`span`、按钮、工具栏和 `body` 为 `currentTarget`；点箭头描边或图标留白时，target 分别为 `path` 或 `svg`，两条路径都不含 span。普通函数监听器中的 `this` 也指向 `currentTarget`，箭头函数的 `this` 则保留词法绑定。图不覆盖 Shadow DOM（影子 DOM）：跨影子边界时 `target` 可能被重定向；`bubbles` 决定是否向普通祖先冒泡，`composed` 决定能否穿过影子边界，二者不是同一开关。输入框获得和失去焦点时分别派发 `focus` 与 `blur`，这两个原生事件不冒泡；父级要委托焦点变化时可监听会冒泡的 `focusin` 与 `focusout`。

### 什么时候用父级监听器处理子控件？

event delegation（事件委托）让一个父级监听器处理多个后代控件，包括稍后插入的控件，因此不用逐一注册监听器。它适合事件会冒泡、父级确实拥有这些控件、目标匹配规则清楚的场景；它不会消除每次事件分发或处理器本身的计算。

~~~html
<h1 id="summary">Recent reports</h1>
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true">
    <span class="sort-label">Most recent</span>
  </button>
  <button type="button" data-sort="oldest" aria-pressed="false">
    <svg class="sort-icon" width="16" height="16" viewBox="0 0 16 16"
         aria-hidden="true">
      <path d="M8 13V3m-4 4 4-4 4 4" fill="none" stroke="currentColor"
            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span class="sort-label">Oldest first</span>
  </button>
</div>
<ol id="reports">
  <li data-id="may" data-date="2026-05-01">May report</li>
  <li data-id="april" data-date="2026-04-01">April report</li>
</ol>
~~~

图标 SVG 设为 `16 × 16`，内部 `path` 画出箭头，因此页面中有实际可见的命中区域；旁边的文字已经说明按钮用途，图标用 `aria-hidden="true"` 隐藏其重复信息。

~~~css
#sort-controls .sort-icon {
  vertical-align: -0.15em;
}
~~~

~~~javascript
const controls = document.querySelector("#sort-controls");
const reports = document.querySelector("#reports");

function applySort(intent, activeButton) {
  if (intent !== "recent" && intent !== "oldest") return;

  const rows = Array.from(
    reports.querySelectorAll(":scope > li[data-date]")
  );
  const direction = intent === "oldest" ? 1 : -1;
  rows.sort((a, b) =>
    direction * a.dataset.date.localeCompare(b.dataset.date)
  );
  for (const row of rows) reports.append(row);

  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.setAttribute("aria-pressed", String(button === activeButton));
  }
}

controls.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-sort]");
  if (!button || !controls.contains(button)) return;

  const intent = button.dataset.sort;
  console.log("Sort requested:", intent); // 点击“最早优先”时得到 "oldest"
  applySort(intent, button);
});
~~~

点击标签文字或图标时，`closest()` 从命中的后代向上找到带 `data-sort` 的按钮；`controls.contains(button)` 确认它属于这个工具栏。处理器读到 `oldest` 后，`applySort()` 先拒绝未知意图，再用固定的 ISO 日期值比较两行。`querySelectorAll()` 给出当前行的静态集合，`Array.from()` 把它变为可排序数组；对现有行调用 `append()` 会移动节点，而不是重新创建行。事件处理器同步完成后，本例得到：

| 时点 / 意图 | 行顺序（`data-id`） | `recent` | `oldest` |
| --- | --- | --- | --- |
| 初始 HTML / `recent` | `may` → `april` | `aria-pressed="true"` | `aria-pressed="false"` |
| 点击处理完成 / `oldest` | `april` → `may` | `aria-pressed="false"` | `aria-pressed="true"` |

本节的 `applySort()` 只负责把同一排序意图写成 DOM 顺序和按钮状态；完整页面还要让 URL、前进后退与这份状态同步，见[每次 URL 变化都会加载新文档吗？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)。若操作会删除匹配节点并继续遍历，应先取静态快照，避免移除节点改变实时集合；集合差异见[修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F)。

### 默认动作与传播控制是两回事

按钮若位于表单中，点击可能触发表单提交；这是与事件传播分开的默认动作。`preventDefault()` 只在事件可取消且监听器不是 passive listener（被动监听器）时取消默认动作，它不会停止冒泡。`stopPropagation()` 不取消正在运行的回调，也不会跳过当前 `EventTarget` 本次捕获或非捕获调用中剩余的匹配监听器；它会阻止随后沿路径进行的监听器调用。目标上的捕获调用结束后，若它设置了停止传播标志，目标上的非捕获调用会被跳过（两次调用中的 `eventPhase` 都是 `AT_TARGET`）。`stopImmediatePropagation()` 还会停止当前 `EventTarget` 本次调用中的后续监听器。

如果滚动或触控监听器不需要取消浏览器默认滚动，设置 `{ passive: true }` 能表明这一点；被动监听器调用 `preventDefault()` 无法取消默认动作。DOM 标准规定，未显式设置 `passive` 的 `touchstart`、`touchmove`、`wheel` 和 `mousewheel` 监听器，在 `Window`、`Document`、`documentElement` 或 `body` 上默认 passive 为 true；确实需要拦截时，应先按事件的 `cancelable` 状态判断，再显式设置 `{ passive: false }`。

### 移动端点击与手势策略

历史上的移动端 click 延迟有特定条件：部分浏览器曾等待判断一次触摸是否还会成为双击缩放手势。它不是今天所有浏览器、所有 viewport（视口）或所有输入模式下的固定延迟。先设置符合设备宽度的 viewport；不要为了绕开历史延迟而禁止用户缩放。

~~~html
<meta name="viewport" content="width=device-width, initial-scale=1">
~~~

若某个控件不需要双击缩放，但仍应允许平移和双指缩放，可以对该控件使用 Pointer Events（指针事件）的 `touch-action: manipulation`：

~~~css
#sort-controls button[data-sort] {
  touch-action: manipulation;
}
~~~

它让浏览器保留平移和连续缩放，同时不把双击缩放作为该元素上的手势。把规则限制在确实需要的控件，不要用 `touch-action: none` 全局封锁操作。原生 `<button>` 自带键盘激活；自制的 `role="button"` 还必须补足键盘行为。Chrome 的 viewport 诊断指出一个特定条件：初始视口未针对移动设备优化时，点击可能延后至多 300 毫秒；其他浏览器和输入设置会不同，不能把这个值当成所有移动端点击的固定时延。除非目标设备实测仍有兼容问题，不要同时在 `touchend` 和 `click` 上触发同一动作，以免合成 click 与原生 click 重复执行。

### 拖动时怎样跟踪坐标并处理取消？

Pointer Events（指针事件）把鼠标、触摸和笔输入统一到 pointer 事件，但一次拖动不是只有 `pointermove`：它从 `pointerdown` 开始，可通过 `setPointerCapture(pointerId)` 把后续该 pointer 的事件留给手柄；正常释放由 `pointerup` 结束，系统接管手势时可能收到 `pointercancel`，捕获释放后会有 `lostpointercapture`。清理时按 `pointerId` 匹配当前拖动，避免另一根手指或旧事件结束错误手势。

坐标属性对应不同参照系：

| 属性 | 参照系 | 适合回答的问题 |
|---|---|---|
| `clientX / clientY` | viewport（视口） | 指针现在相对当前可视区域在哪里 |
| `pageX / pageY` | 文档 | 指针在页面内容坐标中在哪里 |
| `screenX / screenY` | 屏幕 | 指针相对设备显示区域的位置 |

下面把一个报表卡片放进定位容器。移动用 client 坐标的差值；初始卡片位置来自同一个定位容器的 `offsetLeft` / `offsetTop`。本例假设容器没有 CSS 缩放或旋转，拖动时页面与容器也不滚动；在此条件下，视口坐标的位移对应卡片的 CSS 像素位移。若变换或滚动改变坐标参照系，就需先转换到同一坐标空间。

~~~html
<div id="report-canvas">
  <button id="movable-report" type="button" aria-describedby="move-report-help">
    May report
  </button>
</div>
<p id="move-report-help">鼠标或触摸拖动卡片；聚焦后也可用方向键移动。</p>
~~~

~~~css
#report-canvas {
  position: relative;
  width: 24rem;
  height: 12rem;
  border: 1px solid;
}

#movable-report {
  position: absolute;
  left: 0;
  top: 0;
  touch-action: none;
}
~~~

~~~javascript
const card = document.querySelector("#movable-report");
let drag = null;

card.addEventListener("pointerdown", (event) => {
  const nonPrimary = !event.isPrimary;
  const secondaryMouse = event.pointerType === "mouse" && event.button !== 0;
  if (drag || nonPrimary || secondaryMouse) return;
  drag = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    left: card.offsetLeft,
    top: card.offsetTop,
  };
  card.setPointerCapture(event.pointerId);
});

card.addEventListener("pointermove", (event) => {
  if (!drag || drag.pointerId !== event.pointerId) return;
  const left = drag.left + event.clientX - drag.x;
  const top = drag.top + event.clientY - drag.y;
  card.style.left = `${left}px`;
  card.style.top = `${top}px`;
});

function finishDrag(event, canceled = false) {
  if (!drag || drag.pointerId !== event.pointerId) {
    return;
  }
  const start = drag;
  drag = null;
  if (canceled) {
    card.style.left = start.left + "px";
    card.style.top = start.top + "px";
  }
}

card.addEventListener("pointerup", finishDrag);
card.addEventListener(
  "pointercancel",
  (event) => finishDrag(event, true),
);
card.addEventListener(
  "lostpointercapture",
  (event) => finishDrag(event, true),
);

card.addEventListener("keydown", (event) => {
  const step = event.shiftKey ? 24 : 8;
  let dx = 0;
  let dy = 0;
  if (event.key === "ArrowLeft") dx = -step;
  else if (event.key === "ArrowRight") dx = step;
  else if (event.key === "ArrowUp") dy = -step;
  else if (event.key === "ArrowDown") dy = step;
  else return;

  event.preventDefault();
  card.style.left = `${card.offsetLeft + dx}px`;
  card.style.top = `${card.offsetTop + dy}px`;
});
~~~

卡片仍连接文档时，捕获让它在指针移出按钮后仍收到同一指针的移动与结束事件；正常抬起保留新位置，取消或捕获丢失则回到拖动起点。捕获目标脱离文档后，规范建议（SHOULD）把捕获目标改为 `document`，因此卸载时不能依赖卡片监听器收到 `lostpointercapture`。卸载区域时，应先清空拖动状态、释放捕获，再移除节点；下面的清理函数与前面的拖动代码共用同一作用域中的 `card` 和 `drag`：

~~~javascript
function disposeCard() {
  const activeDrag = drag;
  drag = null;
  if (activeDrag && card.hasPointerCapture(activeDrag.pointerId)) {
    card.releasePointerCapture(activeDrag.pointerId);
  }
  card.remove();
}
~~~

`touch-action: none` 会禁止从卡片上开始的视口平移与缩放，所以只应放在确实需要拖动的小控件上；页面其余区域仍可正常滚动。另有 `contextmenu` 和 `selectstart` 的默认动作可在特定自定义交互上取消，但全页禁用菜单或选中文字会移除浏览器本身提供的操作，也不是安全机制。

### 窗口 resize、元素尺寸与 scroll 应监听在哪里？

`resize` 事件用于窗口/视口尺寸变化；若要响应某个报表容器自身的尺寸变化，使用 `ResizeObserver`（尺寸变化观察器）。`scroll` 应监听页面或实际发生滚动的容器；元素滚动时，把 listener 绑在该元素上，而不是假设它会冒泡到任意父级。两种事件都可能频繁触发，应让处理器只做该界面所需的更新。

Navigator 对象（浏览器环境信息接口）提供环境线索：`navigator.language` 是浏览器报告的首选语言，`navigator.platform` 是平台字符串，`navigator.userAgent` 是 user-agent 字符串（用户代理字符串）。语言不是国籍，平台或 user-agent 字符串也不能证明某个 API 可用；相关识别信息还会增加隐私暴露。页面需要容器尺寸能力时，直接检测 `ResizeObserver`，不按浏览器品牌猜测。

~~~javascript
const reportList = document.querySelector("#reports");
const lifetime = new AbortController();
let sizeObserver = null;

function recordViewportWidth() {
  if (reportList) {
    reportList.dataset.viewportWidth = String(window.innerWidth);
  }
}

if (reportList && typeof ResizeObserver === "function") {
  sizeObserver = new ResizeObserver(([entry]) => {
    if (!entry) return;
    reportList.dataset.containerWidth = String(
      Math.round(entry.contentRect.width)
    );
  });
  sizeObserver.observe(reportList);
} else if (reportList) {
  window.addEventListener("resize", recordViewportWidth, {
    signal: lifetime.signal,
  });
  recordViewportWidth();
}

function stopObservingReport() {
  lifetime.abort();
  sizeObserver?.disconnect();
}
~~~

检测到 `ResizeObserver` 时，更新来自实际报表容器；退回 `window.resize` 时只知道视口变化，父容器单独改变大小不会触发该回退。示例中的 `stopObservingReport()` 应由移除该页面区域的一方调用。

页面区域被移除时，用 `AbortController`（中止控制器）的 `signal` 一次清除绑定到该 signal 的事件监听器；`ResizeObserver` 则调用 `disconnect()` 停止观察。文档就绪和页面加载完成时，`DOMContentLoaded` / `load` 的触发条件见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)。

### 把浏览器事件交给 React 时，交接什么？

若同一报表页由 React 管理，浏览器仍然派发 click；React 的 `onClick` 处理函数收到筛选意图 `oldest` 后，把它交给 state（状态）更新。浏览器这一侧的输入仍是点击事件和当前 DOM；交给应用的意图是“筛选变为 `oldest`”。React 章节从这个输入继续，讲状态快照、组件重算和 commit（提交）后需要的 DOM 变化。见[React 如何把用户操作变成更新后的界面？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)。React 管理的节点应由 React 状态描述；若另用 DOM API 直接改它们，下一次 React 提交可能覆盖这些修改。

React 的 JSX 事件使用 SyntheticEvent（合成事件），保留常用的 DOM 事件概念；`onClick` 默认冒泡，`onClickCapture` 对应捕获。`currentTarget` 在当前处理函数执行时指向该 JSX 监听器所在元素。React DOM 17 起不再池化事件；当前监听函数返回后，React 仍会把 `event.currentTarget` 清为 `null`。因此跨越 `await` 或延后回调前，先把 `event.currentTarget.dataset.sort` 读成普通字符串。这里的 `handleSort` 直接绑定到带筛选意图的按钮，例如 `<button data-sort="oldest" onClick={handleSort}>Oldest first</button>`；若把处理器绑定到工具栏，`currentTarget` 就是工具栏，而不是带 `data-sort` 的按钮：

~~~jsx
async function handleSort(event) {
  const intent = event.currentTarget.dataset.sort;
  await savePreference(intent);
  setSort(intent); // 使用已保存的字符串，不再读取 event.currentTarget
}
~~~

React DOM 的 `persist()` 不用于延长 `currentTarget` 的有效期；这里要保存的是 `intent`。React 17 也把委托根从 `document` 移到 React root container，但 React 事件对象中的 `currentTarget` 仍表示 JSX 监听元素。与原生 `focus`、`blur` 不冒泡不同，React 的 `onFocus`、`onBlur` 会沿 React 树传播。React Native 的事件行为有自己的边界。

**延伸：**[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)交代该页面的首帧和筛选入口；[每次 URL 变化都会加载新文档吗？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)展示同一点击如何更新历史地址和列表；[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)说明 click 处理器如何等待主线程并交接到渲染机会；[跨浏览上下文如何通信？](#53.%20%E5%90%8C%E4%B8%80%E6%8A%A5%E8%A1%A8%E5%9C%A8%E5%A4%9A%E4%B8%AA%E6%A0%87%E7%AD%BE%E9%A1%B5%E4%B8%AD%E6%80%8E%E6%A0%B7%E4%BA%A4%E6%8D%A2%E5%8F%98%E5%8C%96%EF%BC%9F)讲跨文档消息；[JavaScript 事件总线怎样处理重入？](#56.%20JavaScript%20%E4%BA%8B%E4%BB%B6%E6%80%BB%E7%BA%BF%E5%9C%A8%E7%9B%91%E5%90%AC%E5%99%A8%E4%B8%AD%E9%87%8D%E5%85%A5%E6%97%B6%E6%80%8E%E6%A0%B7%E4%BF%9D%E6%8C%81%E9%A1%BA%E5%BA%8F%EF%BC%9F)讨论应用层发布/订阅。

> [!info]- 来源
> - 查询、树节点与事件机制：[WHATWG DOM，Living Standard（2026-11-11 更新）](https://dom.spec.whatwg.org/) 的 [`querySelector()`](https://dom.spec.whatwg.org/#dom-parentnode-queryselector)、[`querySelectorAll()`](https://dom.spec.whatwg.org/#dom-parentnode-queryselectorall)、[节点复制算法](https://dom.spec.whatwg.org/#concept-node-clone)、[事件分发、invoke 与 inner invoke](https://dom.spec.whatwg.org/#concept-event-dispatch)。涵盖首个匹配、静态结果、cloneNode 复制范围、事件阶段、`target` / `currentTarget`、传播和取消。核对日期：2026-11-12。
> - 输入框默认值、dirty value flag 与表单 reset：[WHATWG HTML，input element](https://html.spec.whatwg.org/multipage/input.html#the-input-element)；表单控件及 fieldset 的禁用规则：[form control infrastructure](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#enabling-and-disabling-form-controls:-the-disabled-attribute) 与 [fieldset element](https://html.spec.whatwg.org/multipage/form-elements.html#the-fieldset-element)。包含 first-legend 例外。持续更新规范，核对日期：2026-11-12。
> - `innerText` 的读取和写入、`data-*` 与 `dataset`、HTML 属性：[WHATWG HTML，DOM](https://html.spec.whatwg.org/multipage/dom.html#the-innertext-and-outertext-properties)，§3.2.4、§3.2.6.6、§3.2.7；图片 `src` 与 `alt`：[The `img` element](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element)。持续更新规范，核对日期：2026-11-12。
> - `element.style` 读取行内声明、`getComputedStyle()` 读取解析后的样式：[CSS Object Model (CSSOM) Level 1](https://drafts.csswg.org/cssom/)，§7。CSS Working Group Editor’s Draft，核对日期：2026-11-12。
> - passive 默认值与 `preventDefault()` 的条件：[WHATWG DOM，addEventListener](https://dom.spec.whatwg.org/#dom-eventtarget-addeventlistener)。窗口尺寸、页面与元素滚动的目标：[CSSOM View](https://drafts.csswg.org/cssom-view/)，CSS Working Group Editor’s Draft，核对日期：2026-11-12。
> - pointer capture、取消和 `touch-action`：[Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/)，W3C Recommendation，2026-06-30，§§4.1、5.1、7；元素尺寸观察与 `disconnect()`：[Resize Observer](https://drafts.csswg.org/resize-observer/)，CSS Working Group Editor’s Draft。均核对日期：2026-11-12。
> - `key` 与修饰键 `shiftKey`：[UI Events](https://www.w3.org/TR/uievents/)，KeyboardEvent，W3C Working Draft，2026-02-21，核对日期：2026-11-12。`code`、`repeat` 和旧 `keypress` 不在本页示例中。
> - SVG 可点击区域按可见 fill/stroke 和 `pointer-events` 规则命中：[SVG 2，Pointer Events property](https://www.w3.org/TR/SVG2/interact.html#PointerEventsProperty)，W3C Candidate Recommendation Snapshot（2026-10-06），核对日期：2026-11-12。
> - 初始 viewport 未适配移动设备时，点击可能延迟至多 300 毫秒：[Chrome Performance Insights：Optimize viewport for mobile](https://developer.chrome.com/docs/performance/insights/viewport)，适用条件见文档，发布于 2025-10-08，核对日期：2026-11-12。
> - React DOM 事件对象、`currentTarget` 与 React DOM 不使用 `persist()`：[React event object](https://react.dev/reference/react-dom/components/common#react-event-object)；React 17 移除事件池并把委托根移入 root container：[React 17 release notes](https://legacy.reactjs.org/blog/2020/10/20/react-v17.html)。本文关于监听器返回后清空 `currentTarget` 的版本结论以 [React DOM v19.2.0 分发源码](https://github.com/facebook/react/blob/v19.2.0/packages/react-dom-bindings/src/events/DOMPluginEventSystem.js#L240-L252) 为准；React `onFocus`、`onBlur` 的传播说明见同一发布说明。核对日期：2026-11-12。
> - Navigator 的语言、平台和 userAgent 接口及隐私要求：[WHATWG HTML，Navigator object](https://html.spec.whatwg.org/multipage/system-state.html#the-navigator-object)。持续更新规范，核对日期：2026-11-12。
## 5. 浏览器 JavaScript 何时运行，画面何时更新？

案例背景：上一章的报表页已显示 `https://example.test/reports?sort=recent#summary`，`/reports.js` 也已注册“最早优先”按钮的 click 处理器。用户点击后，处理器同步把当前 URL 改为 `sort=oldest`、切换按钮的 `aria-pressed` 并把行重排为 April、May。这里追问：如果点击到达时该窗口事件循环正运行一段同步 JavaScript，处理器何时开始？这些同步改动何时有机会变成新的画面？[浏览器首帧与点击交接](#%E4%BB%8E%E9%A6%96%E5%B8%A7%E4%BA%A4%E6%8E%A5%E5%88%B0%E7%AD%9B%E9%80%89%E6%9B%B4%E6%96%B0)给出页面和操作，本章沿一次处理过程追踪调度边界。

### task source 怎样交出下一次工作？

HTML 的窗口事件循环协调事件、脚本、渲染和网络等工作；这是宿主调度模型，不对应所有浏览器固定的线程流水线。一个 task（任务）封装宿主安排的一段工作；task source（任务源）按工作类别分组，例如用户交互、定时器和更新渲染。事件循环的 task queue（任务队列）不是所有回调共用的单一先进先出队列：规范允许用户代理把不同任务源合并到一个或多个队列，并在有可运行任务的队列中选择下一项。它会保留同一任务源要求的顺序；不同队列之间由用户代理选择。

**图：task 完成与 callback 返回后的检查点分别回到哪里**

![用户输入、定时器与渲染机会怎样成为候选任务；task 边界检查点回到 task 选择，callback 检查点则恢复当前 task 的宿主步骤](../../frontend/runtime/resources/event-loop-task-selection.svg)

常见的页面处理路径里，事件循环选中的一个普通 task 会运行到任务步骤结束，期间同步 JavaScript 不会被另一个普通 task 抢占。因此，点击到达时如果当前同步脚本很长，或它后续排入的微任务一直新增，click handler 就只能等待。task 步骤结束后，事件循环执行 task 边界检查点；这次检查点排空后，事件循环才会选择下一项 task。若某次脚本或 Web IDL callback 的清理先让 JavaScript execution context stack（执行上下文栈）变空，也会先进入同一套排空算法；但这种检查点排空后会回到调用它的宿主步骤，让当前 task 继续执行，并不会直接跳到下一项 task。两种入口都会持续取出微任务，直到队列为空。

规范没有规定跨所有 task queue 的固定优先级。HTML 举例说明，用户代理可以将鼠标和键盘工作分到一队列，并在四次选择中三次优先处理该队列，同时仍让其他队列推进；这是展示实现自由度的例子，不是浏览器必须采用的公平策略。因而一次点击可以等当前工作结束，也可能在微任务排空后再等候 task 选择；规范不保证每个点击之后立刻更新画面。

渲染机会（rendering opportunity）由用户代理根据显示刷新、页面可见性、性能和其他条件判断。HTML 把机会判断和排入更新渲染 task 的步骤定义为与事件循环主步骤并行；同步 JavaScript 正在运行时，这个机会仍可能出现并把 task 排入队列。被延迟的是事件循环之后选择并执行更新渲染 task 的时刻，不是这一步机会判断本身。页面隐藏或当前没有渲染机会时，文档不会进入本轮更新；若用户代理认为更新没有可见效果且没有待运行的 rAF callback，也可以跳过文档更新，此外还有其他允许跳过的理由。更新渲染 task 仍要参与队列选择；若 timer 和渲染 task 都已可运行且属于同一队列，就先取该队列中较早的可运行 task；不同队列间如何选择由用户代理决定。

### 微任务的先后顺序与让出的边界

microtask（微任务）是当前 JavaScript 工作完成后、下一个普通 task 运行前处理的短小延续，例如已满足 Promise 上注册的 reaction（处理器）。ECMAScript 定义 Promise reaction job，HTML 宿主把它们接入事件循环的微任务队列。下面保留一个最小可追踪例子，并让一个微任务在执行时再排入另一个微任务：

~~~javascript
console.log("start");
setTimeout(() => console.log("timer task"), 0);
Promise.resolve().then(() => {
  console.log("Promise reaction");
  queueMicrotask(() => console.log("queued by reaction"));
});
queueMicrotask(() => console.log("queued microtask"));
console.log("end");
~~~

顺序是 `start`、`end`、`Promise reaction`、`queued microtask`、`queued by reaction`，随后计时器回调在其延迟门槛达到且被选中时运行。同步代码先入队 Promise reaction，再入队 `queueMicrotask()`；reaction 执行时，新微任务排到现有队列尾部，所以它在 `queued microtask` 之后运行。微任务检查点不会因为某个微任务返回就结束，而是把其间新增的微任务也排空。

`setTimeout(fn, 0)` 只安排一个之后可运行的 timer task，不会在当前同步段中途切走，也不保证它一定先于或后于一次渲染更新。类似地，`await Promise.resolve()` 会把续接安排为微任务，不会主动让浏览器先处理输入或绘制。长同步循环和不断追加微任务会阻止事件循环选择并执行更新渲染 task，因此可能错过预期呈现时机；HTML 定义的渲染机会判断与 task 排入仍可在并行步骤中发生。有界计算若要主动让出，应拆成后续 task、交给 Worker，或使用框架提供且目标环境支持的调度策略。

在报表页的 click handler 中，URL 与 DOM 的状态转换都在同步处理时完成：`history.pushState()` 新增同文档历史条目并更新当前文档 URL，脚本可立即从 `location` 读到 `sort=oldest`；它不会重取文档，也不会替页面排序。handler 随后分别把按钮状态从 `true/false` 改为 `false/true`，并把 DOM 行从 May、April 改为 April、May。handler 返回时 DOM 已是新顺序，但屏幕仍可能显示上一帧。下面先画出“状态 → handler → 新状态”，再沿该 listener 返回后的宿主步骤追踪观察用的 Promise、微任务、`requestAnimationFrame()` 和 timer；它们不是排序功能本身的依赖。两次本地重放分别用 CDP 模拟鼠标输入和同步 `.click()` 触发：模拟鼠标输入那次观察到渲染 task 先运行，脚本 `.click()` 那次观察到 timer 先运行。这只是两次运行记录，不能推出触发类型决定顺序，也不代表 task source 有固定优先级。

**图：一次点击中的状态转换、listener 检查点和后续 task 选择**

![物理输入的 click task 中，同一报表从旧状态经 listener A 到新状态；微任务排空后恢复当前事件分发，task 结束后再选择后续任务](../../frontend/runtime/resources/event-loop-click-trace.svg)

理解图里的 listener 交接要看两个规范调用点。DOM 的事件分发通过 Web IDL `call a user object's operation` 调用 `EventListener`；rAF 则由 HTML 用 Web IDL callback function 调用。两条 Web IDL 返回路径都会先执行 `clean up after running a callback`，再执行 HTML 的 `clean up after running script`。前一步清理 callback 宿主状态，本身不运行微任务；后一步从 JavaScript 执行上下文栈移除脚本，若栈此时为空才触发微任务检查点。因此，物理输入的 click task 中 listener A 返回时，微任务可在事件分发继续调用 listener B 前运行；排空后恢复的是当前事件分发，而非下一项 task。若 JavaScript 正在调用 `element.click()`，外层脚本仍在栈上，listener A 返回不会让栈变空；A、B 都会先返回，外层脚本结束后才运行检查点。无论 callback 中途是否触发过检查点，task 自身步骤结束后仍有 task 边界检查点；HTML 的防重入标志会阻止嵌套检查点重复排空同一队列。

### `requestAnimationFrame` 把写入对齐到渲染更新

`requestAnimationFrame(callback)` 把 callback 注册到文档的动画帧 callback 列表。它不是独立 task，也不是微任务；用户代理选中更新渲染 task 后，HTML 在执行这一轮的常规样式和布局更新之前运行列表中的动画帧 callbacks。若页面有可呈现的渲染机会且用户代理没有跳过更新，这能让动画写入和当前更新对齐。DOM 修改并不要求应用一定调用 rAF，普通 DOM 改动也可以在后续更新渲染中反映出来。

rAF callback 本身通过 Web IDL callback 调用。callback 返回后，Web IDL 先清理 callback 状态，再清理 script；如果执行上下文栈变空，后者就在同一个渲染 task 内运行微任务检查点。排空后控制返回当前更新渲染算法，继续运行后续 rAF callback，再进入常规样式和布局步骤；检查点不会把这次渲染 task 结束掉。rAF callback 内排入的 Promise reaction 因而能在该轮样式与布局步骤之前执行，但不会额外获得一轮输入或绘制机会。HTML 的更新渲染算法随后按需重算样式、布局和其他文档更新步骤。浏览器如何把更新结果继续交给绘制、合成和屏幕呈现，取决于引擎实现；见[一次 DOM 改动怎样进入布局与绘制？](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

rAF 的回调时刻受渲染机会与页面状态影响，不是固定的 `60 Hz` 定时器；隐藏页面或被节流时，回调可能延迟。它给出的时间戳适合计算动画经过时间，但 callback 中大量计算仍会拖慢当前渲染更新。读几何值还可能促使同步布局，不能假定把读写放进 rAF 就只做合成。

### `requestIdleCallback` 只安排可推迟的小块工作

`requestIdleCallback(callback, { timeout })` 让用户代理在它认为空闲时安排低优先级工作，并把剩余空闲时间的估计传给 `deadline.timeRemaining()`。空闲期何时开始、可有多长由用户代理决定；页面忙或隐藏时，回调可能很久都不运行。提供正数 `timeout` 后，若回调没有在 idle period 内运行，超过期限后，用户代理会安排超时 task；规范允许它再等待一段由实现决定的时间才入队，入队后仍要等该 task 被选中运行，`didTimeout` 只说明这个 callback 是因 timeout 才执行。`timeRemaining()` 是估计值，不是执行预算或抢占点。

~~~javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift()); // processNext 只处理一个有界项目
  }
  if (workQueue.length) requestIdleCallback(runIdleSlice, { timeout: 2000 });
}

requestIdleCallback(runIdleSlice, { timeout: 2000 });
~~~

这里的 `workQueue` 和 `processNext` 是应用自己的队列与工作函数。`requestIdleCallback()` 在目标浏览器中需做能力检测；不支持时可以退回普通 task 分片，但 `setTimeout()` 不能保证回调发生时浏览器正空闲。React 等框架的 scheduler 也建立在宿主机制之上，不是 HTML 规范统一规定的 task source。

Node.js 有另一套宿主边界：它按 libuv 阶段处理 I/O、定时器和 `setImmediate()`，并额外提供 `process.nextTick()` 队列；CommonJS 顶层和 ES module 顶层中，nextTick 与 Promise 微任务的相对顺序也可能不同。这里的渲染机会与 rAF 讨论针对浏览器窗口，不要把它改写成 Node 的固定阶段图；见 [Node.js 事件循环阶段与微任务队列如何交互？](../../engineering-foundations/backend/node-event-loop-and-microtasks.md)。

**延伸：**[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)说明解析期间的脚本调度；[DOM 事件如何传播，何时适合事件委托？](#4.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E6%80%8E%E6%A0%B7%E6%9F%A5%E8%AF%A2%E3%80%81%E6%9B%B4%E6%96%B0%20DOM%20%E5%B9%B6%E5%93%8D%E5%BA%94%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9F)说明 click 如何到达处理器；[JavaScript 异步](#40.%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E6%80%8E%E6%A0%B7%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%EF%BC%9F)解释 Promise 本身的语言行为；[如何测量并诊断网页性能？](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)帮助区分点击前等待、handler 执行和后续呈现延迟。

> [!info]- 来源
> - **任务源、task queue、task 结束检查点、task 选择与渲染机会。** [WHATWG HTML §8.1.7 Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)，Living Standard，核对日期：2026-11-11；重点对照 §8.1.7.1 Definitions、§8.1.7.2 Queuing tasks 和 [§8.1.7.3 Processing model](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model)。定义段说明 task source 如何映射到 task queue、不同来源可合并；processing model 规定从所选队列取最早的可运行 task、task 步骤结束后的微任务检查点，以及渲染机会如何在并行步骤中排入 rendering task source。规范的用户交互优先示例只是实现自由度示意，不是固定策略。
> - **DOM listener、callback 清理与空栈检查点。** [WHATWG DOM inner invoke](https://dom.spec.whatwg.org/#concept-event-listener-inner-invoke) 对事件 listener 执行 Web IDL 的 [§3.11 call a user object's operation](https://webidl.spec.whatwg.org/#call-a-user-objects-operation)；rAF callback 路径见 [§3.12 invoke a callback function](https://webidl.spec.whatwg.org/#invoke-a-callback-function)，Web IDL Living Standard 核对日期：2026-11-11。两条返回算法依次运行 `clean up after running a callback` 和 `clean up after running script`；前者不做 checkpoint，后者调用 [WHATWG HTML §8.1.4.4 clean up after running script](https://html.spec.whatwg.org/multipage/webappapis.html#clean-up-after-running-script)，在 JS 执行上下文栈变空时触发 [§8.1.7.3 perform a microtask checkpoint](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint)，Living Standard 核对日期：2026-11-11。
> - **History API 与当前文档 URL。** [WHATWG HTML §7.2.5 The `History` interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，Living Standard，核对日期：2026-11-11。`pushState()` 更新同一文档的 session history 与当前 URL，不会触发文档重取；列表排序是报表 handler 的另一项 DOM 操作。
> - **Promise reaction 与微任务队列。** [ECMAScript 2026 §27.2.1.8 TriggerPromiseReactions](https://tc39.es/ecma262/2026/#sec-triggerpromisereactions) 为 reaction 生成 job；[§9.5.5 HostEnqueuePromiseJob](https://tc39.es/ecma262/2026/#sec-hostenqueuepromisejob) 要求按调用顺序运行这些 Promise jobs。[WHATWG HTML §8.1.6.6.4 HostEnqueuePromiseJob](https://html.spec.whatwg.org/multipage/webappapis.html#hostenqueuepromisejob) 将其接入浏览器宿主队列；[§8.8 Microtask queuing](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#microtask-queuing) 规定 `queueMicrotask()` 使用同一事件循环的微任务队列，Living Standard，核对日期：2026-11-11。
> - **rAF 与更新渲染步骤。** [WHATWG HTML §8.12 run the animation frame callbacks](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#run-the-animation-frame-callbacks) 定义按序调用；[§8.1.7 update the rendering](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering) 将运行动画帧 callbacks 排在样式/布局更新之前，Living Standard，核对日期：2026-11-11。
> - **空闲回调。** [W3C `requestIdleCallback()` Working Draft，2025-05-21，§§2、4.1、4.3、5](https://www.w3.org/TR/requestidlecallback/) 定义用户代理决定的 idle period、deadline 与超时 callback；[WHATWG HTML §8.1.7.3 Processing model](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model) 说明浏览器窗口事件循环在无可运行 task 时才启动 idle period，Living Standard，核对日期：2026-11-11。
> - **Node 边界。** [Node.js v26.13.0 Event Loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) 说明 libuv 阶段；[Node.js v26.13.0 `process.nextTick()` 与 `queueMicrotask()`](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) 说明 nextTick 队列、CommonJS/ES module 排序差异和 Legacy 状态，核对日期：2026-11-11。
> - **本地重放。** 用 headless Chrome `157.0.8103.50` 经 CDP `Input.dispatchMouseEvent` 对本地按钮模拟一次鼠标输入，产生可信的 click 事件，观察到 `click A → promise microtask → queueMicrotask → microtask queued by promise → click B → rAF A → microtask from rAF A → rAF B → timer task`。另一次从同步脚本调用 `button.click()`，观察到 `click A → click B → outer end → promise microtask → queueMicrotask → microtask queued by promise → timer task → rAF A → microtask from rAF A → rAF B`。这两次本机运行观察到相反先后；它们不构成不同 task source 的固定优先级保证。另以文档中的同一语句块重放同步代码例，只在 `console.log` 外包了一层记录器，观察到 `start → end → Promise reaction → queued microtask → queued by reaction → timer task`。本地 CDP 模拟鼠标输入 trace 和代码示例的运行记录在本轮报告目录；同步 `.click()` 的对照记录来自独立复读。
## 6. React如何把一次用户操作变成界面更新？

**案例背景。** 沿用浏览器主线中的 `/reports?sort=recent#summary` 报表页，本章用 React 实现它的筛选控件和列表。`#summary` 是浏览器定位片段，不会发给服务端；服务端按 `sort=recent` 给出 May、April。现在用户点 **Oldest first**。React 把 `sort` 改为 `oldest` 后，会先用手头已有的两条记录在本地排成 April、May，再在提交后请求服务端确认。若很快又选回 **Most recent**，界面再次先排成 May、April；较早的请求不能把较新的选择误标成已确认。

以下示例按 React 19.3.0 与对应 React DOM 核验。本章从点击处理器接手，解释一次状态更新如何经过 `render`（渲染）和 `commit`（提交）改变 React 管理的 DOM（文档对象模型）。`useEffect`（副作用同步）在提交后协调需要跟随已提交状态的外部工作，例如网络请求。完整页面由路由把选择写入浏览器历史，并在 Back 时恢复；这里展示 React 内部轮次，省略 URL（统一资源定位符）与历史栈接线，细节见[筛选状态与前进后退](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。本章停在 React 已提交 DOM；后续是否需要样式计算、布局或绘制，由浏览器决定，接回[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)。

先看点击后没有再次切换选择的一轮；快速反选时，后文再展开旧响应的处理。

| 阶段 | 这一轮发生什么 |
| --- | --- |
| 点击处理器 | 用户选择 Oldest first；处理器排入 `sort=oldest` 与 `requestId=1`，当前处理器仍读到旧的 `sort=recent`。 |
| `render` | React 读取新状态，从上次成功的两条记录派生 April、May，并计算“等待请求 1”；这里不发网络请求。 |
| `commit` | React 更新选中按钮、行顺序和提示对应的 DOM。 |
| `useEffect` 建立 | 提交后，Effect 才调用 `fetchReports("oldest")`。 |
| 响应回调 | 成功或失败回调排入带 `requestId=1` 的结果；React 再 render、commit，显示确认，或单独报错并保留上次成功数据。 |

### 处理器读到的是本次界面的状态快照

`state`（状态）变量不会被 setter（状态更新函数）原地改写；调用 setter 不会改变当前处理器读到的 `state`。React 每次调用组件，都给它一份当前状态快照；事件处理器也是在某一次 `render` 时创建的。因此在本例的 `chooseSort` 中，若这轮的 `sort` 还是 `recent`，调用 `setSort("oldest")` 后，这个处理器里的 `sort` 仍然是 `recent`。本例的一次点击中，React 会在处理器返回后一起处理排序和请求编号这两个更新，再据此计算下一份界面。

例如本轮 `count` 为 `0` 时，同一处理器连续调用两次 `setCount(count + 1)`，两次都根据快照 `0` 排入 `1`，结果仍是 `1`。若要让每一步基于队列中前一步的结果，传入 updater（更新函数）。以下处理器定义在组件函数内部：

~~~tsx
const [count, setCount] = useState(0);

function addFromSnapshot() {
  setCount(count + 1);
  setCount(count + 1);
}

function addFromQueue() {
  setCount(value => value + 1);
  setCount(value => value + 1);
}
~~~

在 `count` 快照为 `0` 时单独调用 `addFromSnapshot`，结果是 `1`；单独调用 `addFromQueue`，React 依次应用两个 updater，结果是 `2`。本页的 `setRequestId(id => id + 1)` 也用 updater，让编号从待处理状态继续递增。

**用户动作直接触发的一次性工作放在事件处理器里；从 props（属性）和 state 可算出的值在 render 里计算；只有需要随着已提交界面同步外部系统的工作才放进 Effect。** 本例点击处理器记录新的排序意图，`sortReports` 在 render 中派生可见行，Effect 在 commit 后请求与这份选择相符的数据。把可见行再写进一份 state 并用 Effect 同步，会多出一次不必要的更新轮次。

下面的 TypeScript JSX（TSX）代码把 `fetchReports` 作为路由传入的数据层函数：它接收排序值，成功时返回已验证的 `Report[]`，失败时以拒绝的 Promise 表示。`initialReports` 常量是“路由已经取得并验证首屏服务端数据”的合成输入；组件从收到这份数据开始，不实现首屏读取。列表以每条报表稳定的 `key`（键）作为身份，排序不会更换报表身份。`periodStart` 用固定格式日期排序；`period` 只作 May、April 这样的显示标签，不按月份单词的字母顺序比较。两个排序按钮用 `aria-pressed` 暴露当前选择。初始数据由路由先给好，所以 `requestId=0` 时跳过请求。示例刻意只保留 React 状态和请求身份；真实 URL 历史接线在上面的浏览器章节。若需知道排序状态由哪些组件共同持有，见[如何在 React 中组合组件与复用行为？](#7.%20%E5%A6%82%E4%BD%95%E5%9C%A8%20React%20%E4%B8%AD%E7%BB%84%E5%90%88%E7%BB%84%E4%BB%B6%E4%B8%8E%E5%A4%8D%E7%94%A8%E8%A1%8C%E4%B8%BA%EF%BC%9F)。

> [!info]- 输入类型与首屏示意数据
>
> ~~~tsx
> import { useEffect, useState } from "react";
>
> type SortOrder = "recent" | "oldest";
> type Report = {
>   id: string;
>   period: string;
>   periodStart: string;
>   title: string;
> };
> type FetchReports = (sort: SortOrder) => Promise<Report[]>;
> type SuccessfulRequest = {
>   requestId: number;
>   sort: SortOrder;
>   reports: Report[];
> };
> type FailedRequest = {
>   requestId: number;
>   sort: SortOrder;
> };
>
> const initialReports: Report[] = [
>   {
>     id: "may",
>     period: "May",
>     periodStart: "2026-05-01",
>     title: "May summary"
>   },
>   {
>     id: "april",
>     period: "April",
>     periodStart: "2026-04-01",
>     title: "April summary"
>   }
> ];
>
> function sortReports(reports: Report[], sort: SortOrder): Report[] {
>   // periodStart 是固定格式 YYYY-MM-DD；复制后排序，不改写上游数据。
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
> ~~~

#### 点击怎样记录新的选择？

下面依次展开同一个 `ReportsPage` 组件；输入、状态、Effect、派生值、JSX、路由这六段按顺序拼接，组成完整示例。`sort` 保存当前选择，`requestId` 标识本次确认请求；`lastSuccess` 保存最近一次有效成功数据，`lastFailure` 单独记录失败。分开保存后，当前请求失败也能保留旧数据，并明确告诉读者它尚未被这次请求确认。

~~~tsx
function ReportsPage({
  initialSort,
  initialReports,
  fetchReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
  fetchReports: FetchReports;
}) {
  const [sort, setSort] = useState(initialSort);
  const [requestId, setRequestId] = useState(0);
  const [lastSuccess, setLastSuccess] = useState<SuccessfulRequest>({
    requestId: 0,
    sort: initialSort,
    reports: initialReports
  });
  const [lastFailure, setLastFailure] = useState<
    FailedRequest | null
  >(null);

  function chooseSort(nextSort: SortOrder) {
    if (nextSort === sort) return;
    setSort(nextSort);
    setRequestId(id => id + 1);
  }
~~~

处理器只排入新选择和新编号。此时还没有向服务端发请求，也没有直接挪动列表节点。React 接着根据新状态 render、commit，再执行相应 Effect。

#### 提交后，怎样识别这一轮请求？

这个 Effect 属于特定的一次已提交选择。它把当时的 `requestId` 和 `sort` 放进结果，同时用独立的 `ignore` 变量记录自己的生命周期。首屏 `requestId=0` 已有路由数据，直接跳过读取。

~~~tsx
  useEffect(() => {
    if (requestId === 0) return;

    let ignore = false;
    const currentRequestId = requestId;

    fetchReports(sort).then(
      reports => {
        if (!ignore) {
          setLastSuccess({
            requestId: currentRequestId,
            sort,
            reports
          });
        }
      },
      () => {
        if (!ignore) {
          setLastFailure({ requestId: currentRequestId, sort });
        }
      }
    );

    return () => {
      ignore = true;
    };
  }, [sort, requestId, fetchReports]);
~~~

`ignore` 在这次 Effect 被清理后阻止旧回调写状态。回调写入结果时附上的编号还承担另一项工作：即使旧回调抢在 cleanup 前运行，它也只能写入自己的编号，不能把后来的请求误标为已确认。稍后的时序表会分别跟踪这两种情况。

#### 状态怎样决定列表和提示？

每次 render 都从当前状态算出以下三个值。`visibleReports` 用最近一次成功数据配合当前排序；是否确认或失败，则必须同时匹配当前请求编号和排序。

~~~tsx
  const requestConfirmed =
    lastSuccess.requestId === requestId && lastSuccess.sort === sort;
  const requestFailed =
    lastFailure !== null &&
    lastFailure.requestId === requestId &&
    lastFailure.sort === sort;
  const visibleReports = sortReports(lastSuccess.reports, sort);
~~~

| 当前结果 | 界面提示 | 列表使用的数据 |
| --- | --- | --- |
| 匹配当前编号和排序的失败结果存在 | 通过 `role="alert"` 显示失败 | 最近成功数据，按当前选择排序 |
| 否则，成功结果匹配当前编号与排序 | 通过 `role="status"` 显示已确认 | 本次成功数据 |
| 其余情况 | 通过 `role="status"` 显示等待当前请求 | 最近成功数据，按当前选择排序 |

返回的 JSX 根据这些值描述界面：按钮点击调用 `chooseSort`，其 `aria-pressed` 跟随 `sort`；列表遍历 `visibleReports`，以 `report.id` 为 key。React 的 commit 再把这份描述落实到 DOM。

> [!info]- 组件的 JSX 返回部分（承接上面的 ReportsPage）
>
> ~~~tsx
>   return (
>     <section>
>       <div role="group" aria-label="报表排序">
>         <button
>           type="button"
>           aria-pressed={sort === "recent"}
>           onClick={() => chooseSort("recent")}
>         >
>           Most recent
>         </button>
>         <button
>           type="button"
>           aria-pressed={sort === "oldest"}
>           onClick={() => chooseSort("oldest")}
>         >
>           Oldest first
>         </button>
>       </div>
>
>       {requestFailed ? (
>         <p role="alert">
>           {"当前选择：" + sort + "；请求 #" + requestId +
>             " 失败。仍显示上次成功（" + lastSuccess.sort +
>             "）的数据，并按当前选择排序。"}
>         </p>
>       ) : requestConfirmed ? (
>         <p role="status">
>           {"服务端已确认当前选择：" + sort + "（请求 #" + requestId + "）。"}
>         </p>
>       ) : (
>         <p role="status">
>           {"当前选择：" + sort + "；等待请求 #" + requestId +
>             "。下方保留上次成功（" + lastSuccess.sort +
>             "）的数据，并按当前选择排序。"}
>         </p>
>       )}
>
>       <ul>
>         {visibleReports.map(report => (
>           <li key={report.id}>{report.period} — {report.title}</li>
>         ))}
>       </ul>
>     </section>
>   );
> }
> ~~~

路由传入初始排序、首屏数据和数据层函数。下面的外层组件只展示这些输入怎样交接，不实现 URL/history 或真实请求。

> [!info]- 路由如何传入本例输入
>
> ~~~tsx
> function ReportsRoute({
>   fetchReports
> }: {
>   fetchReports: FetchReports;
> }) {
>   return (
>     <ReportsPage
>       initialSort="recent"
>       initialReports={initialReports}
>       fetchReports={fetchReports}
>     />
>   );
> }
> ~~~

`initialSort` 和 `initialReports` 是首屏输入；`useState` 只在首次挂载时用它们初始化。后续 URL 变化不能只改这两个 prop 就期待状态自动重置。由于 `fetchReports` 在依赖中，同一数据域内应传入稳定的数据层函数；若每次 render 都新建函数，Effect 会把它当作依赖变化而重新请求。若 `fetchReports` 内部读取原始 JSON，也应先在数据边界验证形状，而不是只用 TypeScript 类型断言；见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。完整路由需要在用户选择筛选时用 `pushState` 新增历史项；若用 `replaceState` 覆盖当前项，Back 就无法返回之前的选择。路由还要在 `popstate` 到来时把 URL 中的排序交给状态所有者。若 Back 恢复的排序需要重新向服务端确认，即使排序值和上一次相同，路由也要为这次读取发出新请求身份；若能复用该历史项对应的有效数据，则不必为了编号而强制请求。React Router 与单页应用（SPA）/多页应用（MPA）的边界见[React 路由如何把 URL 映射到视图？](#62.%20React%20%E8%B7%AF%E7%94%B1%E6%80%8E%E6%A0%B7%E6%8A%8A%E5%9C%B0%E5%9D%80%E6%98%A0%E5%B0%84%E5%88%B0%E7%95%8C%E9%9D%A2%E5%B9%B6%E5%8A%A0%E8%BD%BD%E6%95%B0%E6%8D%AE%EF%BC%9F)。

请求身份只约束同一数据域内的确认结果，不负责隔离界面正在显示的数据。切换账户时，仅增加请求编号仍会让 `lastSuccess.reports` 中的旧账户行留在列表里，等待期间和失败时尤其明显。路由应在数据域变化时同时隔离或清空成功数据；一种直接做法是按账户 ID 重新挂载 `ReportsPage`，并传入该账户已取得的首屏数据。

**跟着 May 和 April 走一遍。** 初始 `requestId=0` 的路由输入是 May、April，首屏直接显示它们，不额外请求。点击 **Oldest first** 后，React 将 `sort=oldest` 与编号 `1` 排入更新；下一次 render 从上次成功的两条记录派生 April、May。commit 提交按钮、列表和等待提示；之后 Effect 才为 `oldest` 启动请求 `1`。排序操作由点击触发，纯排序在 render 执行，请求则由已提交选择的 Effect 发起。请求成功或失败时，回调只把带编号的结果排入状态；React 下一轮 render 和 commit 才更新确认提示或错误提示。

若请求 `1` 尚未结束时又点 **Most recent**，下一次 render 会把选择和请求身份计算为 `recent #2`，并从当前上次成功数据派生 May、April；commit 更新按钮、列表和等待 `#2` 的提示。这个 render 本身不会发请求。依赖改变的旧 Effect 会清理，然后新 Effect 才启动请求 `2`。旧请求 `1` 的响应回调可能在 cleanup 前或后运行，两个路径的生命周期和显示数据不同。这里比较的是回调实际运行的时刻；Promise 先完成，并不代表排队的回调已在 cleanup 前运行：

| 请求 1 回调相对 cleanup 的时机 | 响应回调 | 等待请求 2 时的列表与提示 |
| --- | --- | --- |
| cleanup 前运行 | `ignore` 仍为 `false`，成功回调可把响应写为 `lastSuccess`，但仍标记 `requestId=1`。 | 用这份刚到的成功数据按当前 `recent` 排序；确认条件仍不匹配 `#2`，所以界面继续等待请求 2。 |
| cleanup 后运行 | cleanup 已将 `ignore` 设为 `true`，回调不写入状态。 | 保留之前的 `lastSuccess`，按当前 `recent` 排序；界面继续等待请求 2。 |

若请求 `1` 的失败回调在 cleanup 前运行，它只记下编号 `1` 的失败，不改 `lastSuccess`，也不能把请求 `2` 标成失败；cleanup 后运行则直接被忽略。无论哪条路径，编号 `1` 都不能确认编号 `2`。请求身份决定哪个响应可以确认当前轮次；`lastSuccess` 决定等待或失败时屏幕拿哪份同一数据域的成功数据来显示。若当前请求失败，独立的 `role="alert"` 会报错，列表保留同一数据域最近成功的数据，并按当前选择排序；不会把旧数据说成服务端刚确认的结果。

cleanup 守卫是“Effect 已被 React 清理后不再采用它的结果”，不是取消网络请求的承诺。Back 若需重新向服务端确认同一排序，也由路由创建新的请求身份；若重用缓存数据，则由路由提供相应有效结果。生产应用要缓存、去重、取消、重试或协调多组件请求时，通常由路由数据层或查询库承担这些契约，见[React 如何维护服务端数据与乐观更新？](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。

### 渲染、协调与提交是不同工作

`render` 阶段调用组件，把当前 props、state 转成 JSX 元素描述。它是计算，不是直接改 DOM。并发特性可能让尚未提交的 render 暂停、重试或放弃；因此不能在 render 中发请求、写 URL、改现有对象，或手动改 React 管理的 DOM。**是否调用组件、是否产生 DOM 变化、浏览器是否绘制，是三个不同问题。**

reconciliation（协调）按树中的位置、元素类型和 key（键）对应前后两次描述。本例的 `sortReports` 每次按当前 `sort` 生成新数组；它不修改 `lastSuccess.reports`。May 和 April 的 `id` 在顺序改变时保持不变，`key`（键）取 `report.id`，让 React 把前后两棵列表中属于同一报表的行对应起来。key 只需在同一列表兄弟节点间稳定且唯一；用数组下标代替数据身份，排序后行内状态可能跟着位置走。

render 完成后才进入 `commit`（提交阶段），React 将必要的改动写到宿主树。一个 setter 不等于一次 DOM 修改：新旧界面若相同，React 可以不改 DOM；若排序改变，则更新所需的行位置和按钮属性。React 负责 DOM commit，浏览器按需在后续渲染机会处理样式、布局或绘制；任务排队和帧调度的细节见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)。浏览器帧与 React setter 不是一一对应关系。

React 会把同一批的多个状态更新一起处理，避免逐个更新都触发一次完整的 render/commit，这叫 batching（批量处理）。本例点击处理器同时排入 `sort` 与 `requestId`，React 不会先提交一个只改排序、又立刻提交一个只改编号的半成品。React 18 起，使用 `createRoot` 的应用也会自动批量处理 Promise、定时器和原生事件处理器中的更新；React 18 的旧 `ReactDOM.render` 根会保留旧的批处理范围，升级后切换根 API 才启用新行为。批量处理不会改写当前 handler 的快照，也不表示每个更新都会单独绘制一帧。

> [!example] JSX 描述界面，不是 HTML（超文本标记语言）字符串
> JSX 是描述元素的语法。构建工具可以把它转换成自动运行时的 `react/jsx-runtime` 调用，也可以转换成经典的 `React.createElement` 调用。转换方式不改变 state 快照、render 和 commit 的关系。

### Effect在提交后同步外部系统

`Effect` 适合做由“组件现在需要与外部系统保持一致”触发的工作，例如订阅、连接，或按已提交选择读取服务端数据。它不适合代替点击处理器执行只由那次点击触发的一次性动作，也不适合在两份 React state 之间搬运可直接算出的值。需要时 `useEffect` 在 commit 后运行；依赖改变时先用旧闭包执行 `cleanup`（清理），再用新值执行 `setup`（建立）；卸载时再执行最后一次清理。依赖应包含 setup 实际读取的响应式值，React 用 `Object.is` 比较它们。本例的 `sort`、`requestId` 与 `fetchReports` 都在依赖中。

React 不能保证 Effect 总在浏览器 paint（绘制）之后运行。与点击交互有关的 Effect 可能在 paint 前运行；其他更新通常会让浏览器先绘制。若任务本身需要测量或在绘制前调整 DOM，可评估 `useLayoutEffect`；本例发起数据请求，不依赖这个精确帧时机。Promise 失败由此处显式转为状态与错误提示；渲染期间抛出的异常属于错误边界处理范围。

根组件包在 `StrictMode`（严格模式）中时，开发环境首次挂载会额外执行一次 Effect 的 `setup → cleanup`，再执行正式 setup，用来检查清理能否撤销建立工作。不是生产环境每次都发两次请求。本例初次调用因 `requestId=0` 提前返回，既不启动请求也没有可调用的 cleanup；之后排序更新才会为请求建立清理函数。即便使用 ignore，网络请求本身也可能继续运行；它解决的是清理后旧闭包不能采用结果。

类组件的 `render()` 同样必须保持纯计算。维护旧类组件时，`componentDidMount` 和 `componentDidUpdate` 可在 DOM 提交后同步外部系统，`componentWillUnmount` 可清理连接；若要在 DOM 更新前读取布局快照，使用 `getSnapshotBeforeUpdate`。这些生命周期帮助定位阶段，但不与函数组件的 Effect 一一对应；React 仍支持 class components（类组件），但新组件通常使用函数组件。若一次排序确实让用户输入变慢，再看[如何让报表筛选在昂贵更新时保持响应？](#8.%20%E5%A6%82%E4%BD%95%E8%AE%A9%E6%8A%A5%E8%A1%A8%E7%AD%9B%E9%80%89%E5%9C%A8%E6%98%82%E8%B4%B5%E6%9B%B4%E6%96%B0%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F)；若是渲染抛出的异常需要恢复，则看[React 错误边界能恢复哪些失败？](#11.%20React%E9%94%99%E8%AF%AF%E8%BE%B9%E7%95%8C%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E5%A4%B1%E8%B4%A5%EF%BC%9F)。

> [!info]- 来源与版本核验（当前 React 文档 19.3；历史行为按 React 18 核验，日期 2026-11-12）
>
> - 状态快照、setter 请求下一次 render、处理器保留当前状态，以及函数 updater 在队列中逐个计算：[State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)、[`useState`](https://react.dev/reference/react/useState)，React 19.3 文档。
>
> - render/commit 分工、render 纯净及组件调用不必对应 DOM 改动：[Render and Commit](https://react.dev/learn/render-and-commit)、[Keeping Components Pure](https://react.dev/learn/keeping-components-pure)，React 19.3 文档。
>
> - 同级 key 与树位置怎样确定状态身份：[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 19.3 文档。
>
> - Effect 与事件的不同触发来源，依赖比较，改变依赖时先 cleanup 再 setup，Effect 相对 paint 的时序条件，以及 fetch 结果忽略模式：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)、[`useEffect`](https://react.dev/reference/react/useEffect)，React 19.3 文档；绘制前测量布局的 API：[`useLayoutEffect`](https://react.dev/reference/react/useLayoutEffect)，React 19.3 文档。
>
> - 根 StrictMode 的开发时额外 Effect setup/cleanup 检查：[StrictMode](https://react.dev/reference/react/StrictMode)，React 19.3 文档。
>
> - React 18 `createRoot` 与 legacy `ReactDOM.render` 的行为边界：[How to Upgrade to React 18 — Client Rendering APIs](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#updates-to-client-rendering-apis)；自动批处理：[React v18 — Automatic Batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)；并发 render 的中断、恢复、放弃与完整树提交：[React v18 — What Is Concurrent React?](https://react.dev/blog/2022/03/29/react-v18#what-is-concurrent-react)，React 团队发布文档。
>
> - `pushState` 添加历史项、`replaceState` 替换当前项：[HTML Standard — History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，核验日期 2026-11-12。
>
> - JSX 自动与经典转换：[Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform)，React 团队，2020-09-22。
>
> - 类组件 render、`getSnapshotBeforeUpdate` 与 mount/update/unmount lifecycle：[Component](https://react.dev/reference/react/Component)，React 19.3 文档。
>
> - URL 片段只供客户端定位且不会随 HTTP（超文本传输协议）请求发给服务端：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-12。
## 7. 如何在 React 中组合组件与复用行为？

**案例背景。** 报表页地址为 `/reports?sort=recent#summary`：查询参数决定排序，片段 `#summary` 只负责浏览器定位。路由把服务端给出的 May、April 两行与 `initialSort="recent"` 传入；初次提交选中 **Most recent**，显示 May 在 April 前。用户点 **Oldest first** 后，工具栏要选中旧序，列表要排成 April、May。因为同一份 `sort`（排序状态）同时决定两个界面，包含工具栏和列表的最近共同父组件负责持有它。父组件把状态和派生结果传给子组件，工具栏把用户意图通过回调交还状态所有者。远距离组件要共享行距偏好时，可选 Context；多个组件要复用同种外部监听行为时，可选自定义 Hook；父组件确实需要子组件的窄范围命令式动作时，才暴露 ref。

本章代码按 React 19.3 与 React DOM 19.3 核验。状态所有权示例省略 URL 与历史栈；若要让排序选择进入浏览器历史，可用 `pushState` 写入排序，并在 `popstate` 时把 Back/Forward 恢复的排序同步给同一状态所有者，见[浏览器主线](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。

> [!info]- 读旧版示例时需要识别的 API 差异
>
> React 19 的 Context 可直接用 `<Context value={...}>` 作为 Provider（提供者）；React 18 及更早版本需用 `<Context.Provider>`。React 19 函数组件也能把 `ref` 当作 prop，旧版本需 `forwardRef`。本章使用自动 JSX 转换，TSX 使用对应的 React 19 类型声明。下面使用当前写法；`use` 和 `useEffectEvent` 的调用规则在对应小节解释。

### 把状态放在共同使用者之上的最近一层

本例由调用方传入 `<ReportsPage reports={reports} initialSort="recent" />`。`reports` 只有 May、April 两行：May 的 `periodStart` 是 `2026-05-01`，April 的是 `2026-04-01`；本例日期固定为 `YYYY-MM-DD`。显示标签 `period` 不参与排序。`ReportsPage` 是工具栏和列表的最近共同祖先；它持有 `sort` 并在 render（渲染）中派生行顺序。

这一次数据流从父组件向下、用户意图再向上：

~~~mermaid
flowchart TD
    P["ReportsPage<br/>持有 sort<br/>派生有序 rows"] -->|"sort 与回调"| T["ReportToolbar<br/>显示选中按钮"]
    P -->|"有序 reports"| L["ReportList<br/>按顺序显示行"]
    T -->|"点击调用 onSortChange"| P
~~~

首次 render 中 `sort="recent"`，提交后 **Most recent** 被选中，列表为 May、April。排序按钮不直接改列表：工具栏接收 `sort` 和 `onSortChange`，其中回调就是父组件的 `setSort`；点击时调用它，安排下一轮 render。状态所有者从 `oldest` 派生新 `rows`，commit（提交）后工具栏与列表一起显示 Oldest first、April/May。`sortReports` 复制数组再排，不原地修改路由给的报表；`ReportList` 只显示派生结果，并用稳定的报表 ID 做 `key`（列表项标识）。当多个组件需要协调同一份状态时，通常由一处更新、其他组件读取，把 state 提到它们的最近共同祖先；提得更高会让职责和更新路径变宽，不会自动改善性能。

`initialSort` 只用于首次挂载时初始化 `useState`。完整路由若在 `popstate` 后拿到新排序，不能只换这个 prop 就期待组件状态自动重置；应让路由直接拥有排序状态并把它作为受控 prop 传入，或显式更新/重新挂载状态所有者。例如，只把同一实例的 `initialSort` prop 改成 `oldest`，按钮和列表仍保持 recent、May/April；调用 `setSort("oldest")` 才会安排状态更新，提交后显示 oldest、April/May。当前片段只展示组件通信，不实现 URL/history。

props（属性）适合父子层级清楚的数据向下传和 callback prop（回调属性）向上交互。若两个组件没有共享状态，贸然把 state 上移只会扩大维护范围。跨较深子树读取主题、地区或行距偏好时，可考虑 Context（上下文）；多处功能需共享并统一更新策略的客户端状态，可再考虑 store（共享状态容器），如 Redux；服务端拥有的报表记录仍归查询层，不因放进 Context 就获得缓存、请求身份或取消语义。Redux 的 action（动作）、reducer（归约器）、selector（选择器）和异步工作流见[Redux 如何组织共享界面状态与异步工作？](#60.%20Redux%20%E5%A6%82%E4%BD%95%E7%BB%84%E7%BB%87%E5%85%B1%E4%BA%AB%E7%95%8C%E9%9D%A2%E7%8A%B6%E6%80%81%E4%B8%8E%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!example]- 完整示例：排序状态、按钮与报表列表
>
> ~~~tsx
> import { useState } from "react";
>
> type SortOrder = "recent" | "oldest";
> type Report = {
>   id: string;
>   period: string;
>   periodStart: string;
>   title: string;
> };
>
> function sortReports(reports: Report[], sort: SortOrder): Report[] {
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
>
> export function ReportsPage({
>   reports,
>   initialSort
> }: {
>   reports: Report[];
>   initialSort: SortOrder;
> }) {
>   const [sort, setSort] = useState(initialSort);
>   const rows = sortReports(reports, sort);
>
>   return (
>     <main>
>       <ReportToolbar sort={sort} onSortChange={setSort} />
>       <ReportList reports={rows} />
>     </main>
>   );
> }
>
> function ReportToolbar({
>   sort,
>   onSortChange
> }: {
>   sort: SortOrder;
>   onSortChange: (sort: SortOrder) => void;
> }) {
>   return (
>     <div role="group" aria-label="报表排序">
>       <button
>         type="button"
>         aria-pressed={sort === "recent"}
>         onClick={() => onSortChange("recent")}
>       >
>         Most recent
>       </button>
>       <button
>         type="button"
>         aria-pressed={sort === "oldest"}
>         onClick={() => onSortChange("oldest")}
>       >
>         Oldest first
>       </button>
>     </div>
>   );
> }
>
> function ReportList({ reports }: { reports: Report[] }) {
>   return (
>     <ul>
>       {reports.map(report => (
>         <li key={report.id}>
>           {report.period} — {report.title}
>         </li>
>       ))}
>     </ul>
>   );
> }
>
> const reports: Report[] = [
>   {
>     id: "may",
>     period: "May",
>     periodStart: "2026-05-01",
>     title: "May report"
>   },
>   {
>     id: "april",
>     period: "April",
>     periodStart: "2026-04-01",
>     title: "April report"
>   }
> ];
>
> export function ReportsDemo() {
>   return <ReportsPage reports={reports} initialSort="recent" />;
> }
> ~~~

### 用Context传递远距离视图偏好

`ReportsView` 把视图内容作为 `children`（子节点）交给 `ReportViewProvider`；Provider 决定把这些内容放进 Context 子树。中间的 `ReportPanel` 只负责把收到的 children 放在 `<section>` 中，不用接收或转发 `density`。因此行距消费者即使隔着普通布局组件，仍能读到最近的 Provider。

下面的框表示组件包含关系。蓝色外框内的两个消费者读取同一份 `density`，中间布局组件只转交 `children`，不必转交行距值：

![Provider持有行距状态，布局组件内的两个消费者读取同一Context](../../frontend/frameworks/resources/report-context-ownership.svg)

`ReportsView` 调用 Provider 时，把 `<ReportPanel>` 作为 `children` 交给它；`ReportPanel` 再把控制按钮和列表放入自己的 `<section>`。调用方提供内容，组件决定插入位置，这就是 children 组合。`useContext` 向上查找这个 Context 最近的 Provider；子树里若再嵌一个同类型 Provider，只有它下面的消费者改读内层值。Context 对象本身不保存状态；这里真正持有 `density` 的是 Provider 中的 `useState`。初始 `density="comfortable"`：按钮写“切换紧凑行距”，列表 `lineHeight=1.8`。点击调用 `setDensity("compact")` 后，Provider 提供的新 value 让两个消费者更新：按钮变为“恢复舒适行距”，列表 `lineHeight=1.2`。若消费者上方没有该 Context 的 Provider，`useReportView` 会读到默认 `null` 并报错，明确要求调用方补齐 Provider。

此例每次 Provider render 都新建 `{ density, setDensity }` 对象，因此 value 引用也改变。React 用 `Object.is` 比较新旧 `value`；即使两个对象字段完全相同，只要引用不同，Context 消费者就会更新。点击行距按钮时 `density` 确实变化，两个消费者需要新值。若父组件因其他状态或 `reports` 更新而重新 render，即使 `density` 没变，Provider 仍会创建新对象并使 Context 消费者更新；即使消费者包在 `memo`（按 props 浅比较跳过子组件渲染的优化）中，也挡不住 Context 值变化。确认这造成可见成本后，再考虑稳定 value 或拆分 Context。TypeScript 中为 Context 值和消费者建立类型边界的旧例仍见[归档中的旧 TypeScript Context 与自定义 Hook 示例](../../archive/front-end/0-1_Learning_Notes/react_typescript/typed-hooks-and-context.md)。Context 不会改变报表记录的服务端所有权，查询身份、新鲜度、取消与变更协调仍由[服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)负责。

> [!example]- 完整示例：Provider、children 与两个消费者
>
> ~~~jsx
> import { createContext, useContext, useState } from "react";
>
> const ReportViewContext = createContext(null);
>
> function ReportViewProvider({ children }) {
>   const [density, setDensity] = useState("comfortable");
>
>   return (
>     <ReportViewContext value={{ density, setDensity }}>
>       {children}
>     </ReportViewContext>
>   );
> }
>
> function ReportPanel({ children }) {
>   return <section>{children}</section>;
> }
>
> function useReportView() {
>   const value = useContext(ReportViewContext);
>   if (value === null) {
>     throw new Error("useReportView 必须在 ReportViewProvider 内调用");
>   }
>   return value;
> }
>
> function DensityControl() {
>   const { density, setDensity } = useReportView();
>   const nextDensity = density === "compact" ? "comfortable" : "compact";
>
>   return (
>     <button type="button" onClick={() => setDensity(nextDensity)}>
>       {density === "compact" ? "恢复舒适行距" : "切换紧凑行距"}
>     </button>
>   );
> }
>
> function ReportRows({ reports }) {
>   const { density } = useReportView();
>   return (
>     <ul style={{ lineHeight: density === "compact" ? 1.2 : 1.8 }}>
>       {reports.map(report => (
>         <li key={report.id}>{report.title}</li>
>       ))}
>     </ul>
>   );
> }
>
> export function ReportsView({ reports }) {
>   return (
>     <ReportViewProvider>
>       <ReportPanel>
>         <DensityControl />
>         <ReportRows reports={reports} />
>       </ReportPanel>
>     </ReportViewProvider>
>   );
> }
> ~~~

### 用自定义Hook复用状态行为

自定义 Hook 复用的是一段 Hook 行为，不会让不同调用自动共用 state。下面每个 `useWindowSize()` 调用都创建自己的 size 状态和 `resize` 监听器；多个组件可以用同样方式订阅窗口尺寸，各自独立更新。

~~~jsx
import { useEffect, useState } from "react";

export function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    function update() {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    }

    window.addEventListener("resize", update);
    update();
    return () => window.removeEventListener("resize", update);
  }, []);

  return size;
}
~~~

`useEffect`（用于提交后同步外部系统的 Hook）在首次 commit（提交）后才运行，所以首次 render（渲染）暂时返回 `0 × 0`；随后 Effect 读取浏览器尺寸并更新。服务端也不会运行这个 Effect，服务端渲染与客户端首轮 hydration（水合）都会看到相同占位值。若两个组件都调用这个 Hook，在 `700×900` 窗口下它们会各自从占位值更新到 `700×900`；窗口变为 `720×900` 后，各自的监听器再把自己的 state 更新到新尺寸。相同输出是因为两次都读取同一个 `window`，不表示它们共用一份 state。卸载时每次调用都移除自己建立的监听器。若有很多消费者需要共享同一个外部窗口 store，应明确订阅同一 store（可用 React 的 [`useSyncExternalStore`](https://react.dev/reference/react/useSyncExternalStore)），而不是误以为每次调用同一自定义 Hook 就共享状态。

大多数 Hook 必须在组件或其他 Hook 顶层按固定顺序调用。React 19 的 `use` API 是特殊例外：它可以在条件和循环里读 Promise 或 Context，但仍须处于组件或 Hook 中，而且不能放进 `try/catch`；`useContext` 等普通 Hook 仍遵守固定顺序。

React 19.2 的 `useEffectEvent` 用于 Effect 里的 Effect Event（效果事件）逻辑：它在调用时读取最新提交的 props/state，但不因此让连接等 Effect 重新建立。它是一个 Hook，可在组件或自定义 Hook 顶层创建；自定义 Hook 可接收普通 callback 并用 `useEffectEvent(callback)` 包装，再由该 Hook 自己的 Effect 调用。Effect Event 要留在定义它的组件或 Hook 内，只能由本地 Effect 或另一个 Effect Event 调用；不能传给子组件、拿来当普通点击回调，也不能用它隐藏本来应该声明的 Effect 依赖。Effect Event 的函数身份每次 render 都会变化，不放进依赖数组。Effect 生命周期见[React 更新轮次](#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)。

### ref用于窄范围的命令式能力

界面需要随值变化时用 state；ref 可持有不驱动界面的可变值，也可引用已提交的 DOM。下面父工具栏只调用子组件公开的 `focus()`，输入节点始终由 `ReportSearchInput` 自己持有。

~~~tsx
import { useImperativeHandle, useRef, type Ref } from "react";

type SearchHandle = {
  focus(): void;
};

function ReportSearchInput({ ref }: { ref: Ref<SearchHandle> }) {
  const inputRef = useRef<HTMLInputElement>(null);
  useImperativeHandle(
    ref,
    () => ({
      focus() {
        inputRef.current?.focus();
      }
    }),
    []
  );
  return <input ref={inputRef} aria-label="搜索报表" />;
}

export function ReportFocusControl() {
  const searchRef = useRef<SearchHandle>(null);
  return (
    <>
      <ReportSearchInput ref={searchRef} />
      <button type="button" onClick={() => searchRef.current?.focus()}>
        聚焦搜索
      </button>
    </>
  );
}
~~~

React 19 的函数组件可把 `ref`（引用）当作 prop 接收；React 18 及更早版本要用 `forwardRef` 转发。若父组件只需要 `focus()`，`useImperativeHandle` 暴露这个有限动作即可，不把内部节点和实现一起交出去。通过这种 API，调用者只依赖子组件承诺的行为。

### 组合组件与旧式逻辑复用接口

`children`（子节点）组合让调用方提供内容，由接收组件决定把它插在哪里；前面的 `ReportPanel` 接收按钮和列表的 JSX，再把它们放进 `<section>`。render prop（渲染属性）是可由列表提供的扩展接口：如果 `ReportList` 接收 `renderRow` prop，调用方可传 `renderRow={report => <strong>{report.title}</strong>}`，列表对每条报表调用这个函数，并把返回的 JSX 放进对应行；当前 `ReportList` 只接收 `reports`，没有实现这个扩展 prop。higher-order component（高阶组件，HOC）包装组件并返回新组件。自定义 Hook 通常更适合复用 Hook 状态逻辑，但旧库的 render prop 或 HOC 也可能是稳定且清楚的 API，不必只为“改成 Hook”而重写。

条件分支也是组合的一部分：二选一用三元表达式，只在条件为真时渲染用逻辑 AND，能早退时用 `if`。在 `ReportsPage` 里，`ReportList` 必须收到 `reports`；错误写法 `{rows.length && <ReportList reports={rows} />}` 在 `rows` 为空时得到数字 `0`，React 会把它渲染出来。改成 `{rows.length > 0 && <ReportList reports={rows} />}` 时，空数组得到布尔值 `false`，不会多出数字。

这些模式解决状态归属和行为复用。若一次交互的 React render 成本已测出，再看[如何测量并减少不必要的 React 工作？](#14.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)；本章不把 memoization（记忆化）当作组件组合规则。

> [!info]- 来源与版本核验（React 19.3；核验日期 2026-11-12）
>
> - props 传递、调用方提供 JSX children、共同使用者的 state 归属、Context 数据下传：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component)、[Passing JSX as children](https://react.dev/learn/passing-props-to-a-component#passing-jsx-as-children)、[Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)、[useState](https://react.dev/reference/react/useState#returns)、[Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)，React 19.3 文档。
> - Context 的默认值、最近 Provider、value 变化触发消费者更新、React 19 新 Provider 语法与旧 `.Provider`：[createContext](https://react.dev/reference/react/createContext)、[useContext](https://react.dev/reference/react/useContext)，React 19.3 文档。
> - 自定义 Hook 复用行为与调用限制：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)、[Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)；React 19 的 `use` 可在条件/循环中读资源，但不能在 `try/catch` 中：[use](https://react.dev/reference/react/use)。
> - React 19.2 的 `useEffectEvent` 最新提交值、组件与自定义 Hook 中的定义/调用范围、依赖与身份限制：[useEffectEvent](https://react.dev/reference/react/useEffectEvent)、[Caveats](https://react.dev/reference/react/useEffectEvent#caveats)、[Using Effect Events in custom Hooks](https://react.dev/reference/react/useEffectEvent#using-effect-events-in-custom-hooks)、[React 19.2](https://react.dev/blog/2025/10/01/react-19-2)，React 官方文档。
> - React 19 的自动 JSX 转换要求及对应类型声明：[React 19 Upgrade Guide — New JSX Transform is now required](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#new-jsx-transform-is-now-required)。
> - ref 与命令式 handle；React 19 可直接收 ref prop，旧版需 `forwardRef`：[useRef](https://react.dev/reference/react/useRef)、[useImperativeHandle](https://react.dev/reference/react/useImperativeHandle)、[forwardRef](https://react.dev/reference/react/forwardRef)，React 19.3 文档。
> - 多处读取同一外部 store 的订阅 API：[useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore)，React 19.3 文档。
> - 逻辑 AND 条件渲染：[Conditional Rendering](https://react.dev/learn/conditional-rendering#logical-and-operator)，React 19.3 文档。
> - render prop 与 higher-order component 的旧式复用接口：[Render Props](https://legacy.reactjs.org/docs/render-props.html)、[Higher-Order Components](https://legacy.reactjs.org/docs/higher-order-components.html)，React 官方旧版文档；用于解释仍存在于库 API 中的接口。
> - toggle button 的 `aria-pressed`：[WAI-ARIA APG — Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)，W3C WAI 官方模式，核验日期 2026-11-12。
> - 当前 React 文档版本：[Versions](https://react.dev/versions)，React 19.3，核验日期 2026-11-12。
## 8. 如何让报表筛选在昂贵更新时保持响应？

**案例背景。** 报表页已经收到 May、April 两条数据，当前列表可按日期排序。用户在搜索框输入标题时，输入框应立即显示新字符；如果报表结果很多，列表可以稍后跟上。用户点击“查看摘要”时，也希望保留当前列表，等摘要代码准备好再切换。下面分别跟踪输入筛选和摘要切换，区分紧急更新、可延后的 render（渲染）、commit（提交）、Transition（过渡更新）和 Suspense（挂起边界）。这些 API 调整 React 的工作优先级，不会把 JavaScript 移到另一个线程，也不设固定毫秒延迟。

以下行为按 React 19.3 与 React DOM 19.3 核验。先看同一次输入如何产生两轮更新，再看等待摘要代码时如何保留当前界面。状态快照见[React 更新轮次](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)，服务端查询仍由[服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)管理。本章省略 URL 与 Back 接线，见[浏览器历史栈机制](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。

> [!info]- 挂载方式与版本前提
>
> 本例从空挂载点创建客户端界面，使用 `createRoot`。若服务端已经输出 React HTML，应以首轮内容匹配的 `hydrateRoot` 接管。文本或 DOM 结构不匹配可能使 hydration（客户端接管）失败并转为客户端渲染：错误位于 Suspense 边界内时可从最近边界重建，没有边界时会重建整个根。属性值不匹配的处理不同，React 不保证修补属性。
>
> `useDeferredValue` 和 `useTransition` 自 React 18 提供；React 19 支持异步 Transition Action（动作），跨 `await` 的状态更新限制在后文说明。若查旧资料，React 18 的 `ReactDOM.render` 使用接近 React 17 的旧根兼容模式；React 19 已移除此 API，当前入口使用 `createRoot`。
### 输入保持即时，结果视图可以延后

这里把搜索框的 `query` 作为紧急状态，把 `useDeferredValue` 返回的 `deferredQuery` 交给结果组件 `ReportResults`。用 `isStale = query !== deferredQuery` 判断列表是否尚未跟上输入，并据此显示等待提示。列表子组件用 `memo`（记忆化组件）包住；示例的 `reports` 数组来自已经取得的一份数据集，在输入变化期间保持同一引用且不原地改写。否则子组件收到新数组时仍会重渲染，不能用这个例子说明如何跳过旧查询的列表工作。

假设初始搜索词为空，列表显示 May、April。用户一次把搜索框填成 `apr` 时，`onChange` 处理器排入新的 `query` 更新；setter 不会改写本轮仍读到的状态快照。下一轮紧急 render 得到新 `query`，但 `deferredQuery` 仍可能为空。下面按 React 实际提交顺序展开。

render（渲染）按状态快照计算下一份界面。React 采用计算结果时，commit（提交）才把必要的 DOM 改动应用到页面。下面把事件处理器安排更新与之后的提交分开：

| 次序 | 本例发生什么 |
| --- | --- |
| 1. 输入事件 | 用户一次把搜索框填成 `apr`；处理器排入 `query` 更新。 |
| 2. 紧急 render / commit | render 得到 `query="apr"`、`deferredQuery=""`、`isStale=true`。提交后输入显示 `apr`、等待提示出现；列表 DOM 仍是 May、April，`ReportResults` 的 props 未变，可跳过这轮工作。 |
| 3. 后台 render | React 尝试用 `deferredQuery="apr"` 计算新列表；此时旧列表仍是已提交的画面。中途有更紧急更新时，可放弃这轮并按最新输入重试。 |
| 4. 后台 commit | 若 `apr` 这一轮被采用，新结果提交为 April，`isStale` 转为 `false`，等待提示消失。 |

表格说的是 React 提交次序，不承诺每一步都单独显示成浏览器绘制的一帧；后台工作若很快完成，用户可能只看见最终列表。

`memo` 只在子组件 props（属性）没变时提供跳过重渲染的机会；它是性能优化，不是输出正确性的保证。如果输入时父组件同时换了 `reports` 数组，默认浅比较会发现数组引用不同，子组件仍会渲染。若项目已配置 React Compiler（React 编译器）并检查过该组件的编译结果，编译器也可能自动建立相同的跳过边界；本例显式使用 `memo`，让代码即使未配置编译器也能呈现这个因果关系。

本例直接更新 `query`，所以输入事件是紧急更新。如果把更新 `query` 本身包进 Transition，`useDeferredValue` 会直接返回新词，不会再额外创建一轮 deferred render；要保留受控输入的即时响应，应让输入状态保持紧急。

`useDeferredValue` 不承诺等待某个固定时长；React 会在紧急更新后开始后台 render，并可在后续输入到来时中断、重启。它也不等于 debounce（防抖），不会减少网络请求数。上面的过滤发生在 render 中，但 `reports.filter(...)` 是一段同步 JavaScript，运行到结束前主线程不能插入新输入事件，React 也不能抢占这段函数。如果全量过滤本身已经是长任务，应先缩小数据、优化算法、拆成能在小块之间让出主线程的工作，或放入 Web Worker（网页工作线程）；若成本来自许多结果组件的 render，跳过旧查询子树才会有帮助。远端搜索频率仍应由明确的请求策略或查询层控制。

> [!example]- 完整示例：输入状态与结果列表
>
> ~~~tsx
> import { memo, useDeferredValue, useState } from "react";
>
> type FilterReport = {
>   id: string;
>   title: string;
> };
>
> export function ReportFilter({ reports }: { reports: FilterReport[] }) {
>   const [query, setQuery] = useState("");
>   const deferredQuery = useDeferredValue(query);
>   const isStale = query !== deferredQuery;
>
>   return (
>     <section>
>       <label>
>         搜索报表
>         <input
>           value={query}
>           onChange={event => setQuery(event.currentTarget.value)}
>         />
>       </label>
>       {isStale && (
>         <p role="status">列表仍对应旧的搜索词，正在更新。</p>
>       )}
>       <div aria-busy={isStale}>
>         <ReportResults reports={reports} query={deferredQuery} />
>       </div>
>     </section>
>   );
> }
>
> const ReportResults = memo(function ReportResults({
>   reports,
>   query
> }: {
>   reports: FilterReport[];
>   query: string;
> }) {
>   const visibleReports = reports.filter(report =>
>     report.title.toLowerCase().includes(query.toLowerCase())
>   );
>
>   return (
>     <ul>
>       {visibleReports.map(report => (
>         <li key={report.id}>{report.title}</li>
>       ))}
>     </ul>
>   );
> });
> ~~~

### 用Transition标记非紧急的界面切换

第二个问题是用户点击“查看摘要”后，摘要模块可能尚未下载。这个独立例子从清空搜索框、已选 oldest 的列表开始，行顺序为 April、May；下面只处理从列表切换到摘要。`useTransition` 把 `view` 更新标为非紧急 Transition，并提供 `isPending`（仍在等待）反馈。调用 `startTransition` 时，包住的函数会立即运行；它标记其中的 state 更新，而不是延迟执行事件处理器。Transition 不能用来控制受控文本输入；这里用它处理的是一整块摘要视图。

本例首次挂载时 `view="rows"`，先显示 April、May；摘要模块即使尚未下载，也不会让当前列表挂起。点击把 `view` 设为 `"summary"` 后，React 才需要那个模块来呈现摘要。假定此时模块仍未就绪，同一个 Suspense 边界会因已有内容和更新方式不同而呈现不同结果；模块准备好后，摘要显示“当前共有 2 条报表”：

| 开始等待时的状态 | 等待期间显示什么 | 模块准备好后 |
| --- | --- | --- |
| 已显示列表，点击由 Transition 更新 `view` | 保留 April、May；`isPending` 提示正在准备摘要 | 重试 render，提交摘要 |
| 对照：若把同次点击改为紧急更新 `view` | 用 fallback（备用界面）替换列表 | 重试 render，提交摘要 |
| 首次直接挂载摘要，还没有已提交内容 | 显示 fallback，没有旧内容可保留 | 首次提交摘要 |

这解释了为什么“资源还没加载完”不必等于“把已有页面换成加载提示”。快速加载时，用户也可能看不到等待提示。

Suspense 可以等待多种资源，但等待资源不代表每次都会显示 fallback；当前边界是否已有内容以及更新优先级会影响呈现。这里用 `lazy` 加载组件代码。读取数据时，可用 React 19 的 `use(promise)` 读取跨重渲染复用的 Promise，例如由服务端组件传来的 Promise，也可使用集成 Suspense 的数据框架。传给 `use` 的数据 Promise 必须能跨重渲染复用，不能每次 render 都新建；带 `precedence` 的样式表也能让边界等待样式表加载，但不适用 Promise 身份缓存条件。普通 `fetch` 放在 `useEffect` 或事件处理器里，不会自动触发边界；这类工作需要自己的加载状态。模块加载或数据读取失败时，最近的错误边界/查询错误状态负责显示错误。同一个 `lazy` 声明会缓存 loader Promise，重置错误边界不会再次调用 loader；产品可提供刷新页面的恢复入口，让新页面重新尝试加载模块，前提是发布资源或网络已经恢复。

若使用 TanStack Query v5（最低要求 React 18），数据挂起读取采用专用 `useSuspenseQuery`、`useSuspenseInfiniteQuery` 等 Hook（钩子）；不要照搬 v4 的 `useQuery({ suspense: true })` 选项，v5 移除了旧的布尔开关。普通 `useQuery` 的 pending 状态不会自行让 React Suspense 边界显示 fallback。`useSuspenseQuery` 的初次加载错误需要错误边界；后台刷新失败可以保留已有缓存，重试还需要错误边界重置或查询层的恢复机制。

> [!example]- 完整示例：切换摘要与懒加载模块
>
> ~~~tsx
> // ReportWorkspace.tsx
> import { lazy, Suspense, useState, useTransition } from "react";
>
> type WorkspaceReport = {
>   id: string;
>   title: string;
> };
>
> const ReportSummary = lazy(() => import("./ReportSummary.js"));
>
> export function ReportWorkspace({ reports }: { reports: WorkspaceReport[] }) {
>   const [view, setView] = useState<"rows" | "summary">("rows");
>   const [isPending, startTransition] = useTransition();
>
>   function openSummary() {
>     startTransition(() => {
>       setView("summary");
>     });
>   }
>
>   return (
>     <main>
>       <button type="button" onClick={openSummary}>
>         查看摘要
>       </button>
>       {isPending && <span role="status">正在准备摘要视图…</span>}
>       <Suspense fallback={<p>正在加载摘要模块…</p>}>
>         {view === "summary" ? (
>           <ReportSummary reports={reports} />
>         ) : (
>           <ul>
>             {reports.map(report => (
>               <li key={report.id}>{report.title}</li>
>             ))}
>           </ul>
>         )}
>       </Suspense>
>     </main>
>   );
> }
> ~~~
>
> `ReportSummary.tsx` 默认导出接收同一组报表的组件：
>
> ~~~tsx
> // ReportSummary.tsx
> type SummaryReport = {
>   id: string;
>   title: string;
> };
>
> export default function ReportSummary({
>   reports
> }: {
>   reports: SummaryReport[];
> }) {
>   return (
>     <section>
>       <h2>报表摘要</h2>
>       <p>当前共有 {reports.length} 条报表。</p>
>     </section>
>   );
> }
> ~~~

Transition 表示渲染优先级，不会把模块请求移到后台线程，也不自动保证自定义异步请求的完成顺序。React 19 的 `useTransition` 可以接收异步 Action（动作），并在 Action 等待期间维持 pending 状态。单次刷新可以在 `startTransition` 中等待 `fetchSummary()`：等待期间保留当前 `summary` 文本，显示正在刷新提示。成功后，再用一次 `startTransition` 包住状态更新，用返回文本更新 `summary` 并清除 `error`，继续把结果渲染标为非紧急；失败时只更新 `error`，保留已有摘要。


为避免这个单按钮入口重复发请求，下面的完整示例在 pending 时禁用按钮，结束后恢复。若界面允许前一轮结束前再次触发（例如重新启用同一按钮或提供其他入口），请求可能乱序返回；仍要用请求编号、取消或数据层排序规则避免旧结果覆盖新选择。React 的 `useActionState`、`<form>` Action 与 Server Functions 会在各自适用的工作流中处理请求顺序；`useTransition` 本身主要负责非紧急 render。

> [!example]- 完整示例：异步刷新、等待与失败状态
>
> ~~~tsx
> // SummaryRefresh.tsx
> import { useState, useTransition } from "react";
>
> export function SummaryRefresh({
>   fetchSummary
> }: {
>   fetchSummary: () => Promise<string>;
> }) {
>   const [summary, setSummary] = useState("尚未加载摘要");
>   const [error, setError] = useState<string | null>(null);
>   const [isPending, startTransition] = useTransition();
>
>   function refresh() {
>     startTransition(async () => {
>       try {
>         const nextSummary = await fetchSummary();
>         startTransition(() => {
>           setSummary(nextSummary);
>           setError(null);
>         });
>       } catch {
>         startTransition(() => setError("摘要读取失败。"));
>       }
>     });
>   }
>
>   return (
>     <section>
>       <button type="button" onClick={refresh} disabled={isPending}>
>         刷新摘要
>       </button>
>       {isPending && <p role="status">正在刷新摘要…</p>}
>       {error && <p role="alert">{error}</p>}
>       <div aria-busy={isPending}>
>         <p>{summary}</p>
>       </div>
>     </section>
>   );
> }
> ~~~

如果长同步计算仍占住主线程，先优化计算或交给 Worker；若问题来自同时挂载过多结果行，继续看[长列表何时适合虚拟滚动？](#15.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。筛选子树的 memo 边界见[React 渲染优化](#14.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源与版本核验（React 19.3；核验日期 2026-11-12）
>
> - `useDeferredValue` 未传 `initialValue` 时初次直接返回当前值；更新先尝试旧 deferred 值，再可中断地后台 render 新值；Transition 内会直接返回新值；不设固定延迟、不减少网络请求：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)，React 19.3。
> - `memo` 按 props 浅比较跳过重渲染的条件；React Compiler 在已配置时可自动应用等价优化：[`memo`](https://react.dev/reference/react/memo)、[React Compiler](https://react.dev/learn/react-compiler)，React 19.3。
> - Transition 可中断、不能控制文本输入；React 19 Action 跨 `await` 更新要再次包 `startTransition`，自定义异步工作可能乱序；`useActionState` 与 form Actions 覆盖特定顺序管理场景：[useTransition](https://react.dev/reference/react/useTransition)、[`useActionState`](https://react.dev/reference/react/useActionState)，React 19.3。
> - 已揭示边界在 Transition 中保留旧内容；Suspense 可等待 `lazy`、交给 `use` 的 Promise、集成数据源、带 `precedence` 的样式表等资源。Promise 缓存条件只适用于传给 `use` 的数据 Promise；Effect/事件处理器中的普通 fetch 不会自动触发边界：[Suspense](https://react.dev/reference/react/Suspense#what-activates-a-suspense-boundary)、[`lazy`](https://react.dev/reference/react/lazy)、[`use`](https://react.dev/reference/react/use#reading-a-promise-with-use-vs-fetching-in-an-effect)，React 19.3。
> - `lazy` 会缓存声明的 loader Promise；同一声明失败后仅重置错误边界不会再次调用 loader，整页刷新可作为重新尝试模块请求的恢复路径：[lazy](https://react.dev/reference/react/lazy)，React 19.3；刷新后的第二次请求由本章隔离回放实测。
> - `hydrateRoot` 要求服务端 HTML 与客户端首轮一致。文本或树结构不匹配可能导致客户端重建，错误范围取最近 Suspense 边界或整个根；属性差异则不保证被修补：[hydrateRoot caveats](https://react.dev/reference/react-dom/client/hydrateRoot#caveats)、[React error 418](https://react.dev/errors/418)、[React 18 hydration recovery](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#other-breaking-changes)，React 团队；本章另对 text、boundary、root、attribute 四种情况做了独立回放。
> - React 18 的 `createRoot` 启用并发渲染/新根行为，`useTransition` 和 `useDeferredValue` 出自 React 18 并发特性；已有服务端 HTML 用 `hydrateRoot` 并匹配客户端首轮内容：[React 18 Upgrade Guide](https://react.dev/blog/2022/03/08/react-18-upgrade-guide)、[React v18](https://react.dev/blog/2022/03/29/react-v18)、[`hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot)，React 团队发布说明。
> - React 19 移除 `ReactDOM.render`，客户端入口使用 `createRoot`：[React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)，React 团队发布说明。
> - React render 与 commit 不是一回事；`aria-busy` 标记仍在更新的区域：[Render and Commit](https://react.dev/learn/render-and-commit)，React 19.3；[WAI-ARIA 1.2 `aria-busy`](https://www.w3.org/TR/wai-aria-1.2/#aria-busy)，W3C。
> - TanStack Query v5 专用 Suspense Hook、查询失败与错误边界恢复：[Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[`useSuspenseQuery`](https://tanstack.com/query/latest/docs/framework/react/reference/useSuspenseQuery)、[Migrating to v5](https://tanstack.com/query/latest/docs/framework/react/guides/migrating-to-v5)，TanStack 官方文档。
> - React 文档版本：[Versions](https://react.dev/versions)，当前 React 19.3，核验日期 2026-11-12。
## 9. React界面如何维护服务端数据与乐观更新的正确性？

**案例背景。** 报表路由当前账户为 `acct-a`，地址是 `/reports?sort=recent#summary`，服务端给出 May、April 两行。点击 **Oldest first** 后，路由把 `sort` 推入浏览器历史，当前排序变为 April、May；此时 UI（界面）可以先在完整的同账户记录上本地排序，再等待对应查询确认。服务端拥有报表，TanStack Query 的查询缓存只是客户端副本。账户 ID 和会改变结果的筛选条件都属于查询身份：切到 `acct-b` 时，查询键随账户改变；若没有匹配的 B 账户路由行或缓存，就先显示等待/空状态，绝不能把 A 账户的行当作 B 的结果。

浏览器请求会带路径和 `?sort=recent`，不会带 `#summary`；片段只供客户端定位。地址栏、前进/后退与查询状态如何连接由[浏览器导航路径](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)负责。本例只接收路由解析出的 `accountId`、当前 `sort`、匹配的初始数据和排序回调；`pushState`、`popstate` 订阅及路由库由调用方实现。使用 `useQuery` 的组件还须位于 `<QueryClientProvider>` 下，查询/保存函数由应用提供网络适配器；示例不创建这些接线。

### 排序值构成查询身份

`queryKey`（查询键）描述 `queryFn`（查询函数）将取回的结果。这里响应取决于 `accountId` 和 `sort`，所以两者都在 key 中；同一账户的排序列表放在共同前缀下，失效时可只刷新该账户的列表。若再加改变记录集合的过滤条件或页码，也要把它加入 key。

| 阶段 | 当前身份 | 列表与提示 |
| --- | --- | --- |
| 初始路由 | `['reports', 'acct-a', 'list', 'recent']` | 路由给出的 May、April 只种入匹配的账户与排序；`initialData` 可直接显示。 |
| 点击 Oldest first | URL/路由状态先变为 `sort='oldest'`；key 变为 `['reports', 'acct-a', 'list', 'oldest']` | 若这个 key 没有缓存，当前请求等待时只在同账户、同一完整记录集合上把路由行排成 April、May；这批本地行不是该 key 的服务端确认结果，行操作保持禁用。 |
| Oldest 响应到达 | 只更新 `acct-a/oldest` | 列表换成该 key 的服务端数据。先前 `recent` 的请求即使完成，也只能写入 `recent` key；若 query function 消费了取消信号，它也可能在离开 key 时被取消。 |
| 切换到账户 B | `['reports', 'acct-b', 'list', sort]` | key 与页面身份都含账户。若没有匹配的 B 路由行/缓存，先等待或显示空状态，不能把 A 账户的 May、April 当作 B 数据。 |

路由把当前 URL 的排序解析为 `sort`，调用方提供的 `onSortChange` 负责用 `pushState` 新增历史项；浏览器 Back 产生 `popstate` 后，调用方把旧 `sort` 传回，查询 key 随之切回。本例只消费这些路由输入和回调，不实现上述 History API 逻辑。这里保留 `#summary` 只是说明它不参与服务器请求或 query key；只有客户端明确把片段映射为请求参数时，映射后的值才成为查询输入。

路由提供的完整报表行只作为 `initialSort`、`initialAccountId` 对应查询的 `initialData`（初始数据）；其他排序/账户不接收这份缓存种子。TanStack Query v5 会把 `initialData` 写入查询缓存，并按新鲜度策略处理；若路由还给出这批数据的生成时间，就用 JavaScript 毫秒时间戳传入 `initialDataUpdatedAt`，否则客户端会把初始化时刻当成数据时间。30 秒 `staleTime`（新鲜期）只是客户端在该窗口内避免按过期策略自动重取，不承诺服务器数据没有变化；失效仍可强制校准。

`placeholderData`（占位数据）用途不同：它不写入 cache，结果带 `isPlaceholderData` 标记。若为了平滑排序而复用上一 key 的行，应先确认上一 key 的账户仍是当前账户，并在界面标明它还不是新排序的服务端确认；绝不能用上一账户的数据作占位。本文主示例不用这个选项，而是在数据成员完全相同的同账户列表上做本地排序。

本文使用普通 TanStack Query v5 `useQuery` 的状态返回路径，没有设置 `throwOnError`：请求失败保存在 `isError`、`error`、`data` 中。若应用改为抛错配置或 Suspense 查询，失败会走不同界面路径，见[错误边界章节](#11.%20React%E9%94%99%E8%AF%AF%E8%BE%B9%E7%95%8C%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E5%A4%B1%E8%B4%A5%EF%BC%9F)。没有当前 key 数据时会先处于 `isPending`；失败则检查 `isError` 与 `data`：无 query data 时保留同账户路由行（若有）并允许重试，有上次成功结果时保留结果并提示刷新失败。切换排序后若该 key 已有缓存，可以先显示缓存，再按 `staleTime` 等策略后台校准。

### 变更先乐观显示，再与服务端协调

在 `acct-a/oldest` 已显示服务端确认数据时，点击 April 行的 **Mark reviewed**。事件把 `{ accountId: "acct-a", sort: "oldest", id: "april", reviewed: true }` 交给 mutation（服务端变更）。等待保存时，TanStack Query 暴露这份待处理变量；组件按账户、排序和行 ID 把 April 的 `reviewed` 暂时显示为 `true`，查询缓存仍保存上次服务端确认的行。

**保存期间：缓存行与匹配的待处理变量合成界面**

![保存期间查询缓存与待处理 mutation 变量合成界面的状态图](../../frontend/frameworks/resources/react-server-state-overlay.svg)

图中展示已回放失败分支在保存仍 pending 时的合成结果：焦点重取先把新 April、May 写入缓存。下表再展开后续时序；保存请求和 `onSettled` 发起的重取都失败，因此 cache 保留那次焦点重取的结果。

| 时点 | `acct-a/oldest` 的 query cache；匹配的 mutation variable | 界面 |
| --- | --- | --- |
| 焦点重取到达，保存仍 pending | April `reviewed=false`；May 是新标题。变量为 April `reviewed=true`。 | April 显示 `true`；May 保留新标题。 |
| 保存请求失败，`onSettled` 重取中 | cache 不变；变量仍 pending。 | April 仍显示 `true`；May 仍保留新标题。 |
| `onSettled` 重取结束 | 该重取失败，cache 保留上次成功值；pending 变量解除。 | overlay 消失，April 回到 `false`；May 新标题仍在。旧整表快照没有把列表恢复成旧值。 |

1. `submit` 先用共享 QueryClient 检查是否已有这类保存，再启动 mutation；所有行按钮在待处理期间禁用。这个示例主动限制为一次报表标记操作，不让其它调用入口绕过 `submit`。
2. 保存期间发生后台重取时，查询缓存可以照常接收服务器结果；界面层的待处理变量仍盖住 April 的标记。保存请求失败后，mutation 仍等待 `onSettled` 的失效重取收尾；在它退出 pending 前，overlay 继续盖住标记。pending 结束时覆盖消失，列表保留当时可用的查询结果或同账户路由备用数据；不会以旧整表快照覆盖新结果。
3. 保存成功时，`onSuccess` 根据这次提交的 `accountId` 和 `sort` 找到原查询 key，并用服务器返回的 April 行更新缓存。`onSettled` 失效该账户的列表前缀：在本例联网且活跃查询可运行时，匹配的活跃查询会立即重取；非活跃排序只会标为失效、等下次使用再读取。回调返回的 Promise 完成前 mutation 仍处于 pending。

这条成功路径假设保存后发起的列表读取能看到刚才的提交。等待失效重取完成，本身不提供 read-your-writes（读己之写）保证：若它读的是落后副本，仍可能把已确认的新行换回旧值。这种接口需让校准读取到达权威数据源，或按服务端提供的修订号拒绝低于已确认版本的结果；仅延长 overlay 不能修复读取契约。

完整组件只消费路由 props、路由排序回调、provider 和网络适配器；不实现 `pushState`、`popstate` 或客户端创建：

> [!example]- 报表查询与乐观更新组件（TanStack Query v5）
>
> ~~~tsx
> import {
>   useIsMutating,
>   useMutation,
>   useMutationState,
>   useQuery,
>   useQueryClient
> } from "@tanstack/react-query";
>
> type SortOrder = "recent" | "oldest";
> type Report = {
>   id: string;
>   period: string;
>   periodStart: string; // 规范化的 YYYY-MM-DD，可按字典序排序
>   title: string;
>   reviewed: boolean;
> };
>
> const reportKeys = {
>   lists: (accountId: string) =>
>     ["reports", accountId, "list"] as const,
>   list: (accountId: string, sort: SortOrder) => [
>     ...reportKeys.lists(accountId),
>     sort
>   ] as const,
>   markReviewed: () => ["reports", "mark-reviewed"] as const
> };
>
> type MarkReviewed = {
>   accountId: string;
>   sort: SortOrder;
>   id: string;
>   reviewed: boolean;
> };
>
> declare function fetchReports(
>   accountId: string,
>   sort: SortOrder,
>   signal: AbortSignal
> ): Promise<Report[]>;
> declare function saveReviewed(
>   accountId: string,
>   id: string,
>   reviewed: boolean
> ): Promise<Report>;
>
> function sortReports(reports: Report[], sort: SortOrder) {
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
>
> type ReportsRouteProps = {
>   accountId: string; // 当前已登录/选中的账户
>   sort: SortOrder; // 路由从 URL 解析
>   onSortChange: (sort: SortOrder) => void; // 路由写入 pushState
>   initialAccountId: string;
>   initialSort: SortOrder;
>   initialReports: Report[];
>   initialReportsUpdatedAt: number | undefined;
> };
>
> function useReports({
>   accountId,
>   sort,
>   initialAccountId,
>   initialSort,
>   initialReports,
>   initialReportsUpdatedAt
> }: Pick<ReportsRouteProps,
>   | "accountId"
>   | "sort"
>   | "initialAccountId"
>   | "initialSort"
>   | "initialReports"
>   | "initialReportsUpdatedAt"
> >) {
>   const routeDataMatchesQuery =
>     accountId === initialAccountId && sort === initialSort;
>
>   return useQuery({
>     queryKey: reportKeys.list(accountId, sort),
>     queryFn: ({ signal }) =>
>       fetchReports(accountId, sort, signal),
>     initialData: routeDataMatchesQuery
>       ? initialReports
>       : undefined,
>     initialDataUpdatedAt: routeDataMatchesQuery
>       ? initialReportsUpdatedAt
>       : undefined,
>     staleTime: 30_000
>   });
> }
>
> function useMarkReviewed() {
>   const client = useQueryClient();
>   const mutation = useMutation({
>     mutationKey: reportKeys.markReviewed(),
>     mutationFn: (change: MarkReviewed) =>
>       saveReviewed(
>         change.accountId,
>         change.id,
>         change.reviewed
>       ),
>     onSuccess: (saved, change, _result, context) => {
>       const key = reportKeys.list(
>         change.accountId,
>         change.sort
>       );
>       context.client.setQueryData<Report[]>(
>         key,
>         rows => rows?.map(row =>
>           row.id === saved.id ? saved : row
>         )
>       );
>     },
>     onSettled: (_data, _error, change, _result, context) =>
>       context.client.invalidateQueries({
>         queryKey: reportKeys.lists(change.accountId)
>       })
>   });
>
>   function submit(change: MarkReviewed) {
>     // 其它入口也必须经过这道提交级门闩。
>     const hasPending = client.isMutating({
>       mutationKey: reportKeys.markReviewed()
>     }) > 0;
>     if (hasPending) return;
>     mutation.mutate(change);
>   }
>
>   return {
>     isError: mutation.isError,
>     isPending: mutation.isPending,
>     submit
>   };
> }
>
> function ReportsRoute(props: ReportsRouteProps) {
>   return <ReportsPage key={props.accountId} {...props} />;
> }
>
> function ReportsPage({
>   accountId,
>   sort,
>   onSortChange,
>   initialAccountId,
>   initialReports,
>   ...route
> }: ReportsRouteProps) {
>   const query = useReports({
>     accountId,
>     sort,
>     initialAccountId,
>     initialSort: route.initialSort,
>     initialReports,
>     initialReportsUpdatedAt: route.initialReportsUpdatedAt
>   });
>   const update = useMarkReviewed();
>   const isSavingReviewed = useIsMutating({
>     mutationKey: reportKeys.markReviewed()
>   }) > 0;
>   const hasRouteRowsForAccount =
>     accountId === initialAccountId;
>   const confirmedReports = query.data ?? (
>     hasRouteRowsForAccount
>       ? sortReports(initialReports, sort)
>       : []
>   );
>   const pendingChanges = useMutationState<MarkReviewed>({
>     filters: {
>       mutationKey: reportKeys.markReviewed(),
>       status: "pending"
>     },
>     select: mutation =>
>       mutation.state.variables as MarkReviewed
>   });
>   const visibleReports = confirmedReports.map(report => {
>     const pending = pendingChanges.find(change =>
>       change.accountId === accountId &&
>       change.sort === sort &&
>       change.id === report.id
>     );
>     return pending
>       ? { ...report, reviewed: pending.reviewed }
>       : report;
>   });
>
>   return (
>     <section>
>       <div role="group" aria-label="报表排序">
>         <button
>           type="button"
>           onClick={() => onSortChange("recent")}
>         >
>           Most recent first
>         </button>
>         <button
>           type="button"
>           onClick={() => onSortChange("oldest")}
>         >
>           Oldest first
>         </button>
>       </div>
>
>       {query.isPending && (
>         <p role="status">
>           {hasRouteRowsForAccount
>             ? "正在等待服务端确认当前排序…"
>             : "正在读取当前账户的报表…"}
>         </p>
>       )}
>       {query.isFetching && !query.isPending && (
>         <p role="status">正在更新当前账户的报表…</p>
>       )}
>       {query.isError && (
>         <div>
>           <p role="alert">
>             {query.data === undefined
>               ? hasRouteRowsForAccount
>                 ? "确认失败；仍显示同账户的路由报表。"
>                 : "读取失败；尚无当前账户的报表数据。"
>               : "刷新失败；仍显示上次成功的结果。"}
>           </p>
>           <button
>             type="button"
>             onClick={() => query.refetch()}
>           >
>             重试读取
>           </button>
>         </div>
>       )}
>       {update.isError && (
>         <p role="alert">
>           保存失败；已撤去这次待处理显示，
>           列表保留当前可用结果，可再次提交。
>         </p>
>       )}
>       {update.isPending && (
>         <p role="status">正在保存报表更改…</p>
>       )}
>
>       <div aria-busy={query.isFetching}>
>         <ul>
>           {visibleReports.map(report => (
>             <li key={report.id}>
>               {report.period} — {report.title}
>               <span>
>                 {report.reviewed
>                   ? "Reviewed"
>                   : "Not reviewed"}
>               </span>
>               <button
>                 type="button"
>                 disabled={
>                   !query.data ||
>                   query.isPlaceholderData ||
>                   report.reviewed ||
>                   isSavingReviewed
>                 }
>                 onClick={() => update.submit({
>                   accountId,
>                   sort,
>                   id: report.id,
>                   reviewed: true
>                 })}
>               >
>                 Mark reviewed
>               </button>
>             </li>
>           ))}
>         </ul>
>       </div>
>     </section>
>   );
> }
> ~~~

`<QueryClientProvider>` 应在 `ReportsRoute` 的祖先位置提供同一个 QueryClient；`fetchReports` 与 `saveReviewed` 是应用适配器，需要检查 HTTP 响应并将 JSON 作为 `unknown`（尚未验证的数据）运行时校验，TypeScript 声明不会验证网络值。结构合法还不够：保存响应必须对应本次账户和行。本例由已授权的请求资源范围绑定账户，适配器再确认返回的 `saved.id` 等于提交的 `id`；不匹配就按错误处理，不能交给 `onSuccess` 更新另一行。

代码中的 query function 读取 `signal`（取消信号）并交给 `fetchReports`：适配器把它继续传给 `fetch` 才能中止底层请求；适配器忽略时网络仍可能完成，但已取消的查询状态不会接收该结果。若 query function 连 signal 都不读取，离开页面的请求通常可完成并写入自己的旧 key。客户端取消不能承诺服务器停止执行。

排序例子只在记录成员完全相同的 May/April 全列表上本地重排。若账户、筛选、搜索词或页码改变了集合，就不能把旧集合重排后称为当前结果；切换期间应显示当前查询缓存或等待状态。若有上一排序/账户的占位值，必须确认账户身份相同并标出 `isPlaceholderData`，且不允许在占位行上操作。

`staleTime: 30_000` 与“服务端 30 秒内不变”不是一回事。TanStack Query v5 的过期查询可按挂载、窗口重新聚焦或网络恢复等策略后台读取；手动失效也能要求刷新。若用户改了 URL 中的 `sort` 并点击 Back，路由状态应回到原值，query key 也切回对应缓存；`replaceState` 不会像 `pushState` 那样为每次用户选择新增可回退历史项。

### 整表快照回滚的前提与竞态

另一种乐观更新会在 `onMutate` 中先改查询缓存并保存整表快照，失败时用快照回滚，成功时把服务器行写回该 key。下面保留这组回调，作为列表 key 在变更期间确实独占时可用的方案：

~~~tsx
onMutate: async (change: MarkReviewed, context) => {
  const key = reportKeys.list(change.accountId, change.sort);
  await context.client.cancelQueries({
    queryKey: key,
    exact: true
  });
  const previous = context.client.getQueryData<Report[]>(key);
  context.client.setQueryData<Report[]>(key, rows =>
    rows?.map(row => row.id === change.id
      ? { ...row, reviewed: change.reviewed }
      : row)
  );
  return { key, previous };
},
onError: (_error, _change, snapshot, context) => {
  if (snapshot?.previous !== undefined) {
    context.client.setQueryData(snapshot.key, snapshot.previous);
  }
},
onSuccess: (saved, _change, snapshot, context) => {
  if (snapshot) {
    context.client.setQueryData<Report[]>(snapshot.key, rows =>
      rows?.map(row => row.id === saved.id ? saved : row)
    );
  }
}
~~~

这组快照回调只有在同一列表 key 没有并行写入，也没有后续重取覆盖乐观值时才可靠。`cancelQueries` 只取消调用时已匹配的读取，不是锁；`staleTime` 到期后的窗口聚焦、轮询或手动 `refetch` 仍能在保存期间更新缓存。实际回放把时钟推进 31 秒后触发聚焦读取：读取先把服务端 April 的 `false` 和 May 的新标题写入缓存，覆盖此前 April 的乐观 `true`；保存失败后，旧整表快照再把 April、May 整体恢复为旧表，May 新标题随之丢失。主示例因此使用界面层 overlay，让 pending 变量覆盖读取结果，不把一次旧快照当成共享缓存的权威值。

主例以同一个 mutation key（变更键）和共享 QueryClient 做一次全局标记门闩：`useIsMutating` 禁用所有报表行按钮，`submit` 再检查是否有同类保存正在处理，并且只暴露 `submit`、状态，不把可绕过门闩的原生 `mutate` 返回给调用方。若允许多行并发提交，`useMutationState` 会返回多份 pending variables，必须按账户、排序、行 ID 过滤，并用 `submittedAt` 或明确的冲突策略决定同一行显示哪次变更；当前门闩刻意不开放这种并发。

查询缓存和页面中任何已确认数据仍是服务端状态的副本，不是授权来源。若同一报表另有详情 key，也要按 `accountId` 更新/失效详情项，不能只修当前列表。切换账号时 query key 会隔离组件读取的缓存项；退出登录或权限范围更换时，若旧账户数据不该留在客户端，再显式移除对应缓存。对不上账户身份的界面 fallback 不应暂时显示旧账户行。

最后，React 手写 `useEffect` 请求要在 cleanup 中忽略过期结果或取消请求；该请求模式与 TanStack Query 的 key/cache 管理由[React 更新轮次中的数据请求](#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)对照学习。有关错误如何从查询状态进入错误边界，见[React 错误边界](#11.%20React%E9%94%99%E8%AF%AF%E8%BE%B9%E7%95%8C%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E5%A4%B1%E8%B4%A5%EF%BC%9F)。网络 JSON 仍需在运行时校验，见[如何处理不可信 JSON？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。

> [!info]- 来源与版本核验（React 19.3；TanStack Query v5 Latest；核验日期 2026-11-12）
> - Query key 应包含会改变 `queryFn` 结果的变量；此处账户和排序都影响数据：[Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)，TanStack Query v5 Latest。
> - Query function 获取 `AbortSignal`。访问它可让 TanStack Query 取消查询状态；继续传给 transport 才会取消底层请求。手动取消会回滚 query state，但不代表服务器停止处理：[Query Functions](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions)、[Query Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)，TanStack Query v5 Latest。
> - `initialData` 写入 cache；`initialDataUpdatedAt` 可提供原数据时间。`placeholderData` 不进 cache，结果带 `isPlaceholderData`：[Initial Query Data](https://tanstack.com/query/latest/docs/framework/react/guides/initial-query-data)、[Placeholder Query Data](https://tanstack.com/query/latest/docs/framework/react/guides/placeholder-query-data)，TanStack Query v5 Latest。
> - 普通 `useQuery` 的 `throwOnError` 与错误状态返回：[useQuery](https://tanstack.com/query/latest/docs/framework/react/reference/functions/useQuery)，TanStack Query v5 Latest。
> - `staleTime` 控制客户端 freshness；stale query 的自动重取入口及按 key 前缀失效：[Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)、[Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)，TanStack Query v5 Latest。
> - mutation 回调收到提交变量，`onSettled` 返回的 Promise 会在 mutation 完成前等待；`useMutationState` 可以读取同 key 的多笔 pending variables，并可选择 `submittedAt`：[useMutation](https://tanstack.com/query/latest/docs/framework/react/reference/functions/useMutation)、[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5 Latest。
> - Cache optimistic update 和 UI variables overlay 是两种受支持路径；pending variables 可能同时有多笔：[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5 Latest。
> - `invalidateQueries` 将匹配查询标为 invalidated，默认立即重取活跃查询；非活跃查询留在缓存并等待下次使用：[QueryClient.invalidateQueries](https://tanstack.com/query/latest/docs/framework/react/reference/classes/QueryClient#invalidatequeries)，TanStack Query v5 Latest。
> - `QueryClientProvider` 把一个 QueryClient 提供给子树中的查询组件：[QueryClientProvider](https://tanstack.com/query/latest/docs/framework/react/reference/functions/QueryClientProvider)，TanStack Query v5 Latest。
> - query cache 可以按 query key 前缀移除：[QueryClient](https://tanstack.com/query/latest/docs/framework/react/reference/classes/QueryClient)，TanStack Query v5 Latest。
> - HTTP URI 的 fragment 不作为请求目标发送：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)。浏览器历史恢复 `sort` 的完整路由流程见[浏览器导航路径](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。
> - Effect cleanup 防止过期读取写回界面：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3。
## 10. 管理表格打开多步骤编辑后，怎样在查询变化与提交冲突中保住用户意图？

**案例背景。** 管理员从 `/reports?sort=oldest#summary` 打开合成报表列表。报表 42 出现在第一页；用户选择它后翻到第 2 页，再从“已选 1 项”打开编辑抽屉。详情读取到强 ETag（实体标签）`"report-42-v7"` 和一份可编辑表示。编辑器允许改通知方式和备注，后来表格筛选、分页响应可能先后变化；另一位用户也可能先保存。页面要让 Uniform Resource Locator（统一资源定位符，URL）、选择、编辑草稿和服务端版本各自有明确所有者，才能不把任何一份旧数据误当成用户最新意图。

报表 42 的合成表示为：

~~~json
{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

`delivery.channel` 与 `delivery.recipients` 是本教学变体新增的字段，数据不对应真实业务。报表 42 的 GET、条件 PATCH、强 ETag 和 `412` 行为与[HTTP API 条件更新契约](../../engineering-foundations/backend/http-api-contracts.md)一致；本文聚焦表格与编辑器怎样保留草稿。

~~~mermaid
flowchart TD
  URL[sort / filter / page 来自 URL] --> Query[查询当前页]
  Query --> Rows[用 report.id 标识行]
  Rows --> Selection[选择集合按 ID 跨页保留]
  Selection --> Open[按选中 ID GET 详情与 ETag]
  Open --> Baseline[编辑基线 + 本地草稿分开保存]
  Baseline --> Validate[联动字段与异步校验按 ID 和代次归属]
  Validate --> Patch[仅序列化已改变且当前模式有效的字段]
  Patch --> Match{If-Match 仍匹配？}
  Match -->|是| Saved[接收新表示和 ETag，刷新查询]
  Match -->|否，412| Reload[保留草稿，读取当前表示并三方比较]
  Reload --> Confirm[用户选择并确认新基线]
  Confirm --> Patch
~~~

表格查询只决定当前看到哪些行；编辑草稿以稳定资源 ID 和它自己的服务端基线为依据。若把整张表、选中行和表单值都写进同一个临时对象，一次筛选响应就可能覆盖用户正在改的输入。

### URL 查询、行选择与详情草稿怎样各自保存？

表格的 `sort`、筛选和页码可复制、刷新和由浏览器后退恢复，所以它们放在 URL。开始地址是 `/reports?sort=oldest#summary`。用户选择“已发布”后，路由写成 `/reports?sort=oldest&status=published&page=1#summary`；点“下一页”再变为 `/reports?sort=oldest&status=published&page=2#summary`。片段 `#summary` 仍是客户端定位信息，不是筛选参数。

本例的合成表格投影只有两行一页：第 1 页含 ID `17`、`42`；第 2 页含 ID `61`。主流程是在第 1 页选择 `42`、翻页后仍保留 `{42}`，再从“已选 1 项”打开编辑抽屉。另一个筛选分支里，用户把筛选从“已发布”改为“处理中”，路由重置页码并写成 `/reports?sort=oldest&status=open&page=1#summary`；页面清除原集合并告知用户，因为旧过滤条件选出的 ID 可能不属于新结果。若产品需要保留跨筛选选择，应明确将其做成独立的“已选对象”集合并在批量操作前重新校验权限，不能因隐藏行而悄悄套用旧集合。排序或页码改变不会清除当前筛选下的显式选择。

列表行以 `report.id` 而非页内下标作为稳定身份。打开编辑器后，客户端对 `/api/reports/42` 重新 GET，而不是把表格行的摘要字段直接当成完整详情。每次读取和 PATCH 都由服务端按当前身份检查对报表 42 的权限；URL 参数、已选 ID、隐藏按钮或客户端缓存都不授权访问。

编辑器收到响应后保存三份相互关联的状态：基线表示、对应的 ETag、本地草稿。后续表格排序结果或缓存刷新只更新表格查询；它不把表单重置成新的列表对象。草稿脏时关闭抽屉或切换到另一行，先让用户留下、保存或明确丢弃；重新开启报表 42 是一个新编辑会话，必须再读取当前详情和 ETag。React 的局部状态应跟随这个会话，而不是跟随“当前页第 0 行”等列表位置；只有用户明确切换资源或开始新会话时才换编辑器身份。`React` 中组件状态会随组件树的位置与 `key` 变化而保留或重置；筛选列表重渲染与编辑会话重建是两个不同事件。

### 条件字段与动态输入怎样生成有效草稿？

本例的 `email` 模式显示收件人，至少保留一个有效地址；`download` 模式隐藏收件人。草稿可以在未保存的编辑会话里暂存隐藏输入，用户切回 `email` 时仍看见它们，但提交序列化器只写当前模式允许的字段。Merge Patch（合并补丁）一般规定省略成员表示保持、`null` 表示删除；本合成接口另有领域规则：合并后若 `channel` 为 `download`，服务端规范化时移除 `recipients`，并在成功表示中不返回它。比如 `{"delivery":{"channel":"download"},"note":null}` 合并后得到不含 `recipients` 和 `note` 的规范表示。保存成功后，客户端用返回表示和新 ETag 重设基线，并从该表示重建已确认表单；此时收件人列表为空，已删除的隐藏旧值不再留在草稿中。如果随后重新切回 `email`，需要显式补充收件人，不能把服务端刚删除的旧值又提交回来。

`note` 是可选成员，详情类型用 `note?: string` 才能接收条件更新契约中删除备注后的合法 GET/200 表示。新草稿从详情复制备注；只有用户明确执行“移除备注”动作，才把草稿属性记为缺失。将它改成空字符串是另一种输入，不等同于删除。基线里有 `note`、草稿现在缺少它时，客户端发送 `note: null`；基线与草稿都没有备注时，序列化器省略该成员。服务端返回备注缺失后，后续草稿也从这个规范表示重建。

动态收件人行的内部身份与 API 中的字符串数组分开。下面的 `clientId` 在新增时分配一次，并随行移动或删除；它不是邮件地址、数据库 ID，也不会写进 API。这样 React 行键、焦点和异步校验状态不会因为数组重排而错绑到另一个地址。

> [!example]- 可选：完整补丁序列化与规范化响应重建代码
>
> ~~~typescript
> type Report42 = {
>   id: 42;
>   title: string;
>   delivery: { channel: "email" | "download"; recipients?: string[] };
>   note?: string;
> };
>
> type RecipientField = { clientId: string; value: string };
> type ReportDraft = {
>   channel: "email" | "download";
>   recipients: RecipientField[];
>   note?: string;
> };
>
> type ReportPatch = {
>   delivery?: { channel?: "email" | "download"; recipients?: string[] };
>   note?: string | null;
> };
>
> const report42: Report42 = {
>   id: 42,
>   title: "Monthly summary",
>   delivery: { channel: "email", recipients: ["reader@example.test"] },
>   note: "Draft",
> };
>
> function makePatch(baseline: Report42, draft: ReportDraft): ReportPatch {
>   const patch: ReportPatch = {};
>   const delivery: NonNullable<ReportPatch["delivery"]> = {};
>
>   if (draft.channel !== baseline.delivery.channel) delivery.channel = draft.channel;
>   if (draft.channel === "email") {
>     const recipients = draft.recipients.map(field => field.value.trim());
>     if (JSON.stringify(recipients) !== JSON.stringify(baseline.delivery.recipients ?? [])) {
>       delivery.recipients = recipients;
>     }
>   }
>   if (Object.keys(delivery).length > 0) patch.delivery = delivery;
>   if (draft.note !== baseline.note) patch.note = draft.note ?? null;
>   return patch;
> }
>
> const draft: ReportDraft = {
>   channel: "download",
>   recipients: [
>     { clientId: "recipient-1", value: "reader@example.test" },
>     { clientId: "recipient-2", value: "analyst@example.test" },
>   ],
>   note: "Draft",
> };
> const patch = makePatch(report42, draft);
> // => { delivery: { channel: "download" } }
> // 隐藏的 recipients 仍在本地草稿中，但不进入这个模式的 PATCH。
>
> const removeNoteDraft = { ...draft };
> delete removeNoteDraft.note; // 显式移除属性，区别于 note: ""
> const removeNotePatch = makePatch(report42, removeNoteDraft);
> // => { delivery: { channel: "download" }, note: null }
> // null 是 Merge Patch 的删除指令，序列化后的正文明确包含 note:null。
>
> declare function newRecipientClientId(): string;
> function draftFromReport(saved: Report42): ReportDraft {
>   return {
>     channel: saved.delivery.channel,
>     recipients: (saved.delivery.recipients ?? []).map(value => ({ clientId: newRecipientClientId(), value })),
>     ...(saved.note === undefined ? {} : { note: saved.note }),
>   };
> }
> const savedV8: Report42 = {
>   id: 42,
>   title: "Monthly summary",
>   delivery: { channel: "download" }, // 200 不含 recipients
>   // 备注已删除，200 也不含 note
> };
> const rebuiltDraft = draftFromReport(savedV8);
> // => { channel: "download", recipients: [] }；旧隐藏收件人不再存在于草稿。
> ~~~

下面三次变更展示序列化器的关键输入与结果。省略 `recipients` 只表示 Merge Patch 不直接改写此成员；`download` 的服务端规范化才在成功表示中删除它。

| 用户变更 | PATCH 正文 | 成功表示和下一份草稿 |
|---|---|---|
| v7 从 `email` 切到 `download`，备注 `Draft` 不变 | `{"delivery":{"channel":"download"}}` | 200 不含 `recipients`；以响应重建时 `recipients: []` |
| 同上，并明确移除备注 | `{"delivery":{"channel":"download"},"note":null}` | 200 不含 `recipients` 和 `note`；后续草稿也缺少备注属性 |
| 保持 `email`，新增 `analyst@example.test` | `{"delivery":{"recipients":["reader@example.test","analyst@example.test"]}}` | 数组整体替换；备注未改，不进入补丁 |

三行分别展示三个操作：下载模式只改渠道；`note:null` 表示用户明确删除；邮件模式把收件人数组整体替换。

上述函数只构造增量字段。若 `note` 没有变化，它不会被塞回补丁去覆盖另一个用户刚改过的备注；从基线中删除备注时才明确写入 `null`。若 `channel` 为 `download`，它不会将隐藏的收件人数组放进补丁；成功响应中的规范表示也不会再含旧收件人。进入 `email` 模式后，全部动态行按当前顺序序列化，服务器仍验证地址、重复项、是否至少一项和最终资源约束；客户端即时提示不能替代服务端验证。切换到 `download` 会在同一事件处理中递增并作废每个收件人的校验代次，清除当前错误并丢弃待返回 ticket；切回 `email` 时用仍在草稿中的当前值重新校验。关闭编辑会话或移除动态行也同步作废 ticket，避免隐藏字段、已关闭草稿或新会话被旧响应改写。

异步校验必须绑定编辑会话、输入身份与发起时的依赖值。例子中的 `organizationId` 是本教学校验 API 的合成依赖：同一邮箱在不同组织可能有不同可用性。为每个 `sessionId + clientId` 分配单调请求代次，并保存实际校验快照；只有会话仍打开、ticket 仍最新且快照仍与当前字段相同的响应才可以改写错误状态。不同编辑会话即使复用了同一个动态行 ID，也不会接受彼此的迟到结果。

对 `recipient-1`，服务端接收的校验结果按下列次序归属：

| 时刻 | 当前快照和代次 | UI 状态 |
|---|---|---|
| 输入 `reader@old.example.test` | `edit-A / recipient-1 / gen=1 / org-a` | 发出请求 1 |
| 输入改为 `reader@example.test` | 同步更新快照并推进到 `gen=2` | 发出请求 2；请求 1 后到时已过期 |
| 切换到 `download` | 同步推进代次、删除 ticket 与快照 | 收件人隐藏；请求 1 或 2 都不能写入错误 |
| 切回 `email` | 以当前值重新校验，创建 `gen=4` | 只接受新请求；若关掉抽屉，当前 ticket 也立即失效 |
| 重开为 `edit-B` | 键空间变为 `edit-B / recipient-1` | 即使 clientId 与邮箱相同，旧会话响应也无法命中新状态 |

校验结果为 `ok: false` 时始终显示错误；如果响应缺少或给出空 `message`，客户端用“该地址未通过校验”兜底，不能把 `undefined` 传给表示清错的 setter。

> [!example]- 可选：带编辑会话生命周期的校验 ticket 实现
>
> ~~~typescript
> type RecipientField = { clientId: string; value: string };
> type ValidationTicket = { generation: number; snapshot: string };
> const latestTicket = new Map<string, ValidationTicket>();
> const generationByField = new Map<string, number>();
> const currentSnapshotByField = new Map<string, string>();
> declare function checkRecipient(input: { value: string; organizationId: string }): Promise<{ ok: boolean; message?: string }>;
> declare function setIssue(sessionId: string, clientId: string, message: string | undefined): void;
> declare function updateDraftRecipient(sessionId: string, clientId: string, value: string): void;
> declare function updateDraftChannel(sessionId: string, channel: "email" | "download"): void;
>
> function fieldKey(sessionId: string, clientId: string) {
>   return `${sessionId}:${clientId}`; // sessionId 是每次打开编辑器新建的唯一 ID
> }
>
> function invalidateRecipientTicket(sessionId: string, clientId: string) {
>   const key = fieldKey(sessionId, clientId);
>   generationByField.set(key, (generationByField.get(key) ?? 0) + 1);
>   latestTicket.delete(key);
>   currentSnapshotByField.delete(key);
>   setIssue(sessionId, clientId, undefined);
> }
>
> function onRecipientInput(sessionId: string, field: RecipientField, nextValue: string, organizationId: string) {
>   const key = fieldKey(sessionId, field.clientId);
>   const snapshot = JSON.stringify({ value: nextValue.trim(), organizationId });
>   currentSnapshotByField.set(key, snapshot); // 同步作废旧依赖快照
>   updateDraftRecipient(sessionId, field.clientId, nextValue);
>
>   const generation = (generationByField.get(key) ?? 0) + 1;
>   generationByField.set(key, generation);
>   const ticket = { generation, snapshot };
>   latestTicket.set(key, ticket);
>   const isCurrent = () => {
>     const current = latestTicket.get(key);
>     return current?.generation === ticket.generation &&
>       current.snapshot === ticket.snapshot &&
>       currentSnapshotByField.get(key) === ticket.snapshot;
>   };
>   void checkRecipient({ value: nextValue.trim(), organizationId }).then(result => {
>     if (!isCurrent()) return;
>     setIssue(sessionId, field.clientId, result.ok ? undefined : (result.message || "该地址未通过校验"));
>   }, () => {
>     if (!isCurrent()) return;
>     setIssue(sessionId, field.clientId, "暂时无法验证；保留当前草稿");
>   });
> }
>
> function changeChannel(sessionId: string, channel: "email" | "download", fields: RecipientField[], organizationId: string) {
>   updateDraftChannel(sessionId, channel);
>   for (const field of fields) {
>     if (channel === "download") invalidateRecipientTicket(sessionId, field.clientId);
>     else onRecipientInput(sessionId, field, field.value, organizationId);
>   }
> }
>
> function closeEditSession(sessionId: string, fields: RecipientField[]) {
>   for (const field of fields) invalidateRecipientTicket(sessionId, field.clientId);
> }
>
> function removeRecipient(sessionId: string, field: RecipientField) {
>   invalidateRecipientTicket(sessionId, field.clientId);
>   // 然后从该会话草稿移除此行。
> }
> ~~~

以 `recipient-1` 为例，用户先输入 `reader@old.example.test` 并发出第 1 次请求，接着同步改成 `reader@example.test` 并发出第 2 次请求。若第 1 次响应先于第 2 次响应返回，输入处理器已经把快照改为新值，旧响应不能再改写错误；若第 2 次先返回“可用”，再晚到的第 1 次响应仍被新代次挡住。`organizationId` 等其它依赖改变时也调用同一个输入处理函数，即使邮箱文本没变。若此时从 `email` 切到 `download`，`changeChannel` 在发出下一次响应前同步递增代次并删除 ticket；旧 Promise 返回时 `latestTicket.get(key)` 已为空，不能把错误写回隐藏输入。切回 `email` 时当前字段值重新发起校验。移除字段或关闭抽屉同样使 ticket 失效；关闭后重开使用新的 `sessionId`，即使复用了 `clientId` 也不会让旧响应命中新会话。校验服务暂时失败时保留草稿并显示“暂时无法验证”，不能把网络失败说成字段有效。

### 服务器版本改变时怎样处理 `412`？

GET 已读取强 ETag `"report-42-v7"`。用户将备注改为“Send after review”，并在 `email` 模式添加 `analyst@example.test`。提交使用原始基线的 `If-Match`；版本检查与更新由服务器在同一个原子操作中完成：

~~~http
PATCH /api/reports/42 HTTP/1.1
Content-Type: application/merge-patch+json
If-Match: "report-42-v7"

{"delivery":{"recipients":["reader@example.test","analyst@example.test"]},"note":"Send after review"}
~~~

这里的 `412` 是一条重新从 v7 开始的冲突分支。上一节的 `savedV8` 是“切到下载并保存成功”分支；本段的 v8 则是另一位用户在冲突分支里提交的表示，两者不是同一次连续编辑。

假如另一位用户先保存，把当前资源推进到 `"report-42-v8"` 并将备注写成“Reviewed”，上述旧条件不会覆盖它。服务返回 `412 Precondition Failed` 和 Problem Details；至少包含 `type`、`title`、`status`。客户端不能自动重发同一补丁，也不能把当前 `ETag` 静默换成 v8 后再提交。

这时编辑器仍保留原基线 v7、完整的本地草稿和每个字段的校验状态。它重新 GET 当前表示与 ETag v8，再按字段比较三份值：

| 字段 | v7 基线 | 本地草稿 | v8 当前值 | 展示给用户的差异 |
|---|---|---|---|---|
| `title` | `Monthly summary` | `Monthly summary` | `Monthly summary — May` | 只有服务端改过，可采用当前值 |
| `delivery.recipients` | `[reader@example.test]` | `[reader@example.test, analyst@example.test]` | `[reader@example.test]` | 只有本地改过，可在重新确认后保留本地增量 |
| `note` | `Draft` | `Send after review` | `Reviewed` | 两边都改过，要求用户选择或再次编辑 |

若用户确认采用服务端标题、保留本地新增收件人并把备注设为 `Reviewed; send after review`，客户端用 v8 作为新基线重新计算一个最小补丁，展示差异后才提交 `If-Match: "report-42-v8"`。成功时服务器返回新的表示和新强 ETag；本例递增到 `"report-42-v9"`。如果本地意图是移除备注，三方比较会把“属性缺失”与空字符串、服务端当前值分别显示；用户确认删除后仍将 `note: null` 作为补丁语义提交。若合并或提交之间又发生修改，新的 `412` 再次保留草稿并按相同过程处理。冲突界面解决的是“用户想提交什么”，不是让客户端猜测某个版本理应胜出。

成功响应替换详情缓存中的已确认表示和 ETag，再刷新受影响的列表查询。服务端可能因此把报表移出当前筛选页，或改变其排序位置；不能为了让乐观 UI 看起来稳定而在旧页保留已不符合筛选的数据。独立路由中的编辑表单也使用同一基线、草稿、异步校验和条件提交生命周期；它不依赖从表格入口打开。

**延伸阅读：**[React 如何维护服务端数据与乐观更新](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)说明列表查询身份与缓存更新；[React 路由如何把地址映射到界面并恢复前进后退](#62.%20React%20%E8%B7%AF%E7%94%B1%E6%80%8E%E6%A0%B7%E6%8A%8A%E5%9C%B0%E5%9D%80%E6%98%A0%E5%B0%84%E5%88%B0%E7%95%8C%E9%9D%A2%E5%B9%B6%E5%8A%A0%E8%BD%BD%E6%95%B0%E6%8D%AE%EF%BC%9F)说明查询 URL 的导航状态；[语义化 HTML 表单如何支持键盘与辅助技术用户](#16.%20%E8%AF%AD%E4%B9%89%E5%8C%96%20HTML%20%E8%A1%A8%E5%8D%95%E5%A6%82%E4%BD%95%E6%94%AF%E6%8C%81%E9%94%AE%E7%9B%98%E4%B8%8E%E8%BE%85%E5%8A%A9%E6%8A%80%E6%9C%AF%E7%94%A8%E6%88%B7%EF%BC%9F)说明字段错误与焦点。条件 PATCH 和授权的服务端边界见[HTTP API 契约](../../engineering-foundations/backend/http-api-contracts.md)。

> [!info]- 来源
> - **表格行身份与 React 编辑状态生命周期：** [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 官方文档，核对日期 2026-11-09。
> - **URL、查询参数与历史状态：** [WHATWG HTML: History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，[WHATWG URL: URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)；并参见[浏览器怎样让筛选状态跟随地址栏与前进后退](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)。
> - **强 ETag、`If-Match`、原子条件更新、`412` 与合并补丁：** [HTTP API 条件更新契约](../../engineering-foundations/backend/http-api-contracts.md)；具体协议由其所引 RFC 核验。本篇的字段和版本是冻结的合成示例。
> - **表单校验与错误提示的用户界面边界：** [语义化 HTML 表单怎样支持键盘与辅助技术用户](#16.%20%E8%AF%AD%E4%B9%89%E5%8C%96%20HTML%20%E8%A1%A8%E5%8D%95%E5%A6%82%E4%BD%95%E6%94%AF%E6%8C%81%E9%94%AE%E7%9B%98%E4%B8%8E%E8%BE%85%E5%8A%A9%E6%8A%80%E6%9C%AF%E7%94%A8%E6%88%B7%EF%BC%9F)。校验响应代次与草稿隔离是本文根据该合成流程明确的客户端所有权。
## 11. React错误边界能恢复哪些失败？

**案例背景。** 延续报表页：服务端给出 May、April，用户选 **Oldest first** 后，路由状态变为 `sort=oldest`，父组件把排好序的 April、May 传给列表；排序状态随浏览器前进/后退恢复，见[浏览器导航路径](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。若列表组件在 `render`（渲染）时抛错，错误边界可以把这块列表换成备用界面，让边界外的排序区域继续留在页面。它能捕获 React 渲染路径中的子树错误、React 提交阶段同步执行时的异常，以及 React 明确追踪的部分异步失败。普通点击、定时器和 Effect 启动后自行运行的 Promise 拒绝，仍须各自处理。

### 先按失败发生的位置选择处理方式

Error Boundary（错误边界）是包住子树、在子树出错时改显示 fallback（备用界面）的组件。React 内置的边界由类组件实现：`static getDerivedStateFromError`（从错误派生状态）让下一次 render 进入 fallback，`componentDidCatch`（捕获错误）在提交阶段记录错误与组件栈。React 19.3 的捕获边界如下：

| 失败发生的位置 | 最近错误边界会怎样处理 |
| --- | --- |
| 子组件构造、render 或 React 生命周期中的同步错误 | 显示最近边界的 fallback（备用界面）。错误若发生在边界自身的 render/生命周期，则交给更外层边界。 |
| React 管理的 Effect setup/cleanup 同步抛错 | React 19.3.0 浏览器回放中由最近仍挂载的边界接住；若内层边界随子树卸载，仍挂载的外层边界可以接住。没有仍挂载的祖先边界时，就无边界可显示 fallback。 |
| `useTransition()` 返回的 `startTransition` 中，动作函数（Action）同步抛错或返回的 Promise 拒绝 | 交给包住调用 `useTransition()` 组件的边界。若 Action 另行启动 Promise 却不 return/await，拒绝不会自动归入此 Action。 |
| 从 React 导入的独立 `startTransition` 回调抛错或返回拒绝的 Promise | 这个 API 用于标记更新；此回调中的错误会进入全局错误报告，不会因此交给错误边界。不要把它和 `useTransition()` 返回的同名函数混为一谈。 |
| `use(promise)` 在 render 中读取已复用的 Promise | Promise pending 时由最近 `Suspense`（挂起边界）管理等待；首次挂载等情形会显示 fallback，Transition 等更新也可能保留已显示内容。Promise 拒绝时进入最近错误边界。Promise 应跨重渲染复用，不能每次 render 都创建新的 Promise。 |
| 普通点击处理器、定时器或 Effect 启动的 Promise 后续拒绝 | 错误边界不会自动接住。处理器里用 `try/catch`，异步任务显式处理 Promise 拒绝，或把错误写入界面状态。 |
| `useEffect` 启动的普通请求失败 | 把失败和重试放在请求状态中；它不会自动变成 render 错误或 Suspense 挂起。 |
| 服务端渲染期间抛错 | 类错误边界不捕获服务端错误，由服务端渲染管线处理。流式 SSR 可用 `Suspense` 输出 fallback；若客户端随后重试渲染仍报错，才可能由客户端错误边界处理。 |

React 19 文档把 Error Boundary 的内置用途描述为捕获子树 rendering errors，并明确排除普通事件、一般异步任务、服务端渲染和边界自身错误。React 调用 Effect setup/cleanup 时，可捕获其中的同步抛错；普通 `useEffect` 也可能在浏览器绘制后运行，这不要求它与 DOM 提交同步。本章实测了 19.3.0 中仍挂载边界的捕获范围。由 Effect 启动、之后才拒绝的 Promise 已离开 React 当次调用，必须自行处理。Hook 返回的 `startTransition` 是文档列出的例外；独立导入的同名 API 不提供这条错误边界路径。

### 边界放在用户能理解的恢复位置

本例把报表列表和排序区拆开。当前示例已处于 `oldest` 状态，父组件把 April、May 两行传入；列表 render 出错时，最近仍挂载的 `ReportBoundary` 用 fallback 替换列表，排序区仍留在外层页面。图中虚线表示组件树的父子关系，橙色箭头表示发生错误后列表内容被 fallback 替换。

![报表列表位于错误边界内，排序区在边界外](../../frontend/frameworks/resources/react-error-boundaries-scope.svg)

下面给出边界、报表区域和一个最小调用。工具栏固定显示 `Oldest first`，只代表边界外仍在页面的区域；此例省略 URL 和实际排序逻辑，由父组件传入已按 April、May 排序的数据。`key={accountId}` 让切换账户时重新建立边界和列表树，边界本地的失败状态不会带到新账户；它只重置 React 子树身份，不负责隔离查询缓存或验证报表数据，共享查询缓存且账户会改变结果时，查询身份也必须区分账户。查询键如何区分结果集，见[报表查询章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。目前 React 内置边界仍由类组件实现；即使用函数组件组装页面，也能在子树周围嵌入类边界或使用现有边界库。

> [!example]- 完整的类边界与报表区域
>
> ~~~jsx
> import { Component } from "react";
>
> class ReportBoundary extends Component {
>   state = { hasError: false };
>
>   static getDerivedStateFromError() {
>     return { hasError: true };
>   }
>
>   componentDidCatch(error, info) {
>     console.error(
>       "报表区域渲染失败",
>       error,
>       info.componentStack
>     );
>   }
>
>   render() {
>     if (this.state.hasError) {
>       return (
>         <section>
>           <p role="alert">报表列表暂时无法显示。</p>
>           <button
>             type="button"
>             onClick={() => this.setState({ hasError: false })}
>           >
>             重新渲染列表
>           </button>
>         </section>
>       );
>     }
>     return this.props.children;
>   }
> }
>
> function ReportsShell({ accountId, reports }) {
>   return (
>     <main>
>       <p>当前排序：Oldest first</p>
>       <ReportBoundary key={accountId}>
>         <ReportsList reports={reports} />
>       </ReportBoundary>
>     </main>
>   );
> }
>
> function ReportsList({ reports }) {
>   return (
>     <ul>
>       {reports.map(report => (
>         <li key={report.id}>{report.title}</li>
>       ))}
>     </ul>
>   );
> }
>
> const initialReports = [
>   { id: "april", title: "April" },
>   { id: "may", title: "May" }
> ];
>
> function App() {
>   return (
>     <ReportsShell
>       accountId="a"
>       reports={initialReports}
>     />
>   );
> }
> ~~~

起始调用用账户 `a` 和已排序的 `initialReports` 显示 April、May。若父组件为同一账户传入 `reports = [null]`，列表在渲染这条空记录并读取其属性时会触发 `TypeError`，fallback 替代列表而工具栏继续留在页面。坏输入不变时点击“重新渲染列表”会再失败；先传回有效行，边界仍会保留 fallback，直到再次点击重试才恢复。若换成新的账户 ID 且传入有效行，`key` 会重建边界。真实 API JSON 应先做运行时校验；这里注入的 render TypeError 只验证错误边界，不能替代请求或数据校验失败的处理。

“重新渲染列表”按钮只把边界状态重置为可尝试渲染；它不会修复错误数据，也不会重新发送查询。若 `reports` 仍含 `null`，子树一重试就再次报错。真正的恢复动作应先由数据所有者修复输入、重新读取或离开故障路由，然后再重置/重新挂载边界。查询状态、重试和缓存由[报表服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)负责。

边界粒度按用户能理解和恢复的区域决定：把整页包起来会连工具栏一起隐藏；每一行都放边界则可能留下许多局部错误框，读者也难以知道列表是否完整。JSX 中写 `try { return <ReportsList /> } catch { ... }` 捕获不到之后的子组件 render，因为那一行只创建元素描述，React 会在后续工作中调用子组件。

### 错误边界与其他失败处理方式

普通 TanStack Query v5 `useQuery` 默认把请求失败作为结果状态交给组件；组件读取 `isError`、`error`、`data` 决定报错和重试。配置 `throwOnError` 或改用 `useSuspenseQuery` 时，查询 Hook 会按当前规则把错误抛入边界；应用也可以在 render 中自行抛出查询错误。`useSuspenseQuery` 的默认规则不是“所有失败都丢弃数据”：无缓存数据时错误交给边界；已有缓存但后台刷新失败时，默认继续显示缓存数据。若用边界承接查询错误并在 fallback 提供重试，需要用 TanStack 的 Query Error Reset Boundary 协调查询错误重置和边界重置；只清空 React 边界的 `hasError` 不会重置查询状态。

客户端资源暂未就绪时，`Suspense` 可用 fallback 显示等待界面；首次挂载或不保留旧内容的更新通常会切到它。若已显示的内容在 Transition 等更新中再次挂起，React 也可能保留旧界面。错误边界的 fallback 则表示子树已经失败。`use(promise)` 只在 render 中读取并跨重渲染复用的 Promise：pending 属于挂起，拒绝属于错误。普通 `fetch` 写在 `useEffect` 或点击处理器中不会自动进入 Suspense；常规查询若选择 `isError` 状态路径，也无须额外套一层错误边界。

状态更新包在 Transition（过渡）中时，如果新内容暂时挂起，React 可以继续显示已经提交的旧内容，而不马上换成 Suspense fallback。是否保留旧界面由更新方式与边界位置决定；Transition 不会把已提交的旧数据变成新请求结果。

> [!info]- 来源与版本核验（React 19.3；TanStack Query v5 Latest；核验日期 2026-11-12）
> - React 类边界的 `getDerivedStateFromError`、`componentDidCatch`、错误粒度建议，以及事件、普通异步任务、服务端渲染和边界自身的排除范围：[Component — Catching Rendering Errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，React 19.3。
> - `useTransition()` 返回的 `startTransition` 把其 Action 的同步抛错或返回的 Promise rejection 交给最近边界：[useTransition — Displaying an error to users](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary)，React 19.3。独立导入的 `startTransition` 走全局错误报告，按 [React 19.3.0 实现](https://github.com/react/react/blob/v19.3.0/packages/react/src/ReactStartTransition.js)核验。
> - `use(promise)` 在 render 时读取 Promise；pending 进入 Suspense，rejection 进入 Error Boundary，Promise 应缓存以便重渲染复用：[use](https://react.dev/reference/react/use)，React 19.3。
> - Effect setup 在提交后由 React 调用、清理在依赖改变/卸载时执行；普通 `useEffect` 可能在绘制后运行：[useEffect](https://react.dev/reference/react/useEffect)，React 19.3。同步错误是否由仍挂载的最近边界接住按本章 React 19.3.0 浏览器回放核验；Promise 后续拒绝由异步路径处理。
> - 流式 SSR 中组件错误可由最近 `Suspense` 在服务端输出 fallback；客户端后续 render 再发生错误时才可能由客户端边界接住：[Suspense — Providing a fallback for server errors and client-only content](https://react.dev/reference/react/Suspense#providing-a-fallback-for-server-errors-and-client-only-content)，React 19.3。
> - TanStack Query `useQuery` 的 `throwOnError` 与 error-as-state 选项：[useQuery](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery)，TanStack Query v5 Latest，核验日期 2026-11-12。
> - `useSuspenseQuery` 无可显示数据时的错误边界路径、缓存存在时的后台刷新错误规则和 `QueryErrorResetBoundary`：[Suspense guide](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[QueryErrorResetBoundary](https://tanstack.com/query/latest/docs/framework/react/reference/QueryErrorResetBoundary)，TanStack Query v5 Latest，核验日期 2026-11-12。
> - Suspense 不侦测 Effect/事件处理器内的普通请求；更新中再次挂起时，Transition/`useDeferredValue` 可避免已显示内容立即切到 fallback：[Suspense](https://react.dev/reference/react/Suspense#what-activates-a-suspense-boundary)，React 19.3。
## 12. 为什么一次 DOM 改动会增加布局或绘制工作？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，看到 May、April 两行报表；点击“最早优先”后，页面把地址中的 `sort` 参数改为 `oldest`，并把 Document Object Model (DOM, 文档对象模型) 中的行顺序换成 April → May。[DOM 更新与事件章节](#4.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E6%80%8E%E6%A0%B7%E6%9F%A5%E8%AF%A2%E3%80%81%E6%9B%B4%E6%96%B0%20DOM%20%E5%B9%B6%E5%93%8D%E5%BA%94%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9F)解释了点击处理器怎样改动节点；本章从“新 DOM 已经写入”开始，解释浏览器怎样让后续画面与新状态一致，以及脚本何时可能为了读取当前几何而等浏览器先更新布局。

### 浏览器需要让哪些信息重新一致？

HyperText Markup Language (HTML, 超文本标记语言) 标准定义浏览器何时有机会更新窗口渲染，但没有规定每个浏览器都使用同一套内部阶段、线程或绘图技术。把报表变成画面的过程可先分成几层：Cascading Style Sheets (CSS, 层叠样式表) 规则针对当前 DOM 计算 computed style (计算样式)；layout (布局) 为盒子求出尺寸与位置；paint (绘制) 生成描述可见内容的绘制操作；需要生成新像素时再做 rasterization (栅格化)；compositing (合成) 把已有与更新后的绘制表面组合，再交给显示过程。

![点击后的 DOM 状态怎样经过按需的样式、布局与绘制更新进入画面](../../frontend/html-css/resources/rendering-update.svg)

图是用来说明依赖关系的概念模型，不表示每次改动都要顺序重做每一层。浏览器可以延后并合并工作、复用仍有效的结果，也可以跳过没有失效的阶段。渲染机会与 JavaScript 任务的边界见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)：处理器返回后 DOM 已是新顺序，但浏览器不保证每个任务后都立即显示一帧；请求或异步业务结果是否完成，也不会由 DOM 写入自动保证。对通常按 DOM 顺序从上到下排布的报表，April 会从第二行移到第一行，May 移到第二行；相关几何与绘制输出更新后，下一次实际呈现的画面才会显示 April 在上。几何读取可以让脚本拿到计算后的值，但不会因此立即把一帧画到屏幕上。

| 对这张报表做什么 | 浏览器可能要更新什么 | 仅凭操作名称不能推出什么 |
| --- | --- | --- |
| 把两行从 May → April 调成 April → May | 更新受影响的样式、几何或绘制结果 | 失效范围取决于选择器依赖、布局关系与引擎优化 |
| 只把按钮文字颜色改成强调色 | 重算适用样式并更新相应绘制结果 | 若尺寸与换行不变，原有几何可能仍可复用 |
| 改宽度、字体或会占空间的内容 | 重新计算受影响盒子的尺寸与后续位置，再更新绘制 | 重排范围不一定只限于被改的节点 |
| 改变 `transform` 或 `opacity` | 某些实现路径可不重新布局，甚至复用绘制结果 | 不能仅凭属性名保证提升图层、只走合成或使用 GPU |
| DOM / 样式写入后读取几何 | 若所需样式或布局已失效，读取前可能同步更新 | 同一几何读取接口并非每次调用都触发布局 |

reflow (重排) 和 repaint (重绘) 是常见工程用语，不是跨浏览器可比较的性能分数。一个节点改变尺寸后，后续流式内容的位置可能一起改变；反过来，属性改了但布局几何未失效时，也可能不需要重做布局。`transform` 和 `opacity` 常被选作动画候选，是因为它们在某些渲染路径中可以绕过布局或复用绘制内容；目标页面是否真的走这条路，应看目标浏览器的性能录制。

### 为什么读几何会让脚本停下来？

浏览器可以把样式或布局结果标为待更新，继续运行 JavaScript，并把工作留到下一次渲染更新。可测量几何的 application programming interface (API, 应用程序接口) 必须返回调用时可观察到的当前值：`offsetWidth` 在普通单盒案例中返回未应用变换的整数边框盒宽度；`getBoundingClientRect()` 返回相对视口的包围矩形，并把变换计入。如果前面的 DOM / CSS 写入使返回值依赖的数据失效，实现就可能在返回前同步重算样式或布局。若数据仍然是最新的，读取可以复用结果，不必新做一次布局。

![几何读取遇到失效布局时，浏览器先同步更新再把当前值交回脚本](../../frontend/html-css/resources/geometry-read-flow.svg)

同步刷新会让脚本等所需计算完成后才继续；其中同步执行布局的情况，Chrome 文档称为 forced reflow (强制重排)。被等待的工作不一定是 API 本身的固定成本：它取决于此前哪些数据失效、布局影响范围多大，以及实现是否能复用结果。图示的是“读取当前值”这一契约带来的实现压力，不意味着每次读取都会刷新。

下面是一个独立的宽度例子，不是前面的报表行。它从同一组已有元素开始：两个没有最小 / 最大宽度约束、没有变换的普通块级元素，边框盒宽度分别为 100px 和 160px。`box-sizing: border-box` 使声明的宽度指定边框盒宽度，因此将当前值加 10 后，目标宽度分别为 110px 和 170px。

~~~html
<div id="width-demo">
  <div class="item" style="width: 100px"></div>
  <div class="item" style="width: 160px"></div>
</div>
~~~

~~~css
#width-demo .item {
  box-sizing: border-box;
  padding: 4px;
  border: 1px solid;
}
~~~

`querySelectorAll()` 返回的 `NodeList` 没有 `Array.prototype.map()`，所以先用 `Array.from()` 转成数组：

~~~javascript
const items = Array.from(
  document.querySelectorAll("#width-demo .item")
);
~~~

下面两段是从上述相同起始宽度分别运行的写法，不是先后执行。第一段每次写完宽度就读取同一元素的新宽度；若该写入使布局数据失效，后读会迫使浏览器先把当前尺寸算出来：

~~~javascript
const widthsAfterEachWrite = [];
for (const item of items) {
  item.style.width = (item.offsetWidth + 10) + "px";
  widthsAfterEachWrite.push(item.offsetWidth);
}
~~~

如果每个新值只依赖它自己的原宽度，而且不必观察前一项写入后的中间几何，就不必在每次写入后立即读回。先读取所有原值，再统一写入；若仍需要验证最终几何，可在最后集中读取：

~~~javascript
const nextWidths = items.map(item => item.offsetWidth + 10);
items.forEach((item, index) => {
  item.style.width = nextWidths[index] + "px";
});
const widthsAfterBatch = items.map(item => item.offsetWidth);
~~~

探针在记录前先读取两个 `offsetWidth`，确保初始几何已就绪。在同一版 headless Chrome (无头 Chrome) 的可重复探针中，两种写法都得到 110px、170px：逐项版本第一次读取原值 100px，写入 110px 后立即读取时，浏览器更新当前几何；随后第二项从原值 160px 写成 170px 并再次读取，又需要更新几何。批量版本先读到 `[100, 160]`，再写入两个新值；末尾第一次读取处理两项变更，第二次读取复用刚更新的结果。用 Chrome DevTools Protocol (CDP, Chrome 开发者工具协议) 记录这一段脚本时，逐项写后读观察到 2 次布局事件，批量读写并在末尾读回观察到 1 次。若开始时的布局本来已失效，批量代码开头的读取也可能先触发更新；这次计数只说明这个小例子的读写次序，不证明任何批量操作在所有页面都更快。应先在性能录制里确认同步布局，再定位让数据失效的写入和紧跟其后的读取。

几何读取接口返回的盒子与坐标系不同：例如，变换会影响 `getBoundingClientRect()` 的结果，却不影响 `offsetWidth`。按问题选择测量方式，见[哪个 DOM 几何 API 能回答哪种测量问题？](#25.%20%E5%93%AA%E4%BA%9B%E7%BD%91%E9%A1%B5%E5%87%A0%E4%BD%95%E6%8E%A5%E5%8F%A3%E8%83%BD%E6%B5%8B%E9%87%8F%E5%93%AA%E4%B8%80%E7%A7%8D%E7%9B%92%E5%AD%90%EF%BC%9F)。

### 引擎怎样实现这些步骤？

Web 平台规定 DOM、CSS 和几何 API 的可观察结果，不要求各浏览器共享一个内部管线。以 Chromium 的 RenderingNG 为例，渲染器会处理样式、布局、预绘制和绘制记录；后续把绘制内容分块栅格化，再提交 compositor frame (合成帧)，由 Chromium 的 Viz 组件聚合可见表面并绘制。Chromium 文档展示的 graphics processing unit (GPU, 图形处理器) 纹理 tile (图块) 是这一实现中的数据结构；实际设备可能使用不同的栅格后端或回退路径，其他引擎的组件名称和阶段安排也会不同。因此，浏览器通用解释要落在“输入状态、失效数据与画面结果”，性能判断则要看目标引擎的录制。

如果报表增长到许多行，先区分网络传输、服务端查询、客户端数据计算和已挂载节点的样式与布局成本。虚拟滚动主要减少同时挂载的 DOM；不会自动缩小已下载数据或消除对全量数据的计算。窗口计算、可变行高、焦点与辅助技术边界见[长报表列表何时适合虚拟滚动？](#15.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)；性能录制怎样区分处理时长、布局与绘制成本，见[如何测量并诊断网页性能问题？](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源与核验
> - **渲染机会与更新渲染。** [WHATWG HTML §8.1.7 Event loops / update the rendering](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering)，Living Standard，更新于 2026-11-11，核对于 2026-11-12。规范定义渲染机会与更新渲染中的样式、布局等步骤；图示的绘制、栅格化和合成阶段是概念说明，不是 HTML 要求的跨浏览器固定管线。
> - **盒子生成与布局模型。** [CSS Display Module Level 3](https://www.w3.org/TR/css-display-3/)，W3C Candidate Recommendation Draft，2026-06-05；用于解释元素生成的盒与格式化模型。
> - **几何读取的返回值。** [CSSOM View Module Level 1](https://drafts.csswg.org/cssom-view/)，Editor’s Draft，2026-11-05，`offsetWidth` 与 `getBoundingClientRect()` 算法；[CSS Sizing Module Level 3](https://www.w3.org/TR/css-sizing-3/#box-sizing)，`box-sizing` 的尺寸解释。CSSOM View 当前页面标明是讨论中的编辑草案，核对于 2026-11-12。
> - **强制重排诊断。** [Chrome Performance Insights: Forced reflow](https://developer.chrome.com/docs/performance/insights/forced-reflow)，Chrome DevTools 官方文档，更新于 2025-10-08；其强制重排描述和诊断范围针对 Chrome 实现。
> - **Chromium 实现路径。** [RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture) 与 [Key data structures in RenderingNG](https://developer.chrome.com/docs/chromium/renderingng-data-structures)，Chromium 官方架构文档；核对于 2026-11-12。文中的 Viz、tile (图块) 和 compositor frame (合成帧) 仅描述 Chromium。
> - **本地探针。** 本轮 headless Chrome `157.0.8103.51` 使用 CDP 记录布局：记录前显式读取两个元素的 `offsetWidth` 使初始几何就绪；逐项写后读出现 2 个 `Layout` 完成事件，批量写入并在末尾读回出现 1 个；两种结果均为 `[110, 170]`。这是本机配置和该 DOM/CSS 的可重复观察，不作跨版本性能承诺。
## 13. 如何测量并诊断网页性能问题？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，等报表首屏出现，再点击“最早优先”把 May → April 排成 April → May。有人反馈“页面开得慢”，有人反馈“点击没反应”；这两种描述可能落在不同阶段，修复前要先把用户感受到的时间与浏览器实际工作对应起来。

### 三项核心指标分别回答什么？

Core Web Vitals（核心网页指标）目前包含三项稳定指标，分别覆盖主要内容加载、交互响应和视觉稳定性。表里的“良好”阈值是现场数据的分档标准，不是单次访问的服务保证。

| 指标 | 它回答的问题 | 良好阈值 |
|---|---|---:|
| Largest Contentful Paint（最大内容绘制，LCP） | 视口中最大的合格图片、文字块或视频何时绘制，通常用来观察主要内容是否及时出现 | ≤ 2.5 秒 |
| Interaction to Next Paint（交互到下一次绘制，INP） | 用户点击、触屏或键盘交互后，浏览器何时能呈现下一帧；有时没有新帧要绘制，也不保证业务结果已出现；每次访问通常取最慢交互，交互很多时每 50 次排除一个最慢值 | ≤ 200 毫秒 |
| Cumulative Layout Shift（累积布局偏移，CLS） | 页面生命周期中最大一组连续的意外布局偏移有多大 | ≤ 0.1 |

评估一个页面或站点时，要看真实访问样本在移动端、桌面端分别计算的第 75 百分位（p75）：至少 75% 的访问达到良好阈值，才会被划入该指标的良好档。它是现场人群分布的摘要，不能说明每次访问都一样快。CLS 也不是把整次访问的所有偏移直接相加；它取一组相邻偏移组成的 session window（会话窗口）中的最大分数，窗口内相邻偏移间隔少于 1 秒，且窗口最长为 5 秒。阈值与口径截至 2026-11-06 核对；发布说明或测量产品改变时，应重新核实。

INP 不是“事件处理器运行了多久”。一个逻辑交互可能产生 `pointerdown`、`pointerup`、`click` 等多个 Event Timing 条目；浏览器按关联条目汇总交互延迟，再定位三段时间。输入延迟结束于相关回调开始，不是处理器自身的耗时：

| 阶段 | 起止点 | 报表点击中的可能原因 |
|---|---|---|
| input delay（输入延迟） | 用户开始点击，到该交互的第一个事件回调开始 | 更早运行的长任务、脚本执行或其他主线程工作 |
| processing duration（处理时长） | 该交互相关事件回调执行期间 | 点击处理器排序数据、React 计算更新或其他监听器工作 |
| presentation delay（呈现延迟） | 事件回调结束，到浏览器下一次可以呈现帧时（有时没有新帧要绘制） | 样式、布局、绘制等渲染工作，或下一帧前的其他主线程任务；指标不保证业务结果已在这帧出现 |

例如，一次假设录制从用户输入 0 ms 开始，回调在 90 ms 开始，105 ms 调用几何 API 并因同步布局等待 85 ms，回调在 195 ms 返回，下一帧在 230 ms 呈现。对应三段是 90 / 105 / 35 ms；85 ms 的同步布局属于处理时长，因为它发生在回调内。若同一读取发生在回调返回之后、下一帧呈现之前，它才可能落在呈现延迟。这些数字用于演示归类，不是报表的实测数据。

所以处理器很短也可能有高 INP：点击前主线程忙会增加输入延迟；DOM 修改后的布局与绘制会增加呈现延迟。反过来，INP 衡量到这次呈现机会为止，并不计量之后才完成的网络请求或所有异步业务效果；下一帧也可能尚未显示业务结果。复杂操作可先给出加载状态等可见反馈，结果到达后再更新内容。浏览器点击、处理器、微任务与渲染机会的边界见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)。

### 现场数据与实验室录制怎样配合？

field data（现场数据）来自实际用户访问，包含设备、网络、地理位置、缓存状态和用户行为的差异，适合判断用户整体体验及指标分布。lab data（实验室数据）在较受控的设备、网络和位置中运行，适合重现路径、比较改动并检查原因；一次 Lighthouse 加载录制并没有真实交互，不能直接给出该次访问的 INP。Total Blocking Time（总阻塞时间，TBT）可以提示页面加载期间主线程被长任务占用的风险，但它是实验室诊断指标，不等同于 INP，也无法代表用户何时点击。

用同一个 URL 和动作做前后比较，并记录浏览器、设备、网络模拟、缓存是否冷启动以及数据来自现场还是实验室。现场指标看相同设备分组与百分位；排查点击时，用 Chrome DevTools（Chrome 开发者工具）的 Performance 面板交互轨道录制一次真实点击，观察输入延迟、处理时长、呈现延迟以及对应的主线程任务。排查加载时单独录制导航；Network 面板检查关键请求的发起时点、传输和响应时间。一次实验室运行解释某个复现条件，不替代多用户的现场分布。

### 怎样从用户症状找到主要成本？

| 观察到的症状 | 先看什么 | 可能的下一步 |
|---|---|---|
| `/reports` 的主要内容迟迟没有出现 | 实际 LCP 元素、服务器首字节、重定向、关键资源何时被发现与完成、渲染延迟 | 若资源发现晚，调整 HTML 中可发现性或优先级；若响应晚，追网络或服务端；若图片是 LCP，避免对它延迟加载 |
| 点“最早优先”后，按下去很久才开始处理 | 交互的输入延迟，点击到达前的主线程任务 | 查长任务、脚本解析执行或其他占用；有界的非关键计算可切到后续任务或 Worker |
| 处理器开始后，列表迟迟没变化 | 交互的处理时长、事件处理器和框架提交工作 | 定位数据排序、组件计算或回调；只拆分确实阻塞主线程的工作 |
| 处理器很快结束，但下一帧仍晚 | 呈现延迟、事件回调结束后的样式/布局/绘制轨迹 | 检查 DOM 规模和昂贵样式；见[为什么一次 DOM 改动会增加布局或绘制工作？](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F) |
| React 处理时长长 | 浏览器 Performance 录制与组件 render/commit 记录 | 用 [React Profiler](#14.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F) 找出组件工作，再回到浏览器轨迹查看提交后的样式、布局和绘制 |
| 路由主脚本传输或解析时间长 | Network 请求体积、脚本解析与执行时间、生产构建的 chunk | 检查路由代码是否实际拆分并延后加载；构建产物边界见[构建工具](#51.%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%BA%90%E7%A0%81%E5%8F%98%E6%88%90%E5%8F%AF%E5%8F%91%E5%B8%83%E4%BA%A7%E7%89%A9%EF%BC%9F) |
| 图片出现时文字或按钮向下跳 | CLS 事件、缺少尺寸的图片/嵌入内容、字体替换或异步插入 | 提前保留内容空间并复现相同网络条件 |
| 首屏按钮显示了但点击无反馈 | 脚本是否已完成初始化，或处理器是否被主线程工作挡住 | 分清“已经看见”与“事件可处理”；HTML 脚本调度边界见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F) |

若 click handler 在返回前调用 `offsetWidth` 或 `getBoundingClientRect()`，并因此同步触发布局，这段成本在 INP 中计入处理时长；若几何读取或渲染工作发生在事件回调结束后、下一帧出现前，则计入呈现延迟。录制中出现强制刷新时，再检查具体调用顺序；不要因为看到布局或绘制就先把它们视为缺陷。修复后在同一 URL、设备、数据和动作下复测，再用相同设备分组观察现场样本。DOM 变更引发的工作边界见[为什么一次 DOM 改动会增加布局或绘制工作？](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

### 优化首屏时，先处理实际 LCP 路径

打开 Performance 或 Lighthouse 录制后，先确定本次视口中的实际 LCP 元素，再看它的资源从哪里发现、何时开始请求、何时响应、何时绘制。不同设备视口、URL 参数和缓存可能让同一路由的 LCP 元素不同，因此不要只按本机一次录制假定全体用户看见同一内容。若 LCP 是图片，不要对它使用延迟加载；为图片或嵌入内容声明尺寸可以提前留出空间，减少后续内容位移。

只有录制显示某个非关键图片或脚本与关键路径竞争时，才考虑延后它。若阻塞样式表确实拖慢 LCP，可以比较内联首屏必需样式是否有收益；代价是 HTML 变大，而且首屏样式不能像独立样式表那样单独复用缓存。服务端渲染或静态输出可能让内容更早进入 HTML，但不会自动保证 LCP 或 INP 良好。HTTP 新鲜度、缓存验证与网络请求时序见[HTTP 协议与缓存](../../engineering-foundations/networking/http-protocols-and-websockets.md)；图片加载策略见[如何延迟加载图片而不损害 LCP 或布局稳定性？](#26.%20%E5%9B%BE%E7%89%87%E4%B8%8E%E5%AA%92%E4%BD%93%E8%B5%84%E6%BA%90%E6%80%8E%E6%A0%B7%E5%8A%A0%E8%BD%BD%E5%B9%B6%E4%BF%9D%E6%8C%81%E9%A1%B5%E9%9D%A2%E7%A8%B3%E5%AE%9A%EF%BC%9F)。

### 大列表要先分辨数据成本与 DOM 成本

如果报表数据量很大，不要仅凭条目数决定方案：先分别看网络传输了多少、查询/筛选和转换计算了多少、同时挂载了多少节点，以及交互中的布局和绘制花了多少时间。客户端不需要全量结果时，分页、增量加载、服务端过滤或返回汇总值可减少传输与数据处理；若用户需要大量数据但录制确认瓶颈是大量已挂载行，虚拟滚动可减少可见窗口之外的 DOM 工作。虚拟滚动不自动减少完整数据集的下载、内存或 `O(n)` 计算；它的计算、测量、焦点、键盘和辅助技术边界集中在[长报表列表何时适合虚拟滚动？](#15.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。

### 这些加载事件各自说明什么？

| 时间点 | 可以回答的问题 | 不能据此推出什么 |
|---|---|---|
| First Contentful Paint（首次内容绘制，FCP） | 第一次文本、图片等内容何时出现在页面 | 主要内容是否已就绪，或应用按钮是否可用 |
| Time to First Byte（首字节时间，TTFB） | 从导航开始到收到首个响应字节的时长 | 响应体解析和主要内容绘制是否已经完成 |
| `DOMContentLoaded`（DCL） | HTML 解析结束，解析完成后的延后脚本处理流程到达该步后，事件何时触发 | 图片加载完成、应用所有异步初始化结束或页面达到可交互状态 |
| `load` | 会延迟该事件的文档依赖资源何时完成加载 | 用户何时第一次看到内容或点击何时有反馈 |

DCL 在解析完成后的延后脚本队列执行流程之后触发；普通、无顶层 `await` 的模块会先同步执行，因此可以在事件前注册处理器。若模块在顶层 `await` 暂停、依赖异步模块，或只启动 `fetch()` / Promise 工作，后续续体不因 DCL 而一概完成。样式表也可能通过等待延后脚本而间接推迟 DCL。详细脚本与就绪条件见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)。首屏与加载里程碑并非同一个指标；First Input Delay（首次输入延迟，FID）已由 INP 取代，不属于当前核心网页指标；FCP、TTFB 和 TBT 仍可用于诊断。

> [!info]- 来源
> - 核心网页指标当前集合、良好阈值及按移动端 / 桌面端 p75 评估： [web.dev：Web Vitals](https://web.dev/articles/vitals)，当前指标说明，2024-10-31 更新；[阈值定义方法](https://web.dev/articles/defining-core-web-vitals-thresholds)，表格与百分位说明，2025-05-07 更新。核对日期：2026-11-06。
> - LCP 候选元素、时间范围及阈值： [web.dev：Largest Contentful Paint](https://web.dev/articles/lcp)，LCP 定义与合格元素，2025-09-04 更新；避免延迟加载 LCP 图片与首屏资源优先级： [优化 LCP](https://web.dev/articles/optimize-lcp)，资源发现和加载延迟章节。核对日期：2026-11-06。
> - INP 汇总范围、离群值处理、良好阈值及输入延迟/处理时长/呈现延迟： [web.dev：Interaction to Next Paint](https://web.dev/articles/inp)，定义与交互阶段，2025-09-02 更新。核对日期：2026-11-06。
> - CLS 的布局偏移、会话窗口与 p75 阈值： [web.dev：Cumulative Layout Shift](https://web.dev/articles/cls)，CLS 定义与阈值。核对日期：2026-11-06。
> - 实验室与现场数据的差异、Lighthouse 加载录制与真实交互的边界、TBT 的诊断用途： [web.dev：Why lab and field data can be different](https://web.dev/articles/lab-and-field-data-differences)，实验室/现场及 INP 小节。核对日期：2026-11-06。
> - 录制加载和运行时交互、Performance 交互轨道及各阶段提示： [Chrome DevTools：Performance features reference](https://developer.chrome.com/docs/devtools/performance/reference)，录制与 Interactions track；请求瀑布、响应头和请求时序： [Chrome DevTools：Network panel](https://developer.chrome.com/docs/devtools/network/overview/)，Requests 与 Timing 章节。核对日期：2026-11-06。
> - FCP、导航首字节、DCL 与 `load` 的计时边界： [W3C Paint Timing](https://www.w3.org/TR/2025/WD-paint-timing-20250517/)，Working Draft，2025-05-17，FCP 定义；[W3C Navigation Timing Level 2](https://www.w3.org/TR/navigation-timing-2/)，Working Draft，2026-11-02，`responseStart`、`domContentLoadedEventStart` 与 `loadEventStart`；[web.dev：Time to First Byte](https://web.dev/articles/ttfb)，导航开始到收到首个响应字节的定义，2025-11-18 更新；[WHATWG HTML：解析结束](https://html.spec.whatwg.org/multipage/parsing.html#the-end)，DCL 与加载事件算法。核对日期：2026-11-06。
> - 交互关联条目与 INP 时间分段： [W3C Event Timing](https://www.w3.org/TR/event-timing/)，Working Draft，2026-10-13，Event Timing 条目与 interaction id；[web.dev：Interaction to Next Paint](https://web.dev/articles/inp)，交互阶段。核对日期：2026-11-06。
> - FID 停止作为核心网页指标并由 INP 取代： [web.dev：First Input Delay](https://web.dev/articles/fid)，弃用说明，2024-09-09。核对日期：2026-11-06。
## 14. 如何测量并减少不必要的React工作？

**案例背景。** 报表页当前 URL 为 `/reports?sort=recent#summary`，服务端给 May、April 两行；选择 **Oldest first** 后，`sort=oldest` 让可见顺序变成 April、May。打开说明面板不改变报表数据；若这个按钮仍让大量行再次执行组件函数，可能有可优化的 React 工作；若主要时间发生在提交后的布局和绘制，memoization（记忆化）不会修复浏览器瓶颈。排序的 URL 与 Back 恢复由[浏览器历史栈机制](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)负责，本章代码聚焦面板更新与 React 成本测量。

~~~mermaid
flowchart TD
    A[重放实际交互] --> B{时间花在哪里？}
    B --> C[组件计算或列表变换]
    B --> D[提交DOM变化]
    B --> E[浏览器布局与绘制]
    C --> F[缩小状态影响范围或测量后缓存]
    D --> G[检查改变的节点和列表规模]
    E --> H[回到浏览器性能与CSS测量]
    F --> I[用同一交互复测]
    G --> I
    H --> I
~~~

### 先分清render和DOM变化

React 的 render（渲染）是组件计算下一份元素描述；render 可能没有产生任何 DOM 改动，但仍消耗 JavaScript 时间。React commit 才应用必要宿主变化；浏览器之后可能布局、绘制或合成。React DevTools Profiler（React 开发者工具性能面板）适合观察一次交互中哪些组件参与提交、render 耗时怎样变化；React 的 `<Profiler>` API 则可在指定子树中程序化记录这些时长。浏览器 Performance 面板用于看主线程脚本、样式、布局和绘制。围绕同一交互、同一数据和目标设备记录基线，再比较修改后的结果。

例如，若打开说明面板时 Profiler 显示每个 `ReportRow` 都计算了一遍，但行 props 和结果都未变，可以检查状态范围和组件边界；若 React 时间很短而布局成本明显，继续看[浏览器渲染测量](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)或[长列表](#15.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。单看 render 次数或控制台日志不能证明用户感知性能已经变好。

### React Compiler改变手工memo的默认做法

React Compiler（React 编译器）v1.0 已稳定，React 官方当前文档为 React 19.3。Compiler 是可选的构建期优化，启用后通常会自动缓存组件和 Hook 中可安全复用的工作，新代码一般不必先手写一层 `memo`、`useMemo`、`useCallback`。它是否覆盖某个文件取决于项目构建配置和可编译代码；不会把任意普通工具函数变成跨组件共享缓存。

未启用 Compiler 或需要明确边界时，这些 API 才由工程师手工使用：`memo` 可在 props 按 `Object.is` 比较相同的情况下跳过子组件更新；`useMemo` 缓存一次 render 中的计算值；`useCallback` 缓存函数引用。组件自身 state、所读 Context 等更新仍能触发 render。不要把缓存用于正确性、资源生命周期或语义身份；React 可在文档列出的情况下丢弃 `useMemo` 缓存。

下面只用本地 `reviewed` 状态演示对象身份如何影响更新；真实服务端保存采用[查询与乐观更新章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)的写入流程。

~~~jsx
import { memo, useCallback, useMemo, useState } from "react";

function ReportBoard({ initialReports }) {
  const [reports, setReports] = useState(initialReports);
  const [query, setQuery] = useState("");
  const [helpOpen, setHelpOpen] = useState(false);

  const visible = useMemo(
    () => reports.filter(report => report.title.includes(query)),
    [reports, query]
  );
  const toggleReviewed = useCallback(id => {
    setReports(current => current.map(report =>
      report.id === id ? { ...report, reviewed: !report.reviewed } : report
    ));
  }, []);

  return (
    <>
      <input value={query} onChange={event => setQuery(event.target.value)} />
      <button type="button" onClick={() => setHelpOpen(open => !open)}>
        {helpOpen ? "隐藏说明" : "显示说明"}
      </button>
      {helpOpen && <p>说明面板</p>}
      <ul>
        {visible.map(report => (
          <ReportRow key={report.id} report={report} onToggle={toggleReviewed} />
        ))}
      </ul>
    </>
  );
}

const ReportRow = memo(function ReportRow({ report, onToggle }) {
  return (
    <li>
      {report.title}
      <button type="button" onClick={() => onToggle(report.id)}>
        {report.reviewed ? "已读" : "标为已读"}
      </button>
    </li>
  );
});
~~~

这里假设 `reports` 以不可变方式更新，只创建发生变化的那一行对象。切换 `helpOpen` 时，`reports` 与 `query` 没变，`visible` 可复用；既有行对象和 `toggleReviewed` 引用也相同，于是未启用 Compiler 时 `memo` 可以跳过这些行。输入变动时过滤仍要重新计算；如果那次工作本身才是瓶颈，缓存身份不会减少算法扫描数据的成本。

### 用结果决定优化是否值得保留

为同一交互记录组件耗时、commit 数量、脚本和浏览器布局成本。检查 Compiler 的编译覆盖后，再比较它自动优化与手工 memoization 的收益；若手工缓存增加依赖复杂度却没有缩短交互，就删掉这层复杂度。稳定 key 用来保留行身份，不是性能 API；组件状态的范围则优先按所有权整理，见[如何组合组件与复用行为？](#7.%20%E5%A6%82%E4%BD%95%E5%9C%A8%20React%20%E4%B8%AD%E7%BB%84%E5%90%88%E7%BB%84%E4%BB%B6%E4%B8%8E%E5%A4%8D%E7%94%A8%E8%A1%8C%E4%B8%BA%EF%BC%9F)。

用 CSS 隐藏已挂载面板时，它仍留在 React 树中，state 和 Effect 继续存在；条件移除会卸载组件并执行 cleanup，再显示时会创建新实例。二者应按生命周期和交互需求选择。Fragment 可免去多余 DOM 包装节点，但这本身不构成可测的性能结论。

> [!info]- 来源与版本核验（React 19.3；Compiler v1.0；2026-11-06）
> - React 文档当前版本及 Compiler 稳定状态：[Versions](https://react.dev/versions)、[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，核验日期 2026-11-06；Compiler v1.0 于 2025-10-07 发布。
> - 编译器的自动缓存范围、建议先 profile、以及手工 memoization 的当前角色：[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，React 19.3 文档。
> - `memo` 的比较、state/Context 更新和 Compiler 行为：[memo](https://react.dev/reference/react/memo)；计算值与函数引用：[useMemo](https://react.dev/reference/react/useMemo)、[useCallback](https://react.dev/reference/react/useCallback)，React 19.3 文档。
> - React DevTools 的 Profiler 面板：[React Developer Tools](https://react.dev/learn/react-developer-tools)，React 19.3 文档；指定子树的程序化性能分析：[Profiler](https://react.dev/reference/react/Profiler)，React 19.3 文档。浏览器阶段见[Performance Metrics and Analysis](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。
## 15. 长报表列表何时适合虚拟滚动？

**案例背景。** 报表页从 `/reports?sort=recent#summary` 加载 May、April 两行；选择 **Oldest first** 后，`sort=oldest` 让可见顺序变成 April、May。这个小列表不需要 virtual scrolling（虚拟滚动）。当数据增长时，新的问题是：报表历史增长到十万条时，用户要看什么、客户端要拿多少数据、DOM 需要同时挂载多少行？网络量、计算量和已渲染节点是不同成本，先识别主因再选机制。

100,000 条本身不是虚拟化阈值：接收和转换这些记录在部分设备上可能可行，逐行为整个列表创建 DOM 仍可能让内存、样式与布局成本变高。行复杂度、设备、数据形状和交互共同决定该选什么，要分别测量请求、脚本、渲染和内存。

~~~mermaid
flowchart TD
    A[先确认用户要完成的任务] --> B{需要什么结果？}
    B -- 只要计数或汇总 --> C[服务端聚合]
    B -- 搜索排序一批记录 --> D[服务端过滤排序并分页]
    B -- 连续浏览且DOM是瓶颈 --> E[虚拟化当前浏览窗口]
    B -- 客户端转换计算太久 --> F[优化算法或分块/Web Worker]
    D --> G[测量传输、脚本和DOM成本]
    E --> G
    F --> G
~~~

### 十万条报表先决定哪些数据需要传输

假设报表库有 100,000 条记录。用户若只看计数或按月趋势，服务端可返回聚合值；若需搜索和按日期排序，接口可按过滤条件、稳定排序和页码/游标返回一页数据。游标要与排序规则一致；用相同时间戳加稳定 ID 作次级排序，避免新增记录时分页边界任意漂移。

分页或增量加载减少一次传输的数据量，但用户要等待后续页、看到加载/错误/结束状态。只在浏览器已经持有完整数据时做本地虚拟化，并不会减少网络传输或 JS 对象内存。若本地筛选计算才是主线程瓶颈，虚拟化也不会让全量筛选变便宜；应减少服务端返回量、改算法，或在适合时分块/放到 Web Worker（网页工作线程）。用户只需汇总时，传回汇总通常更直接。

| 主要瓶颈 | 对应处理方向 | 需要接受的代价 |
|---|---|---|
| 网络传了用户暂时用不到的记录 | 服务端过滤、排序、分页或增量请求 | 处理页状态、排序一致性和重复/遗漏边界 |
| 本地对全部记录做昂贵转换 | 服务端预计算、改算法、分块或 Web Worker（网页工作线程） | 分块会延迟完整结果；Worker 有序列化和通信成本 |
| 大量挂载节点拖慢渲染/布局 | 性能测量确认后虚拟化可见窗口 | 测量、滚动位置、焦点和辅助技术都更复杂 |
| 用户只想看总数/趋势 | 服务端聚合 | 不能交互浏览未返回的明细 |

### 固定行高怎样算出挂载窗口

先用固定高度推演。假设每行 40px，窗口高 480px，上下各多渲染 4 行（overscan，预渲染缓冲区）。用户滚到 `scrollTop = 4000px`：屏幕可见第 100 到第 111 行（从 0 编号）；上下加 overscan 后挂载 `[96, 116)` 共 20 行，而不是 100,000 行。滚动容器仍需呈现全列表约 4,000,000px 的总高度，窗口只偏移到第 96 行的位置。

~~~js
function getWindow(totalRows, scrollTop, viewportHeight, rowHeight, overscan = 4) {
  const firstVisible = Math.floor(scrollTop / rowHeight);
  const start = Math.max(0, firstVisible - overscan);
  const end = Math.min(
    totalRows,
    Math.ceil((scrollTop + viewportHeight) / rowHeight) + overscan
  );
  return {
    start,
    end,
    offsetY: start * rowHeight,
    totalHeight: totalRows * rowHeight
  };
}

const range = getWindow(100_000, 4_000, 480, 40);
// { start: 96, end: 116, offsetY: 3840, totalHeight: 4000000 }
// 已载入的报表数据只取窗口内的子数组：items.slice(range.start, range.end)
~~~

渲染时只把窗口内的报表行放在 `offsetY` 对应的位置，以 `totalHeight` 保留滚动范围；滚动容器的 `scrollTop` 和视口高度须从真实容器测量，并在滚动或尺寸变化时更新。行 key 要使用报表 ID，不能随窗口索引改变。窗口外的行一旦卸载，key 不会替它保存组件本地状态；需要保留的行状态应放在外部并按 ID 关联。若离页后还要回到原处，保存可见行 ID 与行内相对偏移，返回时再定位。

固定高度公式不适用于可换行标题、展开摘要或异步载入内容的行。此时先估计高度，再测量已挂载行的真实高度，并更新后续行的位置；若视口上方行变高/变矮，要修正滚动偏移以保住当前阅读锚点。已维护的虚拟器通常提供尺寸测量和锚点策略，但其 API 应按项目安装版本核对。

### 让被卸载的行仍能被键盘和辅助技术使用

虚拟化会卸载窗口外的节点。若焦点正落在一行按钮上，而该行随后被回收，焦点不能静默丢失；交互式列表要跟踪活动报表 ID，设计上下移动、跳转和焦点恢复，并确保当前活动项仍在 DOM 中。普通数据表若要支持浏览、打印和辅助技术，分页的原生 `<table>` 往往更易理解。只有确实采用列表框或网格等复合控件模式时，才实现该模式要求的键盘交互和焦点模型。

当 DOM 只包含集合的一部分时，WAI-ARIA 对支持的 listitem/treeitem 角色提供 `aria-posinset` 与 `aria-setsize`；表格、grid 或 treegrid 则有 `aria-rowindex` 与 `aria-rowcount`。这些数值必须对应真实位置和总数，不能用 ARIA 属性弥补错误角色或不完整键盘行为。用目标浏览器和屏幕阅读器验证滚动、读序、焦点、加载与空结果。

先以真实报表交互在[性能指标与诊断](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)里区分请求、脚本、DOM、布局和内存成本。React 组件本身的 render 成本见[React渲染优化](#14.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源与版本核验（2026-11-06）
> - 虚拟列表的实际测量、可变行高与滚动锚点：[TanStack Virtual — Virtualizer API](https://tanstack.com/virtual/latest/docs/api/virtualizer)，官方当前文档，核验日期 2026-11-06。
> - 只呈现部分集合时的位置与总量属性、以及表格/网格行位置：[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)，W3C Recommendation，2023-06-06。
> - 动态加载 listbox 项的键盘模式和 `aria-posinset`/`aria-setsize`：[WAI-ARIA APG — Listbox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)，W3C WAI 官方模式，核验日期 2026-11-06。
## 16. 语义化 HTML 表单如何支持键盘与辅助技术用户？

沿用一张合成的 2026 年 10 月订单月报：用户用键盘选择月份、地区和订单状态，提交筛选后查看订单号、地区与状态。HTML（HyperText Markup Language，超文本标记语言）标记决定控件的名称、角色和值；浏览器把当前选择序列化为 GET 请求；报表应用校验这些查询值、按约定筛选订单，再返回有标题关系的数据表。本例用 CSS（Cascading Style Sheets，层叠样式表）安排视觉布局，控件语义与原生操作由 HTML 提供。

### 先建立有语言和视口的文档

文档骨架让浏览器正确解释页面，并让辅助技术更容易定位主要内容。`<!doctype html>` 选择标准模式；根元素的 `lang` 声明主要语言；文件本身也须使用 UTF-8 编码，字符集声明不会转换错误编码的字节。`meta name="viewport"` 这个 viewport（视口）声明让窄屏布局视口的宽度与设备宽度相符，但它本身不会把固定宽度布局变成响应式布局。

~~~html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>月度订单报表</title>
</head>
<body>
  <main>
    <h1>月度订单报表</h1>
    <!-- 报表筛选表单与结果表格 -->
  </main>
</body>
</html>
~~~

让标题层级表达页面结构，用 `main`、`nav` 等 landmark（地标区域）标记主要区域。`id` 在一份文档中应唯一，既可关联标签，也可用于片段导航；`class` 可把多个元素归为同一组样式。

> [!info]- 页面元数据与内容模型
> `title` 命名浏览器标签页。`meta name="description"` 可提供搜索摘要，但搜索引擎可能改从正文生成摘要；`link rel="icon"` 提供站点图标，搜索结果是否展示图标仍由搜索引擎决定。Google Search 不使用 `meta name="keywords"` 作为排名信号。`div` 和 `span` 适合没有更具体语义的布局容器；不要因默认字号或块级显示来选择元素，因为 CSS 可以改变显示方式，却不改变元素语义。HTML 内容模型仍决定元素能否嵌套：例如，段落只接受 phrasing content（短语内容），把 `div` 设成 inline 样式也不会使它成为段落可接受的内容。

### 让控件名称、提交值和动作明确

每个字段都要有可见且程序化关联的 `label`（标签）；按钮可用自身文字命名。显式 `for`/`id` 关联能为控件提供名称，标签也扩大了可点击区域，例如点击复选框的标签可切换选中状态；把输入控件放在 `label` 内也是有效关联方式。`fieldset` 与 `legend` 把同一问题的控件组成有名称的一组。下面的 GET 表单适合非敏感筛选值，因为查询可以出现在 URL（统一资源定位符）中并被收藏或分享；敏感值不应放入 URL。

~~~html
<form action="/reports" method="get">
  <label for="month">月份</label>
  <input id="month" name="month" type="month" value="2026-10" required>

  <label for="region">地区</label>
  <select id="region" name="region">
    <option value="" selected>全部地区</option>
    <option value="north">北区</option>
    <option value="south">南区</option>
  </select>

  <fieldset>
    <legend>订单状态（可多选）</legend>
    <label><input type="checkbox" name="status" value="open"> 处理中</label>
    <label><input type="checkbox" name="status" value="closed"> 已完成</label>
  </fieldset>

  <button type="submit">筛选报表</button>
</form>
~~~

组名“订单状态（可多选）”说明两项复选框回答的是同一个问题；各选项仍要能单独辨认。辅助技术可能按平台习惯在选项前重复读出组名，所以组名保持简短。

在常见浏览器的顺序键盘导航中，用户按 Tab 会依照文档顺序到达月份、地区、两项状态和提交按钮。本例保留预设月份 `2026-10`；月控件可能包含多个键盘停靠位置，用户继续 Tab 到“地区”；这是一个单选 `<select>`，其可访问名称来自关联标签“地区”，当前选项是“全部地区”。在 HTML Accessibility API Mappings 的映射中，这种未设 `multiple`、默认大小为 1 的下拉选择控件对应 `combobox`（组合框）角色；浏览器和辅助技术的具体显示与读法可能不同。继续按 Tab 到“处理中”复选框，它以原生 checkbox（复选框）角色和标签“处理中”提供名称与选中状态；按空格键（Space）把状态从未选中切换为已选中。按 Tab 到“已完成”，再按空格键选中它。最后 Tab 到名称为“筛选报表”的按钮，按空格键或 Enter 激活。这个键盘路径最终选择 2026 年 10 月、全部地区及两种状态；本例不承诺所有平台逐字相同的播报内容。

提交后，浏览器按表单中的元素顺序构造 `name=value` 项。在本例中，没有 `name` 或被禁用的控件不产生项目；未选中的复选框和单选框也不提交；本例没有 `name` 的提交按钮不会多出一项。`checked` 和 `selected` 属性建立初始选中状态；用户操作后，提交采用控件当前的选中状态，而不是原始属性值。同名的已选复选框会分别产生项目，而且次序按文档中的控件顺序确定，不按用户点击顺序确定。浏览器按表单 URL 编码规则将项目写进 GET 查询串。本例的名称和值只包含字母、数字或连字符，所以在结果中不需转义；“都是 ASCII”本身不能推出无需编码，例如 `&`、`+` 和空格仍需要编码处理。

`type="month"` 支持时，非空值以类似 `2026-10` 的年月字符串表示：年份为至少四位且大于零的数字，后接连字符及 `01`–`12` 的两位月份。不支持该输入类型的浏览器会把它按文本输入处理，仍可输入任意字符串；它不再保证提供月份选择器或月份格式校验。`required` 可阻止常规提交空值，但服务器仍须校验真实收到的值。

| 用户选择 | GET 请求路径与查询参数 | 合成服务器按本页约定进行的筛选 |
| --- | --- | --- |
| 2026 年 10 月、全部地区、不限制状态 | `/reports?month=2026-10&region=` | 返回当月所有地区和状态的订单 |
| 2026 年 10 月、全部地区、处理中与已完成 | `/reports?month=2026-10&region=&status=open&status=closed` | 匹配任一所选状态；这是下方结果表对应的请求 |
| 2026 年 10 月、北区、只选处理中 | `/reports?month=2026-10&region=north&status=open` | 仅匹配北区且处于处理中的订单 |
| 2026 年 10 月、北区、未选状态 | `/reports?month=2026-10&region=north` | 仅匹配北区，不限制状态 |

这些业务含义由合成报表应用定义，不是 HTML 或 URL 自动带来的规则：`month` 必须是一个有效的年月；缺失、空或格式无效时，服务器返回字段错误并要求重新选月，不静默改用其他月份。有效但没有订单的月份返回空结果和说明。`region=` 或省略 `region` 都表示全部地区；`north`、`south` 分别表示北区、南区，其他非空值返回错误。省略全部 `status` 表示不限制状态；多个 `status` 值组成一个列表，命中其中任一值即可；未知状态值返回错误。

结果表明确对应第二行请求 `/reports?month=2026-10&region=&status=open&status=closed`，因此可同时显示来自北区的处理中订单 `A-1042` 与来自南区的已完成订单 `A-1043`。浏览器负责提交查询值；应用负责按上面的契约筛选并生成结果。

> [!info]- 相邻表单控件的边界
> `type="password"` 只遮住屏幕显示，不会加密传输或替代安全存储；文件选择器的 `accept` 只是可选类型提示，服务器仍须校验收到的文件。`select multiple` 也可让一个字段提交多个同名值。相同 `name` 的单选按钮保证同组只能选择一个值，复选框则可提交多个已选值。表单里的按钮默认可能提交表单，因此写明 `type="submit"`、`type="reset"` 或 `type="button"`；页面导航用有真实 `href` 的链接，`href="#"` 会导航到当前文档顶部，不能当作无动作的占位符。若地区改变会影响下一级门店选项，应用更新选项时还要清除不再有效的旧门店值；选项暂不可用时应明确告知用户。

### 让报表结果保持数据表语义

当数据的行和列本身有意义时，用表格标记，而不是用 CSS Grid（网格布局）伪造表格语义。`caption` 说明表格主题；`th scope="col"` 给出列标题，`scope="row"` 标记本行的识别值。这样读者可以把单元格 `A-1042` 关联到“订单号”，并把“处理中”关联到“状态”列与该行；具体导航方式和播报文字随浏览器与辅助技术而异。

~~~html
<table>
  <caption>2026 年 10 月订单结果（全部地区，处理中或已完成）</caption>
  <thead>
    <tr>
      <th scope="col">订单号</th>
      <th scope="col">地区</th>
      <th scope="col">状态</th>
    </tr>
  </thead>
  <tbody>
    <tr><th scope="row">A-1042</th><td>北区</td><td>处理中</td></tr>
    <tr><th scope="row">A-1043</th><td>南区</td><td>已完成</td></tr>
  </tbody>
</table>
~~~

> [!info]- 其他内容结构与窄屏表格
> `rowspan` 或 `colspan` 会占据后续单元格位置；例如三列表格中，上行一个 `rowspan="2"` 已占下行第一列，下行只再写两个单元格。无序项目用 `ul`，有序步骤用 `ol`，术语与解释用 `dl`、`dt`、`dd`；不应用连续空格或非断行空格排版。窄屏宽表可以放入局部横向滚动容器，避免整个页面横向溢出，详见[固定与流动内容的布局选择](#21.%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F)。

### 键盘、焦点与校验错误

Tab 顺序通常跟随有意义的 HTML 文档顺序；`:focus-visible` 或 `:focus` 样式应保留可辨认、未被完全遮挡的焦点提示。不要只用颜色、图标或位置表达错误状态。CSS Flexbox（弹性盒布局）的 `order` 和 Grid（网格布局）的放置规则可改变视觉位置，却不会改变默认顺序导航或非视觉阅读顺序；CSS Display Level 4 另定义 `reading-flow`、`reading-order` 来改变特定布局下的阅读/焦点顺序，本例没有使用它们。必须让视觉和阅读顺序一致时，应先检查源码顺序，而不是用视觉移动掩盖结构问题。

通知邮箱是同一报表页上的另一个独立表单。原生约束可以阻止空邮箱或格式错误的邮箱提交，并在字段上触发可取消的 `invalid` 事件。若应用取消浏览器的原生错误提示，表单仍因约束失败而不能提交，但应用仍需提供可发现的错误通知并更新字段状态。下面单字段示例使用 `aria-describedby` 关联帮助和错误文本，用 `aria-invalid` 标出当前错误；动态显示错误并不保证每种辅助技术都会立刻播报它，因此示例还会把焦点移回邮箱字段。

~~~html
<form action="/notification-settings" method="post">
  <label for="email">通知邮箱</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">用于接收筛选完成通知。</p>
  <p id="email-error" hidden></p>
  <button type="submit">保存通知设置</button>
</form>
~~~

在表单标记之后运行以下脚本；若使用外部脚本，也可用 `defer` 确保表单节点已经创建：

~~~js
const email = document.querySelector("#email");
const error = document.querySelector("#email-error");
let hasShownError = false;

function updateEmailError() {
  const message = email.validity.valueMissing
    ? "请填写通知邮箱。"
    : email.validity.typeMismatch
      ? "请输入有效的邮箱地址。"
      : email.validity.valid
        ? ""
        : email.validationMessage || "请检查通知邮箱。";

  error.textContent = message;
  error.hidden = message === "";
  if (message) {
    email.setAttribute("aria-invalid", "true");
  } else {
    email.removeAttribute("aria-invalid");
  }
}

email.addEventListener("invalid", (event) => {
  event.preventDefault();
  hasShownError = true;
  updateEmailError();
  email.focus();
});

email.addEventListener("input", () => {
  if (!hasShownError) return;
  updateEmailError();
  if (email.validity.valid) hasShownError = false;
});
~~~

第一次提交空值时，`validity.valueMissing` 使应用显示“请填写通知邮箱。”。若用户改成 `person@`，`validity.typeMismatch` 使错误继续显示并更新为“请输入有效的邮箱地址。”，不会误显示为已恢复。输入合法的 `team@example.com` 后，错误文字清空、错误段落重新隐藏、`aria-invalid` 移除。只有当字段满足原生约束时，表单才会按默认行为提交到服务器；服务器还应再次校验输入。

| 时刻 | 字段值 | 可见与程序化状态 | 焦点 |
| --- | --- | --- | --- |
| 初始 | 空 | 帮助说明显示；错误段落为空且带 `hidden`，没有 `aria-invalid` | 由用户决定 |
| 提交空值后 | 空 | 显示“请填写通知邮箱。”、移除 `hidden`、设置 `aria-invalid="true"` | 应用移至邮箱字段 |
| 改成非空但格式错误 | `person@` | 更新为格式错误说明，保留 `aria-invalid="true"` | 留在邮箱字段 |
| 修正后 | `team@example.com` | 清空错误、恢复 `hidden` 并移除 `aria-invalid` | 留在字段，用户可继续 Tab |

> [!info]- HTML 字符引用与用户输入
> 在普通 HTML 文本上下文中，源码 `&lt;` 和 `&amp;` 分别显示为 `<` 和 `&`；`&nbsp;` 表示不换行空格，不应用来代替 CSS 间距。字符引用依所在解析状态处理：例如 `script` 中的 script data 与 `style` 中的 RAWTEXT 状态不会按普通正文那样解码字符引用。它也不是动态字符串安全插入的替代品；把用户输入作为普通文字显示时，应使用 DOM（Document Object Model，文档对象模型）的文本接口，而不是把拼接后的字符串当作标记解析。

> [!info]- 来源
> - 文档骨架、语言、地标、内容模型与文本结构：WHATWG HTML Living Standard，§3–4；更新时间 2026-11-11：[document semantics and metadata](https://html.spec.whatwg.org/multipage/semantics.html)、[grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)，检查于 2026-11-11。
> - 表单标签、分组、输入类型、当前控件状态、按钮、月字符串和约束验证：WHATWG HTML Living Standard，§4.10；更新时间 2026-11-11：[forms](https://html.spec.whatwg.org/multipage/forms.html)、[input](https://html.spec.whatwg.org/multipage/input.html)、[months](https://html.spec.whatwg.org/multipage/common-microsyntaxes.html#months)，检查于 2026-11-11。
> - 表单项按控件顺序构造、重复名称与 GET 查询序列化：WHATWG HTML Living Standard，§4.10.22，[form control infrastructure](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-form-data-set)；URL 表单编码算法：[WHATWG URL Standard](https://url.spec.whatwg.org/#concept-urlencoded-serializer)，检查于 2026-11-11。
> - 单选 `<select>` 的组合框映射：W3C HTML Accessibility API Mappings 1.0，§3.5.116，Working Draft（2026-10-12）：[HTML AAM](https://www.w3.org/TR/2026/WD-html-aam-1.0-20261012/)，检查于 2026-11-11。
> - 标签、分组、错误通知和提交后错误处理：W3C WAI Forms Tutorial，[Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/)、[Grouping Controls](https://www.w3.org/WAI/tutorials/forms/grouping/)、[User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/#after-submit)，检查于 2026-11-11。复选框 Space 与按钮 Space/Enter：WAI-ARIA Authoring Practices Guide，[Checkbox keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/#keyboardinteraction)、[Button keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/button/#keyboardinteraction)，检查于 2026-11-11。
> - 结果表格标题、行列标题关系与跨行跨列：WHATWG HTML Living Standard，§4.9；更新时间 2026-11-11：[tables](https://html.spec.whatwg.org/multipage/tables.html)，检查于 2026-11-11。
> - `aria-describedby` 隐藏内容引用与文本接口：W3C Accessible Name and Description Computation 1.2，§4.3.2，[computation steps](https://www.w3.org/TR/accname-1.2/#computation-steps)；WHATWG DOM Standard，[`Node.textContent`](https://dom.spec.whatwg.org/#dom-node-textcontent)，检查于 2026-11-11。
> - 焦点可见、不被完全遮挡、状态不只用颜色：W3C WCAG 2.2，Success Criteria 2.4.7、2.4.11、1.4.1，Recommendation（2024-12-12）：[WCAG 2.2](https://www.w3.org/TR/WCAG22/)，检查于 2026-11-11。
> - `order` 对非视觉与顺序导航的作用，以及 `reading-flow`、`reading-order`：W3C CSS Display Level 4，§3.1、§4，Working Draft（2025-11-06）：[CSS Display Level 4](https://www.w3.org/TR/css-display-4/#reading-flow)，检查于 2026-11-11。Flexbox 顺序：W3C CSS Flexible Box Layout Module Level 1，§5.4；Grid 放置：W3C CSS Grid Layout Module Level 2，§4，检查于 2026-11-11。
> - 字符引用、HTML 解析状态和动态文本内容：WHATWG HTML Living Standard，§13.2.5、§13.5；更新时间 2026-11-11：[HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html)、[named character references](https://html.spec.whatwg.org/multipage/named-characters.html)，检查于 2026-11-11。
> - Google 搜索摘要、站点图标和 meta keywords：Google Search Central，[snippets](https://developers.google.com/search/docs/appearance/snippet)、[favicon](https://developers.google.com/search/docs/appearance/favicon-in-search)、[supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)，检查于 2026-11-11。
## 17. CSS 级联如何决定最终生效的声明？

案例背景：2026 年 10 月的订单月报要给数据行交替着色，并单独加粗其中一行。表格由一行表头和数据 A、数据 B、数据 C 三行组成。HTML（HyperText Markup Language，超文本标记语言）给出表格与行的结构；CSS（Cascading Style Sheets，层叠样式表）的层叠（cascade，亦称级联）回答同一元素、同一属性有多条适用声明时，哪一条胜出。浏览器先筛掉不适用的声明，再按来源、封装上下文、元素附加样式、层叠层（cascade layer）、选择器权重（specificity）、作用域接近度及声明顺序比较。若胜出的值是 CSS-wide keyword（CSS 全局关键字），还要按关键字决定继承、初始值或回退范围。

### 先确认选择器匹配到谁

结构伪类只数元素兄弟，源码中的空白文本节点不占位置；位置从 1 开始：

~~~css
tbody > tr:nth-child(even) { background: #f4f7fb; }
tbody > tr:nth-child(even of .data-row) { font-weight: 600; }
~~~

~~~html
<table>
<tbody>
  <tr class="heading"><th>本月订单</th></tr>
  <tr class="data-row"><td>数据 A</td></tr>
  <tr class="data-row"><td>数据 B</td></tr>
  <tr class="data-row"><td>数据 C</td></tr>
</tbody>
</table>
~~~

| 行 | 所有 `tr` 中的序号 | 筛出 `.data-row` 后的序号 | `:nth-child(even)` | `:nth-child(even of .data-row)` |
| --- | ---: | ---: | --- | --- |
| 表头 | 1 | — | — | — |
| 数据 A | 2 | 1 | 命中 | — |
| 数据 B | 3 | 2 | — | 命中 |
| 数据 C | 4 | 3 | 命中 | — |

第一条规则改 A、C 的背景，第二条改 B 的字重；它们没有给同一元素的同一属性竞争。把 `.data-row` 放在伪类前面，如 `tr.data-row:nth-child(even)`，只要求匹配行有该类，不会改变 `:nth-child()` 对所有元素兄弟的计数范围，因此仍命中 A、C。

`:first-child`、`:last-child`、`:nth-child()` 和 `:nth-last-child()` 都按元素兄弟位置匹配；`nth-last-child()` 从末尾倒数。`:nth-child(2n+1)` 表示第 1、第 3 等位置；这里的 `n` 依次取非负整数。写成 `:nth-child(表达式 of S)` 时，先用选择器列表 `S` 筛选，再按筛选后的位置计数；例如 `:nth-last-child(-n+2 of .data-row)` 可选中数据 B、数据 C。相应的 `-of-type` 形式只在同一父元素下按元素类型计数，即匹配相同命名空间和标签名的兄弟。

选择器权重依 `(ID, 类/属性/伪类, 元素/伪元素)` 三列从左向右比较。上面第一条 `tbody > tr:nth-child(even)` 是 `(0, 1, 2)`：一个伪类、两个类型选择器。第二条 `tbody > tr:nth-child(even of .data-row)` 是 `(0, 2, 2)`，因为 `of S` 中最具体选择器 `.data-row` 再贡献一个类权重。`:nth-child(... of S)` 和 `:nth-last-child(... of S)` 各自先计一个伪类，再加 `S` 中最具体选择器的权重；权重取 `S` 整个列表中的最大值，即使贡献最大值的分支没有匹配兄弟，也仍会计入。比如 `of .data-row, #not-in-report` 中的 ID 分支仍贡献 ID 权重，但目标行仍须匹配列表中的某个分支。`:not()`、`:is()`、`:has()` 本身不额外计一个伪类，而取参数列表中最具体选择器的权重；`:where()` 本身及其参数权重为零。

当 `content` 属性的计算值不是 `none`、且盒生成未被抑制时，`::before` 和 `::after` 分别在元素实际内容前、后生成盒子；它们不是新增的 DOM（Document Object Model，文档对象模型）节点。例如，可以用装饰括号包住报表中的状态：

~~~html
<span class="status">处理中</span>
~~~

~~~css
.status::before { content: "［"; }
.status::after { content: "］"; }
~~~

这里的括号只是装饰，去掉样式后“处理中”仍在文档中。清除浮动技巧（clearfix）也可用 `::after` 空伪元素生成辅助盒：

~~~css
.group::after {
  content: "";
  display: table;
  clear: both;
}
~~~

这个辅助盒参与正常流；`clear: both` 将它排到两侧浮动之后，容器的自动高度因此包含这段空间。不要只用生成内容表达唯一的状态文字、说明或交互功能；用户关闭或替换样式时，它可能消失，也不一定像正文一样便于选取。WAI 旧的 F87 失败技术已经标记过时，当前浏览器和辅助技术对生成文字的支持也已改善，因此不能说所有生成文字都会被辅助技术隐藏；本例仍把有意义的状态保留为实际文本。`::before` 和 `::after` 也不会在 `<img>` 等被替换元素上生成。

### 按级联步骤找到胜出声明

比较之前，先确认样式表适用于当前文档、条件规则为真、选择器匹配目标，且属性和值在解析阶段语法有效；不满足这些条件的声明不会进入层叠。含自定义属性替换函数 `var()` 的值则可能在赢得层叠后、计算值阶段才发现替换结果不符合属性语法。两种情况的结果不同：

~~~css
.parse-invalid {
  background-color: red;
  background-color: 20px;
}

.var-invalid {
  background-color: red;
  --surface: 20px;
  background-color: var(--surface);
}
~~~

~~~html
<p class="parse-invalid">解析阶段无效</p>
<p class="var-invalid">替换后无效</p>
~~~

第一条规则的 `20px` 在解析时无效，被丢弃，所以背景仍为红色。第二条的 `var()` 在解析时有效，先赢得层叠；替换出 `20px` 后才对 `background-color` 无效，此值按 `unset` 处理。由于 `background-color` 不继承，它取初始透明值，不会回头恢复已被抛弃的红色声明；若这种失效发生在继承属性上，则按继承处理。以下步骤针对同一元素的同一属性；前一步已分出高下时，后面的步骤不再参与：

1. **来源与重要性。** 从高到低为过渡中的声明、用户代理 `!important`、用户 `!important`、作者 `!important`、动画声明、作者普通声明、用户普通声明、用户代理普通声明。用户代理是浏览器或其他用户代理提供的默认样式。某些宿主语言也会把 `bgcolor` 这类非 CSS 表现提示映射到作者表现提示来源，其优先级位于一般用户来源与作者来源之间；本例没有使用这种提示。`!important` 会改变优先次序，也会让后续覆盖更难维护。
2. **封装上下文。** 跨越 Shadow DOM（影子 DOM）等边界比较规则时，普通声明由外层上下文优先，重要声明由内层上下文优先。
3. **元素附加样式。** 在来源、上下文和重要性相同的情况下，直接写在元素 `style` 属性（内联样式）中的声明优先于选择器匹配到的规则；它并不会越过前面的来源与重要性比较。
4. **层叠层。** 同一来源和上下文内，普通声明由层顺序较后的层优先，未分层普通声明排在所有显式层之后。重要声明的层序反转，因此显式层中的重要声明优先于未分层的重要声明。
5. **选择器权重。** 只在以上步骤持平时比较。ID 列先比；前一列一旦分出高下，后一列不能抵消。通配符 `*` 与组合符 `>`、`+`、`~` 不增加权重。
6. **作用域接近度与声明顺序。** 至少有一条规则位于 `@scope` 中、且两条规则的作用域根不同或其中一条无作用域根时，前面步骤（包括选择器权重）持平后，从作用域根到目标的代际或兄弟元素跳数较少者优先；没有作用域根的规则视为无限跳。`@scope` 前置的根选择器不计入规则自身的选择器权重。最后由样式表顺序打平局；同一文件中可把后出现的声明理解为后者胜出，被 `@import` 引入的样式表则按导入位置参与顺序比较。

下面三条规则的选择器权重都是 `(0, 1, 0)`。根元素的 ID 不会加入 `@scope` 内部规则的选择器权重；对 `.status` 而言，`#monthly-report` 根有两个祖先跳数，`.status-group` 根有一个，无作用域规则视作无限跳，因此较近作用域胜出，即使无作用域规则写在最后：

~~~html
<section id="monthly-report">
  <div class="status-group"><p class="status">处理中</p></div>
</section>
~~~

~~~css
@scope (#monthly-report) { .status { color: #8a3b00; } }
@scope (.status-group) { .status { color: #555; } }
.status { color: purple; }
~~~

下面两条作者普通样式都给同一个报表状态元素设置 `color`，且其他优先步骤都相同。`#status` 的选择器权重 `(1, 0, 0)` 高于三个类 `(0, 3, 0)`，所以即使类规则写在后面，ID 规则仍胜出：

~~~html
<p id="status" class="report status warning">待处理</p>
~~~

~~~css
#status { color: #8a3b00; }
.report.status.warning { color: #b00020; }
~~~

### 用层次组织样式来源

层叠层（cascade layer）可以把 reset、第三方组件、业务组件和工具类样式分开。先声明层顺序，再让选择器保持适度的权重：

~~~css
@layer reset, components, utilities;

@layer reset {
  .revert-important.has-reset { color: green; }
}

@layer components {
  #layer-status { color: #8a3b00; }
  .revert-normal { color: #8a3b00; }
  .revert-important { color: revert-layer !important; }
}

@layer utilities {
  .text-muted { color: #555; }
  .revert-normal { color: revert-layer; }
  .revert-important { color: #555 !important; }
}
~~~

~~~html
<p id="layer-status" class="text-muted">状态由工具类设为灰色</p>
<p class="revert-normal">普通声明回退到组件层</p>
<p class="revert-important has-reset">重要声明回退到 reset 层</p>
<p class="revert-important">没有较低优先级作者声明时回退到用户代理来源</p>
~~~

第一个状态同时匹配 `components` 层的 ID 选择器与 `utilities` 层的单类选择器。普通声明按层列表从前到后排优先级，因此较后的 `utilities` 声明胜出，即使它的选择器权重较低。未分层普通声明排在所有显式层之后；重要声明的层序反转，因此较早层的 `!important` 声明优先于较晚层及未分层的重要声明。层只在相同来源和封装上下文内排序，不能越过来源、重要性或封装上下文等更早步骤。

对于层叠层中的声明，`revert-layer` 不是“选前一条规则”：它会让该属性重新计算，仿佛当前层以及这一层的普通级与重要级两个层序位置之间的声明都没有为此元素指定该属性。普通工具层的 `revert-layer` 因而显出组件层的棕色。组件层中的重要声明回滚时，工具层的重要灰色处于被略去的区间；较早 `reset` 层的普通绿色仍可胜出。没有该 reset 声明时，本例同一作者来源没有剩余的低优先级值，于是继续回退到前一来源，露出用户代理默认颜色。

### 级联之后，属性怎样继承？

> [!info] 五个常见 CSS-wide keyword
> `inherit` 明确取父元素的计算值，即使该属性通常不继承；`initial` 取属性定义的初始值；`unset` 按属性是否继承来选择，继承属性等同 `inherit`，非继承属性等同 `initial`。作者来源上的 `revert` 会去掉作者来源（包括动画来源）的该属性声明，露出用户来源结果；若没有用户样式，则露出用户代理来源。例如对 `<em>` 写 `font-style: revert`，浏览器的默认斜体可重新生效。对于本节的层叠层规则，`revert-layer` 会去掉当前层及其普通级与重要级层序位置之间的声明；若同一来源没有剩余的低优先级值，就回退到前一来源，见层叠层示例。两种回滚关键字都不等同于 `unset`。

没有胜出声明时，继承属性从父元素取得计算值，非继承属性取初始值。父元素选择器的选择器权重不会“传给”子元素：

~~~html
<article id="report">
  <span class="status">处理中</span>
</article>
~~~

~~~css
#report { color: #222; font-family: system-ui, sans-serif; margin: 2rem; }
.status { color: #8a3b00; }
~~~

`span` 自己的 `color` 声明胜出，它仍从父级继承 `font-family`；父级的 `margin` 不会继承。`color`、`font-family` 和 `line-height` 是默认继承属性；`width`、`padding`、`margin`、`display`、`position` 默认不继承，具体以属性定义为准。

数字、长度和百分比行高的继承结果不同。父元素字号为 `20px` 时，`line-height: 1.5` 计算并继承为数字 `1.5`；字号为 `12px` 的子元素据此得到 `12 × 1.5 = 18px` 的行高。父元素设 `line-height: 30px` 或 `line-height: 150%` 时，两者都先计算为 `30px` 长度；子元素继承长度 `30px`，即使字号降到 `12px`，行高仍是 `30px`。

父级链接的下划线还可能沿盒树绘制到后代文字。文本装饰不是普通继承属性，而是沿盒树传播；对子级 `<em>` 写 `text-decoration: none` 不会取消祖先建立的下划线，应修改建立该装饰的元素规则。

### 文本元素怎样表达不同含义？

在订单月报中，用 `h1`–`h6` 标记标题层级，例如页面主标题用 `h1`、月份区块标题用 `h2`；说明段落用 `p`。标题层级表达文档结构，字号和间距交给 CSS。只有换行本身有意义时才用 `br`；`hr` 表示段落级内容之间的主题转换。`strong` 表示重要性、严重程度或紧急性，`b` 只是引起注意；`em` 表示语气重读，`i` 表示另一种语调或与正文表达方式不同的内容，例如术语。`del` 和 `ins` 标记删除与插入的内容，`s` 表示内容已不再准确，`u` 可标记错别字等非文本注记，例如在“订单状太”中用它标出误写的“太”。CSS 可以改变这些元素的外观，不能替换它们表达的文档语义。

### 报表文字和背景样式怎样组合？

`font-family`（字体族）按书写顺序尝试字体，末尾应给出 `sans-serif`、`serif` 等通用族作为回退。`text-align`（文本对齐）对齐块内的行文字；`text-indent`（首行缩进）设置段落首行缩进。它们不会替代文本语义。只想调整字体的一个方面时，使用对应长属性，例如 `font-weight`（字重），避免顺手覆盖其他设置。

> [!info] `font` 简写会重置它的字体子属性
> `font`（字体简写）为相应字体长属性提供声明；这些长属性仍分别参与前述单属性层叠。规范列为 `font` 子属性的其他属性也会先重置为初始值，因此它可能把 `font-style: italic` 重置为 `normal`，并把 `font-kerning: none` 重置为 `auto`。需要保留其他字体设置时，改用目标长属性。

~~~css
.report-title {
  font-style: italic;
  font-kerning: none;
  font: 600 1.25rem/1.3 system-ui, sans-serif;
}

.report-summary {
  font-size: 1rem;
  line-height: 1.5;
  text-indent: 1em;
}

.report-total {
  text-align: end;
  font-weight: 700;
}
~~~

`background-image`（背景图像）既可用 `url()` 指向图片，也可用 `linear-gradient()`（线性渐变）生成渐变；图像层绘制在 `background-color`（背景色）上方。背景色可透过图片透明处显示，也能在图片未加载时提供底色。报表状态仍要作为正文文字保留，不能只靠背景颜色或渐变表达。

`background-size`（背景尺寸）的 `cover` 会等比缩放并覆盖整个背景区，可能裁去图片边缘；`contain` 会等比缩放并完整放入背景区，可能留下空白。简写中用斜线分隔位置和尺寸；`background` 还会把未写出的背景子属性重置为初始值：

下面的 `/assets/report-cover.jpg` 只是示例路径。

~~~css
.report-cover {
  background: center / cover no-repeat url("/assets/report-cover.jpg");
}
~~~

只想调整一个背景属性时，使用对应长属性，避免简写顺带重置其他图层设置：

~~~css
.report-status {
  color: #704000;
  background-color: #fff3d6;
  background-image: linear-gradient(180deg, rgb(255 255 255 / 35%), transparent);
}
~~~

属性选择器例如 `[data-state="warning"]` 可把显式状态映射到样式；扁平、可维护的类选择器通常比逐层增加选择器权重更容易覆盖。CSS-in-JS（在 JavaScript 中生成或组织 CSS）生成的类名也仍参与浏览器层叠。

内联关键 CSS 有时可省去首屏样式表请求的等待；它会增大首次 HTML 响应；若后续样式表仍含同一规则，这些内容就同时存在于 HTML 和 CSS 两份资源中。是否有收益应结合缓存、载入路径与实测判断，而不是把它当作选择器加速技巧，参见[网页性能测量与诊断](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - 标题、段落、换行、主题分隔、强调与修订文本的 HTML 语义：WHATWG HTML Living Standard，[Sections](https://html.spec.whatwg.org/multipage/sections.html)、[Grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[Text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)，更新时间 2026-11-11，检查于 2026-11-11。
> - 声明过滤、来源/重要性、层排序及 `revert` / `revert-layer` 的回滚：W3C CSS Cascading and Inheritance Level 5，§5–7.3.5，Candidate Recommendation Snapshot（2022-01-13）：[CSS Cascade Level 5](https://www.w3.org/TR/css-cascade-5/)，检查于 2026-11-12。
> - `@scope` 接近度的跳数、无作用域根的无限跳及根选择器不计入规则权重：W3C CSS Cascading and Inheritance Level 6，§2.1、§2.5.1，Exploratory Working Draft（2024-09-06；差异草案明确建议实现时以 Level 5 为参考）：[CSS Cascade Level 6](https://www.w3.org/TR/css-cascade-6/)，检查于 2026-11-12。
> - 结构伪类计数、`of S` 筛选和选择器权重计算：W3C Selectors Level 4，§13.3–13.4、§15，Working Draft（2026-01-22）：[Selectors Level 4](https://www.w3.org/TR/selectors-4/)，检查于 2026-11-11。
> - `::before`、`::after` 生成位置和替换元素限制：W3C CSS Pseudo-Elements Level 4，§4.1，Working Draft（2025-06-27）：[CSS Pseudo-Elements](https://www.w3.org/TR/css-pseudo-4/#generated-content)，检查于 2026-11-12。
> - `content: normal` 在 `::before`、`::after` 上计算为 `none`：W3C CSS Generated Content Level 3，§1，Working Draft（2025-12-04）：[CSS Generated Content](https://www.w3.org/TR/css-content-3/)，检查于 2026-11-12。
> - `display: none` 不生成盒子：W3C CSS Display Level 3，§2.5，Candidate Recommendation Draft（2026-06-05）：[CSS Display](https://www.w3.org/TR/css-display-3/#box-generation)，检查于 2026-11-12。
> - `clear: both` 将正常流块级盒推到先前的双侧浮动下方，正常流子盒也计入父级自动高度：W3C CSS 2.2，§9.5.2、§10.6.3，First Public Working Draft（2016-04-12）：[CSS 2.2 floats](https://www.w3.org/TR/CSS22/visuren.html#flow-control)、[block auto height](https://www.w3.org/TR/CSS22/visudet.html#normal-block)，检查于 2026-11-12。
> - `var()` 替换后的值在计算值阶段无效时，不会恢复先前声明：W3C CSS Custom Properties for Cascading Variables Level 1，§3.1，Candidate Recommendation Snapshot（2022-06-16）：[CSS Variables](https://www.w3.org/TR/css-variables-1/#invalid-variables)，检查于 2026-11-12。
> - 将 CSS 生成内容用于装饰的适用条件：W3C WAI WCAG 2.2 Technique C9（2026-01-12 更新）；关于非装饰性生成文字的旧失败技术 F87 已标记过时，且指出当前支持状况不应一概视为失败：[C9](https://www.w3.org/WAI/WCAG22/Techniques/css/C9)、[F87（Obsolete）](https://www.w3.org/WAI/WCAG22/Techniques/failures/F87)，检查于 2026-11-11。
> - 状态信息不能只用颜色表达：W3C Web Content Accessibility Guidelines 2.2，Success Criterion 1.4.1，Recommendation（2024-12-12）：[Use of Color](https://www.w3.org/TR/WCAG22/#use-of-color)，检查于 2026-11-11。
> - 文本装饰的盒树传播：W3C CSS Text Decoration Level 3，§2，Candidate Recommendation Draft（2022-05-05）：[CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/#line-decoration)，检查于 2026-11-11。
> - 字体属性、字体族回退、`font` 子属性重置：W3C CSS Fonts Level 4，§2.7、§3，Working Draft（2026-11-04）：[CSS Fonts](https://www.w3.org/TR/css-fonts-4/)，检查于 2026-11-12。
> - 数字、长度和百分比 `line-height` 的计算及继承：W3C CSS Inline Layout Level 3，§5.1，Working Draft（2024-12-18）：[CSS Inline Layout](https://www.w3.org/TR/css-inline-3/)，检查于 2026-11-12。
> - 背景层、背景色、图像、`background` 简写与尺寸：W3C CSS Backgrounds and Borders Level 3，§2.1–2.3、§2.9–2.10，Candidate Recommendation Draft（2024-03-11）：[CSS Backgrounds and Borders](https://www.w3.org/TR/css-backgrounds-3/)，检查于 2026-11-12。
> - 内联关键 CSS 的适用情况与缓存、HTML 体积权衡：web.dev [Optimize resource loading](https://web.dev/learn/performance/optimize-resource-loading/)，Inline critical CSS，2023-11-01 更新，检查于 2026-11-11。
## 18. CSS 如何计算元素盒子的尺寸？

固定的 `width` 和 `height` 要先看量到哪一条边。默认 `content-box` 把声明值给内容区；`border-box` 把它给边框盒，再从中扣除 padding 与 border。margin 始终在 border 外。本页用宽度演算四层；高度遵循同样的边缘规则，但 `min-height`、`max-height` 和布局约束可能改变浏览器最后采用的高度。

### 用报表筛选面板演算宽度

报表页面每个父级内容区宽 `360px`。每次只放一个筛选面板，并从父级内容区左边界 `x=0` 开始，所以面板左边框位于左 margin 之后的 `x=12px`。筛选面板左右各有 `16px` padding、`1px solid` border 和 `12px` margin。为单独观察固定宽度，让它以 `inline-block` 排在父级的一行中：它按块盒计算宽高，但像行内内容一样占据这一行。父级固定宽 `360px` 且不换行；不设 `min-width` 或 `max-width`，也不让 Flex/Grid 布局改写尺寸。图中的虚线是父级内容区边界；斜线表示透明的 margin 区域。

~~~css
.track { width: 360px; white-space: nowrap; }
.panel {
  display: inline-block;
  width: 360px;
  margin-inline: 12px;
  padding-inline: 16px;
  border: 1px solid;
}
.panel.border-box { box-sizing: border-box; }
.panel.border-box.fit { width: 336px; }
~~~

图表的三行分别使用类组合 `panel`、`panel border-box` 和 `panel border-box fit`；每种情况都在独立的 `360px` 父级中计算。

从里到外，padding box 是内容区加 padding；border box 再包住 border；margin box 最外面再加 margin。

![固定宽度子项的content-box、border-box与父级边界尺寸](../../frontend/html-css/resources/box-model-and-bfc-width-comparison.svg)

默认 `content-box` 的 `width: 360px` 量的是内容区。加上两侧 padding 后，padding box 是 `360 + 16 × 2 = 392px`；再加两侧 border，border box 是 `394px`；最后加 `24px` margin，margin box 是 `418px`。由于左 margin 位于父区内，子项边框盒向右越出父区 `46px`，margin box 外缘总共越出 `58px`。

改成 `box-sizing: border-box`，声明的 `360px` 包含内容、padding 和 border：

> [!example] border-box，width 360px
> 内容区 `360 - 32 - 2 = 326px`；padding box `358px`；border box `360px`。margin box 是 `360 + 24 = 384px`，所以边框盒越出父区 `12px`、最外侧 margin box 越出 `24px`。

若父区宽 `360px`，并希望左右 margin 各 `12px` 后也完全放得下，可把 border-box 宽度设为 `336px`：内容区 `302px`，padding box `334px`，border box `336px`，margin box 恰为 `360px`。这把原来的边界计算闭合为一个可用宽度：父级宽度先扣掉两侧 margin，剩余值就是边框盒上限。

| 声明值实际控制的宽度 | 内容区 | padding box | border box | margin box |
|---|---:|---:|---:|---:|
| `content-box; width:360px` | `360px` | `392px` | `394px` | `418px` |
| `border-box; width:360px` | `326px` | `358px` | `360px` | `384px` |
| `border-box; width:336px` | `302px` | `334px` | `336px` | `360px` |

表只计算 `width` 对该盒生效、浏览器采用值未被其他规则改写的情形。像普通 `span` 这样的非替换行内盒不能直接用 `width` 定宽；`min-width`、`max-width` 或 Flex/Grid 的尺寸计算也会改变最后采用的宽度。`height` 同理：只有固定值实际采用时，`box-sizing` 才决定它量到内容盒还是边框盒；最小/最大高度和布局也可能改写最终尺寸。`box-sizing` 也影响 `flex-basis` 等 sizing properties 的固定值解释。

若 border-box 声明宽度只有 `20px`，而两侧 padding 与 border 合计 `34px`，内容区不会变成负数：内容宽度下限为 `0px`，边框盒仍会长到 `34px`。保留两侧 `12px` margin 时，margin box 是 `58px`。

常见重置让页面元素和伪元素采用 border-box，使组件声明宽度更接近可见边框宽度：

~~~css
*, *::before, *::after {
  box-sizing: border-box;
}
~~~

`padding` 和 `margin` 的一至四值简写按上、右、下、左分配：一值设四边；两值为上下、左右；三值为上、左右、下；四值按顺时针排列。

### 边框几何可以画小三角

内容宽高与 padding 都为零时，边框仍占据空间。下面的等宽实线边框在 Chromium 中汇到中心，形成四个三角；只给左边着色、其他三边保持透明，就会露出朝右的三角：

![零尺寸盒子的四条边框收尖到中心，只显示左边框时形成向右三角](../../frontend/html-css/resources/box-model-border-triangle.svg)

~~~css
.caret-right {
  display: inline-block;
  width: 0;
  height: 0;
  padding: 0;
  border: 10px solid transparent;
  border-left-color: currentColor;
  border-radius: 0;
}
~~~

把这组样式用于空 `span` 时，`inline-block` 使宽高声明生效；四条边框仍占宽度，其中未着色的三条透明边框也会占位，边框盒为 `20 × 20px`。`padding: 0` 与 `border-radius: 0` 保持图示的尖角。若希望形状独立于边框、随方盒一起缩放，可改用 `clip-path` 绘制向下的三角形。百分比坐标从盒子左上角开始，y 值向下增加：

~~~css
.caret-down {
  display: inline-block;
  width: 1rem;
  aspect-ratio: 1;
  background: currentColor;
  clip-path: polygon(0 0, 100% 0, 50% 100%);
}
~~~

装饰性箭头可以对辅助技术隐藏；若箭头表达开合状态或方向，还要通过控件文字或其他语义暴露该信息。

要看 margin 怎样在普通流中相遇，以及 float 怎样影响块的边界，请继续读[块格式化上下文如何约束浮动和外边距](#19.%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F)。居中和浮层位置分别见[Flex/Grid 对齐](#21.%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F)与[定位和堆叠](#22.%20%E5%AE%9A%E4%BD%8D%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%E5%85%83%E7%B4%A0%E4%BD%8D%E7%BD%AE%E4%B8%8E%E5%89%8D%E5%90%8E%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

CSS 声明的盒尺寸和脚本读取到的几何值是不同问题：对本例单一、未分片的面板，`offsetWidth` 返回边框盒的整数宽度，通常包括占位滚动条，但不含 margin，也不应用变换；各 API 的测量边界见[DOM 几何 API](#25.%20%E5%93%AA%E4%BA%9B%E7%BD%91%E9%A1%B5%E5%87%A0%E4%BD%95%E6%8E%A5%E5%8F%A3%E8%83%BD%E6%B5%8B%E9%87%8F%E5%93%AA%E4%B8%80%E7%A7%8D%E7%9B%92%E5%AD%90%EF%BC%9F)。

> [!info]- 来源
> - **盒子的四层边缘与间距简写。** CSS Box Model Module Level 3，§2.1、§3.2、§4.2，W3C Recommendation（2024-04-11）：[CSS Box Model Level 3](https://www.w3.org/TR/css-box-3/#boxes-edges)。其中 margin 在 border 外且背景透明，margin/padding 简写按一至四值分配边缘；访问于 2026-11-12。
> - **`box-sizing`、声明宽度与下限。** CSS Box Sizing Module Level 3，§3.3，W3C Working Draft（2026-09-04）：[CSS Sizing Level 3](https://www.w3.org/TR/css-sizing-3/#box-sizing)。`border-box` 不包含 margin，计算内容尺寸时将负数下限为零；访问于 2026-11-12。
> - **inline-block 与普通 inline 宽度。** CSS 2.2，§10.3.1、§10.3.9，W3C First Public Working Draft（2016-04-12）：[CSS 2.2 width calculation](https://www.w3.org/TR/CSS22/visudet.html#inlineblock-width)。普通非替换 inline 的 `width` 不生效；inline-block 按自身宽度规则处理。该文档是历史草案；访问于 2026-11-12。
> - **边框三角与 `clip-path`。** 本页边框三角已在 Chromium 149 实际渲染；[CSS Backgrounds Level 3 §4.4](https://www.w3.org/TR/css-backgrounds-3/#corner-transitions) 并未强制规定角部颜色切换的精确路径。透明边框属性见 CSS 2.2 §8.5：[CSS 2.2 box model](https://www.w3.org/TR/CSS22/box.html#border-properties)，W3C First Public Working Draft（2016-04-12）；形状裁切见 CSS Masking Module Level 1 §5.1：[CSS Masking](https://www.w3.org/TR/css-masking-1/#the-clip-path)，W3C Candidate Recommendation Draft（2021-08-05）。访问于 2026-11-12。
> - **`offsetWidth`。** CSSOM View Module，§7：[CSSOM View](https://www.w3.org/TR/cssom-view-1/#dom-htmlelement-offsetwidth)，W3C Working Draft（2025-09-16）。访问于 2026-11-12。
## 19. 块格式化上下文如何约束浮动和外边距？

块格式化上下文（block formatting context, BFC）是一套独立的块级排版环境。建立 BFC 的盒子（BFC 根）会为自己的内容开启新的格式化上下文，根盒自身仍参加外层格式化上下文。浮动盒（float）脱离普通流，却仍会缩窄旁边的行框（line box）。普通块的自动高度不直接计入内部 float 的边缘；float 缩窄行框、增加文字行数时，仍会间接增加普通块的高度。BFC 根在高度为 auto 时，会把参与该 BFC 的浮动后代计入到底部外边距边缘（bottom margin edge）。固定高度或高度限制会约束最终结果。BFC 根本身也不会自动创建堆叠上下文或定位包含块。

在报表页面里，<code>display: flow-root</code> 是直接建立 BFC 的写法。下面沿同一报表页面说明摘要卡内部浮动如何被自动高度纳入、外部浮动怎样影响新 BFC 根，以及垂直外边距（margin）何时折叠。盒子的 content、border 与 margin 尺寸见[CSS 如何计算元素盒子的尺寸](#18.%20CSS%20%E5%A6%82%E4%BD%95%E8%AE%A1%E7%AE%97%E5%85%83%E7%B4%A0%E7%9B%92%E5%AD%90%E7%9A%84%E5%B0%BA%E5%AF%B8%EF%BC%9F)。

### 为什么报表卡片里浮动徽标会撑不开父级？

假设摘要卡宽 <code>360px</code>，根字号 <code>16px</code>；徽标宽高各 <code>3rem</code>，右 margin 为 <code>8px</code>；文字行高 <code>20px</code>：

~~~html
<div class="summary">
  <span class="badge">异常</span>
  <p>共12条记录需要复核。</p>
</div>
~~~

~~~css
html { font-size: 16px; }
.summary { width: 360px; background: #f3f6fa; }
.summary.flow-root { display: flow-root; }
.badge {
  float: left;
  inline-size: 3rem;
  block-size: 3rem;
  margin-right: 8px;
}
.summary p { margin: 0; line-height: 20px; }
~~~

徽标是 <code>48 × 48px</code>。它和右侧 <code>8px</code> margin 一起占 <code>56px</code>，所以文字旁边的行框宽 <code>360 − 48 − 8 = 304px</code>；文字实测约 <code>162px</code>，只占一行。段落块盒仍宽 <code>360px</code>。普通块卡片的内容高是 <code>20px</code>，徽标则向下露出背景 <code>48 − 20 = 28px</code>。把卡片改为 <code>display: flow-root</code> 后，BFC 根的自动高度增至 <code>48px</code>，将参与这个 BFC 的徽标纳入高度。

![普通块的自动高度不直接计入内部 float 的边缘；flow-root 根按本 BFC 浮动的底部 margin edge 扩展](../../frontend/html-css/resources/bfc-internal-float.svg)

### 外部 float 怎样影响一个 BFC 盒？

BFC 根的内容使用内部格式化上下文排版；根盒仍在外层按普通流参与布局。若它和 float 属于同一个外层 BFC，根的 **边框盒（border box）** 不与该 float 的 **外边距盒（margin box）** 重叠。空间不足时，根可以变窄，或移到前方 float 下面。以下例子沿用 <code>360px</code> 外层、左 float <code>120px × 80px</code>，并让内部提示卡自身建立 BFC：

~~~css
.outer { display: flow-root; inline-size: 360px; }
.external-float { float: left; inline-size: 120px; block-size: 80px; }
.note { display: flow-root; block-size: 32px; } /* 自动宽度 */
.note.fixed { inline-size: 300px; }             /* 固定宽度 */
~~~

![相同外层 BFC 中的 float 与内层 BFC 根：自动宽度并排，固定宽300px的测量结果移到下方](../../frontend/html-css/resources/bfc-external-float.svg)

Chromium <code>149.0.7827.55</code> 实测：自动宽度的提示卡从 <code>x=120px</code> 开始，占剩余 <code>240px</code>；固定宽 <code>220px</code> 时可以并排，右边还余 <code>20px</code>；固定宽 <code>300px</code> 放不下，实测移至 float 下方 <code>80px</code>。这些具体宽度和落点是该浏览器与这组 CSS 数值下的结果，不是 CSS 对所有空间条件规定的唯一策略。例中未给 float 或提示卡加 margin、padding、border；若有这些尺寸，避让判断仍比较 float 的 margin box 与 BFC 根的 border box。

### 相邻 margin 为什么不是简单相加？

同一 BFC 中，前一个普通流块的下 margin 与紧随其后的普通流块兄弟的上 margin 可以折叠；后一个兄弟带有 clearance（clear 为避开 float 加入的间隔）时例外。两边之间若有 line box、这种 clearance、padding 或 border，就不会相邻折叠。每个兄弟自己的 border 和 padding 位于自己的 margin 内，不会自动隔开这两条外侧 margin。

两个正 margin 取较大值：状态卡 A 的下 margin <code>24px</code> 与卡 B 的上 margin <code>16px</code> 折叠为 <code>24px</code>，不是 <code>40px</code>。一正一负时，用最大正值加上最负值：<code>24px + (−16px) = 8px</code>。若两个 margin 都为负，则取更负者，例如 <code>−24px</code> 与 <code>−16px</code> 折叠为 <code>−24px</code>。

~~~css
.report-card { block-size: 20px; margin-block-end: 24px; }
.report-card + .report-card { margin-block-start: 16px; }
~~~

![同一 BFC 内兄弟块级盒的24px与16px正 margin 合并，以及24px与负16px合并](../../frontend/html-css/resources/bfc-sibling-margins.svg)

父级的上 margin 还可能与首个普通流块子级的上 margin 向外折叠：父级上边没有 border 或 padding，两条 margin 之间没有 line box，且首个子级没有 clearance 时，父 margin <code>24px</code> 与子 margin <code>16px</code> 折叠为父级外侧的 <code>24px</code>。此时子盒从父盒顶部开始。若父级改成 <code>display: flow-root</code>，父的外 margin 仍为 <code>24px</code>，子 margin <code>16px</code> 留在父盒内部；父自动高度因此从子盒的固定 <code>20px</code> 增为 <code>36px</code>。

~~~css
.sheet { display: flow-root; inline-size: 200px; }
.panel { margin-block-start: 24px; }
.panel > .first-row {
  inline-size: 150px;
  block-size: 20px;
  margin-block-start: 16px;
}
.panel.flow-root { display: flow-root; }
~~~

![普通块父级的首个子 margin 向外折叠；flow-root 将16px子 margin 留在父盒内](../../frontend/html-css/resources/bfc-parent-child-margins.svg)

BFC 阻止的是盒内外跨边界折叠，不会自动取消 BFC 根自身与外层的 margin 规则。

### 如何创建 BFC，什么副作用值得注意？

- <code>display: flow-root</code> 直接建立 BFC，不裁切内容，也不创建滚动容器。
- 浮动、绝对定位、inline-block、table cell 和 table caption 等也会为内容建立格式化上下文；它们自身还有浮动、定位、行内排版或表格布局行为。Flex/Grid 容器建立各自的格式化上下文，不是 BFC；相邻项目的 margin 不折叠，float 不会使项目按浮动盒参与布局。
- 对块盒，计算后的 <code>overflow</code> 值为 <code>hidden</code>、<code>auto</code> 或 <code>scroll</code> 时也会建立独立格式化上下文。它们都是滚动容器；<code>hidden</code> 不显示滚动界面，但仍允许程序滚动。<code>auto</code> 即使没有溢出，也不保证界面上有滚动条；若用户代理用可见滚动机制，只有存在溢出时才显示。<code>scroll</code> 在用户代理采用可见滚动机制时，即使没有溢出也应显示。若只想建立 BFC，选 <code>flow-root</code>，不要把 <code>overflow: hidden</code> 当作没有其他效果的替代品。
- <code>overflow: clip</code> 可裁切溢出，但本身不建立格式化上下文或滚动容器。若另一轴设成非 <code>visible</code> / <code>clip</code> 的值，两个轴的计算值可能让原来的 <code>clip</code> 变为 <code>hidden</code>；这时要按计算后的值判断是否建立 BFC。

旧环境里也常见 clearfix 清除伪元素：

~~~css
.legacy-parent::after {
  content: "";
  display: table;
  clear: both;
}
~~~

<code>clear: both</code> 会把这个生成的清除盒放到前方 float 下方；它作为普通流子盒参与父级自动高度，因此可让父背景延伸到 float 底部。但它没有让父盒成为同样的 BFC 根，所以不能取代 <code>flow-root</code> 来建立外部浮动避让或父子 margin 的边界。

> [!info]- 来源
> - **BFC 与独立格式化边界。** CSS Display Module Level 3，§2.2、附录 A，W3C Candidate Recommendation Draft（2026-06-05）：[CSS Display Level 3](https://www.w3.org/TR/css-display-3/)。flow-root 为内容建立 BFC；独立格式化上下文隔开 float 影响与 margin collapse；Flex/Grid 建立各自格式化上下文。草案状态截至 2026-11-12。
> - **块级 float 布局与清除。** CSS 2.2，§9.4.1、§9.5、§9.5.2，W3C First Public Working Draft（2016-04-12）：[BFC](https://www.w3.org/TR/CSS22/visuren.html#block-formatting)、[float 避让](https://www.w3.org/TR/CSS22/visuren.html#floats)、[clear 与 clearance](https://www.w3.org/TR/CSS22/visuren.html#flow-control)。§9.5 的避让对象限定为同外层 BFC 中 float 的 margin box；普通流 BFC 根的 border box 可能下移，clearance 不检查 float 自身或其他 BFC 中的 float。该文档是历史草案。
> - **BFC 根的自动高度。** CSS 2.2，§10.6.7，W3C First Public Working Draft（2016-04-12）：[Auto heights for BFC roots](https://www.w3.org/TR/CSS22/visudet.html#root-height)。自动高度纳入参与该 BFC 的浮动后代底部 margin edge；其他 BFC、绝对定位后代与嵌套在其他 float 中的浮动不计入。
> - **相邻与父子 margin 折叠。** CSS 2.2，§8.3.1，W3C First Public Working Draft（2016-04-12）：[Collapsing margins](https://www.w3.org/TR/CSS22/box.html#collapsing-margins)。它定义边缘相邻条件、父子折叠条件及多条正负 margin 的合并算法。
> - **overflow、滚动容器与格式化上下文。** CSS Overflow Module Level 3，§3.1，W3C Working Draft（2025-10-07）：[Managing Overflow](https://www.w3.org/TR/css-overflow-3/#overflow-properties)。该草案定义可滚动值、clip 例外、滚动界面条件、计算值和独立格式化上下文；访问于 2026-11-12。
> - **Flex/Grid 项目的边距与 float。** [CSS Flexbox Level 1 §4.2](https://www.w3.org/TR/css-flexbox-1/#item-margins)、[CSS Grid Level 2 §6.4](https://www.w3.org/TR/css-grid-2/#item-margins)：相邻项目的 margin 不折叠；项目按各自格式化上下文排布，float 不会使它们按浮动盒参与布局。
## 20. 哪些 CSS 单位与响应式布局规则适合当前空间？

Cascading Style Sheets (CSS, 层叠样式表) 的长度单位先问“相对于什么”，断点再问“谁的尺寸或状态改变时需要换规则”。报表页面通常让 Grid (网格布局) 的自动重复轨道根据网格容器可用宽度和轨道最小尺寸决定列数，不会先量卡片文字宽度；media query (媒体查询) 响应视口或用户偏好；container query (容器查询) 则让放在主栏、窄侧栏等不同区域的卡片按自身可用宽度调整。

### 常见尺寸单位各自参照什么？

| 单位 | 参照 | 常见用途 | 需要记住的边界 |
| --- | --- | --- | --- |
| `px` | CSS reference pixel (CSS 参考像素) | 边框、精确间距 | 不保证最终绘制成一个物理设备像素 |
| `%` | 由该属性定义的参照盒或参照值 | 流动宽度、偏移 | 每个属性的百分比基准不同，不能只看符号 |
| `em` | 通常取使用该值的元素计算字号；用于 `font-size` 时取继承字号 | 随文字缩放的局部间距 | 嵌套字号可能逐层相乘 |
| `rem` | 根元素的计算字号 | 跨组件的一致文字相对尺寸 | 媒体查询和容器查询对相对单位的求值规则不同 |
| `vw` / `vh` | 默认 large viewport (大视口) 的宽、高；每单位为对应尺寸的 1% | 视口区域 | 视口不是普通内容盒；工具栏展开时，`100vh` 可能大于当前可见高度 |
| `svh` / `lvh` / `dvh` | 每单位分别为 small viewport height (小视口高度)、large viewport height (大视口高度)、dynamic viewport height (动态视口高度) 的 1% | 移动端全高界面 | 需选择是否随浏览器工具栏伸缩 |
| `vmin` / `vmax` | 默认 large viewport 的短边 / 长边；每单位为对应边长的 1% | 随方向变化的尺寸 | 不表示内容容器宽度 |

例如，若初始字号与根字号均为 16px，`1.5rem = 24px`；将根元素计算字号改为 20px 后，普通声明中的 `5rem = 100px`。`em` 用在非 `font-size` 声明时参照当前元素字号；用在 `font-size` 本身时参照父元素继承来的字号。`rem` 让一组声明共用根字号，但如果在根元素上计算 `font-size`，CSS 对该循环关系采用初始字号。

媒体查询、容器查询和普通样式声明对字号相对单位的求值需要分开看：

| 使用位置 | `em` 的参照 | `rem` 的参照 |
| --- | --- | --- |
| 普通样式声明 | 使用该值的元素计算字号；`font-size` 取父元素字号 | 根元素计算字号 |
| `@media` | 初始 `font-size` 值 | 初始 `font-size` 值 |
| `@container` 尺寸条件 | 被选中查询容器的计算字号 | 根元素计算字号 |

因此，固定根字号可能影响用户的基础文字偏好；而媒体查询中的 `rem` 断点不会跟随页面自己的 `html { font-size: ... }` 声明改变。CSS `1px` 是参考像素：设备像素比、页面缩放与栅格对齐会共同影响它最终覆盖多少个设备像素。

对会改变可见视口高度的浏览器工具栏，`100svh` 按工具栏展开时的小视口计算，`100lvh` 按收起时的大视口计算，`100dvh` 随当前动态视口变化。想让关键内容在工具栏展开时也完整可见，可从小视口单位开始；想随可见区域伸缩，则考虑动态单位，并接受伸缩时的布局变化。

`100vw` 按视口宽度计算；内部滚动容器的滚动条槽只缩小该容器的内容宽度，不缩小视口。在本机 headless Chrome (无头 Chrome) `157.0.8103.51` 的 700px 视口中，内部滚动 `<section>` 设置为 `width: 700px; height: 100px; overflow-x: hidden; overflow-y: auto; scrollbar-gutter: stable`，并放入高度超过 100px 的内容。经典垂直滚动条在该容器内预留 15px；容器内容宽 685px，与 700px 视口宽度不同。内部 `width: 100vw` 子项按视口宽度为 700px；`width: 100%` 子项按该滚动区域提供的宽度为 685px。数字绑定于本机滚动条环境；overlay scrollbar (覆盖式滚动条) 不占用这段宽度。CSS Overflow 规定根元素的 `scrollbar-gutter` 应用到视口；`vw` 与根滚动条槽的实际尺寸关系需另按目标浏览器检查，不能直接套用这个内部容器结果。若目标是填满当前内容区，块容器通常用 `width: 100%` 或保持 `width: auto`，让父级分配可用空间。如果还需要手动设 `width: 100%`，带有内边距或边框的元素可配合 `box-sizing: border-box`，避免外尺寸超出父级；其他滚动条模式也应按目标环境检查。

### 断点由视口还是组件决定？

| 需要响应的变化 | 起点 | 报表中的例子 |
| --- | --- | --- |
| 整个页面的视口宽度或方向变化 | `@media` | 小视口把并排区域改为单列，内容按文档源顺序堆叠 |
| 卡片自身分配到的宽度变化 | `@container` | 同一查询卡片在主栏横排，在窄侧栏竖排 |
| 重复卡片随网格可用宽度换列 | Grid 自动重复轨道 | 有空间就放下一列，不硬编码设备名称 |

断点应服务于内容，而不是机械套用“手机 / 平板 / 桌面”的设备标签。报表外框在视口宽度 48rem 及以下由两列改为单列，项目按源文档顺序堆叠；这个改列规则本身不会重排侧栏或其他区域的文档顺序：

~~~css
.report-layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 1rem;
}

@media (max-width: 48rem) {
  .report-layout { grid-template-columns: minmax(0, 1fr); }
}
~~~

媒体查询里的 `em`、`rem` 等字号相对单位按初始字号求值，不按页面样式改过的根字号求值。若初始字号是 16px，`48rem = 768px`，且 `max-width` 包含等号：视口正好 768px 时也改成单列。即使页面写了 `html { font-size: 20px; }`，这个媒体断点仍为 768px。若用户代理或用户偏好改变初始字号，断点也会按那个初始值计算。

若筛选栏按面板自身宽度换列，建立 inline-size query container (行内尺寸查询容器)，再由该容器决定后代样式。未命名 `@container` 从被设样式的元素向外寻找最近的合格祖先；若需要查询更外层的特定容器，可用 `container-name` 指定名称。本例的 `.report-panel` 提供可查询的 inline size (行内尺寸)，`.report-filter` 是被调整的后代。默认横向书写模式下，inline size 是内容盒宽度；改为纵向书写模式时，它沿行内轴，物理上对应高度。查询条件只能作用于查询容器的后代。筛选区只包含月份、地区与提交按钮三个项目；每个 `label` 把说明与输入控件放在一起，便于作为一组参与 Grid 布局：

~~~html
<section class="report-panel">
  <form class="report-filter" action="/reports" method="get">
    <label>月份
      <input name="month" type="month" value="2026-10">
    </label>
    <label>地区
      <select name="region">
        <option value="">全部地区</option>
        <option value="north">北区</option>
      </select>
    </label>
    <button type="submit">筛选报表</button>
  </form>
</section>
~~~

~~~css
.report-panel {
  container-type: inline-size;
}
.report-filter {
  display: grid;
  grid-template-columns: 1fr;
}

@container (inline-size > 30rem) {
  .report-filter {
    grid-template-columns: 1fr 1fr auto;
    align-items: end;
  }
}
~~~

在根字号 16px、面板内容盒为 480px 的演算中，`30rem = 480px`，但条件使用严格大于号，所以 480px 仍是单列；宽度超过 480px 才是三列。以整数 CSS px 步进时，481px 是第一个匹配值；若容器宽度可以是小数，则 480px 以上的任意值都会匹配。若页面把根字号改为 20px，`rem` 查询阈值为 600px；若要让阈值随面板自身字号缩放，可改用 `em`，它按被选中查询容器的计算字号求值。

本例条件使用逻辑特征 `inline-size`，它随书写模式沿行内轴查询；若改用物理特征 `width`，默认横向书写模式下它指向同一宽度，而纵向书写模式下 `width` 是与行内轴垂直的物理宽度，未必由 `container-type: inline-size` 提供。`container-type: inline-size` 让元素成为沿行内轴可查询尺寸的容器，并应用行内尺寸包含与样式包含，建立独立格式化上下文。它改变容器自身的内在尺寸计算，因此组件的行内尺寸应由父级布局或明确约束提供，而不应依赖子内容把容器撑宽。本例的 `section` 是普通块盒，填满父级可用宽度；更复杂的组件需结合自身布局用途选择查询容器。

### 用内容和实际宽度决定响应规则

#### 让 Grid 按可容纳的最小轨道自动换列

自动列数由 Grid container (网格容器) 的可用行内尺寸和轨道最小值决定，不是先测卡片文字宽度。沿用报表主栏的 880px 可用宽度、根字号 16px，并把最小轨道设为 `15rem = 240px`、间隔设为 `1rem = 16px`：三列至少需要 `3 × 240 + 2 × 16 = 752px`，四列要 `4 × 240 + 3 × 16 = 1008px`，所以这里最多排三列。以下独立例子用三个普通卡片展示；按默认自动放置每项占一列：

~~~html
<section class="report-cards" aria-label="月度报表">
  <article>订单总量</article>
  <article>准时交付</article>
  <article>待复核</article>
</section>
~~~

~~~css
.report-cards {
  display: grid;
  inline-size: min(100%, 880px);
  grid-template-columns:
    repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}
~~~

若有三张卡片，每列约 `(880 − 2 × 16) ÷ 3 = 282.7px`；本机 Chromium 157 测得约 282.66px。若只有两张卡片，自动重复仍可容纳三条最小轨道，但 `auto-fit` 折叠没有项目的第三条轨道及其相邻间隔，两列各约 `(880 − 16) ÷ 2 = 432px`。若主栏变成 220px，`min(100%, 15rem)` 允许唯一轨道降至 220px。`auto-fill` 会保留空轨道的位置，适合想在两张卡片后留出空槽而不拉宽卡片的情况。

#### 让字号随视口连续变化

以前端设计稿宽 1000px 且视口同为 1000px 为例，宽 200px 的图标占画布 20%，所以对应 `20vw`。这只是特定设计宽度下的换算；如果图标在窄屏仍需保持可读尺寸，`20vw` 会随视口继续缩小，可能需要 `clamp()` 上下限，或让布局在内容放不下时重排。

~~~css
.report-title {
  font-size: clamp(1.25rem, calc(2vw + 0.75rem), 2rem);
}
~~~

根字号为 16px 时，`1.25rem = 20px` 是下限，`2rem = 32px` 是上限：

| 视口宽度 | 中间表达式 `2vw + 0.75rem` | 最终字号 |
| --- | --- | --- |
| 300px | 18px | 20px，下限生效 |
| 600px | 24px | 24px，随视口变化 |
| 1000px | 32px | 32px，正好到达上限 |
| 1200px | 36px | 32px，上限生效 |

不需要连续缩放时，用媒体查询表达台阶变化；需要适配组件大小时，用容器查询；重复内容应随可用宽度换列时，可让 Grid 自动重复轨道参与计算。固定轨道、`fr` 分配与内在最小尺寸的完整关系见[固定与流动内容适合哪种 CSS 布局？](#21.%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F)。

### 受限文本与行数裁切

单行 ellipsis (省略号) 要求文本块有受限的行内宽度、文字不换行、溢出被裁切；`text-overflow` 只决定怎样提示溢出，不替代这些条件。下面假设工具栏父级宽度为 360px，标题直接作为 Flex 项；先看裁切写在该项目上的版本：

~~~html
<nav class="toolbar" aria-label="当前报表操作">
  <a class="report-name" href="/reports/october">
    2026 年 10 月跨地区订单处理与复核情况汇总
  </a>
  <button type="button">筛选</button>
</nav>
~~~

~~~css
.toolbar {
  display: flex;
  inline-size: 360px;
  gap: 16px;
}
.toolbar > .report-name {
  flex: 1 1 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
~~~

这个例子把 `overflow: hidden` 写在直接 Flex 项上；它属于可滚动的溢出值（虽然不显示滚动条，仍能通过程序滚动），所以该项目的自动主轴最小尺寸为零，不需再写 `min-inline-size: 0`。如果保留一个内层链接、只在链接上裁切，直接 Flex 项本身仍可能因为内容最小宽度拒绝收缩：

~~~html
<div class="toolbar">
  <div class="report-name">
    <a href="/reports/october">
      2026 年 10 月跨地区订单处理与复核情况汇总
    </a>
  </div>
  <button type="button">筛选</button>
</div>
~~~

这时在直接项目上设零最小行内尺寸，并在内层文本元素上裁切：

~~~css
.toolbar > .report-name {
  flex: 1 1 0;
  min-inline-size: 0;
}
.toolbar > .report-name > a {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
~~~

在 Grid 中也要看项目的直接轨道和最小尺寸条件：像 `minmax(0, 1fr)` 这样的零下限轨道已经允许轨道收缩，但内容本身仍需断行、裁切或滚动。`overflow: clip` 不是 `hidden` 的同义写法：前者不建立 scroll container (滚动容器)，可能保留基于内容的自动最小尺寸。需要看完整轨道约束时见[固定与流动内容适合哪种 CSS 布局？](#21.%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F)。

多行摘要可用目标浏览器支持的行数裁切形式。CSS Overflow Level 4 草案定义了未加前缀的 `line-clamp`；截至本地 Chromium 157，`CSS.supports("line-clamp", "3")` 返回 `false`，而 `CSS.supports("-webkit-line-clamp", "3")` 返回 `true`。以下兼容写法在此浏览器中可识别；目标浏览器仍需验证：

~~~css
.report-summary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
~~~

裁切会改变可见部分，不会删除文本值；用户能否看见、朗读或复制未显示部分取决于交互与工具。关键信息应提供阅读或复制全文的办法；不要把省略号当成唯一披露方式。

### 细边框何时等于一个设备像素？

`1px` 是一个 CSS 参考像素，不保证是一条物理设备像素宽的线。若 effective device pixel ratio (DPR, 有效设备像素比) 约为 2，`0.5 CSS px` 名义上接近一个设备像素；实际绘制还受缩放、边缘对齐和栅格化影响。因此分数线与阴影是视觉技巧，应在目标设备检查。

~~~css
.hairline {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
~~~

> [!info]- 来源与核验
> - **CSS 绝对、相对与视口单位。** W3C [CSS Values and Units Module Level 4](https://www.w3.org/TR/css-values-4/)，Working Draft，2024-03-12，§§6.1–6.2；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-values-4/)，2026-08-24。包括 `px`、`em`、`rem`、`vw` / `vh`、`svh` / `lvh` / `dvh`、`vmin` / `vmax` 与 `clamp()`。
> - **媒体查询中的相对单位。** W3C [Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/)，Working Draft，2026-02-19，§1.3；媒体查询中的字号相对单位按初始字号解析，核对日期：2026-11-12。
> - **容器查询与相对单位。** W3C [CSS Conditional Rules Level 5](https://www.w3.org/TR/css-conditional-5/)，Working Draft，2025-10-30，§§5、6.1；查询容器、`container-type: inline-size` 与容器查询条件中 `em` / `rem` 的参照值，核对日期：2026-11-12。
> - **文本溢出与行数裁切。** W3C [CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/)，Working Draft，2025-10-07，§§3.1、5.1；[CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/)，Working Draft，2023-03-21，§5.1；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-overflow-4/)，2026-10-16，§§5.1、5.1.1，定义 `line-clamp` 与遗留的 `-webkit-line-clamp` 语法。
> - **Grid / Flex 自动最小尺寸。** W3C [CSS Flexible Box Layout Level 1](https://www.w3.org/TR/css-flexbox-1/)，Candidate Recommendation Draft，2025-10-14，§4.5；[CSS Grid Layout Level 2](https://www.w3.org/TR/css-grid-2/)，Candidate Recommendation Draft，2025-03-26，§6.6。核对日期：2026-11-12。
> - **本地探针。** 本轮 headless Chrome `157.0.8103.51`：根字号 20px、查询容器字号 10px 时，`30rem` 条件在宽度 601px 匹配、`30em` 在 301px 即匹配；视口 800px 时 `max-width: 48rem` 不匹配；`CSS.supports()` 对未加前缀 `line-clamp` 返回 `false`、对 `-webkit-line-clamp` 返回 `true`。滚动条宽度例子使用 700px 视口和内部 `.scroll-area { width: 700px; height: 100px; overflow-x: hidden; overflow-y: auto; scrollbar-gutter: stable }`，内容高度 202px；内部 `100vw` / `width: 100%` 子项的实际宽度分别为 700px / 685px。该数值不代表根元素的视口滚动条行为，也不能替代目标浏览器矩阵检查。
## 21. 固定与流动内容适合哪种 CSS 布局？

报表外框常同时有固定侧栏和可伸缩主栏；操作工具栏沿一个方向排列链接与按钮；卡片列表则要在窄宽度下自动换列。沿用报表页的 `<main>` 作为主栏：先描述项目之间怎样分配空间，再选布局。Flexbox (弹性盒布局) 适合沿一个主轴分配项目；Grid (网格布局) 适合显式组织行列轨道。作为 Cascading Style Sheets (CSS, 层叠样式表) 布局模型，默认情况下两者只改变盒子的视觉布局，不会改写 HyperText Markup Language (HTML, 超文本标记语言) 文档中 Document Object Model (DOM, 文档对象模型) 节点的源顺序。

### 固定侧栏与流动结果区

先把设计输入说清楚：报表外框的内容宽度固定为 1120px，左侧导航固定为 14rem（按根字号 16px，即 224px），中间留 16px。没有内容下限时，主栏剩余宽度为：

> [!example] 报表主栏的轨道宽度
> `1120 - 224 - 16 = 880px`。但主栏若含 `min-content`（最小内容尺寸）为 920px 的不可断内容，`1fr` 的自动最小轨道会取 920px；两轨与间隔合计 `224 + 16 + 920 = 1160px`，超出设定为 1120px 的外框 40px。改成 `minmax(0, 1fr)` 后，主栏轨道仍是 880px；本例中的 920px 内容盒被裁掉 40px，真实内容则要自行换行、裁切或滚动。

下面用一个固定 920px 宽的合成内容，单独展示轨道下限怎样影响结果区。它不是实际统一资源定位符的宽度；真实内容如何保留全文见例子之后。

~~~html
<div class="report-layout">
  <nav aria-label="报表分类导航">...</nav>
  <main>
    <h1>月度订单</h1>
    <p class="report-url">
      <span class="synthetic-token">合成的 920px 不可断内容</span>
    </p>
  </main>
</div>
~~~

~~~css
.report-layout {
  display: grid;
  inline-size: 1120px;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 16px;
}
.report-url {
  display: block;
  overflow: hidden;
  white-space: nowrap;
}
.synthetic-token { display: inline-block; inline-size: 920px; }
~~~

在这个单列主栏中，`1fr` 等价于 `minmax(auto, 1fr)`：`auto` 是轨道最小范围，不总是 min-content (最小内容尺寸)；本例的直接 grid item (网格项目) 在默认约束下采用内容下限，因此 920px 内容会撑开它。`minmax(0, 1fr)` 明确把轨道下限设为零，因而能收进剩下的 880px；它不会替长内容选择换行或滚动方式。这里直接网格项目的自动最小尺寸也已是零，所以不必再为同一问题加 `min-inline-size: 0`。

这个合成行内盒会被裁切，只用于看清轨道宽度。若换成真实链接地址并要显示全文，应移除固定宽度和 `white-space: nowrap` / 裁切规则，再为长词设置 `overflow-wrap: anywhere`。若结果是宽数据表，应保留真实 `<table>` 的行列和标题关系，把表放进局部横向滚动容器；该滚动区域应有名称，并确保目标浏览器里键盘用户能到达和滚动它。

下面的 Flex 规则替换上例的 `.report-layout` 布局声明；沿用 1120px 外框、16px 间距和根字号 16px，导航仍为 224px，主栏仍为 880px：

~~~css
.report-layout { display: flex; inline-size: 1120px; gap: 16px; }
.report-layout > nav { flex: 0 0 14rem; }
.report-layout > main { flex: 1 1 0; min-inline-size: 0; }
~~~

flex item (弹性项目) 的主轴自动最小尺寸在默认情况下可能受内容最小宽度限制；长链接地址或大表格因此可能拒绝收缩。`min-inline-size: 0` 明确允许主栏沿行方向缩小，内容随后要自行换行、裁切或在局部滚动。Grid 与 Flex 的细节和适用条件不同：多列关系要按轨道同时对齐时 Grid 更容易表达；只需沿主轴分配一排控件时 Flex 更直接。Flex 可以换行，但每条 flex line (弹性行) 仍各自分配，不会像 Grid 那样把不同项目排成共同列轨道。

### Flexbox 一次处理一个主轴

`display: flex` 或 `inline-flex` 会创建 flex container (弹性容器)，其参与正常流的直接子元素成为 flex item (弹性项目)，非纯空白的直接文本内容会被包进匿名项目；绝对定位的子元素不参与这套空间分配。`flex-direction` 决定 main axis (主轴)，cross axis (交叉轴) 与其垂直。布局先求项目的 flex base size (Flex 基础尺寸)，再把它限制在最小 / 最大尺寸之间，得到 hypothetical main size (假设主尺寸)。算法比较各项外部假设主尺寸（包括外边距）之和与容器内主尺寸，决定本轮使用增长还是收缩；因此 min/max 约束在选择分支之前就会参与判断。随后以基础尺寸为起点分配空间：增长按 `flex-grow` 比例分配 positive free space (正剩余空间)；收缩按 `flex-shrink` 与基础尺寸的乘积，即 scaled flex-shrink factor (缩放后的收缩权重)，分配 negative free space (负剩余空间)。算法依据违反约束的情况冻结部分项目，再把剩余空间分给未冻结的项目。这里先考虑增长因子合计不小于 1 的常见情形；若一行的增长因子合计小于 1，可能只用掉部分正剩余空间。

| 属性 | 负责什么 |
| --- | --- |
| `flex-direction`、`flex-wrap` | 主轴方向、是否产生多条 flex line (弹性行) |
| `justify-content` | 项目尺寸与自动外边距确定后，沿主轴分配剩余空间 |
| `align-items`、`align-self` | 项目在各自 Flex line 的交叉轴上对齐 |
| `align-content` | 在交叉轴上对齐 Flex line；只对允许换行的容器生效，单条 line 也可能移动 |
| `gap` | 项目之间的间距；先从容器可用空间中扣除，再计算可分配空间 |
| `flex-grow`、`flex-shrink`、`flex-basis` | 正剩余空间增长比例、负空间收缩权重、基础尺寸 |
| `order` | 改变 Flex 项目的视觉顺序，不改 DOM 顺序 |

![默认横向书写模式、direction:ltr、flex-direction:row 下 Flexbox 的两轴方向和项目排列；图中标出 main-start、main-end、cross-start、cross-end](../../frontend/html-css/resources/flex-axes.svg)

本图以默认 horizontal writing mode (横向书写模式)、`direction: ltr` (left-to-right, 从左向右) 和 `flex-direction: row` 为例：主轴从左向右，交叉轴从上向下。改用 `column` 后，主轴沿列方向，交叉轴随之交换。两轴起点和终点的物理方向随书写模式与 `direction` 变化；`row-reverse` / `column-reverse` 会反转主轴方向。main size (主尺寸) 和 cross size (交叉尺寸) 分别指项目沿主轴和交叉轴的尺寸。

> [!example] 允许换行的容器即使只有一条 line，也能移动它
> 设容器高 100px、唯一项目高 20px，并使用 `flex-wrap: wrap`、`align-content: flex-end` 和 `align-items: flex-start`。在默认行方向下，单条弹性行的起点落在 `y = 80px`。若把容器改成 `flex-wrap: nowrap`，它成为单行 Flex 容器，`align-content` 不生效，项目仍从 `y = 0px` 开始。

> [!example] 负剩余空间遇到最小尺寸时重新分配
> 容器内宽 256px，项目间距 16px，所以两项共有 240px 可用空间。两项的基础尺寸分别为 200px 和 100px，`flex-shrink` 都为 1，合计比可用空间多 60px。初次按 `1 × 200 : 1 × 100` 的缩放收缩权重分配，得到暂定尺寸 160px 和 80px。若第一项的最小行内尺寸为 180px，它触及下限后被冻结；剩下的第二项重新分配余下空间，最终为 60px。最终尺寸 `180 + 60 + 16 = 256px` 正好填满容器。本机 Chromium 探针也测得 180px、60px。

~~~html
<div class="shrink-demo">
  <div class="first"></div>
  <div class="second"></div>
</div>
~~~

~~~css
.shrink-demo { display: flex; inline-size: 256px; gap: 16px; }
.first { flex: 0 1 200px; min-inline-size: 180px; }
.second { flex: 0 1 100px; min-inline-size: 0; }
~~~

为从零基准分配剩余空间，可显式写 `flex: 1 1 0`。其中 `flex-grow` 与 `flex-shrink` 都为 1，`flex-basis` 明确为零。CSS Flexbox 规范定义的单数值简写 `flex: 1` 也表示以零基准分配空间；本机 Chromium `157.0.8103.51` 的 `getComputedStyle()` 却将它序列化为 `0%`。在主轴尺寸不确定的列容器中，百分比基准会按内容解析，因而可能与明确的零长度表现不同。下文的探针把 `flex: 1` 与 `flex: 1 1 0` 分开测量；若布局依赖确定的零基准且主轴尺寸可能不确定，应写三值形式。

这个差异在本机无头 Chrome 的小例子里可见：自动高度的列容器有两个项目，文字内容高分别为 40px 和 20px，项目设 `min-height: 0; overflow: hidden`。单值 `flex: 1` 的计算基准为 `0%`，两项按内容得到 40px、20px，容器高 60px；显式写 `flex: 1 1 0px` 时，容器与两项高度都为 0px。该尺寸结果是本机 Chromium 157 的探针观察；它限定了上面的写法建议，不意味着所有主轴或浏览器都会出现相同差异。

`flex: auto` 等价于 `1 1 auto`：先参考明确的主轴尺寸，尺寸为 `auto` 时再依据内容。`flex: none` 等价于 `0 0 auto`，按基础尺寸排布且不增长或收缩。`flex: initial` 等价于 `0 1 auto`：有正剩余时不增长，空间不足时仍可收缩到其最小尺寸。项目的自动最小尺寸可能继续阻止收缩，因此还要看其内容和溢出规则。

### 用 Flex 排列报表工具栏并截断长标题

一排导航、操作按钮和当前报表名只有一条主轴，适合 Flex。工具栏可放在 `<main>` 的标题下方；以下 360px 与 1120px 是单独演算的工具栏宽度，不沿用前面 880px 的主栏约束。为让宽度演算可复现，例子把两个链接固定为 64px，按钮固定为 43px，间隔均为 16px；标题项目从零基准增长，标题本身采用单行省略号。

~~~html
<nav class="report-toolbar" aria-label="当前报表操作">
  <a class="fixed-link" href="/reports">全部报表</a>
  <a class="fixed-link" href="/reports/monthly">月度报表</a>
  <span class="current-report">
    2026 年 10 月跨地区订单处理与复核情况汇总
  </span>
  <button type="button">导出</button>
</nav>
~~~

~~~css
.report-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  inline-size: 360px;
  font-size: 16px;
}
.report-toolbar > * { box-sizing: border-box; }
.fixed-link { flex: 0 0 64px; white-space: nowrap; }
.current-report {
  flex: 1 1 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.report-toolbar > button { flex: 0 0 43px; padding: 0; }
~~~

工具栏内容宽度为 360px 时，固定部分共占 `64 + 64 + 43 + 3 × 16 = 219px`，标题从零基准得到 `360 − 219 = 141px` 的正剩余空间。这不是 `flex-shrink` 把标题压窄；标题按 `flex-grow` 增长到 141px 后，才在盒内显示省略号。这个标题在本机 16px 字号的 Chromium 探针中自然宽度约 316px；实际文字宽度会随字体变化。把 `inline-size` 改为 1120px 时，标题得到 `1120 − 219 = 901px`，足够显示完整文本。`overflow: hidden` 在直接 Flex 项上属于可滚动的溢出值：它不显示滚动条，但内容仍能通过程序滚动；因此该项的自动主轴最小尺寸为零。如果只在内层子元素上裁切，外层 Flex 项通常要另写 `min-inline-size: 0` 允许收缩。

裁切只隐藏视觉部分，文本仍在 DOM 中。若标题需要导航，应使用真实链接并保留完整的可访问名称；同时确保省略容器不会裁掉键盘焦点指示。不要用已截断的字符串替换完整标题。

### Grid 同时定义行与列

`display: grid` 或 `inline-grid` 建立显式或隐式行列轨道。固定尺寸适合不变的导航，`fr` 表示按因子分配可用剩余空间，但每条轨道仍要满足自身的最小和最大尺寸。内容关键时，可用 `min-content`、`max-content`、`auto` 与 `fit-content()` 参与轨道尺寸计算：`min-content` 尽量缩到仍可在合法断点换行的最窄尺寸；`max-content` (最大内容尺寸) 则按不利用软换行机会时的内容宽度计算。最终结果还受容器空间、可换行机会与显式约束影响。

~~~css
.cards {
  display: grid;
  grid-template-columns:
    repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}
~~~

这里的 `.cards` 直接子项是卡片；容器宽度明确时，默认自动放置会让每张卡片占一列：

~~~html
<section class="cards" aria-label="月度报表">
  <article><h2>订单总量</h2><p>本月订单数量与上月比较。</p></article>
  <article><h2>准时交付</h2><p>按地区查看订单交付情况。</p></article>
  <article><h2>待复核</h2><p>需要进一步检查的订单。</p></article>
</section>
~~~

根字号为 16px 时，轨道的设计下限是 `15rem = 240px`。沿用 880px 的报表主栏，3 条轨道需 `3 × 240 + 2 × 16 = 752px`，4 条需 `4 × 240 + 3 × 16 = 1008px`，放不下，所以三张及以上卡片排三列，每列约 `(880 − 2 × 16) ÷ 3 = 282.7px`；第四张会进入下一行。若只有两张卡片，`auto-fit` 折叠未放入项目的第三条重复轨道及其相邻间隔，于是每列约 `(880 − 16) ÷ 2 = 432px`。若主栏缩到 220px，`min(100%, 15rem)` 使单列轨道下限缩到 220px。轨道宽度和卡片自身的宽度约束是两件事：若卡片写了 `min-inline-size: 300px`，它仍可撑到 300px 并在 220px 轨道内溢出。本机 Chromium 探针测得 880px 容器中，两张卡片各 432px、三张各约 282.66px，220px 容器中轨道宽 220px。若要在空位保留未使用的轨道槽位，可选择 `auto-fill`；`auto-fit` 则折叠空轨道，让现有项目伸展。

### 居中未知尺寸的内容

如果内容应留在正常流中，让父容器负责二维或单轴对齐。容器必须有多余空间，否则没有可分配的空白：

~~~css
.center-grid {
  display: grid;
  place-items: center;
}

.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

`place-items: center` 将 Grid 项目在格内水平与垂直对齐；Flex 版分别沿主轴和交叉轴对齐。需要覆盖整个区域时，应让容器从父级布局或轨道取得预期高度，而不是给内容写固定尺寸。

居中浮层离开普通流，需要先确定它的包含块，再用定位和 `transform` 让未知尺寸自身回移；规则见[定位如何确定元素位置与前后顺序？](#22.%20%E5%AE%9A%E4%BD%8D%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%E5%85%83%E7%B4%A0%E4%BD%8D%E7%BD%AE%E4%B8%8E%E5%89%8D%E5%90%8E%E9%A1%BA%E5%BA%8F%EF%BC%9F)。本节的居中元素仍留在正常流中，浮层位置由定位机制决定。

### 看懂旧布局，不把它当新布局首选

- **float (浮动)。** 让文字绕排浮动盒；还要处理包含浮动与外边距交互，见[block formatting context (BFC, 块级格式上下文) 如何约束浮动和外边距？](#19.%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F)。
- **表格布局。** 可维护旧项目；`display: table-cell` 不会创建 HTML 表格的标题、行列等语义。
- **inline-block (行内块)。** 源码空白会形成项目间隙，基线也可能影响对齐。
- **绝对定位。** 可把按钮锚定到卡片角落，但它脱离普通流，不参与父级尺寸计算。
- **Bootstrap Grid。** 是框架约定，不等同于 CSS Grid。新项目先确认实际采用的 Bootstrap 版本，再按对应官方文档选类名与断点。

> [!info]- Bootstrap 3.4.1 与 Bootstrap 4.6 的旧网格示例
> 归档 Bootstrap 3.4.1 示例使用十二列系统：`.container` / `.container-fluid`、`.row`、`.col-xs-*` / `.col-sm-*` / `.col-md-*` / `.col-lg-*`。断点为 `<768px`、`≥768px`、`≥992px`、`≥1200px`。归档截图显示的是 Bootstrap 4.6：它有 `.col-` 与 `.col-xl-`，并包含 `576px` 断点，不能用它推断 Bootstrap 3 的类名和断点。可[打开归档 Bootstrap 4 网格截图](../../archive/front-end/0-1_Learning_Notes/CSS/grid.png) 查看。
>
> Bootstrap 3 插件 JavaScript 需要先加载 jQuery；CSS 网格本身不需要该依赖。Bootstrap 官方文档目前将 Bootstrap 3 与 Bootstrap 4 标为结束支持：3.4.1 的维护于 2019-07-24 结束，4.6.2 于 2023-01-01 结束；它们适合作为旧项目维护资料，不是新项目的默认选择。
>
> 来源：[Bootstrap 3.4 Grid system](https://getbootstrap.com/docs/3.4/css/#grid) 与 [Bootstrap 3.4 JavaScript 插件依赖](https://getbootstrap.com/docs/3.4/javascript/)；[Bootstrap 4.6 Grid system](https://getbootstrap.com/docs/4.6/layout/grid/) 与 [Bootstrap 官方结束支持说明](https://getbootstrap.com/docs/4.6/end-of-life/)，核对日期：2026-11-12。

在未使用显式阅读顺序控制时，HTML 源码顺序仍是文档与键盘顺序的通常依据。Flex `order`、`row-reverse` 和 Grid 指定区域改变视觉位置，不会同步改写源码或默认顺序；不要用它们修补错误的源顺序。

> [!info]- 来源与核验
> - **Flex 项目的轴、尺寸与自动最小尺寸。** W3C [CSS Flexible Box Layout Module Level 1](https://www.w3.org/TR/css-flexbox-1/)，Candidate Recommendation Draft，2025-10-14，§§4.5、6、7.1、8.3–8.4、9；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-flexbox/)，2026-05-08。用于单数值 `flex` 简写、基础尺寸、正 / 负剩余空间分配与约束处理。
> - **Grid 轨道和自动重复。** W3C [CSS Grid Layout Module Level 2](https://www.w3.org/TR/css-grid-2/)，Candidate Recommendation Draft，2025-03-26，§§6.6、7.2.3、12；`1fr` 的自动最小范围、`auto-fit` 折叠空轨道与轨道尺寸算法。
> - **Flex/Grid 项目自动最小尺寸与裁切值。** W3C [CSS Overflow Module Level 3](https://www.w3.org/TR/css-overflow-3/)，Working Draft，2025-10-07，§3.1；`hidden`、`clip` 与 `scroll` 的区别，核对日期：2026-11-12。
> - **绘制顺序与格式化模型。** W3C [CSS Display Module Level 3](https://www.w3.org/TR/css-display-3/)，Candidate Recommendation Draft，2026-06-05，§3.1；`order` 改变视觉顺序，不改默认的语音呈现顺序与顺序键盘导航顺序。
> - **键盘焦点顺序。** W3C [Understanding Success Criterion 2.4.3: Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)；焦点移动顺序需保留内容含义与操作关系。
> - **本地布局探针。** 本轮 headless Chrome `157.0.8103.51`：`1fr` 案例主轨道为 920px、两轨与间距合计 1160px，超出 1120px 外框 40px；`minmax(0, 1fr)` 主轨道为 880px。`auto-fit` 在 880px 容器中排出 3 × 282.66px 或 2 × 432px；220px 容器中的轨道为 220px，另测 `min-inline-size: 300px` 卡片本身为 300px 并溢出轨道。负剩余空间的冻结例最终为 180px、60px。独立 Flex 探针中，`flex: 1` 的计算 `flex-basis` 为 `0%`，`flex: 1 1 0` 为 `0px`；自动高度列容器、两项内容高 40px / 20px 时，前者尺寸为 40px / 20px、容器高 60px，后者项目和容器都为 0px。工具栏代码本身使用 `flex: 1 1 0`，不是此处的单值简写探针。这些数字是本机对固定输入的核验，不是跨浏览器性能或兼容性保证。
## 22. 定位如何确定元素位置与前后顺序？

报表卡片里的状态徽标要贴住卡片右上角，弹窗要位于视口中央，工具条则要在滚动时贴顶，直到所属区域离开。`position` 决定盒子怎样参与布局、相对什么参照移动；containing block（包含块）提供定位坐标；stacking context（堆叠上下文）决定绘制时一组盒子如何整体排前后。`display` 决定元素生成什么盒子、使用哪类布局，它回答的是另一类问题。

> [!info] 先把四个问题分开
> normal flow（普通流）中，盒子按块级或行内等布局规则排布；本例的绝对定位徽标脱离普通流，后续内容不会为它留位置。
>
> inset properties（偏移属性）包括物理方向的 `top`、`right`、`bottom`、`left`，也包括逻辑方向的 `inset-block-start`、`inset-inline-end` 等。padding edge（内边距边缘）是 padding box（内边距盒）的外缘。
>
> | 属性或概念 | 要回答的问题 | 常见结果 |
> | --- | --- | --- |
> | `display` | 生成什么盒子，内部如何排布？ | `block`、`flex`、`grid` 选择盒子的类型和布局；`none` 不生成元素及其后代的盒子 |
> | `position` | 盒子是否保留流中位置，偏移怎样解释？ | `relative` 保留原位置再视觉偏移；`absolute` 脱离普通流 |
> | 包含块 | 定位坐标相对哪个矩形计算？ | 绝对定位常用最近建立包含块的祖先 padding edge |
> | 堆叠上下文 | 哪些盒子作为一个组参与前后绘制？ | 子组先在组内排序，再由父级比较整个组 |
>
### position（定位方式）值分别保留什么？

| `position` | 普通流中的位置 | 偏移参照 | 常见滚动表现 |
| --- | --- | --- | --- |
| `static`（静态） | 保留 | 普通流；`top` 等偏移不生效 | 随文档移动 |
| `relative`（相对定位） | 保留原位置 | 元素原来的流位置 | 随文档移动；可为绝对定位后代建立包含块 |
| `absolute`（绝对定位） | 不占原流位置 | 最近建立绝对定位包含块的祖先；若不存在则用初始包含块 | 随该包含块移动 |
| `fixed`（固定定位） | 不占原流位置 | 最近建立固定定位包含块的祖先；通常是视口 | 参照该包含块固定；若祖先建立了固定定位包含块，就不一定贴着视口 |
| `sticky`（粘性定位） | 保留原位置 | 最近滚动容器的滚动视口，并受自身包含块约束 | 在某轴至少一个 inset 不是 `auto` 时，滚动期间才会沿该轴贴近边缘 |

`absolute` 和 `fixed` 会把盒子的外部 `display` 类型块化（blockify），例如内联盒会变成块级定位盒；这只改变盒子的布局类型，不会因此选定包含块或创建堆叠上下文。

所有非 `static` 的 `position` 值都会为后代建立绝对定位包含块。普通块级祖先建立的包含块通常以 padding edge 为边界；`position: relative` 是常见做法。更一般地说，应查找最近建立绝对定位包含块的祖先，而不是默认把父元素当作参照。`transform` 或 `perspective` 非 `none`、`filter` 非 `none`（但对当前浏览上下文的根元素有例外），以及 `contain: layout` 或 `contain: paint` 也会建立绝对与固定定位后代的包含块；因此这类祖先会让 `fixed` 后代改为相对祖先定位。这些属性还各自有创建堆叠上下文的规则；`contain: paint` 会裁切后代绘制。Grid 容器等布局有专门的包含块规则。于是 `position: relative` 单独可以提供坐标参照，但配合 `z-index: auto` 时本身不会新建堆叠上下文。

### 把徽标放到卡片右上角

下面是一个明确的定位案例：卡片的 `320 × 180px` 没有 padding 或 border，所以其 padding box 与内容盒同尺寸；徽标为 `32 × 24px`，距上、右边缘各 `8px`。

~~~css
.report-card {
  position: relative;
  width: 320px;
  height: 180px;
}

.report-card__badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 24px;
}
~~~

卡片建立绝对定位包含块，徽标的右、上偏移从这个 padding box 计算。左坐标为 `320 − 8 − 32 = 280px`，上坐标为 `8px`，所以徽标左上角是 `(280, 8)`。它脱离普通流，标题仍按自己的流位置排版。

![卡片 padding box 与绝对定位徽标的尺寸、边距和计算坐标](../../frontend/html-css/resources/css-position-badge-containing-block.svg)

### 让未知尺寸的弹窗居中

遮罩层可覆盖固定定位包含块，再用 Grid（网格布局）对齐弹窗。视口为 `1120 × 700px`、弹窗为 `320 × 160px` 时，视口中心是 `(560, 350)`；弹窗左上角因此是 `(560 − 160, 350 − 80) = (400, 270)`。

~~~css
.dialog-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
}

.dialog {
  width: 320px;
  height: 160px;
}
~~~

另一种方案不使用 Grid：让遮罩建立绝对定位包含块，再将弹窗左上角定位到包含块中心，最后平移自身宽高的一半。此例中遮罩没有 padding 或 border，仍以 `1120 × 700px` 视口为 `fixed` 包含块：

~~~css
.dialog-backdrop {
  position: fixed;
  inset: 0;
  display: block;
}

.dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 320px;
  height: 160px;
  transform: translate(-50%, -50%);
}
~~~

这里 `top` 与 `left` 以遮罩的 padding box 为参照；`translate` 再将弹窗自身左上角向左、向上移动宽高的一半，结果也是 `(400, 270)`。这和前一段的 Grid 流内子项居中是两套独立方案：在上面的显式 inset 方案中，是遮罩的 `position: fixed` 建立绝对定位包含块；弹窗靠偏移和平移居中。使用 `fixed` 时，应检查祖先是否建立了固定定位包含块；否则参照物通常是视口。

### sticky 为什么没有贴住？

`sticky` 在要粘住的轴上至少需要一个非 `auto` inset，例如 `top: 0`。它相对最近滚动容器的滚动视口移动，并且受自身包含块限制。假设文档顶部有一个 `300px` 高的包裹层，里面的工具条高 `32px`、设 `top: 0`：窗口滚动 `100px` 后，工具条顶边能贴在视口 `y=0`；滚动到 `290px` 时，包裹层底边已到 `y=10`，工具条只能移到 `y=10−32=−22px`，再随包裹层离开。若包裹层只有 `32px` 高，滚动 `100px` 后工具条已在 `y=−100px`，没有剩余空间可粘住。

祖先的 `overflow` 可能改变最近滚动容器，即使那个祖先当前没有可见滚动条；因此应沿祖先链确认实际滚动容器和 sticky 可移动的空间。

### z-index 为什么仍然在下面？

先看最小结构：`.shell` 与 `.other` 是同一 `.stage` 下的重叠兄弟，`.dialog` 则是 `.shell` 的子项。它们覆盖相同的演示区域，因而能观察到谁画在上面：

~~~html
<div class="stage">
  <div class="shell"><div class="dialog">弹窗</div></div>
  <div class="other">其他内容</div>
</div>
~~~

`z-index` 的数值只在相同堆叠上下文中比较。新建的堆叠上下文会作为一个整体放进父上下文，因此内部子项的数值不能越过祖先组，与组外元素直接比较：

~~~css
.stage { position: relative; width: 240px; height: 120px; }
.shell, .other { position: absolute; inset: 0; }
.shell  { z-index: 1; }
.shell .dialog {
  position: absolute; inset: 20px; width: auto; height: auto;
  z-index: 9999; background: #ded3f4;
}
.other { z-index: 2; background: #cfe2fa; }
~~~

`.dialog` 仍在 `.shell` 这一绘制组中；组外 `.other` 的层级高于 `.shell` 时，子项的 `9999` 不会改变这两个组的顺序。蓝色的 `.other` 此时覆盖紫色弹窗；仅把 `.shell` 改为 `z-index: 3`，紫色弹窗才出现在蓝色区域上面。应调整实际参与比较的祖先层级，或把弹窗放入能与目标组同层比较的结构。

上面的比较限定于普通文档层叠。调用原生 `<dialog>` 的 `showModal()` 会把该对话框放入 top layer（顶层）；顶层内容作为根元素的同级整体绘制，普通文档中的任意 `z-index` 都不能把它盖住。

| 观察到的问题 | 先检查 |
| --- | --- |
| 兄弟节点被推开或覆盖 | 普通流位置、绝对定位包含块 |
| 高 `z-index` 元素仍被遮住 | 实际参与比较的祖先堆叠上下文及其层级 |
| 浮动没有计入父元素高度 | [BFC 与流式布局边界](#19.%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F) |

> [!info] 常见堆叠上下文创建条件
> 定位盒配合非 `auto` 的 `z-index`、`fixed` 或 `sticky`（即使 `z-index: auto`）、非 `none` 的 `transform`、`perspective` 或 `filter`、小于 `1` 的 `opacity`、`isolation: isolate`、`contain: layout` 或 `contain: paint` 都会创建堆叠上下文。Flex/Grid 子项配合非 `auto` 的 `z-index` 也会创建。`will-change` 只有在它指向的属性本来会带来对应效果时，才会提前建立包含块或堆叠上下文；不要把所有创建条件都当成同时建立包含块。

> [!info]- 来源
> - `position`、包含块、偏移、sticky 滚动视口和定位盒层叠：W3C CSS Positioned Layout Level 3，Working Draft，2025-10-07，§§2、2.1、2.2、3.4，[规范](https://www.w3.org/TR/css-position-3/)。
> - 顶层绘制顺序：W3C CSS Positioned Layout Level 4，Working Draft，2025-10-07，§§3.1、4，[规范](https://www.w3.org/TR/css-position-4/)。
> - `display:none`、blockification：W3C CSS Display Module Level 3，Candidate Recommendation Draft，2026-06-05，§§2.5、2.7，[规范](https://www.w3.org/TR/css-display-3/)。
> - Flex/Grid 子项的 `z-index` 和绝对定位边界：W3C CSS Flexible Box Layout Module Level 1，Candidate Recommendation Draft，2025-10-14，§§4.1、4.3，[规范](https://www.w3.org/TR/css-flexbox-1/)；CSS Grid Layout Module Level 1，Candidate Recommendation Draft，2025-03-26，§§6.5、9.1、9.2，[规范](https://www.w3.org/TR/css-grid-1/)。
> - `transform` 建立后代定位包含块和堆叠上下文：W3C CSS Transforms Module Level 1，Candidate Recommendation，2019-02-14，§3，[规范](https://www.w3.org/TR/css-transforms-1/)；`perspective` 非 `none` 的包含块和堆叠效果：W3C CSS Transforms Module Level 2，Working Draft，2021-11-09，§8，[规范](https://www.w3.org/TR/css-transforms-2/)；`contain: layout` 与 `contain: paint` 的包含块、堆叠及裁切：W3C CSS Containment Module Level 2，Working Draft，2022-09-17，§§3.2、3.4，[规范](https://www.w3.org/TR/css-contain-2/)。
> - `filter` 的包含块与堆叠效果：W3C Filter Effects Module Level 1，Working Draft，2018-12-18，§5，[规范](https://www.w3.org/TR/filter-effects-1/)；`will-change` 的提前效果：W3C CSS Will Change Module Level 1，Candidate Recommendation Draft，2022-05-05，§2，[规范](https://www.w3.org/TR/css-will-change-1/)；整体透明度：W3C CSS Color Module Level 4，Candidate Recommendation Draft，2026-11-03，§3.3，[规范](https://www.w3.org/TR/css-color-4/)；`isolation`：W3C Compositing and Blending Level 1，Candidate Recommendation Draft，2024-03-21，§3.4.2，[规范](https://www.w3.org/TR/compositing-1/)。
> - 原生模态对话框进入 top layer：WHATWG HTML Living Standard，更新于 2026-11-11，§4.11.4，[`showModal()` 与模态显示算法](https://html.spec.whatwg.org/multipage/interactive-elements.html#dom-dialog-showmodal)。
> - 相关布局边界另见 [BFC 与流式布局边界](#19.%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F)；隐藏状态见[隐藏与可访问性](#23.%20%E9%9A%90%E8%97%8F%E7%8A%B6%E6%80%81%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E7%84%A6%E7%82%B9%E4%B8%8E%E5%8F%AF%E8%AE%BF%E9%97%AE%E6%80%A7%EF%BC%9F)，运动见[CSS 过渡与动画](#24.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%BF%87%E6%B8%A1%EF%BC%8C%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E5%85%B3%E9%94%AE%E5%B8%A7%E5%8A%A8%E7%94%BB%EF%BC%9F)，布局绘制路径见[渲染流水线与强制布局](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。
## 23. 隐藏状态会怎样影响焦点与可访问性？

报表详情面板关闭时，用户不应看见它、Tab 不应进入里面，屏幕阅读器也不应继续把它当作当前可用内容。淡出只影响绘制；隐藏策略还要同时处理布局、指针、键盘焦点和 accessibility tree（无障碍树）。

### 几种隐藏方式留下什么？

| 状态 | 布局空间 | 指针命中 | 键盘焦点 | 无障碍树 |
| --- | --- | --- | --- | --- |
| `display: none`（不生成显示盒）或普通 HTML `hidden`（未被作者样式覆盖） | 移除 | 不绘制、不命中 | 隐藏期间不能聚焦 | 通常不暴露 |
| `visibility: hidden`（不可见） | 保留 | hidden 后代不命中；显式设为 `visible` 的后代可命中 | hidden 后代通常不能聚焦；visible 后代可以 | hidden 后代通常不暴露；visible 后代可能暴露 |
| `opacity: 0`（不透明度为零） | 保留 | 仍可能命中 | 仍可能聚焦 | 通常仍暴露 |
| `inert`（惰性子树） | 样式决定 | 子树不接收交互 | 子树不可聚焦 | 辅助技术通常忽略该子树；视觉仍由 CSS 决定 |
| `aria-hidden="true"`（辅助技术隐藏状态） | 样式决定 | 样式决定 | 不会自行禁用焦点 | 从辅助技术呈现中隐藏子树 |

`visibility:hidden` 只对仍保持隐藏值的盒子隐藏绘制和交互；后代显式设为 `visibility:visible` 后会重新绘制、参与指针命中，也可以接收焦点。父级 `visibility:hidden` 不等同于禁用整棵子树的 `inert`。

> [!info] HTML `hidden` 的两种状态
> 表中普通 `hidden` 指默认隐藏状态；如果作者规则把该元素的 `display` 改成可生成盒子的值，CSS 可以覆盖这项隐藏样式。`hidden="until-found"` 是另一种状态：内容仍隐藏，但保留布局盒，并可由页内查找或片段导航揭示；不要把它当作 `display:none` 的同义写法。

`opacity` 不继承；浏览器把元素及其后代作为透明绘制组处理，因此子元素设为 `opacity: 1` 也无法穿透父元素的 `opacity: 0`。pointer-events（指针命中行为）只影响指针，`pointer-events: none` 不会关闭键盘焦点或无障碍呈现。

> [!info] inert 与 aria-hidden 的责任不同
> HTML `inert` 属性让整个子树暂时退出常规用户交互和顺序焦点导航，也让辅助技术忽略它。`aria-hidden` 只改变无障碍树，不负责取消焦点；不要把它放在仍有可聚焦后代的区域上。

### 关闭面板时先处理焦点

打开时移除 `hidden` 和 `inert` 并更新触发按钮的 `aria-expanded`；关闭时若焦点还在面板内，先把焦点移回触发按钮，再同步设置 `inert`、`hidden` 和折叠状态。CSS transition 负责进入与退出的视觉淡变，交互状态不等动画事件；关闭期间重新打开时，只要重新设为打开状态，当前过渡就会反向到新目标。

~~~html
<button type="button" aria-controls="report-details" aria-expanded="false">
  查看详情
</button>
<section id="report-details" hidden inert>
  <h2>筛选结果详情</h2>
  <button type="button" data-close>关闭详情</button>
</section>
~~~

~~~css
#report-details {
  display: none;
  opacity: 0;
  transition: opacity 180ms ease, display 180ms allow-discrete;
}

#report-details:not([hidden]) {
  display: block;
  opacity: 1;
}

@starting-style {
  #report-details:not([hidden]) { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  #report-details { transition-duration: 0s; }
}
~~~

~~~javascript
const trigger = document.querySelector('[aria-controls="report-details"]');
const panel = document.querySelector("#report-details");
const closeButton = panel.querySelector("[data-close]");

function setDetailsOpen(open) {
  if (!open && panel.contains(document.activeElement)) trigger.focus();
  panel.inert = !open;
  panel.hidden = !open;
  trigger.setAttribute("aria-expanded", String(open));
}

trigger.addEventListener("click", () => setDetailsOpen(panel.hidden));
closeButton.addEventListener("click", () => setDetailsOpen(false));
~~~

这里的示例不等待 `transitionend` 才切换焦点、`inert` 或 `hidden`；所以减少动态效果时即时关闭也能完成，关闭过渡中重新打开也不会留下待执行的延时隐藏操作。

### display 也能参与离散过渡

`display` 不像 `opacity` 那样逐帧插值。CSS Transitions Level 2 允许在实现支持时用 `transition-behavior: allow-discrete` 参与离散切换，并用 `@starting-style` 定义新显示内容的起始样式。按 CSS Display Level 4 §2.9，从 `none` 进入其他显示值时，元素在过渡开始就生成显示盒；从其他值退出到 `none` 时，元素直到过渡结束才移出显示盒，所以可与透明度淡变配合。忽略过渡和动画这两个级联来源后，元素的 `display` 值若仍为 `none`，它就处于惰性状态；上面的例子在状态切换时也显式同步设置 `inert`，不等待淡变结束。

> [!info]- 来源
> - 显示盒生成和 <code>display</code>：W3C CSS Display Level 3，Candidate Recommendation Draft（2026-06-05），[CSS Display](https://www.w3.org/TR/css-display-3/)，检查于 2026-11-06。
> - <code>display</code> 离散过渡中生成/移除显示盒的时点与 inert 行为：W3C CSS Display Level 4，§2.9，Working Draft（2025-11-06），[Animating and Interpolating display](https://www.w3.org/TR/css-display-4/#display-animation)，检查于 2026-11-06。
> - `visibility` 的后代覆盖：W3C CSS Display Level 3，§4，Candidate Recommendation Draft（2026-06-05），[visibility](https://www.w3.org/TR/css-display-3/#visibility)，检查于 2026-11-06。
> - `opacity` 的非继承性、整组透明绘制和命中测试：W3C CSS Color Level 4，Candidate Recommendation Draft（2026-11-03），[CSS Color](https://www.w3.org/TR/css-color-4/)，检查于 2026-11-06。
> - `pointer-events` 对指针命中与顺序焦点导航的边界：W3C CSS Basic User Interface Level 4，Working Draft（2026-01-20），[CSS Basic User Interface](https://www.w3.org/TR/css-ui-4/)，检查于 2026-11-06。
> - `inert` 子树与交互：WHATWG HTML Living Standard（2026-11-05 更新），[Inert subtrees](https://html.spec.whatwg.org/multipage/interaction.html#inert-subtrees)，检查于 2026-11-06。
> - 普通 `hidden` 与 `until-found` 状态：WHATWG HTML Living Standard（2026-11-05 更新），[The `hidden` attribute](https://html.spec.whatwg.org/multipage/interaction.html#the-hidden-attribute)，检查于 2026-11-06。
> - `aria-hidden` 和 `aria-expanded` 状态：W3C WAI-ARIA 1.2，Recommendation（2023-06-06），[WAI-ARIA](https://www.w3.org/TR/wai-aria-1.2/)，检查于 2026-11-06。
> - 离散显示过渡：W3C CSS Transitions Level 2，Working Draft（2026-02-04），[transition-behavior](https://www.w3.org/TR/css-transitions-2/#transition-behavior-property)，检查于 2026-11-06。
> - 减少动态效果：W3C Media Queries Level 5，Working Draft（2026-02-19），[prefers-reduced-motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion)，检查于 2026-11-06。
> - 键盘操作和焦点管理：W3C WAI [ARIA APG Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)，检查于 2026-11-06。
## 24. 何时使用过渡，何时使用关键帧动画？

报表筛选按钮改变颜色、卡片从正面翻到背面，都是两个状态间的视觉过渡；面板进入时先越过终点再回落，装饰图片条带则要连续循环。transition（过渡）在样式值变化时插值；keyframe animation（关键帧动画）用 `@keyframes` 指定时间点上的样式。

> [!info] 先按状态模型选机制
> 一个起点到一个终点，且由 hover、焦点或 class 状态变化触发，通常用 transition。需要按时间点指定多个状态、自动开始、循环、播放方向或暂停时，用 keyframes。若属性沿同一条插值路径略过目标再回来，可用输出进度超出 `[0,1]` 的 easing（缓动函数）；若要安排几个明确的中间状态，则用关键帧。两种方式都要评估对阅读和操作的影响。

### 状态变化用 transition

~~~css
.filter-button {
  background-color: #17324d;
  transition: background-color 180ms ease-out;
}

.filter-button:hover,
.filter-button:focus-visible {
  background-color: #24547d;
}
~~~

| 属性 | 作用 |
| --- | --- |
| `transition-property` | 指定参与过渡的属性，如 `opacity`、`transform` |
| `transition-duration` | 插值持续时间 |
| `transition-timing-function` | 把时间进度映射为插值进度的曲线，如 `ease-out`、`cubic-bezier(...)` |
| `transition-delay` | 开始前等待的时间 |

下例的各属性列表等长，按逗号位置一一对应：

~~~css
.result-card {
  transition-property: transform, opacity;
  transition-duration: 300ms, 200ms;
  transition-timing-function: ease-out, linear;
  transition-delay: 0ms, 100ms;
}
~~~

把过渡声明放在基础状态上，进入和离开状态都会应用。只把声明写在 `:hover` 规则中，离开 hover 时基础状态没有过渡声明，返回过程可能直接跳变。

状态规则决定目标值，过渡中的画面则是当前插值值。若目标在过渡中改变，浏览器从当前画面继续转向新目标；在这个按钮例子里，目标回到原端点时会启动一段缩短的返回过渡，而不是把动画时间轴倒放。在本例的单次回切中，反向缩短因子由旧缓动函数在目标改变时的输出进度决定，也就是沿值区间已走过的比例；不能只用已过毫秒数代替。`cubic-bezier(.34, 1.56, .64, 1)` 的输出可超过 `1`，但只有属性能表示超出端点的值时，画面才会越过终点；例如 `transform: translateY(0) → translateY(100px)` 可以越过 `100px` 后回落，`opacity: 0 → 1` 的计算值则限制在 `[0,1]`。

### 多个时间点用 @keyframes

~~~css
@keyframes panel-enter {
  0%   { transform: translateY(8px); opacity: 0; }
  55%  { transform: translateY(-2px); opacity: 1; }
  100% { transform: translateY(0); opacity: 1; }
}

.report-panel {
  transform: none;
  opacity: 1;
}

.report-panel.is-entering {
  animation: panel-enter 240ms ease-out both;
}
~~~

将 `.is-entering` 加到面板会启动动画。55% 时面板先越过终点 `2px`，最后再回到原位；这个中间关键帧明确指定了越过与回落的时间。如果只要简单越过同一条路径的目标，也可以使用上一节的过冲缓动；这里保留 `55%` 是为了控制中间状态何时发生。

| 属性 | 作用 |
| --- | --- |
| `animation-name` | 选择 `@keyframes` 规则 |
| `animation-duration` | 一轮持续时间 |
| `animation-timing-function` | 在相邻定义了该属性的关键帧之间映射时间进度；可在关键帧中为接下来的一段另设缓动 |
| `animation-delay` | 第一轮开始前等待时间 |
| `animation-iteration-count` | 轮数或 `infinite` |
| `animation-direction` | 正向、反向或交替播放 |
| `animation-fill-mode` | 动画区间外是否应用播放边界时的效果值 |
| `animation-play-state` | `running` 或 `paused` |

本例是一轮默认正向播放且没有延迟，因此实际播放起点和终点的样式分别是 `0%` 与 `100%` 关键帧。若在开始前加延迟，`animation-fill-mode: both` 会应用实际播放起点的效果值；结束后则保留动画实际结束时的效果值。它们不一定总是端点关键帧：播放方向（如反向、交替）和迭代次数（尤其是小数轮数）会决定动画在哪个进度开始与结束，边界处也可能是两个关键帧之间插值出的样式。只要动画声明仍适用于元素，这些填充值就继续参与样式；移除 `.is-entering` 后，面板回到基础样式的 `opacity: 1; transform: none`。fill mode（填充模式）不会把结果写成永久状态。`animation-play-state: paused` 则暂停在当前播放位置；改回 `running` 时从那里继续。

### 用两面翻牌理解 3D transform

transform（变换）可平移、旋转或缩放绘制盒子。下面用类名控制两面卡片的角度；实际交互卡片还需单独提供按钮状态、焦点行为和内容语义，纯 CSS 的背面隐藏只影响绘制，不能代替内容可访问性处理。

~~~html
<div class="flip-demo" aria-hidden="true">
  <div class="flip-demo__inner">
    <div class="flip-demo__face flip-demo__front">正面</div>
    <div class="flip-demo__face flip-demo__back">背面</div>
  </div>
</div>
~~~

~~~css
.flip-demo {
  width: 200px;
  height: 120px;
  perspective: 800px;
}

.flip-demo__inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 600ms ease;
}

.flip-demo.is-flipped .flip-demo__inner { transform: rotateY(180deg); }

.flip-demo__face {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  backface-visibility: hidden;
  color: white;
}

.flip-demo__front { background: #24547d; }
.flip-demo__back { background: #8c3d16; transform: rotateY(180deg); }
~~~

外层 `perspective` 提供近大远小的透视效果；内层 `preserve-3d` 保留两个面的三维位置；背面先旋转 `180deg`，这样父级翻转后它才转到朝向读者的一侧。未加 `.is-flipped` 时，蓝色正面朝向读者；加入该类后，内层转过 `180deg`，正面背向读者，橙色背面转到前方。示例整体 `aria-hidden="true"`，文字只用于演示，不承载页面内容。

`translate`（平移）移动，`rotate`（旋转）改变朝向，`scale`（缩放）改变绘制尺寸。`transform-origin`（变换原点）默认在盒子中心；旋转或缩放时改变它，会改变视觉效果所绕的参照点。多种变换函数组合时顺序会影响结果，交换平移和旋转的顺序可能得到不同位置。`transform` 不重新安排周围普通流项目，但可能扩展可滚动溢出区域，并为后代建立 containing block（包含块）与 stacking context（堆叠上下文）。

### 无限滚动图片条带怎样无缝循环？

以下“双组三图”例子用作纯装饰的 CSS 理想尺寸演算。本例明确采用水平书写、从左到右的条带：视窗宽 `320px`，原图组三张、复制组三张，共六项；整条轨道宽度是视窗的 `600%`，移动 `50%` 对应其中一组三张的理论宽度。

~~~html
<div class="strip-window" aria-hidden="true">
  <div class="strip-track">
    <img src="a.jpg" alt="">
    <img src="b.jpg" alt="">
    <img src="c.jpg" alt="">
    <img src="a.jpg" alt="">
    <img src="b.jpg" alt="">
    <img src="c.jpg" alt="">
  </div>
</div>
~~~

~~~css
.strip-window {
  width: 320px;
  overflow: hidden;
  writing-mode: horizontal-tb;
  direction: ltr;
}

.strip-track {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 600%;
  animation: strip-loop 18s linear infinite;
}

.strip-track img {
  flex: 0 0 calc(100% / 6);
  min-inline-size: 0;
  height: auto;
}

@keyframes strip-loop {
  to { transform: translateX(-50%); }
}
~~~

> [!example] 循环距离
> 轨道宽 `6 × 320 = 1920px`；两个等宽图组各占 `960px`。`translateX(-50%)` 移动 `1920 × 0.5 = 960px = 3 × 320px`，在理想尺寸下，下一组占据原组的位置。这里固定的百分比 `flex-basis` 负责每项宽度；`<img>` 的默认 `min-inline-size: auto` 可能按内容尺寸阻止它缩到 `320px`，因此设为 `0`。例如原图自然宽 `640px` 时，不覆写这个最小尺寸的 Chrome 实测每项仍宽 `640px`，第四项在移动半轨道后落到 `x=960px`，无法接上首组三项。加上 `min-inline-size: 0` 后每项约为 `320px`，第四项落在 `x≈0`；实测仍有不到 `0.05px` 的子像素误差。此几何演算是按 CSS px 计算的理想值，不是对所有图片、浏览器和屏幕都无接缝的保证。素材宽高比不同不影响横向组宽；若卡片宽度或组数变化，需同步调整轨道和每项比例。

**循环位置示意（按理想 CSS px 比例）**

![起点时视窗显示原组 A；整条轨道左移 960px 后，同一视窗显示内容相同、颜色和字母对应的复制组 A。](../../frontend/html-css/resources/css-transitions-and-animations-strip-loop.svg)

下一轮开始时，位移从 `-960px` 重置到 `0`，视窗由复制组 A 切回原组 A。两组内容、排列和尺寸相同，理想几何下重置前后的画面才相同；这就是复制一整组能隐藏循环接点的原因。

这个循环没有控制按钮、键盘浏览、暂停机制或轮播语义，所以不能充当内容轮播。内容轮播应提供前后切换；若自动播放，还要提供停止/开始控制，键盘焦点进入后停止，只有用户显式重启才恢复，并在鼠标悬停时停止。还要处理 prefers-reduced-motion（减少动态效果偏好）。若动画只是装饰，也要确保它不承载唯一信息。

`align-items: flex-start` 还避免 flex 默认的交叉轴拉伸把每张图拉成同一高度。`height: auto` 会按图像比例确定高度：本例自然尺寸分别为 `640×320`、`640×640`、`640×480` 的三张图缩到约 `320px` 宽后分别高约 `160px`、`320px`、`240px`。高度不同不改变横向组宽或移动距离；若去掉 `align-items: flex-start`，默认拉伸可能改变这些高度。

示例上的 `aria-hidden="true"` 只隐藏辅助技术树中的条带，不会暂停屏幕上的运动。若把自动移动的条带放在其他页面内容旁并持续超过五秒，应提供暂停、停止或隐藏机制，除非该运动对活动不可或缺（WCAG 2.2 成功准则 2.2.2）。

### 动画性能与减少动态效果

每帧需要的样式变化可能牵涉样式计算、布局、绘制、栅格化或合成，具体工作由属性、元素内容和浏览器实现共同决定。`transform` 与 `opacity` 通常不改变周围布局，在满足实现的合成条件时可避免逐帧重新布局或绘制；属性名本身不能证明动画一定在合成线程或 GPU 上执行。Chrome Performance 面板的 Animations 轨道会标记未合成动画；选中后可查看未合成原因。应测量目标页面，而不是假定所有浏览器和元素都有同一执行路径。[渲染流水线与强制布局](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)说明写入和几何读取如何影响布局工作。

`will-change`（即将变化提示）只是预告可能发生的变化，不是强制创建 GPU 图层的开关。浏览器可用它提前准备优化，但实现可能不同；若对应属性会创建堆叠上下文或包含块，提前提示也会产生该效果，并可能占用资源。只在测量确认有收益时，对少量元素短时使用，变化结束后移除。`translateZ(0)` 也不是通用加速开关。

~~~css
@media (prefers-reduced-motion: reduce) {
  .report-panel.is-entering,
  .strip-track { animation: none; }

  .filter-button,
  .result-card,
  .flip-demo__inner { transition: none; }
}
~~~

用户选择 `reduce` 表示希望减少可能引起不适或分心的非必要运动。这里面板保持基础可见样式、条带停在第一组的起点；按钮和翻牌状态仍更新，只是不再插值移动。状态由 class 和属性值表达，不由动画是否结束来保存；运动被关闭后，界面仍要显示相同结果，也不能让动画成为唯一信息通道。

> [!info]- 来源
> - 隐式过渡与中断、当前插值值、反向缩短：W3C CSS Transitions Level 1，Working Draft（2026-01-08），§§2–4、§3.1，[CSS Transitions](https://www.w3.org/TR/css-transitions-1/)，检查于 2026-11-12。
> - 显式关键帧、移除动画、暂停与填充模式：W3C CSS Animations Level 1，Working Draft（2023-03-02），§§1–2、3.4–3.9、4，[CSS Animations](https://www.w3.org/TR/css-animations-1/)，检查于 2026-11-12。
> - cubic Bézier 的进度映射与 `opacity` 对 `[0,1]` 的计算值限制：W3C CSS Easing Functions Level 2，First Public Working Draft（2024-08-29），§2.3；CSS Color Module Level 4，Candidate Recommendation Draft（2026-11-03），§3.3，[CSS Easing](https://www.w3.org/TR/css-easing-2/) 与 [CSS Color](https://www.w3.org/TR/css-color-4/)，检查于 2026-11-12。
> - flex 项目默认交叉轴拉伸与 `align-items: flex-start`：W3C CSS Flexible Box Layout Module Level 1，Candidate Recommendation Draft（2025-10-14），§8.3；自动最小尺寸与内容最小尺寸：§4.5，[CSS Flexbox](https://www.w3.org/TR/css-flexbox-1/#align-items-property)，检查于 2026-11-12。
> - `min-inline-size` 与书写模式的物理尺寸映射：W3C CSS Logical Properties and Values Level 1，Working Draft（2025-12-04），§4.1，[CSS Logical Properties](https://www.w3.org/TR/css-logical-1/)，检查于 2026-11-12。
> - 变换、绘制溢出、包含块、堆叠上下文、变换原点、函数顺序及平移百分比相对 reference box：W3C CSS Transforms Level 1，Candidate Recommendation（2019-02-14），§§3–6、9.1，[CSS Transforms](https://www.w3.org/TR/css-transforms-1/)，检查于 2026-11-12。
> - 三维变换模型、保留 3D、透视与背面可见性：W3C CSS Transforms Level 2，Working Draft（2021-11-09），§§4.1、7、8、10，[backface-visibility](https://www.w3.org/TR/css-transforms-2/#backface-visibility-property)，检查于 2026-11-12。
> - `will-change` 提示的实现差异、潜在资源消耗与副作用：W3C CSS Will Change Level 1，Candidate Recommendation Draft（2022-05-05），§§1.2、2，[CSS Will Change](https://www.w3.org/TR/css-will-change-1/)，检查于 2026-11-12。
> - 减少非必要运动的用户偏好：W3C Media Queries Level 5，Working Draft（2026-02-19），§12.1，[prefers-reduced-motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion)，检查于 2026-11-12。
> - 检查未合成动画和未合成原因：Chrome DevTools [Performance features reference](https://developer.chrome.com/docs/devtools/performance/reference)，View animations 一节，检查于 2026-11-12。
> - 轮播控制、焦点进入后停止与悬停停止：W3C WAI [ARIA APG Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)，About This Pattern，检查于 2026-11-12。
> - 自动移动内容与页面其他内容并列显示时的暂停、停止或隐藏机制：W3C WCAG 2.2 Recommendation（2024-12-12），成功准则 2.2.2，[Pause, Stop, Hide](https://www.w3.org/TR/WCAG22/#pause-stop-hide)，检查于 2026-11-12。
> - `aria-hidden` 对辅助技术树的影响：W3C WAI-ARIA 1.2 Recommendation（2023-06-06），§7.1，[Excluding Elements from the Accessibility Tree](https://www.w3.org/TR/wai-aria-1.2/#aria-hidden)，检查于 2026-11-12。
## 25. 哪些网页几何接口能测量哪一种盒子？

Document Object Model（文档对象模型，DOM）提供多组几何 API，它们测量的盒子和坐标系不同。读布局偏移尺寸（`offset*`）或内客户区尺寸（`client*`），读滚动范围与偏移（`scroll*`），读包含 CSS transform（变换）后的视口矩形则用 `getBoundingClientRect()`（获取包围矩形）。一次几何读取可能迫使浏览器先完成尚未更新的样式或布局，但值已是最新时不一定产生新布局。

```text
┌────────────────────────── margin ──────────────────────────┐
│ ┌────────────────────── border ─────────────────────────┐ │
│ │ ┌────────────────── padding ───────────────────────┐  │ │
│ │ │ ┌────────────── content ──────────────────────┐  │  │ │
│ │ │ └────────────────────────────────────────────┘  │  │ │
│ │ └─────────────────────────────────────────────────┘  │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 先按测量目标选择属性

| API | 返回内容 | 不包含或需留意 |
| --- | --- | --- |
| `offsetWidth` / `offsetHeight` | 整数布局尺寸，含 padding、border 和占空间的滚动条 | 不含 margin；不反映 CSS transform |
| `clientWidth` / `clientHeight` | padding 区域尺寸 | 不含 border 和占空间的滚动条 |
| `scrollWidth` / `scrollHeight` | 滚动区域尺寸，包含溢出的内容 | 不含 border；不是“用户一定能滚动”的保证 |
| `scrollLeft` / `scrollTop` | 当前滚动偏移 | 可写；某些布局中数值可为小数或超出熟悉范围 |
| `offsetLeft` / `offsetTop` | 相对 `offsetParent`（偏移父元素）的边缘位置 | 它不一定是直接父元素或最近定位祖先 |
| `getBoundingClientRect()` | 相对视口、包含 transform 后的边框矩形联合范围 | 不含 margin；返回读取时的快照 |

这些数字使用 CSS 像素，不是设备物理像素。占空间的滚动条会改变布局测量，覆盖式滚动条则可能不占空间；这取决于平台及浏览器设置。

### 用固定数字对照布局尺寸

假设一个内容盒宽 `320px`，左右 padding 各 `16px`，左右 border 各 `1px`，没有占空间的滚动条：

~~~css
.content-box {
  box-sizing: content-box;
  width: 320px;
  padding-inline: 16px;
  border: 1px solid;
}
~~~

> [!example] 内容盒尺寸的计算
> `offsetWidth = 320 + 16×2 + 1×2 = 354px`；`clientWidth = 320 + 16×2 = 352px`。前者含边框，后者含 padding 但不含边框。

把声明宽度改为 `box-sizing: border-box; width: 320px`，则内容宽度为 `320 − 16×2 − 1×2 = 286px`；在同样无滚动条的条件下，`clientWidth = 318px`、`offsetWidth = 320px`。

### 读滚动区域与当前偏移

`scrollHeight` / `scrollWidth` 表示滚动区域尺寸。溢出内容可能使它大于可见的 `clientHeight` / `clientWidth`：

~~~javascript
const hasVerticalOverflow = element.scrollHeight > element.clientHeight;
const currentY = element.scrollTop;
element.scrollTop = 0; // 回到顶部
~~~

`scrollTop` 和 `scrollLeft` 可写。反向书写方向、弹性滚动及缩放等情形会使数值不符合“非负整数”的简单假设。

在 standards mode（标准模式）下，根元素 `document.documentElement.scrollHeight` 特别返回视口滚动区域高度与视口高度的较大值；`clientHeight` 则是扣除占空间滚动条后的视口高度。对普通元素，`scrollHeight` 返回其自身滚动区域高度。

### offset 相对哪个父元素？

`offsetParent`（偏移父元素）由同名属性给出。`offsetTop` / `offsetLeft` 描述元素边框边缘相对该父元素 padding 边缘的位置；表格结构、固定定位、包含块和 Shadow DOM（影子 DOM）边界等都会影响返回的父元素。它不固定等同于最近的 `position` 祖先。

### 读变换后的视口矩形

`getBoundingClientRect()` 返回元素非空 client rect（客户端矩形）的最小包围矩形，坐标原点在当前视口左上角，尺寸受 transform 影响。行内内容跨多行时可能有多个 client rect，方法返回它们的联合矩形；结果是本次读取时的 DOMRect（DOM 矩形）快照。

~~~javascript
const rect = element.getBoundingClientRect();
// rect.top / bottom：相对视口顶部的上下边缘
// rect.left / right：相对视口左侧的左右边缘
// rect.width / height：变换后边框盒联合范围，单位为 CSS px
~~~

~~~text
视口左上角 (0, 0)
┌──────────────────────────────────────────────┐
│          ┌────── rect.left ──────┐            │
│          │ 元素 transform 后的外接矩形 │            │
│          └────────────────────────┘            │
└──────────────────────────────────────────────┘
~~~

以矩形判断是否与视口相交，只能说明几何区域有正面积交叠，无法判断元素是否被其他内容遮挡、是否透明或辅助技术是否可见。`getBoundingClientRect()` 对退化的零宽或零高元素也可能返回矩形，因此必须单独检查宽高。下面假设文档处于 standards mode；根元素的 `clientWidth`/`clientHeight` 表示扣除占空间滚动条后的视口尺寸。

~~~javascript
function overlapsViewport(element) {
  const rect = element.getBoundingClientRect();
  const root = document.documentElement;
  return rect.width > 0 && rect.height > 0 &&
    rect.bottom > 0 && rect.top < root.clientHeight &&
    rect.right > 0 && rect.left < root.clientWidth;
}
~~~

### 把写入和读取分批

偶尔读取一次几何属性时，选与问题相符的盒子和坐标系。滚动阈值通知或图片延迟加载优先使用 IntersectionObserver（相交观察器）[图片加载中的观察器示例](#26.%20%E5%9B%BE%E7%89%87%E4%B8%8E%E5%AA%92%E4%BD%93%E8%B5%84%E6%BA%90%E6%80%8E%E6%A0%B7%E5%8A%A0%E8%BD%BD%E5%B9%B6%E4%BF%9D%E6%8C%81%E9%A1%B5%E9%9D%A2%E7%A8%B3%E5%AE%9A%EF%BC%9F)，而不是反复轮询矩形；观察器会异步报告相交状态，但不承诺完全不触发布局工作。

若先改样式再马上读几何值，浏览器可能同步完成待处理的样式或布局；循环交替执行写入和读取会重复付出这类成本。有关批量读取、批量写入的路径见[渲染流水线与强制布局](#12.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - 元素布局尺寸、滚动 API、视口矩形：W3C CSSOM View，Working Draft（2025-09-16），[CSSOM View](https://www.w3.org/TR/cssom-view-1/)，检查于 2026-11-06。其中 [Element.scrollHeight](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight) 说明根元素和普通元素的滚动高度规则。
> - 异步相交通知：W3C [Intersection Observer](https://www.w3.org/TR/intersection-observer/)，Working Draft（2023-10-18），检查于 2026-11-06。
## 26. 图片与媒体资源怎样加载并保持页面稳定？

同一张图片可能是装饰、信息本身，也可能是链接或按钮的操作入口；资源何时请求则关系到首屏内容和网络开销。先按内容决定 HTML 语义与替代文本，再选择尺寸、候选资源和加载时机。

> [!info] 替代文本由用途决定
> alternative text（替代文本）通过 `alt` 提供。纯装饰图使用 `alt=""`；信息图用简洁文字传达页面所需信息；图片是链接或按钮唯一内容时，写出该控件的目的。`title` 不能代替替代文本或表单标签。

### 先按内容选择图像与媒体元素

图像内容用 `<img>`，到另一位置的导航用 `<a href>`，可播放音频和视频分别用 `<audio>`、`<video>`。先决定资源在文档中的语义与替代文本，再选择 URL、尺寸和加载时机。

### 资源地址相对哪个基准？

| 写法 | 示例 | 解析位置 |
| --- | --- | --- |
| 带 scheme 的 URL（统一资源定位符，网址） | `https://example.com/a.png` | 使用 URL 自身的方案和地址；`mailto:team@example.com` 有 scheme（方案）但没有主机 |
| 根相对路径 | `/assets/chart.png` | 从文档基准 URL 的 origin（源）根目录解析；`<base>` 可能改变 origin |
| 文档相对路径 | `../assets/chart.png` | 默认相对当前文档 URL；`<base>` 可改变文档基准 URL |

`src` 指向要载入的图像资源；`href` 为链接提供导航目标。根相对 URL 不是永远相对页面原站：若 `<base href="https://cdn.example.net/reports/q4/">` 改变了文档基准，`/assets/chart.png` 会解析为 `https://cdn.example.net/assets/chart.png`，`../assets/chart.png` 则解析为 `https://cdn.example.net/reports/assets/chart.png`。Unix 风格的文件系统路径 `/project/site/image.png` 不是网络地址。用 `<a>` 导航，用 `<button>` 执行动作；`href="#"` 会改变片段位置并可能影响历史记录，不是无操作占位符。`target="_blank"` 请求新的浏览上下文，适合确需另开页面的导航；给出明确的链接文字，显式写 `rel="noopener"` 也能表明不向新页面暴露 opener。

### 原生延迟加载适合什么图片？

普通首屏之外的内容图片可以使用 HTML `loading="lazy"`。浏览器决定具体的延迟阈值；元素仍需真实的 `src` 或 `srcset`，单写 `data-src` 不会开始图片请求。

~~~html
<img
  src="/assets/monthly-report.webp"
  alt="四月至六月的报表趋势图，六月达到最高值"
  width="640"
  height="360"
  loading="lazy">
~~~

`width` 和 `height` 提供图像固有比例。`640 × 360` 的比例为 `16:9`；若 CSS 将图片显示为 `320px` 宽，预留高度约 `320 × 9 ÷ 16 = 180px`，图片数据到达前浏览器就有尺寸可用于布局。也可用 CSS `aspect-ratio: 16 / 9` 表达容器比例。

对首屏可见、可能成为 Largest Contentful Paint（最大内容绘制，LCP）的主图不要盲目设置 lazy；延迟发现或请求会推迟它的呈现。

### 响应式候选文件怎样被选中？

`srcset` 中的 `640w`、`1280w` 描述候选图像文件的固有像素宽度；`sizes` 描述当前布局给图像留下的 CSS 像素宽度。下面的样式让图像在视口窄于 `640px` 时占满视口，宽屏上限为 `640px`，因此 `sizes` 与实际展示宽度相符：

~~~html
<img class="report-responsive"
     src="/assets/report-640.webp"
     srcset="/assets/report-640.webp 640w, /assets/report-1280.webp 1280w"
     sizes="(max-width: 640px) 100vw, 640px"
     width="640" height="360"
     alt="四月至六月的报表趋势图，六月达到最高值">
~~~

~~~css
.report-responsive {
  display: block;
  width: min(100vw, 640px);
  height: auto;
}
~~~

把布局宽度乘以设备像素比（DPR）可得到一个候选密度目标：`320px × DPR 2 = 640`，通常由 `640w` 资源满足；`640px × DPR 2 = 1280`，通常由 `1280w` 资源满足。浏览器结合可用候选、设备像素比和用户代理策略选文件；`sizes` 要反映页面实际留给图片的宽度。

若窄屏需要不同裁切而不是同一画面的高低分辨率版本，使用 `<picture>` 的 `<source media>` 切换图像，再由 `<img>` 提供后备资源、尺寸和 `alt`。下面两个裁切都保持 `16:9`；若不同裁切有不同宽高比，也要按断点调整展示盒比例：

~~~html
<picture>
  <source media="(max-width: 640px)" srcset="/assets/report-narrow-crop.webp">
  <img src="/assets/report-wide-crop.webp"
       width="640" height="360"
       alt="四月至六月的报表趋势图，六月达到最高值">
</picture>
~~~

### 何时用 IntersectionObserver（相交观察器）？

IntersectionObserver（相交观察器）适合自定义滚动根、预加载边距、阈值，或目标进入范围时除了加载图片还要执行其他工作。普通图片优先让浏览器通过原生属性自行安排。

~~~html
<img src="/assets/placeholder.png"
     data-src="/assets/offscreen-chart.png"
     alt="报表图表"
     width="640" height="360">
~~~

~~~javascript
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;

    const image = entry.target;
    image.src = image.dataset.src;
    image.removeAttribute("data-src");
    observer.unobserve(image);
  }
}, { rootMargin: "200px" });

document.querySelectorAll("img[data-src]").forEach((image) => observer.observe(image));
// 组件卸载且拥有该观察器时，调用 observer.disconnect()。
~~~

正的 `rootMargin` 会在图片进入可视根之前启动加载。`threshold: 0` 下边缘相接也可能报告 `isIntersecting: true`，即使交集矩形面积为零；相交状态不是“至少一像素可见”或“未被遮挡”的证明。通知异步交付，但不保证回调在主线程之外执行。

### 音频、视频和链接要保留什么语义？

`<audio>` 与 `<video>` 用于可播放媒体；提供 `controls`，让用户能启动、暂停和调整播放。媒体格式和编解码器支持因浏览器与平台而异，可按目标环境提供多个 `<source>`。`preload` 是加载偏好提示，实际请求仍由用户代理策略决定；`autoplay` 也是播放请求，可能受自动播放策略限制。

~~~html
<audio controls preload="metadata">
  <source src="/media/summary.ogg" type="audio/ogg">
  <source src="/media/summary.mp3" type="audio/mpeg">
</audio>

<video controls preload="metadata" width="640" height="360"
       poster="/media/preview.jpg">
  <source src="/media/demo.webm" type="video/webm">
  <source src="/media/demo.mp4" type="video/mp4">
  <track kind="captions" src="/media/demo.zh.vtt" srclang="zh" label="中文字幕">
</video>
~~~

给视频标出宽高或比例，降低播放器加入布局时的跳动；字幕通过 `<track>` 提供。音频与视频用 controls 表达播放交互，不要把视觉样式当成媒体控件语义。

对旧浏览器缺少 IntersectionObserver 的页面，才考虑滚动和 resize 几何检查作为回退；该方式应节流：挂载时先检查一次，在 scroll/resize 时合并检查；组件卸载时移除监听器并取消尚未执行的定时检查，避免保留 DOM 引用。矩形判断复用[DOM 几何 API](#25.%20%E5%93%AA%E4%BA%9B%E7%BD%91%E9%A1%B5%E5%87%A0%E4%BD%95%E6%8E%A5%E5%8F%A3%E8%83%BD%E6%B5%8B%E9%87%8F%E5%93%AA%E4%B8%80%E7%A7%8D%E7%9B%92%E5%AD%90%EF%BC%9F)中矩形的实际测量边界。性能比较应看真实路由和设备数据，见[浏览器性能测量](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)与[浏览器如何把 URL 绘制成像素](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)。

> [!info]- 来源
> - 文档基准 URL、相对 URL 解析与链接：WHATWG HTML Living Standard（2026-11-05 更新），[Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)、[Links](https://html.spec.whatwg.org/multipage/links.html#link-type-noopener)；URL Standard，[Basic URL parser](https://url.spec.whatwg.org/#concept-basic-url-parser)。
> - `picture`、`source`、`img`、音视频元素：同一 WHATWG HTML Living Standard，[Embedded content](https://html.spec.whatwg.org/multipage/embedded-content.html) 与 [Media elements](https://html.spec.whatwg.org/multipage/media.html)，检查于 2026-11-06。
> - `loading` 与图片资源加载：WHATWG HTML Living Standard，[Lazy loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes)，检查于 2026-11-06。
> - 图片信息、装饰图片和功能图片的 `alt`：W3C WAI [Images Tutorial](https://www.w3.org/WAI/tutorials/images/)，检查于 2026-11-06。
> - 图片作为 LCP 内容与加载优先级：Google Chrome for Developers，[Optimize Largest Contentful Paint](https://web.dev/articles/optimize-lcp#optimize_when_the_lcp_element_is_an_image)，最后更新 2025-03-31，检查于 2026-11-06。
> - 相交矩形、边缘相接和 `rootMargin`：W3C [Intersection Observer](https://www.w3.org/TR/intersection-observer/)，Working Draft，2023-10-18。
> - 视口矩形 API：W3C [CSSOM View](https://www.w3.org/TR/cssom-view-1/)，Working Draft，2025-09-16。
## 27. 怎样为报表图标选择资源形式？

报表工具栏的图标可以内嵌 SVG（可缩放矢量图形）、使用可缓存的外部 SVG/图片、从雪碧图中裁取，或沿用图标字体。选择时要看图标颜色能否随状态改变、是否跨页面复用、下载与缓存边界，以及控件怎样获得可访问名称。

### SVG 怎样兼顾颜色、复用与替代文本？

同页面中的行内 SVG 是文档的一部分，可以用 CSS 设置颜色；让形状使用 `currentColor`（当前文字颜色），就能跟随按钮的 `color`（文字颜色）。按钮已有可见文字时，图标只是装饰：

~~~html
<button type="button" class="report-action">
  <svg class="report-action__icon" viewBox="0 0 16 16" aria-hidden="true">
    <path d="M7 2h2v5h5v2H9v5H7V9H2V7h5z" fill="currentColor" />
  </svg>
  <span>添加筛选条件</span>
</button>
~~~

~~~css
.report-action { color: #24547d; }
.report-action__icon { width: 1em; height: 1em; }
~~~

如果图标内容固定、在多个页面复用，可把 SVG 作为独立资源交给 `<img>`，从而按 URL 单独缓存。宿主页面的 CSS 不能直接选择外部 SVG 文档中的路径，SVG 里的 `currentColor` 也不会继承按钮颜色；信息图像应在 `<img alt>` 写替代文本，按钮内已有可见名称时用 `alt=""`：

~~~html
<button type="button">
  <img src="/assets/add-filter.svg" width="16" height="16" alt="">
  <span>添加筛选条件</span>
</button>
~~~

行内 SVG 便于按主题换色，但标记会随 HTML 一同传输；外部 SVG 可独立缓存和复用，缓存策略允许时多个页面可重用同一 URL、减少重复传输，却不适合直接由宿主页面逐路径改色。控件名称应来自控件内的可见文字、图片的替代文本，或显式关联的可访问名称；孤立的相邻文字不会自动成为控件名称。

### CSS Sprite 怎样裁出图集中的一格？

CSS Sprite（雪碧图）把多个小图排进同一张 sprite sheet（精灵图集），再用固定尺寸的盒子和 `background-position`（背景图像定位）露出目标区域。假设图集是 `64 × 32px`，每格 `16 × 16px`，共有 4 列、2 行：

```text
x →    0      16      32      48
y   ┌──────┬──────┬──────┬──────┐
0   │  1   │  2   │  3   │  4   │
    ├──────┼──────┼──────┼──────┤
16  │  5   │  6   │ [7]  │  8   │
    └──────┴──────┴──────┴──────┘
```

> [!example] 第二行第三列的坐标
> 以左上角为原点，该格左上角在 `(32, 16)`；背景向左、向上移动对应距离后，它落在 `16 × 16px` 的视窗内，所以两个定位偏移写成 `-32px -16px`。

~~~css
.icon-edit {
  display: inline-block;
  width: 16px;
  height: 16px;
  background-image: url("/assets/report-icons.png");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
~~~

图集变化时，每个图标坐标都可能要更新；改动一个格子也会改变整张图集资源，页面需要获取更新后的整份图像。若用内容哈希命名，文件 URL 也随之变化。图标多时可由资源构建步骤生成坐标，避免人工维护数字。背景图本身不提供有意义的替代文本；功能图标要由按钮或链接的可访问名称表达。

若图片本身承载信息，使用 `<img>` 提供替代文本，并按[图片资源加载规则](#26.%20%E5%9B%BE%E7%89%87%E4%B8%8E%E5%AA%92%E4%BD%93%E8%B5%84%E6%BA%90%E6%80%8E%E6%A0%B7%E5%8A%A0%E8%BD%BD%E5%B9%B6%E4%BF%9D%E6%8C%81%E9%A1%B5%E9%9D%A2%E7%A8%B3%E5%AE%9A%EF%BC%9F)处理宽高、候选资源和加载时机。

### Sprite 是否一定比独立图片快？

合并能减少一些独立资源请求，但并不自动减少总传输量：页面可能为一个图标下载整张图集。HTTP/2 可在一个连接上多路复用多个流，图片请求数也不等于每张图都新建连接。比较时按实际页面测总字节、压缩、缓存复用和更新频率；图标经常独立变化或只在少数页面出现时，分开缓存可能更合适。

### 图标字体怎样保留可访问名称？

icon font（图标字体）把图案映射到字体字形，因此可按文字方式用 CSS 控制颜色和尺寸。每个私用区码点只对配套字体文件有意义；字体载入失败时，外形可能缺失或变成替代符号。把图标保持为装饰，让按钮或链接文字承担功能名称：

~~~css
@font-face {
  font-family: "report-icons";
  src: url("/assets/report-icons.woff2") format("woff2");
}

.icon {
  font-family: "report-icons";
  font-size: 1.25rem;
  line-height: 1;
}
~~~

~~~html
<button type="button">
  <span class="icon" aria-hidden="true">&#xe900;</span>
  <span>编辑报表</span>
</button>
~~~

`aria-hidden="true"` 把纯装饰字形从辅助技术呈现中隐藏，按钮的可见文字仍提供名称。若设计确实是无文字图标按钮，应给按钮本身设置合适名称，例如 `aria-label="编辑报表"`；不要让私用区字符成为唯一可理解的名称。

### 旧横幅图展示的是静态选中项

雪碧图从同一张资源里裁出装饰性小图；横幅则按状态显示完整图片，图片角色不同会影响替代文本和加载时机。下面保留归档横幅图与 `.current` 片段，展示静态选中项。图片原件保持不变：

![归档横幅原图](../../archive/front-end/0-1_Learning_Notes/HTML/banner.png)

旧例用 `.current` 显示选中的一项，是静态横幅切换状态的 CSS 片段：

~~~html
<ul class="report-banner">
  <li class="current">
    <a href="/reports/monthly"><img src="/assets/monthly-banner.jpg" alt="查看月度订单报表"></a>
  </li>
  <li>
    <a href="/reports/quarterly"><img src="/assets/quarterly-banner.jpg" alt="查看季度订单报表"></a>
  </li>
</ul>
~~~

~~~css
.report-banner {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 5;
  margin: 0;
  padding: 0;
  list-style: none;
}
.report-banner li { position: absolute; inset: 0; display: none; }
.report-banner li.current { display: block; }
.report-banner img { display: block; width: 100%; height: 100%; object-fit: cover; }
~~~

这段代码只决定哪项显示；它没有自动轮换、前后按钮、键盘模式或暂停控制，因此不构成完整轮播。真正的自动轮播需提供操作控制并照顾焦点、悬停和减少动态效果；连续移动图片的装饰演算见[CSS 过渡与动画](#24.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%BF%87%E6%B8%A1%EF%BC%8C%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E5%85%B3%E9%94%AE%E5%B8%A7%E5%8A%A8%E7%94%BB%EF%BC%9F)。

> [!info]- 来源
> - 背景图像坐标：W3C CSS Backgrounds and Borders Level 3，Candidate Recommendation Draft（2024-03-11），[background-position](https://www.w3.org/TR/css-backgrounds-3/#the-background-position)，检查于 2026-11-06。
> - 多路复用：IETF RFC 9113，HTTP/2，Standards Track（2022-06），[Streams and multiplexing](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing)，检查于 2026-11-06。
> - HTTP 缓存语义：IETF RFC 9111，HTTP Caching，Standards Track（2022-06），[HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，检查于 2026-11-06。
> - 可下载字体及 <code>@font-face</code>：W3C CSS Fonts Level 4，Working Draft（2026-11-04），[CSS Fonts Level 4](https://www.w3.org/TR/css-fonts-4/)，检查于 2026-11-06。
> - 隐藏装饰字形并保留控件名称：W3C WAI-ARIA 1.2，Recommendation（2023-06-06），[`aria-hidden`](https://www.w3.org/TR/wai-aria-1.2/#aria-hidden)，及 WAI [Images Tutorial](https://www.w3.org/WAI/tutorials/images/)，检查于 2026-11-06。
> - SVG 文档、形状与呈现：W3C SVG 2，Candidate Recommendation Snapshot（2026-10-06），[SVG 2](https://www.w3.org/TR/SVG2/)，检查于 2026-11-06；该快照预计不早于 2026-12-01 进入 Recommendation 阶段。
> - `currentColor` 值：W3C CSS Color Level 4，Candidate Recommendation Draft（2026-11-03），[currentcolor](https://www.w3.org/TR/css-color-4/#valdef-color-currentcolor)，检查于 2026-11-06。
> - `<img>` 的替代文本和图标规则：WHATWG HTML Living Standard（2026-11-05 更新），[Images](https://html.spec.whatwg.org/multipage/images.html#the-img-element)，检查于 2026-11-06；外部 SVG 作为图像资源时的处理见 [SVG 2: embedded content](https://www.w3.org/TR/SVG2/embedded.html)。
> - 自动轮播控制：W3C WAI [ARIA APG Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)，检查于 2026-11-06。
## 28. JavaScript 值如何转换、比较，并成为属性键？

**案例背景：**2026 年 10 月的报表导入中，`first` 与 `retry` 的 `reportId` 相同但金额不同，`rows` 还保留了一个缺失位置。导入代码需要保住合法的零金额、识别缺行，并决定按业务键还是对象身份查记录。本章用这组输入说明值转换、相等比较、对象图比较和属性键转换；后续章节沿用同一组输入：

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
const rows = [first, , retry]; // 第二个位置是空位；第三项是重试记录
~~~

业务字段 `reportId` 相同，表示两条输入记录描述同一业务实体；`first` 与 `retry` 仍是两个对象。它们的 `owner` 字段也指向内容相同、身份不同的对象。

### 值的类型决定哪些转换有意义

JavaScript 有七种 primitive types（原始值类型）：`undefined`（未定义值）、`null`（空值）、`Boolean`（布尔值）、`Number`（数值）、`BigInt`（大整数）、`String`（字符串）和 `Symbol`（符号）。`Symbol()` 每次调用都会产生新值；`Symbol.for(key)` 则会从全局注册表取回同一注册符号。其他值都是 `object`（对象），函数也属于对象。对象赋值复制的是对象引用值，两个变量可以指向同一个对象；这是一条语言行为规则，不意味着对象一定物理存放在某个特定内存区域。

| 类型 | 本章会用到的行为 |
|---|---|
| `undefined` | 缺少属性或越界读取的常见结果；也可显式存入属性 |
| `null` | 显式表示“当前没有对象”；历史兼容使 `typeof null` 返回 `"object"` |
| `Boolean` | 只有 `false` 为假值 |
| `Number` | `binary64`（二进制 64 位浮点）数值；包含 `NaN`、正负无穷和带符号的零 |
| `BigInt` | 任意精度整数；不能直接与 `Number` 混做算术 |
| `String` | 不可变的 UTF-16 `code unit` 序列 |
| `Symbol` | 唯一的原始值，可作为属性键 |

值的运行时存储位置和布局由引擎决定；reference type（引用类型）可用来简称对象按身份传递的语义，但不能据此推断栈、堆或指针布局。

### 真值转换不是数值转换

`0` 是假值，但空数组和空对象是真值；非空字符串 `"false"` 也是真值。`Number` 转换遵循另一套规则，因此输入含义重要时应显式转换。

`Boolean(value)` 与 `!!value` 都执行真值转换；在历史浏览器对象 `document.all` 上，二者也都返回 `false`，因为标准为它保留了特殊例外。

~~~javascript
Boolean("false");  // true
Boolean([]);       // true
Boolean({});       // true

Number("");        // 0
Number(null);      // 0
Number(undefined); // NaN

Number.isNaN(NaN);  // true
Number.isNaN("x");  // false：不做隐式转换
~~~

浏览器里的历史对象 `document.all` 带有标准附录定义的特殊行为，此外 `typeof document.all` 为 `"undefined"`，且 `document.all == null` 为 `true`。普通对象的真值规则不受影响，业务代码不应依赖这个例外。

逻辑运算也不会自动把结果变成 `Boolean`。逻辑与 `&&` 返回某个操作数，因此 React 条件渲染中，`0 && <ItemList />` 的结果是 `0`，可能直接显示数字零；条件需要表达“条数大于零”时就写出比较条件。

~~~jsx
0 && <ItemList />; // 结果为 0

function ReportPanel({ validCount, rows }) {
  return validCount > 0 ? <ItemList items={rows} /> : null;
}
~~~

### 比较运算回答的是不同问题

strict equality（严格相等，`===`）不做跨类型强制转换；loose equality（宽松相等，`==`）遵循多条转换规则，包括 `null == undefined` 这一特殊情况。除非特意使用转换规则，通常优先用 `===`。对一般输入，`value == null` 是一种有意同时判断 `null` 与 `undefined` 的写法。

对象比较关注的是 identity（身份）：两个对象字段相同，也不会因此变成同一对象。

~~~javascript
first.reportId === retry.reportId; // true：业务字段相等
first === retry;                    // false：对象身份不同
first.owner === retry.owner;        // false：嵌套对象身份不同

5 == "5";              // true：字符串转换为数值后比较
5 === "5";             // false
null == undefined;     // true
~~~

几个常见比较规则的差别集中在 NaN、有符号零和对象上：

| 操作 | NaN 与自身 | +0 与 -0 | 对象 |
|---|---|---|---|
| === | 不相等 | 相等 | 按身份 |
| `Object.is`（SameValue，同值） | 相等 | 不同 | 按身份 |
| `Map`（映射） / `Set`（集合，SameValueZero，同值零） | 相等 | 相等 | 按身份 |

~~~javascript
NaN === NaN;                    // false
Object.is(NaN, NaN);            // true
Object.is(+0, -0);              // false
new Set([NaN, NaN, -0, +0]).size; // 2
~~~

`Map` 和 `Set` 使用 SameValueZero（同值零），所以它们既能识别重复 `NaN`，也会把 `+0` 和 `-0` 视为同一个键或成员。集合章节把这个规则用于报表索引和去重，见[何时使用 Map、Set 或普通对象？](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

`Number` 采用 IEEE 754 `binary64`（二进制 64 位浮点）；`0.1` 和 `0.2` 这样的十进制小数通常没有精确的有限二进制表示。比较结果是否可接受需要由金额精度、容差和舍入规则共同决定，不能把某个固定 `epsilon`（误差容限）当作所有领域的通用答案。

~~~javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // 对这个量级的例子成立
~~~

金额可在币种规则允许时用最小单位整数表示，或使用明确舍入规则的十进制运算。

### 结构比较要把输入范围写成契约

`===` 对对象只比较身份；业务判断有时还需要问两份输入是否有相同的数据结构。这不是 JavaScript 内建的统一规则，比较结果取决于应用选择的输入契约。这里比较筛选条件和接口纯数据：普通对象键的插入顺序不重要，数组顺序重要，键缺失与显式 `undefined` 不同。

本例只讨论有限、无环的数据对象图；不同属性可以共享同一个子对象。容器限于当前 realm（执行环境）的普通数组、普通对象或 null 原型对象；叶子是 `null`、`undefined`、布尔值、字符串或数字；容器的数据属性为自有、可枚举的字符串键。数组的 `length` 是不可枚举的自有属性，因此代码会单独比较它，再比较可枚举键。Symbol 或其他不可枚举属性、访问器、代理、函数、BigInt、Symbol 值及 Date、Map 等带内部状态的对象都在契约之外；代码不负责检测循环，调用方必须保证输入无环。普通对象可继承标准 `Object.prototype` 成员，但继承属性不参与比较。调用方应先保证输入符合契约；这段递归代码不是验证不可信对象的通用入口。

~~~javascript
function isPlainObject(value) {
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function deepEqual(left, right) {
  const leftIsObject = left !== null && typeof left === "object";
  const rightIsObject = right !== null && typeof right === "object";
  if (!leftIsObject || !rightIsObject) {
    return !leftIsObject && !rightIsObject && Object.is(left, right);
  }

  const leftIsArray = Array.isArray(left);
  const rightIsArray = Array.isArray(right);
  if (leftIsArray !== rightIsArray) return false;

  if (leftIsArray) {
    if (Object.getPrototypeOf(left) !== Array.prototype ||
        Object.getPrototypeOf(right) !== Array.prototype) {
      throw new TypeError("只支持当前 realm 的普通数组");
    }
    if (left.length !== right.length) return false;
  } else {
    if (!isPlainObject(left) || !isPlainObject(right)) {
      throw new TypeError("只支持普通对象或 null 原型对象");
    }
    if (Object.getPrototypeOf(left) !== Object.getPrototypeOf(right)) {
      return false;
    }
  }

  if (Object.is(left, right)) return true;

  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) return false;

  for (const key of leftKeys) {
    if (!Object.hasOwn(right, key)) return false;

    const leftDescriptor = Object.getOwnPropertyDescriptor(left, key);
    const rightDescriptor = Object.getOwnPropertyDescriptor(right, key);
    if (!Object.hasOwn(leftDescriptor, "value") ||
        !Object.hasOwn(rightDescriptor, "value")) {
      throw new TypeError("只支持数据属性");
    }
    if (!deepEqual(leftDescriptor.value, rightDescriptor.value)) {
      return false;
    }
  }
  return true;
}
~~~

递归步骤可以按四件事复算：先区分叶子与容器，叶子用 `Object.is`；再确认两边同为数组或对象；对象原型类别不同就不相等，数组先比不可枚举的 `length`；最后比较可枚举自有键集合，并对每个键的值递归。对象键次序因此不影响结果；数组索引是否存在仍影响结果，因为空位不在 `Object.keys` 里。使用属性描述符读取数据值，不会调用输入 getter；当比较走到一个可枚举访问器属性时会抛 `TypeError`。若两边是同一对象引用，容器类别检查后就会由 `Object.is` 短路，因此本函数不能用作输入验证器。

| 输入 | 差异 | 结果 |
| --- | --- | --- |
| `{ a: 1, b: 2 }` 与 `{ b: 2, a: 1 }` | 只有键插入顺序不同 | `true` |
| `{ amount: undefined }` 与 `{}` | 自有键缺失 | `false` |
| `[]` 与 `[,]` | 数组 `length` 分别为 0 与 1 | `false` |
| `[,]` 与 `[undefined]` | 前者索引 0 是空位，后者有自有元素 | `false` |
| `[1, 2]` 与 `[2, 1]` | 数组值的索引顺序不同 | `false` |
| `{ value: NaN }` 与 `{ value: NaN }` | `Object.is(NaN, NaN)` | `true` |
| `{ value: -0 }` 与 `{ value: +0 }` | `Object.is(-0, +0)` | `false` |
| `{}` 与 `Object.create(null)` | 自有键相同，原型类别不同 | `false` |
| 左侧两个属性共享同一子对象，右侧各自保存等值副本 | 比较值，不维护两边的共享身份关系 | `true` |
| 两个不同的 `new Date(0)` | Date 有本契约之外的内部状态 | 抛 `TypeError` |

同一批报表行能把身份比较和结构比较区分开：两个 `owner` 的引用不同，但按本契约内容相等；两条记录的金额不同，因此结构不相等。

例如，两个记录可以分别共享一个等值子对象，比较器会按值递归，不要求两侧的共享关系一致。普通对象和 null 原型对象都可装载键值，但本契约把它们的原型类别也纳入结果：

~~~javascript
deepEqual({}, Object.create(null)); // false
deepEqual({ value: NaN }, { value: NaN }); // true
deepEqual({ value: -0 }, { value: +0 });   // false
deepEqual(first.owner, retry.owner); // true：引用不同，数据相同
deepEqual(first, retry); // false：amount 不同
~~~

单看可见原型不能证明一个对象确实是纯数据：把 Date 的原型手动改成 `Object.prototype` 会越过这项检查。因此，输入边界必须保证对象来自可信的纯数据构造流程；对任意对象、Proxy 或带隐藏内部状态的值，先用适合其来源的解析和校验。递归深度仍受 JavaScript 调用栈限制；无环是本例前提，代码不负责检测环。

用 `JSON.stringify` 直接比较字符串也不是结构相等：属性插入顺序可能改变输出，显式 `undefined` 属性会被省略，数值 `-0` 会序列化成 `0`。

~~~javascript
JSON.stringify({ a: 1, b: 2 }) === JSON.stringify({ b: 2, a: 1 }); // false
JSON.stringify({ amount: undefined }) === JSON.stringify({});    // true
JSON.stringify({ amount: -0 }) === JSON.stringify({ amount: 0 }); // true
~~~

若这些差异会影响业务判断，应比较经过约束的数据结构；对象隔离或保留共享身份关系则是复制问题，见[如何安全地深拷贝 JavaScript 值？](#31.%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E6%B7%B1%E6%8B%B7%E8%B4%9D%20JavaScript%20%E5%80%BC%EF%BC%9F)。


### 变量保存对象身份，不会自动复制对象

把对象赋给新变量后，两个绑定仍指向同一个对象。属性赋值会先求出并记录左侧的基对象，再求右侧；右侧即使重新绑定变量，也不会改变已记录的基对象。

~~~javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }：写入落在先前记录的旧对象上
~~~

求值顺序可拆成三步：赋值左侧先记下旧对象 `A` 的 `x` 属性位置，右侧再把 `a` 改指向新对象 `B`，最后把 `B` 写进已记下的 `A.x`。

![赋值顺序：先记录旧对象的 x 属性位置，再把新对象写入该位置](../../frontend/javascript/resources/javascript-types-assignment-order.svg)

*图：左侧求值时固定写入位置；整个表达式求值完成后，`a` 与 `b` 分别指向新旧对象。*

函数实参按值传递：形参拿到实参值的副本。实参若是原始值，修改形参不改调用方的绑定；若是对象，副本仍指向同一对象，所以属性变更可见，但重新给形参赋另一个对象不会重绑调用方变量。

~~~javascript
function update(count, profile) {
  count += 1;
  profile.name = "Grace";
  profile = { name: "Replacement" };
}

let count = 1;
const profile = { name: "Ada" };
update(count, profile);
count;        // 1
profile.name; // "Grace"
~~~

这也解释了浅拷贝为何会共享嵌套对象：新数组或新记录只复制了里面的对象引用。数组变异、复制和空位规则见[数组操作怎样处理空位与复制？](#30.%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E4%B8%8E%E5%A4%8D%E5%88%B6%EF%BC%9F)；需要隔离整张对象图时见[如何安全地深拷贝 JavaScript 值？](#31.%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E6%B7%B1%E6%8B%B7%E8%B4%9D%20JavaScript%20%E5%80%BC%EF%BC%9F)。

### 类型检查能回答什么，不能证明什么

- `typeof` 适合检查原始值和函数，但 `typeof null` 的历史结果是 "object"。
- `Array.isArray` 检查数组，也能识别来自另一个 realm（执行环境）的数组。
- `instanceof` 通常检查构造函数的 `prototype` 是否出现在对象原型链上。不同 realm 的构造函数拥有不同 prototype，因此本地 Array 检查另一个窗口创建的数组可能为 false；`Symbol.hasInstance` 还可以定制检查。
- `Object.prototype.toString.call(value)` 给出内建标签，但 `Symbol.toStringTag` 可以改变显示结果，标签不是类型证明。

~~~javascript
typeof null; // "object"
Array.isArray([]); // true

const misleading = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(misleading); // "[object Array]"，但它不是数组
~~~

应检查程序真正需要的形状或行为，而不是只依赖通用标签。

### 普通对象属性键会先转换

普通对象的属性键只能是字符串或 `Symbol`。方括号里传入其他值时，JavaScript 会执行 `ToPropertyKey`（转成属性键）；对象可以通过 `Symbol.toPrimitive` 等钩子影响转换结果，因此不能简单概括为“总是调用 `toString`”。

转换分两步：`ToPropertyKey` 先用字符串提示（string hint）调用 `ToPrimitive`（转成原始值）；对象若提供可调用的 `Symbol.toPrimitive` 就以该提示调用它，若提供了非 `null`/`undefined` 的不可调用值则报错。没有这个方法时，普通转换依次试 `toString`、`valueOf`，取第一个原始值。得到 `Symbol` 时原样保留，其他原始值再转成字符串；`Symbol.toPrimitive` 若返回对象会抛出 `TypeError`，普通转换若两个方法都未返回原始值也会抛错。

| 键输入 | `ToPrimitive` 的结果 | 最终属性键 |
|---|---|---|
| `123` | 数值 `123` | 字符串 `"123"` |
| `accountKey` | 字符串 `"account"` | 字符串 `"account"` |
| `symbolKey` | `Symbol("account")` | 同一个 Symbol |
| `first`、`retry` | 各自都得到字符串 `"[object Object]"` | 同一个字符串键；后写值覆盖先写值 |

`first` 和 `retry` 都没有自定义转换钩子；它们继承的 `Object.prototype.toString` 先返回相同的 `"[object Object]"`，于是普通对象转换在 `toString` 这一步就结束了。

~~~javascript
const dictionary = {};
dictionary[123] = "number key";
dictionary["123"]; // "number key"

const accountKey = {
  [Symbol.toPrimitive](hint) {
    console.log(hint); // "string"
    return "account";
  },
};
dictionary[accountKey] = "Ada";
dictionary.account; // "Ada"

const symbol = Symbol("account");
const symbolKey = {
  [Symbol.toPrimitive](hint) {
    console.log(hint); // "string"
    return symbol;
  },
};
dictionary[symbolKey] = "symbol key";
dictionary[symbol]; // "symbol key"：Symbol 被保留为属性键

dictionary[first] = "first object";
dictionary[retry] = "retry object";
dictionary["[object Object]"]; // "retry object"：默认转换相同，后写覆盖先写
~~~

如果键需要保持对象身份、数字与字符串必须区分，或需要任意类型的键，使用 `Map`。若普通对象确实是字典，可用 `Object.create(null)` 去掉继承原型行为，并用 `Object.hasOwn` 检查自有属性。键值集合的选择见[何时使用 Map、Set 或普通对象？](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

### 枚举与复制属性时，先看 API 选中了什么

`Object.keys`、`Object.values` 和 `Object.entries` 选择同一类属性：自有、可枚举、字符串键；`Symbol` 键不在结果中。`keys` 只列键；`values` 和 `entries` 会读取相应的值，因此可能调用 getter。普通对象的数组索引键先按数值升序排列，其他字符串键按创建顺序排列；`Proxy` 和特殊对象可能有不同的键顺序。`for...in` 还会遍历可枚举的继承字符串键，因此对象数据和数组索引应选不同的遍历方式。

~~~javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]
Object.entries(record); // [["name", "Ada"], ["age", 36]]

const keyOrder = {};
keyOrder["4294967296"] = "large integer, not an array index";
keyOrder["4294967295"] = "one past the maximum array index";
keyOrder["2"] = "array index";
Object.keys(keyOrder);
// ["2", "4294967296", "4294967295"]

for (const [key, value] of Object.entries(record)) {
  console.log(key, value);
}
~~~

`Object.assign(target, ...sources)` 把来源对象的自有可枚举字符串键和 `Symbol` 键浅复制到已有 target，修改并返回 target，后面的来源覆盖前面的属性。读取来源可能触发 getter，写入 target 可能触发 setter。对象展开也浅复制，但会在新对象上创建数据属性，不会写入传入的已有 target。

~~~javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target 是 { a: 1, b: 3, c: 4 }

const defaults = { retries: 2 };
const overrides = { retries: 4 };
const merged = { ...defaults, ...overrides };
// merged 是新对象；retries 为 4，defaults 不变
~~~

这些方法适合检查或组装属性记录，不会深拷贝嵌套对象。数组的复制、迭代输入与空位结果见[数组操作怎样处理空位与复制？](#30.%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E4%B8%8E%E5%A4%8D%E5%88%B6%EF%BC%9F)；复杂对象图的隔离见[如何安全地深拷贝 JavaScript 值？](#31.%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E6%B7%B1%E6%8B%B7%E8%B4%9D%20JavaScript%20%E5%80%BC%EF%BC%9F)。

### 缺失属性默认值与解构

读取嵌套字段时，optional chaining（可选链）运算符 `?.` 只在它检查的值为 `null` 或 `undefined` 时短路，不把 `0`、`false` 或空字符串当成缺失。根变量本身若未声明，使用 `?.` 仍会抛 `ReferenceError`；用括号结束一段链后，括号外的普通属性读取也不再受短路保护。

~~~javascript
const report = { profile: null, rows };
report.profile?.name; // undefined
// report?.profile.name; // TypeError：report 存在，但后续普通访问 .name 遇到 null
report.rows[0]?.amount; // 0：合法的零值
report.rows[1]?.amount; // undefined：读取空位

const count = 0;
count?.toFixed(0); // "0"：零既非 null 也非 undefined

const key = "value";
({ value: 1 })?.[key]; // 1
const maybeCall = undefined;
maybeCall?.(); // undefined

const user = null;
user?.profile?.name; // undefined
// (user?.profile).name; // TypeError：括号结束了短路链
// undeclaredUser?.name; // ReferenceError：根标识符不存在
~~~

若只有缺省值应触发回退，使用 nullish coalescing（空值合并）运算符 `??`；`||` 会把所有假值都替换。它们在此沿用同一个报表值，因此金额 `0` 仍保留，而空位读取产生的 `undefined` 会触发默认值。`??` 与 `||` 或 `&&` 不能不加括号混用。

~~~javascript
report.rows[0].amount ?? 100; // 0
report.rows[0].amount || 100; // 100
report.rows[1]?.amount ?? 100; // 100
~~~

destructuring（解构）把属性或可迭代值绑定到局部变量。默认初始化仅在读到 `undefined` 时运行，所以不会覆盖合法零值、`false`、空字符串或 `null`。对象剩余项收集来源对象余下的自有可枚举属性，但只复制一层；数组解构按迭代器取值，省略绑定仍会向前消费一个值。

~~~javascript
const { amount: firstAmount = 100, owner: firstOwner, ...rowFields } = first;
// firstAmount 是 0；firstOwner 仍是 first.owner；rowFields 只创建浅层新对象

const { profile = { name: "Guest" } } = report;
profile; // null：默认值只处理 undefined

const [firstRow, , ...tail] = rows;
firstRow === first; // true
tail[0] === retry; // true：rest 收集剩余项，形成新数组
Object.hasOwn(rows, 1); // false：索引 1 没有自有属性
1 in rows; // false：本例的原型链上也没有索引 1
rowFields; // { reportId: "r-104" }：只剩下 first 的其他自有可枚举字段
~~~

数组解构和数组展开同样消费迭代器；本例原型链没有索引 1，所以空位被读成 `undefined`。`Object.hasOwn` 可区分自有索引与空位，`in` 还会检查原型链：继承索引可让 `Object.hasOwn(rows, 1)` 为假而 `1 in rows` 为真。数组空位的其他读取结果见[数组空位如何改变遍历结果？](#%E7%A9%BA%E4%BD%8D%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E9%81%8D%E5%8E%86%E7%BB%93%E6%9E%9C)；同一个属性是否缺失或显式为 `undefined`，也不能只靠读取结果区分。

### 模板标签收到值，但不会自动净化它

模板字面量（template literal）会把表达式插入文本。tagged template（带标签模板）调用函数时，会把固定文本片段和各个表达式值分开传入；标签函数可以做格式化或领域处理，但插入用户输入不会因此自动安全。

~~~javascript
function capture(strings, ...values) {
  return { strings: [...strings], values };
}

const untrusted = "<b>user text</b>";
capture`label: ${untrusted}`;
// strings 是 ["label: ", ""]；values 是 ["<b>user text</b>"]
~~~

标签函数需要按实际输出上下文选择转义或净化规则，不能把“使用了 tagged template”当作安全保证。报表文本进入 DOM 时的上下文边界见[报表标题进入 DOM 时如何避免 XSS？](../../engineering-foundations/security/web-browser-security-boundaries.md)。

> [!info]- 来源
> - 值类型、原始值与对象行为：[ECMAScript 2026 §6.1–6.2](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html)。
> - 严格相等、SameValue、SameValueZero 和宽松相等：[ECMAScript 2026 §7.2.9、§7.2.10、§7.2.13、§7.2.14](https://tc39.es/ecma262/2026/multipage/abstract-operations.html)，访问于 2026-11-12。
> - 属性键转换先执行 `ToPrimitive`（含 string hint 下的 `OrdinaryToPrimitive`），再按 Symbol 保留或转成字符串：[ECMAScript 2026 §7.1.1、§7.1.1.1、§7.1.19](https://tc39.es/ecma262/2026/multipage/abstract-operations.html)，访问于 2026-11-12。
> - 本章教学 `deepEqual` 的属性描述符与数组检查：[ECMAScript 2026 — OrdinaryGetOwnProperty](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarygetownproperty)、[Array Exotic Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-array-exotic-objects)、[Object.hasOwn](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)、[数组实例的 length](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-properties-of-array-instances-length)，访问于 2026-11-12。比较契约、不支持类型及“输入必须无环”由本章示例定义。
> - 赋值先求得左侧引用，再求右侧值并写回：[ECMAScript 2026 §13.15.2 Assignment Operators — Runtime Semantics](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-assignment-operators-runtime-semantics-evaluation)，访问于 2026-11-12。
> - `JSON.stringify` 对不可表示的对象值、`undefined` 属性、数字与属性枚举顺序的处理：[ECMAScript 2026 §25.5.4.2、§25.5.4.5、§10.1.11.1](https://tc39.es/ecma262/2026/)，访问于 2026-11-12。
> - `document.all` 的历史例外：[ECMAScript 2026 Annex B IsHTMLDDA internal slot](https://tc39.es/ecma262/2026/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。
> - `instanceof` 与 `Object.prototype.toString` 的检查行为：[ECMAScript 2026 §13.10.2 InstanceofOperator](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-instanceofoperator)、[§20.1.3.6 Object.prototype.toString](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.prototype.tostring)。
> - Object.keys / values / entries 与 Object.assign 的属性范围：[ECMAScript 2026 §20.1.2](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html)；普通对象的键顺序：[§10.1.11.1 OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)。
> - 可选链与空值合并的短路条件、运算优先级：[ECMAScript 2026 §13.3.9 Optional Chains](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-optional-chains) 与 [§13.13 Binary Logical Operators](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-binary-logical-operators)。
> - 对象与数组解构默认值、剩余项和迭代读取：[ECMAScript 2026 §14.3.3 Destructuring Binding Patterns](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-destructuring-binding-patterns)；数组迭代器及空位的属性读取：[ECMAScript 2026 §23.1.3.38 Array.prototype.values](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)；自有性测试：[§20.1.2.14 Object.hasOwn](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)，访问于 2026-11-12。
> - 带标签模板调用参数的组成：[ECMAScript 2026 §13.3.11 Tagged Templates](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-tagged-templates)。
> - React 条件渲染中 0 会作为结果呈现：[React 文档 Conditional Rendering](https://react.dev/learn/conditional-rendering)，访问于 2026-11-06。
> - 本章值转换和相等示例在 Node.js v26.13.0 / V8 14.6.202.34-node.40 执行，2026-11-12；`deepEqual` 边界用例同版本执行，原始复演日期 2026-11-09。
## 29. 何时使用 Map、Set 或普通对象？

报表导入按输入顺序逐条读取业务记录；同一个 `reportId` 可能出现重试。程序既要用 `Map`（映射）保留同一 `reportId` 最后读到的记录，也要为某个对象实例保存临时状态。选择数据结构前，先确定“相同”指什么、键需要什么类型，以及数据是否要按插入顺序遍历。对象字段与身份的比较规则见[JavaScript 值如何转换、比较，并成为属性键？](#28.%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%EF%BC%8C%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F)。

用一次导入中的两条记录说明这些选择：

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
~~~

两条记录的 `reportId` 和 `owner` 字段内容相同，但记录对象和 `owner` 对象的身份都不同。

后文的覆盖策略只保留输入顺序最后读到的一条；若业务要比较事件时间或版本号，必须先按该规则判断是否覆盖，`Map.set` 不会自行判断哪条记录更新。

### 先按数据形状选择

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Map`（映射） | 任意键值对、对象身份键、需要直接遍历或 `size` | 键可以是任意值；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员或反复进行成员查询 | 按插入顺序保存；成员按相等规则去重 |
| `Array`（数组） | 有位置、重复项或要按索引访问的数据 | 每个位置独立，即使值相同也可重复 |
| 普通对象 | 固定字段的记录，或确实需要字符串 / `Symbol` 属性键的字典 | 其他输入需先转换成字符串或 `Symbol`，转换也可能抛错；普通原型行为仍然存在 |

### Map 的键按值或身份匹配

`Map` 键可以是任意值。相同对象身份能查到原条目；字段完全相同但分别创建的两个对象是不同键。数字 `7` 和字符串 `"7"` 也不同。更新已有键只替换值，不移动其遍历位置；删除后重新插入才会移到末尾。

~~~javascript
const byId = new Map();
byId.set(7, { name: "Ada" });
byId.set("7", { name: "Grace" });

byId.get(7); // { name: "Ada" }
byId.has(8); // false
byId.size; // 2

const firstKey = { id: "r-104" };
const copiedKey = { id: "r-104" };
const byObject = new Map([[firstKey, "selected"], ["next", "another"]]);

byObject.get(copiedKey); // undefined：字段相同，身份不同
byObject.set(firstKey, "reviewed");
[...byObject.keys()]; // [firstKey, "next"]：更新不移动位置
byObject.delete(firstKey);
byObject.set(firstKey, "reselected"); // 删除后再插入，位于末尾
[...byObject.keys()]; // ["next", firstKey]
~~~

`Map` 使用 `SameValueZero`（同值零）：`NaN` 与 `NaN` 匹配，`+0` 与 `-0` 视为同一个键；对象则按身份匹配。常用操作是 `set`、`get`、`has`、`delete`、`clear` 和 `size`。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器产出 `[key, value]`；`forEach` 的参数顺序为 `(value, key, map)`。

`get(key)` 返回 `undefined` 既可能表示没有该键，也可能表示键存在且保存了 `undefined`；需要区分这两种状态时，再用 `has(key)`。

~~~javascript
const optionalValue = new Map([["cached", undefined]]);
[optionalValue.get("cached"), optionalValue.has("cached")]; // [undefined, true]
[optionalValue.get("missing"), optionalValue.has("missing")]; // [undefined, false]
~~~

默认 `Map` 迭代器会产出键值对，因此可直接解构遍历：

~~~javascript
const byName = new Map([["ada", { name: "Ada" }], ["grace", { name: "Grace" }]]);
for (const [id, person] of byName) {
  console.log(id, person.name);
}
~~~

例如，两个输入对象可以描述同一个 `reportId`，但其对象身份仍不同。按业务 id 索引要把字段作为键；若要区分具体对象实例，则直接以对象作键：

~~~javascript
const rowById = new Map();
rowById.set(first.reportId, first);
rowById.get("r-104") === first; // true：此时记录的是首条输入
rowById.set(retry.reportId, retry);

rowById.get("r-104") === retry; // true：后一次写入替换值
rowById.size; // 1

const metadataByRow = new Map([[first, { selected: true }]]);
metadataByRow.has(retry); // false：重试记录是另一个对象
~~~

### Set 按相等规则保留唯一值

`Set`（集合）保存唯一成员并按插入顺序遍历。删除后再次添加可以移动顺序。它也使用 `SameValueZero`（同值零），因此 `NaN` 只保留一次、有符号零合并，而两个对象即使字段相同仍是两个成员。

~~~javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]

const specialNumbers = new Set([NaN, NaN, -0, +0]);
[...specialNumbers]; // [NaN, 0]：NaN 去重，零合并

const importedIds = new Set([first.reportId, retry.reportId]);
[...importedIds]; // ["r-104"]：按业务 ID 去重

const selectedRows = new Set([first, retry]);
selectedRows.size; // 2：对象身份不同
~~~

常用操作是 `add`、`has`、`delete`、`clear` 和 `size`。`keys()` 与 `values()` 产出相同成员；`entries()` 为 `Map` 兼容性产出 `[value, value]`；`forEach` 的参数为 `(value, value, set)`。

ECMAScript 2025 标准化 `Set` 的 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。运算接收者必须是真正的 `Set`；另一侧可用类 Set 对象（Set-like object），但要遵守成员接口：`size` 报告成员数，`has(value)` 判断成员，`keys()` 返回逐个产出成员的迭代器。

规范先把 `size` 转成数值，若为 `NaN` 就抛 `TypeError`；其余数值转为整数或无穷，结果为负就抛 `RangeError`。仅能被 `for...of` 读取的数组不满足这个接口，数组也没有成员语义所需的 `size` 和 `has`；而 `keys()` 直接返回一个数组也不行，因为该算法要求它返回迭代器对象。`Map` 满足这组接口并按键参与运算。面向旧运行时仍需检查支持。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true

const availableByName = new Map([["search", true], ["admin", true]]);
[...enabled.intersection(availableByName)]; // ["search"]：按 Map 的键判断

const requestedInOrder = new Set(["review", "export", "search"]);
const supported = new Set(["export", "review"]);
[...requestedInOrder.intersection(supported)]; // ["export", "review"]

const sameSizeRequest = new Set(["review", "export"]);
const sameSizeSupport = new Set(["export", "review"]);
[...sameSizeRequest.intersection(sameSizeSupport)]; // ["review", "export"]：同大小时按接收者顺序

const arrayAsKeys = {
  size: 2,
  has(value) { return supported.has(value); },
  keys() { return ["export", "review"]; },
};
try {
  requestedInOrder.intersection(arrayAsKeys);
} catch (error) {
  error.name; // "TypeError"：keys() 返回的是数组，不是迭代器对象
}
~~~

`intersection` 根据接收者大小与参数 `size` 报告值选择迭代来源：接收者大小小于或等于该值时按接收者顺序检查；接收者较大时按参数 `keys()` 的成员迭代器顺序检查。因此结果 Set 的插入顺序不一定沿用接收者。三对二的例子按 `supported` 的顺序产生；同大小的例子按接收者顺序产生。若结果顺序用于展示，应显式确定排序规则。

### 普通对象仍适合固定字段与字典

记录 `{ reportId, amount, owner }` 的属性有固定名称时，用普通对象表达最清楚。属性键只能是字符串或 `Symbol`；把数字或对象等其他值放在方括号中时，JavaScript 会先执行属性键转换。数字 `123` 和字符串 `"123"` 因而会撞到同一个属性；若对象无法转换成原始值，访问会抛 `TypeError`。`Object.create(null)` 仅去掉继承原型，不会改变键转换。

~~~javascript
const dictionary = Object.create(null);
dictionary[123] = "number";
dictionary["123"]; // "number"

const record = { reportId: "r-104", amount: 0 };
Object.hasOwn(record, "amount"); // true
Object.hasOwn(record, "toString"); // false

function lookupDictionary(key) {
  try {
    return dictionary[key];
  } catch (error) {
    return error.name;
  }
}
lookupDictionary(Object.create(null)); // "TypeError"：对象键无法转换成原始值
~~~

`Object.hasOwn` 可区分自有和继承属性，也不会因对象覆盖了 `hasOwnProperty` 而失效。需要精确说明哪些属性可枚举、如何复制，请看[JavaScript 值如何转换、比较，并成为属性键？](#%E6%9E%9A%E4%B8%BE%E4%B8%8E%E5%A4%8D%E5%88%B6%E5%B1%9E%E6%80%A7%E6%97%B6%EF%BC%8C%E5%85%88%E7%9C%8B%20API%20%E9%80%89%E4%B8%AD%E4%BA%86%E4%BB%80%E4%B9%88)。

属性遍历顺序也与 `Map` 不同：`Object.keys` 先按数值顺序列出可枚举的自有数组索引键，再按创建顺序列出其他可枚举的自有字符串键；它不列 `Symbol` 键。若用对象表达字典，且处理结果依赖插入顺序，先确认代码实际采用的枚举 API 和键类型。

~~~javascript
const orderedObject = {};
orderedObject.z = "created first";
orderedObject["10"] = "index ten";
orderedObject["2"] = "index two";
Object.keys(orderedObject); // ["2", "10", "z"]
~~~

### 成本和生命周期也属于选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小为次线性，但不规定具体哈希表或常数时间实现。总体成本还取决于外围算法：如果过滤 n 个数组项时每次都新建同一张查找表，建表成本会被重复支付。需要比较数组去重、批量移除和排序的结果时，见[数组操作怎样处理空位与复制？](#30.%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E4%B8%8E%E5%A4%8D%E5%88%B6%EF%BC%9F)。

普通 `Map` 强持有当前条目中的键和值，`Set` 强持有当前成员。用 `Map.set` 替换已有键对应的值后，`Map` 不再因此持有被替换的旧值；删除条目也会解除该条目的持有。集合自身不再可达时，也不会仅靠内部引用让整个集合永久存活。对象实例的元数据若不应延长键对象寿命，可考虑 `WeakMap`（弱映射）；它不提供遍历、`size` 或确定的清理时间，详见[弱集合与弱引用能保证什么？](#38.%20%E5%BC%B1%E9%9B%86%E5%90%88%E4%B8%8E%E5%BC%B1%E5%BC%95%E7%94%A8%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - Map / Set 可接受的键、成员比较、遍历与平均次线性访问要求：[ECMAScript 2026 §§24.1–24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - `SameValueZero` 的定义：[ECMAScript 2026 §7.2.10](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Set 运算和 Set-like 参数契约：[ECMAScript 2025 §§24.2.1.2、24.2.4.5–24.2.4.16](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-getsetrecord)；`intersection` 按较小一侧遍历：[§24.2.4.9](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set.prototype.intersection)。
> - 普通对象自有键顺序与 `Object.keys` 的筛选范围：[ECMAScript 2026 §10.1.11.1](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys) 与 [§20.1.2.19](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.keys)。
> - 普通对象属性键转换为字符串或 `Symbol`：[ECMAScript 2026 §7.1.19 `ToPropertyKey`](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)；强集合与弱集合的键值及可观察边界：[§§24.1–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
## 30. JavaScript 数组操作如何处理空位、修改与复制？

2026 年 10 月月报导入两条 `reportId` 相同的记录：首条金额为 0，重试记录金额为 120；数组第二个位置刻意保留空位。本章先用这组报表行对照去重策略，再用短数组看空位、删除、排序与展平，在复制节回到 `rows` 和 `owner` 观察浅复制。选择哪条报表记录由业务规则决定：后文会比较 Map 保留最后一次写入与排序后保留组内首项的不同结果。

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
const rows = [first, , retry];
~~~

业务字段 `reportId` 相同，表示两条输入记录描述同一业务实体；`first` 与 `retry` 仍是两个对象。它们的 `owner` 字段也指向内容相同、身份不同的对象，后文用来说明浅复制共享嵌套对象。普通业务结果通常应使用稠密数组；这个空位用于辨别 JavaScript 操作的迭代契约。空位、显式 `undefined` 和数组迭代器返回的 `undefined` 不是同一个结构状态。

### 去重前先选“相同”的定义

对于原始值，`Set`（集合）按 `SameValueZero`（同值零）保留首次出现顺序。`NaN` 会和 `NaN` 合并，`+0` 与 `-0` 合并；对象按身份去重，字段相同但引用不同的对象仍会保留。相等规则和 `Map`（映射）/ `Set` 的键行为见[何时使用 Map、Set 或普通对象？](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

~~~javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2：对象身份不同
~~~

用 `indexOf` 过滤也能保留首次值，但 `indexOf` 使用严格相等，找不到 `NaN`；于是每个 `NaN` 都会因 `indexOf(NaN)` 返回 `-1` 而被过滤掉。`filter` 自身会跳过没有属性的位置。

~~~javascript
const values = [NaN, NaN, 1, 1];
values.filter((value, index) => values.indexOf(value) === index); // [1]
[...new Set(values)]; // [NaN, 1]
~~~

记录若按业务字段判重，用 `Map` 把字段映射到最后出现的对象。重复 `reportId` 的后一个对象替换值，而 `Map` 键的遍历位置仍取首次插入时的位置：

~~~javascript
function uniqueByReportId(items) {
  const byId = new Map();
  items.forEach(item => byId.set(item.reportId, item));
  return [...byId.values()];
}

uniqueByReportId(rows); // [retry]
~~~

这里使用 `forEach`，空位不会被当成一条记录；若输入可能包含显式 `undefined`，仍需在业务边界另行校验。重复项按 `reportId` 保留最后版本，是一个业务策略，不是 `Map` 自动推断出来的“对象相等”。

如果结果允许改变顺序，也可先排序副本，再对相邻项按同一业务等价关系去重。这个策略是“保留排序后每组首项”，不同于上面的 Map “保留最后一次写入”：当前输入的排序比较相等，稳定排序保留原顺序，所以结果会保留 `first`（金额 `0`），Map 结果则保留 `retry`（金额 `120`）。比较器必须把所有相等项排在一起；`same` 必须和 `compare` 表达同一组等价类。函数先用 `filter` 跳过普通空位；它假设原型链没有提供缺失索引，每个现存元素都是记录且不含显式 `undefined`，外部输入不满足时应先校验。

~~~javascript
function uniqueSorted(items, compare, same) {
  const result = [];
  const presentItems = items.filter(() => true); // 跳过空位，结果已是稠密副本
  for (const item of presentItems.sort(compare)) {
    if (result.length === 0 || !same(result[result.length - 1], item)) {
      result.push(item);
    }
  }
  return result;
}

uniqueSorted(
  rows,
  (left, right) => left.reportId === right.reportId ? 0
    : left.reportId < right.reportId ? -1 : 1,
  (left, right) => left.reportId === right.reportId,
).map(item => item.amount); // [0]：排序策略保留组内首项
uniqueByReportId(rows).map(item => item.amount); // [120]：Map 策略保留最后一次写入
~~~

`filter` 已经创建稠密副本，`sort` 只改变这个副本的顺序；这段方法不会修改 `items`，无需再展开复制一次。当“保留首次顺序”重要时，不要用排序去重替代 Set 或 Map。

### 删除匹配项时，选择副本还是原地修改

若原数组还要给其他调用方使用，用 `filter` 返回新数组。下面两个写法分别展示直接检查排除列表，和排除列表较大时先建一次 `Set`；`includes` 与 `Set.has` 都按 `SameValueZero` 判断值，比较对象时按身份。这里的副本/原地差异按稠密数组说明；稀疏数组会产生另一种结果。

~~~javascript
const removeWithFilter = (items, ...excluded) =>
  items.filter(item => !excluded.includes(item));

const removeWithSet = (items, ...excluded) => {
  const removed = new Set(excluded);
  return items.filter(item => !removed.has(item));
};

removeWithFilter([1, 2, 1, 3], 1); // [2, 3]
removeWithSet([NaN, 1, NaN], NaN); // [1]
~~~

第一种在长度为 n 的输入和 m 个排除值下会做至多 n×m 次成员比较；第二种建立一次 Set，再逐项查询。规范只要求 Set 的平均访问时间相对集合大小为次线性，不保证所有引擎的精确常数或具体实现。若移除对象记录的业务 id，应先从记录读取 id，而不是把一个“字段相同”的新对象当成同一对象。

若调用方明确要求原地修改，可用 `splice`；删除后索引上的后续元素会左移，因此命中时不应递增索引。

~~~javascript
function removeInPlace(items, ...excluded) {
  let index = 0;
  while (index < items.length) {
    if (excluded.includes(items[index])) items.splice(index, 1);
    else index += 1;
  }
  return items;
}

const mutable = [1, 2, 1, 3];
removeInPlace(mutable, 1); // mutable 变为 [2, 3]

const sparseForRemoval = [, 1];
const filteredRemoval = sparseForRemoval.filter(value => value !== 1);
const splicedRemoval = sparseForRemoval.slice();
removeInPlace(splicedRemoval, 1);
filteredRemoval; // []：filter 跳过空位
splicedRemoval.length; // 1：splice 删除 1 后保留了原空位
0 in splicedRemoval; // false
~~~

连续多次 splice 可能让整体移动成本接近平方级；大批删除通常先构造结果或采用一次线性压缩实现。原地循环读取空位会得到 `undefined`，若排除列表含 `undefined`，该空位也会被当作命中项删除；filter 则不会为它调用回调。

### 空位怎样改变遍历结果

空位表示该索引没有自有属性；它不同于存在一个值为 `undefined` 的属性。多数数组回调方法用 `HasProperty`（属性存在性检查）检查索引，因此普通稀疏数组的空位会被跳过；若原型链上存在同索引属性，该属性也可能被访问。`find` 系列（查找方法）会按查找方向逐个读取索引，遇到第一个使回调返回真值的位置就立即停止；原型链没有同索引属性时，空位会以 `undefined` 传给回调。

下表按没有继承索引属性的普通数组描述空位结果。

| 操作 | 输入有空位时的行为 | 是否改动原数组 |
|---|---|---|
| `map` | 跳过空位，并在对应结果位置保留空位 | 否 |
| `filter` | 跳过空位，结果只包含通过的现存值 | 否 |
| `forEach`、`some`、`every`、`reduce` | 普通空位不调用回调；`reduce` 无初始值且没有现存项时抛错 | 否 |
| `find`、`findIndex`、`findLast`、`findLastIndex` | 按查找方向读取；普通空位作为 `undefined` 传给回调，命中后立即停止 | 否 |
| `for...of`、数组展开 | 消费数组迭代器；无继承索引属性时，空位读成 `undefined` | 否 |
| `flat` | 被展平层级中自身与原型链都不存在的索引不写入结果 | 否 |
| `sort`、`reverse`、`splice` | 操作原接收数组；稀疏结构可能改变 | 是 |
| `toSorted`、`toReversed`、`toSpliced` | 生成副本；被复制的空位若无继承索引值，会写成显式 `undefined` | 否 |

~~~javascript
const sparse = [, "x"];

Object.hasOwn(sparse, 0); // false：索引 0 没有自有属性
0 in sparse; // false：原型链上也没有索引 0
sparse[0]; // undefined
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
const visited = [];
sparse.find((value, index) => {
  visited.push(index);
  return value === undefined;
});
visited; // [0]：空位读为 undefined 后命中，find 随即停止
[...sparse]; // [undefined, "x"]
Object.keys(sparse); // ["1"]
~~~

数组回调中的索引存在性检查也会看到原型链上的属性，因此某个“空位”若继承到同索引值，就会被 `map` 等方法访问。`for...in` 枚举可枚举的字符串属性名，可能包含自定义或继承属性；`for...of` 消费数组迭代器，读出位置上的值，通常更适合数组数据。

~~~javascript
const inheritedPrototype = Object.create(Array.prototype);
inheritedPrototype[0] = "from prototype";
const holeWithInheritedIndex = new Array(1);
Object.setPrototypeOf(holeWithInheritedIndex, inheritedPrototype);
Object.hasOwn(holeWithInheritedIndex, 0); // false：仍没有自有索引 0
0 in holeWithInheritedIndex; // true：原型链提供了索引 0
holeWithInheritedIndex[0]; // "from prototype"
holeWithInheritedIndex.map(value => value); // ["from prototype"]

const enumerableArray = [10, 20];
enumerableArray.note = "custom property";
const extraProperties = Object.create(Array.prototype);
extraProperties.label = "inherited property";
Object.setPrototypeOf(enumerableArray, extraProperties);

const keys = [];
for (const key in enumerableArray) keys.push(key);
keys; // ["0", "1", "note", "label"]

const values = [];
for (const value of enumerableArray) values.push(value);
values; // [10, 20]
~~~

`some` 和 `every` 在答案确定后会提前停止，也会跳过普通空位；空数组上 `some` 为 `false`，`every` 为 `true`。若需要判断“所有项都满足”但不接受空输入，需另行处理空数组。

~~~javascript
[].some(() => true); // false
[].every(() => false); // true
new Array(2).some(() => true); // false：空位不会调用回调
new Array(2).every(() => false); // true：所有空位都被跳过
~~~

`map` 和 `filter` 的回调都接收 `value`、`index`、`array`。把 `parseInt` 直接作为 `map` 回调会让索引被当作 `radix`；显式传入基数才能得到预期值。

~~~javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
~~~

### 从迭代器或类数组输入创建数组

`Array.from` 可以消费可迭代对象，也可以按 `length` 和索引读取类数组对象；可选映射函数能在创建时转换元素。对没有继承索引的普通稀疏数组，迭代器读取空位得到 `undefined`，所以结果是稠密数组；如果原型链提供该索引，则读取继承值。数组展开也消费迭代器并产生同样的结果，但不能像 `Array.from` 一样处理只有 `length` 和索引的类数组对象。

~~~javascript
Array.from(rows); // [first, undefined, retry]
Array.from(new Set(["paid", "review", "paid"])); // ["paid", "review"]
Array.from({ 0: "r-104", 1: "r-105", length: 2 }); // ["r-104", "r-105"]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]

Array(3);    // 长度为 3 的稀疏数组
Array.of(3); // [3]：参数本身作为元素
Array.of(1, 2, 3); // [1, 2, 3]
~~~

类数组读取、可迭代对象和 `Array.from` 的差异也会出现在[HTMLCollection 与 NodeList 如何处理实时集合？](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F)的 DOM 集合快照中；迭代协议本身见[迭代器与生成器如何按需产出值？](#43.%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E6%80%8E%E6%A0%B7%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%B9%B6%E6%B8%85%E7%90%86%E6%95%B0%E6%8D%AE%EF%BC%9F)。文本要按 Unicode 码点遍历时，`Array.from(string)` 也会消费字符串迭代器；用户感知字符可能由多个码点组成，还需另做分段，详见[文本算法应按什么单位计数和比较？](../../engineering-foundations/algorithms/text-units-and-algorithms.md)。

### 复制数组只复制一层

数组展开和 `slice` 会创建新数组，但元素值仍是原来的对象引用；修改复制数组内的嵌套记录，原数组仍能观察到这次属性变更。对原型链没有同索引属性的普通稀疏数组，`slice` 和 `concat` 保留空位；展开与 `Array.from` 通过迭代读取时会把它变为 `undefined`。

| 结果 | `Object.hasOwn(..., 1)` | 读取 `[1]` | 现存记录及 `owner` 是否仍共享 |
| --- | --- | --- | --- |
| `rows.slice()` | `false` | `undefined` | 是 |
| `[...rows]` | `true` | `undefined` | 是 |

~~~javascript
const slicedRows = rows.slice();
const spreadRows = [...rows];

Object.hasOwn(slicedRows, 1); // false：slice 保留这个空位
Object.hasOwn(spreadRows, 1); // true：展开写入显式 undefined
slicedRows[0] === rows[0]; // true：数组副本仍引用同一条记录
spreadRows[0].owner === rows[0].owner; // true：嵌套对象也共享
spreadRows[0].owner.name = "Grace";
rows[0].owner.name; // "Grace"：原数组仍可观察到同一对象的变化

const scoreRows = [{ score: 1 }];
const scoreCopy = [...scoreRows];
scoreCopy[0].score = 2;
scoreRows[0].score; // 2：副本中的对象仍与原数组共享
~~~

对象展开与数组展开不是同一协议。数组展开消费迭代器；`Object.assign` 和对象展开读取自有可枚举属性。两者都只是浅复制，且对 `getter`、`setter` 的影响不同；见[JavaScript 值如何转换、比较，并成为属性键？](#28.%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%EF%BC%8C%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F)。

`concat` 返回浅层新数组，还会检查 `Symbol.isConcatSpreadable`，所以数组展开与 `concat` 不总是等价：展开要求输入可迭代；`concat` 则可展开带有长度和索引的类数组对象。

~~~javascript
const concatOnly = {
  0: "x",
  length: 1,
  [Symbol.isConcatSpreadable]: true,
};
[1].concat(concatOnly); // [1, "x"]
// [...concatOnly]; // TypeError：该对象没有迭代器
~~~

### 数组排序如何比较并处理原数组

`sort` 原地排序，默认按字符串形式比较；排序规范要求稳定，因此比较结果相等的元素仍保持原有相对顺序。ES2019 将稳定性要求纳入标准。`toSorted` 使用同类排序规则但返回副本；如要按数字升序，需传入比较函数。

~~~javascript
[1, 11, 2].sort(); // [1, 11, 2]：默认按字符串比较
[1, 11, 2].toSorted((left, right) => left - right); // [1, 2, 11]：原数组不变
~~~

### flat、递归与逐层 concat 的空位结果

`flat(depth)` 返回展平副本，默认只展平一层；`flat(Infinity)` 不设置展平层数上限，也不检测循环，应当用于无环的嵌套数组；极深嵌套仍可能超出引擎调用栈或资源限制。它会跳过被访问层级中原型链上也不存在的索引，不会递归展平 `Set` 之类的非数组可迭代对象。

~~~javascript
const sparseNested = [, [, 1]];
[].concat(...sparseNested); // [undefined, <1 empty item>, 1]
sparseNested.flat(Infinity); // [1]
~~~

旧式逐层 concat 的差别来自两步：外层展开消费迭代器，把没有继承值的外层空位变成 `undefined`；concat 随后浅复制嵌套数组时仍可保留其中空位。它还可能反复复制宽数组，或超过引擎的实参数量限制。

递归循环可清楚展示层级规则，但极深输入可能耗尽调用栈；这里按每个数值索引读取，因此没有继承同索引值时，空位变成 `undefined`，与 `flat` 不同。

~~~javascript
function flattenNested(items) {
  const result = [];
  function append(list) {
    for (let index = 0; index < list.length; index += 1) {
      const value = list[index];
      if (Array.isArray(value)) append(value);
      else result.push(value);
    }
  }
  append(items);
  return result;
}

flattenNested([1, [2, [3]], 4]); // [1, 2, 3, 4]
[1, [2, [3]], 4].flat(Infinity); // [1, 2, 3, 4]
~~~

迭代式 `[].concat(...items)` 每轮展平一层，可能命中参数数量限制、重复复制大数组，且空位行为与 `flat` 不同。如果输入没有嵌套数组，它会直接返回原输入，而非副本。循环只适用于无环、普通且嵌套数组可由 `concat` 默认展开的输入；若某个嵌套数组设置 `Symbol.isConcatSpreadable = false`，`some(Array.isArray)` 仍看到它，`concat` 却不展开它，循环将无法收敛。

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

需要复杂嵌套展平时，先确认期望的层数、空位语义和是否要保留输入身份；这些都是接口行为，不只是性能选择。

### 大数组求最大值时避免展开成大量实参

`Math.max(...values)` 和 `Math.max.apply(null, values)` 都会把每个值变成一个函数实参。很大的输入可能超过引擎允许的参数数量，具体阈值由实现决定。循环每次只传固定数量参数，也能明示空数组和非法数值的策略。

~~~javascript
function maxOfNumbers(values) {
  let max = -Infinity;
  for (const value of values) {
    max = Math.max(max, value);
  }
  return max;
}

maxOfNumbers([]); // -Infinity
maxOfNumbers([7, NaN]); // NaN
maxOfNumbers([, 7]); // NaN：数组迭代器把空位读成 undefined
~~~

如果业务把空位视为不存在，应使用会跳过空位的遍历并明确空输入结果；Number 无效值如何处理也应由调用方决定。

> [!info]- 来源
> - 数组方法对缺失索引的读取、HasProperty、回调参数、concat、flat、展开复制与排序：[ECMAScript 2026 §23.1.3 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)。
> - `concat` 与 `Symbol.isConcatSpreadable` 的展开规则：[ECMAScript 2026 §23.1.3.2 Array.prototype.concat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.concat)；稳定排序：[ECMAScript 2026 §23.1.3.30 Array.prototype.sort](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `for...in` 与 `for...of` 的枚举和迭代规则：[ECMAScript 2026 §14.7.5](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)；数组迭代器的索引读取：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - `Object.hasOwn` 只检查对象自有属性，不查原型链：[ECMAScript 2026 §20.1.2.14](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)，访问于 2026-11-12。
> - Set 去重、SameValueZero 与平均访问时间：[ECMAScript 2026 §24.1–24.2 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；[§7.2.10 SameValueZero](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Math.max 和实参处理：[ECMAScript 2026 §21.3.2.25](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
## 31. 如何安全地深拷贝 JavaScript 值？

报表要保存一份可独立编辑的快照时，浅复制只会新建外层数组或对象，嵌套 `owner` 仍可能与当前界面共享。所谓“深拷贝”没有脱离数据模型的通用实现：先确认输入类型、循环引用、共享子对象、原型行为和所有权边界，再选择 `JSON`、`structuredClone`（结构化克隆）或范围受限的手写复制器。

复制建立新的对象图；它不回答两个值是否满足同一结构契约。若只需判断受限纯数据是否结构相等，见[JavaScript 如何按约定比较对象与数组？](#%E7%BB%93%E6%9E%84%E6%AF%94%E8%BE%83%E8%A6%81%E6%8A%8A%E8%BE%93%E5%85%A5%E8%8C%83%E5%9B%B4%E5%86%99%E6%88%90%E5%A5%91%E7%BA%A6)。

### JSON 往返只适合 JSON 形状的数据

`JSON.parse(JSON.stringify(value))` 不是通用拷贝：

- `Date` 会变成字符串，`Map` 和 `Set` 通常变成空对象。
- 对象中值为 `undefined`、函数或 `Symbol` 的字符串键属性会被省略；`Symbol` 键属性也不参与 JSON 序列化。数组空位及这些不支持的值会变成 `null`。
- BigInt 和循环引用会使序列化抛错。
- 不会保留对象身份或原型、属性描述符等结构。

~~~javascript
JSON.stringify([, undefined, NaN]); // "[null,null,null]"
~~~

如果数据契约本来就是 JSON 值，序列化可能足够；否则应选能表达实际对象图的复制策略。

### structuredClone 复制对象图并保留图内关系

structured clone（结构化克隆）算法由 `structuredClone(value)` 调用，返回新对象图。它支持多种标准内建类型，也能处理循环引用和多处指向同一个子对象的关系。复制后的节点与输入节点身份不同，但克隆结果内部原先共享的引用仍共享。

这里特意换成两条本来就共享同一个 `owner` 的记录，用来观察克隆保留图内共享关系；这与前章字段相似但身份不同的 `first` / `retry` 是不同输入。

~~~javascript
const sharedOwner = { id: "u-17", name: "Ada" };
const report = {
  rows: [
    { reportId: "r-104", amount: 0, owner: sharedOwner },
    { reportId: "r-105", amount: 120, owner: sharedOwner },
  ],
  focusedOwner: sharedOwner,
};
report.self = report;

const snapshot = structuredClone(report);
snapshot !== report; // true
snapshot.self === snapshot; // true：循环关系保留
snapshot.rows[0].owner === snapshot.rows[1].owner; // true：共享子对象关系保留
snapshot.focusedOwner === snapshot.rows[0].owner; // true
snapshot.rows[0].owner !== sharedOwner; // true：与原对象图分离
~~~

标准没有承诺所有对象都可克隆，也不保留任意类行为。函数、`WeakMap`（弱映射）、`Symbol` 值和普通 DOM `Node` 没有相应的序列化步骤，会抛 `DataCloneError`；普通类实例则按普通对象数据克隆，原型和方法不会随对象图复制。若属性值依赖 `getter`，序列化会读取值，访问器本身不会作为访问器复制。其他平台对象也要检查该类型是否定义了序列化步骤。

~~~javascript
class ReportRow {
  constructor() {
    this.reportId = "r-104";
  }
  label() {
    return this.reportId;
  }
}

const classCopy = structuredClone(new ReportRow());
Object.getPrototypeOf(classCopy) === Object.prototype; // true
classCopy.label; // undefined：实例方法没有复制

function cloneErrorName(value) {
  try {
    structuredClone(value);
    return "cloned";
  } catch (error) {
    return error.name;
  }
}

cloneErrorName(() => {}); // "DataCloneError"
cloneErrorName(new WeakMap()); // "DataCloneError"
cloneErrorName(Symbol("value")); // "DataCloneError"
~~~

`structuredClone` 的 `transfer`（转移）选项会转移可转移对象的底层资源，而不是复制一份；被转移的原输入将不再可用。`ArrayBuffer` 是常见示例：

~~~javascript
const buffer = new ArrayBuffer(8);
const transferred = structuredClone({ buffer }, { transfer: [buffer] });

transferred.buffer.byteLength; // 8
buffer.byteLength; // 0：原 buffer 已分离
~~~

只有所有权确实要交给另一端时才转移；否则普通 `structuredClone` 会保留输入并创建复制品。

新建包装对象不总表示底层数据独立。环境允许 `SharedArrayBuffer`（共享数组缓冲区）时，结构化克隆会产生新包装对象，但它们仍指向同一块共享字节；要获得独立快照，应显式复制数据。

~~~javascript
const sharedBuffer = new SharedArrayBuffer(1);
const sharedCopy = structuredClone(sharedBuffer);
const sourceByte = new Uint8Array(sharedBuffer);
const copiedByte = new Uint8Array(sharedCopy);

sharedCopy !== sharedBuffer; // true：包装对象不同
sourceByte[0] = 42;
copiedByte[0]; // 42：底层字节仍共享
~~~

### 何时 JSON 与 structuredClone 都不符合契约

若应用类型有限且需要定制属性语义，可实现范围受限的复制器。下面的实现支持同 `realm`（执行环境）的基础 `Date`、`RegExp`、`Map`、`Set`、数组，以及原型为当前 realm `Object.prototype` 或 `null` 的普通对象；它只递归自有、可枚举的字符串键。数组上的自有可枚举字符串扩展属性也会复制；`Date`、`RegExp`、`Map`、`Set` 上的扩展属性会被忽略。不要输入这些内建类型的自定义子类：`instanceof` 分支会将其降为对应基础类型，丢失子类原型和方法。`RegExp.lastIndex` 在此实现中按原值赋给副本，因此输入契约限定它为普通数字位置，不能带一个需独立复制的对象值。

`seen` 用 `WeakMap`（弱映射）在递归子项之前记录当前对象与副本的映射：再次遇到同一节点时直接返回已登记的副本，因此能保留循环回指和图内共享身份。输入契约还需说明其他边界：函数和 `Symbol` 值原样返回，不会隔离；`Symbol` 键和非枚举属性被忽略；访问器属性会通过读取 `value[key]` 执行 getter，结果被写成普通数据属性，原描述符不会保留。

> [!example]- 一个有限范围的递归复制器实现
>
> ~~~javascript
> function deepCopy(value, seen = new WeakMap()) {
>   if (value === null || typeof value !== "object") return value;
>   if (seen.has(value)) return seen.get(value);
>
>   let copy;
>   if (value instanceof Date) {
>     copy = new Date(value.getTime());
>   } else if (value instanceof RegExp) {
>     copy = new RegExp(value.source, value.flags);
>     copy.lastIndex = value.lastIndex;
>   } else if (value instanceof Map) {
>     copy = new Map();
>     seen.set(value, copy);
>     for (const [key, item] of value) {
>       copy.set(deepCopy(key, seen), deepCopy(item, seen));
>     }
>     return copy;
>   } else if (value instanceof Set) {
>     copy = new Set();
>     seen.set(value, copy);
>     for (const item of value) copy.add(deepCopy(item, seen));
>     return copy;
>   } else if (Array.isArray(value)) {
>     copy = new Array(value.length);
>   } else {
>     const prototype = Object.getPrototypeOf(value);
>     if (prototype !== Object.prototype && prototype !== null) {
>       throw new TypeError("Unsupported object type");
>     }
>     copy = Object.create(prototype);
>   }
>
>   seen.set(value, copy);
>   if (value instanceof Date || value instanceof RegExp) return copy;
>
>   for (const key of Object.keys(value)) {
>     Object.defineProperty(copy, key, {
>       value: deepCopy(value[key], seen),
>       enumerable: true,
>       writable: true,
>       configurable: true,
>     });
>   }
>   return copy;
> }
> ~~~

~~~javascript
const trailingHoles = deepCopy([1, , ,]);
trailingHoles.length === 3; // true
0 in trailingHoles; // true
1 in trailingHoles; // false
2 in trailingHoles; // false

const emptySparse = deepCopy(new Array(3));
emptySparse.length === 3; // true
Object.keys(emptySparse); // []

const extendedArray = Object.assign([, 1], { note: "extra" });
deepCopy(extendedArray).note; // "extra"
~~~

这个实现不是通用库的替代品。只要输入可能带 getter、副作用、跨 realm 内建值、特殊宿主对象或未知原型，就应缩小输入契约或采用已定义这些类型行为的标准机制，而不是静默地产生错误的“副本”。

> [!info]- 来源
> - `structuredClone` 的深拷贝、可转移对象及转移后原值不可用：[WHATWG HTML Living Standard §2.7.11 Structured cloning API](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning-api)，更新时间 2026-11-05。
> - 可序列化平台对象的约束、循环和重复引用：[WHATWG HTML Living Standard §2.7.1](https://html.spec.whatwg.org/multipage/structured-data.html#serializable-objects) 与 [§2.7.4 StructuredSerializeInternal](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializeinternal)；DOM `Node` 的接口定义：[DOM Standard §4.4](https://dom.spec.whatwg.org/#interface-node)。
> - 对象属性读取（包括 getter 执行）及反序列化：[WHATWG HTML Living Standard §2.7.4](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializeinternal) 与 [§2.7.7 StructuredDeserialize](https://html.spec.whatwg.org/multipage/structured-data.html#structureddeserialize)。
> - `Date.prototype.getTime()` 的时间值读取：[ECMAScript 2026 §21.4.4.23](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-date.prototype.gettime)。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
## 32. JavaScript 作用域与闭包如何保留状态？

**案例背景。** 网页用 `attachLogger` 为按钮注册点击日志；注册函数返回后，用户再点击按钮，callback（回调）为什么仍能读到当时传入的 `label`？scope（作用域）决定一个名称在哪里可见，closure（闭包）让函数以后仍能访问它定义处的绑定。本章沿名称查找、声明初始化和几个延后执行的回调追踪这条路径。ordinary function（普通函数）的 `this` 由调用形式提供；arrow function（箭头函数）没有自己的 `this` 绑定，而是从定义处的外层环境读取。本章的接收者规则只针对普通函数；更多形式见[JavaScript 函数的 `this` 值由什么决定？](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F)。

以下代码块彼此独立。标为 HTML 的代码需要浏览器；计时器例子使用浏览器或 Node.js 提供的计时 API。

### 名称查找沿函数的定义位置进行

当代码读取标识符时，JavaScript 从当前 lexical environment（词法环境）查找对应的 binding（绑定）；当前环境没有该名称才沿外层环境继续。每次调用 `outer` 时，函数体开始执行前的声明实例化会建立 `inner` 的绑定并创建函数对象；它的 `[[Environment]]` 指向这次 `outer` 调用的词法环境。接着函数体才执行，初始化 `label` 并返回这个函数。即使本次 `outer` 调用结束，返回的函数仍能让那份环境可达。`callFromElsewhere` 调用返回值时，才建立 `inner` 本次调用的局部环境。调用者的局部环境不会插入函数定义时建立的查找链；普通函数调用者能提供实参和接收者 `this`，箭头函数则从词法外层读取 `this`。

下面的图只展示 `outer` 已返回、`inner` 又被调用之后的名称查找。`inner` 的局部环境里有 `detail`，没有 `label`；因此查找沿函数对象保留的那次 `outer` 环境继续，而不是沿调用者 `callFromElsewhere` 的局部环境继续。

~~~mermaid
flowchart TB
  Q["inner 读取 label"] -->|先查当前环境| I["inner 的词法环境<br/>有 detail；没有 label"]
  I -->|未找到 label，沿定义时的外层环境查找| O["outer 本次调用的环境<br/>label = outer；命中并停止"]
~~~

~~~javascript
const label = "global";

function outer() {
  const read = inner;
  const label = "outer";
  function inner() {
    const detail = "inner";
    return [label, detail];
  }
  return read;
}

function callFromElsewhere() {
  const label = "caller";
  const read = outer();
  return read();
}

callFromElsewhere(); // ["outer", "inner"]
~~~

这里的环境节点是语言规范描述名称查找的抽象，不表示引擎必须按相同形状分配 JavaScript 对象。execution context（执行上下文）描述当前正在执行的脚本或函数及其状态；environment record（环境记录）描述绑定与名称查找操作。调用栈告诉我们哪些调用尚未返回，词法链告诉我们一个名称按什么顺序解析；两者相关，但不是同一条链。

### 声明方式决定绑定范围与初始化时机

`var`、`let`、`const` 的差异不只是“函数级或块级”：声明先在哪个环境建立绑定、什么时候初始化，也会决定读取结果。

| 声明 | 绑定范围 | 初始化时机 | 重复声明与重新赋值 |
| --- | --- | --- | --- |
| `var` | 普通函数作用域；脚本或模块的顶层也有各自范围 | 本节没有同名形参的例子里，声明实例化把新变量绑定初始化为 `undefined`；声明中的初始化式到代码执行至声明处才运行 | 兼容的 `var` 声明可重复；可重新赋值 |
| `let` | 所在词法作用域，如代码块或脚本、模块顶层 | 进入作用域先建立未初始化绑定；从进入作用域到声明初始化完成是 temporal dead zone（暂时性死区）；无初始化式时到声明处初始化为 `undefined` | 同一词法作用域不能重复声明；可重新赋值 |
| `const` | 所在词法作用域，如代码块或脚本、模块顶层 | 与 `let` 一样先建立未初始化绑定；从进入作用域到声明初始化完成是暂时性死区；通常必须写初始化式，`for...in` / `for...of` 头部例外 | 同一词法作用域不能重复声明；初始化后不能重新绑定 |

`if` 代码块不会为 `var` 创建新绑定，因此即使声明写在条件块里，函数开头读取的也是已初始化为 `undefined` 的同一个 `status`。`let` 和 `const` 进入代码块时已经有绑定，但初始化前读取会抛出 `ReferenceError`。下例的内层 `let count` 已经遮蔽外层 `count`；查找遇到这个尚未初始化的内层绑定就抛错，不会跳过它再去读外层的 `0`。离开代码块后，外层 `count` 仍为 `0`。`const` 限制变量名重新绑定，不会冻结它指向的对象。
`for...in` 和 `for...of` 头部的 `const` 由每轮枚举或迭代取出的值初始化；普通 `const` 声明则必须显式写初始化式。

~~~javascript
function readBeforeAssignment() {
  console.log(status); // undefined
  if (true) {
    var status = "ready";
  }
  return status; // "ready"
}

let count = 0;
let tdzError;
{
  try {
    count;
  } catch (error) {
    tdzError = error.name;
  }
  let count = 1;
}

const options = { theme: "light" };
options.theme = "dark";
let reassignmentError;
try {
  options = {};
} catch (error) {
  reassignmentError = error.name;
}
const statusAfterReturn = readBeforeAssignment();
[statusAfterReturn, tdzError, count, options.theme, reassignmentError];
// ["ready", "ReferenceError", 0, "dark", "TypeError"]
~~~

兼容的 `var` 名称可以在同一变量作用域重复声明，但不能与同一作用域内冲突的词法声明混用；重复声明同名 `let` 或 `const` 是语法错误。绑定不需要重新赋值时通常用 `const`，需要重新赋值时用 `let`；维护依赖函数作用域的旧代码时才需要 `var`。

#### “顶层”取决于宿主怎样执行代码

浏览器经典脚本、浏览器模块、Node.js CommonJS 和 Node.js ESM 都能声明顶层变量，但它们处在不同的外层环境中。top-level `this`（顶层 `this`）也不总是全局对象；`globalThis` 才是跨这些调用位置访问当前 Realm（执行域）全局 `this` 值的标准入口。

| 运行方式 | 顶层声明 | 顶层 `this` | 宿主全局入口 |
| --- | --- | --- | --- |
| 浏览器 classic script（经典脚本，`<script>` 不写 `type="module"`） | `var` 通常成为 `window` 属性；`let` / `const` 是 global lexical binding（全局词法绑定） | 当前全局 `this` 值，即 `window` | `window`、`globalThis` |
| 浏览器 module script（模块脚本） | `var`、`let`、`const` 都是 module-local binding（模块局部绑定） | `undefined` | `globalThis`；窗口页面另有 `window` |
| Node.js CommonJS（Node.js 模块格式，简称 CJS） | `var`、`let`、`const` 都是 wrapper-local binding（包装函数内的局部绑定） | 包装函数收到的初始 `exports` 对象 | `globalThis` |
| Node.js ECMAScript module（ES 模块，简称 ESM） | `var`、`let`、`const` 都是 module-local binding | `undefined` | `globalThis` |

浏览器主线程的 `window` 代表窗口全局；Web Worker（Web 工作线程）有自己的全局环境，可用 `self` 或 `globalThis`，没有 `window`。模块规则与 Node.js 包格式及互操作的更多差异见[ECMAScript 模块与 CommonJS 在语法、加载和运行时有什么不同？](#49.%20ECMAScript%20%E6%A8%A1%E5%9D%97%E4%B8%8E%20CommonJS%EF%BC%88Node.js%20%E6%A8%A1%E5%9D%97%E6%A0%BC%E5%BC%8F%EF%BC%89%E5%9C%A8%E8%AF%AD%E6%B3%95%E3%80%81%E5%8A%A0%E8%BD%BD%E5%92%8C%E8%BF%90%E8%A1%8C%E6%97%B6%E6%9C%89%E4%BB%80%E4%B9%88%E4%B8%8D%E5%90%8C%EF%BC%9F)。

~~~html
<script>
  var scriptValue = "global object property";
  let scriptBinding = "global lexical binding";

  const browserScriptResults = [
    window.scriptValue,
    window.scriptBinding,
    scriptBinding,
    this === globalThis,
  ];
  // ["global object property", undefined, "global lexical binding", true]
</script>
~~~

### 闭包保留绑定，而不是冻结快照

closure（闭包）使函数代码以后仍能访问它定义处可见的绑定。每次调用 `makeCounter(start)` 都会建立参数 `start` 和独立的局部 `value` 绑定。执行到 `let value = start` 时，用 `start` 的值初始化 `value`。返回的函数保留对这份 `value` 的访问。`value++` 先读取旧值，再把加一后的值写回原绑定，然后以旧值作为表达式结果交给调用者。因此第一次调用将 `value` 从 `10` 写成 `11` 并返回 `10`；第二次读取同一绑定时从 `11` 开始。它不是创建时复制下来的快照。

~~~javascript
function makeCounter(start) {
  let value = start;
  return () => value++;
}

const first = makeCounter(10);
const second = makeCounter(-2);
const firstResults = [first(), first(), first()];
const secondResults = [second(), second(), second()];
[firstResults, secondResults];
// [[10, 11, 12], [-2, -1, 0]]
~~~

同一次调用也可以返回多个共享状态的函数。`increment`、`decrement` 和 `reset` 都访问同一份 `current`；`reset` 把该绑定改回输入的初值，不会创建一个新的计数器。

~~~javascript
function createCounter(init) {
  let current = init;
  return {
    increment() { return ++current; },
    decrement() { return --current; },
    reset() { return current = init; },
  };
}

const counter = createCounter(5);
[counter.increment(), counter.reset(), counter.decrement()]; // [6, 5, 4]
~~~

### 报表处理器把闭包状态与调用时接收者结合起来

报表服务创建处理器时，工厂函数把 `tag` 和 `calls` 两个词法绑定交给返回的普通函数继续访问。每次方法调用都更新同一份 `calls`；闭包不会顺带捕获普通函数的 `this`。先看 `service.onReport(...)`：成员调用以 `service` 为接收者，所以 `onReport` 里的 `this` 是 `service`。函数体又执行 `this.format(...)` 这个成员调用，于是 `format` 里的 `this` 仍是 `service`。

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

const service = {
  prefix: "Sales",
  format(report, tag, sequence) {
    return `${this.prefix}/${tag}: ${report.title} #${sequence}`;
  },
  onReport: makeReportHandler("daily"),
};

const firstReport = service.onReport({ title: "Q4" });
const secondReport = service.onReport({ title: "Q4" });
const { onReport } = service;
let bareCallError;
try {
  onReport({ title: "Q4" });
} catch (error) {
  bareCallError = error.name;
}
const reportAfterBareCall = service.onReport({ title: "Q4" });
[firstReport, secondReport, bareCallError, reportAfterBareCall];
// [
//   "Sales/daily: Q4 #1",
//   "Sales/daily: Q4 #2",
//   "TypeError",
//   "Sales/daily: Q4 #4",
// ]
~~~

裸调时，`onReport` 的严格模式使 `this` 为 `undefined`。函数先执行 `calls += 1`，再读 `this.format` 才抛出 `TypeError`；因此下一次正常服务调用是 `#4`。`tag`、`calls` 来自函数定义时的词法环境；普通函数的 `this` 则由每次调用形式分别提供。箭头函数没有自己的 `this`；若此处把处理器改写成箭头，它会读定义它的外层 `this`，不再随 `service.onReport(...)` 改变。

### 循环回调需要符合预期数量的绑定

循环把回调保存起来、稍后才调用时，关键是每个回调最后读取的是同一份绑定，还是每轮各自的绑定。`var` 在循环里重复赋值同一份函数作用域绑定；顶层示例里的 `var` 归脚本/模块环境，放进普通函数时则归函数环境。带 `let` 的 `for` 循环会为每轮提供新的绑定：第一轮体读取 `j = 0`，回调记住这份绑定；循环体结束后，语言先把当前值复制到下一轮的新绑定，再在新绑定上执行 `j++`。因此下一轮体是 `1`，第一份回调仍读旧的 `0`。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

[fromVar.map(fn => fn()), fromLet.map(fn => fn())];
// [[3, 3, 3], [0, 1, 2]]
~~~

旧代码也能用 Immediately Invoked Function Expression（IIFE，立即调用函数表达式）为每轮新建一个函数调用参数绑定。回调读取各自的 `capturedIndex`，所以得到和 `let` 循环相同的结果。

~~~javascript
const callbacks = [];
for (var index = 0; index < 3; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}
callbacks.map(fn => fn()); // [0, 1, 2]
~~~

### 工厂函数专门化行为，回调保留捕获值

工厂可以把一次调用建立的参数绑定保存在闭包里，返回一个更专用的函数。本例的 `x` 绑定在工厂返回后仍可读，且后续不再赋值；这正是“捕获值”恰好保持不变的条件。同一机制也让延后执行的 callback（回调）读取注册时的参数绑定。

~~~javascript
function add(x) {
  return function (y) {
    return x + y;
  };
}

const addFive = add(5);
addFive(3); // 8
~~~

下面两段 DOM 代码都要在浏览器页面的 `<body>` 已经存在后运行。注册监听器后，`attachLogger` 已经返回；真实用户可以之后点击按钮。这里用 `dispatchEvent` 在注册函数返回后同步派发事件，监听器会在 `dispatchEvent` 返回前运行。箭头回调读取 `attachLogger` 那次调用创建的 `label` 参数绑定；该绑定之后不再赋值。

~~~javascript
function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener("click", () => {
    console.log("Clicked: " + label);
  });
}

const loggerButton = document.createElement("button");
loggerButton.id = "btn1";
document.body.append(loggerButton);
attachLogger("btn1", "primary");
loggerButton.dispatchEvent(new MouseEvent("click"));
// 控制台输出："Clicked: primary"
~~~

animation frame（动画帧）回调也会延后运行。`animate` 每次调用都会建立 `start`、`element`、`from`、`to` 和 `duration` 绑定；这些参数和 `start` 随后不再赋值。`performance.now()` 返回毫秒时间戳，因此 `duration` 也以毫秒计。后续每一帧的 `update` 都从同一次 `animate` 调用读取它们，算出当前位置，再决定是否请求下一帧。代码也必须等页面 `<body>` 已经存在后运行。

~~~javascript
function animate(element, from, to, duration) {
  const start = performance.now();

  function update() {
    const elapsed = performance.now() - start;
    const progress = Math.min(elapsed / duration, 1);
    const value = from + (to - from) * progress;
    element.style.left = value + "px";

    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

const animatedElement = document.createElement("div");
animatedElement.textContent = "报表已更新";
animatedElement.style.position = "relative";
document.body.append(animatedElement);
animate(animatedElement, 0, 100, 1000); // duration 必须大于 0
~~~

当进度到达 `1` 时，`style.left` 最终为 `100px`，并且不再请求下一帧。`left` 对普通静态定位元素不起偏移作用；本例设置 `position: relative`，只移动绘制位置，不移除元素在正常流中占据的空间。

### 定时回调怎样用闭包保留调度状态

debounce（防抖）在一段静默时间后运行最后一次调用；throttle（节流）则限制调用频率。两者都让返回函数通过闭包保存跨调用状态，但保存内容和更新时机不同。库和自定义包装函数可以选择 leading-edge（首沿）、trailing-edge（尾沿）或两者兼有；下面的实现分别是 trailing-only debounce（仅尾沿防抖）和 leading-only throttle（仅首沿节流）。示例把 `wait` 和 `interval` 设为正整数毫秒数；时间表采用理想时钟推演，不代表任一宿主的实际触发测量或保证。节流的推论只针对正间隔。

~~~javascript
function debounce(fn, wait) {
  let timer;

  function debounced(...args) {
    const receiver = this;
    clearTimeout(timer);
    timer = setTimeout(() => {
      timer = undefined;
      fn.apply(receiver, args);
    }, wait);
  }

  debounced.cancel = function () {
    clearTimeout(timer);
    timer = undefined;
  };

  return debounced;
}

function throttleLeading(fn, interval) {
  let lastCallAt = null;

  return function (...args) {
    const now = performance.now();
    if (lastCallAt !== null && now - lastCallAt < interval) return;

    lastCallAt = now;
    return fn.apply(this, args);
  };
}
~~~

`timer` 来自某一次 `debounce(fn, wait)` 调用，并由返回的 `debounced` 闭包跨调用共享。每次进入 `debounced(...args)` 时都会新建这一轮的 `args` 绑定与 `receiver` 绑定；旧计时器被清除后，新计时器的箭头回调访问的就是这次调用的接收者和参数。因而静默期结束时只执行最后一组输入。`.cancel()` 只撤销尚未触发的 timer。`throttleLeading` 用 `performance.now()` 的单调时钟计算间隔，系统校时不会改变这段差值；用 `null` 表示“尚无上次调用时间”，因此即使计时器初始读数为 `0`，第一次调用也会立即通过；到达间隔边界时，差值等于 `interval`，本次也会通过。

下面是理想时钟的合成时间线：等待值与节流间隔都设为 `100ms`，`pageA`、`pageB`、`pageC` 表示不同接收者，包装目标把接收者页面名和搜索词记下来。每一行同时把相同输入交给两个包装函数；这些时刻是便于推演的逻辑时间，不是宿主时钟的测量结果。

| 理想时刻 | 防抖包装函数收到的输入与状态 | 首沿节流包装函数收到的输入与结果 |
| ---: | --- | --- |
| `0ms` | `debouncedSearch.call(pageA, "A")`：设置 `100ms` 等待 | `throttledSearch.call(pageA, "A")`：立即以 `pageA` 和 `"A"` 执行，记录上次通过时刻 `0` |
| `40ms` | `debouncedSearch.call(pageB, "B")`：取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageB, "B")`：丢弃，距离上次通过 `40ms` |
| `110ms` | `debouncedSearch.call(pageC, "C")`：再次取消旧 timer，重新等待 `100ms` | `throttledSearch.call(pageC, "C")`：执行，距上次通过 `110ms`，超过间隔 |
| 自 `210ms` 起 | 若无新调用，timer 以 `pageC` 和 `"C"` 执行 | 没有新调用 |

`setTimeout` 接收 delay（延迟）并由宿主安排计时器任务；它不保证回调会在指定的精确时刻触发。隔离复现中，Node.js 26.13.0 的高分辨率时间实测有时观察到略短于传入值的等待，因此上表采用理想时钟，不把时间点当作实际保证。Node.js 26.13 将小于 `1ms` 或大于 `2147483647ms` 的 delay 改为 `1ms`，并截去非整数小数部分；这是 Node 的边界，不可套用为所有宿主的规则。控件销毁时应移除事件监听器并调用 `.cancel()`；它只移除尚未触发的防抖 callback。如果 callback 已经启动 `fetch`，还可以调用该请求 AbortController（中止控制器）的 `abort()`，这会取消客户端操作，但不会撤回服务端已经收到并开始处理的工作。

节流实现先写入 `lastCallAt` 再调用目标函数，所以目标同步重入时会看到这次调用的时间：若重入时仍未经过间隔，会被挡下；若目标同步耗时已达到或超过间隔才重入，重入会通过。`interval` 为 `0` 时该判断不会限制同步重入；本节的节流结论限于正间隔。

### 闭包生命周期取决于可达性

外层调用返回后，返回函数仍可观察它使用的绑定，这是行为保证；这不表示引擎必须把所有局部变量永久装进一个环境对象。长期存在的事件监听器可以让闭包与数据继续可达，控件销毁时应移除监听器和其他引用。循环引用本身不等于内存泄漏；需要判断的是活动程序仍能否沿引用到达这些数据。

**相关机制：** [JavaScript 对象如何查找属性并组织成员？](#33.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%B1%9E%E6%80%A7%E5%B9%B6%E7%BB%84%E7%BB%87%E6%88%90%E5%91%98%EF%BC%9F) 将同一报表处理器放入服务实例，并说明 `format` 如何从原型查找；[JavaScript 函数的 `this` 值由什么决定？](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F) 解释调用形式怎样提供接收者。

> [!info]- 来源
> - 词法环境、环境记录和标识符查找：[ECMAScript 2026 Execution Contexts](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-execution-contexts)、[Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)、[GetIdentifierReference](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getidentifierreference)、[NewFunctionEnvironment](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-newfunctionenvironment)。
> - `var`、`let`、`const` 的绑定建立、初始化和声明限制：[ECMAScript 2026 FunctionDeclarationInstantiation](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-functiondeclarationinstantiation)、[Source Text Module Record InitializeEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html#sec-source-text-module-record-initialize-environment)、[Let and Const Declarations](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-let-and-const-declarations)、[Variable Statement](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-variable-statement)。
> - 函数对象保留定义处环境，以及普通函数调用与箭头函数 `this` 的区别：[ECMAScript 2026 Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)、[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)、[EvaluateCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatecall)、[OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)。
> - `for (let...)` 的每轮绑定复制与更新顺序：[ECMAScript 2026 ForBodyEvaluation](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-forbodyevaluation)、[CreatePerIterationEnvironment](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-createperiterationenvironment)。
> - 浏览器经典脚本、模块脚本、DOM 点击与 Web Worker 全局环境：[WHATWG HTML The `script` element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)、[Document.body](https://html.spec.whatwg.org/multipage/dom.html#dom-document-body)、[dispatchEvent](https://dom.spec.whatwg.org/#dom-eventtarget-dispatchevent)、[The global scope](https://html.spec.whatwg.org/multipage/workers.html#the-global-scope)（Living Standard，核对日期 2026-11-12）；Node.js [CommonJS module wrapper](https://nodejs.org/api/modules.html#the-module-wrapper) 与 [ECMAScript modules](https://nodejs.org/api/esm.html)（官方文档 26.13.1，实际回放 Node.js 26.13.0）。
> - 动画帧、计时器时限和延迟任务：[WHATWG HTML `requestAnimationFrame`](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#dom-animationframeprovider-requestanimationframe)、[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)（Living Standard，核对日期 2026-11-12）、[Node.js Timers: `setTimeout`](https://nodejs.org/api/timers.html#settimeoutcallback-delay-args)（官方文档 26.13.1）；单调时间戳：[W3C High Resolution Time `performance.now()`](https://www.w3.org/TR/hr-time-3/#dom-performance-now)（Level 3，核对日期 2026-11-12）；`position: relative` 的偏移语义：[CSS Positioned Layout Level 3](https://drafts.csswg.org/css-position-3/#valdef-position-relative)（Editor’s Draft，2026-05-14）。
> - 监听器注册与请求取消边界：[WHATWG DOM `addEventListener`](https://dom.spec.whatwg.org/#dom-eventtarget-addeventlistener)、[Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)、[Fetch Standard Aborting a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，核对日期 2026-11-12。
## 33. JavaScript 对象如何查找属性并组织成员？

**案例背景。** 一个报表页面创建多个服务实例：每个实例有自己的区域前缀和调用次数，但共享格式化方法。读取 `service.prefix` 可以在实例自身找到值，读取 `service.format` 却要去它的原型上找。下面沿这次属性查找，解释成员放在哪里、getter/setter 怎样参与读写，以及为什么改一个共享方法会影响多个实例。

property key（属性键）可以是字符串或 `Symbol`（符号）。点号语法 `object.key` 使用字符串键 `"key"`；方括号语法 `object[symbolKey]` 可以用 Symbol 值，之后的查找和赋值规则相同。

instance（实例）状态与共享 method（方法）分别存在哪里，取决于对象之间的关系。这里先分开两个名字相近的概念：对象的 `[[Prototype]]` 内部链接负责查找，组成 prototype chain（原型链）；对本页普通 constructor function（构造函数）的直接 `new C()`，构造函数上的 `prototype` 属性提供新建接收者的初始原型，前提是它的值为对象。若值不是对象，构造过程会按函数所在 Realm（执行域）回退到对应的内建原型。下文的报表服务实例 `service` 从 `ReportService.prototype` 共享 `format`；图分别展示读取 `service.format`、函数对象自身的继承链，以及 `new` 的原型传递。

![实例的属性查找链与构造函数自身的继承链](../../frontend/javascript/resources/objects-functions-and-prototypes-prototype-links.svg)

图中第一行输入的是属性键 `format`：从 `service` 沿 `[[Prototype]]` 找到共享函数并返回；若某个键一路未找到，到达 `null` 后结果才是 `undefined`。第二行实线表示沿函数对象的 `[[Prototype]]` 链前进；最后的 `null` 是链末端，并非一个对象。第三行虚线只表示 `new` 读取构造函数的 `prototype` 属性值并把该对象用作新实例的 `[[Prototype]]`；若属性值不是对象，则会改用构造函数所在执行域相应的内建原型。

### 属性查找沿原型链进行

ordinary object（普通对象）用 property descriptor（属性描述符）记录属性的值或访问器。读取 `object.key` 时先检查 own property（自有属性）；没有匹配的描述符，就沿 `[[Prototype]]` 链继续查找，直到命中或到达 `null`。命中 data descriptor（数据描述符）时返回 `value`，它也可以是函数。命中 accessor descriptor（访问器描述符）时，若有 getter（读取器），就以原始接收者 `object` 为 `this` 调用它；若没有 getter，读取结果为 `undefined`。沿链始终没有找到属性，也会得到 `undefined`。

getter 的 `this` 不因属性位于原型上而改变，也不是额外的位置实参。继承不是拷贝：实例保留自己的属性，需要共享成员时通过查找取得。setter（设置器）怎样处理赋值，稍后用同一个接收者继续说明。

~~~javascript
const base = { kind: "report" };
const record = Object.create(base);
record.title = "Q4";
const marker = Symbol("reviewed");
record[marker] = true;

Object.hasOwn(record, "title"); // true：title 是 record 的自有属性
Object.hasOwn(record, "kind");  // false：kind 不在 record 自身
"kind" in record;               // true：in 会继续检查原型链
record.kind;                    // "report"
record.missing;                 // undefined：查找到原型链末端仍未找到
Object.hasOwn(record, marker); // true：Symbol 也是有效属性键
Object.getOwnPropertySymbols(record); // [marker]
Object.getPrototypeOf(record) === base; // true
~~~

`Object.hasOwn(object, key)` 只问属性是否定义在这个对象自身；`key in object` 也会报告继承属性。因而当值可能是 `undefined` 时，用属性是否存在来判断不能只看 `object[key]` 的结果。

数据描述符保存 `value`；访问器描述符保存 `get` 与 `set`。本例的 `name` 访问器定义在 `guestProfile` 的原型 `profile` 上；读取或写入这个继承属性时，语言仍以原始接收者 `guestProfile` 为 `this` 调用 getter 或 setter，所以它可以读取或改变实例自己的状态：

~~~javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true,
});

const guestProfile = Object.create(profile);
// 先在 profile 找到 getter；getter 的 this 是 guestProfile。
guestProfile.name; // "John"
// this._name 在 guestProfile 上不存在，于是从 profile 读取 "John"。

// 再在 profile 找到 setter；setter 的 this 仍是 guestProfile。
guestProfile.name = "Jo";
// setter 内的赋值找到 profile 上可写的 _name 数据属性，
// 随后在 guestProfile 上新建 _name，留下 profile._name 不变。
[profile.name, guestProfile.name,
  Object.hasOwn(guestProfile, "name"),
  Object.hasOwn(guestProfile, "_name")];
// ["John", "Jo", false, true]
~~~

getter 是会执行的代码：读取属性可能产生副作用或抛错。访问器对外看起来像属性读取或赋值，但其行为由 getter/setter 决定；只有 getter 而没有 setter 的属性不能通过普通赋值改变。

### 报表服务把实例状态与共享行为分开

案例背景：报表页面为每个服务实例保存不同的区域前缀和处理器，所有实例共享同一个格式化算法。工厂函数用 closure（闭包）分别保存处理器的标签与调用次数。调用 `service.onReport(...)` 先执行实例自己的处理器；处理器再读取 `this.format` 并从原型取得共享函数，最后由这个函数通过 `this.prefix` 读取实例前缀。

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

function ReportService(prefix) {
  this.prefix = prefix;                        // 每个实例各自持有
  this.onReport = makeReportHandler("daily"); // 每个实例各自持有闭包状态
}

ReportService.prototype.format = function (report, tag, sequence) {
  return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
};

const service = new ReportService("Sales");
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #2"
Object.hasOwn(service, "format"); // false
Object.hasOwn(ReportService.prototype, "format"); // true
Object.getPrototypeOf(service) === ReportService.prototype; // true
~~~

`prefix` 和 `onReport` 是构造器运行时写入实例的自有属性，处理器闭包各自保留 `tag` 与 `calls`。每次 `service.onReport(...)` 都先调用该处理器；它读取 `this.format` 时沿 `service.[[Prototype]]` 找到 `ReportService.prototype.format`，再以 `service` 为 `this` 调用这个共享函数。`format` 函数体执行到 `this.prefix` 时，才读取实例自己的 `"Sales"`。构造器、实例、函数调用的关系分别属于原型与 `this` 的机制；[函数的 `this` 值由什么决定？](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F) 继续解释调用形式怎样提供接收者。

### `[[Prototype]]` 与函数的 `prototype` 是两种关系

函数本身也是对象，因此它也有内部 `[[Prototype]]` 链，通常从 `Function.prototype` 继续到 `Object.prototype`。可构造的普通函数通常还有一个自有的数据属性 `prototype`，其值是供实例查找共享成员的对象。对本页这样的普通基础构造函数调用 `new C()` 时，构造过程读取当时的 `C.prototype` 值，初始化新建接收者的 `[[Prototype]]`；实例不是通过函数对象自身的 `[[Prototype]]` 找到成员。构造器若显式返回另一个对象，`new` 的最终结果会改为那个对象，具体返回规则见后面的构造章节。

~~~javascript
function ReportService() {}

// 函数对象自身的原型
Object.getPrototypeOf(ReportService) === Function.prototype; // true
Object.getPrototypeOf(ReportService.prototype) ===
  Object.prototype; // true
Object.hasOwn(ReportService, "prototype"); // true：构造函数上的普通属性

const firstService = new ReportService();
const firstPrototype = ReportService.prototype;
ReportService.prototype = { format() { return "new"; } };
const laterService = new ReportService();

// 已有实例不被迁移
Object.getPrototypeOf(firstService) === firstPrototype; // true
// 新实例采用新值
Object.getPrototypeOf(laterService) === ReportService.prototype; // true
~~~

上例替换的是函数上的 `prototype` 属性。已创建实例仍连着旧原型对象；新实例采用新对象。若只是给当前原型对象添加或修改方法，属性查找能到达该对象的实例会看到变化；若实例有同名自有属性，查找在实例处就停止，共享方法仍被遮蔽。

`prototype` 属性的值只需是对象，不要求它一定是专为该构造函数创建的原型对象；函数本身也是对象，可以成为另一个构造函数实例的原型。反过来，若普通构造函数的 `prototype` 被改成 `null` 或其他原始值，`new` 会回退到该构造函数所属执行域的 `Object.prototype`：

~~~javascript
function Parent() {}
function Child() {}
Child.prototype = Parent; // Parent 是函数对象，因此可以作为原型
Object.getPrototypeOf(new Child()) === Parent; // true

function FallbackDemo() {}
FallbackDemo.prototype = null;
// 同一执行域内，回退结果为 Object.prototype。
Object.getPrototypeOf(new FallbackDemo()) === Object.prototype; // true
~~~

`class`（类）语法也利用这套对象关系，而不是另建一类公开成员存储。公开实例字段初始化为每个新实例创建自有属性；公开非静态方法和访问器放在类的原型对象上；公开 `static`（静态）成员是构造函数本身的属性。

~~~javascript
class User {
  label = "member";
  get displayLabel() { return this.label; }
  greet() { return "Hi"; }
  static category = "account";
}

const user = new User();
Object.hasOwn(user, "label"); // true：实例字段
Object.hasOwn(user, "greet"); // false：方法在原型上
Object.hasOwn(Object.getPrototypeOf(user), "displayLabel"); // true
Object.hasOwn(User, "category"); // true：静态属性属于构造函数
~~~

箭头函数和上例 `greet()` 这样的普通简洁方法默认没有自有的 `prototype` 属性，也不能用 `new` 构造；生成器简洁方法与异步生成器简洁方法则有自有的 `prototype` 属性，但同样不能用 `new`。这些函数仍是对象，有自己的 `[[Prototype]]`。其构造能力边界会在[JavaScript 的 `new` 如何构造对象？](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F)中继续说明。

### 属性描述符决定读写是否执行代码

data descriptor（数据描述符）的 `value` 存值，`writable`（可写）控制能否通过赋值改值；accessor descriptor（访问器描述符）的 `get` 和 `set` 控制读取与写入时执行什么代码。两类都有 `enumerable`（可枚举）与 `configurable`（可配置）标记。对象字面量的普通数据属性通常三个标记都为真；`Object.defineProperty` 新建属性时未提供的标记都为假。

| 字段 | 作用 |
|---|---|
| `value`、`writable` | 数据属性保存的值，以及普通赋值能否更新它 |
| `get`、`set` | 读取或写入时调用的函数；未提供的读取器/设置器相当于 `undefined` |
| `enumerable` | `Object.keys` 只列自有、可枚举的字符串键；`for...in` 还会沿原型链枚举可枚举的字符串键；这两种枚举都不列 Symbol 键 |
| `configurable` | 是否通常可以删除、改标记，或在数据属性与访问器属性之间切换 |

~~~javascript
const descriptorDemo = {};
Object.defineProperty(descriptorDemo, "item", {
  value: 1, writable: true, enumerable: true, configurable: true,
});

Object.defineProperty(descriptorDemo, "item", { value: 2 });
const sameType = Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[sameType.value, sameType.writable,
  sameType.enumerable, sameType.configurable];
// [2, true, true, true]：同类描述符只更新给出的 value

Object.defineProperty(descriptorDemo, "item", { get() { return 3; } });
const switchedToAccessor =
  Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[descriptorDemo.item, switchedToAccessor.set,
  switchedToAccessor.enumerable, switchedToAccessor.configurable];
// [3, undefined, true, true]：writable/value 不再属于访问器描述符

Object.defineProperty(descriptorDemo, "item", { value: 4 });
const switchedToData =
  Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[switchedToData.value, switchedToData.writable,
  switchedToData.enumerable, switchedToData.configurable];
// [4, false, true, true]：新类型专有的 writable 缺省为 false

Object.defineProperty(descriptorDemo, "fresh", { value: 1 });
const fresh = Object.getOwnPropertyDescriptor(descriptorDemo, "fresh");
[fresh.writable, fresh.enumerable, fresh.configurable];
// [false, false, false]
~~~

更新已有属性时，未给出的同类字段保持原值。切换数据/访问器类型要求属性可配置；旧类型专有字段会去掉，新类型专有字段按默认值补齐，而未提供的共同字段 `enumerable`、`configurable` 继续保留。这个区别解释了上例：切换回数据属性后，`writable` 是 `false`，但可枚举、可配置仍是 `true`。不可配置属性不能任意删除或重新定义；给不可写属性或无 setter 的属性赋值时，strict mode（严格模式）中的普通赋值会抛出 `TypeError`，非严格代码则可能静默失败。

### 继承属性的赋值会调用 setter 或建立自有属性

读取与赋值都沿原型关系查找，但找到后执行的规则不同。若继承位置有 setter，setter 会以最初接收者作为 `this` 执行。沿链未找到同名属性，或找到可写的继承数据属性时，可扩展的接收者可以建立自有属性；若继承位置是不可写数据属性，普通赋值不能覆盖它。

~~~javascript
const defaults = { mode: "shared" };
const localSettings = Object.create(defaults);
localSettings.mode = "local";

[defaults.mode, localSettings.mode,
  Object.hasOwn(localSettings, "mode")];
// ["shared", "local", true]

const lockedDefaults = {};
Object.defineProperty(lockedDefaults, "mode", { value: "fixed" });
const lockedSettings = Object.create(lockedDefaults);
Reflect.set(lockedSettings, "mode", "changed"); // false：写入被拒绝
lockedSettings.mode; // "fixed"
~~~

`Object.defineProperty` 创建的 `lockedDefaults.mode` 默认不可写，所以赋值没有在实例建出同名属性。使用普通赋值时，严格代码对这种拒绝会抛出 `TypeError`；`Reflect.set` 则把写入是否成功作为布尔结果交还调用者。访问器 setter 仍可自行决定要改哪个状态，因此属性赋值不总等于写入同名字段。

自有属性会遮住原型上的同名属性；删除自有属性后，查找才会重新落到原型上。给构造函数添加静态属性，只会修改函数对象本身。下面的实例沿 `Example.prototype` 查找，不经过函数对象 `Example`，所以读不到它的静态属性；前面 `Child.prototype = Parent` 那种特意把函数对象放进原型链的配置则不同。

~~~javascript
function Example() {
  Example.value = function () { return 1; };
  this.value = function () { return 2; };
}
Example.prototype.value = function () { return 3; };
Example.value = function () { return 4; };

Example.value(); // 4
const instance = new Example();
instance.value(); // 2：实例自有属性遮住原型方法
delete instance.value;
instance.value(); // 3：删除遮蔽属性后，查找回到原型方法
Example.value(); // 1：构造函数体改写函数对象自己的静态属性
~~~

### 没有原型的对象与引擎优化

`Object.create(null)` 建立的字典对象没有原型，因此不会继承 `Object.prototype` 上的 `toString` 等属性：

~~~javascript
const dictionary = Object.create(null);
dictionary.toString; // undefined
"toString" in dictionary; // false
~~~

这适合确实需要没有继承键的字典；也意味着这些对象不能直接调用常规对象方法，使用前要明确要用哪些操作。

V8 可用 hidden class（隐藏类）和属性布局转换优化属性访问，但这是引擎实现选择，不是 ECMAScript 对象语义的保证。只有性能测量定位到属性访问瓶颈时，才值得为形状稳定性调整布局。

**相关机制：** [函数 `this` 与绑定](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F)解释方法调用和继承 getter 怎样接收 `this`；[使用 `new` 构造对象](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F)跟进实例的初始原型、构造器与返回值；[Proxy 代理对象](#36.%20JavaScript%20%E7%9A%84%20Proxy%20%E5%A6%82%E4%BD%95%E6%8B%A6%E6%88%AA%E5%AF%B9%E8%B1%A1%E6%93%8D%E4%BD%9C%EF%BC%9F)说明被拦截的读取、写入和属性描述符约束。

> [!info]- 来源
> - 属性读取沿原型链查找、并把原接收者传给 getter：[ECMAScript 2026 OrdinaryGet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryget)（§10.1.8.1）。
> - 属性写入沿链判断数据属性或调用 setter：[ECMAScript 2026 OrdinarySet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryset)（§10.1.9.1）和 [OrdinarySetWithOwnDescriptor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarysetwithowndescriptor)（§10.1.9.2）。
> - `Object.defineProperty`、描述符默认值与可枚举键：[ECMAScript 2026 Object.defineProperty](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.defineproperty)（§20.1.2.4）、[Object.keys](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.keys)（§20.1.2.19）和 [Object.hasOwn](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)（§20.1.2.14）。
> - 属性键是字符串或 Symbol，字符串与 Symbol 的自有键枚举：[ECMAScript 2026 ToPropertyKey](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)（§7.1.19）、[Object.getOwnPropertySymbols](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.getownpropertysymbols)（§20.1.2.11）。
> - 普通构造器依 `prototype` 属性选择新实例原型，并在属性不是对象时回退到构造器所在执行域的内建原型：[ECMAScript 2026 GetPrototypeFromConstructor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor)（§10.1.14）。[Class Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)（§15.7）规定类字段和方法的创建位置。
> - `Object.prototype.__proto__` 是规范标为可选实现且遗留的特性；读写原型优先用 `Object.getPrototypeOf` 与 `Object.setPrototypeOf`：[ECMAScript 2026 Object.prototype.__proto__](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.prototype.__proto__)（§20.1.3.8）。
> - V8 的隐藏类和属性访问优化：[V8 Fast Properties](https://v8.dev/blog/fast-properties)。
## 34. JavaScript 函数的 `this` 值由什么决定？

**案例背景。** 报表服务要把 Q4 数据格式化成一行文本：`service.onReport(...)` 能格式化报表，把同一个函数取出再裸调却抛 `TypeError`。函数值没有改变，调用表达式变了。本页讲 ordinary function（普通函数）在普通调用中的 `this`；构造调用见[JavaScript 的 `new` 如何构造对象？](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

以下每个代码块都可独立运行，行内注释给出求值结果。包含 sloppy function（非严格函数）的代码块须按 classic script（经典脚本）执行，不能改作 ES module（ES 模块）；DOM（Document Object Model，文档对象模型）例子需要浏览器页面已有 `document.body`。

### 调用形式为报表处理器提供接收者

同一个处理器先以方法形式调用，再取出裸调，最后恢复为方法调用：

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

const service = {
  prefix: "Sales",
  format(report, tag, sequence) {
    return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
  },
  onReport: makeReportHandler("daily"),
};

const firstReport = service.onReport({ title: "Q4" });
const detached = service.onReport;
let detachedError;
try {
  detached({ title: "Q4" });
} catch (error) {
  detachedError = error.name;
}
const thirdReport = service.onReport({ title: "Q4" });
[firstReport, detachedError, thirdReport];
// ["Sales/daily: Q4 #1", "TypeError", "Sales/daily: Q4 #3"]
~~~

`service.onReport(...)` 是方法调用，属性访问的基底 `service` 成为这次调用的 `this`。存入 `detached` 后再用变量调用，通常没有对象基底；这个 strict function（严格函数）收到 `undefined`，访问 `this.format` 时抛出 `TypeError`。处理器也把计数存在 closure（闭包）里；失败发生在递增之后，所以第三次调用成功时返回 `#3`。

### 严格模式会改变部分调用行为

先分清两步：ordinary function（普通函数）调用时，调用表达式提供一个 `this` 初值，即 receiver（接收者）；被调函数自己的模式再决定怎样绑定这个初值。点号或方括号属性调用会保留属性访问的基底，基底可以是对象或原始值。常见作用域里的变量裸调用 `fn()` 提供 `undefined`；非严格脚本的 `with` 环境是特殊情况，可以为这种调用提供对象接收者。

strict mode（严格模式）会让部分历史代码中的错误变成异常，也改变普通函数如何绑定 `this`。经典脚本或函数体可用开头的 `"use strict"` 指令启用它；ES module（ES 模块）和 class（类）方法则自动处于严格模式。strict function（严格函数）原样保留初值；sloppy function（非严格函数）把 `null` 或 `undefined` 换成函数所属 Realm（执行域）的全局 `this` 值，并把数字、字符串、布尔值、BigInt（大整数）或 Symbol（符号值）接收者装箱。即使调用表达式位于严格代码中，非严格被调函数仍会进行转换。严格模式不是安全沙箱，也不会让 `eval` 变安全。

| 被调函数模式 | 常见变量裸调用 `fn()` | `fn.call(null)` | `fn.call(7)` |
| --- | --- | --- | --- |
| strict function（严格函数） | `undefined` | `null` | 原始数字 `7` |
| sloppy function（非严格函数） | 所属 Realm 的全局 `this` 值 | 所属 Realm 的全局 `this` 值 | Number object（Number 包装对象） |

~~~javascript
function sloppyTarget() {
  return this;
}

function strictCaller() {
  "use strict";
  return sloppyTarget();
}
strictCaller() === globalThis; // true：被调函数仍按非严格模式绑定 this。

function writeUndeclaredName() {
  "use strict";
  undeclaredName = 1;
}

try {
  writeUndeclaredName();
} catch (error) {
  error.name; // "ReferenceError"
}
~~~

严格函数把 `this` 原样保留，非严格函数则按表格转换。`strictCaller` 虽然严格，仍不会替它调用的 `sloppyTarget` 改变模式。严格代码中给不可写属性赋值会抛出 `TypeError`，并禁止 `with`、旧式八进制字面量和严格函数中的重复形参。

### `call`、`apply` 与 `bind` 的调用时机不同

三个方法何时执行目标、怎样提供实参和 `thisArg`（传给目标函数的 `this` 参数）如下：

| 方法 | 目标执行时机 | 实参来源 | `thisArg`（传给目标函数的 `this` 参数）怎样到达目标 |
| --- | --- | --- | --- |
| `call` | 立即 | 后续分开的参数 | 原样交给目标；strict function 保留，sloppy function 按上一节转换 |
| `apply` | 立即 | 空列表，或从对象的 `length` 和索引读取 | 原样交给目标；strict function 保留，sloppy function 按上一节转换 |
| `bind`（绑定） | 调用返回的新函数时 | 保存的前置参数，再加调用时参数 | 保存并交给目标；strict function 保留，sloppy function 按上一节转换 |

目标若是 arrow function（箭头函数）或 bound function（绑定函数）则会忽略传入的 `thisArg`；箭头函数稍后单独说明。`apply` 省略 argument list（实参列表）或传 `null`、`undefined` 时使用空列表；其他输入必须是对象，内置方法按其 `length` 与数字索引读取实参，不会遍历迭代器。

~~~javascript
function describe(prefix, report, punctuation) {
  "use strict";
  const message = this.prefix + ": " + prefix + " " + report.title;
  return message + (punctuation === undefined ? "" : punctuation);
}

const salesContext = { prefix: "Sales" };
const report = { title: "Q4" };
const boundDescribe = describe.bind(salesContext, "Ready");
const reboundDescribe = boundDescribe.bind(
  { prefix: "Ignored" }, report, "!",
);

const callResults = [
  describe.call(salesContext, "Ready", report),
  describe.apply(salesContext, ["Ready", report]),
  describe.apply(salesContext, { 0: "Ready", 1: report, length: 2 }),
  boundDescribe(report),
  reboundDescribe(),
];

function countArgs() {
  return arguments.length;
}
let primitiveListError;
try {
  countArgs.apply(salesContext, "Q4");
} catch (error) {
  primitiveListError = error.name;
}
const applyResults = [
  countArgs.apply(salesContext),
  countArgs.apply(salesContext, null),
  countArgs.apply(salesContext, undefined),
  countArgs.apply(salesContext, { 0: "one", length: 1 }),
  countArgs.apply(salesContext, new Set(["one"])),
  primitiveListError,
];
[callResults[0], callResults[4], applyResults];
// [
//   "Sales: Ready Q4",
//   "Sales: Ready Q4!",
//   [0, 0, 0, 1, 0, "TypeError"],
// ]
~~~

再次对已绑定函数调用 `bind` 不会改掉最初保存的接收者，但会把新前置实参追加在原参数之后；`reboundDescribe()` 因此在原报表结果后追加标点。`Set` 实例没有 `length`，而 `apply` 不读取它的迭代器，所以这里得到空实参列表；原始字符串不是对象，作为原生 `apply` 的参数列表会抛 `TypeError`。`new` 调用可构造的绑定函数时会忽略已保存的接收者，却保留前置参数；构造行为见[JavaScript 的 `new` 如何构造对象？](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F)。只用包装函数拼接实参，不会自动得到原生绑定函数的构造行为或相同的 `name`、`length` 等元数据。

### 箭头函数与宿主回调遵循不同规则

arrow function（箭头函数）没有自己的 `this`、`arguments`、`super` 或 `new.target` 绑定，不能用 `new` 构造；它创建时也没有自有 `prototype` 属性。这两点并非因果关系，因为可构造的 bound function（绑定函数）也没有自有 `prototype`。箭头读取定义位置的 lexical `this`（词法 `this`）；`call`、`apply` 和 `bind` 可以传递实参或预填参数，但不能替换这个 `this`。需要让对象成为接收者时使用普通方法；需要词法 `this` 时才使用箭头函数。

~~~javascript
function makePanel(title) {
  return {
    title,
    read() { return this.title; },
    readArrow: label => this.title + ":" + label,
  };
}

const panel = makePanel.call({ title: "Outer" }, "Q4");
const arrowReader = panel.readArrow;
let arrowConstructError;
try {
  new arrowReader();
} catch (error) {
  arrowConstructError = error.name;
}
[
  panel.read(),
  panel.readArrow("direct"),
  panel.readArrow.call({ title: "Call" }, "call"),
  panel.readArrow.apply({ title: "Apply" }, ["apply"]),
  panel.readArrow.bind({ title: "Bind" }, "bind")(),
  Object.hasOwn(arrowReader, "prototype"),
  arrowConstructError,
];
// [
//   "Q4",
//   "Outer:direct", "Outer:call", "Outer:apply", "Outer:bind",
//   false, "TypeError",
// ]
~~~

`makePanel` 的这次调用通过 `call` 收到 `{ title: "Outer" }` 作为 `this`。`readArrow` 调用时访问的是 `makePanel` 这次调用的 `this`，其 `title` 值为 `"Outer"`，不是创建箭头时复制下来的一份值。之后的 `call`、`apply` 或 `bind` 都不能把箭头的 `this` 改成别的对象，但照常传入或预填 `"call"`、`"apply"`、`"bind"` 这些实参；`panel.read()` 是普通方法，才以 `panel` 为接收者。

host API（宿主 API）提供接收者的另一例是 DOM event listener（文档对象模型事件监听器）。普通监听函数运行时，DOM 把注册该监听器的当前对象设为 `event.currentTarget`，并作为监听函数的 `this`；事件冒泡时它可以与事件目标 `event.target` 不同；本例中前者是 `wrapper`，后者是按钮。`currentTarget` 只在监听器执行期间可用，派发结束后会重置。箭头仍保留外层 `this`，所以应通过事件对象显式读取目标：

~~~javascript
const button = document.createElement("button");
const wrapper = document.createElement("div");
wrapper.append(button);
document.body.append(wrapper);
const listenerResults = [];

wrapper.addEventListener("click", function (event) {
  const matches = this === event.currentTarget &&
    this === wrapper && event.target === button;
  listenerResults.push(matches);
});
wrapper.addEventListener("click", event => {
  const matches = event.currentTarget === wrapper &&
    event.target === button;
  listenerResults.push(matches);
});
button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
listenerResults;
// [true, true]
~~~

### 临时属性调用辅助函数只覆盖有限契约

临时 Symbol（符号值）属性能演示未绑定 ordinary function 通过 `receiver.method()` 如何把 `receiver` 作为 `this`：先将函数放到临时键，再用 `receiver[key](...)` 的方法调用形式执行它，最后删除该键。箭头函数和 bound function 会忽略这个方法接收者；这个办法也只适合可扩展的普通对象或函数。辅助函数会拒绝非对象接收者；原生 `call`、`apply`、`bind` 则把给定值传给目标，再由目标按自身严格性决定是否转换。non-extensible object（不可扩展对象）、Proxy（代理对象）以及宿主对象可能让属性定义、读取或删除失败或产生额外行为。

~~~javascript
function callWithObjectReceiver(fn, receiver, ...args) {
  if (receiver === null ||
      (typeof receiver !== "object" && typeof receiver !== "function")) {
    throw new TypeError("This exercise requires an object receiver");
  }
  const key = Symbol("temporary call");
  Object.defineProperty(receiver, key, { value: fn, configurable: true });
  try {
    return receiver[key](...args);
  } finally {
    delete receiver[key];
  }
}

const receiver = { base: 10 };
function addToBase(amount) {
  "use strict";
  return this.base + amount;
}
const sum = callWithObjectReceiver(addToBase, receiver, 3);

function failAfterReceivingThis() {
  "use strict";
  if (this !== receiver) throw new TypeError("receiver was lost");
  throw new Error("target failed");
}
let failureName;
try {
  callWithObjectReceiver(failAfterReceivingThis, receiver);
} catch (error) {
  failureName = error.name;
}
[sum, failureName, Object.getOwnPropertySymbols(receiver).length];
// [13, "Error", 0]
~~~

`finally` 会在目标抛错后继续执行删除语句；普通接收者的例子验证临时 Symbol 已清除。目标若把临时键改成不可配置，非严格辅助函数的删除会返回 `false`，键会留下；若辅助函数处于严格模式，删除会抛 `TypeError` 并可能替换目标原先的异常。归档中的 `myApply` 练习用 `Array.prototype.slice.call` 复制类数组实参，遇到 `null` 或 `undefined` 时直接使用空列表，再委托给范围受限的 `myCall`；`countArgs.myApply(receiver, [])` 与 `countArgs.myApply(receiver, null)` 都令被调函数收到 0 个实参。

> [!info]- 归档练习：范围受限的 myCall 与 myApply
>
> 该练习用临时 Symbol 属性制造方法调用语法，只接受对象或函数接收者。apply 版本把 nullish（`null` 或 `undefined`）实参列表当作空列表，并复制其他 array-like（类数组）输入；它不模拟原始值接收者转换，也不完全复现原生 `apply` 对非对象实参列表的检查，且不能覆盖不可扩展对象和 Proxy 的所有行为。
>
> ~~~javascript
> Function.prototype.myCall = function (context, ...args) {
>   if (context === null ||
>       (typeof context !== "object" && typeof context !== "function")) {
>     throw new TypeError("This exercise requires an object receiver");
>   }
>   const key = Symbol("temporary call");
>   Object.defineProperty(context, key, {
>     value: this, configurable: true,
>   });
>   try {
>     return context[key](...args);
>   } finally {
>     delete context[key];
>   }
> };
>
> Function.prototype.myApply = function (context, args) {
>   const list = args === null || args === undefined
>     ? []
>     : Array.prototype.slice.call(args);
>   return this.myCall(context, ...list);
> };
>
> const receiver = { base: 10 };
> function sum(a, b) { return this.base + a + b; }
> function countArgs() { return arguments.length; }
>
> const zeroWithArray = countArgs.myApply(receiver, []);
> const zeroWithNull = countArgs.myApply(receiver, null);
> [sum.myCall(receiver, 1, 2), zeroWithArray, zeroWithNull];
> // [13, 0, 0]
> ~~~
>
> 唯一 Symbol 避免与既有字符串键冲突；`finally` 总会执行删除尝试，但目标若让临时键不可配置，属性就无法清除。向 `Function.prototype` 添加自定义方法会修改共享内置对象，因此这仅是机制练习，应用代码应使用内置方法。

**相关机制：** [JavaScript 对象如何查找属性？](#33.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%B1%9E%E6%80%A7%E5%B9%B6%E7%BB%84%E7%BB%87%E6%88%90%E5%91%98%EF%BC%9F) 解释属性查找和 getter；[JavaScript 的 `new` 如何构造对象？](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F) 说明绑定函数构造时为何忽略已绑定的 `this`。

> [!info]- 来源
>
> - 严格模式与普通调用的接收者绑定：[ECMAScript 2026 Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)、[Function Calls](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-function-calls) 和 [OrdinaryCallBindThis](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinarycallbindthis)（§10.2.1.2）。
>
> - 显式接收者与绑定函数：[ECMAScript Function.prototype.call](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.call)、[Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply) 和 [Function.prototype.bind](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.bind)；箭头函数：[Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)。
>
> - DOM 普通事件监听器的接收者：[WHATWG DOM Event Listener Invocation](https://dom.spec.whatwg.org/#concept-event-listener-invoke)。
## 35. JavaScript 的 `new` 如何构造对象？

创建一个报表服务时，我们希望新对象保留自己的区域名称，同时复用共享的格式化方法。`new ReportService("Sales")` 怎样选定它的原型、让构造器里的 `this` 指向它，最后又为什么可能返回另一个对象？先跟完这个普通基类构造过程，再看派生 `class`、`new.target` 和绑定函数的变化。

### 报表服务使用构造出的接收者

案例背景：报表页面创建一个区域服务。新对象需要保留自己的 `prefix` 和带独立调用次数的处理器；格式化算法在构造函数的原型对象上共享：

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

function ReportService(prefix) {
  this.prefix = prefix;
  this.onReport = makeReportHandler("daily");
}

ReportService.prototype.format = function (report, tag, sequence) {
  return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
};

const service = new ReportService("Sales");
Object.getPrototypeOf(service) === ReportService.prototype; // true
service.prefix; // "Sales"
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
~~~

**先选原型并建立接收者。** 在直接调用 `new C(a, b)` 时，语言先求值构造器表达式和实参，再检查 `C` 是否有 `[[Construct]]` internal method（内部构造方法）；没有就抛 `TypeError`。这里的内部方法是语言定义的构造操作，并非用户对象上名为 `Construct` 的属性。普通基类构造从 `newTarget.prototype` 选择新对象的内部原型 `[[Prototype]]`；直接 `new C(...)` 时，`newTarget` 就是 `C`。

下图从目标已通过构造能力检查后开始，只画普通基类构造；receiver（接收者）指新建并将交给构造器作为 `this` 的对象。

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  P["读取 newTarget.prototype"] --> T{"读取值是对象？"}
  T -->|是，包括函数| V["采用这个对象作为原型"]
  T -->|否，包括 null| R["采用 newTarget 所属 Realm 的<br/>Object.prototype"]
  V --> I["创建接收者，绑定 this<br/>初始化实例字段（若有）"]
  R --> I
~~~

本例的 `newTarget` 是 `ReportService`，它的 `.prototype` 是对象，因此走左支。构造函数还没运行，接收者已经连接到共享的原型对象；随后 `this.prefix` 和 `this.onReport` 写到这个接收者。这里的原型回退按 `newTarget` 所属 Realm（执行域）选择，该环境有自己的一套内建对象；不要默认总是当前代码所在环境的 `Object.prototype`。

构造器没有返回替换对象，所以 `service` 就是新接收者。接着 `service.onReport(...)` 使 `service` 成为处理器的 `this`；处理器沿实例原型找到 `format`，再从接收者读取 `prefix`。调用形式如何提供这个接收者，见[JavaScript 函数的 `this` 值由什么决定？](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F)；共享方法如何被找到，见[JavaScript 对象如何查找属性并组织成员？](#33.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%B1%9E%E6%80%A7%E5%B9%B6%E7%BB%84%E7%BB%87%E6%88%90%E5%91%98%EF%BC%9F)。

读取原型、初始化实例字段或执行构造器时若抛错，本次构造就中断，不会继续到正常返回。派生 `class` 的接收者初始化另有规则，下面接着说明。

只要 `newTarget.prototype` 的值是对象，它就可以作为新接收者的原型，函数本身也可以。普通 `new C()` 中 `newTarget` 就是 `C`；若普通函数构造器的 `prototype` 为 `null` 或其他原始值，构造过程会回退到 `newTarget` 所属 Realm 的 `Object.prototype`：

~~~javascript
function Parent() {}
function Child() {}
Child.prototype = Parent; // 函数也是对象，可以作为原型
Object.getPrototypeOf(new Child()) === Parent; // true

function FallbackDemo() {}
FallbackDemo.prototype = null;
// 同一 Realm：回退到当前 Object.prototype
Object.getPrototypeOf(new FallbackDemo()) === Object.prototype; // true
~~~

### 构造器返回值可能替换接收者

**再运行函数体并选择最终结果。** 沿用上一图已建立的接收者，普通基类构造器会把实参交给函数体。函数体对 `this` 的修改留在接收者上，但最终是否返回它，要看构造器的返回值：

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 280}}}%%
flowchart TD
  I["已有接收者作为 this<br/>运行构造器函数体"] --> T{"返回值是对象？"}
  T -->|是，包括函数| O["返回显式对象<br/>它替换新建的接收者"]
  T -->|否，包括 null 和 undefined| N["返回新建的接收者"]
~~~

数字、字符串、布尔值、Symbol、BigInt、`null` 和 `undefined` 都是 primitive value（原始值），不用于替换接收者。没有显式 `return` 时相当于返回 `undefined`，所以报表案例走右支。以下四个例子分别改变返回值，其他构造规则不变：

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive().created; // true：数字返回值被忽略

function ReturnsNull() {
  this.created = true;
  return null;
}
new ReturnsNull().created; // true：null 也不是对象

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }：显式对象取代 this

function ReturnsFunction() {
  return function replacement() {};
}
typeof new ReturnsFunction(); // "function"
~~~

派生 `class` 构造器（derived constructor）必须先由 `super()` 初始化 `this`，才能读取或写入它。`super()` 用同一个 `newTarget` 调用基类构造器，并把基类构造结果绑定为派生构造器的 `this`；因此基类显式返回对象时，派生构造器接着初始化的是这个返回对象。如果派生构造器直接返回对象或函数，则可以不调用 `super()`。派生构造器的返回规则也不同于基类：调用 `super()` 后返回 `undefined` 会采用已初始化的 `this`，返回对象或函数会替换它；未调用 `super()` 却返回 `undefined` 会因没有接收者而抛出 `ReferenceError`，返回 `null` 或其他原始值会抛出 `TypeError`。

下面的派生类示例沿用上节已经定义的 `ReportService`；从头执行本文代码时先运行上节报表案例。

~~~javascript
class FactoryReport extends ReportService {
  constructor(prefix) {
    return new ReportService(prefix); // 返回对象，可以不调用 super()
  }
}

const factoryResult = new FactoryReport("North");
factoryResult.prefix; // "North"
Object.getPrototypeOf(factoryResult) === ReportService.prototype; // true
factoryResult instanceof FactoryReport; // false：结果是替换对象

class InvalidDerivedReport extends ReportService {
  constructor() {
    return 1; // 非 undefined 原始值不允许
  }
}
try {
  new InvalidDerivedReport();
} catch (error) {
  error.name; // "TypeError"
}

class UninitializedReport extends ReportService {
  constructor() {
    return undefined; // 没有 super()，也没有初始化 this
  }
}
try {
  new UninitializedReport();
} catch (error) {
  error.name; // "ReferenceError"
}
~~~

### `new.target` 标识本次构造目标

`new.target` 读取这次构造传入的 `newTarget`。普通 `new C()` 中它是 `C`；`Reflect.construct(C, args, D)` 运行的仍是 `C`，但让 `D` 成为 `newTarget`，于是普通基类创建接收者时改从 `D.prototype` 选原型。省略第三参数时 `newTarget` 仍为 `C`。相反，把不可构造的箭头函数传作第三参数，如 `Reflect.construct(function C() {}, [], () => {})`，会抛出 `TypeError`，不会进入目标构造器函数体。

> [!info] Reflect 的检查顺序
> `Reflect.construct` 是函数调用，先求值 `C`、`args` 和 `D` 的实参表达式。进入它后先检查 `C`、显式提供时再检查 `D`，两者都必须可构造；随后要求 `args` 是对象，从它读取数组状的实参列表，最后启动构造。任一步抛错就不再继续。这个顺序不同于“先读取参数列表，再判断能不能构造”。

派生 class 每次调用 `super()` 都把同一个 `newTarget` 传给基类，因此多层继承中每一层构造器都看到同一次构造传入的目标。`super()` 把基类的构造结果（包括基类显式返回的对象）绑定为派生构造器的 `this`，再初始化派生类自己的实例字段。

下面的派生类代码沿用前面报表案例中已经定义的 `makeReportHandler` 和 `ReportService`；请按本文顺序执行。

~~~javascript
class RegionalReportService extends ReportService {
  constructor(prefix) {
    super(prefix);
    this.createdBy = new.target;
  }
}

const regional = new RegionalReportService("Sales");
regional.createdBy === RegionalReportService; // true
Object.getPrototypeOf(regional) ===
  RegionalReportService.prototype; // true
regional.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
~~~

**箭头读取外层收到的目标。** 下面让同一个函数分别被普通调用和构造调用；它返回一个箭头函数，稍后再读出那次调用的 `new.target`：

~~~javascript
function TargetReader() {
  return () => new.target;
}

const arrowFromCall = TargetReader();
const arrowFromConstruction = new TargetReader();
[
  arrowFromCall() === undefined,
  arrowFromConstruction() === TargetReader,
]; // [true, true]
~~~

**Reflect 可以分开“执行谁”和“按谁选原型”。** `BaseReader` 执行函数体，而 `AlternateTarget` 提供本次 `newTarget`：

~~~javascript
function BaseReader() {
  this.seenTarget = new.target;
}
function AlternateTarget() {}
AlternateTarget.prototype = { source: "alternate" };
const reflected = Reflect.construct(BaseReader, [], AlternateTarget);
const reflectedResults = [
  reflected.seenTarget === AlternateTarget,
  Object.getPrototypeOf(reflected) === AlternateTarget.prototype,
]; // [true, true]
reflectedResults; // [true, true]
~~~

**基类返回的对象沿 `super()` 传给派生层。** 这个三层例子里的基类返回新对象，每一层接着使用它；`new.target` 始终是 `LeafLayer`：

~~~javascript
class ReplacementBase {
  constructor() {
    return { fromBase: true, seenByBase: new.target };
  }
}
class MiddleLayer extends ReplacementBase {
  constructor() {
    super();
    this.fromMiddle = true;
  }
}
class LeafLayer extends MiddleLayer {
  constructor() {
    super();
    this.seenByLeaf = new.target;
  }
}
const leaf = new LeafLayer();
const leafResults = [
  leaf.fromBase,
  leaf.fromMiddle,
  leaf.seenByBase === LeafLayer,
  leaf.seenByLeaf === LeafLayer,
];
leafResults; // [true, true, true, true]
~~~

`new.target` 不是等价于构造器函数体的局部名称：它是沿这次构造传递的目标。箭头函数自身不建立这个绑定。在本例的函数内嵌套中，它沿词法环境读取 `TargetReader` 那次调用收到的 `newTarget`。`TargetReader()` 直接调用时该值是 `undefined`，`new TargetReader()` 时是 `TargetReader`；通过 `new LeafLayer()` 逐层执行 `super()` 进入基类时，基类中的 `new.target` 仍是 `LeafLayer`，不是当前执行的基类构造器名称。

### 可调用的函数未必可以用 `new`

构造器表达式与实参求值完毕后，`new` 按 `IsConstructor`（构造能力检查）判断目标是否具有构造能力；仅能被普通调用不够。普通函数声明通常可构造。class 构造器也有构造能力，可以作为 `Reflect.construct` 的目标或通过派生类的 `super()` 调用；直接写 `C()` 则会抛出 `TypeError`。箭头函数、普通非生成器简洁方法、生成器函数、async function（异步函数）和 async generator（异步生成器）都不可构造；生成器与异步生成器简洁方法也不可构造。函数上是否有名为 `prototype` 的属性不能单独证明它可构造，例如生成器函数及生成器简洁方法可以有这个属性但仍不支持 `new`。

这两项能力可以直接并排看。下表检查语法刚创建的函数，尚未手动添加、删除或替换其属性：

| 函数形式 | 自有 `prototype` | 能否作为构造目标 |
|---|---|---|
| 普通 `function F() {}` | 有 | 能 |
| `class C {}` | 有 | 能；直接 `C()` 仍报错 |
| 箭头函数 | 无 | 不能 |
| 普通非生成器简洁方法 | 无 | 不能 |
| 生成器函数或生成器简洁方法 | 有 | 不能 |
| 异步函数或普通异步简洁方法 | 无 | 不能 |
| 异步生成器函数或方法 | 有 | 不能 |

能力检查不阻止更早的实参求值。下面目标不可构造，但计数已经增加；因此不能把 `new` 的错误理解成“什么都没发生”：

~~~javascript
const notAConstructor = () => {};
let argumentCount = 0;
let constructionError;
try {
  new notAConstructor(++argumentCount);
} catch (error) {
  constructionError = error.name;
}
[constructionError, argumentCount]; // ["TypeError", 1]
~~~

绑定函数（bound function）是否能构造取决于目标函数：目标可构造时，`bind` 返回的绑定函数也可构造。使用 `new` 调用它时，已经绑定的 `this` 会被忽略，但绑定的前置参数仍会加入实参列表；当 `newTarget` 正是这个绑定函数时，构造会改用原目标函数作为 `newTarget`。

~~~javascript
function BuildReport(prefix, title) {
  this.prefix = prefix;
  this.title = title;
  this.seenTarget = new.target;
}

const boundBuildReport = BuildReport.bind({ prefix: "ignored" }, "North");
const builtReport = new boundBuildReport("Q4");
[
  builtReport.prefix,
  builtReport.title,
  builtReport.seenTarget === BuildReport,
  Object.getPrototypeOf(builtReport) === BuildReport.prototype,
];
// ["North", "Q4", true, true]
~~~

### 简化的 `new` 模型有有限输入范围

下面的教学模型只模拟当前 Realm 中直接使用的普通基类函数构造器：目标须已知可构造，函数体不依赖 `new.target`，而 `fn.prototype` 的值和构造器的直接返回值均不能是浏览器历史特殊对象 `document.all`。该对象虽然 `typeof` 返回 `"undefined"`，语言仍将它视为对象；模型用 `typeof` 判断这两个直接值时无法识别它。模型展示原型选择、接收者绑定和显式返回对象替换规则；不实现 class、派生构造器、绑定函数、内置构造器、Proxy 的 `construct` trap 或跨 Realm 回退。应用代码应直接使用 `new`、class 语法或 `Reflect.construct`。

~~~javascript
function emulateNew(fn, ...args) {
  const candidate = fn.prototype;
  const prototype =
    candidate !== null &&
    (typeof candidate === "object" || typeof candidate === "function")
      ? candidate
      : Object.prototype;
  const receiver = Object.create(prototype);
  const result = Reflect.apply(fn, receiver, args);
  const isObject =
    result !== null &&
    (typeof result === "object" || typeof result === "function");
  return isObject ? result : receiver;
}

function SimpleReport(prefix) {
  this.prefix = prefix;
}
SimpleReport.prototype.describe = function () { return this.prefix; };

const simple = emulateNew(SimpleReport, "West");
[
  Object.getPrototypeOf(simple) === SimpleReport.prototype,
  simple.describe(),
];
// [true, "West"]
~~~

改用 `Reflect.apply` 可避免函数自有的 `apply` 属性遮住内建调用方法，但这个模型依旧不能替代 `[[Construct]]`：它没有 `newTarget`，会把箭头函数当作普通函数调用，也不能调用 class 构造器。不能仅凭 `typeof fn === "function"` 就判断它可构造，class 也不能被这个模型当作普通函数执行。

**相关机制：** [Proxy 如何拦截构造操作？](#36.%20JavaScript%20%E7%9A%84%20Proxy%20%E5%A6%82%E4%BD%95%E6%8B%A6%E6%88%AA%E5%AF%B9%E8%B1%A1%E6%93%8D%E4%BD%9C%EF%BC%9F)说明可构造代理和 `construct` trap 必须返回对象的条件；[JavaScript 对象如何查找属性并组织成员？](#33.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%B1%9E%E6%80%A7%E5%B9%B6%E7%BB%84%E7%BB%87%E6%88%90%E5%91%98%EF%BC%9F)解释新实例连接原型后怎样找到共享成员。

> [!info]- 来源
> - `new` 表达式先检查目标是否具有构造能力，再调用 `Construct`：[ECMAScript 2026 EvaluateNew](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-evaluatenew)（§13.3.5.1.1）。
> - 普通函数的接收者创建、实例字段初始化与基类/派生构造返回规则：[ECMAScript 2026 Function Objects `[[Construct]]`](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects-construct-argumentslist-newtarget)（§10.2.2）。
> - 从 `newTarget.prototype` 选原型及非对象回退：[ECMAScript 2026 GetPrototypeFromConstructor](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor)（§10.1.14）。
> - 派生 class 的构造器和 `super()` 语义：[ECMAScript 2026 Class Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)（§15.7）。
> - `new.target` 取得当前函数环境中的 `NewTarget`：[ECMAScript 2026 GetNewTarget](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getnewtarget)（§9.4.5），以及 [Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)（§9.1.1.3）。
> - `Reflect.construct` 先检查 `target` 和 `newTarget` 的构造能力，再把 `argumentsList` 转成实参列表：[ECMAScript 2026 Reflect.construct](https://tc39.es/ecma262/2026/multipage/reflection.html#sec-reflect.construct)（§28.1.2）。派生类执行 `super()` 时沿用同一个 `newTarget`，并把基类构造结果绑定为 `this`：[SuperCall](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-super-keyword)（§13.3.7.1）。
> - 绑定函数只有在目标可构造时才有 `[[Construct]]`，构造时合并前置实参并处理 `newTarget`：[ECMAScript 2026 Bound Function Exotic Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-bound-function-exotic-objects)（§10.4.1）。
> - 箭头函数没有本地 `new.target` 绑定，`new.target` 会沿词法环境解析：[ECMAScript 2026 Arrow Function Definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)（§15.3）。
> - 浏览器的 `document.all` 是带 `[[IsHTMLDDA]]` 的 `HTMLAllCollection` 对象，因此 `typeof` 会返回 `"undefined"`：[WHATWG HTML Standard HTMLAllCollection](https://html.spec.whatwg.org/multipage/common-dom-interfaces.html#the-htmlallcollection-interface)（§2.6.4.1）。
## 36. JavaScript 的 `Proxy` 如何拦截对象操作？

Proxy（代理对象）把 target（目标对象）与 handler（处理器）配对。经代理执行读取、赋值等操作时，对应 trap（拦截方法）可以观察或改变操作；未定义 trap 时默认按目标对象执行。Reflect（反射 API）转发操作并保留 receiver 语义，但 trap 仍须遵守固定属性的不变量。

### 报表处理器只观察经过代理的操作

案例背景：本页新建一个构造器、实例和处理器。先用直接读取 `target[property]` 的代理观察继承 getter，再用 `Reflect.get` 显示 receiver（接收者）为何会改变 getter 内部读取是否经过代理；最后追踪方法调用的日志来源：

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

function ReportService(prefix) {
  this.prefix = prefix;
  this.onReport = makeReportHandler("daily");
}

ReportService.prototype.format = function (report, tag, sequence) {
  return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
};

Object.defineProperty(ReportService.prototype, "label", {
  configurable: true,
  get() {
    return this.prefix + " reports";
  },
});

const service = new ReportService("Sales");
const direct = new Proxy(service, {
  get(target, property) {
    console.log("direct get", String(property));
    return target[property];
  },
});

const observed = new Proxy(service, {
  get(target, property, receiver) {
    console.log("get", String(property));
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("set", String(property));
    if (property === "prefix" && typeof value !== "string") {
      throw new TypeError("prefix must be a string");
    }
    return Reflect.set(target, property, value, receiver);
  },
});

direct.label;
// 记录 direct get label；返回 "Sales reports"，getter 的 this 是 target

observed.label;
// 记录 get label、get prefix；getter 的 this 是 observed

observed.onReport({ title: "Q4" });
// 记录 get onReport、get format、get prefix
// 返回 "Sales/daily: Q4 #1"

observed.prefix = "Ops"; // 记录 set prefix
observed.onReport({ title: "Q4" }); // "Ops/daily: Q4 #2"
~~~

直接代理的 `direct.label` 只触发 `direct get label`：求值 `target[property]` 时，继承 getter 的 `this` 是原始 target，所以 getter 读取 `this.prefix` 不再经过代理。`Reflect.get(target, property, receiver)` 显式把代理作为 getter 的接收者，因此 `observed.label` 还会触发 `get prefix`。

方法日志则来自另一个机制。`observed.onReport(...)` 是方法调用，返回的处理器以 `observed` 为 `this`；它读取 `this.format` 时触发 `get format`，`format` 再读取 `this.prefix` 时触发 `get prefix`。即使 trap 用直接的 `target[property]` 返回这个方法，调用表达式仍会把 `observed` 作为 `this`。若代码保留原始 `service` 引用，就能绕过代理。代理也有独立身份：`observed !== service`。Proxy 是 JavaScript 运行时对象特性，不是 TypeScript 类型特性。

### trap 必须保留属性操作的可观察语义

getter 会在读取时执行代码，不是被动存储的值。若 trap 直接求值 `target[property]`，继承的 getter 会以 `target` 为 `this`。使用 `Reflect.get(target, property, receiver)` 转发会保留 `receiver`，因此 getter 对其他属性的读取也能经过代理观察。`Reflect.set` 同样接收 `receiver`，并返回布尔值。

若 `set` trap 返回 `false`，非严格赋值可能静默失败，严格赋值会抛出 `TypeError`。返回 `true` 也不能让 trap 违背 `target` 的某些固定属性。

~~~javascript
const rejected = new Proxy({ prefix: "Sales" }, {
  set() { return false; },
});

Reflect.set(rejected, "prefix", "Ops"); // false
rejected.prefix; // "Sales"
(function () {
  "use strict";
  rejected.prefix = "Ops"; // TypeError：set trap 报告写入失败
})();
~~~

Proxy invariant（代理不变量）禁止 trap 对不可配置的 `target` 属性报告矛盾结果。例如，`get` trap 不能为不可配置且不可写的自有数据属性返回其他值；对应的不可配置访问器若没有 getter，则必须返回 `undefined`。`set` trap 不能谎报对固定不可写属性的修改成功，也不能谎报对不可配置且没有 setter 的访问器写入成功。违反约束会抛出 `TypeError`。

~~~javascript
const fixed = Object.freeze({ id: 7 });
const inconsistent = new Proxy(fixed, {
  get(target, property, receiver) {
    if (property === "id") return 8;
    return Reflect.get(target, property, receiver);
  },
});

inconsistent.id; // TypeError：不能用 8 代替固定值 7
~~~

一个高层操作可能触发多个 trap。例如 `array.push(value)` 会写入数组索引，并更新 `length`。校验或记录写入时，应覆盖需要观察的每个操作。

归档中的校验示例用数字属性演示读写：读取和写入都会被记录，无效写入则在转发前抛错。因此 Proxy 会改变可观察行为，不是透明的性能优化。

~~~javascript
const product = new Proxy({ price: 10 }, {
  get(target, property, receiver) {
    console.log("read", String(property));
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("write", String(property));
    if (property === "price" && (!Number.isFinite(value) || value < 0)) {
      throw new RangeError("price must be a non-negative finite number");
    }
    return Reflect.set(target, property, value, receiver);
  },
});

product.price = 12; // 记录 write price 并更新目标对象
product.price;      // 12；触发 get trap
// product.price = -1; // 在转发写入前抛出 RangeError
~~~


### 可调用和可构造 target 保留相应能力

Proxy 的 `target` 必须是对象。若 `target` 可调用或可构造，代理也具有相应能力；`construct` trap 必须返回对象。`Reflect.construct` 会连同参数一起转发 `newTarget`。

~~~javascript
function ReportFactory(prefix) {
  this.prefix = prefix;
}

const tracedFactory = new Proxy(ReportFactory, {
  construct(target, args, newTarget) {
    console.log("construct", args[0]);
    return Reflect.construct(target, args, newTarget);
  },
});

const created = new tracedFactory("Finance"); // 记录 construct Finance
created instanceof ReportFactory; // true
~~~

Vue 2 用访问器实现响应式属性，Vue 3 则对响应式对象使用 Proxy；这是框架选择的例子，不代表所有应用都必须采用其中一种。

已知属性有稳定读写契约时使用访问器；需要拦截对象上的操作时再用 Proxy，例如校验之后新增的键或记录一组属性访问。Proxy 无法观察通过另行保留的 `target` 引用执行的操作。

**相关机制：** [对象与原型](#33.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%B1%9E%E6%80%A7%E5%B9%B6%E7%BB%84%E7%BB%87%E6%88%90%E5%91%98%EF%BC%9F) 解释属性描述符和 getter；[使用 `new` 构造对象](#35.%20JavaScript%20%E7%9A%84%20new%20%E5%A6%82%E4%BD%95%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%EF%BC%9F) 说明代理构造和 `construct` 的边界。


> [!info]- 来源
> - Proxy 的 target/handler 分发、get/set 和 construct：[ECMAScript 2026 Proxy Object Internal Methods](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-proxy-object-internal-methods-and-internal-slots)（§10.5）。
> - Proxy trap 必须遵守的对象内部方法不变量：[ECMAScript Invariants of the Essential Internal Methods](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-invariants-of-the-essential-internal-methods)（§6.1.7.3）。
> - getter 的 receiver 语义：[ECMAScript OrdinaryGet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryget)（§10.1.8.1）；对应转发 API：[ECMAScript Reflect](https://tc39.es/ecma262/2026/multipage/reflection.html)（§28）。
> - Vue 2 与 Vue 3 响应式机制的实现选择：[Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html)。
## 37. 函数变换如何改变调用过程？

函数可以返回新函数，也可以由包装器改变一次调用的处理流程。本章沿调用过程看 rest parameter（剩余参数）、currying（柯里化）与 partial application（部分应用）、composition（组合）、decorator（装饰器）和 memoization（记忆化）：参数何时齐备、this 如何传递、返回值与异常如何处理；涉及缓存时再定义键策略。

### 返回函数可以捕获状态，也可以不捕获

rest parameter（剩余参数）把尚未被前面形参接收的实参收集成数组；下面的函数只有 `...args`，所以它收集全部实参。显式传入 `undefined` 仍计为一个实参。返回函数只有在后续调用需要读取外层绑定时，才需要 closure（闭包）状态。

~~~javascript
function argumentsLength(...args) {
  return args.length;
}

argumentsLength();            // 0
argumentsLength(undefined);   // 1
argumentsLength({}, null, 3); // 3

function createHelloWorld() {
  return () => "Hello World";
}

const hello = createHelloWorld();
hello({}, null, 42); // "Hello World"；无需捕获状态
~~~

JavaScript 函数即使没有声明形参，也可以接收多余实参；这里没有读取它们，所以不需要声明 rest parameter。

### 柯里化把实参分到多次调用中提供

严格意义的 currying（柯里化）把多参数函数变为每次接收一个参数的一串函数，例如 `sum(a, b, c)` 变为 `curriedSum(a)(b)(c)`。partial application（部分应用）则先固定部分实参，返回等待其余实参的新函数，不要求每次只接收一个。下面是常见的宽松 `curry` 辅助函数：它允许一次提供一个或多个实参，收集够声明的数量后才调用原函数。简单位置参数函数可用 `fn.length` 作为 arity（元数）约定，但它不代表通用参数契约：它只数第一个带默认值的形参之前的形参，rest parameter 也不计入长度。占位符和可变参数函数需要另定规则。

~~~javascript
function curry(fn) {
  "use strict";
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return function (...next) {
      return curried.apply(this, args.concat(next));
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);

curriedSum(1)(2)(3); // 6
curriedSum(1, 2)(3); // 6
curriedSum(1, 2, 3); // 6

function describeParts(prefix, period) {
  return this.name + ":" + prefix + "/" + period;
}

const partial = curry(describeParts).call({ name: "first" }, "daily");
partial.call({ name: "final" }, "Q4"); // "final:daily/Q4"
~~~

以 `curriedSum(1)(2)(3)` 为例，参数的状态变化如下。每一步返回的函数都保留当前前缀；它不会把其他分支的前缀一起修改。

| 这次调用 | 当前收集到的实参 | 是否调用 `sum` | 返回值 |
| --- | --- | --- | --- |
| `curriedSum(1)` | `[1]` | 否，距离 `sum.length = 3` 还差两个 | 等待后续参数的函数 |
| 上一步结果 `(2)` | `[1, 2]` | 否，还差一个 | 新的等待函数 |
| 上一步结果 `(3)` | `[1, 2, 3]` | 是，调用 `sum(1, 2, 3)` | `6` |

不借助 `curry` 也能做部分应用：`const addOneDirect = (b, c) => sum(1, b, c)` 固定第一个参数，调用 `addOneDirect(2, 3)` 得到 `6`。它一次接收剩余两个参数。下面的 `const addOne = curriedSum(1)` 既是宽松柯里化的一步，也产生了固定前缀的部分应用；它可先调用 `addOne(2, 3)` 得到 `6`，再调用 `addOne(4, 5)` 得到 `10`；两次都从同一个 `[1]` 前缀开始。对于 `function f(a, b = 10) { return a + b; }`，`f.length` 为 `1`，所以 `curry(f)(2)` 已立即返回 `12`，不会等待第二次调用。这正是必须先选择参数契约的原因。

这个实现会转发补足参数那次调用的接收者，不会保存第一次部分调用的接收者。达到声明元数时，它也会保留多余实参。这些都属于该辅助函数的契约。

### 组合把上一步输出接到下一步输入

function composition（函数组合）从右向左执行：`compose([f, g, h])(x)` 计算 `f(g(h(x)))`。函数列表为空时返回 identity function（恒等函数），也就是原样返回输入。

~~~javascript
function compose(functions) {
  return function (value) {
    for (let i = functions.length - 1; i >= 0; i--) {
      const step = functions[i];
      value = step(value);
    }
    return value;
  };
}

const transform = compose([
  value => value + 1,
  value => value * value,
  value => 2 + value,
]);

transform(4); // 37: 4 -> 6 -> 36 -> 37
compose([])(42); // 42
~~~

对 `n` 个单输入函数，每次正常完成的组合调用执行 `n` 次，循环仅使用常量额外空间。若操作不可交换或带副作用，执行顺序就很重要。这个 `compose` 是同步组合：某一步抛错会立即退出循环，把同一个异常传给调用者，左侧剩余步骤不会运行；某一步返回 Promise 时，它会把这个 Promise 对象原样交给下一步，不会等待兑现值。若步骤需要异步串接，应显式选择 Promise 链或 async/await 的组合契约。

循环先把步骤函数取到局部变量，再裸调用，避免把 `functions` 数组意外作为接收者。裸调用提供 `undefined` 接收者；被调用函数若为非严格函数，仍会按自身规则将其转换为全局对象。

### 包装器转发一次调用并附加一种策略

wrapper（包装器）是调用原函数并附加策略的新函数。计时 decorator（装饰器）应转发 `this` 和全部实参，并在原函数返回或抛错时都报告耗时。`finally` 会处理正常返回和异常完成两种情况；只要记录耗时本身正常完成，原返回值或异常便继续向外传递。若 `finally` 自己抛错或执行 `return`，则会覆盖之前的完成结果。

~~~javascript
function withTiming(fn) {
  "use strict";
  return function (...args) {
    const started = performance.now();
    try {
      return fn.apply(this, args);
    } finally {
      console.log((fn.name || "operation") + ": " +
        (performance.now() - started) + " ms");
    }
  };
}
~~~

包装器本身是严格函数，因此裸调用时收到的 `undefined` 会原样传给 `fn.apply`；被包装函数仍按自己的严格性决定如何处理它。若包装器在非严格模式下运行，裸调用时 `this` 会先变成全局对象，`apply` 就无法保留原调用的接收者语义。这个计时包装器只测同步执行时间。若 `fn` 返回 Promise，`finally` 会在 Promise 对象返回后立即运行，不会计入异步操作完成前的时间；测异步完成耗时需要按 Promise 生命周期另行包装。

TypeScript 的显式 `this` 参数只向类型检查器描述接收者，不会增加运行时实参。

函数装饰器模式指用包装器增加调用策略；它与 JavaScript 或 TypeScript 的 decorator syntax（装饰器语法）不同；语法可用的位置与行为取决于采用的语言模式，见末尾的装饰器章节。

单次调用包装器保存一个布尔绑定。应在调用目标函数前置位，因此第一次调用即使抛错也会消耗机会。后续调用返回 `undefined`；第一次的结果或异常原样传递。

~~~javascript
function once(fn) {
  "use strict";
  let called = false;
  return function (...args) {
    if (called) return undefined;
    called = true;
    return fn.apply(this, args);
  };
}

let calls = 0;
const onlyOnce = once(function (a, b, c) {
  calls += 1;
  return a + b + c;
});

onlyOnce(1, 2, 3); // 6
onlyOnce(2, 3, 6); // undefined
calls;             // 1
~~~

若首次调用抛错，标志已经置位，因此下次不会重试目标函数；首次返回的 Promise 后来拒绝也不会重置这个标志。这种策略不同于“只允许一次成功调用”；包装可能失败的操作时应明确选择。

~~~javascript
let attempts = 0;
const failOnce = once(function () {
  attempts += 1;
  throw new Error("failed");
});

try { failOnce(); } catch (error) { error.message; } // "failed"
failOnce(); // undefined
attempts;   // 1
~~~

### 记忆化在调用前增加缓存键策略

memoization（记忆化）会缓存结果，命中时跳过原函数调用。因此必须确认相同缓存键能复用同一个结果，而且跳过原调用的副作用是允许的；读取随时间变化的状态通常还需要失效策略。判断是否命中要检查键是否存在，而不是缓存值是否为真：`0`、`false`、`undefined` 都可能是有效结果。

`LeetCode 2623` 只接受有限整数实参：`sum(a, b)` 中 `0 ≤ a, b ≤ 10^5`，`fib(n)` 和 `factorial(n)` 中 `1 ≤ n ≤ 10`。因此该题可将有序整数实参元组序列化为键；这不是任意 JavaScript number 元组的通用编码。`Map.has` 可以区分键不存在和缓存值为 `undefined`。下例只将实参放入缓存键，因此只适用于结果不依赖 `this` 的这些函数；缓存未命中时仍转发 `this`，并不意味着缓存键也包含它。

~~~javascript
function memoizeNumeric(fn) {
  "use strict";
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}

let evaluations = 0;
const add = memoizeNumeric(function (a, b) {
  evaluations += 1;
  return a + b;
});

[add(2, 2), add(2, 2), add(1, 2), evaluations];
// [4, 4, 3, 2]
~~~

序列化元组保留实参顺序，因此 `[2, 3]` 和 `[3, 2]` 是不同键，即使函数返回相同结果。把这种键推广到任意 JavaScript 值时会遇到碰撞：`[NaN]` 与 `[Infinity]` 都会序列化为 `"[null]"`，`[-0]` 会序列化为 `"[0]"`；`[undefined]` 与 `[null]` 也都会序列化为 `"[null]"`。对象身份会丢失；依赖接收者的函数没有把 `this` 放入键；循环输入会在序列化时抛错。通用记忆化必须先定义实参、接收者身份、可变输入和失败结果的处理方式，再决定缓存结构。

这个实现先调用 `fn`，再写缓存。若 `fn` 同步抛错，`cache.set` 不执行，下次同键调用仍会重试；若它返回 Promise，Promise 对象会立即入缓存，后续同键调用共享这个对象，即使它后来拒绝也不会自动清除。要把它用于异步请求，必须另外决定拒绝结果是否保留，以及何时过期或重试。

只包装 `fib` 外层调用，不会缓存原始 `fib` 函数内部直接发起的递归调用。要缓存每个子问题，递归调用也必须经过记忆化函数或共享内部缓存。

**相关机制：** [函数 `this` 与绑定](#34.%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E7%94%B1%E4%BB%80%E4%B9%88%E5%86%B3%E5%AE%9A%EF%BC%9F) 解释包装器为什么用 `apply` 保留接收者；[作用域与闭包](#32.%20JavaScript%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E7%8A%B6%E6%80%81%EF%BC%9F) 解释 `once` 和记忆化保留的状态；[Map 与 Set](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F) 说明缓存键相等性和存在性；[TypeScript 装饰器](#48.%20%E9%A1%B9%E7%9B%AE%E4%BD%BF%E7%94%A8%E5%93%AA%E7%A7%8D%20TypeScript%20%E8%A3%85%E9%A5%B0%E5%99%A8%E6%A8%A1%E5%BC%8F%EF%BC%9F) 讲解装饰器语法。


> [!info]- 来源
> - 函数闭包和 length 属性：[ECMAScript Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)（§10.2）、[Function length](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function-instances-length)（§20.2.4.1）。
> - 包装器转发接收者及参数：[ECMAScript Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply)；缓存键示例中的存在检查和序列化：[Map.prototype.has](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map.prototype.has)（§24.1.3.9）、[JSON.stringify](https://tc39.es/ecma262/2026/multipage/structured-data.html#sec-json.stringify)（§25.5.4）。
> - 计时示例的 API：[W3C High Resolution Time performance.now](https://www.w3.org/TR/hr-time-3/#dom-performance-now)；TypeScript 显式 this 参数：[TypeScript Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)。
> - 特定题目输入契约和作者解法仍保留在 [Memoize](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2623.%20Memoize.md)、[Function Composition](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2629.%20Function%20Composition.md)、[Allow One Function Call](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2666.%20Allow%20One%20Function%20Call.md) 和 [Return Length of Arguments Passed](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2703.%20Return%20Length%20of%20Arguments%20Passed.md)。
## 38. 弱集合与弱引用能保证什么？

报表页面关闭后，某个记录对象只应由仍在使用它的界面持有。`WeakMap`（弱映射）可以把元数据关联到对象，而不单独延长键的生命周期；`WeakRef`（弱引用）和 `FinalizationRegistry`（最终化注册表）也不能提供及时、必达的清理保证。本章先界定“弱持有”，再说明它适合与不适合承担的责任。常规 `Map`（映射）的强引用与身份键见[何时使用 Map、Set 或普通对象？](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

本章的对象身份示例是两条同业务 id 的输入：

~~~javascript
const first = { reportId: "r-104", amount: 0 };
const retry = { reportId: "r-104", amount: 120 };
~~~

### WeakMap 关联数据，但不拥有键

`WeakMap`（弱映射）把可弱持有的键与值关联起来。只要键仍从程序其他强引用路径可达，就能读取对应值；当键不再存活时，条目本身不会保住它。`WeakMap` 不提供 `size`、键枚举或 `forEach`，因为这些接口会让程序观察到不确定的回收时点。

对象是最常见的键。ECMAScript 2023 起，非注册 `Symbol`（符号）也可作为弱键；`Symbol.for` 创建的注册 `Symbol` 不能弱持有。

~~~javascript
const rowMetadata = new WeakMap();

rowMetadata.set(first, { selected: true, row: first });
rowMetadata.get(first); // { selected: true, row: first }
rowMetadata.has(retry); // false：键是另一个对象身份

const privateKey = Symbol("row metadata");
rowMetadata.set(privateKey, { source: "non-registered symbol" });

const sharedKey = Symbol.for("shared");
rowMetadata.has(sharedKey); // false
// rowMetadata.set(sharedKey, {}); // TypeError
~~~

`WeakMap` 条目只在键对象仍存活时提供关联值；即使值反向引用键，这条弱键关联也不会单独保住键。上例的 `rowMetadata` 若还有另一个强引用路径指向 `first`，键和其值仍可读；若其他路径都断开，条目本身不会使两者继续存活。不要把这条规则误解为“只要用 `WeakMap`，相关对象就一定能回收”。

适合 `WeakMap` 的情况是给其他代码所有的节点或类实例保存私有元数据；对象生命周期由外部所有者决定，元数据不需要独立枚举。若需要列出、计数或明确删除所有缓存项，普通 `Map` 加显式清理更合适。

### WeakSet 只跟踪可弱持有的成员

`WeakSet`（弱集合）按身份弱跟踪对象或非注册 `Symbol`，提供 `add`、`has`、`delete`，但没有遍历和 `size`。它适合标记由其他部分拥有的对象是否已经处理过：

~~~javascript
const processedRows = new WeakSet();

function processOnce(row) {
  if (processedRows.has(row)) return;
  processedRows.add(row);
  // 对这个对象身份执行一次处理
}

processOnce(first);
processedRows.has(first); // true
processedRows.has(retry); // false
~~~

这里按对象身份区分记录，不按 `reportId` 或字段内容去重。需要按业务 id 去重时应使用普通 `Map` 或 `Set`，并选择明确的键。

### WeakRef 和 FinalizationRegistry 不提供释放时限

`WeakRef`（弱引用）的目标可以是对象或非注册 `Symbol`（符号）。`deref()` 在目标仍可用时返回该目标，否则返回 `undefined`。成功取到目标后，规范要求该目标在当前 ECMAScript 代码执行完成前不被回收，因此同一次执行内可先检查再使用；之后是否仍存活不受保证。

~~~javascript
const weakRow = new WeakRef(first);
const row = weakRow.deref();

if (row !== undefined) {
  rowMetadata.set(row, { selected: true });
}

const weakSymbolTarget = Symbol("weak reference target");
new WeakRef(weakSymbolTarget).deref() === weakSymbolTarget; // true：非注册 Symbol 也可作为目标
~~~

`FinalizationRegistry`（最终化注册表）可在目标不可达后请求运行清理回调，但对象何时回收、回调何时运行都没有保证；回调可能延迟很久，程序退出前也可能永不运行。只要注册仍有效，注册表就强持有 `heldValue`；调用 `unregister(token)` 可以提前移除对应注册。目标本身不能直接作为 `heldValue`（会抛 `TypeError`）；若 `heldValue` 间接引用目标，这条强路径会使目标继续存活，回调也就无法因它不可达而运行。

~~~javascript
const registry = new FinalizationRegistry(label => {
  console.log("eventual cleanup hint:", label);
});

let temporaryRow = { reportId: "temporary" };
const unregisterToken = {};
registry.register(temporaryRow, "temporary row", unregisterToken);
// registry.register(temporaryRow, temporaryRow); // TypeError
// registry.register(temporaryRow, { row: temporaryRow }); // 注册合法，但 heldValue 会保住目标
temporaryRow = null;
registry.unregister(unregisterToken); // 可显式取消这条注册
~~~

因此，这些 API 适合不影响正确性的缓存提示、附加元数据或机会式清理；不适合释放文件、网络连接、锁、计费记录、UI 状态或任何要求及时发生的动作。需要确定结束时间时，由明确的所有者调用 `dispose`、`removeEventListener`、`clearInterval` 或对应的清理函数。

对象仍被保留时，应找出强引用链，而不是等待最终化。堆保留路径的诊断见[对象为什么在不再有用后仍留在内存中？](#39.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E4%B8%BA%E4%BD%95%E4%BC%9A%E5%9C%A8%E4%B8%8D%E5%86%8D%E6%9C%89%E7%94%A8%E5%90%8E%E4%BB%8D%E7%95%99%E5%9C%A8%E5%86%85%E5%AD%98%E4%B8%AD%EF%BC%9F)。

> [!info]- 来源
> - WeakMap / WeakSet 的键资格、弱键值关系和不可枚举约束：[ECMAScript 2026 §24.3–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - WeakRef 目标和构造：[ECMAScript 2026 §26.1.1.1](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref-target)；`deref()` 保活当前代码执行：[§26.1.3.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref.prototype.deref)。
> - FinalizationRegistry 注册目标、heldValue 和取消注册：[ECMAScript 2026 `FinalizationRegistry.prototype.register`](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry.prototype.register)；对象与注册表清理模型：[§26.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry-objects)、[§9.9](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 运行时实际核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06；核对目标构造、键资格和同步 `deref()` 行为，不以一次运行推断最终化时序。
## 39. JavaScript 对象为何会在不再有用后仍留在内存中？

用户关闭报表后，如果旧结果还被全局事件处理器、计时器闭包或缓存引用，垃圾回收器仍能从程序根沿引用链找到它们。判断“业务上已过期”并不能让对象自动回收；需要断开不再需要的强引用。本章从报表监听器的保留路径解释原因，再给出诊断步骤。弱引用的语言保证见[弱集合与弱引用能保证什么？](#38.%20%E5%BC%B1%E9%9B%86%E5%90%88%E4%B8%8E%E5%BC%B1%E5%BC%95%E7%94%A8%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 可达性是保留问题，不是对象之间是否成环

JavaScript 语言不规定某一种垃圾回收算法，也不承诺某个不可达对象何时被回收。以追踪式回收器为例，它从全局对象、活动执行状态等运行时根出发，沿强引用标记对象；循环引用本身不妨碍回收，仍可从根到达的对象则需要保留。V8 的 Orinoco 是一个具体实现，使用分代、并行、增量和并发工作；这些实现细节会变化，不构成 JavaScript 语言保证。这个模型帮助理解保留路径，但具体算法与时机由引擎决定。

下面的打开函数在报表打开期间创建 `rows`。若关闭报表时漏掉监听器清理，`window` 仍持有处理器，处理器闭包又持有 `rows` 和嵌套记录：

~~~javascript
function openReport(target) {
  const owner = { id: "u-17", name: "Ada" };
  const first = { reportId: "r-104", amount: 0, owner };
  const rows = [first];

  function render(currentRows) {
    console.log(currentRows.map(row => `${row.reportId}:${row.owner.name}`).join(", "));
  }

  function onResize() {
    render(rows);
  }

  target.addEventListener("resize", onResize);
  return () => target.removeEventListener("resize", onResize);
}

let releaseReport = openReport(window);
// 关闭报表时既移除监听器，也放弃持有清理闭包：
releaseReport();
releaseReport = null;
~~~

~~~mermaid
flowchart LR
  Window[window 根] --> Listener[resize 监听器]
  Listener --> Resize[onResize 闭包]
  Runtime[执行环境根] --> Handle[releaseReport 绑定]
  Handle --> Cleanup[清理闭包]
  Cleanup --> Resize
  Resize --> Rows[rows 数组]
  Rows --> Row[报表记录对象]
  Row --> Owner[嵌套 owner 对象]
~~~

图中记录已经不在当前界面，却仍沿 `window` → Listener → `onResize` → rows → Row 可达；`releaseReport` 绑定还经清理闭包指向同一个 `onResize`。调用清理函数只移除 `window` 的监听器路径，随后还要放弃持有清理闭包的绑定；其他引用仍需由各自所有者解除。

常见保留路径还包括：

- timeout、interval、订阅或未结束任务仍持有回调；回调闭包保留旧报表。
- 应用级 Map 缓存未删除条目，强持有键及关联值。
- 脱离 DOM 树且仍能从根到达的节点仍会被保留；仅有节点和自身监听器之间的引用环不足以证明泄漏。
- 调试器控制台、断点或堆分析工具暂时保留对象。

这些只是检查线索，必须沿实际对象的保留链确认，不能只凭“用了闭包”或“数组很大”就认定泄漏。

### 用重复操作和堆快照定位所有者

在浏览器中固定一组操作，例如打开报表、切换筛选、关闭报表，再重复数次。分别记录操作前后的 heap snapshot（堆快照），用比较视图查找反复留下的对象，再检查选中对象的 retainers（保留者）和到根的路径。

若路径来自 `window` 上的监听器，应由注册监听器的报表生命周期调用 `removeEventListener`；若来自应用缓存，则由缓存所有者删除条目；若来自定时器，创建它的生命周期应在关闭时调用 `clearInterval` 或 `clearTimeout`。清理点要与资源的真实所有权一致，而不是把 `FinalizationRegistry`（最终化注册表）当成释放按钮。

Chrome DevTools 堆快照可以显示对象到根的保留者，比较视图可检查打开再关闭是否持续留下对象。Node.js 也能生成 V8 堆快照检查服务端对象；两种工具呈现的细节是运行时诊断能力，不是 ECMAScript 语义。

> [!info]- 来源
> - 追踪式回收、根集合和不可达对象的实现示例：[V8 “Trash talk: the Orinoco garbage collector”](https://v8.dev/blog/trash-talk)，2018-08-14；这是当时的 V8 实现说明，不代表当前所有引擎。
> - `WeakRef` 与 `FinalizationRegistry` 不保证回收和清理时机：[ECMAScript 2026 §9.9 Processing Model](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 比较堆快照、检查保留者和脱离 DOM 节点：[Chrome DevTools 官方指南 “Record heap snapshots”](https://developer.chrome.com/docs/devtools/memory-problems/heap-snapshots)，访问于 2026-11-06。
## 40. 回调、Promise 与 async 函数怎样组合异步工作？

### 案例背景

用户打开 `reportId="42"` 的报表，再把排序切到 `recent`。页面通过 Fetch API 经 HTTP（超文本传输协议）分别请求报表、摘要和访问权限；三项彼此独立，可以同时发出。本例接口以 JSON 返回数据；Fetch 先给出 `Response` 响应对象，正文还需另行读取。三份响应都成功、正文都能解析，并通过各自的运行时校验后，界面才收到一组可信数据。只有权限允许查看明细时，页面才继续读取行。用户离开页面时，页面持有的 `AbortController`（中止控制器）可以通过 `AbortSignal`（中止信号）通知支持取消的工作停止。

这条过程有几个不同边界：callback（回调）描述“之后要调用的函数”；Promise 表示将来成功值或失败原因；异步函数与等待运算符（`async`/`await`）写出等待与错误传播；宿主决定异步回调何时有机会运行；取消则由具体 API 的中止信号等机制处理。把 Promise 放进组合器不会自动启动限额调度或停止其他工作。

三次 `fetch()` 调用先启动三项请求。`Promise.all` 等待三份 `Response`，代码随后才检查 HTTP 状态；某项较早返回 404，也要等另外两份响应到达，才会在这份实现中被检查出来。

![同一组报表参数与 signal 启动三个 Fetch；等待三份 Response，再检查 HTTP 状态](../../frontend/javascript/resources/report-promise-pipeline.svg)

上图的成功出口只是三份 HTTP 状态可接受的响应，正文还没有被代码读完。接下来同时读取三份 JSON，再等待它们全部解析完成，最后运行同步校验器。只有这两道等待及校验都通过，`loadReport` 才交付数据；任一阶段失败都会拒绝它返回的 Promise。组合器本身不会取消其他已启动的工作。

![三份响应分别读取 JSON，全部解析完成后逐项校验，交付报表摘要和权限，权限决定是否续读行](../../frontend/javascript/resources/report-promise-results.svg)

第二张图沿用同一 `reportId`、`sort` 和页面 signal。若权限允许且行页码已知，下一步可交给[并发池按上限启动任务](#41.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%B9%B6%E5%8F%91%E5%B9%B6%E6%94%B6%E5%B0%BE%E5%A4%B1%E8%B4%A5%EF%BC%9F)；如果下一页要等前页给出 cursor（游标），就按页顺序推进，见[报表行怎样按页异步读取？](#%E6%8A%A5%E8%A1%A8%E8%A1%8C%E6%80%8E%E6%A0%B7%E6%8C%89%E9%A1%B5%E5%BC%82%E6%AD%A5%E8%AF%BB%E5%8F%96%EF%BC%9F)。Promise 只传递结果和失败，不会替页面完成结构校验、权限判断、限流或取消。

### 回调如何表示延后的工作？

callback（回调）是作为参数交给另一段代码、由那段代码决定何时调用的函数。回调不一定异步：`array.map(fn)` 会在当前调用中同步调用 `fn`，Fetch 的完成处理器则稍后运行。若每一步要等上一步的值，嵌套回调会把成功路径、失败路径和后续动作散落在多层函数中：

~~~javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
~~~

Promise 把“未来的一个值或失败原因”作为可传递的对象。它从待定（`pending`）转为履行（`fulfilled`）或拒绝（`rejected`）之一；状态只改变一次。Promise 不持有一条通用的取消命令，也不意味着底层工作在另一个线程运行。

`new Promise(executor)` 会在构造时同步调用执行器；执行器若同步抛错，构造所得 Promise 会以该异常拒绝。`resolve` 与 `reject` 用来报告结果，但后续 `.then()` 注册的处理器不会在注册它的那段同步代码中内联运行。下面先输出“执行器”、再输出“构造完成”；计时器调用 `resolve` 后，Promise 处理器才有机会输出结果：

~~~javascript
const response = new Promise(resolve => {
  console.log("执行器");
  setTimeout(() => resolve("报表响应已到"), 20);
});

console.log("构造完成");
response.then(value => console.log(value));
~~~

这段程序先输出 `执行器`、`构造完成`。计时器的 20 毫秒是最早等待时间，不保证回调恰在该时刻运行；计时器属于宿主 API。在浏览器中，Promise 处理器（reaction）和 `await` 的续段会作为microtask（微任务）排队；当前 JavaScript 调用栈清空后，浏览器执行微任务检查点，把队列中的微任务逐个跑完，再继续事件循环的后续步骤。于是 `await` 先让出当前同步片段，而续段会在后续微任务中继续。绘制机会与其他任务（task）的交错由宿主决定，见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)和 [Node.js 事件循环阶段与微任务队列如何交互？](../../engineering-foundations/backend/node-event-loop-and-microtasks.md)。

### Promise 链怎样传递值和失败？

每次调用 `.then()` 都返回一个新 Promise。成功处理器返回普通值时，新 Promise 以该值履行；它抛出异常时，新 Promise 以该异常拒绝；若它返回 Promise，新 Promise 会采用该 Promise；若返回普通对象且它的 `then` 属性是函数（thenable），新 Promise 会调用这个 `then`，根据它调用的解析或拒绝回调决定结果。内建 Promise 同样有 `then` 方法，但 `Promise.resolve(p)` 遇到确为 Promise 且读到 `p.constructor === Promise` 的 `p` 时会直接返回它；普通 thenable 的getter（取值器）和采用作业不应套用到这条捷径上。`.catch(handler)` 等价于只提供拒绝处理器的 `.then(undefined, handler)`：处理器返回普通值或最终履行的 Promise/thenable，后续链才恢复成功。

~~~javascript
function parseReport(response) {
  if (!response.ok) throw new Error("报表响应 HTTP " + response.status);
  return response.json();
}

fetch("/api/reports/42?sort=recent")
  .then(parseReport)
  .then(validateReport)
  .then(renderReport)
  .catch(showRequestFailure);
~~~

若 `parseReport`、`validateReport` 或 `renderReport` 同步抛错，或 `response.json()` 返回的 Promise 拒绝，拒绝会沿后续链传播，直到某一层接手。处理器返回错误提示文案会把链恢复为成功；若界面层需要保留“请求失败”状态，就应返回或抛出符合该状态契约的结果。哪个层拥有足够上下文来恢复或上报，见[JavaScript 错误应在哪一层恢复、传播或上报？](#44.%20JavaScript%20%E9%94%99%E8%AF%AF%E5%BA%94%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%81%A2%E5%A4%8D%E3%80%81%E4%BC%A0%E6%92%AD%E6%88%96%E4%B8%8A%E6%8A%A5%EF%BC%9F)。

`.finally(cleanup)` 在履行或拒绝时都会运行，不接收原来的值或原因。回调返回的普通成功值会被忽略；清理成功则原值或原拒绝继续传递。若清理抛错或返回最终拒绝的 Promise / thenable，清理失败取代原结果。可让 `finally` 等待异步清理，但不要用其返回值改写业务结果。

异步函数（`async function`）调用时立即执行函数体，直到遇到第一个等待运算符（`await`）或结束；即使被等待的值已经可用，续行也不会在当前语句段内同步接着执行。调用总会返回 Promise。`await` 会让当前异步函数暂停并把控制权还给调用者，等被等待的值履行后再继续；若它拒绝，拒绝会像该处抛错一样进入 `try/catch` 或向外传播。`try` 的 `finally` 会在正常返回或抛错时运行；其中新的 `return` 或 `throw` 可以替换原先的完成结果。

~~~javascript
async function loadUserAndOrders(userId) {
  const user = await getUser(userId);
  const orders = await getOrders(user.id);
  return { user, orders };
}

loadUserAndOrders("u-42")
  .then(({ orders }) => renderOrders(orders))
  .catch(showRequestFailure);
~~~

这里第二个请求要用第一个请求给出的 `user.id`，所以顺序 `await` 是数据依赖；如果两个请求互不依赖，顺序 `await` 会白白等前一个完成，应先启动两项工作再组合。

### TypeScript 的 Promise 类型能保证什么？

`Promise<T>` 只能在编译期约束 TypeScript 代码中的类型，注解编译后不会检查服务端 JSON。把外部值先当作未知类型（`unknown`），读取正文后执行真正的运行时校验：

~~~typescript
async function parseReport(response: Response): Promise<Report> {
  if (!response.ok) {
    throw new Error("报表请求失败，HTTP " + response.status);
  }

  const value: unknown = await response.json();
  return validateReport(value);
}
~~~

`validateReport` 必须检查接口实际约束，并在数据不符时拒绝；只写 `Promise<Report>` 不会增加校验。

### 报表请求何时并发、何时顺序等待？

Fetch API（Fetch 应用程序接口）的调用会启动请求，然后返回一个 Promise。把已经启动的 Promise 交给 `Promise.all` 是等待它们的结果，不是把它们排进一个稍后启动的队列。独立请求可以先同时发出：

~~~javascript
async function loadReport(reportId, sort, signal) {
  const paths = [
    "/api/reports/" + encodeURIComponent(reportId) +
      "?sort=" + encodeURIComponent(sort),
    "/api/reports/" + encodeURIComponent(reportId) + "/summary",
    "/api/reports/" + encodeURIComponent(reportId) + "/permissions",
  ];

  const responses = await Promise.all(
    paths.map(path => fetch(path, { signal }))
  );

  const failed = responses.find(response => !response.ok);
  if (failed) throw new Error("HTTP " + failed.status);

  const [rawReport, rawSummary, rawPermissions] = await Promise.all(
    responses.map(response => response.json())
  );

  // 这三个校验器同步返回已校验值；无效数据时同步抛错。
  return {
    report: validateReport(rawReport),
    summary: validateSummary(rawSummary),
    permissions: validatePermissions(rawPermissions),
  };
}
~~~

`fetch()` 的 Promise 在可用的 `Response` 到达时履行；HTTP `404` 或 `500` 仍是一个响应，不会仅因状态码而拒绝。`response.ok` 只在 HTTP 状态码为 `200–299` 时为真，因此仍需显式检查。响应体由 `json()` 另行读取和解析，这一步仍可能等待，也可能因中止或无效 JSON 而拒绝。校验器再把未知的 JSON 形状变成应用接受的数据。

第一轮 `Promise.all` 等三项 Fetch Promise 全部履行才继续检查状态；任一 Fetch Promise 拒绝时，它会尽早以该原因拒绝，但不会取消其他已启动请求。三项 Response 都到达后，代码按输入顺序检查 HTTP 状态；有一项不是成功状态时立即抛错，因此不会开始读取任何正文。三项状态都成功后，第二轮才同时调用三个 `json()`，并等待三个解析 Promise 全部履行；其中一项解析拒绝时，后续同步校验都不会运行。最后三个校验器依次同步返回已校验值，或同步抛错。若把校验器改成 `async` 函数，返回对象里的字段会是 Promise；外层 `async` 函数不会递归等待普通对象的属性。

主例使用教学权限值 `{ canReadRows: true }`；校验器返回这个布尔字段后，页面在 `await loadReport` 的下一行分支。页面持有控制器，离开时发出中止信号：

~~~javascript
const controller = new AbortController();
window.addEventListener("pagehide", () => controller.abort(), { once: true });

const data = await loadReport("42", "recent", controller.signal);
if (data.permissions.canReadRows) {
  console.log("权限允许：继续读取报表行");
} else {
  console.log("权限不允许：只显示报表和摘要");
}
~~~

这里的 `canReadRows` 是合成教学字段；真实接口应按其实际权限契约定义和校验该值。前端分支只决定是否继续请求，明细 API 仍须独立验证调用者的读取权限。若它为 `true`，行读取会从这个分支开始；若为 `false`，主例停在报表与摘要。行页码已知时可把每页请求交给[并发池按上限启动任务](#41.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%B9%B6%E5%8F%91%E5%B9%B6%E6%94%B6%E5%B0%BE%E5%A4%B1%E8%B4%A5%EF%BC%9F)；下一页必须等前页给出游标（cursor）时按页顺序推进，见[报表行怎样按页异步读取？](#%E6%8A%A5%E8%A1%A8%E8%A1%8C%E6%80%8E%E6%A0%B7%E6%8C%89%E9%A1%B5%E5%BC%82%E6%AD%A5%E8%AF%BB%E5%8F%96%EF%BC%9F)。页面离开时的 `abort()` 会通知 Fetch 及其他主动监听同一中止信号的 API；它不会强行终止任意 Promise，也不能撤销服务器已执行的副作用。

页面可把同一个 `AbortSignal` 传给三项 Fetch；控制器发出 abort 后，Fetch 按自己的中止协议响应。Promise 组合器不会代替页面调用 `abort()`，也不会撤回服务器已经执行的副作用。若 Promise 被超时竞速淘汰，工作也不会因此自动停止，后文会区分“停止等待”和“取消操作”。

多项异步工作的组合条件可按结果需求选择：

| 方法 | 组合 Promise 何时结束 | 报表场景中的含义 |
| --- | --- | --- |
| `Promise.all` | 全部履行才履行；任一拒绝就拒绝 | 报表、摘要和权限都必需；结果数组按输入顺序排列 |
| `Promise.allSettled` | 所有输入都结束后履行每项状态和值或原因 | 需要展示每个独立小部件的成功或失败 |
| `Promise.any` | 首个履行就履行；全部拒绝才以聚合错误（`AggregateError`）拒绝 | 多个镜像或备选端点中任一成功即可 |
| `Promise.race` | 首个履行或拒绝决定结果 | 观察任务与计时器谁先结束；组合结果不会取消没赢的工作 |

这些方法都消费同步 iterable（可迭代对象）。对空可迭代对象，`all([])` 与 `allSettled([])` 履行 `[]`；`any([])` 以空 `errors` 的聚合错误（`AggregateError`）拒绝；`race([])` 永远待定（pending）。若调用时输入是已启动的请求，任何组合器都不能限流。若需要在有槽位时才调用请求，必须把任务工厂交给[异步并发池](#41.%20%E6%80%8E%E6%A0%B7%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%B9%B6%E5%8F%91%E5%B9%B6%E6%94%B6%E5%B0%BE%E5%A4%B1%E8%B4%A5%EF%BC%9F)。

#### 两个 Promise 结果怎样相加？

> [!example] 完成顺序不改结果位置
> 假设请求 A 在 20 ms 后履行 `2`，请求 B 在 60 ms 后履行 `5`。A 先完成，但 `Promise.all([A, B])` 最终给出 `[2, 5]`，再相加得到 `7`。
>
> 如果 A 在 50 ms 后履行 `10`，B 在 30 ms 后履行 `-12`，结果仍是 `[10, -12]`，相加为 `-2`。若任一项拒绝，`Promise.all` 拒绝；另一项仍可能继续并产生副作用。

#### 组合器如何保留输入顺序？

先看 `Promise.resolve` 怎样采用普通 thenable。读取 `then` getter 是同步步骤；调用取得的 `then` 函数则安排为后续 Promise 作业，因此这两个动作不在同一时刻发生：

~~~javascript
const events = [];
const thenable = {
  get then() {
    events.push("读取 then");
    return resolve => {
      events.push("调用 then");
      resolve("摘要已到");
    };
  },
};

Promise.resolve(thenable).then(value => events.push(value));
events.push("当前同步代码结束");
// 立即：["读取 then", "当前同步代码结束"]
// 随后：再依次追加 "调用 then"、"摘要已到"
~~~

原生组合方法接收可迭代值，并对每项执行 Promise 解析与结果登记。即使第二项先结束，它的处理器也写入第二个位置；所以数组顺序取决于输入，不取决于完成先后。下面的折叠实现用于观察这套最小机制，不是可替代原生 Promise 的兼容性填充（polyfill）：它假设普通内建 `Promise`，不模拟子类构造器、`Symbol.species` 或所有恶意 thenable 的防护。

> [!example]- 完整教学实现：四个 Promise 组合器
>
> ~~~javascript
> function allTeaching(iterable) {
>   return new Promise((resolve, reject) => {
>     const values = [];
>     let remaining = 1; // 哨兵：同步遍历还没有结束
>     let index = 0;
>
>     for (const item of iterable) {
>       const current = index++;
>       remaining++;
>       Promise.resolve(item).then(value => {
>         values[current] = value;
>         if (--remaining === 0) resolve(values);
>       }, reject);
>     }
>
>     if (--remaining === 0) resolve(values);
>   });
> }
>
> function allSettledTeaching(iterable) {
>   return new Promise(resolve => {
>     const results = [];
>     let remaining = 1;
>     let index = 0;
>
>     for (const item of iterable) {
>       const current = index++;
>       remaining++;
>       Promise.resolve(item).then(
>         value => {
>           results[current] = { status: "fulfilled", value };
>           if (--remaining === 0) resolve(results);
>         },
>         reason => {
>           results[current] = { status: "rejected", reason };
>           if (--remaining === 0) resolve(results);
>         }
>       );
>     }
>
>     if (--remaining === 0) resolve(results);
>   });
> }
>
> function anyTeaching(iterable) {
>   return new Promise((resolve, reject) => {
>     const errors = [];
>     let remaining = 1;
>     let index = 0;
>
>     for (const item of iterable) {
>       const current = index++;
>       remaining++;
>       Promise.resolve(item).then(
>         resolve,
>         reason => {
>           errors[current] = reason;
>           if (--remaining === 0) {
>             reject(new AggregateError(errors, "没有输入履行"));
>           }
>         }
>       );
>     }
>
>     if (--remaining === 0) {
>       reject(new AggregateError(errors, "没有输入履行"));
>     }
>   });
> }
>
> function raceTeaching(iterable) {
>   return new Promise((resolve, reject) => {
>     for (const item of iterable) {
>       Promise.resolve(item).then(resolve, reject);
>     }
>     // 空输入没有可决定胜负的项，输出保持 pending。
>   });
> }
> ~~~
>
> `remaining` 从 `1` 开始，把“同步遍历还在进行”也计作一个未完成项。以两项 `all` 为例，计数经历 `1 → 2 → 3`；遍历完先减掉哨兵成为 `2`；两个处理器再各减一次，归零时履行。空输入则 `1 → 0`，此时组合 Promise 已履行 `[]`，但后来附加的 `.then()` 仍会稍后运行。`any` 用同一哨兵等待所有拒绝，并按输入位置登记原因。
>
> 同步遍历可能执行输入对象上的代码。如果已经成功取出一项值，但处理这一项时发生同步异常，例如已有 Promise 的 `constructor` getter（取值器）抛错，组合 Promise 会拒绝，并尝试通过尚未结束的迭代器所提供的可选 `return()` 方法进行关闭。普通 thenable 对象需要被采用时，`Promise.resolve(thenable)` 会在当前调用读取它的 `then` 取值器；取值器抛错会变成该项的拒绝 Promise，所以组合器仍继续读取后续项。取出的 `then` 函数稍后通过 Promise 作业调用，之后的异步拒绝同样不会中止同步遍历。内建 Promise 也有 `then`，但 `Promise.resolve(p)` 对确为 Promise 且读到 `p.constructor === Promise` 的 `p` 有直接返回的捷径；组合器随后仍会在同步遍历中读取并调用输入的 `p.then`。若 `iterator.next()` 自己抛错，或读取迭代结果的 `done` / `value` 时抛错，规范会将迭代记录标记为完成；组合 Promise 拒绝，但不再调用该迭代器的 `return()`。

### 定时器和超时究竟能取消什么？

Promise 没有通用取消操作。`Promise.race` 只决定调用方先观察到哪个结果：超时先拒绝时，底层工作仍可能继续。定时器延迟到期只是回调获得运行机会的门槛；当前 JavaScript 不会被它打断，回调也可能更晚运行。

#### 怎样把定时器延迟包装成 Promise？

~~~javascript
function sleep(millis) {
  return new Promise(resolve => setTimeout(resolve, millis));
}

const start = Date.now();
sleep(100).then(() => console.log(Date.now() - start)); // 约 100 ms 或更久
~~~

这段 `sleep` 只等待一个宿主计时器，不会阻塞当前线程。浏览器与 Node.js 的定时器接口由各自宿主定义；零延时或短延时都不承诺实时执行。浏览器的 `setTimeout` / `setInterval` 返回数值 ID，Node.js 返回 `Timeout` 对象；TypeScript 中对应的声明取决于项目选择的宿主类型。

#### 怎样让异步操作与计时器竞速？

~~~javascript
function timeLimit(fn, millis) {
  // 在 ES module 或 strict mode 中定义，调用时的 this 才原样传递。
  return function (...args) {
    let timerId;
    const timeout = new Promise((_, reject) => {
      timerId = setTimeout(
        () => reject(new Error("Time Limit Exceeded")),
        millis
      );
    });

    let work;
    try {
      work = Promise.resolve(fn.apply(this, args));
    } catch (error) {
      work = Promise.reject(error);
    }

    return Promise.race([work, timeout])
      .finally(() => clearTimeout(timerId));
  };
}
~~~

包装器用普通函数保留调用时的 `this`，并把 `fn` 同步抛出的异常转成拒绝。工作先结束时，`finally` 清除仍待运行的计时器。只有超时回调实际得到调度时，竞速才会以超时拒绝包装 Promise；`fn` 仍可能完成。计时器到期不能抢占当前 JavaScript，包装器也不会停止工作。

> [!info] TypeScript 的 this 参数不改变运行时调用
> 可以用显式 this 参数保留包装函数的调用类型；它会在编译时擦除，不是实际传入的第一个参数。运行时仍要用普通 function 接住调用上下文，并像本例一样以 fn.apply(this, args) 调用原函数；箭头函数捕获外层 this，不适合此处。
>
> ~~~typescript
> type TimedFunction<This, Args extends unknown[], Result> =
>   (this: This, ...args: Args) => Promise<Result>;
> ~~~


> [!example] 50 ms 的等待上限不等于 50 ms 后强行中断
> 假设请求要 100 ms 才完成，`timeLimit(request, 50)` 会在超时回调得到调度后拒绝调用方，底层请求仍可能继续。若限制改为 150 ms，工作可以先成功返回。若函数等待 120 ms 后返回两参数之和，`timeLimit(fn, 150)(5, 10)` 在理想调度下得到 `15`；若函数同步抛错，拒绝直接传播且清除计时器，无须等满预算。
>
> 若 `fn` 同步占用 80 ms 后才返回一个已履行的 Promise，计时器无法在这段同步工作中抢占 JavaScript。同步代码让出后，Promise reaction 可先于到期的计时器任务运行，故这个运行可能成功；50 ms 不是硬实时截止线。

若操作支持取消，应使用它公开的取消契约。例如 Fetch 接收 `AbortSignal`，页面在不再需要请求时可调用对应控制器的 `abort()`。这个 signal 让 Fetch 及其他主动监听它的 API 有机会停止工作；任意 Promise 和任意同步函数不会因此强制终止。它也不能撤销服务端已经收到并执行的写入。

#### 取消一次或重复定时器时，哪些调用还会发生？

一次性计时器可把它的 ID 暴露给取消函数：

~~~javascript
function cancellable(fn, args, millis) {
  const timerId = setTimeout(() => fn(...args), millis);
  return () => clearTimeout(timerId);
}
~~~

| 输入 | 预期调用 | 原因 |
| --- | --- | --- |
| `fn(x)=x*5`，`args=[2]`，`t=20`，`cancelT=50` | 约 20 ms 调用一次，结果为 `10` | 回调先开始，后续取消不能撤回它 |
| `fn(x)=x²`，`args=[2]`，`t=100`，`cancelT=50` | 不调用 | 取消时回调仍在等待 |
| `fn(x,y)=x*y`，`args=[2,4]`，`t=30`，`cancelT=100` | 约 30 ms 调用一次，结果为 `8` | 回调在取消前已完成 |

这些毫秒是题目输入，不是精确计时保证。取消只能清掉仍待执行的回调；它不打断已开始运行的函数，也不把函数结果交给 `cancellable` 的调用者。若 `fn` 依赖 `this`，需显式传接收者（receiver）或先绑定。

原练习要求重复计时器立即调用一次，再按给定间隔安排后续调用：

~~~javascript
function cancellableInterval(fn, args, millis) {
  fn(...args); // 第一次同步调用
  const intervalId = setInterval(() => fn(...args), millis);
  return () => clearInterval(intervalId);
}
~~~

| 输入 | 理想化调用时刻 | 每次函数结果 |
| --- | --- | --- |
| `fn(x)=2*x`，`args=[4]`，`t=35`，`cancelT=190` | `0, 35, 70, 105, 140, 175 ms` | 每次 `8` |
| `fn(x,y)=x*y`，`args=[2,5]`，`t=30`，`cancelT=165` | `0, 30, 60, 90, 120, 150 ms` | 每次 `10` |
| `fn(x,y,z)=x+y+z`，`args=[5,1,3]`，`t=50`，`cancelT=180` | `0, 50, 100, 150 ms` | 每次 `9` |

`setInterval` 不等待 Promise 返回值。若 `fn` 是异步函数、一次执行比间隔更长，下一次调用仍可开始，多个调用可能重叠；`clearInterval` 只阻止后续计时器回调，不会取消已经启动的 Promise 工作。错误恢复和重叠策略必须由调用方另行定义。

### Promise 处理器为什么会交错？

要推导顺序，先区分“注册处理器”与“把处理器作业入队”。同步代码给已履行 Promise 调用 `.then` 时，规范会立即为处理器入队；给待定 Promise 调用 `.then` 时，先保存 reaction（反应记录），等 Promise 状态改变才入队。作业运行后若履行下游 Promise，也会把已保存的下游 reaction 排入队列尾部。浏览器将 Promise 处理器作业（Promise reaction job）放入微任务队列，在微任务检查点按入队顺序逐个处理；Node.js 另有宿主调度边界。以下第一组的两个源 Promise 已履行，所以同步代码先排好 `0` 和 `2`；执行 `0` 才使下游处理器 `1` 入队，队列中已有 `2`，因此输出为 `0, 2, 1, 3`。

~~~javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// Node.js v26.13.0 的 CommonJS 模块格式：0, 2, 1, 3
~~~

原归档练习还保留了三条链的交错以及处理器返回已履行 Promise 时的附加采用作业。先追踪第一段的关键作业，队列左侧是下一项：

| 步骤 | 动作 | 队列 |
| --- | --- | --- |
| 起始 | 两条链的首个处理器已注册在已履行 Promise 上 | `[输出 0, 输出 1]` |
| 1 | 输出 0 的处理器返回 `Promise.resolve(4)`，Promise 解析流程安排采用作业 | `[输出 1, 采用]` |
| 2 | 输出 1 的处理器运行，并使它的下游处理器入队 | `[采用, 输出 2]` |
| 3 | 采用作业调用所返回 Promise 的 `then`；该 Promise 已以 `4` 履行，于是转发值的作业入队 | `[输出 2, 转发 4]` |
| 4 | 输出 2 的处理器运行，并把输出 3 排到队尾 | `[转发 4, 输出 3]` |
| 5 | 转发作业履行第一条链的下游 Promise，输出 4 才入队 | `[输出 3, 输出 4]` |

这说明处理器运行会触发新的 Promise 状态转换和后续入队；不能只按 `.then` 的源代码注册位置排序。下列输出在 Node.js `v26.13.0` CommonJS 中逐段重放；它们展示当前例子的入队关系，不是跨宿主固定的“第几个 tick”公式。

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3))
  .then(() => console.log(5))
  .then(() => console.log(6));
// 0, 1, 2, 3, 4, 5, 6
~~~

~~~javascript
Promise.resolve().then(() => console.log(0))
  .then(() => console.log(1)).then(() => console.log(2));
Promise.resolve().then(() => console.log(3))
  .then(() => console.log(4)).then(() => console.log(5));
Promise.resolve().then(() => console.log(6))
  .then(() => console.log(7)).then(() => console.log(8));
// 0, 3, 6, 1, 4, 7, 2, 5, 8
~~~

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(1);
}).then(() => console.log(2)).then(() => console.log(3));

Promise.resolve().then(() => {
  console.log(4);
  return Promise.resolve(5);
}).then(() => console.log(6)).then(() => console.log(7));
// 0, 4, 2, 6, 3, 7
~~~

几个旧 Promise reaction 顺序练习现已合并在本节；题目原页仍可从[归档入口](../../archive/front-end/Deprecated_Interview_Notes/promise-reaction-order-exercises.md)查找。浏览器事件循环、Node.js 定时器和微任务队列分别遵循各自宿主调度；不要把某个 Node 输出顺序直接推成浏览器计时器、绘制和 Promise 的固定先后。

> [!info]- 来源
> - **Promise 状态、链式传值、thenable 采用、组合器与 `async` 函数。** [ECMAScript 2027 草案（2026-11-08）](https://tc39.es/ecma262/)，核对日期：2026-11-12；异步函数在 §15.8，迭代抽象操作在 §7.4、迭代器对象在 §27.1，Promise 在 §27.5。对应 [Promise 对象](https://tc39.es/ecma262/#sec-promise-objects)、[`Promise.resolve`](https://tc39.es/ecma262/#sec-promise.resolve)、[thenable 采用作业](https://tc39.es/ecma262/#sec-newpromiseresolvethenablejob)、[`Promise.all`](https://tc39.es/ecma262/#sec-promise.all)、[`allSettled`](https://tc39.es/ecma262/#sec-promise.allsettled)、[`any`](https://tc39.es/ecma262/#sec-promise.any)、[`race`](https://tc39.es/ecma262/#sec-promise.race)、[`finally`](https://tc39.es/ecma262/#sec-promise.prototype.finally)、[PerformPromiseThen](https://tc39.es/ecma262/#sec-performpromisethen)、[TriggerPromiseReactions](https://tc39.es/ecma262/#sec-triggerpromisereactions)、[NewPromiseReactionJob](https://tc39.es/ecma262/#sec-newpromisereactionjob)、[IteratorStepValue](https://tc39.es/ecma262/#sec-iteratorstepvalue)、[IteratorClose](https://tc39.es/ecma262/#sec-iteratorclose) 与 [async function definitions](https://tc39.es/ecma262/#sec-async-function-definitions)。
> - **Promise 作业怎样进入宿主队列。** 浏览器把 Promise 作业放入微任务队列，并在微任务检查点运行它们，见 [WHATWG HTML §8.1.6.6.4 HostEnqueuePromiseJob](https://html.spec.whatwg.org/multipage/webappapis.html#hostenqueuepromisejob)、[§8.1.7 Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)、[§8.8 Microtask queuing](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#microtask-queuing) 与 [Perform a microtask checkpoint](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint)，Living Standard 更新时间：2026-11-11；Node.js v26.13.0 的 `process.nextTick()`、`queueMicrotask()` 与 Promise 微任务队列边界见 [Process 文档](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)。这些宿主规则不把某次 Node 输出推广成浏览器 task 与绘制之间的固定优先级。
> - **HTTP 响应、状态与正文读取。** [WHATWG Fetch Standard §2.2.6 Responses 与 §5.3 Body mixin](https://fetch.spec.whatwg.org/#responses)，Living Standard，核对日期：2026-11-12；[Response.ok](https://fetch.spec.whatwg.org/#dom-response-ok) 对应 200–299 状态，[Body.json()](https://fetch.spec.whatwg.org/#dom-body-json) 执行正文读取与解析。
> - **定时器。** [WHATWG HTML §8.7 Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，Living Standard，更新时间 2026-11-11，说明计时器回调的调度及不精确延迟；Node.js 定时器行为以[Node.js v26.13.0 Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html)为宿主边界。
> - **取消。** [WHATWG DOM §3 Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)，Living Standard，更新时间 2026-11-11；[WHATWG Fetch §5.5 Abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard，更新时间 2026-10-19。DOM 说明 Promise 本身没有内建中止机制，API 可选择接受并观察 `AbortSignal`。
> - **TypeScript 擦除。** [TypeScript Handbook：Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，访问日期：2026-11-12。
> - **包装函数的显式 `this` 类型。** [TypeScript Handbook：Declaring this in a Function](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)，类型参数在编译时擦除；运行时调用仍由普通函数及 `apply` 保留接收者。
## 41. 怎样限制异步任务的并发并收尾失败？

上一章的报表案例已经收到 `reportId="42"`、`sort="recent"` 的三项基础数据并通过运行时校验；权限结果 `canReadRows === true`，所以页面现在可以读取明细。五个页码事先已知，页面还持有生命周期使用的 `AbortSignal` (中止信号)。本章把上一章控制器的 `controller.signal` 简称为 `pageSignal`；页面离开时仍由 `controller.abort()` 发出信号。本例把任务池同时追踪的活动任务数限为两个。`2` 是这个案例给出的资源限制，不代表所有服务的通用最佳值。

### 先把任务保持为惰性，再填满空槽位

调用 Fetch API 的 `fetch(url)` 时，请求就开始，并返回一个 Promise。若先创建五个 Fetch Promise 再交给 `Promise.all`，五个请求已经全部启动；组合器只会等它们的结果。

要控制启动时间，把每项工作写成task factory (任务工厂)：函数被调用时才创建请求。下面 `map` 只生成五个异步函数（`async` 函数），尚未请求任何一页：

~~~javascript
function createPageTasks(reportId, sort) {
  return [1, 2, 3, 4, 5].map(page => async ({ signal }) => {
    const query = new URLSearchParams({
      page: String(page),
      sort,
    });
    const url =
      "/api/reports/" + encodeURIComponent(reportId) + "/rows?" + query;
    const response = await fetch(url, { signal });
    if (!response.ok) throw new Error("页 " + page + " 请求失败");
    return response.json();
  });
}
~~~

任务池消费同步 iterable (可迭代对象)，其中每项都必须是函数。同时最多等待两个工厂调用，并把 `{ signal, index }` 作为参数传给每个被调用的工厂；代码用 `runTask` 的 Promise 等待调用返回值结算。若工厂启动额外工作却先返回，池会释放槽位，而那项工作仍可能继续；工厂若自行启动多项并发工作，池也不会分别限流。

Fetch 收到 HTTP 非成功状态时仍会履行并给出响应对象（`Response`）；本例检查 `response.ok`，并在收到响应后立即把非 2xx 状态转换为任务拒绝，没有读取或取消那条响应正文流。于是该工厂 Promise 已结算、槽位已释放，正文流却可能仍打开。成功状态下，`response.json()` 会继续读取并解析正文，工厂 Promise 要等这一步结算才释放槽位。因此 `limit` 限制池仍在等待的任务数，不限制物理 HTTP 请求、连接或响应体流的数量。并发池接收每个工厂的最终成功值或失败原因，不负责解释 HTTP 或 JSON 契约。

下图和后面的时间线使用从五页主例缩小出的三页合成输入：页 1、2 先占槽，页 2 随后失败，页 3 等待补位。

![三项合成分页任务输入任务池：页 1 与页 2 在 t=0ms 占满两个活动槽；页 2 在 t=10ms 以 new Error("B failed") 拒绝，页 1 仍在运行，页 3 尚未启动](../../frontend/javascript/resources/bounded-pool-input-failure.svg)

图一先把输入、起始状态和失败时刻固定下来：工厂 `index` 从 0 开始；页 1 用 30 ms 得到 A，页 2 用 10 ms 以 `new Error("B failed")` 失败，页 3 启动后用 20 ms 得到 C。接着看这个 Error 如何走向两种终态：

![页 2 的 new Error("B failed") 分成 stop 与 collect 两条路径：stop 停止取项、尝试 return 一次、排空页 1 后拒绝；collect 把拒绝写入索引 1，启动页 3，并按输入位置返回 A、错误记录和 C](../../frontend/javascript/resources/bounded-pool-outcomes.svg)

页码从 1 开始，工厂索引从 0 开始；因此页 2 对应 `results[1]`。`collect` 的履行值和拒绝原因分别保存在 `value` 与 `reason` 字段，结果按输入位置排列。

调度器用 `nextIndex` 记下一个输入位置，用 `active` 集合占住运行中的槽位，并用 `peakActive` 记实际活动数的峰值。它有空槽位时持续取项并启动任务；槽位填满后，用竞速组合器（`Promise.race`）等待一项任务结算或停止通知先到。任务结算会腾出槽位，调度器再填所有可用空位。每项结果写入 `results[index]`，所以完成先后不会改变输出位置。

### 用同一条时间线推算成功、失败和继续收集

为了逐步看清失败策略，下面沿用图中的三项惰性任务工厂，`limit` 为 2。页 1 在启动 30 ms 后履行并给出 `"A"`；页 2 在 10 ms 后以 `new Error("B failed")` 拒绝；页 3 在启动 20 ms 后履行并给出 `"C"`。这些延迟是合成输入，不是网络测量。

| 时刻 | 活动状态 | `failure: "stop"` | `failure: "collect"` |
| --- | --- | --- | --- |
| `0 ms` | 页 1、页 2 启动，活动数 `2` | `peakActive = 2` | `peakActive = 2` |
| `10 ms` | 页 2 拒绝，页 1 仍在运行 | 记录首次失败、停止取项，尝试调用 `return()` 一次；页 3 不启动 | 在结果位置 `1` 记录拒绝，腾出的槽位启动页 3 |
| `30 ms` | 页 1 完成；`collect` 中页 3 也已完成 | 排空后以 `new Error("B failed")` 拒绝池调用 | 按输入位置履行 A、Error 和 C 的三项状态记录，峰值仍是 `2` |

`stop`（停止）是默认策略：首个被池观察到的任务失败后，不再调用新任务工厂；池停止取项，并尝试对尚未耗尽的输入迭代器调用一次可选的 `return()`，然后等待已经启动的任务全部结算，再以第一个停止原因拒绝。一次 `return()` 调用不保证迭代器自己的清理已经完成。排空只表示池不再等待活动任务；它不会回滚已完成的写入，也不会把忽略 signal 的工作杀掉。

`collect`（收集）把每个实际启动任务的履行值或拒绝原因保存为状态记录，并继续填充空槽位，直到输入耗尽且活动任务排空。履行（`fulfilled`）表示任务成功，拒绝（`rejected`）表示任务失败；对应字段分别是 `value` 和 `reason`。未启动的任务没有结果记录。工厂索引从 0 开始，Fetch 的 `page` 参数从 1 开始；例如页 2 对应 `results[1]`。

### Abort 会停止调度，不会强行终止任意 Promise

中止信号收到 `abort` 事件时，池停止再取输入，尝试对未耗尽的同步迭代器调用一次可选的 `return()`，并唤醒正在等待活动任务结算的调度器。池把同一个中止信号传给在途工厂；Fetch 会按 Fetch 的取消协议响应它，普通 Promise 本身没有强制终止能力。若在途任务忽略该信号或永不结算，池就继续等待，调用不会提前结束。

| 时刻 | 池和输入 | 已启动任务 |
| --- | --- | --- |
| `0 ms` | 从页 1、页 2 开始，活动数为 `2` | 两个工厂都收到同一个 `pageSignal` |
| `5 ms`：页面调用 `controller.abort()` | 停止取项，尝试调用迭代器 `return()` 一次，不启动页 3，并立即唤醒调度器 | 支持中止的 Fetch 收到信号；忽略它的工作仍运行 |
| 已启动任务全部结算后 | 用选定的首个停止原因拒绝池调用 | 不会再启动任务；一次 `return()` 不保证迭代器清理已完成 |

停止原因按首先调用 `stop(reason)` 的事件确定。比如 stop 策略下若页 2 的失败先被池观察到，后来到达的外部 abort 不会替换这个失败；若 abort 先被观察到，随后到达的任务失败也不会替换中止原因。`collect` 不会因单项任务失败调用 `stop`，但外部 abort 仍会停止整池并拒绝。

页面取消与“任一任务失败就取消兄弟请求”是两项独立策略。本例只把页面生命周期已有的中止信号传给任务，任务失败不会自动调用控制器的 `abort()`。若调用方要求失败时中止仍在途的 Fetch，应定义相应控制器和失败策略。即使 Fetch 中止，也不能撤回服务器已经收到并执行的写操作。

在该报表案例中，`pageSignal` 是 `controller.signal`；页面离开处理器调用同一个 `controller.abort()`。调用方只在权限校验通过后创建任务：

~~~javascript
const pageSignal = controller.signal;
const pageTasks = createPageTasks("42", "recent");
const { results, peakActive } = await runBounded(pageTasks, 2, {
  failure: "collect",
  signal: pageSignal,
});

for (const [index, result] of results.entries()) {
  if (result.status === "fulfilled") {
    console.log(index, result.value);
  } else {
    console.error(index, result.reason);
  }
}
~~~

若外部 abort、输入迭代器错误或非法任务项使池整体拒绝，`await runBounded(...)` 会抛出原因，不会返回这份 `results`。

如果上游没有预先得到五个页码，而是每次要等上一页返回 `nextCursor` 才能确定下一项，就不适合提前构造这组任务；应从已知输入开始顺序读取，[报表行怎样按页异步读取？](#%E6%8A%A5%E8%A1%A8%E8%A1%8C%E6%80%8E%E6%A0%B7%E6%8C%89%E9%A1%B5%E5%BC%82%E6%AD%A5%E8%AF%BB%E5%8F%96%EF%BC%9F)解释了这种依赖。

### 可折叠查看：有限范围的教学实现

- `limit` 必须是大于 0 的安全整数；`failure` 只能是 `"stop"` 或 `"collect"`。
- 输入是同步可迭代对象，逐项产出的值必须是函数；池只在有槽位时调用它，并以 `{ signal, index }` 调用。
- 池仍在等待的活动任务数不会超过 `limit`；它等待工厂调用返回值的结算，不限制工厂启动但未纳入返回值的底层工作。成功时履行 `{ results, peakActive }`；`stop` 时以首次停止原因拒绝；`collect` 时履行已运行项目的状态和值或原因。
- 外部 abort、同步输入错误和非法任务项都会拒绝整个池，即使 `failure` 是 `"collect"`。输入中尚未取到的项目不会被检查。
- 停止或 abort 后停止取项，并尝试对未耗尽迭代器（iterator）调用一次可选的 `return()`；一次调用不保证迭代器完成自己的清理。清理异常不会覆盖已确定的首个停止原因。池会等待已启动任务的返回值结算。
- 只支持同步可迭代对象；不提供重试、异步迭代、持久配额或持久化。它限制调用工厂的并发，不限制工厂内部额外发起的工作。

同步 `iterator.next()` 可以在池调用期间触发用户代码。本例只说明 `next()` 函数体内同步触发 abort、并返回普通数据属性步骤的情况：若返回 `{ done: true }`，池记录输入耗尽，不再尝试 `return()`；若返回 `{ done: false, value: task }`，池尝试调用一次 `return()`，再次确认停止状态后不启动刚取到的任务。带自定义 `done` 或 `value` getter 的迭代步骤会在属性读取期间执行其他代码，不属于这项说明覆盖的重入路径。

> [!example]- 完整代码：runBounded
>
> ~~~javascript
> async function runBounded(tasks, limit, { failure = "stop", signal } = {}) {
>   if (!Number.isSafeInteger(limit) || limit < 1) {
>     throw new RangeError("limit 必须是正整数");
>   }
>   if (failure !== "stop" && failure !== "collect") {
>     throw new TypeError('failure 必须是 "stop" 或 "collect"');
>   }
>   if (tasks == null || typeof tasks[Symbol.iterator] !== "function") {
>     throw new TypeError("tasks 必须是同步 iterable");
>   }
>
>   const iterator = tasks[Symbol.iterator]();
>   if (iterator == null || typeof iterator.next !== "function") {
>     throw new TypeError("tasks 必须产生 iterator");
>   }
>
>   const results = [];
>   const active = new Set();
>   let nextIndex = 0;
>   let activeCount = 0;
>   let peakActive = 0;
>   let exhausted = false;
>   let pulling = false;
>   let returnAfterNext = false;
>   let iteratorReturnAttempted = false;
>   let stopped = false;
>   let stopReason;
>   let wakeStop;
>   const stopSignal = new Promise(resolve => {
>     wakeStop = resolve;
>   });
>
>   function attemptIteratorReturn() {
>     if (iteratorReturnAttempted || exhausted) return;
>     iteratorReturnAttempted = true;
>     const returnMethod = iterator.return;
>     if (returnMethod == null) return;
>     if (typeof returnMethod !== "function") {
>       throw new TypeError("iterator.return 必须是函数");
>     }
>     const result = returnMethod.call(iterator);
>     if (result === null ||
>         (typeof result !== "object" && typeof result !== "function")) {
>       throw new TypeError("iterator.return 必须返回对象");
>     }
>   }
>
>   function attemptIteratorReturnSafely() {
>     try {
>       attemptIteratorReturn();
>     } catch {
>       // 清理错误不覆盖原先确定的失败或 abort reason。
>     }
>   }
>
>   function stop(reason) {
>     if (!stopped) {
>       stopped = true;
>       stopReason = reason;
>     }
>     if (pulling) returnAfterNext = true;
>     else attemptIteratorReturnSafely();
>     wakeStop();
>   }
>
>   const onAbort = () => stop(signal.reason);
>   if (signal) {
>     if (signal.aborted) onAbort();
>     else signal.addEventListener("abort", onAbort, { once: true });
>   }
>
>   async function runTask(task, index) {
>     activeCount++;
>     peakActive = Math.max(peakActive, activeCount);
>     try {
>       const value = await task({ signal, index });
>       results[index] = failure === "collect"
>         ? { status: "fulfilled", value }
>         : value;
>     } catch (reason) {
>       if (failure === "collect") {
>         results[index] = { status: "rejected", reason };
>       } else {
>         stop(reason);
>       }
>     } finally {
>       activeCount--;
>     }
>   }
>
>   try {
>     while (!stopped && !exhausted) {
>       while (!stopped && !exhausted && active.size < limit) {
>         if (signal?.aborted) {
>           stop(signal.reason);
>           break;
>         }
>
>         pulling = true;
>         let step;
>         try {
>           step = iterator.next();
>         } finally {
>           pulling = false;
>         }
>
>         if (step === null ||
>             (typeof step !== "object" && typeof step !== "function")) {
>           throw new TypeError("iterator.next 必须返回对象");
>         }
>         if (step.done) {
>           exhausted = true;
>           returnAfterNext = false;
>           break;
>         }
>         if (returnAfterNext) {
>           returnAfterNext = false;
>           attemptIteratorReturnSafely();
>         }
>         if (stopped || signal?.aborted) {
>           if (!stopped) stop(signal.reason);
>           break;
>         }
>
>         const task = step.value;
>         if (stopped || signal?.aborted) {
>           if (!stopped) stop(signal.reason);
>           break;
>         }
>         if (typeof task !== "function") {
>           throw new TypeError("第 " + nextIndex + " 项不是任务函数");
>         }
>
>         const index = nextIndex++;
>         let tracked;
>         tracked = runTask(task, index).finally(() => active.delete(tracked));
>         active.add(tracked);
>       }
>
>       if (!stopped && active.size > 0) {
>         await Promise.race([...active, stopSignal]);
>       }
>     }
>   } catch (error) {
>     stop(error);
>   }
>
>   if (stopped && !exhausted) attemptIteratorReturnSafely();
>   await Promise.all(active);
>   if (signal) signal.removeEventListener("abort", onAbort);
>   if (stopped) throw stopReason;
>   return { results, peakActive };
> }
> ~~~

`runTask` 在每项任务内部接住抛出或拒绝，所以活动任务完成时池能统一等待。`stop` 把首次停止原因留在 `stopReason`；`collect` 则把项的状态写回 `results[index]`。`Promise.race([...active, stopSignal])` 只用于“任一活动任务结算”与“池已停止”之间唤醒调度器；它本身不取消输掉的 Promise。最后的 `Promise.all(active)` 负责排空已启动任务。

首个停止原因优先、尝试调用未耗尽迭代器的 `return()`、以及 abort 后等待活动任务 Promise，是这份 `runBounded` 的应用层契约；ECMAScript 规定同步迭代步骤怎样读取和调用迭代器的 `return()`，DOM/Fetch 规定哪些活动能响应 AbortSignal，但这些标准并没有定义这个教学池的 stop/collect 策略。

> [!info]- 来源
> - **同步迭代器步骤与关闭。** [ECMAScript 2027 草案（2026-11-08）§7.4.4、§7.4.10–7.4.11、§27.8.1.3](https://tc39.es/ecma262/#sec-iteratorclose)，核对日期：2026-11-12。`GetIterator`、`IteratorStepValue`、`IteratorClose` 和生成器的 `return()` 支持同步输入与关闭方法语义；一次生成器 `return()` 可以返回 `done: false`，因此池的单次尝试不保证生成器清理完毕。
> - **Promise 竞速。** [ECMAScript 2027 草案 §27.5.4.5 `Promise.race`](https://tc39.es/ecma262/#sec-promise.race)，核对日期：2026-11-12。它按首个结算输入决定组合 Promise；此处只拿它唤醒调度器，不把它当作活动任务取消机制。
> - **Fetch 响应与正文。** [WHATWG Fetch §2.2.3 Statuses、§5.3 Body mixin、§5.5 Response](https://fetch.spec.whatwg.org/)，Living Standard 更新时间：2026-10-19。`ok` 对应 200–299 状态；`json()` 消费并解析正文，解析可拒绝；Fetch 只有遇到网络错误等失败时才拒绝，HTTP 非成功状态仍可产生 Response。
> - **AbortSignal。** [WHATWG DOM §3 Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)，Living Standard 更新时间：2026-11-11；Promise 本身没有内建 abort，API 可以选择接受、响应或忽略 `AbortSignal`。
> - **Fetch 中止。** [WHATWG Fetch §5.6 Fetch methods — Abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard 更新时间：2026-10-19。Fetch 可响应 signal 并中止 Fetch/响应体处理；这不能撤销远端已发生的副作用。
> - **隔离执行范围。** 使用 Node.js `v26.13.0` / V8 `14.6.202.34-node.40` 实测顺序、`stop` / `collect`、abort、iterator `return()` 和本地 loopback HTTP 响应体场景。图和时间表的 10/20/30 ms 是合成延迟，只表达完成先后，不是网络测量或其他宿主的时间保证。
## 42. 链式接口如何先排队、再依次执行延后任务？

### 案例背景

用一个合成的 LazyMan 案例说明方法链如何变成按序执行的闭包队列。调用者希望先写完三项命令，再依次看到吃水果、等待后醒来、吃面包：

~~~javascript
new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
~~~

这里的 `Ada` 是这条链的示例身份；精简输出只打印食物和等待，不打印名字。链式调用在当前同步代码里把三项任务放进实例的 `tasks` 数组；构造函数安排的初始定时器回调稍后才启动第一项。队列不是宿主事件循环的任务队列，里面保存的是应用自己的函数。

![构造函数先安排 setTimeout 箭头回调 this.next()，链式方法随后同步登记三项。初始 next 取出 eat fruit；已登记的 sleep 闭包设置 10 ms 定时器后返回；等待回调再推进至 eat bread，最终 next 发现队列为空并返回](../../frontend/javascript/resources/lazyman-queue-timing.svg)

### 为什么构造时要延后第一项？

如果构造函数立刻调用 `next()`，当时 `tasks` 还是空数组；`shift()` 会取到 `undefined`，而后续 `.eat()` 与 `.sleep()` 尚未执行。构造函数改用 `setTimeout` 安排一个稍后的回调，让当前同步链先把三项工作登记好。JavaScript 不会在这段同步代码中途切去执行另一个普通定时器回调；具体回调何时获得调度由宿主决定。

下面是本例的完整教学队列。`name` 记录实例身份；任务输出为聚焦顺序而省略名字。

~~~javascript
class LazyMan {
  constructor(name) {
    this.name = name;
    this.tasks = [];
    setTimeout(() => this.next(), 0);
  }

  eat(food) {
    this.tasks.push(() => {
      console.log("eat " + food);
      this.next();
    });
    return this;
  }

  sleep(ms) {
    this.tasks.push(() => {
      setTimeout(() => {
        console.log("wake up after " + ms + "ms");
        this.next();
      }, ms);
    });
    return this;
  }

  next() {
    const task = this.tasks.shift();
    if (task) task();
  }
}
~~~

`.eat(food)` 和 `.sleep(ms)` 当场只把函数压入队列，并返回同一个 `this`，所以调用者可以继续链式调用。closure（闭包）保留入队时的 `food` 或 `ms`；箭头函数也在回调中继续使用同一个实例的 `this`。等 `next()` 取出函数时，工作才真正发生。

`next()` 取出并执行队首任务；若队列为空，它就返回。构造函数安排的定时器回调负责第一次调用 `next()`，之后由各项任务在自己的工作完成时调用一次。普通 `eat` 任务打印后立刻推进；轮到已登记的 `sleep` 闭包时，它才安排定时器并返回，等回调打印醒来消息后再推进。调用者按本例约定只使用 `.eat()`、`.sleep()` 这类登记方法，不直接调用 `next()`。

`next()` 是这个类自己定义的普通方法，不是浏览器、Node.js、定时器或 Promise 内建的队列推进接口。

### 队列怎样推进到最终输出？

继续跟踪同一条合成输入。`tasks` 中从左到右是下一项先执行；`next()` 取走队首后，任务可能同步推进，也可能把推进交给稍后的宿主回调。

| 阶段 | 应用队列剩余项 | 正在执行的工作 | 谁触发下一步 |
| --- | --- | --- | --- |
| 链式调用结束 | `eat fruit → sleep 10 → eat bread` | 尚未启动 | 构造函数安排的初始定时器回调；当前同步代码结束后才有机会运行 |
| 初始 `next()` 取出第一项 | `sleep 10 → eat bread` | `eat fruit` 打印，然后同步调用 `next()` | 当前 JavaScript 调用 |
| `next()` 取出已登记的等待闭包 | `eat bread` | 执行等待闭包，安排延时参数为 10 ms 的定时器，然后返回；队列暂不继续 | 宿主稍后调度的定时器回调 |
| 等待回调运行 | `eat bread` | 打印醒来消息，再调用 `next()` | 当前定时器回调中的 JavaScript |
| 最后一项完成 | 空 | `eat bread` 打印，再调用 `next()`；`shift()` 得到 `undefined`，调用结束 | 无下一项 |

输出顺序是：

> [!example] Ada 的三个排队命令
> 输入为 `eat("fruit")`、`sleep(10)`、`eat("bread")`。`sleep` 任务未在入队时等待；它直到轮到自己时才启动 10 ms 定时器。定时器回调运行后才推进到面包任务。
>
> ~~~text
> eat fruit
> wake up after 10ms
> eat bread
> ~~~

这里的 10 ms 是传给定时器的延时参数，醒来日志复用同一参数，不表示测得的经过时间。浏览器标准说明定时器会在指定延时后安排回调，但负载或其他任务可让实际执行变晚；Node.js v26.13.0 也明确不保证精确时刻或回调间的固定顺序。本例只依赖“等待回调推进队列”这一先后关系。

在原例中，若外部代码在 `sleep` 等待期间调用 `.eat("cake")`，新闭包追加到 `tasks` 尾部；回调推进后，原有 `eat bread` 先于 `eat cake` 执行。另一个变体以 `.sleep(10)` 作为最后一项：等待闭包已出队，所以 `tasks.length` 暂时为 0，但等待回调仍在途；此时追加的 `eat cake` 会在回调推进后运行。只有最后一项完成并调用 `next()`、而 `next()` 看到空队列返回之后，后续单纯追加任务才不会自动重启队列，因为登记方法只入队，不安排新的启动回调。

这个串行队列依赖一个明确约定：调用者只登记任务；每个出队任务只在自身工作完成时调用一次 `next()`。若漏调，队列就停住；若任务提前或重复调用，后续任务可能在当前工作完成前启动。调用者直接调用 `next()` 也可能绕过尚未完成的等待。任务抛错时本实现没有恢复策略；等待中的定时器没有保存句柄，不能由实例取消。连续的同步任务会通过 `next()` 递归推进，很多项可能耗尽调用栈。它只演示链式登记、闭包保存参数和显式推进，不是具备错误恢复或取消能力的生产队列。

若任务需要返回值、并发组合或把失败交给调用者处理，可以用 Promise 链或 `async function` (异步函数)；[回调、Promise 与 async 函数怎样组合异步工作？](#40.%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E6%80%8E%E6%A0%B7%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%EF%BC%9F)解释这些结果怎样传播。本页只回答链式命令如何排队并按序推进。

> [!info]- 来源
> - **浏览器定时器与事件循环。** [WHATWG HTML §8.7 Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)、[§8.1.7 Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)，Living Standard 更新时间：2026-11-11。定时器初始化会创建稍后进入 timer task source（定时器任务源）的任务；事件循环先执行当前选中的任务步骤，之后再选择可运行任务。标准明确不保证定时器按精确延时准点运行。
> - **Node.js 计时器范围。** [Node.js v26.13.0 Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html)。Node 定时器采用不同的内部实现；文档说明实际时刻及回调顺序不作精确保证，且小于 1 ms（含 0）的延迟参数（`delay`）会设为 1 ms。本例不把浏览器定时器的延时规则外推到 Node。
> - **闭包与箭头函数。** [ECMAScript 2027 草案（2026-11-08）§10.2 ECMAScript Function Objects、§15.3 Arrow Function Definitions](https://tc39.es/ecma262/)，核对日期：2026-11-12。函数对象保存它闭合的词法环境；箭头函数不创建自己的 `this` 绑定。本例入队的函数稍后仍能读取 `food`、`ms` 参数，并通过外层方法的 `this` 调用 `next()`。
## 43. 迭代器与生成器怎样按需产出并清理数据？

### 案例背景

报表 42 有很多行，页面通过 Fetch API（浏览器的应用程序编程接口）逐页请求并逐行追加结果，不必先把所有页合成一个大数组。它检查 HTTP（超文本传输协议）状态并读取 JSON（JavaScript 对象表示法）。调用方希望处理一行后再取下一行，也可能在找到目标行或用户取消时提前停止。迭代协议规定生产者怎样交付下一项、怎样表示结束；生成器可把暂停和清理逻辑写在产出值的代码旁边。

### 可迭代对象怎样交给消费者逐项读取？

iterable（可迭代对象）通过 Symbol.iterator 提供 iterator（迭代器）。迭代器的 next() 返回一个对象：消费者把 done 转成布尔值，false 表示继续使用 value，true 表示结束。done 缺省时按 false 处理；结束时 value 可以省略。有 length 或数字键并不会自动让普通对象可迭代。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }
~~~

数组、字符串、Map、Set、类型化数组和 arguments 对象都能迭代。Document Object Model（文档对象模型，DOM）的 NodeList（节点列表）也支持迭代，但它是宿主 API；集合是否实时变化取决于返回它的具体 API，DOM 集合的实时/静态差异见[HTMLCollection 与 NodeList 如何处理集合变化？](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F)。

~~~mermaid
flowchart LR
  A["iterable：调用 Symbol.iterator"] --> B["iterator：调用 next()"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["消费 result.value"]
  D --> B
  C -- "true" --> E["结束"]
~~~

一个 iterable 每次可以返回新的 iterator，但协议不要求如此。很多内置迭代器和 generator 会把自身作为 iterator 返回，所以那种对象消费一次后已经结束；自定义 iterator 是否可迭代、是否可重用由它自己的协议实现决定：

~~~javascript
const range = {
  start: 1,
  end: 3,
  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) return { value: current++, done: false };
        return { value: undefined, done: true };
      }
    };
  }
};

[...range]; // [1, 2, 3]

const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true
~~~

### 生成器怎样暂停、接收值并委托工作？

generator（生成器）函数调用时只创建一个同时实现可迭代协议和迭代器协议的对象，函数体尚未执行。首次调用 next() 才开始运行函数体，直到第一个 yield 暂停并把当前值交给调用方；下一次 next() 才恢复。第一次 next(value) 的参数会被忽略，因为还没有暂停在 yield；后续参数会成为当前暂停处 yield 表达式的值。

~~~javascript
function* conversation() {
  const name = yield "你叫什么名字？";
  const hobby = yield "你好，" + name + "！你喜欢做什么？";
  return name + "喜欢" + hobby;
}

const chat = conversation();
chat.next();          // { value: "你叫什么名字？", done: false }
chat.next("Ada");     // { value: "你好，Ada！你喜欢做什么？", done: false }
chat.next("编程");    // { value: "Ada喜欢编程", done: true }
~~~

yield* 把读取委托给另一个 iterable 或 generator，并把子生成器的 return 值交回当前生成器。它能把递归遍历组合成一个惰性输出序列：

~~~javascript
function* flatten(items) {
  for (const item of items) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}

[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]

function* child() {
  yield "item";
  return 42;
}
function* parent() {
  return yield* child();
}
const delegated = parent();
delegated.next(); // { value: "item", done: false }
delegated.next(); // { value: 42, done: true }
~~~

生成器按调用方需求才计算后续值。它可以表达大序列或无限序列，而不把所有结果预先放进数组：

~~~javascript
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

const fib = fibonacci();
fib.next().value; // 0
fib.next().value; // 1
fib.next().value; // 1
fib.next().value; // 2
~~~

同一状态思路也可按需产生序号，不需要提前分配全部 id。下面只在同一个生成器实例内、计数尚未超过 Number 精确整数范围时保证不重复；不同实例使用同一前缀仍会生成相同 ID：

~~~javascript
function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}

const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
~~~

### 提前退出如何通知迭代器清理？

迭代器可以实现 return()，作为调用者不再请求下一项时的清理钩子。for...of 因循环体中的 break、throw 或其他突然控制流离开时会调用该钩子；若生成器使用 try/finally，关闭时会执行 finally。

~~~javascript
const source = {
  [Symbol.iterator]() {
    let value = 0;
    return {
      next() {
        return { value: value++, done: false };
      },
      return() {
        console.log("释放迭代器资源");
        return { done: true };
      }
    };
  }
};

for (const value of source) {
  if (value === 2) break; // 退出时调用 return()
}
~~~

这是一种协议层的“不会再向你要值”通知，不等于中断任意底层工作。若 iterator 的 next() 已在等待网络、文件或流，return() 本身不会替这些宿主 API 实现取消；要停止它们，还需其显式取消机制，例如把 AbortSignal 传给 Fetch。

对异步生成器，若一次 next() 仍在等待，之后调用 return() 不会抢占那次挂起的 next；它要等该次操作完成后才有机会关闭。正在执行的 Fetch 仍需单独通过 AbortSignal 中止。

> [!warning] 关闭钩子由消费者的退出路径触发
> 上述保证针对循环体执行 break、throw 等情况。若 iterator 自己的 next() 抛错，不能据此假定消费者会再调用它的 return() 清理；需要可靠释放资源时，应把清理放进生成器自己的 finally 或使用宿主 API 的显式关闭协议。

### 报表行怎样按页异步读取？

async iterable（异步可迭代对象）通过 Symbol.asyncIterator 提供 async iterator（异步迭代器）。每次 next() 返回一个稍后完成的 Promise；for await...of（异步迭代循环）等待当前一项并处理完循环体，再请求下一项。这样消费者的处理速度自然限制下一次读取，形成逐项 backpressure（背压）。

表格行是第二阶段：三项基础请求的响应已通过状态和结构校验，页面也依据权限结果决定可以读取行后，把 loadReport(42, sort, signal) 使用的同一报表 ID、排序和请求信号交给独立分页接口。客户端权限判断只控制是否发起交互，服务端仍须独立验证访问权。行请求不属于基础 Promise.all，也不必先把所有行读进内存；若基础请求失败或用户切换筛选，页面不会继续交付这条旧行流。下面假设行记录至少有字符串 id；validateReportPage 在响应边界检查分页形状，appendRow 作为参数注入，返回当前行追加完成的 Promise；它必须绑定本次筛选独立拥有的输出容器。currentSort、selectedRowId 和取消按钮来自同一个报表界面。

~~~javascript
function validateReportRow(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      typeof value.id !== "string") {
    throw new Error("报表行缺少字符串 id");
  }
  return value;
}

function validateReportPage(value) {
  if (!value || typeof value !== "object" || !Array.isArray(value.items)) {
    throw new Error("报表分页响应缺少 items 数组");
  }
  if (value.nextCursor !== null &&
      (typeof value.nextCursor !== "string" || value.nextCursor.length === 0)) {
    throw new Error("nextCursor 必须是非空字符串或 null");
  }
  return {
    items: value.items.map(validateReportRow),
    nextCursor: value.nextCursor
  };
}

async function* reportRows(reportId, sort, signal) {
  let cursor = null;
  const seenCursors = new Set();

  try {
    while (true) {
      const query = new URLSearchParams({ sort });
      if (cursor !== null) query.set("cursor", cursor);
      const response = await fetch(
        "/api/reports/" + reportId + "/rows?" + query,
        { signal }
      );
      if (!response.ok) throw new Error("HTTP " + response.status);

      const page = validateReportPage(await response.json());
      for (const row of page.items) yield row;
      if (page.nextCursor === null) return;
      if (seenCursors.has(page.nextCursor)) {
        throw new Error("报表接口重复返回分页游标");
      }
      seenCursors.add(page.nextCursor);
      cursor = page.nextCursor;
    }
  } finally {
    console.log("报表行迭代已关闭");
  }
}

async function appendReportRows(reportId, sort, stopAfterId, signal, appendRow) {
  try {
    for await (const row of reportRows(reportId, sort, signal)) {
      if (signal.aborted) throw signal.reason;
      await appendRow(row);
      if (row.id === stopAfterId) break;
    }
  } catch (error) {
    if (signal.aborted && error === signal.reason) return;
    throw error;
  }
}

const controller = new AbortController(); // 用户取消时向正在运行的 Fetch 发信号
cancelButton.addEventListener("click", () => controller.abort(), { once: true });
appendReportRows(42, currentSort, selectedRowId, controller.signal, appendRow)
  .catch(showReportError);
~~~

找到目标行后 break 会关闭 async iterator，因此生成器的 finally 会执行；未请求的后续页不会再读取。若用户在 fetch 等待期间按“取消”，外层需通过 AbortController（中止控制器）调用 abort()，Fetch 才会收到 AbortSignal（中止信号）。若取消发生在 appendRow 等待期间，该行追加已开始且本例没有把 signal 交给 appendRow，不能撤回；如果它直接写共享当前列表，旧行就可能混入新筛选。因此调用方应像[错误处理章节](#%E6%8A%A5%E8%A1%A8%E8%AF%B7%E6%B1%82%E7%9A%84%E9%94%99%E8%AF%AF%E7%94%B1%E8%B0%81%E6%8E%A5%E6%89%8B%EF%BC%9F)那样为每一代创建独立容器，切换时替换当前容器；已开始的旧追加只能写脱离页面的旧容器。追加完成后，循环在开始下一行前检查 signal，不会再追加缓存的后续行。catch 只吞掉与该 signal.reason 相同的取消原因；恰好同时发生的独立校验或追加错误仍会向上传播。异步迭代协议不会自动取消正在进行的网络请求，也不能撤销远端已经完成的写操作。此例在每页响应后检查 items、行结构和 nextCursor，并拒绝重复游标；它逐页持有一个响应体并逐行交付，没有把整个报表预存为数组。

> [!example] 在当前页停止后不会请求下一页
> 假设当前页交付行 r-101、r-102，并带有 nextCursor。若 r-102 是 stopAfterId，循环在消费 r-102 后执行 break；生成器关闭并运行 finally，停在该页，不会更新 cursor 或发出下一页请求。

for await...of（异步迭代循环）也能读取同步 iterable 中的 Promise，但按输入顺序等待，而非按最快完成顺序产出。下面两个计时器在数组构造时同时启动，第二项先完成；迭代结果仍为 first、second：

~~~javascript
const slow = new Promise(resolve => setTimeout(() => resolve("first"), 20));
const fast = new Promise(resolve => setTimeout(() => resolve("second"), 0));

async function collectInInputOrder() {
  const values = [];
  for await (const value of [slow, fast]) values.push(value);
  return values;
}

collectInInputOrder().then(values => console.log(JSON.stringify(values)));
// ["first","second"]
~~~

> [!warning] 并行 Promise 不要只按序等待
> 若第二个 Promise 在第一个仍 pending 时先拒绝，for await...of 仍等待第一个；宿主可能在循环读取到第二项前先报告这个拒绝未处理。若多项工作彼此独立并且都需要观察成功或失败，先用 Promise.all 或 Promise.allSettled 安装统一处理路径。

若目标是汇总独立操作，通常用 Promise.all；异步迭代适合逐项到达、逐项消费的数据。Promise 组合的输入顺序与取消边界见[回调、Promise 与 async 函数怎样组合异步工作？](#%E6%8A%A5%E8%A1%A8%E8%AF%B7%E6%B1%82%E4%BD%95%E6%97%B6%E5%B9%B6%E5%8F%91%E3%80%81%E4%BD%95%E6%97%B6%E9%A1%BA%E5%BA%8F%E7%AD%89%E5%BE%85%EF%BC%9F)。

在 async/await 标准化以前，co 等库曾运行生成器：生成器 yield 一个 Promise，runner（驱动器）在 Promise 完成后把值传给 next()，拒绝时把错误传给 throw()。这是历史控制流模式；async 函数有自己的 Promise 语义，并不是由用户可见的 generator 实例实现。

> [!info]- 来源
> - iterable、iterator、generator、async iterator、yield* 与迭代关闭：ECMAScript 2027 规范（2026-11-05 草案快照），[迭代协议](https://tc39.es/ecma262/#sec-iteration)、[IteratorClose](https://tc39.es/ecma262/#sec-iteratorclose)、[AsyncIteratorClose](https://tc39.es/ecma262/#sec-asynciteratorclose)、[异步生成器请求队列](https://tc39.es/ecma262/#sec-asyncgeneratordrainqueue)、[for-of 与 for-await-of](https://tc39.es/ecma262/#sec-for-in-and-for-of-statements-runtime-semantics-labelledevaluation)。
> - Fetch 中止与响应体清理：[Fetch Standard，Living Standard 2026-10-19：abort a fetch](https://fetch.spec.whatwg.org/#abort-fetch)。中止请求与回滚远端业务副作用是不同保证。
> - DOM NodeList 的可迭代与集合实时性：由相应 DOM API 定义，见[DOM Standard，Living Standard 2026-11-04：NodeList](https://dom.spec.whatwg.org/#interface-nodelist)与本仓库的[DOM 集合章节](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F)。
> - 宿主计时器不保证精确触发时间，拒绝处理器的安装时机也可能触发全局未处理拒绝报告：WHATWG HTML Living Standard（2026-11-05），[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)、[unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)。
## 44. JavaScript 错误应在哪一层恢复、传播或上报？

### 案例背景

报表筛选触发三项并发 Fetch API（浏览器的应用程序编程接口）请求，分别取报表、摘要和权限；三者都校验成功后，同一报表 ID、排序和取消信号还可驱动迭代章节的分页行流。任一网络失败、HTTP（超文本传输协议）404、JSON（JavaScript 对象表示法）解析失败或结构错误，都由服务函数拒绝给页面；即使数据请求成功，组件渲染也仍可能出错。每个错误都要交给一个能决定下一步的层级：页面选择提示、保留旧数据或重试，渲染边界负责限定范围内的 user interface（用户界面，UI）兜底，全局处理器只记录遗漏。

### 报表请求的错误由谁接手？

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

`loadReport` 来自[异步请求章节](#%E6%8A%A5%E8%A1%A8%E8%AF%B7%E6%B1%82%E4%BD%95%E6%97%B6%E5%B9%B6%E5%8F%91%E3%80%81%E4%BD%95%E6%97%B6%E9%A1%BA%E5%BA%8F%E7%AD%89%E5%BE%85%EF%BC%9F)，返回已校验的三项基础数据；`appendReportRows` 来自[分页迭代章节](#%E6%8A%A5%E8%A1%A8%E8%A1%8C%E6%80%8E%E6%A0%B7%E6%8C%89%E9%A1%B5%E5%BC%82%E6%AD%A5%E8%AF%BB%E5%8F%96%EF%BC%9F)，沿用这次的 sort 和 signal。Promise.all 自身不会取消同组请求；这里在处理非取消失败时显式中止共享 signal，停止仍支持取消的兄弟 Fetch 和行流。实际页面可把基础数据与行列表的 loading 拆开；这里用一个状态聚焦最新请求的错误归属。序号检查和 abort 各有作用：signal 尽力停止支持取消的 Fetch；若旧结果仍完成，序号阻止它覆盖当前筛选或清掉新请求的 loading。

> [!example] 两次筛选交错返回
> recent 请求先启动，随后 oldest 请求启动并使 recent 的 signal 中止。序号保护本节的报表、摘要、权限、用户可见错误和 loading 状态；旧请求的 finally 不会关闭 oldest 的 loading。真正的取消原因被静默；若旧请求恰好产生独立错误，仍会交给 reportError 记录，但不会覆盖当前筛选的提示。分页章节说明，每行追加前还会检查同一个 signal；若 append 已开始且不支持取消，它仍可能完成，但只写本代容器；容器已被新请求替换时，旧写入不会显示，也不会再开始下一行。只有最新一代完成、失败或被用户取消时，页面才清理这次 loading。

检查 response.ok 把“服务器给了一个 HTTP 响应”与“这个响应可供页面使用”分开。Fetch Promise 在响应可用时给出 Response；正文还需由 json() 读取，解析或运行时校验都可能失败。此例在权限字段允许后才调用分页函数，rows 接口仍必须在服务端重新验证权限。Fetch、JSON 和 Promise 的行为见异步章节。

> [!example] HTTP 404 如何走到界面提示？
> Fetch 成功拿到状态为 404 的 Response，所以不会因状态码自动拒绝；loadReport 检查 response.ok 后拒绝，把失败交给 onRefreshClick 的 catch。页面仍掌握当前筛选交互，于是更新错误提示并上报；finally 则关闭最新请求的 loading 状态。

页面能显示可恢复的错误，所以它可以在 catch 中更新界面。若一个底层 helper 只记录日志后正常返回，调用方会误以为 Promise 已成功；若当前层没有恢复决定，就把错误继续抛给知道页面上下文的上层。

### try/catch/finally 覆盖哪段控制流？

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

### 浏览器全局处理器能兜住什么？

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

### React 错误边界覆盖哪个 UI 范围？

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
## 45. 收到不可信 JSON 后，TypeScript 怎样建立可信的类型？

月度报表页从接口或浏览器存储读入数据时，输入内容在运行时仍只是外部值。TypeScript 的类型注解会在输出 JavaScript 时擦除；它们能检查我们写下的代码，却不会替 `JSON.parse` 检查实际字段，也不会验证用户是否有权访问某份报表。

因此，数据要经过两个不同步骤：先解析 JSON（JavaScript 对象表示法）语法，再按运行时规则检查结构和取值。成功后从已检查字段重新构造应用对象，后续代码才可以依赖这个对象的静态类型。图只画运行时执行链；`unknown` 是编译期的静态边界，不是 JSON 解析后的运行时转换。

~~~mermaid
flowchart TB
  A[已取得的接口或存储文本] --> B{JSON.parse}
  B -- 语法错误 --> E[返回 syntax]
  B -- 解析成功 --> C[JavaScript 运行时值]
  C --> D{逐项检查字段和值}
  D -- 检查失败 --> F[返回 shape]
  D -- 检查通过 --> G[按已检查字段重建对象]
  G --> H[业务代码使用已检查对象]
~~~

如果文本来自浏览器存储，`getItem` 返回 `null` 时会在进入这条共用链之前返回 `missing`。

### 怎样在运行时检查报表数据？

`unknown`（未知类型）允许一个值暂时存在，但在缩窄到更具体类型前不允许任意读取属性。下面的解析器分别处理语法错误、缺失存储值和字段结构错误；每个通过的行都被重新构造成 `ReportRow`，而不是把外部对象直接断言成该类型。

~~~typescript
type Role = "admin" | "reader";
type ReportStatus = "open" | "published" | "archived";

type ReportRow = {
  id: string;
  title: string;
  month: string;
  region: string;
  status: ReportStatus;
  total: number;
  ownerEmail: string;
};

type ReportData = {
  viewer: { id: string; role: Role };
  rows: ReportRow[];
};

type ParseResult<T> =
  | { ok: true; value: T }
  | { ok: false; reason: "syntax" | "shape" | "missing" };

function isRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function parseReportData(text: string): ParseResult<ReportData> {
  let input: unknown;
  try {
    input = JSON.parse(text);
  } catch {
    return { ok: false, reason: "syntax" };
  }

  if (
    !isRecord(input) ||
    !isRecord(input.viewer) ||
    typeof input.viewer.id !== "string" ||
    (input.viewer.role !== "admin" &&
      input.viewer.role !== "reader") ||
    !Array.isArray(input.rows)
  ) {
    return { ok: false, reason: "shape" };
  }

  const rows: unknown[] = input.rows;
  const checkedRows: ReportRow[] = [];
  for (const candidate of rows) {
    if (
      !isRecord(candidate) ||
      typeof candidate.id !== "string" ||
      typeof candidate.title !== "string" ||
      typeof candidate.month !== "string" ||
      !/^\d{4}-(0[1-9]|1[0-2])$/.test(candidate.month) ||
      typeof candidate.region !== "string" ||
      (candidate.status !== "open" &&
        candidate.status !== "published" &&
        candidate.status !== "archived") ||
      typeof candidate.total !== "number" ||
      !Number.isFinite(candidate.total) ||
      typeof candidate.ownerEmail !== "string"
    ) {
      return { ok: false, reason: "shape" };
    }

    checkedRows.push({
      id: candidate.id,
      title: candidate.title,
      month: candidate.month,
      region: candidate.region,
      status: candidate.status,
      total: candidate.total,
      ownerEmail: candidate.ownerEmail
    });
  }

  return {
    ok: true,
    value: {
      viewer: { id: input.viewer.id, role: input.viewer.role },
      rows: checkedRows
    }
  };
}

function readStoredReport(
  storage: Storage
): ParseResult<ReportData> {
  const text = storage.getItem("monthly-report");
  if (text === null) return { ok: false, reason: "missing" };
  return parseReportData(text);
}

const manualResult = parseReportData(`
{
  "viewer": {
    "id": "u-7",
    "role": "reader"
  },
  "rows": [
    {
      "id": "r-21",
      "title": "北区月报",
      "month": "2026-10",
      "region": "north",
      "status": "published",
      "total": 820,
      "ownerEmail": "ada@example.com"
    }
  ]
}
`);
~~~

TypeScript 标准库把 `JSON.parse` 的返回类型声明为 `any`。赋给 `let input: unknown` 只改变编译器看到的静态类型；运行时仍是 `JSON.parse` 得到的同一个值，并没有自动验证或转换。`isRecord` 内部的对象、非 `null`、非数组条件会实际运行；返回类型 `value is Record<string, unknown>` 则是函数向编译器作出的缩窄承诺，编译器依据它分析后续属性访问，不会替函数证明该承诺正确。实现中的布尔检查和类型谓词必须保持一致。`Array.isArray` 在 TypeScript 标准库中的类型谓词会把值缩窄为 `any[]`，所以这里立即把 `input.rows` 赋给 `unknown[]`，让循环中的每个 `candidate` 仍须先检查再读取。

解析器现在只保证字段形状和示例所写的格式规则。它在运行时检查月份符合 `YYYY-MM` 形式、`total` 是有限数值，但返回类型仍分别是普通 `string` 和 `number`，并未把这两条细则编码进静态类型。解析器按已检查字段重建 `ReportData`，因此忽略并丢弃未声明字段；它不证明 `viewer.id` 是当前登录用户，也不证明该用户可以查看报表，这些授权判断必须由受信任的服务端完成。若业务还要求金额非负、地区来自配置清单等约束，应把对应规则也写入运行时解析，而不是只扩大 TypeScript 类型。`readStoredReport` 把缺失项转换为 `missing`，但不捕获存储访问异常：调用时读取 `localStorage` 可能因来源或策略抛出 `SecurityError`，而 `getItem` 的其他异常也会向上抛出。调用方应按自身降级策略处理，不要把存储故障误报成 JSON 语法错误。

### 怎样用 Zod 在同一个输入边界生成运行时检查和静态类型？

如果手写检查开始重复字段路径和类型判断，可以在同一个报表 JSON 边界使用 schema（结构模式）。下面固定用 Zod `4.6.7`，声明与上例相同的字段形状，但两种检查的接纳规则并不相同：手写解析器重建已知字段并忽略额外键，`z.strictObject` 会拒绝额外键；默认的 `z.object` 则会剥除未知键。Zod 还要求 `ownerEmail` 符合邮箱格式，而手写版本只要求它是字符串。是否拒绝额外键、邮箱需要多严格，应按接口契约决定。不能只为了得到 `z.infer` 类型就把宽泛外部数据断言成模型。

~~~typescript
import * as z from "zod"; // zod@4.6.7

const ReportRowSchema = z.strictObject({
  id: z.string(),
  title: z.string(),
  month: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/),
  region: z.string(),
  status: z.enum(["open", "published", "archived"]),
  total: z.number(), // Zod 4 的 number schema 只接受有限数值
  ownerEmail: z.email(),
});

const ReportDataSchema = z.strictObject({
  viewer: z.strictObject({
    id: z.string(),
    role: z.enum(["admin", "reader"]),
  }),
  rows: z.array(ReportRowSchema),
});

type ReportDataFromSchema = z.infer<typeof ReportDataSchema>;

function parseReportDataWithZod(
  text: string
): ParseResult<ReportDataFromSchema> {
  let input: unknown;
  try {
    input = JSON.parse(text);
  } catch {
    return { ok: false, reason: "syntax" };
  }

  const parsed = ReportDataSchema.safeParse(input);
  if (!parsed.success) {
    const firstIssue = parsed.error.issues[0];
    console.log(firstIssue?.path, firstIssue?.message);
    return { ok: false, reason: "shape" };
  }
  return { ok: true, value: parsed.data };
}

const zodResult = parseReportDataWithZod(`
{
  "viewer": {
    "id": "u-7",
    "role": "reader"
  },
  "rows": [
    {
      "id": "r-21",
      "title": "北区月报",
      "month": "2026-10",
      "region": "north",
      "status": "published",
      "total": "820",
      "ownerEmail": "ada@example.com"
    }
  ]
}
`);
// 第一个结构错误的 path 为 ["rows", 0, "total"]。
// 字符串不会被默默转成数字。
~~~

JSON 语法仍先由 `JSON.parse` 处理；成功后 `input` 是静态 `unknown`，`safeParse` 再实际检查字段和值。成功分支的 `parsed.data` 是已校验并推导出的 `ReportDataFromSchema`。失败分支的 `ZodError.issues` 保存结构化问题；`path` 用字段键和数组索引定位，例如 `rows` 第 0 项的 `total` 对应 `["rows", 0, "total"]`，不是 JSON 文本的行号和列号。遇到未声明键时，路径可能只到包含它的对象（如 `["rows", 0]`），具体键名在问题消息中。手写示例的 `total` 是数值 `820`，所以通过；Zod 示例将该字段改为字符串 `"820"`，虽然仍是语法合法的 JSON，Zod 结构检查会拒绝它。同一个字符串输入也会被手写解析器拒绝，因为它要求 `total` 的运行时类型是 `number`。包装函数打印首个 issue 后只向调用者返回 `{ ok: false, reason: "shape" }`，不会把完整 issue 传出去。后文的 `if (zodResult.ok)` 因此不会调用角色标签函数。

Zod 4 的 `z.number()` 已拒绝 `NaN` 与正负无穷，因此这里不再重复加有限数检查。服务器侧可用 Pydantic 模型检查请求，FastAPI 则从路由与模型声明生成 OpenAPI 契约；实际响应是否兑现契约仍需核验，见[HTTP API 如何描述实际运行的请求与响应契约](../../engineering-foundations/backend/http-api-contracts.md)。Zod 与 Pydantic 都检查运行时输入；TypeScript 的 `z.infer` 只帮助后续代码在编译期保持同一结构，不会自动让网络载荷、浏览器存储或授权可信。

### 类型联合新增分支时怎样让编译器提醒调用处？

解析器仅接受已知角色。调用端在分支中处理角色时，可以把默认分支赋给 `never`（不可能出现的类型）。若以后把 `editor` 加入 `Role`，但忘了补充下列分支，类型检查会在 `never` 赋值处报错。若 `editor` 是外部数据允许的新角色，还必须同步让上面的运行时解析器接受它；只扩充联合类型和显示分支不会使它通过输入检查。这里的标签仅用于界面显示，不是授权判断。

~~~typescript
function roleLabel(role: Role): string {
  switch (role) {
    case "admin":
      return "管理员";
    case "reader":
      return "只读用户";
    default: {
      const unhandled: never = role;
      throw new Error(`未处理的角色：${unhandled}`);
    }
  }
}

if (manualResult.ok) {
  console.log(roleLabel(manualResult.value.viewer.role));
}
if (zodResult.ok) {
  console.log(roleLabel(zodResult.value.viewer.role));
}
~~~

这两道检查覆盖不同边界：运行时解析器决定外部值是否进入应用；穷尽性检查提醒开发者是否处理了应用类型中所有已支持的分支。泛型和工具类型也只描述编译期关系，见[泛型怎样保留输入与输出之间的类型关系？](#46.%20%E6%B3%9B%E5%9E%8B%E6%80%8E%E6%A0%B7%E4%BF%9D%E7%95%99%E8%BE%93%E5%85%A5%E4%B8%8E%E8%BE%93%E5%87%BA%E4%B9%8B%E9%97%B4%E7%9A%84%E7%B1%BB%E5%9E%8B%E5%85%B3%E7%B3%BB%EF%BC%9F)与[怎样从报表类型派生数据形状并约束方法中的 `this`？](#47.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E7%B1%BB%E5%9E%8B%E6%B4%BE%E7%94%9F%E6%95%B0%E6%8D%AE%E5%BD%A2%E7%8A%B6%E5%B9%B6%E7%BA%A6%E6%9D%9F%E6%96%B9%E6%B3%95%E4%B8%AD%E7%9A%84%20this%EF%BC%9F)。

> [!info]- 来源
> - [TypeScript Handbook：unknown 与类型缩窄](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
> - [TypeScript Handbook：断言与类型兼容](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions)、[类型兼容与健全性取舍](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness)
> - [TypeScript Handbook：穷尽性检查](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)
> - **Zod `4.6.7`：** [版本发布记录](https://github.com/colinhacks/zod/releases/tag/v4.6.7)、[4.6.7 文档与源码](https://github.com/colinhacks/zod/tree/v4.6.7/packages/docs/content)、[对象 schema 与 strict keys](https://zod.dev/api?id=objects)、[`safeParse` 与 `z.infer`](https://zod.dev/basics)、[错误 issue 路径](https://zod.dev/packages/core#issues)、[Zod 4 的格式 API](https://zod.dev/v4)。已在隔离的临时目录安装此版本，TypeScript 编译并于 Node `v26.13.0` 运行核对，2026-11-12。
>
> 按 `JSON.parse` 的语法错误、存储缺失值，以及报表结构检查整理；[TypeScript 类型注解会在输出 JavaScript 时擦除](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，`localStorage` 属性访问可能抛出的 `SecurityError` 见 [HTML Standard：localStorage](https://html.spec.whatwg.org/multipage/webstorage.html#dom-localstorage)。来源核对日期：2026-11-12。
## 46. 泛型怎样保留输入与输出之间的类型关系？

报表页会处理很多种行数据和分页结果。若每个函数都复制一份实现，维护成本很高；若一律把参数和返回值写成 `any`（任意类型），调用处又会丢掉具体字段信息。generic（泛型）让同一段逻辑保留调用时的具体类型。

### 怎样把所选字段的类型一并保留下来？

type parameter（类型参数）像是类型层面的变量。编译器可以从调用参数推断它，也可以由调用者显式指定。下面的 `T` 代表整行类型，`K` 受 `keyof T`（类型键集合）约束，只能取该类型已有的键；indexed access type（索引访问类型）`T[K]` 则返回所选键对应的值类型。

~~~typescript
type ReportRow = {
  id: string;
  title: string;
  month: string;
  region: string;
  status: "open" | "published" | "archived";
  total: number;
  ownerEmail: string;
};

function getProperty<T, K extends keyof T>(row: T, key: K): T[K] {
  return row[key];
}

const row: ReportRow = {
  id: "r-21",
  title: "北区月报",
  month: "2026-10",
  region: "north",
  status: "published",
  total: 820,
  ownerEmail: "ada@example.com"
};

const reportId = getProperty(row, "id");       // string
const reportTotal = getProperty(row, "total"); // number
const statusOrTotalKey: "status" | "total" =
  Math.random() < 0.5 ? "status" : "total";
// ReportRow["status"] | number
const statusOrTotal = getProperty(row, statusOrTotalKey);
// getProperty(row, "owner");                  // 编译错误：不是 ReportRow 的键
~~~

`T` 与 `K` 是两个分别推断的类型参数：`T` 保留行形状，`K extends keyof T` 中的 `extends` 是 constraint（约束），要求本次传入的键属于该行已有的键。返回类型 `T[K]` 再按 `K` 取属性值类型，因此单键 `"id"` 得到 `string`，单键 `"total"` 得到 `number`。

把一次调用拆开看，编译器先从 `row` 得到 `T`，再把键限制在 `keyof T` 内，并由传入的字面量键推断 `K`，最后计算 `T[K]`：

| 调用与推导 | 返回类型 |
|---|---|
| `getProperty(row, "id")`：`T = ReportRow`，`K = "id"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["id"]`，为 `string` |
| `getProperty(row, "total")`：`T = ReportRow`，`K = "total"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["total"]`，为 `number` |
| `getProperty(row, statusOrTotalKey)`：`T = ReportRow`，`K` 是 `"status"` 和 `"total"` 组成的联合 | `T[K]` 是 `ReportRow["status"]` 与 `number` 的联合 |

单独保留 `K` 很重要：若签名只把参数写成 `keyof T`、返回值写成 `T[keyof T]`，即使传入字面量 `"id"`，返回类型也会包含字段值类型的联合。若调用者只掌握部分键组成的联合，`T[K]` 只合并这些键对应的字段类型；例如 `"status" | "total"` 得到 `ReportRow["status"] | number`。只有 `K = keyof ReportRow` 时才覆盖全部字段，本例的结果为 `string | number`。泛型约束保证编译器看到的键有效，不在运行时校验键或行数据。

### 怎样让分页与仓储接口为不同数据复用？

泛型也可把类型关系保留在对象结构和一组操作中。报表页面拿到 `ReportPage<ReportRow>`，下游仍知道 `rows` 里的每一项是报表行；同一容器也能装其他数据，而不必退化成 `unknown[]` 或 `any[]`。

~~~typescript
type ReportPage<T> = {
  rows: T[];
  total: number;
  nextCursor: string | null;
};

interface Repository<T> {
  getById(id: string): T | undefined;
  getAll(): T[];
  save(item: T): void;
}

function firstRow<T>(page: ReportPage<T>): T | undefined {
  return page.rows[0];
}

const reports: ReportPage<ReportRow> = {
  rows: [row],
  total: 1,
  nextCursor: null
};
const emptyPage: ReportPage<ReportRow> = {
  rows: [],
  total: 0,
  nextCursor: null
};
const first = firstRow(reports);
if (first) first.total.toFixed(2); // first.total 仍是 number
console.log(firstRow(emptyPage)); // undefined：空页没有第一行
~~~

`reports` 的类型是 `ReportPage<ReportRow>`；传给 `firstRow<T>` 时，参数形状让编译器推断 `T = ReportRow`，因此 `first` 是 `ReportRow | undefined`。`Repository<ReportRow>` 也把同一个 `T` 替换到每个操作：`getById` 返回 `ReportRow | undefined`，`getAll` 返回 `ReportRow[]`，`save` 接收 `ReportRow`。

泛型保留的是编译器掌握的关系；它不会在运行时检查服务器是否真的返回 `ReportRow`。来自网络或存储的外部输入应先保持为 `unknown` 并逐项验证，见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。工具类型则可进一步从 `ReportRow` 派生列表预览或更新请求形状，见[怎样从报表类型派生数据形状并约束方法中的 `this`？](#47.%20%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%8A%A5%E8%A1%A8%E7%B1%BB%E5%9E%8B%E6%B4%BE%E7%94%9F%E6%95%B0%E6%8D%AE%E5%BD%A2%E7%8A%B6%E5%B9%B6%E7%BA%A6%E6%9D%9F%E6%96%B9%E6%B3%95%E4%B8%AD%E7%9A%84%20this%EF%BC%9F)。

> [!info]- 来源
> - [TypeScript Handbook：泛型与类型参数推断](https://www.typescriptlang.org/docs/handbook/2/generics.html)
> - [TypeScript Handbook：`keyof` 类型操作符](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)、[索引访问类型](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
>
> 来源核对日期：2026-11-12。代码以 TypeScript 5.7.2 执行严格模式和 `noUncheckedIndexedAccess` 检查。
## 47. 怎样从报表类型派生数据形状并约束方法中的 `this`？

列表预览和局部更新可以从 `ReportRow` 派生；状态标签使用与 `ReportRow.status` 共用的 `ReportStatus`，避免两处状态定义漂移。对象字面量中的方法也需要知道调用接收者有哪些字段：`ThisType<T>` 或显式的 `this` 参数能提供编译期上下文。工具类型只影响静态检查，不会投影或验证运行时数据，也不会替方法绑定接收者；不可信的外部输入应在数据边界执行运行时检查。

### 哪些工具类型适合哪些数据形状？

下面用 `Pick` 从 `ReportRow` 选出列表预览字段，用 `Partial` 把允许编辑的字段变为可选项；`Record` 则为共享的 `ReportStatus` 联合要求每个状态都有标签。

~~~typescript
type ReportStatus = "open" | "published" | "archived";

interface ReportRow {
  id: string;
  title: string;
  month: string;
  region: string;
  status: ReportStatus;
  total: number;
  ownerEmail: string;
}

type ReportPreview = Pick<ReportRow, "id" | "title" | "month" | "total">;
type ReportPatch = Partial<Pick<ReportRow, "title" | "region">>;
type StatusLabels = Record<ReportStatus, string>;

const labels: StatusLabels = {
  open: "待审核",
  published: "已发布",
  archived: "已归档"
};

const input = { region: "north", ownerEmail: "ada@example.com" };
const patch: ReportPatch = input;
console.log(Object.keys(patch)); // ["region", "ownerEmail"]：仍是同一个运行时对象
~~~

`Partial<Pick<ReportRow, "title" | "region">>` 从内向外展开为 `{ title?: string; region?: string }`。示例变量 `input` 含有共同键 `region`，所以它可赋给这个部分类型；多出的 `ownerEmail` 仍留在同一个运行时对象中。若变量只有 `ownerEmail`，则与目标类型没有共同属性而不能赋值；直接把含 `ownerEmail` 的新对象字面量赋给 `ReportPatch` 也会触发多余属性检查。`Pick` 只筛选静态声明的字段，列表展示若需要实际投影，仍须在运行时构造新对象。

`ReportStatus` 增加 `"scheduled"` 后，`labels` 会因缺少该键而报错，提醒界面补上新状态。当前 `ReportPatch` 的字段是可选 `string`；在示例所用的 `strictNullChecks` 下，显式写入 `null` 不通过检查。只有当接口把 `null` 定义为清空字段等业务操作时，才应在对应属性类型中加入 `| null`，并让运行时边界按该语义解析。启用 `exactOptionalPropertyTypes`（要求 `strictNullChecks`）时，可选字段可以省略，但不能显式写 `undefined`，除非其类型包含 `undefined`；未启用时，编译器允许把 `undefined` 赋给可选字段。无论开关如何，读取 `patch.title` 都可能得到 `undefined`，因为属性可以缺席。

接收网络或存储中的更新数据时，运行时仍要按接口白名单检查字段，并区分省略、`null` 和具体值。这个检查针对不可信输入；本地按 `ReportPatch` 构造的对象仍由编译器检查。

常用变换可按目的理解：

| 需要 | 工具类型 | 结果与边界 |
|---|---|---|
| 列表类型只声明所需字段 | `Pick<T, K>` / `Omit<T, K>` | 选取或排除键；不会复制或投影对象 |
| 表达部分更新或完成默认值后的完整配置 | `Partial<T>` / `Required<T>` | 属性变为可选或必需；运行时仍需合并、检查 |
| 标出只读视图 | `Readonly<T>` | 浅层地禁止通过该类型重新赋值属性；不冻结对象 |
| 给一组键创建映射 | `Record<K, V>` | 约束对象键和值的类型；动态输入仍须验证 |
| 从联合类型中筛选成员 | `Exclude<U, X>` / `Extract<U, X>` | 移除或保留可赋给指定类型的成员 |
| 排除 `null` 与 `undefined` | `NonNullable<T>` | 仅改变静态类型，不会替值做空值检查 |
| 读取函数签名 | `Parameters<F>` / `ReturnType<F>` | 得到参数元组或返回类型；对重载函数取最后一个签名 |
| 读取构造签名 | `ConstructorParameters<C>` / `InstanceType<C>` | 得到构造参数元组或实例类型 |
| 解开 Promise 返回类型 | `Awaited<T>` | 递归解包 Promise 及兼容其 `then` 约定的类型；不会等待运行时值 |

这些工具大多通过 mapped type（映射类型）、conditional type（条件类型）或索引访问组合实现。阅读 `Partial<Pick<ReportRow, "title" | "region">>` 时，先用 `Pick` 取两个允许编辑的字段，再用 `Partial` 将它们变为可选；前文已展开其具体对象形状。

### 条件类型遇到联合类型时，为什么会逐项筛选？

条件类型（conditional type）若在被检查的位置直接写类型参数，例如 `T extends X`，传入联合类型时会把联合成员逐个代入条件。`Exclude` 就利用这个规则：成员可赋给排除类型时变成 `never`，剩余成员再组成联合。

~~~typescript
type WithoutArchived<T> = T extends "archived" ? never : T;
type VisibleStatus = WithoutArchived<ReportStatus>;
// "open" | "published" | never -> "open" | "published"

const visibleStatus: VisibleStatus = "published";
// @ts-expect-error "archived" 已被筛掉
const archivedStatus: VisibleStatus = "archived";

type IsArchived<T> = T extends "archived" ? true : false;
type DistributedCheck = IsArchived<ReportStatus>; // true | false -> boolean
const distributedTrue: DistributedCheck = true;
const distributedFalse: DistributedCheck = false;

type IsWholeUnionArchived<T> = [T] extends ["archived"] ? true : false;
type WholeStatusCheck = IsWholeUnionArchived<ReportStatus>; // false
const wholeStatusCheck: WholeStatusCheck = false;
// @ts-expect-error 整个 ReportStatus 联合并非全是 "archived"
const wholeStatusTrue: WholeStatusCheck = true;
~~~

`WithoutArchived<ReportStatus>` 会得到 `"open" | "published" | never`，而 `never` 没有可取值，所以结果只剩前两种状态。两个布尔条件使用相同的分支：裸 `T` 分配后得到 `true | false`（也就是 `boolean`）；把 `T` 包在元组中则比较整个联合，结果为 `false`。同样，`Exclude<ReportStatus, "archived">` 与 `VisibleStatus` 一样得到剩余状态。

### 对象字面量方法里的 `this` 怎样获得上下文类型？

`ThisType<T>` 是一个 contextual typing marker（上下文类型标记），可让对象字面量中的方法把 `this` 看作 `T`。它不会添加属性、绑定运行时接收者或改变对象；检查依赖 `noImplicitThis`。

~~~typescript
type ObjectDescriptor<Data, Methods> = {
  data: Data;
  methods: Methods & ThisType<Data & Methods>;
};

function makeObject<Data, Methods>(
  descriptor: ObjectDescriptor<Data, Methods>
): Data & Methods {
  return { ...descriptor.data, ...descriptor.methods };
}

const rowCounter = makeObject({
  data: { loadedRows: 0 },
  methods: {
    addLoadedRow() {
      this.loadedRows += 1; // 此处 this 有 loadedRows: number
    }
  }
});

rowCounter.addLoadedRow();
console.log(rowCounter.loadedRows); // 1
~~~

调用 `makeObject` 时，编译器从 `data` 推断 `Data = { loadedRows: number }`，从 `methods` 推断含 `addLoadedRow` 的 `Methods`；`ThisType<Data & Methods>` 再把两个对象的成员提供给方法体中的 `this`。返回表达式在运行时通过对象展开合并两个对象，再由 `rowCounter.addLoadedRow()` 的成员调用提供接收者，计数随后变为 1。这个小例只适用于数据和方法都是普通对象且所需成员是可枚举自有属性的情况；从原型继承的方法不会被对象展开复制。`Data & Methods` 本身不会禁止两个输入对象有重名键；重名时后展开的 `methods` 会覆盖 `data`，而交叉类型仍可能描述冲突字段。本例保持两边键名不重叠。

另一个做法是在普通函数签名中显式声明接收者：

~~~typescript
interface ReportViewer {
  name: string;
  describe(this: ReportViewer): string;
}

const viewer: ReportViewer = {
  name: "Ada",
  describe() { return `报表查看者：${this.name}`; }
};

console.log(viewer.describe()); // 报表查看者：Ada
~~~

`this: ReportViewer` 只是编译期接收者注解；调用 `viewer.describe()` 时仍由普通 JavaScript 成员调用提供 `this`。`ThisType<T>` 也只影响方法体中的静态检查，不会替你调用 `bind`。单独取出 `viewer.describe` 后直接调用，会因缺少显式接收者而报类型错误；单独取出 `rowCounter.addLoadedRow` 后直接调用可能通过静态检查，但运行时仍需要正确的接收者。如果 `ReportPatch` 来自网络或存储，需在该输入边界挑选并验证字段；类型工具不会过滤其运行时键。解析入口见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。

> [!info]- 来源
> - [TypeScript Utility Types 参考](https://www.typescriptlang.org/docs/handbook/utility-types.html)
> - [TypeScript Handbook：映射类型](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)、[条件类型](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)、[上下文类型](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)
> - [TSConfig：`exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html)
>
> 来源核对日期：2026-11-12。示例以 TypeScript 5.7.2、`strict` 模式、`noImplicitThis` 及文中说明的精确可选属性设置检查。
## 48. 项目使用哪种 TypeScript 装饰器模式？

报表服务可能要给方法加日志、缓存或指标统计。decorator（装饰器）在类或类成员定义时调用，可以替换被装饰的定义；本文聚焦方法装饰器。TypeScript 5.0 起可使用新版（提案）模式；`experimentalDecorators` 选择旧版（legacy）模式。两者的调用参数、可修饰位置和元数据配置不同，不能把一种模式的装饰器直接贴到另一种项目里。

| 模式与配置边界 |
|---|
| 新模式（TypeScript 5.0 起）：有效配置未启用 `experimentalDecorators`；新版**方法**装饰器收到原方法函数和上下文对象，可返回替代方法。不能装饰参数，也不能使用 `emitDecoratorMetadata`。字段装饰器的第一个参数是 `undefined`，调用约定并非所有成员相同。 |
| 旧模式（legacy）：有效配置设置 `experimentalDecorators: true`；方法装饰器收到 `target`、属性键和描述符。可使用参数装饰器；若框架要读取 TypeScript 生成的设计类型元数据，再按其要求启用 `emitDecoratorMetadata` 并加载 `reflect-metadata`。 |

TypeScript 5.0 的无标志模式采用 TC39 新装饰器提案的调用约定，常被称为“标准装饰器”以区别旧版实现；截至 2026-11-12，TC39 当前提案列表仍标为 Stage 2.7，尚未完成标准化。因此这里的“新版/标准”说明 TypeScript 的模式边界，不表示提案已成为正式 ECMAScript 标准。

### 新版方法装饰器怎样保留原方法的签名？

TypeScript 5.0 引入了不依赖 `experimentalDecorators` 的新版装饰器实现。执行类定义时，`@loggedMethod` 收到当前的 `loadMonth` 函数和方法上下文；它返回的包装函数会被安装为 `ReportService.prototype.loadMonth`。创建 `ReportService` 实例时不会因此记录日志；稍后调用 `service.loadMonth(...)` 才进入包装函数，日志后它用同一个 `this` 和参数调用原方法，再把原方法的返回值交还调用方。下面的 generic（泛型）保留这项转发的接收者、参数元组和返回值类型。

~~~typescript
function loggedMethod<This, Args extends unknown[], Return>(
  original: (this: This, ...args: Args) => Return,
  context: ClassMethodDecoratorContext<
    This,
    (this: This, ...args: Args) => Return
  >
) {
  const name = String(context.name);

  return function (this: This, ...args: Args): Return {
    console.log("报表方法调用：", name);
    return original.call(this, ...args);
  };
}

class ReportService {
  @loggedMethod
  async loadMonth(month: string): Promise<string[]> {
    return [`${month} 报表已加载`];
  }
}

const service = new ReportService();
void service.loadMonth("2026-10")
  .then(rows => console.log(rows));
// 先记录“报表方法调用： loadMonth”。
// Promise 完成后输出 ["2026-10 报表已加载"]。
~~~

源代码中的 `@` 不一定会原样出现在输出 JavaScript：编译器或构建器可能把它转换为运行时辅助代码；若构建流水线保留装饰器语法，目标运行时就必须支持相应语法和语义。应检查实际构建产物，而不能只凭 TypeScript 源文件判断。

### 旧版方法装饰器为什么不能沿用同一签名？

开启 `experimentalDecorators` 后，旧版方法装饰器接收原型或构造函数、属性键和属性描述符。下面装饰的是实例方法，所以 `target` 是类原型；`descriptor.value` 是 `loadMonth` 当前的方法函数槽位。装饰器把包装函数写回该槽位，TypeScript 的旧版装饰器运行时代码随后将更新后的描述符应用回原方法。许多既有框架依赖此约定，也可能使用参数装饰器或 `emitDecoratorMetadata`。

~~~typescript
function legacyLog(
  target: object,
  key: string | symbol,
  descriptor: PropertyDescriptor
) {
  const original = descriptor.value;
  descriptor.value = function (
    this: unknown, ...args: unknown[]
  ) {
    console.log("旧版报表方法调用：", key);
    return original.apply(this, args);
  };
}

class LegacyReportService {
  @legacyLog
  loadMonth(month: string): string {
    return `${month} 报表已加载`;
  }
}

const legacyService = new LegacyReportService();
console.log(legacyService.loadMonth("2026-10"));
// 依次记录“旧版报表方法调用： loadMonth”和“2026-10 报表已加载”。
~~~

要判断现有文件采用哪种模式，应查看**实际编译该文件的项目配置**。使用 `tsc` 时，可运行 `tsc -p path/to/tsconfig.json --showConfig` 查看合并 `extends` 后的有效值；TypeScript 5.0 起，有效的 `experimentalDecorators: true` 表示旧版，否则是新版。多配置仓库要选实际参与构建的配置；若另一个构建器还会转换装饰器，则再检查它的配置和最终 JavaScript 产物。

这两个例子都只是在方法调用周围加日志；它们不会验证网络响应，也不会证明调用者有查看报表的权限。需要在不可信数据入口检查实际值时，使用[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。选择新版或旧版装饰器后，继续核对[ECMAScript 模块与 CommonJS 的加载边界](#49.%20ECMAScript%20%E6%A8%A1%E5%9D%97%E4%B8%8E%20CommonJS%EF%BC%88Node.js%20%E6%A8%A1%E5%9D%97%E6%A0%BC%E5%BC%8F%EF%BC%89%E5%9C%A8%E8%AF%AD%E6%B3%95%E3%80%81%E5%8A%A0%E8%BD%BD%E5%92%8C%E8%BF%90%E8%A1%8C%E6%97%B6%E6%9C%89%E4%BB%80%E4%B9%88%E4%B8%8D%E5%90%8C%EF%BC%9F)。

> [!info]- 来源
> - [TypeScript 5.0 发布说明：新版装饰器及其与旧版的差异](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators)
> - [TypeScript TSConfig：`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/experimentalDecorators.html)、[`emitDecoratorMetadata`](https://www.typescriptlang.org/tsconfig/emitDecoratorMetadata.html)
> - [TC39 装饰器提案](https://github.com/tc39/proposal-decorators)、[TC39 当前提案阶段列表](https://github.com/tc39/proposals)
>
> 提案阶段按 2026-11-12 的当前列表核对。示例以 TypeScript 5.7.2 分别按无 `experimentalDecorators` 的新版模式和 `experimentalDecorators: true` 的旧版模式严格编译；`target: ES2022` 的产物已在 Node v26.13.0 运行，`target: ESNext` 是否保留 `@` 也已检查。
## 49. ECMAScript 模块与 CommonJS（Node.js 模块格式）在语法、加载和运行时有什么不同？

**案例背景。** 本章使用合成的月报页面。把数据读取、数字格式化和页面入口拆到不同文件后，写下 `import` 并不等于浏览器或 Node.js 已经知道去哪找文件。读者要分清三层：ECMAScript module（ECMAScript 模块，ESM）语法声明依赖与导出；宿主（浏览器或 Node.js）依各自规则定位、加载并执行文件；bundler（打包器）还能在构建时改写依赖图。下面沿报表页面从入口到数据响应，再切换到 Node.js 模块格式，追踪每一层接手的输入和交出的结果。

| 这一层 | 它决定什么 | 报表例子 |
| --- | --- | --- |
| ECMAScript 模块语法 | 哪些名字被导入、导出；依赖属于静态声明还是运行时请求 | `import { loadReport } from ...` |
| 宿主（浏览器或 Node.js） | 文件格式、模块说明符解析、读取/下载、执行环境 | 浏览器 URL 与 import map；Node.js 文件扩展名与包配置 |
| bundler（打包器） | 构建时怎样解析、转换、拆分并优化产物 | 可能保留 ESM、改成 CommonJS，或输出浏览器脚本 |

### ESM 静态导入怎样描述报表模块之间的依赖？

ECMAScript 2015（ES2015）定义了这种模块格式。static import（静态导入）与 `export` 声明依赖和公开名称；它们不规定浏览器要发哪个 HTTP 请求，也不规定 Node.js 要用哪个文件系统路径。静态依赖在模块代码运行前就能从语法结构中识别，因此宿主可先建立 module graph（模块图），再把导入名连到导出绑定。

下面的浏览器入口需要 HTML 和四个模块文件：让本地 HTTP 服务器以 `examples/browser/` 为文件根目录，并把 JavaScript 文件作为 `text/javascript` 返回，因为浏览器模块脚本要求 JavaScript MIME 类型；页面先加载 `reports/report-page.js`，import map（导入映射表）把 `@reports/` 指向同源 `reports/` 目录，入口再用相对说明符导入读取函数、用映射名导入格式化函数。服务器让 `/api/reports?month=2026-10` 返回含有限数值 `total: 1200` 的 JSON，页面便从“读取中”更新为 `1,200`。经典脚本的独立支线会另取 `lazy-tip.js` 并打印提示。模块不能从 `file:` 路径直接这样加载；入口用 top-level await（顶层 await，ES2022）等待读取结果。

**文件：** `examples/browser/index.html`

~~~html file=examples/browser/index.html
<!doctype html>
<meta charset="utf-8">
<title>报表</title>
<p>本月总额：<output id="total">读取中</output></p>
<script type="importmap">
{
  "imports": {
    "@reports/": "./reports/"
  }
}
</script>
<script type="module" src="./reports/report-page.js"></script>
<script>
  // 经典脚本不能写静态 import，但可以按需调用 import()。
  import("./lazy-tip.js").then(({ message }) => console.log(message()));
</script>
~~~

**文件：** `examples/browser/reports/report-page.js`

~~~javascript file=examples/browser/reports/report-page.js
import { loadReport } from "./report-api.js";
import formatTotal from "@reports/report-format.js";

const result = await loadReport("2026-10");
if (!result || !Number.isFinite(result.total)) {
  throw new TypeError("报表响应必须包含数值 total");
}
document.querySelector("#total").textContent = formatTotal(result.total);
~~~

**文件：** `examples/browser/reports/report-api.js`

~~~javascript file=examples/browser/reports/report-api.js
export async function loadReport(month) {
  // 当前页面没有跨源 <base>，所以此地址仍指向本地站点。
  const requestUrl = `/api/reports?month=${encodeURIComponent(month)}`;
  const response = await fetch(requestUrl);
  if (!response.ok) throw new Error(`报表请求失败：${response.status}`);
  return response.json();
}
~~~

**文件：** `examples/browser/reports/report-format.js`

~~~javascript file=examples/browser/reports/report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}
~~~

**文件：** `examples/browser/lazy-tip.js`

~~~javascript file=examples/browser/lazy-tip.js
export function message() {
  return "按需模块已加载";
}
~~~

| 模块步骤 | 输入与操作 | 输出 |
| --- | --- | --- |
| 定位入口 | HTML 解析到模块脚本后，按文档 base URL（基准 URL）定位并取回 `report-page.js` | 入口模块源代码 |
| 解析与取回依赖 | 读取入口的静态 `import`；相对说明符按导入者 URL 解析，`@reports/` 用 import map 解析；再递归处理各依赖的静态导入。浏览器会并行取回已发现的模块，但不会一次知道整个图 | `report-api.js`、`report-format.js` 等依赖模块源代码；跨源模块还须通过 Cross-Origin Resource Sharing（跨源资源共享，CORS） |
| 链接 | 将各模块的导入名连到目标模块的导出绑定，并检查名字是否存在 | 绑定已连接；名字不匹配时模块代码不会开始求值 |
| 求值 | 按模块图执行依赖，再执行入口；本例入口的顶层 await 等待 API 响应 | 数据检查通过后，入口把格式化结果写入 `output` |

链接不等于变量已经有值：若导出方的 `let` / `const` 绑定尚未初始化，提前读取仍会抛出 `ReferenceError`。本例没有循环依赖，先完成依赖求值才执行入口；循环中的提前读取与[作用域中的暂时性死区](#32.%20JavaScript%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E7%8A%B6%E6%80%81%EF%BC%9F)遵循同一初始化边界。

入口中的 `loadReport` 是 named export（命名导出），名称要与导入列表对应；`formatTotal` 是 default export（默认导出），导入方可自选本地名字。单个模块最多有一个默认导出，也可以同时有多个命名导出；导入方可用 `as` 为命名导入另取本地名字。API 响应经 `response.json()` 得到的是运行时数据；JavaScript 不会因为变量名或 TypeScript 类型声明就替服务端验证结构，TypeScript 类型也不会凭空成为 JavaScript 运行时导出，所以入口显式检查 `total` 是数值后才格式化。

若没有 `type="importmap"`，浏览器不能仅凭 `@reports/report-format.js` 猜测 Node Package Manager（npm）的包目录；映射表为 bare module specifier（裸模块说明符）提供目标 URL。相对导入则相对当前导入者的模块 URL 解析。HTML 中入口的 `src` 相对文档 base URL（基准 URL）解析。浏览器里的 `fetch("/api/...")` 也按当前 Window 环境的 API base URL 解析；它通常是文档 base URL，而文档若含跨源 `<base href>`，根相对路径会落到该 base 所在源，不一定与页面源相同；此时请求也受 CORS 限制。本例没有 `<base>`，所以请求落在提供页面的本地站点。Node.js 的 `fetch()` 没有浏览器文档基准，直接传 `"/api/..."` 会因缺少绝对基准 URL 而失败。模块文件定位与应用数据请求不要混作一回事。

导入会建立到导出绑定的连接（live binding，实时绑定），而不是在导入时复制一个值。导入方可以读取导出方之后写入的值，但不能直接给导入名赋值。下面两个文件演示读取同一绑定在更新前后的当前值：`before` 是普通变量，保存第一次读到的字符串；再次读取 `selectedMonth` 才会得到更新后的字符串。

**文件：** `examples/esm-binding/month-state.js`

~~~javascript file=examples/esm-binding/month-state.js
export let selectedMonth = "2026-10";

export function selectNextMonth() {
  selectedMonth = "2026-11";
}
~~~

**文件：** `examples/esm-binding/read-month.js`

~~~javascript file=examples/esm-binding/read-month.js
import { selectedMonth, selectNextMonth } from "./month-state.js";

const before = selectedMonth;
selectNextMonth();
console.log(JSON.stringify([before, selectedMonth]));
// selectedMonth = "2026-12"; // 导入绑定不能由此模块写入
~~~

默认导出也只是 ESM 公开接口的一种写法，不代表模块本身只返回一个值。ESM 可以保留一个明确的默认名称，同时具名暴露其他能力：

**文件：** `examples/esm-binding/report-format.js`

~~~javascript file=examples/esm-binding/report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}

export function formatMonth(month) {
  return month.replace("-", "年") + "月";
}
~~~

**文件：** `examples/esm-binding/use-format.js`

~~~javascript file=examples/esm-binding/use-format.js
import formatTotal, {
  formatMonth as monthLabel,
} from "./report-format.js";

console.log(JSON.stringify([monthLabel("2026-10"), formatTotal(1200)]));
// ["2026年10月","1,200"]
~~~

静态 `import` 声明必须位于模块顶层，不适合放进条件分支；要按用户选择延后读取某项功能，可用 dynamic import（动态导入）`import()`。它在调用处发起异步模块加载并返回 Promise，成功后兑现为模块命名空间对象；同一宿主此前已加载的模块可能被复用，因此调用不保证每次都重新取回文件。它不是静态导入声明。浏览器经典脚本、Node.js CommonJS 和 ESM 都可以调用动态导入，但是否被 bundler 拆成独立 chunk（代码块）取决于构建配置。

**文件：** `examples/esm-binding/load-optional.js`

~~~javascript file=examples/esm-binding/load-optional.js
export async function loadOptionalReport(shouldOpen) {
  if (!shouldOpen) return null;
  const { renderChart } = await import("./optional-chart.js");
  return renderChart();
}
~~~

**文件：** `examples/esm-binding/optional-chart.js`

~~~javascript file=examples/esm-binding/optional-chart.js
export function renderChart() {
  return "图表已加载";
}
~~~

ES2022 起，ESM 顶层可以使用 `await`。浏览器示例中的 `report-page.js` 在顶层等待数据；在本文无环依赖图中，依赖它的导入者要等它成功完成后才开始执行自己的模块体。独立依赖分支仍可继续求值。Promise continuation 与其他任务在事件循环中的顺序见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)。

#### 目录入口怎样重新导出一个模块的公开接口？

barrel（聚合导出模块）是用 `export` 转发其他模块接口的 ESM 文件。它把报表目录要公开的名称集中到一个入口，不会自动创建组件、切换宿主或保证减少最终文件：

**文件：** `examples/barrel/reports/index.mjs`

~~~javascript file=examples/barrel/reports/index.mjs
export { ReportTable } from "./ReportTable.mjs";
export { ReportToolbar } from "./ReportToolbar.mjs";
~~~

**文件：** `examples/barrel/ReportsPage.mjs`

~~~javascript file=examples/barrel/ReportsPage.mjs
import { ReportTable, ReportToolbar } from "./reports/index.mjs";

console.log(JSON.stringify([ReportTable.name, ReportToolbar.name]));
~~~

**文件：** `examples/barrel/reports/ReportTable.mjs`

~~~javascript file=examples/barrel/reports/ReportTable.mjs
export class ReportTable {}
~~~

**文件：** `examples/barrel/reports/ReportToolbar.mjs`

~~~javascript file=examples/barrel/reports/ReportToolbar.mjs
export class ReportToolbar {}
~~~

导出列表应有意挑选，避免无意公开内部模块。内部模块若又从同一聚合入口导入彼此，依赖图可能形成循环；同目录实现通常直接导入具体文件更清楚。若多个 `export *` 路径导出同名但指向不同绑定，该名称会有歧义；若它们最终解析到同一绑定，则不因此产生歧义。显式重导出或改名可让接口意图更清楚。barrel 仍会静态依赖被重导出的模块；最终可以删掉哪些未用代码，还取决于打包器怎样分析导出与副作用，见下文的 tree shaking（摇树优化）。

### CommonJS 与 ESM 的加载和文件识别有什么区别？

CommonJS（Node.js 模块格式，简称 CJS）是 Node.js 的包装函数与 `require()` / `module.exports` 机制；它不是另一套 ECMAScript 语言规范。ESM 在浏览器与 Node.js 都有模块语法，但文件解析、资源定位、取回规则仍由宿主决定。先看语言层面的差异，再分别看浏览器执行模式和 Node.js 文件格式，才能判断相同一行代码在哪个环境成立。

| 关注点 | ESM | CJS（Node.js） |
| --- | --- | --- |
| 导入与导出 | 静态 `import`、`export`；也可调用 `import()` | `require()` 运行时导入，`module.exports` 导出；也可调用 `import()` |
| 顶层 `this` | `undefined` | 包装函数最初收到的 `exports` 对象 |
| strict mode（严格模式） | 自动启用 | 默认不启用；文件可写 `"use strict"` |
| 顶层 `await` | 支持 | CJS 源文件不能直接使用；`import()` 可以加载异步 ESM |
| 解析者 | 浏览器或 Node.js 宿主 | Node.js 或构建工具 |

这里的 `require()` 是代码运行到调用表达式时才同步执行；静态 `import` 则在模块体运行前建立依赖。`import()` 是运行时异步加载，不会改变当前 CJS 文件格式。Node.js 26 另允许 `require()` 同步加载没有顶层 `await` 的 ESM 依赖图；这一互操作边界稍后单独核对。

#### 浏览器 classic script（经典脚本）与 module script（模块脚本）

| 脚本类型与加载 | 顶层代码环境 |
| --- | --- |
| 经典脚本 `<script>`：不能写静态 `import` / `export`，但可调用 `import()`。普通外部脚本在解析器遇到时暂停 HTML 解析，直到取回并执行；`async` 并行取回、完成后尽快执行；`defer` 并行取回，在文档解析后按顺序执行。 | 多个经典脚本在同一页面全局环境中运行；顶层 `this` 是页面全局 `this`。顶层 `var` 可成为 `window` 属性；`let` / `const` 是全局词法绑定。 |
| 模块脚本 `<script type="module">`：随 HTML 解析取回入口，并逐步发现、并行取回静态依赖；默认在文档解析完成后求值，`async` 在模块图就绪后可提前执行，`defer` 不改变时机。跨源模块请求需通过 CORS；裸模块说明符须由 import map 映射。 | 每个模块有自己的模块环境；模块自动处于 strict mode，顶层 `this` 为 `undefined`，顶层 `var` / `let` / `const` 不成为 `window` 属性。 |

两行分别对应 `<script>` 与 `<script type="module">`。两种脚本共用 JavaScript 引擎，但脚本类型会改变解析语法、名称环境和执行调度。把 `type="module"` 去掉，不只是改了请求方式：静态 `import` 语法也不再属于有效的经典脚本。

#### Node.js 怎样判定文件格式与解析说明符？

Node.js 同时支持 CJS 与 ESM。以下规则对应 Node.js 26.13.x；当模块加载器变化时，应按部署的 Node 主版本复核。

| 文件标记 | Node.js 处理格式 |
| --- | --- |
| `.mjs` | 总是按 ESM 处理 |
| `.cjs` | 总是按 CJS 处理 |
| `.js`，最近的 `package.json` 写有 `"type": "module"` | 按 ESM 处理 |
| `.js`，最近的 `package.json` 写有 `"type": "commonjs"` | 按 CJS 处理 |
| 没有显式格式标记的歧义 `.js` | Node 26 默认进行语法探测；源码含在 CJS 包装器中无法成立的语法时按 ESM 处理，否则按 CJS 处理。单独的 `import()` 可留在 CJS |

显式包类型示例：

**文件：** `examples/esm-binding/package.json`

~~~json file=examples/esm-binding/package.json
{
  "type": "module"
}
~~~

syntax detection（语法探测）在 Node.js 22.7.0 与 20.19.0 起默认开启；Node.js 26.13.1 官方文档仍标为 Release candidate（候选稳定阶段），并指出对歧义文件扫描语法会有额外开销。它会识别静态 `import` / `export`、`import.meta`、顶层 `await`，以及对包装器参数的顶层词法重声明（例如 `const require = 1`）等无法作为 CJS 执行的语法；`import()` 表达式也可用于 CJS，因此单独出现 `import()` 不会把 `.js` 文件改判为 ESM。新项目应在最近的 `package.json` 明确写 `"type"`，或使用 `.mjs` / `.cjs`，让宿主和构建工具不必猜测。

`require()` 走 CommonJS 的解析与同步调用路径；Node.js 26 满足条件时也可通过它同步加载 ESM。`import()` 走 ESM 的加载路径。CommonJS 的相对 `require()` 从当前文件出发解析，支持扩展名补全和目录/包入口；Node ESM 的相对路径也从导入者位置解析，但要求写出扩展名，也不能省略目录的 `index.js`。裸包名在 Node 中按 Node 的包查找规则解析，并可能受 `package.json` 的 `exports` 映射限制；浏览器则用 URL 和 import map。`fetch()` 又是应用发出的数据请求，不能因文件用了 ESM 就期待 Node 把 `"/api/..."` 自动补成某个服务器地址；Node 侧应传绝对 URL，或用已知的 API 基址创建 `new URL("/api/...", base)`。

#### CJS 包装函数如何影响顶层绑定与 this？

Node.js 会把每个 CJS 文件的内容放进类似下面的函数包装器中执行，并把 `exports`、`require`、`module`、`__filename` 与 `__dirname` 作为局部参数提供。月报税前金额 `100` 与税率 `0.08` 经 `read-math.cjs` 调用后得到 `108`。`exports` 起初只是与 `module.exports` 指向同一对象的局部快捷变量，因此给 `exports.totalWithTax` 赋属性会公开这个函数；重新给 `exports` 赋新值只改局部变量，替换模块导出必须给 `module.exports` 赋值。下例是真正可运行的 `.cjs` 文件：

**文件：** `examples/node-commonjs/math.cjs`

~~~javascript file=examples/node-commonjs/math.cjs
const taxRate = 0.08;

exports.totalWithTax = function totalWithTax(net) {
  return net * (1 + taxRate);
};
~~~

**文件：** `examples/node-commonjs/read-math.cjs`

~~~javascript file=examples/node-commonjs/read-math.cjs
const math = require("./math.cjs");
console.log(math.totalWithTax(100)); // 108
~~~

**文件：** `examples/node-commonjs/replace-exports.cjs`

~~~javascript file=examples/node-commonjs/replace-exports.cjs
const initialExports = this;
exports = { ignored: true };
const shortcutDidNotReplace = module.exports === initialExports;
module.exports = { replaced: true };
const pointsToInitial = this === initialExports;
const pointsToReplacement = this === module.exports;
const checks = [
  shortcutDidNotReplace,
  pointsToInitial,
  pointsToReplacement,
];
console.log(JSON.stringify(checks));
// [true,true,false]
~~~

把同一段赋值按时间排开，引用关系更容易看清。令 A 是初始导出对象，B 是 `{ ignored: true }`，C 是 `{ replaced: true }`：

| 时刻 | 局部 `exports` | `module.exports` | 顶层 `this` |
|---|---|---|---|
| 包装器刚开始执行 | A | A | A |
| 执行 `exports = B` 后 | B | A | A |
| 执行 `module.exports = C` 后 | B | C | A |

最终 `require()` 交给调用者的是 C；改变局部变量或替换模块导出，都不会把已经固定的顶层 `this` 改成 C。

`taxRate` 只在这个包装函数里可见。包装函数最初收到的 `exports` 对象同时是顶层 `this`；`replace-exports.cjs` 把 `module.exports` 换成另一个对象后，顶层 `this` 仍指向初始对象。ESM 不使用这个包装器：顶层声明是模块绑定，顶层 `this` 为 `undefined`，而模块自动处在严格模式。

#### `require()` 第一次调用怎样执行模块，第二次又返回什么？

CJS 的 `require()` 是运行到调用处时才执行的同步调用表达式，可放在条件或函数里；它不是静态依赖声明。普通无环首次加载时，Node 解析目标文件、执行包装函数，完成后把当时的 `module.exports` 值交回调用者。之后再次 `require()` 同一解析文件时，Node 不重新执行模块体，而是从缓存的模块记录读取此刻的 `module.exports`；若它未被替换，本例才会再次得到同一个对象。下例让已返回的对象把模块导出替换为另一个对象：

**文件：** `examples/node-commonjs/load-once.cjs`

~~~javascript file=examples/node-commonjs/load-once.cjs
console.log("module evaluated");
const october = { month: "October" };
module.exports = october;
october.replace = () => {
  module.exports = { month: "November" };
};
~~~

**文件：** `examples/node-commonjs/use-cache.cjs`

~~~javascript file=examples/node-commonjs/use-cache.cjs
console.log("before first require");
const first = require("./load-once.cjs");
console.log("after first require");
first.replace();
const second = require("./load-once.cjs");
const result = [first === second, first.month, second.month];
console.log(JSON.stringify(result));
~~~

运行 `use-cache.cjs` 时，输出顺序是调用前日志、模块体日志、首次调用返回后的日志、`[false,"October","November"]`；第二次调用没有再次打印 `module evaluated`。第一个变量仍引用旧对象，缓存中的模块记录则已指向新导出。清除缓存或解析到不同文件会改变是否命中同一项的前提。

#### Node.js 里 CJS 与 ESM 怎样互操作？

| 方向 | 规则与可依赖结果 |
| --- | --- |
| ESM 导入 CJS | CJS 的 `module.exports` 值作为默认导出；它可以是对象，也可以是数字、函数等其他值。Node 还可能从 CJS 源码静态分析出命名导出供兼容使用；该分析是启发式便利功能，不能依赖动态修改后的属性同步。 |
| CJS 用 `import()` 导入 ESM | 可异步导入，得到 Promise；适用于含顶层 `await` 的 ESM。 |
| CJS 用 `require()` 导入 ESM | Node 26 默认可同步加载没有顶层 `await` 的 ESM 依赖图，通常返回 module namespace object（模块命名空间对象）；默认导出位于 `.default`。若依赖图有顶层 `await`，抛出 `ERR_REQUIRE_ASYNC_MODULE`，改用 `import()`。 |

下面的 `.mjs` 明确没有顶层 `await`，所以 `use-modules.cjs` 可同步 `require()` 并得到命名空间对象；异步模块仍可通过 `import()` 读取。运行该文件时，第一行立即输出 `["October","1,200","legacy CJS"]`，随后显示 `ERR_REQUIRE_ASYNC_MODULE`，最后异步分支输出 `ready`。

**文件：** `examples/node-interop/modern-report.mjs`

~~~javascript file=examples/node-interop/modern-report.mjs
export const reportName = "October";
export default function formatTotal(total) {
  return new Intl.NumberFormat("en-US").format(total);
}
~~~

**文件：** `examples/node-interop/async-report.mjs`

~~~javascript file=examples/node-interop/async-report.mjs
await Promise.resolve();
export const ready = "ready";
~~~

**文件：** `examples/node-interop/legacy-report.cjs`

~~~javascript file=examples/node-interop/legacy-report.cjs
module.exports = { source: "legacy CJS" };
~~~

**文件：** `examples/node-interop/use-modules.cjs`

~~~javascript file=examples/node-interop/use-modules.cjs
const modern = require("./modern-report.mjs");
const legacy = require("./legacy-report.cjs");
const importedValues = [
  modern.reportName,
  modern.default(1200),
  legacy.source,
];
console.log(JSON.stringify(importedValues));

try {
  require("./async-report.mjs");
} catch (error) {
  console.log(error.code); // ERR_REQUIRE_ASYNC_MODULE
}

import("./async-report.mjs").then(({ ready }) => console.log(ready));
~~~

Node.js 的 ESM 默认导入 CJS 时，默认值就是 `module.exports`；这个值不保证是对象。先看上面的对象导出，再看下面把数字 `42` 直接赋给 `module.exports`、由 ESM 默认导入读取：

**文件：** `examples/node-interop/use-legacy.mjs`

~~~javascript file=examples/node-interop/use-legacy.mjs
import legacy from "./legacy-report.cjs";
console.log(legacy.source); // legacy CJS
~~~

**文件：** `examples/node-interop/number.cjs`

~~~javascript file=examples/node-interop/number.cjs
module.exports = 42;
~~~

**文件：** `examples/node-interop/use-number.mjs`

~~~javascript file=examples/node-interop/use-number.mjs
import value from "./number.cjs";
console.log(typeof value, value); // number 42
~~~

ESM 还可以显式写 `export { value as "module.exports" }`，让 CJS 的 `require()` 直接返回 `value`；这种兼容写法会替代命名空间对象，其他具名导出也不会自动并入该值。上面的 `.mjs` 默认导入直接读取 `module.exports`。ESM 导入 CJS 时，Node 会尝试从 CJS 源码静态探测部分命名导出；这是启发式互操作，不是 ECMAScript 保证。Node 先静态扫描可能的命名导出，在执行或复用 CJS 后，用当时的 `module.exports` 初始化这些命名导出的值；若 CJS 文件已被 `require()` 并修改属性，命名导入读到的是初始化这些命名导出时的值，之后的属性改动不会同步到它。这个例子先以 CJS 读出 `October`，在 ESM 导入发生前改为 `November`，导入完成后再改为 `December`：

**文件：** `examples/node-interop/mutable-month.cjs`

~~~javascript file=examples/node-interop/mutable-month.cjs
exports.month = "October";
exports.setMonth = (month) => { exports.month = month; };
~~~

**文件：** `examples/node-interop/read-month.mjs`

~~~javascript file=examples/node-interop/read-month.mjs
import legacy, { month } from "./mutable-month.cjs";
export { month };
export default legacy;
~~~

**文件：** `examples/node-interop/use-months.cjs`

~~~javascript file=examples/node-interop/use-months.cjs
const legacy = require("./mutable-month.cjs");
legacy.setMonth("November");
import("./read-month.mjs").then((namespace) => {
  const importedDefault = namespace.default;
  legacy.setMonth("December");
  console.log(JSON.stringify([importedDefault.month, namespace.month]));
});
~~~

运行该文件输出 `["December","November"]`：默认导入仍引用那个对象，因此能读到后来改成的 `December`；命名导入是在 ESM 为 CJS 初始化命名导出时取到的 `November`，不会跟着后续修改。

跨格式接口应以 Node.js 当前版本文档为准；要让应用在多个 Node 主版本或打包器间保持稳定，清晰声明文件格式并用实际目标运行时回放。

### 为什么 ESM 并不自动保证 tree shaking？

tree shaking（摇树优化）是 bundler（打包器）尝试删除未使用导出或模块的优化，不是 ESM 运行时保证。静态 `import` / `export` 让工具可以分析依赖与被引用的名字，但工具仍需判断模块执行是否有 side effect（副作用）。例如，一个已进入应用依赖图、需要靠它注册事件监听器或加载 CSS 的模块，即使没有被引用的导出，也必须保留其副作用；若包把它误标为 `sideEffects: false`，打包器可能删除该模块，导致监听器未注册或样式缺失。构建器输出的仍可能是 ESM、浏览器脚本或 CJS；最终产物由相应宿主按自己的规则加载。

barrel 能集中公开名字，但静态重导出仍会把上游纳入待分析的依赖图；它本身不保证减包。是否拆成独立 chunk、哪些未用导出能被删、怎样尊重副作用声明，都由具体构建工具、配置、包元数据和输出目标决定。开发服务器和生产构建的差异、构建器怎样生成最终产物，见[构建工具怎样把源码变成可发布产物？](#51.%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%BA%90%E7%A0%81%E5%8F%98%E6%88%90%E5%8F%AF%E5%8F%91%E5%B8%83%E4%BA%A7%E7%89%A9%EF%BC%9F)。

> [!info]- 来源
> - ECMAScript 2026 §16：静态 import/export、Module Requests、模块请求加载、链接与求值：[Scripts and Modules](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html)，其中 §16.2.1.6 说明循环模块记录与异步求值，§16.2.1.7 说明源码模块记录、导出解析与环境初始化。导入绑定及模块顶层 this：[Module Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)（§9.1.1.5，导入绑定间接读取目标绑定，模块 this 为 undefined）；ESM 严格模式：[Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)。顶层 await 自 ES2022 起进入 ECMAScript 标准。
> - WHATWG HTML Living Standard（核对日期 2026-11-12）：经典脚本与模块脚本的语法、取回和执行时机、async / defer 与模块跨源 CORS 要求：[The script element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)（§4.12.1）。
> - WHATWG HTML Living Standard（核对日期 2026-11-12）：浏览器 URL-like / bare module specifier 解析和 import map：[Module specifier resolution](https://html.spec.whatwg.org/multipage/webappapis.html#resolve-a-module-specifier)、[Import maps](https://html.spec.whatwg.org/multipage/webappapis.html#import-maps)；Window 环境的 API base URL 取文档当前 base URL，文档 base URL 可由 `<base href>` 改变：[Window script settings](https://html.spec.whatwg.org/multipage/nav-history-apis.html#script-settings-for-window-objects)、[Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)；`Request` 字符串输入按 API base URL 解析：[Fetch Standard §5.4](https://fetch.spec.whatwg.org/#dom-request)。
> - Node.js v26.13.1 官方文档：文件扩展名、最近的 package.json type、syntax detection 与显式声明格式建议：[Determining module system](https://nodejs.org/docs/v26.13.1/api/packages.html#determining-module-system)（v22.7.0 与 v20.19.0 起默认探测，Stability 1.2 — Release candidate）；CommonJS 包装器与顶层作用域：[The module wrapper](https://nodejs.org/docs/v26.13.1/api/modules.html#the-module-wrapper)；Node ESM 相对说明符解析：[Import specifiers](https://nodejs.org/docs/v26.13.1/api/esm.html#import-specifiers)；CommonJS 缓存与 `exports` 快捷变量：[Caching](https://nodejs.org/docs/v26.13.1/api/modules.html#caching)、[The exports shortcut](https://nodejs.org/docs/v26.13.1/api/modules.html#exports-shortcut)；ESM 导入 CJS 默认值和启发式命名导出：[CommonJS namespaces](https://nodejs.org/docs/v26.13.1/api/esm.html#commonjs-namespaces)；互操作与 `require(ESM)` 同步图限制：[Loading ECMAScript modules using require()](https://nodejs.org/docs/v26.13.1/api/modules.html#loading-ecmascript-modules-using-require)（该功能自 v25.4.0 起不再是实验性）。行为在 Node.js v26.13.0 实测。
> - Webpack 官方指南：[Tree shaking](https://webpack.js.org/guides/tree-shaking) 解释静态 ESM 使用分析、sideEffects 包字段与副作用误标。此处不把 Webpack 的优化行为推广成所有 bundler 的保证。

来源核对日期：2026-11-12。
## 50. 怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？

报表页可能在本地 Chrome 正常，却在部署后的旧 WebView 上因语法解析或缺少 API 失败。判断一项特性时，要分清它进入哪一版 ECMAScript、目标运行时是否实现，以及构建器实际转换了什么。TypeScript 的类型声明和构建选项也不能代替运行时能力检测。

### ECMAScript 版本能告诉我们什么？

ECMAScript 年份表示语言规范的版本；它本身不表示每个浏览器或 Node.js 发行版都已经实现所有特性。下面列出报表代码可能用到的一些边界。`structuredClone` 是由浏览器、Node.js 等宿主提供的 API（应用程序接口），不属于 ECMAScript 年份表。

| 特性 | 语言版本 | 使用边界 |
|---|---|---|
| `Object.keys` | ES5 | 返回自有且可枚举的字符串键，不含 Symbol 键 |
| `Object.assign`、`Object.is` | ES2015 | 前者会修改目标对象；后者使用 SameValue 比较规则 |
| `Array.from`、`Array.of` | ES2015 | 分别从可迭代或类数组输入创建数组，以及从参数列表创建数组 |
| `Object.values`、`Object.entries` | ES2017 | 只枚举自有、可枚举的字符串键 |
| `Promise.all`、`Promise.race` | ES2015 | 完成条件与取消边界见[异步 JavaScript](#40.%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E6%80%8E%E6%A0%B7%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%EF%BC%9F) |
| `Promise.allSettled` | ES2020 | 等所有输入结束后分别给出完成或拒绝结果 |
| `globalThis` | ES2020 | 当前 realm（执行域）的全局 `this` 值；浏览器网页的 Window 环境中为 `WindowProxy`，Node.js 中为 Node 全局对象 |
| `Promise.any` | ES2021 | 最先兑现的输入使聚合 Promise 成功；全部拒绝才以 `AggregateError` 拒绝 |
| `Array.prototype.at`、`Object.hasOwn` | ES2022 | 前者接受负索引；后者检查自有属性，不调用可覆盖的 `hasOwnProperty` |
| `Object.groupBy`、`Map.groupBy`、`Promise.withResolvers` | ES2024 | 分别按回调结果分组对象键或 Map 键、以及创建 Promise 与其控制函数 |
| `Set` 的集合方法、`RegExp.escape` | ES2025 | 集合并交差等操作；后者转义插入正则表达式的字面文本 |
| `structuredClone` | 浏览器与 Node.js 宿主 API | 可复制支持结构化克隆的值和循环引用；不能复制函数，也不保留自定义类原型 |

版本表适合初步定位；具体支持仍要核对目标浏览器版本、Node.js 主版本和嵌入式 WebView。单个运行时还可能只实现同一版规范中的部分功能。

### 语法转换、类型声明和 polyfill 有什么差别？

语法转换器可以把目标环境无法解析的语法改写成旧语法，但一般不会自动补上运行时缺失的内置 API。polyfill（兼容补丁）则在运行时提供缺少的方法或对象。TypeScript 的 `target` 决定 `tsc` 会把多少 JavaScript 语法降级；`lib` 选择类型检查时可见的标准库声明。把 `"DOM"` 或 `"ES2022"` 加入 `lib` 只让编译器认识这些名字，不会在运行时创建 `Object.hasOwn`。

~~~json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noEmit": true
  }
}
~~~

在报表页面中，`Object.hasOwn` 和 `Array.prototype.at` 即使通过类型检查，也应由部署目标提供或由项目显式加入 polyfill：

~~~javascript
const options = Object.create(null);
options.enabled = false;

Object.hasOwn(options, "enabled"); // true
["2026-09", "2026-10"].at(-1);   // "2026-10"
~~~

### Vite 的开发与生产目标分别由什么控制？

Vite 8.3 的开发转换默认以现代浏览器和 `esnext` 为目标；生产 bundle（打包产物）默认面向 2026-01-01 的 Baseline Widely Available（广泛可用基线）浏览器范围：Chrome/Edge 111、Firefox 114、Safari/iOS 16.4 及以上。可以用 `build.target` 调整生产语法目标。Vite 8 用 Oxc 转换 TypeScript，但只做转译，不执行完整类型检查；项目应另跑 `tsc --noEmit`。

Vite 的 `build.target` 与 `tsconfig.json` 的 `target` 名字相似，却分别控制生产 bundle（打包产物）的浏览器语法降级与 TypeScript 编译器的输出行为。Vite 默认只转换语法，并不补齐所有缺失 API；降低目标语法也不能让 `Object.hasOwn` 自动出现。需要旧浏览器兼容时，应分别确定语法目标和 API 补丁方案，再在代表性运行时检查构建产物。

截至 2026-11-06，TypeScript 7.1 beta（测试版）文档已将 `es2026` 列为稳定的 `target` 与 `lib` 选项。可用名称由项目实际安装的 TypeScript 版本决定；上面的配置刻意使用稳定较久的 `ES2022`。

`structuredClone` 的克隆范围由宿主定义。它可以处理循环引用、`Map`、`Set` 和 `Date` 等结构化可克隆值，但不能复制函数或保留自定义类的原型；不支持的值会抛出 `DataCloneError`。不要假设它必然比其他拷贝方法更快。

> [!info]- 来源
> - [ECMAScript 2026 规范](https://tc39.es/ecma262/2026/)
> - [TypeScript TSConfig：`target`](https://www.typescriptlang.org/tsconfig/#target)、[`lib`](https://www.typescriptlang.org/tsconfig/#lib)
> - [TypeScript 7.1 beta：ES2026 `target` 与 `lib`](https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/)
> - [Vite 8.3：TypeScript 转译与目标配置](https://vite.dev/guide/features.html#typescript)、[生产构建浏览器兼容](https://vite.dev/guide/build.html#browser-compatibility)
> - [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)、[Node.js 26.13：`structuredClone`](https://nodejs.org/api/globals.html#structuredclonevalue-options)
>
> Vite 浏览器版本与默认值按 Vite 8.3 文档核对；运行时更新后重新检查项目目标。来源核对日期：2026-11-06。

相关模块加载和构建链路见[ECMAScript 模块与 CommonJS 的加载边界](#49.%20ECMAScript%20%E6%A8%A1%E5%9D%97%E4%B8%8E%20CommonJS%EF%BC%88Node.js%20%E6%A8%A1%E5%9D%97%E6%A0%BC%E5%BC%8F%EF%BC%89%E5%9C%A8%E8%AF%AD%E6%B3%95%E3%80%81%E5%8A%A0%E8%BD%BD%E5%92%8C%E8%BF%90%E8%A1%8C%E6%97%B6%E6%9C%89%E4%BB%80%E4%B9%88%E4%B8%8D%E5%90%8C%EF%BC%9F)和[构建工具怎样把源码变成可发布产物？](#51.%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%BA%90%E7%A0%81%E5%8F%98%E6%88%90%E5%8F%AF%E5%8F%91%E5%B8%83%E4%BA%A7%E7%89%A9%EF%BC%9F)。
## 51. 构建工具怎样把源码变成可发布产物？

用一张合成的月度报表页跟踪源码如何变成浏览器请求的 URL。最后再看 v42 发布后，仍打开的 v41 页面为什么可能要取回旧的编辑器分块，以及发布时要保留什么。这个例子采用 Node.js 26.13.0、Vite 8.3.5 和 Webpack 5.109.0；文件名来自固定版本和配置的独立小项目，不代表产品默认值。

入口 `index.html` 引用 `src/main.ts`。主文件从 `rows.ts` 导入 `formatRow`，并静态导入 `report.css`；CSS 的 `url()` 引用图标；用户点击“打开编辑器”时，事件处理器才调用 `import("./editor.ts")`。`import()` 语法形成异步依赖边，点击处理器决定何时调用它。构建时会先找到并转换 `editor.ts`，但没有预加载时，浏览器等到这次调用才请求其生成文件。

`package.json` 中的脚本启动构建命令；它不是浏览器模块图的入口。Vite 默认以项目根目录的 `index.html` 开始。本例给 Webpack 显式设置 `entry: "./index.html"`，并配置生成页面的位置。

![合成报表项目的模块依赖关系](../../frontend/tooling/resources/build-tools-module-dependencies.svg)

图只画本例源码的模块关系。`main.ts` 保留对 `rows.ts` 中 `formatRow` 的值导入；`rows.ts` 的 `Column` 只作类型标注，TypeScript 擦除后不进入 JavaScript。处理 `report.css` 时，CSS 解析器才发现 `url('./report.svg')` 并排入该资源请求；本例关闭小资源内联，所以图标输出为单独文件。编辑器的异步边由 `import()` 语法建立，点击处理器只决定调用时机。

构建器按请求逐步扩展这张图，再把图中的关系变成浏览器可访问的产物：

1. **选入口。** `package.json` 的脚本启动构建器，但不是模块图入口。Vite 默认从项目根目录的 `index.html` 开始；本例为 Webpack 显式设置 `entry: "./index.html"`。
2. **递归发现依赖。** 对每个待处理请求，模块解析器（resolver）从导入方定位资源，再由匹配的加载器（loader）或内置处理器读取并转换。解析器检查转换后的内容，记录发现的静态、动态和资源依赖边，再把尚未处理的目标请求入队；继续处理，直到待处理请求队列为空。比如相对请求 `./rows.ts` 从导入方目录定位，包名则按安装位置和包元数据解析；本例只使用相对请求。
3. **优化并分块。** 队列清空时，本例的模块图才完整。摇树优化（tree shaking）删除可证明未使用的导出；代码分割（code splitting）决定模块怎样组成初始或异步的代码分块（chunk）。因此 Webpack 的 `optimization.splitChunks` 等规则会影响文件分组，不能只看源码写了几个入口。本例实际输出中没有 `unusedChart` 的哨兵字符串。
4. **生成并改写引用。** 构建器写出 HTML、JavaScript、CSS 和资源文件，把源请求改为生成文件间的引用；可选 manifest 记录入口到输出文件的映射。v41/v42 表格展示同一配置的实际文件名。哈希还会受图中引用和其他构建输入影响，不能只用某个源文件或最终 JS 字节独立推算。
5. **部署并运行。** 将整套产物部署在与公开路径相配的位置。浏览器沿 HTML 请求初始 JS 和 CSS，CSS 再引用图标；运行到生成代码里的动态导入时，Vite 请求改写后的 ESM URL，Webpack 则用 chunk ID、运行时文件名映射和 `output.publicPath` 组装 URL。此例只有在首次调用且没有预加载或可复用缓存时才会产生编辑器网络请求；HTML 相对 URL 的具体结果见下文实测。

### 为什么要固定 Node.js 与包管理器版本？

要复现一份构建，至少需要知道 Node.js、包管理器、锁文件和构建器的版本。`package.json` 的 `packageManager` 字段可记录项目采用的管理器及版本，但不会安装 Node.js；Node 版本仍应由版本文件、CI 镜像或运行环境固定。锁文件复用依赖解析结果，却不能固定操作系统、环境变量、系统工具或构建脚本读取的任意外部输入。

Node.js 25 起不再随发行包提供 Corepack。若项目依赖 Corepack 提供的命令代理，应按当前 Corepack 文档单独安装；也可按所选包管理器的官方流程固定版本。比如 `package.json` 把 `build` 脚本映射到 `vite build`，再由 `pnpm build` 运行。CI 与本地使用相同工具和锁文件能减少解析差异，仍需检查实际生成路径和部署结果。

### Webpack 的模块加载器与插件分别处理什么？

先把合成页面的请求关系和浏览器看到的产物分开：

| 源码或入口 | 构建时发现的关系 | 本例浏览器何时请求生成文件 |
|---|---|---|
| `index.html` | Vite 默认入口；Webpack 显式指定 `./index.html` | 取得页面 HTML 时 |
| `src/main.ts` | HTML 的 `<script type="module" src="./src/main.ts">` 引入 | 页面启动时加载生成的初始 JavaScript |
| `src/rows.ts`、`src/report.css` | `main.ts` 静态导入 | 跟随入口的初始依赖加载；样式再引用图标 |
| `src/report.svg` | CSS 解析发现的 `url()` 请求 | 浏览器取 CSS 后请求，或由构建配置内联 |
| `src/editor.ts` | 点击处理器里的动态 `import()` | 本例第一次点击时请求生成的编辑器分块 |

在 Webpack 5.109.0 的实测配置中，HTML 输出名放在 `assets/` 目录，页面实际 URL 为 `/reports/assets/index-5248e5cf.html`。HTML 中的脚本 `../assets/__html_68cecd12_0-7cc84df8.js` 和样式 `../assets/__html_68cecd12_0-efdbfebc.css`，都要相对于这个 HTML URL 解析，因此请求落在 `/reports/assets/`。CSS 再引用 `/reports/assets/report-b1d5801f.svg`。如果把相同 HTML 原样放到 `/reports/index.html`，这两个 `../assets/…` 会解析到 `/assets/…`；本例的请求因此得到 404。HTML 的部署 URL 必须和它内部的相对引用及服务器挂载位置一致。

Webpack 输出的初始脚本把动态导入变为 chunk ID 与运行时映射；本例的运行时使用 `output.publicPath: "/reports/"`，点击后才请求 `/reports/assets/354-b92eb80e.js`。另有一个 stats 列出的 `assets/main-fa829d06.js` 没有被生成 HTML 引用，也没有浏览器请求。检查页面加载应沿 HTML、CSS 和脚本中的实际引用走，不能把每个 emitted asset 都当成必请求文件。

Webpack 由入口和导入边建立模块图。每个请求先解析到实际资源，再由匹配的加载器或内置处理器读取并转换；解析器根据转换后的文本发现后续边。加载器的常规阶段（normal）按 `use` 数组从右向左执行；若定义前置钩子（pitch），Webpack 会先从左向右调用它。某个 pitch 返回结果时，会跳过该加载器及它右侧尚未执行的常规函数，并把返回值交给左侧加载器，按 normal 顺序反向继续。下面的 Sass 配置先编译 Sass，再将结果交给 PostCSS：

~~~javascript
module: {
  rules: [
    {
      test: /\.s[ac]ss$/i,
      type: "css/auto",
      use: ["postcss-loader", "sass-loader"]
    }
  ]
}
~~~

这里 `type: "css/auto"` 明确让 Sass 转出的 CSS 交给 CSS 模块解析。若两步确实各有职责，才保留两个转换器；普通 CSS 已有原生处理时，不要仅为旧配置习惯重复加 loader。Sass、Less、Stylus 或 PostCSS 仍需各自的预处理器。

Webpack 5.109.0 中原生 CSS 和 HTML 的默认值是 `auto`。它不是按文件任意混用两套解析器：旧规则可能使原生处理在整个编译中关闭，所以要同时构建一个应走原生能力的文件和一个应走旧规则的文件。没有冲突配置时，原生 CSS 能处理常见 CSS、`@import`、`url()` 与 CSS Modules；原生 HTML 能据入口和模块图生成页面引用。模板型旧页面要按实际行为逐项迁移。

Webpack 5.107.0 加入原生 TypeScript 擦除，5.109.0 默认启用 `experiments.typescript: "auto"`。它只擦除类型，不做类型检查，也不处理 TSX、enum 等需要额外转换的语法。`module.stripTypeScriptTypes` 这个 Node API 在 Node 22 系列从 22.13.0 提供、在 23 系列从 23.2.0 提供；Node 22.6.0 提供的是命令行类型擦除选项，并没有这个 API。Webpack 5.109 的 `auto` 会检测 API 和相关 loader 规则。`ts-loader@9.6.2` 默认会检查类型；使用 `transpileOnly: true`、Webpack 原生擦除或 Vite 转译时，应另有 `tsc --noEmit` 等类型检查步骤。

以下 loader 仅做字符串替换，不理解 JavaScript 结构；要按语法节点改写代码，应使用抽象语法树（AST）转换器：

~~~javascript
export default function replaceReportTitle(source) {
  return source.replaceAll("__REPORT_TITLE__", "Monthly Reports");
}
~~~

Webpack Asset Modules（资源模块）可处理图片、字体、媒体与文本资源，在许多项目里可替代旧的 `file-loader`、`url-loader` 或 `raw-loader` 配置。图标最终是独立文件还是 CSS 中的 data URL，取决于工具版本、资源大小和内联配置。本例为观察浏览器 URL 明确将 Vite `assetsInlineLimit` 设为 `0`。

插件（plugin）处理一次构建中的共享状态或资源；新增产物应在 `compilation.hooks.processAssets` 选择合适阶段。下面的统计插件在 `done` 时把 JSON 写到运行命令时的当前目录；它不会自动写入 `dist/`，也不是 Webpack asset：

~~~javascript
import { writeFileSync } from "node:fs";

class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tap("BuildStatsPlugin", stats => {
      const json = stats.toJson({ assets: true, modules: false });
      writeFileSync("build-stats.json", JSON.stringify(json, null, 2));
    });
  }
}
~~~

`DefinePlugin` 在构建时替换代码表达式；写入客户端 bundle 的值会交给浏览器用户，不能放入密钥。

> [!info]- Webpack 5.109 自动探测、emit 阶段与旧插件迁移细节
> CSS 和 HTML 的 `auto` 在构建配置层先用 `/file.css`、`/file.module.css`、`/file.html` 等合成路径探测。`test`、`resource` 或 `include` 任一条件可能计入；规则中的 `exclude` 不参与这项宽松探测。探测还会把正则中明确引用扩展名的模式计入：例如 `/source\.css$/` 即使不匹配 `/file.css`，仍可关闭这一编译的原生 CSS。只有显式 `type` 或未设 `enforce` 的普通 `loader/use` 才算接管；`pre`、`post` loader 不触发关闭。若 `auto` 保持启用，真实模块只有在默认原生类型仍被选中、已应用 loader 且没有 `matchResource` 显式重定类型时，才沿旧解析路径退让给 loader 产物。
> 在使用默认 `resolve.extensions` 时，显式 `experiments.html: true` 会让 `.html` 排在 JavaScript 扩展名前，因此目录入口可优先解析为 `index.html`；`auto` 则把 `.html` 放在 JavaScript 后。自定义扩展名顺序时按实际配置判断。
>
> `processAssets` 的 stage 决定生成或读取资源的时点。`ADDITIONAL` 位于代码压缩、source map 和传输压缩之前，适合新增自有文件；若到 `SUMMARIZE` 才新增文件，`OPTIMIZE_SIZE` 已经过，Webpack 不会重跑整个阶段；若某个处理器订阅了 `additionalAssets`，仍可单独处理后续新增资源。Webpack 5.109 的默认 JavaScript minimizer 就使用这种订阅，因此不能仅凭新增阶段断言文件不会被压缩；还要看该处理器的匹配与处理条件。全部 `processAssets` 阶段完成并封存资源后，Webpack 才调用 `emit`，随后写入配置的 output filesystem；后注册的 emit tap 仍能看到较早 tap 的改动，但它新增的文件已错过先前 stage。`afterEmit` 已在输出后，修改不会回写刚才的文件。Webpack 5.109 默认 `backCompat: true`，此时写封存的 `Compilation.assets` 会警告；关闭兼容模式后该对象被冻结。需要新增或变换产物时使用正确 stage 的 `processAssets`，统计信息则可在 `done` 写到独立文件。
>
> `HtmlWebpackPlugin` 当前 README 标记为弃用；Webpack 5.109 原生 HTML 可覆盖常见页面产物，但模板插件的定制行为仍须逐项核对。CSS/HTML 内置压缩从 5.110.0 才开始。当前 `CompressionWebpackPlugin` 已弃用，压缩 generator 迁入 `minimizer-webpack-plugin`，迁移选项从 `minimizer-webpack-plugin@5.11.0` 起提供；生成 `.gz`/`.br` 文件不代表服务器已按内容协商返回相应 `Content-Encoding`。Webpack 5.109 默认 JavaScript 压缩仍使用 Terser；`terser-webpack-plugin` 于自身 5.6.0 更名。覆盖 `optimization.minimizer` 时，保留默认项需包含 `"..."`。更多历史选项见[归档的 Webpack 插件对照表](../../archive/front-end/Deprecated_Interview_Notes/webpack-plugin-history.md)。

### Vite 开发服务器为什么不能代替生产构建检查？

按 Vite 8.3.5 说明，开发服务器按请求提供转换后的原生 ESM，也用 Rolldown 预打包依赖；生产 `vite build` 由 Rolldown 生成静态 HTML、JavaScript、CSS 和资源。两条路径在分块、目标浏览器、公开路径和服务器行为上可能不同。HMR（热模块替换）是开发期机制：服务器通知变化并提供更新模块，浏览器运行时取得更新并调用模块的接受回调；当前模块边界无法处理时才会整页刷新。它不是生产文件发布。

Vite 默认以项目根目录 `index.html` 为生产入口。本例把生成的页面挂在 `/reports/`，并显式生成 manifest、关闭小 SVG 内联：

~~~javascript
import { defineConfig } from "vite";

export default defineConfig({
  base: "/reports/",
  build: { manifest: true, assetsInlineLimit: 0 }
});
~~~

生成的 HTML 指向初始脚本和样式，CSS 再指向 SVG；构建也会把源码中的动态导入改写为生成文件名：

~~~html
<script type="module" src="/reports/assets/index-gRN8M4PG.js"></script>
<link rel="stylesheet" href="/reports/assets/index-QsJV6IX7.css">
~~~

~~~css
background: url(/reports/assets/report-D2wE4vR2.svg);
~~~

v41 的入口脚本保留 `import('./editor-x2UHusWa.js')` 这个改写后的目标（实际输出由预加载辅助函数包装）：

~~~javascript
await import("./editor-x2UHusWa.js");
~~~

脚本从 `/reports/assets/` 加载，浏览器因此请求 `/reports/assets/editor-x2UHusWa.js`，而不是请求源码 `editor.ts`。本例用无界面 Chromium 首次打开页面时未请求编辑器；点击后该 URL 返回 200。

Vite 的 manifest 默认不生成。本例打开它是为核对源入口到输出文件的映射，例如 `"index.html"` 记录 `dynamicImports: ["src/editor.ts"]`，而 `"src/editor.ts"` 的 `file` 是 `"assets/editor-x2UHusWa.js"`。这些 `file` 值是相对输出目录的路径，不含 `/reports/` URL 前缀；浏览器按 HTML、CSS 和生成 JavaScript 中的引用请求文件，不请求 manifest。服务端或集成工具若需要这份映射，可打开 `build.manifest`。

若恢复默认内联阈值，本例的小 SVG 会变成 CSS 的 data URL，不再单独发 SVG 请求。部署到子路径时，`base` 要与静态站点挂载路径一致。`vite preview` 可预览生产构建，不是生产服务器；还要在实际部署 URL 检查 HTML、初始脚本/样式、异步分块、图像、缓存头、压缩和路由回退。Vite/Oxc 转译 TypeScript 不等于类型检查。Vite 8.3.5 的 `build.target` 默认面向 2026-01-01 的 Baseline Widely Available 浏览器范围；它决定语法转换范围，不补齐运行时 API，也不由 `tsconfig.json` 的 `target` 代替。若要支持更早浏览器，还要单独安排 API polyfill（应用程序接口兼容补丁）并在目标环境验证。参见[怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？](#50.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E7%9B%AE%E6%A0%87%E6%B5%8F%E8%A7%88%E5%99%A8%E6%88%96%20Node.js%20%E6%98%AF%E5%90%A6%E6%94%AF%E6%8C%81%E4%B8%80%E9%A1%B9%20JavaScript%20%E7%89%B9%E6%80%A7%EF%BC%9F)。

### 新入口与带哈希代码分块怎样作为同一版本发布？

独立构建的 v41 与 v42 只改变编辑器文字。构建器改写入口中的编辑器目标，所以即使 `main.ts` 源码不变，生成的入口 JavaScript 内容也变了，入口和编辑器文件名都随之变化。下面是这个合成 fixture 的实际输出；未变的 CSS 与 SVG 文件保持原名：

| 浏览器请求（`base` 为 `/reports/`） | v41 | v42 |
|---|---|---|
| 新页面从 HTML 取得的入口 JS | `/reports/assets/index-gRN8M4PG.js` | `/reports/assets/index-ClYpL0PO.js` |
| 首次点击时的编辑器分块 | `/reports/assets/editor-x2UHusWa.js` | `/reports/assets/editor-BLsXx8VX.js` |
| 初始 CSS | `/reports/assets/index-QsJV6IX7.css` | 相同 |
| CSS 图标 | `/reports/assets/report-D2wE4vR2.svg` | 相同 |

该命名来自这组构建器输出，不应推断为仅凭入口脚本最终字节就能独立计算文件名的通用规则。

![v41 旧标签与 v42 新标签分别请求对应编辑器分块](../../frontend/tooling/resources/build-tools-release-v41-v42.svg)

发布前把一整套 v42 入口、样式、图像和异步分块写到目标存储，再核对它们能从对应 URL 读取，最后切换源站的 HTML 或 release 指针。这个切换只能保证指针更新本身的原子性；CDN 边缘可能短时仍返回旧 HTML。因此不要覆写同一个哈希 URL 的内容，也不要在仍有旧 HTML、旧标签或旧 Service Worker 时删除其引用的文件。

上面的 200/404 来自实际浏览器测试。v41 标签已加载入口但尚未点编辑器；保留旧 chunk 后首次点击请求旧 URL 并返回 200，提前删除后该首次请求返回 404，导入失败。若编辑器已由该页面加载，之后重复调用通常复用已加载模块，不会再发同一请求；若浏览器/Service Worker 有可用副本，也可能不请求网络。若服务器把缺失 chunk 回退到 HTML，网络状态可以是 200，但动态导入仍会因响应不是 JavaScript 而失败。

回滚静态发布时，把入口 HTML 与其清单（若有服务端消费者）配对指回 v41；已打开的 v42 页面仍可能需要 v42 文件。旧版保留窗口要覆盖仍服务的 HTML、打开的页面和可能继续接管旧页面的 Service Worker。后端 API 是否兼容新旧页面是另一条发布边界。HTTP 缓存和 Service Worker Cache Storage 也需分开看：

| 资源 | 缓存边界 |
|---|---|
| 可变 HTML 或当前 release 指针 | 可用 `Cache-Control: no-cache` 保存响应，但复用前要重新验证；也可缩短新鲜时间 |
| 带哈希的脚本、CSS 与图片 | 只有同一路径永不改写内容时才适合长缓存和 `immutable` |
| manifest | 浏览器通常不请求；服务端读取时按版本保存，或与入口一同重新验证 |
| Service Worker Cache Storage | 独立于 HTTP 缓存；按版本保留旧页仍需的文件 |

`no-cache` 允许存储响应，但再次使用前要求验证；它不是 `no-store`。`immutable` 表示新鲜期内内容不变。遇到动态 chunk 加载失败时，应识别可恢复的发布错配，保留用户未保存的草稿，并让用户保存或选择刷新；不要把所有导入错误都判成发布错配，也不要无限重载。本页止于静态资源部署；构建一次、逐环境验证、渐进放量和服务端回滚见[如何晋级并回滚已验证的报表服务产物](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)。

### Source map 怎样用于调试，又会暴露什么？

Source map（源映射）记录生成代码位置与原始源码位置的对应关系。调试器或错误收集工具可用它把生成代码中的行列位置映回源码；映射本身不重建原始文件。映射粒度、loader 是否提供映射、文件内嵌或外置、是否含源码文本，会影响定位、构建成本和公开信息。

| Webpack `devtool` 例子 | 主要含义 | 适用边界 |
|---|---|---|
| `eval-source-map` | 逐模块用 `eval` 关联完整映射 | 开发定位精度高；官方将初次构建列为 slowest |
| `cheap-source-map` | 行级映射，忽略 loader 提供的映射 | 不支持列级断点；映射可能停留在转换后的行 |
| `cheap-module-source-map` | 使用 loader 映射后简化到行级 | 能映回更早源码，但不保留列级位置 |
| `source-map` | 外置完整映射，bundle 通常写引用 | 错误定位可恢复行列；需检查 `.map` 是否可公开请求 |
| `hidden-source-map` | 外置映射但 bundle 不写 `sourceMappingURL` | 可将 `.map` 单独上传到私有错误工具；隐藏引用不等于访问控制 |
| `nosources-source-map` | 不内嵌 `sourcesContent` | 仍可能泄露文件名和映射关系，不是源码权限边界 |

`cheap-` 只保留行级位置。`module-` 只在 cheap 组合中表示消费 loader 映射；完整 `source-map` 本身就会使用可用的 loader 映射。Webpack 5.105 起可用数组按 JavaScript、CSS 或两者设置 source map 类型；这里的 `all` 指 JavaScript 与 CSS，不是任意图像、字体或资源。当前完整语法还含 `-debugids`，Webpack 5.112.0 加入 `-scopes`；组合顺序与可用性按锁定版本核对。旧预设的详细映射见[Webpack source map 预设对照](../../archive/front-end/Deprecated_Interview_Notes/webpack-source-map-presets.md)。

Source map 不是权限边界：若 `.map` URL 仍由服务器公开提供，去掉 bundle 引用不能阻止知道路径的人请求。`nosources` 只去掉内嵌源码文本，仍可能暴露目录和文件名。发布时分别检查输出文件、服务器静态资源规则和错误收集工具的访问权限。

> [!info]- 来源
> - **Node 与包管理器：** [Node.js 25.0.0 发布说明](https://nodejs.org/en/blog/release/v25.0.0) 与 [Corepack 配置项目](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html)：Corepack 从 Node 25 起不随发行包提供；[Corepack 的 `packageManager` 字段](https://github.com/nodejs/corepack#when-authoring-packages)说明包管理器版本声明。[Node.js 22.6.0 发布说明](https://nodejs.org/en/blog/release/v22.6.0)说明当时加入的是 `--experimental-strip-types` 命令行功能；[`module.stripTypeScriptTypes()` 文档](https://nodejs.org/download/release/v22.13.0/docs/api/module.html#modulestriptypescripttypescode-options)、[22.13.0 发布说明](https://nodejs.org/en/blog/release/v22.13.0)、[23.2.0 发布说明](https://nodejs.org/en/blog/release/v23.2.0)确认 API 版本边界。核对日期：2026-11-12。
> - **Webpack 模块图与浏览器 URL：** [NormalModule.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/NormalModule.js#L1576-L1650)、[Compilation.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compilation.js#L1766-L1810) 及 [ImportParserPlugin.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/dependencies/ImportParserPlugin.js#L580-L620)说明转换后解析依赖和异步边；[Webpack chunk runtime](https://github.com/webpack/webpack/blob/v5.109.0/lib/web/JsonpChunkLoadingRuntimeModule.js#L135-L196)说明运行时如何组合 public path 和文件名。Webpack HTML 配置和发布路径见[原生 HTML](https://webpack.js.org/guides/native-html/)与[输出管理](https://webpack.js.org/guides/output-management/)。
> - **Webpack CSS、HTML 与 TypeScript：** [v5.109 defaults.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L649-L686) 展示 `auto` 合成路径探测与原生 TypeScript 默认；[RuleSetCompiler.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/rules/RuleSetCompiler.js#L473-L578) 包含宽松规则探测与扩展名正则判断；[implicitTypeLoaderFallback.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/util/implicitTypeLoaderFallback.js#L13-L51) 展示 loader 逐模块退让条件。Native CSS/HTML 及[experiments.typescript](https://webpack.js.org/configuration/experiments/#experimentstypescript)文档核对 5.109/5.110 边界；[HtmlWebpackPlugin 当前 README](https://github.com/jantimon/html-webpack-plugin#readme)标记弃用。Node API feature detection 见 [TypeScriptPlugin.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/typescript/TypeScriptPlugin.js#L119-L134)。
> - **Webpack loader、插件与压缩：** [processAssets 阶段与 additionalAssets](https://webpack.js.org/api/compilation-hooks/#processassets)说明新增产物的阶段顺序及后续资源回调；[minimizer-webpack-plugin v5.6.1](https://github.com/webpack/minimizer-webpack-plugin/blob/v5.6.1/src/index.js) 的 `OPTIMIZE_SIZE` 订阅启用 `additionalAssets: true`，匹配的后续资源仍可进入该处理器；[HTML 默认入口](https://webpack.js.org/configuration/experiments/#html-as-the-default-entry)说明默认扩展名顺序。[Loaders](https://webpack.js.org/concepts/loaders/)解释 pitch/normal 次序；[ts-loader `transpileOnly`](https://github.com/TypeStrong/ts-loader#transpileonly)说明默认类型检查和纯转译选项；[Asset Modules](https://webpack.js.org/guides/asset-modules/)解释资源处理；[Compiler.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compiler.js#L1081-L1106)、[Compilation.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compilation.js#L3806-L3834)和 [defaults.js backCompat 默认值](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L622-L623)核实 emit、processAssets、资源封存与兼容模式。[CompressionWebpackPlugin 当前 README](https://github.com/webpack/compression-webpack-plugin#readme)标记弃用；压缩迁移选项要求 `minimizer-webpack-plugin@5.11.0`，见[迁移文档](https://github.com/webpack/compression-webpack-plugin#migrating)。[Terser minimizer 5.6.0](https://github.com/webpack/minimizer-webpack-plugin/releases/tag/v5.6.0)记录包名变更。
> - **Vite 与 source map：** 固定版本 [Vite 8.3.5 build](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/build.md)、[assets](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/assets.md)、[features](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/features.md)、[HMR API](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/api-hmr.md)、[build options](https://github.com/vitejs/vite/blob/v8.3.5/docs/config/build-options.md)、[manifest](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/backend-integration.md)及[生产动态导入辅助逻辑](https://github.com/vitejs/vite/blob/v8.3.5/packages/vite/src/node/plugins/importAnalysisBuild.ts#L314-L344)。Source map 版本与预设见[Webpack devtool 表](https://webpack.js.org/configuration/devtool/)、[5.105 数组配置](https://webpack.js.org/blog/2026-02-03-webpack-5-105/)和[5.112 scopes](https://webpack.js.org/blog/2026-10-13-webpack-5-112/)。缓存语义见 [RFC 9111 §5.2](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2)、[RFC 8246](https://www.rfc-editor.org/rfc/rfc8246.html)与[Service Workers](https://www.w3.org/TR/service-workers/)。
>
> v41/v42 的具体文件名和请求是 Node.js 26.13.0、Vite 8.3.5 的合成 fixture 实测；Webpack HTML 路径与 chunk 文件名是 Node.js 26.13.0、Webpack 5.109.0 的独立 fixture 实测。它们是版本与配置结果，不是稳定 API。
## 52. 报表页面里的状态应该放在哪里？

案例背景：用户打开 `/reports/42?sort=recent#summary`，希望刷新后继续查看同一报表、复制链接分享当前排序，并在另一标签页改变偏好后看到更新。重开时，页面从路径取报表 ID、从查询参数还原 `sort`，然后通过 HTTP 请求服务端报表；片段 `#summary` 定位页面中的摘要。若返回快照仍是 `running`，页面拿到与快照一致的 `event_cursor` 后再订阅更新，见[流式报表恢复案例](#54.%20%E6%B5%81%E5%BC%8F%E6%8A%A5%E8%A1%A8%E6%96%AD%E7%BA%BF%E9%87%8D%E8%BF%9E%E5%90%8E%EF%BC%8C%E7%95%8C%E9%9D%A2%E6%80%8E%E6%A0%B7%E4%BF%9D%E7%95%99%E6%AD%A3%E7%A1%AE%E7%8A%B6%E6%80%81%EF%BC%9F)。报表内容由服务端维护，可分享的筛选条件进入 URL，Web Storage (网页存储) 只保存客户端偏好或草稿。

| 状态 | 合适的所有者 | 原因 |
|---|---|---|
| 报表 42 的进度、最终状态和权限 | 服务端 API | 多设备共享且需要可信的业务记录；缓存只能用于显示，不能取代权威状态 |
| `sort=recent`、定位到 `#summary` | URL 查询参数与片段 | 刷新、复制和浏览器历史都能恢复这份视图状态 |
| 列密度、隐藏提示等小型偏好 | `localStorage` | 同源页面可读写，并可跨标签页保留；浏览器策略仍可能限制或清除它 |
| 未提交的本标签页筛选草稿 | `sessionStorage` | 适合随当前顶层浏览上下文存活，重载后还可恢复 |
| 登录会话标识 | 服务器管理的 Cookie | 符合域、路径、传输安全和请求凭证规则时会随请求发送 |

`localStorage` 和 `sessionStorage` 是同步的字符串键值 API；调用会占用当前 JavaScript 执行时间。它们不提供多键事务或条目级过期时间，也不适合作为大型结构化数据的数据库。Storage Standard 为这两个存储端点各建议 5 MiB 配额；这是规范建议，不保证用户代理一定能提供，写入也可能因配额或策略限制失败。较大的本地记录和需要原子提交的更新可用 IndexedDB 事务；`navigator.storage.estimate()` 只能给出近似使用量和配额，不能保证数据不会被策略拒绝或清除。

同源并不总表示顶层页面和嵌入式第三方页面共享同一个存储区：浏览器可限制第三方存储，存储分区也可能把嵌入上下文隔离。不要假设同一页面在顶层打开和放入 iframe 后能读到相同数据。

`sessionStorage` 通常按来源和顶层浏览上下文隔离，因而不同标签页各有一份，并能在同一标签页重载时保留。由带 opener 的页面新开的辅助浏览上下文，初始时可能收到 opener 的 sessionStorage 副本，之后两边各自变化；不要把这种初始复制当作共享存储。浏览器会话恢复等生命周期行为也由用户代理决定。

本地存储写入不是跨标签页锁。标签页 A 和 B 同时读取计数 4、各自加一并写回时，最终值可能仍为 5。值实际发生变化时，其他共享该存储区的文档会收到 storage event (存储事件)，写入者本身不会收到；若 `setItem()` 写入的字符串与原值相同，规范会提前返回，不派发事件。事件只是通知，不会把多步读改写变成事务。需要协作时，使用 IndexedDB 事务或明确的跨上下文协调协议。

> [!example] 用存储通知偏好变化
> 排序是 URL 状态，以下键只保存列密度。两个标签页分别运行这两段代码。示例假定 B 中该键尚未设置或原值为 `"false"`；A 监听其他文档的有效变化，B 调整偏好后写入。即使通知到达，A 也应把它当作“偏好有变化”的信号，再从存储读取值。
>
> 标签页 A：
>
> ~~~javascript
> const key = "reports:compact-columns";
> window.addEventListener("storage", event => {
>   if (event.storageArea === localStorage && event.key === key) {
>     applyCompactColumns(localStorage.getItem(key) === "true");
>   }
> });
> ~~~
>
> 标签页 B：
>
> ~~~javascript
> localStorage.setItem("reports:compact-columns", "true");
> ~~~

Web Storage 可被当前页面上的脚本读取；若 cross-site scripting (跨站脚本攻击，XSS) 进入页面，存储在其中的 bearer token (持有者令牌) 也可能被窃取。`HttpOnly` Cookie 不向普通页面脚本暴露，但浏览器会按 Cookie 规则自动附带它，服务端仍需设计 Cross-Site Request Forgery (跨站请求伪造，CSRF) 防护。`SameSite=None` Cookie 必须同时带 `Secure`。选用一种存储形式并不会自动解决认证与授权问题。

**延伸阅读：** [同一报表在多个标签页中怎样交换变化？](#53.%20%E5%90%8C%E4%B8%80%E6%8A%A5%E8%A1%A8%E5%9C%A8%E5%A4%9A%E4%B8%AA%E6%A0%87%E7%AD%BE%E9%A1%B5%E4%B8%AD%E6%80%8E%E6%A0%B7%E4%BA%A4%E6%8D%A2%E5%8F%98%E5%8C%96%EF%BC%9F) 解释怎样通知其他标签页；[Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) 讨论 Cookie、XSS 与 CSRF。

> [!info]- 来源
> - `localStorage`、`sessionStorage` 的作用域、storage event (存储事件) 与访问策略：[WHATWG HTML Standard，Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，§12.2，2026-11-06 核对。
> - 浏览器配额、存储持久性和驱逐由实现与用户代理策略影响；`navigator.storage.estimate()` 返回近似值：[WHATWG Storage Standard](https://storage.spec.whatwg.org/)，2026-11-06 核对。
> - Web Storage 的 5 MiB 是每个存储端点的规范配额建议；Storage Standard 说明 storage key 的分区模型预期会演进：[WHATWG Storage Standard，§4.1–4.2](https://storage.spec.whatwg.org/#storage-endpoints)，2026-11-06 核对。
> - 用户代理可限制第三方文档对 `localStorage` 的访问：[WHATWG HTML Standard，Web Storage privacy](https://html.spec.whatwg.org/multipage/webstorage.html#user-tracking)，2026-11-06 核对。
> - 结构化本地记录与事务：[Indexed Database API 3.0](https://w3c.github.io/IndexedDB/)，2026-11-06 核对。
> - 已发布的 Cookie 存储与请求发送规则、`Secure`、`HttpOnly` 属性：[RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html)。
> - `SameSite` 属性及 `SameSite=None` 要求 `Secure`：当前 IETF 文稿 `draft-ietf-httpbis-rfc6265bis-22` 的 §4.1.2.7、§5.7；截至 2026-11-06，Datatracker 仍标记 RFC Editor「Final Approval Pending」，普通 RFC 发布页尚未提供：[IETF 文稿](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis/)，[官方流程状态](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/)。
## 53. 同一报表在多个标签页中怎样交换变化？

案例背景：用户在标签页 A 查看报表 42，在标签页 B 重新生成报表。A 需要知道自己的画面可能过时，并刷新权威数据。browsing context (浏览上下文) 能否直接通信，取决于来源、浏览器存储分区和生命周期；通知本身也不等于共享或持久化业务状态。

| 需求 | 机制 | 关键边界 |
|---|---|---|
| same-origin (同源) 且符合存储分区条件的临时广播 | `BroadcastChannel` | 消息不持久化；不在线的标签页收不到历史消息 |
| 存储一项值并通知其他文档 | `localStorage` + `storage` 事件 | 字符串写入、无事务或锁；写入者不收到自己的事件 |
| 同源上下文共享一个协调者或连接 | `SharedWorker` (共享工作线程) | worker 内存不是持久状态，需探测浏览器支持；页面关闭或进入 back-forward cache (前进/后退缓存，BFCache) 时需清理或重连端口 |
| 跨源 iframe (内嵌框架) 或窗口消息 | `postMessage()` | 固定目标 origin (来源)，并验证发送方窗口和数据结构 |
| 服务端持续更新或跨设备状态 | SSE、Fetch 流或 WebSocket | 服务端认证授权；重连与状态恢复由应用协议定义 |

在简单的同源通知中，发送报表标识和单调状态版本即可；不要把另一个标签页发来的对象当成权威记录。接收端发现版本更高时，重新请求服务端快照可以减少陈旧数据和消息缺失的影响。`BroadcastChannel` 会用 structured clone (结构化克隆) 传递消息，不保留共享对象引用，也不会替应用保存未读消息。

> [!example] 通知“报表可能更新”，再读权威状态
> A 已持有报表 42 的版本 9。B 提交更新后收到服务端版本 11、状态 `ready`，并广播一条轻量通知；本例假设版本在同一报表 ID 下单调递增。若 A 收到高于当前版本的提示，就 GET 权威快照；广播不携带快照游标，也不补发离线期间的历史。
>
> ~~~javascript
> const channel = new BroadcastChannel("reports");
> let currentVersion = 9;
>
> channel.addEventListener("message", event => {
>   const message = event.data;
>   if (!message || message.type !== "report:changed" ||
>       message.reportId !== 42 || !Number.isSafeInteger(message.version)) return;
>   if (message.version <= currentVersion) return;
>   void reloadReportFromServer(42, message.version);
> });
>
> async function reloadReportFromServer(reportId, announcedVersion) {
>   try {
>     const response = await fetch(`/api/reports/${reportId}`);
>     if (!response.ok) throw new Error("Snapshot request failed");
>     const latest = await response.json();
>     if (latest.id !== reportId || !Number.isSafeInteger(latest.version)) {
>       throw new Error("Invalid snapshot");
>     }
>     if (latest.version > currentVersion) {
>       currentVersion = latest.version;
>       renderReport(latest);
>     }
>     if (currentVersion < announcedVersion) showRefreshPending();
>   } catch {
>     // Keep the current view and show a bounded refresh error; do not retry forever.
>     if (currentVersion < announcedVersion) showRefreshUnavailable();
>   }
> }
>
> function announceChanged(reportId, version) {
>   channel.postMessage({ type: "report:changed", reportId, version });
> }
>
> // 页面所有者释放时执行；生命周期恢复时重新创建 channel。
> function disposeReportChannel() {
>   channel.close();
> }
> ~~~

若更新值本身要跨刷新保留，可写入 `localStorage` 并监听其他文档的 `storage` 事件；值发生变化时其他文档才收到通知，写入文档不收到，同一字符串重复写入也不派发事件。此机制只报告发生过某次有效变化，不协调并发写入。对于复杂协调，WHATWG HTML 建议考虑 `SharedWorker`：它可以集中管理端口、版本或一条共享连接。页面可以在 `pagehide` 尝试发送断开消息、在恢复时重新注册，但 `pagehide` 不是可靠的退出确认；崩溃或系统回收时需靠租约/心跳过期，并允许回来的页面重新注册。旧端口也应从 worker 的集合中移除并 `close()`，而不能假设平台会向另一端提供通用的 peer-close event (对端关闭事件)。

> [!example] SharedWorker 端口需要显式注销
> `SharedWorker` 可以在内存中把一个标签页的变更转给其他连接页面。正常离开时页面发 `disconnect` 并关闭自己的端口；从 BFCache 恢复时重新建立端口。以下代码只展示协作式注销与恢复，不实现心跳或租约；若页面进程直接退出，worker 仍需按上文策略清除过期连接。
>
> ~~~javascript
> // report-worker.js
> const ports = new Set();
> self.addEventListener("connect", event => {
>   const port = event.ports[0];
>   ports.add(port);
>   const dropPort = () => {
>     ports.delete(port);
>     port.close();
>   };
>   port.addEventListener("message", ({ data }) => {
>     if (data?.type === "disconnect") return dropPort();
>     for (const peer of ports) if (peer !== port) peer.postMessage(data);
>   });
>   port.addEventListener("messageerror", dropPort);
>   port.start();
> });
> ~~~
>
> ~~~javascript
> // 页面所有者维护自己的连接，并在恢复时重新注册。
> let port;
> function connectReportWorker() {
>   port = new SharedWorker("/report-worker.js").port;
>   port.onmessage = event => renderReportNotice(event.data);
> }
> connectReportWorker();
> window.addEventListener("pagehide", () => {
>   port?.postMessage({ type: "disconnect" });
>   port?.close();
>   port = null;
> });
> window.addEventListener("pageshow", event => {
>   if (event.persisted) connectReportWorker();
> });
> ~~~

跨源页面必须在 `postMessage(data, targetOrigin)` 中设置精确目标来源。接收方同时检查 `event.origin`（消息来源）和 `event.source`（发送窗口），再验证允许的消息类型、字段及大小；来源不包括路径。子页先装好监听器并向父页发 `ready`，父页再发 `refresh`，避免消息先于监听器到达。使用 `"*"` 发送敏感内容可能把消息交给已经导航到另一站点的目标窗口。信任的页面也可能因 cross-site scripting (跨站脚本攻击，XSS) 被控制，因此来源校验不能替代操作授权和载荷校验。

~~~javascript
const childOrigin = "https://reports.example";
const frame = document.querySelector("#report-frame");
window.addEventListener("message", event => {
  if (event.origin !== childOrigin || event.source !== frame.contentWindow) return;
  if (event.data?.type === "ready") {
    frame.contentWindow.postMessage({ type: "refresh", reportId: 42 }, childOrigin);
  }
});
~~~

~~~javascript
// 子页在装好监听器后向父页宣告 ready。
const parentOrigin = "https://app.example";
window.addEventListener("message", event => {
  if (event.origin !== parentOrigin || event.source !== window.parent) return;
  if (event.data?.type !== "refresh" || event.data.reportId !== 42) return;
  refreshEmbeddedReport();
});
window.parent.postMessage({ type: "ready" }, parentOrigin);
~~~

WebSocket 适合经过服务器的持续双向消息，不是两个标签页互相通知的默认方案。它的握手来源检查不等同于 Fetch 的 Cross-Origin Resource Sharing (跨源资源共享，CORS) 响应许可；服务端仍需检查握手 `Origin`、验证身份，并逐条授权敏感操作。连接建立后，WebSocket 也不会替业务消息提供去重、确认或断线补发。

**延伸阅读：** [流式报表断线重连后，界面怎样保留正确状态？](#54.%20%E6%B5%81%E5%BC%8F%E6%8A%A5%E8%A1%A8%E6%96%AD%E7%BA%BF%E9%87%8D%E8%BF%9E%E5%90%8E%EF%BC%8C%E7%95%8C%E9%9D%A2%E6%80%8E%E6%A0%B7%E4%BF%9D%E7%95%99%E6%AD%A3%E7%A1%AE%E7%8A%B6%E6%80%81%EF%BC%9F) 对接服务器事件；[报表页面里的状态应该放在哪里？](#52.%20%E6%8A%A5%E8%A1%A8%E9%A1%B5%E9%9D%A2%E9%87%8C%E7%9A%84%E7%8A%B6%E6%80%81%E5%BA%94%E8%AF%A5%E6%94%BE%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F) 说明本地状态的寿命与事务边界。

> [!info]- 来源
> - 跨文档消息、`postMessage` 目标源、`BroadcastChannel` 与共享 worker 的适用场景：[WHATWG HTML Standard，Web Messaging](https://html.spec.whatwg.org/multipage/web-messaging.html)，§9.3–9.5，2026-11-06 核对。
> - `BroadcastChannel` 消息结构化克隆：[WHATWG HTML Standard，Structured data](https://html.spec.whatwg.org/multipage/structured-data.html)，2026-11-06 核对。
> - 存储事件只向共享存储区中的其他文档派发：[WHATWG HTML Standard，Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，§12.2.4，2026-11-06 核对。
> - WebSocket 的连接、来源和消息协议：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，2026-11-06 核对。
> - `pagehide` 的 `persisted` 值用于表示页面可能留在历史缓存并在返回时复用；它不是可靠的最终退出通知：[WHATWG HTML Standard，PageTransitionEvent](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-pagetransitionevent-interface)，2026-11-06 核对。
## 54. 流式报表断线重连后，界面怎样保留正确状态？

案例背景：用户重开 `/reports/42?sort=recent#summary`。页面从服务端取到报表 42 的状态快照，再订阅进度；断线后浏览器会自动重连，但同一事件可能重放，页面也可能比服务端落后。界面需要分清传输游标、业务状态版本和报表终态。

本文沿用 [实时更新该选哪种传输？](../../engineering-foundations/networking/real-time-web-updates.md) 中的 Server-sent Events (服务器发送事件，SSE) 案例：初始快照为 `id=42, version=9, status=running, event_cursor=103`。这里快照 JSON 的 `id=42` 是报表资源标识；后续 SSE 事件行的 `id: 104` 才是日志续读游标；`version=9` 是报表状态的单调修订号；`status` 描述业务运行状态。这三者职责不同，不能相互比较。

### 页面要显示两种状态

服务端报表状态回答“报表现在是什么结果”；本地连接状态回答“页面是否正在接收更新”。连接短暂重连时，已有的报表快照仍然有用，但应标出更新正在恢复，而不把它误报成失败。

| 服务端报表状态 | 页面连接状态 | 可以显示什么 |
|---|---|---|
| `running` | 已连接 | 当前状态与最近一次进度；结果仍未完成 |
| `running` | 正在重连 | 保留最后可用状态并标注可能过时 |
| `ready` | 任意 | 已完成；停止进度订阅 |
| `failed` 或 `canceled` | 任意 | 显示服务端记录的终态；断线本身不能生成这种业务结论 |

`EventSource` 收到 `error` 时可能仍会自动重连，因此不能直接把报表标成 `failed`。当报表状态是 `ready`、`failed` 或 `canceled` 等终态时，页面可关闭事件源；产品应由 API 合同明确哪些状态终止这项工作。

~~~mermaid
flowchart TD
    Snapshot[读取报表快照和对应游标] --> Open[建立 SSE 连接]
    Open --> Wait[等待当前连接的下一事件]
    Wait --> Event{收到更新事件？}
    Event -->|没有新事件| Wait
    Event -->|版本较旧或重复| Wait
    Event -->|新版本| Apply[合并状态并更新界面]
    Apply --> Terminal{业务状态已终止？}
    Terminal -->|否| Wait
    Terminal -->|是| Close[关闭订阅]
    Wait -->|连接丢失| Reconnect[保留快照并显示重连中]
    Reconnect --> Resume[浏览器用原 EventSource 自动重连]
    Resume --> Wait
    Reconnect -->|游标过期 reset| Refresh[关闭旧连接并重新读取快照和游标]
    Refresh --> SnapshotTerminal{新快照是否仍在运行？}
    SnapshotTerminal -->|是| Open
    SnapshotTerminal -->|否| Close
~~~

### 怎样合并状态并从游标恢复？

第一次订阅必须接在与快照一致的位置之后。若快照版本 9 已涵盖事件日志游标 103，页面从 103 之后订阅；不能分别读取一个随时变化的快照和另一个独立游标，否则两者之间的更新可能被跳过。初连 URL 中的 `after` 是应用约定，原生 `EventSource` 不能让页面设置任意请求头。

服务器接着发出日志事件 104、105：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

接收端按 `version` 合并业务状态，按 SSE 的 `id` 续读事件。版本不大于本地版本时忽略重复或旧消息；更高版本才更新界面。本例事件包含该视图所需的最新状态。如果 API 发送的是依赖前序版本的增量补丁，发现版本不连续时应重新 GET 快照，而不能把缺少的字段猜出来。

~~~javascript
const initialSnapshot = { id: 42, version: 9, status: "running", progress: 0, event_cursor: "103" };
let report = {
  id: initialSnapshot.id,
  version: initialSnapshot.version,
  status: initialSnapshot.status,
  progress: initialSnapshot.progress,
};
let source;
let recoveryInProgress = false;
let recoveryAttempts = 0;
const reportStatuses = new Set(["running", "ready", "failed", "canceled"]);
const terminalStatuses = new Set(["ready", "failed", "canceled"]);

function subscribe(eventCursor) {
  const currentSource = new EventSource(`/api/reports/42/events?after=${encodeURIComponent(eventCursor)}`);
  source = currentSource;
  currentSource.addEventListener("open", () => {
    if (source === currentSource) showConnectionState("connected");
  });
  currentSource.addEventListener("report.updated", event => {
    if (source !== currentSource) return;
    let update;
    try {
      update = JSON.parse(event.data);
    } catch {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
      return;
    }
    if (!update || update.report_id !== report.id ||
        !Number.isSafeInteger(update.version) ||
        !reportStatuses.has(update.status) || !Number.isFinite(update.progress) ||
        update.progress < 0 || update.progress > 100) {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
      return;
    }
    // 合法的旧版本或重放帧不是坏数据；保留这条连接继续等待。
    if (update.version <= report.version) return;
    recoveryAttempts = 0;
    // EventSource 用 SSE id 续读；业务状态只按 report.version 合并。
    report = { ...report, version: update.version, status: update.status, progress: update.progress };
    renderReport(report);
    if (terminalStatuses.has(report.status)) closeCurrentSource(currentSource);
  });
  currentSource.addEventListener("reset", () => {
    if (source !== currentSource || terminalStatuses.has(report.status)) return;
    closeCurrentSource(currentSource);
    void refreshSnapshotAndSubscribe();
  });
  currentSource.addEventListener("error", () => {
    if (source !== currentSource || terminalStatuses.has(report.status)) return;
    if (currentSource.readyState === EventSource.CONNECTING) {
      showConnectionState("reconnecting");
    } else if (currentSource.readyState === EventSource.CLOSED) {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
    }
  });
}

function closeCurrentSource(currentSource) {
  if (source !== currentSource) return;
  source = undefined;
  currentSource.close();
}

async function refreshSnapshotAndSubscribe() {
  if (recoveryInProgress) return;
  if (recoveryAttempts >= 1) {
    showRefreshUnavailable();
    return;
  }
  recoveryAttempts += 1;
  recoveryInProgress = true;
  source?.close();
  source = undefined;
  try {
    const response = await fetch("/api/reports/42");
    if (!response.ok) throw new Error("Snapshot request failed");
    const snapshot = await response.json();
    if (snapshot.id !== report.id || !Number.isSafeInteger(snapshot.version) ||
        snapshot.version < report.version || !reportStatuses.has(snapshot.status) ||
        !Number.isFinite(snapshot.progress) || snapshot.progress < 0 || snapshot.progress > 100 ||
        typeof snapshot.event_cursor !== "string") {
      throw new Error("Invalid or older snapshot");
    }
    report = {
      id: snapshot.id,
      version: snapshot.version,
      status: snapshot.status,
      progress: snapshot.progress,
    };
    renderReport(report);
    if (!terminalStatuses.has(report.status)) subscribe(snapshot.event_cursor);
  } catch {
    // Keep the last usable report and show one bounded recovery error.
    showRefreshUnavailable();
  } finally {
    recoveryInProgress = false;
  }
}

subscribe(initialSnapshot.event_cursor);
~~~

初连请求为 `GET /api/reports/42/events?after=103`。当连接读到事件 104 后断开，浏览器重连仍访问同一 URL（包括 `?after=103`），并附带 `Last-Event-ID: 104`；本例的服务端合同规定，有效的 `Last-Event-ID` 优先于初始查询参数，因此从 104 之后续读事件 105。若本地已合并到仍在运行的版本 10，再收到版本 10 时会直接忽略，并让同一 EventSource 继续等待；版本 11 已是 `ready`，接受后就关闭订阅。`event_cursor` 只存在于初始或重新取得的快照中，不是自动变化的本地状态。`Last-Event-ID` 表示浏览器已解析到该事件位置，不表示应用监听器已经完成渲染、写入本地库或执行外部副作用。只关心最新报表状态时，按 `version` 去重并在恢复后读取权威快照足够；若每条业务事件都必须处理，则另需持久记录已处理 ID、去重和显式确认。

游标过期时，服务器可发送含 `data` 并以空行结束的 `event: reset`，浏览器才会派发事件。页面关闭旧 EventSource，重新 GET 一致快照和游标；版本较旧或数据无效时保留原显示并提示一次恢复失败，只有新快照仍为 `running` 才用新游标订阅。若快照已是 `ready`、`failed` 或 `canceled`，展示它并保持连接关闭。`EventSource` 的 `error` 若状态为 `CONNECTING`，表示浏览器仍在重连；若为 `CLOSED`，示例转为一次快照恢复。连续 reset、坏帧或立即关闭最多自动恢复一次；接收更高业务版本后才重置这个预算，避免反复重取或重连。恢复失败后显示错误。

### Fetch 自定义流和 SSE 有什么不同？

若 API 需要自定义请求头或 POST 查询，再考虑 Fetch 响应流。`reader.read()` 给出的是任意字节块，不保证一个块刚好是一条记录；UTF-8 字符和 JSON 记录都可能跨块。需要自己持续解码、缓冲到完整分隔符、校验字段和终止条件。传输方式比较见上述实时更新说明；本节聚焦界面和 parser (解析器) 的责任。

旧例还保留了一个自定义 newline-delimited JSON (按行分隔的 JSON，NDJSON) 作业协议模型。它与前面的 SSE 报表协议不同：模型中的 `runId` 标识一次生成作业，`seq` 是该私有日志的应用游标；它既不是 SSE 的 `id`，也不是报表 `version`。客户端用幂等键提交作业并获得稳定 `runId`，续读时带已接受的 `seq`；旧序号可重放并丢弃，跳号则拒绝，作业最终状态仍以状态接口为准。该模型限制单条帧为 8,192 个 UTF-16 代码单元、可见输出为 64 Ki 代码单元，并覆盖坏 JSON、提早 EOF、超时和本地取消；EOF 本身不等于收到终态。以下折叠段保留协议示例与可执行模型，供确实采用自定义 NDJSON API 的场景参考。

> [!example]- 自定义 Fetch/NDJSON 作业 parser 与断线案例
> 此实现是 Node Web Streams 与 Response API 上的合成协议模型，不是浏览器端到端或生产服务测试；八组断言覆盖 UTF-8 与帧跨块、合并帧、服务端错误、格式错误、提前结束、断线、超时、本地中止及渲染回调返回后阻止消费已缓冲的终态。
>
> ~~~text
> POST /api/runs
> Idempotency-Key: submit-7f2a
> {"prompt":"Summarize the public release notes"}
>
> 202 Accepted
> {"runId":"run-7f2a","status":"queued"}
>
> GET /api/runs/run-7f2a/events?after=0
> Content-Type: application/x-ndjson
>
> {"type":"delta","seq":1,"text":"The release adds "}
> {"type":"delta","seq":2,"text":"a search filter."}
> {"type":"complete","seq":3,"runId":"run-7f2a"}
> ~~~
>
> 这个小协议展示提交幂等键、稳定作业 ID、续读序号与明确终态；它是应用契约示例，不是浏览器标准。下面的 parser 会逐块解码并验证序号，遇到没有终态的 EOF 时保留部分文本但不标为完成。
>
> ~~~javascript
> import assert from "node:assert/strict";
>
> const MAX_FRAME_CHARS = 8 * 1024;
> const MAX_OUTPUT_CHARS = 64 * 1024;
> const DECODE_SLICE_BYTES = 4 * 1024;
>
> function readWithSignal(reader, signal) {
>   if (!signal) return reader.read();
>   const abortReason = () => signal.reason ?? new DOMException("Aborted", "AbortError");
>   if (signal.aborted) return Promise.reject(abortReason());
>
>   return new Promise((resolve, reject) => {
>     const onAbort = () => reject(abortReason());
>     signal.addEventListener("abort", onAbort, { once: true });
>     reader.read().then(resolve, reject).finally(() => {
>       signal.removeEventListener("abort", onAbort);
>     });
>   });
> }
>
> async function consumeRun(response, {
>   runId,
>   signal,
>   afterSequence = 0,
>   currentOutputChars = 0,
>   onState = () => {},
>   onText = async () => {},
> } = {}) {
>   let state = "idle";
>   let sequence = afterSequence;
>   let outputChars = currentOutputChars;
>   let carry = "";
>   let terminal = false;
>   let errorCode;
>   let detail;
>   let reader;
>   const decoder = new TextDecoder("utf-8", { fatal: true });
>
>   const transition = next => {
>     const allowed = {
>       idle: ["connecting", "canceled"],
>       connecting: ["streaming", "completed", "failed", "canceled"],
>       streaming: ["connecting", "completed", "failed", "canceled"],
>     };
>     if (state === next) return;
>     if (!allowed[state]?.includes(next)) {
>       throw new Error("Invalid view-state transition: " + state + " -> " + next);
>     }
>     state = next;
>     onState(state);
>   };
>
>   const result = () => ({ state, sequence, outputChars, errorCode, detail });
>
>   async function acceptLine(line) {
>     signal?.throwIfAborted();
>     if (terminal) throw new Error("Frame received after a terminal frame");
>     if (!line) throw new Error("Empty frame");
>     if (line.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
>
>     let event;
>     try {
>       event = JSON.parse(line);
>     } catch {
>       throw new Error("Malformed JSON frame");
>     }
>
>     if (!event || Array.isArray(event) || typeof event !== "object") {
>       throw new Error("Frame must be a JSON object");
>     }
>     if (!Number.isSafeInteger(event.seq) || event.seq < 1) {
>       throw new Error("Frame has an invalid sequence number");
>     }
>     if (event.seq <= sequence) return; // replayed event already applied
>     if (event.seq !== sequence + 1) throw new Error("Event sequence gap");
>     if (typeof event.type !== "string") throw new Error("Frame has no event type");
>
>     if (event.type === "delta") {
>       if (typeof event.text !== "string") throw new Error("Delta text must be a string");
>       if (outputChars + event.text.length > MAX_OUTPUT_CHARS) {
>         throw new Error("Output exceeds the display limit");
>       }
>       if (state === "connecting") transition("streaming");
>       await onText(event.text, signal);
>       // onText 成功返回表示这一整帧已经应用；这才是可续读的位置。
>       sequence = event.seq;
>       outputChars += event.text.length;
>       signal?.throwIfAborted();
>       return;
>     }
>
>     if (event.type === "complete") {
>       if (event.runId !== runId) throw new Error("Terminal frame has the wrong runId");
>       sequence = event.seq;
>       terminal = true;
>       transition("completed");
>       return;
>     }
>
>     if (event.type === "error") {
>       if (typeof event.code !== "string" || !event.code) {
>         throw new Error("Error frame has no error code");
>       }
>       sequence = event.seq;
>       errorCode = event.code;
>       terminal = true;
>       transition("failed");
>       return;
>     }
>
>     throw new Error("Unknown event type");
>   }
>
>   async function feedText(text) {
>     carry += text;
>     let newline;
>     while ((newline = carry.indexOf("\n")) !== -1) {
>       let line = carry.slice(0, newline);
>       carry = carry.slice(newline + 1);
>       if (line.endsWith("\r")) line = line.slice(0, -1);
>       await acceptLine(line);
>       if (terminal) return;
>     }
>     if (carry.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
>   }
>
>   transition("connecting");
>   try {
>     if (!response.body) throw new Error("Response has no body");
>     reader = response.body.getReader();
>     if (!response.ok) throw new Error("HTTP " + response.status);
>     if (!response.headers.get("content-type")?.toLowerCase().includes("application/x-ndjson")) {
>       throw new Error("Unexpected response content type");
>     }
>
>     while (true) {
>       const { done, value } = await readWithSignal(reader, signal);
>       if (done) {
>         await feedText(decoder.decode());
>         if (terminal) return result();
>         if (carry.length) throw new Error("EOF inside an unterminated frame");
>         throw new Error("EOF before a terminal frame");
>       }
>
>       for (let offset = 0; offset < value.byteLength; offset += DECODE_SLICE_BYTES) {
>         const part = value.subarray(offset, offset + DECODE_SLICE_BYTES);
>         await feedText(decoder.decode(part, { stream: true }));
>         if (terminal) return result();
>       }
>     }
>   } catch (error) {
>     detail = error instanceof Error ? error.message : String(error);
>     if (signal?.aborted && signal.reason?.name === "TimeoutError") {
>       transition("failed");
>     } else if (signal?.aborted) {
>       transition("canceled");
>     } else {
>       transition("failed");
>     }
>     return result();
>   } finally {
>     if (reader) {
>       try {
>         await reader.cancel();
>       } catch {
>         // Preserve the parse, read, timeout, or abort result.
>       }
>       reader.releaseLock();
>     }
>   }
> }
>
> const encoder = new TextEncoder();
> const asBytes = text => encoder.encode(text);
>
> function responseFrom(chunks, { open = false, status = 200 } = {}) {
>   const body = new ReadableStream({
>     start(controller) {
>       for (const chunk of chunks) controller.enqueue(chunk);
>       if (!open) controller.close();
>     },
>   });
>   return new Response(body, {
>     status,
>     headers: { "content-type": "application/x-ndjson; charset=utf-8" },
>   });
> }
>
> function responseDisconnectAfter(chunk) {
>   let sent = false;
>   const body = new ReadableStream({
>     pull(controller) {
>       if (!sent) {
>         sent = true;
>         controller.enqueue(chunk);
>       } else {
>         controller.error(new Error("Connection dropped"));
>       }
>     },
>   }, { highWaterMark: 0 });
>   return new Response(body, {
>     headers: { "content-type": "application/x-ndjson; charset=utf-8" },
>   });
> }
>
> async function check(name, response, expectedState, expectedText = "", options = {}) {
>   const states = [];
>   let text = "";
>   const result = await consumeRun(response, {
>     runId: "run-7",
>     ...options,
>     onState: state => states.push(state),
>     onText: chunk => { text += chunk; },
>   });
>   assert.equal(result.state, expectedState, name);
>   assert.equal(text, expectedText, name + " partial text");
>   return { result, states };
> }
>
> // Split one multibyte character and one record across reads; the final read
> // also contains a coalesced complete record.
> const multibyte = asBytes("好");
> const normal = await check(
>   "split UTF-8 and coalesced frames",
>   responseFrom([
>     asBytes('{"type":"delta","seq":1,"text":"你'),
>     multibyte.slice(0, 1),
>     multibyte.slice(1),
>     asBytes('"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
>   ]),
>   "completed",
>   "你好",
> );
> assert.deepEqual(normal.states, ["connecting", "streaming", "completed"]);
> console.log("PASS normal, multibyte split, frame split, and coalesced frames");
>
> const serverError = await check(
>   "server error frame",
>   responseFrom([asBytes('{"type":"error","seq":1,"code":"MODEL_UNAVAILABLE"}\n')]),
>   "failed",
> );
> assert.equal(serverError.result.errorCode, "MODEL_UNAVAILABLE");
> console.log("PASS terminal server-error frame");
>
> const malformed = await check(
>   "malformed JSON",
>   responseFrom([asBytes("{not-"), asBytes("json}\n")]),
>   "failed",
> );
> assert.match(malformed.result.detail, /Malformed JSON/);
> console.log("PASS malformed frame split across reads");
>
> const prematureEof = await check(
>   "premature EOF",
>   responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')]),
>   "failed",
>   "partial",
> );
> assert.match(prematureEof.result.detail, /EOF before a terminal frame/);
> console.log("PASS EOF preserves partial text but does not complete");
>
> const disconnected = await check(
>   "abrupt disconnect",
>   responseDisconnectAfter(asBytes('{"type":"delta","seq":1,"text":"partial"}\n')),
>   "failed",
>   "partial",
> );
> assert.match(disconnected.result.detail, /Connection dropped/);
> console.log("PASS abrupt disconnect preserves partial text but does not complete");
>
> const timeoutController = new AbortController();
> const timeoutTimer = setTimeout(() => {
>   timeoutController.abort(new DOMException("Deadline exceeded", "TimeoutError"));
> }, 5);
> const timeout = await check(
>   "timeout",
>   responseFrom([], { open: true }),
>   "failed",
>   "",
>   { signal: timeoutController.signal },
> );
> clearTimeout(timeoutTimer);
> assert.match(timeout.result.detail, /Deadline exceeded/);
> console.log("PASS timeout remains a failure, not completion");
>
> const stopController = new AbortController();
> const stopTimer = setTimeout(() => {
>   stopController.abort(new DOMException("Stopped by user", "AbortError"));
> }, 5);
> const stopped = await check(
>   "explicit abort after partial text",
>   responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')], { open: true }),
>   "canceled",
>   "partial",
>   { signal: stopController.signal },
> );
> clearTimeout(stopTimer);
> assert.match(stopped.result.detail, /Stopped by user/);
> console.log("PASS explicit abort keeps partial text and marks only the local view canceled");
>
> const bufferedRaceController = new AbortController();
> const bufferedRaceStates = [];
> let bufferedRaceText = "";
> const bufferedRace = await consumeRun(responseFrom([
>   asBytes('{"type":"delta","seq":1,"text":"partial"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
> ]), {
>   runId: "run-7",
>   signal: bufferedRaceController.signal,
>   onState: state => bufferedRaceStates.push(state),
>   onText: async chunk => {
>     bufferedRaceText += chunk;
>     await Promise.resolve();
>     bufferedRaceController.abort(new DOMException("Stopped while rendering", "AbortError"));
>   },
> });
> assert.equal(bufferedRace.state, "canceled");
> assert.equal(bufferedRace.sequence, 1);
> assert.equal(bufferedRace.outputChars, "partial".length);
> assert.equal(bufferedRaceText, "partial");
> assert.deepEqual(bufferedRaceStates, ["connecting", "streaming", "canceled"]);
> assert.match(bufferedRace.detail, /Stopped while rendering/);
> console.log("PASS abort after text callback returns prevents a buffered terminal frame");
> ~~~

本地 `AbortController.abort()` 或取消 reader 只会结束当前页面对响应体的读取，不证明服务端工作停止。若产品允许取消作业，还要发取消请求并查询权威作业状态，直到服务端报告终态。`onText` 成功返回表示整帧文本已完整接收并应用，只有此后才推进 `sequence` 和输出长度；回调若先应用部分文本再拒绝，就无法安全确定续读点。解析器在等待 `onText` 时不能强行打断任意 Promise，回调必须有界并自行响应传入的取消信号，或让其完成后再处理中止。示例的竞争测试仅证明渲染回调返回后，中止会阻止消费同一缓冲区里的终态帧。解析器等待回调完成也形成背压：若回调将 DOM 写入排入队列，应在队列保持较小时再读取下一块；可以用 `requestAnimationFrame` 合并可见更新，但它不提供恢复保证。路由卸载时释放 reader 和事件源，保留有用但不完整的文本，并将其标为部分结果。将收到的状态先交给本地 reducer 或事件总线再更新多个视图时，监听器重入也可能改变处理顺序；见[事件总线重入案例](#56.%20JavaScript%20%E4%BA%8B%E4%BB%B6%E6%80%BB%E7%BA%BF%E5%9C%A8%E7%9B%91%E5%90%AC%E5%99%A8%E4%B8%AD%E9%87%8D%E5%85%A5%E6%97%B6%E6%80%8E%E6%A0%B7%E4%BF%9D%E6%8C%81%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

渲染本身也应有界：把同一帧中到达的文本增量合并后每帧更新一次，而不是每个 token 都刷新 DOM；输出很长时限制缓冲或只渲染可见窗口。状态区域使用 `role="status"` 与 `aria-live="polite"` 可播报连接、完成或失败，但不要逐字播报每个 token。

**延伸阅读：** [实时更新该选哪种传输？](../../engineering-foundations/networking/real-time-web-updates.md) 定义 SSE 的线格式、id/version 和重连边界；[API 可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) 讨论未知结果与安全重试；[JavaScript 事件总线在监听器中重入时怎样保持顺序？](#56.%20JavaScript%20%E4%BA%8B%E4%BB%B6%E6%80%BB%E7%BA%BF%E5%9C%A8%E7%9B%91%E5%90%AC%E5%99%A8%E4%B8%AD%E9%87%8D%E5%85%A5%E6%97%B6%E6%80%8E%E6%A0%B7%E4%BF%9D%E6%8C%81%E9%A1%BA%E5%BA%8F%EF%BC%9F) 讨论把一个状态更新送到本地多个模块。

若应用交付的是持久 AI run 的完整事件，本篇负责传输解码、断线续读与本地取消边界；事件到达后如何把 `runId`、序号、工具调用与不完整 Markdown 安全地投影到聊天界面，见[一轮 AI 聊天怎样安全展示增量回答、工具状态与恢复操作](#55.%20%E4%B8%80%E8%BD%AE%20AI%20%E8%81%8A%E5%A4%A9%E6%80%8E%E6%A0%B7%E5%AE%89%E5%85%A8%E5%9C%B0%E5%B1%95%E7%A4%BA%E5%A2%9E%E9%87%8F%E5%9B%9E%E7%AD%94%E3%80%81%E5%B7%A5%E5%85%B7%E7%8A%B6%E6%80%81%E4%B8%8E%E6%81%A2%E5%A4%8D%E6%93%8D%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - SSE 字段解析、EventSource 自动重连和 `Last-Event-ID`：[WHATWG HTML Standard，Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，2026-11-06 核对；报表 42 的 `id`、`version` 和终态沿用[实时更新协议案例](../../engineering-foundations/networking/real-time-web-updates.md)。
> - Fetch 响应体与 keepalive、流读取、reader 取消：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)；[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，2026-11-06 核对。
> - 增量 UTF-8 解码：[WHATWG Encoding Standard，TextDecoder](https://encoding.spec.whatwg.org/#interface-textdecoder)，2026-11-06 核对。
> - `AbortController` 和 `AbortSignal` 的 API 语义：[WHATWG DOM Standard](https://dom.spec.whatwg.org/#interface-abortcontroller)，2026-11-06 核对。
> - `role="status"` 的状态播报语义：[W3C WAI-ARIA 1.2，status role](https://www.w3.org/TR/wai-aria-1.2/#status)，2026-11-06 核对。
## 55. 一轮 AI 聊天怎样安全地展示增量回答、工具状态与恢复操作？

**案例背景。** 开发者要求：“解释 build 42 的失败并准备缺陷单；提交前让我审核。”运行服务已鉴权并创建 `run-r42-7`。只读工具 `read_build_log` 的调用标识是 `c1`；它查到 `unit-tests` 中 `reject_empty_name` 预期 Hypertext Transfer Protocol（超文本传输协议，HTTP）`400`、实际 HTTP `200`、进程退出状态为 `1`。拿到这项证据前，界面只能显示正在检查，不能先把根因写成结论。随后运行生成解释和待审核的缺陷单草稿，进入 `awaiting_approval`；审核人批准仍未变化的草稿后，同一运行才会调用创建工单动作。`runId` 标识持久运行，事件 `seq` 表示本应用日志顺序，`c1` 配对模型工具请求与结果；它们不是连接 ID，也不能互相替代。案例中的 ID、构建资料和工单均为合成教学数据。

本篇从[流式传输已经交付哪些完整事件](#54.%20%E6%B5%81%E5%BC%8F%E6%8A%A5%E8%A1%A8%E6%96%AD%E7%BA%BF%E9%87%8D%E8%BF%9E%E5%90%8E%EF%BC%8C%E7%95%8C%E9%9D%A2%E6%80%8E%E6%A0%B7%E4%BF%9D%E7%95%99%E6%AD%A3%E7%A1%AE%E7%8A%B6%E6%80%81%EF%BC%9F)之后开始：客户端已经解出一条完整的 JavaScript Object Notation（JavaScript 对象表示法，JSON）应用事件，接下来要验证它属于哪次运行、只应用一次，并把未完成的 Markdown 与工具结果当作不可信内容安全呈现。运行状态、审批和副作用的权威恢复记录仍由[AI 运行如何断线恢复并避免副作用重复](../../ai-engineering/systems/ai-application-architecture.md)负责；聊天组件不能凭最后看到的一帧推断服务端状态。

~~~mermaid
flowchart TD
  Snapshot[读取完整投影与同一游标] --> Events[接收完整事件]
  Events --> Identity{runId 与 seq 有效？}
  Identity -->|旧序号| Ignore[忽略重放]
  Identity -->|序号跳跃| Catchup[同一 run 补读历史]
  Identity -->|下一序号| Reduce[更新同一条消息或工具卡]
  Reduce --> Safe[Markdown 全文解析后消毒；工具摘要按文本呈现]
  Safe --> View[显示内容、运行态与连接态]
  View --> Approval{已有证据和待审草稿？}
  Approval -->|否| ReadOnly[继续读取并准备草稿]
  Approval -->|是| Awaiting[awaiting_approval：展示绑定的草稿]
  Awaiting -->|批准未变化草稿| Resume[同一 run 恢复写入]
  Resume -->|结果未知| Reconcile[原操作键对账]
  Reconcile -->|确认 ISSUE-842 已创建| Attach[更新原 c2 卡片与原 run]
  Attach --> Done[权威结果确认后 completed]
  View --> Action{停止或新一轮尝试}
  Action -->|停止| Cancel[请求取消并查询权威状态]
  Action -->|重试| NewRun[确认旧写未发生且不会迟到后才创建]
~~~

图中补读、恢复、取消和对账都是原运行的服务端动作；单纯重连只恢复事件交付。下表把 `run-r42-7` 的应用事件投影到稳定的界面项目。`seq` 是此合成应用协议的字段，不是 MCP 的 JSON-RPC ID，也不是任何传输标准自动提供的字段。`c2` 是本例第二个模型工具调用的合成标识，绑定创建缺陷单动作；远端操作键另为 `run-r42-7:create-issue:v1`。

| 事件 | 客户端投影 | 身份与更新规则 |
|---|---|---|
| `seq=1, run.status=running` | 同一轮回答显示“正在检查” | 仅更新 `run-r42-7` 的运行状态 |
| `seq=2, assistant.delta` | 助手气泡显示“正在读取 build 42 日志” | 还没有失败证据，不能先陈述根因 |
| `seq=3, tool.started, toolCallId=c1` | 创建“读取构建日志”卡片并显示等待 | 卡片键使用 `(runId, toolCallId)`，重放时更新原卡片 |
| `seq=4, tool.completed, toolCallId=c1` | 将卡片标为“只读结果已返回”，展示失败测试摘要 | 结果必须配回 `c1`；正文是数据，不是可执行指令 |
| `seq=5, assistant.delta` | 同一气泡解释 `reject_empty_name` 实际返回 HTTP 200，并告知正在准备缺陷单草稿 | 证据已到达，草稿仍在运行中生成 |
| `seq=6, run.status=awaiting_approval` | 同一事件携带持久草稿投影，显示仓库、标题、正文、证据摘要和审核按钮 | `payloadHash` 标识这份精确动作摘要；此时尚未创建工单 |
| `seq=7, run.status=running` | 用户批准后，同一轮恢复执行并显示“正在提交已审核草稿” | 运行 ID 不变，事件游标继续递增 |
| `seq=8, tool.started, toolCallId=c2` | 创建“创建缺陷单”卡片 | `c2` 配对工具请求；远端操作键为 `run-r42-7:create-issue:v1` |
| `seq=9, tool.effect_unknown, toolCallId=c2` | 卡片显示“提交结果待对账” | 超时不能显示失败或触发盲重发；原操作可能已创建工单 |
| `seq=10, run.status=effect_unknown` | 运行显示“外部结果待确认” | 运行账本保留原键、请求摘要和待对账状态 |
| `seq=11, tool.completed, toolCallId=c2` | 同一张卡片显示对账得到的 `ISSUE-842` | 原操作键结果已确认，不创建第二个 run 或工单 |
| `seq=12, assistant.delta` | 同一气泡告知工单 `ISSUE-842` 已存在 | 只追加本轮文本，工单结果继续配回 `c2` |
| `seq=13, run.status=completed` | 显示已完成并停止等待更多事件 | 只有权威副作用记录确认结果后才进入终态 |

### 怎样应用重放事件而不重复消息或工具卡？

重新打开对话时，先从服务端读取 `run-r42-7` 的权威投影快照及其游标，再订阅后续事件。快照里的 `lastSeq` 和此前已应用的文本、工具卡片、运行状态必须来自同一版本。事件必须通过边界校验：`runId` 必须匹配；`seq` 是安全整数；事件类型和必需字段属于允许集合；工具事件有非空 `toolCallId`。事件顺序使用一个客户端游标：重复序号不再追加，下一序号正常推进，出现缺口则先补读。下面将这三个分支写成投影函数。

> [!example]- 代码：按运行与事件游标更新聊天投影
> ~~~typescript
> type RunEvent = {
>   runId: string;
>   seq: number;
>   type: "assistant.delta" | "tool.started" | "tool.effect_unknown" | "tool.completed" | "run.status";
>   toolCallId?: string;
>   toolName?: string;
>   text?: string;
>   status?: "running" | "awaiting_approval" | "effect_unknown" | "completed" | "failed" | "rejected" | "cancel_requested" | "canceled";
>   summary?: string;
>   approvalDraft?: ApprovalDraftView;
> };
>
> type ApprovalDraftView = {
>   repositoryId: string;
>   title: string;
>   body: string;
>   evidenceSummary: string;
>   payloadHash: string;
> };
>
> type Projection = {
>   runId: string;
>   lastSeq: number;
>   assistantText: string;
>   tools: Map<string, { name: string; status: "running" | "effect_unknown" | "completed"; summary?: string }>;
>   runStatus: string;
>   approvalDraft?: ApprovalDraftView;
> };
>
> function applyEvent(view: Projection, event: RunEvent): Projection | "catch-up" | "ignore" {
>   if (event.runId !== view.runId || !Number.isSafeInteger(event.seq) || event.seq < 1) {
>     throw new Error("Invalid run event identity");
>   }
>   if (event.seq <= view.lastSeq) return "ignore"; // 同一日志游标的重放不能再次追加
>   if (event.seq !== view.lastSeq + 1) return "catch-up"; // 不跳过缺失的增量
>
>   const next = { ...view, lastSeq: event.seq, tools: new Map(view.tools) };
>   if (event.type === "assistant.delta") {
>     if (typeof event.text !== "string") throw new Error("Invalid text delta");
>     next.assistantText += event.text;
>   } else if (event.type === "tool.started") {
>     if (!event.toolCallId || !event.toolName) throw new Error("Missing tool identity");
>     const prior = next.tools.get(event.toolCallId);
>     next.tools.set(event.toolCallId, prior ?? { name: event.toolName, status: "running" });
>   } else if (event.type === "tool.effect_unknown") {
>     if (!event.toolCallId) throw new Error("Missing toolCallId");
>     const prior = next.tools.get(event.toolCallId);
>     if (!prior) throw new Error("Unknown tool operation");
>     next.tools.set(event.toolCallId, { ...prior, status: "effect_unknown" });
>   } else if (event.type === "tool.completed") {
>     if (!event.toolCallId || typeof event.summary !== "string") {
>       throw new Error("Invalid tool result");
>     }
>     const prior = next.tools.get(event.toolCallId);
>     if (!prior) throw new Error("Tool result has no matching request");
>     next.tools.set(event.toolCallId, { ...prior, status: "completed", summary: event.summary });
>   } else if (event.type === "run.status") {
>     if (typeof event.status !== "string") throw new Error("Invalid run status");
>     next.runStatus = event.status;
>     if (event.status === "awaiting_approval") {
>       if (!event.approvalDraft) throw new Error("Missing persisted approval draft projection");
>       next.approvalDraft = event.approvalDraft;
>     }
>   }
>   return next;
> }
>
> // 服务端在游标 3 生成快照时，必须一起提供此前的文本和 c1 卡片。
> const snapshotAt3: Projection = {
>   runId: "run-r42-7",
>   lastSeq: 3,
>   assistantText: "正在读取 build 42 日志",
>   tools: new Map([["c1", { name: "read_build_log", status: "running" as const }]]),
>   runStatus: "running",
> };
> const after4 = applyEvent(snapshotAt3, {
>   runId: "run-r42-7", seq: 4, type: "tool.completed", toolCallId: "c1",
>   summary: "reject_empty_name: expected HTTP 400, actual HTTP 200, exit 1",
> });
> if (after4 === "catch-up" || after4 === "ignore") throw new Error("Expected c1 card update");
> ~~~

此投影器假定上游已把不可信 JSON 解析为 `unknown` 并检查字段；TypeScript 类型声明不会验证网络数据。真实应用的 schema（结构模式）还应约束工具名称、状态转换和文本大小。事件序号重复时不再追加文本；遇到跳号先向同一个运行补读历史或重新取得权威快照，不能把之后的增量接到缺失内容上。恢复快照必须把 `lastSeq` 和该游标之前的**完整可见投影**作为同一一致版本：示例 `lastSeq=3` 快照含 `seq=2` 的助手文本和状态为 `running` 的 `c1` 卡片，因此 `seq=4` 可以更新已存在的卡片。若只恢复 `runStatus` 与 `lastSeq`，下一条 `tool.completed(c1)` 会找不到卡片；如果服务只能给状态与最新位置，客户端须从已有本地投影位置重放，或从可重放起点补齐，不能跳到服务端最新序号。序号绑定的是本客户端可见的应用事件流。本例每个 run 只创建一个助手气泡，所以以 `runId` 作为气泡 key 足够；若一个 run 会生成多条助手消息，事件与持久记录还需提供稳定 `messageId`，key 才能用 `(runId, messageId)`。工具卡片的 Document Object Model（文档对象模型，DOM）key 使用稳定的 `(runId, toolCallId)`，不要按数组下标或每次渲染时的随机值生成，否则一次重连可能重建卡片、丢失展开状态或重复宣告结果。`c1` 是模型工具调用 ID；若工具来自 Model Context Protocol（模型上下文协议，MCP），其 JSON-RPC 请求 ID 仍是另一层相关标识。

断线时保留最后一条可用文本和卡片，并把连接标为“正在恢复”。重新打开处于 `awaiting_approval` 的运行时，权威快照或可重放的 `run.status` 事件还要携带服务端已保存的审批草稿投影：目标仓库、标题、正文、证据摘要和 `payloadHash`。运行记录中的 `payload_hash` 映射为这个客户端字段；它绑定精确动作内容。按钮提交 `runId` 与该 hash，而不让客户端重组待写入 payload；服务端在接收批准时重新核对当前保存的摘要和权限，任一变化就让旧批准失效并要求重新审核。hash 不替代身份、授权或批准。只有运行 API 报告的状态决定它是否仍在运行或已终止：EOF、浏览器关闭连接、收到一个完成样式的文本片段，都不足以证明 `completed`。普通问答和受审批控制的工具运行共用这个投影层，但运行控制权仍归服务端。

### 不完整 Markdown 和工具结果怎样安全显示？

流中的 Markdown 可能跨多个事件结束。下面的三项是准确的 JavaScript 字符串；分片边界不插入任何字符，片段 2 以 `java` 结束，片段 3 以 `script:` 开始：

~~~typescript
const chunks = [
  "日志显示为：\n\n```text\n<not executed>\n",
  "```\n\n[打开链接](java",
  "script:alert(1))",
];
let accumulated = "";
const frames: string[] = [];
for (const chunk of chunks) {
  accumulated += chunk; // 不在分片之间添加空格或换行
  frames.push(accumulated); // 每帧都把完整文本交给后文的 safeMarkdown
}
~~~

不要用正则表达式拼一个“增量 HTML 解析器”，也不要把片段直接拼进 `innerHTML`。数组第一项含未闭合代码围栏，第二项关闭围栏并开始链接目标，第三项直接接上 `script:`，所以累计 Markdown 中确实有危险 URI `javascript:alert(1)`，不是换行导致的无效链接。每次都从同一助手消息的完整累计 Markdown 重新解析，再在 HyperText Markup Language（超文本标记语言，HTML）注入点前消毒；代码围栏与链接在各个中间帧都按同一安全路径处理。验证时先检查 Marked 18.1.3 的未净化输出含完整 `href="javascript:alert(1)"`，再确认 DOMPurify 输出已移除该 href；仅检查最终 DOM 不足以证明测试真的生成过危险目标。

~~~tsx
import { marked } from "marked";
import DOMPurify from "dompurify";

const chatPolicy = {
  USE_PROFILES: { html: true },
  // 只保留 HTTPS/HTTP、站内根路径和片段链接；不允许图片远程加载。
  ALLOWED_URI_REGEXP: /^(?:https?:\/\/|\/(?!\/)|#)/i,
  FORBID_TAGS: ["img", "style", "iframe", "audio", "video"],
  FORBID_ATTR: ["target", "style"],
};

function safeMarkdown(source: string): string {
  const generated = marked.parse(source, { async: false });
  if (typeof generated !== "string") throw new Error("Unexpected async Markdown parser");
  return DOMPurify.sanitize(generated, chatPolicy);
}

function AssistantMessage({ text }: { text: string }) {
  const html = safeMarkdown(text); // 每次更新对完整消息重解析并消毒
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}
~~~

这里的 `marked` 只负责把 Markdown 变成 HTML；它不负责净化结果。`DOMPurify` 在受控的 HTML sink 前运行，并对 URI 使用窄白名单。消毒后不能再把内容交给会改写 DOM 的高亮器或插件；若之后确有改写，必须在最终写入前重新消毒。示例使用 Marked 18.1.3 和 DOMPurify 3.4.17；若不需要富文本，直接把字符串放进 React 文本子节点或 DOM `textContent` 更简单。此示例将外部图片、样式和新窗口链接排除；这些能力只有在产品需要且有独立策略时才应加入。

工具输出也不是可信 HTML。对 `c1` 的只读结果，只把已检查的 `step`、`failed_test`、`expected`、`actual` 和 `exit_status` 映射为文本节点；例如 `summary.textContent = tool.summary`。若需要渲染 Markdown，同样完整解析、消毒后再显示。卡片上的“运行中”“已返回”“失败”等标签来自允许的运行事件；内容渲染本身不执行工具，不把模型的工具请求当成浏览器命令，也不以显示一个成功样式图标代替服务端结果。

### 停止、继续和重试分别改变什么？

用户操作应同时显示所针对的运行和操作结果。连接重连是传输行为；停止是发给运行服务的控制请求；继续和重试则有不同的运行身份：

| 操作 | 客户端动作 | `runId` 与已有文本 | 何时可安全呈现 |
|---|---|---|---|
| 重连 | 按最后已应用序号重新读取同一次运行 | 仍为 `run-r42-7`；忽略旧 `seq`、补齐缺口 | 断线不取消后台运行，也不清空部分回答 |
| 停止 | 对当前运行发送已鉴权的取消请求，然后查询运行状态 | 仍为 `run-r42-7`；保留部分文本并显示“取消请求处理中” | 收到服务端 `canceled` 才显示已取消；若动作结果仍未知，继续显示待确认 |
| 继续 | 用户审批当前未变的待审批草稿，提交给恢复端点 | 同一个 `run-r42-7`；运行序号继续向前 | 草稿摘要或权限变化会使旧审批失效，须重新确认；写入结果未知时仍沿同一 run 对账 |
| 重试 | 只有权威确认旧写入未发生且不会迟到后，用户仍要求尝试，才提交新请求 | 新意图创建新的 `runId` 和事件序号；旧消息保留 | 若原操作已成功，把原工单显示在原 `c2` 卡片并结束原 run；若结果仍未知，不创建同效的新 run |

`AbortController.abort()` 或关闭 SSE/Fetch reader 只停止当前连接的读取，不证明服务端已停止生成或工具已取消。停止按钮若发送取消请求，事件仍可能晚到；界面可以保留它们，但要以服务端最终状态更新标记。审批继续只唤醒原有已持久化运行和操作摘要，不重新提交初始问题；权限、目标或草稿改变时再次确认。`run-r42-7` 的审批通过后按稳定操作键 `run-r42-7:create-issue:v1` 创建工单。若远端超时，原 `c2` 卡片保持待对账；对账确认 `ISSUE-842` 已创建时，把该 ID 与最终文本写回原 run，再显示完成，不能通过新 run 再做同一效果。只有服务权威确认旧写未提交且不会迟到，才允许用户以新 `runId` 再试。此边界沿用[工具请求怎样成为一次获准的应用操作](../../ai-engineering/agents/tool-design-and-function-calling.md)与[运行服务的副作用恢复契约](../../ai-engineering/systems/ai-application-architecture.md)。

> [!info]- 来源
> - **聊天所消费的运行状态、同一 run 的审批恢复、取消与结果未知：** [AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../../ai-engineering/systems/ai-application-architecture.md)；本文是其客户端投影，不重写持久化运行协议。
> - **工具 ID 与结果的关联、模型请求不是执行许可：** [应用怎样设计并执行模型提出的工具请求](../../ai-engineering/agents/tool-design-and-function-calling.md)。`runId + seq` 是本应用事件合同；不是 MCP JSON-RPC 或模型 API 的通用帧格式。
> - **Marked 的同步 parse API、异步选项与不负责净化输出：** [Marked 18.1.3 README](https://github.com/markedjs/marked/blob/v18.1.3/README.md)、[高级用法与 options](https://github.com/markedjs/marked/blob/v18.1.3/docs/USING_ADVANCED.md) 和 [package metadata](https://github.com/markedjs/marked/blob/v18.1.3/package.json)；[DOMPurify 3.4.17 README](https://github.com/cure53/DOMPurify/tree/3.4.17)。在 Node.js 26.13.0 下实际运行跨片段恶意链接与代码围栏样例；核对日期 2026-11-09。Marked 18 要求 Node.js 20 或更新版本。
> - **动态 HTML 是独立安全边界，工具文字可由 DOM 文本接口显示：** [WHATWG DOM：`textContent`](https://dom.spec.whatwg.org/#dom-node-textcontent) 与 [DOMPurify：Security Goals & Threat Model](https://github.com/cure53/DOMPurify/wiki/Security-Goals-&-Threat-Model)，核对日期 2026-11-09。
## 56. JavaScript 事件总线在监听器中重入时怎样保持顺序？

案例背景：报表 42 的页面收到进度更新后，会让多个界面模块同步响应。event bus (事件总线) 把发布者和订阅者隔开，但监听器也可能在分发过程中增删订阅，甚至再次发布同名事件。实现必须规定当前这次分发看哪些监听器，以及一次性监听器何时注销。

下面的总线是应用层的 publish–subscribe (发布订阅) 模式，不是浏览器的 DOM 事件系统。它在 `emit()` 开始时复制监听器集合；分发途中发生的增删只影响之后开始的分发。`once()` 在调用用户函数前先标记并注销，因此递归 `emit()` 也不能再次执行同一个一次性监听器。

~~~javascript
class EventBus {
  events = new Map();

  on(type, listener) {
    let listeners = this.events.get(type);
    if (!listeners) this.events.set(type, listeners = new Set());
    listeners.add(listener);
    return () => this.off(type, listener);
  }

  once(type, listener) {
    let fired = false;
    const wrapper = (...args) => {
      if (fired) return;
      fired = true;
      this.off(type, wrapper); // 在用户代码运行前注销
      listener(...args);
    };
    return this.on(type, wrapper);
  }

  off(type, listener) {
    const listeners = this.events.get(type);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(type);
  }

  emit(type, ...args) {
    for (const listener of [...(this.events.get(type) ?? [])]) {
      listener(...args);
    }
  }
}
~~~

> [!example] 跟踪一次重入分发
> 初始顺序是 `summary`、一次性 `once`、旧的 `legacy`。处理版本 10 时，`summary` 移除 `legacy`、加入 `recovery`，随后同步发布版本 11。版本 11 的分发会取一份新快照；其中的 `once` 监听器注销自己后又发布版本 12。
>
> `v10`、`v11`、`v12` 是展示重入顺序的合成输入，不是报表 42 的服务端版本序列；SSE 示例中服务端版本 11 已是 `ready` 终态。真实报表消费者只把已接受的服务端状态交给界面，并继续按业务 `version` 拒绝旧更新。
>
> ~~~javascript
> const bus = new EventBus();
> const trace = [];
> let onceReentered = false;
> const legacy = e => trace.push(`legacy v${e.version}`);
> const recovery = e => trace.push(`recovery v${e.version}`);
>
> bus.on("report:updated", e => {
>   trace.push(`summary v${e.version}`);
>   if (e.version === 10) {
>     bus.off("report:updated", legacy);
>     bus.on("report:updated", recovery);
>     bus.emit("report:updated", { reportId: 42, version: 11 });
>   }
> });
> bus.once("report:updated", e => {
>   trace.push(`once v${e.version}`);
>   if (!onceReentered) {
>     onceReentered = true;
>     bus.emit("report:updated", { reportId: 42, version: 12 });
>   }
> });
> bus.on("report:updated", legacy);
> bus.emit("report:updated", { reportId: 42, version: 10 });
> console.log(trace);
> ~~~
>
> 输出顺序是 `summary v10 → summary v11 → once v11 → summary v12 → recovery v12 → recovery v11 → legacy v10`。版本 10 开始的旧快照仍含 `legacy`，所以即使它已注销，最后仍会执行一次；新加入的 `recovery` 不在版本 10 的快照中，但会出现在后续的快照中。`once` 先注销，避免后续新快照再次包含它；外层版本 10 的快照仍持有包装器，真正阻止它第二次调用用户函数的是 `fired` 检查。

这个行为来自本实现的快照策略，不是所有事件总线的通用保证。同步监听器抛错时，此实现会让错误向 `emit()` 调用者传播，并停止后续监听器；异步监听器返回的 Promise 不会被等待。生产实现应按需要另行定义错误隔离、异步处理和监听器移除语义。

若一个对象自然拥有订阅者，例如数据模型通知观察者，Observer (观察者模式) 让对象直接管理订阅关系。若多个模块只通过主题名沟通，事件总线用代理降低直接耦合，但会增加追踪事件来源的成本。两者都可把流式报表状态更新送到本地界面；跨标签页则需使用浏览上下文间的通信机制。

**延伸阅读：** [修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](#57.%20%E4%BF%AE%E6%94%B9%20DOM%20%E6%97%B6%EF%BC%8CHTMLCollection%20%E5%92%8C%20NodeList%20%E4%BC%9A%E6%80%8E%E6%A0%B7%E5%8F%98%E5%8C%96%EF%BC%9F) 跟踪状态通知后的节点增删；[同一报表在多个标签页中怎样交换变化？](#53.%20%E5%90%8C%E4%B8%80%E6%8A%A5%E8%A1%A8%E5%9C%A8%E5%A4%9A%E4%B8%AA%E6%A0%87%E7%AD%BE%E9%A1%B5%E4%B8%AD%E6%80%8E%E6%A0%B7%E4%BA%A4%E6%8D%A2%E5%8F%98%E5%8C%96%EF%BC%9F) 介绍跨标签页消息；[DOM 事件传播如何经过节点？](#4.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E6%80%8E%E6%A0%B7%E6%9F%A5%E8%AF%A2%E3%80%81%E6%9B%B4%E6%96%B0%20DOM%20%E5%B9%B6%E5%93%8D%E5%BA%94%E7%94%A8%E6%88%B7%E8%BE%93%E5%85%A5%EF%BC%9F) 介绍浏览器自身的事件阶段和取消规则。

> [!info]- 来源
> - `Set` 保存不同监听函数并按插入顺序迭代；`emit()` 的快照和 `once()` 的注销策略是本文这份应用实现明确采用的规则：[ECMAScript Language Specification，Keyed Collections](https://tc39.es/ecma262/multipage/keyed-collections.html#sec-set-objects)，2026-11-06 核对。
> - DOM 事件的分发规则由浏览器平台定义，与上述应用层事件总线不同：[WHATWG DOM Standard，Events](https://dom.spec.whatwg.org/#events)。
## 57. 修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？

案例背景：报表列表收到新结果后，界面要删除旧行并插入新行。Document Object Model (文档对象模型，DOM) 的查询会返回 HTMLCollection（元素集合）或 NodeList（节点列表）；集合成员可能随树变化，也可能固定。若代码在遍历时修改实时集合，索引会移动，导致行被跳过。

### 先查询到要操作的节点

`document.documentElement` 是 `<html>` 根元素，`document.body` 指向 `<body>`；脚本若在 HTML parser 解析到相应标签前运行，`body` 可能还是 `null`。`getElementById()` 与 `querySelector()` 都返回一个元素或 `null`，后者的参数是 CSS 选择器。拿到容器后，可继续在容器内查询，避免把页面上另一个同类按钮误当成报表控件：

~~~javascript
const reports = document.querySelector("#reports");
const controls = document.querySelector("#sort-controls");
const oldestButton = controls?.querySelector('button[data-sort="oldest"]') ?? null;
const directRows = reports?.querySelectorAll(":scope > li[data-id]") ?? [];
~~~

`querySelectorAll()` 在没有匹配项时仍返回长度为 `0` 的 `NodeList`；`querySelector()` 则返回 `null`。选择器字符串若不是有效 CSS 语法，查询会抛 `SyntaxError`，不是返回空结果。完整页面的 `body`、根元素和控件在 DOM 构建后的关系见[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)。

| 来源 | 类型 | 包含什么 | 查询后发生 DOM 变更时 |
|---|---|---|---|
| `element.children`、`getElementsByClassName()`、`getElementsByTagName()` | `HTMLCollection` | 元素节点 | 实时反映当前树 |
| `element.querySelectorAll()` | `NodeList` | 匹配元素 | 静态成员列表 |
| `element.childNodes` | `NodeList` | 元素、文本、注释等子节点 | 实时反映当前树 |

因此，`NodeList` 不代表“静态”。需要根据具体查询 API 的契约判断；空白文本也会成为 `childNodes` 中的文本节点；通用节点应使用 `nodeName`，因为 `tagName` 只属于元素。`HTMLCollection` 和 `NodeList` 都不是普通数组，直接调用 `map()` 不可行，可用 `Array.from()` 创建数组快照。

> [!example] 正向删除实时集合会跳过一行
> 开始时列表按顺序是 `[r1, r2, r3]`。这些只是合成行 ID，与报表 ID、业务版本或事件游标无关。`children` 是实时集合：删掉索引 0 的 `r1` 后，`r2` 移到索引 0、`r3` 移到索引 1。循环把索引递增到 1，于是跳过 `r2`，下一轮删的是 `r3`。
>
> ~~~html
> <ul id="reports">
>   <li class="report" id="r1">报告 1</li>
>   <li class="report" id="r2">报告 2</li>
>   <li class="report" id="r3">报告 3</li>
> </ul>
> ~~~
>
> ~~~javascript
> const list = document.querySelector("#reports");
> const liveRows = list.children;
> const queriedRows = list.querySelectorAll(":scope > .report");
>
> for (let i = 0; i < liveRows.length; i += 1) {
>   liveRows[i].remove();
> }
> // 起初 r1、r2、r3；循环结束后 r2 仍在列表中。
> // queriedRows 仍有 3 个成员，但 queriedRows[0].isConnected 为 false。
> ~~~
>
> 若在这份原始列表上先复制成员，循环处理的就是固定顺序 `[r1, r2, r3]`，删除树节点不会改变待遍历数组。`querySelectorAll()` 的静态列表也仍有三个成员，但其中已移除节点的 `isConnected` 会变成 `false`：静态只固定列表成员，不冻结节点对象。以下是与上面错误循环二选一的写法，应从同一份初始列表开始。
>
> ~~~javascript
> for (const row of Array.from(liveRows)) row.remove();
> ~~~

实时集合适合反映 DOM 的当前成员，但不适合一边按递增索引遍历、一边改变成员；也可从后往前删。静态快照则适合一次查询后按成员执行任务。查询何时更新、节点本身是否仍连接到文档，是两个不同问题。实时描述的是可观察的成员结果，不承诺浏览器内部怎样、多久计算一次。

**延伸阅读：** [JavaScript 事件总线在监听器中重入时怎样保持顺序？](#56.%20JavaScript%20%E4%BA%8B%E4%BB%B6%E6%80%BB%E7%BA%BF%E5%9C%A8%E7%9B%91%E5%90%AC%E5%99%A8%E4%B8%AD%E9%87%8D%E5%85%A5%E6%97%B6%E6%80%8E%E6%A0%B7%E4%BF%9D%E6%8C%81%E9%A1%BA%E5%BA%8F%EF%BC%9F) 说明状态更新如何触发本地模块；[用户离开报表页时，分析事件怎样尽力发送？](#58.%20%E7%94%A8%E6%88%B7%E7%A6%BB%E5%BC%80%E6%8A%A5%E8%A1%A8%E9%A1%B5%E6%97%B6%EF%BC%8C%E5%88%86%E6%9E%90%E4%BA%8B%E4%BB%B6%E6%80%8E%E6%A0%B7%E5%B0%BD%E5%8A%9B%E5%8F%91%E9%80%81%EF%BC%9F) 说明导航期间的遥测边界；[浏览器如何从输入到绘制界面？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F) 讨论 DOM 与后续渲染。

> [!info]- 来源
> - `NodeList`、`HTMLCollection` 的集合定义与 live/static 成员规则：[WHATWG DOM Standard，Old-style collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection)，2026-11-07 核对。
> - `querySelectorAll()` 返回静态 `NodeList`，由其 API 规范定义：[WHATWG DOM Standard，ParentNode](https://dom.spec.whatwg.org/#dom-parentnode-queryselectorall)，2026-11-07 核对。
> - `querySelector()` 首个匹配项或 `null`、`querySelectorAll()` 静态匹配结果及作用域查询：[WHATWG DOM Standard，ParentNode](https://dom.spec.whatwg.org/#interface-parentnode)，持续更新规范，selector matching methods。核对日期：2026-11-07。
## 58. 用户离开报表页时，分析事件怎样尽力发送？

案例背景：用户打开报表、改变一次筛选，然后立刻导航到别处。analytics event (分析事件) 不应拖慢筛选或导航；页面可先在内存中收集少量事件，再小批量发送，并在页面变为隐藏时尝试提交一批。这个生命周期信号只提供最后一次机会，不能保证服务器已收到。

### 先限制采集内容和积压量

先列出产品真正需要的事件名与字段。只收集允许的 `report_opened`、`filter_applied` 等事件和受控的页面代号；不要把搜索框原文、完整 URL、用户令牌或可识别身份的值塞进载荷。用户关闭可选采集时，停止入队并清空仍在应用内存中的未发送数据；已经交给 Beacon 或 Fetch 的批次可能还在途，不能由这个开关撤回。

内存队列需要上限和明示的溢出策略。下面采用最多 200 条，满时丢弃最旧条目；每 50 条或定时尝试发送一批。生产实现还应限制序列化后的字节数，因为事件条数不能代表请求体大小。`visibilitychange` 到 `hidden` 时只尝试一批，队列若仍有剩余，页面退出后可能被丢弃。发送小批次时可以先试 Beacon API，它不会等待服务器响应。

> [!example] 报表打开和筛选变化
> 页面先把 `report_opened` 和 `filter_applied` 放进内存队列。这两条尚未达到 50 条的成批门槛；若用户在 10 秒定时器触发前切换页面，文档变为 `hidden` 时处理器会将两条一起取出并尝试发送。

~~~javascript
const MAX_PENDING = 200;
const BATCH_SIZE = 50;
const allowedNames = new Set(["report_opened", "filter_applied"]);
const allowedScreens = new Set(["report_list", "report_detail"]);
const queue = [];
let collectionEnabled = false;
let flushScheduled = false;

function setCollectionEnabled(enabled) {
  collectionEnabled = enabled;
  if (!enabled) queue.length = 0;
}

function sendBatch(batch) {
  const body = new Blob([JSON.stringify(batch)], { type: "application/json" });
  // 本例假设同源端点。返回 true 仅表示浏览器已接受排队。
  if (navigator.sendBeacon?.("/analytics", body)) return;
  // Beacon 不可用或拒绝排队时尝试 Fetch；两者共享 keepalive 配额，不能保证后者绕过拒绝。
  void fetch("/analytics", { method: "POST", body, keepalive: true }).catch(() => {});
}

function trackEvent(name, screen) {
  if (!collectionEnabled || !allowedNames.has(name) || !allowedScreens.has(screen)) return;
  if (queue.length === MAX_PENDING) queue.shift();
  queue.push({ name, screen, ts: Date.now() });
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
  if (!queue.length) return;
  sendBatch(queue.splice(0, BATCH_SIZE));
}

setInterval(flushEvents, 10_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushEvents();
});

setCollectionEnabled(true);
trackEvent("report_opened", "report_detail");
trackEvent("filter_applied", "report_detail");
~~~

### “已排队”不等于“已记录”

Beacon API 的 `navigator.sendBeacon()` 返回 `true` 只表示用户代理接受了传输排队；它没有响应回调，也不报告服务器是否处理。浏览器会在文档变为 `hidden` 时安排发送，但设备进程随后仍可能被系统终止。若需要自定义请求头或更细控制，可尝试 Fetch API 的 `keepalive` 请求；Beacon 和 Fetch keepalive 共用限额，一个 Fetch 组中尚未完成请求的正文总量受 64 KiB 限制，队列太大时提交可能被拒绝。若 Beacon 因这个限额被拒绝，回退到 Fetch 不能绕过限额。两个接口都不能替代可靠业务队列、服务器确认或幂等去重。

本例 `flushEvents()` 在尝试发送前从内存队列取出一批。传输失败后该批不会自动重试；这正是“尽力发送”的损失边界。若统计数据不可丢，应把它升级为持久队列并设计服务端确认与重放，而不是阻塞离页等待。

**延伸阅读：** [报表页面里的状态应该放在哪里？](#52.%20%E6%8A%A5%E8%A1%A8%E9%A1%B5%E9%9D%A2%E9%87%8C%E7%9A%84%E7%8A%B6%E6%80%81%E5%BA%94%E8%AF%A5%E6%94%BE%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F) 说明偏好与业务状态的归属；[流式报表断线重连后，界面怎样保留正确状态？](#54.%20%E6%B5%81%E5%BC%8F%E6%8A%A5%E8%A1%A8%E6%96%AD%E7%BA%BF%E9%87%8D%E8%BF%9E%E5%90%8E%EF%BC%8C%E7%95%8C%E9%9D%A2%E6%80%8E%E6%A0%B7%E4%BF%9D%E7%95%99%E6%AD%A3%E7%A1%AE%E7%8A%B6%E6%80%81%EF%BC%9F) 说明哪些消息影响报表正确性、不能混同于可丢弃的分析事件；[WebView 怎样安全地开放原生能力并更新页面包？](#59.%20WebView%20%E6%80%8E%E6%A0%B7%E5%AE%89%E5%85%A8%E5%9C%B0%E5%BC%80%E6%94%BE%E5%8E%9F%E7%94%9F%E8%83%BD%E5%8A%9B%E5%B9%B6%E6%9B%B4%E6%96%B0%E9%A1%B5%E9%9D%A2%E5%8C%85%EF%BC%9F) 讨论混合应用中的宿主权限。

> [!info]- 来源
> - Beacon 是非阻塞的尽力传输；返回值仅表示排队成功，且无响应回调：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3，2026-11-06 核对。
> - Beacon 在页面 `visibilityState` 变为 `hidden` 时安排发送；规范也提示后台页面在移动设备上仍可能随进程终止而丢失：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3、§4，2026-11-06 核对。
> - Fetch `keepalive` 与 64 KiB 的在途请求总量限制：[WHATWG Fetch Standard，HTTP-network-or-cache fetch](https://fetch.spec.whatwg.org/)，2026-11-06 核对。
> - 页面可见性状态：[WHATWG HTML Standard，Page visibility](https://html.spec.whatwg.org/multipage/interaction.html#page-visibility)，2026-11-06 核对。
## 59. WebView 怎样安全地开放原生能力并更新页面包？

案例背景：报表应用把页面放进原生应用的 WebView，页面需要请求宿主打开报表详情；页面脚本同时会随应用安装或网络更新。JavaScript bridge (原生桥接接口) 把页面输入送到宿主应用的权限边界，因此必须把“哪个页面能发消息”“消息能请求什么”“更新后的代码是否兼容”作为一条信任链来设计。

WebView 没有一个跨平台统一的原生桥接标准。Android 与 Apple WebKit 的 API、回调线程、来源信息和回复方式都不同；平台 API 只能提供边界线索，最终由宿主原生代码检查操作和授权。

### 一条消息怎样变成原生操作？

| 平台 | 消息入口 | 平台能提供的来源信息 | 重要边界 |
|---|---|---|---|
| Android WebView | 优先考虑 AndroidX `WebViewCompat.addWebMessageListener()` | 回调含 `sourceOrigin`、`isMainFrame` 和回复代理 | 注册时需设 `allowedOriginRules` 并在加载页面前安装；规则匹配 scheme (协议)、host (主机)、port (端口)，不匹配路径，而且匹配来源的子框架页面也可收到注入对象 |
| Android 旧版接口 | `addJavascriptInterface()` | 旧桥接对象没有可信的逐消息来源校验 | 标注 `@JavascriptInterface` 的方法可暴露给各内嵌框架页面；只适合严格控制且完全可信的内容，不能让不可信内容复用同一个 WebView |
| Apple WebKit | `WKScriptMessageHandler` 或带回复的 `WKScriptMessageHandlerWithReply` | `WKScriptMessage.frameInfo` 提供 `securityOrigin` 与 `isMainFrame` | 由宿主安装具名消息处理器；消息处理与回复是 WebKit API，不等同于 Android 的同步对象调用 |

AndroidX `WebViewCompat.addWebMessageListener()` 需要用 `WebViewFeature.isFeatureSupported()` 检查当前 WebView 是否支持。现代接口仍需检查来源和主框架页面：可信主机下的广告内嵌框架，或遭 cross-site scripting (跨站脚本攻击，XSS) 控制的页面脚本，也可能发消息。`allowedOriginRules` 不区分路径，例如允许 `https://reports.example` 也会匹配这个来源上的其他路径。只加载 HTTPS 并允许受控的页面，收到消息后再校验 origin (来源)、frame (框架页面)、操作名、schema (参数结构)、数据范围和调用者权限。回调通常在主线程执行，耗时工作应移交后台线程。

建议把应用自己的桥接契约做成窄的异步 remote procedure call (远程过程调用，RPC) 形状，例如 `{id, operation, payload}`，回复带同一 `id` 以及成功结果或错误码。定义允许的操作和参数、版本协商、取消、超时和权限拒绝；不要开放任意方法调用、JavaScript 求值或文件路径访问。确认来源只是信任的一部分，不能代替业务授权。

> [!example] 先检查消息，再处理一个允许的操作
> 以下是宿主侧伪代码，说明检查顺序，不是 Android 或 Apple 的可直接编译 API。`platformMetadata` 由原生平台回调提供，`untrustedBody` 才是网页发送的数据；页面不能靠在 body 中填来源或主 frame 来证明身份。示例只开放 `openReport`：宿主确认平台提供的受信来源和主 frame，再验证 `reportId`、检查当前用户权限，授权后才调用原生操作并回复。
>
> ~~~text
> platformMetadata = { sourceOrigin: platformOrigin, isMainFrame: platformFrameFlag }
> untrustedBody = { id: "req-17", operation: "openReport", payload: { reportId: 42 } }
>
> handle(platformMetadata, untrustedBody, reply):
>   reject unless trustedOrigin(platformMetadata.sourceOrigin)
>   reject unless platformMetadata.isMainFrame
>   message = parseAndValidate(untrustedBody)
>   reject unless message.operation == "openReport"
>   reject unless schemaValid(message.payload) and validReportId(message.payload.reportId)
>   reject unless authorize(currentNativeUser, "openReport", message.payload.reportId)
>   result = openReport(message.payload.reportId)
>   reply({ id: message.id, ok: true, payload: result })
> ~~~

Android 的来源和主 frame 信息来自 `WebMessageListener` 平台回调；Apple 宿主应从 `WKScriptMessage.frameInfo.securityOrigin` 与 `isMainFrame` 读取对应元数据。两者都不应从网页 body 取值。如果页面只需要浏览器已有能力，例如定位并展示地图，优先评估 Web API（如 `navigator.geolocation`）；浏览器可以按标准权限流程提示用户，减少原生接口暴露面。较旧的隐藏 iframe 自定义 URL scheme（例如 `myapp://api/location`）曾用于触发宿主拦截，但参数长度、回复通道、回调 ID 和错误处理都要自行实现；把它当成遗留兼容方案，不作为新桥接推荐。

### 下载更新包怎样进入桥接信任区？

下载的 HTML、JavaScript、CSS 与图片 bundle (资源包) 不是无权限的数据：只要在可调用桥接接口的 WebView 中执行，就可能请求宿主能力。因此资源包校验是桥接安全的一部分，但更新下载和消息授权仍是两套不同机制，不能用其中一套替代另一套。

一个最小可审查的更新流程可以是：

1. 应用启动时立即载入最后一个已验证版本；按新鲜度策略或用户请求在后台检查更新，不挡住启动。
2. 从允许的更新源获取小型更新 manifest (清单)，包含不可变包版本、支持的原生桥接 API 版本范围、资源清单、大小和完整性摘要。
3. 只从允许的包源下载；拒绝未授权的重定向，把包写入临时目录并完整校验后才候选安装。HTTPS 来源认证传输对端；若威胁模型包含 CDN 或更新源被攻陷，使用由原生应用内固定信任锚验证的发布者签名，不能把同一未认证源同时给的 hash (散列值) 当成独立身份验证。
4. 确认包满足当前桥接 bridge API (桥接接口) 的兼容条件，再原子切换到已验证目录；不接受半下载或半安装状态。
5. 保留上一版可用包。启动探测失败或启动崩溃达到策略阈值时回滚，并把下一次检查退避。

宿主本地资源的装载方式也会影响来源隔离。Android 官方建议用 `WebViewAssetLoader` 通过受控的 HTTP(S) 风格 origin (来源) 提供本地资源，并避免依赖 `file://`；它解决的是资源装载与同源行为，不会替你验证网络下载包的签名，也不等同于原生桥接接口的授权策略。Apple 平台需采用对应 WebKit 资源方案，不能照搬 Android 配置。

> [!example] 桥接接口版本不兼容时拒绝切换
> 当前应用只实现桥接接口 `2.0`，远端 manifest (清单) 声明新包最低要求 `2.1`。即使文件下载完整、hash (散列值) 匹配，也应保留旧包并延后切换；完整性证明“文件与清单相同”，不证明“页面和宿主能够协作”。

下载包中的密钥、会话数据和最终权限仍应留在原生安全存储或服务端。新页面获准调用原生桥接接口也不代表其所有代码都可信；为包更新和桥接操作分别记录版本、验证结果与授权决策，便于回滚和调查。

**延伸阅读：** [报表页面里的状态应该放在哪里？](#52.%20%E6%8A%A5%E8%A1%A8%E9%A1%B5%E9%9D%A2%E9%87%8C%E7%9A%84%E7%8A%B6%E6%80%81%E5%BA%94%E8%AF%A5%E6%94%BE%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F) 说明本地数据不应冒充服务端事实；[Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) 讨论来源、XSS 和授权边界。

> [!info]- 来源
> - AndroidX bridge API、来源规则、frame 信息、功能检测与回调线程：[Android Developers，Access native APIs with JavaScript bridge](https://developer.android.com/develop/ui/views/layout/webapps/native-api-access-jsbridge)，2026-11-06 核对。
> - 旧式 `addJavascriptInterface` 的 frame 暴露与桥接风险：[Android Developers，Insecure WebView native bridges](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges)，2026-11-06 核对。
> - Android 本地资源通过 `WebViewAssetLoader`、避免 `file://` 的建议：[Android Developers，Load in-app content](https://developer.android.com/develop/ui/views/layout/webapps/load-local-content)，2026-11-06 核对。
> - Apple WebKit 消息处理器与回复：[Apple Developer Documentation，WKScriptMessageHandler](https://developer.apple.com/documentation/webkit/wkscriptmessagehandler)；[WKScriptMessageHandlerWithReply](https://developer.apple.com/documentation/webkit/wkscriptmessagehandlerwithreply/usercontentcontroller%28_%3Adidreceive%3Areplyhandler%3A%29?language=objc)，2026-11-06 核对。
> - Apple 消息 frame 的 `isMainFrame`、`securityOrigin`：[Apple Developer Documentation，WKFrameInfo](https://developer.apple.com/documentation/webkit/wkframeinfo)；[WKScriptMessage.frameInfo](https://developer.apple.com/documentation/webkit/wkscriptmessage/frameinfo)，2026-11-06 核对。
> - Bundle 签名、兼容矩阵、原子切换与回滚是应用更新策略，不是 WebView 平台规范；本文把它们作为威胁模型驱动的设计建议。
## 60. Redux 如何组织共享界面状态与异步工作？

**案例背景。** 报表页打开 `/reports?sort=recent#summary`，服务端给出 May、April。用户选 **Oldest first** 后，路由把 `sort=oldest` 写成一条新历史记录；路由提交新地址后，组件用新的 `sort` 组成查询 key，TanStack Query 复用仍新鲜的缓存，或在缺少/过期时发请求，结果可用后显示 April、May。浏览器 Back 回到 recent 后，同样按 recent 的查询 key 复用缓存或重取结果。`#summary` 只用于浏览器定位，不会随 HTTP 请求发送。排序由 URL 与路由拥有，报表行由 TanStack Query 缓存服务端结果。Redux（共享状态管理库）只接手另一类问题：报表表格和远处的批量操作栏都需要读取、修改同一份已选报表 ID。选择变化会清除与旧集合对应的预览；用户点“预览导出范围”按钮时，才按当前选中 ID 发起请求。

~~~mermaid
flowchart TD
    A[URL sort=recent] --> B[组件按sort查询报表行]
    B --> C[查询缓存持有 May、April]
    C --> D
    D[选择行] --> E[dispatch action]
    E --> F[reducer更新共享selectedIds]
    F --> G[清空旧预览并使旧requestId失效]
    F --> H[表格与批量操作栏读取同一选择]
    H --> I[用户点击预览导出范围]
    I --> J[dispatch thunk并保存requestId]
    J --> K{返回的requestId仍是当前值？}
    K -->|是| P[保存当前预览或错误]
    K -->|否| Q[忽略过期结果]
    A --> M[选择oldest并新增历史项]
    M --> N[按oldest查缓存或取数，数据可用后显示April、May]
    N --> O[Back恢复recent，复用缓存或重取对应行]
~~~

### 先确定什么状态需要共享

Redux 的价值在于让多个相隔较远的组件围绕同一份客户端状态和明确的更新动作协作。它不会自动取代 URL、组件本地 state 或服务端查询缓存。沿报表案例看，状态由谁拥有，决定了刷新、返回和请求完成时谁负责恢复：

| 状态 | 所有者 | 本例中的结果 |
| --- | --- | --- |
| `sort=recent` 或 `sort=oldest` | URL 与路由 | 刷新、分享地址和浏览器 Back 都能恢复筛选条件 |
| May、April 等报表行 | 服务端；客户端查询缓存保存副本 | 查询身份包含 `sort`，不同排序对应不同结果；见[React 如何维护服务端数据与乐观更新？](#%E6%8E%92%E5%BA%8F%E5%80%BC%E6%9E%84%E6%88%90%E6%9F%A5%E8%AF%A2%E8%BA%AB%E4%BB%BD) |
| 已选报表 ID | Redux store | 表格、计数提示和批量操作栏可以读取同一份数组 |
| 当前弹层是否打开 | 使用它的组件 | 只影响局部展示时，不必提升到全局 store |
| 导出预览请求状态 | 本例的 Redux 工作流 | 选择变化清除旧预览；点击按钮后，异步结果只更新它对应的当前请求 |

如果只有一个组件使用某值，就让它留在组件中；两个相邻组件共享时，先比较提升到最近共同父组件是否更简单，见[如何在 React 中组合组件与复用行为？](#%E6%8A%8A%E7%8A%B6%E6%80%81%E6%94%BE%E5%9C%A8%E5%85%B1%E5%90%8C%E4%BD%BF%E7%94%A8%E8%80%85%E4%B9%8B%E4%B8%8A%E7%9A%84%E6%9C%80%E8%BF%91%E4%B8%80%E5%B1%82)。Redux 不会让数据变成“全局自动同步”；它给出明确的读写入口。React Router 路由加载与历史项的提交时机见[React 路由如何把地址映射到界面并加载数据？](#%E6%95%B0%E6%8D%AE%E6%A8%A1%E5%BC%8F%E5%85%88%E5%8C%B9%E9%85%8D%E8%B7%AF%E7%94%B1%EF%BC%8C%E5%86%8D%E5%8A%A0%E8%BD%BD%E5%8C%B9%E9%85%8D%E9%A1%B5%E9%9D%A2%E7%9A%84%E6%95%B0%E6%8D%AE)。

### action 怎样经过 store 更新共享选择

在 Redux Toolkit（Redux 官方工具集）中，`configureStore` 建立 store（状态容器）并合并 reducer（状态更新函数）；传入 reducer 对象时，它会按功能组合这些 reducer，并默认启用与 Redux DevTools 浏览器扩展的集成，安装扩展后可检查 action 和状态。DevTools 会看到已派发的数据，因此不要把凭证放进 Redux state 或 action。`createSlice` 将一类状态、reducer 和 action creator（动作创建函数）放在一起。reducer 收到 action（动作）后同步计算下一状态，不执行网络请求或其他副作用。

下面按报表 ID 切换选择。Redux Toolkit 允许 reducer 写成对 draft 的局部修改，Immer 会据此产出新的不可变状态；这不是直接修改 store 中已经发布的对象。把选择保存为 ID 而不是数组下标，排序改变后仍会选择同一份报表。

一个 action 只说明“发生了什么”，表格组件不需要自己去找批量操作栏并直接改它的 props。调用 `dispatch(toggleReport("april"))` 后，reducer 将 `selectedIds` 从 `[]` 变成 `["april"]`；所有订阅这个值的组件都能看到新状态。它们仍要使用稳定的报表 ID，不应以当前列表位置作身份。

### 异步结果怎样避免覆盖较新的选择

导出范围预览是用户点击按钮后开始的一次性工作。假设用户先选中 May，点击“预览导出范围”后为 `["may"]` 派发请求；再选中 April，旧预览会清空，用户再次点击按钮才会为 `["may", "april"]` 派发第二个请求。如果第一份响应较晚到达，它描述的是旧集合，不能覆盖第二份预览。`createAsyncThunk`（异步 thunk 创建器）会为一次调用派发 `pending`、`fulfilled` 或 `rejected` 生命周期 action，并把本次唯一 `requestId` 放在 `action.meta` 中。reducer 只接受仍匹配当前 ID 的结果。

这个示例约定接口 `POST /api/reports/export-preview` 接收 `reportIds`，只返回非负安全整数 `reportCount` 与 `estimatedBytes`，不创建导出文件。服务端仍须按当前身份和租户逐个授权这些 ID；客户端 Redux 中的选择不能代替[服务端资源权限检查](../../engineering-foundations/security/web-security-and-authentication.md)。把响应先视为 `unknown` 并检查结构，因为 TypeScript 泛型或断言本身不会验证服务器实际返回值；边界校验细节见[TypeScript 如何处理不可信 JSON？](#45.%20%E6%94%B6%E5%88%B0%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%20%E5%90%8E%EF%BC%8CTypeScript%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E5%8F%AF%E4%BF%A1%E7%9A%84%E7%B1%BB%E5%9E%8B%EF%BC%9F)。

~~~typescript
// features/report-selection/reportSelectionSlice.ts
import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";

type Preview = { reportCount: number; estimatedBytes: number };
type PreviewState = {
  status: "idle" | "pending" | "ready" | "error";
  currentRequestId: string | null;
  result: Preview | null;
  error: string | null;
};
type ReportSelectionState = {
  selectedIds: string[];
  preview: PreviewState;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonNegativeSafeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function parsePreview(value: unknown): Preview {
  if (
    !isRecord(value) ||
    !isNonNegativeSafeInteger(value.reportCount) ||
    !isNonNegativeSafeInteger(value.estimatedBytes)
  ) {
    throw new Error("报表服务返回了无效的导出预览");
  }
  return { reportCount: value.reportCount, estimatedBytes: value.estimatedBytes };
}

export const loadExportPreview = createAsyncThunk<Preview, string[]>(
  "reportSelection/loadExportPreview",
  async (reportIds, { signal }) => {
    const response = await fetch("/api/reports/export-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reportIds }),
      signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload: unknown = await response.json();
    return parsePreview(payload);
  }
);

const emptyPreview = (): PreviewState => ({
  status: "idle",
  currentRequestId: null,
  result: null,
  error: null,
});

const initialState: ReportSelectionState = {
  selectedIds: [],
  preview: emptyPreview(),
};

export const reportSelectionSlice = createSlice({
  name: "reportSelection",
  initialState,
  reducers: {
    toggleReport(state, action: PayloadAction<string>) {
      const index = state.selectedIds.indexOf(action.payload);
      if (index === -1) state.selectedIds.push(action.payload);
      else state.selectedIds.splice(index, 1);
      state.preview = emptyPreview();
    },
    clearSelection(state) {
      state.selectedIds = [];
      state.preview = emptyPreview();
    },
  },
  extraReducers: builder => {
    builder
      .addCase(loadExportPreview.pending, (state, action) => {
        state.preview = {
          status: "pending",
          currentRequestId: action.meta.requestId,
          result: null,
          error: null,
        };
      })
      .addCase(loadExportPreview.fulfilled, (state, action) => {
        if (state.preview.currentRequestId !== action.meta.requestId) return;
        state.preview = {
          status: "ready",
          currentRequestId: null,
          result: action.payload,
          error: null,
        };
      })
      .addCase(loadExportPreview.rejected, (state, action) => {
        if (state.preview.currentRequestId !== action.meta.requestId) return;
        state.preview = {
          status: action.meta.aborted ? "idle" : "error",
          currentRequestId: null,
          result: null,
          error: action.meta.aborted ? null : action.error.message ?? "请求失败",
        };
      });
  },
});

export const { toggleReport, clearSelection } = reportSelectionSlice.actions;
export const reportSelectionReducer = reportSelectionSlice.reducer;
~~~

异步 action 创建器负责启动请求；`extraReducers` 在 slice（状态切片）里响应它的生命周期。每次选择变化都会把预览状态和当前 ID 清空；新请求开始时记录自己的 ID。因而，旧请求即使没有取消且稍后成功或失败，也无法提交到当前界面。

> [!example] 两份请求按开始顺序而不是返回顺序判定
> 初始行是 May、April。用户只选 May 后点击“预览导出范围”，第一次预览请求带 ID `req-1`；接着用户再选 April，旧预览清空，再次点击同一按钮后才开始 `req-2`。`req-2` 先返回 `reportCount: 2`，状态变为 `ready` 且 `currentRequestId` 归为 `null`。随后 `req-1` 即使返回 `reportCount: 1`，也因 ID 与当前的 `null` 不匹配而被忽略。浏览器 Back 只把 URL 排序恢复为 recent；同一批稳定 ID 仍表示已选 May、April。

`requestId` 负责识别一次调用，不会自动停止网络请求。payload creator 收到的 `signal` 可以传给 `fetch`；调用 `dispatch(loadExportPreview(ids)).abort()` 也会请求取消该 thunk。取消客户端读取不保证已经接到请求的服务端停止工作。示例的状态只表示“当前集合的预览”，若产品要同时保留多份并发预览或多个导出作业，应按 `requestId` 或服务端作业 ID 分开存储，而不能用一个 latest-request 槽覆盖所有结果。

### React 组件怎样读取并派发类型安全的状态

`configureStore` 会组合 reducer，并默认包含 thunk middleware（中间件）；在 TypeScript 项目中，从创建好的 store 推导 `RootState` 和 `AppDispatch`，再用 React-Redux（Redux 的 React 绑定）9.1 及以上的 `.withTypes()` 建立应用专用 Hook（钩子）。Hook 文件只导入 store 的类型，避免组件与 store 之间形成运行时循环导入。

~~~typescript
// app/store.ts
import { configureStore } from "@reduxjs/toolkit";
import { reportSelectionReducer } from "../features/report-selection/reportSelectionSlice";

export const store = configureStore({
  reducer: { reportSelection: reportSelectionReducer },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
~~~

~~~typescript
// app/hooks.ts
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "./store";

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
~~~

根节点用 `<Provider store={store}>` 包住需要访问 Redux 的 React 子树。行组件按报表 ID 读取选中状态并派发 action；批量工具栏读取同一份数组，再以它的快照发起预览。

~~~tsx
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { loadExportPreview, toggleReport } from "./reportSelectionSlice";

type Report = { id: string; period: string; title: string };

function ReportRow({ report }: { report: Report }) {
  const selected = useAppSelector(state =>
    state.reportSelection.selectedIds.includes(report.id)
  );
  const dispatch = useAppDispatch();

  return (
    <li>
      <label>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => dispatch(toggleReport(report.id))}
        />
        {report.period} — {report.title}
      </label>
    </li>
  );
}

function ExportPreviewToolbar() {
  const selectedIds = useAppSelector(state => state.reportSelection.selectedIds);
  const preview = useAppSelector(state => state.reportSelection.preview);
  const dispatch = useAppDispatch();

  return (
    <section aria-label="批量操作">
      <button
        type="button"
        disabled={selectedIds.length === 0 || preview.status === "pending"}
        onClick={() => void dispatch(loadExportPreview([...selectedIds]))}
      >
        预览导出范围
      </button>
      {preview.status === "pending" && <p role="status">正在计算导出范围…</p>}
      {preview.status === "ready" && preview.result && (
        <p role="status">
          {preview.result.reportCount} 份报表，约 {preview.result.estimatedBytes} 字节
        </p>
      )}
      {preview.status === "error" && <p role="alert">{preview.error}</p>}
    </section>
  );
}
~~~

`useSelector` 默认用严格引用相等比较前后选择结果；像上面一样读取布尔值、字符串或 store 中现有数组可以直接观察状态变化。若每次 selector 都新建对象，默认比较会认为结果不同而触发重新渲染；需要一起返回多个字段时，可分别调用 Hook、使用有记忆的 selector，或显式选择比较函数。渲染成本是否值得优化应通过[React 工作测量](#14.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)判断。

### middleware 与 thunk 分别插入哪一步

普通 action 到达 Redux store 后，同步调用 reducer 并保存新状态。middleware（中间件）包裹 `dispatch`，可以在 action 到达 reducer 前后观察或扩展这一流程；thunk middleware 允许 `dispatch` 接受函数，让这个函数访问 `dispatch`、`getState` 并等待异步任务，再派发普通结果 action。Redux Toolkit 默认已配置 thunk，新增中间件时用 `getDefaultMiddleware()` 扩展默认列表，不要为了添加一项日志就替换默认值。

`createAsyncThunk` 已为一次请求组织了 pending、fulfilled、rejected 三种 action；一般无需再手写一个“把所有函数 action 变成异步”的 middleware。只有当工作需要响应后续 action 或状态变化、而不是由某次显式派发触发时，才进一步考虑 listener middleware。缓存服务端数据可用 Redux Toolkit Query（RTK Query）；本报表案例已经以 TanStack Query 持有查询缓存，不再把同一批行同时放入 Redux。

> [!info]- 来源
> - 状态切片、自动生成的 action creator、Immer draft、`configureStore` 默认 middleware 与 DevTools：[Redux Toolkit — `createSlice`](https://redux-toolkit.js.org/api/createSlice)、[`configureStore`](https://redux-toolkit.js.org/api/configureStore)、[Why Redux Toolkit Is Redux Today](https://redux-toolkit.js.org/introduction/why-rtk-is-redux-today)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 异步 thunk 生命周期 action、`meta.requestId`、`signal`、`abort()` 与错误结果：[Redux Toolkit — `createAsyncThunk`](https://redux-toolkit.js.org/api/createAsyncThunk)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 缓存服务端数据用 Redux Toolkit Query、一次命令式异步工作用 thunk、响应后续状态变化用 listener middleware：[Redux Toolkit — Side Effects Approaches](https://redux-toolkit.js.org/usage/side-effects-approaches)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 从 store 推导 `RootState` 和 `AppDispatch`，以及用 `.withTypes()` 创建 typed hooks：[Redux Toolkit — TypeScript Quick Start](https://redux-toolkit.js.org/tutorials/typescript)、[React-Redux — TypeScript Usage](https://react-redux.js.org/using-react-redux/usage-with-typescript)，React-Redux 9.3.1，核对日期：2026-11-06。
> - selector 默认使用严格 `===` 比较及多值选择建议：[React-Redux — Hooks API](https://react-redux.js.org/api/hooks)，React-Redux 9.3.1，核对日期：2026-11-06。
> - 路由 PUSH 加入新筛选历史、POP 依 URL 恢复筛选和目标数据：[React Router 路由导航](#%E6%95%B0%E6%8D%AE%E6%A8%A1%E5%BC%8F%E5%85%88%E5%8C%B9%E9%85%8D%E8%B7%AF%E7%94%B1%EF%BC%8C%E5%86%8D%E5%8A%A0%E8%BD%BD%E5%8C%B9%E9%85%8D%E9%A1%B5%E9%9D%A2%E7%9A%84%E6%95%B0%E6%8D%AE)，React Router 8.5.1，核对日期：2026-11-06。
> - `sort` 是 URL 状态、报表行为查询数据，不应由 Redux 再保存第二份：[React Server State 章节](#%E6%8E%92%E5%BA%8F%E5%80%BC%E6%9E%84%E6%88%90%E6%9F%A5%E8%AF%A2%E8%BA%AB%E4%BB%BD)，TanStack Query v5.90.3，核对日期：2026-11-06。
## 61. 如何为产品选择前端框架？

**案例背景。** 以报表页面为例：浏览器地址是 `/reports?sort=recent#summary`，服务端实际收到 `/reports?sort=recent` 并据此返回 May、April 两行；`#summary` 只供浏览器定位。用户点 **Oldest first** 后，`pushState` 新增 `sort=oldest` 历史项，可见顺序成为 April、May；按浏览器 Back 会恢复 `sort=recent` 和 May、April。完整历史行为见[浏览器导航路径](#%E8%AE%A9%E6%8E%92%E5%BA%8F%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。框架选择要回答的是团队怎样可靠地交付这类更新，以及页面还需要怎样的路由、服务端渲染、无障碍和运维支持。单说“有虚拟 DOM”不能回答这些问题。

### virtual DOM（虚拟 DOM）模型说明什么？

React 组件以当前 props（属性）和 state（状态）返回元素描述。React 将新旧描述进行 reconciliation（协调），再把必要变化 commit（提交）到宿主环境，例如 DOM（文档对象模型）。virtual DOM（虚拟 DOM）是这类描述与协调模型的简称，不是一张真实 DOM 的副本，也不自动表示更新更快。

报表排序改变的是行的顺序。React 可以借助稳定的 `key` 将新旧行对应起来；改变的 JSX 之后是否产生 DOM 修改、修改多少，以及浏览器是否需要布局和绘制，是不同阶段的问题。完整的状态身份与提交过程见[React如何把一次用户操作变成界面更新？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)。

```jsx
{reports.map(report => (
  <ReportRow key={report.id} report={report} />
))}
```

React 用组件类型、树中的位置和同级 key 判断状态能否保留。其他框架可以使用虚拟树协调、编译期转换或更细粒度的依赖追踪；这些是实现取舍，不是产品性能排名。框架各自的更新成本还取决于组件结构、数据量、浏览器工作和具体版本。

### 用一个真实交互比较候选方案

先把报表页的一项代表性交互做成纵向切片：初始 URL 与服务端响应、排序控件、错误与加载状态、键盘使用、测试和部署都在范围内。比较候选时记录用户实际需要的行为，而不是只测孤立的组件基准。

| 需要核对的部分 | 对这张报表页的具体问题 |
|---|---|
| 页面交付 | 首次打开是否要先看到服务端生成的报表，还是可以等客户端请求？ |
| 导航与状态 | `sort`、片段 `#summary`、刷新和浏览器返回是否保持一致？ |
| 交互与无障碍 | 排序控件是否可用键盘操作，结果顺序变化是否容易理解？ |
| 数据与错误 | 服务端结果怎样缓存、过期、重试，以及局部失败时显示什么？ |
| 团队与运行 | 团队能否调试、测试、升级候选框架及其路由和构建工具？ |
| 迁移成本 | 已有页面行为、集成和验证证据需要重做多少？ |

若切片中真正耗时的是服务端网络，换渲染模型不能缩短请求；若测得长任务来自本地计算，服务端查询或 Web Worker（网页工作线程）可能比调整组件树更合适；若大量已挂载行让 DOM 工作变重，再评估虚拟滚动。用实际交互的证据判断瓶颈，后续章节分别解释这些机制。

### 决定前验证边界

框架不是唯一变量。真实环境还包括数据形状、设备、浏览器、访问性需求、发布约束和团队维护能力。保留一个候选框架的理由，应能说清它满足了哪条必要约束、测试了哪条路径，以及哪类工作仍由浏览器或服务端承担。

React 的逐次更新模型见[React如何把一次用户操作变成界面更新？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)；路由与客户端导航的判断见[React路由如何把 URL 映射到视图？](#62.%20React%20%E8%B7%AF%E7%94%B1%E6%80%8E%E6%A0%B7%E6%8A%8A%E5%9C%B0%E5%9D%80%E6%98%A0%E5%B0%84%E5%88%B0%E7%95%8C%E9%9D%A2%E5%B9%B6%E5%8A%A0%E8%BD%BD%E6%95%B0%E6%8D%AE%EF%BC%9F)。

> [!info]- 来源与版本核验（2026-11-06）
> - 本文关于 React 描述、render 与 commit 的边界：React 19.3 当前文档，[Render and Commit](https://react.dev/learn/render-and-commit)、[Versions](https://react.dev/versions)，核验日期 2026-11-06。
> - 框架实现可采用不同渲染机制：React 文档同上；Vue 官方文档，[Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism)，核验日期 2026-11-06。
> - URI 片段只在客户端用于定位，不属于发给服务端的请求：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
## 62. React 路由怎样把地址映射到界面并加载数据？

**案例背景。** 用户打开 `/reports?sort=recent#summary`。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 告诉服务端返回 May、April 两份报表；`#summary` 只用于浏览器定位，不属于 Hypertext Transfer Protocol（超文本传输协议，HTTP）请求。用户点 **Oldest first** 后，地址应新增 `sort=oldest` 历史项，加载结果后行序为 April、May；按 Back 则回到 `sort=recent` 和 May、April。路由把地址、数据请求和界面更新连在一起，不能只把 URL 当作组件选择器。

~~~mermaid
flowchart TD
    A[读取地址 /reports 与查询 sort=recent] --> B[匹配报表路由]
    B --> C[loader（加载器）从地址读 sort]
    C --> D[请求服务端 May、April]
    D --> E[useLoaderData 渲染当前列表]
    E --> F[点击 Oldest first]
    F --> G[PUSH pending：recent 地址和列表暂留]
    G --> H[加载器请求 oldest 数据]
    H --> I{loader 结算}
    I -->|成功| J[提交 oldest URL、历史项与列表]
    I -->|失败| K[提交 oldest URL 与路由错误界面]
    J --> L[Back 的 POP 立即恢复 recent 地址]
    L --> M[loader 等待期间仍显示 oldest 列表]
    M --> N{recent loader 结算后显示列表或错误}
~~~

### 路径、查询和片段各自表达什么

路由器用 pathname（路径名）选择页面，例如 `/reports` 或 `/reports/:reportId`；动态段 `:reportId` 用来标识一份具体报表。多个动态段也能组合成 `/teams/:teamId/reports/:reportId`，`useParams` 读取匹配的路径值。查询参数描述页面当前的筛选、排序或分页状态，像 `?sort=oldest` 可以复制、刷新和由浏览器历史恢复。片段 `#summary` 由浏览器用于定位页面内的位置，客户端能读到它，普通 HTTP 请求不会把它发给服务端。

因此，报表排序由 URL 作为状态来源；用户打开旧地址或按 Back 时，路由从地址重建数据请求和选中状态。不要再用独立的 React state 保存一份互相竞争的 sort。需要低层理解 `pushState`、`popstate` 和片段导航时，见[浏览器导航与历史如何恢复筛选状态？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)。

### 数据模式先匹配路由，再加载匹配页面的数据

React Router 有 Declarative Mode（声明式模式）、Data Mode（数据模式）和 Framework Mode（框架模式）三种模式。声明式模式适合只把路径匹配到组件；数据模式在路由配置之外增加 loader（加载器）、action（提交处理器）、pending（等待）状态和错误边界；框架模式在数据模式上再提供文件路由、类型生成、Server-Side Rendering（服务端渲染，SSR）和静态渲染。以下用当前 React Router v8.5.1 的数据模式与 `createBrowserRouter` 把同一报表地址接到数据加载器。此例是浏览器端路由；框架模式的 loader 可以运行在服务端，部署边界不同。

下面从首次 `recent` loader 已成功、May 和 April 已显示后开始观察。PUSH 切换时关注三处：浏览器地址、`useNavigation().location` 中的目标地址、当前已提交的列表。POP 的地址栏更新时间不同，所以不能把两种导航压成“地址与列表一起切换”。

| 导航 | loader 等待时 | loader 结算后 |
|---|---|---|
| 点 Oldest first（PUSH） | 地址和已提交列表仍是 recent；`navigation.location` 是 oldest。 | 成功时提交 oldest 地址、历史项和 April/May；失败时仍提交目标地址和历史项，但显示该目标路由的错误界面。 |
| 按 Back（POP） | 浏览器地址和历史指针先回到 recent；已提交路由状态与列表暂留 oldest，`navigation.location` 指向 recent。 | 成功后列表切回 May/April；失败后显示 recent 路由的错误界面。 |

首次打开页面时还没有旧列表；上面的“暂留”只适用于从已显示 recent 的状态导航。

~~~tsx
import {
  createBrowserRouter,
  data,
  isRouteErrorResponse,
  Link,
  Outlet,
  useLoaderData,
  useNavigation,
  useParams,
  useRevalidator,
  useRouteError,
  type LoaderFunctionArgs
} from "react-router";
import { RouterProvider } from "react-router/dom";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };

function isReport(value: unknown): value is Report {
  if (typeof value !== "object" || value === null) return false;
  const row = value as Record<string, unknown>;
  return typeof row.id === "string" &&
    typeof row.period === "string" &&
    typeof row.title === "string";
}

function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) {
    throw data("报表服务返回的不是列表", { status: 502 });
  }
  return (value as unknown[]).map(row => {
    if (!isReport(row)) {
      throw data("报表服务返回了无效行", { status: 502 });
    }
    return row;
  });
}

async function reportsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const rawSort = url.searchParams.get("sort") ?? "recent";
  if (rawSort !== "recent" && rawSort !== "oldest") {
    throw data("不支持这个排序方式", { status: 400 });
  }
  const requestedSort: SortOrder = rawSort;

  const apiUrl = new URL("/api/reports", url.origin);
  apiUrl.searchParams.set("sort", requestedSort);
  const response = await fetch(apiUrl, { signal: request.signal });
  if (!response.ok) {
    throw data("报表读取失败", { status: response.status });
  }

  const payload: unknown = await response.json();
  return { sort: requestedSort, reports: parseReports(payload) };
}

function Root() {
  return <Outlet />;
}

function ReportsPage() {
  const { sort, reports } = useLoaderData<typeof reportsLoader>();
  const navigation = useNavigation();
  const loading = navigation.state !== "idle";
  const pendingSort = navigation.location
    ? new URLSearchParams(navigation.location.search).get("sort")
    : null;

  return (
    <main>
      <h1 id="summary">报表</h1>
      <nav aria-label="报表排序">
        <Link
          to="/reports?sort=recent#summary"
          aria-current={sort === "recent" ? "page" : undefined}
        >
          Recent
        </Link>
        {" · "}
        <Link
          to="/reports?sort=oldest#summary"
          aria-current={sort === "oldest" ? "page" : undefined}
        >
          Oldest first
        </Link>
      </nav>
      {loading && (
        <p role="status">
          {pendingSort === "oldest" ? "正在切换到最早顺序…" : "正在加载所选排序…"}
        </p>
      )}
      <ol aria-label="报表" aria-busy={loading}>
        {reports.map(report => (
          <li key={report.id}>
            <Link to={"/reports/" + encodeURIComponent(report.id)}>
              {report.period} — {report.title}
            </Link>
          </li>
        ))}
      </ol>
    </main>
  );
}

function ReportDetail() {
  const { reportId } = useParams();
  return <h1>报表 ID：{reportId}</h1>;
}

function ReportsErrorBoundary() {
  const error = useRouteError();
  const revalidator = useRevalidator();
  const status = isRouteErrorResponse(error) ? error.status : undefined;

  return (
    <section>
      <p role="alert">
        {status === 400 ? "不支持这个排序方式。" : "报表列表暂时无法显示。"}
      </p>
      {(!isRouteErrorResponse(error) || (status !== undefined && status >= 500)) && (
        <button
          type="button"
          onClick={() => revalidator.revalidate()}
          disabled={revalidator.state !== "idle"}
        >
          重新加载
        </button>
      )}
    </section>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      {
        path: "reports",
        loader: reportsLoader,
        Component: ReportsPage,
        ErrorBoundary: ReportsErrorBoundary
      },
      { path: "reports/:reportId", Component: ReportDetail },
      { path: "*", Component: () => <h1>页面不存在</h1> }
    ]
  }
]);

export function App() {
  return <RouterProvider router={router} />;
}
~~~

`reportsLoader` 从当前 URL 校验 `sort`，再把它传给同源 `/api/reports`；片段不会进入 API URL。这个片段假定应用已挂载 `App`，托管端把 `/reports` 文档请求回退到应用入口，同时让 `/api/reports` 继续进入 API 处理器。PUSH 的目标 loader 结算时，不论成功还是失败都会提交目标地址与历史项：成功时换成目标列表，失败时换成目标错误界面。POP 则先改变浏览器历史地址，等待期间保留已提交的列表；loader 结算后再显示 recent 列表或它的错误界面。按 Back 重新走旧 URL 的 loader，不保证取回首次访问时的缓存快照。`useNavigation` 的 `location` 展示等待中的目标，`useLoaderData` 和 `aria-current` 仍代表当前已提交结果。不要在 `Link` 点击之外再手动调用 `history.pushState`，否则浏览器历史和路由状态会有两套写入者。

### 请求取消、过期响应与错误边界

一次数据导航被新的导航打断时，React Router 会取消前一轮 loader 请求并立即处理新地址。把 loader 收到的 `request.signal` 传给底层 `fetch`，客户端就能停止等待已失效的读取；路由器也不会把过期的页面结果提交到当前导航。**这不等于服务端停止了工作**：请求到达服务端后，服务端仍可能继续处理，所以取消客户端读取不能代替写操作的幂等、权限或事务约束。

loader 返回的数据交给匹配的路由组件；它抛出的 HTTP 状态或异常交给最近的路由 `ErrorBoundary`。报表排序参数的 400 错误会提示排序无效，不提供只会重复失败的重试；网络错误或 5xx 可通过 `useRevalidator` 重跑当前已提交 URL 的 loader。列表项的详细页用 `:reportId` 动态段匹配；真实应用也应给它自己的 loader，并在不存在时抛出 404。当前列表错误边界不会把服务端 404 说成“找不到某一份报表”。

路由错误边界也覆盖它下面的 React 子组件：同步渲染错误和子组件 Effect setup 同步抛出的异常会交给边界；事件处理器、timer 或后续 Promise 拒绝不会被它捕获，应在触发这些工作的位置处理。

### 客户端导航与整页导航怎么选

内部 `Link` 在当前文档中切换路由；外部地址或需要浏览器请求另一个完整文档时，使用普通 `<a>`。读取完整 location 时可用 `useLocation`，有明确的程序化跳转需求（例如提交成功后）时再用 `useNavigate`；普通链接仍应保留锚点语义。客户端导航可保留共同布局和局部界面，但部署端必须把直接打开的 `/reports` **文档请求**交给应用入口；`/api/reports` 仍须由 API 处理器应答，不能一并回退到 HTML。若托管环境无法配置路径回退，可以考虑 `HashRouter`（哈希路由器）；它会占用本例的 URL 片段空间。若同时要支持 `#summary` 锚点，应用还得定义并解析自己的片段格式或负责滚动恢复，不能原样使用这个简单地址。`MemoryRouter`（内存路由器）让地址保存在内存中，适合测试和非浏览器环境。

single-page application（单页应用，SPA）与 multi-page application（多页应用，MPA）描述的是页面导航方式，不是服务端渲染的二选一：React Router 框架模式能服务端渲染，也能选择客户端或静态输出。内容以可爬取文档和无 JavaScript 首屏为主时，完整文档导航通常更直接；需要大量共享界面和路由内数据交互时，客户端导航更容易保留上下文。两种方式都要提供语义化链接、明确的加载与错误状态，并验证直接访问和刷新目标 URL。

React Router v8.5.1 的 `useParams`、`Link` 和路由对象 API 承接归档 v6 例子；老 v5 的 `component={Post}` 与 `withRouter` 是另一套接口，不要混用。v5 的 `StaticRouter` 以固定 location 做服务端匹配；当前 Framework Mode 使用自己的服务端路由入口，不应把它当作同一 API。需要维护旧项目时，先看实际依赖版本，再查对应版本的文档。React 组件的状态更新与提交顺序见[React如何把用户操作变成界面更新？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)，服务端查询缓存见[React界面如何维护服务端数据与乐观更新的正确性？](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。

> [!info]- 来源与版本核验（React Router v8.5.1；2026-11-06）
> - 当前稳定版本、v8 迁移边界与运行时最低版本：[React Router Changelog](https://reactrouter.com/changelog)，v8.5.1，2026-10-27。
> - 三种模式的职责和框架模式的服务端渲染 / 静态渲染能力：[Picking a Mode](https://reactrouter.com/start/modes)，核验日期 2026-11-06。
> - 路由对象、嵌套页、动态段和 loader：[Routing](https://reactrouter.com/start/data/routing)、[Route Object](https://reactrouter.com/start/data/route-object)、[Data Loading](https://reactrouter.com/start/data/data-loading)，React Router v8.5.1，核验日期 2026-11-06。
> - 导航提交、等待界面和 pending 位置：[Navigating](https://reactrouter.com/start/data/navigating)、[Pending UI](https://reactrouter.com/start/data/pending-ui)、[useNavigation](https://reactrouter.com/api/hooks/useNavigation)，React Router v8.5.1，核验日期 2026-11-06。
> - 浏览器入口 `react-router/dom` 提供带 `react-dom` flushSync 的 `RouterProvider`：[RouterProvider](https://reactrouter.com/api/data-routers/RouterProvider)，React Router v8.5.1，核验日期 2026-11-06。
> - 当前 location、程序化导航和 loader 重验证的 hook：[useLocation](https://reactrouter.com/api/hooks/useLocation)、[useNavigate](https://api.reactrouter.com/v8/functions/react-router.useNavigate.html)、[useRevalidator](https://api.reactrouter.com/v8/functions/react-router.useRevalidator.html)，React Router v8.5.1，核验日期 2026-11-06。
> - 导航打断、loader 取消和服务端仍可能处理请求：[Race Conditions](https://reactrouter.com/explanation/race-conditions)，React Router v8.5.1，核验日期 2026-11-06。
> - 路由错误边界、最近边界和 404 响应：[Error Boundaries](https://reactrouter.com/how-to/error-boundary)，React Router v8.5.1，核验日期 2026-11-06。
> - React 子组件同步错误由边界兜底、事件处理和异步回调不在该范围：[React Component — Catching rendering errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，核验日期 2026-11-06。
> - 本轮隔离重放（2026-11-06）：Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0；React Router 8.5.1 核对 PUSH/POP 等待期的地址与列表、502 错误提交与重试；相关浏览器排序用例通过。接口为本地合成测试服务。
## 63. Next.js 如何把文件路由、服务端数据与客户端交互连接起来？

**案例背景。** 报表页打开 `/reports?sort=recent#summary`。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端取得 May、April；用户点 **Oldest first** 后，URL 进入 `sort=oldest`，页面显示 April、May，再按 Back 恢复 recent 顺序。`#summary` 是浏览器片段，不会发给服务端。这条主流程假设搜索框为空；若用户已输入查询，客户端本地 query 可以在排序导航和 Back 后继续保留，当前列表仍会被它过滤。本文按当前 Next.js 16.4.5 App Router（应用路由器）讲清：文件怎样选中页面、服务器怎样读 URL 并取数、客户端代码从哪里开始，以及加载和错误如何沿路由边界显示。

~~~mermaid
flowchart TD
    A["/reports?sort=recent#summary"] --> B[Page 读取 searchParams 并启动两项请求]
    B --> C[先显示外壳与排序链接]
    B --> D[摘要与报表分别等待]
    D --> E[数据到达后填充相应区域]
    E --> F[列表中的搜索组件水合后可输入]
    C --> G[排序 Link 可交互后，进入 oldest]
    G --> H{客户端是否已有可复用的目标载荷？}
    H -->|是| I[使用对应 oldest 页面载荷]
    H -->|否| J[服务端 Page 按 oldest 再读取上游]
    J --> I
    I --> K[Back 选择 recent，仍按缓存与请求规则恢复]
    D -->|请求失败| Err[段级 error 界面替换此页面区域]
~~~

### 文件路由把路径落到页面与布局

App Router 把路由写在 `app` 目录：`app/reports/page.tsx` 对应 `/reports`，`app/reports/[reportId]/page.tsx` 对应 `/reports/:reportId`；`layout.tsx` 为一组子路由提供共享外壳，客户端导航时可继续保留。`route.ts` 则按 Hypertext Transfer Protocol（超文本传输协议，HTTP）方法定义 Application Programming Interface（应用程序编程接口，API）端点，不是页面组件；它导出 `GET`、`POST` 等具名函数并返回 `Response`。运行时与部署方式由配置和托管环境决定，放在 Next.js 项目里本身不会自动变成 serverless function（无服务器函数）。

页面收到的动态 `params` 和查询 `searchParams` 都是 Promise，需要在服务端页面中 `await`。对本例来说，`searchParams` 的 `sort` 决定请求哪种顺序；读取它会让页面依赖本次请求，不能把这个值放进不会随导航更新的共享 layout。需要在客户端组件读查询状态时，可使用 `useSearchParams`；若页面本身已经是 Server Component，优先在 Page 读取后把需要的值传给客户端叶节点。

### 服务端与客户端组件在哪条线交接

App Router 的 layout 和 page 默认是 Server Components（服务端组件）。它们能在服务端访问数据库、私有环境变量和后端接口；不进入客户端 JavaScript 包。需要本地 state（状态）、事件处理器、Effect（副作用）或浏览器 API 时，用 `"use client"` 声明 Client Component（客户端组件）的模块边界，并尽量把边界放在实际交互的最小子树。

`"use client"` 不表示“只在浏览器生成 HyperText Markup Language（超文本标记语言，HTML）”。首次访问时，Next.js 会用 Server Component 结果和 Client Component 生成初始 HTML；浏览器先展示静态预览，再下载并 hydrate（水合，让已有标记获得交互）客户端组件。水合要求服务器 HTML 与浏览器首次渲染相同；时间、随机数、地区设置或仅浏览器可读的数据都可能让两边不一致。需要浏览器专属值时，先输出稳定内容，再在首次提交后的 Effect 中读取。后续客户端导航使用 React Server Component Payload（React 服务端组件载荷，RSC payload）更新界面。服务端传给客户端的组件属性（props）必须可序列化；这不是保密机制，可序列化的字符串凭证一旦放进 props 也会进入客户端载荷。函数和数据库连接通常不可序列化，不应作为普通 props 传递。Server Component 可以把已渲染的内容作为 `children` 交给一个 Client Component，但不要从客户端模块图直接导入依赖服务端能力的代码；只传报表展示所需字段，不传内部记录或凭证。

### 用 URL 选排序，并并行加载可独立等待的数据

`page.tsx` 作为 Server Component 读取查询参数。以下例子在得知排序后同时启动报表列表和摘要请求；列表由异步 Server Component 在 `Suspense`（挂起边界）中等待，摘要可独立返回。切换排序的 `Link` 可以直接写在 Server Component 中：链接负责客户端导航、保留路径和片段，若需要服务器重新生成目标载荷，Next.js 再用新的 `searchParams` 运行页面；可复用的客户端载荷则无需这次执行。这是 React Router 浏览器 loader 的替代实现：本例在 Next 服务端向占位上游 `reports.example.test` 请求数据，必须为该主机配置可达的测试服务；它不是浏览器对本应用同源 `/api/reports` 的请求。

~~~tsx
// app/reports/page.tsx
import { Suspense } from "react";
import Link from "next/link";
import { ReportSearch } from "./report-search";

type SortOrder = "recent" | "oldest";
type Report = {
  id: string;
  period: string;
  title: string;
};
type Summary = { totalReports: number };
type PageProps = {
  searchParams: Promise<{ sort?: string | string[] }>;
};

function isReport(value: unknown): value is Report {
  if (typeof value !== "object" || value === null) return false;
  const row = value as Record<string, unknown>;
  return typeof row.id === "string" &&
    typeof row.period === "string" &&
    typeof row.title === "string";
}

function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) throw new Error("Invalid report response");
  return (value as unknown[]).map(row => {
    if (!isReport(row)) throw new Error("Invalid report row");
    return { id: row.id, period: row.period, title: row.title };
  });
}

function parseSummary(value: unknown): Summary {
  if (typeof value !== "object" || value === null) {
    throw new Error("Invalid summary response");
  }
  const summary = value as Record<string, unknown>;
  if (typeof summary.totalReports !== "number" ||
      !Number.isSafeInteger(summary.totalReports) || summary.totalReports < 0) {
    throw new Error("Invalid report count");
  }
  return { totalReports: summary.totalReports };
}

async function getReports(sort: SortOrder): Promise<Report[]> {
  const response = await fetch(
    "https://reports.example.test/api/reports?sort=" + encodeURIComponent(sort),
    { cache: "no-store" }
  );
  if (!response.ok) throw new Error("Could not load reports");
  const payload: unknown = await response.json();
  return parseReports(payload);
}

async function getSummary(): Promise<Summary> {
  const response = await fetch(
    "https://reports.example.test/api/reports/summary",
    { cache: "no-store" }
  );
  if (!response.ok) throw new Error("Could not load report summary");
  const payload: unknown = await response.json();
  return parseSummary(payload);
}

export default async function ReportsPage({ searchParams }: PageProps) {
  const { sort: rawSort } = await searchParams;
  const sort: SortOrder = rawSort === "oldest" ? "oldest" : "recent";
  const reportsPromise = getReports(sort);
  const summaryPromise = getSummary();

  return (
    <main>
      <h1 id="summary">报表摘要</h1>
      <nav aria-label="报表排序">
        <Link
          href="/reports?sort=recent#summary"
          aria-current={sort === "recent" ? "page" : undefined}
        >
          Recent
        </Link>
        {" · "}
        <Link
          href="/reports?sort=oldest#summary"
          aria-current={sort === "oldest" ? "page" : undefined}
        >
          Oldest first
        </Link>
      </nav>

      <Suspense fallback={<p role="status">正在取得摘要…</p>}>
        <ReportSummary promise={summaryPromise} />
      </Suspense>
      <Suspense fallback={<p role="status">正在取得报表…</p>}>
        <ReportList promise={reportsPromise} />
      </Suspense>
    </main>
  );
}

async function ReportSummary({ promise }: { promise: Promise<Summary> }) {
  const summary = await promise;
  return <p>报表数量：{summary.totalReports}</p>;
}

async function ReportList({ promise }: { promise: Promise<Report[]> }) {
  const reports = await promise;
  return <ReportSearch reports={reports} />;
}
~~~

`ReportSearch` 放在独立文件 `app/reports/report-search.tsx`，因为它需要输入 state 和 `onChange`。数据先在服务端取得，再以普通可序列化数组传入：

~~~tsx
"use client";

import { useState } from "react";

type Report = {
  id: string;
  period: string;
  title: string;
};

export function ReportSearch({ reports }: { reports: Report[] }) {
  const [query, setQuery] = useState("");
  const visible = reports.filter(report =>
    report.title.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <section>
      <label>
        搜索报表
        <input value={query} onChange={event => setQuery(event.target.value)} />
      </label>
      <ol aria-label="报表">
        {visible.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}
~~~

输入和本地过滤属于客户端交互；读报表权限、访问私有服务和确定 URL 排序应由服务端负责，但本例没有实现鉴权，真实应用要先在服务端检查用户能否读取这些报表。这里只把少量报表展示字段传到浏览器供本地标题过滤；如果数据量很大或过滤结果受权限、分页影响，应把条件放入 URL 并让服务端按条件查询。`response.json()` 的静态类型不能验证运行时形状；示例在服务边界先把它视为 `unknown`，再逐行检查并投影成三个客户端展示字段，不把上游行对象中可能存在的内部字段顺手传入 RSC payload。摘要中的 `totalReports` 也要求为非负安全整数。

此页的参数策略是：只有单个字符串 `oldest` 选择最早顺序；缺失、`recent`、非法值或重复参数（`string[]`）都回退到 `recent`。这是本例选定的回退契约；React Router 例子则会对其读取到的非法首值返回 400。

`cache: "no-store"` 控制这个 Next 服务端 `fetch` 在实际执行时不要读写持久数据缓存；若 `Page` 执行，它会向上游请求新结果。它不强迫每次 Link/Back 都重新执行服务端 Page：客户端路由可能直接复用已缓存的 React Server Component Payload（React 服务端组件载荷，RSC），因此 `no-store` 也不保证每次浏览器导航都打到上游。当前案例按 URL 保存排序条件，但不冻结返回数据的版本。Next.js 16.4.5 默认的 `auto no cache` 会在动态页面的每次请求中取数，在静态预渲染页面的构建时取数；本例访问 `searchParams`，所以是请求时页面。开启 `cacheComponents`（缓存组件）后，数据默认按请求动态读取；需要跨请求缓存时，使用 `use cache`（缓存指令）明确标出可复用的页面、函数或组件。开发模式的 Hot Module Replacement（热模块替换，HMR）也可能暂时复用 `no-store` 结果，不能把热更新时没变化误判为生产缓存策略。

### 加载、失败和重试各有自己的边界

`app/reports/loading.tsx` 自动为该路由段提供加载界面；更小的 `Suspense` 区域可以让摘要和列表各自出现。等待界面只是表示数据尚未准备好，不会处理读取失败。

~~~tsx
// app/reports/loading.tsx
export default function Loading() {
  return <p role="status">正在打开报表…</p>;
}
~~~

在同一段创建 `app/reports/error.tsx`，用 Client Component 显示可恢复的错误状态。此边界包住当前段的页面和子段，但不会捕获同段 `layout.tsx` 自己抛出的错误；错误向上交给父段边界。Next.js 16.3 起，重试回调 `retry` 已稳定；它会重新读取并渲染边界内的内容。根 `layout.tsx` 本身失败时，使用 `app/global-error.tsx`；全局错误界面要自己提供 `html` 与 `body`。

~~~tsx
// app/reports/error.tsx
"use client";

import { useEffect } from "react";

export default function ReportsError({
  error,
  retry
}: {
  error: unknown;
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <section>
      <p role="alert">报表暂时无法显示。</p>
      <button type="button" onClick={() => retry()}>
        重新读取
      </button>
    </section>
  );
}
~~~

此页的 `Link` 使用客户端过渡，Back 会把地址恢复到 `sort=recent`；App Router 可以复用客户端路由缓存，也可以请求服务器取得对应页面，不能据此断言一定发生网络重取，也不保证恢复某个旧数据快照。若服务端报表本身未改变，页面排序仍回到 May、April；若服务端数据已变，URL 只固定查询条件，不冻结数据版本。在服务端页面函数中没有 React Router 那样公开的 loader `request.signal`，不能因为用户切换路由，就宣称 Next 已停止服务端接口或数据库工作。客户端自己启动的 fetch 可用 `AbortController` 在组件清理时取消等待；服务端请求则应有合适的超时、幂等和数据一致性保护。当服务端实际重新执行 Page 时，才从新 URL 读取对应排序并请求上游。较低层的 History API 与 Back 语义见[浏览器导航与历史如何恢复筛选状态？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)，React 中的过期响应和查询缓存见[React界面如何维护服务端数据与乐观更新的正确性？](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。

`app/reports/error.tsx` 中的 `retry()` 会重新读取并渲染边界内的页面内容；例如当前 `sort=oldest` 的上游请求失败时，它仍以 oldest 参数重试，成功后列表替换错误界面。它不会悄悄改回 recent。

### 旧版 Pages Router（页面路由器）代码怎样与 App Router 区分

当前例子使用 App Router；旧 Pages Router 应按它自己的运行模型维护，不要把两套 API 拼进一个文件。

| 需求 | Pages Router 旧入口 | 当前 App Router |
|---|---|---|
| 动态路径参数 | `next/router` 的 `router.query` | 页面收到 Promise `params`，`await` 后读取 |
| 查询参数 | `router.query`；自动静态优化期间首屏可能暂时为空，客户端代码应在 Effect（副作用）中等 `router.isReady` | 页面收到 Promise `searchParams`；读取会使用请求时 URL |
| 服务端数据 | `getServerSideProps` 按请求读取；`getStaticProps` 配合 `getStaticPaths` 构建静态页 | 默认 Server Component 读取服务端数据；本篇 `no-store` 示例每次按请求读取 |
| 刷新静态结果 | `getStaticProps` 的 `revalidate` 支持 Incremental Static Regeneration（增量静态再生，ISR） | 按当前 App Router 缓存配置选择重新读取或缓存 |
| API 端点 | `pages/api` 的默认处理器 | `app/**/route.ts` 按 HTTP 方法导出处理器 |

Pages Router 中的 `revalidate: 60` 是允许请求触发再生成的最小间隔，不是后台每分钟准点重建；间隔过后，首个请求可能先读到旧页，同时触发新版本生成。动态路由还要用 `getStaticPaths` 的 `fallback` 决定构建时未列出的路径是直接 404，还是首个请求到来时先生成页面。这个 ISR 语义只用于识别维护中的旧 Pages Router 代码，不与本篇 App Router 的 `no-store` 报表请求混用。

App Router 的客户端导航优先用 `next/link`；需要在客户端代码中编程导航时，使用 `next/navigation` 的 `useRouter`。旧 `next/router`、`router.query` 和 Pages Router 数据函数不适用于 `app/` 页面。当前客户端组件和服务端组件的边界不因保留 Pages Router 而消失：同一项目可以逐段迁移，但每段代码都必须明确属于哪种路由器。

> [!info]- 来源与版本核验（Next.js 16.4.5；2026-11-06）
> - 当前稳定版本：Next.js 官方 [v16.4.5 release](https://github.com/vercel/next.js/releases/tag/v16.4.5)；以下 App Router 文档按官方当前页面核验于 2026-11-06。
> - 服务端与客户端组件的默认归属、首次页面文档、hydrate、可序列化属性与边界范围：[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)。
> - 服务端到客户端只传界面所需数据及在服务端检查授权：[Data Security — Passing Data from Server to Client](https://nextjs.org/docs/app/guides/data-security#passing-data-from-server-to-client)，核验日期 2026-11-06。
> - 页面 `params` / `searchParams` Promise、查询参数触发动态渲染及共享 layout 不接收 searchParams：[page.js](https://nextjs.org/docs/app/api-reference/file-conventions/page)。
> - `Link` 的客户端导航、预取与历史行为：[Linking and Navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating)、[Link API](https://nextjs.org/docs/app/api-reference/components/link)。
> - Server Component 中读取数据、并行请求与 Suspense 流式返回：[Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data)、[loading.js](https://nextjs.org/docs/app/api-reference/file-conventions/loading)。
> - 水合一致性、Effect 仅在客户端运行，以及首屏输出要求：[React hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)、[React useEffect](https://react.dev/reference/react/useEffect)。
> - `fetch` 缓存默认值、`no-store`、请求期页面与开发热模块替换缓存：[fetch API](https://nextjs.org/docs/app/api-reference/functions/fetch)、[Cache Components](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents)。
> - `loading.tsx`、`error.tsx`、稳定的 `retry` 与 `global-error.tsx`：[loading.js](https://nextjs.org/docs/app/api-reference/file-conventions/loading)、[error.js](https://nextjs.org/docs/app/api-reference/file-conventions/error)，Next.js 16.3 起 `retry` 稳定；核验版本 16.4.5。
> - Pages Router 参数与 `router.isReady`：[Pages Router useRouter](https://nextjs.org/docs/pages/api-reference/functions/use-router)。
> - Pages Router 按请求读取、静态生成与 ISR：[getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props)、[getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths)、[Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration)。
> - App Router 路由端点的方法导出与响应：[Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route)。
> - 本轮隔离重放（2026-11-06）：Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0；Next.js 16.4.5 生产构建核对排序、Back 的 RSC 复用、本地搜索保留及摘要失败后的 retry。上游为本地合成测试服务。
## 64. Lodash 何时适合处理报表列表，哪些方法会修改输入？

**案例背景。** 用户在 `/reports?sort=recent#summary` 看到 May、April 两份报表。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端返回 May、April；点击 **Oldest first** 后，地址的 `sort` 变为 `oldest`，服务端返回 April、May；按 Back 回到 recent 和 May、April。地址和请求属于路由层；Lodash 只转换已经交给它的数据，不拥有排序状态，也不会替代服务端查询。

~~~mermaid
flowchart LR
    A[URL sort=recent] --> B[服务端返回 May、April]
    B --> C[组件显示列表]
    C --> D[Oldest first 开始路由导航]
    D --> E[loader 读取 oldest 并返回数据]
    E --> F[结算后提交 oldest URL 与 April、May]
    F --> Back[Back 恢复 recent URL 并重跑路由数据]
    B -.本地拥有副本时才选此分支.-> G[本地列表]
    G --> H[orderBy 返回新数组]
    G --> I[merge 按索引原地合并]
~~~

### 排序逻辑应跟着数据来源走

真实应用让 `sort` 查询参数决定服务端顺序；同一列表不要再由组件状态保存一份排序，也不要在收到已经排好序的服务端结果后重复排序。若数据确实由当前组件本地排序，`_.orderBy` 会按指定字段和方向返回一个新数组，不会改动传入的 recent 数组：

~~~javascript
const recent = [
  { id: "may", period: "May", month: "2026-05" },
  { id: "april", period: "April", month: "2026-04" }
];

const oldest = _.orderBy(recent, ["month"], ["asc"]);

oldest.map(report => report.period); // ["April", "May"]
recent.map(report => report.period); // ["May", "April"]
oldest[0] === recent[1]; // true：新数组仍共享 April 行对象
~~~

`_.sortBy` 同样返回新数组，按升序排列；要写清升降序或多个字段时用 `_.orderBy`。新数组只是行引用的新顺序，`oldest[0]` 仍是 `recent[1]` 那个 April 对象；改行对象会同时改到两边。图中的分支表示组件确实拥有一份本地数据时才做本地转换，不表示服务端排序页还要二次排序。生产路由仍从 URL 发出排序请求，避免两套逻辑相互覆盖。

### 深合并为什么会改到已有报表数据

`_.merge(target, ...sources)` 会递归合并并修改第一个参数，然后返回这个目标对象。数组按索引合并，不会拼接：

~~~javascript
const cached = {
  reports: [
    { id: "may", period: "May", owner: { team: "Ops" } },
    { id: "april", period: "April" }
  ]
};
const patch = {
  reports: [{ owner: { reviewed: true } }]
};

const changed = _.merge(cached, patch);
changed === cached; // true
cached.reports[0].owner.reviewed; // true
cached.reports.length; // 2，patch 的第 0 项合并进原第 0 项
~~~

把同一个引用传回 React state，可能因引用没变而跳过渲染；若 `cached` 还被请求缓存、其他组件或测试共享，也会一起看到被改的值。要建立新值，可以把新对象作为目标：

~~~javascript
const next = _.merge({}, cached, { reports: [{ owner: { reviewed: false } }] });
next !== cached; // true
~~~

这个写法只改变目标引用，不会让数组按 ID 匹配；数组仍按索引合并。纯列表补项应显式拼接，例如 `[...cached.reports, newReport]`。`_.assign` 也会修改目标，只做浅层赋值。用库方法前，先看它返回哪个对象以及是否改变输入。

同一个 `patch.reports[0]` 会随当前排序改到不同报表：

| 正在合并的顺序 | 第 0 行 | 补丁结果落到 |
|---|---|---|
| recent：May、April | May | May 的 `owner.reviewed` |
| oldest：April、May | April | April 的 `owner.reviewed` |

如果补丁实际针对某个 `report.id`，先按 ID 找到那一行再更新，别把“第 0 行”当成报表身份。

需要写入嵌套路径时，`_.set` 也会原地修改目标：

~~~javascript
const draft = {};
const result = _.set(draft, "owner.team", "Ops");
result === draft; // true
draft.owner.team; // "Ops"
~~~

### 深路径默认值要区分缺失与 null

`_.get` 只在路径结果为 `undefined` 时采用默认值；如果接口明确返回 `null`，结果仍是 `null`：

~~~javascript
const missingOwner = { owner: {} };
const emptyOwner = { owner: { name: null } };

_.get(missingOwner, "owner.name", "Unknown"); // "Unknown"
_.get(emptyOwner, "owner.name", "Unknown");   // null
emptyOwner.owner?.name ?? "Unknown";          // "Unknown"
~~~

当报表确实允许“没有负责人”和“负责人字段未返回”表达不同状态时，这个差异会改变空态文案。字段路径固定时，原生可选链和显式回退值通常更直接。

### 其他方法先看返回值和边界

| 方法 | 对界面数据的实际契约 |
|---|---|
| `_.concat(array, ...values)` | 返回浅拼接的新数组；把传入数组展开一层，数组里再嵌套的数组保持嵌套。 |
| `_.drop(array, n = 1)` | 返回去掉前 `n` 项后的新切片。 |
| `_.find(collection, predicate, fromIndex = 0)` | 只找第一项；数组可从 `fromIndex` 开始，不会返回全部匹配行。 |
| `_.each(collection, iteratee)` | 遍历后返回原集合；`_.forEach` 是别名，不适合当作变换后的新列表。 |
| `_.keys(object)` | 返回对象自有、可枚举的字符串键，不含 Symbol（符号）键。 |
| `_.uniq(array)` | 返回保留首次出现顺序的新数组；若只需原生值集合，Set（集合）可能更清楚。 |
| `_.compact(array)` | 移除所有假值，包括 `0`、`false` 和空字符串；报表字段可能合法为 `0` 时不能用它清洗行。 |
| `_.times(n, iteratee)` | 调用迭代器 `n` 次并返回结果数组。 |

`_.uniqueId(prefix)` 只使用当前 Lodash 模块实例的递增计数器；结果受先前调用影响，不保证跨进程或多份模块全局唯一，也不是安全令牌。列表行优先用服务端稳定的 `report.id`；认证能力令牌应使用具备相应安全契约的生成器。

### 搜索输入可以延迟，排序导航不应延迟

Lodash 的 debounce（防抖）方法 `_.debounce` 会等最后一次调用后的等待时间过去再执行；`leading`、`trailing` 和 `maxWait` 会改变它何时运行。用它减少报表标题搜索的请求频率时，保留当前 URL 的 `sort`，并在组件卸载或输入控件销毁时取消尚未触发的调用：

~~~javascript
const scheduleReportSearch = _.debounce(
  (query, sort) => fetchReports({ sort, query }),
  300,
  { trailing: true, maxWait: 1000 }
);

function onSearchInput(query, currentUrlSort) {
  scheduleReportSearch(query, currentUrlSort);
}

function onSortNavigation(navigate) {
  scheduleReportSearch.cancel(); // 丢弃尚未开始的旧排序搜索
  navigate("/reports?sort=oldest#summary"); // 立即开始路由导航
}

function onSearchPanelUnmount() {
  scheduleReportSearch.cancel();
}
~~~

防抖函数要在一段组件生命周期内复用；排序处理器取消待发的搜索，再立即把导航交给路由。React Router Data Mode 会先加载目标数据，地址和历史项在结算时提交；这里的 `navigate` 只表示开始导航，不表示地址在点击瞬间提交。Back 则由浏览器选回 recent 历史项并触发路由加载。`cancel` 只撤销尚未触发的调用，不会中止已经发出的网络请求；真正停止传输需要请求服务配合 AbortSignal（请求取消信号）。

这段处理器只覆盖显式点击与卸载。Back/Forward 不会经过 `onSortNavigation`：若 oldest 下的搜索计时器尚未触发，Back 已提交 recent 后，它仍可能带着捕获的 oldest 发请求。接入真实路由时，应在每次已提交的 sort 改变时同样取消旧待发搜索，并用请求代次或查询键保护结果；已经启动的旧请求即便无法取消，也不能覆盖新条件下的列表。

同时开启 leading 和 trailing 时，trailing 只在等待窗口内发生多次调用后才会再执行；若调用方需要立即提交尚待执行的尾部输入，可用 `.flush()`：

~~~javascript
const search = _.debounce(fetchReports, 300, { leading: true, trailing: true });
search({ query: "O" });
search({ query: "Ops" }); // 窗口内第二次调用，结束时会执行 trailing
search.flush(); // 若 trailing 尚待执行，现在就执行
~~~

Lodash 的 throttle（节流）方法 `_.throttle` 则限制调用频率，适合按固定间隔响应滚动或连续事件，不等同于 debounce。若要理解这两种计时包装函数怎样用闭包保存 timer、最新参数和触发时刻，见[原生闭包如何实现定时防抖与首沿节流？](#%E5%AE%9A%E6%97%B6%E5%9B%9E%E8%B0%83%E6%80%8E%E6%A0%B7%E7%94%A8%E9%97%AD%E5%8C%85%E4%BF%9D%E7%95%99%E8%B0%83%E5%BA%A6%E7%8A%B6%E6%80%81)。

### 何时优先用原生操作

路径明确时，原生可选链、`Array.prototype.flat`（数组扁平化）、Set 或对象展开常常更易读。需要 Lodash 的边界行为时，先核对版本和输入形状，再决定是否使用。按方法导入可以帮助构建器裁剪依赖，但最终包体还受模块格式和构建配置影响；要用生产产物测量，不能只凭写法推断体积。

相关内容见[现代 JavaScript 特性](#50.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E7%9B%AE%E6%A0%87%E6%B5%8F%E8%A7%88%E5%99%A8%E6%88%96%20Node.js%20%E6%98%AF%E5%90%A6%E6%94%AF%E6%8C%81%E4%B8%80%E9%A1%B9%20JavaScript%20%E7%89%B9%E6%80%A7%EF%BC%9F)与[前端性能测量](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源与版本核验（Lodash 4.18.1；2026-11-06）
> - 当前稳定版本及 4.18.1 发布记录：[Lodash Releases](https://github.com/lodash/lodash/releases)，2026-04-01。
> - 排序、深合并、数组按索引合并、对象路径、字符串、集合和计时方法：[Lodash 4.18.1 API 文档](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md)。
> - 原生数组展平与空值运算符：[Array.prototype.flat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat)、[Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)，核验日期 2026-11-06。
## 65. ahooks 怎样管理报表请求、分页与列表身份？

**案例背景。** 报表从 `/reports?sort=recent#summary` 打开时显示 May、April。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 是排序和历史状态的来源；用户选 **Oldest first** 后，路由把 `sort=oldest` 传给报表请求，列表变成 April、May；按 Back 时 recent 再次成为请求输入。ahooks 管组件中的请求状态、分页或可编辑列表，不应另存一份竞争的 sort。

~~~mermaid
flowchart TD
    A[父 loader 只解析 URL，提交 sort=recent] --> B[Hook 请求报表]
    B --> C[显示 May、April]
    C --> D[Oldest first 发起路由导航]
    D --> E[父 loader 只返回 sort=oldest，路由提交]
    E --> F[Hook 发起 oldest 请求；旧列表可暂留]
    F --> G[新请求成功后显示 April、May]
    G --> H[Back 先恢复 recent 地址]
    H --> I[父 loader 提交 recent，Hook 再请求列表]
~~~

### 请求 Hook（钩子）管本地请求状态，不自动取得传输控制权

下面的例子假定父级只负责路由：它从 URL loader 的**已提交数据**中取出 `sort` 并传给组件；不要把 `navigation.location` 中尚未提交的目标值提前传入。父 loader 在这个替代方案中只解析并校验 `sort`，不取报表：其返回值为 `{ sort }`，父组件再将 `useLoaderData()` 中已提交的 `sort` 传给 `ReportPanel`。此处由组件独自拥有列表请求，不同时配置 React Router loader 或 TanStack Query 请求同一份列表。`fetchReports` 是会校验响应形状的 Application Programming Interface（应用程序编程接口，API）客户端。初次渲染会自动请求；`refreshDeps` 改变时，Hook 使用最新的服务函数再次请求。等待期间 `data` 可以保留上次成功的列表：

~~~tsx
import { useState } from "react";
import { useDebounce, useRequest } from "ahooks";
import { fetchReports } from "./report-api";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };

function ReportPanel({ sort }: { sort: SortOrder }) {
  const [query, setQuery] = useState("");
  const settledQuery = useDebounce(query, { wait: 300 });
  const { data: reports, loading, error } = useRequest(
    () => fetchReports({ sort, query: settledQuery }),
    { refreshDeps: [sort, settledQuery] }
  );

  return (
    <section>
      <label>
        搜索报表
        <input
          value={query}
          onChange={event => setQuery(event.target.value)}
        />
      </label>
      {loading && <p role="status">正在加载报表…</p>}
      {error && <p role="alert">报表读取失败。</p>}
      <ol aria-label="报表" aria-busy={loading}>
        {reports?.map((report: Report) => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}
~~~

`useDebounce` 返回延迟后的值，不返回网络请求。假设输入前搜索条件为空，用户输入 `Ops` 后立刻切换到 oldest，且路由在 300 ms 防抖到期前已经提交 oldest，服务调用顺序是 `recent/"" → oldest/"" → oldest/"Ops"`：排序导航一开始，路由仍保留 recent 的已提交页面；等 oldest loader 成功，父级才把 `sort=oldest` 交给这个组件，随后 `refreshDeps` 触发请求；300 ms 到期后搜索值再触发一次。若路由更慢，搜索值会先在 recent 下生效，调用顺序也随之改变；决定请求参数的是当时已提交的 sort 和已稳定的搜索值。新的 `useRequest` 调用会让前一次结果过期，但等新数据成功前，屏幕上的旧列表仍是最近一次成功结果，不代表它已经符合 oldest 或 `Ops` 条件。按 Back 时父级在 recent loader 结算前仍保留 oldest，因此 Hook 不会抢先发 recent 请求。输入防抖不延迟路由导航。若 React Router loader 或 TanStack Query 已经负责同一份列表，就不要再挂这段 `useRequest` 重复读取。

`useRequest` 默认自动运行（且 `ready` 为 true）；`manual: true` 才等待调用 `run` 或 `runAsync`。`run` 返回 `void`，失败由 `onError` 等回调处理；`runAsync` 返回 Promise，调用方应处理失败。v3.11.0 的 `Fetch.runAsync` 会等服务 Promise 结算后才比较请求代次；若它已过期，才以 `CancelledError` 拒绝，`run` 会处理这个取消错误。`cancel()` 会立即让 Hook 忽略当前 Promise 的结果并结束 Hook 的等待状态，但 `runAsync` 仍需等原服务 Promise 结算后才能拒绝；如果服务 Promise 永不结算，调用方的 `runAsync` 也可能一直 pending。它不会撤销已经发给浏览器或服务端的网络请求。若传输必须停止，服务本身还要接收并响应 AbortSignal（请求取消信号），通常由 AbortController（请求控制器）发出。

常用状态和控制各自回答不同问题：

| 返回值 | 契约 |
|---|---|
| `data / error / loading / params` | 最近请求的数据、错误、等待状态和最后一次参数。 |
| `run` | 启动服务，返回 `void`；普通失败走 Hook 的错误回调。 |
| `runAsync` | 启动服务并返回 Promise；取消的调用也可能拒绝。 |
| `refresh / refreshAsync` | 使用最近一次参数重新请求。 |
| `mutate` | 改变 Hook 当前展示的数据；不等于写入服务端，也不自动同步其他数据所有者。 |
| `cancel` | 忽略当前请求结果；不等于底层请求的 AbortController。 |

v3.11.0 的其他 `useRequest` 选项还包括首次自动调用时使用的 `defaultParams`、`onBefore` / `onSuccess` / `onError` / `onFinally` 回调，以及 `retryCount` / `retryInterval` 重试控制；重试适合可安全重放的读取。维护 v2 项目时会遇到 `debounceInterval` / `throttleInterval`；v3 将名称改为 `debounceWait` / `throttleWait`，并以 `usePagination`、`useInfiniteScroll` 替代 `pagination`、`loadMore` 请求选项，原来的 `formatResult` 转换要放在服务层。升级代码前先核对实际依赖版本，别把两代选项混用。

### 分页服务返回 total 与 list，滚动加载返回下一段

`usePagination` 的服务接收 `current` 和 `pageSize`，解析为 `{ total, list }`；排序变化时 `refreshDeps` 会重置到第一页并重新请求。例中 42 条、每页 20 条，下一页按钮会走到第 2 页，再走到第 3 页，并在加载或到末页时禁用。Hook 的页码是局部状态；需要刷新或 Back 保留页码时，应像排序一样让 URL 成为来源并把页码传给服务。

~~~tsx
import { usePagination } from "ahooks";
import { fetchReportPage } from "./report-api";

// 沿用上文的 SortOrder、Report 类型。
function PagedReports({ sort }: { sort: SortOrder }) {
  const { data, loading, pagination } = usePagination(
    ({ current, pageSize }) =>
      fetchReportPage({ sort, current, pageSize }),
    { defaultPageSize: 20, refreshDeps: [sort] }
  );

  return (
    <section>
      <ol aria-label="报表" aria-busy={loading}>
        {data?.list.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
      <button
        type="button"
        onClick={() => pagination.changeCurrent(pagination.current + 1)}
        disabled={loading || !data || pagination.current * pagination.pageSize >= data.total}
      >
        下一页
      </button>
    </section>
  );
}

// API 响应形状：{ total: 42, list: Report[] }；pageSize 为 20 时可依次到第 2、3 页。
~~~

`useInfiniteScroll` 则把已累计数据交回服务，让服务用当前游标获取下一页；Hook 会把新列表接到已有列表后面。继续条件、错误、载入更多状态和稳定的行 ID 仍要由组件呈现。下面只用显式按钮触发后续页，便于读者看清每次请求的来源：

~~~tsx
import { useInfiniteScroll } from "ahooks";
import { fetchNextReportPage } from "./report-api";

type ReportPage = { list: Report[]; nextCursor: string | null };

function ReportFeed({ sort }: { sort: SortOrder }) {
  const { data, loading, loadingMore, error, noMore, loadMore } =
    useInfiniteScroll(
      (current?: ReportPage) =>
        fetchNextReportPage({ sort, cursor: current?.nextCursor ?? null }),
      {
        reloadDeps: [sort],
        isNoMore: current => current != null && current.nextCursor === null
      }
    );

  return (
    <div style={{ height: 360, overflow: "auto" }}>
      {loading && <p role="status">正在读取报表…</p>}
      {error && <p role="alert">继续加载失败。</p>}
      <ol>
        {data?.list.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
      <button
        type="button"
        onClick={loadMore}
        disabled={loading || loadingMore || noMore}
      >
        {noMore ? "没有更多报表" : "加载更多"}
      </button>
    </div>
  );
}
~~~

若选择滚动自动续页，可另传滚动容器 `target` 与 `threshold`；短首屏未填满容器时，Hook 可能自动继续取下一页。若同时提供自动滚动和按钮，两个触发可能撞上同一个在途游标，应在服务边界合并相同 `(sort, cursor)` 请求。上例只使用手动按钮。

这里 `fetchNextReportPage` 的响应有 `list` 和 `nextCursor`；`isNoMore` 在游标为 null 时停止。实际接口要校验分页响应，并限制重复请求和授权范围。ahooks v3.11.0 修复了空页导致连续自动请求的问题；仍应处理空列表、错误和没有下一页的状态。

### 可编辑表单行要用可复现的稳定身份

`useState(() => reports)` 只把 props 当作首次初始化值；父路由后来传来 oldest 列表时，已编辑列表不会自动同步。下面明确把表单定义成一次编辑会话的快照：要放弃草稿并换数据时，调用者应显式开始新会话或重置列表。服务端报表使用自己的 `report.id`；新增草稿在点击事件中只生成一次 ID：

~~~tsx
function EditableReportList({ reports }: { reports: Report[] }) {
  const [list, setList] = useState(() => reports);

  return (
    <>
      <button
        type="button"
        onClick={() => {
          const draft = {
            id: `draft:${crypto.randomUUID()}`,
            period: "草稿",
            title: "待补报表"
          };
          setList(current => [draft, ...current]);
        }}
      >
        添加草稿
      </button>
      {list.map(report => (
        <div key={report.id}>
          {report.period} — {report.title}
          <button
            type="button"
            onClick={() => setList(current => current.filter(row => row.id !== report.id))}
          >
            移除
          </button>
        </div>
      ))}
    </>
  );
}
~~~

ahooks v3.11.0 文档把 `useDynamicList.getKey(index)` 描述为可保持列表项身份的 key；但在 React 19.3.1 开发 StrictMode 下实测，初始化和插入都触发其内部 key ref 的重复递增，插入前 May/April 的 key 为 2/3，插入后变为 4/2，新草稿为 5，和常见使用者预期不符。这是该版本与开发 StrictMode 的实测问题，不应泛化为 React 的 key 契约；主例因此用业务 `report.id` 和每次新增只生成一次的草稿 ID。若维护依赖 `getKey` 的代码，应在实际 React、ahooks 版本和 StrictMode 配置下覆盖插入、移动、重置行为。`useDynamicList` v3.11.0 还提供 `move`、`batchRemove`、`replace`、`push` / `pop`、`unshift` / `shift` 和 `resetList`；`merge(index, items)` 是把多项插入列表的位置操作，不是 Lodash 的对象深合并。`sortList` 会保留 `0`、`false` 和空字符串，只剔除 `null` 与 `undefined`。

`useVirtualList` 在 v3.11.0 返回 `[visibleRows, scrollTo]`，每项带 `data` 和源 `index`，通过 `containerTarget` / `wrapperTarget` 配置滚动容器；`itemHeight` 可为固定数值或按行计算的函数，行高要与实际布局相符；源数组要保持稳定或由 `useMemo` 记住，否则 Hook 会重复重新计算。归档 ahooks v2.6 使用对象返回值 `{ list, containerProps, wrapperProps, scrollTo }`；其 `itemHeight` 函数按源索引给出高度，没有独立的 `estimateSize` 参数，不要混用版本。虚拟化只减少挂载的 Document Object Model（文档对象模型，DOM）行数，不会减少网络分页或完整源数组的内存；变高行、可访问边界与滚动成本见[大列表如何在网络、DOM 和可访问性之间取舍？](#15.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。

### 轻量状态和时序工具也有边界

`useBoolean` 提供显式布尔动作，`useToggle` 切换两个值，`useMap` 和 `useSet` 管集合；`useCreation(factory, deps)` 按依赖复用创建结果，但不提供资源生命周期或永久语义缓存保证。不要在其 factory 中做 Effect 副作用。

`useLatest(value)` 返回会更新到最新值的 ref，适合已安装的长生命周期回调读取新数据；`useMemoizedFn(fn)` 保持函数引用稳定，同时调用最新的函数体。前者解决回调读取哪个值，后者解决函数身份是否变化，两者契约不同。`useLocalStorageState` 方便持久化浏览器设置，也可同步其他标签页；Storage（浏览器存储）可能不可用或被用户改写，不能当作可信权限来源，服务端渲染也应等到浏览器端读取。

`useMount` / `useUnmount` 是 Effect 建立与清理的封装，不等于进程生命周期内绝对只运行一次。根级 React StrictMode 开发模式会额外执行一次 setup → cleanup → setup；订阅或计时器等副作用要能正确清理，首次载入也不能产生不可逆的重复动作。

| Hook | 返回 / 默认时序 |
|---|---|
| `useDebounce(value)` | 延迟后的值，`wait` 默认 1000 ms，`leading` 默认 false，`trailing` 默认 true；`maxWait` 可选。 |
| `useThrottle(value)` | 限频后的值，`wait` 默认 1000 ms，`leading` 与 `trailing` 默认 true。 |
| `useDebounceFn(fn)` | `{ run, cancel, flush }`；默认 `wait` 1000 ms、leading false、trailing true。 |
| `useThrottleFn(fn)` | `{ run, cancel, flush }`；默认 `wait` 1000 ms、leading / trailing true。 |

debounce 的 `cancel` 只取消尚未执行的函数调用；请求已经开始后，必须另行管理网络取消。排序点击应立即发起导航，地址与列表的提交时点由路由决定；输入搜索适合等待停顿后再查。更多 React Hook 生命周期见[React 组件如何组合状态与行为？](#7.%20%E5%A6%82%E4%BD%95%E5%9C%A8%20React%20%E4%B8%AD%E7%BB%84%E5%90%88%E7%BB%84%E4%BB%B6%E4%B8%8E%E5%A4%8D%E7%94%A8%E8%A1%8C%E4%B8%BA%EF%BC%9F)，服务端查询与乐观更新见[React界面如何维护服务端数据与乐观更新的正确性？](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。

> [!info]- 来源与版本核验（ahooks v3.11.0；2026-11-06）
> - 当前稳定版本和 v3.11.0 的分页、取消、空页、动态列表假值修复：[ahooks v3.11.0 release](https://github.com/alibaba/hooks/releases/tag/v3.11.0)，2026-10-27。
> - `useRequest` 的默认自动执行、手动控制与状态：[useRequest](https://ahooks.js.org/hooks/use-request/)；`runAsync` 取消拒绝和 `run` 处理由 [v3.11.0 Fetch source](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/Fetch.ts) 核验。
> - 请求回调、默认参数、重试和 v3 `debounceWait` / `throttleWait`：[v3.11.0 option types](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/types.ts)；v2 到 v3 的旧请求选项迁移：[upgrade guide](https://ahooks.js.org/guide/upgrade/)，2026-11-06。
> - 分页响应和 `refreshDeps`：[usePagination](https://ahooks.js.org/hooks/use-pagination/)；累积列表、游标服务、停止条件与滚动目标：[useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll/)。
> - `useDynamicList` 的文档 key 契约、操作与 `sortList`：[useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list/)、[v3.11.0 type definition](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useDynamicList/index.ts)、[v3.11.0 release changes](https://github.com/alibaba/hooks/releases/tag/v3.11.0)。开发 StrictMode key 漂移是 v3.11.0 + React 19.3.1 的本地实测，不作为通用 API 语义。
> - `useLatest`、`useMemoizedFn`、`useLocalStorageState` 和 Mount/Unmount helper：[useLatest](https://ahooks.js.org/hooks/use-latest/)、[useMemoizedFn](https://ahooks.js.org/hooks/use-memoized-fn/)、[useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state/)、[useMount](https://ahooks.js.org/hooks/use-mount/)、[useUnmount](https://ahooks.js.org/hooks/use-unmount/)，核验日期 2026-11-06。
> - 当前虚拟列表结果形状与行高函数：[useVirtualList](https://ahooks.js.org/hooks/use-virtual-list/)、[v3.11.0 implementation](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useVirtualList/index.ts)；v2.6.0 旧结果形状：[v2.6.0 source](https://github.com/alibaba/hooks/blob/v2.6.0/packages/hooks/src/useVirtualList/index.ts)。
> - debounce / throttle 返回值与默认选项：[useDebounce](https://ahooks.js.org/hooks/use-debounce/)、[useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn/)、[useThrottle](https://ahooks.js.org/hooks/use-throttle/)、[useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn/)。
> - 本轮隔离重放（2026-11-06）：Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0；ahooks 3.11.0 核对请求代次、分页重置、手动游标追加、草稿会话和取消；短首屏自动加载与按钮并用可重复请求同一游标，主例因此只保留按钮触发。
## 66. 前端测试怎样证明报表排序、历史恢复和发布产物正确？

**案例背景。** 用户打开 `/reports?sort=recent#summary`，看到 May、April。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端返回该顺序；点击 **Oldest first** 后，地址变成 `sort=oldest`，列表为 April、May；按 Back 则回到 recent 和 May、April。测试要验证用户看到的结果、真实地址历史和请求边界；点击事件触发过或内部状态等于某值，都不足以证明整条流程可用。

~~~mermaid
flowchart LR
    A[纯函数与契约] --> B[组件交互和异步状态]
    B --> C[真实浏览器路由与 Back]
    C --> D[生产构建资源]
    D --> E[发布同一份已验证产物]
~~~

### 先按风险选择测试边界

| 测试边界 | 适合验证 | 报表排序例子 |
|---|---|---|
| 单元测试 | 无 Document Object Model（文档对象模型，DOM）的纯转换与解析 | 无效 `sort` 被拒绝；报表响应字段映射正确。 |
| 组件集成测试 | 组件、Hook（钩子）、可访问控件和请求边界一起工作 | 点排序控件后显示等待状态，成功后行序变为 April、May，失败时出现错误提示。 |
| 浏览器端到端测试 | 浏览器历史、真实 URL、路由、资源和服务组合 | 从 recent 点 Oldest first，确认 URL 和行序，再按 Back 恢复 recent。 |

保持单元测试简单纯粹；请求和 React 组件的关系用组件测试；浏览器 Back、片段锚点、生产资源路径等风险由真实浏览器覆盖。组件测试不模拟出真实浏览器历史时，不能替代 Back 测试。

### 用用户能找到的名称和内容断言

React Testing Library 的查询名称表达等待契约：`getByRole` 表示元素现在应存在且唯一；`queryByRole` 适合断言它不存在；`findByRole` 返回 Promise 并等待元素出现。优先使用角色和可访问名称，避免检查组件内部状态、CSS class 或 hook 调用次数。

组件集成测试可以用 `user-event` 的用户操作模拟器执行点击和键盘交互；异步数据出现时等待可见行或状态，而不是固定睡眠。`waitFor` 的回调必须在未满足时抛出断言错误，返回 `false` 不会要求它重试；也不要把点击等副作用放进会重跑的回调。完整异步 Mock 与计时例子见[Jest 怎样验证报表请求中的异步状态和结果？](#67.%20Jest%20%E6%80%8E%E6%A0%B7%E9%AA%8C%E8%AF%81%E6%8A%A5%E8%A1%A8%E8%AF%B7%E6%B1%82%E4%B8%AD%E7%9A%84%E5%BC%82%E6%AD%A5%E7%8A%B6%E6%80%81%E5%92%8C%E7%BB%93%E6%9E%9C%EF%BC%9F)。

React Testing Library 16.3.3 也从 `@testing-library/react` 导出 `renderHook`，可单独验证有复用价值的 Hook 契约；只被一个组件使用的 Hook 通常直接测那个组件更能表达用户行为。Testing Library 的 render 和 user-event helper 已处理一般交互的 React `act` 边界；测试从 helper 外部直接触发更新时，再显式包在 `act` 中。快照适合记录稳定的小结构，较大的快照本身说不清用户需要看到什么，排序和错误行为仍应使用有含义的断言。

### 浏览器测试应经过同一条 URL 和 Back 流程

下面的端到端测试是 React Router Data Mode 浏览器 loader 加同源 `/api/reports` 的方案。它假定 Playwright 配置了应用 `baseURL` 与启动待测应用的 `webServer`。`page.route` 只拦截浏览器页面发出的请求；Next Server Component 在服务器进程发出的上游 `fetch` 不会经过它，要为 Next 配置可达的服务端测试上游。此处在浏览器 API 边界按 `sort` 返回固定数据，断言链接、地址、列表和浏览器历史；拦截器中的断言只检查实际出现的请求，URL 和行序断言验证界面行为；它们不证明每次导航一定发生网络调用。若还要证明应用确实接入接口，可增加至少一次拦截命中的断言，或用不会出现在初始静态页面中的 fixture 值。这里不固定请求次数，因为预取、路由再验证或返回历史项可能影响网络调用次数：

~~~ts
import { expect, test } from "@playwright/test";

const recentRows = [
  { id: "may", period: "May", title: "Operations" },
  { id: "april", period: "April", title: "Finance" }
];
const oldestRows = [...recentRows].reverse();

test("sorts reports and restores the previous URL with Back", async ({ page }) => {
  await page.route(/\/api\/reports(?:\?.*)?$/, async route => {
    expect(route.request().method()).toBe("GET");
    const url = new URL(route.request().url());
    const sorts = url.searchParams.getAll("sort");
    expect(sorts).toHaveLength(1);
    const sort = sorts[0];
    expect(["recent", "oldest"]).toContain(sort);
    const rows = sort === "oldest" ? oldestRows : recentRows;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(rows)
    });
  });

  await page.goto("/reports?sort=recent#summary");
  const rows = page.getByRole("list", { name: "报表" }).getByRole("listitem");
  await expect(rows).toHaveText([
    "May — Operations",
    "April — Finance"
  ]);

  await page.getByRole("link", { name: "Oldest first" }).click();
  await expect(page).toHaveURL(/\/reports\?sort=oldest#summary$/);
  await expect(rows).toHaveText([
    "April — Finance",
    "May — Operations"
  ]);

  await page.goBack();
  await expect(page).toHaveURL(/\/reports\?sort=recent#summary$/);
  await expect(rows).toHaveText([
    "May — Operations",
    "April — Finance"
  ]);
});
~~~

这类测试把 `#summary` 留在页面地址，并让 API 只按查询参数读取排序；浏览器不会把片段发给服务端。URL 断言只证明片段仍在地址栏，不证明页面滚动到了 `id="summary"` 的位置；若页面确有滚动契约，应单独断言锚点与视口位置。DOM 角色查询也只证明可访问树中的结构和名称，不证明屏幕阅读器实际播报。测试应用可以把 `page.route` 换成测试服务或 Mock Service Worker（请求拦截工具），但不要在同一案例里一边 Mock 页面实现、一边又声称覆盖了真实路由。

### 验证将发布的构建产物

开发热更新服务主要验证开发链路，不会完整覆盖打包后的资源地址、分块加载或部署路径。常用交付检查顺序是：

~~~text
typecheck -> unit/component tests -> production build
  -> serve that build -> critical browser journey -> promote the same artifact
~~~

用接近生产的服务器启动刚生成的构建产物，再执行一次上面的关键用户流程；使用 Vite 时，`vite preview` 可以本地预览刚构建的 `dist`，但官方不把它定位为生产服务器。发布时晋级同一份通过检查的产物，避免重新构建后部署了另一份代码。Source map（源码映射）应绑定发布版本并受控上传；隐藏注释不会自动阻止外部直接访问 map 文件。公共的构建产物晋级、运行时和发布门禁见[应用部署与持续集成及持续交付（CI/CD）](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)，通用测试边界见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)。

> [!info]- 来源与版本核验（React Testing Library 16.3.3；user-event 14.6.8；Playwright 1.65.0；2026-11-06）
> - React Testing Library 当前包版本：[npm package](https://www.npmjs.com/package/@testing-library/react)，16.3.3；角色查询和异步行为：[ByRole](https://testing-library.com/docs/queries/byrole/)、[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)。
> - `renderHook` API 与测试单个 Hook 的适用边界：[React Testing Library API](https://testing-library.com/docs/react-testing-library/api/#renderhook)，v16.3.3，核验日期 2026-11-06。
> - user-event 当前版本：[npm package](https://www.npmjs.com/package/@testing-library/user-event)，14.6.8；用户交互模型：[Introduction](https://testing-library.com/docs/user-event/intro/)，核验日期 2026-11-06。
> - Playwright 当前包版本：[npm package](https://www.npmjs.com/package/@playwright/test)，1.65.0；浏览器端断言与拦截请求：[Assertions](https://playwright.dev/docs/test-assertions)、[Page route](https://playwright.dev/docs/api/class-page#page-route)，核验日期 2026-11-06。
> - 测试产物服务器配置：[Playwright webServer](https://playwright.dev/docs/test-webserver)。
> - `vite preview` 用于本地预览构建产物，不是生产服务器：[Vite CLI](https://vite.dev/guide/cli.html#vite-preview)、[Static deployment](https://vite.dev/guide/static-deploy.html)，按 Vite v8.3.5 官方文档核验于 2026-11-06。
## 67. Jest 怎样验证报表请求中的异步状态和结果？

**案例背景。** 报表页从 recent 的 May、April 开始；用户点 **Oldest first** 后，页面应显示等待状态，读取完成再展示 April、May。生产路由还要确认 `sort` 写进 URL 并能按 Back 恢复；这里的 Jest 组件测试只隔离点击、定时 Mock（模拟）和可见列表，不声称模拟了真实浏览器历史，完整 Back 流程见[前端测试怎样证明报表排序、历史恢复和发布产物正确？](#66.%20%E5%89%8D%E7%AB%AF%E6%B5%8B%E8%AF%95%E6%80%8E%E6%A0%B7%E8%AF%81%E6%98%8E%E6%8A%A5%E8%A1%A8%E6%8E%92%E5%BA%8F%E3%80%81%E5%8E%86%E5%8F%B2%E6%81%A2%E5%A4%8D%E5%92%8C%E5%8F%91%E5%B8%83%E4%BA%A7%E7%89%A9%E6%AD%A3%E7%A1%AE%EF%BC%9F)。

### 测试必须等待承载断言的异步工作

在 Promise 风格的 Jest 测试里，框架会等待测试返回或 `await` 的 Promise；另一种受支持的异步方式是 `done` 回调，不要在同一个测试中混用两种完成协议。若启动请求却不等待，测试可能在断言执行前就结束。`rejects` / `resolves` 自身也会返回 Promise，必须 `return` 或 `await`；不能把同步 `toThrow` 用在已经执行过的调用结果上。

### 用用户操作和假时钟控制请求返回

下例用 300 ms 定时器模拟报表服务。运行 TSX 前要配置 `jsdom` 环境及 TypeScript/JSX transformer；测试全局从 `@jest/globals` 显式导入。Fake timers（假时钟）让测试控制响应时机：先点击控件、确认等待状态和旧列表还在，再只推进所需时间，最后检查新行序。这个小组件仅用于隔离请求状态；真正的 sort URL 与 Back 由浏览器测试覆盖：

~~~tsx
import { useState } from "react";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/jest-globals";
import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type LoadReports = (sort: SortOrder) => Promise<Report[]>;

const recentRows: Report[] = [
  { id: "may", period: "May", title: "Operations" },
  { id: "april", period: "April", title: "Finance" }
];
const oldestRows = [...recentRows].reverse();

function ReportPanel({ loadReports }: { loadReports: LoadReports }) {
  const [rows, setRows] = useState(recentRows);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function showOldest() {
    setLoading(true);
    setError(false);
    try {
      setRows(await loadReports("oldest"));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <button type="button" disabled={loading} onClick={() => void showOldest()}>
        Oldest first
      </button>
      {loading && <p role="status">正在读取 oldest 排序…</p>}
      {error && <p role="alert">报表读取失败。</p>}
      <ol aria-label="报表" aria-busy={loading}>
        {rows.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

test("keeps the visible rows pending, then shows the oldest order", async () => {
  const loadReports = jest.fn<LoadReports>(
    sort =>
      new Promise(resolve => {
        setTimeout(
          () => resolve(sort === "oldest" ? oldestRows : recentRows),
          300
        );
      })
  );
  const user = userEvent.setup({
    advanceTimers: jest.advanceTimersByTime
  });

  render(<ReportPanel loadReports={loadReports} />);
  await user.click(screen.getByRole("button", { name: "Oldest first" }));

  expect(loadReports).toHaveBeenCalledWith("oldest");
  expect(screen.getByRole("status")).toBeInTheDocument();
  const list = screen.getByRole("list", { name: "报表" });
  expect(within(list).getAllByRole("listitem").map(row => row.textContent))
    .toEqual(["May — Operations", "April — Finance"]);

  await act(async () => {
    await jest.advanceTimersByTimeAsync(300);
  });

  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(within(list).getAllByRole("listitem").map(row => row.textContent))
    .toEqual(["April — Finance", "May — Operations"]);
});
~~~

`user-event` 在输入或点击过程中也会安排定时任务；启用 Jest 假时钟时，把 `jest.advanceTimersByTime` 传给 `userEvent.setup`。不要用 `delay: null` 绕过假计时器。对只需立即完成的服务 Mock 可用 `mockResolvedValue`；需要验证防抖或加载延迟时，让 Mock Promise 用明确的定时器解决，并调用 `advanceTimersByTimeAsync`。异步定时器 API 会让 Promise 回调有机会执行，旧式 fake timers 不支持它。

此处推进 300 ms 会让定时器调用 Mock Promise 的 `resolve`；`act` 再等 React 把 `setRows` 和 `setLoading(false)` 提交到 DOM，之后同步查询才观察得到 April、May 和消失的等待提示。按钮在 `loading` 时禁用，因此本例定义的是一次只处理一个请求；若产品允许连续切换或重试，要另测并发返回次序和过期结果保护。

当目标元素本来就不存在且需要异步出现时，`findByRole` 返回等待 Promise；如果整条断言需要重试，用 `waitFor`，其回调应在未满足时抛错。固定等待 1 秒既慢又不说明等的是什么。组件请求失败的测试应再用 `mockRejectedValue` 并确认用户能找到 `role="alert"`，不要只断言 Mock 曾经被调用。

### Mock 要停在真实依赖边界

`jest.fn` 可记录参数、调用和 Promise 结果；例如 `mock.results[0].value` 是 Mock 返回的 Promise 对象，不是它之后兑现的报表数组。组件例最后断言的是 Promise 结算后用户实际看到的行序。`jest.spyOn(object, method)` 默认仍会执行原实现，需调用 `mockReturnValue` / `mockImplementation` 才替换，并在测试后用 `mockRestore` 恢复。普通函数 Mock（模拟函数）应断言业务代码如何处理 May、April，不要只复述自己设置了什么结果。

在 Babel 或其他转换为 CommonJS（通用模块系统）的配置中，`jest.mock` 可能由 transformer（代码转换器）提升到导入前。原生 ECMAScript Module（ECMAScript 模块，ESM）的静态导入先执行，Mock 必须在动态导入被测模块前登记：

~~~javascript
import { jest } from "@jest/globals";

jest.unstable_mockModule("./report-api.js", () => ({
  fetchReports: jest.fn()
}));

const { reportsLoader } = await import("./reports-loader.js");
~~~

`reports-loader.js` 应在模块中导入 `./report-api.js` 的 `fetchReports`；测试先登记该依赖的 Mock，再动态导入真正使用它的 loader。`unstable_mockModule` 仍带 unstable 前缀，模块 ESM Mock 方式要和项目的 Jest 版本、Node 运行时以及 transformer 配置一致。Jest 30.5.2 对 Node 24.9+ 同步可求值的 ESM 图也有 automock 和手写 Mock 支持；包含顶层 await 或异步 resolver（模块解析器）/ transformer 的图仍要按当前 ESM 文档选方法。

### 断言要匹配数据结构和观察方式

| 断言 | 适合检查 |
|---|---|
| `toBe(value)` | 原始值或引用相同，使用 `Object.is` 语义。 |
| `toEqual(value)` | 数组和对象的递归值。 |
| `toStrictEqual(value)` | 还要区分缺失属性、`undefined` 属性等结构差异。 |
| `toHaveBeenCalledWith(args)` | Mock 在实际调用边界收到的参数。 |
| `toThrow(error)` | 同步抛错；传入函数本身，而非已经执行的结果。 |

Mock 清理方法不会互相替代：

| 方法 | 清除什么 | 保留什么 |
|---|---|---|
| `jest.clearAllMocks()` | 调用、实例与结果记录 | Mock 的实现与返回值设置 |
| `jest.resetAllMocks()` | 调用记录和 Mock 实现 | spy 仍被替换；需要另行恢复原属性 |
| `jest.restoreAllMocks()` | `spyOn` / 替换属性保存的原实现 | 独立创建或手动赋值的 `jest.fn()` 不会自动还原 |

`beforeAll` / `afterAll` 可为整组测试打开和关闭共享资源；`beforeEach` / `afterEach` 负责逐测试建立和恢复假时钟、spy 与 DOM；不要让一个用例的调用记录或待处理计时器泄漏到另一个用例。Jest 的 `--coverage` 报告哪些分支执行过，不代表断言已验证了用户要的 May/April 顺序、错误恢复或历史行为。

> [!info]- 来源与版本核验（Jest 30.5.2；React Testing Library 16.3.3；user-event 14.6.8；2026-11-06）
> - 当前包版本及发行记录：[Jest v30.5.2 release](https://github.com/jestjs/jest/releases/tag/v30.5.2)，2026-09-18。
> - 定时器 Mock、推进时钟以及异步 timer API：[Timer Mocks](https://jestjs.io/docs/timer-mocks)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5.2，核验日期 2026-11-06。
> - 函数 Mock、spy 和 ESM 模块 Mock：[Mock Functions](https://jestjs.io/docs/mock-functions)、[ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules)，Jest 30.5.2，核验日期 2026-11-06。
> - 假时钟下的用户操作、异步查询和重试断言：[user-event setup options](https://testing-library.com/docs/user-event/options/)、[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)，核验日期 2026-11-06。
