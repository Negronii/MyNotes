# CSS 级联如何决定最终生效的声明？

本章以一份订单月报为例：页面要给表格数据行交替着色，并单独加粗其中一行。表格有一行表头和数据 A、数据 B、数据 C 三行。HTML（HyperText Markup Language，超文本标记语言）描述表格和行的结构；CSS（Cascading Style Sheets，层叠样式表）负责外观。同一元素的同一属性常有多条声明同时适用，cascade（层叠，也称级联）就是 CSS 决定其中哪一条胜出的规则。

浏览器的判断分三步：先用选择器确定哪些声明适用于该元素；再依次比较来源与重要性、封装上下文、元素附加样式、cascade layer（层叠层）、specificity（选择器权重）、作用域接近度和声明顺序，选出胜者；如果胜出的值是 `inherit`、`revert` 这类 CSS-wide keyword（CSS 全局关键字），最后还要按关键字取继承值、初始值或回退结果。下文按这个顺序展开，最后补充报表常用的 HTML 文本语义和文字、背景样式。

## 先确认选择器匹配到谁

层叠只在“已匹配到该元素”的声明之间比较，所以第一步是弄清每条规则选中了哪些行。下面两条规则都用结构伪类按位置选行。结构伪类只计算元素兄弟，源码里的空白文本节点不占位置，位置从 1 开始数：

~~~css
tbody > tr:nth-child(even) { background: #f4f7fb; }
tbody > tr:nth-child(even of .data-row) { font-weight: 600; }
~~~

~~~html
<table>
<tbody>
  <tr class="heading"><th>本月订单</th></tr>
  <tr class="data-row"><td>数据 A</td></tr>
  <tr class="data-row"><td>数据 B</td></tr>
  <tr class="data-row"><td>数据 C</td></tr>
</tbody>
</table>
~~~

| 行 | 所有 `tr` 中的序号 | 筛出 `.data-row` 后的序号 | `:nth-child(even)` | `:nth-child(even of .data-row)` |
| --- | ---: | ---: | --- | --- |
| 表头 | 1 | — | — | — |
| 数据 A | 2 | 1 | 命中 | — |
| 数据 B | 3 | 2 | — | 命中 |
| 数据 C | 4 | 3 | 命中 | — |

第一条规则改 A、C 的背景，第二条改 B 的字重，两条规则并没有争夺同一元素的同一属性。把 `.data-row` 放在伪类前面，如 `tr.data-row:nth-child(even)`，只要求匹配行有该类，不会改变 `:nth-child()` 对所有元素兄弟的计数范围，因此仍命中 A、C。

`:first-child`、`:last-child`、`:nth-child()` 和 `:nth-last-child()` 都按元素兄弟位置匹配；`nth-last-child()` 从末尾倒数。`:nth-child(2n+1)` 表示第 1、第 3 等位置；这里的 `n` 依次取非负整数。写成 `:nth-child(表达式 of S)` 时，先用选择器列表 `S` 筛选，再按筛选后的位置计数；例如 `:nth-last-child(-n+2 of .data-row)` 可选中数据 B、数据 C。相应的 `-of-type` 形式只在同一父元素下按元素类型计数，即匹配相同命名空间和标签名的兄弟。

选择器除了决定匹配谁，还带有一个权重，后面的层叠比较会用到它。选择器权重按 `(ID, 类/属性/伪类, 元素/伪元素)` 三列从左向右比较。上面第一条 `tbody > tr:nth-child(even)` 是 `(0, 1, 2)`：一个伪类、两个类型选择器。第二条 `tbody > tr:nth-child(even of .data-row)` 是 `(0, 2, 2)`，因为 `of S` 中最具体选择器 `.data-row` 再贡献一个类权重。`:nth-child(... of S)` 和 `:nth-last-child(... of S)` 各自先计一个伪类，再加上 `S` 中最具体选择器的权重。这个最大值按整个列表计算，与哪个分支实际匹配无关：`of .data-row, #not-in-report` 即使没有任何元素带这个 ID，也按 ID 分支计权重；不过目标行本身仍须匹配列表中的某个分支才会被选中。`:not()`、`:is()`、`:has()` 本身不额外计一个伪类，而取参数列表中最具体选择器的权重；`:where()` 本身及其参数权重为零。

选择器还能选中伪元素，为元素生成 DOM 之外的额外盒子。只要 `content` 属性的计算值不是 `none`，且盒子生成没有被 `display: none` 等方式抑制，`::before` 和 `::after` 就分别在元素实际内容的前面和后面生成盒子；它们不是新增的 DOM（Document Object Model，文档对象模型）节点。例如，可以用装饰括号包住报表中的状态：

~~~html
<span class="status">处理中</span>
~~~

~~~css
.status::before { content: "［"; }
.status::after { content: "］"; }
~~~

这里的括号只是装饰，去掉样式后“处理中”仍在文档中。清除浮动技巧（clearfix）也可用 `::after` 空伪元素生成辅助盒：

~~~css
.group::after {
  content: "";
  display: table;
  clear: both;
}
~~~

这个辅助盒参与正常流，`clear: both` 把它排到左右两侧浮动的下方，容器的自动高度因此会包住浮动元素。

不要只靠生成内容表达状态文字、说明或交互功能：用户关闭或替换样式后，这些内容可能消失，也不一定能像正文一样被选中复制。WAI（W3C Web Accessibility Initiative）曾把非装饰性生成文字列为失败技术 F87，现在这条已标记为过时，当前浏览器和辅助技术也大多能读出生成文字，所以不能断言生成文字一定对辅助技术不可见。本例仍把有意义的状态写成实际文本。`::before` 和 `::after` 也不会在 `<img>` 等被替换元素上生成。

## 按级联步骤找到胜出声明

确定匹配关系后，进入层叠比较的声明还要满足几个条件：样式表适用于当前文档（例如媒体条件成立），`@media`、`@supports` 等条件规则为真，选择器匹配目标元素，属性和值在解析阶段语法有效。不满足的声明直接被丢弃。例外是含 `var()`（自定义属性替换函数）的值：解析时浏览器还不知道替换结果，只能先让它参与层叠，到计算值阶段才发现替换结果可能不合法。两种无效的后果不同：

~~~css
.parse-invalid {
  background-color: red;
  background-color: 20px;
}

.var-invalid {
  background-color: red;
  --surface: 20px;
  background-color: var(--surface);
}
~~~

~~~html
<p class="parse-invalid">解析阶段无效</p>
<p class="var-invalid">替换后无效</p>
~~~

第一条规则中的 `20px` 在解析时就无效而被丢弃，背景仍为红色。第二条规则中的 `var(--surface)` 在解析时有效，于是赢得层叠；替换成 `20px` 后才发现它不是合法颜色，这时该属性按 `unset` 处理。`background-color` 不继承，所以结果是初始值透明，而不是回头恢复已落选的红色；如果出问题的是继承属性，结果就是父元素的值。

剩下的有效声明按以下步骤比较。每一步只比较同一元素的同一属性；某一步分出高下后，后面的步骤不再参与：

1. **来源与重要性。** 声明有三个来源：用户代理（浏览器自带的默认样式）、用户（读者自己配置的样式）和作者（网页开发者写的样式）。优先级从高到低为：过渡中的声明、用户代理 `!important`、用户 `!important`、作者 `!important`、动画声明、作者普通声明、用户普通声明、用户代理普通声明。某些宿主语言也会把 `bgcolor` 这类非 CSS 表现提示映射到作者表现提示来源，其优先级位于一般用户来源与作者来源之间；本例没有使用这种提示。`!important` 会改变优先次序，也会让后续覆盖更难维护。
2. **封装上下文。** 比较来自 Shadow DOM（影子 DOM）内外的规则时，普通声明外层优先，重要声明内层优先。
3. **元素附加样式。** 在来源、上下文和重要性相同的情况下，直接写在元素 `style` 属性（内联样式）中的声明优先于选择器匹配到的规则；它并不会越过前面的来源与重要性比较。
4. **层叠层。** 同一来源和上下文内，普通声明由层顺序较后的层优先，未分层普通声明排在所有显式层之后。重要声明的层序反转，因此显式层中的重要声明优先于未分层的重要声明。
5. **选择器权重。** 只在以上步骤持平时比较。ID 列先比；前一列一旦分出高下，后一列不能抵消。通配符 `*` 与组合符 `>`、`+`、`~` 不增加权重。
6. **作用域接近度与声明顺序。** `@scope (根选择器) { ... }` 把内部规则限定在根元素的子树中。若前面步骤（包括选择器权重）都持平，且至少一条规则位于 `@scope` 中，就比较作用域根到目标元素之间隔了几代（或几个兄弟元素），跳数少者优先；没有作用域根的规则视为无限跳。`@scope` 括号里的根选择器不计入内部规则的选择器权重。仍持平时按声明顺序决定：同一文件中后出现的胜出，被 `@import` 引入的样式表按导入语句所在位置参与排序。

下面三条规则的选择器权重都是 `(0, 1, 0)`，因为 `#monthly-report` 这个根选择器的 ID 不计入内部 `.status` 规则。从 `.status` 往上数，到 `#monthly-report` 隔两代，到 `.status-group` 隔一代，无作用域规则视为无限跳，所以 `.status-group` 作用域中的 `#555` 胜出，即使无作用域规则写在最后：

~~~html
<section id="monthly-report">
  <div class="status-group"><p class="status">处理中</p></div>
</section>
~~~

~~~css
@scope (#monthly-report) { .status { color: #8a3b00; } }
@scope (.status-group) { .status { color: #555; } }
.status { color: purple; }
~~~

再看选择器权重决定胜负的情况。下面两条作者普通样式都给同一个状态元素设置 `color`，前四步都持平。`#status` 的选择器权重 `(1, 0, 0)` 高于三个类 `(0, 3, 0)`，所以即使类规则写在后面，ID 规则仍胜出：

~~~html
<p id="status" class="report status warning">待处理</p>
~~~

~~~css
#status { color: #8a3b00; }
.report.status.warning { color: #b00020; }
~~~

## 用层次组织样式来源

上一节最后的例子说明，靠提高选择器权重来覆盖样式，会让后来的规则越写越重。层叠层把 reset、第三方组件、业务组件和工具类样式分到不同层，由层顺序而不是选择器权重决定胜负。先声明层顺序，选择器保持适度权重即可：

~~~css
@layer reset, components, utilities;

@layer reset {
  .revert-important.has-reset { color: green; }
}

@layer components {
  #layer-status { color: #8a3b00; }
  .revert-normal { color: #8a3b00; }
  .revert-important { color: revert-layer !important; }
}

@layer utilities {
  .text-muted { color: #555; }
  .revert-normal { color: revert-layer; }
  .revert-important { color: #555 !important; }
}
~~~

~~~html
<p id="layer-status" class="text-muted">状态由工具类设为灰色</p>
<p class="revert-normal">普通声明回退到组件层</p>
<p class="revert-important has-reset">重要声明回退到 reset 层</p>
<p class="revert-important">没有较低优先级作者声明时回退到用户代理来源</p>
~~~

第一个段落同时匹配 `components` 层的 ID 选择器和 `utilities` 层的单类选择器。普通声明中，层列表越靠后的层优先级越高，因此 `utilities` 的灰色胜出，即使它的选择器权重较低。未分层普通声明排在所有显式层之后；重要声明的层序反转，因此较早层的 `!important` 声明优先于较晚层及未分层的重要声明。层只在相同来源和封装上下文内排序，不能越过来源、重要性或封装上下文等更早步骤。

示例后三段演示 `revert-layer`。它不是“改用上一条规则”，而是重新计算该属性，仿佛当前层的声明，以及优先级排序中位于当前层“重要级位置”与“普通级位置”之间的所有声明，都没有为这个元素设置该属性。

- 第二段：`utilities` 层的普通声明 `revert-layer` 胜出后回滚，露出 `components` 层的棕色。
- 第三段：重要声明中较早的层优先，`components` 层的 `revert-layer !important` 胜出。回滚时，`utilities` 层的重要灰色正好位于被略去的区间，`reset` 层的普通绿色不在区间内，于是绿色胜出。
- 第四段：没有 `.has-reset`，作者来源里已无可用的值，于是继续回退到前一来源，显示用户代理的默认颜色。

## 级联之后，属性怎样继承？

> [!info] 五个常见 CSS-wide keyword
> `inherit` 明确取父元素的计算值，即使该属性通常不继承；`initial` 取属性定义的初始值；`unset` 按属性是否继承来选择，继承属性等同 `inherit`，非继承属性等同 `initial`。作者来源上的 `revert` 会去掉作者来源（包括动画来源）的该属性声明，露出用户来源结果；若没有用户样式，则露出用户代理来源。例如对 `<em>` 写 `font-style: revert`，浏览器的默认斜体可重新生效。对于本节的层叠层规则，`revert-layer` 会去掉当前层及其普通级与重要级层序位置之间的声明；若同一来源没有剩余的低优先级值，就回退到前一来源，见层叠层示例。两种回滚关键字都不等同于 `unset`。

如果某个属性在层叠后没有任何胜出声明，继承属性从父元素取得计算值，非继承属性取初始值。继承只传值，父元素选择器的权重不会“传给”子元素：

~~~html
<article id="report">
  <span class="status">处理中</span>
</article>
~~~

~~~css
#report { color: #222; font-family: system-ui, sans-serif; margin: 2rem; }
.status { color: #8a3b00; }
~~~

`span` 自己的 `color` 声明胜出，它仍从父级继承 `font-family`；父级的 `margin` 不会继承。`color`、`font-family` 和 `line-height` 是默认继承属性；`width`、`padding`、`margin`、`display`、`position` 默认不继承，具体以属性定义为准。

数字、长度和百分比行高的继承结果不同。父元素字号为 `20px` 时，`line-height: 1.5` 计算并继承为数字 `1.5`；字号为 `12px` 的子元素据此得到 `12 × 1.5 = 18px` 的行高。父元素设 `line-height: 30px` 或 `line-height: 150%` 时，两者都先计算为 `30px` 长度；子元素继承长度 `30px`，即使字号降到 `12px`，行高仍是 `30px`。

链接下划线这类文本装饰看起来像继承，其实不是。`text-decoration` 本身不继承，但祖先画的装饰线会沿盒树延伸到后代文字上；对子级 `<em>` 写 `text-decoration: none` 取消不了祖先的下划线，要改的是设置该装饰的那个元素的规则。

## 文本元素怎样表达不同含义？

前面讨论的是 CSS 怎样决定外观；外观之下，HTML 元素本身表达文档含义。在订单月报中，用 `h1`–`h6` 标记标题层级，例如页面主标题用 `h1`、月份区块标题用 `h2`；说明段落用 `p`。标题层级表达文档结构，字号和间距交给 CSS。只有换行本身有意义时才用 `br`；`hr` 表示段落级内容之间的主题转换。`strong` 表示重要性、严重程度或紧急性，`b` 只是引起注意；`em` 表示语气重读，`i` 表示另一种语调或与正文表达方式不同的内容，例如术语。`del` 和 `ins` 标记删除与插入的内容，`s` 表示内容已不再准确，`u` 可标记错别字等非文本注记，例如在“订单状太”中用它标出误写的“太”。CSS 可以改变这些元素的外观，不能替换它们表达的文档语义。

## 报表文字和背景样式怎样组合？

`font-family`（字体族）按书写顺序尝试字体，末尾应给出 `sans-serif`、`serif` 等通用字体族作为回退。`text-align`（文本对齐）控制块内各行文字的对齐方式，`text-indent`（首行缩进）设置段落首行缩进；它们只改外观，不代替文本语义。只想调整字体的某一方面时，用对应的长属性，例如 `font-weight`（字重），以免顺手覆盖其他设置。

> [!info] `font` 简写会重置它的字体子属性
> `font`（字体简写）展开成一组字体长属性的声明，每个长属性仍各自参与前面讲的层叠。简写里没写出的子属性会被设为初始值，所以下例中 `.report-title` 先写的 `font-style: italic` 会被重置为 `normal`，`font-kerning: none` 会被重置为 `auto`。需要保留其他字体设置时，改用目标长属性。

~~~css
.report-title {
  font-style: italic;
  font-kerning: none;
  font: 600 1.25rem/1.3 system-ui, sans-serif;
}

.report-summary {
  font-size: 1rem;
  line-height: 1.5;
  text-indent: 1em;
}

.report-total {
  text-align: end;
  font-weight: 700;
}
~~~

`background-image`（背景图像）既可用 `url()` 指向图片，也可用 `linear-gradient()`（线性渐变）生成渐变；图像绘制在 `background-color`（背景色）上方。背景色会从图片的透明处透出来，也能在图片未加载时提供底色。报表状态仍要作为正文文字保留，不能只靠背景颜色或渐变表达。

`background-size`（背景尺寸）的 `cover` 会等比缩放并覆盖整个背景区，可能裁去图片边缘；`contain` 会等比缩放并完整放入背景区，可能留下空白。在 `background` 简写中，位置和尺寸之间用斜线分隔；简写还会把未写出的背景子属性重置为初始值。下例中的 `/assets/report-cover.jpg` 只是示例路径：

~~~css
.report-cover {
  background: center / cover no-repeat url("/assets/report-cover.jpg");
}
~~~

只想调整一个背景属性时，使用对应长属性，避免简写顺带重置其他图层设置：

~~~css
.report-status {
  color: #704000;
  background-color: #fff3d6;
  background-image: linear-gradient(180deg, rgb(255 255 255 / 35%), transparent);
}
~~~

属性选择器（如 `[data-state="warning"]`）可以把显式状态映射到样式。扁平的类选择器比层层叠加的长选择器更容易被覆盖和维护。CSS-in-JS（在 JavaScript 中生成或组织 CSS）生成的类名同样参与浏览器层叠，不会绕过上面的规则。

把首屏需要的关键 CSS 内联进 HTML，有时能省去等待样式表请求的时间，代价是首次 HTML 响应变大；如果外部样式表里仍有同样的规则，这部分内容会下载两次，且内联部分无法被单独缓存。是否划算要结合缓存、加载路径和实测判断，它与选择器匹配速度无关，参见[网页性能测量与诊断](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 标题、段落、换行、主题分隔、强调与修订文本的 HTML 语义：WHATWG HTML Living Standard，[Sections](https://html.spec.whatwg.org/multipage/sections.html)、[Grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[Text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)，更新时间 2026-11-11，检查于 2026-11-11。
> - 声明过滤、来源/重要性、层排序及 `revert` / `revert-layer` 的回滚：W3C CSS Cascading and Inheritance Level 5，§5–7.3.5，Candidate Recommendation Snapshot（2022-01-13）：[CSS Cascade Level 5](https://www.w3.org/TR/css-cascade-5/)，检查于 2026-11-12。
> - `@scope` 接近度的跳数、无作用域根的无限跳及根选择器不计入规则权重：W3C CSS Cascading and Inheritance Level 6，§2.1、§2.5.1，Exploratory Working Draft（2024-09-06；差异草案明确建议实现时以 Level 5 为参考）：[CSS Cascade Level 6](https://www.w3.org/TR/css-cascade-6/)，检查于 2026-11-12。
> - 结构伪类计数、`of S` 筛选和选择器权重计算：W3C Selectors Level 4，§13.3–13.4、§15，Working Draft（2026-01-22）：[Selectors Level 4](https://www.w3.org/TR/selectors-4/)，检查于 2026-11-11。
> - `::before`、`::after` 生成位置和替换元素限制：W3C CSS Pseudo-Elements Level 4，§4.1，Working Draft（2025-06-27）：[CSS Pseudo-Elements](https://www.w3.org/TR/css-pseudo-4/#generated-content)，检查于 2026-11-12。
> - `content: normal` 在 `::before`、`::after` 上计算为 `none`：W3C CSS Generated Content Level 3，§1，Working Draft（2025-12-04）：[CSS Generated Content](https://www.w3.org/TR/css-content-3/)，检查于 2026-11-12。
> - `display: none` 不生成盒子：W3C CSS Display Level 3，§2.5，Candidate Recommendation Draft（2026-06-05）：[CSS Display](https://www.w3.org/TR/css-display-3/#box-generation)，检查于 2026-11-12。
> - `clear: both` 将正常流块级盒推到先前的双侧浮动下方，正常流子盒也计入父级自动高度：W3C CSS 2.2，§9.5.2、§10.6.3，First Public Working Draft（2016-04-12）：[CSS 2.2 floats](https://www.w3.org/TR/CSS22/visuren.html#flow-control)、[block auto height](https://www.w3.org/TR/CSS22/visudet.html#normal-block)，检查于 2026-11-12。
> - `var()` 替换后的值在计算值阶段无效时，不会恢复先前声明：W3C CSS Custom Properties for Cascading Variables Level 1，§3.1，Candidate Recommendation Snapshot（2022-06-16）：[CSS Variables](https://www.w3.org/TR/css-variables-1/#invalid-variables)，检查于 2026-11-12。
> - 将 CSS 生成内容用于装饰的适用条件：W3C WAI WCAG 2.2 Technique C9（2026-01-12 更新）；关于非装饰性生成文字的旧失败技术 F87 已标记过时，且指出当前支持状况不应一概视为失败：[C9](https://www.w3.org/WAI/WCAG22/Techniques/css/C9)、[F87（Obsolete）](https://www.w3.org/WAI/WCAG22/Techniques/failures/F87)，检查于 2026-11-11。
> - 状态信息不能只用颜色表达：W3C Web Content Accessibility Guidelines 2.2，Success Criterion 1.4.1，Recommendation（2024-12-12）：[Use of Color](https://www.w3.org/TR/WCAG22/#use-of-color)，检查于 2026-11-11。
> - 文本装饰的盒树传播：W3C CSS Text Decoration Level 3，§2，Candidate Recommendation Draft（2022-05-05）：[CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/#line-decoration)，检查于 2026-11-11。
> - 字体属性、字体族回退、`font` 子属性重置：W3C CSS Fonts Level 4，§2.7、§3，Working Draft（2026-11-04）：[CSS Fonts](https://www.w3.org/TR/css-fonts-4/)，检查于 2026-11-12。
> - 数字、长度和百分比 `line-height` 的计算及继承：W3C CSS Inline Layout Level 3，§5.1，Working Draft（2024-12-18）：[CSS Inline Layout](https://www.w3.org/TR/css-inline-3/)，检查于 2026-11-12。
> - 背景层、背景色、图像、`background` 简写与尺寸：W3C CSS Backgrounds and Borders Level 3，§2.1–2.3、§2.9–2.10，Candidate Recommendation Draft（2024-03-11）：[CSS Backgrounds and Borders](https://www.w3.org/TR/css-backgrounds-3/)，检查于 2026-11-12。
> - 内联关键 CSS 的适用情况与缓存、HTML 体积权衡：web.dev [Optimize resource loading](https://web.dev/learn/performance/optimize-resource-loading/)，Inline critical CSS，2023-11-01 更新，检查于 2026-11-11。
