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

## Keep selectors maintainable

Attribute selectors such as `[data-state="active"]` can reflect state in markup. BEM naming (`.block__element--modifier`) tends to keep selectors flat and easier to override. CSS-in-JS-generated classes still participate in the browser's cascade; the generation method does not remove cascade rules.

Critical CSS can reduce dependence on a render-blocking stylesheet for content that must appear early, but it adds markup bytes and can duplicate later CSS. Treat it as a measured delivery choice, not as an automatic selector-speed technique. See [Performance Metrics and Analysis](../performance/performance-metrics-and-analysis.md).

**Specifications:** [Selectors Level 4](https://www.w3.org/TR/selectors-4/#specificity-rules), [CSS Cascading and Inheritance Level 5](https://www.w3.org/TR/css-cascade-5/), and [CSS Display, visual order](https://www.w3.org/TR/css-display-3/#order-property).


**Related questions:** [CSS inheritance](./css-inheritance.md) explains which values flow to children; [responsive CSS units and layout](./responsive-css-units-and-layout.md) covers size references and breakpoints; [semantic HTML forms](./accessible-html-forms.md) covers native controls and validation; [text overflow and line clamp](./css-text-overflow-and-line-clamp.md) covers visual truncation.
