# 何时监听文档就绪、资源加载与窗口变化？

这份早期笔记的就绪事件主线已并入前端浏览器章节。等待 Document Object Model（文档对象模型，DOM）就绪与响应窗口尺寸、滚动变化，是不同的监听目的：

- [脚本如何影响 HTML 解析与文档就绪？](../../../../frontend/html-css/browser-html-and-css.md#DOMContentLoaded%20%E5%92%8C%20load%20%E5%88%86%E5%88%AB%E8%AF%B4%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)解释 DOMContentLoaded、load、readyState 与延迟注册监听器。
- [浏览器怎样查询、更新 DOM 并响应用户输入？](../../../../frontend/browser-apis/dom-manipulation-and-events.md#%E7%AA%97%E5%8F%A3%20resize%E3%80%81%E5%85%83%E7%B4%A0%E5%B0%BA%E5%AF%B8%E4%B8%8E%20scroll%20%E5%BA%94%E7%9B%91%E5%90%AC%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F)说明 window resize、ResizeObserver、页面或元素 scroll 的监听目标与清理。

本归档路径保留作旧链接入口；就绪时序及 resize / scroll 的机制以以上章节为准。
