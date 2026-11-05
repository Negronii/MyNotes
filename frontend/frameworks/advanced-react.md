# How can a React search interface stay responsive as results update? / React搜索界面如何在更新结果时保持响应？

**Core answer / 核心回答：** Keep the controlled input urgent, and let React defer the expensive result view or mark a navigation-like update as a Transition. A Suspense boundary can limit loading feedback to the result region. Include all result-changing inputs in the query key; use a separate debounce only when reducing request frequency is a product requirement. The state snapshot and commit path are explained in [React Basics / React基础](./react-basics.md). / 保持受控输入紧急更新，让 React 延后昂贵的结果视图，或把类似导航的更新标记为 Transition。Suspense 边界可以把加载反馈限制在结果区域。查询键要包含所有影响结果的输入；只有产品需要减少请求频率时才另做 debounce。state 快照与提交路径见[React Basics / React基础](./react-basics.md)。

This is the main interaction route: typing requests an urgent input update, while a deferred query value drives a Suspense-enabled result view. `useDeferredValue` schedules rendering; it is not a debounce and does not suppress requests. The [server-state deep question](./react-server-state-and-optimistic-updates.md) owns query identity, cache freshness, mutation, and rollback semantics.

## Schedule input and results separately / 分开调度输入和结果

This search panel keeps the text input responsive and places the loading fallback around only the result list. Query-key identity and server-cache freshness are explained in [the server-state deep question](./react-server-state-and-optimistic-updates.md). `useSuspenseQuery` is the TanStack Query v5 data source that suspends here; a normal query or fetch started in an Effect does not automatically suspend. The memoized result boundary allows React to skip this child when an urgent parent render leaves `deferredQuery` and `tab` unchanged; without it, the child still renders on each parent input update even though the deferred value is old. It renders again when either deferred prop advances.

~~~tsx
import { memo, Suspense, useDeferredValue, useState, useTransition } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";

type SearchHit = { id: string; title: string };
declare function searchTasks(query: string, tab: "tasks" | "summary"): Promise<SearchHit[]>;

function TaskSearch() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<"tasks" | "summary">("tasks");
  const [isPending, startTransition] = useTransition();
  const deferredQuery = useDeferredValue(query);
  const showingOlderResults = query !== deferredQuery;

  function selectTab(next: "tasks" | "summary") {
    startTransition(() => setTab(next));
  }

  return (
    <section>
      <input
        aria-label="Search tasks"
        value={query}
        onChange={event => setQuery(event.target.value)}
      />
      <button type="button" onClick={() => selectTab("summary")}>Summary</button>
      {isPending && <span>Updating view…</span>}
      <Suspense fallback={<p>Loading results…</p>}>
        <div aria-busy={showingOlderResults}>
          <TaskSearchResults query={deferredQuery} tab={tab} />
        </div>
      </Suspense>
    </section>
  );
}

const TaskSearchResults = memo(
  function TaskSearchResults({ query, tab }: { query: string; tab: "tasks" | "summary" }) {
    const { data } = useSuspenseQuery({
      queryKey: ["tasks", "search", query, tab],
      queryFn: () => searchTasks(query, tab)
    });
    return <ul>{data.map(hit => <li key={hit.id}>{hit.title}</li>)}</ul>;
  }
);
~~~

`useTransition` exposes `isPending` and marks state updates inside `startTransition` as non-urgent; its callback runs immediately, and it cannot control a text input. With an async action, wrap state updates after each `await` in another `startTransition` to mark them as transitions. `useDeferredValue` lets a child keep seeing the previous value while React prepares an interruptible background render. It has no fixed delay and does not suppress network requests, so use an explicit debounce when the goal is fewer requests. Neither API parallelizes JavaScript on another CPU thread or makes a long synchronous calculation faster; use a better algorithm, memoization, or a worker when computation itself blocks. `Suspense` only shows this fallback when its child suspends through a supported source such as `use` with a cached Promise or a Suspense-enabled framework/library. Pair data errors with an [Error Boundary](./react-error-boundaries.md) or use explicit pending/error states; Suspense is not a request error handler. Keep renders pure because React may retry interrupted work.

## Who owns server data and local UI state? / 服务端数据与本地界面状态由谁管理？

**Core answer / 核心回答：** Keep transient choices and drafts in local state; identify server queries by every result-changing input, give cached data an explicit freshness policy, and reconcile mutations with the server response. The complete query, optimistic-update, rollback-race, and A-to-B identity example is in [How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？](./react-server-state-and-optimistic-updates.md). / 将临时选择和草稿保存在本地 state 中；查询键包含所有影响结果的输入，为缓存规定新鲜度，并用服务端响应协调变更。完整的查询、乐观更新、回滚竞态和 A→B 身份示例见[React界面如何维护服务端数据与乐观更新的正确性？](./react-server-state-and-optimistic-updates.md).

Keep the search interaction readable by passing results and callbacks explicitly. If the same behavior appears in multiple components, see [React component composition / React 组件组合](react-component-composition.md) for state ownership, reusable Hooks, and narrow imperative actions.

**Sources checked 2026-10-15** — [React: `useTransition`](https://react.dev/reference/react/useTransition), [`useDeferredValue`](https://react.dev/reference/react/useDeferredValue), [React `Suspense`](https://react.dev/reference/react/Suspense), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [React `use`](https://react.dev/reference/react/use).
