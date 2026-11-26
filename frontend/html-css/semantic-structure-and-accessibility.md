# 页面结构怎样让所有人都能读懂和操作？

同一份 HTML 有几类读者：用眼睛看的人、只用键盘的人、靠屏幕阅读器听页面的人，还有浏览器和搜索引擎。本章回答：HTML 要写出哪些结构，这些读者才都能找到内容、理解它，并按合理的顺序操作。

本章沿用主线一的[报表页](../browser/from-url-to-interactive-page.md)：地址 `/reports/42?sort=recent#summary`，标题带 `id="summary"`，`#sort-controls` 里的两个排序按钮“最近优先”（`Most recent`）和“最早优先”（`Oldest first`）用 `aria-pressed` 标出当前排序，数据有 May（`r-104`）、April（`r-103`）两行。主线一关心它何时显示、点击何时生效；这里看同一份 HTML 表达了什么结构。

页面界面沿用主线一的英文文字，正文用中文称呼它们。本章给两行补上“订单数”（`Orders`）和“对账状态”（`Reconciliation`）两列，数值是教学用的合成值。

## 文档骨架先告诉浏览器怎样解释页面

骨架里的每一行都回答浏览器的一个问题：

- `<!doctype html>`：用标准模式解析和布局，而不是兼容旧页面的怪异模式。
- `<html lang="en">`：页面主要语言，必须与内容的实际语言一致。屏幕阅读器据此选发音规则，浏览器也可能据此选字体、拼写检查词典和日期选择器等控件的界面语言。页面里夹着另一种语言的片段时，在那个元素上再写 `lang`，例如一段中文说明写 `<p lang="zh-CN">`。
- `<meta charset="utf-8">`：字节按什么编码解码。文件本身也必须真的以 UTF-8 保存；这条声明修不好已经编错的字节。
- `<meta name="viewport" content="width=device-width, initial-scale=1">`：在窄屏上让 layout viewport (布局视口) 的宽度等于设备宽度。它只设视口，不会把固定宽度的布局变成响应式布局；响应式要靠 CSS，见[页面怎样响应视口、容器和用户设置？](./responsive-units-and-layout.md)。
- `<title>`：命名浏览器标签页。

~~~html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Report 42</title>
</head>
<body>
  <header><!-- 站点名与账户菜单 --></header>
  <nav aria-label="Reports">…</nav>
  <main>
    <h1 id="summary">Recent reports</h1>
    <div id="sort-controls">
      <button type="button" data-sort="recent" aria-pressed="true">Most recent</button>
      <button type="button" data-sort="oldest" aria-pressed="false">Oldest first</button>
    </div>
    <!-- 结果表格，见下文 -->
  </main>
</body>
</html>
~~~

> [!info]- 其他元数据与内容模型
> `meta name="description"` 可提供搜索摘要，但搜索引擎可能改从正文生成；`link rel="icon"` 提供站点图标，搜索结果是否展示仍由搜索引擎决定。Google Search 不把 `meta name="keywords"` 当作排名信号。
>
> 元素按含义选，不按默认外观选：CSS 能改显示方式，改不了语义。`div`、`span` 留给没有更具体含义的容器。内容模型也不随 CSS 改变：段落只接受 phrasing content (短语内容)，把 `div` 设成 `display: inline` 也不能放进 `p`。

## 标题和 landmark 让人跳到想去的地方

视力正常的人扫一眼就知道页面分几块。读屏用户靠两种结构做同样的事：按标题跳，或按 landmark (地标区域) 跳。

- **标题层级**表达文档大纲：页面主题用一个 `h1`，下级区块用 `h2`，再往下用 `h3`。层级表达结构，字号交给 CSS；不要因为想要小一点的字就跳级。
- **landmark** 标记页面区域：`header`、`nav`、`main`、`aside`、`footer`、带名称的 `section` 和 `form` 等。上面骨架里，读屏用户可以直接跳到 `main` 跳过站点导航；页面有多个 `nav` 时用 `aria-label` 区分它们。

`id` 在一份文档中必须唯一，它既用于把标签关联到控件，也是片段导航的目标：地址里的 `#summary` 让浏览器滚到 `h1#summary`。`class` 则把多个元素归入同一组样式，可以重复。

## 文本元素表达含义，不表达外观

下表是常用文本元素的含义。浏览器默认样式只是这些含义的一种呈现，CSS 改了外观，含义不变。

| 想表达的意思 | 用 | 不要用来 |
| --- | --- | --- |
| 段落 | `p` | 用 `br` 连续换行模拟段距 |
| 有意义的换行（地址、诗行） | `br` | 制造垂直间距 |
| 段落级的主题转换 | `hr` | 画装饰分隔线（用 CSS 边框） |
| 重要、严重或紧急 | `strong` | 仅为加粗 |
| 引起注意但不加重要性 | `b` | 表达“重要” |
| 语气重读，改变句意 | `em` | 仅为斜体 |
| 另一种语调或表达方式，如术语、外语词 | `i` | 表达重读 |
| 删除与插入的修订 | `del`、`ins` | 表达“已不准确” |
| 内容已不再准确 | `s` | 记录修订历史 |
| 非文本注记，如标出错别字 | `u` | 装饰下划线 |
| 无序项目 / 有序步骤 / 术语与解释 | `ul` / `ol` / `dl`、`dt`、`dd` | 用连续空格或 `&nbsp;` 对齐 |

`u` 的例子：在“订单状太”中用 `<u>太</u>` 标出误写的字。连续空格和 `&nbsp;` 都不该用来排版，间距和对齐交给 CSS。

## 有行列关系的数据用真表格

主线一为了观察加载时序，把两行写成了列表 `ol#reports`。一旦每行有几列可以横向比较的数据，就该改用表格标记。用 CSS Grid 摆出“像表格”的样子没有表格语义：屏幕阅读器无法告诉用户某个单元格属于哪一行哪一列。

~~~html
<table>
  <caption>Report 42: monthly orders, most recent first</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Orders</th>
      <th scope="col">Reconciliation</th>
    </tr>
  </thead>
  <tbody>
    <tr data-id="r-104"><th scope="row">May</th><td>128</td><td>Reconciled</td></tr>
    <tr data-id="r-103"><th scope="row">April</th><td>117</td><td class="pending">Pending</td></tr>
  </tbody>
</table>
~~~

`data-id` 仍留给脚本：主线一的排序处理器重排 `ol#reports` 里的 `li`，换成表格后要改为重排 `tbody` 里的 `tr`。这个表格版本只用于本主线讨论结构和布局；其他主线关心行数据和排序代码，仍沿用 `ol#reports`。

- `caption` 给表格起名。读屏用户进入表格时先听到它，知道这张表讲什么、按什么排序。
- `th scope="col"` 标出列标题，`th scope="row"` 标出标识这一行的值。月份唯一标识一行，所以 May、April 用 `th` 而不是 `td`。

有了这两种标题，用户停在 `117` 上时，屏幕阅读器能告诉他这是 April 行、`Orders` 列；停在 `Pending` 上时，能报出它属于 April 行的 `Reconciliation` 列。具体导航键和播报措辞随浏览器与辅助技术而异。

### 跨行单元格占住后面的位置

`rowspan`、`colspan` 让一个单元格占据多个格位，被占的格位在后续行里不再写单元格。给表格加一列“季度”（`Quarter`），May 和 April 同属第二季度（`Q2`）：

~~~html
<thead>
  <tr><th scope="col">Quarter</th><th scope="col">Month</th><th scope="col">Orders</th><th scope="col">Reconciliation</th></tr>
</thead>
<tbody>
  <tr><th scope="rowgroup" rowspan="2">Q2</th><th scope="row">May</th><td>128</td><td>Reconciled</td></tr>
  <tr><th scope="row">April</th><td>117</td><td>Pending</td></tr>
</tbody>
~~~

四列表格里，第一行写满四个单元格；第二行的第一列已被 `Q2` 占住，所以只写三个。若第二行仍写四个，最后一个会被挤到第五列，整列错位。`scope="rowgroup"` 说明 `Q2` 是整个 `tbody` 的标题。

### 窄屏上让表格自己横向滚动

列多的表在窄屏上放不下时，不要让整个页面横向溢出，而是把表格放进一个局部横向滚动容器：

~~~html
<div class="table-scroll">
  <table>…</table>
</div>
~~~

~~~css
.table-scroll { overflow-x: auto; }
~~~

这样只有表格区域左右滚动，标题、按钮和正文仍按视口宽度排版。`overflow` 会让容器成为滚动容器，副作用见[盒子的尺寸怎样计算？](./box-model-and-normal-flow.md)；固定内容与流动内容怎样分配宽度见[Flex 和 Grid 怎样把空间分给每个项目？](./flex-and-grid-layout.md)。

## 焦点顺序跟随源码

键盘用户按 Tab 在可聚焦元素之间移动，这条路径叫 sequential focus navigation (顺序焦点导航)。屏幕阅读器线性朗读页面时走的也是同一种顺序。两者的规则相同：**默认顺序就是 DOM 中的源码顺序**，CSS 把元素画在哪里不影响它。

具体有三条规则：

1. 链接、按钮、表单控件等原生可交互元素天生可聚焦，按源码先后进入 Tab 顺序。
2. `tabindex="0"` 把本来不可聚焦的元素按源码位置加入 Tab 顺序；`tabindex="-1"` 让元素可被脚本 `focus()`，但不进入 Tab 顺序。表单出错后把焦点移到错误摘要，用的就是后者。
3. 正数 `tabindex` 会让这些元素排在所有 `tabindex="0"` 和原生可聚焦元素之前，按数值从小到大访问。它让焦点先跳到页面某处再回到开头，几乎总是破坏顺序，不要用。

### 视觉重排的代价

Flexbox 的 `order` 和 `flex-direction: row-reverse`、Grid 的放置规则、绝对定位，都只改视觉位置，不改 Tab 顺序和朗读顺序。看报表页的排序按钮：源码里“最近优先”在前。假设设计要求宽屏上把“最早优先”放在左边，有人这样写：

~~~css
#sort-controls { display: flex; }
#sort-controls [data-sort="oldest"] { order: -1; }
~~~

视觉上从左到右是“最早优先 | 最近优先”，但按 Tab 时焦点先到右边的“最近优先”，再往左跳到“最早优先”；屏幕阅读器也先读“最近优先”。看着屏幕操作的键盘用户会觉得焦点在乱跳。

修法是直接调换两个按钮在 HTML 里的顺序，让源码顺序就是想要的阅读顺序，再删掉 `order`。视觉移动只适合不改变阅读意义的场合，例如纯装饰元素。

> [!info] 草案：`reading-flow` 与 `reading-order`
> W3C CSS Display Level 4（Working Draft，2025-11-06）定义了 `reading-flow`（加在 flex、grid 等容器上）和 `reading-order`（加在项目上），让特定布局里的阅读与焦点顺序跟随视觉顺序。它们仍是草案，浏览器支持要按目标环境核对。本章的做法是先修源码顺序，不依赖它们。

### 焦点要看得见、不被盖住

焦点顺序合理还不够，用户还得看见焦点在哪。不要只写 `outline: none` 去掉浏览器默认焦点框；需要自定义时，用 `:focus-visible` 给出清晰的样式：

~~~css
#sort-controls button:focus-visible {
  outline: 3px solid #1a5fb4;
  outline-offset: 2px;
}
~~~

`:focus-visible` 只在浏览器判断用户需要看到焦点时匹配，例如键盘操作；鼠标点击按钮时通常不显示焦点框。获得焦点的元素也不能被吸顶的页头、页脚或浮层完全盖住，否则用户按了 Tab 却找不到焦点。

## 状态不能只靠颜色

报表页有两处状态：哪个排序按钮处于按下状态，哪一行还没对账。只用颜色表达这两种状态，色觉障碍用户、黑白打印和高对比度模式下的用户都会丢失信息；屏幕阅读器更是读不出颜色。

每种状态要同时满足两个条件：

- **程序可读**：按下状态写在 `aria-pressed="true"` 上，辅助技术会读作“已按下”；对账状态写成单元格里的文字 `Pending`。
- **视觉上不只靠色相**：再加一种颜色以外的线索，例如边框、字重、图标或文字。

~~~css
#sort-controls button[aria-pressed="true"] {
  border-bottom: 3px solid currentColor;
  font-weight: 600;
}

td.pending {
  background: #fff3d6; /* 颜色只是辅助，单元格里仍写 Pending */
}
~~~

样式直接选 `[aria-pressed="true"]`，程序状态和视觉状态就来自同一个属性，脚本只需改一处，两者不会不一致。表单错误也遵循同一原则，见[表单控件怎样命名、提交和校验？](./accessible-forms-and-submission.md)。

## 用户输入按文字显示

HTML 源码里的 `<` 和 `&` 有特殊含义，要显示它们本身就写 character reference (字符引用)：普通文本里 `&lt;` 显示为 `<`，`&amp;` 显示为 `&`，`&nbsp;` 是不换行空格。字符引用按所在解析状态处理：`script` 里的 script data 状态和 `style` 里的 RAWTEXT 状态都不会像正文那样解码它们。

字符引用是写源码的手段，不是安全显示动态字符串的手段。报表标题、负责人姓名这类来自用户的值，要通过 DOM 的文本接口（如 `textContent`）写进页面，浏览器只把它当文字；不要把拼接好的字符串交给 `innerHTML` 当标记解析。几种内容接口的区别见[怎样查询和修改 DOM？](../browser/dom-queries-and-updates.md)，不可信文本的安全显示见[不可信报表标题怎样安全显示？](../../engineering-foundations/services/sessions-and-browser-boundaries.md#不可信报表标题怎样安全显示？)。

## 结构定好之后，表单和样式从这里接手

到这里，报表页有了能被正确解释的骨架、可跳转的标题和 landmark、带行列标题的真表格，以及与视觉一致的源码顺序；排序按钮和对账状态都不只靠颜色。

下一步给报表页加一张筛选表单。问题变成：控件的名字从哪来，用户的选择怎样变成 URL 查询串，出错时又怎样让所有人都发现？见[表单控件怎样命名、提交和校验，才对所有人可用？](./accessible-forms-and-submission.md)。

> [!info]- 来源
> - 文档骨架、语言、元数据、标题与 landmark 元素、内容模型：WHATWG HTML Living Standard §3–4，[The lang attribute](https://html.spec.whatwg.org/multipage/dom.html#the-lang-and-xml:lang-attributes)（§3.2.6.2：用户代理可据语言选字体、发音、词典和日期选择器等控件界面）、[Document semantics and metadata](https://html.spec.whatwg.org/multipage/semantics.html)、[Sections](https://html.spec.whatwg.org/multipage/sections.html)，更新时间 2026-11-11，检查于 2026-11-11。
> - 文本语义速查（段落、换行、主题分隔、强调、修订、列表）：WHATWG HTML Living Standard，[Grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[Text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)、[Edits](https://html.spec.whatwg.org/multipage/edits.html)，检查于 2026-11-11。
> - 表格标题、`th scope`、行列标题关系、`rowspan`/`colspan` 格位：WHATWG HTML Living Standard §4.9，[Tables](https://html.spec.whatwg.org/multipage/tables.html)，检查于 2026-11-11。
> - 顺序焦点导航与 `tabindex` 的 0、负数、正数取值：WHATWG HTML Living Standard §6.6.3，[The tabindex attribute](https://html.spec.whatwg.org/multipage/interaction.html#attr-tabindex)，检查于 2026-11-26。
> - `order` 不影响非视觉媒体与顺序导航，以及 `reading-flow`、`reading-order`：W3C CSS Display Level 4，§3.1、§4，Working Draft（2025-11-06），[CSS Display Level 4](https://www.w3.org/TR/css-display-4/#reading-flow)；Flexbox 重排与可访问性：W3C CSS Flexible Box Layout Level 1 §5.4；Grid 放置：W3C CSS Grid Layout Level 2 §4，检查于 2026-11-11。
> - landmark 区域与多个同类 landmark 用名称区分：W3C HTML Accessibility API Mappings 1.0（元素到 landmark 角色的映射），[HTML AAM](https://www.w3.org/TR/html-aam-1.0/)；WAI-ARIA Authoring Practices Guide，[Landmark Regions](https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/)，检查于 2026-11-26。
> - `:focus-visible` 由浏览器按启发式判断是否匹配：W3C Selectors Level 4 §9.4，[The Focus-Indicated Pseudo-class](https://www.w3.org/TR/selectors-4/#the-focus-visible-pseudo)，检查于 2026-11-26。
> - 焦点可见、焦点不被完全遮挡、状态不只用颜色：W3C WCAG 2.2，Success Criteria 2.4.7、2.4.11、1.4.1，Recommendation（2024-12-12），[WCAG 2.2](https://www.w3.org/TR/WCAG22/)，检查于 2026-11-11。
> - 字符引用、script data 与 RAWTEXT 解析状态、动态文本：WHATWG HTML Living Standard §13.2.5、§13.5，[Parsing HTML documents](https://html.spec.whatwg.org/multipage/parsing.html)、[Named character references](https://html.spec.whatwg.org/multipage/named-characters.html)；WHATWG DOM Standard，[`Node.textContent`](https://dom.spec.whatwg.org/#dom-node-textcontent)，检查于 2026-11-11。
> - 搜索摘要、站点图标与 meta keywords：Google Search Central，[Snippets](https://developers.google.com/search/docs/appearance/snippet)、[Favicon](https://developers.google.com/search/docs/appearance/favicon-in-search)、[Supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)，检查于 2026-11-11。
