# CSS 如何计算元素盒子的尺寸？

每个元素的盒子由内到外分四层：content box（内容盒，下文也称内容区）、padding box（内边距盒）、border box（边框盒）和 margin box（外边距盒）。给 `width` 或 `height` 写一个固定值时，首先要弄清这个值量的是哪一层。默认的 `box-sizing: content-box` 把声明值交给内容区；`border-box` 把它交给边框盒，内容区再从中扣掉 padding 与 border。margin 始终在 border 外，不计入这两种声明值。

本页以宽度为例逐层计算。高度遵循同样的规则，但 `min-height`、`max-height` 和所在布局可能改变浏览器最后采用的高度。

## 用报表筛选面板演算宽度

设想报表页面里有一个筛选面板，放在内容区宽 `360px` 的父级中。面板左右各有 `16px` padding、`1px solid` border 和 `12px` margin。它从父级内容区左边界 `x=0` 开始排，所以左边框落在左 margin 之后的 `x=12px`。

为了只观察固定宽度的效果，例子排除了其他会改写尺寸的因素：面板用 `inline-block`，按块盒的规则计算宽高，又像行内内容一样排在父级的一行里；父级设为不换行；不设 `min-width` 或 `max-width`，也不放进 Flex/Grid 布局。图中的虚线是父级内容区边界，斜线表示透明的 margin 区域。

~~~css
.track { width: 360px; white-space: nowrap; }
.panel {
  display: inline-block;
  width: 360px;
  margin-inline: 12px;
  padding-inline: 16px;
  border: 1px solid;
}
.panel.border-box { box-sizing: border-box; }
.panel.border-box.fit { width: 336px; }
~~~

下图的三行分别对应类组合 `panel`、`panel border-box` 和 `panel border-box fit`，每种情况各放在一个独立的 `360px` 父级中。计算时从里往外加：padding box 是内容区加两侧 padding，border box 再加两侧 border，margin box 最后加两侧 margin。

![固定宽度子项的content-box、border-box与父级边界尺寸](resources/box-model-and-bfc-width-comparison.svg)

默认 `content-box` 的 `width: 360px` 量的是内容区。加上两侧 padding 后，padding box 是 `360 + 16 × 2 = 392px`；再加两侧 border，border box 是 `394px`；最后加 `24px` margin，margin box 是 `418px`。左边框位于 `x=12px`，所以边框盒右缘在 `12 + 394 = 406px`，越出父级 `46px`；margin box 右缘在 `418px`，越出 `58px`。

改成 `box-sizing: border-box`，声明的 `360px` 包含内容、padding 和 border：

> [!example] border-box，width 360px
> 内容区 `360 - 32 - 2 = 326px`；padding box `358px`；border box `360px`。margin box 是 `360 + 24 = 384px`，所以边框盒越出父区 `12px`、最外侧 margin box 越出 `24px`。

若希望面板连同左右各 `12px` 的 margin 都完全放进 `360px` 的父级，可把 border-box 宽度设为 `336px`：内容区 `302px`，padding box `334px`，border box `336px`，margin box 恰为 `360px`。规律是：父级宽度扣掉两侧 margin，剩下的就是 border-box 宽度的上限。

| 声明值实际控制的宽度 | 内容区 | padding box | border box | margin box |
|---|---:|---:|---:|---:|
| `content-box; width:360px` | `360px` | `392px` | `394px` | `418px` |
| `border-box; width:360px` | `326px` | `358px` | `360px` | `384px` |
| `border-box; width:336px` | `302px` | `334px` | `336px` | `360px` |

表只计算 `width` 对该盒生效、浏览器采用值未被其他规则改写的情形。像普通 `span` 这样的非替换行内盒不能直接用 `width` 定宽；`min-width`、`max-width` 或 Flex/Grid 的尺寸计算也会改变最后采用的宽度。`height` 同理：只有固定值实际采用时，`box-sizing` 才决定它量到内容盒还是边框盒；最小/最大高度和布局也可能改写最终尺寸。`box-sizing` 同样决定 `flex-basis` 等其他尺寸属性的固定值量到哪一层。

若 border-box 声明宽度只有 `20px`，而两侧 padding 与 border 合计 `34px`，内容区不会变成负数：内容宽度下限为 `0px`，边框盒仍会长到 `34px`。保留两侧 `12px` margin 时，margin box 是 `58px`。

常见重置让页面元素和伪元素采用 border-box，使组件声明宽度更接近可见边框宽度：

~~~css
*, *::before, *::after {
  box-sizing: border-box;
}
~~~

`padding` 和 `margin` 的一至四值简写按上、右、下、左分配：一值设四边；两值为上下、左右；三值为上、左右、下；四值按顺时针排列。

## 边框几何可以画小三角

盒模型的边框几何还有一个常见用途。内容宽高与 padding 都为零时，边框仍占据空间：四条等宽的实线边框在中心汇合（下图为 Chromium 渲染结果），各自形成一个三角。只给左边框着色、其他三边保持透明，就露出一个朝右的三角：

![零尺寸盒子的四条边框收尖到中心，只显示左边框时形成向右三角](resources/box-model-border-triangle.svg)

~~~css
.caret-right {
  display: inline-block;
  width: 0;
  height: 0;
  padding: 0;
  border: 10px solid transparent;
  border-left-color: currentColor;
  border-radius: 0;
}
~~~

把这组样式用于空 `span` 时，`inline-block` 使宽高声明生效；四条边框仍占宽度，其中未着色的三条透明边框也会占位，边框盒为 `20 × 20px`。`padding: 0` 与 `border-radius: 0` 保证图示的尖角。若希望三角形不依赖边框、能随盒子尺寸一起缩放，可以改用 `clip-path` 裁切背景。下面换成一个朝下的三角：多边形的百分比坐标以盒子左上角为原点，y 值向下增加，三个点依次是左上、右上和底边中点。

~~~css
.caret-down {
  display: inline-block;
  width: 1rem;
  aspect-ratio: 1;
  background: currentColor;
  clip-path: polygon(0 0, 100% 0, 50% 100%);
}
~~~

装饰性箭头可以对辅助技术隐藏；若箭头表达开合状态或方向，还要通过控件文字或其他语义暴露该信息。

要看 margin 怎样在普通流中相遇，以及 float 怎样影响块的边界，请继续读[块格式化上下文如何约束浮动和外边距](./bfc-and-flow-containment.md)。居中和浮层位置分别见[Flex/Grid 对齐](./flex-and-grid-layout.md)与[定位和堆叠](./css-position-display-and-animations.md)。

CSS 声明的盒尺寸与脚本读到的几何值是两个问题。以本例这种没有被拆成多个片段的面板为例，`offsetWidth` 返回边框盒的整数宽度，包括占布局空间的滚动条，但不含 margin，也不计 transform。各 API 分别量哪一层，见[DOM 几何 API](./dom-properties.md)。

> [!info]- 来源
> - **盒子的四层边缘与间距简写。** CSS Box Model Module Level 3，§2.1、§3.2、§4.2，W3C Recommendation（2024-04-11）：[CSS Box Model Level 3](https://www.w3.org/TR/css-box-3/#boxes-edges)。其中 margin 在 border 外且背景透明，margin/padding 简写按一至四值分配边缘；访问于 2026-11-12。
> - **`box-sizing`、声明宽度与下限。** CSS Box Sizing Module Level 3，§3.3，W3C Working Draft（2026-09-04）：[CSS Sizing Level 3](https://www.w3.org/TR/css-sizing-3/#box-sizing)。`border-box` 不包含 margin，计算内容尺寸时将负数下限为零；访问于 2026-11-12。
> - **inline-block 与普通 inline 宽度。** CSS 2.2，§10.3.1、§10.3.9，W3C First Public Working Draft（2016-04-12）：[CSS 2.2 width calculation](https://www.w3.org/TR/CSS22/visudet.html#inlineblock-width)。普通非替换 inline 的 `width` 不生效；inline-block 按自身宽度规则处理。该文档是历史草案；访问于 2026-11-12。
> - **边框三角与 `clip-path`。** 本页边框三角已在 Chromium 149 实际渲染；[CSS Backgrounds Level 3 §4.4](https://www.w3.org/TR/css-backgrounds-3/#corner-transitions) 并未强制规定角部颜色切换的精确路径。透明边框属性见 CSS 2.2 §8.5：[CSS 2.2 box model](https://www.w3.org/TR/CSS22/box.html#border-properties)，W3C First Public Working Draft（2016-04-12）；形状裁切见 CSS Masking Module Level 1 §5.1：[CSS Masking](https://www.w3.org/TR/css-masking-1/#the-clip-path)，W3C Candidate Recommendation Draft（2021-08-05）。访问于 2026-11-12。
> - **`offsetWidth`。** CSSOM View Module，§7：[CSSOM View](https://www.w3.org/TR/cssom-view-1/#dom-htmlelement-offsetwidth)，W3C Working Draft（2025-09-16）。访问于 2026-11-12。
