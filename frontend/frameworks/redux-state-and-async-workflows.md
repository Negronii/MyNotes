# Redux 如何组织共享界面状态与异步工作？

**案例背景。** 报表页打开 `/reports?sort=recent#summary`，服务端给出 May、April。用户选 **Oldest first** 后，路由把 `sort=oldest` 写成一条新历史记录；路由提交新地址后，组件用新的 `sort` 组成查询 key，TanStack Query 复用仍新鲜的缓存，或在缺少/过期时发请求，结果可用后显示 April、May。浏览器 Back 回到 recent 后，同样按 recent 的查询 key 复用缓存或重取结果。`#summary` 只用于浏览器定位，不会随 HTTP 请求发送。排序由 URL 与路由拥有，报表行由 TanStack Query 缓存服务端结果。Redux（共享状态管理库）只接手另一类问题：报表表格和远处的批量操作栏都需要读取、修改同一份已选报表 ID。选择变化会清除与旧集合对应的预览；用户点“预览导出范围”按钮时，才按当前选中 ID 发起请求。

~~~mermaid
flowchart TD
    A[URL sort=recent] --> B[组件按sort查询报表行]
    B --> C[查询缓存持有 May、April]
    C --> D
    D[选择行] --> E[dispatch action]
    E --> F[reducer更新共享selectedIds]
    F --> G[清空旧预览并使旧requestId失效]
    F --> H[表格与批量操作栏读取同一选择]
    H --> I[用户点击预览导出范围]
    I --> J[dispatch thunk并保存requestId]
    J --> K{返回的requestId仍是当前值？}
    K -->|是| P[保存当前预览或错误]
    K -->|否| Q[忽略过期结果]
    A --> M[选择oldest并新增历史项]
    M --> N[按oldest查缓存或取数，数据可用后显示April、May]
    N --> O[Back恢复recent，复用缓存或重取对应行]
~~~

## 先确定什么状态需要共享

Redux 的价值在于让多个相隔较远的组件围绕同一份客户端状态和明确的更新动作协作。它不会自动取代 URL、组件本地 state 或服务端查询缓存。沿报表案例看，状态由谁拥有，决定了刷新、返回和请求完成时谁负责恢复：

| 状态 | 所有者 | 本例中的结果 |
| --- | --- | --- |
| `sort=recent` 或 `sort=oldest` | URL 与路由 | 刷新、分享地址和浏览器 Back 都能恢复筛选条件 |
| May、April 等报表行 | 服务端；客户端查询缓存保存副本 | 查询身份包含 `sort`，不同排序对应不同结果；见[React 如何维护服务端数据与乐观更新？](./react-server-state-and-optimistic-updates.md#排序值构成查询身份) |
| 已选报表 ID | Redux store | 表格、计数提示和批量操作栏可以读取同一份数组 |
| 当前弹层是否打开 | 使用它的组件 | 只影响局部展示时，不必提升到全局 store |
| 导出预览请求状态 | 本例的 Redux 工作流 | 选择变化清除旧预览；点击按钮后，异步结果只更新它对应的当前请求 |

如果只有一个组件使用某值，就让它留在组件中；两个相邻组件共享时，先比较提升到最近共同父组件是否更简单，见[如何在 React 中组合组件与复用行为？](./react-component-composition.md#把状态放在共同使用者之上的最近一层)。Redux 不会让数据变成“全局自动同步”；它给出明确的读写入口。React Router 路由加载与历史项的提交时机见[React 路由如何把地址映射到界面并加载数据？](./react-routing-and-navigation.md#数据模式先匹配路由，再加载匹配页面的数据)。

## action 怎样经过 store 更新共享选择

在 Redux Toolkit（Redux 官方工具集）中，`configureStore` 建立 store（状态容器）并合并 reducer（状态更新函数）；传入 reducer 对象时，它会按功能组合这些 reducer，并默认启用与 Redux DevTools 浏览器扩展的集成，安装扩展后可检查 action 和状态。DevTools 会看到已派发的数据，因此不要把凭证放进 Redux state 或 action。`createSlice` 将一类状态、reducer 和 action creator（动作创建函数）放在一起。reducer 收到 action（动作）后同步计算下一状态，不执行网络请求或其他副作用。

下面按报表 ID 切换选择。Redux Toolkit 允许 reducer 写成对 draft 的局部修改，Immer 会据此产出新的不可变状态；这不是直接修改 store 中已经发布的对象。把选择保存为 ID 而不是数组下标，排序改变后仍会选择同一份报表。

一个 action 只说明“发生了什么”，表格组件不需要自己去找批量操作栏并直接改它的 props。调用 `dispatch(toggleReport("april"))` 后，reducer 将 `selectedIds` 从 `[]` 变成 `["april"]`；所有订阅这个值的组件都能看到新状态。它们仍要使用稳定的报表 ID，不应以当前列表位置作身份。

## 异步结果怎样避免覆盖较新的选择

导出范围预览是用户点击按钮后开始的一次性工作。假设用户先选中 May，点击“预览导出范围”后为 `["may"]` 派发请求；再选中 April，旧预览会清空，用户再次点击按钮才会为 `["may", "april"]` 派发第二个请求。如果第一份响应较晚到达，它描述的是旧集合，不能覆盖第二份预览。`createAsyncThunk`（异步 thunk 创建器）会为一次调用派发 `pending`、`fulfilled` 或 `rejected` 生命周期 action，并把本次唯一 `requestId` 放在 `action.meta` 中。reducer 只接受仍匹配当前 ID 的结果。

这个示例约定接口 `POST /api/reports/export-preview` 接收 `reportIds`，只返回非负安全整数 `reportCount` 与 `estimatedBytes`，不创建导出文件。服务端仍须按当前身份和租户逐个授权这些 ID；客户端 Redux 中的选择不能代替[服务端资源权限检查](../../engineering-foundations/security/web-security-and-authentication.md)。把响应先视为 `unknown` 并检查结构，因为 TypeScript 泛型或断言本身不会验证服务器实际返回值；边界校验细节见[TypeScript 如何处理不可信 JSON？](../typescript/advanced-typescript.md)。

~~~typescript
// features/report-selection/reportSelectionSlice.ts
import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";

type Preview = { reportCount: number; estimatedBytes: number };
type PreviewState = {
  status: "idle" | "pending" | "ready" | "error";
  currentRequestId: string | null;
  result: Preview | null;
  error: string | null;
};
type ReportSelectionState = {
  selectedIds: string[];
  preview: PreviewState;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonNegativeSafeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function parsePreview(value: unknown): Preview {
  if (
    !isRecord(value) ||
    !isNonNegativeSafeInteger(value.reportCount) ||
    !isNonNegativeSafeInteger(value.estimatedBytes)
  ) {
    throw new Error("报表服务返回了无效的导出预览");
  }
  return { reportCount: value.reportCount, estimatedBytes: value.estimatedBytes };
}

export const loadExportPreview = createAsyncThunk<Preview, string[]>(
  "reportSelection/loadExportPreview",
  async (reportIds, { signal }) => {
    const response = await fetch("/api/reports/export-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reportIds }),
      signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload: unknown = await response.json();
    return parsePreview(payload);
  }
);

const emptyPreview = (): PreviewState => ({
  status: "idle",
  currentRequestId: null,
  result: null,
  error: null,
});

const initialState: ReportSelectionState = {
  selectedIds: [],
  preview: emptyPreview(),
};

export const reportSelectionSlice = createSlice({
  name: "reportSelection",
  initialState,
  reducers: {
    toggleReport(state, action: PayloadAction<string>) {
      const index = state.selectedIds.indexOf(action.payload);
      if (index === -1) state.selectedIds.push(action.payload);
      else state.selectedIds.splice(index, 1);
      state.preview = emptyPreview();
    },
    clearSelection(state) {
      state.selectedIds = [];
      state.preview = emptyPreview();
    },
  },
  extraReducers: builder => {
    builder
      .addCase(loadExportPreview.pending, (state, action) => {
        state.preview = {
          status: "pending",
          currentRequestId: action.meta.requestId,
          result: null,
          error: null,
        };
      })
      .addCase(loadExportPreview.fulfilled, (state, action) => {
        if (state.preview.currentRequestId !== action.meta.requestId) return;
        state.preview = {
          status: "ready",
          currentRequestId: null,
          result: action.payload,
          error: null,
        };
      })
      .addCase(loadExportPreview.rejected, (state, action) => {
        if (state.preview.currentRequestId !== action.meta.requestId) return;
        state.preview = {
          status: action.meta.aborted ? "idle" : "error",
          currentRequestId: null,
          result: null,
          error: action.meta.aborted ? null : action.error.message ?? "请求失败",
        };
      });
  },
});

export const { toggleReport, clearSelection } = reportSelectionSlice.actions;
export const reportSelectionReducer = reportSelectionSlice.reducer;
~~~

异步 action 创建器负责启动请求；`extraReducers` 在 slice（状态切片）里响应它的生命周期。每次选择变化都会把预览状态和当前 ID 清空；新请求开始时记录自己的 ID。因而，旧请求即使没有取消且稍后成功或失败，也无法提交到当前界面。

> [!example] 两份请求按开始顺序而不是返回顺序判定
> 初始行是 May、April。用户只选 May 后点击“预览导出范围”，第一次预览请求带 ID `req-1`；接着用户再选 April，旧预览清空，再次点击同一按钮后才开始 `req-2`。`req-2` 先返回 `reportCount: 2`，状态变为 `ready` 且 `currentRequestId` 归为 `null`。随后 `req-1` 即使返回 `reportCount: 1`，也因 ID 与当前的 `null` 不匹配而被忽略。浏览器 Back 只把 URL 排序恢复为 recent；同一批稳定 ID 仍表示已选 May、April。

`requestId` 负责识别一次调用，不会自动停止网络请求。payload creator 收到的 `signal` 可以传给 `fetch`；调用 `dispatch(loadExportPreview(ids)).abort()` 也会请求取消该 thunk。取消客户端读取不保证已经接到请求的服务端停止工作。示例的状态只表示“当前集合的预览”，若产品要同时保留多份并发预览或多个导出作业，应按 `requestId` 或服务端作业 ID 分开存储，而不能用一个 latest-request 槽覆盖所有结果。

## React 组件怎样读取并派发类型安全的状态

`configureStore` 会组合 reducer，并默认包含 thunk middleware（中间件）；在 TypeScript 项目中，从创建好的 store 推导 `RootState` 和 `AppDispatch`，再用 React-Redux（Redux 的 React 绑定）9.1 及以上的 `.withTypes()` 建立应用专用 Hook（钩子）。Hook 文件只导入 store 的类型，避免组件与 store 之间形成运行时循环导入。

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

根节点用 `<Provider store={store}>` 包住需要访问 Redux 的 React 子树。行组件按报表 ID 读取选中状态并派发 action；批量工具栏读取同一份数组，再以它的快照发起预览。

~~~tsx
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { loadExportPreview, toggleReport } from "./reportSelectionSlice";

type Report = { id: string; period: string; title: string };

function ReportRow({ report }: { report: Report }) {
  const selected = useAppSelector(state =>
    state.reportSelection.selectedIds.includes(report.id)
  );
  const dispatch = useAppDispatch();

  return (
    <li>
      <label>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => dispatch(toggleReport(report.id))}
        />
        {report.period} — {report.title}
      </label>
    </li>
  );
}

function ExportPreviewToolbar() {
  const selectedIds = useAppSelector(state => state.reportSelection.selectedIds);
  const preview = useAppSelector(state => state.reportSelection.preview);
  const dispatch = useAppDispatch();

  return (
    <section aria-label="批量操作">
      <button
        type="button"
        disabled={selectedIds.length === 0 || preview.status === "pending"}
        onClick={() => void dispatch(loadExportPreview([...selectedIds]))}
      >
        预览导出范围
      </button>
      {preview.status === "pending" && <p role="status">正在计算导出范围…</p>}
      {preview.status === "ready" && preview.result && (
        <p role="status">
          {preview.result.reportCount} 份报表，约 {preview.result.estimatedBytes} 字节
        </p>
      )}
      {preview.status === "error" && <p role="alert">{preview.error}</p>}
    </section>
  );
}
~~~

`useSelector` 默认用严格引用相等比较前后选择结果；像上面一样读取布尔值、字符串或 store 中现有数组可以直接观察状态变化。若每次 selector 都新建对象，默认比较会认为结果不同而触发重新渲染；需要一起返回多个字段时，可分别调用 Hook、使用有记忆的 selector，或显式选择比较函数。渲染成本是否值得优化应通过[React 工作测量](../performance/react-rendering-optimization.md)判断。

## middleware 与 thunk 分别插入哪一步

普通 action 到达 Redux store 后，同步调用 reducer 并保存新状态。middleware（中间件）包裹 `dispatch`，可以在 action 到达 reducer 前后观察或扩展这一流程；thunk middleware 允许 `dispatch` 接受函数，让这个函数访问 `dispatch`、`getState` 并等待异步任务，再派发普通结果 action。Redux Toolkit 默认已配置 thunk，新增中间件时用 `getDefaultMiddleware()` 扩展默认列表，不要为了添加一项日志就替换默认值。

`createAsyncThunk` 已为一次请求组织了 pending、fulfilled、rejected 三种 action；一般无需再手写一个“把所有函数 action 变成异步”的 middleware。只有当工作需要响应后续 action 或状态变化、而不是由某次显式派发触发时，才进一步考虑 listener middleware。缓存服务端数据可用 Redux Toolkit Query（RTK Query）；本报表案例已经以 TanStack Query 持有查询缓存，不再把同一批行同时放入 Redux。

> [!info]- 来源
> - 状态切片、自动生成的 action creator、Immer draft、`configureStore` 默认 middleware 与 DevTools：[Redux Toolkit — `createSlice`](https://redux-toolkit.js.org/api/createSlice)、[`configureStore`](https://redux-toolkit.js.org/api/configureStore)、[Why Redux Toolkit Is Redux Today](https://redux-toolkit.js.org/introduction/why-rtk-is-redux-today)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 异步 thunk 生命周期 action、`meta.requestId`、`signal`、`abort()` 与错误结果：[Redux Toolkit — `createAsyncThunk`](https://redux-toolkit.js.org/api/createAsyncThunk)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 缓存服务端数据用 Redux Toolkit Query、一次命令式异步工作用 thunk、响应后续状态变化用 listener middleware：[Redux Toolkit — Side Effects Approaches](https://redux-toolkit.js.org/usage/side-effects-approaches)，Redux Toolkit 2.14.0，核对日期：2026-11-06。
> - 从 store 推导 `RootState` 和 `AppDispatch`，以及用 `.withTypes()` 创建 typed hooks：[Redux Toolkit — TypeScript Quick Start](https://redux-toolkit.js.org/tutorials/typescript)、[React-Redux — TypeScript Usage](https://react-redux.js.org/using-react-redux/usage-with-typescript)，React-Redux 9.3.1，核对日期：2026-11-06。
> - selector 默认使用严格 `===` 比较及多值选择建议：[React-Redux — Hooks API](https://react-redux.js.org/api/hooks)，React-Redux 9.3.1，核对日期：2026-11-06。
> - 路由 PUSH 加入新筛选历史、POP 依 URL 恢复筛选和目标数据：[React Router 路由导航](./react-routing-and-navigation.md#数据模式先匹配路由，再加载匹配页面的数据)，React Router 8.5.1，核对日期：2026-11-06。
> - `sort` 是 URL 状态、报表行为查询数据，不应由 Redux 再保存第二份：[React Server State 章节](./react-server-state-and-optimistic-updates.md#排序值构成查询身份)，TanStack Query v5.90.3，核对日期：2026-11-06。
