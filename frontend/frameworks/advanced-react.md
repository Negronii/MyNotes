# Advanced React / React进阶

## How can components communicate? / React组件如何通信？

**Core answer / 核心回答：** Keep data flow explicit: pass data down with props, send events up with callback props, and use Context or a store when many distant consumers need shared state. Refs expose imperative capabilities; they are not a substitute for state that drives visible UI. / 保持数据流清晰：用 props 向下传数据，用回调 props 向上传事件；多个较远组件需要共享状态时再考虑 Context 或 store。ref 用于暴露命令式能力，不应替代驱动界面的 state。

~~~jsx
const ThemeContext = createContext("light");

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  );
}

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>Toolbar</div>;
}
~~~

A child can notify its parent through a callback prop. Use Context for values such as theme or locale that are needed across a subtree; a store can help when shared state and update patterns grow more complex. Custom Hooks share stateful logic, but each call has its own Hook state unless the Hook deliberately connects to shared state. Avoid using an event bus as a default substitute for React's data flow.

## Who owns server data and local UI state? / 服务端数据与本地界面状态由谁管理？

**Core answer / 核心回答：** Keep transient choices such as the selected row, open dialog, or draft input in local React state. Treat records owned by a server as server state: identify each query by all inputs that affect it, define when cached data is fresh, and invalidate or update affected entries after a mutation. A query cache is a client read model, not the source of truth. / 将选中行、打开的对话框和输入草稿等临时选择保存在 React 本地状态中。服务器拥有的记录属于服务端状态：查询键要包含所有影响结果的输入，缓存需要明确新鲜期，变更后要更新或失效相关缓存。查询缓存是客户端读模型，不是数据的权威来源。

For example, selecting a row is local UI state, while the list and selected record come from the server. Separate query keys encode their identities; include filters, page, or account identifiers too when they change the result. In TanStack Query v5, `staleTime` defines how long a result is considered fresh. Once stale, it can refetch on configured events; targeted invalidation marks matching entries stale and refetches active observers. The value is a freshness policy, not a promise that the server data cannot change.

~~~tsx
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

type Task = { id: string; title: string; done: boolean };
type TaskPatch = Pick<Task, "id"> & Partial<Pick<Task, "title" | "done">>;

// These request functions parse and validate their responses at the API boundary.
declare function listTasks(): Promise<Task[]>;
declare function getTask(id: string, signal: AbortSignal): Promise<Task>;
declare function saveTask(patch: TaskPatch): Promise<Task>;

const taskKeys = {
  list: ["tasks", "list"] as const,
  detail: (id: string) => ["tasks", "detail", id] as const
};

function useTaskList() {
  return useQuery({
    queryKey: taskKeys.list,
    queryFn: listTasks,
    staleTime: 30_000
  });
}

function useTaskDetail(id: string) {
  return useQuery({
    queryKey: taskKeys.detail(id),
    queryFn: ({ signal }) => getTask(id, signal)
  });
}

function TaskWorkspace() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const list = useTaskList();

  if (list.isPending) return <p>Loading tasks…</p>;
  if (list.isError) return <p role="alert">Could not load tasks.</p>;

  return (
    <div>
      <ul>
        {list.data.map(task => (
          <li key={task.id}>
            <button type="button" onClick={() => setSelectedId(task.id)}>
              {task.title}
            </button>
          </li>
        ))}
      </ul>
      {selectedId !== null && <TaskDetail id={selectedId} />}
    </div>
  );
}

function TaskDetail({ id }: { id: string }) {
  const detail = useTaskDetail(id);
  if (detail.isPending) return <p>Loading selected task…</p>;
  if (detail.isError) return <p role="alert">Could not load this task.</p>;
  return <p>{detail.data.title}</p>;
}

function useSaveTask() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: saveTask,
    onMutate: async patch => {
      const detailKey = taskKeys.detail(patch.id);
      await Promise.all([
        client.cancelQueries({ queryKey: taskKeys.list }),
        client.cancelQueries({ queryKey: detailKey })
      ]);

      const previousList = client.getQueryData<Task[]>(taskKeys.list);
      const previousDetail = client.getQueryData<Task>(detailKey);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === patch.id ? { ...task, ...patch } : task)
      );
      if (previousDetail !== undefined) {
        client.setQueryData<Task>(detailKey, { ...previousDetail, ...patch });
      }
      return { previousList, previousDetail };
    },
    onError: (_error, patch, previous) => {
      if (previous?.previousList !== undefined) {
        client.setQueryData(taskKeys.list, previous.previousList);
      }
      if (previous?.previousDetail !== undefined) {
        client.setQueryData(taskKeys.detail(patch.id), previous.previousDetail);
      }
    },
    onSuccess: saved => {
      client.setQueryData(taskKeys.detail(saved.id), saved);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === saved.id ? saved : task)
      );
    },
    onSettled: (_data, _error, patch) => Promise.all([
      client.invalidateQueries({ queryKey: taskKeys.list }),
      client.invalidateQueries({ queryKey: taskKeys.detail(patch.id) })
    ])
  });
}
~~~

The mutation cancels in-flight reads before writing optimistically, saves snapshots for rollback, replaces both cached views with the server response on success, then invalidates them to reconcile other changes. A pending save can disable its button; on error, the snapshot restores the visible list/detail and the UI can show a retry message. Because rollback restores the whole list snapshot, this example requires at most one mutation in flight across the shared list—not merely one save per task. Otherwise A can fail after B succeeds and restore B's old row too. Broader concurrency needs operation-scoped or version-aware reconciliation instead of blindly restoring that snapshot. If the user switches from task A to B while A is loading, the detail key changes from `detail/A` to `detail/B`; A may finish into its own cache entry, but cannot become B's displayed record. Passing the query's `AbortSignal` to `fetch` can also stop obsolete network work when the service consumes it. A manually managed Effect needs its own stale-result guard or cleanup; the `useWindowSize` Effect in the custom Hook section below shows cleanup, and an Effect fetch by itself does not activate Suspense. See [Advanced TypeScript / TypeScript进阶](../typescript/advanced-typescript.md) for validating API JSON before treating it as a `Task`.

## How do concurrent UI updates and Suspense work? / 并发界面更新与 Suspense 如何工作？

**Core answer / 核心回答：** Keep input state urgent so each keystroke appears immediately; defer expensive result rendering or mark a navigation-like state update as a Transition. React can interrupt and retry that render work so urgent updates get priority. A Suspense boundary gives one part of the screen a fallback while a Suspense-enabled child is not ready. / 输入状态应保持紧急，以便每次按键都立即显示；可以延后昂贵结果区域的渲染，或把类似导航的状态更新标记为 Transition。React 可以中断并重试这部分渲染，让紧急更新优先。Suspense 边界则在支持 Suspense 的子树尚未就绪时，为该区域显示 fallback。

This search panel keeps the text input responsive and places the loading fallback around only the result list. `useSuspenseQuery` is the TanStack Query v5 data source that suspends here; a normal query or fetch started in an Effect does not automatically suspend. The memoized result boundary allows React to skip this child when an urgent parent render leaves `deferredQuery` and `tab` unchanged; without it, the child still renders on each parent input update even though the deferred value is old. It renders again when either deferred prop advances.

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

`useTransition` exposes `isPending` and marks state updates inside `startTransition` as non-urgent; its callback runs immediately, and it cannot control a text input. With an async action, wrap state updates after each `await` in another `startTransition` to mark them as transitions. `useDeferredValue` lets a child keep seeing the previous value while React prepares an interruptible background render. It has no fixed delay and does not suppress network requests, so use an explicit debounce when the goal is fewer requests. Neither API parallelizes JavaScript on another CPU thread or makes a long synchronous calculation faster; use a better algorithm, memoization, or a worker when computation itself blocks. `Suspense` only shows this fallback when its child suspends through a supported source such as `use` with a cached Promise or a Suspense-enabled framework/library. Pair data errors with an Error Boundary or use explicit pending/error states; Suspense is not a request error handler. Keep renders pure because React may retry interrupted work.

## When should you use memo, useMemo, or useCallback? / 何时使用 memo、useMemo和useCallback？

**Core answer / 核心回答：** These are performance tools, not correctness tools. React.memo can skip rendering when props compare equal; useMemo caches a calculated value; useCallback caches a function reference. Add them when profiling or a specific identity boundary shows they help. / 这些 API 是性能工具，不是正确性工具。React.memo 可在 props 比较相等时跳过渲染；useMemo 缓存计算值；useCallback 缓存函数引用。只有性能分析或明确的引用边界表明它们有帮助时再使用。

~~~jsx
import { memo, useCallback, useMemo } from "react";

function ListContainer({ items, onSelect }) {
  const sortedItems = useMemo(
    () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
    [items]
  );

  const handleSelect = useCallback((id) => {
    onSelect(id);
  }, [onSelect]);

  return <ItemList items={sortedItems} onSelect={handleSelect} />;
}

const ItemList = memo(function ItemList({ items, onSelect }) {
  return items.map(item => (
    <button key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </button>
  ));
});
~~~

React.memo's default prop comparison uses Object.is per prop. A component can still render when its own state or consumed context changes; one newly created object or function prop can also prevent a skip. Inline handlers are ordinary JavaScript and are not automatically a performance bug. Keep state near its consumers, avoid unnecessary Effects that trigger render chains, and use the React Profiler to find a real hotspot.

React may discard a useMemo cache in documented circumstances. Do not depend on memoization for resource lifetime, semantic identity, or correctness.

## What does useRef do? / useRef有什么作用？

**Core answer / 核心回答：** useRef returns a stable object whose current field can hold a value between renders. Changing current does not request a render, so use refs for DOM access and bookkeeping, not for displayed state. / useRef 返回一个在多次渲染间保持稳定的对象，其 current 字段可保存可变值。修改 current 不会请求重新渲染，因此 ref 适合 DOM 访问和内部记录，不适合驱动可见界面的状态。

~~~jsx
function SearchBox() {
  const inputRef = useRef(null);

  return (
    <>
      <input ref={inputRef} />
      <button onClick={() => inputRef.current?.focus()}>
        Focus
      </button>
    </>
  );
}
~~~

Other suitable values include a timer ID or an external instance. Do not read or write refs during rendering except for initialization. Use state when a change must update the screen.

## What do forwardRef and useImperativeHandle do? / forwardRef和useImperativeHandle有什么作用？

**Core answer / 核心回答：** In React 18 and earlier, forwardRef lets a component accept and forward a parent's ref; useImperativeHandle can expose a narrow command API. In React 19, a function component can receive ref as a prop, so forwardRef is no longer necessary for new React 19-only components. / React 18 及更早版本中，forwardRef 让组件接收并转发父组件传入的 ref；useImperativeHandle 可暴露范围较小的命令式 API。React 19 的函数组件可以把 ref 作为 prop 接收，因此仅面向 React 19 的新组件不再需要 forwardRef。

~~~jsx
const FancyInput = forwardRef(function FancyInput(props, ref) {
  return <input {...props} ref={ref} className="fancy" />;
});
~~~

Prefer declarative props and callbacks when they express the interaction clearly. Use an imperative ref for cases such as focusing an input or coordinating a third-party widget.

## What is a custom Hook? / 什么是自定义Hook？

**Core answer / 核心回答：** A custom Hook is a function whose name starts with use and that calls other Hooks at the top level. It packages reusable stateful logic; it does not share one state instance across callers by itself. / 自定义 Hook 是名称以 use 开头、并在顶层调用其他 Hook 的函数。它封装可复用的有状态逻辑；仅仅复用 Hook 本身不会让多个调用共享同一份 state。

~~~jsx
function useWindowSize() {
  const [size, setSize] = useState({
    width: 0,
    height: 0
  });

  useEffect(() => {
    function update() {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    }

    window.addEventListener("resize", update);
    update();
    return () => window.removeEventListener("resize", update);
  }, []);

  return size;
}
~~~

Ordinary Hooks must be called in the same order on every render, at the top level of a component or another Hook. React 19’s use API is an exception: it may appear in a condition or loop, but it still belongs inside a component or Hook and cannot be wrapped in try/catch. The lint plugin checks these Rules of Hooks. An Effect's cleanup releases the listener; root StrictMode deliberately repeats setup and cleanup once in development.

## What are render props and higher-order components? / 什么是 render props 和高阶组件？

**Core answer / 核心回答：** Render props pass a function that chooses what to render from data supplied by a component. A higher-order component takes a component and returns a wrapped component. Both remain useful API shapes in some libraries and legacy code; custom Hooks are another way to share logic, not a universal replacement. / render props 通过函数接收组件提供的数据并决定渲染内容。高阶组件接收一个组件并返回包装后的组件。它们仍适用于某些库 API 和旧代码；自定义 Hook 是共享逻辑的另一种方式，并非对二者的通用替代。

~~~jsx
<MouseTracker render={({ x, y }) => (
  <p>Pointer: {x}, {y}</p>
)} />
~~~

A wrapper component can add authorization or instrumentation, but nested wrappers may make the component tree and prop flow harder to follow. Choose the API that makes ownership and behavior clear.

## What are common conditional-rendering patterns? / 常见的条件渲染写法有哪些？

**Core answer / 核心回答：** Use a ternary for either-or, logical AND for render-or-nothing, and an early return for a clear guard. Choose the form that makes the branches easiest to read. / 二选一可用三元表达式；只在条件成立时渲染可用逻辑 AND；明确的前置检查可用 early return。选择最容易读懂分支的写法。

~~~jsx
{isLoggedIn ? <Dashboard /> : <Login />}
{showBanner && <Banner />}

function Profile({ user }) {
  if (!user) return <Loading />;
  return <Content user={user} />;
}
~~~

Because React renders numbers, a numeric left operand can leak into the output: an empty list's length is 0, so {items.length && <List />} displays 0. Use {items.length > 0 && <List />} when that is not intended.

**See also:** [React Basics / React基础](./react-basics.md) for state snapshots and lifecycle context; [Rendering and Computation Optimization / 渲染与计算优化](../performance/rendering-and-computation-optimization.md) for profiling and memoization limits.

**Sources checked 2026-10-15:** [React: `useTransition`](https://react.dev/reference/react/useTransition), [`useDeferredValue`](https://react.dev/reference/react/useDeferredValue), [`Suspense`](https://react.dev/reference/react/Suspense), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries), [Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys), [Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), [Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation), [Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates), [Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation), [React: memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback), [useRef](https://react.dev/reference/react/useRef), [forwardRef](https://react.dev/reference/react/forwardRef), [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [Rules of Hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks), [use](https://react.dev/reference/react/use).
