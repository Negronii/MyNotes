# CSS 级联如何决定最终生效的声明？

当报表中同一状态文字被多个 CSS 规则赋值时，浏览器不会简单地选“选择器最长”或“最后写的规则”。它先筛掉不适用的声明，再按来源与重要性、封装上下文、元素附加样式、级联层、选择器优先级及顺序比较。级联选出声明后，若该值使用 CSS-wide keyword（全局关键字），还要继续按对应规则解析；没有声明时，继承属性通常取父元素的计算值，非继承属性通常取初始值。

## 先确认选择器匹配到谁

报表中表头行不属于数据行；数据 A、数据 B 在所有行里分别位于第 2、第 3 个位置，在 `.data-row` 里则分别是第 1、第 2 个。

~~~css
tbody > tr:nth-child(even) { background: #f4f7fb; }
tbody > tr:nth-child(even of .data-row) { font-weight: 600; }
~~~

~~~html
<tbody>
  <tr class="heading"><th>本月订单</th></tr>
  <tr class="data-row"><td>数据 A</td></tr>
  <tr class="data-row"><td>数据 B</td></tr>
</tbody>
~~~

第一条 `:nth-child(even)` 按所有元素兄弟计数；此例的兄弟全是 `tr`，所以匹配数据 A。第二条先只取 `.data-row`，再从该集合计数，匹配数据 B。选择器先决定声明适用于谁，之后才有级联胜负。

<code>:first-child</code>、<code>:last-child</code>、<code>:nth-child()</code> 和 <code>:nth-last-child()</code> 依据兄弟位置匹配；对应的 <code>-of-type</code> 形式只依据相同标签名计数。选择器先决定声明是否适用于元素，之后才有级联胜负。

设置了可生成的 <code>content</code> 值时，<code>::before</code> 和 <code>::after</code> 会生成附属于元素的盒子，不会新增 DOM 节点。适合放装饰性图标或清除浮动的辅助样式，不要把唯一的文字说明、交互控件或重要状态只放进生成内容。<code>:not()</code>、<code>:is()</code>、<code>:has()</code> 的 specificity 取最具体参数的 specificity；<code>:where()</code> 本身及其参数贡献零。

## 按级联步骤找到胜出声明

以普通页面作者样式为例，按下面顺序比较；前一步已分出高下时，后面的步骤不再参与：

1. **来源与重要性。** 从高到低为过渡中的声明、用户代理 <code>!important</code>、用户 <code>!important</code>、作者 <code>!important</code>、动画声明、作者普通声明、用户普通声明、用户代理普通声明。不要把 <code>!important</code> 当作日常覆盖手段：它会改变这套优先次序，也让后续维护更难。
2. **封装上下文。** 规则跨越 Shadow DOM 等边界时，普通声明中外层上下文优先于内层；重要声明优先方向相反。
3. **元素附加样式。** 同一重要性下，写在元素 <code>style</code> 属性中的声明优先于由样式规则匹配到的声明。
4. **级联层。** 对普通声明，较晚声明的层优先，未分层的普通声明高于显式层；对重要声明，层顺序反转。
5. **specificity（选择器优先级）。** 只在前面步骤持平时比较。
6. **作用域接近度与源码顺序。** 使用 <code>@scope</code> 时，作用域根更近的规则在 specificity 相同后优先；最后才由源码出现顺序打破平局。

下面两条规则都在作者普通样式中。<code>#status</code> 的 specificity <code>(1, 0, 0)</code> 高于三个类 <code>(0, 3, 0)</code>，所以即使后者写在后面，前者仍胜出：

~~~html
<p id="status" class="report status warning">待处理</p>
~~~

~~~css
#status { color: #8a3b00; }
.report.status.warning { color: #b00020; }
~~~

specificity 按 <code>(ID, 类/属性/伪类, 元素/伪元素)</code> 从左向右比较。ID 列先比较；类的数量再多也不能抵消更高的 ID 列。通配符 <code>*</code> 和组合符 <code>&gt;</code>、<code>+</code>、<code>~</code> 不增加 specificity。

## 用层次组织样式来源

级联层让项目按 reset、第三方组件、业务组件和工具类组织冲突；先声明层顺序，再在各层中使用适度的选择器权重。

~~~css
@layer reset, vendor, components, utilities;

@layer components {
  .status { color: #8a3b00; }
}

@layer utilities {
  .text-muted { color: #555; }
}
~~~

普通声明中，后声明的显式层优先于前面的层，未分层样式优先于所有显式层。重要声明中的层顺序相反。层只解决同一来源和上下文中的层级关系；不能用层顺序覆盖更高优先级来源中的规则。若 ID 规则与工具类规则处于不同层，先比较层级，选择器优先级只在更早步骤持平后才比较。

## 级联之后，属性怎样继承？

> [!info] 三个常见 CSS-wide keyword
> `inherit` 明确要求取父元素计算值，即使该属性通常不继承；`initial` 取属性规范定义的初始值；`unset` 按属性本身是否继承来选择，继承属性等同 `inherit`，非继承属性等同 `initial`。

浏览器先得到元素自身的胜出声明；若没有声明，继承属性通常从父元素取计算值，非继承属性取初始值。父元素选择器的 specificity 不会“传给”子元素。

~~~html
<article id="report">
  <span class="status">处理中</span>
</article>
~~~

~~~css
#report { color: #222; font-family: system-ui, sans-serif; margin: 2rem; }
.status { color: #8a3b00; }
~~~

<code>span</code> 自己的 <code>color</code> 声明胜出，并继承父级字体；父级 <code>margin</code> 不会继承。<code>color</code>、<code>font-family</code>、<code>line-height</code>（行高）通常会继承；<code>width</code>、<code>padding</code>、<code>margin</code>、<code>display</code> 和 <code>position</code> 默认不会继承，具体仍以属性定义为准。父链接产生的下划线也可能沿后代文本绘制；对子 <code>em</code> 设置 <code>text-decoration: none</code> 不会抹掉由链接建立的装饰，应修改建立装饰的元素规则。

## 文本元素怎样表达不同含义？

文档标题用 <code>h1</code>–<code>h6</code> 建立层级，段落用 <code>p</code> 表达完整文字；只有换行本身有意义时才用 <code>br</code>，<code>hr</code> 表示段落级内容的主题转换。<code>strong</code> 表示重要性，<code>b</code> 只是引起注意；<code>em</code> 表示语气重读，<code>i</code> 表示另一种语调或技术词。<code>del</code>/<code>ins</code> 标记删除和插入的内容，<code>s</code> 表示内容已不准确，<code>u</code> 标记非文本注记。CSS 可以改变这些元素的外观，不能替换它们表达的文档语义。

## 报表文字和背景样式怎样组合？

<code>font-family</code>（字体族）按书写顺序尝试字体，末尾应给出 <code>sans-serif</code>、<code>serif</code> 等通用族作为回退。<code>text-align</code>（文本对齐）对齐块内行文字，<code>text-indent</code>（首行缩进）设置段落首行的缩进；它们不会替代文本语义。只想调整已有字体的一个方面时，使用对应长属性，例如 <code>font-weight</code>（字重），不要顺手覆盖其他设置。

> [!info] 字体简写会重置未写出的相关属性
> <code>font</code>（字体简写）可在一条声明中设置样式、字重、字号、行高和字体族等。它也会把未显式给值的相关字体长属性重置为初始值；例如新声明可能把之前的斜体恢复为 <code>normal</code>。需要保留其他字体设置时，改用目标长属性。

~~~css
.report-title {
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

> [!example] 无单位行高与长度行高的继承
> 父元素字号为 `20px` 时，`line-height: 1.5` 作为数字继承；`12px` 子元素据此得到 `12 × 1.5 = 18px` 行高。若父元素写 `line-height: 30px`，子元素继承的是 `30px` 长度，字号即使降到 `12px`，行高仍是 `30px`。

<code>background-image</code>（背景图像）既可用 <code>url()</code> 指向图片，也可用 <code>linear-gradient()</code>（线性渐变）生成渐变；两者都是图像层，绘制在 <code>background-color</code>（背景色）上方。背景色能在图片透明处露出，也能为图片加载失败提供底色。报表中的状态文字仍应直接保留在内容里，不能只靠背景颜色或渐变表达状态。

background-size（背景尺寸）用 <code>cover</code> 等比缩放并覆盖整个背景区，因此可能裁掉图片边缘；<code>contain</code> 等比缩放以完整放入背景区，因此可能留下空白。简写中的斜线分隔位置和尺寸；同时，未写出的背景子属性会重置为初始值：

~~~css
.report-cover {
  background: center / cover no-repeat url("/assets/report-cover.jpg");
}
~~~

如果只想调整某一个背景属性，使用对应长属性，避免简写顺带重置其他图层设置。

~~~css
.report-status {
  color: #704000;
  background-color: #fff3d6;
  background-image: linear-gradient(180deg, rgb(255 255 255 / 35%), transparent);
}
~~~

属性选择器例如 <code>[data-state="warning"]</code> 可把显式状态映射到样式；扁平、可维护的类选择器通常比层层增加 specificity 更容易覆盖。CSS-in-JS 生成类名也仍参与浏览器级联。

内联关键 CSS 有时能让首屏关键样式不等待外部样式表，但会增加 HTML 字节并可能与后续 CSS 重复；是否值得应看实际载入路径和测量结果，而不是把它理解成选择器加速技巧，参见[网页性能测量与诊断](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 标题、段落、换行、主题分隔、强调与修订文本的 HTML 语义：WHATWG HTML Living Standard（2026-11-05 更新），[Sections](https://html.spec.whatwg.org/multipage/sections.html)、[Grouping content](https://html.spec.whatwg.org/multipage/grouping-content.html)、[Text-level semantics](https://html.spec.whatwg.org/multipage/text-level-semantics.html)，检查于 2026-11-06。
> - 过滤、级联来源、元素附加样式、层顺序及 specificity 之前的比较：W3C CSS Cascading and Inheritance Level 5，§5–6，Candidate Recommendation Snapshot（2022-01-13，最新正式发布快照）：[CSS Cascade Level 5](https://www.w3.org/TR/css-cascade-5/)，检查于 2026-11-06。
> - <code>@scope</code> 的作用域接近度：W3C CSS Cascading and Inheritance Level 6，§2，Working Draft（2024-09-06；仍是差异草案，基础级联以 Level 5 为参考）：[CSS Cascade Level 6](https://www.w3.org/TR/css-cascade-6/)，检查于 2026-11-06。
> - specificity 与结构伪类：W3C Selectors Level 4，§13.3–13.4、§15，Working Draft（2026-01-22）：[Selectors Level 4](https://www.w3.org/TR/selectors-4/)，检查于 2026-11-06。
> - 生成伪元素：W3C CSS Pseudo-Elements Level 4，§4，Working Draft（2025-06-27）：[CSS Pseudo-Elements](https://www.w3.org/TR/css-pseudo-4/#generated-content)，检查于 2026-11-06。
> - 文本装饰传播：W3C CSS Text Decoration Level 3，§2，Candidate Recommendation Draft（2022-05-05）：[CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/#line-decoration)，检查于 2026-11-06。
> - 字体属性、字体族回退和简写重置规则：W3C CSS Fonts Level 4，§2，Working Draft（2026-11-04）：[CSS Fonts](https://www.w3.org/TR/css-fonts-4/)，检查于 2026-11-06。
> - 无单位与长度 `line-height` 的计算和继承：W3C CSS Inline Layout Level 3，§5.1，Working Draft（2024-12-18）：[CSS Inline Layout](https://www.w3.org/TR/css-inline-3/)，检查于 2026-11-06。
> - 背景层、背景色、图像与简写：W3C CSS Backgrounds and Borders Level 3，§2.1–2.10、§3.9，Candidate Recommendation Draft（2024-03-11）：[CSS Backgrounds and Borders](https://www.w3.org/TR/css-backgrounds-3/)，检查于 2026-11-06。
> - 状态不只用颜色表达：W3C Web Content Accessibility Guidelines 2.2，Success Criterion 1.4.1，Recommendation（2024-12-12）：[Use of Color](https://www.w3.org/TR/WCAG22/#use-of-color)，检查于 2026-11-06。
