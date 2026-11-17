# 收到不可信 JSON 后，TypeScript 怎样建立可信的类型？

月度报表页会从接口或浏览器存储读入数据。这些数据来自程序外部，内容可能与我们声明的类型不符。TypeScript 的类型注解在编译成 JavaScript 时会被擦除：它们只检查我们自己写的代码，既不会替 `JSON.parse` 检查实际收到的字段，也不会验证用户是否有权查看某份报表。

所以外部数据要经过两个独立的步骤：先按 JSON（JavaScript Object Notation）语法解析文本，再按运行时规则检查结构和取值。检查通过后，用已检查的字段重新构造应用对象，后续代码才能放心依赖它的静态类型。下图只画运行时的执行过程；后文用到的 `unknown` 是编译期的类型标注，不对应运行时的任何转换步骤。

~~~mermaid
flowchart TB
  A[已取得的接口或存储文本] --> B{JSON.parse}
  B -- 语法错误 --> E[返回 syntax]
  B -- 解析成功 --> C[JavaScript 运行时值]
  C --> D{逐项检查字段和值}
  D -- 检查失败 --> F[返回 shape]
  D -- 检查通过 --> G[按已检查字段重建对象]
  G --> H[业务代码使用已检查对象]
~~~

图中的 `syntax` 和 `shape` 是解析函数返回的失败原因。如果文本来自浏览器存储，还有第三种失败：`getItem` 返回 `null`（没有存过这一项）时，代码在进入上面这条流程之前就直接返回 `missing`。

## 怎样在运行时检查报表数据？

`unknown`（未知类型）可以接收任何值，但在通过检查缩窄到更具体的类型之前，编译器不允许读取它的属性。下面的解析器分别处理语法错误、存储中缺少数据和字段结构错误；每一行通过检查后都被重新构造成 `ReportRow`，而不是用 `as` 把外部对象直接断言成这个类型。

~~~typescript
type Role = "admin" | "reader";
type ReportStatus = "open" | "published" | "archived";

type ReportRow = {
  id: string;
  title: string;
  month: string;
  region: string;
  status: ReportStatus;
  total: number;
  ownerEmail: string;
};

type ReportData = {
  viewer: { id: string; role: Role };
  rows: ReportRow[];
};

type ParseResult<T> =
  | { ok: true; value: T }
  | { ok: false; reason: "syntax" | "shape" | "missing" };

function isRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function parseReportData(text: string): ParseResult<ReportData> {
  let input: unknown;
  try {
    input = JSON.parse(text);
  } catch {
    return { ok: false, reason: "syntax" };
  }

  if (
    !isRecord(input) ||
    !isRecord(input.viewer) ||
    typeof input.viewer.id !== "string" ||
    (input.viewer.role !== "admin" &&
      input.viewer.role !== "reader") ||
    !Array.isArray(input.rows)
  ) {
    return { ok: false, reason: "shape" };
  }

  const rows: unknown[] = input.rows;
  const checkedRows: ReportRow[] = [];
  for (const candidate of rows) {
    if (
      !isRecord(candidate) ||
      typeof candidate.id !== "string" ||
      typeof candidate.title !== "string" ||
      typeof candidate.month !== "string" ||
      !/^\d{4}-(0[1-9]|1[0-2])$/.test(candidate.month) ||
      typeof candidate.region !== "string" ||
      (candidate.status !== "open" &&
        candidate.status !== "published" &&
        candidate.status !== "archived") ||
      typeof candidate.total !== "number" ||
      !Number.isFinite(candidate.total) ||
      typeof candidate.ownerEmail !== "string"
    ) {
      return { ok: false, reason: "shape" };
    }

    checkedRows.push({
      id: candidate.id,
      title: candidate.title,
      month: candidate.month,
      region: candidate.region,
      status: candidate.status,
      total: candidate.total,
      ownerEmail: candidate.ownerEmail
    });
  }

  return {
    ok: true,
    value: {
      viewer: { id: input.viewer.id, role: input.viewer.role },
      rows: checkedRows
    }
  };
}

function readStoredReport(
  storage: Storage
): ParseResult<ReportData> {
  const text = storage.getItem("monthly-report");
  if (text === null) return { ok: false, reason: "missing" };
  return parseReportData(text);
}

const manualResult = parseReportData(`
{
  "viewer": {
    "id": "u-7",
    "role": "reader"
  },
  "rows": [
    {
      "id": "r-21",
      "title": "北区月报",
      "month": "2026-10",
      "region": "north",
      "status": "published",
      "total": 820,
      "ownerEmail": "ada@example.com"
    }
  ]
}
`);
~~~

逐段看这段代码在编译期和运行时各做了什么。TypeScript 标准库把 `JSON.parse` 的返回类型声明为 `any`；把结果赋给 `let input: unknown`，只改变编译器看到的类型，运行时仍是同一个值，没有任何验证或转换。`isRecord` 里“是对象、不是 `null`、不是数组”这几个条件会在运行时真正执行；而返回类型 `value is Record<string, unknown>`（类型谓词）只是函数对编译器的承诺：返回 `true` 时值就是这种类型。编译器据此放行后续的属性访问，但不会替函数证明承诺成立，所以函数里的布尔检查必须与类型谓词一致。另外，标准库中 `Array.isArray` 的类型谓词会把值缩窄成 `any[]`，因此代码立即把 `input.rows` 赋给 `unknown[]`，让循环里的每个 `candidate` 仍必须先检查再读取。

这个解析器保证的范围也要说清楚。

- **格式规则只在运行时生效。** 它检查月份符合 `YYYY-MM`、`total` 是有限数值，但返回类型里两者仍是普通的 `string` 和 `number`，这两条规则没有写进静态类型。如果业务还要求金额非负、地区来自配置清单等，应把规则加进运行时解析，而不是只修改 TypeScript 类型。
- **未声明的字段会被丢弃。** 解析器只用已检查的字段重建 `ReportData`，输入中多出的字段不会出现在结果里。
- **它不做授权判断。** 解析成功不能证明 `viewer.id` 是当前登录用户，也不能证明该用户有权查看报表；这些判断必须由可信的服务端完成。
- **它不处理存储故障。** `readStoredReport` 只把缺失项转换成 `missing`，不捕获访问存储时的异常：调用方读取 `localStorage` 属性本身就可能因来源或浏览器策略抛出 `SecurityError`，`getItem` 的其他异常也会继续向上抛。调用方应按自己的降级策略处理，不要把存储故障误报成 JSON 语法错误。

## 怎样用 Zod 在同一个输入边界生成运行时检查和静态类型？

手写检查一长，字段路径和类型判断就会大量重复。这时可以在同一个报表 JSON 入口改用 schema（结构模式）库：只声明一次字段结构，就同时得到运行时检查和静态类型。下面使用 Zod `4.6.7`（截至 2026-11-17 的 npm 最新版），声明与上例相同的字段，但两种检查接受的输入并不完全相同：

- 遇到未声明的键时，手写解析器重建已知字段、忽略额外键；这里用的 `z.strictObject` 会直接拒绝；默认的 `z.object` 则会去掉未知键后通过。
- Zod 版本要求 `ownerEmail` 符合邮箱格式，手写版本只要求它是字符串。

是否拒绝额外键、邮箱校验要多严格，应按接口契约决定。无论选哪种，都不能为了拿到 `z.infer` 推出的类型，就把未经检查的外部数据直接断言成这个类型。

~~~typescript
import * as z from "zod"; // zod@4.6.7

const ReportRowSchema = z.strictObject({
  id: z.string(),
  title: z.string(),
  month: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/),
  region: z.string(),
  status: z.enum(["open", "published", "archived"]),
  total: z.number(), // Zod 4 的 number schema 只接受有限数值
  ownerEmail: z.email(),
});

const ReportDataSchema = z.strictObject({
  viewer: z.strictObject({
    id: z.string(),
    role: z.enum(["admin", "reader"]),
  }),
  rows: z.array(ReportRowSchema),
});

type ReportDataFromSchema = z.infer<typeof ReportDataSchema>;

function parseReportDataWithZod(
  text: string
): ParseResult<ReportDataFromSchema> {
  let input: unknown;
  try {
    input = JSON.parse(text);
  } catch {
    return { ok: false, reason: "syntax" };
  }

  const parsed = ReportDataSchema.safeParse(input);
  if (!parsed.success) {
    const firstIssue = parsed.error.issues[0];
    console.log(firstIssue?.path, firstIssue?.message);
    return { ok: false, reason: "shape" };
  }
  return { ok: true, value: parsed.data };
}

const zodResult = parseReportDataWithZod(`
{
  "viewer": {
    "id": "u-7",
    "role": "reader"
  },
  "rows": [
    {
      "id": "r-21",
      "title": "北区月报",
      "month": "2026-10",
      "region": "north",
      "status": "published",
      "total": "820",
      "ownerEmail": "ada@example.com"
    }
  ]
}
`);
// 第一个结构错误的 path 为 ["rows", 0, "total"]。
// 字符串不会被默默转成数字。
~~~

流程与手写版一致：JSON 语法仍先交给 `JSON.parse`；解析成功后 `input` 的静态类型是 `unknown`，再由 `safeParse` 在运行时检查字段和值。成功分支的 `parsed.data` 已经过校验，类型是从 schema 推导出的 `ReportDataFromSchema`。失败分支的 `ZodError.issues` 是结构化的问题列表，每个问题的 `path` 用字段名和数组下标定位，例如 `rows` 第 0 项的 `total` 对应 `["rows", 0, "total"]`，而不是 JSON 文本中的行号和列号。如果问题是出现了未声明的键，路径可能只指到包含它的对象（如 `["rows", 0]`），具体键名写在问题消息里。

两个示例的输入只差一处：手写示例的 `total` 是数值 `820`，因此通过；Zod 示例故意改成字符串 `"820"`。它仍是语法合法的 JSON，但 Zod 的结构检查会拒绝它；同样的输入交给手写解析器也会被拒绝，因为后者要求 `total` 在运行时就是 `number`。包装函数只打印第一个问题，返回给调用方的是 `{ ok: false, reason: "shape" }`，不会把完整的问题列表传出去。所以下一节末尾的 `if (zodResult.ok)` 分支不会执行。

Zod 4 的 `z.number()` 本身就拒绝 `NaN` 和正负无穷，所以 schema 里没有再加有限数检查。同样的思路也用于服务端：Python 服务可以用 Pydantic 模型检查请求，FastAPI 还会根据路由和模型声明生成 OpenAPI 契约，但实际响应是否符合契约仍要另外核验，见[HTTP API 如何描述实际运行的请求与响应契约](../../engineering-foundations/backend/http-api-contracts.md)。Zod 和 Pydantic 做的都是运行时输入检查；`z.infer` 只是让后续 TypeScript 代码在编译期沿用同一结构，它本身不会让网络数据、浏览器存储内容或授权结果变得可信。

## 类型联合新增分支时怎样让编译器提醒调用处？

通过检查的数据进入应用后，还有另一类风险：类型定义改了，使用它的代码却没跟上。解析器只接受 `admin` 和 `reader` 两种角色；调用端按角色分支处理时，可以在默认分支里把值赋给 `never`（不可能出现的类型），这叫 exhaustiveness checking（穷尽性检查）。以后若把 `editor` 加进 `Role`，却忘了在下面补上对应分支，类型检查就会在这次 `never` 赋值处报错。如果外部数据确实会出现 `editor`，还必须同步修改上面的运行时解析器；只扩充联合类型和显示分支，`editor` 仍会在输入检查时被拒绝。这里的标签只用于界面显示，不是授权判断。

~~~typescript
function roleLabel(role: Role): string {
  switch (role) {
    case "admin":
      return "管理员";
    case "reader":
      return "只读用户";
    default: {
      const unhandled: never = role;
      throw new Error(`未处理的角色：${unhandled}`);
    }
  }
}

if (manualResult.ok) {
  console.log(roleLabel(manualResult.value.viewer.role));
}
if (zodResult.ok) {
  console.log(roleLabel(zodResult.value.viewer.role));
}
~~~

这两道检查守的是不同的边界：运行时解析器决定外部值能否进入应用；穷尽性检查则在编译期提醒开发者，应用类型中所有已支持的分支是否都处理到了。泛型和工具类型也只描述编译期关系，见[泛型怎样保留输入与输出之间的类型关系？](./generics.md)与[怎样从报表类型派生数据形状并约束方法中的 `this`？](./utility-types.md)。

> [!info]- 来源
> - [TypeScript Handbook：unknown 与类型缩窄](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
> - [TypeScript Handbook：断言与类型兼容](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions)、[类型兼容与健全性取舍](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness)
> - [TypeScript Handbook：穷尽性检查](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)
> - **Zod `4.6.7`：** [版本发布记录](https://github.com/colinhacks/zod/releases/tag/v4.6.7)、[4.6.7 文档与源码](https://github.com/colinhacks/zod/tree/v4.6.7/packages/docs/content)、[对象 schema 与 strict keys](https://zod.dev/api?id=objects)、[`safeParse` 与 `z.infer`](https://zod.dev/basics)、[错误 issue 路径](https://zod.dev/packages/core#issues)、[Zod 4 的格式 API](https://zod.dev/v4)。已在隔离的临时目录安装此版本，TypeScript 编译并于 Node `v26.13.0` 运行核对，2026-11-12。
>
> 按 `JSON.parse` 的语法错误、存储缺失值，以及报表结构检查整理；[TypeScript 类型注解会在输出 JavaScript 时擦除](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，`localStorage` 属性访问可能抛出的 `SecurityError` 见 [HTML Standard：localStorage](https://html.spec.whatwg.org/multipage/webstorage.html#dom-localstorage)。来源核对日期：2026-11-12。
