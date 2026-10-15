**Browser Basics / 浏览器基础**

Think in stages—fetch, parse, compute style and layout, paint, then present—but treat the exact architecture as engine-specific. 浏览器常可按获取、解析、样式与布局、绘制和合成来理解；具体流水线属于实现，不是跨浏览器 API 保证。

Two interview questions this note prepares you for:

1. **What are the major components of a browser, and what do they do?**
2. **What happens when you type a URL and press Enter?** — the single most-asked frontend interview question.

Along the way it covers the follow-ups most candidates hit next: why `<script>` blocks HTML parsing, reflow vs. paint vs. composite, and how to optimize the critical rendering path.

---

## What are the major components of a modern browser?

**Headline (30s):** A useful high-level model separates rendering, JavaScript execution, networking, and storage. The browser coordinates them, but process boundaries, worker threads, cache layers, and the rendering pipeline vary by engine and platform. **中文：** 可按渲染、脚本执行、网络和存储建立心智模型；进程和线程划分由实现决定。

**Why it's asked:** The interviewer wants to hear that you have a mental model of where work happens. Candidates who can't separate "rendering" from "JS execution" tend to write code that surprises them later (layout thrashing, stale caches, blocking scripts).

### Rendering engine

- **Engines**: Blink (Chrome, Edge), WebKit (Safari), Gecko (Firefox).
- **Typical work**: parse HTML into the DOM; parse CSS rules and compute styles; determine boxes and geometry (layout); produce paint instructions; then present the result. Engines use different internal trees and may skip stages when a change does not require them.
- `display: none` generates no principal box; `visibility: hidden` keeps layout space while hiding the element. These are CSS box-generation and visibility rules, not a promise about a particular internal “render tree.”

### JavaScript engine

- **Runtimes**: V8 (Chrome, Node), SpiderMonkey (Firefox), JavaScriptCore (Safari).
- **Key pieces**:
- **Execution and optimization** — engines interpret and/or compile code using implementation-specific strategies; JIT is common but not a language guarantee.
- **Event loop and task queues** — the host schedules timers, promises, networking, and rendering callbacks. See [`7.1 Event Loop`](../runtime/event-loop.md); browser and Node host scheduling differ.
  - **Memory heap + call stack** — object allocation and function execution.

### Networking layer

- **HTTP, TLS, and caches** — requests may be served by browser caches or a service worker before reaching the network. HTTP/2 multiplexes streams over a connection; HTTP/3 uses QUIC over UDP.
- **HSTS** tells a user agent to use HTTPS for a host under the policy's rules.
- **CORS controls response sharing with script, not whether every cross-origin request is sent.** Some requests are sent without a preflight; a preflight is used for requests outside the safelisted cases. A server may already have received a request even when the browser does not expose its response to script. See the [Fetch Standard](https://fetch.spec.whatwg.org/#http-cors-protocol).
- See [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md) for HTTP details.

### Storage

- **Cookies** may accompany matching requests; **localStorage** and **sessionStorage** are synchronous Web Storage; **IndexedDB** supports transactions; **Cache API** stores request/response pairs. Quotas, persistence, and embedded-context access are subject to browser policy. See [`5.2 Browser Storage and Communication`](../browser-apis/browser-storage-and-communication.md).

**See also:** [`7.1 Event Loop`](../runtime/event-loop.md), [`5.2 Browser Storage and Communication`](../browser-apis/browser-storage-and-communication.md), [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md).

---

## What happens when you type a URL and press Enter?

**Headline (30s):** A navigation may consult caches or a service worker, resolve a host, establish or reuse a connection, and request a document. The browser can parse streamed HTML and start fetching discovered resources while parsing continues. Style, layout, script, paint, and presentation can overlap; this is a simplified model, not a single mandatory sequence. **中文：** 导航可能命中缓存或 Service Worker；解析和资源获取可以交叠，渲染阶段也不必严格串行。

**Why it's asked:** This is the "show me your whole mental model in one question" probe. Interviewers want to hear the three big phases (fetch → parse → render) and at least one intelligent follow-up-worthy detail per phase.

### Phase 1 — Resource fetching

- **Name resolution and connection setup** — a network navigation may require DNS and a new connection, but caches, connection reuse, proxies, or service workers can change the path.
- **Transport and security** — HTTP/1.1 and HTTP/2 commonly use TCP; HTTPS authenticates and encrypts with TLS. HTTP/3 uses QUIC over UDP and avoids TCP's cross-stream transport head-of-line blocking.
- Resource hints such as `dns-prefetch` and `preconnect` are hints; the user agent decides how to act on them.

### Phase 2 — Parsing and the critical rendering path

1. **DOM construction**: bytes → characters → tokens → nodes → DOM tree.
2. **Style computation**: CSS is parsed and the cascade determines computed styles; box generation follows the resulting styles and layout mode.
3. **Layout**: the engine computes boxes and geometry. The specifications define layout results; the internal representation is engine-specific.

**Gotcha — parser-blocking scripts:** A parser-inserted classic script without `async` or `defer` can pause HTML parsing while it is fetched and run. Earlier blocking stylesheets can delay script execution when the script may inspect styles. Stylesheets and scripts can therefore delay visible content, but “the browser waits for a complete CSSOM before every first paint” is too broad.

### Phase 3 — Layout, paint, composite

- **Style and layout** — compute styles and the geometry needed for the current presentation. DOM or CSS changes can invalidate work; a geometry read after a write may force pending style/layout work to be calculated synchronously.
- **Paint and presentation** — engines create and update paint output, then present it. A change may skip layout or paint when the engine can reuse existing work.
- **Compositing** — engines may composite layers separately. `transform` and `opacity` can be compositor-friendly for some elements and engines, but do not guarantee a layer or GPU execution.

**Follow-up — “Is it fetch, then parse, then render, strictly in order?”** No. Parsing can begin before the response completes, and an engine may discover and fetch resources early. Script execution and stylesheets can pause parts of that work; presentation can update incrementally.

**See also:** [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md), [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md).

---

## How do URLs and same-document navigation work? / URL 与同文档导航如何工作？

**Core answer / 核心回答：** `URL` parses and serializes a complete address; `URLSearchParams` reads and edits its query pairs. An anchor or `location.assign()` requests navigation to a URL: it normally loads another document, but a fragment-only navigation can remain in the current document. `history.pushState()` and `replaceState()` instead update the current document's session history and URL without loading another document. Those History API calls do not dispatch `popstate`; Back/Forward traversal does, so an app should read the current URL then and synchronize its displayed state. / `URL` 负责解析和序列化完整地址，`URLSearchParams` 读写查询参数。链接或 `location.assign()` 会请求导航到某个 URL：通常会加载新文档，但仅改变片段时可以留在当前文档。`history.pushState()` 和 `replaceState()` 则在当前文档内更新会话历史和 URL，不会加载新文档。它们本身不会触发 `popstate`；浏览器前进或后退遍历历史记录时才会触发，因此应用应在该事件中读取当前 URL 并同步界面。

### Parse query state and choose the navigation operation

- Start from `new URL(location.href)` rather than splitting a URL string by `?` or `&`. Read a single value with `searchParams.get(name)` and repeated values with `getAll(name)`. `set(name, value)` replaces existing pairs with that name; use `append()` when duplicates are intentional. Serializing through `url.search` or `url.href` applies URL encoding.
- An anchor or `location.assign(url)` asks the browser to navigate to a URL and normally creates a history entry; `location.replace(url)` navigates while replacing the current entry. The browser may reuse a document for a same-document fragment navigation, so “navigation” does not always mean a new network request.
- `pushState(state, "", url)` adds a same-document history entry; `replaceState(state, "", url)` edits the current one. The URL must remain same-origin. Neither method fetches that URL or emits `popstate`; update the UI directly after calling it. On Back/Forward traversal, handle `popstate` by deriving the view from `location` (and `event.state` if the app uses it).

This makes filters and tabs linkable and restorable through Back/Forward. Treat query values as untrusted input, validate them against supported options, and avoid putting secrets in a URL.

```html
<label for="sort">Sort results</label>
<select id="sort">
  <option value="recent">Most recent</option>
  <option value="oldest">Oldest first</option>
</select>
<p id="summary"></p>

<script>
const sortSelect = document.querySelector("#sort");
const summary = document.querySelector("#summary");

function syncFromUrl() {
  const url = new URL(location.href);
  const sort = url.searchParams.get("sort") === "oldest" ? "oldest" : "recent";
  sortSelect.value = sort;
  summary.textContent = sort === "oldest" ? "Oldest results first" : "Most recent results first";
}

sortSelect.addEventListener("change", () => {
  const url = new URL(location.href);
  url.searchParams.set("sort", sortSelect.value);
  history.pushState(null, "", url.href);
  syncFromUrl(); // pushState does not dispatch popstate
});

window.addEventListener("popstate", syncFromUrl);
syncFromUrl();
</script>
```

**See also:** [React Router / React 路由](../frameworks/react-basics.md) uses browser history for client-side routes; [Performance Metrics and Analysis / 性能指标与分析](../performance/performance-metrics-and-analysis.md) explains `DOMContentLoaded` and `load`; the [archived URL, location, and History reference](../../archive/front-end/0-1_Learning_Notes/Javascript/readme.md) retains the broader property and method catalog.

**Sources checked 2026-10-15:** [WHATWG URL Standard](https://url.spec.whatwg.org/#urlsearchparams-class) (Living Standard updated 2026-10-07) and [WHATWG HTML Standard: History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface) (Living Standard updated 2026-10-14).

---

## Why does a `<script>` tag block HTML parsing? What do `async` and `defer` change?

**Headline (30s):** A parser-inserted classic script without `async`, `defer`, or another applicable scheduling rule can pause parsing while it is fetched and executed. For classic external scripts, `defer` preserves order and runs after parsing before `DOMContentLoaded`; `async` runs when ready without preserving order. Module scripts are deferred by default unless `async` is present. **中文：** classic `defer` 保序并在解析后执行；`async` 不保序；模块脚本默认延后执行。

**How it works:**

| Attribute | Downloaded | Executed | Blocks parser? | Order preserved? |
|---|---|---|---|---|
| Classic parser-inserted, no attribute | inline or fetched by parser | when parser reaches and can run it | yes | parser order |
| Classic external `defer` | in parallel | after parsing, before `DOMContentLoaded` | no | yes among deferred scripts |
| Classic external `async` | in parallel | when ready | no | no |
| Module script | module graph fetched | deferred by default; `async` changes scheduling | no for normal module scripts | module graph rules apply |

**Gotcha — `defer` applies to classic external scripts:** It has no effect on classic inline scripts; module scripts are deferred by default. Use `async` only when execution order is unimportant.

**See also:** [`2.4 Browser - HTML & CSS part`](../html-css/browser-html-and-css.md) for placement strategy and more `<script>` gotchas.

---

## Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?

**Headline (30s):** Geometry changes commonly require layout; paint-only changes can skip layout; some composited changes can skip both. Which stages run, how much work they cover, and whether a GPU participates depend on the changed property, page, and engine. **中文：** 属性变化可能使布局、绘制或合成失效；实际成本必须按页面和浏览器测量。

**Typical invalidation paths (implementation-dependent):**

1. **Style + layout + paint + presentation** — changes affecting geometry or wrapping, such as many width or font changes.
2. **Style + paint + presentation** — visual changes that do not affect geometry, such as many color changes.
3. **Style + compositor update** — some `transform` / `opacity` changes on elements already suitable for compositing.

These paths are examples, not CSS guarantees. Layer setup, affected-area size, and GPU use depend on the engine and page.

**Gotcha — forced synchronous layout:** Reading current geometry (`offsetHeight`, `getBoundingClientRect`) after a write can force pending style/layout work to be calculated before the value is returned. Repeating write/read pairs can repeat that work. `scrollTop` is a scroll position rather than a geometry measurement. Batch reads before writes when that fits the task, and inspect a performance trace to confirm the issue.

```javascript
// may repeatedly force pending style/layout work
for (const el of items) {
  el.style.width = el.offsetWidth + 10 + 'px';
}

// collect measurements before writing
const widths = items.map(el => el.offsetWidth);
items.forEach((el, i) => { el.style.width = widths[i] + 10 + 'px'; });
```

**See also:** [`2.4 Browser - HTML & CSS part`](../html-css/browser-html-and-css.md) for rendering triggers and optimization tactics, [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md).

---

## How do you optimize the critical rendering path?

**Headline (30s):** Reduce blocking work, let the browser discover critical resources early, and avoid repeated synchronous layout. Validate the result with page-level measurements; `preconnect`, critical CSS, image loading policy, and animation choices all depend on the page and target browsers. **中文：** 优化应从减少阻塞、尽早发现关键资源和避免重复同步布局入手，并用页面测量验证。

**Tactics:**

- **Render-blocking mitigation** — defer scripts whose work is not needed during parsing; critical CSS can reduce a separate blocking request but increases HTML and affects caching; use `content-visibility: auto` only when its rendering semantics fit.
- **Network** — `<link rel="preconnect">` can warm up a connection; use `loading="lazy"` for genuinely off-screen images, not likely LCP images; select image formats and HTTP versions based on target support and measurements.
- **Runtime** — debounce or throttle only when event frequency requires it; use `requestAnimationFrame` for visual updates; profile before preferring `transform`/`opacity` over layout properties.
- **SSR + hydration** — serve HTML first, let client JS attach listeners on top (as in React hydration).
- **Early resource discovery** — some engines use speculative loading while parsing is blocked. This is an implementation optimization, not a page-level guarantee.

**See also:** [`11.1 Performance Metrics and Analysis`](../performance/performance-metrics-and-analysis.md), [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md), [`5.3 Image Lazy Loading`](../browser-apis/image-lazy-loading.md).

**Standards and implementation notes / 标准与实现资料：** [WHATWG HTML scripting](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element), [Fetch Standard: CORS](https://fetch.spec.whatwg.org/#http-cors-protocol), [CSS Display](https://www.w3.org/TR/css-display-3/), [Chrome RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), [Chrome forced-reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
