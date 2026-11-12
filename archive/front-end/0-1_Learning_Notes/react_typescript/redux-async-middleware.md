# 旧式 Redux store 怎样手动接入 thunk 与 middleware？

新建应用应使用[Redux Toolkit 当前异步工作流](../../../../frontend/frameworks/redux-state-and-async-workflows.md)：`configureStore` 默认已配置 thunk。本页保留维护旧式裸 Redux store 时需要识别的两点：middleware 位于 `dispatch` 与 reducer 之间；thunk 让一次用户动作可以在 I/O 前后派发普通 action。

假设 `./reducers` 是现有根 reducer：它把 `report/loadStarted` 记为该 ID 的 `pending`，收到 `report/loadSucceeded` 后保存报表并记为 `succeeded`，收到 `report/loadFailed` 后记为 `failed` 并保存错误。下面先把 thunk 和记录普通 action 的 middleware 安装到旧 store：

~~~typescript
// 仅用于仍使用裸 Redux createStore 的旧项目
import {
  applyMiddleware,
  createStore,
  type Middleware,
  type UnknownAction,
} from "redux";
import { thunk, type ThunkDispatch } from "redux-thunk";
import rootReducer from "./reducers";

type Report = { id: string; title: string };
type RootState = {
  reports: {
    byId: Record<string, Report>;
    statusById: Record<string, "pending" | "succeeded" | "failed">;
    errorById: Record<string, string>;
  };
};
type AppDispatch = ThunkDispatch<RootState, unknown, UnknownAction>;

const actionLog: Middleware<{}, RootState> = store => next => action => {
  const before = store.getState();
  const result = next(action);
  const after = store.getState();
  console.log(action, { before, after });
  return result;
};

export const store = createStore(
  rootReducer,
  applyMiddleware(thunk, actionLog),
);
~~~

普通 action 到达核心 store 后同步执行 reducer。thunk middleware 会拦截函数 action，并调用收到的函数、传入 `dispatch` 与 `getState`。本例返回一个 `Promise<void>`：`loadStarted` 在开始网络请求前同步经过 reducer，结果按同一个 ID 写入 `reports`：

~~~typescript
function parseReport(value: unknown): Report {
  if (
    typeof value !== "object" ||
    value === null ||
    !("id" in value) ||
    typeof value.id !== "string" ||
    !("title" in value) ||
    typeof value.title !== "string"
  ) {
    throw new Error("报表响应格式无效");
  }
  return { id: value.id, title: value.title };
}

export const loadReport = (id: string) =>
  async (dispatch: AppDispatch): Promise<void> => {
    dispatch({ type: "report/loadStarted", payload: { id } });

    let report: Report;
    try {
      const response = await fetch("/api/reports/" + encodeURIComponent(id));
      if (!response.ok) throw new Error("HTTP " + response.status);
      const payload: unknown = await response.json();
      report = parseReport(payload);
      if (report.id !== id) throw new Error("报表响应 ID 不匹配");
    } catch (cause) {
      dispatch({
        type: "report/loadFailed",
        payload: {
          id,
          message: cause instanceof Error ? cause.message : String(cause),
        },
      });
      return;
    }

    dispatch({ type: "report/loadSucceeded", payload: report });
  };
~~~

调用方在 `async` 处理函数中写 `const task = store.dispatch(loadReport("r-42"))`。此时 `r-42` 已同步记为 `pending`；`await task` 等待网络与解析结束，之后 reducer 会把它记为 `succeeded` 并保存报表，或记为 `failed` 并保存错误。响应形状合法后，还必须确认 `report.id` 就是所请求的 `r-42`，否则不能把另一份报表当成本次成功结果。这里 `loadFailed` 表示请求、HTTP 状态、JSON 解码、响应形状或 ID 校验失败；成功派发放在 `try` 外，因而 reducer 或后续 middleware 若抛异常，会沿原调用链传播，不会被误记成网络失败。

`actionLog` 位于 thunk 后面，所以它看不到被 thunk 消费的函数本身；thunk 内重新调用 `dispatch` 派发的普通 action 会重新经过 middleware 链，日志可以记录这些 action 前后的状态。`next(action)` 把当前普通 action 交给链中的下一站，`store.dispatch` 则从链首开始；logger 返回 `next` 的结果。

如果把旧 store 迁到 Redux Toolkit，可在 `configureStore` 的 `middleware` 回调中返回 `getDefaultMiddleware().concat(actionLog)`。默认 thunk 在开发构建中与不可变性、可序列化等检查一起提供；生产构建默认只加入 thunk。一般异步请求无需自定义 async middleware；若逻辑要响应后续 action 或状态变化，再评估 listener middleware。

> [!warning] 一次 dispatch 启动 thunk，不会建立作业队列
> thunk 能在一次 dispatch 中等待异步工作，但这不保证全局 FIFO、跨请求互斥、重试、持久化或背压。确需排队时，应定义单独的队列和确认契约；本页只展示一个 `r-42` 请求。

> [!info]- 来源
> - 裸 Redux store 的 middleware 接入与 action 调用链：[Redux `applyMiddleware`](https://redux.js.org/api/applymiddleware)、[Writing Logic with Thunks](https://redux.js.org/usage/writing-logic-thunks)。
> - Redux Thunk 3.1.0 使用命名导出 `thunk`；middleware 将 `dispatch` 和 `getState` 传给 thunk，并把 thunk 的返回值交回调用方：[Redux Thunk README — Manual Setup](https://github.com/reduxjs/redux-thunk#manual-setup)、[3.1.0 release](https://github.com/reduxjs/redux-thunk/releases/tag/v3.1.0)。
> - Redux Toolkit 2.14.0 的默认中间件及开发、生产构建差异：[getDefaultMiddleware](https://redux-toolkit.js.org/api/getDefaultMiddleware#included-default-middleware)、[configureStore](https://redux-toolkit.js.org/api/configureStore)。
> - 当前示例版本以官方 npm registry 在 2026-11-13 查询为准：Redux 5.0.1、Redux Thunk 3.1.0、Redux Toolkit 2.14.0；旧项目若看到 Redux Thunk default import，应先核对锁文件版本。
