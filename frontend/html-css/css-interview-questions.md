# How do you center an element whose size is unknown? / 如何居中尺寸未知的元素？

**Short answer / 简答** — Put the alignment on a Grid or Flexbox parent when the child should take up space in normal flow. For an overlay, anchor it at the center of its containing block and move it back by half of its own width and height. / 子元素应参与正常流时，由 Grid 或 Flexbox 父容器负责对齐。浮层则先把左上角定位在包含块中心，再向回移动自身宽、高的一半。

## In normal flow / 保持正常流

Grid's `place-items: center` aligns a single grid item within its area. Flexbox's `justify-content` and `align-items` center a single flex item along the main and cross axes. Give the container enough space for the alignment to have an effect.

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

## Overlay / 浮层

For an overlay, use absolute positioning to set the starting point and a transform to account for the element's own size.

~~~css
.overlay { position: relative; }
.overlay__content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
~~~

The insets refer to the containing block. The transform percentages refer to the element's own reference box, so the element can be centered without measuring it. The overlay does not contribute to the parent's normal-flow size.

## Older layouts / 旧式布局

For a fixed-size overlay, equal insets and auto margins distribute the available space. An older negative-margin variant subtracts half the known size from each coordinate.

~~~css
.overlay__fixed {
  position: absolute;
  width: 200px;
  height: 100px;
  inset: 0;
  margin: auto;
}
~~~

Table-cell layout can vertically align its contents with `vertical-align: middle`. Use it when maintaining an existing table-style layout. When centering a layout box, distinguish parent alignment from `text-align: center`, which aligns inline content inside a box.

**Related questions / 相关问题** — [Fixed and fluid layouts / 固定与流动布局](flex-and-grid-layout.md), [positioning and stacking / 定位与堆叠](css-position-display-and-animations.md), [float containment / 包含浮动](bfc-and-flow-containment.md), [CSS triangles / CSS 三角形](box-model-and-bfc.md#A%20triangle%20from%20border%20geometry%20/%20%E7%94%A8%E8%BE%B9%E6%A1%86%E5%87%A0%E4%BD%95%E7%94%BB%E4%B8%89%E8%A7%92%E5%BD%A2), [high-DPR hairlines / 高 DPR 细线](responsive-css-units-and-layout.md#when-does-a-css-hairline-mean-one-device-pixel).

**Sources / 来源** — [CSS Box Alignment §7.3](https://www.w3.org/TR/css-align-3/#place-items-property), [CSS Positioned Layout §4.2](https://www.w3.org/TR/css-position-3/#abspos-margins), [CSS Transforms §6](https://www.w3.org/TR/css-transforms-1/#transform-box).
