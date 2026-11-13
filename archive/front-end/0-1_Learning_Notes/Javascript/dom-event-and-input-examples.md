# 如何用 DOM 事件处理委托、鼠标与键盘输入？

事件传播、事件委托、默认动作、触控策略、坐标系、拖动捕获与取消、键盘 key / code / repeat，以及旧 keypress 的边界已并入 [浏览器怎样查询、更新 DOM 并响应用户输入？](../../../../frontend/browser-apis/dom-manipulation-and-events.md)。

- [一次点击沿哪些节点传播？](../../../../frontend/browser-apis/dom-manipulation-and-events.md#%E4%B8%80%E6%AC%A1%E7%82%B9%E5%87%BB%E6%B2%BF%E5%93%AA%E4%BA%9B%E8%8A%82%E7%82%B9%E4%BC%A0%E6%92%AD%EF%BC%9F)解释 target、currentTarget 和传播阶段。
- [移动端点击与手势策略](../../../../frontend/browser-apis/dom-manipulation-and-events.md#移动端点击与手势策略)讨论 viewport、touch-action 和原生键盘激活。
- [键盘事件怎样区分按键含义、位置与重复？](../../../../frontend/browser-apis/dom-manipulation-and-events.md#%E9%94%AE%E7%9B%98%E4%BA%8B%E4%BB%B6%E6%80%8E%E6%A0%B7%E5%8C%BA%E5%88%86%E6%8C%89%E9%94%AE%E5%90%AB%E4%B9%89%E3%80%81%E4%BD%8D%E7%BD%AE%E4%B8%8E%E9%87%8D%E5%A4%8D%EF%BC%9F)解释 `key`、`code`、`repeat` 和旧 `keypress` 的边界。
- [拖动时怎样跟踪坐标并处理取消？](../../../../frontend/browser-apis/dom-manipulation-and-events.md#%E6%8B%96%E5%8A%A8%E6%97%B6%E6%80%8E%E6%A0%B7%E8%B7%9F%E8%B8%AA%E5%9D%90%E6%A0%87%E5%B9%B6%E5%A4%84%E7%90%86%E5%8F%96%E6%B6%88%EF%BC%9F)保留坐标、pointer capture、cancel 与键盘替代例。
