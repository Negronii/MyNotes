
# 0. Catalogue

### 1. Browser Basics
   - 1.1 Browser Core Components & Navigation Flow

### 2. HTML & CSS
   - 2.1 HTML & CSS Basics
   - 2.2 Box Model and BFC
   - 2.3 Flex & Grid Layout
   - 2.4 Browser - HTML & CSS Part
   - 2.5 DOM Properties
   - 2.6 CSS Interview Questions
   - 2.7 CSS Position, Display, and Animations

### 3. JavaScript Fundamentals
   - 3.1 Javascript Basics
   - 3.2 Javascript Types
   - 3.3 Map & Set in JS
   - 3.4 Memory in JS, WeakMap and WeakSet
   - 3.5 Array in JS
   - 3.6 ES6 New Methods
   - 3.7 Other JS
   - 3.8 Modern JavaScript Features

### 4. Advanced JavaScript
   - 4.1 Object, Function, and Prototype
   - 4.2 Scope & Closure
   - 4.3 Asynchronous JavaScript
   - 4.4 Iterators and Generators
   - 4.5 Error Handling

### 5. DOM & Browser APIs
   - 5.1 DOM Manipulation and Events
   - 5.2 Browser Storage and Communication
   - 5.3 Image Lazy Loading

### 6. TypeScript
   - 6.1 Advanced TypeScript

### 7. Event Loop & Runtime
   - 7.1 Event Loop
   - 7.2 Node.js Fundamentals
   - 7.3 Build Tools

### 8. Networking & Security
   - 8.1 HTTP Protocols and WebSockets
   - 8.2 Web Security and Authentication

### 9. React & Frameworks
   - 9.1 Virtual DOM and Framework Selection
   - 9.2 React Basics
   - 9.3 Advanced React
   - 9.4 Next.js

### 10. Data Structures & Algorithms
   - 10.1 Algorithms and Complexity
   - 10.2 Core Data Structures
   - 10.3 Practical Data Structure Implementations

### 11. Performance Optimization
   - 11.1 Performance Metrics and Analysis
   - 11.2 Rendering and Computation Optimization

### 12. Architecture & Design Patterns
   - 12.1 Software Design Principles
   - 12.2 Design Patterns in Practice

### 13. Libraries
   - 13.1 Lodash
   - 13.2 ahooks

### 14. Professional Skills
   - 14.1 Interview Tips
   - 14.2 Agile and Scrum

### 15. Frontend Testing
   - 15.1 Frontend Testing

### 16. Git & Version Control
   - 16.1 Git Essentials

# 1. Browser


## 1.1 Browser Basics

Two interview questions this note prepares you for:

1. **What are the major components of a browser, and what do they do?**
2. **What happens when you type a URL and press Enter?** — the single most-asked frontend interview question.

Along the way it covers the follow-ups most candidates hit next: why `<script>` blocks HTML parsing, reflow vs. paint vs. composite, and how to optimize the critical rendering path.

---

### What are the major components of a modern browser?

**Headline (30s):** A browser is four cooperating subsystems: a **rendering engine** (parses HTML/CSS into a render tree and paints pixels), a **JavaScript engine** (executes JS, manages async with the event loop), a **networking layer** (fetches resources, enforces TLS/CORS/cache), and **storage** (cookies, localStorage, sessionStorage, IndexedDB, the Cache API for service workers).

**Why it's asked:** The interviewer wants to hear that you have a mental model of where work happens. Candidates who can't separate "rendering" from "JS execution" tend to write code that surprises them later (layout thrashing, stale caches, blocking scripts).

#### Rendering engine

- **Engines**: Blink (Chrome, Edge), WebKit (Safari), Gecko (Firefox).
- **Critical tasks**:
  - Parse HTML/CSS → DOM / CSSOM (reentrant parsing handles malformed HTML).
  - Combine DOM + CSSOM into the **render tree**, excluding non-visual nodes (`<script>`, `<meta>`, `display: none`).
  - **Layout** (compute position/size) → **paint** (fill pixels) → **composite** (layer the painted parts).
- Illustrative: `display: none` removes an element from the render tree; `visibility: hidden` keeps it but hides the pixels.

#### JavaScript engine

- **Runtimes**: V8 (Chrome, Node), SpiderMonkey (Firefox), JavaScriptCore (Safari).
- **Key pieces**:
  - **JIT compilation** — JS compiled to machine code at runtime.
  - **Event loop + callback queue** — schedules async work (`setTimeout`, promises, I/O). See [`7.1 Event Loop`](./7.1%20Event%20Loop.md).
  - **Memory heap + call stack** — object allocation and function execution.

#### Networking layer

- **HTTP/2 multiplexing** — parallel requests over one TCP connection.
- **HSTS** forces HTTPS; **CORS** preflights validate cross-origin requests.
- **Cache directives** — `Cache-Control`, `ETag`. See [`8.1 HTTP Protocols and WebSockets`](./8.1%20HTTP%20Protocols%20and%20WebSockets.md).

#### Storage

- **cookies** (sent on every request), **localStorage** (persistent, ~5MB), **sessionStorage** (per-tab, cleared on tab close), **IndexedDB** (transactional NoSQL for large data), **Cache API** via service workers (offline-first). See [`5.2 Browser Storage and Communication`](./5.2%20Browser%20Storage%20and%20Communication.md).

**See also:** [`7.1 Event Loop`](./7.1%20Event%20Loop.md), [`5.2 Browser Storage and Communication`](./5.2%20Browser%20Storage%20and%20Communication.md), [`8.1 HTTP Protocols and WebSockets`](./8.1%20HTTP%20Protocols%20and%20WebSockets.md).

---

### What happens when you type a URL and press Enter?

**Headline (30s):** The browser resolves the domain via DNS, opens a TCP connection (plus TLS for HTTPS), sends an HTTP request, and streams the response back. As HTML arrives it builds the DOM; as CSS arrives it builds the CSSOM. The two merge into a render tree, which is laid out, painted into layers, and composited to the screen. JavaScript execution and network fetches happen throughout.

**Why it's asked:** This is the "show me your whole mental model in one question" probe. Interviewers want to hear the three big phases (fetch → parse → render) and at least one intelligent follow-up-worthy detail per phase.

#### Phase 1 — Resource fetching

- **DNS lookup** — browser cache → OS cache → ISP's recursive resolver. Preload with `<link rel="dns-prefetch">`.
- **TCP handshake** — 3-way (SYN, SYN-ACK, ACK). HTTPS adds a TLS handshake (client/server hello, key exchange).
- **HTTP/3** uses **QUIC** over UDP to eliminate head-of-line blocking.

#### Phase 2 — Parsing and the critical rendering path

1. **DOM construction**: bytes → characters → tokens → nodes → DOM tree.
2. **CSSOM construction**: CSS rules are cascaded into a CSSOM tree for style computation.
3. **Render tree**: DOM + CSSOM, minus non-rendered nodes.

**Gotcha — the render-blocking trap:** CSS blocks rendering (the browser won't paint until the CSSOM is ready, or you get FOUC). A synchronous `<script>` blocks **both** parsing and rendering, because the script could `document.write` or mutate the DOM before more HTML is parsed.

#### Phase 3 — Layout, paint, composite

- **Layout (reflow)** — compute exact position/size (`%` → pixels). Triggered by resize, font changes, DOM mutation, and *reading* geometry (like `offsetHeight`) after a write.
- **Paint** — produce paint records for backgrounds, text, borders, shadows.
- **Composite** — merge layers in the correct stacking order. **GPU acceleration** kicks in for layers with `transform`, `opacity`, or `will-change`.

**Follow-up — "Is it fetch, then parse, then render, strictly in order?"** No. The browser streams: it starts parsing before all HTML arrives, kicks off speculative fetches for `<img>`/`<script>`/`<link>` it sees early, and paints incrementally. The three phases overlap in time.

**See also:** [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md), [`8.1 HTTP Protocols and WebSockets`](./8.1%20HTTP%20Protocols%20and%20WebSockets.md).

---

### Why does a `<script>` tag block HTML parsing? What do `async` and `defer` change?

**Headline (30s):** A plain `<script>` pauses parsing because the script might call `document.write` or mutate the DOM the parser is still building. `defer` keeps the script in document order but waits until parsing is done (runs before `DOMContentLoaded`). `async` runs as soon as the script is downloaded, regardless of parser state or document order.

**How it works:**

| Attribute | Downloaded | Executed | Blocks parser? | Order preserved? |
|---|---|---|---|---|
| none (default) | inline with parser | immediately | yes | yes |
| `defer` | in parallel | after parsing | no | yes |
| `async` | in parallel | when ready | no | **no** |

**Gotcha — "async is always faster":** Not for scripts that depend on each other. `async` runs in download-completion order, so a library and its consumer can execute in the wrong sequence. Use `defer` when order matters.

**See also:** [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for placement strategy and more `<script>` gotchas.

---

### Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?

**Headline (30s):** Changing geometry (width, position, DOM insertion) causes **reflow** → repaint → composite. Changing non-geometric visuals (color, background) skips reflow but still repaints. Changing **transform** or **opacity** only touches compositing and can run on the GPU — the cheapest path.

**Cost ladder (cheap → expensive):**

1. **Composite only** — `transform`, `opacity` on a composited layer.
2. **Paint + composite** — `background-color`, `visibility`, `color`.
3. **Layout + paint + composite** — `width`, `height`, `top`, `left`, adding/removing DOM, font-size changes.

**Gotcha — layout thrashing:** Reading a geometry property (`offsetHeight`, `getBoundingClientRect`) right after a write forces a **synchronous** layout — the browser must flush pending style/layout work before it can answer. In a loop, this goes quadratic. Batch your reads before your writes, or use FastDOM / `requestAnimationFrame`.

```javascript
// bad — 100 synchronous layouts
for (const el of items) {
  el.style.width = el.offsetWidth + 10 + 'px';
}

// good — 1 layout, 100 writes
const widths = items.map(el => el.offsetWidth);
items.forEach((el, i) => { el.style.width = widths[i] + 10 + 'px'; });
```

**See also:** [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for deeper triggers and optimization tactics, [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md).

---

### How do you optimize the critical rendering path?

**Headline (30s):** Three levers: cut render-blocking resources (inline critical CSS, `defer`/`async` JS), start network work earlier (`preconnect`, `dns-prefetch`, lazy-load offscreen images), and keep runtime cheap (debounce scroll handlers, `requestAnimationFrame` for animations, avoid layout thrashing).

**Tactics:**

- **Render-blocking mitigation** — inline critical CSS; defer non-critical JS; use `content-visibility: auto` to skip offscreen rendering.
- **Network** — `<link rel="preconnect">` for early TCP/TLS; `loading="lazy"` on images; modern formats (WebP, AVIF); HTTP/2 or HTTP/3.
- **Runtime** — debounce scroll/resize handlers; use `requestAnimationFrame` for visual updates; use `transform`/`opacity` over `top`/`left`.
- **SSR + hydration** — serve HTML first, let client JS attach listeners on top (as in React hydration).
- **Speculative parsing** — modern browsers pre-scan HTML for resources to start downloads even while a script is blocking the main parser. You don't call this directly, but it's worth knowing the name.

**See also:** [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md), [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md), [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md).

# 2. HTML & CSS


## 2.1 HTML & CSS Basics

A grab-bag reference for five CSS foundations that show up constantly in interviews: units, selectors/specificity, responsive techniques, inheritance, and text-overflow tricks. Reach for this when you need to refresh the vocabulary — for mechanism-heavy deep dives, cross-links are at the end of each section.

### CSS Units — which to use when

| Unit | Relative to | Use for | Avoid for |
|---|---|---|---|
| `px` | physical pixels | borders, 1-off precise control | body text, layout (accessibility) |
| `%` | parent | widths in grid layouts | nesting widths (unpredictable overflow) |
| `em` | parent `font-size` (or own, for non-`font-size`) | spacing relative to text | deep nesting (compounds) |
| `rem` | root `font-size` | scalable UIs, most typography | fine-grained per-component control |
| `vw` / `vh` | viewport | hero sections, fullscreen elements | full-width inside scrollable pages |
| `dvh` | viewport **minus** mobile UI | mobile hero / full-height on phones | where you need static viewport height |
| `vmin` / `vmax` | smaller / larger viewport dim | keeping elements square across orientations | anything that needs a single axis |

Usage notes:

- **`px`** — precise but not accessibility-friendly at larger zoom levels.
- **`%`** — context-dependent (`width: 50%` = 50% of parent). Nesting `%` widths leads to unexpected overflows.
- **`em`** — relative to parent `font-size`; compounds in nested lists (`1.2em` inside `1.2em` is `1.44em`).
- **`rem`** — root-relative. Setting `html { font-size: 62.5%; }` makes `1rem = 10px` while still respecting user preferences.
- **`100vw`** includes the scrollbar on most desktop browsers — use `width: 100%` inside a body-width container to avoid horizontal overflow.
- **`vh`** doesn't shrink when the mobile browser's address bar shows/hides. Use `dvh` for true full-viewport height on mobile.
- **`vmin` / `vmax`** — `50vmin` always references the smaller dimension, useful for square elements that adapt to orientation.

### CSS Selectors — specificity and performance

#### Specificity hierarchy (highest to lowest)

1. **Inline styles** (`style="..."`)
2. **IDs** (`#id`)
3. **Classes, attributes, pseudo-classes** (`.class`, `[type="text"]`, `:hover`)
4. **Elements, pseudo-elements** (`div`, `::before`)

Specificity is calculated as a tuple `(inline, id, class, element)` and compared left-to-right: `(0, 1, 0, 0)` > `(0, 0, 2, 0)` even if the right side has more selectors. The universal selector (`*`) and combinators (`>`, `+`, `~`) carry zero specificity.

**Specificity battle example:**

```css
/* Specificity: (0, 1, 1, 0) — wins, because ID weight dominates */
##sidebar .menu-item { color: red; }

/* Specificity: (0, 0, 2, 0) — loses, even with more classes */
.menu .menu-item.active { color: blue; }
```

More classes don't overcome a single ID — the `(0, 1, x, x)` tuple always beats any `(0, 0, y, z)`.

**`:not()` quirk:** `:not()` itself adds no specificity, but its argument does. `div:not(.sidebar)` is `(0, 0, 1, 1)` (element + class).

#### Performance and maintainability tactics

- **Attribute selectors** — `[data-state="active"]` lets CSS react to JS state without class juggling.
- **BEM** (`.block__element--modifier`) — flat specificity, trivially overridable by a more specific class.
- **Cascade layers (`@layer`)** — group styles (`@layer base, components, utilities;`) so an author never has to win a specificity war; later layers always beat earlier ones, regardless of selector weight.
- **CSS-in-JS** (styled-components, Emotion) — generates unique class names, sidestepping the specificity game entirely.
- **Critical CSS** — inline selectors for above-the-fold content (`body > .header`) to paint faster.

### Responsive design beyond media queries

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

**See also:** [`2.3 Flex & Grid Layout`](./2.3%20Flex%20%26%20Grid%20Layout.md) for the full Grid / Flexbox reference.

### Inherited CSS properties

Some properties cascade to children by default; most do not. Knowing the short list saves you from reaching for `inherit` unnecessarily.

**Inherited by default:**

- **Font** — `font-family`, `font-size`, `font-style`, `font-weight`, `line-height`
- **Text formatting** — `text-align`, `text-indent`, `text-transform`, `text-decoration`, `text-shadow`
- **Spacing** — `letter-spacing`, `word-spacing`
- **Visibility** — `visibility`

Most layout / box-model properties (`margin`, `padding`, `border`, `width`, `height`, `display`, `position`) do **not** inherit — you'd never want them to.

### Truncating text with ellipsis

#### Single-line truncation

```css
.box {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100px;
}
```

All three properties are needed: `nowrap` keeps text on one line, `overflow: hidden` hides the spill, `text-overflow: ellipsis` paints the `…`.

#### Multi-line truncation

```css
.box {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  width: 100px;
}
```

Uses the old `-webkit-box` layout, but is very widely supported (Chromium, Safari, modern Firefox). For pure-spec alternatives, `line-clamp` is now in CSS Overflow Module Level 4 — ship when browser support matures.

## 2.2 Box Model and BFC

Interview questions this note prepares you for:

1. **What is the CSS box model?**
2. **Content-box vs border-box — which should you use, and why?**
3. **What is a Block Formatting Context (BFC), and what triggers one?**
4. **How do you fix vertical margin collapse?**
5. **How do you contain floating children so the parent doesn't collapse?**

### What is the CSS box model?

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

### Content-box vs border-box — which should you use?

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

### What is a Block Formatting Context, and what triggers one?

**Headline (30s):** A Block Formatting Context (BFC) is an isolated layout region where internal elements don't interact with elements outside it. Inside a BFC: block boxes stack vertically, floats don't escape, adjacent margins collapse *with each other* but not across the BFC boundary, and the BFC's height grows to contain any floated children. You trigger one by setting certain properties on a container — the most common is `overflow: hidden` or `display: flow-root`.

**Rules that apply inside a BFC:**

- Block-level boxes stack vertically along the block axis.
- Floated children do **not** overlap the BFC's boundary.
- The BFC's height adjusts to include any floated children (float no longer collapses the parent).
- Vertical margin collapse occurs between adjacent siblings *inside* the BFC, but never crosses the BFC boundary.
- The BFC is a containing block for absolutely positioned descendants.

**How to create a BFC** (any of these on the container):

- `overflow: hidden` / `auto` / `scroll` (anything other than `visible`)
- `display: flow-root` — the "modern, side-effect-free" trigger (no clipping, no scroll)
- `display: flex` / `grid` / `inline-block` / `table-cell`
- `position: absolute` / `fixed`
- `float: left` / `right` (but that makes the container itself float — rarely what you want)

**Gotcha — "`overflow: hidden` can clip your content":** It triggers a BFC, yes, but it also crops anything that overflows. If you need the BFC behavior without clipping, use `display: flow-root` instead.

### How do you fix vertical margin collapse?

**Headline (30s):** Adjacent block siblings' vertical margins collapse into the larger of the two — so two boxes with `margin: 50px` each don't produce a 100px gap, they produce a 50px gap. To prevent collapse between boxes, wrap one of them in a container that creates a new BFC; margins never collapse across a BFC boundary.

**Before** (margin collapse strikes):

```html
<section>box-one</section>
<section>box-two</section>
```

```css
section { margin: 50px; }
/* Gap between sections: 50px (collapsed), not 100px */
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
.bfc { display: flow-root; } /* or overflow: hidden */
/* Gap is now the full 100px */
```

**Gotcha — padding on the parent doesn't help if the parent itself isn't a BFC:** A top margin on the first child will "escape" through a non-BFC parent and collapse with the parent's own top margin. Either add padding/border to the parent, or make it a BFC.

### How do you contain floating children so the parent doesn't collapse?

**Headline (30s):** When a parent contains only floated children, its height collapses to zero because floats are removed from the normal flow. Fix by making the parent a BFC (the clean modern way) or by using a clearfix pseudo-element (the legacy way).

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

Both make the parent's height include the floated children. Prefer `flow-root` in new code.

**See also:** [`2.6 CSS Interview Questions`](./2.6%20CSS%20Interview%20Questions.md) for more clear-floats patterns and layout interview scenarios.

## 2.3 Flex & Grid Layout

Reach for this when you need to remember the property names and what each one does. For "how should I approach this layout?" style interview answers, the patterns live in [`2.6 CSS Interview Questions`](./2.6%20CSS%20Interview%20Questions.md).

Rule of thumb: **Flexbox for 1D** (rows *or* columns), **Grid for 2D** (rows *and* columns). In practice they compose — a grid item can itself be a flex container.

### Flexbox

`display: flex` (or `inline-flex`) turns an element into a **flex container**; its direct children become **flex items**. Flex items are laid out along a *main axis* (controlled by `flex-direction`) and a perpendicular *cross axis*.

#### Container properties

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

#### Item properties

| Property | What it controls |
|---|---|
| `flex-grow` | share of *extra* space (unitless proportion) |
| `flex-shrink` | share of *deficit* space when items don't fit |
| `flex-basis` | starting size before grow/shrink (length or `auto`) |
| `flex` | shorthand: `flex: <grow> <shrink> <basis>` |
| `align-self` | override `align-items` for one item |
| `order` | reorder items visually (without changing DOM order) |

#### Common flexbox patterns

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

### CSS Grid

`display: grid` (or `inline-grid`) creates a **grid container**. Grids have explicit **tracks** (rows and columns), **lines** (between tracks), **cells** (single row × column), and **areas** (named regions spanning multiple cells).

#### Container properties

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

#### Item properties

| Property | What it controls |
|---|---|
| `grid-column-start` / `grid-column-end` | column span |
| `grid-row-start` / `grid-row-end` | row span |
| `grid-column` / `grid-row` | shorthand (`grid-column: 1 / 3`) |
| `grid-area` | name this item, or shorthand for all four line values |
| `justify-self` / `align-self` | override cell alignment for one item |

#### Common grid patterns

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

### When to reach for which

- **Flexbox** — nav bars, toolbars, button groups, anything that's a line of stuff that might wrap.
- **Grid** — page-level layouts, card grids, forms with aligned labels/inputs, anything 2D.
- **Both together** — Grid for the page structure, Flexbox inside each cell for horizontal clusters.

**See also:** [`2.1 HTML & CSS Basics`](./2.1%20HTML%20%26%20CSS%20Basics.md) for CSS units used with `fr`/`minmax`, [`2.6 CSS Interview Questions`](./2.6%20CSS%20Interview%20Questions.md) for worked interview examples using these layouts.

## 2.4 Browser - HTML & CSS part

## Reflow, Repaint, and the `<script>` Tag

Interview questions this note answers:

1. **Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?**
2. **How do you minimize the cost of reflow?**
3. **What does `<script>` do in HTML, and how do `async` and `defer` change its behavior?**
4. **Where should you place `<script>` tags, and why?**

For the big-picture render pipeline these topics fit into, see [`1.1 Browser Basics`](./1.1%20Browser%20Basics.md).

---

### Reflow vs. repaint vs. composite — what triggers each?

**Headline (30s):** Reflow (also called *layout*) recalculates positions and sizes — expensive because it can cascade across the whole page. Repaint redraws visual styles — cheaper, no layout work. Composite merges already-painted layers on the GPU — cheapest. Every reflow triggers a repaint; every repaint triggers a composite. A pure composite is the fastest path.

**Cost ladder:**

| Phase | Triggered by | Cost |
|---|---|---|
| **Composite only** | `transform`, `opacity` (on a composited layer) | cheap — GPU |
| **Paint + composite** | `color`, `background-color`, `visibility`, shadows | moderate — CPU |
| **Reflow + paint + composite** | `width`, `height`, `top`, `left`, DOM insert/remove, font-size, resize | expensive — can cascade |

#### What triggers reflow

- Window resize.
- Adding, removing, or reordering DOM nodes.
- Changes to layout-affecting styles: `width`, `height`, `margin`, `padding`, `border`, `display`, `position`, `font-*`, `line-height`, `text-align`.
- **Reading** geometry properties (`offsetHeight`, `scrollTop`, `getBoundingClientRect`) after a write — this forces a *synchronous* reflow so the browser can return an accurate answer.

#### What triggers repaint (without reflow)

- `color`, `background`, `background-color`, `background-image`
- `visibility` (going between `visible` and `hidden`)
- `box-shadow`, `outline`, `border-color` (but not `border-width`, which changes layout)

#### What stays on the compositor

- `transform: translate / scale / rotate`
- `opacity`
- `filter` (in modern browsers, with `will-change` hint)

**Gotcha — "just animate `top` and `left`":** These trigger reflow on every frame. Use `transform: translate(...)` instead — same visual effect, pure composite, runs on the GPU.

### How do you minimize the cost of reflow?

**Headline (30s):** Batch writes, then reads (never interleave them); change classes rather than individual styles; pull heavy-DOM work off-screen with document fragments; use BFC to isolate layout; debounce high-frequency events; animate only `transform` and `opacity`.

**Tactics:**

- **Batch style changes.** Add or remove a class with many rules rather than setting `element.style.x` individually. A single class swap = one reflow.
- **Minimize DOM access.** Build subtrees in a `DocumentFragment` or an off-screen element, then attach in one operation.
- **Leverage BFC.** Isolating a subtree in a [Block Formatting Context](./2.2%20Box%20Model%20and%20BFC.md) prevents its reflows from cascading outside.
- **Debounce or throttle** `resize` / `scroll` handlers — see [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md).
- **CSS animations + `requestAnimationFrame`.** Prefer CSS-declarative animations; for JS-driven animations, align writes with `requestAnimationFrame` so the browser batches them into one frame.
- **Avoid layout thrashing.** Don't read a geometry property after writing one in the same loop — the browser is forced to flush layout between every read/write pair.

```javascript
// bad — N synchronous reflows
for (const el of items) {
  el.style.width = el.offsetWidth + 10 + 'px';
}

// good — 1 reflow
const widths = items.map(el => el.offsetWidth);
items.forEach((el, i) => { el.style.width = widths[i] + 10 + 'px'; });
```

**Gotcha — `visibility: hidden` vs `display: none` cost:** `display: none` causes a reflow because the element leaves/rejoins the layout tree. `visibility: hidden` only causes a repaint because the element keeps its space. If you're toggling frequently, prefer `visibility` (or `opacity` + `pointer-events: none`).

### What does the `<script>` tag do?

**Headline (30s):** It embeds or references executable JavaScript. By default, encountering a `<script>` pauses HTML parsing until the script is fetched, parsed, and executed — because the script could call `document.write` or mutate the DOM the parser is still building.

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

### `async` vs. `defer` — which to use when?

**Headline (30s):** Both download the script in parallel with HTML parsing (non-blocking). `defer` then waits until parsing finishes and runs scripts **in document order**. `async` runs each script as soon as it's downloaded, in **whatever order** downloads complete. Use `defer` when you need order (most cases). Use `async` only for scripts that are totally independent — analytics, ads.

| Attribute | Downloads | Executes | Blocks parser? | Preserves order? |
|---|---|---|---|---|
| none | inline with parser | immediately | yes | yes |
| `defer` | in parallel | after `DOMContentLoaded` | no | yes |
| `async` | in parallel | as soon as downloaded | no | **no** |

**Gotcha — "`async` is always the fastest":** For scripts that depend on each other, `async` can execute them in the wrong order, causing `undefined is not a function` bugs. Use `defer` unless you're certain the script has zero ordering requirements.

**Gotcha — `defer` doesn't work on inline scripts:** `defer` is ignored if the `<script>` has no `src`. Move the code into an external file or use `DOMContentLoaded`.

### Where should you place `<script>` tags?

**Headline (30s):** The modern answer: in the `<head>` with `defer`. That starts the download as early as possible (parallel with HTML parsing) while guaranteeing execution after the DOM is ready. The old "put scripts before `</body>`" advice is a workaround for environments without `defer`.

**Ranked, best to worst:**

1. `<head>` with `defer` — parallel download, in-order execution after parsing.
2. `<head>` with `async` — parallel download, but ordering isn't guaranteed.
3. Just before `</body>` — legacy safe default; HTML is fully parsed by the time the script runs.
4. `<head>` with no attribute — **worst**; blocks HTML parsing while downloading and executing.

**Best practices beyond placement:**

- Keep JS in external files (cacheable, easier to maintain).
- Minify and compress in production.
- Use non-blocking loading (`defer` / `async`) whenever possible.

**See also:** [`1.1 Browser Basics`](./1.1%20Browser%20Basics.md) for the full URL→render pipeline that these topics fit into, [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md) for deeper animation/scroll optimization.

## 2.5 DOM Properties

Reach for this when you need to measure an element in JavaScript and can't remember which property includes which layers of the box model. These are all geometry properties — reading them forces a layout flush, so use sparingly in tight loops (see [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for layout thrashing).

### Quick comparison

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

### `offsetHeight` / `offsetWidth`

Total visible size including padding, border, and rendered scrollbar — excludes margin.

```text
offsetHeight = content height + padding-top + padding-bottom + border-top + border-bottom (+ scrollbar)
```

### `clientHeight` / `clientWidth`

Visible content area plus padding — excludes border, scrollbar, and margin. This is the space actually available *for* content.

```text
clientHeight = content height + padding-top + padding-bottom
```

### `scrollHeight` / `scrollWidth`

Full size of the element's content including anything hidden by overflow. When content fits inside, `scrollHeight === clientHeight`.

```text
scrollHeight = total content height + padding (includes overflow beyond viewport)
```

### `scrollTop` / `scrollLeft`

Pixels the content has been scrolled vertically / horizontally. **Writable** — set it to control scroll programmatically.

```javascript
const el = document.getElementById('container');
console.log(el.scrollTop);
el.scrollTop = 0;  // scroll to top
```

### `offsetTop` / `offsetLeft`

Distance from the element's outer border to its `offsetParent`'s inner border. `offsetParent` is the nearest positioned ancestor (`position` other than `static`), defaulting to `<body>` if none exists.

### `getBoundingClientRect()`

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

For real visibility tracking (e.g., lazy loading, analytics), prefer `IntersectionObserver` — it doesn't force layout. See [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md).

### When to reach for which

- Need **total rendered size** including border? → `offsetHeight` / `offsetWidth` or `getBoundingClientRect().height/width`.
- Need **inner content area** (for sizing children)? → `clientHeight` / `clientWidth`.
- Need to know if **overflow exists**? → compare `scrollHeight > clientHeight`.
- Need **current scroll position**, or to **scroll programmatically**? → `scrollTop` / `scrollLeft`.
- Need **viewport-relative position** (for tooltips, drag, scroll effects)? → `getBoundingClientRect()`.
- Need **position within parent** (for layout math)? → `offsetTop` / `offsetLeft` (watch out: relative to `offsetParent`, not necessarily the direct parent).

**See also:** [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) on layout thrashing when reading these in loops, [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md) for `IntersectionObserver`-based visibility.

## 2.6 CSS Interview Questions

## How do you clear floats, and why do you need to?

**Headline (30s):** Floated children are removed from the normal flow, so their parent collapses to zero height. You "clear" the float by either (a) making the parent a Block Formatting Context — `display: flow-root` or `overflow: hidden` — so it contains its floats, or (b) adding a clearing pseudo-element that forces the parent to extend past them.

Floating elements removes them from the normal flow of a document, causing parent containers to collapse if not properly handled. It's crucial for front-end developers to understand the methods available to manage this behavior effectively.

### Methods of clearing floats — pure CSS

#### Pseudo-element method (legacy clearfix)

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

#### Block Formatting Context — the modern way

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

#### Fixed dimensions

Straightforward but inflexible.

```css
.parent {
  width: 300px;
  height: 200px;
}
```

**Pros:** Trivial, universal support.
**Cons:** Breaks if child content grows — any overflow is your problem.

### Clearing element — extra HTML

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

**See also:** [`2.2 Box Model and BFC`](./2.2%20Box%20Model%20and%20BFC.md) on how BFCs contain floats, [`2.3 Flex & Grid Layout`](./2.3%20Flex%20%26%20Grid%20Layout.md) for modern alternatives.

---

## How do you build a three-column layout with fixed sides and a fluid middle?

**Headline (30s):** Six valid approaches, ranked modern → legacy: Flexbox (`flex-grow: 1` on the middle), Grid (`grid-template-columns: 100px 1fr 100px`), absolute positioning, table-cell, float + `calc()`, and inline-block + `calc()`. For new code, use Grid or Flex. Know the others so you can read legacy CSS.

The layout includes two fixed-width divs on the sides (`left` and `right`) and a dynamically adjusting center div (`center`).

### HTML structure

```html
<div class="parent">
  <div class="left">Left</div>
  <div class="center">Center</div>
  <div class="right">Right</div>
</div>
```

### CSS resets

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

### Float-based layout

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

### Table display layout

```css
.parent { display: table; }
.left, .center, .right { display: table-cell; }
```

**Pros:** Stable and predictable rendering.
**Cons:** Semantically wrong for non-tabular data.

### Absolute positioning layout

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

### Flexbox layout

```css
.parent { display: flex; }
.center { flex-grow: 1; }
```

**Pros:** Modern, responsive, minimal code.
**Cons:** Only a concern for very old-browser support.

### Grid layout

```css
.parent {
  display: grid;
  grid-template-columns: 100px 1fr 100px;
}
```

**Pros:** Cleanest, intention-revealing.
**Cons:** Not supported in truly ancient browsers.

**Gotcha — `calc(100% - 200px)` + `box-sizing: content-box`:** If `.parent` has padding and you're using content-box, `100%` doesn't mean what you think. Always normalize with `box-sizing: border-box`.

**See also:** [`2.3 Flex & Grid Layout`](./2.3%20Flex%20%26%20Grid%20Layout.md) for the property reference.

---

## How do you build a two-column layout with one fixed and one responsive side?

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

### Strict responsive solutions (reflow with viewport)

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

### Non-strict solutions (need `calc` or manual math)

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

## How do you center an element in CSS?

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

### Centering with dynamic dimensions (element size unknown)

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

### Centering with fixed dimensions

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

## How do you draw a triangle with pure CSS?

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

## How do you render a crisp 1px line on Retina / high-DPR screens?

**Headline (30s):** On a 2x DPR screen, 1 CSS pixel maps to 2 physical pixels, so a `border: 1px` line appears "chunky". The classic fix is a pseudo-element at 100% of the container width + `transform: scaleY(0.5)`, which lets you render a half-CSS-pixel (i.e. one physical pixel) line without running into the browser's handling of fractional px values.

### Using a pseudo-element + transform

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

### Handling borders with `border-radius`

When the element has `border-radius`, borders and scales interact awkwardly. Use `box-shadow` instead:

```css
.box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

`box-shadow` at fractional values is handled more consistently across modern browsers than a fractional `border-width`.

**Gotcha — `1px solid` on devices with variable DPR:** A single line might look 1px on a laptop (DPR 1), 2px on a 2x phone, or 3px on a 3x phone. If visual consistency matters, feature-detect DPR with `window.devicePixelRatio` and adjust — or use SVG for scale-invariant strokes.

---

## How do you prevent the 300ms tap delay on mobile?

**Headline (30s):** Modern browsers disable the 300ms double-tap-to-zoom delay automatically once they see `<meta name="viewport" content="width=device-width, initial-scale=1">`. That's usually all you need. Libraries like FastClick are legacy — don't add them in new code.

On mobile web apps, browsers historically waited ~300ms after a tap to check whether a second tap was coming (zoom gesture). This delay used to be worked around with libraries like FastClick. Modern browsers detect responsive intent from the viewport meta tag and skip the delay.

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

**Why this works:** A site that declares `width=device-width` is telling the browser "I'm designed for mobile; don't pinch-zoom me." Without that signal, the browser assumes it might need the zoom gesture and waits to see if a second tap is coming.

**Gotcha — FastClick is obsolete and harmful:** On modern browsers, FastClick can actually *cause* double-firing of events because it dispatches synthetic clicks on top of native ones. Remove it from new projects.

## 2.7 CSS Position, Display, and Animations

## How do the CSS `position` values differ?

**Headline (30s):** Five values. `static` is the default (normal flow, offsets do nothing). `relative` reserves its spot in the flow but lets you offset it visually. `absolute` is removed from the flow, positioned relative to its nearest *positioned* ancestor. `fixed` is removed from the flow, positioned relative to the viewport. `sticky` is a hybrid — it flows normally until it crosses a scroll threshold, then sticks like `fixed`.

| Value | In flow? | Positioned relative to | Scrolls with page? |
|---|---|---|---|
| `static` (default) | yes | — (offsets ignored) | yes |
| `relative` | yes (original space reserved) | its own original position | yes |
| `absolute` | no | nearest positioned ancestor | yes (relative to ancestor) |
| `fixed` | no | viewport | no |
| `sticky` | yes → no (after threshold) | scroll container | yes, until sticky |

### `static` (default)

Element flows normally in document order. `top`, `right`, `bottom`, `left`, and `z-index` have no effect.

```css
.box { position: static; }
```

### `relative`

Element stays in normal flow; space is reserved as if it were not positioned. Offset properties shift it *visually* without affecting sibling layout. Also establishes a positioning context for absolutely positioned descendants.

```css
.box { position: relative; top: 10px; left: 20px; }
```

### `absolute`

Element removed from normal flow — no space reserved. Positioned relative to its nearest **positioned ancestor** (any ancestor with `position: relative`, `absolute`, `fixed`, or `sticky`). With no positioned ancestor, the initial containing block (usually `<html>`) is used.

```css
.parent { position: relative; } /* creates positioning context */
.child  { position: absolute; top: 0; right: 0; }
```

### `fixed`

Removed from normal flow; positioned relative to the **viewport**. Stays put while the page scrolls.

```css
.navbar { position: fixed; top: 0; left: 0; right: 0; }
```

**Gotcha — `fixed` inside a `transform`ed ancestor:** If any ancestor has `transform`, `filter`, or `perspective` set (even just `translateZ(0)`), the ancestor becomes the new containing block — and your `fixed` element now scrolls with the ancestor instead of the viewport. Easy to miss until you debug why your header isn't sticky on a page with CSS animations.

### `sticky`

Element starts in normal flow; behaves like `fixed` once scroll crosses a threshold defined by `top`, `right`, `bottom`, or `left`. At least one of those must be set.

```css
.header { position: sticky; top: 0; }
```

**Gotcha — `overflow: hidden` on an ancestor kills `sticky`:** `sticky` only works if its scroll container has `overflow: visible` (or has no overflow set). A `sticky` child inside `overflow: hidden` silently behaves like `relative`. Check the entire ancestor chain when debugging.

### Stacking context and `z-index`

`z-index` controls stacking order along the z-axis, but **only within the same stacking context**. Elements with `position` other than `static` create a stacking context when `z-index` is set; so do elements with `opacity < 1`, `transform`, `filter`, `will-change`, and a few others.

```css
.layer-a { position: relative; z-index: 1; }
.layer-b { position: relative; z-index: 2; } /* above layer-a */
```

**Gotcha — "my `z-index: 9999` isn't on top":** A stacking context is an isolation boundary. A descendant's `z-index` can never escape to compete with elements outside its context — no matter how high the value. If `.modal` sits inside a parent with `transform: translateZ(0)`, any `z-index` on the modal only competes with *siblings inside that parent*. To fix, raise the `z-index` (or create a stacking context) on an ancestor shared with the element you're trying to overlap.

---

## When should you use `display: none` vs `visibility: hidden` vs `opacity: 0`?

**Headline (30s):** `display: none` removes the element from layout entirely (causes reflow; screen readers ignore it; can't animate). `visibility: hidden` keeps the layout space but hides the pixels (cheaper — repaint only; screen readers still ignore). `opacity: 0` keeps the layout and pixels "there" but invisible — the element still receives clicks and is still announced by screen readers unless you add `aria-hidden`.

| Aspect | `display: none` | `visibility: hidden` | `opacity: 0` |
|---|---|---|---|
| **Space in layout** | removed | reserved | reserved |
| **Receives clicks / events** | no | no | **yes** (add `pointer-events: none` to disable) |
| **Announced by screen readers** | no | no | often yes (add `aria-hidden`) |
| **Can animate** | no (all-or-nothing) | yes, on `visibility` | yes, on `opacity` |
| **Cost when toggled** | reflow + paint | paint only | paint only (composite if promoted) |
| **Affects children** | children hidden | children inherit (can override with `visibility: visible`) | children inherit |

#### Decision guide

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

## How do CSS transitions and animations work, and when should you prefer one over the other?

**Headline (30s):** A **transition** interpolates between two states triggered by a property change (e.g., hover). An **animation** runs independently from defined keyframes and can loop, pause, and control fill state. Use transitions for simple state-to-state interactions (hover, focus, click). Use animations for complex, multi-step, or looping motion.

### Transitions

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

### `@keyframes` and `animation`

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

### `transform` properties

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

### GPU compositing and hardware acceleration

Animating `transform` and `opacity` runs on the **compositor** (GPU) instead of triggering layout/paint. `will-change` hints to the browser to pre-promote the element to its own layer. See [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for the full cost ladder.

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* force GPU layer without visible movement */
}
```

**Gotcha — don't `will-change` everything:** Each hinted element becomes its own compositor layer and eats memory. Use `will-change` only for the element you're actively animating; remove it after the animation is done (via class toggle) if the element persists. Over-hinting can hurt performance on low-end devices.

**Gotcha — `transform: translateZ(0)` is a blunt instrument:** It pre-promotes to a GPU layer but burns memory. `will-change: transform` is the modern, intention-revealing equivalent, but both should only be used when you've measured a performance problem.

**See also:** [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for the reflow/repaint cost ladder, [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md) for when GPU acceleration does and doesn't help.

# 3. JavaScript 101


## 3.1 Javascript Basics

## `var`, `let`, and `const`

Reach for this when you need to remember the difference between the three variable declarations, including scoping, hoisting, and the Temporal Dead Zone.

### Quick comparison

| | `var` | `let` | `const` |
|---|---|---|---|
| **Scope** | function | block | block |
| **Hoisted?** | yes, initialized to `undefined` | yes, but uninitialized (TDZ) | yes, but uninitialized (TDZ) |
| **Redeclaration in same scope** | allowed | `SyntaxError` | `SyntaxError` |
| **Reassignment** | allowed | allowed | **not** allowed (binding is frozen) |
| **Must be initialized?** | no | no | yes |

**Default:** use `const`; switch to `let` only when the binding must be reassigned; avoid `var` in new code.

### `var` — function-scoped, hoisted to `undefined`

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

### `let` — block-scoped, Temporal Dead Zone

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

### `const` — block-scoped, binding frozen

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

### Best practice

1. **Default to `const`** — most bindings don't need to change after initialization.
2. **Use `let`** only where reassignment is actually needed (loop counters, accumulators).
3. **Don't use `var` in new code.** ES6 made `let`/`const` available everywhere; `var` only remains for extreme legacy-browser support.

**See also:** [`4.2 Scope & Closure`](./4.2%20Scope%20%26%20Closure.md) for how scope interacts with closures.

## 3.2 Javascript Types

Four interview questions this note prepares you for:

1. **What are the primitive types in JavaScript?**
2. **What's the difference between primitive and reference types?** (with the classic `a.x = a = {}` gotcha)
3. **How do you reliably check a variable's type?**
4. **What types can be used as object keys, and what happens if you use something else?**

---

### What are the primitive types in JavaScript?

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

#### Type-coercion cheat sheet

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

### Primitive vs reference types — what's the difference?

**Headline (30s):** Primitives live on the stack and are compared by value — copying a primitive duplicates the data. Reference types live on the heap; a variable stores a pointer to that heap slot. Assigning one reference variable to another makes both point to the same object; mutating through one reference shows up through the other.

| | Primitive | Reference |
|---|---|---|
| **Stored in** | stack | heap (variable holds a pointer) |
| **Compared** | by value | by reference |
| **Copy on assignment?** | yes (duplicate data) | no (share the same object) |
| **Mutable?** | no | yes |

#### The classic "right-to-left assignment" gotcha

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

### How do you reliably check a variable's type?

**Headline (30s):** `typeof` works for primitives but misidentifies `null` as `'object'` and treats arrays and plain objects identically. `instanceof` works for objects from a specific constructor (within its prototype chain). The reliable-for-everything answer is `Object.prototype.toString.call(x)` — it returns strings like `'[object Array]'`, `'[object Null]'`, `'[object Date]'` — or a thin wrapper around it like a custom `getType()`.

#### `typeof` — fast, primitive-friendly, lies about `null` and arrays

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

#### `instanceof` — constructor-based, no help for primitives

Checks whether the constructor's `prototype` appears in the value's prototype chain. Under the hood, it invokes `Constructor[Symbol.hasInstance]`.

```javascript
[] instanceof Array;     // true
({}) instanceof Object;  // true
'x' instanceof String;   // false  (primitive string ≠ String object)
```

**Reach for it when:** checking whether an object came from a specific class.

**Gotcha — cross-realm objects:** `instanceof` can return `false` for arrays from another iframe or worker because each realm has its own `Array.prototype`. Use `Array.isArray(x)` for arrays specifically.

#### `Object.prototype.toString.call()` — works for everything

```javascript
Object.prototype.toString.call([1, 2, 3]);   // '[object Array]'
Object.prototype.toString.call(null);         // '[object Null]'
Object.prototype.toString.call(new Date());   // '[object Date]'
Object.prototype.toString.call(/regex/);      // '[object RegExp]'
```

**Reach for it when:** you need a definitive type string that works across realms, handles `null` and `undefined`, and distinguishes built-in object types.

#### A custom `getType` combining all three

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

### What types can be used as object keys?

**Headline (30s):** Only **strings** and **symbols**. Anything else is coerced to a string via the value's `toString()`. This means numeric keys are *actually* strings, and two different plain objects used as keys both become `"[object Object]"` — overwriting each other. If you need non-string keys, use `Map` instead.

#### Key conversion rules

- **String or symbol:** used directly.
- **Any other type:** converted via `toString()`.
  - Numeric keys: `obj[123]` and `obj['123']` access the same slot.
  - Plain objects: all become `"[object Object]"` — they collide.
  - Arrays: `[1, 2]` becomes `"1,2"`.
- **`Map`:** keys of **any** type are preserved without coercion.

#### Example 1 — numeric keys collide with string keys

```javascript
const o = {};
const strKey = '123';
const numKey = 123;
o[strKey] = 'string-valued';
o[numKey] = 'number-valued';
console.log(o[strKey]); // 'number-valued'  (both wrote to the same string key)
```

#### Example 2 — Symbol uniqueness

```javascript
const o = {};
const s1 = Symbol('id');
const s2 = Symbol('id');
o[s1] = 'one';
o[s2] = 'two';
console.log(o[s1]); // 'one'  (symbols with the same description are still different)
```

#### Example 3 — two objects as keys collide

```javascript
const o = {};
const k1 = { key: '123' };
const k2 = { key: '456' };
o[k1] = 'one';
o[k2] = 'two';
console.log(o[k1]); // 'two'  (both keys coerced to "[object Object]")
```

**Gotcha — reaching for `Map` when object keys matter:** If you need to associate data with objects without this collision (or without coercion at all), use `Map`. See [`3.3 Map & Set in JS`](./3.3%20Map%20%26%20Set%20in%20JS.md).

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](./3.4%20Memory%20in%20JS,%20WeakMap%20and%20WeakSet.md) for how primitives and references interact with the stack and heap.

## 3.3 Map & Set in JS

Reach for this when you need the API reference for `Map` or `Set` — what methods they expose, how to iterate them, and when to pick them over plain objects and arrays.

### When to use `Map` vs plain object

- **`Map`** — keys of any type (including objects and functions), preserved insertion order, `.size` property, direct iteration with `for...of`. Slightly slower than plain objects for string-only keys but far more predictable.
- **Object** — only string and symbol keys, shape-optimized by the JS engine, but prototype pollution and the `"[object Object]"` coercion trap (see [`3.2 JavaScript Types`](./3.2%20Javascript%20Types.md)) make it risky as a general-purpose dictionary.

Rule of thumb: **if keys are anything other than fixed identifiers, use `Map`**.

### When to use `Set` vs array

- **`Set`** — O(1) uniqueness checks, automatic dedupe on insert, `.has()` is constant time.
- **Array** — ordered, index-addressable, rich iteration methods (`map`, `filter`, `reduce`).

Rule of thumb: **if the primary operation is "is this value present?", use `Set`**. If you need order or positional access, use an array.

---

### `Map`

#### Creating a Map

```javascript
let myMap = new Map();
let fromPairs = new Map([['a', 1], ['b', 2]]);
```

#### Core methods

| Method | What it does |
|---|---|
| `set(key, value)` | add or update an entry |
| `get(key)` | return the value, or `undefined` |
| `has(key)` | boolean check |
| `delete(key)` | remove an entry |
| `clear()` | empty the map |
| `size` | number of entries (property, not method) |

```javascript
myMap.set('key1', 'value1');
myMap.set('key2', 'value2');
myMap.set(3, 'value3'); // any type of key

myMap.get('key1');  // 'value1'
myMap.has('key1');  // true
myMap.delete('key2');
myMap.clear();
```

#### Traversing a Map

```javascript
// Entry iteration (for...of with destructuring)
for (const [key, value] of myMap) {
  console.log(key, value);
}

// forEach — value, key, map (note the unusual order)
myMap.forEach((value, key) => {
  console.log(key, value);
});

// Keys only
for (const key of myMap.keys()) { console.log(key); }

// Values only
for (const value of myMap.values()) { console.log(value); }

// Entries (same as default iteration)
for (const [key, value] of myMap.entries()) { console.log(key, value); }
```

#### Example end-to-end

```javascript
let myMap = new Map();

myMap.set('name', 'Alice');
myMap.set('age', 30);
myMap.set('job', 'developer');

myMap.get('name');   // 'Alice'
myMap.has('job');    // true
myMap.delete('age');

myMap.forEach((value, key) => {
  console.log(`${key}: ${value}`);
});

myMap.clear();
console.log(myMap.size); // 0
```

---

### `Set`

A `Set` holds unique values — assigning a duplicate is a no-op. Keys and values are the same thing.

#### Core methods

| Method | What it does |
|---|---|
| `add(value)` | insert a value (no-op if duplicate) |
| `has(value)` | boolean check |
| `delete(value)` | remove a value |
| `clear()` | empty the set |
| `size` | number of entries |

```javascript
const mySet = new Set();
mySet.add(1);
mySet.add(5);
mySet.add('some text');

mySet.has(1);  // true
mySet.has(3);  // false
mySet.delete(5);
mySet.clear();
```

#### Traversing a Set

```javascript
// for...of yields values in insertion order
for (const value of mySet) { console.log(value); }

// forEach — value, value, set (value given twice for API consistency with Map)
mySet.forEach(value => console.log(value));

// values() and keys() return the same iterator
for (const value of mySet.values()) { console.log(value); }

// entries() yields [value, value] for Map API parity
for (const [v1, v2] of mySet.entries()) { console.log(v1, v2); }
```

#### Example end-to-end

```javascript
const mySet = new Set([1, 2, 3, 4]);

mySet.add(5);
mySet.add(5); // ignored — already present

mySet.has(1);  // true
mySet.has(6);  // false
mySet.delete(3);

mySet.forEach(v => console.log(v)); // 1, 2, 4, 5

mySet.clear();
console.log(mySet.size); // 0
```

### Common idioms

**Remove duplicates from an array:**

```javascript
const unique = [...new Set([1, 2, 2, 3, 3, 3])];
// [1, 2, 3]
```

**Fast set-difference:**

```javascript
const a = new Set([1, 2, 3]);
const b = new Set([2, 3, 4]);
const only = [...a].filter(x => !b.has(x));
// [1]
```

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](./3.4%20Memory%20in%20JS,%20WeakMap%20and%20WeakSet.md) for the garbage-collection-aware variants (`WeakMap` / `WeakSet`), [`3.2 Javascript Types`](./3.2%20Javascript%20Types.md) for why plain objects are unreliable as dictionaries.

## 3.4 Memory in JS, WeakMap and WeakSet

Three interview questions this note prepares you for:

1. **How does JavaScript manage memory? What's the difference between the stack and the heap?**
2. **What is a `WeakMap`, and when would you use one instead of a regular `Map`?**
3. **What is a `WeakSet`, and when would you use one?**

For the garbage collection mechanism itself (mark-and-sweep, reference counting), see [`7.1 Event Loop`](./7.1%20Event%20Loop.md).

---

### How does JavaScript manage memory?

**Headline (30s):** JavaScript stores primitives directly on the **stack** — a fast, LIFO region managed automatically with each function call. Reference types (objects, arrays, functions) are allocated on the **heap**, with the variable on the stack holding only a pointer to the heap slot. The engine's garbage collector reclaims heap memory once nothing references the object.

#### The stack

Operates on a Last-In-First-Out principle. When a function is called, its parameters and local primitives are pushed onto the stack; on return, they're popped. Quick to allocate, quick to free. But limited in size — deep recursion or huge local arrays can trigger `Maximum call stack size exceeded`.

#### The heap

A larger, unstructured memory pool for dynamically allocated data — every object, array, and function body lives here. Allocation and freeing are handled by the JS engine's garbage collector (see [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for the reference-counting and mark-and-sweep mechanisms). The stack holds pointers into the heap; the heap holds the actual data.

**Gotcha — "primitive means stack":** Short strings and inlined number literals commonly live on the stack, but the JS engine is free to intern large strings or box values into heap slots for optimization. The specification doesn't mandate stack vs heap; what *is* guaranteed is the semantic: primitives copy, references share.

---

### What is a `WeakMap`, and when would you use one?

**Headline (30s):** A `WeakMap` is a key-value collection where **the keys must be objects** and are held **weakly** — they don't prevent garbage collection. Once no other reference to a key exists, the engine is free to remove the entry automatically. `WeakMap` is ideal for attaching private data to objects you don't own (DOM nodes, class instances), so the metadata disappears when the object is freed.

**Key differences from `Map`:**

- **Keys must be objects** (not primitives).
- **Keys are held weakly** — no strong reference from the `WeakMap` back to the key.
- **Not enumerable** — no `.keys()`, `.values()`, `.entries()`, `.size`, `.forEach()`. Only `set`, `get`, `has`, `delete`.
- **No access to garbage-collection timing** — you can't observe when entries are reclaimed.

#### When to reach for a `WeakMap`

- **Private fields on class instances** — before class private fields (`#field`) shipped, `WeakMap` was the canonical workaround.
- **Metadata keyed by DOM nodes** — when the node goes away, your metadata goes with it.
- **Caches keyed by objects** — no manual cleanup code; the cache entry disappears once the key is collected.

#### Example — private data on a class instance

```javascript
const privateData = new WeakMap();

class MyClass {
  constructor() {
    privateData.set(this, { secret: 'hidden' });
  }

  getSecret() {
    return privateData.get(this).secret;
  }
}

const instance = new MyClass();
console.log(instance.getSecret()); // 'hidden'

// When `instance` goes out of scope, the entry in privateData
// can be garbage-collected — no manual cleanup needed.
```

**Gotcha — "I can't iterate a WeakMap":** That's deliberate. Iteration would require keeping strong references, defeating the purpose. If you need iteration, you need a regular `Map` plus manual cleanup.

---

### What is a `WeakSet`, and when would you use one?

**Headline (30s):** A `WeakSet` holds a collection of **objects** weakly — objects can drop out when no other reference holds them. It has just three methods (`add`, `has`, `delete`) and no iteration. Use it to track "have I seen this object?" without preventing the object from being garbage-collected.

**Key properties:**

- **Members must be objects.**
- **Weak references** — no ownership; objects are GC-eligible.
- **Not enumerable** — `add`, `has`, `delete` only.

#### When to reach for a `WeakSet`

- **Tracking "processed" objects** without preventing cleanup.
- **Tagging nodes** visually (e.g., "these DOM elements already have listeners attached") where the tag should vanish with the element.

#### Example — dedupe work by object identity

```javascript
const processedObjects = new WeakSet();

function process(obj) {
  if (processedObjects.has(obj)) return;
  // ...actual work...
  processedObjects.add(obj);
}

const obj1 = {};
process(obj1);
process(obj1); // no-op — already seen

// When obj1 goes out of scope, it's eligible for GC,
// and disappears from processedObjects automatically.
```

**Gotcha — not suitable for counting or batch operations:** No `.size`, no iteration. For anything beyond "is this one object present?", use a regular `Set`.

---

### Summary

| | `Map` / `Set` | `WeakMap` / `WeakSet` |
|---|---|---|
| **Keys / members** | any type | **objects only** |
| **GC behavior** | prevents GC (strong refs) | allows GC (weak refs) |
| **Iterable?** | yes | **no** |
| **Size property?** | yes | no |
| **Typical use** | general dictionary / set | lifecycle-scoped metadata, caches |

**See also:** [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for garbage collection mechanics, [`3.3 Map & Set in JS`](./3.3%20Map%20%26%20Set%20in%20JS.md) for the strong-reference variants.

## 3.5 Array in JS

## What's the difference between `for..in` and `for..of`?

**Headline (30s):** `for..in` iterates **enumerable keys** — that's property names on objects, or *string indices* on arrays ("0", "1", "2"). `for..of` iterates **values** from anything iterable — arrays, strings, `Map`, `Set`, `NodeList`, `arguments`. If you want values from an array, use `for..of` (or a plain `for` with index). Reach for `for..in` only when you actually want keys of a plain object.

### `for..in` — iterates enumerable keys

```javascript
const arr = [10, 20, 30];
for (let i in arr) {
  console.log(i); // 0, 1, 2  (indexes as strings)
}

const str = 'abc';
for (let i in str) {
  console.log(i); // 0, 1, 2
}

const obj = { name: 'aaa', age: 30 };
for (let key in obj) {
  console.log(key); // 'name', 'age'
}
```

**Gotcha — `for..in` on arrays yields string indices, not values:** Don't use it on arrays. The indexes come back as strings, and the iteration order is not guaranteed for arrays (it usually *happens* to be numeric for dense arrays, but the spec doesn't require it).

**Gotcha — inherited enumerable properties:** `for..in` walks the prototype chain. A property added to `Object.prototype` shows up in every `for..in` loop. In modern code this rarely happens, but `Object.keys(obj)` or `for..of` over `Object.entries(obj)` is safer.

### `for..of` — iterates values from iterables

```javascript
const arr = [10, 20, 30];
for (let v of arr) console.log(v); // 10, 20, 30

const str = 'abc';
for (let ch of str) console.log(ch); // 'a', 'b', 'c'

function fn() {
  for (let arg of arguments) console.log(arg);
}
fn(100, 200, 'aaa'); // 100, 200, 'aaa'

const s = new Set([10, 20, 30]);
for (let v of s) console.log(v); // 10, 20, 30

const m = new Map([['x', 100], ['y', 200]]);
for (let [key, value] of m) console.log(key, value);
```

**Gotcha — `for..of` doesn't work on plain objects:** Plain objects aren't iterable by default. Convert first: `for (const [k, v] of Object.entries(obj))`.

---

## How do you remove duplicates from an array?

**Headline (30s):** `[...new Set(arr)]` for primitives — O(n) time, one line, impossible to get wrong. For objects keyed by a property, loop + `Map` using that property as the key. Older idioms (`filter + indexOf`, `reduce + includes`) are O(n²) and should only be cited for how *not* to do it.

### 1. Using a Set — the default answer

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return [...new Set(arr)];
}
```

**Time:** O(n). **Space:** O(n).

### 2.1 Filter + `indexOf` — O(n²), avoid

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.filter((item, index) => arr.indexOf(item) === index);
}
```

**Time:** O(n²) — `indexOf` scans the whole array for each element. **Space:** O(n).

### 2.2 Filter + Set — O(n) optimization of 2.1

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  const seen = new Set<T>();
  return arr.filter(item => {
    if (!seen.has(item)) {
      seen.add(item);
      return true;
    }
    return false;
  });
}
```

**Time:** O(n). **Space:** O(n).

### 3. `Map` for dedupe-by-key of objects

```typescript
interface CustomObject {
  id: number;
  name: string;
}

function removeDuplicates(arr: CustomObject[]): CustomObject[] {
  const unique = new Map<number, CustomObject>();
  arr.forEach(obj => unique.set(obj.id, obj));
  return Array.from(unique.values());
}
```

**Time:** O(n). **Space:** O(n). **Note:** the *last* object with a given `id` wins (later `set` overrides earlier).

### 4.1 Reduce + `includes` — O(n²), avoid

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.reduce((acc, current) => {
    if (!acc.includes(current)) acc.push(current);
    return acc;
  }, [] as T[]);
}
```

**Time:** O(n²).

### 4.2 Reduce + Set — O(n) optimization

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  const seen = new Set<T>();
  return arr.reduce((acc, current) => {
    if (!seen.has(current)) {
      seen.add(current);
      acc.push(current);
    }
    return acc;
  }, [] as T[]);
}
```

**Time:** O(n). **Space:** O(n).

### 5. Sort + reduce — O(n log n), preserves nothing

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.sort().reduce((acc, current) => {
    if (acc.length === 0 || acc[acc.length - 1] !== current) acc.push(current);
    return acc;
  }, [] as T[]);
}
```

**Time:** O(n log n). **Note:** destroys original order. Useful only when you already need the array sorted.

### 6. `Array.from(new Set(arr))` — equivalent to option 1

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}
```

**Gotcha — `Set` compares by reference for objects:** `new Set([{id: 1}, {id: 1}])` keeps both entries because they're different references. Dedupe-by-key with a `Map` is the right tool for objects.

---

## What is the spread operator, and how does it compile?

**Headline (30s):** `...` expands an iterable (most commonly an array) in places where multiple values are expected — function calls, array literals, object literals. For older targets, Babel compiles array spread to `.concat()` or `Array.prototype.slice.call(arguments)`.

```typescript
const baseArray = [1, 2, 3, 4];
const array = [...baseArray];
```

Babel compiles this down to something like:

```javascript
var baseArray = [1, 2, 3, 4];
var array = [].concat(baseArray);
```

That transpilation preserves the "shallow copy into a new array" semantic in environments that don't support ES6 syntax.

### BabelJS overview

Babel is a JavaScript compiler that transforms ECMAScript 2015+ code into a version compatible with older browsers and environments. Plugins and presets (`@babel/preset-env`) target a specific set of browsers, so you can write modern syntax and ship compatible output.

**Gotcha — spread is shallow:** `[...arr]` copies top-level elements by reference. Nested objects are shared. For deep copy, use `structuredClone()` (see [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md)).

---

## What are the most-used Array methods?

**Headline (30s):** A small core handles most real-world array work: `map` transforms, `filter` selects, `reduce` folds, `some` / `every` test, `concat` joins, `indexOf` / `lastIndexOf` locate, `sort` and `reverse` reorder in place. Learn the signatures (especially `reduce` and `sort`'s comparator) and you can derive the rest from docs.

### Concatenation — `concat`

Joins two or more arrays into a new array without mutating the originals.

```javascript
const a = ['a', 'b', 'c'];
const b = ['d', 'e', 'f'];
a.concat(b); // ['a', 'b', 'c', 'd', 'e', 'f']
```

### Element checking — `every` / `some`

- `every(fn)` — `true` if **all** elements pass.
- `some(fn)` — `true` if **any** element passes.

```javascript
const isBelow40 = n => n < 40;
const nums = [1, 30, 39, 29, 10, 13];
nums.every(isBelow40); // true
nums.some(isBelow40);  // true
```

### Filtering — `filter`

Returns a new array of elements that pass the predicate.

```javascript
const words = ['spray', 'limit', 'elite', 'exuberant', 'destruction', 'present'];
words.filter(w => w.length > 6); // ['exuberant', 'destruction', 'present']
```

### Mapping — `map`

Returns a new array of transformed values.

```javascript
[1, 4, 9, 16].map(Math.sqrt); // [1, 2, 3, 4]
```

### Sorting — `sort`

Sorts **in place**. Default compares by UTF-16 code unit, **not** numerically.

```javascript
['March', 'Jan', 'Feb', 'Dec'].sort(); // ['Dec', 'Feb', 'Jan', 'March']

[1, 11, 2, 22].sort();                   // [1, 11, 2, 22] — string sort!
[1, 11, 2, 22].sort((a, b) => a - b);    // [1, 2, 11, 22] — numeric sort
```

**Gotcha — default `sort` on numbers is wrong for most use cases.** Always pass a comparator when sorting numbers: `(a, b) => a - b`.

### Reversing — `reverse`

Reverses in place.

```javascript
['one', 'two', 'three'].reverse(); // ['three', 'two', 'one']
```

### Conversion to string — `toString`

```javascript
[1, 2, 'a', '1a'].toString(); // '1,2,a,1a'
```

### Index finding — `indexOf` / `lastIndexOf`

```javascript
const beasts = ['ant', 'bison', 'camel', 'duck', 'bison'];
beasts.indexOf('bison');     // 1
beasts.lastIndexOf('bison'); // 4
```

**See also:** [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for `Array.at()`, `Array.from()`, and other newer methods.

---

## How do you flatten a nested array?

**Headline (30s):** `arr.flat(Infinity)` is the one-liner — supported in all modern environments. The recursive, reduce-based, and iterative variants below are worth recognizing because they show up in interview "implement this yourself" scenarios.

### Recursive approach

```typescript
function arrayFlatten(arr: any[]): any[] {
  let flattened = [];
  for (let i = 0; i < arr.length; i++) {
    if (Array.isArray(arr[i])) {
      flattened = flattened.concat(arrayFlatten(arr[i]));
    } else {
      flattened.push(arr[i]);
    }
  }
  return flattened;
}
```

**Pros:** works anywhere, easy to explain. **Cons:** recursion stack — can fail on very deep arrays.

### Functional (reduce + recursion)

```typescript
function arrayFlatten(arr: any[]): any[] {
  return arr.reduce((prev, cur) =>
    prev.concat(Array.isArray(cur) ? arrayFlatten(cur) : cur), []);
}
```

**Pros:** declarative and concise. **Cons:** same recursion depth concern.

### Iterative approach

```typescript
function arrayFlatten(arr: any[]): any[] {
  while (arr.some(Array.isArray)) {
    arr = [].concat(...arr);
  }
  return arr;
}
```

**Pros:** no recursion — safe on deep arrays. **Cons:** quadratic in the worst case if the array is very jagged.

### ES6 `.flat()` method

```typescript
function arrayFlatten(arr: any[]): any[] {
  return arr.flat(Infinity);
}
```

**Pros:** concise, optimized natively. **Cons:** not available in IE11 and earlier (no longer relevant in most codebases).

**Gotcha — `.flat()` without an argument only flattens one level:** `.flat()` defaults to depth 1; use `.flat(Infinity)` for fully-nested input. Don't rely on the default for unknown nesting depths.

## 3.6 ES6 New Methods

Reach for this when you need a quick reference for the `Object.*` and `Array.*` utility methods introduced in ES6. For newer additions (`Object.hasOwn`, `Array.at`, `structuredClone`), see [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md).

### Object methods

#### `Object.assign(target, ...sources)`

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

#### `Object.is(a, b)`

Same as `===`, with two exceptions:

- `Object.is(NaN, NaN)` is `true` (strict equality would be `false`).
- `Object.is(+0, -0)` is `false` (strict equality would be `true`).

```javascript
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

Reach for it when you need to distinguish `+0` from `-0` (rare) or detect `NaN` without `Number.isNaN`.

#### `Object.keys(obj)`

Array of the object's own enumerable string-keyed property names, in insertion order (with integer keys numerically ordered first).

```javascript
Object.keys({ a: 1, b: 2, c: 3 }); // ['a', 'b', 'c']
```

#### `Object.values(obj)`

Array of the own enumerable values.

```javascript
Object.values({ a: 1, b: 2, c: 3 }); // [1, 2, 3]
```

#### `Object.entries(obj)`

Array of `[key, value]` pairs. Enables iteration with `for...of` destructuring.

```javascript
Object.entries({ a: 1, b: 2, c: 3 });
// [['a', 1], ['b', 2], ['c', 3]]

for (const [key, value] of Object.entries(obj)) {
  console.log(key, value);
}
```

These three methods are the go-to for iterating a plain object — preferred over `for..in`, which walks the prototype chain.

### Array methods

#### `Array.from(arrayLike, mapFn?)`

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

#### `Array.of(...elements)`

Creates an array from its arguments — bypasses the `Array(n)` constructor's "single number means length" quirk.

```javascript
Array.of(1, 2, 3); // [1, 2, 3]

Array(3);      // creates [ <3 empty slots> ] — length 3, no values
Array.of(3);   // creates [3] — one element, value 3
```

**Reach for it when:** constructing an array from a known set of elements and at least one could be a number — `Array.of()` disambiguates the intent.

**See also:** [`3.5 Array in JS`](./3.5%20Array%20in%20JS.md) for array iteration and transformation methods, [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for post-ES6 additions.

## 3.7 Other JS

A grab-bag of short interview-favorite JavaScript topics. Reach for this when someone asks about strict mode, floating-point math, equality operators, or the `!!` idiom.

### What does `'use strict';` do?

Strict mode enforces stricter parsing and error handling. Activate it by adding `'use strict';` at the top of a script or function. It has different semantics from regular code, aimed at improving reliability and performance. Modern modules (ES modules and classes) run in strict mode automatically.

#### Features of strict mode

1. **Mandatory variable declarations.** Assigning to an undeclared variable throws `ReferenceError`, preventing accidental global creation from typos.
2. **Disallows `with` statements.** `with` creates unpredictable scope, hurts performance, and complicates debugging.
3. **Scoped `eval()`.** Declarations inside `eval` no longer leak into the surrounding scope, making `eval` marginally safer.
4. **Secure `this` binding.** A plain function call (not as a method) has `this === undefined`, instead of `this === window`. Prevents accidental global mutation.
5. **No duplicate parameter names.** `function f(a, a) {}` throws. Eliminates a class of typos.
6. **Immutable non-writable properties.** Writing to a non-writable property throws `TypeError` instead of silently failing.
7. **Restrictions on deleting.** `delete` on non-deletable properties throws, protecting language core.
8. **No octal literals.** `010` is a syntax error. Use `0o10` for octal explicitly; use `'\u0061'` instead of `'\141'` for escape sequences.

**Reach for it when:** working in non-module scripts or legacy code where strict mode isn't implicit. In ES modules, classes, and any modern tooling, strict mode is the default.

### Why doesn't `0.1 + 0.2 === 0.3`?

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

### What's the difference between `==` and `===`?

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

### What does `!!` do?

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

#### Why this matters in React

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

## 3.8 Modern JavaScript Features

Reach for this when you need a quick reference for optional chaining, nullish coalescing, destructuring, promise combinators, and other post-ES6 language additions that come up constantly in interviews. For pre-ES2020 additions (`Object.keys`, `Array.from`, etc.), see [`3.6 ES6 New Methods`](./3.6%20ES6%20New%20Methods.md).

### 1. Optional chaining (`?.`)

Short-circuits when the left-hand side is `null` or `undefined`, returning `undefined` instead of throwing.

#### Syntax

```javascript
obj?.prop
obj?.[expr]
func?.(args)
```

#### Use cases

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

### 2. Nullish coalescing (`??`)

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

### 3. Destructuring

#### Object destructuring

```javascript
const { a, b } = obj;
const { a: alias, b = 10 } = obj;   // rename + default
const { a, ...rest } = obj;         // rest pattern
```

#### Array destructuring

```javascript
const [first, second] = arr;
const [a, , c] = arr;        // skip element
const [x, ...tail] = arr;    // rest
const [a = 0, b = 0] = arr;  // defaults
```

#### Nested destructuring

```javascript
const { user: { name, address: { city } } } = data;
const [[a, b], [c, d]] = nested;
```

#### Renaming

```javascript
const { name: userName, id: userId } = user;
```

#### Rest pattern

```javascript
const { a, b, ...others } = obj;   // others = remaining props
const [head, ...rest] = arr;       // rest = remaining elements
```

---

### 4. Template literals

#### Basic interpolation

```javascript
const name = 'World';
`Hello, ${name}!`;
`2 + 2 = ${2 + 2}`;
```

#### Tagged templates

The tag function receives an array of string segments and the interpolated values. Useful for sanitization, i18n, or DSLs.

```javascript
function tag(strings, ...values) {
  return strings.reduce((acc, str, i) => acc + str + (values[i] ?? ''), '');
}
tag`Hello ${'World'}!`;  // 'Hello World!'
```

**Signature:** `tag(strings: TemplateStringsArray, ...values: any[])`

---

### 5. Promise combinators

| Method | Resolves when | Rejects when | Return type |
|---|---|---|---|
| `Promise.all` | All fulfill | Any rejects | `[results]` or first rejection |
| `Promise.allSettled` | All settle (fulfill or reject) | Never | `[{status, value?}, {status, reason?}]` |
| `Promise.any` | Any fulfills | All reject | First fulfilled value or `AggregateError` |
| `Promise.race` | First settles (either way) | First rejects | First result or first rejection |

#### Behavior on rejection

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

**See also:** [`4.3 Asynchronous JavaScript`](./4.3%20Asynchronous%20JavaScript.md) for Promise fundamentals and error handling.

---

### 6. Newer APIs

#### `globalThis`

Cross-environment reference to the global object (`window` in browsers, `global` in Node, `self` in workers).

```javascript
globalThis.setTimeout === window.setTimeout; // true in a browser
```

#### `Array.at(index)`

Index access with support for negative indices counting from the end.

```javascript
const arr = [1, 2, 3];
arr.at(0);   // 1
arr.at(-1);  // 3
arr.at(-2);  // 2
```

Cleaner than `arr[arr.length - 1]` for "last element".

#### `Object.hasOwn(obj, prop)`

Replacement for `obj.hasOwnProperty(prop)` that avoids prototype-lookup edge cases (e.g., when `obj` overrides `hasOwnProperty` or has `null` prototype).

```javascript
const o = { a: 1 };
Object.hasOwn(o, 'a');        // true
Object.hasOwn(o, 'toString'); // false
```

#### `structuredClone(value)`

Deep clone of serializable values. Handles objects, arrays, `Map`, `Set`, `Date`, typed arrays, and circular references — but **not** functions, symbols, DOM nodes, or class instances.

```javascript
const original = { a: 1, nested: { b: 2 } };
const copy = structuredClone(original);
copy.nested.b = 3;
original.nested.b; // still 2
```

Reach for it instead of `JSON.parse(JSON.stringify(x))` — it's faster, handles cycles, and preserves `Date` / `Map` / `Set`.

---

### 7. Modules

#### CommonJS vs ES Modules

| Aspect | CommonJS | ES Modules |
|---|---|---|
| Syntax | `require()`, `module.exports` | `import`, `export` |
| Loading | synchronous | asynchronous (static analysis) |
| Top-level `await` | no | yes |
| Tree-shaking | limited | supported |
| `this` at top level | `exports` | `undefined` |

#### CommonJS

```javascript
const { foo } = require('./module');
module.exports = { bar };
```

#### ES Modules

```javascript
import { foo } from './module.js';
import * as ns from './module.js';
export { bar };
export default baz;
```

#### Dynamic `import()`

Returns a Promise; use for code-splitting or conditional loading.

```javascript
const load = async () => {
  const { default: Component } = await import('./Component.js');
  return Component;
};
```

**Key differences:** `import` is static (parsed at compile time, enables tree-shaking); `import()` is dynamic and returns a Promise (enables lazy loading).

**See also:** [`7.3 Build Tools`](./7.3%20Build%20Tools.md) for module bundling strategies, [`4.3 Asynchronous JavaScript`](./4.3%20Asynchronous%20JavaScript.md) for Promises and async/await fundamentals.

# 4. Advanced Javascript


## 4.1 Object, Function, and Prototype

A bundle of classic interview questions about JavaScript's prototype system, `this`, `new`, and property descriptors.

## What is the JavaScript prototype chain?

**Headline (30s):** Every object has an internal `[[Prototype]]` link (exposed as `__proto__`) pointing to another object. When you access a property that doesn't exist on the object, the engine walks up this chain until it finds the property or reaches `null`. This is how objects inherit behavior in JavaScript — not by copying, but by linking.

**Why interviewers ask this:** Prototypes explain inheritance, `class`, `instanceof`, and why polyfills work the way they do. A candidate who can't describe the chain struggles with React class components, library internals, and debugging "where did this method come from?" questions.

### `prototype` vs. `__proto__`

Two closely related properties that trip up almost everyone:

- **`prototype`** — a property that exists *only on functions*. It's the object that will become `__proto__` of any instance created with `new`.
- **`__proto__`** — a property on *every* object. It points to the object's prototype. Reading it walks up the chain.

### How the chain is formed

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

## What's the difference between `{}` and `Object.create(proto)`?

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

## What is `this` in JavaScript?

**Headline (30s):** `this` is a special binding that is decided **at call time**, not at definition time. Its value depends on *how* a function is called: as a plain function (`fn()`), as a method (`obj.fn()`), as a constructor (`new Fn()`), or explicitly (`fn.call(ctx)`). Arrow functions are the exception — they capture `this` lexically.

**Why interviewers ask this:** It's the #1 source of bugs in hand-rolled code. Understanding `this` is prerequisite to understanding `bind`, `call`, `apply`, class methods, React class components, and event handlers.

### The rules (in precedence order)

1. **`new` binding** — `new Fn()` creates a new object, `this` is that object.
2. **Explicit binding** — `fn.call(ctx)`, `fn.apply(ctx)`, `fn.bind(ctx)` — `this` is `ctx`.
3. **Implicit binding** — `obj.fn()` — `this` is `obj`.
4. **Default binding** — `fn()` — `this` is the global object (`window`) in non-strict mode, or `undefined` in strict mode.
5. **Arrow functions** — ignore all rules above; `this` is inherited lexically from the enclosing scope.

### Examples covering each case

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

## Implement `bind` (and `call` / `apply`)

**Headline (30s):** `bind` returns a new function with a fixed `this` and optionally pre-filled arguments. `call` / `apply` invoke immediately with a given `this` — `call` takes args individually, `apply` takes an array. The classic implementation trick: `call` and `apply` temporarily attach the function as a method on the context object, invoke it, then delete it.

### `bind`

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

### `call` and `apply`

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

## How does `new` work, and how would you implement it?

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

## What are hidden classes?

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

## Why define methods on the prototype instead of in the constructor?

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

## How do static, instance, and prototype properties interact?

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

## What are property descriptors?

**Headline (30s):** Every property on an object has a set of *attributes* (configurable, enumerable, writable, value/get/set) that control its behavior. `Object.defineProperty` lets you set them explicitly. This is how libraries implement read-only properties, computed getters, and non-enumerable "internal" fields.

### Data properties

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

### Accessor properties (`get` / `set`)

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

### Inspecting descriptors

```javascript
Object.getOwnPropertyDescriptor(obj, 'name');
// { value: 'John', writable: false, enumerable: true, configurable: true }
```

**Reach for this when:** implementing reactive frameworks (Vue 2 used `defineProperty` pre-Proxy), enforcing API contracts (read-only IDs), or making fields non-enumerable so they don't leak in logs.

**See also:** [`4.2 Scope & Closure`](./4.2%20Scope%20%26%20Closure.md) for how `this` interacts with scope, [`3.2 JavaScript Types`](./3.2%20Javascript%20Types.md) for primitive vs. reference fundamentals.

## 4.2 Scope & Closure

### What is scope in JavaScript?

**Headline (30s):** Scope is the set of rules that determines *where* a variable is accessible. JavaScript has four scopes layered from broad to narrow: **global**, **module**, **function (local)**, and **block**. When you reference a variable, the engine walks outward through the enclosing scopes until it finds the name or throws `ReferenceError`.

**Why interviewers ask this:** Scope explains almost every "why is this variable `undefined`?" bug. Combined with hoisting and closures, it's foundational knowledge for debugging, module design, and understanding framework internals.

#### Global scope

Declared at the top of a script, outside any function or block. In browsers, `var` and function declarations at the global level become properties of `window`.

```javascript
var globalVar = 'everywhere';
console.log(globalVar);      // 'everywhere'
console.log(window.globalVar); // 'everywhere' (browser, non-module script)
```

Anything on `window` is implicit global state — the usual reason to avoid it. Modules fix this by making the top level module-scoped, not global.

#### Module scope

With ES modules (`<script type="module">` or `.mjs` / bundler-processed files), top-level declarations are scoped to the module — they don't leak to `window`.

#### Function scope

`var` declarations (and function declarations) are scoped to the nearest enclosing function, regardless of blocks.

```javascript
function f() {
  var x = 1;
}
console.log(x); // ReferenceError
```

#### Block scope

`let` and `const` are scoped to the nearest `{}` — `if`, `for`, `while`, or any lone block. `var` ignores blocks.

```javascript
if (true) {
  let inBlock = 'only here';
  var outOfBlock = 'leaks up';
}
console.log(outOfBlock); // 'leaks up'
console.log(inBlock);    // ReferenceError
```

**Reach for `let` / `const`** to avoid hoisting and block-scope surprises. See [`3.1 JavaScript Basics`](./3.1%20Javascript%20Basics.md) for the full comparison.

#### Lexical scope (scope chain)

Scope is determined by *where functions are defined*, not where they're called. An inner function can read variables from any enclosing scope — this is the scope chain.

```javascript
const globalVar = 'g';

function outer() {
  const outerVar = 'o';

  function inner() {
    const innerVar = 'i';
    console.log(globalVar, outerVar, innerVar); // 'g o i'
  }

  inner();
}
outer();
```

Lookup order: `inner` → `outer` → global → `ReferenceError`.

---

### What is a closure?

**Headline (30s):** A closure is a function bundled with a reference to the scope where it was defined. When you return or pass a function out of its defining scope, it still holds live references to the variables it used — those variables survive as long as the closure survives. Closures are how you create private state, factories, and per-instance behavior in JavaScript.

**Why interviewers ask this:** Closures are involved in every nontrivial React hook, every module with private state, and every "why does this loop capture the wrong value?" puzzle. Describing them clearly signals comfort with the language at a deep level.

#### The mental model

```javascript
function makeGreeter(name) {
  return function greet() {
    console.log(`Hello, ${name}`);
  };
}

const greetAlice = makeGreeter('Alice');
greetAlice(); // 'Hello, Alice' — `name` still accessible even though makeGreeter returned long ago
```

`greet` closes over `name`. As long as a reference to `greet` is alive, the engine keeps that `name` slot in memory.

#### Common use cases

**1. Private state**

```javascript
function makeCounter() {
  let count = 0;
  return {
    increment() { count++; return count; },
    decrement() { count--; return count; },
    value()     { return count; }
  };
}

const c = makeCounter();
c.increment(); // 1
c.increment(); // 2
c.count;       // undefined — `count` is not a property
```

Each call to `makeCounter` creates a fresh `count` — different instances don't share state.

**2. Partial application / factories**

```javascript
function multiplyBy(factor) {
  return (n) => n * factor;
}

const double = multiplyBy(2);
const triple = multiplyBy(3);
double(5); // 10
triple(5); // 15
```

**3. Event handlers with captured state**

```javascript
function attachLogger(elementId, label) {
  document.getElementById(elementId).addEventListener('click', () => {
    console.log(`Clicked: ${label}`);
  });
}

attachLogger('btn1', 'primary');
attachLogger('btn2', 'secondary');
```

Each handler captures its own `label`.

#### The classic loop gotcha

```javascript
// Using `var` — all handlers log 5
for (var i = 0; i < 5; i++) {
  setTimeout(() => console.log(i), 100);
}

// Fix 1: use `let` (block-scoped — a new `i` per iteration)
for (let i = 0; i < 5; i++) {
  setTimeout(() => console.log(i), 100); // 0 1 2 3 4
}

// Fix 2 (pre-ES6): IIFE captures the current value
for (var i = 0; i < 5; i++) {
  (function (i) {
    setTimeout(() => console.log(i), 100);
  })(i);
}
```

With `var`, there's **one** `i` shared by every iteration — by the time the timers fire, the loop has finished and `i` is `5`. `let` creates a fresh `i` per iteration, so each closure captures a different slot.

**Gotcha — closures and memory:** A closure keeps its entire enclosing scope alive, even variables it doesn't use (engines optimize this but don't rely on it). Holding onto large objects (DOM nodes, big arrays) via closures is a classic memory leak. When you're done with a closure, drop the reference.

**Modern garbage collection note:** Modern browsers use mark-and-sweep GC, so the old IE-era leak patterns are mostly gone — but you can still create leaks by adding closures as listeners and forgetting to remove them.

---

### Practical summary

- Use `let` / `const` (block-scoped) to keep scope tight and avoid hoisting surprises.
- Use closures intentionally for private state, factories, and per-instance callbacks.
- Beware loops with `var` and asynchronous callbacks — the classic capture bug.
- Remember: a closure's scope is decided *when the function is defined*, not when it's called.

**See also:** [`3.1 JavaScript Basics`](./3.1%20Javascript%20Basics.md) for `var` / `let` / `const` scope semantics, [`4.1 Object, Function, and Prototype`](./4.1%20Object%2C%20Function%2C%20and%20Prototype.md) for how `this` differs from scope.

## 4.3 Asynchronous JavaScript

### Why did JavaScript evolve from callbacks to Promises to `async/await`?

**Headline (30s):** JavaScript is single-threaded — it can't block while waiting for I/O, so every async API has to defer completion. The three generations of async APIs (callbacks → Promises → `async/await`) are all attempts to solve the same problem: *how to express "do this, then that, then that" without creating unreadable spaghetti*. Each generation is strictly more expressive than the last; `async/await` is today's answer.

**Why interviewers ask this:** Async handling is the #1 source of production bugs in frontend code. Interviewers want to see that you can reason about control flow, error propagation, and concurrency — not just memorize `.then()`.

---

### Callbacks — the original async pattern

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

#### Why callbacks hurt: callback hell

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

### Promises — the composable abstraction

**Headline:** A Promise is an object representing a future value — it's in one of three states (`pending`, `fulfilled`, `rejected`), and once settled it never changes. Chaining via `.then()` flattens nested callbacks and gives you a single error channel via `.catch()`.

#### States

- **Pending** — initial; the operation is still running.
- **Fulfilled** — completed successfully, with a value.
- **Rejected** — failed, with a reason (usually an Error).

Once fulfilled or rejected, the state is locked. A rejected promise cannot later resolve; a fulfilled one cannot later fail.

#### Creating and consuming a Promise

```javascript
const promise = new Promise((resolve, reject) => {
  setTimeout(() => resolve('Success!'), 1000);
});

promise.then(value => console.log(value)); // 'Success!' after 1s
```

#### Prototype methods

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

#### Static methods (combinators)

Summary: see [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for the comparison table. Short version:

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

### `async` / `await` — syntactic sugar that looks synchronous

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

#### Sequential vs. parallel with `await` — the trap

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

#### `for await...of`

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

### Microtasks: why this logs `0 2 1 3`

**Headline:** Every `.then()` callback is scheduled as a *microtask*. The event loop drains the entire microtask queue between tasks (and between rendering frames). When two promise chains exist in parallel, their `.then()` callbacks interleave round-robin.

```javascript
Promise.resolve().then(() => console.log(0)).then(() => console.log(1));
Promise.resolve().then(() => console.log(2)).then(() => console.log(3));
// 0 2 1 3
```

Walk-through: both chains' first `.then()` are queued right away. After `0` runs, its second `.then()` gets queued — but chain 2's first `.then()` is already ahead of it.

#### Returning a Promise from `.then()` adds ticks

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

**See also:** [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for the full microtask / macrotask model.

---

### Function patterns: currying

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

### Interview-favorite: implement `LazyMan` (chainable async task queue)

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

### Arrow functions: four things they can't do

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

### Classic gotcha: `['1', '2', '3'].map(parseInt)`

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

**See also:** [`4.5 Error Handling`](./4.5%20Error%20Handling.md) for error handling patterns with Promises and async/await, [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for Promise combinator comparison, [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for the microtask scheduling model.

## 4.4 Iterators and Generators

### What's the iteration protocol, and why does it matter?

**Headline (30s):** JavaScript defines two protocols — **iterable** and **iterator** — that any object can implement to participate in `for...of`, spread (`...`), destructuring, and `Array.from`. A generator is a function that implements both protocols automatically via `yield`. Understanding the protocol is the key to building custom data structures that "just work" with the language's iteration features.

**Why interviewers ask this:** It's the mechanism behind `for...of`, spread syntax, async iteration, and tree/graph traversal patterns. A candidate who can implement a custom iterable shows they understand the language at the protocol level, not just as a collection of built-ins.

---

### Iterable and iterator protocols

#### Iterable

An object is iterable if it has a `[Symbol.iterator]` method that returns an iterator. Built-in iterables: **Array, String, Map, Set, TypedArray, `arguments`, NodeList**. Plain objects are *not* iterable by default.

#### Iterator

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

#### Building a custom iterable

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

### Generators — iterators with cleaner syntax

**Headline (30s):** A generator function (`function*`) returns a generator object — an iterator that's also iterable. Inside the function, `yield` pauses execution and emits a value; the next call to `.next()` resumes from the paused point. The engine automatically manages all the state that a hand-written iterator would have to track manually.

#### Declaration and basic use

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

#### Passing values *into* a generator

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

#### `yield*` — delegating to another iterable

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

### Practical use cases

#### Lazy evaluation of infinite sequences

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

#### Unique ID factory

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

#### Historical note: async flow control

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

### Generators vs. hand-written iterators

| Feature | Custom iterator | Generator |
|---|---|---|
| Syntax | Manual `next()` method | `function*` with `yield` |
| State management | Manual (closure variables) | Automatic (execution paused/resumed) |
| Code complexity | Higher for non-trivial sequences | Simpler and more readable |
| Bidirectional data | Not built-in | `next(value)` passes data in |
| Early termination | Manual `return()` method | Built-in `return()` and `throw()` |

**Reach for generators when:** the sequence has interesting control flow (branching, recursion via `yield*`, infinite streams). Use a hand-written iterator only when you need to precisely control memory layout or can't use generator syntax.

**See also:** [`3.5 Array in JS`](./3.5%20Array%20in%20JS.md) for `for...of` vs `for...in` semantics, [`4.3 Asynchronous JavaScript`](./4.3%20Asynchronous%20JavaScript.md) for `for await...of` and async iteration.

## 4.5 Error Handling

### How should you handle errors in modern JavaScript?

**Headline (30s):** There are five layers to cover — synchronous `try/catch/finally`, custom error classes, promise rejection handling (`.catch` / `try/await`), global handlers (`onerror` / `unhandledrejection`), and framework-level boundaries (React error boundaries). A production app needs *all of them*, because each only catches a specific category of error.

**Why interviewers ask this:** Error handling separates candidates who've shipped to production from those who haven't. Interviewers want to see that you know *which* tool to reach for, that you propagate (not swallow) errors, and that you understand the async-vs-sync distinction.

---

### `try / catch / finally` — synchronous errors

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

### Custom error classes

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

### Promise rejection handling

#### `.catch()` on chains

```javascript
fetch('/api/data')
  .then(res => res.json())
  .catch(err => console.error('Fetch failed:', err))
  .then(data => process(data)); // runs even after catch — with `undefined` if catch ran
```

Two things to know:

1. A `.catch()` returns a *resolved* promise unless it rethrows — subsequent `.then()` calls still run.
2. To stop a chain after a caught error, rethrow or `return Promise.reject(...)` from the `.catch`.

#### `try / catch` around `await`

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

#### Unhandled rejection = silent failure

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

### Global error handlers — your last line of defense

#### `window.onerror` — uncaught synchronous errors

```javascript
window.onerror = function (message, source, lineno, colno, error) {
  logToMonitoring({ message, source, lineno, colno, stack: error?.stack });
  return true; // suppress default browser error UI
};
```

- Returns `true` to suppress the default console output.
- **Cross-origin gotcha:** Scripts loaded from another origin (a CDN, typically) yield `"Script error."` with no stack trace due to CORS. Fix: serve the script with a permissive CORS header and add `crossorigin="anonymous"` to the `<script>` tag.

#### `window.addEventListener('unhandledrejection')`

Catches promise rejections that weren't handled by `.catch` or `try/catch`.

```javascript
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled rejection:', event.reason);
  event.preventDefault(); // suppress console warning
});
```

- `event.reason` — the rejection reason (usually an Error).
- `event.promise` — the rejected promise itself.

#### `window.addEventListener('error')` (capture phase) — resource load errors

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

### React error boundaries

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

#### What error boundaries do **not** catch

- **Event handler errors** — the handler is called from DOM event dispatch, not React's render pipeline. Wrap in `try/catch`.
- **Async code** (`setTimeout`, `fetch.then`, `await` inside `useEffect`). Wrap in `try/catch`.
- **Server-side rendering errors** — the SSR renderer throws directly.
- **Errors thrown inside the boundary itself** — bubble up to a parent boundary.

#### Function components

There's no hook equivalent. Use the community library `react-error-boundary`:

```jsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary fallback={<div>Error!</div>} onError={logError}>
  <MyComponent />
</ErrorBoundary>
```

**Reach for error boundaries when:** rendering third-party components, dynamic content from user input, or async-loaded modules — anywhere a render error shouldn't take down the whole page.

---

### Defense in depth — which layer catches what?

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

**See also:** [`4.3 Asynchronous JavaScript`](./4.3%20Asynchronous%20JavaScript.md) for Promises and `async/await` fundamentals, [`9.2 React Basics`](./9.2%20React%20Basics.md) for the React lifecycle context around error boundaries.

# 5. DOM & Browser APIs


## 5.1 DOM Manipulation and Events

A bundle of interview questions around DOM events, runtime scheduling, and utility patterns that commonly come up.

## How do you write a proper deep copy?

**Headline (30s):** `JSON.parse(JSON.stringify(obj))` is the one-liner — cheap, often good enough, but silently wrong for anything beyond plain objects and primitives. A robust deep copy needs to dispatch on type (`Date`, `RegExp`, `Map`, `Set`, `Array`, plain object), recurse, and use a `WeakMap` to break circular references. Modern code can reach for `structuredClone` for built-in support.

**Why interviewers ask this:** It tests your grasp of reference semantics, edge cases (cycles, special types), and whether you can design a recursive function with proper memoization.

### Why `JSON.parse(JSON.stringify(x))` is insufficient

- **Lost types:** `Map`, `Set`, `Date`, `RegExp` become plain objects or strings.
- **Circular references:** `JSON.stringify` throws.
- **Missing values:** `undefined`, functions, and symbols are stripped.

Reach for `structuredClone(value)` (see [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md)) — it handles all of the above natively. Use a handwritten deep copy only when you need to customize behavior (e.g., skip certain keys).

### Handwritten deep copy

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

## How do DOM events propagate?

**Headline (30s):** Every DOM event travels through three phases: **capture** (from root down to target), **target** (at the element), then **bubble** (back up to root). Most listeners run in the bubble phase by default. Bubbling enables *event delegation* — one listener on a parent handles events from many children, which is how React implements its event system.

### The three phases

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

### Event delegation

Don't attach 1000 listeners to 1000 list items — attach one to the parent and match on the target.

```javascript
parent.addEventListener('click', (e) => {
  const item = e.target.closest('.item');
  if (!item) return;
  console.log('Item clicked:', item.textContent);
});
```

Benefits: fewer listeners (lower memory), works for dynamically added children (no rebinding).

### React's synthetic event system

React implements event delegation at the root container: a single listener catches every click, then dispatches to the right component. The event object you receive is a **SyntheticEvent** — a cross-browser wrapper around the native event.

Handler naming:

- `onClick` — bubble phase (default).
- `onClickCapture` — capture phase.

**Gotcha — SyntheticEvent pooling (React ≤ 16):** In older React versions, the event object was reused; accessing `e.target` inside `setTimeout` returned `null`. Fixed in React 17+. If you hit this in legacy code, call `e.persist()`.

---

## Implement an EventBus / EventEmitter

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

## Observer pattern vs. Publish-Subscribe

**Headline (30s):** Both are reactive messaging patterns, but they differ in coupling. **Observer**: the subject knows its observers directly (DOM events, RxJS subjects). **Publish-Subscribe**: a broker (event bus) sits between, so publishers and subscribers don't know about each other. Pub-Sub is more decoupled but harder to debug because the flow is indirect.

### Observer

```javascript
button.addEventListener('click', handleClick);
// button knows it has a listener called handleClick
```

The subject (`button`) maintains a list of observers and notifies them directly.

### Publish-Subscribe

```javascript
eventBus.on('user:login', updateUI);
eventBus.emit('user:login', { name: 'Alice' });
// Neither `updateUI` nor the emitter knows about each other
// The eventBus is the mediator
```

A topic string names the event channel; anyone can publish, anyone can subscribe.

**Rule of thumb:** Use Observer when there's a natural "owner" of the event (a DOM node, a data model). Use Pub-Sub when you want to decouple modules that shouldn't import each other.

---

## `requestAnimationFrame` vs. `requestIdleCallback` — when do you use each?

**Headline (30s):** `requestAnimationFrame` runs your callback right before the next repaint (~every 16ms at 60fps) — perfect for animation and visual updates. `requestIdleCallback` runs during leftover time at the end of a frame — perfect for *non-urgent* work (analytics, prefetching) that shouldn't compete with user input or rendering.

### `requestAnimationFrame`

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

### `requestIdleCallback`

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

## Finding the maximum in an array — which technique is safe for huge arrays?

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

**See also:** [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md) for Intersection Observer (the modern replacement for scroll-event DOM watchers), [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for the task/microtask scheduling model that rAF and rIC sit inside.

## 5.2 Browser Storage and Communication

A bundle of interview questions about storing data in the browser and sending messages between tabs, iframes, and native shells.

## What's the difference between `localStorage`, `sessionStorage`, and cookies?

**Headline (30s):** All three store client-side data, but differ in capacity, lifetime, and whether the server sees them. `localStorage` persists indefinitely, `sessionStorage` is per-tab, both are client-only (never sent in requests). **Cookies** are tiny (~4KB) but automatically included in every HTTP request, which is why authentication lives there. Pick based on *who needs to read the data* (server vs. client) and *how long it should live*.

**Why interviewers ask this:** This comes up in any question about auth flows, session management, or persistence. Candidates who conflate the three write insecure auth code.

### `localStorage`

- **Capacity:** ~5MB per origin.
- **Lifetime:** persists until cleared by script or user.
- **Access:** synchronous, same-origin, client-only (never sent in HTTP requests).
- **Use for:** user preferences (theme, language), cached client state, offline data.

### `sessionStorage`

Identical API, tab-scoped lifetime.

- **Capacity:** ~5MB per origin.
- **Lifetime:** cleared when the tab closes (survives reloads).
- **Access:** synchronous, same-origin, tab-isolated.
- **Use for:** multi-step form state, wizard progress, temporary SPA state.

### Cookies

- **Capacity:** ~4KB per cookie, ~20 cookies per domain.
- **Lifetime:** configurable with `Expires` / `Max-Age`; session cookies die with the browser.
- **Access:** sent with every HTTP request to the matching domain; readable via `document.cookie` unless `HttpOnly`.
- **Security flags:** `HttpOnly` (blocks JS access), `Secure` (HTTPS only), `SameSite=Strict|Lax|None` (CSRF protection).
- **Use for:** session IDs, CSRF tokens, server-side personalization.

### Quick comparison

| Feature | localStorage | sessionStorage | Cookies |
|---|---|---|---|
| Capacity | ~5MB | ~5MB | ~4KB |
| Sent with requests | No | No | Yes |
| Lifetime | Permanent | Tab session | Configurable |
| Server access | No | No | Yes |
| Accessible to JS | Yes | Yes | Only without `HttpOnly` |

**Gotcha — don't store auth tokens in `localStorage`:** Anything in `localStorage` is readable by any script on the page. An XSS vulnerability becomes a full account takeover. Use `HttpOnly` + `Secure` + `SameSite` cookies for session tokens.

**See also:** [`8.2 Web Security and Authentication`](./8.2%20Web%20Security%20and%20Authentication.md) for XSS/CSRF mitigation and cookie flag deep dives.

---

## `HTMLCollection` vs. `NodeList` — what's the difference?

**Headline (30s):** Both are array-like collections of DOM nodes, but differ in what they contain and how they update. **`HTMLCollection`** holds only `Element` nodes and is **always live** — it reflects DOM changes automatically. **`NodeList`** can hold any node type (Elements, Text, Comments). It's **usually static** (from `querySelectorAll`) but occasionally live (`childNodes`).

### `HTMLCollection`

- Returned by `getElementsByClassName`, `getElementsByTagName`, `.children`.
- Contains only `Element` nodes.
- Always live — queries re-run on each access.

### `NodeList`

- Returned by `querySelectorAll` (static), `childNodes` (live).
- Can contain any node type: `Element`, `Text`, `Comment`.
- Static or live depending on source.

### `.children` vs `.childNodes`

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

## How can tabs of the same origin communicate?

**Headline (30s):** Four main options, roughly in order of complexity. For most same-origin cases, **`BroadcastChannel`** is the cleanest modern answer. The `localStorage` + `storage` event trick works everywhere but feels hacky. `SharedWorker` is powerful but has Safari caveats. `WebSocket` through a server is the only cross-origin option.

### 1. `localStorage` + `storage` event

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

### 2. `BroadcastChannel` API

Purpose-built for same-origin tab messaging. Much cleaner than the storage hack.

```javascript
const channel = new BroadcastChannel('app_channel');

// Listen
channel.onmessage = (e) => console.log('Received:', e.data);

// Send
channel.postMessage({ type: 'update', payload: { id: 1 } });
```

Supported in all modern browsers. First choice for new code.

### 3. `SharedWorker`

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

### 4. WebSockets (cross-origin or real-time)

When tabs need to share updates with a server too (chat, collaborative editing), all tabs connect to the same WebSocket; the server broadcasts.

**Rule of thumb:** Same-origin, simple → `BroadcastChannel`. Same-origin, broad support → `localStorage` + `storage` event. Cross-origin or server-driven → WebSocket.

---

## How do you communicate with an iframe?

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

## What's a JS-Bridge, and how does it work?

**Headline (30s):** A JS-Bridge is a communication layer between native mobile code and JavaScript running inside a `WebView`. Web content is sandboxed and can't call native APIs directly, so the bridge routes calls through one of two mechanisms: **URL-scheme hijacking** (the iframe-src trick) or **global API injection** (the native app exposes functions on `window`). Modern apps usually use global injection for sync calls and URL schemes for legacy support.

### URL scheme method

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

### Global API injection

The native side evaluates JavaScript into the WebView to expose functions on `window`:

```javascript
// Native injects window.NativeBridge beforehand
const version = window.NativeBridge.getVersion();
window.NativeBridge.requestLocation((loc) => console.log(loc));
```

Feels like normal JS — synchronous or callback-based depending on what the native side supports.

**Reach for it when:** building a hybrid app (WebView + native shell). For pure web, use standard browser APIs (`navigator.geolocation`, etc.).

**Gotcha — security:** Never trust data coming from the web side. The bridge can be invoked by any page loaded in the WebView — including malicious ones — unless you restrict the allowed origins.

**See also:** [`1.1 Browser Basics`](./1.1%20Browser%20Basics.md) for where storage and messaging fit into the browser architecture, [`8.2 Web Security and Authentication`](./8.2%20Web%20Security%20and%20Authentication.md) for auth storage and CSRF concerns.

## 5.3 Image Lazy Loading

### How do you lazy-load images in the browser?

**Headline (30s):** Three techniques, in order of preference: (1) the native `loading="lazy"` HTML attribute — one line, no JS; (2) the `IntersectionObserver` API for anything the native attribute can't cover; (3) throttled scroll-event listeners as a last-resort legacy fallback. Modern sites use the native attribute as the default, with an `IntersectionObserver` fallback for older browsers.

**Why interviewers ask this:** It's a common real-world perf question and a great filter for "do you know modern browser APIs or are you still writing jQuery-era scroll listeners?" The follow-up usually digs into CLS (Cumulative Layout Shift) and how to avoid jank when images pop in.

---

### 1. Native lazy loading (preferred)

Modern browsers (Chrome, Edge, Firefox, Safari 15.4+) support the `loading` attribute on `<img>` and `<iframe>`:

```html
<img src="image.jpg" alt="Description" loading="lazy" width="800" height="600">
```

Values:

- `lazy` — defer loading until the image approaches the viewport.
- `eager` — load immediately (default).
- `auto` — let the browser decide.

**Why this is the first choice:**

- Zero JavaScript, zero bundle cost.
- The browser knows best when to prefetch (it considers connection speed, device memory, user preferences).
- Tested and optimized by browser vendors.

**Always include `width` and `height`:** they reserve space before the image loads, preventing Cumulative Layout Shift (CLS) when the image pops in.

---

### 2. `IntersectionObserver` (JS fallback / more control)

When you need behaviors the native attribute doesn't cover — custom thresholds, background images, non-`<img>` elements — use `IntersectionObserver`. It efficiently reports when elements enter or leave the viewport *without* firing a callback on every scroll event.

```html
<img src="placeholder.png" data-src="actual-image.jpg" alt="Description">
```

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);    // stop observing once loaded
    }
  });
}, {
  rootMargin: '200px' // start loading 200px before entering the viewport
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});
```

**Key options:**

- **`rootMargin`** — expand the "viewport" by N pixels so images start loading before they're visible. `'200px'` is a good default for fast connections; shrink it on slow networks.
- **`threshold`** — how much of the element must be visible to trigger. `0` (default) fires as soon as any pixel is visible; `1` waits until fully visible.

**Why `IntersectionObserver` beats scroll listeners:** the browser does the visibility calculation off the main thread and batches callbacks. Scroll handlers run on every scroll event and force layout reads.

---

### 3. Scroll + throttle (legacy fallback only)

For environments without `IntersectionObserver` (rare today — IE only), throttle a scroll listener and check `getBoundingClientRect()`.

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

window.addEventListener('scroll', throttle(() => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    if (img.getBoundingClientRect().top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    }
  });
}, 100));
```

**Gotcha — `getBoundingClientRect()` forces layout:** Calling it inside a scroll handler makes every scroll tick expensive. This is why `IntersectionObserver` won.

---

### Performance: don't trade loading speed for layout jank

Lazy-loading images is great — unless you introduce layout shift every time one appears. Rules to follow:

- **Load above-the-fold images eagerly** (`loading="eager"` or omit the attribute). If the user can see it on first paint, don't lazy-load it.
- **Always reserve space** with explicit `width` / `height` attributes or CSS `aspect-ratio`. Without these, the page jumps when the image arrives — hurting CLS (a Core Web Vital).
- **Combine with `srcset` + modern formats** (WebP, AVIF). Lazy-loading an over-sized JPEG still wastes bandwidth.
- **Use a placeholder** (low-quality image placeholder, LQIP, or a solid color) so the user sees something while the real image loads.

```html
<img
  src="placeholder.webp"
  data-src="full.webp"
  srcset="full-400.webp 400w, full-800.webp 800w, full-1600.webp 1600w"
  sizes="(max-width: 600px) 100vw, 50vw"
  loading="lazy"
  width="800"
  height="600"
  alt="...">
```

**Rule of thumb:**

1. Start with `loading="lazy"` + correct `width` / `height`.
2. Layer an `IntersectionObserver` fallback if you need to support older Safari or non-`<img>` elements.
3. Profile CLS and Largest Contentful Paint after — lazy-loading the wrong images makes both worse.

**See also:** [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md) for Core Web Vitals and broader image-perf strategies, [`5.1 DOM Manipulation and Events`](./5.1%20DOM%20Manipulation%20and%20Events.md) for `IntersectionObserver` in other use cases.

# 6. TypeScript


## 6.1 Advanced TypeScript

A bundle of interview questions about TypeScript's more powerful features — utility types, generics, `Proxy`, and decorators.

## What are TypeScript utility types, and when do you use them?

**Headline (30s):** Utility types are built-in generic type transformers that save you from hand-writing common variations (`Partial<T>`, `Pick<T, K>`, `Omit<T, K>`, etc.). They compose — `Partial<Pick<User, 'name' | 'email'>>` is a valid, readable expression. Knowing them is the difference between a TS developer who copy-pastes interface fields and one who writes maintainable types.

**Why interviewers ask this:** Every medium-size TS codebase relies on utility types. Fluency with them signals you can *design* types, not just annotate variables.

### Transforming object types

| Utility | Does what |
|---|---|
| `Partial<T>` | All properties optional |
| `Required<T>` | All properties required (opposite of `Partial`) |
| `Readonly<T>` | All properties read-only |
| `Pick<T, Keys>` | Subset of properties |
| `Omit<T, Keys>` | All properties except the listed ones |
| `Record<Keys, T>` | Object type with specified keys and value type |

```typescript
interface User { id: number; name: string; email: string; }

// Partial — useful for PATCH payloads
function updateUser(user: Partial<User>) { /* ... */ }
updateUser({ name: 'Alice' }); // valid, even though id/email are missing

// Readonly — useful for props or frozen state
const user: Readonly<User> = { id: 1, name: 'Alice', email: 'a@b.com' };
user.name = 'Bob'; // Error: Cannot assign to 'name'

// Pick / Omit — subsetting
type UserPreview = Pick<User, 'id' | 'name'>;
type UserWithoutEmail = Omit<User, 'email'>;

// Record — dictionary typed by a union of keys
type Role = 'admin' | 'user' | 'guest';
const permissions: Record<Role, string[]> = {
  admin: ['read', 'write', 'delete'],
  user:  ['read', 'write'],
  guest: ['read']
};
```

### Transforming union types

| Utility | Does what |
|---|---|
| `Exclude<Union, X>` | Remove members of `X` from `Union` |
| `Extract<Union, X>` | Keep only members that match `X` |
| `NonNullable<T>` | Remove `null` and `undefined` |

```typescript
type A = Exclude<'a' | 'b' | 'c', 'a'>;        // 'b' | 'c'
type B = Extract<'a' | 'b' | 'c', 'a' | 'b'>;  // 'a' | 'b'
type C = NonNullable<string | null | undefined>; // string
```

### Extracting from functions and classes

| Utility | Does what |
|---|---|
| `ReturnType<T>` | Return type of a function |
| `Parameters<T>` | Parameters of a function as a tuple |
| `InstanceType<T>` | Instance type of a class constructor |
| `ConstructorParameters<T>` | Constructor parameters as a tuple |

```typescript
function getUser() { return { id: 1, name: 'Alice' }; }

type User = ReturnType<typeof getUser>;   // { id: number; name: string }
type P    = Parameters<typeof getUser>;   // []
```

**Reach for them when:** deriving a type from an existing source of truth (an API function, another type) instead of duplicating the shape. The `typeof` operator in type position + `ReturnType` is the power combo.

---

## How do generics work in TypeScript?

**Headline (30s):** Generics let you write functions and types that work for *any* type while still preserving type safety. A generic function takes a type parameter (`<T>`) that gets filled in at call site — either explicitly (`identity<string>('hi')`) or inferred (`identity(42)` → `T = number`). Constraints (`extends`) narrow what `T` can be.

### The basics

```typescript
function identity<T>(value: T): T {
  return value;
}

identity<string>('hello'); // T = string
identity(42);              // T = number (inferred)
```

Without generics, you'd have to write `identity(value: any): any` — which tells the type checker nothing.

### Constraints with `extends`

Restrict `T` to types that have certain properties. The classic example: a property-access helper.

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: 'Alice', age: 30 };
getProperty(user, 'name');  // string
getProperty(user, 'phone'); // Error: 'phone' is not a key of user
```

`K extends keyof T` says "K must be one of the keys of T". The return type `T[K]` picks out the property type for that key — so `getProperty(user, 'name')` is known to return `string`, not `any`.

### Generic interfaces and classes

```typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}

class UserRepository implements Repository<User> {
  getById(id: string): User { /* ... */ }
  getAll(): User[] { /* ... */ }
  save(user: User): void { /* ... */ }
}
```

Once you pin `T = User`, every method signature resolves automatically.

**Reach for generics when:** a function or type logic is identical across multiple types but you still want to preserve the specific type at each call site. If you find yourself writing `any`, try a generic first.

**Gotcha — default type parameters:** `function f<T = string>(x: T) {}` gives `T` a default when you don't pass one. Useful for API ergonomics.

---

## What is `Proxy`, and when do you use it?

**Headline (30s):** A `Proxy` wraps an object and intercepts fundamental operations on it — property reads, writes, deletions, enumeration, and more. You provide a handler object with "traps" (`get`, `set`, `deleteProperty`, `has`, ...) that run when those operations happen. `Proxy` is how modern reactive frameworks (Vue 3) implement observable state and how validators / debuggers add cross-cutting behavior without changing call sites.

### Basic usage

```javascript
const handler = {
  get(target, prop) {
    console.log(`Accessing ${prop}`);
    return Reflect.get(target, prop);
  },
  set(target, prop, value) {
    console.log(`Setting ${prop} = ${value}`);
    return Reflect.set(target, prop, value);
  }
};

const data = new Proxy({ count: 0 }, handler);
data.count;     // logs: Accessing count
data.count = 1; // logs: Setting count = 1
```

The `Reflect.*` helpers are the canonical way to forward the operation to the underlying target — they always do the default thing for that trap.

### Use cases

- **Change detection** (reactivity) — re-render UI when any property changes.
- **Validation** — throw if `value` doesn't pass a schema check.
- **Logging / debugging** — trace every access in a development wrapper.
- **Default values** — return a computed fallback when a property is `undefined`.
- **Read-only wrappers** — throw from `set` / `deleteProperty` to make an object tamper-proof.

### `Object.defineProperty` vs. `Proxy`

Vue 2 used `Object.defineProperty` to define getters/setters on every property of an observed object. Vue 3 switched to `Proxy`. Why?

| | `Object.defineProperty` | `Proxy` |
|---|---|---|
| What it covers | Per-property getters/setters | Whole-object operations |
| Added properties | Not tracked (need `Vue.set`) | Tracked automatically |
| Arrays | Needs array-method patching | Handled natively |
| Browser support | IE9+ | IE not supported |
| Performance (large objects) | Many getters, slow setup | Single proxy wrapper |

**Interview-flavored brainteaser using `defineProperty`:**

```javascript
Object.defineProperty(window, 'a', {
  get() {
    this.value = this.value || 0;
    return ++this.value;
  }
});

console.log(a === 1 && a === 2 && a === 3); // true
```

Every read of `a` runs the getter and returns a new incremented value, so the three comparisons each see `1`, `2`, `3` respectively.

**Reach for `Proxy` when:** building frameworks, instrumentation, or APIs that need behavior woven into many properties. Avoid for hot paths — proxy calls are measurably slower than direct access.

---

## What are decorators, and what are they for?

**Headline (30s):** Decorators are functions that attach metadata or modify behavior at *declaration time* — on classes, methods, or properties. The `@decorator` syntax is syntactic sugar for "call this function with the target at class-creation time". Frameworks like Angular, NestJS, and TypeORM use decorators for dependency injection, routing, and ORM annotations. It's the TypeScript/JS take on Aspect-Oriented Programming.

### Method decorator

Wrap a method with cross-cutting behavior (logging, caching, timing):

```typescript
function log(target: any, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`Calling ${key} with`, args);
    return original.apply(this, args);
  };
}

class Calculator {
  @log
  add(a: number, b: number) { return a + b; }
}

new Calculator().add(1, 2); // logs: Calling add with [1, 2]
```

The decorator receives:

1. `target` — the class prototype (for instance methods) or constructor (for static).
2. `key` — the method name.
3. `descriptor` — the property descriptor. Mutating `descriptor.value` replaces the method.

### Class decorator

Run code at class creation, add metadata, or even replace the class:

```typescript
function sealed(constructor: Function) {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

@sealed
class Greeter { /* instances / prototype can't have properties added or removed */ }
```

### Where decorators show up in practice

- **Angular** — `@Component`, `@Injectable`, `@Input`, `@Output`.
- **NestJS** — `@Controller`, `@Get('/users')`, `@Body()`.
- **TypeORM** — `@Entity`, `@Column`, `@OneToMany`.
- **MobX** — `@observable`, `@action`.

**Reach for them when:** you're building or using a framework that's designed around them. Don't invent decorator-heavy patterns in a plain TS app — regular composition is usually clearer.

**Gotcha — stage 3 vs. legacy decorators:** The decorator proposal has been through multiple iterations. TypeScript's `experimentalDecorators` flag enables the *legacy* (stage 1) syntax. Modern TS (5.0+) also supports the *standard* (stage 3) syntax, which has a different signature. Framework code is usually legacy; new library code should target stage 3.

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](./3.4%20Memory%20in%20JS%2C%20WeakMap%20and%20WeakSet.md) for how reactive proxies interact with GC, [`9.2 React Basics`](./9.2%20React%20Basics.md) for TS patterns common in React codebases.

# 7. Event Loop & Runtime


## 7.1 Event Loop

### How does JavaScript run asynchronous code on a single thread?

**Headline (30s):** JavaScript has one thread and one call stack — it can't truly do two things at once. The **event loop** is the scheduler that makes single-threaded JS feel concurrent. It pulls *one* macrotask from a queue (a `setTimeout` callback, an I/O completion, a UI event), runs it to completion, then drains all queued microtasks (Promise callbacks), then repeats. Asynchronous APIs don't "run in parallel" — they hand work off to the browser or OS, which queues a callback when the work is done.

**Why interviewers ask this:** It's the mental model behind every async bug. A candidate who can walk through a mixed `setTimeout`/Promise/sync example in order demonstrates real understanding of the runtime — not just memorized "`async` is for async stuff".

---

### The execution model

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

### Microtasks vs. macrotasks — the cheat sheet

| Microtasks | Macrotasks |
|---|---|
| `Promise.then` / `.catch` / `.finally` | `setTimeout`, `setInterval` |
| `async`/`await` continuations | I/O callbacks (fetch response, file read) |
| `queueMicrotask(fn)` | UI events (`click`, `scroll`) |
| `MutationObserver` | Rendering callbacks |
| | `setImmediate` (Node only) |

Microtasks have **higher priority** — the whole microtask queue drains between every pair of macrotasks.

---

### Walk-through — what does this print?

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

### Browser vs. Node.js — similar but not identical

#### Browser

The event loop runs on the main thread alongside rendering. Between macrotasks, the browser may *render* — recalculate styles, layout, paint. This is why long-running synchronous code freezes the UI.

Cycle: **macrotask → drain microtasks → maybe render → macrotask → ...**

#### Node.js — phased macrotask queue

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

### Garbage collection — how does the engine free memory?

**Headline:** Modern JS engines use **mark-and-sweep** — starting from root references (globals, call stack locals), the GC walks every reachable object and marks them; unmarked objects are collected. This handles circular references that the older **reference counting** algorithm can't.

#### Reference counting (historical)

Each object stored its incoming reference count. When the count hit zero, the memory freed. Simple, but **circular references leak forever** — two objects pointing to each other keep each other alive even after nothing else references them. Old IE had this problem; modern engines don't.

#### Mark-and-sweep (modern)

Used by V8 (Chrome, Node) and SpiderMonkey (Firefox):

1. Find all *roots* — globals, in-scope locals, the call stack.
2. Mark every object reachable from a root.
3. Sweep — anything unmarked is garbage, free it.

V8 in particular uses **generational GC** (young generation collected frequently, old generation rarely) and **incremental marking** (interleaved with JS execution to avoid long pauses).

---

### Common memory leak sources

Most leaks are the same pattern: something unreachable from your mental model is *actually* reachable through an unexpected reference.

- **Uncleared timers** — a `setInterval` callback holds a closure; the interval keeps a reference to the callback; no one ever clears it.
- **Detached DOM nodes** — JS variable still points to a DOM node that was removed from the tree. Neither the tree nor the JS can be freed.
- **Closures over large scopes** — a returned function keeps the entire enclosing scope alive, including big objects you don't actually use.
- **Accidental globals** — `foo = 1` (no `let`/`const`) at the top level creates a `window.foo`. Never freed.
- **Event listeners not removed** — attached on mount, never removed on unmount, keeps the component alive forever.

#### Detecting leaks

- **Chrome DevTools → Performance tab** — record for a few minutes; if heap usage keeps climbing without drops, there's a leak.
- **Memory tab → heap snapshots** — take one snapshot, do the suspect action, take another, compare. Look for objects that grew between snapshots.
- **Memory tab → allocation timeline** — records new allocations over time, marks which ones weren't freed.

**Rule of thumb:** Every subscription, listener, and timer needs a matching cleanup. In React, that's your `useEffect` return function. In vanilla JS, that's discipline — save the reference and remove it when done.

**See also:** [`3.4 Memory in JS, WeakMap and WeakSet`](./3.4%20Memory%20in%20JS%2C%20WeakMap%20and%20WeakSet.md) for how WeakMap/WeakSet help avoid leaks, [`4.3 Asynchronous JavaScript`](./4.3%20Asynchronous%20JavaScript.md) for Promise microtask scheduling details.

## 7.2 Node.js Fundamentals

A bundle of interview questions about Node.js's runtime model — threads vs. processes, multi-core utilization, and serverless.

## What's the difference between a process and a thread?

**Headline (30s):** A **process** is the OS's unit of isolation — it gets its own memory space and can't directly touch another process's data. A **thread** is a unit of execution *inside* a process; threads share memory with their siblings. Node.js runs user JavaScript on a single thread, so you can't naively use multiple CPU cores without spawning more processes (`cluster`, `fork`) or using worker threads for CPU-bound work.

- **Process** — own memory, isolated, heavier to create, safer.
- **Thread** — shared memory, lighter, data races possible without locks.

Why Node chose a single thread: the event loop model makes I/O-bound code fast and avoids the entire class of threading bugs (races, deadlocks) at the cost of not scaling across CPU cores without extra machinery.

---

## How do you use multiple CPU cores in Node.js?

**Headline (30s):** Three options: **`child_process.fork()`** for spawning independent Node.js processes (usually for one-off CPU work), **`cluster`** for sharing a server port across worker processes (the classic "one process per core" web server pattern), and **worker threads** (`worker_threads`) for sharing memory with the parent. In production, most teams wrap `cluster` with **PM2** instead of managing workers manually.

### `child_process.fork()` — spawn a Node.js process

Creates a child process running another JS file. Parent and child communicate via IPC (`send` / `message`).

```javascript
// main.js
const { fork } = require('child_process');

const child = fork('./compute.js');
child.send({ task: 'fibonacci', n: 40 });

child.on('message', (result) => {
  console.log('Result:', result);
});

// compute.js
process.on('message', (msg) => {
  if (msg.task === 'fibonacci') {
    process.send(fib(msg.n));
  }
});
```

**Reach for `fork`** when you have a one-off CPU-intensive task (image processing, a heavy computation) that would otherwise block the event loop. The cost: process spawn time (tens of milliseconds) and serialization overhead.

### `cluster` — load-balanced HTTP workers

Creates worker processes that all listen on the same port. Incoming connections are load-balanced across them automatically.

```javascript
const cluster = require('cluster');
const http    = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  for (let i = 0; i < numCPUs; i++) cluster.fork();
  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died, restarting...`);
    cluster.fork();
  });
} else {
  http.createServer((_, res) => {
    res.writeHead(200);
    res.end('Hello');
  }).listen(8000);
}
```

**Reach for `cluster`** for Node HTTP servers on multi-core machines — you get near-linear throughput scaling with CPUs and automatic restart on crashes.

### PM2 — production-grade process manager

Don't manage `cluster` by hand in production. PM2 wraps it with health checks, zero-downtime restarts, log rotation, and monitoring.

```bash
pm2 start app.js -i max   # one process per CPU
pm2 list                  # view running processes
pm2 monit                 # real-time metrics
pm2 reload app            # zero-downtime restart
```

**Gotcha — shared state between workers:** Each worker has its own memory. In-memory caches, sessions, or WebSocket connection maps need external storage (Redis) or a broadcast mechanism if you need cross-worker consistency.

---

## What is serverless / cloud functions, and when would you use them?

**Headline (30s):** Serverless (AWS Lambda, Google Cloud Functions, Vercel Edge Functions) runs your code without you managing servers — the cloud provider spins up a process, runs your handler, and tears it down when traffic subsides. You pay per execution, not per idle hour. The big trade-offs: **cold-start latency** (first invocation after idle can take hundreds of ms), hard **execution-time limits** (typically 10–60 seconds), and **no persistent in-memory state** between invocations.

### Advantages over traditional deployment

- **Cost** — pay only for execution time; no idle servers.
- **Auto-scaling** — the platform handles traffic spikes without capacity planning.
- **Operational overhead** — no patching, provisioning, or process management.
- **Deployment speed** — push code directly; no infra pipeline for simple functions.

### Trade-offs

- **Cold starts** — a fresh container costs hundreds of ms on first invocation. Mitigations: provisioned concurrency, smaller bundles, avoid heavy init.
- **Execution limits** — long-running work (reports, data migrations) needs a different compute model.
- **Statelessness** — every invocation might land on a new container. Keep persistent state in a database or cache.
- **Vendor lock-in** — handler signatures, auth, and tooling vary between providers.

### When to reach for serverless

- **API endpoints** — thin, stateless handlers.
- **Webhooks** — receive events from third-party services.
- **Scheduled jobs** — cron-like tasks (cleanup, reports).
- **Event-driven processing** — react to file uploads, DB changes, message queues.

**When not:** persistent connections (WebSocket servers — though providers now offer variants), long-running batch jobs, or workloads where cold-start latency is unacceptable (some user-facing APIs).

**See also:** [`7.1 Event Loop`](./7.1%20Event%20Loop.md) for the single-threaded runtime model that shapes these choices, [`12.1 Software Design Principles`](./12.1%20Software%20Design%20Principles.md) for where serverless fits in overall application architecture.

## 7.3 Build Tools

Reach for this when you need a quick reference for Webpack's core concepts, loaders, plugins, source maps, and adjacent tooling like Corepack. For ESM vs. CommonJS and dynamic imports, see [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md).

### Webpack — core concepts

Webpack is a static module bundler. It starts at an entry file, walks the import graph, and produces one or more optimized bundles the browser can load.

| Concept | What it is |
|---|---|
| **Entry** | Starting file(s) for dependency resolution (e.g., `./src/index.js`) |
| **Output** | Where bundles are written and how they're named |
| **Loaders** | Transform non-JS files (CSS, TS, images) into modules Webpack can ingest |
| **Plugins** | Hook into the build lifecycle (optimization, asset emission, env injection) |
| **Mode** | `development` (fast, readable) or `production` (minified, tree-shaken) |

### The build pipeline

1. **Merge config** — combine CLI flags with config file.
2. **Initialize compiler** — create the compiler, load plugins, call each plugin's `apply`.
3. **Resolve entries** — start from entry points, build a dependency graph.
4. **Apply loaders** — transform each source file through its matching loader chain.
5. **Emit output** — combine modules, optimize (minification, code splitting), write files.

---

### Loaders

Loaders run **right-to-left** — the last entry in `use` executes first, its output feeds the previous one, and so on.

```javascript
module: {
  rules: [
    { test: /\.tsx?$/, use: ['babel-loader', 'ts-loader'] },
    { test: /\.css$/,  use: ['style-loader', 'css-loader'] },
    { test: /\.scss$/, use: ['style-loader', 'css-loader', 'sass-loader'] }
  ]
}
```

For `.tsx`: `ts-loader` compiles TS → ES, then `babel-loader` transpiles ES → target ES.

#### Common loaders

| File type | Loaders |
|---|---|
| JS / TS | `babel-loader`, `ts-loader` |
| CSS | `css-loader`, `style-loader`, `postcss-loader`, `sass-loader` |
| Assets | `file-loader`, `url-loader`, `image-webpack-loader` |

#### Writing a custom loader

A loader is just a function `(source) => transformedSource`:

```javascript
// loaders/strip-comments-loader.js
module.exports = function (source) {
  return source.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '');
};
```

Register it via `resolveLoader.modules` so Webpack can find it from a local directory.

---

### Plugins

Plugins hook into `compiler.hooks` — events fired at specific lifecycle points (`beforeCompile`, `emit`, `done`, etc.).

#### Common plugins

| Plugin | What it does |
|---|---|
| `HtmlWebpackPlugin` | Generates HTML with injected `<script>` / `<link>` tags |
| `MiniCssExtractPlugin` | Extracts CSS into separate files (replaces `style-loader` in production) |
| `DefinePlugin` | Compile-time globals (e.g., `process.env.NODE_ENV`) |
| `TerserWebpackPlugin` | Minifies JS output |
| `CleanWebpackPlugin` | Removes old build artifacts before each build |
| `HotModuleReplacementPlugin` | Enables HMR during development |

#### Writing a custom plugin

A plugin is a class with an `apply(compiler)` method:

```javascript
class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tapAsync('BuildStats', (stats, callback) => {
      const json = JSON.stringify(stats.toJson({ modules: false }), null, 2);
      require('fs').writeFileSync('build-stats.json', json);
      callback();
    });
  }
}
```

Use `tap` for synchronous hooks, `tapAsync` / `tapPromise` for async ones.

---

### Source maps

Source maps map minified/bundled code back to your original source for debugging. Controlled by Webpack's `devtool` option.

| `devtool` | Rebuild speed | Quality | Use case |
|---|---|---|---|
| `eval` | Fastest | Generated code | Dev (fast iteration) |
| `eval-source-map` | Slow | Original source | Dev (accurate) |
| `cheap-source-map` | Medium | Lines only | CI / staging |
| `source-map` | Slowest | Full quality | Production + error tracking |

**Best practices:**

- **Development** — `eval-source-map` gives accurate stack traces with tolerable rebuild time.
- **Production** — emit `source-map` files, upload to your error tracker (Sentry, Bugsnag), but don't serve them publicly in closed-source projects.

---

### Corepack (Node 16.10+)

Built-in Node.js tool for pinning the package manager version per project.

```bash
corepack enable                              # install shims for yarn/pnpm
corepack prepare pnpm@latest --activate      # pin a specific version
```

With `"packageManager": "pnpm@8.15.0"` in `package.json`, any team member running `pnpm install` automatically gets that exact version — no more "works on my machine" from manager-version drift.

---

### When to reach for which

- **Webpack** — full-featured, everything pluggable, the default for large legacy codebases.
- **Vite** — ES modules + esbuild for development, Rollup for production. Dramatically faster dev server. First choice for new projects.
- **Rollup** — optimized for libraries (cleanest output), smaller ecosystem.
- **esbuild / swc / Turbopack** — native-speed bundlers / transpilers, still maturing plugin ecosystems.

**See also:** [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for ES modules and dynamic `import()`, [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md) for bundle-size and code-splitting strategy.

# 8. Networking & Security


## 8.1 HTTP Protocols and WebSockets

A bundle of interview questions about HTTP, the network stack, CORS, and WebSockets — the networking layer beneath every web app.

## What makes an API RESTful?

**Headline (30s):** REST (Representational State Transfer) uses standard HTTP methods to operate on resources identified by URLs. The contract: **nouns are URLs, verbs are HTTP methods**. `GET /posts` returns posts; `POST /posts` creates one; `DELETE /posts/1` deletes one. The "idempotent" methods (`GET`, `PUT`, `DELETE`) produce the same result whether called once or ten times — important for retries and caching.

| Method | Purpose | Idempotent |
|---|---|---|
| GET | Retrieve a resource | Yes |
| POST | Create a new resource | No |
| PUT | Replace a resource entirely | Yes |
| PATCH | Partially update a resource | No |
| DELETE | Remove a resource | Yes |

Example blog API: `GET /posts`, `POST /posts`, `PUT /posts/1`, `DELETE /posts/1`.

**Gotcha — `PUT` vs. `PATCH`:** `PUT` sends the *entire* resource — anything missing is cleared. `PATCH` sends only the fields to change. Most real APIs are loose about this, but interviewers like the distinction.

---

## What are the key HTTP headers to know?

**Request headers:**

- `Accept` — MIME types the client accepts (e.g., `application/json`).
- `Authorization` — credentials (e.g., `Bearer <token>`).
- `Content-Type` — body format (e.g., `application/json`).
- `Cookie` — stored cookies sent to the server.

**Response headers:**

- `Cache-Control` — caching directives (`no-cache`, `max-age=3600`).
- `Content-Length` — body size in bytes.
- `Set-Cookie` — instructs the browser to store a cookie.

**Negotiation headers:**

- `Accept-Encoding` — compression formats the client supports (`gzip`, `br`).
- `Accept-Language` — preferred languages.

---

## What do the HTTP status code ranges mean?

| Range | Category | Common codes |
|---|---|---|
| 1xx | Informational | 100 Continue |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | Server error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

**Rule of thumb:**

- **2xx** — OK, you handled it.
- **3xx** — follow up with another request (redirect, cached copy).
- **4xx** — client's fault, don't retry without changing something.
- **5xx** — server's fault, safe to retry with backoff.

---

## `XMLHttpRequest` vs. `fetch` vs. `axios` — which to use?

**Headline (30s):** `fetch` is the modern default — promise-based, supported everywhere, no dependency. `XMLHttpRequest` is legacy and verbose; you only see it in old code. `axios` is a popular third-party library with quality-of-life features (auto-JSON parsing, interceptors, request cancellation, same API in browser and Node) — reach for it when the project already uses it or when you need those features.

### `XMLHttpRequest`

```javascript
const xhr = new XMLHttpRequest();
xhr.open('GET', '/api/data');
xhr.onload = () => {
  if (xhr.status === 200) console.log(JSON.parse(xhr.responseText));
};
xhr.send();
```

### `fetch`

```javascript
const response = await fetch('/api/data');
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const data = await response.json();
```

**Gotcha — `fetch` doesn't reject on HTTP errors.** A 500 response is still a successful *promise*. You must check `response.ok` (or `response.status`) manually. This surprises almost everyone the first time.

### `axios`

```javascript
const { data } = await axios.get('/api/data');
```

Auto-parses JSON, rejects on 4xx/5xx by default, supports interceptors for auth tokens and global error handling.

---

## What's the OSI model, and why should I care?

**Headline:** The OSI 7-layer model is the reference for thinking about "where in the stack am I right now?" HTTP sits at layer 7; TCP at layer 4; IP at layer 3. Most interview questions only care about the top few layers, and the TCP/IP 4-layer model is what's actually used in practice.

| Layer | Name | Examples |
|---|---|---|
| 7 | Application | HTTP, FTP, DNS |
| 6 | Presentation | SSL/TLS, JPEG |
| 5 | Session | NetBIOS, RPC |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, ICMP |
| 2 | Data Link | Ethernet, MAC |
| 1 | Physical | Cables, hubs |

The **TCP/IP model** simplifies this into four layers: Link, Internet, Transport, Application.

---

## How does a TCP connection begin and end?

### 3-way handshake — connection establishment

1. **Client → Server:** `SYN` (with initial sequence number).
2. **Server → Client:** `SYN-ACK` (acknowledges + sends its own sequence number).
3. **Client → Server:** `ACK` (connection established).

### 4-way handshake — connection termination

1. **A → B:** `FIN` (A has no more data to send).
2. **B → A:** `ACK`.
3. **B → A:** `FIN` (B also done sending).
4. **A → B:** `ACK` (connection closed).

**Why four steps for close?** Each direction closes independently. When A sends `FIN`, B may still have data to send — B's own `FIN` comes only when it's also done.

### TCP packet sticking (sticky packets)

TCP is stream-oriented, not message-oriented — multiple small writes may arrive as a single read, or one large write may arrive split. Solutions:

- **Length-prefix** — each message starts with a byte-length header.
- **Delimiters** — special boundary character (e.g., `\n`).
- **Fixed-length** — pad every message to the same size.

---

## What's different about HTTP/1.1, HTTP/2, and HTTP/3?

| Version | Key features |
|---|---|
| HTTP/1.0 | One TCP connection per request (slow). |
| HTTP/1.1 | Keep-alive (persistent connections), chunked transfer encoding, cache headers (`ETag`, `Cache-Control`). |
| HTTP/2 | Multiplexing (many parallel requests on one TCP connection), header compression (HPACK), server push. |
| HTTP/3 | Built on QUIC (UDP-based). Eliminates TCP head-of-line blocking, faster connection setup (0-RTT on resumption). |

**Why HTTP/2 matters:** In HTTP/1.1, browsers open ~6 parallel connections per origin, and each blocks while in flight. HTTP/2 lets dozens of requests share one connection without blocking each other — fewer handshakes, faster pages.

**Why HTTP/3 matters:** If one packet is lost in HTTP/2 over TCP, *all* multiplexed streams pause until retransmit (head-of-line blocking at the transport layer). HTTP/3 runs over QUIC (UDP-based), so only the affected stream pauses.

---

## What's CORS, and why do I hit errors?

**Headline (30s):** Browsers enforce the **same-origin policy** — a page at `a.com` can't make arbitrary requests to `b.com`, because that would let any malicious page read your authenticated data from other sites. **CORS** (Cross-Origin Resource Sharing) is the mechanism for the target server to *opt in* to requests from specific origins via response headers. If you see a CORS error, it means the server didn't send the headers the browser needs to allow the request.

### The key response headers

```
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

### Preflight requests (`OPTIONS`)

For "non-simple" requests (non-GET/POST, or with custom headers like `Authorization`), the browser first sends an `OPTIONS` request to check if the actual request is allowed. The server responds with the same `Access-Control-*` headers; if they match, the real request goes through.

**Gotcha — `Access-Control-Allow-Credentials: true` can't be combined with `Access-Control-Allow-Origin: *`.** If you want credentials (cookies, auth headers) on a cross-origin request, the server must echo the specific origin.

### CORS workarounds (when you control the backend config, but not the upstream)

#### JSONP — the ancient trick

`<script>` tags aren't subject to same-origin policy, so you can load a remote script that calls a callback function you defined. Limited to `GET` and requires server cooperation.

```html
<script>
  function handleData(data) { console.log(data); }
</script>
<script src="https://api.example.com/data?callback=handleData"></script>
```

#### Reverse proxy (nginx)

Same-origin from the browser's perspective, different origin from the server's. Simple and preferred.

```nginx
location /api/ {
  proxy_pass http://backend-server:8080/;
}
```

**Reach for the proxy when:** you own the frontend hosting but don't want to modify the backend CORS config (e.g., third-party API).

---

## How does WebSocket differ from HTTP?

**Headline (30s):** HTTP is request/response — the client asks, the server answers, done. WebSocket opens a single persistent TCP connection over which *either side* can send messages at any time. That's what makes real-time apps (chat, collaborative editing, live dashboards) possible without polling.

### Handshake

WebSocket begins as an HTTP request with an `Upgrade: websocket` header. If the server agrees, it responds `101 Switching Protocols` and the same TCP connection is now WebSocket.

### Server example (Node.js)

```javascript
const { WebSocketServer } = require('ws');
const wss = new WebSocketServer({ port: 3000 });
const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('message', (msg) => {
    for (const client of clients) {
      if (client !== ws && client.readyState === 1) {
        client.send(msg.toString());
      }
    }
  });
  ws.on('close', () => clients.delete(ws));
});
```

### Client example

```javascript
const ws = new WebSocket('ws://localhost:3000');
ws.onopen    = () => ws.send('Hello');
ws.onmessage = (e) => console.log('Received:', e.data);
ws.onclose   = () => console.log('Disconnected');
```

### WebSocket vs. HTTP keep-alive

HTTP keep-alive reuses a TCP connection across multiple request/response pairs — but the server still can't push data unsolicited. WebSocket keeps an open channel where *either* side can send at any time.

**Reach for WebSocket when:** the server must push updates (live scores, notifications, collaborative editing). For infrequent updates, Server-Sent Events (`EventSource`) or long polling may be simpler.

---

## What resource hints should I add to my HTML?

**Headline (30s):** Four `<link rel>` hints help the browser optimize loading: `preload` for resources you *know* you need this page, `prefetch` for probable next-page resources, `dns-prefetch` for early DNS resolution of third-party origins, and `preconnect` for full handshake (DNS + TCP + TLS) on critical origins. Used well, they shave real time off first paint.

| Directive | Purpose | When to use |
|---|---|---|
| `<link rel="preload">` | Fetch critical resource for current page | Fonts, above-the-fold images, key scripts |
| `<link rel="prefetch">` | Hint for next-page resources (low priority) | Resources for likely next navigation |
| `<link rel="dns-prefetch">` | Resolve DNS early | Third-party domains (CDNs, analytics) |
| `<link rel="preconnect">` | Full DNS + TCP + TLS handshake | High-priority third-party origins |

```html
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://cdn.example.com">
<link rel="dns-prefetch" href="https://analytics.example.com">
<link rel="prefetch" href="/next-page-bundle.js">
```

**Gotcha — `preload` without `as`** is wasted; the browser needs to know the resource type to apply the right priority. **Use `preconnect` sparingly** — too many preconnections actually slow things down.

**See also:** [`1.1 Browser Basics`](./1.1%20Browser%20Basics.md) for how requests fit into the page-load pipeline, [`8.2 Web Security and Authentication`](./8.2%20Web%20Security%20and%20Authentication.md) for HTTPS, auth tokens, and common attacks.

## 8.2 Web Security and Authentication

A bundle of interview questions on authentication, HTTPS, and the common web-security attacks you'll be asked about in any frontend interview.

## Cookies vs. tokens — which to use for authentication?

**Headline (30s):** Both are valid; pick based on architecture. **Cookie-based auth** (server-side sessions) is simple, secure against XSS when you use `HttpOnly`, and works automatically with every request — but doesn't scale as cleanly across domains or microservices. **Token-based auth** (JWT) is stateless, works naturally across domains, and scales horizontally — but requires you to handle storage carefully (XSS risk if in `localStorage`) and has no built-in revocation. Pick cookies for classic server-rendered apps, tokens for SPAs with cross-domain APIs or microservices.

### Cookie-based authentication

1. User logs in with credentials.
2. Server creates a session, stores it server-side, sets `Set-Cookie` with the session ID.
3. Browser automatically sends the cookie with every request.
4. Server looks up the session by ID.

**Properties:**

- Automatic transmission with every request (including CORS when `withCredentials`).
- ~4KB size limit.
- `HttpOnly` — blocks JavaScript access (XSS mitigation).
- `Secure` — HTTPS only.
- `SameSite=Strict|Lax|None` — CSRF protection.

### Token-based authentication (JWT)

1. User logs in with credentials.
2. Server generates a signed JWT containing claims, returns it in the response body.
3. Client stores the token (in memory or `localStorage`) and sends it via `Authorization: Bearer <token>`.
4. Server verifies the signature — no server-side session storage needed.

**Advantages:**

- Stateless — no server-side session store.
- Works across domains (no same-origin cookie restrictions).
- Self-contained — carries user data in the payload.
- Scales in distributed/microservice architectures.

**Trade-offs:**

- Can't be revoked before expiry without a blocklist (Redis, etc.).
- Larger than a session ID.

**Gotcha — JWT in `localStorage` is XSS-vulnerable.** Any XSS payload can read the token. Prefer `HttpOnly` cookies for the token itself; the cost is that you need CSRF protection. If you must store in JS, use short lifetimes + refresh tokens.

---

## What is Single Sign-On (SSO), and how does it work?

**Headline (30s):** SSO lets a user authenticate once with a central provider and access multiple systems without re-entering credentials. The provider issues a signed token that other systems trust. Common protocols: **SAML** (enterprise), **OAuth 2.0** (delegated API access), **OpenID Connect** (OAuth 2.0 + identity layer — the modern default for SSO).

### Typical flow

1. User visits System A → no session → redirect to SSO provider.
2. User authenticates at the SSO provider.
3. SSO provider issues a token/ticket and redirects back to System A.
4. System A validates the token (signature, expiry) and creates its own session.
5. User visits System B → SSO cookie already exists → automatic login.

**Reach for SSO when:** managing auth across multiple internal systems or integrating with enterprise identity providers (Okta, Auth0, Azure AD).

---

## How does HTTPS protect against man-in-the-middle attacks?

**Headline (30s):** HTTPS encrypts traffic using a *hybrid* of asymmetric and symmetric cryptography. The server presents a public-key certificate issued by a trusted Certificate Authority (CA). The client verifies the certificate, uses the public key to exchange a symmetric session key, then both sides encrypt all subsequent data with that key. Because the attacker can't present a valid CA-signed certificate for the target domain, the browser rejects the connection — that's the "This site is not secure" warning.

### Symmetric vs. asymmetric encryption

- **Symmetric** — same key encrypts and decrypts. Fast. Used for bulk data transfer.
- **Asymmetric** — public key encrypts, private key decrypts. Slower, expensive. Used only to establish the symmetric session key.

### The HTTPS handshake (simplified)

1. Client receives the server's public key (inside an SSL/TLS certificate).
2. Client generates a random session key, encrypts it with the server's public key, sends it.
3. Server decrypts with its private key.
4. Both sides use the session key for symmetric encryption of everything that follows.

### The MitM attack vector

An attacker sits between client and server. If the client blindly accepted any public key, the attacker could substitute their own and read everything.

**Prevention — trusted CAs:**

- Certificates are signed by CAs the browser trusts.
- Browser verifies:
  1. The certificate is signed by a trusted CA (chain of trust).
  2. The domain name matches the certificate's subject.
  3. The certificate hasn't expired or been revoked.

If any check fails, the browser blocks the connection.

**Gotcha — self-signed certificates in production:** Users see a scary warning. Use Let's Encrypt for free CA-signed certs; there's no reason to self-sign in production.

---

## XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**Headline (30s):** XSS happens when an attacker injects JavaScript into a page that other users view. The injected script runs with the full privileges of the site — it can read cookies, send authenticated requests, rewrite the DOM, anything the user could do. Prevention: **escape user content on render**, **use a framework that does it for you** (React escapes strings by default), and **set `Content-Security-Policy`** to restrict script sources.

### Common sinks

- `innerHTML` / `outerHTML` — never concatenate user input here.
- `document.write` — same.
- `eval`, `new Function(...)` — never run strings from users.
- `<a href="javascript:...">` — validate URLs.
- React's `dangerouslySetInnerHTML` — the name is a warning.

### Prevention layers

1. **Escape output** — `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, etc. Frameworks like React, Vue, and templating engines do this by default. **Don't defeat the default.**
2. **Content-Security-Policy (CSP)** — restrict where scripts can load from (`script-src 'self'`), block inline scripts unless allowlisted. Even if XSS is injected, the browser refuses to run it.
3. **`HttpOnly` cookies** — session tokens can't be stolen from `document.cookie`.
4. **Input validation** — allowlist the characters you expect (belt + suspenders, not a replacement for escaping).

---

## CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**Headline (30s):** CSRF tricks a logged-in user's browser into sending unwanted authenticated requests to your site. The malicious site embeds a form or image that posts to your domain; because the browser attaches the user's cookies automatically, the request looks legitimate to your server. Prevention: **anti-CSRF tokens** (random tokens per form that the attacker can't guess), **`SameSite` cookies** (modern default, blocks cross-site cookie sends), and **origin/referer checks**.

### Prevention

- **Anti-CSRF tokens** — include a random token in forms; verify server-side. Attacker doesn't have it, can't forge a valid request.
- **`SameSite=Strict` / `SameSite=Lax`** — cookie not sent on cross-origin POSTs. Modern browsers default to `Lax`, which handles most cases.
- **Origin / Referer check** — reject state-changing requests whose `Origin` header doesn't match your domain.

**Gotcha — `SameSite=None` requires `Secure`:** Modern browsers reject `SameSite=None` cookies served over HTTP.

---

## Clickjacking — what is it, how do you prevent it?

**Headline:** Clickjacking overlays a transparent iframe of your site on top of a decoy page — the user thinks they're clicking "Win a prize", but actually they're clicking "Transfer money" on your site with their authenticated session. Prevention: tell the browser to refuse to be framed by another origin.

**Prevention headers:**

```
X-Frame-Options: SAMEORIGIN         (or DENY)
Content-Security-Policy: frame-ancestors 'self'
```

CSP's `frame-ancestors` is the modern approach; `X-Frame-Options` is the legacy one. Set both during migration, then drop `X-Frame-Options`.

---

## DDoS — what is it, what can you actually do?

**Headline:** Distributed Denial of Service floods your server with traffic from a botnet. It's not solvable in application code — the volume is too big. Prevention lives at the edge: **CDN-based DDoS protection** (Cloudflare, AWS Shield, Akamai), **rate limiting** at ingress, and **Web Application Firewalls** (WAFs) to filter known-bad patterns.

What you *can* do in application code: respond quickly with minimal work to known-abusive traffic, cache aggressively so legitimate traffic is cheap, and avoid expensive endpoints that could amplify an attack.

---

## SQL injection — frontend's role?

**Headline:** SQL injection is a backend vulnerability — user input concatenated into raw SQL queries lets attackers manipulate the database. The frontend's role is mostly limited: validate input, but never rely on client-side validation for security. The real fix is on the server: **parameterized queries** / **prepared statements**, which separate SQL from data so injection becomes impossible.

**Prevention layers (backend-owned, but worth knowing):**

- Parameterized queries / prepared statements.
- ORM tools that parameterize by default (Sequelize, TypeORM, Prisma).
- Principle of least privilege on database accounts (read-only service account can't drop tables).
- Input validation (defense in depth, not primary defense).

**See also:** [`8.1 HTTP Protocols and WebSockets`](./8.1%20HTTP%20Protocols%20and%20WebSockets.md) for CORS and HTTPS handshake basics, [`5.2 Browser Storage and Communication`](./5.2%20Browser%20Storage%20and%20Communication.md) for `postMessage` and storage security.

# 9. React & Frameworks


## 9.1 Virtual DOM and Framework Selection

### How does the Virtual DOM work, and is it actually fast?

**Headline (30s):** The Virtual DOM is a JavaScript object tree that mirrors the real DOM. On state change, the framework rebuilds the virtual tree, **diffs** it against the previous one, and applies only the minimal set of changes to the real DOM in a batched update. It's *not* automatically faster than hand-optimized direct DOM manipulation — the real value is **predictable performance at scale** and a **component model** that lets you describe UI declaratively without writing your own DOM diff code.

**Why interviewers ask this:** It separates candidates who understand *why* React and Vue work the way they do from those who just use them. A good answer covers the tradeoff — VDOM is not a silver bullet, it's a productivity and consistency tool.

#### The three-step reconciliation loop

1. **Render** — component re-renders, producing a new virtual tree (plain JS objects).
2. **Diff** — the framework compares the new tree with the previous one. Strategies vary; React's is O(n) heuristic-based, not a full tree-diff (that would be O(n³)).
3. **Commit** — only the changed DOM nodes are touched, in a single batched update.

#### Where VDOM actually helps

- **Batching** — many state updates during one render collapse into one DOM update.
- **Minimal updates** — only changed nodes are touched (no wholesale re-renders).
- **Developer ergonomics** — you describe "what the UI should look like", the framework handles "which DOM operations get there".

#### Where VDOM loses

- **Simple isolated updates** — vanilla JS / jQuery can be faster for "toggle this one class on one element"; no diff overhead.
- **Hot paths** — games, canvases, huge lists — skip VDOM and work directly (React's `useSyncExternalStore`, Vue 3's `createApp` with manual render, or raw canvas/WebGL).

**Reach for VDOM when:** the UI has many components with changing state, and correctness / maintainability matters more than saving a few ms per update.

#### Common VDOM-based frameworks

- **React** — the original popularizer, uses Fiber architecture for interruptible rendering.
- **Vue** — similar VDOM + reactivity system based on Proxy (Vue 3).
- **Preact** — smaller, React-compatible.
- **Inferno / Mithril** — niche but highly optimized.

Non-VDOM reactive frameworks exist too — **Svelte** compiles away reactivity at build time (no runtime diff), **Solid** uses fine-grained reactivity (tracks cell-level updates without VDOM).

---

### How do you choose a frontend framework?

**Headline (30s):** There is no universally correct answer. Pick based on **team experience**, **ecosystem maturity**, and **project requirements** — not on which framework is "hot" right now. React has the biggest ecosystem and the most jobs; Vue is easier to learn and has excellent docs; Angular is opinionated and popular in enterprise. For TypeScript vs. JavaScript: TS almost always wins for codebases that will live more than six months, despite the initial overhead.

**Why interviewers ask this:** A senior candidate should be able to reason about trade-offs, not just parrot "we use X because X is popular." Anti-pattern: switching frameworks mid-project because of an online hype wave.

#### Framework options

- **React / Next.js** — largest ecosystem, best for complex apps with heavy state and interactivity. The default pick in most hiring pools.
- **Vue / Nuxt** — gentle learning curve, excellent docs, great for teams transitioning from jQuery or working on smaller apps.
- **Angular** — opinionated, batteries-included, common in enterprise. Steeper learning curve.
- **Svelte / SvelteKit** — minimal runtime, compile-time reactivity; rapidly growing but smaller ecosystem.
- **Solid / Qwik / others** — emerging frameworks with interesting performance properties; know they exist, don't bet a career-defining project on them.

#### Language: JavaScript or TypeScript?

- **JavaScript** — maximum flexibility, faster onboarding, largest ecosystem.
- **TypeScript** — type safety, better refactoring, fewer runtime bugs. Default for long-lived codebases and teams over ~3 people.

**Rule of thumb:** Any codebase you expect to maintain for more than six months should be TypeScript. The initial learning cost pays for itself the first time you rename a property.

#### The real decision factors

- **Team experience** — a team that ships React in a week will struggle with Svelte for a month. Productivity is dominated by familiarity.
- **Ecosystem size** — does the framework have the libraries you need (routing, forms, data layer, UI kits)?
- **Hiring pool** — can you find engineers who already know it?
- **Project requirements** — SSR needs (Next.js, Nuxt), mobile (React Native, NativeScript), perf ceiling (Solid, Svelte).
- **Long-term bet** — React's momentum is unmatched; Vue's is strong; Svelte's is growing; others are riskier.

**Gotcha — "framework fatigue":** Most teams don't need to move off the framework they're already on. The best framework is usually the one your team already knows.

**See also:** [`9.2 React Basics`](./9.2%20React%20Basics.md) for JSX, the diff algorithm, and the React component model, [`9.4 Next.js`](./9.4%20Next.js.md) for SSR/SSG/ISR rendering strategies.

## 9.2 React Basics

A bundle of interview questions every React developer should be able to answer on the spot — JSX, the diff algorithm, the lifecycle, `setState` behavior, routing, and the SPA/MPA distinction.

## What is JSX, and what does it compile to?

**Headline (30s):** JSX is a syntax extension that lets you write HTML-like markup inside JavaScript. It's not HTML and it's not a string — the transpiler (Babel, SWC, esbuild) rewrites every JSX expression into a `React.createElement(type, props, ...children)` call. That's why you need React in scope historically, and why JSX can embed any JS expression with `{}`.

```jsx
const element = <h1 className="title">Hello</h1>;

// Transpiles to:
const element = React.createElement('h1', { className: 'title' }, 'Hello');
```

**Rules:**

- **Custom components must start with an uppercase letter** (`MyComponent`). Lowercase tags are treated as HTML strings.
- **Expressions go in `{}`** — anything that's a valid JS expression.
- **Attributes are camelCase** (`className`, `onClick`) — because `class` and similar are reserved words.

**Gotcha — "New JSX transform" (React 17+):** You no longer need to `import React from 'react'` in every file just for JSX. The compiler injects the right import automatically.

---

## How does React's diff algorithm decide what to update?

**Headline (30s):** React's reconciler uses three heuristics to keep diffing fast (O(n) instead of the classic O(n³)): (1) elements at the same position of the same type are updated, not recreated; (2) elements with different types have their entire subtree replaced; (3) for lists, `key` props identify which items moved, were added, or removed. The takeaway: **keys must be stable and unique** — using array indices causes subtle bugs when the list reorders.

### The three rules

1. **Same position, same type** — reuse the DOM node, just update props.
2. **Different types** — unmount the old subtree completely, mount the new one.
3. **Lists need keys** — without stable keys, React falls back to index-based matching and misidentifies moved items.

### Keys — the rule you'll be tested on

```jsx
// Good: stable ID as key
{items.map(item => <ListItem key={item.id} data={item} />)}

// Bad: index as key — breaks on insert, delete, or reorder
{items.map((item, i) => <ListItem key={i} data={item} />)}
```

**Why index keys fail:** When you delete item 0, all subsequent indices shift down. React sees "item at key=1 changed its data" instead of "item at key=1 was removed." Any local state in those list items ends up attached to the *wrong* data.

**Gotcha — keys are not globally unique, just unique among siblings.** `key="foo"` in one list doesn't conflict with `key="foo"` in another.

---

## What's the class component lifecycle?

**Headline (30s):** Three phases — **mounting** (first render), **updating** (re-render from props/state change), and **unmounting** (removal). Each phase has well-defined hooks. Most of this is legacy knowledge: function components + hooks replaced it, but interviewers still ask, and you'll still see class components in existing codebases.

### Mounting

```
constructor → getDerivedStateFromProps → render → componentDidMount
```

- **`constructor`** — set initial state, bind methods.
- **`getDerivedStateFromProps`** (rare) — derive state from props, static method.
- **`render`** — return JSX.
- **`componentDidMount`** — DOM is now available; fetch data, start timers, subscribe.

### Updating

```
getDerivedStateFromProps → shouldComponentUpdate → render → getSnapshotBeforeUpdate → componentDidUpdate
```

- **`shouldComponentUpdate`** — return `false` to skip re-render (perf optimization).
- **`componentDidUpdate`** — react to new props/state, e.g. re-fetch if an ID changed.

### Unmounting

```
componentWillUnmount
```

The one place to clean up timers, subscriptions, event listeners — whatever the component set up during mount.

### Error handling

- **`getDerivedStateFromError`** — sync; updates state to render a fallback UI.
- **`componentDidCatch`** — effects like logging.

**Mapping to hooks:**

| Class | Hook |
|---|---|
| `constructor` + `componentDidMount` | `useState` + `useEffect(fn, [])` |
| `componentDidUpdate` | `useEffect(fn, [deps])` |
| `componentWillUnmount` | `useEffect` cleanup return |
| `shouldComponentUpdate` | `React.memo` |

---

## What is an Error Boundary, and what does it catch?

**Headline (30s):** An Error Boundary is a class component that catches JavaScript errors in its subtree during rendering, lifecycle methods, and constructors — and renders a fallback UI instead of letting the whole tree unmount. It does **not** catch errors in event handlers, async code, or SSR. No hook equivalent yet; use the `react-error-boundary` library for function components.

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) return <h1>Something went wrong.</h1>;
    return this.props.children;
  }
}
```

**What it does NOT catch:**

- Event handler errors (wrap in `try/catch`).
- Async code (`setTimeout`, Promises, `await` inside `useEffect`).
- SSR errors.
- Errors thrown inside the boundary itself.

**See also:** [`4.5 Error Handling`](./4.5%20Error%20Handling.md) for the full layered error handling model.

---

## Is `setState` sync or async?

**Headline (30s):** In React 17 and earlier, `setState` was **batched** (async) inside React-controlled code (event handlers, lifecycle methods) but **synchronous** in `setTimeout`, native DOM events, and Promise callbacks. In **React 18+, batching is automatic everywhere** — including async contexts. The practical rule: always treat `setState` as async and never read the new state from `this.state` (class) or a captured closure variable (function) immediately after calling it.

### React 17 and earlier

- Inside React (handlers, lifecycle) — batched, async.
- In `setTimeout`, Promises, native events — synchronous.

### React 18+

- Automatic batching everywhere. All `setState` calls within the same tick collapse into one re-render.

```javascript
// React 18 entry point
import { createRoot } from 'react-dom/client';
createRoot(document.getElementById('root')).render(<App />);
```

**Gotcha — reading state right after setState:**

```javascript
// This does NOT work — state is a closure over the old value
setCount(count + 1);
console.log(count);        // still the old value
console.log(count + 1);    // compute locally if you need the new value

// If you need the updated value in an effect, use useEffect
useEffect(() => { console.log(count); }, [count]);
```

### Updater form for correctness

If multiple updates reference the previous state, use the updater form — it handles batching correctly:

```javascript
// Bad: all three see the same count, so final state is count+1
setCount(count + 1);
setCount(count + 1);
setCount(count + 1);

// Good: each reads the previous result, final state is count+3
setCount(prev => prev + 1);
setCount(prev => prev + 1);
setCount(prev => prev + 1);
```

---

## How does React Router work?

**Headline (30s):** React Router is the de facto SPA routing library. You declare routes in JSX; the router matches the current URL, renders the matching component, and lets you navigate without full page reloads using `<Link>` or the `useNavigate` hook. Three router modes: `BrowserRouter` (clean URLs, needs server config), `HashRouter` (hash-based, no server config needed), `MemoryRouter` (in-memory, for tests).

### Declarative routes

```jsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/posts/:postId" element={<Post />} />
  </Routes>
</BrowserRouter>
```

```jsx
function Post() {
  const { postId } = useParams();
  return <h1>Post {postId}</h1>;
}
```

### Router modes

- **`BrowserRouter`** — uses the History API (`/path`). Requires server config so `/posts/123` returns `index.html` (otherwise 404). Default for production.
- **`HashRouter`** — uses URL hash (`/#/path`). Works without any server config, at the cost of ugly URLs.
- **`MemoryRouter`** — no URL changes; used for testing and non-browser environments (React Native, isolated tests).

**Reach for `HashRouter`** when you can't configure the server (e.g., static hosting that only serves `index.html` at `/`). Otherwise use `BrowserRouter`.

---

## What's the difference between SPA and MPA?

**Headline (30s):** A **Single Page Application** loads one HTML shell and updates the view client-side via JavaScript; no full page reloads. A **Multi-Page Application** serves a new HTML document on every navigation. SPAs win on app-like UX and state preservation; MPAs win on first-load speed, SEO-out-of-the-box, and lower complexity per page. Most modern "SPAs" are actually hybrids — Next.js, Nuxt, Remix use SSR/SSG to get MPA-style first paint with SPA interactivity.

| Aspect | SPA | MPA |
|---|---|---|
| Navigation | Client-side routing, no full reload | Full page reload per navigation |
| Initial load | Slower (downloads entire app bundle) | Faster (smaller per-page bundles) |
| SEO | Challenging (needs SSR/SSG) | Native SEO support |
| UX | Smooth, app-like transitions | Traditional page transitions |
| Complexity | Higher (state, routing, auth flows) | Lower per page |
| Examples | Gmail, Figma, Notion | News sites, e-commerce (pre-hybrid) |

**Reach for SPA when:** the app has rich stateful interactions, reuses most UI across routes, and SEO isn't the primary acquisition channel.

**Reach for MPA (or hybrid SSR)** when: content needs to be indexable, sessions are short, and each page is mostly independent.

**See also:** [`9.4 Next.js`](./9.4%20Next.js.md) for hybrid SPA/MPA rendering strategies (SSR/SSG/ISR), [`9.3 Advanced React`](./9.3%20Advanced%20React.md) for hooks, refs, and component composition patterns.

## 9.3 Advanced React

A bundle of intermediate/advanced React interview questions — component communication, hooks, and reusable component patterns.

## How can components communicate in React?

**Headline (30s):** Four patterns, picked by *direction* and *distance*: **parent→child via props**, **child→parent via callback props** (or refs for imperative access), **cross-cutting via Context API** for shared state that many components need, and **cross-component via state management libraries** (Redux, Zustand) for complex app-wide state. The rule of thumb: start with props, reach for context when you'd otherwise drill the same prop through 3+ levels, reach for a library only when context becomes unwieldy.

### Parent → Child

- **Props** — standard unidirectional data flow.
- **Refs** — for imperative access (focus an input, call a child method). Use sparingly.
- **Context API** — shared data without prop drilling; parent `Provider`, consumer `useContext`.

```jsx
const ThemeContext = createContext('light');

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  );
}

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>...</div>;
}
```

### Child → Parent

- **Callback props** — parent passes a function; child calls it with data.
- **`forwardRef` + `useImperativeHandle`** — child exposes specific methods via ref.
- **Event bubbling** — parent listens on a wrapper; child's event bubbles up.

### Cross-component (not parent-child)

- **State management libraries** — Redux, Zustand, Jotai, MobX. Pick based on complexity and team familiarity.
- **Custom hooks** — extract stateful logic, call from anywhere.
- **Event systems** — custom EventBus for decoupled pub/sub (rarely the right answer in React).

**Rule of thumb:** Props for parent→child. Callbacks for child→parent. Context for deep sharing that's cross-cutting (theme, auth, locale). A store library when state is truly global and complex.

---

## When do you use `useCallback`, `useMemo`, and `React.memo`?

**Headline (30s):** These three work together to skip unnecessary re-renders. **`React.memo`** wraps a component and skips re-render if its props are shallowly equal. **`useMemo`** memoizes a computed value. **`useCallback`** memoizes a function reference. You typically need all three together: `React.memo` on the child, `useCallback` for the function props you pass it, `useMemo` for any computed objects you pass. Without that matching, the child re-renders anyway because the props change reference identity every render.

### `useCallback`

Memoizes a function reference. The child that receives it skips re-rendering when the parent re-renders.

```javascript
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### `useMemo`

Memoizes a computed value. Only recomputes when dependencies change.

```javascript
const sortedList = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);
```

### `React.memo`

Higher-order component that skips re-render when props are shallowly equal.

```javascript
const ExpensiveList = React.memo(({ items }) => (
  items.map(item => <Item key={item.id} data={item} />)
));
```

**Combining the three for maximum effect:**

```jsx
function Parent({ data }) {
  const handleClick = useCallback(() => console.log('clicked'), []);
  const processed  = useMemo(() => heavyProcess(data), [data]);
  return <ExpensiveChild onClick={handleClick} items={processed} />;
}

const ExpensiveChild = React.memo(({ onClick, items }) => { /* ... */ });
```

**Gotcha — don't memoize everything.** Memoization has its own cost (equality checks, closure retention). The framework will re-render fast if the subtree is small. Profile first; memoize only the components that actually re-render expensively.

---

## How do you use `useRef`?

**Headline (30s):** `useRef` returns a mutable object (`{ current }`) that persists across renders **without triggering re-renders** when mutated. Three common use cases: accessing a DOM node imperatively, storing mutable values (timer IDs, previous values) that don't belong in state, and holding non-reactive external instances (WebSocket, observer).

```javascript
const inputRef = useRef(null);
const focusInput = () => inputRef.current.focus();

return <input ref={inputRef} />;
```

**Common patterns:**

- **DOM access** — focusing, measuring, imperative library integration (charts, maps, animations).
- **Previous value** — `useRef` + `useEffect` to remember the last value.
- **Timer / subscription IDs** — store the ID so you can clear it in cleanup.
- **Mutable flags** — "has been initialized", "is currently dragging" — without re-rendering.

**Gotcha — mutating `.current` doesn't re-render.** That's usually the point (it's what makes refs different from state), but it means you can't drive UI with ref values. Use state for anything the UI displays; use refs for bookkeeping.

---

## What does `forwardRef` do?

**Headline (30s):** By default, refs don't pass through custom components — `<MyInput ref={r} />` does nothing useful. `forwardRef` wraps a component so it explicitly forwards its `ref` argument to an underlying DOM element (or uses `useImperativeHandle` to expose a custom API). You need this any time a parent wants imperative access to something inside a custom component.

```javascript
const FancyInput = forwardRef((props, ref) => (
  <input ref={ref} className="fancy" {...props} />
));

// Parent:
const ref = useRef(null);
<FancyInput ref={ref} />
ref.current.focus();
```

**Reach for `forwardRef`** when building a reusable component that should feel like a DOM element (inputs, buttons, custom scroll containers). Combine with `useImperativeHandle` to expose only specific methods instead of the raw DOM node.

---

## What are custom hooks, and when do they differ from regular functions?

**Headline (30s):** A custom hook is a function whose name starts with `use` that *calls other hooks internally*. That's it — the `use` prefix is a convention that lints can enforce. Custom hooks let you reuse stateful logic (state, effects, refs, subscriptions) across components without HOCs or render props. Regular functions can't use hooks — they can only do pure computation or utilities.

| Custom hooks | Regular functions |
|---|---|
| Can call `useState`, `useEffect`, etc. | Cannot call hooks |
| Manage state and side effects | Pure computation only |
| Re-run on every render of the component | Called explicitly |
| Named `useX` by convention | Any name |

### Example: window size hook

```javascript
function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const handler = () => setSize({
      width:  window.innerWidth,
      height: window.innerHeight
    });
    window.addEventListener('resize', handler);
    handler();
    return () => window.removeEventListener('resize', handler);
  }, []);
  return size;
}
```

Any component can call `const { width, height } = useWindowSize()` — the subscription and cleanup are packaged up.

**Gotcha — Rules of Hooks:** Hooks must be called at the top level of a component or custom hook, in the same order every render. No `if`, no loops, no early returns before a hook. If you need conditional logic, branch *inside* the hook's callbacks.

---

## What is the "render props" pattern?

**Headline (30s):** Render props pass a function as a prop that returns JSX — letting the consumer control what to render using data the component provides. It was the main reusability pattern before hooks; today, **custom hooks replace it** for nearly all cases. You'll see it in legacy codebases and in libraries that want a hookless public API.

```jsx
<MouseTracker render={({ x, y }) => (
  <p>Mouse position: {x}, {y}</p>
)} />
```

The `MouseTracker` manages state (mouse position); the parent supplies the render function. Pre-hooks, this was how you shared "track the mouse and render something" across components. Post-hooks, `const { x, y } = useMouse()` does the same with less ceremony.

---

## What are Higher-Order Components (HOCs)?

**Headline (30s):** An HOC is a function that takes a component and returns a new component with added behavior — like decorators for React. They were the classic pattern for cross-cutting concerns (auth, logging, routing) before hooks. Today, **custom hooks are usually cleaner**; HOCs are still relevant for cases where you need to *modify rendering behavior* rather than share logic (e.g., `React.memo`, `connect` from Redux).

```javascript
function withAuth(WrappedComponent) {
  return function AuthenticatedComponent(props) {
    const user = useAuth();
    if (!user) return <Redirect to="/login" />;
    return <WrappedComponent {...props} user={user} />;
  };
}

const ProtectedPage = withAuth(Dashboard);
```

**Trade-offs:**

- Clean syntax at the use site (`withAuth(Dashboard)`).
- But multiple HOCs produce "wrapper hell" in React DevTools.
- Props can collide unexpectedly.
- Types are awkward in TypeScript.

**Rule of thumb:** Custom hooks for logic reuse, HOCs only when you need to actually wrap/alter rendering behavior (`React.memo`, `connect`, `observer` from MobX).

---

## What are common conditional-rendering patterns?

Four idiomatic patterns — pick based on readability at the call site.

```jsx
// 1. Ternary — for either-or
{isLoggedIn ? <Dashboard /> : <Login />}

// 2. Logical AND — for render-or-nothing
{showBanner && <Banner />}

// 3. Early return — for guard clauses in a component
function Component({ data }) {
  if (!data) return <Loading />;
  return <Content data={data} />;
}

// 4. Element variable — for many branches
let content;
if (error)        content = <Error />;
else if (loading) content = <Spinner />;
else              content = <Data />;
return <div>{content}</div>;
```

**Gotcha — `&&` with numbers:** `{list.length && <List items={list} />}` renders the literal `0` when the list is empty (because React renders numbers but not `false`). Coerce to boolean: `{!!list.length && ...}` or `{list.length > 0 && ...}`.

**See also:** [`9.2 React Basics`](./9.2%20React%20Basics.md) for JSX, lifecycle, `setState`, and router basics, [`4.1 Object, Function, and Prototype`](./4.1%20Object%2C%20Function%2C%20and%20Prototype.md) for the `this`/`bind` behavior underneath class components.

## 9.4 Next.js

### Why pick Next.js over plain React?

**Headline (30s):** Plain React is purely client-side — you ship JavaScript, the browser renders the UI. That's fine for app-like experiences but poor for SEO and first-paint performance. Next.js adds **server-side rendering (SSR)**, **static generation (SSG)**, and **incremental regeneration (ISR)** on top of React, plus file-based routing, API routes, and built-in optimizations (image, font, bundle). It lets you pick the right rendering strategy per page instead of committing the whole app to CSR.

**Why interviewers ask this:** SSR vs SSG vs ISR is a *common* frontend systems-design question. Candidates who can't articulate when each applies struggle to architect performant Next.js apps.

#### What Next.js adds over React

- **Server-Side Rendering (SSR)** — HTML generated per request for SEO and fast first paint.
- **Static Site Generation (SSG)** — pre-built HTML at build time for maximum performance.
- **Incremental Static Regeneration (ISR)** — SSG + periodic revalidation.
- **File-based routing** — pages map to file paths, no manual route config.
- **API routes** — backend endpoints colocated with frontend (`pages/api/` or `app/api/`).
- **Built-in optimizations** — automatic code splitting, image optimization (`next/image`), font optimization (`next/font`).

---

### SSR, SSG, ISR, CSR — when do you use each?

**Headline (30s):** Pick the rendering strategy per page based on *how fresh the data needs to be* and *who needs to see it*. **CSR** (plain React) — internal apps, no SEO needs. **SSR** — dynamic content that changes per request, must be indexable. **SSG** — content that rarely changes (blogs, docs, marketing). **ISR** — content that updates periodically (e-commerce catalogs, news) — fast like SSG, but refreshes in the background.

#### SSR — Server-Side Rendering

HTML generated **per request**. React **hydrates** the client to make it interactive.

```javascript
export async function getServerSideProps(context) {
  const res = await fetch(`https://api.example.com/posts`);
  const posts = await res.json();
  return { props: { posts } };
}
```

**When:** dynamic content that needs SEO — product pages, dashboards with personalized content, anything that changes every request.

**Cost:** server CPU per request. First byte is slower than SSG because the server has to render before responding.

#### SSG — Static Site Generation

HTML generated at **build time**. Served as static files from a CDN — the fastest possible delivery.

```javascript
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return { props: { posts } };
}

export async function getStaticPaths() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return {
    paths: posts.map(post => ({ params: { id: post.id.toString() } })),
    fallback: false
  };
}
```

**When:** content that rarely changes (blogs, docs, marketing pages).

**Cost:** build time scales with number of pages. Stale until the next build.

#### ISR — Incremental Static Regeneration

SSG + **on-demand revalidation**. The first visitor after the revalidation window gets the stale cached page; in the background, a fresh version is built and cached for everyone else.

```javascript
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return {
    props: { posts },
    revalidate: 60 // at most every 60 seconds
  };
}
```

**When:** content that updates periodically but doesn't need real-time freshness — e-commerce catalogs, news feeds, social feeds.

**Cost:** nearly as fast as SSG, slightly stale windows are possible.

#### CSR — Client-Side Rendering (plain React)

Ship a minimal HTML shell + JS bundle; the browser renders everything. Next.js supports this too — just use `useEffect` to fetch.

**When:** internal tools, authenticated dashboards where SEO doesn't matter.

**Cost:** slowest first paint, worst SEO.

#### Strategy comparison

| Strategy | Build time | Request time | Freshness | SEO |
|---|---|---|---|---|
| CSR | Fast | Slow (JS renders) | Real-time | Poor |
| SSR | N/A | Moderate (server renders) | Real-time | Good |
| SSG | Slow | Fast (pre-built) | Stale until rebuild | Good |
| ISR | Moderate | Fast (cached) | Periodic | Good |

**Rule of thumb:**

- SEO-required, per-request data → SSR.
- SEO-required, rarely changing → SSG.
- SEO-required, periodic updates → ISR.
- No SEO, interactive → CSR.

**Gotcha — mixing strategies within one app:** Next.js lets you choose per page. Your marketing pages can be SSG; your product pages can be ISR; your dashboard can be CSR. Don't commit the whole app to one strategy.

**Note on the App Router (Next.js 13+):** The newer `app/` directory uses **React Server Components** and replaces `getStaticProps` / `getServerSideProps` with default-server-component rendering + `fetch` options for caching. The mental model maps: server components are implicit SSR, `revalidate` replaces ISR, `cache: 'no-store'` forces SSR freshness.

---

### How does Next.js routing work?

**Headline (30s):** Next.js uses **file-based routing** — the directory structure *is* the route table. A file at `pages/about.js` serves `/about`; `pages/posts/[id].js` serves `/posts/123` with `id='123'`; `pages/[...slug].js` catches any nested path. Navigate with `<Link>` for client-side transitions (Next prefetches linked pages in the background).

#### File-based routing

```
pages/
  index.js          →  /
  about.js          →  /about
  posts/[id].js     →  /posts/123
  [...slug].js      →  /docs/a/b/c  (catch-all)
```

#### Dynamic routes

```jsx
import { useRouter } from 'next/router';

function Post() {
  const router = useRouter();
  const { id } = router.query;
  return <h1>Post {id}</h1>;
}
```

#### Navigation

```jsx
import Link from 'next/link';

<Link href="/posts/1">Read Post</Link>

// Programmatic
const router = useRouter();
router.push('/posts/1');
```

**Prefetching:** `<Link>` prefetches linked pages in the background (only in production). Client-side navigation is instant because the bundle is already there.

**App Router note:** The new `app/` directory uses slightly different conventions — `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` per route — but the file-based concept is the same.

---

### What are API routes, and when should you use them?

**Headline (30s):** API routes let you define server-side endpoints inside the Next.js project — handy for form submissions, proxying external APIs, and small backend logic without spinning up a separate server. They become serverless functions in production (on Vercel), so they scale automatically but share serverless trade-offs (cold starts, execution limits).

```javascript
// pages/api/hello.js
export default function handler(req, res) {
  if (req.method === 'POST') {
    // ...
  }
  res.status(200).json({ message: 'Hello from Next.js' });
}
```

Supports all HTTP methods. Use for:

- **Form handling** — receive `POST`s without a separate backend.
- **Proxying external APIs** — hide API keys, aggregate multiple calls, work around CORS.
- **Lightweight backend** — webhooks, auth callbacks, simple CRUD.

**Reach for them when:** you need a small amount of server logic colocated with your frontend. For serious backends (complex business logic, queues, databases at scale), use a dedicated backend service.

**App Router note:** The App Router uses `app/api/*/route.ts` with named HTTP-method exports (`export async function GET(request) {...}`) — the file-based concept is the same, the handler signature is different.

**See also:** [`9.2 React Basics`](./9.2%20React%20Basics.md) for the SPA/MPA distinction that SSR/SSG blur, [`7.2 Node.js Fundamentals`](./7.2%20Node.js%20Fundamentals.md) for serverless cold starts and execution limits that constrain API routes.

# 10. Data Structures & Algorithms


## 10.1 Algorithms and Complexity

Reach for this when you need a quick reference for the common algorithmic patterns that show up in frontend interviews — dynamic programming, binary search, two pointers, sorting, and string algorithms. Each section gives the canonical implementation with complexity analysis.

### Dynamic programming

Dynamic programming solves problems by breaking them into overlapping subproblems and storing results to avoid redundant computation. Two implementation styles: **top-down (memoization)** and **bottom-up (iterative)** — bottom-up is usually preferred for constant-space optimizations.

#### Fibonacci

**Recursive** — O(2^n) time, O(n) stack space. Exponential because the same subproblems are re-solved.

```javascript
function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
```

**DP (iterative)** — O(n) time, O(1) space.

```javascript
function fib(n) {
  if (n <= 1) return n;
  let prev = 0, curr = 1;
  for (let i = 2; i <= n; i++) {
    [prev, curr] = [curr, prev + curr];
  }
  return curr;
}
```

#### Climbing stairs (frog jump)

Count the ways to reach step `n` by jumping 1 or 2 steps at a time. Same recurrence as Fibonacci: `dp[i] = dp[i-1] + dp[i-2]`.

Generalized to variable step sizes:

```javascript
function climbStairs(n, steps) {
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1;
  for (let i = 1; i <= n; i++) {
    for (const step of steps) {
      if (i >= step) dp[i] += dp[i - step];
    }
  }
  return dp[n];
}
```

#### 0/1 Knapsack

Maximize total value without exceeding weight capacity. Each item can be used at most once. Iterate capacities **in reverse** so each item isn't reused.

```javascript
function knapsack(W, weights, values) {
  const dp = new Array(W + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let w = W; w >= weights[i]; w--) {
      dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

---

### Binary search

O(log n). **Requires a sorted array**. Halves the search space each iteration.

```javascript
function binarySearch(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) return mid;
    if (nums[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}
```

**Gotcha — integer overflow (other languages):** `(left + right) / 2` can overflow in languages with fixed-width ints. Use `left + (right - left) / 2` to be safe. Not an issue for JS `Number`, but interviewers notice.

---

### Two pointers

A broad family of techniques where two indices sweep through an array — often O(n) replacements for naive O(n²) nested loops.

#### Two Sum on sorted array

```javascript
function twoSum(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left < right) {
    const sum = nums[left] + nums[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return [-1, -1];
}
```

#### Move zeros to end (in-place)

```javascript
function moveZeros(nums) {
  let insertPos = 0;
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] !== 0) {
      [nums[insertPos], nums[i]] = [nums[i], nums[insertPos]];
      insertPos++;
    }
  }
}
```

---

### Sorting

#### Quicksort

Average O(n log n), worst O(n²). Pick a pivot, partition into smaller/larger subarrays, recurse.

```javascript
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = [], mid = [], right = [];
  for (const x of arr) {
    if (x < pivot) left.push(x);
    else if (x > pivot) right.push(x);
    else mid.push(x);
  }
  return [...quickSort(left), ...mid, ...quickSort(right)];
}
```

**Reach for `Array.prototype.sort`** in production code — V8 uses TimSort (stable, O(n log n) worst case) as of Node 10+. Write your own only for an interview.

---

### String algorithms

#### Palindrome check

```javascript
function isPalindrome(n) {
  const s = String(n);
  let left = 0, right = s.length - 1;
  while (left < right) {
    if (s[left++] !== s[right--]) return false;
  }
  return true;
}
```

#### Longest consecutive character

```javascript
function longestConsecutive(s) {
  let maxChar = '', maxLen = 0;
  let curLen = 1;
  for (let i = 1; i <= s.length; i++) {
    if (i < s.length && s[i] === s[i - 1]) {
      curLen++;
    } else {
      if (curLen > maxLen) {
        maxLen = curLen;
        maxChar = s[i - 1];
      }
      curLen = 1;
    }
  }
  return { char: maxChar, len: maxLen };
}
```

#### Number formatting (thousand separators)

```javascript
function formatNumber(n) {
  return n.toLocaleString();
}

function formatNumber(n) {
  const s = String(n);
  let result = '';
  let count = 0;
  for (let i = s.length - 1; i >= 0; i--) {
    result = s[i] + result;
    if (++count % 3 === 0 && i > 0) result = ',' + result;
  }
  return result;
}
```

**Reach for `toLocaleString`** in real code — it handles locales automatically. The manual version is what interviewers want to see.

#### Switch letter case

```javascript
function switchCase(s) {
  return s.split('').map(ch => {
    const code = ch.charCodeAt(0);
    if (code >= 65 && code <= 90)  return String.fromCharCode(code + 32); // A-Z → a-z
    if (code >= 97 && code <= 122) return String.fromCharCode(code - 32); // a-z → A-Z
    return ch;
  }).join('');
}
```

---

### Big-O cheat sheet

| Complexity | Example |
|---|---|
| O(1) | Hash map lookup, array index access |
| O(log n) | Binary search, balanced BST operations |
| O(n) | Single pass over array, linear scan |
| O(n log n) | Efficient sorts (merge, quicksort avg, heap) |
| O(n²) | Nested loops, naive sorts (bubble, insertion) |
| O(2^n) | Naive recursive Fibonacci, power set enumeration |
| O(n!) | Generating all permutations |

**See also:** [`10.2 Core Data Structures`](./10.2%20Core%20Data%20Structures.md) for trees, BSTs, and trie references, [`10.3 Practical Data Structure Implementations`](./10.3%20Practical%20Data%20Structure%20Implementations.md) for LRU, queues, and stacks.

## 10.2 Core Data Structures

Reach for this when you need a quick reference for tree-based data structures — traversals, balanced trees, tries, DOM traversal patterns, and the array↔tree conversion that comes up in real frontend work.

### Tree traversals

Three depth-first orders for a binary tree. Choose based on what you're doing:

- **In-order** (Left → Root → Right) — produces **sorted output** for BSTs.
- **Pre-order** (Root → Left → Right) — useful for **copying** or **serializing** trees.
- **Post-order** (Left → Right → Root) — useful for **deletion** (children before parent).

#### Kth smallest in a BST

In-order traversal visits BST nodes in ascending order. Stop at the k-th node.

```javascript
function kthSmallest(root, k) {
  let count = 0, result = null;

  function inorder(node) {
    if (!node || result !== null) return;
    inorder(node.left);
    if (++count === k) { result = node.val; return; }
    inorder(node.right);
  }

  inorder(root);
  return result;
}
```

---

### Why use binary trees?

| Structure | Access | Insert/Delete |
|---|---|---|
| Array | O(1) | O(n) |
| Linked list | O(n) | O(1) |
| Balanced BST | O(log n) | O(log n) |

A balanced binary tree is the "best of both worlds" between arrays and linked lists — O(log n) for both lookup and modification. **An unbalanced tree degrades to a linked list** with O(n) operations, which is why production code uses self-balancing variants.

---

### Self-balancing trees

#### Red-Black Tree

A BST with coloring rules that keep the tree approximately balanced. Properties:

- Each node is red or black.
- The root is black.
- No two consecutive red nodes on any path.
- All paths from root to leaf have the same number of black nodes.

**Used in:** `std::map` (C++), `TreeMap` (Java), Linux kernel scheduler.

#### B-Tree / B+ Tree

Multi-way search trees optimized for disk I/O. Each node contains multiple keys and children, minimizing the number of disk reads needed.

- **B-Tree** — keys and data in all nodes.
- **B+ Tree** — data only in leaf nodes; leaves are linked for efficient range queries.

**Used in:** database indexes (MySQL InnoDB, PostgreSQL), file systems.

---

### Trie (prefix tree)

A tree where each node represents a character. Paths from the root spell prefixes. Checking if a string is a prefix takes O(m) time where m is the string length — independent of the dictionary size.

**Reach for a trie when:** building autocomplete, spell-check, IP routing tables, or any prefix-based lookup.

---

### DOM tree traversal

#### DFS — depth-first search

Visit the deepest descendants first, then backtrack.

```javascript
function dfs(node) {
  visit(node);
  node.childNodes.forEach(child => dfs(child));
}

// Iterative with an explicit stack
function dfsIterative(node) {
  const stack = [node];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    const children = Array.from(n.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
```

#### BFS — breadth-first search

Visit all siblings level by level.

```javascript
function bfs(node) {
  const queue = [node];
  while (queue.length) {
    const n = queue.shift();
    visit(n);
    n.childNodes.forEach(child => queue.push(child));
  }
}
```

**Reach for DFS** when the order of traversal matters (pre/post) or you want to accumulate something recursively. **Reach for BFS** when you need the shortest path in an unweighted graph or "find the nearest match" semantics.

---

### Array ↔ Tree conversion

A classic interview problem — and a real problem that comes up any time you have to map relational data (flat rows) to hierarchical UI (tree components).

#### Array to tree

```javascript
function arrayToTree(arr) {
  const map = new Map();
  let root = null;

  arr.forEach(item => map.set(item.id, { ...item, children: [] }));

  arr.forEach(item => {
    const node = map.get(item.id);
    if (item.parentId === 0) {
      root = node;
    } else {
      map.get(item.parentId)?.children.push(node);
    }
  });

  return root;
}
```

Two-pass O(n): first pass creates all nodes with empty `children`; second pass links children to parents.

#### Tree to array

```javascript
function treeToArray(tree) {
  const result = [];
  function traverse(node, parentId) {
    result.push({ id: node.id, parentId, name: node.name });
    node.children?.forEach(child => traverse(child, node.id));
  }
  traverse(tree, 0);
  return result;
}
```

**Reach for this pattern when:** persisting tree state to a database (array form is easier), loading tree data from a REST API, or reshaping data for a tree UI component.

**See also:** [`10.1 Algorithms and Complexity`](./10.1%20Algorithms%20and%20Complexity.md) for sorts, searches, and DP patterns, [`10.3 Practical Data Structure Implementations`](./10.3%20Practical%20Data%20Structure%20Implementations.md) for LRU cache, queues, and stacks.

## 10.3 Practical Data Structure Implementations

Reach for this when you need canonical JavaScript implementations of the data structures that come up in interviews — LRU cache, queue, stack — plus a note on how React Fiber uses linked-list structures internally.

### LRU Cache

Least Recently Used cache evicts the least recently accessed item when the cache reaches capacity. A classic interview question testing hash maps and ordering.

#### Using `Map` (insertion order)

JavaScript's `Map` preserves insertion order — we can exploit this by deleting and re-inserting on access, so the "oldest" key is always first.

```javascript
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.cache = new Map();
  }

  get(key) {
    if (!this.cache.has(key)) return -1;
    const value = this.cache.get(key);
    this.cache.delete(key);   // remove...
    this.cache.set(key, value); // ...and re-insert as most recent
    return value;
  }

  put(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
```

**Simpler to write, all operations O(1)** thanks to `Map`'s built-in ordering.

#### Using doubly linked list + hash table (the "classic" form)

The canonical textbook implementation: a hash table for O(1) key lookup, a doubly linked list for O(1) ordering. Most recently used items move to the head; the tail is evicted when full. Interviewers who want to see the "real" DS pattern expect this one.

```javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = {};
    this.head = new ListNode(0, 0); // sentinel
    this.tail = new ListNode(0, 0); // sentinel
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get(key) {
    if (!(key in this.map)) return -1;
    const node = this.map[key];
    this._remove(node);
    this._addToHead(node);
    return node.value;
  }

  put(key, value) {
    if (key in this.map) {
      const node = this.map[key];
      node.value = value;
      this._remove(node);
      this._addToHead(node);
    } else {
      if (Object.keys(this.map).length >= this.capacity) {
        const lru = this.tail.prev;
        this._remove(lru);
        delete this.map[lru.key];
      }
      const newNode = new ListNode(key, value);
      this.map[key] = newNode;
      this._addToHead(newNode);
    }
  }

  _addToHead(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
```

**Reach for the `Map`-based version** in code reviews and production; reach for the linked-list version in interviews that specifically ask you to implement it from scratch.

---

### Queue (FIFO)

First In, First Out. Used in BFS, task scheduling, message processing.

#### Linked-list implementation

Array-based `shift()` is **O(n)** because elements shift down. A linked-list queue is O(1) for both enqueue and dequeue.

```javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  enqueue(val) {
    const node = { val, next: null };
    if (this.tail) this.tail.next = node;
    else           this.head = node;
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (!this.head) return null;
    const val = this.head.val;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return val;
  }
}
```

**Gotcha — don't use `arr.shift()` for a queue** in tight loops. It's O(n) because every element has to shift down a slot. Either use a linked list or track a head index and skip over consumed slots.

---

### Stack (LIFO)

Last In, First Out. Used in DFS, undo/redo, expression parsing, browser history.

```javascript
class Stack {
  constructor() { this.items = []; }
  push(val)  { this.items.push(val); }
  pop()      { return this.items.pop(); }
  peek()     { return this.items[this.items.length - 1]; }
  isEmpty()  { return this.items.length === 0; }
}
```

`push` and `pop` on a JavaScript array are O(1), so a plain array is the canonical implementation.

---

### Linked lists in frontend — React Fiber

**Headline:** React Fiber represents the component tree as a **linked structure** (each fiber node has `child`, `sibling`, and `return` pointers) rather than a traditional tree. This enables:

- **Incremental rendering** — work can be split into small units and spread across frames.
- **Priority-based scheduling** — high-priority updates (input, animations) can interrupt lower-priority rendering.
- **Pause and resume** — rendering yields to the browser for layout and paint, then resumes where it left off.

The linked-list-ish structure is chosen precisely because it's *easy to traverse one unit at a time* — walk to the child, record position, yield. Traditional recursive traversal would block the main thread until the whole tree was done.

**Reach for this knowledge when:** interviewers ask about React's Fiber reconciler, concurrent mode, or how React 18's scheduler works under the hood.

**See also:** [`10.1 Algorithms and Complexity`](./10.1%20Algorithms%20and%20Complexity.md) for algorithmic patterns, [`10.2 Core Data Structures`](./10.2%20Core%20Data%20Structures.md) for tree-based structures, [`9.1 Virtual DOM and Framework Selection`](./9.1%20Virtual%20DOM%20and%20Framework%20Selection.md) for VDOM reconciliation details.

# 11. Performance Optimization


## 11.1 Performance Metrics and Analysis

A bundle of interview questions about how to measure, diagnose, and optimize web app performance.

## What are the Core Web Vitals, and what do they measure?

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

## How do you profile a page in Chrome DevTools?

**Headline (30s):** Three tabs cover 90% of perf work. **Performance** — record a flame chart of CPU/network/rendering to find long tasks and layout thrash. **Network** — waterfall view to find slow/blocking requests. **React DevTools Profiler** — component render times and wasted re-renders. Use Lighthouse (or its CLI) for automated scoring and a ranked list of issues.

- **Performance tab** — record CPU, memory, network, rendering. Screenshots at intervals show when content actually appears.
- **Network tab** — request waterfall, timing breakdown, size analysis.
- **React DevTools** — "Highlight updates when components render" visualizes re-renders.

### Lighthouse

Automated auditing tool that scores Performance, Accessibility, Best Practices, and SEO.

```bash
npx lighthouse https://example.com --view --preset=desktop
```

Lighthouse gives actionable suggestions: modern image formats (WebP/AVIF), eliminate render-blocking resources, reduce unused JavaScript, set explicit image dimensions.

---

## How do you diagnose and fix slow pages?

**Headline:** Split the problem into *slow loading* (network, bundle size, server response) and *slow rendering* (long tasks, bad component structure). Diagnose with the Performance tab; apply the right fix per category.

### Slow loading

- Optimize server response time (backend or edge caching).
- Use a CDN for static assets.
- Enable HTTP caching (`Cache-Control`, `ETag`).
- Route-based code splitting (`React.lazy` + `Suspense`).
- Compress assets (gzip, Brotli).
- Preload critical resources (`<link rel="preload">`).

### Slow rendering

- Profile with DevTools to find long tasks (anything > 50ms).
- Optimize API response times; show loading UI for anything > 200ms.
- Use SSR/SSG for content-heavy pages (see [`9.4 Next.js`](./9.4%20Next.js.md)).
- Virtualize long lists (see [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md)).

---

## How does HTTP caching work?

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

## What's the difference between debounce and throttle?

**Headline (30s):** Both rate-limit a function but with different strategies. **Debounce** — wait until the caller has stopped calling for N ms, then run once. Good when only the final value matters (search input). **Throttle** — run at most once every N ms, ignoring calls in between. Good when steady updates matter (scroll handlers, mousemove).

### Debounce

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

### Throttle

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

## How do you optimize first-screen render?

**Headline:** Do less work, do it sooner, defer the rest. Five tactics to apply in order:

1. **Route lazy loading** — split SPA bundles per route, load on demand (`React.lazy` + `Suspense`).
2. **SSR / SSG** — pre-render HTML on the server for immediate content display.
3. **Above-the-fold prioritization** — inline critical CSS, defer non-critical JS, eager-load LCP image.
4. **Image optimization** — lazy-load below-fold images, use `srcset`, modern formats (WebP/AVIF), explicit dimensions.
5. **Pagination / infinite scroll** — load data incrementally instead of all at once.

**Rule of thumb:** The first screen should render from the minimum amount of JS and CSS needed. Everything else — analytics, chat widgets, secondary content — should be deferred to after LCP.

**See also:** [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md), [`9.4 Next.js`](./9.4%20Next.js.md) for SSR/SSG strategies.

---

## How would you design an analytics SDK with minimal perf impact?

**Headline (30s):** Three design principles: **don't block rendering** (fire-and-forget, no sync work), **batch events** (collect locally, flush periodically), and **use the right transport** (`navigator.sendBeacon` for reliability including page unload; image beacons as fallback). Track page views, custom events, performance metrics, and errors.

### What to track

- **Page Views (PV)** — navigation events via the History API.
- **Custom Events** — business-specific (button clicks, form submissions).
- **Performance Data** — `performance.timing`, Core Web Vitals.
- **Errors** — `window.onerror`, `unhandledrejection` (see [`4.5 Error Handling`](./4.5%20Error%20Handling.md)).

### Reporting strategy

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

### Batching

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

**See also:** [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md) for rendering-side perf, [`5.3 Image Lazy Loading`](./5.3%20Image%20Lazy%20Loading.md) for a focused image-perf playbook.

## 11.2 Rendering and Computation Optimization

A bundle of interview questions on optimizing render performance — virtual scrolling, React-specific techniques, and CSS tips.

## How does virtual scrolling work, and when should you use it?

**Headline (30s):** Rendering a DOM node for every item in a large list (thousands of rows) tanks performance. Virtual scrolling **only renders the visible items plus a small buffer** — the rest is simulated with a spacer element that gives the scrollbar its correct length. As the user scrolls, items off-screen are recycled and new ones enter. Rendering cost becomes O(visible window) instead of O(list size).

### How it works

1. Container has a fixed height with `overflow: auto`.
2. A spacer element creates the full scrollable height.
3. Only items in the visible viewport (plus a few buffer rows) are actually rendered.
4. On scroll, off-screen items unmount and new ones mount.

### Libraries

- **React** — `react-virtualized`, `react-window`, `@tanstack/virtual`.
- **Vue** — `vue-virtual-scroll-list`.

**Trade-off:** Extra implementation complexity for rendering performance that's independent of list size. **Reach for virtual scrolling when** you have more than ~500 items that render eagerly, or any time lists can grow unbounded.

**Gotcha — variable-height items:** Simpler libraries assume fixed row height. Variable heights require measuring each item or using an estimate; `@tanstack/virtual` handles this well, `react-window` requires extra config.

---

## What are the main React performance-tuning techniques?

**Headline (30s):** Focus on three levers: **avoid unnecessary re-renders** (`React.memo` + stable props via `useCallback` / `useMemo`), **keep reconciliation cheap** (stable keys, fragments, reasonable component depth), and **preserve state where mounting is expensive** (toggle with CSS instead of unmounting). Profile before optimizing — most "slow" React is fast enough; the wins come from fixing the specific hotspot.

### Toggle visibility with CSS instead of unmounting

`display: none` keeps the component tree alive but hidden — the component doesn't unmount (state preserved, no re-mount cost). Reach for this when the component is expensive to mount and will toggle back soon.

```jsx
<ExpensiveComponent style={{ display: isVisible ? 'block' : 'none' }} />
```

**Trade-off:** the tree still runs lifecycle and occupies memory. Unmount (via conditional rendering) for truly long-term hidden states.

### Use stable keys in lists

Always use unique, stable IDs as keys. Array indices cause incorrect reconciliation when items are reordered or filtered.

```jsx
{items.map(item => <Item key={item.id} data={item} />)}
```

See [`9.2 React Basics`](./9.2%20React%20Basics.md) for why index keys fail.

### Use fragments to cut DOM depth

```jsx
return (
  <>
    <Header />
    <Content />
  </>
);
```

Less DOM depth = less layout and paint work.

### Avoid inline function definitions in JSX

Inline arrow functions in JSX create new references on every render, bypassing `React.memo` on child components:

```jsx
// Bad: new function reference every render
<Button onClick={() => handleClick(id)} />

// Good: stable reference, memo works as expected
const handleItemClick = useCallback(() => handleClick(id), [id]);
<Button onClick={handleItemClick} />
```

**Gotcha — don't `useCallback` everything.** The cost of `useCallback` itself (closure retention, dependency array check) often exceeds what it saves. Only memoize callbacks that are passed to memoized children on hot paths.

### `shouldComponentUpdate`, `PureComponent`, `React.memo`

**Class components:**

```javascript
shouldComponentUpdate(nextProps, nextState) {
  return nextProps.id !== this.props.id;
}

// Or extend React.PureComponent for automatic shallow comparison
```

**Function components:**

```javascript
const MemoizedComponent = React.memo(MyComponent);

// With custom comparator
const MemoizedComponent = React.memo(MyComponent, (prev, next) => {
  return prev.id === next.id;
});
```

See [`9.3 Advanced React`](./9.3%20Advanced%20React.md) for how to combine `React.memo` with `useCallback` / `useMemo`.

### Debugging workflow

1. **Chrome DevTools Performance tab** — record interactions, find long tasks.
2. **React DevTools Profiler** — visualize component render times, identify wasted re-renders.
3. **"Highlight updates"** — see which components re-render on state changes.
4. **Isolate the problem** — move state closer to where it's needed, split large components, memoize expensive computations.

**Rule of thumb:** Profile first, optimize second. Most perf work is about finding the hotspot — the fix is usually simple once you know where it is.

---

## What CSS performance tips actually matter?

**Headline:** Three patterns with clear wins: **shorthand properties** (smaller files, faster parse), **`will-change` on elements about to animate** (tells the browser to promote to its own compositor layer), and **reduce total DOM size + selector complexity** (directly affects layout time). CSS sprites are mostly obsolete in HTTP/2 world but still useful for icon sets.

### Shorthand properties

```css
/* Verbose */
margin-top: 10px;
margin-right: 20px;
margin-bottom: 30px;
margin-left: 40px;

/* Shorthand */
margin: 10px 20px 30px 40px;
```

Smaller file, less parsing, same result.

### CSS sprites

Combine many small images into one file, use `background-position` to show each. Reduces HTTP requests. **Less relevant with HTTP/2 multiplexing**, but still useful for icon sets where you want atomic loading.

### `will-change`

Hints that a property is about to change, so the browser can promote the element to its own compositor layer ahead of time.

```css
.animated-element {
  will-change: transform, opacity;
}
```

**Use sparingly.** Every `will-change` element uses GPU memory. Apply right before the animation; remove after. Applying to many elements backfires.

See [`2.7 CSS Position, Display, and Animations`](./2.7%20CSS%20Position%2C%20Display%2C%20and%20Animations.md) for how GPU compositing and `transform`/`opacity` avoid layout/paint.

### Reduce selector complexity and DOM depth

- Prefer class selectors over descendant chains (`.btn-primary` beats `div.card > ul > li > a`).
- Avoid deep DOM trees; flatten when possible.
- Drop unused CSS — modern bundlers (PurgeCSS, Tailwind's JIT) can do this automatically.

**See also:** [`2.4 Browser - HTML & CSS part`](./2.4%20Browser%20-%20HTML%20%26%20CSS%20part.md) for reflow/repaint/composite fundamentals, [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md) for how to measure what you're optimizing.

# 12. Architecture & Design Patterns


## 12.1 Software Design Principles

A bundle of interview questions on the design principles that separate maintainable frontend code from the kind that rots.

## What are the SOLID principles, and what does each mean?

**Headline (30s):** Five principles — **S**ingle responsibility (one reason to change), **O**pen/closed (extend via new code, not modification), **L**iskov substitution (subtypes work as base types), **I**nterface segregation (many small interfaces beat one fat one), **D**ependency inversion (depend on abstractions, not concretes). Together they push you toward small, decoupled pieces that are easy to change without breaking the rest of the system.

### Single Responsibility Principle (SRP)

A class or module should have only one reason to change.

```javascript
// Violates SRP: handles both data fetching and rendering
class UserPage {
  fetchUser() { /* ... */ }
  renderUser() { /* ... */ }
}

// Follows SRP: separate concerns
class UserService { fetchUser() { /* ... */ } }
class UserView    { render(user) { /* ... */ } }
```

**Frontend example:** A React component that fetches data, transforms it, and renders UI violates SRP. Split into a data hook + a dumb presentational component.

### Open/Closed Principle (OCP)

Open for extension, closed for modification. Add behavior by writing new code, not changing existing code.

```javascript
class ShippingCalculator {
  constructor(strategy) { this.strategy = strategy; }
  calculate(pkg) { return this.strategy.calculate(pkg); }
}

class ExpressShipping  { calculate(pkg) { return pkg.weight * 10; } }
class StandardShipping { calculate(pkg) { return pkg.weight * 5; } }
```

New shipping types? Add a new strategy class — no change to `ShippingCalculator`.

### Liskov Substitution Principle (LSP)

Subtypes must be substitutable for their base types without breaking correctness. A classic violation: `Bird` has `fly()`, `Penguin extends Bird` throws on `fly()` — `Penguin` is not a proper subtype of `Bird` in that design. The fix is usually to rethink the hierarchy (composition, or narrower base classes).

### Interface Segregation Principle (ISP)

Clients shouldn't be forced to depend on methods they don't use. Prefer many small, focused interfaces over one giant one. In TypeScript, this often means splitting a 20-field type into several 3–5 field types composed via intersection.

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions, not concrete implementations.

```javascript
class NotificationService {
  constructor(sender) { this.sender = sender; }
  notify(message) { this.sender.send(message); }
}

class EmailSender { send(msg) { /* send email */ } }
class SmsSender   { send(msg) { /* send SMS   */ } }

new NotificationService(new EmailSender());
new NotificationService(new SmsSender());
```

**DIP is the foundation of dependency injection** — testable code, swappable implementations, no hard-coded dependencies.

---

## What are DRY, KISS, and YAGNI?

**Headline:** Three pragmatic rules. **DRY** — every piece of knowledge has one canonical representation, duplication is a smell. **KISS** — simpler is better than clever. **YAGNI** — don't build it until you actually need it.

### DRY (Don't Repeat Yourself)

Extract repeated logic into shared functions, hooks, or modules. But be careful — coupling is a cost. Sometimes two functions that *look* similar should stay separate because they represent different concepts that happen to share syntax today. **Premature DRY creates false abstractions** that are harder to maintain than the duplication they replaced.

### KISS (Keep It Simple, Stupid)

Prefer the simplest solution that works. Complexity should be justified by concrete requirements, not anticipated future needs. A common frontend failure: pulling in a state-management library for a page that needs three pieces of local state.

### YAGNI (You Aren't Gonna Need It)

Don't implement functionality until it's actually needed. Premature abstraction adds maintenance burden without delivering value. The framework you're planning to swap to in six months? Build for what you need today; refactor when the day comes.

**How to apply all three:** Write the obvious, simple code first. When you see a real duplication pattern (three or more, different places), extract. When you need flexibility (not before), add the seam.

---

## What are common frontend architecture patterns?

**Headline:** Three patterns dominate modern frontends. **Component-based architecture** — UIs as trees of self-contained components (the React / Vue model). **Unidirectional data flow (Flux)** — data flows one way, making state changes predictable (Redux, Zustand, Pinia). **Micro-frontends** — split the app into independently deployable pieces, trading complexity for team autonomy.

### Component-based architecture

Modern frameworks organize UIs as trees of reusable, self-contained components. Each component owns its state, rendering logic, and (optionally) side effects. Benefits: reusability, isolation, clear responsibility boundaries.

### Flux / unidirectional data flow

Data flows one way: **Action → Dispatcher → Store → View**. The view can dispatch new actions, but cannot mutate the store directly. Predictability makes debugging and testing easier.

Implementations: Redux, Zustand, MobX (variant), Pinia. See [`9.3 Advanced React`](./9.3%20Advanced%20React.md) for context + patterns that replace Redux in simpler apps.

### Micro-frontends

Splitting a large frontend into independently deployable apps, each owned by a different team. Common approaches: module federation (Webpack 5), iframes, web components, and build-time composition.

**When to reach for it:** large orgs with multiple teams that need deployment autonomy. **When to avoid it:** most apps. The infrastructure complexity, cross-app consistency issues, and runtime overhead almost always dwarf the benefits until you're at significant org scale.

**See also:** [`12.2 Design Patterns in Practice`](./12.2%20Design%20Patterns%20in%20Practice.md) for the GoF patterns that implement these principles.

## 12.2 Design Patterns in Practice

A bundle of interview questions on the design patterns that come up most in frontend work — plus two system-design mini-problems (low-code editor, RBAC) that exercise those patterns.

## When do you use the Factory pattern?

**Headline (30s):** A factory is a function that encapsulates object creation — hiding `new`, hiding conditional logic, and allowing the factory to return different subtypes based on input. Reach for it when construction is non-trivial or when callers shouldn't need to know which concrete class they're getting. It's arguably the most common pattern in JS because it plays nicely with the language's bias toward plain functions.

```javascript
function createButton(type) {
  if (type === 'primary')   return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
```

**Real-world examples:** `React.createElement()`, jQuery's `$()`, `document.createElement()`, `Array.of`.

---

## When do you use the Singleton pattern?

**Headline:** Guarantees one instance across the app, with a single global access point. Reach for it when a shared resource (store, event bus, cache, connection pool) must be consistent across consumers.

```javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) {
      Store.instance = new Store();
    }
    return Store.instance;
  }
}
```

**Real-world examples:** Redux/Vuex store, global event bus, database connection pool, `window` object.

**Gotcha — singletons hurt testability.** Global state is hard to isolate in tests. Modern apps often sidestep the pattern with **context providers** (React) or **module-scoped singletons** (one instance per module, but injectable in tests). Ask yourself whether "one instance" is the real requirement, or whether "shared instance for this context" would work — the latter is usually better.

---

## When do you use the Strategy pattern?

**Headline (30s):** Defines a family of interchangeable algorithms, each encapsulated behind the same interface. Pick one by key instead of writing a giant switch/if-else. Reach for it when you have multiple algorithms for the same concern (sort, validate, format, price) and callers need to pick at runtime.

```javascript
const strategies = {
  express:   pkg => pkg.weight * 10,
  standard:  pkg => pkg.weight * 5,
  overnight: pkg => pkg.weight * 20,
};

function calculateShipping(strategy, pkg) {
  return strategies[strategy](pkg);
}

calculateShipping('express', { weight: 3 }); // 30
```

**Use cases:** form validation rules, sort algorithms, pricing tiers, authentication methods.

Strategy is the natural implementation of the **Open/Closed Principle** (see [`12.1 Software Design Principles`](./12.1%20Software%20Design%20Principles.md)) — add new strategies without touching the dispatcher.

---

## What's the difference between Observer and Publish-Subscribe?

**Headline (30s):** Both let something react to something else, but differ in **coupling**. **Observer** — the subject holds a direct reference to its observers and calls them itself (`element.addEventListener` fits this model). **Publish-Subscribe** — a central channel mediates; publishers and subscribers never know about each other (event bus). Pub-Sub is more decoupled and flexible; Observer is simpler and easier to trace.

### Observer

```javascript
class Subject {
  constructor() { this.observers = []; }
  subscribe(observer) { this.observers.push(observer); }
  notify(data) { this.observers.forEach(obs => obs.update(data)); }
}
```

**Coupling:** direct. The subject knows its observers.

**Example:** DOM event listeners — the element "knows" every handler it fires.

### Publish-Subscribe

```javascript
const eventBus = new EventBus();
eventBus.on('user:login', updateDashboard);       // subscriber
eventBus.emit('user:login', { name: 'Alice' });   // publisher
```

**Coupling:** indirect — both parties know only the event channel and event name.

**Key difference:** Observer is easier to debug (you can find observers by inspecting the subject); Pub-Sub is more flexible but harder to trace because the wiring is scattered across the codebase.

See [`5.1 DOM Manipulation and Events`](./5.1%20DOM%20Manipulation%20and%20Events.md) for a concrete EventBus implementation.

---

## How would you design the data model for a low-code editor?

**Headline (30s):** A drag-and-drop page builder needs four systems: **a component tree** (each node has id, type, props, style, children), **layer ordering** (z-index via array position), **undo/redo** (command pattern with a history stack), and **real-time collaboration** (WebSocket state sync with conflict resolution, usually OT or CRDT).

### Component model

```javascript
const component = {
  id:    'comp_001',
  type:  'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
```

The tree is the source of truth. Rendering walks the tree; the sidebar edits the tree; persistence serializes the tree.

### Key requirements

- **Component registry** — a map of `type → renderer` so new component types can be added without touching the core.
- **Layer management** — z-index is the array order within `children`; reordering is a splice.
- **Undo/redo** — command pattern with a history stack. Each mutation pushes a reversible command; undo pops and inverts.
- **Real-time collaboration** — WebSocket broadcasts mutations; OT/CRDT resolves conflicts (see [`5.2 Browser Storage and Communication`](./5.2%20Browser%20Storage%20and%20Communication.md)).

---

## How does Role-Based Access Control (RBAC) work?

**Headline:** RBAC assigns permissions to **roles**, not users. Users are then assigned one or more roles. Adding a new role or changing a role's permissions doesn't require touching user records or app code — only the role and permission tables.

### Data model

- **User** — `id`, `username`, `password_hash`
- **Role** — `id`, `role_name` (e.g., admin, editor, viewer)
- **Permission** — `id`, `permission_name` (e.g., read, write, delete)
- **UserRole** — `user_id`, `role_id` (many-to-many)
- **RolePermission** — `role_id`, `permission_id` (many-to-many)

### Access check flow

```
User → UserRole → Role → RolePermission → Permission
```

To check "can this user write?", look up their roles, then the permissions on those roles, then check if `write` is in the set.

**Why this structure:** the indirection through `Role` is what makes RBAC scalable. Assigning a permission to a role changes it for everyone with that role. Assigning a role to a user gives them every permission the role has. No code changes needed.

**See also:** [`12.1 Software Design Principles`](./12.1%20Software%20Design%20Principles.md) for the SOLID foundations these patterns implement, [`5.1 DOM Manipulation and Events`](./5.1%20DOM%20Manipulation%20and%20Events.md) for a concrete EventBus.

# 13. Libraries


## 13.1 Lodash

**Reach for this when** you need a quick reference for Lodash utilities — the functions that still earn their place in a modern codebase (`_.get`, `_.cloneDeep`, `_.debounce`) versus the ones that are now one-liners with native JS.

**Headline:** Lodash is a utility library covering four buckets — **Array**, **Collection**, **Object**, **Function**, **String**. Most of its value today lives in **deep-object helpers** (`_.get`, `_.set`, `_.merge`, `_.cloneDeep`) and **robust debounce/throttle**. Many simpler utilities have native equivalents; check before adding the dependency.

### Array utilities

| Function | Description | Example |
|---|---|---|
| `_.chunk(arr, size)` | Split into chunks of `size` | `_.chunk([1,2,3,4], 2)` → `[[1,2],[3,4]]` |
| `_.compact(arr)` | Remove falsy values | `_.compact([0,1,false,2,'',3])` → `[1,2,3]` |
| `_.difference(arr, values)` | Elements in `arr` not in `values` | `_.difference([2,1],[2,3])` → `[1]` |
| `_.drop(arr, n)` | Remove first `n` elements | `_.drop([1,2,3], 2)` → `[3]` |
| `_.flatten(arr)` | Flatten one level | `_.flatten([1,[2,[3]]])` → `[1,2,[3]]` |
| `_.flattenDeep(arr)` | Flatten recursively | `_.flattenDeep([1,[2,[3]]])` → `[1,2,3]` |
| `_.uniq(arr)` | Remove duplicates | `_.uniq([1,1,2,3,3])` → `[1,2,3]` |
| `_.intersection(a, b)` | Common elements | `_.intersection([1,2],[2,3])` → `[2]` |

### Collection utilities

| Function | Description |
|---|---|
| `_.filter(col, predicate)` | Keep elements where predicate is truthy |
| `_.find(col, predicate)` | First matching element |
| `_.map(col, iteratee)` | Transform each element |
| `_.reduce(col, iteratee, acc)` | Reduce to single value |
| `_.groupBy(col, iteratee)` | Group by key |
| `_.sortBy(col, iteratees)` | Sort by one or more criteria |
| `_.orderBy(col, keys, orders)` | Sort with explicit asc/desc |

### Object utilities

| Function | Description |
|---|---|
| `_.get(obj, path, default)` | Safe deep property access |
| `_.set(obj, path, value)` | Set nested property |
| `_.merge(target, ...sources)` | Deep recursive merge |
| `_.omit(obj, paths)` | New object without specified keys |
| `_.pick(obj, paths)` | New object with only specified keys |
| `_.assign(target, ...sources)` | Shallow copy own properties |
| `_.cloneDeep(obj)` | Deep clone |

`_.get` is especially valuable for safely accessing deeply nested properties:

```javascript
const city = _.get(user, 'address.city', 'Unknown');
```

### Function utilities

#### `_.debounce(fn, wait, options)`

Delays invocation until `wait` ms after the last call. Options: `leading` (invoke on first call), `trailing` (invoke after wait), `maxWait` (maximum delay before forced invocation).

```javascript
const search = _.debounce(fetchResults, 300);
input.addEventListener('input', search);
```

#### `_.throttle(fn, wait, options)`

Invokes at most once per `wait` ms. Options: `leading`, `trailing`.

```javascript
window.addEventListener('scroll', _.throttle(updatePosition, 100));
```

**Why Lodash's versions beat a hand-rolled debounce:** proper `cancel()`/`flush()` methods, `leading` + `trailing` combinations, and `maxWait` (which guarantees eventual execution even under constant calls).

### String utilities

| Function | Example |
|---|---|
| `_.camelCase('foo bar')` | `'fooBar'` |
| `_.kebabCase('fooBar')` | `'foo-bar'` |
| `_.snakeCase('fooBar')` | `'foo_bar'` |
| `_.capitalize('hello')` | `'Hello'` |
| `_.startCase('fooBar')` | `'Foo Bar'` |

### When to reach for Lodash (vs. native)

Lodash earns its place when:

- Working with **deeply nested data** (`_.get`, `_.set`, `_.merge`).
- Needing **reliable debounce/throttle** with edge options.
- **Collection transformations** that would need multiple native chained methods.

**Native equivalents worth checking first:**

| Lodash | Native |
|---|---|
| `_.flatten`, `_.flattenDeep` | `arr.flat(Infinity)` |
| `_.get(obj, 'a.b.c')` | `obj?.a?.b?.c` (optional chaining) |
| `_.uniq([...])` | `[...new Set([...])]` |
| `_.pick`, `_.omit` | Destructuring + rest |
| `_.keys`, `_.values`, `_.entries` | `Object.keys`, etc. |

**Bundle-size gotcha:** `import _ from 'lodash'` pulls in the whole library. Prefer `import get from 'lodash/get'` or switch to `lodash-es` + tree-shaking, which can cut bundles by hundreds of KB.

**See also:** [`3.8 Modern JavaScript Features`](./3.8%20Modern%20JavaScript%20Features.md) for native alternatives like `structuredClone`, [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md) for debounce/throttle decision guide.

## 13.2 ahooks

**Reach for this when** you need a quick reference for ahooks — the React hooks library that covers the hooks people keep rewriting in every project (data fetching, debounced state, localStorage sync, stable callbacks, virtual lists).

**Headline:** ahooks is an Alibaba-maintained React hooks library with production-ready hooks in five buckets — **Data fetching** (`useRequest`, `usePagination`, `useInfiniteScroll`), **State** (`useBoolean`, `useToggle`, `useMap`, `useLocalStorageState`, `useLatest`), **Performance** (`useMemoizedFn`, `useCreation`, `useVirtualList`), **Lifecycle/timing** (`useMount`, `useUnmount`, `useDebounce`, `useThrottle`), and **Dynamic lists** (`useDynamicList`). Install with `npm install ahooks`.

### Data fetching

#### `useRequest`

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

#### `usePagination`

Extends `useRequest` for paginated lists with automatic page state management.

```javascript
const { data, loading, pagination } = usePagination(fetchUsers, {
  defaultPageSize: 20,
});

pagination.changeCurrent(2);
pagination.changePageSize(50);
```

#### `useInfiniteScroll`

Infinite scroll loading with threshold detection.

```javascript
const { data, loading, noMore } = useInfiniteScroll(
  d => fetchMoreItems(d?.nextCursor),
  { target: containerRef, threshold: 100 }
);
```

### State hooks

#### `useToggle` / `useBoolean`

```javascript
const [state, { toggle, setTrue, setFalse }] = useBoolean(false);
```

`useToggle` generalizes to any two values.

#### `useMap` / `useSet`

State management for `Map` and `Set` with convenient mutation helpers.

```javascript
const [map, { set, remove, reset }] = useMap([['key1', 'value1']]);
set('key2', 'value2');
remove('key1');
```

#### `useLocalStorageState`

State that auto-syncs with `localStorage`, handles serialization and errors.

```javascript
const [theme, setTheme] = useLocalStorageState('theme', {
  defaultValue: 'light',
});
```

#### `useLatest`

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

### Performance hooks

#### `useMemoizedFn`

Like `useCallback` but without a dependency array. Returns a stable function reference that always invokes the *latest* version of the function. No stale closures, no manual dep tracking.

```javascript
const handleClick = useMemoizedFn(() => {
  console.log(count);
});
```

**Reach for it instead of `useCallback`** when you want a stable reference but always the freshest state. Significantly safer in practice.

#### `useCreation`

A more reliable `useMemo` that guarantees referential stability and never recalculates unnecessarily (unlike `useMemo`, which the React docs warn may re-run even without dep changes).

#### `useVirtualList`

Virtualizes long lists — renders only visible items.

```javascript
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(
  originalList,
  { itemHeight: 50, overscan: 5 }
);
```

See [`11.2 Rendering and Computation Optimization`](./11.2%20Rendering%20and%20Computation%20Optimization.md) for virtual scrolling background.

### Lifecycle hooks

#### `useMount` / `useUnmount`

Cleaner alternatives to `useEffect` for mount-only or unmount-only logic.

```javascript
useMount(() => { console.log('mounted'); });
useUnmount(() => { console.log('unmounted'); });
```

#### `useDebounce` / `useDebounceFn`

```javascript
const debouncedValue = useDebounce(searchTerm, { wait: 300 });
const { run: debouncedSearch } = useDebounceFn(search, { wait: 300 });
```

#### `useThrottle`

```javascript
const throttledValue = useThrottle(scrollPosition, { wait: 100 });
```

### Dynamic lists

#### `useDynamicList`

Manages ordered lists with immutable operations and **stable keys** for rendering.

```javascript
const { list, push, remove, move, insert, getKey } = useDynamicList([
  { name: 'Alice' },
  { name: 'Bob' },
]);
```

Each item gets a stable key via `getKey(index)` — solves the "what do I use as key?" problem for dynamic forms and sortable lists.

### When to reach for ahooks (vs. hand-rolled)

Reach for ahooks when:

- You're writing the same fetching/debouncing/storage patterns across multiple components.
- You need **production-ready edge-case handling** (cancellation, error retry, stale closures).
- You want **stable references** without fiddling with `useCallback` dependencies.

**Alternatives worth considering:**

- `react-query` / `@tanstack/query` — more focused, richer caching than `useRequest` for server state.
- `swr` — similar philosophy, lighter API surface.
- `zustand` — for shared state rather than per-component hook state.

**See also:** [`9.3 Advanced React`](./9.3%20Advanced%20React.md) for custom hook patterns, [`11.1 Performance Metrics and Analysis`](./11.1%20Performance%20Metrics%20and%20Analysis.md) for debounce/throttle conceptual background.

# 14. Professional Skills


## 14.1 Interview Tips

**Reach for this when** you need a quick reference for the behavioral side of a frontend interview — framing your strengths/weaknesses, answering "why us", discussing salary, and asking good questions back.

**Headline:** Strong behavioral answers share three qualities — **concrete** (backed by specific examples), **relevant** (tied to the role), and **self-aware** (honest about gaps with a plan to close them). Avoid generic phrasing; interviewers hear "I'm a perfectionist" from 90% of candidates.

### Discussing strengths and weaknesses

#### Strengths

Focus on qualities directly relevant to the role. Back each with a concrete example:

- "I'm detail-oriented — in my last project, I caught a data race condition during code review that would have caused intermittent production failures."
- "I learn quickly — I picked up TypeScript and migrated our codebase within two weeks of joining."

#### Weaknesses

Pick real weaknesses that don't conflict with core job requirements, and show how you're addressing them:

- "I sometimes spend too long optimizing code before shipping. I've learned to set time-boxed goals and ship iteratively."
- "I'm less experienced with backend systems. I've been building side projects with Node.js to broaden my skills."

**Avoid** clichés like "I'm a perfectionist" or "I work too hard."

### Salary expectations

- **Research** market rates for your role, level, and location before the interview.
- **Express genuine interest first:** "I'm most interested in the technical challenges and growth opportunities."
- **Provide a range**, not a fixed number: "Based on my research and experience, I'm looking at X–Y, open to discussion based on the full package."
- **If pressed early:** "I'd prefer to understand the role better before discussing numbers."

### Why are you a good fit?

Three pillars:

1. **Skills match** — map your technical skills to their requirements.
2. **Experience alignment** — relevant projects and outcomes.
3. **Cultural fit** — understanding of their product, mission, or engineering culture.

> "Your team is building a high-traffic React application with a focus on performance. I've spent the last two years optimizing rendering performance and implementing virtual scrolling at scale, which directly aligns with your challenges."

### Company research

Show you've done your homework:

- Understand the company's product, market position, and recent developments.
- Connect your skills to their specific needs.
- If you're less familiar, be honest: "I've read about your recent launch of X. I'd love to learn more about the technical stack behind it."

### Addressing lack of experience

- Acknowledge that experience matters, then pivot to your strengths.
- Emphasize transferable skills, learning ability, concrete rapid-ramp examples.

> "While I haven't worked with GraphQL in production, I've built several projects with it and understand the patterns. I'm confident I can be productive within the first sprint."

### Questions to ask the interviewer

**About the role:**

- "What does a typical day look like for someone in this role?"
- "What are the biggest technical challenges the team is facing right now?"
- "How do you measure success for this position in the first 6 months?"

**About the team:**

- "What's the team's approach to code review and knowledge sharing?"
- "How are technical decisions made — top-down or consensus-driven?"

**About growth:**

- "What learning and development opportunities are available?"
- "What does the career progression path look like for engineers here?"

### Closing the interview

- Thank the interviewer for their time.
- Reiterate interest: "This conversation reinforced my excitement about the role. I'd love the opportunity to contribute to the team."
- Ask about next steps: "What does the rest of the process look like?"

**Gotcha — don't skip asking questions.** "No questions" signals lack of interest. Prepare 3–5 in advance, even if your core questions got answered; you can always add "I was curious about X, but you covered it earlier — can you expand on Y?"

## 14.2 Agile and Scrum

**Reach for this when** you need a quick reference for how most modern engineering teams organize work — Agile principles, the Scrum framework (roles, events, artifacts), and the common failure modes.

**Headline:** **Agile** is a philosophy — iterative delivery, continuous feedback, adaptability. **Scrum** is the most widely used framework for practicing Agile, with defined **roles** (Product Owner, Scrum Master, Dev Team), **events** (Sprint, Planning, Standup, Review, Retro), and **artifacts** (Product Backlog, Sprint Backlog, Increment). Interviewers usually want to know you understand both the theory and the real-world tradeoffs.

### Agile principles

From the Agile Manifesto:

- **Working software** over comprehensive documentation.
- **Customer collaboration** over contract negotiation.
- **Responding to change** over following a rigid plan.
- **Individuals and interactions** over processes and tools.

#### In practice

- Deliver working software in short iterations (1–4 weeks).
- Welcome changing requirements, even late in development.
- Business and development teams work together daily.
- Build projects around motivated individuals; trust them to deliver.
- Maintain a sustainable development pace.
- Regularly reflect and adjust processes.

#### Benefits

- **Flexibility** — adapt to changing requirements without derailing the project.
- **Quality** — frequent testing and integration catch issues early.
- **Visibility** — regular demos and retrospectives keep stakeholders informed.
- **Reduced risk** — short iterations surface problems quickly.

### Scrum framework

Scrum is the most widely used Agile framework. It defines roles, events, and artifacts for organizing iterative work.

#### Roles

##### Product Owner

- Defines and prioritizes the **product backlog**.
- Represents stakeholder interests.
- Decides **what** to build and in what order.

##### Scrum Master

- Facilitates the Scrum process; removes impediments.
- Coaches the team on Scrum practices.
- Shields the team from external interruptions.
- **Does not** manage the team — the team is self-organizing.

##### Development Team

- Cross-functional group that designs, builds, and tests the product.
- Typically 3–9 people.
- Self-organizing: the team decides **how** to accomplish sprint goals.

#### Events

##### Sprint

A fixed time-box (usually 2 weeks) during which a potentially shippable increment is created.

##### Sprint Planning

The team selects backlog items for the sprint and breaks them into tasks. Outcome: a sprint goal + a sprint backlog.

##### Daily Standup

A 15-minute daily meeting where each member answers:

1. What did I do yesterday?
2. What will I do today?
3. Are there any blockers?

##### Sprint Review

End-of-sprint demo to stakeholders. Gather feedback and update the product backlog.

##### Sprint Retrospective

The team reflects on the sprint process:

- What went well?
- What could be improved?
- What actions will we take?

#### Artifacts

- **Product Backlog** — ordered list of everything needed in the product.
- **Sprint Backlog** — items selected for the current sprint + the delivery plan.
- **Increment** — the sum of completed backlog items, in a usable state.

### Common challenges

- **Scope creep** — adding items mid-sprint undermines the sprint commitment. Use the backlog for new requests; slot into future sprints.
- **Resistance to change** — teams used to waterfall may struggle with iterative planning. Start with pilot teams and demonstrate results.
- **Skipping retrospectives** — without reflection, the same problems recur. Retrospectives are **not optional**.
- **"Status-report standups"** — standups that become PM status updates defeat the purpose. Keep the "blockers" slot prominent.

**Gotcha — Scrum isn't a silver bullet.** It works best for teams building iterative products with changing requirements. For heavily regulated work (e.g., hardware, medical devices) or teams with fixed requirements, waterfall or hybrid models may still fit. Interviewers appreciate candidates who understand *when* Agile helps, not just how to recite the ceremonies.

**See also:** [`14.1 Interview Tips`](./14.1%20Interview%20Tips.md) for how to discuss Agile experience in interviews.

## 15.1 Frontend Testing

**Reach for this when** you need a quick reference for frontend testing — the test pyramid, Jest/Vitest APIs, mocking, React Testing Library, and patterns like Arrange-Act-Assert.

**Headline:** Five buckets. **Testing pyramid** (unit-heavy, e2e-light). **Jest fundamentals** (`describe`, `it`, matchers, setup/teardown). **Mocking** (`jest.fn`, `jest.mock`, `jest.spyOn`). **React Testing Library** (user-facing queries, `userEvent`, async utilities). **Testing patterns** (AAA, async, custom hooks, snapshots).

### Testing pyramid

Tests should distribute with many fast unit tests at the base, fewer integration tests in the middle, fewest expensive e2e tests at the top.

| Level | Count | Scope | Tools |
|---|---|---|---|
| **Unit** | Most | Single function/component in isolation | Jest, Vitest |
| **Integration** | Middle | Multiple units working together | Jest + RTL, Vitest + Testing Library |
| **E2E** | Fewest | Full app in real browser | Playwright, Cypress, Puppeteer |

- **Unit tests** — fast, cheap, isolate logic. Test pure functions, utilities, individual component behavior.
- **Integration tests** — verify components interact correctly with hooks, context, API mocks.
- **E2E tests** — slow, expensive. Catch real user flows; use sparingly on critical paths.

**Gotcha — inverted pyramids are a common anti-pattern.** Teams over-relying on e2e tests get slow, flaky suites. Push tests down the pyramid whenever possible.

### Jest fundamentals

#### `describe`, `it` / `test`

```javascript
describe('Calculator', () => {
  it('adds two numbers', () => {
    expect(1 + 2).toBe(3);
  });

  test('subtracts two numbers', () => {
    expect(5 - 3).toBe(2);
  });
});
```

`describe` groups tests; `it` and `test` are interchangeable.

#### Common matchers

| Matcher | Use Case |
|---|---|
| `toBe(value)` | Strict equality (`===`). Use for primitives. |
| `toEqual(value)` | Deep equality. Use for objects/arrays. |
| `toBeTruthy()` / `toBeFalsy()` | Boolean coercion |
| `toBeNull()` / `toBeUndefined()` | Null/undefined checks |
| `toThrow()` / `toThrow(error)` | Exception assertion |
| `toContain(item)` | Array/string contains |
| `toHaveLength(n)` | Array/string length |
| `toMatch(regex)` | String matches regex |
| `toBeGreaterThan(n)` / `toBeLessThan(n)` | Number comparison |

```javascript
expect(2 + 2).toBe(4);
expect({ a: 1 }).toEqual({ a: 1 });
expect([1, 2, 3]).toContain(2);
expect(() => fn()).toThrow('error message');
```

#### Setup and teardown

```javascript
describe('Database', () => {
  beforeAll(()  => { /* runs once before all tests */ });
  afterAll(()   => { /* runs once after all tests */ });
  beforeEach(() => { /* runs before each test */ });
  afterEach(()  => { /* runs after each test */ });
});
```

### Mocking

#### `jest.fn()`

Creates a mock function that tracks calls and return values.

```javascript
const mockFn = jest.fn();
mockFn(1, 2);
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith(1, 2);
expect(mockFn).toHaveBeenCalledTimes(1);

mockFn.mockReturnValue(42);
expect(mockFn()).toBe(42);
```

#### `jest.mock()`

Mocks an entire module. Hoisted to the top of the file.

```javascript
jest.mock('./api');
import { fetchUser } from './api';

test('uses mocked fetchUser', async () => {
  fetchUser.mockResolvedValue({ id: 1, name: 'Alice' });
  const user = await fetchUser();
  expect(user.name).toBe('Alice');
});
```

#### `jest.spyOn()`

Spies on an existing method without replacing the module. Restore with `mockRestore()`.

```javascript
const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
// ... test
spy.mockRestore();
```

#### Async mocks

```javascript
const mockFetch = jest.fn();

mockFetch.mockResolvedValue({ data: 'success' });
mockFetch.mockRejectedValue(new Error('Network error'));

mockFetch
  .mockResolvedValueOnce({ page: 1 })
  .mockResolvedValueOnce({ page: 2 });
```

### React Testing Library (RTL)

#### Philosophy

Test from the user's perspective: what they see and do. **Avoid testing implementation details** (state, props, internal methods). Implementation changes shouldn't break tests; user-visible behavior changes should.

#### Core API

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

render(<MyComponent />);

screen.getByText('Submit');        // throws if not found
screen.queryByText('Optional');    // returns null if not found
screen.findByText('Async');        // returns Promise; waits for element
screen.getByRole('button', { name: /submit/i });
screen.getByTestId('custom-id');   // last resort
```

#### Query priority

1. `getByRole` — accessibility-first, closest to real users.
2. `getByLabelText` — forms.
3. `getByPlaceholderText` — forms (fallback).
4. `getByText` — non-interactive content.
5. `getByDisplayValue` — form values.
6. `getByAltText` — images.
7. `getByTitle` — title attribute.
8. `getByTestId` — last resort.

#### User interactions

Prefer `userEvent` over `fireEvent` — `userEvent` simulates real user behavior including proper event order, focus changes, and keyboard events.

```jsx
import userEvent from '@testing-library/user-event';

await userEvent.click(screen.getByRole('button'));
await userEvent.type(screen.getByLabelText('Email'), 'test@example.com');

fireEvent.click(button); // lower-level, avoid unless needed
fireEvent.change(input, { target: { value: 'text' } });
```

#### Async utilities

```jsx
import { waitFor } from '@testing-library/react';

// waitFor — retries until assertion passes or timeout
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// findBy* — shorthand for waitFor + getBy
const button = await screen.findByRole('button', { name: 'Submit' });
```

#### Example: form submission

```jsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

test('submits form with email and password', async () => {
  const onSubmit = jest.fn();
  render(<LoginForm onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
  await userEvent.type(screen.getByLabelText(/password/i), 'secret123');
  await userEvent.click(screen.getByRole('button', { name: /submit/i }));

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'secret123',
    });
  });
});
```

### Testing patterns

#### Arrange-Act-Assert (AAA)

Structure tests in three clear phases for readability.

```jsx
test('increments counter', async () => {
  // Arrange
  render(<Counter />);
  const button = screen.getByRole('button', { name: /increment/i });

  // Act
  await userEvent.click(button);

  // Assert
  expect(screen.getByText('1')).toBeInTheDocument();
});
```

#### Testing async operations

```jsx
test('loads user data', async () => {
  jest.spyOn(api, 'fetchUser').mockResolvedValue({ name: 'Alice' });

  render(<UserProfile userId={1} />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  const name = await screen.findByText('Alice');
  expect(name).toBeInTheDocument();
});
```

#### Testing custom hooks with `renderHook`

```javascript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

test('increments counter', () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

#### Snapshot testing

**Use when** — stable UI components, layout/structure regression.
**Avoid when** — frequently changing UI, large snapshots, behavior testing.

```jsx
test('matches snapshot', () => {
  const { container } = render(<Header />);
  expect(container).toMatchSnapshot();
});
```

Prefer explicit assertions over snapshots when testing behavior. Update snapshots intentionally with `jest -u`.

**See also:** [`9.3 Advanced React`](./9.3%20Advanced%20React.md) for custom-hook patterns under test, [`16.1 Git Essentials`](./16.1%20Git%20Essentials.md) for PR workflow that integrates CI tests.

## 16.1 Git Essentials

**Reach for this when** you need a quick reference for day-to-day Git — core commands, branching, merge vs. rebase, conflict resolution, and the PR workflow.

**Headline:** Six buckets. **Core commands** (init, clone, add, commit, status, log, diff). **Remote operations** (push, pull, fetch). **Branching** (branch, checkout, switch). **Merge vs. rebase** (merge for shared branches, rebase for local). **Recovery tools** (stash, reset vs. revert, reflog). **PR workflow** (feature branches, clear messages, squash-merge).

### Core commands

| Command | Purpose |
|---|---|
| `git init` | Initialize a new repository |
| `git clone <url>` | Clone a remote repository |
| `git add <file>` | Stage changes (`git add .` for all) |
| `git commit -m "msg"` | Commit staged changes |
| `git status` | Show working tree status |
| `git log --oneline` | Compact commit history |
| `git diff` | Unstaged changes (`--staged` for staged) |

### Remote operations

```bash
git remote add origin <url>
git push -u origin main        # first push, sets upstream
git push                       # subsequent pushes
git pull                       # fetch + merge
git fetch                      # download without merging
```

`git pull` = `git fetch` + `git merge`. **Reach for `git fetch`** when you want to inspect remote changes before integrating them; **reach for `git pull`** for the common "get me up to date" case.

### Branching

```bash
git branch feature/login       # create branch
git checkout feature/login     # switch to branch
git checkout -b feature/login  # create + switch (shorthand)
git switch -c feature/login    # modern alternative to checkout -b
git branch -d feature/login    # delete branch (safe — prevents deleting unmerged)
git branch -D feature/login    # force delete
```

#### Branching strategies

**Feature branches:** each feature/bugfix gets its own branch off `main`. Merged back via PR. Dominant in modern trunk-based development.

**Git Flow** (simplified):

- `main` — production-ready code.
- `develop` — integration branch.
- `feature/*` — new features branch off `develop`.
- `hotfix/*` — urgent fixes branch off `main`.

**When to reach for Git Flow** — long release cycles, heavy QA gates. **When to avoid** — teams doing CI/CD with continuous deploys; feature-branch-on-`main` is simpler.

### Merge vs. rebase

#### `git merge`

Combines branches by creating a **merge commit** that ties the two histories together. Non-destructive — original branch history is preserved.

```bash
git checkout main
git merge feature/login
```

```
A---B---C  (main)
     \       \
      D---E   M  (merge commit)
```

#### `git rebase`

Replays commits from one branch **on top of** another, creating a linear history. **Rewrites commit hashes.**

```bash
git checkout feature/login
git rebase main
```

```
A---B---C  (main)
         \
          D'---E'  (feature/login, rebased)
```

#### When to use each

| Scenario | Use |
|---|---|
| Merging a feature branch into `main` via PR | `merge` (preserves context) |
| Updating a feature branch with latest `main` | `rebase` (keeps history clean) |
| Shared/public branches | `merge` (never rebase shared branches) |
| Local-only branches | `rebase` (cleaner log) |

**Golden rule:** never rebase commits that have been pushed and shared with others. Rebasing rewrites history, and anyone with the old history will get a painful conflict when they try to pull.

### Resolving merge conflicts

When Git can't auto-merge, it marks conflicts in the file:

```
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
```

Steps:

1. Open conflicted files; choose the correct code (or combine both).
2. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
3. `git add <file>` to mark as resolved.
4. `git commit` (or `git rebase --continue` if rebasing).

### Useful commands

#### `git stash`

Temporarily shelves uncommitted changes — useful when you need to switch branches mid-change.

```bash
git stash                  # stash changes
git stash list             # see all stashes
git stash pop              # apply most recent and remove
git stash apply            # apply without removing
git stash drop             # discard most recent
```

#### `git cherry-pick`

Apply a specific commit from another branch onto the current branch.

```bash
git cherry-pick <commit-hash>
```

#### `git reset` vs `git revert`

| | `git reset` | `git revert` |
|---|---|---|
| **What it does** | Moves HEAD backward, discarding commits | Creates a new commit that undoes a previous one |
| **History** | Rewrites history (destructive) | Preserves history (safe) |
| **Use case** | Undo local, unpushed commits | Undo a commit that's already pushed |

```bash
git reset --soft HEAD~1    # undo commit, keep changes staged
git reset --mixed HEAD~1   # undo commit, keep changes unstaged (default)
git reset --hard HEAD~1    # undo commit, discard all changes

git revert <commit-hash>   # create a new "undo" commit
```

**Gotcha — `git reset --hard` loses work.** It deletes your uncommitted changes. Combine with `git reflog` to recover if you slipped.

#### `git reflog`

Shows a log of all HEAD movements — invaluable for recovering from accidental `reset --hard` or deleted branches.

```bash
git reflog
git checkout <lost-commit-hash>
```

### PR / code review workflow

1. Create a feature branch from `main`.
2. Make commits with clear, descriptive messages.
3. Push the branch and open a Pull Request.
4. Reviewers comment, request changes, or approve.
5. Address feedback with **new commits** (avoid force-pushing during review — it invalidates review state).
6. Squash-merge or merge into `main`.
7. Delete the feature branch.

#### Commit message conventions

Conventional Commits format — widely adopted, friendly to auto-generated changelogs.

```
type(scope): short description

feat(auth): add JWT token refresh
fix(api): handle 404 in user endpoint
refactor(utils): extract date formatting
docs(readme): update setup instructions
```

**Common types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`.

**See also:** [`14.2 Agile and Scrum`](./14.2%20Agile%20and%20Scrum.md) for how PR review fits into sprint work, [`15.1 Frontend Testing`](./15.1%20Frontend%20Testing.md) for CI test setup on PRs.
