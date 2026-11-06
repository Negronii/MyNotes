# 定位如何确定元素位置与前后顺序？

报表卡片里的状态徽标要贴住卡片右上角，弹窗要位于视口中央，固定工具条则要在滚动时留在可视区域。定位先回答盒子相对哪个参照物放置、是否保留原来的流位置；stacking context（堆叠上下文）再决定一组盒子如何绘制到前后层。

> [!info] 本页所说的几个边界
> normal flow（普通流）是文档中块级、行内和流式布局的排版过程。containing block（包含块）为定位尺寸和偏移提供参照。inset properties（偏移属性）包括逻辑方向的 `inset-block-start`、`inset-inline-end`，也包括物理方向的 `top`、`right`、`bottom`、`left`。

## position（定位方式）值分别保留什么？

| `position` | 普通流中的位置 | 偏移参照 | 常见滚动表现 |
| --- | --- | --- | --- |
| `static`（静态） | 保留 | 普通流；`top` 等偏移不生效 | 随文档移动 |
| `relative`（相对定位） | 保留原位置 | 元素自身原来的流位置 | 随文档移动；可为绝对定位后代建立包含块 |
| `absolute`（绝对定位） | 不占原流位置 | 最近建立绝对定位包含块的祖先；若不存在则用初始包含块 | 随该包含块移动 |
| `fixed`（固定定位） | 不占原流位置 | 最近建立固定定位包含块的祖先；通常是视口 | 相对该包含块固定 |
| `sticky`（粘性定位） | 保留原位置 | 最近滚动容器的滚动视口，并受自身包含块约束 | 到达指定 inset 后贴住滚动视口边缘 |

`absolute` 的常见参照是最近的非 `static` 定位祖先的 padding box（内边距盒）。transform（变换）、perspective（透视）、filter（滤镜）和 will-change（即将变化提示）的部分值也可能建立包含块。`contain: layout` 与 `contain: paint` 都会为绝对和固定定位后代建立包含块；它们同时建立堆叠上下文，`paint` 还会裁切内容。不要只看属性名称，应检查建立了哪种包含块以及随之产生的裁切和层叠效果。

## 把徽标放到卡片右上角

以下卡片没有 padding 或 border，因此默认 `content-box` 与其 padding box 都是 `320 × 180px`；徽标为 `32 × 24px`，距上、右边缘各 `8px`：

~~~css
.report-card {
  position: relative;
  width: 320px;
  height: 180px;
}

.report-card__badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 24px;
}
~~~

> [!example] 用包含块演算坐标
> 卡片 padding box 左上角为 `(0, 0)`。徽标左坐标为 `320 − 8 − 32 = 280px`，上坐标为 `8px`，所以其左上角是 `(280, 8)`。徽标脱离普通流，卡片中的标题仍按自己的流位置排版。

~~~text
卡片 padding box：320 × 180
┌────────────────────────────────────────┐
│                                  ┌─────┐│  top = 8
│                                  │徽标 ││  right = 8
│                                  └─────┘│
└────────────────────────────────────────┘
                          x = 280
~~~

## 让未知尺寸的弹窗居中

遮罩层可覆盖视口并用 Grid（网格布局）对齐弹窗。视口为 `1120 × 700px`，弹窗为 `320 × 160px` 时，视口中心是 `(560, 350)`；弹窗左上角因此是 `(560 − 160, 350 − 80) = (400, 270)`。

~~~css
.dialog-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
}

.dialog {
  width: 320px;
  height: 160px;
}
~~~

> [!example] 同一中心点用偏移表示
> 若弹窗必须以 `position: absolute` 定位，可以令左上角在包含块的 `50% 50%`，再用 `translate(-50%, -50%)` 把自身宽高的一半移回去。使用 `fixed` 时，应检查祖先有没有建立固定定位包含块的属性；这时参照物可能不再是视口。

## sticky 为什么没有贴住？

`sticky` 需要在要粘住的轴上设置非 `auto` inset，例如 `top: 0`。它相对最近的滚动视口移动，并且不能超出其包含块。祖先的 `overflow` 可能建立滚动容器，即使那个祖先当前没有明显滚动条；因此应沿祖先链确认实际滚动容器及可用空间。

## z-index 为什么仍然在下面？

`z-index` 在当前堆叠上下文内排序。子元素不能只靠更大的数值跳出祖先堆叠上下文与外部兄弟直接比较：

~~~css
.shell  { position: relative; z-index: 1; }
.dialog { position: absolute; z-index: 9999; }
.other  { position: relative; z-index: 2; }
~~~

`.dialog` 仍属于 `.shell` 这一绘制组；`.other` 的组排在 `.shell` 上面时，里面的 `9999` 不会改变两组之间的顺序。应调整实际参与比较的祖先层级，或把弹窗放入能与目标组同层比较的结构。

| 观察到的问题 | 先检查 |
| --- | --- |
| 兄弟节点被推开或覆盖 | 普通流位置、绝对定位包含块 |
| 高 `z-index` 元素仍被遮住 | 最近共同堆叠上下文及其层级 |
| 浮动没有计入父元素高度 | [BFC 与流式布局边界](./bfc-and-flow-containment.md) |

> [!info] 常见堆叠上下文创建条件
> 定位元素配合非 `auto` 的 `z-index`、`fixed`、`sticky`、小于 `1` 的 `opacity`、transform、filter、`isolation: isolate` 及部分 containment / `will-change` 值都可能创建堆叠上下文。一个属性是否同时建立包含块要分别看规范规则。

> [!info]- 来源
> - 定位、包含块、sticky 滚动视口和堆叠：W3C CSS Positioned Layout Level 3，Working Draft（2025-10-07），[CSS Positioned Layout](https://www.w3.org/TR/css-position-3/)，检查于 2026-11-06。
> - 变换建立堆叠上下文和后代包含块：W3C CSS Transforms Level 1，Candidate Recommendation（2019-02-14），[CSS Transforms](https://www.w3.org/TR/css-transforms-1/)，检查于 2026-11-06。
> - `filter` 建立后代定位包含块和堆叠上下文：W3C Filter Effects Level 1，Working Draft（2018-12-18），[Filter Effects](https://www.w3.org/TR/filter-effects-1/)，检查于 2026-11-06。
> - `will-change` 提示与潜在布局影响：W3C CSS Will Change Level 1，Candidate Recommendation Draft（2022-05-05），[CSS Will Change](https://www.w3.org/TR/css-will-change-1/)，检查于 2026-11-06。
> - 布局与绘制包含建立定位包含块、堆叠上下文和裁切：W3C CSS Containment Level 2，Working Draft（2022-09-17），[Layout containment](https://www.w3.org/TR/css-contain-2/#layout-containment) 与 [Paint containment](https://www.w3.org/TR/css-contain-2/#paint-containment)，检查于 2026-11-06。
> - 相关布局边界另见[BFC 与流式布局边界](./bfc-and-flow-containment.md)；隐藏状态见[隐藏与可访问性](./css-visibility-and-accessibility.md)，运动见[CSS 过渡与动画](./css-transitions-and-animations.md)，布局绘制路径见[渲染流水线与强制布局](./rendering-pipeline-and-forced-layout.md)。
