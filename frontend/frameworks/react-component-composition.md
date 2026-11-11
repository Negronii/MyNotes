# 如何在 React 中组合组件与复用行为？

**案例背景。** 报表页的浏览器地址为 `/reports?sort=recent#summary`；服务端按 `sort=recent` 返回 May、April，`#summary` 只供浏览器定位。选择 **Oldest first** 后，排序状态变成 `oldest`，可见顺序应为 April、May。这个排序状态要同时驱动工具栏的选中状态和列表顺序，因此由包含二者的最近共同父组件持有；列表只拿已排序的报表数组，工具栏收到更新回调。沿 props（属性）、Context（上下文）、自定义 Hook（自定义钩子）、ref（引用）逐层选择能表达清楚所有权的边界，不把组件组合变成隐式的全局通信。

本章片段只展示组件之间的 state 归属，不实现 URL 与历史栈；完整应用用[浏览器主线的 `pushState` 与 `popstate` 路径](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)新增筛选历史并在后退时恢复排序。

## 把状态放在共同使用者之上的最近一层

排序按 ISO 日期字段 `periodStart` 进行，显示标签 `period` 不参与排序；最近共同父组件持有排序状态，并把它传给工具栏和列表。

~~~tsx
import { useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; periodStart: string; title: string };

function sortReports(reports: Report[], sort: SortOrder) {
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function ReportsPage({ reports, initialSort }: { reports: Report[]; initialSort: SortOrder }) {
  const [sort, setSort] = useState(initialSort);
  const rows = sortReports(reports, sort);

  return (
    <main>
      <ReportToolbar sort={sort} onSortChange={setSort} />
      <ReportList reports={rows} />
    </main>
  );
}

function ReportToolbar({
  sort,
  onSortChange
}: {
  sort: SortOrder;
  onSortChange: (sort: SortOrder) => void;
}) {
  return (
    <div role="group" aria-label="报表排序">
      <button
        type="button"
        aria-pressed={sort === "recent"}
        onClick={() => onSortChange("recent")}
      >
        Most recent
      </button>
      <button
        type="button"
        aria-pressed={sort === "oldest"}
        onClick={() => onSortChange("oldest")}
      >
        Oldest first
      </button>
    </div>
  );
}

function ReportList({ reports }: { reports: Report[] }) {
  return (
    <ul>
      {reports.map(report => (
        <li key={report.id}>{report.period} — {report.title}</li>
      ))}
    </ul>
  );
}
~~~

数据沿 props（属性）向下传，用户意图用 callback prop（回调属性）向上交给状态所有者。这个结构让一次点击的去向可见。若两个组件不共享状态，把 state（状态）提到更高层只会扩大更新范围；若多个远距离组件确实要读取主题、地区设置等值，可以在共同子树上用 Context；跨多个功能共享且需要统一更新策略时，再考虑 store（共享状态容器）。若确实选 Redux 管理这类共享客户端状态，action、reducer、selector 与异步工作流见[Redux 如何组织共享界面状态与异步工作？](./redux-state-and-async-workflows.md)。

Context 适合让同一子树里相距较远的组件读取报表视图偏好。它传递值，但不持有状态；下面 `ReportViewProvider` 用 `useState` 持有行距偏好，工具栏通过 `useContext` 读取并调用 setter，列表也读取新值来呈现行距：

~~~jsx
import { createContext, useContext, useState } from "react";

const ReportViewContext = createContext(null);

function ReportViewProvider({ children }) {
  const [density, setDensity] = useState("comfortable");

  return (
    <ReportViewContext value={{ density, setDensity }}>
      {children}
    </ReportViewContext>
  );
}

function useReportView() {
  const value = useContext(ReportViewContext);
  if (value === null) throw new Error("useReportView 必须在 ReportViewProvider 内调用");
  return value;
}

function DensityControl() {
  const { density, setDensity } = useReportView();
  const nextDensity = density === "compact" ? "comfortable" : "compact";

  return (
    <button type="button" onClick={() => setDensity(nextDensity)}>
      {density === "compact" ? "恢复舒适行距" : "切换紧凑行距"}
    </button>
  );
}

function ReportRows({ reports }) {
  const { density } = useReportView();
  return (
    <ul style={{ lineHeight: density === "compact" ? 1.2 : 1.8 }}>
      {reports.map(report => <li key={report.id}>{report.title}</li>)}
    </ul>
  );
}

function ReportsView({ reports }) {
  return (
    <ReportViewProvider>
      <DensityControl />
      <ReportRows reports={reports} />
    </ReportViewProvider>
  );
}
~~~

`DensityControl` 和 `ReportRows` 都是 Provider 后代，所以 `useContext` 读取最近的 `ReportViewContext` 值。点击按钮调用 Provider 持有的 setter，`density` 与 Provider 提供的 `value` 随之改变；读取这个 Context 的组件会获得新值并更新。若改为 React 18 或更早版本，应把开标签 `<ReportViewContext value={...}>` 改为 `<ReportViewContext.Provider value={...}>`，也把闭标签 `</ReportViewContext>` 改为 `</ReportViewContext.Provider>`。TypeScript 的完整 Context 与自定义 Hook 类型边界见归档中的[Context 与自定义 Hook 示例](../../archive/front-end/0-1_Learning_Notes/react_typescript/typed-hooks-and-context.md)。

服务端拥有的报表记录仍属于服务端状态。把它们放进 Context 不会自动提供查询身份、缓存新鲜度、取消或变更协调；这些由[服务端状态章节](./react-server-state-and-optimistic-updates.md)讲解。

## 用自定义Hook复用状态行为

自定义 Hook 把同一种有状态行为封装起来，但每次调用默认有各自的 state。下面的 Hook 让多个组件共享“监听窗口大小”这一行为，而不会让它们共享同一份 `size`：

~~~jsx
import { useEffect, useState } from "react";

function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    function update() {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    }

    window.addEventListener("resize", update);
    update();
    return () => window.removeEventListener("resize", update);
  }, []);

  return size;
}
~~~

每个 Hook（钩子）调用都注册自己的监听器；如果想共享一份外部 store，应明确连接同一 store。Effect（副作用同步）的 setup、cleanup 和过期请求处理见[更新轮次](./react-basics.md#effect在提交后同步外部系统)。Hook 通常在组件或其他 Hook 顶层以固定顺序调用。React 的 `use` API 例外：可在条件和循环中读取 Promise 或 Context，但仍须处于组件或 Hook 中，且不能放进 `try/catch`。

React 19.2 增加的 `useEffectEvent` 用于 Effect 内部的事件式逻辑：它读取调用时最新提交的值，却不让这些值重新触发连接。它只可在本组件的 Effect 或其他 Effect Event 中调用，不应传给子组件、用作普通事件回调，或借此隐藏本来应该声明的依赖。

## ref用于窄范围的命令式能力

state 改变后要更新界面就用 state；ref 则持有不驱动界面的可变值，或访问已经提交的 DOM。下面父工具栏只能调用搜索框公开的 `focus()`，实际输入节点仍由子组件持有：

~~~jsx
import { useImperativeHandle, useRef } from "react";

function ReportSearchInput({ ref }) {
  const inputRef = useRef(null);
  useImperativeHandle(ref, () => ({
    focus() {
      inputRef.current?.focus();
    }
  }), []);
  return <input ref={inputRef} aria-label="搜索报表" />;
}

function ReportFocusControl() {
  const searchRef = useRef(null);
  return (
    <>
      <ReportSearchInput ref={searchRef} />
      <button type="button" onClick={() => searchRef.current?.focus()}>
        聚焦搜索
      </button>
    </>
  );
}
~~~

React 19 的函数组件可以把 `ref`（引用）当作 prop 接收；React 18 及更早版本的组件需要 `forwardRef` 转发。若父组件只需要 `focus()`，可用 `useImperativeHandle` 暴露这个有限动作，而不把内部节点和实现一起交出去。选 API 时保留子组件的资源所有权。

## 组合组件与旧式逻辑复用接口

children 组合可让调用方控制布局；render prop（渲染属性）把数据交给一个函数，由调用方选择渲染结构；higher-order component（高阶组件，HOC）则包装组件并返回新组件。自定义 Hook 往往适合复用 Hook 状态逻辑，但旧库的 render prop 或 HOC 也可能是明确、稳定的 API，不必只为“改成 Hook”而重写。

条件分支也属于组合的一部分：二选一用三元表达式，只在条件为真时渲染用逻辑 AND，能早退时用 `if`。由于 `0 && <List />` 的结果是数字 `0`，若空数组长度可能为零，应写成 `{items.length > 0 && <List />}`。

这些模式解决状态归属和行为复用。若一次交互的 React render 成本已经测出，再看[如何测量并减少不必要的React工作？](../performance/react-rendering-optimization.md)；本章不把 memoization（记忆化）当作组件组合规则。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - props、共享 state 与 Context 的所有权：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component)、[Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)、[Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)，React 19.3 文档。
> - Context 创建、最近 Provider 的读取值、默认值及 Provider 语法（React 19 用 `<Context value>`；旧版用 `<Context.Provider>`）：[createContext](https://react.dev/reference/react/createContext)、[useContext](https://react.dev/reference/react/useContext)，React 19 官方文档，核对日期 2026-11-09。
> - 自定义 Hook 与 Hook 调用边界：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)、[Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)、[`use`](https://react.dev/reference/react/use)，React 19.3 文档。
> - React 19.2 的 Effect Event 语义与限制：[useEffectEvent](https://react.dev/reference/react/useEffectEvent)，React 官方 API 参考；React 19.2 发布日期 2025-10-01，见[React Blog](https://react.dev/blog)。
> - ref、forwardRef 与受限命令式接口：[useRef](https://react.dev/reference/react/useRef)、[forwardRef](https://react.dev/reference/react/forwardRef)、[useImperativeHandle](https://react.dev/reference/react/useImperativeHandle)，React 19.3 文档。
> - toggle button 的 `aria-pressed` 状态：[WAI-ARIA APG — Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)，W3C WAI 官方模式，核验日期 2026-11-06。
