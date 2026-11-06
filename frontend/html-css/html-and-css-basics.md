# How does the CSS cascade decide which declaration applies? / CSS 级联如何决定最终生效的声明？

CSS first keeps declarations that apply to the element, then resolves their cascade priority. Origin and importance, encapsulation context, element-attached styles, and layer precedence are considered before specificity; scoping proximity where applicable and source order resolve later ties. Specificity is therefore only one part of the cascade; a larger selector weight cannot override a declaration that wins an earlier priority step. / CSS 先筛选适用于元素的声明，再解析级联优先级。来源与重要性、封装上下文、元素附加样式和层顺序先于 specificity；适用时由作用域接近程度及源码顺序进一步打破平局。因此 specificity 只是级联的一部分；更高的选择器权重不能推翻更早优先级步骤已经胜出的声明。

## Compare specificity only after earlier cascade steps

For ordinary author stylesheet rules in the same origin, importance, and layer, compare the tuple `(ID, class/attribute/pseudo-class, type/pseudo-element)` from left to right.

```css
/* (1, 1, 0): wins this same-layer comparison */
#sidebar .menu-item { color: red; }

/* (0, 3, 0): loses even with more classes */
.menu .menu-item.active { color: blue; }
```

An ID column wins before any number of class selectors. The universal selector (`*`) and combinators (`>`, `+`, `~`) add no specificity.

Functional pseudo-classes have defined argument behavior:

- `:not()`, `:is()`, and `:has()` contribute the specificity of their most-specific argument.
- `:where()` contributes zero specificity, including its arguments.
- A selector such as `div:not(.sidebar)` has specificity `(0, 1, 1)`.

Inline style declarations participate in the cascade through a separate element-attached style precedence step; do not treat their behavior as simply “more classes.” Importance and cascade layer rules still matter.

## Use layers to organize priority intentionally

Cascade layers let a stylesheet establish broad precedence groups, then use specificity within the winning layer.

```css
@layer reset, components, utilities;

@layer components {
  .button { color: navy; }
}

@layer utilities {
  .text-red { color: red; }
}
```

For normal declarations, later named layers outrank earlier layers, and unlayered normal declarations outrank declarations in named layers. For important declarations, layer order reverses. Use layer order as an explicit project-level policy rather than relying on ever-growing selector specificity. [CSS Cascading and Inheritance](https://www.w3.org/TR/css-cascade-5/#layer-order) defines the ordering.

## How a child gets a value after the cascade / 级联后子元素怎样得到值

The cascade first finds a winning declaration on the element itself. If none applies, an inherited property normally takes the parent’s computed value, while a non-inherited property takes its initial value. User-agent rules still participate in the cascade. A rule that directly sets a child’s color wins over an inherited color even if the parent was styled with an ID selector.

~~~html
<article id="notice">Read <span class="label">this</span>.</article>
~~~

~~~css
#notice { color: #222; font-family: system-ui, sans-serif; margin: 2rem; }
.label  { color: blue; }
~~~

The span computes blue from its own declaration and inherits the font. The parent's margin does not flow down. Applying `margin: inherit` explicitly would use the parent’s computed margin. Fonts, color, line height, text alignment, letter spacing, and visibility usually inherit. Width, padding, margin, display, and position do not inherit by default. Check the property definition when it matters. / 先看子元素自己是否有生效声明，再按属性的继承规则取值。父元素选择器的优先级不会传给子元素。

**Text decoration / 文本装饰.** A parent's underline can be drawn across descendant text through decoration propagation. On `<a>Title <em>with emphasis</em></a>`, setting `text-decoration: none` on `em` does not erase the line drawn by `a`. Change the rule on the element that establishes the decoration. [CSS Cascade defaulting and inheritance](https://www.w3.org/TR/css-cascade-5/#defaulting) · [CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/#line-decoration)

## Keep selectors maintainable

Attribute selectors such as `[data-state="active"]` can reflect state in markup. BEM naming (`.block__element--modifier`) tends to keep selectors flat and easier to override. CSS-in-JS-generated classes still participate in the browser's cascade; the generation method does not remove cascade rules.

Critical CSS can reduce dependence on a render-blocking stylesheet for content that must appear early, but it adds markup bytes and can duplicate later CSS. Treat it as a measured delivery choice, not as an automatic selector-speed technique. See [Performance Metrics and Analysis](../performance/performance-metrics-and-analysis.md).

**Specifications:** [Selectors Level 4](https://www.w3.org/TR/selectors-4/#specificity-rules), [CSS Cascading and Inheritance Level 5](https://www.w3.org/TR/css-cascade-5/), and [CSS Display, visual order](https://www.w3.org/TR/css-display-3/#order-property).


**Related questions:** [responsive CSS units and layout](./responsive-css-units-and-layout.md) covers size references and breakpoints; [semantic HTML forms](./accessible-html-forms.md) covers native controls and validation; [text overflow and line clamp](./responsive-css-units-and-layout.md#Constrained%20text%20and%20line%20clamping%20/%20%E5%8F%97%E9%99%90%E6%96%87%E6%9C%AC%E4%B8%8E%E8%A1%8C%E6%95%B0%E8%A3%81%E5%88%87) covers visual truncation.
