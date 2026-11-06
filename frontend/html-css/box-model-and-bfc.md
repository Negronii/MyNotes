# CSS 如何计算元素盒子的尺寸？

先确定声明尺寸量到哪里，再把 padding、border 和 margin 加进布局预算。CSS 盒子从内到外依次是 content、padding、border、margin；<code>box-sizing</code> 决定声明宽高包含哪些边缘，但 margin 总是在声明尺寸之外。

![CSS 盒模型原始示意图](../../archive/front-end/0-1_Learning_Notes/CSS/box_model.png)

## 用报表筛选面板演算宽度

假设筛选面板希望占父容器 <code>360px</code>，左右各留 <code>16px</code> 内边距，边框各 <code>1px</code>。默认 <code>content-box</code> 下，<code>width: 360px</code> 量的是内容区，所以实际外框为：

> [!example] 内容盒演算
> <code>360 + 16 × 2 + 1 × 2 = 394px</code>。父区只有 <code>360px</code> 时，面板会多出 <code>34px</code>，可能推动邻列或形成溢出。

设为 <code>box-sizing: border-box</code> 后，声明的 <code>360px</code> 包含内容、padding 和 border；内容区剩余：

> [!example] 边框盒演算
> <code>360 - 16 × 2 - 1 × 2 = 326px</code>。外框正好是 <code>360px</code>；margin 仍额外占用父区空间。

| 声明宽度 | <code>content-box</code> | <code>border-box</code> |
| --- | --- | --- |
| 内容区 | 等于声明宽度 | <code>max(0, 声明宽度 - padding - border)</code>；结果最小为 <code>0</code> |
| 内边距和边框 | 加在内容区外 | 包含在声明宽度内 |
| 外边距 | 始终在盒子外 | 始终在盒子外 |

若左右 padding 与边框合计 <code>34px</code>，但 <code>border-box</code> 声明宽度只有 <code>20px</code>，内容宽度下限为 <code>0px</code>，外框仍要长到 <code>34px</code>，不会出现负内容宽度。

常见重置把页面元素和伪元素统一按边框盒计算，让列宽加法更容易预测：

~~~css
*, *::before, *::after {
  box-sizing: border-box;
}
~~~

该属性也会影响 sizing properties（如 flex-basis）对固定尺寸的解释。<code>padding</code> 和 <code>margin</code> 的一至四值简写按上、右、下、左分配：一值设四边；两值为上下、左右；三值为上、左右、下；四值依顺时针排列。

## 边框几何可以画小三角

宽高为零的盒子仍可通过边框显示形状。给四条边都设 <code>10px solid transparent</code>，再给左边着色，会显示向右的三角；改给下边着色则指向上方。它适合固定的小箭头。若形状要随盒子尺寸独立缩放，可使用 <code>clip-path</code>：

~~~css
.caret {
  display: inline-block;
  width: 1rem;
  aspect-ratio: 1;
  background: currentColor;
  clip-path: polygon(50% 0, 100% 100%, 0 100%);
}
~~~

装饰性箭头可以对辅助技术隐藏；若箭头表达开合状态或方向，还要通过控件文字或其他语义暴露该信息。

要看 float 和块之间的流式边界，请继续读[块格式化上下文如何约束浮动和外边距](./bfc-and-flow-containment.md)。居中和浮层位置则分别见[Flex/Grid 对齐](./flex-and-grid-layout.md)与[定位和堆叠](./css-position-display-and-animations.md)。

CSS 声明的盒尺寸和脚本读取到的几何值是不同问题：例如 <code>offsetWidth</code> 包含边框、通常还包含占位滚动条，但不含 margin，且忽略变换；各 API 的测量边界见 [DOM 几何 API](./dom-properties.md)。

> [!info]- 来源
> - <code>box-sizing</code> 以及 content-box / border-box 边缘：W3C CSS Box Sizing Module Level 3，§3.3，Working Draft（2026-09-04）：[CSS Sizing Level 3](https://www.w3.org/TR/css-sizing-3/#box-sizing)，检查于 2026-11-06。该模块为工作草案；这里的常见盒边缘规则也与 CSS 2.1/2.2 兼容。
> - <code>clip-path</code>：W3C CSS Masking Level 1，§6：[CSS Masking](https://www.w3.org/TR/css-masking-1/#the-clip-path)，检查于 2026-11-06。
> - <code>offsetWidth</code> 的边框盒测量：W3C CSSOM View，§7：[CSSOM View](https://www.w3.org/TR/cssom-view-1/#dom-htmlelement-offsetwidth)，检查于 2026-11-06。
