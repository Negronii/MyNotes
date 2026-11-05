# Why can a CSS change trigger layout, paint, or compositing work? / 为什么 CSS 改动会触发布局、绘制或合成工作？

A DOM or style change invalidates only the work needed for the next correct presentation, but that dependency may include style recalculation, layout, paint, rasterization, and compositing. Layout computes geometry; paint records drawing operations; rasterization turns paint output into pixel content; compositing arranges content for a frame. Reading geometry after a write can synchronously force stale style or layout to become current, but a geometry read does not always cause a new layout. / DOM 或样式变化会使下一次正确呈现所需的工作失效，依赖链可能包含样式重算、布局、绘制、栅格化和合成。布局计算几何；绘制记录绘图操作；栅格化把绘制输出转为像素内容；合成将内容组织成画面。写入后读取几何值可能同步刷新尚未更新的样式或布局，但几何读取并不总会触发布局。

## Which work may be invalidated? / 哪些工作可能失效？

| Change (examples) | Work often needed | Boundary |
|---|---|---|
| Geometry or line-wrap change (`width`, font metrics, inserting a node) | Style, layout, paint, then presentation | Extent depends on layout dependencies and engine |
| Visual-only style change (`color`, many backgrounds) | Style, paint, then presentation | Geometry can be reused |
| Suitable `transform` or `opacity` update | Style or compositor update, then presentation | May avoid layout and paint; layer or GPU use is not guaranteed |
| Read current geometry after DOM/style writes | Potential synchronous style/layout flush | No flush is needed if relevant state is already current |

“Reflow” and “repaint” are convenient shorthand, not portable performance scores. A small element can trigger work beyond itself, while a large subtree can be cheap when relevant data is unchanged. `transform` and `opacity` often make good animation candidates, but do not guarantee compositor-only updates, layer promotion, or GPU execution. Profile the target page and browser.

## How does a layout read become forced work? / 布局读取如何变成同步刷新？

When script changes the DOM or a layout-affecting style, the browser may mark style or layout data dirty and defer recalculation until it needs a current result. A later API that returns current geometry—such as `offsetWidth` or `getBoundingClientRect()`—can require that pending work to run before returning. If the relevant data is already current, the same API need not trigger layout.

This loop repeatedly asks for current geometry after changing style, creating repeated flush opportunities:

~~~javascript
for (const item of items) {
  item.style.width = (item.offsetWidth + 10) + "px";
}
~~~

Collect measurements before writing. This avoids the obvious read-write-read pattern; it does not promise that every later change collapses to one layout or that batching is faster for every workload.

~~~javascript
const widths = items.map(item => item.offsetWidth);
items.forEach((item, index) => {
  item.style.width = (widths[index] + 10) + "px";
});
~~~

Choose a geometry API from the box and coordinate system needed: see [Which DOM geometry API returns the size or coordinate I need?](./dom-properties.md). For a measured performance problem, inspect a rendering trace; [How should browser performance be measured and diagnosed?](../performance/performance-metrics-and-analysis.md) connects the trace to the user-visible symptom.

## Standards versus an implementation pipeline / 标准行为与引擎流水线的界限

CSS and CSSOM View define observable layout results and geometry APIs. They do not require every browser to expose internal stages called “render tree,” “reflow,” “raster,” or “composite,” or require the same process and thread arrangement. Chromium's RenderingNG is one implementation example: Blink produces paint artifacts, Chromium schedules raster work into tiles, compositor components assemble frames, and Viz submits frames for display. Those names and steps describe Chromium, not all browser engines; operating-system composition and display timing also sit outside the web platform's CSS layout contract.

**Sources checked 2026-11-05:** [CSSOM View](https://www.w3.org/TR/cssom-view-1/) for geometry APIs; [CSS Display](https://www.w3.org/TR/css-display-3/) for box and formatting behavior; [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture) for the illustrative implementation pipeline; [Chrome forced reflow guidance](https://developer.chrome.com/docs/performance/insights/forced-reflow).
