# How can a React search interface stay responsive as results update? / React搜索界面如何在更新结果时保持响应？

**Core answer / 核心回答：** Keep the controlled input urgent, and let React defer the expensive result view or mark a navigation-like update as a Transition. A Suspense boundary can limit loading feedback to the result region. Include all result-changing inputs in the query key; use a separate debounce only when reducing request frequency is a product requirement. The state snapshot and commit path are explained in [React Basics / React基础](./react-basics.md). / 保持受控输入紧急更新，让 React 延后昂贵的结果视图，或把类似导航的更新标记为 Transition。Suspense 边界可以把加载反馈限制在结果区域。查询键要包含所有影响结果的输入；只有产品需要减少请求频率时才另做 debounce。state 快照与提交路径见[React Basics / React基础](./react-basics.md)。

This is the main interaction route: typing requests an urgent input update, while a deferred query value drives a Suspense-enabled result view. `useDeferredValue` schedules rendering; it is not a debounce and does not suppress requests. The [server-state deep question](./react-server-state-and-optimistic-updates.md) owns query identity, cache freshness, mutation, and rollback semantics.

## How do concurrent UI updates and Suspense work? / 并发界面更新与 Suspense 如何工作？

**Core answer / 核心回答：** Keep input state urgent so each keystroke appears immediately; defer expensive result rendering or mark a navigation-like state update as a Transition. React can interrupt and retry that render work so urgent updates get priority. A Suspense boundary gives one part of the screen a fallback while a Suspense-enabled child is not ready. / 输入状态应保持紧急，以便每次按键都立即显示；可以延后昂贵结果区域的渲染，或把类似导航的状态更新标记为 Transition。React 可以中断并重试这部分渲染，让紧急更新优先。Suspense 边界则在支持 Suspense 的子树尚未就绪时，为该区域显示 fallback。

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


## How do I compose components and reusable behavior around an interaction? / 如何围绕交互组合组件与可复用行为？

**Core answer / 核心回答：** Use props and callbacks for direct data flow, Context or a store for shared values, custom Hooks for reusable stateful logic, and refs for narrow imperative actions. Use memoization only when profiling or an identity boundary shows a benefit; keep legacy render-prop and wrapper APIs when they make the contract clearer. / 直接数据流使用 props 与回调，共享值使用 Context 或 store，可复用有状态逻辑使用自定义 Hook，窄范围命令式操作使用 ref。只有性能分析或明确的引用边界证明有收益时才加 memo；当旧的 render-prop 或包装器 API 能更清楚表达契约时，可以继续使用。

### How can components communicate? / React组件如何通信？

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

### When should you use memo, useMemo, or useCallback? / 何时使用 memo、useMemo和useCallback？

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

### What does useRef do? / useRef有什么作用？

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

### What do forwardRef and useImperativeHandle do? / forwardRef和useImperativeHandle有什么作用？

**Core answer / 核心回答：** In React 18 and earlier, forwardRef lets a component accept and forward a parent's ref; useImperativeHandle can expose a narrow command API. In React 19, a function component can receive ref as a prop, so forwardRef is no longer necessary for new React 19-only components. / React 18 及更早版本中，forwardRef 让组件接收并转发父组件传入的 ref；useImperativeHandle 可暴露范围较小的命令式 API。React 19 的函数组件可以把 ref 作为 prop 接收，因此仅面向 React 19 的新组件不再需要 forwardRef。

~~~jsx
const FancyInput = forwardRef(function FancyInput(props, ref) {
  return <input {...props} ref={ref} className="fancy" />;
});
~~~

Prefer declarative props and callbacks when they express the interaction clearly. Use an imperative ref for cases such as focusing an input or coordinating a third-party widget.

### What is a custom Hook? / 什么是自定义Hook？

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

### What are render props and higher-order components? / 什么是 render props 和高阶组件？

**Core answer / 核心回答：** Render props pass a function that chooses what to render from data supplied by a component. A higher-order component takes a component and returns a wrapped component. Both remain useful API shapes in some libraries and legacy code; custom Hooks are another way to share logic, not a universal replacement. / render props 通过函数接收组件提供的数据并决定渲染内容。高阶组件接收一个组件并返回包装后的组件。它们仍适用于某些库 API 和旧代码；自定义 Hook 是共享逻辑的另一种方式，并非对二者的通用替代。

~~~jsx
<MouseTracker render={({ x, y }) => (
  <p>Pointer: {x}, {y}</p>
)} />
~~~

A wrapper component can add authorization or instrumentation, but nested wrappers may make the component tree and prop flow harder to follow. Choose the API that makes ownership and behavior clear.

### What are common conditional-rendering patterns? / 常见的条件渲染写法有哪些？

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

**See also:** [React Basics / React基础](./react-basics.md) for state snapshots and lifecycle context; [React Server State and Optimistic Updates / React服务端状态与乐观更新](./react-server-state-and-optimistic-updates.md) for query/cache and mutation rules; [React Error Boundaries / React错误边界](./react-error-boundaries.md) for render-failure recovery; [Rendering and Computation Optimization / 渲染与计算优化](../performance/rendering-and-computation-optimization.md) for profiling and memoization limits.

**Sources checked 2026-10-15:** [React: `useTransition`](https://react.dev/reference/react/useTransition), [`useDeferredValue`](https://react.dev/reference/react/useDeferredValue), [React `Suspense`](https://react.dev/reference/react/Suspense), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [React: memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), [useCallback](https://react.dev/reference/react/useCallback), [useRef](https://react.dev/reference/react/useRef), [forwardRef](https://react.dev/reference/react/forwardRef), [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [Rules of Hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks), [use](https://react.dev/reference/react/use).
