# How should you reduce unnecessary React rendering work? / 如何减少不必要的 React 渲染工作？

First record the expensive interaction and identify which components render and why. Keep transient state near its consumers, use stable data keys for reorderable lists, and add memoization only at a measured boundary. A component render is not automatically a DOM mutation; props, state, context, and parent renders all affect whether work is skipped. / 先记录成本高的交互，确认哪些组件重渲染以及原因。让短暂状态靠近使用它的组件，可重排列表使用稳定数据键，并只在测量后对明确边界做 memoization。组件 render 不等于一定修改 DOM；props、state、context 与父组件 render 都会影响工作能否跳过。

## Start with state and identity

- Keep local interaction state near the components that use it when a large subtree should not observe every update.
- Use a stable item identity as the key when list membership or order can change. An array index is suitable only when the list is fixed and items never move.
- A context or state update can render a component even if it is wrapped with `memo`.
- A newly created object or callback prop can prevent a memoized child from skipping work, but inline values are not inherently a problem.

```jsx
const MemoizedRow = memo(function Row({ item, onSelect }) {
  return (
    <button onClick={() => onSelect(item.id)}>
      {item.name}
    </button>
  );
});
```

Use `useCallback` or `useMemo` when a measured identity boundary matters and the child or calculation is expensive. They add their own bookkeeping and should not be blanket wrappers.

## Measure with the React Profiler

Record the actual interaction in React DevTools Profiler and the browser Performance panel. Check whether time is spent rendering components, committing DOM changes, running JavaScript, or doing browser layout and paint. A React render that produces no changed DOM can still consume JavaScript time; a profiler helps separate those costs.

`React.memo`, `useMemo`, and `useCallback` can skip some work when dependencies and identities remain stable; they are not guarantees against state, context, or scheduled updates. Read the current contracts in the official [React memo](https://react.dev/reference/react/memo), [useMemo](https://react.dev/reference/react/useMemo), and [useCallback](https://react.dev/reference/react/useCallback) documentation.

## Hidden and removed components have different lifecycles

CSS hiding with `display: none` leaves the component mounted in the React tree. Its state and Effects remain active. Conditional removal unmounts the component and runs Effect cleanup; mounting it again creates a new instance and resets local state unless the state is held above it. Choose based on lifecycle and interaction requirements, not just appearance. See [CSS visibility and accessibility](../html-css/css-visibility-and-accessibility.md).

Fragments avoid an extra DOM wrapper when one is not needed, but they do not guarantee a measurable performance gain.

If profiling shows that a long list's mounted DOM is the dominant cost, see [virtual scrolling](./rendering-and-computation-optimization.md). For page-level measurement and performance diagnosis, see [Performance Metrics and Analysis](./performance-metrics-and-analysis.md).
