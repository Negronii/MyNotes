# 前端测试怎样证明报表排序、历史恢复和发布产物正确？

**案例背景。** 用户打开 `/reports?sort=recent#summary`，看到 May、April。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端返回该顺序；点击 **Oldest first** 后，地址变成 `sort=oldest`，列表为 April、May；按 Back 则回到 recent 和 May、April。测试要验证用户看到的结果、真实地址历史和请求边界；点击事件触发过或内部状态等于某值，都不足以证明整条流程可用。

~~~mermaid
flowchart LR
    A[纯函数与契约] --> B[组件交互和异步状态]
    B --> C[真实浏览器路由与 Back]
    C --> D[生产构建资源]
    D --> E[发布同一份已验证产物]
~~~

## 先按风险选择测试边界

| 测试边界 | 适合验证 | 报表排序例子 |
|---|---|---|
| 单元测试 | 无 Document Object Model（文档对象模型，DOM）的纯转换与解析 | 无效 `sort` 被拒绝；报表响应字段映射正确。 |
| 组件集成测试 | 组件、Hook（钩子）、可访问控件和请求边界一起工作 | 点排序控件后显示等待状态，成功后行序变为 April、May，失败时出现错误提示。 |
| 浏览器端到端测试 | 浏览器历史、真实 URL、路由、资源和服务组合 | 从 recent 点 Oldest first，确认 URL 和行序，再按 Back 恢复 recent。 |

保持单元测试简单纯粹；请求和 React 组件的关系用组件测试；浏览器 Back、片段锚点、生产资源路径等风险由真实浏览器覆盖。组件测试不模拟出真实浏览器历史时，不能替代 Back 测试。

## 用用户能找到的名称和内容断言

React Testing Library 的查询名称表达等待契约：`getByRole` 表示元素现在应存在且唯一；`queryByRole` 适合断言它不存在；`findByRole` 返回 Promise 并等待元素出现。优先使用角色和可访问名称，避免检查组件内部状态、CSS class 或 hook 调用次数。

组件集成测试可以用 `user-event` 的用户操作模拟器执行点击和键盘交互；异步数据出现时等待可见行或状态，而不是固定睡眠。`waitFor` 的回调必须在未满足时抛出断言错误，返回 `false` 不会要求它重试；也不要把点击等副作用放进会重跑的回调。完整异步 Mock 与计时例子见[Jest 怎样验证报表请求中的异步状态和结果？](jest-async-tests-and-mocks.md)。

React Testing Library 16.3.3 也从 `@testing-library/react` 导出 `renderHook`，可单独验证有复用价值的 Hook 契约；只被一个组件使用的 Hook 通常直接测那个组件更能表达用户行为。Testing Library 的 render 和 user-event helper 已处理一般交互的 React `act` 边界；测试从 helper 外部直接触发更新时，再显式包在 `act` 中。快照适合记录稳定的小结构，较大的快照本身说不清用户需要看到什么，排序和错误行为仍应使用有含义的断言。

## 浏览器测试应经过同一条 URL 和 Back 流程

下面的端到端测试是 React Router Data Mode 浏览器 loader 加同源 `/api/reports` 的方案。它假定 Playwright 配置了应用 `baseURL` 与启动待测应用的 `webServer`。`page.route` 只拦截浏览器页面发出的请求；Next Server Component 在服务器进程发出的上游 `fetch` 不会经过它，要为 Next 配置可达的服务端测试上游。此处在浏览器 API 边界按 `sort` 返回固定数据，断言链接、地址、列表和浏览器历史；拦截器中的断言只检查实际出现的请求，URL 和行序断言验证界面行为；它们不证明每次导航一定发生网络调用。若还要证明应用确实接入接口，可增加至少一次拦截命中的断言，或用不会出现在初始静态页面中的 fixture 值。这里不固定请求次数，因为预取、路由再验证或返回历史项可能影响网络调用次数：

~~~ts
import { expect, test } from "@playwright/test";

const recentRows = [
  { id: "may", period: "May", title: "Operations" },
  { id: "april", period: "April", title: "Finance" }
];
const oldestRows = [...recentRows].reverse();

test("sorts reports and restores the previous URL with Back", async ({ page }) => {
  await page.route(/\/api\/reports(?:\?.*)?$/, async route => {
    expect(route.request().method()).toBe("GET");
    const url = new URL(route.request().url());
    const sorts = url.searchParams.getAll("sort");
    expect(sorts).toHaveLength(1);
    const sort = sorts[0];
    expect(["recent", "oldest"]).toContain(sort);
    const rows = sort === "oldest" ? oldestRows : recentRows;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(rows)
    });
  });

  await page.goto("/reports?sort=recent#summary");
  const rows = page.getByRole("list", { name: "报表" }).getByRole("listitem");
  await expect(rows).toHaveText([
    "May — Operations",
    "April — Finance"
  ]);

  await page.getByRole("link", { name: "Oldest first" }).click();
  await expect(page).toHaveURL(/\/reports\?sort=oldest#summary$/);
  await expect(rows).toHaveText([
    "April — Finance",
    "May — Operations"
  ]);

  await page.goBack();
  await expect(page).toHaveURL(/\/reports\?sort=recent#summary$/);
  await expect(rows).toHaveText([
    "May — Operations",
    "April — Finance"
  ]);
});
~~~

这类测试把 `#summary` 留在页面地址，并让 API 只按查询参数读取排序；浏览器不会把片段发给服务端。URL 断言只证明片段仍在地址栏，不证明页面滚动到了 `id="summary"` 的位置；若页面确有滚动契约，应单独断言锚点与视口位置。DOM 角色查询也只证明可访问树中的结构和名称，不证明屏幕阅读器实际播报。测试应用可以把 `page.route` 换成测试服务或 Mock Service Worker（请求拦截工具），但不要在同一案例里一边 Mock 页面实现、一边又声称覆盖了真实路由。

## 验证将发布的构建产物

开发热更新服务主要验证开发链路，不会完整覆盖打包后的资源地址、分块加载或部署路径。常用交付检查顺序是：

~~~text
typecheck -> unit/component tests -> production build
  -> serve that build -> critical browser journey -> promote the same artifact
~~~

用接近生产的服务器启动刚生成的构建产物，再执行一次上面的关键用户流程；使用 Vite 时，`vite preview` 可以本地预览刚构建的 `dist`，但官方不把它定位为生产服务器。发布时晋级同一份通过检查的产物，避免重新构建后部署了另一份代码。Source map（源码映射）应绑定发布版本并受控上传；隐藏注释不会自动阻止外部直接访问 map 文件。公共的构建产物晋级、运行时和发布门禁见[应用部署与持续集成及持续交付（CI/CD）](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)，通用测试边界见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)。

> [!info]- 来源与版本核验（React Testing Library 16.3.3；user-event 14.6.8；Playwright 1.65.0；2026-11-06）
> - React Testing Library 当前包版本：[npm package](https://www.npmjs.com/package/@testing-library/react)，16.3.3；角色查询和异步行为：[ByRole](https://testing-library.com/docs/queries/byrole/)、[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)。
> - `renderHook` API 与测试单个 Hook 的适用边界：[React Testing Library API](https://testing-library.com/docs/react-testing-library/api/#renderhook)，v16.3.3，核验日期 2026-11-06。
> - user-event 当前版本：[npm package](https://www.npmjs.com/package/@testing-library/user-event)，14.6.8；用户交互模型：[Introduction](https://testing-library.com/docs/user-event/intro/)，核验日期 2026-11-06。
> - Playwright 当前包版本：[npm package](https://www.npmjs.com/package/@playwright/test)，1.65.0；浏览器端断言与拦截请求：[Assertions](https://playwright.dev/docs/test-assertions)、[Page route](https://playwright.dev/docs/api/class-page#page-route)，核验日期 2026-11-06。
> - 测试产物服务器配置：[Playwright webServer](https://playwright.dev/docs/test-webserver)。
> - `vite preview` 用于本地预览构建产物，不是生产服务器：[Vite CLI](https://vite.dev/guide/cli.html#vite-preview)、[Static deployment](https://vite.dev/guide/static-deploy.html)，按 Vite v8.3.5 官方文档核验于 2026-11-06。
