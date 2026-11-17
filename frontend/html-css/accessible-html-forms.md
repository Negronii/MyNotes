# 语义化 HTML 表单如何支持键盘与辅助技术用户？

本章以一张合成的 2026 年 10 月订单月报为例：用户只用键盘选择月份、地区和订单状态，提交筛选后查看订单号、地区与状态。整个过程分三步：HTML（超文本标记语言）标记决定每个控件的名称、角色和值；浏览器把当前选择序列化为 GET 请求；报表应用校验这些查询值、按约定筛选订单，再返回带行列标题的数据表。CSS（层叠样式表）只负责视觉布局，控件的语义与原生键盘操作都由 HTML 提供。

## 先建立有语言和视口的文档

表单之前，先要有一份结构正确的文档：它让浏览器正确解释页面，也让 assistive technology（辅助技术，如屏幕阅读器）更容易找到主要内容。`<!doctype html>` 让浏览器使用标准模式；根元素的 `lang` 声明页面的主要语言，屏幕阅读器据此选择发音规则；`<meta charset="utf-8">` 声明编码，但文件本身也必须真的以 UTF-8 保存，这条声明不会修正编码错误的字节。`meta name="viewport"` 这条 viewport（视口）声明让窄屏上布局视口的宽度等于设备宽度，但它本身不会把固定宽度的布局变成响应式布局。

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

用标题层级表达页面结构，用 `main`、`nav` 等 landmark（地标区域）标记主要区域，辅助技术用户可以按标题或地标直接跳转。`id` 在一份文档中应唯一，既可用来关联标签，也可作为片段导航的目标；`class` 则把多个元素归入同一组样式。

> [!info]- 页面元数据与内容模型
> `title` 命名浏览器标签页。`meta name="description"` 可提供搜索摘要，但搜索引擎可能改从正文生成摘要；`link rel="icon"` 提供站点图标，搜索结果是否展示图标仍由搜索引擎决定。Google Search 不使用 `meta name="keywords"` 作为排名信号。`div` 和 `span` 适合没有更具体语义的布局容器；不要因默认字号或块级显示来选择元素，因为 CSS 可以改变显示方式，却不改变元素语义。HTML 内容模型仍决定元素能否嵌套：例如，段落只接受 phrasing content（短语内容），把 `div` 设成 inline 样式也不会使它成为段落可接受的内容。

## 让控件名称、提交值和动作明确

每个字段都要有可见的 `label`（标签），并在代码上与控件关联，辅助技术才会把标签文字读作控件的名称；按钮则用自身文字命名。用 `for`/`id` 显式关联或把输入控件放在 `label` 内，都是有效的关联方式；标签还扩大了可点击区域，例如点击复选框的标签文字也能切换选中状态。`fieldset` 与 `legend` 把回答同一问题的控件组成一个有名称的组。下面的表单用 GET 提交，适合非敏感的筛选值：查询会出现在 URL（统一资源定位符）中，可以收藏或分享；敏感值不应放进 URL。

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

下面跟着一位键盘用户走一遍。在常见浏览器中，按 Tab 会依照文档顺序依次到达月份、地区、两项状态和提交按钮。本例保留预设月份 `2026-10`；月份控件内部可能有多个键盘停靠点（如年和月），用户继续按 Tab 离开它，到达“地区”。这是一个单选 `<select>`，其 accessible name（可访问名称）来自关联的标签“地区”，当前选项是“全部地区”。按 HTML Accessibility API Mappings（HTML 到无障碍 API 的映射规范），未设 `multiple`、显示大小为 1 的下拉选择控件对应 `combobox`（组合框）角色；不同浏览器和辅助技术的具体显示与读法可能不同。继续按 Tab 到“处理中”复选框，它以原生 checkbox（复选框）角色提供名称“处理中”和选中状态；按空格键（Space）把它从未选中切换为已选中。按 Tab 到“已完成”，再按空格键选中。最后按 Tab 到名为“筛选报表”的按钮，按空格键或 Enter 激活。这条键盘路径最终选择了 2026 年 10 月、全部地区及两种状态；各平台的播报文字不一定逐字相同。

提交时，浏览器按控件在表单中的顺序构造一组 `name=value` 项。没有 `name` 或被禁用的控件不产生项；未选中的复选框和单选按钮也不提交；本例的提交按钮没有 `name`，因此也不会多出一项。`checked` 和 `selected` 属性只设定初始选中状态；用户操作后，提交的是控件当前的选中状态，而不是原始属性值。多个同名且已选中的复选框各产生一项，次序按它们在文档中的位置，而不是用户点击的先后。浏览器再按表单 URL 编码规则把这些项写进 GET 查询串。本例的名称和值只含字母、数字或连字符，所以结果中无需转义；但“都是 ASCII 字符”并不意味着无需编码，例如 `&`、`+` 和空格仍会被编码。

浏览器支持 `type="month"` 时，非空值是 `2026-10` 这样的年月字符串：至少四位且大于零的年份，后接连字符和 `01`–`12` 的两位月份。不支持这一类型的浏览器会把它当作普通文本框，用户可以输入任意字符串，也不再有月份选择器或月份格式校验。`required` 能阻止正常途径提交空值，但服务器仍须校验实际收到的值。

| 用户选择 | GET 请求路径与查询参数 | 合成服务器按本页约定进行的筛选 |
| --- | --- | --- |
| 2026 年 10 月、全部地区、不限制状态 | `/reports?month=2026-10&region=` | 返回当月所有地区和状态的订单 |
| 2026 年 10 月、全部地区、处理中与已完成 | `/reports?month=2026-10&region=&status=open&status=closed` | 匹配任一所选状态；这是下方结果表对应的请求 |
| 2026 年 10 月、北区、只选处理中 | `/reports?month=2026-10&region=north&status=open` | 仅匹配北区且处于处理中的订单 |
| 2026 年 10 月、北区、未选状态 | `/reports?month=2026-10&region=north` | 仅匹配北区，不限制状态 |

表中第三列的筛选含义由这个合成报表应用约定，不是 HTML 或 URL 自带的规则：`month` 必须是一个有效的年月；缺失、空或格式无效时，服务器返回字段错误并要求重新选月，不静默改用其他月份。有效但没有订单的月份返回空结果和说明。`region=` 或省略 `region` 都表示全部地区；`north`、`south` 分别表示北区、南区，其他非空值返回错误。省略全部 `status` 表示不限制状态；多个 `status` 值组成一个列表，命中其中任一值即可；未知状态值返回错误。

下一节的结果表对应表中第二行的请求 `/reports?month=2026-10&region=&status=open&status=closed`，所以会同时列出北区处理中的订单 `A-1042` 和南区已完成的订单 `A-1043`。浏览器只负责提交查询值；按上述约定筛选并生成结果是应用的工作。

> [!info]- 相邻表单控件的边界
> `type="password"` 只遮住屏幕显示，不会加密传输或替代安全存储；文件选择器的 `accept` 只是可选类型提示，服务器仍须校验收到的文件。`select multiple` 也可让一个字段提交多个同名值。同名的单选按钮构成一组，组内只能选中一个值；复选框则可提交多个已选值。表单里未写 `type` 的按钮默认是提交按钮，因此应写明 `type="submit"`、`type="reset"` 或 `type="button"`；页面导航用有真实 `href` 的链接，`href="#"` 会导航到当前文档顶部，不能当作无动作的占位符。若地区改变会影响下一级门店选项，应用更新选项时还要清除不再有效的旧门店值；选项暂不可用时应明确告知用户。

### placeholder 文字为什么不能替代标签？

筛选表单的每个字段都有可见标签。有人会想用 `placeholder`（占位提示）省掉标签，但两者作用不同。`placeholder` 在控件没有值时显示一个简短样例，例如给本页下文通知邮箱表单的 `input` 加上 `placeholder="name@example.com"`。它不是字段值，提交时不会代替用户输入，也不能满足 `required`；用户一开始输入，提示就消失，因此“通知邮箱”这个可见 `label` 和持续显示的帮助文字仍要保留。

CSS 的 `::placeholder` 伪元素只选中提示文字。例如给这个邮箱字段应用以下规则，可在白色输入背景上显示灰色样例；实际主题仍需检查文字与背景对比度：

~~~css
#email::placeholder {
  color: #595959;
  opacity: 1;
}
~~~

这条规则不会设置邮箱值、改变输入文字的颜色或替代标签。若要选择“正在显示占位提示的整个控件”，对应的是 `:placeholder-shown` 伪类，二者作用对象不同。

## 让报表结果保持数据表语义

筛选提交后，服务器返回结果表。当数据的行和列本身有意义时，应使用表格标记，而不是用 CSS Grid（网格布局）摆出表格的样子——那样没有表格语义。`caption` 说明表格主题；`th scope="col"` 标出列标题，`th scope="row"` 标出标识这一行的值。这样，屏幕阅读器用户可以知道单元格 `A-1042` 属于“订单号”列，“处理中”属于“状态”列和订单 A-1042 这一行；具体的导航方式和播报文字随浏览器与辅助技术而异。

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

前面的键盘路径依赖两件事：焦点顺序合理，焦点位置看得见。Tab 顺序通常跟随 HTML 文档顺序，所以源码顺序本身要有意义；`:focus-visible` 或 `:focus` 样式应保留清晰可辨、不被完全遮挡的焦点指示。CSS Flexbox（弹性盒布局）的 `order` 和 Grid 的放置规则能改变视觉位置，却不改变默认的 Tab 顺序和非视觉阅读顺序。CSS Display Level 4 另外定义了 `reading-flow`、`reading-order`，用于在特定布局中按视觉顺序调整阅读和焦点顺序，本例没有使用。要让视觉顺序和阅读顺序一致，应先调整源码顺序，而不是用视觉移动掩盖结构问题。错误状态同样不能只靠颜色、图标或位置表达，下面的邮箱表单会同时给出文字说明。

校验错误用同一报表页上另一个独立的“通知邮箱”表单说明。原生约束（`required` 和 `type="email"`）会阻止空邮箱或格式错误的邮箱提交，并在字段上触发可取消的 `invalid` 事件。应用若取消浏览器的原生错误提示，表单仍会因约束不满足而无法提交，但应用必须自己提供用户能发现的错误说明，并更新字段状态。下面的单字段示例用 `aria-describedby` 关联帮助和错误文本，用 `aria-invalid` 标出当前错误；动态显示错误并不保证每种辅助技术都会立刻播报它，因此示例还会把焦点移回邮箱字段。

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

以下脚本须在表单标记之后运行；若作为外部脚本引入，可加 `defer`，确保执行时表单节点已经存在：

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

第一次提交空值时，`validity.valueMissing` 使应用显示“请填写通知邮箱。”。用户改成 `person@` 时，`validity.typeMismatch` 让错误继续显示，并更新为“请输入有效的邮箱地址。”，而不会误显示为已修正。输入合法的 `team@example.com` 后，错误文字清空、错误段落重新隐藏、`aria-invalid` 移除。只有当字段满足原生约束时，表单才会按默认行为提交到服务器；服务器还应再次校验输入。

| 时刻 | 字段值 | 可见与程序化状态 | 焦点 |
| --- | --- | --- | --- |
| 初始 | 空 | 帮助说明显示；错误段落为空且带 `hidden`，没有 `aria-invalid` | 由用户决定 |
| 提交空值后 | 空 | 显示“请填写通知邮箱。”、移除 `hidden`、设置 `aria-invalid="true"` | 应用移至邮箱字段 |
| 改成非空但格式错误 | `person@` | 更新为格式错误说明，保留 `aria-invalid="true"` | 留在邮箱字段 |
| 修正后 | `team@example.com` | 清空错误、恢复 `hidden` 并移除 `aria-invalid` | 留在字段，用户可继续 Tab |

> [!info]- HTML 字符引用与用户输入
> 在普通 HTML 文本上下文中，源码 `&lt;` 和 `&amp;` 分别显示为 `<` 和 `&`；`&nbsp;` 表示不换行空格，不应用来代替 CSS 间距。字符引用依所在解析状态处理：例如 `script` 中的 script data 与 `style` 中的 RAWTEXT 状态不会按普通正文那样解码字符引用。它也不是动态字符串安全插入的替代品；把用户输入作为普通文字显示时，应使用 DOM（Document Object Model，文档对象模型）的文本接口，而不是把拼接后的字符串当作标记解析。

> [!info]- 来源
> - 空值提示与标签的边界：[WHATWG HTML — placeholder](https://html.spec.whatwg.org/multipage/input.html#the-placeholder-attribute)；提示文字与控件本身的选择：[CSS Pseudo-Elements Level 4 — placeholder](https://www.w3.org/TR/css-pseudo-4/#placeholder-pseudo)、[Selectors Level 4 — placeholder-shown](https://www.w3.org/TR/selectors/#placeholder)。核对日期：2026-11-13。
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
