**Browser HTML and CSS / 浏览器中的 HTML 与 CSS**

Layout, paint, and compositing describe common rendering work, not fixed performance guarantees. `async`, `defer`, and module scripts have distinct scheduling rules. **中文：** 布局、绘制和合成是常见实现阶段，不是固定成本保证；脚本属性的执行时序需按类型区分。

# Reflow, Repaint, and the `<script>` Tag

Interview questions this note answers:

1. **Reflow vs. repaint vs. composite — what triggers each, and which is cheapest?**
2. **How do you minimize the cost of reflow?**
3. **What does `<script>` do in HTML, and how do `async` and `defer` change its behavior?**
4. **Where should you place `<script>` tags, and why?**

For the big-picture render pipeline these topics fit into, see [`1.1 Browser Basics`](../browser/browser-basics.md).

---

## Reflow vs. repaint vs. composite — what triggers each?

**Headline (30s):** Layout recomputes geometry; paint updates visual output; compositing combines content for presentation. A change may require one stage or several. The affected area, thread, layer, and GPU use depend on the page and engine, so the stage names are not a universal cost ranking.

**Typical invalidation paths:**

| Stage pattern | Examples | Boundary |
|---|---|---|
| Style + layout + paint + presentation | Changes affecting geometry or line wrapping, such as many width or font changes | Can affect related boxes; extent depends on layout and engine |
| Style + paint + presentation | Visual changes that do not affect geometry, such as many color changes | Layout may be reused |
| Style + compositor update | Some `transform` / `opacity` changes on an element suitable for compositing | May avoid layout and paint; layer setup and GPU use are not guaranteed |

### What triggers reflow

- Window resize.
- Adding, removing, or reordering DOM nodes.
- Changes to layout-affecting styles: `width`, `height`, `margin`, `padding`, `border`, `display`, `position`, `font-*`, `line-height`, `text-align`.
- **Reading** geometry properties (`offsetHeight`, `getBoundingClientRect`) after a write can force pending style/layout work synchronously. `scrollTop` is a scroll position, not a geometry measurement.

### What triggers repaint (without reflow)

- `color`, `background`, `background-color`, `background-image`
- `visibility` (going between `visible` and `hidden`)
- `box-shadow`, `outline`, `border-color` (but not `border-width`, which changes layout)

### Compositor-friendly properties (conditional)

- `transform` and `opacity` can be good candidates for visual animation when a trace shows layout or paint is the bottleneck.
- `filter`, `will-change`, and other properties have property- and engine-specific effects; none guarantees compositor-only work.

**Gotcha — avoid a promised “GPU path”:** `transform` can avoid layout in common cases, but may still require paint, layer setup, or other work. Compare traces on target browsers and devices.

## How do you minimize the cost of reflow?

**Headline (30s):** Reduce unnecessary DOM work, group geometry reads before writes when that fits the task, and profile forced synchronous layout. A BFC manages float and margin interactions; it is not a layout-containment guarantee. CSS containment has distinct behavior and should be applied intentionally.

**Tactics:**

- **Group writes.** A class change or a series of style writes may be batched by the browser; it does not guarantee exactly one layout.
- **Avoid interleaving writes and geometry reads.** A `DocumentFragment` can clarify subtree construction, but is not automatically faster than direct DOM operations.
- **Use containment only for a real boundary.** See [Block Formatting Context](./box-model-and-bfc.md) for float and margin behavior; do not treat it as CSS layout containment.
- **Debounce or throttle** `resize` / `scroll` handlers — see [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md).
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

## What does the `<script>` tag do?

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

## `async` vs. `defer` — which to use when?

**Headline (30s):** For classic external scripts, `defer` fetches in parallel and executes after parsing in document order; `async` fetches in parallel and executes when ready without preserving order. Module scripts are deferred by default. Choose based on dependencies and when the script must run.

| Attribute | Downloads | Executes | Blocks parser? | Preserves order? |
|---|---|---|---|---|
| Classic parser-inserted, no attribute | inline or fetched by parser | when parser reaches and can run it | yes | parser order |
| Classic external `defer` | in parallel | after parsing, before `DOMContentLoaded` | no | yes among deferred scripts |
| Classic external `async` | in parallel | when ready | no | no |
| Module script | module graph fetched | deferred by default; `async` changes scheduling | no for normal module scripts | module graph rules apply |

**Gotcha — `defer` applies to classic external scripts:** It has no effect on classic inline scripts; module scripts are deferred by default. Use `async` only when execution order is unimportant.

**Gotcha — `defer` doesn't work on inline scripts:** `defer` is ignored if the `<script>` has no `src`. Move the code into an external file or use `DOMContentLoaded`.

## Where should you place `<script>` tags?

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

**See also:** [`1.1 Browser Basics`](../browser/browser-basics.md) for the high-level pipeline, [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md) for animation and scroll optimization.

**Standards and implementation notes / 标准与实现资料：** [WHATWG HTML scripting](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element), [CSS Display](https://www.w3.org/TR/css-display-3/), [Chrome RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture), [Chrome forced-reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
