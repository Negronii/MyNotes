# Which DOM geometry API answers which measurement question? / 哪个 DOM 几何 API 能回答哪种测量问题？

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

## Quick comparison

| Property | Includes | Excludes or caveat | Writable? |
|---|---|---|---|
| `offsetHeight` / `offsetWidth` | Border box; ordinarily a rendered scrollbar | Margin; ignores transforms; integer CSS px | No |
| `clientHeight` / `clientWidth` | Padding area | Border and rendered scrollbar; integer CSS px | No |
| `scrollHeight` / `scrollWidth` | Scrolling area, including overflow | Border; integer CSS px; not a guarantee the content is user-scrollable | No |
| `scrollTop` / `scrollLeft` | Current scroll offset | Values may be fractional or outside usual range in some layouts | Yes |
| `offsetTop` / `offsetLeft` | Offset from `offsetParent` padding edge to element border edge | Not necessarily relative to the direct parent | No |
| `getBoundingClientRect()` | Viewport-relative union of transformed border-box fragments | Excludes margin; a snapshot | No |

Dimensions are in CSS pixels, not device pixels. Scrollbars differ by platform: a rendered scrollbar consumes layout space on some configurations but overlays content on others. Do not derive a physical-device-pixel measurement from these values.

## Choose by the box or coordinate space

### Layout box and inner client area

`offsetHeight` and `offsetWidth` return integer layout dimensions for the border box, normally including a rendered scrollbar and excluding margin. They ignore CSS transforms.

```text
offsetHeight ≈ content height + padding + border (+ rendered scrollbar)
```

`clientHeight` and `clientWidth` return the padding area minus a rendered scrollbar; the border and margin are excluded. In standards mode, the root element's client dimensions correspond to the viewport dimensions.

```text
clientHeight ≈ content height + padding - rendered scrollbar
```

### Scrolling area and current offset

`scrollHeight` measures the scrolling area, including content outside the visible client area. It can exceed `clientHeight` when content overflows. In standards mode, the root element's `scrollHeight` is the maximum of the viewport scrolling-area height and viewport height.

```javascript
const hasOverflow = element.scrollHeight > element.clientHeight;
const y = element.scrollTop;
element.scrollTop = 0; // scroll to the top
```

`scrollTop` and `scrollLeft` are writable. Reverse-direction scrolling and elastic overscroll can produce values outside the familiar range, so avoid assuming every result is a nonnegative integer.

### Position relative to the offset parent

`offsetTop` and `offsetLeft` measure from the element's border edge to the padding edge of its `offsetParent`. The offset parent is not simply the nearest positioned ancestor: tables, containing blocks, fixed positioning, zoom, shadow-tree boundaries, and missing boxes can affect which element is returned. Some elements, including `body` in common cases, return zero.

### Viewport-relative visual rectangle

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

## Measurement without repeated layout work

For an occasional measurement, choose the API whose box and coordinate system match the task. For threshold-based visibility such as lazy loading or analytics, prefer [IntersectionObserver](../browser-apis/image-lazy-loading.md) over repeatedly polling geometry. It reports asynchronously and is not a blanket guarantee that no layout work occurs.

A write followed by a geometry read can force pending layout; alternating writes and reads in a loop can repeat that work. See [Rendering pipeline and forced layout](./rendering-pipeline-and-forced-layout.md) for the read/write batching example.

**Specifications:** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines these geometry APIs, including the [root `scrollHeight` rule](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight); [Intersection Observer](https://www.w3.org/TR/intersection-observer/) defines asynchronous intersection notifications.
