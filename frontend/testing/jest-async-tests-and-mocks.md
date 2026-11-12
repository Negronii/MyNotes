# Jest 怎样验证报表请求中的异步状态和结果？

**案例背景。** 报表页从 recent 的 May、April 开始；用户点 **Oldest first** 后，页面应显示等待状态，读取完成再展示 April、May。生产路由还要确认 `sort` 写进 URL 并能按 Back 恢复；这里的 Jest 组件测试只隔离点击、定时 Mock（模拟）和可见列表，不声称模拟了真实浏览器历史，完整 Back 流程见[前端测试怎样证明报表排序、历史恢复和发布产物正确？](frontend-testing.md)。

## 测试必须等待承载断言的异步工作

在 Promise 风格的 Jest 测试里，框架会等待测试返回或 `await` 的 Promise；另一种受支持的异步方式是 `done` 回调，不要在同一个测试中混用两种完成协议。若启动请求却不等待，测试可能在断言执行前就结束。`rejects` / `resolves` 自身也会返回 Promise，必须 `return` 或 `await`；`toThrow` 只检查同步调用抛错，异步拒绝应写成 `await expect(loadReports()).rejects.toThrow("unavailable")`。先按界面契约拆出可观察结果：本例要分别确认点击后旧行保留且显示等待、成功后顺序更新、失败后显示错误并保留旧行；只断言加载函数被调用不能覆盖这些结果。

## 用用户操作和假时钟控制请求返回

下例用 300 ms 定时器模拟报表服务。运行 TypeScript JSX（TSX）前要配置独立的 `jest-environment-jsdom` 套件、`testEnvironment: "jsdom"` 和 TypeScript/JSX transformer（代码转换器）；Jest 默认 `node` 环境没有 Document Object Model（文档对象模型，DOM）。此代码按 Babel `@babel/preset-react` 的自动 JSX 运行时（automatic runtime）编译，并保留 Jest 默认的 `injectGlobals: true`，让 React Testing Library 自动注册的 `afterEach(cleanup)` 生效。本例以这两项配置为前提；若使用传统 JSX（classic runtime），生成 `React.createElement` 的 TSX 模块还须导入 `React`。测试全局从 `@jest/globals` 显式导入。Fake timers（假时钟）让测试控制响应时机：先点击控件、确认等待状态和旧列表还在，再只推进所需时间，最后检查新行序。这个小组件仅用于隔离请求状态；真正的 sort URL 与 Back 由浏览器测试覆盖：

这组测试里的时间由测试推进，页面仍通过正常的 Promise 与 React 更新路径变化：

| 测试操作 | 被测组件发生什么 | 此时断言什么 |
| --- | --- | --- |
| 渲染初始组件 | 使用 recent 的旧行。 | 后续步骤以 May、April 为基线。 |
| 点击 Oldest first，暂不推进 300 ms | `loadReports("oldest")` 返回尚未兑现的 Promise；组件进入 loading。 | 请求参数为 oldest；等待提示出现，May、April 仍在。 |
| 在 `act` 中推进 300 ms | timer 兑现 Promise，处理函数续跑，React 提交新行并结束 loading。 | April、May 已出现，等待提示消失。 |
| 另一独立用例：请求直接拒绝 | 组件捕获错误，保留初始旧行并结束 loading。 | 等到错误提示出现，检查 May、April 仍在且没有等待提示。 |

> [!example]- 完整组件与 Jest 异步测试代码
>
> ~~~tsx
> import { useState } from "react";
> import {
>   act,
>   render,
>   screen,
>   within
> } from "@testing-library/react";
> import userEvent from "@testing-library/user-event";
> import "@testing-library/jest-dom/jest-globals";
> import {
>   afterEach,
>   beforeEach,
>   expect,
>   jest,
>   test
> } from "@jest/globals";
>
> type SortOrder = "recent" | "oldest";
> type Report = { id: string; period: string; title: string };
> type LoadReports = (sort: SortOrder) => Promise<Report[]>;
>
> const recentRows: Report[] = [
>   { id: "may", period: "May", title: "Operations" },
>   { id: "april", period: "April", title: "Finance" }
> ];
> const oldestRows = [...recentRows].reverse();
>
> function ReportPanel({
>   loadReports
> }: { loadReports: LoadReports }) {
>   const [rows, setRows] = useState(recentRows);
>   const [loading, setLoading] = useState(false);
>   const [error, setError] = useState(false);
>
>   async function showOldest() {
>     setLoading(true);
>     setError(false);
>     try {
>       setRows(await loadReports("oldest"));
>     } catch {
>       setError(true);
>     } finally {
>       setLoading(false);
>     }
>   }
>
>   return (
>     <section>
>       <button
>         type="button"
>         disabled={loading}
>         onClick={() => void showOldest()}
>       >
>         Oldest first
>       </button>
>       {loading && <p role="status">正在读取 oldest 排序…</p>}
>       {error && <p role="alert">报表读取失败。</p>}
>       <ol aria-label="报表" aria-busy={loading}>
>         {rows.map(report => (
>           <li key={report.id}>{report.period} — {report.title}</li>
>         ))}
>       </ol>
>     </section>
>   );
> }
>
> beforeEach(() => {
>   jest.useFakeTimers();
> });
>
> afterEach(() => {
>   jest.runOnlyPendingTimers();
>   jest.useRealTimers();
> });
>
> test(
>   "keeps the visible rows pending, then shows the oldest order",
>   async () => {
>     const loadReports = jest.fn<LoadReports>(
>       sort =>
>         new Promise(resolve => {
>           setTimeout(
>             () =>
>               resolve(
>                 sort === "oldest" ? oldestRows : recentRows
>               ),
>             300
>           );
>         })
>     );
>     const user = userEvent.setup({
>       advanceTimers: jest.advanceTimersByTime
>     });
>
>     render(<ReportPanel loadReports={loadReports} />);
>     await user.click(
>       screen.getByRole("button", { name: "Oldest first" })
>     );
>
>     expect(loadReports).toHaveBeenCalledWith("oldest");
>     expect(screen.getByRole("status")).toBeInTheDocument();
>     const list = screen.getByRole("list", { name: "报表" });
>     const rowsText = () =>
>       within(list)
>         .getAllByRole("listitem")
>         .map(row => row.textContent);
>     expect(rowsText()).toEqual([
>       "May — Operations",
>       "April — Finance"
>     ]);
>
>     await act(async () => {
>       await jest.advanceTimersByTimeAsync(300);
>     });
>
>     expect(screen.queryByRole("status")).not.toBeInTheDocument();
>     expect(rowsText()).toEqual([
>       "April — Finance",
>       "May — Operations"
>     ]);
>   }
> );
>
> test(
>   "shows an alert and keeps the old rows when loading rejects",
>   async () => {
>     const loadReports = jest.fn<LoadReports>()
>       .mockRejectedValue(new Error("service unavailable"));
>     const user = userEvent.setup({
>       advanceTimers: jest.advanceTimersByTime
>     });
>
>     render(<ReportPanel loadReports={loadReports} />);
>     await user.click(
>       screen.getByRole("button", { name: "Oldest first" })
>     );
>
>     const alert = await screen.findByRole("alert");
>     expect(alert).toHaveTextContent("报表读取失败。");
>     const list = screen.getByRole("list", { name: "报表" });
>     const rowsText = () =>
>       within(list)
>         .getAllByRole("listitem")
>         .map(row => row.textContent);
>     expect(rowsText()).toEqual([
>       "May — Operations",
>       "April — Finance"
>     ]);
>     expect(screen.queryByRole("status")).not.toBeInTheDocument();
>   }
> );
> ~~~

`user-event` 在输入或点击过程中也会安排定时任务；启用 Jest 假时钟时，把 `jest.advanceTimersByTime` 传给 `userEvent.setup`。不要用 `delay: null` 绕过假计时器。对只需立即完成的服务 Mock 可用 `mockResolvedValue`；需要验证防抖或加载延迟时，让 Mock Promise 用明确的定时器解决，并调用 `advanceTimersByTimeAsync`。现代假时钟的异步定时器 API 会让已排入的 Promise 回调有机会在计时器推进时执行；旧式 fake timers 不支持它。每例结束时先调用 `runOnlyPendingTimers` 再恢复真实计时器，可避免第三方库留下的定时任务泄漏到后续测试或清理代码。

此处推进 300 ms 会让定时器调用 Mock Promise 的 `resolve`；`act` 再等 React 把 `setRows` 和 `setLoading(false)` 提交到 DOM，之后同步查询才观察得到 April、May 和消失的等待提示。按钮在 `loading` 时禁用，因此本例定义的是一次只处理一个请求；若产品允许连续切换或重试，要另测并发返回次序和过期结果保护。

当目标元素本来就不存在且需要异步出现时，`findByRole` 返回等待 Promise；如果整条断言需要重试，用 `waitFor`，其回调应在未满足时抛错。固定等待 1 秒既慢又不说明等的是什么。代码中的失败分支使用 `mockRejectedValue`，等待可见 `role="alert"`，并确认 May、April 旧行仍在、等待提示已消失；这能检查拒绝是否映射成页面状态。

## Mock 要停在真实依赖边界

`jest.fn` 可记录参数、调用和 Promise 结果；例如 `mock.results[0].value` 是 Mock 返回的 Promise 对象，不是它之后兑现的报表数组。组件例最后断言的是 Promise 结算后用户实际看到的行序。`jest.spyOn(object, method)` 创建 spy（监视函数），默认仍会执行原实现，需调用 `mockReturnValue` / `mockImplementation` 才替换，并在测试后用 `mockRestore` 恢复。普通函数 Mock（模拟函数）应断言业务代码如何处理 May、April，不要只复述自己设置了什么结果。

在 Babel 转换为 CommonJS（通用模块系统）的配置中，`babel-jest` 会把 `jest.mock` 提升到导入前；不要把这一转换行为假设为所有 transformer（代码转换器）的通用规则。ECMAScript Module（ECMAScript 模块，ESM）的静态导入先执行；本例用 `unstable_mockModule` 显式登记 factory 时，应先登记它，再动态导入被测模块：

~~~javascript
import { jest } from "@jest/globals";

jest.unstable_mockModule("./report-api.js", () => ({
  fetchReports: jest.fn()
}));

const { reportsLoader } = await import("./reports-loader.js");
~~~

`reports-loader.js` 应在模块中导入 `./report-api.js` 的 `fetchReports`；测试先登记该依赖的 Mock，再动态导入真正使用它的 loader。Jest 30.5 的 ESM 测试支持整体仍标为实验性，`unstable_mockModule` 也带 unstable 前缀；原生 ESM 测试还须关闭转换或让 transformer 输出 ESM，并用 Node 的 `--experimental-vm-modules` 启动 Jest。示例只展示 mock 登记顺序，实际 `.mjs` 文件或 `type: "module"` 配置须与项目一致。Jest 30.5.2 对 Node 24.9+ 同步可求值的 ESM 图也支持 automock（自动 Mock）和手写 Mock；包含顶层 `await` 或异步 resolver（模块解析器）/ transformer 的图仍要按当前 ESM 文档选方法。

## 断言要匹配数据结构和观察方式

| 断言 | 适合检查 |
|---|---|
| `toBe(value)` | 原始值或引用相同，使用 `Object.is` 语义。 |
| `toEqual(value)` | 数组和对象的递归值。 |
| `toStrictEqual(value)` | 还要区分缺失属性、`undefined` 属性等结构差异。 |
| `toHaveBeenCalledWith(args)` | Mock 在实际调用边界收到的参数。 |
| `toThrow(error)` | 同步抛错；传入函数本身，而非已经执行的结果。 |

Mock 清理方法不会互相替代：

- `jest.clearAllMocks()` 清空调用、上下文、实例与结果记录，保留 Mock 实现和一次性返回值设置。
- `jest.resetAllMocks()` 清空调用记录并重置 Mock 实现；`spyOn` 目标仍指向替换后的 Mock，不会恢复原属性。
- `jest.restoreAllMocks()` 把 `spyOn` / `replaceProperty` 改过的对象属性恢复为原方法或原值。独立的 `jest.fn()` 和手动赋值不会自动还原；已保存的 spy 变量仍是 Mock 引用，对象属性恢复不会清空这条引用的调用记录。

`beforeAll` / `afterAll` 可为整组测试打开和关闭共享资源；`beforeEach` / `afterEach` 负责逐测试建立和恢复假时钟、spy 与 DOM；不要让一个用例的调用记录或待处理计时器泄漏到另一个用例。Jest 的 `--coverage` 报告哪些分支执行过，不代表断言已验证了用户要的 May/April 顺序、错误恢复或历史行为。

> [!info]- 来源与版本核验（Jest 30.5.2；React Testing Library 16.3.3；user-event 14.6.10；jest-dom 7.0.1；2026-11-12）
> - 当前包版本：[Jest](https://www.npmjs.com/package/jest)，30.5.2；[`jest-environment-jsdom`](https://www.npmjs.com/package/jest-environment-jsdom)，30.5.2；[React Testing Library](https://www.npmjs.com/package/@testing-library/react)，16.3.3；[user-event](https://www.npmjs.com/package/@testing-library/user-event)，14.6.10；[jest-dom](https://www.npmjs.com/package/@testing-library/jest-dom)，7.0.1，均按 npm registry 核验于 2026-11-12。Jest 30.5.2 的发行时间为 2026-09-18：[release](https://github.com/jestjs/jest/releases/tag/v30.5.2)。
> - Jest 的 Promise 测试、显式全局导入与环境设置：[Globals](https://jestjs.io/docs/api)、[Configuring Jest](https://jestjs.io/docs/configuration)，Jest 30.5，核验日期 2026-11-12。
> - 例子所用的 JSX automatic runtime 与 RTL 自动 cleanup 前提：[Babel preset-react runtime](https://babeljs.io/docs/babel-preset-react#runtime)、[Jest `injectGlobals`](https://jestjs.io/docs/configuration#injectglobals-boolean)、[RTL cleanup](https://testing-library.com/docs/react-testing-library/api/#cleanup)，核验日期 2026-11-12。
> - 现代/legacy 假时钟、异步 timer API 与 `runOnlyPendingTimers`：[Timer Mocks](https://jestjs.io/docs/timer-mocks)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5，核验日期 2026-11-12。
> - Mock 返回记录、`spyOn`、清理与恢复：[Mock Functions](https://jestjs.io/docs/mock-function-api)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5，核验日期 2026-11-12。
> - `babel-jest` 的 mock 提升与 ESM 静态导入、`unstable_mockModule`、Node 24.9+ automock 的边界：[Manual Mocks](https://jestjs.io/docs/manual-mocks)、[ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules)，Jest 30.5，核验日期 2026-11-12。
> - 用户操作中的假时钟推进及其回调签名：[user-event Options](https://testing-library.com/docs/user-event/options/)，v14.6.10；`findBy`、`waitFor` 的重试条件和等待 Promise：[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)；`act`、自动 cleanup：[React Testing Library API](https://testing-library.com/docs/react-testing-library/api/)，核验日期 2026-11-12。
