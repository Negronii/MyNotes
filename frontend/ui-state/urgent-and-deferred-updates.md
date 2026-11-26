# 昂贵更新时，怎样让输入保持即时？

本章回答：当一次状态更新会触发昂贵的 render 时，怎样让输入框、按钮这类直接反馈先到，让结果列表或新视图稍后跟上，以及在等待代码或数据时是保留旧界面还是显示加载提示。读者已经知道一次更新怎样经过 render 和 commit；这里要区分的是 React 给不同更新安排的优先级。

**案例。** 沿用主线一的报表页，行数据已经取到。本章跟踪两个场景：一是用户在新增的搜索框里输入标题，结果列表 `ReportResults` 按搜索词 `query` 过滤；二是用户点新增的“查看摘要”按钮，切换到一个按需加载的摘要模块 `ReportSummary`。行为按 React 19.3 与 React DOM 19.3 核对。

先说清本章所有 API 的共同边界：**它们只调整 React 安排 render 工作的优先级。** 它们不会把 JavaScript 挪到另一个线程，不设置固定的毫秒延迟，也不能打断一段正在运行的同步函数。

## 紧急更新与可延后的更新

用户打字时，输入框必须立刻显示新字符，这是 urgent update（紧急更新）。结果列表晚一点更新，用户能接受。React 能把这两类工作分开：先提交紧急的部分，再在后台计算可延后的部分；后台 render 进行中若有新的紧急更新到来，React 可以放弃这轮计算，按最新输入重来。

React 能中断的只是组件和组件之间的 render 工作。一个组件内部的 `reports.filter(...)` 是一段同步 JavaScript，运行到结束前主线程不能处理新输入，React 也插不进去。

## useDeferredValue：输入先提交，结果后跟上

搜索框的 `query` 是紧急状态，直接由 `onChange` 更新。`useDeferredValue(query)` 返回一个“落后一步”的副本 `deferredQuery`，把它而不是 `query` 交给结果列表。`isStale = query !== deferredQuery` 表示列表还没跟上输入，用来显示陈旧提示。

假设初始搜索词为空，列表显示 May、April。用户一次把搜索框填成 `apr`（例如粘贴）：

| 次序 | 发生什么 |
| --- | --- |
| 1. 输入事件 | 处理器排入 `query="apr"`。 |
| 2. 紧急 render 与 commit | render 得到 `query="apr"`、`deferredQuery=""`、`isStale=true`。提交后输入框显示 `apr`，陈旧提示出现；`ReportResults` 的 props 没变，这一轮跳过它，列表 DOM 仍是 May、April。 |
| 3. 后台 render | React 用 `deferredQuery="apr"` 计算新列表，屏幕上仍是已提交的旧列表。期间若用户又输入，这轮可被放弃，按最新值重来。 |
| 4. 后台 commit | 采用这一轮后，列表提交为 April，`isStale` 变回 `false`，提示消失。 |

这是 React 的提交次序，不承诺每一步都单独绘制成一帧；后台工作很快完成时，用户可能只看到最终列表。

> [!example]- 完整示例：输入状态与结果列表
>
> ~~~tsx
> import { memo, useDeferredValue, useState } from "react";
>
> type FilterReport = { id: string; title: string };
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
>         <input value={query} onChange={event => setQuery(event.currentTarget.value)} />
>       </label>
>       {isStale && <p role="status">列表仍对应旧的搜索词，正在更新。</p>}
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
>   const visible = reports.filter(report =>
>     report.title.toLowerCase().includes(query.toLowerCase())
>   );
>   return (
>     <ol>
>       {visible.map(report => <li key={report.id}>{report.title}</li>)}
>     </ol>
>   );
> });
> ~~~

两个前提决定这个方案是否成立：

- **输入状态必须保持紧急。** 如果把 `setQuery` 本身包进 Transition，`useDeferredValue` 会直接返回新值，不再多安排一轮延后 render，输入框也失去即时响应。
- **结果组件必须能在紧急那一轮被跳过**，下一节解释。

## memo 边界决定能否跳过旧列表

第 2 步能跳过 `ReportResults`，靠的是 `memo`（记忆化组件）：它按浅比较检查 props，`reports` 和 `query` 都没变就跳过这次 render。没有这道边界，紧急 render 会用旧的 `deferredQuery` 把整个列表重算一遍，输入照样变慢。

浅比较比的是引用。`reports` 必须在输入期间保持同一个数组、也不被原地修改；父组件若每次 render 都传一个新数组，`memo` 就会认为 props 变了。`memo` 是性能优化，不是正确性保证。项目配置了 React Compiler（React 编译器）并核对过编译结果时，编译器可能自动建立同样的跳过边界；本例显式写 `memo`，让因果关系在没有编译器时也看得见。怎样测量和建立 memo 边界，见[React 渲染慢时，先改什么？](../delivery/react-rendering-optimization.md)。

## deferred 不是 debounce

`useDeferredValue` 和 debounce（防抖）解决不同的问题：

- **它不等待固定时长。** React 在紧急更新之后立即开始后台 render，有新输入就中断重来；没有“停止输入 300 ms 后再算”这回事。
- **它不减少网络请求。** 若结果来自远端搜索，每个 `deferredQuery` 值仍可能触发一次请求；请求频率要由明确的请求策略或查询层控制，debounce 的语义见[怎样包装一个函数而不弄丢参数、this 和结果？](../javascript/wrapping-functions.md)。
- **它不缩短同步计算。** 全量过滤本身若已是长任务，React 也无法在中途让出。这时要先缩小数据、改进算法、把工作拆成能在小块之间让出主线程的片段，或放进 Web Worker（网页工作线程），见[用户觉得慢时，怎样从指标走到证据？](../delivery/performance-metrics-and-diagnosis.md)。只有成本来自许多结果组件的 render 时，跳过旧查询的子树才有帮助。

## useTransition：把一次界面切换标为非紧急

第二个场景独立于搜索：搜索框为空，列表按“最早优先”显示 April、May；用户点“查看摘要”，而摘要模块的代码可能还没下载。

`useTransition` 返回 `[isPending, startTransition]`。`startTransition(fn)` 会**立即同步**调用 `fn`，并把 `fn` 里排入的状态更新标为 Transition（过渡更新）。它标记的是更新的优先级，不会推迟处理器的执行。`isPending` 在这次 Transition 完成前为 `true`，可用来给出轻量的等待反馈。Transition 可被更紧急的更新打断，所以不能用它更新受控文本输入的值。

~~~tsx
const ReportSummary = lazy(() => import("./ReportSummary.js"));

function openSummary() {
  startTransition(() => {
    setView("summary");
  });
}
~~~

## Suspense 在等什么，等待时显示什么

`<Suspense fallback={…}>` 包住一块子树。子树里的组件在 render 时发现所需资源还没就绪，就 suspend（挂起），由最近的 Suspense 边界决定等待期间显示什么。能让边界进入等待的资源有：

- `lazy` 加载的组件代码；
- 通过 `use(promise)` 读取的 Promise；
- 集成了 Suspense 的数据框架或数据库（例如下面的 TanStack `useSuspenseQuery`）；
- 带 `precedence` 属性的样式表。

写在 `useEffect` 或事件处理器里的普通 `fetch` 不会触发边界，它需要自己的加载状态。

“资源还没就绪”不等于“把已有页面换成加载提示”。同一个边界在等摘要模块时，显示什么取决于它是否已经有内容，以及这次更新是不是 Transition：

| 开始等待时 | 等待期间显示 | 模块就绪后 |
| --- | --- | --- |
| 已显示列表，点击用 Transition 更新 `view` | 保留 April、May；`isPending` 为真，可提示“正在准备摘要” | 重试 render，提交摘要“当前共有 2 条报表” |
| 对照：同一次点击用普通（紧急）更新 `view` | fallback 替换掉列表 | 重试 render，提交摘要 |
| 首次挂载就直接渲染摘要 | fallback，因为没有旧内容可保留 | 首次提交摘要 |

模块很快加载完时，用户可能根本看不到任何等待提示。

模块加载失败时，由最近的错误边界显示错误，见[错误发生在哪里，决定了谁能接住它？](./react-error-boundaries.md)。注意 `lazy` 会缓存它的 loader Promise：同一个 `lazy` 声明失败后，仅仅重置错误边界不会再次调用 loader。可以提供刷新页面的恢复入口，让新页面重新请求模块；前提是发布资源或网络已经恢复。

> [!example]- 完整示例：切换摘要与懒加载模块
>
> ~~~tsx
> // ReportWorkspace.tsx
> import { lazy, Suspense, useState, useTransition } from "react";
>
> type WorkspaceReport = { id: string; title: string };
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
>       <button type="button" onClick={openSummary}>查看摘要</button>
>       {isPending && <span role="status">正在准备摘要视图…</span>}
>       <Suspense fallback={<p>正在加载摘要模块…</p>}>
>         {view === "summary" ? (
>           <ReportSummary reports={reports} />
>         ) : (
>           <ol>
>             {reports.map(report => <li key={report.id}>{report.title}</li>)}
>           </ol>
>         )}
>       </Suspense>
>     </main>
>   );
> }
>
> // ReportSummary.tsx
> export default function ReportSummary({ reports }: { reports: { id: string; title: string }[] }) {
>   return (
>     <section>
>       <h2>报表摘要</h2>
>       <p>当前共有 {reports.length} 条报表。</p>
>     </section>
>   );
> }
> ~~~

## use(promise) 必须复用同一个 Promise

React 19 的 `use(promise)` 在 render 中读取 Promise：pending 时挂起，交给最近的 Suspense；履行后返回值；拒绝时交给最近的错误边界。

关键要求是：**多次 render 之间传入的必须是同一个 Promise 对象。** 组件 render 时若写 `use(fetchSummary())`，每轮 render 都拿到一个新的 pending Promise，组件会反复挂起，React 也会对这种未缓存的 Promise 发出警告。Promise 应来自 render 之外，例如由服务端组件创建后传下来，或由支持 Suspense 的数据框架缓存。这条要求只针对交给 `use` 的 Promise；`lazy` 和带 `precedence` 的样式表由 React 自己管理。

## 异步 Action：等待期间保持 isPending

摘要显示后，用户可能要刷新摘要数据。React 19 的 `startTransition` 可以接收 async 函数，称为 Action（动作）；Action 等待期间 `isPending` 一直为 `true`。

> [!warning] await 之后的更新要再包一次
> React 目前不会自动把 `await` 之后排入的状态更新算进同一个 Transition。成功或失败后写状态时，要再用一次 `startTransition` 包住，否则这些更新按普通优先级处理。

一次刷新的流程是：等待期间保留当前摘要文字并显示“正在刷新”；成功后在新的 `startTransition` 里写入新摘要并清除错误；失败时只写错误，保留已有摘要。

Transition 只管 render 优先级，不保证自定义异步请求的完成顺序。下面的示例在 pending 时禁用按钮，避免这个唯一入口重复发请求；若界面允许上一轮结束前再次触发，请求可能乱序返回，仍要用请求编号、取消或数据层的排序规则拒绝旧结果，见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](./server-state-and-optimistic-updates.md)。`useActionState`、`<form>` Action 和 Server Functions 会在各自的工作流里管理请求顺序。

> [!example]- 完整示例：异步刷新、等待与失败
>
> ~~~tsx
> import { useState, useTransition } from "react";
>
> export function SummaryRefresh({ fetchSummary }: { fetchSummary: () => Promise<string> }) {
>   const [summary, setSummary] = useState("尚未加载摘要");
>   const [error, setError] = useState<string | null>(null);
>   const [isPending, startTransition] = useTransition();
>
>   function refresh() {
>     startTransition(async () => {
>       try {
>         const next = await fetchSummary();
>         startTransition(() => {
>           setSummary(next);
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
>       <button type="button" onClick={refresh} disabled={isPending}>刷新摘要</button>
>       {isPending && <p role="status">正在刷新摘要…</p>}
>       {error && <p role="alert">{error}</p>}
>       <div aria-busy={isPending}>
>         <p>{summary}</p>
>       </div>
>     </section>
>   );
> }
> ~~~

## 实例：TanStack Query 的 Suspense 读取（v5）

TanStack Query v5（要求 React 18 及以上）用专门的 Hook 接入 Suspense：`useSuspenseQuery`、`useSuspenseInfiniteQuery` 等。v4 的 `useQuery({ suspense: true })` 布尔开关在 v5 已移除，不要照搬旧代码。普通 `useQuery` 的 pending 状态不会让 Suspense 边界显示 fallback，它把加载状态作为返回值交给组件。

`useSuspenseQuery` 初次加载失败时把错误抛给错误边界；已有缓存而后台刷新失败时，默认继续显示缓存数据。重试需要错误边界重置配合查询层的恢复机制，交接方式见[错误发生在哪里，决定了谁能接住它？](./react-error-boundaries.md)。

## hydration：客户端首轮必须和服务端 HTML 一致

本章的例子在一个空挂载点上用 `createRoot` 创建界面。如果服务端已经输出了 React 生成的 HTML，就改用 `hydrateRoot` 接管：React 不重建 DOM，而是把已有节点和客户端首轮 render 的结果对应起来，并挂上事件处理。前提是客户端首轮 render 必须和服务端 HTML 一致。

不一致时：

- **文本内容或 DOM 结构不匹配**，hydration 失败，React 改为在客户端重新渲染。不匹配发生在某个 Suspense 边界内时，从最近的边界开始重建；没有边界时重建整个根。
- **属性值不匹配**，React 不保证修补，页面可能保留服务端给出的错误属性。

所以客户端首轮不要读服务端没有的东西（`window` 尺寸、`Date.now()`、浏览器存储），这类值放进 Effect 在挂载后读取，或用 `useSyncExternalStore` 的服务端快照参数提供一致的初始值。

> [!info] 版本差异：根入口与并发特性
> `useDeferredValue` 和 `useTransition` 自 React 18 提供，React 19 加入异步 Action。React 18 中 `ReactDOM.render` 仍可用但已弃用，它按 React 17 的旧模式运行，不启用并发特性；React 19 已移除这个 API，客户端入口是 `createRoot`（新渲染）或 `hydrateRoot`（接管服务端 HTML）。

## 何时选哪个

| 你要的效果 | 用什么 | 不能指望它 |
| --- | --- | --- |
| 输入即时，依赖它的昂贵子树稍后跟上 | `useDeferredValue` + 子树的 `memo` 边界 | 减少请求次数、缩短同步计算 |
| 一次按钮切换不要阻塞其他交互，等待时保留旧界面 | `useTransition` | 控制受控文本输入；保证异步请求顺序 |
| 等代码或数据时，为一块区域指定等待界面 | `<Suspense>` + `lazy` / `use(promise)` / Suspense 数据 Hook | 发现 Effect 里的普通 `fetch` |
| 一次异步操作期间持续显示 pending | async Action（React 19） | 自动把 `await` 后的更新算进 Transition |
| 限制远端搜索请求频率 | debounce 或查询层策略 | 让输入框更即时 |
| 同步计算本身就是长任务 | 分块让出主线程、Web Worker | 由 React 优先级 API 解决 |

## 等待之外，失败交给谁？

本章把一次昂贵更新拆成两部分：紧急的输入和按钮反馈先提交，延后的列表和视图在后台计算；Suspense 决定等待代码和数据时是保留旧界面还是显示 fallback。等待之外的另一种结局是失败：模块加载失败、`use` 读到被拒绝的 Promise、render 抛错。哪些失败会交给错误边界，边界放在哪、重试按钮到底重试了什么，是[错误发生在哪里，决定了谁能接住它？](./react-error-boundaries.md)要回答的问题。若问题来自同时挂载过多结果行，见[长列表的成本在哪里，分页和虚拟化各省掉什么？](../delivery/long-lists-pagination-and-virtualization.md)。

> [!info]- 来源
>
> - `useDeferredValue` 初次直接返回当前值；更新时先用旧值、再可中断地后台 render 新值；在 Transition 内直接返回新值；不设固定延迟、不减少请求（“useDeferredValue”“deferred 不是 debounce”）：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)，React 19.3。
> - `memo` 按 props 浅比较跳过 render；React Compiler 可自动应用等价优化（“memo 边界”）：[memo](https://react.dev/reference/react/memo)、[React Compiler](https://react.dev/learn/react-compiler)，React 19.3。
> - Transition 立即调用回调、可中断、不能控制文本输入；Action 跨 `await` 的更新需再包 `startTransition`；自定义异步工作可能乱序；`useActionState` 与 form Action 管理顺序（“useTransition”“异步 Action”）：[useTransition](https://react.dev/reference/react/useTransition)、[useActionState](https://react.dev/reference/react/useActionState)，React 19.3。
> - 什么能激活 Suspense 边界；已显示内容在 Transition 中被保留；Effect/事件处理器里的普通 fetch 不触发边界（“Suspense 在等什么”）：[Suspense — What activates a Suspense boundary](https://react.dev/reference/react/Suspense#what-activates-a-suspense-boundary)，React 19.3。
> - `lazy` 缓存 loader Promise，同一声明失败后重置错误边界不会再次调用 loader：[lazy](https://react.dev/reference/react/lazy)，React 19.3；整页刷新后发出第二次模块请求由原章节隔离回放实测。
> - `use(promise)` 的挂起、拒绝与 Promise 复用要求（“use(promise)”）：[use — Reading a promise with use vs fetching in an Effect](https://react.dev/reference/react/use#reading-a-promise-with-use-vs-fetching-in-an-effect)，React 19.3。
> - TanStack Query v5 专用 Suspense Hook、移除 `suspense: true`、错误边界与后台刷新错误（“TanStack Query 实例”）：[Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[useSuspenseQuery](https://tanstack.com/query/latest/docs/framework/react/reference/useSuspenseQuery)、[Migrating to v5](https://tanstack.com/query/latest/docs/framework/react/guides/migrating-to-v5)，TanStack 官方文档，核对 2026-11-12。
> - `hydrateRoot` 要求首轮一致；文本/结构不匹配时按最近 Suspense 边界或整个根重建，属性不保证修补（“hydration”）：[hydrateRoot — Caveats](https://react.dev/reference/react-dom/client/hydrateRoot#caveats)、[React error 418](https://react.dev/errors/418)、[React 18 Upgrade Guide — Other Breaking Changes](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#other-breaking-changes)；原章节对 text、boundary、root、attribute 四种情况做了独立回放。
> - React 18 的 `createRoot` 与并发特性、旧 `ReactDOM.render` 的行为；React 19 移除 `ReactDOM.render`（“版本差异”）：[React 18 Upgrade Guide](https://react.dev/blog/2022/03/08/react-18-upgrade-guide)、[React v18](https://react.dev/blog/2022/03/29/react-v18)、[React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)，React 团队。
> - render 与 commit 的区分；`aria-busy` 标记仍在更新的区域：[Render and Commit](https://react.dev/learn/render-and-commit)，React 19.3；[WAI-ARIA 1.2 `aria-busy`](https://www.w3.org/TR/wai-aria-1.2/#aria-busy)，W3C。
> - 当前 React 文档版本：[Versions](https://react.dev/versions)，React 19.3，核对 2026-11-12。
