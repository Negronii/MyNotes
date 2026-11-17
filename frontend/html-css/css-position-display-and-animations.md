# 定位如何确定元素位置与前后顺序？

以一个报表页面为例，有三个定位需求：卡片里的状态徽标要贴住卡片右上角，弹窗要位于视口中央，工具条要在滚动时贴住顶部，直到它所在的区域滚出视口。解决这些需求要分清几个概念：`position` 决定盒子是否留在流中、相对什么移动；containing block（包含块）是定位坐标的参照矩形；stacking context（堆叠上下文）决定绘制时哪些盒子作为一组整体排前后。`display` 则决定元素生成什么盒子、内部用哪种布局，回答的是另一类问题。

> [!info] 先把四个问题分开
> normal flow（普通流）中，盒子按块级或行内等布局规则排布；本例的绝对定位徽标脱离普通流，后续内容不会为它留位置。
>
> inset properties（偏移属性）包括物理方向的 `top`、`right`、`bottom`、`left`，也包括逻辑方向的 `inset-block-start`、`inset-inline-end` 等。padding edge（内边距边缘）是 padding box（内边距盒）的外缘。
>
> | 属性或概念 | 要回答的问题 | 常见结果 |
> | --- | --- | --- |
> | `display` | 生成什么盒子，内部如何排布？ | `block`、`flex`、`grid` 选择盒子的类型和布局；`none` 不生成元素及其后代的盒子 |
> | `position` | 盒子是否保留流中位置，偏移怎样解释？ | `relative` 保留原位置再视觉偏移；`absolute` 脱离普通流 |
> | 包含块 | 定位坐标相对哪个矩形计算？ | 绝对定位常用最近建立包含块的祖先 padding edge |
> | 堆叠上下文 | 哪些盒子作为一个组参与前后绘制？ | 子组先在组内排序，再由父级比较整个组 |

## position（定位方式）值分别保留什么？

| `position` | 普通流中的位置 | 偏移参照 | 常见滚动表现 |
| --- | --- | --- | --- |
| `static`（静态） | 保留 | 普通流；`top` 等偏移不生效 | 随文档移动 |
| `relative`（相对定位） | 保留原位置 | 元素原来的流位置 | 随文档移动；可为绝对定位后代建立包含块 |
| `absolute`（绝对定位） | 不占原流位置 | 最近建立绝对定位包含块的祖先；若不存在则用初始包含块 | 随该包含块移动 |
| `fixed`（固定定位） | 不占原流位置 | 最近建立固定定位包含块的祖先；通常是视口 | 参照该包含块固定；若祖先建立了固定定位包含块，就不一定贴着视口 |
| `sticky`（粘性定位） | 保留原位置 | 最近滚动容器的滚动视口，并受自身包含块约束 | 在某轴至少一个 inset 不是 `auto` 时，滚动期间才会沿该轴贴近边缘 |

`absolute` 和 `fixed` 还会把盒子的外部 `display` 类型块化（blockify），例如 `display: inline` 的元素会变成块级盒。这只改变盒子的类型，与包含块的选择和堆叠上下文的创建无关。

表中“建立包含块的祖先”需要展开说明。所有非 `static` 的 `position` 值都会为绝对定位后代建立包含块，边界通常是该祖先的 padding edge；实践中最常用的是给父级加 `position: relative`。所以找绝对定位的参照时，应沿祖先链查找最近一个建立了包含块的祖先，而不是默认用父元素。

除了 `position`，以下属性也会为绝对定位和固定定位后代建立包含块：`transform` 或 `perspective` 不为 `none`、`filter` 不为 `none`（根元素例外），以及 `contain: layout` 或 `contain: paint`。这意味着祖先上的一个 `transform` 就能让 `fixed` 后代不再相对视口定位，而是相对这个祖先。这些属性还各自会创建堆叠上下文，`contain: paint` 还会裁切后代的绘制；Grid 容器等布局也有专门的包含块规则。反过来，`position: relative` 配合默认的 `z-index: auto` 时只提供坐标参照，不会新建堆叠上下文。

## 把徽标放到卡片右上角

回到开头的第一个需求。卡片尺寸为 `320 × 180px`，没有 padding 或 border，所以它的 padding box 与内容盒同尺寸；徽标为 `32 × 24px`，距卡片上边和右边各 `8px`。

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

卡片的 `position: relative` 建立了包含块，徽标的 `top`、`right` 从卡片的 padding box 边缘算起。左坐标为 `320 − 8 − 32 = 280px`，上坐标为 `8px`，所以徽标左上角是 `(280, 8)`。它脱离普通流，标题仍按自己的流位置排版。

![卡片 padding box 与绝对定位徽标的尺寸、边距和计算坐标](resources/css-position-badge-containing-block.svg)

## 让未知尺寸的弹窗居中

第二个需求是弹窗居中。做法之一是让遮罩层用 `position: fixed; inset: 0` 铺满视口，再用 Grid（网格布局）把弹窗对齐到中央。视口为 `1120 × 700px`、弹窗为 `320 × 160px` 时，视口中心是 `(560, 350)`；弹窗左上角因此是 `(560 − 160, 350 − 80) = (400, 270)`。

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

另一种方案不用 Grid：遮罩仍是铺满视口的 `fixed` 盒，同时为弹窗建立绝对定位包含块；弹窗先把左上角定位到包含块中心，再向左上平移自身宽高的一半。此例中遮罩没有 padding 或 border，尺寸就是 `1120 × 700px` 的视口：

~~~css
.dialog-backdrop {
  position: fixed;
  inset: 0;
  display: block;
}

.dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 320px;
  height: 160px;
  transform: translate(-50%, -50%);
}
~~~

`top: 50%` 与 `left: 50%` 相对遮罩的 padding box 计算，把弹窗左上角放到 `(560, 350)`；`translate(-50%, -50%)` 的百分比则相对弹窗自身，向左、向上各移 `160px` 和 `80px`，结果同样是 `(400, 270)`。两种方案的区别在于：Grid 方案中弹窗是遮罩的普通网格项目，由对齐属性居中；这一方案中弹窗是绝对定位盒，靠遮罩的 `position: fixed` 建立的包含块和偏移、平移居中。两种方案都依赖遮罩铺满视口：如果某个祖先为 `fixed` 后代建立了包含块（见上一节），遮罩就会改为铺满那个祖先。

## sticky 为什么没有贴住？

第三个需求是工具条贴顶。`sticky` 在要粘住的轴上至少需要一个非 `auto` 的 inset，例如 `top: 0`。它相对最近滚动容器的可视区域贴边，但不能移出自身包含块（通常是父元素）的范围。假设文档顶部有一个 `300px` 高的包裹层，工具条是它的第一个子元素，高 `32px`、设 `top: 0`：窗口滚动 `100px` 后，工具条顶边贴在视口 `y=0`；滚动到 `290px` 时，包裹层底边已到 `y=10`，工具条只能停在 `y=10−32=−22px`，随后跟着包裹层滚走。若包裹层只有 `32px` 高，即和工具条一样高，就没有可供移动的空间：滚动 `100px` 后工具条已在 `y=−100px`，看起来完全没有粘住。

另一个常见原因是祖先的 `overflow`：设为 `hidden`、`auto` 或 `scroll` 的祖先会成为最近滚动容器，即使它当前没有可见滚动条，工具条也会相对它而不是视口贴边。排查时应沿祖先链确认实际的滚动容器，以及 sticky 元素在包含块内还有多少移动空间。

## z-index 为什么仍然在下面？

位置确定后，还要决定重叠时谁画在上面。常见的困惑是给弹窗设了很大的 `z-index`，它仍被别的内容盖住。先看最小结构：`.shell` 与 `.other` 是同一个 `.stage` 下的兄弟，`.dialog` 是 `.shell` 的子元素。三者覆盖同一块演示区域，可以直接观察谁在上面：

~~~html
<div class="stage">
  <div class="shell"><div class="dialog">弹窗</div></div>
  <div class="other">其他内容</div>
</div>
~~~

`z-index` 的数值只在相同堆叠上下文中比较。新建的堆叠上下文会作为一个整体放进父上下文，因此内部子项的数值不能越过祖先组，与组外元素直接比较：

~~~css
.stage { position: relative; width: 240px; height: 120px; }
.shell, .other { position: absolute; inset: 0; }
.shell  { z-index: 1; }
.shell .dialog {
  position: absolute; inset: 20px; width: auto; height: auto;
  z-index: 9999; background: #ded3f4;
}
.other { z-index: 2; background: #cfe2fa; }
~~~

`.dialog` 仍在 `.shell` 这一绘制组中；组外 `.other` 的层级高于 `.shell` 时，子项的 `9999` 不会改变这两个组的顺序。蓝色的 `.other` 此时覆盖紫色弹窗；仅把 `.shell` 改为 `z-index: 3`，紫色弹窗才出现在蓝色区域上面。应调整实际参与比较的祖先层级，或把弹窗放入能与目标组同层比较的结构。

以上比较只发生在普通文档内部。调用原生 `<dialog>` 的 `showModal()` 会把对话框放入 top layer（顶层），popover 也会进入顶层；顶层内容绘制在整个文档之上，普通文档中任何 `z-index` 都不能盖住它。

| 观察到的问题 | 先检查 |
| --- | --- |
| 兄弟节点被推开或覆盖 | 普通流位置、绝对定位包含块 |
| 高 `z-index` 元素仍被遮住 | 实际参与比较的祖先堆叠上下文及其层级 |
| 浮动没有计入父元素高度 | [BFC 与流式布局边界](./bfc-and-flow-containment.md) |

> [!info] 常见堆叠上下文创建条件
> 定位盒配合非 `auto` 的 `z-index`、`fixed` 或 `sticky`（即使 `z-index: auto`）、非 `none` 的 `transform`、`perspective` 或 `filter`、小于 `1` 的 `opacity`、`isolation: isolate`、`contain: layout` 或 `contain: paint` 都会创建堆叠上下文。Flex/Grid 子项配合非 `auto` 的 `z-index` 也会创建。`will-change` 只有在它指向的属性本来会带来对应效果时，才会提前建立包含块或堆叠上下文；不要把所有创建条件都当成同时建立包含块。

> [!info]- 来源
> - `position`、包含块、偏移、sticky 滚动视口和定位盒层叠：W3C CSS Positioned Layout Level 3，Working Draft，2025-10-07，§§2、2.1、2.2、3.4，[规范](https://www.w3.org/TR/css-position-3/)。
> - 顶层绘制顺序：W3C CSS Positioned Layout Level 4，Working Draft，2025-10-07，§§3.1、4，[规范](https://www.w3.org/TR/css-position-4/)。
> - `display:none`、blockification：W3C CSS Display Module Level 3，Candidate Recommendation Draft，2026-06-05，§§2.5、2.7，[规范](https://www.w3.org/TR/css-display-3/)。
> - Flex/Grid 子项的 `z-index` 和绝对定位边界：W3C CSS Flexible Box Layout Module Level 1，Candidate Recommendation Draft，2025-10-14，§§4.1、4.3，[规范](https://www.w3.org/TR/css-flexbox-1/)；CSS Grid Layout Module Level 1，Candidate Recommendation Draft，2025-03-26，§§6.5、9.1、9.2，[规范](https://www.w3.org/TR/css-grid-1/)。
> - `transform` 建立后代定位包含块和堆叠上下文：W3C CSS Transforms Module Level 1，Candidate Recommendation，2019-02-14，§3，[规范](https://www.w3.org/TR/css-transforms-1/)；`perspective` 非 `none` 的包含块和堆叠效果：W3C CSS Transforms Module Level 2，Working Draft，2021-11-09，§8，[规范](https://www.w3.org/TR/css-transforms-2/)；`contain: layout` 与 `contain: paint` 的包含块、堆叠及裁切：W3C CSS Containment Module Level 2，Working Draft，2022-09-17，§§3.2、3.4，[规范](https://www.w3.org/TR/css-contain-2/)。
> - `filter` 的包含块与堆叠效果：W3C Filter Effects Module Level 1，Working Draft，2018-12-18，§5，[规范](https://www.w3.org/TR/filter-effects-1/)；`will-change` 的提前效果：W3C CSS Will Change Module Level 1，Candidate Recommendation Draft，2022-05-05，§2，[规范](https://www.w3.org/TR/css-will-change-1/)；整体透明度：W3C CSS Color Module Level 4，Candidate Recommendation Draft，2026-11-03，§3.3，[规范](https://www.w3.org/TR/css-color-4/)；`isolation`：W3C Compositing and Blending Level 1，Candidate Recommendation Draft，2024-03-21，§3.4.2，[规范](https://www.w3.org/TR/compositing-1/)。
> - 原生模态对话框进入 top layer：WHATWG HTML Living Standard，更新于 2026-11-11，§4.11.4，[`showModal()` 与模态显示算法](https://html.spec.whatwg.org/multipage/interactive-elements.html#dom-dialog-showmodal)；popover 显示时同样加入 top layer：[The popover attribute](https://html.spec.whatwg.org/multipage/popover.html#the-popover-attribute)。
> - 相关布局边界另见 [BFC 与流式布局边界](./bfc-and-flow-containment.md)；隐藏状态见[隐藏与可访问性](./css-visibility-and-accessibility.md)，运动见[CSS 过渡与动画](./css-transitions-and-animations.md)，布局绘制路径见[渲染流水线与强制布局](./rendering-pipeline-and-forced-layout.md)。
