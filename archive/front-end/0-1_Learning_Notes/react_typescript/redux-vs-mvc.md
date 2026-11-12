# Redux 和 MVC 分别描述什么？

MVC（Model-View-Controller，模型-视图-控制器）描述一组组织职责；Redux 描述共享 state（状态）的容器以及 action、reducer 驱动的单向更新流。它们不是同一层面的互斥方案：采用 MVC 的系统也可在某个 UI 边界使用 Redux；简单局部交互通常不需要额外 store。

以一个合成报表页为例。这里的 MVC 特指 ASP.NET Core 一类服务端 Web MVC：`ReportsController` 收到 `GET /reports?sort=recent`，协调 Model 中的报表数据与业务规则，准备 View 所需的数据并选择报表 View；View 用数据生成响应页面。Controller 负责处理请求并在 Model 与 View 间协调，Model 提供应用数据和业务规则，View 呈现结果。三者分工不等于把页面里的每个 UI 部件映射成一个 MVC 角色。

页面返回后，表格中的 April 行与批量工具栏都要读取已选报表 ID。初始 `state.reportSelection.selectedIds=[]`；用户点击 April 行时，行组件派发 `{ type: "reportSelection/reportToggled", payload: "april" }`。reducer 根据当前数组算出 `state.reportSelection.selectedIds=["april"]`，store 保存新状态并通知订阅者；行组件从 ID 算出复选框为选中，工具栏读到同一 ID 并更新批量操作状态。Redux 在这个例子里处理的是两处 UI 共享的客户端选择状态；它没有替代服务端 MVC 的职责。

| 报表页中的值 | 所有者 | 原因 |
| --- | --- | --- |
| `sort=recent` | URL 与路由 | 地址可恢复排序条件；浏览器历史切换也由路由处理。 |
| May、April 等报表行 | 服务器；TanStack Query 保存客户端缓存副本 | 它们是服务器数据，查询缓存负责请求与复用，不需要再复制进 Redux。 |
| `state.reportSelection.selectedIds` | Redux store | 表格行和批量工具栏要共享稳定的报表 ID。 |
| 单组件弹层是否打开 | 使用它的组件 | 只有局部展示读取时，本地 state 已足够。 |

这张表标出该报表页中各状态的归属；回到概念层，两种方案的关注点可以这样比较：

| 问题 | MVC | Redux |
| --- | --- | --- |
| 主要描述 | 模型、视图、控制器如何分工 | 共享状态怎样经 action 与 reducer 转换 |
| 典型边界 | 应用或界面的职责划分 | 一个需要多个功能共同读取或更新的状态容器 |
| 是否互斥 | 可与 Redux 并存 | 不是 MVC 的替代命名 |

更完整的状态归属与 Redux 更新流程见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。

> [!info]- 来源
> - MVC 的 Controller、Model 与 View 职责；本例将范围限定为服务端 Web MVC：[Microsoft — Overview of ASP.NET Core MVC](https://learn.microsoft.com/en-us/aspnet/core/mvc/overview?view=aspnetcore-10.0#mvc-pattern)、[MDN — MVC](https://developer.mozilla.org/en-US/docs/Glossary/MVC)，官方文档，核对日期：2026-11-13。
> - Redux store、action、reducer 的单向更新流与状态归属建议：[Redux Fundamentals — Application Data Flow](https://redux.js.org/tutorials/fundamentals/part-2-concepts-data-flow#redux-application-data-flow)、[Redux Style Guide — Evaluate Where Each Piece of State Should Live](https://redux.js.org/style-guide/#evaluate-where-each-piece-of-state-should-live)，Redux 官方文档，核对日期：2026-11-13。
