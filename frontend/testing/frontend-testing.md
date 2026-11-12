# 前端测试怎样证明报表排序、历史恢复和发布产物正确？

**案例背景。** 用户打开 `/reports?sort=recent#summary`，看到 May、April。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端返回该顺序；点击 **Oldest first** 后，地址变成 `sort=oldest`，列表为 April、May；按 Back 则回到 recent 和 May、April。测试要验证用户看到的结果、真实地址历史和请求边界；点击事件触发过或内部状态等于某值，都不足以证明整条流程可用。

## 先按风险选择测试边界

| 测试边界 | 适合验证 | 报表排序例子 |
|---|---|---|
| 单元测试 | 无 Document Object Model（文档对象模型，DOM）的纯转换与解析 | 无效 `sort` 被拒绝；报表响应字段映射正确。 |
| 组件集成测试 | 组件、Hook（钩子）、可访问控件和请求边界一起工作 | 点排序控件后显示等待状态，成功后行序变为 April、May，失败时出现错误提示。 |
| 浏览器端到端测试 | 浏览器历史、真实 URL、路由、资源和服务组合 | 从 recent 点 Oldest first，确认 URL 和行序，再按 Back 恢复 recent。 |

保持单元测试简单纯粹；请求和 React 组件的关系用组件测试；浏览器 Back、片段锚点、生产资源路径等风险由真实浏览器覆盖。组件测试不模拟出真实浏览器历史时，不能替代 Back 测试。

## 用用户能找到的名称和内容断言

React Testing Library 的查询名称表达等待契约：`getByRole` 表示元素现在应存在且唯一；`queryByRole` 在没有匹配时返回 `null`，适合断言不存在，但有多个匹配仍会抛错；`findByRole` 返回 Promise，等待唯一匹配出现。优先使用角色和可访问名称，避免检查组件内部状态、CSS class 或 hook 调用次数。

组件集成测试可以用 `user-event` 的用户操作模拟器执行点击和键盘交互；异步数据出现时等待可见行或状态，而不是固定睡眠。`waitFor` 的回调必须在未满足时抛出断言错误，返回 `false` 不会要求它重试；也不要把点击等副作用放进会重跑的回调。完整异步 Mock（模拟）与计时例子见[Jest 怎样验证报表请求中的异步状态和结果？](jest-async-tests-and-mocks.md)。

React Testing Library 16.3.3 也从 `@testing-library/react` 导出 `renderHook`，适合单独验证作为复用接口的 Hook 契约；只被一个组件使用的 Hook 通常直接测那个组件，更能表达用户行为。Testing Library 的 `render` 和 `user-event` 操作工具已处理一般交互的 React `act` 边界；测试从这些工具外部直接触发更新时，再显式包在 `act` 中。快照适合记录稳定的小结构，较大的快照本身说不清用户需要看到什么，排序和错误行为仍应使用有含义的断言。

## 浏览器测试应经过同一条 URL 和 Back 流程

下面的端到端测试约定被测 React Router 数据模式（Data Mode）页面部署在站点根路径，并将 Playwright `baseURL` 指向该站点根地址：浏览器 loader（路由数据加载器）从当前页面 URL 读取唯一的 `sort` 值，向同源 `GET /api/reports?sort=…` 请求报表，再按响应顺序渲染名为“报表”的列表；“Oldest first”链接将地址变为 `/reports?sort=oldest#summary` 并创建历史项，Back 恢复 recent 地址。若应用注册 Service Worker（服务工作线程），还须在 Playwright `use` 配置中阻断它，使 `page.route` 能观察该请求。`page.route` 只拦截浏览器页面发出的请求；Next.js Server Component（服务端组件）在服务器进程发出的上游 `fetch` 不会经过它，要为 Next.js 配置可达的服务端测试上游。

测试为 recent 和 oldest 两种响应分别设置只会由该响应提供的标记标题。除了检查地址和行序，测试还用精确的来源（origin）与路径名（pathname）限定路由，记录整个流程收到的 `sort` 值，并要求两种排序都至少命中过一次。预取也可以满足该请求要求，所以不固定请求发生在点击的哪个时点或总次数；各页的独有标题则证明页面消费的是对应排序的响应，而不是把 recent 行在客户端反转：

不用展开代码，可以先核对这三次页面结果：

| 用户步骤 | 页面地址中的排序 | 应看到的列表 |
| --- | --- | --- |
| 打开报表 | `sort=recent` | May、April；两行标题都带 `Recent API:`。 |
| 点击 Oldest first | `sort=oldest` | April、May；两行标题都带 `Oldest API:`。 |
| 按 Back | `sort=recent` | 恢复 May、April 及 `Recent API:` 标题。 |

三个地址都保留 `#summary`。标题标记只属于测试输入：即使应用发了 oldest 请求，却丢弃响应、只倒序排列旧行，第二步也会因仍显示 `Recent API:` 而失败。

> [!example]- 完整 Playwright 浏览器测试
>
> ~~~ts
> import { expect, test } from "@playwright/test";
>
> const recentRows = [
>   {
>     id: "may-recent",
>     period: "May",
>     title: "Recent API: Operations"
>   },
>   {
>     id: "april-recent",
>     period: "April",
>     title: "Recent API: Finance"
>   }
> ];
> const oldestRows = [
>   {
>     id: "april-oldest",
>     period: "April",
>     title: "Oldest API: Finance"
>   },
>   {
>     id: "may-oldest",
>     period: "May",
>     title: "Oldest API: Operations"
>   }
> ];
>
> test(
>   "sorts reports and restores the previous URL with Back",
>   async ({ page }) => {
>     const configuredBaseURL = test.info().project.use.baseURL;
>     if (typeof configuredBaseURL !== "string") {
>       throw new Error(
>         "This test requires a configured Playwright baseURL."
>       );
>     }
>
>     const appOrigin = new URL(configuredBaseURL).origin;
>     const reportURL = (sort: "recent" | "oldest") => {
>       const url = new URL("/reports", configuredBaseURL);
>       url.searchParams.set("sort", sort);
>       url.hash = "summary";
>       return url.href;
>     };
>     const servedSorts = new Set<string>();
>
>     await page.route(
>       url =>
>         url.origin === appOrigin && url.pathname === "/api/reports",
>       async route => {
>         expect(route.request().method()).toBe("GET");
>         const requestURL = new URL(route.request().url());
>         const sorts = requestURL.searchParams.getAll("sort");
>         expect(sorts).toHaveLength(1);
>         const sort = sorts[0];
>         if (sort !== "recent" && sort !== "oldest") {
>           throw new Error(
>             `Unexpected sort value: ${sort ?? "(missing)"}`
>           );
>         }
>         servedSorts.add(sort);
>         const rows = sort === "oldest" ? oldestRows : recentRows;
>         await route.fulfill({
>           status: 200,
>           contentType: "application/json",
>           body: JSON.stringify(rows)
>         });
>       }
>     );
>
>     await page.goto(reportURL("recent"));
>     const rows = page
>       .getByRole("list", { name: "报表" })
>       .getByRole("listitem");
>     await expect(rows).toHaveText([
>       "May — Recent API: Operations",
>       "April — Recent API: Finance"
>     ]);
>
>     await page.getByRole("link", { name: "Oldest first" }).click();
>     await expect(page).toHaveURL(reportURL("oldest"));
>     await expect(rows).toHaveText([
>       "April — Oldest API: Finance",
>       "May — Oldest API: Operations"
>     ]);
>
>     await page.goBack();
>     await expect(page).toHaveURL(reportURL("recent"));
>     await expect(rows).toHaveText([
>       "May — Recent API: Operations",
>       "April — Recent API: Finance"
>     ]);
>
>     expect(servedSorts.has("recent")).toBe(true);
>     expect(servedSorts.has("oldest")).toBe(true);
>   }
> );
> ~~~

这类测试把 `#summary` 留在页面地址，并让 API 只按查询参数读取排序；浏览器不会把片段发给服务端。URL 断言只证明片段仍在地址栏，不证明页面滚动到了 `id="summary"` 的位置；若页面确有滚动契约，应单独断言锚点与视口位置。DOM 角色查询按 DOM 的角色和可访问名称匹配，不证明屏幕阅读器实际播报。`page.route` 不会拦截已被 Service Worker 接管的请求，Playwright 项目配置须让本例可观察到预期的请求，例如设置 `serviceWorkers: "block"`；启用路由还会禁用 HTTP 缓存，因此不能用此 Mock 测试证明浏览器缓存行为。测试应用可以把 `page.route` 换成测试服务或 Mock Service Worker（请求拦截工具），但不要在同一案例里一边 Mock 页面实现、一边又声称覆盖了真实路由。

## 验证将发布的构建产物

开发热更新服务主要验证开发链路，不会完整覆盖打包后的资源地址、分块加载或部署路径。常用交付检查顺序是：

~~~text
typecheck -> unit/component tests -> production build
  -> serve that build -> critical browser journey
  -> promote the same artifact
~~~

用接近生产的服务器启动刚生成的构建产物，再冷开一个深链或刷新页面，确认实际代码分块（chunk）加载并执行关键用户流程；本例从根路径进入且 Mock 了 API，所以本地构建检查只覆盖该配置下的前端资源与行为。目标部署若使用子路径、不同的单页应用（SPA）回退规则、真实 API 代理或 Service Worker，另在该基础路径（base）与服务器配置下冷开深链/刷新，并按发布风险决定是否使用真实 API。使用 Vite 时，`vite preview` 可以本地预览刚构建的 `dist`，但官方不把它定位为生产服务器。发布时晋级同一份通过检查的产物，避免重新构建后部署了另一份代码。Source map（源码映射）应绑定发布版本并受控上传；若 `.map` 文件仍随产物发布且可从公开路径访问，隐藏 sourceMappingURL 注释本身不会阻止外部直接请求该文件。公共的构建产物晋级、运行时和发布门禁见[应用部署与持续集成及持续交付（CI/CD）](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)，通用测试边界见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)。

> [!info]- 来源与版本核验（React Router 8.5.1；React Testing Library 16.3.3；user-event 14.6.10；Playwright 1.65.0；Vite 8.3.8；2026-11-12）
> - React Testing Library 当前包版本：[npm package](https://www.npmjs.com/package/@testing-library/react)，16.3.3；角色查询、异步行为、`renderHook` 与 `act`：[ByRole](https://testing-library.com/docs/queries/byrole/)、[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)、[API](https://testing-library.com/docs/react-testing-library/api/)，核验日期 2026-11-12。
> - user-event 当前版本：[npm package](https://www.npmjs.com/package/@testing-library/user-event)，14.6.10；用户交互模型与假时钟设置：[Introduction](https://testing-library.com/docs/user-event/intro/)、[Options](https://testing-library.com/docs/user-event/options/)，核验日期 2026-11-12。
> - React Router Data Mode 用 route `loader` 提供组件数据：[Data Loading](https://reactrouter.com/start/data/data-loading)；本例使用 React Router 8.5.1 实跑。
> - Playwright 当前包版本：[npm package](https://www.npmjs.com/package/@playwright/test)，1.65.0；浏览器端断言、精确请求拦截、URL predicate 与 Service Worker 边界：[Assertions](https://playwright.dev/docs/test-assertions)、[Page route](https://playwright.dev/docs/api/class-page#page-route)、[Network](https://playwright.dev/docs/network)、[Configuration (use)](https://playwright.dev/docs/test-use-options)，核验日期 2026-11-12。
> - 测试产物服务器配置：[Playwright webServer](https://playwright.dev/docs/test-webserver)。
> - Vite 当前包版本：[npm package](https://www.npmjs.com/package/vite)，8.3.8；`vite preview` 用于本地预览构建产物，不是生产服务器：[Vite CLI](https://vite.dev/guide/cli.html#vite-preview)、[Static deployment](https://vite.dev/guide/static-deploy.html)，核验日期 2026-11-12。
