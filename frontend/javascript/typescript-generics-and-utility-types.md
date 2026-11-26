# 泛型和工具类型怎样从已有类型推出新类型？

为每种数据各写一份函数，维护成本高；一律写成 `any` (任意类型)，调用处又丢掉了字段信息。generic (泛型)让同一段逻辑在每次调用时保留具体类型；utility type (工具类型)则从已有类型推出新的形状，例如列表预览和局部更新。本章依次讲类型参数、`keyof` 与索引访问、泛型容器、常用工具类型、分配式条件类型，以及怎样给方法里的 `this` 提供类型。

本章是[TypeScript 能保证什么，外部数据又该怎样验证？](./typescript-guarantees-and-runtime-validation.md)的支线，沿用那里报表页的行类型 `ReportRow` 和行数据 r-104。这里讲的一切都只作用于编译期：不会在运行时筛选字段、验证数据，也不会替方法绑定 `this`。

```typescript
type ReportStatus = "open" | "published" | "archived";

interface ReportRow {
  id: string;
  title: string;
  month: string;
  status: ReportStatus;
  amount: number;
  ownerEmail: string;
}

const row: ReportRow = {
  id: "r-104",
  title: "May",
  month: "2026-05",
  status: "open",
  amount: 120,
  ownerEmail: "ada@example.com",
};
```

## 取一个字段时，怎样保留它的类型？

type parameter (类型参数)相当于类型层面的变量：编译器可以从调用参数推断它，调用者也可以显式指定。

下面的 `getProperty` 用 `T` 代表整行的类型。`keyof T` 是 `T` 所有键名组成的联合类型；`K extends keyof T` 里的 `extends` 表示 constraint (约束)，要求传入的键属于这一行已有的键；indexed access type (索引访问类型)`T[K]` 再取出所选键对应的值类型。

```typescript
function getProperty<T, K extends keyof T>(row: T, key: K): T[K] {
  return row[key];
}

const reportId = getProperty(row, "id");       // string
const reportAmount = getProperty(row, "amount"); // number

const statusOrAmountKey: "status" | "amount" =
  Math.random() < 0.5 ? "status" : "amount";
const statusOrAmount = getProperty(row, statusOrAmountKey); // ReportStatus | number

// getProperty(row, "owner"); // 编译错误："owner" 不是 ReportRow 的键
```

编译器对每次调用做三件事：从 `row` 推断 `T`，从传入的键推断 `K` 并检查它在 `keyof T` 内，再计算 `T[K]`：

| 调用 | 推断 | 返回类型 |
| --- | --- | --- |
| `getProperty(row, "id")` | `T = ReportRow`，`K = "id"` | `ReportRow["id"]`，即 `string` |
| `getProperty(row, "amount")` | `T = ReportRow`，`K = "amount"` | `ReportRow["amount"]`，即 `number` |
| `getProperty(row, statusOrAmountKey)` | `T = ReportRow`，`K = "status" \| "amount"` | `ReportStatus \| number` |

为键单独设类型参数 `K` 是关键。如果签名写成 `(row: T, key: keyof T): T[keyof T]`，即使传入字面量 `"id"`，返回类型也是所有字段值类型的联合，本例为 `string | number`。保留 `K` 之后，`T[K]` 只合并实际传入的那几个键对应的类型。

约束只保证编译器看到的键有效。运行时并不校验键，也不校验行数据本身。

## 怎样让分页和仓储接口复用于不同数据？

泛型也可以把类型关系保留在数据结构和一组操作里。报表页拿到 `ReportPage<ReportRow>`，下游仍知道 `rows` 里每一项都是报表行；同一个容器也能装别的数据，而不必退化成 `unknown[]` 或 `any[]`。

```typescript
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

const reports: ReportPage<ReportRow> = { rows: [row], total: 1, nextCursor: null };
const emptyPage: ReportPage<ReportRow> = { rows: [], total: 0, nextCursor: null };

const first = firstRow(reports);
if (first) first.amount.toFixed(2); // first.amount 仍是 number
console.log(firstRow(emptyPage));  // undefined：空页没有第一行
```

传入 `reports` 时，编译器从参数形状推断 `T = ReportRow`，所以 `first` 的类型是 `ReportRow | undefined`。`Repository<ReportRow>` 把同一个 `T` 代入每个操作：`getById` 返回 `ReportRow | undefined`，`getAll` 返回 `ReportRow[]`，`save` 接收 `ReportRow`。

泛型保留的是编译器掌握的关系。服务器是否真的返回 `ReportRow`，仍要在数据边界按三步检查。

## Pick、Partial、Record 改变了什么？

列表预览、局部更新、状态标签这些形状，都可以从 `ReportRow` 推出来，不必再手写一遍：

```typescript
type ReportPreview = Pick<ReportRow, "id" | "title" | "month" | "amount">;
type ReportPatch = Partial<Pick<ReportRow, "title" | "month">>;
type StatusLabels = Record<ReportStatus, string>;

const labels: StatusLabels = {
  open: "待审核",
  published: "已发布",
  archived: "已归档",
};
```

嵌套的工具类型由内向外读：`Pick` 先取出 `title` 和 `month`，`Partial` 再把它们变成可选，结果是 `{ title?: string; month?: string }`。

`StatusLabels` 要求 `ReportStatus` 的每个成员都有标签。以后给 `ReportStatus` 加上 `"scheduled"`，`labels` 会因缺少这个键而报错，提醒界面补上新状态的文字。状态标签和行类型共用同一个联合，两处定义就不会各改各的。

这些工具只改变类型，不碰对象：

```typescript
const input = { month: "2026-06", ownerEmail: "eve@example.com" };
const patch: ReportPatch = input;
console.log(Object.keys(patch)); // ["month", "ownerEmail"]：仍是同一个运行时对象
```

`input` 与 `ReportPatch` 有共同的键 `month`，所以可以赋值；多出的 `ownerEmail` 没有被删掉。有两种情况会被编译器拦下：

- 变量里只有 `ownerEmail`，和目标类型没有任何共同属性。目标类型的属性全部可选，TypeScript 称这种类型为 weak type，此时赋值报错。
- 直接把含 `ownerEmail` 的**新对象字面量**赋给 `ReportPatch`，会触发多余属性检查。

可见 `Pick` 只在类型上筛字段。列表展示如果真的只想带这几个字段，要在运行时构造新对象。

## 省略、null、undefined 有什么不同？

局部更新里，“没传这个字段”“传了 `null`”“传了 `undefined`”是三种状态，接口要先约定它们各自的含义。

- **省略。** `ReportPatch` 的字段可选，不写就是“不修改”。
- **`null`。** 开启 `strictNullChecks`（`strict` 已包含）后，`{ title: null }` 不能赋给 `ReportPatch`。只有接口约定 `null` 表示“清空该字段”这类业务操作时，才在属性类型里加 `| null`，并让运行时解析按这层含义处理。
- **`undefined`。** 开启 `exactOptionalPropertyTypes`（它要求同时开启 `strictNullChecks`）后，可选字段可以省略，但除非类型里写了 `undefined`，否则不能显式赋值为 `undefined`；不开启时编译器允许这样赋值。

无论这个开关怎样设置，读取 `patch.title` 都可能得到 `undefined`，因为属性本身可以不存在。

更新数据来自网络或存储时，运行时仍要按接口白名单检查字段，并区分省略、`null` 和具体值；本地按 `ReportPatch` 构造的对象则由编译器检查。

## 常用工具类型速查

| 需要 | 工具类型 | 结果与边界 |
| --- | --- | --- |
| 只声明所需字段 | `Pick<T, K>` / `Omit<T, K>` | 选取或排除键；不复制、不投影对象 |
| 部分更新，或补齐默认值后的完整配置 | `Partial<T>` / `Required<T>` | 属性变为可选或必需；运行时仍需合并、检查 |
| 只读视图 | `Readonly<T>` | 浅层禁止通过该类型给属性重新赋值；不冻结对象 |
| 一组键到值的映射 | `Record<K, V>` | 约束键和值的类型；动态输入仍须验证 |
| 从联合中筛选成员 | `Exclude<U, X>` / `Extract<U, X>` | 移除或保留可赋给 `X` 的成员 |
| 去掉 `null` 和 `undefined` | `NonNullable<T>` | 只改静态类型，不替值做空值检查 |
| 读取函数签名 | `Parameters<F>` / `ReturnType<F>` | 参数元组或返回类型；重载函数取最后一个签名 |
| 读取构造签名 | `ConstructorParameters<C>` / `InstanceType<C>` | 构造参数元组或实例类型 |
| 解开 Promise | `Awaited<T>` | 递归解包 Promise 及符合其 `then` 约定的类型；不等待运行时值 |

这些工具大多由 mapped type (映射类型)、conditional type (条件类型)和索引访问类型组合而成。其中 `Exclude`、`Extract` 依赖条件类型的一条特殊规则，下一节单独说明。

## 条件类型遇到联合，为什么会逐项筛选？

条件类型写作 `T extends X ? A : B`。如果 `extends` 左边是一个“裸”类型参数（没有包进数组、元组等结构），传入联合类型时，编译器把联合成员逐个代入，再把结果合成联合。这叫 distributive conditional type (分配式条件类型)。

```typescript
type WithoutArchived<T> = T extends "archived" ? never : T;
type VisibleStatus = WithoutArchived<ReportStatus>;
// "open" | "published" | never  →  "open" | "published"

type IsArchived<T> = T extends "archived" ? true : false;
type DistributedCheck = IsArchived<ReportStatus>;
// false | false | true  →  boolean

type IsWholeUnionArchived<T> = [T] extends ["archived"] ? true : false;
type WholeStatusCheck = IsWholeUnionArchived<ReportStatus>;
// 不分配，整个联合与 "archived" 比较  →  false
```

逐个看：

- `WithoutArchived` 对三个成员分别得到 `"open"`、`"published"`、`never`。`never` 没有任何值，在联合中被吸收，结果只剩前两个。内置的 `Exclude<ReportStatus, "archived">` 就是这样实现的，结果相同。
- `IsArchived` 和 `IsWholeUnionArchived` 的分支完全一样，区别只在 `T` 是否“裸”。裸 `T` 会分配，三个成员得到 `false`、`false`、`true`，合起来是 `boolean`。
- 把 `T` 包进元组 `[T]` 就不再分配，比较的是整个联合是否可赋给 `"archived"`，答案是 `false`。

需要“对整个联合作判断”时，用元组包一层；需要“逐个成员筛选”时，保持裸参数。

## 对象字面量方法里的 this 怎样获得类型？

前面的工具都在推导数据形状。另一类问题出在方法上：对象字面量里的方法默认不知道 `this` 指向什么。TypeScript 有两种办法在编译期提供这个信息，它们都不在运行时绑定 `this`；`this` 实际是什么，仍按[函数里的变量和 this 从哪来？](./scope-closures-and-this.md)里的调用规则决定。

**`ThisType<T>`。** 它是一个标记接口。作为对象字面量的上下文类型时，其中的方法把 `this` 当作 `T`。它不添加属性，不改变对象，只在开启 `noImplicitThis`（`strict` 已包含）时生效。

```typescript
type ObjectDescriptor<Data, Methods> = {
  data: Data;
  methods: Methods & ThisType<Data & Methods>;
};

function makeObject<Data, Methods>(
  descriptor: ObjectDescriptor<Data, Methods>
): Data & Methods {
  return { ...descriptor.data, ...descriptor.methods };
}

const rowCounter = makeObject({
  data: { loadedRows: 0 },
  methods: {
    addLoadedRow() {
      this.loadedRows += 1; // this 有 loadedRows: number
    },
  },
});

rowCounter.addLoadedRow();
console.log(rowCounter.loadedRows); // 1
```

编译器从 `data` 推断 `Data = { loadedRows: number }`，从 `methods` 推断含 `addLoadedRow` 的 `Methods`，`ThisType<Data & Methods>` 再把两边的成员提供给方法体里的 `this`。运行时，`makeObject` 用对象展开合并两个对象，`rowCounter.addLoadedRow()` 这次成员调用提供了接收者，计数变为 1。

这个小例子只适用于数据和方法都是普通对象、所需成员都是可枚举自有属性的情况，因为对象展开不复制原型上的方法。`Data & Methods` 也不禁止两边有重名键：重名时后展开的 `methods` 覆盖 `data`，交叉类型却可能描述了冲突的字段。本例让两边键名不重叠。

**显式的 `this` 参数。** 在函数签名里声明接收者的类型：

```typescript
interface ReportViewer {
  name: string;
  describe(this: ReportViewer): string;
}

const viewer: ReportViewer = {
  name: "Ada",
  describe() {
    return `报表查看者：${this.name}`;
  },
};

console.log(viewer.describe()); // 报表查看者：Ada
```

`this: ReportViewer` 是编译期对**调用方式**的要求。两种办法的差别在方法被单独取出时显现：

- `const d = viewer.describe; d();` 编译报错，因为调用时缺少所需的 `this`。在严格模式（含 ES 模块）下运行，`this` 是 `undefined`，读 `this.name` 确实会抛 `TypeError`。
- `const add = rowCounter.addLoadedRow; add();` 能通过静态检查，因为 `ThisType` 只给方法体内部提供类型，不约束调用方；运行时 `this` 已经不对。

## 推出来的类型交回哪里

本支线给出了从已有类型推导新类型的工具：类型参数在调用之间保留关系，`keyof` 与 `T[K]` 让取字段保留字段类型，工具类型推出预览、补丁和标签映射，分配式条件类型逐项筛选联合，`ThisType` 和 `this` 参数在编译期描述接收者。

它们都只描述编译期关系。`ReportPatch` 这类数据来自网络或存储时，要回到[TypeScript 能保证什么，外部数据又该怎样验证？](./typescript-guarantees-and-runtime-validation.md)的三步，在输入边界挑选并验证字段。装饰器怎样用这里的泛型参数保留被包装方法的签名，见[TypeScript 的两种装饰器模式有什么不同？](./typescript-decorators.md)。

> [!info]- 来源
> - **类型参数、推断与约束**（“取一个字段时，怎样保留它的类型”“怎样让分页和仓储接口复用于不同数据”）：TypeScript Handbook [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)；[Keyof Type Operator](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)；[Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)。
> - **工具类型与速查表**（“Pick、Partial、Record 改变了什么”“常用工具类型速查”）：[Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)；[Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)。
> - **省略、null、undefined**：[TSConfig `exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html)。
> - **分配式条件类型**：[Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)（Distributive Conditional Types 一节）。
> - **ThisType 与上下文类型**（“对象字面量方法里的 this 怎样获得类型”）：[Utility Types: ThisType](https://www.typescriptlang.org/docs/handbook/utility-types.html)、[Contextual Typing](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)。
>
> 来源核对日期：2026-11-12。原稿示例以 TypeScript 5.7.2 在 `strict`、`noUncheckedIndexedAccess` 下检查；本章改用 r-104 数据后以同一版本重新编译并运行，编译期错误用 `@ts-expect-error` 逐条确认，`exactOptionalPropertyTypes` 的开关差异单独验证。
