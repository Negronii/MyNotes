# 前端

先跟着报表页面走完一次导航，再看筛选点击怎样改变下一帧。读完主线后，可以继续深入布局、JavaScript 数据与调用、异步任务，最后连接类型、构建和交付验证。

## 从问题开始

- [浏览器如何把 URL 变成第一帧？](browser/browser-basics.md)——建议先读，沿同一个报表页面从地址栏走到画面出现。
- [一次操作怎样变成界面更新？](../review/index.md#%E4%B8%80%E6%AC%A1%E6%93%8D%E4%BD%9C%E6%80%8E%E6%A0%B7%E5%8F%98%E6%88%90%E7%95%8C%E9%9D%A2%E6%9B%B4%E6%96%B0%EF%BC%9F)——先看原生事件与调度，再切换到同一筛选意图的 React 实现，沿状态提交走到下一帧。
- [页面已经可见，为什么操作还很慢？](performance/performance-metrics-and-analysis.md)——从性能录制定位延迟落在哪一段。

## Reading order / 阅读顺序

### 从 URL 到第一帧

- [浏览器如何把 URL 变成第一帧？](browser/browser-basics.md)
- [每次 URL 变化都会加载新文档吗？](browser/browser-navigation-and-history.md)
- [脚本如何影响 HTML 解析与文档就绪？](html-css/browser-html-and-css.md)

### 从筛选点击到下一帧

- [浏览器怎样查询、更新 DOM 并响应用户输入？](browser-apis/dom-manipulation-and-events.md)
- [浏览器 JavaScript 何时运行，画面何时更新？](runtime/event-loop.md)
- [React如何把一次用户操作变成界面更新？](frameworks/react-basics.md)
- [如何在 React 中组合组件与复用行为？](frameworks/react-component-composition.md)
- [如何让报表筛选在昂贵更新时保持响应？](frameworks/advanced-react.md)
- [React界面如何维护服务端数据与乐观更新的正确性？](frameworks/react-server-state-and-optimistic-updates.md)
- [管理表格打开多步骤编辑后，怎样在查询变化与提交冲突中保住用户意图？](frameworks/management-table-and-form-workflows.md)
- [React错误边界能恢复哪些失败？](frameworks/react-error-boundaries.md)
- [为什么一次 DOM 改动会增加布局或绘制工作？](html-css/rendering-pipeline-and-forced-layout.md)
- [如何测量并诊断网页性能问题？](performance/performance-metrics-and-analysis.md)
- [如何测量并减少不必要的React工作？](performance/react-rendering-optimization.md)
- [长报表列表何时适合虚拟滚动？](performance/rendering-and-computation-optimization.md)

### 结构、布局与可访问交互

- [语义化 HTML 表单如何支持键盘与辅助技术用户？](html-css/accessible-html-forms.md)
- [CSS 级联如何决定最终生效的声明？](html-css/html-and-css-basics.md)
- [CSS 如何计算元素盒子的尺寸？](html-css/box-model-and-bfc.md)
- [块格式化上下文如何约束浮动和外边距？](html-css/bfc-and-flow-containment.md)
- [哪些 CSS 单位与响应式布局规则适合当前空间？](html-css/responsive-css-units-and-layout.md)
- [固定与流动内容适合哪种 CSS 布局？](html-css/flex-and-grid-layout.md)
- [定位如何确定元素位置与前后顺序？](html-css/css-position-display-and-animations.md)
- [隐藏状态会怎样影响焦点与可访问性？](html-css/css-visibility-and-accessibility.md)
- [何时使用过渡，何时使用关键帧动画？](html-css/css-transitions-and-animations.md)
- [哪些网页几何接口能测量哪一种盒子？](html-css/dom-properties.md)
- [图片与媒体资源怎样加载并保持页面稳定？](browser-apis/image-lazy-loading.md)
- [怎样为报表图标选择资源形式？](performance/css-sprites-and-image-caching.md)

### JavaScript 的值、对象与调用

- [JavaScript 值如何转换、比较，并成为属性键？](javascript/javascript-types.md)
- [何时使用 Map、Set 或普通对象？](javascript/map-and-set.md)
- [JavaScript 数组操作如何处理空位、修改与复制？](javascript/arrays.md)
- [如何安全地深拷贝 JavaScript 值？](javascript/deep-copy-and-structured-clone.md)
- [JavaScript 作用域与闭包如何保留状态？](javascript/scope-and-closure.md)
- [JavaScript 对象如何查找属性并组织成员？](javascript/objects-functions-and-prototypes.md)
- [JavaScript 函数的 `this` 值由什么决定？](javascript/this-and-function-binding.md)
- [JavaScript 的 `new` 如何构造对象？](javascript/construction-and-new.md)
- [JavaScript 的 `Proxy` 如何拦截对象操作？](javascript/proxy.md)
- [函数变换如何改变调用过程？](javascript/currying-and-partial-application.md)
- [弱集合与弱引用能保证什么？](javascript/javascript-memory-weakmap-and-weakset.md)
- [JavaScript 对象为何会在不再有用后仍留在内存中？](runtime/javascript-garbage-collection-and-retained-objects.md)

### 异步任务与错误恢复

- [回调、Promise 与 async 函数怎样组合异步工作？](javascript/asynchronous-javascript.md)
- [怎样限制异步任务的并发并收尾失败？](javascript/bounded-async-concurrency.md)
- [链式接口如何先排队、再依次执行延后任务？](javascript/chainable-task-queue.md)
- [迭代器与生成器怎样按需产出并清理数据？](javascript/iterators-and-generators.md)
- [JavaScript 错误应在哪一层恢复、传播或上报？](javascript/error-handling.md)

### 类型、模块与构建产物

- [收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](typescript/advanced-typescript.md)
- [泛型怎样保留输入与输出之间的类型关系？](typescript/generics.md)
- [怎样从报表类型派生数据形状并约束方法中的 `this`？](typescript/utility-types.md)
- [项目使用哪种 TypeScript 装饰器模式？](typescript/decorators.md)
- [ECMAScript 模块与 CommonJS（Node.js 模块格式）在语法、加载和运行时有什么不同？](javascript/modules-and-host-boundaries.md)
- [怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？](javascript/modern-javascript-features.md)
- [构建工具怎样把源码变成可发布产物？](tooling/build-tools.md)

### 浏览器状态、通信与流式结果

- [报表页面里的状态应该放在哪里？](browser-apis/browser-storage-and-communication.md)
- [同一报表在多个标签页中怎样交换变化？](browser-apis/browser-context-communication.md)
- [流式报表断线重连后，界面怎样保留正确状态？](browser-apis/streaming-ux.md)
- [一轮 AI 聊天怎样安全地展示增量回答、工具状态与恢复操作？](browser-apis/streaming-ai-chat.md)
- [JavaScript 事件总线在监听器中重入时怎样保持顺序？](browser-apis/event-bus-and-observer-patterns.md)
- [修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](browser-apis/dom-collections.md)
- [用户离开报表页时，分析事件怎样尽力发送？](performance/analytics-event-delivery-on-navigation.md)
- [WebView 怎样安全地开放原生能力并更新页面包？](browser-apis/webview-javascript-bridge.md)

### 框架、工具选择与交付验收

- [Redux 如何组织共享界面状态与异步工作？](frameworks/redux-state-and-async-workflows.md)
- [如何为产品选择前端框架？](frameworks/virtual-dom-and-framework-selection.md)
- [React 路由怎样把地址映射到界面并加载数据？](frameworks/react-routing-and-navigation.md)
- [Next.js 如何把文件路由、服务端数据与客户端交互连接起来？](frameworks/next-js.md)
- [Lodash 何时适合处理报表列表，哪些方法会修改输入？](libraries/lodash.md)
- [ahooks 怎样管理报表请求、分页与列表身份？](libraries/ahooks.md)
- [前端测试怎样证明报表排序、历史恢复和发布产物正确？](testing/frontend-testing.md)
- [Jest 怎样验证报表请求中的异步状态和结果？](testing/jest-async-tests-and-mocks.md)

## 共享基础

通用算法、数据结构、网络、安全、Git 与团队实践集中在[工程基础](../engineering-foundations/index.md)，供前端与其他工程主题共同引用。
