# How does CSS calculate an element's box size? / CSS 如何计算元素盒子的尺寸？

A CSS box has content, padding, border, and margin layers. With the default `box-sizing: content-box`, declared width and height size the content area; padding and border are added outside it. With `box-sizing: border-box`, the declared dimensions include content, padding, and border. Margin remains outside both. / CSS 盒模型包含内容、内边距、边框和外边距。默认的 `box-sizing: content-box` 把声明的宽高用于内容区，内边距和边框会在外侧增加尺寸；`box-sizing: border-box` 则将内容、内边距和边框都包含在声明尺寸内。两种模式下 margin 都在盒子外面。

~~~text
┌────────────── margin ──────────────┐
│ ┌──────────── border ────────────┐ │
│ │ ┌────────── padding ────────┐ │ │
│ │ │          content           │ │ │
│ │ └───────────────────────────┘ │ │
│ └───────────────────────────────┘ │
└───────────────────────────────────┘
~~~

For `width: 100px; padding: 10px; border: 5px solid`, the content-box width is `100 + 20 + 10 = 130px`. Under border-box the outer border edge remains 100px and the content area shrinks to 70px. Height follows the same rule.

| Declared `width`/`height` size | `content-box` | `border-box` |
|---|---|---|
| Content area | Yes | No |
| Padding and border | Added outside the declared size | Included in the declared size |
| Margin | Always outside | Always outside |

A common reset makes sizing arithmetic predictable, including generated pseudo-elements:

~~~css
*, *::before, *::after {
  box-sizing: border-box;
}
~~~

The `padding` and `margin` shorthands accept one to four values in top/right/bottom/left order: one value sets all sides; two set vertical then horizontal; three set top, horizontal, bottom; four set each side clockwise.

~~~css
.box-a { border: 1px solid black; }
.box-b { border: 3px dashed red; }

.box {
  width: 100px;
  height: 100px;
  padding: 10px;
  border: 5px solid black;
  box-sizing: border-box; /* outer border box stays 100 × 100 */
}
~~~

For the flow rules that determine how floats and margins interact around boxes, see [How does a block formatting context contain floats and margins?](./bfc-and-flow-containment.md). For CSS layout coordinates and DOM geometry, see [DOM geometry APIs](./dom-properties.md).

**Specification:** [CSS 2.2 box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions), checked 2026-11-05.
