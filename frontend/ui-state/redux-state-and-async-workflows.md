# Redux 怎样管理跨组件的客户端状态和异步请求？

当一份纯客户端状态要被页面上相距很远的几个组件同时读写，而且希望每次变化都可追踪时，可以把它放进 Redux 的 store (状态容器)。本章沿一次“勾选行 → 请求导出预览 → 显示结果”的操作，说明 Redux 的更新链、异步请求放在哪里、怎样不让迟到的响应覆盖较新的选择，以及组件怎样订阅才不会多余渲染。读者需要知道一份状态该归谁（见[界面状态的所有权](state-ownership-and-composition.md)），以及“异步结果按身份归属”的原理（见[服务端数据的缓存与乐观更新](server-state-and-optimistic-updates.md#异步结果按身份归属)）。

示例按 Redux Toolkit 2.14.0 与 React-Redux 9.3.1 核对（2026-11-12 时两者均为 npm latest）。

## 案例：勾选报表行，预览导出范围

沿用主线一的报表页 `/reports/42?sort=recent#summary`。排序归 URL，May、April 两行归服务器、由查询缓存保存副本（见[路由与 loader](routing-and-loaders.md) 和上一章）。本章新增的是一份纯客户端状态：用户勾选了哪些行，以及针对这组勾选的导出预览。两行的行 ID 沿用主线一：May 是 `r-104`，April 是 `r-103`。

勾选框在每一行里，批量操作栏在表格上方，预览结果显示在页面另一侧；三处都要读写同一份状态。预览接口 `POST /api/reports/42/export-preview` 只估算行数和字节数，不创建文件或作业。接口、ID 和返回值都是合成示例。

## 哪些状态进 Redux

先按所有权把这页的状态分开：

- **排序** 在 URL：分享、刷新和 Back 都恢复它。Back 不会改动 Redux 里的勾选。
- **报表行** 归服务器，查询缓存保存副本，键里含 `sort`。不要把同一批行再复制进 Redux：两个缓存所有者会各自过期、各自更新，迟早不一致。Redux 应用若要缓存服务器数据，官方方案是 RTK Query；本例已用 TanStack Query，就只用它。
- **已选行 ID** 进 Redux：行、工具栏都读同一组稳定 ID，排序或列表位置变了也仍指向同一行。
- **预览状态与结果** 进同一个 slice (状态切片)：工具栏和预览区共用，而且勾选一变，预览就要在同一次更新里作废。
- **弹层开关** 这类只影响一个组件的值，留在组件本地。

只有一个组件用的值留在组件里；两个相邻组件共享时，先考虑提升到最近的共同父组件。多个相距较远的部分共享、并且需要统一可追踪的更新时，再评估 Redux。若预览结果可以按选择集合缓存复用，查询缓存可能更合适；本例只保留“当前选择”的一份预览，所以用 slice 演示。

store 默认只在本次运行期间保存勾选；本例没有把勾选写进 URL，也没有持久化，刷新后就清空。

## action 怎样经过 store 变成新状态

勾选框派发的是一个事实：“某一行被勾选或取消勾选”。Redux 的 action (动作)就是描述这个事实的普通对象，`payload` (载荷)携带所需的值；reducer (归约函数)根据当前 state 和 action 同步算出下一份 state；store 保存结果并通知订阅者。

设开始时 `selectedIds=[]`。点 April 行派发：

~~~js
{ type: "rowSelection/rowToggled", payload: "r-103" }
~~~

reducer 算出 `selectedIds=["r-103"]`，并在同一次计算里把旧预览清空；store 通知订阅者，各组件的 selector (选择器)重新检查：April 行的 selector 得到 `true`，工具栏读到新的数组引用。行 ID 不随排序改变，所以不要用数组下标代替它。

Redux Toolkit 的 `createSlice` 把初始状态、reducers 和自动生成的 action creator 放在一起。reducer 里可以写 `push`、`splice` 这种看似原地修改的代码：Immer 把它们记录为对 draft (草稿副本)的修改，再产出新的不可变 state，并没有改动 store 已发布的对象。reducer 只计算状态，不能在里面发请求、启动计时器或取消请求。

## 异步工作插在 dispatch 的路径上

reducer 不能发请求，异步工作就要放在 `dispatch` 之前。普通 action 先经过已配置的 middleware (中间件)，再交给核心 `dispatch`，然后根 reducer 同步计算新状态。中间件包裹 `dispatch`，可以观察 action、扩展 `dispatch` 能接受的输入，或在 action 到达 reducer 前后执行副作用。

thunk middleware 让 `dispatch` 能接受一个函数。这个函数（thunk）在 reducer 之外运行，可以读 `getState`、派发普通 action、等待异步操作；store 本身仍然只根据普通 action 同步更新。`configureStore` 默认加入 thunk、开发期检查和 Redux DevTools 集成；添加自定义中间件时用 `getDefaultMiddleware().concat(...)` 保留默认项。

DevTools 能看到所有派发过的 action 和 state，所以不要把凭证放进去，也不要把 `AbortController`、Promise 这类运行时对象存进 Redux state。

`createAsyncThunk` 为常见的请求生命周期生成 action：正常启动时先派发 `pending`，再调用 payload creator (载荷函数)执行请求，完成后派发 `fulfilled` 或 `rejected`。slice 用 `extraReducers` 响应它们。这套生命周期是 `createAsyncThunk` 提供的，手写的普通 thunk 不会自动派发。若工作需要响应**后续**的 action 或状态变化，再评估 listener middleware；普通按钮触发的请求不必手写异步中间件。

## 用 requestId 守住唯一的预览槽

预览请求携带发起那一刻的 ID 快照。用户先勾 May、点预览，第一份请求体是 `["r-104"]`；接着又勾 April，reducer 立即清空旧预览；再点预览，第二份请求体是 `["r-104","r-103"]`。两份响应的返回顺序不确定，第一份可能更晚到。reducer 不能只看“收到了成功”，还要确认这份结果仍属于当前请求。

这是“按身份归属”的单槽版本。身份是 `createAsyncThunk` 为每次调用在客户端生成的 `requestId`，随生命周期 action 的 `meta` 传给 reducer；它不进 HTTP 请求，也不需要服务器回传。

~~~mermaid
flowchart TD
    CLICK["工具栏派发预览 thunk"] --> PENDING["createAsyncThunk 先派发 pending"]
    PENDING --> SAVE["reducer 记录<br/>preview.currentRequestId = meta.requestId"]
    SAVE --> POST["payload creator 再发 POST<br/>body 只有 rowIds 快照"]
    POST --> DONE["fulfilled / rejected<br/>meta.requestId 随 action 回来"]
    DONE --> CHECK{"与 preview.currentRequestId<br/>相等？"}
    CHECK -->|是| APPLY["fulfilled → ready<br/>rejected → error 或 idle"]
    CHECK -->|否| IGNORE["忽略过期结果"]
~~~

`pending` 把新 ID 写进 `currentRequestId`；勾选变化把它清成 `null`；结果到达时只有 ID 相等才生效。所以过期请求即使没被取消、晚些才成功或失败，也覆盖不了当前预览。

> [!example] 两份预览按请求身份接收，不按返回先后接收
> `req-1`、`req-2` 是便于跟踪的标签，实际 ID 由 thunk 生成；`4096`、`1024` 字节是合成值。
>
> | 操作或返回 | `selectedIds` | 预览状态 |
> |---|---|---|
> | 初始 | `[]` | `idle`；`currentRequestId = null` |
> | 勾 May，启动 `req-1` | `["r-104"]` | `pending`；当前 ID `req-1`；请求体 `{"rowIds":["r-104"]}` |
> | 勾 April | `["r-104","r-103"]` | `idle`；旧预览与当前 ID 清为 `null` |
> | 启动 `req-2` | `["r-104","r-103"]` | `pending`；当前 ID `req-2`；请求体 `{"rowIds":["r-104","r-103"]}` |
> | `req-2` 先返回 `{rowCount: 2, estimatedBytes: 4096}` | `["r-104","r-103"]` | ID 匹配，转为 `ready`；当前 ID 清为 `null` |
> | `req-1` 后返回 `{rowCount: 1, estimatedBytes: 1024}` | `["r-104","r-103"]` | `req-1` ≠ `null`，忽略；预览仍是 `req-2` 的结果 |
>
> 按 Back 只恢复 `sort` 和对应的行查询；勾选不在 URL 里，`["r-104","r-103"]` 不随 Back 改变。

本例只有一个预览槽。若要同时保留多个并发预览或导出作业，就按请求 ID 或服务端作业 ID 分格存储，而不是共用一个槽。

服务器仍须按当前调用者和租户范围逐个授权这些行 ID，客户端勾选不能代替服务端资源权限检查，见[服务怎样逐次确认这个主体能对这份资源做这个动作？](../../engineering-foundations/services/per-request-authorization.md)。响应 JSON 先当作 `unknown`，在运行时校验 `rowCount`、`estimatedBytes` 是非负安全整数（见 [TypeScript 能保证什么](../javascript/typescript-guarantees-and-runtime-validation.md)）。

## 取消与错误

**取消。** requestId 判断结果归属，取消尽量停止客户端的工作，两者不是一回事。`dispatch(thunk)` 返回的 Promise 带一个 `.abort()` 方法，调用它会触发 payload creator 收到的 `signal`；本例把 `signal` 传给了 `fetch`。当前请求被取消时，reducer 把预览恢复成 `idle`、保留勾选；若它早已被新选择或新请求取代，取消产生的旧 `rejected` 同样因 ID 不匹配而被忽略。本例的工具栏没有保存这个 Promise，要接入取消就得保存它并在合适时机调用 `.abort()`。客户端中止读取不保证服务器已停止处理，见[取消与超时停得住什么](../javascript/cancellation-timeouts-and-concurrency.md)。

**错误。** HTTP 错误状态、无效 JSON 和结构不符的响应都变成 `rejected`。payload creator 把它们统一转成固定文案“无法计算导出预览，请稍后重试”，不把解析器的原始 `SyntaxError` 或响应片段放进 action、state、界面或 DevTools；只有 `signal.aborted` 时原样抛出，让取消仍可识别（`meta.aborted`）。若服务器定义了结构化错误载荷，先按运行时 schema 校验，再用 `rejectWithValue` 只保存允许展示的字段。

`dispatch(thunk)` 返回的 Promise 总以 `fulfilled` 或 `rejected` action 结束，不会自己抛错。调用方需要在失败时进入 `catch`，就调用 `.unwrap()`。本例的预览区直接由 Redux state 驱动，工具栏不必等待这个 Promise。

**没有乐观更新，也不需要补偿。** 勾选 action 记录的是已经发生的本地操作，预览出错不会把 ID 回滚。预览接口没有远端写入，所以可以用同一组勾选直接重试。若按钮改成“创建导出作业”，情况就变了：网络超时不能证明服务器没有创建作业，那是有外部效果的命令，需要接口提供幂等键、作业 ID 或核对流程（见[写请求超时后，怎样查清结果并安全重试？](../../engineering-foundations/services/deadlines-retries-and-unknown-outcomes.md)），不能照搬只读预览的重试结论。

## 接进 React：类型化 Hook 与 selector 引用

把 reducer 映射传给 `configureStore`，它组合出根 reducer；根状态类型和 dispatch 类型再从 store 推导。React-Redux 自 9.1.0 起提供 `.withTypes()`，让带类型的 Hook 复用这两个类型。应用根节点用 `<Provider store={store}>` 提供 store。`hooks.ts` 只导入 store 的**类型**，不产生反向的运行时依赖：

~~~ts
// app/store.ts
import { configureStore } from "@reduxjs/toolkit";
import { rowSelectionReducer } from "../features/row-selection/rowSelectionSlice";

export const store = configureStore({ reducer: { rowSelection: rowSelectionReducer } });
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// app/hooks.ts
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "./store";

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
~~~

store 通知订阅者后，`useSelector` 先看根 state 快照：`Object.is` 判断快照没变，就复用上次的 selector 结果，不重新运行；快照变了才重新计算，并默认用 `===` 比较新旧结果，不相等才让组件重新渲染。行组件的 selector 返回布尔值 `selectedIds.includes(row.id)`：与这一行无关的 action 不会改变它，该行就不会因 store 通知而重新渲染。

不要在 selector 里每次临时拼一个对象，例如 `state => ({ selected: …, status: … })`。字段值即使没变，新对象的引用每次都不同，任何一次 Redux 更新都会被判为“结果变了”。要合并多个值，可以分别调用 Hook、用记忆化 selector，或确认浅比较合适后传入 `shallowEqual`。selector 应是纯函数。以上只描述 store 通知引发的检查：组件仍可能因父组件更新而渲染，selector 也可能在渲染时或开发期检查中运行。是否值得继续优化，用测量决定，见 [React 渲染优化](../delivery/react-rendering-optimization.md)。

## 完整实现

> [!example]- Slice、异步预览请求与组件接线
>
> ~~~ts
> // features/row-selection/rowSelectionSlice.ts
> import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
>
> type Preview = { rowCount: number; estimatedBytes: number };
> type PreviewState = {
>   status: "idle" | "pending" | "ready" | "error";
>   currentRequestId: string | null;
>   result: Preview | null;
>   error: string | null;
> };
> type RowSelectionState = { selectedIds: string[]; preview: PreviewState };
>
> const isRecord = (v: unknown): v is Record<string, unknown> =>
>   typeof v === "object" && v !== null && !Array.isArray(v);
> const isCount = (v: unknown): v is number =>
>   typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
>
> function parsePreview(value: unknown): Preview {
>   if (!isRecord(value) || !isCount(value.rowCount) || !isCount(value.estimatedBytes)) {
>     throw new Error("报表服务返回了无效的导出预览");
>   }
>   return { rowCount: value.rowCount, estimatedBytes: value.estimatedBytes };
> }
>
> const previewFailedMessage = "无法计算导出预览，请稍后重试";
>
> export const loadExportPreview = createAsyncThunk<
>   Preview,
>   { reportId: string; rowIds: string[] },
>   { rejectValue: string }
> >("rowSelection/loadExportPreview", async ({ reportId, rowIds }, { signal, rejectWithValue }) => {
>   try {
>     const response = await fetch(`/api/reports/${encodeURIComponent(reportId)}/export-preview`, {
>       method: "POST",
>       headers: { "Content-Type": "application/json" },
>       body: JSON.stringify({ rowIds }),
>       signal,
>     });
>     if (!response.ok) return rejectWithValue(previewFailedMessage);
>     const payload: unknown = await response.json();
>     return parsePreview(payload);
>   } catch (error) {
>     if (signal.aborted) throw error;          // 保留可识别的取消
>     return rejectWithValue(previewFailedMessage); // 其他错误统一成固定文案
>   }
> });
>
> const emptyPreview = (): PreviewState =>
>   ({ status: "idle", currentRequestId: null, result: null, error: null });
>
> const rowSelectionSlice = createSlice({
>   name: "rowSelection",
>   initialState: { selectedIds: [], preview: emptyPreview() } as RowSelectionState,
>   reducers: {
>     rowToggled(state, action: PayloadAction<string>) {
>       const index = state.selectedIds.indexOf(action.payload);
>       if (index === -1) state.selectedIds.push(action.payload);
>       else state.selectedIds.splice(index, 1);
>       state.preview = emptyPreview();       // 旧结果不再代表当前集合
>     },
>     selectionCleared(state) {
>       state.selectedIds = [];
>       state.preview = emptyPreview();
>     },
>   },
>   extraReducers: builder => {
>     builder
>       .addCase(loadExportPreview.pending, (state, action) => {
>         state.preview = {
>           status: "pending", currentRequestId: action.meta.requestId, result: null, error: null,
>         };
>       })
>       .addCase(loadExportPreview.fulfilled, (state, action) => {
>         if (state.preview.currentRequestId !== action.meta.requestId) return;
>         state.preview = { status: "ready", currentRequestId: null, result: action.payload, error: null };
>       })
>       .addCase(loadExportPreview.rejected, (state, action) => {
>         if (state.preview.currentRequestId !== action.meta.requestId) return;
>         const aborted = action.meta.aborted;
>         state.preview = {
>           status: aborted ? "idle" : "error",
>           currentRequestId: null,
>           result: null,
>           error: aborted ? null : action.payload ?? previewFailedMessage,
>         };
>       });
>   },
> });
>
> export const { rowToggled, selectionCleared } = rowSelectionSlice.actions;
> export const rowSelectionReducer = rowSelectionSlice.reducer;
> ~~~
>
> ~~~tsx
> // features/row-selection/components.tsx
> import { useAppDispatch, useAppSelector } from "../../app/hooks";
> import { loadExportPreview, rowToggled } from "./rowSelectionSlice";
>
> type Row = { id: string; period: string; title: string };
>
> export function ReportRow({ row }: { row: Row }) {
>   const selected = useAppSelector(s => s.rowSelection.selectedIds.includes(row.id));
>   const dispatch = useAppDispatch();
>   return (
>     <li>
>       <label>
>         <input type="checkbox" checked={selected} onChange={() => dispatch(rowToggled(row.id))} />
>         {row.period} — {row.title}
>       </label>
>     </li>
>   );
> }
>
> export function ExportPreviewToolbar({ reportId }: { reportId: string }) {
>   const selectedIds = useAppSelector(s => s.rowSelection.selectedIds);
>   const status = useAppSelector(s => s.rowSelection.preview.status);
>   const dispatch = useAppDispatch();
>   return (
>     <button
>       type="button"
>       disabled={selectedIds.length === 0 || status === "pending"}
>       onClick={() => void dispatch(loadExportPreview({ reportId, rowIds: [...selectedIds] }))}
>     >
>       预览导出范围
>     </button>
>   );
> }
>
> export function ExportPreviewPanel() {
>   const preview = useAppSelector(s => s.rowSelection.preview);
>   if (preview.status === "pending") return <p role="status">正在计算导出范围…</p>;
>   if (preview.status === "error") return <p role="alert">{preview.error}</p>;
>   if (preview.status === "ready" && preview.result) {
>     return <p role="status">{preview.result.rowCount} 行，约 {preview.result.estimatedBytes} 字节</p>;
>   }
>   return <p>尚无当前选择的预览</p>;
> }
> ~~~

## 本章交出了什么

Redux 管的是跨组件共享的纯客户端状态：action 描述事实，reducer 同步算出新状态，异步工作由 thunk 放在 dispatch 之前；`createAsyncThunk` 的 `meta.requestId` 让唯一的预览槽只接收当前请求的结果，取消和错误各自转成明确的状态，服务器数据留给查询缓存。同一个勾选集合在[编辑会话与条件写入](editing-sessions-and-conditional-writes.md)里继续使用：那里要回答，选择跨页、跨筛选时何时作废，以及基于选择打开的编辑抽屉怎样安全保存。

> [!info]- 来源
> 版本按 npm 包登记与官方文档核对，2026-11-12。
> - store 默认项与 reducer 合并（“异步工作插在 dispatch 的路径上”）：[Redux Toolkit `configureStore` — Purpose and Behavior](https://redux-toolkit.js.org/api/configureStore#purpose-and-behavior)；[npm Redux Toolkit 版本列表](https://www.npmjs.com/package/@reduxjs/toolkit?activeTab=versions) 将 2.14.0 标为 latest。
> - slice 与 Immer 不可变更新（“action 怎样经过 store 变成新状态”）：[`createSlice`](https://redux-toolkit.js.org/api/createSlice)、[Writing Reducers with Immer](https://redux-toolkit.js.org/usage/immer-reducers)。
> - 生命周期 action、`requestId`、`signal`、`.abort()`、`meta.aborted`、`rejectWithValue`、`.unwrap()`（“用 requestId 守住唯一的预览槽”“取消与错误”）：[`createAsyncThunk`](https://redux-toolkit.js.org/api/createAsyncThunk)。“只接收仍匹配当前请求 ID 的结果”是应用层的归属选择。
> - thunk、RTK Query、listener middleware 的选用（“哪些状态进 Redux”“异步工作插在 dispatch 的路径上”）：[Asynchronous Logic and Data Fetching](https://redux-toolkit.js.org/usage/usage-guide#asynchronous-logic-and-data-fetching)。
> - 类型化 Hook（“接进 React”）：[Usage with TypeScript](https://redux-toolkit.js.org/usage/usage-with-typescript#getting-the-dispatch-type)、[React-Redux TypeScript 使用说明](https://react-redux.js.org/using-react-redux/usage-with-typescript)；[npm React-Redux 版本列表](https://www.npmjs.com/package/react-redux?activeTab=versions) 将 9.3.1 标为 latest。
> - selector 默认 `===` 比较、新对象触发更新及三种处理方式：[React-Redux Hooks — Equality Comparisons and Updates](https://react-redux.js.org/api/hooks#equality-comparisons-and-updates)；同快照复用的 `Object.is` 检查：[React 19.3.1 `useSyncExternalStoreWithSelector`](https://github.com/react/react/blob/v19.3.1/packages/use-sync-external-store/src/useSyncExternalStoreWithSelector.js)、[React-Redux 9.3.1 `useSelector`](https://github.com/reduxjs/react-redux/blob/v9.3.1/src/hooks/useSelector.ts)。
