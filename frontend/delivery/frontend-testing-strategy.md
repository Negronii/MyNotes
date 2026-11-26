# 前端测试该在哪一层证明什么？

一项前端功能是否正确，往往要同时证明几件性质不同的事：数据转换对不对，组件在等待、成功、失败时显示什么，真实浏览器里地址和历史是否按预期变化，以及将要发布的那份构建产物能不能跑起来。本章说明每件事该由哪一层测试证明、断言该怎么写才真正证明了它，以及每种断言证明不了什么。读者手上有报表页的行为约定，以及前两章讲的构建与发布流程。

## 要证明的结论

沿用[主线一的报表页](../browser/from-url-to-interactive-page.md)。本章要证明的是排序这条流程：

1. 用户打开 `/reports/42?sort=recent#summary`，`ol#reports` 里是 May、April 两行（业务 ID `r-104`、`r-103`），“最近优先”（`Most recent`）按钮处于按下状态（`aria-pressed="true"`）。
2. 点击“最早优先”（`Oldest first`）后，地址变成 `/reports/42?sort=oldest#summary` 并新增一条历史记录，列表变为 April、May，“最早优先”变为按下状态。
3. 按 Back，地址回到 `sort=recent`，列表恢复 May、April。

本章新增一个标识符：页面向同源的 `GET /api/reports/42?sort=…` 读取按该顺序排好的行，每行形如 `{ id: "r-104", label: "May report" }`。

“点击事件触发了”或“组件内部 state 等于 `oldest`”都不足以证明这条流程可用。测试要验证的是用户看到的结果、真实的地址与历史，以及请求边界上发生了什么。

## 按风险选测试边界

| 测试边界 | 适合证明 | 报表排序中的例子 |
|---|---|---|
| 单元测试 | 不涉及 DOM 的纯转换与解析 | 非法的 `sort` 值被拒绝；接口字段正确映射成行数据 |
| 组件集成测试 | 组件、Hook、可访问控件和请求边界一起工作 | 点“最早优先”后显示等待状态并保留旧行；成功后行序变为 April、May；失败时出现错误提示 |
| 浏览器端到端测试 | 浏览器历史、真实 URL、路由、资源加载和服务组合 | 从 recent 点“最早优先”，确认 URL 和行序，再按 Back 恢复 recent |

分工的原则是让每种风险落在能真实复现它的最低一层：

- 单元测试保持纯粹，不碰 DOM 和网络。
- 请求与组件状态的关系放在组件测试里，用可控的 Mock 制造等待、成功和失败。
- 浏览器 Back、片段锚点、生产资源路径这类风险只有真实浏览器能覆盖。组件测试没有真实的会话历史，不能替代 Back 测试。

把风险对应到可证明边界的通用方法见[怎样用测试边界验证一次报表服务改动？](../../engineering-foundations/testing/software-testing-strategy.md)；本章只讲前端特有的边界。

## 组件测试：按用户能找到的角色和名称查询

组件测试常用 React Testing Library（RTL）。它的查询函数名本身就是一份契约，说明“现在应该有几个、要不要等”：

| 查询 | 没有匹配 | 多个匹配 | 适合 |
|---|---|---|---|
| `getByRole` | 立即抛错 | 抛错 | 断言元素此刻存在且唯一 |
| `queryByRole` | 返回 `null` | 抛错 | 断言元素不存在 |
| `findByRole` | 返回的 Promise 在超时后拒绝 | Promise 拒绝 | 等待一个异步出现的唯一元素 |

每种都有 `getAllBy…`、`queryAllBy…`、`findAllBy…` 的复数版本，用于本来就有多个匹配的场合，例如列表项。

**优先按角色和可访问名称查询。** `getByRole("button", { name: "Oldest first" })` 找的是用户和辅助技术看到的那个按钮：它的可访问名称来自按钮里的文字，`aria-hidden` 的箭头图标不参与。角色查询还能带状态，例如 `{ name: "Oldest first", pressed: true }` 直接断言按下状态。这样写的测试不依赖组件内部 state、CSS class 或 Hook 调用次数，重构实现时不会无故失败，而按钮名字或角色真被改坏时一定失败。

其余几条约定：

- **用户操作用 `user-event`。** 它按真实用户的事件序列执行点击和键盘输入，比直接派发单个事件更接近浏览器行为。
- **等待可见结果，不固定睡眠。** 异步数据出现时等可见的行或状态提示；等待和重试的细节、`act` 边界和假时钟见下一章[异步代码和外部依赖怎样测才可信？](async-tests-and-mocks.md)。
- **Hook 契约用 `renderHook`。** 作为复用接口发布的 Hook 可以单独测；只被一个组件使用的 Hook，直接测那个组件更能表达用户行为。
- **快照只记录稳定的小结构。** 大快照说不清用户需要看到什么，排序和错误行为应写有含义的断言。

## 浏览器测试：走一遍真实的 URL 与 Back

端到端测试用 Playwright 驱动真实浏览器。下面的测试只依赖报表页对外的契约，不关心页面用路由库的 loader（见[路由怎样把 URL 变成已提交的数据和界面？](../ui-state/routing-and-loaders.md)）还是手写 `pushState` 实现：

- Playwright 的 `baseURL` 只给站点 origin（如 `http://localhost:4173`），测试自己拼出 `/reports/42?…` 这样的完整路径。
- 页面从当前 URL 读取唯一的 `sort` 值，请求 `GET /api/reports/42?sort=…`，按响应顺序把每行的 `label` 渲染进 `ol#reports`。
- “最早优先”把地址改为 `sort=oldest` 并新增历史记录；Back 恢复 recent 地址并重新显示 recent 的数据。

测试为 recent 和 oldest 两种响应各准备一组**只属于该响应的行文字**：`label` 带 `Recent API:` 或 `Oldest API:` 前缀。先不看代码，三步的预期是：

| 用户步骤 | 地址中的排序 | “最早优先”按下 | 应看到的列表 |
| --- | --- | --- | --- |
| 打开报表 | `sort=recent` | 否 | May、April，行文字带 `Recent API:` |
| 点击“最早优先” | `sort=oldest` | 是 | April、May，行文字带 `Oldest API:` |
| 按 Back | `sort=recent` | 否 | 恢复 May、April 及 `Recent API:` 前缀 |

三个地址都保留 `#summary`。

> [!example]- 完整 Playwright 测试
>
> 项目配置需要设置 `baseURL`，并在 `use` 中设置 `serviceWorkers: "block"`（原因见下文“page.route 拦得到什么”）。报表页只有 `ol#reports` 一个列表，所以直接按 `list` 角色定位；页面有多个列表时，应给它一个可访问名称再按名称查询。
>
> ~~~ts
> import { expect, test } from "@playwright/test";
>
> type Sort = "recent" | "oldest";
>
> const rowsBySort: Record<Sort, { id: string; label: string }[]> = {
>   recent: [
>     { id: "r-104", label: "Recent API: May report" },
>     { id: "r-103", label: "Recent API: April report" }
>   ],
>   oldest: [
>     { id: "r-103", label: "Oldest API: April report" },
>     { id: "r-104", label: "Oldest API: May report" }
>   ]
> };
>
> test("sorts the report and restores the previous URL with Back", async ({ page }) => {
>   const baseURL = test.info().project.use.baseURL;
>   if (typeof baseURL !== "string") {
>     throw new Error("This test requires a configured Playwright baseURL.");
>   }
>   const appOrigin = new URL(baseURL).origin;
>   const reportURL = (sort: Sort) => {
>     const url = new URL("/reports/42", baseURL);
>     url.searchParams.set("sort", sort);
>     url.hash = "summary";
>     return url.href;
>   };
>   const servedSorts = new Set<Sort>();
>
>   await page.route(
>     url => url.origin === appOrigin && url.pathname === "/api/reports/42",
>     async route => {
>       expect(route.request().method()).toBe("GET");
>       const sorts = new URL(route.request().url()).searchParams.getAll("sort");
>       expect(sorts).toHaveLength(1);
>       const sort = sorts[0];
>       if (sort !== "recent" && sort !== "oldest") {
>         throw new Error(`Unexpected sort value: ${sort ?? "(missing)"}`);
>       }
>       servedSorts.add(sort);
>       await route.fulfill({ json: rowsBySort[sort] });
>     }
>   );
>
>   const rows = page.getByRole("list").getByRole("listitem");
>   const oldestButton = page.getByRole("button", { name: "Oldest first" });
>
>   await page.goto(reportURL("recent"));
>   await expect(rows).toHaveText(["Recent API: May report", "Recent API: April report"]);
>   await expect(oldestButton).toHaveAttribute("aria-pressed", "false");
>
>   await oldestButton.click();
>   await expect(page).toHaveURL(reportURL("oldest"));
>   await expect(oldestButton).toHaveAttribute("aria-pressed", "true");
>   await expect(rows).toHaveText(["Oldest API: April report", "Oldest API: May report"]);
>
>   await page.goBack();
>   await expect(page).toHaveURL(reportURL("recent"));
>   await expect(oldestButton).toHaveAttribute("aria-pressed", "false");
>   await expect(rows).toHaveText(["Recent API: May report", "Recent API: April report"]);
>
>   expect([...servedSorts].sort()).toEqual(["oldest", "recent"]);
> });
> ~~~

## 怎样证明页面真的用了拦截返回的数据

拦截请求再断言页面，有一个容易漏掉的缺口：页面发了 oldest 请求，却丢弃响应，只把 recent 的旧行在客户端倒序排列。行序照样是 April、May，只检查行序的测试会通过。

上面的测试用三道检查堵住这个缺口：

1. **按响应独有的标记断言。** oldest 响应的行文字都带 `Oldest API:`。上面那种错误实现在第二步仍显示 `Recent API:`，断言失败。这一步证明页面**消费**了对应的响应，而不只是**发出**了请求。
2. **精确限定被拦截的请求。** 路由谓词同时匹配 origin 和 pathname，处理函数再要求方法是 `GET`、`sort` 恰好出现一次且取值合法；不合约定的请求让测试失败，而不是被悄悄放过。
3. **记录整个流程收到的排序值。** `servedSorts` 最后必须同时包含 recent 和 oldest。测试不规定请求发生在点击前后的哪个时刻，也不规定总次数，因为预取或 Back 时重新请求都是合法实现；它只要求两种排序都确实经过了拦截。

> [!info] 实跑记录（Playwright 1.65.0，Chrome 158.0.8127.89，2026-11-26）
> 上面的测试对一个按本节契约实现的最小页面实跑通过。把页面改成“发 oldest 请求但只倒序 recent 行”后，测试在第二步的行文本断言处失败。

## page.route 拦得到什么

`page.route` 只能拦截**这个浏览器页面**发出的请求，几条边界决定了 Mock 测试能证明的范围：

- **Service Worker 接管的请求拦不到。** 应用若注册了 Service Worker，请求可能由它处理而不经过 `page.route`。本例要求在 Playwright 配置里设置 `serviceWorkers: "block"`。
- **服务端发出的请求拦不到。** 例如 Next.js Server Component 在服务器进程里发出的上游 `fetch` 不经过浏览器，要为它配置测试用的上游服务。
- **启用路由会禁用 HTTP 缓存。** 所以这类测试不能证明浏览器缓存行为；缓存语义见[发布新版本时，怎样让缓存和还开着的旧页面都不出错？](hashed-release-and-caching.md)。
- **Mock 替换的部分不在证明范围内。** 可以把 `page.route` 换成测试服务或 Mock Service Worker，但不要在同一个测试里一边 Mock 掉页面依赖的实现，一边声称覆盖了真实路由或真实 API。

## URL 和 DOM 断言证明不了什么

每种断言只证明它观察到的那一层：

- **`toHaveURL` 只证明地址栏里的地址。** `#summary` 指向摘要标题 `h1#summary`，它留在地址里，但片段不会发给服务端（URL 各分量的分工见[地址变了，浏览器什么时候加载新文档，界面状态何时该写进 URL？](../browser/navigation-history-and-url-state.md)），所以 API 只能按查询参数读取排序。URL 断言也不证明页面滚到了这个标题；页面若有滚动契约，要单独断言锚点与视口位置。
- **角色查询不证明读屏实际播报。** `getByRole` 按 DOM 计算出的角色和可访问名称匹配，说明无障碍树里有这个按钮，不说明某款屏幕阅读器会怎样读它。
- **Mock 响应不证明真实服务。** 拦截测试证明的是“给定这种响应，页面行为正确”；真实 API 的契约要由服务端测试或接真实上游的测试证明。

## 交付检查：测将要发布的那份产物

开发服务器主要验证开发链路，不会完整覆盖打包后的资源地址、代码分块（chunk）加载和部署路径。常用的交付检查顺序是：

~~~text
typecheck -> unit/component tests -> production build
  -> serve that build -> critical browser journey
  -> promote the same artifact
~~~

几个要点：

- **在构建产物上跑关键旅程。** 用接近生产的服务器启动刚生成的产物，冷开一个深链或刷新页面，确认实际的 chunk 能加载并执行，再走一遍上面的排序流程。本例用本地服务器提供产物，并 Mock 了 API，所以只覆盖这种配置下的前端资源与行为。
- **部署配置不同就另测。** 目标环境若使用另一个 base 路径、不同的单页应用（SPA）回退规则、真实 API 代理或 Service Worker，要在相应的 base 路径和服务器配置下再冷开深链和刷新，并按发布风险决定是否接真实 API。
- **跨版本再测一次发布。** 先打开 v41 页面，部署 v42，再在旧页面里首次打开编辑抽屉：旧 chunk 应返回 200 且内容是 JavaScript；请求资源目录下不存在的文件应得到 404，而不是回退的 HTML。这一步检验上一章的发布顺序和回退规则是否真的落实。
- **晋级同一份产物。** 发布时晋级通过检查的那一份构建产物，而不是重新构建；重新构建可能部署出另一份代码。
- **Source map 绑定版本、受控上传。** `.map` 文件若仍随产物发布在公开路径上，只隐藏 `sourceMappingURL` 注释并不能阻止外部直接请求它；source map 的语义与暴露面见[构建器怎样把源码变成可部署的文件？](build-pipeline-and-bundling.md)。

> [!info] Vite 的本地预览（Vite 8.3.8，核对于 2026-11-12）
> `vite preview` 可以在本地预览刚构建的 `dist`，适合做上面的冷开检查，但官方不把它定位为生产服务器。

产物晋级、运行时配置和发布门禁的通用做法见[如何晋级并回滚已验证的报表服务产物？](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)。

## 分好层之后，组件层的异步断言怎样写

到这里，排序流程的每一项结论都有了归属：纯转换归单元测试，Back 与真实 URL 归浏览器测试，发布前在构建产物上复跑关键旅程。剩下最容易写错的是组件层：等待状态要在请求还没返回时断言，成功和失败要由测试控制何时发生，Mock 要停在真正的依赖边界上。这些在[异步代码和外部依赖怎样测才可信？](async-tests-and-mocks.md)里展开。

> [!info]- 来源
> - 测试边界与按角色查询（“组件测试”一节）：React Testing Library 16.3.3（[npm](https://www.npmjs.com/package/@testing-library/react)）；查询变体的契约与 `pressed` 等状态选项：[ByRole](https://testing-library.com/docs/queries/byrole/)、[About Queries](https://testing-library.com/docs/queries/about/)；`findBy` 的等待：[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)；`renderHook` 与 `act`：[API](https://testing-library.com/docs/react-testing-library/api/)，核对于 2026-11-12。
> - `user-event` 的用户交互模型：user-event 14.6.10（[npm](https://www.npmjs.com/package/@testing-library/user-event)），[Introduction](https://testing-library.com/docs/user-event/intro/)，核对于 2026-11-12。
> - 路由 loader 提供页面数据（“浏览器测试”一节提到的实现方式之一）：React Router 8.5.1，[Data Loading](https://reactrouter.com/start/data/data-loading)，核对于 2026-11-12。
> - Playwright 断言、URL 谓词路由、`route.fulfill`、路由禁用 HTTP 缓存、Service Worker 边界与 `serviceWorkers` 配置（“浏览器测试”“page.route 拦得到什么”两节）：Playwright 1.65.0（[npm](https://www.npmjs.com/package/@playwright/test)），[Assertions](https://playwright.dev/docs/test-assertions)、[Page route](https://playwright.dev/docs/api/class-page#page-route)、[Network](https://playwright.dev/docs/network)、[Configuration (use)](https://playwright.dev/docs/test-use-options)，核对于 2026-11-12。
> - 用测试服务器启动构建产物：[Playwright webServer](https://playwright.dev/docs/test-webserver)，核对于 2026-11-12。
> - `vite preview` 用于本地预览、不是生产服务器：Vite 8.3.8（[npm](https://www.npmjs.com/package/vite)），[Vite CLI](https://vite.dev/guide/cli.html#vite-preview)、[Static deployment](https://vite.dev/guide/static-deploy.html)，核对于 2026-11-12。
