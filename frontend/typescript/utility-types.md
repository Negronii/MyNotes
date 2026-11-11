# 怎样从报表类型派生数据形状并约束方法中的 `this`？

列表预览和局部更新可以从 `ReportRow` 派生；状态标签使用与 `ReportRow.status` 共用的 `ReportStatus`，避免两处状态定义漂移。对象字面量中的方法也需要知道调用接收者有哪些字段：`ThisType<T>` 或显式的 `this` 参数能提供编译期上下文。工具类型只影响静态检查，不会投影或验证运行时数据，也不会替方法绑定接收者；不可信的外部输入应在数据边界执行运行时检查。

## 哪些工具类型适合哪些数据形状？

下面用 `Pick` 从 `ReportRow` 选出列表预览字段，用 `Partial` 把允许编辑的字段变为可选项；`Record` 则为共享的 `ReportStatus` 联合要求每个状态都有标签。

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

`Partial<Pick<ReportRow, "title" | "region">>` 从内向外展开为 `{ title?: string; region?: string }`。示例变量 `input` 含有共同键 `region`，所以它可赋给这个部分类型；多出的 `ownerEmail` 仍留在同一个运行时对象中。若变量只有 `ownerEmail`，则与目标类型没有共同属性而不能赋值；直接把含 `ownerEmail` 的新对象字面量赋给 `ReportPatch` 也会触发多余属性检查。`Pick` 只筛选静态声明的字段，列表展示若需要实际投影，仍须在运行时构造新对象。

`ReportStatus` 增加 `"scheduled"` 后，`labels` 会因缺少该键而报错，提醒界面补上新状态。当前 `ReportPatch` 的字段是可选 `string`；在示例所用的 `strictNullChecks` 下，显式写入 `null` 不通过检查。只有当接口把 `null` 定义为清空字段等业务操作时，才应在对应属性类型中加入 `| null`，并让运行时边界按该语义解析。启用 `exactOptionalPropertyTypes`（要求 `strictNullChecks`）时，可选字段可以省略，但不能显式写 `undefined`，除非其类型包含 `undefined`；未启用时，编译器允许把 `undefined` 赋给可选字段。无论开关如何，读取 `patch.title` 都可能得到 `undefined`，因为属性可以缺席。

接收网络或存储中的更新数据时，运行时仍要按接口白名单检查字段，并区分省略、`null` 和具体值。这个检查针对不可信输入；本地按 `ReportPatch` 构造的对象仍由编译器检查。

常用变换可按目的理解：

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

这些工具大多通过 mapped type（映射类型）、conditional type（条件类型）或索引访问组合实现。阅读 `Partial<Pick<ReportRow, "title" | "region">>` 时，先用 `Pick` 取两个允许编辑的字段，再用 `Partial` 将它们变为可选；前文已展开其具体对象形状。

## 条件类型遇到联合类型时，为什么会逐项筛选？

条件类型（conditional type）若在被检查的位置直接写类型参数，例如 `T extends X`，传入联合类型时会把联合成员逐个代入条件。`Exclude` 就利用这个规则：成员可赋给排除类型时变成 `never`，剩余成员再组成联合。

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

`WithoutArchived<ReportStatus>` 会得到 `"open" | "published" | never`，而 `never` 没有可取值，所以结果只剩前两种状态。两个布尔条件使用相同的分支：裸 `T` 分配后得到 `true | false`（也就是 `boolean`）；把 `T` 包在元组中则比较整个联合，结果为 `false`。同样，`Exclude<ReportStatus, "archived">` 与 `VisibleStatus` 一样得到剩余状态。

## 对象字面量方法里的 `this` 怎样获得上下文类型？

`ThisType<T>` 是一个 contextual typing marker（上下文类型标记），可让对象字面量中的方法把 `this` 看作 `T`。它不会添加属性、绑定运行时接收者或改变对象；检查依赖 `noImplicitThis`。

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

`this: ReportViewer` 只是编译期接收者注解；调用 `viewer.describe()` 时仍由普通 JavaScript 成员调用提供 `this`。`ThisType<T>` 也只影响方法体中的静态检查，不会替你调用 `bind`。单独取出 `viewer.describe` 后直接调用，会因缺少显式接收者而报类型错误；单独取出 `rowCounter.addLoadedRow` 后直接调用可能通过静态检查，但运行时仍需要正确的接收者。如果 `ReportPatch` 来自网络或存储，需在该输入边界挑选并验证字段；类型工具不会过滤其运行时键。解析入口见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。

> [!info]- 来源
> - [TypeScript Utility Types 参考](https://www.typescriptlang.org/docs/handbook/utility-types.html)
> - [TypeScript Handbook：映射类型](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)、[条件类型](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)、[上下文类型](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)
> - [TSConfig：`exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html)
>
> 来源核对日期：2026-11-12。示例以 TypeScript 5.7.2、`strict` 模式、`noImplicitThis` 及文中说明的精确可选属性设置检查。
