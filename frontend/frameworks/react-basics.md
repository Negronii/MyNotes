# React如何把一次用户操作变成界面更新？

**案例背景。** 沿用浏览器主线中的 `/reports?sort=recent#summary` 报表页，本章用 React 实现它的筛选控件和列表。`#summary` 是浏览器定位片段，不会发给服务端；服务端按 `sort=recent` 给出 May、April。现在用户点 **Oldest first**。React 把 `sort` 改为 `oldest` 后，会先用手头已有的两条记录在本地排成 April、May，再在提交后请求服务端确认。若很快又选回 **Most recent**，界面再次先排成 May、April；较早的请求不能把较新的选择误标成已确认。

以下示例按 React 19.3.0 与对应 React DOM 核验。本章从点击处理器接手，解释一次状态更新如何经过 `render`（渲染）和 `commit`（提交）改变 React 管理的 DOM（文档对象模型）。`useEffect`（副作用同步）在提交后协调需要跟随已提交状态的外部工作，例如网络请求。完整页面由路由把选择写入浏览器历史，并在 Back 时恢复；这里展示 React 内部轮次，省略 URL（统一资源定位符）与历史栈接线，细节见[筛选状态与前进后退](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)。本章停在 React 已提交 DOM；后续是否需要样式计算、布局或绘制，由浏览器决定，接回[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)。

先看点击后没有再次切换选择的一轮；快速反选时，后文再展开旧响应的处理。

| 阶段 | 这一轮发生什么 |
| --- | --- |
| 点击处理器 | 用户选择 Oldest first；处理器排入 `sort=oldest` 与 `requestId=1`，当前处理器仍读到旧的 `sort=recent`。 |
| `render` | React 读取新状态，从上次成功的两条记录派生 April、May，并计算“等待请求 1”；这里不发网络请求。 |
| `commit` | React 更新选中按钮、行顺序和提示对应的 DOM。 |
| `useEffect` 建立 | 提交后，Effect 才调用 `fetchReports("oldest")`。 |
| 响应回调 | 成功或失败回调排入带 `requestId=1` 的结果；React 再 render、commit，显示确认，或单独报错并保留上次成功数据。 |

## 处理器读到的是本次界面的状态快照

`state`（状态）变量不会被 setter（状态更新函数）原地改写；调用 setter 不会改变当前处理器读到的 `state`。React 每次调用组件，都给它一份当前状态快照；事件处理器也是在某一次 `render` 时创建的。因此在本例的 `chooseSort` 中，若这轮的 `sort` 还是 `recent`，调用 `setSort("oldest")` 后，这个处理器里的 `sort` 仍然是 `recent`。本例的一次点击中，React 会在处理器返回后一起处理排序和请求编号这两个更新，再据此计算下一份界面。

例如本轮 `count` 为 `0` 时，同一处理器连续调用两次 `setCount(count + 1)`，两次都根据快照 `0` 排入 `1`，结果仍是 `1`。若要让每一步基于队列中前一步的结果，传入 updater（更新函数）。以下处理器定义在组件函数内部：

~~~tsx
const [count, setCount] = useState(0);

function addFromSnapshot() {
  setCount(count + 1);
  setCount(count + 1);
}

function addFromQueue() {
  setCount(value => value + 1);
  setCount(value => value + 1);
}
~~~

在 `count` 快照为 `0` 时单独调用 `addFromSnapshot`，结果是 `1`；单独调用 `addFromQueue`，React 依次应用两个 updater，结果是 `2`。本页的 `setRequestId(id => id + 1)` 也用 updater，让编号从待处理状态继续递增。

**用户动作直接触发的一次性工作放在事件处理器里；从 props（属性）和 state 可算出的值在 render 里计算；只有需要随着已提交界面同步外部系统的工作才放进 Effect。** 本例点击处理器记录新的排序意图，`sortReports` 在 render 中派生可见行，Effect 在 commit 后请求与这份选择相符的数据。把可见行再写进一份 state 并用 Effect 同步，会多出一次不必要的更新轮次。

下面的 TypeScript JSX（TSX）代码把 `fetchReports` 作为路由传入的数据层函数：它接收排序值，成功时返回已验证的 `Report[]`，失败时以拒绝的 Promise 表示。`initialReports` 常量是“路由已经取得并验证首屏服务端数据”的合成输入；组件从收到这份数据开始，不实现首屏读取。列表以每条报表稳定的 `key`（键）作为身份，排序不会更换报表身份。`periodStart` 用固定格式日期排序；`period` 只作 May、April 这样的显示标签，不按月份单词的字母顺序比较。两个排序按钮用 `aria-pressed` 暴露当前选择。初始数据由路由先给好，所以 `requestId=0` 时跳过请求。示例刻意只保留 React 状态和请求身份；真实 URL 历史接线在上面的浏览器章节。若需知道排序状态由哪些组件共同持有，见[如何在 React 中组合组件与复用行为？](./react-component-composition.md)。

> [!info]- 输入类型与首屏示意数据
>
> ~~~tsx
> import { useEffect, useState } from "react";
>
> type SortOrder = "recent" | "oldest";
> type Report = {
>   id: string;
>   period: string;
>   periodStart: string;
>   title: string;
> };
> type FetchReports = (sort: SortOrder) => Promise<Report[]>;
> type SuccessfulRequest = {
>   requestId: number;
>   sort: SortOrder;
>   reports: Report[];
> };
> type FailedRequest = {
>   requestId: number;
>   sort: SortOrder;
> };
>
> const initialReports: Report[] = [
>   {
>     id: "may",
>     period: "May",
>     periodStart: "2026-05-01",
>     title: "May summary"
>   },
>   {
>     id: "april",
>     period: "April",
>     periodStart: "2026-04-01",
>     title: "April summary"
>   }
> ];
>
> function sortReports(reports: Report[], sort: SortOrder): Report[] {
>   // periodStart 是固定格式 YYYY-MM-DD；复制后排序，不改写上游数据。
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
> ~~~

### 点击怎样记录新的选择？

下面依次展开同一个 `ReportsPage` 组件；输入、状态、Effect、派生值、JSX、路由这六段按顺序拼接，组成完整示例。`sort` 保存当前选择，`requestId` 标识本次确认请求；`lastSuccess` 保存最近一次有效成功数据，`lastFailure` 单独记录失败。分开保存后，当前请求失败也能保留旧数据，并明确告诉读者它尚未被这次请求确认。

~~~tsx
function ReportsPage({
  initialSort,
  initialReports,
  fetchReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
  fetchReports: FetchReports;
}) {
  const [sort, setSort] = useState(initialSort);
  const [requestId, setRequestId] = useState(0);
  const [lastSuccess, setLastSuccess] = useState<SuccessfulRequest>({
    requestId: 0,
    sort: initialSort,
    reports: initialReports
  });
  const [lastFailure, setLastFailure] = useState<
    FailedRequest | null
  >(null);

  function chooseSort(nextSort: SortOrder) {
    if (nextSort === sort) return;
    setSort(nextSort);
    setRequestId(id => id + 1);
  }
~~~

处理器只排入新选择和新编号。此时还没有向服务端发请求，也没有直接挪动列表节点。React 接着根据新状态 render、commit，再执行相应 Effect。

### 提交后，怎样识别这一轮请求？

这个 Effect 属于特定的一次已提交选择。它把当时的 `requestId` 和 `sort` 放进结果，同时用独立的 `ignore` 变量记录自己的生命周期。首屏 `requestId=0` 已有路由数据，直接跳过读取。

~~~tsx
  useEffect(() => {
    if (requestId === 0) return;

    let ignore = false;
    const currentRequestId = requestId;

    fetchReports(sort).then(
      reports => {
        if (!ignore) {
          setLastSuccess({
            requestId: currentRequestId,
            sort,
            reports
          });
        }
      },
      () => {
        if (!ignore) {
          setLastFailure({ requestId: currentRequestId, sort });
        }
      }
    );

    return () => {
      ignore = true;
    };
  }, [sort, requestId, fetchReports]);
~~~

`ignore` 在这次 Effect 被清理后阻止旧回调写状态。回调写入结果时附上的编号还承担另一项工作：即使旧回调抢在 cleanup 前运行，它也只能写入自己的编号，不能把后来的请求误标为已确认。稍后的时序表会分别跟踪这两种情况。

### 状态怎样决定列表和提示？

每次 render 都从当前状态算出以下三个值。`visibleReports` 用最近一次成功数据配合当前排序；是否确认或失败，则必须同时匹配当前请求编号和排序。

~~~tsx
  const requestConfirmed =
    lastSuccess.requestId === requestId && lastSuccess.sort === sort;
  const requestFailed =
    lastFailure !== null &&
    lastFailure.requestId === requestId &&
    lastFailure.sort === sort;
  const visibleReports = sortReports(lastSuccess.reports, sort);
~~~

| 当前结果 | 界面提示 | 列表使用的数据 |
| --- | --- | --- |
| 匹配当前编号和排序的失败结果存在 | 通过 `role="alert"` 显示失败 | 最近成功数据，按当前选择排序 |
| 否则，成功结果匹配当前编号与排序 | 通过 `role="status"` 显示已确认 | 本次成功数据 |
| 其余情况 | 通过 `role="status"` 显示等待当前请求 | 最近成功数据，按当前选择排序 |

返回的 JSX 根据这些值描述界面：按钮点击调用 `chooseSort`，其 `aria-pressed` 跟随 `sort`；列表遍历 `visibleReports`，以 `report.id` 为 key。React 的 commit 再把这份描述落实到 DOM。

> [!info]- 组件的 JSX 返回部分（承接上面的 ReportsPage）
>
> ~~~tsx
>   return (
>     <section>
>       <div role="group" aria-label="报表排序">
>         <button
>           type="button"
>           aria-pressed={sort === "recent"}
>           onClick={() => chooseSort("recent")}
>         >
>           Most recent
>         </button>
>         <button
>           type="button"
>           aria-pressed={sort === "oldest"}
>           onClick={() => chooseSort("oldest")}
>         >
>           Oldest first
>         </button>
>       </div>
>
>       {requestFailed ? (
>         <p role="alert">
>           {"当前选择：" + sort + "；请求 #" + requestId +
>             " 失败。仍显示上次成功（" + lastSuccess.sort +
>             "）的数据，并按当前选择排序。"}
>         </p>
>       ) : requestConfirmed ? (
>         <p role="status">
>           {"服务端已确认当前选择：" + sort + "（请求 #" + requestId + "）。"}
>         </p>
>       ) : (
>         <p role="status">
>           {"当前选择：" + sort + "；等待请求 #" + requestId +
>             "。下方保留上次成功（" + lastSuccess.sort +
>             "）的数据，并按当前选择排序。"}
>         </p>
>       )}
>
>       <ul>
>         {visibleReports.map(report => (
>           <li key={report.id}>{report.period} — {report.title}</li>
>         ))}
>       </ul>
>     </section>
>   );
> }
> ~~~

路由传入初始排序、首屏数据和数据层函数。下面的外层组件只展示这些输入怎样交接，不实现 URL/history 或真实请求。

> [!info]- 路由如何传入本例输入
>
> ~~~tsx
> function ReportsRoute({
>   fetchReports
> }: {
>   fetchReports: FetchReports;
> }) {
>   return (
>     <ReportsPage
>       initialSort="recent"
>       initialReports={initialReports}
>       fetchReports={fetchReports}
>     />
>   );
> }
> ~~~

`initialSort` 和 `initialReports` 是首屏输入；`useState` 只在首次挂载时用它们初始化。后续 URL 变化不能只改这两个 prop 就期待状态自动重置。由于 `fetchReports` 在依赖中，同一数据域内应传入稳定的数据层函数；若每次 render 都新建函数，Effect 会把它当作依赖变化而重新请求。若 `fetchReports` 内部读取原始 JSON，也应先在数据边界验证形状，而不是只用 TypeScript 类型断言；见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](../typescript/advanced-typescript.md)。完整路由需要在用户选择筛选时用 `pushState` 新增历史项；若用 `replaceState` 覆盖当前项，Back 就无法返回之前的选择。路由还要在 `popstate` 到来时把 URL 中的排序交给状态所有者。若 Back 恢复的排序需要重新向服务端确认，即使排序值和上一次相同，路由也要为这次读取发出新请求身份；若能复用该历史项对应的有效数据，则不必为了编号而强制请求。React Router 与单页应用（SPA）/多页应用（MPA）的边界见[React 路由如何把 URL 映射到视图？](./react-routing-and-navigation.md)。

请求身份只约束同一数据域内的确认结果，不负责隔离界面正在显示的数据。切换账户时，仅增加请求编号仍会让 `lastSuccess.reports` 中的旧账户行留在列表里，等待期间和失败时尤其明显。路由应在数据域变化时同时隔离或清空成功数据；一种直接做法是按账户 ID 重新挂载 `ReportsPage`，并传入该账户已取得的首屏数据。

**跟着 May 和 April 走一遍。** 初始 `requestId=0` 的路由输入是 May、April，首屏直接显示它们，不额外请求。点击 **Oldest first** 后，React 将 `sort=oldest` 与编号 `1` 排入更新；下一次 render 从上次成功的两条记录派生 April、May。commit 提交按钮、列表和等待提示；之后 Effect 才为 `oldest` 启动请求 `1`。排序操作由点击触发，纯排序在 render 执行，请求则由已提交选择的 Effect 发起。请求成功或失败时，回调只把带编号的结果排入状态；React 下一轮 render 和 commit 才更新确认提示或错误提示。

若请求 `1` 尚未结束时又点 **Most recent**，下一次 render 会把选择和请求身份计算为 `recent #2`，并从当前上次成功数据派生 May、April；commit 更新按钮、列表和等待 `#2` 的提示。这个 render 本身不会发请求。依赖改变的旧 Effect 会清理，然后新 Effect 才启动请求 `2`。旧请求 `1` 的响应回调可能在 cleanup 前或后运行，两个路径的生命周期和显示数据不同。这里比较的是回调实际运行的时刻；Promise 先完成，并不代表排队的回调已在 cleanup 前运行：

| 请求 1 回调相对 cleanup 的时机 | 响应回调 | 等待请求 2 时的列表与提示 |
| --- | --- | --- |
| cleanup 前运行 | `ignore` 仍为 `false`，成功回调可把响应写为 `lastSuccess`，但仍标记 `requestId=1`。 | 用这份刚到的成功数据按当前 `recent` 排序；确认条件仍不匹配 `#2`，所以界面继续等待请求 2。 |
| cleanup 后运行 | cleanup 已将 `ignore` 设为 `true`，回调不写入状态。 | 保留之前的 `lastSuccess`，按当前 `recent` 排序；界面继续等待请求 2。 |

若请求 `1` 的失败回调在 cleanup 前运行，它只记下编号 `1` 的失败，不改 `lastSuccess`，也不能把请求 `2` 标成失败；cleanup 后运行则直接被忽略。无论哪条路径，编号 `1` 都不能确认编号 `2`。请求身份决定哪个响应可以确认当前轮次；`lastSuccess` 决定等待或失败时屏幕拿哪份同一数据域的成功数据来显示。若当前请求失败，独立的 `role="alert"` 会报错，列表保留同一数据域最近成功的数据，并按当前选择排序；不会把旧数据说成服务端刚确认的结果。

cleanup 守卫是“Effect 已被 React 清理后不再采用它的结果”，不是取消网络请求的承诺。Back 若需重新向服务端确认同一排序，也由路由创建新的请求身份；若重用缓存数据，则由路由提供相应有效结果。生产应用要缓存、去重、取消、重试或协调多组件请求时，通常由路由数据层或查询库承担这些契约，见[React 如何维护服务端数据与乐观更新？](./react-server-state-and-optimistic-updates.md)。

## 渲染、协调与提交是不同工作

`render` 阶段调用组件，把当前 props、state 转成 JSX 元素描述。它是计算，不是直接改 DOM。并发特性可能让尚未提交的 render 暂停、重试或放弃；因此不能在 render 中发请求、写 URL、改现有对象，或手动改 React 管理的 DOM。**是否调用组件、是否产生 DOM 变化、浏览器是否绘制，是三个不同问题。**

reconciliation（协调）按树中的位置、元素类型和 key（键）对应前后两次描述。本例的 `sortReports` 每次按当前 `sort` 生成新数组；它不修改 `lastSuccess.reports`。May 和 April 的 `id` 在顺序改变时保持不变，`key`（键）取 `report.id`，让 React 把前后两棵列表中属于同一报表的行对应起来。key 只需在同一列表兄弟节点间稳定且唯一；用数组下标代替数据身份，排序后行内状态可能跟着位置走。

render 完成后才进入 `commit`（提交阶段），React 将必要的改动写到宿主树。一个 setter 不等于一次 DOM 修改：新旧界面若相同，React 可以不改 DOM；若排序改变，则更新所需的行位置和按钮属性。React 负责 DOM commit，浏览器按需在后续渲染机会处理样式、布局或绘制；任务排队和帧调度的细节见[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)。浏览器帧与 React setter 不是一一对应关系。

React 会把同一批的多个状态更新一起处理，避免逐个更新都触发一次完整的 render/commit，这叫 batching（批量处理）。本例点击处理器同时排入 `sort` 与 `requestId`，React 不会先提交一个只改排序、又立刻提交一个只改编号的半成品。React 18 起，使用 `createRoot` 的应用也会自动批量处理 Promise、定时器和原生事件处理器中的更新；React 18 的旧 `ReactDOM.render` 根会保留旧的批处理范围，升级后切换根 API 才启用新行为。批量处理不会改写当前 handler 的快照，也不表示每个更新都会单独绘制一帧。

> [!example] JSX 描述界面，不是 HTML（超文本标记语言）字符串
> JSX 是描述元素的语法。构建工具可以把它转换成自动运行时的 `react/jsx-runtime` 调用，也可以转换成经典的 `React.createElement` 调用。转换方式不改变 state 快照、render 和 commit 的关系。

## Effect在提交后同步外部系统

`Effect` 适合做由“组件现在需要与外部系统保持一致”触发的工作，例如订阅、连接，或按已提交选择读取服务端数据。它不适合代替点击处理器执行只由那次点击触发的一次性动作，也不适合在两份 React state 之间搬运可直接算出的值。需要时 `useEffect` 在 commit 后运行；依赖改变时先用旧闭包执行 `cleanup`（清理），再用新值执行 `setup`（建立）；卸载时再执行最后一次清理。依赖应包含 setup 实际读取的响应式值，React 用 `Object.is` 比较它们。本例的 `sort`、`requestId` 与 `fetchReports` 都在依赖中。

React 不能保证 Effect 总在浏览器 paint（绘制）之后运行。与点击交互有关的 Effect 可能在 paint 前运行；其他更新通常会让浏览器先绘制。若任务本身需要测量或在绘制前调整 DOM，可评估 `useLayoutEffect`；本例发起数据请求，不依赖这个精确帧时机。Promise 失败由此处显式转为状态与错误提示；渲染期间抛出的异常属于错误边界处理范围。

根组件包在 `StrictMode`（严格模式）中时，开发环境首次挂载会额外执行一次 Effect 的 `setup → cleanup`，再执行正式 setup，用来检查清理能否撤销建立工作。不是生产环境每次都发两次请求。本例初次调用因 `requestId=0` 提前返回，既不启动请求也没有可调用的 cleanup；之后排序更新才会为请求建立清理函数。即便使用 ignore，网络请求本身也可能继续运行；它解决的是清理后旧闭包不能采用结果。

类组件的 `render()` 同样必须保持纯计算。维护旧类组件时，`componentDidMount` 和 `componentDidUpdate` 可在 DOM 提交后同步外部系统，`componentWillUnmount` 可清理连接；若要在 DOM 更新前读取布局快照，使用 `getSnapshotBeforeUpdate`。这些生命周期帮助定位阶段，但不与函数组件的 Effect 一一对应；React 仍支持 class components（类组件），但新组件通常使用函数组件。若一次排序确实让用户输入变慢，再看[如何让报表筛选在昂贵更新时保持响应？](./advanced-react.md)；若是渲染抛出的异常需要恢复，则看[React 错误边界能恢复哪些失败？](./react-error-boundaries.md)。

> [!info]- 来源与版本核验（当前 React 文档 19.3；历史行为按 React 18 核验，日期 2026-11-12）
>
> - 状态快照、setter 请求下一次 render、处理器保留当前状态，以及函数 updater 在队列中逐个计算：[State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)、[`useState`](https://react.dev/reference/react/useState)，React 19.3 文档。
>
> - render/commit 分工、render 纯净及组件调用不必对应 DOM 改动：[Render and Commit](https://react.dev/learn/render-and-commit)、[Keeping Components Pure](https://react.dev/learn/keeping-components-pure)，React 19.3 文档。
>
> - 同级 key 与树位置怎样确定状态身份：[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 19.3 文档。
>
> - Effect 与事件的不同触发来源，依赖比较，改变依赖时先 cleanup 再 setup，Effect 相对 paint 的时序条件，以及 fetch 结果忽略模式：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)、[`useEffect`](https://react.dev/reference/react/useEffect)，React 19.3 文档；绘制前测量布局的 API：[`useLayoutEffect`](https://react.dev/reference/react/useLayoutEffect)，React 19.3 文档。
>
> - 根 StrictMode 的开发时额外 Effect setup/cleanup 检查：[StrictMode](https://react.dev/reference/react/StrictMode)，React 19.3 文档。
>
> - React 18 `createRoot` 与 legacy `ReactDOM.render` 的行为边界：[How to Upgrade to React 18 — Client Rendering APIs](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#updates-to-client-rendering-apis)；自动批处理：[React v18 — Automatic Batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)；并发 render 的中断、恢复、放弃与完整树提交：[React v18 — What Is Concurrent React?](https://react.dev/blog/2022/03/29/react-v18#what-is-concurrent-react)，React 团队发布文档。
>
> - `pushState` 添加历史项、`replaceState` 替换当前项：[HTML Standard — History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，核验日期 2026-11-12。
>
> - JSX 自动与经典转换：[Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform)，React 团队，2020-09-22。
>
> - 类组件 render、`getSnapshotBeforeUpdate` 与 mount/update/unmount lifecycle：[Component](https://react.dev/reference/react/Component)，React 19.3 文档。
>
> - URL 片段只供客户端定位且不会随 HTTP（超文本传输协议）请求发给服务端：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-12。
