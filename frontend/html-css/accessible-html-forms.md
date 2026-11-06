# 语义化 HTML 表单如何支持键盘与辅助技术用户？

从一次只读报表筛选开始：读者选择月份、地区和状态，提交后查看结果。用 HTML 元素表达控件的用途和关系，再用 CSS 布局；样式改变位置和外观，不会替代控件语义、键盘行为或文档顺序。

## 先建立有语言和视口的文档

页面骨架提供浏览器解释和辅助技术导航所需的信息。<code>&lt;!doctype html&gt;</code> 选择标准模式；根元素的 <code>lang</code> 声明主要语言；<code>title</code> 命名浏览器标签页；<code>meta viewport</code> 让窄屏的布局视口与设备宽度相符。文件也应实际使用 UTF-8 编码，字符集声明不会把错误编码的字节转换成正确内容。视口声明本身不会让固定宽度布局变得响应式。

~~~html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="按月份、地区和订单状态查看月度订单。">
  <link rel="icon" href="/favicon.ico">
  <title>月度订单报表</title>
</head>
<body>
  <main>
    <h1>月度订单报表</h1>
    <!-- 报表筛选表单与结果表格 -->
  </main>
</body>
</html>
~~~

让标题层级表达页面结构，用 <code>main</code>、<code>nav</code> 等 landmark 标记主要区域。<code>div</code> 和 <code>span</code> 适合没有更具体语义的布局容器；不要按默认字号或默认块级显示来选择元素，因为 CSS 可以改变显示方式，不能因此改变元素语义。<code>id</code> 在一份文档中应唯一，可用于 label 关联和片段导航；<code>class</code> 则可把多个元素归为同一组样式。HTML 内容模型仍决定元素能否嵌套，例如段落只接受 phrasing content；给 <code>div</code> 设成 inline 样式也不会让它变成段落可接受的语义内容。

<code>meta name="description"</code> 可提供页面摘要，但搜索引擎可能改从正文生成摘要；<code>link rel="icon"</code> 提供浏览器和搜索结果可用的站点图标。<code>meta name="keywords"</code> 不是 Google Search 的排名信号，不应为了 SEO 把关键词堆在 head 里。

## 让控件名称、提交值和动作明确

每个输入字段都要有可见且程序化关联的 <code>label</code>（标签）；按钮可由自己的文字命名。下面的表单用 <code>GET</code> 表达只读筛选，并把字段名和值放进 URL；只有在筛选结果可以安全地由 URL 表达时才适用。缺少 <code>name</code> 的字段不会进入提交数据；未选中的复选框（checkbox）或单选框（radio）也不会提交。<code>placeholder</code> 只是输入提示，不能替代标签。

~~~html
<form action="/reports" method="get">
  <label for="month">月份</label>
  <input id="month" name="month" type="month" value="2026-10">

  <label for="region">地区</label>
  <select id="region" name="region">
    <option value="">全部地区</option>
    <option value="north">北区</option>
    <option value="south">南区</option>
  </select>

  <fieldset>
    <legend>订单状态（可多选）</legend>
    <label><input type="checkbox" name="status" value="open"> 处理中</label>
    <label><input type="checkbox" name="status" value="closed"> 已完成</label>
  </fieldset>

  <button type="submit">筛选报表</button>
</form>
~~~

下方结果表示月份“2026-10”、全部地区且不限制状态，对应查询 `/reports?month=2026-10&region=`。地区的空值仍会提交为 `region=`；不勾任何状态时则没有 `status` 键。月份“2026-10”、地区“北区”并勾选两种状态时，浏览器按表单字段顺序构造另一条查询；同名复选框产生重复键。

~~~text
/reports?month=2026-10&region=
/reports?month=2026-10&region=north&status=open&status=closed
/reports?month=2026-10&region=&status=open    （全部地区、只选处理中）
/reports?month=2026-10&region=north           （未选状态）
~~~

<code>input</code> 的类型决定控件语义、输入方式和可用的原生约束。<code>type="password"</code> 只遮住屏幕显示，不会加密传输或替代安全存储；文件选择器的 <code>accept</code> 只提示可选类型，服务端仍须校验收到的文件。<code>checked</code> 和 <code>selected</code> 标记初始选择；用户操作后的当前状态才决定提交数据。<code>select multiple</code> 也能让一个字段提交多组选项值，序列化结果会出现重复键。单选组用相同 <code>name</code> 保证只能选一个值；复选框允许同名字段提交多个已选值。若地区变化会改变下一级门店选项，更新选项时也要清除不再有效的旧门店值，并在选项不可用时明确告知用户；这属于交互状态管理，单靠 CSS 不会级联更新数据。

使用 <code>fieldset</code> 和 <code>legend</code> 把共享问题的一组控件归在一起。表单内的 <code>button</code> 默认可能提交表单，因此给按钮显式写 <code>type</code>：<code>submit</code> 提交，<code>reset</code> 恢复默认值，<code>button</code> 用作其他动作。页面导航用有真实 <code>href</code> 的链接；重置、筛选等动作使用按钮，<code>href="#"</code> 不是中性的占位符。

## 让报表结果保持数据表语义

当列和行本身有意义时，用表格标记数据，不要用 Grid 伪造表格语义。用 <code>caption</code> 说明表格内容，用 <code>th scope="col"</code> 标记列标题；行标题则按数据关系使用 <code>scope="row"</code>。无序条目用 <code>ul</code>，有序步骤用 <code>ol</code>，术语与解释用 <code>dl</code>/<code>dt</code>/<code>dd</code>；不应用连续空格或非断行空格排版。

~~~html
<table>
  <caption>2026 年 10 月订单结果</caption>
  <thead>
    <tr>
      <th scope="col">订单号</th>
      <th scope="col">地区</th>
      <th scope="col">状态</th>
    </tr>
  </thead>
  <tbody>
    <tr><th scope="row">A-1042</th><td>北区</td><td>处理中</td></tr>
    <tr><th scope="row">A-1043</th><td>南区</td><td>已完成</td></tr>
  </tbody>
</table>
~~~

表格中的 <code>rowspan</code> 或 <code>colspan</code> 会占据后续单元格位置；例如三列表中，上行一个 <code>rowspan="2"</code> 已占下行第一列，下行只再写两个单元格。窄屏宽表可以放入局部横向滚动容器，避免页面整体横向溢出，详见[固定与流动内容的布局选择](./flex-and-grid-layout.md)。

## 键盘、焦点与校验错误

原生控件提供用户熟悉的键盘操作和约束验证。标签、说明和错误文案要靠真实关系连接，而不是只靠颜色、图标或位置表达状态。Tab 顺序跟随有意义的文档顺序；<code>:focus-visible</code> 或 <code>:focus</code> 样式应保留可辨认的焦点轮廓，不要为了视觉整齐移除它。

这是报表页内另一个保存通知设置的表单，与上面的 GET 筛选表单分开。浏览器原生约束可以阻止空邮箱提交并触发 `invalid` 事件，但不会替作者改写隐藏的错误段落或设置 `aria-invalid`。若应用接管反馈，可在该字段的 `invalid` 事件处理中写入错误文本、移除 `hidden` 并设 `aria-invalid="true"`；输入改正后清除错误状态。以下表格演算的正是应用处理后的状态。

~~~html
<form action="/notification-settings" method="post">
  <label for="email">通知邮箱</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">用于接收筛选完成通知。</p>
  <p id="email-error" hidden></p>
  <button type="submit">保存通知设置</button>
</form>
~~~

应用必须把错误写成文本、用 <code>aria-describedby</code> 关联字段、用 <code>aria-invalid</code> 标记无效状态。原生验证阻止提交时，浏览器通常会把焦点放到无效字段；若应用接管了提交流程，则由应用负责将焦点移至第一个错误字段。辅助属性只补充语义，不会创建键盘行为或验证规则；服务端仍需检查收到的数据。

| 时刻 | 字段值 | 可见状态 | 焦点 |
| --- | --- | --- | --- |
| 初始 | 空 | 帮助说明显示，错误段落带 `hidden`，没有 `aria-invalid` | 由用户决定 |
| 提交空值，应用处理 `invalid` | 空 | 应用写入错误、移除 `hidden`、设置 `aria-invalid="true"` | 浏览器聚焦邮箱字段 |
| 修正后 | team@example.com | 输入处理清除错误、恢复 `hidden` 并移除 `aria-invalid` | 留在字段或由用户继续移动 |

默认阅读和键盘顺序跟随 HTML 源码顺序。Flex <code>order</code> 和 Grid 放置只改变视觉布局，不会同步重排键盘与非视觉阅读顺序；不要用它们修补错误的源顺序。

> [!info] HTML 字符引用与用户输入
> HTML 源码中的 <code>&amp;lt;</code> 和 <code>&amp;amp;</code> 分别表示文本 <code>&lt;</code> 和 <code>&amp;</code>；<code>&amp;nbsp;</code> 表示不换行空格，不应拿它代替 CSS 间距。字符引用在 HTML 解析时解码。它不是动态字符串安全插入的替代方案；把用户输入作为文本显示时，应使用 DOM 的文本接口，而非把拼接后的字符串当作标记解析。

> [!info]- 来源
> - 文档骨架、语言和语义：WHATWG HTML Living Standard，§3 文档结构与语义、§4.3 元数据；该规范 2026-11-05 更新：[HTML Standard](https://html.spec.whatwg.org/multipage/).
> - 表单标签、表单控件、按钮、验证与提交：WHATWG HTML Living Standard，§4.10；同上。
> - 表单标签与错误通知：W3C WAI Forms Tutorial，[Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/) 和 [User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/)，检查于 2026-11-06。
> - 数据表结构：WHATWG HTML Living Standard，§4.9 Tabular data；同上。
> - 字符引用：WHATWG HTML Living Standard，§13.5 Named character references；该部分 2026-10-07 更新：[HTML Standard: named character references](https://html.spec.whatwg.org/multipage/named-characters.html).
> - 焦点可见性与键盘：W3C WCAG 2.2，Recommendation（2024-12-12），Success Criteria 2.4.7 Focus Visible、2.4.11 Focus Not Obscured；[WCAG 2.2](https://www.w3.org/TR/WCAG22/)，检查于 2026-11-06。<code>:focus-visible</code> 的具体样式由页面设计决定。
> - 搜索摘要、标题链接、站点图标与不支持的 meta keywords：Google Search Central，[Snippets](https://developers.google.com/search/docs/appearance/snippet)、[Title links](https://developers.google.com/search/docs/appearance/title-link)、[Favicon](https://developers.google.com/search/docs/appearance/favicon-in-search) 和 [supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)，检查于 2026-11-06。搜索结果呈现由搜索引擎决定。
