# TypeScript 的 Promise 类型能保证什么？

**案例背景：** 报表接口返回一段 JSON（JavaScript Object Notation，JavaScript 对象表示法）文本，页面要把它安全地交给类型为 `ReportData` 的显示逻辑。`Promise<ReportData>` 的泛型说明 TypeScript 应怎样检查成功结果；它不会替运行时检查接口内容，也不会保证操作一定成功。

## `Promise<ReportData>` 表示什么，不表示什么？

| 类型信息或运行结果 | 它表达的内容 |
|---|---|
| `Promise<ReportData>` 的泛型 `ReportData` | Promise 成功完成时，TypeScript 按 `ReportData` 检查后续代码 |
| 请求、JSON 语法解析或字段校验失败 | Promise 仍可能被拒绝；标准 `Promise<T>` 没有单独描述拒绝原因的类型参数 |
| 服务端 JSON | 即使代码声明为 `ReportData`，类型注解也不会运行时检查 JSON 字段 |

类型检查能帮助我们在可信的校验结果之后安全地使用字段；数据跨进程或网络边界时，先将其作为 `unknown`，再运行真正的结构检查。下面用一段模拟接口响应的 JSON 文本，从输入走到成功值或拒绝：

~~~typescript
type ReportData = { id: number; title: string };

function parseReport(value: unknown): ReportData {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("expected a report object");
  }

  const record = value as { id?: unknown; title?: unknown };
  if (typeof record.id !== "number" || typeof record.title !== "string") {
    throw new TypeError("invalid report shape");
  }
  return { id: record.id, title: record.title };
}

async function readReport(json: string): Promise<ReportData> {
  const value: unknown = JSON.parse(json);
  return parseReport(value);
}

async function showExamples() {
  const report = await readReport('{"id":42,"title":"Monthly"}');
  console.log(report.id, report.title); // 42, "Monthly"

  try {
    await readReport('{"id":"42","title":"Monthly"}');
  } catch (error) {
    console.log(error instanceof TypeError); // true
  }
}

showExamples();
~~~

`parseReport` 里的 `as` 只是类型断言：它让编译器允许读取 `id` 和 `title`，这两个字段的类型仍是 `unknown`；紧接着的 `typeof` 检查才会检查运行时实际值。第一段输入经 `JSON.parse` 得到的值仍先以 `unknown` 保存；`parseReport` 逐字段检查后才返回 `ReportData`，所以 `readReport` 的成功结果确实符合本例的结构。第二段是语法合法的 JSON，但 `id` 是字符串，因此校验器抛出 `TypeError`，`readReport` 返回的 Promise 被拒绝。若 JSON 语法本身有误，`JSON.parse` 会先抛 `SyntaxError`，校验器不会运行；在 `async` 函数中两类异常都会使 Promise 被拒绝，调用方可用 `try` / `catch` 处理。`Promise<ReportData>` 只让后续成功路径按 `ReportData` 检查，不承诺不拒绝，也不给拒绝原因一个专属类型。

Promise 的状态转换、链式传值、并发组合与 `async`/`await` 怎样传播拒绝，见[回调、Promise 与 async 函数怎样组合异步工作？](../../../../frontend/javascript/asynchronous-javascript.md#typescript-的-promise-类型能保证什么)。计时器由浏览器或 Node.js 等宿主提供；把定时器结果包装成 Promise 不会改变其宿主调度或产生自动取消能力，亦见该章的[定时器和超时说明](../../../../frontend/javascript/asynchronous-javascript.md#定时器和超时究竟能取消什么)。

> [!info]- 来源
> - 类型注解编译后擦除、不能改变运行时行为：[TypeScript Handbook — Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，核对 2026-11-12；`unknown` 需先缩小类型再使用：[TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)，核对 2026-11-12。
> - 标准 TypeScript Promise 声明只有成功值泛型 `T`；`reject` 接受未进一步约束的原因，并返回 `Promise<T>`：[TypeScript 5.9.3 `es2015.promise.d.ts`](https://github.com/microsoft/TypeScript/blob/v5.9.3/src/lib/es2015.promise.d.ts)，§`PromiseConstructor`，2026-11-12 核对。
> - Promise 在运行时可以成功完成或拒绝：[ECMAScript 2026 Control Abstraction Objects](https://tc39.es/ecma262/2026/multipage/control-abstraction-objects.html#sec-promise-objects)，§27.2 Promise Objects；`JSON.parse` 对无效 JSON 文本抛 `SyntaxError`：[ECMAScript 2026 Structured Data](https://tc39.es/ecma262/2026/multipage/structured-data.html)，§25.5.2 `JSON.parse`；`async` 函数把异常作为拒绝原因返回：[ECMAScript 2026 Language Functions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html)，§15.8.4 `EvaluateAsyncFunctionBody`；均核对 2026-11-12。
