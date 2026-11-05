# When are icon fonts useful, and how are they loaded? / 何时适合使用图标字体，如何加载？

An icon font maps glyphs to font code points, so CSS can size and color them like text. It is convenient for a fixed icon set but needs an accessible text alternative and a reliable font load. / 图标字体把字形映射到字体码点，因此可像文字一样通过 CSS 调整尺寸和颜色。它适合固定图标集，但仍需无障碍文本替代和可靠的字体加载。

## Icon Fonts

Icon fonts are font files that contain vector-based icons instead of letters and numbers. They offer flexibility and efficiency in web design.

## Advantages of Icon Fonts vs. Images/Background Images

### Flexibility
- **Scalability:** Icon fonts can be scaled to any size without losing quality.
- **Styling:** Easily modify styles such as size, color, and shadow using CSS.

### Lightweight
- **Performance:** Small file sizes lead to faster loading times and reduced server requests.
- **Consistency:** Consistent appearance across different devices and resolutions.

### Compatibility
- **Cross-Browser Support:** Compatible with almost all major browsers, ensuring a consistent user experience.

## How to Use Icon Fonts

### Downloading Icon Fonts

1. Go to [Iconfont](https://www.iconfont.cn/) and log in.
2. Navigate to 素材库 (Material Library) → 官方图标库 (Official Icon Library).
3. Add the desired icons to the cart.
4. Click 添加至项目 (Add to Project).
5. Create a new project by clicking the folder icon with a plus sign.
6. Download the project from the project page.

### Invoking Icon Fonts

1. **Include the Font Icon Stylesheet:**
   ```html
   <link rel="stylesheet" href="./iconfont.css">
   ```

2. **Use the Icon in HTML:**
   ```html
   <span class="iconfont icon-favourites-fill"></span>
   ```
   - `iconfont`: Basic styles for using the font.
   - `icon-xxx`: Class name corresponding to the specific icon.

3. **Customizing Icons with CSS:**
   ```css
   .icon-favourites-fill {
       color: red;
       font-size: 24px;
   }
   ```

### Uploading Custom Icons

If the icons in the design draft are not available in Iconfont, you can upload your own.

1. Request vector illustrations in SVG format from the designer.
2. Upload the SVG icons to Iconfont:
   - Click 上传SVG图标 (Upload SVG Icons).
   - Browse local icons and remove colors before submission.
3. Add the icons to the cart and download them for use.
