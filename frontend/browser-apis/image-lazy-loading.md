**Image Lazy Loading / 浏览器图片懒加载**

Use native lazy loading for ordinary off-screen images; choose `IntersectionObserver` only when code must control the loading decision. 原生懒加载适合普通图片；只有确实需要自定义加载时机时才引入观察器。

## How do you lazy-load images in the browser?

**Headline (30s):** Prefer native `loading="lazy"` for an image with a real `src` or `srcset`. Use `IntersectionObserver` when you need custom thresholds, roots, or non-image work. A scroll handler is a fallback only when the observer is unavailable. **中文：** 原生属性必须配合图片源；观察器用于自定义交集策略；滚动监听只作兼容性回退。

**Why interviewers ask this:** It's a common real-world perf question and a great filter for "do you know modern browser APIs or are you still writing jQuery-era scroll listeners?" The follow-up usually digs into CLS (Cumulative Layout Shift) and how to avoid jank when images pop in.

---

## 1. Native lazy loading (preferred)

Current browser engines support `loading="lazy"` for `<img>` and `<iframe>`; check the browsers your product targets when supporting older engines:

```html
<img src="image.jpg" alt="Description" loading="lazy" width="800" height="600">
```

Values:

- `lazy` — ask the user agent to defer fetching until its visibility conditions are met.
- `eager` — request loading without lazy deferral (the default state).
- `data-src` is not a native loading source. An `<img>` needs `src` or `srcset`; the browser cannot load the URL stored only in a `data-*` attribute.

**Why this is the first choice:**

- Zero JavaScript, zero bundle cost.
- The browser controls the deferral threshold, which may vary by implementation.
- No JavaScript observer or scroll listener is required for this common case.

**Include intrinsic `width` and `height`:** together they let the browser reserve an aspect ratio before the image loads, reducing layout shifts. CSS can still change the rendered size.

---

## 2. `IntersectionObserver` (JS fallback / more control)

When you need behaviors the native attribute does not cover—such as a custom root, a threshold, or loading work beyond an `<img>`—use `IntersectionObserver`. It reports queued intersection changes; the API does not promise that callback code runs off the main thread.

```html
<img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="actual-image.jpg" alt="Description" width="800" height="600">
```

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);    // stop observing after scheduling the request
    }
  });
}, {
  rootMargin: '200px' // expand the root rectangle by 200px on each side
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});

// Call observer.disconnect() when the component or page owning it is disposed.
```

**Key options:**

- **`rootMargin`** — expand or shrink the root rectangle; positive values can trigger before the target reaches the root. Choose the distance from measured product behavior, not a universal constant.
- **`threshold`** — intersection ratios at which entries are queued. With `0`, an edge-adjacent intersection can have a zero-area intersection rectangle, so `isIntersecting` does not mean “at least one pixel is visible.”

**Why `IntersectionObserver` can help:** the browser batches intersection notifications instead of requiring application code to poll geometry on every scroll event. A geometry read can force style or layout work when rendering state is dirty; neither mechanism has a universal cost guarantee.

---

## 3. Scroll + throttle (legacy fallback only)

For a required environment without `IntersectionObserver`, a scroll/resize fallback can check `getBoundingClientRect()`. Feature-detect the API and test this fallback in the actual target browser.

```javascript
function throttle(fn, delay) {
  let timer = null;
  return function (...args) {
    if (timer) return;
    timer = setTimeout(() => {
      fn.apply(this, args);
      timer = null;
    }, delay);
  };
}

const checkImages = throttle(() => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    const rect = img.getBoundingClientRect();
    if (rect.bottom > 0 && rect.top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    }
  });
}, 100);

window.addEventListener('scroll', checkImages, { passive: true });
window.addEventListener('resize', checkImages, { passive: true });
checkImages(); // also handle images already near the viewport
```

**Gotcha — geometry reads are conditional work:** `getBoundingClientRect()` returns current geometry and may force pending style/layout updates. Avoid alternating DOM writes and reads in a hot loop; do not assume every call forces a full-page layout.

---

## Performance: don't trade loading speed for layout jank

Lazy-loading images is great — unless you introduce layout shift every time one appears. Rules to follow:

- **Do not lazy-load likely LCP or immediately visible images.** Deferring a critical image can delay presentation; use `loading="eager"` or omit the attribute when appropriate.
- **Reserve an aspect ratio** with intrinsic `width` / `height` or CSS `aspect-ratio` to reduce layout shifts.
- **Combine with `srcset` + modern formats** (WebP, AVIF). Lazy-loading an over-sized JPEG still wastes bandwidth.
- **Use a placeholder** (low-quality image placeholder, LQIP, or a solid color) so the user sees something while the real image loads.

```html
<img
  src="full-800.webp"
  srcset="full-400.webp 400w, full-800.webp 800w, full-1600.webp 1600w"
  sizes="(max-width: 600px) 100vw, 50vw"
  loading="lazy"
  width="800"
  height="600"
  alt="Describe the image's purpose">
```

**Rule of thumb:**

1. Use `loading="lazy"` with an actual `src` or `srcset`, appropriate `alt`, and intrinsic dimensions.
2. Use `IntersectionObserver` for a concrete custom-loading need; unobserve loaded targets and disconnect the observer when its owner is disposed.
3. Check layout stability and LCP in the page's real loading context; lazy-loading the wrong images can delay important content.

**See also:** [`11.1 Performance Metrics and Analysis`](../performance/performance-metrics-and-analysis.md) for Core Web Vitals and broader image-perf strategies, [`5.1 DOM Manipulation and Events`](./dom-manipulation-and-events.md) for `IntersectionObserver` in other use cases.

**Standards / 规范：** [WHATWG `img` element and source requirements](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element), [WHATWG lazy-loading attributes](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#lazy-loading-attributes), [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/), [CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/).
