# 怎样用开发者工具对照页面与设计稿？

在月度报表页面中，若卡片宽度、文字颜色或图片位置与设计稿不符，先用浏览器开发者工具（DevTools）观察页面真实状态，再回到源码修复。检查器里的样式编辑只作用于当前页面会话；它适合验证假设，最终改动仍应回写项目样式并在真实布局里复查。

## 怎样找出实际生效的样式？

在 Chrome DevTools（开发者工具）的 **Elements** 面板选中报表卡片，先看CSS（Cascading Style Sheets，层叠样式表）的匹配规则和被覆盖的声明，再到 **Computed** 面板确认浏览器用于渲染的计算值。临时切换一条规则可以验证“是不是被另一条规则盖住”或“是不是容器尺寸影响了子项”；它不会自动修改本地 CSS 文件。

![Google Debug Tool](google-inspect.png)

建议顺序如下：

1. 在 **Elements** 中选中受影响的节点，沿 DOM 树确认选中了预期元素。
2. 在样式面板检查匹配选择器、来源文件、覆盖状态与媒体查询；临时勾选或修改值来验证假设。
3. 在 **Computed** 中查看最终值和可展开的来源，确认继承或级联后采用了哪条规则。
4. 若元素没出现或交互异常，再查 **Console** 的错误；警告图标不一定代表 CSS 声明无效。
5. 若资源或加载有问题，到 **Network** 看请求状态、耗时和传输大小；若卡顿或反复布局，到 **Performance** 录制并查看主线程、样式计算和布局工作。

## 怎样把设计稿的数值换成页面里的 CSS 值？

在 PxCook 或其他设计检查工具中用标尺读取间距、宽度和颜色前，先确定设计稿使用的视口大小及缩放规则。设计工具显示的像素可能是 CSS pixel（CSS 像素）、device pixel（设备像素），或经过画布缩放后的数值；不能仅凭尺上的数字推断应该直接写入 `px`。

例如报表卡片在设计稿里宽 320，页面实际内容宽 300。先确认父容器内容宽和左右内边距，再看卡片是否有 `max-width` 或 `box-sizing` 约束。若临时把宽度从 320 改到 300 后对齐，仍需确认窄视口、长标题和侧栏状态没有被破坏，再把合适的规则写回源码。

**另见：**[盒尺寸与格式化上下文怎样改变布局计算？](../../../../frontend/html-css/box-model-and-bfc.md)、[构建工具怎样验证生产产物？](../../../../frontend/tooling/build-tools.md)。

> [!info]- 来源
> - [Chrome DevTools：Elements 面板](https://developer.chrome.com/docs/devtools/elements/)
> - [Chrome DevTools：查看无效或被覆盖的 CSS](https://developer.chrome.com/docs/devtools/css/issues/)
> - [Chrome DevTools：Performance 面板](https://developer.chrome.com/docs/devtools/performance/)、[Network 面板](https://developer.chrome.com/docs/devtools/network/)
>
> 浏览器工具说明按 Chrome 官方当前文档核对：2026-11-06。原附件截图保留不变。
