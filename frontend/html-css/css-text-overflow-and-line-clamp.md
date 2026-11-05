# How can CSS truncate one or several lines of text? / CSS 如何截断单行或多行文本？

For one line, keep the text on one line, clip overflow, and ask the browser to show an ellipsis. For a multiline excerpt, use the supported line-clamp syntax for the target browsers and constrain overflow. Truncation changes what is visible, not the underlying text; ensure the full content remains available when users need to read or copy it. / 单行截断需要保持单行、裁切溢出，并让浏览器绘制省略号。多行摘要则使用目标浏览器支持的行数裁切语法并限制溢出。截断只改变可见内容，不会删除底层文本；若用户需要完整阅读或复制，应提供可访问的完整内容。

## Single-line ellipsis

All three properties have distinct roles: `white-space` prevents wrapping, `overflow` clips the extra text, and `text-overflow` requests the ellipsis marker.

```css
.title {
  width: 100px; /* demonstration constraint; a parent may constrain production content */
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

The box also needs a constrained inline size, which can come from its parent layout. In a Flex or Grid item, `min-width: 0` may be needed so the item's intrinsic minimum does not force it wider than the available track. See [Flexbox and Grid layout](./flex-and-grid-layout.md).

## Multiline clamp

The legacy WebKit-compatible form uses a vertical box and an explicit line count:

```css
.excerpt {
  width: 100px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
```

CSS Overflow Level 4 specifies a `line-clamp` shorthand and documents the legacy compatibility form. It is a Working Draft, and supported behavior can vary; check the target browsers and exact syntax before shipping. [CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/#propdef-line-clamp).

`text-overflow` signals that inline content is clipped; it does not itself constrain the element's width or make multi-line clamping happen. For important text, provide a way to view the full value, preserve it in accessible text, and avoid using visual truncation as the only way to disclose essential information.

**Specification:** [CSS Overflow Module Level 4](https://www.w3.org/TR/css-overflow-4/).
