# Which CSS properties inherit their values from a parent? / 哪些 CSS 属性会从父元素继承值？

If a property is inherited and no declaration sets the child’s value, the child normally uses its parent’s computed value. Many text properties inherit, including font family, font size, line height, color, and text alignment. Box and layout properties such as margin, padding, width, display, and position do not inherit by default. / 如果某个属性会继承且没有声明设置子元素的值，子元素通常使用父元素的计算值。许多文本属性会继承，包括字体族、字号、行高、颜色和文本对齐；margin、padding、width、display、position 等盒模型和布局属性默认不继承。

```css
article {
  color: #222;
  font-family: system-ui, sans-serif;
  margin: 2rem;
}

article p {
  /* color and font-family inherit from article */
  /* margin does not inherit; this paragraph uses its own initial margin */
}
```

A child can explicitly request inheritance for any property with `inherit`:

```css
article p { margin: inherit; }
```

Common inherited property groups include:

- **Font:** `font-family`, `font-size`, `font-style`, `font-weight`, `line-height`
- **Text formatting:** `text-align`, `text-indent`, `text-transform`, `text-shadow`
- **Spacing and visibility:** `letter-spacing`, `word-spacing`, `visibility`

This is a useful rule of thumb, not an exhaustive list; check the property's definition when its default behavior matters.

## Why does a text-decoration line continue through a child?

`text-decoration` itself is not inherited. A line drawn by an ancestor can nevertheless continue across descendant text through text-decoration propagation. Setting `text-decoration: none` on a child does not simply erase the ancestor's underline. Put or remove the decoration on the element that establishes it.

```html
<a href="/article">
  Article title <em>with emphasis</em>
</a>
```

```css
a { text-decoration: underline; }
a em { text-decoration: none; } /* does not cancel the ancestor's propagated line */
```

The selected value and inheritance are part of CSS value processing; see [CSS Cascading and Inheritance](https://www.w3.org/TR/css-cascade-5/#inheritance) and [CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/).
