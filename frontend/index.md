# 前端

先跟着报表页面走完一次导航，再看筛选点击怎样改变下一帧。读完主线后，可以继续深入布局、JavaScript 数据与调用、异步任务，最后连接类型、构建和交付验证。

## 从问题开始

- [从输入 URL 到第一帧，发生了什么？](browser/browser-basics.md)——建议先读，沿同一个报表页面从地址栏走到画面出现。
- [一次操作怎样变成界面更新？](../review/index.md#一次操作怎样变成界面更新？)——沿事件处理、React 状态变化走到下一帧。
- [页面已经可见，为什么操作还很慢？](performance/performance-metrics-and-analysis.md)——从性能录制定位延迟落在哪一段。

## Reading order / 阅读顺序

### 从 URL 到第一帧

- [浏览器如何把 URL 变成第一帧？](browser/browser-basics.md)
- [每次 URL 变化都会加载新文档吗？](browser/browser-navigation-and-history.md)
- [脚本如何影响 HTML 解析与文档就绪？](html-css/browser-html-and-css.md)

### 从筛选点击到下一帧

- [DOM 事件如何传播，何时适合事件委托？](browser-apis/dom-manipulation-and-events.md)
- [浏览器 JavaScript 何时运行，画面何时更新？](runtime/event-loop.md)
- [React如何把一次用户操作变成界面更新？](frameworks/react-basics.md)
- [如何在React中组合组件与复用行为？](frameworks/react-component-composition.md)
- [如何让报表筛选在昂贵更新时保持响应？](frameworks/advanced-react.md)
- [React界面如何维护服务端数据与乐观更新的正确性？](frameworks/react-server-state-and-optimistic-updates.md)
- [React错误边界能恢复哪些失败？](frameworks/react-error-boundaries.md)
- [为什么一次 DOM 改动会增加布局或绘制工作？](html-css/rendering-pipeline-and-forced-layout.md)
- [如何测量并诊断网页性能问题？](performance/performance-metrics-and-analysis.md)
- [如何测量并减少不必要的React工作？](performance/react-rendering-optimization.md)
- [长报表列表何时适合虚拟滚动？](performance/rendering-and-computation-optimization.md)

### 结构、布局与可访问交互

- [How do semantic HTML forms support keyboard and assistive-technology users? / 语义化 HTML 表单如何支持键盘与辅助技术用户？](html-css/accessible-html-forms.md)
- [How does the CSS cascade decide which declaration applies? / CSS 级联如何决定最终生效的声明？](html-css/html-and-css-basics.md)
- [How does CSS calculate an element's box size? / CSS 如何计算元素盒子的尺寸？](html-css/box-model-and-bfc.md)
- [How does a block formatting context contain floats and margins? / 块格式化上下文如何约束浮动和外边距？](html-css/bfc-and-flow-containment.md)
- [Which CSS units and responsive layout rules fit the available space? / 哪些 CSS 单位与响应式布局规则适合当前空间？](html-css/responsive-css-units-and-layout.md)
- [Which CSS layout tool fits fixed and fluid content? / 固定与流动内容适合哪种 CSS 布局？](html-css/flex-and-grid-layout.md)
- [How do you center an element whose size is unknown? / 如何居中尺寸未知的元素？](html-css/css-interview-questions.md)
- [How do CSS positioning and stacking determine where an element appears? / CSS 定位与堆叠如何决定元素的显示位置？](html-css/css-position-display-and-animations.md)
- [What changes when an element is visually hidden with CSS? / 用 CSS 隐藏元素时会发生什么变化？](html-css/css-visibility-and-accessibility.md)
- [When should CSS use a transition or a keyframe animation? / CSS 应在何时使用 transition 或关键帧动画？](html-css/css-transitions-and-animations.md)
- [Which DOM geometry API answers which measurement question? / 哪个 DOM 几何 API 能回答哪种测量问题？](html-css/dom-properties.md)
- [How should a browser page lazy-load images without hurting LCP or layout stability? / 如何延迟加载图片而不损害 LCP 或布局稳定性？](browser-apis/image-lazy-loading.md)
- [When should small images be combined into a CSS sprite? / 何时应把多个小图片合并为 CSS Sprite？](performance/css-sprites-and-image-caching.md)

### JavaScript 的值、对象与调用

- [JavaScript 值如何转换、比较，并成为属性键？](javascript/javascript-types.md)
- [何时使用 Map、Set 或普通对象？](javascript/map-and-set.md)
- [JavaScript 数组操作如何处理空位、修改与复制？](javascript/arrays.md)
- [如何安全地深拷贝 JavaScript 值？](javascript/deep-copy-and-structured-clone.md)
- [How do var, let, and const differ? / var、let 与 const 有什么区别？](javascript/javascript-basics.md)
- [How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？](javascript/scope-and-closure.md)
- [How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？](javascript/objects-functions-and-prototypes.md)
- [How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？](javascript/this-and-function-binding.md)
- [What does new do when it constructs an object? / new 构造对象时做了什么？](javascript/construction-and-new.md)
- [How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？](javascript/proxy.md)
- [How does currying support partial application? / 柯里化如何支持部分应用？](javascript/currying-and-partial-application.md)
- [What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？](javascript/other-javascript-topics.md)
- [弱集合与弱引用能保证什么？](javascript/javascript-memory-weakmap-and-weakset.md)
- [JavaScript 对象为何会在不再有用后仍留在内存中？](runtime/javascript-garbage-collection-and-retained-objects.md)

### 异步任务与错误恢复

- [How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？](javascript/asynchronous-javascript.md)
- [How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？](javascript/chainable-task-queue.md)
- [How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？](javascript/iterators-and-generators.md)
- [Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？](javascript/error-handling.md)

### 类型、模块与构建产物

- [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](typescript/advanced-typescript.md)
- [How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？](typescript/generics.md)
- [What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？](typescript/utility-types.md)
- [Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？](typescript/decorators.md)
- [How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？](javascript/modules-and-host-boundaries.md)
- [How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？](javascript/modern-javascript-features.md)
- [How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？](tooling/build-tools.md)

### 浏览器状态、通信与流式结果

- [What is the difference between an HTMLCollection and a NodeList? / HTMLCollection 与 NodeList 有什么区别？](browser-apis/dom-collections.md)
- [How can a JavaScript event bus handle reentrancy? / JavaScript 事件总线如何处理重入？](browser-apis/event-bus-and-observer-patterns.md)
- [Where should browser state live: Web Storage or cookies? / 浏览器状态应放在哪里：Web Storage 还是 Cookie？](browser-apis/browser-storage-and-communication.md)
- [How do browser contexts communicate? / 浏览上下文之间如何通信？](browser-apis/browser-context-communication.md)
- [How does a native app expose capabilities to WebView JavaScript? / 原生应用如何向 WebView JavaScript 暴露能力？](browser-apis/webview-javascript-bridge.md)
- [How should a UI render a streamed answer without mistaking partial output for completion? / 界面如何呈现流式回答而不把部分内容误判为完成？](browser-apis/streaming-ux.md)
- [How can an analytics client reduce work and try to send events during navigation? / 分析客户端如何降低工作量并尝试在导航时发送事件？](performance/analytics-event-delivery-on-navigation.md)

### 框架、工具选择与交付验收

- [如何为产品选择前端框架？](frameworks/virtual-dom-and-framework-selection.md)
- [How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？](frameworks/react-routing-and-navigation.md)
- [How should a Next.js app render and route its pages? / Next.js应用应如何渲染页面并组织路由？](frameworks/next-js.md)
- [When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？](libraries/lodash.md)
- [When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？](libraries/ahooks.md)
- [What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？](testing/frontend-testing.md)
- [How can a Jest test verify behavior across an asynchronous boundary? / Jest 怎样验证跨异步边界的行为？](testing/jest-async-tests-and-mocks.md)

## 共享基础

通用算法、数据结构、网络、安全、Git 与团队实践集中在[工程基础](../engineering-foundations/index.md)，供前端与其他工程主题共同引用。
