# 如何让报表筛选在昂贵更新时保持响应？

**案例背景。** 报表页当前 URL 为 `/reports?sort=recent#summary`，服务端给出 May、April；选择 **Oldest first** 后，`sort=oldest` 让行顺序变成 April、May。随后输入标题筛选时，输入值要即时显示；若结果视图渲染很重，可以让它稍后跟进。React 提供的是更新优先级和可中断的后台 render（渲染），不是把 JavaScript 移到另一个线程，也不是按固定时间延迟请求。状态快照在[React更新轮次](./react-basics.md)说明；服务端查询身份仍由[服务端状态章节](./react-server-state-and-optimistic-updates.md)负责。URL 与 Back 的同步采用[浏览器历史栈机制](../browser/browser-navigation-and-history.md#让筛选状态跟随地址栏与前进后退)，本章代码省略这层连接。

## 输入保持即时，结果视图可以延后

下面把标题筛选输入作为紧急更新，并把搜索词交给 `useDeferredValue`。昂贵过滤放进结果子组件；示例假设该子树的构建结果确实能在 props（属性）不变时跳过重渲染。仅启用 React Compiler（React 编译器）不保证它覆盖了这个子树，需检查实际编译结果；否则输入更新仍可能让结果子组件立即重算。边界的选择和检查见[React渲染优化章节](../performance/react-rendering-optimization.md)。`isStale` 表示结果还对应上一个查询词，所以界面可以保留旧结果同时标出正在更新：

~~~jsx
import { useDeferredValue, useState } from "react";

function ReportFilter({ reports }) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <section aria-busy={isStale}>
      <label>
        搜索报表
        <input value={query} onChange={event => setQuery(event.target.value)} />
      </label>
      {isStale && <p>结果仍对应上一个搜索词，正在更新。</p>}
      <ReportResults reports={reports} query={deferredQuery} />
    </section>
  );
}

function ReportResults({ reports, query }) {
  const visibleReports = reports.filter(report =>
    report.title.toLowerCase().includes(query.toLowerCase())
  );
  return <ul>{visibleReports.map(report => <li key={report.id}>{report.title}</li>)}</ul>;
}
~~~

输入从空字符串变为 `"apr"` 时，紧急更新先显示 `apr`；若 deferred 值仍为空，列表暂时保留 April、May，`isStale` 显示结果仍旧。随后当 deferred 值成为 `"apr"` 并提交时，列表只剩 April。`useDeferredValue` 不设定毫秒延迟，也不保证某个结果会跳过；React 可中断尚未提交的组件工作，但不能抢占已经开始运行的同步 `reports.filter(...)`。如果全量过滤本身是长任务，优先减少计算量、分块或放到 Web Worker（网页工作线程）；如果耗时来自大量行组件的渲染，延后子树更新才有帮助。它也不是 debounce（防抖），不承诺减少请求数；请求频率要由明确的产品策略或服务端查询层管理。

## 用Transition标记非紧急的界面切换

打开报表摘要或切换大视图通常不需要阻塞输入。`useTransition` 可把这类 Transition（过渡更新）标记为非紧急，并通过 `isPending` 暴露仍在准备的状态。它不能控制受控文本输入；如果 Transition render 执行一次同步 `reports.filter(...)`，React 也不能在这个函数运行中途抢占 JavaScript。

~~~jsx
import { Suspense, lazy, useState, useTransition } from "react";

const ReportSummary = lazy(() => import("./ReportSummary.js"));

function ReportWorkspace({ reports }) {
  const [view, setView] = useState("rows");
  const [isPending, startTransition] = useTransition();

  function openSummary() {
    startTransition(() => setView("summary"));
  }

  return (
    <main>
      <button type="button" onClick={openSummary}>查看摘要</button>
      {isPending && <span>正在准备摘要视图…</span>}
      <Suspense fallback={<p>正在加载摘要模块…</p>}>
        {view === "summary"
          ? <ReportSummary reports={reports} />
          : <ul>{reports.map(report => <li key={report.id}>{report.title}</li>)}</ul>}
      </Suspense>
    </main>
  );
}
~~~

Suspense（挂起边界）仅在子树通过受支持的方式暂停时显示最近边界的 fallback（备用界面）；上例由 `lazy` 加载摘要模块。点击前列表已显示；点击后视图状态在 Transition 中更新，若模块仍在加载，实际画面是查看摘要按钮、`isPending` 等待文案和旧的 April、May 列表。模块加载成功后才提交摘要。这个交互不会直接显示“正在加载摘要模块”的 fallback；若首次加载时边界里尚无已显示内容，或非 Transition 更新导致内容被隐藏，fallback 才承担等待画面。读缓存 Promise 的 `use`、服务端组件或明确支持 Suspense 的框架也可触发它。TanStack Query v5 的 `useSuspenseQuery` 是专门的挂起查询入口；普通 `useQuery` 的 pending 状态默认不会触发 Suspense，把普通 `fetch` 放在 `useEffect` 中也不会自动挂起。异步查询的错误和重试不能只靠 loading fallback 处理。

React 19 的 Transition 支持异步 Action（动作）。当前文档仍指出：跨 `await` 后的 state 更新若要继续保持 Transition 优先级，需要再包一层 `startTransition`；自定义异步动作若可能乱序完成，仍需显式管理结果顺序。React 19.3 下这些状态优先级规则不改变服务端数据的一致性契约。

如果长同步计算本身仍占住主线程，先检查算法和工作量；必要时移到 Web Worker（网页工作线程）。若成本来自屏幕上挂载了太多报表行，转到[长列表何时适合虚拟滚动？](../performance/rendering-and-computation-optimization.md)。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 延后值不等于 debounce，后台 render 可中断：[useDeferredValue](https://react.dev/reference/react/useDeferredValue)，React 19.3 文档。
> - Transition 的优先级、`isPending`、异步 Action 与 `await` 后再包 state 更新：[useTransition](https://react.dev/reference/react/useTransition)，React 19.3 文档；核验日期 2026-11-06。
> - 支持 Suspense 的触发条件、最近边界和 fallback：[Suspense](https://react.dev/reference/react/Suspense)、[lazy](https://react.dev/reference/react/lazy)、[`use`](https://react.dev/reference/react/use)，React 19.3 文档。
> - TanStack Query v5 专用挂起查询：[Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense)、[`useSuspenseQuery`](https://tanstack.com/query/latest/docs/framework/react/reference/useSuspenseQuery)，v5.90.3。
> - Compiler 是否覆盖指定组件的检查：[React Compiler Debugging](https://react.dev/learn/react-compiler/debugging)，React 19.3 文档。
> - React 文档当前版本及本章 API 适用版本：[Versions](https://react.dev/versions)，最新文档标为 19.3，核验日期 2026-11-06。
