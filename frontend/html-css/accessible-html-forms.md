# 语义化 HTML 表单如何支持键盘与辅助技术用户？

沿用一张合成的 2026 年 10 月订单月报：用户用键盘选择月份、地区和订单状态，提交筛选后查看订单号、地区与状态。HTML（HyperText Markup Language，超文本标记语言）标记决定控件的名称、角色和值；浏览器把当前选择序列化为 GET 请求；报表应用校验这些查询值、按约定筛选订单，再返回有标题关系的数据表。本例用 CSS（Cascading Style Sheets，层叠样式表）安排视觉布局，控件语义与原生操作由 HTML 提供。

## 先建立有语言和视口的文档

文档骨架让浏览器正确解释页面，并让辅助技术更容易定位主要内容。`<!doctype html>` 选择标准模式；根元素的 `lang` 声明主要语言；文件本身也须使用 UTF-8 编码，字符集声明不会转换错误编码的字节。`meta name="viewport"` 这个 viewport（视口）声明让窄屏布局视口的宽度与设备宽度相符，但它本身不会把固定宽度布局变成响应式布局。

~~~html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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

让标题层级表达页面结构，用 `main`、`nav` 等 landmark（地标区域）标记主要区域。`id` 在一份文档中应唯一，既可关联标签，也可用于片段导航；`class` 可把多个元素归为同一组样式。

> [!info]- 页面元数据与内容模型
> `title` 命名浏览器标签页。`meta name="description"` 可提供搜索摘要，但搜索引擎可能改从正文生成摘要；`link rel="icon"` 提供站点图标，搜索结果是否展示图标仍由搜索引擎决定。Google Search 不使用 `meta name="keywords"` 作为排名信号。`div` 和 `span` 适合没有更具体语义的布局容器；不要因默认字号或块级显示来选择元素，因为 CSS 可以改变显示方式，却不改变元素语义。HTML 内容模型仍决定元素能否嵌套：例如，段落只接受 phrasing content（短语内容），把 `div` 设成 inline 样式也不会使它成为段落可接受的内容。

## 让控件名称、提交值和动作明确

每个字段都要有可见且程序化关联的 `label`（标签）；按钮可用自身文字命名。显式 `for`/`id` 关联能为控件提供名称，标签也扩大了可点击区域，例如点击复选框的标签可切换选中状态；把输入控件放在 `label` 内也是有效关联方式。`fieldset` 与 `legend` 把同一问题的控件组成有名称的一组。下面的 GET 表单适合非敏感筛选值，因为查询可以出现在 URL（统一资源定位符）中并被收藏或分享；敏感值不应放入 URL。

~~~html
<form action="/reports" method="get">
  <label for="month">月份</label>
  <input id="month" name="month" type="month" value="2026-10" required>

  <label for="region">地区</label>
  <select id="region" name="region">
    <option value="" selected>全部地区</option>
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

组名“订单状态（可多选）”说明两项复选框回答的是同一个问题；各选项仍要能单独辨认。辅助技术可能按平台习惯在选项前重复读出组名，所以组名保持简短。

在常见浏览器的顺序键盘导航中，用户按 Tab 会依照文档顺序到达月份、地区、两项状态和提交按钮。本例保留预设月份 `2026-10`；月控件可能包含多个键盘停靠位置，用户继续 Tab 到“地区”；这是一个单选 `<select>`，其可访问名称来自关联标签“地区”，当前选项是“全部地区”。在 HTML Accessibility API Mappings 的映射中，这种未设 `multiple`、默认大小为 1 的下拉选择控件对应 `combobox`（组合框）角色；浏览器和辅助技术的具体显示与读法可能不同。继续按 Tab 到“处理中”复选框，它以原生 checkbox（复选框）角色和标签“处理中”提供名称与选中状态；按空格键（Space）把状态从未选中切换为已选中。按 Tab 到“已完成”，再按空格键选中它。最后 Tab 到名称为“筛选报表”的按钮，按空格键或 Enter 激活。这个键盘路径最终选择 2026 年 10 月、全部地区及两种状态；本例不承诺所有平台逐字相同的播报内容。

提交后，浏览器按表单中的元素顺序构造 `name=value` 项。在本例中，没有 `name` 或被禁用的控件不产生项目；未选中的复选框和单选框也不提交；本例没有 `name` 的提交按钮不会多出一项。`checked` 和 `selected` 属性建立初始选中状态；用户操作后，提交采用控件当前的选中状态，而不是原始属性值。同名的已选复选框会分别产生项目，而且次序按文档中的控件顺序确定，不按用户点击顺序确定。浏览器按表单 URL 编码规则将项目写进 GET 查询串。本例的名称和值只包含字母、数字或连字符，所以在结果中不需转义；“都是 ASCII”本身不能推出无需编码，例如 `&`、`+` 和空格仍需要编码处理。

`type="month"` 支持时，非空值以类似 `2026-10` 的年月字符串表示：年份为至少四位且大于零的数字，后接连字符及 `01`–`12` 的两位月份。不支持该输入类型的浏览器会把它按文本输入处理，仍可输入任意字符串；它不再保证提供月份选择器或月份格式校验。`required` 可阻止常规提交空值，但服务器仍须校验真实收到的值。

| 用户选择 | GET 请求路径与查询参数 | 合成服务器按本页约定进行的筛选 |
| --- | --- | --- |
| 2026 年 10 月、全部地区、不限制状态 | `/reports?month=2026-10&region=` | 返回当月所有地区和状态的订单 |
| 2026 年 10 月、全部地区、处理中与已完成 | `/reports?month=2026-10&region=&status=open&status=closed` | 匹配任一所选状态；这是下方结果表对应的请求 |
| 2026 年 10 月、北区、只选处理中 | `/reports?month=2026-10&region=north&status=open` | 仅匹配北区且处于处理中的订单 |
| 2026 年 10 月、北区、未选状态 | `/reports?month=2026-10&region=north` | 仅匹配北区，不限制状态 |

这些业务含义由合成报表应用定义，不是 HTML 或 URL 自动带来的规则：`month` 必须是一个有效的年月；缺失、空或格式无效时，服务器返回字段错误并要求重新选月，不静默改用其他月份。有效但没有订单的月份返回空结果和说明。`region=` 或省略 `region` 都表示全部地区；`north`、`south` 分别表示北区、南区，其他非空值返回错误。省略全部 `status` 表示不限制状态；多个 `status` 值组成一个列表，命中其中任一值即可；未知状态值返回错误。

结果表明确对应第二行请求 `/reports?month=2026-10&region=&status=open&status=closed`，因此可同时显示来自北区的处理中订单 `A-1042` 与来自南区的已完成订单 `A-1043`。浏览器负责提交查询值；应用负责按上面的契约筛选并生成结果。

> [!info]- 相邻表单控件的边界
> `type="password"` 只遮住屏幕显示，不会加密传输或替代安全存储；文件选择器的 `accept` 只是可选类型提示，服务器仍须校验收到的文件。`select multiple` 也可让一个字段提交多个同名值。相同 `name` 的单选按钮保证同组只能选择一个值，复选框则可提交多个已选值。表单里的按钮默认可能提交表单，因此写明 `type="submit"`、`type="reset"` 或 `type="button"`；页面导航用有真实 `href` 的链接，`href="#"` 会导航到当前文档顶部，不能当作无动作的占位符。若地区改变会影响下一级门店选项，应用更新选项时还要清除不再有效的旧门店值；选项暂不可用时应明确告知用户。

## 让报表结果保持数据表语义

当数据的行和列本身有意义时，用表格标记，而不是用 CSS Grid（网格布局）伪造表格语义。`caption` 说明表格主题；`th scope="col"` 给出列标题，`scope="row"` 标记本行的识别值。这样读者可以把单元格 `A-1042` 关联到“订单号”，并把“处理中”关联到“状态”列与该行；具体导航方式和播报文字随浏览器与辅助技术而异。

~~~html
<table>
  <caption>2026 年 10 月订单结果（全部地区，处理中或已完成）</caption>
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

> [!info]- 其他内容结构与窄屏表格
> `rowspan` 或 `colspan` 会占据后续单元格位置；例如三列表格中，上行一个 `rowspan="2"` 已占下行第一列，下行只再写两个单元格。无序项目用 `ul`，有序步骤用 `ol`，术语与解释用 `dl`、`dt`、`dd`；不应用连续空格或非断行空格排版。窄屏宽表可以放入局部横向滚动容器，避免整个页面横向溢出，详见[固定与流动内容的布局选择](./flex-and-grid-layout.md)。

## 键盘、焦点与校验错误

Tab 顺序通常跟随有意义的 HTML 文档顺序；`:focus-visible` 或 `:focus` 样式应保留可辨认、未被完全遮挡的焦点提示。不要只用颜色、图标或位置表达错误状态。CSS Flexbox（弹性盒布局）的 `order` 和 Grid（网格布局）的放置规则可改变视觉位置，却不会改变默认顺序导航或非视觉阅读顺序；CSS Display Level 4 另定义 `reading-flow`、`reading-order` 来改变特定布局下的阅读/焦点顺序，本例没有使用它们。必须让视觉和阅读顺序一致时，应先检查源码顺序，而不是用视觉移动掩盖结构问题。

通知邮箱是同一报表页上的另一个独立表单。原生约束可以阻止空邮箱或格式错误的邮箱提交，并在字段上触发可取消的 `invalid` 事件。若应用取消浏览器的原生错误提示，表单仍因约束失败而不能提交，但应用仍需提供可发现的错误通知并更新字段状态。下面单字段示例使用 `aria-describedby` 关联帮助和错误文本，用 `aria-invalid` 标出当前错误；动态显示错误并不保证每种辅助技术都会立刻播报它，因此示例还会把焦点移回邮箱字段。

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

在表单标记之后运行以下脚本；若使用外部脚本，也可用 `defer` 确保表单节点已经创建：

~~~js
const email = document.querySelector("#email");
const error = document.querySelector("#email-error");
let hasShownError = false;

function updateEmailError() {
  const message = email.validity.valueMissing
    ? "请填写通知邮箱。"
    : email.validity.typeMismatch
      ? "请输入有效的邮箱地址。"
      : email.validity.valid
        ? ""
        : email.validationMessage || "请检查通知邮箱。";

  error.textContent = message;
  error.hidden = message === "";
  if (message) {
    email.setAttribute("aria-invalid", "true");
  } else {
    email.removeAttribute("aria-invalid");
  }
}

email.addEventListener("invalid", (event) => {
  event.preventDefault();
  hasShownError = true;
  updateEmailError();
  email.focus();
});

email.addEventListener("input", () => {
  if (!hasShownError) return;
  updateEmailError();
  if (email.validity.valid) hasShownError = false;
});
~~~

第一次提交空值时，`validity.valueMissing` 使应用显示“请填写通知邮箱。”。若用户改成 `person@`，`validity.typeMismatch` 使错误继续显示并更新为“请输入有效的邮箱地址。”，不会误显示为已恢复。输入合法的 `team@example.com` 后，错误文字清空、错误段落重新隐藏、`aria-invalid` 移除。只有当字段满足原生约束时，表单才会按默认行为提交到服务器；服务器还应再次校验输入。

| 时刻 | 字段值 | 可见与程序化状态 | 焦点 |
| --- | --- | --- | --- |
| 初始 | 空 | 帮助说明显示；错误段落为空且带 `hidden`，没有 `aria-invalid` | 由用户决定 |
| 提交空值后 | 空 | 显示“请填写通知邮箱。”、移除 `hidden`、设置 `aria-invalid="true"` | 应用移至邮箱字段 |
| 改成非空但格式错误 | `person@` | 更新为格式错误说明，保留 `aria-invalid="true"` | 留在邮箱字段 |
| 修正后 | `team@example.com` | 清空错误、恢复 `hidden` 并移除 `aria-invalid` | 留在字段，用户可继续 Tab |

> [!info]- HTML 字符引用与用户输入
> 在普通 HTML 文本上下文中，源码 `&lt;` 和 `&amp;` 分别显示为 `<` 和 `&`；`&nbsp;` 表示不换行空格，不应用来代替 CSS 间距。字符引用依所在解析状态处理：例如 `script` 中的 script data 与 `style` 中的 RAWTEXT 状态不会按普通正文那样解码字符引用。它也不是动态字符串安全插入的替代品；把用户输入作为普通文字显示时，应使用 DOM（Document Object Model，文档对象模型）的文本接口，而不是把拼接后的字符串当作标记解析。

> [!info]- 来源
> - 文档骨架、语言、地标、内容模型与文本结构：WHATWG HTML Living Standard，§3–4；更新时间 2026-11-11：[document semantics and metadata](https://html.spec.whatwg.org/multipage/semantics.html)、[grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)，检查于 2026-11-11。
> - 表单标签、分组、输入类型、当前控件状态、按钮、月字符串和约束验证：WHATWG HTML Living Standard，§4.10；更新时间 2026-11-11：[forms](https://html.spec.whatwg.org/multipage/forms.html)、[input](https://html.spec.whatwg.org/multipage/input.html)、[months](https://html.spec.whatwg.org/multipage/common-microsyntaxes.html#months)，检查于 2026-11-11。
> - 表单项按控件顺序构造、重复名称与 GET 查询序列化：WHATWG HTML Living Standard，§4.10.22，[form control infrastructure](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-form-data-set)；URL 表单编码算法：[WHATWG URL Standard](https://url.spec.whatwg.org/#concept-urlencoded-serializer)，检查于 2026-11-11。
> - 单选 `<select>` 的组合框映射：W3C HTML Accessibility API Mappings 1.0，§3.5.116，Working Draft（2026-10-12）：[HTML AAM](https://www.w3.org/TR/2026/WD-html-aam-1.0-20261012/)，检查于 2026-11-11。
> - 标签、分组、错误通知和提交后错误处理：W3C WAI Forms Tutorial，[Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/)、[Grouping Controls](https://www.w3.org/WAI/tutorials/forms/grouping/)、[User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/#after-submit)，检查于 2026-11-11。复选框 Space 与按钮 Space/Enter：WAI-ARIA Authoring Practices Guide，[Checkbox keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/#keyboardinteraction)、[Button keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/button/#keyboardinteraction)，检查于 2026-11-11。
> - 结果表格标题、行列标题关系与跨行跨列：WHATWG HTML Living Standard，§4.9；更新时间 2026-11-11：[tables](https://html.spec.whatwg.org/multipage/tables.html)，检查于 2026-11-11。
> - `aria-describedby` 隐藏内容引用与文本接口：W3C Accessible Name and Description Computation 1.2，§4.3.2，[computation steps](https://www.w3.org/TR/accname-1.2/#computation-steps)；WHATWG DOM Standard，[`Node.textContent`](https://dom.spec.whatwg.org/#dom-node-textcontent)，检查于 2026-11-11。
> - 焦点可见、不被完全遮挡、状态不只用颜色：W3C WCAG 2.2，Success Criteria 2.4.7、2.4.11、1.4.1，Recommendation（2024-12-12）：[WCAG 2.2](https://www.w3.org/TR/WCAG22/)，检查于 2026-11-11。
> - `order` 对非视觉与顺序导航的作用，以及 `reading-flow`、`reading-order`：W3C CSS Display Level 4，§3.1、§4，Working Draft（2025-11-06）：[CSS Display Level 4](https://www.w3.org/TR/css-display-4/#reading-flow)，检查于 2026-11-11。Flexbox 顺序：W3C CSS Flexible Box Layout Module Level 1，§5.4；Grid 放置：W3C CSS Grid Layout Module Level 2，§4，检查于 2026-11-11。
> - 字符引用、HTML 解析状态和动态文本内容：WHATWG HTML Living Standard，§13.2.5、§13.5；更新时间 2026-11-11：[HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html)、[named character references](https://html.spec.whatwg.org/multipage/named-characters.html)，检查于 2026-11-11。
> - Google 搜索摘要、站点图标和 meta keywords：Google Search Central，[snippets](https://developers.google.com/search/docs/appearance/snippet)、[favicon](https://developers.google.com/search/docs/appearance/favicon-in-search)、[supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)，检查于 2026-11-11。
