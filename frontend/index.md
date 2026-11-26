# 前端

浏览器在一条事件循环里把 URL、HTML、CSS 和 JavaScript 变成可交互的像素。前端工程要让每份状态有唯一的所有者、让每个异步结果按身份落到对的界面上，并用测量和测试证明页面对所有用户都正确、够快。

第一次读，从[打开一个 URL 后，页面怎样变得可见又可交互？](browser/from-url-to-interactive-page.md)开始。它建立全领域共用的报表页案例：一张能按“最近优先 / 最早优先”排序的报表，后面各条主线分别看它的首帧与点击、布局与表单、数据与请求代码、编辑与并发保存、构建发布与性能。

## 五条主线

### 一、页面怎样在浏览器里运行？

浏览器先从 URL 取回 HTML，边解析边发现 CSS、脚本和图片；首帧可见与处理器就绪是两条不同的线。事件循环按任务、微任务和渲染机会安排工作；一次点击沿 DOM 传播到处理器，处理器改 DOM 后，浏览器只重算失效的那部分布局和绘制，读几何值可能迫使它提前同步计算。地址分量各有分工：只有该分享、该恢复的界面状态才写进 URL。

- [打开一个 URL 后，页面怎样变得可见又可交互？](browser/from-url-to-interactive-page.md)
- [事件循环怎样安排任务、微任务和渲染？](browser/event-loop-tasks-and-rendering.md)
- [怎样查询和修改 DOM，才拿到并改到预期的节点？](browser/dom-queries-and-updates.md)
- [一次点击怎样传播到处理器，处理器该怎样注册和清理？](browser/dom-events.md)
- [DOM 改动后浏览器重做了什么，读几何值为什么会卡住脚本？](browser/rendering-pipeline-and-forced-layout.md)
  - 支线：[图片和音视频该怎样写语义、定地址、选文件和定加载时机？](browser/images-and-media-loading.md)
- [地址变了，浏览器什么时候加载新文档，界面状态何时该写进 URL？](browser/navigation-history-and-url-state.md)
  - 支线：[嵌入原生应用的页面，怎样安全地调用原生能力并更新页面包？](browser/webview-javascript-bridge.md)

### 二、HTML 和 CSS 怎样决定页面的结构、外观和谁能用它？

结构与语义决定读屏、键盘和搜索看到什么，焦点顺序跟随源码；表单靠可见名称、原生控件和明确的提交规则对所有人可用。层叠和继承决定每个属性的值；盒模型、正常流、Flex 与 Grid 决定空间怎样分配，定位与堆叠决定谁参照谁、谁盖住谁。响应式规则按视口、容器和用户设置调整布局；隐藏与动效都要同时照顾布局、指针、焦点和读屏。

- [页面结构怎样让所有人都能读懂和操作？](html-css/semantic-structure-and-accessibility.md)
- [表单控件怎样命名、提交和校验，才对所有人可用？](html-css/accessible-forms-and-submission.md)
- [多条 CSS 声明冲突时谁赢，没有声明时值又从哪来？](html-css/css-cascade-and-inheritance.md)
- [盒子的尺寸怎样计算，块和浮动怎样在流里排开？](html-css/box-model-and-normal-flow.md)
- [Flex 和 Grid 怎样把空间分给每个项目？](html-css/flex-and-grid-layout.md)
- [定位元素参照谁，为什么大 z-index 还会被盖住？](html-css/positioning-and-stacking.md)
- [页面怎样响应视口、容器和用户设置？](html-css/responsive-units-and-layout.md)
- [隐藏内容时，布局、指针、焦点和读屏各受什么影响？](html-css/hiding-content-and-focus.md)
- [过渡和关键帧动画怎样选，怎样不伤性能和可访问性？](html-css/transitions-and-animations.md)

### 三、JavaScript 与 TypeScript 的值、对象、函数和异步按什么规则工作？

值与对象：相等有三种规则，属性读写沿原型链查找并按描述符落点，集合与复制要先定义“相同”和对象图。函数与异步：变量来自词法环境，this 来自调用形式；Promise 链传递值和失败，取消、超时与并发上限各自只停得住一部分；失败交给有上下文的那一层。程序与运行时：模块由宿主定位、链接和执行，对象按可达性回收；TypeScript 只在编译期检查，外部数据仍要在运行时验证。

- [JavaScript 的值有哪些类型，“相等”又有几种？](javascript/values-types-and-equality.md)
- [读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](javascript/objects-properties-and-prototypes.md)
  - 支线：[new 一个对象时发生了什么？](javascript/construction-and-new.md)
  - 支线：[Proxy 能拦截什么，又在哪里拦不住？](javascript/proxy-and-reflect.md)
- [数组、Map、Set 和普通对象怎样选，空位和去重有哪些坑？](javascript/arrays-maps-and-sets.md)
- [复制一个对象到底复制了什么？](javascript/copying-and-object-graphs.md)
- [函数里的变量和 this 从哪来？](javascript/scope-closures-and-this.md)
- [怎样包装一个函数而不弄丢参数、this 和结果？](javascript/wrapping-functions.md)
  - 支线：[同步事件总线在分发途中增删监听器会怎样？](javascript/event-bus-and-observer-patterns.md)
- [Promise 和 async 函数怎样传递值和失败？](javascript/promises-and-async-functions.md)
- [取消、超时和并发上限各自停得住什么？](javascript/cancellation-timeouts-and-concurrency.md)
  - 支线：[迭代器和生成器怎样按需产出值，提前退出时怎样清理？](javascript/iterators-and-generators.md)
- [一次失败该由哪一层处理？](javascript/error-handling-across-layers.md)
- [import 写下后，谁负责找到、链接和执行文件？](javascript/modules-and-host-boundaries.md)
  - 支线：[用一个新 API 之前，怎样确认运行时真的支持？](javascript/feature-availability.md)
- [对象什么时候能被回收，弱引用能帮什么、不能帮什么？](javascript/memory-reachability-and-weak-references.md)
- [TypeScript 能保证什么，外部数据又该怎样验证？](javascript/typescript-guarantees-and-runtime-validation.md)
  - 支线：[泛型和工具类型怎样从已有类型推出新类型？](javascript/typescript-generics-and-utility-types.md)
  - 支线：[TypeScript 的两种装饰器模式有什么不同？](javascript/typescript-decorators.md)

### 四、界面状态归谁，异步结果怎样按身份落到对的界面上？

React 把一次操作拆成快照、render、commit 和绘制，key 决定状态属于谁。每份状态只有一个所有者：URL、查询缓存、全局 store、编辑会话、组件或服务端。路由只把已提交的导航交给界面；迟到的响应按请求身份归属，不按到达顺序覆盖。并发保存靠条件写入和三方合并；昂贵更新可以延后，错误由能恢复的那一层接住。跨标签页的通知和服务端推送都只是提示，最终要向权威核实。

- [React 怎样把一次用户操作变成界面更新？](ui-state/react-update-model.md)
  - 支线：[虚拟 DOM 到底声明了什么，框架该怎样选？](ui-state/virtual-dom-and-framework-selection.md)
- [一份界面状态该由谁持有？](ui-state/state-ownership-and-composition.md)
- [路由怎样把 URL 变成已提交的数据和界面？](ui-state/routing-and-loaders.md)
  - 支线：[Next.js App Router 怎样把服务端渲染、缓存和客户端交互分开？](ui-state/next-js-app-router.md)
- [服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](ui-state/server-state-and-optimistic-updates.md)
  - 支线：[Redux 怎样管理跨组件的客户端状态和异步请求？](ui-state/redux-state-and-async-workflows.md)
- [编辑表单怎样在别人同时修改时安全保存？](ui-state/editing-sessions-and-conditional-writes.md)
- [昂贵更新时，怎样让输入保持即时？](ui-state/urgent-and-deferred-updates.md)
- [错误发生在哪里，决定了谁能接住它？](ui-state/react-error-boundaries.md)
- [浏览器能把状态存在哪里，标签页和窗口之间怎样互相通知？](ui-state/browser-storage-and-cross-context-messaging.md)
- [服务端持续推送时，界面怎样合并更新并从断线恢复？](ui-state/streaming-updates-and-resume.md)
  - 支线：[AI 聊天界面怎样应用重放事件、安全渲染 Markdown，并处理停止与重试？](ui-state/streaming-ai-chat.md)

### 五、前端代码怎样构建、测试、发布，并测出慢在哪里？

构建器把源码图变成带哈希的文件；发布时成组上传、最后切换入口，旧页面仍能取到旧文件，缓存按文件类别分别设置。测试按风险分层，证明页面真的用了对应的响应，并测将要发布的那份产物。用户觉得慢时，先从现场指标和症状找到慢的阶段，再改渲染或列表规模，并用同一口径复测。

- [构建器怎样把源码变成可部署的文件？](delivery/build-pipeline-and-bundling.md)
- [发布新版本时，怎样让缓存和还开着的旧页面都不出错？](delivery/hashed-release-and-caching.md)
  - 支线：[图标该用行内 SVG、外部图片、雪碧图还是图标字体？](delivery/icon-delivery.md)
- [前端测试该在哪一层证明什么？](delivery/frontend-testing-strategy.md)
- [异步代码和外部依赖怎样测才可信？](delivery/async-tests-and-mocks.md)
- [用户觉得慢时，怎样从指标走到证据？](delivery/performance-metrics-and-diagnosis.md)
  - 支线：[页面离开时，分析事件怎样尽力送出，又能确认什么？](delivery/analytics-events-on-page-exit.md)
- [React 渲染慢时，先改什么？](delivery/react-rendering-optimization.md)
- [长列表的成本在哪里，分页和虚拟化各省掉什么？](delivery/long-lists-pagination-and-virtualization.md)

## Reading order / 阅读顺序

### 页面怎样在浏览器里运行？

- [打开一个 URL 后，页面怎样变得可见又可交互？](browser/from-url-to-interactive-page.md)
- [事件循环怎样安排任务、微任务和渲染？](browser/event-loop-tasks-and-rendering.md)
- [怎样查询和修改 DOM，才拿到并改到预期的节点？](browser/dom-queries-and-updates.md)
- [一次点击怎样传播到处理器，处理器该怎样注册和清理？](browser/dom-events.md)
- [DOM 改动后浏览器重做了什么，读几何值为什么会卡住脚本？](browser/rendering-pipeline-and-forced-layout.md)
- [图片和音视频该怎样写语义、定地址、选文件和定加载时机？](browser/images-and-media-loading.md)
- [地址变了，浏览器什么时候加载新文档，界面状态何时该写进 URL？](browser/navigation-history-and-url-state.md)
- [嵌入原生应用的页面，怎样安全地调用原生能力并更新页面包？](browser/webview-javascript-bridge.md)

### HTML 和 CSS 怎样决定页面的结构、外观和谁能用它？

- [页面结构怎样让所有人都能读懂和操作？](html-css/semantic-structure-and-accessibility.md)
- [表单控件怎样命名、提交和校验，才对所有人可用？](html-css/accessible-forms-and-submission.md)
- [多条 CSS 声明冲突时谁赢，没有声明时值又从哪来？](html-css/css-cascade-and-inheritance.md)
- [盒子的尺寸怎样计算，块和浮动怎样在流里排开？](html-css/box-model-and-normal-flow.md)
- [Flex 和 Grid 怎样把空间分给每个项目？](html-css/flex-and-grid-layout.md)
- [定位元素参照谁，为什么大 z-index 还会被盖住？](html-css/positioning-and-stacking.md)
- [页面怎样响应视口、容器和用户设置？](html-css/responsive-units-and-layout.md)
- [隐藏内容时，布局、指针、焦点和读屏各受什么影响？](html-css/hiding-content-and-focus.md)
- [过渡和关键帧动画怎样选，怎样不伤性能和可访问性？](html-css/transitions-and-animations.md)

### JavaScript 与 TypeScript 的值、对象、函数和异步按什么规则工作？

- [JavaScript 的值有哪些类型，“相等”又有几种？](javascript/values-types-and-equality.md)
- [读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](javascript/objects-properties-and-prototypes.md)
- [new 一个对象时发生了什么？](javascript/construction-and-new.md)
- [Proxy 能拦截什么，又在哪里拦不住？](javascript/proxy-and-reflect.md)
- [数组、Map、Set 和普通对象怎样选，空位和去重有哪些坑？](javascript/arrays-maps-and-sets.md)
- [复制一个对象到底复制了什么？](javascript/copying-and-object-graphs.md)
- [函数里的变量和 this 从哪来？](javascript/scope-closures-and-this.md)
- [怎样包装一个函数而不弄丢参数、this 和结果？](javascript/wrapping-functions.md)
- [同步事件总线在分发途中增删监听器会怎样？](javascript/event-bus-and-observer-patterns.md)
- [Promise 和 async 函数怎样传递值和失败？](javascript/promises-and-async-functions.md)
- [取消、超时和并发上限各自停得住什么？](javascript/cancellation-timeouts-and-concurrency.md)
- [迭代器和生成器怎样按需产出值，提前退出时怎样清理？](javascript/iterators-and-generators.md)
- [一次失败该由哪一层处理？](javascript/error-handling-across-layers.md)
- [import 写下后，谁负责找到、链接和执行文件？](javascript/modules-and-host-boundaries.md)
- [用一个新 API 之前，怎样确认运行时真的支持？](javascript/feature-availability.md)
- [对象什么时候能被回收，弱引用能帮什么、不能帮什么？](javascript/memory-reachability-and-weak-references.md)
- [TypeScript 能保证什么，外部数据又该怎样验证？](javascript/typescript-guarantees-and-runtime-validation.md)
- [泛型和工具类型怎样从已有类型推出新类型？](javascript/typescript-generics-and-utility-types.md)
- [TypeScript 的两种装饰器模式有什么不同？](javascript/typescript-decorators.md)

### 界面状态归谁，异步结果怎样按身份落到对的界面上？

- [React 怎样把一次用户操作变成界面更新？](ui-state/react-update-model.md)
- [虚拟 DOM 到底声明了什么，框架该怎样选？](ui-state/virtual-dom-and-framework-selection.md)
- [一份界面状态该由谁持有？](ui-state/state-ownership-and-composition.md)
- [路由怎样把 URL 变成已提交的数据和界面？](ui-state/routing-and-loaders.md)
- [Next.js App Router 怎样把服务端渲染、缓存和客户端交互分开？](ui-state/next-js-app-router.md)
- [服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](ui-state/server-state-and-optimistic-updates.md)
- [Redux 怎样管理跨组件的客户端状态和异步请求？](ui-state/redux-state-and-async-workflows.md)
- [编辑表单怎样在别人同时修改时安全保存？](ui-state/editing-sessions-and-conditional-writes.md)
- [昂贵更新时，怎样让输入保持即时？](ui-state/urgent-and-deferred-updates.md)
- [错误发生在哪里，决定了谁能接住它？](ui-state/react-error-boundaries.md)
- [浏览器能把状态存在哪里，标签页和窗口之间怎样互相通知？](ui-state/browser-storage-and-cross-context-messaging.md)
- [服务端持续推送时，界面怎样合并更新并从断线恢复？](ui-state/streaming-updates-and-resume.md)
- [AI 聊天界面怎样应用重放事件、安全渲染 Markdown，并处理停止与重试？](ui-state/streaming-ai-chat.md)

### 前端代码怎样构建、测试、发布，并测出慢在哪里？

- [构建器怎样把源码变成可部署的文件？](delivery/build-pipeline-and-bundling.md)
- [发布新版本时，怎样让缓存和还开着的旧页面都不出错？](delivery/hashed-release-and-caching.md)
- [图标该用行内 SVG、外部图片、雪碧图还是图标字体？](delivery/icon-delivery.md)
- [前端测试该在哪一层证明什么？](delivery/frontend-testing-strategy.md)
- [异步代码和外部依赖怎样测才可信？](delivery/async-tests-and-mocks.md)
- [用户觉得慢时，怎样从指标走到证据？](delivery/performance-metrics-and-diagnosis.md)
- [页面离开时，分析事件怎样尽力送出，又能确认什么？](delivery/analytics-events-on-page-exit.md)
- [React 渲染慢时，先改什么？](delivery/react-rendering-optimization.md)
- [长列表的成本在哪里，分页和虚拟化各省掉什么？](delivery/long-lists-pagination-and-virtualization.md)

## 共享基础

通用算法、数据结构、网络、安全、Git 与团队实践集中在[工程基础](../engineering-foundations/index.md)，供前端与其他工程主题共同引用。AI 应用的运行恢复与外部写入见 [AI 工程](../ai-engineering/index.md)主线四。
