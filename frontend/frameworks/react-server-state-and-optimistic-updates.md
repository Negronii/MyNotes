# React界面如何维护服务端数据与乐观更新的正确性？

**案例背景。** 报表路由当前账户为 `acct-a`，地址是 `/reports?sort=recent#summary`，服务端给出 May、April 两行。点击 **Oldest first** 后，路由把 `sort` 推入浏览器历史，当前排序变为 April、May；此时 UI（界面）可以先把手头同一账户的完整记录在本地重排，再等待对应查询返回服务端的确认结果。报表归服务端所有，TanStack Query（服务端数据查询与缓存库）的查询缓存只是客户端副本。账户 ID 和会改变结果的筛选条件都属于查询身份：切到 `acct-b` 时，查询键随账户改变；若没有 B 账户的路由行或缓存，就先显示等待或空状态，绝不能把 A 账户的行当作 B 的结果。下文的“路由行”指路由随页面一起交付的初始报表行。

浏览器请求会带路径和 `?sort=recent`，不会带 `#summary`；片段只供客户端定位。地址栏、前进/后退与查询状态如何连接由[浏览器导航路径](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)负责。本例组件只接收路由解析出的 `accountId`、当前 `sort`、与之匹配的初始数据和排序回调；`pushState`、`popstate` 订阅和路由库由调用方实现。使用 `useQuery` 的组件还须位于 `<QueryClientProvider>` 之下，读取和保存函数由应用的网络适配器提供；示例不包含这些接线。

## 排序值构成查询身份

`queryKey`（查询键）标识 `queryFn`（查询函数）将取回的那份结果。这里的响应取决于 `accountId` 和 `sort`，所以两者都在 key 中；同一账户的各排序列表共用一个前缀，失效时可以只刷新该账户的列表。若再增加会改变记录集合的过滤条件或页码，也要把它们加入 key。

| 阶段 | 当前身份 | 列表与提示 |
| --- | --- | --- |
| 初始路由 | `['reports', 'acct-a', 'list', 'recent']` | 路由给出的 May、April 只作为这个账户与排序的初始缓存；`initialData` 可直接显示。 |
| 点击 Oldest first | URL/路由状态先变为 `sort='oldest'`；key 变为 `['reports', 'acct-a', 'list', 'oldest']` | 若这个 key 没有缓存，请求等待期间只把同账户、同一完整记录集合的路由行在本地排成 April、May；这批行不是该 key 的服务端确认结果，行内操作保持禁用。 |
| Oldest 响应到达 | 只更新 `acct-a/oldest` | 列表换成该 key 的服务端数据。先前 `recent` 的请求即使随后完成，也只会写入 `recent` key；若 query function 读取了取消信号，离开该 key 时请求还可能被取消。 |
| 切换到账户 B | `['reports', 'acct-b', 'list', sort]` | key 与页面身份都含账户。若没有 B 的路由行或缓存，先等待或显示空状态，不能把 A 账户的 May、April 当作 B 的数据。 |

路由把当前 URL 的排序解析为 `sort`，调用方提供的 `onSortChange` 负责用 `pushState` 新增历史项；浏览器 Back 产生 `popstate` 后，调用方把旧 `sort` 传回，查询 key 随之切回。本例只消费这些路由输入和回调，不实现上述 History API 逻辑。这里保留 `#summary` 只是说明它不参与服务器请求或 query key；只有客户端明确把片段映射为请求参数时，映射后的值才成为查询输入。

路由行只作为 `initialAccountId`、`initialSort` 所对应查询的 `initialData`（初始数据）；其他排序或账户的查询不使用这份数据。TanStack Query v5 会把 `initialData` 写入查询缓存，并按新鲜度策略处理；若路由还给出这批数据的生成时间，就以 JavaScript 毫秒时间戳传给 `initialDataUpdatedAt`，否则客户端会把初始化时刻当成数据时间。30 秒的 `staleTime`（新鲜期）只表示客户端在这段时间内不按过期策略自动重取，并不保证服务器数据没变；手动失效仍可强制重新读取。

`placeholderData`（占位数据）用途不同：它不写入 cache，查询结果带 `isPlaceholderData` 标记。若为了让排序切换更平滑而复用上一个 key 的行，应先确认上一个 key 的账户仍是当前账户，并在界面上标明这些行尚未得到新排序的服务端确认；绝不能拿其他账户的数据作占位。本文主示例不用这个选项，而是在数据成员完全相同的同账户列表上做本地排序。

本文使用普通 TanStack Query v5 `useQuery` 的状态返回路径，没有设置 `throwOnError`：请求失败保存在 `isError`、`error`、`data` 中。若应用改为抛错配置或 Suspense 查询，失败会走不同界面路径，见[错误边界章节](./react-error-boundaries.md)。当前 key 还没有数据时，查询处于 `isPending`。失败时结合 `isError` 与 `data` 判断：没有查询数据，就显示同账户的路由行（若有）并允许重试；已有上次成功的结果，就保留它并提示刷新失败。切换排序后若该 key 已有缓存，可以先显示缓存，再按 `staleTime` 等策略在后台重新读取。

## 变更先乐观显示，再与服务端协调

读取之外，用户还会修改数据。假设 `acct-a/oldest` 已显示服务端确认的数据，用户点击 April 行的 **Mark reviewed**（标为已审阅）。点击事件把 `{ accountId: "acct-a", sort: "oldest", id: "april", reviewed: true }` 交给 mutation（服务端变更）。保存期间，TanStack Query 暴露这份待处理的变量；组件按账户、排序和行 ID 找到 April，暂时把它的 `reviewed` 显示为 `true`，而查询缓存里仍是上次服务端确认的行。这种只在界面层叠加待处理值、不改缓存的做法，下文称为 overlay（界面覆盖层）。

**保存期间：缓存行与匹配的待处理变量合成界面**

![保存期间查询缓存与待处理 mutation 变量合成界面的状态图](resources/react-server-state-overlay.svg)

上图取失败分支中的一个时刻：保存请求仍 pending 时，窗口重新获得焦点触发了一次重取（焦点重取），把服务端最新的 April、May 写入缓存；此时 May 的标题已被他人改过。下表接着展开后续时序：保存请求和 `onSettled` 发起的重取都失败，因此 cache 保留那次焦点重取的结果。

| 时点 | `acct-a/oldest` 的 query cache；匹配的 mutation variable | 界面 |
| --- | --- | --- |
| 焦点重取到达，保存仍 pending | April `reviewed=false`；May 是新标题。变量为 April `reviewed=true`。 | April 显示 `true`；May 保留新标题。 |
| 保存请求失败，`onSettled` 重取中 | cache 不变；变量仍 pending。 | April 仍显示 `true`；May 仍保留新标题。 |
| `onSettled` 重取结束 | 该重取失败，cache 保留上次成功值；pending 变量解除。 | overlay 消失，April 回到 `false`；May 新标题仍在。旧整表快照没有把列表恢复成旧值。 |

1. `submit` 先用共享的 QueryClient 检查是否已有同类保存在进行，再启动 mutation；待处理期间所有行按钮都禁用。这个示例有意限制同一时间只有一次标记操作，也不让其他调用入口绕过 `submit`。
2. 保存期间若发生后台重取，查询缓存照常接收服务器结果，界面层的待处理变量仍盖住 April 的标记。保存请求失败后，mutation 还要等 `onSettled` 触发的失效重取结束；在它退出 pending 之前，overlay 继续盖住标记。pending 结束时 overlay 消失，列表显示当时可用的查询结果或同账户的路由行，不会用旧的整表快照覆盖新结果。
3. 保存成功时，`onSuccess` 根据这次提交的 `accountId` 和 `sort` 找到原查询 key，并用服务器返回的 April 行更新缓存。`onSettled` 让该账户的整个列表前缀失效：在本例联网、活跃查询可以运行时，匹配的活跃查询会立即重取；非活跃的排序只被标为失效，等下次使用时再读取。回调返回的 Promise 完成之前，mutation 仍处于 pending。

这条成功路径假设保存后发起的列表读取能看到刚才的提交。等失效重取完成，并不等于获得 read-your-writes（读己之写）保证：若这次读取落到了落后的副本上，仍可能把已确认的新行换回旧值。这种接口需让校准读取到达权威数据源，或按服务端提供的修订号拒绝低于已确认版本的结果；仅延长 overlay 不能修复读取契约。

完整组件只使用路由 props、路由的排序回调、provider 和网络适配器，不实现 `pushState`、`popstate`，也不创建 QueryClient：

> [!example]- 报表查询与乐观更新组件（TanStack Query v5）
>
> ~~~tsx
> import {
>   useIsMutating,
>   useMutation,
>   useMutationState,
>   useQuery,
>   useQueryClient
> } from "@tanstack/react-query";
>
> type SortOrder = "recent" | "oldest";
> type Report = {
>   id: string;
>   period: string;
>   periodStart: string; // 规范化的 YYYY-MM-DD，可按字典序排序
>   title: string;
>   reviewed: boolean;
> };
>
> const reportKeys = {
>   lists: (accountId: string) =>
>     ["reports", accountId, "list"] as const,
>   list: (accountId: string, sort: SortOrder) => [
>     ...reportKeys.lists(accountId),
>     sort
>   ] as const,
>   markReviewed: () => ["reports", "mark-reviewed"] as const
> };
>
> type MarkReviewed = {
>   accountId: string;
>   sort: SortOrder;
>   id: string;
>   reviewed: boolean;
> };
>
> declare function fetchReports(
>   accountId: string,
>   sort: SortOrder,
>   signal: AbortSignal
> ): Promise<Report[]>;
> declare function saveReviewed(
>   accountId: string,
>   id: string,
>   reviewed: boolean
> ): Promise<Report>;
>
> function sortReports(reports: Report[], sort: SortOrder) {
>   return [...reports].sort((a, b) => {
>     const order = a.periodStart.localeCompare(b.periodStart);
>     return sort === "recent" ? -order : order;
>   });
> }
>
> type ReportsRouteProps = {
>   accountId: string; // 当前已登录/选中的账户
>   sort: SortOrder; // 路由从 URL 解析
>   onSortChange: (sort: SortOrder) => void; // 路由写入 pushState
>   initialAccountId: string;
>   initialSort: SortOrder;
>   initialReports: Report[];
>   initialReportsUpdatedAt: number | undefined;
> };
>
> function useReports({
>   accountId,
>   sort,
>   initialAccountId,
>   initialSort,
>   initialReports,
>   initialReportsUpdatedAt
> }: Pick<ReportsRouteProps,
>   | "accountId"
>   | "sort"
>   | "initialAccountId"
>   | "initialSort"
>   | "initialReports"
>   | "initialReportsUpdatedAt"
> >) {
>   const routeDataMatchesQuery =
>     accountId === initialAccountId && sort === initialSort;
>
>   return useQuery({
>     queryKey: reportKeys.list(accountId, sort),
>     queryFn: ({ signal }) =>
>       fetchReports(accountId, sort, signal),
>     initialData: routeDataMatchesQuery
>       ? initialReports
>       : undefined,
>     initialDataUpdatedAt: routeDataMatchesQuery
>       ? initialReportsUpdatedAt
>       : undefined,
>     staleTime: 30_000
>   });
> }
>
> function useMarkReviewed() {
>   const client = useQueryClient();
>   const mutation = useMutation({
>     mutationKey: reportKeys.markReviewed(),
>     mutationFn: (change: MarkReviewed) =>
>       saveReviewed(
>         change.accountId,
>         change.id,
>         change.reviewed
>       ),
>     onSuccess: (saved, change, _result, context) => {
>       const key = reportKeys.list(
>         change.accountId,
>         change.sort
>       );
>       context.client.setQueryData<Report[]>(
>         key,
>         rows => rows?.map(row =>
>           row.id === saved.id ? saved : row
>         )
>       );
>     },
>     onSettled: (_data, _error, change, _result, context) =>
>       context.client.invalidateQueries({
>         queryKey: reportKeys.lists(change.accountId)
>       })
>   });
>
>   function submit(change: MarkReviewed) {
>     // 其它入口也必须经过这道提交级门闩。
>     const hasPending = client.isMutating({
>       mutationKey: reportKeys.markReviewed()
>     }) > 0;
>     if (hasPending) return;
>     mutation.mutate(change);
>   }
>
>   return {
>     isError: mutation.isError,
>     isPending: mutation.isPending,
>     submit
>   };
> }
>
> function ReportsRoute(props: ReportsRouteProps) {
>   return <ReportsPage key={props.accountId} {...props} />;
> }
>
> function ReportsPage({
>   accountId,
>   sort,
>   onSortChange,
>   initialAccountId,
>   initialReports,
>   ...route
> }: ReportsRouteProps) {
>   const query = useReports({
>     accountId,
>     sort,
>     initialAccountId,
>     initialSort: route.initialSort,
>     initialReports,
>     initialReportsUpdatedAt: route.initialReportsUpdatedAt
>   });
>   const update = useMarkReviewed();
>   const isSavingReviewed = useIsMutating({
>     mutationKey: reportKeys.markReviewed()
>   }) > 0;
>   const hasRouteRowsForAccount =
>     accountId === initialAccountId;
>   const confirmedReports = query.data ?? (
>     hasRouteRowsForAccount
>       ? sortReports(initialReports, sort)
>       : []
>   );
>   const pendingChanges = useMutationState<MarkReviewed>({
>     filters: {
>       mutationKey: reportKeys.markReviewed(),
>       status: "pending"
>     },
>     select: mutation =>
>       mutation.state.variables as MarkReviewed
>   });
>   const visibleReports = confirmedReports.map(report => {
>     const pending = pendingChanges.find(change =>
>       change.accountId === accountId &&
>       change.sort === sort &&
>       change.id === report.id
>     );
>     return pending
>       ? { ...report, reviewed: pending.reviewed }
>       : report;
>   });
>
>   return (
>     <section>
>       <div role="group" aria-label="报表排序">
>         <button
>           type="button"
>           onClick={() => onSortChange("recent")}
>         >
>           Most recent first
>         </button>
>         <button
>           type="button"
>           onClick={() => onSortChange("oldest")}
>         >
>           Oldest first
>         </button>
>       </div>
>
>       {query.isPending && (
>         <p role="status">
>           {hasRouteRowsForAccount
>             ? "正在等待服务端确认当前排序…"
>             : "正在读取当前账户的报表…"}
>         </p>
>       )}
>       {query.isFetching && !query.isPending && (
>         <p role="status">正在更新当前账户的报表…</p>
>       )}
>       {query.isError && (
>         <div>
>           <p role="alert">
>             {query.data === undefined
>               ? hasRouteRowsForAccount
>                 ? "确认失败；仍显示同账户的路由报表。"
>                 : "读取失败；尚无当前账户的报表数据。"
>               : "刷新失败；仍显示上次成功的结果。"}
>           </p>
>           <button
>             type="button"
>             onClick={() => query.refetch()}
>           >
>             重试读取
>           </button>
>         </div>
>       )}
>       {update.isError && (
>         <p role="alert">
>           保存失败；已撤去这次待处理显示，
>           列表保留当前可用结果，可再次提交。
>         </p>
>       )}
>       {update.isPending && (
>         <p role="status">正在保存报表更改…</p>
>       )}
>
>       <div aria-busy={query.isFetching}>
>         <ul>
>           {visibleReports.map(report => (
>             <li key={report.id}>
>               {report.period} — {report.title}
>               <span>
>                 {report.reviewed
>                   ? "Reviewed"
>                   : "Not reviewed"}
>               </span>
>               <button
>                 type="button"
>                 disabled={
>                   !query.data ||
>                   query.isPlaceholderData ||
>                   report.reviewed ||
>                   isSavingReviewed
>                 }
>                 onClick={() => update.submit({
>                   accountId,
>                   sort,
>                   id: report.id,
>                   reviewed: true
>                 })}
>               >
>                 Mark reviewed
>               </button>
>             </li>
>           ))}
>         </ul>
>       </div>
>     </section>
>   );
> }
> ~~~

`<QueryClientProvider>` 应在 `ReportsRoute` 的祖先位置提供同一个 QueryClient；`fetchReports` 与 `saveReviewed` 是应用适配器，需要检查 HTTP 响应并将 JSON 作为 `unknown`（尚未验证的数据）运行时校验，TypeScript 声明不会验证网络值。结构合法还不够：保存响应必须对应本次账户和行。本例由已授权的请求资源范围绑定账户，适配器再确认返回的 `saved.id` 等于提交的 `id`；不匹配就按错误处理，不能交给 `onSuccess` 更新另一行。

代码中的 query function 读取 `signal`（取消信号）并交给 `fetchReports`。适配器要把它继续传给 `fetch`，才能中止底层请求；适配器若忽略它，网络请求仍可能完成，但已取消的查询不会接收这个结果。若 query function 根本不读取 signal，离开页面后请求通常会照常完成，并写入它自己的旧 key。无论哪种情况，客户端取消都不能保证服务器停止执行。

排序例子只在记录成员完全相同的 May/April 全列表上本地重排。若账户、筛选、搜索词或页码改变了集合，就不能把旧集合重排后称为当前结果；切换期间应显示当前查询缓存或等待状态。若有上一排序/账户的占位值，必须确认账户身份相同并标出 `isPlaceholderData`，且不允许在占位行上操作。

`staleTime: 30_000` 与“服务端 30 秒内不变”不是一回事。TanStack Query v5 中，过期的查询会在挂载、窗口重新聚焦或网络恢复时在后台重新读取；手动失效也能要求刷新。若用户改了 URL 中的 `sort` 后点击 Back，路由状态应回到原值，query key 也随之切回对应缓存。若路由改用 `replaceState`，就不会像 `pushState` 那样为每次选择新增历史项，Back 也回不到上一个排序。

## 整表快照回滚的前提与竞态

上面的 overlay 不改缓存。另一种常见的乐观更新则在 `onMutate` 中直接修改查询缓存并保存整表快照，失败时用快照回滚，成功时把服务器返回的行写回该 key。下面保留这组回调；只有在变更期间确实没有其他写入会碰这个列表 key 时，它才适用：

~~~tsx
onMutate: async (change: MarkReviewed, context) => {
  const key = reportKeys.list(change.accountId, change.sort);
  await context.client.cancelQueries({
    queryKey: key,
    exact: true
  });
  const previous = context.client.getQueryData<Report[]>(key);
  context.client.setQueryData<Report[]>(key, rows =>
    rows?.map(row => row.id === change.id
      ? { ...row, reviewed: change.reviewed }
      : row)
  );
  return { key, previous };
},
onError: (_error, _change, snapshot, context) => {
  if (snapshot?.previous !== undefined) {
    context.client.setQueryData(snapshot.key, snapshot.previous);
  }
},
onSuccess: (saved, _change, snapshot, context) => {
  if (snapshot) {
    context.client.setQueryData<Report[]>(snapshot.key, rows =>
      rows?.map(row => row.id === saved.id ? saved : row)
    );
  }
}
~~~

这组快照回调只有在同一列表 key 没有并行写入，也没有后续重取覆盖乐观值时才可靠。`cancelQueries` 只取消调用时已匹配的读取，不是锁；`staleTime` 到期后的窗口聚焦、轮询或手动 `refetch` 仍能在保存期间更新缓存。一次回放中，把时钟推进 31 秒（超过 30 秒的 `staleTime`）后触发焦点重取：读取先把服务端 April 的 `false` 和 May 的新标题写入缓存，覆盖了 April 乐观写入的 `true`；保存失败后，旧的整表快照又把 April、May 整体恢复成旧表，May 的新标题随之丢失。所以主示例采用界面层 overlay，让 pending 变量盖在读取结果之上，而不是把一份旧快照当成共享缓存的权威值。

主例用同一个 mutation key（变更键）和共享的 QueryClient 实现一道全局门闩，保证同时只有一次标记操作：`useIsMutating` 禁用所有报表行按钮，`submit` 再检查是否已有同类保存在处理；`useMarkReviewed` 只对外暴露 `submit` 和状态，不返回可以绕过门闩的原生 `mutate`。若允许多行并发提交，`useMutationState` 会返回多份 pending variables，必须按账户、排序、行 ID 过滤，并用 `submittedAt` 或明确的冲突策略决定同一行显示哪次变更；当前门闩刻意不开放这种并发。

查询缓存和页面中任何已确认数据仍是服务端状态的副本，不是授权来源。若同一报表另有详情 key，也要按 `accountId` 更新/失效详情项，不能只修当前列表。切换账号时，query key 会把组件读取的缓存项按账户隔开；退出登录或权限范围变化时，若旧账户的数据不该留在客户端，还要显式移除对应缓存。任何账户对不上的备用显示，都不应临时展示旧账户的行。

最后，若不用 TanStack Query 而在 `useEffect` 中手写请求，就要在 cleanup 中忽略过期结果或取消请求；这种写法与 TanStack Query 的 key/cache 管理可对照[React 更新轮次中的数据请求](./react-basics.md#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)学习。有关错误如何从查询状态进入错误边界，见[React 错误边界](./react-error-boundaries.md)。网络 JSON 仍需在运行时校验，见[如何处理不可信 JSON？](../typescript/advanced-typescript.md)。

> [!info]- 来源与版本核验（React 19.3；TanStack Query v5 Latest；核验日期 2026-11-12）
> - Query key 应包含会改变 `queryFn` 结果的变量；此处账户和排序都影响数据：[Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)，TanStack Query v5 Latest。
> - Query function 获取 `AbortSignal`。访问它可让 TanStack Query 取消查询状态；继续传给 transport 才会取消底层请求。手动取消会回滚 query state，但不代表服务器停止处理：[Query Functions](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions)、[Query Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)，TanStack Query v5 Latest。
> - `initialData` 写入 cache；`initialDataUpdatedAt` 可提供原数据时间。`placeholderData` 不进 cache，结果带 `isPlaceholderData`：[Initial Query Data](https://tanstack.com/query/latest/docs/framework/react/guides/initial-query-data)、[Placeholder Query Data](https://tanstack.com/query/latest/docs/framework/react/guides/placeholder-query-data)，TanStack Query v5 Latest。
> - 普通 `useQuery` 的 `throwOnError` 与错误状态返回：[useQuery](https://tanstack.com/query/latest/docs/framework/react/reference/functions/useQuery)，TanStack Query v5 Latest。
> - `staleTime` 控制客户端 freshness；stale query 的自动重取入口及按 key 前缀失效：[Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)、[Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)，TanStack Query v5 Latest。
> - mutation 回调收到提交变量，`onSettled` 返回的 Promise 会在 mutation 完成前等待；`useMutationState` 可以读取同 key 的多笔 pending variables，并可选择 `submittedAt`：[useMutation](https://tanstack.com/query/latest/docs/framework/react/reference/functions/useMutation)、[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5 Latest。
> - Cache optimistic update 和 UI variables overlay 是两种受支持路径；pending variables 可能同时有多笔：[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5 Latest。
> - `invalidateQueries` 将匹配查询标为 invalidated，默认立即重取活跃查询；非活跃查询留在缓存并等待下次使用：[QueryClient.invalidateQueries](https://tanstack.com/query/latest/docs/framework/react/reference/classes/QueryClient#invalidatequeries)，TanStack Query v5 Latest。
> - `QueryClientProvider` 把一个 QueryClient 提供给子树中的查询组件：[QueryClientProvider](https://tanstack.com/query/latest/docs/framework/react/reference/functions/QueryClientProvider)，TanStack Query v5 Latest。
> - query cache 可以按 query key 前缀移除：[QueryClient](https://tanstack.com/query/latest/docs/framework/react/reference/classes/QueryClient)，TanStack Query v5 Latest。
> - HTTP URI 的 fragment 不作为请求目标发送：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)。浏览器历史恢复 `sort` 的完整路由流程见[浏览器导航路径](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)。
> - Effect cleanup 防止过期读取写回界面：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3。
