# How can CSS draw a small triangle without an image? / 如何不用图片用 CSS 绘制小三角形？

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

The element has no content box, so the visible shape is created by its border geometry. Color the bottom border for an upward-pointing triangle, top for downward, left for rightward, or right for leftward.

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

**See also:** [CSS Display](https://www.w3.org/TR/css-display-3/) describes box generation; [CSS Masking](https://www.w3.org/TR/css-masking-1/#the-clip-path) defines clipping paths.
