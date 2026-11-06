# 图片与媒体资源怎样加载并保持页面稳定？

同一张图片可能是装饰、信息本身，也可能是链接或按钮的操作入口；资源何时请求则关系到首屏内容和网络开销。先按内容决定 HTML 语义与替代文本，再选择尺寸、候选资源和加载时机。

> [!info] 替代文本由用途决定
> alternative text（替代文本）通过 `alt` 提供。纯装饰图使用 `alt=""`；信息图用简洁文字传达页面所需信息；图片是链接或按钮唯一内容时，写出该控件的目的。`title` 不能代替替代文本或表单标签。

## 先按内容选择图像与媒体元素

图像内容用 `<img>`，到另一位置的导航用 `<a href>`，可播放音频和视频分别用 `<audio>`、`<video>`。先决定资源在文档中的语义与替代文本，再选择 URL、尺寸和加载时机。

## 资源地址相对哪个基准？

| 写法 | 示例 | 解析位置 |
| --- | --- | --- |
| 带 scheme 的 URL（统一资源定位符，网址） | `https://example.com/a.png` | 使用 URL 自身的方案和地址；`mailto:team@example.com` 有 scheme（方案）但没有主机 |
| 根相对路径 | `/assets/chart.png` | 从文档基准 URL 的 origin（源）根目录解析；`<base>` 可能改变 origin |
| 文档相对路径 | `../assets/chart.png` | 默认相对当前文档 URL；`<base>` 可改变文档基准 URL |

`src` 指向要载入的图像资源；`href` 为链接提供导航目标。根相对 URL 不是永远相对页面原站：若 `<base href="https://cdn.example.net/reports/q4/">` 改变了文档基准，`/assets/chart.png` 会解析为 `https://cdn.example.net/assets/chart.png`，`../assets/chart.png` 则解析为 `https://cdn.example.net/reports/assets/chart.png`。Unix 风格的文件系统路径 `/project/site/image.png` 不是网络地址。用 `<a>` 导航，用 `<button>` 执行动作；`href="#"` 会改变片段位置并可能影响历史记录，不是无操作占位符。`target="_blank"` 请求新的浏览上下文，适合确需另开页面的导航；给出明确的链接文字，显式写 `rel="noopener"` 也能表明不向新页面暴露 opener。

## 原生延迟加载适合什么图片？

普通首屏之外的内容图片可以使用 HTML `loading="lazy"`。浏览器决定具体的延迟阈值；元素仍需真实的 `src` 或 `srcset`，单写 `data-src` 不会开始图片请求。

~~~html
<img
  src="/assets/monthly-report.webp"
  alt="四月至六月的报表趋势图，六月达到最高值"
  width="640"
  height="360"
  loading="lazy">
~~~

`width` 和 `height` 提供图像固有比例。`640 × 360` 的比例为 `16:9`；若 CSS 将图片显示为 `320px` 宽，预留高度约 `320 × 9 ÷ 16 = 180px`，图片数据到达前浏览器就有尺寸可用于布局。也可用 CSS `aspect-ratio: 16 / 9` 表达容器比例。

对首屏可见、可能成为 Largest Contentful Paint（最大内容绘制，LCP）的主图不要盲目设置 lazy；延迟发现或请求会推迟它的呈现。

## 响应式候选文件怎样被选中？

`srcset` 中的 `640w`、`1280w` 描述候选图像文件的固有像素宽度；`sizes` 描述当前布局给图像留下的 CSS 像素宽度。下面的样式让图像在视口窄于 `640px` 时占满视口，宽屏上限为 `640px`，因此 `sizes` 与实际展示宽度相符：

~~~html
<img class="report-responsive"
     src="/assets/report-640.webp"
     srcset="/assets/report-640.webp 640w, /assets/report-1280.webp 1280w"
     sizes="(max-width: 640px) 100vw, 640px"
     width="640" height="360"
     alt="四月至六月的报表趋势图，六月达到最高值">
~~~

~~~css
.report-responsive {
  display: block;
  width: min(100vw, 640px);
  height: auto;
}
~~~

把布局宽度乘以设备像素比（DPR）可得到一个候选密度目标：`320px × DPR 2 = 640`，通常由 `640w` 资源满足；`640px × DPR 2 = 1280`，通常由 `1280w` 资源满足。浏览器结合可用候选、设备像素比和用户代理策略选文件；`sizes` 要反映页面实际留给图片的宽度。

若窄屏需要不同裁切而不是同一画面的高低分辨率版本，使用 `<picture>` 的 `<source media>` 切换图像，再由 `<img>` 提供后备资源、尺寸和 `alt`。下面两个裁切都保持 `16:9`；若不同裁切有不同宽高比，也要按断点调整展示盒比例：

~~~html
<picture>
  <source media="(max-width: 640px)" srcset="/assets/report-narrow-crop.webp">
  <img src="/assets/report-wide-crop.webp"
       width="640" height="360"
       alt="四月至六月的报表趋势图，六月达到最高值">
</picture>
~~~

## 何时用 IntersectionObserver（相交观察器）？

IntersectionObserver（相交观察器）适合自定义滚动根、预加载边距、阈值，或目标进入范围时除了加载图片还要执行其他工作。普通图片优先让浏览器通过原生属性自行安排。

~~~html
<img src="/assets/placeholder.png"
     data-src="/assets/offscreen-chart.png"
     alt="报表图表"
     width="640" height="360">
~~~

~~~javascript
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;

    const image = entry.target;
    image.src = image.dataset.src;
    image.removeAttribute("data-src");
    observer.unobserve(image);
  }
}, { rootMargin: "200px" });

document.querySelectorAll("img[data-src]").forEach((image) => observer.observe(image));
// 组件卸载且拥有该观察器时，调用 observer.disconnect()。
~~~

正的 `rootMargin` 会在图片进入可视根之前启动加载。`threshold: 0` 下边缘相接也可能报告 `isIntersecting: true`，即使交集矩形面积为零；相交状态不是“至少一像素可见”或“未被遮挡”的证明。通知异步交付，但不保证回调在主线程之外执行。

## 音频、视频和链接要保留什么语义？

`<audio>` 与 `<video>` 用于可播放媒体；提供 `controls`，让用户能启动、暂停和调整播放。媒体格式和编解码器支持因浏览器与平台而异，可按目标环境提供多个 `<source>`。`preload` 是加载偏好提示，实际请求仍由用户代理策略决定；`autoplay` 也是播放请求，可能受自动播放策略限制。

~~~html
<audio controls preload="metadata">
  <source src="/media/summary.ogg" type="audio/ogg">
  <source src="/media/summary.mp3" type="audio/mpeg">
</audio>

<video controls preload="metadata" width="640" height="360"
       poster="/media/preview.jpg">
  <source src="/media/demo.webm" type="video/webm">
  <source src="/media/demo.mp4" type="video/mp4">
  <track kind="captions" src="/media/demo.zh.vtt" srclang="zh" label="中文字幕">
</video>
~~~

给视频标出宽高或比例，降低播放器加入布局时的跳动；字幕通过 `<track>` 提供。音频与视频用 controls 表达播放交互，不要把视觉样式当成媒体控件语义。

对旧浏览器缺少 IntersectionObserver 的页面，才考虑滚动和 resize 几何检查作为回退；该方式应节流：挂载时先检查一次，在 scroll/resize 时合并检查；组件卸载时移除监听器并取消尚未执行的定时检查，避免保留 DOM 引用。矩形判断复用[DOM 几何 API](../html-css/dom-properties.md)中矩形的实际测量边界。性能比较应看真实路由和设备数据，见[浏览器性能测量](../performance/performance-metrics-and-analysis.md)与[浏览器如何把 URL 绘制成像素](../browser/browser-basics.md)。

> [!info]- 来源
> - 文档基准 URL、相对 URL 解析与链接：WHATWG HTML Living Standard（2026-11-05 更新），[Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)、[Links](https://html.spec.whatwg.org/multipage/links.html#link-type-noopener)；URL Standard，[Basic URL parser](https://url.spec.whatwg.org/#concept-basic-url-parser)。
> - `picture`、`source`、`img`、音视频元素：同一 WHATWG HTML Living Standard，[Embedded content](https://html.spec.whatwg.org/multipage/embedded-content.html) 与 [Media elements](https://html.spec.whatwg.org/multipage/media.html)，检查于 2026-11-06。
> - `loading` 与图片资源加载：WHATWG HTML Living Standard，[Lazy loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes)，检查于 2026-11-06。
> - 图片信息、装饰图片和功能图片的 `alt`：W3C WAI [Images Tutorial](https://www.w3.org/WAI/tutorials/images/)，检查于 2026-11-06。
> - 图片作为 LCP 内容与加载优先级：Google Chrome for Developers，[Optimize Largest Contentful Paint](https://web.dev/articles/optimize-lcp#optimize_when_the_lcp_element_is_an_image)，最后更新 2025-03-31，检查于 2026-11-06。
> - 相交矩形、边缘相接和 `rootMargin`：W3C [Intersection Observer](https://www.w3.org/TR/intersection-observer/)，Working Draft，2023-10-18。
> - 视口矩形 API：W3C [CSSOM View](https://www.w3.org/TR/cssom-view-1/)，Working Draft，2025-09-16。
