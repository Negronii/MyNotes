# 何时使用过渡，何时使用关键帧动画？

报表筛选按钮改变颜色、卡片从正面翻到背面，都是两个状态间的视觉过渡；先越过目标再回落的过冲效果需要指定中间状态，重复移动图片条带还需要控制循环。transition（过渡）在样式变化后插值；keyframe animation（关键帧动画）通过 `@keyframes` 定义时间点上的样式。

> [!info] 先按状态模型选机制
> 一个起点到一个终点，且由 hover、焦点或 class 状态变化触发，通常用 transition。需要多个中间步骤、自动开始、循环、反向或暂停时，用 keyframes。两种方式都要评估对阅读和操作的影响。

## 状态变化用 transition

~~~css
.filter-button {
  background-color: #17324d;
  transition: background-color 180ms ease-out;
}

.filter-button:hover,
.filter-button:focus-visible {
  background-color: #24547d;
}
~~~

| 属性 | 作用 |
| --- | --- |
| `transition-property` | 指定参与过渡的属性，如 `opacity`、`transform` |
| `transition-duration` | 插值持续时间 |
| `transition-timing-function` | 速度曲线，如 `ease-out`、`cubic-bezier(...)` |
| `transition-delay` | 开始前等待的时间 |

多个属性使用不同时间时，按逗号位置一一对应：

~~~css
.result-card {
  transition-property: transform, opacity;
  transition-duration: 300ms, 200ms;
  transition-timing-function: ease-out, linear;
  transition-delay: 0ms, 100ms;
}
~~~

把过渡声明放在基础状态上，进入和离开状态都会应用。只把声明写在 `:hover` 规则中，离开 hover 时基础状态没有过渡声明，返回过程可能直接跳变。

## 多个时间点用 @keyframes

~~~css
@keyframes panel-enter {
  0%   { transform: translateY(8px); opacity: 0; }
  55%  { transform: translateY(-2px); opacity: 1; }
  100% { transform: translateY(0); opacity: 1; }
}

.report-panel {
  animation: panel-enter 240ms ease-out both;
}
~~~

55% 时面板先越过终点 `2px`，最后再回到原位；这个中间关键帧表现轻微过冲。

| 属性 | 作用 |
| --- | --- |
| `animation-name` | 选择 `@keyframes` 规则 |
| `animation-duration` | 一轮持续时间 |
| `animation-timing-function` | 一轮或关键帧段的速度曲线 |
| `animation-delay` | 第一轮开始前等待时间 |
| `animation-iteration-count` | 轮数或 `infinite` |
| `animation-direction` | 正向、反向或交替播放 |
| `animation-fill-mode` | 活跃播放前后是否应用关键帧样式 |
| `animation-play-state` | `running` 或 `paused` |

## 用两面翻牌理解 3D transform

transform（变换）可平移、旋转或缩放绘制盒子。原归档例子只有正面与背面两块，因此是两面翻牌示意，不是六面立方体。下面用类名控制角度，实际交互卡片还需单独提供按钮状态、焦点行为和内容语义；纯 CSS 的背面隐藏只影响绘制，不能代替内容可访问性处理。

~~~html
<div class="flip-demo" aria-hidden="true">
  <div class="flip-demo__inner">
    <div class="flip-demo__face flip-demo__front">正面</div>
    <div class="flip-demo__face flip-demo__back">背面</div>
  </div>
</div>
~~~

~~~css
.flip-demo {
  width: 200px;
  height: 120px;
  perspective: 800px;
}

.flip-demo__inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 600ms ease;
}

.flip-demo.is-flipped .flip-demo__inner { transform: rotateY(180deg); }

.flip-demo__face {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  backface-visibility: hidden;
  color: white;
}

.flip-demo__front { background: #24547d; }
.flip-demo__back { background: #8c3d16; transform: rotateY(180deg); }
~~~

未加 `.is-flipped` 时，蓝色“正面”朝向读者；加入该类后，内层转过 `180deg`，正面背向读者，橙色“背面”转到前方。示例整体 `aria-hidden="true"`，文字只用于演示，不承载页面内容。

`translate`（平移）移动，`rotate`（旋转）改变朝向，`scale`（缩放）改变绘制尺寸。`transform-origin`（变换原点）默认在盒子中心；旋转或缩放时改变它，会改变视觉效果所绕的参照点。多种变换函数组合时顺序会影响结果，交换平移和旋转的顺序可能得到不同位置。`transform` 不重新安排周围普通流项目，但可能扩展可滚动溢出区域，并为后代建立 containing block（包含块）与 stacking context（堆叠上下文）。

## 无限滚动图片条带怎样无缝循环？

以下例子沿用归档中的“双组三图”结构，用作纯装饰的 CSS 理想尺寸演算。视窗宽 `320px`，原图组三张、复制组三张，共六项；整条轨道宽度是视窗的 `600%`，移动 `50%` 对应其中一组三张的理论宽度。

~~~html
<div class="strip-window" aria-hidden="true">
  <div class="strip-track">
    <img src="a.jpg" alt="">
    <img src="b.jpg" alt="">
    <img src="c.jpg" alt="">
    <img src="a.jpg" alt="">
    <img src="b.jpg" alt="">
    <img src="c.jpg" alt="">
  </div>
</div>
~~~

~~~css
.strip-window { width: 320px; overflow: hidden; }

.strip-track {
  display: flex;
  width: 600%;
  animation: strip-loop 18s linear infinite;
}

.strip-track img {
  flex: 0 0 calc(100% / 6);
  width: 100%;
  height: auto;
}

@keyframes strip-loop {
  to { transform: translateX(-50%); }
}
~~~

> [!example] 循环距离
> 轨道宽 `6 × 320 = 1920px`；两个等宽图组各占 `960px`。`translateX(-50%)` 移动 `1920 × 0.5 = 960px = 3 × 320px`，在理想尺寸下，下一组占据原组的位置。实际 Flex 项可能因子像素尺寸取整出现极小接缝；要验证特定图片、浏览器和显示设备的结果，不把这组算式当作像素级无缝保证。素材宽高比不同不影响横向组宽；若卡片宽度或组数变化，需同步调整轨道和每项比例。

这个循环没有控制按钮、键盘浏览、暂停机制或轮播语义，所以不能充当内容轮播。正式轮播应提供前后切换和停止/开始控制；自动播放在焦点进入轮播后停止，直到用户通过控制器显式重启；指针悬停时也停止。还要处理 prefers-reduced-motion（减少动态效果偏好）。若动画只是装饰，也要确保它不承载唯一信息。

## 动画性能与减少动态效果

样式变化可能触发样式计算、布局、绘制、栅格化和合成。`transform` 与 `opacity` 在某些场景可以避免重复布局，但不能保证只走合成器或 GPU 路径。应观察具体页面的渲染轨迹；[渲染流水线与强制布局](./rendering-pipeline-and-forced-layout.md)说明写入和几何读取如何影响布局工作。

will-change（即将变化提示）是提前告知可能变化的提示，不是强制创建 GPU 图层的开关；部分提示还会创建堆叠上下文或包含块并占用内存。只在测量确认有收益时对小范围、短时间使用，结束后移除。`translateZ(0)` 也不是通用加速开关。

~~~css
@media (prefers-reduced-motion: reduce) {
  .report-panel,
  .result-card {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
    transition-duration: 0.01ms;
  }

  .flip-demo__inner { transition: none; }
  .strip-track { animation: none; }
}
~~~

减少动态效果时仍保留必要的状态反馈，并避免内容因动画停止而不可见。

> [!info]- 来源
> - 属性过渡与离散属性状态：W3C CSS Transitions Level 2，Working Draft（2026-02-04），[CSS Transitions](https://www.w3.org/TR/css-transitions-2/)，检查于 2026-11-06。
> - 关键帧动画：W3C CSS Animations Level 1，Working Draft（2023-03-02），[CSS Animations](https://www.w3.org/TR/css-animations-1/)，检查于 2026-11-06。
> - 变换、绘制溢出、包含块和堆叠上下文：W3C CSS Transforms Level 1，Candidate Recommendation（2019-02-14），[CSS Transforms](https://www.w3.org/TR/css-transforms-1/)，检查于 2026-11-06。
> - 三维变换、透视、保留 3D 与两面翻牌：W3C CSS Transforms Level 2，Working Draft（2021-11-09），[backface-visibility](https://www.w3.org/TR/css-transforms-2/#backface-visibility)，检查于 2026-11-06。
> - `will-change` 提示：W3C CSS Will Change Level 1，Candidate Recommendation Draft（2022-05-05），[CSS Will Change](https://www.w3.org/TR/css-will-change-1/)，检查于 2026-11-06。
> - 减少动态效果偏好：W3C Media Queries Level 5，Working Draft（2026-02-19），[prefers-reduced-motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion)，检查于 2026-11-06。
> - 轮播控制和自动播放行为：W3C WAI [ARIA APG Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)，检查于 2026-11-06。
