# Frontend / 前端

Start with JavaScript and the browser runtime, then follow navigation, layout, and events into a React interface. The later questions cover diagnosis, testing, and delivery. / 先理解 JavaScript 与浏览器运行时，再沿导航、布局和事件走到 React 界面，最后学习诊断、测试与交付。

## Reading order / 阅读顺序

### JavaScript / JavaScript

- [How do var, let, and const differ? / var、let 与 const 有什么区别？](javascript/javascript-basics.md)
- [How do JavaScript values convert, compare, and become property keys? / JavaScript 值如何转换、比较并成为属性键？](javascript/javascript-types.md)
- [When should I use Map, Set, or an object? / 何时应使用 Map、Set 或普通对象？](javascript/map-and-set.md)
- [What do weak collections and weak references guarantee? / 弱集合和弱引用能保证什么？](javascript/javascript-memory-weakmap-and-weakset.md)
- [How do JavaScript array operations differ on holes, mutation, and copying? / JavaScript 数组操作对空位、修改和复制有何差异？](javascript/arrays.md)
- [How do Object and Array helper APIs copy or enumerate data? / Object 与 Array 辅助方法如何复制或枚举数据？](javascript/es6-new-methods.md)
- [What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？](javascript/other-javascript-topics.md)
- [How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？](javascript/modern-javascript-features.md)
- [How do optional access and destructuring handle missing values? / 可选访问和解构如何处理缺失值？](javascript/optional-chaining-and-destructuring.md)
- [How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？](javascript/modules-and-host-boundaries.md)

### Advanced JavaScript / JavaScript进阶

- [How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？](javascript/objects-functions-and-prototypes.md)
- [How does a JavaScript function get its this value? / JavaScript 函数的 this 值如何确定？](javascript/this-and-function-binding.md)
- [What does new do when it constructs an object? / new 构造对象时做了什么？](javascript/construction-and-new.md)
- [How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？](javascript/proxy.md)
- [How do lexical scope and closures preserve access to state? / 词法作用域与闭包如何保留对状态的访问？](javascript/scope-and-closure.md)
- [How do callbacks, Promises, and async functions compose asynchronous work? / 回调、Promise 与 async 函数如何组合异步任务？](javascript/asynchronous-javascript.md)
- [How does currying support partial application? / 柯里化如何支持部分应用？](javascript/currying-and-partial-application.md)
- [How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？](javascript/chainable-task-queue.md)
- [How do iterators and generators produce values on demand? / 迭代器与生成器如何按需产出值？](javascript/iterators-and-generators.md)
- [Where should a JavaScript error be recovered or reported? / JavaScript 错误应在哪一层恢复或上报？](javascript/error-handling.md)

### TypeScript / TypeScript

- [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](typescript/advanced-typescript.md)
- [What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？](typescript/utility-types.md)
- [How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？](typescript/generics.md)
- [Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？](typescript/decorators.md)

### Browser runtime / 浏览器运行时

- [When does browser JavaScript run relative to a frame? / 浏览器 JavaScript 如何与每一帧交错？](runtime/event-loop.md)
- [How can a JavaScript object stay in memory after it is no longer useful? / JavaScript 对象为什么在不再有用后仍会留在内存中？](runtime/javascript-garbage-collection-and-retained-objects.md)

### Browser / 浏览器

- [How does a browser turn a URL into pixels? / 浏览器如何把 URL 变成屏幕像素？](browser/browser-basics.md)
- [Does every URL change load a new document? / 每次 URL 变化都会加载新文档吗？](browser/browser-navigation-and-history.md)

### HTML and CSS / HTML与CSS

- [How does the CSS cascade decide which declaration applies? / CSS 级联如何决定最终生效的声明？](html-css/html-and-css-basics.md)
- [Which CSS units and responsive layout rules fit the available space? / 哪些 CSS 单位与响应式布局规则适合当前空间？](html-css/responsive-css-units-and-layout.md)
- [How do semantic HTML forms support keyboard and assistive-technology users? / 语义化 HTML 表单如何支持键盘与辅助技术用户？](html-css/accessible-html-forms.md)
- [How does CSS calculate an element's box size? / CSS 如何计算元素盒子的尺寸？](html-css/box-model-and-bfc.md)
- [How does a block formatting context contain floats and margins? / 块格式化上下文如何约束浮动和外边距？](html-css/bfc-and-flow-containment.md)
- [Which CSS layout tool fits fixed and fluid content? / 固定与流动内容适合哪种 CSS 布局？](html-css/flex-and-grid-layout.md)
- [How do scripts affect HTML parsing and document readiness? / 脚本如何影响 HTML 解析与文档就绪？](html-css/browser-html-and-css.md)
- [Why can a CSS change trigger layout, paint, or compositing work? / 为什么 CSS 改动会触发布局、绘制或合成工作？](html-css/rendering-pipeline-and-forced-layout.md)
- [Which DOM geometry API answers which measurement question? / 哪个 DOM 几何 API 能回答哪种测量问题？](html-css/dom-properties.md)
- [How do you center an element whose size is unknown? / 如何居中尺寸未知的元素？](html-css/css-interview-questions.md)
- [How do CSS positioning and stacking determine where an element appears? / CSS 定位与堆叠如何决定元素的显示位置？](html-css/css-position-display-and-animations.md)
- [What changes when an element is visually hidden with CSS? / 用 CSS 隐藏元素时会发生什么变化？](html-css/css-visibility-and-accessibility.md)
- [When should CSS use a transition or a keyframe animation? / CSS 应在何时使用 transition 或关键帧动画？](html-css/css-transitions-and-animations.md)

### Browser APIs / 浏览器API

- [How do DOM events propagate, and when does delegation work? / DOM 事件如何传播，何时适合事件委托？](browser-apis/dom-manipulation-and-events.md)
- [How can a JavaScript event bus handle reentrancy? / JavaScript 事件总线如何处理重入？](browser-apis/event-bus-and-observer-patterns.md)
- [How do you deep-copy a JavaScript value safely? / 如何安全地深拷贝 JavaScript 值？](javascript/deep-copy-and-structured-clone.md)
- [Where should browser state live: Web Storage or cookies? / 浏览器状态应放在哪里：Web Storage 还是 Cookie？](browser-apis/browser-storage-and-communication.md)
- [What is the difference between an HTMLCollection and a NodeList? / HTMLCollection 与 NodeList 有什么区别？](browser-apis/dom-collections.md)
- [How do browser contexts communicate? / 浏览上下文之间如何通信？](browser-apis/browser-context-communication.md)
- [How does a native app expose capabilities to WebView JavaScript? / 原生应用如何向 WebView JavaScript 暴露能力？](browser-apis/webview-javascript-bridge.md)
- [How should a browser page lazy-load images without hurting LCP or layout stability? / 如何延迟加载图片而不损害 LCP 或布局稳定性？](browser-apis/image-lazy-loading.md)
- [How should a UI render a streamed answer without mistaking partial output for completion? / 界面如何呈现流式回答而不把部分内容误判为完成？](browser-apis/streaming-ux.md)

### React and frameworks / React与框架

- [How should I choose a frontend framework for a product? / 如何为产品选择前端框架？](frameworks/virtual-dom-and-framework-selection.md)
- [How does React turn a user action into an updated interface? / React如何把用户操作变成更新后的界面？](frameworks/react-basics.md)
- [Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？](frameworks/react-error-boundaries.md)
- [How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？](frameworks/react-routing-and-navigation.md)
- [How do I compose components and reusable behavior around an interaction? / 如何围绕交互组合组件与可复用行为？](frameworks/react-component-composition.md)
- [How can a React search interface stay responsive as results update? / React搜索界面如何在更新结果时保持响应？](frameworks/advanced-react.md)
- [How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？](frameworks/react-server-state-and-optimistic-updates.md)
- [How should a Next.js app render and route its pages? / Next.js应用应如何渲染页面并组织路由？](frameworks/next-js.md)

### Libraries / 库

- [When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？](libraries/lodash.md)
- [When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？](libraries/ahooks.md)

### Performance / 性能

- [How do you measure and diagnose web performance problems? / 如何测量和诊断网页性能问题？](performance/performance-metrics-and-analysis.md)
- [How can an analytics client reduce work and try to send events during navigation? / 分析客户端如何降低工作量并尝试在导航时发送事件？](performance/analytics-event-delivery-on-navigation.md)
- [When does virtual scrolling help a long list? / 长列表何时适合使用虚拟滚动？](performance/rendering-and-computation-optimization.md)
- [How should you reduce unnecessary React rendering work? / 如何减少不必要的 React 渲染工作？](performance/react-rendering-optimization.md)
- [When should small images be combined into a CSS sprite? / 何时应把多个小图片合并为 CSS Sprite？](performance/css-sprites-and-image-caching.md)

### Testing / 测试

- [What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？](testing/frontend-testing.md)
- [How can a Jest test verify behavior across an asynchronous boundary? / Jest 怎样验证跨异步边界的行为？](testing/jest-async-tests-and-mocks.md)

### Build tooling / 构建工具链

- [How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？](tooling/build-tools.md)

## Shared foundations / 共享基础

通用算法、数据结构、网络、安全、Git 与团队实践集中在 [Engineering Foundations / 工程基础](../engineering-foundations/index.md)，供前端与其他工程主题共同引用。
