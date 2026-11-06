# React如何把一次用户操作变成界面更新？

**案例背景。** 浏览器主线已经把 `/reports?sort=recent#summary` 的点击交给 React 处理器。`#summary` 是浏览器定位片段，不会随 HTTP 请求发给服务端；服务端依据 `sort=recent` 返回 May、April。本章从 React 处理器继续：用户点击 **Oldest first**，排序状态请求变为 `oldest`，完整应用以 `pushState` 记录新筛选项，可见行在下一次提交时先变成 April、May；随后 Effect（副作用同步）请求对应服务端数据，只有仍有效的 Effect 响应才能确认新结果。按浏览器后退时，路由从 URL 恢复 `recent`，列表回到 May、April；这段 React 示例省略 URL/history 集成，细节见[筛选状态与前进后退](../browser/browser-navigation-and-history.md#让筛选状态跟随地址栏与前进后退)。React 负责从 state（状态）推导下一份界面描述，并提交 commit（提交）的 DOM（文档对象模型）变化；浏览器样式、布局和绘制接回[浏览器渲染主线](../browser/browser-basics.md)。

~~~mermaid
flowchart TD
    A[点击 Oldest first] --> B[处理器请求 sort=oldest]
    B --> C[下一次 render（渲染）读到 oldest]
    C --> D[按稳定 key（键）对应报表行]
    D --> E[提交必要 DOM 变化]
    E --> F[Effect 请求当前排序]
    F --> G{该 Effect 仍有效？}
    G -- 是（ignore=false） --> H[保存服务端结果并再次 render]
    G -- 否（已 cleanup） --> I[忽略过期响应]
    E --> J[浏览器后续处理样式与像素]
~~~

## 处理器读到的是本次界面的状态快照

state（状态）不在组件函数的局部变量里被原地改写。React 每次调用组件时给它一份当前快照；事件处理器也属于那次 render（渲染）。调用 setter（状态更新函数）会排入下一次状态更新，因此同一处理器里的 `sort` 仍然是 `recent`。

报表用 `periodStart` 保存 `YYYY-MM-DD` 排序值，`period` 只作为 May、April 这样的显示标签；不能按月份单词的字母顺序推断日期先后。

~~~tsx
import { useEffect, useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; periodStart: string; title: string };

declare function fetchReports(sort: SortOrder): Promise<Report[]>;

const initialReports: Report[] = [
  { id: "may", period: "May", periodStart: "2026-05-01", title: "May summary" },
  { id: "april", period: "April", periodStart: "2026-04-01", title: "April summary" }
];
// 路由把 URL 的 sort=recent 和这份服务端响应交给 ReportsPage。

function sortReports(reports: Report[], sort: SortOrder) {
  // 复制数组，避免对 state 持有的数组原地 sort。
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function ReportsPage({
  initialSort,
  initialReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
}) {
  const [sort, setSort] = useState(initialSort);
  const [requestId, setRequestId] = useState(0);
  const [reports, setReports] = useState(initialReports);
  const [status, setStatus] = useState<"confirmed" | "pending" | "error">("confirmed");

  function chooseSort(nextSort: SortOrder) {
    if (nextSort === sort) return;
    setSort(nextSort);
    setRequestId(id => id + 1);
    setStatus("pending");
  }

  useEffect(() => {
    if (requestId === 0) return;

    let ignore = false;
    fetchReports(sort).then(
      nextReports => {
        if (!ignore) {
          setReports(nextReports);
          setStatus("confirmed");
        }
      },
      () => {
        if (!ignore) setStatus("error");
      }
    );

    return () => {
      ignore = true;
    };
  }, [sort, requestId]);

  const visibleReports = sortReports(reports, sort);

  return (
    <section>
      <button type="button" onClick={() => chooseSort("oldest")}>
        Oldest first
      </button>
      <p aria-live="polite">
        {status === "pending" ? "正在确认服务端结果" :
         status === "error" ? "确认失败；仍显示本地已有报表" :
         `当前排序：${sort}`}
      </p>
      <ul>
        {visibleReports.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ul>
    </section>
  );
}

function ReportsRoute() {
  return <ReportsPage initialSort="recent" initialReports={initialReports} />;
}
~~~

这段代码把同一次操作拆成两个可见结果：`setSort("oldest")` 请求一次新 render，下一次提交就可见本地 April、May 顺序，不必等网络；Effect 的结果再替换数据并改变确认状态。完整应用应由路由把排序写入一条新历史项，并在 `popstate` 时把当前 URL 恢复到 React 状态；本例聚焦更新轮次，省略这层集成。不要用替换当前历史项的写法代替新筛选历史项，否则用户无法按 Back 返回 `recent`。手写 Effect 只演示提交后的同步和旧结果防护。

`requestId` 初始为 `0`，让首屏沿用服务器已经给出的 May、April，并跳过 `recent` 请求；它也作为 Effect 的依赖之一，但响应回调不会比较这个编号。旧请求失效的门槛是对应 Effect 已运行 cleanup：cleanup 把自己的 `ignore` 设为 `true`，后续 Promise 即使返回也不会写 state。这个清理不会取消网络请求；当完整路由、另一排序控件或浏览器后退让排序再次变化时，新一轮 Effect 会清理旧闭包并请求当前值。请求失败时，界面保留已有数据并把失败显示出来，而不是把本地排序误称为服务端已确认。

## 渲染、协调与提交是不同工作

render 阶段调用组件，得到当前状态对应的 JSX 元素描述。渲染应保持纯净，因为 React 可能重试或放弃尚未提交的工作；不要在组件函数里改 DOM、写 URL、发请求或直接调用 setter。若下一状态依赖前一状态，用 updater（更新函数）让排队更新逐个读取队列中的值：

~~~jsx
setCount(count + 1);
setCount(count + 1);
~~~

如果这两次 setter 在同一个处理器中运行，都会从当前 render 的 `count` 快照计算，所以只加一。若下一次更新要基于队列中刚排入的值，使用 updater：

~~~jsx
setCount(value => value + 1);
setCount(value => value + 1);
~~~

React 18 的 `createRoot` 把自动批处理扩展到 Promise、定时器和原生事件回调，因此这里一个 Promise 成功回调中的 `setReports` 与 `setStatus` 会作为同一批更新处理；旧 `ReactDOM.render` 根的自动批处理范围较窄。

reconciliation（协调）用树位置、元素类型和同级 key 将前后两次描述对应起来。上例的 `report.id` 是稳定身份；排序变动时，React 可以把既有行对应到新位置。若用数组索引作 key，插入或重排后行内输入状态可能跟着位置而不是报表走。key 只需在同级列表中唯一。

commit 阶段才把已完成结果写到宿主树。render 调用组件不等于每次都会改 DOM；若行顺序变化，React 只提交所需宿主改动。之后浏览器是否布局、绘制以及何时呈现到帧上，由浏览器渲染阶段决定，不与每个 setter 一一对应。

> [!example] JSX描述界面，不是HTML字符串
> JSX 是 JavaScript 中描述元素的语法。构建配置可将它转换为自动 JSX runtime 的 `react/jsx-runtime` 调用，也可使用经典的 `React.createElement` 形式；转换方式不会改变上面的 state、render 和 commit 关系。

## Effect在提交后同步外部系统

Effect 用于让已提交的组件与 React 之外的系统保持一致，例如订阅事件、连接服务或发送请求。依赖变化后的顺序是：先用旧值执行 cleanup，再用新值 setup；卸载时执行最后一次 cleanup。Effect 在 commit 后运行，但 React 不保证它总在浏览器 paint 之后运行；具体帧边界仍由[浏览器主线](../runtime/event-loop.md)说明。没有外部系统要同步时，派生排序数组应直接在 render 里算，不要为了它再加一个 Effect 和 state。

开发环境在根组件开启 StrictMode（严格模式）时，React 可在首挂载额外执行一次 setup 与 cleanup 来暴露不完整的清理逻辑。此例首轮 Effect 因 `requestId === 0` 直接返回，不会因此发出重复请求；这项检查不代表生产中每个请求都会重复。手写 Effect 获取数据时要清理或忽略已经失效的响应；若要缓存、去重、刷新和更新服务端数据，接着读[React如何维护服务端数据与乐观更新？](./react-server-state-and-optimistic-updates.md)。

类组件的 `render` 同样要纯净；`getSnapshotBeforeUpdate` 在 DOM 变更前读取快照，`componentDidMount`、`componentDidUpdate` 和 `componentWillUnmount` 过去常承接外部同步与清理。函数组件 Effect 有自己的 setup/cleanup 生命周期，不能把每个类方法简单替换成同名 Hook。渲染失败的恢复由[React错误边界章节](./react-error-boundaries.md)负责；路由和 SPA/MPA 的完整边界见[React路由如何把 URL 映射到视图？](./react-routing-and-navigation.md)。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 状态是快照、setter 请求下一次 render、updater 按队列应用：React 官方 [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)，核验日期 2026-11-06。
> - React 18 `createRoot` 将自动批处理扩展到 Promise、定时器和原生事件回调：[React 18 — Automatic Batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)，React 团队，2022-03-29。
> - render/commit 以及状态保留由类型、位置和 key 决定：[Render and Commit](https://react.dev/learn/render-and-commit)、[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 19.3 文档。
> - Effect 在 commit 后 setup、依赖改变时先 cleanup 再 setup、StrictMode 根边界的开发检查及过期 fetch 响应处理：[useEffect](https://react.dev/reference/react/useEffect)、[StrictMode](https://react.dev/reference/react/StrictMode#enabling-strict-mode-for-a-part-of-the-app)、[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3 文档。
> - 自动/经典 JSX runtime 的转换边界：[Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform)，React 团队，2020-09-22。
> - URL 修改当前历史项的标准语义：[HTML Standard, History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，核验日期 2026-11-06。
> - URI 片段只在客户端用于定位，不属于发给服务端的请求：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
