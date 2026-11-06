# 为什么一次 DOM 改动会增加布局或绘制工作？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary`，看到 May、April 两行报表；点击“最早优先”后，页面把 URL 中的 `sort` 改为 `oldest`，并把行顺序换成 April → May。`/reports.js` 的处理器同步改 DOM，但列表何时出现在屏幕上、浏览器为此需要多少工作，是接下来的问题。

~~~mermaid
flowchart TD
    CLICK[点击“最早优先”] --> DOM[同步改动 DOM：行顺序与 aria-pressed]
    DOM --> INVALID[相关样式或布局数据可能失效]
    INVALID --> STYLE[需要时重新计算样式]
    STYLE -->|几何或换行有变化| LAYOUT[需要时重新计算布局]
    STYLE -->|几何不变但像素变化| PAINT[更新受影响的绘制结果]
    LAYOUT --> PAINT
    PAINT --> RASTER[需要时栅格化]
    RASTER --> COMPOSITE[合成画面]
    COMPOSITE --> FRAME[有需要时在后续渲染机会呈现]
    DOM -->|若脚本此时读取几何| READ[脚本读取当前几何]
    READ --> CHECK{相关数据已经是最新？}
    CHECK -->|是| VALUE[返回几何值，脚本继续]
    CHECK -->|否| FLUSH[返回前同步刷新样式或布局]
    FLUSH --> VALUE
    STYLE -->|属性与实现路径都适合时| MAYBE[某些实现可跳过布局或绘制]
    MAYBE --> COMPOSITE
~~~

图里的阶段是帮助解释依赖的概念模型，不表示每次更新都必须走完全部步骤。浏览器可延后并合并工作，也可跳过没有失效的阶段；脚本中的几何读取若要求最新结果，则可能让原本可延后的刷新提前发生。DOM 改动会提供下一帧的呈现状态；后续网络请求或异步业务结果是否已完成，是另一条时间线，浏览器也不保证每个任务后都立刻呈现。渲染机会与这条时间边界见[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)。

## 浏览器需要让哪些信息重新一致？

DOM 描述节点及其父子顺序，CSS 规则为这些节点提供样式。样式计算得到当前适用的 computed style（计算样式）；布局根据样式、内容和可用空间计算盒子的尺寸与位置；绘制把可见内容表示为绘制操作。后续实现可把绘制操作栅格化为像素内容，再合成各层并提交画面。简单说，列表换序先改了结构，浏览器必须保证它下一次显示时，结构、样式和几何彼此一致。

| 对这张报表做什么 | 下一次呈现通常要考虑什么 | 为什么不能仅凭操作名称断言成本 |
|---|---|---|
| 把两行从 May → April 调成 April → May | 更新列表有关的样式与几何，必要时重绘 | 具体失效范围取决于布局依赖和引擎优化 |
| 只把当前按钮文字颜色改为强调色 | 重算相关样式并更新可见像素 | 若尺寸、字体和换行不变，可能复用已有几何 |
| 改宽度、字体尺寸，或插入会占空间的内容 | 可能重新布局受影响的区域并更新绘制 | 几何变化会影响后续内容的位置，影响范围不一定只在一个节点内 |
| 改变适合合成处理的 `transform` 或 `opacity` | 有些情况下可以跳过布局或绘制 | 不保证只在合成阶段完成，也不保证提升图层或使用 GPU |
| DOM / 样式改动后读取几何 | 若返回值依赖的样式或布局已失效，读取前可能同步刷新 | 若数据仍是最新的，同一读取 API 不需要触发布局 |

`reflow`（重排）和 `repaint`（重绘）是常用说法，不是可以跨浏览器直接比较的性能分数。即使影响的是一个小节点，它的位置也可能牵动后续内容；反过来，大量节点若没有相关数据变化，也不必每次都重算。`transform` 和 `opacity` 常作为动画候选，是因为某些更新路径可以跳过布局或绘制；要确认目标页面是否走了这条路径，应检查实际录制，而不是只看 CSS 属性名。

## 为什么读几何会让脚本停下来？

浏览器可以把样式或布局标为待更新，先继续运行 JavaScript，等需要显示或读取当前结果时再计算。`offsetWidth`、`getBoundingClientRect()` 等几何 API 要返回调用时的尺寸或坐标；如果前面的 DOM / 样式写入已经使相关数据失效，浏览器就可能先刷新再返回。这里的停顿不是这个 API 每次都会“主动制造布局”，而是它要求拿到尚未更新的当前值。DOM 写入本身同步生效；同步刷新发生时，脚本会在几何值返回前付出这一段工作。

下面的示例从同一组已有元素开始：两个不受最小/最大宽度或变换约束的普通块级元素，边框盒宽度分别为 100px 和 160px；`box-sizing: border-box` 让 `style.width` 也指定边框盒宽度，因此两种代码都意图把宽度改为 110px 和 170px。示例使用数组而不是直接把 `querySelectorAll()` 返回的 `NodeList` 当作有 `.map()` 的数组：

~~~html
<div id="width-demo">
  <div class="item" style="width: 100px"></div>
  <div class="item" style="width: 160px"></div>
</div>
~~~

~~~css
#width-demo .item {
  box-sizing: border-box;
  padding: 4px;
  border: 1px solid;
}
~~~

~~~javascript
const items = Array.from(document.querySelectorAll("#width-demo .item"));
~~~

以下两段代码是从上述相同初始宽度分别运行的两种写法，不是先后连续执行。第一种在每次写入宽度后，又读取下一项当前宽度。若某次写入使后续读取依赖的几何数据失效，读取可能触发同步刷新，形成反复的读—写：

~~~javascript
for (const item of items) {
  item.style.width = (item.offsetWidth + 10) + "px";
}
~~~

若需求是按原始宽度统一增加 10 像素，可以先读取一组尺寸，再写回；按上述起始尺寸，写入结果同样是 110px 和 170px：

~~~javascript
const widths = items.map(item => item.offsetWidth);
items.forEach((item, index) => {
  item.style.width = (widths[index] + 10) + "px";
});
~~~

第二种顺序消除了显眼的交替读写，允许浏览器把后续更新合并处理；它不保证整段代码只发生一次布局，也不保证所有数据和页面上都更快。先确认页面确有强制刷新，再用性能录制定位写入与读取的位置。不同几何 API 返回的盒子与坐标系不同，按问题选择，见[哪个 DOM 几何 API 能回答哪种测量问题？](./dom-properties.md)。

## 引擎怎样实现这些步骤？

Web 平台规定 DOM、CSS 和几何 API 可观察到的结果，但不要求每个浏览器使用相同的内部阶段、进程或线程。以 Chromium 的 RenderingNG 为例，Blink 会计算样式、布局并生成绘制产物，后续可把绘制列表分块栅格化为 GPU 纹理 tile，再提交 compositor frame，由 Viz 聚合并绘制到屏幕；若某次变化不需要某些阶段，管线可以跳过它们。其他引擎的内部组件名称和调度方式可以不同，因此性能判断应围绕可见效果和录制数据，而不是把 Chromium 流程当作所有浏览器的硬性规范。

如果报表扩大到许多行，先分清瓶颈在网络传输、服务端查询、客户端数据计算，还是已挂载节点的样式与布局。虚拟滚动主要减少同时挂载的 DOM；它不会自动缩小已下载数据或消除对全量数据的计算。完整的窗口计算、可变行高、焦点和辅助技术边界在[长报表列表何时适合虚拟滚动？](../performance/rendering-and-computation-optimization.md)展开；性能录制怎样区分主线程、布局和绘制成本，见[如何测量并诊断网页性能问题？](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 本章的概念阶段不是 Web 平台规定的完整固定流水线；渲染机会、更新渲染： [WHATWG HTML：事件循环与更新渲染](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering)，Living Standard，持续更新；核对日期：2026-11-06。
> - 盒子、布局与几何读取的可观察行为： [CSS Display](https://www.w3.org/TR/css-display-3/)，W3C Candidate Recommendation Draft，2026-06-05，display 类型与盒子生成；[CSS Sizing](https://www.w3.org/TR/css-sizing-3/#box-sizing)，box-sizing 的宽度计算；[CSSOM View](https://drafts.csswg.org/cssom-view/)，CSSWG Editor's Draft，`offsetWidth` 与 `getBoundingClientRect()`；核对日期：2026-11-06。
> - DOM / 样式失效后读取几何可能触发同步布局，以及读写交错的风险： [Chrome Performance Insights：Forced reflow](https://developer.chrome.com/docs/performance/insights/forced-reflow)，Chrome DevTools 文档，2025-10-08 更新；该诊断解释 Chrome 实现。
> - 作为一个实现案例的样式、布局、绘制、tile 栅格化、Viz 合成与可跳过阶段： [Chromium RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)，[RenderingNG 数据结构：tiles 与 Viz](https://developer.chrome.com/docs/chromium/renderingng-data-structures)，Chromium 架构说明；核对日期：2026-11-06。
