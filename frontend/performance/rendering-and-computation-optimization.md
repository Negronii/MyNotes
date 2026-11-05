# When does virtual scrolling help a long list? / 长列表何时适合使用虚拟滚动？

Virtual scrolling keeps the full scrollable extent but mounts only rows near the visible window. It can reduce DOM, layout, and rendering work when profiling shows a large rendered list is the bottleneck. It does not automatically reduce the memory or `O(n)` processing cost of the complete data set, and it adds work for measurement, focus, keyboard navigation, accessibility, and scroll restoration. / 虚拟滚动保留完整列表的滚动范围，但只挂载可视区域附近的行。当性能分析确认大量已渲染行是瓶颈时，它可以减少 DOM、布局和绘制工作。它不会自动减少完整数据集的内存或 `O(n)` 处理成本，并会增加测量、焦点、键盘导航、无障碍与滚动恢复的复杂度。

For a fixed row height, compute the first and last visible indices from `scrollTop` and viewport height. Add a small overscan region to reduce visible gaps during scrolling. A spacer represents the full list height, and the mounted window is offset by the height of skipped rows.

```jsx
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
```

`scrollTop` and `viewportHeight` must be measured from the actual scroll container and kept synchronized with scroll and resize events. This illustration assumes a fixed row height. Variable-height rows need measurements or estimates and a policy for correcting positions when estimates change.

| Consider virtualization when… | Account for… |
|---|---|
| A profile shows DOM/layout/render cost from a long mounted list | Focus movement, keyboard navigation, and screen-reader expectations |
| The list is unbounded or grows as users interact | Measurement and scroll correction for variable-height content |
| Only a small window needs to be visible at once | Data transformation may still traverse all items |

For production use, choose a maintained virtualizer compatible with the application version, such as [TanStack Virtual](https://tanstack.com/virtual/latest/docs/introduction). Start with measurement and a real user interaction; virtualization is not useful if the list is already cheap.

See [Performance Metrics and Analysis](./performance-metrics-and-analysis.md) for profiling guidance and [React rendering optimization](./react-rendering-optimization.md) when component work is the measured bottleneck.
