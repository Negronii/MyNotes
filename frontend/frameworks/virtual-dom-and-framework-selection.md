# 如何为产品选择前端框架？

**合成案例。** 用户打开 URL（统一资源定位符）`/reports?sort=recent#summary`，报表路由加载器（loader）读取 `sort=recent` 并交付 May、April 两行；`#summary` 指向页面已有的 `<h1 id="summary">`，是浏览器定位片段，不会随 HTTP（超文本传输协议）请求发给服务端。用户点 **Oldest first** 后，路由读取 `oldest`；成功时提交 April、May 与对应地址。按浏览器 Back 后，页面回到 `sort=recent` 和 May、April。这里采用 [React Router 8.5.1 Data Mode（数据模式）](./react-routing-and-navigation.md) 的加载时序：新增历史项（PUSH）等待时可暂留 recent 地址与已提交行；返回旧历史项（POP）时，浏览器地址先变回 recent，而视图可暂留已提交的 oldest 行。中间状态在下方逐项说明；加载成功后，地址、已提交选择和行数据才重新对齐。本文从路由交付数据开始比较框架如何更新 DOM（文档对象模型），不把请求耗时误算成虚拟 DOM（virtual DOM）的工作。地址与历史的浏览器行为见[浏览器导航与历史如何恢复筛选状态？](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)。

## virtual DOM（虚拟 DOM）模型说明什么？

界面框架都要把应用状态变成浏览器可操作的节点，但不要把三个实现阶段的产物误当成同一种结构。React 的 element（元素）和 Vue 的 virtual node（虚拟节点，VNode）是运行时交给渲染器处理的界面描述；Svelte 的编译器则把组件变成浏览器执行的 JavaScript 模块，模块中的更新代码再操作界面。它们都不是浏览器 DOM 的副本；element 或 VNode 也不是现成 DOM 节点。

在 React 中，一次状态或属性变化会触发组件重新计算 `render`（渲染）结果。React 用 reconciliation（协调）把新旧元素描述对应起来，然后在 `commit`（提交）阶段对宿主树（浏览器中通常是 DOM）应用必要变化。组件被再次调用不等于 DOM 一定被改写：新结果与旧结果相同时，可以没有 DOM 修改；浏览器是否要重算样式、布局或绘制，又是之后的工作。React 元素也不是现成的 DOM 节点。

列表排序说明了“数据顺序”和“条目身份”是两件事。May、April 变成 April、May 时，`id` 仍标识同一份报表。React 的 `key`（键）、Vue 的 `:key`、Svelte `#each` 块的键都让框架按同级条目身份对应前后两次输出；用数组下标充当身份，May 的输入内容可能留在位置一而被 April 使用。键只在持续挂载的列表子树内生效：若路由卸载整棵列表，key 不会替应用保存草稿。virtual DOM 让开发者声明界面，再由协调器处理节点对应；它本身不意味着一定更快，也不意味着每次更新都重建实际 DOM。

## 用一个真实交互比较候选方案

按 React Router 8.5.1 Data Mode 的这条路径，把浏览器地址、已提交选择与行、待定目标分开看：

- **首次 recent 读取完成：** 地址和已提交选择为 `recent`，行是 `[May, April]`；没有待定目标，`#summary` 指向当前文档已有的报表标题。
- **点击 Oldest first，PUSH loader 等待：** 地址仍是 recent；已提交选择和行仍为 recent / `[May, April]`；待定目标是 `oldest`。页面显示正在切换，当前选中按钮仍应对应已提交行。
- **oldest loader 成功：** 路由提交 oldest 地址和数据；选中按钮与行同时成为 `oldest` / `[April, May]`，待定目标清空。
- **oldest loader 失败（替代分支）：** 本例提交 oldest 地址后由路由错误边界显示错误，不把 recent 旧行说成刚由 oldest 确认；这个失败分支结束当前导航，不接着执行下面的 Back 步骤。
- **等 oldest 成功后按 Back，POP loader 等待：** 浏览器地址立即回到 recent；视图仍可保留已提交的 oldest 选择与 `[April, May]`，待定目标是 recent。这个短暂差异应通过单独的等待提示表达。
- **recent loader 成功：** 路由提交 recent 数据，地址、已提交选择、选中按钮和 `[May, April]` 再次对齐，待定目标清空。

PUSH 与 POP 在等待阶段的可见差异来自路由对历史项的处理。React Router 的其他模式或其他路由器可能采用不同提交时点；这段导航时序不能归到 virtual DOM。

若两行已经在客户端，视图也可以从同一份数据派生排序结果。下面的纯函数刻意只处理这两行，不包含导航、请求或渲染；复制数组避免 `sort()` 改写输入：

~~~js
const reports = [
  { id: "may", periodStart: "2026-05-01", title: "May report" },
  { id: "april", periodStart: "2026-04-01", title: "April report" },
];

function orderReports(rows, sort) {
  const direction = sort === "oldest" ? 1 : -1;
  return [...rows].sort((a, b) =>
    direction * a.periodStart.localeCompare(b.periodStart)
  );
}

orderReports(reports, "recent").map(row => row.id); // ["may", "april"]
orderReports(reports, "oldest").map(row => row.id); // ["april", "may"]
~~~

在服务器已按 `sort` 排好数据的路线中，框架接收的就是加载器交付的数组，不应再重复排序。无论数据来自路由加载器还是本地派生，用户界面（UI）的输入都是当前选择、当前行与等待或错误状态；框架从这些值建立或更新界面。

### 三种更新模型怎样接住这份数据？

为隔离行身份更新，沿用 May、April 两行，假设页面、列表和每行组件在查询变化时继续挂载，只替换加载器交付的数组。切换前，May 行的输入框中有草稿 `May draft`，焦点也在这个输入框。这里用脚本触发同一排序状态更新，不用鼠标点排序按钮，以免真实鼠标操作先把焦点移到按钮；此小探针只检验列表项移动时是否复用同一行，不表示真实点击后的焦点应离开按钮。新的数组是 `[April, May]`，May 的身份仍为 `id="may"`。

#### React：元素 key 把 May 对应到新位置

路由交付新 props（属性）后，React 组件按 `[April, May]` 再算一组 element 描述。列表中的 `key={report.id}` 让协调器在同一个父列表下把旧的 May 组件与新列表第二个位置的 May 对应起来；若其组件类型也未变化，行内 state（状态）仍属于 May，React 可以移动原有 `<li>` 与 `<input>`，保留 `May draft` 和该节点的焦点。把 `key` 改成数组下标时，位置一的旧 May 输入会被 April 复用，正是“值跟位置走”的反例。路由若卸载了整个页面，这项状态会销毁，必须由路由缓存或更高层状态另行保存。

~~~jsx
reports.map(report => (
  <ReportRow key={report.id} report={report} />
))
~~~

React 通常会为更新安排组件计算；若应用把触发列表更新的 state 更新显式标记为 Transition（过渡更新），React 可以中断并重新计算这项非紧急 render。这个能力不打断正在运行的排序函数或任意点击处理器；路由是否把导航标成 Transition 则由路由自身决定。

#### Vue：依赖更新生成新 VNode，再按 key 移动旧行

假设 Vue 组件的 `reports` 响应式输入被加载器替换。组件先前渲染时读取了它，所以响应式依赖让组件进入更新；模板生成新的 VNode 列表。模板编译器能标出静态部分和动态绑定，但列表仍由渲染器协调。`v-for` 上的 `:key="report.id"` 让渲染器把旧 May VNode/DOM 对应到新数组中的第二位，移动已有行节点；在这个复用路径中，原输入节点仍装着 `May draft`。没有 key 时 Vue 默认可按位置就地补丁，输入状态就可能和 May 的报表内容分离。

~~~vue
<li v-for="report in reports" :key="report.id">
  <ReportRow :report="report" />
</li>
~~~

#### Svelte：编译模板更新点，运行时按键重排

Svelte 编译器把模板和状态引用转换成 JavaScript 更新代码；当页面收到新的 `reports` 数组时，受影响的模板块执行更新。若页面自行从本地数组计算排序，`$derived` 会在表达式读取状态时记录依赖；依赖失效后，下次读取再计算结果。编译器预先知道哪些模板绑定需要更新，但它不会在编译时知道本次 `reports` 的值或顺序。

~~~svelte
{#each reports as report (report.id)}
  <ReportRow {report} />
{/each}
~~~

带键 `#each` 块在运行时按 `report.id` 对应各行，把旧 May 块从第一位移到第二位，而不是把 May 当成位置一的新内容。只要这个列表仍挂载，行组件身份和其中的输入草稿就跟随 May。Svelte 与 React/Vue 的 VNode 描述与协调不是同一种路径，但这里的输出目标相同：DOM 顺序为 April、May，May 的草稿仍属于 May。

独立 React 浏览器探针确认了稳定 id key 与 index key 的差异：前者让 May 输入值、同一 DOM 节点和焦点跟随 May；后者把它们留在位置一。Vue 与 Svelte 的 keyed 文档描述了按身份复用或移动列表项，但本笔记没有在这两个运行时实测焦点。产品验收应在选定版本的真实浏览器中验证重排后 May 的输入值、DOM 节点和 `document.activeElement`（当前活动元素）。

### 看 DOM 之后还剩哪些工作

框架提交 DOM 后，浏览器仍可能计算样式、执行布局、绘制与合成。小列表换序若伴随复杂样式，瓶颈可能在浏览器；巨大列表即使框架计算很少，也可能因为实际创建了成千上万个节点而变慢。框架的“更新次数”、组件函数调用数、DOM 写入数和用户看到画面的时刻是不同指标，不能拿其中一个推断整个页面体验。

因此把真实切片上的成本拆开测：

| 观测到的主要耗时 | 优先验证的方向 |
|---|---|
| 数据到达慢 | 请求、服务端查询、缓存与是否重复读取；改渲染器不会缩短网络往返。 |
| 主线程计算长 | 排序、筛选、格式化或组件工作；先测热点，再考虑算法、缓存或 Web Worker（网页工作线程）。 |
| 节点很多、滚动或布局慢 | 可见区域实际需要多少行、样式和布局成本；必要时评估虚拟滚动，但它会增加焦点、测量与滚动位置管理。 |
| 首屏或交互时序不符 | 服务端输出、hydration（客户端水合）、路由等待状态以及 JavaScript 到达和执行时点。 |

先用浏览器性能记录或目标设备测出瓶颈，再选择框架能力或局部优化。客户端水合、路由、表单、访问性和错误恢复都可能决定方案；这些能力由框架、路由器、服务端适配器与应用共同组成，不能从“有无 virtual DOM”一个标签推出来。浏览器如何接手 DOM 并绘制见[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)；React 的 render、commit 和后续浏览器工作见[React 如何把一次用户操作变成界面更新？](./react-basics.md)。

## 决定前验证边界

先把候选放进一条真实产品切片：从 `/reports?sort=recent#summary` 首开，点 **Oldest first**，等待数据，按 Back；同时验证键盘操作、焦点、加载和失败状态、直接刷新、深链接、部署产物与自动化测试。每个时点分别记录浏览器地址、路由的待定目标、已提交排序和对应行：已提交排序必须与屏幕行一致；待定目标要明确标出；PUSH/POP 等待期间地址可暂与已提交屏幕不同；成功落定后再核对地址、选中项和数据一致。路由负责路径、查询参数与历史记录的接线，React Router 的例子见[React 路由怎样把地址映射到界面并加载数据？](./react-routing-and-navigation.md)；Next.js App Router 对服务端组件、导航和数据的边界另有约定，见[Next.js 如何把文件路由、服务端数据与客户端交互连接起来？](./next-js.md)。

选择时写下可验证的约束，而不是“虚拟 DOM 更快”或“编译器没有运行时”：

| 约束 | 要核对的实际问题 |
|---|---|
| 首屏与服务端 | HyperText Markup Language（超文本标记语言，HTML）是否必须在客户端脚本执行前包含报表？客户端水合需要恢复哪些交互？ |
| 导航与数据 | `sort`、`#summary`、刷新、错误和 Back 是否恢复同一条状态链？请求与渲染由谁拥有？ |
| 交互与访问性 | 原生语义、键盘、焦点和列表状态在重排后是否仍然正确？ |
| 工程与团队 | 构建、测试、调试、升级、监控和部署方式是否能在团队现有约束下持续维护？ |
| 已测瓶颈 | 耗时在网络、JavaScript 计算、DOM 数量还是浏览器布局绘制？候选机制能改变哪一段？ |


### 用同一组门槛淘汰和保留候选

假设产品额外要求两条报表在 JavaScript 执行前可见，并要求刷新直达、键盘排序、Back 与 May 草稿都通过。以下核验结果是这次合成评审为演示决策而设定的输入，不是本笔记声称跑过的跨框架测试：

- **候选 A：只有客户端渲染的配置。** 它的响应 HTML 样本只有挂载容器，没有报表行；若“脚本运行前必须看见报表”不能放宽，就淘汰这项交付配置，而不是淘汰 React、Vue 或 Svelte 这个框架。
- **候选 B：React 服务端渲染（server-side rendering，SSR）配置及其客户端水合/导航集成。** 假定同一组直达、加载、键盘和排序回放均通过，保留为本次交付候选；理由是它已满足硬门槛。
- **候选 C：Vue 或 Svelte 的 SSR 配置。** 还没有用团队实际适配器和浏览器跑这组门槛，状态应是“待验证”，不是“性能差”或“失败”。完成同样的验收后再比较维护成本或已测瓶颈。

因此这组假设会选 B 交付，并淘汰 A 的客户端渲染配置；它没有证明 React 比 Vue 或 Svelte 快。若后续录制显示耗时主要在服务端请求，换渲染器也不会缩短等待；若在 DOM 布局，就针对节点数和样式验证优化。只有实测暴露了当前路径不能满足的约束，才有迁移理由。

老系统可能要保留已有组件、插件或服务端集成；新系统则应把路由、服务端数据、渲染模型和交付链路一起验证。若候选只在微基准获胜，却没有改善这条真实路径，性能优势尚未成立。测量 React 组件工作可继续看[如何测量并减少不必要的 React 工作？](../performance/react-rendering-optimization.md)；当成本来自本地计算或长列表时，比较[如何为报表选择计算方式与列表渲染策略？](../performance/rendering-and-computation-optimization.md)。

> [!info]- 来源与版本核验（截至 2026-11-13）
> - **React 元素不是 DOM 节点；组件渲染、必要 DOM 提交与浏览器绘制是不同阶段。** React 当前文档：[`createElement`](https://react.dev/reference/react/createElement)（元素对象说明）、[Render and Commit](https://react.dev/learn/render-and-commit)（触发、render、commit、paint）；React 当前主版本文档为 19.3，版本页列出 19.3.0（2026-09-09）：[Versions](https://react.dev/versions)。核验日期：2026-11-13。
> - **React 列表键、组件状态与 Transition 边界。** [Rendering Lists](https://react.dev/learn/rendering-lists) 说明 key 以稳定身份匹配可移动条目；[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state) 说明同一父树中的类型与 key/位置决定状态保留；[`startTransition`](https://react.dev/reference/react/startTransition) 说明显式标记的更新可中断、重新开始，普通更新不自动具备该语义。当前 React 文档，核验日期：2026-11-13。
> - **Vue 模板、VNode、编译提示及批量更新。** [Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism.html) 说明模板渲染函数、静态提升、patch flags 与动态树遍历；[Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html) 说明运行时依赖追踪；[Reactivity Fundamentals](https://vuejs.org/guide/essentials/reactivity-fundamentals.html) 的 DOM Update Timing 说明更新缓冲到 next tick；[List Rendering](https://vuejs.org/guide/essentials/list#maintaining-state-with-key) 说明缺 key 时按位置补丁、有 key 时重用并移动 DOM 列表项；[Performance](https://vuejs.org/guide/best-practices/performance.html) 中 Reduce Reactivity Overhead for Large Immutable Structures 节说明大对象深层响应式的属性读取成本。Vue 当前官方指南页面，核验日期：2026-11-13。
> - **Svelte 编译与 Svelte 5 状态更新。** [Overview](https://svelte.dev/docs/svelte/overview) 和 [`svelte/compiler`](https://svelte.dev/docs/svelte/svelte-compiler) 说明组件编译为 JavaScript 模块；[`$state`](https://svelte.dev/docs/svelte/%24state) 说明响应式状态；[`$derived`](https://svelte.dev/docs/svelte/%24derived#understanding-dependencies) 说明同步读取的依赖在运行时追踪、失效值在下次读取时重算；[`$effect`](https://svelte.dev/docs/svelte/%24effect) 说明更新后的微任务与副作用时序；[keyed each blocks](https://svelte.dev/docs/svelte/each#keyed-each-blocks) 说明运行时按身份插入、移动和删除条目。Svelte 5 文档，核验日期：2026-11-13。
> - **URL 片段不在服务器请求中。** [RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5) 将 fragment 定义为供用户代理处理的标识，不属于检索 URI 的一部分；核验日期：2026-11-13。
