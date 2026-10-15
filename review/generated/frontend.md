# Frontend

> Generated from the [frontend reading map](../../frontend/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. Browser Basics / 浏览器基础

**Browser Basics / 浏览器基础**

Think in stages—fetch, parse, compute style and layout, paint, then present—but treat the exact architecture as engine-specific. 浏览器常可按获取、解析、样式与布局、绘制和合成来理解；具体流水线属于实现，不是跨浏览器 API 保证。

Two interview questions this note prepares you for:

1. **What are the major components of a browser, and what do they do?**
2. **What happens when you type a URL and press Enter?** — the single most-asked frontend interview question.

Along the way it covers the follow-ups most candidates hit next: why `<script>` blocks HTML parsing, reflow vs. paint vs. composite, and how to optimize the critical rendering path.

---

#### What are the major components of a modern browser?

**Headline (30s):** A useful high-level model separates rendering, JavaScript execution, networking, and storage. The browser coordinates them, but process boundaries, worker threads, cache layers, and the rendering pipeline vary by engine and platform. **中文：** 可按渲染、脚本执行、网络和存储建立心智模型；进程和线程划分由实现决定。

**Why it's asked:** The interviewer wants to hear that you have a mental model of where work happens. Candidates who can't separate "rendering" from "JS execution" tend to write code that surprises them later (layout thrashing, stale caches, blocking scripts).

##### Rendering engine

- **Engines**: Blink (Chrome, Edge), WebKit (Safari), Gecko (Firefox).
- **Typical work**: parse HTML into the DOM; parse CSS rules and compute styles; determine boxes and geometry (layout); produce paint instructions; then present the result. Engines use different internal trees and may skip stages when a change does not require them.
- `display: none` generates no principal box; `visibility: hidden` keeps layout space while hiding the element. These are CSS box-generation and visibility rules, not a promise about a particular internal “render tree.”

##### JavaScript engine

- **Runtimes**: V8 (Chrome, Node), SpiderMonkey (Firefox), JavaScriptCore (Safari).
- **Key pieces**:
- **Execution and optimization** — engines interpret and/or compile code using implementation-specific strategies; JIT is common but not a language guarantee.
- **Event loop and task queues** — the host schedules timers, promises, networking, and rendering callbacks. See [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF); browser and Node host scheduling differ.
  - **Memory heap + call stack** — object allocation and function execution.

##### Networking layer

- **HTTP, TLS, and caches** — requests may be served by browser caches or a service worker before reaching the network. HTTP/2 multiplexes streams over a connection; HTTP/3 uses QUIC over UDP.
- **HSTS** tells a user agent to use HTTPS for a host under the policy's rules.
- **CORS controls response sharing with script, not whether every cross-origin request is sent.** Some requests are sent without a preflight; a preflight is used for requests outside the safelisted cases. A server may already have received a request even when the browser does not expose its response to script. See the [Fetch Standard](https://fetch.spec.whatwg.org/#http-cors-protocol).
- See [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md) for HTTP details.

##### Storage

- **Cookies** may accompany matching requests; **localStorage** and **sessionStorage** are synchronous Web Storage; **IndexedDB** supports transactions; **Cache API** stores request/response pairs. Quotas, persistence, and embedded-context access are subject to browser policy. See [`5.2 Browser Storage and Communication`](#23.%20Browser%20Storage%20and%20Communication%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AD%98%E5%82%A8%E4%B8%8E%E9%80%9A%E4%BF%A1).

**See also:** [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF), [`5.2 Browser Storage and Communication`](#23.%20Browser%20Storage%20and%20Communication%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%AD%98%E5%82%A8%E4%B8%8E%E9%80%9A%E4%BF%A1), [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md).

---

#### What happens when you type a URL and press Enter?

**Headline (30s):** A navigation may consult caches or a service worker, resolve a host, establish or reuse a connection, and request a document. The browser can parse streamed HTML and start fetching discovered resources while parsing continues. Style, layout, script, paint, and presentation can overlap; this is a simplified model, not a single mandatory sequence. **中文：** 导航可能命中缓存或 Service Worker；解析和资源获取可以交叠，渲染阶段也不必严格串行。

**Why it's asked:** This is the "show me your whole mental model in one question" probe. Interviewers want to hear the three big phases (fetch → parse → render) and at least one intelligent follow-up-worthy detail per phase.

##### Phase 1 — Resource fetching

- **Name resolution and connection setup** — a network navigation may require DNS and a new connection, but caches, connection reuse, proxies, or service workers can change the path.
- **Transport and security** — HTTP/1.1 and HTTP/2 commonly use TCP; HTTPS authenticates and encrypts with TLS. HTTP/3 uses QUIC over UDP and avoids TCP's cross-stream transport head-of-line blocking.
- Resource hints such as `dns-prefetch` and `preconnect` are hints; the user agent decides how to act on them.

##### Phase 2 — Parsing and the critical rendering path

1. **DOM construction**: bytes → characters → tokens → nodes → DOM tree.
2. **Style computation**: CSS is parsed and the cascade determines computed styles; box generation follows the resulting styles and layout mode.
3. **Layout**: the engine computes boxes and geometry. The specifications define layout results; the internal representation is engine-specific.

**Gotcha — parser-blocking scripts:** A parser-inserted classic script without `async` or `defer` can pause HTML parsing while it is fetched and run. Earlier blocking stylesheets can delay script execution when the script may inspect styles. Stylesheets and scripts can therefore delay visible content, but “the browser waits for a complete CSSOM before every first paint” is too broad.

##### Phase 3 — Layout, paint, composite

- **Style and layout** — compute styles and the geometry needed for the current presentation. DOM or CSS changes can invalidate work; a geometry read after a write may force pending style/layout work to be calculated synchronously.
- **Paint and presentation** — engines create and update paint output, then present it. A change may skip layout or paint when the engine can reuse existing work.
- **Compositing** — engines may composite layers separately. `transform` and `opacity` can be compositor-friendly for some elements and engines, but do not guarantee a layer or GPU execution.

**Follow-up — “Is it fetch, then parse, then render, strictly in order?”** No. Parsing can begin before the response completes, and an engine may discover and fetch resources early. Script execution and stylesheets can pause parts of that work; presentation can update incrementally.

**See also:** [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96), [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](../../engineering-foundations/networking/http-protocols-and-websockets.md).

---

#### How do URLs and same-document navigation work? / URL 与同文档导航如何工作？

**Core answer / 核心回答：** `URL` parses and serializes a complete address; `URLSearchParams` reads and edits its query pairs. An anchor or `location.assign()` requests navigation to a URL: it normally loads another document, but a fragment-only navigation can remain in the current document. `history.pushState()` and `replaceState()` instead update the current document's session history and URL without loading another document. Those History API calls do not dispatch `popstate`; Back/Forward traversal does, so an app should read the current URL then and synchronize its displayed state. / `URL` 负责解析和序列化完整地址，`URLSearchParams` 读写查询参数。链接或 `location.assign()` 会请求导航到某个 URL：通常会加载新文档，但仅改变片段时可以留在当前文档。`history.pushState()` 和 `replaceState()` 则在当前文档内更新会话历史和 URL，不会加载新文档。它们本身不会触发 `popstate`；浏览器前进或后退遍历历史记录时才会触发，因此应用应在该事件中读取当前 URL 并同步界面。

##### Parse query state and choose the navigation operation

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

**See also:** [React Router / React 路由](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) uses browser history for client-side routes; [Performance Metrics and Analysis / 性能指标与分析](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) explains `DOMContentLoaded` and `load`; the [archived URL, location, and History reference](../../archive/front-end/0-1_Learning_Notes/Javascript/readme.md) retains the broader property and method catalog.

**Sources checked 2026-10-15:** [WHATWG URL Standard](https://url.spec.whatwg.org/#urlsearchparams-class) (Living Standard updated 2026-10-07) and [WHATWG HTML Standard: History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface) (Living Standard updated 2026-10-14).

---

#### Why does a `<script>` tag block HTML parsing? What do `async` and `defer` change?

**Headline (30s):** A parser-inserted classic script without `async`, `defer`, or another applicable scheduling rule can pause parsing while it is fetched and executed. For classic external scripts, `defer` preserves order and runs after parsing before `DOMContentLoaded`; `async` runs when ready without preserving order. Module scripts are deferred by default unless `async` is present. **中文：** classic `defer` 保序并在解析后执行；`async` 不保序；模块脚本默认延后执行。

**How it works:**

| Attribute | Downloaded | Executed | Blocks parser? | Order preserved? |
|---|---|---|---|---|
| Classic parser-inserted, no attribute | inline or fetched by parser | when parser reaches and can run it | yes | parser order |
| Classic external `defer` | in parallel | after parsing, before `DOMContentLoaded` | no | yes among deferred scripts |
| Classic external `async` | in parallel | when ready | no | no |
| Module script | module graph fetched | deferred by default; `async` changes scheduling | no for normal module scripts | module graph rules apply |

**Gotcha — `defer` applies to classic external scripts:** It has no effect on classic inline scripts; module scripts are deferred by default. Use `async` only when execution order is unimportant.

**See also:** [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for placement strategy and more `<script>` gotchas.

---

#### Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?

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

**See also:** [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for rendering triggers and optimization tactics, [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96).

---

#### How do you optimize the critical rendering path?

**Headline (30s):** Reduce blocking work, let the browser discover critical resources early, and avoid repeated synchronous layout. Validate the result with page-level measurements; `preconnect`, critical CSS, image loading policy, and animation choices all depend on the page and target browsers. **中文：** 优化应从减少阻塞、尽早发现关键资源和避免重复同步布局入手，并用页面测量验证。

**Tactics:**

- **Render-blocking mitigation** — defer scripts whose work is not needed during parsing; critical CSS can reduce a separate blocking request but increases HTML and affects caching; use `content-visibility: auto` only when its rendering semantics fit.
- **Network** — `<link rel="preconnect">` can warm up a connection; use `loading="lazy"` for genuinely off-screen images, not likely LCP images; select image formats and HTTP versions based on target support and measurements.
- **Runtime** — debounce or throttle only when event frequency requires it; use `requestAnimationFrame` for visual updates; profile before preferring `transform`/`opacity` over layout properties.
- **SSR + hydration** — serve HTML first, let client JS attach listeners on top (as in React hydration).
- **Early resource discovery** — some engines use speculative loading while parsing is blocked. This is an implementation optimization, not a page-level guarantee.

**See also:** [`11.1 Performance Metrics and Analysis`](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90), [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96), [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD).

**Standards and implementation notes / 标准与实现资料：** [WHATWG HTML scripting](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element), [Fetch Standard: CORS](https://fetch.spec.whatwg.org/#http-cors-protocol), [CSS Display](https://www.w3.org/TR/css-display-3/), [Chrome RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), [Chrome forced-reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
## 2. HTML and CSS Basics / HTML 与 CSS 基础

**HTML and CSS Basics / HTML 与 CSS 基础**

A compact reference for five CSS foundations that show up constantly in interviews: units, selectors/specificity, responsive techniques, inheritance, and text-overflow tricks. Reach for this when you need to refresh the vocabulary — for mechanism-heavy deep dives, cross-links are at the end of each section.

**中文：** 重点区分单位及其参照、级联优先级、属性继承、文本截断与语义 HTML 的职责边界。

#### CSS Units — which to use when

| Unit | Relative to | Use for | Avoid for |
|---|---|---|---|
| `px` | CSS reference pixels | borders, precise spacing, sizing | treating them as device pixels |
| `%` | property-specific reference, often a containing block | fluid sizing | assuming every percentage uses the parent's width |
| `em` | parent `font-size` (or own, for non-`font-size`) | spacing relative to text | deep nesting (compounds) |
| `rem` | root `font-size` | scalable UIs, most typography | fine-grained per-component control |
| `vw` / `vh` | default (large) viewport size | viewport-relative layout | assuming `100vw` always equals the content box |
| `svh` / `lvh` / `dvh` | small / large / dynamic viewport height | choose based on browser UI behavior | assuming they are interchangeable |
| `vmin` / `vmax` | smaller / larger viewport dim | keeping elements square across orientations | anything that needs a single axis |

Usage notes:

- **`px`** — a CSS reference pixel, not necessarily one physical/device pixel. Page zoom and `devicePixelRatio` affect how CSS pixels map to the output surface; CSS px itself doesn't prevent page zoom.
- **`%`** — its reference depends on the property. For `width`, it is generally based on the containing block's width; percentages in other properties can resolve differently or remain unresolved until layout.
- **`em`** — for most properties, relative to the element's computed font size; in `font-size`, relative to the inherited font size. It compounds when nested font sizes are set in `em`.
- **`rem`** — relative to the root element's font size. Avoid resetting the root to a fixed pixel size when a design should follow user font preferences.
- **`100vw`** — viewport units are based on the viewport, not necessarily the available content box; classic scrollbars and root overflow settings can make a `100vw` child overflow horizontally. Use the containing block's `width: 100%` for ordinary full-width content.
- **`vh`** — the default `vh` maps to the large viewport. On devices with retractable browser UI it can extend behind that UI. `svh` fits the small viewport; `dvh` follows dynamic UI and can resize while scrolling.
- **`vmin` / `vmax`** — `50vmin` always references the smaller dimension, useful for square elements that adapt to orientation.

#### CSS Selectors — specificity and performance

##### Selector specificity

For selector specificity, compare the ID, class/attribute/pseudo-class, and type/pseudo-element columns from left to right. The cascade resolves origin, importance, context, attached styles, and cascade layer before specificity; specificity is not the only priority rule. Inline `style` attributes have a separate precedence step for declarations of the same importance.

For a simple author-style-sheet comparison, the tuple `(id, class, type)` is compared left-to-right: `(1, 0, 0)` > `(0, 2, 0)` even if the second selector has more classes. The universal selector (`*`) and combinators (`>`, `+`, `~`) carry zero specificity. `:not()`, `:is()`, and `:has()` take the specificity of their most specific argument; `:where()` contributes zero.

**Specificity battle example:**

```css
/* Specificity: (1, 1, 0) — wins, because ID weight dominates */
#sidebar .menu-item { color: red; }

/* Specificity: (0, 3, 0) — loses, even with more classes */
.menu .menu-item.active { color: blue; }
```

More classes don't overcome a single ID within the same cascade context. Importance, layer order, and origin can still decide which declaration participates.

**`:not()` detail:** `:not()` itself adds no specificity; its most-specific argument does. `div:not(.sidebar)` is `(0, 1, 1)` (class + element).

##### Performance and maintainability tactics

- **Attribute selectors** — `[data-state="active"]` lets CSS react to JS state without class juggling.
- **BEM** (`.block__element--modifier`) — flat specificity, trivially overridable by a more specific class.
- **Cascade layers (`@layer`)** — organize styles (`@layer reset, components, utilities;`). For normal declarations, later layers win and unlayered author rules outrank layered author rules; for `!important`, layer order reverses. Specificity still matters within the winning layer.
- **CSS-in-JS** (styled-components, Emotion) — often generates classes, but it still participates in the same cascade and specificity rules.
- **Critical CSS** — inlining genuinely critical styles can reduce a render-blocking stylesheet dependency, but it adds bytes to HTML and should be measured against caching and delivery costs.

#### Responsive design beyond media queries

Media queries still work, but modern CSS gives cleaner options for common cases:

- **Container queries** — style based on *container* size, not viewport. Lets a component respond to the space it's given, which is what you usually want inside a grid.

  ```css
  .card { container-type: inline-size; }

  @container (width > 400px) {
    .card { display: grid; grid-template-columns: 1fr 2fr; }
  }
  ```

- **Intrinsic sizing with Grid** — `minmax()` + `auto-fit` reflows without any media queries.

  ```css
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
  ```

- **CSS variables redefined per breakpoint** — the breakpoint lives in one place, and every element reacts to the change automatically.

  ```css
  :root { --columns: 1; --gap: 8px; }

  @media (min-width: 768px) {
    :root { --columns: 2; --gap: 16px; }
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--columns), 1fr);
    gap: var(--gap);
  }
  ```

**See also:** [`2.3 Flex & Grid Layout`](#4.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for the full Grid / Flexbox reference.

#### Semantic HTML and accessibility / 语义化 HTML 与无障碍交互

Choose elements for their meaning and built-in behavior. Use headings to express the page outline, landmarks such as `<main>` and `<nav>` to identify regions, a `<button>` for an action, and an `<a href>` for navigation. Semantic controls provide keyboard and assistive-technology behavior that a styled `<div>` does not provide by default.

Give form controls programmatic labels with `<label for="…">` or a properly nested label. Give informative images useful alternative text; use `alt=""` for decorative images so they do not add noise to the text alternative. Do not use color or visual positioning as the only way to convey a required state or relationship.

Keep the source order meaningful. CSS can change visual placement without changing the underlying document sequence used by nonvisual presentation.

##### Keyboard, focus, and validation feedback / 键盘、焦点与校验反馈

**Core answer / 核心回答：** Start with native HTML controls: a label gives an input its accessible name, and native buttons and fields already support expected focus and keyboard behavior. Keep keyboard focus visible. Describe errors in text, associate the text with its field using `aria-describedby`, and expose the invalid state with `aria-invalid`. ARIA adds meaning for assistive technology; it does not add focusability, keyboard activation, or validation behavior to a generic element. / 优先使用原生 HTML 控件：标签提供输入框的无障碍名称，原生按钮和表单字段自带预期的焦点与键盘行为。键盘焦点应清晰可见。错误要用文字说明，通过 `aria-describedby` 与字段关联，并用 `aria-invalid` 表达错误状态。ARIA 为辅助技术补充语义，但不会让普通元素自动获得焦点、键盘操作或校验行为。

This form keeps native constraints as the no-JavaScript fallback. Once its custom handler is installed, an invalid submission shows a text error, marks the field, and focuses it; the visible outline identifies where the keyboard user landed. The same error text is in the field's accessible description.

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
form.noValidate = true; // use the custom path only after its handler is ready
</script>
```

Without JavaScript, the browser's `required` and `type="email"` constraints remain active. With JavaScript, Tab reaches the field and then the submit button; submitting an invalid value by keyboard returns focus to the field and exposes the associated error. Clear the error as the value becomes valid, and validate again on the server before accepting submitted data. This is a focused interaction pattern, not a conformance claim for an entire page.

#### Inherited CSS properties

Some properties cascade to children by default; most do not. Knowing the short list saves you from reaching for `inherit` unnecessarily.

**Inherited by default:**

- **Font** — `font-family`, `font-size`, `font-style`, `font-weight`, `line-height`
- **Text formatting** — `text-align`, `text-indent`, `text-transform`, `text-shadow`
- **Spacing** — `letter-spacing`, `word-spacing`
- **Visibility** — `visibility`

Most layout / box-model properties (`margin`, `padding`, `border`, `width`, `height`, `display`, `position`) do **not** inherit; they usually apply to the element's own box.

`text-decoration` is not inherited. A decoration drawn by an ancestor can continue across descendant text, which can make it look inherited; changing the child's `text-decoration` does not simply override the ancestor's line.

#### Truncating text with ellipsis

##### Single-line truncation

```css
.box {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100px;
}
```

All three properties are needed: `nowrap` keeps text on one line, `overflow: hidden` hides the spill, `text-overflow: ellipsis` paints the `…`.

##### Multi-line truncation

```css
.box {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  width: 100px;
}
```

This is the legacy `-webkit-line-clamp` form, with the `-webkit-box` display and orientation declarations required by that syntax. CSS Overflow Module Level 4 specifies a `line-clamp` shorthand and also describes the legacy form for compatibility, but remains a Working Draft; check the exact behavior and support in target browsers before choosing a form.

**Specifications / guidance:** [HTML Standard](https://html.spec.whatwg.org/), [CSS Values and Units](https://www.w3.org/TR/css-values/), [CSS Selectors](https://www.w3.org/TR/selectors-4/), [CSS Cascading and Inheritance](https://www.w3.org/TR/css-cascade-5/), [CSS Display and visual ordering](https://www.w3.org/TR/css-display-3/#order-property), [CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/), [CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/), [WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/), [WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/), and [WAI image alternatives](https://www.w3.org/WAI/tutorials/images/).

**Accessibility sources checked 2026-10-15:** [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/) (including visible focus and text error identification), [WAI Forms: Notifications](https://www.w3.org/WAI/tutorials/forms/notifications/), [ARIA Authoring Practices Guide: Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), and [ARIA Authoring Practices Guide: Read Me First](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/) (ARIA 1.2 role and behavior guidance).
## 3. Box Model and BFC / 盒模型与块格式化上下文

**Box Model and BFC / 盒模型与块格式化上下文**

The box model measures each generated box; a block formatting context (BFC) controls specific float and margin interactions. A BFC is not a stacking context or a general rendering-containment boundary. **中文：** 盒模型描述盒子的尺寸；BFC 主要管理浮动和外边距交互，不等于堆叠上下文或通用布局隔离。

Interview questions this note prepares you for:

1. **What is the CSS box model?**
2. **Content-box vs border-box — which should you use, and why?**
3. **What is a Block Formatting Context (BFC), and what triggers one?**
4. **How do you fix vertical margin collapse?**
5. **How do you contain floating children so the parent doesn't collapse?**

#### What is the CSS box model?

**Headline (30s):** Every element is rendered as a rectangular box with four concentric layers — content, padding, border, margin. The content is the innermost rectangle; padding adds space inside the border; the border wraps the padding; the margin is transparent space pushing away other elements.

```text
┌───────── margin ─────────┐
│ ┌────── border ────────┐ │
│ │ ┌── padding ──────┐  │ │
│ │ │ [  content  ]   │  │ │
│ │ └─────────────────┘  │ │
│ └──────────────────────┘ │
└──────────────────────────┘
```

**Padding and margin shorthand** accept 1–4 values, clockwise from top:

| Values | Applies to |
|---|---|
| 1 value | all four sides |
| 2 values | top/bottom, left/right |
| 3 values | top, left/right, bottom |
| 4 values | top, right, bottom, left |

Individual sides can be targeted with `padding-top`, `margin-left`, etc.

**Border shorthand** is `border: <width> <style> <color>`:

```css
.box-a { border: 1px solid black; }
.box-b { border: 3px dashed red; }
```

#### Content-box vs border-box — which should you use?

**Headline (30s):** `content-box` (the CSS default) sets `width` / `height` on the **content only** — padding and border are added *on top*, making the element bigger than declared. `border-box` includes padding and border *inside* the declared size, so a `width: 100px` element is exactly 100px wide regardless of padding. Most modern codebases reset everything to `border-box` because it's the sane default.

| Property | `content-box` (default) | `border-box` |
|---|---|---|
| `width` includes | content only | content + padding + border |
| Result of `width: 100px; padding: 10px; border: 5px;` | 130px actual width | exactly 100px |
| Friendlier for math | no | yes |

**The recommended reset:**

```css
*, *::before, *::after {
  box-sizing: border-box;
}
```

**Example — fitting a box into exactly 100×100:**

```css
.box {
  width: 100px;
  height: 100px;
  padding: 10px;
  border: 5px solid black;
  box-sizing: border-box;
}
```

Under `border-box`, padding and border stay inside the 100×100 footprint. Under `content-box`, the same declaration produces a 130×130 element.

#### What is a Block Formatting Context, and what triggers one?

**Headline (30s):** A Block Formatting Context (BFC) is a flow-layout context with defined interactions with floats and vertical margin collapsing. A BFC root's auto height includes floats in that context, and its child margins do not collapse through its boundary. That does not make it a stacking context, a containing block for every positioned descendant, or a general layout-containment boundary. **中文：** BFC 会约束浮动与子级外边距的流动；它本身不保证堆叠或定位隔离。

**Rules that apply inside a BFC:**

- Block-level boxes stack vertically along the block axis.
- Floats outside a BFC do not intrude into its contents; a BFC root's auto height includes floats contained by that context.
- Vertical margins of adjacent in-flow block siblings can collapse within the BFC. Child margins do not collapse through the BFC root's boundary; the root's own margins can still participate in its parent context.
- A BFC is not, by itself, a containing block for absolutely positioned descendants. Positioned containing blocks have separate rules.
- A BFC does not by itself create a stacking context or contain all layout invalidation.

**How to create a BFC** (any of these on the container):

- `display: flow-root` — explicitly establishes a BFC without clipping content or adding a scroll container.
- A block container with `overflow: hidden`, `auto`, or `scroll` (but not `overflow: clip`); hidden/scrolling overflow has its own clipping or scrolling effects.
- Floats, absolutely positioned boxes, inline blocks, and table cells/captions establish independent formatting contexts for their contents.
- `display: flex` and `display: grid` establish flex/grid formatting contexts, not BFCs. Their items also do not participate in block margin collapsing or allow floats to intrude in the usual way.

**Gotcha — BFC vs. overflow:** `overflow: hidden` can clip content and establish a scroll container. If the goal is only to contain floats and separate child margins, use `display: flow-root`.

#### How do you fix vertical margin collapse?

**Headline (30s):** Positive vertical margins of adjacent block siblings in the same block formatting context collapse to the larger margin, so two `50px` margins produce a `50px` gap. A formatting-context boundary can prevent a child's margin from collapsing through its container; the container's own margins still follow the parent context's rules.

**Before** (margin collapse strikes):

```html
<section>box-one</section>
<section>box-two</section>
```

```css
section { margin: 50px; }
/* The adjacent positive margins collapse to a 50px gap. */
```

**After** (wrap one in a BFC):

```html
<section>box-one</section>
<div class="bfc">
  <section>box-two</section>
</div>
```

```css
section { margin: 50px; }
.bfc { display: flow-root; }
/* The child's top margin stays inside the BFC; the outer gap is 100px. */
```

**Gotcha — parent/first-child collapse:** If a parent has no border, padding, inline content, clearance, or new formatting context, its first child's top margin can collapse through it. A border, padding, or formatting-context boundary separates those margins.

#### How do you contain floating children so the parent doesn't collapse?

**Headline (30s):** Floats are out of normal flow, so a regular block parent with only floated children may have no height from those children. Make the parent a BFC with `display: flow-root`, or use a clearfix where legacy support requires it.

**Before** (parent collapses):

```css
.container { background: red; }
.box { float: left; width: 100px; height: 100px; }
```

The `.container` has no height — it's a red stripe, not a red rectangle around its floats.

**Fix — the modern way (BFC):**

```css
.container { display: flow-root; }
```

**Fix — the legacy clearfix:**

```css
.container::after {
  content: "";
  display: table;
  clear: both;
}
```

Both make the parent's height include the floated children. Prefer `flow-root` when a BFC is the intended behavior.

**See also:** [`2.6 CSS Interview Questions`](#7.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98) for float-clearing patterns and layout interview scenarios.

**Specifications / 规范：** [CSS Display: formatting contexts](https://www.w3.org/TR/css-display-3/), [CSS 2.2: block formatting contexts](https://www.w3.org/TR/CSS22/visuren.html#block-formatting), [CSS 2.2: box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions).
## 4. Flex & Grid Layout / Flex与Grid布局

**Flexbox and Grid Layout / Flexbox 与 Grid 布局**

Reach for this when you need to remember the property names and what each one does. For "how should I approach this layout?" style interview answers, the patterns live in [`2.6 CSS Interview Questions`](#7.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98).

**中文：** Flexbox 适合单轴排列，Grid 适合二维轨道；遇到内容最小尺寸造成溢出时，可显式使用 `min-width: 0` 或 `minmax(0, 1fr)`。

Rule of thumb: **Flexbox for 1D** (rows *or* columns), **Grid for 2D** (rows *and* columns). In practice they compose — a grid item can itself be a flex container.

#### Flexbox

`display: flex` (or `inline-flex`) turns an element into a **flex container**; its direct children become **flex items**. Flex items are laid out along a *main axis* (controlled by `flex-direction`) and a perpendicular *cross axis*.

##### Container properties

| Property | What it controls | Values |
|---|---|---|
| `display` | declare flex container | `flex`, `inline-flex` |
| `flex-direction` | main-axis direction | `row` (default), `row-reverse`, `column`, `column-reverse` |
| `flex-wrap` | allow items to wrap | `nowrap` (default), `wrap`, `wrap-reverse` |
| `justify-content` | main-axis alignment | `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `space-evenly` |
| `align-items` | cross-axis alignment (per line) | `flex-start`, `flex-end`, `center`, `baseline`, `stretch` |
| `align-content` | cross-axis alignment among lines in a multi-line container | `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `stretch` |
| `gap` | spacing between items | any length |

In a `wrap` or `wrap-reverse` container, `align-content` aligns flex lines when there is extra cross-axis space; it can have an effect even when the items currently form just one line. A `nowrap` container is single-line, so `align-content` has no effect.

##### Item properties

| Property | What it controls |
|---|---|
| `flex-grow` | share of *extra* space (unitless proportion) |
| `flex-shrink` | share of *deficit* space when items don't fit |
| `flex-basis` | starting size before grow/shrink (length or `auto`) |
| `flex` | shorthand: `flex: <grow> <shrink> <basis>` |
| `align-self` | override `align-items` for one item |
| `order` | change an item's visual placement order (without changing source order) |

##### Common flexbox patterns

**Perfect centering:**

```css
.container {
  display: flex;
  justify-content: center;  /* horizontal */
  align-items: center;      /* vertical */
  height: 200px;
}
```

**Nav bar spacing:**

```css
.nav { display: flex; justify-content: space-between; }
```

**Equal-height columns** — with the default `align-items: stretch`, row items whose cross size is `auto` and whose cross-axis margins are not `auto` stretch to their line's cross size. Min/max constraints can limit that stretch, so this is not a guarantee for every item.

##### Intrinsic minimum sizes

Flex items and grid tracks can keep their content-based minimum size, so a long word, URL, or wide table may force overflow instead of shrinking. For a flex item that should be allowed to shrink below its min-content width, use `min-width: 0`; in a column flex layout, the corresponding block-axis fix is often `min-height: 0`.

```css
.row { display: flex; }
.main { flex: 1; min-width: 0; }
.main img { max-width: 100%; }
```

This changes the item's minimum constraint; it does not guarantee that all of its descendants will wrap or fit, so give overflowing content its own policy.

#### CSS Grid

`display: grid` (or `inline-grid`) creates a **grid container**. Grids have explicit **tracks** (rows and columns), **lines** (between tracks), **cells** (single row × column), and **areas** (named regions spanning multiple cells).

##### Container properties

| Property | What it controls |
|---|---|
| `display` | declare grid container (`grid`, `inline-grid`) |
| `grid-template-columns` | column track sizes |
| `grid-template-rows` | row track sizes |
| `grid-template-areas` | named areas laid out as ASCII art |
| `gap` / `row-gap` / `column-gap` | spacing between tracks |
| `justify-items` / `align-items` / `place-items` | how items align *within* their cells |
| `justify-content` / `align-content` / `place-content` | how the grid itself sits *within* the container |

Track sizes can be fixed (`100px`), flexible (`1fr`), or content-based (`auto`, `min-content`, `max-content`). `minmax(min, max)` sets a track's lower and upper sizing functions, for example `minmax(200px, 1fr)`; `repeat(auto-fit, minmax(200px, 1fr))` combines that range with automatic repetition.

An `fr` track with an automatic minimum can still be held open by its items' min-content contribution. If the track must shrink below that content width, make its minimum explicit, commonly `minmax(0, 1fr)`, and decide how the item content should wrap or overflow.

```css
.content-first-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 16rem;
}

.content-first-grid > main { min-width: 0; }
```

##### Item properties

| Property | What it controls |
|---|---|
| `grid-column-start` / `grid-column-end` | column span |
| `grid-row-start` / `grid-row-end` | row span |
| `grid-column` / `grid-row` | shorthand (`grid-column: 1 / 3`) |
| `grid-area` | name this item, or shorthand for all four line values |
| `justify-self` / `align-self` | override cell alignment for one item |

##### Common grid patterns

**Three-column layout with fixed sides:**

```css
.layout {
  display: grid;
  grid-template-columns: 100px 1fr 100px;
  gap: 10px;
}
```

**Responsive card grid (no media queries):**

```css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr));
  gap: 16px;
}
```

The minimum is capped at the container width so the track can still fit on a narrow container.

**Named template areas:**

```css
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
```

#### When to reach for which

- **Flexbox** — nav bars, toolbars, button groups, anything that's a line of stuff that might wrap.
- **Grid** — page-level layouts, card grids, forms with aligned labels/inputs, anything 2D.
- **Both together** — Grid for the page structure, Flexbox inside each cell for horizontal clusters.

Keep meaningful source order in the HTML. Flex `order`, reverse directions, and grid placement change visual layout without rewriting the document's logical/speech order; don't use them to repair incorrect content order.

**See also:** [`2.1 HTML & CSS Basics`](#2.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for CSS units used with `fr`/`minmax`, [`2.6 CSS Interview Questions`](#7.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98) for worked interview examples using these layouts.

**Specifications / 规范：** [CSS Flexible Box Layout](https://www.w3.org/TR/css-flexbox-1/) defines flex sizing and the automatic minimum size; [CSS Grid Layout](https://www.w3.org/TR/css-grid-2/) defines track sizing and grid-item minimums; [CSS Display](https://www.w3.org/TR/css-display-3/#order-property) describes visual reordering and accessibility.
## 5. Browser HTML and CSS / 浏览器中的 HTML 与 CSS

**Browser HTML and CSS / 浏览器中的 HTML 与 CSS**

Layout, paint, and compositing describe common rendering work, not fixed performance guarantees. `async`, `defer`, and module scripts have distinct scheduling rules. **中文：** 布局、绘制和合成是常见实现阶段，不是固定成本保证；脚本属性的执行时序需按类型区分。

### Reflow, Repaint, and the `<script>` Tag

Interview questions this note answers:

1. **Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?**
2. **How do you minimize the cost of reflow?**
3. **What does `<script>` do in HTML, and how do `async` and `defer` change its behavior?**
4. **Where should you place `<script>` tags, and why?**

For the big-picture render pipeline these topics fit into, see [`1.1 Browser Basics`](#1.%20Browser%20Basics%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9F%BA%E7%A1%80).

---

#### Reflow vs. repaint vs. composite — what triggers each?

**Headline (30s):** Layout recomputes geometry; paint updates visual output; compositing combines content for presentation. A change may require one stage or several. The affected area, thread, layer, and GPU use depend on the page and engine, so the stage names are not a universal cost ranking.

**Typical invalidation paths:**

| Stage pattern | Examples | Boundary |
|---|---|---|
| Style + layout + paint + presentation | Changes affecting geometry or line wrapping, such as many width or font changes | Can affect related boxes; extent depends on layout and engine |
| Style + paint + presentation | Visual changes that do not affect geometry, such as many color changes | Layout may be reused |
| Style + compositor update | Some `transform` / `opacity` changes on an element suitable for compositing | May avoid layout and paint; layer setup and GPU use are not guaranteed |

##### What triggers reflow

- Window resize.
- Adding, removing, or reordering DOM nodes.
- Changes to layout-affecting styles: `width`, `height`, `margin`, `padding`, `border`, `display`, `position`, `font-*`, `line-height`, `text-align`.
- **Reading** geometry properties (`offsetHeight`, `getBoundingClientRect`) after a write can force pending style/layout work synchronously. `scrollTop` is a scroll position, not a geometry measurement.

##### What triggers repaint (without reflow)

- `color`, `background`, `background-color`, `background-image`
- `visibility` (going between `visible` and `hidden`)
- `box-shadow`, `outline`, `border-color` (but not `border-width`, which changes layout)

##### Compositor-friendly properties (conditional)

- `transform` and `opacity` can be good candidates for visual animation when a trace shows layout or paint is the bottleneck.
- `filter`, `will-change`, and other properties have property- and engine-specific effects; none guarantees compositor-only work.

**Gotcha — avoid a promised “GPU path”:** `transform` can avoid layout in common cases, but may still require paint, layer setup, or other work. Compare traces on target browsers and devices.

#### How do you minimize the cost of reflow?

**Headline (30s):** Reduce unnecessary DOM work, group geometry reads before writes when that fits the task, and profile forced synchronous layout. A BFC manages float and margin interactions; it is not a layout-containment guarantee. CSS containment has distinct behavior and should be applied intentionally.

**Tactics:**

- **Group writes.** A class change or a series of style writes may be batched by the browser; it does not guarantee exactly one layout.
- **Avoid interleaving writes and geometry reads.** A `DocumentFragment` can clarify subtree construction, but is not automatically faster than direct DOM operations.
- **Use containment only for a real boundary.** See [Block Formatting Context](#3.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) for float and margin behavior; do not treat it as CSS layout containment.
- **Debounce or throttle** `resize` / `scroll` handlers — see [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96).
- **Schedule visual updates deliberately.** CSS animations and `requestAnimationFrame` can align visual work with rendering; neither makes expensive work free.
- **Avoid repeated forced layout.** Do not read a geometry property after every write in a loop; the browser may have to flush pending layout each time.

```javascript
// may repeatedly force pending style/layout work
for (const el of items) {
  el.style.width = el.offsetWidth + 10 + 'px';
}

// collect measurements before writing
const widths = items.map(el => el.offsetWidth);
items.forEach((el, i) => { el.style.width = widths[i] + 10 + 'px'; });
```

**Gotcha — hidden styles have different semantics:** `display: none` generates no box; `visibility: hidden` keeps layout space. Their rendering and accessibility effects differ, so choose by behavior rather than a universal cost claim.

#### What does the `<script>` tag do?

**Headline (30s):** A parser-inserted classic script without `async`, `defer`, or another applicable scheduling rule can pause parsing while it is fetched and executed. The parser must account for scripts that can affect the document as parsing continues.

**Inline:**

```html
<script>
  // JavaScript here
</script>
```

**External:**

```html
<script src="path/to/script.js"></script>
```

#### `async` vs. `defer` — which to use when?

**Headline (30s):** For classic external scripts, `defer` fetches in parallel and executes after parsing in document order; `async` fetches in parallel and executes when ready without preserving order. Module scripts are deferred by default. Choose based on dependencies and when the script must run.

| Attribute | Downloads | Executes | Blocks parser? | Preserves order? |
|---|---|---|---|---|
| Classic parser-inserted, no attribute | inline or fetched by parser | when parser reaches and can run it | yes | parser order |
| Classic external `defer` | in parallel | after parsing, before `DOMContentLoaded` | no | yes among deferred scripts |
| Classic external `async` | in parallel | when ready | no | no |
| Module script | module graph fetched | deferred by default; `async` changes scheduling | no for normal module scripts | module graph rules apply |

**Gotcha — `defer` applies to classic external scripts:** It has no effect on classic inline scripts; module scripts are deferred by default. Use `async` only when execution order is unimportant.

**Gotcha — `defer` doesn't work on inline scripts:** `defer` is ignored if the `<script>` has no `src`. Move the code into an external file or use `DOMContentLoaded`.

#### Where should you place `<script>` tags?

**Headline (30s):** Choose placement and attributes from the script's dependencies. An external classic `defer` script in `<head>` can fetch while parsing and run after parsing; a module script is deferred by default. There is no single best placement for every script.

**Common choices:**

1. `<head>` with classic external `defer` — download in parallel, execute after parsing in document order.
2. `<head>` with `async` — useful when order does not matter; executes when ready.
3. A script near `</body>` — parsing has reached that point, though earlier styles or scripts may still affect readiness.
4. A parser-inserted classic script without an attribute — can block the parser while fetching and running.

**Best practices beyond placement:**

- Keep JS in external files (cacheable, easier to maintain).
- Minify and compress in production.
- Use non-blocking loading (`defer` / `async`) whenever possible.

**See also:** [`1.1 Browser Basics`](#1.%20Browser%20Basics%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9F%BA%E7%A1%80) for the high-level pipeline, [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for animation and scroll optimization.

**Standards and implementation notes / 标准与实现资料：** [WHATWG HTML scripting](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element), [CSS Display](https://www.w3.org/TR/css-display-3/), [Chrome RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), [Chrome forced-reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
## 6. DOM Properties / DOM属性

**DOM Geometry Properties / DOM 几何属性**

These APIs expose different CSSOM measurements. Their values use CSS pixels, but their box, coordinate space, fragment handling, and transform behavior differ. A read may force pending style/layout work to finish; it does not necessarily do so when layout is already current. **中文：** 读取几何值可能同步完成尚未刷新的布局，但不意味着每次读取都会重新布局。

#### Quick comparison

```text
┌─────────────────────────── margin ───────────────┐
│ ┌───────────────────── border ────────────────┐  │
│ │ ┌────────────── padding ────────────────┐   │  │
│ │ │ ┌────────── content ────────────────┐ │   │  │
│ │ │ │                                   │ │   │  │
│ │ │ │                                   │ │   │  │
│ │ │ └───────────────────────────────────┘ │   │  │
│ │ └───────────────────────────────────────┘   │  │
│ └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘

offsetHeight  = border-box measurement, including scrollbar — integer CSS px, ignores transforms
clientHeight  = padding box minus rendered scrollbar        — integer CSS px
scrollHeight  = scrolling area                              — integer CSS px, includes overflow
```

| Property | Includes | Excludes | Writable? |
|---|---|---|---|
| `offsetHeight` / `offsetWidth` | border box; normally includes a rendered scrollbar | margin | no |
| `clientHeight` / `clientWidth` | padding box, excluding a rendered scrollbar | border, scrollbar, margin | no |
| `scrollHeight` / `scrollWidth` | scrolling area, including overflowed content and contributing generated content | border; generally not the scrollbar | no |
| `scrollTop` / `scrollLeft` | current scroll offset | — | **yes** |
| `offsetTop` / `offsetLeft` | offset from the `offsetParent` padding edge to the element's border edge | — | no |
| `getBoundingClientRect()` → `.width` / `.height` | viewport-relative union of transformed border-box fragments | margin | no |

#### `offsetHeight` / `offsetWidth`

Returns an integer CSS-pixel measure of the border-box fragments, ignoring CSS transforms. A rendered scrollbar is included in the familiar layout-box measurement; margin is excluded. It can be zero when the element has no associated box.

```text
offsetHeight ≈ content height + padding + border (+ rendered scrollbar)
```

#### `clientHeight` / `clientWidth`

Returns an integer CSS-pixel measure of the padding edge, excluding a scrollbar rendered between the padding and border edges. Border and margin are excluded. Root-element behavior maps to the viewport in standards mode.

```text
clientHeight ≈ content height + padding - rendered scrollbar
```

#### `scrollHeight` / `scrollWidth`

Returns the integer CSS-pixel height of the scrolling area, which covers content beyond the visible client area. It may differ from `clientHeight` because of overflow; it is not simply a count of text or a guarantee that overflow is user-scrollable. In standards mode, the root element returns `max(viewport scrolling-area height, viewport height)`, not the viewport's visible height.

```text
ordinary element: scrolling-area height (includes overflow beyond the client area)
root element in standards mode: max(viewport scrolling-area height, viewport height)
```

#### `scrollTop` / `scrollLeft`

Current scroll offset in CSS pixels. **Writable** — set it to control scroll programmatically. Values can be fractional or outside the usual range in some layouts (for example, reverse-direction scrolling or elastic overscroll).

```javascript
const el = document.getElementById('container');
console.log(el.scrollTop);
el.scrollTop = 0;  // scroll to top
```

#### `offsetTop` / `offsetLeft`

`offsetTop` / `offsetLeft` measure from the element's border edge to its `offsetParent`'s padding edge. `offsetParent` is not simply the nearest positioned ancestor: tables, containing blocks, fixed positioning, zoom, shadow-tree boundaries, and elements without boxes affect the result. If there is no `offsetParent`, offsets are relative to the initial containing block; some elements such as `body` return zero.

#### `getBoundingClientRect()`

Returns a `DOMRect` for the smallest rectangle enclosing the element's non-empty client rects, **relative to the viewport**. It includes CSS transforms and may differ from offset dimensions; a fragmented inline can have multiple client rects while this method returns their union. The returned object is a snapshot, not a live object.

```javascript
const rect = element.getBoundingClientRect();
// rect.top     - distance from viewport top to element top
// rect.bottom  - distance from viewport top to element bottom
// rect.left    - distance from viewport left to element left
// rect.right   - distance from viewport left to element right
// rect.width   - union width in CSS pixels, including border and transforms
// rect.height  - union height in CSS pixels, including border and transforms
```

**Common pattern — checking if an element is in the viewport:**

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

This is a simple rectangle-overlap check, not a test for occlusion, opacity, or assistive-technology visibility. Zero-area boxes need a separate policy.

For threshold-based visibility tracking (e.g., lazy loading, analytics), prefer `IntersectionObserver` over repeatedly polling geometry. It reports asynchronously; it is not a guarantee that the browser performs no layout work. See [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD).

#### When to reach for which

- Need an **untransformed integer layout-box size**? → `offsetHeight` / `offsetWidth`.
- Need a **viewport-relative transformed rectangle**? → `getBoundingClientRect()`.
- Need **inner content area** (for sizing children)? → `clientHeight` / `clientWidth`.
- Need to know if **overflow exists**? → compare `scrollHeight > clientHeight`.
- Need **current scroll position**, or to **scroll programmatically**? → `scrollTop` / `scrollLeft`.
- Need **viewport-relative position** (for tooltips, drag, scroll effects)? → `getBoundingClientRect()`.
- Need **position within parent** (for layout math)? → `offsetTop` / `offsetLeft` (watch out: relative to `offsetParent`, not necessarily the direct parent).

**See also:** [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) on layout thrashing when reads follow writes, [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for `IntersectionObserver`-based visibility.

**Specifications / 规范：** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines these geometry APIs, including the [root `scrollHeight` rule](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight); [Intersection Observer](https://www.w3.org/TR/intersection-observer/) defines asynchronous intersection notifications.
## 7. CSS Interview Questions / CSS面试题

**CSS Interview Questions / CSS 面试题**

### How do you clear floats, and why do you need to?

**Headline (30s):** A BFC root's auto height includes its floats; `display: flow-root` is the direct modern choice. A clearfix is a legacy alternative. **中文：** 让父级建立 BFC（通常用 `flow-root`）即可包含浮动子项。

#### Methods of clearing floats — pure CSS

##### Pseudo-element method (legacy clearfix)

Use a CSS pseudo-element so you don't need extra markup.

```css
.parent::after {
  content: "";
  display: table;
  clear: both;
}
```

**Pros:** Keeps HTML clean. Well supported.
**Cons:** One more indirection than `flow-root`; not needed in modern code.

##### Block Formatting Context — the modern way

Set a BFC-triggering property on the parent so it contains its floats.

```css
.parent {
  display: flow-root; /* establishes a BFC without clipping or scrolling */
}

/* Legacy alternative */
.parent {
  overflow: hidden;
}
```

**Pros:** One line, no pseudo-element, clean semantics.
**Cons:** `overflow: hidden` clips content that extends past the parent — use `flow-root` when clipping isn't wanted.

#### Clearing element — extra HTML

The legacy fallback: insert a clearing `<div>` at the end.

```html
<div class="parent">
  <div class="child">Content</div>
  <div class="child">Content</div>
  <div class="clearfix"></div>
</div>
```

```css
.clearfix {
  clear: both;
}
```

**Pros:** Works everywhere.
**Cons:** Extra non-semantic markup. Don't use in new code.

**Gotcha — why floats even need clearing:** Floats are taken out of normal flow for surrounding inline content, but text still flows around them. A normal-flow parent can therefore fail to include their height. Flexbox and Grid are usually simpler for page layout.

**See also:** [`2.2 Box Model and BFC`](#3.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) on how BFCs contain floats, [`2.3 Flex & Grid Layout`](#4.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for modern alternatives.

---

### How do you build a three-column layout with fixed sides and a fluid middle?

**Headline (30s):** Use Grid (`100px minmax(0, 1fr) 100px`) when the columns are a page/grid structure, or Flexbox when they form a row of items. Float/table/absolute techniques are useful to recognize in legacy code. **中文：** 新布局优先考虑 Grid 或 Flex，并确认中间列是否需要突破内容最小宽度。

The layout includes two fixed-width divs on the sides (`left` and `right`) and a dynamically adjusting center div (`center`).

#### HTML structure

```html
<div class="parent">
  <div class="left">Left</div>
  <div class="center">Center</div>
  <div class="right">Right</div>
</div>
```

#### CSS resets

Consistent styling across browsers begins with CSS resets:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

div {
  height: 100px;  /* visualization only */
}

.parent {
  width: 100%;
}

.left, .right {
  width: 100px;
}

.left   { background-color: lightblue; }
.center { background-color: lightgreen; }
```

#### Float-based layout

```css
.left  { float: left; }
.right { float: right; }

.center {
  width: calc(100% - 200px);
  margin: 0 100px;
}
```

Or with a clearing BFC:

```css
.parent { overflow: hidden; } /* creates a BFC */

.left   { float: left; }
.right  { float: right; }
.center { float: left; width: calc(100% - 200px); }
```

**Pros:** Broad compatibility with older browsers.
**Cons:** Needs `clear` fixes; brittle.

#### Table display layout

```css
.parent { display: table; }
.left, .center, .right { display: table-cell; }
```

**Pros:** Stable and predictable rendering.
**Cons:** Table layout couples sizing across cells in a column, which can be harder to tune in a responsive content layout than Flexbox or Grid. `display: table` changes visual formatting only; it does not make the `<div>` elements semantic table markup.

#### Absolute positioning layout

```css
.parent { position: relative; }

.left  { position: absolute; left: 0; }
.right { position: absolute; right: 0; }

.center {
  margin: 0 100px;
  width: calc(100% - 200px);
}
```

**Pros:** Complete positional control.
**Cons:** Elements leave the normal flow; parent can collapse; responsiveness is harder.

#### Flexbox layout

```css
.parent { display: flex; }
.left, .right { flex: 0 0 100px; }
.center { flex: 1; min-width: 0; }
```

**Pros:** Modern, responsive, minimal code.
**Cons:** Only a concern for very old-browser support.

#### Grid layout

```css
.parent {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) 100px;
}
```

**Pros:** Cleanest, intention-revealing.
**Cons:** Not supported in truly ancient browsers.

**Gotcha — `calc(100% - 200px)` + `box-sizing: content-box`:** If `.parent` has padding and you're using content-box, `100%` doesn't mean what you think. Always normalize with `box-sizing: border-box`.

**See also:** [`2.3 Flex & Grid Layout`](#4.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for the property reference.

If the center content must wrap or scroll instead of setting a minimum width, specify that policy on the item (for example, `overflow-wrap: anywhere` for long URLs). Flex/grid intrinsic minimum sizing can otherwise keep the middle track wider than its available space.

---

### How do you build a two-column layout with one fixed and one responsive side?

**Headline (30s):** Use Flexbox (`flex: 1` on the fluid side) or Grid (`200px minmax(0, 1fr)`) for modern code; legacy methods need more width and overflow care. **中文：** 先选 Flex 或 Grid，再决定内容过长时是否换行、裁切或滚动。

```html
<div class="container">
  <div class="left-side">Fixed width</div>
  <div class="right-side">Responsive width</div>
</div>
```

```css
.container {
  width: 100%;
  height: 200px; /* visualization */
}

.left-side  { width: 200px; background-color: lightblue; }
.right-side { background-color: lightgreen; }
```

#### Strict responsive solutions (reflow with viewport)

**Flexbox:**

```css
.container  { display: flex; }
.left-side  { flex: 0 0 200px; }
.right-side { flex: 1; min-width: 0; }
```

**Grid:**

```css
.container {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
}
```

**Table:**

```css
.container  { display: table; width: 100%; }
.left-side,
.right-side { display: table-cell; }
```

#### Non-strict solutions (need `calc` or manual math)

**Float:**

```css
.left-side { float: left; }
.right-side {
  margin-left: 200px;
  width: calc(100% - 200px);
}
```

Or with both floated:

```css
.container  { overflow: hidden; }
.left-side  { float: left; width: 200px; }
.right-side { float: left; width: calc(100% - 200px); }
```

**Absolute positioning:**

```css
.container  { position: relative; }
.left-side  { position: absolute; left: 0; }
.right-side {
  margin-left: 200px;
  width: calc(100% - 200px);
}
```

**Inline-block:**

```css
.container  { font-size: 0; /* eat whitespace between inline-blocks */ }
.left-side,
.right-side { display: inline-block; vertical-align: top; font-size: 1rem; }
.right-side { width: calc(100% - 200px); }
```

**Gotcha — the whitespace between inline-blocks:** Browsers render whitespace (including newlines) between inline-block elements as a space character, which shifts your layout. `font-size: 0` on the parent is the classic workaround; restore a nonzero font size on the children so their labels remain visible. Flexbox and Grid have no such quirk.

---

### How do you center an element in CSS?

**Headline (30s):** Put `place-items: center` on a Grid container, or use `justify-content` and `align-items` on a Flex container. Absolute positioning with a translate works when you need a positioned overlay. **中文：** Flex/Grid 居中时，布局声明应放在父容器上。

```html
<div class="container">
  <div class="center-item">Centered content</div>
</div>

<style>
  .container {
    width: 300px;
    height: 300px;
    border: 1px solid black;
  }
</style>
```

#### Centering with dynamic dimensions (element size unknown)

The layout properties go on the container; the item remains a normal child.

**Flexbox (preferred):**

```css
.container {
  display: flex;
  justify-content: center;
  align-items: center;
}
```

**CSS Grid:**

```css
.container {
  display: grid;
  place-items: center;
}
```

**Absolute + transform:**

```css
.container { position: relative; }

.center-item {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**Table-cell:**

```css
.container   { display: table; }
.center-item {
  display: table-cell;
  vertical-align: middle;
  text-align: center;
}
```

#### Centering with fixed dimensions

**Absolute + negative margin:**

```css
.container { position: relative; }

.center-item {
  position: absolute;
  width: 200px;
  height: 100px;
  top: 50%;
  left: 50%;
  margin-top: -50px;   /* half of height */
  margin-left: -100px; /* half of width */
}
```

**Absolute + auto margins:**

```css
.container { position: relative; }

.center-item {
  position: absolute;
  width: 200px;
  height: 100px;
  top: 0; right: 0; bottom: 0; left: 0;
  margin: auto;
}
```

With definite width and height, setting all four insets to `0` and `margin: auto` distributes the remaining space and centers the item. This is still an out-of-flow solution: the item does not size the container.

**Gotcha — `transform: translate(-50%, -50%)` on a percentage parent:** `transform` uses the element's *own* size, so this centers correctly even when the element's size is unknown. The negative-margin trick only works if you know the exact dimensions ahead of time.

---

### How do you draw a triangle with pure CSS?

**Headline (30s):** Give a zero-size element thick borders, make three transparent, and color the fourth; the colored border forms a triangle. **中文：** 零尺寸盒子的彩色边框可以组成小三角形。

The shape needs no image asset, and its border color can be changed in CSS.

```html
<div class="triangle"></div>
```

```css
.triangle {
  width: 0;
  height: 0;
  border: 10px solid transparent;
  border-left: 10px solid red; /* points right */
}
```

**How it works:**

- A 20×20 border box made of borders only (the content box is zero size).
- Four borders meet at 45° diagonals. Three transparent borders + one colored = a triangle pointing in the direction opposite the colored side.

**Customization:**

- `border-bottom` solid → triangle points **up**.
- `border-top` solid → triangle points **down**.
- `border-left` solid → triangle points **right**.
- `border-right` solid → triangle points **left**.

**Gotcha — alternative:** `clip-path: polygon(50% 0, 100% 100%, 0 100%)` can express a scalable triangle. Choose based on the shape and its sizing needs.

---

### How do you render a crisp 1px line on Retina / high-DPR screens?

**Headline (30s):** A CSS pixel is not a device pixel. A `1px` border remains one CSS pixel and may cover multiple device pixels; a half-pixel technique can target one device pixel at a particular scale, but alignment and zoom affect rasterization. **中文：** 不同 DPR 下 CSS 像素映射到设备像素不同，不能保证某种写法处处是一条物理像素线。

#### Using a pseudo-element + transform

```css
.box { position: relative; }

.box::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 100%;
}
```

At an effective 2× device-pixel ratio and 1:1 CSS scaling, this makes the painted thickness 0.5 CSS px (nominally one device px). Test the actual device/zoom: subpixel position and scaling can still spread the paint across device pixels.

#### Handling borders with `border-radius`

When the element has `border-radius`, a scaled pseudo-element may not follow the corner shape. A fractional shadow is another option to test:

```css
.box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

Fractional `box-shadow` or border widths are not a cross-device guarantee of a crisp physical-pixel line; their rasterization depends on scale and alignment.

**Gotcha — device ratio and zoom:** A 1 CSS px stroke may cover roughly one device pixel at 1×, two at 2×, or three at 3× before accounting for page zoom and OS scaling. SVG is useful for scalable geometry, but it also rasterizes onto device pixels; it does not promise a one-device-pixel stroke.

---

### How do you prevent the 300ms tap delay on mobile?

**Headline (30s):** The historical delay is not a universal behavior. An optimized mobile viewport avoids Chrome's documented delay condition; on a specific control, `touch-action: manipulation` allows panning/pinch zoom while excluding double-tap gestures. **中文：** 先检查移动 viewport；只有需要控制手势时才设置 `touch-action`。

Some mobile browsers historically delayed click dispatch while waiting to distinguish a tap from a double-tap zoom gesture. Modern engines commonly avoid that wait in responsive-viewport cases, but behavior depends on the browser, viewport, and input target; do not assume every mobile click has a fixed 300 ms delay.

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

The viewport declaration sets the layout viewport to the device width. It does not disable pinch zoom, and authors should not disable user zoom to remove a historical delay. Chrome currently documents a possible delay of up to 300 ms when the initial viewport is not optimized for mobile.

For an interactive region where the desired policy is to allow panning and pinch zoom but not double-tap zoom, Pointer Events defines `touch-action: manipulation`:

```css
button,
[role="button"] {
  touch-action: manipulation;
}
```

**Gotcha — synthetic clicks:** A legacy tap library that dispatches its own click can conflict with the browser's native click. Avoid adding one unless a tested target still requires it; do not pair touch-end activation with a second click activation.

**Specifications / references:** [CSS Display](https://www.w3.org/TR/css-display-3/#the-display-properties) defines the separation between visual formatting and document semantics; [CSS 2.2 tables](https://www.w3.org/TR/CSS22/tables.html) and [CSS 2.1 floats](https://www.w3.org/TR/CSS22/visuren.html#floats) cover the legacy layout mechanisms; [CSS Flexbox](https://www.w3.org/TR/css-flexbox-1/) and [CSS Grid](https://www.w3.org/TR/css-grid-2/) define the modern layout examples; [CSS Values and Units](https://www.w3.org/TR/css-values/) defines CSS pixels and viewport units; [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines `devicePixelRatio`; [Pointer Events](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property) defines `touch-action`; [Chrome's mobile viewport guidance](https://developer.chrome.com/docs/performance/insights/viewport) describes its current tap-delay condition.
## 8. CSS Position, Display, and Animations / CSS定位、显示与动画

**CSS Position, Display, and Animations / CSS 定位、显示与动画**

Positioning, stacking contexts, visibility, and compositing answer different questions. A containing block controls coordinates; a stacking context controls paint ordering; a BFC controls flow interactions. **中文：** 定位坐标、堆叠顺序、可见性和格式化上下文不可混为一谈。

### How do the CSS `position` values differ?

**Headline (30s):** `static` and `relative` stay in flow; `absolute` and `fixed` are out of flow; `sticky` stays in flow and is offset relative to a scrollport while scrolling. Absolute/fixed containing blocks are established by specific ancestor properties, not only by `position`. **中文：** sticky 保持在文档流中；absolute/fixed 的定位包含块也可能由 transform 或 containment 等属性建立。

| Value | In flow? | Positioned relative to | Scrolls with page? |
|---|---|---|---|
| `static` (default) | yes | — (offsets ignored) | yes |
| `relative` | yes (original space reserved) | its original position | yes |
| `absolute` | no | nearest ancestor establishing its absolute-position containing block | follows that containing block |
| `fixed` | no | nearest fixed-position containing block, usually the viewport | fixed to that containing block |
| `sticky` | yes | nearest scrollport in the relevant axis, constrained by its containing block | yes; its visual offset changes while sticking |

#### `static` (default)

Element flows normally in document order. `top`, `right`, `bottom`, `left`, and `z-index` have no effect.

```css
.box { position: static; }
```

#### `relative`

Element stays in normal flow; space is reserved as if it were not positioned. Offset properties shift it *visually* without affecting sibling layout. Also establishes a positioning context for absolutely positioned descendants.

```css
.box { position: relative; top: 10px; left: 20px; }
```

#### `absolute`

Element removed from normal flow — no space reserved. Its containing block is established by the nearest qualifying ancestor; a non-static `position` value is common, and properties such as `transform` or `contain` can also establish one. Without such an ancestor, the initial containing block is used.

```css
.parent { position: relative; } /* creates positioning context */
.child  { position: absolute; top: 0; right: 0; }
```

#### `fixed`

Removed from normal flow; positioned relative to a fixed-position containing block, usually the viewport. It stays fixed as the document scrolls only when that viewport is the containing block.

```css
.navbar { position: fixed; top: 0; left: 0; right: 0; }
```

**Gotcha — fixed descendants:** Properties including `transform`, `perspective`, `filter`, and some `contain` / `will-change` values can establish a fixed-position containing block. A fixed descendant may then move with that ancestor instead of the viewport.

#### `sticky`

Element remains in normal flow. In an axis where a non-`auto` inset is specified, it is offset relative to the nearest scrollport as scrolling would move it past the sticky view rectangle, subject to its containing block.

```css
.header { position: sticky; top: 0; }
```

**Gotcha — overflow ancestors:** An ancestor with `overflow: hidden`, `auto`, or `scroll` can become the nearest scroll container even when it does not visibly scroll. Sticky positioning then uses that ancestor's scrollport; it may not respond to the page's scroll as expected. Inspect the scroll-container chain and the sticky element's containing block.

#### Stacking context and `z-index`

`z-index` affects stacking order within stacking contexts. Positioned elements with a non-`auto` `z-index` create a stacking context; fixed and sticky boxes create one even with `z-index: auto`. Other triggers include `opacity` below `1`, transforms, filters, `isolation: isolate`, and some containment or `will-change` values.

```css
.layer-a { position: relative; z-index: 1; }
.layer-b { position: relative; z-index: 2; } /* above layer-a */
```

**Gotcha — "my `z-index: 9999` isn't on top":** A stacking context is an isolation boundary. A descendant's `z-index` can never escape to compete with elements outside its context — no matter how high the value. If `.modal` sits inside a parent with `transform: translateZ(0)`, any `z-index` on the modal only competes with *siblings inside that parent*. To fix, raise the `z-index` (or create a stacking context) on an ancestor shared with the element you're trying to overlap.

---

### When should you use `display: none` vs `visibility: hidden` vs `opacity: 0`?

**Headline (30s):** `display: none` generates no box; `visibility: hidden` keeps layout space but hides the element; `opacity: 0` makes it transparent while it remains in layout and can still receive focus and pointer input. Their accessibility effects differ too. **中文：** 视觉隐藏不一定等于从交互或无障碍树中移除。

| Aspect | `display: none` | `visibility: hidden` | `opacity: 0` |
|---|---|---|---|
| **Space in layout** | removed | reserved | reserved |
| **Receives clicks / events** | no | no | **yes** (add `pointer-events: none` to disable) |
| **Accessibility tree** | generally omitted | generally omitted | often still exposed; inspect semantics and assistive technology |
| **Can animate** | discrete display transitions are possible in supporting browsers | visibility is discrete | opacity is interpolated |
| **Rendering work** | removes/recreates the box | keeps layout space | keeps the box; compositing is implementation-dependent |
| **Affects children** | children hidden | children inherit (can override with `visibility: visible`) | group opacity includes descendants; the value is not inherited |

`opacity` is not inherited, but the element and its descendants are composited as one group. A child with `opacity: 1` cannot undo a transparent parent.

##### Decision guide

- Need the element **gone** from layout and generally from the accessibility tree? → `display: none`.
- Need to **hide visually but preserve layout** (keep siblings stable)? → `visibility: hidden`.
- Need to **fade in/out** with a transition? → animate `opacity`; also manage keyboard focus, pointer input, and accessibility semantics while hidden. `pointer-events: none` alone does not remove an element from keyboard focus.

```css
.hidden-flow        { display: none; }
.hidden-space       { visibility: hidden; }
.hidden-transparent { opacity: 0; pointer-events: none; }
```

**Gotcha — discrete display transitions:** `display` is not interpolated like `opacity`; CSS Transitions can opt into a discrete transition with `transition-behavior: allow-discrete` and a starting style in supporting browsers. Check target-browser support before relying on it.

---

### How do CSS transitions and animations work, and when should you prefer one over the other?

**Headline (30s):** A **transition** interpolates between two states triggered by a property change (e.g., hover). An **animation** runs independently from defined keyframes and can loop, pause, and control fill state. Use transitions for simple state-to-state interactions (hover, focus, click). Use animations for complex, multi-step, or looping motion.

#### Transitions

```css
.element { transition: property duration timing-function delay; }

.button { transition: background-color 0.3s ease-in-out 0.1s; }
```

Individual properties:

| Property | Purpose |
|---|---|
| `transition-property` | which properties animate (`all`, `color`, `transform`, etc.) |
| `transition-duration` | length (e.g., `0.3s`, `300ms`) |
| `transition-timing-function` | easing (`ease`, `linear`, `ease-in`, `ease-out`, `cubic-bezier(...)`) |
| `transition-delay` | delay before start |

```css
.element {
  transition-property: transform, opacity;
  transition-duration: 0.3s, 0.2s;
  transition-timing-function: ease-out, linear;
  transition-delay: 0s, 0.1s;
}
```

#### `@keyframes` and `animation`

Keyframes define intermediate states; `animation` applies them.

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes slideIn {
  0%   { transform: translateX(-100%); }
  50%  { transform: translateX(10%); }
  100% { transform: translateX(0); }
}

.box { animation: fadeIn 0.5s ease-out forwards; }
```

Individual properties:

| Property | Purpose |
|---|---|
| `animation-name` | keyframes name |
| `animation-duration` | length of one cycle |
| `animation-timing-function` | easing (can vary per keyframe) |
| `animation-delay` | delay before start |
| `animation-iteration-count` | `1`, `infinite`, or a number |
| `animation-direction` | `normal`, `reverse`, `alternate`, `alternate-reverse` |
| `animation-fill-mode` | `none`, `forwards`, `backwards`, `both` |
| `animation-play-state` | `running` or `paused` |

#### `transform` properties

| Function | Effect |
|---|---|
| `translate(x, y)` | move |
| `translateX(x)` / `translateY(y)` / `translateZ(z)` | move on one axis (Z needs 3D context) |
| `rotate(angle)` | 2D rotate |
| `rotateX/Y/Z(angle)` | 3D rotate |
| `scale(x, y)` | resize |
| `scaleX(x)` / `scaleY(y)` | resize per axis |

```css
.card { transform: translate(10px, 20px) rotate(5deg) scale(1.05); }
```

#### Compositing and `will-change`

Animating `transform` and `opacity` can let an engine update presentation without recalculating layout, but neither property guarantees compositor-only or GPU work. `will-change` is a hint that may have memory and stacking effects; it does not guarantee layer promotion. See [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for typical invalidation paths.

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* may affect compositing; it does not guarantee GPU acceleration */
}
```

**Gotcha — don't `will-change` everything:** Browsers may allocate extra resources or alter stacking behavior for hinted properties. Apply it only after measurement, keep the hinted region small, and remove it when no longer needed.

**Gotcha — `transform: translateZ(0)` is not a GPU switch:** It changes transform behavior and may affect stacking/containing blocks; it does not guarantee a faster path. Use neither it nor `will-change` as a substitute for profiling.

**See also:** [`2.2 Box Model and BFC`](#3.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) for formatting-context behavior, [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for rendering invalidation, [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for measurement guidance.

**Specifications / 规范：** [CSS Positioned Layout](https://www.w3.org/TR/css-position-3/), [CSS Display](https://www.w3.org/TR/css-display-3/), [CSS Color opacity](https://www.w3.org/TR/css-color-4/#transparency), [CSS Transforms](https://www.w3.org/TR/css-transforms-1/), [CSS Transitions](https://www.w3.org/TR/css-transitions-2/), [W3C WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/).
## 9. JavaScript Basics / JavaScript基础

### JavaScript Variable Declarations / JavaScript 变量声明

**Key terms / 关键词:** binding 绑定 · function scope 函数作用域 · block scope 块级作用域 · hoisting 提升 · Temporal Dead Zone 暂时性死区

The main choice is whether a binding may be reassigned and how long it is visible. Prefer `const` when the binding stays fixed, use `let` when it must be reassigned, and recognize `var` when maintaining older code. / 选择声明方式时，重点看绑定是否需要重新赋值以及它的可见范围。绑定不需重新赋值时优先用 `const`，需要重新赋值时用 `let`，维护旧代码时识别 `var` 的作用域行为。

| Behavior / 行为 | `var` | `let` | `const` |
|---|---|---|---|
| Scope / 作用域 | Function scope; top-level context depends on script, module, or host / 函数作用域；顶层由脚本、模块或宿主决定 | Lexical block / 词法块 | Lexical block / 词法块 |
| Before declaration / 声明前访问 | Initialized to `undefined` when its binding is created / 绑定创建时初始化为 `undefined` | TDZ; access throws / TDZ，访问会抛错 | TDZ; access throws / TDZ，访问会抛错 |
| Same-scope redeclaration / 同作用域重复声明 | Often allowed for `var` / 通常允许 | Syntax error / 语法错误 | Syntax error / 语法错误 |
| Reassignment / 重新赋值 | Allowed / 允许 | Allowed / 允许 | Binding cannot be reassigned / 绑定不能重新赋值 |
| Initializer required / 是否必须初始化 | No / 否 | No / 否 | Yes / 是 |

#### `var`: function scope / 函数作用域

A `var` declaration belongs to the nearest function scope, or the top-level variable environment provided by the current script, module, or host wrapper; a surrounding `if` or `for` block does not create a new `var` scope. The binding exists before the declaration executes and starts as `undefined`; its initializer still runs at its written position. / `var` 属于最近的函数作用域；若代码位于顶层，则属于当前脚本、模块或宿主包装器提供的顶层变量环境。外层的 `if` 或 `for` 块不会创建新的 `var` 作用域。绑定在声明执行前已经存在，初值为 `undefined`；初始化表达式仍在代码写出的位置执行。

```javascript
function example() {
  console.log(value); // undefined
  if (true) {
    var value = 10;
  }
  console.log(value); // 10
}
```

#### `let` and `const`: lexical scope / 词法作用域

A lexical binding is in the Temporal Dead Zone from entry into its scope until its declaration is evaluated. The binding is not usable during that interval. `const` also requires an initializer and prevents reassignment of the binding; it does not freeze an object stored in that binding. / 词法绑定从进入作用域开始，到声明执行之前处于暂时性死区（TDZ），这段时间不能访问。`const` 还要求声明时初始化，并禁止重新赋值绑定；它不会冻结绑定所指向的对象。

```javascript
const settings = { theme: "light" };
settings.theme = "dark"; // allowed: the object is mutable
// settings = {};        // TypeError: the binding cannot be reassigned

{
  // console.log(count); // ReferenceError: still in the TDZ
  let count = 1;
}
```

At the top level, script, module, and host environments differ. In a classic browser script, a global `var` can create a property on the global object, while `let` and `const` create global lexical bindings instead. Do not assume this browser-script behavior for ES modules or Node modules. / 顶层行为会因脚本、模块和宿主环境而异。在浏览器经典脚本中，全局 `var` 可以在全局对象上创建属性，而 `let`、`const` 创建的是全局词法绑定。不要把该浏览器脚本行为直接套用到 ES 模块或 Node 模块。

**Interview answer / 面试回答:** `var` is function-scoped and initialized to `undefined` when its binding is created. `let` and `const` are block-scoped and inaccessible in the TDZ before declaration evaluation. `const` protects the binding from reassignment, not the referenced object from mutation. / `var` 是函数作用域，绑定创建时会初始化为 `undefined`。`let` 和 `const` 是块级词法作用域，声明执行前处于 TDZ。 `const` 保护的是绑定，不能阻止对象内容被修改。

See [ECMAScript declarations and environments](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html), including [Module Environment Records](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records), for the language rules. / 变量声明与环境记录规则见 [ECMAScript 声明和执行上下文规范](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html)，包括[模块环境记录](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)。

Related: [Scope and Closure / 作用域与闭包](#18.%20Scope%20&%20Closure%20/%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85).
## 10. JavaScript Types / JavaScript类型

### JavaScript Types and Coercion / JavaScript 类型与类型转换

**Key terms / 关键词:** primitive 原始值 · object 对象 · coercion 隐式转换 · property key 属性键 · realm 执行领域

JavaScript has seven primitive types: `undefined`, `null`, `boolean`, `number`, `bigint`, `string`, and `symbol`. Other values are objects, including functions. A value’s language semantics are specified; whether an engine stores it on a stack, heap, or elsewhere is an implementation detail. / JavaScript 有七种原始类型：`undefined`、`null`、`boolean`、`number`、`bigint`、`string` 和 `symbol`。其他值都是对象，函数也属于对象。语言规范定义的是值的行为；引擎是否把值放在栈、堆或其他位置属于实现细节。

| Type / 类型 | Useful fact / 要点 |
|---|---|
| `undefined` | Default value of an uninitialized `var` binding or missing result / 未初始化的 `var` 绑定或缺失结果的默认值 |
| `null` | Intentional absence; `typeof null` is the historical string `"object"` / 表示有意为空；`typeof null` 因历史兼容结果为 `"object"` |
| `boolean` | Falsy values include `false`, `0`, `-0`, `0n`, `""`, `null`, `undefined`, and `NaN` / 假值包括这些值 |
| `number` | IEEE 754 binary64; includes `NaN` and infinities / IEEE 754 binary64，包含 `NaN` 与无穷值 |
| `bigint` | Arbitrary-precision integers; cannot be mixed with Number arithmetic without conversion / 任意精度整数；算术运算不能直接与 Number 混用 |
| `string` | Immutable sequence of UTF-16 code units / 不可变的 UTF-16 码元序列 |
| `symbol` | Unique primitive value, often used as a property key / 唯一原始值，常用作属性键 |

Objects and functions are mutable or callable according to their own behavior; “reference type” is a useful description of assignment and identity, not a guarantee about physical memory layout. / 对象和函数的可变性、可调用性由各自行为决定。“引用类型”可以帮助解释赋值与身份，但不代表固定的物理内存布局。

#### Coercion essentials / 类型转换要点

Truthiness and numeric conversion are separate operations. Empty arrays and objects are truthy; `Number("")` and `Number(null)` are zero; `Number(undefined)` is `NaN`. Use explicit conversions where the input contract matters. / 布尔转换与数值转换是不同操作。空数组和空对象都是真值；`Number("")` 与 `Number(null)` 为 0；`Number(undefined)` 为 `NaN`。输入契约重要时应显式转换。

```javascript
Boolean("false"); // true: nonempty string
Boolean([]);      // true
Number("");       // 0
Number(null);     // 0
Number(undefined);// NaN

Number.isNaN(NaN); // true
NaN === NaN;       // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

Use `x === null` to test specifically for null. `Number.isNaN(x)` tests NaN without first coercing non-number inputs. / 若要专门判断 null，使用 `x === null`。`Number.isNaN(x)` 不会先把非数值输入强制转换。

#### Assignment and object identity / 赋值与对象身份

Assigning an object value to another binding makes both bindings refer to the same object. A property assignment evaluates and remembers its base object before evaluating the right side; it does not create an “undefined slot” in advance. / 把对象值赋给另一个绑定后，两个绑定会引用同一个对象。属性赋值会先求值并记录基对象，再求值右侧表达式；这时还不会提前创建一个值为 `undefined` 的属性槽。

```javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }
```

Evaluation first captures the old object as the base of `a.x`. The right side then reassigns `a` to a new object; the final property write still targets the captured old object, which `b` references. / 求值先把旧对象记录为 `a.x` 的基对象；右侧随后把 `a` 重新绑定到新对象；最后写入仍作用于之前记录的旧对象，也就是 `b` 引用的对象。

#### Choosing a type check / 如何选择类型判断方式

- `typeof` is useful for primitives and functions, with the `null` quirk shown above. / `typeof` 适合判断原始值和函数，但要记住 null 的历史特例。
- `Array.isArray(value)` is the robust array check, including arrays from another realm. / `Array.isArray(value)` 能可靠识别来自其他 realm 的数组。
- By default, `instanceof` checks whether the RHS constructor’s `.prototype` occurs in the LHS value’s prototype chain ([`OrdinaryHasInstance`](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance)). Constructors from different realms normally have different prototype objects, so a foreign value can fail against the local constructor but pass against its own realm’s constructor. `Symbol.hasInstance` can customize the check. / 默认情况下，`instanceof` 检查右侧构造函数的 `.prototype` 是否出现在左侧值的原型链中（见 [`OrdinaryHasInstance`](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance)）。不同 realm 中的构造函数通常有不同原型对象，因此跨 realm 的值可能无法通过本地构造函数判断，却能通过其所属 realm 的构造函数判断。`Symbol.hasInstance` 可自定义该检查。
- `Object.prototype.toString.call(value)` is a useful built-in tag, not a definitive type oracle: `Symbol.toStringTag` can change the displayed tag. / `Object.prototype.toString.call(value)` 可读取内置标签，但不是绝对可靠的类型证明：`Symbol.toStringTag` 可以改变显示标签。

```javascript
typeof null; // "object"
Array.isArray([]); // true

const custom = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(custom); // "[object Array]" — a spoofable tag
```

For application validation, prefer a check for the behavior or data shape the code actually requires, rather than a generic display string. / 应用校验应检查代码实际依赖的行为或数据结构，不要只依赖通用类型字符串。

See [ECMAScript Object.prototype.toString](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring) and its use of `Symbol.toStringTag`. / 详见 [ECMAScript Object.prototype.toString 规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring)及其对 `Symbol.toStringTag` 的处理。

#### Object property keys / 对象属性键

A property key is a string or a symbol. When another value is used in bracket notation, JavaScript applies `ToPropertyKey`: objects may run `Symbol.toPrimitive` or other conversion hooks before producing a string or symbol. This is more precise than saying every key simply calls `toString()`. / 属性键是字符串或 Symbol。方括号中使用其他值时，JavaScript 会执行 `ToPropertyKey`：对象可能先运行 `Symbol.toPrimitive` 等转换钩子，再得到字符串或 Symbol。因此“其他键都直接调用 `toString()`”并不准确。

```javascript
const record = {};
record[123] = "number";
record["123"]; // "number"

const key = { [Symbol.toPrimitive]: () => "account" };
record[key] = "Ada";
record.account; // "Ada"

const map = new Map();
map[{ id: 1 }] = "property key conversion";
map.set({ id: 1 }, "object identity key"); // Map does not coerce keys
```

Use `Map` when distinct object identities or uncoerced non-string keys matter. For plain-object dictionaries, use `Object.hasOwn` for ownership checks; `Object.create(null)` avoids an inherited prototype but still uses property-key conversion. / 需要区分对象身份或避免键转换时使用 `Map`。普通对象字典可用 `Object.hasOwn` 判断自有属性；`Object.create(null)` 可去掉继承原型，但仍会转换属性键。

**Interview answer / 面试回答:** JavaScript has seven primitive types. Objects are assigned and compared by identity, but stack-versus-heap layout is engine-specific. Use `typeof` for basic primitive checks, `Array.isArray` for arrays, and `instanceof` for a constructor’s prototype-chain relationship, accounting for realm-specific constructor identity. Object keys are strings or symbols after `ToPropertyKey` conversion. / JavaScript 有七种原始类型。对象按身份赋值和比较，但栈与堆的布局由引擎决定。基础类型判断可用 `typeof`，数组用 `Array.isArray`；使用 `instanceof` 判断构造函数的原型链关系时，应考虑 realm 中构造函数身份的差异。对象键经过 `ToPropertyKey` 后只能是字符串或 Symbol。

See [ECMAScript types and values](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html) and [property key conversion](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey). / 详见 [ECMAScript 类型和值](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html) 与 [属性键转换](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey)。

Related: [Map and Set / JavaScript 中的 Map 与 Set](#11.%20Map%20and%20Set%20in%20JavaScript%20/%20JavaScript%20%E4%B8%AD%E7%9A%84%20Map%20%E4%B8%8E%20Set); [Memory, WeakMap and WeakSet / JavaScript 内存、WeakMap 与 WeakSet](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef).
## 11. Map and Set in JavaScript / JavaScript 中的 Map 与 Set

### Map and Set in JavaScript / JavaScript 中的 Map 与 Set

**Key terms / 关键词:** keyed collection 键控集合 · SameValueZero 相同值零 · insertion order 插入顺序 · set-like object 类 Set 对象

Use `Map` for key-value data when keys are not just fixed strings or symbols, or when direct iteration and a size property help. Use `Set` when uniqueness and membership are central. ECMAScript specifies observable ordering and equality, but not a particular hash-table implementation or constant-time performance. / 当键不只是固定字符串或 Symbol，或需要直接迭代与 size 属性时，可用 `Map` 保存键值数据；当重点是唯一性和成员判断时，可用 `Set`。ECMAScript 规定可观察到的顺序和相等规则，但不规定具体哈希表实现或恒定时间性能。

#### Choosing a collection / 选择集合

- `Map`: keys may be any value; object keys use identity; entries iterate in insertion order. Updating an existing key does not move its position. Delete then reinsert to place it at the end. / `Map`：键可以是任意值；对象键按身份比较；条目按插入顺序迭代。更新已有键不会改变位置；删除后重新插入才会移到末尾。
- `Set`: stores unique values in insertion order. Deleting and adding a value again places it at the end. / `Set`：按插入顺序保存唯一值。删除后再次添加会移到末尾。
- Plain objects coerce property keys to strings or symbols and include prototype behavior unless created with a null prototype. For ordinary dictionaries, `Object.hasOwn` avoids an overridden `hasOwnProperty`; `Map` is often simpler when keys are dynamic. / 普通对象会把属性键转换为字符串或 Symbol；除非创建为 null 原型对象，否则还有原型行为。对象字典可用 `Object.hasOwn` 避免被覆盖的 `hasOwnProperty`；键动态时通常 Map 更简单。
- Arrays are suited to indexed, positional data. A Set is not a replacement when duplicate positions or random indexing matter. / 数组适合按索引排列的数据；若需要保留重复位置或随机索引，Set 不能替代数组。

Both Map and Set use SameValueZero for keys or members: NaN matches NaN, and +0 and -0 are treated as the same key. Objects compare by identity. / Map 和 Set 对键或成员使用 SameValueZero：NaN 与自身相同，+0 与 -0 被视为同一个键；对象按身份比较。

#### Map / 映射

```javascript
const userById = new Map();
userById.set(7, { name: "Ada" });
userById.set("7", { name: "Grace" }); // number and string keys differ

userById.get(7); // { name: "Ada" }
userById.has(8); // false
userById.size; // 2

for (const [id, user] of userById) {
  console.log(id, user.name); // insertion order
}
```

Core methods are `set`, `get`, `has`, `delete`, `clear`, and the `size` property. `keys()`, `values()`, and `entries()` return iterators; the default iterator is `entries()`. `forEach` receives `(value, key, map)`. / 常用方法包括 `set`、`get`、`has`、`delete`、`clear`，以及 `size` 属性。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器等同于 `entries()`。`forEach` 的参数顺序是 `(value, key, map)`。

| Method / 方法 | Result / 返回值 |
|---|---|
| `set(key, value)` | The Map, for chaining / 返回 Map，可链式调用 |
| `get(key)` | Value or `undefined` / 值或 `undefined` |
| `has(key)` | Boolean / 布尔值 |
| `delete(key)` | Whether an entry was removed / 是否删除了条目 |
| `clear()` | Empties the Map / 清空 Map |

#### Set / 集合

```javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]
```

Core methods are `add`, `has`, `delete`, `clear`, and the `size` property. `keys()` and `values()` produce the same values; `entries()` yields `[value, value]` for compatibility with Map iteration. `forEach` receives `(value, value, set)`. / 常用方法包括 `add`、`has`、`delete`、`clear`，以及 `size` 属性。`keys()` 和 `values()` 产出相同的值；为兼容 Map 迭代，`entries()` 产出 `[value, value]`。`forEach` 的参数顺序是 `(value, value, set)`。

| Method / 方法 | Result / 返回值 |
|---|---|
| `add(value)` | The Set, for chaining / 返回 Set，可链式调用 |
| `has(value)` | Boolean / 布尔值 |
| `delete(value)` | Whether a value was removed / 是否删除了值 |
| `clear()` | Empties the Set / 清空 Set |

#### Set composition methods / Set 集合运算

ECMAScript 2025 standardized `union`, `intersection`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, and `isDisjointFrom`. They accept set-like inputs and return a Set or boolean as indicated by the method. Check runtime support when targeting older engines. / ECMAScript 2025 标准化了 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。这些方法接受类 Set 输入，并按方法返回 Set 或布尔值。面向较旧引擎时需确认运行时支持。

```javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true
```

#### Common patterns / 常见用法

```javascript
const unique = [...new Set([1, 2, 2, 3])]; // [1, 2, 3]

const right = new Set([2, 3, 4]);
const leftOnly = [...new Set([1, 2, 3])]
  .filter(value => !right.has(value)); // [1]
```

For repeated membership checks, build the lookup Set once rather than inside the filter callback. / 需要反复查询成员时，应先创建一次 Set，而不是在 filter 回调中重复创建。

**Interview answer / 面试回答:** Map preserves arbitrary key identity and insertion order; Set preserves unique values in insertion order. Both use SameValueZero, while plain object keys undergo property-key conversion. Their complexity depends on the implementation; the standard requires average sublinear access rather than a fixed O(1) guarantee. / Map 保留任意键的身份和插入顺序；Set 按插入顺序保存唯一值。二者使用 SameValueZero，普通对象键则会进行属性键转换。复杂度取决于实现；标准只要求平均访问优于线性，并不保证固定 O(1)。

See [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) and [Set methods](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects). / 详见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) 与 [Set 方法规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects)。

Related: [JavaScript Types and Coercion / JavaScript 类型与类型转换](#10.%20JavaScript%20Types%20/%20JavaScript%E7%B1%BB%E5%9E%8B); [Memory and weak collections / JavaScript 内存与弱集合](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef).
## 12. JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef

### JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef

**Key terms / 关键词:** reachability 可达性 · weak key 弱键 · garbage collection 垃圾回收 · finalization 清理回调

JavaScript specifies object identity, reachability-related weak collection behavior, and observable results. It does not require values to live on a “stack” or “heap,” prescribe one garbage collector, or promise when collection occurs. Treat weak references as a way to avoid owning a key, never as a predictable cleanup schedule. / JavaScript 规定对象身份、弱集合相关行为和可观察结果，但不要求值存放在“栈”或“堆”中，不规定唯一的垃圾回收算法，也不保证何时回收。弱引用用于避免强持有某个键，不能当作可预测的清理计划。

#### WeakMap / 弱映射

A WeakMap associates a weakly held key with a strongly held value. The entry does not by itself keep its key alive. It has no enumeration, `size`, or `forEach`, because exposing which keys remain would make garbage-collection timing observable. / WeakMap 把弱持有的键关联到强持有的值。该条目本身不会让键保持存活。它没有枚举、`size` 或 `forEach`，因为暴露哪些键仍存在会使垃圾回收时机变得可观察。

Since ECMAScript 2023, keys may be objects or non-registered symbols. `Symbol.for(...)` symbols are registered and cannot be weak keys. Older runtimes may support only object keys, so check the target runtime if symbol keys are needed. / 从 ECMAScript 2023 起，键可以是对象或非注册 Symbol。`Symbol.for(...)` 创建的注册 Symbol 不能作为弱键。较旧运行时可能只支持对象键；需要 Symbol 键时应检查目标运行时支持情况。

```javascript
const metadata = new WeakMap();

function attachMetadata(node, info) {
  metadata.set(node, info);
}
function readMetadata(node) {
  return metadata.get(node);
}

const privateSymbol = Symbol("metadata");
metadata.set(privateSymbol, { source: "ES2023 non-registered symbol key" });

const registered = Symbol.for("shared");
metadata.has(registered); // false
// metadata.set(registered, {}); // TypeError
```

Typical uses include metadata keyed by objects owned elsewhere, or data associated with class instances without creating a public property. The WeakMap entry does not by itself keep its key alive, even when the value refers back to the key; another strong path to the key, such as an externally retained value, can still keep it alive. / 常见用途包括为其他代码持有的对象保存元数据，或为类实例关联数据而不增加公开属性。WeakMap 条目本身不会让键保持存活，即使值又引用该键也是如此；但若存在其他强引用路径（例如值被外部继续持有），键仍会存活。

#### WeakSet / 弱集合

A WeakSet weakly tracks objects or non-registered symbols and supports membership operations, but no enumeration or size. Use it for identity-based “seen” tracking when retaining the tracked value would be undesirable. / WeakSet 弱持有对象或非注册 Symbol，只提供成员操作，没有枚举或 size。若不希望跟踪操作本身延长对象生命周期，可用它按身份记录“已见过”的对象。

```javascript
const processed = new WeakSet();

function processOnce(value) {
  if (processed.has(value)) return;
  processed.add(value);
  // perform work once for this identity
}
```

A normal Set or Map strongly retains its members or keys. Use one when iteration, counting, or deterministic lifetime management matters. / 普通 Set 或 Map 会强持有成员或键。需要枚举、计数或确定生命周期时应使用普通集合。

#### WeakRef and FinalizationRegistry / 弱引用与最终化注册表

`WeakRef` and `FinalizationRegistry` were standardized in ES2021. A WeakRef lets a program try to access a target without making that target strongly reachable through the reference. `deref()` returns the target if it is still available, otherwise `undefined`. A FinalizationRegistry may schedule cleanup after a target becomes unreachable. Neither the collection time nor the callback time is guaranteed; cleanup may be delayed or omitted before program exit. Do not use either API for correctness-critical resource release, accounting, or prompt UI updates. / `WeakRef` 和 `FinalizationRegistry` 于 ES2021 标准化。WeakRef 允许程序尝试访问目标，但不会通过该引用强持有目标。`deref()` 在目标仍可用时返回它，否则返回 `undefined`。FinalizationRegistry 可能在目标不可达后安排清理回调，但回收和回调时机都没有保证；程序退出前回调也可能未执行。不要把这些 API 用于正确性关键的资源释放、计数或及时 UI 更新。

If `deref()` returns a target, ECMAScript keeps it alive until the current job completes. This provides consistency within that job; it does not promise that the target remains afterward. / 如果 `deref()` 返回目标，ECMAScript 会使它至少存活到当前 job 结束，以保证该 job 内行为一致；这不承诺目标之后仍然存活。

See [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) and [weak references and finalization](https://tc39.es/ecma262/2025/multipage/managing-memory.html). The specification explicitly permits implementation-dependent collection latency. / 详见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) 和 [弱引用与最终化规范](https://tc39.es/ecma262/2025/multipage/managing-memory.html)。规范明确允许回收延迟由实现决定。

**Interview answer / 面试回答:** WeakMap and WeakSet let object identity be associated or tracked without the collection itself keeping the key alive. Their lack of enumeration prevents programs from depending on nondeterministic garbage-collection timing. WeakRef and finalization callbacks are likewise nondeterministic, so use them only for opportunistic behavior. / WeakMap 和 WeakSet 可关联或跟踪对象身份，而不会由集合本身强持有键。它们不能枚举，避免程序依赖不确定的垃圾回收时机。WeakRef 和最终化回调同样不确定，只适合可有可无的优化行为。

Related: [Map and Set / JavaScript 中的 Map 与 Set](#11.%20Map%20and%20Set%20in%20JavaScript%20/%20JavaScript%20%E4%B8%AD%E7%9A%84%20Map%20%E4%B8%8E%20Set); [Event Loop and Host Scheduling / 事件循环与宿主调度](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF).
## 13. JavaScript Arrays / JavaScript 数组

### JavaScript Arrays / JavaScript 数组

**Key terms / 关键词:** iterable 可迭代对象 · sparse array 稀疏数组 · SameValueZero 相同值零 · shallow copy 浅拷贝

Arrays are ordered objects with indexed properties and an iterable interface. Choose an operation by its contract: iteration protocol, holes, mutation, and equality can change the result. / 数组是带索引属性并实现可迭代协议的有序对象。选择操作时要看清迭代协议、空位、是否修改原数组及相等规则，这些都会影响结果。

#### Iterating keys or values / 遍历键还是值

Use `for...of` for values from an iterable. Use `for...in` only when enumerating property names, usually on a plain object. A normal dense array’s own index keys are visited in ascending order, but `for...in` can also include custom and inherited enumerable string properties. / 用 `for...of` 遍历可迭代对象的值；`for...in` 遍历属性名，通常用于普通对象。普通稠密数组的自有索引键按升序枚举，但 `for...in` 也可能包含自定义属性和原型链上的可枚举字符串属性。

```javascript
const values = [10, 20];
for (const key in values) console.log(key); // "0", "1"
for (const value of values) console.log(value); // 10, 20

const record = { name: "Ada", age: 36 };
for (const [key, value] of Object.entries(record)) {
  console.log(key, value); // own enumerable string-keyed properties
}
```

An array hole is different from an own property whose value is `undefined`: `for...of` reads a hole as `undefined`; methods such as `map` and `filter` skip absent indices. `for...in` lists only existing enumerable properties. Avoid using it when the array’s positional values are intended. / 数组空位不同于值为 `undefined` 的自有属性：`for...of` 读取空位时得到 `undefined`，而 `map`、`filter` 等方法会跳过不存在的索引。`for...in` 只列出现存的可枚举属性。需要按位置处理数组值时不要用它。

The ordering and inheritance behavior follows the [ECMAScript for-in/for-of rules](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements). / 顺序与继承行为遵循 [ECMAScript for-in/for-of 规范](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)。

#### Removing duplicates / 数组去重

For primitive values, `[...new Set(values)]` keeps the first occurrence in iteration order. Set uses SameValueZero: `NaN` matches `NaN`, and `+0` matches `-0`. Objects compare by identity, so two different objects with the same fields remain distinct. / 对原始值，`[...new Set(values)]` 会按迭代顺序保留首次出现的值。Set 使用 SameValueZero：`NaN` 与自身相同，`+0` 与 `-0` 相同。对象按引用身份比较，因此字段相同但引用不同的对象仍会保留。

```javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2: distinct references
```

For object deduplication by a field, a Map is concise. In this example the last value for an id wins, while the key retains the order of its first insertion. / 按对象字段去重时可用 Map。以下实现中相同 id 的最后一个对象胜出，但键的遍历位置仍按首次插入顺序保留。

```javascript
function uniqueById(items) {
  const byId = new Map();
  for (const item of items) byId.set(item.id, item);
  return [...byId.values()];
}
```

A Set/Map approach is commonly linear in practical runtimes, but ECMAScript requires average access to be sublinear, not a specific O(1) implementation or end-to-end complexity. Linear `indexOf`/accumulator searches can be quadratic; choose them only when the input size or other requirements justify them. A sort-based approach changes order and needs a comparator whose equality matches the deduplication rule. / Set/Map 在常见运行时中通常表现为线性处理，但 ECMAScript 只要求平均访问复杂度优于线性，并未规定必须 O(1)，整体复杂度也取决于运行时。反复用 `indexOf` 或累加器查找可能达到平方复杂度。排序去重会改变顺序，且比较器的相等规则必须符合去重需求。

See the [ECMAScript keyed collections specification](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) for Set and Map equality and ordering semantics. / Set 与 Map 的相等和顺序语义见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html)。

#### Array methods: mutation and holes / 数组方法：修改行为与空位

- `map` transforms each present index and returns a new array; it skips holes and preserves those holes in the result. / `map` 转换每个已存在的索引并返回新数组；它跳过空位，结果中也保留对应空位。
- `filter` returns the present values that pass the predicate; holes are skipped and are not copied. / `filter` 返回通过判断的现存值；空位会跳过，也不会复制。
- `some` and `every` stop when the answer is known; both skip holes. On an empty array, `some` is false and `every` is true. / `some` 和 `every` 在结论已确定时停止；二者都会跳过空位。空数组上 `some` 为 false，`every` 为 true。
- `reduce` folds present elements; provide an initial value when the empty-array case matters. / `reduce` 折叠现存元素；若空数组也需有定义的结果，应提供初始值。
- `concat` returns a shallow new array and can consult `Symbol.isConcatSpreadable`; spread syntax follows the iterable protocol instead. / `concat` 返回浅拷贝新数组，并可能遵循 `Symbol.isConcatSpreadable`；展开语法则使用可迭代协议。
- `sort` and `reverse` mutate the receiver; `toSorted` and `toReversed` (ES2023) return copies. Sorting is stable since ES2019. Default `sort()` compares string forms, not numeric values. / `sort` 和 `reverse` 会修改原数组；ES2023 的 `toSorted`、`toReversed` 返回副本。ES2019 起排序稳定。默认 `sort()` 比较字符串形式，而非数值大小。

```javascript
[1, 11, 2].sort(); // [1, 11, 2] — lexicographic string ordering
[1, 11, 2].toSorted((a, b) => a - b); // [1, 2, 11]; receiver is unchanged

const sparse = [, "x"];
[...sparse]; // [undefined, "x"] — spread consumes the array iterator
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
sparse.flat(); // ["x"] — flat removes holes at flattened levels
```

#### Spread and copying / 展开与拷贝

Array spread consumes an iterable and copies its yielded values shallowly. Nested objects are still shared. Object spread is a separate operation: it copies an object’s own enumerable properties into a new object. / 数组展开会消费可迭代对象并浅拷贝其产出的值；嵌套对象仍然共享。对象展开是另一种操作：把对象的自有可枚举属性复制到新对象。

```javascript
const original = [{ score: 1 }];
const copy = [...original];
copy[0].score = 2;
original[0].score; // 2 — the nested object is shared

const merged = { ...defaults, ...overrides }; // later properties replace earlier ones
```

Transpilers may lower spread in different ways according to the target and helper settings. Do not treat one Babel output such as `[].concat(value)` as the language semantics: array spread uses the iterator, while `concat` has different behavior for sparse arrays and spreadable objects. / 转译器会按目标环境与配置选择不同实现。不要把某一种 Babel 输出（如 `[].concat(value)`）当作语言语义：数组展开消费迭代器，而 `concat` 对稀疏数组和可展开对象的处理不同。

#### Flattening nested arrays / 展平嵌套数组

`flat(depth)` (ES2019) returns a shallowly flattened copy and defaults to depth 1. Use `flat(Infinity)` when arbitrary nesting is intended; it removes holes at levels it flattens and does not recursively flatten non-array iterables. / ES2019 的 `flat(depth)` 返回浅层展平副本，默认深度为 1。确实需要展平任意嵌套时可用 `flat(Infinity)`；它会移除被展平层级中的空位，不会递归展平非数组可迭代对象。

A recursive implementation makes the rule explicit, but can exceed the call-stack limit on deeply nested input. This version visits every numeric position, so a hole becomes `undefined`, unlike `flat`. / 递归实现能直观表达规则，但极深输入可能超出调用栈限制。以下版本逐个访问数值索引，因此空位会变成 `undefined`，与 `flat` 不同。

```javascript
function flattenNested(items) {
  const result = [];
  for (let i = 0; i < items.length; i++) {
    const value = items[i];
    if (Array.isArray(value)) result.push(...flattenNested(value));
    else result.push(value);
  }
  return result;
}

flattenNested([1, [2, [3]], 4]); // [1, 2, 3, 4]
[1, [2, [3]], 4].flat(Infinity); // [1, 2, 3, 4]
```

The historical iterative `[].concat(...items)` pattern flattens one level per pass. It can hit argument-count limits, repeatedly copy large arrays, and has different sparse-array behavior from `flat`; it may also return the original input when no nested array exists. / 传统迭代写法 `[].concat(...items)` 每轮展平一层，但可能触发参数数量限制、反复复制大数组，而且稀疏数组行为与 `flat` 不同；若没有嵌套数组，它还可能直接返回原数组。

```javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
```

Prefer `flat` when its hole and depth semantics match the task. / 若 `flat` 的空位和深度语义符合需求，应优先使用。

**Interview answer / 面试回答:** `for...of` reads array values; Set deduplicates by SameValueZero while preserving first-seen order; array methods differ on holes and mutation; spread is shallow; and `flat` is the built-in flattening operation. / `for...of` 读取数组值；Set 按 SameValueZero 去重并保留首次出现顺序；数组方法对空位和原数组修改的行为不同；展开是浅拷贝；内置展平方法是 `flat`。
## 14. ES6 New Methods / ES6新增方法

### Object and Array Methods / 对象与数组方法

**Key terms / 关键词:** own property 自有属性 · enumerable 可枚举 · shallow copy 浅拷贝 · array-like 类数组对象

This is a focused reference for selected Object and Array methods and their edition boundaries. Newer additions such as Object.hasOwn and Array.at are covered in [Modern JavaScript Features / 现代 JavaScript 特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7). / 本笔记选列部分 Object 与 Array 方法，并标明其版本边界。Object.hasOwn、Array.at 等后续新增方法见[现代 JavaScript 特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7)。

#### Object methods / Object 方法

##### Object.assign(target, ...sources)

Copies enumerable own string and symbol properties from each source to target, mutates and returns target. Later sources overwrite earlier properties. The copy is shallow. Reading a source may invoke getters; writing to the target may invoke setters. / 把各个来源对象的自有可枚举字符串键和 Symbol 键复制到 target，修改并返回 target。后面的来源会覆盖前面的同名属性。该操作是浅拷贝；读取来源对象可能触发 getter，写入 target 可能触发 setter。

```javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target is { a: 1, b: 3, c: 4 }

const merged = Object.assign({}, defaults, overrides);
```

Object spread is often more concise, but is not identical in every detail: it creates own data properties in a new object, while Object.assign writes to its existing target and can invoke target setters. / 对象展开通常更简洁，但细节并非处处等价：展开会在新对象上创建自有数据属性；Object.assign 则写入已有目标对象，可能触发目标 setter。

##### Object.is(a, b)

Uses SameValue equality. It differs from === for NaN and signed zero: / 使用 SameValue 相等规则。它对 NaN 和有符号零的处理与 === 不同：

```javascript
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
NaN === NaN;         // false
+0 === -0;           // true
```

##### Object.keys, Object.values, and Object.entries

Object.keys was standardized in ES5; Object.values and Object.entries were added in ES2017. They return an object’s own enumerable string-keyed property names, values, or pairs. Symbol-keyed properties are excluded. For ordinary objects, array-index string keys come first in ascending numeric order, followed by other string keys in creation order. This ordinary-object order is not a guarantee for proxies or every exotic object. / Object.keys 属于 ES5；Object.values 和 Object.entries 于 ES2017 加入。它们分别返回对象的自有可枚举字符串键、值或键值对数组。Symbol 键不会包含在结果中。对普通对象，数组索引字符串键先按数值升序排列，其余字符串键按创建顺序排列。代理或其他特殊对象不一定遵循普通对象的顺序。

```javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]

const keyOrder = {};
keyOrder["4294967296"] = "large integer, not an array index";
keyOrder["4294967295"] = "one past the maximum array index";
keyOrder["2"] = "array index";
Object.keys(keyOrder); // ["2", "4294967296", "4294967295"]

for (const [key, value] of Object.entries(record)) {
  console.log(key, value);
}
```

For a plain dictionary, remember that own-property checks and inherited properties are different questions. See [JavaScript Types and Coercion / JavaScript 类型与类型转换](#10.%20JavaScript%20Types%20/%20JavaScript%E7%B1%BB%E5%9E%8B). / 普通对象作字典时，要区分自有属性与继承属性。详见[JavaScript 类型与类型转换](#10.%20JavaScript%20Types%20/%20JavaScript%E7%B1%BB%E5%9E%8B)。

#### Array methods / Array 方法

##### Array.from(arrayLikeOrIterable, mapFn?)

Creates a new array from an iterable or array-like input, optionally mapping each value as it is created. Array-like input is read by index, so a missing index is observed as undefined in the result. / 从可迭代对象或类数组输入创建新数组，并可在创建时映射元素。类数组输入按索引读取，因此缺失索引会在结果中表现为 undefined。

```javascript
const arrayLike = { 0: "a", 1: "b", length: 2 };
Array.from(arrayLike); // ["a", "b"]

Array.from(new Set([1, 2, 2, 3])); // [1, 2, 3]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]

Array.from([, "x"]); // [undefined, "x"]
```

##### Array.of(...items)

Creates an array from its arguments. It avoids the Array constructor’s special treatment of a single numeric argument as a requested length. / 根据参数创建数组，避免 Array 构造器把单个数字参数特殊解释为数组长度。

```javascript
Array(3);    // an array of length 3 with three holes
Array.of(3); // [3]
Array.of(1, 2, 3); // [1, 2, 3]
```

See [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys) for the ordinary-object order, plus [fundamental objects](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) and [indexed collections](https://tc39.es/ecma262/2025/multipage/indexed-collections.html) for the other methods. / 普通对象的属性顺序见 [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)；其他方法见 [基础对象](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) 与 [索引集合](https://tc39.es/ecma262/2025/multipage/indexed-collections.html)。

**Interview answer / 面试回答:** Object.assign mutates its target and shallow-copies enumerable own string and symbol properties. Object.keys/values/entries inspect own enumerable string-keyed properties. Array.from accepts iterables and array-like objects; Array.of treats each argument as an element, including a single number. / Object.assign 会修改目标对象，并浅拷贝自有可枚举字符串键和 Symbol 键。Object.keys/values/entries 只处理自有可枚举字符串键。Array.from 接受可迭代对象和类数组对象；Array.of 把每个参数都作为元素，包括单个数字参数。

Related: [JavaScript Arrays / JavaScript 数组](#13.%20JavaScript%20Arrays%20/%20JavaScript%20%E6%95%B0%E7%BB%84); [Modern JavaScript Features / 现代 JavaScript 特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7).
## 15. Other JavaScript Topics / JavaScript其他内容

### Other JavaScript Topics / JavaScript 其他主题

**Key terms / 关键词:** strict mode 严格模式 · floating-point binary64 浮点数 · equality 相等比较 · truthiness 真值转换

This note collects a few distinct language details that are useful when reading or reviewing JavaScript: strict mode, floating-point comparison, equality, and boolean conversion. / 本笔记收录几项阅读或审查 JavaScript 时常用的语言知识：严格模式、浮点比较、相等比较与布尔转换。

#### Strict mode / 严格模式

Strict mode changes selected language behaviors, including undeclared assignment, duplicate parameter names, and the default `this` value for a plain function call. ES modules and class bodies are automatically strict. A classic script can opt in with a directive; a function can opt in with a directive at the start of its body. / 严格模式会改变部分语言行为，包括未声明赋值、重复形参，以及普通函数调用时的默认 `this`。ES 模块和 class 函数体自动采用严格模式；经典脚本可在开头添加指令，函数也可在函数体开头添加指令。

```javascript
"use strict";
undeclaredName = 1; // ReferenceError

function inspectThis() {
  return this;
}
inspectThis(); // undefined in strict mode
```

Strict mode does not make `eval` safe, and class or module code is already strict. / 严格模式不会让 `eval` 变安全；class 和模块代码本身已经是严格模式。

Other recognizable differences include rejecting `with`, rejecting legacy octal numeric literals and duplicate parameter names in strict functions, and throwing rather than silently ignoring some writes to non-writable properties. / 其他常见差异包括禁止 `with`、禁止旧式八进制数字字面量和严格函数中的重复形参，以及对某些不可写属性的赋值由静默忽略改为抛错。

#### Floating-point comparison / 浮点数比较

JavaScript Number uses IEEE 754 binary64. Many decimal fractions, including 0.1 and 0.2, have no exact finite binary representation, so arithmetic can produce a nearby representable value. The acceptable error depends on the domain and magnitude; choose a domain-specific tolerance instead of a universal epsilon. / JavaScript Number 使用 IEEE 754 binary64。许多十进制小数（如 0.1、0.2）无法用有限二进制位精确表示，因此计算结果可能是邻近的可表示值。可接受误差取决于领域和数值大小，应按具体场景设定容差，而不是套用统一 epsilon。

```javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // true for this scale and example
```

For money, use integer minor units when the currency’s rules allow it, or use a decimal arithmetic library with an explicit rounding policy. / 金额计算可在币种规则允许时使用整数最小单位，或使用明确指定舍入策略的十进制运算库。

#### Equality: `==`, `===`, and `Object.is` / 相等比较

`===` avoids coercion between different types. `==` follows a set of conversion rules rather than one simple “convert both to the same type” rule; it includes the special `null == undefined` case. Prefer `===` unless coercion is an intentional part of the condition. / `===` 不会在不同类型之间进行隐式转换。`==` 遵循一组转换规则，不能简单概括为“双方都转成同一类型”；其中包括特殊规则 `null == undefined`。除非有意依赖转换规则，否则优先用 `===`。

```javascript
5 == "5";           // true
5 === "5";          // false
null == undefined;  // true
null === undefined; // false
NaN === NaN;        // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

For ordinary values, the deliberate nullish check `value == null` matches `null` or `undefined`; use it only when both are meant to share a branch. `Object.is` differs from strict equality for NaN and signed zero; Map and Set use SameValueZero instead. / 对普通值而言，有意使用的空值判断 `value == null` 会匹配 `null` 或 `undefined`；仅在二者确实走同一分支时使用。`Object.is` 与严格相等对 NaN 和有符号零的处理不同；Map 与 Set 则使用 SameValueZero。

#### Boolean conversion / 布尔转换

`Boolean(value)` and `!!value` both apply truthiness conversion. For ordinary values, empty strings, zero, `NaN`, `null`, `undefined`, and `false` are falsy; ordinary objects, including empty arrays and empty objects, are truthy. Choose either spelling according to the surrounding code style; no useful general speed claim follows from the syntax. / `Boolean(value)` 和 `!!value` 都执行真值转换。对普通值而言，空字符串、零、`NaN`、`null`、`undefined` 和 `false` 为假值；包括空数组和空对象在内的普通对象都是真值。按代码风格选择写法，不应据此作普遍性能判断。

Browser compatibility exception: `document.all` has the legacy `[[IsHTMLDDA]]` behavior: it is falsy, `typeof document.all` is `"undefined"`, and it loosely equals both nullish values (`document.all == null`). It is not an ordinary object. / 浏览器兼容性例外：`document.all` 具有历史 `[[IsHTMLDDA]]` 行为，会被判为假值，`typeof document.all` 为 `"undefined"`，且与两种空值都宽松相等（`document.all == null`）。它不是普通对象。

See [ECMAScript Annex B `[[IsHTMLDDA]]`](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot). / 详见 [ECMAScript 附录 B `[[IsHTMLDDA]]`](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。

When rendering with React, `&&` returns one of its operands rather than a Boolean. If the left operand is `0`, that `0` may be rendered. Use an explicit Boolean condition when the result should be either a component or nothing. / 在 React 中，`&&` 返回操作数之一，而不是布尔值。若左侧为 `0`，结果中的 `0` 可能被渲染。希望结果只能是组件或空内容时，应显式转换为布尔条件。

```jsx
{items.length > 0 && <ItemList items={items} />}
```

See React’s [conditional rendering documentation](https://react.dev/learn/conditional-rendering). / 详见 React 的[条件渲染文档](https://react.dev/learn/conditional-rendering)。

**Interview answer / 面试回答:** Strict mode removes selected legacy behaviors but is not a security sandbox. Number comparisons need domain-specific tolerance because decimal fractions may not be represented exactly. Use `===` by default; use `== null` only when intentionally matching nullish values. Ordinary objects are truthy, with the legacy browser `document.all` exception. / 严格模式移除部分历史行为，但不是安全沙箱。由于十进制小数可能无法精确表示，数值比较应按领域选择容差。默认使用 `===`；只有在有意匹配空值时才使用 `== null`。普通对象都是真值，浏览器历史兼容对象 `document.all` 是例外。

See [ECMAScript equality and coercion](https://tc39.es/ecma262/2025/multipage/abstract-operations.html) for the normative rules. / 相等与类型转换的规范规则见 [ECMAScript 抽象操作](https://tc39.es/ecma262/2025/multipage/abstract-operations.html)。
## 16. Modern JavaScript Features / 现代JavaScript特性

### Modern JavaScript Features / 现代 JavaScript 特性

**Key terms / 关键词:** optional chaining 可选链 · nullish coalescing 空值合并 · promise combinator Promise 组合方法 · structured clone 结构化克隆 · module 模块

This is a selected reference to commonly used standardized features, not a complete catalog of “modern JavaScript.” A feature’s edition and its runtime availability are separate questions: check the runtime or build target before relying on it. / 这里选列常用的标准化特性，并非“现代 JavaScript”完整目录。特性属于哪个版本与目标运行时是否支持是两个问题；依赖某项特性前应检查运行时或构建目标。

#### Optional chaining and nullish coalescing / 可选链与空值合并

Optional chaining stops only when the value immediately before the chain is `null` or `undefined`; it does not test general falsiness. A missing root identifier still throws, and grouping ends a chain. / 可选链只在链上前一个值为 `null` 或 `undefined` 时短路，不判断一般假值。根标识符不存在时仍会抛错，括号分组也会结束链式短路。

```javascript
const user = { profile: null };
user.profile?.name; // undefined
const count = 0;
count?.toFixed(0); // "0"

const key = "value";
const object = { value: 1 };
object?.[key]; // 1
const maybeCall = undefined;
maybeCall?.(); // undefined

const settings = {};
settings.timeout ?? 1000; // 1000
settings.timeout || 1000; // 1000
0 ?? 1000; // 0
0 || 1000; // 1000
```

Use `??` when only nullish values should trigger a fallback; use `||` when all falsy values should. Parenthesize when mixing `??` with `||` or `&&`; unparenthesized mixing is a syntax error. / 只有 nullish 值应触发默认值时用 `??`；所有假值都应触发时用 `||`。`??` 与 `||` 或 `&&` 混用时应加括号，不加括号会产生语法错误。

#### Destructuring, rest, and template literals / 解构、剩余项与模板字符串

Destructuring and template literals were standardized in ES2015; object rest/spread was standardized in ES2018. Destructuring reads properties or iterable values into bindings. Defaults apply when the extracted value is `undefined`, not for every falsy value. Object rest gathers remaining own enumerable properties; array rest consumes the remaining iterable values. / 解构和模板字符串属于 ES2015；对象剩余项/展开属于 ES2018。解构把属性或可迭代值读入绑定。默认值只在取出的值为 `undefined` 时生效，不适用于所有假值。对象剩余项收集其余自有可枚举属性；数组剩余项消费迭代器中的剩余值。

```javascript
const { name: displayName, active = true, ...extra } = user;
const [first, , ...tail] = ["a", "b", "c"];
const greeting = `Hello, ${displayName}!`
```

Tagged templates pass cooked string segments and interpolated values separately. They are useful for formatting or domain-specific processing; they do not sanitize input automatically. / 带标签模板会分别传入处理后的字符串片段和插值。它可用于格式化或特定领域处理，但不会自动净化输入。

#### Promise combinators / Promise 组合方法

| Method / 方法 | Edition / 版本 | Fulfillment / 成功条件 | Rejection / 失败条件 |
|---|---|---|---|
| `Promise.all` | ES2015 | Every input fulfills / 全部成功 | An input rejects / 某项失败 |
| `Promise.allSettled` | ES2020 | Every input settles; returns each outcome / 全部结束并返回每项结果 | Normally does not reject for an input rejection / 不因某项输入拒绝而拒绝 |
| `Promise.any` | ES2021 | First input fulfills / 首个成功项 | All inputs reject; rejects with `AggregateError` / 全部失败时以 `AggregateError` 拒绝 |
| `Promise.race` | ES2015 | First settlement is fulfillment / 首个完成项成功 | First settlement is rejection / 首个完成项拒绝 |

The specification installs both fulfillment and rejection reactions for each input in [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace). / 规范中的 [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace) 会为每项输入同时安装成功和拒绝处理器。

`all`, `any`, and `race` settle the returned promise early when their condition is met, but do not cancel the other work. Passing promises usually starts their underlying operations before the combinator is called. Use an explicit cancellation mechanism, such as AbortController when supported by the API, if losing work should stop. / 当满足条件时，`all`、`any` 和 `race` 会提前完成返回的 Promise，但不会取消其他任务。传入的 Promise 通常已在调用组合方法前启动底层操作。若需停止未获胜的任务，应使用 API 支持的取消机制，例如 AbortController。

#### Selected APIs and editions / 部分 API 与版本

- `globalThis` — ES2020 access to the current realm’s global object; its host-specific properties differ. / ES2020 提供当前 realm 的全局对象入口；其属性因宿主环境而异。
- `Array.prototype.at(index)` — ES2022 indexing with negative offsets from the end. / ES2022 索引方法，支持从末尾反向计数。
- `Object.hasOwn(object, key)` — ES2022 own-property test that works with null-prototype objects and overridden `hasOwnProperty`. / ES2022 自有属性判断，可用于 null 原型对象或覆盖了 `hasOwnProperty` 的对象。
- `structuredClone(value)` — a host API, not an ECMAScript edition feature. Browsers and current Node releases expose it ([Node global API](https://nodejs.org/api/globals.html#structuredclonevalue-options)). It clones structured-cloneable values and supports cycles and built-in data such as Map, Set, and Date. It does not preserve custom class prototypes or clone functions; unsupported values can throw `DataCloneError`. Do not assume it is faster than another method. / 这是宿主 API，不属于某个 ECMAScript 版本特性；浏览器和当前 Node 版本均提供该方法（见 [Node 全局 API](https://nodejs.org/api/globals.html#structuredclonevalue-options)）。它可复制结构化克隆支持的值，支持循环引用以及 Map、Set、Date 等内置数据；不会保留自定义类原型，也不能克隆函数；不支持的值可能抛出 `DataCloneError`。不要假设它必然比其他方法快。
- `Object.assign` and `Object.is` are ES2015. `Object.keys` is ES5; `Object.values` and `Object.entries` are ES2017. / `Object.assign` 和 `Object.is` 属于 ES2015。`Object.keys` 属于 ES5；`Object.values` 和 `Object.entries` 属于 ES2017。

```javascript
const values = ["first", "last"];
values.at(-1); // "last"

const options = Object.create(null);
options.enabled = false;
Object.hasOwn(options, "enabled"); // true
```

#### Modules: language and host boundaries / 模块：语言与宿主边界

ECMAScript modules are part of the language: static `import` / `export`, module-scoped bindings, strict mode, and top-level `this === undefined`. Top-level await was standardized in ES2022. Dynamic `import()` returns a Promise and is supported by both Node module systems. CommonJS (`require`, `module.exports`) is Node’s module wrapper, not ECMAScript module syntax. / ECMAScript 模块属于语言规范：使用静态 `import` / `export`，绑定具有模块作用域，自动采用严格模式，顶层 `this === undefined`。顶层 await 于 ES2022 标准化。动态 `import()` 返回 Promise，Node 两种模块系统都可使用。CommonJS（`require`、`module.exports`）是 Node 的模块包装机制，不是 ECMAScript 模块语法。

These two `.mjs` files show static imports/exports and a dynamic import of the same module. / 以下两个 `.mjs` 文件演示静态导入/导出，以及对同一模块进行动态导入。

```javascript
// features.mjs
export const featureName = "search";
export default function createFeature() {
  return featureName;
}
```

```javascript
// app.mjs
import createFeature, { featureName } from "./features.mjs";
export { featureName };

createFeature(); // "search"
import("./features.mjs").then(({ featureName }) => featureName);
```

| Concern / 维度 | ECMAScript module / ES 模块 | Node CommonJS / Node CommonJS |
|---|---|---|
| Static syntax / 静态语法 | `import`, `export` | `require()`, `module.exports` |
| Top-level await / 顶层 await | Supported / 支持 | Not supported in a CJS wrapper / CJS 包装器中不支持 |
| Top-level `this` / 顶层 `this` | `undefined` | Node wrapper’s `exports` value / Node 包装器的 `exports` 值 |
| Tree shaking / Tree shaking | Depends on bundler and package metadata / 取决于打包器和包元数据 | Not guaranteed by the format / 模块格式不保证 |

A bundler may analyze ESM imports for tree shaking, but ESM syntax alone does not guarantee code removal. Node decides whether a file is ESM or CJS using extensions, package settings, or explicit input flags; browser module loading follows browser rules. / 打包器可以分析 ESM 导入以执行 tree shaking，但仅使用 ESM 语法不保证代码一定被移除。Node 会根据扩展名、包设置或显式输入参数确定文件属于 ESM 还是 CJS；浏览器模块加载则遵循浏览器规则。

**Interview answer / 面试回答:** Optional chaining checks nullish values, while `??` preserves valid falsy values. Promise combinators aggregate outcomes but do not cancel work. ESM is standardized JavaScript syntax; CommonJS is a Node module system, and bundler behavior such as tree shaking depends on tooling. / 可选链检查 nullish 值，`??` 会保留有效的假值。Promise 组合方法聚合结果，但不会取消任务。ESM 是标准 JavaScript 模块语法；CommonJS 是 Node 模块系统，tree shaking 等行为取决于工具链。

See the [ECMAScript language specification](https://tc39.es/ecma262/2025/) for edition-specific features and the [HTML structured clone algorithm](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) for the host API. / 版本相关语言特性见 [ECMAScript 语言规范](https://tc39.es/ecma262/2025/)；宿主结构化克隆 API 见 [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)。

Related: [Object and Array Methods / 对象与数组方法](#14.%20ES6%20New%20Methods%20/%20ES6%E6%96%B0%E5%A2%9E%E6%96%B9%E6%B3%95); [Asynchronous JavaScript / 异步 JavaScript](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript).
## 17. Object, Function, and Prototype / 对象、函数与原型

### Objects, Functions, and Prototypes / 对象、函数与原型

**Key terms / 关键词:** internal prototype 内部原型 · constructor 构造函数 · receiver 接收者 · property descriptor 属性描述符 · constructible 可构造

JavaScript objects delegate property lookup through an internal prototype link. Function call syntax determines the receiver for ordinary functions; arrow functions capture it lexically. These rules explain inheritance, this, new, and descriptors without assuming a particular engine memory layout. / JavaScript 对象通过内部原型链接委托属性查找。普通函数的调用语法决定接收者；箭头函数从词法作用域捕获接收者。这些规则可解释继承、this、new 和属性描述符，无需假设特定引擎的内存布局。

#### Prototype lookup / 原型查找

Each ordinary object has an internal `[[Prototype]]` value, which may be null. If a property is not found on the object, lookup continues through that prototype chain. Use Object.getPrototypeOf and Object.create for explicit work with the chain. / 每个普通对象都有一个内部 `[[Prototype]]` 值，也可能为 null。对象上找不到属性时，会沿原型链继续查找。显式操作原型链时应使用 Object.getPrototypeOf 和 Object.create。

Many constructible function objects have an own property named `prototype`, which supplies the prototype for instances created by `new` when its value is an object. It is not present on every function: arrow functions and methods are not constructible and do not have it. The expression `__proto__` is a legacy accessor inherited from Object.prototype, not a special own property on every object. Prefer `Object.getPrototypeOf(obj)`. / 许多可构造函数对象都有名为 `prototype` 的自有属性；当其值为对象时，`new` 会将其用作实例原型。并非所有函数都有该属性：箭头函数和方法不可构造。表达式 `__proto__` 是从 Object.prototype 继承的历史访问器，并非每个对象都有的特殊自有属性。优先使用 `Object.getPrototypeOf(obj)`。

```javascript
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
```

```javascript
const ordinary = {};
Object.getPrototypeOf(ordinary) === Object.prototype; // true

const custom = Object.create({ greet: "hello" });
custom.greet; // inherited value

const dictionary = Object.create(null);
dictionary.toString; // undefined
```

The legacy Object.prototype.__proto__ accessor is documented as normative optional and legacy in ECMAScript. / ECMAScript 将历史 Object.prototype.__proto__ 访问器标为可选实现的历史特性，详见[规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.__proto__)。

#### this is determined by the call / this 由调用方式决定

For an ordinary function, the call expression supplies the receiver. A method call obj.fn() supplies obj; a plain call to a strict function supplies undefined, while a plain sloppy-mode call substitutes the host’s global this value. In browser classic scripts that global is generally window; Node module wrappers have their own top-level conventions. / 对普通函数而言，调用表达式提供接收者。obj.fn() 这样的调用以 obj 为接收者；严格模式下普通函数调用的接收者是 undefined，非严格模式下则替换为宿主的全局 this。浏览器经典脚本中的全局对象通常是 window；Node 模块包装器有自己的顶层约定。

new creates a receiver; call/apply pass an explicit this value; bind creates a function with a bound receiver and leading arguments. A bound function used with new ignores its bound receiver, but keeps the bound arguments. Arrow functions use the surrounding this and cannot be rebound with call/apply/bind. / new 会创建接收者；call/apply 显式传入 this；bind 创建带绑定接收者和前置参数的新函数。绑定函数通过 new 调用时会忽略绑定接收者，但仍使用绑定参数。箭头函数使用外层 this，call/apply/bind 无法重新绑定它。

```javascript
const service = {
  url: "/data",
  fetch() { return this.url; }
};

service.fetch(); // "/data"
const detached = service.fetch;
detached(); // no longer uses service as its receiver

function describe(prefix, name) {
  return prefix + " " + name + " (" + this.role + ")";
}
describe.call({ role: "admin" }, "Hello", "Ada");
describe.apply({ role: "admin" }, ["Hello", "Ada"]);
const greetAdmin = describe.bind({ role: "admin" }, "Hello");
greetAdmin("Ada");
```

##### Small binding exercise / 简化绑定练习

This helper demonstrates partial application for functions called with object receivers. It is not a replacement for Function.prototype.bind: native bind also handles constructor calls, constructibility, and function metadata. / 以下辅助函数演示对象接收者上的部分应用，并非 Function.prototype.bind 的替代品：原生 bind 还处理构造调用、可构造性和函数元数据。

```javascript
function bindForObjectReceiver(fn, receiver, ...leadingArgs) {
  return function (...laterArgs) {
    return fn.apply(receiver, [...leadingArgs, ...laterArgs]);
  };
}
```

Likewise, assigning a function to a temporary property can explain how a method call supplies this. This limited example only accepts an extensible object receiver and does not model primitive receivers or all exotic objects. A complete call/apply polyfill must also model strict functions, null/undefined, exceptions, and proxies. Use the built-ins in application code. / 把函数临时赋给对象属性可以说明方法调用如何提供 this。以下简化示例只接受可扩展对象接收者，不能处理原始值接收者或所有特殊对象。完整模拟 call/apply 还必须处理严格函数、null/undefined、异常和代理。应用代码应使用内置方法。

```javascript
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
```

#### What new does / new 的行为

For a constructible function, new creates an object with the constructor’s effective prototype, calls the constructor with that object as this, and returns the explicit object/function result if one is returned. Primitive return values are ignored. Classes and built-ins have additional construction semantics. / 对可构造函数，new 会创建一个原型为构造函数有效原型的对象，以该对象作为 this 调用构造函数；若构造函数返回对象或函数，则返回该值，否则返回新对象。原始值返回会被忽略。class 和内置构造器还有额外语义。

The specification’s [`GetPrototypeFromConstructor`](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) operation accepts any object-valued `prototype`, including a function, and otherwise uses the constructor realm’s intrinsic fallback. / 规范的 [`GetPrototypeFromConstructor`](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) 会接受任何对象类型的 `prototype`（包括函数）；若不是对象，则使用构造函数所在 realm 的内置回退原型。

The following is a teaching model for ordinary constructors from the current realm; it is not a full polyfill for classes, bound functions, built-ins, proxies, or new.target. / 以下仅为当前 realm 中普通构造函数的教学模型，并非 class、绑定函数、内置构造器、代理或 new.target 的完整 polyfill。

```javascript
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

function CallablePrototype() {}
function Example() {}
Example.prototype = CallablePrototype;
const example = emulateNew(Example);
Object.getPrototypeOf(example) === CallablePrototype; // true
```

#### Methods and fields / 方法与字段

A function assigned in a constructor creates an own function property for each instance; a prototype method is shared through lookup. Choose based on per-instance state, identity, and behavior rather than assuming the prototype version is always faster. In class syntax, ordinary methods are placed on the prototype; instance fields create own properties on each instance; static methods and fields belong to the class constructor. / 在构造函数中赋值的函数会为每个实例创建自有函数属性；原型方法通过查找共享。应按实例状态、身份和行为选择，而不要假设原型方法一定更快。class 语法中的普通方法放在原型上；实例字段为每个实例创建自有属性；静态方法和字段属于类构造函数。

```javascript
class User {
  label = "member"; // own instance field
  greet() { return "Hi"; } // shared prototype method
  static category = "account"; // property on the class constructor
}

const user = new User();
Object.hasOwn(user, "label"); // true
Object.hasOwn(user, "greet"); // false
Object.hasOwn(User, "category"); // true
```

#### Hidden classes are engine internals / 隐藏类属于引擎实现

V8 uses HiddenClasses (also called Maps) to track object shapes and optimize property access. Objects initialized with the same named properties in the same order can share a shape in V8. This is implementation-specific and may change; optimize object layouts only when profiling shows a real cost. / V8 使用 HiddenClasses（也称 Maps）跟踪对象形状并优化属性访问。在 V8 中，以相同顺序初始化相同命名属性的对象可能共享形状。这是实现细节，未来可能改变；只有性能分析显示确有成本时才优化对象布局。

The V8-specific mechanism and examples are described in [Fast properties in V8](https://v8.dev/blog/fast-properties). They are not ECMAScript guarantees. / V8 的具体机制与示例见 [V8 快速属性说明](https://v8.dev/blog/fast-properties)，这些不是 ECMAScript 保证。

#### Static, instance, and prototype properties / 静态、实例与原型属性

Constructor properties, own instance properties, and prototype properties live on different objects. Own properties are found before inherited properties; a static property on the constructor is not part of an instance’s prototype lookup. / 构造函数属性、实例自有属性和原型属性属于不同对象。查找时先看自有属性，再看继承属性；构造函数上的静态属性不属于实例的原型查找链。

```javascript
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
```

#### Property descriptors / 属性描述符

Own properties have attributes. Data properties use value and writable; accessor properties use get and set. Both kinds have enumerable and configurable. Object.defineProperty lets code set these explicitly. / 自有属性有属性特征。数据属性使用 value 和 writable；访问器属性使用 get 和 set。两类属性都有 enumerable 和 configurable。Object.defineProperty 可显式设置这些特征。

| Attribute / 特征 | Meaning / 含义 |
|---|---|
| value | Stored value / 存储值 |
| writable | Whether assignment may change a data property / 赋值是否可修改数据属性 |
| get / set | Accessor functions used on read or write / 读取或写入时调用的访问器函数 |
| enumerable | Included by own enumerable key APIs; for...in also walks the prototype chain / 自有可枚举键 API 会包含；for...in 还会遍历原型链 |
| configurable | Whether the property can generally be deleted or reconfigured / 通常能否删除或重新配置 |

```javascript
const record = {};
Object.defineProperty(record, "id", {
  value: 7,
  writable: false,
  enumerable: true,
  configurable: false
});

Object.getOwnPropertyDescriptor(record, "id");
// { value: 7, writable: false, enumerable: true, configurable: false }
```

An accessor can compute or validate a value on read or write. / 访问器可在读取或写入时计算或校验值。

```javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true
});

profile.name; // "John" — calls the getter
profile.name = "Jo"; // calls the setter
profile._name; // "Jo"
```

An assignment to a non-writable property is ignored in sloppy code and throws in strict code. / 非严格代码中，对不可写属性赋值会被忽略；严格代码中会抛错。

**Interview answer / 面试回答:** Objects inherit through an internal prototype link. An object created by `constructorFn` normally inherits from that constructor’s object-valued `constructorFn.prototype`; this differs from `Function.prototype`, which function objects themselves typically inherit through their internal prototype link. `__proto__` is a legacy accessor. For ordinary functions, `this` follows the call form; arrows capture it lexically. `new` constructs an instance, and own properties shadow prototype properties. / 对象通过内部原型链接继承属性。由 `constructorFn` 创建的对象通常继承自其对象类型的 `constructorFn.prototype`；这与函数对象自身通常通过内部原型链接继承的 `Function.prototype` 不同。`__proto__` 是历史访问器。普通函数的 `this` 由调用方式决定；箭头函数从外层词法捕获。`new` 构造实例，自有属性会遮蔽原型属性。

See the [ECMAScript Object and Function sections](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) for normative behavior. / 规范行为详见 [ECMAScript Object 与 Function 章节](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html)。

Related: [JavaScript Types and Coercion / JavaScript 类型与类型转换](#10.%20JavaScript%20Types%20/%20JavaScript%E7%B1%BB%E5%9E%8B); [Scope and Closure / 作用域与闭包](#18.%20Scope%20&%20Closure%20/%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85).
## 18. Scope & Closure / 作用域与闭包

### Scope & Closure / 作用域与闭包

> **核心解释 / Core idea：** 作用域（scope）决定一个绑定（binding）可以在哪里被查找；闭包（closure）让函数继续访问其定义时外层词法环境中的绑定。  
> **Interview answer / 面试简答：** Scope is lexical: names are resolved from where a function is defined, not where it is called. A closure keeps access to captured bindings after the outer function returns, while those bindings can still change. / 作用域由代码定义位置决定，而非调用位置；外层函数返回后，闭包仍可访问捕获的绑定，且读取的是该绑定的当前值。

#### 作用域与名称查找 / Scope and name resolution

作用域描述标识符在哪段代码中可见。JavaScript 按词法结构解析名称：先查当前环境，再沿外层环境逐层查找；到达最外层仍找不到时，读取会产生 `ReferenceError`。引擎用执行上下文与词法环境（lexical environment）描述这套关系；这是规范模型，不要求实现必须用同名的内存对象。[ECMAScript 规范的执行上下文与环境记录](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html)和 [MDN 闭包指南](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)提供了标准定义与示例。

##### 全局作用域（global scope）

“全局”取决于宿主环境。跨环境代码可用 `globalThis` 指向当前全局对象；浏览器窗口通常是 `window`，Web Worker 使用自己的全局对象。在浏览器的经典非模块脚本顶层，`var` 和函数声明会成为全局对象属性；顶层 `let`、`const` 不会。

~~~html
<script>
  var scriptVar = 'global object property';
  let scriptBinding = 'global lexical binding';

  console.log(window.scriptVar);     // 'global object property'
  console.log(window.scriptBinding); // undefined
</script>
~~~

模块顶层是模块作用域，不会因为写在文件顶层就自动成为 `window` 属性。脚本和模块语义不同，阅读顶层声明时要先确认代码以哪种方式执行。

宿主对全局对象的提供方式有所不同；跨环境代码可用 `globalThis` 访问当前全局对象。关于[全局对象与脚本顶层声明](https://developer.mozilla.org/en-US/docs/Glossary/Global_object)及 [`let` 的作用域和暂时性死区](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)，可参见MDN说明。

##### 函数作用域与块级作用域 / Function and block scope

`var` 的作用域是最近的函数；函数外声明时，它属于脚本的全局环境或模块环境。它不会因 `if`、`for` 或普通代码块而缩小范围。`let`、`const` 则属于最近的块，包括 `if`、`switch`、循环和独立的 `{}`；模块顶层的 `let`、`const` 属于该模块。

~~~javascript
function example() {
  if (true) {
    var functionScoped = 'visible in the function';
    let blockScoped = 'visible only in this block';
  }

  console.log(functionScoped); // 'visible in the function'
  console.log(blockScoped);    // ReferenceError
}
~~~

`let` 和 `const` 声明也会在进入作用域时建立绑定，但在执行到声明前处于暂时性死区（temporal dead zone）；此时读取会抛出 `ReferenceError`。因此，更准确的做法是“用 `let` / `const` 获得块级作用域和更早的错误检查”，而不是说它们完全没有提升。`const` 禁止重新给绑定赋值，但若绑定指向对象，对象内容仍可变。更完整的声明对比见 [JavaScript 基础](#9.%20JavaScript%20Basics%20/%20JavaScript%E5%9F%BA%E7%A1%80)。

##### 词法作用域（lexical scope）与作用域链（scope chain）

函数从定义它的位置取得外层作用域。调用者自己的局部变量不会插入被调用函数的词法作用域链。

~~~javascript
const label = 'global';

function outer() {
  const label = 'outer';

  function inner() {
    const detail = 'inner';
    return [label, detail];
  }

  return inner;
}

function callFromElsewhere() {
  const label = 'caller';
  return outer()();
}

console.log(callFromElsewhere()); // ['outer', 'inner']
~~~

这里 `inner` 先查自己的 `detail`，再查 `outer` 的 `label`，最后才可能查到全局环境；`callFromElsewhere` 的 `label` 不参与查找。

#### 闭包（closure）：函数与其定义时的词法环境

<a id="note-5022c0a9e63a-a1"></a>
<a id="note-5022c0a9e63a-a2"></a>

闭包是函数与其定义时可访问的词法环境之间的关系。JavaScript 函数创建时就带有这种词法访问能力；当内层函数在外层函数返回后仍可被调用时，这种能力就特别明显。闭包访问的是变量绑定，不是创建函数那一刻复制出来的值。[MDN 的闭包说明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)展示了这一行为。

~~~javascript
function makeReader() {
  let state = 'before';
  const read = () => state;

  state = 'after';
  return read;
}

const readState = makeReader();
console.log(readState()); // 'after'
~~~

`readState` 读取同一个 `state` 绑定，所以外层函数返回前的赋值可被看到。若每次调用 `makeReader`，则每次都有独立的 `state`。

##### 闭包的常见用途 / Common uses

**私有状态（private state）。** 返回多个共享同一环境的操作，可以让状态不作为对象属性暴露：

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
counter.count;       // undefined: count 不是对象属性
~~~

每次调用 `makeCounter` 都会创建一份独立状态。这是一种封装方式；现代 JavaScript 也提供 class 私有字段等其他机制。

**函数工厂与偏应用（function factory / partial application）。** 参数可被闭包固定下来，生成用途不同的函数：

~~~javascript
function multiplyBy(factor) {
  return (number) => number * factor;
}

const double = multiplyBy(2);
const triple = multiplyBy(3);

double(5); // 10
triple(5); // 15
~~~

**事件回调（event callback）。** 回调可访问注册时所在作用域里的变量：

~~~javascript
function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener('click', () => {
    console.log('Clicked: ' + label);
  });
}

attachLogger('btn1', 'primary');
attachLogger('btn2', 'secondary');
~~~

两个回调各自通过调用 `attachLogger` 时创建的环境读取自己的 `label`。

##### 循环中的 `var` 与 `let` / Loop bindings

`var` 在循环外的函数作用域内只有一个绑定；循环结束后，延迟执行的回调会读到它的最终值。循环头使用 `let` 时，每次迭代有独立的绑定：

~~~javascript
const varCallbacks = [];
for (var i = 0; i < 5; i++) {
  varCallbacks.push(() => i);
}

const letCallbacks = [];
for (let j = 0; j < 5; j++) {
  letCallbacks.push(() => j);
}

console.log(varCallbacks.map((callback) => callback())); // [5, 5, 5, 5, 5]
console.log(letCallbacks.map((callback) => callback())); // [0, 1, 2, 3, 4]
~~~

若旧代码必须使用 `var`，IIFE（立即调用函数表达式）也可为每次迭代创建一份参数绑定：

~~~javascript
const callbacks = [];
for (var index = 0; index < 5; index++) {
  (function (capturedIndex) {
    callbacks.push(() => capturedIndex);
  })(index);
}

console.log(callbacks.map((callback) => callback())); // [0, 1, 2, 3, 4]
~~~

现代代码通常直接用 `let` 或 `const` 表达每轮迭代的绑定，避免额外包装函数。

##### 闭包与内存生命周期 / Closures and memory lifetime

函数返回并不意味着它创建的局部绑定立即失效：只要某个可达闭包仍能读取这些绑定，程序就必须保留可观察到的行为。但不能据此推断“整个外层作用域中的每个变量都必然一直占用内存”；引擎可以优化未被使用的内容，而垃圾回收器何时回收不可达对象也不由源码中的作用域结束时刻决定。

实际需要关注的是引用路径：长期保存的回调若读取大型对象，就可能让该对象继续可达。事件监听器会持有回调；不再需要时，移除监听器并释放其他回调引用，才可能让相关对象变为可回收。单纯存在循环引用不等于泄漏；关键是对象图是否仍从程序可达。关于闭包可能带来的性能和内存成本，参见 [MDN 性能说明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures#performance_considerations)。

#### 复习要点 / Takeaways

- `var` 是函数级（或脚本/模块顶层）绑定；`let`、`const` 是块级绑定。
- 词法作用域按函数定义位置查找；调用位置不改变外层查找链。
- 闭包保留对绑定的访问，读到的可以是后续更新后的值。
- 生命周期由可达引用决定；函数离开词法作用域不等于相关数据立即释放。

**延伸阅读：** [JavaScript 基础](#9.%20JavaScript%20Basics%20/%20JavaScript%E5%9F%BA%E7%A1%80)说明声明差异；[对象、函数与原型](#17.%20Object,%20Function,%20and%20Prototype%20/%20%E5%AF%B9%E8%B1%A1%E3%80%81%E5%87%BD%E6%95%B0%E4%B8%8E%E5%8E%9F%E5%9E%8B)解释 `this` 的调用规则为何不同于词法作用域。
## 19. Asynchronous JavaScript / 异步JavaScript

### Asynchronous JavaScript / 异步 JavaScript

**Key terms / 关键词:** callback 回调 · Promise Promise 对象 · microtask 微任务 · async iterable 异步可迭代对象 · concurrency 并发

Asynchronous APIs let a program continue while work is pending, but “async” does not itself mean that JavaScript executes CPU work in parallel or that the host uses one thread. Promises were standardized in ES2015, async functions/await in ES2017, and async iteration in ES2018. Callbacks, Promises, and async/await express deferred control flow with different composition and error-handling styles. / 异步 API 让程序在等待任务时继续推进，但“异步”本身不表示 JavaScript 会并行执行 CPU 计算，也不表示宿主只有一个线程。Promise 属于 ES2015，async 函数/await 属于 ES2017，异步迭代属于 ES2018。回调、Promise 和 async/await 是表达延后控制流的不同方式，在组合能力和错误处理上各有特点。

#### Callbacks, Promises, and async/await / 回调、Promise 与 async/await

A callback passes a function to an API to be called later. Dependent callback nesting can make control flow and error paths hard to follow; callbacks are still appropriate for event handlers and many host APIs. / 回调把函数传给 API，供其稍后调用。依赖关系层层嵌套时，控制流和错误路径会难以跟踪；事件处理器和许多宿主 API 仍适合使用回调。

```javascript
readUser(userId, (error, user) => {
  if (error) return handle(error);
  readOrders(user.id, (error, orders) => {
    if (error) return handle(error);
    renderOrders(orders);
  });
});
```

A Promise represents a future fulfillment or rejection. Once settled, its state does not change. then returns another Promise, so success and failure can be composed; catch handles a rejection by recovering with a value or propagating with a throw. / Promise 表示未来的成功结果或拒绝原因。状态一旦确定就不会改变。then 返回新的 Promise，因此成功和失败流程可以组合；catch 可以通过返回值恢复，也可以通过再次抛出错误继续传播。

```javascript
const result = getUser(userId)
  .then(user => getOrders(user.id))
  .then(renderOrders)
  .catch(handleError);
```

An async function always returns a Promise. await suspends that function until its operand settles, then resumes with the fulfillment value or throws the rejection into the surrounding control flow. Code before the first suspension runs synchronously. / async 函数始终返回 Promise。await 会暂停该函数，直到操作数完成，再以成功值继续或把拒绝原因抛入当前控制流。第一个暂停点之前的代码仍同步执行。

```javascript
async function loadOrders(userId) {
  try {
    const user = await getUser(userId);
    return await getOrders(user.id);
  } catch (error) {
    handleError(error);
    throw error; // the returned Promise remains rejected
  }
}
```

#### Promise states and combinators / Promise 状态与组合方法

A Promise executor runs immediately when new Promise(executor) is called; reactions registered through then run asynchronously as Promise jobs. finally normally passes the original outcome through; if its callback throws or returns a rejected Promise, the resulting chain rejects with that new failure. / 调用 new Promise(executor) 时，executor 会立即运行；通过 then 注册的处理器则作为 Promise job 异步执行。finally 通常保留原结果；若回调抛错或返回拒绝的 Promise，后续链会以新错误拒绝。

| Method / 方法 | Returned Promise fulfills when / 成功条件 | Returned Promise rejects when / 拒绝条件 |
|---|---|---|
| Promise.all | Every input fulfills; values keep input order / 全部成功，值按输入顺序排列 | An input rejects / 任一输入拒绝 |
| Promise.allSettled | All inputs settle; each outcome is returned / 全部完成并返回每项状态 | Not because an input rejects / 不会因某项输入拒绝 |
| Promise.any | First input fulfills / 首个输入成功 | All inputs reject; AggregateError is returned / 全部拒绝时返回 AggregateError |
| Promise.race | First settlement is fulfillment / 首个完成项成功 | First settlement is rejection / 首个完成项拒绝 |

The specification installs both fulfillment and rejection reactions for each input in [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace). / 规范中的 [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace) 会为每项输入同时安装成功和拒绝处理器。

These methods coordinate already-created work; they do not cancel losing operations. If an API supports cancellation and abandoned work should stop, use its explicit mechanism, such as AbortController with Fetch. / 这些方法只协调已经创建的任务，不会取消未获胜的操作。若 API 支持取消且希望停止无用任务，应使用显式取消机制，例如 Fetch 配合 AbortController。

#### Sequential and concurrent work / 顺序执行与并发启动

Await independent operations together when they may proceed concurrently. This is concurrency, not necessarily parallel JavaScript computation: the host may overlap I/O while each JavaScript agent still runs one job at a time. / 相互独立且可同时推进的操作可一起等待。这是并发，不一定是 JavaScript 计算并行：宿主可以重叠处理 I/O，而每个 JavaScript agent 仍一次执行一个 job。

```javascript
// Dependent: the second operation needs the first result.
const user = await fetchUser(id);
const orders = await fetchOrders(user.id);

// Independent: start both before awaiting either.
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts()
]);
```

for await...of awaits values from an async iterable in iteration order. It can also adapt a synchronous iterable of Promises, but awaits each yielded value before continuing. If all operations are independent, Promise.all usually expresses both concurrency and rejection handling more directly. / for await...of 按迭代顺序等待异步可迭代对象产出的值。它也能适配由 Promise 组成的同步可迭代对象，但会在继续前等待当前值。若操作彼此独立，Promise.all 通常更直接地表达并发启动和拒绝处理。

#### Promise-job order / Promise job 顺序

Promise reactions are queued as jobs; when one handler queues another reaction, already-queued jobs run first. This explains the interleaving below. Exact checkpoints are provided by the host, so keep browser event-loop and Node scheduling rules separate. / Promise 处理器会排入 job 队列；某个处理器新增后续处理器时，队列中已存在的 job 会先运行。下面的交错顺序由此产生。具体检查点由宿主提供，因此应区分浏览器事件循环和 Node 调度规则。

```javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0, 2, 1, 3
```

Returning a Promise from a handler makes the next Promise adopt its eventual state. The timing of visible reactions follows the job queue, not a portable count of “ticks”; use a runnable example only for the runtime and context tested. / 处理器返回 Promise 时，后续 Promise 会采用它最终的状态。可观察到的处理顺序取决于 job 队列，不宜用跨环境固定的“tick 数”描述；具体示例只代表实际测试过的运行时和上下文。

```javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(value => console.log(value));

Promise.resolve().then(() => console.log(1))
  .then(() => console.log(2))
  .then(() => console.log(3));
// Node.js v26.11.1, CommonJS: 0, 1, 2, 3, 4
```

The returned Promise is adopted by the chained Promise; its reactions join the same job queue as the second chain. Do not model this as one universal “extra tick.” / 后续 Promise 会采用处理器返回的 Promise 状态；其处理器也会进入第二条链所在的 job 队列。不要把它概括为跨宿主通用的“多一个 tick”。

See [ECMAScript Promise jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) and the [browser event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops). Node queue ordering is documented separately in [Event Loop and Host Scheduling / 事件循环与宿主调度](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF). / 详见 [ECMAScript Promise job 规范](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) 与 [浏览器事件循环规范](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)。Node 队列顺序在 [事件循环与宿主调度](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF) 中单独说明。

#### Currying / 柯里化

Currying adapts a multi-argument function into a sequence of calls, allowing partial application. This compact implementation uses fn.length as the arity and supports ordinary positional functions; defaults, rest parameters, placeholders, and other arity rules need a different contract. / 柯里化把多参数函数改造成一系列调用，以支持部分应用。以下简化实现用 fn.length 作为元数，适用于普通位置参数函数；默认参数、剩余参数、占位符及其他元数规则需要另行设计。

```javascript
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
```

#### A chainable task queue / 链式异步任务队列

This LazyMan example queues actions and defers the first step so the synchronous method chain is built before execution begins. Each action calls next() only when its work is complete. Time is in milliseconds. / 这个 LazyMan 示例把操作加入队列，并延后首步执行，以便先完成同步方法链。每个任务只在自身完成后调用 next()。时间单位为毫秒。

```javascript
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
```

This is a teaching example, not a cancellation-aware production queue. A production design should define failure handling, cancellation, and what happens when a task never completes. / 这是讲解示例，不是带取消能力的生产队列。生产实现还需定义失败处理、取消方式，以及任务永不完成时的行为。

#### Arrow functions / 箭头函数

Arrow functions capture this lexically; they do not have their own this or arguments, are not constructible with new, and do not have a prototype property. Use method syntax when a method needs its receiver as this; use rest parameters for a local argument list. / 箭头函数从外层词法作用域捕获 this；它没有自己的 this 或 arguments，不能用 new 构造，也没有 prototype 属性。方法需要把接收者作为 this 时使用方法语法；需要函数自己的参数列表时使用剩余参数。

```javascript
const counter = {
  value: 1,
  read() { return this.value; },
  readArrow: () => this.value // captures surrounding this, not counter
};
```

An arrow function can still be useful as an instance field when lexical capture is intentional; call, apply, and bind cannot replace its captured this. / 若确实需要词法捕获，箭头函数也可作为实例字段；call、apply 和 bind 无法替换捕获到的 this。

#### Callback arity gotcha / 回调参数个数陷阱

The `Array.prototype.map` callback receives the value, index, and array. `parseInt` interprets its second parameter as a radix, so passing it directly to `map` changes the radix for later items. / `Array.prototype.map` 的回调会收到值、索引和数组。`parseInt` 把第二个参数解释为基数，因此直接传给 `map` 会让后续元素使用不同基数。

See the [ECMAScript `Array.prototype.map` algorithm](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map). / 详见 [ECMAScript `Array.prototype.map` 规范算法](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map)。

```javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
```

**Interview answer / 面试回答:** Promises compose asynchronous outcomes and provide a rejection channel; async/await expresses that control flow in sequential syntax. Use Promise.all for independent operations that must all succeed, but remember it does not cancel sibling work. Promise reactions are jobs; host event-loop ordering depends on the environment. / Promise 可组合异步结果并提供拒绝传播通道；async/await 用顺序语法表达这种控制流。多个独立操作都必须成功时可用 Promise.all，但它不会取消其他任务。Promise 处理器以 job 执行，宿主事件循环顺序因环境而异。

Related: [Error Handling / JavaScript 错误处理](#21.%20Error%20Handling%20/%20%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86); [Iterators and Generators / 迭代器与生成器](#20.%20Iterators%20and%20Generators%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8); [Event Loop and Host Scheduling / 事件循环与宿主调度](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF).
## 20. Iterators and Generators / 迭代器与生成器

### Iterators and Generators / 迭代器与生成器

**Key terms / 关键词:** iterable 可迭代对象 · iterator 迭代器 · iterator result 迭代结果 · generator 生成器 · async iteration 异步迭代

The iterable/iterator protocols were standardized in ES2015. An iterable supplies an iterator through Symbol.iterator. An iterator supplies successive results through next(). This protocol powers for...of, array spread, and array destructuring; Array.from accepts either an iterable or an array-like input. An object is not iterable just because it has numeric keys or a length. / 可迭代对象/迭代器协议属于 ES2015。可迭代对象通过 Symbol.iterator 提供迭代器；迭代器通过 next() 提供后续结果。for...of、数组展开和数组解构都使用该协议；Array.from 接受可迭代对象或类数组输入。对象有数字键或 length 并不自动意味着它可迭代。

#### Iterable and iterator protocols / 可迭代协议与迭代器协议

An iterator result is an object. The consumer converts its `done` property to Boolean; if that property is absent, it acts as `false`. `value` supplies the current item and may be absent when iteration is complete. For example, `{ value: 42 }` is a non-complete result. / 迭代结果是一个对象。消费者会把其 `done` 属性转换为布尔值；若属性缺失，则按 `false` 处理。`value` 提供当前项，迭代完成时可以省略。例如，`{ value: 42 }` 表示尚未完成的结果。

Arrays, strings, Maps, Sets, typed arrays, and arguments objects are language-provided iterables. NodeList is iterable in modern browser DOM implementations, but it is a host API rather than a JavaScript-language collection. Plain objects are not iterable by default. / 数组、字符串、Map、Set、类型化数组和 arguments 对象是语言提供的可迭代对象。现代浏览器 DOM 实现中的 NodeList 也可迭代，但它属于宿主 API，而非 JavaScript 语言集合。普通对象默认不可迭代。

```javascript
const values = [10, 20];
const iterator = values[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: undefined, done: true }

for (const [key, value] of new Map([["x", 1], ["y", 2]])) {
  console.log(key, value);
}
```

This reusable range iterable is designed to return a fresh iterator on each Symbol.iterator call. The protocol does not require that: iterator objects and generators often return themselves and are one-shot. The optional return method gives resource-owning iterators a cleanup hook; for...of closes an iterator when `break` or an abrupt completion of the loop body exits iteration. / 这个可重复使用的 range 可迭代对象设计为每次调用 Symbol.iterator 都返回新迭代器；协议并不要求如此：迭代器对象和生成器常常返回自身，因此只能消费一次。可选的 return 方法为持有资源的迭代器提供清理钩子；`break` 或循环体发生异常等控制流离开迭代时，for...of 会关闭迭代器。

```javascript
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
```

```javascript
const oneShot = (function* values() { yield 1; })();
oneShot[Symbol.iterator]() === oneShot; // true: the iterator is its own iterable
```

See the [ECMAScript iteration interfaces](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration), [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete), and [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose) algorithms. / 可迭代接口见 [ECMAScript 迭代规范](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteration)，结果完成判断和迭代器关闭算法分别见 [IteratorComplete](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorcomplete) 与 [IteratorClose](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-iteratorclose)。

#### Generators / 生成器

A generator function returns an object that is both iterable and an iterator. yield pauses it and produces a value; the next() call resumes it. The first next(value) argument is ignored because execution has not paused at a yield yet; later values become the result of the suspended yield expression. / 生成器函数返回同时具备可迭代对象和迭代器特征的对象。yield 会暂停函数并产出值；下一次调用 next() 时继续执行。首次 next(value) 的参数会被忽略，因为函数尚未暂停在 yield 表达式上；之后传入的值会成为暂停处 yield 表达式的结果。

```javascript
function* conversation() {
  const name = yield "What is your name?";
  const hobby = yield "Hello, " + name + "! What do you enjoy?";
  return name + " likes " + hobby;
}

const chat = conversation();
chat.next();          // { value: "What is your name?", done: false }
chat.next("Ada");     // { value: "Hello, Ada! What do you enjoy?", done: false }
chat.next("coding");  // { value: "Ada likes coding", done: true }
```

yield* delegates iteration to another iterable or generator, including its completion result. It is useful for composing traversals. / yield* 把迭代委托给另一个可迭代对象或生成器，也会接收其完成结果，适合组合遍历逻辑。

```javascript
function* flatten(items) {
  for (const item of items) {
    if (Array.isArray(item)) yield* flatten(item);
    else yield item;
  }
}

[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]
```

#### Lazy sequences and control flow / 惰性序列与控制流

Generators compute on demand, which can represent large or infinite sequences without storing every value. The consumer controls how many values to request. / 生成器按需计算，可表示很大或无限的序列，而不必预先保存所有值。消费者决定请求多少项。

```javascript
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
```

The same lazy state can produce identifiers without storing an unbounded array of them. / 同样的惰性状态也可逐个生成标识符，而无需预先保存一个不断增长的数组。

```javascript
function* ids(prefix = "id") {
  let next = 0;
  while (true) yield prefix + "_" + next++;
}

const userIds = ids("user");
userIds.next().value; // "user_0"
userIds.next().value; // "user_1"
```

Before async/await, libraries such as co used a runner to yield Promises from generators and resume with their results. This is a historical control-flow pattern; async functions standardize a different syntax and runtime protocol, rather than literally exposing a generator implementation. / async/await 出现之前，co 等库会通过 runner 执行生成器：yield Promise，再用结果恢复执行。这是一种历史控制流模式；async 函数标准化了不同的语法和运行时协议，并非直接暴露生成器实现。

```javascript
function* legacyFlow() {
  const response = yield fetch("/api/user");
  return response.json();
}
// A runner must await each yielded value and resume the generator.
```

#### Async iteration / 异步迭代

An async iterable (standardized in ES2018) supplies Symbol.asyncIterator; each next() call makes its iterator result available asynchronously. for await...of waits for each next result in sequence, which is useful for streams whose next value becomes available over time. For a synchronous array of independent Promises, Promise.all is usually simpler and handles all rejections together. / ES2018 标准化的异步可迭代对象通过 Symbol.asyncIterator 提供迭代器；每次调用 next() 都会异步提供迭代结果。for await...of 按顺序等待每次 next() 的结果，适用于后续值逐步到达的数据流。同步数组中相互独立的 Promise 通常用 Promise.all 更简单，也能统一处理拒绝。

See [Asynchronous JavaScript / 异步 JavaScript](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for Promise aggregation and host scheduling.

**Interview answer / 面试回答:** An iterable returns an iterator from Symbol.iterator; an iterator’s next() returns value/done results. Generators implement both protocols and suspend at yield. Async iterables use Symbol.asyncIterator and are consumed with for await...of. / 可迭代对象通过 Symbol.iterator 返回迭代器；迭代器的 next() 返回 value/done 结果。生成器自动实现这两种协议，并在 yield 处暂停。异步迭代器使用 Symbol.asyncIterator，通过 for await...of 消费。
## 21. Error Handling / 错误处理

### Error Handling in JavaScript / JavaScript 错误处理

**Key terms / 关键词:** throw 抛出 · rejection Promise 拒绝 · error boundary 错误边界 · error cause 错误原因 · uncaught error 未捕获错误

Handle an error at the layer that owns enough context to recover, add information, or report it. A catch handler that only logs and then returns can silently convert failure into success; propagate failures when the caller must decide what to do. Browser globals, Node process handlers, and React boundaries have different scopes. / 应在拥有足够上下文进行恢复、补充信息或上报的层级处理错误。若 catch 只记录日志后正常返回，就可能把失败悄悄转换成成功；调用方仍需决策时应继续传播错误。浏览器全局处理器、Node 进程处理器和 React 错误边界的作用范围不同。

#### Synchronous code and cleanup / 同步代码与清理

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

#### Custom errors / 自定义错误

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

#### Promise rejections and Fetch / Promise 拒绝与 Fetch

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

#### Browser-global reporting / 浏览器全局上报

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

#### React error boundaries / React 错误边界

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

Related: [Asynchronous JavaScript / 异步 JavaScript](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript); [Modern JavaScript Features / 现代 JavaScript 特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7).
## 22. DOM Manipulation and Events / DOM操作与事件

**DOM Manipulation and Events / DOM 操作与事件**

DOM APIs expose tree mutation, events, and scheduling, but API guarantees differ from framework behavior and browser rendering choices. DOM 标准规定树与事件语义；框架事件系统和渲染性能细节另有版本与实现边界。

### How do you write a proper deep copy?

**Headline (30s):** JSON round-tripping only copies JSON-compatible data: it drops or changes values and rejects cycles. `structuredClone` handles cycles and supported built-in types; a handwritten clone is a domain-specific policy, not a universal deep-copy algorithm. **中文：** JSON 往返只适用于有限的数据形状；结构化克隆覆盖更多内建类型；手写克隆必须明确支持范围。

**Why interviewers ask this:** It tests your grasp of reference semantics, edge cases (cycles, special types), and whether you can design a recursive function with proper memoization.

#### Why `JSON.parse(JSON.stringify(x))` is insufficient

- **Changed values:** a `Date` serializes to a string; a typical `Map` or `Set` becomes `{}`.
- **Unsupported values:** object properties whose values are `undefined`, functions, or symbols are omitted; such array entries become `null`; a top-level unsupported value can make parsing fail.
- **Circular references and `BigInt`:** `JSON.stringify` throws.

Reach for `structuredClone(value)` (see [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7)) for supported structured-cloneable values. Functions and DOM nodes are not cloneable, and cloning does not preserve arbitrary class behavior. Use a handwritten clone only for a deliberately bounded data model or a custom policy (for example, omitting selected fields).

#### Handwritten deep copy

```javascript
function deepCopy(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return seen.get(value);

  let copy;
  if (value instanceof Date) {
    copy = new Date(value.getTime());
  } else if (value instanceof RegExp) {
    copy = new RegExp(value.source, value.flags);
    copy.lastIndex = value.lastIndex;
  } else if (value instanceof Map) {
    copy = new Map();
    seen.set(value, copy);
    for (const [key, item] of value) {
      copy.set(deepCopy(key, seen), deepCopy(item, seen));
    }
    return copy;
  } else if (value instanceof Set) {
    copy = new Set();
    seen.set(value, copy);
    for (const item of value) copy.add(deepCopy(item, seen));
    return copy;
  } else if (Array.isArray(value)) {
    copy = new Array(value.length);
  } else {
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new TypeError('Unsupported object type');
    }
    copy = Object.create(prototype);
  }

  seen.set(value, copy);
  if (value instanceof Date || value instanceof RegExp) return copy;

  // This example copies enumerable own string-keyed data in arrays/plain objects.
  for (const key of Object.keys(value)) {
    Object.defineProperty(copy, key, {
      value: deepCopy(value[key], seen),
      enumerable: true,
      writable: true,
      configurable: true,
    });
  }
  return copy;
}
```

This sample handles same-realm `Date`, `RegExp`, `Map`, `Set`, arrays, and plain objects with enumerable string keys. It does not preserve symbols, descriptors, accessors, arbitrary prototypes, or custom properties on the special built-ins. The `WeakMap` preserves cycles and repeated references; `Map` keys must be cloned as well as values.

```javascript
const trailingHoles = deepCopy([1, , ,]);
console.assert(trailingHoles.length === 3 && 0 in trailingHoles && !(1 in trailingHoles) && !(2 in trailingHoles));

const emptySparse = deepCopy(new Array(3));
console.assert(emptySparse.length === 3 && Object.keys(emptySparse).length === 0);
```

---

### How do DOM events propagate?

**Headline (30s):** Events with a propagation path can invoke capture listeners on the way to the target and bubble listeners on the way back. Whether an event bubbles or crosses a shadow boundary depends on its flags. Most `addEventListener` handlers use bubble mode by default. **中文：** 事件传播分捕获、目标和冒泡阶段，但是否冒泡、是否跨越 Shadow DOM 边界取决于事件标志。

#### The three phases

1. **Capture** — capture listeners run along the path toward the target.
2. **Target** — listeners on the target run.
3. **Bubble** — if `event.bubbles` is true, bubble listeners run back along the path.

```javascript
document.body.addEventListener('click', () => console.log('body (bubble)'));
document.body.addEventListener('click', () => console.log('body (capture)'), { capture: true });
button.addEventListener('click', () => console.log('button'));

// Clicking the button logs:
// body (capture)  → capture phase
// button          → target
// body (bubble)   → bubble phase
```

`event.target` is the event's target; `event.currentTarget` is the object whose listener is currently running. Shadow DOM can retarget `target` for listeners outside a shadow tree.

##### Default actions and listener options / 默认行为与监听器选项

Propagation and the browser's default action are separate. `preventDefault()` only cancels a cancelable event when called from a non-passive listener; it does not stop propagation. `stopPropagation()` stops the event reaching later objects on the path, while `stopImmediatePropagation()` also stops later listeners on the current object.

Use `{ passive: true }` for scroll/touch listeners that never cancel scrolling. In a passive listener, `preventDefault()` is ignored. The DOM Standard defines passive defaults for certain `touchstart`, `touchmove`, `wheel`, and `mousewheel` listeners on `Window`, `Document`, and document root/body targets; set the option explicitly when cancellation is required.

#### Event delegation

For many child controls, one parent listener can handle bubbled events. Match a descendant of the event target; delegation only works for event types that bubble.

```javascript
parent.addEventListener('click', (e) => {
  const target = e.target instanceof Element ? e.target : null;
  const item = target?.closest('.item');
  if (!item) return;
  console.log('Item clicked:', item.textContent);
});
```

Benefits: fewer per-item registrations and dynamically added descendants need no rebinding. Choose based on the event's propagation behavior and the needed target checks.

#### React's synthetic event system

React DOM exposes a **SyntheticEvent** with familiar event properties and JSX handlers for capture and bubble phases. Its internal delegation strategy is a framework implementation detail; React 17 changed the delegation root, so do not use one version's internals as a DOM rule.

Handler naming:

- `onClick` — bubble phase (default).
- `onClickCapture` — capture phase.

**Historical note — event pooling:** React DOM versions before 17 pooled SyntheticEvent objects; React 17 removed that behavior. `persist()` is not needed for current React DOM handlers. React Native has separate event behavior.

---

### Implement an EventBus / EventEmitter

**Headline (30s):** An EventBus stores listeners by event name. A `once` wrapper must remove itself before calling user code so recursion or a thrown error cannot make it run a second time. **中文：** 一次性监听器应在调用用户回调前注销，避免递归触发或异常导致重复调用。

```javascript
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
      this.off(event, wrapper); // remove before user code, including recursive emits
      listener(...args);
    };
    this.on(event, wrapper);
  }

  emit(event, ...args) {
    // Snapshot listeners: changes during this emit affect the next emit.
    for (const listener of [...(this.events.get(event) ?? [])]) listener(...args);
  }

  off(event, listener) {
    const listeners = this.events.get(event);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(event);
  }
}
```

**Reentrancy regression:** the outer `emit` keeps its listener snapshot while a nested `emit` uses the updated listener set. A later `once` wrapper can therefore still appear in the outer snapshot after the nested call removes it; its `fired` guard makes that second snapshot entry a no-op.

```javascript
const bus = new EventBus();
let firstCalls = 0;
let laterCalls = 0;
bus.once('x', () => { firstCalls += 1; bus.emit('x'); });
bus.once('x', () => { laterCalls += 1; });
bus.emit('x');
console.assert(firstCalls === 1 && laterCalls === 1);
```

**Gotcha — anonymous listeners:** `bus.on('x', () => {...})` can't be removed later because you don't have a reference to the function. Always save the reference if you'll need `off`.

**Contract of this small example:** a thrown listener stops the current `emit`; the listener snapshot means additions/removals during dispatch affect the next emission. A production emitter should document its error and mutation policy.

---

### Observer pattern vs. Publish-Subscribe

**Headline (30s):** Both are reactive messaging patterns, but they differ in coupling. **Observer**: the subject knows its observers directly (DOM events, RxJS subjects). **Publish-Subscribe**: a broker (event bus) sits between, so publishers and subscribers don't know about each other. Pub-Sub is more decoupled but harder to debug because the flow is indirect.

#### Observer

```javascript
button.addEventListener('click', handleClick);
// button knows it has a listener called handleClick
```

The subject (`button`) maintains a list of observers and notifies them directly.

#### Publish-Subscribe

```javascript
eventBus.on('user:login', updateUI);
eventBus.emit('user:login', { name: 'Alice' });
// Neither `updateUI` nor the emitter knows about each other
// The eventBus is the mediator
```

A topic string names the event channel; anyone can publish, anyone can subscribe.

**Rule of thumb:** Use Observer when there's a natural "owner" of the event (a DOM node, a data model). Use Pub-Sub when you want to decouple modules that shouldn't import each other.

---

### `requestAnimationFrame` vs. `requestIdleCallback` — when do you use each?

**Headline (30s):** `requestAnimationFrame` schedules visual work for a rendering opportunity. Its cadence follows the user agent and display; it is not a fixed 16 ms timer. `requestIdleCallback` offers an idle-time opportunity for non-critical work, but it can be delayed and needs a deliberate fallback when unavailable. **中文：** rAF 与绘制节奏关联；rIC 适合可延后任务，但两者都不是固定间隔定时器。

#### `requestAnimationFrame`

```javascript
function animate() {
  element.style.transform = `translateX(${x++}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

- Runs before a rendering update when the user agent schedules one; timing varies with refresh rate and page visibility.
- The first callback receives a high-resolution timestamp.

#### `requestIdleCallback`

```javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;

  // Process one bounded unit; a timeout is not permission to drain the queue.
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift());
  }

  if (workQueue.length) {
    requestIdleCallback(runIdleSlice, { timeout: 2000 });
  }
}

requestIdleCallback(runIdleSlice, { timeout: 2000 });
```

- `deadline.timeRemaining()` is the user agent's estimate of idle time remaining; do not treat it as a hard frame budget.
- `{ timeout }` asks the user agent not to leave the callback waiting indefinitely; `deadline.didTimeout` identifies that path.
- Keep each `processNext` unit bounded. A timeout callback still processes only one unit, then reschedules any remaining work.
- Feature-detect the API. `setTimeout` can be a functional fallback, but it is not an idle scheduler and gives no equivalent scheduling guarantee.

Framework schedulers may also split work and yield, but they are separate scheduling systems; do not equate React's scheduler with `requestIdleCallback`.

**Rule of thumb:**

- Must happen this frame? → `requestAnimationFrame`.
- Low priority, whenever the browser has idle time? → `requestIdleCallback` when available, with a fallback chosen for the task's guarantees.

---

### Finding the maximum in an array — which technique is safe for huge arrays?

**Headline (30s):** Spread and `apply` pass each array element as a function argument, so very large calls can exceed an implementation's argument limit. The limit varies; it is not a portable “100k” boundary. A loop or reduction avoids that argument-list limit. **中文：** 展开数组会形成大型实参列表，限制因实现而异；循环或归约不受该限制。

```javascript
// Concise, but very large argument lists may exceed an implementation limit
Math.max(...arr);
Math.max.apply(null, arr);

// Iterates without building a large argument list; for numeric arrays,
// an empty array matches Math.max() by producing -Infinity.
let max = -Infinity;
for (const value of arr) max = Math.max(max, value);
```

**Gotcha — input semantics:** `Math.max()` with no arguments returns `-Infinity`, and any `NaN` input makes its result `NaN`. If the application wants a different empty-input or non-number policy, handle that explicitly.

**See also:** [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for Intersection Observer, [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF) for the task/microtask scheduling model around browser callbacks.

**Standards and current docs / 规范与文档：** [WHATWG DOM events](https://dom.spec.whatwg.org/#concept-event-dispatch), [ECMAScript array objects](https://tc39.es/ecma262/multipage/indexed-collections.html), [WHATWG structured data](https://html.spec.whatwg.org/multipage/structured-data.html), [React DOM event handlers](https://react.dev/learn/responding-to-events), [React 17 event delegation change](https://react.dev/blog/2020/08/10/react-v17-rc#changes-to-event-delegation), [requestIdleCallback specification](https://w3c.github.io/requestidlecallback/), [Chrome `requestIdleCallback` guide](https://developer.chrome.com/blog/using-requestidlecallback), [CSSOM View](https://www.w3.org/TR/cssom-view-1/).
## 23. Browser Storage and Communication / 浏览器存储与通信

**Browser Storage and Communication / 浏览器存储与通信**

Browser storage is scoped by origin and browsing context, subject to browser quota and privacy policy. Cookies can accompany matching requests; Web Storage does not. 浏览器存储受源、浏览上下文、配额和隐私策略约束；只有符合条件的 Cookie 会随请求发送。

### What's the difference between `localStorage`, `sessionStorage`, and cookies?

**Headline (30s):** `localStorage` and `sessionStorage` are synchronous, origin-scoped key/value stores that scripts read explicitly. Cookies have domain, path, and cross-site sending rules, and matching cookies can be attached to requests. `localStorage` usually outlives a page session; `sessionStorage` is tied to a top-level browsing context. Choose from the data's lifetime, reader, and threat model. **中文：** Web Storage 由脚本显式读取；符合域、路径及跨站策略的 Cookie 会随请求发送。应按数据生命周期、读取方和威胁模型选择。

**Why interviewers ask this:** This comes up in any question about auth flows, session management, or persistence. Candidates who conflate the three write insecure auth code.

#### `localStorage`

- **Scope:** the origin's storage area; third-party contexts may be further partitioned or restricted by browser privacy policy.
- **Capacity:** the Storage Standard recommends a 5 MiB quota for the `localStorage` endpoint; actual availability can vary with user-agent policy and browser mode.
- **Lifetime:** persists until cleared or evicted; there is no per-entry expiration API.
- **Access:** synchronous string key/value operations, initiated by script; values are not automatically attached to HTTP requests.
- **Use for:** user preferences (theme, language), cached client state, offline data.

#### `sessionStorage`

Same API, scoped to an origin and a top-level browsing context. A new tab normally has its own area; an auxiliary window opened by a page can start with a copy of the opener's session storage, after which the two diverge.

- **Capacity:** the Storage Standard recommends a 5 MiB quota for the `sessionStorage` endpoint; actual availability can vary with user-agent policy and browser mode.
- **Lifetime:** survives reloads and same-tab navigation; cleared when the top-level browsing context's session ends (session restoration is user-agent-dependent).
- **Access:** synchronous string key/value operations; it does not automatically attach values to requests.
- **Use for:** multi-step form state, wizard progress, temporary SPA state.

#### Cookies

- **Capacity:** small per-cookie and per-site limits apply; exact usable limits vary by browser, so do not rely on a fixed cookie count or byte capacity.
- **Lifetime:** `Expires` / `Max-Age` set persistence; a session cookie normally ends with the browser session, whose restoration behavior varies.
- **Access:** a matching cookie may be sent with a request according to `Domain`, `Path`, `Secure`, `SameSite`, and the request's credentials policy. Script can read non-`HttpOnly` cookies through `document.cookie`.
- **Security attributes:** `HttpOnly` hides a cookie from non-HTTP APIs such as `document.cookie`; `Secure` restricts it to secure transport; `SameSite=Strict|Lax|None` controls cross-site sending. `SameSite` can reduce some CSRF exposure but is not a complete CSRF defense; `SameSite=None` requires `Secure` in current cookie rules.
- **Use for:** server-managed session identifiers when the application is designed around cookie authentication. Add CSRF defenses suited to the request flow.

#### Quick comparison

| Feature | `localStorage` | `sessionStorage` | Cookies |
|---|---|---|---|
| Scope | Origin storage area, subject to browser privacy policy | Origin + top-level browsing context | Domain/path and cookie policy |
| Capacity | Storage Standard recommends 5 MiB per endpoint; actual availability is browser-policy dependent | Storage Standard recommends 5 MiB per endpoint; actual availability is browser-policy dependent | Small; browser limits vary |
| Sent with requests | No automatic attachment | No automatic attachment | Matching cookies may be attached, subject to request and cookie policy |
| Lifetime | Persists until removed or evicted | Browsing-context session | Session or configured expiration |
| Server access | Only if page code sends it | Only if page code sends it | Yes, when the cookie is included |
| Accessible to JS | Yes | Yes | Unless `HttpOnly` |

**Security trade-off:** Any script running in the page can read Web Storage, so an XSS flaw can expose stored bearer tokens. `HttpOnly` cookies keep the cookie value out of page JavaScript, but cookies introduce request-forgery and cross-site policy concerns. Choose the session design deliberately; neither storage choice fixes XSS.

#### Quotas, partitioning, and coordination / 配额、分区与协调

The Storage Standard recommends 5 MiB quotas for the `localStorage` and `sessionStorage` endpoints. A recommended endpoint quota is not a guarantee of usable space in every browser mode: user-agent policy can restrict or disable access, and larger storage APIs use implementation-defined quotas. `navigator.storage.estimate()` reports approximate usage and quota; best-effort storage can be evicted under pressure. Use IndexedDB for larger structured data or transactions, and handle quota and access errors.

The standard's baseline storage key is the origin, while browser privacy behavior can further partition or gate storage in embedded third-party contexts. Do not assume an embedded site shares the same storage it sees when opened as a top-level page; this is browser- and policy-dependent.

Web Storage has no multi-key transaction or cross-tab lock. A read-modify-write sequence can race across tabs, and the `storage` event is a notification after a change, not a lock. Use IndexedDB transactions or an explicit coordination mechanism when updates must be atomic.

**See also:** [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for XSS/CSRF mitigation and cookie flag deep dives.

---

### `HTMLCollection` vs. `NodeList` — what's the difference?

**Headline (30s):** Both are array-like collections of DOM nodes, but differ in what they contain and how they update. **`HTMLCollection`** holds only `Element` nodes and is live — it reflects matching DOM changes. **`NodeList`** can hold any node type (Elements, Text, Comments); whether it is live depends on the API that returned it (`querySelectorAll` is static, while `childNodes` is live).

#### `HTMLCollection`

- Returned by `getElementsByClassName`, `getElementsByTagName`, `.children`.
- Contains only `Element` nodes.
- Live — its items reflect changes to the underlying tree; this does not promise that an engine reruns a query on every property access.

#### `NodeList`

- Returned by `querySelectorAll` (static), `childNodes` (live).
- Can contain any node type: `Element`, `Text`, `Comment`.
- Its liveness depends on the API that returned it.

#### `.children` vs `.childNodes`

```html
<p id="p1">
  <em>hello</em> world <b>bold</b><!-- comment -->
</p>
```

- `p.children` → `HTMLCollection`: `[<em>, <b>]` — elements only.
- `p.childNodes` → `NodeList`: `[<em>, " world ", <b>, <!-- comment -->]` — everything.

**Gotcha — mutating while iterating a live collection:** Removing elements from a live `HTMLCollection` during a `for` loop makes the indexes shift underneath you. Either iterate backwards, or convert to an array first (`Array.from(collection)`).

**Rule of thumb:** Reach for `querySelectorAll` by default — the static snapshot is easier to reason about. Fall back to `getElementsByClassName` when you explicitly need live updates.

---

### How can tabs of the same origin communicate?

**Headline (30s):** Four common options. For eligible same-origin contexts, **`BroadcastChannel`** is often the simplest. `localStorage` + `storage` is a broadly available persistence-backed workaround; `SharedWorker` can share in-memory state but should be feature-detected. Use `WebSocket` for server-mediated updates, not simply because two contexts have different origins.

#### 1. `localStorage` + `storage` event

Writing to `localStorage` queues a `storage` event for other documents that share that storage area; the document making the change does not receive its own event. Privacy partitioning can affect which embedded documents share an area.

```javascript
// Tab A listens
window.addEventListener('storage', (e) => {
  if (e.key === 'message') console.log('Received:', e.newValue);
});

// Tab B sends
localStorage.setItem('message', JSON.stringify({ text: 'hello', ts: Date.now() }));
```

**Gotcha — the writer gets no event:** The document that called `setItem` does not receive its own event. This is cross-document notification, not a same-document event bus.

#### 2. `BroadcastChannel` API

Purpose-built for messaging among eligible same-origin contexts, subject to the browser's storage partition and privacy rules. It transmits structured-clone data without persisting it.

```javascript
const channel = new BroadcastChannel('app_channel');

// Listen
channel.onmessage = (e) => console.log('Received:', e.data);

// Send
channel.postMessage({ type: 'update', payload: { id: 1 } });
```

Feature-detect it for the target browsers. Close the channel when its owner is done.

#### 3. `SharedWorker`

A worker instance shared by connected same-origin contexts can hold in-memory state while clients remain connected. It is not durable storage; feature-detect it where browser coverage matters.

```javascript
// worker.js
const ports = new Set();
onconnect = (e) => {
  const port = e.ports[0];
  ports.add(port);
  port.onmessage = (msg) => {
    // broadcast to all other tabs
    ports.forEach(p => { if (p !== port) p.postMessage(msg.data); });
  };
};
```

Do not treat a shared worker as a durable store or assume it survives after every client disconnects.
This small broadcast sketch omits port cleanup; a real worker needs an explicit client-disconnect and stale-port policy.

#### 4. WebSockets for server-mediated updates

Use WebSocket when the application needs a persistent, bidirectional connection to a server. A difference in origin alone does not make it the only or default channel between contexts. The WebSocket protocol is not CORS: validate the handshake `Origin` and authenticate and authorize each connection on the server.

**Rule of thumb:** Ephemeral same-origin messages → `BroadcastChannel`; persist-and-notify use cases → `localStorage` plus `storage`; cross-origin frame messaging → `postMessage` with origin checks; server-mediated updates → WebSocket or another authenticated server channel.

---

### How do you communicate with an iframe?

**Headline (30s):** Use `window.postMessage(data, targetOrigin)` for window-to-window messaging across origins. The parent calls `iframe.contentWindow.postMessage(...)`; the iframe calls `window.parent.postMessage(...)`. Both sides listen for `message`, check `event.origin` and the expected `event.source`, and validate the message shape. **中文：** 跨源窗口通信可用 `postMessage`；接收方必须核验来源、窗口和数据格式。

```javascript
// Parent → iframe
const iframe = document.getElementById('myIframe');
iframe.contentWindow.postMessage(
  { action: 'update' },
  'https://child-origin.com'
);

// Iframe → parent
window.parent.postMessage(
  { status: 'ready' },
  'https://parent-origin.com'
);

// Receiving inside the iframe; on the parent page compare against iframe.contentWindow.
const expectedOrigin = 'https://parent-origin.com';
const expectedWindow = window.parent;
window.addEventListener('message', (e) => {
  if (e.origin !== expectedOrigin || e.source !== expectedWindow) return;
  if (!e.data || typeof e.data !== 'object' || typeof e.data.action !== 'string') return;
  console.log('Received:', e.data);
});
```

**Gotcha — avoid `'*'` for confidential messages:** A wildcard can deliver to a window after it has navigated to another origin. Specify the expected scheme, host, and port.

**Gotcha — origin checks do not validate data:** A trusted origin can still be compromised. Parse and validate the message before acting on it; `postMessage` payloads use structured cloning, not shared object references.

---

### What's a JS-Bridge, and how does it work?

**Headline (30s):** A JS-Bridge is a communication layer between native mobile code and JavaScript running inside a `WebView`. Web content is sandboxed and can't call native APIs directly, so the bridge routes calls through one of two mechanisms: **URL-scheme hijacking** (the iframe-src trick) or **global API injection** (the native app exposes functions on `window`). Modern apps usually use global injection for sync calls and URL schemes for legacy support.

#### URL scheme method

The native app registers a custom scheme (e.g., `myapp://`). The web side loads a URL matching that scheme in a hidden iframe, which the native app intercepts before it actually navigates.

```javascript
const bridge = {
  invoke(path, data, onSuccess, onError) {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = `myapp://${path}?data=${encodeURIComponent(JSON.stringify(data))}`;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 100);
  },
  getLocation(onSuccess, onError) {
    this.invoke('api/location', {}, onSuccess, onError);
  }
};
```

**Limitation:** URL length caps, no direct response — callbacks must be stored by ID and invoked by the native side.

#### Global API injection

The native side evaluates JavaScript into the WebView to expose functions on `window`:

```javascript
// Native injects window.NativeBridge beforehand
const version = window.NativeBridge.getVersion();
window.NativeBridge.requestLocation((loc) => console.log(loc));
```

Feels like normal JS — synchronous or callback-based depending on what the native side supports.

**Reach for it when:** building a hybrid app (WebView + native shell). For pure web, use standard browser APIs (`navigator.geolocation`, etc.).

**Gotcha — security:** Treat bridge calls as privileged input. Restrict which frames and origins can reach the bridge, validate each operation and argument natively, and avoid exposing capabilities to arbitrary page content.

**See also:** [`1.1 Browser Basics`](#1.%20Browser%20Basics%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9F%BA%E7%A1%80) for where storage and messaging fit into the browser architecture, [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for auth storage and CSRF concerns.

**Standards and current guidance / 标准与文档：** [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html), [WHATWG Storage Standard](https://storage.spec.whatwg.org/), [WHATWG DOM collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection), [MDN storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), [WHATWG cross-document messaging and BroadcastChannel](https://html.spec.whatwg.org/multipage/web-messaging.html), [WHATWG WebSockets](https://websockets.spec.whatwg.org/), [IETF cookies draft (work in progress)](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/).
## 24. Image Lazy Loading / 浏览器图片懒加载

**Image Lazy Loading / 浏览器图片懒加载**

Use native lazy loading for ordinary off-screen images; choose `IntersectionObserver` only when code must control the loading decision. 原生懒加载适合普通图片；只有确实需要自定义加载时机时才引入观察器。

#### How do you lazy-load images in the browser?

**Headline (30s):** Prefer native `loading="lazy"` for an image with a real `src` or `srcset`. Use `IntersectionObserver` when you need custom thresholds, roots, or non-image work. A scroll handler is a fallback only when the observer is unavailable. **中文：** 原生属性必须配合图片源；观察器用于自定义交集策略；滚动监听只作兼容性回退。

**Why interviewers ask this:** It's a common real-world perf question and a great filter for "do you know modern browser APIs or are you still writing jQuery-era scroll listeners?" The follow-up usually digs into CLS (Cumulative Layout Shift) and how to avoid jank when images pop in.

---

#### 1. Native lazy loading (preferred)

Current browser engines support `loading="lazy"` for `<img>` and `<iframe>`; check the browsers your product targets when supporting older engines:

```html
<img src="image.jpg" alt="Description" loading="lazy" width="800" height="600">
```

Values:

- `lazy` — ask the user agent to defer fetching until its visibility conditions are met.
- `eager` — request loading without lazy deferral (the default state).
- `data-src` is not a native loading source. An `<img>` needs `src` or `srcset`; the browser cannot load the URL stored only in a `data-*` attribute.

**Why this is the first choice:**

- Zero JavaScript, zero bundle cost.
- The browser controls the deferral threshold, which may vary by implementation.
- No JavaScript observer or scroll listener is required for this common case.

**Include intrinsic `width` and `height`:** together they let the browser reserve an aspect ratio before the image loads, reducing layout shifts. CSS can still change the rendered size.

---

#### 2. `IntersectionObserver` (JS fallback / more control)

When you need behaviors the native attribute does not cover—such as a custom root, a threshold, or loading work beyond an `<img>`—use `IntersectionObserver`. It reports queued intersection changes; the API does not promise that callback code runs off the main thread.

```html
<img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="actual-image.jpg" alt="Description" width="800" height="600">
```

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);    // stop observing after scheduling the request
    }
  });
}, {
  rootMargin: '200px' // expand the root rectangle by 200px on each side
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});

// Call observer.disconnect() when the component or page owning it is disposed.
```

**Key options:**

- **`rootMargin`** — expand or shrink the root rectangle; positive values can trigger before the target reaches the root. Choose the distance from measured product behavior, not a universal constant.
- **`threshold`** — intersection ratios at which entries are queued. With `0`, an edge-adjacent intersection can have a zero-area intersection rectangle, so `isIntersecting` does not mean “at least one pixel is visible.”

**Why `IntersectionObserver` can help:** the browser batches intersection notifications instead of requiring application code to poll geometry on every scroll event. A geometry read can force style or layout work when rendering state is dirty; neither mechanism has a universal cost guarantee.

---

#### 3. Scroll + throttle (legacy fallback only)

For a required environment without `IntersectionObserver`, a scroll/resize fallback can check `getBoundingClientRect()`. Feature-detect the API and test this fallback in the actual target browser.

```javascript
function throttle(fn, delay) {
  let timer = null;
  return function (...args) {
    if (timer) return;
    timer = setTimeout(() => {
      fn.apply(this, args);
      timer = null;
    }, delay);
  };
}

const checkImages = throttle(() => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    const rect = img.getBoundingClientRect();
    if (rect.bottom > 0 && rect.top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    }
  });
}, 100);

window.addEventListener('scroll', checkImages, { passive: true });
window.addEventListener('resize', checkImages, { passive: true });
checkImages(); // also handle images already near the viewport
```

**Gotcha — geometry reads are conditional work:** `getBoundingClientRect()` returns current geometry and may force pending style/layout updates. Avoid alternating DOM writes and reads in a hot loop; do not assume every call forces a full-page layout.

---

#### Performance: don't trade loading speed for layout jank

Lazy-loading images is great — unless you introduce layout shift every time one appears. Rules to follow:

- **Do not lazy-load likely LCP or immediately visible images.** Deferring a critical image can delay presentation; use `loading="eager"` or omit the attribute when appropriate.
- **Reserve an aspect ratio** with intrinsic `width` / `height` or CSS `aspect-ratio` to reduce layout shifts.
- **Combine with `srcset` + modern formats** (WebP, AVIF). Lazy-loading an over-sized JPEG still wastes bandwidth.
- **Use a placeholder** (low-quality image placeholder, LQIP, or a solid color) so the user sees something while the real image loads.

```html
<img
  src="full-800.webp"
  srcset="full-400.webp 400w, full-800.webp 800w, full-1600.webp 1600w"
  sizes="(max-width: 600px) 100vw, 50vw"
  loading="lazy"
  width="800"
  height="600"
  alt="Describe the image's purpose">
```

**Rule of thumb:**

1. Use `loading="lazy"` with an actual `src` or `srcset`, appropriate `alt`, and intrinsic dimensions.
2. Use `IntersectionObserver` for a concrete custom-loading need; unobserve loaded targets and disconnect the observer when its owner is disposed.
3. Check layout stability and LCP in the page's real loading context; lazy-loading the wrong images can delay important content.

**See also:** [`11.1 Performance Metrics and Analysis`](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for Core Web Vitals and broader image-perf strategies, [`5.1 DOM Manipulation and Events`](#22.%20DOM%20Manipulation%20and%20Events%20/%20DOM%E6%93%8D%E4%BD%9C%E4%B8%8E%E4%BA%8B%E4%BB%B6) for `IntersectionObserver` in other use cases.

**Standards / 规范：** [WHATWG `img` element and source requirements](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element), [WHATWG lazy-loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes), [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/), [CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/).
## 25. Advanced TypeScript / TypeScript进阶

### Advanced TypeScript / TypeScript进阶

TypeScript checks relationships between values while editing and compiling JavaScript. Type declarations are erased from emitted JavaScript, so a successful typecheck does not validate untrusted runtime values. The type system also makes deliberate soundness tradeoffs; values typed with any or an unchecked assertion can bypass useful checks.

#### How do types meet untrusted JSON? / 类型如何处理不可信 JSON？

**Core answer / 核心回答：** Treat API bodies and browser storage as untrusted runtime data. Parse into `unknown`, validate the shape and values with JavaScript checks, and only then construct a trusted typed value. A type annotation or assertion changes what the checker believes; it does not inspect the data. / API 响应和浏览器存储都应视为不可信运行时数据。先将解析结果放入 `unknown`，再用 JavaScript 检查结构和值，最后才构造可信的类型化对象。类型注解或断言只会改变检查器的判断，不会检查数据本身。

`JSON.parse` can throw for malformed JSON and, on success, still says nothing about the object's shape. `unknown` keeps that boundary visible: every property read must follow a runtime guard. This example handles both syntax and shape failures without an unchecked cast; the storage adapter also makes a missing key explicit.

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

After validation, ordinary control-flow narrowing applies to the declared model. An exhaustive switch protects the code that consumes the validated role; it does not prove that the parser itself is correct.

~~~typescript
function roleLabel(profile: Profile): string {
  switch (profile.role) {
    case "admin": return "Administrator";
    case "reader": return "Reader";
    default: {
      const unreachable: never = profile.role;
      return unreachable;
    }
  }
}
~~~

The union lets the checker require narrowing before type-safe access to `value`, but it does not require every caller to inspect the result. The `never` assignment checks exhaustiveness only in this `roleLabel` switch; it does not force every switch over `Profile.role` to include the same guard. Only the runtime checks establish that this particular JSON value is a `Profile`. If the server later adds a role, the parser deliberately rejects it until the application accepts that value; update the validator and exhaustive consumers together.

#### What are utility types? / 什么是工具类型？

**Core answer / 核心回答：** Utility types transform an existing type so related shapes stay connected instead of copying property declarations. They are compile-time descriptions: Readonly does not freeze an object, and Partial does not validate an incoming request. / 工具类型可以转换已有类型，让相关数据结构保持关联，避免重复声明字段。它们只描述编译期类型：Readonly 不会冻结对象，Partial 也不会验证传入的请求。

| Utility | Result |
|---|---|
| Partial<T> | Makes each property optional. |
| Required<T> | Makes each property required. |
| Readonly<T> | Makes each property readonly at compile time; it is shallow. |
| Pick<T, K> / Omit<T, K> | Selects or removes a set of keys. |
| Record<K, V> | Describes an object whose keys and values follow the supplied types. |
| Exclude<U, X> / Extract<U, X> | Removes from or selects members of a union. |
| NonNullable<T> | Removes null and undefined from a type. |
| ReturnType<F> / Parameters<F> | Extracts a function's return type or parameter tuple. |
| InstanceType<C> / ConstructorParameters<C> | Extracts a class instance type or constructor parameter tuple. |

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

A type such as UserPatch is useful for expressing an allowed shape, but runtime code still needs to check that a parsed JSON value contains valid fields and values.

#### How do generics work? / 泛型如何工作？

**Core answer / 核心回答：** A generic preserves a relationship between input and output types. TypeScript can infer a type parameter from a call, and an extends constraint limits which values are accepted. / 泛型用于保留输入和输出类型之间的关系。TypeScript 可以根据调用推断类型参数；extends 约束用于限制可接受的类型。

~~~typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30 };
const userName = getProperty(user, "name"); // string
// getProperty(user, "phone"); // Type error: no such key
~~~

A generic interface can keep that relationship across a group of operations:

~~~typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}
~~~

Use generics when the same logic should preserve specific types across multiple callers. A type parameter is not a runtime check; it describes the contract enforced by the checker where type information is available.

#### What is Proxy? / Proxy是什么？

**Core answer / 核心回答：** JavaScript Proxy wraps an object and lets a handler intercept operations such as property reads, writes, deletion, or membership checks. It is a runtime JavaScript feature, not a TypeScript type feature. Reflect methods forward operations while preserving their normal semantics. / JavaScript Proxy 包装一个对象，并让 handler 拦截属性读取、写入、删除和成员检查等操作。它是 JavaScript 的运行时功能，不是 TypeScript 类型功能。Reflect 方法可按正常语义转发这些操作。

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
data.count;
data.count = 1;
~~~

Common uses include reactive state, validation, and instrumentation. A proxy only observes operations that pass through it; references to the original target can bypass its traps. Unlike defining a getter for each known property, a proxy can intercept later-added properties, but compatibility and object behavior still matter. Vue 2 used property getters and setters for reactivity; Vue 3 uses proxies for reactive objects.

#### What are decorators? / 什么是装饰器？

**Core answer / 核心回答：** Decorators run at class-definition time and can wrap or register class elements. TypeScript supports standard ECMAScript decorators and a separate legacy mode. Their signatures and capabilities differ; use the mode required by the framework rather than copying a decorator from another configuration. / 装饰器在类定义时运行，可包装或注册类成员。TypeScript 支持标准 ECMAScript 装饰器和另一套旧版模式。两种模式的签名和能力不同；应使用框架要求的模式，不要直接复制其他配置中的装饰器。

##### Standard decorators in TypeScript 5.0+ / TypeScript 5.0+标准装饰器

Standard decorators receive the original method and a context object. A method decorator may return a replacement method.

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

Standard decorators do not support parameter decorators and are not compatible with emitDecoratorMetadata.

##### Legacy decorators / 旧版装饰器

Existing Angular, NestJS, and ORM projects may use the legacy decorator mode enabled by experimentalDecorators. A legacy method decorator receives a target, property key, and property descriptor. That signature is different from the standard form; the legacy emitDecoratorMetadata option also belongs to this mode.

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

Do not use decorator metadata as general runtime validation. For an external JSON value, parse and validate the actual value with runtime logic or a validation library.

#### How do you check every member of a union? / 如何确保联合类型分支完整？

**Core answer / 核心回答：** Narrow a discriminated union by its tag, then assign the final branch to never. If a new union member is added without a branch, the assignment becomes a type error. / 通过判别字段缩小联合类型；最后将剩余分支赋给 never。如果新增联合成员却没有增加对应分支，该赋值就会产生类型错误。

~~~typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; side: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "square":
      return shape.side ** 2;
    default: {
      const exhaustive: never = shape;
      return exhaustive;
    }
  }
}
~~~

**See also:** [JavaScript Memory, WeakMap and WeakSet / JavaScript内存、WeakMap与WeakSet](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef) for object identity and proxies; [React Basics / React基础](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) for component API examples.

**Sources checked 2026-10-15:** [TypeScript: Basic Types and `unknown`](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types and assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions), [Narrowing and Exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking), [TypeScript: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html), [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html), [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness), [TypeScript 5.0 Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators), [Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth).
## 26. Event Loop / 事件循环

### Event Loop and Host Scheduling / 事件循环与宿主调度

**Key terms / 关键词:** JavaScript agent JavaScript 执行代理 · task 任务 · microtask 微任务 · event loop 事件循环 · libuv libuv

ECMAScript defines language execution and Promise jobs; the host defines event loops, timers, I/O, and rendering. A JavaScript agent executes its jobs one at a time, but browsers and Node can create additional workers or agents. Asynchronous I/O may be handled by the host or operating system; “async” does not mean all work runs on one thread. / ECMAScript 定义语言执行和 Promise job；宿主定义事件循环、计时器、I/O 和渲染。单个 JavaScript agent 一次执行一个 job，但浏览器和 Node 可以创建其他 worker 或 agent。异步 I/O 可能由宿主或操作系统处理；“异步”不表示所有工作都在同一线程运行。

#### Browser event loop / 浏览器事件循环

In the HTML event loop, a task such as a script or timer callback runs to completion. A microtask checkpoint then drains queued microtasks, including newly queued microtasks, before the loop proceeds. Promise reactions and queueMicrotask use this queue. Rendering is a separate opportunity controlled by the browser; it is not guaranteed after every task or at a fixed frame boundary. / 在 HTML 事件循环中，脚本或计时器回调等任务会执行到完成。随后进行微任务检查点，清空队列中的微任务（包括执行过程中新增的微任务），再继续循环。Promise 处理器和 queueMicrotask 使用该队列。渲染由浏览器在独立机会中处理；不保证每个任务后立即渲染，也不保证固定帧边界。

```javascript
console.log("start");

setTimeout(() => console.log("timer task"), 0);

new Promise(resolve => {
  console.log("Promise executor runs synchronously");
  resolve();
}).then(() => console.log("Promise reaction"));

console.log("end");

// Typical browser ordering:
// start
// Promise executor runs synchronously
// end
// Promise reaction
// timer task
```

A zero-delay timer is eligible only after its minimum delay and when the host schedules its timer task; it does not mean “run immediately.” The Promise-versus-timer ordering above describes the browser task and microtask model, not the precise timing of rendering. / 零延迟计时器要等到最小延迟满足且宿主调度相应计时器任务后才可运行，并不表示“立即执行”。上例中 Promise 与计时器的先后关系描述浏览器任务和微任务模型，不代表渲染时机。

The [WHATWG HTML event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) defines browser tasks, microtask checkpoints, and rendering opportunities. These browser rules should not be inferred from a Node run. / [WHATWG HTML 事件循环标准](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) 定义浏览器任务、微任务检查点和渲染机会。不能通过 Node 执行结果推断浏览器规则。

#### Node.js event loop / Node.js 事件循环

Node uses libuv phases to coordinate timers and I/O callbacks. A useful simplified outline is timers, pending callbacks, poll, check, and close callbacks; idle/prepare are internal phases. The poll phase handles I/O, and setImmediate callbacks run in the check phase. Timer callbacks become eligible after their threshold, not at an exact deadline. / Node 使用 libuv 阶段协调计时器和 I/O 回调。简化来看包括 timers、pending callbacks、poll、check 和 close callbacks；idle/prepare 是内部阶段。poll 阶段处理 I/O，setImmediate 回调在 check 阶段运行。计时器达到阈值后才具备运行资格，并不保证精确截止时间执行。

Since libuv 1.45.0 (Node.js 20), timers run after the poll phase in each loop iteration; earlier versions also ran timers before poll. This affects some timer/setImmediate interactions. At top level, do not rely on a fixed order between setTimeout(fn, 0) and setImmediate(fn); context and timing matter. / 从 libuv 1.45.0（Node.js 20）开始，每轮事件循环中计时器在 poll 阶段之后运行；较早版本还会在 poll 前运行计时器。这会影响部分 timer/setImmediate 交互。在顶层不要依赖 setTimeout(fn, 0) 和 setImmediate(fn) 的固定顺序；上下文和时序都会影响结果。

#### Node nextTick and Promise jobs / Node nextTick 与 Promise job

Node has a next-tick queue in addition to the Promise/queueMicrotask queue. Current Node documentation specifies different top-level ordering for CommonJS and ES modules: in CommonJS, nextTick callbacks run before Promise and queueMicrotask callbacks; during ES module evaluation, Promise reactions and queueMicrotask callbacks run before nextTick callbacks. Do not state a module-independent ordering. / 除 Promise/queueMicrotask 队列外，Node 还有 nextTick 队列。当前 Node 文档明确说明 CommonJS 与 ES 模块顶层顺序不同：CommonJS 中 nextTick 回调先于 Promise 和 queueMicrotask 回调；ES 模块求值期间，Promise 和 queueMicrotask 回调先于 nextTick 回调。不能写成与模块类型无关的固定顺序。

```javascript
// CommonJS top level (for example, a .cjs file)
Promise.resolve().then(() => console.log("promise"));
queueMicrotask(() => console.log("microtask"));
process.nextTick(() => console.log("nextTick"));
// Node.js v26.11.1: nextTick, promise, microtask
```

```javascript
// ES module top level (for example, a .mjs file)
Promise.resolve().then(() => console.log("promise"));
queueMicrotask(() => console.log("microtask"));
process.nextTick(() => console.log("nextTick"));
// Node.js v26.11.1: promise, microtask, nextTick
```

Node marks process.nextTick as Legacy starting in Node v20.18.0 and v22.7.0; for most userland deferrals, its current docs recommend queueMicrotask unless nextTick-specific behavior is required. Recursively scheduling nextTick can starve I/O. These are Node runtime rules, not browser behavior. / Node 从 v20.18.0 和 v22.7.0 开始把 process.nextTick 标为 Legacy；当前文档建议大多数用户态延迟场景使用 queueMicrotask，除非确实需要 nextTick 的专有行为。递归调度 nextTick 可能饿死 I/O。这些属于 Node 运行时规则，不是浏览器行为。

The queue examples were run with Node v26.11.1. Current official Node v26 documentation was checked on 2026-10-15: [process.nextTick and queueMicrotask](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), [event-loop phases and the Node 20 timer change](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick). / 队列示例在 Node v26.11.1 中执行。2026-10-15 核对了当前官方 Node v26 文档：[process.nextTick 与 queueMicrotask](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)、[事件循环阶段与 Node 20 计时器变更](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)。

#### Garbage collection and retained objects / 垃圾回收与对象保留

ECMAScript does not specify whether an engine uses mark-and-sweep, reference counting, a stack, or a heap, and programs cannot rely on collection at a chosen time. An object that remains reachable through a long-lived reference cannot be reclaimed; cycles alone do not imply a leak. / ECMAScript 不规定引擎必须使用标记清除、引用计数、栈或堆，程序也不能依赖在指定时刻完成回收。对象若仍能从长期存活的引用到达，就不能回收；仅有循环引用并不意味着泄漏。

One implementation model traces from roots such as the global object and active execution state, marks reachable objects, and reclaims unreachable ones; an unreachable cycle can therefore be collected. V8's Orinoco overview describes generations and parallel, incremental, and concurrent GC work. These are engine mechanisms that may change, not ECMAScript requirements. / 一种引擎实现模型是从全局对象、活动执行状态等根开始追踪，标记可达对象并回收不可达对象；因此不可达的循环引用也可回收。V8 的 Orinoco 说明介绍了分代回收，以及并行、增量和并发 GC 工作。这些是可能演进的引擎机制，不是 ECMAScript 要求。

See V8's [Orinoco garbage collector overview](https://v8.dev/blog/trash-talk) for this implementation example. / 这一实现示例见 V8 的 [Orinoco 垃圾回收器说明](https://v8.dev/blog/trash-talk)。

Common retention paths include an uncleared interval, a listener attached to a long-lived object, a detached DOM node still referenced by application code, or a closure retained with values it actually captures. These are investigation leads, not proof that a leak exists. In browser tools, compare heap snapshots around a repeatable action and inspect retained paths. / 常见保留路径包括未清除的 interval、挂在长期存活对象上的监听器、仍被应用代码引用的脱离 DOM 树节点，或闭包实际捕获并长期持有的值。这些只是排查线索，并不能证明已发生泄漏。浏览器工具中可围绕可重复操作比较堆快照，并检查保留路径。

If a subscription, listener, or timer should end before the owning object does, keep its handle and release it at that lifetime boundary. For weak references and their nondeterministic cleanup behavior, see [JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef). / 若订阅、监听器或计时器应早于所属对象结束，就保存其句柄并在生命周期边界释放。弱引用及其不确定的清理时机见[JavaScript 内存、WeakMap、WeakSet 与 WeakRef](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef)。

**Interview answer / 面试回答:** The event loop is host-defined. In browsers, tasks run to completion and a microtask checkpoint drains Promise reactions before the host continues; rendering is scheduled separately. Node uses libuv phases and adds nextTick scheduling, whose order relative to Promise jobs differs between top-level CJS and ESM. Always state the host and module context. / 事件循环由宿主定义。浏览器任务执行到完成后会进行微任务检查点，清空 Promise 处理器，再由宿主继续调度；渲染单独安排。Node 使用 libuv 阶段并增加 nextTick 调度，其与 Promise job 的相对顺序在 CJS 和 ESM 顶层不同。说明结论时应给出宿主和模块上下文。

Related: [Asynchronous JavaScript / 异步 JavaScript](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript); [Memory, WeakMap and WeakSet / JavaScript 内存、WeakMap 与 WeakSet](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef).
## 27. Build Tools / 构建工具

### Build Tools / 构建工具

Build tools resolve modules, transform source files, and produce output for development or deployment. The exact pipeline depends on the tool and version.

**Core answer / 核心回答：** A bundler follows the module graph, transforms selected modules, and emits assets; loaders transform modules while plugins use broader compiler hooks. / 打包器沿模块依赖图处理文件、转换选定模块并输出资源；loader 转换模块，plugin 则可通过更广泛的 compiler hooks 扩展构建过程。

#### Webpack concepts / Webpack核心概念

Webpack starts from configured entries, resolves their dependency graph, applies loaders to modules, and emits assets. Its configuration names entry points, output, mode, module rules, plugins, and optimization.

| Term | Role |
|---|---|
| Entry | Starting point for dependency resolution. |
| Output | Destination and naming for emitted assets. |
| Loader | Transforms one module's source before bundling. |
| Plugin | Hooks into compiler or compilation stages to add broader build behavior. |
| Mode | Enables development or production defaults; explicit settings can override them. |

##### Loader order / Loader执行顺序

Normal loader functions execute right to left. Pitch functions, when present, run left to right.

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

For the TypeScript rule, ts-loader runs first and its output is then passed to babel-loader. A real project should choose one clear TypeScript transform pipeline; running overlapping transforms can add cost or change output unexpectedly.

| Common loader role | Examples | Typical work |
|---|---|---|
| JavaScript or TypeScript transform | babel-loader, ts-loader | Transpile syntax or TypeScript according to the configured toolchain. |
| Styles | sass-loader, css-loader, style-loader | Compile Sass, resolve CSS imports and URLs, then inject styles in a development page. Production builds may extract CSS into files. |
| Static assets | Webpack 5 Asset Modules | Emit or inline resources using built-in module types instead of older file-loader or url-loader setups. |

##### Loader and plugin examples / Loader与插件示例

A small text replacement shows the loader shape. It is not a JavaScript parser; use a syntax-aware transform when source structure matters.

~~~javascript
module.exports = function replaceBuildLabel(source) {
  return source.replaceAll("__BUILD_LABEL__", "demo");
};
~~~

A plugin can subscribe to a compiler hook. The done hook runs after compilation and is an AsyncSeriesHook. A synchronous handler may register with tap; asynchronous handlers may use tapAsync or tapPromise so the hook waits for their work.

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

Production plugins should write to an explicit destination and handle concurrent or watch builds deliberately; the example is a minimal local illustration.

| Plugin | Typical role |
|---|---|
| HtmlWebpackPlugin | Generates an HTML document and injects emitted script or stylesheet references. |
| DefinePlugin | Replaces configured expressions at compile time; it does not read a runtime environment variable from the browser. |
| MiniCssExtractPlugin | Emits CSS into separate files when the build needs extracted styles. |

These are examples, not a required plugin stack; a framework may provide equivalent build features. As of the Webpack docs checked on 2026-10-15, the HtmlWebpackPlugin README marks it deprecated; the native HTML guide describes experiments.html and output.html as alternatives for generated pages, and still labels native HTML experimental. Check the installed Webpack version and template needs before migrating.

##### Source maps / Source map

A source map relates emitted code to source files for debugging and error reporting. Select devtool based on rebuild speed, trace detail, artifact size, and whether the map is published. A map that is uploaded privately can still be exposed if the deployment serves it publicly; configuration alone does not set the access policy.

| devtool example | Output meaning |
|---|---|
| eval-source-map | Evaluates modules with source maps for development debugging. |
| source-map | Emits an external map with a sourceMappingURL reference. |
| hidden-source-map | Emits an external map without the reference comment; useful when a release pipeline uploads maps separately. |
| nosources-source-map | Omits embedded source content, but mappings and source paths may still be present. |

These names describe different map delivery and detail choices; compare the configured output rather than treating them as a fixed speed ranking or a security boundary.

#### Vite and the development/production split / Vite与开发、生产构建的区别

Vite's development server serves native ES modules with on-demand transforms and HMR. In Vite 8, the production build uses Rolldown to produce optimized assets. Earlier Vite releases used a different production bundler pipeline, so state the major version when the distinction matters.

A fast dev server is not evidence that the production output has the same graph or performance. Run the configured production build and inspect its assets when validating deployment behavior.

#### Corepack and package-manager pinning / Corepack与包管理器版本固定

A package.json packageManager field records the package manager and version a project expects. Corepack can use that field to select a matching manager when its shims are installed. Corepack was bundled with Node.js through Node 24, but Node 25 and later no longer distribute it by default; a current project may need to install or provision Corepack separately.

~~~json
{
  "packageManager": "pnpm@10.0.0"
}
~~~

The field alone does not install a package manager or guarantee that every environment honors it. Pin and provision the tool through the project's supported runtime and CI setup.

**Choosing a tool / 工具选择：** Compare plugin and loader needs, ecosystem, output constraints, team familiarity, and build behavior for the project. No single bundler is the right choice for every application or library.

**See also:** [Modern JavaScript Features / 现代JavaScript特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7) for modules and dynamic imports; [Performance Metrics and Analysis / 性能指标与分析](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for measuring bundle and load behavior.

**Sources checked 2026-10-15:** [Webpack: Loaders](https://webpack.js.org/concepts/loaders/), [Asset Modules](https://webpack.js.org/guides/asset-modules/), [Webpack: Plugins](https://webpack.js.org/concepts/plugins/), [DefinePlugin](https://webpack.js.org/plugins/define-plugin/), [HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme), [Webpack Native HTML guide](https://webpack.js.org/guides/native-html/), [style-loader](https://github.com/webpack/style-loader#readme), [css-loader](https://github.com/webpack/css-loader#readme), [MiniCssExtractPlugin](https://github.com/webpack/mini-css-extract-plugin#readme), [Webpack: Writing a Plugin](https://webpack.js.org/contribute/writing-a-plugin/), [Webpack Compiler Hooks](https://webpack.js.org/api/compiler-hooks/), [Webpack devtool](https://webpack.js.org/configuration/devtool/), [Vite 8 guide](https://vite.dev/guide/), [Vite 8.0.10 source](https://github.com/vitejs/vite/blob/v8.0.10/README.md), [Node.js 25 Corepack docs](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html), [Corepack project README](https://github.com/nodejs/corepack#readme).
## 28. Virtual DOM and Framework Selection / 虚拟DOM与框架选择

### Virtual DOM and Framework Selection / 虚拟DOM与框架选择

#### How does reconciliation work, and does a Virtual DOM make an app faster? / React如何协调界面，虚拟DOM是否天然更快？

**Core answer / 核心回答：** React components describe the UI for a particular set of props and state. React compares the next element description with the previous one, then commits the necessary host changes. “Virtual DOM” is a useful shorthand for this model, not a speed guarantee: the cost depends on the component tree, update, browser work, and framework implementation. / React 组件根据当前 props 和 state 描述界面。React 将新的元素描述与之前的结果协调，再提交必要的宿主环境变更。“虚拟 DOM”是这种模型的常见简称，不代表它天然更快；实际成本取决于组件树、更新内容、浏览器工作和框架实现。

##### A practical React model / React中的实用模型

1. **Render / 渲染：** React calls components to calculate the next UI description. Rendering should be pure; concurrent work may be restarted or discarded.
2. **Reconciliation / 协调：** React matches the new description to the previous tree. Element type, position, and sibling keys help determine whether identity and state are preserved.
3. **Commit / 提交：** React applies the completed changes to the host tree, such as the DOM. Effects run in their documented phase; they are not part of render.

Keys identify siblings across renders. A stable data ID is a good key when list items can move, be inserted, or be removed. An array index can be acceptable for a fixed list whose order and membership never change. Changing a component's type or key can reset its state.

~~~jsx
{items.map(item => <ListItem key={item.id} item={item} />)}
~~~

The reconciler uses heuristics instead of a general-purpose minimum-edit tree algorithm. Treat complexity claims as implementation-specific; the useful takeaway is that stable identity lets React preserve the right component state while updating a changing tree.

##### Where the model helps / 适用范围

Declarative rendering keeps UI descriptions aligned with state and lets the framework manage host updates. It can also add work for tiny isolated changes, and it does not remove browser layout, paint, or scripting costs. Use the browser and framework profilers to identify a real bottleneck before choosing a different rendering model.

React and Vue use virtual-tree reconciliation in their standard component models. Other approaches compile templates or update fine-grained dependencies. These are implementation choices, not a universal ranking.

#### How do you choose a frontend framework? / 如何选择前端框架？

**Core answer / 核心回答：** Choose for the product's rendering and interaction needs, the team's ability to maintain it, required integrations, accessibility, deployment constraints, and the framework's support horizon. Evaluate a representative feature before migrating; popularity or a benchmark alone cannot predict project fit. / 根据产品的渲染与交互需求、团队维护能力、所需集成、无障碍要求、部署约束和框架支持周期来选择。迁移前先实现一个有代表性的功能；流行度或单项基准测试不足以判断项目是否适合。

| Decision factor | Questions to answer |
|---|---|
| Rendering and routing | Does the product need client-only navigation, server rendering, static output, or a mix? |
| Team and codebase | Which framework and language can the team debug, test, and upgrade? |
| Ecosystem | Are the needed router, form, data, accessibility, and build tools supported? |
| Operations | Can the chosen runtime, hosting model, and release process support it? |
| Migration cost | What working behavior, tests, and integrations would need to be replaced? |

TypeScript adds static checking and editor support, but its types are erased and do not validate runtime data. Consider the language and migration cost alongside project size and contributor turnover; there is no reliable “six-month” or “three-person” threshold.

**See also:** [React Basics / React基础](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) for element identity and component state; [Next.js / Next.js开发](#31.%20Next.js%20/%20Next.js%E5%BC%80%E5%8F%91) for router-specific rendering models.

**Sources checked 2026-10-15:** [React Reconciliation](https://legacy.reactjs.org/docs/reconciliation.html), [Vue Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism), [React: Render and Commit](https://react.dev/learn/render-and-commit), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TypeScript: erased structural types](https://www.typescriptlang.org/docs/handbook/typescript-for-oopers.html#erased-structural-types).
## 29. React Basics / React基础

### React Basics / React基础

React components describe UI from props and state. These notes focus on JSX, element identity, class lifecycle methods, state updates, and routing.

#### What is JSX, and what does it compile to? / JSX是什么，最终会编译成什么？

**Core answer / 核心回答：** JSX is syntax for describing elements inside JavaScript; it is not HTML text. A configured compiler transforms JSX using either the classic factory runtime or the automatic JSX runtime. The emitted calls depend on the compiler and its configuration. / JSX 是在 JavaScript 中描述元素的语法，不是 HTML 字符串。配置好的编译器会使用经典工厂模式或自动 JSX runtime 转换它；实际生成的调用取决于编译器和配置。

~~~jsx
const element = <h1 className="title">Hello</h1>;
~~~

With the automatic runtime, a React compiler can emit calls to helpers from react/jsx-runtime. With the classic runtime, it can emit React.createElement calls. The automatic transform means React does not need to be imported solely for JSX when the project is configured for it.

- Lowercase tags such as **div** name built-in elements; uppercase identifiers such as **Profile** name component values.
- Curly braces insert JavaScript expressions into JSX.
- React DOM uses names such as **className** and **onClick** rather than HTML attribute spelling.

#### How does React match elements between renders? / React如何判断哪些元素需要更新？

**Core answer / 核心回答：** React uses element type, tree position, and keys among siblings to match elements and preserve component state. Stable keys should represent item identity when a list can change; an index is suitable only when the list's membership and order are fixed. / React 使用元素类型、树中的位置和兄弟元素间的 key 来匹配元素并保留组件 state。列表可能变化时，稳定 key 应代表数据项身份；只有列表成员和顺序固定时，索引才适合作为 key。

~~~jsx
{items.map(item => <ListItem key={item.id} item={item} />)}
~~~

Keys are local to one set of siblings; they do not need to be unique across the entire application. React may preserve state for a matching element and reset it when its type or key changes. This is why an index key can attach local state to the wrong data after an insertion, deletion, or reorder.

#### What are class lifecycle methods? / 类组件的生命周期方法是什么？

**Core answer / 核心回答：** Class components have mount, update, and unmount lifecycles. Rendering can be repeated or abandoned, so keep render pure and put external synchronization in lifecycle methods or Effects. Function component Effects have setup and cleanup semantics; there is no exact one-to-one mapping from each class method to a Hook. / 类组件有挂载、更新和卸载阶段。render 可能重复执行或被放弃，因此应保持纯净，并将外部同步放在生命周期方法或 Effect 中。函数组件 Effect 有自己的 setup 和 cleanup 语义，不能把每个类方法与 Hook 一一对应。

| Class lifecycle | Purpose |
|---|---|
| **constructor** | Initialize state and instance fields. |
| **getDerivedStateFromProps** | Runs before render on mount and updates; rarely derives state from incoming props. |
| **render** | Return the next UI description; do not perform side effects here. |
| **shouldComponentUpdate** | Runs before an update render and can skip it as a performance optimization. |
| **getSnapshotBeforeUpdate** | Runs after render but before DOM mutations; its return value is passed to componentDidUpdate. |
| **componentDidMount** | Synchronize with external systems after the component commits. |
| **componentDidUpdate** | React to committed prop or state changes; guard against unnecessary loops. |
| **componentWillUnmount** | Release subscriptions, timers, and other resources. |
| **getDerivedStateFromError / componentDidCatch** | Render fallback UI and report errors from a descendant subtree. |

An Effect runs after a commit; React runs its previous cleanup before setting up the Effect again when dependencies change, and on unmount. In development, root StrictMode adds an extra setup-and-cleanup cycle to help expose incomplete cleanup. This is a development check, not an extra production lifecycle.

#### What does an Error Boundary catch? / Error Boundary能捕获哪些错误？

**Core answer / 核心回答：** A React Error Boundary is a class component that displays fallback UI for errors thrown while rendering descendants, in their constructors, or in their React lifecycle methods. It does not catch event-handler errors, ordinary asynchronous callbacks, server-rendering errors, or errors thrown by the boundary itself. One documented exception is an error thrown inside the function passed to the startTransition function returned by useTransition (including a rejected Promise returned by that function). / React Error Boundary 是类组件，可在后代树渲染、构造函数或 React 生命周期方法抛错时显示备用 UI。它不会捕获事件处理器、普通异步回调、服务端渲染或边界自身抛出的错误。一个文档列出的例外是 useTransition 返回的 startTransition 所执行函数抛错（包括该函数返回的 rejected Promise）。

~~~jsx
import React from "react";

class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error(error, info.componentStack);
  }

  render() {
    return this.state.hasError
      ? <p>Something went wrong.</p>
      : this.props.children;
  }
}
~~~

The built-in React boundary API is class-based. A library can make boundary composition easier, but try/catch around JSX does not catch rendering failures.

#### Is setState synchronous? / setState是同步还是异步？

**Core answer / 核心回答：** A state setter requests another render; it does not mutate the state snapshot held by the current render or event handler. React 18+ with createRoot also batches updates from timeouts, promises, and native event handlers. React 17 and React 18's legacy ReactDOM.render path batch fewer contexts. / state setter 会请求下一次渲染，不会改写当前 render 或事件处理器持有的 state 快照。React 18+ 使用 createRoot 时，也会批处理 timeout、Promise 和原生事件处理器中的更新。React 17 以及 React 18 的旧 ReactDOM.render 路径会批处理较少的场景。

~~~jsx
setCount(count + 1);
console.log(count); // This render's snapshot is unchanged.

setCount(previous => previous + 1);
setCount(previous => previous + 1); // Queued updates build on each other.
~~~

Use an updater when the next value depends on the previous value. Read the new state during a later render or in an Effect when appropriate; do not expect the variable in the current handler to change.

#### How does React Router work? / React Router如何工作？

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

#### What is the difference between an SPA and an MPA? / SPA和MPA有什么区别？

**Core answer / 核心回答：** An MPA navigation requests another document; an SPA typically keeps one document loaded and updates route content in the client. Server rendering and client navigation can be combined, so many current applications use a hybrid model. Choose based on content delivery, interaction, accessibility, and operational needs rather than the label alone. / MPA 导航会请求另一个文档；SPA 通常保留一个文档并在客户端更新路由内容。服务端渲染和客户端导航可以组合，因此许多现代应用采用混合模式。应根据内容交付、交互、无障碍和运维需求选择，而非只看标签。

| Aspect | SPA pattern | MPA pattern |
|---|---|---|
| Navigation | Client router updates the current document | Browser requests another document |
| State | Client state can persist between route changes | State often needs URL, storage, or server persistence |
| Initial delivery | Depends on shell size, rendering, and data strategy | Depends on document and asset delivery |
| SEO and accessibility | Require deliberate rendering and semantic structure | Also require meaningful HTML and semantic structure |

**See also:** [Next.js / Next.js开发](#31.%20Next.js%20/%20Next.js%E5%BC%80%E5%8F%91) for router-specific rendering; [Advanced React / React进阶](#30.%20Advanced%20React%20/%20React%E8%BF%9B%E9%98%B6) for Hooks, refs, and component composition.

**Sources checked 2026-10-15:** [React: Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform), [React: Render and Commit](https://react.dev/learn/render-and-commit), [StrictMode](https://react.dev/reference/react/StrictMode), [Component and lifecycle methods](https://react.dev/reference/react/Component), [Error Boundary caveats](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary), [useTransition Error Boundary example](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary), [Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Queueing State Updates](https://react.dev/learn/queueing-a-series-of-state-updates), [React Router v6 Concepts](https://reactrouter.com/docs/en/v6/start/concepts), [React Router: Picking a Mode](https://reactrouter.com/start/modes).
## 30. Advanced React / React进阶

### Advanced React / React进阶

#### How can components communicate? / React组件如何通信？

**Core answer / 核心回答：** Keep data flow explicit: pass data down with props, send events up with callback props, and use Context or a store when many distant consumers need shared state. Refs expose imperative capabilities; they are not a substitute for state that drives visible UI. / 保持数据流清晰：用 props 向下传数据，用回调 props 向上传事件；多个较远组件需要共享状态时再考虑 Context 或 store。ref 用于暴露命令式能力，不应替代驱动界面的 state。

~~~jsx
const ThemeContext = createContext("light");

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  );
}

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>Toolbar</div>;
}
~~~

A child can notify its parent through a callback prop. Use Context for values such as theme or locale that are needed across a subtree; a store can help when shared state and update patterns grow more complex. Custom Hooks share stateful logic, but each call has its own Hook state unless the Hook deliberately connects to shared state. Avoid using an event bus as a default substitute for React's data flow.

#### Who owns server data and local UI state? / 服务端数据与本地界面状态由谁管理？

**Core answer / 核心回答：** Keep transient choices such as the selected row, open dialog, or draft input in local React state. Treat records owned by a server as server state: identify each query by all inputs that affect it, define when cached data is fresh, and invalidate or update affected entries after a mutation. A query cache is a client read model, not the source of truth. / 将选中行、打开的对话框和输入草稿等临时选择保存在 React 本地状态中。服务器拥有的记录属于服务端状态：查询键要包含所有影响结果的输入，缓存需要明确新鲜期，变更后要更新或失效相关缓存。查询缓存是客户端读模型，不是数据的权威来源。

For example, selecting a row is local UI state, while the list and selected record come from the server. Separate query keys encode their identities; include filters, page, or account identifiers too when they change the result. In TanStack Query v5, `staleTime` defines how long a result is considered fresh. Once stale, it can refetch on configured events; targeted invalidation marks matching entries stale and refetches active observers. The value is a freshness policy, not a promise that the server data cannot change.

~~~tsx
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

type Task = { id: string; title: string; done: boolean };
type TaskPatch = Pick<Task, "id"> & Partial<Pick<Task, "title" | "done">>;

// These request functions parse and validate their responses at the API boundary.
declare function listTasks(): Promise<Task[]>;
declare function getTask(id: string, signal: AbortSignal): Promise<Task>;
declare function saveTask(patch: TaskPatch): Promise<Task>;

const taskKeys = {
  list: ["tasks", "list"] as const,
  detail: (id: string) => ["tasks", "detail", id] as const
};

function useTaskList() {
  return useQuery({
    queryKey: taskKeys.list,
    queryFn: listTasks,
    staleTime: 30_000
  });
}

function useTaskDetail(id: string) {
  return useQuery({
    queryKey: taskKeys.detail(id),
    queryFn: ({ signal }) => getTask(id, signal)
  });
}

function TaskWorkspace() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const list = useTaskList();

  if (list.isPending) return <p>Loading tasks…</p>;
  if (list.isError) return <p role="alert">Could not load tasks.</p>;

  return (
    <div>
      <ul>
        {list.data.map(task => (
          <li key={task.id}>
            <button type="button" onClick={() => setSelectedId(task.id)}>
              {task.title}
            </button>
          </li>
        ))}
      </ul>
      {selectedId !== null && <TaskDetail id={selectedId} />}
    </div>
  );
}

function TaskDetail({ id }: { id: string }) {
  const detail = useTaskDetail(id);
  if (detail.isPending) return <p>Loading selected task…</p>;
  if (detail.isError) return <p role="alert">Could not load this task.</p>;
  return <p>{detail.data.title}</p>;
}

function useSaveTask() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: saveTask,
    onMutate: async patch => {
      const detailKey = taskKeys.detail(patch.id);
      await Promise.all([
        client.cancelQueries({ queryKey: taskKeys.list }),
        client.cancelQueries({ queryKey: detailKey })
      ]);

      const previousList = client.getQueryData<Task[]>(taskKeys.list);
      const previousDetail = client.getQueryData<Task>(detailKey);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === patch.id ? { ...task, ...patch } : task)
      );
      if (previousDetail !== undefined) {
        client.setQueryData<Task>(detailKey, { ...previousDetail, ...patch });
      }
      return { previousList, previousDetail };
    },
    onError: (_error, patch, previous) => {
      if (previous?.previousList !== undefined) {
        client.setQueryData(taskKeys.list, previous.previousList);
      }
      if (previous?.previousDetail !== undefined) {
        client.setQueryData(taskKeys.detail(patch.id), previous.previousDetail);
      }
    },
    onSuccess: saved => {
      client.setQueryData(taskKeys.detail(saved.id), saved);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === saved.id ? saved : task)
      );
    },
    onSettled: (_data, _error, patch) => Promise.all([
      client.invalidateQueries({ queryKey: taskKeys.list }),
      client.invalidateQueries({ queryKey: taskKeys.detail(patch.id) })
    ])
  });
}
~~~

The mutation cancels in-flight reads before writing optimistically, saves snapshots for rollback, replaces both cached views with the server response on success, then invalidates them to reconcile other changes. A pending save can disable its button; on error, the snapshot restores the visible list/detail and the UI can show a retry message. Because rollback restores the whole list snapshot, this example requires at most one mutation in flight across the shared list—not merely one save per task. Otherwise A can fail after B succeeds and restore B's old row too. Broader concurrency needs operation-scoped or version-aware reconciliation instead of blindly restoring that snapshot. If the user switches from task A to B while A is loading, the detail key changes from `detail/A` to `detail/B`; A may finish into its own cache entry, but cannot become B's displayed record. Passing the query's `AbortSignal` to `fetch` can also stop obsolete network work when the service consumes it. A manually managed Effect needs its own stale-result guard or cleanup; the `useWindowSize` Effect in the custom Hook section below shows cleanup, and an Effect fetch by itself does not activate Suspense. See [Advanced TypeScript / TypeScript进阶](#25.%20Advanced%20TypeScript%20/%20TypeScript%E8%BF%9B%E9%98%B6) for validating API JSON before treating it as a `Task`.

#### How do concurrent UI updates and Suspense work? / 并发界面更新与 Suspense 如何工作？

**Core answer / 核心回答：** Keep input state urgent so each keystroke appears immediately; defer expensive result rendering or mark a navigation-like state update as a Transition. React can interrupt and retry that render work so urgent updates get priority. A Suspense boundary gives one part of the screen a fallback while a Suspense-enabled child is not ready. / 输入状态应保持紧急，以便每次按键都立即显示；可以延后昂贵结果区域的渲染，或把类似导航的状态更新标记为 Transition。React 可以中断并重试这部分渲染，让紧急更新优先。Suspense 边界则在支持 Suspense 的子树尚未就绪时，为该区域显示 fallback。

This search panel keeps the text input responsive and places the loading fallback around only the result list. `useSuspenseQuery` is the TanStack Query v5 data source that suspends here; a normal query or fetch started in an Effect does not automatically suspend. The memoized result boundary allows React to skip this child when an urgent parent render leaves `deferredQuery` and `tab` unchanged; without it, the child still renders on each parent input update even though the deferred value is old. It renders again when either deferred prop advances.

~~~tsx
import { memo, Suspense, useDeferredValue, useState, useTransition } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";

type SearchHit = { id: string; title: string };
declare function searchTasks(query: string, tab: "tasks" | "summary"): Promise<SearchHit[]>;

function TaskSearch() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<"tasks" | "summary">("tasks");
  const [isPending, startTransition] = useTransition();
  const deferredQuery = useDeferredValue(query);
  const showingOlderResults = query !== deferredQuery;

  function selectTab(next: "tasks" | "summary") {
    startTransition(() => setTab(next));
  }

  return (
    <section>
      <input
        aria-label="Search tasks"
        value={query}
        onChange={event => setQuery(event.target.value)}
      />
      <button type="button" onClick={() => selectTab("summary")}>Summary</button>
      {isPending && <span>Updating view…</span>}
      <Suspense fallback={<p>Loading results…</p>}>
        <div aria-busy={showingOlderResults}>
          <TaskSearchResults query={deferredQuery} tab={tab} />
        </div>
      </Suspense>
    </section>
  );
}

const TaskSearchResults = memo(
  function TaskSearchResults({ query, tab }: { query: string; tab: "tasks" | "summary" }) {
    const { data } = useSuspenseQuery({
      queryKey: ["tasks", "search", query, tab],
      queryFn: () => searchTasks(query, tab)
    });
    return <ul>{data.map(hit => <li key={hit.id}>{hit.title}</li>)}</ul>;
  }
);
~~~

`useTransition` exposes `isPending` and marks state updates inside `startTransition` as non-urgent; its callback runs immediately, and it cannot control a text input. With an async action, wrap state updates after each `await` in another `startTransition` to mark them as transitions. `useDeferredValue` lets a child keep seeing the previous value while React prepares an interruptible background render. It has no fixed delay and does not suppress network requests, so use an explicit debounce when the goal is fewer requests. Neither API parallelizes JavaScript on another CPU thread or makes a long synchronous calculation faster; use a better algorithm, memoization, or a worker when computation itself blocks. `Suspense` only shows this fallback when its child suspends through a supported source such as `use` with a cached Promise or a Suspense-enabled framework/library. Pair data errors with an Error Boundary or use explicit pending/error states; Suspense is not a request error handler. Keep renders pure because React may retry interrupted work.

#### When should you use memo, useMemo, or useCallback? / 何时使用 memo、useMemo和useCallback？

**Core answer / 核心回答：** These are performance tools, not correctness tools. React.memo can skip rendering when props compare equal; useMemo caches a calculated value; useCallback caches a function reference. Add them when profiling or a specific identity boundary shows they help. / 这些 API 是性能工具，不是正确性工具。React.memo 可在 props 比较相等时跳过渲染；useMemo 缓存计算值；useCallback 缓存函数引用。只有性能分析或明确的引用边界表明它们有帮助时再使用。

~~~jsx
import { memo, useCallback, useMemo } from "react";

function ListContainer({ items, onSelect }) {
  const sortedItems = useMemo(
    () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
    [items]
  );

  const handleSelect = useCallback((id) => {
    onSelect(id);
  }, [onSelect]);

  return <ItemList items={sortedItems} onSelect={handleSelect} />;
}

const ItemList = memo(function ItemList({ items, onSelect }) {
  return items.map(item => (
    <button key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </button>
  ));
});
~~~

React.memo's default prop comparison uses Object.is per prop. A component can still render when its own state or consumed context changes; one newly created object or function prop can also prevent a skip. Inline handlers are ordinary JavaScript and are not automatically a performance bug. Keep state near its consumers, avoid unnecessary Effects that trigger render chains, and use the React Profiler to find a real hotspot.

React may discard a useMemo cache in documented circumstances. Do not depend on memoization for resource lifetime, semantic identity, or correctness.

#### What does useRef do? / useRef有什么作用？

**Core answer / 核心回答：** useRef returns a stable object whose current field can hold a value between renders. Changing current does not request a render, so use refs for DOM access and bookkeeping, not for displayed state. / useRef 返回一个在多次渲染间保持稳定的对象，其 current 字段可保存可变值。修改 current 不会请求重新渲染，因此 ref 适合 DOM 访问和内部记录，不适合驱动可见界面的状态。

~~~jsx
function SearchBox() {
  const inputRef = useRef(null);

  return (
    <>
      <input ref={inputRef} />
      <button onClick={() => inputRef.current?.focus()}>
        Focus
      </button>
    </>
  );
}
~~~

Other suitable values include a timer ID or an external instance. Do not read or write refs during rendering except for initialization. Use state when a change must update the screen.

#### What do forwardRef and useImperativeHandle do? / forwardRef和useImperativeHandle有什么作用？

**Core answer / 核心回答：** In React 18 and earlier, forwardRef lets a component accept and forward a parent's ref; useImperativeHandle can expose a narrow command API. In React 19, a function component can receive ref as a prop, so forwardRef is no longer necessary for new React 19-only components. / React 18 及更早版本中，forwardRef 让组件接收并转发父组件传入的 ref；useImperativeHandle 可暴露范围较小的命令式 API。React 19 的函数组件可以把 ref 作为 prop 接收，因此仅面向 React 19 的新组件不再需要 forwardRef。

~~~jsx
const FancyInput = forwardRef(function FancyInput(props, ref) {
  return <input {...props} ref={ref} className="fancy" />;
});
~~~

Prefer declarative props and callbacks when they express the interaction clearly. Use an imperative ref for cases such as focusing an input or coordinating a third-party widget.

#### What is a custom Hook? / 什么是自定义Hook？

**Core answer / 核心回答：** A custom Hook is a function whose name starts with use and that calls other Hooks at the top level. It packages reusable stateful logic; it does not share one state instance across callers by itself. / 自定义 Hook 是名称以 use 开头、并在顶层调用其他 Hook 的函数。它封装可复用的有状态逻辑；仅仅复用 Hook 本身不会让多个调用共享同一份 state。

~~~jsx
function useWindowSize() {
  const [size, setSize] = useState({
    width: 0,
    height: 0
  });

  useEffect(() => {
    function update() {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    }

    window.addEventListener("resize", update);
    update();
    return () => window.removeEventListener("resize", update);
  }, []);

  return size;
}
~~~

Ordinary Hooks must be called in the same order on every render, at the top level of a component or another Hook. React 19’s use API is an exception: it may appear in a condition or loop, but it still belongs inside a component or Hook and cannot be wrapped in try/catch. The lint plugin checks these Rules of Hooks. An Effect's cleanup releases the listener; root StrictMode deliberately repeats setup and cleanup once in development.

#### What are render props and higher-order components? / 什么是 render props 和高阶组件？

**Core answer / 核心回答：** Render props pass a function that chooses what to render from data supplied by a component. A higher-order component takes a component and returns a wrapped component. Both remain useful API shapes in some libraries and legacy code; custom Hooks are another way to share logic, not a universal replacement. / render props 通过函数接收组件提供的数据并决定渲染内容。高阶组件接收一个组件并返回包装后的组件。它们仍适用于某些库 API 和旧代码；自定义 Hook 是共享逻辑的另一种方式，并非对二者的通用替代。

~~~jsx
<MouseTracker render={({ x, y }) => (
  <p>Pointer: {x}, {y}</p>
)} />
~~~

A wrapper component can add authorization or instrumentation, but nested wrappers may make the component tree and prop flow harder to follow. Choose the API that makes ownership and behavior clear.

#### What are common conditional-rendering patterns? / 常见的条件渲染写法有哪些？

**Core answer / 核心回答：** Use a ternary for either-or, logical AND for render-or-nothing, and an early return for a clear guard. Choose the form that makes the branches easiest to read. / 二选一可用三元表达式；只在条件成立时渲染可用逻辑 AND；明确的前置检查可用 early return。选择最容易读懂分支的写法。

~~~jsx
{isLoggedIn ? <Dashboard /> : <Login />}
{showBanner && <Banner />}

function Profile({ user }) {
  if (!user) return <Loading />;
  return <Content user={user} />;
}
~~~

Because React renders numbers, a numeric left operand can leak into the output: an empty list's length is 0, so {items.length && <List />} displays 0. Use {items.length > 0 && <List />} when that is not intended.

**See also:** [React Basics / React基础](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) for state snapshots and lifecycle context; [Rendering and Computation Optimization / 渲染与计算优化](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for profiling and memoization limits.

**Sources checked 2026-10-15:** [React: `useTransition`](https://react.dev/reference/react/useTransition), [`useDeferredValue`](https://react.dev/reference/react/useDeferredValue), [`Suspense`](https://react.dev/reference/react/Suspense), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries), [Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys), [Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), [Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation), [Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates), [Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation), [React: memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback), [useRef](https://react.dev/reference/react/useRef), [forwardRef](https://react.dev/reference/react/forwardRef), [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [Rules of Hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks), [use](https://react.dev/reference/react/use).
## 31. Next.js / Next.js开发

### Next.js / Next.js开发

#### What does Next.js add to React? / Next.js为React增加了什么？

**Core answer / 核心回答：** Next.js is a React framework that combines routing, server and client rendering, data access, and deployment integrations. Its Pages Router and App Router have different file conventions and rendering APIs, so name the router and version when describing behavior. / Next.js 是 React 框架，整合路由、服务端与客户端渲染、数据访问和部署集成。Pages Router 与 App Router 的文件约定和渲染 API 不同，说明行为时要注明路由器和版本。

Next.js can produce HTML on the server or ahead of a request, and it can update route content in the browser. These options are not one global switch: choose based on the route's data freshness, user-specific content, runtime, and caching needs.

#### Pages Router: SSR, SSG, and ISR / Pages Router：SSR、SSG和ISR

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

#### App Router: Server Components and caching / App Router：Server Components与缓存

Under the app directory, pages and layouts are Server Components by default. They can fetch on the server and pass serializable data to a Client Component. A file marked use client creates a client boundary for Hooks, event handlers, and browser APIs. Client Components may still contribute to initial HTML; use client does not mean the whole route is client-only.

~~~tsx
// app/posts/page.tsx — App Router
async function getPosts() {
  const response = await fetch("https://api.example.com/posts", {
    cache: "no-store"
  });
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

In the current Next.js 16.4.1 documentation checked on 2026-10-15, App Router fetch requests are not cached by default. Set caching deliberately, for example with a fetch revalidation option; with Cache Components enabled, a use cache directive can cache a component or function. Request-time data and static shells can be combined with Suspense and streaming. Older Next.js App Router versions had different fetch defaults, so do not carry a versionless caching rule between projects.

A Client Component can receive data from a Server Component through props, but props crossing the boundary must be serializable. Keep secrets and server-only dependencies on the server.

#### How do hydration and streaming fit together? / Hydration 与流式渲染如何衔接？

**Core answer / 核心回答：** Server-rendered HTML can appear before the client JavaScript is ready. Hydration makes that existing markup interactive by matching it to React's initial client render and attaching behavior; the two initial outputs must agree. Effects run only in the browser after a component commits. In the App Router, a `Suspense` boundary can show a useful fallback while a slower child waits, then stream that region into the page. / 服务端 HTML 可以先于客户端 JavaScript 显示。Hydration 将已有标记与 React 客户端的首次渲染匹配并附加交互行为；两端首次输出必须一致。Effect 只在浏览器中、组件提交后运行。App Router 中的 `Suspense` 边界可以先显示有用的占位内容，再把等待中的子区域流式送入页面。

##### Hydration timeline and one mismatch diagnostic

1. The server sends HTML. The browser can display it before React's client code runs; React-specific handlers and state are not attached yet, although ordinary HTML behavior still works.
2. The client loads React and hydrates the existing DOM. React expects the first client render to match the server HTML, then attaches component behavior.
3. After the client commit, `useEffect` can read browser-only state and schedule a later render. Effects do not run during server rendering, so they cannot supply initial server HTML.

A diagnostic example is `new Date().toLocaleDateString()` rendered during both server and initial client rendering: the clock, locale, or time zone can make the strings differ. Start with the hydration warning and compare the server output with the first client render; trace values that depend on time, randomness, browser APIs, or independently changing data. Prefer a stable value shared by both renders. If content must be browser-specific, render a stable initial placeholder and update after hydration, accepting that the user may see a second pass. `suppressHydrationWarning` is a narrow escape hatch for an unavoidable one-level text or attribute difference, not a fix for a mismatched subtree.

##### Place a Suspense boundary around a useful streamed region

In Next.js 16.4.1 App Router, the fetching guide documents route-level `loading.tsx` and smaller `<Suspense>` boundaries. Content outside a boundary can render while the child inside waits. Start independent data work before awaiting it, then let the child suspend so the boundary has time to show its fallback. The example follows the existing archived [App Router data-fetching and Suspense example](../../archive/front-end/0-1_Learning_Notes/next.js/readme.md); `getPosts()` is an application data function returning a promise.

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

If the page awaits `getPosts()` before returning this tree, that request cannot be streamed inside the boundary. Place boundaries around independently useful parts: a boundary that is too high can hold back the whole page, while a boundary around a tiny fragment can create a choppy reveal. A fallback is visible page content, so give it meaningful text. If an update needs an assistive-technology announcement, add the appropriate live-region semantics; that does not move keyboard focus or create interaction behavior. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](#2.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for the focused keyboard, naming, and error model. A pending fallback also does not make a failed request successful; provide a separate error path.

#### How does file-based routing work? / 文件系统路由如何工作？

**Core answer / 核心回答：** The route tree follows files, but the conventions differ between routers. Pages Router uses files such as pages/about.js and pages/posts/[id].js. App Router uses route segments containing page.tsx and can add layout.tsx, loading.tsx, and error.tsx. / 路由树由文件结构决定，但两种路由器的约定不同。Pages Router 使用 pages/about.js、pages/posts/[id].js 等文件；App Router 使用包含 page.tsx 的路由段，并可加入 layout.tsx、loading.tsx 和 error.tsx。

Use Link for navigation. Prefetching is production-only and differs by router: App Router can fully prefetch static routes and partially prefetch dynamic routes to a loading boundary; Pages Router's default behavior differs. Treat prefetch as an optimization, not a guarantee that a destination is already loaded.

#### What are API routes and Route Handlers? / API routes和Route Handler是什么？

**Core answer / 核心回答：** Pages Router API routes use a default handler in pages/api. App Router Route Handlers use named HTTP method exports in a route.ts file. The runtime and deployment model depend on configuration and hosting; an endpoint is not automatically a serverless function just because it is in a Next.js app. / Pages Router 的 API route 在 pages/api 中使用默认 handler；App Router 的 Route Handler 在 route.ts 中导出 HTTP 方法函数。运行时和部署模型取决于配置与托管平台；接口不会因为位于 Next.js 应用中就自动成为 serverless function。

~~~ts
// app/api/hello/route.ts — App Router
export async function GET() {
  return Response.json({ message: "Hello from Next.js" });
}
~~~

Use framework endpoints for colocated, bounded server work such as webhooks or a small proxy. A larger backend may need its own service boundary, runtime, and operational controls.

**See also:** [React Basics / React基础](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) for client navigation and document models; [Node.js Fundamentals / Node.js基础](../../engineering-foundations/backend/node-js-fundamentals.md) for server runtime constraints.

**Sources checked 2026-10-15:** [React 19.3 versions and release](https://react.dev/versions), [React `hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot), [React `useEffect`](https://react.dev/reference/react/useEffect), [React `Suspense`](https://react.dev/reference/react/Suspense), [Next.js 16.4.1 App Router migration guide](https://nextjs.org/docs/app/guides/migrating/app-router-migration), [Next.js 16.4.1 Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data), [Pages Router getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props), [Pages Router getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths), [Pages Router Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration), [use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache), [Incremental Static Regeneration](https://nextjs.org/docs/app/guides/incremental-static-regeneration), [Link](https://nextjs.org/docs/app/api-reference/components/link), and [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route).
## 32. Performance Metrics and Analysis / 性能指标与分析

### Performance Metrics and Analysis / 性能指标与分析

#### What are the Core Web Vitals? / 什么是Core Web Vitals？

**Core answer / 核心回答：** The current Core Web Vitals are LCP for loading, INP for responsiveness, and CLS for visual stability. “Good” thresholds are LCP at or below 2.5 seconds, INP at or below 200 ms, and CLS at or below 0.1, evaluated at the 75th percentile of real page visits, segmented by mobile and desktop. / 当前 Core Web Vitals 包括衡量加载的 LCP、衡量响应性的 INP，以及衡量视觉稳定性的 CLS。“良好”阈值为 LCP 不超过 2.5 秒、INP 不超过 200 毫秒、CLS 不超过 0.1，并按真实访问数据的第 75 百分位评估。

| Metric | What it measures | Good threshold |
|---|---|---:|
| **LCP** | When the largest image or text block in the viewport is rendered. | ≤ 2.5 s |
| **INP** | A latency intended to represent all or nearly all interactions during a page visit. | ≤ 200 ms |
| **CLS** | Unexpected visual instability from layout shifts. | ≤ 0.1 |

##### Other render and navigation milestones / 其他渲染与导航里程碑

| Milestone | Meaning |
|---|---|
| **FCP** | First Contentful Paint: the first text or image content is rendered. |
| **DOMContentLoaded (DCL)** | The HTML is parsed and deferred/module scripts have executed; it does not wait for images or async scripts. |
| **load** | The document and dependent resources such as scripts, stylesheets, frames, and non-lazy images have loaded. |

These milestones have different scopes; do not treat them as a fixed sequence with LCP. DCL is useful when DOM readiness matters, while load waits for dependent resources.

FID was retired as a Core Web Vital in March 2024 and replaced by INP. FCP, TTFB, long tasks, and TBT remain useful diagnostic metrics, but they are not Core Web Vitals.

##### Field data and lab data / 真实用户数据与实验室数据

Core Web Vitals are primarily field metrics. Real-user monitoring shows the experience across actual devices, networks, routes, and interactions. Lab tools such as Lighthouse and DevTools help reproduce and diagnose issues before release, but their results do not equal field results.

Lighthouse cannot measure a page's real INP without user interactions; Total Blocking Time is a lab proxy, not the same metric. A load-only lab run may also miss layout shifts caused later by interaction. Compare field data at the same percentile and device segment when checking whether users improved.

#### How do you profile a page? / 如何分析页面性能？

Use tools that answer a specific question:

- **Performance panel:** inspect main-thread tasks, rendering, layout, and interaction traces.
- **Network panel:** inspect request timing, blocking, transfer size, and cache behavior.
- **React Profiler:** inspect which components render during a recorded interaction.
- **Lighthouse:** collect a repeatable lab trace and diagnostic opportunities.

Record the route, device and network conditions, browser, and whether the measurement is field or lab. A score is a signal; inspect the trace and user impact before choosing a fix.

#### How do you diagnose a slow page? / 如何诊断页面变慢？

**Core answer / 核心回答：** Separate slow initial display from slow interaction, then identify the dominant cost before changing code. The cause may be server response, network transfer, JavaScript execution, layout, rendering, or a specific event handler. / 先区分首屏显示慢和交互响应慢，再找出主要成本后修改代码。原因可能是服务端响应、网络传输、JavaScript 执行、布局、绘制或特定事件处理器。

| Symptom | Inspect first |
|---|---|
| Main content appears late | TTFB, redirects, critical requests, LCP resource discovery and render delay. |
| Input feels delayed | Long main-thread tasks, event-handler work, and work scheduled after input. |
| Content jumps | Missing image or embed dimensions, late injected content, and font swaps. |
| Route bundle is large | Emitted chunk composition and whether deferred code is actually split. |

Potential changes include caching immutable assets, reducing unnecessary JavaScript, splitting rarely used routes, reserving image space, and virtualizing a measured long list. Re-measure the same user-visible interaction after the change.

#### How does HTTP caching help? / HTTP缓存如何帮助性能？

A fresh cached response can be reused according to its freshness policy. After it becomes stale, validators such as ETag can let a client ask whether the representation changed; the server can answer that the stored response remains valid. Content-hashed assets can use a long freshness lifetime because a changed file receives a different URL.

- **Cache-Control: max-age=N** sets a freshness lifetime.
- **Cache-Control: no-cache** permits storage but requires validation before reuse.
- **Cache-Control: no-store** instructs caches not to store the response.
- **ETag** is a validator used with conditional requests; it is not itself a cache lifetime.

Choose policy by resource and user-data sensitivity. Do not apply one cache rule to both versioned static assets and personalized responses.

#### What is the difference between debounce and throttle? / debounce和throttle有什么区别？

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

#### How do you improve first-screen rendering? / 如何改善首屏呈现？

Start with the actual LCP element and critical path. Make that resource discoverable promptly, avoid lazy-loading the LCP image, and reserve dimensions for images or embeds to prevent layout shifts. Defer below-the-fold images and non-critical code when the measurement shows they compete with critical work. SSR or static output can help in some routes, but does not by itself guarantee a good LCP or INP.

#### How can an analytics SDK limit work during navigation? / 如何降低分析SDK对页面的影响？

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

**See also:** [Image Lazy Loading / 图片懒加载](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for image loading choices; [Rendering and Computation Optimization / 渲染与计算优化](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for React and long-list work.

**Sources checked 2026-10-15:** [PerformancePaintTiming (FP/FCP)](https://developer.mozilla.org/en-US/docs/Web/API/PerformancePaintTiming), [DOMContentLoaded event](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event), [Window load event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event), [Web Vitals](https://web.dev/articles/vitals), [INP](https://web.dev/articles/inp), [LCP](https://web.dev/articles/lcp), [CLS](https://web.dev/articles/cls), [Lab and Field Data Differences](https://web.dev/articles/lab-and-field-data-differences), [HTTP Caching (RFC 9111)](https://www.rfc-editor.org/rfc/rfc9111.html), [ETag (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html#name-etag), [Beacon specification](https://w3c.github.io/beacon/).
## 33. Rendering and Computation Optimization / 渲染与计算优化

### Rendering and Computation Optimization / 渲染与计算优化

#### How does virtual scrolling work? / 虚拟滚动如何工作？

**Core answer / 核心回答：** Virtual scrolling keeps a scrollable viewport but mounts only the visible rows and a small overscan buffer. The list's full data may still take memory or computation; virtualization mainly reduces the rendered DOM and related layout work. / 虚拟滚动保留可滚动视口，但只挂载可见行和少量缓冲行。完整列表的数据仍可能占用内存或计算时间；虚拟化主要减少渲染的 DOM 和相关布局工作。

A fixed-height implementation can estimate the visible range directly. The outer spacer represents the full list height so the scrollbar has the right extent; the mounted window is offset by the height of the skipped rows. Variable-height rows need measurement or estimates, and all virtualizers need correct container dimensions and scroll behavior.

~~~jsx
function VirtualWindow({ items, scrollTop, viewportHeight, rowHeight = 40 }) {
  const overscan = 3;
  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const end = Math.min(
    items.length,
    Math.ceil((scrollTop + viewportHeight) / rowHeight) + overscan
  );

  return (
    <div style={{ height: items.length * rowHeight, position: "relative" }}>
      <div style={{ position: "absolute", top: start * rowHeight, left: 0, right: 0 }}>
        {items.slice(start, end).map(item => (
          <div key={item.id} style={{ height: rowHeight }}>{item.label}</div>
        ))}
      </div>
    </div>
  );
}
~~~

Here scrollTop and viewportHeight are measured from the scroll container; production code must keep those measurements synchronized and account for focus, keyboard navigation, and screen-reader expectations.

| Use when | Cost to account for |
|---|---|
| Profiling shows DOM or layout cost from a large rendered list. | More complex focus, accessibility, measurement, and scroll restoration behavior. |
| A list is unbounded or grows with user activity. | Data transformation may still be O(n), even when mounted rows are limited. |

For React, packages include react-window and @tanstack/react-virtual. Choose an adapter and API version supported by the application.

#### How do you tune React rendering? / 如何优化React渲染？

**Core answer / 核心回答：** First identify which interaction is expensive. Keep state close to the components that use it, avoid unnecessary update chains, and measure before adding memoization. A component render is not automatically a DOM mutation. / 先确认哪个交互成本高。将 state 放在实际使用它的组件附近，避免不必要的更新链，并在添加 memoization 前进行测量。组件 render 不等于一定修改 DOM。

- **Stable keys:** use a data identity when sibling items can change order or membership. Use an index only for fixed lists.
- **Memoization:** React.memo, useMemo, and useCallback can help at measured boundaries; state and context changes can still render a memoized component.
- **State placement:** local transient state can often stay near its consumers instead of making a large subtree observe every update.
- **Hidden versus removed:** CSS display:none keeps the component in the React tree. Its state and Effects remain active while hidden. Conditional removal unmounts it and runs cleanup; remounting creates a new instance.
- **Fragments:** avoid an extra DOM wrapper when one is not needed. A fragment does not guarantee a measurable performance improvement.
- **Profiler:** record the actual interaction with browser and React profiling tools before changing architecture.

~~~jsx
const MemoizedRow = memo(function Row({ item, onSelect }) {
  return (
    <button onClick={() => onSelect(item.id)}>
      {item.name}
    </button>
  );
});
~~~

A new callback or object prop can prevent a memoized child from skipping its render, but inline functions are not inherently wrong. Add useCallback or useMemo when the child is expensive and the identity boundary matters, not as a blanket rule.

#### CSS sprites and rendering changes / CSS Sprite与渲染改动

A CSS sprite combines small images into one image. Give each icon a fixed-size element and use background-position to expose its rectangle, for example background-position: -32px -16px. This can reduce separate image requests when request overhead matters, but it couples assets to one file: updating one icon invalidates the combined image and coordinates are harder to maintain. HTTP/2 multiplexes multiple requests over one connection, so request count alone is not enough reason to build a sprite; compare cache behavior, bytes, and maintenance cost for the actual asset set.

~~~css
.icon-edit {
  width: 16px;
  height: 16px;
  background-image: url("/icons.png");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
~~~

#### Which CSS changes are worth testing? / 哪些CSS改动值得测试？

Layout, paint, compositing, and JavaScript can all affect a frame. Animate transform or opacity when that fits the design, but confirm the result in a trace; these properties do not make every animation free. Avoid forcing synchronous layout by reading layout and then writing layout repeatedly in the same task.

will-change is a hint, not a command to allocate a compositor layer. Use it narrowly and only when a measured animation benefits; unnecessary use can consume memory and make performance worse. Reducing DOM work and measuring real interactions are more reliable than assuming a shorter selector or shorthand property will speed up a page.

**See also:** [Browser HTML and CSS / 浏览器中的HTML与CSS](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for rendering stages; [Performance Metrics and Analysis / 性能指标与分析](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for measurement.

**Sources checked 2026-10-15:** [React: memo](https://react.dev/reference/react/memo), [React: useMemo](https://react.dev/reference/react/useMemo), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TanStack Virtual](https://tanstack.com/virtual/latest/docs/introduction), [CSS Will Change Module](https://www.w3.org/TR/css-will-change-1/), [MDN background-position](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-position), [HTTP/2 RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing).
## 34. Lodash / Lodash工具库

### Lodash / Lodash工具库

Lodash provides utilities for arrays, collections, objects, functions, and strings. Use this page as a lookup; compare simple operations with the language's built-in APIs and check the installed Lodash version.

#### Common utilities / 常用工具

**Core answer / 核心回答：** Lodash is most useful when its path, collection, or timing contract saves repeated edge-case code; check the exact method signature before substituting a native operation. / Lodash 在其路径、集合或定时语义能够减少重复边界处理时最有价值；替换为原生方法前应核对具体方法的签名与行为。

##### Arrays / 数组

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

##### Collections / 集合

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

##### Objects / 对象

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

##### Strings / 字符串

| Signature | Example result |
|---|---|
| _.camelCase(string) | _.camelCase("Foo BAR") → "fooBar" |
| _.kebabCase(string) | _.kebabCase("fooBar") → "foo-bar" |
| _.snakeCase(string) | _.snakeCase("fooBar") → "foo_bar" |
| _.capitalize(string) | _.capitalize("hello") → "Hello" |
| _.startCase(string) | _.startCase("fooBar") → "Foo Bar" |

#### Debounce and throttle / 防抖与节流

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

#### When should you use Lodash? / 何时使用Lodash？

Use the library when its edge-case behavior or object/path API simplifies real code. For a known object shape, optional chaining may be clearer; for unique values, Set may fit; for deep cloning, choose an API only after checking its supported data types and semantics. Bundle impact depends on module format and build configuration. Use per-method imports where appropriate and measure the production output rather than assuming a specific size reduction.

**See also:** [Modern JavaScript Features / 现代JavaScript特性](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7) for native alternatives such as structuredClone; [Performance Metrics and Analysis / 性能指标与分析](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for choosing debounce or throttle by workload.

**Sources checked 2026-10-15:** [Lodash 4.17.21 API source, including debounce and throttle](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md), [Array.prototype.flat()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat), [Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing).
## 35. ahooks / ahooks Hook库

### ahooks / ahooks Hook库

ahooks is a collection of React Hooks for recurring UI and data-fetching patterns. The APIs below follow the current documentation checked on 2026-10-15; verify them against the package version installed in a project.

**Core answer / 核心回答：** ahooks packages common React state, effect, request, and list patterns into Hooks; its helpers still follow React’s render and Effect rules, and each API must match the installed version. / ahooks 将常见的 React 状态、Effect、请求和列表模式封装成 Hook；这些工具仍遵守 React 的 render 与 Effect 规则，每个 API 都应与项目安装版本一致。

#### Data fetching / 数据请求

##### useRequest

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

##### usePagination and useInfiniteScroll

usePagination expects a service that returns a total count and list, and exposes pagination state and change methods.

~~~javascript
const { data, loading, pagination } = usePagination(
  ({ current, pageSize }) => fetchUsers({ current, pageSize }),
  { defaultPageSize: 20 }
);

pagination.changeCurrent(2);
~~~

useInfiniteScroll expects a service that returns a data object containing a list. Its result includes data, loading, loadingMore, noMore, and loadMore. Configure the scroll target and no-more condition to match the UI; it cannot determine the product's pagination contract for you.

#### State and browser storage / 状态与浏览器存储

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

#### Function identity and list rendering / 函数引用与列表渲染

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

Variable-height rows need the measurement behavior supported by the installed version. See [Rendering and Computation Optimization / 渲染与计算优化](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96).

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

#### Effects and timing / Effect与时机

useMount and useUnmount package common Effect setup and cleanup. Their behavior follows React's Effect lifecycle, including the extra development setup-and-cleanup cycle under root StrictMode. They do not mean “run once for the lifetime of this process.”

useDebounce and useThrottle return delayed or rate-limited values; useDebounceFn and useThrottleFn wrap functions. Check whether the chosen hook returns a value, run function, or cancellation control before relying on an example from another version.

**Reach for ahooks / 何时使用：** It can reduce repeated hook boilerplate when its API matches the product behavior. Keep custom logic when cancellation, caching, errors, or data ownership need explicit control. For server-state caching and synchronization, compare a dedicated data library such as TanStack Query or SWR instead of assuming one hook collection covers every use case.

**See also:** [Advanced React / React进阶](#30.%20Advanced%20React%20/%20React%E8%BF%9B%E9%98%B6) for Hook rules and Effect cleanup plus the generic server-state cache, mutation, concurrency, and Suspense lifecycle; [Performance Metrics and Analysis / 性能指标与分析](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for debounce and throttle tradeoffs.

**Sources checked 2026-10-15:** [ahooks useRequest](https://ahooks.js.org/hooks/use-request), [ahooks v3.10.0 useRequest implementation](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/Fetch.ts), [ahooks v2 to v3 upgrade notes](https://ahooks.js.org/guide/upgrade/), [ahooks 2.6.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v2.6.0/packages/hooks/src/useVirtualList/index.ts), [ahooks 3.10.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useVirtualList/index.ts), [usePagination](https://ahooks.js.org/hooks/use-pagination), [useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll), [useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state), [useLatest](https://ahooks.js.org/hooks/use-latest), [useMemoizedFn](https://ahooks.js.org/hooks/use-memoized-fn), [useVirtualList](https://ahooks.js.org/hooks/use-virtual-list), [useCreation](https://ahooks.js.org/hooks/use-creation), [useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn), [useThrottle](https://ahooks.js.org/hooks/use-throttle), [useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn), [useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list), [useUnmount](https://ahooks.js.org/hooks/use-unmount), [React StrictMode](https://react.dev/reference/react/StrictMode).
## 36. Frontend Testing / 前端测试

### Frontend Testing / 前端测试

#### How should frontend tests be divided? / 前端测试如何分层？

**Core answer / 核心回答：** Put each assertion at the lowest layer that can verify the behavior reliably. Unit tests isolate pure logic, integration tests exercise boundaries between components and services, and browser tests verify important end-to-end flows. This is a risk and feedback-cost heuristic, not a required test-count pyramid. / 在能够可靠验证行为的最低层测试。单元测试隔离纯逻辑，集成测试覆盖组件与服务之间的边界，浏览器测试验证重要端到端流程。这是权衡风险和反馈成本的经验方法，不是固定的测试数量金字塔。

| Layer | Useful for | Example tools |
|---|---|---|
| Unit | Pure functions and isolated behavior | Jest, Vitest |
| Integration | Components, hooks, context, and API boundaries together | React Testing Library with Jest or Vitest |
| End-to-end | Browser navigation, persistence, and critical user journeys | Playwright, Cypress |

Keep browser tests for behavior that depends on the real browser or application wiring. A test pyramid is a planning aid; a project's distribution should follow its actual risks and feedback costs.

#### Jest fundamentals / Jest基础

~~~javascript
describe("calculator", () => {
  test("adds two numbers", () => {
    expect(2 + 2).toBe(4);
  });

  test("compares object values", () => {
    expect({ count: 2 }).toEqual({ count: 2 });
  });
});
~~~

toBe uses Object.is semantics. toEqual compares nested values; toStrictEqual also distinguishes cases such as missing properties and undefined values. Common matchers include toContain, toHaveLength, toThrow, and toHaveBeenCalledWith.

Setup hooks run at different scopes: beforeAll and afterAll surround a suite, while beforeEach and afterEach run around each test. Restore state that could leak between tests.

##### Mock functions / Mock函数

~~~javascript
const save = jest.fn();
save({ id: 1 });

expect(save).toHaveBeenCalledWith({ id: 1 });

save.mockResolvedValue({ ok: true });
await expect(save()).resolves.toEqual({ ok: true });
~~~

jest.spyOn wraps an existing method and can be restored. The cleanup operations differ:

- **mockClear** clears call history while keeping the implementation.
- **mockReset** clears call history and the mock implementation.
- **mockRestore** restores the original implementation for a function created by spyOn. restoreAllMocks also restores spies and properties replaced with replaceProperty.

For a CommonJS test transformed with babel-jest, jest.mock is hoisted by the transformer and the module can be required after the mock declaration:

~~~javascript
// CommonJS / babel-jest transformed module test.
jest.mock("./api", () => ({ fetchUser: jest.fn() }));
const { fetchUser } = require("./api");

test("loads a user", async () => {
  fetchUser.mockResolvedValue({ id: 1, name: "Ada" });
  await expect(fetchUser(1)).resolves.toMatchObject({ name: "Ada" });
});
~~~

Native ESM evaluates static imports before test code, so the CJS hoisting example does not transfer directly; Jest documents unstable_mockModule followed by dynamic import for ESM. A spy created with jest.spyOn calls the original method by default; mockImplementation replaces it, and mockRestore restores the original:

~~~javascript
const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
// assertions using the spy
warnSpy.mockRestore();
~~~

#### React Testing Library / React Testing Library

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

#### Testing custom Hooks and snapshots / 测试自定义Hook与快照

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

**See also:** [Advanced React / React进阶](#30.%20Advanced%20React%20/%20React%E8%BF%9B%E9%98%B6) for custom Hook semantics; [Git Essentials / Git基础](../../engineering-foundations/version-control/git-essentials.md) for how tests fit into review and CI.

**Sources checked 2026-10-15:** [Jest Mock Functions](https://jestjs.io/docs/mock-functions), [Jest Object and Mock Lifecycle](https://jestjs.io/docs/jest-object), [Jest ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules), [React Testing Library API](https://testing-library.com/docs/react-testing-library/api/), [Testing Library Queries](https://testing-library.com/docs/queries/about/), [user-event](https://testing-library.com/docs/user-event/intro/), [Testing Library Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/).
