# Next.js 如何把文件路由、服务端数据与客户端交互连接起来？

**案例背景。** 报表页打开 `/reports?sort=recent#summary`。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端取得 May、April；用户点 **Oldest first** 后，URL 进入 `sort=oldest`，页面显示 April、May，再按 Back 恢复 recent 顺序。`#summary` 是浏览器片段，不会发给服务端。这条主流程假设搜索框为空；若用户已输入查询，客户端本地 query 可以在排序导航和 Back 后继续保留，当前列表仍会被它过滤。本文按当前 Next.js 16.4.5 App Router（应用路由器）讲清：文件怎样选中页面、服务器怎样读 URL 并取数、客户端代码从哪里开始，以及加载和错误如何沿路由边界显示。

~~~mermaid
flowchart TD
    A["/reports?sort=recent#summary"] --> B[Page 读取 searchParams 并启动两项请求]
    B --> C[先显示外壳与排序链接]
    B --> D[摘要与报表分别等待]
    D --> E[数据到达后填充相应区域]
    E --> F[列表中的搜索组件水合后可输入]
    C --> G[排序 Link 可交互后，进入 oldest]
    G --> H{客户端是否已有可复用的目标载荷？}
    H -->|是| I[使用对应 oldest 页面载荷]
    H -->|否| J[服务端 Page 按 oldest 再读取上游]
    J --> I
    I --> K[Back 选择 recent，仍按缓存与请求规则恢复]
    D -->|请求失败| Err[段级 error 界面替换此页面区域]
~~~

## 文件路由把路径落到页面与布局

App Router 把路由写在 `app` 目录：`app/reports/page.tsx` 对应 `/reports`，`app/reports/[reportId]/page.tsx` 对应 `/reports/:reportId`；`layout.tsx` 为一组子路由提供共享外壳，客户端导航时可继续保留。`route.ts` 则按 Hypertext Transfer Protocol（超文本传输协议，HTTP）方法定义 Application Programming Interface（应用程序编程接口，API）端点，不是页面组件；它导出 `GET`、`POST` 等具名函数并返回 `Response`。运行时与部署方式由配置和托管环境决定，放在 Next.js 项目里本身不会自动变成 serverless function（无服务器函数）。

页面收到的动态 `params` 和查询 `searchParams` 都是 Promise，需要在服务端页面中 `await`。对本例来说，`searchParams` 的 `sort` 决定请求哪种顺序；读取它会让页面依赖本次请求，不能把这个值放进不会随导航更新的共享 layout。需要在客户端组件读查询状态时，可使用 `useSearchParams`；若页面本身已经是 Server Component，优先在 Page 读取后把需要的值传给客户端叶节点。

## 服务端与客户端组件在哪条线交接

App Router 的 layout 和 page 默认是 Server Components（服务端组件）。它们能在服务端访问数据库、私有环境变量和后端接口；不进入客户端 JavaScript 包。需要本地 state（状态）、事件处理器、Effect（副作用）或浏览器 API 时，用 `"use client"` 声明 Client Component（客户端组件）的模块边界，并尽量把边界放在实际交互的最小子树。

`"use client"` 不表示“只在浏览器生成 HyperText Markup Language（超文本标记语言，HTML）”。首次访问时，Next.js 会用 Server Component 结果和 Client Component 生成初始 HTML；浏览器先展示静态预览，再下载并 hydrate（水合，让已有标记获得交互）客户端组件。水合要求服务器 HTML 与浏览器首次渲染相同；时间、随机数、地区设置或仅浏览器可读的数据都可能让两边不一致。需要浏览器专属值时，先输出稳定内容，再在首次提交后的 Effect 中读取。后续客户端导航使用 React Server Component Payload（React 服务端组件载荷，RSC payload）更新界面。服务端传给客户端的组件属性（props）必须可序列化；这不是保密机制，可序列化的字符串凭证一旦放进 props 也会进入客户端载荷。函数和数据库连接通常不可序列化，不应作为普通 props 传递。Server Component 可以把已渲染的内容作为 `children` 交给一个 Client Component，但不要从客户端模块图直接导入依赖服务端能力的代码；只传报表展示所需字段，不传内部记录或凭证。

## 用 URL 选排序，并并行加载可独立等待的数据

`page.tsx` 作为 Server Component 读取查询参数。以下例子在得知排序后同时启动报表列表和摘要请求；列表由异步 Server Component 在 `Suspense`（挂起边界）中等待，摘要可独立返回。切换排序的 `Link` 可以直接写在 Server Component 中：链接负责客户端导航、保留路径和片段，若需要服务器重新生成目标载荷，Next.js 再用新的 `searchParams` 运行页面；可复用的客户端载荷则无需这次执行。这是 React Router 浏览器 loader 的替代实现：本例在 Next 服务端向占位上游 `reports.example.test` 请求数据，必须为该主机配置可达的测试服务；它不是浏览器对本应用同源 `/api/reports` 的请求。

~~~tsx
// app/reports/page.tsx
import { Suspense } from "react";
import Link from "next/link";
import { ReportSearch } from "./report-search";

type SortOrder = "recent" | "oldest";
type Report = {
  id: string;
  period: string;
  title: string;
};
type Summary = { totalReports: number };
type PageProps = {
  searchParams: Promise<{ sort?: string | string[] }>;
};

function isReport(value: unknown): value is Report {
  if (typeof value !== "object" || value === null) return false;
  const row = value as Record<string, unknown>;
  return typeof row.id === "string" &&
    typeof row.period === "string" &&
    typeof row.title === "string";
}

function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) throw new Error("Invalid report response");
  return (value as unknown[]).map(row => {
    if (!isReport(row)) throw new Error("Invalid report row");
    return { id: row.id, period: row.period, title: row.title };
  });
}

function parseSummary(value: unknown): Summary {
  if (typeof value !== "object" || value === null) {
    throw new Error("Invalid summary response");
  }
  const summary = value as Record<string, unknown>;
  if (typeof summary.totalReports !== "number" ||
      !Number.isSafeInteger(summary.totalReports) || summary.totalReports < 0) {
    throw new Error("Invalid report count");
  }
  return { totalReports: summary.totalReports };
}

async function getReports(sort: SortOrder): Promise<Report[]> {
  const response = await fetch(
    "https://reports.example.test/api/reports?sort=" + encodeURIComponent(sort),
    { cache: "no-store" }
  );
  if (!response.ok) throw new Error("Could not load reports");
  const payload: unknown = await response.json();
  return parseReports(payload);
}

async function getSummary(): Promise<Summary> {
  const response = await fetch(
    "https://reports.example.test/api/reports/summary",
    { cache: "no-store" }
  );
  if (!response.ok) throw new Error("Could not load report summary");
  const payload: unknown = await response.json();
  return parseSummary(payload);
}

export default async function ReportsPage({ searchParams }: PageProps) {
  const { sort: rawSort } = await searchParams;
  const sort: SortOrder = rawSort === "oldest" ? "oldest" : "recent";
  const reportsPromise = getReports(sort);
  const summaryPromise = getSummary();

  return (
    <main>
      <h1 id="summary">报表摘要</h1>
      <nav aria-label="报表排序">
        <Link
          href="/reports?sort=recent#summary"
          aria-current={sort === "recent" ? "page" : undefined}
        >
          Recent
        </Link>
        {" · "}
        <Link
          href="/reports?sort=oldest#summary"
          aria-current={sort === "oldest" ? "page" : undefined}
        >
          Oldest first
        </Link>
      </nav>

      <Suspense fallback={<p role="status">正在取得摘要…</p>}>
        <ReportSummary promise={summaryPromise} />
      </Suspense>
      <Suspense fallback={<p role="status">正在取得报表…</p>}>
        <ReportList promise={reportsPromise} />
      </Suspense>
    </main>
  );
}

async function ReportSummary({ promise }: { promise: Promise<Summary> }) {
  const summary = await promise;
  return <p>报表数量：{summary.totalReports}</p>;
}

async function ReportList({ promise }: { promise: Promise<Report[]> }) {
  const reports = await promise;
  return <ReportSearch reports={reports} />;
}
~~~

`ReportSearch` 放在独立文件 `app/reports/report-search.tsx`，因为它需要输入 state 和 `onChange`。数据先在服务端取得，再以普通可序列化数组传入：

~~~tsx
"use client";

import { useState } from "react";

type Report = {
  id: string;
  period: string;
  title: string;
};

export function ReportSearch({ reports }: { reports: Report[] }) {
  const [query, setQuery] = useState("");
  const visible = reports.filter(report =>
    report.title.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <section>
      <label>
        搜索报表
        <input value={query} onChange={event => setQuery(event.target.value)} />
      </label>
      <ol aria-label="报表">
        {visible.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}
~~~

输入和本地过滤属于客户端交互；读报表权限、访问私有服务和确定 URL 排序应由服务端负责，但本例没有实现鉴权，真实应用要先在服务端检查用户能否读取这些报表。这里只把少量报表展示字段传到浏览器供本地标题过滤；如果数据量很大或过滤结果受权限、分页影响，应把条件放入 URL 并让服务端按条件查询。`response.json()` 的静态类型不能验证运行时形状；示例在服务边界先把它视为 `unknown`，再逐行检查并投影成三个客户端展示字段，不把上游行对象中可能存在的内部字段顺手传入 RSC payload。摘要中的 `totalReports` 也要求为非负安全整数。

此页的参数策略是：只有单个字符串 `oldest` 选择最早顺序；缺失、`recent`、非法值或重复参数（`string[]`）都回退到 `recent`。这是本例选定的回退契约；React Router 例子则会对其读取到的非法首值返回 400。

`cache: "no-store"` 控制这个 Next 服务端 `fetch` 在实际执行时不要读写持久数据缓存；若 `Page` 执行，它会向上游请求新结果。它不强迫每次 Link/Back 都重新执行服务端 Page：客户端路由可能直接复用已缓存的 React Server Component Payload（React 服务端组件载荷，RSC），因此 `no-store` 也不保证每次浏览器导航都打到上游。当前案例按 URL 保存排序条件，但不冻结返回数据的版本。Next.js 16.4.5 默认的 `auto no cache` 会在动态页面的每次请求中取数，在静态预渲染页面的构建时取数；本例访问 `searchParams`，所以是请求时页面。开启 `cacheComponents`（缓存组件）后，数据默认按请求动态读取；需要跨请求缓存时，使用 `use cache`（缓存指令）明确标出可复用的页面、函数或组件。开发模式的 Hot Module Replacement（热模块替换，HMR）也可能暂时复用 `no-store` 结果，不能把热更新时没变化误判为生产缓存策略。

## 加载、失败和重试各有自己的边界

`app/reports/loading.tsx` 自动为该路由段提供加载界面；更小的 `Suspense` 区域可以让摘要和列表各自出现。等待界面只是表示数据尚未准备好，不会处理读取失败。

~~~tsx
// app/reports/loading.tsx
export default function Loading() {
  return <p role="status">正在打开报表…</p>;
}
~~~

在同一段创建 `app/reports/error.tsx`，用 Client Component 显示可恢复的错误状态。此边界包住当前段的页面和子段，但不会捕获同段 `layout.tsx` 自己抛出的错误；错误向上交给父段边界。Next.js 16.3 起，重试回调 `retry` 已稳定；它会重新读取并渲染边界内的内容。根 `layout.tsx` 本身失败时，使用 `app/global-error.tsx`；全局错误界面要自己提供 `html` 与 `body`。

~~~tsx
// app/reports/error.tsx
"use client";

import { useEffect } from "react";

export default function ReportsError({
  error,
  retry
}: {
  error: unknown;
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <section>
      <p role="alert">报表暂时无法显示。</p>
      <button type="button" onClick={() => retry()}>
        重新读取
      </button>
    </section>
  );
}
~~~

此页的 `Link` 使用客户端过渡，Back 会把地址恢复到 `sort=recent`；App Router 可以复用客户端路由缓存，也可以请求服务器取得对应页面，不能据此断言一定发生网络重取，也不保证恢复某个旧数据快照。若服务端报表本身未改变，页面排序仍回到 May、April；若服务端数据已变，URL 只固定查询条件，不冻结数据版本。在服务端页面函数中没有 React Router 那样公开的 loader `request.signal`，不能因为用户切换路由，就宣称 Next 已停止服务端接口或数据库工作。客户端自己启动的 fetch 可用 `AbortController` 在组件清理时取消等待；服务端请求则应有合适的超时、幂等和数据一致性保护。当服务端实际重新执行 Page 时，才从新 URL 读取对应排序并请求上游。较低层的 History API 与 Back 语义见[浏览器导航与历史如何恢复筛选状态？](../browser/browser-navigation-and-history.md)，React 中的过期响应和查询缓存见[React界面如何维护服务端数据与乐观更新的正确性？](./react-server-state-and-optimistic-updates.md)。

`app/reports/error.tsx` 中的 `retry()` 会重新读取并渲染边界内的页面内容；例如当前 `sort=oldest` 的上游请求失败时，它仍以 oldest 参数重试，成功后列表替换错误界面。它不会悄悄改回 recent。

## 旧版 Pages Router（页面路由器）代码怎样与 App Router 区分

当前例子使用 App Router；旧 Pages Router 应按它自己的运行模型维护，不要把两套 API 拼进一个文件。

| 需求 | Pages Router 旧入口 | 当前 App Router |
|---|---|---|
| 动态路径参数 | `next/router` 的 `router.query` | 页面收到 Promise `params`，`await` 后读取 |
| 查询参数 | `router.query`；自动静态优化期间首屏可能暂时为空，客户端代码应在 Effect（副作用）中等 `router.isReady` | 页面收到 Promise `searchParams`；读取会使用请求时 URL |
| 服务端数据 | `getServerSideProps` 按请求读取；`getStaticProps` 配合 `getStaticPaths` 构建静态页 | 默认 Server Component 读取服务端数据；本篇 `no-store` 示例每次按请求读取 |
| 刷新静态结果 | `getStaticProps` 的 `revalidate` 支持 Incremental Static Regeneration（增量静态再生，ISR） | 按当前 App Router 缓存配置选择重新读取或缓存 |
| API 端点 | `pages/api` 的默认处理器 | `app/**/route.ts` 按 HTTP 方法导出处理器 |

Pages Router 中的 `revalidate: 60` 是允许请求触发再生成的最小间隔，不是后台每分钟准点重建；间隔过后，首个请求可能先读到旧页，同时触发新版本生成。动态路由还要用 `getStaticPaths` 的 `fallback` 决定构建时未列出的路径是直接 404，还是首个请求到来时先生成页面。这个 ISR 语义只用于识别维护中的旧 Pages Router 代码，不与本篇 App Router 的 `no-store` 报表请求混用。

App Router 的客户端导航优先用 `next/link`；需要在客户端代码中编程导航时，使用 `next/navigation` 的 `useRouter`。旧 `next/router`、`router.query` 和 Pages Router 数据函数不适用于 `app/` 页面。当前客户端组件和服务端组件的边界不因保留 Pages Router 而消失：同一项目可以逐段迁移，但每段代码都必须明确属于哪种路由器。

> [!info]- 来源与版本核验（Next.js 16.4.5；2026-11-06）
> - 当前稳定版本：Next.js 官方 [v16.4.5 release](https://github.com/vercel/next.js/releases/tag/v16.4.5)；以下 App Router 文档按官方当前页面核验于 2026-11-06。
> - 服务端与客户端组件的默认归属、首次页面文档、hydrate、可序列化属性与边界范围：[Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)。
> - 服务端到客户端只传界面所需数据及在服务端检查授权：[Data Security — Passing Data from Server to Client](https://nextjs.org/docs/app/guides/data-security#passing-data-from-server-to-client)，核验日期 2026-11-06。
> - 页面 `params` / `searchParams` Promise、查询参数触发动态渲染及共享 layout 不接收 searchParams：[page.js](https://nextjs.org/docs/app/api-reference/file-conventions/page)。
> - `Link` 的客户端导航、预取与历史行为：[Linking and Navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating)、[Link API](https://nextjs.org/docs/app/api-reference/components/link)。
> - Server Component 中读取数据、并行请求与 Suspense 流式返回：[Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data)、[loading.js](https://nextjs.org/docs/app/api-reference/file-conventions/loading)。
> - 水合一致性、Effect 仅在客户端运行，以及首屏输出要求：[React hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)、[React useEffect](https://react.dev/reference/react/useEffect)。
> - `fetch` 缓存默认值、`no-store`、请求期页面与开发热模块替换缓存：[fetch API](https://nextjs.org/docs/app/api-reference/functions/fetch)、[Cache Components](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents)。
> - `loading.tsx`、`error.tsx`、稳定的 `retry` 与 `global-error.tsx`：[loading.js](https://nextjs.org/docs/app/api-reference/file-conventions/loading)、[error.js](https://nextjs.org/docs/app/api-reference/file-conventions/error)，Next.js 16.3 起 `retry` 稳定；核验版本 16.4.5。
> - Pages Router 参数与 `router.isReady`：[Pages Router useRouter](https://nextjs.org/docs/pages/api-reference/functions/use-router)。
> - Pages Router 按请求读取、静态生成与 ISR：[getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props)、[getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths)、[Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration)。
> - App Router 路由端点的方法导出与响应：[Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route)。
> - 本轮隔离重放（2026-11-06）：Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0；Next.js 16.4.5 生产构建核对排序、Back 的 RSC 复用、本地搜索保留及摘要失败后的 retry。上游为本地合成测试服务。
