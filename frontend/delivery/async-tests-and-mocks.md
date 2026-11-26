# 异步代码和外部依赖怎样测才可信？

异步测试最常见的失败方式不是报错，而是“假通过”：测试在请求返回前就结束了，断言根本没跑；或者 Mock 替换得太深，测的只是自己设置的返回值。本章说明一个异步组件测试要满足哪些条件才算证明了结论：测试被发现并等到断言执行，运行环境具备 DOM，时间由测试控制，React 更新提交后再观察，Mock 停在真实依赖边界，断言和清理各选对语义。具体实例用 Jest 30.5 与 React Testing Library（RTL）16.3；上一章已经说明组件测试负责证明什么，以及 RTL 查询的契约。

## 要证明的三个结果

沿用[主线一的报表页](../browser/from-url-to-interactive-page.md)。上一章把排序的等待、成功和失败交给组件测试；本章新增两个标识符：组件 `ReportPanel`，以及它通过 prop 接收的数据函数 `loadReports(sort)`。组件渲染主线一的两个排序按钮（`Most recent`、`Oldest first`）和 `ol#reports` 列表，行数据沿用 `r-104`（May report）与 `r-103`（April report）。用户点“最早优先”（`Oldest first`）后，界面契约拆成三个可观察结果：

1. **等待中**：出现 `role="status"` 的等待提示，May、April 旧行仍在。
2. **成功**：行序变为 April、May，等待提示消失，`Oldest first` 变为按下状态（`aria-pressed="true"`）。
3. **失败**：出现 `role="alert"` 的错误提示，旧行保留，等待提示消失。

只断言 `loadReports` 被调用过，三项都没有覆盖。真实地址和 Back 不在本章范围内，它们由浏览器测试证明（见[前端测试该在哪一层证明什么？](frontend-testing-strategy.md)）。

## 测试文件要先被发现

测试运行器先按配置找到测试文件，再载入并执行其中注册的用例。文件没被发现，里面的 `test()` 永远不会跑，也不会报错。

> [!info] Jest 30.5 的发现规则
> 默认配置下，`ReportPanel.test.tsx`、`ReportPanel.spec.tsx` 或 `__tests__/ReportPanel.tsx` 都会被收集；放在别处的普通组件文件 `ReportPanel.tsx`，不会因为里面写了 `test()` 就成为测试文件。
>
> 项目可以用 `testMatch`（glob 模式）或 `testRegex`（正则）改变规则，两者不能同时设置；根目录、忽略规则和命令行筛选也会影响实际运行集合。找不到测试时，先用 `jest --listTests` 看实际收集到的列表。

被发现只说明路径符合条件。TSX 文件还需要转换器和 DOM 环境才能执行，见下文“运行环境”。

## 测试必须等到断言执行完

异步测试要明确告诉运行器“什么时候算完”，这叫 completion protocol (完成协议)。Jest 支持两种：

- **返回 Promise**：`async` 测试函数返回的 Promise，或测试中 `return` 的 Promise，运行器会等它结算。
- **`done` 回调**：测试函数声明 `done` 参数，运行器等到它被调用。

同一个测试里不要混用两种。启动了异步工作却既不 `await` 也不 `return`，测试函数会在断言执行前就返回，表现为通过。

两条容易写错的断言：

- `expect(p).resolves` / `.rejects` 自身也返回 Promise，必须 `await` 或 `return`，否则同样不会被等待。
- `toThrow` 只检查同步调用抛错。异步拒绝要写成 `await expect(loadReports("oldest")).rejects.toThrow("unavailable")`。

## 运行环境：DOM 和 JSX 不是默认就有的

组件测试运行在 Node 里，浏览器的 DOM 要由测试环境模拟，JSX 要由转换器编译。这些前提不满足时，测试要么报错，要么在不知情的情况下少了一步清理。

> [!info] 本章实例的环境前提（Jest 30.5.2、jest-environment-jsdom 30.5.2）
> - **DOM**：Jest 默认的 `node` 环境没有 DOM。要单独安装 `jest-environment-jsdom`，并设置 `testEnvironment: "jsdom"`。
> - **TSX**：要配置 TypeScript/JSX 转换器。本例用 Babel 的 `@babel/preset-react` 自动 JSX 运行时（automatic runtime），所以组件文件不需要导入 `React`；若用传统运行时（classic runtime），生成 `React.createElement` 的模块必须导入 `React`。
> - **自动清理**：RTL 会在检测到全局 `afterEach` 时自动注册 `cleanup`，卸载上一个测试渲染的组件。这依赖 Jest 默认的 `injectGlobals: true`；测试代码里的 `expect`、`jest`、`test` 等则从 `@jest/globals` 显式导入。关掉全局注入时，要自己在 `afterEach` 里调用 `cleanup`。

## 假时钟：由测试决定请求何时返回

要断言“等待中”，测试必须在请求还没返回时观察界面；要断言“成功”，又必须让它返回。fake timers (假时钟) 把 `setTimeout` 等计时器换成由测试推进的版本，于是可以把报表服务模拟成“300 ms 后返回”，并精确控制这 300 ms 何时流过。

页面仍然走正常的 Promise 与 React 更新路径，测试只控制时间。成功用例的步骤是：

| 测试操作 | 被测组件发生什么 | 此时断言什么 |
| --- | --- | --- |
| 渲染组件 | 显示 recent 的旧行 | 以 May、April 为基线 |
| 点击“最早优先”，暂不推进时间 | `loadReports("oldest")` 返回尚未兑现的 Promise，组件进入 loading | 调用参数为 `"oldest"`；等待提示出现；May、April 仍在 |
| 在 `act` 中推进 300 ms | 计时器兑现 Promise，处理函数继续执行，React 提交新行并结束 loading | April、May 出现；等待提示消失；“最早优先”按下 |

失败用例让 `loadReports` 直接拒绝，等错误提示出现后检查旧行仍在、没有等待提示、“最早优先”未按下。

> [!example]- 完整组件与测试代码（2026-11-26 用 Jest 30.5.2、RTL 16.3.3、user-event 14.6.10、jest-dom 7.0.1、React 19.3.1 实跑通过）
>
> ~~~tsx
> import { useState } from "react";
> import { act, render, screen, within } from "@testing-library/react";
> import userEvent from "@testing-library/user-event";
> import "@testing-library/jest-dom/jest-globals";
> import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";
>
> type SortOrder = "recent" | "oldest";
> type Report = { id: string; label: string };
> type LoadReports = (sort: SortOrder) => Promise<Report[]>;
>
> const recentRows: Report[] = [
>   { id: "r-104", label: "May report" },
>   { id: "r-103", label: "April report" }
> ];
> const oldestRows = [...recentRows].reverse();
>
> function ReportPanel({ loadReports }: { loadReports: LoadReports }) {
>   const [sort, setSort] = useState<SortOrder>("recent");
>   const [rows, setRows] = useState(recentRows);
>   const [loading, setLoading] = useState(false);
>   const [error, setError] = useState(false);
>
>   async function showSort(next: SortOrder) {
>     setLoading(true);
>     setError(false);
>     try {
>       setRows(await loadReports(next));
>       setSort(next);
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
>         aria-pressed={sort === "recent"}
>         disabled={loading}
>         onClick={() => void showSort("recent")}
>       >
>         Most recent
>       </button>
>       <button
>         type="button"
>         aria-pressed={sort === "oldest"}
>         disabled={loading}
>         onClick={() => void showSort("oldest")}
>       >
>         Oldest first
>       </button>
>       {loading && <p role="status">Loading reports…</p>}
>       {error && <p role="alert">Could not load reports.</p>}
>       <ol id="reports" aria-busy={loading}>
>         {rows.map(report => (
>           <li key={report.id}>{report.label}</li>
>         ))}
>       </ol>
>     </section>
>   );
> }
>
> const rowsText = () =>
>   within(screen.getByRole("list"))
>     .getAllByRole("listitem")
>     .map(row => row.textContent);
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
> test("keeps the old rows while pending, then shows the oldest order", async () => {
>   const loadReports = jest.fn<LoadReports>(
>     sort =>
>       new Promise(resolve => {
>         setTimeout(() => resolve(sort === "oldest" ? oldestRows : recentRows), 300);
>       })
>   );
>   const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
>
>   render(<ReportPanel loadReports={loadReports} />);
>   await user.click(screen.getByRole("button", { name: "Oldest first" }));
>
>   expect(loadReports).toHaveBeenCalledWith("oldest");
>   expect(screen.getByRole("status")).toBeInTheDocument();
>   expect(rowsText()).toEqual(["May report", "April report"]);
>
>   await act(async () => {
>     await jest.advanceTimersByTimeAsync(300);
>   });
>
>   expect(screen.queryByRole("status")).not.toBeInTheDocument();
>   expect(rowsText()).toEqual(["April report", "May report"]);
>   expect(
>     screen.getByRole("button", { name: "Oldest first", pressed: true })
>   ).toBeInTheDocument();
> });
>
> test("shows an alert and keeps the old rows when loading rejects", async () => {
>   const loadReports = jest
>     .fn<LoadReports>()
>     .mockRejectedValue(new Error("service unavailable"));
>   const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
>
>   render(<ReportPanel loadReports={loadReports} />);
>   await user.click(screen.getByRole("button", { name: "Oldest first" }));
>
>   expect(await screen.findByRole("alert")).toHaveTextContent("Could not load reports.");
>   expect(rowsText()).toEqual(["May report", "April report"]);
>   expect(screen.queryByRole("status")).not.toBeInTheDocument();
>   expect(
>     screen.getByRole("button", { name: "Oldest first", pressed: false })
>   ).toBeInTheDocument();
> });
> ~~~

使用假时钟有四条规则：

- **把推进函数交给 `user-event`。** `user-event` 在点击和输入过程中也会安排计时任务；启用假时钟后，它自己的等待也要靠推进，所以 `userEvent.setup` 要传入 `advanceTimers: jest.advanceTimersByTime`。不要用 `delay: null` 绕过。
- **推进时用异步版本。** 计时器回调兑现 Promise 后，后续的 `then` 回调和 `await` 续跑在微任务里执行（时机见[事件循环怎样安排任务、微任务和渲染？](../browser/event-loop-tasks-and-rendering.md)）。`jest.advanceTimersByTimeAsync` 会让已排入的 Promise 回调有机会在推进过程中执行；同步的 `advanceTimersByTime` 不会等它们。异步计时器 API 只在现代假时钟下可用，旧式（legacy）假时钟不支持。
- **只为需要计时的场景设计延迟。** 只需立即完成的服务 Mock 用 `mockResolvedValue` 即可；要验证防抖或加载延迟时，才让 Mock Promise 由明确的计时器兑现。
- **每个测试结束先清掉待执行计时器，再恢复真实时钟。** 示例在 `afterEach` 里先 `runOnlyPendingTimers` 再 `useRealTimers`，避免组件或第三方库留下的计时任务泄漏到下一个测试或清理代码里。

## act：等 React 把更新提交到 DOM

推进 300 ms 只让计时器兑现了 Promise。处理函数随后调用 `setRows`、`setSort`、`setLoading(false)`，React 还要把这些更新渲染并提交到 DOM（render 与 commit 两段见[React 怎样把一次用户操作变成界面更新？](../ui-state/react-update-model.md)）。`act` 的作用就是把一段会触发 React 更新的代码包起来，等这些更新全部处理完再返回。示例把推进时间放进 `await act(async () => …)`，之后的同步查询才观察得到 April、May 和消失的等待提示。

RTL 的 `render` 和 `user-event` 的操作已经替一般交互处理了 `act` 边界，所以点击不需要再包一层。只有从这些工具之外触发更新时，例如推进假时钟、直接调用会改状态的回调，才需要显式包在 `act` 里。

**等待异步出现的元素用 `findBy`，等待整条断言成立用 `waitFor`。** 失败用例里错误提示要等 Promise 拒绝后才出现，所以用 `await screen.findByRole("alert")`。如果需要反复重试的是一整条断言，用 `waitFor`，它有两条约束：

- 回调在条件未满足时必须**抛出**断言错误；返回 `false` 不会触发重试。
- 不要把点击等副作用放进回调，因为回调会被重复执行。

固定睡眠一秒既慢，又不说明在等什么，不要用。

**本例只定义了一次一个请求。** 按钮在 `loading` 时禁用，所以不会出现两个请求同时在途。产品若允许连续切换或重试，还要另测请求乱序返回时，迟到的旧响应不会覆盖新结果；按身份丢弃过期结果的机制见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](../ui-state/server-state-and-optimistic-updates.md)。

## Mock 停在真实依赖边界

Mock 的价值在于替换一个**不受控的外部依赖**（网络、时钟、存储），让被测代码的其余部分照常运行。替换得越深，测试证明的就越少。本例把 `loadReports` 作为 prop 注入，Mock 恰好停在组件与数据服务的边界：组件的状态管理、渲染和可访问标记都是真实代码。

使用 Jest Mock 时要分清几件事：

- **`jest.fn` 记录的是调用，不是结果的含义。** 它记录参数、`this`、返回值。`mock.results[0].value` 是 Mock 返回的那个 Promise 对象，不是它之后兑现的报表数组。示例最后断言的是 Promise 结算后用户实际看到的行序，而不是复述自己设置的返回值。
- **`jest.spyOn(object, method)` 默认仍执行原实现。** 要替换行为，需再调用 `mockReturnValue` / `mockImplementation`；测试后用 `mockRestore` 恢复原方法。
- **模块 Mock 的生效顺序取决于模块系统。** 被测模块在加载时就绑定了它导入的依赖，所以 Mock 必须在被测模块加载前登记。

> [!info] Jest 30.5 中的模块 Mock 顺序
> 在 Babel 把代码转换成 CommonJS 的配置下，`babel-jest` 会把 `jest.mock(...)` 调用提升到所有导入之前，所以写在文件中间也能生效。这是该转换器的行为，不是所有转换器的通用规则。
>
> 原生 ESM 中静态 `import` 总是先于模块体执行（ESM 的加载与链接见[import 写下后，谁负责找到、链接和执行文件？](../javascript/modules-and-host-boundaries.md)），无法提升。做法是先用 `unstable_mockModule` 登记工厂函数，再用动态 `import()` 加载被测模块：
>
> ~~~javascript
> import { jest } from "@jest/globals";
>
> jest.unstable_mockModule("./report-api.js", () => ({
>   fetchReports: jest.fn()
> }));
>
> const { reportsLoader } = await import("./reports-loader.js");
> ~~~
>
> 这里 `reports-loader.js` 静态导入了 `./report-api.js` 的 `fetchReports`，动态导入发生在登记之后，所以它拿到的是 Mock。几个前提：Jest 的 ESM 支持整体仍标为实验性，`unstable_mockModule` 带 unstable 前缀；要关闭转换或让转换器输出 ESM，并用 Node 的 `--experimental-vm-modules` 启动 Jest；文件要用 `.mjs` 或在 `package.json` 里设 `"type": "module"`。Jest 30.5.2 对 Node 24.9+ 上可同步求值的 ESM 图也支持 automock 和手写 Mock；含顶层 `await` 或异步解析器/转换器的图，按当前 ESM 文档选方法。2026-11-26 在 Node 26.13.1 上实跑过上面的登记顺序。

## 断言按数据结构和观察方式选

| 断言 | 适合检查 |
|---|---|
| `toBe(value)` | 原始值或同一引用，按 `Object.is` 比较（三种相等规则见[JavaScript 的值有哪些类型，“相等”又有几种？](../javascript/values-types-and-equality.md)） |
| `toEqual(value)` | 数组和对象的递归值相等 |
| `toStrictEqual(value)` | 在 `toEqual` 之上，还区分缺失属性与值为 `undefined` 的属性等结构差异 |
| `toHaveBeenCalledWith(...args)` | Mock 在调用边界实际收到的参数 |
| `toThrow(error)` | 同步抛错；要传入函数本身，而不是已经执行的结果 |

示例比较行文本用 `toEqual`，因为每次查询得到的都是新数组，`toBe` 永远不会相等。

## 三种 Mock 清理不等价

Jest 提供三个全局清理方法，名字相近，清掉的东西不同：

| 方法 | 调用记录 | Mock 实现 | 被 `spyOn` / `replaceProperty` 改过的对象属性 |
|---|---|---|---|
| `jest.clearAllMocks()` | 清空（`calls`、`instances`、`contexts`、`results`） | 保留，包括一次性返回值设置 | 不恢复 |
| `jest.resetAllMocks()` | 清空 | 换成返回 `undefined` 的空函数 | 不恢复，属性仍指向 Mock |
| `jest.restoreAllMocks()` | 见下 | 见下 | 恢复为原方法或原值 |

`restoreAllMocks` 只对 `jest.spyOn` 和 `jest.replaceProperty` 生效。独立的 `jest.fn()` 和手动赋值上去的 Mock 不会自动还原，要自己恢复。另外，之前保存在变量里的 spy 仍是 Mock 引用；对象属性恢复成原方法后，不要再通过这个变量的调用记录推断原方法是否被调用。

清理的作用域也要配对：`beforeAll` / `afterAll` 管整组测试共享的资源；`beforeEach` / `afterEach` 逐个测试建立和恢复假时钟、spy 与 DOM。目标是不让一个用例的调用记录、待执行计时器或渲染结果泄漏到另一个用例。

## 覆盖率只说明代码执行过

Jest 的 `--coverage` 报告哪些行和分支执行过。执行过不等于被验证过：一个点击“最早优先”并推进时间、却不写任何断言的测试，同样能让成功分支全部算作“已覆盖”。May、April 的顺序、失败后旧行保留、Back 恢复地址，这些结论只能由对应的断言证明。覆盖率适合找出完全没有测试经过的分支，不适合当作正确性的证据。

## 测试证明了对，下一步证明够快

到这里，排序流程的正确性已经由三层测试和构建产物检查覆盖。正确之外，用户还会抱怨“慢”：点击排序后要等多久才看到新行，这段时间花在网络、主线程计算还是渲染上？[用户觉得慢时，怎样从指标走到证据？](performance-metrics-and-diagnosis.md)从性能指标出发，用 50,000 行排序实验回答这个问题。

> [!info]- 来源
> - 测试文件发现、`testMatch` 与 `testRegex` 互斥、路径过滤（“测试文件要先被发现”）：[Jest Configuration — testMatch](https://jestjs.io/docs/configuration#testmatch-arraystring)；实际收集结果：[Jest CLI — listTests](https://jestjs.io/docs/cli#--listtests)，Jest 30.5 文档，核对于 2026-11-13。
> - 版本：[Jest](https://www.npmjs.com/package/jest) 30.5.2（发布于 2026-09-18，[release](https://github.com/jestjs/jest/releases/tag/v30.5.2)）、[jest-environment-jsdom](https://www.npmjs.com/package/jest-environment-jsdom) 30.5.2、[React Testing Library](https://www.npmjs.com/package/@testing-library/react) 16.3.3、[user-event](https://www.npmjs.com/package/@testing-library/user-event) 14.6.10、[jest-dom](https://www.npmjs.com/package/@testing-library/jest-dom) 7.0.1，npm registry，核对于 2026-11-12。
> - Promise 测试与 `done` 回调、`resolves`/`rejects`、显式导入全局、测试环境配置（“完成协议”“运行环境”）：[Globals](https://jestjs.io/docs/api)、[Configuring Jest](https://jestjs.io/docs/configuration)，Jest 30.5，核对于 2026-11-12。
> - 自动 JSX 运行时与 RTL 自动 cleanup 的前提：[Babel preset-react runtime](https://babeljs.io/docs/babel-preset-react#runtime)、[Jest `injectGlobals`](https://jestjs.io/docs/configuration#injectglobals-boolean)、[RTL cleanup](https://testing-library.com/docs/react-testing-library/api/#cleanup)，核对于 2026-11-12。
> - 现代与旧式假时钟、`advanceTimersByTimeAsync` 让 Promise 回调先执行、`runOnlyPendingTimers`（“假时钟”）：[Timer Mocks](https://jestjs.io/docs/timer-mocks)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5，核对于 2026-11-12。
> - 假时钟下 `user-event` 的 `advanceTimers` 选项：[user-event Options](https://testing-library.com/docs/user-event/options/)，v14.6.10；`findBy` 与 `waitFor` 的重试条件：[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)；`act` 与自动 cleanup：[React Testing Library API](https://testing-library.com/docs/react-testing-library/api/)，核对于 2026-11-12。
> - `mock.results`、`spyOn`、`mockClear`/`mockReset`/`mockRestore` 及对应全局方法（“Mock 停在真实依赖边界”“三种 Mock 清理不等价”）：[Mock Functions](https://jestjs.io/docs/mock-function-api)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5，核对于 2026-11-26。
> - `babel-jest` 提升 `jest.mock`、ESM 静态导入与 `unstable_mockModule`、Node 24.9+ automock 边界：[Manual Mocks](https://jestjs.io/docs/manual-mocks)、[ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules)，Jest 30.5，核对于 2026-11-12。
> - 断言语义（`toBe` 用 `Object.is`、`toStrictEqual` 的额外检查）：[Expect](https://jestjs.io/docs/expect)，Jest 30.5，核对于 2026-11-26。
