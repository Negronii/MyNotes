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

#### Semantic HTML and accessibility

Choose elements for their meaning and built-in behavior. Use headings to express the page outline, landmarks such as `<main>` and `<nav>` to identify regions, a `<button>` for an action, and an `<a href>` for navigation. Semantic controls provide keyboard and assistive-technology behavior that a styled `<div>` does not provide by default.

Give form controls programmatic labels with `<label for="…">` or a properly nested label. Give informative images useful alternative text; use `alt=""` for decorative images so they do not add noise to the text alternative. Do not use color or visual positioning as the only way to convey a required state or relationship.

Keep the source order meaningful. CSS can change visual placement without changing the underlying document sequence used by nonvisual presentation.

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

Reach for this when you need to remember the property names and what each one does. For "how should I approach this layout?" style interview answers, the patterns live in [`2.6 CSS Interview Questions`](#7.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98).

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
| `align-content` | cross-axis alignment (between lines, when wrapping) | `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `stretch` |
| `gap` | spacing between items | any length |

`align-content` only has a visible effect when items wrap onto multiple lines.

##### Item properties

| Property | What it controls |
|---|---|
| `flex-grow` | share of *extra* space (unitless proportion) |
| `flex-shrink` | share of *deficit* space when items don't fit |
| `flex-basis` | starting size before grow/shrink (length or `auto`) |
| `flex` | shorthand: `flex: <grow> <shrink> <basis>` |
| `align-self` | override `align-items` for one item |
| `order` | reorder items visually (without changing DOM order) |

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

**Equal-height columns** — flex items automatically stretch to match the tallest sibling in their cross-axis direction.

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

Track sizes can be absolute (`100px`), flexible (`1fr`), content-based (`auto`, `min-content`, `max-content`), or intrinsic (`minmax(200px, 1fr)`, `repeat(auto-fit, minmax(200px, 1fr))`).

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
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}
```

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

**See also:** [`2.1 HTML & CSS Basics`](#2.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for CSS units used with `fr`/`minmax`, [`2.6 CSS Interview Questions`](#7.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98) for worked interview examples using these layouts.
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

Reach for this when you need to measure an element in JavaScript and can't remember which property includes which layers of the box model. These are all geometry properties — reading them forces a layout flush, so use sparingly in tight loops (see [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for layout thrashing).

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

offsetHeight  = border + padding + content (+ scrollbar)   — total visible size
clientHeight  = padding + content                          — inside space
scrollHeight  = padding + FULL content (incl. overflowed)  — total scrollable size
```

| Property | Includes | Excludes | Writable? |
|---|---|---|---|
| `offsetHeight` / `offsetWidth` | content, padding, border, scrollbar | margin | no |
| `clientHeight` / `clientWidth` | content, padding | border, scrollbar, margin | no |
| `scrollHeight` / `scrollWidth` | content (including overflowed), padding | border, scrollbar, margin | no |
| `scrollTop` / `scrollLeft` | current scroll offset | — | **yes** |
| `offsetTop` / `offsetLeft` | distance from element border to `offsetParent`'s inner border | — | no |
| `getBoundingClientRect()` → `.width` / `.height` | same as `offsetWidth` / `offsetHeight` (viewport-relative) | margin | no |

#### `offsetHeight` / `offsetWidth`

Total visible size including padding, border, and rendered scrollbar — excludes margin.

```text
offsetHeight = content height + padding-top + padding-bottom + border-top + border-bottom (+ scrollbar)
```

#### `clientHeight` / `clientWidth`

Visible content area plus padding — excludes border, scrollbar, and margin. This is the space actually available *for* content.

```text
clientHeight = content height + padding-top + padding-bottom
```

#### `scrollHeight` / `scrollWidth`

Full size of the element's content including anything hidden by overflow. When content fits inside, `scrollHeight === clientHeight`.

```text
scrollHeight = total content height + padding (includes overflow beyond viewport)
```

#### `scrollTop` / `scrollLeft`

Pixels the content has been scrolled vertically / horizontally. **Writable** — set it to control scroll programmatically.

```javascript
const el = document.getElementById('container');
console.log(el.scrollTop);
el.scrollTop = 0;  // scroll to top
```

#### `offsetTop` / `offsetLeft`

Distance from the element's outer border to its `offsetParent`'s inner border. `offsetParent` is the nearest positioned ancestor (`position` other than `static`), defaulting to `<body>` if none exists.

#### `getBoundingClientRect()`

Returns a `DOMRect` with the element's size and position **relative to the viewport**. The go-to method for scroll-aware positioning (tooltips, visibility checks, drag handles).

```javascript
const rect = element.getBoundingClientRect();
// rect.top     - distance from viewport top to element top
// rect.bottom  - distance from viewport top to element bottom
// rect.left    - distance from viewport left to element left
// rect.right   - distance from viewport left to element right
// rect.width   - element width (including border)
// rect.height  - element height (including border)
```

**Common pattern — checking if an element is in the viewport:**

```javascript
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top < window.innerHeight &&
    rect.bottom > 0 &&
    rect.left < window.innerWidth &&
    rect.right > 0
  );
}
```

For real visibility tracking (e.g., lazy loading, analytics), prefer `IntersectionObserver` — it doesn't force layout. See [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD).

#### When to reach for which

- Need **total rendered size** including border? → `offsetHeight` / `offsetWidth` or `getBoundingClientRect().height/width`.
- Need **inner content area** (for sizing children)? → `clientHeight` / `clientWidth`.
- Need to know if **overflow exists**? → compare `scrollHeight > clientHeight`.
- Need **current scroll position**, or to **scroll programmatically**? → `scrollTop` / `scrollLeft`.
- Need **viewport-relative position** (for tooltips, drag, scroll effects)? → `getBoundingClientRect()`.
- Need **position within parent** (for layout math)? → `offsetTop` / `offsetLeft` (watch out: relative to `offsetParent`, not necessarily the direct parent).

**See also:** [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) on layout thrashing when reading these in loops, [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for `IntersectionObserver`-based visibility.
## 7. CSS Interview Questions / CSS面试题

### How do you clear floats, and why do you need to?

**Headline (30s):** Floated children are removed from the normal flow, so their parent collapses to zero height. You "clear" the float by either (a) making the parent a Block Formatting Context — `display: flow-root` or `overflow: hidden` — so it contains its floats, or (b) adding a clearing pseudo-element that forces the parent to extend past them.

Floating elements removes them from the normal flow of a document, causing parent containers to collapse if not properly handled. It's crucial for front-end developers to understand the methods available to manage this behavior effectively.

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
  display: flow-root; /* clean, no side effects */
}

/* Legacy alternative */
.parent {
  overflow: hidden;
}
```

**Pros:** One line, no pseudo-element, clean semantics.
**Cons:** `overflow: hidden` clips content that extends past the parent — use `flow-root` when clipping isn't wanted.

##### Fixed dimensions

Straightforward but inflexible.

```css
.parent {
  width: 300px;
  height: 200px;
}
```

**Pros:** Trivial, universal support.
**Cons:** Breaks if child content grows — any overflow is your problem.

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

**Gotcha — why floats even need clearing:** Floats were designed for wrapping text around images, not for page layout. They leave the normal flow, so height collapses in their parent. Flexbox and Grid solve layout problems directly and don't have this issue — float-based layouts are legacy.

**See also:** [`2.2 Box Model and BFC`](#3.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) on how BFCs contain floats, [`2.3 Flex & Grid Layout`](#4.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for modern alternatives.

---

### How do you build a three-column layout with fixed sides and a fluid middle?

**Headline (30s):** Six valid approaches, ranked modern → legacy: Flexbox (`flex-grow: 1` on the middle), Grid (`grid-template-columns: 100px 1fr 100px`), absolute positioning, table-cell, float + `calc()`, and inline-block + `calc()`. For new code, use Grid or Flex. Know the others so you can read legacy CSS.

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
.center { float: left; width: calc(100% - 100px); }
```

**Pros:** Broad compatibility with older browsers.
**Cons:** Needs `clear` fixes; brittle.

#### Table display layout

```css
.parent { display: table; }
.left, .center, .right { display: table-cell; }
```

**Pros:** Stable and predictable rendering.
**Cons:** Semantically wrong for non-tabular data.

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
.center { flex-grow: 1; }
```

**Pros:** Modern, responsive, minimal code.
**Cons:** Only a concern for very old-browser support.

#### Grid layout

```css
.parent {
  display: grid;
  grid-template-columns: 100px 1fr 100px;
}
```

**Pros:** Cleanest, intention-revealing.
**Cons:** Not supported in truly ancient browsers.

**Gotcha — `calc(100% - 200px)` + `box-sizing: content-box`:** If `.parent` has padding and you're using content-box, `100%` doesn't mean what you think. Always normalize with `box-sizing: border-box`.

**See also:** [`2.3 Flex & Grid Layout`](#4.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for the property reference.

---

### How do you build a two-column layout with one fixed and one responsive side?

**Headline (30s):** Same ladder as the three-column layout but simpler. Flexbox (`flex-grow: 1` on the fluid side) or Grid (`grid-template-columns: 200px 1fr`) for modern code. Float, absolute positioning, and inline-block are legacy fallbacks.

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
.right-side { flex-grow: 1; }
```

**Grid:**

```css
.container {
  display: grid;
  grid-template-columns: 200px 1fr;
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
.right-side { display: inline-block; vertical-align: top; }
.right-side { width: calc(100% - 200px); }
```

**Gotcha — the whitespace between inline-blocks:** Browsers render whitespace (including newlines) between inline-block elements as a space character, which shifts your layout. `font-size: 0` on the parent is the classic workaround. Flexbox and Grid have no such quirk.

---

### How do you center an element in CSS?

**Headline (30s):** Flexbox or Grid for modern code (`place-items: center` / `justify-content + align-items: center`). If you need to support ancient browsers, fall back to absolute + `transform: translate(-50%, -50%)` (works for unknown dimensions) or absolute + negative margins (fixed dimensions only).

```html
<div class="container">
  <div class="center-fixed"></div>
  <div class="center-auto"></div>
  <div class="center-dynamic"></div>
  <div class="center-flex"></div>
  <div class="center-grid"></div>
  <div class="center-table"></div>
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

**Flexbox (preferred):**

```css
.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}
```

**CSS Grid:**

```css
.center-grid {
  display: grid;
  place-items: center;
  height: 100vh;
}
```

**Absolute + transform:**

```css
.container { position: relative; }

.center-dynamic {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**Table-cell:**

```css
.container   { display: table; }
.center-table {
  display: table-cell;
  vertical-align: middle;
  text-align: center;
}
```

#### Centering with fixed dimensions

**Absolute + negative margin:**

```css
.container { position: relative; }

.center-fixed {
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

.center-auto {
  position: absolute;
  width: 200px;
  height: 100px;
  top: 0; right: 0; bottom: 0; left: 0;
  margin: auto;
}
```

Setting `top/right/bottom/left: 0` expands the element's margin box to fill the container; `margin: auto` then distributes the leftover space evenly on all sides because the element has fixed dimensions.

**Gotcha — `transform: translate(-50%, -50%)` on a percentage parent:** `transform` uses the element's *own* size, so this centers correctly even when the element's size is unknown. The negative-margin trick only works if you know the exact dimensions ahead of time.

---

### How do you draw a triangle with pure CSS?

**Headline (30s):** Give a zero-size element thick borders, make three of them transparent, and color the fourth. The "visible" border forms the triangle. No image, no HTTP request, trivially recolorable.

CSS-based triangles improve loading times and reduce bandwidth by eliminating an HTTP request. Scalable, easily recolorable.

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

- A 20×20 "element" made of borders only (content is zero size).
- Four borders meet at 45° diagonals. Three transparent borders + one colored = a triangle pointing in the direction opposite the colored side.

**Customization:**

- `border-bottom` solid → triangle points **up**.
- `border-top` solid → triangle points **down**.
- `border-left` solid → triangle points **right**.
- `border-right` solid → triangle points **left**.

**Gotcha — modern alternative:** `clip-path: polygon(50% 0, 100% 100%, 0 100%)` is often cleaner when the triangle size is dynamic. Use borders for tiny fixed-size arrow indicators, `clip-path` for scalable shapes.

---

### How do you render a crisp 1px line on Retina / high-DPR screens?

**Headline (30s):** On a 2x DPR screen, 1 CSS pixel maps to 2 physical pixels, so a `border: 1px` line appears "chunky". The classic fix is a pseudo-element at 100% of the container width + `transform: scaleY(0.5)`, which lets you render a half-CSS-pixel (i.e. one physical pixel) line without running into the browser's handling of fractional px values.

#### Using a pseudo-element + transform

```css
.box::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}
```

#### Handling borders with `border-radius`

When the element has `border-radius`, borders and scales interact awkwardly. Use `box-shadow` instead:

```css
.box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

`box-shadow` at fractional values is handled more consistently across modern browsers than a fractional `border-width`.

**Gotcha — `1px solid` on devices with variable DPR:** A single line might look 1px on a laptop (DPR 1), 2px on a 2x phone, or 3px on a 3x phone. If visual consistency matters, feature-detect DPR with `window.devicePixelRatio` and adjust — or use SVG for scale-invariant strokes.

---

### How do you prevent the 300ms tap delay on mobile?

**Headline (30s):** Modern browsers disable the 300ms double-tap-to-zoom delay automatically once they see `<meta name="viewport" content="width=device-width, initial-scale=1">`. That's usually all you need. Libraries like FastClick are legacy — don't add them in new code.

On mobile web apps, browsers historically waited ~300ms after a tap to check whether a second tap was coming (zoom gesture). This delay used to be worked around with libraries like FastClick. Modern browsers detect responsive intent from the viewport meta tag and skip the delay.

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

**Why this works:** A site that declares `width=device-width` is telling the browser "I'm designed for mobile; don't pinch-zoom me." Without that signal, the browser assumes it might need the zoom gesture and waits to see if a second tap is coming.

**Gotcha — FastClick is obsolete and harmful:** On modern browsers, FastClick can actually *cause* double-firing of events because it dispatches synthetic clicks on top of native ones. Remove it from new projects.
## 8. CSS Position, Display, and Animations / CSS定位、显示与动画

### How do the CSS `position` values differ?

**Headline (30s):** Five values. `static` is the default (normal flow, offsets do nothing). `relative` reserves its spot in the flow but lets you offset it visually. `absolute` is removed from the flow, positioned relative to its nearest *positioned* ancestor. `fixed` is removed from the flow, positioned relative to the viewport. `sticky` is a hybrid — it flows normally until it crosses a scroll threshold, then sticks like `fixed`.

| Value | In flow? | Positioned relative to | Scrolls with page? |
|---|---|---|---|
| `static` (default) | yes | — (offsets ignored) | yes |
| `relative` | yes (original space reserved) | its own original position | yes |
| `absolute` | no | nearest positioned ancestor | yes (relative to ancestor) |
| `fixed` | no | viewport | no |
| `sticky` | yes → no (after threshold) | scroll container | yes, until sticky |

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

Element removed from normal flow — no space reserved. Positioned relative to its nearest **positioned ancestor** (any ancestor with `position: relative`, `absolute`, `fixed`, or `sticky`). With no positioned ancestor, the initial containing block (usually `<html>`) is used.

```css
.parent { position: relative; } /* creates positioning context */
.child  { position: absolute; top: 0; right: 0; }
```

#### `fixed`

Removed from normal flow; positioned relative to the **viewport**. Stays put while the page scrolls.

```css
.navbar { position: fixed; top: 0; left: 0; right: 0; }
```

**Gotcha — `fixed` inside a `transform`ed ancestor:** If any ancestor has `transform`, `filter`, or `perspective` set (even just `translateZ(0)`), the ancestor becomes the new containing block — and your `fixed` element now scrolls with the ancestor instead of the viewport. Easy to miss until you debug why your header isn't sticky on a page with CSS animations.

#### `sticky`

Element starts in normal flow; behaves like `fixed` once scroll crosses a threshold defined by `top`, `right`, `bottom`, or `left`. At least one of those must be set.

```css
.header { position: sticky; top: 0; }
```

**Gotcha — `overflow: hidden` on an ancestor kills `sticky`:** `sticky` only works if its scroll container has `overflow: visible` (or has no overflow set). A `sticky` child inside `overflow: hidden` silently behaves like `relative`. Check the entire ancestor chain when debugging.

#### Stacking context and `z-index`

`z-index` controls stacking order along the z-axis, but **only within the same stacking context**. Elements with `position` other than `static` create a stacking context when `z-index` is set; so do elements with `opacity < 1`, `transform`, `filter`, `will-change`, and a few others.

```css
.layer-a { position: relative; z-index: 1; }
.layer-b { position: relative; z-index: 2; } /* above layer-a */
```

**Gotcha — "my `z-index: 9999` isn't on top":** A stacking context is an isolation boundary. A descendant's `z-index` can never escape to compete with elements outside its context — no matter how high the value. If `.modal` sits inside a parent with `transform: translateZ(0)`, any `z-index` on the modal only competes with *siblings inside that parent*. To fix, raise the `z-index` (or create a stacking context) on an ancestor shared with the element you're trying to overlap.

---

### When should you use `display: none` vs `visibility: hidden` vs `opacity: 0`?

**Headline (30s):** `display: none` removes the element from layout entirely (causes reflow; screen readers ignore it; can't animate). `visibility: hidden` keeps the layout space but hides the pixels (cheaper — repaint only; screen readers still ignore). `opacity: 0` keeps the layout and pixels "there" but invisible — the element still receives clicks and is still announced by screen readers unless you add `aria-hidden`.

| Aspect | `display: none` | `visibility: hidden` | `opacity: 0` |
|---|---|---|---|
| **Space in layout** | removed | reserved | reserved |
| **Receives clicks / events** | no | no | **yes** (add `pointer-events: none` to disable) |
| **Announced by screen readers** | no | no | often yes (add `aria-hidden`) |
| **Can animate** | no (all-or-nothing) | yes, on `visibility` | yes, on `opacity` |
| **Cost when toggled** | reflow + paint | paint only | paint only (composite if promoted) |
| **Affects children** | children hidden | children inherit (can override with `visibility: visible`) | children inherit |

##### Decision guide

- Need the element **gone** — no space, no a11y, responsive toggle? → `display: none`.
- Need to **hide visually but preserve layout** (keep siblings stable)? → `visibility: hidden`.
- Need to **fade in/out** with a transition? → `opacity: 0` (with `pointer-events: none` when hidden, and `aria-hidden` for a11y).

```css
.hidden-flow        { display: none; }
.hidden-space       { visibility: hidden; }
.hidden-transparent { opacity: 0; pointer-events: none; }
```

**Gotcha — transitioning from `display: none`:** You can't fade in something from `display: none` because the element has no "before" frame to animate from. Either use `visibility` + `opacity`, or use the modern `transition-behavior: allow-discrete` (spec-level; Chromium first, with limited older-browser support at time of writing).

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

#### GPU compositing and hardware acceleration

Animating `transform` and `opacity` runs on the **compositor** (GPU) instead of triggering layout/paint. `will-change` hints to the browser to pre-promote the element to its own layer. See [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for the full cost ladder.

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* force GPU layer without visible movement */
}
```

**Gotcha — don't `will-change` everything:** Each hinted element becomes its own compositor layer and eats memory. Use `will-change` only for the element you're actively animating; remove it after the animation is done (via class toggle) if the element persists. Over-hinting can hurt performance on low-end devices.

**Gotcha — `transform: translateZ(0)` is a blunt instrument:** It pre-promotes to a GPU layer but burns memory. `will-change: transform` is the modern, intention-revealing equivalent, but both should only be used when you've measured a performance problem.

**See also:** [`2.4 Browser - HTML & CSS part`](#5.%20Browser%20HTML%20and%20CSS%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%AD%E7%9A%84%20HTML%20%E4%B8%8E%20CSS) for the reflow/repaint cost ladder, [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for when GPU acceleration does and doesn't help.
## 9. JavaScript Basics / JavaScript基础

### `var`, `let`, and `const`

Reach for this when you need to remember the difference between the three variable declarations, including scoping, hoisting, and the Temporal Dead Zone.

#### Quick comparison

| | `var` | `let` | `const` |
|---|---|---|---|
| **Scope** | function | block | block |
| **Hoisted?** | yes, initialized to `undefined` | yes, but uninitialized (TDZ) | yes, but uninitialized (TDZ) |
| **Redeclaration in same scope** | allowed | `SyntaxError` | `SyntaxError` |
| **Reassignment** | allowed | allowed | **not** allowed (binding is frozen) |
| **Must be initialized?** | no | no | yes |

**Default:** use `const`; switch to `let` only when the binding must be reassigned; avoid `var` in new code.

#### `var` — function-scoped, hoisted to `undefined`

A `var` declaration is hoisted to the top of its enclosing function (or global scope), but it's only *initialized* at its declaration line. Accessing before initialization returns `undefined` rather than throwing.

```javascript
console.log(a); // undefined
var a = 10;
console.log(a); // 10

function foo() {
  console.log(a); // undefined  (hoisted function-scoped a, not the outer a)
  var a = 20;
  console.log(a); // 20
}
```

**Quirks worth knowing:**

- Can be redeclared in the same scope without error.
- Ignores block boundaries — a `var` declared inside `if` or `for` leaks to the enclosing function.

#### `let` — block-scoped, Temporal Dead Zone

A `let` declaration is hoisted to the top of its block, but lives in the **Temporal Dead Zone (TDZ)** from the start of the block until the declaration is reached. Access inside the TDZ throws `ReferenceError`.

```javascript
console.log(a); // ReferenceError: Cannot access 'a' before initialization
let a = 10;
console.log(a); // 10

function foo() {
  console.log(a); // ReferenceError (inner a shadows the outer one and is in TDZ)
  let a = 20;
  console.log(a); // 20
  // let a = 30; // SyntaxError: 'a' already declared
}
```

**Key properties:**

- Block-scoped — lives only inside the `{ ... }` it was declared in. (Unlike `var`, `let` doesn't leak out of `if` / `for` blocks.)
- Cannot be redeclared in the same block.

#### `const` — block-scoped, binding frozen

`const` behaves like `let` (block scope, TDZ) **plus**: the variable must be initialized at declaration, and its binding cannot be reassigned. The *contents* of a mutable object pointed to by a `const` binding can still be modified.

```javascript
console.log(a); // ReferenceError (TDZ)
// const a;   // SyntaxError: missing initializer
const a = 10;
// a = 20;   // TypeError: assignment to constant variable

const b = [];
b[0] = 10; // fine — mutating the array
// b = [10]; // TypeError — reassigning the binding
```

**Common misconception:** `const` does not make the value immutable — it makes the *binding* immutable. For deep immutability, use `Object.freeze`, or reach for immutable-data libraries.

#### Best practice

1. **Default to `const`** — most bindings don't need to change after initialization.
2. **Use `let`** only where reassignment is actually needed (loop counters, accumulators).
3. **Don't use `var` in new code.** ES6 made `let`/`const` available everywhere; `var` only remains for extreme legacy-browser support.

**See also:** [`Scope & Closure / 作用域与闭包`](#18.%20Scope%20&%20Closure%20/%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85) for how scope interacts with closures.
## 10. JavaScript Types / JavaScript类型

Four interview questions this note prepares you for:

1. **What are the primitive types in JavaScript?**
2. **What's the difference between primitive and reference types?** (with the classic `a.x = a = {}` gotcha)
3. **How do you reliably check a variable's type?**
4. **What types can be used as object keys, and what happens if you use something else?**

---

#### What are the primitive types in JavaScript?

**Headline (30s):** Seven primitives: `undefined`, `null`, `boolean`, `number`, `string`, `symbol`, `bigint`. Primitives are immutable and compared by value. Everything else (`object`, `array`, `function`, `Date`, `Map`, ...) is a reference type, compared by reference.

| Type | Represents | Quirk worth knowing |
|---|---|---|
| `undefined` | uninitialized value | default for declared-but-unset variables |
| `null` | intentional absence | `typeof null === 'object'` (historical bug) |
| `boolean` | `true` / `false` | falsy values: `false`, `0`, `-0`, `''`, `null`, `undefined`, `NaN` |
| `number` | IEEE 754 double | `NaN !== NaN`; use `Number.isNaN()` |
| `string` | character sequence | immutable |
| `symbol` (ES6) | unique identifier | `Symbol('x') !== Symbol('x')` even with same description |
| `bigint` (ES11) | arbitrary-precision integer | literal suffix `n` (`123n`) |

##### Type-coercion cheat sheet

**To boolean:**

- Falsy: `false`, `0`, `-0`, `''`, `null`, `undefined`, `NaN`.
- Everything else is truthy — including `'0'`, `'false'`, `{}`, `[]`.

**To number:**

| Input | Result |
|---|---|
| `Number('')` | `0` |
| `Number('123')` | `123` |
| `Number('abc')` | `NaN` |
| `Number(true)` | `1` |
| `Number(false)` | `0` |
| `Number(null)` | `0` |
| `Number(undefined)` | `NaN` |
| `Number({})` | `NaN` |

**Gotcha — `NaN !== NaN`:** The only value in JavaScript not equal to itself. To test, use `Number.isNaN(x)` (or `Object.is(x, NaN)`) — never `x === NaN`.

**Gotcha — `typeof null === 'object'`:** A bug from the first version of JavaScript that's too widely depended on to fix. When you need to detect `null`, check `x === null` explicitly.

---

#### Primitive vs reference types — what's the difference?

**Headline (30s):** Primitives live on the stack and are compared by value — copying a primitive duplicates the data. Reference types live on the heap; a variable stores a pointer to that heap slot. Assigning one reference variable to another makes both point to the same object; mutating through one reference shows up through the other.

| | Primitive | Reference |
|---|---|---|
| **Stored in** | stack | heap (variable holds a pointer) |
| **Compared** | by value | by reference |
| **Copy on assignment?** | yes (duplicate data) | no (share the same object) |
| **Mutable?** | no | yes |

##### The classic "right-to-left assignment" gotcha

**What does this print, and why?**

```javascript
let a = {n: 1};
let b = a;
a.x = a = {n: 2};
console.log(a.x);
console.log(b.x);
```

**Output:**

```text
undefined
{n: 2}
```

**Why** — two rules do the heavy lifting:

1. **Sequential assignments execute right-to-left.** `a.x = a = {n: 2}` is `a = {n: 2}` first, then `a.x = (result of that)`.
2. **Dot notation (`a.x`) captures its target at the moment it's evaluated.** Before JS evaluates the right side, it's already decided which object `a.x` refers to — the *original* object (still held by `b`).

**Step by step:**

1. After `let a = {n: 1}; let b = a;` — both `a` and `b` point to `{n: 1}`.
2. JS evaluates `a.x` on the left side, reserving a slot on the original object (now it's `{n: 1, x: undefined}`, still held by both `a` and `b`).
3. JS evaluates the right side: `a = {n: 2}` — `a` now points to a *new* object `{n: 2}`. `b` still points to the old one.
4. JS assigns the right side's value (`{n: 2}`) to the slot it reserved in step 2. That slot is on the *original* object, which only `b` holds now.

**Final state:**

- `a` → `{n: 2}` (no `x` property)
- `b` → `{n: 1, x: {n: 2}}`

So `a.x` is `undefined`; `b.x` is `{n: 2}`.

**Gotcha — do not write code like this in production.** If you see it in an interview, slow down, draw the heap, and walk through each step.

---

#### How do you reliably check a variable's type?

**Headline (30s):** `typeof` works for primitives but misidentifies `null` as `'object'` and treats arrays and plain objects identically. `instanceof` works for objects from a specific constructor (within its prototype chain). The reliable-for-everything answer is `Object.prototype.toString.call(x)` — it returns strings like `'[object Array]'`, `'[object Null]'`, `'[object Date]'` — or a thin wrapper around it like a custom `getType()`.

##### `typeof` — fast, primitive-friendly, lies about `null` and arrays

```javascript
typeof 1;          // 'number'
typeof 'test';     // 'string'
typeof true;       // 'boolean'
typeof undefined;  // 'undefined'
typeof function(){}; // 'function'
typeof null;       // 'object'  ← historical bug
typeof [];         // 'object'  ← arrays look the same as plain objects
typeof {};         // 'object'
```

**Reach for it when:** you just need to verify a primitive, and you're not worried about `null`.

##### `instanceof` — constructor-based, no help for primitives

Checks whether the constructor's `prototype` appears in the value's prototype chain. Under the hood, it invokes `Constructor[Symbol.hasInstance]`.

```javascript
[] instanceof Array;     // true
({}) instanceof Object;  // true
'x' instanceof String;   // false  (primitive string ≠ String object)
```

**Reach for it when:** checking whether an object came from a specific class.

**Gotcha — cross-realm objects:** `instanceof` can return `false` for arrays from another iframe or worker because each realm has its own `Array.prototype`. Use `Array.isArray(x)` for arrays specifically.

##### `Object.prototype.toString.call()` — works for everything

```javascript
Object.prototype.toString.call([1, 2, 3]);   // '[object Array]'
Object.prototype.toString.call(null);         // '[object Null]'
Object.prototype.toString.call(new Date());   // '[object Date]'
Object.prototype.toString.call(/regex/);      // '[object RegExp]'
```

**Reach for it when:** you need a definitive type string that works across realms, handles `null` and `undefined`, and distinguishes built-in object types.

##### A custom `getType` combining all three

```javascript
function getType(val) {
  const t = typeof val;
  if (t !== 'object') return t;        // primitives
  if (val === null) return 'null';
  return Object.prototype.toString.call(val).slice(8, -1).toLowerCase();
}

getType(null);         // 'null'
getType([1, 2, 3]);    // 'array'
getType(new Date());   // 'date'
```

**Reach for it when:** you want one function that gives clean names for everything.

---

#### What types can be used as object keys?

**Headline (30s):** Only **strings** and **symbols**. Anything else is coerced to a string via the value's `toString()`. This means numeric keys are *actually* strings, and two different plain objects used as keys both become `"[object Object]"` — overwriting each other. If you need non-string keys, use `Map` instead.

##### Key conversion rules

- **String or symbol:** used directly.
- **Any other type:** converted via `toString()`.
  - Numeric keys: `obj[123]` and `obj['123']` access the same slot.
  - Plain objects: all become `"[object Object]"` — they collide.
  - Arrays: `[1, 2]` becomes `"1,2"`.
- **`Map`:** keys of **any** type are preserved without coercion.

##### Example 1 — numeric keys collide with string keys

```javascript
const o = {};
const strKey = '123';
const numKey = 123;
o[strKey] = 'string-valued';
o[numKey] = 'number-valued';
console.log(o[strKey]); // 'number-valued'  (both wrote to the same string key)
```

##### Example 2 — Symbol uniqueness

```javascript
const o = {};
const s1 = Symbol('id');
const s2 = Symbol('id');
o[s1] = 'one';
o[s2] = 'two';
console.log(o[s1]); // 'one'  (symbols with the same description are still different)
```

##### Example 3 — two objects as keys collide

```javascript
const o = {};
const k1 = { key: '123' };
const k2 = { key: '456' };
o[k1] = 'one';
o[k2] = 'two';
console.log(o[k1]); // 'two'  (both keys coerced to "[object Object]")
```

**Gotcha — reaching for `Map` when object keys matter:** If you need to associate data with objects without this collision (or without coercion at all), use `Map`. See [`3.3 Map & Set in JS`](#11.%20Map%20and%20Set%20in%20JavaScript%20/%20JavaScript%20%E4%B8%AD%E7%9A%84%20Map%20%E4%B8%8E%20Set).

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef) for how primitives and references interact with the stack and heap.
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

Reach for this when you need a quick reference for the `Object.*` and `Array.*` utility methods introduced in ES6. For newer additions (`Object.hasOwn`, `Array.at`, `structuredClone`), see [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7).

#### Object methods

##### `Object.assign(target, ...sources)`

Copies enumerable own properties from one or more source objects into the target. Returns the target. **Shallow** copy; later sources win for duplicate keys.

```javascript
const target = { a: 1, b: 2 };
const source = { b: 3, c: 4 };
Object.assign(target, source);
// target is now { a: 1, b: 3, c: 4 }

// Common idiom: merge without mutating any input
const merged = Object.assign({}, obj1, obj2);
```

**Modern alternative:** object spread — `{ ...obj1, ...obj2 }` — is usually cleaner for this use case.

##### `Object.is(a, b)`

Same as `===`, with two exceptions:

- `Object.is(NaN, NaN)` is `true` (strict equality would be `false`).
- `Object.is(+0, -0)` is `false` (strict equality would be `true`).

```javascript
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

Reach for it when you need to distinguish `+0` from `-0` (rare) or detect `NaN` without `Number.isNaN`.

##### `Object.keys(obj)`

Array of the object's own enumerable string-keyed property names, in insertion order (with integer keys numerically ordered first).

```javascript
Object.keys({ a: 1, b: 2, c: 3 }); // ['a', 'b', 'c']
```

##### `Object.values(obj)`

Array of the own enumerable values.

```javascript
Object.values({ a: 1, b: 2, c: 3 }); // [1, 2, 3]
```

##### `Object.entries(obj)`

Array of `[key, value]` pairs. Enables iteration with `for...of` destructuring.

```javascript
Object.entries({ a: 1, b: 2, c: 3 });
// [['a', 1], ['b', 2], ['c', 3]]

for (const [key, value] of Object.entries(obj)) {
  console.log(key, value);
}
```

These three methods are the go-to for iterating a plain object — preferred over `for..in`, which walks the prototype chain.

#### Array methods

##### `Array.from(arrayLike, mapFn?)`

Creates a new, shallow-copied array from an array-like or iterable object. Optional mapping function transforms each element during creation.

```javascript
// From an array-like
const arrayLike = { 0: 'a', 1: 'b', length: 2 };
Array.from(arrayLike); // ['a', 'b']

// From a Set (dedupe idiom)
Array.from(new Set([1, 2, 2, 3])); // [1, 2, 3]

// With a map function
Array.from({ length: 3 }, (_, i) => i * 2); // [0, 2, 4]
```

##### `Array.of(...elements)`

Creates an array from its arguments — bypasses the `Array(n)` constructor's "single number means length" quirk.

```javascript
Array.of(1, 2, 3); // [1, 2, 3]

Array(3);      // creates [ <3 empty slots> ] — length 3, no values
Array.of(3);   // creates [3] — one element, value 3
```

**Reach for it when:** constructing an array from a known set of elements and at least one could be a number — `Array.of()` disambiguates the intent.

**See also:** [`3.5 Array in JS`](#13.%20JavaScript%20Arrays%20/%20JavaScript%20%E6%95%B0%E7%BB%84) for array iteration and transformation methods, [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7) for post-ES6 additions.
## 15. Other JavaScript Topics / JavaScript其他内容

A grab-bag of short interview-favorite JavaScript topics. Reach for this when someone asks about strict mode, floating-point math, equality operators, or the `!!` idiom.

#### What does `'use strict';` do?

Strict mode enforces stricter parsing and error handling. Activate it by adding `'use strict';` at the top of a script or function. It has different semantics from regular code, aimed at improving reliability and performance. Modern modules (ES modules and classes) run in strict mode automatically.

##### Features of strict mode

1. **Mandatory variable declarations.** Assigning to an undeclared variable throws `ReferenceError`, preventing accidental global creation from typos.
2. **Disallows `with` statements.** `with` creates unpredictable scope, hurts performance, and complicates debugging.
3. **Scoped `eval()`.** Declarations inside `eval` no longer leak into the surrounding scope, making `eval` marginally safer.
4. **Secure `this` binding.** A plain function call (not as a method) has `this === undefined`, instead of `this === window`. Prevents accidental global mutation.
5. **No duplicate parameter names.** `function f(a, a) {}` throws. Eliminates a class of typos.
6. **Immutable non-writable properties.** Writing to a non-writable property throws `TypeError` instead of silently failing.
7. **Restrictions on deleting.** `delete` on non-deletable properties throws, protecting language core.
8. **No octal literals.** `010` is a syntax error. Use `0o10` for octal explicitly; use `'\u0061'` instead of `'\141'` for escape sequences.

**Reach for it when:** working in non-module scripts or legacy code where strict mode isn't implicit. In ES modules, classes, and any modern tooling, strict mode is the default.

#### Why doesn't `0.1 + 0.2 === 0.3`?

**Headline:** IEEE 754 floating-point can't represent `0.1` or `0.2` exactly in binary. The tiny representation errors accumulate, so `0.1 + 0.2` lands at `0.30000000000000004`.

To compare floating-point numbers safely, check whether they're within a small tolerance:

```javascript
const tolerance = 0.0001;
const sum = 0.1 + 0.2;
const target = 0.3;

if (Math.abs(sum - target) < tolerance) {
  console.log('Equal');
} else {
  console.log('Not Equal');
}
```

For currency calculations, avoid floating-point entirely — work in integer cents (or use a decimal library).

#### What's the difference between `==` and `===`?

- `==` (loose equality) performs **type coercion** before comparing. Values are converted to a common type.
- `===` (strict equality) compares **value and type** without conversion.

```javascript
5 == '5';          // true  — string '5' coerced to number
null == undefined; // true  — special rule
0 == false;        // true  — false coerced to 0
'' == false;       // true  — both coerced to 0

5 === '5';          // false
null === undefined; // false
0 === false;        // false
```

**Rule of thumb:** always use `===`, with one common exception — `value == null` is a concise way to check for both `null` and `undefined` in one expression.

**Gotcha — "`==` with `NaN`":** `NaN == anything` is always `false`, including `NaN == NaN`. Use `Number.isNaN(x)` to detect it.

#### What does `!!` do?

Converts any value to its boolean equivalent. The first `!` coerces to boolean and negates; the second `!` negates back.

```javascript
!!'hello';    // true
!!0;          // false
!!null;       // false
!!undefined;  // false
!!NaN;        // false
!!'';         // false
!!{};         // true
!![];         // true
```

##### Why this matters in React

React renders the literal value `0` in the DOM but ignores `false`. So short-circuiting with `&&` can leak an unwanted `0`:

```jsx
{list.length && <ItemList items={list} />}
// when list is empty: renders `0` in the DOM
```

The fix is to coerce to boolean first:

```jsx
{!!list.length && <ItemList items={list} />}
// when list is empty: renders nothing
```

**Gotcha — `!!` vs. `Boolean()`:** Functionally identical — pick whichever your team's lint rules prefer. `!!` is slightly faster in micro-benchmarks, but the difference is irrelevant in practice.
## 16. Modern JavaScript Features / 现代JavaScript特性

Reach for this when you need a quick reference for optional chaining, nullish coalescing, destructuring, promise combinators, and other post-ES6 language additions that come up constantly in interviews. For pre-ES2020 additions (`Object.keys`, `Array.from`, etc.), see [`3.6 ES6 New Methods`](#14.%20ES6%20New%20Methods%20/%20ES6%E6%96%B0%E5%A2%9E%E6%96%B9%E6%B3%95).

#### 1. Optional chaining (`?.`)

Short-circuits when the left-hand side is `null` or `undefined`, returning `undefined` instead of throwing.

##### Syntax

```javascript
obj?.prop
obj?.[expr]
func?.(args)
```

##### Use cases

**Objects:**

```javascript
const user = { address: { city: 'NYC' } };
user?.address?.city;    // 'NYC'
user?.profile?.avatar;  // undefined (no error)
```

**Methods:**

```javascript
const obj = { greet: () => 'hi' };
obj.greet?.();  // 'hi'
obj.missing?.(); // undefined
```

**Arrays:**

```javascript
const arr = [1, 2, 3];
arr?.[0];   // 1
arr?.[10];  // undefined
```

**Nested optional access:**

```javascript
const data = { items: [{ name: 'a' }] };
data?.items?.[0]?.name; // 'a'
```

**Gotcha — `?.` only short-circuits on `null` and `undefined`:** Any other falsy value (like `0` or `''`) does *not* trigger short-circuit, which is the point — `?.` checks structural existence, not truthiness.

---

#### 2. Nullish coalescing (`??`)

Returns the right-hand side only when the left-hand side is `null` or `undefined`. Unlike `||`, does **not** treat `0`, `''`, or `false` as falsy.

| Left value | `a \|\| b` | `a ?? b` |
|---|---|---|
| `null` | `b` | `b` |
| `undefined` | `b` | `b` |
| `0` | `b` | `0` |
| `''` | `b` | `''` |
| `false` | `b` | `false` |
| `NaN` | `b` | `NaN` |

**When to use each:**

- `??` — defaulting where `0`, `''`, or `false` are valid values.
- `||` — defaulting where any falsy value should trigger the fallback.

```javascript
const count = 0;
count || 10;   // 10
count ?? 10;   // 0

const name = '';
name || 'Anonymous';   // 'Anonymous'
name ?? 'Anonymous';   // ''
```

---

#### 3. Destructuring

##### Object destructuring

```javascript
const { a, b } = obj;
const { a: alias, b = 10 } = obj;   // rename + default
const { a, ...rest } = obj;         // rest pattern
```

##### Array destructuring

```javascript
const [first, second] = arr;
const [a, , c] = arr;        // skip element
const [x, ...tail] = arr;    // rest
const [a = 0, b = 0] = arr;  // defaults
```

##### Nested destructuring

```javascript
const { user: { name, address: { city } } } = data;
const [[a, b], [c, d]] = nested;
```

##### Renaming

```javascript
const { name: userName, id: userId } = user;
```

##### Rest pattern

```javascript
const { a, b, ...others } = obj;   // others = remaining props
const [head, ...rest] = arr;       // rest = remaining elements
```

---

#### 4. Template literals

##### Basic interpolation

```javascript
const name = 'World';
`Hello, ${name}!`;
`2 + 2 = ${2 + 2}`;
```

##### Tagged templates

The tag function receives an array of string segments and the interpolated values. Useful for sanitization, i18n, or DSLs.

```javascript
function tag(strings, ...values) {
  return strings.reduce((acc, str, i) => acc + str + (values[i] ?? ''), '');
}
tag`Hello ${'World'}!`;  // 'Hello World!'
```

**Signature:** `tag(strings: TemplateStringsArray, ...values: any[])`

---

#### 5. Promise combinators

| Method | Resolves when | Rejects when | Return type |
|---|---|---|---|
| `Promise.all` | All fulfill | Any rejects | `[results]` or first rejection |
| `Promise.allSettled` | All settle (fulfill or reject) | Never | `[{status, value?}, {status, reason?}]` |
| `Promise.any` | Any fulfills | All reject | First fulfilled value or `AggregateError` |
| `Promise.race` | First settles (either way) | First rejects | First result or first rejection |

##### Behavior on rejection

```javascript
// Promise.all — short-circuits on first rejection
Promise.all([p1, p2, p3]).catch(e => e);  // rejects with p1's error if p1 rejects

// Promise.allSettled — never rejects
Promise.allSettled([p1, p2, p3]).then(results => {
  // results: [{status:'fulfilled', value}, {status:'rejected', reason}, ...]
});

// Promise.any — rejects only if all reject (AggregateError)
Promise.any([p1, p2, p3]).then(v => v);   // first fulfilled value

// Promise.race — first to settle wins (fulfill or reject)
Promise.race([p1, p2, p3]);               // first result or first error
```

**Reach for them when:**

- Parallel work, everything must succeed → `Promise.all`.
- Parallel work, collect all outcomes → `Promise.allSettled`.
- Parallel work, first success wins → `Promise.any`.
- Parallel work with a timeout → `Promise.race` (racing against a timeout promise).

**See also:** [`4.3 Asynchronous JavaScript`](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for Promise fundamentals and error handling.

---

#### 6. Newer APIs

##### `globalThis`

Cross-environment reference to the global object (`window` in browsers, `global` in Node, `self` in workers).

```javascript
globalThis.setTimeout === window.setTimeout; // true in a browser
```

##### `Array.at(index)`

Index access with support for negative indices counting from the end.

```javascript
const arr = [1, 2, 3];
arr.at(0);   // 1
arr.at(-1);  // 3
arr.at(-2);  // 2
```

Cleaner than `arr[arr.length - 1]` for "last element".

##### `Object.hasOwn(obj, prop)`

Replacement for `obj.hasOwnProperty(prop)` that avoids prototype-lookup edge cases (e.g., when `obj` overrides `hasOwnProperty` or has `null` prototype).

```javascript
const o = { a: 1 };
Object.hasOwn(o, 'a');        // true
Object.hasOwn(o, 'toString'); // false
```

##### `structuredClone(value)`

Deep clone of serializable values. Handles objects, arrays, `Map`, `Set`, `Date`, typed arrays, and circular references — but **not** functions, symbols, DOM nodes, or class instances.

```javascript
const original = { a: 1, nested: { b: 2 } };
const copy = structuredClone(original);
copy.nested.b = 3;
original.nested.b; // still 2
```

Reach for it instead of `JSON.parse(JSON.stringify(x))` — it's faster, handles cycles, and preserves `Date` / `Map` / `Set`.

---

#### 7. Modules

##### CommonJS vs ES Modules

| Aspect | CommonJS | ES Modules |
|---|---|---|
| Syntax | `require()`, `module.exports` | `import`, `export` |
| Loading | synchronous | asynchronous (static analysis) |
| Top-level `await` | no | yes |
| Tree-shaking | limited | supported |
| `this` at top level | `exports` | `undefined` |

##### CommonJS

```javascript
const { foo } = require('./module');
module.exports = { bar };
```

##### ES Modules

```javascript
import { foo } from './module.js';
import * as ns from './module.js';
export { bar };
export default baz;
```

##### Dynamic `import()`

Returns a Promise; use for code-splitting or conditional loading.

```javascript
const load = async () => {
  const { default: Component } = await import('./Component.js');
  return Component;
};
```

**Key differences:** `import` is static (parsed at compile time, enables tree-shaking); `import()` is dynamic and returns a Promise (enables lazy loading).

**See also:** [`7.3 Build Tools`](#27.%20Build%20Tools%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7) for module bundling strategies, [`4.3 Asynchronous JavaScript`](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for Promises and async/await fundamentals.
## 17. Object, Function, and Prototype / 对象、函数与原型

A bundle of classic interview questions about JavaScript's prototype system, `this`, `new`, and property descriptors.

### What is the JavaScript prototype chain?

**Headline (30s):** Every object has an internal `[[Prototype]]` link (exposed as `__proto__`) pointing to another object. When you access a property that doesn't exist on the object, the engine walks up this chain until it finds the property or reaches `null`. This is how objects inherit behavior in JavaScript — not by copying, but by linking.

**Why interviewers ask this:** Prototypes explain inheritance, `class`, `instanceof`, and why polyfills work the way they do. A candidate who can't describe the chain struggles with React class components, library internals, and debugging "where did this method come from?" questions.

#### `prototype` vs. `__proto__`

Two closely related properties that trip up almost everyone:

- **`prototype`** — a property that exists *only on functions*. It's the object that will become `__proto__` of any instance created with `new`.
- **`__proto__`** — a property on *every* object. It points to the object's prototype. Reading it walks up the chain.

#### How the chain is formed

1. A constructor function has a `.prototype` object.
2. Calling the constructor with `new` creates a new object whose `__proto__` is set to the constructor's `.prototype`.
3. That prototype object has its own `__proto__` pointing to `Object.prototype`.
4. `Object.prototype.__proto__` is `null` — end of chain.

```javascript
function Person(name) {
  this.name = name;
}

Person.prototype.sayHello = function() {
  console.log(`Hello, my name is ${this.name}`);
};

const alice = new Person('Alice');
alice.sayHello(); // 'Hello, my name is Alice'

alice.__proto__ === Person.prototype;                  // true
Person.prototype.__proto__ === Object.prototype;       // true
Object.prototype.__proto__;                            // null
```

When `alice.sayHello()` is called, the engine searches `alice` → `Person.prototype` (found!) and invokes it.

**Gotcha — `class` is syntactic sugar:** `class Foo {}` is essentially `function Foo() {}` with a prototype, so `typeof Foo === 'function'`. Understanding the chain helps debug transpiled output.

---

### What's the difference between `{}` and `Object.create(proto)`?

**Headline (30s):** `{}` creates an object whose prototype is `Object.prototype`. `Object.create(proto)` lets you choose any prototype (including `null`). Use `Object.create` when you need custom inheritance or a "clean" dictionary with no inherited keys.

```javascript
const obj1 = {};
obj1.__proto__ === Object.prototype; // true

const obj2 = Object.create({ greet: 'hi' });
obj2.greet;                          // 'hi' (inherited)
obj2.__proto__ === Object.prototype; // false

const bag = Object.create(null);     // no prototype at all
bag.toString;                        // undefined — no inherited methods
```

**Reach for `Object.create(null)` when:** building a hash map where keys might collide with inherited names like `toString` or `hasOwnProperty`. The modern alternative is `Map`.

---

### What is `this` in JavaScript?

**Headline (30s):** `this` is a special binding that is decided **at call time**, not at definition time. Its value depends on *how* a function is called: as a plain function (`fn()`), as a method (`obj.fn()`), as a constructor (`new Fn()`), or explicitly (`fn.call(ctx)`). Arrow functions are the exception — they capture `this` lexically.

**Why interviewers ask this:** It's the #1 source of bugs in hand-rolled code. Understanding `this` is prerequisite to understanding `bind`, `call`, `apply`, class methods, React class components, and event handlers.

#### The rules (in precedence order)

1. **`new` binding** — `new Fn()` creates a new object, `this` is that object.
2. **Explicit binding** — `fn.call(ctx)`, `fn.apply(ctx)`, `fn.bind(ctx)` — `this` is `ctx`.
3. **Implicit binding** — `obj.fn()` — `this` is `obj`.
4. **Default binding** — `fn()` — `this` is the global object (`window`) in non-strict mode, or `undefined` in strict mode.
5. **Arrow functions** — ignore all rules above; `this` is inherited lexically from the enclosing scope.

#### Examples covering each case

```javascript
// 1. Default
function f() { return this; }
f();                          // window (sloppy) / undefined (strict)

// 2. Implicit (method call)
const obj = { f, name: 'obj' };
obj.f();                      // obj

// 3. Explicit
f.call({ name: 'ctx' });      // { name: 'ctx' }

// 4. new
function Person(n) { this.name = n; }
new Person('Alice');          // { name: 'Alice' }

// 5. Arrow — captures lexically
const wrapper = {
  name: 'outer',
  run() {
    const arrow = () => this.name;
    return arrow();           // 'outer' — `this` is `wrapper`
  }
};
```

**Gotcha — losing `this`:** Passing a method as a callback drops the binding:

```javascript
const api = {
  url: '/data',
  fetch() { return this.url; }
};
const f = api.fetch;
f();                          // undefined in strict mode — `this` is no longer `api`

// Fix options:
api.fetch.bind(api);          // pre-bind
() => api.fetch();            // wrap in arrow
```

---

### Implement `bind` (and `call` / `apply`)

**Headline (30s):** `bind` returns a new function with a fixed `this` and optionally pre-filled arguments. `call` / `apply` invoke immediately with a given `this` — `call` takes args individually, `apply` takes an array. The classic implementation trick: `call` and `apply` temporarily attach the function as a method on the context object, invoke it, then delete it.

#### `bind`

```javascript
Function.prototype.myBind = function (context, ...preBoundArgs) {
  const originalFn = this;
  return function (...newArgs) {
    return originalFn.apply(context, preBoundArgs.concat(newArgs));
  };
};

function greet(greeting, name) {
  return `${greeting}, ${name}! I'm ${this.role}`;
}

const boundGreet = greet.myBind({ role: 'admin' }, 'Hello');
boundGreet('Alice'); // 'Hello, Alice! I'm admin'
```

#### `call` and `apply`

The trick: assign the function to a unique key on the context, call it as a method (so `this` binds to the context), then delete the key.

```javascript
Function.prototype.myCall = function (context = globalThis, ...args) {
  const key = Symbol();
  context[key] = this;
  const result = context[key](...args);
  delete context[key];
  return result;
};

Function.prototype.myApply = function (context = globalThis, args = []) {
  const key = Symbol();
  context[key] = this;
  const result = context[key](...args);
  delete context[key];
  return result;
};
```

**Gotcha — `bind` + arrow functions:** Arrow functions don't have their own `this`, so `bind` can't change `this` for an arrow function (only the pre-bound arguments take effect).

**Gotcha — `bind` + `new`:** If a bound function is used as a constructor with `new`, the `new` binding wins — the pre-bound `this` is ignored, but pre-bound arguments are still applied.

---

### How does `new` work, and how would you implement it?

**Headline (30s):** `new Fn(...args)` does four things: (1) creates a new object whose prototype is `Fn.prototype`; (2) calls `Fn` with `this` set to the new object; (3) if `Fn` explicitly returns an object, that's the result; otherwise the new object is returned.

```javascript
function _new(fn, ...args) {
  const obj = Object.create(fn.prototype);        // 1. new object linked to prototype
  const result = fn.apply(obj, args);             // 2. run constructor
  return result instanceof Object ? result : obj; // 3. explicit object return wins
}

function Person(name) {
  this.name = name;
}
const p = _new(Person, 'Tom');
p.name;                          // 'Tom'
p instanceof Person;             // true
```

**Gotcha — returning a primitive:** Returning a string/number/boolean from a constructor is ignored. Returning an object overrides the default `this` return.

---

### What are hidden classes?

**Headline (30s):** V8 (and similar engines) assign each JS object a "hidden class" that records its shape — which properties it has and in what order. Objects with the same shape share the same hidden class, which makes property access fast. Creating objects with consistent property order helps the engine optimize; adding/removing properties dynamically creates new hidden classes and costs performance.

```javascript
function createPoint(x, y) {
  return { x, y };               // every call produces same shape → same hidden class
}

// Good: consistent shape
const p1 = createPoint(1, 2);
const p2 = createPoint(3, 4);

// Bad: different construction order creates different hidden classes
const a = {};
a.x = 1;
a.y = 2;

const b = {};
b.y = 2;
b.x = 1;                         // different hidden class than `a`!
```

**Reach for this knowledge when:** writing hot-path code that allocates many similar objects (game engines, data pipelines). For typical app code, hidden classes are an implementation detail you don't need to worry about.

---

### Why define methods on the prototype instead of in the constructor?

**Headline (30s):** Methods defined inside the constructor are copied into **every** instance, wasting memory. Methods on the prototype are **shared** — all instances look them up through the prototype chain. Prototype methods also support proper inheritance and can be monkey-patched to update all existing instances at once.

```javascript
// Bad: a new `greet` function is created for every instance
function Person(name) {
  this.name = name;
  this.greet = function() { console.log(`Hi, ${this.name}`); };
}

// Good: one shared function on the prototype
function Person(name) {
  this.name = name;
}
Person.prototype.greet = function() { console.log(`Hi, ${this.name}`); };
```

In modern code, write `class` — it does this for you. `class Foo { method() {} }` puts `method` on `Foo.prototype` automatically; fields declared outside the constructor also go on the prototype.

---

### How do static, instance, and prototype properties interact?

This appears as an execution-order puzzle. Walk through it step by step.

```javascript
function Foo() {
  Foo.a = function() { console.log(1); };
  this.a = function() { console.log(2); };
}
Foo.prototype.a = function() { console.log(3); };
Foo.a = function() { console.log(4); };

Foo.a();           // 4
const obj = new Foo();
obj.a();           // 2
Foo.a();           // 1
```

**Breakdown:**

1. After definition, `Foo.a` is the "logs 4" function, so `Foo.a()` prints `4`.
2. `new Foo()` runs the body: it **reassigns** `Foo.a` to "logs 1" and creates an instance property `obj.a` = "logs 2".
3. `obj.a()` — instance property takes precedence over prototype, so it prints `2`.
4. `Foo.a()` — now prints `1`, because the constructor overwrote the static property.

**Precedence lookup order for `obj.a`:**

1. Own (instance) properties.
2. Prototype chain (`Foo.prototype`, `Object.prototype`, ...).

Static properties (`Foo.a`) are entirely separate — they live on the constructor function itself, not on the instance chain.

---

### What are property descriptors?

**Headline (30s):** Every property on an object has a set of *attributes* (configurable, enumerable, writable, value/get/set) that control its behavior. `Object.defineProperty` lets you set them explicitly. This is how libraries implement read-only properties, computed getters, and non-enumerable "internal" fields.

#### Data properties

| Attribute | Meaning |
|---|---|
| `value` | The property's actual value |
| `writable` | Whether the value can be reassigned |
| `enumerable` | Whether the property shows up in `for...in` / `Object.keys` |
| `configurable` | Whether the property can be deleted or redefined |

```javascript
const obj = {};
Object.defineProperty(obj, 'name', {
  value: 'John',
  writable: false,
  enumerable: true,
  configurable: true
});
obj.name = 'Jane';   // silently fails (or throws in strict mode)
obj.name;            // 'John'
```

#### Accessor properties (`get` / `set`)

```javascript
const obj = { _name: 'John' };
Object.defineProperty(obj, 'name', {
  get() { return this._name; },
  set(v) { this._name = v; },
  enumerable: true,
  configurable: true
});
obj.name;         // 'John' (calls get)
obj.name = 'Jo';  // calls set
```

#### Inspecting descriptors

```javascript
Object.getOwnPropertyDescriptor(obj, 'name');
// { value: 'John', writable: false, enumerable: true, configurable: true }
```

**Reach for this when:** implementing reactive frameworks (Vue 2 used `defineProperty` pre-Proxy), enforcing API contracts (read-only IDs), or making fields non-enumerable so they don't leak in logs.

**See also:** [`Scope & Closure / 作用域与闭包`](#18.%20Scope%20&%20Closure%20/%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85) for how `this` interacts with scope, [`3.2 JavaScript Types`](#10.%20JavaScript%20Types%20/%20JavaScript%E7%B1%BB%E5%9E%8B) for primitive vs. reference fundamentals.
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

#### Why did JavaScript evolve from callbacks to Promises to `async/await`?

**Headline (30s):** JavaScript is single-threaded — it can't block while waiting for I/O, so every async API has to defer completion. The three generations of async APIs (callbacks → Promises → `async/await`) are all attempts to solve the same problem: *how to express "do this, then that, then that" without creating unreadable spaghetti*. Each generation is strictly more expressive than the last; `async/await` is today's answer.

**Why interviewers ask this:** Async handling is the #1 source of production bugs in frontend code. Interviewers want to see that you can reason about control flow, error propagation, and concurrency — not just memorize `.then()`.

---

#### Callbacks — the original async pattern

A callback is a function you pass to another function to be invoked when an async operation finishes.

```javascript
function fetchData(url, callback) {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', url);
  xhr.onload = () => callback(null, xhr.responseText);
  xhr.onerror = () => callback(new Error('Request failed'));
  xhr.send();
}
```

##### Why callbacks hurt: callback hell

When async operations depend on each other, callbacks nest:

```javascript
getUser(userId, (user) => {
  getOrders(user.id, (orders) => {
    getOrderDetails(orders[0].id, (details) => {
      // indent continues forever...
    });
  });
});
```

Three real problems: (1) hard to read, (2) error handling must be repeated at every level, (3) no way to compose (e.g., "run these in parallel, wait for all"). Promises were introduced to fix all three.

---

#### Promises — the composable abstraction

**Headline:** A Promise is an object representing a future value — it's in one of three states (`pending`, `fulfilled`, `rejected`), and once settled it never changes. Chaining via `.then()` flattens nested callbacks and gives you a single error channel via `.catch()`.

##### States

- **Pending** — initial; the operation is still running.
- **Fulfilled** — completed successfully, with a value.
- **Rejected** — failed, with a reason (usually an Error).

Once fulfilled or rejected, the state is locked. A rejected promise cannot later resolve; a fulfilled one cannot later fail.

##### Creating and consuming a Promise

```javascript
const promise = new Promise((resolve, reject) => {
  setTimeout(() => resolve('Success!'), 1000);
});

promise.then(value => console.log(value)); // 'Success!' after 1s
```

##### Prototype methods

- **`.then(onFulfilled, onRejected)`** — register handlers. Returns a new promise, so chains compose.
- **`.catch(onRejected)`** — shorthand for `.then(undefined, onRejected)`.
- **`.finally(onSettled)`** — runs no matter what; useful for cleanup (hide loading spinner, release resources).

```javascript
fetchData('/api/users')
  .then(text => JSON.parse(text))
  .then(users => console.log(users))
  .catch(err => console.error(err))
  .finally(() => console.log('Done'));
```

##### Static methods (combinators)

Summary: see [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7) for the comparison table. Short version:

- **`Promise.all`** — parallel, fails fast.
- **`Promise.allSettled`** — parallel, never fails; returns every outcome.
- **`Promise.any`** — first success wins.
- **`Promise.race`** — first settlement wins (success or failure).

```javascript
const [users, posts, comments] = await Promise.all([
  fetch('/api/users').then(r => r.json()),
  fetch('/api/posts').then(r => r.json()),
  fetch('/api/comments').then(r => r.json())
]);
```

---

#### `async` / `await` — syntactic sugar that looks synchronous

**Headline:** An `async` function automatically returns a Promise. `await` pauses the function body until the Promise settles, then resumes with the value (or throws if rejected). This lets you write sequential async code using `try/catch` — no callback nesting, no `.then()` chains.

```javascript
async function loadUser(userId) {
  try {
    const user = await getUser(userId);
    const orders = await getOrders(user.id);
    const details = await getOrderDetails(orders[0].id);
    return details;
  } catch (err) {
    console.error('Failed:', err);
  }
}
```

Compare with the callback hell example above — same logic, no nesting, errors flow to a single `catch`.

##### Sequential vs. parallel with `await` — the trap

`await` pauses the function. If you chain `await`s for independent operations, you serialize them by accident:

```javascript
// Bad: sequential when they could be parallel
const users = await fetch('/api/users');
const posts = await fetch('/api/posts');
// Total time = users + posts

// Good: kick both off, then await
const [users, posts] = await Promise.all([
  fetch('/api/users'),
  fetch('/api/posts')
]);
// Total time = max(users, posts)
```

**Rule of thumb:** If two `await`s don't depend on each other's results, you probably want `Promise.all`.

##### `for await...of`

Iterates over an async iterable, awaiting each value. Order of processing is guaranteed, but promises can be created eagerly and awaited lazily:

```javascript
async function processAll() {
  const p1 = fetch('/api/1');
  const p2 = fetch('/api/2');
  const p3 = fetch('/api/3');

  for await (const response of [p1, p2, p3]) {
    const data = await response.json();
    console.log(data);
  }
}
```

The three fetches start concurrently (they're created before the loop). `for await` only controls when each *result* is processed, not when each promise starts.

---

#### Microtasks: why this logs `0 2 1 3`

**Headline:** Every `.then()` callback is scheduled as a *microtask*. The event loop drains the entire microtask queue between tasks (and between rendering frames). When two promise chains exist in parallel, their `.then()` callbacks interleave round-robin.

```javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0 2 1 3
```

Walk-through: both chains' first `.then()` are queued right away. After `0` runs, its second `.then()` gets queued — but chain 2's first `.then()` is already ahead of it.

##### Returning a Promise from `.then()` adds ticks

When a `.then()` callback returns another Promise, the chain waits an extra microtask tick for it to unwrap:

```javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then(res => console.log(res));

Promise.resolve().then(() => console.log(1))
                 .then(() => console.log(2))
                 .then(() => console.log(3));
// 0 1 2 3 4
```

The extra hop lets chains without inner Promises "catch up" two ticks.

**See also:** [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF) for the full microtask / macrotask model.

---

#### Function patterns: currying

Currying transforms `fn(a, b, c)` into `fn(a)(b)(c)`. Useful for partial application, reusable specialized functions, and functional composition.

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function (...next) {
      return curried.apply(this, args.concat(next));
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);
curriedSum(1)(2)(3);    // 6
curriedSum(1, 2)(3);    // 6
curriedSum(1)(2, 3);    // 6
```

Uses: configuration helpers (`http.get(headers)(url)`), event handler factories, and building composition pipelines (Ramda, lodash/fp).

---

#### Interview-favorite: implement `LazyMan` (chainable async task queue)

**Headline:** Build a chainable API where `eat` / `sleep` queue actions and run in order. The trick: queue a task list inside the constructor, defer execution with `setTimeout(0)` so the entire chain is built first, and give each task responsibility for calling `next()` when it's done.

```javascript
class LazyMan {
  constructor(name) {
    this.name = name;
    this.taskList = [];
    setTimeout(() => this.next(), 0);
  }

  eat(food) {
    this.taskList.push(() => {
      console.log(`eat ${food}`);
      this.next();
    });
    return this;
  }

  sleep(time) {
    this.taskList.push(() => {
      setTimeout(() => {
        console.log(`wake up after ${time}ms`);
        this.next();
      }, time);
    });
    return this;
  }

  next() {
    const task = this.taskList.shift();
    task && task();
  }
}

new LazyMan('ronron').eat('apple').sleep(1000).eat('banana');
// eat apple → wake up after 1000ms → eat banana
```

Key ideas:

- **Chainable API** — each method returns `this`.
- **Deferred start** — `setTimeout(0)` in the constructor makes sure `.eat().sleep().eat()` finish pushing before `next()` runs.
- **Sequential async flow** — each task calls `next()` only when it's truly done; async tasks (like `sleep`) call it inside their own `setTimeout`.

---

#### Arrow functions: four things they can't do

Arrow functions are concise and lexically bind `this`, but they have real limits:

1. **No own `this`** — they inherit from the enclosing scope. Unsuitable as object methods when you want `this` to be the object.

    ```javascript
    const obj = {
      name: 'Alice',
      greet: () => console.log(this.name) // `this` is NOT obj
    };
    ```

2. **No `arguments` object** — use rest parameters instead: `(...args) => ...`.

3. **Cannot be used with `new`** — throws `TypeError`.

4. **Not suitable as prototype methods** — same problem as (1); `this` won't be the instance.

---

#### Classic gotcha: `['1', '2', '3'].map(parseInt)`

**Headline:** Result is `[1, NaN, NaN]`, not `[1, 2, 3]`. Reason: `map` passes three arguments `(value, index, array)` to the callback, and `parseInt` accepts `(string, radix)` — so it becomes `parseInt('2', 1)` (radix 1 is invalid) and `parseInt('3', 2)` (`'3'` isn't a binary digit).

```javascript
['1', '2', '3'].map(parseInt);
// parseInt('1', 0) → 1     (radix 0 defaults to base 10)
// parseInt('2', 1) → NaN   (radix 1 is invalid)
// parseInt('3', 2) → NaN   ('3' is not a binary digit)
// [1, NaN, NaN]

// Fix:
['1', '2', '3'].map(s => parseInt(s, 10)); // [1, 2, 3]
['1', '2', '3'].map(Number);               // [1, 2, 3]
```

**Gotcha — why this matters:** Any time you pass a unary-argument function to `.map`/`.forEach`/`.filter` and the function actually accepts a second argument, you can hit this. Always wrap with an arrow if the callback shape doesn't match.

**See also:** [`4.5 Error Handling`](#21.%20Error%20Handling%20/%20%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86) for error handling patterns with Promises and async/await, [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7) for Promise combinator comparison, [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF) for the microtask scheduling model.
## 20. Iterators and Generators / 迭代器与生成器

#### What's the iteration protocol, and why does it matter?

**Headline (30s):** JavaScript defines two protocols — **iterable** and **iterator** — that any object can implement to participate in `for...of`, spread (`...`), destructuring, and `Array.from`. A generator is a function that implements both protocols automatically via `yield`. Understanding the protocol is the key to building custom data structures that "just work" with the language's iteration features.

**Why interviewers ask this:** It's the mechanism behind `for...of`, spread syntax, async iteration, and tree/graph traversal patterns. A candidate who can implement a custom iterable shows they understand the language at the protocol level, not just as a collection of built-ins.

---

#### Iterable and iterator protocols

##### Iterable

An object is iterable if it has a `[Symbol.iterator]` method that returns an iterator. Built-in iterables: **Array, String, Map, Set, TypedArray, `arguments`, NodeList**. Plain objects are *not* iterable by default.

##### Iterator

An iterator is any object with a `next()` method that returns `{ value, done }`:

- `value` — the next item.
- `done` — `true` when the sequence is exhausted; `false` otherwise.

```javascript
const arr = [10, 20, 30];
const it = arr[Symbol.iterator]();

it.next(); // { value: 10, done: false }
it.next(); // { value: 20, done: false }
it.next(); // { value: 30, done: false }
it.next(); // { value: undefined, done: true }
```

##### Building a custom iterable

```javascript
class Range {
  constructor(start, end) {
    this.start = start;
    this.end = end;
  }

  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) {
          return { value: current++, done: false };
        }
        return { value: undefined, done: true };
      }
    };
  }
}

for (const n of new Range(1, 5)) console.log(n); // 1 2 3 4 5
[...new Range(3, 6)];                             // [3, 4, 5, 6]
```

Once an object implements `[Symbol.iterator]`, *all* iteration features work — `for...of`, spread, destructuring, `Array.from`, `Map` / `Set` construction. That's the payoff.

**Gotcha — iterators are "one-shot" by default:** Once `done: true`, most iterators can't be restarted. Always re-call `[Symbol.iterator]()` for a fresh iterator. Built-in arrays follow this pattern: `const it = arr[Symbol.iterator](); it.next(); // later: can't restart it`.

---

#### Generators — iterators with cleaner syntax

**Headline (30s):** A generator function (`function*`) returns a generator object — an iterator that's also iterable. Inside the function, `yield` pauses execution and emits a value; the next call to `.next()` resumes from the paused point. The engine automatically manages all the state that a hand-written iterator would have to track manually.

##### Declaration and basic use

```javascript
function* countdown(n) {
  while (n > 0) {
    yield n;
    n--;
  }
}

const gen = countdown(3);
gen.next(); // { value: 3, done: false }
gen.next(); // { value: 2, done: false }
gen.next(); // { value: 1, done: false }
gen.next(); // { value: undefined, done: true }

for (const v of countdown(3)) console.log(v); // 3 2 1
```

##### Passing values *into* a generator

The argument to `.next(value)` becomes the result of the paused `yield` expression:

```javascript
function* conversation() {
  const name = yield 'What is your name?';
  const hobby = yield `Hello, ${name}! What is your hobby?`;
  return `${name} likes ${hobby}`;
}

const chat = conversation();
chat.next().value;         // 'What is your name?'
chat.next('Alice').value;  // 'Hello, Alice! What is your hobby?'
chat.next('coding').value; // 'Alice likes coding'
```

**Mental model:** `yield x` is a two-way door — it emits `x` out, then waits until the next `.next(y)` call sends `y` back in.

##### `yield*` — delegating to another iterable

`yield*` delegates to another iterable or generator, "inlining" all its values:

```javascript
function* flatten(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) {
      yield* flatten(item);   // recursive delegation
    } else {
      yield item;
    }
  }
}

[...flatten([1, [2, [3, 4]], 5])]; // [1, 2, 3, 4, 5]
```

---

#### Practical use cases

##### Lazy evaluation of infinite sequences

Generators produce values on demand — perfect for sequences too large (or infinite) to store:

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

Nothing is computed until you ask. Take as many values as you need and stop — no wasted work.

##### Unique ID factory

```javascript
function* idGenerator(prefix = 'id') {
  let n = 0;
  while (true) {
    yield `${prefix}_${n++}`;
  }
}

const gen = idGenerator('user');
gen.next().value; // 'user_0'
gen.next().value; // 'user_1'
```

Cleaner than keeping a mutable counter in module scope.

##### Historical note: async flow control

Before `async/await`, generators + a promise runner (like the `co` library) gave you synchronous-looking async code:

```javascript
function* fetchUser(id) {
  const response = yield fetch(`/api/users/${id}`);
  const user = yield response.json();
  return user;
}
```

A runner would call `.next()` with each resolved value. Today, `async/await` does exactly this under the hood and is what you should use in production — but the pattern is worth recognizing in legacy code.

---

#### Generators vs. hand-written iterators

| Feature | Custom iterator | Generator |
|---|---|---|
| Syntax | Manual `next()` method | `function*` with `yield` |
| State management | Manual (closure variables) | Automatic (execution paused/resumed) |
| Code complexity | Higher for non-trivial sequences | Simpler and more readable |
| Bidirectional data | Not built-in | `next(value)` passes data in |
| Early termination | Manual `return()` method | Built-in `return()` and `throw()` |

**Reach for generators when:** the sequence has interesting control flow (branching, recursion via `yield*`, infinite streams). Use a hand-written iterator only when you need to precisely control memory layout or can't use generator syntax.

**See also:** [`3.5 Array in JS`](#13.%20JavaScript%20Arrays%20/%20JavaScript%20%E6%95%B0%E7%BB%84) for `for...of` vs `for...in` semantics, [`4.3 Asynchronous JavaScript`](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for `for await...of` and async iteration.
## 21. Error Handling / 错误处理

#### How should you handle errors in modern JavaScript?

**Headline (30s):** There are five layers to cover — synchronous `try/catch/finally`, custom error classes, promise rejection handling (`.catch` / `try/await`), global handlers (`onerror` / `unhandledrejection`), and framework-level boundaries (React error boundaries). A production app needs *all of them*, because each only catches a specific category of error.

**Why interviewers ask this:** Error handling separates candidates who've shipped to production from those who haven't. Interviewers want to see that you know *which* tool to reach for, that you propagate (not swallow) errors, and that you understand the async-vs-sync distinction.

---

#### `try / catch / finally` — synchronous errors

```javascript
try {
  riskyOperation();
} catch (error) {
  console.error(error.message);
} finally {
  cleanup(); // always runs — even if try returns or throws
}
```

- **`finally`** runs regardless — after `return`, after `throw`, after `catch`. Use it for cleanup (close files, reset UI state, clear timers).
- **Rethrowing** — `throw error` (not bare `throw`) preserves the original error object and stack trace.
- **Nested try/catch** — inner `catch` can rethrow to the outer one.

```javascript
try {
  try {
    throw new Error('inner');
  } catch (e) {
    console.log('inner caught');
    throw e; // propagate to outer
  }
} catch (e) {
  console.log('outer caught:', e.message);
}
```

**Gotcha — `try/catch` doesn't catch async errors:** A `throw` inside a `setTimeout` callback, unhandled promise rejection, or unhandled async function escapes `try/catch` entirely. Each async mechanism has its own catching mechanism (see below).

---

#### Custom error classes

**Headline:** Extend `Error`, call `super(message)`, set `this.name`, and optionally attach structured context. Custom error classes let you distinguish error types at the catch site (`if (e instanceof ValidationError)`) and attach domain-specific fields.

```javascript
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

// Throwing
throw new ValidationError('Invalid email', 'email');

// Catching and branching
try {
  validate(input);
} catch (e) {
  if (e instanceof ValidationError) {
    showFieldError(e.field, e.message);
  } else {
    throw e; // don't swallow unexpected errors
  }
}
```

**Why `Object.setPrototypeOf`?** In some transpiled or pre-ES6 environments, extending built-in classes loses the prototype chain — `e instanceof ValidationError` returns `false` unexpectedly. Manually setting the prototype fixes it. In modern environments you can usually omit this, but it's defensive.

**Rule of thumb:** If you're going to branch on error type at the catch site, define a class for it. If you're just surfacing the message, a plain `Error` is fine.

---

#### Promise rejection handling

##### `.catch()` on chains

```javascript
fetch('/api/data')
  .then(res => res.json())
  .catch(err => console.error('Fetch failed:', err))
  .then(data => process(data)); // runs even after catch — with `undefined` if catch ran
```

Two things to know:

1. A `.catch()` returns a *resolved* promise unless it rethrows — subsequent `.then()` calls still run.
2. To stop a chain after a caught error, rethrow or `return Promise.reject(...)` from the `.catch`.

##### `try / catch` around `await`

The cleanest pattern: write linear code, handle errors with regular `try / catch`.

```javascript
async function loadData() {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(err);
    throw err; // reject the returned promise
  }
}
```

**Gotcha — `fetch` doesn't reject on HTTP errors:** A 404 or 500 response is still a *successful* promise. You must check `res.ok` (or `res.status`) manually and throw if needed.

##### Unhandled rejection = silent failure

A promise rejection with no `.catch()` (and no `try/catch` around `await`) becomes an **unhandled rejection**. Browsers log a warning; Node.js may exit the process. In either case, the real bug is usually invisible.

```javascript
// BAD — if fetch fails, the rejection is unhandled
async function bad() {
  const res = await fetch('/api');
  return res.json();
}

// GOOD
async function good() {
  try {
    const res = await fetch('/api');
    return res.json();
  } catch (e) {
    handleError(e);
  }
}
```

**Rule of thumb:** Every `await` in a real app should have a `try/catch` at some level — either the function itself or a caller. Every `.then()` chain should end in a `.catch()`.

---

#### Global error handlers — your last line of defense

##### `window.onerror` — uncaught synchronous errors

```javascript
window.onerror = function (message, source, lineno, colno, error) {
  logToMonitoring({ message, source, lineno, colno, stack: error?.stack });
  return true; // suppress default browser error UI
};
```

- Returns `true` to suppress the default console output.
- **Cross-origin gotcha:** Scripts loaded from another origin (a CDN, typically) yield `"Script error."` with no stack trace due to CORS. Fix: serve the script with a permissive CORS header and add `crossorigin="anonymous"` to the `<script>` tag.

##### `window.addEventListener('unhandledrejection')`

Catches promise rejections that weren't handled by `.catch` or `try/catch`.

```javascript
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled rejection:', event.reason);
  event.preventDefault(); // suppress console warning
});
```

- `event.reason` — the rejection reason (usually an Error).
- `event.promise` — the rejected promise itself.

##### `window.addEventListener('error')` (capture phase) — resource load errors

`onerror` doesn't fire when `<img>`, `<script>`, or `<link>` fail to load. Listen for `error` events in capture phase to catch them.

```javascript
window.addEventListener('error', event => {
  if (event.target !== window) {
    console.error('Resource failed:', event.target.src || event.target.href);
  }
}, true); // `true` = capture phase; required for resource errors
```

**Production setup — three listeners:**

1. `window.onerror` — uncaught JS errors.
2. `unhandledrejection` — async rejections.
3. `error` in capture — resource load failures.

Wire all three to your monitoring backend (Sentry, Datadog, custom). Without all three, you'll miss real production bugs.

---

#### React error boundaries

**Headline:** React catches rendering / lifecycle / constructor errors inside the component tree via *error boundaries*, which are class components implementing `getDerivedStateFromError` and/or `componentDidCatch`. They render a fallback UI instead of letting the whole tree unmount.

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

- **`getDerivedStateFromError`** — sync, returns a state patch for the fallback UI.
- **`componentDidCatch`** — effects (logging, telemetry).

##### What error boundaries do **not** catch

- **Event handler errors** — the handler is called from DOM event dispatch, not React's render pipeline. Wrap in `try/catch`.
- **Async code** (`setTimeout`, `fetch.then`, `await` inside `useEffect`). Wrap in `try/catch`.
- **Server-side rendering errors** — the SSR renderer throws directly.
- **Errors thrown inside the boundary itself** — bubble up to a parent boundary.

##### Function components

There's no hook equivalent. Use the community library `react-error-boundary`:

```jsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary fallback={<div>Error!</div>} onError={logError}>
  <MyComponent />
</ErrorBoundary>
```

**Reach for error boundaries when:** rendering third-party components, dynamic content from user input, or async-loaded modules — anywhere a render error shouldn't take down the whole page.

---

#### Defense in depth — which layer catches what?

| Error source | Caught by |
|---|---|
| Sync throw in function body | `try / catch` in caller |
| `await`ed promise rejection | `try / catch` around `await` |
| `.then()` chain rejection | `.catch()` in chain |
| Uncaught anything | `window.onerror` / `unhandledrejection` |
| Image / script failed to load | `window.addEventListener('error', ..., true)` |
| React render / lifecycle throw | Error boundary |
| React event handler throw | `try / catch` in handler |

A production app uses all of them. Missing any layer lets bugs go silent.

**See also:** [`4.3 Asynchronous JavaScript`](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for Promises and `async/await` fundamentals, [`9.2 React Basics`](#29.%20React%20Basics%20/%20React%E5%9F%BA%E7%A1%80) for the React lifecycle context around error boundaries.
## 22. DOM Manipulation and Events / DOM操作与事件

A bundle of interview questions around DOM events, runtime scheduling, and utility patterns that commonly come up.

### How do you write a proper deep copy?

**Headline (30s):** `JSON.parse(JSON.stringify(obj))` is the one-liner — cheap, often good enough, but silently wrong for anything beyond plain objects and primitives. A robust deep copy needs to dispatch on type (`Date`, `RegExp`, `Map`, `Set`, `Array`, plain object), recurse, and use a `WeakMap` to break circular references. Modern code can reach for `structuredClone` for built-in support.

**Why interviewers ask this:** It tests your grasp of reference semantics, edge cases (cycles, special types), and whether you can design a recursive function with proper memoization.

#### Why `JSON.parse(JSON.stringify(x))` is insufficient

- **Lost types:** `Map`, `Set`, `Date`, `RegExp` become plain objects or strings.
- **Circular references:** `JSON.stringify` throws.
- **Missing values:** `undefined`, functions, and symbols are stripped.

Reach for `structuredClone(value)` (see [`3.8 Modern JavaScript Features`](#16.%20Modern%20JavaScript%20Features%20/%20%E7%8E%B0%E4%BB%A3JavaScript%E7%89%B9%E6%80%A7)) — it handles all of the above natively. Use a handwritten deep copy only when you need to customize behavior (e.g., skip certain keys).

#### Handwritten deep copy

```typescript
function deepCopy(obj: any, map = new WeakMap()): any {
  if (obj === null || typeof obj !== 'object') return obj;
  if (map.has(obj)) return map.get(obj);

  let copy: any;

  if (obj instanceof Date) {
    copy = new Date(obj.getTime());
  } else if (obj instanceof RegExp) {
    copy = new RegExp(obj.source, obj.flags);
  } else if (obj instanceof Map) {
    copy = new Map();
    map.set(obj, copy);
    obj.forEach((value, key) => copy.set(key, deepCopy(value, map)));
  } else if (obj instanceof Set) {
    copy = new Set();
    map.set(obj, copy);
    obj.forEach(value => copy.add(deepCopy(value, map)));
  } else {
    copy = Array.isArray(obj) ? [] : {};
    map.set(obj, copy);
    Object.keys(obj).forEach(key => {
      copy[key] = deepCopy(obj[key], map);
    });
  }

  return copy;
}
```

**Gotcha — `Date` and `RegExp`:** Their state is internal, not enumerable property slots. Iterating keys on them gives you `{}`. You *must* special-case them.

**Gotcha — circular references:** The `WeakMap` stores already-copied objects so that when you hit the same reference twice, you return the existing copy instead of recursing forever.

---

### How do DOM events propagate?

**Headline (30s):** Every DOM event travels through three phases: **capture** (from root down to target), **target** (at the element), then **bubble** (back up to root). Most listeners run in the bubble phase by default. Bubbling enables *event delegation* — one listener on a parent handles events from many children, which is how React implements its event system.

#### The three phases

1. **Capture** — event descends from `document` → `html` → `body` → ... → target's parent.
2. **Target** — event reaches the element that was acted on.
3. **Bubble** — event ascends back up the same path to `document`.

```javascript
document.body.addEventListener('click', () => console.log('body (bubble)'));
document.body.addEventListener('click', () => console.log('body (capture)'), true);
button.addEventListener('click', () => console.log('button'));

// Clicking the button logs:
// body (capture)  → capture phase
// button          → target
// body (bubble)   → bubble phase
```

#### Event delegation

Don't attach 1000 listeners to 1000 list items — attach one to the parent and match on the target.

```javascript
parent.addEventListener('click', (e) => {
  const item = e.target.closest('.item');
  if (!item) return;
  console.log('Item clicked:', item.textContent);
});
```

Benefits: fewer listeners (lower memory), works for dynamically added children (no rebinding).

#### React's synthetic event system

React implements event delegation at the root container: a single listener catches every click, then dispatches to the right component. The event object you receive is a **SyntheticEvent** — a cross-browser wrapper around the native event.

Handler naming:

- `onClick` — bubble phase (default).
- `onClickCapture` — capture phase.

**Gotcha — SyntheticEvent pooling (React ≤ 16):** In older React versions, the event object was reused; accessing `e.target` inside `setTimeout` returned `null`. Fixed in React 17+. If you hit this in legacy code, call `e.persist()`.

---

### Implement an EventBus / EventEmitter

**Headline (30s):** An EventBus is a simple publish/subscribe store: `on` registers a listener, `emit` fires an event with arguments, `off` removes. The standard interview version also supports `once`. The trick with `once` is to wrap the listener so it removes itself after the first call — passing the wrapper (not the original) to `on` so `off` can find it.

```typescript
class EventBus {
  private events: Record<string, Function[]> = {};

  on(event: string, listener: Function): void {
    if (!this.events[event]) this.events[event] = [];
    this.events[event].push(listener);
  }

  once(event: string, listener: Function): void {
    const wrapper = (...args: any[]) => {
      listener(...args);
      this.off(event, wrapper);  // remove the wrapper, not the original
    };
    this.on(event, wrapper);
  }

  emit(event: string, ...args: any[]): void {
    this.events[event]?.forEach(listener => listener(...args));
  }

  off(event: string, listener: Function): void {
    if (this.events[event]) {
      this.events[event] = this.events[event].filter(l => l !== listener);
    }
  }
}
```

**Gotcha — anonymous listeners:** `bus.on('x', () => {...})` can't be removed later because you don't have a reference to the function. Always save the reference if you'll need `off`.

**Gotcha — listener errors:** A listener that throws in your `emit` loop will stop subsequent listeners. Wrap the call in `try/catch` if you want graceful handling.

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

**Headline (30s):** `requestAnimationFrame` runs your callback right before the next repaint (~every 16ms at 60fps) — perfect for animation and visual updates. `requestIdleCallback` runs during leftover time at the end of a frame — perfect for *non-urgent* work (analytics, prefetching) that shouldn't compete with user input or rendering.

#### `requestAnimationFrame`

```javascript
function animate() {
  element.style.transform = `translateX(${x++}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

- Synchronized with the display refresh rate.
- Paused when the tab is hidden (battery friendly).
- The first callback receives a high-resolution timestamp.

#### `requestIdleCallback`

```javascript
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0 && workQueue.length) {
    processNext(workQueue.shift());
  }
}, { timeout: 2000 }); // fallback if idle time never arrives
```

- `deadline.timeRemaining()` tells you how many ms you have before the frame budget expires.
- The `timeout` option forces execution after that many ms even if the browser is busy.
- Not supported in Safari — use `setTimeout` as a fallback if you need it.

React Fiber uses a similar idea: split rendering into small chunks and yield back to the browser between them, so high-priority work (input, animation) isn't blocked.

**Rule of thumb:**

- Must happen this frame? → `requestAnimationFrame`.
- Low priority, whenever the browser is free? → `requestIdleCallback` (with a fallback for Safari).

---

### Finding the maximum in an array — which technique is safe for huge arrays?

**Headline (30s):** `Math.max(...arr)` and `Math.max.apply(null, arr)` are concise but push every element onto the call stack — they throw `RangeError: Maximum call stack size exceeded` on arrays of ~100k+ elements. For production code with potentially large arrays, use `reduce`. It's slightly more typing but works for any size.

```javascript
// Concise but stack-limited
Math.max(...arr);
Math.max.apply(null, arr);

// Safe for arrays of any size
arr.reduce((max, cur) => cur > max ? cur : max, arr[0]);

// Also safe (simple loop)
let max = arr[0];
for (let i = 1; i < arr.length; i++) {
  if (arr[i] > max) max = arr[i];
}
```

**Gotcha — empty arrays:** `Math.max()` with no arguments returns `-Infinity`. `reduce` without an initial value throws. Provide a sensible default for either approach.

**See also:** [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for Intersection Observer (the modern replacement for scroll-event DOM watchers), [`7.1 Event Loop`](#26.%20Event%20Loop%20/%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF) for the task/microtask scheduling model that rAF and rIC sit inside.
## 23. Browser Storage and Communication / 浏览器存储与通信

A bundle of interview questions about storing data in the browser and sending messages between tabs, iframes, and native shells.

### What's the difference between `localStorage`, `sessionStorage`, and cookies?

**Headline (30s):** All three store client-side data, but differ in capacity, lifetime, and whether the server sees them. `localStorage` persists indefinitely, `sessionStorage` is per-tab, both are client-only (never sent in requests). **Cookies** are tiny (~4KB) but automatically included in every HTTP request, which is why authentication lives there. Pick based on *who needs to read the data* (server vs. client) and *how long it should live*.

**Why interviewers ask this:** This comes up in any question about auth flows, session management, or persistence. Candidates who conflate the three write insecure auth code.

#### `localStorage`

- **Capacity:** ~5MB per origin.
- **Lifetime:** persists until cleared by script or user.
- **Access:** synchronous, same-origin, client-only (never sent in HTTP requests).
- **Use for:** user preferences (theme, language), cached client state, offline data.

#### `sessionStorage`

Identical API, tab-scoped lifetime.

- **Capacity:** ~5MB per origin.
- **Lifetime:** cleared when the tab closes (survives reloads).
- **Access:** synchronous, same-origin, tab-isolated.
- **Use for:** multi-step form state, wizard progress, temporary SPA state.

#### Cookies

- **Capacity:** ~4KB per cookie, ~20 cookies per domain.
- **Lifetime:** configurable with `Expires` / `Max-Age`; session cookies die with the browser.
- **Access:** sent with every HTTP request to the matching domain; readable via `document.cookie` unless `HttpOnly`.
- **Security flags:** `HttpOnly` (blocks JS access), `Secure` (HTTPS only), `SameSite=Strict|Lax|None` (CSRF protection).
- **Use for:** session IDs, CSRF tokens, server-side personalization.

#### Quick comparison

| Feature | localStorage | sessionStorage | Cookies |
|---|---|---|---|
| Capacity | ~5MB | ~5MB | ~4KB |
| Sent with requests | No | No | Yes |
| Lifetime | Permanent | Tab session | Configurable |
| Server access | No | No | Yes |
| Accessible to JS | Yes | Yes | Only without `HttpOnly` |

**Gotcha — don't store auth tokens in `localStorage`:** Anything in `localStorage` is readable by any script on the page. An XSS vulnerability becomes a full account takeover. Use `HttpOnly` + `Secure` + `SameSite` cookies for session tokens.

**See also:** [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for XSS/CSRF mitigation and cookie flag deep dives.

---

### `HTMLCollection` vs. `NodeList` — what's the difference?

**Headline (30s):** Both are array-like collections of DOM nodes, but differ in what they contain and how they update. **`HTMLCollection`** holds only `Element` nodes and is **always live** — it reflects DOM changes automatically. **`NodeList`** can hold any node type (Elements, Text, Comments). It's **usually static** (from `querySelectorAll`) but occasionally live (`childNodes`).

#### `HTMLCollection`

- Returned by `getElementsByClassName`, `getElementsByTagName`, `.children`.
- Contains only `Element` nodes.
- Always live — queries re-run on each access.

#### `NodeList`

- Returned by `querySelectorAll` (static), `childNodes` (live).
- Can contain any node type: `Element`, `Text`, `Comment`.
- Static or live depending on source.

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

**Headline (30s):** Four main options, roughly in order of complexity. For most same-origin cases, **`BroadcastChannel`** is the cleanest modern answer. The `localStorage` + `storage` event trick works everywhere but feels hacky. `SharedWorker` is powerful but has Safari caveats. `WebSocket` through a server is the only cross-origin option.

#### 1. `localStorage` + `storage` event

The simplest cross-browser approach. Writing to `localStorage` fires a `storage` event in *other* same-origin tabs (not the tab that wrote).

```javascript
// Tab A listens
window.addEventListener('storage', (e) => {
  if (e.key === 'message') console.log('Received:', e.newValue);
});

// Tab B sends
localStorage.setItem('message', JSON.stringify({ text: 'hello', ts: Date.now() }));
```

**Gotcha — only fires in *other* tabs:** The tab that called `setItem` does NOT receive its own event. Works only between tabs, not within one tab.

#### 2. `BroadcastChannel` API

Purpose-built for same-origin tab messaging. Much cleaner than the storage hack.

```javascript
const channel = new BroadcastChannel('app_channel');

// Listen
channel.onmessage = (e) => console.log('Received:', e.data);

// Send
channel.postMessage({ type: 'update', payload: { id: 1 } });
```

Supported in all modern browsers. First choice for new code.

#### 3. `SharedWorker`

A Web Worker that survives across tabs and can hold shared state. Each tab connects via a port.

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

**Gotcha — not supported in Safari on iOS.** Avoid if you need universal support.

#### 4. WebSockets (cross-origin or real-time)

When tabs need to share updates with a server too (chat, collaborative editing), all tabs connect to the same WebSocket; the server broadcasts.

**Rule of thumb:** Same-origin, simple → `BroadcastChannel`. Same-origin, broad support → `localStorage` + `storage` event. Cross-origin or server-driven → WebSocket.

---

### How do you communicate with an iframe?

**Headline (30s):** Use `window.postMessage(data, targetOrigin)`. It's the *only* safe way to cross origin boundaries. The parent calls `iframe.contentWindow.postMessage(...)`; the iframe calls `window.parent.postMessage(...)`. Both sides listen with `window.addEventListener('message', ...)`. **Critical:** always validate `event.origin` — never trust incoming messages without checking the sender.

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

// Receiving (both sides)
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://trusted-origin.com') return; // ALWAYS check
  console.log('Received:', e.data);
});
```

**Gotcha — never use `'*'` as the target origin in production:** `'*'` sends the message to any origin, exposing you if the iframe is hijacked or navigated to a hostile page. Always specify the exact origin you expect.

**Gotcha — origin validation is mandatory:** Without `if (e.origin !== ...)`, any page can embed your iframe and send it malicious messages. Treat incoming `message` events like untrusted input.

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

**Gotcha — security:** Never trust data coming from the web side. The bridge can be invoked by any page loaded in the WebView — including malicious ones — unless you restrict the allowed origins.

**See also:** [`1.1 Browser Basics`](#1.%20Browser%20Basics%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9F%BA%E7%A1%80) for where storage and messaging fit into the browser architecture, [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for auth storage and CSRF concerns.
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

**Sources checked 2026-10-15:** [TypeScript: Basic Types](https://www.typescriptlang.org/docs/handbook/2/basic-types), [TypeScript: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html), [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html), [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness), [Narrowing and Exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking), [TypeScript 5.0 Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators), [Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth).
## 26. Event Loop / 事件循环

#### How does JavaScript run asynchronous code on a single thread?

**Headline (30s):** JavaScript has one thread and one call stack — it can't truly do two things at once. The **event loop** is the scheduler that makes single-threaded JS feel concurrent. It pulls *one* macrotask from a queue (a `setTimeout` callback, an I/O completion, a UI event), runs it to completion, then drains all queued microtasks (Promise callbacks), then repeats. Asynchronous APIs don't "run in parallel" — they hand work off to the browser or OS, which queues a callback when the work is done.

**Why interviewers ask this:** It's the mental model behind every async bug. A candidate who can walk through a mixed `setTimeout`/Promise/sync example in order demonstrates real understanding of the runtime — not just memorized "`async` is for async stuff".

---

#### The execution model

Imagine three data structures and one loop:

1. **Call stack** — what's currently executing (synchronous code).
2. **Microtask queue** — Promise callbacks, `queueMicrotask`, `MutationObserver`.
3. **Macrotask queue** — `setTimeout`, `setInterval`, I/O completions, UI events, `setImmediate` (Node).

The loop cycle:

1. Run all synchronous code until the call stack is empty.
2. Drain the entire microtask queue (running any microtasks those create too).
3. Pick *one* macrotask from the macrotask queue, execute it.
4. Go to step 2.

**Key insight — microtasks drain completely between macrotasks.** Adding a microtask from inside another microtask will run before the next macrotask. This is why `Promise.then` always runs before `setTimeout(fn, 0)`.

---

#### Microtasks vs. macrotasks — the cheat sheet

| Microtasks | Macrotasks |
|---|---|
| `Promise.then` / `.catch` / `.finally` | `setTimeout`, `setInterval` |
| `async`/`await` continuations | I/O callbacks (fetch response, file read) |
| `queueMicrotask(fn)` | UI events (`click`, `scroll`) |
| `MutationObserver` | Rendering callbacks |
| | `setImmediate` (Node only) |

Microtasks have **higher priority** — the whole microtask queue drains between every pair of macrotasks.

---

#### Walk-through — what does this print?

```javascript
console.log('Start');

setTimeout(() => console.log('Timeout'), 0);

new Promise((resolve) => {
  console.log('Promise constructor');
  resolve();
}).then(() => console.log('Promise then'));

console.log('End');
```

Output:

```
Start
Promise constructor
End
Promise then
Timeout
```

Trace:

1. `console.log('Start')` — sync, logs immediately.
2. `setTimeout(..., 0)` — queues a macrotask.
3. `new Promise(...)` — the executor runs *synchronously*, so `'Promise constructor'` logs now. `.then()` queues a microtask.
4. `console.log('End')` — sync.
5. Call stack empty → drain microtasks → `'Promise then'`.
6. One macrotask → `'Timeout'`.

**Gotcha — the Promise constructor is synchronous.** `new Promise(fn)` runs `fn` immediately. Only `.then` / `.catch` callbacks are microtasks.

---

#### Browser vs. Node.js — similar but not identical

##### Browser

The event loop runs on the main thread alongside rendering. Between macrotasks, the browser may *render* — recalculate styles, layout, paint. This is why long-running synchronous code freezes the UI.

Cycle: **macrotask → drain microtasks → maybe render → macrotask → ...**

##### Node.js — phased macrotask queue

Node organizes macrotasks into six phases that run in order every tick:

1. **Timers** — `setTimeout` / `setInterval` callbacks whose time is up.
2. **Pending callbacks** — a few system-level I/O errors.
3. **Idle / prepare** — internal.
4. **Poll** — retrieve new I/O events.
5. **Check** — `setImmediate` callbacks.
6. **Close callbacks** — `socket.on('close')` etc.

Between *each phase*, Node drains microtasks. Among microtasks, **`process.nextTick`** has the highest priority — it runs before Promise callbacks.

```javascript
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));

// Output (deterministic for first two):
// nextTick
// promise
// timeout / immediate (order depends on timing of the top-level call)
```

**Reach for `process.nextTick`** when you need to defer work to "right after the current operation" with higher priority than Promise callbacks. Use sparingly — recursive `nextTick` calls can starve I/O.

---

#### Garbage collection — how does the engine free memory?

**Headline:** Modern JS engines use **mark-and-sweep** — starting from root references (globals, call stack locals), the GC walks every reachable object and marks them; unmarked objects are collected. This handles circular references that the older **reference counting** algorithm can't.

##### Reference counting (historical)

Each object stored its incoming reference count. When the count hit zero, the memory freed. Simple, but **circular references leak forever** — two objects pointing to each other keep each other alive even after nothing else references them. Old IE had this problem; modern engines don't.

##### Mark-and-sweep (modern)

Used by V8 (Chrome, Node) and SpiderMonkey (Firefox):

1. Find all *roots* — globals, in-scope locals, the call stack.
2. Mark every object reachable from a root.
3. Sweep — anything unmarked is garbage, free it.

V8 in particular uses **generational GC** (young generation collected frequently, old generation rarely) and **incremental marking** (interleaved with JS execution to avoid long pauses).

---

#### Common memory leak sources

Most leaks are the same pattern: something unreachable from your mental model is *actually* reachable through an unexpected reference.

- **Uncleared timers** — a `setInterval` callback holds a closure; the interval keeps a reference to the callback; no one ever clears it.
- **Detached DOM nodes** — JS variable still points to a DOM node that was removed from the tree. Neither the tree nor the JS can be freed.
- **Closures over large scopes** — a returned function keeps the entire enclosing scope alive, including big objects you don't actually use.
- **Accidental globals** — `foo = 1` (no `let`/`const`) at the top level creates a `window.foo`. Never freed.
- **Event listeners not removed** — attached on mount, never removed on unmount, keeps the component alive forever.

##### Detecting leaks

- **Chrome DevTools → Performance tab** — record for a few minutes; if heap usage keeps climbing without drops, there's a leak.
- **Memory tab → heap snapshots** — take one snapshot, do the suspect action, take another, compare. Look for objects that grew between snapshots.
- **Memory tab → allocation timeline** — records new allocations over time, marks which ones weren't freed.

**Rule of thumb:** Every subscription, listener, and timer needs a matching cleanup. In React, that's your `useEffect` return function. In vanilla JS, that's discipline — save the reference and remove it when done.

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](#12.%20JavaScript%20Memory,%20WeakMap,%20WeakSet,%20and%20WeakRef%20/%20JavaScript%20%E5%86%85%E5%AD%98%E3%80%81WeakMap%E3%80%81WeakSet%20%E4%B8%8E%20WeakRef) for how WeakMap/WeakSet help avoid leaks, [`4.3 Asynchronous JavaScript`](#19.%20Asynchronous%20JavaScript%20/%20%E5%BC%82%E6%AD%A5JavaScript) for Promise microtask scheduling details.
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

**Sources checked 2026-10-15:** [React: memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback), [useRef](https://react.dev/reference/react/useRef), [forwardRef](https://react.dev/reference/react/forwardRef), [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [Rules of Hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks), [use](https://react.dev/reference/react/use), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects).
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

**Sources checked 2026-10-15:** [Next.js 16.4.1 App Router migration guide](https://nextjs.org/docs/app/guides/migrating/app-router-migration), [Pages Router getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props), [Pages Router getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths), [Pages Router Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration), [Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data), [use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache), [Incremental Static Regeneration](https://nextjs.org/docs/app/guides/incremental-static-regeneration), [Link](https://nextjs.org/docs/app/api-reference/components/link), [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route).
## 32. Performance Metrics and Analysis / 性能指标与分析

A bundle of interview questions about how to measure, diagnose, and optimize web app performance.

### What are the Core Web Vitals, and what do they measure?

**Headline (30s):** Core Web Vitals are a small set of user-centric performance metrics Google uses to score page quality. The three key ones: **LCP** (how fast does the main content appear?), **FID/INP** (how responsive does the page feel to input?), and **CLS** (how stable is the layout?). Each has a target threshold that's considered "good". Missing them hurts SEO and user retention.

| Metric | Description | Target |
|---|---|---|
| **FP** (First Paint) | First pixel rendered on screen | — |
| **FCP** (First Contentful Paint) | First DOM content visible (text, image) | < 1.8s |
| **LCP** (Largest Contentful Paint) | Largest visible element rendered | < 2.5s |
| **FID** (First Input Delay) | Time from first interaction to response | < 100ms |
| **INP** (Interaction to Next Paint) | Replacing FID; worst-case responsiveness | < 200ms |
| **CLS** (Cumulative Layout Shift) | Visual stability during loading | < 0.1 |
| **DCL** (DOMContentLoaded) | DOM fully parsed (no stylesheets/images) | — |
| **Load** | Page + all resources fully loaded | — |

Loading order: FP → FCP → LCP → DCL → Load.

**Gotcha — FID is being replaced by INP.** INP measures the *worst* interaction latency instead of just the first — more representative of real user experience. Update your dashboards.

---

### How do you profile a page in Chrome DevTools?

**Headline (30s):** Three tabs cover 90% of perf work. **Performance** — record a flame chart of CPU/network/rendering to find long tasks and layout thrash. **Network** — waterfall view to find slow/blocking requests. **React DevTools Profiler** — component render times and wasted re-renders. Use Lighthouse (or its CLI) for automated scoring and a ranked list of issues.

- **Performance tab** — record CPU, memory, network, rendering. Screenshots at intervals show when content actually appears.
- **Network tab** — request waterfall, timing breakdown, size analysis.
- **React DevTools** — "Highlight updates when components render" visualizes re-renders.

#### Lighthouse

Automated auditing tool that scores Performance, Accessibility, Best Practices, and SEO.

```bash
npx lighthouse https://example.com --view --preset=desktop
```

Lighthouse gives actionable suggestions: modern image formats (WebP/AVIF), eliminate render-blocking resources, reduce unused JavaScript, set explicit image dimensions.

---

### How do you diagnose and fix slow pages?

**Headline:** Split the problem into *slow loading* (network, bundle size, server response) and *slow rendering* (long tasks, bad component structure). Diagnose with the Performance tab; apply the right fix per category.

#### Slow loading

- Optimize server response time (backend or edge caching).
- Use a CDN for static assets.
- Enable HTTP caching (`Cache-Control`, `ETag`).
- Route-based code splitting (`React.lazy` + `Suspense`).
- Compress assets (gzip, Brotli).
- Preload critical resources (`<link rel="preload">`).

#### Slow rendering

- Profile with DevTools to find long tasks (anything > 50ms).
- Optimize API response times; show loading UI for anything > 200ms.
- Use SSR/SSG for content-heavy pages (see [`9.4 Next.js`](#31.%20Next.js%20/%20Next.js%E5%BC%80%E5%8F%91)).
- Virtualize long lists (see [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96)).

---

### How does HTTP caching work?

**Headline (30s):** Two mechanisms work together: **`Cache-Control: max-age=N`** tells the browser to reuse the cached copy for N seconds without asking (strong cache). **`ETag`** (or `Last-Modified`) gives the server a fingerprint — when max-age expires, the browser asks "still valid?"; if yes, the server responds 304 with no body, saving bandwidth (negotiated cache). Done right, users never re-download unchanged assets.

| Header | Purpose |
|---|---|
| `Cache-Control: max-age=31536000` | Cache for 1 year; use content-hashed filenames for cache busting |
| `ETag` | Version identifier; server returns 304 if unchanged |
| `Last-Modified` | Timestamp-based validation |

**Strategy:**

- **Immutable assets** (JS/CSS bundles with content hash in the filename) — long `max-age`, never revalidated.
- **HTML** — `no-cache` (or short `max-age`) with `ETag` so the browser always checks for updates but avoids re-downloading if nothing changed.

**Gotcha — `no-cache` ≠ "don't cache".** `no-cache` means "cache, but always revalidate with the server". Use `no-store` if you truly never want caching (rarely right outside sensitive pages).

---

### What's the difference between debounce and throttle?

**Headline (30s):** Both rate-limit a function but with different strategies. **Debounce** — wait until the caller has stopped calling for N ms, then run once. Good when only the final value matters (search input). **Throttle** — run at most once every N ms, ignoring calls in between. Good when steady updates matter (scroll handlers, mousemove).

#### Debounce

Fires after a period of inactivity. Each call resets the timer.

```javascript
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
```

**Use cases:** search input (fire the API call only when the user pauses typing), form validation, window resize handling.

#### Throttle

Fires at most once per interval.

```javascript
function throttle(fn, interval) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}
```

**Use cases:** scroll handlers, mousemove tracking, rate-limited API calls.

| | Debounce | Throttle |
|---|---|---|
| Fires | After inactivity period | At regular intervals |
| Best for | Final value matters (search) | Steady updates matter (scroll) |

**Gotcha — leading vs. trailing edge:** "Trailing" debounce fires at the *end* of inactivity (the common implementation above). "Leading" fires at the *start*. Some APIs need both — lodash's `debounce(fn, delay, { leading: true, trailing: true })` handles it.

---

### How do you optimize first-screen render?

**Headline:** Do less work, do it sooner, defer the rest. Five tactics to apply in order:

1. **Route lazy loading** — split SPA bundles per route, load on demand (`React.lazy` + `Suspense`).
2. **SSR / SSG** — pre-render HTML on the server for immediate content display.
3. **Above-the-fold prioritization** — inline critical CSS, defer non-critical JS, eager-load LCP image.
4. **Image optimization** — lazy-load below-fold images, use `srcset`, modern formats (WebP/AVIF), explicit dimensions.
5. **Pagination / infinite scroll** — load data incrementally instead of all at once.

**Rule of thumb:** The first screen should render from the minimum amount of JS and CSS needed. Everything else — analytics, chat widgets, secondary content — should be deferred to after LCP.

**See also:** [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD), [`9.4 Next.js`](#31.%20Next.js%20/%20Next.js%E5%BC%80%E5%8F%91) for SSR/SSG strategies.

---

### How would you design an analytics SDK with minimal perf impact?

**Headline (30s):** Three design principles: **don't block rendering** (fire-and-forget, no sync work), **batch events** (collect locally, flush periodically), and **use the right transport** (`navigator.sendBeacon` for reliability including page unload; image beacons as fallback). Track page views, custom events, performance metrics, and errors.

#### What to track

- **Page Views (PV)** — navigation events via the History API.
- **Custom Events** — business-specific (button clicks, form submissions).
- **Performance Data** — `performance.timing`, Core Web Vitals.
- **Errors** — `window.onerror`, `unhandledrejection` (see [`4.5 Error Handling`](#21.%20Error%20Handling%20/%20%E9%94%99%E8%AF%AF%E5%A4%84%E7%90%86)).

#### Reporting strategy

```javascript
function report(url, data) {
  const body = JSON.stringify(data);
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body); // reliable even during unload
  } else {
    new Image().src = `${url}?data=${encodeURIComponent(body)}`; // fallback
  }
}
```

**Why `sendBeacon`:** it's designed for this. Fires the request in the background without waiting; works even when the page is about to close; doesn't block navigation.

#### Batching

Collect events in memory; flush every 10 seconds or on `beforeunload`. Reduces request count drastically.

```javascript
const queue = [];
function track(event) {
  queue.push({ event, ts: Date.now() });
  if (queue.length >= 50) flush();
}
function flush() {
  if (queue.length === 0) return;
  report('/analytics', queue.splice(0));
}
setInterval(flush, 10_000);
window.addEventListener('beforeunload', flush);
```

**See also:** [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for rendering-side perf, [`5.3 Image Lazy Loading`](#24.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for a focused image-perf playbook.
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

**Reach for this when** you need a quick reference for ahooks — the React hooks library that covers the hooks people keep rewriting in every project (data fetching, debounced state, localStorage sync, stable callbacks, virtual lists).

**Headline:** ahooks is an Alibaba-maintained React hooks library with production-ready hooks in five buckets — **Data fetching** (`useRequest`, `usePagination`, `useInfiniteScroll`), **State** (`useBoolean`, `useToggle`, `useMap`, `useLocalStorageState`, `useLatest`), **Performance** (`useMemoizedFn`, `useCreation`, `useVirtualList`), **Lifecycle/timing** (`useMount`, `useUnmount`, `useDebounce`, `useThrottle`), and **Dynamic lists** (`useDynamicList`). Install with `npm install ahooks`.

#### Data fetching

##### `useRequest`

Core data-fetching hook with loading states, error handling, polling, debouncing, throttling, caching, retry, and pagination built in.

```javascript
import { useRequest } from 'ahooks';

const { data, loading, error, run } = useRequest(fetchUserData, {
  manual: false,
  pollingInterval: 5000,
  debounceWait: 300,
  retryCount: 3,
  onSuccess: (data) => console.log(data),
  onError: (error) => console.error(error),
});
```

**Reach for it when** you'd otherwise write 20+ lines of fetching boilerplate per component. Replaces most hand-rolled `useEffect + fetch` patterns.

##### `usePagination`

Extends `useRequest` for paginated lists with automatic page state management.

```javascript
const { data, loading, pagination } = usePagination(fetchUsers, {
  defaultPageSize: 20,
});

pagination.changeCurrent(2);
pagination.changePageSize(50);
```

##### `useInfiniteScroll`

Infinite scroll loading with threshold detection.

```javascript
const { data, loading, noMore } = useInfiniteScroll(
  d => fetchMoreItems(d?.nextCursor),
  { target: containerRef, threshold: 100 }
);
```

#### State hooks

##### `useToggle` / `useBoolean`

```javascript
const [state, { toggle, setTrue, setFalse }] = useBoolean(false);
```

`useToggle` generalizes to any two values.

##### `useMap` / `useSet`

State management for `Map` and `Set` with convenient mutation helpers.

```javascript
const [map, { set, remove, reset }] = useMap([['key1', 'value1']]);
set('key2', 'value2');
remove('key1');
```

##### `useLocalStorageState`

State that auto-syncs with `localStorage`, handles serialization and errors.

```javascript
const [theme, setTheme] = useLocalStorageState('theme', {
  defaultValue: 'light',
});
```

##### `useLatest`

Returns a ref that always holds the latest value. Solves **stale closure** bugs in `setInterval`/`setTimeout` callbacks.

```javascript
const latestCount = useLatest(count);

useEffect(() => {
  const timer = setInterval(() => {
    console.log(latestCount.current);
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

#### Performance hooks

##### `useMemoizedFn`

Like `useCallback` but without a dependency array. Returns a stable function reference that always invokes the *latest* version of the function. No stale closures, no manual dep tracking.

```javascript
const handleClick = useMemoizedFn(() => {
  console.log(count);
});
```

**Reach for it instead of `useCallback`** when you want a stable reference but always the freshest state. Significantly safer in practice.

##### `useCreation`

A more reliable `useMemo` that guarantees referential stability and never recalculates unnecessarily (unlike `useMemo`, which the React docs warn may re-run even without dep changes).

##### `useVirtualList`

Virtualizes long lists — renders only visible items.

```javascript
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(
  originalList,
  { itemHeight: 50, overscan: 5 }
);
```

See [`11.2 Rendering and Computation Optimization`](#33.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for virtual scrolling background.

#### Lifecycle hooks

##### `useMount` / `useUnmount`

Cleaner alternatives to `useEffect` for mount-only or unmount-only logic.

```javascript
useMount(() => { console.log('mounted'); });
useUnmount(() => { console.log('unmounted'); });
```

##### `useDebounce` / `useDebounceFn`

```javascript
const debouncedValue = useDebounce(searchTerm, { wait: 300 });
const { run: debouncedSearch } = useDebounceFn(search, { wait: 300 });
```

##### `useThrottle`

```javascript
const throttledValue = useThrottle(scrollPosition, { wait: 100 });
```

#### Dynamic lists

##### `useDynamicList`

Manages ordered lists with immutable operations and **stable keys** for rendering.

```javascript
const { list, push, remove, move, insert, getKey } = useDynamicList([
  { name: 'Alice' },
  { name: 'Bob' },
]);
```

Each item gets a stable key via `getKey(index)` — solves the "what do I use as key?" problem for dynamic forms and sortable lists.

#### When to reach for ahooks (vs. hand-rolled)

Reach for ahooks when:

- You're writing the same fetching/debouncing/storage patterns across multiple components.
- You need **production-ready edge-case handling** (cancellation, error retry, stale closures).
- You want **stable references** without fiddling with `useCallback` dependencies.

**Alternatives worth considering:**

- `react-query` / `@tanstack/query` — more focused, richer caching than `useRequest` for server state.
- `swr` — similar philosophy, lighter API surface.
- `zustand` — for shared state rather than per-component hook state.

**See also:** [`9.3 Advanced React`](#30.%20Advanced%20React%20/%20React%E8%BF%9B%E9%98%B6) for custom hook patterns, [`11.1 Performance Metrics and Analysis`](#32.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for debounce/throttle conceptual background.
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
