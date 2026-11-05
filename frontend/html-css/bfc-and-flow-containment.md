# How does a block formatting context contain floats and margins? / 块格式化上下文如何约束浮动和外边距？

A block formatting context (BFC) is a flow-layout boundary: floats cannot intrude into its contents, its auto height includes floats inside it, and child margins do not collapse through its boundary. It is not a stacking context, a universal containing block, or general layout containment. Use `display: flow-root` when the intended change is simply to contain floats and separate child margins. / 块格式化上下文（BFC）是流式布局的边界：外部浮动不会侵入其内容，BFC 根的自动高度会包含其中的浮动，子元素外边距也不会穿过该边界折叠。BFC 不等于堆叠上下文、通用定位包含块或整体布局隔离。若目的只是包含浮动并分隔子级 margin，使用 `display: flow-root`。

## Float containment / 包含浮动

Floats leave normal flow, so a normal-flow parent whose children are all floated may have no height from those children. A BFC root contains its floats:

~~~css
.container { background: red; }
.box { float: left; width: 100px; height: 100px; }

/* Before: .container may collapse to a stripe. */
.container { display: flow-root; } /* includes the floated child */
~~~

Use a clearfix when maintaining legacy markup or browser support requires it:

~~~css
.parent::after {
  content: "";
  display: table;
  clear: both;
}
~~~

A clearing element can also end the float interaction, but adds non-semantic markup:

~~~html
<div class="parent">
  <div class="child">Content</div>
  <div class="clear"></div>
</div>
~~~

~~~css
.clear { clear: both; }
~~~

`overflow: hidden` can establish a BFC but also clips overflow and creates a scroll container. Prefer `flow-root` when clipping and scrolling are not wanted. `overflow: clip` does not establish a BFC.

## Margin collapse / 外边距折叠

Adjacent positive vertical margins of in-flow block siblings in the same BFC collapse to the larger value: two `50px` margins create a `50px` gap. A formatting-context boundary prevents a child's margin from collapsing through the container, though the container's own margins still follow its parent context.

~~~html
<section>box one</section>
<section>box two</section>
~~~

~~~css
section { margin: 50px; }
/* Adjacent positive margins collapse to a 50px gap. */
~~~

Wrap a child in a BFC to keep its margin inside that boundary:

~~~html
<section>box one</section>
<div class="bfc"><section>box two</section></div>
~~~

~~~css
section { margin: 50px; }
.bfc { display: flow-root; }
/* The child's top margin stays inside the BFC; the outer gap is 100px. */
~~~

A parent's first child's top margin can also collapse through a parent without border, padding, inline content, clearance, or a new formatting context. A border, padding, or formatting-context boundary separates the margins.

## What establishes a BFC? / 哪些条件会建立 BFC？

- `display: flow-root` explicitly establishes a BFC without clipping or scrolling.
- A block container with `overflow: hidden`, `auto`, or `scroll` establishes a BFC; `overflow: clip` does not.
- Floats, absolutely positioned boxes, inline blocks, and table cells/captions establish independent formatting contexts for their contents.
- Flex and grid containers establish their own formatting contexts, not BFCs. Their items do not participate in block margin collapsing or the usual float intrusion rules.

A BFC has defined flow behavior, not the separate rules for stacking and positioned containing blocks. See [CSS position and stacking](./css-position-display-and-animations.md).

**Specifications:** [CSS Display: formatting contexts](https://www.w3.org/TR/css-display-3/); [CSS 2.2: block formatting contexts](https://www.w3.org/TR/CSS22/visuren.html#block-formatting); checked 2026-11-05.
