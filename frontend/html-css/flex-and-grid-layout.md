# 固定与流动内容适合哪种 CSS 布局？

报表外框常同时有固定侧栏和可伸缩主栏；筛选栏则沿一个方向排列控件；卡片列表要在窄宽度下自动换列。上一章的 `<main>` 承载筛选表单和结果表；本章用它作为主栏。选择 Flexbox 或 Grid 时先描述这些关系：Flexbox 解决一条主轴上的分配和对齐，Grid 显式建立行列轨道。默认情况下，这些布局属性只改变视觉位置，不改变 HTML 的源顺序。

![Flexbox composition example](../../archive/front-end/0-1_Learning_Notes/CSS/flex.png)

## 固定侧栏与流动结果区

设整个报表外框的内容宽度为 <code>1120px</code>，左侧导航固定为 <code>14rem = 224px</code>，中间留 <code>1rem = 16px</code>（按根字号 <code>16px</code> 计算）。Grid 主栏剩余宽度为：

> [!example] 轨道宽度演算
> <code>1120 - 224 - 16 = 880px</code>。为了演算自动最小轨道，假设主栏中有一个合成的不可断长内容，其 min-content 宽度为 <code>920px</code>。使用 <code>1fr</code> 时自动最小轨道可按这 <code>920px</code> 撑开，整行达到 <code>224 + 16 + 920 = 1160px</code>，比外框多 <code>40px</code>；改成 <code>minmax(0, 1fr)</code> 后主栏收缩到 <code>880px</code>，长内容本身仍需裁切、换行或滚动。

~~~html
<div class="report-layout">
  <nav aria-label="报表导航">...</nav>
  <main>
    <h1>月度订单</h1>
    <p class="report-url"><span class="synthetic-token">合成的 920px 不可断内容</span></p>
  </main>
</div>
~~~

~~~css
.report-layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 16px;
}
.report-url {
  display: block;
  overflow: hidden;
  white-space: nowrap;
}
.synthetic-token { display: inline-block; width: 920px; }
~~~

<code>minmax(0, 1fr)</code> 让 Grid 轨道本身可收缩，因此这里不需要再给直接 Grid 项目加 <code>min-width: 0</code>。这里第一个不可断的行内盒只会被裁切，合成内容用来展示轨道尺寸变化；真实长标题的省略号见下一节。若要把合成盒换成真实长 URL 并显示全文，应移除 <code>.synthetic-token</code> 的 <code>920px</code> 固定宽度，并从 <code>.report-url</code> 去掉 <code>white-space: nowrap</code> 和裁切，再为链接设置 <code>overflow-wrap: anywhere</code>。若结果是宽数据表，把真实 <code>table</code> 保留在带名称且可由键盘到达的局部横向滚动容器内。

同样的固定/弹性关系也可以用 Flex 表达：

~~~css
.report-layout { display: flex; gap: 1rem; }
.report-layout > nav { flex: 0 0 14rem; }
.report-layout > main { flex: 1 1 0; min-width: 0; }
~~~

选择 Grid 通常更容易说清多个列轨道；只需按主轴分配空间时，Flex 更直接。若导航只是单独一行控件，Flex 更合适；若侧栏、主栏、页头和页脚需要同时安排行与列，Grid 更容易表达二维关系。

## Flexbox 一次处理一个主轴

<code>display: flex</code> 或 <code>inline-flex</code> 让直接子元素成为 Flex 项目；<code>flex-direction</code> 决定主轴方向，交叉轴与其垂直。<code>align-content</code> 用于设置了 <code>flex-wrap: wrap</code> 的容器，并在交叉轴存在剩余空间时分配 flex line；即使最终只有一条 line，也可能移动它。<code>nowrap</code> 容器的单行项目由 <code>align-items</code> / <code>align-self</code> 对齐。

> [!example] 一条 flex line 也能被 align-content 移动
> 容器高 <code>100px</code>、单行项目高 <code>20px</code> 且 <code>align-content: end</code> 时，<code>flex-wrap: wrap</code> 的单行会移到 <code>y=80px</code>；将容器改成 <code>nowrap</code>，项目仍从 <code>y=0</code> 开始。

| 属性 | 负责什么 |
| --- | --- |
| <code>flex-direction</code>、<code>flex-wrap</code> | 主轴方向、是否换行 |
| <code>justify-content</code> | 主轴上的分布与对齐 |
| <code>align-items</code>、<code>align-self</code> | 交叉轴上的项目对齐 |
| <code>align-content</code> | 开启换行时 flex line 的交叉轴分布；单条 line 也可能移动 |
| <code>gap</code> | 项目之间的间距 |
| <code>flex-grow</code>、<code>flex-shrink</code>、<code>flex-basis</code> | 可增长因子、可收缩因子、起始尺寸 |
| <code>order</code> | 仅改变视觉顺序，不改变文档与键盘顺序 |

为精确表示从零基准分配剩余空间，示例显式写 <code>flex: 1 1 0</code>。规范把单数值简写 <code>flex: 1</code> 定义为 <code>1 1 0</code>；常见浏览器的计算样式可能序列化为 <code>0%</code>，在主轴尺寸不确定时，百分比基准可能按内容解析。<code>flex: auto</code> 等于 <code>1 1 auto</code>，以明确的主轴 <code>width</code>/<code>height</code> 为基准，若其值为 <code>auto</code> 则以内容为基准；<code>flex: none</code> 等于 <code>0 0 auto</code>。项目的自动最小尺寸还可能影响最终大小，需结合内容溢出规则判断。

## 用 Flex 排列一行报表导航，并收缩长标题

一排导航、操作按钮和当前报表名只有一条主轴，适合 Flex。若长标题需要让按钮留在原位，允许标题项目收缩，并明确单行裁切规则；内容仍可从真实标题或链接访问。

~~~html
<nav class="report-toolbar" aria-label="报表导航">
  <a href="/reports">全部报表</a>
  <a href="/reports/monthly">月度报表</a>
  <span class="current-report">2026 年 10 月跨地区订单处理与复核情况汇总</span>
  <button type="button">导出</button>
</nav>
~~~

~~~css
.report-toolbar { display: flex; align-items: center; gap: 16px; }
.current-report {
  flex: 1 1 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
~~~

两个链接约占 <code>64px</code> 各，导出按钮约 <code>43px</code>，三处 gap 共 <code>48px</code>。在 <code>360px</code> 工具栏里标题可用约 <code>360 - (64 + 64 + 43) - 48 = 141px</code>；自然宽度约 <code>322px</code> 的标题因此显示省略号。换到 <code>1120px</code> 时标题盒约 <code>901px</code>，文本完整显示。具体文字宽度会随字体变化。因为 <code>overflow: hidden</code> 在直接 Flex 项上，自动最小主尺寸已经为零，这里不需要再加 <code>min-width: 0</code>。若标题本身是导航目标，应使用真实链接并保留完整可访问名称，而不是仅呈现截断后的伪文字。

## Grid 同时定义行与列

<code>display: grid</code> 或 <code>inline-grid</code> 建立显式或隐式行列轨道。固定宽度适合不变的导航，<code>fr</code> 将可用剩余空间按因子分配；<code>minmax(min, max)</code> 给轨道范围。内容关键时，<code>min-content</code>、<code>max-content</code>、<code>auto</code> 和 <code>fit-content()</code> 可参与轨道尺寸计算。

~~~css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}
~~~

每列至少尽量宽 <code>15rem</code>，容器窄于此值时最小项由 <code>min(100%, 15rem)</code> 缩到容器宽度；<code>auto-fit</code> 按可用空间重复轨道，并会折叠没有内容的轨道。沿用上面的 <code>880px</code> 主栏，根字号 <code>16px</code> 时每卡片的设计下限是 <code>15rem = 240px</code>：三列需 <code>3×240 + 2×16 = 752px</code>，四列需 <code>4×240 + 3×16 = 1008px</code>，因此有至少三张卡片时排三列，各约 <code>(880 - 2×16) ÷ 3 = 282.7px</code>。若只有两张卡片，空轨道折叠，两列各约 <code>(880 - 16) ÷ 2 = 432px</code>；容器缩到 <code>220px</code> 时单列下限缩到 <code>100%</code>，宽度为 <code>220px</code>。固定下限应来自卡片内容要求，再决定文字换行、裁切还是局部滚动。

## 居中未知尺寸的内容

如果内容应留在正常流中，用父容器负责二维或单轴对齐。容器必须有多余空间，否则居中没有可分配的空白：

~~~css
.center-grid {
  display: grid;
  place-items: center;
}

.center-flex {
  display: flex;
  justify-content: center;
  align-items: center;
}
~~~

<code>place-items: center</code> 将 Grid 项目在格内水平和垂直对齐；Flex 版分别沿主轴和交叉轴对齐。需要覆盖整个区域时，让容器本身拿到预期高度，例如由布局轨道或父级分配，而不是给子项写固定尺寸。

居中浮层会离开普通流，需要先确定它的包含块，再用定位和 transform 让未知尺寸自身回移；规则见[CSS 定位与堆叠](./css-position-display-and-animations.md)。本节讨论正常流居中，浮层的位置由定位机制决定。

## 看懂旧布局，不把它当新布局首选

- **Float** 让文字环绕浮动盒，需处理包含浮动与 margin 交互，见[BFC 如何约束浮动和外边距](./bfc-and-flow-containment.md)。
- **表格布局**可用于维护旧项目；<code>display: table-cell</code> 不会创建 HTML 表格的标题、行列等语义。
- **Inline-block** 项目会保留源码空白形成的间隙，可能需要处理基线对齐。
- **绝对定位**能把按钮锚定到卡片角落，但脱离普通流，不会参与父级尺寸计算。
- **Bootstrap Grid** 是框架约定，不等同于 CSS Grid；Bootstrap 3.4.1 和 4.6 的官方文档都标记版本已结束支持，只作为维护旧项目的版本参考。新项目先确认实际采用的版本，按其官方文档选择类名和断点。

宽订单表保留 HTML 表格结构；若它比结果区宽，把表格放入有名称且可由键盘到达的局部横向滚动区域，不要拆掉行列标题关系。

> [!info]- Bootstrap 3.4.1 的旧网格示例
> 归档示例使用 Bootstrap 3.4.1 的十二列系统：<code>.container</code> / <code>.container-fluid</code>、<code>.row</code>、<code>.col-xs-*</code> / <code>.col-sm-*</code> / <code>.col-md-*</code> / <code>.col-lg-*</code>。其中断点是 <code>&lt;768px</code>、<code>≥768px</code>、<code>≥992px</code>、<code>≥1200px</code>。归档附图来自 Bootstrap 4 的 <code>.col-</code>、<code>.col-xl-*</code> 版本，不能用它推断 Bootstrap 3 的类名和断点。Bootstrap 3 插件 JavaScript 需要先加载 jQuery，纯 CSS 网格不需要；新项目不要把这套旧类名当原生 Grid。
>
> ![Bootstrap 4 网格断点原图](../../archive/front-end/0-1_Learning_Notes/CSS/grid.png)
>
> 来源：Bootstrap 3.4 CSS 文档，[Grid system](https://getbootstrap.com/docs/3.4/css/#grid) 与 [JavaScript 插件依赖](https://getbootstrap.com/docs/3.4/javascript/)，版本 3.4.1；归档图示为 Bootstrap 4.6 旧文档截取，[Bootstrap 4 Grid](https://getbootstrap.com/docs/4.6/layout/grid/)。两版文档均标记结束支持，检查于 2026-11-06。

在未使用显式阅读顺序控制时，HTML 源码顺序决定默认阅读和键盘操作顺序。Flex <code>order</code>、<code>row-reverse</code> 和 Grid 指定区域只改变视觉位置；不要用它们修补错误的源顺序。

> [!info]- 来源
> - Flex line、项目自动最小尺寸、<code>flex</code> 简写和 <code>align-content</code>：W3C CSS Flexible Box Layout Level 1，§4.5、§6、§7.1、§8.4，Candidate Recommendation Draft（2025-10-14）：[CSS Flexbox Level 1](https://www.w3.org/TR/css-flexbox-1/)，检查于 2026-11-06。
> - Grid 轨道与自动最小轨道尺寸：W3C CSS Grid Layout Level 2，§6.6、§12，Candidate Recommendation Draft（2025-03-26）：[CSS Grid Level 2](https://www.w3.org/TR/css-grid-2/#min-size-auto)，检查于 2026-11-06。
> - Flex 项目自动最小尺寸与 overflow 值的关系：W3C CSS Overflow Level 3，§3.1，Working Draft（2025-10-07）：[CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/#overflow-properties)，检查于 2026-11-06。
> - Grid/Flex 视觉顺序与格式化模型：W3C CSS Display Module Level 3，§2（Candidate Recommendation Draft，2026-06-05）：[CSS Display Level 3](https://www.w3.org/TR/css-display-3/)，检查于 2026-11-06。
