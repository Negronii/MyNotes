# 块格式化上下文如何约束浮动和外边距？

block formatting context（BFC，块格式化上下文）是流式布局的一道边界。建立 BFC 的块会包含内部浮动，外部浮动不会侵入它的内容，子元素 margin 也不会穿过边界折叠。BFC 不等于 stacking context（堆叠上下文）、定位包含块或所有方向上的布局隔离；若只需要隔开普通流中的浮动和外边距，可用 <code>display: flow-root</code>。

> [!info] BFC 的边界效果
> BFC 主要约束块流、浮动与外边距。它本身不决定绘制层级，也不会为任意后代提供绝对定位的包含块；需要层叠或定位时应分别看 stacking context 与 containing block。

## 为什么报表卡片里浮动徽标会撑不开父级？

浮动盒离开普通流；即使容器里还有普通流段落，若段落本身只有一行高、旁边的浮动徽标更高，父级自动高度仍只由段落高度决定，背景会在徽标底部之前结束。让容器建立 BFC 后，其自动高度也会包住内部浮动：

~~~html
<div class="summary">
  <span class="badge">异常</span>
  <p>共 12 条记录需要复核。</p>
</div>
~~~

~~~css
.badge { float: left; inline-size: 3rem; block-size: 3rem; }
.summary { display: flow-root; background: #f3f6fa; }
.summary p { margin: 0; line-height: 20px; }
~~~

> [!example] 前后状态
> 根字号为 <code>16px</code> 时，徽标的 <code>3rem</code> 高为 <code>48px</code>；段落 margin 为 <code>0</code>、单行高度为 <code>20px</code>。没有 <code>flow-root</code> 时，`.summary` 内容盒高 <code>20px</code>，徽标超出背景；加上后内容盒高为 <code>48px</code>，背景包住徽标。

同一格式化上下文外的浮动也不能侵入 BFC 的内容区域；建立 BFC 的整个盒子仍可能被浮动挤窄，或在空间不足时移到浮动下方。普通块级容器若没有建立 BFC，浮动影响可能延伸到下一个清除或格式化边界。

## 相邻 margin 为什么不是简单相加？

同一 BFC 中相邻、处于普通流的块级兄弟元素，它们的正向垂直 margin 会折叠为较大的值。例如一行状态卡片下 margin 为 <code>24px</code>，下一张卡片上 margin 为 <code>16px</code>，最终间隔是 <code>24px</code> 而不是 <code>40px</code>。若一正一负，结果是最大正值加最负的负值：<code>24px + (-16px) = 8px</code>；缺少一侧时按 <code>0</code> 参与计算。

~~~css
.report-card { margin-block: 24px; }
.report-card + .report-card { margin-block-start: 16px; }
/* 同一块格式化上下文中的相邻外边距合并后，间隔为 24px。 */
~~~

父级和第一个普通流块子元素的上 margin 也可能向外折叠，条件包括两者之间没有 border、padding、行内内容、clearance 或新格式化上下文。给父级加边框、内边距或建立 BFC，会把这条折叠路径分开。BFC 边界不取消容器自己的 margin 与其父级上下文的折叠规则。

## 如何创建 BFC，什么副作用值得注意？

- <code>display: flow-root</code> 明确建立 BFC，不裁切内容，也不建立滚动区域。
- 块容器设置 <code>overflow: hidden</code>、<code>auto</code> 或 <code>scroll</code> 会建立 BFC；同时可能裁切内容或成为滚动容器。若不希望这些副作用，不要只为了清浮动而选 <code>overflow: hidden</code>。
- <code>overflow: clip</code> 会裁切溢出，但不建立 BFC；与另一轴的可滚动 overflow 值组合时，计算值可能落到 <code>hidden</code>。
- 浮动、绝对定位、inline-block、table cell 等盒会为其内部内容建立独立格式化上下文。
- Flex 和 Grid 容器建立各自的格式化上下文，不是 BFC；它们的项目不按普通块流参与外边距折叠，也不受普通 float 侵入规则控制。

旧项目若必须兼容不能使用 <code>flow-root</code> 的环境，可用清除伪元素方案；新代码优先选直接表达意图的属性：

~~~css
.legacy-parent::after {
  content: "";
  display: table;
  clear: both;
}
~~~

> [!info]- 来源
> - 格式化上下文、<code>flow-root</code>、float containment、margin collapse 和 Flex/Grid 的格式化边界：W3C CSS Display Module Level 3，§2.2，Candidate Recommendation Draft（2026-06-05）：[CSS Display Level 3](https://www.w3.org/TR/css-display-3/)，检查于 2026-11-06。
> - BFC、float 和 margin 折叠的传统定义：W3C CSS 2.2，§8.3.1、§9.4.1、§9.5，First Public Working Draft（2016-04-12）：[CSS 2.2, margin collapsing](https://www.w3.org/TR/CSS22/box.html#collapsing-margins) 与 [BFC / floats](https://www.w3.org/TR/CSS22/visuren.html#block-formatting)，检查于 2026-11-06。该文档是工作草案；格式化上下文的现代模型另见上项 CSS Display Level 3。
> - <code>overflow</code> 的滚动与裁切行为：W3C CSS Overflow Module Level 3，§3：[CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/)，检查于 2026-11-06。
