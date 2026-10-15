# Advanced TypeScript / TypeScript进阶

TypeScript checks relationships between values while editing and compiling JavaScript. Type declarations are erased from emitted JavaScript, so a successful typecheck does not validate untrusted runtime values. The type system also makes deliberate soundness tradeoffs; values typed with any or an unchecked assertion can bypass useful checks.

## What are utility types? / 什么是工具类型？

**Core answer / 核心回答：** Utility types transform an existing type so related shapes stay connected instead of copying property declarations. They are compile-time descriptions: Readonly does not freeze an object, and Partial does not validate an incoming request. / 工具类型可以转换已有类型，让相关数据结构保持关联，避免重复声明字段。它们只描述编译期类型：Readonly 不会冻结对象，Partial 也不会验证传入的请求。

| Utility | Result |
|---|---|
| Partial<T> | Makes each property optional. |
| Required<T> | Makes each property required. |
| Readonly<T> | Makes each property readonly at compile time; it is shallow. |
| Pick<T, K> / Omit<T, K> | Selects or removes a set of keys. |
| Record<K, V> | Describes an object whose keys and values follow the supplied types. |
| Exclude<U, X> / Extract<U, X> | Removes from or selects members of a union. |
| NonNullable<T> | Removes null and undefined from a type. |
| ReturnType<F> / Parameters<F> | Extracts a function's return type or parameter tuple. |
| InstanceType<C> / ConstructorParameters<C> | Extracts a class instance type or constructor parameter tuple. |

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

A type such as UserPatch is useful for expressing an allowed shape, but runtime code still needs to check that a parsed JSON value contains valid fields and values.

## How do generics work? / 泛型如何工作？

**Core answer / 核心回答：** A generic preserves a relationship between input and output types. TypeScript can infer a type parameter from a call, and an extends constraint limits which values are accepted. / 泛型用于保留输入和输出类型之间的关系。TypeScript 可以根据调用推断类型参数；extends 约束用于限制可接受的类型。

~~~typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30 };
const userName = getProperty(user, "name"); // string
// getProperty(user, "phone"); // Type error: no such key
~~~

A generic interface can keep that relationship across a group of operations:

~~~typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}
~~~

Use generics when the same logic should preserve specific types across multiple callers. A type parameter is not a runtime check; it describes the contract enforced by the checker where type information is available.

## What is Proxy? / Proxy是什么？

**Core answer / 核心回答：** JavaScript Proxy wraps an object and lets a handler intercept operations such as property reads, writes, deletion, or membership checks. It is a runtime JavaScript feature, not a TypeScript type feature. Reflect methods forward operations while preserving their normal semantics. / JavaScript Proxy 包装一个对象，并让 handler 拦截属性读取、写入、删除和成员检查等操作。它是 JavaScript 的运行时功能，不是 TypeScript 类型功能。Reflect 方法可按正常语义转发这些操作。

~~~javascript
const handler = {
  get(target, property, receiver) {
    console.log("read", property);
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("write", property);
    return Reflect.set(target, property, value, receiver);
  }
};

const data = new Proxy({ count: 0 }, handler);
data.count;
data.count = 1;
~~~

Common uses include reactive state, validation, and instrumentation. A proxy only observes operations that pass through it; references to the original target can bypass its traps. Unlike defining a getter for each known property, a proxy can intercept later-added properties, but compatibility and object behavior still matter. Vue 2 used property getters and setters for reactivity; Vue 3 uses proxies for reactive objects.

## What are decorators? / 什么是装饰器？

**Core answer / 核心回答：** Decorators run at class-definition time and can wrap or register class elements. TypeScript supports standard ECMAScript decorators and a separate legacy mode. Their signatures and capabilities differ; use the mode required by the framework rather than copying a decorator from another configuration. / 装饰器在类定义时运行，可包装或注册类成员。TypeScript 支持标准 ECMAScript 装饰器和另一套旧版模式。两种模式的签名和能力不同；应使用框架要求的模式，不要直接复制其他配置中的装饰器。

### Standard decorators in TypeScript 5.0+ / TypeScript 5.0+标准装饰器

Standard decorators receive the original method and a context object. A method decorator may return a replacement method.

~~~typescript
function loggedMethod<This, Args extends unknown[], Return>(
  original: (this: This, ...args: Args) => Return,
  context: ClassMethodDecoratorContext<
    This,
    (this: This, ...args: Args) => Return
  >
) {
  const name = String(context.name);

  return function (this: This, ...args: Args): Return {
    console.log("calling", name);
    return original.call(this, ...args);
  };
}

class Calculator {
  @loggedMethod
  add(a: number, b: number) {
    return a + b;
  }
}
~~~

Standard decorators do not support parameter decorators and are not compatible with emitDecoratorMetadata.

### Legacy decorators / 旧版装饰器

Existing Angular, NestJS, and ORM projects may use the legacy decorator mode enabled by experimentalDecorators. A legacy method decorator receives a target, property key, and property descriptor. That signature is different from the standard form; the legacy emitDecoratorMetadata option also belongs to this mode.

~~~typescript
function legacyLog(
  target: object,
  key: string | symbol,
  descriptor: PropertyDescriptor
) {
  const original = descriptor.value;
  descriptor.value = function (...args: unknown[]) {
    console.log("calling", key);
    return original.apply(this, args);
  };
}
~~~

Do not use decorator metadata as general runtime validation. For an external JSON value, parse and validate the actual value with runtime logic or a validation library.

## How do you check every member of a union? / 如何确保联合类型分支完整？

**Core answer / 核心回答：** Narrow a discriminated union by its tag, then assign the final branch to never. If a new union member is added without a branch, the assignment becomes a type error. / 通过判别字段缩小联合类型；最后将剩余分支赋给 never。如果新增联合成员却没有增加对应分支，该赋值就会产生类型错误。

~~~typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; side: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "square":
      return shape.side ** 2;
    default: {
      const exhaustive: never = shape;
      return exhaustive;
    }
  }
}
~~~

**See also:** [JavaScript Memory, WeakMap and WeakSet / JavaScript内存、WeakMap与WeakSet](../javascript/javascript-memory-weakmap-and-weakset.md) for object identity and proxies; [React Basics / React基础](../frameworks/react-basics.md) for component API examples.

**Sources checked 2026-10-15:** [TypeScript: Basic Types](https://www.typescriptlang.org/docs/handbook/2/basic-types), [TypeScript: Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html), [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html), [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness), [Narrowing and Exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking), [TypeScript 5.0 Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators), [Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth).
