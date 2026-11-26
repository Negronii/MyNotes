# 虚拟 DOM 到底声明了什么，框架该怎样选？

选前端框架时，常听到“虚拟 DOM 更快”或“编译器没有运行时所以更快”。本章回答两件事：虚拟 DOM 这类界面描述到底声明了什么、没声明什么；以及为什么框架要用真实产品路径上的约束和测量来选，而不是用这些标签。读者已经知道 React 怎样经过 render、协调和 commit 更新 DOM，以及 `key` 怎样决定列表项的身份。

**案例。** 沿用主线一的报表页 `/reports/42?sort=recent#summary` 和 May、April 两行。用户点“最早优先”后，路由取回按 oldest 排好的数据，列表要变成 April、May。本章的比较从“路由已经交付新数组”开始，只看框架怎样把它变成 DOM 更新，不把请求耗时算到虚拟 DOM 头上。React 部分按 React 19.3 核对，Vue 按当前 Vue 3 官方指南、Svelte 按 Svelte 5 文档核对（2026-11-13）。

## 界面描述不是 DOM 的副本

所有界面框架都要把应用状态变成浏览器里的节点，但中间产物不一样：

- **React** 的组件 render 产生 element（元素），是描述“这里应该有什么”的普通对象。
- **Vue** 的模板被编译成渲染函数，运行时产生 VNode（virtual node，虚拟节点），同样是交给渲染器的描述。
- **Svelte** 没有这类运行时描述。编译器把组件转换成 JavaScript 模块，模块里的更新代码在状态变化时直接操作 DOM。

element 和 VNode 都不是浏览器 DOM 的副本，也不是现成的 DOM 节点。所谓 virtual DOM（虚拟 DOM），说的是“开发者声明界面应该是什么样，框架负责把新旧描述对应起来、算出要改哪些节点”。它声明的是**结果**，没有声明**成本**：它不意味着更新一定更快，也不意味着每次更新都重建真实 DOM。组件被再次调用，结果和上次相同时可以完全不改 DOM；DOM 改了以后浏览器是否重算样式、布局、重新绘制，又是另一回事。React 这三段的区分见[React 怎样把一次用户操作变成界面更新？](./react-update-model.md#render、commit%20和%20paint%20是三件事)。

## 同一次换序：三种框架怎样保住 May 的草稿

列表排序把两件事放在一起考验：数据顺序变了，条目身份没变。May 从第一位移到第二位，它的 `id` 仍是 `r-104`。三种框架都要求给列表项一个身份键，让它按身份而不是按位置对应前后两次输出。

为了单独观察身份，设一个小探针：页面、列表和每行组件都保持挂载，只替换路由交付的数组；每行有一个输入框，切换前 May 行输入了 `May draft`，焦点也在其中。排序用脚本触发，而不是鼠标点按钮，因为真实点击会先把焦点移到按钮上。新数组是 `[April, May]`。期望结果是：DOM 顺序变成 April、May，`May draft` 和焦点仍在 May 行的那个输入框里。

### React：元素 key 把 May 对应到新位置

React 用新数组重新计算一组 element。`key={report.id}` 让协调器在同一个父列表下，把旧的 May 对应到新列表第二位的 May；组件类型没变，行内 state 仍属于 May，React 移动原有的 `<li>` 和 `<input>`，草稿和焦点都跟着走。

~~~jsx
reports.map(report => <ReportRow key={report.id} report={report} />)
~~~

把 `key` 换成数组下标，第一位上原属 May 的输入框会被 April 复用，草稿和焦点留在第一个位置。key 的完整规则（包括下标 key 错位的逐行推演）见[React 怎样把一次用户操作变成界面更新？](./react-update-model.md#key%20决定状态属于谁)。

React 默认按普通优先级完成这次 render；只有触发更新的状态被显式标成 Transition 时，React 才可能中断这次 render 稍后重算，而且中断只发生在组件之间，不会打断正在运行的排序函数或点击处理器。路由是否把导航标成 Transition，由路由库决定。

### Vue：依赖变化触发重新渲染，再按 key 移动旧行

组件上次渲染时读过响应式的 `reports`，响应式系统记下了这个依赖。`reports` 被替换后，组件重新渲染，模板生成新的 VNode 列表。模板编译器能提前标出静态部分和动态绑定（静态提升、patch flags），但列表顺序只有运行时才知道，仍要由渲染器协调。`v-for` 上的 `:key="report.id"` 让渲染器把旧的 May VNode 及其 DOM 对应到新数组的第二位，移动已有的行节点，输入框里仍是 `May draft`。

~~~vue
<li v-for="report in reports" :key="report.id">
  <ReportRow :report="report" />
</li>
~~~

没有 key 时，Vue 默认按位置原地更新（patch），输入状态就会和 May 的内容错开。Vue 还会把同一时刻的多次状态变化缓冲到下一个 tick 再统一更新 DOM。

### Svelte：编译出更新点，运行时按键重排

Svelte 编译器把模板和对状态的引用转换成更新代码；收到新的 `reports` 数组时，受影响的模板块执行更新。若页面改为从本地数组自行排序，Svelte 5 的 `$derived` 会在读取状态时记录依赖，依赖变化后在下次读取时重算。编译器事先知道哪些绑定可能要更新，但不知道这次 `reports` 的值和顺序，所以列表仍要在运行时对应。

~~~svelte
{#each reports as report (report.id)}
  <ReportRow {report} />
{/each}
~~~

带键的 `#each` 块在运行时按 `report.id` 对应各行，把 May 块从第一位移到第二位，而不是在第一位上改写内容。Svelte 不经过 VNode 描述和协调，但结果相同：DOM 顺序变为 April、May，草稿仍属于 May。

### 探针证明了什么

一个独立的 React 浏览器探针确认了稳定 ID 作 key 和下标作 key 的差异：前者让 May 的输入值、同一个 DOM 节点和焦点都跟着 May，后者把它们留在第一个位置。Vue 和 Svelte 的文档说明带 key 的列表会按身份复用和移动条目，但没有在这两个框架里实测焦点。产品验收应在选定版本的真实浏览器里检查重排后 May 的输入值、DOM 节点和 `document.activeElement`（当前活动元素）。

三种模型的结论是同一个：**列表身份由你提供的键决定，与有没有虚拟 DOM 无关。** 键也只在列表子树持续挂载时起作用；路由若卸载了整个列表，草稿要由更高层的所有者保存。

## 写进 DOM 之后，框架管不到什么

三种框架都只负责把变化写进 DOM。写入之后，浏览器仍要计算样式、布局、绘制和合成。小列表换序若伴随复杂样式，瓶颈可能在浏览器；巨大列表即使框架本身计算很少，也可能因为真的创建了成千上万个节点而变慢。框架的更新次数、组件函数调用次数、DOM 写入次数和用户看到新画面的时刻是四个不同的量，不能用其中一个推断整个页面的体验。

所以先在目标设备上测出时间花在哪，再看换框架能不能改变那一段：

| 时间主要花在 | 换渲染器能否改善 |
| --- | --- |
| 数据到达（请求、服务端查询、重复读取） | 不能；改渲染器不会缩短网络往返。 |
| 主线程计算（排序、筛选、格式化） | 通常不能；先优化算法、缓存，或移到 Web Worker。 |
| 组件 render 工作 | 可能；但先试同框架内的状态下移和 memo 边界。 |
| 节点很多、布局或滚动慢 | 不能直接改善；减少实际挂载的节点（分页、虚拟化），它会带来焦点、测量和滚动位置的管理成本。 |
| 首屏或交互时序（服务端输出、hydration、脚本到达） | 取决于框架配套的服务端渲染和交付能力，而不是有无虚拟 DOM。 |

从症状找到证据的完整方法见[用户觉得慢时，怎样从指标走到证据？](../delivery/performance-metrics-and-diagnosis.md)；React 侧的测量见[React 渲染慢时，先改什么？](../delivery/react-rendering-optimization.md)；节点数量问题见[长列表的成本在哪里，分页和虚拟化各省掉什么？](../delivery/long-lists-pagination-and-virtualization.md)。

导航时序同样与虚拟 DOM 无关。点“最早优先”后数据还在路上时，地址、屏幕上已提交的行和待定的导航目标可能暂时不一致；按 Back 时浏览器地址先变、屏幕后变。这些时点由路由库决定，见[路由怎样把 URL 变成已提交的数据和界面？](./routing-and-loaders.md)。

## 选型：写下可验证的约束

把“虚拟 DOM 更快”“编译器没有运行时”换成可以逐条核对的约束：

| 约束 | 要核对的问题 |
| --- | --- |
| 首屏与服务端 | 报表是否必须在客户端脚本执行前就出现在 HTML 里？hydration 后要恢复哪些交互？ |
| 导航与数据 | `sort`、`#summary`、刷新、错误和 Back 是否恢复同一条状态链？请求和渲染由谁负责？ |
| 交互与无障碍 | 原生语义、键盘、焦点和列表状态在重排后是否仍然正确？ |
| 工程与团队 | 构建、测试、调试、升级、监控和部署能否在团队现有条件下长期维护？ |
| 已测瓶颈 | 耗时在网络、JavaScript 计算、DOM 数量还是浏览器布局绘制？候选方案能改变哪一段？ |

这些能力由框架、路由器、服务端适配器和应用代码共同提供，不能从“有没有虚拟 DOM”一个标签推出来。验证时把候选放进一条真实的产品切片（一条完整的用户操作路径）：从 `/reports/42?sort=recent#summary` 首次打开，点“最早优先”，等待数据，按 Back；同时检查键盘操作、焦点、加载和失败状态、直接刷新、深链接、部署产物和自动化测试。每个时点记录浏览器地址、待定的导航目标、已提交的排序和屏幕上的行：已提交排序必须与屏幕上的行一致，待定目标要明确提示，导航完成后三者重新对齐。Next.js App Router 对服务端组件、导航和数据另有约定，见[Next.js App Router 怎样把服务端渲染、缓存和客户端交互分开？](./next-js-app-router.md)。

### 用同一组门槛淘汰和保留候选

> [!example] 一次合成评审
> 以下候选和核验结果是为演示决策过程设定的输入，不是跑过的跨框架测试。产品额外要求：两条报表在 JavaScript 执行前可见；刷新直达、键盘排序、Back 和 May 草稿全部通过。
>
> - **候选 A：只做客户端渲染的配置。** 响应 HTML 只有挂载容器，没有报表行。“脚本运行前必须看见报表”不能放宽，所以淘汰这种**交付配置**，而不是淘汰 React、Vue 或 Svelte 这个框架。
> - **候选 B：React 服务端渲染（SSR）配置及其 hydration、导航集成。** 假定直达、加载、键盘和排序回放全部通过，保留为交付候选，理由是它满足了硬门槛。
> - **候选 C：Vue 或 Svelte 的 SSR 配置。** 还没用团队实际的适配器和浏览器跑这组门槛，状态是“待验证”，不是“性能差”或“失败”。跑完同样的验收后，再比较维护成本或已测瓶颈。
>
> 在这组假设下选 B 交付、淘汰 A。这个结论不证明 React 比 Vue 或 Svelte 快。

之后若录制显示耗时主要在服务端请求，换渲染器也不会缩短等待；若在 DOM 布局，就针对节点数和样式优化。只有实测暴露了当前方案无法满足的约束，才构成迁移理由。老系统还要考虑已有组件、插件和服务端集成的迁移成本；新系统则应把路由、服务端数据、渲染模型和交付链路放在一起验证。某个候选只在微基准测试里胜出、却没改善这条真实路径时，它的性能优势还不成立。

## 选型看路径与瓶颈，不看标签

虚拟 DOM 声明的是“界面应该是什么”，框架负责把它落到 DOM；列表身份由键决定，DOM 写入之后的样式、布局和绘制成本由浏览器承担，导航时序由路由决定，三者都与有没有虚拟 DOM 无关。选框架时，用一条真实产品切片上的硬门槛淘汰交付配置，用实测瓶颈判断换方案能改变哪一段。

> [!info]- 来源
>
> - React element 不是 DOM 节点；render、commit 与浏览器绘制是不同阶段（“界面描述不是 DOM 的副本”）：[createElement](https://react.dev/reference/react/createElement)、[Render and Commit](https://react.dev/learn/render-and-commit)；React 当前主版本 19.3，版本页列出 19.3.0（2026-09-09）：[Versions](https://react.dev/versions)，核对 2026-11-13。
> - React key 以稳定身份匹配可移动条目、位置/类型/key 决定状态保留、显式 Transition 更新可中断（“React：元素 key”）：[Rendering Lists](https://react.dev/learn/rendering-lists)、[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)、[startTransition](https://react.dev/reference/react/startTransition)，核对 2026-11-13。
> - Vue 模板编译为渲染函数、静态提升与 patch flags（“Vue”）：[Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism.html)；运行时依赖追踪：[Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html)；DOM 更新缓冲到下一个 tick：[Reactivity Fundamentals — DOM Update Timing](https://vuejs.org/guide/essentials/reactivity-fundamentals.html)；缺 key 按位置 patch、有 key 复用并移动：[List Rendering — Maintaining State with key](https://vuejs.org/guide/essentials/list#maintaining-state-with-key)；大对象深层响应式的成本：[Performance — Reduce Reactivity Overhead for Large Immutable Structures](https://vuejs.org/guide/best-practices/performance.html)，Vue 当前官方指南，核对 2026-11-13。
> - Svelte 组件编译为 JavaScript 模块（“Svelte”）：[Overview](https://svelte.dev/docs/svelte/overview)、[svelte/compiler](https://svelte.dev/docs/svelte/svelte-compiler)；`$state`：[$state](https://svelte.dev/docs/svelte/%24state)；`$derived` 运行时追踪依赖、下次读取时重算：[$derived — Understanding dependencies](https://svelte.dev/docs/svelte/%24derived#understanding-dependencies)；`$effect` 的时序：[$effect](https://svelte.dev/docs/svelte/%24effect)；带键 each 块按身份插入、移动、删除：[keyed each blocks](https://svelte.dev/docs/svelte/each#keyed-each-blocks)，Svelte 5 文档，核对 2026-11-13。
> - React 稳定 ID key 与下标 key 的输入值、DOM 节点和焦点差异（“探针证明了什么”）：原章节独立 React 浏览器探针；Vue 与 Svelte 的焦点未实测。
> - URL 片段不随请求发给服务端（案例）：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核对 2026-11-13。
