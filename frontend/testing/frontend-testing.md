# What evidence shows a frontend change works through production delivery? / 哪些证据能证明前端改动可用并能正确交付？

**Core answer / 核心回答：** Build the production output, run a critical browser journey against that output on a production-like server, then promote the exact artifact that passed. A development server alone does not exercise emitted assets or deployment paths. The general risk-to-test-boundary principle belongs to [Software Testing Strategy / 软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md); the tool choices for local logic and component behavior are outlined below. / 构建生产产物，在接近生产环境的服务上用该产物运行关键浏览器流程，然后晋级同一份通过检查的产物。单独运行开发服务器无法覆盖实际生成的资源或部署路径。通用的风险与测试边界原则见[软件测试策略](../../engineering-foundations/testing/software-testing-strategy.md)；本地逻辑和组件行为的工具选择见下文。

## How should frontend tests be divided? / 前端测试如何分层？

**Core answer / 核心回答：** Use a unit test for isolated logic, a component integration test for user-visible wiring, and a browser test when real navigation, persistence, browser behavior, emitted assets, or service wiring is part of the risk. Keep the feedback loop cheap where it can provide reliable evidence. / 隔离逻辑用单元测试，验证用户可见的组件连接用集成测试；当风险涉及真实导航、持久化、浏览器行为、生成资源或服务连接时使用浏览器测试。能可靠提供证据时，优先保持反馈成本较低。

| Layer | Useful for | Example tools |
|---|---|---|
| Unit | Pure functions and isolated behavior | Jest, Vitest |
| Integration | Components, hooks, context, and API boundaries together | React Testing Library with Jest or Vitest |
| End-to-end | Browser navigation, persistence, and critical user journeys | Playwright, Cypress |

Keep browser tests for behavior that depends on the real browser or application wiring. A test pyramid is a planning aid; a project's distribution should follow its actual risks and feedback costs.

## Jest fundamentals / Jest基础

Use Jest when the risk can be reproduced around logic, state, or a dependency boundary. A test that starts asynchronous work must return or await the Promise that contains its assertions. Place the mock at the dependency and assert the behavior of the caller. [How a Jest test verifies asynchronous behavior / Jest 怎样验证异步行为](jest-async-tests-and-mocks.md) contains the complete async, lifecycle, matcher, CommonJS and native ESM examples.

## React Testing Library / React Testing Library

Test through user-visible roles, labels, text, and interactions. Queries have different timing contracts:

| Query | Use when |
|---|---|
| getBy... | The element should exist now; throws if absent or ambiguous. |
| queryBy... | Checking that an element is absent; returns null if absent. |
| findBy... | The element should appear asynchronously; returns a Promise. |

Prefer getByRole with an accessible name when it represents the user's interaction. Use getByLabelText for form controls. A test ID is an escape hatch when the UI has no suitable user-facing query.

~~~jsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

test("submits the entered email", async () => {
  // Arrange
  const user = userEvent.setup();
  const onSubmit = jest.fn();
  render(<EmailForm onSubmit={onSubmit} />);

  // Act
  await user.type(
    screen.getByRole("textbox", { name: /email/i }),
    "person@example.com"
  );
  await user.click(screen.getByRole("button", { name: /submit/i }));

  // Assert
  expect(onSubmit).toHaveBeenCalledWith("person@example.com");
});
~~~

userEvent models a higher-level interaction sequence, including keyboard and focus behavior. It is not a real browser. fireEvent dispatches a lower-level event and can be useful when a test specifically needs that event boundary.

The form test above follows Arrange–Act–Assert (AAA): prepare the user and component, perform the interaction, then check the observable result.

For an asynchronous appearance, prefer findBy...:

~~~javascript
const result = await screen.findByText("Loaded");
expect(result).toBeInTheDocument();
~~~

Use waitFor when the assertion itself needs retrying. Its callback must throw for a retry; returning false does not request another attempt. Avoid placing side effects inside waitFor because the callback can run more than once.

## Testing custom Hooks and snapshots / 测试自定义Hook与快照

React Testing Library exports renderHook from @testing-library/react. It renders a test component around the Hook. Most Testing Library render and interaction helpers already use React act; use act for an update initiated outside those helpers when the test needs to flush it.

~~~javascript
import { act, renderHook } from "@testing-library/react";

test("increments the counter", () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => result.current.increment());

  expect(result.current.count).toBe(1);
});
~~~

Snapshots can capture stable structure, but a large snapshot does not explain which behavior matters. Use focused assertions for user-visible behavior and update snapshots intentionally when the expected output changes.

## Release checks / 发布检查

CI should connect fast source checks to the exact production output. A small frontend release path is:

**核心原则 / Core idea：** 先完成类型、单元和组件检查，再生成生产构建；用接近生产的服务运行这份构建产物，执行关键浏览器流程，最后晋级同一份已验证产物，避免重新构建后发布了另一份代码。HMR 只验证开发热更新链路，不能证明生产资源路径、分块或发布产物正常；Vite preview 可以本地预览刚生成的 `dist`，但官方定位不是生产服务器。Source map 应关联到具体发布版本并受控上传；`hidden` 只隐藏源码映射注释，不阻止他人直接访问映射文件。

~~~text
lockfile install -> type check -> unit/component tests -> production build
  -> serve the built output -> one critical browser smoke -> retain/promote that output
~~~

For example, a project can run `npm run typecheck`, `npm run test:ci`, and `npm run build`, then `npx playwright test tests/release-smoke.spec.ts`. Configure Playwright's `webServer.command` to start `npm run preview` (or the framework's built-output server) after the build so this browser test sees emitted assets rather than the HMR server; script names are project-specific.

Type checks catch static contract errors; unit and component tests catch local logic and UI wiring; a production build catches transforms, asset emission, and chunk or base-path issues that a dev server may not exercise. Then serve the generated output with a production-like static server and run one browser test for a critical journey, such as opening search, submitting a query, and seeing results. A Playwright `webServer` can start the local artifact server for the test; with Vite, `vite preview` serves the just-built `dist` locally for this check, but is not a production server. Promote the tested output rather than rebuilding it for release.

Use browser checks where real routing, asset URLs, browser behavior, or app/service wiring matters. A passing HMR session proves the development loop works; it does not prove production chunks load from the deployed base path or that the published artifact works. Source maps can translate minified error locations back to original source when tied to a release and uploaded to a controlled error-reporting system. A hidden map removes the source-map comment, not the file or access risk; do not leave private maps at a public asset URL. The shared [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) note owns artifact promotion, runtime secrets, and rollout gates.

**See also:** [Advanced React / React进阶](../frameworks/advanced-react.md) for custom Hook semantics; [Git Essentials / Git基础](../../engineering-foundations/version-control/git-essentials.md) for how tests fit into review and CI.

**Sources checked 2026-10-15:** [Jest Mock Functions](https://jestjs.io/docs/mock-functions), [Jest Object and Mock Lifecycle](https://jestjs.io/docs/jest-object), [Jest ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules), [React Testing Library API](https://testing-library.com/docs/react-testing-library/api/), [Testing Library Queries](https://testing-library.com/docs/queries/about/), [user-event](https://testing-library.com/docs/user-event/intro/), [Testing Library Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/), [Vite static deployment](https://vite.dev/guide/static-deploy.html), [Playwright web server](https://playwright.dev/docs/test-webserver).
