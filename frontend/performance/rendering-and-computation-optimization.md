# Rendering and Computation Optimization / 渲染与计算优化

## How does virtual scrolling work? / 虚拟滚动如何工作？

**Core answer / 核心回答：** Virtual scrolling keeps a scrollable viewport but mounts only the visible rows and a small overscan buffer. The list's full data may still take memory or computation; virtualization mainly reduces the rendered DOM and related layout work. / 虚拟滚动保留可滚动视口，但只挂载可见行和少量缓冲行。完整列表的数据仍可能占用内存或计算时间；虚拟化主要减少渲染的 DOM 和相关布局工作。

A fixed-height implementation can estimate the visible range directly. The outer spacer represents the full list height so the scrollbar has the right extent; the mounted window is offset by the height of the skipped rows. Variable-height rows need measurement or estimates, and all virtualizers need correct container dimensions and scroll behavior.

~~~jsx
function VirtualWindow({ items, scrollTop, viewportHeight, rowHeight = 40 }) {
  const overscan = 3;
  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const end = Math.min(
    items.length,
    Math.ceil((scrollTop + viewportHeight) / rowHeight) + overscan
  );

  return (
    <div style={{ height: items.length * rowHeight, position: "relative" }}>
      <div style={{ position: "absolute", top: start * rowHeight, left: 0, right: 0 }}>
        {items.slice(start, end).map(item => (
          <div key={item.id} style={{ height: rowHeight }}>{item.label}</div>
        ))}
      </div>
    </div>
  );
}
~~~

Here scrollTop and viewportHeight are measured from the scroll container; production code must keep those measurements synchronized and account for focus, keyboard navigation, and screen-reader expectations.

| Use when | Cost to account for |
|---|---|
| Profiling shows DOM or layout cost from a large rendered list. | More complex focus, accessibility, measurement, and scroll restoration behavior. |
| A list is unbounded or grows with user activity. | Data transformation may still be O(n), even when mounted rows are limited. |

For React, packages include react-window and @tanstack/react-virtual. Choose an adapter and API version supported by the application.

## How do you tune React rendering? / 如何优化React渲染？

**Core answer / 核心回答：** First identify which interaction is expensive. Keep state close to the components that use it, avoid unnecessary update chains, and measure before adding memoization. A component render is not automatically a DOM mutation. / 先确认哪个交互成本高。将 state 放在实际使用它的组件附近，避免不必要的更新链，并在添加 memoization 前进行测量。组件 render 不等于一定修改 DOM。

- **Stable keys:** use a data identity when sibling items can change order or membership. Use an index only for fixed lists.
- **Memoization:** React.memo, useMemo, and useCallback can help at measured boundaries; state and context changes can still render a memoized component.
- **State placement:** local transient state can often stay near its consumers instead of making a large subtree observe every update.
- **Hidden versus removed:** CSS display:none keeps the component in the React tree. Its state and Effects remain active while hidden. Conditional removal unmounts it and runs cleanup; remounting creates a new instance.
- **Fragments:** avoid an extra DOM wrapper when one is not needed. A fragment does not guarantee a measurable performance improvement.
- **Profiler:** record the actual interaction with browser and React profiling tools before changing architecture.

~~~jsx
const MemoizedRow = memo(function Row({ item, onSelect }) {
  return (
    <button onClick={() => onSelect(item.id)}>
      {item.name}
    </button>
  );
});
~~~

A new callback or object prop can prevent a memoized child from skipping its render, but inline functions are not inherently wrong. Add useCallback or useMemo when the child is expensive and the identity boundary matters, not as a blanket rule.

## CSS sprites and rendering changes / CSS Sprite与渲染改动

A CSS sprite combines small images into one image. Give each icon a fixed-size element and use background-position to expose its rectangle, for example background-position: -32px -16px. This can reduce separate image requests when request overhead matters, but it couples assets to one file: updating one icon invalidates the combined image and coordinates are harder to maintain. HTTP/2 multiplexes multiple requests over one connection, so request count alone is not enough reason to build a sprite; compare cache behavior, bytes, and maintenance cost for the actual asset set.

~~~css
.icon-edit {
  width: 16px;
  height: 16px;
  background-image: url("/icons.png");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
~~~

## Which CSS changes are worth testing? / 哪些CSS改动值得测试？

Layout, paint, compositing, and JavaScript can all affect a frame. Animate transform or opacity when that fits the design, but confirm the result in a trace; these properties do not make every animation free. Avoid forcing synchronous layout by reading layout and then writing layout repeatedly in the same task.

will-change is a hint, not a command to allocate a compositor layer. Use it narrowly and only when a measured animation benefits; unnecessary use can consume memory and make performance worse. Reducing DOM work and measuring real interactions are more reliable than assuming a shorter selector or shorthand property will speed up a page.

**See also:** [Browser HTML and CSS / 浏览器中的HTML与CSS](../html-css/browser-html-and-css.md) for rendering stages; [Performance Metrics and Analysis / 性能指标与分析](./performance-metrics-and-analysis.md) for measurement.

**Sources checked 2026-10-15:** [React: memo](https://react.dev/reference/react/memo), [React: useMemo](https://react.dev/reference/react/useMemo), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TanStack Virtual](https://tanstack.com/virtual/latest/docs/introduction), [CSS Will Change Module](https://www.w3.org/TR/css-will-change-1/), [MDN background-position](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-position), [HTTP/2 RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing).
