# 如何让报表筛选在昂贵更新时保持响应？

**案例背景。** 报表页已经收到 May、April 两条数据，当前列表可按日期排序。用户在搜索框输入标题时，输入框应立即显示新字符；如果报表结果很多，列表可以稍后跟上。用户点击“查看摘要”时，也希望保留当前列表，等摘要代码准备好再切换。下面分别跟踪输入筛选和摘要切换，区分紧急更新、可延后的 render（渲染）、commit（提交）、Transition（过渡更新）和 Suspense（挂起边界）。这些 API 调整 React 的工作优先级，不会把 JavaScript 移到另一个线程，也不设固定毫秒延迟。

以下行为按 React 19.3 与 React DOM 19.3 核验。先看同一次输入如何产生两轮更新，再看等待摘要代码时如何保留当前界面。状态快照见[React 更新轮次](./react-basics.md)，服务端查询仍由[服务端状态章节](./react-server-state-and-optimistic-updates.md)管理。本章省略 URL 与 Back 接线，见[浏览器历史栈机制](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)。

> [!info]- 挂载方式与版本前提
>
> 本例从空挂载点创建客户端界面，使用 `createRoot`。若服务端已经输出 React HTML，应以首轮内容匹配的 `hydrateRoot` 接管。文本或 DOM 结构不匹配可能使 hydration（客户端接管）失败并转为客户端渲染：错误位于 Suspense 边界内时可从最近边界重建，没有边界时会重建整个根。属性值不匹配的处理不同，React 不保证修补属性。
>
> `useDeferredValue` 和 `useTransition` 自 React 18 提供；React 19 支持异步 Transition Action（动作），跨 `await` 的状态更新限制在后文说明。若查旧资料，React 18 的 `ReactDOM.render` 使用接近 React 17 的旧根兼容模式；React 19 已移除此 API，当前入口使用 `createRoot`。
## 输入保持即时，结果视图可以延后

这里把搜索框的 `query` 作为紧急状态，把 `useDeferredValue` 返回的 `deferredQuery` 交给结果组件 `ReportResults`。用 `isStale = query !== deferredQuery` 判断列表是否尚未跟上输入，并据此显示等待提示。列表子组件用 `memo`（记忆化组件）包住；示例的 `reports` 数组来自已经取得的一份数据集，在输入变化期间保持同一引用且不原地改写。否则子组件收到新数组时仍会重渲染，不能用这个例子说明如何跳过旧查询的列表工作。

假设初始搜索词为空，列表显示 May、April。用户一次把搜索框填成 `apr` 时，`onChange` 处理器排入新的 `query` 更新；setter 不会改写本轮仍读到的状态快照。下一轮紧急 render 得到新 `query`，但 `deferredQuery` 仍可能为空。下面按 React 实际提交顺序展开。

render（渲染）按状态快照计算下一份界面。React 采用计算结果时，commit（提交）才把必要的 DOM 改动应用到页面。下面把事件处理器安排更新与之后的提交分开：

| 次序 | 本例发生什么 |
| --- | --- |
| 1. 输入事件 | 用户一次把搜索框填成 `apr`；处理器排入 `query` 更新。 |
| 2. 紧急 render / commit | render 得到 `query="apr"`、`deferredQuery=""`、`isStale=true`。提交后输入显示 `apr`、等待提示出现；列表 DOM 仍是 May、April，`ReportResults` 的 props 未变，可跳过这轮工作。 |
| 3. 后台 render | React 尝试用 `deferredQuery="apr"` 计算新列表；此时旧列表仍是已提交的画面。中途有更紧急更新时，可放弃这轮并按最新输入重试。 |
| 4. 后台 commit | 若 `apr` 这一轮被采用，新结果提交为 April，`isStale` 转为 `false`，等待提示消失。 |

表格说的是 React 提交次序，不承诺每一步都单独显示成浏览器绘制的一帧；后台工作若很快完成，用户可能只看见最终列表。

`memo` 只在子组件 props（属性）没变时提供跳过重渲染的机会；它是性能优化，不是输出正确性的保证。如果输入时父组件同时换了 `reports` 数组，默认浅比较会发现数组引用不同，子组件仍会渲染。若项目已配置 React Compiler（React 编译器）并检查过该组件的编译结果，编译器也可能自动建立相同的跳过边界；本例显式使用 `memo`，让代码即使未配置编译器也能呈现这个因果关系。

本例直接更新 `query`，所以输入事件是紧急更新。如果把更新 `query` 本身包进 Transition，`useDeferredValue` 会直接返回新词，不会再额外创建一轮 deferred render；要保留受控输入的即时响应，应让输入状态保持紧急。

`useDeferredValue` 不承诺等待某个固定时长；React 会在紧急更新后开始后台 render，并可在后续输入到来时中断、重启。它也不等于 debounce（防抖），不会减少网络请求数。上面的过滤发生在 render 中，但 `reports.filter(...)` 是一段同步 JavaScript，运行到结束前主线程不能插入新输入事件，React 也不能抢占这段函数。如果全量过滤本身已经是长任务，应先缩小数据、优化算法、拆成能在小块之间让出主线程的工作，或放入 Web Worker（网页工作线程）；若成本来自许多结果组件的 render，跳过旧查询子树才会有帮助。远端搜索频率仍应由明确的请求策略或查询层控制。

> [!example]- 完整示例：输入状态与结果列表
>
> ~~~tsx
> import { memo, useDeferredValue, useState } from "react";
>
> type FilterReport = {
>   id: string;
>   title: string;
> };
>
> export function ReportFilter({ reports }: { reports: FilterReport[] }) {
>   const [query, setQuery] = useState("");
>   const deferredQuery = useDeferredValue(query);
>   const isStale = query !== deferredQuery;
>
>   return (
>     <section>
>       <label>
>         搜索报表
>         <input
>           value={query}
>           onChange={event => setQuery(event.currentTarget.value)}
>         />
>       </label>
>       {isStale && (
>         <p role="status">列表仍对应旧的搜索词，正在更新。</p>
>       )}
>       <div aria-busy={isStale}>
>         <ReportResults reports={reports} query={deferredQuery} />
>       </div>
>     </section>
>   );
> }
>
> const ReportResults = memo(function ReportResults({
>   reports,
>   query
> }: {
>   reports: FilterReport[];
>   query: string;
> }) {
>   const visibleReports = reports.filter(report =>
>     report.title.toLowerCase().includes(query.toLowerCase())
>   );
>
>   return (
>     <ul>
>       {visibleReports.map(report => (
>         <li key={report.id}>{report.title}</li>
>       ))}
>     </ul>
>   );
> });
> ~~~

## 用Transition标记非紧急的界面切换

第二个问题是用户点击“查看摘要”后，摘要模块可能尚未下载。这个独立例子从清空搜索框、已选 oldest 的列表开始，行顺序为 April、May；下面只处理从列表切换到摘要。`useTransition` 把 `view` 更新标为非紧急 Transition，并提供 `isPending`（仍在等待）反馈。调用 `startTransition` 时，包住的函数会立即运行；它标记其中的 state 更新，而不是延迟执行事件处理器。Transition 不能用来控制受控文本输入；这里用它处理的是一整块摘要视图。

本例首次挂载时 `view="rows"`，先显示 April、May；摘要模块即使尚未下载，也不会让当前列表挂起。点击把 `view` 设为 `"summary"` 后，React 才需要那个模块来呈现摘要。假定此时模块仍未就绪，同一个 Suspense 边界会因已有内容和更新方式不同而呈现不同结果；模块准备好后，摘要显示“当前共有 2 条报表”：

| 开始等待时的状态 | 等待期间显示什么 | 模块准备好后 |
| --- | --- | --- |
| 已显示列表，点击由 Transition 更新 `view` | 保留 April、May；`isPending` 提示正在准备摘要 | 重试 render，提交摘要 |
| 对照：若把同次点击改为紧急更新 `view` | 用 fallback（备用界面）替换列表 | 重试 render，提交摘要 |
| 首次直接挂载摘要，还没有已提交内容 | 显示 fallback，没有旧内容可保留 | 首次提交摘要 |

这解释了为什么“资源还没加载完”不必等于“把已有页面换成加载提示”。快速加载时，用户也可能看不到等待提示。

Suspense 可以等待多种资源，但等待资源不代表每次都会显示 fallback；当前边界是否已有内容以及更新优先级会影响呈现。这里用 `lazy` 加载组件代码。读取数据时，可用 React 19 的 `use(promise)` 读取跨重渲染复用的 Promise，例如由服务端组件传来的 Promise，也可使用集成 Suspense 的数据框架。传给 `use` 的数据 Promise 必须能跨重渲染复用，不能每次 render 都新建；带 `precedence` 的样式表也能让边界等待样式表加载，但不适用 Promise 身份缓存条件。普通 `fetch` 放在 `useEffect` 或事件处理器里，不会自动触发边界；这类工作需要自己的加载状态。模块加载或数据读取失败时，最近的错误边界/查询错误状态负责显示错误。同一个 `lazy` 声明会缓存 loader Promise，重置错误边界不会再次调用 loader；产品可提供刷新页面的恢复入口，让新页面重新尝试加载模块，前提是发布资源或网络已经恢复。

若使用 TanStack Query v5（最低要求 React 18），数据挂起读取采用专用 `useSuspenseQuery`、`useSuspenseInfiniteQuery` 等 Hook（钩子）；不要照搬 v4 的 `useQuery({ suspense: true })` 选项，v5 移除了旧的布尔开关。普通 `useQuery` 的 pending 状态不会自行让 React Suspense 边界显示 fallback。`useSuspenseQuery` 的初次加载错误需要错误边界；后台刷新失败可以保留已有缓存，重试还需要错误边界重置或查询层的恢复机制。

> [!example]- 完整示例：切换摘要与懒加载模块
>
> ~~~tsx
> // ReportWorkspace.tsx
> import { lazy, Suspense, useState, useTransition } from "react";
>
> type WorkspaceReport = {
>   id: string;
>   title: string;
> };
>
> const ReportSummary = lazy(() => import("./ReportSummary.js"));
>
> export function ReportWorkspace({ reports }: { reports: WorkspaceReport[] }) {
>   const [view, setView] = useState<"rows" | "summary">("rows");
>   const [isPending, startTransition] = useTransition();
>
>   function openSummary() {
>     startTransition(() => {
>       setView("summary");
>     });
>   }
>
>   return (
>     <main>
>       <button type="button" onClick={openSummary}>
>         查看摘要
>       </button>
>       {isPending && <span role="status">正在准备摘要视图…</span>}
>       <Suspense fallback={<p>正在加载摘要模块…</p>}>
>         {view === "summary" ? (
>           <ReportSummary reports={reports} />
>         ) : (
>           <ul>
>             {reports.map(report => (
>               <li key={report.id}>{report.title}</li>
>             ))}
>           </ul>
>         )}
>       </Suspense>
>     </main>
>   );
> }
> ~~~
>
> `ReportSummary.tsx` 默认导出接收同一组报表的组件：
>
> ~~~tsx
> // ReportSummary.tsx
> type SummaryReport = {
>   id: string;
>   title: string;
> };
>
> export default function ReportSummary({
>   reports
> }: {
>   reports: SummaryReport[];
> }) {
>   return (
>     <section>
>       <h2>报表摘要</h2>
>       <p>当前共有 {reports.length} 条报表。</p>
>     </section>
>   );
> }
> ~~~

Transition 表示渲染优先级，不会把模块请求移到后台线程，也不自动保证自定义异步请求的完成顺序。React 19 的 `useTransition` 可以接收异步 Action（动作），并在 Action 等待期间维持 pending 状态。单次刷新可以在 `startTransition` 中等待 `fetchSummary()`：等待期间保留当前 `summary` 文本，显示正在刷新提示。成功后，再用一次 `startTransition` 包住状态更新，用返回文本更新 `summary` 并清除 `error`，继续把结果渲染标为非紧急；失败时只更新 `error`，保留已有摘要。


为避免这个单按钮入口重复发请求，下面的完整示例在 pending 时禁用按钮，结束后恢复。若界面允许前一轮结束前再次触发（例如重新启用同一按钮或提供其他入口），请求可能乱序返回；仍要用请求编号、取消或数据层排序规则避免旧结果覆盖新选择。React 的 `useActionState`、`<form>` Action 与 Server Functions 会在各自适用的工作流中处理请求顺序；`useTransition` 本身主要负责非紧急 render。

> [!example]- 完整示例：异步刷新、等待与失败状态
>
> ~~~tsx
> // SummaryRefresh.tsx
> import { useState, useTransition } from "react";
>
> export function SummaryRefresh({
>   fetchSummary
> }: {
>   fetchSummary: () => Promise<string>;
> }) {
>   const [summary, setSummary] = useState("尚未加载摘要");
>   const [error, setError] = useState<string | null>(null);
>   const [isPending, startTransition] = useTransition();
>
>   function refresh() {
>     startTransition(async () => {
>       try {
>         const nextSummary = await fetchSummary();
>         startTransition(() => {
>           setSummary(nextSummary);
>           setError(null);
>         });
>       } catch {
>         startTransition(() => setError("摘要读取失败。"));
>       }
>     });
>   }
>
>   return (
>     <section>
>       <button type="button" onClick={refresh} disabled={isPending}>
>         刷新摘要
>       </button>
>       {isPending && <p role="status">正在刷新摘要…</p>}
>       {error && <p role="alert">{error}</p>}
>       <div aria-busy={isPending}>
>         <p>{summary}</p>
>       </div>
>     </section>
>   );
> }
> ~~~

如果长同步计算仍占住主线程，先优化计算或交给 Worker；若问题来自同时挂载过多结果行，继续看[长列表何时适合虚拟滚动？](../performance/rendering-and-computation-optimization.md)。筛选子树的 memo 边界见[React 渲染优化](../performance/react-rendering-optimization.md)。

> [!info]- 来源与版本核验（React 19.3；核验日期 2026-11-12）
>
> - `useDeferredValue` 未传 `initialValue` 时初次直接返回当前值；更新先尝试旧 deferred 值，再可中断地后台 render 新值；Transition 内会直接返回新值；不设固定延迟、不减少网络请求：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)，React 19.3。
> - `memo` 按 props 浅比较跳过重渲染的条件；React Compiler 在已配置时可自动应用等价优化：[`memo`](https://react.dev/reference/react/memo)、[React Compiler](https://react.dev/learn/react-compiler)，React 19.3。
> - Transition 可中断、不能控制文本输入；React 19 Action 跨 `await` 更新要再次包 `startTransition`，自定义异步工作可能乱序；`useActionState` 与 form Actions 覆盖特定顺序管理场景：[useTransition](https://react.dev/reference/react/useTransition)、[`useActionState`](https://react.dev/reference/react/useActionState)，React 19.3。
> - 已揭示边界在 Transition 中保留旧内容；Suspense 可等待 `lazy`、交给 `use` 的 Promise、集成数据源、带 `precedence` 的样式表等资源。Promise 缓存条件只适用于传给 `use` 的数据 Promise；Effect/事件处理器中的普通 fetch 不会自动触发边界：[Suspense](https://react.dev/reference/react/Suspense#what-activates-a-suspense-boundary)、[`lazy`](https://react.dev/reference/react/lazy)、[`use`](https://react.dev/reference/react/use#reading-a-promise-with-use-vs-fetching-in-an-effect)，React 19.3。
> - `lazy` 会缓存声明的 loader Promise；同一声明失败后仅重置错误边界不会再次调用 loader，整页刷新可作为重新尝试模块请求的恢复路径：[lazy](https://react.dev/reference/react/lazy)，React 19.3；刷新后的第二次请求由本章隔离回放实测。
> - `hydrateRoot` 要求服务端 HTML 与客户端首轮一致。文本或树结构不匹配可能导致客户端重建，错误范围取最近 Suspense 边界或整个根；属性差异则不保证被修补：[hydrateRoot caveats](https://react.dev/reference/react-dom/client/hydrateRoot#caveats)、[React error 418](https://react.dev/errors/418)、[React 18 hydration recovery](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#other-breaking-changes)，React 团队；本章另对 text、boundary、root、attribute 四种情况做了独立回放。
> - React 18 的 `createRoot` 启用并发渲染/新根行为，`useTransition` 和 `useDeferredValue` 出自 React 18 并发特性；已有服务端 HTML 用 `hydrateRoot` 并匹配客户端首轮内容：[React 18 Upgrade Guide](https://react.dev/blog/2022/03/08/react-18-upgrade-guide)、[React v18](https://react.dev/blog/2022/03/29/react-v18)、[`hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot)，React 团队发布说明。
> - React 19 移除 `ReactDOM.render`，客户端入口使用 `createRoot`：[React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)，React 团队发布说明。
> - React render 与 commit 不是一回事；`aria-busy` 标记仍在更新的区域：[Render and Commit](https://react.dev/learn/render-and-commit)，React 19.3；[WAI-ARIA 1.2 `aria-busy`](https://www.w3.org/TR/wai-aria-1.2/#aria-busy)，W3C。
> - TanStack Query v5 专用 Suspense Hook、查询失败与错误边界恢复：[Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[`useSuspenseQuery`](https://tanstack.com/query/latest/docs/framework/react/reference/useSuspenseQuery)、[Migrating to v5](https://tanstack.com/query/latest/docs/framework/react/guides/migrating-to-v5)，TanStack 官方文档。
> - React 文档版本：[Versions](https://react.dev/versions)，当前 React 19.3，核验日期 2026-11-12。
