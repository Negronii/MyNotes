# 固定与流动内容适合哪种 CSS 布局？

本章以一个报表页面为例，它有三处布局需求：外框由固定宽度的侧栏和可伸缩的主栏 `<main>` 组成；操作工具栏沿一个方向排列链接和按钮；卡片列表要在宽度变窄时自动减少列数。选布局之前，先说清项目之间怎样分配空间。Flexbox (弹性盒布局) 适合沿一个主轴分配项目；Grid (网格布局) 适合同时组织行和列。两者默认只改变盒子在屏幕上的位置，不会改变 DOM 中节点的源顺序。

## 固定侧栏与流动结果区

先给出设计数值：报表外框的内容宽度固定为 1120px，左侧导航固定为 14rem（根字号 16px 时即 224px），两栏之间留 16px。如果主栏内容没有宽度下限，主栏得到剩余的宽度：

> [!example] 报表主栏的轨道宽度
> `1120 - 224 - 16 = 880px`。但主栏若含 `min-content`（最小内容尺寸）为 920px 的不可断内容，`1fr` 的自动最小轨道会取 920px；两轨与间隔合计 `224 + 16 + 920 = 1160px`，超出设定为 1120px 的外框 40px。改成 `minmax(0, 1fr)` 后，主栏轨道仍是 880px；本例中的 920px 内容盒被裁掉 40px，真实内容则要自行换行、裁切或滚动。

下面用一个人为设定为 920px 宽、不能断行的行内块，模拟主栏里的长链接地址，单独观察轨道下限的影响。真实内容怎样完整显示，见例子之后。

~~~html
<div class="report-layout">
  <nav aria-label="报表分类导航">...</nav>
  <main>
    <h1>月度订单</h1>
    <p class="report-url">
      <span class="synthetic-token">合成的 920px 不可断内容</span>
    </p>
  </main>
</div>
~~~

~~~css
.report-layout {
  display: grid;
  inline-size: 1120px;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 16px;
}
.report-url {
  display: block;
  overflow: hidden;
  white-space: nowrap;
}
.synthetic-token { display: inline-block; inline-size: 920px; }
~~~

为什么 `1fr` 会被撑开？单独写的 `1fr` 等价于 `minmax(auto, 1fr)`，其中 `auto` 是轨道的最小值。`auto` 并不总等于 min-content，但在本例中，主栏这个 grid item (网格项目) 的自动最小尺寸取它的内容下限，所以 920px 的内容把轨道撑开了。`minmax(0, 1fr)` 明确把轨道下限设为零，轨道因此能收到剩余的 880px；至于长内容是换行还是滚动，它不负责。轨道下限不再是 `auto` 后，网格项目的自动最小尺寸也随之为零，所以不需要再给 `<main>` 加 `min-inline-size: 0`。

例中的 920px 行内块被裁切，只是为了看清轨道宽度。若换成真实链接地址并要显示全文，应移除固定宽度和 `white-space: nowrap` / 裁切规则，再为长词设置 `overflow-wrap: anywhere`。若结果是宽数据表，应保留真实 `<table>` 的行列和标题关系，把表放进局部横向滚动容器；该滚动区域应有名称，并确保目标浏览器里键盘用户能到达和滚动它。

下面的 Flex 规则替换上例的 `.report-layout` 布局声明；沿用 1120px 外框、16px 间距和根字号 16px，导航仍为 224px，主栏仍为 880px：

~~~css
.report-layout { display: flex; inline-size: 1120px; gap: 16px; }
.report-layout > nav { flex: 0 0 14rem; }
.report-layout > main { flex: 1 1 0; min-inline-size: 0; }
~~~

这里必须写 `min-inline-size: 0`。flex item (弹性项目) 在主轴上的自动最小尺寸默认不小于其内容的最小宽度，长链接或大表格会因此拒绝收缩。`min-inline-size: 0` 允许主栏沿行方向缩小，内容再自行换行、裁切或局部滚动。两种写法得到相同的宽度，但适用场景不同：多个项目需要按共同的列对齐时，Grid 更容易表达；只需沿一条主轴排一排控件时，Flex 更直接。Flex 虽然可以换行，但每条 flex line (弹性行) 独立分配空间，不同行的项目不会像 Grid 那样对齐成共同的列。

## Flexbox 一次处理一个主轴

上面的 Flex 写法用到了 `flex` 简写和自动最小尺寸，下面系统说明 Flexbox 怎样分配空间。`display: flex` 或 `inline-flex` 创建 flex container (弹性容器)，它的直接子元素成为 flex item；直接写在容器里的非空白文本会被包进匿名项目，绝对定位的子元素则不参与空间分配。`flex-direction` 决定 main axis (主轴)，cross axis (交叉轴) 与之垂直。

在一条 flex line 上，尺寸分三步确定：

1. 求每个项目的 flex base size (基础尺寸)，再把它限制在最小 / 最大尺寸之间，得到 hypothetical main size (假设主尺寸)。
2. 把各项的假设主尺寸加上外边距和间距求和，与容器的主轴内尺寸比较：总和较小就增长，否则就收缩。因为第 1 步已经应用了 min/max，这些约束在选择增长还是收缩之前就参与了判断。
3. 从基础尺寸出发分配差额。增长时按 `flex-grow` 的比例分配 positive free space (正剩余空间)；收缩时按 `flex-shrink` 与基础尺寸的乘积，即 scaled flex-shrink factor (缩放后的收缩权重)，分摊 negative free space (负剩余空间)。某个项目分配后违反了自己的最小或最大尺寸时，把它固定在边界上（称为冻结），再把剩下的差额分给其余项目，直到所有项目都确定。

以上说的是增长因子合计不小于 1 的常见情形；若一行的 `flex-grow` 合计小于 1，项目只会分走部分正剩余空间。

| 属性 | 负责什么 |
| --- | --- |
| `flex-direction`、`flex-wrap` | 主轴方向、是否产生多条 flex line (弹性行) |
| `justify-content` | 项目尺寸与自动外边距确定后，沿主轴分配剩余空间 |
| `align-items`、`align-self` | 项目在各自 Flex line 的交叉轴上对齐 |
| `align-content` | 在交叉轴上对齐 Flex line；只对允许换行的容器生效，单条 line 也可能移动 |
| `gap` | 项目之间的间距；先从容器可用空间中扣除，再计算可分配空间 |
| `flex-grow`、`flex-shrink`、`flex-basis` | 正剩余空间增长比例、负空间收缩权重、基础尺寸 |
| `order` | 改变 Flex 项目的视觉顺序，不改 DOM 顺序 |

![默认横向书写模式、direction:ltr、flex-direction:row 下 Flexbox 的两轴方向和项目排列；图中标出 main-start、main-end、cross-start、cross-end](resources/flex-axes.svg)

本图以默认的 horizontal writing mode (横向书写模式)、`direction: ltr` (left-to-right, 从左向右) 和 `flex-direction: row` 为例：主轴从左向右，交叉轴从上向下。改用 `column` 后，主轴沿列方向，交叉轴随之交换。两轴起点和终点的物理方向随书写模式与 `direction` 变化；`row-reverse` / `column-reverse` 会反转主轴方向。main size (主尺寸) 和 cross size (交叉尺寸) 分别指项目沿主轴和交叉轴的尺寸。

> [!example] 允许换行的容器即使只有一条 line，也能移动它
> 设容器高 100px、唯一项目高 20px，并使用 `flex-wrap: wrap`、`align-content: flex-end` 和 `align-items: flex-start`。在默认行方向下，这条唯一的弹性行被推到底部，项目从 `y = 80px` 开始。若把容器改成 `flex-wrap: nowrap`，它成为单行 Flex 容器，`align-content` 不生效，项目仍从 `y = 0px` 开始。

> [!example] 负剩余空间遇到最小尺寸时重新分配
> 容器内宽 256px，项目间距 16px，所以两项共有 240px 可用空间。两项的基础尺寸分别为 200px 和 100px，`flex-shrink` 都为 1，合计比可用空间多 60px。按 `1 × 200 : 1 × 100 = 2 : 1` 的收缩权重分摊，第一项缩 40px、第二项缩 20px，暂定尺寸为 160px 和 80px。但第一项的最小行内尺寸是 180px，暂定值低于下限，于是它被冻结在 180px；第二项拿到剩下的 `240 − 180 = 60px`。最终尺寸 `180 + 60 + 16 = 256px` 正好填满容器。本机 Chromium 探针也测得 180px、60px。

~~~html
<div class="shrink-demo">
  <div class="first"></div>
  <div class="second"></div>
</div>
~~~

~~~css
.shrink-demo { display: flex; inline-size: 256px; gap: 16px; }
.first { flex: 0 1 200px; min-inline-size: 180px; }
.second { flex: 0 1 100px; min-inline-size: 0; }
~~~

前面的主栏和下文的工具栏都写成 `flex: 1 1 0`，表示 `flex-grow` 与 `flex-shrink` 都为 1、`flex-basis` 明确为零，即从零出发按比例分配全部空间。CSS Flexbox 规范中，单值简写 `flex: 1` 也表示零基准；但本机 Chromium `157.0.8103.51` 的 `getComputedStyle()` 把它的基础尺寸报告为 `0%`。在主轴尺寸不确定的列容器中，百分比基准会按内容解析，因而可能与明确的零长度表现不同。下文的探针把 `flex: 1` 与 `flex: 1 1 0` 分开测量；若布局依赖确定的零基准且主轴尺寸可能不确定，应写三值形式。

在本机无头 Chrome 中可以复现这个差异：自动高度的列容器有两个项目，文字内容高分别为 40px 和 20px，项目设 `min-height: 0; overflow: hidden`。单值 `flex: 1` 的计算基准为 `0%`，两项按内容得到 40px、20px，容器高 60px；显式写 `flex: 1 1 0px` 时，容器与两项高度都为 0px。该尺寸结果是本机 Chromium 157 的探针观察；它限定了上面的写法建议，不意味着所有主轴或浏览器都会出现相同差异。

`flex: auto` 等价于 `1 1 auto`：先参考明确的主轴尺寸，尺寸为 `auto` 时再依据内容。`flex: none` 等价于 `0 0 auto`，按基础尺寸排布且不增长或收缩。`flex: initial` 等价于 `0 1 auto`：有正剩余时不增长，空间不足时仍可收缩到其最小尺寸。项目的自动最小尺寸可能继续阻止收缩，因此还要看其内容和溢出规则。

## 用 Flex 排列报表工具栏并截断长标题

回到第二个需求：工具栏里的导航链接、当前报表名和导出按钮排成一行，只有一条主轴，适合 Flex。工具栏放在 `<main>` 的标题下方。为了让宽度可以手算，下面分别用 360px 和 1120px 两个工具栏宽度演算，不受前面 880px 主栏的约束；两个链接固定为 64px，按钮固定为 43px，间隔都是 16px；报表名项目从零基准增长，放不下时显示单行省略号。

~~~html
<nav class="report-toolbar" aria-label="当前报表操作">
  <a class="fixed-link" href="/reports">全部报表</a>
  <a class="fixed-link" href="/reports/monthly">月度报表</a>
  <span class="current-report">
    2026 年 10 月跨地区订单处理与复核情况汇总
  </span>
  <button type="button">导出</button>
</nav>
~~~

~~~css
.report-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  inline-size: 360px;
  font-size: 16px;
}
.report-toolbar > * { box-sizing: border-box; }
.fixed-link { flex: 0 0 64px; white-space: nowrap; }
.current-report {
  flex: 1 1 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.report-toolbar > button { flex: 0 0 43px; padding: 0; }
~~~

工具栏内容宽度为 360px 时，固定部分共占 `64 + 64 + 43 + 3 × 16 = 219px`，标题从零基准得到 `360 − 219 = 141px` 的正剩余空间。这不是 `flex-shrink` 把标题压窄；标题按 `flex-grow` 增长到 141px 后，才在盒内显示省略号。在本机 Chromium 中，这个标题在 16px 字号下的完整宽度约 316px，实际宽度随字体而变。把 `inline-size` 改为 1120px 时，标题得到 `1120 − 219 = 901px`，足以完整显示。

这里标题项目不需要 `min-inline-size: 0`，原因是它自己设了 `overflow: hidden`。`hidden` 会让盒子成为滚动容器（不显示滚动条，但脚本仍可滚动它），而 flex 项目的自动最小尺寸只对非滚动容器取内容下限，所以这个项目的自动最小尺寸为零。如果只在内层子元素上裁切，外层 flex 项目通常仍要另写 `min-inline-size: 0` 才能收缩。

裁切只隐藏视觉部分，文本仍在 DOM 中。若标题需要导航，应使用真实链接并保留完整的可访问名称；同时确保省略容器不会裁掉键盘焦点指示。不要用已截断的字符串替换完整标题。

## Grid 同时定义行与列

第三个需求是卡片列表，卡片要按共同的列对齐，适合 Grid。`display: grid` 或 `inline-grid` 让容器按行列轨道排布子项，轨道可以显式定义，也可以在放置项目时隐式生成。固定尺寸适合不变的导航，`fr` 按比例分配剩余空间，但每条轨道仍要满足自身的最小和最大尺寸。轨道宽度要由内容决定时，可用 `min-content`、`max-content`、`auto` 与 `fit-content()` 参与轨道尺寸计算：`min-content` 尽量缩到仍可在合法断点换行的最窄尺寸；`max-content` (最大内容尺寸) 则按不利用软换行机会时的内容宽度计算。最终结果还受容器空间、可换行机会与显式约束影响。

~~~css
.cards {
  display: grid;
  grid-template-columns:
    repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}
~~~

`repeat(auto-fit, ...)` 会按容器宽度放下尽可能多条列轨道，每条至少 `min(100%, 15rem)`，多余空间由 `1fr` 均分。`.cards` 的直接子项是卡片，默认的自动放置让每张卡片依次占一格：

~~~html
<section class="cards" aria-label="月度报表">
  <article><h2>订单总量</h2><p>本月订单数量与上月比较。</p></article>
  <article><h2>准时交付</h2><p>按地区查看订单交付情况。</p></article>
  <article><h2>待复核</h2><p>需要进一步检查的订单。</p></article>
</section>
~~~

根字号为 16px 时，轨道的设计下限是 `15rem = 240px`。沿用 880px 的报表主栏，3 条轨道需 `3 × 240 + 2 × 16 = 752px`，4 条需 `4 × 240 + 3 × 16 = 1008px`，放不下，所以三张及以上卡片排三列，每列约 `(880 − 2 × 16) ÷ 3 = 282.7px`；第四张会进入下一行。若只有两张卡片，`auto-fit` 折叠未放入项目的第三条重复轨道及其相邻间隔，于是每列约 `(880 − 16) ÷ 2 = 432px`。若主栏缩到 220px，`min(100%, 15rem)` 使单列轨道下限缩到 220px。轨道宽度和卡片自身的宽度约束是两件事：若卡片写了 `min-inline-size: 300px`，它仍可撑到 300px 并在 220px 轨道内溢出。本机 Chromium 探针测得 880px 容器中，两张卡片各 432px、三张各约 282.66px，220px 容器中轨道宽 220px。若要在空位保留未使用的轨道槽位，可选择 `auto-fill`；`auto-fit` 则折叠空轨道，让现有项目伸展。

## 居中未知尺寸的内容

Flex 和 Grid 的对齐属性也是居中未知尺寸内容最简单的办法。如果内容应留在正常流中，就让父容器负责对齐，可以同时居中两个方向，也可以只居中一个方向。前提是容器比内容大，否则没有多余空间可分配：

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

`place-items: center` 将 Grid 项目在格内水平与垂直对齐；Flex 版分别沿主轴和交叉轴对齐。需要覆盖整个区域时，应让容器从父级布局或轨道取得预期高度，而不是给内容写固定尺寸。

浮层（如弹窗）要脱离普通流，居中方式不同：先确定它的包含块，再用定位偏移和 `transform` 让它按自身尺寸回移，规则见[定位如何确定元素位置与前后顺序？](./css-position-display-and-animations.md)。

## 看懂旧布局，不把它当新布局首选

- **float (浮动)。** 用于让文字绕排浮动盒；父级怎样包住浮动、外边距怎样折叠，见[块格式化上下文 (BFC) 如何约束浮动和外边距？](./bfc-and-flow-containment.md)。
- **表格布局。** 可维护旧项目；`display: table-cell` 不会创建 HTML 表格的标题、行列等语义。
- **inline-block (行内块)。** 源码空白会形成项目间隙，基线也可能影响对齐。
- **绝对定位。** 可把按钮锚定到卡片角落，但它脱离普通流，不参与父级尺寸计算。
- **Bootstrap Grid。** 是框架约定，不等同于 CSS Grid。新项目先确认实际采用的 Bootstrap 版本，再按对应官方文档选类名与断点。

> [!info]- Bootstrap 3.4.1 与 Bootstrap 4.6 的旧网格示例
> 归档 Bootstrap 3.4.1 示例使用十二列系统：`.container` / `.container-fluid`、`.row`、`.col-xs-*` / `.col-sm-*` / `.col-md-*` / `.col-lg-*`。断点为 `<768px`、`≥768px`、`≥992px`、`≥1200px`。归档截图显示的是 Bootstrap 4.6：它有 `.col-` 与 `.col-xl-`，并包含 `576px` 断点，不能用它推断 Bootstrap 3 的类名和断点。可[打开归档 Bootstrap 4 网格截图](../../archive/front-end/0-1_Learning_Notes/CSS/grid.png) 查看。
>
> Bootstrap 3 插件 JavaScript 需要先加载 jQuery；CSS 网格本身不需要该依赖。Bootstrap 官方文档目前将 Bootstrap 3 与 Bootstrap 4 标为结束支持：3.4.1 的维护于 2019-07-24 结束，4.6.2 于 2023-01-01 结束；它们适合作为旧项目维护资料，不是新项目的默认选择。
>
> 来源：[Bootstrap 3.4 Grid system](https://getbootstrap.com/docs/3.4/css/#grid) 与 [Bootstrap 3.4 JavaScript 插件依赖](https://getbootstrap.com/docs/3.4/javascript/)；[Bootstrap 4.6 Grid system](https://getbootstrap.com/docs/4.6/layout/grid/) 与 [Bootstrap 官方结束支持说明](https://getbootstrap.com/docs/4.6/end-of-life/)，核对日期：2026-11-12。

最后回到开头的提醒：Flex 和 Grid 只改变视觉位置。Flex 的 `order`、`row-reverse` 和 Grid 的指定区域都不会改动源码顺序；没有使用 CSS 显式阅读顺序控制（`reading-flow` 等属性）时，屏幕阅读器和 Tab 键仍按源码顺序前进。所以不要用它们修补错误的源码顺序，视觉顺序与源码顺序差异过大时，键盘用户会感到焦点乱跳。

> [!info]- 来源与核验
> - **Flex 项目的轴、尺寸与自动最小尺寸。** W3C [CSS Flexible Box Layout Module Level 1](https://www.w3.org/TR/css-flexbox-1/)，Candidate Recommendation Draft，2025-10-14，§§4.5、6、7.1、8.3–8.4、9；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-flexbox/)，2026-05-08。用于单数值 `flex` 简写、基础尺寸、正 / 负剩余空间分配与约束处理。
> - **Grid 轨道和自动重复。** W3C [CSS Grid Layout Module Level 2](https://www.w3.org/TR/css-grid-2/)，Candidate Recommendation Draft，2025-03-26，§§6.6、7.2.3、12；`1fr` 的自动最小范围、`auto-fit` 折叠空轨道与轨道尺寸算法。
> - **Flex/Grid 项目自动最小尺寸与裁切值。** W3C [CSS Overflow Module Level 3](https://www.w3.org/TR/css-overflow-3/)，Working Draft，2025-10-07，§3.1；`hidden`、`clip` 与 `scroll` 的区别，核对日期：2026-11-12。
> - **绘制顺序与格式化模型。** W3C [CSS Display Module Level 3](https://www.w3.org/TR/css-display-3/)，Candidate Recommendation Draft，2026-06-05，§3.1；`order` 改变视觉顺序，不改默认的语音呈现顺序与顺序键盘导航顺序。显式阅读顺序控制 `reading-flow` / `reading-order`：W3C [CSS Display Module Level 4](https://www.w3.org/TR/css-display-4/) 中的 reading order 一节，Working Draft；浏览器支持情况需按目标环境确认。
> - **键盘焦点顺序。** W3C [Understanding Success Criterion 2.4.3: Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)；焦点移动顺序需保留内容含义与操作关系。
> - **本地布局探针。** 本轮 headless Chrome `157.0.8103.51`：`1fr` 案例主轨道为 920px、两轨与间距合计 1160px，超出 1120px 外框 40px；`minmax(0, 1fr)` 主轨道为 880px。`auto-fit` 在 880px 容器中排出 3 × 282.66px 或 2 × 432px；220px 容器中的轨道为 220px，另测 `min-inline-size: 300px` 卡片本身为 300px 并溢出轨道。负剩余空间的冻结例最终为 180px、60px。独立 Flex 探针中，`flex: 1` 的计算 `flex-basis` 为 `0%`，`flex: 1 1 0` 为 `0px`；自动高度列容器、两项内容高 40px / 20px 时，前者尺寸为 40px / 20px、容器高 60px，后者项目和容器都为 0px。工具栏代码本身使用 `flex: 1 1 0`，不是此处的单值简写探针。这些数字是本机对固定输入的核验，不是跨浏览器性能或兼容性保证。
