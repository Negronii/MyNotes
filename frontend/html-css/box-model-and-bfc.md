**Box Model and BFC / 盒模型与块格式化上下文**

The box model measures each generated box; a block formatting context (BFC) controls specific float and margin interactions. A BFC is not a stacking context or a general rendering-containment boundary. **中文：** 盒模型描述盒子的尺寸；BFC 主要管理浮动和外边距交互，不等于堆叠上下文或通用布局隔离。

Interview questions this note prepares you for:

1. **What is the CSS box model?**
2. **Content-box vs border-box — which should you use, and why?**
3. **What is a Block Formatting Context (BFC), and what triggers one?**
4. **How do you fix vertical margin collapse?**
5. **How do you contain floating children so the parent doesn't collapse?**

## What is the CSS box model?

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

## Content-box vs border-box — which should you use?

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

## What is a Block Formatting Context, and what triggers one?

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

## How do you fix vertical margin collapse?

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

## How do you contain floating children so the parent doesn't collapse?

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

**See also:** [`2.6 CSS Interview Questions`](./css-interview-questions.md) for float-clearing patterns and layout interview scenarios.

**Specifications / 规范：** [CSS Display: formatting contexts](https://www.w3.org/TR/css-display-3/), [CSS 2.2: block formatting contexts](https://www.w3.org/TR/CSS22/visuren.html#block-formatting), [CSS 2.2: box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions).
