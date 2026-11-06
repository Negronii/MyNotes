# 长报表列表何时适合虚拟滚动？

**案例背景。** 报表页从 `/reports?sort=recent#summary` 加载 May、April 两行；选择 **Oldest first** 后，`sort=oldest` 让可见顺序变成 April、May。这个小列表不需要 virtual scrolling（虚拟滚动）。当数据增长时，新的问题是：报表历史增长到十万条时，用户要看什么、客户端要拿多少数据、DOM 需要同时挂载多少行？网络量、计算量和已渲染节点是不同成本，先识别主因再选机制。

100,000 条本身不是虚拟化阈值：接收和转换这些记录在部分设备上可能可行，逐行为整个列表创建 DOM 仍可能让内存、样式与布局成本变高。行复杂度、设备、数据形状和交互共同决定该选什么，要分别测量请求、脚本、渲染和内存。

~~~mermaid
flowchart TD
    A[先确认用户要完成的任务] --> B{需要什么结果？}
    B -- 只要计数或汇总 --> C[服务端聚合]
    B -- 搜索排序一批记录 --> D[服务端过滤排序并分页]
    B -- 连续浏览且DOM是瓶颈 --> E[虚拟化当前浏览窗口]
    B -- 客户端转换计算太久 --> F[优化算法或分块/Web Worker]
    D --> G[测量传输、脚本和DOM成本]
    E --> G
    F --> G
~~~

## 十万条报表先决定哪些数据需要传输

假设报表库有 100,000 条记录。用户若只看计数或按月趋势，服务端可返回聚合值；若需搜索和按日期排序，接口可按过滤条件、稳定排序和页码/游标返回一页数据。游标要与排序规则一致；用相同时间戳加稳定 ID 作次级排序，避免新增记录时分页边界任意漂移。

分页或增量加载减少一次传输的数据量，但用户要等待后续页、看到加载/错误/结束状态。只在浏览器已经持有完整数据时做本地虚拟化，并不会减少网络传输或 JS 对象内存。若本地筛选计算才是主线程瓶颈，虚拟化也不会让全量筛选变便宜；应减少服务端返回量、改算法，或在适合时分块/放到 Web Worker（网页工作线程）。用户只需汇总时，传回汇总通常更直接。

| 主要瓶颈 | 对应处理方向 | 需要接受的代价 |
|---|---|---|
| 网络传了用户暂时用不到的记录 | 服务端过滤、排序、分页或增量请求 | 处理页状态、排序一致性和重复/遗漏边界 |
| 本地对全部记录做昂贵转换 | 服务端预计算、改算法、分块或 Web Worker（网页工作线程） | 分块会延迟完整结果；Worker 有序列化和通信成本 |
| 大量挂载节点拖慢渲染/布局 | 性能测量确认后虚拟化可见窗口 | 测量、滚动位置、焦点和辅助技术都更复杂 |
| 用户只想看总数/趋势 | 服务端聚合 | 不能交互浏览未返回的明细 |

## 固定行高怎样算出挂载窗口

先用固定高度推演。假设每行 40px，窗口高 480px，上下各多渲染 4 行（overscan，预渲染缓冲区）。用户滚到 `scrollTop = 4000px`：屏幕可见第 100 到第 111 行（从 0 编号）；上下加 overscan 后挂载 `[96, 116)` 共 20 行，而不是 100,000 行。滚动容器仍需呈现全列表约 4,000,000px 的总高度，窗口只偏移到第 96 行的位置。

~~~js
function getWindow(totalRows, scrollTop, viewportHeight, rowHeight, overscan = 4) {
  const firstVisible = Math.floor(scrollTop / rowHeight);
  const start = Math.max(0, firstVisible - overscan);
  const end = Math.min(
    totalRows,
    Math.ceil((scrollTop + viewportHeight) / rowHeight) + overscan
  );
  return {
    start,
    end,
    offsetY: start * rowHeight,
    totalHeight: totalRows * rowHeight
  };
}

const range = getWindow(100_000, 4_000, 480, 40);
// { start: 96, end: 116, offsetY: 3840, totalHeight: 4000000 }
// 已载入的报表数据只取窗口内的子数组：items.slice(range.start, range.end)
~~~

渲染时只把窗口内的报表行放在 `offsetY` 对应的位置，以 `totalHeight` 保留滚动范围；滚动容器的 `scrollTop` 和视口高度须从真实容器测量，并在滚动或尺寸变化时更新。行 key 要使用报表 ID，不能随窗口索引改变。窗口外的行一旦卸载，key 不会替它保存组件本地状态；需要保留的行状态应放在外部并按 ID 关联。若离页后还要回到原处，保存可见行 ID 与行内相对偏移，返回时再定位。

固定高度公式不适用于可换行标题、展开摘要或异步载入内容的行。此时先估计高度，再测量已挂载行的真实高度，并更新后续行的位置；若视口上方行变高/变矮，要修正滚动偏移以保住当前阅读锚点。已维护的虚拟器通常提供尺寸测量和锚点策略，但其 API 应按项目安装版本核对。

## 让被卸载的行仍能被键盘和辅助技术使用

虚拟化会卸载窗口外的节点。若焦点正落在一行按钮上，而该行随后被回收，焦点不能静默丢失；交互式列表要跟踪活动报表 ID，设计上下移动、跳转和焦点恢复，并确保当前活动项仍在 DOM 中。普通数据表若要支持浏览、打印和辅助技术，分页的原生 `<table>` 往往更易理解。只有确实采用列表框或网格等复合控件模式时，才实现该模式要求的键盘交互和焦点模型。

当 DOM 只包含集合的一部分时，WAI-ARIA 对支持的 listitem/treeitem 角色提供 `aria-posinset` 与 `aria-setsize`；表格、grid 或 treegrid 则有 `aria-rowindex` 与 `aria-rowcount`。这些数值必须对应真实位置和总数，不能用 ARIA 属性弥补错误角色或不完整键盘行为。用目标浏览器和屏幕阅读器验证滚动、读序、焦点、加载与空结果。

先以真实报表交互在[性能指标与诊断](./performance-metrics-and-analysis.md)里区分请求、脚本、DOM、布局和内存成本。React 组件本身的 render 成本见[React渲染优化](./react-rendering-optimization.md)。

> [!info]- 来源与版本核验（2026-11-06）
> - 虚拟列表的实际测量、可变行高与滚动锚点：[TanStack Virtual — Virtualizer API](https://tanstack.com/virtual/latest/docs/api/virtualizer)，官方当前文档，核验日期 2026-11-06。
> - 只呈现部分集合时的位置与总量属性、以及表格/网格行位置：[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)，W3C Recommendation，2023-06-06。
> - 动态加载 listbox 项的键盘模式和 `aria-posinset`/`aria-setsize`：[WAI-ARIA APG — Listbox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/)，W3C WAI 官方模式，核验日期 2026-11-06。
