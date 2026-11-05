# How do TypeScript generics preserve relationships between types? / TypeScript 泛型如何保留类型之间的关系？

**Core answer / 核心回答：** A generic type parameter preserves a relationship between inputs and outputs. TypeScript can infer a parameter from a call, while an extends constraint limits the values it accepts. Use generics when the same logic should preserve specific types across multiple callers. / 泛型参数用于保留输入与输出之间的关系。TypeScript 可从调用中推断类型参数；extends 约束限制可接受的值。当同一逻辑需要为不同调用者保留各自具体类型时，使用泛型。

~~~typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30 };
const userName = getProperty(user, "name"); // string
// getProperty(user, "phone"); // Type error: no such key
~~~

Here K must be a key of T. The indexed access type T[K] connects the chosen key to its corresponding property type; the function does not widen every result to a union of all possible property types. / 这里 K 必须是 T 的键。索引访问类型 T[K] 把所选键与对应属性类型关联起来；函数不会把每个结果都扩大成所有属性类型的联合。

A generic interface preserves the same relationship across a group of operations: / 泛型接口可让一组操作共享同一种类型关系：

~~~typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}
~~~

A type parameter is not a runtime check. It describes a contract enforced by the checker where type information is available. External values still need runtime validation; see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](./advanced-typescript.md). See the [TypeScript Generics handbook](https://www.typescriptlang.org/docs/handbook/2/generics.html).
