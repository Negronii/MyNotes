# How do CSS sprites and a static image banner work? / CSS 雪碧图和静态图片横幅如何工作？

A sprite uses one image file with `background-position` to reveal a selected region. A static banner can stack image items and reveal the selected item, but this example is not a complete carousel: it has no rotation, controls, keyboard behavior, or pause mechanism. / 雪碧图使用一张图片，并通过 `background-position` 显示选定区域。静态横幅可叠放多个图片条目并显示当前项，但此示例不是完整轮播：没有自动轮播、控制项、键盘操作或暂停机制。

![Archived banner design example](banner.png)

## Sprites

Sprites combine multiple images into one. They can reduce request count in some setups, but do not guarantee faster loading; image size, caching, compression, and how the assets are used also matter. This remains a useful technique for fixed icon sheets and legacy projects.

### Steps to Use Sprites

1. Create a container and set its size to the size of the desired sprite.
2. Set the sprite image as the background of the container.
3. Adjust the background position to display the correct part of the sprite.

**Example:**
```css
.sprite {
  width: 50px;
  height: 50px;
  background: url('sprite.png') no-repeat;
  background-position: -10px -20px; /* Adjust based on sprite position */
}
```

## Banner

For creating a banner with multiple images, this small CSS example shows a static selected slide. It does not implement rotation, controls, keyboard behavior, or an accessible carousel pattern. A production carousel needs visible controls, a way to pause automatic movement, and content that remains usable with assistive technology.

1. Use an unordered list (`<ul>`) with list items (`<li>`) for each image.
2. Position the list items using CSS.
3. Indicate the current image with a class like `.current`.

**Example:**
```html
<ul class="banner">
  <li class="current"><a href="image1.jpg"><img src="image1.jpg" alt="Image 1"></a></li>
  <li><a href="image2.jpg"><img src="image2.jpg" alt="Image 2"></a></li>
  <!-- Additional images -->
</ul>
```

```css
.banner {
  position: relative;
  overflow: hidden;
}
.banner li {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  display: none;
}
.banner li.current {
  display: block;
}
```

**See also / 另见：** [Image Lazy Loading / 浏览器图片懒加载](../../../../frontend/browser-apis/image-lazy-loading.md) for progressive image loading and [HTML and CSS Basics / HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md) for semantic content.
