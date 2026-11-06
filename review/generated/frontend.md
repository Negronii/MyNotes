# Frontend

> Generated from the [frontend reading map](../../frontend/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. 浏览器如何把 URL 变成第一帧？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，需要看到最近报表；随后点击“最早优先”，期望列表更新。先沿初次导航走到可见页面，再从同一页跟进点击。

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

图的两条分支分别跟踪“画面可见”和“处理器可用”。解析期间，CSS、模块脚本、图片获取与后续 HTML 解析可以交叠推进；不必等所有资源都到齐才有首帧。模块图获取完成只表示依赖资源已就绪；普通模块还要等 HTML 解析结束，并满足脚本阻塞样式表状态，才开始求值。图片若晚到，可以填入预留空间而不必挪动已有内容。图是帮助跟踪这条报表路线的模型，不是每个引擎都必须遵循的逐步流水线。浏览器负责导航、资源协调与画面呈现，JavaScript engine（JavaScript 引擎，如 V8、JavaScriptCore 或 SpiderMonkey）负责执行脚本；各自的进程和线程边界属于实现选择。

### 先确定浏览器要打开什么

地址栏文本先被判定为搜索词还是 URL；这里已给出 URL，因此例子从跨文档导航开始。路径 `/reports` 和查询 `sort=recent` 会参与请求；片段 `#summary` 留在浏览器端，不会随 HTTP 请求发给服务器。匹配范围的 Service Worker（服务工作线程）或可用缓存可能直接提供响应；若走网络，缓存也可能需要验证。对本例的 HTTPS URL，协议、主机和端口共同确定 origin（源）；有匹配的活动连接时浏览器可以复用，需要新建连接且没有可用主机地址时才查询 Domain Name System（域名系统，DNS）。Transport Layer Security（传输层安全协议，TLS）可保护传输；HTTP/2 常运行在 TCP/TLS 上，HTTP/3 使用 QUIC。浏览器随后发送带 `/reports?sort=recent` 的请求并收到响应头和响应体，再将响应体按到达情况交给新 `Document` 的 HTML parser。协议协商、重定向、缓存与连接复用等细节见[HTTP、DNS 与连接建立](../../engineering-foundations/networking/http-protocols-and-websockets.md)。

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

浏览器不必等完整响应下载完才开始解析；随着标记到达，HTML parser 建立 DOM，并发现样式表、模块脚本和图片等资源。浏览器通常能并行获取独立资源，也可能用实现特有的预扫描提前发现资源。适用于当前媒体环境的外部样式表可能阻止首次显示；没有 `async` 或 `defer` 的解析器插入经典脚本会阻塞 HTML 解析。这里的普通模块脚本会并行获取，等解析完成、模块依赖图就绪且阻塞脚本的样式表条件满足后运行。具体脚本依赖关系见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)。

DOM 表示文档节点，CSS 规则决定这些节点如何呈现。浏览器按需计算样式和布局：例如标题文字的换行取决于字体和可用宽度，图片的宽高属性则让图片数据到达前也能先分配画面空间。后到的字体仍可能改变文字宽度或换行。渲染引擎（如 Blink、WebKit、Gecko）据此准备绘制结果，再把内容转换为像素并组合成待显示画面；JavaScript 引擎（如 V8、JavaScriptCore、SpiderMonkey）负责执行脚本。Blink/Chromium 的 RenderingNG 是一种实现实例，不是所有浏览器的强制结构。

### 从首帧交接到筛选更新

首帧可能先于 `load` 事件和客户端代码可交互的时点出现。比如 HTML 已显示报表，但模块脚本尚未完成下载、运行或注册点击处理器。若报表由 React 服务端输出，hydration（客户端水合）还要在已有 DOM 上运行客户端代码并接入组件行为，见[Next.js 中的 hydration 与流式渲染](#How%20do%20hydration%20and%20streaming%20fit%20together?%20/%20Hydration%20%E4%B8%8E%E6%B5%81%E5%BC%8F%E6%B8%B2%E6%9F%93%E5%A6%82%E4%BD%95%E8%A1%94%E6%8E%A5%EF%BC%9F)。若点击没有反馈，先确认处理器何时可用；若处理器已经注册，则查看事件是否被主线程上其他工作挡住。

当用户点击“最早优先”，`/reports.js` 的 DOM 事件处理器可以把 `sort=oldest` 写入 URL，设置按钮的 `aria-pressed` 状态，并改动列表节点。节点修改立即改变 DOM；样式、布局、绘制和之后的画面呈现则由浏览器在后续工作中按需完成。异步处理器与画面更新之间的关系见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)，点击如何到达处理器见[DOM 事件如何传播，何时适合事件委托？](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F)，更新后可能需要的布局和绘制见[为什么一次 DOM 改动会增加布局或绘制工作？](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

| 现象 | 优先检查的阶段 |
|---|---|
| 首个 HTML 字节迟迟不到 | 重定向、缓存命中、连接建立、服务端响应和网络瀑布 |
| HTML 已到，主要内容仍迟 | 关键 CSS/脚本的阻塞关系、LCP 资源发现与渲染时机 |
| 页面可见，筛选点击迟迟没有反馈 | 点击前主线程工作、处理器运行时间、处理后的渲染工作 |
| 内容出现后位置跳动 | 图片或字体的尺寸和到达时机、后插入内容及布局偏移记录 |

先沿测得的依赖关系定位，再决定要改请求、脚本、布局还是绘制。相同的“首屏慢”现象可能来自服务器响应、资源发现或内容渲染，单独改 CSS 选择器无法同时解释这些原因。见[如何测量并诊断网页性能问题？](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - URL 片段及导航后文档状态： [WHATWG HTML：导航与会话历史](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，持续更新规范，导航、同文档导航与历史遍历章节；[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，请求 URL 处理章节。核对日期：2026-11-06。
> - HTTPS origin、DNS 与本例网络协议： [WHATWG URL Standard：Origin](https://url.spec.whatwg.org/#origin)；[RFC 1034：DNS concepts and facilities](https://www.rfc-editor.org/rfc/rfc1034)、[RFC 1035：DNS implementation and specification](https://www.rfc-editor.org/rfc/rfc1035)；[RFC 8446：TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)；[RFC 9113：HTTP/2](https://www.rfc-editor.org/rfc/rfc9113)、[RFC 9000：QUIC](https://www.rfc-editor.org/rfc/rfc9000) 与 [RFC 9114：HTTP/3](https://www.rfc-editor.org/rfc/rfc9114)。核对日期：2026-11-06。
> - HTML 解析和浏览器渲染在 Chromium 中的一种实现： [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)，架构概览。核对日期：2026-11-06。
> - 浏览器渲染引擎名称： [Blink](https://www.chromium.org/blink/)，Chromium rendering engine；[WebKit](https://webkit.org/)，WebKit browser engine；[Gecko](https://firefox-source-docs.mozilla.org/overview/gecko.html)，Firefox rendering engine。JavaScript 引擎名称： [V8](https://v8.dev/)、[JavaScriptCore](https://docs.webkit.org/Deep%20Dive/JSC/JavaScriptCore.html)、[SpiderMonkey](https://firefox-source-docs.mozilla.org/js/)。核对日期：2026-11-06。
## 2. 每次 URL 变化都会加载新文档吗？

案例背景：用户先打开 `https://example.test/reports?sort=recent#summary`，随后点“最早优先”并可能按浏览器后退。要让这三个时点显示正确的报表，先判断浏览器是在换文档、跳转片段，还是只更新当前文档的历史地址。

### 先解析 URL，再选导航操作

用 `URL` 解析地址，避免自己按 `?`、`&` 或 `#` 切字符串。`searchParams.get()` 读取一个值，`getAll()` 读取同名多值，`set()` 替换该名字的值，`append()` 则有意保留并追加一个值；对象序列化时会处理 URL 编码。查询参数来自地址栏或外部链接，必须按业务允许值校验，也不要把口令或访问令牌放进 URL。

| 需要的行为 | API / 行为 | 是否获取新文档 |
|---|---|---|
| 打开另一个地址并留下新历史项 | 点击 `<a>` 或 `location.assign(url)` | 通常换 `Document`；目标只是片段时可留在当前 `Document` |
| 打开地址并替换当前历史项 | `location.replace(url)` | 替换当前历史项；目标是否换 `Document` 仍取决于导航目标 |
| 当前文档新增一项路由状态 | `history.pushState(state, "", sameOriginUrl)` | 否 |
| 修改当前历史项的路由状态 | `history.replaceState(state, "", sameOriginUrl)` | 否 |

History API 的目标 URL 必须符合当前文档可改写 URL 的规则；对本例的 HTTPS 页面，可以改路径、查询和片段，但不能改协议、主机或端口。`pushState()` 和 `replaceState()` 都不会发起该地址的网络请求，也不会因为调用本身派发 `popstate` 或 `hashchange`。应用若要显示与新 URL 对应的内容，仍须自己同步界面；目标是别的服务器资源时，应正常导航或显式发出请求。

### 让筛选状态跟随地址栏与前进后退

报表页面初始地址是 `/reports?sort=recent#summary`。这次服务器返回的 HTML 已包含 `h1#summary`、两个筛选按钮以及 May、April 两行；普通模块脚本由首帧示例头部的 `<script type="module" src="/reports.js"></script>` 引用。用户点击“最早优先”后，模块将查询参数改成 `sort=oldest`，并把已在客户端的数据按日期升序排进列表。若数据由服务器提供，更新 URL 后还需按该状态请求新结果，并处理加载、错误和过期响应。

~~~html
<!-- /reports?sort=recent 的服务端 HTML 初始状态 -->
<h1 id="summary">Recent reports</h1>
<img src="/report-summary.png" width="320" height="180" alt="Report summary">
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
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

`renderReports()` 先按 URL 状态选顺序，再同步两个按钮的 `aria-pressed`，最后用 `replaceChildren()` 写入行。初始服务器 HTML 已显示 May → April；用户点“最早优先”后，新地址是 `/reports?sort=oldest#summary`，按钮切成 pressed，行变为 April → May。若用户分享一条 `sort=oldest` 深链，`reports.js` 的初次运行会按 URL 修正列表；要让首批 HTML 本身就显示正确顺序，服务器也应按查询参数生成行和按钮状态。

`pushState()` 只记录 URL；点击处理器主动调用 `renderReports()`，本例也不把应用状态重复存进 `history.state`。其他应用若把额外恢复信息放在 `state` 参数里，可以在 `popstate` 的 `event.state` 读取；本例将 URL 当作排序状态的唯一来源。接着用户在这两条共享同一个 `Document` 的历史项之间后退或前进时，浏览器派发 `popstate`，同一个仍在的监听器从当前 `location` 读回排序并恢复按钮与列表。再后退离开这个文档时，当前监听器并不接管另一文档的恢复或重新加载；浏览器处理的是另一条历史项及其页面状态。

通过地址栏、链接或 `location` 改变片段会执行片段导航，可让浏览器滚到 `#summary` 并建立历史项；这是浏览器导航行为，不需要应用重画列表。脚本调用 History API 改成另一个片段则不会自动滚动，也不会因为调用本身派发 `hashchange`；遍历相应历史项时，`popstate` 可能与片段变化事件共同出现。客户端路由器可以复用这些历史项，但 URL 变化与视图绘制是两项不同工作。

浏览器首次收到 `.../reports?sort=recent#summary` 时，`#summary` 是浏览器用来定位的片段，服务器只处理路径与查询。筛选点击改成 `sort=oldest` 后，仍是同一个 `Document`：浏览器不重新解析 `/reports`，应用继续负责产生新列表节点。这个边界让地址可复制、可返回，同时不把 History API 误解成网络导航。

**延伸：** [DOM 事件如何传播，何时适合事件委托？](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F)解释点击处理器如何收到按钮事件；React 中 URL 与客户端导航如何映射到视图，见[React 路由如何把 URL 映射到视图？](#61.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F)，组件状态更新见[React 如何把用户操作变成更新后的界面？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)。

> [!info]- 来源
> - URL 查询参数的解析与序列化： [WHATWG URL Standard：URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，持续更新规范，URLSearchParams 接口章节。核对日期：2026-11-06。
> - 片段导航、同文档导航、会话历史遍历、`pushState()`、`popstate` 与 `hashchange`： [WHATWG HTML：导航与会话历史](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，持续更新规范，navigation、History interface 与事件章节。核对日期：2026-11-06。
## 3. 脚本如何影响 HTML 解析与文档就绪？

案例背景：报表服务器已返回标题、筛选按钮和初始行，浏览器还在解析 HTML，并同时获取 `/reports.css` 与 `/reports.js`。用户要尽快看到内容，之后点击按钮时脚本也必须已经注册处理器。下面按脚本下载、执行、文档就绪的先后关系判断哪些工作会挡住哪一步。

### 不同脚本属性怎样改变解析顺序？

表格说的是 HTML parser（HTML 解析器）插入的脚本；动态插入的脚本有不同默认调度，不能把它们混为一谈。

| 脚本形式 | 下载与解析的关系 | 运行时机与顺序 |
|---|---|---|
| 外部经典脚本，不带 `async` / `defer` | parser 遇到时开始获取并暂停继续解析 | 资源可运行后在 parser 继续前执行，保持文档顺序 |
| 外部经典脚本 `defer` | 与解析并行获取 | 解析完成后、`DOMContentLoaded` 前执行；多个 defer 脚本按文档顺序 |
| 外部经典脚本 `async` | 与解析并行获取 | 下载就绪后尽快执行；若解析还在进行，会暂时打断解析；不保证多个 async 脚本的顺序 |
| 普通模块脚本 | 模块及依赖图与解析并行获取 | 默认延后到解析完成后执行，遵循模块依赖关系 |
| `async` 模块脚本 | 模块及依赖图与解析并行获取 | 模块图就绪后尽快执行，不保证相对其他异步脚本的顺序 |
| 内联经典脚本，有无 `defer` | 没有外部文件要获取 | parser 到达该元素且没有待等的阻塞样式表时执行；没有 `src` 时 `defer` 不起延后作用 |

`defer` 适合依赖已解析文档、且需要保持外部经典脚本文档顺序的代码。`async` 适合执行不依赖解析结果或其他脚本的独立工作。模块脚本默认延后执行，给模块加 `async` 会改变这个选择。

### 为什么解析器有时必须停下来？

解析 HTML 就像按顺序读取标记并逐个建立节点。经典脚本能在节点还没建完时查询、修改文档，甚至用 `document.write()` 改变后续解析结果；浏览器不能一概把这种脚本当作与文档无关的文件而继续前进。因此，脚本获取可以和其他资源获取重叠，但脚本执行本身可能成为解析的依赖点。

样式表对脚本的影响不是浏览器先分析某段 JavaScript 是否调用了 `getComputedStyle()`。HTML 定义了一个脚本阻塞样式表状态：样式表元素由 parser 创建时已启用、参与样式规则、媒体条件匹配且尚未加载完成，才会进入该文档的阻塞集合。后续要执行的同步 parser 脚本或延后脚本，会按这个集合判断是否等待；即便 `/reports.js` 只给按钮注册事件，也可能先等 `/reports.css`。

适用于当前媒体环境的外部样式表通常会阻止首次绘制。不是“所有 CSS 必须全部下载后才能开始任何绘制”，而是当前渲染和脚本执行各自要满足规范定义的样式依赖。

沿用报表页的 HTML：

~~~html
<head>
  <link rel="stylesheet" href="/reports.css">
  <script type="module" src="/reports.js"></script>
</head>
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

这段沿用首帧章的完整报表结构：服务器先输出 May → April 的行，`#summary` 是片段目标；外部模块 `/reports.js` 在 parser 完成后运行。

| 此刻的资源状态 | parser 与首帧 | 筛选处理器与就绪事件 |
|---|---|---|
| HTML 主体和 `/reports.css` 已就绪，模块图仍在下载，图片还未到 | parser 已建出标题、按钮和两行；样式可用时浏览器可在渲染机会绘出首帧；图片宽高让空位先保留 | `reports.js` 尚未运行，按钮还没有处理器，`DOMContentLoaded` 尚未触发 |
| `/reports.css` 仍是当前 parser 创建的阻塞样式表，模块图已就绪 | parser 仍可继续解析普通模块脚本后的 HTML；若当前样式表阻止渲染，首帧会等到样式依赖解除 | 普通模块仍要等解析结束、模块图就绪且文档没有阻塞脚本的样式表；脚本之后才能注册处理器，随后才排入 `DOMContentLoaded` |

在表格第一行的状态下，本页可以先显示标题与预渲染行；用户如果过早点击，页面还可能没有 listener。待模块图与阻塞样式表条件满足，`/reports.js` 运行并注册处理器。若图片较晚到，预留的宽高减少它到达后挤动文字的机会。

### `DOMContentLoaded` 和 `load` 分别说明什么？

`DOMContentLoaded` 在文档解析完成、parser 的延后脚本队列处理流程之后触发；普通 `defer` 脚本和没有异步模块依赖、且模块本身没有顶层 `await` 的模块代码会在此流程同步运行，因此可在事件前注册处理器。若模块使用顶层 `await`、依赖异步模块，或只启动一个异步请求并把后续工作放进 Promise 回调，应用的后续初始化可以晚于 `DOMContentLoaded`；因此这个事件不代表所有异步初始化已完成。它不等图片或 `async` 脚本完成。因为延后脚本可能等待脚本阻塞样式表，所以样式表也可能间接推迟这个事件。

`load` 要等文档中所有仍会延迟该事件的资源；普通图片、样式表、脚本和子框架可能在其中，懒加载资源通常不必挡住它。具体资源是否延迟 load 由 HTML 的加载算法定义。两种事件都不是“首帧已出现”或“按钮已可用”的指标。

两种事件都不能回答“用户什么时候第一次看到主要内容”或“筛选按钮现在是否可用”。首帧可以早于 `load`，而报表内容也可能已显示、模块脚本还没注册筛选处理器。反过来，`DOMContentLoaded` 触发后，一次长脚本任务仍会让点击处理器排队等待。可见时点和就绪事件的区别见[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)；用户侧的加载与交互数据见[如何测量并诊断网页性能问题？](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - 解析器插入的经典脚本、`async`、`defer` 与模块调度： [WHATWG HTML：脚本元素](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)，持续更新规范，脚本准备与执行算法章节。核对日期：2026-11-06。
> - 阻塞脚本样式表的判定状态： [WHATWG HTML：样式与脚本交互](https://html.spec.whatwg.org/multipage/semantics.html#has-a-style-sheet-that-is-blocking-scripts)，持续更新规范，media 匹配、启用与加载状态条件。核对日期：2026-11-06。
> - 延后脚本、模块脚本到 `DOMContentLoaded` / `load` 的顺序： [WHATWG HTML：解析结束](https://html.spec.whatwg.org/multipage/parsing.html#the-end)与[HTML 中调用脚本](https://html.spec.whatwg.org/multipage/webappapis.html#calling-scripts)，持续更新规范，解析结束、延后脚本队列和模块求值步骤。核对日期：2026-11-06。
## 4. DOM 事件如何传播，何时适合事件委托？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary` 后，页面显示 May、April 两行和“最早优先”按钮。点击按钮要把 `oldest` 这个筛选意图交给应用，由应用更新地址和列表。按钮里面还可能有图标或文字节点；事件委托必须从真实事件目标找到所属按钮，并确认它属于这个工具栏。

### 一次点击沿哪些节点传播？

浏览器为事件确定传播路径后，监听器可以沿路径经历三个阶段：捕获阶段从外层祖先走向目标；目标阶段运行目标上的监听器；若事件的 `bubbles` 为真，冒泡阶段再从目标向祖先返回。不是所有事件都会冒泡，所以委托前要确认事件类型的传播约定。

~~~javascript
const button = document.querySelector('#sort-controls button[data-sort="oldest"]');
const label = button.querySelector("span");

document.body.addEventListener("click", () => console.log("body bubble"));
document.body.addEventListener("click", () => console.log("body capture"), { capture: true });
label.addEventListener("click", () => console.log("label target"));
button.addEventListener("click", () => console.log("button bubble"));

// 点击 span：body capture → span target → button bubble → body bubble
~~~

`event.target` 是最初的事件目标；`event.currentTarget` 是当前正在运行监听器的对象。若按钮里还有 `<svg>` 或 `<span>`，`target` 可能是它们；处理器应先找到最近的筛选按钮。Shadow DOM（影子 DOM）边界外的监听器可能看到被重定向的 `target`；事件的 `bubbles` 与 `composed` 标记影响事件能否穿过相应边界。

### 什么时候用父级监听器处理子控件？

事件委托让一个父级监听器处理多个后代控件，包括稍后插入的控件，因此不用逐一注册监听器。它适合事件会冒泡、父级确实拥有这些控件、目标匹配规则清楚的场景；它不会消除每次事件分发或处理器本身的计算。

~~~html
<h1 id="summary">Recent reports</h1>
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
</div>
<ol id="reports"><li data-id="may">May report</li><li data-id="april">April report</li></ol>
~~~

~~~javascript
const controls = document.querySelector("#sort-controls");

controls.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-sort]");
  if (!button || !controls.contains(button)) return;

  const sortIntent = button.dataset.sort;
  console.log("Sort requested:", sortIntent); // 点击“最早优先”时得到 "oldest"
});
~~~

点击 `span` 或 `svg` 时，`closest()` 会从该后代向上找到带 `data-sort` 的按钮；`controls.contains(button)` 确认匹配结果没有越出工具栏。事件处理器交出的值是按钮声明的 `recent` 或 `oldest`；点击“最早优先”时输出 `oldest`。应用据此把查询参数写回 URL、切换按钮的 `aria-pressed`，并将列表行改成 April → May；这条状态转换见[每次 URL 变化都会加载新文档吗？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)。如果事件处理器要移除匹配元素再循环，先选择静态快照或合适的实时集合，避免移除节点改变下一次索引；见[如何选择 DOM 集合？](#53.%20What%20is%20the%20difference%20between%20an%20HTMLCollection%20and%20a%20NodeList?%20/%20HTMLCollection%20%E4%B8%8E%20NodeList%20%E6%9C%89%E4%BB%80%E4%B9%88%E5%8C%BA%E5%88%AB%EF%BC%9F)。

### 默认动作与传播控制是两回事

按钮若位于表单中，点击可能触发表单提交；这是与事件传播分开的默认动作。`preventDefault()` 只在事件可取消且监听器不是 passive 时取消默认动作，它不会停止冒泡。`stopPropagation()` 阻止事件继续传到路径上后续对象；`stopImmediatePropagation()` 还会阻止当前对象上后续监听器运行。

如果滚动或触控监听器不需要取消浏览器默认滚动，设置 `{ passive: true }` 能表明这一点；passive 监听器调用 `preventDefault()` 无法取消默认动作。DOM 标准规定，未显式设置 `passive` 的 `touchstart`、`touchmove`、`wheel` 和 `mousewheel` 监听器，在 `Window`、`Document`、`documentElement` 或 `body` 上默认 passive 为 true；确实需要拦截时，应先按事件的 `cancelable` 状态判断，再显式设置 `{ passive: false }`。

### 移动端点击与手势策略

历史上的移动端 click 延迟有特定条件：部分浏览器曾等待判断一次触摸是否还会成为双击缩放手势。它不是今天所有浏览器、所有 viewport 或所有输入模式下的固定延迟。先设置符合设备宽度的 viewport；不要为了绕开历史延迟而禁止用户缩放。

~~~html
<meta name="viewport" content="width=device-width, initial-scale=1">
~~~

若某个控件不需要双击缩放，但仍应允许平移和双指缩放，可以对该控件使用 Pointer Events 的 `touch-action: manipulation`：

~~~css
#sort-controls button[data-sort] {
  touch-action: manipulation;
}
~~~

它让浏览器保留平移和连续缩放，同时不把双击缩放作为该元素上的手势。把规则限制在确实需要的控件，不要用 `touch-action: none` 全局封锁操作。原生 `<button>` 自带键盘激活；自制的 `role="button"` 还必须补足键盘行为。Chrome 的 viewport 诊断指出一个特定条件：初始视口未针对移动设备优化时，点击可能延后至多 300 毫秒；其他浏览器和输入设置会不同，不能把这个值当成所有移动端点击的固定时延。除非目标设备实测仍有兼容问题，不要同时在 touch-end 和 click 上触发同一动作，以免合成 click 与原生 click 重复执行。

### 把浏览器事件交给 React 时，交接什么？

若同一报表页由 React 管理，浏览器仍然派发 click；React 的 `onClick` handler 因这次点击触发，并把筛选意图 `oldest` 传给状态更新。事件处理器可从目标元素读取该值，也可由按钮各自的闭包传入。浏览器这一侧的输入是已发生的事件、当前 URL `sort=recent` 和当前 DOM；交给下一章的应用意图是“筛选变为 `oldest`”。React 章节从这个输入继续，讲 state 快照、组件重算和 commit 后需要的 DOM 变化。见[React 如何把用户操作变成更新后的界面？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)。React 管理的节点应由 React state 描述；若另用 DOM API 直接改它们，下一次 React commit 可能覆盖这些修改。

React 的 JSX 事件名和事件对象保留常用的 DOM 事件概念，`onClick` 默认冒泡、`onClickCapture` 对应捕获。事件委托的具体根节点属于 React 实现细节：React 17 将委托根从 `document` 移到了 React root container；早期 React DOM 还会池化 SyntheticEvent，React 17 起移除了池化，所以当前 React DOM 不需要为异步读取事件调用 `persist()`。React Native 的事件行为另有边界。

**延伸：**[浏览器如何把 URL 变成第一帧？](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)交代该页面的首帧和筛选入口；[每次 URL 变化都会加载新文档吗？](#2.%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F)展示同一点击如何更新历史地址和列表；[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)说明 click 处理器如何等待主线程并交接到渲染机会；[跨浏览上下文如何通信？](#56.%20How%20do%20browser%20contexts%20communicate?%20/%20%E6%B5%8F%E8%A7%88%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B9%8B%E9%97%B4%E5%A6%82%E4%BD%95%E9%80%9A%E4%BF%A1%EF%BC%9F)讲跨文档消息；[JavaScript 事件总线怎样处理重入？](#54.%20How%20can%20a%20JavaScript%20event%20bus%20handle%20reentrancy?%20/%20JavaScript%20%E4%BA%8B%E4%BB%B6%E6%80%BB%E7%BA%BF%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E9%87%8D%E5%85%A5%EF%BC%9F)讨论应用层发布/订阅。

> [!info]- 来源
> - 捕获、目标、冒泡、事件目标、默认动作及取消： [WHATWG DOM：事件分发](https://dom.spec.whatwg.org/#concept-event-dispatch)，Living Standard，事件分发算法；[WHATWG DOM：Event 接口](https://dom.spec.whatwg.org/#interface-event)，事件标记与取消行为。核对日期：2026-11-06。
> - `touch-action` 的手势边界： [Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property)，W3C Recommendation，`manipulation` 值与直接操控行为章节。核对日期：2026-11-06。
> - passive 默认值与取消行为： [WHATWG DOM：事件监听器](https://dom.spec.whatwg.org/#dom-addeventlistener)，Living Standard，passive 监听器与阻止默认动作章节。核对日期：2026-11-06。
> - React 事件处理器与事件阶段： [React：Responding to Events](https://react.dev/learn/responding-to-events)；React 17 将委托根移到 root container：[React 17：Changes to Event Delegation](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#changes-to-event-delegation)；React 17 移除事件池：[React 17：No Event Pooling](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#no-event-pooling)。核对日期：2026-11-06。
> - 移动端 viewport 诊断的适用条件： [Chrome Performance Insights：Optimize viewport for mobile](https://developer.chrome.com/docs/performance/insights/viewport)，Chrome DevTools 指标说明。核对日期：2026-11-06。
## 5. 浏览器 JavaScript 何时运行，画面何时更新？

案例背景：报表页已经显示 `sort=recent` 的行，`/reports.js` 也已注册 click 处理器，用户点击“最早优先”。如果浏览器正忙，处理器什么时候能运行？处理器改完 URL 和 DOM 后，用户又要等到什么时候才能看到新顺序？沿一次点击走完这两个时间边界。

> [!info] 任务和微任务
> **task（任务）**是宿主安排的工作单元，例如用户输入、计时器回调或网络事件处理。一个 task 中的同步 JavaScript 不会被另一个普通 task 插入执行。**microtask（微任务）**用于当前工作结束后的短小延续，例如 Promise reaction（Promise 处理器）；微任务检查点会清空队列，包括在运行中新增的微任务。ECMAScript 定义 Promise 的语言行为，浏览器宿主定义它们怎样接入事件循环。

~~~mermaid
flowchart TD
    A[执行包含 click 的 task（任务）] --> B[同步处理器运行到返回]
    B --> C[完成 microtask（微任务）检查点]
    C -->|仍有微任务| C
    C --> D[事件循环选择下一项可运行任务]
    D --> E{选中的是渲染更新任务?}
    E -->|是| F[运行该次渲染更新的 requestAnimationFrame 回调]
    F --> G[按需执行样式、布局等渲染步骤]
    G --> C
    E -->|否| H[运行所选任务]
    H --> C
~~~

渲染机会会使用户代理把更新任务排入单独的 rendering task source（渲染任务源）；事件循环随后从可运行任务中选择下一项，选择策略不意味着每个 click 后同步检查一次渲染。图只表示一次交互后可能经过的顺序，不保证每轮都绘制；浏览器也会因刷新率、页面可见性和资源状况推迟或跳过画面更新。

图把这次 click 中 `/reports.js` 的业务处理器简化成一个同步段；真实事件分发还可能调用其他监听器，它们不在这条示例时序里。

### 微任务的先后顺序与让出的边界

~~~javascript
console.log("start");
setTimeout(() => console.log("timer task"), 0);
Promise.resolve().then(() => console.log("Promise reaction"));
queueMicrotask(() => console.log("queued microtask"));
console.log("end");
~~~

当前同步脚本先输出 `start`、`end`。脚本返回时排队的 Promise reaction 和 `queueMicrotask()` 回调按入队顺序在微任务检查点执行；计时器回调是后续 task，只有达到计时器允许执行的时点后才有资格运行。`setTimeout(fn, 0)` 不表示立刻切走，也不承诺下一个画面会先出现。若当前处理器很长，用户点击会等它完成才开始处理；若处理器不断追加微任务，检查点会持续排空队列，浏览器也就迟迟不能处理后续任务或渲染。

`new Promise(executor)` 中的 `executor` 在构造时同步运行；由 `.then()` 注册的 reaction 才排入微任务。上面的例子使用 `Promise.resolve().then()`，所以 `Promise reaction` 出现在同步输出之后。Promise 的语言行为见[异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

在报表页的例子里，点击发生时可能正有脚本任务占用主线程，这会增加输入延迟。处理器开始后，`pushState()` 和节点修改是同步的；处理器结束后，微任务仍可能继续安排工作，浏览器再看是否有机会更新报表画面。`await Promise.resolve()` 或把工作切成一串微任务并不会主动让浏览器绘制。若计算确实太重，应把有界工作切到后续 task、Web Worker 或适合的框架调度策略；需要确认是哪段时间占用主线程时，沿 [INP 的交互阶段](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)看录制结果。

### `requestAnimationFrame` 把写入对齐到渲染更新

若动画或视觉写入需要按渲染更新同步，使用 `requestAnimationFrame(callback)`。回调会在该次渲染更新的常规样式与布局步骤之前运行，参数提供可用于时间计算的高精度时间戳。调用率取决于可用的渲染机会和页面状态；刷新率、后台限速都会影响它，所以它不是固定的 60 Hz 计时器。把变换属性的写入放入 rAF 可以让写入时机与画面同步，但不会让计算免费，也不保证浏览器只做合成工作。DOM/样式写入后读取几何值仍可能触发同步布局，详见[为什么一次 DOM 改动会增加布局或绘制工作？](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

### `requestIdleCallback` 只安排可推迟的小块工作

`requestIdleCallback(callback, { timeout })` 允许用户代理在空闲时段安排低优先级工作。`deadline.timeRemaining()` 是对剩余空闲时间的估计，不是硬性运行预算；每轮处理一个有界单元，剩余工作再排队。即使设置 `timeout`，回调被延迟到超时后也不应因此一次清空无界队列。该 API 并非所有浏览器都支持，需按目标环境检测；用 `setTimeout()` 代替时只能保证之后有一次计时器机会，不能保证当时空闲。

~~~javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift()); // 每次工作仍须有界
  }
  if (workQueue.length) requestIdleCallback(runIdleSlice, { timeout: 2000 });
}

requestIdleCallback(runIdleSlice, { timeout: 2000 });
~~~

React 等框架的 scheduler 是建立在宿主机制上的另一套排程策略，不是浏览器 HTML 规范中的 task source。使用分片调度也不能假定每两个代码块之间浏览器一定会绘制。

**延伸：** [脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F)说明解析阶段的脚本调度；[DOM 事件如何传播，何时适合事件委托？](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F)说明 click 处理器如何接收事件；[JavaScript 异步](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F)解释 Promise 本身的语言行为。Node 有不同的宿主调度边界，见[Node 运行时与调度](../../engineering-foundations/backend/node-event-loop-and-microtasks.md)。

> [!info]- 来源
> - 浏览器任务、微任务检查点、渲染机会和动画帧回调： [WHATWG HTML：Web 应用 API 与事件循环](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)，持续更新规范，事件循环、微任务与更新渲染章节。核对日期：2026-11-06。
> - 空闲回调和 `IdleDeadline`： [W3C `requestIdleCallback()`](https://www.w3.org/TR/requestidlecallback/)，Working Draft，2025-05-21，接口与处理算法章节；[Chrome `requestIdleCallback` guide](https://developer.chrome.com/blog/using-requestidlecallback)，使用建议。核对日期：2026-11-06。
> - Promise 构造器执行器的同步调用： [ECMAScript：Promise 构造器](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-promise-executor)，Living Standard，执行器调用算法。核对日期：2026-11-06。
## 6. React如何把一次用户操作变成界面更新？

**案例背景。** 浏览器主线已经把 `/reports?sort=recent#summary` 的点击交给 React 处理器。`#summary` 是浏览器定位片段，不会随 HTTP 请求发给服务端；服务端依据 `sort=recent` 返回 May、April。本章从 React 处理器继续：用户点击 **Oldest first**，排序状态请求变为 `oldest`，完整应用以 `pushState` 记录新筛选项，可见行在下一次提交时先变成 April、May；随后 Effect（副作用同步）请求对应服务端数据，只有仍有效的 Effect 响应才能确认新结果。按浏览器后退时，路由从 URL 恢复 `recent`，列表回到 May、April；这段 React 示例省略 URL/history 集成，细节见[筛选状态与前进后退](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。React 负责从 state（状态）推导下一份界面描述，并提交 commit（提交）的 DOM（文档对象模型）变化；浏览器样式、布局和绘制接回[浏览器渲染主线](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F)。

~~~mermaid
flowchart TD
    A[点击 Oldest first] --> B[处理器请求 sort=oldest]
    B --> C[下一次 render（渲染）读到 oldest]
    C --> D[按稳定 key（键）对应报表行]
    D --> E[提交必要 DOM 变化]
    E --> F[Effect 请求当前排序]
    F --> G{该 Effect 仍有效？}
    G -- 是（ignore=false） --> H[保存服务端结果并再次 render]
    G -- 否（已 cleanup） --> I[忽略过期响应]
    E --> J[浏览器后续处理样式与像素]
~~~

### 处理器读到的是本次界面的状态快照

state（状态）不在组件函数的局部变量里被原地改写。React 每次调用组件时给它一份当前快照；事件处理器也属于那次 render（渲染）。调用 setter（状态更新函数）会排入下一次状态更新，因此同一处理器里的 `sort` 仍然是 `recent`。

报表用 `periodStart` 保存 `YYYY-MM-DD` 排序值，`period` 只作为 May、April 这样的显示标签；不能按月份单词的字母顺序推断日期先后。

~~~tsx
import { useEffect, useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; periodStart: string; title: string };

declare function fetchReports(sort: SortOrder): Promise<Report[]>;

const initialReports: Report[] = [
  { id: "may", period: "May", periodStart: "2026-05-01", title: "May summary" },
  { id: "april", period: "April", periodStart: "2026-04-01", title: "April summary" }
];
// 路由把 URL 的 sort=recent 和这份服务端响应交给 ReportsPage。

function sortReports(reports: Report[], sort: SortOrder) {
  // 复制数组，避免对 state 持有的数组原地 sort。
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function ReportsPage({
  initialSort,
  initialReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
}) {
  const [sort, setSort] = useState(initialSort);
  const [requestId, setRequestId] = useState(0);
  const [reports, setReports] = useState(initialReports);
  const [status, setStatus] = useState<"confirmed" | "pending" | "error">("confirmed");

  function chooseSort(nextSort: SortOrder) {
    if (nextSort === sort) return;
    setSort(nextSort);
    setRequestId(id => id + 1);
    setStatus("pending");
  }

  useEffect(() => {
    if (requestId === 0) return;

    let ignore = false;
    fetchReports(sort).then(
      nextReports => {
        if (!ignore) {
          setReports(nextReports);
          setStatus("confirmed");
        }
      },
      () => {
        if (!ignore) setStatus("error");
      }
    );

    return () => {
      ignore = true;
    };
  }, [sort, requestId]);

  const visibleReports = sortReports(reports, sort);

  return (
    <section>
      <button type="button" onClick={() => chooseSort("oldest")}>
        Oldest first
      </button>
      <p aria-live="polite">
        {status === "pending" ? "正在确认服务端结果" :
         status === "error" ? "确认失败；仍显示本地已有报表" :
         `当前排序：${sort}`}
      </p>
      <ul>
        {visibleReports.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ul>
    </section>
  );
}

function ReportsRoute() {
  return <ReportsPage initialSort="recent" initialReports={initialReports} />;
}
~~~

这段代码把同一次操作拆成两个可见结果：`setSort("oldest")` 请求一次新 render，下一次提交就可见本地 April、May 顺序，不必等网络；Effect 的结果再替换数据并改变确认状态。完整应用应由路由把排序写入一条新历史项，并在 `popstate` 时把当前 URL 恢复到 React 状态；本例聚焦更新轮次，省略这层集成。不要用替换当前历史项的写法代替新筛选历史项，否则用户无法按 Back 返回 `recent`。手写 Effect 只演示提交后的同步和旧结果防护。

`requestId` 初始为 `0`，让首屏沿用服务器已经给出的 May、April，并跳过 `recent` 请求；它也作为 Effect 的依赖之一，但响应回调不会比较这个编号。旧请求失效的门槛是对应 Effect 已运行 cleanup：cleanup 把自己的 `ignore` 设为 `true`，后续 Promise 即使返回也不会写 state。这个清理不会取消网络请求；当完整路由、另一排序控件或浏览器后退让排序再次变化时，新一轮 Effect 会清理旧闭包并请求当前值。请求失败时，界面保留已有数据并把失败显示出来，而不是把本地排序误称为服务端已确认。

### 渲染、协调与提交是不同工作

render 阶段调用组件，得到当前状态对应的 JSX 元素描述。渲染应保持纯净，因为 React 可能重试或放弃尚未提交的工作；不要在组件函数里改 DOM、写 URL、发请求或直接调用 setter。若下一状态依赖前一状态，用 updater（更新函数）让排队更新逐个读取队列中的值：

~~~jsx
setCount(count + 1);
setCount(count + 1);
~~~

如果这两次 setter 在同一个处理器中运行，都会从当前 render 的 `count` 快照计算，所以只加一。若下一次更新要基于队列中刚排入的值，使用 updater：

~~~jsx
setCount(value => value + 1);
setCount(value => value + 1);
~~~

React 18 的 `createRoot` 把自动批处理扩展到 Promise、定时器和原生事件回调，因此这里一个 Promise 成功回调中的 `setReports` 与 `setStatus` 会作为同一批更新处理；旧 `ReactDOM.render` 根的自动批处理范围较窄。

reconciliation（协调）用树位置、元素类型和同级 key 将前后两次描述对应起来。上例的 `report.id` 是稳定身份；排序变动时，React 可以把既有行对应到新位置。若用数组索引作 key，插入或重排后行内输入状态可能跟着位置而不是报表走。key 只需在同级列表中唯一。

commit 阶段才把已完成结果写到宿主树。render 调用组件不等于每次都会改 DOM；若行顺序变化，React 只提交所需宿主改动。之后浏览器是否布局、绘制以及何时呈现到帧上，由浏览器渲染阶段决定，不与每个 setter 一一对应。

> [!example] JSX描述界面，不是HTML字符串
> JSX 是 JavaScript 中描述元素的语法。构建配置可将它转换为自动 JSX runtime 的 `react/jsx-runtime` 调用，也可使用经典的 `React.createElement` 形式；转换方式不会改变上面的 state、render 和 commit 关系。

### Effect在提交后同步外部系统

Effect 用于让已提交的组件与 React 之外的系统保持一致，例如订阅事件、连接服务或发送请求。依赖变化后的顺序是：先用旧值执行 cleanup，再用新值 setup；卸载时执行最后一次 cleanup。Effect 在 commit 后运行，但 React 不保证它总在浏览器 paint 之后运行；具体帧边界仍由[浏览器主线](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)说明。没有外部系统要同步时，派生排序数组应直接在 render 里算，不要为了它再加一个 Effect 和 state。

开发环境在根组件开启 StrictMode（严格模式）时，React 可在首挂载额外执行一次 setup 与 cleanup 来暴露不完整的清理逻辑。此例首轮 Effect 因 `requestId === 0` 直接返回，不会因此发出重复请求；这项检查不代表生产中每个请求都会重复。手写 Effect 获取数据时要清理或忽略已经失效的响应；若要缓存、去重、刷新和更新服务端数据，接着读[React如何维护服务端数据与乐观更新？](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)。

类组件的 `render` 同样要纯净；`getSnapshotBeforeUpdate` 在 DOM 变更前读取快照，`componentDidMount`、`componentDidUpdate` 和 `componentWillUnmount` 过去常承接外部同步与清理。函数组件 Effect 有自己的 setup/cleanup 生命周期，不能把每个类方法简单替换成同名 Hook。渲染失败的恢复由[React错误边界章节](#10.%20React%E9%94%99%E8%AF%AF%E8%BE%B9%E7%95%8C%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E5%A4%B1%E8%B4%A5%EF%BC%9F)负责；路由和 SPA/MPA 的完整边界见[React路由如何把 URL 映射到视图？](#61.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F)。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 状态是快照、setter 请求下一次 render、updater 按队列应用：React 官方 [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)，核验日期 2026-11-06。
> - React 18 `createRoot` 将自动批处理扩展到 Promise、定时器和原生事件回调：[React 18 — Automatic Batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)，React 团队，2022-03-29。
> - render/commit 以及状态保留由类型、位置和 key 决定：[Render and Commit](https://react.dev/learn/render-and-commit)、[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 19.3 文档。
> - Effect 在 commit 后 setup、依赖改变时先 cleanup 再 setup、StrictMode 根边界的开发检查及过期 fetch 响应处理：[useEffect](https://react.dev/reference/react/useEffect)、[StrictMode](https://react.dev/reference/react/StrictMode#enabling-strict-mode-for-a-part-of-the-app)、[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3 文档。
> - 自动/经典 JSX runtime 的转换边界：[Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform)，React 团队，2020-09-22。
> - URL 修改当前历史项的标准语义：[HTML Standard, History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，核验日期 2026-11-06。
> - URI 片段只在客户端用于定位，不属于发给服务端的请求：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
## 7. 如何在React中组合组件与复用行为？

**案例背景。** 报表页的浏览器地址为 `/reports?sort=recent#summary`；服务端按 `sort=recent` 返回 May、April，`#summary` 只供浏览器定位。选择 **Oldest first** 后，排序状态变成 `oldest`，可见顺序应为 April、May。这个排序状态要同时驱动工具栏的选中状态和列表顺序，因此由包含二者的最近共同父组件持有；列表只拿已排序的报表数组，工具栏收到更新回调。沿 props（属性）、Context（上下文）、自定义 Hook（自定义钩子）、ref（引用）逐层选择能表达清楚所有权的边界，不把组件组合变成隐式的全局通信。

本章片段只展示组件之间的 state 归属，不实现 URL 与历史栈；完整应用用[浏览器主线的 `pushState` 与 `popstate` 路径](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)新增筛选历史并在后退时恢复排序。

### 把状态放在共同使用者之上的最近一层

排序按 ISO 日期字段 `periodStart` 进行，显示标签 `period` 不参与排序；最近共同父组件持有排序状态，并把它传给工具栏和列表。

~~~tsx
import { useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; periodStart: string; title: string };

function sortReports(reports: Report[], sort: SortOrder) {
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function ReportsPage({ reports, initialSort }: { reports: Report[]; initialSort: SortOrder }) {
  const [sort, setSort] = useState(initialSort);
  const rows = sortReports(reports, sort);

  return (
    <main>
      <ReportToolbar sort={sort} onSortChange={setSort} />
      <ReportList reports={rows} />
    </main>
  );
}

function ReportToolbar({
  sort,
  onSortChange
}: {
  sort: SortOrder;
  onSortChange: (sort: SortOrder) => void;
}) {
  return (
    <div role="group" aria-label="报表排序">
      <button
        type="button"
        aria-pressed={sort === "recent"}
        onClick={() => onSortChange("recent")}
      >
        Most recent
      </button>
      <button
        type="button"
        aria-pressed={sort === "oldest"}
        onClick={() => onSortChange("oldest")}
      >
        Oldest first
      </button>
    </div>
  );
}

function ReportList({ reports }: { reports: Report[] }) {
  return (
    <ul>
      {reports.map(report => (
        <li key={report.id}>{report.period} — {report.title}</li>
      ))}
    </ul>
  );
}
~~~

数据沿 props（属性）向下传，用户意图用 callback prop（回调属性）向上交给状态所有者。这个结构让一次点击的去向可见。若两个组件不共享状态，把 state（状态）提到更高层只会扩大更新范围；若多个远距离组件确实要读取主题、地区设置等值，可以在共同子树上用 Context；跨多个功能共享且需要统一更新策略时，再考虑 store（共享状态容器）。

服务端拥有的报表记录仍属于服务端状态。把它们放进 Context 不会自动提供查询身份、缓存新鲜度、取消或变更协调；这些由[服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)讲解。

### 用自定义Hook复用状态行为

自定义 Hook 把同一种有状态行为封装起来，但每次调用默认有各自的 state。下面的 Hook 让多个组件共享“监听窗口大小”这一行为，而不会让它们共享同一份 `size`：

~~~jsx
import { useEffect, useState } from "react";

function useWindowSize() {
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

每个 Hook（钩子）调用都注册自己的监听器；如果想共享一份外部 store，应明确连接同一 store。Effect（副作用同步）的 setup、cleanup 和过期请求处理见[更新轮次](#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)。Hook 通常在组件或其他 Hook 顶层以固定顺序调用。React 的 `use` API 例外：可在条件和循环中读取 Promise 或 Context，但仍须处于组件或 Hook 中，且不能放进 `try/catch`。

React 19.2 增加的 `useEffectEvent` 用于 Effect 内部的事件式逻辑：它读取调用时最新提交的值，却不让这些值重新触发连接。它只可在本组件的 Effect 或其他 Effect Event 中调用，不应传给子组件、用作普通事件回调，或借此隐藏本来应该声明的依赖。

### ref用于窄范围的命令式能力

state 改变后要更新界面就用 state；ref 则持有不驱动界面的可变值，或访问已经提交的 DOM。下面父工具栏只能调用搜索框公开的 `focus()`，实际输入节点仍由子组件持有：

~~~jsx
import { useImperativeHandle, useRef } from "react";

function ReportSearchInput({ ref }) {
  const inputRef = useRef(null);
  useImperativeHandle(ref, () => ({
    focus() {
      inputRef.current?.focus();
    }
  }), []);
  return <input ref={inputRef} aria-label="搜索报表" />;
}

function ReportFocusControl() {
  const searchRef = useRef(null);
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

React 19 的函数组件可以把 `ref`（引用）当作 prop 接收；React 18 及更早版本的组件需要 `forwardRef` 转发。若父组件只需要 `focus()`，可用 `useImperativeHandle` 暴露这个有限动作，而不把内部节点和实现一起交出去。选 API 时保留子组件的资源所有权。

### 组合组件与旧式逻辑复用接口

children 组合可让调用方控制布局；render prop（渲染属性）把数据交给一个函数，由调用方选择渲染结构；higher-order component（高阶组件，HOC）则包装组件并返回新组件。自定义 Hook 往往适合复用 Hook 状态逻辑，但旧库的 render prop 或 HOC 也可能是明确、稳定的 API，不必只为“改成 Hook”而重写。

条件分支也属于组合的一部分：二选一用三元表达式，只在条件为真时渲染用逻辑 AND，能早退时用 `if`。由于 `0 && <List />` 的结果是数字 `0`，若空数组长度可能为零，应写成 `{items.length > 0 && <List />}`。

这些模式解决状态归属和行为复用。若一次交互的 React render 成本已经测出，再看[如何测量并减少不必要的React工作？](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)；本章不把 memoization（记忆化）当作组件组合规则。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - props、共享 state 与 Context 的所有权：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component)、[Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)、[Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)，React 19.3 文档。
> - 自定义 Hook 与 Hook 调用边界：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)、[Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)、[`use`](https://react.dev/reference/react/use)，React 19.3 文档。
> - React 19.2 的 Effect Event 语义与限制：[useEffectEvent](https://react.dev/reference/react/useEffectEvent)，React 官方 API 参考；React 19.2 发布日期 2025-10-01，见[React Blog](https://react.dev/blog)。
> - ref、forwardRef 与受限命令式接口：[useRef](https://react.dev/reference/react/useRef)、[forwardRef](https://react.dev/reference/react/forwardRef)、[useImperativeHandle](https://react.dev/reference/react/useImperativeHandle)，React 19.3 文档。
> - toggle button 的 `aria-pressed` 状态：[WAI-ARIA APG — Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)，W3C WAI 官方模式，核验日期 2026-11-06。
## 8. 如何让报表筛选在昂贵更新时保持响应？

**案例背景。** 报表页当前 URL 为 `/reports?sort=recent#summary`，服务端给出 May、April；选择 **Oldest first** 后，`sort=oldest` 让行顺序变成 April、May。随后输入标题筛选时，输入值要即时显示；若结果视图渲染很重，可以让它稍后跟进。React 提供的是更新优先级和可中断的后台 render（渲染），不是把 JavaScript 移到另一个线程，也不是按固定时间延迟请求。状态快照在[React更新轮次](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)说明；服务端查询身份仍由[服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)负责。URL 与 Back 的同步采用[浏览器历史栈机制](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)，本章代码省略这层连接。

### 输入保持即时，结果视图可以延后

下面把标题筛选输入作为紧急更新，并把搜索词交给 `useDeferredValue`。昂贵过滤放进结果子组件；示例假设该子树的构建结果确实能在 props（属性）不变时跳过重渲染。仅启用 React Compiler（React 编译器）不保证它覆盖了这个子树，需检查实际编译结果；否则输入更新仍可能让结果子组件立即重算。边界的选择和检查见[React渲染优化章节](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)。`isStale` 表示结果还对应上一个查询词，所以界面可以保留旧结果同时标出正在更新：

~~~jsx
import { useDeferredValue, useState } from "react";

function ReportFilter({ reports }) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <section aria-busy={isStale}>
      <label>
        搜索报表
        <input value={query} onChange={event => setQuery(event.target.value)} />
      </label>
      {isStale && <p>结果仍对应上一个搜索词，正在更新。</p>}
      <ReportResults reports={reports} query={deferredQuery} />
    </section>
  );
}

function ReportResults({ reports, query }) {
  const visibleReports = reports.filter(report =>
    report.title.toLowerCase().includes(query.toLowerCase())
  );
  return <ul>{visibleReports.map(report => <li key={report.id}>{report.title}</li>)}</ul>;
}
~~~

输入从空字符串变为 `"apr"` 时，紧急更新先显示 `apr`；若 deferred 值仍为空，列表暂时保留 April、May，`isStale` 显示结果仍旧。随后当 deferred 值成为 `"apr"` 并提交时，列表只剩 April。`useDeferredValue` 不设定毫秒延迟，也不保证某个结果会跳过；React 可中断尚未提交的组件工作，但不能抢占已经开始运行的同步 `reports.filter(...)`。如果全量过滤本身是长任务，优先减少计算量、分块或放到 Web Worker（网页工作线程）；如果耗时来自大量行组件的渲染，延后子树更新才有帮助。它也不是 debounce（防抖），不承诺减少请求数；请求频率要由明确的产品策略或服务端查询层管理。

### 用Transition标记非紧急的界面切换

打开报表摘要或切换大视图通常不需要阻塞输入。`useTransition` 可把这类 Transition（过渡更新）标记为非紧急，并通过 `isPending` 暴露仍在准备的状态。它不能控制受控文本输入；如果 Transition render 执行一次同步 `reports.filter(...)`，React 也不能在这个函数运行中途抢占 JavaScript。

~~~jsx
import { Suspense, lazy, useState, useTransition } from "react";

const ReportSummary = lazy(() => import("./ReportSummary.js"));

function ReportWorkspace({ reports }) {
  const [view, setView] = useState("rows");
  const [isPending, startTransition] = useTransition();

  function openSummary() {
    startTransition(() => setView("summary"));
  }

  return (
    <main>
      <button type="button" onClick={openSummary}>查看摘要</button>
      {isPending && <span>正在准备摘要视图…</span>}
      <Suspense fallback={<p>正在加载摘要模块…</p>}>
        {view === "summary"
          ? <ReportSummary reports={reports} />
          : <ul>{reports.map(report => <li key={report.id}>{report.title}</li>)}</ul>}
      </Suspense>
    </main>
  );
}
~~~

Suspense（挂起边界）仅在子树通过受支持的方式暂停时显示最近边界的 fallback（备用界面）；上例由 `lazy` 加载摘要模块。点击前列表已显示；点击后视图状态在 Transition 中更新，若模块仍在加载，实际画面是查看摘要按钮、`isPending` 等待文案和旧的 April、May 列表。模块加载成功后才提交摘要。这个交互不会直接显示“正在加载摘要模块”的 fallback；若首次加载时边界里尚无已显示内容，或非 Transition 更新导致内容被隐藏，fallback 才承担等待画面。读缓存 Promise 的 `use`、服务端组件或明确支持 Suspense 的框架也可触发它。TanStack Query v5 的 `useSuspenseQuery` 是专门的挂起查询入口；普通 `useQuery` 的 pending 状态默认不会触发 Suspense，把普通 `fetch` 放在 `useEffect` 中也不会自动挂起。异步查询的错误和重试不能只靠 loading fallback 处理。

React 19 的 Transition 支持异步 Action（动作）。当前文档仍指出：跨 `await` 后的 state 更新若要继续保持 Transition 优先级，需要再包一层 `startTransition`；自定义异步动作若可能乱序完成，仍需显式管理结果顺序。React 19.3 下这些状态优先级规则不改变服务端数据的一致性契约。

如果长同步计算本身仍占住主线程，先检查算法和工作量；必要时移到 Web Worker（网页工作线程）。若成本来自屏幕上挂载了太多报表行，转到[长列表何时适合虚拟滚动？](#14.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 延后值不等于 debounce，后台 render 可中断：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)，React 19.3 文档。
> - Transition 的优先级、`isPending`、异步 Action 与 `await` 后再包 state 更新：[useTransition](https://react.dev/reference/react/useTransition)，React 19.3 文档；核验日期 2026-11-06。
> - 支持 Suspense 的触发条件、最近边界和 fallback：[Suspense](https://react.dev/reference/react/Suspense)、[lazy](https://react.dev/reference/react/lazy)、[`use`](https://react.dev/reference/react/use)，React 19.3 文档。
> - TanStack Query v5 专用挂起查询：[Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[`useSuspenseQuery`](https://tanstack.com/query/latest/docs/framework/react/reference/useSuspenseQuery)，v5.90.3。
> - Compiler 是否覆盖指定组件的检查：[React Compiler Debugging](https://react.dev/learn/react-compiler/debugging)，React 19.3 文档。
> - React 文档当前版本及本章 API 适用版本：[Versions](https://react.dev/versions)，最新文档标为 19.3，核验日期 2026-11-06。
## 9. React界面如何维护服务端数据与乐观更新的正确性？

**案例背景。** 报表页初始地址是 `/reports?sort=recent#summary`。浏览器只把路径和查询参数 `/reports?sort=recent` 发给服务端；`#summary` 是客户端定位片段。服务端给出 May、April 两行。用户选择 **Oldest first** 后，URL 中的 `sort` 变为 `oldest`，可见顺序先变成 April、May，再由当前查询结果确认。完整应用用[浏览器主线的 `pushState` 与 `popstate` 路径](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)记录筛选历史并在 Back 时恢复 `recent`；本章的查询示例省略 URL/history 集成。排序偏好是界面/路由状态，报表记录由服务端拥有；query cache（查询缓存）只是客户端对服务端结果的副本。要避免把旧排序结果误当成新结果，查询身份必须包含影响返回数据的筛选条件。

### 排序值构成查询身份

以下示例使用 TanStack Query v5.90.3。`queryKey` 的排序项不同，代表两份不同的查询结果；`queryFn` 使用同一次 render 闭包中的 `sort` 发请求，这个值也构成 key。首次由路由加载的报表只作为 `initialSort` 对应查询的初始数据，不会被误塞进另一种排序的缓存项。

~~~tsx
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

type SortOrder = "recent" | "oldest";
type Report = {
  id: string;
  period: string;
  periodStart: string;
  title: string;
  reviewed: boolean;
};

const reportKeys = {
  lists: () => ["reports", "list"] as const,
  list: (sort: SortOrder) => ["reports", "list", sort] as const
};

declare function fetchReports(sort: SortOrder, signal: AbortSignal): Promise<Report[]>;

function sortReports(reports: Report[], sort: SortOrder) {
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function useReports(sort: SortOrder, initialSort: SortOrder, initialReports: Report[]) {
  return useQuery({
    queryKey: reportKeys.list(sort),
    queryFn: ({ signal }) => fetchReports(sort, signal),
    initialData: sort === initialSort ? initialReports : undefined,
    staleTime: 30_000
  });
}

function ReportsPage({
  initialSort,
  initialReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
}) {
  const [sort, setSort] = useState(initialSort);
  const query = useReports(sort, initialSort, initialReports);
  const visibleReports = query.data ?? sortReports(initialReports, sort);

  function chooseSort(next: SortOrder) {
    setSort(next);
  }

  return (
    <section aria-busy={query.isFetching}>
      <button type="button" onClick={() => chooseSort("oldest")}>
        Oldest first
      </button>
      {query.isPending && <p>列表已按 {sort} 本地排序，正在等待服务端确认…</p>}
      {query.isFetching && !query.isPending && <p>正在更新当前排序…</p>}
      {query.isError && (
        <div>
          <p role="alert">
            {query.data === undefined
              ? "服务端确认失败；仍显示本地已有报表。"
              : "更新失败；仍显示上次取得的结果。"}
          </p>
          <button type="button" onClick={() => query.refetch()}>
            重试服务端确认
          </button>
        </div>
      )}
      <ul>{visibleReports.map(report => <li key={report.id}>{report.period} — {report.title}</li>)}</ul>
    </section>
  );
}
~~~

切换到 `oldest` 后，查询 key 改变；若这个 key 还没有缓存，`visibleReports` 暂时用路由交来的 May、April 在本地按 `periodStart` 排成 April、May，并显示“正在等待服务端确认”。这只在同一份完整记录集合里改变排序时成立；若筛选条件改变成员集合或数据是分页子集，就不能把另一结果集重新排序来冒充当前结果。响应到达后，列表改用当前 query 的结果；首次请求失败时仍保留本地行和排序控件，提示错误并提供 `query.refetch()` 重试。旧 `recent` 请求若仍成功完成，也只能填充 `recent` 对应缓存，不会变成 `oldest` 的行；若 query function 消费取消信号，旧读取还可能被取消。若用户以前查询过 `oldest`，缓存中已有数据时可以先显示它，再根据新鲜度策略重新取数。若使用 `placeholderData` 保留旧排序行，界面也要标出它仍对应旧 key，不能把它说成已确认的新排序。代码中的 `setSort` 只演示排序状态如何切换查询 key；完整路由还要用 `pushState` 新增 `sort=oldest` 历史项，并在 `popstate` 时恢复 URL 对应的查询状态，不能把 `replaceState` 当成等价操作。

`staleTime: 30_000` 表示这份缓存 30 秒内按客户端策略视为 fresh；它不承诺服务端数据在这段时间不变，也不是数据库一致性保证。需要强制校准时，对受影响的 key 做失效。`#summary` 不会随 HTTP 请求发送，也不会决定服务端数据；只有客户端明确把片段值映射成请求参数时，那个映射后的参数才进入 query key。

### 变更先乐观显示，再与服务端协调

以下变更示例接在上面的查询流程之后：先切换到 `oldest`，等服务端成功返回，使 `reports/list/oldest` 缓存里已有真实报表行；再点击 April 行的 **Mark reviewed**。调用端用 `{ id: "april", reviewed: true, sort: "oldest" }` 调用这个 mutation。只有当前排序 key 已有已确认的 `query.data` 时才启用该操作；切换排序期间展示的本地临时行只用于保持列表，不提供可变更数据。此时 oldest 缓存先把 April 从未读改为已读；保存成功后用服务端响应替换它并失效相关列表，失败时回滚为未读。

~~~tsx
type MarkReviewed = {
  id: string;
  reviewed: boolean;
  sort: SortOrder;
};

declare function saveReviewed(id: string, reviewed: boolean): Promise<Report>;

function useMarkReviewed() {
  return useMutation({
    mutationFn: ({ id, reviewed }: MarkReviewed) => saveReviewed(id, reviewed),
    onMutate: async (change: MarkReviewed, context) => {
      const key = reportKeys.list(change.sort);
      await context.client.cancelQueries({ queryKey: key });
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
    },
    onSettled: (_data, _error, _change, _snapshot, context) =>
      context.client.invalidateQueries({ queryKey: reportKeys.lists() })
  });
}
~~~

这里回滚的是整份当前列表快照，因此这个简化方案假设 `reports/list` 前缀下的所有排序视图共用一个变更入口：从 `onMutate` 到 `onSettled` 返回的失效 Promise 完成前，全局只有一个乐观变更。否则另一排序 key 上的 mutation 或失效重抓可能覆盖乐观值，整表回滚也可能抹掉另一笔已成功变更。调用端应使用列表级 `isPending` gate 禁用所有排序视图中的行操作，不能只按行或按当前排序 key 禁用；首次切换时的本地临时行以及当前 key 尚无 `query.data` 的视图也要禁用操作。如果存在其他触发入口，它们也必须共享提交级串行约束；单靠某个 hook 的 `isPending` 显示或禁用按钮不能阻止其他入口并发提交。若 mutation 失败，界面可检查 `isError`，并用同一组变量重试，例如再次提交上面的 April 参数。当前片段只展示 hook/cache 处理，没有渲染调用按钮。若同一报表还缓存为详情查询，更新也要覆盖或失效对应的详情 key，不能只改当前列表。服务端仍是权威来源；乐观更新只是让等待中的界面先表达用户意图。

查询函数收到的 `AbortSignal` 要传给 `fetch` 才能让客户端取消底层读取；取消与忽略旧响应是客户端行为，不能承诺服务端已经停止处理请求。若手写 Effect 而不用查询库，要用 cleanup 忽略过期结果，见[React更新轮次中的数据请求](#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)。API JSON 仍须在边界运行时校验；TypeScript 类型本身不会验证网络数据，见[如何处理不可信 JSON？](#46.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F)。

> [!info]- 来源与版本核验（TanStack Query v5.90.3；React 19.3；2026-11-06）
> - `queryKey` 标识查询，函数参数可从 QueryFunctionContext 读取 `signal`：[Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)、[Query Functions](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions)，TanStack Query v5.90.3，核验日期 2026-11-06。
> - query status、`refetch`、mutation callback 与返回 Promise 的等待语义：[useQuery](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery)、[useMutation](https://tanstack.com/query/latest/docs/framework/react/reference/useMutation)、[Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)，TanStack Query v5.90.3。
> - `staleTime`、失效和缓存策略：[Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)、[Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)、[`QueryClient.setQueryData`](https://tanstack.com/query/latest/docs/reference/QueryClient#queryclientsetquerydata)，TanStack Query v5.90.3。
> - 取消信号与乐观更新快照/回滚：[Query Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)、[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5.90.3。
> - React 手写 Effect 请求必须清理失效响应：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3 文档，核验日期 2026-11-06。
> - HTTP 资源标识中的片段不随请求发送：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
## 10. React错误边界能恢复哪些失败？

**案例背景。** 报表页从 `/reports?sort=recent#summary` 显示服务端给出的 May、April；选择 **Oldest first** 后，`sort=oldest` 让列表顺序变为 April、May。排序写入历史并在 Back 时从 URL 恢复由[浏览器导航路径](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)负责。若这片列表的某个组件在 render（渲染）时抛错，Error Boundary（错误边界）可以替代列表显示备用内容，同时让排序工具栏等边界外界面继续工作。它也能接住 React 管理的子组件 Effect setup/cleanup 中同步抛出的错误；点击处理器和 Effect 启动的异步任务失败则各有自己的处理路径。

### 边界放在用户能理解的恢复位置

React 内置的错误边界仍由类组件实现；`fallback`（备用界面）应说明用户能做什么。`static getDerivedStateFromError` 决定下一次 render 是否显示 fallback；`componentDidCatch` 适合记录错误和组件栈。下面的边界包住报表区域；按钮重置边界并重新渲染子树，不会重试数据请求：

~~~jsx
import { Component } from "react";

class ReportBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error(error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <section>
          <p role="alert">报表区域无法显示。</p>
          <button type="button" onClick={() => this.setState({ failed: false })}>
            重新尝试显示
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}

function ReportsShell({ reports }) {
  return (
    <>
      <div role="toolbar">报表排序工具栏（占位）</div>
      <ReportBoundary>
        <ReportsList reports={reports} />
      </ReportBoundary>
    </>
  );
}

function ReportsList({ reports }) {
  return <ul>{reports.map(report => <li key={report.id}>{report.title}</li>)}</ul>;
}
~~~

可临时把 `reports` 设为 `[null]` 检查边界：`ReportsList` 读取空行的属性时抛错，列表被备用界面替换，排序工具栏占位仍留在边界外。边界粒度决定错误后保留多少界面。这里 `reports.map` 在被边界包住的 `ReportsList` 组件中执行，所以行渲染出错会落到该边界；包住整页会让工具栏也消失，每个单元格都放边界又会产生许多细碎的恢复区。应按用户能独立理解和恢复的区域划分。重新渲染同一失败组件会再次触发边界；对于查询错误，通常应让数据层重试请求并把错误状态呈现在列表边缘。

在 `return <ReportsList />` 周围写普通 `try/catch` 捕获不到 `ReportsList` 后续的 render 错误：JSX 先创建元素描述，React 稍后才渲染其子树；用边界明确包住要隔离的区域。

### 错误边界与其他失败处理方式

React 会把子组件 render、构造函数、React 生命周期，以及 React 管理的子组件 Effect setup/cleanup 中同步抛出的错误交给最近的错误边界。React 19 的 Transition Action（过渡动作）里抛出的错误也会转交边界；`use` 读取的 Promise 若拒绝，同样会进入最近边界。边界自己 render 抛错时，只能交给更外层边界。

这些失败路径按同步调用还是异步任务区分：

| 失败发生位置 | 处理方式 |
|---|---|
| 普通点击处理器 | 在处理器里 try/catch，设置界面错误或上报 |
| 子组件 Effect setup/cleanup 同步抛错 | 由最近错误边界显示备用界面 |
| Effect 启动的 Promise 后续拒绝、定时器回调异步抛错 | 显式处理 rejection 或更新错误状态；不会自动交给错误边界 |
| `useEffect` 请求返回失败 | 在请求/查询状态显示失败和重试；异步请求失败不会自动变成 render error |
| Suspense 子树仍在加载 | 需要等待界面时由最近 `<Suspense>` fallback 承担；Transition 中可保留已显示内容 |
| 服务端渲染阶段 | 由框架或服务端渲染管线处理，不靠客户端边界 |

边界本身没有函数组件版本的内置等价 API，可复用类边界或使用已有边界库。错误边界显示“这一块无法工作”；Suspense（挂起边界）表示“这一块还没准备好”；查询错误则说明“这次数据读取失败”。[报表服务端状态章节](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F)负责请求缓存、错误重试和更新顺序。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 类组件捕获范围、未捕获类别、`getDerivedStateFromError` 与 `componentDidCatch`：[Component — Catching Rendering Errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，React 19.3 文档。
> - Effect setup/cleanup 在 commit 阶段由 React 调用：[useEffect](https://react.dev/reference/react/useEffect)，React 19.3 文档。React 19.3.0 + jsdom 30.1.3 中同步子 Effect throw 由最近边界捕获；Promise 后续 rejection 与定时器回调仍需异步错误处理。
> - JSX 描述如何在后续 render 中成为已提交界面：[Render and Commit](https://react.dev/learn/render-and-commit)，React 19.3 文档。
> - Transition Action 中抛错交给边界：[useTransition — Displaying an error to users with an error boundary](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary)，React 19.3 文档。
> - 被拒绝 Promise 与最近错误边界：[use](https://react.dev/reference/react/use)，React 19.3 文档。
> - Suspense fallback 仅处理挂起中的内容：[Suspense](https://react.dev/reference/react/Suspense)，React 19.3 文档；核验日期 2026-11-06。
## 11. 为什么一次 DOM 改动会增加布局或绘制工作？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，看到 May、April 两行报表；点击“最早优先”后，页面把 URL 中的 `sort` 改为 `oldest`，并把行顺序换成 April → May。`/reports.js` 的处理器同步改 DOM，但列表何时出现在屏幕上、浏览器为此需要多少工作，是接下来的问题。

~~~mermaid
flowchart TD
    CLICK[点击“最早优先”] --> DOM[同步改动 DOM：行顺序与 aria-pressed]
    DOM --> INVALID[相关样式或布局数据可能失效]
    INVALID --> STYLE[需要时重新计算样式]
    STYLE -->|几何或换行有变化| LAYOUT[需要时重新计算布局]
    STYLE -->|几何不变但像素变化| PAINT[更新受影响的绘制结果]
    LAYOUT --> PAINT
    PAINT --> RASTER[需要时栅格化]
    RASTER --> COMPOSITE[合成画面]
    COMPOSITE --> FRAME[有需要时在后续渲染机会呈现]
    DOM -->|若脚本此时读取几何| READ[脚本读取当前几何]
    READ --> CHECK{相关数据已经是最新？}
    CHECK -->|是| VALUE[返回几何值，脚本继续]
    CHECK -->|否| FLUSH[返回前同步刷新样式或布局]
    FLUSH --> VALUE
    STYLE -->|属性与实现路径都适合时| MAYBE[某些实现可跳过布局或绘制]
    MAYBE --> COMPOSITE
~~~

图里的阶段是帮助解释依赖的概念模型，不表示每次更新都必须走完全部步骤。浏览器可延后并合并工作，也可跳过没有失效的阶段；脚本中的几何读取若要求最新结果，则可能让原本可延后的刷新提前发生。DOM 改动会提供下一帧的呈现状态；后续网络请求或异步业务结果是否已完成，是另一条时间线，浏览器也不保证每个任务后都立刻呈现。渲染机会与这条时间边界见[浏览器 JavaScript 何时运行，画面何时更新？](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)。

### 浏览器需要让哪些信息重新一致？

DOM 描述节点及其父子顺序，CSS 规则为这些节点提供样式。样式计算得到当前适用的 computed style（计算样式）；布局根据样式、内容和可用空间计算盒子的尺寸与位置；绘制把可见内容表示为绘制操作。后续实现可把绘制操作栅格化为像素内容，再合成各层并提交画面。简单说，列表换序先改了结构，浏览器必须保证它下一次显示时，结构、样式和几何彼此一致。

| 对这张报表做什么 | 下一次呈现通常要考虑什么 | 为什么不能仅凭操作名称断言成本 |
|---|---|---|
| 把两行从 May → April 调成 April → May | 更新列表有关的样式与几何，必要时重绘 | 具体失效范围取决于布局依赖和引擎优化 |
| 只把当前按钮文字颜色改为强调色 | 重算相关样式并更新可见像素 | 若尺寸、字体和换行不变，可能复用已有几何 |
| 改宽度、字体尺寸，或插入会占空间的内容 | 可能重新布局受影响的区域并更新绘制 | 几何变化会影响后续内容的位置，影响范围不一定只在一个节点内 |
| 改变适合合成处理的 `transform` 或 `opacity` | 有些情况下可以跳过布局或绘制 | 不保证只在合成阶段完成，也不保证提升图层或使用 GPU |
| DOM / 样式改动后读取几何 | 若返回值依赖的样式或布局已失效，读取前可能同步刷新 | 若数据仍是最新的，同一读取 API 不需要触发布局 |

`reflow`（重排）和 `repaint`（重绘）是常用说法，不是可以跨浏览器直接比较的性能分数。即使影响的是一个小节点，它的位置也可能牵动后续内容；反过来，大量节点若没有相关数据变化，也不必每次都重算。`transform` 和 `opacity` 常作为动画候选，是因为某些更新路径可以跳过布局或绘制；要确认目标页面是否走了这条路径，应检查实际录制，而不是只看 CSS 属性名。

### 为什么读几何会让脚本停下来？

浏览器可以把样式或布局标为待更新，先继续运行 JavaScript，等需要显示或读取当前结果时再计算。`offsetWidth`、`getBoundingClientRect()` 等几何 API 要返回调用时的尺寸或坐标；如果前面的 DOM / 样式写入已经使相关数据失效，浏览器就可能先刷新再返回。这里的停顿不是这个 API 每次都会“主动制造布局”，而是它要求拿到尚未更新的当前值。DOM 写入本身同步生效；同步刷新发生时，脚本会在几何值返回前付出这一段工作。

下面的示例从同一组已有元素开始：两个不受最小/最大宽度或变换约束的普通块级元素，边框盒宽度分别为 100px 和 160px；`box-sizing: border-box` 让 `style.width` 也指定边框盒宽度，因此两种代码都意图把宽度改为 110px 和 170px。示例使用数组而不是直接把 `querySelectorAll()` 返回的 `NodeList` 当作有 `.map()` 的数组：

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

~~~javascript
const items = Array.from(document.querySelectorAll("#width-demo .item"));
~~~

以下两段代码是从上述相同初始宽度分别运行的两种写法，不是先后连续执行。第一种在每次写入宽度后，又读取下一项当前宽度。若某次写入使后续读取依赖的几何数据失效，读取可能触发同步刷新，形成反复的读—写：

~~~javascript
for (const item of items) {
  item.style.width = (item.offsetWidth + 10) + "px";
}
~~~

若需求是按原始宽度统一增加 10 像素，可以先读取一组尺寸，再写回；按上述起始尺寸，写入结果同样是 110px 和 170px：

~~~javascript
const widths = items.map(item => item.offsetWidth);
items.forEach((item, index) => {
  item.style.width = (widths[index] + 10) + "px";
});
~~~

第二种顺序消除了显眼的交替读写，允许浏览器把后续更新合并处理；它不保证整段代码只发生一次布局，也不保证所有数据和页面上都更快。先确认页面确有强制刷新，再用性能录制定位写入与读取的位置。不同几何 API 返回的盒子与坐标系不同，按问题选择，见[哪个 DOM 几何 API 能回答哪种测量问题？](#25.%20Which%20DOM%20geometry%20API%20answers%20which%20measurement%20question?%20/%20%E5%93%AA%E4%B8%AA%20DOM%20%E5%87%A0%E4%BD%95%20API%20%E8%83%BD%E5%9B%9E%E7%AD%94%E5%93%AA%E7%A7%8D%E6%B5%8B%E9%87%8F%E9%97%AE%E9%A2%98%EF%BC%9F)。

### 引擎怎样实现这些步骤？

Web 平台规定 DOM、CSS 和几何 API 可观察到的结果，但不要求每个浏览器使用相同的内部阶段、进程或线程。以 Chromium 的 RenderingNG 为例，Blink 会计算样式、布局并生成绘制产物，后续可把绘制列表分块栅格化为 GPU 纹理 tile，再提交 compositor frame，由 Viz 聚合并绘制到屏幕；若某次变化不需要某些阶段，管线可以跳过它们。其他引擎的内部组件名称和调度方式可以不同，因此性能判断应围绕可见效果和录制数据，而不是把 Chromium 流程当作所有浏览器的硬性规范。

如果报表扩大到许多行，先分清瓶颈在网络传输、服务端查询、客户端数据计算，还是已挂载节点的样式与布局。虚拟滚动主要减少同时挂载的 DOM；它不会自动缩小已下载数据或消除对全量数据的计算。完整的窗口计算、可变行高、焦点和辅助技术边界在[长报表列表何时适合虚拟滚动？](#14.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)展开；性能录制怎样区分主线程、布局和绘制成本，见[如何测量并诊断网页性能问题？](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。

> [!info]- 来源
> - 本章的概念阶段不是 Web 平台规定的完整固定流水线；渲染机会、更新渲染： [WHATWG HTML：事件循环与更新渲染](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering)，Living Standard，持续更新；核对日期：2026-11-06。
> - 盒子、布局与几何读取的可观察行为： [CSS Display](https://www.w3.org/TR/css-display-3/)，W3C Candidate Recommendation Draft，2026-06-05，display 类型与盒子生成；[CSS Sizing](https://www.w3.org/TR/css-sizing-3/#box-sizing)，box-sizing 的宽度计算；[CSSOM View](https://drafts.csswg.org/cssom-view/)，CSSWG Editor's Draft，`offsetWidth` 与 `getBoundingClientRect()`；核对日期：2026-11-06。
> - DOM / 样式失效后读取几何可能触发同步布局，以及读写交错的风险： [Chrome Performance Insights：Forced reflow](https://developer.chrome.com/docs/performance/insights/forced-reflow)，Chrome DevTools 文档，2025-10-08 更新；该诊断解释 Chrome 实现。
> - 作为一个实现案例的样式、布局、绘制、tile 栅格化、Viz 合成与可跳过阶段： [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)，[RenderingNG 数据结构：tiles 与 Viz](https://developer.chrome.com/docs/chromium/renderingng-data-structures)，Chromium 架构说明；核对日期：2026-11-06。
## 12. 如何测量并诊断网页性能问题？

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
| 处理器很快结束，但下一帧仍晚 | 呈现延迟、事件回调结束后的样式/布局/绘制轨迹 | 检查 DOM 规模和昂贵样式；见[为什么一次 DOM 改动会增加布局或绘制工作？](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F) |
| React 处理时长长 | 浏览器 Performance 录制与组件 render/commit 记录 | 用 [React Profiler](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F) 找出组件工作，再回到浏览器轨迹查看提交后的样式、布局和绘制 |
| 路由主脚本传输或解析时间长 | Network 请求体积、脚本解析与执行时间、生产构建的 chunk | 检查路由代码是否实际拆分并延后加载；构建产物边界见[构建工具](#52.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F) |
| 图片出现时文字或按钮向下跳 | CLS 事件、缺少尺寸的图片/嵌入内容、字体替换或异步插入 | 提前保留内容空间并复现相同网络条件 |
| 首屏按钮显示了但点击无反馈 | 脚本是否已完成初始化，或处理器是否被主线程工作挡住 | 分清“已经看见”与“事件可处理”；HTML 脚本调度边界见[脚本如何影响 HTML 解析与文档就绪？](#3.%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F) |

若 click handler 在返回前调用 `offsetWidth` 或 `getBoundingClientRect()`，并因此同步触发布局，这段成本在 INP 中计入处理时长；若几何读取或渲染工作发生在事件回调结束后、下一帧出现前，则计入呈现延迟。录制中出现强制刷新时，再检查具体调用顺序；不要因为看到布局或绘制就先把它们视为缺陷。修复后在同一 URL、设备、数据和动作下复测，再用相同设备分组观察现场样本。DOM 变更引发的工作边界见[为什么一次 DOM 改动会增加布局或绘制工作？](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

### 优化首屏时，先处理实际 LCP 路径

打开 Performance 或 Lighthouse 录制后，先确定本次视口中的实际 LCP 元素，再看它的资源从哪里发现、何时开始请求、何时响应、何时绘制。不同设备视口、URL 参数和缓存可能让同一路由的 LCP 元素不同，因此不要只按本机一次录制假定全体用户看见同一内容。若 LCP 是图片，不要对它使用延迟加载；为图片或嵌入内容声明尺寸可以提前留出空间，减少后续内容位移。

只有录制显示某个非关键图片或脚本与关键路径竞争时，才考虑延后它。若阻塞样式表确实拖慢 LCP，可以比较内联首屏必需样式是否有收益；代价是 HTML 变大，而且首屏样式不能像独立样式表那样单独复用缓存。服务端渲染或静态输出可能让内容更早进入 HTML，但不会自动保证 LCP 或 INP 良好。HTTP 新鲜度、缓存验证与网络请求时序见[HTTP 协议与缓存](../../engineering-foundations/networking/http-protocols-and-websockets.md)；图片加载策略见[如何延迟加载图片而不损害 LCP 或布局稳定性？](#26.%20How%20should%20a%20browser%20page%20lazy-load%20images%20without%20hurting%20LCP%20or%20layout%20stability?%20/%20%E5%A6%82%E4%BD%95%E5%BB%B6%E8%BF%9F%E5%8A%A0%E8%BD%BD%E5%9B%BE%E7%89%87%E8%80%8C%E4%B8%8D%E6%8D%9F%E5%AE%B3%20LCP%20%E6%88%96%E5%B8%83%E5%B1%80%E7%A8%B3%E5%AE%9A%E6%80%A7%EF%BC%9F)。

### 大列表要先分辨数据成本与 DOM 成本

如果报表数据量很大，不要仅凭条目数决定方案：先分别看网络传输了多少、查询/筛选和转换计算了多少、同时挂载了多少节点，以及交互中的布局和绘制花了多少时间。客户端不需要全量结果时，分页、增量加载、服务端过滤或返回汇总值可减少传输与数据处理；若用户需要大量数据但录制确认瓶颈是大量已挂载行，虚拟滚动可减少可见窗口之外的 DOM 工作。虚拟滚动不自动减少完整数据集的下载、内存或 `O(n)` 计算；它的计算、测量、焦点、键盘和辅助技术边界集中在[长报表列表何时适合虚拟滚动？](#14.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。

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
## 13. 如何测量并减少不必要的React工作？

**案例背景。** 报表页当前 URL 为 `/reports?sort=recent#summary`，服务端给 May、April 两行；选择 **Oldest first** 后，`sort=oldest` 让可见顺序变成 April、May。打开说明面板不改变报表数据；若这个按钮仍让大量行再次执行组件函数，可能有可优化的 React 工作；若主要时间发生在提交后的布局和绘制，memoization（记忆化）不会修复浏览器瓶颈。排序的 URL 与 Back 恢复由[浏览器历史栈机制](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)负责，本章代码聚焦面板更新与 React 成本测量。

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

例如，若打开说明面板时 Profiler 显示每个 `ReportRow` 都计算了一遍，但行 props 和结果都未变，可以检查状态范围和组件边界；若 React 时间很短而布局成本明显，继续看[浏览器渲染测量](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)或[长列表](#14.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F)。单看 render 次数或控制台日志不能证明用户感知性能已经变好。

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

为同一交互记录组件耗时、commit 数量、脚本和浏览器布局成本。检查 Compiler 的编译覆盖后，再比较它自动优化与手工 memoization 的收益；若手工缓存增加依赖复杂度却没有缩短交互，就删掉这层复杂度。稳定 key 用来保留行身份，不是性能 API；组件状态的范围则优先按所有权整理，见[如何组合组件与复用行为？](#7.%20%E5%A6%82%E4%BD%95%E5%9C%A8React%E4%B8%AD%E7%BB%84%E5%90%88%E7%BB%84%E4%BB%B6%E4%B8%8E%E5%A4%8D%E7%94%A8%E8%A1%8C%E4%B8%BA%EF%BC%9F)。

用 CSS 隐藏已挂载面板时，它仍留在 React 树中，state 和 Effect 继续存在；条件移除会卸载组件并执行 cleanup，再显示时会创建新实例。二者应按生命周期和交互需求选择。Fragment 可免去多余 DOM 包装节点，但这本身不构成可测的性能结论。

> [!info]- 来源与版本核验（React 19.3；Compiler v1.0；2026-11-06）
> - React 文档当前版本及 Compiler 稳定状态：[Versions](https://react.dev/versions)、[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，核验日期 2026-11-06；Compiler v1.0 于 2025-10-07 发布。
> - 编译器的自动缓存范围、建议先 profile、以及手工 memoization 的当前角色：[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，React 19.3 文档。
> - `memo` 的比较、state/Context 更新和 Compiler 行为：[memo](https://react.dev/reference/react/memo)；计算值与函数引用：[useMemo](https://react.dev/reference/react/useMemo)、[useCallback](https://react.dev/reference/react/useCallback)，React 19.3 文档。
> - React DevTools 的 Profiler 面板：[React Developer Tools](https://react.dev/learn/react-developer-tools)，React 19.3 文档；指定子树的程序化性能分析：[Profiler](https://react.dev/reference/react/Profiler)，React 19.3 文档。浏览器阶段见[Performance Metrics and Analysis](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)。
## 14. 长报表列表何时适合虚拟滚动？

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

先以真实报表交互在[性能指标与诊断](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F)里区分请求、脚本、DOM、布局和内存成本。React 组件本身的 render 成本见[React渲染优化](#13.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E5%87%8F%E5%B0%91%E4%B8%8D%E5%BF%85%E8%A6%81%E7%9A%84React%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源与版本核验（2026-11-06）
> - 虚拟列表的实际测量、可变行高与滚动锚点：[TanStack Virtual — Virtualizer API](https://tanstack.com/virtual/latest/docs/api/virtualizer)，官方当前文档，核验日期 2026-11-06。
> - 只呈现部分集合时的位置与总量属性、以及表格/网格行位置：[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)，W3C Recommendation，2023-06-06。
> - 动态加载 listbox 项的键盘模式和 `aria-posinset`/`aria-setsize`：[WAI-ARIA APG — Listbox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)，W3C WAI 官方模式，核验日期 2026-11-06。
## 15. How do semantic HTML forms support keyboard and assistive-technology users? / 语义化 HTML 表单如何支持键盘与辅助技术用户？

Use native elements for their built-in meaning and behavior: a `label` gives a form control a programmatic name, a `button` supports keyboard activation, and an `a href` represents navigation. Keep focus visible; describe validation errors in text, associate them with the field, and focus the invalid field after a custom submission is rejected. ARIA adds information for assistive technology but does not create keyboard behavior or native validation. / 使用原生元素获得其内建语义与行为：`label` 为表单控件提供程序化名称，`button` 支持键盘激活，`a href` 表示导航。保持焦点可见；用文字描述校验错误并关联到字段，自定义提交被拒绝时将焦点移到无效字段。ARIA 为辅助技术提供信息，但不会创建键盘行为或原生校验。

Use heading levels to express structure, landmarks such as `main` and `nav` to identify regions, and `alt` text that conveys an informative image's purpose. Use empty alternative text (`alt=""`) for decorative images. Keep source order meaningful because CSS visual placement does not change document order for nonvisual presentation. Do not rely on color or position alone to communicate a required state.

This form keeps the browser's `required` and `type="email"` constraints as the no-JavaScript baseline. Once the custom handler is installed, it reports the invalid state in text, associates the error through `aria-describedby`, marks the field, and moves focus to it.

```html
<form id="subscribe" action="/subscribe" method="post">
  <label for="email">Email address</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">Enter an address such as name@example.com.</p>
  <p id="email-error" hidden></p>
  <button type="submit">Subscribe</button>
</form>

<style>
  :focus { outline: 3px solid currentColor; outline-offset: 2px; }
</style>

<script>
const form = document.querySelector("#subscribe");
const email = form.elements.namedItem("email");
const error = document.querySelector("#email-error");

function clearError() {
  error.textContent = "";
  error.hidden = true;
  email.removeAttribute("aria-invalid");
}

email.addEventListener("input", () => {
  if (email.validity.valid) clearError();
});

form.addEventListener("submit", event => {
  if (email.validity.valid) {
    clearError();
    return;
  }

  event.preventDefault();
  error.textContent = email.validity.valueMissing
    ? "Enter an email address."
    : "Enter a valid email address.";
  error.hidden = false;
  email.setAttribute("aria-invalid", "true");
  email.focus();
});
form.noValidate = true; // Enable custom feedback after the handler is ready.
</script>
```

Before JavaScript installs the handler, the native constraints can reject an invalid submission. After installation, Tab reaches the input and button; invalid submission focuses the field and associates its visible error with the accessible description. The client check improves feedback, but the server must validate submitted values before accepting them. This is an example interaction, not a claim that one snippet makes an entire page conformant.

Group related controls with a `fieldset` and `legend` when their shared question matters. A clear page heading and landmarks help a reader find the form before they interact with individual fields. [WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/)

**Guidance / 指南** — [WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/), [WAI form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/), [WAI image alternatives](https://www.w3.org/WAI/tutorials/images/), [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/), [ARIA authoring principles](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/), [keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), and the [HTML Standard](https://html.spec.whatwg.org/).
## 16. How does the CSS cascade decide which declaration applies? / CSS 级联如何决定最终生效的声明？

CSS first keeps declarations that apply to the element, then resolves their cascade priority. Origin and importance, encapsulation context, element-attached styles, and layer precedence are considered before specificity; scoping proximity where applicable and source order resolve later ties. Specificity is therefore only one part of the cascade; a larger selector weight cannot override a declaration that wins an earlier priority step. / CSS 先筛选适用于元素的声明，再解析级联优先级。来源与重要性、封装上下文、元素附加样式和层顺序先于 specificity；适用时由作用域接近程度及源码顺序进一步打破平局。因此 specificity 只是级联的一部分；更高的选择器权重不能推翻更早优先级步骤已经胜出的声明。

### Compare specificity only after earlier cascade steps

For ordinary author stylesheet rules in the same origin, importance, and layer, compare the tuple `(ID, class/attribute/pseudo-class, type/pseudo-element)` from left to right.

```css
/* (1, 1, 0): wins this same-layer comparison */
#sidebar .menu-item { color: red; }

/* (0, 3, 0): loses even with more classes */
.menu .menu-item.active { color: blue; }
```

An ID column wins before any number of class selectors. The universal selector (`*`) and combinators (`>`, `+`, `~`) add no specificity.

Functional pseudo-classes have defined argument behavior:

- `:not()`, `:is()`, and `:has()` contribute the specificity of their most-specific argument.
- `:where()` contributes zero specificity, including its arguments.
- A selector such as `div:not(.sidebar)` has specificity `(0, 1, 1)`.

Inline style declarations participate in the cascade through a separate element-attached style precedence step; do not treat their behavior as simply “more classes.” Importance and cascade layer rules still matter.

### Use layers to organize priority intentionally

Cascade layers let a stylesheet establish broad precedence groups, then use specificity within the winning layer.

```css
@layer reset, components, utilities;

@layer components {
  .button { color: navy; }
}

@layer utilities {
  .text-red { color: red; }
}
```

For normal declarations, later named layers outrank earlier layers, and unlayered normal declarations outrank declarations in named layers. For important declarations, layer order reverses. Use layer order as an explicit project-level policy rather than relying on ever-growing selector specificity. [CSS Cascading and Inheritance](https://www.w3.org/TR/css-cascade-5/#layer-order) defines the ordering.

### How a child gets a value after the cascade / 级联后子元素怎样得到值

The cascade first finds a winning declaration on the element itself. If none applies, an inherited property normally takes the parent’s computed value, while a non-inherited property takes its initial value. User-agent rules still participate in the cascade. A rule that directly sets a child’s color wins over an inherited color even if the parent was styled with an ID selector.

~~~html
<article id="notice">Read <span class="label">this</span>.</article>
~~~

~~~css
#notice { color: #222; font-family: system-ui, sans-serif; margin: 2rem; }
.label  { color: blue; }
~~~

The span computes blue from its own declaration and inherits the font. The parent's margin does not flow down. Applying `margin: inherit` explicitly would use the parent’s computed margin. Fonts, color, line height, text alignment, letter spacing, and visibility usually inherit. Width, padding, margin, display, and position do not inherit by default. Check the property definition when it matters. / 先看子元素自己是否有生效声明，再按属性的继承规则取值。父元素选择器的优先级不会传给子元素。

**Text decoration / 文本装饰.** A parent's underline can be drawn across descendant text through decoration propagation. On `<a>Title <em>with emphasis</em></a>`, setting `text-decoration: none` on `em` does not erase the line drawn by `a`. Change the rule on the element that establishes the decoration. [CSS Cascade defaulting and inheritance](https://www.w3.org/TR/css-cascade-5/#defaulting) · [CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/#line-decoration)

### Keep selectors maintainable

Attribute selectors such as `[data-state="active"]` can reflect state in markup. BEM naming (`.block__element--modifier`) tends to keep selectors flat and easier to override. CSS-in-JS-generated classes still participate in the browser's cascade; the generation method does not remove cascade rules.

Critical CSS can reduce dependence on a render-blocking stylesheet for content that must appear early, but it adds markup bytes and can duplicate later CSS. Treat it as a measured delivery choice, not as an automatic selector-speed technique. See [Performance Metrics and Analysis](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F).

**Specifications:** [Selectors Level 4](https://www.w3.org/TR/selectors-4/#specificity-rules), [CSS Cascading and Inheritance Level 5](https://www.w3.org/TR/css-cascade-5/), and [CSS Display, visual order](https://www.w3.org/TR/css-display-3/#order-property).


**Related questions:** [responsive CSS units and layout](#19.%20Which%20CSS%20units%20and%20responsive%20layout%20rules%20fit%20the%20available%20space?%20/%20%E5%93%AA%E4%BA%9B%20CSS%20%E5%8D%95%E4%BD%8D%E4%B8%8E%E5%93%8D%E5%BA%94%E5%BC%8F%E5%B8%83%E5%B1%80%E8%A7%84%E5%88%99%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E7%A9%BA%E9%97%B4%EF%BC%9F) covers size references and breakpoints; [semantic HTML forms](#15.%20How%20do%20semantic%20HTML%20forms%20support%20keyboard%20and%20assistive-technology%20users?%20/%20%E8%AF%AD%E4%B9%89%E5%8C%96%20HTML%20%E8%A1%A8%E5%8D%95%E5%A6%82%E4%BD%95%E6%94%AF%E6%8C%81%E9%94%AE%E7%9B%98%E4%B8%8E%E8%BE%85%E5%8A%A9%E6%8A%80%E6%9C%AF%E7%94%A8%E6%88%B7%EF%BC%9F) covers native controls and validation; [text overflow and line clamp](#Constrained%20text%20and%20line%20clamping%20/%20%E5%8F%97%E9%99%90%E6%96%87%E6%9C%AC%E4%B8%8E%E8%A1%8C%E6%95%B0%E8%A3%81%E5%88%87) covers visual truncation.
## 17. How does CSS calculate an element's box size? / CSS 如何计算元素盒子的尺寸？

A CSS box has content, padding, border, and margin layers. With the default `box-sizing: content-box`, declared width and height size the content area; padding and border are added outside it. With `box-sizing: border-box`, the declared dimensions include content, padding, and border. Margin remains outside both. / CSS 盒模型包含内容、内边距、边框和外边距。默认的 `box-sizing: content-box` 把声明的宽高用于内容区，内边距和边框会在外侧增加尺寸；`box-sizing: border-box` 则将内容、内边距和边框都包含在声明尺寸内。两种模式下 margin 都在盒子外面。

~~~text
┌────────────── margin ──────────────┐
│ ┌──────────── border ────────────┐ │
│ │ ┌────────── padding ────────┐ │ │
│ │ │          content           │ │ │
│ │ └───────────────────────────┘ │ │
│ └───────────────────────────────┘ │
└───────────────────────────────────┘
~~~

For `width: 100px; padding: 10px; border: 5px solid`, the content-box width is `100 + 20 + 10 = 130px`. Under border-box the outer border edge remains 100px and the content area shrinks to 70px. Height follows the same rule.

| Declared `width`/`height` size | `content-box` | `border-box` |
|---|---|---|
| Content area | Yes | No |
| Padding and border | Added outside the declared size | Included in the declared size |
| Margin | Always outside | Always outside |

A common reset makes sizing arithmetic predictable, including generated pseudo-elements:

~~~css
*, *::before, *::after {
  box-sizing: border-box;
}
~~~

The `padding` and `margin` shorthands accept one to four values in top/right/bottom/left order: one value sets all sides; two set vertical then horizontal; three set top, horizontal, bottom; four set each side clockwise.

~~~css
.box-a { border: 1px solid black; }
.box-b { border: 3px dashed red; }

.box {
  width: 100px;
  height: 100px;
  padding: 10px;
  border: 5px solid black;
  box-sizing: border-box; /* outer border box stays 100 × 100 */
}
~~~

### A triangle from border geometry / 用边框几何画三角形

A zero-size element with thick borders forms four triangular border regions. Make three borders transparent and color one: the colored region becomes a triangle pointing away from that border. This is useful for small carets and callouts; use `clip-path` when the shape must scale independently of border thickness. / 零尺寸元素的粗边框会形成四个三角形区域。将三个边框设为透明并给一个边框着色，彩色区域会形成一个朝向该彩色边框相反方向的三角形，适合小箭头和气泡尖角；若形状需要独立缩放，可考虑 `clip-path`。

```html
<div class="triangle" aria-hidden="true"></div>
```

```css
.triangle {
  width: 0;
  height: 0;
  border: 10px solid transparent;
  border-left-color: red; /* points right */
}
```

The element’s content box has zero width and height, so the visible shape is created by its border geometry. Color the bottom border for an upward-pointing triangle, top for downward, left for rightward, or right for leftward.

For a shape whose dimensions should follow its box rather than a fixed border size:

```css
.triangle {
  width: 1rem;
  aspect-ratio: 1;
  background: currentColor;
  clip-path: polygon(50% 0, 100% 100%, 0 100%);
}
```

The second example makes an upward triangle; change the polygon points to change direction. A decorative caret should be hidden from assistive technology if it adds no meaning. If it communicates state or direction, expose that information through the control's text or semantics as well.

[CSS Masking on clipping paths](https://www.w3.org/TR/css-masking-1/#the-clip-path)

For the flow rules that determine how floats and margins interact around boxes, see [How does a block formatting context contain floats and margins?](#18.%20How%20does%20a%20block%20formatting%20context%20contain%20floats%20and%20margins?%20/%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F). For CSS layout coordinates and DOM geometry, see [DOM geometry APIs](#25.%20Which%20DOM%20geometry%20API%20answers%20which%20measurement%20question?%20/%20%E5%93%AA%E4%B8%AA%20DOM%20%E5%87%A0%E4%BD%95%20API%20%E8%83%BD%E5%9B%9E%E7%AD%94%E5%93%AA%E7%A7%8D%E6%B5%8B%E9%87%8F%E9%97%AE%E9%A2%98%EF%BC%9F).

**Specification:** [CSS 2.2 box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions), checked 2026-11-05.
## 18. How does a block formatting context contain floats and margins? / 块格式化上下文如何约束浮动和外边距？

A block formatting context (BFC) is a flow-layout boundary: floats cannot intrude into its contents, its auto height includes floats inside it, and child margins do not collapse through its boundary. It is not a stacking context, a universal containing block, or general layout containment. Use `display: flow-root` when the intended change is simply to contain floats and separate child margins. / 块格式化上下文（BFC）是流式布局的边界：外部浮动不会侵入其内容，BFC 根的自动高度会包含其中的浮动，子元素外边距也不会穿过该边界折叠。BFC 不等于堆叠上下文、通用定位包含块或整体布局隔离。若目的只是包含浮动并分隔子级 margin，使用 `display: flow-root`。

### Float containment / 包含浮动

Floats leave normal flow, so a normal-flow parent whose children are all floated may have no height from those children. A BFC root contains its floats:

~~~css
.container { background: red; }
.box { float: left; width: 100px; height: 100px; }

/* Before: .container may collapse to a stripe. */
.container { display: flow-root; } /* includes the floated child */
~~~

Use a clearfix when maintaining legacy markup or browser support requires it:

~~~css
.parent::after {
  content: "";
  display: table;
  clear: both;
}
~~~

A clearing element can also end the float interaction, but adds non-semantic markup:

~~~html
<div class="parent">
  <div class="child">Content</div>
  <div class="clear"></div>
</div>
~~~

~~~css
.clear { clear: both; }
~~~

`overflow: hidden` can establish a BFC but also clips overflow and creates a scroll container. Prefer `flow-root` when clipping and scrolling are not wanted. `overflow: clip` does not establish a BFC.

### Margin collapse / 外边距折叠

Adjacent positive vertical margins of in-flow block siblings in the same BFC collapse to the larger value: two `50px` margins create a `50px` gap. A formatting-context boundary prevents a child's margin from collapsing through the container, though the container's own margins still follow its parent context.

~~~html
<section>box one</section>
<section>box two</section>
~~~

~~~css
section { margin: 50px; }
/* Adjacent positive margins collapse to a 50px gap. */
~~~

Wrap a child in a BFC to keep its margin inside that boundary:

~~~html
<section>box one</section>
<div class="bfc"><section>box two</section></div>
~~~

~~~css
section { margin: 50px; }
.bfc { display: flow-root; }
/* The child's top margin stays inside the BFC; the outer gap is 100px. */
~~~

A parent's first child's top margin can also collapse through a parent without border, padding, inline content, clearance, or a new formatting context. A border, padding, or formatting-context boundary separates the margins.

### What establishes a BFC? / 哪些条件会建立 BFC？

- `display: flow-root` explicitly establishes a BFC without clipping or scrolling.
- A block container with `overflow: hidden`, `auto`, or `scroll` establishes a BFC; `overflow: clip` does not.
- Floats, absolutely positioned boxes, inline blocks, and table cells/captions establish independent formatting contexts for their contents.
- Flex and grid containers establish their own formatting contexts, not BFCs. Their items do not participate in block margin collapsing or the usual float intrusion rules.

A BFC has defined flow behavior, not the separate rules for stacking and positioned containing blocks. See [CSS position and stacking](#22.%20How%20do%20CSS%20positioning%20and%20stacking%20determine%20where%20an%20element%20appears?%20/%20CSS%20%E5%AE%9A%E4%BD%8D%E4%B8%8E%E5%A0%86%E5%8F%A0%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E5%85%83%E7%B4%A0%E7%9A%84%E6%98%BE%E7%A4%BA%E4%BD%8D%E7%BD%AE%EF%BC%9F).

**Specifications:** [CSS Display: formatting contexts](https://www.w3.org/TR/css-display-3/); [CSS 2.2: block formatting contexts](https://www.w3.org/TR/CSS22/visuren.html#block-formatting); checked 2026-11-05.
## 19. Which CSS units and responsive layout rules fit the available space? / 哪些 CSS 单位与响应式布局规则适合当前空间？

Choose a unit by its reference: CSS pixels for a stable CSS-space length, percentages for a property-specific containing-block relationship, font-relative units for text-scaled dimensions, and viewport units for viewport-sized regions. Choose the responsive layout mechanism by what the component can measure: Grid's intrinsic tracks for content-driven columns, media queries for viewport conditions, and container queries when a component should react to its own allocated width. / 根据参照选择单位：固定 CSS 空间尺寸使用 CSS 像素，容器关系使用百分比，随文字缩放的尺寸使用字体相对单位，视口区域使用视口单位。再根据布局约束选择响应式机制：内容驱动的列可用 Grid 内在轨道，视口条件可用媒体查询，组件需要响应自身可用宽度时可用容器查询。

### What does each unit measure?

| Unit | Reference | Useful for | Watch for |
|---|---|---|---|
| `px` | CSS reference pixel | Borders and precise spacing | It is not necessarily one physical device pixel |
| `%` | A reference defined by the property | Fluid sizes and offsets | Different properties can use different percentage bases |
| `em` | Usually the element's computed font size; on `font-size`, the inherited size | Spacing that should scale with text | Nested font-size declarations can compound |
| `rem` | Root element's font size | Consistent text-relative sizing across components | A fixed root size can ignore user text preferences |
| `vw` / `vh` | Large viewport dimensions | Viewport-relative sizing | Viewport is not always the available content box |
| `svh` / `lvh` / `dvh` | Small, large, and dynamic viewport heights | Full-height mobile UI with an explicit browser-chrome policy | Dynamic viewport dimensions can change as browser UI changes |
| `vmin` / `vmax` | Smaller / larger viewport dimension | A shape that should adapt to orientation | It chooses one viewport axis relationship, not a content width |

A CSS pixel is a reference unit. Browser zoom and device-pixel ratio affect how CSS lengths map to output pixels; writing `1px` does not promise a one-device-pixel stroke. For a property such as `width`, a percentage is generally resolved against a containing block; the percentage basis for other properties is defined separately. `em` usually follows the element's font size for non-`font-size` properties, while its own `font-size` resolves against the inherited font size. `rem` follows the root element.

The default `vh` corresponds to the large viewport. On devices with retractable browser controls, a `100vh` region can extend behind those controls. Use `svh` when fitting the small viewport matters or `dvh` when following the changing viewport matters. See [CSS Values and Units, viewport-relative lengths](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths).

### How should a layout adapt?

| Constraint | Starting point | Example |
|---|---|---|
| Component responds to the viewport | Media query | Change design tokens at a breakpoint |
| Component responds to its own available width | Container query | Reflow a card within a sidebar or grid |
| Repeating columns should fit content without a fixed breakpoint | Intrinsic Grid sizing | `repeat(auto-fit, minmax(...))` |

A content-driven card grid can fit as many columns as the available width allows:

```css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1rem;
}
```

A component can instead respond to the width of its query container:

```css
.card-grid { container-type: inline-size; }

@container (width > 28rem) {
  .card { display: grid; grid-template-columns: 1fr 2fr; }
}
```

For site-wide tokens, define the breakpoint in one place and reuse the values:

```css
:root { --columns: 1; --gap: 0.5rem; }

@media (min-width: 48rem) {
  :root { --columns: 2; --gap: 1rem; }
}

.cards {
  display: grid;
  grid-template-columns: repeat(var(--columns), minmax(0, 1fr));
  gap: var(--gap);
}
```

Use the available containing block for ordinary full-width content. A child with `width: 100vw` can overflow when the viewport width includes a classic scrollbar while the content box does not. Grid's track choice and intrinsic minimums are covered in [Flexbox and Grid layout](#20.%20Which%20CSS%20layout%20tool%20fits%20fixed%20and%20fluid%20content?%20/%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F).

### Constrained text and line clamping / 受限文本与行数裁切

For one line, keep the text on one line, clip overflow, and ask the browser to show an ellipsis. For a multiline excerpt, use a line-clamp form supported by the target browsers. Truncation changes what is visible, not the underlying text; ensure the full content remains available when users need to read or copy it. / 单行截断需要保持单行、裁切溢出，并让浏览器绘制省略号。多行摘要则使用目标浏览器支持的行数裁切语法并限制溢出。截断只改变可见内容，不会删除底层文本；若用户需要完整阅读或复制，应提供可访问的完整内容。

#### Single-line ellipsis

All three properties have distinct roles: `white-space` prevents wrapping, `overflow` clips the extra text, and `text-overflow` requests the ellipsis marker.

```css
.title {
  width: 100px; /* demonstration constraint; a parent may constrain production content */
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

The box also needs a constrained inline size, which can come from its parent layout. In a Flex or Grid item, `min-width: 0` may be needed so the item's intrinsic minimum does not force it wider than the available track. See [Flexbox and Grid layout](#20.%20Which%20CSS%20layout%20tool%20fits%20fixed%20and%20fluid%20content?%20/%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F).

#### Multiline clamp

When the target browsers still need the WebKit-compatible form, use a vertical box and an explicit line count.

```css
.excerpt {
  width: 100px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
```

CSS Overflow Level 4 defines the unprefixed `line-clamp` shorthand as well as the compatibility syntax. Choose the unprefixed form once it meets the project’s browser support target. Check the actual rendered behavior on overflowing and short content. [CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/#propdef-line-clamp)

`text-overflow` signals that inline content is clipped; it does not itself constrain the element's width or make multi-line clamping happen. For important text, provide a way to view the full value, preserve it in accessible text, and avoid using visual truncation as the only way to disclose essential information.

**Specification:** [CSS Overflow Module Level 4](https://www.w3.org/TR/css-overflow-4/).

### When does a CSS hairline mean one device pixel?

A `1px` border is one CSS pixel; the output can cover more than one device pixel depending on device-pixel ratio, zoom, OS scaling, and subpixel alignment. At an effective 2× scale, a half-CSS-pixel painted line is nominally one device pixel, but rasterization and alignment still vary. Treat fractional widths as a visual technique to test on target devices, not a physical-pixel guarantee.

```css
.box { position: relative; }

.box::before {
  content: "";
  position: absolute;
  inset-inline: 0;
  bottom: 0;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 100%;
}
```

For rounded edges, a fractional shadow is another technique to test:

```css
.box { box-shadow: 0 0 0 0.5px #d9d9d9; }
```

Both techniques depend on output scale and alignment. SVG also rasterizes to device pixels; it does not ensure a physical-pixel stroke.

**Specifications:** [CSS Values and Units Level 4](https://www.w3.org/TR/css-values-4/) defines reference pixels, font-relative and viewport-relative lengths; [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines `devicePixelRatio`; [CSS Containment Level 3](https://www.w3.org/TR/css-contain-3/#container-queries) defines size container queries; [CSS Grid Level 2](https://www.w3.org/TR/css-grid-2/) defines intrinsic track sizing.
## 20. Which CSS layout tool fits fixed and fluid content? / 固定与流动内容适合哪种 CSS 布局？

Use Flexbox for a one-dimensional row or column of items and Grid when rows and columns form a two-dimensional structure. For a fixed side with a fluid region, set the fixed track explicitly and make the flexible minimum shrinkable: for example, Grid's `minmax(0, 1fr)` or a Flex item with `min-width: 0`. Choose from the relationship among content, then define what should happen to overflow. / 一行或一列的项目优先考虑 Flexbox；需要同时安排行与列的二维结构时考虑 Grid。固定侧栏加流动区域时，明确固定轨道，并让弹性部分的最小值可以收缩，例如 Grid 的 `minmax(0, 1fr)` 或 Flex 子项的 `min-width: 0`。先根据内容关系选择布局，再规定溢出时如何处理。

| Layout problem | Good starting point | Why |
|---|---|---|
| Toolbar or row of items | Flexbox | One main axis, with optional wrapping |
| Page with fixed sidebars and a fluid center | Grid | The three column tracks are explicit |
| One fixed column and one fluid column | Grid or Flexbox | Both express the fixed/flexible relationship |
| Content of unknown size centered in a region | Grid or Flexbox | Alignment stays in normal flow |
| Legacy browser/layout constraints | Float, table, absolute, or inline-block patterns | Recognize their tradeoffs and existing formatting model |

### Fixed and fluid columns / 固定与流动列

For a fixed-width sidebar and flexible content, Grid makes the track relationship explicit. The HTML source order remains meaningful for reading and keyboard navigation:

~~~html
<div class="two-column">
  <aside>Navigation</aside>
  <main>Article content</main>
</div>

<div class="three-column">
  <aside>Left rail</aside>
  <main>Main content</main>
  <aside>Right rail</aside>
</div>
~~~

~~~css
.two-column {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 16px;
}
.two-column > main { min-width: 0; }
~~~

For a row of items, Flex expresses the same decision:

~~~css
.two-column { display: flex; gap: 16px; }
.two-column > aside { flex: 0 0 200px; }
.two-column > main { flex: 1; min-width: 0; }
~~~

For fixed side columns around a flexible center:

~~~css
.three-column {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) 100px;
  gap: 10px;
}
~~~

The middle region's min-content width can otherwise prevent it from shrinking around a long URL, word, or wide table. `min-width: 0` lets the item shrink; it does not decide whether descendants wrap, clip, or scroll. Give content a policy such as `overflow-wrap: anywhere` for long URLs or a scroll container for wide tables. In a column Flex layout the analogous block-axis constraint is often `min-height: 0`.

### Why can Flexbox and Grid still overflow? / Flexbox 与 Grid 为什么仍可能溢出？

Flex items and Grid tracks have intrinsic minimum sizing behavior. Long words, fixed-size descendants, and wide tables can contribute a content-based minimum larger than the available space. Lower the relevant minimum only when the design permits it; do not treat `min-width: 0` or `minmax(0, 1fr)` as automatic wrapping.

~~~css
.row { display: flex; }
.row > main { flex: 1; min-width: 0; }
.row > main img { max-width: 100%; }

.content-first-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 16rem;
}
.content-first-grid > main { min-width: 0; }
~~~

### Flexbox essentials / Flexbox 要点

`display: flex` or `inline-flex` makes direct children flex items arranged on a main axis and a perpendicular cross axis.

| Container property | Controls |
|---|---|
| `flex-direction` | Main-axis direction: row, row-reverse, column, column-reverse |
| `flex-wrap` | Whether items wrap |
| `justify-content` | Alignment/distribution along the main axis |
| `align-items` | Alignment within each line on the cross axis |
| `align-content` | Distribution of multiple flex lines when cross-axis space is available |
| `gap` | Space between items |

In a wrapping flex container, `align-content` aligns flex lines when extra cross-axis space exists and can affect a single line. In a `nowrap` container there is only one line, so `align-content` has no effect.

| Item property | Controls |
|---|---|
| `flex-grow` / `flex-shrink` / `flex-basis` | Growth, shrinking, and starting size |
| `flex` | Shorthand for grow, shrink, and basis |
| `align-self` | Cross-axis alignment of one item |
| `order` | Visual order without changing document order |

The shorthand and common values differ: `flex: 1` uses a zero basis and shares free space; `flex: auto` starts from the item's size; `flex: none` is inflexible. Do not assume every item can shrink below its minimum content size.

~~~css
.toolbar { display: flex; justify-content: space-between; gap: 1rem; }
.centered-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

### Grid essentials / Grid 要点

`display: grid` or `inline-grid` creates explicit or implicit row and column tracks.

| Container property | Controls |
|---|---|
| `grid-template-columns` / `grid-template-rows` | Track sizes |
| `grid-template-areas` | Named regions |
| `gap` | Space between tracks |
| `justify-items` / `align-items` / `place-items` | Item alignment inside cells |
| `justify-content` / `align-content` / `place-content` | Grid alignment inside the container |

Tracks can be fixed, flexible (`fr`), or content-sized (`min-content`, `max-content`, `auto`). `minmax(min, max)` sets lower and upper track sizing functions; `repeat(auto-fit, minmax(200px, 1fr))` creates responsive tracks. An `fr` track with an automatic minimum can still be held open by min-content contributions; use `minmax(0, 1fr)` when the design needs it to shrink below them, then choose a wrapping or overflow policy.

~~~css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr));
  gap: 16px;
}
~~~

The inner `min(100%, 250px)` lets the minimum fit a container narrower than 250px. Named areas can describe page structure:

~~~css
.page {
  display: grid;
  grid-template-columns: 200px 1fr;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
}
.page-header  { grid-area: header; }
.page-sidebar { grid-area: sidebar; }
.page-main    { grid-area: main; }
.page-footer  { grid-area: footer; }
~~~

Grid item properties include `grid-column`/`grid-row` placement and `justify-self`/`align-self` alignment.

For two-axis alignment in one region, use a [centering rule that works with unknown content size / 尺寸未知时的居中规则](#21.%20How%20do%20you%20center%20an%20element%20whose%20size%20is%20unknown?%20/%20%E5%A6%82%E4%BD%95%E5%B1%85%E4%B8%AD%E5%B0%BA%E5%AF%B8%E6%9C%AA%E7%9F%A5%E7%9A%84%E5%85%83%E7%B4%A0%EF%BC%9F).

### Legacy layout patterns / 旧式布局模式

Use these to understand existing layouts; choose Flex/Grid for ordinary new row, column, and page-structure work.

| Technique | Example pattern | Tradeoff |
|---|---|---|
| Float | `float: left` and `float: right` around a center with margins | Needs float containment/clearing and width math; see [BFC containment](#18.%20How%20does%20a%20block%20formatting%20context%20contain%20floats%20and%20margins?%20/%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F) |
| Table display | `display: table` / `table-cell` | Cell sizing couples content; visual display does not create semantic table markup |
| Absolute positioning | Fixed edges with a fluid center | Children leave normal flow; the parent does not grow around them |
| Inline-block | Two inline-block columns | Whitespace between elements can create a gap; legacy workarounds set parent font-size to 0 |

~~~css
/* Legacy 3-column float pattern; width math assumes normalized box sizing. */
.left { float: left; width: 100px; }
.right { float: right; width: 100px; }
.center { margin: 0 100px; width: calc(100% - 200px); }

/* Table-style 3-column layout. */
.table-layout { display: table; width: 100%; }
.table-layout > * { display: table-cell; }

/* Inline-block two-column layout; restore child text size. */
.inline-layout { font-size: 0; }
.inline-layout > * { display: inline-block; vertical-align: top; font-size: 1rem; }
~~~

Absolute positioning can also form fixed side columns around a center with matching margins and width math. Use it only when out-of-flow placement is intended.

Keep meaningful document order in the HTML. Flex `order`, reverse directions, and Grid placement change visual order without changing source or assistive-technology order; do not use them to repair incorrect content order.

**See also:** [Responsive CSS units and pixels](#19.%20Which%20CSS%20units%20and%20responsive%20layout%20rules%20fit%20the%20available%20space?%20/%20%E5%93%AA%E4%BA%9B%20CSS%20%E5%8D%95%E4%BD%8D%E4%B8%8E%E5%93%8D%E5%BA%94%E5%BC%8F%E5%B8%83%E5%B1%80%E8%A7%84%E5%88%99%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E7%A9%BA%E9%97%B4%EF%BC%9F) for container queries and viewport sizing; [Box sizing](#17.%20How%20does%20CSS%20calculate%20an%20element%27s%20box%20size?%20/%20CSS%20%E5%A6%82%E4%BD%95%E8%AE%A1%E7%AE%97%E5%85%83%E7%B4%A0%E7%9B%92%E5%AD%90%E7%9A%84%E5%B0%BA%E5%AF%B8%EF%BC%9F) for dimensions; [CSS position and stacking](#22.%20How%20do%20CSS%20positioning%20and%20stacking%20determine%20where%20an%20element%20appears?%20/%20CSS%20%E5%AE%9A%E4%BD%8D%E4%B8%8E%E5%A0%86%E5%8F%A0%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E5%85%83%E7%B4%A0%E7%9A%84%E6%98%BE%E7%A4%BA%E4%BD%8D%E7%BD%AE%EF%BC%9F) for out-of-flow placement.

**Specifications:** [CSS Flexible Box Layout](https://www.w3.org/TR/css-flexbox-1/) defines flex sizing and automatic minimum sizes; [CSS Grid Layout](https://www.w3.org/TR/css-grid-2/) defines track sizing and grid-item minimums; [CSS Display](https://www.w3.org/TR/css-display-3/#order-property) describes formatting contexts and visual reordering; checked 2026-11-05.
## 21. How do you center an element whose size is unknown? / 如何居中尺寸未知的元素？

**Short answer / 简答** — Put the alignment on a Grid or Flexbox parent when the child should take up space in normal flow. For an overlay, anchor it at the center of its containing block and move it back by half of its own width and height. / 子元素应参与正常流时，由 Grid 或 Flexbox 父容器负责对齐。浮层则先把左上角定位在包含块中心，再向回移动自身宽、高的一半。

### In normal flow / 保持正常流

Grid's `place-items: center` aligns a single grid item within its area. Flexbox's `justify-content` and `align-items` center a single flex item along the main and cross axes. Give the container enough space for the alignment to have an effect.

~~~html
<div class="center-grid"><div>Centered content</div></div>
~~~

~~~css
.center-grid { display: grid; place-items: center; }
~~~

~~~css
.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

### Overlay / 浮层

For an overlay, use absolute positioning to set the starting point and a transform to account for the element's own size.

~~~css
.overlay { position: relative; }
.overlay__content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
~~~

The insets refer to the containing block. The transform percentages refer to the element's own reference box, so the element can be centered without measuring it. The overlay does not contribute to the parent's normal-flow size.

### Older layouts / 旧式布局

For a fixed-size overlay, equal insets and auto margins distribute the available space. An older negative-margin variant subtracts half the known size from each coordinate.

~~~css
.overlay__fixed {
  position: absolute;
  width: 200px;
  height: 100px;
  inset: 0;
  margin: auto;
}
~~~

Table-cell layout can vertically align its contents with `vertical-align: middle`. Use it when maintaining an existing table-style layout. When centering a layout box, distinguish parent alignment from `text-align: center`, which aligns inline content inside a box.

**Related questions / 相关问题** — [Fixed and fluid layouts / 固定与流动布局](#20.%20Which%20CSS%20layout%20tool%20fits%20fixed%20and%20fluid%20content?%20/%20%E5%9B%BA%E5%AE%9A%E4%B8%8E%E6%B5%81%E5%8A%A8%E5%86%85%E5%AE%B9%E9%80%82%E5%90%88%E5%93%AA%E7%A7%8D%20CSS%20%E5%B8%83%E5%B1%80%EF%BC%9F), [positioning and stacking / 定位与堆叠](#22.%20How%20do%20CSS%20positioning%20and%20stacking%20determine%20where%20an%20element%20appears?%20/%20CSS%20%E5%AE%9A%E4%BD%8D%E4%B8%8E%E5%A0%86%E5%8F%A0%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E5%85%83%E7%B4%A0%E7%9A%84%E6%98%BE%E7%A4%BA%E4%BD%8D%E7%BD%AE%EF%BC%9F), [float containment / 包含浮动](#18.%20How%20does%20a%20block%20formatting%20context%20contain%20floats%20and%20margins?%20/%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F), [CSS triangles / CSS 三角形](#A%20triangle%20from%20border%20geometry%20/%20%E7%94%A8%E8%BE%B9%E6%A1%86%E5%87%A0%E4%BD%95%E7%94%BB%E4%B8%89%E8%A7%92%E5%BD%A2), [high-DPR hairlines / 高 DPR 细线](#When%20does%20a%20CSS%20hairline%20mean%20one%20device%20pixel?).

**Sources / 来源** — [CSS Box Alignment §7.3](https://www.w3.org/TR/css-align-3/#place-items-property), [CSS Positioned Layout §4.2](https://www.w3.org/TR/css-position-3/#abspos-margins), [CSS Transforms §6](https://www.w3.org/TR/css-transforms-1/#transform-box).
## 22. How do CSS positioning and stacking determine where an element appears? / CSS 定位与堆叠如何决定元素的显示位置？

Positioning answers where a box is anchored and whether it occupies normal-flow space; stacking contexts answer which painted group is in front. `relative` and `sticky` preserve the element's flow slot, while `absolute` and `fixed` remove it from normal flow. A large `z-index` only competes inside its stacking context, so coordinates, flow, and paint order must be debugged separately. / 定位决定盒子的锚点及其是否占据普通流空间；堆叠上下文决定绘制的分组谁在前。`relative` 和 `sticky` 保留元素的流位置，`absolute` 和 `fixed` 则脱离普通流。很大的 `z-index` 也只在自身堆叠上下文内参与排序，因此应分别排查坐标、文档流和绘制顺序。

### Position values

| Value | In normal flow? | Position reference | Typical scroll behavior |
|---|---|---|---|
| `static` | Yes | Normal flow; inset offsets do not apply | Moves with document |
| `relative` | Yes; original space stays reserved | Its normal-flow position | Moves with document |
| `absolute` | No | Nearest ancestor establishing an absolute-position containing block; otherwise initial containing block | Follows that containing block |
| `fixed` | No | Nearest fixed-position containing block, often the viewport | Stays at that containing block as document scrolls |
| `sticky` | Yes | Nearest scrollport in the inset axis, constrained by its containing block | Moves until constrained by sticky inset |

`relative` offsets the box visually without moving siblings. It also establishes an absolute-position containing block for descendants:

```css
.card { position: relative; }
.card__badge { position: absolute; inset-block-start: 0; inset-inline-end: 0; }
```

An ancestor with non-`static` positioning commonly establishes the absolute containing block. Other properties, including some transforms and containment values, can establish containing blocks too. A fixed element usually tracks the viewport, but an ancestor with transform, perspective, filter, or relevant containment/`will-change` values can establish a fixed-position containing block; a supposedly fixed descendant may then move with that ancestor.

`sticky` remains in flow and sticks relative to the nearest scrollport when an inset such as `top: 0` is set. An ancestor's overflow can establish the relevant scroll container even when it does not visibly scroll, so inspect the scroll-container chain if sticky behavior differs from expectation. The containing block limits how far the sticky box can move.

### Stacking contexts and `z-index`

Within a stacking context, stacking rules order its child contexts. A descendant cannot use a larger `z-index` to escape the ancestor context and compete directly with an outside sibling.

```css
.shell { position: relative; z-index: 1; }
.dialog { position: absolute; z-index: 9999; }
.other { position: relative; z-index: 2; }
```

Here `.dialog` remains inside `.shell`'s stacking context; the outside `.other` context can paint above the whole shell. Raise the relevant ancestor's stacking position or move the dialog to a context that can compete at the needed level.

A positioned box with a non-`auto` `z-index` creates a stacking context. Fixed and sticky boxes also create one. Other common context creators include opacity below 1, transforms, filters, isolation, and some containment or `will-change` values. Check the property's own rules before assuming a stacking or containing-block effect.

| Question | Relevant model |
|---|---|
| Why did this sibling move or overlap? | Normal flow and containing blocks |
| Why did this large z-index stay underneath? | Stacking-context hierarchy |
| Why did a float not increase its parent's height? | Block formatting context; see [BFC and flow containment](#18.%20How%20does%20a%20block%20formatting%20context%20contain%20floats%20and%20margins?%20/%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F) |

**Specification:** [CSS Positioned Layout Level 3](https://www.w3.org/TR/css-position-3/) defines position, insets, sticky scrollports, and stacking behavior. See [BFC and flow containment](#18.%20How%20does%20a%20block%20formatting%20context%20contain%20floats%20and%20margins?%20/%20%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87%E5%A6%82%E4%BD%95%E7%BA%A6%E6%9D%9F%E6%B5%AE%E5%8A%A8%E5%92%8C%E5%A4%96%E8%BE%B9%E8%B7%9D%EF%BC%9F) for the separate flow boundary; [CSS visibility](#23.%20What%20changes%20when%20an%20element%20is%20visually%20hidden%20with%20CSS?%20/%20%E7%94%A8%20CSS%20%E9%9A%90%E8%97%8F%E5%85%83%E7%B4%A0%E6%97%B6%E4%BC%9A%E5%8F%91%E7%94%9F%E4%BB%80%E4%B9%88%E5%8F%98%E5%8C%96%EF%BC%9F) for hidden-state effects; [CSS transitions and animations](#24.%20When%20should%20CSS%20use%20a%20transition%20or%20a%20keyframe%20animation?%20/%20CSS%20%E5%BA%94%E5%9C%A8%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20transition%20%E6%88%96%E5%85%B3%E9%94%AE%E5%B8%A7%E5%8A%A8%E7%94%BB%EF%BC%9F) for motion and profiling; and [rendering pipeline and forced layout](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F) when a style change affects layout or paint.
## 23. What changes when an element is visually hidden with CSS? / 用 CSS 隐藏元素时会发生什么变化？

Choose a hiding method by the state users should experience. `display: none` removes the box from layout and generally from the accessibility tree; `visibility: hidden` keeps layout space but suppresses visibility; `opacity: 0` makes a rendered box transparent while it can still receive focus and pointer input. Fading is only visual: also manage focus, input, and accessible state while the element is hidden. / 根据用户应体验的状态选择隐藏方式。`display: none` 会从布局中移除盒子，通常也从无障碍树中移除；`visibility: hidden` 保留布局空间但隐藏可见性；`opacity: 0` 让已布局的盒子透明，但它仍可能接收焦点和指针输入。淡出只改变视觉效果；元素隐藏时还要管理焦点、输入和无障碍状态。

| Behavior | `display: none` | `visibility: hidden` | `opacity: 0` |
|---|---|---|---|
| Layout space | Removed | Reserved | Reserved |
| Pointer activation | No rendered box to hit | Hidden | Can still receive input; pair with a deliberate input policy |
| Keyboard focus | Not focusable while hidden | Not focusable while hidden | May remain focusable |
| Accessibility tree | Generally omitted | Generally omitted | Usually remains exposed; inspect control semantics |
| Visual interpolation | Display changes discretely | Visibility changes discretely | Opacity interpolates |
| Children | Not rendered | Inherit hidden visibility, though a child may override it | Paint as one group; a child cannot undo parent transparency |

The element's opacity is not inherited, but opacity composites the element and its descendants as a group. A child set to `opacity: 1` cannot make itself visible through a parent at zero opacity.

```css
.is-removed { display: none; }
.is-space-preserved { visibility: hidden; }
.is-faded-out { opacity: 0; pointer-events: none; }
```

`pointer-events: none` does not remove an element from keyboard focus or the accessibility tree. When a dialog or menu closes, also move or restore focus and update its accessible state; do not rely on opacity alone to make the control unavailable.

### Can `display` transition while showing an element?

`display` is not interpolated like opacity. CSS Transitions can opt into a discrete display transition in supporting browsers. A starting style defines the entry state, and `transition-behavior: allow-discrete` enables the discrete transition:

```css
.panel {
  display: none;
  opacity: 0;
  transition: opacity 180ms ease, display 180ms allow-discrete;
}

.panel.is-open {
  display: block;
  opacity: 1;
}

@starting-style {
  .panel.is-open {
    opacity: 0;
  }
}
```

Check target-browser support. Move focus and update accessible state as soon as the close action occurs; do not leave a transparent control interactive while waiting for `display` to switch. For a reduced-motion preference, shorten or remove nonessential movement and fades.

**Specifications:** [CSS Display](https://www.w3.org/TR/css-display-3/), [CSS Color transparency](https://www.w3.org/TR/css-color-4/#transparency), [CSS Transitions Level 2](https://www.w3.org/TR/css-transitions-2/#transition-behavior-property), and [Media Queries: reduced motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion).
## 24. When should CSS use a transition or a keyframe animation? / CSS 应在何时使用 transition 或关键帧动画？

A transition interpolates between two computed states after a property change, such as a hover or class toggle. A keyframe animation defines a sequence that can start independently, repeat, reverse, pause, or fill after its last keyframe. Prefer a transition for a simple state change; use keyframes for a multi-step or looping sequence. Respect reduced-motion preferences, and profile the actual effect instead of assuming a property is free to animate. / transition 在属性变化后于两个计算状态之间插值，例如 hover 或 class 切换。关键帧动画定义一段可独立启动、重复、反向、暂停或保留结束状态的序列。简单状态变化优先 transition；多阶段或循环序列使用关键帧。尊重减少动态效果偏好，并针对真实效果做性能分析，不要假定某属性动画没有成本。

### Transitions: move between states

```css
.button {
  background-color: navy;
  transition: background-color 180ms ease-out;
}

.button:hover {
  background-color: royalblue;
}
```

| Property | Role |
|---|---|
| `transition-property` | Which properties to transition, such as `opacity` or `transform` |
| `transition-duration` | Length of the interpolation |
| `transition-timing-function` | Easing curve, such as `ease-out` or `cubic-bezier(...)` |
| `transition-delay` | Wait before starting |

When multiple properties use different durations or delays, list their values in corresponding order:

```css
.card {
  transition-property: transform, opacity;
  transition-duration: 300ms, 200ms;
  transition-timing-function: ease-out, linear;
  transition-delay: 0ms, 100ms;
}
```

### Keyframes: define intermediate motion

```css
@keyframes slide-in {
  0%   { transform: translateX(-100%); }
  50%  { transform: translateX(10%); }
  100% { transform: translateX(0); }
}

.panel {
  animation: slide-in 420ms ease-out both;
}
```

| Property | Role |
|---|---|
| `animation-name` | Select the `@keyframes` rule |
| `animation-duration` | Length of one cycle |
| `animation-timing-function` | Easing for the cycle or keyframe segment |
| `animation-delay` | Wait before the first cycle |
| `animation-iteration-count` | Number of cycles or `infinite` |
| `animation-direction` | `normal`, `reverse`, `alternate`, or `alternate-reverse` |
| `animation-fill-mode` | Whether keyframe values apply before/after active motion |
| `animation-play-state` | `running` or `paused` |

CSS transforms can translate, rotate, and scale a box:

| Function | Effect |
|---|---|
| `translate(x, y)`, `translateX(x)`, `translateY(y)` | Move in 2D |
| `translateZ(z)`, `rotateX/Y/Z(angle)` | Move or rotate in 3D |
| `rotate(angle)` | Rotate in 2D |
| `scale(x, y)`, `scaleX(x)`, `scaleY(y)` | Resize visually |

```css
.card { transform: translate(10px, 20px) rotate(5deg) scale(1.05); }
```

### What does animation cost?

A change can require style recalculation, layout, paint, rasterization, and compositing. Animating `transform` or `opacity` can let an engine update presentation without repeating layout, but neither guarantees compositor-only or GPU work. Consult a trace and the [rendering pipeline](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F) for the observed invalidation path.

`will-change` is a hint, not a command to promote a layer. Some hints can consume memory or change stacking/containing-block behavior. Use it only on a small region after profiling shows it helps, then remove the hint when no longer needed. `transform: translateZ(0)` is not a universal GPU switch and may affect stacking and containing blocks.

```css
@media (prefers-reduced-motion: reduce) {
  .panel,
  .card {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
    transition-duration: 0.01ms;
  }
}
```

This example reduces duration for selected motion. Choose a treatment that preserves necessary state feedback and avoids unexpected movement; not all motion should be removed indiscriminately.

**Specifications:** [CSS Transitions Level 2](https://www.w3.org/TR/css-transitions-2/), [CSS Animations Level 1](https://www.w3.org/TR/css-animations-1/), [CSS Transforms Level 1](https://www.w3.org/TR/css-transforms-1/), [CSS Will Change](https://www.w3.org/TR/css-will-change-1/), and [Media Queries: reduced motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion).
## 25. Which DOM geometry API answers which measurement question? / 哪个 DOM 几何 API 能回答哪种测量问题？

These DOM APIs measure different boxes and coordinate spaces. Use `offset*` values for integer, untransformed layout dimensions; `client*` for the inner padding area; `scroll*` for scrolling extent and position; and `getBoundingClientRect()` for a transformed viewport-relative rectangle. A read may force pending style or layout work to finish, but does not necessarily cause a new layout when the measurements are already current. / 这些 DOM API 测量的盒子和坐标空间不同。`offset*` 提供整数、未变换的布局尺寸；`client*` 提供内侧 padding 区域；`scroll*` 提供滚动范围和位置；`getBoundingClientRect()` 提供相对于视口且受变换影响的矩形。读取可能迫使尚未完成的样式或布局工作同步完成，但如果测量值已经是最新的，不一定会触发新布局。

```text
┌─────────────────────────── margin ───────────────┐
│ ┌───────────────────── border ────────────────┐  │
│ │ ┌────────────── padding ────────────────┐   │  │
│ │ │ ┌────────── content ────────────────┐ │   │  │
│ │ │ │                                   │ │   │  │
│ │ │ └───────────────────────────────────┘ │   │  │
│ │ └───────────────────────────────────────┘   │  │
│ └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Quick comparison

| Property | Includes | Excludes or caveat | Writable? |
|---|---|---|---|
| `offsetHeight` / `offsetWidth` | Border box; ordinarily a rendered scrollbar | Margin; ignores transforms; integer CSS px | No |
| `clientHeight` / `clientWidth` | Padding area | Border and rendered scrollbar; integer CSS px | No |
| `scrollHeight` / `scrollWidth` | Scrolling area, including overflow | Border; integer CSS px; not a guarantee the content is user-scrollable | No |
| `scrollTop` / `scrollLeft` | Current scroll offset | Values may be fractional or outside usual range in some layouts | Yes |
| `offsetTop` / `offsetLeft` | Offset from `offsetParent` padding edge to element border edge | Not necessarily relative to the direct parent | No |
| `getBoundingClientRect()` | Viewport-relative union of transformed border-box fragments | Excludes margin; a snapshot | No |

Dimensions are in CSS pixels, not device pixels. Scrollbars differ by platform: a rendered scrollbar consumes layout space on some configurations but overlays content on others. Do not derive a physical-device-pixel measurement from these values.

### Choose by the box or coordinate space

#### Layout box and inner client area

`offsetHeight` and `offsetWidth` return integer layout dimensions for the border box, normally including a rendered scrollbar and excluding margin. They ignore CSS transforms.

```text
offsetHeight ≈ content height + padding + border (+ rendered scrollbar)
```

`clientHeight` and `clientWidth` return the padding area minus a rendered scrollbar; the border and margin are excluded. In standards mode, the root element's client dimensions correspond to the viewport dimensions.

```text
clientHeight ≈ content height + padding - rendered scrollbar
```

#### Scrolling area and current offset

`scrollHeight` measures the scrolling area, including content outside the visible client area. It can exceed `clientHeight` when content overflows. In standards mode, the root element's `scrollHeight` is the maximum of the viewport scrolling-area height and viewport height.

```javascript
const hasOverflow = element.scrollHeight > element.clientHeight;
const y = element.scrollTop;
element.scrollTop = 0; // scroll to the top
```

`scrollTop` and `scrollLeft` are writable. Reverse-direction scrolling and elastic overscroll can produce values outside the familiar range, so avoid assuming every result is a nonnegative integer.

#### Position relative to the offset parent

`offsetTop` and `offsetLeft` measure from the element's border edge to the padding edge of its `offsetParent`. The offset parent is not simply the nearest positioned ancestor: tables, containing blocks, fixed positioning, zoom, shadow-tree boundaries, and missing boxes can affect which element is returned. Some elements, including `body` in common cases, return zero.

#### Viewport-relative visual rectangle

`getBoundingClientRect()` returns the smallest rectangle enclosing the element's nonempty client rects, relative to the viewport. It includes CSS transforms. Fragmented inline content can produce several client rects; this method returns their union. Its result is a snapshot, not a live object.

```javascript
const rect = element.getBoundingClientRect();
// rect.top / bottom: distance from viewport top to each edge
// rect.left / right: distance from viewport left to each edge
// rect.width / height: transformed border-box union in CSS px
```

A basic viewport-overlap check is:

```javascript
function overlapsViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top < window.innerHeight &&
    rect.bottom > 0 &&
    rect.left < window.innerWidth &&
    rect.right > 0
  );
}
```

This checks rectangle overlap, not whether the element is occluded, transparent, or exposed to assistive technology. Decide separately how zero-area rectangles should behave.

### Measurement without repeated layout work

For an occasional measurement, choose the API whose box and coordinate system match the task. For threshold-based visibility such as lazy loading or analytics, prefer [IntersectionObserver](#26.%20How%20should%20a%20browser%20page%20lazy-load%20images%20without%20hurting%20LCP%20or%20layout%20stability?%20/%20%E5%A6%82%E4%BD%95%E5%BB%B6%E8%BF%9F%E5%8A%A0%E8%BD%BD%E5%9B%BE%E7%89%87%E8%80%8C%E4%B8%8D%E6%8D%9F%E5%AE%B3%20LCP%20%E6%88%96%E5%B8%83%E5%B1%80%E7%A8%B3%E5%AE%9A%E6%80%A7%EF%BC%9F) over repeatedly polling geometry. It reports asynchronously and is not a blanket guarantee that no layout work occurs.

A write followed by a geometry read can force pending layout; alternating writes and reads in a loop can repeat that work. See [Rendering pipeline and forced layout](#11.%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%B8%80%E6%AC%A1%20DOM%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E5%A2%9E%E5%8A%A0%E5%B8%83%E5%B1%80%E6%88%96%E7%BB%98%E5%88%B6%E5%B7%A5%E4%BD%9C%EF%BC%9F) for the read/write batching example.

**Specifications:** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines these geometry APIs, including the [root `scrollHeight` rule](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight); [Intersection Observer](https://www.w3.org/TR/intersection-observer/) defines asynchronous intersection notifications.
## 26. How should a browser page lazy-load images without hurting LCP or layout stability? / 如何延迟加载图片而不损害 LCP 或布局稳定性？

For an ordinary off-screen image, prefer native `loading="lazy"` with a real `src` or `srcset`; the browser chooses its deferral threshold. Reserve the image's aspect ratio with `width`/`height` or CSS `aspect-ratio`. Use `IntersectionObserver` only when loading needs a custom root, threshold, or non-image action, and do not defer an image likely to be the page's LCP element. / 普通视口外图片优先使用带真实 `src` 或 `srcset` 的原生 `loading="lazy"`，由浏览器决定何时开始加载。通过 `width`/`height` 或 CSS `aspect-ratio` 预留图片纵横比。只有需要自定义 root、阈值或执行非图片操作时才使用 `IntersectionObserver`，且不要延迟可能成为页面 LCP 元素的图片。

### Native lazy loading / 原生懒加载

~~~html
<img src="image.jpg" alt="Description" loading="lazy" width="800" height="600">
~~~

`lazy` asks the user agent to defer fetching until its visibility conditions are met; `eager` requests without lazy deferral. A `data-src` attribute alone is not a loading source: the element needs `src` or `srcset`. Browser-selected thresholds vary by implementation. Intrinsic dimensions let the browser reserve the aspect ratio before bytes arrive; CSS can still change the rendered size.

### Custom loading with Intersection Observer / 用观察器自定义加载

Use an observer for behavior the native attribute does not expose, such as a custom root margin, threshold, or work beyond an image request. It queues intersection changes; it does not promise that the callback runs off the main thread.

~~~html
<img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="actual-image.jpg" alt="Description" width="800" height="600">
~~~

~~~javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const img = entry.target;
    img.src = img.dataset.src;
    img.removeAttribute("data-src");
    observer.unobserve(img);
  });
}, { rootMargin: "200px" });

document.querySelectorAll("img[data-src]").forEach((img) => observer.observe(img));
// On teardown, call observer.disconnect() when this page/component owns the observer.
~~~

A positive `rootMargin` can begin work before the target reaches the root. `threshold: 0` has an edge-adjacent case: an intersecting target can have a zero-area intersection rectangle, so `isIntersecting` does not mean at least one pixel is visible. Do not use that flag as a visibility or occlusion test.

### Legacy scroll fallback / 旧环境滚动回退

Use a scroll/resize fallback only when the required target browser lacks `IntersectionObserver`. It reads viewport geometry and should be throttled; geometry reads can force pending layout when state is dirty, but do not necessarily do so. See [DOM geometry APIs](#25.%20Which%20DOM%20geometry%20API%20answers%20which%20measurement%20question?%20/%20%E5%93%AA%E4%B8%AA%20DOM%20%E5%87%A0%E4%BD%95%20API%20%E8%83%BD%E5%9B%9E%E7%AD%94%E5%93%AA%E7%A7%8D%E6%B5%8B%E9%87%8F%E9%97%AE%E9%A2%98%EF%BC%9F) for the exact box and coordinate returned, and [Debounce and throttle / 防抖与节流](#63.%20When%20should%20a%20UI%20use%20Lodash%20instead%20of%20a%20native%20JavaScript%20operation?%20/%20%E7%95%8C%E9%9D%A2%E4%BD%95%E6%97%B6%E5%BA%94%E4%BD%BF%E7%94%A8%20Lodash%20%E8%80%8C%E4%B8%8D%E6%98%AF%E5%8E%9F%E7%94%9F%20JavaScript%EF%BC%9F) for rate-limiting options.

~~~javascript
function checkImages() {
  document.querySelectorAll("img[data-src]").forEach((img) => {
    const rect = img.getBoundingClientRect();
    if (rect.bottom > 0 && rect.top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute("data-src");
    }
  });
}

let checkScheduled = false;
function scheduleImageCheck() {
  if (checkScheduled) return;
  checkScheduled = true;
  setTimeout(() => {
    checkScheduled = false;
    checkImages();
  }, 100);
}

window.addEventListener("scroll", scheduleImageCheck, { passive: true });
window.addEventListener("resize", scheduleImageCheck, { passive: true });
checkImages();
~~~

### Protect loading speed and visual stability / 保护加载速度与视觉稳定性

Do not blindly lazy-load the first visible or likely LCP image: delaying its fetch can increase LCP. Reserve image space using intrinsic dimensions or an aspect ratio to reduce layout shift; choose an appropriate responsive candidate with `srcset`/`sizes`, rather than loading an oversized source. A placeholder can avoid a blank region but does not replace dimension reservation. Measure the actual route and device; see [browser performance measurement](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F) and the [URL-to-pixels path](#1.%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E7%AC%AC%E4%B8%80%E5%B8%A7%EF%BC%9F).

**Standards / 规范：** [WHATWG image element and source requirements](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element); [WHATWG lazy-loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes); [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/); [CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/), checked 2026-11-05.
## 27. When should small images be combined into a CSS sprite? / 何时应把多个小图片合并为 CSS Sprite？

A CSS sprite places several small images in one file and reveals each image with a fixed-size element and `background-position`. It can reduce separate image requests in some delivery setups, but couples cache invalidation and coordinates: changing one icon replaces the combined asset. With HTTP/2 multiplexing, request count alone is not enough reason to create a sprite; compare transfer bytes, cache reuse, and maintenance cost for the actual assets. / CSS Sprite 把多个小图放进一个文件，再通过固定尺寸元素和 `background-position` 显示其中一块。它在某些传输方式下可以减少独立图片请求，但会把缓存失效与坐标耦合起来：改动一个图标就要替换整个合并资源。HTTP/2 支持多路复用，仅凭请求数量不足以决定是否合并；应结合实际资源的传输字节、缓存复用和维护成本比较。

```css
.icon-edit {
  width: 16px;
  height: 16px;
  background-image: url("/icons.png");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
```

The offset exposes the desired sprite rectangle. Centralize coordinates or generate them as part of asset processing when the sprite has many entries. An independently cached icon can be a better fit when it changes often or is used on routes that should not download the full sprite.

HTTP/2 multiplexes streams over a connection, so multiple assets need not imply one connection per image. That does not make every request free or settle the trade-off: measure the emitted files and cache behavior. See [HTTP protocols and caching](../../engineering-foundations/networking/http-protocols-and-websockets.md) for the shared transport explanation.

**References:** [CSS Backgrounds and Borders: background positioning](https://www.w3.org/TR/css-backgrounds-3/#the-background-position), [HTTP/2 RFC 9113, streams and multiplexing](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing).
## 28. JavaScript 值如何转换、比较，并成为属性键？

报表结果里，金额 0、缺失的数组位置、两个字段相同的记录，看起来都像“没有数据”或“同一条记录”；JavaScript 会按不同规则处理它们。本章从一次结果导入开始，先分清值与对象身份，再说明比较和属性键转换。后续章节沿用这组输入：

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

业务字段 reportId 相同，表示两条输入记录描述同一业务实体；first 与 retry 仍是两个对象。它们的 owner 字段也指向内容相同、身份不同的对象。

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

对普通值，`Boolean(value)` 与 `!!value` 都执行真值转换。

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

浏览器里的历史对象 `document.all` 是例外：它带有标准附录定义的特殊行为，`Boolean(document.all)` 为 `false`，`typeof document.all` 为 `"undefined"`，且 `document.all == null` 为 `true`。这不是普通对象的真值规则，业务代码不应依赖它。

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

5 == "5";              // true
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

### 变量保存对象身份，不会自动复制对象

把对象赋给新变量后，两个绑定仍指向同一个对象。属性赋值会先求出并记录左侧的基对象，再求右侧；右侧即使重新绑定变量，也不会改变已记录的基对象。

~~~javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }：写入落在先前记录的旧对象上
~~~

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

~~~javascript
const dictionary = {};
dictionary[123] = "number key";
dictionary["123"]; // "number key"

const accountKey = {
  [Symbol.toPrimitive]: () => "account",
};
dictionary[accountKey] = "Ada";
dictionary.account; // "Ada"

dictionary[first] = "first object";
dictionary[retry]; // "first object"：两个对象默认都转成 "[object Object]"
~~~

如果键需要保持对象身份、数字与字符串必须区分，或需要任意类型的键，使用 `Map`。若普通对象确实是字典，可用 `Object.create(null)` 去掉继承原型行为，并用 `Object.hasOwn` 检查自有属性。键值集合的选择见[何时使用 Map、Set 或普通对象？](#29.%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F)。

### 枚举与复制属性时，先看 API 选中了什么

`Object.keys`、`Object.values` 和 `Object.entries` 读取对象的自有、可枚举、字符串键属性；`Symbol` 键不在结果中。普通对象的数组索引键先按数值升序排列，其他字符串键按创建顺序排列；`Proxy` 和特殊对象可能有不同的键顺序。`for...in` 还会遍历可枚举的继承字符串键，因此对象数据和数组索引应选不同的遍历方式。

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

读取嵌套字段时，optional chaining（可选链）运算符 `?.` 只在紧邻值为 `null` 或 `undefined` 时停止，不把 `0`、`false` 或空字符串当成缺失。根变量本身若未声明，使用 `?.` 仍会抛 `ReferenceError`；用括号结束一段链后，括号外的普通属性读取也不再受短路保护。

~~~javascript
const report = { profile: null, rows };
report.profile?.name; // undefined
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

destructuring（解构）把属性或可迭代值绑定到局部变量。默认初始化仅在读到 `undefined` 时运行，所以不会覆盖合法零值、`false`、空字符串或 `null`。对象剩余项收集来源对象余下的自有可枚举属性，但只复制一层；数组解构按迭代器取值，空位读成 `undefined`，而省略绑定仍会向前消费一个值。

~~~javascript
const { amount: firstAmount = 100, owner: firstOwner, ...rowFields } = first;
// firstAmount 是 0；firstOwner 仍是 first.owner；rowFields 只创建浅层新对象

const { profile = { name: "Guest" } } = report;
profile; // null：默认值只处理 undefined

const [firstRow, , ...tail] = rows;
firstRow === first; // true
tail[0] === retry; // true：rest 收集剩余项，形成新数组
1 in rows; // false：被省略的项对应空位
~~~

数组解构和数组展开同样消费迭代器，空位的其他读取结果见[数组空位如何改变遍历结果？](#%E7%A9%BA%E4%BD%8D%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E9%81%8D%E5%8E%86%E7%BB%93%E6%9E%9C)；同一个属性是否缺失或显式为 `undefined`，也不能只靠读取结果区分。

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
> - 严格相等、SameValue、SameValueZero 和 ToPropertyKey：[ECMAScript 2026 §7.2.9–7.2.14、§7.1.19](https://tc39.es/ecma262/2026/multipage/abstract-operations.html)。
> - `document.all` 的历史例外：[ECMAScript 2026 Annex B IsHTMLDDA internal slot](https://tc39.es/ecma262/2026/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。
> - `instanceof` 与 `Object.prototype.toString` 的检查行为：[ECMAScript 2026 §13.10.2 InstanceofOperator](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-instanceofoperator)、[§20.1.3.6 Object.prototype.toString](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.prototype.tostring)。
> - Object.keys / values / entries 与 Object.assign 的属性范围：[ECMAScript 2026 §20.1.2](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html)；普通对象的键顺序：[§10.1.11.1 OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)。
> - 可选链与空值合并的短路条件、运算优先级：[ECMAScript 2026 §13.3.9 Optional Chains](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-optional-chains) 与 [§13.13 Binary Logical Operators](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-binary-logical-operators)。
> - 对象与数组解构默认值、剩余项和迭代读取：[ECMAScript 2026 §14.3.3 Destructuring Binding Patterns](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-destructuring-binding-patterns)；数组迭代器：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - 带标签模板调用参数的组成：[ECMAScript 2026 §13.3.11 Tagged Templates](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-tagged-templates)。
> - React 条件渲染中 0 会作为结果呈现：[React 文档 Conditional Rendering](https://react.dev/learn/conditional-rendering)，访问于 2026-11-06。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
## 29. 何时使用 Map、Set 或普通对象？

报表导入有一列是业务记录，有些记录可能重试；程序既要用 `Map`（映射）按 `reportId` 找最新值，也要为某个对象实例保存临时状态。选择数据结构前，先确定“相同”指什么、键需要什么类型，以及数据是否要按插入顺序遍历。对象字段与身份的比较规则见[JavaScript 值如何转换、比较，并成为属性键？](#28.%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%EF%BC%8C%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F)。

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

### 先按数据形状选择

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Map`（映射） | 任意键值对、对象身份键、需要直接遍历或 `size` | 键可以是任意值；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员或反复进行成员查询 | 按插入顺序保存；成员按相等规则去重 |
| `Array`（数组） | 有位置、重复项或要按索引访问的数据 | 每个位置独立，即使值相同也可重复 |
| 普通对象 | 固定字段的记录，或确实需要字符串 / `Symbol` 属性键的字典 | 其他键会先转成字符串或 `Symbol`；普通原型行为仍然存在 |

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

const selectedRows = new Set([first, retry]);
selectedRows.size; // 2：对象身份不同
~~~

常用操作是 `add`、`has`、`delete`、`clear` 和 `size`。`keys()` 与 `values()` 产出相同成员；`entries()` 为 `Map` 兼容性产出 `[value, value]`；`forEach` 的参数为 `(value, value, set)`。

ECMAScript 2025 标准化 `Set` 的 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。参数可以是类 Set 对象：至少提供 `size`、`has()` 和 `keys()`；例如 `Map` 可按键参与这些运算。调用方法的接收者仍必须是 `Set`。面向旧运行时仍需检查支持。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true
~~~

### 普通对象仍适合固定字段与字典

记录 `{ reportId, amount, owner }` 的属性有固定名称时，用普通对象表达最清楚。若把对象当作任意键字典，必须记住属性键转换：对象键一般转成字符串，数字 `123` 和字符串 `"123"` 会撞到同一个属性；`Object.create(null)` 仅去掉继承原型，不会改变键转换。

~~~javascript
const dictionary = Object.create(null);
dictionary[123] = "number";
dictionary["123"]; // "number"

const record = { reportId: "r-104", amount: 0 };
Object.hasOwn(record, "amount"); // true
Object.hasOwn(record, "toString"); // false
~~~

`Object.hasOwn` 可区分自有和继承属性，也不会因对象覆盖了 `hasOwnProperty` 而失效。需要精确说明哪些属性可枚举、如何复制，请看[JavaScript 值如何转换、比较，并成为属性键？](#%E6%9E%9A%E4%B8%BE%E4%B8%8E%E5%A4%8D%E5%88%B6%E5%B1%9E%E6%80%A7%E6%97%B6%EF%BC%8C%E5%85%88%E7%9C%8B%20API%20%E9%80%89%E4%B8%AD%E4%BA%86%E4%BB%80%E4%B9%88)。

### 成本和生命周期也属于选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小为次线性，但不规定具体哈希表或常数时间实现。总体成本还取决于外围算法：如果过滤 n 个数组项时每次都新建同一张查找表，建表成本会被重复支付。需要比较数组去重、批量移除和排序的结果时，见[数组操作怎样处理空位与复制？](#30.%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E4%B8%8E%E5%A4%8D%E5%88%B6%EF%BC%9F)。

普通 `Map` 强持有键和值，`Set` 强持有成员，直到删除条目或集合自身不再可达。对象实例的元数据若不应延长键对象寿命，可考虑 `WeakMap`（弱映射）；它不提供遍历、`size` 或确定的清理时间，详见[弱集合与弱引用能保证什么？](#40.%20%E5%BC%B1%E9%9B%86%E5%90%88%E4%B8%8E%E5%BC%B1%E5%BC%95%E7%94%A8%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - Map / Set 的插入顺序、SameValueZero 和集合运算：[ECMAScript 2026 §24.1–24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - Map / Set 平均访问时间的规范下限：[ECMAScript 2026 §24.1–24.2 implementation requirements](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；类 Set 参数的读取方式：[GetSetRecord](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-getsetrecord)。
> - SameValueZero 的定义：[ECMAScript 2026 §7.2.10](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
## 30. JavaScript 数组操作如何处理空位、修改与复制？

报表结果既可能包含同一业务记录的重复输入，也可能因上游筛选留下稀疏位置。数组操作的结果取决于它读取的是值还是存在的索引、是否修改原数组，以及复制时是否只复制一层。本章复用同一组输入；第二个位置是刻意保留的空位，第三个位置是重复业务 `id` 的更新记录：

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

普通业务结果通常应使用稠密数组；这个空位用于辨别 JavaScript 操作的迭代契约。空位、显式 `undefined` 和数组迭代器返回的 `undefined` 不是同一个结构状态。

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

记录若按业务字段判重，用 `Map` 把字段映射到最新对象。重复 `reportId` 的后一个对象替换值，而 `Map` 键的遍历位置仍取首次插入时的位置：

~~~javascript
function uniqueByReportId(items) {
  const byId = new Map();
  items.forEach(item => byId.set(item.reportId, item));
  return [...byId.values()];
}

uniqueByReportId(rows); // [retry]
~~~

这里使用 `forEach`，空位不会被当成一条记录；若输入可能包含显式 `undefined`，仍需在业务边界另行校验。重复项按 `reportId` 保留最后版本，是一个业务策略，不是 `Map` 自动推断出来的“对象相等”。

如果结果允许改变顺序，也可先排序副本，再对相邻项按同一业务等价关系去重。这个策略是“保留排序后每组首项”，不同于上面的 Map “保留最后一次写入”：当前输入的排序比较相等，稳定排序保留原顺序，所以结果会保留 `first`（金额 `0`），Map 结果则保留 `retry`（金额 `120`）。比较器必须把所有相等项排在一起；`same` 必须和 `compare` 表达同一组等价类。函数先用 `filter` 跳过空位；它假设每个现存元素都是记录，不含显式 `undefined`，外部输入不满足时应先校验。

~~~typescript
function uniqueSorted<T>(
  items: T[],
  compare: (left: T, right: T) => number,
  same: (left: T, right: T) => boolean,
): T[] {
  const result: T[] = [];
  const presentItems = items.filter(() => true); // 跳过空位，保留现存值
  for (const item of [...presentItems].sort(compare)) {
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

这个方法会改变排序顺序，但不会修改输入数组；当“保留首次顺序”重要时，不要用排序去重替代 Set 或 Map。

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

空位表示该索引没有自有属性；它不同于存在一个值为 `undefined` 的属性。多数数组回调方法用 `HasProperty`（属性存在性检查）检查索引，因此普通稀疏数组的空位会被跳过；若原型链上存在同索引属性，该属性也可能被访问。`find` 系列（查找方法）则读取每个索引；原型链没有同索引属性时，空位会以 `undefined` 传给回调。

下表按没有继承索引属性的普通数组描述空位结果。

| 操作 | 输入有空位时的行为 | 是否改动原数组 |
|---|---|---|
| `map` | 跳过空位，并在对应结果位置保留空位 | 否 |
| `filter` | 跳过空位，结果只包含通过的现存值 | 否 |
| `forEach`、`some`、`every`、`reduce` | 普通空位不调用回调；`reduce` 无初始值且没有现存项时抛错 | 否 |
| `find`、`findIndex`、`findLast`、`findLastIndex` | 按索引读取；回调会收到 `undefined` | 否 |
| `for...of`、数组展开 | 消费数组迭代器；无继承索引属性时，空位读成 `undefined` | 否 |
| `flat` | 被展平层级中不存在的索引不写入结果 | 否 |
| `sort`、`reverse`、`splice` | 操作原接收数组；稀疏结构可能改变 | 是 |
| `toSorted`、`toReversed`、`toSpliced` | 生成副本；读取空位时会在结果中写入 `undefined` | 否 |

~~~javascript
const sparse = [, "x"];

0 in sparse; // false
sparse[0]; // undefined
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
const visited = [];
sparse.find((value, index) => {
  visited.push(index);
  return value === undefined;
});
visited; // [0]：find 回调确实访问了空位
[...sparse]; // [undefined, "x"]
Object.keys(sparse); // ["1"]
~~~

数组回调中的索引存在性检查也会看到原型链上的属性，因此某个“空位”若继承到同索引值，就会被 `map` 等方法访问。`for...in` 枚举可枚举的字符串属性名，可能包含自定义或继承属性；`for...of` 消费数组迭代器，读出位置上的值，通常更适合数组数据。

~~~javascript
const inheritedPrototype = Object.create(Array.prototype);
inheritedPrototype[0] = "from prototype";
const holeWithInheritedIndex = new Array(1);
Object.setPrototypeOf(holeWithInheritedIndex, inheritedPrototype);
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

`Array.from` 可以消费可迭代对象，也可以按 `length` 和索引读取类数组对象；可选映射函数能在创建时转换元素。空位在读取时成为 `undefined`，因此结果是稠密数组。数组展开也消费迭代器并产生同样的空位值，但不能像 `Array.from` 一样处理只有 `length` 和索引的类数组对象。

~~~javascript
Array.from(rows); // [first, undefined, retry]
Array.from(new Set(["paid", "review", "paid"])); // ["paid", "review"]
Array.from({ 0: "r-104", 1: "r-105", length: 2 }); // ["r-104", "r-105"]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]

Array(3);    // 长度为 3 的稀疏数组
Array.of(3); // [3]：参数本身作为元素
Array.of(1, 2, 3); // [1, 2, 3]
~~~

类数组读取、可迭代对象和 `Array.from` 的差异也会出现在[HTMLCollection 与 NodeList 如何处理实时集合？](#53.%20What%20is%20the%20difference%20between%20an%20HTMLCollection%20and%20a%20NodeList?%20/%20HTMLCollection%20%E4%B8%8E%20NodeList%20%E6%9C%89%E4%BB%80%E4%B9%88%E5%8C%BA%E5%88%AB%EF%BC%9F)的 DOM 集合快照中；迭代协议本身见[迭代器与生成器如何按需产出值？](#44.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F)。文本要按 Unicode 码点遍历时，`Array.from(string)` 也会消费字符串迭代器；用户感知字符可能由多个码点组成，还需另做分段，详见[文本算法应按什么单位计数和比较？](../../engineering-foundations/algorithms/text-units-and-algorithms.md)。

### 复制数组只复制一层

数组展开和 `slice` 会创建新数组，但元素值仍是原来的对象引用；修改复制数组内的嵌套记录，原数组仍能观察到这次属性变更。数组的空位行为还取决于复制方式：`slice` 和 `concat` 可保留空位，展开与 `Array.from` 通过迭代会把它们变为 `undefined`。

~~~javascript
const original = [{ score: 1 }];
const copy = [...original];
copy[0].score = 2;
original[0].score; // 2：嵌套对象共享

const holeCopy = sparse.slice();
0 in holeCopy; // false：slice 保留空位

const spreadCopy = [...sparse];
0 in spreadCopy; // true：展开生成了显式 undefined
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

`flat(depth)` 返回展平副本，默认只展平一层；`flat(Infinity)` 展开所有非循环嵌套数组层级。它会跳过被访问层级中的空位，不会递归展平 `Set` 之类的非数组可迭代对象。

~~~javascript
const sparseNested = [, [, 1]];
[].concat(...sparseNested); // [undefined, <1 empty item>, 1]
sparseNested.flat(Infinity); // [1]
~~~

旧式逐层 concat 的差别来自两步：外层展开消费迭代器，把外层空位变成 undefined；concat 随后浅复制嵌套数组时仍保留其中空位。它还可能反复复制宽数组，或超过引擎的实参数量限制。

递归循环可清楚展示层级规则，但极深输入可能耗尽调用栈；这里按每个数值索引读取，因此空位变成 undefined，与 flat 不同。

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

迭代式 `[].concat(...items)` 每轮展平一层，可能命中参数数量限制、重复复制大数组，且空位行为与 `flat` 不同。如果输入没有嵌套数组，它还会直接返回原输入，而非副本。

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
> - `concat` 与 `Symbol.isConcatSpreadable` 的展开规则：[ECMAScript 2026 §23.1.3.2 Array.prototype.concat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.concat)；稳定排序：[ECMAScript 2019 §22.1.3.27 Array.prototype.sort](https://tc39.es/ecma262/2019/#sec-array.prototype.sort)。
> - `for...in` 与 `for...of` 的枚举和迭代规则：[ECMAScript 2026 §14.7.5](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)；数组迭代器的索引读取：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - Set 去重、SameValueZero 与平均访问时间：[ECMAScript 2026 §24.1–24.2 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；[§7.2.10 SameValueZero](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Math.max 和实参处理：[ECMAScript 2026 §21.3.2.24](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
## 31. 如何安全地深拷贝 JavaScript 值？

报表要保存一份可独立编辑的快照时，浅复制只会新建外层数组或对象，嵌套 `owner` 仍可能与当前界面共享。所谓“深拷贝”没有脱离数据模型的通用实现：先确认输入类型、循环引用、共享子对象、原型行为和所有权边界，再选择 `JSON`、`structuredClone`（结构化克隆）或范围受限的手写复制器。

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
## 32. How do var, let, and const differ? / var、let 与 const 有什么区别？

**Core answer / 核心回答：** Choose a declaration by its scope and whether its binding must be reassigned. var is function-scoped and starts as undefined when its binding is created. let and const are block-scoped and cannot be read before their declaration initializes them. const prevents rebinding; it does not freeze an object. / 根据作用域和是否需要重新绑定来选择声明方式。var 是函数作用域，绑定创建时初值为 undefined。let 和 const 是块级作用域，声明初始化前不可访问。const 禁止重新绑定，但不会冻结对象。

| Behavior / 行为 | var | let | const |
|---|---|---|---|
| Scope / 作用域 | Function scope; top-level behavior depends on script, module, or host / 函数作用域；顶层由脚本、模块或宿主决定 | Lexical block / 词法块 | Lexical block / 词法块 |
| Before declaration / 声明前访问 | Binding exists and is initialized to undefined / 绑定已建立并初始化为 undefined | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 |
| Same-scope redeclaration / 同作用域重复声明 | Often allowed for var / 通常允许 | Syntax error / 语法错误 | Syntax error / 语法错误 |
| Reassignment / 重新赋值 | Allowed / 允许 | Allowed / 允许 | Binding cannot be reassigned / 绑定不能重新赋值 |
| Initializer required / 是否必须初始化 | No / 否 | No / 否 | Yes / 是 |

### How scope and initialization differ / 作用域与初始化的差异

A var declaration belongs to the nearest function scope. An if or for block does not create a separate var binding. Its binding is initialized to undefined when the environment is created, but the initializer expression still runs at its written position. / var 属于最近的函数作用域，if 或 for 块不会为它创建独立绑定。环境创建时该绑定会初始化为 undefined，但初始化表达式仍在代码写出的位置执行。

~~~javascript
function example() {
  console.log(value); // undefined
  if (true) {
    var value = 10;
  }
  console.log(value); // 10
}
~~~

let and const belong to the nearest lexical block, including if, switch, loops, and a standalone brace block. Their bindings are established with the block but remain in the Temporal Dead Zone until declaration evaluation. The precise description is not “they are never hoisted”; it is that they cannot be accessed before initialization. / let 和 const 属于最近的词法块，包括 if、switch、循环和独立代码块。进入代码块时绑定已经建立，但在声明执行前仍处于暂时性死区。准确说法不是“它们不会提升”，而是初始化前不能访问。 See MDN’s [let reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let) for the temporal-dead-zone behavior.

~~~javascript
{
  // console.log(count); // ReferenceError: still in the TDZ
  let count = 1;
}

const settings = { theme: "light" };
settings.theme = "dark"; // allowed: the object can still mutate
// settings = {};        // TypeError: the binding cannot be reassigned
~~~

At the top level, a classic browser script, an ES module, and a Node module have different environments. In a classic browser script, global var can create a property on the global object, while top-level let and const create global lexical bindings instead. Do not apply that script behavior to modules. / 经典浏览器脚本、ES 模块和 Node 模块的顶层环境不同。在经典浏览器脚本中，全局 var 可在全局对象上创建属性；顶层 let 和 const 则创建全局词法绑定。不要把脚本行为套用到模块。

Across hosts, globalThis refers to the current global object. A browser window normally provides window on the main thread, while workers have their own global object. In a classic browser script, the difference between global var and lexical bindings is observable through window: / 跨宿主访问当前全局对象时可使用 globalThis。浏览器主线程通常提供 window，worker 则有自己的全局对象。在经典浏览器脚本中，可通过 window 观察全局 var 与词法绑定的区别：

~~~html
<script>
  var scriptVar = 'global object property';
  let scriptBinding = 'global lexical binding';

  console.log(window.scriptVar);     // 'global object property'
  console.log(window.scriptBinding); // undefined
</script>
~~~

See MDN on the [global object](https://developer.mozilla.org/en-US/docs/Glossary/Global_object) for the host boundary.

The binding rules for var, let, and const are specified in [ECMAScript statements and declarations](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html); the environment model, including [module environment records](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records), is described in [ECMAScript execution contexts](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html). For how outer lexical environments form the name-lookup chain and how a closure continues to access a binding, see [Scope and Closure / 作用域与闭包](#33.%20How%20do%20lexical%20scope%20and%20closures%20preserve%20access%20to%20state?%20/%20%E8%AF%8D%E6%B3%95%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E5%AF%B9%E7%8A%B6%E6%80%81%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F). / var、let、const 的绑定规则见 [ECMAScript 语句与声明](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html)；包括[模块环境记录](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)在内的环境模型见 [ECMAScript 执行上下文](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html)。外层词法环境如何形成名称查找链、闭包如何继续访问绑定，见[作用域与闭包](#33.%20How%20do%20lexical%20scope%20and%20closures%20preserve%20access%20to%20state?%20/%20%E8%AF%8D%E6%B3%95%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E5%AF%B9%E7%8A%B6%E6%80%81%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F)。
## 33. How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？

**Core answer / 核心回答：** JavaScript resolves a name from the function’s definition environment outward, not from its caller. A closure is a function that keeps access to bindings from that lexical environment. It reads the binding’s current value, so state can remain observable after the outer call returns. / JavaScript 按函数的定义环境向外查找名称，不按调用者的位置查找。闭包让函数继续访问定义时外层词法环境中的绑定；它读取绑定的当前值，因此外层函数返回后状态仍可被观察。

### How name lookup follows lexical structure / 名称查找如何沿词法结构进行

An identifier lookup starts in the current lexical environment and continues through its enclosing environments. The caller’s local variables are not inserted into a function’s lookup chain. Execution contexts and lexical environment records are the specification model for this behavior; engines need not allocate objects with those exact names or shapes. / 标识符先在当前词法环境中查找，再逐层向外查找。调用者的局部变量不会插入被调用函数的查找链。执行上下文和词法环境记录是规范描述这种行为的模型；引擎不必创建名称和结构完全相同的对象。

See the [ECMAScript execution-context and environment-record specification](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html). / 详见 [ECMAScript 执行上下文与环境记录规范](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html)。

~~~javascript
const label = "global";

function outer() {
  const label = "outer";
  function inner() {
    const detail = "inner";
    return [label, detail];
  }
  return inner;
}

function callFromElsewhere() {
  const label = "caller";
  return outer()();
}

callFromElsewhere(); // ["outer", "inner"]
~~~

inner finds its own detail, then outer’s label, and only then could reach the global environment. The caller’s label is irrelevant. / inner 先找到自己的 detail，再找到 outer 的 label，之后才可能到达全局环境；caller 的 label 不参与查找。

~~~mermaid
flowchart LR
  inner["inner environment: detail"] --> outer["outer environment: label"]
  outer --> global["global environment"]
  caller["caller environment: label"] -. "not part of lookup chain" .-> inner
~~~

### What a closure retains / 闭包保留了什么

A closure is a function together with its access to the lexical bindings it uses. It does not copy the value present when the function was created. / 闭包是函数及其对所用词法绑定的访问能力；创建函数时的值不会被定格为一份副本。 MDN’s [closure guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures) demonstrates this behavior. / MDN 的[闭包指南](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)展示了这一行为。

~~~javascript
function makeReader() {
  let state = "before";
  const read = () => state;
  state = "after";
  return read;
}

const readState = makeReader();
readState(); // "after"
~~~

Each call to makeReader creates a distinct state binding. Several returned functions can intentionally share one binding, which is useful for private state. / 每次调用 makeReader 都会创建独立的 state 绑定。多个返回函数也可以有意共享一个绑定，从而形成私有状态。

~~~javascript
function makeCounter() {
  let count = 0;
  return {
    increment() { count++; return count; },
    decrement() { count--; return count; },
    value() { return count; },
  };
}

const counter = makeCounter();
counter.increment(); // 1
counter.increment(); // 2
counter.count;       // undefined: count is not an object property
~~~

A function factory can retain a parameter to specialize later calls. Event callbacks similarly retain values from the registration call. / 函数工厂可以保留参数，让后续调用使用专门化的函数。事件回调也会保留注册回调时所在环境中的值。

~~~javascript
function multiplyBy(factor) {
  return number => number * factor;
}
const double = multiplyBy(2);
const triple = multiplyBy(3);
double(5); // 10
triple(5); // 15

function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener("click", () => {
    console.log("Clicked: " + label);
  });
}

attachLogger("btn1", "primary");
attachLogger("btn2", "secondary");
~~~

### Why loop callbacks differ / 循环回调为什么读到不同值

A var loop has one function-scoped binding, so deferred callbacks read its final value. A let loop creates a per-iteration binding, so each callback retains the value for its iteration. / var 循环使用一个函数级绑定，延后执行的回调会读到它的最终值。let 循环为每次迭代创建绑定，因此回调保留各自迭代中的值。

~~~javascript
const fromVar = [];
for (var i = 0; i < 3; i++) fromVar.push(() => i);

const fromLet = [];
for (let j = 0; j < 3; j++) fromLet.push(() => j);

fromVar.map(fn => fn()); // [3, 3, 3]
fromLet.map(fn => fn()); // [0, 1, 2]
~~~

An IIFE can introduce a separate parameter binding in legacy var code, but modern code normally expresses the intended per-iteration binding directly with let. / 旧式 var 代码可用 IIFE 为每轮引入独立参数绑定；现代代码通常直接用 let 表达每轮独立绑定的意图。

~~~javascript
const callbacks = [];
for (var index = 0; index < 3; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}
callbacks.map(fn => fn()); // [0, 1, 2]
~~~

### How closure lifetime relates to memory / 闭包生命周期与内存有何关系

An outer call returning does not make a captured binding immediately unusable. As long as a reachable closure can observe it, the program must preserve the behavior. This does not mean every variable in the entire outer scope must occupy memory forever; implementations can optimize unobservable values. / 外层调用返回并不意味着捕获的绑定立即失效。只要可达闭包仍能观察它，程序就必须保留可观察行为；但这不表示外层作用域中的所有变量都必然永久占用内存，引擎可以优化不可观察的值。

Think in terms of reachability: a long-lived listener that closes over a large object can keep that object reachable. Remove the listener and other references when their lifetime ends. A cycle alone is not a leak; MDN discusses [closure performance considerations](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures#performance_considerations); the important question is whether a path from live program state still reaches the objects. For garbage-collection models and diagnostics, see [Event Loop and Host Scheduling / 事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F). / 从可达性判断更实用：长期保存的监听器若闭包捕获大型对象，就可能让对象继续可达。生命周期结束时移除监听器及其他引用。循环引用本身不等于泄漏，关键是活动程序状态是否仍有到这些对象的引用路径。垃圾回收模型与排查见[事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)。

**See also:** [JavaScript Basics / JavaScript 基础](#32.%20How%20do%20var,%20let,%20and%20const%20differ?%20/%20var%E3%80%81let%20%E4%B8%8E%20const%20%E6%9C%89%E4%BB%80%E4%B9%88%E5%8C%BA%E5%88%AB%EF%BC%9F) explains the binding and temporal-dead-zone rules that determine which environment a closure can capture. Ordinary function this is determined by call form, not lexical name lookup; see [Function this and Binding / 函数 this 与绑定](#35.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F).
## 34. How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？

**Core answer / 核心回答：** An object first checks its own properties, then follows its internal prototype link until a match or the end of the chain. Constructor prototypes supply a default prototype to instances created with new, while instance fields, prototype methods, static members, and property descriptors control where properties live and how they behave. / 对象先查自有属性，再沿内部原型链接向上查找，直到找到匹配属性或到达链尾。构造函数的 prototype 为 new 创建的实例提供默认原型；实例字段、原型方法、静态成员和属性描述符决定属性的位置与行为。

### How prototype lookup works / 原型查找如何工作

An ordinary object has an internal `[[Prototype]]` value, which may be null. If a property is missing from the object, lookup continues along this chain. Use Object.getPrototypeOf and Object.create when the chain must be inspected or created explicitly. / 普通对象有一个内部 `[[Prototype]]` 值，也可能为 null。对象上找不到属性时，查找会沿原型链继续。需要显式检查或创建原型链时，使用 Object.getPrototypeOf 和 Object.create。

Many constructible functions have an own property named prototype. When that value is an object, new uses it as the prototype for the created instance. It is distinct from Function.prototype, which function objects themselves normally inherit through their own internal prototype link. Arrow functions and methods are not constructible and do not have an own prototype property. The legacy __proto__ accessor is inherited from Object.prototype; prefer Object.getPrototypeOf. / 许多可构造函数有名为 prototype 的自有属性；若该值为对象，new 会把它用作新实例的原型。它不同于 Function.prototype，后者通常是函数对象自身通过内部原型链接继承的对象。箭头函数和方法不可构造，也没有自有 prototype 属性。历史访问器 __proto__ 从 Object.prototype 继承而来；优先使用 Object.getPrototypeOf。

~~~javascript
function Person(name) {
  this.name = name;
}
Person.prototype.greet = function () {
  return "Hello, " + this.name;
};

const ada = new Person("Ada");
ada.greet(); // "Hello, Ada"
Object.getPrototypeOf(ada) === Person.prototype; // true
Object.getPrototypeOf(Person.prototype) === Object.prototype; // true
Object.getPrototypeOf(Object.prototype); // null
~~~

Object.create lets code choose a prototype directly. A null-prototype object has no inherited toString method, which can be useful for dictionaries. / Object.create 可直接选择原型。null 原型对象没有继承 toString 方法，可用于字典。

~~~javascript
const ordinary = {};
Object.getPrototypeOf(ordinary) === Object.prototype; // true

const custom = Object.create({ greet: "hello" });
custom.greet; // inherited value

const dictionary = Object.create(null);
dictionary.toString; // undefined
~~~

The old Object.prototype.__proto__ accessor is a legacy, normative-optional feature in ECMAScript. / ECMAScript 将旧版 Object.prototype.__proto__ 访问器标记为历史且规范可选的特性，见[规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.__proto__)。

### Where instance, prototype, and static properties live / 实例、原型与静态属性分别在哪里

A function assigned inside a constructor becomes an own function property on each instance. A prototype method is found through the shared prototype. Class methods are placed on the prototype; class instance fields create own properties; static members belong to the class constructor itself. Choose based on state, identity, and behavior rather than assuming one placement is always faster. / 在构造函数中赋值的函数会成为每个实例上的自有函数属性；原型方法则通过共享原型查找。class 方法放在原型上，实例字段创建自有属性，静态成员属于 class 构造函数本身。应按状态、身份和行为选择，不要假设某一种布局总是更快。

~~~javascript
class User {
  label = "member";                // own instance field
  greet() { return "Hi"; }         // shared prototype method
  static category = "account";     // property on the class constructor
}

const user = new User();
Object.hasOwn(user, "label");      // true
Object.hasOwn(user, "greet");      // false
Object.hasOwn(User, "category");   // true
~~~

Own properties are checked before inherited ones; an own value can shadow a prototype method. Static properties on the constructor are not part of an instance’s prototype lookup. / 自有属性先于继承属性查找；自有值可以遮蔽原型方法。构造函数上的静态属性不属于实例的原型查找链。

~~~javascript
function Example() {
  Example.value = function () { return 1; };
  this.value = function () { return 2; };
}
Example.prototype.value = function () { return 3; };
Example.value = function () { return 4; };

Example.value(); // 4
const instance = new Example();
instance.value(); // 2: own property shadows the prototype method
Example.value(); // 1: constructor body replaced the static property
~~~

### How property descriptors affect reads and writes / 属性描述符如何影响读写

Own properties have attributes. A data property stores a value and may be writable; an accessor property uses getter and setter functions. Both kinds also have enumerable and configurable attributes. Object.defineProperty sets them explicitly. / 自有属性有属性特征。数据属性保存值并可设置是否可写；访问器属性通过 getter 和 setter 函数读写。两种属性都有 enumerable 和 configurable 特征，可由 Object.defineProperty 显式设置。

| Attribute / 特征 | Meaning / 含义 |
|---|---|
| value | Stored value / 存储值 |
| writable | Whether assignment may change a data property / 赋值是否能修改数据属性 |
| get / set | Functions used when reading or writing an accessor property / 访问器属性读写时调用的函数 |
| enumerable | Included in own-enumerable key APIs; for...in also walks the prototype chain / 自有可枚举键 API 会包含；for...in 还遍历原型链 |
| configurable | Whether the property can generally be deleted or reconfigured / 通常能否删除或重新配置 |

~~~javascript
const record = {};
Object.defineProperty(record, "id", {
  value: 7,
  writable: false,
  enumerable: true,
  configurable: false
});
Object.getOwnPropertyDescriptor(record, "id");
// { value: 7, writable: false, enumerable: true, configurable: false }
~~~

A setter can validate or normalize writes; a getter can compute a read. Assignment to a non-writable property is ignored in sloppy code and throws in strict code. / setter 可校验或规范写入值；getter 可在读取时计算。非严格代码对不可写属性的赋值会被忽略，严格模式则会抛错。

~~~javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true
});

profile.name; // "John"
profile.name = "Jo";
profile._name; // "Jo"
~~~

### Which object shapes are engine-specific / 哪些对象形状细节属于引擎实现

V8 uses HiddenClasses (also called Maps) to track object shapes and optimize property access. Objects initialized with the same named properties in the same order can share a shape in V8. This is an implementation detail, not an ECMAScript guarantee; optimize layouts only when profiling identifies a real cost. / V8 使用 HiddenClasses（也称 Maps）跟踪对象形状并优化属性访问。在 V8 中，以相同顺序初始化相同命名属性的对象可能共享形状。这是实现细节，不是 ECMAScript 保证；只有性能分析发现实际成本时才优化布局。

See [Fast properties in V8](https://v8.dev/blog/fast-properties). For how a call supplies this and how new creates an instance, see [Function this and Binding / 函数 this 与绑定](#35.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F) and [Construction with new / 使用 new 构造对象](#36.%20What%20does%20new%20do%20when%20it%20constructs%20an%20object?%20/%20new%20%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%E6%97%B6%E5%81%9A%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%9F).
## 35. How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？

**Core answer / 核心回答：** An ordinary function gets its this value from the call form: obj.method() supplies obj, call/apply supply an explicit receiver, and bind creates a bound function. A plain strict-function call uses undefined. An arrow function instead captures this from its surrounding lexical environment and cannot be rebound. / 普通函数的 this 由调用方式决定：obj.method() 以 obj 为接收者，call/apply 显式提供接收者，bind 创建绑定函数；严格函数的普通调用中 this 为 undefined。箭头函数从外层词法环境捕获 this，不能重新绑定。

### Ordinary calls supply the receiver / 普通调用形式提供接收者

~~~javascript
const service = {
  url: "/data",
  fetch() { return this.url; }
};

service.fetch(); // "/data"
const detached = service.fetch;
detached(); // TypeError in strict code; it no longer has service as its receiver
~~~

In sloppy code, a plain call substitutes the host’s global this value. In a browser classic script that is generally window; Node module wrappers have their own top-level conventions. Strict mode, ES modules, and class bodies use strict semantics. / 非严格代码中的普通调用会把 this 替换为宿主全局值；浏览器经典脚本中通常为 window，Node 模块包装器另有顶层约定。严格模式、ES 模块和 class 函数体使用严格语义。

### Explicit receiver methods / 显式接收者方法

call invokes immediately with separate arguments; apply invokes immediately with an argument list; bind creates a new function with a bound receiver and leading arguments. / call 使用分开的参数立即调用；apply 使用参数列表立即调用；bind 创建一个绑定接收者和前置参数的新函数。

~~~javascript
function describe(prefix, name) {
  return prefix + " " + name + " (" + this.role + ")";
}

describe.call({ role: "admin" }, "Hello", "Ada");
describe.apply({ role: "admin" }, ["Hello", "Ada"]);
const greetAdmin = describe.bind({ role: "admin" }, "Hello");
greetAdmin("Ada"); // "Hello Ada (admin)"
~~~

If a bound function is called with new, its bound receiver is ignored, but its leading arguments remain in effect. Arrow functions have no own this or arguments, are not constructible with new, and do not have an own prototype property. call, apply, or bind cannot replace an arrow’s lexical this. Use method syntax when the method needs its object as this; use an arrow when lexical capture is intentional. / 绑定函数通过 new 调用时会忽略已绑定的接收者，但保留前置参数。箭头函数没有自己的 this 或 arguments，不能通过 new 构造，也没有自有 prototype 属性。call、apply 和 bind 都不能替换箭头函数捕获的 this。方法需要对象作为 this 时使用方法语法；确实需要词法捕获时使用箭头函数。

~~~javascript
const counter = {
  value: 1,
  read() { return this.value; },
  readArrow: () => this.value // captures surrounding this, not counter
};
~~~

A host API can supply a receiver when it invokes a callback. The DOM calls an ordinary event listener with this set to event.currentTarget; an arrow keeps its surrounding this, so use the event property explicitly. See the [WHATWG DOM listener-invocation algorithm](https://dom.spec.whatwg.org/#concept-event-listener-invoke) and [DOM event propagation / DOM 事件传播](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F) for the surrounding event contract. / 宿主 API 调用回调时也可提供接收者。DOM 调用普通事件监听器时会把 this 设为 event.currentTarget；箭头函数保留外层 this，因此应显式读取事件属性。详见 [WHATWG DOM 监听器调用算法](https://dom.spec.whatwg.org/#concept-event-listener-invoke)及 [DOM 事件传播](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F)中的相关契约。

~~~javascript
const button = document.querySelector("button"); // assume a button exists
button.addEventListener("click", function (event) {
  this === event.currentTarget; // true
});
button.addEventListener("click", event => {
  event.currentTarget === button; // true: arrow this is not the listener receiver
});
~~~

Lexical name lookup and lexical this are separate ideas: closures capture outer bindings, while an ordinary function’s this depends on its invocation. See [Scope and Closure / 作用域与闭包](#33.%20How%20do%20lexical%20scope%20and%20closures%20preserve%20access%20to%20state?%20/%20%E8%AF%8D%E6%B3%95%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E5%AF%B9%E7%8A%B6%E6%80%81%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F).

### Why a small bind helper is not a polyfill / 简化 bind 模型为何不是 polyfill

This helper illustrates partial application for an object receiver. Native bind also handles constructor calls, constructibility, and function metadata. / 这个辅助函数演示对象接收者上的部分应用；原生 bind 还处理构造调用、可构造性和函数元数据。

~~~javascript
function bindForObjectReceiver(fn, receiver, ...leadingArgs) {
  return function (...laterArgs) {
    return fn.apply(receiver, [...leadingArgs, ...laterArgs]);
  };
}
~~~

A temporary property can also show how method-call syntax supplies this. This limited example only accepts an extensible object receiver; it does not model primitive receivers, proxies, strict/sloppy conversion, or every exceptional case. Use the built-ins in application code. / 临时属性也能展示方法调用如何提供 this。这个有限示例只接受可扩展对象接收者，不能模拟原始值接收者、代理、严格/非严格转换或所有异常情况。应用代码应使用内置方法。

~~~javascript
function callWithObjectReceiver(fn, receiver, ...args) {
  if (receiver === null ||
      (typeof receiver !== "object" && typeof receiver !== "function")) {
    throw new TypeError("This example requires an object receiver");
  }
  const key = Symbol("temporary method");
  Object.defineProperty(receiver, key, { value: fn, configurable: true });
  try {
    return receiver[key](...args);
  } finally {
    delete receiver[key];
  }
}
~~~

Ordinary function call behavior is specified by ECMAScript’s [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call), [Function.prototype.apply](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.apply), [Function.prototype.bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind), and [arrow-function definitions](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions). / 普通函数调用行为见 ECMAScript 的 [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call)、[Function.prototype.apply](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.apply)、[Function.prototype.bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind) 和[箭头函数定义](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-arrow-function-definitions)。
## 36. What does new do when it constructs an object? / new 构造对象时做了什么？

**Core answer / 核心回答：** For a constructible function, new creates a receiver whose prototype comes from the constructor’s effective prototype, calls the constructor with that receiver as this, then returns an explicit object or function result if supplied. A primitive return is ignored. / 对可构造函数，new 会创建一个原型取自构造函数有效 prototype 的接收者，以它作为 this 调用构造函数；若构造函数显式返回对象或函数，则返回该值，否则返回新接收者。原始值返回会被忽略。

~~~mermaid
flowchart LR
  A["Read effective constructor prototype"] --> B["Create receiver with that prototype"]
  B --> C["Call constructor with receiver as this"]
  C --> D{"Did it return an object or function?"}
  D -- "yes" --> E["Return explicit result"]
  D -- "no: undefined or primitive" --> F["Return created receiver"]
~~~

### Constructor and instance relationship / 构造函数与实例的关系

~~~javascript
function Person(name) {
  this.name = name;
}
Person.prototype.greet = function () {
  return "Hello, " + this.name;
};

const ada = new Person("Ada");
ada.greet(); // "Hello, Ada"
Object.getPrototypeOf(ada) === Person.prototype; // true
~~~

The prototype used for an instance is the constructor’s object-valued prototype property, not Function.prototype. If its prototype value is not an object, the language falls back to the appropriate intrinsic prototype; the exact fallback depends on the constructor’s realm. The specification’s [GetPrototypeFromConstructor](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) accepts any object-valued prototype, including a function. / 实例所用原型来自构造函数的对象类型 prototype 属性，不是 Function.prototype。若该属性不是对象，语言会回退到相应内置原型；具体回退取决于构造函数所在 realm。规范的 [GetPrototypeFromConstructor](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) 接受任何对象类型的 prototype，包括函数。

### Object returns replace the created receiver / 返回对象会替换新建接收者

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive(); // the new object with created: true

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }
~~~

A teaching model for ordinary constructors from the current realm makes the main steps visible. It is not a full polyfill for classes, bound functions, built-ins, proxies, or new.target. / 以下普通当前 realm 构造函数教学模型展示主要步骤；它不是 class、绑定函数、内置构造器、代理或 new.target 的完整 polyfill。

~~~javascript
function emulateNew(fn, ...args) {
  const candidate = fn.prototype;
  const prototype =
    candidate !== null &&
    (typeof candidate === "object" || typeof candidate === "function")
      ? candidate
      : Object.prototype;
  const instance = Object.create(prototype);
  const result = fn.apply(instance, args);
  const isObject =
    result !== null &&
    (typeof result === "object" || typeof result === "function");
  return isObject ? result : instance;
}
~~~

The helper also models a function-valued prototype, because functions are objects and are accepted as prototype objects by Object.create and the constructor operation. / 该辅助函数也能处理函数类型的 prototype，因为函数是对象，Object.create 与构造算法都接受函数作为原型对象。

~~~javascript
function CallablePrototype() {}
function Example() {}
Example.prototype = CallablePrototype;
const example = emulateNew(Example);
Object.getPrototypeOf(example) === CallablePrototype; // true
~~~

Class constructors have semantics beyond ordinary functions, including restrictions on how they are called; see the [ECMAScript class-definition rules](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions). Built-in constructors also have additional construction semantics, so use new or class syntax in application code rather than this teaching helper. For property lookup and the roles of instance, prototype, and static members, see [Objects and Prototypes / 对象与原型](#34.%20How%20do%20JavaScript%20objects%20find%20and%20organize%20properties?%20/%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%92%8C%E7%BB%84%E7%BB%87%E5%B1%9E%E6%80%A7%EF%BC%9F). / class 构造器拥有普通函数所没有的语义，包括调用方式限制；详见 [ECMAScript 类定义规则](https://tc39.es/ecma262/2025/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)。内置构造器也有额外构造语义，因此应用代码应使用 new 或 class 语法，而不是此教学辅助函数。属性查找及实例、原型、静态成员的作用见[对象与原型](#34.%20How%20do%20JavaScript%20objects%20find%20and%20organize%20properties?%20/%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%92%8C%E7%BB%84%E7%BB%87%E5%B1%9E%E6%80%A7%EF%BC%9F)。
## 37. How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？

**Core answer / 核心回答：** A Proxy pairs a target object with a handler. When code operates through the proxy, matching handler traps can intercept reads, writes, deletion, membership checks, and other operations; Reflect methods forward an operation with its normal semantics. Proxy is a JavaScript runtime feature, not a TypeScript type feature. / Proxy 将目标对象与 handler 配对。代码通过代理执行操作时，对应 trap 可拦截读取、写入、删除、成员检查等行为；Reflect 方法可按正常语义转发操作。Proxy 是 JavaScript 运行时功能，不是 TypeScript 类型特性。

~~~javascript
const handler = {
  get(target, property, receiver) {
    console.log("read", property);
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("write", property);
    return Reflect.set(target, property, value, receiver);
  }
};

const data = new Proxy({ count: 0 }, handler);
data.count;    // logs "read", then returns 0
data.count = 1; // logs "write", then updates the target
~~~

Typical uses include reactive state, validation, and instrumentation. A proxy only observes operations that pass through it; a retained reference to the original target can bypass its traps. A proxy can intercept later-added properties, unlike defining a getter for each known property, but the object’s invariants and compatibility requirements still matter. / 常见用途包括响应式状态、校验和测量。代理只能观察经由代理执行的操作；若代码保留原始 target 的引用，就能绕过这些 trap。代理可以拦截后来添加的属性，而逐个定义 getter 做不到，但仍须考虑对象不变量和兼容性。

Vue 2 used property getters and setters for reactivity; Vue 3 uses proxies for reactive objects. This is an example of framework implementation, not a guarantee that every reactive system needs Proxy. / Vue 2 使用属性 getter 和 setter 实现响应式；Vue 3 的响应式对象使用代理。这是框架实现示例，不代表所有响应式系统都必须使用 Proxy。

Vue 2 used property getters and setters for reactivity, while Vue 3 uses proxies for reactive objects. See [Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth). This framework example does not imply that every reactive system needs Proxy. / Vue 2 使用属性 getter 和 setter 实现响应式，Vue 3 则对响应式对象使用代理。详见 [Vue 响应式原理](https://vuejs.org/guide/extras/reactivity-in-depth)。框架示例不意味着所有响应式系统都必须使用 Proxy。

See [ECMAScript Proxy objects](https://tc39.es/ecma262/2025/multipage/proxy-object.html) for trap invariants and [Reflect](https://tc39.es/ecma262/2025/multipage/reflection.html) for forwarding operations.
## 38. How does currying support partial application? / 柯里化如何支持部分应用？

**Core answer / 核心回答：** Currying transforms a function that accepts several arguments into a sequence of calls. Supplying fewer than the expected arguments returns another function; later calls complete the argument list. This supports partial application, but the arity rule must match the function’s contract. / 柯里化把接收多个参数的函数转换为一系列调用。参数不足时返回新函数，后续调用补齐参数，实现部分应用；但元数判断规则必须符合函数契约。

This compact implementation uses fn.length as arity and supports ordinary positional functions. Default parameters, rest parameters, placeholders, and other arity conventions need a different contract. / 这个简化实现用 fn.length 作为元数，仅支持普通位置参数函数。默认参数、剩余参数、占位符及其他元数约定需要另外定义。

~~~javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return function (...next) {
      return curried.apply(this, [...args, ...next]);
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);
curriedSum(1)(2)(3); // 6
curriedSum(1, 2)(3); // 6
~~~

Currying transforms argument flow; it does not change how ordinary function this is supplied. See [Function this and Binding / 函数 this 与绑定](#35.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F).
## 39. What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？

**Core answer / 核心回答：** Strict mode turns selected legacy mistakes into errors and changes some function behavior, including the this value of a plain call. ES modules and class bodies are strict automatically. It is not a security sandbox and does not make eval safe. / 严格模式会把部分历史代码中的错误变成异常，并改变一些函数行为，包括普通调用中的 this 值。ES 模块和 class 函数体自动采用严格模式。严格模式不是安全沙箱，也不会让 eval 变安全。

A classic script can opt in with a "use strict" directive at the start of the script; an ordinary function can opt in with a directive at the beginning of its body. An assignment to an undeclared name then throws instead of creating an accidental global. A strict plain function call receives undefined as this. / 经典脚本可在开头用 "use strict" 指令启用严格模式；普通函数也可在函数体开头启用。此时给未声明名称赋值会抛错，而不会意外创建全局变量。严格模式下普通函数调用的 this 是 undefined。

~~~javascript
"use strict";

undeclaredName = 1; // ReferenceError

function inspectThis() {
  return this;
}
inspectThis(); // undefined
~~~

Other recognizable differences include rejecting with, rejecting legacy octal numeric literals and duplicate parameter names in strict functions, and throwing rather than silently ignoring some writes to non-writable properties. Class and module code is already strict, so an extra directive is unnecessary there. / 其他可识别的差异包括禁止 with、旧式八进制数字字面量和严格函数中的重复形参；对部分不可写属性的赋值也会抛错，而非静默忽略。class 和模块代码本来就是严格模式，无需额外指令。

These rules are part of the [ECMAScript strict mode code semantics](https://tc39.es/ecma262/2025/#sec-strict-mode-code). Strict mode changes only specified language behaviors. It does not validate input or impose a security boundary. / 这些规则属于 [ECMAScript 严格模式语义](https://tc39.es/ecma262/2025/#sec-strict-mode-code)。严格模式只改变规范明确列出的语言行为，不会验证输入，也不会建立安全边界。

For the strict-call effect on this, see [Function this and Binding / 函数 this 与绑定](#35.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F). For value conversion, truthiness, and equality, see [JavaScript Types / JavaScript 类型](#28.%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%EF%BC%8C%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F).
## 40. 弱集合与弱引用能保证什么？

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

对象仍被保留时，应找出强引用链，而不是等待最终化。堆保留路径的诊断见[对象为什么在不再有用后仍留在内存中？](#41.%20JavaScript%20%E5%AF%B9%E8%B1%A1%E4%B8%BA%E4%BD%95%E4%BC%9A%E5%9C%A8%E4%B8%8D%E5%86%8D%E6%9C%89%E7%94%A8%E5%90%8E%E4%BB%8D%E7%95%99%E5%9C%A8%E5%86%85%E5%AD%98%E4%B8%AD%EF%BC%9F)。

> [!info]- 来源
> - WeakMap / WeakSet 的键资格、弱键值关系和不可枚举约束：[ECMAScript 2026 §24.3–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - WeakRef 目标和构造：[ECMAScript 2026 §26.1.1.1](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref-target)；`deref()` 保活当前代码执行：[§26.1.3.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref.prototype.deref)。
> - FinalizationRegistry 注册目标、heldValue 和取消注册：[ECMAScript 2026 `FinalizationRegistry.prototype.register`](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry.prototype.register)；对象与注册表清理模型：[§26.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry-objects)、[§9.9](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 运行时实际核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06；核对目标构造、键资格和同步 `deref()` 行为，不以一次运行推断最终化时序。
## 41. JavaScript 对象为何会在不再有用后仍留在内存中？

用户关闭报表后，如果旧结果还被全局事件处理器、计时器闭包或缓存引用，垃圾回收器仍能从程序根沿引用链找到它们。判断“业务上已过期”并不能让对象自动回收；需要断开不再需要的强引用。本章从报表监听器的保留路径解释原因，再给出诊断步骤。弱引用的语言保证见[弱集合与弱引用能保证什么？](#40.%20%E5%BC%B1%E9%9B%86%E5%90%88%E4%B8%8E%E5%BC%B1%E5%BC%95%E7%94%A8%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

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
## 42. How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？

**Core answer / 核心回答：** A callback gives an API a function to call later. A Promise represents one future fulfillment or rejection and composes with then and catch. An async function returns a Promise, while await writes the same control flow in sequential syntax. Promise combinators coordinate already-started work; they do not cancel it. / 回调把函数交给 API 供其稍后调用。Promise 表示未来的一次成功或拒绝，并可通过 then 和 catch 组合。async 函数返回 Promise，await 用顺序语法表达同一控制流。Promise 组合方法协调已经启动的任务，但不会取消它们。


### How callbacks express deferred work / 回调如何表达延后执行

A callback passes a function to an API to be called later. Dependent callback nesting can make control flow and error paths hard to follow; callbacks still fit event handlers and many host APIs. / 回调把函数交给 API，供其稍后调用。若任务相互依赖，层层嵌套会让控制流和错误路径难以跟踪；事件处理器和许多宿主 API 仍适合用回调。

~~~javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
~~~

Promises were standardized in ES2015, async functions and await in ES2017, and async iteration in ES2018. Asynchronous APIs allow a program to continue while work is pending; that does not by itself imply parallel JavaScript computation. / Promise 于 ES2015 标准化，async 函数与 await 于 ES2017 标准化，异步迭代于 ES2018 标准化。异步 API 让程序在等待任务时继续推进，但这本身不表示 JavaScript 计算并行执行。

### What a Promise state means / Promise 状态表示什么

A Promise begins pending and settles once, either fulfilled with a value or rejected with a reason. It cannot change state after settlement. The executor passed to new Promise runs immediately; registered reactions run later as Promise jobs. / Promise 初始处于 pending 状态，之后只会成功完成并带有值，或拒绝并带有原因；完成后状态不可改变。传给 new Promise 的 executor 立即运行；注册的处理器稍后作为 Promise job 运行。

~~~mermaid
stateDiagram-v2
  [*] --> pending
  pending --> fulfilled
  pending --> rejected
  fulfilled --> [*]
  rejected --> [*]
~~~

then returns a new Promise, so a returned value fulfills the next link, a thrown error rejects it, and a returned Promise is adopted. catch handles a rejection; returning normally recovers with its value, while throwing propagates a rejection. / then 会返回一个新 Promise：返回值让下一环节成功完成，抛错会使其拒绝，返回 Promise 时后续会采用其最终状态。catch 处理拒绝；正常返回即以返回值恢复，抛错则继续传播拒绝。

finally normally passes through the original fulfillment value or rejection reason. If its callback throws or returns a rejected Promise, the new chain rejects with that failure. / finally 通常保留原成功值或拒绝原因。若回调抛错或返回拒绝的 Promise，新链会以该错误拒绝。

~~~javascript
const result = getUser(userId)
  .then(user => getOrders(user.id))
  .then(renderOrders)
  .catch(handleError);
~~~

An async function always returns a Promise. Code before its first suspension point runs synchronously. await suspends the async function until its operand settles, then resumes with the value or throws the rejection into the surrounding control flow. / async 函数始终返回 Promise。第一个暂停点之前的代码同步运行。await 会暂停该函数，直到操作数完成，再以成功值继续，或把拒绝原因抛入当前控制流。

~~~javascript
async function loadOrders(userId) {
  try {
    const user = await getUser(userId);
    return await getOrders(user.id);
  } catch (error) {
    handleError(error);
    throw error; // returned Promise remains rejected
  }
}
~~~

For deciding where to recover or propagate a rejection, see [Error Handling / 错误处理](#45.%20Where%20should%20a%20JavaScript%20error%20be%20recovered%20or%20reported?%20/%20JavaScript%20%E9%94%99%E8%AF%AF%E5%BA%94%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%81%A2%E5%A4%8D%E6%88%96%E4%B8%8A%E6%8A%A5%EF%BC%9F).

### Which Promise combinator fits? / 应选择哪个 Promise 组合方法？

| Method / 方法 | Returned Promise fulfills when / 成功条件 | Returned Promise rejects when / 拒绝条件 |
|---|---|---|
| Promise.all | Every input fulfills; result values keep input order / 全部成功；结果按输入顺序排列 | An input rejects / 任一输入拒绝 |
| Promise.allSettled | All inputs settle; each outcome is returned / 全部结束并返回各项结果 | Not because an input rejects / 不会因某项输入拒绝 |
| Promise.any | First input fulfills / 首项成功 | All inputs reject with AggregateError / 全部拒绝并产生 AggregateError |
| Promise.race | First settlement is fulfillment / 首项完成为成功 | First settlement is rejection / 首项完成为拒绝 |

These methods coordinate inputs; they do not cancel losing operations. Passing promises usually means their underlying work has already started. If an API supports cancellation and abandoned work should stop, use its explicit mechanism, such as AbortController with Fetch. / 这些方法用于协调输入，不会取消未获胜的操作。传入 Promise 时，其底层任务通常已经启动。若 API 支持取消且不再需要的工作应停止，使用其显式机制，例如 Fetch 配合 AbortController。

The methods were added across editions: Promise.all and Promise.race in ES2015, Promise.allSettled in ES2020, and Promise.any in ES2021. Their normative completion behavior is in the [ECMAScript Promise combinator algorithms](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-combinator-objects). Promise.race installs both fulfillment and rejection reactions for each input in [PerformPromiseRace](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace).

### When should operations be awaited sequentially or concurrently? / 何时顺序等待，何时并发推进？

Await sequentially when a later operation depends on the earlier result. Start independent operations before awaiting either, then coordinate them with Promise.all when all results are required. This is concurrency, not necessarily parallel JavaScript CPU work: a host may overlap I/O while a JavaScript agent still runs one job at a time. / 后续操作依赖前项结果时顺序 await。操作彼此独立时，应先启动它们，再用 Promise.all 等待所需结果。这是并发，不一定是 JavaScript CPU 计算并行：宿主可重叠处理 I/O，而 JavaScript agent 仍一次执行一个 job。

~~~javascript
// Dependent: the second operation needs the first result.
const user = await fetchUser(id);
const orders = await fetchOrders(user.id);

// Independent: start both before awaiting either.
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts()
]);
~~~

for await...of consumes async iterables in order and can also adapt a synchronous iterable of Promises, awaiting each value before continuing. For independent operations, Promise.all is usually clearer. The protocol and sequential-consumption details belong to [Iterators and Generators / 迭代器与生成器](#44.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F).

### How Promise-job order is observed / 如何观察 Promise job 顺序

Promise reactions are queued as jobs. When one handler queues a later reaction, already-queued jobs run first. The host determines checkpoints, so keep browser task/rendering rules and Node scheduling rules in [Event Loop and Host Scheduling / 事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F), not in this language-level note. / Promise 处理器会排入 job 队列。某个处理器新增后续处理器时，已排队的 job 先运行。检查点由宿主决定；浏览器任务/渲染规则和 Node 调度规则见[事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F)，不在此处混作语言保证。

~~~javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0, 2, 1, 3
~~~

Returning a Promise from a handler makes the next Promise adopt its eventual state. The following observed order is scoped to the tested context, not a portable count of “ticks.” / 处理器返回 Promise 时，后续 Promise 会采用它最终的状态。下例顺序限定于实际测试的上下文，不应转述为跨环境通用的“tick 数”。

~~~javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3));
// Node.js v26.11.1, CommonJS: 0, 1, 2, 3, 4
~~~

See [ECMAScript Promise jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) and the [browser event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops). Node queue ordering and CJS/ESM context are explained separately in the runtime note. The focused [Currying and Partial Application / 柯里化与部分应用](#38.%20How%20does%20currying%20support%20partial%20application?%20/%20%E6%9F%AF%E9%87%8C%E5%8C%96%E5%A6%82%E4%BD%95%E6%94%AF%E6%8C%81%E9%83%A8%E5%88%86%E5%BA%94%E7%94%A8%EF%BC%9F) and [Chainable Task Queue / 链式任务队列](#43.%20How%20can%20a%20chainable%20API%20queue%20delayed%20tasks?%20/%20%E9%93%BE%E5%BC%8F%20API%20%E5%A6%82%E4%BD%95%E6%8E%92%E9%98%9F%E6%89%A7%E8%A1%8C%E5%BB%B6%E5%90%8E%E4%BB%BB%E5%8A%A1%EF%BC%9F) articles preserve two code exercises from the original collection.
## 43. How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？

**Core answer / 核心回答：** A chainable task API can append closures to a queue and return the same builder object. Deferring the first step allows the synchronous chain to finish building before the queue starts. Each task advances the queue only after its own work completes. / 链式任务 API 可把闭包追加到队列并返回同一 builder 对象。延后首步执行可先让同步调用链构建完成；每个任务只在自身工作结束后推进队列。

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

new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
// eat fruit → wake up after 10ms → eat bread
~~~

The time unit is milliseconds. This is a teaching example, not a production queue: it does not define failure handling, cancellation, or behavior when a task never completes. / 时间单位为毫秒。这是教学示例，不是生产队列；它没有定义错误处理、取消方式或任务永不完成时的行为。

For standard Promise composition, rejection propagation, and concurrency, see [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F). Timer callback scheduling is host behavior; see [Event Loop and Host Scheduling / 事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F).
## 44. How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？

**Core answer / 核心回答：** An iterable provides an iterator through Symbol.iterator; each iterator next() call returns an object whose done value tells the consumer whether to stop. A generator implements this protocol by pausing at yield. Async iterables provide next results asynchronously and are consumed in order with for await...of. / 可迭代对象通过 Symbol.iterator 提供迭代器；每次调用 next() 返回带 done 值的对象，用于告知消费者是否停止。生成器在 yield 处暂停，以此实现该协议。异步可迭代对象异步提供 next 结果，并由 for await...of 按序消费。

### How iterable and iterator protocols work / 可迭代与迭代器协议如何工作

The iterable protocol exposes Symbol.iterator, which returns an iterator. The iterator’s next() method returns an object. The consumer converts its done property to Boolean; if done is missing, it acts as false. value supplies the current item and can be absent on completion. An object is not iterable just because it has numeric keys or a length. / 可迭代协议通过 Symbol.iterator 返回迭代器。迭代器的 next() 返回对象。消费者把 done 转为布尔值；若缺少 done，按 false 处理。value 提供当前项，完成时可以省略。有数字键或 length 的对象不会自动变成可迭代对象。

The protocol is defined by the [ECMAScript iteration interfaces](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration). / 协议定义见 [ECMAScript 迭代接口](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration)。

Arrays, strings, Maps, Sets, typed arrays, and arguments objects are language-provided iterables. A DOM `NodeList` also supports iteration. Its source API determines whether membership is live or static, which matters if you mutate the DOM while iterating. [DOM collection semantics](#53.%20What%20is%20the%20difference%20between%20an%20HTMLCollection%20and%20a%20NodeList?%20/%20HTMLCollection%20%E4%B8%8E%20NodeList%20%E6%9C%89%E4%BB%80%E4%B9%88%E5%8C%BA%E5%88%AB%EF%BC%9F) Plain objects are not iterable by default. / 数组、字符串、Map、Set、类型化数组和 arguments 对象由语言提供迭代能力。现代浏览器 DOM 实现中的 NodeList 也可迭代，但它是宿主 API，不是 JavaScript 语言集合。普通对象默认不可迭代。

~~~javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }

for (const [key, value] of new Map([["x", 1], ["y", 2]])) {
  console.log(key, value);
}
~~~

~~~mermaid
flowchart LR
  A["Iterable: Symbol.iterator()"] --> B["Iterator: next()"]
  B --> C{"Boolean(result.done)"}
  C -- "false" --> D["Use result.value"]
  D --> B
  C -- "true" --> E["Stop"]
~~~

An iterable can return a fresh iterator each time, but the protocol does not require that. Iterator objects and generators often return themselves and are one-shot. / 可迭代对象可以每次都返回新迭代器，但协议不要求如此。迭代器对象和生成器通常返回自身，因此只能消费一次。

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

### How early exit closes an iterator / 提前退出如何关闭迭代器

An iterator may expose return() as a cleanup hook. for...of closes the iterator when break or an abrupt completion such as an exception exits the loop. / 迭代器可提供 return() 清理钩子。break 或异常等 abrupt completion 离开 for...of 时，循环会关闭迭代器。

~~~javascript
const source = {
  [Symbol.iterator]() {
    let value = 0;
    return {
      next() {
        return { value: value++, done: false };
      },
      return() {
        console.log("release iterator resource");
        return { done: true };
      }
    };
  }
};

for (const value of source) {
  if (value === 2) break; // calls return() before leaving
}
~~~

The specification’s [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose) algorithm defines this cleanup behavior. It also defines how the consumer interprets iterator results in [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete).

### What yield and next(value) exchange / yield 与 next(value) 交换什么

A generator function returns an object that is both iterable and an iterator. yield pauses execution and produces a value; the next() call resumes it. The first next(value) argument is ignored because execution has not paused at a yield yet. Later arguments become the result of the suspended yield expression. / 生成器函数返回同时是可迭代对象和迭代器的对象。yield 暂停执行并产出值；调用 next() 时恢复。第一次 next(value) 的参数会被忽略，因为函数尚未暂停在 yield；之后传入的值会成为暂停处 yield 表达式的结果。

~~~javascript
function* conversation() {
  const name = yield "What is your name?";
  const hobby = yield "Hello, " + name + "! What do you enjoy?";
  return name + " likes " + hobby;
}

const chat = conversation();
chat.next();          // { value: "What is your name?", done: false }
chat.next("Ada");     // { value: "Hello, Ada! What do you enjoy?", done: false }
chat.next("coding");  // { value: "Ada likes coding", done: true }
~~~

yield* delegates iteration to another iterable or generator and receives its completion result. It can compose recursive traversals. / yield* 把迭代委托给另一个可迭代对象或生成器，并接收其完成结果，可用于组合递归遍历。

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
  const completion = yield* child();
  return completion;
}
const delegated = parent();
delegated.next(); // { value: "item", done: false }
delegated.next(); // { value: 42, done: true }
~~~

### Why generators are useful for lazy sequences / 生成器为何适合惰性序列

Generators compute on demand, so the consumer controls how many values to request. This can represent large or infinite sequences without storing every value in an array. / 生成器按需计算，由消费者决定请求多少项，因此可表示大型或无限序列，而不必预存所有值。

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

function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}
const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
~~~

Before async/await, libraries such as co used a runner to yield Promises from generators and resume with their results. This is a historical pattern; async functions standardize another syntax and runtime protocol, rather than exposing a generator implementation. / async/await 出现以前，co 等库通过 runner 让生成器 yield Promise，再根据结果恢复执行。这是历史模式；async 函数标准化的是另一种语法与运行时协议，并非直接暴露生成器实现。

### How async iteration differs / 异步迭代有何不同

An async iterable (standardized in ES2018) supplies Symbol.asyncIterator. Each next() call makes its iterator result available asynchronously; for await...of waits for each result in sequence. This suits streams whose next value becomes available over time. A synchronous array of independent Promises is usually clearer with Promise.all. / 异步可迭代对象（ES2018 标准化）通过 Symbol.asyncIterator 提供迭代器，每次 next() 异步提供迭代结果；for await...of 按顺序等待各项，适合后续值逐渐到达的流。同步数组中相互独立的 Promise 通常用 Promise.all 更清晰。

`for await...of` can also consume a synchronous iterable of Promises, awaiting each yielded value before requesting the next one. If the Promises have already started, this preserves input order rather than yielding whichever finishes first. / `for await...of` 也能消费由 Promise 组成的同步可迭代对象；每项完成后才继续请求下一项。即使 Promise 已经启动，结果仍按输入顺序处理，而非按最快完成顺序产出。

~~~javascript
async function collectInOrder(tasks) {
  const values = [];
  for await (const value of tasks) values.push(value);
  return values;
}

collectInOrder([Promise.resolve("first"), Promise.resolve("second")])
  .then(values => console.log(values)); // ["first", "second"]
~~~

See [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) for Promise aggregation and host scheduling. Browser and Node event-loop details remain in [Event Loop and Host Scheduling / 事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F).
## 45. Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？

**Core answer / 核心回答：** Handle a failure at the layer with enough context to recover, add information, or report it. If the current layer cannot decide what recovery means, propagate the error. A catch that only logs and returns can silently turn failure into success; browser-global and React handlers cover specific last-resort scopes. / 应在拥有足够上下文进行恢复、补充信息或上报的层级处理错误。当前层无法决定如何恢复时，应继续传播。只记录日志后正常返回的 catch 会悄悄把失败转成成功；浏览器全局处理器和 React 边界只覆盖特定的兜底范围。

### What try/catch/finally cover / try/catch/finally 能处理什么

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

### When to define a custom Error / 何时定义自定义 Error

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

### How to propagate or recover a Promise rejection / 如何传播或恢复 Promise 拒绝

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

Every rejection needs an owner somewhere in the call chain. The browser’s unhandledrejection event is useful for diagnostics, but it is a late signal, not a substitute for local recovery or deliberate propagation. Host reporting and process behavior differ. See [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) for Promise chain mechanics. / 每个拒绝都应由调用链某处明确负责。浏览器的 unhandledrejection 事件可用于诊断，但只是较晚的信号，不能替代本地恢复或明确传播。宿主上报和进程行为有所不同。Promise 链机制见 [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

### What browser-global handlers cover / 浏览器全局处理器覆盖什么

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

### What React error boundaries cover / React 错误边界覆盖什么

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
## 46. How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？

**Short answer / 简答** — Treat API bodies and browser storage as untrusted runtime data. Parse into `unknown`, check syntax and shape, then construct a value whose fields match the application's type. The checker can enforce exhaustive use of that type. The parser does not establish whether a supplied role or identity claim is authorized. / 把 API 响应和浏览器存储视为不可信数据。先解析为 `unknown`，校验语法和结构，再构造与应用类型匹配的值。编译器可以检查是否处理所有受支持的类型分支。结构校验无法证明输入里的角色或身份已经获得授权。

Type annotations are erased from emitted JavaScript. TypeScript’s type system also makes deliberate soundness tradeoffs, and any or an unchecked assertion can bypass useful checks. / 类型注解会从生成的 JavaScript 中擦除。TypeScript 类型系统也有意作出某些健全性取舍；any 或未校验的断言会绕过有效检查。

~~~mermaid
flowchart LR
  A["External text"] --> B{"JSON.parse"}
  B -- "syntax error" --> E["Parse error result"]
  B -- "valid syntax: unknown" --> C{"Runtime shape and value checks"}
  C -- "invalid shape" --> E
  C -- "valid Profile" --> D["Construct typed value"]
~~~

### Validate a value at runtime / 在运行时校验值

JSON.parse can throw for malformed JSON and, on success, still says nothing about the object’s shape. Keep the parsed result as unknown so every property access follows a runtime guard. This example handles syntax and shape failures without an unchecked cast; the storage adapter also makes a missing key explicit. / JSON.parse 遇到格式错误的 JSON 会抛错；成功解析也不能说明对象结构正确。将结果保留为 unknown，使每次属性读取都必须经过运行时保护。此示例不使用未经检查的类型断言来处理语法和结构错误；存储适配器也显式处理缺失键。

~~~typescript
type Profile = {
  id: string;
  label: string;
  role: "admin" | "reader";
};

type ParseResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseProfile(text: string): ParseResult<Profile> {
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return { ok: false, error: "Invalid JSON syntax" };
  }

  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.label !== "string" ||
    (value.role !== "admin" && value.role !== "reader")
  ) {
    return { ok: false, error: "Expected id, label, and a known role" };
  }

  return {
    ok: true,
    value: { id: value.id, label: value.label, role: value.role }
  };
}

function readStoredProfile(storage: Storage): ParseResult<Profile> {
  const text = storage.getItem("profile");
  if (text === null) return { ok: false, error: "No saved profile" };
  return parseProfile(text);
}

const valid = parseProfile('{"id":"u-7","label":"Ada","role":"reader"}');
const malformed = parseProfile('{"id":7,"label":"Ada","role":"reader"}');
// valid.ok is true; malformed.ok is false with a structural error.
~~~

### Handle every validated variant / 处理每个已校验的分支

Callers first inspect `ParseResult.ok`. After the parser succeeds, the UI can narrow on the validated role. Assign the unhandled default value to `never` so an added role becomes a compile error at this switch.

~~~typescript
function roleLabel(role: Profile["role"]): string {
  switch (role) {
    case "admin":
      return "Administrator";
    case "reader":
      return "Reader";
    default: {
      const unhandled: never = role;
      throw new Error(`Unhandled role: ${unhandled}`);
    }
  }
}

if (valid.ok) roleLabel(valid.value.role); // "Reader"
~~~

If the server introduces `editor`, the parser still rejects it until the client deliberately supports it. When you add `editor` to `Profile["role"]`, the missing switch case fails the `never` assignment. Update the runtime guard and the consumers together. These checks serve different points in the same data path. The runtime parser protects the input boundary, while the compiler checks the supported cases at this switch. / 输入校验挡住外部未知值，`never` 让受支持的类型新增分支时在该 switch 报错。 [TypeScript handbook on exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)

Utility types and generics describe compile-time relationships, not runtime guards: [Utility Types / 工具类型](#48.%20What%20do%20TypeScript%20utility%20types%20guarantee?%20/%20TypeScript%20%E5%B7%A5%E5%85%B7%E7%B1%BB%E5%9E%8B%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F), [Generics / 泛型](#47.%20How%20do%20TypeScript%20generics%20preserve%20relationships%20between%20types?%20/%20TypeScript%20%E6%B3%9B%E5%9E%8B%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E7%B1%BB%E5%9E%8B%E4%B9%8B%E9%97%B4%E7%9A%84%E5%85%B3%E7%B3%BB%EF%BC%9F). Decorator modes answer a separate class-definition question: [TypeScript Decorators / TypeScript 装饰器](#49.%20Which%20TypeScript%20decorator%20mode%20does%20a%20project%20use?%20/%20%E9%A1%B9%E7%9B%AE%E4%BD%BF%E7%94%A8%E5%93%AA%E7%A7%8D%20TypeScript%20%E8%A3%85%E9%A5%B0%E5%99%A8%E6%A8%A1%E5%BC%8F%EF%BC%9F). JavaScript Proxy is a runtime object feature, not a TypeScript type feature; see [JavaScript Proxy / JavaScript Proxy](#37.%20How%20does%20JavaScript%20Proxy%20intercept%20object%20operations?%20/%20JavaScript%20Proxy%20%E5%A6%82%E4%BD%95%E6%8B%A6%E6%88%AA%E5%AF%B9%E8%B1%A1%E6%93%8D%E4%BD%9C%EF%BC%9F).

**Sources checked 2026-10-15:** [TypeScript Basic Types and unknown](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types and assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions), and [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness).
## 47. How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？

**Core answer / 核心回答：** A generic type parameter preserves a relationship between inputs and outputs. TypeScript can infer a parameter from a call, while an extends constraint limits the values it accepts. Use generics when the same logic should preserve specific types across multiple callers. / 泛型参数用于保留输入与输出之间的关系。TypeScript 可从调用中推断类型参数；extends 约束限制可接受的值。当同一逻辑需要为不同调用者保留各自具体类型时，使用泛型。

~~~typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30 };
const userName = getProperty(user, "name"); // string
// getProperty(user, "phone"); // Type error: no such key
~~~

Here K must be a key of T. The indexed access type T[K] connects the chosen key to its corresponding property type; the function does not widen every result to a union of all possible property types. / 这里 K 必须是 T 的键。索引访问类型 T[K] 把所选键与对应属性类型关联起来；函数不会把每个结果都扩大成所有属性类型的联合。

A generic interface preserves the same relationship across a group of operations: / 泛型接口可让一组操作共享同一种类型关系：

~~~typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}
~~~

A type parameter is not a runtime check. It describes a contract enforced by the checker where type information is available. External values still need runtime validation; see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#46.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript Generics handbook](https://www.typescriptlang.org/docs/handbook/2/generics.html).
## 48. What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？

**Core answer / 核心回答：** Utility types derive one compile-time type from another, helping related shapes stay connected instead of repeating property declarations. They do not change or validate runtime values. Readonly is shallow and does not freeze an object; Partial does not validate a request. / 工具类型从已有类型推导出新编译期类型，避免重复声明并让相关结构保持关联。它们不会改变或验证运行时值。Readonly 是浅层的，也不会冻结对象；Partial 不会校验请求。

| Utility type / 工具类型 | Type-level result / 类型结果 |
|---|---|
| Partial<T> | Makes each property optional / 所有属性可选 |
| Required<T> | Makes each property required / 所有属性必需 |
| Readonly<T> | Makes each property readonly at compile time; shallow / 编译期只读；浅层 |
| Pick<T, K> / Omit<T, K> | Selects or removes keys / 选择或移除属性 |
| Record<K, V> | Describes keys and values of an object shape / 描述对象键和值 |
| Exclude<U, X> / Extract<U, X> | Removes from or selects members of a union / 从联合中排除或选取成员 |
| NonNullable<T> | Removes null and undefined / 移除 null 和 undefined |
| ReturnType<F> / Parameters<F> | Extracts a function return type or parameter tuple / 提取返回类型或参数元组 |
| InstanceType<C> / ConstructorParameters<C> | Extracts a class instance type or constructor parameter tuple / 提取类实例类型或构造参数元组 |
| ThisType<T> | Contextual `this` type marker for object-literal methods; it does not change runtime values / 对象字面量方法的上下文 `this` 类型标记；不改变运行时值 |

~~~typescript
interface User {
  id: number;
  name: string;
  email: string;
}

type UserPreview = Pick<User, "id" | "name">;
type UserPatch = Partial<Pick<User, "name" | "email">>;

type Role = "admin" | "editor" | "reader";
const permissions: Record<Role, string[]> = {
  admin: ["read", "write"],
  editor: ["read", "write"],
  reader: ["read"]
};
~~~

UserPatch expresses an allowed shape to the checker; runtime code still needs to validate parsed JSON. For that boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#46.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript Utility Types reference](https://www.typescriptlang.org/docs/handbook/utility-types.html).

### How does ThisType contextually type this? / ThisType 如何提供 this 的上下文类型？

`ThisType<T>` is a contextual-typing marker for `this` inside object-literal methods. It does not add a property or bind a runtime receiver, and the check depends on `noImplicitThis`. An explicit `this: Person` parameter is a separate compile-time receiver annotation. / `ThisType<T>` 是对象字面量方法中 `this` 的上下文类型标记。它不会添加属性或绑定运行时接收者，相关检查依赖 `noImplicitThis`。显式的 `this: Person` 参数则是另一种编译期接收者注解。

~~~typescript
type ObjectDescriptor<Data, Methods> = {
  data: Data;
  methods: Methods & ThisType<Data & Methods>;
};

function makeObject<Data, Methods>(descriptor: ObjectDescriptor<Data, Methods>): Data & Methods {
  return { ...descriptor.data, ...descriptor.methods };
}

const counter = makeObject({
  data: { value: 0 },
  methods: { increment() { this.value += 1; } }
});
counter.increment(); // this.value is contextually typed as number
~~~

~~~typescript
interface Person {
  name: string;
  greet(this: Person): void;
}

const person: Person = {
  name: "Ada",
  greet() { console.log(this.name); }
};
~~~
## 49. Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？

**Core answer / 核心回答：** TypeScript supports standard ECMAScript decorators and a separate legacy mode. Their signatures and capabilities differ. Use the mode required by the framework and compiler configuration; do not copy a decorator from a different project without checking its mode. / TypeScript 支持标准 ECMAScript 装饰器和独立的旧版模式。两者的签名与能力不同。应使用框架和编译配置要求的模式，不要未确认模式就复制其他项目的装饰器。

### Standard decorators in TypeScript 5.0 and later / TypeScript 5.0 及之后的标准装饰器

A standard method decorator receives the original method and a context object; it may return a replacement method. / 标准方法装饰器接收原始方法和上下文对象，也可以返回替代方法。

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
    console.log("calling", name);
    return original.call(this, ...args);
  };
}

class Calculator {
  @loggedMethod
  add(a: number, b: number) {
    return a + b;
  }
}
~~~

Standard decorators do not support parameter decorators and are not compatible with emitDecoratorMetadata. / 标准装饰器不支持参数装饰器，也不兼容 emitDecoratorMetadata。

### Legacy decorator mode / 旧版装饰器模式

Existing Angular, NestJS, and ORM projects may use legacy decorator mode enabled by experimentalDecorators. A legacy method decorator receives a target, property key, and property descriptor, unlike the standard signature. Legacy emitDecoratorMetadata also belongs to this mode. / 既有 Angular、NestJS 和 ORM 项目可能使用 experimentalDecorators 启用的旧版模式。旧版方法装饰器接收 target、属性键和属性描述符，与标准签名不同；旧版 emitDecoratorMetadata 也属于该模式。

~~~typescript
function legacyLog(
  target: object,
  key: string | symbol,
  descriptor: PropertyDescriptor
) {
  const original = descriptor.value;
  descriptor.value = function (...args: unknown[]) {
    console.log("calling", key);
    return original.apply(this, args);
  };
}
~~~

Decorator metadata is not general runtime validation. For an external JSON value, validate the value itself with runtime logic or a validation library. For the separate unknown-JSON runtime boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#46.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript 5.0 decorator release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators). Sources checked 2026-10-15.
## 50. How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？

**Core answer / 核心回答：** ECMAScript modules (ESM) are standardized JavaScript syntax with static imports and exports, module-scoped bindings, strict mode, and top-level this equal to undefined. CommonJS (CJS) is Node’s module wrapper using require and module.exports. Module syntax, host loading rules, bundler analysis, and runtime scheduling are separate concerns. / ECMAScript 模块（ESM）是标准 JavaScript 语法，使用静态导入与导出，绑定属于模块作用域，自动采用严格模式，顶层 this 为 undefined。CommonJS（CJS）是 Node 使用 require 和 module.exports 的模块包装机制。模块语法、宿主加载规则、打包器分析和运行时调度是不同问题。

### ESM syntax and dynamic import / ESM 语法与动态导入

Static import and export declarations are part of ECMAScript. Top-level await was standardized in ES2022. Dynamic import() returns a Promise and Node supports it from either module system. / 静态 import 与 export 声明属于 ECMAScript。顶层 await 于 ES2022 标准化。动态 import() 返回 Promise，Node 两种模块系统都支持它。

~~~javascript
// features.mjs
export const featureName = "search";
export default function createFeature() {
  return featureName;
}
~~~

~~~javascript
// app.mjs
import createFeature, { featureName } from "./features.mjs";
export { featureName };

createFeature(); // "search"
import("./features.mjs").then(({ featureName }) => featureName);
~~~

### What differs between ESM and CJS / ESM 与 CJS 有何不同

| Concern / 维度 | ECMAScript module / ES 模块 | Node CommonJS / Node CommonJS |
|---|---|---|
| Static syntax / 静态语法 | import, export | require(), module.exports |
| Top-level await / 顶层 await | Supported / 支持 | Not supported in a CJS wrapper / CJS 包装器中不支持 |
| Top-level this / 顶层 this | undefined | Node wrapper’s exports value / Node 包装器的 exports 值 |
| Strict mode / 严格模式 | Automatic / 自动采用 | Depends on code context / 取决于代码上下文 |

Node determines whether a file is ESM or CJS using extensions, package settings, or explicit input options; browser module loading follows browser rules. CommonJS is not ECMAScript module syntax. / Node 根据扩展名、包配置或显式输入选项判断文件属于 ESM 还是 CJS；浏览器模块加载遵循浏览器规则。CommonJS 不是 ECMAScript 模块语法。

See the [ECMAScript module specification](https://tc39.es/ecma262/2025/multipage/ecmascript-language-scripts-and-modules.html) and [Node.js ESM documentation](https://nodejs.org/api/esm.html). This page describes module semantics and loading boundaries, not Node event-loop ordering; see [Event Loop and Host Scheduling / 事件循环与宿主调度](#5.%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E4%BD%95%E6%97%B6%E8%BF%90%E8%A1%8C%EF%BC%8C%E7%94%BB%E9%9D%A2%E4%BD%95%E6%97%B6%E6%9B%B4%E6%96%B0%EF%BC%9F) for scheduling.

### Why ESM syntax does not guarantee tree shaking / 为什么 ESM 语法不保证 tree shaking

A bundler can analyze ESM imports for tree shaking, but using ESM syntax alone does not guarantee code removal. The result depends on the bundler and package metadata. See [Build Tools / 构建工具](#52.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F) for the transform and production-output boundary. / 打包器可分析 ESM 导入并执行 tree shaking，但仅使用 ESM 语法并不保证代码会被移除；结果还取决于打包器和包元数据。变换与生产产物边界见 [Build Tools / 构建工具](#52.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F).
## 51. How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？

**Core answer / 核心回答：** A feature’s ECMAScript edition and support in the target runtime are separate facts. Syntax must parse in the target environment or be transformed; APIs also need runtime support or a suitable polyfill. Check the actual browsers, Node versions, and build target before relying on a feature. / 特性属于哪个 ECMAScript 版本，与目标运行时是否支持是两件事。语法必须能被目标环境解析或经过转换；API 也需要运行时实现或合适的 polyfill。依赖某项特性前要检查实际浏览器、Node 版本和构建目标。

### Selected APIs and edition boundaries / 部分 API 与版本边界

| Feature / 特性 | Edition or source / 版本或来源 | Boundary / 边界 |
|---|---|---|
| Object.keys | ES5 | Own enumerable string keys / 自有可枚举字符串键 |
| Object.assign, Object.is | ES2015 | Object.assign mutates its target; Object.is uses SameValue / Object.assign 会修改目标；Object.is 使用 SameValue |
| Object.values, Object.entries | ES2017 | Own enumerable string-keyed values or pairs / 自有可枚举字符串键的值或键值对 |
| Array.from, Array.of | ES2015 | Iterable/array-like conversion or argument list / 可迭代或类数组转换，或参数列表建数组 |
| Promise.all, Promise.race | ES2015 | Outcome semantics and cancellation limits: see [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 完成条件和不取消其他操作见异步页 |
| Promise.allSettled | ES2020 | See [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 见异步页的 Promise 比较表 |
| Promise.any | ES2021 | See [Asynchronous JavaScript / 异步 JavaScript](#42.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 见异步页的 Promise 比较表 |
| globalThis | ES2020 | Current realm’s global object; host-specific properties differ / 当前 realm 的全局对象；宿主属性不同 |
| Array.prototype.at | ES2022 | Supports negative offsets from the end / 支持从末尾反向计数 |
| Object.hasOwn | ES2022 | Own-property test works with null-prototype objects and overridden hasOwnProperty / 可用于 null 原型对象和被覆盖的 hasOwnProperty |
| structuredClone | Host API, not an ECMAScript edition feature / 宿主 API，不属于 ECMAScript 版本特性 | Structured-cloneable values, cycles, Map, Set, Date; not functions or custom class prototypes / 支持结构化克隆值、循环引用、Map、Set、Date；不支持函数或自定义类原型 |

The edition number does not establish that a particular browser or runtime build implements the feature. Syntax transforms also do not automatically supply missing built-in APIs. Verify the configured target and run checks in the actual runtime set. / 版本号并不能证明特定浏览器或运行时构建实现了该特性。语法转换也不会自动补齐缺少的内置 API。应核对配置目标，并在实际运行环境中检查。

~~~javascript
const values = ["first", "last"];
values.at(-1); // "last"

const options = Object.create(null);
options.enabled = false;
Object.hasOwn(options, "enabled"); // true
~~~

structuredClone is exposed by browsers and current Node releases, but it does not preserve custom class prototypes or clone functions; unsupported values can throw DataCloneError. Do not assume it is faster than another copying method. See the [HTML structured clone algorithm](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) and [Node global API](https://nodejs.org/api/globals.html#structuredclonevalue-options). Sources checked 2026-10-15. / structuredClone 可由浏览器和当前 Node 版本使用，但不会保留自定义类原型或复制函数；不支持的值可能抛出 DataCloneError。不要假设它必然比其他复制方法快。见 [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) 与 [Node 全局 API](https://nodejs.org/api/globals.html#structuredclonevalue-options)。来源核对日期：2026-10-15。

For edition-specific language features, see the [ECMAScript 2025 specification](https://tc39.es/ecma262/2025/). / 版本相关语言特性见 [ECMAScript 2025 规范](https://tc39.es/ecma262/2025/)。

**See also:** [Optional Chaining and Destructuring / 可选链与解构](#%E7%BC%BA%E5%A4%B1%E5%B1%9E%E6%80%A7%E9%BB%98%E8%AE%A4%E5%80%BC%E4%B8%8E%E8%A7%A3%E6%9E%84) explains syntax semantics; [Modules and Host Boundaries / 模块与宿主边界](#50.%20How%20do%20ECMAScript%20modules%20and%20CommonJS%20differ?%20/%20ECMAScript%20%E6%A8%A1%E5%9D%97%E4%B8%8E%20CommonJS%20%E6%9C%89%E4%BD%95%E5%8C%BA%E5%88%AB%EF%BC%9F) explains ESM and CommonJS; [Object helpers / 对象辅助方法](#%E6%9E%9A%E4%B8%BE%E4%B8%8E%E5%A4%8D%E5%88%B6%E5%B1%9E%E6%80%A7%E6%97%B6%EF%BC%8C%E5%85%88%E7%9C%8B%20API%20%E9%80%89%E4%B8%AD%E4%BA%86%E4%BB%80%E4%B9%88) and [Array helpers / 数组辅助方法](#%E4%BB%8E%E8%BF%AD%E4%BB%A3%E5%99%A8%E6%88%96%E7%B1%BB%E6%95%B0%E7%BB%84%E8%BE%93%E5%85%A5%E5%88%9B%E5%BB%BA%E6%95%B0%E7%BB%84) covers property-copying and enumeration behavior.
## 52. How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？

**Core answer / 核心回答：** A bundler follows a module graph, transforms selected modules, and emits assets. Loaders transform individual modules; plugins use broader compiler hooks. A successful development server does not prove that the production build has the same assets, paths, chunks, or source-map exposure. / 打包器沿模块图解析依赖、转换选定模块并输出资源。loader 转换单个模块；plugin 通过更广泛的 compiler hooks 扩展构建。开发服务器成功不代表生产构建具有相同资源、路径、分块或 source map 暴露方式。

~~~mermaid
flowchart LR
  A["Entry points"] --> B["Resolve module graph"]
  B --> C["Apply loaders / transforms"]
  C --> D["Compiler and plugin hooks"]
  D --> E["Emit production assets and maps"]
  E --> F["Serve and inspect built output"]
~~~

### Pin the toolchain before building / 构建前固定工具链

`package.json` can record a project’s package manager and version, for example `"packageManager": "pnpm@10.0.0"` in a project that has tested that version. Provision the pinned tool in both CI and local development, then install from the committed lockfile. The field describes the expected tool. Corepack’s installed shims can select it, but the field alone does not install a manager. Node.js distributed Corepack starting with the 14.19 and 16.9 release lines through Node 24 and dropped it from Node 25 onward. Provision Corepack separately or use the package manager's documented installer. / 声明工具版本后，CI 和本地还需要安装相同版本并按锁文件安装依赖。 [Corepack project README](https://github.com/nodejs/corepack#readme) · [Node.js 25 release](https://nodejs.org/en/blog/release/v25.0.0)

### How Webpack loaders and plugins differ / Webpack loader 与 plugin 有何不同

Webpack starts from configured entries, resolves their dependency graph, applies loaders to modules, and emits assets. Configuration names entry points, output, mode, module rules, plugins, and optimization. / Webpack 从配置的入口出发解析依赖图，对模块执行 loader，再输出资源。配置项包括 entry、output、mode、module rules、plugins 和 optimization。

| Term / 名称 | Role / 作用 |
|---|---|
| Entry | Starting point for dependency resolution / 依赖解析的起点 |
| Output | Destination and naming for emitted assets / 输出资源的目录和命名 |
| Loader | Transforms one module’s source before bundling / 打包前转换单个模块源码 |
| Plugin | Hooks into compiler or compilation stages for broader behavior / 通过 compiler 或 compilation 阶段扩展行为 |
| Mode | Enables development or production defaults; explicit settings may override / 启用开发或生产默认值；显式设置可覆盖 |

Normal loader functions run right to left. Pitch functions, when present, run left to right. / 普通 loader 函数从右向左执行；若有 pitch 函数，则从左向右执行。

~~~javascript
module: {
  rules: [
    {
      test: /\.tsx?$/,
      use: ["babel-loader", "ts-loader"]
    },
    {
      test: /\.scss$/,
      use: ["style-loader", "css-loader", "sass-loader"]
    }
  ]
}
~~~

For the TypeScript rule, ts-loader runs first and its output goes to babel-loader. Choose one clear TypeScript transform pipeline; overlapping transforms can add cost or change output unexpectedly. / TypeScript 规则中 ts-loader 先运行，其输出再交给 babel-loader。应选择清晰的 TypeScript 转换链；重叠转换可能增加成本或意外改变产物。

Common loader roles include JS/TS transforms, style processing, and static assets. Webpack 5 Asset Modules can emit or inline assets without older file-loader/url-loader setups. The exact loader stack depends on the project. / 常见 loader 用于 JS/TS 转换、样式处理和静态资源。Webpack 5 Asset Modules 可直接输出或内联资源，不必沿用旧式 file-loader/url-loader 配置。具体链路取决于项目需求。

A text replacement loader illustrates the loader shape, but it does not parse JavaScript syntax. Use a syntax-aware transform when source structure matters. / 字符串替换示例说明 loader 形式，但不会解析 JavaScript 语法；源码结构重要时应使用语法感知的转换器。

~~~javascript
module.exports = function replaceBuildLabel(source) {
  return source.replaceAll("__BUILD_LABEL__", "demo");
};
~~~

A plugin can subscribe to compiler hooks. The done hook runs after compilation and is an AsyncSeriesHook; synchronous handlers can use tap, while asynchronous handlers can use tapAsync or tapPromise so the hook waits for their work. / plugin 可订阅 compiler hooks。done hook 在编译结束后运行，是 AsyncSeriesHook；同步处理器可用 tap，异步处理器可用 tapAsync 或 tapPromise，以便 hook 等待其工作。

~~~javascript
class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tap("BuildStatsPlugin", stats => {
      const json = stats.toJson({ modules: false });
      require("node:fs").writeFileSync(
        "build-stats.json",
        JSON.stringify(json, null, 2)
      );
    });
  }
}
~~~

Example plugins have distinct roles: HtmlWebpackPlugin can generate HTML and inject emitted assets; DefinePlugin replaces configured expressions at compile time rather than reading a browser runtime environment variable; MiniCssExtractPlugin can emit CSS files. They are examples, not a required stack. As of the Webpack docs checked on 2026-10-15, the HtmlWebpackPlugin README marks it deprecated while the native HTML guide describes experiments.html and output.html as alternatives and still labels native HTML experimental. Check installed Webpack version and template needs before migrating. / 插件示例作用不同：HtmlWebpackPlugin 可生成 HTML 并注入输出资源；DefinePlugin 在编译时替换配置表达式，不会读取浏览器运行时环境变量；MiniCssExtractPlugin 可把 CSS 输出为独立文件。它们只是示例，不是必需组合。根据 2026-10-15 核对的 Webpack 文档，HtmlWebpackPlugin README 标记已弃用；原生 HTML 指南介绍 experiments.html 与 output.html 作为替代方案，同时仍标为实验性。迁移前应检查所用 Webpack 版本和模板需求。

Sources checked 2026-10-15: [Webpack Loaders](https://webpack.js.org/concepts/loaders/), [Asset Modules](https://webpack.js.org/guides/asset-modules/), [Webpack Plugins](https://webpack.js.org/concepts/plugins/), [DefinePlugin](https://webpack.js.org/plugins/define-plugin/), [HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme), [Webpack Native HTML guide](https://webpack.js.org/guides/native-html/), [style-loader](https://github.com/webpack/style-loader#readme), [css-loader](https://github.com/webpack-contrib/css-loader#readme), [MiniCssExtractPlugin](https://github.com/webpack/mini-css-extract-plugin#readme), [Webpack: Writing a Plugin](https://webpack.js.org/contribute/writing-a-plugin/), [Compiler hooks](https://webpack.js.org/api/compiler-hooks/).

### Why Vite development and production need separate checks / 为什么 Vite 开发与生产需要分别检查

The standard Vite development path serves native ES modules with on-demand transforms and HMR. Vite 8 uses Rolldown for production builds. Check the project's selected development mode and production settings when diagnosing differences. / Vite 的常规开发路径用原生 ES 模块、按需转换和 HMR 提供资源。Vite 8 的生产构建使用 Rolldown。排查差异时看该项目选用的开发模式和生产配置。

A fast development server is not evidence that production output has the same graph or performance. Run the configured production build and inspect its generated assets. For release verification, serve the generated output and check actual paths and chunks; HMR only validates the development loop. / 开发服务器速度快并不能证明生产产物具有相同依赖图或性能。应运行配置的生产构建并检查输出资源。发布验证要服务生成的产物并检查实际路径和分块；HMR 只验证开发循环。

Sources checked 2026-10-15: [Vite 8 guide](https://vite.dev/guide/) and [Vite 8.0.10 source](https://github.com/vitejs/vite/blob/v8.0.10/README.md).

### What a source map exposes / Source map 会暴露什么

A source map relates emitted code to source files for debugging and error reporting. Choose Webpack devtool by rebuild speed, trace detail, artifact size, and whether the map is published. A privately uploaded map can still be exposed if deployment serves it publicly; configuration alone does not define access policy. / source map 将输出代码关联回源文件，用于调试和错误报告。选择 Webpack devtool 时要看重建速度、追踪细节、产物大小和是否公开 map。私下上传的 map 若部署时能被公开访问，仍可能暴露；配置本身不等于访问策略。

| devtool example | Output meaning / 输出含义 |
|---|---|
| eval-source-map | Evaluates modules with source maps for development debugging / 开发调试用 eval 与 source map |
| source-map | Emits an external map with a sourceMappingURL reference / 输出外部 map 并带 sourceMappingURL 引用 |
| hidden-source-map | Emits an external map without the reference comment; useful when a release process uploads maps separately / 输出外部 map 但无引用注释；适合由发布流程单独上传 |
| nosources-source-map | Omits embedded source content, but mappings and source paths may remain / 不嵌入源码内容，但映射和源码路径仍可能存在 |

These names represent different detail and delivery choices, not a universal speed ranking or security boundary. See [Webpack devtool configuration](https://webpack.js.org/configuration/devtool/). Release mapping and access control belong to the release process; see [Frontend Testing / 前端测试](#65.%20What%20evidence%20shows%20a%20frontend%20change%20works%20through%20production%20delivery?%20/%20%E5%93%AA%E4%BA%9B%E8%AF%81%E6%8D%AE%E8%83%BD%E8%AF%81%E6%98%8E%E5%89%8D%E7%AB%AF%E6%94%B9%E5%8A%A8%E5%8F%AF%E7%94%A8%E5%B9%B6%E8%83%BD%E6%AD%A3%E7%A1%AE%E4%BA%A4%E4%BB%98%EF%BC%9F) for built-output browser smoke checks and [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) for the shared release path.
## 53. What is the difference between an HTMLCollection and a NodeList? / HTMLCollection 与 NodeList 有什么区别？

Both are array-like collections of DOM nodes, but they differ in which nodes they contain and whether their view updates. An `HTMLCollection` contains elements and is live. A `NodeList` may include text and comment nodes; whether it is live depends on the API that returned it: `querySelectorAll()` is static, while `childNodes` is live. Choose from the returned API's contract, and avoid mutating a live collection while advancing forward through its indexes. / 两者都是类数组的 DOM 节点集合，但包含的节点类型和更新方式不同。`HTMLCollection` 只含元素且是实时集合。`NodeList` 可含文本和注释节点；是否实时取决于返回它的 API：`querySelectorAll()` 是静态集合，而 `childNodes` 是实时集合。应根据具体 API 的契约选择，并避免在正向按索引遍历时修改实时集合。

| Collection | Typical source | Contents | Update behavior |
|---|---|---|---|
| `HTMLCollection` | `getElementsByClassName()`, `getElementsByTagName()`, `children` | `Element` nodes only | Live |
| `NodeList` | `querySelectorAll()` | Matching elements | Static snapshot |
| `NodeList` | `childNodes` | Elements, text, comments, and other child nodes | Live |

~~~html
<p id="p1"><em>hello</em> world <b>bold</b><!-- comment --></p>
~~~

~~~javascript
const paragraph = document.querySelector("#p1");
const elements = paragraph.children;
const childNodes = paragraph.childNodes;
const snapshot = paragraph.querySelectorAll("*");
paragraph.append(document.createElement("i"));

elements.length;   // 3 elements: em, b, i
childNodes.length; // 5 nodes: em, text, b, comment, i
snapshot.length;   // still 2 members: em, b
~~~

A static list fixes which nodes are members. It does not freeze the node objects or their properties. Whitespace and comments can appear in `childNodes`; `tagName` belongs to elements, while all nodes have a `nodeName`.

Removing items from a live collection while incrementing the index shifts later entries underneath the loop. Iterate backward or take an explicit snapshot:

~~~javascript
for (const element of Array.from(container.getElementsByClassName("item"))) {
  element.remove();
}
~~~

Use `querySelectorAll()` when a static result is simpler to reason about. Use a live collection only when reflecting subsequent matching-tree changes is useful; “live” specifies observable data, not how often an engine recomputes it.

**See also:** [How do DOM events propagate?](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F) discusses event targets in a changing DOM.

**Specification:** [WHATWG DOM: `NodeList` and `HTMLCollection`](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection), checked 2026-11-05.
## 54. How can a JavaScript event bus handle reentrancy? / JavaScript 事件总线如何处理重入？

An event bus keeps listeners by event name and emits to a snapshot so that listener additions or removals during dispatch affect the next emission. A one-time wrapper should mark itself fired and unregister before calling user code; this keeps recursive emits and reentrant snapshots from invoking it twice. Observer and publish-subscribe are different coupling patterns: an observer subject knows its listeners, while a bus mediates between publishers and subscribers. / 事件总线按事件名保存监听器，触发时遍历快照，因此分发期间新增或删除监听器影响下一次触发。一次性包装器应先标记已触发并注销，再调用用户代码；这能避免递归触发和重入快照造成重复调用。观察者与发布订阅的耦合方式不同：观察者主体直接知道监听者，事件总线则位于发布者和订阅者之间。

~~~javascript
class EventBus {
  events = new Map();

  on(event, listener) {
    if (!this.events.has(event)) this.events.set(event, new Set());
    this.events.get(event).add(listener);
  }

  once(event, listener) {
    let fired = false;
    const wrapper = (...args) => {
      if (fired) return;
      fired = true;
      this.off(event, wrapper); // unregister before user code can recurse
      listener(...args);
    };
    this.on(event, wrapper);
  }

  emit(event, ...args) {
    // Mutations during dispatch affect the next emission.
    for (const listener of [...(this.events.get(event) ?? [])]) listener(...args);
  }

  off(event, listener) {
    const listeners = this.events.get(event);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(event);
  }
}
~~~

A reentrant case explains why both the snapshot and the `fired` guard matter:

~~~javascript
const bus = new EventBus();
let firstCalls = 0;
let laterCalls = 0;
bus.once("x", () => { firstCalls += 1; bus.emit("x"); });
bus.once("x", () => { laterCalls += 1; });
bus.emit("x");
console.assert(firstCalls === 1 && laterCalls === 1);
~~~

The outer emission still has its original snapshot after the nested emission removes the later one-time listener. Its wrapper remains present in the outer snapshot, but the `fired` guard makes the second entry a no-op. This small implementation propagates a thrown listener error and documents snapshot mutation; production emitters should define their own error, removal, and async-listener policies.

Use **Observer** when there is a natural subject that owns its subscribers, such as a DOM node or data model. Use **publish-subscribe** when a broker should decouple modules, accepting the indirect path's debugging cost.

**See also:** [How do DOM events propagate?](#4.%20DOM%20%E4%BA%8B%E4%BB%B6%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E4%BA%8B%E4%BB%B6%E5%A7%94%E6%89%98%EF%BC%9F) covers platform event dispatch, which has different phases and cancellation rules.

**Terminology note:** this is an application-level pattern, not the browser DOM event system.
## 55. Where should browser state live: Web Storage or cookies? / 浏览器状态应放在哪里：Web Storage 还是 Cookie？

Use Web Storage when page JavaScript explicitly reads same-origin client state; use cookies when a matching request should carry a small value to a server, such as a session identifier. The choice depends on lifetime, request behavior, size, browser policy, and threat model. Web Storage is synchronous and has no multi-key transaction; cookies are sent according to domain, path, secure-transport, SameSite, and credentials rules. / 页面脚本显式读取同源客户端状态时可选 Web Storage；需要随符合条件的请求发送小型数据（例如会话标识）时可选 Cookie。应根据生命周期、请求行为、容量、浏览器策略和威胁模型选择。Web Storage 为同步接口且没有多键事务；Cookie 是否发送取决于域、路径、安全传输、SameSite 与凭证规则。

| Feature | `localStorage` | `sessionStorage` | Cookies |
|---|---|---|---|
| Scope | Origin storage area; privacy policy may partition or restrict embedded contexts | Origin plus top-level browsing context | Domain/path and cookie policy |
| Lifetime | Persists until removed or evicted; no per-entry expiry API | Usually the top-level context's session; restoration is user-agent dependent | Session or `Expires`/`Max-Age` |
| Request behavior | Not attached automatically | Not attached automatically | Matching cookies may be attached subject to policy and request credentials |
| JavaScript access | Readable by page scripts | Readable by page scripts | Readable through `document.cookie` unless `HttpOnly` |
| Typical fit | Preferences or small client state | Temporary per-tab or wizard state | Server-managed sessions when designed for cookie authentication |

`localStorage` and `sessionStorage` expose synchronous string key/value operations. `localStorage` usually persists until cleared or evicted; it has no per-entry expiry API. `sessionStorage` survives reloads and same-tab navigation and is cleared when that top-level browsing context's session ends, though session restoration is user-agent dependent. A newly opened tab normally has a separate area; an auxiliary context opened by a page may begin with a copy of its opener's session storage, after which the two diverge. The Storage Standard recommends 5 MiB for each endpoint, but this is not a guarantee of usable space: browser mode, policy, and storage pressure matter. For larger structured data or atomic updates, use IndexedDB and handle quota/access errors. `navigator.storage.estimate()` reports approximate usage and quota; best-effort data may be evicted.

The storage key is based on origin, while privacy behavior can further partition or gate embedded third-party storage. Do not assume an embedded page shares the same storage view it receives as a top-level page. Web Storage has no cross-tab lock or multi-key transaction: a read-modify-write can race, and another document's `storage` event is a notification after a write, not an atomicity mechanism. Use IndexedDB transactions or explicit coordination when updates must be atomic; see [How do browser contexts communicate?](#56.%20How%20do%20browser%20contexts%20communicate?%20/%20%E6%B5%8F%E8%A7%88%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B9%8B%E9%97%B4%E5%A6%82%E4%BD%95%E9%80%9A%E4%BF%A1%EF%BC%9F).

Any script running in the page can read Web Storage, so XSS can expose stored bearer tokens. `HttpOnly` keeps a cookie value out of page JavaScript; cookies still introduce CSRF and cross-site policy concerns. `SameSite` can reduce some CSRF exposure but is not a complete defense, and `SameSite=None` requires `Secure` under current cookie rules. Choose a complete session design rather than treating either storage type as a security fix.

**See also:** [Web Security and Authentication / Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) covers XSS, CSRF, and cookie flags; [How does a native app expose capabilities to WebView JavaScript?](#57.%20How%20does%20a%20native%20app%20expose%20capabilities%20to%20WebView%20JavaScript?%20/%20%E5%8E%9F%E7%94%9F%E5%BA%94%E7%94%A8%E5%A6%82%E4%BD%95%E5%90%91%20WebView%20JavaScript%20%E6%9A%B4%E9%9C%B2%E8%83%BD%E5%8A%9B%EF%BC%9F) covers privileged hybrid-app interfaces.

**Standards / 规范：** [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html); [WHATWG Storage Standard](https://storage.spec.whatwg.org/); [IETF HTTP cookie draft](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/); [MDN storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), checked 2026-11-05.
## 56. How do browser contexts communicate? / 浏览上下文之间如何通信？

For same-origin tabs or frames that share an eligible storage partition, use `BroadcastChannel` for ephemeral messages, or `localStorage` plus the `storage` event when persisted state is useful. For windows across origins, use `postMessage` with a specific target origin, then validate the sender window, sender origin, and payload. Use a WebSocket when communication must go through a server. Browser privacy partitioning, frame lifecycle, and trust boundaries affect which contexts can communicate. / 对共享适用存储分区的同源标签页或 frame，临时消息可用 `BroadcastChannel`；需要同时保留状态时可用 `localStorage` 与 `storage` 事件。跨源窗口使用 `postMessage` 并指定目标源，接收端还要校验来源窗口、来源 origin 和消息格式。需要服务器参与时使用 WebSocket。浏览器隐私分区、frame 生命周期和信任边界都会影响通信范围。

| Need | Mechanism | Main constraint |
|---|---|---|
| Ephemeral same-origin messages | `BroadcastChannel` | Eligible contexts must share the relevant storage key; close the channel when its owner ends |
| Persisted state plus notification | `localStorage` and `storage` | The writer does not receive its own event; this is not a transaction or lock |
| Shared in-memory coordinator | `SharedWorker` | State is not durable; feature-detect and clean up disconnected ports |
| Cross-origin window/frame messages | `postMessage` | Pin `targetOrigin`; validate `event.origin`, `event.source`, and data |
| Server-mediated updates | WebSocket or another authenticated connection | Authenticate and authorize on the server; validate the handshake origin |

### Same-origin contexts / 同源上下文

A storage event is queued for other documents sharing that storage area; the document that called `setItem` does not receive its own event. Browser storage partitioning can affect which embedded contexts share an area.

~~~javascript
// Tab A listens.
window.addEventListener("storage", (event) => {
  if (event.key === "message") console.log("Received:", event.newValue);
});

// Tab B writes; Tab B does not receive the event.
localStorage.setItem("message", JSON.stringify({ text: "hello", ts: Date.now() }));
~~~

`BroadcastChannel` is purpose-built for structured-clone messages among eligible contexts and does not persist them.

~~~javascript
const channel = new BroadcastChannel("app_channel");
channel.onmessage = (event) => console.log("Received:", event.data);
channel.postMessage({ type: "update", payload: { id: 1 } });
// When this owner is finished:
channel.close();
~~~

A `SharedWorker` can coordinate connected contexts through ports. Its state lasts only as long as the worker, and a collection of ports needs a policy for removing stale entries. Use a disconnect message when a page can cooperate, then remove and close the worker's port. / SharedWorker 可以通过端口协调多个页面。状态随 worker 生命周期结束。页面能主动退出时，先发断开消息，worker 再移除并关闭对应端口。

~~~javascript
// worker.js
const ports = new Set();
self.onconnect = (event) => {
  const port = event.ports[0];
  ports.add(port);
  function dropPort() {
    ports.delete(port);
    port.close();
  }
  port.onmessage = (message) => {
    if (message.data?.type === "disconnect") {
      dropPort();
      return;
    }
    ports.forEach((other) => {
      if (other !== port) other.postMessage(message.data);
    });
  };
  port.onmessageerror = dropPort; // This example closes a port after a decode failure.
};
~~~

~~~javascript
// Page
function connect() {
  const connection = new SharedWorker("./worker.js").port;
  connection.onmessage = (event) => console.log("Received:", event.data);
  return connection;
}

let port = connect();
window.addEventListener("pagehide", () => {
  port.postMessage({ type: "disconnect" });
  port.close();
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) port = connect();
});
~~~

`pagehide` is best effort. For abrupt tab exits, expire connections after a bounded period without a reply, and let a resumed client register again. The HTML standard defines `close()` and the `messageerror` event for a deserialization failure. It provides no portable peer-close notification for this cleanup. [HTML Standard on MessagePort and broadcast cleanup](https://html.spec.whatwg.org/multipage/web-messaging.html#broadcasting-to-many-ports)

### Cross-origin windows / 跨源窗口

The sender chooses a precise target origin; the receiver checks both origin and the expected window before interpreting the structured-clone payload.

~~~javascript
const iframe = document.getElementById("myIframe");

// Parent → iframe
iframe.contentWindow.postMessage({ action: "update" }, "https://child-origin.example");

// Iframe → parent
window.parent.postMessage({ status: "ready" }, "https://parent-origin.example");

// Receiver inside the iframe. On the parent, compare source with iframe.contentWindow.
const expectedOrigin = "https://parent-origin.example";
const expectedWindow = window.parent;
window.addEventListener("message", (event) => {
  if (event.origin !== expectedOrigin || event.source !== expectedWindow) return;
  if (!event.data || typeof event.data !== "object" ||
      typeof event.data.action !== "string") return;
  handleAction(event.data.action);
});
~~~

Avoid `"*"` for confidential messages: a target window may navigate before delivery. An origin check alone is not enough; a trusted page can be compromised, so validate the message schema and allowed operations. The payload is structured-cloned, not a shared object reference.

A WebSocket is for a server-mediated, persistent bidirectional channel, not a default workaround for two tabs with different origins. The WebSocket protocol is not CORS; validate the handshake's `Origin` and authenticate and authorize each connection on the server. See [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md).

**See also:** [Where should browser state live: Web Storage or cookies?](#55.%20Where%20should%20browser%20state%20live:%20Web%20Storage%20or%20cookies?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E7%8A%B6%E6%80%81%E5%BA%94%E6%94%BE%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9AWeb%20Storage%20%E8%BF%98%E6%98%AF%20Cookie%EF%BC%9F) covers storage lifetime and races.

**Standards / 规范：** [WHATWG HTML: cross-document messaging and BroadcastChannel](https://html.spec.whatwg.org/multipage/web-messaging.html); [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html); [WHATWG WebSockets](https://websockets.spec.whatwg.org/); checked 2026-11-05.
## 57. How does a native app expose capabilities to WebView JavaScript? / 原生应用如何向 WebView JavaScript 暴露能力？

A JavaScript bridge is a host-app interface that lets code in a WebView request selected native operations; it is platform-specific, not a browser standard. Common designs include a native object injected into JavaScript, a message handler with an explicit reply path, or a legacy custom-URL interception scheme. Because bridge calls cross from page code into privileged host capabilities, expose only narrow operations to trusted content and validate every operation and argument on the native side. / JavaScript Bridge 是宿主应用提供给 WebView 页面代码的接口，让页面请求指定原生操作；它因平台而异，并非浏览器标准。常见设计包括注入 JavaScript 的原生对象、带显式回复路径的消息处理器，或较旧的自定义 URL 拦截方案。Bridge 会把页面代码连接到有权限的宿主能力，因此只向可信内容开放有限操作，并由原生端验证每个操作和参数。

### Platform APIs / 平台 API

Android's `addJavascriptInterface` exposes an annotated native object as a JavaScript interface. Android warns that it can grant JavaScript control over the host app; the object can be exposed to all frames, so do not expose it to untrusted content. Apple's `WKScriptMessageHandler` gives JavaScript a named message handler; the native delegate receives a message object with body and frame information, and newer reply handlers can return a response. These platform APIs have different lifecycles, threading and frame rules, so do not treat one sample as portable across WebViews.

### An illustrative JavaScript contract / JavaScript 接口示例

The following is a page-side sketch only. `NativeBridge` is supplied by the app and is not a standard web API.

~~~javascript
// The host app injects or registers this interface for trusted content.
window.NativeBridge.requestLocation((location) => {
  renderLocation(location);
});
~~~

A real contract should define operation names, argument and reply schemas, error behavior, cancellation, and whether calls are synchronous or asynchronous. Validate origin/frame identity and authorization on the native side; page-side checks alone cannot protect native capabilities. If untrusted pages can load, do not let them navigate inside a WebView that exposes a privileged bridge.

### Legacy custom-scheme pattern / 旧式自定义协议模式

An older design appends a hidden iframe with a URL such as `myapp://api/location?data=...` and lets the native host intercept the navigation. The URL carries encoded arguments but may hit platform length limits and has no direct reply; callbacks require a separate request identifier and return channel. Treat this as an implementation-specific legacy pattern, not a general WebView recommendation.

~~~javascript
const bridge = {
  invoke(path, data) {
    const iframe = document.createElement("iframe");
    iframe.hidden = true;
    iframe.src = "myapp://" + path + "?data=" +
      encodeURIComponent(JSON.stringify(data));
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 100);
  },
  getLocation() {
    this.invoke("api/location", {});
  }
};
~~~

This sketch only shows the request side. A complete bridge needs a response channel, request identifiers, timeouts, error handling, and a native authorization check.

For a normal web page, use standard browser APIs such as `navigator.geolocation` when they fit; the browser mediates permission and device access.

**Sources checked 2026-11-05:** [Android Developers: WebView JavaScript interfaces and security warning](https://developer.android.com/develop/ui/views/layout/webapps/webview); [Android Developers: JS bridge guidance](https://developer.android.com/develop/ui/views/layout/webapps/native-api-access-jsbridge); [Apple Developer Documentation: WKScriptMessage](https://developer.apple.com/documentation/webkit/wkscriptmessage); [Apple Developer Documentation: message handler with reply](https://developer.apple.com/documentation/webkit/wkusercontentcontroller/addscriptmessagehandlerwithreply%28_%3Acontentworld%3Aname%3A%29).
## 58. How should a UI render a streamed answer without mistaking partial output for completion? / 界面如何呈现流式回答而不把部分内容误判为完成？

**Core answer / 核心回答：** Treat a streamed answer as partial until the client receives and validates an explicit terminal event for the same run. Keep useful deltas visible, label them as incomplete, and bound decoding, buffering, rendering, and recovery. If the event connection ends without a terminal event, preserve the text but treat the result as unknown and query the run's authoritative status. Stopping the local reader cancels this view; stopping server work requires a separate cancellation request and confirmation. / 收到并验证同一次运行的明确终态事件之前，都应把流式回答视为部分结果。保留有用的增量文本并标记为未完成，同时限制解码、缓冲、渲染和恢复的资源。如果事件连接在终态事件前结束，应保留文本、把结果视为未知并查询运行的权威状态。停止本地读取只会取消当前视图；停止服务端工作需要单独发出取消请求并确认。

**Key terms / 关键术语：** partial output / 部分输出；terminal event / 终态事件；run state / 运行状态；resume cursor / 恢复游标；backpressure / 背压；local cancellation / 本地取消。

### Which state can the interface safely show? / 界面可以准确显示哪些状态？

The browser view tracks what this page has received and can render. The [durable run record / 持久运行记录](../../ai-engineering/systems/ai-application-architecture.md) owns the server's queued, running, completed, failed, and canceled states. A text delta moves the view into `streaming`. A valid `complete` event for the expected `runId` confirms success in this example, while a terminal `error` frame confirms that the server reported failure. When a disconnect, timeout, or framing error interrupts the read, preserve partial text and query the run record. The same [unknown outcome / 结果未知](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) matters when deciding whether to retry a regular request.

| View state | What the user can infer |
|---|---|
| `idle` | No stream is being viewed. |
| `connecting` | Submission, event connection, or an allowed resume request is in progress. |
| `streaming` | At least one valid delta arrived. The visible answer is partial. |
| `completed` | A valid `complete` frame for this `runId` arrived. |
| `failed` | The view cannot continue normally. A valid error frame reports server failure; a transport, framing, timeout, or recovery failure leaves the run's final server state unknown until queried. Keep useful text labeled as incomplete. |
| `canceled` | The local reader or view was stopped. The server may still be queued or running unless its status confirms cancellation. |

The sequence below shows the main success and recovery paths. Status queries answer what happened to the run; they do not make a broken event stream complete. A cancellation request can remain pending until the server reports a terminal status.

~~~mermaid
sequenceDiagram
    actor User
    participant UI as Browser view
    participant Events as Event endpoint
    participant Runs as Run status API

    User->>UI: Submit prompt
    UI->>Runs: POST /api/runs (idempotency key)
    Runs-->>UI: 202 + stable runId
    UI->>Events: GET /api/runs/{runId}/events?after=seq
    loop Valid progress
        Events-->>UI: delta(seq, text)
        UI-->>User: Append text, label as partial
    end
    alt Valid completion event
        Events-->>UI: complete(seq, runId)
        UI-->>User: Mark answer complete
    else Valid error event
        Events-->>UI: error(seq, runId)
        UI-->>User: Keep partial text and show the failure
    else Disconnect, EOF, timeout, or invalid stream
        Events--xUI: No valid terminal event
        UI->>Runs: GET /api/runs/{runId}
        Runs-->>UI: Authoritative status
        UI-->>User: Keep partial text and show known or unknown run state
    else User stops this view
        User->>UI: Stop
        UI->>Events: Abort local fetch and reader
        UI-->>User: Mark this view stopped
        opt Also ask the server to stop work
            UI->>Runs: POST /api/runs/{runId}/cancel
            Runs-->>UI: Cancellation accepted or current status
            UI->>Runs: Query within the recovery budget
        end
    end
~~~

### A small application protocol / 简洁的应用协议

This example uses Fetch to read newline-delimited JSON records. It is a synthetic application contract, not an additional transport standard and not a redefinition of Server-Sent Events (SSE). `POST /api/runs` accepts an `Idempotency-Key` and returns `202` with a stable `runId`; the client then reads `GET /api/runs/{runId}/events?after={lastSequence}`. Each event is one UTF-8 JSON object followed by LF (CRLF is also accepted), and carries a monotonically increasing `seq`. A `delta` adds partial text; `complete` and `error` are terminal. On reconnect the server may replay older sequence numbers, which the client drops, while a gap fails the stream. `GET /api/runs/{runId}` remains authoritative for run status.

~~~text
POST /api/runs
Idempotency-Key: submit-7f2a
{"prompt":"Summarize the public release notes"}

202 Accepted
{"runId":"run-7f2a","status":"queued"}

GET /api/runs/run-7f2a/events?after=0
Content-Type: application/x-ndjson

{"type":"delta","seq":1,"text":"The release adds "}
{"type":"delta","seq":2,"text":"a search filter."}
{"type":"complete","seq":3,"runId":"run-7f2a"}
~~~

The complete frame is the success boundary for this example. EOF before a terminal frame is an incomplete response, even when it follows valid text. A terminal error preserves earlier deltas as partial output. A timeout or disconnect may be retried only within the contract: for example, at most two event reconnections during a short deadline, using the same runId and last accepted seq. Never create a replacement run merely because the event request failed. If the cursor expired or the run is still active after the retry budget, query current status and explain that the visible text is partial.

The HTTP body yields byte chunks. A read can split inside UTF-8 characters, inside one JSON record, or between records; one read can also contain several records. TextDecoder with stream mode carries an incomplete multibyte sequence into the next decode call. The parser below independently buffers until LF and therefore does not mistake a transport chunk for a record. It caps each frame and its incomplete line buffer at 8,192 UTF-16 code units (the units counted by JavaScript `String.length`), not 8 KiB of encoded bytes, and total displayed text at 64 Ki UTF-16 code units. These are example product limits, not browser or protocol defaults.

### Executable protocol model / 可执行协议模型

The following standalone snippet uses Node's Web Streams and Response APIs to exercise the parser and interaction states. It is a protocol model, not a test in a real browser and not proof of any production server behavior. The parser awaits onText; a browser can use that point to batch updates on requestAnimationFrame and pause reading while a small render queue drains.

~~~javascript
import assert from "node:assert/strict";

const MAX_FRAME_CHARS = 8 * 1024;
const MAX_OUTPUT_CHARS = 64 * 1024;
const DECODE_SLICE_BYTES = 4 * 1024;

function readWithSignal(reader, signal) {
  if (!signal) return reader.read();
  const abortReason = () => signal.reason ?? new DOMException("Aborted", "AbortError");
  if (signal.aborted) return Promise.reject(abortReason());

  return new Promise((resolve, reject) => {
    const onAbort = () => reject(abortReason());
    signal.addEventListener("abort", onAbort, { once: true });
    reader.read().then(resolve, reject).finally(() => {
      signal.removeEventListener("abort", onAbort);
    });
  });
}

async function consumeRun(response, {
  runId,
  signal,
  afterSequence = 0,
  currentOutputChars = 0,
  onState = () => {},
  onText = async () => {},
} = {}) {
  let state = "idle";
  let sequence = afterSequence;
  let outputChars = currentOutputChars;
  let carry = "";
  let terminal = false;
  let errorCode;
  let detail;
  let reader;
  const decoder = new TextDecoder("utf-8", { fatal: true });

  const transition = next => {
    const allowed = {
      idle: ["connecting", "canceled"],
      connecting: ["streaming", "completed", "failed", "canceled"],
      streaming: ["connecting", "completed", "failed", "canceled"],
    };
    if (state === next) return;
    if (!allowed[state]?.includes(next)) {
      throw new Error("Invalid view-state transition: " + state + " -> " + next);
    }
    state = next;
    onState(state);
  };

  const result = () => ({ state, sequence, outputChars, errorCode, detail });

  async function acceptLine(line) {
    signal?.throwIfAborted();
    if (terminal) throw new Error("Frame received after a terminal frame");
    if (!line) throw new Error("Empty frame");
    if (line.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");

    let event;
    try {
      event = JSON.parse(line);
    } catch {
      throw new Error("Malformed JSON frame");
    }

    if (!event || Array.isArray(event) || typeof event !== "object") {
      throw new Error("Frame must be a JSON object");
    }
    if (!Number.isSafeInteger(event.seq) || event.seq < 1) {
      throw new Error("Frame has an invalid sequence number");
    }
    if (event.seq <= sequence) return; // replayed event already applied
    if (event.seq !== sequence + 1) throw new Error("Event sequence gap");
    if (typeof event.type !== "string") throw new Error("Frame has no event type");

    if (event.type === "delta") {
      if (typeof event.text !== "string") throw new Error("Delta text must be a string");
      if (outputChars + event.text.length > MAX_OUTPUT_CHARS) {
        throw new Error("Output exceeds the display limit");
      }
      sequence = event.seq;
      outputChars += event.text.length;
      if (state === "connecting") transition("streaming");
      await onText(event.text);
      signal?.throwIfAborted();
      return;
    }

    if (event.type === "complete") {
      if (event.runId !== runId) throw new Error("Terminal frame has the wrong runId");
      sequence = event.seq;
      terminal = true;
      transition("completed");
      return;
    }

    if (event.type === "error") {
      if (typeof event.code !== "string" || !event.code) {
        throw new Error("Error frame has no error code");
      }
      sequence = event.seq;
      errorCode = event.code;
      terminal = true;
      transition("failed");
      return;
    }

    throw new Error("Unknown event type");
  }

  async function feedText(text) {
    carry += text;
    let newline;
    while ((newline = carry.indexOf("\n")) !== -1) {
      let line = carry.slice(0, newline);
      carry = carry.slice(newline + 1);
      if (line.endsWith("\r")) line = line.slice(0, -1);
      await acceptLine(line);
      if (terminal) return;
    }
    if (carry.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
  }

  transition("connecting");
  try {
    if (!response.body) throw new Error("Response has no body");
    reader = response.body.getReader();
    if (!response.ok) throw new Error("HTTP " + response.status);
    if (!response.headers.get("content-type")?.toLowerCase().includes("application/x-ndjson")) {
      throw new Error("Unexpected response content type");
    }

    while (true) {
      const { done, value } = await readWithSignal(reader, signal);
      if (done) {
        await feedText(decoder.decode());
        if (terminal) return result();
        if (carry.length) throw new Error("EOF inside an unterminated frame");
        throw new Error("EOF before a terminal frame");
      }

      for (let offset = 0; offset < value.byteLength; offset += DECODE_SLICE_BYTES) {
        const part = value.subarray(offset, offset + DECODE_SLICE_BYTES);
        await feedText(decoder.decode(part, { stream: true }));
        if (terminal) return result();
      }
    }
  } catch (error) {
    detail = error instanceof Error ? error.message : String(error);
    if (signal?.aborted && signal.reason?.name === "TimeoutError") {
      transition("failed");
    } else if (signal?.aborted) {
      transition("canceled");
    } else {
      transition("failed");
    }
    return result();
  } finally {
    if (reader) {
      try {
        await reader.cancel();
      } catch {
        // Preserve the parse, read, timeout, or abort result.
      }
      reader.releaseLock();
    }
  }
}

const encoder = new TextEncoder();
const asBytes = text => encoder.encode(text);

function responseFrom(chunks, { open = false, status = 200 } = {}) {
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      if (!open) controller.close();
    },
  });
  return new Response(body, {
    status,
    headers: { "content-type": "application/x-ndjson; charset=utf-8" },
  });
}

function responseDisconnectAfter(chunk) {
  let sent = false;
  const body = new ReadableStream({
    pull(controller) {
      if (!sent) {
        sent = true;
        controller.enqueue(chunk);
      } else {
        controller.error(new Error("Connection dropped"));
      }
    },
  }, { highWaterMark: 0 });
  return new Response(body, {
    headers: { "content-type": "application/x-ndjson; charset=utf-8" },
  });
}

async function check(name, response, expectedState, expectedText = "", options = {}) {
  const states = [];
  let text = "";
  const result = await consumeRun(response, {
    runId: "run-7",
    ...options,
    onState: state => states.push(state),
    onText: chunk => { text += chunk; },
  });
  assert.equal(result.state, expectedState, name);
  assert.equal(text, expectedText, name + " partial text");
  return { result, states };
}

// Split one multibyte character and one record across reads; the final read
// also contains a coalesced complete record.
const multibyte = asBytes("好");
const normal = await check(
  "split UTF-8 and coalesced frames",
  responseFrom([
    asBytes('{"type":"delta","seq":1,"text":"你'),
    multibyte.slice(0, 1),
    multibyte.slice(1),
    asBytes('"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
  ]),
  "completed",
  "你好",
);
assert.deepEqual(normal.states, ["connecting", "streaming", "completed"]);
console.log("PASS normal, multibyte split, frame split, and coalesced frames");

const serverError = await check(
  "server error frame",
  responseFrom([asBytes('{"type":"error","seq":1,"code":"MODEL_UNAVAILABLE"}\n')]),
  "failed",
);
assert.equal(serverError.result.errorCode, "MODEL_UNAVAILABLE");
console.log("PASS terminal server-error frame");

const malformed = await check(
  "malformed JSON",
  responseFrom([asBytes("{not-"), asBytes("json}\n")]),
  "failed",
);
assert.match(malformed.result.detail, /Malformed JSON/);
console.log("PASS malformed frame split across reads");

const prematureEof = await check(
  "premature EOF",
  responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')]),
  "failed",
  "partial",
);
assert.match(prematureEof.result.detail, /EOF before a terminal frame/);
console.log("PASS EOF preserves partial text but does not complete");

const disconnected = await check(
  "abrupt disconnect",
  responseDisconnectAfter(asBytes('{"type":"delta","seq":1,"text":"partial"}\n')),
  "failed",
  "partial",
);
assert.match(disconnected.result.detail, /Connection dropped/);
console.log("PASS abrupt disconnect preserves partial text but does not complete");

const timeoutController = new AbortController();
const timeoutTimer = setTimeout(() => {
  timeoutController.abort(new DOMException("Deadline exceeded", "TimeoutError"));
}, 5);
const timeout = await check(
  "timeout",
  responseFrom([], { open: true }),
  "failed",
  "",
  { signal: timeoutController.signal },
);
clearTimeout(timeoutTimer);
assert.match(timeout.result.detail, /Deadline exceeded/);
console.log("PASS timeout remains a failure, not completion");

const stopController = new AbortController();
const stopTimer = setTimeout(() => {
  stopController.abort(new DOMException("Stopped by user", "AbortError"));
}, 5);
const stopped = await check(
  "explicit abort after partial text",
  responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')], { open: true }),
  "canceled",
  "partial",
  { signal: stopController.signal },
);
clearTimeout(stopTimer);
assert.match(stopped.result.detail, /Stopped by user/);
console.log("PASS explicit abort keeps partial text and marks only the local view canceled");

const bufferedRaceController = new AbortController();
const bufferedRaceStates = [];
let bufferedRaceText = "";
const bufferedRace = await consumeRun(responseFrom([
  asBytes('{"type":"delta","seq":1,"text":"partial"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
]), {
  runId: "run-7",
  signal: bufferedRaceController.signal,
  onState: state => bufferedRaceStates.push(state),
  onText: async chunk => {
    bufferedRaceText += chunk;
    await Promise.resolve();
    bufferedRaceController.abort(new DOMException("Stopped while rendering", "AbortError"));
  },
});
assert.equal(bufferedRace.state, "canceled");
assert.equal(bufferedRace.sequence, 1);
assert.equal(bufferedRace.outputChars, "partial".length);
assert.equal(bufferedRaceText, "partial");
assert.deepEqual(bufferedRaceStates, ["connecting", "streaming", "canceled"]);
assert.match(bufferedRace.detail, /Stopped while rendering/);
console.log("PASS abort during awaited text handling prevents a buffered complete frame");
~~~

**Executable proof / 可执行验证：** The standalone model above ran with Node.js v26.11.1 on 2026-11-05. All eight assertion-backed case groups passed: split UTF-8 and frame boundaries with coalesced frames, terminal server error, malformed JSON, premature EOF, abrupt disconnect, timeout, explicit local abort, and abort during awaited rendering. This exercises the synthetic stream model; it does not test a browser or production server. / 上述独立模型于 2026-11-05 使用 Node.js v26.11.1 运行，所有八组断言场景均通过：拆分 UTF-8、跨帧读取与合并帧的正常路径、服务端终态错误、格式错误的 JSON、过早 EOF、连接中断、超时、显式本地中止以及渲染等待期间中止。此验证针对合成流模型，不覆盖真实浏览器或生产服务端。

For a browser, create one AbortController for the active event request and pass its signal to Fetch. The stop button and route cleanup should abort that request and release its reader. If the product also wants to stop server work, send POST /api/runs/{runId}/cancel and keep showing a pending cancellation until GET /api/runs/{runId} reports a terminal state. AbortController.abort() and reader.cancel() affect the local fetch/body consumption; neither proves the worker stopped.

Keep render work bounded as well as network buffering. Accumulate adjacent delta text and update the output once per animation frame rather than rerendering the component for every token. Cap the pending render string; because the parser awaits onText, it can pause its next read while the UI drains that small queue. The sample also caps the full visible answer. A larger product can persist output by run and render a bounded window instead of keeping an ever-growing DOM.

Leave partial output visible when it remains useful, but label it as incomplete and avoid actions that require a finished result. Expose a concise state message in a dedicated status region, for example a native element with role=status and aria-live=polite. Announce connection, completion, failure, or stop transitions and perhaps occasional long-running progress; do not announce every token. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](#16.%20How%20does%20the%20CSS%20cascade%20decide%20which%20declaration%20applies?%20/%20CSS%20%E7%BA%A7%E8%81%94%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E6%9C%80%E7%BB%88%E7%94%9F%E6%95%88%E7%9A%84%E5%A3%B0%E6%98%8E%EF%BC%9F) for native controls and status semantics.

**Representative answer / 代表性回答：** I treat streamed output as framed bytes that may arrive in arbitrary chunks. The client incrementally decodes UTF-8, validates sequence numbers, keeps partial text, and displays completion only after a valid terminal event. It batches rendering, bounds memory and retries, and tears down the local reader on stop or route change. A client abort does not prove the server run stopped, so I query the run record or request cancellation separately. / 我会把流式输出视为可能以任意分块到达的带帧字节。客户端增量解码 UTF-8、校验序号、保留部分文本，并且只在收到有效终态事件后显示完成。界面合并渲染、限制内存和重试次数，并在用户停止或路由卸载时清理本地读取器。客户端中止不能证明服务端运行已停止，因此还要查询运行记录或单独请求取消。

### Related notes / 相关笔记

- [Choosing a transport for real-time updates / 怎样选择实时传输](../../engineering-foundations/networking/real-time-web-updates.md) explains SSE framing, EventSource limits, and Fetch stream boundaries.
- [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) explains deadlines, cancellation, retry safety, and unknown outcomes.
- [AI Application Architecture / AI应用架构](../../ai-engineering/systems/ai-application-architecture.md) owns run identity, durable state, checkpoints, side effects, and server cancellation.

**Sources checked 2026-10-15 / 来源核对日期：** The [WHATWG Streams Standard](https://streams.spec.whatwg.org/) defines readable-stream readers and local consumer cancellation; the [DOM Standard's AbortController](https://dom.spec.whatwg.org/#interface-abortcontroller) defines signaling abort to an API that accepts an AbortSignal, and [AbortSignal.throwIfAborted()](https://dom.spec.whatwg.org/#dom-abortsignal-throwifaborted) provides checkpoints between asynchronous operations; the [WHATWG Encoding Standard](https://encoding.spec.whatwg.org/) defines streaming UTF-8 decode behavior. The [WHATWG Server-sent Events section](https://html.spec.whatwg.org/multipage/server-sent-events.html) defines EventSource reconnection and event IDs; this note's parser instead exercises its explicitly synthetic newline-delimited JSON application contract. Browser behavior was not tested here.
## 59. How can an analytics client reduce work and try to send events during navigation? / 分析客户端如何降低工作量并尝试在导航时发送事件？

Keep analytics off the application's critical path: collect events in a bounded in-memory queue, send small batches on a threshold or timer, and try one final batch when the document becomes hidden. This reduces per-event work and gives the client a best-effort delivery opportunity. It cannot guarantee server receipt, and pending events can be lost if the page exits. / 不要让分析采集阻塞应用关键路径：先把事件放入有界内存队列，达到阈值或定时发送小批次，并在文档转为隐藏时尝试发送最后一批。这可以减少逐事件开销，并提供尽力发送的机会；它无法保证服务器收到，页面退出时仍可能丢失未发送事件。

### Decide what can enter the queue / 决定哪些事件可以进入队列

Define the purpose and the fields it needs before adding instrumentation. For optional analytics, use the application's collection preference, allowlist event names and screen values, and leave raw input, full URLs, and identifiers out of the event payload. If the user opts out, stop accepting events and discard the pending queue.

### Batch without blocking navigation / 批量发送并保持导航顺畅

The example drops the oldest pending item when the queue is full and sends one bounded batch from the visibility-change handler. Tune the limits to payload size and the loss the application can tolerate.

```javascript
const MAX_PENDING = 200;
const BATCH_SIZE = 50;
const eventNames = new Set(["report_opened", "filter_applied"]);
const screens = new Set(["report_list", "report_detail"]);
const queue = [];
let collectionEnabled = false;
let flushScheduled = false;

function setCollectionEnabled(enabled) {
  collectionEnabled = enabled;
  if (!enabled) queue.length = 0;
}

function report(url, events) {
  const body = new Blob([JSON.stringify(events)], { type: "application/json" });
  if (navigator.sendBeacon && navigator.sendBeacon(url, body)) return;
  void fetch(url, { method: "POST", body, keepalive: true }).catch(() => {});
}

function trackEvent(name, screen) {
  if (!collectionEnabled || !eventNames.has(name) || !screens.has(screen)) return;
  if (queue.length === MAX_PENDING) queue.shift(); // Drop the oldest item to stay bounded.
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
  if (queue.length === 0) return;
  const batch = queue.splice(0, BATCH_SIZE);
  report("/analytics", batch); // Accepted for queuing is not server acknowledgement.
}

setInterval(flushEvents, 10_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushEvents();
});
```

`sendBeacon()` returns whether the browser accepted the payload for queuing. If the browser lacks Beacon or declines this payload, the code attempts a `fetch()` request with `keepalive`. Neither result confirms application-level processing or server acknowledgement. The visibility handler attempts only one batch; if the queue contains more, a later timer or scheduled threshold flush may attempt the rest, but page teardown can still discard them.

Keep the queue bound and choose an explicit overflow policy. Do not make application correctness depend on analytics delivery or block navigation while waiting for an acknowledgement.

**Specifications:** [Beacon](https://w3c.github.io/beacon/) defines the Beacon API and its queueing result; [Fetch Standard, `keepalive`](https://fetch.spec.whatwg.org/#request-keepalive-flag) defines keepalive request behavior.
## 60. 如何为产品选择前端框架？

**案例背景。** 以报表页面为例：浏览器地址是 `/reports?sort=recent#summary`，服务端实际收到 `/reports?sort=recent` 并据此返回 May、April 两行；`#summary` 只供浏览器定位。用户点 **Oldest first** 后，`pushState` 新增 `sort=oldest` 历史项，可见顺序成为 April、May；按浏览器 Back 会恢复 `sort=recent` 和 May、April。完整历史行为见[浏览器导航路径](#%E8%AE%A9%E7%AD%9B%E9%80%89%E7%8A%B6%E6%80%81%E8%B7%9F%E9%9A%8F%E5%9C%B0%E5%9D%80%E6%A0%8F%E4%B8%8E%E5%89%8D%E8%BF%9B%E5%90%8E%E9%80%80)。框架选择要回答的是团队怎样可靠地交付这类更新，以及页面还需要怎样的路由、服务端渲染、无障碍和运维支持。单说“有虚拟 DOM”不能回答这些问题。

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

React 的逐次更新模型见[React如何把一次用户操作变成界面更新？](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)；路由与客户端导航的判断见[React路由如何把 URL 映射到视图？](#61.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F)。

> [!info]- 来源与版本核验（2026-11-06）
> - 本文关于 React 描述、render 与 commit 的边界：React 19.3 当前文档，[Render and Commit](https://react.dev/learn/render-and-commit)、[Versions](https://react.dev/versions)，核验日期 2026-11-06。
> - 框架实现可采用不同渲染机制：React 文档同上；Vue 官方文档，[Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism)，核验日期 2026-11-06。
> - URI 片段只在客户端用于定位，不属于发给服务端的请求：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
## 61. How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？

**Core answer / 核心回答：** React Router matches the current location to a route, while SPA and MPA describe whether navigation updates the current document or requests another one. The choice depends on delivery, interaction, accessibility, hosting, and operations. / React Router 将当前地址匹配到路由；SPA 与 MPA 则描述导航是更新当前文档还是请求另一个文档。选择取决于内容交付、交互、无障碍、托管和运维需求。

### How does React Router work? / React Router如何工作？

**Core answer / 核心回答：** React Router matches the current location to a route and renders the configured UI. The example below uses the React Router v6 declarative API; current releases also offer data and framework modes with additional APIs. A browser-history router needs the host to serve the application entry point for client-side paths. / React Router 将当前地址匹配到路由并渲染对应界面。下面的例子使用 React Router v6 声明式 API；当前版本还提供数据模式和框架模式。浏览器历史路由要求服务器将客户端路径回退到应用入口文件。

~~~jsx
import { BrowserRouter, Routes, Route, useParams } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/posts/:postId" element={<Post />} />
      </Routes>
    </BrowserRouter>
  );
}

function Home() {
  return <h1>Home</h1>;
}

function Post() {
  const { postId } = useParams();
  return <h1>Post {postId}</h1>;
}
~~~

- **BrowserRouter** uses the browser History API and clean paths.
- **HashRouter** stores the route after the URL hash; it can fit hosting where server fallback configuration is unavailable.
- **MemoryRouter** stores location in memory and is useful in tests or non-browser contexts.

Use Link for navigation users can follow and useNavigate for programmatic navigation. Route API and package imports vary by React Router version; follow the version installed by the project.

### What is the difference between an SPA and an MPA? / SPA和MPA有什么区别？

**Core answer / 核心回答：** An MPA navigation requests another document; an SPA typically keeps one document loaded and updates route content in the client. Server rendering and client navigation can be combined, so many current applications use a hybrid model. Choose based on content delivery, interaction, accessibility, and operational needs rather than the label alone. / MPA 导航会请求另一个文档；SPA 通常保留一个文档并在客户端更新路由内容。服务端渲染和客户端导航可以组合，因此许多现代应用采用混合模式。应根据内容交付、交互、无障碍和运维需求选择，而非只看标签。

| Aspect | SPA pattern | MPA pattern |
|---|---|---|
| Navigation | Client router updates the current document | Browser requests another document |
| State | Client state can persist between route changes | State often needs URL, storage, or server persistence |
| Initial delivery | Depends on shell size, rendering, and data strategy | Depends on document and asset delivery |
| SEO and accessibility | Require deliberate rendering and semantic structure | Also require meaningful HTML and semantic structure |

**See also:** [React Basics / React基础](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F) for state-driven rendering; [Next.js / Next.js开发](#62.%20How%20should%20a%20Next.js%20app%20render%20and%20route%20its%20pages?%20/%20Next.js%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%B8%B2%E6%9F%93%E9%A1%B5%E9%9D%A2%E5%B9%B6%E7%BB%84%E7%BB%87%E8%B7%AF%E7%94%B1%EF%BC%9F) for server/client rendering and framework routing.

**Sources checked 2026-10-15:** [React Router v6 Concepts](https://reactrouter.com/docs/en/v6/start/concepts), [React Router: Picking a Mode](https://reactrouter.com/start/modes).
## 62. How should a Next.js app render and route its pages? / Next.js应用应如何渲染页面并组织路由？

**Core answer / 核心回答：** Choose the Pages Router or App Router deliberately, then decide per route which work belongs in a request-time server render, reusable static output, a Client Component, or a smaller streamed region. Name the Next.js version when discussing cache defaults: these behaviors have changed across releases. Server-rendered HTML streaming during page navigation is separate from streaming an operation's incremental answer after the page is open; the latter belongs to [Streaming UX / 流式交互](#58.%20How%20should%20a%20UI%20render%20a%20streamed%20answer%20without%20mistaking%20partial%20output%20for%20completion?%20/%20%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%91%88%E7%8E%B0%E6%B5%81%E5%BC%8F%E5%9B%9E%E7%AD%94%E8%80%8C%E4%B8%8D%E6%8A%8A%E9%83%A8%E5%88%86%E5%86%85%E5%AE%B9%E8%AF%AF%E5%88%A4%E4%B8%BA%E5%AE%8C%E6%88%90%EF%BC%9F). / 先明确使用 Pages Router 还是 App Router，再按路由决定哪些工作适合请求时服务端渲染、可复用静态输出、Client Component 或较小的流式区域。说明缓存默认值时要注明 Next.js 版本，因为不同版本的行为发生过变化。页面导航期间流式传送服务端 HTML，与页面打开后流式呈现某次操作的增量回答，是不同层次；后者见 [Streaming UX / 流式交互](#58.%20How%20should%20a%20UI%20render%20a%20streamed%20answer%20without%20mistaking%20partial%20output%20for%20completion?%20/%20%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%91%88%E7%8E%B0%E6%B5%81%E5%BC%8F%E5%9B%9E%E7%AD%94%E8%80%8C%E4%B8%8D%E6%8A%8A%E9%83%A8%E5%88%86%E5%86%85%E5%AE%B9%E8%AF%AF%E5%88%A4%E4%B8%BA%E5%AE%8C%E6%88%90%EF%BC%9F)。


### What does Next.js add to React? / Next.js为React增加了什么？

**Core answer / 核心回答：** Next.js is a React framework that combines routing, server and client rendering, data access, and deployment integrations. Its Pages Router and App Router have different file conventions and rendering APIs, so name the router and version when describing behavior. / Next.js 是 React 框架，整合路由、服务端与客户端渲染、数据访问和部署集成。Pages Router 与 App Router 的文件约定和渲染 API 不同，说明行为时要注明路由器和版本。

Next.js can produce HTML on the server or ahead of a request, and it can update route content in the browser. These options are not one global switch: choose based on the route's data freshness, user-specific content, runtime, and caching needs.

### Pages Router: SSR, SSG, and ISR / Pages Router：SSR、SSG和ISR

The following APIs belong to the **Pages Router** under the pages directory.

| Strategy | API | When it fits |
|---|---|---|
| Server rendering per request | getServerSideProps | Request-specific data or authorization must be resolved on the server for each request. |
| Static generation | getStaticProps and, for dynamic paths, getStaticPaths | Output can be produced before a request and reused. |
| Incremental Static Regeneration | getStaticProps with revalidate | A generated page can be refreshed after a time window or on demand. |
| Client-side data | Browser fetch or a client data library | Data is user-specific or does not need to be in the initial server-rendered response. |

~~~jsx
// pages/posts/[id].js — Pages Router
export async function getServerSideProps({ params }) {
  const response = await fetch(
    "https://api.example.com/posts/" + params.id
  );

  if (response.status === 404) return { notFound: true };
  if (!response.ok) throw new Error("Post request failed: " + response.status);

  return { props: { post: await response.json() } };
}

export default function PostPage({ post }) {
  return <article><h1>{post.title}</h1></article>;
}
~~~

For ISR, a successful getStaticProps result can return revalidate: 60. This is a minimum interval before a request can trigger regeneration, not a timer that regenerates every minute. After the interval, a request can receive the stale page while regeneration runs; a successful new result replaces the cached version. Dynamic paths also need getStaticPaths and a deliberate fallback policy. In this Pages Router example, fallback: false makes paths omitted from the build-time list return 404; fallback: "blocking" generates an omitted path on its first request before returning HTML.

~~~jsx
// pages/posts/[id].js — Pages Router
export async function getStaticPaths() {
  const response = await fetch("https://api.example.com/posts");
  if (!response.ok) throw new Error("Could not list posts");
  const posts = await response.json();

  return {
    paths: posts.map(post => ({ params: { id: String(post.id) } })),
    fallback: "blocking"
  };
}

export async function getStaticProps({ params }) {
  const response = await fetch("https://api.example.com/posts/" + params.id);
  if (response.status === 404) return { notFound: true };
  if (!response.ok) throw new Error("Post request failed: " + response.status);

  return { props: { post: await response.json() }, revalidate: 60 };
}
~~~

### App Router: Server Components and caching / App Router：Server Components与缓存

Under the app directory, pages and layouts are Server Components by default. They can fetch on the server and pass serializable data to a Client Component. A file marked use client creates a client boundary for Hooks, event handlers, and browser APIs. Client Components may still contribute to initial HTML; use client does not mean the whole route is client-only.

The following example uses the App Router with Cache Components disabled.

~~~tsx
// app/posts/page.tsx — App Router
async function getPosts() {
  const response = await fetch("https://api.example.com/posts", {
    cache: "no-store"
  });
  if (!response.ok) throw new Error("Posts request failed");
  return response.json();
}

export default async function PostsPage() {
  const posts = await getPosts();
  return (
    <ul>
      {posts.map(post => <li key={post.id}>{post.title}</li>)}
    </ul>
  );
}
~~~

With Cache Components disabled, the default server `fetch` mode is `auto no cache`. That mode does not opt a fetch into the persistent Data Cache. A statically prerendered route can still fetch once during `next build` and serve its prerendered output. A route using request-time APIs can fetch per request. Choose deliberately. Use `cache: "no-store"` for data that must be fetched per request, or opt into caching with `force-cache` or a compatible `next.revalidate` policy. In development, the HMR cache can reuse even `no-store` fetches until navigation or a full reload. [Next.js fetch reference, checked 2026-11-06](https://nextjs.org/docs/app/api-reference/functions/fetch#optionscache)

With Cache Components enabled, a component or function can opt into caching with `use cache`. To stream the uncached posts in this example, move the fetch into an async child with a Suspense ancestor. That boundary lets Next.js prerender the surrounding shell while the child waits for request-time data. Check where the result is reused and how it gets invalidated before choosing a cache lifetime. / 区分数据缓存、静态预渲染的页面产物与开发环境的 HMR 缓存。开启 Cache Components 后，把请求时才读取的数据放到 Suspense 边界下。 [Next.js on streaming uncached data](https://nextjs.org/docs/app/getting-started/caching#streaming-uncached-data)

A Client Component can receive data from a Server Component through props, but props crossing the boundary must be serializable. Keep secrets and server-only dependencies on the server.

### How do hydration and streaming fit together? / Hydration 与流式渲染如何衔接？

**Core answer / 核心回答：** Server-rendered HTML can appear before the client JavaScript is ready. Hydration makes that existing markup interactive by matching it to React's initial client render and attaching behavior; the two initial outputs must agree. Effects run only in the browser after a component commits. In the App Router, a `Suspense` boundary can show a useful fallback while a slower child waits, then stream that region into the page. / 服务端 HTML 可以先于客户端 JavaScript 显示。Hydration 将已有标记与 React 客户端的首次渲染匹配并附加交互行为；两端首次输出必须一致。Effect 只在浏览器中、组件提交后运行。App Router 中的 `Suspense` 边界可以先显示有用的占位内容，再把等待中的子区域流式送入页面。

#### Hydration timeline and one mismatch diagnostic

1. The server sends HTML. The browser can display it before React's client code runs; React-specific handlers and state are not attached yet, although ordinary HTML behavior still works.
2. The client loads React and hydrates the existing DOM. React expects the first client render to match the server HTML, then attaches component behavior.
3. After the client commit, `useEffect` can read browser-only state and schedule a later render. Effects do not run during server rendering, so they cannot supply initial server HTML.

A diagnostic example is `new Date().toLocaleDateString()` rendered during both server and initial client rendering: the clock, locale, or time zone can make the strings differ. Start with the hydration warning and compare the server output with the first client render; trace values that depend on time, randomness, browser APIs, or independently changing data. Prefer a stable value shared by both renders. If content must be browser-specific, render a stable initial placeholder and update after hydration, accepting that the user may see a second pass. `suppressHydrationWarning` is a narrow escape hatch for an unavoidable one-level text or attribute difference, not a fix for a mismatched subtree.

#### Place a Suspense boundary around a useful streamed region

In the App Router, the fetching guide documents route-level `loading.tsx` and smaller `<Suspense>` boundaries. Content outside a boundary can render while the child inside waits. Start independent data work before awaiting it, then let the child suspend so the boundary has time to show its fallback. The example follows the existing archived [App Router data-fetching and Suspense example](../../archive/front-end/0-1_Learning_Notes/next.js/readme.md); `getPosts()` is an application data function returning a promise.

```tsx
import { Suspense } from "react";

type Post = { id: number; title: string };

async function getPosts(): Promise<Post[]> {
  const response = await fetch("https://api.example.com/posts");
  if (!response.ok) throw new Error("Post request failed");
  return response.json();
}

export default function Page() {
  const posts = getPosts(); // start the request without blocking the page

  return (
    <main>
      <h1>Latest posts</h1>
      <Suspense fallback={<p>Loading posts…</p>}>
        <PostList posts={posts} />
      </Suspense>
    </main>
  );
}

async function PostList({ posts }: { posts: Promise<Post[]> }) {
  const items = await posts;
  return <ul>{items.map(post => <li key={post.id}>{post.title}</li>)}</ul>;
}
```

If the page awaits `getPosts()` before returning this tree, that request cannot be streamed inside the boundary. Place boundaries around independently useful parts: a boundary that is too high can hold back the whole page, while a boundary around a tiny fragment can create a choppy reveal. A fallback is visible page content, so give it meaningful text. If an update needs an assistive-technology announcement, add the appropriate live-region semantics; that does not move keyboard focus or create interaction behavior. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](#16.%20How%20does%20the%20CSS%20cascade%20decide%20which%20declaration%20applies?%20/%20CSS%20%E7%BA%A7%E8%81%94%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E6%9C%80%E7%BB%88%E7%94%9F%E6%95%88%E7%9A%84%E5%A3%B0%E6%98%8E%EF%BC%9F) for the focused keyboard, naming, and error model. A pending fallback also does not make a failed request successful; provide a separate error path.

### How does file-based routing work? / 文件系统路由如何工作？

**Core answer / 核心回答：** The route tree follows files, but the conventions differ between routers. Pages Router uses files such as pages/about.js and pages/posts/[id].js. App Router uses route segments containing page.tsx and can add layout.tsx, loading.tsx, and error.tsx. / 路由树由文件结构决定，但两种路由器的约定不同。Pages Router 使用 pages/about.js、pages/posts/[id].js 等文件；App Router 使用包含 page.tsx 的路由段，并可加入 layout.tsx、loading.tsx 和 error.tsx。

Use Link for navigation. Prefetching is production-only and differs by router: App Router can fully prefetch static routes and partially prefetch dynamic routes to a loading boundary; Pages Router's default behavior differs. Treat prefetch as an optimization, not a guarantee that a destination is already loaded.

In the Pages Router, an automatically statically optimized page may have an empty `router.query` during prerendering. In a client Effect that depends on those fields, check `router.isReady` before using them. [Versioned route-parameter examples / 路由参数版本示例](../../archive/front-end/Deprecated_Interview_Notes/react-router-v5-and-next-pages-router-parameters.md) · [Next.js Pages Router `useRouter`](https://nextjs.org/docs/pages/api-reference/functions/use-router)

### What are API routes and Route Handlers? / API routes和Route Handler是什么？

**Core answer / 核心回答：** Pages Router API routes use a default handler in pages/api. App Router Route Handlers use named HTTP method exports in a route.ts file. The runtime and deployment model depend on configuration and hosting; an endpoint is not automatically a serverless function just because it is in a Next.js app. / Pages Router 的 API route 在 pages/api 中使用默认 handler；App Router 的 Route Handler 在 route.ts 中导出 HTTP 方法函数。运行时和部署模型取决于配置与托管平台；接口不会因为位于 Next.js 应用中就自动成为 serverless function。

~~~ts
// app/api/hello/route.ts — App Router
export async function GET() {
  return Response.json({ message: "Hello from Next.js" });
}
~~~

Use framework endpoints for colocated, bounded server work such as webhooks or a small proxy. A larger backend may need its own service boundary, runtime, and operational controls.

**See also:** [React Routing and Navigation / React路由与导航](#61.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F) for client navigation and SPA/MPA document models; [React Basics / React基础](#6.%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E4%B8%80%E6%AC%A1%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F) for state-driven rendering; [Node.js Fundamentals / Node.js基础](../../engineering-foundations/backend/node-js-fundamentals.md) for server runtime constraints.

**Sources checked 2026-10-15:** [React release and version references](https://react.dev/versions), [React `hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot), [React `useEffect`](https://react.dev/reference/react/useEffect), [React `Suspense`](https://react.dev/reference/react/Suspense), [Next.js 16.4.1 App Router migration guide](https://nextjs.org/docs/app/guides/migrating/app-router-migration), [Next.js 16.4.1 Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data), [Pages Router getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props), [Pages Router getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths), [Pages Router Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration), [use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache), [Incremental Static Regeneration](https://nextjs.org/docs/app/guides/incremental-static-regeneration), [Link](https://nextjs.org/docs/app/api-reference/components/link), and [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route).
## 63. When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？

**Core answer / 核心回答：** Use Lodash when its documented path, collection, or timing contract removes repeated edge-case code. For a simple known shape, prefer the native operation when it expresses the same behavior more clearly; compare the exact semantics and installed version before substituting. This page is a method lookup, not a claim that one option is always smaller or faster. / Lodash 的路径、集合或定时语义能减少重复的边界处理时可使用它。对象结构简单明确时，如果原生操作能更清晰表达相同行为，就优先考虑原生 API；替换前要核对具体语义和安装版本。本文用于查找方法，不表示某种选择总是更小或更快。

### Common utilities / 常用工具

#### Arrays / 数组

| Signature | Behavior |
|---|---|
| _.chunk(array, size) | Split into groups of up to size items. |
| _.compact(array) | Remove false, null, 0, empty string, undefined, and NaN. |
| _.difference(array, values) | Keep values from the first array that are absent from the other array; returns a new array. |
| _.intersection(array, ...arrays) | Return values present in all arrays. |
| _.flatten(array) / _.flattenDeep(array) | Flatten one level / recursively flatten nested arrays. |
| _.uniq(array) | Return a new array with duplicate values removed. |

~~~javascript
_.chunk([1, 2, 3, 4], 2);          // [[1, 2], [3, 4]]
_.difference([2, 1], [2, 3]);     // [1]
_.intersection([1, 2], [2, 3]);   // [2]
_.flatten([1, [2, [3]]]);         // [1, 2, [3]]
~~~

Native Array.prototype.flat() defaults to depth 1; flat(Infinity) recursively flattens. That corresponds to the one-level and recursive distinction above, not a universal replacement for all Lodash collection semantics.

#### Collections / 集合

| Signature | Behavior |
|---|---|
| _.filter(collection, predicate) | Return every matching value. |
| _.find(collection, predicate) | Return the first matching value, or undefined. |
| _.map(collection, iteratee) | Transform values in arrays or object collections. |
| _.reduce(collection, iteratee, accumulator) | Accumulate values into one result. |
| _.groupBy(collection, iteratee) | Build an object whose keys come from the iteratee and whose values are matching arrays. |
| _.sortBy(collection, iteratees) | Sort ascending by one or more criteria. |
| _.orderBy(collection, iteratees, orders) | Sort by criteria with explicit asc/desc directions. |

~~~javascript
_.groupBy([6.1, 4.2, 6.3], Math.floor); // { "4": [4.2], "6": [6.1, 6.3] }
_.orderBy(users, ["age", "name"], ["desc", "asc"]);
~~~

#### Objects / 对象

| Signature | Behavior |
|---|---|
| _.get(object, path, defaultValue) | Read a deep path; use the default only when the resolved value is undefined. |
| _.set(object, path, value) | Create path segments as needed and mutate the target object. |
| _.merge(target, ...sources) | Recursively merge enumerable properties and mutate target. |
| _.assign(target, ...sources) | Shallow-assign own enumerable properties and mutate target. |
| _.pick(object, paths) / _.omit(object, paths) | Return a new object with selected / excluded paths. |
| _.cloneDeep(value) | Recursively clone values supported by Lodash's clone rules. |

~~~javascript
const city = _.get(user, "address.city", "Unknown");
const nullableCity = { address: { city: null } };
_.get(nullableCity, "address.city", "Unknown"); // null
nullableCity.address?.city ?? "Unknown";       // "Unknown"
~~~

The difference matters: Lodash's get default handles an absent path or undefined value, while JavaScript's nullish coalescing operator also falls back for null. For a statically known path, optional chaining plus an explicit fallback may be clearer.

#### Strings / 字符串

| Signature | Example result |
|---|---|
| _.camelCase(string) | _.camelCase("Foo BAR") → "fooBar" |
| _.kebabCase(string) | _.kebabCase("fooBar") → "foo-bar" |
| _.snakeCase(string) | _.snakeCase("fooBar") → "foo_bar" |
| _.capitalize(string) | _.capitalize("hello") → "Hello" |
| _.startCase(string) | _.startCase("fooBar") → "Foo Bar" |

### Debounce and throttle / 防抖与节流

**Core answer / 核心回答：** Debounce delays work until calls stop for a wait period; throttle limits calls to at most once per interval. Leading, trailing, and maxWait options change the contract, so describe the configuration being used. / debounce 会等到调用静止一段时间后再执行；throttle 将执行限制为每个时间间隔至多一次。leading、trailing 和 maxWait 选项会改变具体行为，因此要说明配置。

~~~javascript
const debouncedSearch = _.debounce(search, 300, {
  trailing: true,
  maxWait: 1000
});

input.addEventListener("input", debouncedSearch);

// When the listener is removed or the component is disposed:
debouncedSearch.cancel();
~~~

Lodash's debounced function also has flush() to invoke a pending call immediately. When both leading and trailing are enabled, a trailing invocation occurs only if there was another call during the wait period. Throttled functions also expose cancel() and flush(). Review the exact leading/trailing settings when a delayed call must not run after unmount or navigation.

### When should you use Lodash? / 何时使用Lodash？

Use the library when its edge-case behavior or object/path API simplifies real code. For a known object shape, optional chaining may be clearer; for unique values, Set may fit; for deep cloning, choose an API only after checking its supported data types and semantics. Bundle impact depends on module format and build configuration. Use per-method imports where appropriate and measure the production output rather than assuming a specific size reduction.

**See also:** [Modern JavaScript Features / 现代JavaScript特性](#51.%20How%20do%20edition%20and%20runtime%20support%20affect%20JavaScript%20feature%20use?%20/%20%E8%AF%AD%E8%A8%80%E7%89%88%E6%9C%AC%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6%E6%94%AF%E6%8C%81%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20JavaScript%20%E7%89%B9%E6%80%A7%E7%9A%84%E4%BD%BF%E7%94%A8%EF%BC%9F) for native alternatives such as structuredClone; [Performance Metrics and Analysis / 性能指标与分析](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F) for choosing debounce or throttle by workload.

**Sources checked 2026-10-15:** [Lodash 4.17.21 API source, including debounce and throttle](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md), [Array.prototype.flat()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat), [Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing).
## 64. When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？

**Core answer / 核心回答：** Use ahooks when an existing helper matches the interaction's state, lifecycle, request, or list contract and the installed package version. A helper still follows React's render and Effect rules; it does not replace decisions about data ownership, cache freshness, transport cancellation, or item identity. The APIs here follow documentation checked on 2026-10-15. / 当现有 ahooks 工具符合交互的状态、生命周期、请求或列表语义，并且与项目安装版本一致时再使用。工具仍遵守 React 的 render 和 Effect 规则；它不会替代对数据归属、缓存新鲜度、传输取消或列表项身份的判断。此处 API 依据 2026-10-15 核对的文档。

### Data fetching / 数据请求

#### useRequest

useRequest wraps an asynchronous service and exposes request state and controls. It runs on mount by default; manual: true makes the caller start it with run or runAsync.

~~~jsx
function UserButton({ userId }) {
  const { data, loading, error, run } = useRequest(fetchUser, {
    manual: true,
    retryCount: 2,
    onSuccess(user) {
      console.log(user);
    }
  });

  return (
    <button type="button" disabled={loading} onClick={() => run(userId)}>
      {loading ? "Loading" : "Load user"}
    </button>
  );
}
~~~

Choose polling, debounce, or retry options for the specific request. The useRequest cancel method ignores data and errors from the current Promise; it does not stop that Promise. In debounce mode, cancel can stop a call that has not started. Pass an AbortSignal to the service when the network transport itself must stop.

#### usePagination and useInfiniteScroll

usePagination expects a service that returns a total count and list, and exposes pagination state and change methods.

~~~javascript
const { data, loading, pagination } = usePagination(
  ({ current, pageSize }) => fetchUsers({ current, pageSize }),
  { defaultPageSize: 20 }
);

pagination.changeCurrent(2);
~~~

`useInfiniteScroll` passes the accumulated data to the service when loading more. For downward loading, return the next page's `list` and cursor so the Hook can append the page. Configure the scroll target and stopping rule for the UI. The [archive's list-loading example / 归档列表加载示例](../../archive/front-end/Deprecated_Interview_Notes/12.2%20ahooks.md#List-loading%20service%20contracts%20/%20%E5%88%97%E8%A1%A8%E5%8A%A0%E8%BD%BD%E7%9A%84%E6%9C%8D%E5%8A%A1%E5%A5%91%E7%BA%A6) shows the complete service contract. [ahooks v3.10.0 source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useInfiniteScroll/index.tsx)

### State and browser storage / 状态与浏览器存储

~~~javascript
const [enabled, { toggle, setTrue, setFalse }] = useBoolean(false);
const [settings, setSettings] = useLocalStorageState("settings", {
  defaultValue: {}
});
~~~

Other state utilities include useToggle, useMap, and useSet. useLocalStorageState serializes browser storage and can optionally synchronize changes from other tabs. Storage is browser-local and can fail or be unavailable in server rendering, so treat it as persistence convenience rather than a source of trusted data.

useLatest returns a ref whose current value is refreshed to the latest input. It can help a long-lived callback read current data without rebuilding a timer or listener on every render.

~~~javascript
const latestCount = useLatest(count);

useEffect(() => {
  const timer = setInterval(() => {
    console.log(latestCount.current);
  }, 1000);
  return () => clearInterval(timer);
}, []);
~~~

### Function identity and list rendering / 函数引用与列表渲染

useMemoizedFn returns a stable function reference that calls the latest function body. It can simplify a callback identity boundary, but it does not remove the need to understand which state a callback should observe.

~~~javascript
function SaveButton({ currentRecordId }) {
  const saveLatest = useMemoizedFn(() => save(currentRecordId));
  return <button onClick={saveLatest}>Save</button>;
}
~~~

useCreation(factory, deps) is an ahooks helper for creating a value with dependency-based reuse. Treat it as a library convenience rather than a resource-lifecycle primitive or a correctness guarantee.

useVirtualList renders a visible window and a buffer from a larger array. In ahooks 3.10.0, it returns the tuple [list, scrollTo(index)]; each list entry is shaped as { data, index }. Pass containerTarget and wrapperTarget refs in the options.

~~~jsx
const containerRef = useRef(null);
const wrapperRef = useRef(null);
const [list, scrollTo] = useVirtualList(users, {
  containerTarget: containerRef,
  wrapperTarget: wrapperRef,
  itemHeight: 48,
  overscan: 5
});

return (
  <>
    <button type="button" onClick={() => scrollTo(40)}>Jump to row</button>
    <div ref={containerRef} style={{ height: 360, overflow: "auto" }}>
      <div ref={wrapperRef}>
        {list.map(({ data, index }) => (
          <div key={data.id} style={{ height: 48 }}>{data.name}</div>
        ))}
      </div>
    </div>
  </>
);
~~~

ahooks v2.6.0 uses a different useVirtualList result shape with containerProps and wrapperProps; v3 redesigned this API. Do not mix the versions. The v2.6.0 package returns these props for the scroll container and wrapper:

~~~jsx
// ahooks 2.6.0 result shape; use only with the matching installed version.
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(users, {
  itemHeight: 48,
  overscan: 5
});

return (
  <div
    {...containerProps}
    style={{ ...containerProps.style, height: 360 }}
  >
    <div {...wrapperProps}>
      {list.map(({ data, index }) => (
        <div key={data.id} style={{ height: 48 }}>{data.name}</div>
      ))}
    </div>
  </div>
);
~~~

Variable-height rows need the measurement behavior supported by the installed version. See [Rendering and Computation Optimization / 渲染与计算优化](#14.%20%E9%95%BF%E6%8A%A5%E8%A1%A8%E5%88%97%E8%A1%A8%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%E8%99%9A%E6%8B%9F%E6%BB%9A%E5%8A%A8%EF%BC%9F).

useDynamicList exposes list and operations such as push, remove, move, insert, and getKey(index). Use getKey(index) as the React key so item identity survives edits; callbacks receive the current index.

~~~jsx
const { list, push, remove, insert, getKey } = useDynamicList([
  { name: "Ada" }
]);

return (
  <>
    {list.map((item, index) => (
      <div key={getKey(index)}>
        {item.name}
        <button type="button" onClick={() => remove(index)}>Remove</button>
      </div>
    ))}
    <button type="button" onClick={() => insert(0, { name: "Grace" })}>
      Add first
    </button>
    <button type="button" onClick={() => push({ name: "Lin" })}>Add</button>
  </>
);
~~~

### Effects and timing / Effect与时机

useMount and useUnmount package common Effect setup and cleanup. Their behavior follows React's Effect lifecycle, including the extra development setup-and-cleanup cycle under root StrictMode. They do not mean “run once for the lifetime of this process.”

useDebounce and useThrottle return delayed or rate-limited values; useDebounceFn and useThrottleFn wrap functions. Check whether the chosen hook returns a value, run function, or cancellation control before relying on an example from another version.

**Reach for ahooks / 何时使用：** It can reduce repeated hook boilerplate when its API matches the product behavior. Keep custom logic when cancellation, caching, errors, or data ownership need explicit control. For server-state caching and synchronization, compare a dedicated data library such as TanStack Query or SWR instead of assuming one hook collection covers every use case.

**See also / 另见** — [React component composition / React 组件组合](#7.%20%E5%A6%82%E4%BD%95%E5%9C%A8React%E4%B8%AD%E7%BB%84%E5%90%88%E7%BB%84%E4%BB%B6%E4%B8%8E%E5%A4%8D%E7%94%A8%E8%A1%8C%E4%B8%BA%EF%BC%9F) for Hook rules and Effect cleanup, [React server state / React 服务端状态](#9.%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F) for query and mutation rules, and [Performance Metrics and Analysis / 性能指标与分析](#12.%20%E5%A6%82%E4%BD%95%E6%B5%8B%E9%87%8F%E5%B9%B6%E8%AF%8A%E6%96%AD%E7%BD%91%E9%A1%B5%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98%EF%BC%9F) for debounce and throttle tradeoffs.

**Sources checked 2026-10-15:** [ahooks useRequest](https://ahooks.js.org/hooks/use-request), [ahooks v3.10.0 useRequest implementation](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/Fetch.ts), [ahooks v2 to v3 upgrade notes](https://ahooks.js.org/guide/upgrade/), [ahooks 2.6.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v2.6.0/packages/hooks/src/useVirtualList/index.ts), [ahooks 3.10.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useVirtualList/index.ts), [usePagination](https://ahooks.js.org/hooks/use-pagination), [useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll), [useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state), [useLatest](https://ahooks.js.org/hooks/use-latest), [useMemoizedFn](https://ahooks.js.org/hooks/use-memoized-fn), [useVirtualList](https://ahooks.js.org/hooks/use-virtual-list), [useCreation](https://ahooks.js.org/hooks/use-creation), [useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn), [useThrottle](https://ahooks.js.org/hooks/use-throttle), [useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn), [useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list), [useUnmount](https://ahooks.js.org/hooks/use-unmount), [React StrictMode](https://react.dev/reference/react/StrictMode).
## 65. What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？

**Core answer / 核心回答：** Build the production output, run a critical browser journey against that output on a production-like server, then promote the exact artifact that passed. A development server alone does not exercise emitted assets or deployment paths. The general risk-to-test-boundary principle belongs to [Software Testing Strategy / 软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md); the tool choices for local logic and component behavior are outlined below. / 构建生产产物，在接近生产环境的服务上用该产物运行关键浏览器流程，然后晋级同一份通过检查的产物。单独运行开发服务器无法覆盖实际生成的资源或部署路径。通用的风险与测试边界原则见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)；本地逻辑和组件行为的工具选择见下文。

### How should frontend tests be divided? / 前端测试如何分层？

**Core answer / 核心回答：** Use a unit test for isolated logic, a component integration test for user-visible wiring, and a browser test when real navigation, persistence, browser behavior, emitted assets, or service wiring is part of the risk. Keep the feedback loop cheap where it can provide reliable evidence. / 隔离逻辑用单元测试，验证用户可见的组件连接用集成测试；当风险涉及真实导航、持久化、浏览器行为、生成资源或服务连接时使用浏览器测试。能可靠提供证据时，优先保持反馈成本较低。

| Layer | Useful for | Example tools |
|---|---|---|
| Unit | Pure functions and isolated behavior | Jest, Vitest |
| Integration | Components, hooks, context, and API boundaries together | React Testing Library with Jest or Vitest |
| End-to-end | Browser navigation, persistence, and critical user journeys | Playwright, Cypress |

Keep browser tests for behavior that depends on the real browser or application wiring. A test pyramid is a planning aid; a project's distribution should follow its actual risks and feedback costs.

### Jest fundamentals / Jest基础

Use Jest when the risk can be reproduced around logic, state, or a dependency boundary. A test that starts asynchronous work must return or await the Promise that contains its assertions. Place the mock at the dependency and assert the behavior of the caller. [How a Jest test verifies asynchronous behavior / Jest 怎样验证异步行为](#66.%20How%20can%20a%20Jest%20test%20verify%20behavior%20across%20an%20asynchronous%20boundary?%20/%20Jest%20%E6%80%8E%E6%A0%B7%E9%AA%8C%E8%AF%81%E8%B7%A8%E5%BC%82%E6%AD%A5%E8%BE%B9%E7%95%8C%E7%9A%84%E8%A1%8C%E4%B8%BA%EF%BC%9F) contains the complete async, lifecycle, matcher, CommonJS and native ESM examples.

### React Testing Library / React Testing Library

Test through user-visible roles, labels, text, and interactions. Queries have different timing contracts:

| Query | Use when |
|---|---|
| getBy... | The element should exist now; throws if absent or ambiguous. |
| queryBy... | Checking that an element is absent; returns null if absent. |
| findBy... | The element should appear asynchronously; returns a Promise. |

Prefer getByRole with an accessible name when it represents the user's interaction. Use getByLabelText for form controls. A test ID is an escape hatch when the UI has no suitable user-facing query.

~~~jsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

test("submits the entered email", async () => {
  // Arrange
  const user = userEvent.setup();
  const onSubmit = jest.fn();
  render(<EmailForm onSubmit={onSubmit} />);

  // Act
  await user.type(
    screen.getByRole("textbox", { name: /email/i }),
    "person@example.com"
  );
  await user.click(screen.getByRole("button", { name: /submit/i }));

  // Assert
  expect(onSubmit).toHaveBeenCalledWith("person@example.com");
});
~~~

userEvent models a higher-level interaction sequence, including keyboard and focus behavior. It is not a real browser. fireEvent dispatches a lower-level event and can be useful when a test specifically needs that event boundary.

The form test above follows Arrange–Act–Assert (AAA): prepare the user and component, perform the interaction, then check the observable result.

For an asynchronous appearance, prefer findBy...:

~~~javascript
const result = await screen.findByText("Loaded");
expect(result).toBeInTheDocument();
~~~

Use waitFor when the assertion itself needs retrying. Its callback must throw for a retry; returning false does not request another attempt. Avoid placing side effects inside waitFor because the callback can run more than once.

### Testing custom Hooks and snapshots / 测试自定义Hook与快照

React Testing Library exports renderHook from @testing-library/react. It renders a test component around the Hook. Most Testing Library render and interaction helpers already use React act; use act for an update initiated outside those helpers when the test needs to flush it.

~~~javascript
import { act, renderHook } from "@testing-library/react";

test("increments the counter", () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => result.current.increment());

  expect(result.current.count).toBe(1);
});
~~~

Snapshots can capture stable structure, but a large snapshot does not explain which behavior matters. Use focused assertions for user-visible behavior and update snapshots intentionally when the expected output changes.

### Release checks / 发布检查

CI should connect fast source checks to the exact production output. A small frontend release path is:

**核心原则 / Core idea：** 先完成类型、单元和组件检查，再生成生产构建；用接近生产的服务运行这份构建产物，执行关键浏览器流程，最后晋级同一份已验证产物，避免重新构建后发布了另一份代码。HMR 只验证开发热更新链路，不能证明生产资源路径、分块或发布产物正常；Vite preview 可以本地预览刚生成的 `dist`，但官方定位不是生产服务器。Source map 应关联到具体发布版本并受控上传；`hidden` 只隐藏源码映射注释，不阻止他人直接访问映射文件。

~~~text
lockfile install -> type check -> unit/component tests -> production build
  -> serve the built output -> one critical browser smoke -> retain/promote that output
~~~

For example, a project can run `npm run typecheck`, `npm run test:ci`, and `npm run build`, then `npx playwright test tests/release-smoke.spec.ts`. Configure Playwright's `webServer.command` to start `npm run preview` (or the framework's built-output server) after the build so this browser test sees emitted assets rather than the HMR server; script names are project-specific.

Type checks catch static contract errors; unit and component tests catch local logic and UI wiring; a production build catches transforms, asset emission, and chunk or base-path issues that a dev server may not exercise. Then serve the generated output with a production-like static server and run one browser test for a critical journey, such as opening search, submitting a query, and seeing results. A Playwright `webServer` can start the local artifact server for the test; with Vite, `vite preview` serves the just-built `dist` locally for this check, but is not a production server. Promote the tested output rather than rebuilding it for release.

Use browser checks where real routing, asset URLs, browser behavior, or app/service wiring matters. A passing HMR session proves the development loop works; it does not prove production chunks load from the deployed base path or that the published artifact works. Source maps can translate minified error locations back to original source when tied to a release and uploaded to a controlled error-reporting system. A hidden map removes the source-map comment, not the file or access risk; do not leave private maps at a public asset URL. The shared [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) note owns artifact promotion, runtime secrets, and rollout gates.

**See also:** [Advanced React / React进阶](#8.%20%E5%A6%82%E4%BD%95%E8%AE%A9%E6%8A%A5%E8%A1%A8%E7%AD%9B%E9%80%89%E5%9C%A8%E6%98%82%E8%B4%B5%E6%9B%B4%E6%96%B0%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) for custom Hook semantics; [Git Essentials / Git基础](../../engineering-foundations/version-control/git-essentials.md) for how tests fit into review and CI.

**Sources checked 2026-10-15:** [Jest Mock Functions](https://jestjs.io/docs/mock-functions), [Jest Object and Mock Lifecycle](https://jestjs.io/docs/jest-object), [Jest ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules), [React Testing Library API](https://testing-library.com/docs/react-testing-library/api/), [Testing Library Queries](https://testing-library.com/docs/queries/about/), [user-event](https://testing-library.com/docs/user-event/intro/), [Testing Library Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/), [Vite static deployment](https://vite.dev/guide/static-deploy.html), [Playwright web server](https://playwright.dev/docs/test-webserver).
## 66. How can a Jest test verify behavior across an asynchronous boundary? / Jest 怎样验证跨异步边界的行为？

Wait for the Promise that carries the assertion, give the code under test an explicit dependency boundary, and assert what the code does with the result. Set up and restore only the resources the test owns. Module mocking depends on the test's module system. / 等待承载断言的 Promise，在被测代码的依赖边界安排模拟，并断言被测代码如何处理结果。测试只负责准备和恢复自己拥有的资源。模块模拟方式取决于测试使用的模块系统。

**Key terms / 关键术语** · observable behavior / 可观察行为 · dependency boundary / 依赖边界 · test lifecycle / 测试生命周期 · module mock / 模块模拟

### Suites and cases / 测试套件与用例

describe groups related tests; test and its alias it define a case. Use clear names that describe behavior. Starting a name with “should” is a style choice, not a Jest requirement.

~~~javascript
function add(left, right) {
  return left + right;
}

function subtract(left, right) {
  return left - right;
}

describe('calculator', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  test('subtracts a larger value', () => {
    expect(subtract(5, 10)).toBe(-5);
  });
});
~~~

Arrange–Act–Assert makes setup, behavior, and verification easy to scan. A small test may not need a separate variable for every phase.

Common file names include .test.js and .spec.js; the project’s Jest configuration determines which files are collected.

### Async tests / 异步测试

Return or await the Promise so Jest waits for the assertion. For rejected Promises, use the rejects matcher.

~~~javascript
test('loads a user', async () => {
  const user = await getUser(1);
  expect(user).toHaveProperty('id', 1);
});

test('reports a failed request', async () => {
  await expect(getUser(-1)).rejects.toThrow('not found');
});
~~~

A test that starts an asynchronous operation but neither awaits it nor returns its Promise can finish before the assertion runs.

### Setup and cleanup / 准备与清理

beforeAll and afterAll run once around a test scope; beforeEach and afterEach run around each test in that scope. Use cleanup hooks for resources that tests actually open.

~~~javascript
describe('temporary resource', () => {
  let resource;

  beforeAll(async () => {
    resource = await openResource();
  });

  afterAll(async () => {
    await resource.close();
  });

  beforeEach(async () => {
    await resource.clear();
  });

  test('stores a record', async () => {
    await resource.insert({ id: 1, name: 'Ada' });
    expect(await resource.count()).toBe(1);
  });
});
~~~

### Mock functions and spies / Mock 函数与 spy

#### jest.fn

jest.fn creates a mock function whose calls and results can be inspected.

~~~javascript
const callback = jest.fn();
callback('saved');

expect(callback).toHaveBeenCalledWith('saved');
expect(callback).toHaveBeenCalledTimes(1);
~~~

#### jest.mock in a CommonJS/transformed setup

This example uses CommonJS require with a test configuration that transforms or otherwise supports this mocking pattern. In Babel-transformed tests, jest.mock calls are hoisted by the Jest transformer, so the mock is registered before the module is required.

~~~javascript
jest.mock('./api', () => ({
  fetchUser: jest.fn(),
}));

const api = require('./api');
const { loadUser } = require('./userService'); // userService delegates to api.fetchUser

test('uses the API boundary', async () => {
  api.fetchUser.mockResolvedValue({ id: 1, name: 'Ada' });

  await expect(loadUser(1)).resolves.toEqual({ id: 1, name: 'Ada' });
});
~~~

A module mock replaces a dependency at the module boundary. The test should still assert the behavior of the code under test rather than only reasserting the mock configuration.

#### Native ESM modules

Native ESM evaluates static imports before the test body, so the CommonJS-style hoisting example does not apply. Jest's documentation provides jest.unstable_mockModule followed by dynamic import for ESM mocking. The API name is marked unstable; check the Jest version and runtime configuration.

~~~javascript
import { jest } from '@jest/globals';

jest.unstable_mockModule('./api.js', () => ({
  fetchUser: jest.fn(),
}));

const { fetchUser } = await import('./api.js');
~~~

#### jest.spyOn

jest.spyOn observes an existing object method and calls the original implementation by default. Provide a mock implementation or return value when the test needs replacement behavior. Restore the spy after use.

~~~javascript
const service = {
  greet: name => 'Hello ' + name,
};

const spy = jest.spyOn(service, 'greet').mockReturnValue('Hi Bob');

expect(service.greet('Bob')).toBe('Hi Bob');
expect(spy).toHaveBeenCalledWith('Bob');

spy.mockRestore();
~~~

mockRestore restores a spy created by jest.spyOn. Use clearAllMocks, resetAllMocks, or restoreAllMocks according to whether the test needs to clear call history, reset implementations, or restore replaced properties; these operations are not interchangeable.

### Common matchers / 常见 matcher

| Matcher | Use |
|---|---|
| **toBe(value)** | Compare with Object.is semantics. |
| **toEqual(value)** | Compare nested object or array values. |
| **toStrictEqual(value)** | Also distinguish missing properties from properties set to `undefined` and similar structural cases. |
| **toMatchObject(value)** | Check that an object contains the expected subset. |
| **toBeTruthy / toBeFalsy** | Check the Boolean coercion of a value. |
| **toBeNull / toBeUndefined** | Distinguish null from undefined. |
| **toContain(value)** | Check an array item or string substring. |
| **toHaveLength(n)** | Check a length property. |
| **toThrow(error)** | Check a synchronous function for a thrown error; pass the function, not its already-evaluated result. |
| **toHaveBeenCalled()** | Check that a mock or spy was called. |
| **toHaveBeenCalledWith(args)** | Check arguments recorded by a mock or spy. |

### Coverage / 覆盖率

Run Jest with the project’s configured coverage option, commonly --coverage. Coverage reports which statements, branches, functions, and lines ran; a high percentage does not prove that assertions check meaningful behavior or edge cases.

### References / 参考资料

- [Jest 30.0 documentation](https://jestjs.io/docs/30.0/getting-started)
- [Jest: ECMAScript Modules](https://jestjs.io/docs/30.0/ecmascript-modules)
- [Jest: The Jest Object](https://jestjs.io/docs/30.0/jest-object)
- [Jest: Mock Functions](https://jestjs.io/docs/30.0/mock-functions)
- [Frontend Testing / 前端测试](#65.%20What%20evidence%20shows%20a%20frontend%20change%20works%20through%20production%20delivery?%20/%20%E5%93%AA%E4%BA%9B%E8%AF%81%E6%8D%AE%E8%83%BD%E8%AF%81%E6%98%8E%E5%89%8D%E7%AB%AF%E6%94%B9%E5%8A%A8%E5%8F%AF%E7%94%A8%E5%B9%B6%E8%83%BD%E6%AD%A3%E7%A1%AE%E4%BA%A4%E4%BB%98%EF%BC%9F)
