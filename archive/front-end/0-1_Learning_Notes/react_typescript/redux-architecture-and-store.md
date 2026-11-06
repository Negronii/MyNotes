# 经典 Redux 架构图怎样对应现代实现？

原课程图展示多个 React 组件订阅 store，交互产生 action，再经 middleware 到 reducer 更新 state。它可以帮助回忆单向数据流，但图中的“异步 middleware”不是所有 Redux 异步请求都必须自定义实现的结论。

![原课程中的 Redux 架构图](reduce_architecture.png)

新建或现代化 Redux 应用时，使用[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)：其中按当前 Redux Toolkit 版本说明 configureStore 默认中间件、createSlice、typed hooks 与请求生命周期。action 到达核心 store 后同步运行 reducer；thunk middleware 才让 dispatch 接受函数并在外部工作后继续派发结果。

旧课程按语言、主题、认证等 feature 拆 reducer 的想法仍可用，但文件名如何组织只是项目选择，不改变 action → reducer → 新 state → 订阅者 render 的更新方向。服务端报表行仍由服务端查询缓存拥有，完整案例见[React 服务端状态章节](../../../../frontend/frameworks/react-server-state-and-optimistic-updates.md)。

> [!info]- 来源
> - 图片保留自旧课程文件 reduce_architecture.png；图中异步中间件画法不作为当前接口保证。
> - 当前 Redux 推荐工具集与状态流：[Redux Toolkit — Why Redux Toolkit Is Redux Today](https://redux-toolkit.js.org/introduction/why-rtk-is-redux-today)，2.14.0 文档，核对日期：2026-11-06。
