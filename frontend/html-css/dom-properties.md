**DOM Geometry Properties / DOM 几何属性**

These APIs expose different CSSOM measurements. Their values use CSS pixels, but their box, coordinate space, fragment handling, and transform behavior differ. A read may force pending style/layout work to finish; it does not necessarily do so when layout is already current. **中文：** 读取几何值可能同步完成尚未刷新的布局，但不意味着每次读取都会重新布局。

## Quick comparison

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

## `offsetHeight` / `offsetWidth`

Returns an integer CSS-pixel measure of the border-box fragments, ignoring CSS transforms. A rendered scrollbar is included in the familiar layout-box measurement; margin is excluded. It can be zero when the element has no associated box.

```text
offsetHeight ≈ content height + padding + border (+ rendered scrollbar)
```

## `clientHeight` / `clientWidth`

Returns an integer CSS-pixel measure of the padding edge, excluding a scrollbar rendered between the padding and border edges. Border and margin are excluded. Root-element behavior maps to the viewport in standards mode.

```text
clientHeight ≈ content height + padding - rendered scrollbar
```

## `scrollHeight` / `scrollWidth`

Returns the integer CSS-pixel height of the scrolling area, which covers content beyond the visible client area. It may differ from `clientHeight` because of overflow; it is not simply a count of text or a guarantee that overflow is user-scrollable. In standards mode, the root element returns `max(viewport scrolling-area height, viewport height)`, not the viewport's visible height.

```text
ordinary element: scrolling-area height (includes overflow beyond the client area)
root element in standards mode: max(viewport scrolling-area height, viewport height)
```

## `scrollTop` / `scrollLeft`

Current scroll offset in CSS pixels. **Writable** — set it to control scroll programmatically. Values can be fractional or outside the usual range in some layouts (for example, reverse-direction scrolling or elastic overscroll).

```javascript
const el = document.getElementById('container');
console.log(el.scrollTop);
el.scrollTop = 0;  // scroll to top
```

## `offsetTop` / `offsetLeft`

`offsetTop` / `offsetLeft` measure from the element's border edge to its `offsetParent`'s padding edge. `offsetParent` is not simply the nearest positioned ancestor: tables, containing blocks, fixed positioning, zoom, shadow-tree boundaries, and elements without boxes affect the result. If there is no `offsetParent`, offsets are relative to the initial containing block; some elements such as `body` return zero.

## `getBoundingClientRect()`

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

For threshold-based visibility tracking (e.g., lazy loading, analytics), prefer `IntersectionObserver` over repeatedly polling geometry. It reports asynchronously; it is not a guarantee that the browser performs no layout work. See [`5.3 Image Lazy Loading`](../browser-apis/image-lazy-loading.md).

## When to reach for which

- Need an **untransformed integer layout-box size**? → `offsetHeight` / `offsetWidth`.
- Need a **viewport-relative transformed rectangle**? → `getBoundingClientRect()`.
- Need **inner content area** (for sizing children)? → `clientHeight` / `clientWidth`.
- Need to know if **overflow exists**? → compare `scrollHeight > clientHeight`.
- Need **current scroll position**, or to **scroll programmatically**? → `scrollTop` / `scrollLeft`.
- Need **viewport-relative position** (for tooltips, drag, scroll effects)? → `getBoundingClientRect()`.
- Need **position within parent** (for layout math)? → `offsetTop` / `offsetLeft` (watch out: relative to `offsetParent`, not necessarily the direct parent).

**See also:** [`2.4 Browser - HTML & CSS part`](./browser-html-and-css.md) on layout thrashing when reads follow writes, [`5.3 Image Lazy Loading`](../browser-apis/image-lazy-loading.md) for `IntersectionObserver`-based visibility.

**Specifications / 规范：** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines these geometry APIs, including the [root `scrollHeight` rule](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight); [Intersection Observer](https://www.w3.org/TR/intersection-observer/) defines asynchronous intersection notifications.
