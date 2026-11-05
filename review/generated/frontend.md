# Frontend

> Generated from the [frontend reading map](../../frontend/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. How does a browser turn a URL into pixels? / 浏览器如何把 URL 变成屏幕像素？

### How does a browser turn a URL into pixels? / 浏览器如何把 URL 变成屏幕像素？

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

The document lane is incremental, not a queue of stages that each finish once. The parser can discover stylesheets, scripts, images, and other resources before reaching the end of the response. A parser-inserted classic script may pause parsing; `async`, `defer`, and module scripts have distinct schedules. See [How do scripts affect HTML parsing and readiness?](#6.%20How%20do%20scripts%20affect%20HTML%20parsing%20and%20document%20readiness?%20/%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F).

Layout produces geometry; paint produces drawing output, not a bitmap. Rasterization makes pixel content from drawing records, and compositing arranges content into a frame. Engines may reuse existing work, run parts in parallel, or use different stage names. Chromium's RenderingNG documentation is one implementation example, not a requirement for WebKit, Gecko, or the web platform. See [Why can a CSS change trigger layout, paint, or compositing work?](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F).

A URL change is not always a new document. Same-document fragment navigation and History API updates have their own behavior; see [Does every URL change load a new document?](#2.%20Does%20every%20URL%20change%20load%20a%20new%20document?%20/%20%E6%AF%8F%E6%AC%A1%20URL%20%E5%8F%98%E5%8C%96%E9%83%BD%E4%BC%9A%E5%8A%A0%E8%BD%BD%E6%96%B0%E6%96%87%E6%A1%A3%E5%90%97%EF%BC%9F). To investigate a slow or unstable page, use measurements and traces rather than assuming a stage name identifies the cause; see [How should browser performance be measured and diagnosed?](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90).

**Evidence / 资料：** [WHATWG HTML: navigation and session history](https://html.spec.whatwg.org/multipage/nav-history-apis.html); [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/); [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), checked 2026-11-05.
## 2. Does every URL change load a new document? / 每次 URL 变化都会加载新文档吗？

### Does every URL change load a new document? / 每次 URL 变化都会加载新文档吗？

No. A cross-document navigation switches to another `Document` and may fetch a response; a fragment navigation can add a session-history entry that shares the current document; `history.pushState()` and `replaceState()` update the current document's URL and history without fetching that address. Use the URL as the shareable source of route state, and synchronize the UI when the user traverses Back or Forward. / 不会。跨文档导航会切换到另一个 `Document`，并可能获取响应；片段导航可新增历史条目但仍共享当前文档；`history.pushState()` 和 `replaceState()` 则在当前文档内更新 URL 与历史记录，不会请求该地址。让 URL 保存可分享的路由状态，并在用户前进或后退时同步界面。

#### Parse query state and choose an operation / 解析查询状态并选择操作

Create a `URL` from the current address instead of splitting strings on `?` and `&`. `searchParams.get()` reads one value, `getAll()` reads repeated values, `set()` replaces values with that name, and `append()` deliberately adds another pair. Serialization handles URL encoding. Query parameters are untrusted input: validate values and keep secrets out of URLs.

- Use an anchor or `location.assign(url)` for a normal navigation that should create a history entry. Use `location.replace(url)` when the current entry should be replaced.
- Use `pushState(state, "", url)` to add a same-document entry, or `replaceState(...)` to edit the current entry. The URL must be same-origin. These calls do not fetch the URL or fire `popstate` or `hashchange`.
- On Back/Forward traversal, handle `popstate` and derive the displayed route from `location` (and `event.state` when the application uses it). Fragment navigation is distinct: history traversal involving fragment changes can dispatch `popstate`; a fragment change can also dispatch `hashchange`.

This sorting example keeps its selected value and summary in step with the query string. It updates the view directly after `pushState`, then re-reads the address after history traversal.

~~~html
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
  syncFromUrl();
});

window.addEventListener("popstate", syncFromUrl);
syncFromUrl();
</script>
~~~

A client-side router can use these same-document entries to change views, but it owns rendering and route restoration. Browser History API behavior is not the same as a document navigation, even when the visible URL changes.

**See also:** [React Router / React 路由](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) builds client-side routes on browser history; [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) covers network requests once navigation takes a fetching path.

**Standards / 规范：** [WHATWG URL Standard: `URLSearchParams`](https://url.spec.whatwg.org/#urlsearchparams-class); [WHATWG HTML: same-document navigation and History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface), checked 2026-11-05.
## 3. HTML and CSS Basics / HTML 与 CSS 基础

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

**See also:** [`2.3 Flex & Grid Layout`](#5.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for the full Grid / Flexbox reference.

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
## 4. Box Model and BFC / 盒模型与块格式化上下文

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

**See also:** [`2.6 CSS Interview Questions`](#9.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98) for float-clearing patterns and layout interview scenarios.

**Specifications / 规范：** [CSS Display: formatting contexts](https://www.w3.org/TR/css-display-3/), [CSS 2.2: block formatting contexts](https://www.w3.org/TR/CSS22/visuren.html#block-formatting), [CSS 2.2: box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions).
## 5. Flex & Grid Layout / Flex与Grid布局

**Flexbox and Grid Layout / Flexbox 与 Grid 布局**

Reach for this when you need to remember the property names and what each one does. For "how should I approach this layout?" style interview answers, the patterns live in [`2.6 CSS Interview Questions`](#9.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98).

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

**See also:** [`2.1 HTML & CSS Basics`](#3.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for CSS units used with `fr`/`minmax`, [`2.6 CSS Interview Questions`](#9.%20CSS%20Interview%20Questions%20/%20CSS%E9%9D%A2%E8%AF%95%E9%A2%98) for worked interview examples using these layouts.

**Specifications / 规范：** [CSS Flexible Box Layout](https://www.w3.org/TR/css-flexbox-1/) defines flex sizing and the automatic minimum size; [CSS Grid Layout](https://www.w3.org/TR/css-grid-2/) defines track sizing and grid-item minimums; [CSS Display](https://www.w3.org/TR/css-display-3/#order-property) describes visual reordering and accessibility.
## 6. How do scripts affect HTML parsing and document readiness? / 脚本如何影响 HTML 解析与文档就绪？

### How do scripts affect HTML parsing and document readiness? / 脚本如何影响 HTML 解析与文档就绪？

A parser-inserted classic script without `async` or `defer` can pause HTML parsing while it is fetched and run; it may also wait for an earlier stylesheet when it can inspect style. `defer` and ordinary module scripts fetch while parsing continues, then execute after parsing in their specified order; `async` scripts execute when ready without preserving relative order. Choose a mode from the script's dependencies and required start time, not from one placement rule. / 未带 `async` 或 `defer` 的解析器插入经典脚本可能在获取和执行期间暂停 HTML 解析；如果脚本能读取样式，它也可能等待之前的样式表。`defer` 与普通模块脚本会在解析期间获取，再按相应顺序于解析完成后执行；`async` 脚本就绪后即执行，不保持相对顺序。应根据依赖关系和所需运行时机选择模式，而不是依赖单一的位置口诀。

#### Script scheduling / 脚本调度

| Script | Fetch | Execution | Relative order |
|---|---|---|---|
| Parser-inserted classic, no scheduling attribute | Parser fetches it; parser pauses | When available and eligible to run | Parser order |
| External classic `defer` | In parallel with parsing | After parsing, before `DOMContentLoaded` | Document order among deferred classic scripts |
| External classic `async` | In parallel with parsing | As soon as available; parsing can pause to run it | Not preserved |
| Module without `async` | Module graph loads in parallel with parsing | Deferred until parsing is complete | Module and dependency rules |
| Module with `async` | Module graph loads in parallel | As soon as its graph is ready | Not preserved relative to other async work |
| Classic inline with `defer` | No fetch | Runs when parser reaches it | `defer` has no effect without `src` |

`DOMContentLoaded` fires after the document has been parsed and deferred and ordinary module scripts have executed; it does not wait for images or `async` scripts. A deferred script can itself wait for a stylesheet that blocks scripts, so stylesheet loading can delay that script and therefore `DOMContentLoaded`. `load` waits on a wider set of dependent resources. These milestones do not promise that every image is decoded or that the page is visually complete.

Use `defer` for ordered external classic scripts that need the parsed document. Use `async` for a script whose execution does not depend on other scripts or parser output. Module scripts are deferred by default; adding `async` changes that schedule. Dynamically inserted scripts have different defaults from parser-inserted ones, so state which case you mean.

#### Why scripts can pause the parser / 脚本为何会暂停解析

A classic script can inspect or modify the document while the parser is constructing it; it can also write markup that changes parsing. The browser therefore cannot always continue as if the script were an independent resource. A parser-blocking script's fetch can overlap resource discovery and other downloads, but its execution creates a dependency point.

Stylesheets matter when a pending script can read style information: the browser may delay that script until a blocking stylesheet is available. This is why “all CSS must finish before first paint” is inaccurate; the relevant blocking relationships depend on the script and style state.

~~~html
<head>
  <link rel="stylesheet" href="/app.css">
  <script src="/app.js" defer></script>
</head>
~~~

Here HTML parsing and script fetching can proceed together. Once parsing ends, `app.js` executes before `DOMContentLoaded`; it can rely on the parsed document, but should not assume images have loaded.

**See also:** [How does a browser turn a URL into pixels?](#1.%20How%20does%20a%20browser%20turn%20a%20URL%20into%20pixels?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E5%B1%8F%E5%B9%95%E5%83%8F%E7%B4%A0%EF%BC%9F) places script scheduling in the navigation path; [When does browser JavaScript run relative to a frame?](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F) explains tasks, microtasks, and rendering opportunities; [How should browser performance be measured and diagnosed?](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) distinguishes readiness events from user-visible performance.

**Standards / 规范：** [WHATWG HTML: the script element and script preparation](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element); [WHATWG HTML: DOMContentLoaded](https://html.spec.whatwg.org/multipage/dom.html#the-end); checked 2026-11-05.
## 7. Why can a CSS change trigger layout, paint, or compositing work? / 为什么 CSS 改动会触发布局、绘制或合成工作？

### Why can a CSS change trigger layout, paint, or compositing work? / 为什么 CSS 改动会触发布局、绘制或合成工作？

A DOM or style change invalidates only the work needed for the next correct presentation, but that dependency may include style recalculation, layout, paint, rasterization, and compositing. Layout computes geometry; paint records drawing operations; rasterization turns paint output into pixel content; compositing arranges content for a frame. Reading geometry after a write can synchronously force stale style or layout to become current, but a geometry read does not always cause a new layout. / DOM 或样式变化会使下一次正确呈现所需的工作失效，依赖链可能包含样式重算、布局、绘制、栅格化和合成。布局计算几何；绘制记录绘图操作；栅格化把绘制输出转为像素内容；合成将内容组织成画面。写入后读取几何值可能同步刷新尚未更新的样式或布局，但几何读取并不总会触发布局。

#### Which work may be invalidated? / 哪些工作可能失效？

| Change (examples) | Work often needed | Boundary |
|---|---|---|
| Geometry or line-wrap change (`width`, font metrics, inserting a node) | Style, layout, paint, then presentation | Extent depends on layout dependencies and engine |
| Visual-only style change (`color`, many backgrounds) | Style, paint, then presentation | Geometry can be reused |
| Suitable `transform` or `opacity` update | Style or compositor update, then presentation | May avoid layout and paint; layer or GPU use is not guaranteed |
| Read current geometry after DOM/style writes | Potential synchronous style/layout flush | No flush is needed if relevant state is already current |

“Reflow” and “repaint” are convenient shorthand, not portable performance scores. A small element can trigger work beyond itself, while a large subtree can be cheap when relevant data is unchanged. `transform` and `opacity` often make good animation candidates, but do not guarantee compositor-only updates, layer promotion, or GPU execution. Profile the target page and browser.

#### How does a layout read become forced work? / 布局读取如何变成同步刷新？

When script changes the DOM or a layout-affecting style, the browser may mark style or layout data dirty and defer recalculation until it needs a current result. A later API that returns current geometry—such as `offsetWidth` or `getBoundingClientRect()`—can require that pending work to run before returning. If the relevant data is already current, the same API need not trigger layout.

This loop repeatedly asks for current geometry after changing style, creating repeated flush opportunities:

~~~javascript
for (const item of items) {
  item.style.width = (item.offsetWidth + 10) + "px";
}
~~~

Collect measurements before writing. This avoids the obvious read-write-read pattern; it does not promise that every later change collapses to one layout or that batching is faster for every workload.

~~~javascript
const widths = items.map(item => item.offsetWidth);
items.forEach((item, index) => {
  item.style.width = (widths[index] + 10) + "px";
});
~~~

Choose a geometry API from the box and coordinate system needed: see [Which DOM geometry API returns the size or coordinate I need?](#8.%20DOM%20Properties%20/%20DOM%E5%B1%9E%E6%80%A7). For a measured performance problem, inspect a rendering trace; [How should browser performance be measured and diagnosed?](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) connects the trace to the user-visible symptom.

#### Standards versus an implementation pipeline / 标准行为与引擎流水线的界限

CSS and CSSOM View define observable layout results and geometry APIs. They do not require every browser to expose internal stages called “render tree,” “reflow,” “raster,” or “composite,” or require the same process and thread arrangement. Chromium's RenderingNG is one implementation example: Blink produces paint artifacts, Chromium schedules raster work into tiles, compositor components assemble frames, and Viz submits frames for display. Those names and steps describe Chromium, not all browser engines; operating-system composition and display timing also sit outside the web platform's CSS layout contract.

**Sources checked 2026-11-05:** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) for geometry APIs; [CSS Display](https://www.w3.org/TR/css-display-3/) for box and formatting behavior; [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture) for the illustrative implementation pipeline; [Chrome forced reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
## 8. DOM Properties / DOM属性

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

For threshold-based visibility tracking (e.g., lazy loading, analytics), prefer `IntersectionObserver` over repeatedly polling geometry. It reports asynchronously; it is not a guarantee that the browser performs no layout work. See [`5.3 Image Lazy Loading`](#33.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD).

#### When to reach for which

- Need an **untransformed integer layout-box size**? → `offsetHeight` / `offsetWidth`.
- Need a **viewport-relative transformed rectangle**? → `getBoundingClientRect()`.
- Need **inner content area** (for sizing children)? → `clientHeight` / `clientWidth`.
- Need to know if **overflow exists**? → compare `scrollHeight > clientHeight`.
- Need **current scroll position**, or to **scroll programmatically**? → `scrollTop` / `scrollLeft`.
- Need **viewport-relative position** (for tooltips, drag, scroll effects)? → `getBoundingClientRect()`.
- Need **position within parent** (for layout math)? → `offsetTop` / `offsetLeft` (watch out: relative to `offsetParent`, not necessarily the direct parent).

**See also:** [`2.4 Browser - HTML & CSS part`](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F) on layout thrashing when reads follow writes, [`5.3 Image Lazy Loading`](#33.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for `IntersectionObserver`-based visibility.

**Specifications / 规范：** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines these geometry APIs, including the [root `scrollHeight` rule](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight); [Intersection Observer](https://www.w3.org/TR/intersection-observer/) defines asynchronous intersection notifications.
## 9. CSS Interview Questions / CSS面试题

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

**See also:** [`2.2 Box Model and BFC`](#4.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) on how BFCs contain floats, [`2.3 Flex & Grid Layout`](#5.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for modern alternatives.

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

**See also:** [`2.3 Flex & Grid Layout`](#5.%20Flex%20&%20Grid%20Layout%20/%20Flex%E4%B8%8EGrid%E5%B8%83%E5%B1%80) for the property reference.

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
## 10. CSS Position, Display, and Animations / CSS定位、显示与动画

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

Animating `transform` and `opacity` can let an engine update presentation without recalculating layout, but neither property guarantees compositor-only or GPU work. `will-change` is a hint that may have memory and stacking effects; it does not guarantee layer promotion. See [`2.4 Browser - HTML & CSS part`](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F) for typical invalidation paths.

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* may affect compositing; it does not guarantee GPU acceleration */
}
```

**Gotcha — don't `will-change` everything:** Browsers may allocate extra resources or alter stacking behavior for hinted properties. Apply it only after measurement, keep the hinted region small, and remove it when no longer needed.

**Gotcha — `transform: translateZ(0)` is not a GPU switch:** It changes transform behavior and may affect stacking/containing blocks; it does not guarantee a faster path. Use neither it nor `will-change` as a substitute for profiling.

**See also:** [`2.2 Box Model and BFC`](#4.%20Box%20Model%20and%20BFC%20/%20%E7%9B%92%E6%A8%A1%E5%9E%8B%E4%B8%8E%E5%9D%97%E6%A0%BC%E5%BC%8F%E5%8C%96%E4%B8%8A%E4%B8%8B%E6%96%87) for formatting-context behavior, [`2.4 Browser - HTML & CSS part`](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F) for rendering invalidation, [`11.2 Rendering and Computation Optimization`](#52.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for measurement guidance.

**Specifications / 规范：** [CSS Positioned Layout](https://www.w3.org/TR/css-position-3/), [CSS Display](https://www.w3.org/TR/css-display-3/), [CSS Color opacity](https://www.w3.org/TR/css-color-4/#transparency), [CSS Transforms](https://www.w3.org/TR/css-transforms-1/), [CSS Transitions](https://www.w3.org/TR/css-transitions-2/), [W3C WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/).
## 11. How do var, let, and const differ? / var、let 与 const 有什么区别？

### How do var, let, and const differ? / var、let 与 const 有什么区别？

**Core answer / 核心回答：** Choose a declaration by its scope and whether its binding must be reassigned. var is function-scoped and starts as undefined when its binding is created. let and const are block-scoped and cannot be read before their declaration initializes them. const prevents rebinding; it does not freeze an object. / 根据作用域和是否需要重新绑定来选择声明方式。var 是函数作用域，绑定创建时初值为 undefined。let 和 const 是块级作用域，声明初始化前不可访问。const 禁止重新绑定，但不会冻结对象。

| Behavior / 行为 | var | let | const |
|---|---|---|---|
| Scope / 作用域 | Function scope; top-level behavior depends on script, module, or host / 函数作用域；顶层由脚本、模块或宿主决定 | Lexical block / 词法块 | Lexical block / 词法块 |
| Before declaration / 声明前访问 | Binding exists and is initialized to undefined / 绑定已建立并初始化为 undefined | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 |
| Same-scope redeclaration / 同作用域重复声明 | Often allowed for var / 通常允许 | Syntax error / 语法错误 | Syntax error / 语法错误 |
| Reassignment / 重新赋值 | Allowed / 允许 | Allowed / 允许 | Binding cannot be reassigned / 绑定不能重新赋值 |
| Initializer required / 是否必须初始化 | No / 否 | No / 否 | Yes / 是 |

#### How scope and initialization differ / 作用域与初始化的差异

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

let and const belong to the nearest lexical block, including if, switch, loops, and a standalone brace block. Their bindings are established with the block but remain in the Temporal Dead Zone until declaration evaluation. The precise description is not “they are never hoisted”; it is that they cannot be accessed before initialization. / let 和 const 属于最近的词法块，包括 if、switch、循环和独立代码块。进入代码块时绑定已经建立，但在声明执行前仍处于暂时性死区。准确说法不是“它们不会提升”，而是初始化前不能访问。

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

The declaration and environment rules are defined by the [ECMAScript specification](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html), including [module environment records](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records). For how outer lexical environments form the name-lookup chain and how a closure continues to access a binding, see [Scope and Closure / 作用域与闭包](#25.%20How%20do%20lexical%20scope%20and%20closures%20preserve%20access%20to%20state?%20/%20%E8%AF%8D%E6%B3%95%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E5%AF%B9%E7%8A%B6%E6%80%81%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F).
## 12. How do JavaScript values convert, compare, and become property keys? / JavaScript 值如何转换、比较并成为属性键？

### How do JavaScript values convert, compare, and become property keys? / JavaScript 值如何转换、比较并成为属性键？

**Core answer / 核心回答：** JavaScript has seven primitive types; all other values are objects, including functions. Conversions are operation-specific, equality operators use different rules, and ordinary object properties accept only strings or symbols after key conversion. Objects assigned to variables retain identity rather than being copied. / JavaScript 有七种原始类型，其余值都是对象，包括函数。转换取决于具体操作，相等运算符采用不同规则，普通对象属性键经过转换后只能是字符串或 Symbol。赋值对象时保留的是身份，不是对象副本。

#### Value types and useful facts / 类型与要点

| Type / 类型 | Useful fact / 要点 |
|---|---|
| undefined | Default value of an uninitialized var binding or a missing result / 未初始化 var 绑定或缺失结果的默认值 |
| null | Intentional absence; typeof null is the historical string "object" / 表示有意为空；typeof null 因历史兼容结果为 "object" |
| boolean | Falsy values include false, 0, -0, 0n, "", null, undefined, and NaN / 假值包括这些值 |
| number | IEEE 754 binary64; includes NaN and infinities / IEEE 754 binary64，包含 NaN 与无穷值 |
| bigint | Arbitrary-precision integers; cannot mix with Number arithmetic without conversion / 任意精度整数；算术运算不能直接与 Number 混用 |
| string | Immutable sequence of UTF-16 code units / 不可变的 UTF-16 码元序列 |
| symbol | Unique primitive value, often used as a property key / 唯一原始值，常用作属性键 |

Whether an engine stores values on a stack, heap, or elsewhere is an implementation detail. “Reference type” is useful shorthand for object identity and assignment, not a physical memory guarantee. / 值在栈、堆或其他位置存储属于引擎实现细节。“引用类型”适合描述对象身份和赋值语义，不是物理内存保证。

#### Truthiness is not numeric conversion / 真值转换不等于数值转换

Empty arrays and objects are truthy. An empty string and zero are falsy, while the nonempty string "false" is truthy. Number conversion follows different rules: Number("") and Number(null) are 0; Number(undefined) is NaN. Use explicit conversion when the input contract matters. / 空数组和空对象是真值。空字符串和零是假值，而非空字符串 "false" 是真值。数值转换遵循另一套规则：Number("") 和 Number(null) 为 0，Number(undefined) 为 NaN。输入契约重要时应显式转换。

~~~javascript
Boolean("false"); // true
Boolean([]);      // true
Number("");       // 0
Number(null);     // 0
Number(undefined);// NaN

Number.isNaN(NaN);  // true
Number.isNaN("x"); // false: no coercion
~~~

For ordinary values, Boolean(value) and !!value both apply truthiness conversion. The legacy browser document.all exception has the special `[[IsHTMLDDA]]` behavior: it is falsy, typeof returns "undefined", and it loosely equals nullish values. It is not an ordinary object. / 对普通值而言，Boolean(value) 和 !!value 都执行真值转换。浏览器历史对象 document.all 具有特殊 `[[IsHTMLDDA]]` 行为：它是假值，typeof 返回 "undefined"，并且与 nullish 值宽松相等。它不是普通对象。

See [ECMAScript Annex B IsHTMLDDA](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot). / 详见 [ECMAScript 附录 B IsHTMLDDA](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。

Logical AND returns one of its operands, not a Boolean. In React, a numeric zero on the left can therefore render as zero; compare with zero explicitly when the result should be a component or nothing. / 逻辑与会返回其中一个操作数，而非布尔值。因此在 React 中，左侧数字 0 可能直接显示为 0；若结果应当是组件或空内容，就显式比较是否大于零。

~~~jsx
{items.length > 0 && <ItemList items={items} />}
~~~

See [React conditional rendering](https://react.dev/learn/conditional-rendering) and [Advanced React / React 进阶](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) for the rendered behavior.

#### How equality rules differ / 相等比较规则有何差别

Strict equality === does not coerce across different types. Loose equality == follows several conversion rules, including the special null == undefined case; it is not simply “convert both sides to the same type.” Prefer === unless coercion is intentional. For ordinary values, value == null intentionally tests both null and undefined. / 严格相等 === 不会在不同类型间转换。宽松相等 == 遵循多条转换规则，包括 null == undefined 这一特殊情况；它并非简单地“把双方转成相同类型”。除非有意依赖转换，否则优先使用 ===。对普通值而言，value == null 可有意同时判断 null 和 undefined。

| Comparison / 比较 | NaN with itself / NaN 自身比较 | +0 with -0 / 有符号零比较 | Object values / 对象值 |
|---|---|---|---|
| === | false | equal / 相等 | identity / 身份 |
| Object.is (SameValue) | true | different / 不同 | identity / 身份 |
| Map/Set (SameValueZero) | same / 相同 | equal / 相等 | identity / 身份 |

~~~javascript
5 == "5";            // true
5 === "5";           // false
null == undefined;   // true
NaN === NaN;         // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
new Set([NaN, NaN]).size; // 1
~~~

#### Why decimal comparisons need a domain rule / 十进制数值比较为何需要场景规则

Number uses binary64, so many decimal fractions such as 0.1 and 0.2 do not have exact finite binary representations. Arithmetic may therefore produce a nearby representable result. The acceptable tolerance depends on the value’s scale and domain; there is no universal epsilon that is correct for every comparison. / Number 使用 binary64，0.1、0.2 等许多十进制小数都无法用有限二进制位精确表示，算术结果可能是邻近的可表示值。可接受容差取决于数值尺度和业务领域，不存在适用于所有比较的统一 epsilon。

~~~javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // true for this scale and example
~~~

For money, use integer minor units when the currency rules allow it, or use decimal arithmetic with an explicit rounding policy. / 金额计算可在币种规则允许时使用整数最小单位，或采用明确舍入规则的十进制运算。

#### Object assignment preserves identity / 对象赋值保留身份

Assigning an object to another binding makes both bindings refer to the same object. In a property assignment, JavaScript evaluates and remembers the base object before it evaluates the right-hand side. / 把对象赋给另一绑定后，两者引用同一个对象。属性赋值会先求值并记录基对象，然后才求值右侧。

~~~javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }
~~~

The left side captures the original object before the right side reassigns a. The final write still targets that captured original object, now also named b. / 左侧在右侧重新绑定 a 前就记录了旧对象；最终写入仍作用于该旧对象，此时它也由 b 引用。

#### How to check a value’s type / 如何判断值的类型

- typeof is useful for primitives and functions, with the historical null result shown above.
- Array.isArray reliably recognizes arrays, including arrays from another realm.
- instanceof normally checks whether the constructor’s .prototype occurs in the value’s prototype chain. Constructors from separate realms normally have distinct prototype objects, so a foreign value can fail against the local constructor but pass against its own realm’s constructor. Symbol.hasInstance can customize the check.
- Object.prototype.toString.call(value) reports a built-in tag, but Symbol.toStringTag can change the displayed tag. It is not a definitive type proof.

~~~javascript
typeof null; // "object"
Array.isArray([]); // true

const custom = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(custom); // "[object Array]" — a spoofable tag
~~~

Validate the shape or behavior the program actually requires instead of relying on a generic display string. The normative [OrdinaryHasInstance](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance) algorithm describes the default instanceof rule. / 应按程序实际需要验证结构或行为，不要只依赖通用显示字符串。默认 instanceof 规则见规范的 [OrdinaryHasInstance](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance)。

#### How bracket notation converts object keys / 方括号属性如何转换键

An ordinary property key is a string or a symbol. When another value is used inside brackets, JavaScript applies ToPropertyKey; an object can run Symbol.toPrimitive or other conversion hooks before producing a string or symbol. It is not accurate to say every key simply calls toString(). / 普通属性键是字符串或 Symbol。方括号中使用其他值时，JavaScript 执行 ToPropertyKey；对象可在生成字符串或 Symbol 前运行 Symbol.toPrimitive 等转换钩子。不能简单说所有键都会直接调用 toString()。

~~~javascript
const record = {};
record[123] = "number";
record["123"]; // "number"

const key = { [Symbol.toPrimitive]: () => "account" };
record[key] = "Ada";
record.account; // "Ada"

const first = { id: 1 };
const second = { id: 1 };
record[first] = "overwritten key";
record[second]; // "overwritten key": both became the string "[object Object]"

const map = new Map();
map.set(first, "first identity");
map.set(second, "second identity"); // Map does not coerce object keys
~~~

Use Map when object identity or uncoerced non-string keys matter. Plain-object dictionaries still convert property keys; Object.create(null) removes inherited prototype behavior, and Object.hasOwn tests own membership safely. See [Map and Set / JavaScript 中的 Map 与 Set](#13.%20When%20should%20I%20use%20Map,%20Set,%20or%20an%20object?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F). / 若需要对象身份或未经转换的非字符串键，使用 Map。普通对象字典仍会转换键；Object.create(null) 可去掉继承原型，Object.hasOwn 可安全判断自有属性。另见 [Map and Set / JavaScript 中的 Map 与 Set](#13.%20When%20should%20I%20use%20Map,%20Set,%20or%20an%20object?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F).

**Related:** [Other JavaScript Topics / JavaScript 其他主题](#17.%20What%20does%20JavaScript%20strict%20mode%20change?%20/%20JavaScript%20%E4%B8%A5%E6%A0%BC%E6%A8%A1%E5%BC%8F%E4%BC%9A%E6%94%B9%E5%8F%98%E4%BB%80%E4%B9%88%EF%BC%9F) covers strict mode; [Object and Array Methods / 对象与数组方法](#16.%20How%20do%20Object%20and%20Array%20helper%20APIs%20copy%20or%20enumerate%20data?%20/%20Object%20%E4%B8%8E%20Array%20%E8%BE%85%E5%8A%A9%E6%96%B9%E6%B3%95%E5%A6%82%E4%BD%95%E5%A4%8D%E5%88%B6%E6%88%96%E6%9E%9A%E4%B8%BE%E6%95%B0%E6%8D%AE%EF%BC%9F) explains own enumerable keys and copying APIs.
## 13. When should I use Map, Set, or an object? / 何时应使用 Map、Set 或普通对象？

### When should I use Map, Set, or an object? / 何时应使用 Map、Set 或普通对象？

**Core answer / 核心回答：** Use Map for key-value data when keys may be arbitrary values or identity matters; use Set when uniqueness or repeated membership checks are central; use arrays for ordered positions and duplicates; use ordinary objects when property-key conversion and object-shaped data are intended. Map and Set preserve insertion order and compare keys or members with SameValueZero. / 键可以是任意值或身份重要时使用 Map；唯一性或反复成员查询是重点时使用 Set；需要位置顺序或重复值时使用数组；确实需要属性键转换和对象形状时使用普通对象。Map 和 Set 保留插入顺序，并用 SameValueZero 比较键或成员。

#### Choose by data shape / 按数据形状选择

| Structure / 结构 | Use when / 适用场景 | Key or order behavior / 键与顺序 |
|---|---|---|
| Map | Arbitrary key-value pairs, object identity keys, direct iteration, or size / 任意键值、对象身份、直接遍历或 size | Any value can be a key; entries iterate in insertion order / 键可为任意值；条目按插入顺序遍历 |
| Set | Unique values or repeated membership checks / 唯一值或反复成员查询 | Values are unique and iterate in insertion order / 值唯一并按插入顺序遍历 |
| Array | Positional data, duplicates, indexed access / 位置数据、重复项、索引访问 | Each position is distinct / 每个位置都独立 |
| Object | Fixed string/symbol properties or object-shaped records / 固定字符串/Symbol 属性或对象记录 | Other keys convert to strings or symbols; prototype behavior applies unless null-prototype / 其他键转为字符串或 Symbol；除非为 null 原型，否则有原型行为 |

Ordinary dictionaries can use Object.hasOwn to distinguish own from inherited properties and avoid an overridden hasOwnProperty. Object.create(null) removes the inherited prototype but still applies property-key conversion. For that conversion rule, see [JavaScript Types / JavaScript 类型](#12.%20How%20do%20JavaScript%20values%20convert,%20compare,%20and%20become%20property%20keys?%20/%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F). / 普通对象字典可用 Object.hasOwn 区分自有与继承属性，并避免被覆盖的 hasOwnProperty。Object.create(null) 去掉继承原型，但仍执行属性键转换。转换规则见 [JavaScript Types / JavaScript 类型](#12.%20How%20do%20JavaScript%20values%20convert,%20compare,%20and%20become%20property%20keys?%20/%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F)。

#### How Map compares keys and iterates / Map 如何比较键并遍历

A Map key can be any value. Object keys are compared by identity, not by their fields. Number and string keys differ. Updating an existing key changes its value but not its insertion position; deleting and reinserting moves it to the end. / Map 的键可以是任意值。对象键按身份比较，不按字段比较；数字键和字符串键不同。更新已有键的值不会改变插入位置；删除再插入会移动到末尾。

~~~javascript
const userById = new Map();
userById.set(7, { name: "Ada" });
userById.set("7", { name: "Grace" });

userById.get(7); // { name: "Ada" }
userById.has(8); // false
userById.size; // 2

for (const [id, user] of userById) {
  console.log(id, user.name); // insertion order
}

const first = { id: 1 };
const second = { id: 1 };
const byObject = new Map([[first, "first"]]);
byObject.get(second); // undefined: different object identity
~~~

Map uses SameValueZero: NaN matches NaN, and +0 and -0 represent the same key. Common methods are set, get, has, delete, clear, and size. keys(), values(), and entries() return iterators; the default iterator is entries(). forEach receives (value, key, map). / Map 使用 SameValueZero：NaN 与自身相同，+0 和 -0 表示同一个键。常用方法为 set、get、has、delete、clear 和 size。keys()、values() 和 entries() 返回迭代器；默认迭代器为 entries()。forEach 参数顺序为 (value, key, map)。

#### How Set stores unique values / Set 如何保存唯一值

A Set stores unique values in insertion order. Delete then add a value to move it to the end. It uses SameValueZero, so NaN matches NaN, signed zeroes match, and objects are unique by identity. / Set 按插入顺序存储唯一值。删除后再次添加可把值移到末尾。它使用 SameValueZero：NaN 匹配 NaN，有符号零相同，对象按身份去重。

~~~javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]
~~~

Common methods are add, has, delete, clear, and size. keys() and values() produce the same values; entries() yields [value, value] for Map-iteration compatibility; forEach receives (value, value, set). / 常用方法为 add、has、delete、clear 和 size。keys() 与 values() 产出相同值；entries() 为兼容 Map 遍历产出 [value, value]；forEach 参数为 (value, value, set)。

#### Set composition and complexity / Set 运算与复杂度

ECMAScript 2025 standardized union, intersection, difference, symmetricDifference, isSubsetOf, isSupersetOf, and isDisjointFrom. They accept set-like inputs and return a Set or Boolean as indicated. Check support when targeting older engines. / ECMAScript 2025 标准化了 union、intersection、difference、symmetricDifference、isSubsetOf、isSupersetOf 和 isDisjointFrom。它们接受类 Set 输入，并按方法返回 Set 或布尔值。面向旧引擎时应检查支持情况。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true

const right = new Set([2, 3, 4]);
const leftOnly = [...new Set([1, 2, 3])]
  .filter(value => !right.has(value)); // [1]
~~~

For repeated membership checks, build the lookup Set once rather than inside the filter callback. A Set-based array deduplication example and its order requirements belong in [JavaScript Arrays / JavaScript 数组](#15.%20How%20do%20JavaScript%20array%20operations%20differ%20on%20holes,%20mutation,%20and%20copying?%20/%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%AF%B9%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E5%92%8C%E5%A4%8D%E5%88%B6%E6%9C%89%E4%BD%95%E5%B7%AE%E5%BC%82%EF%BC%9F). / 需要反复查询成员时，应先创建一次 Set，不要在 filter 回调中反复创建。Set 数组去重示例及其顺序要求见 [JavaScript Arrays / JavaScript 数组](#15.%20How%20do%20JavaScript%20array%20operations%20differ%20on%20holes,%20mutation,%20and%20copying?%20/%20JavaScript%20%E6%95%B0%E7%BB%84%E6%93%8D%E4%BD%9C%E5%AF%B9%E7%A9%BA%E4%BD%8D%E3%80%81%E4%BF%AE%E6%94%B9%E5%92%8C%E5%A4%8D%E5%88%B6%E6%9C%89%E4%BD%95%E5%B7%AE%E5%BC%82%EF%BC%9F)。

ECMAScript requires average access to be sublinear, not a specific O(1) implementation. End-to-end cost also depends on the surrounding algorithm. See the [ECMAScript keyed collections specification](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) and [Set methods](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects).
## 14. What do weak collections and weak references guarantee? / 弱集合和弱引用能保证什么？

### What do weak collections and weak references guarantee? / 弱集合和弱引用能保证什么？

**Core answer / 核心回答：** WeakMap and WeakSet associate or track a key without making it strongly reachable through that entry. WeakRef and finalization callbacks are opportunistic: the language does not promise when collection or cleanup occurs. Use weak references to avoid ownership, never as a correctness-critical release schedule. / WeakMap 和 WeakSet 可关联或跟踪键，而不会通过该条目强持有键。WeakRef 和最终化回调只适合机会式行为：语言不保证回收或清理的时机。弱引用用于避免所有权，不可作为正确性关键的释放计划。

#### What a WeakMap holds / WeakMap 持有和不持有什么

A WeakMap associates a weakly held key with a strongly held value. The entry does not by itself keep the key alive. WeakMap has no enumeration, size, or forEach because revealing which keys remain would expose nondeterministic garbage-collection timing. / WeakMap 将弱持有的键与强持有的值关联。条目本身不会使键保持存活。WeakMap 没有枚举、size 或 forEach，因为暴露仍存在的键会让程序观察不确定的垃圾回收时机。

Since ECMAScript 2023, keys may be objects or non-registered symbols. Symbol.for symbols are registered and cannot be weak keys. Older runtimes may support only object keys, so check the target runtime if symbol keys matter. / 自 ECMAScript 2023 起，键可为对象或非注册 Symbol。Symbol.for 创建的 Symbol 已注册，不能作为弱键。较旧运行时可能只支持对象键；需要 Symbol 键时应检查目标运行时支持。

~~~javascript
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
~~~

Typical uses include metadata keyed by objects owned elsewhere, or data associated with class instances without adding a public property. Even if the WeakMap value refers back to its key, the entry alone does not keep that key alive; another strong path to the key can still keep it alive. / 常见用途包括为其他代码持有的对象保存元数据，或为类实例关联数据而不添加公开属性。即使 WeakMap 的值又引用该键，条目本身也不会让键存活；其他强引用路径仍可能保留它。

#### When WeakSet fits / 何时适合使用 WeakSet

WeakSet weakly tracks objects or non-registered symbols and supports membership operations, but no enumeration or size. It is useful for identity-based “seen” tracking when retaining the tracked value would be undesirable. / WeakSet 弱持有对象或非注册 Symbol，只提供成员操作，没有枚举或 size。若不希望跟踪操作延长对象生命周期，可用它按身份记录“已见过”的值。

~~~javascript
const processed = new WeakSet();

function processOnce(value) {
  if (processed.has(value)) return;
  processed.add(value);
  // perform work once for this identity
}
~~~

A normal Set or Map strongly retains members or keys. Use one when iteration, counting, or deterministic lifetime management matters. / 普通 Set 或 Map 会强持有成员或键；需要遍历、计数或确定生命周期时使用普通集合。

#### What WeakRef and finalization cannot promise / WeakRef 与最终化不能承诺什么

WeakRef and FinalizationRegistry were standardized in ES2021. WeakRef.deref() returns its target if still available, otherwise undefined. FinalizationRegistry may schedule a cleanup callback after a target becomes unreachable. Neither collection time nor callback time is guaranteed, and the callback may not run before program exit. Do not use these APIs for correctness-critical resource release, accounting, or prompt UI updates. / WeakRef 和 FinalizationRegistry 于 ES2021 标准化。WeakRef.deref() 在目标仍可用时返回它，否则返回 undefined。FinalizationRegistry 可能在目标不可达后安排清理回调。回收和回调时机均无保证，程序退出前也可能不执行。不要用这些 API 处理正确性关键的资源释放、计数或及时 UI 更新。

If deref() returns a target, ECMAScript keeps it alive until the current job completes. This keeps behavior consistent within that job but does not promise that the target remains afterward. / deref() 返回目标后，ECMAScript 会使它至少存活到当前 job 结束，以保证该 job 内行为一致；这不承诺目标之后仍存活。

The [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) and [weak-reference specification](https://tc39.es/ecma262/2025/multipage/managing-memory.html) permit implementation-dependent collection latency. Reachability models and heap-diagnostic context are covered by [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F).
## 15. How do JavaScript array operations differ on holes, mutation, and copying? / JavaScript 数组操作对空位、修改和复制有何差异？

### How do JavaScript array operations differ on holes, mutation, and copying? / JavaScript 数组操作对空位、修改和复制有何差异？

**Core answer / 核心回答：** Choose an array operation by whether it reads values or keys, skips holes, mutates the receiver, consumes an iterator, or makes a shallow copy. These details affect the result even when two operations look like equivalent ways to “loop” or “copy.” / 选择数组操作时要看它遍历值还是键、是否跳过空位、是否修改原数组、是否消费迭代器，以及是否只做浅拷贝。即使两个操作看起来都在“遍历”或“复制”，细节也会影响结果。

#### Should I iterate keys or values? / 应遍历键还是值？

Use for...of for values from an iterable. Use for...in only when enumerating property names, usually on a plain object. A normal dense array’s own index keys are visited in ascending order, but for...in can also include custom and inherited enumerable string properties. / 用 for...of 遍历可迭代对象的值。for...in 用于枚举属性名，通常用于普通对象。普通稠密数组的自有索引键按升序访问，但 for...in 也可能包含自定义及继承的可枚举字符串属性。

~~~javascript
const values = [10, 20];
for (const key in values) console.log(key); // "0", "1"
for (const value of values) console.log(value); // 10, 20

const record = { name: "Ada", age: 36 };
for (const [key, value] of Object.entries(record)) {
  console.log(key, value); // own enumerable string-keyed properties
}
~~~

A hole is different from an own property whose value is undefined. for...of reads a hole as undefined; map and filter skip absent indices; for...in lists only existing enumerable properties. Avoid for...in when array positions are the data. / 空位不同于值为 undefined 的自有属性。for...of 读取空位会得到 undefined；map 和 filter 跳过不存在的索引；for...in 只列出现存可枚举属性。数组位置本身代表数据时不要用 for...in。

See the [ECMAScript for-in/for-of rules](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements). For iteration protocol details, see [Iterators and Generators / 迭代器与生成器](#29.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F).

#### How do array methods treat holes and mutation? / 数组方法如何处理空位和原数组？

- map transforms each present index and returns a new array. It skips holes and preserves corresponding holes in its result.
- filter returns present values that pass the predicate. It skips holes and does not copy them.
- some and every stop when the answer is known; both skip holes. On an empty array, some is false and every is true.
- reduce folds present elements and skips holes. Supply an initial value when the empty-array case needs a defined result.
- concat returns a shallow new array and can consult Symbol.isConcatSpreadable. Spread syntax instead follows the iterable protocol.
- sort and reverse mutate the receiver; ES2023 toSorted and toReversed return copies. Sorting is stable since ES2019. Default sort compares string forms, not numeric values.

~~~javascript
[1, 11, 2].sort(); // [1, 11, 2]: string ordering
[1, 11, 2].toSorted((a, b) => a - b); // [1, 2, 11]; original is unchanged

const sparse = [, "x"];
[...sparse]; // [undefined, "x"]: spread consumes the iterator
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
sparse.flat(); // ["x"]: flat removes holes at flattened levels
~~~

The callback arity also matters: map passes value, index, and array. parseInt interprets its second parameter as a radix, so passing it directly changes the radix for later items. / 回调参数个数也会影响结果：map 传入值、索引和数组。parseInt 把第二个参数作为基数，因此直接传给 map 会让后续元素使用不同基数。

~~~javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
~~~

The callback arguments are part of the [ECMAScript Array.prototype.map algorithm](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map).

#### How shallow are array and object copies? / 数组和对象复制有多浅？

Array spread consumes an iterable and copies yielded values shallowly. Nested objects remain shared. Object spread is separate: it copies an object’s own enumerable properties into a new object. / 数组展开会消费可迭代对象，并浅拷贝产出的值；嵌套对象仍然共享。对象展开则会把对象的自有可枚举属性复制到新对象。

~~~javascript
const original = [{ score: 1 }];
const copy = [...original];
copy[0].score = 2;
original[0].score; // 2: the nested object is shared

const merged = { ...defaults, ...overrides }; // later properties replace earlier ones
~~~

Transpilers can lower spread differently according to the target and helper settings. Do not treat output such as [].concat(value) as the language semantics: array spread consumes an iterator, while concat differs for sparse arrays and spreadable objects. / 转译器会按目标和辅助函数配置采用不同输出。不要把 [].concat(value) 之类的输出当作语言语义：数组展开消费迭代器，而 concat 对稀疏数组和可展开对象的处理不同。

#### How should nested arrays be flattened? / 应如何展平嵌套数组？

flat(depth), standardized in ES2019, returns a shallowly flattened copy and defaults to depth 1. Use flat(Infinity) for arbitrary nesting; it removes holes at flattened levels and does not recursively flatten non-array iterables. / ES2019 标准化的 flat(depth) 返回浅层展平副本，默认深度为 1。任意深度可用 flat(Infinity)；它会移除被展平层级中的空位，不会递归展平非数组可迭代对象。

A recursive implementation makes the rule explicit but can exceed the call-stack limit on deeply nested input. This version visits every numeric position, so a hole becomes undefined, unlike flat. / 递归实现能直观表达规则，但极深输入可能超出调用栈限制。这个版本访问每个数值索引，因此空位会变为 undefined，与 flat 不同。

~~~javascript
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
~~~

The historical iterative [].concat(...items) pattern flattens one level per pass. It can hit argument-count limits, repeatedly copy large arrays, and produce different sparse-array results from flat. It may return the original input when no nested array exists. / 传统迭代写法 [].concat(...items) 每轮展平一层，可能触发参数数量限制、反复复制大数组，且稀疏数组结果不同于 flat。若无嵌套数组，它还可能直接返回原输入。

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

Prefer flat when its depth and hole semantics match the task. For Set/Map equality used by deduplication, see [Map and Set / JavaScript 中的 Map 与 Set](#13.%20When%20should%20I%20use%20Map,%20Set,%20or%20an%20object?%20/%20%E4%BD%95%E6%97%B6%E5%BA%94%E4%BD%BF%E7%94%A8%20Map%E3%80%81Set%20%E6%88%96%E6%99%AE%E9%80%9A%E5%AF%B9%E8%B1%A1%EF%BC%9F). That page owns the keyed-collection contract; this page keeps the array-specific decision and examples.
## 16. How do Object and Array helper APIs copy or enumerate data? / Object 与 Array 辅助方法如何复制或枚举数据？

### How do Object and Array helper APIs copy or enumerate data? / Object 与 Array 辅助方法如何复制或枚举数据？

**Core answer / 核心回答：** Check which properties an API selects, whether it mutates an existing target, and whether an array input is treated as iterable or array-like. Similar-looking helpers can differ in ownership, symbols, getters, holes, and return values. / 选择 API 时要确认它读取哪些属性、是否修改已有目标，以及数组输入按可迭代对象还是类数组对象处理。外观相似的方法在属性归属、Symbol、getter、空位和返回值上可能不同。

#### Object.assign: copy into an existing target / Object.assign：复制到已有目标

Object.assign(target, ...sources) copies each source’s own enumerable string and symbol properties into target, mutates and returns target, and lets later sources overwrite earlier properties. The copy is shallow. Reading a source may invoke getters; writing to the target may invoke setters. / Object.assign(target, ...sources) 把来源对象的自有可枚举字符串键和 Symbol 键复制到 target，修改并返回 target；后面的来源覆盖前面的属性。复制是浅拷贝。读取来源对象可能调用 getter，写入 target 可能调用 setter。

~~~javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target is { a: 1, b: 3, c: 4 }

const merged = Object.assign({}, defaults, overrides);
~~~

Object spread also makes a shallow copy, but creates own data properties on a new object. Object.assign writes to its existing target and can invoke target setters. / 对象展开同样进行浅拷贝，但会在新对象上创建自有数据属性。Object.assign 写入已有目标，可能调用目标 setter。

#### What Object.keys, values, and entries include / Object.keys、values 和 entries 会包含什么

Object.keys was standardized in ES5; Object.values and Object.entries were added in ES2017. They select own, enumerable, string-keyed properties. Symbol-keyed properties are excluded. For ordinary objects, array-index string keys come first in ascending numeric order; other string keys follow creation order. This ordinary-object order is not a guarantee for proxies or every exotic object. / Object.keys 属于 ES5；Object.values 和 Object.entries 于 ES2017 加入。它们选择自有、可枚举、字符串键属性，不包含 Symbol 键。普通对象的数组索引字符串键先按数值升序排列，其余字符串键按创建顺序排列。代理和特殊对象不一定遵循普通对象顺序。

~~~javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]

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

For the exact ordinary-object own-key ordering, see [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys). To distinguish own from inherited properties, see [Objects and Prototypes / 对象与原型](#21.%20How%20do%20JavaScript%20objects%20find%20and%20organize%20properties?%20/%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%92%8C%E7%BB%84%E7%BB%87%E5%B1%9E%E6%80%A7%EF%BC%9F).

Object.is applies SameValue equality: NaN equals itself, while +0 and -0 differ. For the comparison table and Map/Set’s SameValueZero rule, see [JavaScript Types / JavaScript 类型](#12.%20How%20do%20JavaScript%20values%20convert,%20compare,%20and%20become%20property%20keys?%20/%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F). / Object.is 使用 SameValue 相等规则：NaN 与自身相等，而 +0 和 -0 不同。比较表及 Map/Set 的 SameValueZero 规则见 [JavaScript Types / JavaScript 类型](#12.%20How%20do%20JavaScript%20values%20convert,%20compare,%20and%20become%20property%20keys?%20/%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F)。

#### When Array.from and Array.of differ / Array.from 与 Array.of 有何区别

Array.from creates an array from an iterable or an array-like input and can map each value during creation. Array-like inputs are read by index, so a missing index becomes undefined in the result. Array.of treats every argument as an element, avoiding Array’s special single-number length behavior. / Array.from 可从可迭代对象或类数组对象创建数组，并能在创建时映射元素。类数组对象按索引读取，因此缺失索引会在结果中变成 undefined。Array.of 把每个参数都作为元素，避免 Array 对单个数字参数的长度特判。

~~~javascript
const arrayLike = { 0: "a", 1: "b", length: 2 };
Array.from(arrayLike); // ["a", "b"]

Array.from(new Set([1, 2, 2, 3])); // [1, 2, 3]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]
Array.from([, "x"]); // [undefined, "x"]

Array(3);    // length 3 with three holes
Array.of(3); // [3]
Array.of(1, 2, 3); // [1, 2, 3]
~~~

Array.from accepts either an iterable or an array-like input, but those are different protocols. For iteration details, see [Iterators and Generators / 迭代器与生成器](#29.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F). Newer APIs such as Object.hasOwn and Array.prototype.at are listed in [Modern JavaScript Features / 现代 JavaScript 特性](#18.%20How%20do%20edition%20and%20runtime%20support%20affect%20JavaScript%20feature%20use?%20/%20%E8%AF%AD%E8%A8%80%E7%89%88%E6%9C%AC%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6%E6%94%AF%E6%8C%81%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20JavaScript%20%E7%89%B9%E6%80%A7%E7%9A%84%E4%BD%BF%E7%94%A8%EF%BC%9F). The relevant methods are defined in the [ECMAScript fundamental objects](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) and [indexed collections](https://tc39.es/ecma262/2025/multipage/indexed-collections.html) sections.
## 17. What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？

### What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？

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

For the strict-call effect on this, see [Function this and Binding / 函数 this 与绑定](#22.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F). For value conversion, truthiness, and equality, see [JavaScript Types / JavaScript 类型](#12.%20How%20do%20JavaScript%20values%20convert,%20compare,%20and%20become%20property%20keys?%20/%20JavaScript%20%E5%80%BC%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E3%80%81%E6%AF%94%E8%BE%83%E5%B9%B6%E6%88%90%E4%B8%BA%E5%B1%9E%E6%80%A7%E9%94%AE%EF%BC%9F).
## 18. How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？

### How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？

**Core answer / 核心回答：** A feature’s ECMAScript edition and support in the target runtime are separate facts. Syntax must parse in the target environment or be transformed; APIs also need runtime support or a suitable polyfill. Check the actual browsers, Node versions, and build target before relying on a feature. / 特性属于哪个 ECMAScript 版本，与目标运行时是否支持是两件事。语法必须能被目标环境解析或经过转换；API 也需要运行时实现或合适的 polyfill。依赖某项特性前要检查实际浏览器、Node 版本和构建目标。

#### Selected APIs and edition boundaries / 部分 API 与版本边界

| Feature / 特性 | Edition or source / 版本或来源 | Boundary / 边界 |
|---|---|---|
| Object.keys | ES5 | Own enumerable string keys / 自有可枚举字符串键 |
| Object.assign, Object.is | ES2015 | Object.assign mutates its target; Object.is uses SameValue / Object.assign 会修改目标；Object.is 使用 SameValue |
| Object.values, Object.entries | ES2017 | Own enumerable string-keyed values or pairs / 自有可枚举字符串键的值或键值对 |
| Array.from, Array.of | ES2015 | Iterable/array-like conversion or argument list / 可迭代或类数组转换，或参数列表建数组 |
| Promise.all, Promise.race | ES2015 | Outcome semantics and cancellation limits: see [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 完成条件和不取消其他操作见异步页 |
| Promise.allSettled | ES2020 | See [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 见异步页的 Promise 比较表 |
| Promise.any | ES2021 | See [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) / 见异步页的 Promise 比较表 |
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

**See also:** [Optional Chaining and Destructuring / 可选链与解构](#19.%20How%20do%20optional%20access%20and%20destructuring%20handle%20missing%20values?%20/%20%E5%8F%AF%E9%80%89%E8%AE%BF%E9%97%AE%E5%92%8C%E8%A7%A3%E6%9E%84%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E7%BC%BA%E5%A4%B1%E5%80%BC%EF%BC%9F) explains syntax semantics; [Modules and Host Boundaries / 模块与宿主边界](#20.%20How%20do%20ECMAScript%20modules%20and%20CommonJS%20differ?%20/%20ECMAScript%20%E6%A8%A1%E5%9D%97%E4%B8%8E%20CommonJS%20%E6%9C%89%E4%BD%95%E5%8C%BA%E5%88%AB%EF%BC%9F) explains ESM and CommonJS; [Object and Array Methods / 对象与数组方法](#16.%20How%20do%20Object%20and%20Array%20helper%20APIs%20copy%20or%20enumerate%20data?%20/%20Object%20%E4%B8%8E%20Array%20%E8%BE%85%E5%8A%A9%E6%96%B9%E6%B3%95%E5%A6%82%E4%BD%95%E5%A4%8D%E5%88%B6%E6%88%96%E6%9E%9A%E4%B8%BE%E6%95%B0%E6%8D%AE%EF%BC%9F) covers property-copying and enumeration behavior.
## 19. How do optional access and destructuring handle missing values? / 可选访问和解构如何处理缺失值？

### How do optional access and destructuring handle missing values? / 可选访问和解构如何处理缺失值？

**Core answer / 核心回答：** Optional chaining stops only on null or undefined, nullish coalescing defaults only for those same values, and destructuring defaults apply only when the extracted value is undefined. These operators preserve meaningful falsy values such as 0, false, and the empty string. / 可选链只在 null 或 undefined 时短路，空值合并也仅对这两种值使用默认值，解构默认值则只在取出的值为 undefined 时生效。这些语法会保留 0、false 和空字符串等有效假值。

#### Optional chaining and nullish coalescing / 可选链与空值合并

Optional chaining checks the value immediately before ?. It does not test general falsiness. A missing root identifier still throws, and grouping ends the chain. / 可选链检查 ?. 前紧邻的值，不判断一般假值。根标识符不存在时仍会抛错；括号分组会结束链式短路。

~~~javascript
const user = { profile: null };
user.profile?.name; // undefined

const count = 0;
count?.toFixed(0); // "0"

const key = "value";
const object = { value: 1 };
object?.[key]; // 1

const maybeCall = undefined;
maybeCall?.(); // undefined
~~~

Use ?? when only nullish values should trigger a fallback; use || when every falsy value should. Unparenthesized mixing of ?? with || or && is a syntax error. / 仅 nullish 值应触发默认值时使用 ??；所有假值都应触发时使用 ||。?? 与 || 或 && 不加括号混用会产生语法错误。

~~~javascript
const settings = {};
settings.timeout ?? 1000; // 1000
settings.timeout || 1000; // 1000
0 ?? 1000; // 0
0 || 1000; // 1000
~~~

#### Destructuring defaults and rest / 解构默认值与剩余项

Destructuring reads object properties or iterable values into bindings. A default initializer runs only when the extracted value is undefined, not for null, false, zero, or an empty string. Object rest gathers remaining own enumerable properties; array rest consumes the remaining iterator values. / 解构会把对象属性或可迭代对象的值读入绑定。默认值仅在取出值为 undefined 时运行，不适用于 null、false、0 或空字符串。对象剩余项收集其余自有可枚举属性；数组剩余项消费迭代器中剩余的值。

~~~javascript
const user = { name: "Ada", active: false, role: "reader" };
const { name: displayName, active = true, ...extra } = user;
// displayName is "Ada"; active stays false; extra is { role: "reader" }

const [first, , ...tail] = ["a", "b", "c"];
// first is "a"; tail is ["c"]
~~~

Array destructuring depends on the iterable protocol, not numeric property names alone. See [Iterators and Generators / 迭代器与生成器](#29.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F).

#### What tagged templates do not do / 带标签模板不会自动做什么

Template literals interpolate expressions into strings. A tagged template instead passes cooked string segments and interpolated values separately to a function. It can implement formatting or domain-specific processing, but it does not sanitize interpolated input automatically. / 模板字符串会把表达式插入字符串。带标签模板会把处理后的字符串片段和插值分别传给函数，可用于格式化或领域特定处理，但不会自动净化插值输入。

The syntax and defaulting rules here complement edition/API support in [Modern JavaScript Features / 现代 JavaScript 特性](#18.%20How%20do%20edition%20and%20runtime%20support%20affect%20JavaScript%20feature%20use?%20/%20%E8%AF%AD%E8%A8%80%E7%89%88%E6%9C%AC%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6%E6%94%AF%E6%8C%81%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20JavaScript%20%E7%89%B9%E6%80%A7%E7%9A%84%E4%BD%BF%E7%94%A8%EF%BC%9F).
## 20. How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？

### How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？

**Core answer / 核心回答：** ECMAScript modules (ESM) are standardized JavaScript syntax with static imports and exports, module-scoped bindings, strict mode, and top-level this equal to undefined. CommonJS (CJS) is Node’s module wrapper using require and module.exports. Module syntax, host loading rules, bundler analysis, and runtime scheduling are separate concerns. / ECMAScript 模块（ESM）是标准 JavaScript 语法，使用静态导入与导出，绑定属于模块作用域，自动采用严格模式，顶层 this 为 undefined。CommonJS（CJS）是 Node 使用 require 和 module.exports 的模块包装机制。模块语法、宿主加载规则、打包器分析和运行时调度是不同问题。

#### ESM syntax and dynamic import / ESM 语法与动态导入

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

#### What differs between ESM and CJS / ESM 与 CJS 有何不同

| Concern / 维度 | ECMAScript module / ES 模块 | Node CommonJS / Node CommonJS |
|---|---|---|
| Static syntax / 静态语法 | import, export | require(), module.exports |
| Top-level await / 顶层 await | Supported / 支持 | Not supported in a CJS wrapper / CJS 包装器中不支持 |
| Top-level this / 顶层 this | undefined | Node wrapper’s exports value / Node 包装器的 exports 值 |
| Strict mode / 严格模式 | Automatic / 自动采用 | Depends on code context / 取决于代码上下文 |

Node determines whether a file is ESM or CJS using extensions, package settings, or explicit input options; browser module loading follows browser rules. CommonJS is not ECMAScript module syntax. / Node 根据扩展名、包配置或显式输入选项判断文件属于 ESM 还是 CJS；浏览器模块加载遵循浏览器规则。CommonJS 不是 ECMAScript 模块语法。

See the [ECMAScript module specification](https://tc39.es/ecma262/2025/multipage/ecmascript-language-scripts-and-modules.html) and [Node.js ESM documentation](https://nodejs.org/api/esm.html). This page describes module semantics and loading boundaries, not Node event-loop ordering; see [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F) for scheduling.

#### Why ESM syntax does not guarantee tree shaking / 为什么 ESM 语法不保证 tree shaking

A bundler can analyze ESM imports for tree shaking, but using ESM syntax alone does not guarantee code removal. The result depends on the bundler and package metadata. See [Build Tools / 构建工具](#42.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F) for the transform and production-output boundary. / 打包器可分析 ESM 导入并执行 tree shaking，但仅使用 ESM 语法并不保证代码会被移除；结果还取决于打包器和包元数据。变换与生产产物边界见 [Build Tools / 构建工具](#42.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F).
## 21. How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？

### How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？

**Core answer / 核心回答：** An object first checks its own properties, then follows its internal prototype link until a match or the end of the chain. Constructor prototypes supply a default prototype to instances created with new, while instance fields, prototype methods, static members, and property descriptors control where properties live and how they behave. / 对象先查自有属性，再沿内部原型链接向上查找，直到找到匹配属性或到达链尾。构造函数的 prototype 为 new 创建的实例提供默认原型；实例字段、原型方法、静态成员和属性描述符决定属性的位置与行为。

#### How prototype lookup works / 原型查找如何工作

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

#### Where instance, prototype, and static properties live / 实例、原型与静态属性分别在哪里

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

#### How property descriptors affect reads and writes / 属性描述符如何影响读写

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

#### Which object shapes are engine-specific / 哪些对象形状细节属于引擎实现

V8 uses HiddenClasses (also called Maps) to track object shapes and optimize property access. Objects initialized with the same named properties in the same order can share a shape in V8. This is an implementation detail, not an ECMAScript guarantee; optimize layouts only when profiling identifies a real cost. / V8 使用 HiddenClasses（也称 Maps）跟踪对象形状并优化属性访问。在 V8 中，以相同顺序初始化相同命名属性的对象可能共享形状。这是实现细节，不是 ECMAScript 保证；只有性能分析发现实际成本时才优化布局。

See [Fast properties in V8](https://v8.dev/blog/fast-properties). For how a call supplies this and how new creates an instance, see [Function this and Binding / 函数 this 与绑定](#22.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F) and [Construction with new / 使用 new 构造对象](#23.%20What%20does%20new%20do%20when%20it%20constructs%20an%20object?%20/%20new%20%E6%9E%84%E9%80%A0%E5%AF%B9%E8%B1%A1%E6%97%B6%E5%81%9A%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%9F).
## 22. How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？

### How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？

**Core answer / 核心回答：** An ordinary function gets its this value from the call form: obj.method() supplies obj, call/apply supply an explicit receiver, and bind creates a bound function. A plain strict-function call uses undefined. An arrow function instead captures this from its surrounding lexical environment and cannot be rebound. / 普通函数的 this 由调用方式决定：obj.method() 以 obj 为接收者，call/apply 显式提供接收者，bind 创建绑定函数；严格函数的普通调用中 this 为 undefined。箭头函数从外层词法环境捕获 this，不能重新绑定。

#### Ordinary calls supply the receiver / 普通调用形式提供接收者

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

#### Explicit receiver methods / 显式接收者方法

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

Lexical name lookup and lexical this are separate ideas: closures capture outer bindings, while an ordinary function’s this depends on its invocation. See [Scope and Closure / 作用域与闭包](#25.%20How%20do%20lexical%20scope%20and%20closures%20preserve%20access%20to%20state?%20/%20%E8%AF%8D%E6%B3%95%E4%BD%9C%E7%94%A8%E5%9F%9F%E4%B8%8E%E9%97%AD%E5%8C%85%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E5%AF%B9%E7%8A%B6%E6%80%81%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F).

#### Why a small bind helper is not a polyfill / 简化 bind 模型为何不是 polyfill

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

Ordinary function call behavior is specified by ECMAScript’s [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call), [bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind), and arrow-function definitions. / 普通函数调用行为见 ECMAScript 的 [Function.prototype.call](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.call)、[bind](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-function.prototype.bind) 和箭头函数定义。
## 23. What does new do when it constructs an object? / new 构造对象时做了什么？

### What does new do when it constructs an object? / new 构造对象时做了什么？

**Core answer / 核心回答：** For a constructible function, new creates a receiver whose prototype comes from the constructor’s effective prototype, calls the constructor with that receiver as this, then returns an explicit object or function result if supplied. A primitive return is ignored. / 对可构造函数，new 会创建一个原型取自构造函数有效 prototype 的接收者，以它作为 this 调用构造函数；若构造函数显式返回对象或函数，则返回该值，否则返回新接收者。原始值返回会被忽略。

~~~mermaid
flowchart LR
  A["Read effective constructor prototype"] --> B["Create receiver with that prototype"]
  B --> C["Call constructor with receiver as this"]
  C --> D{"Did it return an object or function?"}
  D -- "yes" --> E["Return explicit result"]
  D -- "no: undefined or primitive" --> F["Return created receiver"]
~~~

#### Constructor and instance relationship / 构造函数与实例的关系

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

#### Object returns replace the created receiver / 返回对象会替换新建接收者

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

Classes and built-in constructors have additional construction semantics, so use new or class syntax in application code rather than this teaching helper. For property lookup and the roles of instance, prototype, and static members, see [Objects and Prototypes / 对象与原型](#21.%20How%20do%20JavaScript%20objects%20find%20and%20organize%20properties?%20/%20JavaScript%20%E5%AF%B9%E8%B1%A1%E5%A6%82%E4%BD%95%E6%9F%A5%E6%89%BE%E5%92%8C%E7%BB%84%E7%BB%87%E5%B1%9E%E6%80%A7%EF%BC%9F).
## 24. How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？

### How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？

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
## 25. How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？

### How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？

**Core answer / 核心回答：** JavaScript resolves a name from the function’s definition environment outward, not from its caller. A closure is a function that keeps access to bindings from that lexical environment. It reads the binding’s current value, so state can remain observable after the outer call returns. / JavaScript 按函数的定义环境向外查找名称，不按调用者的位置查找。闭包让函数继续访问定义时外层词法环境中的绑定；它读取绑定的当前值，因此外层函数返回后状态仍可被观察。

#### How name lookup follows lexical structure / 名称查找如何沿词法结构进行

An identifier lookup starts in the current lexical environment and continues through its enclosing environments. The caller’s local variables are not inserted into a function’s lookup chain. Execution contexts and lexical environment records are the specification model for this behavior; engines need not allocate objects with those exact names or shapes. / 标识符先在当前词法环境中查找，再逐层向外查找。调用者的局部变量不会插入被调用函数的查找链。执行上下文和词法环境记录是规范描述这种行为的模型；引擎不必创建名称和结构完全相同的对象。

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

#### What a closure retains / 闭包保留了什么

A closure is a function together with its access to the lexical bindings it uses. It does not copy the value present when the function was created. / 闭包是函数及其对所用词法绑定的访问能力；创建函数时的值不会被定格为一份副本。

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
double(5); // 10

function attachLogger(element, label) {
  element.addEventListener("click", () => console.log("Clicked: " + label));
}
~~~

#### Why loop callbacks differ / 循环回调为什么读到不同值

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

#### How closure lifetime relates to memory / 闭包生命周期与内存有何关系

An outer call returning does not make a captured binding immediately unusable. As long as a reachable closure can observe it, the program must preserve the behavior. This does not mean every variable in the entire outer scope must occupy memory forever; implementations can optimize unobservable values. / 外层调用返回并不意味着捕获的绑定立即失效。只要可达闭包仍能观察它，程序就必须保留可观察行为；但这不表示外层作用域中的所有变量都必然永久占用内存，引擎可以优化不可观察的值。

Think in terms of reachability: a long-lived listener that closes over a large object can keep that object reachable. Remove the listener and other references when their lifetime ends. A cycle alone is not a leak; the important question is whether a path from live program state still reaches the objects. For garbage-collection models and diagnostics, see [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F). / 从可达性判断更实用：长期保存的监听器若闭包捕获大型对象，就可能让对象继续可达。生命周期结束时移除监听器及其他引用。循环引用本身不等于泄漏，关键是活动程序状态是否仍有到这些对象的引用路径。垃圾回收模型与排查见[事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F)。

**See also:** [JavaScript Basics / JavaScript 基础](#11.%20How%20do%20var,%20let,%20and%20const%20differ?%20/%20var%E3%80%81let%20%E4%B8%8E%20const%20%E6%9C%89%E4%BB%80%E4%B9%88%E5%8C%BA%E5%88%AB%EF%BC%9F) explains the binding and temporal-dead-zone rules that determine which environment a closure can capture. Ordinary function this is determined by call form, not lexical name lookup; see [Function this and Binding / 函数 this 与绑定](#22.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F).
## 26. How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？

### How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？

**Core answer / 核心回答：** A callback gives an API a function to call later. A Promise represents one future fulfillment or rejection and composes with then and catch. An async function returns a Promise, while await writes the same control flow in sequential syntax. Promise combinators coordinate already-started work; they do not cancel it. / 回调把函数交给 API 供其稍后调用。Promise 表示未来的一次成功或拒绝，并可通过 then 和 catch 组合。async 函数返回 Promise，await 用顺序语法表达同一控制流。Promise 组合方法协调已经启动的任务，但不会取消它们。

Promises were standardized in ES2015, async functions and await in ES2017, and async iteration in ES2018. Asynchronous APIs allow a program to continue while work is pending; that does not by itself imply parallel JavaScript computation. / Promise 于 ES2015 标准化，async 函数与 await 于 ES2017 标准化，异步迭代于 ES2018 标准化。异步 API 让程序在等待任务时继续推进，但这本身不表示 JavaScript 计算并行执行。

#### What a Promise state means / Promise 状态表示什么

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

For deciding where to recover or propagate a rejection, see [Error Handling / 错误处理](#30.%20Where%20should%20a%20JavaScript%20error%20be%20recovered%20or%20reported?%20/%20JavaScript%20%E9%94%99%E8%AF%AF%E5%BA%94%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%81%A2%E5%A4%8D%E6%88%96%E4%B8%8A%E6%8A%A5%EF%BC%9F).

#### Which Promise combinator fits? / 应选择哪个 Promise 组合方法？

| Method / 方法 | Returned Promise fulfills when / 成功条件 | Returned Promise rejects when / 拒绝条件 |
|---|---|---|
| Promise.all | Every input fulfills; result values keep input order / 全部成功；结果按输入顺序排列 | An input rejects / 任一输入拒绝 |
| Promise.allSettled | All inputs settle; each outcome is returned / 全部结束并返回各项结果 | Not because an input rejects / 不会因某项输入拒绝 |
| Promise.any | First input fulfills / 首项成功 | All inputs reject with AggregateError / 全部拒绝并产生 AggregateError |
| Promise.race | First settlement is fulfillment / 首项完成为成功 | First settlement is rejection / 首项完成为拒绝 |

These methods coordinate inputs; they do not cancel losing operations. Passing promises usually means their underlying work has already started. If an API supports cancellation and abandoned work should stop, use its explicit mechanism, such as AbortController with Fetch. / 这些方法用于协调输入，不会取消未获胜的操作。传入 Promise 时，其底层任务通常已经启动。若 API 支持取消且不再需要的工作应停止，使用其显式机制，例如 Fetch 配合 AbortController。

The methods were added across editions: Promise.all and Promise.race in ES2015, Promise.allSettled in ES2020, and Promise.any in ES2021. Their normative completion behavior is in the [ECMAScript Promise combinator algorithms](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-combinator-objects). Promise.race installs both fulfillment and rejection reactions for each input in [PerformPromiseRace](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace).

#### When should operations be awaited sequentially or concurrently? / 何时顺序等待，何时并发推进？

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

for await...of consumes async iterables in order and can also adapt a synchronous iterable of Promises, awaiting each value before continuing. For independent operations, Promise.all is usually clearer. The protocol and sequential-consumption details belong to [Iterators and Generators / 迭代器与生成器](#29.%20How%20do%20iterators%20and%20generators%20produce%20values%20on%20demand?%20/%20%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E7%94%9F%E6%88%90%E5%99%A8%E5%A6%82%E4%BD%95%E6%8C%89%E9%9C%80%E4%BA%A7%E5%87%BA%E5%80%BC%EF%BC%9F).

#### How Promise-job order is observed / 如何观察 Promise job 顺序

Promise reactions are queued as jobs. When one handler queues a later reaction, already-queued jobs run first. The host determines checkpoints, so keep browser task/rendering rules and Node scheduling rules in [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F), not in this language-level note. / Promise 处理器会排入 job 队列。某个处理器新增后续处理器时，已排队的 job 先运行。检查点由宿主决定；浏览器任务/渲染规则和 Node 调度规则见[事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F)，不在此处混作语言保证。

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

See [ECMAScript Promise jobs](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects) and the [browser event-loop standard](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops). Node queue ordering and CJS/ESM context are explained separately in the runtime note. The focused [Currying and Partial Application / 柯里化与部分应用](#27.%20How%20does%20currying%20support%20partial%20application?%20/%20%E6%9F%AF%E9%87%8C%E5%8C%96%E5%A6%82%E4%BD%95%E6%94%AF%E6%8C%81%E9%83%A8%E5%88%86%E5%BA%94%E7%94%A8%EF%BC%9F) and [Chainable Task Queue / 链式任务队列](#28.%20How%20can%20a%20chainable%20API%20queue%20delayed%20tasks?%20/%20%E9%93%BE%E5%BC%8F%20API%20%E5%A6%82%E4%BD%95%E6%8E%92%E9%98%9F%E6%89%A7%E8%A1%8C%E5%BB%B6%E5%90%8E%E4%BB%BB%E5%8A%A1%EF%BC%9F) articles preserve two code exercises from the original collection.
## 27. How does currying support partial application? / 柯里化如何支持部分应用？

### How does currying support partial application? / 柯里化如何支持部分应用？

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

Currying transforms argument flow; it does not change how ordinary function this is supplied. See [Function this and Binding / 函数 this 与绑定](#22.%20How%20does%20a%20JavaScript%20function%20get%20its%20this%20value?%20/%20JavaScript%20%E5%87%BD%E6%95%B0%E7%9A%84%20this%20%E5%80%BC%E5%A6%82%E4%BD%95%E7%A1%AE%E5%AE%9A%EF%BC%9F).
## 28. How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？

### How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？

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

For standard Promise composition, rejection propagation, and concurrency, see [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F). Timer callback scheduling is host behavior; see [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F).
## 29. How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？

### How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？

**Core answer / 核心回答：** An iterable provides an iterator through Symbol.iterator; each iterator next() call returns an object whose done value tells the consumer whether to stop. A generator implements this protocol by pausing at yield. Async iterables provide next results asynchronously and are consumed in order with for await...of. / 可迭代对象通过 Symbol.iterator 提供迭代器；每次调用 next() 返回带 done 值的对象，用于告知消费者是否停止。生成器在 yield 处暂停，以此实现该协议。异步可迭代对象异步提供 next 结果，并由 for await...of 按序消费。

#### How iterable and iterator protocols work / 可迭代与迭代器协议如何工作

The iterable protocol exposes Symbol.iterator, which returns an iterator. The iterator’s next() method returns an object. The consumer converts its done property to Boolean; if done is missing, it acts as false. value supplies the current item and can be absent on completion. An object is not iterable just because it has numeric keys or a length. / 可迭代协议通过 Symbol.iterator 返回迭代器。迭代器的 next() 返回对象。消费者把 done 转为布尔值；若缺少 done，按 false 处理。value 提供当前项，完成时可以省略。有数字键或 length 的对象不会自动变成可迭代对象。

Arrays, strings, Maps, Sets, typed arrays, and arguments objects are language-provided iterables. NodeList is iterable in modern browser DOM implementations, but it is a host API rather than a JavaScript-language collection. Plain objects are not iterable by default. / 数组、字符串、Map、Set、类型化数组和 arguments 对象由语言提供迭代能力。现代浏览器 DOM 实现中的 NodeList 也可迭代，但它是宿主 API，不是 JavaScript 语言集合。普通对象默认不可迭代。

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

#### How early exit closes an iterator / 提前退出如何关闭迭代器

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

#### What yield and next(value) exchange / yield 与 next(value) 交换什么

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

#### Why generators are useful for lazy sequences / 生成器为何适合惰性序列

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

#### How async iteration differs / 异步迭代有何不同

An async iterable (standardized in ES2018) supplies Symbol.asyncIterator. Each next() call makes its iterator result available asynchronously; for await...of waits for each result in sequence. This suits streams whose next value becomes available over time. A synchronous array of independent Promises is usually clearer with Promise.all. / 异步可迭代对象（ES2018 标准化）通过 Symbol.asyncIterator 提供迭代器，每次 next() 异步提供迭代结果；for await...of 按顺序等待各项，适合后续值逐渐到达的流。同步数组中相互独立的 Promise 通常用 Promise.all 更清晰。

See [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) for Promise aggregation and host scheduling. Browser and Node event-loop details remain in [Event Loop and Host Scheduling / 事件循环与宿主调度](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F).
## 30. Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？

### Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？

**Core answer / 核心回答：** Handle a failure at the layer with enough context to recover, add information, or report it. If the current layer cannot decide what recovery means, propagate the error. A catch that only logs and returns can silently turn failure into success; browser-global and React handlers cover specific last-resort scopes. / 应在拥有足够上下文进行恢复、补充信息或上报的层级处理错误。当前层无法决定如何恢复时，应继续传播。只记录日志后正常返回的 catch 会悄悄把失败转成成功；浏览器全局处理器和 React 边界只覆盖特定的兜底范围。

#### What try/catch/finally cover / try/catch/finally 能处理什么

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

#### When to define a custom Error / 何时定义自定义 Error

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

#### How to propagate or recover a Promise rejection / 如何传播或恢复 Promise 拒绝

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

Every rejection needs an owner somewhere in the call chain. The browser’s unhandledrejection event is useful for diagnostics, but it is a late signal, not a substitute for local recovery or deliberate propagation. Host reporting and process behavior differ. See [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) for Promise chain mechanics. / 每个拒绝都应由调用链某处明确负责。浏览器的 unhandledrejection 事件可用于诊断，但只是较晚的信号，不能替代本地恢复或明确传播。宿主上报和进程行为有所不同。Promise 链机制见 [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

#### What browser-global handlers cover / 浏览器全局处理器覆盖什么

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

#### What React error boundaries cover / React 错误边界覆盖什么

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
## 31. DOM Manipulation and Events / DOM操作与事件

**DOM Manipulation and Events / DOM 操作与事件**

DOM APIs expose tree mutation, events, and scheduling, but API guarantees differ from framework behavior and browser rendering choices. DOM 标准规定树与事件语义；框架事件系统和渲染性能细节另有版本与实现边界。

### How do you write a proper deep copy?

**Headline (30s):** JSON round-tripping only copies JSON-compatible data: it drops or changes values and rejects cycles. `structuredClone` handles cycles and supported built-in types; a handwritten clone is a domain-specific policy, not a universal deep-copy algorithm. **中文：** JSON 往返只适用于有限的数据形状；结构化克隆覆盖更多内建类型；手写克隆必须明确支持范围。

**Why interviewers ask this:** It tests your grasp of reference semantics, edge cases (cycles, special types), and whether you can design a recursive function with proper memoization.

#### Why `JSON.parse(JSON.stringify(x))` is insufficient

- **Changed values:** a `Date` serializes to a string; a typical `Map` or `Set` becomes `{}`.
- **Unsupported values:** object properties whose values are `undefined`, functions, or symbols are omitted; such array entries become `null`; a top-level unsupported value can make parsing fail.
- **Circular references and `BigInt`:** `JSON.stringify` throws.

Reach for `structuredClone(value)` (see [`3.8 Modern JavaScript Features`](#18.%20How%20do%20edition%20and%20runtime%20support%20affect%20JavaScript%20feature%20use?%20/%20%E8%AF%AD%E8%A8%80%E7%89%88%E6%9C%AC%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6%E6%94%AF%E6%8C%81%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20JavaScript%20%E7%89%B9%E6%80%A7%E7%9A%84%E4%BD%BF%E7%94%A8%EF%BC%9F)) for supported structured-cloneable values. Functions and DOM nodes are not cloneable, and cloning does not preserve arbitrary class behavior. Use a handwritten clone only for a deliberately bounded data model or a custom policy (for example, omitting selected fields).

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

**See also:** [`5.3 Image Lazy Loading`](#33.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for Intersection Observer, [`7.1 Event Loop`](#40.%20When%20does%20browser%20JavaScript%20run%20relative%20to%20a%20frame?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%20JavaScript%20%E5%A6%82%E4%BD%95%E4%B8%8E%E6%AF%8F%E4%B8%80%E5%B8%A7%E4%BA%A4%E9%94%99%EF%BC%9F) for the task/microtask scheduling model around browser callbacks.

**Standards and current docs / 规范与文档：** [WHATWG DOM events](https://dom.spec.whatwg.org/#concept-event-dispatch), [ECMAScript array objects](https://tc39.es/ecma262/multipage/indexed-collections.html), [WHATWG structured data](https://html.spec.whatwg.org/multipage/structured-data.html), [React DOM event handlers](https://react.dev/learn/responding-to-events), [React 17 event delegation change](https://react.dev/blog/2020/08/10/react-v17-rc#changes-to-event-delegation), [requestIdleCallback specification](https://w3c.github.io/requestidlecallback/), [Chrome `requestIdleCallback` guide](https://developer.chrome.com/blog/using-requestidlecallback), [CSSOM View](https://www.w3.org/TR/cssom-view-1/).
## 32. Browser Storage and Communication / 浏览器存储与通信

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

**See also:** [`1.1 Browser Basics`](#1.%20How%20does%20a%20browser%20turn%20a%20URL%20into%20pixels?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E5%B1%8F%E5%B9%95%E5%83%8F%E7%B4%A0%EF%BC%9F) for the navigation path that creates a new document, [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for auth storage and CSRF concerns.

**Standards and current guidance / 标准与文档：** [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html), [WHATWG Storage Standard](https://storage.spec.whatwg.org/), [WHATWG DOM collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection), [MDN storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), [WHATWG cross-document messaging and BroadcastChannel](https://html.spec.whatwg.org/multipage/web-messaging.html), [WHATWG WebSockets](https://websockets.spec.whatwg.org/), [IETF cookies draft (work in progress)](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/).
## 33. Image Lazy Loading / 浏览器图片懒加载

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

**See also:** [`11.1 Performance Metrics and Analysis`](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for Core Web Vitals and broader image-perf strategies, [`5.1 DOM Manipulation and Events`](#31.%20DOM%20Manipulation%20and%20Events%20/%20DOM%E6%93%8D%E4%BD%9C%E4%B8%8E%E4%BA%8B%E4%BB%B6) for `IntersectionObserver` in other use cases.

**Standards / 规范：** [WHATWG `img` element and source requirements](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element), [WHATWG lazy-loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes), [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/), [CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/).
## 34. How should a UI render a streamed answer without mistaking partial output for completion? / 界面如何呈现流式回答而不把部分内容误判为完成？

### How should a UI render a streamed answer without mistaking partial output for completion? / 界面如何呈现流式回答而不把部分内容误判为完成？

**Core answer / 核心回答：** Treat a streamed answer as partial until the client receives and validates an explicit terminal event for the same run. Keep useful deltas visible, label them as incomplete, and bound decoding, buffering, rendering, and recovery. If the event connection ends without a terminal event, preserve the text but treat the result as unknown and query the run's authoritative status. Stopping the local reader cancels this view; stopping server work requires a separate cancellation request and confirmation. / 收到并验证同一次运行的明确终态事件之前，都应把流式回答视为部分结果。保留有用的增量文本并标记为未完成，同时限制解码、缓冲、渲染和恢复的资源。如果事件连接在终态事件前结束，应保留文本、把结果视为未知并查询运行的权威状态。停止本地读取只会取消当前视图；停止服务端工作需要单独发出取消请求并确认。

**Key terms / 关键术语：** partial output / 部分输出；terminal event / 终态事件；run state / 运行状态；resume cursor / 恢复游标；backpressure / 背压；local cancellation / 本地取消。

#### Which state can the interface safely show? / 界面可以准确显示哪些状态？

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

#### A small application protocol / 简洁的应用协议

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

#### Executable protocol model / 可执行协议模型

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

Leave partial output visible when it remains useful, but label it as incomplete and avoid actions that require a finished result. Expose a concise state message in a dedicated status region, for example a native element with role=status and aria-live=polite. Announce connection, completion, failure, or stop transitions and perhaps occasional long-running progress; do not announce every token. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](#3.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for native controls and status semantics.

**Representative answer / 代表性回答：** I treat streamed output as framed bytes that may arrive in arbitrary chunks. The client incrementally decodes UTF-8, validates sequence numbers, keeps partial text, and displays completion only after a valid terminal event. It batches rendering, bounds memory and retries, and tears down the local reader on stop or route change. A client abort does not prove the server run stopped, so I query the run record or request cancellation separately. / 我会把流式输出视为可能以任意分块到达的带帧字节。客户端增量解码 UTF-8、校验序号、保留部分文本，并且只在收到有效终态事件后显示完成。界面合并渲染、限制内存和重试次数，并在用户停止或路由卸载时清理本地读取器。客户端中止不能证明服务端运行已停止，因此还要查询运行记录或单独请求取消。

#### Related notes / 相关笔记

- [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) owns transport selection, SSE framing, EventSource limits, and Fetch stream boundaries.
- [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) explains deadlines, cancellation, retry safety, and unknown outcomes.
- [AI Application Architecture / AI应用架构](../../ai-engineering/systems/ai-application-architecture.md) owns run identity, durable state, checkpoints, side effects, and server cancellation.

**Sources checked 2026-10-15 / 来源核对日期：** The [WHATWG Streams Standard](https://streams.spec.whatwg.org/) defines readable-stream readers and local consumer cancellation; the [DOM Standard's AbortController](https://dom.spec.whatwg.org/#interface-abortcontroller) defines signaling abort to an API that accepts an AbortSignal, and [AbortSignal.throwIfAborted()](https://dom.spec.whatwg.org/#dom-abortsignal-throwifaborted) provides checkpoints between asynchronous operations; the [WHATWG Encoding Standard](https://encoding.spec.whatwg.org/) defines streaming UTF-8 decode behavior. The [WHATWG Server-sent Events section](https://html.spec.whatwg.org/multipage/server-sent-events.html) defines EventSource reconnection and event IDs; this note's parser instead exercises its explicitly synthetic newline-delimited JSON application contract. Browser behavior was not tested here.
## 35. How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？

### How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？

**Core answer / 核心回答：** Treat API bodies and browser storage as untrusted runtime data. Parse into unknown, validate both syntax and shape with JavaScript checks, then construct a trusted typed value. A type annotation, utility type, or assertion changes what the checker believes; it does not inspect incoming data. / API 响应和浏览器存储都是不可信的运行时数据。先解析为 unknown，再用 JavaScript 检查语法和结构，最后构造可信的类型化值。类型注解、工具类型或断言只改变检查器的判断，不会检查输入数据。

Type annotations are erased from emitted JavaScript. TypeScript’s type system also makes deliberate soundness tradeoffs, and any or an unchecked assertion can bypass useful checks. / 类型注解会从生成的 JavaScript 中擦除。TypeScript 类型系统也有意作出某些健全性取舍；any 或未校验的断言会绕过有效检查。

~~~mermaid
flowchart LR
  A["External text"] --> B{"JSON.parse"}
  B -- "syntax error" --> E["Parse error result"]
  B -- "valid syntax: unknown" --> C{"Runtime shape and value checks"}
  C -- "invalid shape" --> E
  C -- "valid Profile" --> D["Construct typed value"]
~~~

#### Validate a value at runtime / 在运行时校验值

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

After validation, ordinary control-flow narrowing applies to the declared model. The caller still needs to inspect ParseResult.ok before using value; a type-safe representation does not choose the application’s error policy. If the server adds a new role, this parser deliberately rejects it until the application accepts it; update the validator and exhaustive consumers together. For exhaustive handling of every role or result variant, see [Checking Every Union Case / 联合类型穷尽检查](#38.%20How%20can%20TypeScript%20check%20every%20case%20in%20a%20discriminated%20union?%20/%20TypeScript%20%E5%A6%82%E4%BD%95%E6%A3%80%E6%9F%A5%E5%88%A4%E5%88%AB%E8%81%94%E5%90%88%E7%9A%84%E6%AF%8F%E4%B8%AA%E5%88%86%E6%94%AF%EF%BC%9F). / 校验后可对声明模型执行普通控制流缩窄。调用方仍需先检查 ParseResult.ok 才能使用 value；类型安全的表示不会替应用选择错误处理策略。若服务端增加角色，解析器会先拒绝它，直到应用明确接受；应同步更新验证器和穷尽处理分支。需要确保处理每个角色或结果分支时，见[联合类型穷尽检查](#38.%20How%20can%20TypeScript%20check%20every%20case%20in%20a%20discriminated%20union?%20/%20TypeScript%20%E5%A6%82%E4%BD%95%E6%A3%80%E6%9F%A5%E5%88%A4%E5%88%AB%E8%81%94%E5%90%88%E7%9A%84%E6%AF%8F%E4%B8%AA%E5%88%86%E6%94%AF%EF%BC%9F)。

Utility types and generics describe compile-time relationships, not runtime guards: [Utility Types / 工具类型](#36.%20What%20do%20TypeScript%20utility%20types%20guarantee?%20/%20TypeScript%20%E5%B7%A5%E5%85%B7%E7%B1%BB%E5%9E%8B%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F), [Generics / 泛型](#37.%20How%20do%20TypeScript%20generics%20preserve%20relationships%20between%20types?%20/%20TypeScript%20%E6%B3%9B%E5%9E%8B%E5%A6%82%E4%BD%95%E4%BF%9D%E7%95%99%E7%B1%BB%E5%9E%8B%E4%B9%8B%E9%97%B4%E7%9A%84%E5%85%B3%E7%B3%BB%EF%BC%9F). Decorator modes answer a separate class-definition question: [TypeScript Decorators / TypeScript 装饰器](#39.%20Which%20TypeScript%20decorator%20mode%20does%20a%20project%20use?%20/%20%E9%A1%B9%E7%9B%AE%E4%BD%BF%E7%94%A8%E5%93%AA%E7%A7%8D%20TypeScript%20%E8%A3%85%E9%A5%B0%E5%99%A8%E6%A8%A1%E5%BC%8F%EF%BC%9F). JavaScript Proxy is a runtime object feature, not a TypeScript type feature; see [JavaScript Proxy / JavaScript Proxy](#24.%20How%20does%20JavaScript%20Proxy%20intercept%20object%20operations?%20/%20JavaScript%20Proxy%20%E5%A6%82%E4%BD%95%E6%8B%A6%E6%88%AA%E5%AF%B9%E8%B1%A1%E6%93%8D%E4%BD%9C%EF%BC%9F).

**Sources checked 2026-10-15:** [TypeScript Basic Types and unknown](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types and assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions), and [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness).
## 36. What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？

### What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？

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

UserPatch expresses an allowed shape to the checker; runtime code still needs to validate parsed JSON. For that boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#35.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript Utility Types reference](https://www.typescriptlang.org/docs/handbook/utility-types.html).
## 37. How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？

### How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？

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

A type parameter is not a runtime check. It describes a contract enforced by the checker where type information is available. External values still need runtime validation; see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#35.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript Generics handbook](https://www.typescriptlang.org/docs/handbook/2/generics.html).
## 38. How can TypeScript check every case in a discriminated union? / TypeScript 如何检查判别联合的每个分支？

### How can TypeScript check every case in a discriminated union? / TypeScript 如何检查判别联合的每个分支？

**Core answer / 核心回答：** Narrow a discriminated union by its tag, then assign the final branch to never. If a new member is added but not handled, the remaining value is no longer never and the assignment becomes a type error. / 先按判别字段缩小联合类型，再把最后剩余分支赋给 never。若新增成员却没有相应处理，剩余值就不再是 never，赋值会产生类型错误。

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

The never assignment checks exhaustiveness at this switch. It does not force every caller or every other switch to include the same cases, and it does not validate incoming JSON. Runtime checks establish whether an external value actually matches the declared union. See [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#35.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F).

See the [TypeScript handbook on exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking).
## 39. Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？

### Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？

**Core answer / 核心回答：** TypeScript supports standard ECMAScript decorators and a separate legacy mode. Their signatures and capabilities differ. Use the mode required by the framework and compiler configuration; do not copy a decorator from a different project without checking its mode. / TypeScript 支持标准 ECMAScript 装饰器和独立的旧版模式。两者的签名与能力不同。应使用框架和编译配置要求的模式，不要未确认模式就复制其他项目的装饰器。

#### Standard decorators in TypeScript 5.0 and later / TypeScript 5.0 及之后的标准装饰器

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

#### Legacy decorator mode / 旧版装饰器模式

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

Decorator metadata is not general runtime validation. For an external JSON value, validate the value itself with runtime logic or a validation library. For the separate unknown-JSON runtime boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](#35.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F). See the [TypeScript 5.0 decorator release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators). Sources checked 2026-10-15.
## 40. When does browser JavaScript run relative to a frame? / 浏览器 JavaScript 如何与每一帧交错？

### When does browser JavaScript run relative to a frame? / 浏览器 JavaScript 如何与每一帧交错？

A browser runs one task on a JavaScript agent to completion, then performs a microtask checkpoint that drains Promise reactions and other microtasks, including newly queued ones. A rendering opportunity is a separate user-agent decision: it may update rendering between tasks, but it need not produce a frame after every task or on a fixed 16 ms cadence. `requestAnimationFrame` is for work tied to a rendering update; `requestIdleCallback` is for deferrable work when an idle opportunity is available. / 浏览器中的一个 JavaScript agent 会把当前任务执行完，再进行微任务检查点，清空 Promise 处理器和其他微任务，包括期间新加入的微任务。渲染机会由用户代理单独决定：浏览器可在任务之间更新画面，但不必每个任务后都生成一帧，也不保证固定的 16 毫秒节奏。`requestAnimationFrame` 用于与渲染更新同步的工作；`requestIdleCallback` 用于有空闲机会时可延后的工作。

~~~mermaid
flowchart TD
    T[Run one task to completion] --> M[Microtask checkpoint]
    M -->|more microtasks queued| M
    M --> D{Rendering opportunity now?}
    D -->|no| I[Possible idle callback opportunity]
    D -->|yes| R[Run requestAnimationFrame callbacks]
    R --> U[Update rendering as needed]
    U --> I
    I --> N[Select another task]
    N --> T
~~~

This is a mental model, not a promise that every pass includes rendering or idle callbacks. A long task or endless microtask chain can keep the browser from reaching a rendering opportunity. A zero-delay timer is eligible after its minimum delay; it is not an immediate yield.

~~~javascript
console.log("start");
setTimeout(() => console.log("timer task"), 0);
Promise.resolve().then(() => console.log("Promise reaction"));
queueMicrotask(() => console.log("microtask"));
console.log("end");

// In a typical browser task:
// start
// end
// Promise reaction
// microtask
// timer task
~~~

The Promise executor runs synchronously. Promise reactions and `queueMicrotask` callbacks run as microtasks; the host later chooses when the timer task runs. A microtask added during a checkpoint is processed before the next task.

#### Visual updates and `requestAnimationFrame` / 视觉更新与 rAF

Use `requestAnimationFrame(callback)` for an update that should be made before a browser rendering update. Its callback receives a high-resolution timestamp useful for time-based animation. The callback rate follows available rendering opportunities and can vary with refresh rate and page visibility; it is not a fixed 60 Hz timer. Updating a transform in rAF can coordinate a write with rendering, but does not make the work free or guarantee a compositor path.

#### Deferrable work and `requestIdleCallback` / 可延后工作与 rIC

`requestIdleCallback(callback, {timeout})` lets the user agent schedule work during an idle period. `deadline.timeRemaining()` is an estimate, not a hard budget. Process a bounded unit and yield again; a timeout is not a reason to drain an unbounded queue. Support varies, so feature-detect it. A `setTimeout` fallback runs at a later timer opportunity but does not provide an idle-time guarantee.

~~~javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift()); // keep each unit bounded
  }
  if (workQueue.length) requestIdleCallback(runIdleSlice, { timeout: 2000 });
}
requestIdleCallback(runIdleSlice, { timeout: 2000 });
~~~

Framework schedulers such as React's scheduler are separate policies layered on host scheduling. Do not treat them as browser task queues or promise that rendering occurs between chunks.

**See also:** [How do scripts affect HTML parsing and document readiness?](#6.%20How%20do%20scripts%20affect%20HTML%20parsing%20and%20document%20readiness?%20/%20%E8%84%9A%E6%9C%AC%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20HTML%20%E8%A7%A3%E6%9E%90%E4%B8%8E%E6%96%87%E6%A1%A3%E5%B0%B1%E7%BB%AA%EF%BC%9F) describes parser scheduling; [Why can a CSS change trigger layout, paint, or compositing work?](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F) describes rendering work after DOM changes; [Asynchronous JavaScript / 异步 JavaScript](#26.%20How%20do%20callbacks,%20Promises,%20and%20async%20functions%20compose%20asynchronous%20work?%20/%20%E5%9B%9E%E8%B0%83%E3%80%81Promise%20%E4%B8%8E%20async%20%E5%87%BD%E6%95%B0%E5%A6%82%E4%BD%95%E7%BB%84%E5%90%88%E5%BC%82%E6%AD%A5%E4%BB%BB%E5%8A%A1%EF%BC%9F) covers language-level Promise behavior.

**Standards / references:** [WHATWG HTML event loops and rendering opportunities](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops); [W3C requestIdleCallback](https://www.w3.org/TR/requestidlecallback/); [Chrome requestIdleCallback guide](https://developer.chrome.com/blog/using-requestidlecallback), checked 2026-11-05.


For the host-specific server contrast, see [Node runtime and scheduling / Node 运行时与调度](../../engineering-foundations/backend/node-js-fundamentals.md).
## 41. How can a JavaScript object stay in memory after it is no longer useful? / JavaScript 对象为什么在不再有用后仍会留在内存中？

### How can a JavaScript object stay in memory after it is no longer useful? / JavaScript 对象为什么在不再有用后仍会留在内存中？

JavaScript does not promise when memory is reclaimed or require a particular garbage-collection algorithm. An object becomes eligible for collection when it is unreachable from the runtime's roots; cycles alone are collectable, but a long-lived reference to a detached node, listener, timer, closure-captured value, or cache entry can keep an object reachable. Diagnose the retaining path in a repeatable heap comparison, then release the reference at the correct lifetime boundary. / JavaScript 不承诺何时回收内存，也不要求某种垃圾回收算法。对象从运行时根不可达时才具备回收资格；循环引用本身可以回收，但长期存活的脱离 DOM 节点、监听器、计时器、闭包捕获值或缓存项会让对象仍可达。应通过可重复操作前后的堆快照检查保留路径，并在正确的生命周期边界释放引用。

A tracing collector is one implementation strategy: it starts from roots such as globals and active execution state, marks reachable objects, and can reclaim unmarked objects, including unreachable cycles. V8's Orinoco collector is a concrete example with generational, parallel, incremental, and concurrent work; those details can change and are not JavaScript language requirements.

For practical diagnosis, reproduce the same action, compare heap snapshots, and inspect retaining paths. Common leads include an uncleared interval, a listener on a long-lived object, a detached DOM node still referenced by application code, or a closure holding a large value. These patterns are investigation clues, not proof by themselves. Keep a listener, timer, subscription, or cache handle when its lifetime should end earlier than its owner, and release it at that boundary.

**See also:** [JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef](#14.%20What%20do%20weak%20collections%20and%20weak%20references%20guarantee?%20/%20%E5%BC%B1%E9%9B%86%E5%90%88%E5%92%8C%E5%BC%B1%E5%BC%95%E7%94%A8%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F) covers weak-reference use and nondeterministic cleanup; [How do DOM events propagate?](#31.%20DOM%20Manipulation%20and%20Events%20/%20DOM%E6%93%8D%E4%BD%9C%E4%B8%8E%E4%BA%8B%E4%BB%B6) covers listener lifetimes.

**Evidence:** [ECMAScript 2026 weak-reference processing model](https://tc39.es/ecma262/2026/#sec-processing-model-of-weakref-and-finalizationregistry-targets) explicitly makes no guarantee that an object will be collected at a particular time; [V8 Orinoco overview](https://v8.dev/blog/trash-talk), checked 2026-11-05, is an implementation illustration.
## 42. How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？

### How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？

**Core answer / 核心回答：** A bundler follows a module graph, transforms selected modules, and emits assets. Loaders transform individual modules; plugins use broader compiler hooks. A successful development server does not prove that the production build has the same assets, paths, chunks, or source-map exposure. / 打包器沿模块图解析依赖、转换选定模块并输出资源。loader 转换单个模块；plugin 通过更广泛的 compiler hooks 扩展构建。开发服务器成功不代表生产构建具有相同资源、路径、分块或 source map 暴露方式。

~~~mermaid
flowchart LR
  A["Entry points"] --> B["Resolve module graph"]
  B --> C["Apply loaders / transforms"]
  C --> D["Compiler and plugin hooks"]
  D --> E["Emit production assets and maps"]
  E --> F["Serve and inspect built output"]
~~~

#### How Webpack loaders and plugins differ / Webpack loader 与 plugin 有何不同

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

Sources checked 2026-10-15: [Webpack Loaders](https://webpack.js.org/concepts/loaders/), [Asset Modules](https://webpack.js.org/guides/asset-modules/), [Webpack Plugins](https://webpack.js.org/concepts/plugins/), [DefinePlugin](https://webpack.js.org/plugins/define-plugin/), [HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme), [Webpack Native HTML guide](https://webpack.js.org/guides/native-html/), [style-loader](https://github.com/webpack/style-loader#readme), [css-loader](https://github.com/webpack-contrib/css-loader#readme), [MiniCssExtractPlugin](https://github.com/webpack/mini-css-extract-plugin#readme), [Compiler hooks](https://webpack.js.org/api/compiler-hooks/).

#### Why Vite development and production need separate checks / 为什么 Vite 开发与生产需要分别检查

Vite’s development server serves native ES modules with on-demand transforms and HMR. Vite 8 uses Rolldown for its production build; earlier Vite releases used a different production bundler pipeline. State the major version when the distinction matters. / Vite 开发服务器以原生 ES 模块、按需转换和 HMR 提供资源。Vite 8 的生产构建使用 Rolldown；更早版本采用不同的生产打包链。差异重要时应注明主版本。

A fast development server is not evidence that production output has the same graph or performance. Run the configured production build and inspect its generated assets. For release verification, serve the generated output and check actual paths and chunks; HMR only validates the development loop. / 开发服务器速度快并不能证明生产产物具有相同依赖图或性能。应运行配置的生产构建并检查输出资源。发布验证要服务生成的产物并检查实际路径和分块；HMR 只验证开发循环。

Sources checked 2026-10-15: [Vite 8 guide](https://vite.dev/guide/) and [Vite 8.0.10 source](https://github.com/vitejs/vite/blob/v8.0.10/README.md).

#### What a source map exposes / Source map 会暴露什么

A source map relates emitted code to source files for debugging and error reporting. Choose Webpack devtool by rebuild speed, trace detail, artifact size, and whether the map is published. A privately uploaded map can still be exposed if deployment serves it publicly; configuration alone does not define access policy. / source map 将输出代码关联回源文件，用于调试和错误报告。选择 Webpack devtool 时要看重建速度、追踪细节、产物大小和是否公开 map。私下上传的 map 若部署时能被公开访问，仍可能暴露；配置本身不等于访问策略。

| devtool example | Output meaning / 输出含义 |
|---|---|
| eval-source-map | Evaluates modules with source maps for development debugging / 开发调试用 eval 与 source map |
| source-map | Emits an external map with a sourceMappingURL reference / 输出外部 map 并带 sourceMappingURL 引用 |
| hidden-source-map | Emits an external map without the reference comment; useful when a release process uploads maps separately / 输出外部 map 但无引用注释；适合由发布流程单独上传 |
| nosources-source-map | Omits embedded source content, but mappings and source paths may remain / 不嵌入源码内容，但映射和源码路径仍可能存在 |

These names represent different detail and delivery choices, not a universal speed ranking or security boundary. Pinning package-manager versions is a separate environment concern; see [Package Manager Pinning / 包管理器版本固定](#43.%20How%20does%20a%20project%20pin%20its%20package-manager%20version?%20/%20%E9%A1%B9%E7%9B%AE%E5%A6%82%E4%BD%95%E5%9B%BA%E5%AE%9A%E5%8C%85%E7%AE%A1%E7%90%86%E5%99%A8%E7%89%88%E6%9C%AC%EF%BC%9F). See [Webpack devtool configuration](https://webpack.js.org/configuration/devtool/). Release mapping and access control belong to the release process; see [Frontend Testing / 前端测试](#55.%20What%20evidence%20shows%20a%20frontend%20change%20works%20through%20production%20delivery?%20/%20%E5%93%AA%E4%BA%9B%E8%AF%81%E6%8D%AE%E8%83%BD%E8%AF%81%E6%98%8E%E5%89%8D%E7%AB%AF%E6%94%B9%E5%8A%A8%E5%8F%AF%E7%94%A8%E5%B9%B6%E8%83%BD%E6%AD%A3%E7%A1%AE%E4%BA%A4%E4%BB%98%EF%BC%9F) for built-output browser smoke checks and [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) for the shared release path.
## 43. How does a project pin its package-manager version? / 项目如何固定包管理器版本？

### How does a project pin its package-manager version? / 项目如何固定包管理器版本？

**Core answer / 核心回答：** The package.json packageManager field records the package manager and version expected by a project. Corepack can select a matching version when its shims are installed, but the field does not itself install the manager or guarantee every environment honors it. / package.json 的 packageManager 字段记录项目期望使用的包管理器及版本。安装 Corepack shims 后，Corepack 可选择匹配版本；但该字段本身不会安装包管理器，也不保证每个环境都会遵循它。

~~~json
{
  "packageManager": "pnpm@10.0.0"
}
~~~

Corepack was bundled with Node.js through Node 24, but Node 25 and later no longer distribute it by default. A current project may need to install or provision Corepack separately. Pin and provision the tool through the project’s supported runtime and CI setup. / Corepack 随 Node.js 提供至 Node 24；Node 25 及之后的版本默认不再分发。当前项目可能需要单独安装或供应 Corepack。应通过项目支持的运行时和 CI 配置固定并供应工具。

Sources checked 2026-10-15: [Node.js 25 Corepack documentation](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html) and [Corepack project README](https://github.com/nodejs/corepack#readme). The rest of the build pipeline is in [Build Tools / 构建工具](#42.%20How%20do%20build%20tools%20transform%20modules%20and%20validate%20production%20output?%20/%20%E6%9E%84%E5%BB%BA%E5%B7%A5%E5%85%B7%E5%A6%82%E4%BD%95%E8%BD%AC%E6%8D%A2%E6%A8%A1%E5%9D%97%E5%B9%B6%E9%AA%8C%E8%AF%81%E7%94%9F%E4%BA%A7%E4%BA%A7%E7%89%A9%EF%BC%9F).
## 44. How should I choose a frontend framework for a product? / 如何为产品选择前端框架？

### How should I choose a frontend framework for a product? / 如何为产品选择前端框架？

**Core answer / 核心回答：** Start from the route's rendering, interaction, accessibility, and operational needs, then compare how candidate frameworks express updates and what the team can maintain. Prototype one representative feature and measure its real bottleneck; a virtual DOM label or a standalone benchmark does not predict project fit by itself. / 先从页面的渲染、交互、无障碍和运维需求出发，再比较候选框架如何表达更新以及团队能否长期维护。用一个有代表性的功能做原型，并测量真实瓶颈；虚拟 DOM 这一标签或单项基准测试本身都不能判断项目是否适合。


#### How does reconciliation work, and does a Virtual DOM make an app faster? / React如何协调界面，虚拟DOM是否天然更快？

**Core answer / 核心回答：** React components describe the UI for a particular set of props and state. React compares the next element description with the previous one, then commits the necessary host changes. “Virtual DOM” is a useful shorthand for this model, not a speed guarantee: the cost depends on the component tree, update, browser work, and framework implementation. / React 组件根据当前 props 和 state 描述界面。React 将新的元素描述与之前的结果协调，再提交必要的宿主环境变更。“虚拟 DOM”是这种模型的常见简称，不代表它天然更快；实际成本取决于组件树、更新内容、浏览器工作和框架实现。

##### A practical React model / React中的实用模型

1. **Render / 渲染：** React calls components to calculate the next UI description. Rendering should be pure; concurrent work may be restarted or discarded.
2. **Reconciliation / 协调：** React matches the new description to the previous tree. The exact type, position, and key rules that preserve or reset component state are explained in [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F); they should not be inferred from a generic “virtual DOM” slogan.
3. **Commit / 提交：** React applies the completed changes to the host tree, such as the DOM. Effects run in their documented phase; they are not part of render.

~~~jsx
{items.map(item => <ListItem key={item.id} item={item} />)}
~~~

The reconciler uses heuristics rather than a general-purpose minimum-edit tree algorithm. Treat complexity claims as implementation-specific; the useful question for framework choice is what work a representative update actually causes in the framework and browser.

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

**See also:** [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for element identity and component state; [Next.js / Next.js开发](#50.%20How%20should%20a%20Next.js%20app%20render%20and%20route%20its%20pages?%20/%20Next.js%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%B8%B2%E6%9F%93%E9%A1%B5%E9%9D%A2%E5%B9%B6%E7%BB%84%E7%BB%87%E8%B7%AF%E7%94%B1%EF%BC%9F) for router-specific rendering models.

**Sources checked 2026-10-15:** [React Reconciliation](https://legacy.reactjs.org/docs/reconciliation.html), [Vue Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism), [React: Render and Commit](https://react.dev/learn/render-and-commit), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TypeScript: erased structural types](https://www.typescriptlang.org/docs/handbook/typescript-for-oopers.html#erased-structural-types).
## 45. How does React turn a user action into an updated interface? / React如何把用户操作变成更新后的界面？

### How does React turn a user action into an updated interface? / React如何把用户操作变成更新后的界面？

**Core answer / 核心回答：** A user action reaches a React handler through the browser's event system. The handler requests a state update, but it continues to read the snapshot from its current render. React then renders the next component descriptions, matches them by type, position, and sibling keys, and commits the required host changes. The browser handles the later style, layout, and paint work. This route connects [DOM events / DOM事件](#31.%20DOM%20Manipulation%20and%20Events%20/%20DOM%E6%93%8D%E4%BD%9C%E4%B8%8E%E4%BA%8B%E4%BB%B6), React state, and [browser rendering / 浏览器渲染](#1.%20How%20does%20a%20browser%20turn%20a%20URL%20into%20pixels?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E5%B1%8F%E5%B9%95%E5%83%8F%E7%B4%A0%EF%BC%9F); it does not promise one paint for every setter call. / 用户操作经由浏览器事件系统到达 React 处理器。处理器请求状态更新，但仍读取当前这次 render 的快照。随后 React 重新计算组件描述，按元素类型、位置和兄弟 key 匹配，并提交必要的宿主环境变更。之后的样式、布局和绘制由浏览器处理。这条路线连接 [DOM events / DOM事件](#31.%20DOM%20Manipulation%20and%20Events%20/%20DOM%E6%93%8D%E4%BD%9C%E4%B8%8E%E4%BA%8B%E4%BB%B6)、React state 与[浏览器渲染](#1.%20How%20does%20a%20browser%20turn%20a%20URL%20into%20pixels?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E5%8F%98%E6%88%90%E5%B1%8F%E5%B9%95%E5%83%8F%E7%B4%A0%EF%BC%9F)；它不保证每次调用 setter 都对应一次绘制。

~~~mermaid
flowchart LR
    A[User input event] --> B[Handler requests state update]
    B --> C[Next render reads queued state]
    C --> D[React matches elements and state identity]
    D --> E[Commit necessary host changes]
    E --> F[Browser updates pixels when needed]
    B -. current handler keeps its render snapshot .-> C
~~~


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

**Core answer / 核心回答：** An Error Boundary can show fallback UI for errors in descendant rendering and React lifecycles, with documented exceptions such as event-handler and ordinary async errors. The exact scope, Transition exception, and class example are in [Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？](#46.%20Which%20errors%20can%20a%20React%20Error%20Boundary%20recover%20from?%20/%20React%20Error%20Boundary%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E9%94%99%E8%AF%AF%EF%BC%9F). / Error Boundary 可为后代渲染和 React 生命周期中的错误显示备用 UI，但事件处理器和普通异步错误等情况不在其范围内。完整范围、Transition 例外和类组件示例见[React Error Boundary能恢复哪些错误？](#46.%20Which%20errors%20can%20a%20React%20Error%20Boundary%20recover%20from?%20/%20React%20Error%20Boundary%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E9%94%99%E8%AF%AF%EF%BC%9F).

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

**Core answer / 核心回答：** React Router matches a location to a route, then renders its configured UI. The v6 declarative example, router choices, hosting fallback, and SPA/MPA tradeoffs are in [How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？](#47.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F). / React Router 将地址匹配到路由并渲染对应界面。v6 声明式示例、路由器选择、托管回退及 SPA/MPA 权衡见[React路由如何映射 URL 并选择导航模型？](#47.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F).

#### What is the difference between an SPA and an MPA? / SPA和MPA有什么区别？

**Core answer / 核心回答：** An SPA usually updates route content in one loaded document; an MPA requests another document. Rendering modes can be combined, so evaluate the actual delivery and operating needs. The comparison table and navigation example are in [the React routing question](#47.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F). / SPA 通常在已加载的文档中更新路由内容；MPA 会请求另一个文档。渲染模式可以组合，应结合内容交付和运维需求判断。比较表和路由示例见[React 路由问题](#47.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F).

**Sources checked 2026-10-15:** [React: Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform), [React: Render and Commit](https://react.dev/learn/render-and-commit), [StrictMode](https://react.dev/reference/react/StrictMode), [Component and lifecycle methods](https://react.dev/reference/react/Component), [Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Queueing State Updates](https://react.dev/learn/queueing-a-series-of-state-updates).
## 46. Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？

### Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？

**Core answer / 核心回答：** A React Error Boundary is a class component that displays fallback UI for errors thrown while rendering descendants, in their constructors, or in their React lifecycle methods. It does not catch event-handler errors, ordinary asynchronous callbacks, server-rendering errors, or errors thrown by the boundary itself. One documented exception is an error thrown inside the function passed to the startTransition function returned by useTransition (including a rejected Promise returned by that function). / React Error Boundary 是类组件，可在后代树渲染、构造函数或 React 生命周期方法抛错时显示备用 UI。它不会捕获事件处理器、普通异步回调、服务端渲染或边界自身抛出的错误。一个文档列出的例外是 useTransition 返回的 startTransition 所执行函数抛错（包括该函数返回的 rejected Promise）。

#### Boundary example and limits / 边界示例与范围

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

**See also:** [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for state updates and render/commit; [Advanced React / React进阶](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) for Suspense loading and error states.

**Sources checked 2026-10-15:** [Component and lifecycle methods](https://react.dev/reference/react/Component), [Error Boundary caveats](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary), [useTransition Error Boundary example](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary).
## 47. How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？

### How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？

**Core answer / 核心回答：** React Router matches the current location to a route, while SPA and MPA describe whether navigation updates the current document or requests another one. The choice depends on delivery, interaction, accessibility, hosting, and operations. / React Router 将当前地址匹配到路由；SPA 与 MPA 则描述导航是更新当前文档还是请求另一个文档。选择取决于内容交付、交互、无障碍、托管和运维需求。

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

**See also:** [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for state-driven rendering; [Next.js / Next.js开发](#50.%20How%20should%20a%20Next.js%20app%20render%20and%20route%20its%20pages?%20/%20Next.js%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E6%B8%B2%E6%9F%93%E9%A1%B5%E9%9D%A2%E5%B9%B6%E7%BB%84%E7%BB%87%E8%B7%AF%E7%94%B1%EF%BC%9F) for server/client rendering and framework routing.

**Sources checked 2026-10-15:** [React Router v6 Concepts](https://reactrouter.com/docs/en/v6/start/concepts), [React Router: Picking a Mode](https://reactrouter.com/start/modes).
## 48. How can a React search interface stay responsive as results update? / React搜索界面如何在更新结果时保持响应？

### How can a React search interface stay responsive as results update? / React搜索界面如何在更新结果时保持响应？

**Core answer / 核心回答：** Keep the controlled input urgent, and let React defer the expensive result view or mark a navigation-like update as a Transition. A Suspense boundary can limit loading feedback to the result region. Include all result-changing inputs in the query key; use a separate debounce only when reducing request frequency is a product requirement. The state snapshot and commit path are explained in [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F). / 保持受控输入紧急更新，让 React 延后昂贵的结果视图，或把类似导航的更新标记为 Transition。Suspense 边界可以把加载反馈限制在结果区域。查询键要包含所有影响结果的输入；只有产品需要减少请求频率时才另做 debounce。state 快照与提交路径见[React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F)。

This is the main interaction route: typing requests an urgent input update, while a deferred query value drives a Suspense-enabled result view. `useDeferredValue` schedules rendering; it is not a debounce and does not suppress requests. The [server-state deep question](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F) owns query identity, cache freshness, mutation, and rollback semantics.

#### How do concurrent UI updates and Suspense work? / 并发界面更新与 Suspense 如何工作？

**Core answer / 核心回答：** Keep input state urgent so each keystroke appears immediately; defer expensive result rendering or mark a navigation-like state update as a Transition. React can interrupt and retry that render work so urgent updates get priority. A Suspense boundary gives one part of the screen a fallback while a Suspense-enabled child is not ready. / 输入状态应保持紧急，以便每次按键都立即显示；可以延后昂贵结果区域的渲染，或把类似导航的状态更新标记为 Transition。React 可以中断并重试这部分渲染，让紧急更新优先。Suspense 边界则在支持 Suspense 的子树尚未就绪时，为该区域显示 fallback。

This search panel keeps the text input responsive and places the loading fallback around only the result list. Query-key identity and server-cache freshness are explained in [the server-state deep question](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F). `useSuspenseQuery` is the TanStack Query v5 data source that suspends here; a normal query or fetch started in an Effect does not automatically suspend. The memoized result boundary allows React to skip this child when an urgent parent render leaves `deferredQuery` and `tab` unchanged; without it, the child still renders on each parent input update even though the deferred value is old. It renders again when either deferred prop advances.

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

`useTransition` exposes `isPending` and marks state updates inside `startTransition` as non-urgent; its callback runs immediately, and it cannot control a text input. With an async action, wrap state updates after each `await` in another `startTransition` to mark them as transitions. `useDeferredValue` lets a child keep seeing the previous value while React prepares an interruptible background render. It has no fixed delay and does not suppress network requests, so use an explicit debounce when the goal is fewer requests. Neither API parallelizes JavaScript on another CPU thread or makes a long synchronous calculation faster; use a better algorithm, memoization, or a worker when computation itself blocks. `Suspense` only shows this fallback when its child suspends through a supported source such as `use` with a cached Promise or a Suspense-enabled framework/library. Pair data errors with an [Error Boundary](#46.%20Which%20errors%20can%20a%20React%20Error%20Boundary%20recover%20from?%20/%20React%20Error%20Boundary%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E9%94%99%E8%AF%AF%EF%BC%9F) or use explicit pending/error states; Suspense is not a request error handler. Keep renders pure because React may retry interrupted work.

#### Who owns server data and local UI state? / 服务端数据与本地界面状态由谁管理？

**Core answer / 核心回答：** Keep transient choices and drafts in local state; identify server queries by every result-changing input, give cached data an explicit freshness policy, and reconcile mutations with the server response. The complete query, optimistic-update, rollback-race, and A-to-B identity example is in [How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F). / 将临时选择和草稿保存在本地 state 中；查询键包含所有影响结果的输入，为缓存规定新鲜度，并用服务端响应协调变更。完整的查询、乐观更新、回滚竞态和 A→B 身份示例见[React界面如何维护服务端数据与乐观更新的正确性？](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F).


#### How do I compose components and reusable behavior around an interaction? / 如何围绕交互组合组件与可复用行为？

**Core answer / 核心回答：** Use props and callbacks for direct data flow, Context or a store for shared values, custom Hooks for reusable stateful logic, and refs for narrow imperative actions. Use memoization only when profiling or an identity boundary shows a benefit; keep legacy render-prop and wrapper APIs when they make the contract clearer. / 直接数据流使用 props 与回调，共享值使用 Context 或 store，可复用有状态逻辑使用自定义 Hook，窄范围命令式操作使用 ref。只有性能分析或明确的引用边界证明有收益时才加 memo；当旧的 render-prop 或包装器 API 能更清楚表达契约时，可以继续使用。

##### How can components communicate? / React组件如何通信？

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

##### When should you use memo, useMemo, or useCallback? / 何时使用 memo、useMemo和useCallback？

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

##### What does useRef do? / useRef有什么作用？

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

##### What do forwardRef and useImperativeHandle do? / forwardRef和useImperativeHandle有什么作用？

**Core answer / 核心回答：** In React 18 and earlier, forwardRef lets a component accept and forward a parent's ref; useImperativeHandle can expose a narrow command API. In React 19, a function component can receive ref as a prop, so forwardRef is no longer necessary for new React 19-only components. / React 18 及更早版本中，forwardRef 让组件接收并转发父组件传入的 ref；useImperativeHandle 可暴露范围较小的命令式 API。React 19 的函数组件可以把 ref 作为 prop 接收，因此仅面向 React 19 的新组件不再需要 forwardRef。

~~~jsx
const FancyInput = forwardRef(function FancyInput(props, ref) {
  return <input {...props} ref={ref} className="fancy" />;
});
~~~

Prefer declarative props and callbacks when they express the interaction clearly. Use an imperative ref for cases such as focusing an input or coordinating a third-party widget.

##### What is a custom Hook? / 什么是自定义Hook？

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

##### What are render props and higher-order components? / 什么是 render props 和高阶组件？

**Core answer / 核心回答：** Render props pass a function that chooses what to render from data supplied by a component. A higher-order component takes a component and returns a wrapped component. Both remain useful API shapes in some libraries and legacy code; custom Hooks are another way to share logic, not a universal replacement. / render props 通过函数接收组件提供的数据并决定渲染内容。高阶组件接收一个组件并返回包装后的组件。它们仍适用于某些库 API 和旧代码；自定义 Hook 是共享逻辑的另一种方式，并非对二者的通用替代。

~~~jsx
<MouseTracker render={({ x, y }) => (
  <p>Pointer: {x}, {y}</p>
)} />
~~~

A wrapper component can add authorization or instrumentation, but nested wrappers may make the component tree and prop flow harder to follow. Choose the API that makes ownership and behavior clear.

##### What are common conditional-rendering patterns? / 常见的条件渲染写法有哪些？

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

**See also:** [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for state snapshots and lifecycle context; [React Server State and Optimistic Updates / React服务端状态与乐观更新](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F) for query/cache and mutation rules; [React Error Boundaries / React错误边界](#46.%20Which%20errors%20can%20a%20React%20Error%20Boundary%20recover%20from?%20/%20React%20Error%20Boundary%E8%83%BD%E6%81%A2%E5%A4%8D%E5%93%AA%E4%BA%9B%E9%94%99%E8%AF%AF%EF%BC%9F) for render-failure recovery; [Rendering and Computation Optimization / 渲染与计算优化](#52.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for profiling and memoization limits.

**Sources checked 2026-10-15:** [React: `useTransition`](https://react.dev/reference/react/useTransition), [`useDeferredValue`](https://react.dev/reference/react/useDeferredValue), [React `Suspense`](https://react.dev/reference/react/Suspense), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [React: memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback), [useRef](https://react.dev/reference/react/useRef), [forwardRef](https://react.dev/reference/react/forwardRef), [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [Rules of Hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks), [use](https://react.dev/reference/react/use).
## 49. How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？

### How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？

**Core answer / 核心回答：** Keep transient choices such as the selected row, open dialog, or draft input in local React state. Treat records owned by a server as server state: identify each query by all inputs that affect it, define when cached data is fresh, and invalidate or update affected entries after a mutation. A query cache is a client read model, not the source of truth. / 将选中行、打开的对话框和输入草稿等临时选择保存在 React 本地状态中。服务器拥有的记录属于服务端状态：查询键要包含所有影响结果的输入，缓存需要明确新鲜期，变更后要更新或失效相关缓存。查询缓存是客户端读模型，不是数据的权威来源。

#### Identify ownership, freshness, and mutation effects / 区分数据归属、新鲜度和变更影响

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

The mutation cancels in-flight reads before writing optimistically, saves snapshots for rollback, replaces both cached views with the server response on success, then invalidates them to reconcile other changes. A pending save can disable its button; on error, the snapshot restores the visible list/detail and the UI can show a retry message. Because rollback restores the whole list snapshot, this example requires at most one mutation in flight across the shared list—not merely one save per task. Otherwise A can fail after B succeeds and restore B's old row too. Broader concurrency needs operation-scoped or version-aware reconciliation instead of blindly restoring that snapshot. If the user switches from task A to B while A is loading, the detail key changes from `detail/A` to `detail/B`; A may finish into its own cache entry, but cannot become B's displayed record. Passing the query's `AbortSignal` to `fetch` can also stop obsolete network work when the service consumes it. A manually managed Effect needs its own stale-result guard or cleanup; [the `useWindowSize` Effect example](#What%20is%20a%20custom%20Hook?%20/%20%E4%BB%80%E4%B9%88%E6%98%AF%E8%87%AA%E5%AE%9A%E4%B9%89Hook%EF%BC%9F) shows cleanup, and an Effect fetch by itself does not activate Suspense. See [Advanced TypeScript / TypeScript进阶](#35.%20How%20should%20TypeScript%20handle%20untrusted%20JSON?%20/%20TypeScript%20%E5%BA%94%E5%A6%82%E4%BD%95%E5%A4%84%E7%90%86%E4%B8%8D%E5%8F%AF%E4%BF%A1%20JSON%EF%BC%9F) for validating API JSON before treating it as a `Task`.

**Related task / 相关任务：** The [responsive React search question / React搜索响应问题](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) shows how the result view stays responsive while its query key follows the user's inputs. This page explains the cache identity, freshness, optimistic mutation, rollback, and concurrency rules used by that UI. / [React搜索响应问题](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F)说明结果查询如何跟随用户输入、同时保持界面响应；本文说明该界面所需的缓存身份、新鲜度、乐观变更、回滚与并发规则。

**See also:** [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for state snapshots and the render/commit path.

**Sources checked 2026-10-15:** [React: Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries), [Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys), [Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), [Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation), [Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates), [Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation).
## 50. How should a Next.js app render and route its pages? / Next.js应用应如何渲染页面并组织路由？

### How should a Next.js app render and route its pages? / Next.js应用应如何渲染页面并组织路由？

**Core answer / 核心回答：** Choose the Pages Router or App Router deliberately, then decide per route which work belongs in a request-time server render, reusable static output, a Client Component, or a smaller streamed region. Name the Next.js version when discussing cache defaults: these behaviors have changed across releases. Server-rendered HTML streaming during page navigation is separate from streaming an operation's incremental answer after the page is open; the latter belongs to [Streaming UX / 流式交互](#34.%20How%20should%20a%20UI%20render%20a%20streamed%20answer%20without%20mistaking%20partial%20output%20for%20completion?%20/%20%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%91%88%E7%8E%B0%E6%B5%81%E5%BC%8F%E5%9B%9E%E7%AD%94%E8%80%8C%E4%B8%8D%E6%8A%8A%E9%83%A8%E5%88%86%E5%86%85%E5%AE%B9%E8%AF%AF%E5%88%A4%E4%B8%BA%E5%AE%8C%E6%88%90%EF%BC%9F). / 先明确使用 Pages Router 还是 App Router，再按路由决定哪些工作适合请求时服务端渲染、可复用静态输出、Client Component 或较小的流式区域。说明缓存默认值时要注明 Next.js 版本，因为不同版本的行为发生过变化。页面导航期间流式传送服务端 HTML，与页面打开后流式呈现某次操作的增量回答，是不同层次；后者见 [Streaming UX / 流式交互](#34.%20How%20should%20a%20UI%20render%20a%20streamed%20answer%20without%20mistaking%20partial%20output%20for%20completion?%20/%20%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%91%88%E7%8E%B0%E6%B5%81%E5%BC%8F%E5%9B%9E%E7%AD%94%E8%80%8C%E4%B8%8D%E6%8A%8A%E9%83%A8%E5%88%86%E5%86%85%E5%AE%B9%E8%AF%AF%E5%88%A4%E4%B8%BA%E5%AE%8C%E6%88%90%EF%BC%9F)。


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

If the page awaits `getPosts()` before returning this tree, that request cannot be streamed inside the boundary. Place boundaries around independently useful parts: a boundary that is too high can hold back the whole page, while a boundary around a tiny fragment can create a choppy reveal. A fallback is visible page content, so give it meaningful text. If an update needs an assistive-technology announcement, add the appropriate live-region semantics; that does not move keyboard focus or create interaction behavior. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](#3.%20HTML%20and%20CSS%20Basics%20/%20HTML%20%E4%B8%8E%20CSS%20%E5%9F%BA%E7%A1%80) for the focused keyboard, naming, and error model. A pending fallback also does not make a failed request successful; provide a separate error path.

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

**See also:** [React Routing and Navigation / React路由与导航](#47.%20How%20do%20React%20routes%20map%20URLs%20to%20views,%20and%20when%20is%20SPA%20navigation%20a%20fit?%20/%20React%E8%B7%AF%E7%94%B1%E5%A6%82%E4%BD%95%E6%8A%8A%20URL%20%E6%98%A0%E5%B0%84%E5%88%B0%E8%A7%86%E5%9B%BE%EF%BC%8C%E4%BD%95%E6%97%B6%E9%80%82%E5%90%88%20SPA%20%E5%AF%BC%E8%88%AA%EF%BC%9F) for client navigation and SPA/MPA document models; [React Basics / React基础](#45.%20How%20does%20React%20turn%20a%20user%20action%20into%20an%20updated%20interface?%20/%20React%E5%A6%82%E4%BD%95%E6%8A%8A%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E5%8F%98%E6%88%90%E6%9B%B4%E6%96%B0%E5%90%8E%E7%9A%84%E7%95%8C%E9%9D%A2%EF%BC%9F) for state-driven rendering; [Node.js Fundamentals / Node.js基础](../../engineering-foundations/backend/node-js-fundamentals.md) for server runtime constraints.

**Sources checked 2026-10-15:** [React 19.3 versions and release](https://react.dev/versions), [React `hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot), [React `useEffect`](https://react.dev/reference/react/useEffect), [React `Suspense`](https://react.dev/reference/react/Suspense), [Next.js 16.4.1 App Router migration guide](https://nextjs.org/docs/app/guides/migrating/app-router-migration), [Next.js 16.4.1 Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data), [Pages Router getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props), [Pages Router getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths), [Pages Router Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration), [use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache), [Incremental Static Regeneration](https://nextjs.org/docs/app/guides/incremental-static-regeneration), [Link](https://nextjs.org/docs/app/api-reference/components/link), and [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route).
## 51. Performance Metrics and Analysis / 性能指标与分析

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

**See also:** [Image Lazy Loading / 图片懒加载](#33.%20Image%20Lazy%20Loading%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E5%9B%BE%E7%89%87%E6%87%92%E5%8A%A0%E8%BD%BD) for image loading choices; [Rendering and Computation Optimization / 渲染与计算优化](#52.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96) for React and long-list work.

**Sources checked 2026-10-15:** [PerformancePaintTiming (FP/FCP)](https://developer.mozilla.org/en-US/docs/Web/API/PerformancePaintTiming), [DOMContentLoaded event](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event), [Window load event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event), [Web Vitals](https://web.dev/articles/vitals), [INP](https://web.dev/articles/inp), [LCP](https://web.dev/articles/lcp), [CLS](https://web.dev/articles/cls), [Lab and Field Data Differences](https://web.dev/articles/lab-and-field-data-differences), [HTTP Caching (RFC 9111)](https://www.rfc-editor.org/rfc/rfc9111.html), [ETag (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html#name-etag), [Beacon specification](https://w3c.github.io/beacon/).
## 52. Rendering and Computation Optimization / 渲染与计算优化

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

**See also:** [Browser HTML and CSS / 浏览器中的HTML与CSS](#7.%20Why%20can%20a%20CSS%20change%20trigger%20layout,%20paint,%20or%20compositing%20work?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%20CSS%20%E6%94%B9%E5%8A%A8%E4%BC%9A%E8%A7%A6%E5%8F%91%E5%B8%83%E5%B1%80%E3%80%81%E7%BB%98%E5%88%B6%E6%88%96%E5%90%88%E6%88%90%E5%B7%A5%E4%BD%9C%EF%BC%9F) for rendering stages; [Performance Metrics and Analysis / 性能指标与分析](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for measurement.

**Sources checked 2026-10-15:** [React: memo](https://react.dev/reference/react/memo), [React: useMemo](https://react.dev/reference/react/useMemo), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TanStack Virtual](https://tanstack.com/virtual/latest/docs/introduction), [CSS Will Change Module](https://www.w3.org/TR/css-will-change-1/), [MDN background-position](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-position), [HTTP/2 RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing).
## 53. When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？

### When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？

**Core answer / 核心回答：** Use Lodash when its documented path, collection, or timing contract removes repeated edge-case code. For a simple known shape, prefer the native operation when it expresses the same behavior more clearly; compare the exact semantics and installed version before substituting. This page is a method lookup, not a claim that one option is always smaller or faster. / Lodash 的路径、集合或定时语义能减少重复的边界处理时可使用它。对象结构简单明确时，如果原生操作能更清晰表达相同行为，就优先考虑原生 API；替换前要核对具体语义和安装版本。本文用于查找方法，不表示某种选择总是更小或更快。

#### Common utilities / 常用工具

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

**See also:** [Modern JavaScript Features / 现代JavaScript特性](#18.%20How%20do%20edition%20and%20runtime%20support%20affect%20JavaScript%20feature%20use?%20/%20%E8%AF%AD%E8%A8%80%E7%89%88%E6%9C%AC%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6%E6%94%AF%E6%8C%81%E5%A6%82%E4%BD%95%E5%BD%B1%E5%93%8D%20JavaScript%20%E7%89%B9%E6%80%A7%E7%9A%84%E4%BD%BF%E7%94%A8%EF%BC%9F) for native alternatives such as structuredClone; [Performance Metrics and Analysis / 性能指标与分析](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for choosing debounce or throttle by workload.

**Sources checked 2026-10-15:** [Lodash 4.17.21 API source, including debounce and throttle](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md), [Array.prototype.flat()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat), [Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing).
## 54. When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？

### When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？

**Core answer / 核心回答：** Use ahooks when an existing helper matches the interaction's state, lifecycle, request, or list contract and the installed package version. A helper still follows React's render and Effect rules; it does not replace decisions about data ownership, cache freshness, transport cancellation, or item identity. The APIs here follow documentation checked on 2026-10-15. / 当现有 ahooks 工具符合交互的状态、生命周期、请求或列表语义，并且与项目安装版本一致时再使用。工具仍遵守 React 的 render 和 Effect 规则；它不会替代对数据归属、缓存新鲜度、传输取消或列表项身份的判断。此处 API 依据 2026-10-15 核对的文档。

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

Variable-height rows need the measurement behavior supported by the installed version. See [Rendering and Computation Optimization / 渲染与计算优化](#52.%20Rendering%20and%20Computation%20Optimization%20/%20%E6%B8%B2%E6%9F%93%E4%B8%8E%E8%AE%A1%E7%AE%97%E4%BC%98%E5%8C%96).

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

**See also:** [Advanced React / React进阶](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) for Hook rules, Effect cleanup, deferred rendering, and Suspense; [React Server State and Optimistic Updates / React服务端状态与乐观更新](#49.%20How%20should%20a%20React%20UI%20keep%20server%20data%20and%20optimistic%20updates%20correct?%20/%20React%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E7%BB%B4%E6%8A%A4%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%95%B0%E6%8D%AE%E4%B8%8E%E4%B9%90%E8%A7%82%E6%9B%B4%E6%96%B0%E7%9A%84%E6%AD%A3%E7%A1%AE%E6%80%A7%EF%BC%9F) for query-cache and mutation rules; [Performance Metrics and Analysis / 性能指标与分析](#51.%20Performance%20Metrics%20and%20Analysis%20/%20%E6%80%A7%E8%83%BD%E6%8C%87%E6%A0%87%E4%B8%8E%E5%88%86%E6%9E%90) for debounce and throttle tradeoffs.

**Sources checked 2026-10-15:** [ahooks useRequest](https://ahooks.js.org/hooks/use-request), [ahooks v3.10.0 useRequest implementation](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/Fetch.ts), [ahooks v2 to v3 upgrade notes](https://ahooks.js.org/guide/upgrade/), [ahooks 2.6.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v2.6.0/packages/hooks/src/useVirtualList/index.ts), [ahooks 3.10.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useVirtualList/index.ts), [usePagination](https://ahooks.js.org/hooks/use-pagination), [useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll), [useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state), [useLatest](https://ahooks.js.org/hooks/use-latest), [useMemoizedFn](https://ahooks.js.org/hooks/use-memoized-fn), [useVirtualList](https://ahooks.js.org/hooks/use-virtual-list), [useCreation](https://ahooks.js.org/hooks/use-creation), [useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn), [useThrottle](https://ahooks.js.org/hooks/use-throttle), [useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn), [useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list), [useUnmount](https://ahooks.js.org/hooks/use-unmount), [React StrictMode](https://react.dev/reference/react/StrictMode).
## 55. What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？

### What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？

**Core answer / 核心回答：** Build the production output, run a critical browser journey against that output on a production-like server, then promote the exact artifact that passed. A development server alone does not exercise emitted assets or deployment paths. The general risk-to-test-boundary principle belongs to [Software Testing Strategy / 软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md); the tool choices for local logic and component behavior are outlined below. / 构建生产产物，在接近生产环境的服务上用该产物运行关键浏览器流程，然后晋级同一份通过检查的产物。单独运行开发服务器无法覆盖实际生成的资源或部署路径。通用的风险与测试边界原则见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)；本地逻辑和组件行为的工具选择见下文。

#### How should frontend tests be divided? / 前端测试如何分层？

**Core answer / 核心回答：** Use a unit test for isolated logic, a component integration test for user-visible wiring, and a browser test when real navigation, persistence, browser behavior, emitted assets, or service wiring is part of the risk. Keep the feedback loop cheap where it can provide reliable evidence. / 隔离逻辑用单元测试，验证用户可见的组件连接用集成测试；当风险涉及真实导航、持久化、浏览器行为、生成资源或服务连接时使用浏览器测试。能可靠提供证据时，优先保持反馈成本较低。

| Layer | Useful for | Example tools |
|---|---|---|
| Unit | Pure functions and isolated behavior | Jest, Vitest |
| Integration | Components, hooks, context, and API boundaries together | React Testing Library with Jest or Vitest |
| End-to-end | Browser navigation, persistence, and critical user journeys | Playwright, Cypress |

Keep browser tests for behavior that depends on the real browser or application wiring. A test pyramid is a planning aid; a project's distribution should follow its actual risks and feedback costs.

#### Jest fundamentals / Jest基础

Use Jest when the risk can be reproduced around logic, state, or a dependency boundary. A test that starts asynchronous work must return or await the Promise that contains its assertions. Place the mock at the dependency and assert the behavior of the caller. [How a Jest test verifies asynchronous behavior / Jest 怎样验证异步行为](#56.%20How%20can%20a%20Jest%20test%20verify%20behavior%20across%20an%20asynchronous%20boundary?%20/%20Jest%20%E6%80%8E%E6%A0%B7%E9%AA%8C%E8%AF%81%E8%B7%A8%E5%BC%82%E6%AD%A5%E8%BE%B9%E7%95%8C%E7%9A%84%E8%A1%8C%E4%B8%BA%EF%BC%9F) contains the complete async, lifecycle, matcher, CommonJS and native ESM examples.

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

#### Release checks / 发布检查

CI should connect fast source checks to the exact production output. A small frontend release path is:

**核心原则 / Core idea：** 先完成类型、单元和组件检查，再生成生产构建；用接近生产的服务运行这份构建产物，执行关键浏览器流程，最后晋级同一份已验证产物，避免重新构建后发布了另一份代码。HMR 只验证开发热更新链路，不能证明生产资源路径、分块或发布产物正常；Vite preview 可以本地预览刚生成的 `dist`，但官方定位不是生产服务器。Source map 应关联到具体发布版本并受控上传；`hidden` 只隐藏源码映射注释，不阻止他人直接访问映射文件。

~~~text
lockfile install -> type check -> unit/component tests -> production build
  -> serve the built output -> one critical browser smoke -> retain/promote that output
~~~

For example, a project can run `npm run typecheck`, `npm run test:ci`, and `npm run build`, then `npx playwright test tests/release-smoke.spec.ts`. Configure Playwright's `webServer.command` to start `npm run preview` (or the framework's built-output server) after the build so this browser test sees emitted assets rather than the HMR server; script names are project-specific.

Type checks catch static contract errors; unit and component tests catch local logic and UI wiring; a production build catches transforms, asset emission, and chunk or base-path issues that a dev server may not exercise. Then serve the generated output with a production-like static server and run one browser test for a critical journey, such as opening search, submitting a query, and seeing results. A Playwright `webServer` can start the local artifact server for the test; with Vite, `vite preview` serves the just-built `dist` locally for this check, but is not a production server. Promote the tested output rather than rebuilding it for release.

Use browser checks where real routing, asset URLs, browser behavior, or app/service wiring matters. A passing HMR session proves the development loop works; it does not prove production chunks load from the deployed base path or that the published artifact works. Source maps can translate minified error locations back to original source when tied to a release and uploaded to a controlled error-reporting system. A hidden map removes the source-map comment, not the file or access risk; do not leave private maps at a public asset URL. The shared [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) note owns artifact promotion, runtime secrets, and rollout gates.

**See also:** [Advanced React / React进阶](#48.%20How%20can%20a%20React%20search%20interface%20stay%20responsive%20as%20results%20update?%20/%20React%E6%90%9C%E7%B4%A2%E7%95%8C%E9%9D%A2%E5%A6%82%E4%BD%95%E5%9C%A8%E6%9B%B4%E6%96%B0%E7%BB%93%E6%9E%9C%E6%97%B6%E4%BF%9D%E6%8C%81%E5%93%8D%E5%BA%94%EF%BC%9F) for custom Hook semantics; [Git Essentials / Git基础](../../engineering-foundations/version-control/git-essentials.md) for how tests fit into review and CI.

**Sources checked 2026-10-15:** [Jest Mock Functions](https://jestjs.io/docs/mock-functions), [Jest Object and Mock Lifecycle](https://jestjs.io/docs/jest-object), [Jest ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules), [React Testing Library API](https://testing-library.com/docs/react-testing-library/api/), [Testing Library Queries](https://testing-library.com/docs/queries/about/), [user-event](https://testing-library.com/docs/user-event/intro/), [Testing Library Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/), [Vite static deployment](https://vite.dev/guide/static-deploy.html), [Playwright web server](https://playwright.dev/docs/test-webserver).
## 56. How can a Jest test verify behavior across an asynchronous boundary? / Jest 怎样验证跨异步边界的行为？

### How can a Jest test verify behavior across an asynchronous boundary? / Jest 怎样验证跨异步边界的行为？

Wait for the Promise that carries the assertion, give the code under test an explicit dependency boundary, and assert what the code does with the result. Set up and restore only the resources the test owns. Module mocking depends on the test's module system. / 等待承载断言的 Promise，在被测代码的依赖边界安排模拟，并断言被测代码如何处理结果。测试只负责准备和恢复自己拥有的资源。模块模拟方式取决于测试使用的模块系统。

**Key terms / 关键术语** · observable behavior / 可观察行为 · dependency boundary / 依赖边界 · test lifecycle / 测试生命周期 · module mock / 模块模拟

#### Suites and cases / 测试套件与用例

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

#### Async tests / 异步测试

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

#### Setup and cleanup / 准备与清理

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

#### Mock functions and spies / Mock 函数与 spy

##### jest.fn

jest.fn creates a mock function whose calls and results can be inspected.

~~~javascript
const callback = jest.fn();
callback('saved');

expect(callback).toHaveBeenCalledWith('saved');
expect(callback).toHaveBeenCalledTimes(1);
~~~

##### jest.mock in a CommonJS/transformed setup

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

##### Native ESM modules

Native ESM evaluates static imports before the test body, so the CommonJS-style hoisting example does not apply. Jest's documentation provides jest.unstable_mockModule followed by dynamic import for ESM mocking. The API name is marked unstable; check the Jest version and runtime configuration.

~~~javascript
import { jest } from '@jest/globals';

jest.unstable_mockModule('./api.js', () => ({
  fetchUser: jest.fn(),
}));

const { fetchUser } = await import('./api.js');
~~~

##### jest.spyOn

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

#### Common matchers / 常见 matcher

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

#### Coverage / 覆盖率

Run Jest with the project’s configured coverage option, commonly --coverage. Coverage reports which statements, branches, functions, and lines ran; a high percentage does not prove that assertions check meaningful behavior or edge cases.

#### References / 参考资料

- [Jest 30.0 documentation](https://jestjs.io/docs/30.0/getting-started)
- [Jest: ECMAScript Modules](https://jestjs.io/docs/30.0/ecmascript-modules)
- [Jest: The Jest Object](https://jestjs.io/docs/30.0/jest-object)
- [Jest: Mock Functions](https://jestjs.io/docs/30.0/mock-functions)
- [Frontend Testing / 前端测试](#55.%20What%20evidence%20shows%20a%20frontend%20change%20works%20through%20production%20delivery?%20/%20%E5%93%AA%E4%BA%9B%E8%AF%81%E6%8D%AE%E8%83%BD%E8%AF%81%E6%98%8E%E5%89%8D%E7%AB%AF%E6%94%B9%E5%8A%A8%E5%8F%AF%E7%94%A8%E5%B9%B6%E8%83%BD%E6%AD%A3%E7%A1%AE%E4%BA%A4%E4%BB%98%EF%BC%9F)
