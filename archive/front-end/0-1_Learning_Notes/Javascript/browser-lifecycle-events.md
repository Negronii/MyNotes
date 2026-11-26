# 何时监听文档就绪、资源加载与窗口变化？

这份早期笔记中关于页面就绪事件的内容已并入前端浏览器章节。等待 Document Object Model（文档对象模型，DOM）就绪，和响应窗口尺寸或滚动变化，是两类不同的监听需求，分别见：

- [脚本如何影响 HTML 解析与文档就绪？](../../../../frontend/browser/from-url-to-interactive-page.md)解释 DOMContentLoaded、load、readyState 与延迟注册监听器。
- [浏览器怎样查询、更新 DOM 并响应用户输入？](../../../../frontend/browser/dom-events.md)说明 window resize、ResizeObserver、页面或元素 scroll 的监听目标与清理。

本归档路径保留作旧链接入口；就绪时序及 resize / scroll 的机制以以上章节为准。
