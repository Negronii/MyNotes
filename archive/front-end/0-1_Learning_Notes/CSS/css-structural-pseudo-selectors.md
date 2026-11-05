# How do CSS pseudo-classes and pseudo-elements target parts of a document? / CSS 伪类和伪元素怎样定位文档中的局部？

`:first-child`, `:nth-child()`, and related pseudo-classes count element siblings; `:nth-of-type()` counts only siblings with the same element name. `::before` and `::after` style generated content attached to a matched element. Use the canonical [CSS cascade and selector note](../../../../frontend/html-css/html-and-css-basics.md) for specificity and cascade order. / `:first-child`、`:nth-child()` 等伪类按元素兄弟顺序计数；`:nth-of-type()` 只统计相同元素名的兄弟。`::before` 与 `::after` 用于给匹配元素附加并修饰生成内容。specificity 与级联顺序见规范主题[CSS 级联与选择器](../../../../frontend/html-css/html-and-css-basics.md)。

## Structural pseudo-classes / 结构伪类

```css
p:first-child { color: blue; }
p:last-child { color: green; }
p:nth-child(2) { color: red; }
p:nth-last-child(2) { color: purple; }
p:nth-of-type(3) { color: orange; }
p:nth-last-of-type(3) { color: pink; }
```

```html
<div>
  <p>First paragraph (blue)</p>
  <p>Second paragraph (red)</p>
  <p>Third paragraph (orange)</p>
  <p>Fourth paragraph (pink)</p>
  <p>Fifth paragraph (purple)</p>
  <p>Sixth paragraph (green)</p>
</div>
```

`p:nth-child(3)` would match only if the third element child is a paragraph; `p:nth-of-type(3)` matches the third paragraph even when other element types appear before it.

## Generated pseudo-elements / 生成伪元素

`::before` and `::after` create generated boxes associated with an element; they are not new DOM nodes. Use them for decorative or presentational content, not information that should be available as document text.

```css
p::before {
  content: "Prefix ";
  color: red;
}

p::after {
  content: " Suffix";
  color: blue;
}
```

```html
<p>This is a paragraph.</p>
```

**Sources / 来源** — [Selectors Level 4](https://www.w3.org/TR/selectors-4/), [CSS Pseudo-Elements Level 4](https://www.w3.org/TR/css-pseudo-4/#generated-content).
