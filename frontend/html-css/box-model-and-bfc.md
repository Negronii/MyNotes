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

## A triangle from border geometry / 用边框几何画三角形

A zero-size element with thick borders forms four triangular border regions. Make three borders transparent and color one: the colored region becomes a triangle pointing away from that border. This is useful for small carets and callouts; use `clip-path` when the shape must scale independently of border thickness. / 零尺寸元素的粗边框会形成四个三角形区域。将三个边框设为透明并给一个边框着色，彩色区域会形成一个朝向该彩色边框相反方向的三角形，适合小箭头和气泡尖角；若形状需要独立缩放，可考虑 `clip-path`。

```html
<div class="triangle" aria-hidden="true"></div>
```

```css
.triangle {
  width: 0;
  height: 0;
  border: 10px solid transparent;
  border-left-color: red; /* points right */
}
```

The element’s content box has zero width and height, so the visible shape is created by its border geometry. Color the bottom border for an upward-pointing triangle, top for downward, left for rightward, or right for leftward.

For a shape whose dimensions should follow its box rather than a fixed border size:

```css
.triangle {
  width: 1rem;
  aspect-ratio: 1;
  background: currentColor;
  clip-path: polygon(50% 0, 100% 100%, 0 100%);
}
```

The second example makes an upward triangle; change the polygon points to change direction. A decorative caret should be hidden from assistive technology if it adds no meaning. If it communicates state or direction, expose that information through the control's text or semantics as well.

[CSS Masking on clipping paths](https://www.w3.org/TR/css-masking-1/#the-clip-path)

For the flow rules that determine how floats and margins interact around boxes, see [How does a block formatting context contain floats and margins?](./bfc-and-flow-containment.md). For CSS layout coordinates and DOM geometry, see [DOM geometry APIs](./dom-properties.md).

**Specification:** [CSS 2.2 box model](https://www.w3.org/TR/CSS22/box.html#box-dimensions), checked 2026-11-05.
