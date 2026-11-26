# React 怎样把一次用户操作变成界面更新？

本章回答：用户点一下按钮，React 怎样从这次点击算出新界面、写进 DOM，再让请求结果落回正确的那一轮界面。读者已经知道浏览器怎样把点击派发给处理器、怎样在渲染机会里重算样式和布局；这里接手的是处理器调用 setter 之后，React 自己做的工作。

**案例。** 沿用主线一的报表页 `/reports/42?sort=recent#summary`：服务端按 `sort=recent` 给出 May、April 两行，页面上有“最近优先”和“最早优先”两个排序按钮，用 `aria-pressed` 标出当前选择。本章用 React 实现排序控件和列表，新增这些标识符：排序状态 `sort`（`"recent"` 或 `"oldest"`）、请求编号 `requestId`、最近一次成功结果 `lastSuccess`、最近一次失败 `lastFailure`，以及路由传入的数据层函数 `fetchReports(sort)`。用户点“最早优先”后，界面先用手头的两行在本地排成 April、May，再向服务端确认；若用户很快又点回“最近优先”，旧请求不能把新选择标成已确认。代码里的数据和接口都是教学用的合成示例；行为按 React 19.3 与 React DOM 19.3 核对。URL 和历史栈怎样跟着排序变化，见[地址变了，浏览器什么时候加载新文档？](../browser/navigation-history-and-url-state.md)。

## 一次点击走过哪几步

先看点击后没有再次切换的一轮。React 把工作分成几段，每段只做一件事；下图按时间画出每段由谁执行、交给下一段什么：

~~~mermaid
%%{init: {"sequence": {"mirrorActors": false, "actorMargin": 30, "width": 130}}}%%
sequenceDiagram
  participant H as 事件处理器
  participant R as React render
  participant C as React commit
  participant B as 浏览器
  participant E as Effect
  Note over H: 用户点“最早优先”
  H->>R: 同一批排入<br/>sort = "oldest"<br/>requestId = 1
  Note over H: 处理器里的 sort<br/>仍是 "recent"
  Note over R: 调用组件<br/>派生 April、May<br/>提示“等待请求 #35;1”<br/>不发请求、不碰 DOM
  R->>C: 协调出的必要改动
  Note over C: 写 aria-pressed<br/>移动两行<br/>改提示文字
  par 浏览器绘制
    C-)B: DOM 已是新顺序
    Note over B: 之后的渲染机会<br/>样式、布局、绘制
  and Effect：与 paint 的先后不保证
    C->>E: commit 后运行 setup
    Note over E: fetchReports<br/>("oldest")<br/>等响应或失败
  end
  E->>R: 响应回调排入编号 1 的<br/>成功或失败结果
  Note over R,C: 再走一轮 render 和 commit<br/>显示“已确认”或报错
~~~

事件处理器、Effect 和响应回调是你的代码，render 和 commit 由 React 执行，paint 归浏览器。下面各节依次解释：处理器为什么读到旧值，render、commit 和 paint 为什么是三件事，React 靠什么把前后两次的行对上，副作用该放在哪一段，以及迟到的响应怎样不写错界面。

## 处理器读到的是这一轮的状态快照

React 每次调用组件，都给它一份当前状态的快照；事件处理器是在某一轮 render 里创建的函数，闭包里拿到的就是那一轮的值。setter (状态更新函数)不会原地改写这份快照，它只是向 React 排入一个更新，请求下一轮 render。所以本例的 `chooseSort` 在 `sort` 为 `"recent"` 时调用 `setSort("oldest")`，这个处理器接下来读到的 `sort` 还是 `"recent"`。

同一个处理器连续调用两次 `setCount(count + 1)`，两次都基于快照里的 `0` 排入 `1`，结果是 `1`。要让每一步基于队列里上一步的结果，就传 updater (更新函数)：

~~~tsx
const [count, setCount] = useState(0);

function addFromSnapshot() {
  setCount(count + 1); // 排入 0 + 1
  setCount(count + 1); // 仍排入 0 + 1，结果是 1
}

function addFromQueue() {
  setCount(n => n + 1); // 0 → 1
  setCount(n => n + 1); // 1 → 2，结果是 2
}
~~~

本例的 `setRequestId(id => id + 1)` 用 updater，让编号从队列里的待处理值继续递增。

React 用 `Object.is` 比较新旧状态。传给 setter 的值与当前状态是同一个引用时，React 可以跳过这个组件及其子树的重新渲染。原地修改对象再把它传回 setter 就会撞上这一点：例如 lodash 的 `_.merge(cached, patch)` 返回的就是被改过的 `cached` 本身，`setReports(_.merge(cached, patch))` 交给 React 的引用没变，界面可能不更新，而共享这个对象的缓存和其他组件却已经看到了改动。更新状态时要建立新对象；哪些方法原地修改、怎样复制，见[复制一个对象到底复制了什么？](../javascript/copying-and-object-graphs.md)。`Object.is` 本身的规则见[JavaScript 的值有哪些类型，“相等”又有几种？](../javascript/values-types-and-equality.md)。

## render、commit 和 paint 是三件事

**是否调用组件、是否改 DOM、浏览器是否重新绘制，是三个独立的问题。** React 负责前两段，浏览器负责第三段。

**render** 是计算。React 调用组件，把当前 props 和 state 变成 JSX 元素描述。JSX 是描述元素的语法，构建工具把它编译成 `react/jsx-runtime` 的调用（旧的经典转换编译成 `React.createElement`），转换方式不影响本章的阶段划分。并发特性下，一次尚未提交的 render 可能被暂停、重来或整个放弃，所以 render 必须是纯计算：不发请求，不写 URL，不改已有对象，也不手动改 React 管理的 DOM。

render 时 React 还要做 reconciliation (协调)：把新描述和上一次的描述逐个对应起来，算出哪些宿主节点要新建、移动、更新或删除。对应规则由树中位置、元素类型和 `key` 决定，见下一节。

**commit** 是写入。React 把协调出的必要改动应用到宿主树（浏览器里就是 DOM）。一个 setter 不等于一次 DOM 修改：新旧描述相同，React 就不改 DOM。

**paint** 是浏览器的事。commit 结束时 DOM 已经是新顺序，用户看到它却要等之后的渲染机会。React 的 setter、render 次数和浏览器帧之间没有一一对应。浏览器怎样安排渲染机会，见[事件循环怎样安排任务、微任务和渲染？](../browser/event-loop-tasks-and-rendering.md)；DOM 改动后浏览器重做了哪些工作，见[DOM 改动后浏览器重做了什么？](../browser/rendering-pipeline-and-forced-layout.md)。

### 批处理：同一批更新只走一轮

React 把同一批的多个状态更新合起来处理，只做一轮 render 和 commit，这叫 batching (批处理)。本例点击处理器同时排入 `sort` 和 `requestId`，React 不会先提交一个只改了排序的半成品，再提交一个只改了编号的版本。批处理不改变当前处理器的快照，也不意味着每次 commit 都单独绘制一帧。

> [!info] 版本差异：批处理的范围
> React 18 起，用 `createRoot` 创建的根会自动批处理所有更新，包括 Promise 回调、定时器和原生事件处理器里的更新。React 18 中仍用旧 `ReactDOM.render` 创建的根只在 React 事件处理器内批处理，换成 `createRoot` 才启用新行为。React 19 已移除 `ReactDOM.render`。

## key 决定状态属于谁

协调时，React 先按树中的位置和元素类型判断“这还是不是同一个组件”。位置相同、类型相同，组件就被保留，它的 state 和对应的 DOM 节点也跟着保留；类型变了或者组件从树里移除，state 就被销毁。列表里的兄弟节点位置会变，这时靠 `key` 标识身份：React 把新旧两组兄弟中 `key` 相同的元素看作同一个组件。

**用业务 ID 作 key。** 本例每一行都有服务端给的稳定 ID：May 是 `r-104`，April 是 `r-103`，列表写成 `<li key={report.id}>`。排序从 May、April 变成 April、May 时，两行的 ID 不变，React 就移动原有的两个节点，而不是在原位置上改写内容。`key` 只需在同一列表的兄弟之间唯一且稳定，不必全局唯一。

**用数组下标作 key 会让状态跟着位置走。** 设想每行有一个保存局部输入的子组件：May 行输入了“检查空名称”，April 行输入了“核对响应码”。现在在列表顶部插入一条草稿：

| key 方案 | 插入后位置 0 | 位置 1 | 位置 2 |
| --- | --- | --- | --- |
| 下标 `key={index}` | 草稿，却带着 May 的“检查空名称” | May，却带着 April 的“核对响应码” | April，输入为空 |
| 业务 ID `key={row.id}` | 草稿，输入为空 | May，“检查空名称” | April，“核对响应码” |

下标方案里，key `0` 在插入前后都存在，React 认为它还是原来那个组件，于是把 May 的局部状态交给了草稿。焦点和未受控输入框的值也会这样错位。新增的草稿行没有服务端 ID 时，在创建它的事件处理器里生成一次 ID（例如 `draft:${crypto.randomUUID()}`），之后一直使用；不要在 render 里每次生成新 ID，那样每轮都会让该行重新挂载。

**换 key 就是有意重置。** 同一位置上的组件换了 `key`，React 会销毁旧组件、挂载新组件，所有 state 从头初始化。这是丢弃一整块状态的标准做法：切换账户时写 `<ReportsPage key={accountId} … />`，旧账户的成功数据、等待状态和失败记录就不会留到新账户下。反过来，组件一旦被卸载（例如路由离开了整个列表），key 也保不住其中的状态，需要由更高层的所有者保存，见[一份界面状态该由谁持有？](./state-ownership-and-composition.md)。

> [!info]- 实例：ahooks `useDynamicList` 在开发 StrictMode 下的 key 漂移（ahooks v3.11.0，React 19.3.1 本地实测）
> `useDynamicList` 管理可增删的列表，文档把它的 `getKey(index)` 描述为可保持列表项身份的 key。但在 React 19.3.1 开发 StrictMode 下，初始化和 `insert(0, draft)` 都会让其内部 key ref 重复递增：插入前是 `[May:2, April:3]`，插入后是 `[Draft:5, May:4, April:2]`，May 和 April 的 key 都变了。这是该版本组合下的实测结果，不是 React 的 key 契约。维护依赖 `getKey` 的代码时，应在实际版本和 StrictMode 配置下测试插入、移动和重置；新代码直接用业务 ID 和一次生成的草稿 ID 更稳。同一 Hook 的 `merge(index, items)` 是在指定位置插入多项，不是 lodash 式的对象深合并；`sortList` 只剔除 `null` 和 `undefined`，保留 `0`、`false` 和空字符串。

## 事件、render、Effect 各放什么

三类工作各有位置：

- **由用户这次动作直接触发的一次性工作，放在事件处理器里。** 本例记录新的排序选择和请求编号。
- **能从 props 和 state 算出来的值，在 render 里算。** 本例从 `lastSuccess.reports` 和当前 `sort` 派生可见行。把派生结果再存进一份 state、用 Effect 去同步，会多一轮不必要的更新，还可能短暂显示不一致的中间态。
- **需要跟着已提交界面去同步外部系统的工作，放进 Effect。** 本例按已提交的排序向服务端读取数据。订阅、连接、计时器也属于这一类。

下面是组件的状态和处理器。类型定义、排序函数和首屏数据放在折叠块里；`initialReports` 代表路由已经取得并校验过的首屏数据。

> [!info]- 类型、排序函数与首屏数据
>
> ~~~tsx
> import { useEffect, useState } from "react";
>
> type SortOrder = "recent" | "oldest";
> type Report = { id: string; period: string; periodStart: string; title: string };
> type FetchReports = (sort: SortOrder) => Promise<Report[]>;
> type SuccessfulRequest = { requestId: number; sort: SortOrder; reports: Report[] };
> type FailedRequest = { requestId: number; sort: SortOrder };
>
> const initialReports: Report[] = [
>   { id: "r-104", period: "May", periodStart: "2026-05-01", title: "May report" },
>   { id: "r-103", period: "April", periodStart: "2026-04-01", title: "April report" }
> ];
>
> // periodStart 固定为 YYYY-MM-DD，可按字符串比较；period 只作显示标签。
> // 复制后排序，不改写上游数组。
> function sortReports(reports: Report[], sort: SortOrder): Report[] {
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
> ~~~

~~~tsx
function ReportsPage({
  initialSort,
  initialReports,
  fetchReports
}: {
  initialSort: SortOrder;
  initialReports: Report[];
  fetchReports: FetchReports;
}) {
  const [sort, setSort] = useState(initialSort);
  const [requestId, setRequestId] = useState(0);
  const [lastSuccess, setLastSuccess] = useState<SuccessfulRequest>({
    requestId: 0,
    sort: initialSort,
    reports: initialReports
  });
  const [lastFailure, setLastFailure] = useState<FailedRequest | null>(null);

  function chooseSort(nextSort: SortOrder) {
    if (nextSort === sort) return;
    setSort(nextSort);
    setRequestId(id => id + 1);
  }
  // 下接 Effect、派生值和 JSX
~~~

处理器只排入新选择和新编号，既没有发请求，也没有直接挪动列表节点。路由以 `<ReportsPage initialSort="recent" initialReports={initialReports} fetchReports={fetchReports} />` 传入首屏输入；`useState` 只在首次挂载时读取这两个初始值，之后再改这两个 prop 不会重置状态，原因和处理办法见[一份界面状态该由谁持有？](./state-ownership-and-composition.md)。

## Effect 怎样跟随已提交的选择，又怎样拒绝过期结果

### Effect 的生命周期

Effect 由“组件现在需要和外部系统保持一致”触发，而不是由某次点击触发。React 在 commit 之后运行它的 setup (建立)；依赖变化时，先用旧闭包运行上一次返回的 cleanup (清理)，再用新值运行新的 setup；组件卸载时运行最后一次 cleanup。依赖数组要列出 setup 实际读取的所有响应式值，React 用 `Object.is` 逐个比较。

本例依赖 `sort`、`requestId` 和 `fetchReports`。`fetchReports` 在依赖里，所以路由要传入一个稳定的函数；若父组件每轮 render 都新建这个函数，Effect 会把它当作依赖变化而重新请求。`fetchReports` 内部若读取原始 JSON，应先在数据边界校验形状，而不是只靠 TypeScript 类型断言，见[TypeScript 能保证什么，外部数据又该怎样验证？](../javascript/typescript-guarantees-and-runtime-validation.md)。

React 不保证 Effect 总在浏览器绘制之后运行：由点击等交互引起的 Effect 可能在 paint 之前运行，其他更新通常让浏览器先绘制。需要在绘制前测量或调整 DOM 时，用 `useLayoutEffect`；本例只是发请求，不依赖精确的帧时机。

### 用请求编号和清理标记守住结果

一个 Effect 属于某一次已提交的选择。它把当时的 `requestId` 和 `sort` 附在结果上，再用局部变量 `ignore` 记录自己是否已被清理。首屏 `requestId=0` 已有路由数据，直接跳过。

~~~tsx
  useEffect(() => {
    if (requestId === 0) return;

    let ignore = false;
    const currentRequestId = requestId;

    fetchReports(sort).then(
      reports => {
        if (!ignore) setLastSuccess({ requestId: currentRequestId, sort, reports });
      },
      () => {
        if (!ignore) setLastFailure({ requestId: currentRequestId, sort });
      }
    );

    return () => {
      ignore = true;
    };
  }, [sort, requestId, fetchReports]);
~~~

两道守卫各管一件事。`ignore` 让已被清理的 Effect 不再写状态；结果上附带的编号保证：即使旧回调抢在 cleanup 之前运行，它也只能写入自己的编号，不能把后来的请求标成已确认。

现在走一遍快速反选：请求 `1`（oldest）还没结束，用户又点“最近优先”。commit 之后，React 先运行 Effect 1 的 cleanup，再运行 Effect 2 的 setup；请求 `1` 的回调可能落在 cleanup 之前或之后，下图的 `alt` 画出这两种结局：

~~~mermaid
%%{init: {"sequence": {"mirrorActors": false, "actorMargin": 24, "width": 110}}}%%
sequenceDiagram
  participant RC as React render<br/>与 commit
  participant E1 as Effect 1<br/>（oldest）
  participant E2 as Effect 2<br/>（recent）
  participant S as 服务端
  participant L as lastSuccess
  Note over E1: setup<br/>ignore = false<br/>currentRequestId = 1
  E1->>S: 请求 1<br/>fetchReports("oldest")
  Note over RC: 处理器：用户点“最近优先”<br/>排入 sort = "recent"<br/>requestId = 2
  Note over RC: render 从当前 lastSuccess<br/>派生 May、April<br/>提示等待请求 2<br/>commit 写入 DOM
  alt 请求 1 的回调在 cleanup 之前执行
    S-->>E1: 请求 1 成功，回调运行<br/>ignore 仍是 false
    E1->>L: 写入 requestId = 1<br/>sort = "oldest" 和这批 reports
    RC->>E1: cleanup：ignore = true
    RC->>E2: setup：发出请求 2
    Note over L: 1 ≠ 2<br/>这批数据按 recent<br/>排序显示，仍提示<br/>等待请求 2
  else 回调在 cleanup 之后执行
    RC->>E1: cleanup：ignore = true
    RC->>E2: setup：发出请求 2
    S-->>E1: 请求 1 的回调运行<br/>ignore 已是 true，什么也不写
    Note over L: 原 lastSuccess<br/>不变，按 recent<br/>排序，仍提示<br/>等待请求 2
  end
  E2->>S: 请求 2<br/>fetchReports("recent")
~~~

这里比较的是回调实际执行的时刻：Promise 早已完成，不代表排队的回调已经在 cleanup 前执行。两种结局里界面都还在等请求 `2`：前一种 `ignore` 没拦住，但编号让写入只算请求 `1` 的成功。

失败回调同理：cleanup 之前执行时，它只记下编号 `1` 的失败，不改 `lastSuccess`，也不能把请求 `2` 标成失败；cleanup 之后执行则被忽略。

cleanup 守卫的含义是“React 清理这个 Effect 后，不再采用它的结果”，不是取消网络请求，请求本身可能继续跑完。要真正停止传输，要把 `AbortSignal` 传给 `fetch` 并在 cleanup 里中止；即便如此，中止也不撤销服务端已经执行的副作用，见[取消、超时和并发上限各自停得住什么？](../javascript/cancellation-timeouts-and-concurrency.md)。

请求编号只在同一个数据域里区分轮次，不隔离界面正在显示的数据。切换账户时只递增编号，`lastSuccess.reports` 里旧账户的行仍会在等待和失败时显示出来；应按上一节的做法用 `key={accountId}` 重新挂载。这里的“给每个异步结果附上它所属的身份，只让匹配当前身份的结果落到界面上”是前端处理乱序结果的共同原理。Redux 的 `meta.requestId`、编辑会话的提交编号、查询缓存的 query key 都是同一思路，汇总见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](./server-state-and-optimistic-updates.md)；生产应用需要缓存、去重、取消和重试时，通常交给路由数据层或查询库。

## 成功和失败分开存，界面才说得清

本例把最近一次成功的数据和最近一次失败分开存。这样当前请求失败时，列表仍有可显示的数据，提示又能说明这份数据还没被本次请求确认。每轮 render 从状态算出三个值：

~~~tsx
  const requestConfirmed =
    lastSuccess.requestId === requestId && lastSuccess.sort === sort;
  const requestFailed =
    lastFailure !== null &&
    lastFailure.requestId === requestId &&
    lastFailure.sort === sort;
  const visibleReports = sortReports(lastSuccess.reports, sort);
~~~

| 当前状态 | 提示 | 列表数据 |
| --- | --- | --- |
| 有与当前编号和排序匹配的失败 | `role="alert"`：当前请求失败 | 最近成功的数据，按当前选择排序 |
| 否则，成功结果与当前编号和排序匹配 | `role="status"`：服务端已确认 | 本次成功的数据 |
| 其余情况 | `role="status"`：等待当前请求 | 最近成功的数据，按当前选择排序 |

失败时界面保留同一数据域里最近成功的数据并按当前选择排序，但不会把它说成服务端刚确认的结果。首屏 `requestId=0` 时，`lastSuccess` 就是路由给的数据，三个条件里第二条成立。

> [!example]- 组件的 JSX 部分（接在上面的派生值之后）
>
> ~~~tsx
>   return (
>     <section>
>       <div role="group" aria-label="报表排序">
>         <button type="button" aria-pressed={sort === "recent"} onClick={() => chooseSort("recent")}>
>           最近优先
>         </button>
>         <button type="button" aria-pressed={sort === "oldest"} onClick={() => chooseSort("oldest")}>
>           最早优先
>         </button>
>       </div>
>
>       {requestFailed ? (
>         <p role="alert">
>           {`当前选择：${sort}；请求 #${requestId} 失败。仍显示上次成功（${lastSuccess.sort}）的数据，并按当前选择排序。`}
>         </p>
>       ) : requestConfirmed ? (
>         <p role="status">{`服务端已确认当前选择：${sort}（请求 #${requestId}）。`}</p>
>       ) : (
>         <p role="status">
>           {`当前选择：${sort}；等待请求 #${requestId}。下方是上次成功（${lastSuccess.sort}）的数据，已按当前选择排序。`}
>         </p>
>       )}
>
>       <ol>
>         {visibleReports.map(report => (
>           <li key={report.id}>{report.period} — {report.title}</li>
>         ))}
>       </ol>
>     </section>
>   );
> }
> ~~~

## StrictMode 在开发环境里故意多调用一次

根组件包在 `StrictMode` (严格模式)里时，React 在开发环境做两类额外调用，用来暴露不纯的代码：

- **组件函数、`useState` 初始化函数和 updater 各多调用一次**，结果丢弃其中一次。render 若有副作用（例如改了外部对象），重复调用会让问题显形。
- **每个 Effect 在首次挂载时多走一遍 setup → cleanup**，再正式 setup。cleanup 若没能撤销 setup 的工作（例如没退订、没清计时器），这一步会暴露出来。

生产环境不做这些额外调用。本例初次挂载时 `requestId=0` 直接返回，既不发请求也没有 cleanup；之后每次排序都会建立带 cleanup 的 Effect。首次加载时不可逆的动作（例如写入一条不该重复的记录）不应放在挂载 Effect 里，ahooks 的 `useMount` 这类封装也只是 Effect 的建立与清理，同样会被 StrictMode 多跑一遍。

## 长期回调怎样读到最新值

有时一个长期存在的回调（例如注册一次的事件监听或计时器）需要读到最新的 props 或 state，却不想因为值变了就重建它。常见做法是把最新值放进 ref，但写 ref 的时机决定读到的是什么。

> [!info] 实例：ahooks `useLatest` 与 `useMemoizedFn`（ahooks v3.11.0）
> `useLatest(value)` 返回一个 ref，实现是在每次 render 期间直接执行 `ref.current = value`。`useMemoizedFn(fn)` 返回一个身份稳定的包装函数，同样在 render 期间把新的 `fn` 写进内部 ref；它解决的是函数身份变化的问题，`useLatest` 解决的是读值的问题。

React 要求不要在 render 中读写 ref，原因就在 render 和 commit 的分离：并发渲染下，一次 render 可能被中断并最终放弃，而 render 期间写进 ref 的值已经留下了。回调随后读到的可能是一个从未提交到屏幕上的值。所以 `useLatest` 给的是“最近一次 render 的值”，不是“最近一次已提交的值”；`useMemoizedFn` 调用的也可能是被放弃那轮 render 的函数体。这个结论是从实现代码和 React 的渲染规则推出来的。

如果这段逻辑只在 Effect 里调用，React 19.2 起可以用 `useEffectEvent`：它返回的函数在调用时读取最新已提交的 props 和 state，又不必列进 Effect 依赖，不会让连接、订阅等 Effect 因此重建。它的边界很窄：只能在定义它的组件或自定义 Hook 里、由本地 Effect 或另一个 Effect Event 调用；不能当普通点击回调，不能传给子组件，也不能用来隐藏本该声明的依赖。它的函数身份每轮 render 都会变，不要放进依赖数组。事件处理器本来就在每轮 render 里重新创建，直接读当轮的快照即可，不需要这类工具。

## 类组件的生命周期对照

维护旧代码时会遇到 class component (类组件)。它的 `render()` 同样必须是纯计算。`componentDidMount` 和 `componentDidUpdate` 在 DOM 提交后运行，可用来同步外部系统；`componentWillUnmount` 负责清理；需要在 DOM 更新前读取布局快照（例如滚动位置）时用 `getSnapshotBeforeUpdate`，它的返回值作为第三个参数交给 `componentDidUpdate`。这些方法帮助判断代码处在哪个阶段，但不与函数组件的 Effect 一一对应：一个 Effect 把建立和清理写在一起，按依赖变化成对运行，而类组件要把同一件事拆到挂载、更新、卸载三个方法里自己对齐。React 仍支持类组件，新组件通常写成函数组件。错误边界目前仍只能用类组件实现，见[错误发生在哪里，决定了谁能接住它？](./react-error-boundaries.md)。

## sort 之外的状态该放在哪？

到这里，一次点击在 React 里的路径是完整的：处理器排入更新，render 从快照算出描述，协调按位置、类型和 `key` 把新旧描述对上，commit 写进 DOM，浏览器再绘制；Effect 在 commit 后跟随已提交的选择去同步外部系统，用身份标记拒绝过期结果。本章默认 `sort` 就放在 `ReportsPage` 里。可报表页里还有 URL、查询缓存、勾选的行和编辑抽屉里的草稿，这些状态分别该由谁持有、什么时候要上提或进 store，是[一份界面状态该由谁持有？](./state-ownership-and-composition.md)要回答的问题。若一次排序让输入变慢，见[昂贵更新时，怎样让输入保持即时？](./urgent-and-deferred-updates.md)；若要测量和减少 render 工作，见[React 渲染慢时，先改什么？](../delivery/react-rendering-optimization.md)。

> [!info]- 来源
>
> - 状态快照、setter 请求下一轮 render、updater 按队列计算、`Object.is` 相同时跳过渲染（“处理器读到的是这一轮的状态快照”）：[State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)、[`useState`](https://react.dev/reference/react/useState)，React 19.3 文档，核对 2026-11-12。
> - `_.merge` 原地修改并返回目标对象（同上节 lodash 例）：[Lodash 4.18.1 API 文档](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md)，核对 2026-11-12。
> - render/commit 分工、render 纯净、组件调用不必对应 DOM 改动、浏览器绘制是之后的一步（“render、commit 和 paint 是三件事”）：[Render and Commit](https://react.dev/learn/render-and-commit)、[Keeping Components Pure](https://react.dev/learn/keeping-components-pure)，React 19.3 文档。
> - 并发 render 可中断、恢复、放弃并整树提交；自动批处理；`createRoot` 与旧 `ReactDOM.render` 的边界（“批处理”）：[React v18 — What Is Concurrent React?](https://react.dev/blog/2022/03/29/react-v18#what-is-concurrent-react)、[React v18 — Automatic Batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching)、[How to Upgrade to React 18 — Client Rendering APIs](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#updates-to-client-rendering-apis)，React 团队。
> - JSX 自动与经典转换：[Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform)，React 团队，2020-09-22。
> - 位置、类型与 key 决定状态保留，换 key 重置状态（“key 决定状态属于谁”）：[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)（含 Option 2: Resetting state with a key）、[Rendering Lists — Keeping list items in order with key](https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key)，React 19.3 文档。
> - `useDynamicList` 的 key 契约、操作与 `sortList`（`useDynamicList` 实例）：[useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list/)、[v3.11.0 源码](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useDynamicList/index.ts)、[v3.11.0 release](https://github.com/alibaba/hooks/releases/tag/v3.11.0)；开发 StrictMode 下的 key 漂移是 2026-11-12 以 React 19.3.1、ahooks 3.11.0、jsdom 26.1.0 的本地重放结果，不作为通用 API 语义。
> - Effect 与事件的触发来源、依赖比较、cleanup 再 setup、Effect 相对 paint 的时序、忽略过期 fetch 结果的模式（“Effect 怎样跟随已提交的选择”）：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)、[You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)、[`useEffect`](https://react.dev/reference/react/useEffect)、[`useLayoutEffect`](https://react.dev/reference/react/useLayoutEffect)，React 19.3 文档。
> - StrictMode 的开发期额外 render 与 Effect setup/cleanup（“StrictMode”）：[StrictMode](https://react.dev/reference/react/StrictMode)，React 19.3 文档；`useMount`/`useUnmount` 的用途：[useMount](https://ahooks.js.org/hooks/use-mount/)、[useUnmount](https://ahooks.js.org/hooks/use-unmount/)，核对 2026-11-06。
> - `useLatest`、`useMemoizedFn` 在 render 期写 ref（“长期回调怎样读到最新值”）：[v3.11.0 useLatest](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useLatest/index.ts)、[v3.11.0 useMemoizedFn](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useMemoizedFn/index.ts)；不在 render 中读写 ref：[`useRef` caveats](https://react.dev/reference/react/useRef#caveats)；Effect Event 读最新已提交值与调用边界：[`useEffectEvent`](https://react.dev/reference/react/useEffectEvent)、[React 19.2](https://react.dev/blog/2025/10/01/react-19-2)，核对 2026-11-12。
> - 类组件 `render`、mount/update/unmount 生命周期与 `getSnapshotBeforeUpdate`（“类组件的生命周期对照”）：[Component](https://react.dev/reference/react/Component)，React 19.3 文档。
> - 当前 React 文档版本：[Versions](https://react.dev/versions)，React 19.3，核对 2026-11-12。
