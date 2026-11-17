# 哪些 CSS 单位与响应式布局规则适合当前空间？

响应式布局要回答两个问题。第一，Cascading Style Sheets (CSS, 层叠样式表) 的长度单位“相对于什么”计算；第二，样式规则应该在“谁的尺寸或状态”变化时切换。本章用一个报表页面举例，第二个问题有三种常见答案：media query (媒体查询) 响应整个视口或用户偏好；container query (容器查询) 让同一张卡片放在主栏或窄侧栏时，按自身分到的宽度调整；Grid (网格布局) 的自动重复轨道则按网格容器的可用宽度和每列最小宽度自动决定列数，不需要先测量卡片文字有多宽。

## 常见尺寸单位各自参照什么？

| 单位 | 参照 | 常见用途 | 需要记住的边界 |
| --- | --- | --- | --- |
| `px` | CSS reference pixel (CSS 参考像素) | 边框、精确间距 | 不保证最终绘制成一个物理设备像素 |
| `%` | 由该属性定义的参照盒或参照值 | 流动宽度、偏移 | 每个属性的百分比基准不同，不能只看符号 |
| `em` | 通常取使用该值的元素计算字号；用于 `font-size` 时取继承字号 | 随文字缩放的局部间距 | 嵌套字号可能逐层相乘 |
| `rem` | 根元素的计算字号 | 跨组件的一致文字相对尺寸 | 媒体查询和容器查询对相对单位的求值规则不同 |
| `vw` / `vh` | 默认 large viewport (大视口) 的宽、高；每单位为对应尺寸的 1% | 视口区域 | 视口不是普通内容盒；工具栏展开时，`100vh` 可能大于当前可见高度 |
| `svh` / `lvh` / `dvh` | 每单位分别为 small viewport height (小视口高度)、large viewport height (大视口高度)、dynamic viewport height (动态视口高度) 的 1% | 移动端全高界面 | 需选择是否随浏览器工具栏伸缩 |
| `vmin` / `vmax` | 默认 large viewport 的短边 / 长边；每单位为对应边长的 1% | 随方向变化的尺寸 | 不表示内容容器宽度 |

例如，若初始字号与根字号均为 16px，`1.5rem = 24px`；将根元素计算字号改为 20px 后，普通声明中的 `5rem = 100px`。`em` 用在非 `font-size` 声明时参照当前元素字号；用在 `font-size` 本身时参照父元素继承来的字号。`rem` 让一组声明共用根字号；如果 `rem` 用在根元素自己的 `font-size` 上，为避免循环引用，它参照初始字号。

不过，同样写 `em` 或 `rem`，放在普通声明、`@media` 条件和 `@container` 条件里，参照的字号并不相同：

| 使用位置 | `em` 的参照 | `rem` 的参照 |
| --- | --- | --- |
| 普通样式声明 | 使用该值的元素计算字号；`font-size` 取父元素字号 | 根元素计算字号 |
| `@media` | 初始 `font-size` 值 | 初始 `font-size` 值 |
| `@container` 尺寸条件 | 被选中查询容器的计算字号 | 根元素计算字号 |

由表可知，媒体查询中的 `rem` 断点不会随页面自己写的 `html { font-size: ... }` 改变，只跟随初始字号（受用户浏览器字号设置影响）。另外，页面用 `px` 把根字号写死，会覆盖用户在浏览器里设置的基础字号偏好。表中的 CSS `1px` 是参考像素：设备像素比、页面缩放与栅格对齐共同决定它最终覆盖多少个设备像素，详见文末“细边框”一节。

移动端浏览器的地址栏、工具栏会展开和收起，可见视口高度随之变化。`100svh` 按工具栏展开时的小视口计算，`100lvh` 按工具栏收起时的大视口计算，`100dvh` 跟随当前的动态视口。想让关键内容在工具栏展开时也完整可见，可以先用小视口单位；想让元素跟随可见区域伸缩，就用动态单位，但要接受伸缩时布局跟着变化。

`100vw` 和 `100%` 也常被混用，但前者按视口宽度计算，后者按父级提供的宽度计算。页面内部滚动容器的滚动条只占用该容器自己的宽度，不缩小视口，所以两者会出现差异。在本机 headless Chrome (无头 Chrome) `157.0.8103.51` 的 700px 视口中，内部滚动 `<section>` 设置为 `width: 700px; height: 100px; overflow-x: hidden; overflow-y: auto; scrollbar-gutter: stable`，并放入高度超过 100px 的内容。经典垂直滚动条在该容器内预留 15px；容器内容宽 685px，与 700px 视口宽度不同。内部 `width: 100vw` 子项按视口宽度为 700px；`width: 100%` 子项按该滚动区域提供的宽度为 685px。这些数字取决于本机的滚动条样式；overlay scrollbar (覆盖式滚动条) 不占宽度，就不会出现差异。根元素（整页）的滚动条情况不同：CSS Overflow 规定根元素的 `scrollbar-gutter` 作用于视口，`vw` 与整页滚动条的关系要在目标浏览器里另行检查，不能套用这个内部容器的结果。

如果目标是填满当前内容区，块级元素保持 `width: auto` 即可，或者写 `width: 100%`，让父级分配可用空间。手动写 `width: 100%` 时，带内边距或边框的元素应配合 `box-sizing: border-box`，以免外尺寸超出父级。

## 断点由视口还是组件决定？

| 需要响应的变化 | 起点 | 报表中的例子 |
| --- | --- | --- |
| 整个页面的视口宽度或方向变化 | `@media` | 小视口把并排区域改为单列，内容按文档源顺序堆叠 |
| 卡片自身分配到的宽度变化 | `@container` | 同一查询卡片在主栏横排，在窄侧栏竖排 |
| 重复卡片随网格可用宽度换列 | Grid 自动重复轨道 | 有空间就放下一列，不硬编码设备名称 |

断点应该设在内容开始放不下的位置，而不是机械套用“手机 / 平板 / 桌面”的设备标签。下面的报表外框在视口宽度不超过 48rem 时由两列（侧栏 + 主栏）改为单列，各区域按 HTML 源码顺序上下堆叠；这条规则只改列数，不改变区域的先后顺序：

~~~css
.report-layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 1rem;
}

@media (max-width: 48rem) {
  .report-layout { grid-template-columns: minmax(0, 1fr); }
}
~~~

媒体查询里的 `em`、`rem` 等字号相对单位按初始字号求值，不按页面样式改过的根字号求值。若初始字号是 16px，`48rem = 768px`，且 `max-width` 包含等号：视口正好 768px 时也改成单列。即使页面写了 `html { font-size: 20px; }`，这个媒体断点仍为 768px。若用户代理或用户偏好改变初始字号，断点也会按那个初始值计算。

媒体查询只知道视口宽度。报表的筛选栏可能放在宽主栏里，也可能放在窄面板里，这时应该按面板自身宽度换列，也就是使用容器查询。做法是把面板设为 inline-size query container (行内尺寸查询容器)，再写 `@container` 规则调整它的后代。几点规则：

- 查询条件只能用来设置查询容器的后代，不能设置容器自己。
- 未命名的 `@container` 从被设样式的元素向外找最近的合格祖先容器；要查询更外层的特定容器，用 `container-name` 命名。
- inline size (行内尺寸) 是沿文字排列方向的尺寸：默认横向书写时就是内容盒宽度，纵向书写时物理上对应高度。

本例中 `.report-panel` 是查询容器，`.report-filter` 是被调整的后代。筛选区有月份、地区和提交按钮三项；每个 `label` 把说明文字和输入控件包在一起，作为一个 Grid 项目参与布局：

~~~html
<section class="report-panel">
  <form class="report-filter" action="/reports" method="get">
    <label>月份
      <input name="month" type="month" value="2026-10">
    </label>
    <label>地区
      <select name="region">
        <option value="">全部地区</option>
        <option value="north">北区</option>
      </select>
    </label>
    <button type="submit">筛选报表</button>
  </form>
</section>
~~~

~~~css
.report-panel {
  container-type: inline-size;
}
.report-filter {
  display: grid;
  grid-template-columns: 1fr;
}

@container (inline-size > 30rem) {
  .report-filter {
    grid-template-columns: 1fr 1fr auto;
    align-items: end;
  }
}
~~~

在根字号 16px、面板内容盒为 480px 的演算中，`30rem = 480px`，但条件使用严格大于号，所以 480px 仍是单列；宽度超过 480px 才是三列。以整数 CSS px 步进时，481px 是第一个匹配值；若容器宽度可以是小数，则 480px 以上的任意值都会匹配。若页面把根字号改为 20px，`rem` 查询阈值为 600px；若要让阈值随面板自身字号缩放，可改用 `em`，它按被选中查询容器的计算字号求值。

本例条件使用逻辑特征 `inline-size`，它随书写模式沿行内轴查询；若改用物理特征 `width`，默认横向书写模式下它指向同一宽度，而纵向书写模式下 `width` 是与行内轴垂直的物理宽度，未必由 `container-type: inline-size` 提供。`container-type: inline-size` 除了让元素可被查询，还会对它施加行内尺寸包含（inline-size containment）和样式包含，并建立独立格式化上下文。行内尺寸包含意味着计算容器的内在宽度时不再考虑子内容，因此容器的宽度应由父级布局或明确约束提供，不能指望子内容把它撑宽。本例的 `section` 是普通块盒，填满父级可用宽度；更复杂的组件需结合自身布局用途选择查询容器。

## 用内容和实际宽度决定响应规则

### 让 Grid 按可容纳的最小轨道自动换列

自动列数由 Grid container (网格容器) 的可用行内尺寸和轨道最小值决定，与卡片文字宽度无关。假设报表主栏的可用宽度为 880px、根字号 16px，最小轨道设为 `15rem = 240px`，间隔设为 `1rem = 16px`：三列至少需要 `3 × 240 + 2 × 16 = 752px`，四列要 `4 × 240 + 3 × 16 = 1008px`，所以这里最多排三列。以下独立例子用三个普通卡片展示；按默认自动放置每项占一列：

~~~html
<section class="report-cards" aria-label="月度报表">
  <article>订单总量</article>
  <article>准时交付</article>
  <article>待复核</article>
</section>
~~~

~~~css
.report-cards {
  display: grid;
  inline-size: min(100%, 880px);
  grid-template-columns:
    repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1rem;
}
~~~

若有三张卡片，每列约 `(880 − 2 × 16) ÷ 3 = 282.7px`；本机 Chromium 157 测得约 282.66px。若只有两张卡片，自动重复仍可容纳三条最小轨道，但 `auto-fit` 折叠没有项目的第三条轨道及其相邻间隔，两列各约 `(880 − 16) ÷ 2 = 432px`。若主栏变成 220px，`min(100%, 15rem)` 允许唯一轨道降至 220px。`auto-fill` 会保留空轨道的位置，适合想在两张卡片后留出空槽而不拉宽卡片的情况。

### 让字号随视口连续变化

视口单位也可以把设计稿尺寸换算成随视口缩放的尺寸。假设设计稿宽 1000px、视口同为 1000px，宽 200px 的图标占画布 20%，所以对应 `20vw`。这只是特定设计宽度下的换算：视口变窄时 `20vw` 会一直缩小。如果图标或文字在窄屏上仍需保持可读，就要用 `clamp(最小值, 首选值, 最大值)` 给出上下限，或在内容放不下时改变布局。下面的标题字号就用 `clamp()` 随视口连续变化：

~~~css
.report-title {
  font-size: clamp(1.25rem, calc(2vw + 0.75rem), 2rem);
}
~~~

根字号为 16px 时，`1.25rem = 20px` 是下限，`2rem = 32px` 是上限：

| 视口宽度 | 中间表达式 `2vw + 0.75rem` | 最终字号 |
| --- | --- | --- |
| 300px | 18px | 20px，下限生效 |
| 600px | 24px | 24px，随视口变化 |
| 1000px | 32px | 32px，正好到达上限 |
| 1200px | 36px | 32px，上限生效 |

不需要连续缩放时，用媒体查询表达台阶变化；需要适配组件大小时，用容器查询；重复内容应随可用宽度换列时，可让 Grid 自动重复轨道参与计算。固定轨道、`fr` 分配与内在最小尺寸的完整关系见[固定与流动内容适合哪种 CSS 布局？](./flex-and-grid-layout.md)。

## 受限文本与行数裁切

空间不够时，除了换列和缩放，还可以裁切文字。单行 ellipsis (省略号) 需要同时满足三个条件：文本块的行内宽度受限、文字不换行、溢出部分被裁切；`text-overflow` 只决定用什么提示溢出，不能代替这些条件。下面的工具栏宽 360px，报表标题链接直接作为 Flex 项目；先看把裁切写在这个项目上的版本：

~~~html
<nav class="toolbar" aria-label="当前报表操作">
  <a class="report-name" href="/reports/october">
    2026 年 10 月跨地区订单处理与复核情况汇总
  </a>
  <button type="button">筛选</button>
</nav>
~~~

~~~css
.toolbar {
  display: flex;
  inline-size: 360px;
  gap: 16px;
}
.toolbar > .report-name {
  flex: 1 1 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
~~~

Flex 项目默认的最小宽度是 `auto`，通常不会小于内容的最小宽度，所以一行不换行的长标题会阻止项目收缩。这个例子把 `overflow: hidden` 写在 Flex 项目本身；`hidden` 会让元素成为滚动容器（不显示滚动条，但仍可由程序滚动），而滚动容器的自动最小尺寸为零，所以不必再写 `min-inline-size: 0`。如果标题外面多包了一层，只在内层链接上裁切，外层的 Flex 项目仍会因为内容最小宽度而拒绝收缩：

~~~html
<div class="toolbar">
  <div class="report-name">
    <a href="/reports/october">
      2026 年 10 月跨地区订单处理与复核情况汇总
    </a>
  </div>
  <button type="button">筛选</button>
</div>
~~~

这时在直接项目上设零最小行内尺寸，并在内层文本元素上裁切：

~~~css
.toolbar > .report-name {
  flex: 1 1 0;
  min-inline-size: 0;
}
.toolbar > .report-name > a {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
~~~

在 Grid 中也要看项目的直接轨道和最小尺寸条件：像 `minmax(0, 1fr)` 这样的零下限轨道已经允许轨道收缩，但内容本身仍需断行、裁切或滚动。`overflow: clip` 不是 `hidden` 的同义写法：前者不建立 scroll container (滚动容器)，可能保留基于内容的自动最小尺寸。需要看完整轨道约束时见[固定与流动内容适合哪种 CSS 布局？](./flex-and-grid-layout.md)。

多行摘要要按行数裁切，需使用目标浏览器支持的写法。CSS Overflow Level 4 草案定义了未加前缀的 `line-clamp`，但在本地 Chromium 157 中，`CSS.supports("line-clamp", "3")` 返回 `false`，而 `CSS.supports("-webkit-line-clamp", "3")` 返回 `true`。下面带前缀的兼容写法在该浏览器中有效，其他目标浏览器仍需验证：

~~~css
.report-summary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
~~~

裁切会改变可见部分，不会删除文本值；用户能否看见、朗读或复制未显示部分取决于交互与工具。关键信息应提供阅读或复制全文的办法；不要把省略号当成唯一披露方式。

## 细边框何时等于一个设备像素？

`1px` 是一个 CSS 参考像素，不保证画出一个物理设备像素宽的线。若 effective device pixel ratio (DPR, 有效设备像素比) 约为 2，一个 CSS 像素对应两个设备像素，`0.5px` 名义上约等于一个设备像素；但实际绘制还受缩放、边缘对齐和栅格化影响。因此，用小数宽度的边框或阴影画细线只是视觉技巧，要在目标设备上检查效果。

~~~css
.hairline {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
~~~

> [!info]- 来源与核验
> - **CSS 绝对、相对与视口单位。** W3C [CSS Values and Units Module Level 4](https://www.w3.org/TR/css-values-4/)，Working Draft，2024-03-12，§§6.1–6.2；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-values-4/)，2026-08-24。包括 `px`、`em`、`rem`、`vw` / `vh`、`svh` / `lvh` / `dvh`、`vmin` / `vmax` 与 `clamp()`。
> - **媒体查询中的相对单位。** W3C [Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/)，Working Draft，2026-02-19，§1.3；媒体查询中的字号相对单位按初始字号解析，核对日期：2026-11-12。
> - **容器查询与相对单位。** W3C [CSS Conditional Rules Level 5](https://www.w3.org/TR/css-conditional-5/)，Working Draft，2025-10-30，§§5、6.1；查询容器、`container-type: inline-size` 与容器查询条件中 `em` / `rem` 的参照值，核对日期：2026-11-12。
> - **文本溢出与行数裁切。** W3C [CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/)，Working Draft，2025-10-07，§§3.1、5.1；[CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/)，Working Draft，2023-03-21，§5.1；并核对 [CSSWG 编辑草案](https://drafts.csswg.org/css-overflow-4/)，2026-10-16，§§5.1、5.1.1，定义 `line-clamp` 与遗留的 `-webkit-line-clamp` 语法。
> - **Grid / Flex 自动最小尺寸。** W3C [CSS Flexible Box Layout Level 1](https://www.w3.org/TR/css-flexbox-1/)，Candidate Recommendation Draft，2025-10-14，§4.5；[CSS Grid Layout Level 2](https://www.w3.org/TR/css-grid-2/)，Candidate Recommendation Draft，2025-03-26，§6.6。核对日期：2026-11-12。
> - **本地探针。** 本轮 headless Chrome `157.0.8103.51`：根字号 20px、查询容器字号 10px 时，`30rem` 条件在宽度 601px 匹配、`30em` 在 301px 即匹配；视口 800px 时 `max-width: 48rem` 不匹配；`CSS.supports()` 对未加前缀 `line-clamp` 返回 `false`、对 `-webkit-line-clamp` 返回 `true`。滚动条宽度例子使用 700px 视口和内部 `.scroll-area { width: 700px; height: 100px; overflow-x: hidden; overflow-y: auto; scrollbar-gutter: stable }`，内容高度 202px；内部 `100vw` / `width: 100%` 子项的实际宽度分别为 700px / 685px。该数值不代表根元素的视口滚动条行为，也不能替代目标浏览器矩阵检查。
