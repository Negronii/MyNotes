# How do you measure and diagnose web performance problems? / 如何测量和诊断网页性能问题？

Start with the user-visible symptom, measure the affected route and interaction, and identify the dominant cost before changing code. Core Web Vitals describe field experience: LCP for loading, INP for interaction responsiveness, and CLS for visual stability. Lab traces help explain causes but are not a substitute for real-user data. / 从用户能感知的问题出发，测量受影响的页面与交互，并在改代码前找出主要成本。Core Web Vitals 用于描述真实用户体验：LCP 衡量加载，INP 衡量交互响应，CLS 衡量视觉稳定。实验室追踪有助于解释原因，但不能替代真实用户数据。

## What do the main metrics measure?

| Metric | User-visible outcome | Current “good” threshold |
|---|---|---:|
| **LCP** | Time until the largest visible image or text block is rendered | ≤ 2.5 s |
| **INP** | Responsiveness across page interactions during a visit | ≤ 200 ms |
| **CLS** | Unexpected layout movement during the page lifecycle | ≤ 0.1 |

Good thresholds are assessed at the 75th percentile of real visits, segmented by mobile and desktop. They are field-data thresholds, not guarantees that every visit feels fast. See [web.dev Web Vitals](https://web.dev/articles/vitals) and the metric definitions for [LCP](https://web.dev/articles/lcp), [INP](https://web.dev/articles/inp), and [CLS](https://web.dev/articles/cls).

Other milestones answer different questions:

| Milestone | Meaning |
|---|---|
| **FCP** | First text or image content is rendered |
| **DOMContentLoaded (DCL)** | Parsing completed and deferred/module scripts executed; it does not wait for images or async scripts |
| **load** | The document and dependent resources such as scripts, stylesheets, frames, and non-lazy images loaded |
| **TTFB** | Time until the first response byte begins arriving |

Do not assume these milestones always form one simple sequence with LCP. FID was retired as a Core Web Vital and replaced by INP; FCP, TTFB, long tasks, and TBT remain useful diagnostics but are not themselves current Core Web Vitals. See [DOMContentLoaded](https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event) and [load](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event) for their event boundaries.

## Field data and lab data answer different questions

Field data records actual routes, devices, networks, and interactions. Use it to check whether users improved, comparing the same device segment and percentile. Lab tools such as Lighthouse and DevTools make runs repeatable and expose likely causes before release, but a lab run does not represent every user's experience.

A load-only Lighthouse run has no real user interaction, so it cannot directly measure that visit's INP. Total Blocking Time is a lab diagnostic proxy, not the INP metric. A load trace can also miss layout shifts caused later by interaction. See [lab and field data differences](https://web.dev/articles/lab-and-field-data-differences).

## How do you find the dominant cost?

Capture enough context to reproduce a comparison: route, device, network conditions, browser, and whether the number is field or lab data. Then inspect the tool that matches the symptom.

| Symptom | Inspect first |
|---|---|
| Main content appears late | TTFB, redirects, critical request timing, and LCP resource discovery/render delay |
| Input feels delayed | Long main-thread tasks, event-handler work, and work scheduled after input |
| Content jumps | Missing image/embed dimensions, late-injected content, and font swaps |
| Route bundle is large | Emitted chunk contents and whether deferred code is actually split |

Use the Performance panel to inspect scripting, layout, paint, and interaction traces; Network to inspect request timing, transfer size, and cache behavior; React Profiler to inspect component work; and Lighthouse for a repeatable lab run. A score is a clue. Inspect the trace and user impact before choosing a fix, then measure the same route and interaction again.

For a first-screen issue, identify the actual LCP element and critical path. Make that resource discoverable promptly, avoid lazy-loading the LCP image, and reserve image/embed dimensions to reduce shifts. Defer below-the-fold images and non-critical code only when measurements show they compete with critical work. If a render-blocking stylesheet delays the LCP element, test whether inlining only the required initial styles helps; this adds bytes to the HTML and gives up separate stylesheet-cache reuse, so measure the trade-off ([web.dev resource-loading guidance](https://web.dev/learn/performance/optimize-resource-loading)). Server-rendered or static output can help some routes but does not guarantee a good LCP or INP.

HTTP freshness and validation are separate mechanisms; see [HTTP protocols and caching](../../engineering-foundations/networking/http-protocols-and-websockets.md) for their canonical explanation. For debounce and throttle behavior, see [Lodash timing utilities](../libraries/lodash.md). See [rendering and computation optimization](./rendering-and-computation-optimization.md) for virtual lists and React work, and [image lazy loading](../browser-apis/image-lazy-loading.md) for image policy.
