# React界面如何维护服务端数据与乐观更新的正确性？

**案例背景。** 报表页初始地址是 `/reports?sort=recent#summary`。浏览器只把路径和查询参数 `/reports?sort=recent` 发给服务端；`#summary` 是客户端定位片段。服务端给出 May、April 两行。用户选择 **Oldest first** 后，URL 中的 `sort` 变为 `oldest`，可见顺序先变成 April、May，再由当前查询结果确认。完整应用用[浏览器主线的 `pushState` 与 `popstate` 路径](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)记录筛选历史并在 Back 时恢复 `recent`；本章的查询示例省略 URL/history 集成。排序偏好是界面/路由状态，报表记录由服务端拥有；query cache（查询缓存）只是客户端对服务端结果的副本。要避免把旧排序结果误当成新结果，查询身份必须包含影响返回数据的筛选条件。

## 排序值构成查询身份

以下示例使用 TanStack Query v5.90.3。`queryKey` 的排序项不同，代表两份不同的查询结果；`queryFn` 使用同一次 render 闭包中的 `sort` 发请求，这个值也构成 key。首次由路由加载的报表只作为 `initialSort` 对应查询的初始数据，不会被误塞进另一种排序的缓存项。

~~~tsx
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

type SortOrder = "recent" | "oldest";
type Report = {
  id: string;
  period: string;
  periodStart: string;
  title: string;
  reviewed: boolean;
};

const reportKeys = {
  lists: () => ["reports", "list"] as const,
  list: (sort: SortOrder) => ["reports", "list", sort] as const
};

declare function fetchReports(sort: SortOrder, signal: AbortSignal): Promise<Report[]>;

function sortReports(reports: Report[], sort: SortOrder) {
  return [...reports].sort((a, b) => {
    const order = a.periodStart.localeCompare(b.periodStart);
    return sort === "recent" ? -order : order;
  });
}

function useReports(sort: SortOrder, initialSort: SortOrder, initialReports: Report[]) {
  return useQuery({
    queryKey: reportKeys.list(sort),
    queryFn: ({ signal }) => fetchReports(sort, signal),
    initialData: sort === initialSort ? initialReports : undefined,
    staleTime: 30_000
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
  const query = useReports(sort, initialSort, initialReports);
  const visibleReports = query.data ?? sortReports(initialReports, sort);

  function chooseSort(next: SortOrder) {
    setSort(next);
  }

  return (
    <section aria-busy={query.isFetching}>
      <button type="button" onClick={() => chooseSort("oldest")}>
        Oldest first
      </button>
      {query.isPending && <p>列表已按 {sort} 本地排序，正在等待服务端确认…</p>}
      {query.isFetching && !query.isPending && <p>正在更新当前排序…</p>}
      {query.isError && (
        <div>
          <p role="alert">
            {query.data === undefined
              ? "服务端确认失败；仍显示本地已有报表。"
              : "更新失败；仍显示上次取得的结果。"}
          </p>
          <button type="button" onClick={() => query.refetch()}>
            重试服务端确认
          </button>
        </div>
      )}
      <ul>{visibleReports.map(report => <li key={report.id}>{report.period} — {report.title}</li>)}</ul>
    </section>
  );
}
~~~

切换到 `oldest` 后，查询 key 改变；若这个 key 还没有缓存，`visibleReports` 暂时用路由交来的 May、April 在本地按 `periodStart` 排成 April、May，并显示“正在等待服务端确认”。这只在同一份完整记录集合里改变排序时成立；若筛选条件改变成员集合或数据是分页子集，就不能把另一结果集重新排序来冒充当前结果。响应到达后，列表改用当前 query 的结果；首次请求失败时仍保留本地行和排序控件，提示错误并提供 `query.refetch()` 重试。旧 `recent` 请求若仍成功完成，也只能填充 `recent` 对应缓存，不会变成 `oldest` 的行；若 query function 消费取消信号，旧读取还可能被取消。若用户以前查询过 `oldest`，缓存中已有数据时可以先显示它，再根据新鲜度策略重新取数。若使用 `placeholderData` 保留旧排序行，界面也要标出它仍对应旧 key，不能把它说成已确认的新排序。代码中的 `setSort` 只演示排序状态如何切换查询 key；完整路由还要用 `pushState` 新增 `sort=oldest` 历史项，并在 `popstate` 时恢复 URL 对应的查询状态，不能把 `replaceState` 当成等价操作。

`staleTime: 30_000` 表示这份缓存 30 秒内按客户端策略视为 fresh；它不承诺服务端数据在这段时间不变，也不是数据库一致性保证。需要强制校准时，对受影响的 key 做失效。`#summary` 不会随 HTTP 请求发送，也不会决定服务端数据；只有客户端明确把片段值映射成请求参数时，那个映射后的参数才进入 query key。

## 变更先乐观显示，再与服务端协调

以下变更示例接在上面的查询流程之后：先切换到 `oldest`，等服务端成功返回，使 `reports/list/oldest` 缓存里已有真实报表行；再点击 April 行的 **Mark reviewed**。调用端用 `{ id: "april", reviewed: true, sort: "oldest" }` 调用这个 mutation。只有当前排序 key 已有已确认的 `query.data` 时才启用该操作；切换排序期间展示的本地临时行只用于保持列表，不提供可变更数据。此时 oldest 缓存先把 April 从未读改为已读；保存成功后用服务端响应替换它并失效相关列表，失败时回滚为未读。

~~~tsx
type MarkReviewed = {
  id: string;
  reviewed: boolean;
  sort: SortOrder;
};

declare function saveReviewed(id: string, reviewed: boolean): Promise<Report>;

function useMarkReviewed() {
  return useMutation({
    mutationFn: ({ id, reviewed }: MarkReviewed) => saveReviewed(id, reviewed),
    onMutate: async (change: MarkReviewed, context) => {
      const key = reportKeys.list(change.sort);
      await context.client.cancelQueries({ queryKey: key });
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
    },
    onSettled: (_data, _error, _change, _snapshot, context) =>
      context.client.invalidateQueries({ queryKey: reportKeys.lists() })
  });
}
~~~

这里回滚的是整份当前列表快照，因此这个简化方案假设 `reports/list` 前缀下的所有排序视图共用一个变更入口：从 `onMutate` 到 `onSettled` 返回的失效 Promise 完成前，全局只有一个乐观变更。否则另一排序 key 上的 mutation 或失效重抓可能覆盖乐观值，整表回滚也可能抹掉另一笔已成功变更。调用端应使用列表级 `isPending` gate 禁用所有排序视图中的行操作，不能只按行或按当前排序 key 禁用；首次切换时的本地临时行以及当前 key 尚无 `query.data` 的视图也要禁用操作。如果存在其他触发入口，它们也必须共享提交级串行约束；单靠某个 hook 的 `isPending` 显示或禁用按钮不能阻止其他入口并发提交。若 mutation 失败，界面可检查 `isError`，并用同一组变量重试，例如再次提交上面的 April 参数。当前片段只展示 hook/cache 处理，没有渲染调用按钮。若同一报表还缓存为详情查询，更新也要覆盖或失效对应的详情 key，不能只改当前列表。服务端仍是权威来源；乐观更新只是让等待中的界面先表达用户意图。

查询函数收到的 `AbortSignal` 要传给 `fetch` 才能让客户端取消底层读取；取消与忽略旧响应是客户端行为，不能承诺服务端已经停止处理请求。若手写 Effect 而不用查询库，要用 cleanup 忽略过期结果，见[React更新轮次中的数据请求](./react-basics.md#effect在提交后同步外部系统)。API JSON 仍须在边界运行时校验；TypeScript 类型本身不会验证网络数据，见[如何处理不可信 JSON？](../typescript/advanced-typescript.md)。

> [!info]- 来源与版本核验（TanStack Query v5.90.3；React 19.3；2026-11-06）
> - `queryKey` 标识查询，函数参数可从 QueryFunctionContext 读取 `signal`：[Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)、[Query Functions](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions)，TanStack Query v5.90.3，核验日期 2026-11-06。
> - query status、`refetch`、mutation callback 与返回 Promise 的等待语义：[useQuery](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery)、[useMutation](https://tanstack.com/query/latest/docs/framework/react/reference/useMutation)、[Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)，TanStack Query v5.90.3。
> - `staleTime`、失效和缓存策略：[Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)、[Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)、[`QueryClient.setQueryData`](https://tanstack.com/query/latest/docs/reference/QueryClient#queryclientsetquerydata)，TanStack Query v5.90.3。
> - 取消信号与乐观更新快照/回滚：[Query Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)、[Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)，TanStack Query v5.90.3。
> - React 手写 Effect 请求必须清理失效响应：[Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)，React 19.3 文档，核验日期 2026-11-06。
> - HTTP 资源标识中的片段不随请求发送：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986#section-3.5)，核验日期 2026-11-06。
