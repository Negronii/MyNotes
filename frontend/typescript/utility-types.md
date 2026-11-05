# What do TypeScript utility types guarantee? / TypeScript 工具类型能保证什么？

**Core answer / 核心回答：** Utility types derive one compile-time type from another, helping related shapes stay connected instead of repeating property declarations. They do not change or validate runtime values. Readonly is shallow and does not freeze an object; Partial does not validate a request. / 工具类型从已有类型推导出新编译期类型，避免重复声明并让相关结构保持关联。它们不会改变或验证运行时值。Readonly 是浅层的，也不会冻结对象；Partial 不会校验请求。

| Utility type / 工具类型 | Type-level result / 类型结果 |
|---|---|
| Partial<T> | Makes each property optional / 所有属性可选 |
| Required<T> | Makes each property required / 所有属性必需 |
| Readonly<T> | Makes each property readonly at compile time; shallow / 编译期只读；浅层 |
| Pick<T, K> / Omit<T, K> | Selects or removes keys / 选择或移除属性 |
| Record<K, V> | Describes keys and values of an object shape / 描述对象键和值 |
| Exclude<U, X> / Extract<U, X> | Removes from or selects members of a union / 从联合中排除或选取成员 |
| NonNullable<T> | Removes null and undefined / 移除 null 和 undefined |
| ReturnType<F> / Parameters<F> | Extracts a function return type or parameter tuple / 提取返回类型或参数元组 |
| InstanceType<C> / ConstructorParameters<C> | Extracts a class instance type or constructor parameter tuple / 提取类实例类型或构造参数元组 |
| ThisType<T> | Contextual `this` type marker for object-literal methods; it does not change runtime values / 对象字面量方法的上下文 `this` 类型标记；不改变运行时值 |

~~~typescript
interface User {
  id: number;
  name: string;
  email: string;
}

type UserPreview = Pick<User, "id" | "name">;
type UserPatch = Partial<Pick<User, "name" | "email">>;

type Role = "admin" | "editor" | "reader";
const permissions: Record<Role, string[]> = {
  admin: ["read", "write"],
  editor: ["read", "write"],
  reader: ["read"]
};
~~~

UserPatch expresses an allowed shape to the checker; runtime code still needs to validate parsed JSON. For that boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](./advanced-typescript.md). See the [TypeScript Utility Types reference](https://www.typescriptlang.org/docs/handbook/utility-types.html).

## How does ThisType contextually type this? / ThisType 如何提供 this 的上下文类型？

`ThisType<T>` is a contextual-typing marker for `this` inside object-literal methods. It does not add a property or bind a runtime receiver, and the check depends on `noImplicitThis`. An explicit `this: Person` parameter is a separate compile-time receiver annotation. / `ThisType<T>` 是对象字面量方法中 `this` 的上下文类型标记。它不会添加属性或绑定运行时接收者，相关检查依赖 `noImplicitThis`。显式的 `this: Person` 参数则是另一种编译期接收者注解。

~~~typescript
type ObjectDescriptor<Data, Methods> = {
  data: Data;
  methods: Methods & ThisType<Data & Methods>;
};

function makeObject<Data, Methods>(descriptor: ObjectDescriptor<Data, Methods>): Data & Methods {
  return { ...descriptor.data, ...descriptor.methods };
}

const counter = makeObject({
  data: { value: 0 },
  methods: { increment() { this.value += 1; } }
});
counter.increment(); // this.value is contextually typed as number
~~~

~~~typescript
interface Person {
  name: string;
  greet(this: Person): void;
}

const person: Person = {
  name: "Ada",
  greet() { console.log(this.name); }
};
~~~
