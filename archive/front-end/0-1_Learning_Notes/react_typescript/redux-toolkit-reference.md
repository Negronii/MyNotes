# Redux Toolkit 的 prepare 回调怎样构造 action payload？

共享状态、store、typed hooks 和异步请求的主线见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。本页只保留 createSlice 的 prepare 配置：它让生成的 action creator 接受调用参数，并集中整理成 reducer 收到的 payload；它不替 payload 做服务端授权或运行时输入校验。

~~~typescript
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

type Report = { id: string; title: string; period: string };

const reportSlice = createSlice({
  name: "reports",
  initialState: [] as Report[],
  reducers: {
    reportAdded: {
      reducer(state, action: PayloadAction<Report>) {
        state.push(action.payload);
      },
      prepare(id: string, title: string, period: string) {
        return {
          payload: { id, title: title.trim(), period },
        };
      },
    },
  },
});

export const { reportAdded } = reportSlice.actions;
export const reportReducer = reportSlice.reducer;

// 调用参数由 prepare 统一组装；reducer 只收到标准化 payload。
const action = reportAdded("r-42", "  月度汇总  ", "2026-10");
// action.payload.title === "月度汇总"
~~~

reducer 中看似 push 的写法由 Redux Toolkit/Immer 转成新的不可变 state；prepare 负责 action 创建时的输入整理，reducer 负责基于当前 state 计算下一状态。更常见、无额外参数转换时，直接用 createSlice 自动生成的 action creator 即可。此处 API 按 Redux Toolkit 2.14.0 官方文档核对。

> [!info]- 来源
> - createSlice reducer 对象配置中的 prepare 回调：[Redux Toolkit createSlice](https://redux-toolkit.js.org/api/createSlice#customizing-generated-action-creators)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - Immer draft 与不可变更新：[Redux Toolkit — Writing Reducers with Immer](https://redux-toolkit.js.org/usage/immer-reducers)，2.14.0 文档，核对日期：2026-11-06。
