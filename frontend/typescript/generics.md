# 泛型怎样保留输入与输出之间的类型关系？

报表页要处理多种行数据和分页结果。如果为每种数据各复制一份函数，维护成本很高；如果一律把参数和返回值写成 `any`（任意类型），调用处又会丢掉具体的字段信息。generic（泛型）让同一段逻辑在每次调用时保留具体的类型。

## 怎样把所选字段的类型一并保留下来？

type parameter（类型参数）相当于类型层面的变量：编译器可以从调用参数推断它，调用者也可以显式指定。下面的 `getProperty` 用 `T` 代表整行的类型；`keyof T` 得到 `T` 所有键名组成的联合类型，`K` 被约束在其中，只能取该行已有的键；indexed access type（索引访问类型）`T[K]` 再取出所选键对应的值类型。

~~~typescript
type ReportRow = {
  id: string;
  title: string;
  month: string;
  region: string;
  status: "open" | "published" | "archived";
  total: number;
  ownerEmail: string;
};

function getProperty<T, K extends keyof T>(row: T, key: K): T[K] {
  return row[key];
}

const row: ReportRow = {
  id: "r-21",
  title: "北区月报",
  month: "2026-10",
  region: "north",
  status: "published",
  total: 820,
  ownerEmail: "ada@example.com"
};

const reportId = getProperty(row, "id");       // string
const reportTotal = getProperty(row, "total"); // number
const statusOrTotalKey: "status" | "total" =
  Math.random() < 0.5 ? "status" : "total";
// ReportRow["status"] | number
const statusOrTotal = getProperty(row, statusOrTotalKey);
// getProperty(row, "owner");                  // 编译错误：不是 ReportRow 的键
~~~

`T` 和 `K` 是分别推断的两个类型参数：`T` 记住行的形状；`K extends keyof T` 里的 `extends` 表示 constraint（约束），要求本次传入的键属于这一行已有的键。返回类型 `T[K]` 按 `K` 取出对应字段的类型。

把一次调用拆开看：编译器先从 `row` 推断出 `T`，再由传入的字面量键推断出 `K` 并检查它是否在 `keyof T` 内，最后计算 `T[K]`：

| 调用与推导 | 返回类型 |
|---|---|
| `getProperty(row, "id")`：`T = ReportRow`，`K = "id"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["id"]`，为 `string` |
| `getProperty(row, "total")`：`T = ReportRow`，`K = "total"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["total"]`，为 `number` |
| `getProperty(row, statusOrTotalKey)`：`T = ReportRow`，`K` 是 `"status"` 和 `"total"` 组成的联合 | `T[K]` 是 `ReportRow["status"]` 与 `number` 的联合 |

为键单独设一个类型参数 `K` 很重要。如果签名把参数直接写成 `keyof T`、返回值写成 `T[keyof T]`，那么即使传入字面量 `"id"`，返回类型也是所有字段值类型的联合。保留 `K` 后，传入的键是几个键的联合时，`T[K]` 也只合并这几个键对应的字段类型：例如 `"status" | "total"` 得到 `ReportRow["status"] | number`。只有 `K` 是完整的 `keyof ReportRow` 时，结果才覆盖全部字段，本例为 `string | number`。泛型约束只保证编译器看到的键有效，运行时并不会校验键或行数据。

## 怎样让分页与仓储接口为不同数据复用？

泛型不只用于单个函数，也可以把类型关系保留在数据结构和一组操作中。报表页面拿到 `ReportPage<ReportRow>`，下游仍知道 `rows` 里的每一项是报表行；同一容器也能装其他数据，而不必退化成 `unknown[]` 或 `any[]`。

~~~typescript
type ReportPage<T> = {
  rows: T[];
  total: number;
  nextCursor: string | null;
};

interface Repository<T> {
  getById(id: string): T | undefined;
  getAll(): T[];
  save(item: T): void;
}

function firstRow<T>(page: ReportPage<T>): T | undefined {
  return page.rows[0];
}

const reports: ReportPage<ReportRow> = {
  rows: [row],
  total: 1,
  nextCursor: null
};
const emptyPage: ReportPage<ReportRow> = {
  rows: [],
  total: 0,
  nextCursor: null
};
const first = firstRow(reports);
if (first) first.total.toFixed(2); // first.total 仍是 number
console.log(firstRow(emptyPage)); // undefined：空页没有第一行
~~~

`reports` 的类型是 `ReportPage<ReportRow>`；传给 `firstRow<T>` 时，参数形状让编译器推断 `T = ReportRow`，因此 `first` 是 `ReportRow | undefined`。`Repository<ReportRow>` 也把同一个 `T` 替换到每个操作：`getById` 返回 `ReportRow | undefined`，`getAll` 返回 `ReportRow[]`，`save` 接收 `ReportRow`。

泛型保留的是编译器掌握的关系；它不会在运行时检查服务器是否真的返回 `ReportRow`。来自网络或存储的外部输入应先保持为 `unknown` 并逐项验证，见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。工具类型则可进一步从 `ReportRow` 派生列表预览或更新请求形状，见[怎样从报表类型派生数据形状并约束方法中的 `this`？](./utility-types.md)。

> [!info]- 来源
> - [TypeScript Handbook：泛型与类型参数推断](https://www.typescriptlang.org/docs/handbook/2/generics.html)
> - [TypeScript Handbook：`keyof` 类型操作符](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)、[索引访问类型](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
>
> 来源核对日期：2026-11-12。代码以 TypeScript 5.7.2 执行严格模式和 `noUncheckedIndexedAccess` 检查。
