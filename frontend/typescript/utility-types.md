# 怎样从报表行派生预览、更新请求和状态标签？

同一条报表数据会用于接口、列表预览、详情编辑和状态标签映射。如果每个位置重新声明字段，修改字段名时容易漏改一处。TypeScript 的 utility type（工具类型）从现有类型派生新的编译期形状；它们不会验证或转换运行时对象。

## 哪些工具类型适合哪些数据形状？

下面把一份 `ReportRow` 派生成列表需要的预览、允许编辑的局部更新和状态标签映射。`Pick` 选取字段，`Partial` 把选中的字段变成可选项，`Record` 要求每个状态都对应一个标签。

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

若 `ReportStatus` 增加 `"scheduled"`，`labels` 会因缺少该键而报错；这让新增状态需要同步更新界面映射。`ReportPatch` 只收窄 `patch` 这个变量可通过静态类型访问的字段，不会从对象中删除 `ownerEmail`。这里先把对象存入变量再赋值，因此结构类型允许多出的字段；直接把带额外键的新对象字面量写给 `ReportPatch` 通常会触发多余属性检查。接收更新请求时应在运行时挑选并验证白名单字段，再处理未提供、提供 `null` 和提供具体值之间的业务差异。

常用变换可按目的理解：

| 需要 | 工具类型 | 结果与边界 |
|---|---|---|
| 列表只露出部分字段 | `Pick<T, K>` / `Omit<T, K>` | 选取或排除键；不会复制对象 |
| 表达部分更新或完成默认值后的完整配置 | `Partial<T>` / `Required<T>` | 属性变为可选或必需；运行时仍需合并、检查 |
| 标出只读视图 | `Readonly<T>` | 浅层地禁止通过该类型重新赋值属性；不冻结对象 |
| 给一组键创建映射 | `Record<K, V>` | 约束对象键和值的类型；动态输入仍须验证 |
| 从联合类型中筛选成员 | `Exclude<U, X>` / `Extract<U, X>` | 移除或保留可赋给指定类型的成员 |
| 排除 `null` 与 `undefined` | `NonNullable<T>` | 仅改变静态类型，不会替值做空值检查 |
| 读取函数签名 | `Parameters<F>` / `ReturnType<F>` | 得到参数元组或返回类型 |
| 读取构造签名 | `ConstructorParameters<C>` / `InstanceType<C>` | 得到构造参数元组或实例类型 |
| 解开 Promise 返回类型 | `Awaited<T>` | 递归得到等待后的类型；不会等待运行时值 |

这些工具大多通过mapped type（映射类型）、conditional type（条件类型）或索引访问组合实现。阅读 `Partial<Pick<ReportRow, "title" | "region">>` 时，可以从内到外读：先取两个允许编辑的字段，再把它们变为可选。

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
      this.loadedRows += 1;
    }
  }
});

rowCounter.addLoadedRow(); // this.loadedRows 在编译期被识别为 number
~~~

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
~~~

`this: ReportViewer` 只是编译期注解，JavaScript 调用时仍按普通 `this` 绑定规则运行；`ThisType<T>` 也不会替你调用 `bind`。两者与上面的 `ReportPatch` 一样，只有在运行时对象经过边界检查后才有可靠的业务含义。解析入口见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。

> [!info]- 来源
> - [TypeScript Utility Types 参考](https://www.typescriptlang.org/docs/handbook/utility-types.html)
> - [TypeScript Handbook：映射类型](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)、[条件类型](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)、[上下文类型](https://www.typescriptlang.org/docs/handbook/type-inference.html#contextual-typing)
>
> 来源核对日期：2026-11-06。示例以 TypeScript 5.7.2、`strict` 模式和 `noImplicitThis` 检查。
