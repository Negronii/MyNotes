# How did ahooks v2.6 size variable-height virtual rows? / ahooks v2.6 如何设置变高虚拟列表项的尺寸？

In ahooks v2.6.0, useVirtualList accepts itemHeight as either a fixed pixel value or a function of the source index. For variable-height rows, the returned height must match the rendered row; this version has no separate estimateSize option. / ahooks v2.6.0 的 useVirtualList 支持用固定像素值或按源索引计算的函数设置 itemHeight。变高列表项的返回尺寸必须与实际渲染高度一致；此版本没有单独的 estimateSize 选项。

This preserves the v2.6.0 contract from the archived reference. Its object result (list, containerProps, wrapperProps, scrollTo) changed in v3; use the versioned examples in the [maintained ahooks note](../../../frontend/libraries/ahooks.md) for the current tuple/ref shape. Virtualization reduces mounted rows, not source-data memory; see [rendering and computation optimization](../../../frontend/performance/rendering-and-computation-optimization.md).

**Version sources / 版本来源:** [ahooks v2.6.0 useVirtualList documentation](https://ahooks-v2.js.org/hooks/ui/use-virtual-list/) and [v2.6.0 implementation](https://raw.githubusercontent.com/alibaba/hooks/v2.6.0/packages/hooks/src/useVirtualList/index.ts), checked 2026-10-15.
