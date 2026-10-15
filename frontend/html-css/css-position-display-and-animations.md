**CSS Position, Display, and Animations / CSS 定位、显示与动画**

Positioning, stacking contexts, visibility, and compositing answer different questions. A containing block controls coordinates; a stacking context controls paint ordering; a BFC controls flow interactions. **中文：** 定位坐标、堆叠顺序、可见性和格式化上下文不可混为一谈。

# How do the CSS `position` values differ?

**Headline (30s):** `static` and `relative` stay in flow; `absolute` and `fixed` are out of flow; `sticky` stays in flow and is offset relative to a scrollport while scrolling. Absolute/fixed containing blocks are established by specific ancestor properties, not only by `position`. **中文：** sticky 保持在文档流中；absolute/fixed 的定位包含块也可能由 transform 或 containment 等属性建立。

| Value | In flow? | Positioned relative to | Scrolls with page? |
|---|---|---|---|
| `static` (default) | yes | — (offsets ignored) | yes |
| `relative` | yes (original space reserved) | its original position | yes |
| `absolute` | no | nearest ancestor establishing its absolute-position containing block | follows that containing block |
| `fixed` | no | nearest fixed-position containing block, usually the viewport | fixed to that containing block |
| `sticky` | yes | nearest scrollport in the relevant axis, constrained by its containing block | yes; its visual offset changes while sticking |

## `static` (default)

Element flows normally in document order. `top`, `right`, `bottom`, `left`, and `z-index` have no effect.

```css
.box { position: static; }
```

## `relative`

Element stays in normal flow; space is reserved as if it were not positioned. Offset properties shift it *visually* without affecting sibling layout. Also establishes a positioning context for absolutely positioned descendants.

```css
.box { position: relative; top: 10px; left: 20px; }
```

## `absolute`

Element removed from normal flow — no space reserved. Its containing block is established by the nearest qualifying ancestor; a non-static `position` value is common, and properties such as `transform` or `contain` can also establish one. Without such an ancestor, the initial containing block is used.

```css
.parent { position: relative; } /* creates positioning context */
.child  { position: absolute; top: 0; right: 0; }
```

## `fixed`

Removed from normal flow; positioned relative to a fixed-position containing block, usually the viewport. It stays fixed as the document scrolls only when that viewport is the containing block.

```css
.navbar { position: fixed; top: 0; left: 0; right: 0; }
```

**Gotcha — fixed descendants:** Properties including `transform`, `perspective`, `filter`, and some `contain` / `will-change` values can establish a fixed-position containing block. A fixed descendant may then move with that ancestor instead of the viewport.

## `sticky`

Element remains in normal flow. In an axis where a non-`auto` inset is specified, it is offset relative to the nearest scrollport as scrolling would move it past the sticky view rectangle, subject to its containing block.

```css
.header { position: sticky; top: 0; }
```

**Gotcha — overflow ancestors:** An ancestor with `overflow: hidden`, `auto`, or `scroll` can become the nearest scroll container even when it does not visibly scroll. Sticky positioning then uses that ancestor's scrollport; it may not respond to the page's scroll as expected. Inspect the scroll-container chain and the sticky element's containing block.

## Stacking context and `z-index`

`z-index` affects stacking order within stacking contexts. Positioned elements with a non-`auto` `z-index` create a stacking context; fixed and sticky boxes create one even with `z-index: auto`. Other triggers include `opacity` below `1`, transforms, filters, `isolation: isolate`, and some containment or `will-change` values.

```css
.layer-a { position: relative; z-index: 1; }
.layer-b { position: relative; z-index: 2; } /* above layer-a */
```

**Gotcha — "my `z-index: 9999` isn't on top":** A stacking context is an isolation boundary. A descendant's `z-index` can never escape to compete with elements outside its context — no matter how high the value. If `.modal` sits inside a parent with `transform: translateZ(0)`, any `z-index` on the modal only competes with *siblings inside that parent*. To fix, raise the `z-index` (or create a stacking context) on an ancestor shared with the element you're trying to overlap.

---

# When should you use `display: none` vs `visibility: hidden` vs `opacity: 0`?

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

### Decision guide

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

# How do CSS transitions and animations work, and when should you prefer one over the other?

**Headline (30s):** A **transition** interpolates between two states triggered by a property change (e.g., hover). An **animation** runs independently from defined keyframes and can loop, pause, and control fill state. Use transitions for simple state-to-state interactions (hover, focus, click). Use animations for complex, multi-step, or looping motion.

## Transitions

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

## `@keyframes` and `animation`

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

## `transform` properties

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

## Compositing and `will-change`

Animating `transform` and `opacity` can let an engine update presentation without recalculating layout, but neither property guarantees compositor-only or GPU work. `will-change` is a hint that may have memory and stacking effects; it does not guarantee layer promotion. See [`2.4 Browser - HTML & CSS part`](./browser-html-and-css.md) for typical invalidation paths.

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* may affect compositing; it does not guarantee GPU acceleration */
}
```

**Gotcha — don't `will-change` everything:** Browsers may allocate extra resources or alter stacking behavior for hinted properties. Apply it only after measurement, keep the hinted region small, and remove it when no longer needed.

**Gotcha — `transform: translateZ(0)` is not a GPU switch:** It changes transform behavior and may affect stacking/containing blocks; it does not guarantee a faster path. Use neither it nor `will-change` as a substitute for profiling.

**See also:** [`2.2 Box Model and BFC`](./box-model-and-bfc.md) for formatting-context behavior, [`2.4 Browser - HTML & CSS part`](./browser-html-and-css.md) for rendering invalidation, [`11.2 Rendering and Computation Optimization`](../performance/rendering-and-computation-optimization.md) for measurement guidance.

**Specifications / 规范：** [CSS Positioned Layout](https://www.w3.org/TR/css-position-3/), [CSS Display](https://www.w3.org/TR/css-display-3/), [CSS Color opacity](https://www.w3.org/TR/css-color-4/#transparency), [CSS Transforms](https://www.w3.org/TR/css-transforms-1/), [CSS Transitions](https://www.w3.org/TR/css-transitions-2/), [W3C WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/).
