# 泛型怎样保留输入与输出之间的类型关系？

报表页会处理很多种行数据：月度汇总行、权限信息和分页结果。若每个函数都复制一份实现，维护成本很高；若一律把参数和返回值写成 `any`（任意类型），调用处又会丢掉具体字段信息。generic（泛型）让同一段逻辑保留调用时的具体类型。

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
// getProperty(row, "owner");                  // 编译错误：不是 ReportRow 的键
~~~

`K extends keyof T` 中的 `extends` 是 constraint（约束），意思是 `K` 必须属于允许的键集合。没有这个约束，函数就无法安全访问 `row[key]`。由于返回值是 `T[K]`，读 `id` 得到 `string`，读 `total` 得到 `number`；若把返回类型写成 `T[keyof T]`，结果会变成所有字段类型的联合。

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

泛型保留的是编译器掌握的关系；它不会在运行时检查服务器是否真的返回 `ReportRow`。真实输入仍应先保持为 `unknown` 并逐项验证，见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。工具类型则可进一步从 `ReportRow` 派生只读表格行或更新请求形状，见[怎样从报表行派生预览、更新请求和状态标签？](./utility-types.md)。

> [!info]- 来源
> - [TypeScript Handbook：泛型与类型参数推断](https://www.typescriptlang.org/docs/handbook/2/generics.html)
> - [TypeScript Handbook：`keyof` 类型操作符](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)、[索引访问类型](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
>
> 来源核对日期：2026-11-06。代码以 TypeScript 5.7.2 执行严格模式检查。
