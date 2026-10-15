**CSS Interview Questions / CSS 面试题**

# How do you clear floats, and why do you need to?

**Headline (30s):** A BFC root's auto height includes its floats; `display: flow-root` is the direct modern choice. A clearfix is a legacy alternative. **中文：** 让父级建立 BFC（通常用 `flow-root`）即可包含浮动子项。

## Methods of clearing floats — pure CSS

### Pseudo-element method (legacy clearfix)

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

### Block Formatting Context — the modern way

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

## Clearing element — extra HTML

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

**See also:** [`2.2 Box Model and BFC`](./box-model-and-bfc.md) on how BFCs contain floats, [`2.3 Flex & Grid Layout`](./flex-and-grid-layout.md) for modern alternatives.

---

# How do you build a three-column layout with fixed sides and a fluid middle?

**Headline (30s):** Use Grid (`100px minmax(0, 1fr) 100px`) when the columns are a page/grid structure, or Flexbox when they form a row of items. Float/table/absolute techniques are useful to recognize in legacy code. **中文：** 新布局优先考虑 Grid 或 Flex，并确认中间列是否需要突破内容最小宽度。

The layout includes two fixed-width divs on the sides (`left` and `right`) and a dynamically adjusting center div (`center`).

## HTML structure

```html
<div class="parent">
  <div class="left">Left</div>
  <div class="center">Center</div>
  <div class="right">Right</div>
</div>
```

## CSS resets

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

## Float-based layout

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

## Table display layout

```css
.parent { display: table; }
.left, .center, .right { display: table-cell; }
```

**Pros:** Stable and predictable rendering.
**Cons:** Table layout couples sizing across cells in a column, which can be harder to tune in a responsive content layout than Flexbox or Grid. `display: table` changes visual formatting only; it does not make the `<div>` elements semantic table markup.

## Absolute positioning layout

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

## Flexbox layout

```css
.parent { display: flex; }
.left, .right { flex: 0 0 100px; }
.center { flex: 1; min-width: 0; }
```

**Pros:** Modern, responsive, minimal code.
**Cons:** Only a concern for very old-browser support.

## Grid layout

```css
.parent {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) 100px;
}
```

**Pros:** Cleanest, intention-revealing.
**Cons:** Not supported in truly ancient browsers.

**Gotcha — `calc(100% - 200px)` + `box-sizing: content-box`:** If `.parent` has padding and you're using content-box, `100%` doesn't mean what you think. Always normalize with `box-sizing: border-box`.

**See also:** [`2.3 Flex & Grid Layout`](./flex-and-grid-layout.md) for the property reference.

If the center content must wrap or scroll instead of setting a minimum width, specify that policy on the item (for example, `overflow-wrap: anywhere` for long URLs). Flex/grid intrinsic minimum sizing can otherwise keep the middle track wider than its available space.

---

# How do you build a two-column layout with one fixed and one responsive side?

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

## Strict responsive solutions (reflow with viewport)

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

## Non-strict solutions (need `calc` or manual math)

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

# How do you center an element in CSS?

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

## Centering with dynamic dimensions (element size unknown)

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

## Centering with fixed dimensions

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

# How do you draw a triangle with pure CSS?

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

# How do you render a crisp 1px line on Retina / high-DPR screens?

**Headline (30s):** A CSS pixel is not a device pixel. A `1px` border remains one CSS pixel and may cover multiple device pixels; a half-pixel technique can target one device pixel at a particular scale, but alignment and zoom affect rasterization. **中文：** 不同 DPR 下 CSS 像素映射到设备像素不同，不能保证某种写法处处是一条物理像素线。

## Using a pseudo-element + transform

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

## Handling borders with `border-radius`

When the element has `border-radius`, a scaled pseudo-element may not follow the corner shape. A fractional shadow is another option to test:

```css
.box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

Fractional `box-shadow` or border widths are not a cross-device guarantee of a crisp physical-pixel line; their rasterization depends on scale and alignment.

**Gotcha — device ratio and zoom:** A 1 CSS px stroke may cover roughly one device pixel at 1×, two at 2×, or three at 3× before accounting for page zoom and OS scaling. SVG is useful for scalable geometry, but it also rasterizes onto device pixels; it does not promise a one-device-pixel stroke.

---

# How do you prevent the 300ms tap delay on mobile?

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
