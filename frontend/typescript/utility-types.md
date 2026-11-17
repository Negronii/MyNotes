# 怎样从报表类型派生数据形状并约束方法中的 `this`？

本文继续使用报表页的行类型 `ReportRow`（下方代码会重新声明）。列表预览、局部更新这些数据形状，可以用 utility type（工具类型）从 `ReportRow` 派生，而不必再手写一遍；状态标签和 `ReportRow.status` 共用同一个 `ReportStatus` 联合，以免两处状态定义各改各的。本文后半部分处理另一个问题：对象字面量里的方法要知道 `this` 上有哪些字段，`ThisType<T>` 或显式的 `this` 参数可以在编译期提供这个信息。

这些手段都只作用于静态检查：它们不会在运行时筛选或验证数据，也不会替方法绑定 `this`。不可信的外部输入仍要在数据边界做运行时检查。

## 哪些工具类型适合哪些数据形状？

下面用 `Pick` 从 `ReportRow` 选出列表预览需要的字段，用 `Partial` 把允许编辑的字段变成可选；`Record` 则要求共享的 `ReportStatus` 中每个状态都有一个标签。

~~~typescript
type ReportStatus = "open" | "published" | "archived";

interface ReportRow {
  id: string;
  title: string;
  month: string;
  region: string;
  status: ReportStatus;
  total: number;
  ownerEmail: string;
}

type ReportPreview = Pick<ReportRow, "id" | "title" | "month" | "total">;
type ReportPatch = Partial<Pick<ReportRow, "title" | "region">>;
type StatusLabels = Record<ReportStatus, string>;

const labels: StatusLabels = {
  open: "待审核",
  published: "已发布",
  archived: "已归档"
};

const input = { region: "north", ownerEmail: "ada@example.com" };
const patch: ReportPatch = input;
console.log(Object.keys(patch)); // ["region", "ownerEmail"]：仍是同一个运行时对象
~~~

`Partial<Pick<ReportRow, "title" | "region">>` 由内向外展开为 `{ title?: string; region?: string }`。变量 `input` 与它有共同的键 `region`，所以可以赋值；多出的 `ownerEmail` 并不会被删掉，仍留在同一个运行时对象里，`Object.keys` 的输出证明了这一点。如果变量只有 `ownerEmail`，它与目标类型没有任何共同属性（目标类型的属性全部可选，TypeScript 称为 weak type），赋值会报错；直接把含 `ownerEmail` 的新对象字面量赋给 `ReportPatch`，也会被多余属性检查拦下。可见 `Pick` 只筛选类型上声明的字段；列表展示如果真的只想带这几个字段，仍要在运行时构造新对象。

`ReportStatus` 增加 `"scheduled"` 后，`labels` 会因缺少这个键而报错，提醒界面补上新状态的标签。

更新数据还要分清“省略”“`null`”和“`undefined`”。当前 `ReportPatch` 的字段是可选的 `string`；示例开启了 `strictNullChecks`，所以显式写入 `null` 无法通过检查。只有当接口约定 `null` 表示“清空该字段”之类的业务操作时，才应在对应属性类型里加上 `| null`，并让运行时边界按这层含义解析。至于 `undefined`：启用 `exactOptionalPropertyTypes`（它要求同时开启 `strictNullChecks`）后，可选字段可以省略，但除非类型里写了 `undefined`，否则不能显式赋值为 `undefined`；不启用时，编译器允许这样赋值。无论这个开关如何设置，读取 `patch.title` 都可能得到 `undefined`，因为属性本身可以不存在。

接收网络或存储中的更新数据时，运行时仍要按接口白名单检查字段，并区分省略、`null` 和具体值。这个检查针对不可信输入；本地按 `ReportPatch` 构造的对象仍由编译器检查。

其他常用工具类型可以按用途对照：

| 需要 | 工具类型 | 结果与边界 |
|---|---|---|
| 列表类型只声明所需字段 | `Pick<T, K>` / `Omit<T, K>` | 选取或排除键；不会复制或投影对象 |
| 表达部分更新或完成默认值后的完整配置 | `Partial<T>` / `Required<T>` | 属性变为可选或必需；运行时仍需合并、检查 |
| 标出只读视图 | `Readonly<T>` | 浅层地禁止通过该类型重新赋值属性；不冻结对象 |
| 给一组键创建映射 | `Record<K, V>` | 约束对象键和值的类型；动态输入仍须验证 |
| 从联合类型中筛选成员 | `Exclude<U, X>` / `Extract<U, X>` | 移除或保留可赋给指定类型的成员 |
| 排除 `null` 与 `undefined` | `NonNullable<T>` | 仅改变静态类型，不会替值做空值检查 |
| 读取函数签名 | `Parameters<F>` / `ReturnType<F>` | 得到参数元组或返回类型；对重载函数取最后一个签名 |
| 读取构造签名 | `ConstructorParameters<C>` / `InstanceType<C>` | 得到构造参数元组或实例类型 |
| 解开 Promise 返回类型 | `Awaited<T>` | 递归解包 Promise 及兼容其 `then` 约定的类型；不会等待运行时值 |

这些工具大多由 mapped type（映射类型）、conditional type（条件类型）和索引访问类型组合而成。嵌套使用时由内向外阅读，例如前面的 `Partial<Pick<...>>`：先由 `Pick` 取出两个可编辑字段，再由 `Partial` 把它们变为可选。表中 `Exclude`、`Extract` 这类筛选联合成员的工具，依赖条件类型的一条特殊规则，下一节单独说明。

## 条件类型遇到联合类型时，为什么会逐项筛选？

条件类型写作 `T extends X ? A : B`。如果 `extends` 左边直接是一个“裸”类型参数（没有包在数组、元组等结构里），那么传入联合类型时，编译器会把联合成员逐个代入条件，再把各自的结果合成联合。这叫 distributive conditional type（分配式条件类型）。`Exclude` 就利用了这条规则：可以赋给排除类型的成员变成 `never`，其余成员保留下来重新组成联合。

~~~typescript
type WithoutArchived<T> = T extends "archived" ? never : T;
type VisibleStatus = WithoutArchived<ReportStatus>;
// "open" | "published" | never -> "open" | "published"

const visibleStatus: VisibleStatus = "published";
// @ts-expect-error "archived" 已被筛掉
const archivedStatus: VisibleStatus = "archived";

type IsArchived<T> = T extends "archived" ? true : false;
type DistributedCheck = IsArchived<ReportStatus>; // true | false -> boolean
const distributedTrue: DistributedCheck = true;
const distributedFalse: DistributedCheck = false;

type IsWholeUnionArchived<T> = [T] extends ["archived"] ? true : false;
type WholeStatusCheck = IsWholeUnionArchived<ReportStatus>; // false
const wholeStatusCheck: WholeStatusCheck = false;
// @ts-expect-error 整个 ReportStatus 联合并非全是 "archived"
const wholeStatusTrue: WholeStatusCheck = true;
~~~

`WithoutArchived<ReportStatus>` 先得到 `"open" | "published" | never`；`never` 没有任何可取的值，在联合中会被吸收，所以结果只剩前两种状态。内置的 `Exclude<ReportStatus, "archived">` 得到同样的结果。后两个条件类型的分支完全相同，区别只在 `T` 是否“裸”：裸 `T` 会分配，三个成员分别得到 `false`、`false`、`true`，合起来是 `true | false`，即 `boolean`；把 `T` 包进元组 `[T]` 后不再分配，比较的是整个联合，结果为 `false`。

## 对象字面量方法里的 `this` 怎样获得上下文类型？

前面的工具类型都在派生数据形状。另一类问题出在方法上：对象字面量中的方法默认不知道 `this` 指向什么对象。`ThisType<T>` 是一个标记接口，作为对象字面量的上下文类型时，会让其中的方法把 `this` 当作 `T`。它不会添加属性、不会在运行时绑定 `this`，也不会改变对象本身；只有开启 `noImplicitThis`（`strict` 已包含）时它才生效。

~~~typescript
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
      this.loadedRows += 1; // 此处 this 有 loadedRows: number
    }
  }
});

rowCounter.addLoadedRow();
console.log(rowCounter.loadedRows); // 1
~~~

调用 `makeObject` 时，编译器从 `data` 推断 `Data = { loadedRows: number }`，从 `methods` 推断含 `addLoadedRow` 的 `Methods`；`ThisType<Data & Methods>` 再把两个对象的成员提供给方法体中的 `this`。返回表达式在运行时通过对象展开合并两个对象，再由 `rowCounter.addLoadedRow()` 的成员调用提供接收者，计数随后变为 1。这个小例只适用于数据和方法都是普通对象且所需成员是可枚举自有属性的情况；从原型继承的方法不会被对象展开复制。`Data & Methods` 本身不会禁止两个输入对象有重名键；重名时后展开的 `methods` 会覆盖 `data`，而交叉类型仍可能描述冲突字段。本例保持两边键名不重叠。

另一个做法是在普通函数签名中显式声明接收者：

~~~typescript
interface ReportViewer {
  name: string;
  describe(this: ReportViewer): string;
}

const viewer: ReportViewer = {
  name: "Ada",
  describe() { return `报表查看者：${this.name}`; }
};

console.log(viewer.describe()); // 报表查看者：Ada
~~~

`this: ReportViewer` 只是编译期对调用方式的要求；运行时调用 `viewer.describe()`，`this` 仍由普通的 JavaScript 方法调用提供。`ThisType<T>` 同样只影响方法体内的静态检查，不会替你调用 `bind`。两者的差别在方法被单独取出时显现：把 `viewer.describe` 赋给变量后直接调用，编译器会因为缺少所需的 `this` 而报错；把 `rowCounter.addLoadedRow` 取出后直接调用，却可能通过静态检查，而运行时 `this` 已经不对。

`ReportPatch` 这类更新数据若来自网络或存储，前面的工具类型都不会过滤它的运行时键，要在输入边界挑选并验证字段，做法见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。

> [!info]- 来源
> - [TypeScript Utility Types 参考](https://www.typescriptlang.org/docs/handbook/utility-types.html)
> - [TypeScript Handbook：映射类型](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)、[条件类型](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)、[上下文类型](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)
> - [TSConfig：`exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html)
>
> 来源核对日期：2026-11-12。示例以 TypeScript 5.7.2、`strict` 模式、`noImplicitThis` 及文中说明的精确可选属性设置检查。
