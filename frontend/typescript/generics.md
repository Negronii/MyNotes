# 泛型怎样保留输入与输出之间的类型关系？

报表页会处理很多种行数据和分页结果。若每个函数都复制一份实现，维护成本很高；若一律把参数和返回值写成 `any`（任意类型），调用处又会丢掉具体字段信息。generic（泛型）让同一段逻辑保留调用时的具体类型。

## 怎样把所选字段的类型一并保留下来？

type parameter（类型参数）像是类型层面的变量。编译器可以从调用参数推断它，也可以由调用者显式指定。下面的 `T` 代表整行类型，`K` 受 `keyof T`（类型键集合）约束，只能取该类型已有的键；indexed access type（索引访问类型）`T[K]` 则返回所选键对应的值类型。

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

`T` 与 `K` 是两个分别推断的类型参数：`T` 保留行形状，`K extends keyof T` 中的 `extends` 是 constraint（约束），要求本次传入的键属于该行已有的键。返回类型 `T[K]` 再按 `K` 取属性值类型，因此单键 `"id"` 得到 `string`，单键 `"total"` 得到 `number`。

把一次调用拆开看，编译器先从 `row` 得到 `T`，再把键限制在 `keyof T` 内，并由传入的字面量键推断 `K`，最后计算 `T[K]`：

| 调用与推导 | 返回类型 |
|---|---|
| `getProperty(row, "id")`：`T = ReportRow`，`K = "id"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["id"]`，为 `string` |
| `getProperty(row, "total")`：`T = ReportRow`，`K = "total"`，满足 `K extends keyof T` | `T[K]`，即 `ReportRow["total"]`，为 `number` |
| `getProperty(row, statusOrTotalKey)`：`T = ReportRow`，`K` 是 `"status"` 和 `"total"` 组成的联合 | `T[K]` 是 `ReportRow["status"]` 与 `number` 的联合 |

单独保留 `K` 很重要：若签名只把参数写成 `keyof T`、返回值写成 `T[keyof T]`，即使传入字面量 `"id"`，返回类型也会包含字段值类型的联合。若调用者只掌握部分键组成的联合，`T[K]` 只合并这些键对应的字段类型；例如 `"status" | "total"` 得到 `ReportRow["status"] | number`。只有 `K = keyof ReportRow` 时才覆盖全部字段，本例的结果为 `string | number`。泛型约束保证编译器看到的键有效，不在运行时校验键或行数据。

## 怎样让分页与仓储接口为不同数据复用？

泛型也可把类型关系保留在对象结构和一组操作中。报表页面拿到 `ReportPage<ReportRow>`，下游仍知道 `rows` 里的每一项是报表行；同一容器也能装其他数据，而不必退化成 `unknown[]` 或 `any[]`。

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
