# 经典 Redux 架构图怎样对应现代实现？

![原课程中的 Redux 架构图](reduce_architecture.png)

这张课程图围绕一条被正常转发的 action（动作）画出单向数据流：用户交互派发 action；若配置了 middleware（中间件），它先经过这些包装层；经 `next(action)` 转发到核心 `dispatch` 后，根 reducer 同步计算新 state，store 保存结果，再通知订阅者。middleware 可以拦截、延迟或改写 action，所以不是每次 dispatch 都必然到达 reducer。

图中的多个 reducer 可以按功能域拆分。使用 reducer 映射时，根 reducer 把**同一个 action 和每个 slice 的旧 state**分别传给对应 reducer，再组合成下一份根 state；不是 middleware 挑一块 reducer 更新。某个 slice 不处理这条 action 时，通常返回自己的原 state。

图里的 `subscribe` 是 store 通知订阅者的概念，不代表每次派发都会让所有组件重新渲染。现代函数组件用 React-Redux 的 `useDispatch` 派发 action，用 `useSelector` 读取所需值并订阅 store。收到通知后，React-Redux 会先检查当前 Redux state 快照；若 `Object.is` 判断快照未变，就复用上次选取结果，不再运行 selector。快照改变时才计算新选取结果，再默认以严格 `===` 比较前后结果；只有选取结果变化，这个订阅才触发该组件重渲染。这是课程图中的 store 订阅与当前组件更新之间的连接；组件自身或父组件的渲染、开发期检查仍可能再次运行 selector。

图中的两块 middleware 和“异步”标注表示一种可扩展 dispatch 的做法，不表示每个 Redux 请求都要手写异步 middleware。thunk middleware 收到函数时会截获它，并用 `dispatch` 和 `getState` 调用这个函数；函数本身不交给 reducer。手写 thunk 可以同步或异步，自行决定派发哪些普通 action、何时派发。这些新 action 再进入 middleware 链；被转发到核心 dispatch 的 action 才由 reducer 同步计算下一状态。

Redux Toolkit 的 `configureStore` 接受 slice reducer 映射并组合根 reducer，默认加入 thunk；`createSlice` 用于组织功能域的 action 与 reducer。由 `createAsyncThunk` 创建的 thunk 在正常启动路径先派发 `pending`，再调用 payload creator 执行请求，之后按结果派发 `fulfilled` 或 `rejected`；应用可在 slice 的 `extraReducers` 中为这些 action 编写处理器，更新业务 state。普通手写 thunk 不会自动获得这套生命周期；若 `condition` 返回 `false`，默认也不派发生命周期 action（除非开启 `dispatchConditionRejection`）。完整的当前请求示例及过期响应、取消和错误分支见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。

例如，主篇报表页面的 `selectedIds` 初始为 `[]`。点选 April 行，组件派发 `{ type: "reportSelection/reportToggled", payload: "april" }`；reducer 得到 `["april"]`，行的 selector 随之选出 `true`，工具栏 selector 读到新的 ID 数组。即使另一个 action 通知了 store 订阅者，若当前 state 快照未变，React-Redux 可复用上次的选取结果；若快照变化但某组件选出的值相同，默认比较也不会因这次通知触发它重渲染。

Redux 是否应该持有一份数据，取决于谁需要一起读取和更新它。当前报表案例把跨组件的已选 ID 放进 Redux；路由继续持有 URL 排序，服务端报表行继续由 TanStack Query 缓存。旧课程按功能域组织 reducer 的目录方式仍可用，但文件夹布局不会改变被转发的 action 经根 reducer 更新 state、再通知订阅者的机制。

旧类组件可继续通过 React-Redux 的 `connect` 维护；React-Redux 9.3.0 起已将 `connect` 标为 deprecated，hooks 是新函数组件的默认建议。类型与旧用法边界见[旧类组件怎样通过 connect 读取 Redux？](react-redux-legacy-and-hooks-integration.md)。

> [!info]- 来源
> - 架构图保留自旧课程文件 `reduce_architecture.png`；图中术语是课程示意，不作为当前 API 合约。
> - **当前 store 与异步入口。** [Redux Toolkit `configureStore`](https://redux-toolkit.js.org/api/configureStore) 说明 reducer 映射会组合为根 reducer 并默认加入 thunk；[Redux Toolkit `createAsyncThunk` 生命周期](https://redux-toolkit.js.org/api/createAsyncThunk#return-value) 说明正常启动时先派发 `pending`，再运行 payload creator，按结果派发后续 action；[执行前取消](https://redux-toolkit.js.org/api/createAsyncThunk#canceling-before-execution) 说明 `condition` 返回 `false` 时默认不派发任何 action。对应当前包版本：Redux Toolkit 2.14.0，核对日期：2026-11-12。
> - **thunk 函数与 store 通知。** [Redux — Writing Logic with Thunks](https://redux.js.org/usage/writing-logic-thunks#how-does-the-middleware-work) 说明 thunk middleware 收到函数后会用 store 的 `dispatch`、`getState` 调用它，函数逻辑可以同步或异步；[Redux — Store](https://redux.js.org/api/store#subscribelistener) 说明 reducer 返回后通知 store listener。 [Redux `combineReducers`](https://redux.js.org/api/combinereducers) 说明各 slice reducer 接收各自的 state 与相同 action，并合成为根 state。
> - **组件订阅。** [React-Redux Hooks API — Equality Comparisons and Updates](https://react-redux.js.org/api/hooks#equality-comparisons-and-updates) 说明默认 `===` 选择结果比较；[React-Redux 9.3.1 `useSelector` 源码](https://github.com/reduxjs/react-redux/blob/v9.3.1/src/hooks/useSelector.ts)将 `store.getState` 和 selector 接到 `useSyncExternalStoreWithSelector`；[React 19.3.1 selector helper 源码](https://github.com/react/react/blob/v19.3.1/packages/use-sync-external-store/src/useSyncExternalStoreWithSelector.js)在 `Object.is` 判定 snapshot 相同后复用上次选择结果。
> - **旧 React-Redux 集成。** [React-Redux TypeScript 使用说明](https://react-redux.js.org/using-react-redux/usage-with-typescript)说明 hooks 为当前建议，并标注 `connect` 自 React-Redux 9.3.0 起 deprecated；[React-Redux 版本列表](https://www.npmjs.com/package/react-redux?activeTab=versions)将 9.3.1 标为 latest，核对日期：2026-11-12。
