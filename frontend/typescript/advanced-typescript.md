# 收到不可信 JSON 后，TypeScript 怎样建立可信的类型？

月度报表页从接口或浏览器存储读入数据时，输入内容在运行时仍只是外部值。TypeScript 的类型注解会在输出 JavaScript 时擦除；它们能检查我们写下的代码，却不会替 `JSON.parse` 检查实际字段，也不会验证用户是否有权访问某份报表。

因此，数据要经过两个不同步骤：先解析 JSON（JavaScript 对象表示法）语法，再按运行时规则检查结构和取值。成功后从已检查字段重新构造应用对象，后续代码才可以依赖这个对象的静态类型。图只画运行时执行链；`unknown` 是编译期的静态边界，不是 JSON 解析后的运行时转换。

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

如果文本来自浏览器存储，`getItem` 返回 `null` 时会在进入这条共用链之前返回 `missing`。

## 怎样在运行时检查报表数据？

`unknown`（未知类型）允许一个值暂时存在，但在缩窄到更具体类型前不允许任意读取属性。下面的解析器分别处理语法错误、缺失存储值和字段结构错误；每个通过的行都被重新构造成 `ReportRow`，而不是把外部对象直接断言成该类型。

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

TypeScript 标准库把 `JSON.parse` 的返回类型声明为 `any`。赋给 `let input: unknown` 只改变编译器看到的静态类型；运行时仍是 `JSON.parse` 得到的同一个值，并没有自动验证或转换。`isRecord` 内部的对象、非 `null`、非数组条件会实际运行；返回类型 `value is Record<string, unknown>` 则是函数向编译器作出的缩窄承诺，编译器依据它分析后续属性访问，不会替函数证明该承诺正确。实现中的布尔检查和类型谓词必须保持一致。`Array.isArray` 在 TypeScript 标准库中的类型谓词会把值缩窄为 `any[]`，所以这里立即把 `input.rows` 赋给 `unknown[]`，让循环中的每个 `candidate` 仍须先检查再读取。

解析器现在只保证字段形状和示例所写的格式规则。它在运行时检查月份符合 `YYYY-MM` 形式、`total` 是有限数值，但返回类型仍分别是普通 `string` 和 `number`，并未把这两条细则编码进静态类型。解析器按已检查字段重建 `ReportData`，因此忽略并丢弃未声明字段；它不证明 `viewer.id` 是当前登录用户，也不证明该用户可以查看报表，这些授权判断必须由受信任的服务端完成。若业务还要求金额非负、地区来自配置清单等约束，应把对应规则也写入运行时解析，而不是只扩大 TypeScript 类型。`readStoredReport` 把缺失项转换为 `missing`，但不捕获存储访问异常：调用时读取 `localStorage` 可能因来源或策略抛出 `SecurityError`，而 `getItem` 的其他异常也会向上抛出。调用方应按自身降级策略处理，不要把存储故障误报成 JSON 语法错误。

## 怎样用 Zod 在同一个输入边界生成运行时检查和静态类型？

如果手写检查开始重复字段路径和类型判断，可以在同一个报表 JSON 边界使用 schema（结构模式）。下面固定用 Zod `4.6.7`，声明与上例相同的字段形状，但两种检查的接纳规则并不相同：手写解析器重建已知字段并忽略额外键，`z.strictObject` 会拒绝额外键；默认的 `z.object` 则会剥除未知键。Zod 还要求 `ownerEmail` 符合邮箱格式，而手写版本只要求它是字符串。是否拒绝额外键、邮箱需要多严格，应按接口契约决定。不能只为了得到 `z.infer` 类型就把宽泛外部数据断言成模型。

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

JSON 语法仍先由 `JSON.parse` 处理；成功后 `input` 是静态 `unknown`，`safeParse` 再实际检查字段和值。成功分支的 `parsed.data` 是已校验并推导出的 `ReportDataFromSchema`。失败分支的 `ZodError.issues` 保存结构化问题；`path` 用字段键和数组索引定位，例如 `rows` 第 0 项的 `total` 对应 `["rows", 0, "total"]`，不是 JSON 文本的行号和列号。遇到未声明键时，路径可能只到包含它的对象（如 `["rows", 0]`），具体键名在问题消息中。手写示例的 `total` 是数值 `820`，所以通过；Zod 示例将该字段改为字符串 `"820"`，虽然仍是语法合法的 JSON，Zod 结构检查会拒绝它。同一个字符串输入也会被手写解析器拒绝，因为它要求 `total` 的运行时类型是 `number`。包装函数打印首个 issue 后只向调用者返回 `{ ok: false, reason: "shape" }`，不会把完整 issue 传出去。后文的 `if (zodResult.ok)` 因此不会调用角色标签函数。

Zod 4 的 `z.number()` 已拒绝 `NaN` 与正负无穷，因此这里不再重复加有限数检查。服务器侧可用 Pydantic 模型检查请求，FastAPI 则从路由与模型声明生成 OpenAPI 契约；实际响应是否兑现契约仍需核验，见[HTTP API 如何描述实际运行的请求与响应契约](../../engineering-foundations/backend/http-api-contracts.md)。Zod 与 Pydantic 都检查运行时输入；TypeScript 的 `z.infer` 只帮助后续代码在编译期保持同一结构，不会自动让网络载荷、浏览器存储或授权可信。

## 类型联合新增分支时怎样让编译器提醒调用处？

解析器仅接受已知角色。调用端在分支中处理角色时，可以把默认分支赋给 `never`（不可能出现的类型）。若以后把 `editor` 加入 `Role`，但忘了补充下列分支，类型检查会在 `never` 赋值处报错。若 `editor` 是外部数据允许的新角色，还必须同步让上面的运行时解析器接受它；只扩充联合类型和显示分支不会使它通过输入检查。这里的标签仅用于界面显示，不是授权判断。

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

这两道检查覆盖不同边界：运行时解析器决定外部值是否进入应用；穷尽性检查提醒开发者是否处理了应用类型中所有已支持的分支。泛型和工具类型也只描述编译期关系，见[泛型怎样保留输入与输出之间的类型关系？](./generics.md)与[怎样从报表类型派生数据形状并约束方法中的 `this`？](./utility-types.md)。

> [!info]- 来源
> - [TypeScript Handbook：unknown 与类型缩窄](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
> - [TypeScript Handbook：断言与类型兼容](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions)、[类型兼容与健全性取舍](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness)
> - [TypeScript Handbook：穷尽性检查](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)
> - **Zod `4.6.7`：** [版本发布记录](https://github.com/colinhacks/zod/releases/tag/v4.6.7)、[4.6.7 文档与源码](https://github.com/colinhacks/zod/tree/v4.6.7/packages/docs/content)、[对象 schema 与 strict keys](https://zod.dev/api?id=objects)、[`safeParse` 与 `z.infer`](https://zod.dev/basics)、[错误 issue 路径](https://zod.dev/packages/core#issues)、[Zod 4 的格式 API](https://zod.dev/v4)。已在隔离的临时目录安装此版本，TypeScript 编译并于 Node `v26.13.0` 运行核对，2026-11-12。
>
> 按 `JSON.parse` 的语法错误、存储缺失值，以及报表结构检查整理；[TypeScript 类型注解会在输出 JavaScript 时擦除](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，`localStorage` 属性访问可能抛出的 `SecurityError` 见 [HTML Standard：localStorage](https://html.spec.whatwg.org/multipage/webstorage.html#dom-localstorage)。来源核对日期：2026-11-12。
