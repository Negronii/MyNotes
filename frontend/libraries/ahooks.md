# When should a React UI use an ahooks helper? / React界面何时适合使用 ahooks 工具？

**Core answer / 核心回答：** Use ahooks when an existing helper matches the interaction's state, lifecycle, request, or list contract and the installed package version. A helper still follows React's render and Effect rules; it does not replace decisions about data ownership, cache freshness, transport cancellation, or item identity. The APIs here follow documentation checked on 2026-10-15. / 当现有 ahooks 工具符合交互的状态、生命周期、请求或列表语义，并且与项目安装版本一致时再使用。工具仍遵守 React 的 render 和 Effect 规则；它不会替代对数据归属、缓存新鲜度、传输取消或列表项身份的判断。此处 API 依据 2026-10-15 核对的文档。

## Data fetching / 数据请求

### useRequest

useRequest wraps an asynchronous service and exposes request state and controls. It runs on mount by default; manual: true makes the caller start it with run or runAsync.

~~~jsx
function UserButton({ userId }) {
  const { data, loading, error, run } = useRequest(fetchUser, {
    manual: true,
    retryCount: 2,
    onSuccess(user) {
      console.log(user);
    }
  });

  return (
    <button type="button" disabled={loading} onClick={() => run(userId)}>
      {loading ? "Loading" : "Load user"}
    </button>
  );
}
~~~

Choose polling, debounce, or retry options for the specific request. The useRequest cancel method ignores data and errors from the current Promise; it does not stop that Promise. In debounce mode, cancel can stop a call that has not started. Pass an AbortSignal to the service when the network transport itself must stop.

### usePagination and useInfiniteScroll

usePagination expects a service that returns a total count and list, and exposes pagination state and change methods.

~~~javascript
const { data, loading, pagination } = usePagination(
  ({ current, pageSize }) => fetchUsers({ current, pageSize }),
  { defaultPageSize: 20 }
);

pagination.changeCurrent(2);
~~~

`useInfiniteScroll` passes the accumulated data to the service when loading more. For downward loading, return the next page's `list` and cursor so the Hook can append the page. Configure the scroll target and stopping rule for the UI. The [archive's list-loading example / 归档列表加载示例](../../archive/front-end/Deprecated_Interview_Notes/ahooks-list-loading-contracts.md) shows the complete service contract. [ahooks v3.10.0 source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useInfiniteScroll/index.tsx)

## State and browser storage / 状态与浏览器存储

~~~javascript
const [enabled, { toggle, setTrue, setFalse }] = useBoolean(false);
const [settings, setSettings] = useLocalStorageState("settings", {
  defaultValue: {}
});
~~~

Other state utilities include useToggle, useMap, and useSet. useLocalStorageState serializes browser storage and can optionally synchronize changes from other tabs. Storage is browser-local and can fail or be unavailable in server rendering, so treat it as persistence convenience rather than a source of trusted data.

useLatest returns a ref whose current value is refreshed to the latest input. It can help a long-lived callback read current data without rebuilding a timer or listener on every render.

~~~javascript
const latestCount = useLatest(count);

useEffect(() => {
  const timer = setInterval(() => {
    console.log(latestCount.current);
  }, 1000);
  return () => clearInterval(timer);
}, []);
~~~

## Function identity and list rendering / 函数引用与列表渲染

useMemoizedFn returns a stable function reference that calls the latest function body. It can simplify a callback identity boundary, but it does not remove the need to understand which state a callback should observe.

~~~javascript
function SaveButton({ currentRecordId }) {
  const saveLatest = useMemoizedFn(() => save(currentRecordId));
  return <button onClick={saveLatest}>Save</button>;
}
~~~

useCreation(factory, deps) is an ahooks helper for creating a value with dependency-based reuse. Treat it as a library convenience rather than a resource-lifecycle primitive or a correctness guarantee.

useVirtualList renders a visible window and a buffer from a larger array. In ahooks 3.10.0, it returns the tuple [list, scrollTo(index)]; each list entry is shaped as { data, index }. Pass containerTarget and wrapperTarget refs in the options.

~~~jsx
const containerRef = useRef(null);
const wrapperRef = useRef(null);
const [list, scrollTo] = useVirtualList(users, {
  containerTarget: containerRef,
  wrapperTarget: wrapperRef,
  itemHeight: 48,
  overscan: 5
});

return (
  <>
    <button type="button" onClick={() => scrollTo(40)}>Jump to row</button>
    <div ref={containerRef} style={{ height: 360, overflow: "auto" }}>
      <div ref={wrapperRef}>
        {list.map(({ data, index }) => (
          <div key={data.id} style={{ height: 48 }}>{data.name}</div>
        ))}
      </div>
    </div>
  </>
);
~~~

ahooks v2.6.0 uses a different useVirtualList result shape with containerProps and wrapperProps; v3 redesigned this API. Do not mix the versions. The v2.6.0 package returns these props for the scroll container and wrapper:

~~~jsx
// ahooks 2.6.0 result shape; use only with the matching installed version.
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(users, {
  itemHeight: 48,
  overscan: 5
});

return (
  <div
    {...containerProps}
    style={{ ...containerProps.style, height: 360 }}
  >
    <div {...wrapperProps}>
      {list.map(({ data, index }) => (
        <div key={data.id} style={{ height: 48 }}>{data.name}</div>
      ))}
    </div>
  </div>
);
~~~

Variable-height rows need the measurement behavior supported by the installed version. See [Rendering and Computation Optimization / 渲染与计算优化](../performance/rendering-and-computation-optimization.md).

useDynamicList exposes list and operations such as push, remove, move, insert, and getKey(index). Use getKey(index) as the React key so item identity survives edits; callbacks receive the current index.

~~~jsx
const { list, push, remove, insert, getKey } = useDynamicList([
  { name: "Ada" }
]);

return (
  <>
    {list.map((item, index) => (
      <div key={getKey(index)}>
        {item.name}
        <button type="button" onClick={() => remove(index)}>Remove</button>
      </div>
    ))}
    <button type="button" onClick={() => insert(0, { name: "Grace" })}>
      Add first
    </button>
    <button type="button" onClick={() => push({ name: "Lin" })}>Add</button>
  </>
);
~~~

## Effects and timing / Effect与时机

useMount and useUnmount package common Effect setup and cleanup. Their behavior follows React's Effect lifecycle, including the extra development setup-and-cleanup cycle under root StrictMode. They do not mean “run once for the lifetime of this process.”

useDebounce and useThrottle return delayed or rate-limited values; useDebounceFn and useThrottleFn wrap functions. Check whether the chosen hook returns a value, run function, or cancellation control before relying on an example from another version.

**Reach for ahooks / 何时使用：** It can reduce repeated hook boilerplate when its API matches the product behavior. Keep custom logic when cancellation, caching, errors, or data ownership need explicit control. For server-state caching and synchronization, compare a dedicated data library such as TanStack Query or SWR instead of assuming one hook collection covers every use case.

**See also / 另见** — [React component composition / React 组件组合](../frameworks/react-component-composition.md) for Hook rules and Effect cleanup, [React server state / React 服务端状态](../frameworks/react-server-state-and-optimistic-updates.md) for query and mutation rules, and [Performance Metrics and Analysis / 性能指标与分析](../performance/performance-metrics-and-analysis.md) for debounce and throttle tradeoffs.

**Sources checked 2026-10-15:** [ahooks useRequest](https://ahooks.js.org/hooks/use-request), [ahooks v3.10.0 useRequest implementation](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/Fetch.ts), [ahooks v2 to v3 upgrade notes](https://ahooks.js.org/guide/upgrade/), [ahooks 2.6.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v2.6.0/packages/hooks/src/useVirtualList/index.ts), [ahooks 3.10.0 useVirtualList source](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useVirtualList/index.ts), [usePagination](https://ahooks.js.org/hooks/use-pagination), [useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll), [useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state), [useLatest](https://ahooks.js.org/hooks/use-latest), [useMemoizedFn](https://ahooks.js.org/hooks/use-memoized-fn), [useVirtualList](https://ahooks.js.org/hooks/use-virtual-list), [useCreation](https://ahooks.js.org/hooks/use-creation), [useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn), [useThrottle](https://ahooks.js.org/hooks/use-throttle), [useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn), [useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list), [useUnmount](https://ahooks.js.org/hooks/use-unmount), [React StrictMode](https://react.dev/reference/react/StrictMode).
