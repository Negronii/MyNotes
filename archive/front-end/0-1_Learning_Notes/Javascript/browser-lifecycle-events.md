# 何时监听文档就绪、资源加载与窗口变化？

这份早期笔记的就绪事件主线已并入前端浏览器章节。等待 Document Object Model（文档对象模型，DOM）就绪与响应窗口尺寸、滚动变化，是不同的监听目的：

- [脚本如何影响 HTML 解析与文档就绪？](../../../../frontend/html-css/browser-html-and-css.md#domcontentloaded-和-load-分别说明什么)解释 DOMContentLoaded、load、readyState 与延迟注册监听器。
- [浏览器怎样查询、更新 DOM 并响应用户输入？](../../../../frontend/browser-apis/dom-manipulation-and-events.md#窗口-resize元素尺寸与-scroll-应监听在哪里)说明 window resize、ResizeObserver、页面或元素 scroll 的监听目标与清理。

本归档路径保留作旧链接入口；就绪时序及 resize / scroll 的机制以以上章节为准。
