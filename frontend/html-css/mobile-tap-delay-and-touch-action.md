# How should a mobile page handle tap gestures and the historical 300 ms delay? / 移动页面应如何处理点按手势与历史上的 300 毫秒延迟？

The old click delay was conditional: some browsers delayed click dispatch while waiting to distinguish a tap from a double-tap zoom gesture. It is not a universal fixed delay today. Start with a mobile-optimized viewport, then set a gesture policy only on controls that need one. `touch-action: manipulation` allows panning and pinch zoom while excluding double-tap gestures; do not disable user zoom to address a historical delay. / 历史上的点击延迟有触发条件：部分浏览器曾等待判断点按是否为双击缩放，因此延后派发 click；如今不能把它视为普遍固定延迟。先使用适合移动端的 viewport，再仅为确实需要的控件设置手势策略。`touch-action: manipulation` 允许平移和双指缩放，同时排除双击手势；不要为了处理历史延迟而禁用用户缩放。

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

This tells the browser to use a layout viewport aligned with the device width. It does not prevent pinch zoom. Chrome's current guidance documents a possible delay up to 300 ms when the initial viewport is not optimized for mobile; other browsers and input configurations can differ. [Chrome's viewport insight](https://developer.chrome.com/docs/performance/insights/viewport) describes that specific condition.

For an interactive region where double-tap zoom is not part of the desired gesture, Pointer Events defines:

```css
button,
[role="button"] {
  touch-action: manipulation;
}
```

Apply the rule narrowly enough to preserve the intended panning and zoom behavior. Avoid a legacy tap library unless a tested target requires it: a library that synthesizes click can conflict with the browser's native click, so do not activate the same action on both touch-end and click.

**Specification:** [Pointer Events Level 3, `touch-action`](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property) defines the allowed direct-manipulation gestures.
