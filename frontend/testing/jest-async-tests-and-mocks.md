# Jest 怎样验证报表请求中的异步状态和结果？

**案例背景。** 报表页从 recent 的 May、April 开始；用户点 **Oldest first** 后，页面应显示等待状态，读取完成再展示 April、May。生产路由还要确认 `sort` 写进 URL 并能按 Back 恢复；这里的 Jest 组件测试只隔离点击、定时 Mock（模拟）和可见列表，不声称模拟了真实浏览器历史，完整 Back 流程见[前端测试怎样证明报表排序、历史恢复和发布产物正确？](frontend-testing.md)。

## 测试必须等待承载断言的异步工作

在 Promise 风格的 Jest 测试里，框架会等待测试返回或 `await` 的 Promise；另一种受支持的异步方式是 `done` 回调，不要在同一个测试中混用两种完成协议。若启动请求却不等待，测试可能在断言执行前就结束。`rejects` / `resolves` 自身也会返回 Promise，必须 `return` 或 `await`；不能把同步 `toThrow` 用在已经执行过的调用结果上。

## 用用户操作和假时钟控制请求返回

下例用 300 ms 定时器模拟报表服务。运行 TSX 前要配置 `jsdom` 环境及 TypeScript/JSX transformer；测试全局从 `@jest/globals` 显式导入。Fake timers（假时钟）让测试控制响应时机：先点击控件、确认等待状态和旧列表还在，再只推进所需时间，最后检查新行序。这个小组件仅用于隔离请求状态；真正的 sort URL 与 Back 由浏览器测试覆盖：

~~~tsx
import { useState } from "react";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/jest-globals";
import { afterEach, beforeEach, expect, jest, test } from "@jest/globals";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type LoadReports = (sort: SortOrder) => Promise<Report[]>;

const recentRows: Report[] = [
  { id: "may", period: "May", title: "Operations" },
  { id: "april", period: "April", title: "Finance" }
];
const oldestRows = [...recentRows].reverse();

function ReportPanel({ loadReports }: { loadReports: LoadReports }) {
  const [rows, setRows] = useState(recentRows);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function showOldest() {
    setLoading(true);
    setError(false);
    try {
      setRows(await loadReports("oldest"));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <button type="button" disabled={loading} onClick={() => void showOldest()}>
        Oldest first
      </button>
      {loading && <p role="status">正在读取 oldest 排序…</p>}
      {error && <p role="alert">报表读取失败。</p>}
      <ol aria-label="报表" aria-busy={loading}>
        {rows.map(report => (
          <li key={report.id}>{report.period} — {report.title}</li>
        ))}
      </ol>
    </section>
  );
}

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

test("keeps the visible rows pending, then shows the oldest order", async () => {
  const loadReports = jest.fn<LoadReports>(
    sort =>
      new Promise(resolve => {
        setTimeout(
          () => resolve(sort === "oldest" ? oldestRows : recentRows),
          300
        );
      })
  );
  const user = userEvent.setup({
    advanceTimers: jest.advanceTimersByTime
  });

  render(<ReportPanel loadReports={loadReports} />);
  await user.click(screen.getByRole("button", { name: "Oldest first" }));

  expect(loadReports).toHaveBeenCalledWith("oldest");
  expect(screen.getByRole("status")).toBeInTheDocument();
  const list = screen.getByRole("list", { name: "报表" });
  expect(within(list).getAllByRole("listitem").map(row => row.textContent))
    .toEqual(["May — Operations", "April — Finance"]);

  await act(async () => {
    await jest.advanceTimersByTimeAsync(300);
  });

  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(within(list).getAllByRole("listitem").map(row => row.textContent))
    .toEqual(["April — Finance", "May — Operations"]);
});
~~~

`user-event` 在输入或点击过程中也会安排定时任务；启用 Jest 假时钟时，把 `jest.advanceTimersByTime` 传给 `userEvent.setup`。不要用 `delay: null` 绕过假计时器。对只需立即完成的服务 Mock 可用 `mockResolvedValue`；需要验证防抖或加载延迟时，让 Mock Promise 用明确的定时器解决，并调用 `advanceTimersByTimeAsync`。异步定时器 API 会让 Promise 回调有机会执行，旧式 fake timers 不支持它。

此处推进 300 ms 会让定时器调用 Mock Promise 的 `resolve`；`act` 再等 React 把 `setRows` 和 `setLoading(false)` 提交到 DOM，之后同步查询才观察得到 April、May 和消失的等待提示。按钮在 `loading` 时禁用，因此本例定义的是一次只处理一个请求；若产品允许连续切换或重试，要另测并发返回次序和过期结果保护。

当目标元素本来就不存在且需要异步出现时，`findByRole` 返回等待 Promise；如果整条断言需要重试，用 `waitFor`，其回调应在未满足时抛错。固定等待 1 秒既慢又不说明等的是什么。组件请求失败的测试应再用 `mockRejectedValue` 并确认用户能找到 `role="alert"`，不要只断言 Mock 曾经被调用。

## Mock 要停在真实依赖边界

`jest.fn` 可记录参数、调用和 Promise 结果；例如 `mock.results[0].value` 是 Mock 返回的 Promise 对象，不是它之后兑现的报表数组。组件例最后断言的是 Promise 结算后用户实际看到的行序。`jest.spyOn(object, method)` 默认仍会执行原实现，需调用 `mockReturnValue` / `mockImplementation` 才替换，并在测试后用 `mockRestore` 恢复。普通函数 Mock（模拟函数）应断言业务代码如何处理 May、April，不要只复述自己设置了什么结果。

在 Babel 或其他转换为 CommonJS（通用模块系统）的配置中，`jest.mock` 可能由 transformer（代码转换器）提升到导入前。原生 ECMAScript Module（ECMAScript 模块，ESM）的静态导入先执行，Mock 必须在动态导入被测模块前登记：

~~~javascript
import { jest } from "@jest/globals";

jest.unstable_mockModule("./report-api.js", () => ({
  fetchReports: jest.fn()
}));

const { reportsLoader } = await import("./reports-loader.js");
~~~

`reports-loader.js` 应在模块中导入 `./report-api.js` 的 `fetchReports`；测试先登记该依赖的 Mock，再动态导入真正使用它的 loader。`unstable_mockModule` 仍带 unstable 前缀，模块 ESM Mock 方式要和项目的 Jest 版本、Node 运行时以及 transformer 配置一致。Jest 30.5.2 对 Node 24.9+ 同步可求值的 ESM 图也有 automock 和手写 Mock 支持；包含顶层 await 或异步 resolver（模块解析器）/ transformer 的图仍要按当前 ESM 文档选方法。

## 断言要匹配数据结构和观察方式

| 断言 | 适合检查 |
|---|---|
| `toBe(value)` | 原始值或引用相同，使用 `Object.is` 语义。 |
| `toEqual(value)` | 数组和对象的递归值。 |
| `toStrictEqual(value)` | 还要区分缺失属性、`undefined` 属性等结构差异。 |
| `toHaveBeenCalledWith(args)` | Mock 在实际调用边界收到的参数。 |
| `toThrow(error)` | 同步抛错；传入函数本身，而非已经执行的结果。 |

Mock 清理方法不会互相替代：

| 方法 | 清除什么 | 保留什么 |
|---|---|---|
| `jest.clearAllMocks()` | 调用、实例与结果记录 | Mock 的实现与返回值设置 |
| `jest.resetAllMocks()` | 调用记录和 Mock 实现 | spy 仍被替换；需要另行恢复原属性 |
| `jest.restoreAllMocks()` | `spyOn` / 替换属性保存的原实现 | 独立创建或手动赋值的 `jest.fn()` 不会自动还原 |

`beforeAll` / `afterAll` 可为整组测试打开和关闭共享资源；`beforeEach` / `afterEach` 负责逐测试建立和恢复假时钟、spy 与 DOM；不要让一个用例的调用记录或待处理计时器泄漏到另一个用例。Jest 的 `--coverage` 报告哪些分支执行过，不代表断言已验证了用户要的 May/April 顺序、错误恢复或历史行为。

> [!info]- 来源与版本核验（Jest 30.5.2；React Testing Library 16.3.3；user-event 14.6.8；2026-11-06）
> - 当前包版本及发行记录：[Jest v30.5.2 release](https://github.com/jestjs/jest/releases/tag/v30.5.2)，2026-09-18。
> - 定时器 Mock、推进时钟以及异步 timer API：[Timer Mocks](https://jestjs.io/docs/timer-mocks)、[Jest Object API](https://jestjs.io/docs/jest-object)，Jest 30.5.2，核验日期 2026-11-06。
> - 函数 Mock、spy 和 ESM 模块 Mock：[Mock Functions](https://jestjs.io/docs/mock-functions)、[ECMAScript Modules](https://jestjs.io/docs/ecmascript-modules)，Jest 30.5.2，核验日期 2026-11-06。
> - 假时钟下的用户操作、异步查询和重试断言：[user-event setup options](https://testing-library.com/docs/user-event/options/)、[Async Methods](https://testing-library.com/docs/dom-testing-library/api-async/)，核验日期 2026-11-06。
