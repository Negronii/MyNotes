# Redux 如何组织共享界面状态与异步工作？

**合成案例。** 教学报表页打开 `/reports?sort=recent#summary`。下文的 May、April 两行、ID `may` / `april`、预览接口及其返回值都是合成示例，不代表真实产品契约。本例中，路由先提交地址，再由组件里的查询读取报表。排序条件归路由所有；查询缓存的 query key（查询键）包含 `sort`，所以 May、April 两行按当前地址读取或从缓存复用。用户选择 **Oldest first** 后，路由把 `sort=oldest` 写入新历史项，再以新查询键读取 April、May；浏览器 Back 恢复 `recent` 和对应查询。片段 `#summary` 只用于浏览器定位，不发送给服务器。

排序和报表行已有各自的所有者。本章关心的是另一类纯客户端 state（状态）：用户勾选了哪些报表，以及针对这组选择的导出预览请求。报表行、批量操作栏和导出预览区分散在页面各处，却都要读写这份状态，于是把它放进 Redux（集中管理共享状态的 JavaScript 库）的 store（状态容器）。行组件派发选择动作，工具栏发起预览，预览区显示结果。本例的预览接口只估算报表数量与字节数，不创建文件或作业。

## 先确定什么状态需要共享

状态由谁拥有，决定了刷新、Back 和请求完成时谁负责恢复或更新它：

| 状态 | 所有者 | 本例中的行为 |
| --- | --- | --- |
| `sort=recent` 或 `sort=oldest` | URL 与路由 | 分享地址、刷新和浏览器历史恢复排序条件；Back 不会自动改动 Redux 中的已选 ID。 |
| May、April 等报表行 | 服务器；TanStack Query 保存客户端缓存副本 | 查询身份包含 `sort`；相同查询可复用缓存，是否重取由缓存策略决定。不要再把同一批行复制到 Redux。 |
| 已选报表 ID | Redux store | 报表行、批量工具栏能读取同一组稳定 ID；排序或列表位置变化后仍指向同一份报表。 |
| 预览状态与结果 | 本例的 Redux 工作流 | 工具栏和预览区共用；选择改变时，可在更新 ID 的同一次 reducer 计算中让旧预览失效。 |
| 当前弹层是否打开 | 使用它的组件 | 若只影响单个组件的展示，就留在组件本地 state。 |

若只有一个组件使用某个值，就让它留在组件中；两个相邻组件共享时，先考虑把它提升到最近的共同父组件是否更简单，见[如何在 React 中组合组件与复用行为？](./react-component-composition.md#把状态放在共同使用者之上的最近一层)。当页面中多个相距较远的部分要共享同一状态，或需要统一、可追踪的更新时，再评估 Redux。若预览结果可按选择集合缓存复用，还应比较已有的查询缓存是否更合适；本例只保留一份随选择失效的预览，所以用 Redux 的 slice（状态切片）来展示这一工作流。

路由和数据缓存仍各负其责：路由把地址变化交给查询层，查询键区分不同排序的结果，请求缓存负责复用或更新服务器数据。换用其他缓存库时，也应为这批行只选定一个缓存所有者。Redux Toolkit Query 是 Redux 应用中的一种服务器数据缓存方案；本例已用 TanStack Query，因此不在 Redux 里再存一份报表行。查询键怎样区分排序结果，见[排序如何构成服务端查询身份](./react-server-state-and-optimistic-updates.md#排序值构成查询身份)。

Redux store 默认只在应用本次运行期间保存已选 ID；刷新后能否恢复，取决于是否另外实现了持久化。本例没有把选择编码进 URL，也没有启用持久化。

## action 怎样经过 store 更新共享选择

表格中的复选框派发的是“某份报表被选中或取消选中”这个事实。Redux 的 action（动作）是描述变化的普通数据对象，其中 `payload`（载荷）携带这次变化所需的值；reducer（归约函数）根据当前 state 和 action 计算下一份 state。行组件不需要找到批量工具栏去改它的 props：每行的 selector（选择器）从 ID 数组算出自己是否被选中，工具栏则直接订阅这个数组。

假设开始时 `selectedIds=[]`。点击 April 行会派发类似 `{ type: "reportSelection/reportToggled", payload: "april" }` 的 action。同步 reducer 把下一状态算成 `selectedIds=["april"]`，store 随后通知订阅者，各组件的 selector 重新检查。April 行的 selector 得到 `true`，工具栏读到新的数组引用；列表排序不会改变 `"april"` 的身份，不要用数组下标代替报表 ID。

Redux Toolkit（Redux 官方工具集）2.14.0 的 `createSlice` 将初始状态、reducers 和生成的 action creator 放在一起。reducer 中可以写 `push`、`splice` 这类看似原地修改的代码：Immer 把它们记录为对 draft（草稿副本）的修改，再产出新的不可变 state，并没有直接改动 store 已发布的对象。reducer 只计算状态，不能在里面发网络请求、启动计时器或取消请求。

## middleware 与 thunk 分别插入哪一步

reducer 不能发请求，异步工作就要放在 dispatch 的路径上。普通 action 先经过已配置的 middleware（中间件），再被转发到核心 `dispatch`，然后根 reducer 同步计算新状态，store 保存结果并通知订阅者。中间件包裹 `dispatch`，可以观察 action、扩展 dispatch 能接受的输入，或在 action 到达 reducer 前后执行副作用。

thunk middleware（thunk 中间件）让 `dispatch` 接受一个函数；这个 thunk（函数式动作）在 reducer 外运行，可以读取 `getState`、派发普通 action 并等待异步操作；Redux 核心 store 本身仍然只根据普通 action 同步更新状态。Redux Toolkit 的 `configureStore` 默认加入 thunk middleware、开发期检查与 Redux DevTools 集成；添加自定义中间件时，用 `getDefaultMiddleware().concat(...)` 保留默认项。DevTools 可看到已派发的 action 与 state，因此不要放入凭证，也不要把 `AbortController`、Promise 等运行对象保存到 Redux state。

`createAsyncThunk` 用来生成常见请求生命周期的 action：正常启动时先派发 `pending`，再调用 payload creator（载荷函数）执行请求，完成后按结果派发 `fulfilled` 或 `rejected`。slice 用 `extraReducers` 响应这些 action。注意这套生命周期是 `createAsyncThunk` 提供的，手写的普通 thunk 不会自动派发它们。若工作需要响应后续 action 或状态变化，再评估 listener middleware；普通按钮触发的请求一般不必手写一套异步 middleware。

## 异步结果怎样避免覆盖较新的选择

预览请求携带发起时那一刻的 ID 快照。假设用户先选 May 并点击预览，第一份请求是 `["may"]`；之后用户又选了 April，reducer 立即清空旧预览和当前请求 ID。用户再次点击，第二份请求是 `["may", "april"]`。两份响应的返回顺序不确定，第一份可能晚于第二份才到，所以 reducer 不能只看“收到成功”，还要确认这份结果仍属于当前请求。`requestId` 由 thunk 在客户端生成，随生命周期 action 的 `meta` 传给 reducer；它不写进 HTTP 请求，也不需要服务器回传，HTTP body 只含 `reportIds`。

本例接口约定 `POST /api/reports/export-preview` 只读取给定 ID 并返回非负安全整数 `reportCount`、`estimatedBytes`，不创建文件、作业或其他远端效果。服务器仍须按当前调用者及租户范围逐个授权这些 ID；客户端选中状态不能代替[服务器资源权限检查](../../engineering-foundations/security/web-security-and-authentication.md)。网络 JSON 先作为 `unknown` 处理，因为 TypeScript 类型声明不会检查实际响应；边界校验见 [TypeScript 如何处理不可信 JSON？](../typescript/advanced-typescript.md)。

**点击预览后，先记录请求身份，再开始网络读取：**

~~~mermaid
flowchart TD
    CLICK["工具栏派发预览 thunk"] --> PENDING["createAsyncThunk 先派发 pending"]
    PENDING --> SAVE["reducer 记录<br/>state.preview.currentRequestId = action.meta.requestId"]
    SAVE --> POST["payload creator 再发 POST<br/>body 只有 reportIds 快照"]
~~~

本例的 `createAsyncThunk` 每次正常启动都先派发 `pending`，reducer 把其中唯一的 `requestId` 记到 `state.preview.currentRequestId`。请求完成时，reducer 只接受 ID 仍与之匹配的 fulfilled 或 rejected；而选择变化会清空这个字段，新请求开始又会换成新 ID。因此，过期请求即使没有被取消、晚些才成功或失败，也覆盖不了当前预览。

**完成或取消会产生生命周期 action，再检查结果是否仍属于当前预览：**

~~~mermaid
flowchart LR
    ACTION["fulfilled / rejected action<br/>requestId 在 action.meta"] --> CHECK{"与<br/>state.preview.currentRequestId<br/>匹配？"}
    CHECK -->|是| APPLY["按结果更新<br/>fulfilled → ready<br/>rejected → error 或 idle"]
    CHECK -->|否| IGNORE["忽略过期结果"]
~~~

> [!example] 两份预览按请求身份接收，不按返回先后接收
>
> `req-1` 和 `req-2` 是便于跟踪的请求标签，实际 ID 由 thunk 生成。响应中的 `4096` 与 `1024` 字节也是合成教学值。
>
> | 操作或返回 | `selectedIds` | 当前预览状态 |
> | --- | --- | --- |
> | 初始 | `[]` | `idle`；`state.preview.currentRequestId = null` |
> | 选 May，启动 `req-1` | `["may"]` | `pending`；当前 ID 是 `req-1`，POST body 是 `{"reportIds":["may"]}` |
> | 选 April | `["may", "april"]` | `idle`；旧预览与当前 ID 清为 `null` |
> | 再次启动 `req-2` | `["may", "april"]` | `pending`；当前 ID 是 `req-2`，POST body 是 `{"reportIds":["may","april"]}` |
> | `req-2` 先返回 `{reportCount: 2, estimatedBytes: 4096}` | `["may", "april"]` | `meta.requestId` 匹配，转为 `ready`；当前 ID 清为 `null` |
> | `req-1` 后返回 `{reportCount: 1, estimatedBytes: 1024}` | `["may", "april"]` | `meta.requestId` 与 `null` 不匹配，忽略旧结果；预览仍是 `req-2` 的结果 |
>
> 浏览器 Back 只恢复路由的 `sort` 和相应的报表查询；本例没有把已选 ID 放进 URL，所以 `["may", "april"]` 不随 Back 改变。

`requestId` 负责判断结果归属，取消负责尽量停止客户端的工作，两者不是同一件事。`dispatch(thunk)` 返回一个带 `.abort()` 方法的 Promise；调用它会触发 payload creator 收到的 `signal`，本例已把这个 `signal` 传给 `fetch`。当前请求收到取消结果时，reducer 将预览状态恢复为 `idle`，保留用户选择。若它已经被新选择清空或被新请求取代，取消产生的旧 rejected action 也会因 ID 不匹配而忽略。当前的工具栏没有保存 dispatch 返回的 Promise；若要接入取消，调用方需保存它并在合适的时机调用 `.abort()`。客户端中止读取不保证服务器已经停止处理请求。这里只用一个状态槽保存当前选择的那份预览；若要同时保留多个并发预览或导出作业，应按请求 ID 或服务端作业 ID 分别存储状态。

HTTP 错误状态、无效 JSON 和不符合约定结构的响应，都会变成 rejected action。payload creator 将这些错误统一转换成固定文案 `无法计算导出预览，请稍后重试`，不会把 parser 的原始 `SyntaxError` 或响应片段放进 Redux action、state、界面或 DevTools。`dispatch(thunk)` 返回的 Promise 会以 fulfilled 或 rejected action 结束；若调用方需要失败时进入 `catch`，可用 `.unwrap()` 读取成功 payload，非取消失败会在 `catch` 中收到本例的固定文案。本例的预览区直接由 Redux state 驱动，因此工具栏不需要等待这个 Promise。当 rejected action 的 `requestId` 仍匹配当前值时，界面进入 `error` 并显示固定文案；已选 ID 保留；因为本例接口只读，用户可以用相同选择再次请求预览。取消当前请求则不显示为错误。若服务器定义了结构化错误载荷，先按运行时 schema 校验，再用 `rejectWithValue` 保存允许展示的字段。

本例没有对用户选择做乐观更新：选择 action 记录的是已经发生的本地操作，预览出错也不会把 ID 回滚成旧数组。预览接口也没有远端写入，因此不需要补偿操作。若把按钮改为“创建导出作业”，网络超时就不能证明服务器没有创建作业；那是有外部效果的命令，需要由接口提供幂等键、作业 ID 或核对流程，不能照搬这个只读预览的重试结论。

> [!example]- Slice 与异步请求的完整实现
>
> ~~~typescript
> // features/report-selection/reportSelectionSlice.ts
> import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
>
> type Preview = { reportCount: number; estimatedBytes: number };
> type PreviewState = {
>   status: "idle" | "pending" | "ready" | "error";
>   currentRequestId: string | null;
>   result: Preview | null;
>   error: string | null;
> };
> type ReportSelectionState = {
>   selectedIds: string[];
>   preview: PreviewState;
> };
>
> function isRecord(value: unknown): value is Record<string, unknown> {
>   return typeof value === "object" && value !== null && !Array.isArray(value);
> }
>
> function isNonNegativeSafeInteger(value: unknown): value is number {
>   return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
> }
>
> function parsePreview(value: unknown): Preview {
>   if (
>     !isRecord(value) ||
>     !isNonNegativeSafeInteger(value.reportCount) ||
>     !isNonNegativeSafeInteger(value.estimatedBytes)
>   ) {
>     throw new Error("报表服务返回了无效的导出预览");
>   }
>   return { reportCount: value.reportCount, estimatedBytes: value.estimatedBytes };
> }
>
> const previewFailedMessage = "无法计算导出预览，请稍后重试";
>
> export const loadExportPreview = createAsyncThunk<
>   Preview,
>   string[],
>   { rejectValue: string }
> >(
>   "reportSelection/loadExportPreview",
>   async (reportIds, { signal, rejectWithValue }) => {
>     try {
>       const response = await fetch("/api/reports/export-preview", {
>         method: "POST",
>         headers: { "Content-Type": "application/json" },
>         body: JSON.stringify({ reportIds }),
>         signal,
>       });
>       if (!response.ok) return rejectWithValue(previewFailedMessage);
>
>       const payload: unknown = await response.json();
>       return parsePreview(payload);
>     } catch (error) {
>       // Keep aborts recognizable; normalize all other errors before they reach UI or DevTools.
>       if (signal.aborted) throw error;
>       return rejectWithValue(previewFailedMessage);
>     }
>   }
> );
>
> const emptyPreview = (): PreviewState => ({
>   status: "idle",
>   currentRequestId: null,
>   result: null,
>   error: null,
> });
>
> const reportSelectionSlice = createSlice({
>   name: "reportSelection",
>   initialState: {
>     selectedIds: [],
>     preview: emptyPreview(),
>   } satisfies ReportSelectionState as ReportSelectionState,
>   reducers: {
>     reportToggled(state, action: PayloadAction<string>) {
>       const index = state.selectedIds.indexOf(action.payload);
>       if (index === -1) state.selectedIds.push(action.payload);
>       else state.selectedIds.splice(index, 1);
>
>       // 旧选择的结果不可继续代表当前 ID 集合。
>       state.preview = emptyPreview();
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
>           status: "pending",
>           currentRequestId: action.meta.requestId,
>           result: null,
>           error: null,
>         };
>       })
>       .addCase(loadExportPreview.fulfilled, (state, action) => {
>         if (state.preview.currentRequestId !== action.meta.requestId) return;
>
>         state.preview = {
>           status: "ready",
>           currentRequestId: null,
>           result: action.payload,
>           error: null,
>         };
>       })
>       .addCase(loadExportPreview.rejected, (state, action) => {
>         if (state.preview.currentRequestId !== action.meta.requestId) return;
>
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
> export const { reportToggled, selectionCleared } = reportSelectionSlice.actions;
> export const reportSelectionReducer = reportSelectionSlice.reducer;
> ~~~

## React 组件怎样读取并派发类型安全的状态

slice 写好后，还要把它接进 store，再让组件读写。向 `configureStore` 传入 reducer 映射，它会组合出根 reducer；根状态类型和 dispatch 类型再从 store 推导出来。React-Redux 自 9.1.0 起提供 `.withTypes()`，让带类型的 Hook 复用这两个类型，本篇按 9.3.1 核验。应用根节点用 `<Provider store={store}>` 提供 store。下面的 `hooks.ts` 只导入 store 的类型，不会引入反向的运行时依赖。

~~~typescript
// app/store.ts
import { configureStore } from "@reduxjs/toolkit";
import { reportSelectionReducer } from "../features/report-selection/reportSelectionSlice";

export const store = configureStore({
  reducer: { reportSelection: reportSelectionReducer },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
~~~

~~~typescript
// app/hooks.ts
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "./store";

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
~~~

行组件读取一个布尔值并派发选择动作；工具栏发起请求；页面另一处的预览区订阅同一 slice 中的预览状态：

> [!example]- 行复选框、预览按钮与结果面板的接线
>
> ~~~tsx
> import { useAppDispatch, useAppSelector } from "../../app/hooks";
> import { loadExportPreview, reportToggled } from "./reportSelectionSlice";
>
> type Report = { id: string; period: string; title: string };
>
> function ReportRow({ report }: { report: Report }) {
>   const selected = useAppSelector(state =>
>     state.reportSelection.selectedIds.includes(report.id)
>   );
>   const dispatch = useAppDispatch();
>
>   return (
>     <li>
>       <label>
>         <input
>           type="checkbox"
>           checked={selected}
>           onChange={() => dispatch(reportToggled(report.id))}
>         />
>         {report.period} — {report.title}
>       </label>
>     </li>
>   );
> }
>
> function ExportPreviewToolbar() {
>   const selectedIds = useAppSelector(state => state.reportSelection.selectedIds);
>   const previewStatus = useAppSelector(state => state.reportSelection.preview.status);
>   const dispatch = useAppDispatch();
>
>   return (
>     <button
>       type="button"
>       disabled={selectedIds.length === 0 || previewStatus === "pending"}
>       onClick={() => void dispatch(loadExportPreview([...selectedIds]))}
>     >
>       预览导出范围
>     </button>
>   );
> }
>
> function ExportPreviewPanel() {
>   const preview = useAppSelector(state => state.reportSelection.preview);
>
>   if (preview.status === "pending") return <p role="status">正在计算导出范围…</p>;
>   if (preview.status === "error") return <p role="alert">{preview.error}</p>;
>   if (preview.status === "ready" && preview.result) {
>     return (
>       <p role="status">
>         {preview.result.reportCount} 份报表，约 {preview.result.estimatedBytes} 字节
>       </p>
>     );
>   }
>   return <p>尚无当前选择的预览</p>;
> }
> ~~~

store 通知订阅者后，React-Redux 先检查根 state 快照：如果 `Object.is` 判断快照没变，就复用已有的 selector 结果，不必重新运行 selector；快照变了，才重新计算，并默认用严格相等 `===` 比较新旧结果。行组件的 selector 返回布尔值：与这一行无关的 action 不会改变它，于是订阅不会触发该行重新渲染；只有这一行的选择变化时，布尔值才会变。工具栏直接读取 store 中的数组引用，预览区读取当前的预览对象。

不要每次 selector 都临时拼一个对象，例如 `state => ({ selected: state.reportSelection.selectedIds.includes(id), status: state.reportSelection.preview.status })`；即使字段值没变，这个对象每次都是新引用，只要 Redux state 有任何更新，默认比较就会认为结果不同。需要合并多个值时，可以分别调用 Hook、使用记忆化 selector，或在确认浅比较语义合适后传入 `shallowEqual`。selector 应是纯函数。以上只描述 store 通知引发的检查；组件仍可能因父组件更新而 render（渲染），selector 也可能在渲染时或开发期检查中运行。是否继续优化应通过[React 工作测量](../performance/react-rendering-optimization.md)判断。

> [!info]- 来源
> 版本按公开包登记与官方文档核对，日期：2026-11-12。
>
> - **store 默认项与 reducer 合并。** [Redux Toolkit `configureStore` — Purpose and Behavior](https://redux-toolkit.js.org/api/configureStore#purpose-and-behavior) 说明它组合 reducer、默认加入 thunk、开发期检查并启用 DevTools；[npm 上的 Redux Toolkit 版本列表](https://www.npmjs.com/package/@reduxjs/toolkit?activeTab=versions) 将 2.14.0 标为 latest。
> - **slice 与不可变更新。** [Redux Toolkit `createSlice`](https://redux-toolkit.js.org/api/createSlice) 说明它生成 action creator 和 reducer；[Writing Reducers with Immer](https://redux-toolkit.js.org/usage/immer-reducers) 说明 draft 写法如何产出不可变更新。
> - **异步生命周期、请求身份、取消与错误。** [Redux Toolkit `createAsyncThunk`](https://redux-toolkit.js.org/api/createAsyncThunk) 说明三种生命周期 action、`requestId`、`signal`、`.abort()`、`meta.aborted`、序列化错误与 `rejectWithValue`。本例只接收仍匹配当前请求 ID 的规则，是应用级的状态归属选择；网络错误在 thunk 边界转成固定文案。
> - **副作用工具选择。** [Redux Toolkit — Asynchronous Logic and Data Fetching](https://redux-toolkit.js.org/usage/usage-guide#asynchronous-logic-and-data-fetching) 建议先用 thunk 处理通常的命令式异步逻辑，使用 RTK Query 管理 Redux 应用中的服务器数据，并在需要响应后续 action/state 时考虑 listener middleware。本文没有把 TanStack Query 缓存的行复制进 Redux。
> - **TypeScript hooks。** [Redux Toolkit — Usage with TypeScript](https://redux-toolkit.js.org/usage/usage-with-typescript#getting-the-dispatch-type) 示例从 store 推导 `AppDispatch` 并用 `.withTypes()` 建立 Hook；[React-Redux TypeScript 使用说明](https://react-redux.js.org/using-react-redux/usage-with-typescript) 展示 `useSelector.withTypes()`；[npm 上的 React-Redux 版本列表](https://www.npmjs.com/package/react-redux?activeTab=versions) 将 9.3.1 标为 latest。
> - **selector 引用比较。** [React-Redux Hooks API — Equality Comparisons and Updates](https://react-redux.js.org/api/hooks#equality-comparisons-and-updates) 说明默认严格 `===` 比较、返回新对象会触发更新，以及分开选择、记忆化 selector 和 `shallowEqual` 这些处理方式。 同快照复用见 [React 19.3.1 selector helper](https://github.com/react/react/blob/v19.3.1/packages/use-sync-external-store/src/useSyncExternalStoreWithSelector.js) 的 `Object.is` 检查；[React-Redux 9.3.1 useSelector](https://github.com/reduxjs/react-redux/blob/v9.3.1/src/hooks/useSelector.ts) 将 store 快照和 selector 接到此 helper。
> - **路由与服务端数据交接。** [React 路由如何把地址映射到界面并加载数据](./react-routing-and-navigation.md#数据模式先匹配路由，再加载匹配页面的数据) 负责历史导航与路由输入；[服务端状态章节](./react-server-state-and-optimistic-updates.md#排序值构成查询身份) 负责查询键、缓存与过期请求。URI fragment（片段）不属于服务器请求目标，见 [RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)。
