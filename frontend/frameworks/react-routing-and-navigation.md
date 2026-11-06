# React 路由怎样把地址映射到界面并加载数据？

**案例背景。** 用户打开 `/reports?sort=recent#summary`。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 告诉服务端返回 May、April 两份报表；`#summary` 只用于浏览器定位，不属于 Hypertext Transfer Protocol（超文本传输协议，HTTP）请求。用户点 **Oldest first** 后，地址应新增 `sort=oldest` 历史项，加载结果后行序为 April、May；按 Back 则回到 `sort=recent` 和 May、April。路由把地址、数据请求和界面更新连在一起，不能只把 URL 当作组件选择器。

~~~mermaid
flowchart TD
    A[读取地址 /reports 与查询 sort=recent] --> B[匹配报表路由]
    B --> C[loader（加载器）从地址读 sort]
    C --> D[请求服务端 May、April]
    D --> E[useLoaderData 渲染当前列表]
    E --> F[点击 Oldest first]
    F --> G[PUSH pending：recent 地址和列表暂留]
    G --> H[加载器请求 oldest 数据]
    H --> I{loader 结算}
    I -->|成功| J[提交 oldest URL、历史项与列表]
    I -->|失败| K[提交 oldest URL 与路由错误界面]
    J --> L[Back 的 POP 立即恢复 recent 地址]
    L --> M[loader 等待期间仍显示 oldest 列表]
    M --> N{recent loader 结算后显示列表或错误}
~~~

## 路径、查询和片段各自表达什么

路由器用 pathname（路径名）选择页面，例如 `/reports` 或 `/reports/:reportId`；动态段 `:reportId` 用来标识一份具体报表。多个动态段也能组合成 `/teams/:teamId/reports/:reportId`，`useParams` 读取匹配的路径值。查询参数描述页面当前的筛选、排序或分页状态，像 `?sort=oldest` 可以复制、刷新和由浏览器历史恢复。片段 `#summary` 由浏览器用于定位页面内的位置，客户端能读到它，普通 HTTP 请求不会把它发给服务端。

因此，报表排序由 URL 作为状态来源；用户打开旧地址或按 Back 时，路由从地址重建数据请求和选中状态。不要再用独立的 React state 保存一份互相竞争的 sort。需要低层理解 `pushState`、`popstate` 和片段导航时，见[浏览器导航与历史如何恢复筛选状态？](../browser/browser-navigation-and-history.md)。

## 数据模式先匹配路由，再加载匹配页面的数据

React Router 有 Declarative Mode（声明式模式）、Data Mode（数据模式）和 Framework Mode（框架模式）三种模式。声明式模式适合只把路径匹配到组件；数据模式在路由配置之外增加 loader（加载器）、action（提交处理器）、pending（等待）状态和错误边界；框架模式在数据模式上再提供文件路由、类型生成、Server-Side Rendering（服务端渲染，SSR）和静态渲染。以下用当前 React Router v8.5.1 的数据模式与 `createBrowserRouter` 把同一报表地址接到数据加载器。此例是浏览器端路由；框架模式的 loader 可以运行在服务端，部署边界不同。

下面从首次 `recent` loader 已成功、May 和 April 已显示后开始观察。PUSH 切换时关注三处：浏览器地址、`useNavigation().location` 中的目标地址、当前已提交的列表。POP 的地址栏更新时间不同，所以不能把两种导航压成“地址与列表一起切换”。

| 导航 | loader 等待时 | loader 结算后 |
|---|---|---|
| 点 Oldest first（PUSH） | 地址和已提交列表仍是 recent；`navigation.location` 是 oldest。 | 成功时提交 oldest 地址、历史项和 April/May；失败时仍提交目标地址和历史项，但显示该目标路由的错误界面。 |
| 按 Back（POP） | 浏览器地址和历史指针先回到 recent；已提交路由状态与列表暂留 oldest，`navigation.location` 指向 recent。 | 成功后列表切回 May/April；失败后显示 recent 路由的错误界面。 |

首次打开页面时还没有旧列表；上面的“暂留”只适用于从已显示 recent 的状态导航。

~~~tsx
import {
  createBrowserRouter,
  data,
  isRouteErrorResponse,
  Link,
  Outlet,
  useLoaderData,
  useNavigation,
  useParams,
  useRevalidator,
  useRouteError,
  type LoaderFunctionArgs
} from "react-router";
import { RouterProvider } from "react-router/dom";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };

function isReport(value: unknown): value is Report {
  if (typeof value !== "object" || value === null) return false;
  const row = value as Record<string, unknown>;
  return typeof row.id === "string" &&
    typeof row.period === "string" &&
    typeof row.title === "string";
}

function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) {
    throw data("报表服务返回的不是列表", { status: 502 });
  }
  return (value as unknown[]).map(row => {
    if (!isReport(row)) {
      throw data("报表服务返回了无效行", { status: 502 });
    }
    return row;
  });
}

async function reportsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const rawSort = url.searchParams.get("sort") ?? "recent";
  if (rawSort !== "recent" && rawSort !== "oldest") {
    throw data("不支持这个排序方式", { status: 400 });
  }
  const requestedSort: SortOrder = rawSort;

  const apiUrl = new URL("/api/reports", url.origin);
  apiUrl.searchParams.set("sort", requestedSort);
  const response = await fetch(apiUrl, { signal: request.signal });
  if (!response.ok) {
    throw data("报表读取失败", { status: response.status });
  }

  const payload: unknown = await response.json();
  return { sort: requestedSort, reports: parseReports(payload) };
}

function Root() {
  return <Outlet />;
}

function ReportsPage() {
  const { sort, reports } = useLoaderData<typeof reportsLoader>();
  const navigation = useNavigation();
  const loading = navigation.state !== "idle";
  const pendingSort = navigation.location
    ? new URLSearchParams(navigation.location.search).get("sort")
    : null;

  return (
    <main>
      <h1 id="summary">报表</h1>
      <nav aria-label="报表排序">
        <Link
          to="/reports?sort=recent#summary"
          aria-current={sort === "recent" ? "page" : undefined}
        >
          Recent
        </Link>
        {" · "}
        <Link
          to="/reports?sort=oldest#summary"
          aria-current={sort === "oldest" ? "page" : undefined}
        >
          Oldest first
        </Link>
      </nav>
      {loading && (
        <p role="status">
          {pendingSort === "oldest" ? "正在切换到最早顺序…" : "正在加载所选排序…"}
        </p>
      )}
      <ol aria-label="报表" aria-busy={loading}>
        {reports.map(report => (
          <li key={report.id}>
            <Link to={"/reports/" + encodeURIComponent(report.id)}>
              {report.period} — {report.title}
            </Link>
          </li>
        ))}
      </ol>
    </main>
  );
}

function ReportDetail() {
  const { reportId } = useParams();
  return <h1>报表 ID：{reportId}</h1>;
}

function ReportsErrorBoundary() {
  const error = useRouteError();
  const revalidator = useRevalidator();
  const status = isRouteErrorResponse(error) ? error.status : undefined;

  return (
    <section>
      <p role="alert">
        {status === 400 ? "不支持这个排序方式。" : "报表列表暂时无法显示。"}
      </p>
      {(!isRouteErrorResponse(error) || (status !== undefined && status >= 500)) && (
        <button
          type="button"
          onClick={() => revalidator.revalidate()}
          disabled={revalidator.state !== "idle"}
        >
          重新加载
        </button>
      )}
    </section>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      {
        path: "reports",
        loader: reportsLoader,
        Component: ReportsPage,
        ErrorBoundary: ReportsErrorBoundary
      },
      { path: "reports/:reportId", Component: ReportDetail },
      { path: "*", Component: () => <h1>页面不存在</h1> }
    ]
  }
]);

export function App() {
  return <RouterProvider router={router} />;
}
~~~

`reportsLoader` 从当前 URL 校验 `sort`，再把它传给同源 `/api/reports`；片段不会进入 API URL。这个片段假定应用已挂载 `App`，托管端把 `/reports` 文档请求回退到应用入口，同时让 `/api/reports` 继续进入 API 处理器。PUSH 的目标 loader 结算时，不论成功还是失败都会提交目标地址与历史项：成功时换成目标列表，失败时换成目标错误界面。POP 则先改变浏览器历史地址，等待期间保留已提交的列表；loader 结算后再显示 recent 列表或它的错误界面。按 Back 重新走旧 URL 的 loader，不保证取回首次访问时的缓存快照。`useNavigation` 的 `location` 展示等待中的目标，`useLoaderData` 和 `aria-current` 仍代表当前已提交结果。不要在 `Link` 点击之外再手动调用 `history.pushState`，否则浏览器历史和路由状态会有两套写入者。

## 请求取消、过期响应与错误边界

一次数据导航被新的导航打断时，React Router 会取消前一轮 loader 请求并立即处理新地址。把 loader 收到的 `request.signal` 传给底层 `fetch`，客户端就能停止等待已失效的读取；路由器也不会把过期的页面结果提交到当前导航。**这不等于服务端停止了工作**：请求到达服务端后，服务端仍可能继续处理，所以取消客户端读取不能代替写操作的幂等、权限或事务约束。

loader 返回的数据交给匹配的路由组件；它抛出的 HTTP 状态或异常交给最近的路由 `ErrorBoundary`。报表排序参数的 400 错误会提示排序无效，不提供只会重复失败的重试；网络错误或 5xx 可通过 `useRevalidator` 重跑当前已提交 URL 的 loader。列表项的详细页用 `:reportId` 动态段匹配；真实应用也应给它自己的 loader，并在不存在时抛出 404。当前列表错误边界不会把服务端 404 说成“找不到某一份报表”。

路由错误边界也覆盖它下面的 React 子组件：同步渲染错误和子组件 Effect setup 同步抛出的异常会交给边界；事件处理器、timer 或后续 Promise 拒绝不会被它捕获，应在触发这些工作的位置处理。

## 客户端导航与整页导航怎么选

内部 `Link` 在当前文档中切换路由；外部地址或需要浏览器请求另一个完整文档时，使用普通 `<a>`。读取完整 location 时可用 `useLocation`，有明确的程序化跳转需求（例如提交成功后）时再用 `useNavigate`；普通链接仍应保留锚点语义。客户端导航可保留共同布局和局部界面，但部署端必须把直接打开的 `/reports` **文档请求**交给应用入口；`/api/reports` 仍须由 API 处理器应答，不能一并回退到 HTML。若托管环境无法配置路径回退，可以考虑 `HashRouter`（哈希路由器）；它会占用本例的 URL 片段空间。若同时要支持 `#summary` 锚点，应用还得定义并解析自己的片段格式或负责滚动恢复，不能原样使用这个简单地址。`MemoryRouter`（内存路由器）让地址保存在内存中，适合测试和非浏览器环境。

single-page application（单页应用，SPA）与 multi-page application（多页应用，MPA）描述的是页面导航方式，不是服务端渲染的二选一：React Router 框架模式能服务端渲染，也能选择客户端或静态输出。内容以可爬取文档和无 JavaScript 首屏为主时，完整文档导航通常更直接；需要大量共享界面和路由内数据交互时，客户端导航更容易保留上下文。两种方式都要提供语义化链接、明确的加载与错误状态，并验证直接访问和刷新目标 URL。

React Router v8.5.1 的 `useParams`、`Link` 和路由对象 API 承接归档 v6 例子；老 v5 的 `component={Post}` 与 `withRouter` 是另一套接口，不要混用。v5 的 `StaticRouter` 以固定 location 做服务端匹配；当前 Framework Mode 使用自己的服务端路由入口，不应把它当作同一 API。需要维护旧项目时，先看实际依赖版本，再查对应版本的文档。React 组件的状态更新与提交顺序见[React如何把用户操作变成界面更新？](./react-basics.md)，服务端查询缓存见[React界面如何维护服务端数据与乐观更新的正确性？](./react-server-state-and-optimistic-updates.md)。

> [!info]- 来源与版本核验（React Router v8.5.1；2026-11-06）
> - 当前稳定版本、v8 迁移边界与运行时最低版本：[React Router Changelog](https://reactrouter.com/changelog)，v8.5.1，2026-10-27。
> - 三种模式的职责和框架模式的服务端渲染 / 静态渲染能力：[Picking a Mode](https://reactrouter.com/start/modes)，核验日期 2026-11-06。
> - 路由对象、嵌套页、动态段和 loader：[Routing](https://reactrouter.com/start/data/routing)、[Route Object](https://reactrouter.com/start/data/route-object)、[Data Loading](https://reactrouter.com/start/data/data-loading)，React Router v8.5.1，核验日期 2026-11-06。
> - 导航提交、等待界面和 pending 位置：[Navigating](https://reactrouter.com/start/data/navigating)、[Pending UI](https://reactrouter.com/start/data/pending-ui)、[useNavigation](https://reactrouter.com/api/hooks/useNavigation)，React Router v8.5.1，核验日期 2026-11-06。
> - 浏览器入口 `react-router/dom` 提供带 `react-dom` flushSync 的 `RouterProvider`：[RouterProvider](https://reactrouter.com/api/data-routers/RouterProvider)，React Router v8.5.1，核验日期 2026-11-06。
> - 当前 location、程序化导航和 loader 重验证的 hook：[useLocation](https://reactrouter.com/api/hooks/useLocation)、[useNavigate](https://api.reactrouter.com/v8/functions/react-router.useNavigate.html)、[useRevalidator](https://api.reactrouter.com/v8/functions/react-router.useRevalidator.html)，React Router v8.5.1，核验日期 2026-11-06。
> - 导航打断、loader 取消和服务端仍可能处理请求：[Race Conditions](https://reactrouter.com/explanation/race-conditions)，React Router v8.5.1，核验日期 2026-11-06。
> - 路由错误边界、最近边界和 404 响应：[Error Boundaries](https://reactrouter.com/how-to/error-boundary)，React Router v8.5.1，核验日期 2026-11-06。
> - React 子组件同步错误由边界兜底、事件处理和异步回调不在该范围：[React Component — Catching rendering errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，核验日期 2026-11-06。
> - 本轮隔离重放（2026-11-06）：Node 26.11.1、React 19.3.1、Chrome 157、Playwright 1.65.0；React Router 8.5.1 核对 PUSH/POP 等待期的地址与列表、502 错误提交与重试；相关浏览器排序用例通过。接口为本地合成测试服务。
