# Which CSS layout tool fits fixed and fluid content? / 固定与流动内容适合哪种 CSS 布局？

Use Flexbox for a one-dimensional row or column of items and Grid when rows and columns form a two-dimensional structure. For a fixed side with a fluid region, set the fixed track explicitly and make the flexible minimum shrinkable: for example, Grid's `minmax(0, 1fr)` or a Flex item with `min-width: 0`. Choose from the relationship among content, then define what should happen to overflow. / 一行或一列的项目优先考虑 Flexbox；需要同时安排行与列的二维结构时考虑 Grid。固定侧栏加流动区域时，明确固定轨道，并让弹性部分的最小值可以收缩，例如 Grid 的 `minmax(0, 1fr)` 或 Flex 子项的 `min-width: 0`。先根据内容关系选择布局，再规定溢出时如何处理。

| Layout problem | Good starting point | Why |
|---|---|---|
| Toolbar or row of items | Flexbox | One main axis, with optional wrapping |
| Page with fixed sidebars and a fluid center | Grid | The three column tracks are explicit |
| One fixed column and one fluid column | Grid or Flexbox | Both express the fixed/flexible relationship |
| Content of unknown size centered in a region | Grid or Flexbox | Alignment stays in normal flow |
| Legacy browser/layout constraints | Float, table, absolute, or inline-block patterns | Recognize their tradeoffs and existing formatting model |

## Fixed and fluid columns / 固定与流动列

For a fixed-width sidebar and flexible content, Grid makes the track relationship explicit. The HTML source order remains meaningful for reading and keyboard navigation:

~~~html
<div class="two-column">
  <aside>Navigation</aside>
  <main>Article content</main>
</div>

<div class="three-column">
  <aside>Left rail</aside>
  <main>Main content</main>
  <aside>Right rail</aside>
</div>
~~~

~~~css
.two-column {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 16px;
}
.two-column > main { min-width: 0; }
~~~

For a row of items, Flex expresses the same decision:

~~~css
.two-column { display: flex; gap: 16px; }
.two-column > aside { flex: 0 0 200px; }
.two-column > main { flex: 1; min-width: 0; }
~~~

For fixed side columns around a flexible center:

~~~css
.three-column {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) 100px;
  gap: 10px;
}
~~~

The middle region's min-content width can otherwise prevent it from shrinking around a long URL, word, or wide table. `min-width: 0` lets the item shrink; it does not decide whether descendants wrap, clip, or scroll. Give content a policy such as `overflow-wrap: anywhere` for long URLs or a scroll container for wide tables. In a column Flex layout the analogous block-axis constraint is often `min-height: 0`.

## Why can Flexbox and Grid still overflow? / Flexbox 与 Grid 为什么仍可能溢出？

Flex items and Grid tracks have intrinsic minimum sizing behavior. Long words, fixed-size descendants, and wide tables can contribute a content-based minimum larger than the available space. Lower the relevant minimum only when the design permits it; do not treat `min-width: 0` or `minmax(0, 1fr)` as automatic wrapping.

~~~css
.row { display: flex; }
.row > main { flex: 1; min-width: 0; }
.row > main img { max-width: 100%; }

.content-first-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 16rem;
}
.content-first-grid > main { min-width: 0; }
~~~

## Flexbox essentials / Flexbox 要点

`display: flex` or `inline-flex` makes direct children flex items arranged on a main axis and a perpendicular cross axis.

| Container property | Controls |
|---|---|
| `flex-direction` | Main-axis direction: row, row-reverse, column, column-reverse |
| `flex-wrap` | Whether items wrap |
| `justify-content` | Alignment/distribution along the main axis |
| `align-items` | Alignment within each line on the cross axis |
| `align-content` | Distribution of multiple flex lines when cross-axis space is available |
| `gap` | Space between items |

In a wrapping flex container, `align-content` aligns flex lines when extra cross-axis space exists and can affect a single line. In a `nowrap` container there is only one line, so `align-content` has no effect.

| Item property | Controls |
|---|---|
| `flex-grow` / `flex-shrink` / `flex-basis` | Growth, shrinking, and starting size |
| `flex` | Shorthand for grow, shrink, and basis |
| `align-self` | Cross-axis alignment of one item |
| `order` | Visual order without changing document order |

The shorthand and common values differ: `flex: 1` uses a zero basis and shares free space; `flex: auto` starts from the item's size; `flex: none` is inflexible. Do not assume every item can shrink below its minimum content size.

~~~css
.toolbar { display: flex; justify-content: space-between; gap: 1rem; }
.centered-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

## Grid essentials / Grid 要点

`display: grid` or `inline-grid` creates explicit or implicit row and column tracks.

| Container property | Controls |
|---|---|
| `grid-template-columns` / `grid-template-rows` | Track sizes |
| `grid-template-areas` | Named regions |
| `gap` | Space between tracks |
| `justify-items` / `align-items` / `place-items` | Item alignment inside cells |
| `justify-content` / `align-content` / `place-content` | Grid alignment inside the container |

Tracks can be fixed, flexible (`fr`), or content-sized (`min-content`, `max-content`, `auto`). `minmax(min, max)` sets lower and upper track sizing functions; `repeat(auto-fit, minmax(200px, 1fr))` creates responsive tracks. An `fr` track with an automatic minimum can still be held open by min-content contributions; use `minmax(0, 1fr)` when the design needs it to shrink below them, then choose a wrapping or overflow policy.

~~~css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr));
  gap: 16px;
}
~~~

The inner `min(100%, 250px)` lets the minimum fit a container narrower than 250px. Named areas can describe page structure:

~~~css
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
~~~

Grid item properties include `grid-column`/`grid-row` placement and `justify-self`/`align-self` alignment.

## Centering / 居中

For unknown item dimensions, put alignment on the parent. Grid's `place-items: center` and Flexbox's `justify-content` plus `align-items` keep the child in normal flow:

~~~html
<div class="center-grid"><div>Centered content</div></div>
~~~

~~~css
.center-grid { display: grid; place-items: center; }
~~~

~~~css
.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

An overlay can use absolute positioning with a transform when it should not take normal-flow space:

~~~css
.overlay { position: relative; }
.overlay__content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
~~~

The transform percentages use the element's own size, so this works when dimensions are unknown. For definite width and height, setting all four insets to zero and auto margins also centers the out-of-flow box; the box does not size its parent. Negative-margin technique requires known dimensions. Table-cell vertical alignment is a legacy alternative.

## Legacy layout patterns / 旧式布局模式

Use these to understand existing layouts; choose Flex/Grid for ordinary new row, column, and page-structure work.

| Technique | Example pattern | Tradeoff |
|---|---|---|
| Float | `float: left` and `float: right` around a center with margins | Needs float containment/clearing and width math; see [BFC containment](./bfc-and-flow-containment.md) |
| Table display | `display: table` / `table-cell` | Cell sizing couples content; visual display does not create semantic table markup |
| Absolute positioning | Fixed edges with a fluid center | Children leave normal flow; the parent does not grow around them |
| Inline-block | Two inline-block columns | Whitespace between elements can create a gap; legacy workarounds set parent font-size to 0 |

~~~css
/* Legacy 3-column float pattern; width math assumes normalized box sizing. */
.left { float: left; width: 100px; }
.right { float: right; width: 100px; }
.center { margin: 0 100px; width: calc(100% - 200px); }

/* Table-style 3-column layout. */
.table-layout { display: table; width: 100%; }
.table-layout > * { display: table-cell; }

/* Inline-block two-column layout; restore child text size. */
.inline-layout { font-size: 0; }
.inline-layout > * { display: inline-block; vertical-align: top; font-size: 1rem; }
~~~

Absolute positioning can also form fixed side columns around a center with matching margins and width math. Use it only when out-of-flow placement is intended.

Keep meaningful document order in the HTML. Flex `order`, reverse directions, and Grid placement change visual order without changing source or assistive-technology order; do not use them to repair incorrect content order.

**See also:** [Responsive CSS units and pixels](./responsive-css-units-and-layout.md) for container queries and viewport sizing; [Box sizing](./box-model-and-bfc.md) for dimensions; [CSS position and stacking](./css-position-display-and-animations.md) for out-of-flow placement.

**Specifications:** [CSS Flexible Box Layout](https://www.w3.org/TR/css-flexbox-1/) defines flex sizing and automatic minimum sizes; [CSS Grid Layout](https://www.w3.org/TR/css-grid-2/) defines track sizing and grid-item minimums; [CSS Display](https://www.w3.org/TR/css-display-3/#order-property) describes formatting contexts and visual reordering; checked 2026-11-05.
