# 旧式 Redux store 怎样手动接入 thunk 与 middleware？

新建应用应使用[Redux Toolkit 当前异步工作流](../../../../frontend/frameworks/redux-state-and-async-workflows.md)：configureStore 默认已配置 thunk。本页保留维护旧式裸 Redux store 时需要识别的两点：middleware 位于 dispatch 与 reducer 之间；thunk 让一次用户动作可以在 I/O 前后派发普通 action。

~~~typescript
// 仅用于仍使用裸 Redux createStore 的旧项目
import { applyMiddleware, createStore, type UnknownAction, type Middleware } from "redux";
import { thunk } from "redux-thunk";
import rootReducer from "./reducers";

export const store = createStore(rootReducer, applyMiddleware(thunk));
~~~

普通 action 到达核心 store 后同步执行 reducer。thunk middleware 会拦截函数 action，并把 dispatch 与 getState 传给它；请求结束后再派发可序列化的结果 action：

~~~typescript
type Report = { id: string; title: string };
type RootState = { reports: Record<string, Report> };

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
  async (dispatch: import("redux-thunk").ThunkDispatch<RootState, unknown, UnknownAction>) => {
    dispatch({ type: "report/loadStarted", payload: { id } });

    try {
      const response = await fetch("/api/reports/" + encodeURIComponent(id));
      if (!response.ok) throw new Error("HTTP " + response.status);
      const payload: unknown = await response.json();
      const report = parseReport(payload);
      dispatch({ type: "report/loadSucceeded", payload: report });
    } catch (cause) {
      dispatch({
        type: "report/loadFailed",
        payload: cause instanceof Error ? cause.message : String(cause),
      });
    }
  };
~~~

手写 middleware 可在 action 向下传递前后观察 store，例如记录一次普通 action 前后的状态：

~~~typescript
const actionLog: Middleware = store => next => action => {
  const before = store.getState();
  const result = next(action);
  const after = store.getState();
  console.log(action, { before, after });
  return result;
};
~~~

要让它与 Redux Toolkit 共存，应通过 getDefaultMiddleware().concat(actionLog) 保留默认 thunk、不可变性检查与可序列化检查；不要因为需要日志而替换整组默认项。一般异步请求无需自定义 async middleware；若工作是响应后续 action 或状态转移，再评估 listener middleware。

> [!warning] 单一请求槽不等于作业队列
> Redux thunk 能在一次 dispatch 中等待异步工作，但这不保证全局 FIFO、跨请求互斥、重试、持久化或背压。确需排队时，应定义单独的队列和确认契约；本页示例没有建立队列。

> [!info]- 来源
> - Middleware 的调用链与 Redux Toolkit 默认配置：[Redux Toolkit configureStore](https://redux-toolkit.js.org/api/configureStore)、[Side Effects Approaches](https://redux-toolkit.js.org/usage/side-effects-approaches)，2.14.0 文档，核对日期：2026-11-06。
> - Redux Thunk 手动接入裸 store：[Redux Thunk README](https://github.com/reduxjs/redux-thunk#manual-setup)，redux-thunk 官方仓库，核对日期：2026-11-06。
