# 怎样用开发者工具对照页面与设计稿？

在月度报表页面中，若卡片宽度、文字颜色或图片位置与设计稿不符，先用 Chrome DevTools（浏览器开发者工具）观察页面真实状态，再回到源码修复。检查器里的临时编辑通常只影响当前页面会话，刷新后会恢复；启用 Local Overrides（本地替代）时，部分样式编辑可以跨刷新保存；Chrome Workspaces（工作区映射）则可把本地源码接入 DevTools。检查前先确认自己使用的是哪种保存方式。

## 怎样找出实际生效的样式？

在页面中右键报表卡片并选 **Inspect**，进入 **Elements** 面板沿 DOM 树确认选中了预期元素。样式面板显示匹配的 CSS（Cascading Style Sheets，层叠样式表）规则、来源文件和被覆盖的声明；临时勾选或修改一条规则，可以验证“是不是被另一条规则盖住”或“是不是容器尺寸影响了子项”。普通临时修改不会写回项目文件；某些网络资源可由 Local Overrides 保存在覆盖目录，Workspaces 则提供另一种保存本地源码的流程。

![Chrome DevTools 早期查错流程图](google-inspect.png)

这张图保留了原课程中先定位元素、再检查选择器和未生效样式的流程。图里的删除线可见于被覆盖或无效的声明；小三角等图标要结合所在面板和悬停说明判断，不能只按形状或颜色推断错误类型。

接着按以下顺序排查：

1. 在 **Elements** 中选中受影响的节点，沿 DOM 树确认选择器对应的是目标元素。
2. 在 **Styles** 中检查匹配的选择器、来源文件、覆盖状态与媒体查询。若找不到预期规则，检查是否选错元素、样式文件是否加载，以及媒体条件是否生效。
3. 在 **Computed**（计算样式）中查看浏览器解析后应用的值；尺寸问题还可看盒模型，确认内容、内边距和边框怎样组成元素尺寸。
4. 若元素没出现或交互异常，再查 **Console** 的错误；图标或警告提示应结合所属面板的说明，不能一概当作 CSS 声明无效。
5. 若资源或加载有问题，到 **Network** 看请求状态、耗时和传输大小；若卡顿或反复布局，到 **Performance** 录制并查看主线程、样式计算和布局工作。

## 怎样把设计稿的数值换成页面里的 CSS 值？

在 PxCook 或其他设计检查工具中用标尺读取间距、宽度和颜色前，先确认设计稿标注对应的 CSS 视口、导出倍率和画布缩放。工具显示的像素可能是 CSS pixel（CSS 像素）、device pixel（设备像素），也可能是画布缩放后的数值，不能只凭浏览器设备像素比或标尺上的数字推断应该写入多少 `px`。只有在项目已约定导出图倍率时，才按该倍率换算；例如已确认 2 倍导出图的原图宽 640 像素对应 320 CSS 像素，才可据此换算。

例如，同一视口下设计稿要求报表卡片的边框盒宽 320 CSS 像素，而页面实际只有 300 CSS 像素。假设父容器边框盒宽 340 像素、左右内边距各 20 像素且没有边框，因此内容宽是 300 像素；卡片规则为 `width: 320px; max-width: 100%; box-sizing: border-box`。在 **Styles** 中仍会看到 `width: 320px`，但 **Computed** 的宽度和盒模型显示卡片受父容器限制为 300 像素。临时把卡片宽度改成 300 像素仍不会变宽；若设计要求它在这里达到 320 像素，可把父容器边框盒调到 360 像素，使其内容宽达到 320 像素，再检查断点、长标题和侧栏状态。确认合适的父布局规则后，把改动写回源码并在真实页面复查。

**另见：**[盒尺寸与格式化上下文怎样改变布局计算？](../../../../frontend/html-css/box-model-and-bfc.md)、[构建工具怎样验证生产产物？](../../../../frontend/tooling/build-tools.md)。

> [!info]- 来源
> - **Chrome 面板与样式排查：**[Elements 面板](https://developer.chrome.com/docs/devtools/elements/)、[Styles 与 Computed 参考](https://developer.chrome.com/docs/devtools/css/reference)、[CSS 问题标识](https://developer.chrome.com/docs/devtools/css/issues/)、[Performance 面板](https://developer.chrome.com/docs/devtools/performance/)、[Network 面板](https://developer.chrome.com/docs/devtools/network/)。
> - **保存方式：**[Local Overrides](https://developer.chrome.com/docs/devtools/overrides/)、[Workspaces](https://developer.chrome.com/docs/devtools/workspaces/)。
> - **像素与尺寸：**[CSSOM 的 resolved values](https://www.w3.org/TR/cssom/#resolved-values)、[CSS Values and Units 的绝对长度](https://www.w3.org/TR/css-values-4/#absolute-lengths)、[Chrome 设备模式](https://developer.chrome.com/docs/devtools/device-mode/)。
>
> Chrome 面板说明于 2026-11-06 按官方文档核对；Styles/Computed 与 Local Overrides 说明于 2026-11-13 复查。原查错流程图保持不变。
