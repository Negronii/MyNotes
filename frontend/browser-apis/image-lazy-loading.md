# How should a browser page lazy-load images without hurting LCP or layout stability? / 如何延迟加载图片而不损害 LCP 或布局稳定性？

For an ordinary off-screen image, prefer native `loading="lazy"` with a real `src` or `srcset`; the browser chooses its deferral threshold. Reserve the image's aspect ratio with `width`/`height` or CSS `aspect-ratio`. Use `IntersectionObserver` only when loading needs a custom root, threshold, or non-image action, and do not defer an image likely to be the page's LCP element. / 普通视口外图片优先使用带真实 `src` 或 `srcset` 的原生 `loading="lazy"`，由浏览器决定何时开始加载。通过 `width`/`height` 或 CSS `aspect-ratio` 预留图片纵横比。只有需要自定义 root、阈值或执行非图片操作时才使用 `IntersectionObserver`，且不要延迟可能成为页面 LCP 元素的图片。

## Native lazy loading / 原生懒加载

~~~html
<img src="image.jpg" alt="Description" loading="lazy" width="800" height="600">
~~~

`lazy` asks the user agent to defer fetching until its visibility conditions are met; `eager` requests without lazy deferral. A `data-src` attribute alone is not a loading source: the element needs `src` or `srcset`. Browser-selected thresholds vary by implementation. Intrinsic dimensions let the browser reserve the aspect ratio before bytes arrive; CSS can still change the rendered size.

## Custom loading with Intersection Observer / 用观察器自定义加载

Use an observer for behavior the native attribute does not expose, such as a custom root margin, threshold, or work beyond an image request. It queues intersection changes; it does not promise that the callback runs off the main thread.

~~~html
<img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="actual-image.jpg" alt="Description" width="800" height="600">
~~~

~~~javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const img = entry.target;
    img.src = img.dataset.src;
    img.removeAttribute("data-src");
    observer.unobserve(img);
  });
}, { rootMargin: "200px" });

document.querySelectorAll("img[data-src]").forEach((img) => observer.observe(img));
// On teardown, call observer.disconnect() when this page/component owns the observer.
~~~

A positive `rootMargin` can begin work before the target reaches the root. `threshold: 0` has an edge-adjacent case: an intersecting target can have a zero-area intersection rectangle, so `isIntersecting` does not mean at least one pixel is visible. Do not use that flag as a visibility or occlusion test.

## Legacy scroll fallback / 旧环境滚动回退

Use a scroll/resize fallback only when the required target browser lacks `IntersectionObserver`. It reads viewport geometry and should be throttled; geometry reads can force pending layout when state is dirty, but do not necessarily do so. See [DOM geometry APIs](../html-css/dom-properties.md) for the exact box and coordinate returned, and [Debounce and throttle / 防抖与节流](../libraries/lodash.md) for rate-limiting options.

~~~javascript
function checkImages() {
  document.querySelectorAll("img[data-src]").forEach((img) => {
    const rect = img.getBoundingClientRect();
    if (rect.bottom > 0 && rect.top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute("data-src");
    }
  });
}

let checkScheduled = false;
function scheduleImageCheck() {
  if (checkScheduled) return;
  checkScheduled = true;
  setTimeout(() => {
    checkScheduled = false;
    checkImages();
  }, 100);
}

window.addEventListener("scroll", scheduleImageCheck, { passive: true });
window.addEventListener("resize", scheduleImageCheck, { passive: true });
checkImages();
~~~

## Protect loading speed and visual stability / 保护加载速度与视觉稳定性

Do not blindly lazy-load the first visible or likely LCP image: delaying its fetch can increase LCP. Reserve image space using intrinsic dimensions or an aspect ratio to reduce layout shift; choose an appropriate responsive candidate with `srcset`/`sizes`, rather than loading an oversized source. A placeholder can avoid a blank region but does not replace dimension reservation. Measure the actual route and device; see [browser performance measurement](../performance/performance-metrics-and-analysis.md) and the [URL-to-pixels path](../browser/browser-basics.md).

**Standards / 规范：** [WHATWG image element and source requirements](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element); [WHATWG lazy-loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes); [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/); [CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/), checked 2026-11-05.
