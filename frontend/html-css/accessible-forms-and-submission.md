# 表单控件怎样命名、提交和校验，才对所有人可用？

表单把用户的选择交给服务器。它对所有人可用，要过四关：每个控件有能被读出的名字；不用鼠标也能操作；浏览器把选择正确地编码进请求；出错时，每个用户都能发现错在哪、改完后知道已经改对。

本章沿用主线一的报表页，并接着[上一章](./semantic-structure-and-accessibility.md)的骨架和结果表格。我们在表格上方加一张筛选表单，新增字段 `from`（起始月份）、`region`（地区）和 `status`（订单状态：`open` 处理中、`closed` 已完成），再加一张只有 `email` 字段的通知邮箱表单。控件文字沿用页面的英文界面。服务器怎样解释这些字段是本章合成的应用约定，下文在用到时说明。

## 每个控件先要有名字

屏幕阅读器停在一个控件上时，先读它的 accessible name (可访问名称)。对表单字段，这个名字通常来自与它关联的可见 `label`；对按钮，来自按钮自身的文字。

~~~html
<form action="/reports/42" method="get">
  <input type="hidden" name="sort" value="recent">

  <label for="from">From month</label>
  <input id="from" name="from" type="month" value="2026-04" required>

  <label for="region">Region</label>
  <select id="region" name="region">
    <option value="" selected>All regions</option>
    <option value="north">North</option>
    <option value="south">South</option>
  </select>

  <fieldset>
    <legend>Order status</legend>
    <label><input type="checkbox" name="status" value="open"> Open</label>
    <label><input type="checkbox" name="status" value="closed"> Closed</label>
  </fieldset>

  <button type="submit">Filter reports</button>
</form>
~~~

- **关联标签的两种写法都有效**：用 `for` 指向控件的 `id`（`From month`、`Region`），或把控件直接包在 `label` 里（两个复选框）。关联后，点击标签文字也会作用到控件，例如点 `Open` 这个词就能勾选复选框，点击区域因此变大。
- **`fieldset` 与 `legend` 给一组控件起组名**：两个复选框回答的是同一个问题 `Order status`。辅助技术可能按平台习惯在每个选项前重复读组名，所以组名要短；各选项自己的标签仍要能单独辨认。
- **按钮用文字命名**：`Filter reports` 既是可见文字，也是可访问名称。

### placeholder 只是样例，不是名字

有人想用 `placeholder` (占位提示)省掉标签，但它们作用不同。`placeholder` 只在控件没有值时显示一个简短样例，例如给后文的通知邮箱字段加 `placeholder="name@example.com"`。它不是字段值：提交时不会代替用户输入，也不能满足 `required`。用户一开始输入它就消失，所以 `Notification email` 这个可见标签和持续显示的帮助文字仍要保留。

CSS 的 `::placeholder` 伪元素只选中提示文字本身：

~~~css
#email::placeholder {
  color: #595959;
  opacity: 1;
}
~~~

这条规则在白色背景上把样例显示成灰色，实际主题仍要检查文字与背景的对比度。它不改输入文字的颜色，也不改字段值。要选中“正在显示占位提示的整个控件”，用 `:placeholder-shown` 伪类，二者作用对象不同。

## 原生控件自带键盘操作

用原生控件，键盘操作和角色、状态的报告都由浏览器提供，不用自己写。跟一位只用键盘的用户走一遍上面的筛选表单：

1. 按 Tab，焦点按源码顺序依次经过起始月份、地区、两个复选框和提交按钮。隐藏字段 `sort` 不可见也不可聚焦。焦点为什么跟随源码顺序，见[焦点顺序跟随源码](./semantic-structure-and-accessibility.md#焦点顺序跟随源码)。
2. 起始月份保留预设值 `2026-04`。月份控件内部可能有年、月等多个键盘停靠点；用户继续按 Tab 离开它。
3. 到达“地区”。它是单选的 `<select>`，名称来自关联标签 `Region`，当前选项是 `All regions`。按 HTML Accessibility API Mappings (HTML 到无障碍 API 的映射规范)，未设 `multiple`、显示大小为 1 的 `<select>` 映射为 `combobox` (组合框) 角色。用户不改，按 Tab 离开。
4. 到达 `Open` 复选框。它以原生 checkbox 角色报告名称 `Open` 和“未选中”状态；按空格键切换为已选中。再按 Tab 到 `Closed`，同样按空格键选中。
5. 按 Tab 到 `Filter reports` 按钮，按空格键或 Enter 激活，提交表单。

最终选择是：2026 年 4 月起、全部地区、处理中和已完成两种状态。各浏览器和屏幕阅读器的播报措辞不一定相同，但名称、角色、状态和键盘操作都由原生控件提供。

## 浏览器怎样把选择变成 GET 查询串

用户按下提交按钮后，浏览器先构造一份 entry list (表单项列表)，再把它编码成查询串。规则如下：

1. **按控件在文档中的顺序（tree order）逐个收集 `name=value` 项。**
2. **跳过不该提交的控件**：没有 `name` 的、被禁用的、未选中的复选框和单选按钮。按钮只有触发这次提交的那一个才可能产生项，而且它要有 `name`；本例按钮没有 `name`，不产生项。
3. **提交的是控件的当前状态，不是 HTML 属性。** `checked`、`selected`、`value` 属性只设定初始状态；用户操作之后，浏览器读控件此刻的选中状态和值。
4. **同名控件各自产生一项**，顺序按它们在文档中的位置，而不是用户点击的先后。先勾 `Closed` 再勾 `Open`，仍是 `status=open&status=closed`。
5. **按 `application/x-www-form-urlencoded` 规则编码**：空格变成 `+`；ASCII 字母、数字和 `*`、`-`、`.`、`_` 原样保留；其余字符（包括 `&`、`+`、`=` 和中文）按编码后的字节写成 `%XX`，编码通常是 UTF-8。注意“都是 ASCII 字符”不等于无需编码：`a&b` 编码为 `a%26b`，`a+b` 编码为 `a%2Bb`。
6. **用编码结果替换 `action` URL 的整个查询部分**，再导航到这个 URL。`action` 里原有的查询串不会保留。

把这些规则用在刚才的选择上：

| 控件（文档顺序） | 是否产生项 | 项 |
| --- | --- | --- |
| 隐藏字段 `sort` | 是 | `sort=recent` |
| 起始月份 | 是 | `from=2026-04` |
| 地区（选中 `All regions`，值为空串） | 是，值为空 | `region=` |
| `Open`（已选中） | 是 | `status=open` |
| `Closed`（已选中） | 是 | `status=closed` |
| 提交按钮（无 `name`） | 否 | — |

浏览器导航到：

~~~text
/reports/42?sort=recent&from=2026-04&region=&status=open&status=closed
~~~

第 6 条解释了为什么表单里要有隐藏字段 `sort`：当前页面地址是 `/reports/42?sort=recent#summary`，如果不把排序作为字段提交，提交后的 URL 就不再有 `sort`，排序会退回服务器默认值。反过来，用户先点了“最早优先”、脚本把地址改成 `sort=oldest` 时，脚本也要同步更新这个隐藏字段，否则表单会提交旧的排序。URL 里每段该放什么、怎样校验和规范化，见[地址变了，浏览器什么时候加载新文档？](../browser/navigation-history-and-url-state.md)。

GET 适合这类不敏感的筛选：结果 URL 可以收藏、分享和后退。查询串会出现在地址栏、浏览历史和服务器日志里，密码、令牌等敏感值不能用 GET 提交。

### 月份字段的值长什么样

浏览器支持 `type="month"` 时，非空值是 `2026-04` 这样的年月字符串：至少四位且大于零的年份，一个连字符，再加 `01`–`12` 的两位月份。不支持这一类型的浏览器会把它当普通文本框，用户可以输入任意字符串，也没有月份选择器和格式校验。`required` 只能阻止正常途径下的空值提交；有人直接改 URL 或绕过浏览器发请求时，它不起作用。

## 查询串的含义由应用约定

HTML 和 URL 只规定怎样把选择编码成 `name=value`，不规定 `region=` 是“全部地区”还是“地区为空”，也不规定两个 `status` 是“都要满足”还是“满足其一”。这些含义由应用自己约定，服务器必须按约定校验收到的每个值。

本章的合成报表应用这样约定：

- `from` 必须是有效年月。缺失、空或格式无效时返回字段错误，要求重新选择，不静默改用别的月份。报表只列出不早于 `from` 的月份；有效但没有订单的月份显示空结果和说明。
- `region=` 和省略 `region` 都表示全部地区；`north`、`south` 分别表示北区、南区；其他非空值返回错误。
- 省略全部 `status` 表示不限制状态；多个 `status` 组成列表，订单命中其中任一个就计入；未知状态值返回错误。

| 用户选择 | GET 请求 | 服务器按约定怎样筛选 |
| --- | --- | --- |
| 4 月起、全部地区、未选状态 | `/reports/42?sort=recent&from=2026-04&region=` | May、April 两行，统计所有地区和状态的订单 |
| 4 月起、全部地区、处理中与已完成 | `/reports/42?sort=recent&from=2026-04&region=&status=open&status=closed` | 同样两行，只统计这两种状态的订单；就是上面键盘用户发出的请求 |
| 4 月起、北区、只选处理中 | `/reports/42?sort=recent&from=2026-04&region=north&status=open` | 两行，只统计北区处理中的订单 |
| 5 月起、北区、未选状态 | `/reports/42?sort=recent&from=2026-05&region=north` | 只剩 May 一行，统计北区全部状态的订单 |

第一行和第二行的区别在于有没有 `status`。在本应用里，两种状态全选与不选结果相同，但这是约定的巧合：若以后新增“已取消”状态，不选仍是“不限”，全选旧的两项就会把“已取消”排除在外。

## 常被误解的控件行为

- **`type="password"` 只遮住屏幕显示**，不会加密传输，也不替代服务端的安全存储。
- **文件选择器的 `accept` 只是类型提示**，用户仍可能选到别的文件，服务器必须校验收到的内容。
- **一个字段提交多个值有两种写法**：多个同名复选框，或 `<select multiple>`。同名的单选按钮则构成一组，组内只能选中一个。
- **表单里不写 `type` 的 `<button>` 默认是提交按钮。** 表单里放一个“清空筛选”（`Clear filters`）按钮却忘了写类型，点它就会提交表单。所以每个按钮都写明 `type="submit"`、`type="reset"` 或 `type="button"`。要跳转页面则用带真实 `href` 的链接，见[图片和音视频该怎样写语义、定地址？](../browser/images-and-media-loading.md)中 `<a>` 与 `<button>` 的区分。
- **级联选项要清掉失效的旧值。** 假设地区下面还有一级门店，用户先选北区的某家门店，再把地区改成南区：应用更新门店选项时，必须同时清除已经不属于南区的旧门店值，否则旧值会被一并提交。选项暂时加载不出来时，要明确告诉用户，而不是留一个空下拉框。

## 自定义校验错误：一份完整配方

报表页还有一张独立的通知邮箱表单，用它演示怎样自己显示校验错误。

原生约束 `required` 和 `type="email"` 会阻止空邮箱和格式错误的邮箱提交。每次提交尝试中，浏览器对不满足约束的字段派发可取消的 `invalid` 事件。应用取消它，就能用自己的错误文字替换浏览器的原生提示气泡；表单仍会因约束不满足而不提交。但这样一来，让用户发现错误、更新字段状态就成了应用的责任。

~~~html
<form action="/notification-settings" method="post">
  <label for="email">Notification email</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">We email you when a filtered report is ready.</p>
  <p id="email-error" hidden></p>
  <button type="submit">Save notification settings</button>
</form>
~~~

这段标记做了两件事：

- **`aria-describedby` 把帮助文字和错误文字都关联为字段的描述。** 焦点进入字段时，辅助技术先读名称 `Notification email`，再读这两段描述。
- **错误段落默认 `hidden` 且为空。** 按名称与描述的计算规则，被 `aria-describedby` 直接引用的节点即使隐藏，其文字也会计入描述。所以隐藏错误时必须同时清空文字，否则修正后的字段仍可能被读出旧错误。

脚本要在表单节点存在之后运行：放在表单标记之后，或作为外部脚本加 `defer`。脚本调度的细节见[打开一个 URL 后，页面怎样变得可见又可交互？](../browser/from-url-to-interactive-page.md)。

~~~js
const email = document.querySelector("#email");
const error = document.querySelector("#email-error");
let hasShownError = false;

function updateEmailError() {
  const message = email.validity.valueMissing
    ? "Enter your notification email."
    : email.validity.typeMismatch
      ? "Enter a valid email address."
      : email.validity.valid
        ? ""
        : email.validationMessage || "Check your notification email.";

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

配方的五个部分各管一件事：

1. **`invalid` 事件 + `preventDefault()`**：接管错误显示，同时保留浏览器的阻止提交。
2. **`validity` 区分错因**：`valueMissing` 是空值，`typeMismatch` 是格式不对；两者都不是时回退到浏览器的 `validationMessage`。
3. **`aria-invalid="true"`**：让辅助技术报告字段处于错误状态；修正后移除。
4. **把焦点移回字段**：动态插入的错误文字不保证每种辅助技术都会立刻播报，焦点回到字段后，用户会听到名称和包括错误在内的描述。表单有多个字段时，只把焦点移到第一个无效字段，或移到列出全部错误的摘要上。
5. **首次提交后才实时重验**：用户还没提交时不打扰；一旦显示过错误，每次输入都重新判断，修正后立刻撤下错误。

跟着一次输入看状态怎样变化：

| 时刻 | 字段值 | 可见与程序化状态 | 焦点 |
| --- | --- | --- | --- |
| 初始 | 空 | 帮助文字显示；错误段落为空且 `hidden`；没有 `aria-invalid` | 由用户决定 |
| 提交空值后 | 空 | `valueMissing` 为真：显示 `Enter your notification email.`，移除 `hidden`，设置 `aria-invalid="true"` | 移到邮箱字段 |
| 改成 `person@` | `person@` | `typeMismatch` 为真：错误更新为 `Enter a valid email address.`，保留 `aria-invalid="true"` | 留在字段 |
| 改成 `team@example.com` | `team@example.com` | `validity.valid` 为真：清空错误文字，恢复 `hidden`，移除 `aria-invalid` | 留在字段，可继续 Tab |

修正后用户再次提交，字段满足约束，表单按默认行为 POST 到服务器。服务器仍要重新校验：客户端校验只是方便用户，任何人都能绕过它直接发请求。

## 表单可用之后，下一步看样式怎样生效

到这里，报表页的筛选表单有了可读的名字和原生键盘操作；提交时，浏览器按固定规则把选择编码成 `/reports/42?sort=recent&from=2026-04&region=&status=open&status=closed`，服务器按应用约定解释它；通知邮箱表单出错时，每个用户都能看到或听到错误，也能确认已经改对。

这些控件、按钮和表格的外观由许多条 CSS 规则共同决定，同一属性常有几条声明同时适用。下一章回答：它们冲突时谁赢，没有声明时值又从哪来？见[多条 CSS 声明冲突时谁赢？](./css-cascade-and-inheritance.md)。

> [!info]- 来源
> - 表单标签、分组、输入类型、按钮默认类型、当前控件状态、月份字符串：WHATWG HTML Living Standard §4.10，[Forms](https://html.spec.whatwg.org/multipage/forms.html)、[The input element](https://html.spec.whatwg.org/multipage/input.html)、[Months](https://html.spec.whatwg.org/multipage/common-microsyntaxes.html#months)，更新时间 2026-11-11，检查于 2026-11-11。
> - placeholder 与标签的边界：[WHATWG HTML — placeholder](https://html.spec.whatwg.org/multipage/input.html#the-placeholder-attribute)；`::placeholder` 与 `:placeholder-shown`：[CSS Pseudo-Elements Level 4 — placeholder](https://www.w3.org/TR/css-pseudo-4/#placeholder-pseudo)、[Selectors Level 4 — placeholder-shown](https://www.w3.org/TR/selectors/#placeholder)，检查于 2026-11-13。
> - 单选 `<select>` 映射为 combobox：W3C HTML Accessibility API Mappings 1.0 §3.5.116，Working Draft（2026-10-12），[HTML AAM](https://www.w3.org/TR/2026/WD-html-aam-1.0-20261012/)，检查于 2026-11-11。
> - 复选框空格键、按钮空格键与 Enter：WAI-ARIA Authoring Practices Guide，[Checkbox keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/#keyboardinteraction)、[Button keyboard interaction](https://www.w3.org/WAI/ARIA/apg/patterns/button/#keyboardinteraction)，检查于 2026-11-11。
> - 表单项按 tree order 收集、跳过规则（禁用、非提交者按钮、未选中复选框与单选）、重复名称：WHATWG HTML Living Standard §4.10.22.4，[Constructing the entry list](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-form-data-set)，检查于 2026-11-26。
> - GET 提交用编码结果替换 action URL 的查询部分（Mutate action URL）：WHATWG HTML Living Standard §4.10.22.3，[Form submission algorithm](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-algorithm)，检查于 2026-11-26。
> - URL 表单编码（空格变 `+`、保留字符百分号编码）：WHATWG URL Standard，[application/x-www-form-urlencoded serializer](https://url.spec.whatwg.org/#concept-urlencoded-serializer)，检查于 2026-11-11。
> - 约束验证、可取消的 `invalid` 事件、`validity`，以及服务器不能依赖客户端校验：WHATWG HTML Living Standard §4.10.21，[Constraints](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constraints)（含 §4.10.21.4 Security），检查于 2026-11-26。
> - 标签、分组、错误通知与提交后的错误处理：W3C WAI Forms Tutorial，[Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/)、[Grouping Controls](https://www.w3.org/WAI/tutorials/forms/grouping/)、[User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/#after-submit)，检查于 2026-11-11。
> - 被 `aria-describedby` 直接引用的隐藏节点仍计入描述：W3C Accessible Name and Description Computation 1.2 §4.3.2 步骤 2A（Hidden Not Referenced），Working Draft（2026-11-04），[computation steps](https://www.w3.org/TR/accname-1.2/#computation-steps)，检查于 2026-11-26。
