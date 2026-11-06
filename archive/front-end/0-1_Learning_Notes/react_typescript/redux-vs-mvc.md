# Redux 和 MVC 分别描述什么？

MVC（Model-View-Controller，模型-视图-控制器）描述一组组织职责；Redux 描述共享 state（状态）的容器以及 action、reducer 驱动的单向更新流。它们不是同一层面的互斥方案：采用 MVC 的系统也可在某个 UI 边界使用 Redux；简单局部交互通常不需要额外 store。

| 问题 | MVC | Redux |
| --- | --- | --- |
| 主要描述 | 模型、视图、控制器如何分工 | 共享状态怎样经 action 与 reducer 转换 |
| 典型边界 | 应用或界面的职责划分 | 一个需要多个功能共同读取/更新的状态容器 |
| 是否互斥 | 可与 Redux 并存 | 不是 MVC 的替代命名 |

Redux 是否适合当前报表页，要看它是否真的需要多处共享的客户端 state；sort 仍放在 URL，报表行由查询缓存保存。完整状态归属与现代 Redux Toolkit 例子见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。

> [!info]- 来源
> - MVC 是架构风格的职责划分：[MDN — MVC](https://developer.mozilla.org/en-US/docs/Glossary/MVC)，核对日期：2026-11-06。
> - Redux store、action 与 reducer 的单向更新流：[Redux Fundamentals](https://redux.js.org/tutorials/fundamentals/part-2-concepts-data-flow)，Redux 官方文档，核对日期：2026-11-06。
