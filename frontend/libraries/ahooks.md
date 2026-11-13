# ahooks 怎样管理报表请求、分页与列表身份？

**案例背景。** 报表从 `/reports?sort=recent#summary` 打开时，Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 是排序和历史状态的来源。

基准时间线假定搜索框为空、路由正常复用同一页面组件，且 **Oldest first** 使用默认的 PUSH（新增历史项）导航：点击后路由发起导航并运行父级 loader；等待期间 `navigation.location` 已指向 oldest，但 `window.location`、历史项和页面数据仍是 recent，loader 成功后才把新 URL 写入历史并提交 oldest。按 Back 时地址先回到 recent 并触发 loader；完成前路由的已提交 sort 仍是 oldest。搜索框的 `Ops` 值只存在组件本地，不在 URL 中；输入后再切换排序并按 Back，复用的组件会保留 `Ops`。下表先走空搜索的 `useRequest` 方案；分页和游标加载是替代读取方式，可编辑列表则是单独的编辑会话。

下表把父级 loader 提交与报表请求成功分开。精确请求序列假定正常挂载；根级开发 StrictMode 可能额外执行挂载 Effect。

| 时点 | 已提交的 `sort` | `useRequest` 与屏幕上的列表 |
|---|---|---|
| 父级 loader 提交首次 `recent` | `recent` | 组件挂载，`useRequest` 开始请求 `(recent, "")`；列表请求尚未成功。 |
| recent 请求成功 | `recent` | 显示 May、April。 |
| 点击 Oldest first，目标路由尚未结算 | `recent` | 组件仍收到 recent；不提前发 oldest 请求，最近成功的列表仍可见。 |
| 父级 loader（路由数据加载函数）结算并提交 `oldest` | `oldest` | `refreshDeps` 发起 oldest 请求；等待期间 `data` 可保留 May、April。 |
| oldest 请求成功 | `oldest` | `data` 更新为 April、May。 |
| 按 Back，recent loader 尚未结算 | `oldest` | 已提交值仍是 oldest；不提前发 recent 请求。 |
| Back 的 loader 提交 `recent` | `recent` | `refreshDeps` 请求 `(recent, "")`；列表仍显示上次成功的 April、May。 |
| recent 请求成功 | `recent` | `data` 更新为 May、April。 |

## 请求 Hook（钩子）管本地请求状态，不自动取得传输控制权

下面的例子假定采用 React Router 的 Data Mode，且父级只负责路由：它从 URL loader 的**已提交数据**中取出 `sort` 并传给组件；不要把 `navigation.location` 中尚未提交的目标值提前传入。父 loader 在这个替代方案中只解析并校验 `sort`，不取报表：其返回值为 `{ sort }`，父组件再将 `useLoaderData()` 中已提交的 `sort` 传给 `ReportPanel`。发起默认 PUSH 导航后，`navigation.location` 已指向 oldest，但 `window.location` 和历史项还停在 recent，页面也保留已提交数据；loader 成功后 React Router 才把目标 URL 推入历史并提交新页面，随后复用 `ReportPanel` 实例，因此未写进 URL 的本地搜索值会继续保留。此处由组件独自拥有列表请求，不同时配置 React Router loader 或 TanStack Query 请求同一份列表。`fetchReports` 是会校验响应形状的 Application Programming Interface（应用程序编程接口，API）客户端。初次渲染会自动请求；`refreshDeps` 改变时，Hook 使用最新的服务函数再次请求。等待期间 `data` 可以保留上次成功的列表：

~~~tsx
import { useState } from "react";
import { useDebounce, useRequest } from "ahooks";
import { fetchReports } from "./report-api";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };

function ReportPanel({ sort }: { sort: SortOrder }) {
  const [query, setQuery] = useState("");
  const settledQuery = useDebounce(query, { wait: 300 });
  const { data: reports, loading, error } = useRequest(
    () => fetchReports({ sort, query: settledQuery }),
    { refreshDeps: [sort, settledQuery] }
  );

  return (
    <section>
      <label>
        搜索报表
        <input
          value={query}
          onChange={event => setQuery(event.target.value)}
        />
      </label>
      {loading && <p role="status">正在加载报表…</p>}
      {error && <p role="alert">报表读取失败。</p>}
      <ol aria-label="报表" aria-busy={loading}>
        {reports?.map((report: Report) => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}
~~~

`useDebounce` 返回延迟后的值，不返回网络请求。假设输入前搜索条件为空，用户输入 `Ops` 后立刻切换到 oldest，且路由在 300 ms 防抖到期前已经提交 oldest，服务调用顺序是 `recent/"" → oldest/"" → oldest/"Ops"`：排序导航一开始，路由仍保留 recent 的已提交页面；等 oldest loader 成功，父级才把 `sort=oldest` 交给这个组件，随后 `refreshDeps` 触发请求；300 ms 到期后搜索值再触发一次。若路由更慢，搜索值会先在 recent 下生效，调用顺序也随之改变；决定请求参数的是当时已提交的 sort 和已稳定的搜索值。

新的 `useRequest` 调用会让前一次结果过期，但等新数据成功前，屏幕上的旧列表仍是最近一次成功结果，不代表它已经符合 oldest 或 `Ops` 条件。

排序 URL 不包含搜索值；若 oldest/`Ops` 已成功，按 Back 只把排序改回 recent，服务会请求 `(recent, "Ops")`，而非空搜索的 `(recent, "")`。这条完整路径的服务参数是 `recent/"" → oldest/"" → oldest/"Ops" → recent/"Ops"`。输入防抖不延迟路由导航。若 React Router loader 或 TanStack Query 已经负责同一份列表，就不要再挂这段 `useRequest` 重复读取。

`useRequest` 默认自动运行（且 `ready` 为 true）；`manual: true` 才等待调用 `run` 或 `runAsync`。`ready: false` 会阻止请求，即使手动调用 `run` 也不会绕过它。`run` 返回 `void`，失败由 `onError` 等回调处理；`runAsync` 返回 Promise，调用方应处理失败。v3.11.0 的 `Fetch.runAsync` 会等服务 Promise 结算后才比较请求代次；若它已过期，才以 `CancelledError` 拒绝，`run` 会处理这个取消错误。`cancel()` 会立即让 Hook 忽略当前 Promise 的结果并结束 Hook 的等待状态，但 `runAsync` 仍需等原服务 Promise 结算后才能拒绝；如果服务 Promise 永不结算，调用方的 `runAsync` 也可能一直 pending。它不会撤销已经发给浏览器或服务端的网络请求。若传输必须停止，服务本身还要接收并响应 AbortSignal（请求取消信号），通常由 AbortController（请求控制器）发出。

常用状态和控制各自回答不同问题：

| 返回值 | 契约 |
|---|---|
| `data / error / loading / params` | 保留的数据、最近记录的错误、当前等待状态和最近一次传给 `run` 的参数；这些值可能来自不同请求。 |
| `run` | 启动服务，返回 `void`；普通失败走 Hook 的错误回调。 |
| `runAsync` | 启动服务并返回 Promise；取消的调用也可能拒绝。 |
| `refresh / refreshAsync` | 使用最近一次参数重新请求。 |
| `mutate` | 改变 Hook 当前展示的数据；不等于写入服务端，也不自动同步其他数据所有者。 |
| `cancel` | 忽略当前请求结果；不等于底层请求的 AbortController。 |

上面的 `ReportPanel` 通过闭包读取 `sort` 和 `settledQuery`，自动请求没有把它们作为参数传给 `run`；此处的 `params` 不会因此保存这两个闭包值。

v3.11.0 的其他 `useRequest` 选项还包括首次自动调用时使用的 `defaultParams`、`onBefore` / `onSuccess` / `onError` / `onFinally` 回调，以及 `retryCount` / `retryInterval` 重试控制；重试适合可安全重放的读取。维护 v2 项目时会遇到 `debounceInterval` / `throttleInterval`；v3 将名称改为 `debounceWait` / `throttleWait`，并以 `usePagination`、`useInfiniteScroll` 替代 `pagination`、`loadMore` 请求选项，原来的 `formatResult` 转换要放在服务层。升级代码前先核对实际依赖版本，别把两代选项混用。

## 分页服务返回 total 与 list，滚动加载返回下一段

`usePagination` 的服务接收 `current` 和 `pageSize`，解析为 `{ total, list }`；排序变化时 `refreshDeps` 会把页码重置到第 1 页并重新请求。下表是假定 recent 与 oldest 都各有 42 条报表、每页 20 条的成功轨迹：

| 操作 | 服务收到的参数 | 返回列表长度 | `current` 与总数 |
|---|---|---:|---|
| 打开 recent | `(recent, 1, 20)` | 20 | `1`，共 42 条 |
| 下一页 | `(recent, 2, 20)` | 20 | `2`，共 42 条 |
| 再下一页 | `(recent, 3, 20)` | 2 | `3`，已到末页 |
| 排序切到 oldest | `(oldest, 1, 20)` | 20 | 重置到 `1`，共 42 条 |

分页 Hook 以最近一次调用参数计算 `pagination.current`。若第 2 页失败，`data` 仍可能是第 1 页的列表，而 `current` 已是 2；若首次请求失败，列表为空。下方示例把错误显示出来，并用 `refresh()` 重试当前页。若 URL 是页码来源，控件也须从 URL 读取并通过导航更新 URL；只把 URL 页码传进服务函数，不会把 `usePagination` 自己的 `current` 同步成路由状态。

~~~tsx
import { usePagination } from "ahooks";
import { fetchReportPage } from "./report-api";

// 沿用上文的 SortOrder、Report 类型。
function PagedReports({ sort }: { sort: SortOrder }) {
  const { data, loading, error, refresh, pagination } = usePagination(
    ({ current, pageSize }) =>
      fetchReportPage({ sort, current, pageSize }),
    { defaultPageSize: 20, refreshDeps: [sort] }
  );

  return (
    <section>
      {error && (
        <p role="alert">
          {loading
            ? data
              ? `正在重试第 ${pagination.current} 页；下方仍是最近一次成功结果。`
              : `正在读取第 ${pagination.current} 页；尚无成功结果。`
            : data
              ? `第 ${pagination.current} 页读取失败；下方仍是最近一次成功结果。`
              : `第 ${pagination.current} 页读取失败；尚无成功结果。`}
          <button type="button" onClick={refresh} disabled={loading}>
            {loading ? "正在重试…" : `重试第 ${pagination.current} 页`}
          </button>
        </p>
      )}
      <ol aria-label="报表" aria-busy={loading}>
        {data?.list.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
      <button
        type="button"
        onClick={() => pagination.changeCurrent(pagination.current + 1)}
        disabled={
          loading || Boolean(error) || !data ||
          pagination.current * pagination.pageSize >= data.total
        }
      >
        下一页
      </button>
    </section>
  );
}

// API 响应形状：{ total: 42, list: Report[] }；pageSize 为 20 时可依次到第 2、3 页。
~~~

`useInfiniteScroll` 把已累计数据交回服务，让服务用当前游标获取下一页；Hook 会把新列表接到已有列表后面。本例把游标看作排序专属：父级用已提交的 `sort` 作为子组件的 React key，切换排序时新挂载一个空 Hook 实例。这样旧排序的累计数据和游标不会被新排序复用；代价是切换时旧列表暂时消失。如果产品必须保留旧列表，就要同时记录列表所属的 sort，并在新首页成功前禁止以旧游标续页。下面只用显式按钮触发后续页，便于看清每次请求的来源。

~~~tsx
import { useInfiniteScroll } from "ahooks";
import { fetchNextReportPage } from "./report-api";

type ReportPage = { list: Report[]; nextCursor: string | null };

function SortedReportFeed({ sort }: { sort: SortOrder }) {
  return <ReportFeed key={sort} sort={sort} />;
}

function ReportFeed({ sort }: { sort: SortOrder }) {
  const { data, loading, loadingMore, error, noMore, loadMore, reload } =
    useInfiniteScroll(
      (current?: ReportPage) =>
        fetchNextReportPage({ sort, cursor: current?.nextCursor ?? null }),
      { isNoMore: current => current != null && current.nextCursor === null }
    );

  return (
    <div style={{ height: 360, overflow: "auto" }}>
      {loading && <p role="status">正在读取报表…</p>}
      {error && (
        <p role="alert">
          {loading || loadingMore
            ? "正在重试报表页。"
            : data ? "继续加载失败。" : "首页读取失败。"}
          <button
            type="button"
            onClick={data ? loadMore : reload}
            disabled={loading || loadingMore}
          >
            {loading || loadingMore ? "正在重试…" : data ? "重试这一页" : "重试首页"}
          </button>
        </p>
      )}
      <ol>
        {data?.list.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
      <button
        type="button"
        onClick={loadMore}
        disabled={loading || loadingMore || noMore || Boolean(error)}
      >
        {noMore ? "没有更多报表" : "加载更多"}
      </button>
    </div>
  );
}
~~~

假定 recent 和 oldest 各有两页，表中返回值是这个公开合成案例的输入。它展示首页失败和续页失败时，各自应重试哪一段：

| 操作 | 服务输入与返回 | 累计 `data.list` | 界面状态与下一步 |
|---|---|---|---|
| 首次读取 recent | `(recent, null) → [May], recent:page-2` | `[May]` | 可加载下一页。 |
| 加载 recent 下一页 | `(recent, recent:page-2) → [April], null` | `[May, April]` | `noMore` 为真，按钮禁用。 |
| sort 提交 oldest；key 更换后首页失败 | `(oldest, null) → error` | 空 | 只有“重试首页”可用；“加载更多”保持禁用，旧 recent 游标已随旧组件丢弃。 |
| 重试 oldest 首页 | `reload() → (oldest, null) → [April], oldest:page-2` | `[April]` | 可加载下一页。 |
| oldest 续页失败 | `(oldest, oldest:page-2) → error` | `[April]` | 仍显示已成功的首页；“重试这一页”再次调用同一游标。 |
| 重试 oldest 续页成功 | `(oldest, oldest:page-2) → [May], null` | `[April, May]` | `noMore` 为真，按钮禁用。 |

若选择滚动自动续页，可另传滚动容器 `target` 与 `threshold`；短首屏未填满容器时，Hook 可能自动继续取下一页。若同时提供自动滚动和按钮，两个触发可能撞上同一个在途游标，应在服务边界合并相同 `(sort, cursor)` 请求。上例只使用手动按钮。

这里 `fetchNextReportPage` 的响应有 `list` 和 `nextCursor`；`isNoMore` 在游标为 null 时停止。实际接口要校验分页响应，并限制重复请求和授权范围。ahooks v3.11.0 修复了空页导致连续自动请求的问题；仍应处理空列表、错误和没有下一页的状态。

## 可编辑表单行要用可复现的稳定身份

`useState(() => reports)` 只把 props 当作首次初始化值；父路由后来传来 oldest 列表时，已编辑列表不会自动同步。下面明确把表单定义成一次编辑会话的快照：要放弃草稿并换数据时，调用者应显式开始新会话或重置列表。服务端报表使用自己的 `report.id`；新增草稿在点击事件中只生成一次 ID：

~~~tsx
function EditableReportList({ reports }: { reports: Report[] }) {
  const [list, setList] = useState(() => reports);

  return (
    <>
      <button
        type="button"
        onClick={() => {
          const draft = {
            id: `draft:${crypto.randomUUID()}`,
            period: "草稿",
            title: "待补报表"
          };
          setList(current => [draft, ...current]);
        }}
      >
        添加草稿
      </button>
      {list.map(report => (
        <div key={report.id}>
          {report.period} — {report.title}
          <button
            type="button"
            onClick={() => setList(current => current.filter(row => row.id !== report.id))}
          >
            移除
          </button>
        </div>
      ))}
    </>
  );
}
~~~

假设 May 行的输入框已保存了局部值 `"检查空名称"`，April 行保存了 `"核对响应码"`。若用数组下标作 key，插入草稿后位置 0 仍复用原 key 0，草稿会接到 May 的输入值；May 移到位置 1 后又会接到 April 的值。用 `report.id` 时，May 的身份 key 随行移动，局部输入仍留在 May。

ahooks v3.11.0 文档把 `useDynamicList.getKey(index)` 描述为可保持列表项身份的 key；但在 React 19.3.1 开发 StrictMode 下实测，初始化和 `insert(0, draft)` 都触发其内部 key ref 的重复递增：插入前是 `[May:2, April:3]`，插入后是 `[Draft:5, May:4, April:2]`，和常见使用者预期不符。这是该版本与开发 StrictMode 的实测问题，不应泛化为 React 的 key 契约；主例因此用业务 `report.id` 和每次新增只生成一次的草稿 ID。若维护依赖 `getKey` 的代码，应在实际 React、ahooks 版本和 StrictMode 配置下覆盖插入、移动、重置行为。`useDynamicList` v3.11.0 还提供 `move`、`batchRemove`、`replace`、`push` / `pop`、`unshift` / `shift` 和 `resetList`；`merge(index, items)` 是把多项插入列表的位置操作，不是 Lodash 的对象深合并。`sortList` 会保留 `0`、`false` 和空字符串，只剔除 `null` 与 `undefined`。

`useVirtualList` 在 v3.11.0 返回 `[visibleRows, scrollTo]`，每项带 `data` 和源 `index`，通过 `containerTarget` / `wrapperTarget` 配置滚动容器；`itemHeight` 可为固定数值或按行计算的函数，行高要与实际布局相符。源数组每次渲染都换引用时，计算可见范围的 Effect 会再次运行并写入新的可见列表 state，带来额外渲染；内容未变时保持引用稳定，或用 `useMemo` 记住。归档 ahooks v2.6 使用对象返回值 `{ list, containerProps, wrapperProps, scrollTo }`；其 `itemHeight` 函数按源索引给出高度，没有独立的 `estimateSize` 参数，不要混用版本。虚拟化只减少挂载的 Document Object Model（文档对象模型，DOM）行数，不会减少网络分页或完整源数组的内存；变高行、可访问边界与滚动成本见[大列表如何在网络、DOM 和可访问性之间取舍？](../performance/rendering-and-computation-optimization.md)。

## 轻量状态和时序工具也有边界

`useBoolean` 提供显式布尔动作，`useToggle` 切换两个值，`useMap` 和 `useSet` 管集合；`useCreation(factory, deps)` 按依赖复用创建结果，但不提供资源生命周期或永久语义缓存保证。不要在其 factory 中做 Effect 副作用。

`useLatest(value)` 在 ahooks v3.11.0 的实现中会在每次 render（渲染）期间直接写入 `ref.current = value`。已安装的长生命周期回调因此不必重建即可读取新 render 的值；但 React 把组件渲染和提交分成两个阶段，并要求不要在 render 中读写 ref。若 React 正在进行一次 concurrent rendering（并发渲染），这次写入发生在提交前；如果这次渲染最终被放弃，共享 ref 仍可能保留该值，所以回调可能读到未提交的值；这是由实现与 React 渲染规则推得的边界，不是 `useLatest` 的“最新已提交值”保证。

若某段逻辑只由 Effect（副作用）调用，且确实要读取最新已提交的 props/state 而不重建 Effect，可用 React 19.2 起提供的 `useEffectEvent`（效果事件）；它只能由所属组件中的 Effect 或另一个 Effect Event 调用，不能作为普通事件回调或传给子组件，详见[React 如何在 Effect 中读取最新已提交值？](../frameworks/react-component-composition.md#%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89Hook%E5%A4%8D%E7%94%A8%E7%8A%B6%E6%80%81%E8%A1%8C%E4%B8%BA)。

`useMemoizedFn(fn)` 返回身份稳定的函数包装器，并在渲染期间把传入的新函数写入内部 ref；和 `useLatest` 返回调用者可读写的 ref 不同，它解决的是函数身份是否变化。与 `useLatest` 一样，不应把“最新函数体”理解成只读取最新已提交的闭包：被放弃的渲染也可能先改写该 ref。

`useLocalStorageState` 方便持久化浏览器设置。v3.11.0 的 `listenStorageChange` 默认是 `false`；要在同源标签页间同步，需显式设为 `true`。`getInitialValueInEffect` 也默认是 `false`，浏览器初始化时会读存储；若服务端渲染不能在初始 render 读取浏览器存储，可设为 `true`，先用默认值渲染，再在客户端挂载后读取并更新。Storage（浏览器存储）可能不可用或被用户改写，不能当作可信权限来源。

`useMount` / `useUnmount` 是 Effect 建立与清理的封装，不等于进程生命周期内绝对只运行一次。根级 React StrictMode 开发模式会额外执行一次 setup → cleanup → setup；订阅或计时器等副作用要能正确清理，首次载入也不能产生不可逆的重复动作。

| Hook | 返回 / 默认时序 |
|---|---|
| `useDebounce(value)` | 延迟后的值，`wait` 默认 1000 ms，`leading` 默认 false，`trailing` 默认 true；`maxWait` 可选。 |
| `useThrottle(value)` | 限频后的值，`wait` 默认 1000 ms，`leading` 与 `trailing` 默认 true。 |
| `useDebounceFn(fn)` | `{ run, cancel, flush }`；默认 `wait` 1000 ms、leading false、trailing true。 |
| `useThrottleFn(fn)` | `{ run, cancel, flush }`；默认 `wait` 1000 ms、leading / trailing true。 |

debounce 的 `cancel` 只取消尚未执行的函数调用；请求已经开始后，必须另行管理网络取消。排序点击应立即发起导航，地址与列表的提交时点由路由决定；输入搜索适合等待停顿后再查。更多 React Hook 生命周期见[React 组件如何组合状态与行为？](../frameworks/react-component-composition.md)，服务端查询与乐观更新见[React界面如何维护服务端数据与乐观更新的正确性？](../frameworks/react-server-state-and-optimistic-updates.md)。

> [!info]- 来源与版本核验（ahooks v3.11.0；当前稳定版于 2026-11-12 核验）
> - 当前稳定版本和 v3.11.0 的分页、取消、空页、动态列表假值修复：[ahooks v3.11.0 release](https://github.com/alibaba/hooks/releases/tag/v3.11.0)，发布于 2026-10-27；GitHub 的 latest release 在 2026-11-12 仍指向 v3.11.0。
> - `useRequest` 的默认自动执行、手动控制与状态：[useRequest](https://ahooks.js.org/hooks/use-request/)；`ready` 为 false 时阻止调用：[v3.11.0 useAutoRunPlugin](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/plugins/useAutoRunPlugin.ts)，L34–41；调用参数、状态更新、失败保留数据、取消与 refresh：[v3.11.0 Fetch source](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/Fetch.ts)，L61–65、L90–114、L142–154。
> - 请求回调、默认参数、重试和 v3 `debounceWait` / `throttleWait`：[v3.11.0 option types](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/types.ts)；v2 到 v3 的旧请求选项迁移：[upgrade guide](https://ahooks.js.org/guide/upgrade/)，2026-11-06。
> - 分页响应、页码参数和 `refreshDeps`：[usePagination](https://ahooks.js.org/hooks/use-pagination/) 与 [v3.11.0 implementation](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/usePagination/index.ts)，L32–45、L57–67；累积列表、游标服务、成功时替换/追加列表、`loadMore` 复用累计数据及 `reload()` 从首页重试：[useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll/) 与 [v3.11.0 implementation](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useInfiniteScroll/index.tsx)，L29–30、L46–70、L94–100、L115–118。
> - 切换 `key` 会重置该子组件状态：[React Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state#option-2-resetting-state-with-a-key)，19.3 版；按数据 ID 保持行状态：[React Rendering Lists](https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key)。
> - `useDynamicList` 的文档 key 契约、操作与 `sortList`：[useDynamicList](https://ahooks.js.org/hooks/use-dynamic-list/)、[v3.11.0 type definition](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useDynamicList/index.ts)、[v3.11.0 release changes](https://github.com/alibaba/hooks/releases/tag/v3.11.0)。开发 StrictMode key 漂移是 v3.11.0 + React 19.3.1 的本地实测，不作为通用 API 语义。
> - `useLatest`、`useMemoizedFn` 在渲染期更新 ref 的行为：[v3.11.0 useLatest](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useLatest/index.ts)、[v3.11.0 useMemoizedFn](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useMemoizedFn/index.ts)；React 将渲染与提交分阶段，并要求不在渲染中读写 ref：[React `useRef` caveats](https://react.dev/reference/react/useRef#caveats)、[Render and Commit](https://react.dev/learn/render-and-commit)；最新已提交值和 Effect Event 的调用边界：[React `useEffectEvent`](https://react.dev/reference/react/useEffectEvent)，核验日期 2026-11-12。
> - `useLocalStorageState` 默认不监听 storage 变化，也默认在初始化读取存储；两个配置项的默认值与挂载后读取分支：[v3.11.0 createUseStorageState](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/createUseStorageState/index.ts)，L21–25、L59–73、L130–157；API 用途：[useLocalStorageState](https://ahooks.js.org/hooks/use-local-storage-state/)。同源 `localStorage` 变更会通知其他标签页的事实由 [MDN `storage` event](https://developer.mozilla.org/en-US/docs/Web/API/Window/storage_event) 核验，2026-11-12；React `useMount` / `useUnmount` 的用途：[useMount](https://ahooks.js.org/hooks/use-mount/)、[useUnmount](https://ahooks.js.org/hooks/use-unmount/)，原有核验日期 2026-11-06。
> - React Router Data Mode 的 loader 等待与 pending 导航：[Pending UI](https://reactrouter.com/start/data/pending-ui) 和 [useLoaderData](https://reactrouter.com/api/hooks/useLoaderData)，按 8.5.1 官方文档核验；默认 PUSH 在成功完成导航后才写入新历史项：[v8.5.1 `completeNavigation`](https://github.com/remix-run/react-router/blob/react-router%408.5.1/packages/react-router/lib/router/router.ts#L1613-L1619)，2026-11-12。根级开发挂载 Effect 的额外执行：[React StrictMode](https://react.dev/reference/react/StrictMode)，19.3 版。
> - 当前虚拟列表结果形状与行高函数：[useVirtualList](https://ahooks.js.org/hooks/use-virtual-list/)、[v3.11.0 implementation](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useVirtualList/index.ts)；v2.6.0 旧结果形状：[v2.6.0 source](https://github.com/alibaba/hooks/blob/v2.6.0/packages/hooks/src/useVirtualList/index.ts)。
> - debounce / throttle 返回值与默认选项：[useDebounce](https://ahooks.js.org/hooks/use-debounce/)、[useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn/)、[useThrottle](https://ahooks.js.org/hooks/use-throttle/)、[useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn/)。
> - 隔离重放：2026-11-06 以 Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0 和 ahooks 3.11.0 核对请求代次、分页重置、手动游标追加、草稿会话和取消；短首屏自动加载与按钮并用可重复请求同一游标。2026-11-12 以 Node 26.13.0、React 19.3.1、React Router 8.5.1、ahooks 3.11.0 和 jsdom 26.1.0 进一步重放排序切换、首页失败重试、续页同游标重试、PUSH/Back 时序与开发 StrictMode 的 key 序列。服务使用模拟 Promise；这些结果不涵盖真实 HTTP、SSR 或实际滚动表现。
