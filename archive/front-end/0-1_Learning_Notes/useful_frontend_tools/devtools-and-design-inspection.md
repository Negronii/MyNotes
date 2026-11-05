# How do you compare a rendered page with its design? / 如何对照设计检查页面实际效果？

Inspect computed styles and live DOM behavior in DevTools, then compare the measured page with the design values. Browser edits are temporary experiments; copy verified changes back to source and confirm behavior in the real layout. / 用 DevTools 检查计算样式和实时 DOM 行为，再将页面测量值与设计稿对照。浏览器内编辑只是临时验证；确认后应回写源码，并在真实布局中检查效果。

## Chrome DevTools / Chrome 开发者工具

Open DevTools with F12 or the browser menu, then use **Elements** to inspect an element and edit its live styles. These edits are temporary until copied into source code. Console icons distinguish errors, warnings, and informational messages; a warning marker does not always mean that a CSS declaration is invalid.

![Google Debug Tool](google-inspect.png)

Useful workflow:

1. Select the affected element in **Elements** and inspect the matched rules and computed styles.
2. Toggle declarations or adjust values to test a hypothesis.
3. Check **Console** for runtime errors and warnings.
4. Use **Network** for request status, timing, and transferred size; use **Performance** to record scripting, rendering, and layout work.

## Design inspection / 设计稿检查

In PxCook or a similar design-inspection tool, use the ruler to read a measurement and the color picker to inspect a color value. Confirm whether the design value is expressed in CSS pixels, device pixels, or a scaled viewport before copying it into the page.

**Reference / 参考资料：** [Chrome DevTools overview](https://developer.chrome.com/docs/devtools/overview/).
