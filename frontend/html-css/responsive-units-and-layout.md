# 页面怎样响应视口、容器和用户设置？

前几章的例子都用固定宽度手算。真实页面的视口会变，同一组件会放进宽窄不同的容器，用户还可能在浏览器里调大基础字号。本章回答两个问题：长度单位“相对于什么”计算；样式规则该在“谁的尺寸或状态”变化时切换。例子沿用主线一的报表页 `/reports/42`，看它的外框、筛选表单、标题和摘要在不同空间下怎样变化。

## 长度单位各参照什么

| 单位 | 参照 | 常见用途 | 要记住的边界 |
| --- | --- | --- | --- |
| `px` | CSS reference pixel (CSS 参考像素) | 边框、精确间距 | 不保证画成一个物理设备像素，见文末细线一节 |
| `%` | 该属性定义的参照盒或参照值 | 流动宽度、偏移 | 每个属性的百分比基准不同，不能只看符号 |
| `em` | 使用该值的元素的计算字号；用在 `font-size` 上时取继承来的字号 | 随文字缩放的局部间距 | 嵌套字号会逐层相乘 |
| `rem` | 根元素的计算字号 | 跨组件一致的文字相对尺寸 | 在 `@media`、`@container` 里参照不同，见下一节 |
| `vw` / `vh` | 默认 large viewport (大视口) 宽、高的 1% | 视口区域 | 视口不是内容盒；移动端工具栏展开时，`100vh` 可能大于可见高度 |
| `svh` / `lvh` / `dvh` | small (小)、large (大)、dynamic (动态) 视口高度的 1% | 移动端全高界面 | 要选是否随浏览器工具栏伸缩 |
| `vmin` / `vmax` | 默认大视口短边 / 长边的 1% | 随方向变化的尺寸 | 不表示内容容器宽度 |

几个演算：

- 初始字号与根字号都是 `16px` 时，`1.5rem = 24px`；把根元素计算字号改为 `20px` 后，普通声明里的 `5rem = 100px`。
- `em` 用在 `font-size` 上会逐层相乘：父级 `16px`，子元素 `font-size: 1.25em` 得 `20px`，孙元素再写 `1.25em` 得 `25px`。`rem` 让一组声明共用根字号，没有这种累积。
- `rem` 用在根元素自己的 `font-size` 上时，为避免循环引用，参照初始字号。

页面用 `px` 把根字号写死（如 `html { font-size: 16px; }`），会覆盖用户在浏览器里设置的基础字号偏好。用百分比写根字号，如 `html { font-size: 125%; }`，结果按用户的初始字号缩放，保留了这份偏好。

移动端浏览器的地址栏和工具栏会展开、收起，可见视口高度随之变化。`100svh` 按工具栏展开时的小视口算，`100lvh` 按收起时的大视口算，`100dvh` 跟随当前视口。要让关键内容在工具栏展开时也完整可见，用小视口单位；要让元素跟着可见区域伸缩，用动态单位，并接受伸缩时布局随之变化。

## 同一个 em 和 rem 在查询条件里参照不同

| 使用位置 | `em` 的参照 | `rem` 的参照 |
| --- | --- | --- |
| 普通样式声明 | 使用该值的元素的计算字号；`font-size` 上取父元素字号 | 根元素计算字号 |
| `@media` 条件 | 初始 `font-size` 值 | 初始 `font-size` 值 |
| `@container` 尺寸条件 | 被选中的查询容器的计算字号 | 根元素计算字号 |

所以媒体查询里的 `rem` 断点不随页面自己写的 `html { font-size: ... }` 改变，只跟随初始字号，而初始字号受用户的浏览器字号设置影响。容器查询则相反：`rem` 跟页面根字号走，`em` 跟查询容器自己的字号走。两节之后的例子会分别演算。

## 100vw 和 100% 为什么不同

`100vw` 按视口宽度算，`100%` 按父级提供的宽度算。页面内部滚动容器的滚动条只占该容器自己的宽度，不缩小视口，两者就会出现差异。

> [!example] headless Chrome 157.0.8103.51 的内部滚动区域
> 视口 `700px`。内部 `<section>` 设 `width: 700px; height: 100px; overflow-x: hidden; overflow-y: auto; scrollbar-gutter: stable`，内容高 `202px`。经典垂直滚动条在容器内预留 `15px`，容器内容宽 `685px`。子项写 `width: 100vw` 得 `700px`，比容器内容宽多出 `15px`（被 `overflow-x: hidden` 裁掉）；写 `width: 100%` 得 `685px`。
>
> 数值取决于本机滚动条样式；overlay scrollbar (覆盖式滚动条) 不占宽度，就没有差异。整页滚动条的情况不同：CSS Overflow 规定根元素的 `scrollbar-gutter` 作用于视口，`vw` 与整页滚动条的关系要在目标浏览器里另行检查，不能套用这个内部容器的结果。

目标是填满当前内容区时，块级元素保持 `width: auto` 即可，它已经按[块盒宽度等式](./box-model-and-normal-flow.md#不写%20width%20时，块盒怎样放满父级)扣掉了 padding、border 和 margin。手动写 `width: 100%` 时，带 padding 或 border 的元素要配 `box-sizing: border-box`，否则外尺寸超出父级。

## 三种响应机制怎样选

| 需要响应的变化 | 机制 | 报表页里的例子 |
| --- | --- | --- |
| 整个视口的宽度、方向或用户偏好 | `@media` | 窄视口把侧栏 + 主栏改为单列，区域按源码顺序堆叠 |
| 组件自己分到的宽度 | `@container` | 同一筛选表单在宽主栏里横排，在窄面板里竖排 |
| 重复项目随可用宽度换列 | Grid `repeat(auto-fit, ...)` | 摘要卡有空间就放下一列，不写断点 |

断点应设在内容开始放不下的位置，而不是机械套用“手机/平板/桌面”的设备标签。

### @media：按视口切换外框

报表外框在视口宽度不超过 `48rem` 时，从两列（侧栏 + 主栏）改为单列。这条规则只改列数，各区域仍按 HTML 源码顺序上下堆叠：

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

`minmax(0, 1fr)` 的作用见[自动最小尺寸](./flex-and-grid-layout.md#自动最小尺寸让项目拒绝收缩)。初始字号是 `16px` 时，`48rem = 768px`；`max-width` 含等号，视口正好 `768px` 时也是单列。即使页面写了 `html { font-size: 20px; }`，断点仍是 `768px`，不会变成 `960px`。用户在浏览器里改了初始字号，断点就按那个值计算。

### @container：按组件自身宽度切换

媒体查询只知道视口。筛选表单可能放在宽主栏里，也可能放在窄面板里，应该按面板自身宽度换列。做法是把面板设为 inline-size query container (行内尺寸查询容器)，再用 `@container` 规则调整它的后代：

- 查询条件只能用来设置查询容器的后代，不能设置容器自己。
- 未命名的 `@container` 从被设样式的元素向外找最近的合格祖先容器；要查询更外层的特定容器，用 `container-name` 命名。
- inline size (行内尺寸) 是沿文字排列方向的尺寸：横向书写时就是内容盒宽度，纵向书写时物理上对应高度。

沿用[表单一章](./accessible-forms-and-submission.md)的筛选表单，这里只保留起始月份、地区和提交按钮三项。为了让每个控件和它的标签成为一个 Grid 项目，改用把控件包进 `label` 的关联写法（两种写法都有效，见那一章）：

~~~html
<section class="report-panel">
  <form class="report-filter" action="/reports/42" method="get">
    <label>From month
      <input name="from" type="month" value="2026-04">
    </label>
    <label>Region
      <select name="region">
        <option value="">All regions</option>
        <option value="north">North</option>
        <option value="south">South</option>
      </select>
    </label>
    <button type="submit">Filter reports</button>
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

根字号 `16px` 时 `30rem = 480px`。条件用严格大于号，面板内容盒正好 `480px` 时仍是单列，超过才是三列：以整数 CSS px 计，`481px` 是第一个匹配值；容器宽度可以是小数时，`480px` 以上的任何值都匹配。页面把根字号改为 `20px` 时，`rem` 阈值变成 `600px`。要让阈值随面板自身字号缩放，改用 `em`，它按查询容器的计算字号求值。

> [!example] headless Chrome 157.0.8103.51 探针
> 根字号 `20px`、查询容器字号 `10px`：`30rem` 条件在容器宽 `601px` 时匹配（阈值 `600px`）；`30em` 条件在 `301px` 时就匹配（阈值 `300px`）。

条件用的是逻辑特征 `inline-size`，它随书写模式沿行内轴查询。改用物理特征 `width`，横向书写时指向同一宽度；纵向书写时 `width` 与行内轴垂直，未必由 `container-type: inline-size` 提供。

`container-type: inline-size` 除了让元素可被查询，还给它施加行内尺寸包含（inline-size containment）和样式包含，并建立独立格式化上下文。行内尺寸包含意味着计算容器的内在宽度时不考虑子内容，所以容器宽度要由父级布局或明确约束提供，不能指望子内容把它撑宽。本例的 `section` 是普通块盒，宽度来自父级。

### auto-fit：不写断点的换列

摘要卡用 `repeat(auto-fit, minmax(min(100%, 15rem), 1fr))`，由 Grid 容器的可用宽度和每列下限直接算出列数，与卡片文字宽度无关，也不需要断点。`880px` 主栏放 3 列、两张卡片时折叠空轨道等演算，以及 `auto-fill` 的区别，见[auto-fit 与 auto-fill](./flex-and-grid-layout.md#auto-fit%20与%20auto-fill%20按宽度决定列数)。

## 用 clamp 让字号连续变化

视口单位能把设计稿尺寸换算成随视口缩放的尺寸。设计稿宽 `1000px`、视口也是 `1000px` 时，宽 `200px` 的图标占 `20%`，对应 `20vw`。但这只在那个设计宽度下成立：视口变窄时 `20vw` 会一直缩小。要在窄屏上保持可读，就用 `clamp(最小值, 首选值, 最大值)` 给出上下限，或者在内容放不下时改变布局。

报表标题的字号随视口连续变化：

~~~css
.report-title {
  font-size: clamp(1.25rem, calc(2vw + 0.75rem), 2rem);
}
~~~

根字号 `16px` 时，下限 `1.25rem = 20px`，上限 `2rem = 32px`，`0.75rem = 12px`：

| 视口宽度 | `2vw + 0.75rem` | 最终字号 |
| --- | --- | --- |
| `300px` | `6 + 12 = 18px` | `20px`，下限生效 |
| `600px` | `12 + 12 = 24px` | `24px`，随视口变化 |
| `1000px` | `20 + 12 = 32px` | `32px`，正好到上限 |
| `1200px` | `24 + 12 = 36px` | `32px`，上限生效 |

首选值里保留一个 `rem` 项，使字号在视口固定时仍随根字号变化。需要台阶式变化时用媒体查询，需要适配组件大小时用容器查询。

## 文字放不下时怎样省略和裁切

空间不够时，除了换列和缩放，还可以裁切文字。单行 ellipsis (省略号) 要同时满足三个条件：

1. 文本所在的盒子行内宽度受限；
2. 文字不换行（`white-space: nowrap`）；
3. 溢出部分被裁切（`overflow: hidden` 等非 `visible` 值）。

`text-overflow: ellipsis` 只决定用什么提示溢出，不能代替这三个条件：

~~~css
.report-name {
  display: block;
  inline-size: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
~~~

文字在 Flex 或 Grid 项目里时，第 1 条还取决于项目能不能缩小：项目的自动最小尺寸可能让它按内容宽度拒绝收缩，于是宽度从未受限，省略号也不出现。报表工具栏的标题截断、外面多包一层时要在哪一层写 `min-inline-size: 0`，见[自动最小尺寸让项目拒绝收缩](./flex-and-grid-layout.md#自动最小尺寸让项目拒绝收缩)。

### 多行摘要按行数裁切

多行摘要按行数裁切，要用目标浏览器支持的写法。CSS Overflow Level 4 草案定义了未加前缀的 `line-clamp`，但在本机 Chromium 157 中，`CSS.supports("line-clamp", "3")` 返回 `false`，`CSS.supports("-webkit-line-clamp", "3")` 返回 `true`。下面带前缀的写法在该浏览器中有效，其他目标浏览器仍需验证：

~~~css
.report-summary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
~~~

裁切改变的是可见部分，不删除文本。用户能否看见、朗读或复制未显示的部分，取决于交互和所用工具。关键信息要提供阅读或复制全文的办法，不要把省略号当成唯一的披露方式。

## 细线：1px 何时等于一个设备像素

`1px` 是一个 CSS 参考像素，不保证画成一个物理设备像素宽的线。effective device pixel ratio (DPR，有效设备像素比) 约为 2 时，一个 CSS 像素对应两个设备像素，`0.5px` 名义上约等于一个设备像素；实际绘制还受页面缩放、边缘对齐和栅格化影响。所以用小数宽度的边框或阴影画 hairline (细线) 只是视觉技巧，要在目标设备上检查效果：

~~~css
.hairline {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
~~~

## 布局之后：收起一块内容会影响什么

到这里，报表页的外框、筛选表单、标题和摘要都能随视口、容器和用户字号变化：单位决定参照什么，`@media`、`@container` 和 `auto-fit` 决定规则在谁变化时切换，省略和裁切处理最后放不下的文字。界面还会在状态变化时隐藏或展开某些部分，例如收起筛选面板；那时布局、指针、焦点和读屏各受什么影响，见下一章[隐藏内容时，布局、指针、焦点和读屏各受什么影响](./hiding-content-and-focus.md)。

> [!info]- 来源
> - **绝对、相对与视口单位，`clamp()`**（“长度单位各参照什么”“用 clamp 让字号连续变化”）：W3C CSS Values and Units Module Level 4，Working Draft 2024-03-12，§§6.1–6.2，<https://www.w3.org/TR/css-values-4/>；并核对 CSSWG 编辑草案 2026-08-24，<https://drafts.csswg.org/css-values-4/>。包括 `px`、`em`、`rem`、`vw`/`vh`、`svh`/`lvh`/`dvh`、`vmin`/`vmax`、根元素 `font-size` 上的 `rem`。
> - **媒体查询中的相对单位按初始字号求值**（“同一个 em 和 rem 在查询条件里参照不同”“@media”）：W3C Media Queries Level 5，Working Draft 2026-02-19，§1.3，<https://www.w3.org/TR/mediaqueries-5/>。核对日期 2026-11-12。
> - **查询容器、`container-type: inline-size` 的包含效果、容器条件中的 `em`/`rem`**（“同一个 em 和 rem 在查询条件里参照不同”“@container”）：W3C CSS Conditional Rules Level 5，Working Draft 2025-10-30，§§5、6.1，<https://www.w3.org/TR/css-conditional-5/>。核对日期 2026-11-12。
> - **根元素 `scrollbar-gutter` 作用于视口；文本溢出；`line-clamp` 与 `-webkit-line-clamp`**（“100vw 和 100% 为什么不同”“文字放不下时怎样省略和裁切”）：W3C CSS Overflow Level 3，Working Draft 2025-10-07，§§3.1、5.1，<https://www.w3.org/TR/css-overflow-3/>；CSS Overflow Level 4，Working Draft 2023-03-21，§5.1，<https://www.w3.org/TR/css-overflow-4/>；并核对 CSSWG 编辑草案 2026-10-16，§§5.1、5.1.1，<https://drafts.csswg.org/css-overflow-4/>。
> - **Flex/Grid 自动最小尺寸**（“文字放不下时怎样省略和裁切”的链接说明）：W3C CSS Flexible Box Layout Level 1，Candidate Recommendation Draft 2025-10-14，§4.5，<https://www.w3.org/TR/css-flexbox-1/>；CSS Grid Layout Level 2，Candidate Recommendation Draft 2025-03-26，§6.6，<https://www.w3.org/TR/css-grid-2/>。核对日期 2026-11-12。
> - **本地探针**（各 `[!example]` 与 `line-clamp` 支持）：headless Chrome `157.0.8103.51`。根字号 `20px`、查询容器字号 `10px` 时 `30rem` 在 `601px` 匹配、`30em` 在 `301px` 匹配；`CSS.supports()` 对 `line-clamp` 返回 `false`、对 `-webkit-line-clamp` 返回 `true`；`700px` 视口内部滚动区域（内容高 `202px`）中 `100vw`/`100%` 子项为 `700px`/`685px`。不代表根元素视口滚动条的行为，也不能替代目标浏览器矩阵检查。
