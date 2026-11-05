# How can a mobile page respond to taps without disabling zoom? / 移动页面如何快速响应点击且不禁用缩放？

The common 300 ms tap delay came from some mobile browsers distinguishing a possible double-tap zoom; the exact behavior varies by browser. For a control where double-tap zoom is not needed, `touch-action: manipulation` permits user-agent panning and continuous zoom such as pinch while excluding behaviors triggered by multiple activations. Test the target browser and assistive-technology combinations, and do not disable page zoom globally. / 一些移动浏览器过去会通过约 300 毫秒的点击延迟来区分双击缩放；具体行为因浏览器而异。若某个控件不需要双击缩放，可用 `touch-action: manipulation` 允许浏览器处理平移及捏合等连续缩放，同时排除依赖连续激活的行为。应在目标浏览器和辅助技术组合上测试，不要全局禁用页面缩放。

~~~css
button {
  touch-action: manipulation;
}
~~~

Apply the rule only where its gesture policy fits. The value does not disable ordinary control activation or text selection; it changes which direct-manipulation panning and zooming behaviors the user agent may handle. A responsive viewport is part of mobile setup, but do not assume it removes a click delay on every target browser. Test actual devices instead of adding a tap library by default.

For DOM listeners, propagation, and passive touch-listener behavior, see [DOM Manipulation and Events](../../../frontend/browser-apis/dom-manipulation-and-events.md). The [Pointer Events specification](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property) defines `manipulation` and its relationship to panning, continuous zoom, and double-tap gestures; [Chrome's historical guide](https://developer.chrome.com/blog/300ms-tap-delay-gone-away) describes the viewport and delay behavior for that browser family.
