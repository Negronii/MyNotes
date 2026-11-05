# How should a page handle 100,000 data entries? / 页面如何处理十万条数据？

First clarify whether users need all records, a count, a search, or only the current viewport. Prefer server-side filtering, sorting, and pagination when the client cannot use all the data. A large dataset alone does not justify an extra middleware layer. / 先确认用户需要全部记录、计数、搜索结果还是仅当前视口。客户端用不到全部数据时，优先考虑服务端过滤、排序和分页；数据量大本身不足以证明需要额外中间层。

Receiving and transforming 100,000 small records may be feasible on some devices; creating a DOM node for every row can still be expensive in memory, style, layout, and accessibility navigation. Measure on target devices and select the smallest technique that meets the interaction:

- **Pagination or incremental loading:** transfer needed slices and expose loading, error, and continuation states. Cursor pagination can be more stable than offsets when records change, subject to API ordering requirements.
- **Virtualized list/grid:** keep visible rows and a small overscan window in the DOM while maintaining scroll geometry. Account for variable-height rows, keyboard navigation, focus, screen readers, and scroll restoration.
- **Chunked work or a Web Worker:** move expensive client-side transformation off the main thread when computation is the bottleneck; a worker does not make a huge DOM cheap.
- **Aggregation:** return a server-computed count or trend when users need a summary rather than every record.

Avoid a fixed item-count threshold. Row complexity, device memory, data shape, and interaction all matter. Profile network transfer, scripting, rendering, and memory separately. See [Performance Metrics and Analysis](../../../frontend/performance/performance-metrics-and-analysis.md) and [Rendering and Computation Optimization](../../../frontend/performance/rendering-and-computation-optimization.md).
