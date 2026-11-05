# How do you keep flex navigation and text from overflowing? / 如何避免 Flex 导航和文字溢出？

A flex item's automatic minimum size can prevent it from shrinking to the available width. For an ellipsized flex child, give the relevant item `min-width: 0`; keep the page's logical source order meaningful even if the visual layout changes. / Flex 子项的自动最小尺寸可能阻止它缩到可用宽度。需要截断文字时，让相关项目使用 `min-width: 0`；即使视觉布局改变，也应保持有意义的文档顺序。

![Flex Model Composition](flex.png)

## Archived flexbox examples / 归档 Flexbox 示例

### Responsive Navbar with Flexbox

```html
<nav class="navbar">
    <div class="nav-item">Home</div>
    <div class="nav-item">About</div>
    <div class="nav-item">Services</div>
    <div class="nav-item">Contact</div>
</nav>
```

```css
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #333;
    padding: 10px;
}
.nav-item {
    color: white;
    padding: 10px;
    text-decoration: none;
}
.nav-item:hover {
    background-color: #575757;
}
```

### Automatic Ellipsis with Flexbox

```html
<div class="flex-container">
    <div class="flex-item ellipsis">This is a long text that will be truncated with an ellipsis when it overflows the container.</div>
</div>
```

```css
.flex-container {
    display: flex;
    width: 200px;
}
.flex-item {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0; /* Override the content-based automatic minimum when shrinking is intended. */
}
```

Flex items often have a content-based automatic minimum size, so long unbreakable text may prevent the expected shrink. Use `min-width: 0` for a row item or `min-height: 0` for a column item when it should shrink, and decide whether its contents wrap, clip, or scroll.

### Multi-line Text Ellipsis

```html
<div class="ellipsis2">
    This is a long text that will be truncated with an ellipsis after two lines when it overflows the container. It is an example of how to handle multi-line text overflow in a flexbox layout.
</div>
```

```css
.ellipsis2 {
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    white-space: normal;
}
```

**See also / 另见：** [Flex & Grid Layout / Flex与Grid布局](../../../../frontend/html-css/flex-and-grid-layout.md) covers sizing, alignment, intrinsic minimums, and the complete property reference; [HTML and CSS Basics / HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md) covers general text truncation.
