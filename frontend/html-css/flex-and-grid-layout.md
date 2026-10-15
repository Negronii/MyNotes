**Flexbox and Grid Layout / Flexbox 与 Grid 布局**

Reach for this when you need to remember the property names and what each one does. For "how should I approach this layout?" style interview answers, the patterns live in [`2.6 CSS Interview Questions`](./css-interview-questions.md).

**中文：** Flexbox 适合单轴排列，Grid 适合二维轨道；遇到内容最小尺寸造成溢出时，可显式使用 `min-width: 0` 或 `minmax(0, 1fr)`。

Rule of thumb: **Flexbox for 1D** (rows *or* columns), **Grid for 2D** (rows *and* columns). In practice they compose — a grid item can itself be a flex container.

## Flexbox

`display: flex` (or `inline-flex`) turns an element into a **flex container**; its direct children become **flex items**. Flex items are laid out along a *main axis* (controlled by `flex-direction`) and a perpendicular *cross axis*.

### Container properties

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

### Item properties

| Property | What it controls |
|---|---|
| `flex-grow` | share of *extra* space (unitless proportion) |
| `flex-shrink` | share of *deficit* space when items don't fit |
| `flex-basis` | starting size before grow/shrink (length or `auto`) |
| `flex` | shorthand: `flex: <grow> <shrink> <basis>` |
| `align-self` | override `align-items` for one item |
| `order` | change an item's visual placement order (without changing source order) |

### Common flexbox patterns

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

### Intrinsic minimum sizes

Flex items and grid tracks can keep their content-based minimum size, so a long word, URL, or wide table may force overflow instead of shrinking. For a flex item that should be allowed to shrink below its min-content width, use `min-width: 0`; in a column flex layout, the corresponding block-axis fix is often `min-height: 0`.

```css
.row { display: flex; }
.main { flex: 1; min-width: 0; }
.main img { max-width: 100%; }
```

This changes the item's minimum constraint; it does not guarantee that all of its descendants will wrap or fit, so give overflowing content its own policy.

## CSS Grid

`display: grid` (or `inline-grid`) creates a **grid container**. Grids have explicit **tracks** (rows and columns), **lines** (between tracks), **cells** (single row × column), and **areas** (named regions spanning multiple cells).

### Container properties

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

### Item properties

| Property | What it controls |
|---|---|
| `grid-column-start` / `grid-column-end` | column span |
| `grid-row-start` / `grid-row-end` | row span |
| `grid-column` / `grid-row` | shorthand (`grid-column: 1 / 3`) |
| `grid-area` | name this item, or shorthand for all four line values |
| `justify-self` / `align-self` | override cell alignment for one item |

### Common grid patterns

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

## When to reach for which

- **Flexbox** — nav bars, toolbars, button groups, anything that's a line of stuff that might wrap.
- **Grid** — page-level layouts, card grids, forms with aligned labels/inputs, anything 2D.
- **Both together** — Grid for the page structure, Flexbox inside each cell for horizontal clusters.

Keep meaningful source order in the HTML. Flex `order`, reverse directions, and grid placement change visual layout without rewriting the document's logical/speech order; don't use them to repair incorrect content order.

**See also:** [`2.1 HTML & CSS Basics`](./html-and-css-basics.md) for CSS units used with `fr`/`minmax`, [`2.6 CSS Interview Questions`](./css-interview-questions.md) for worked interview examples using these layouts.

**Specifications / 规范：** [CSS Flexible Box Layout](https://www.w3.org/TR/css-flexbox-1/) defines flex sizing and the automatic minimum size; [CSS Grid Layout](https://www.w3.org/TR/css-grid-2/) defines track sizing and grid-item minimums; [CSS Display](https://www.w3.org/TR/css-display-3/#order-property) describes visual reordering and accessibility.
