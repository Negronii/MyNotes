# How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？

**Core answer / 核心回答：** Treat API bodies and browser storage as untrusted runtime data. Parse into unknown, validate both syntax and shape with JavaScript checks, then construct a trusted typed value. A type annotation, utility type, or assertion changes what the checker believes; it does not inspect incoming data. / API 响应和浏览器存储都是不可信的运行时数据。先解析为 unknown，再用 JavaScript 检查语法和结构，最后构造可信的类型化值。类型注解、工具类型或断言只改变检查器的判断，不会检查输入数据。

Type annotations are erased from emitted JavaScript. TypeScript’s type system also makes deliberate soundness tradeoffs, and any or an unchecked assertion can bypass useful checks. / 类型注解会从生成的 JavaScript 中擦除。TypeScript 类型系统也有意作出某些健全性取舍；any 或未校验的断言会绕过有效检查。

~~~mermaid
flowchart LR
  A["External text"] --> B{"JSON.parse"}
  B -- "syntax error" --> E["Parse error result"]
  B -- "valid syntax: unknown" --> C{"Runtime shape and value checks"}
  C -- "invalid shape" --> E
  C -- "valid Profile" --> D["Construct typed value"]
~~~

## Validate a value at runtime / 在运行时校验值

JSON.parse can throw for malformed JSON and, on success, still says nothing about the object’s shape. Keep the parsed result as unknown so every property access follows a runtime guard. This example handles syntax and shape failures without an unchecked cast; the storage adapter also makes a missing key explicit. / JSON.parse 遇到格式错误的 JSON 会抛错；成功解析也不能说明对象结构正确。将结果保留为 unknown，使每次属性读取都必须经过运行时保护。此示例不使用未经检查的类型断言来处理语法和结构错误；存储适配器也显式处理缺失键。

~~~typescript
type Profile = {
  id: string;
  label: string;
  role: "admin" | "reader";
};

type ParseResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseProfile(text: string): ParseResult<Profile> {
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return { ok: false, error: "Invalid JSON syntax" };
  }

  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.label !== "string" ||
    (value.role !== "admin" && value.role !== "reader")
  ) {
    return { ok: false, error: "Expected id, label, and a known role" };
  }

  return {
    ok: true,
    value: { id: value.id, label: value.label, role: value.role }
  };
}

function readStoredProfile(storage: Storage): ParseResult<Profile> {
  const text = storage.getItem("profile");
  if (text === null) return { ok: false, error: "No saved profile" };
  return parseProfile(text);
}

const valid = parseProfile('{"id":"u-7","label":"Ada","role":"reader"}');
const malformed = parseProfile('{"id":7,"label":"Ada","role":"reader"}');
// valid.ok is true; malformed.ok is false with a structural error.
~~~

After validation, ordinary control-flow narrowing applies to the declared model. The caller still needs to inspect ParseResult.ok before using value; a type-safe representation does not choose the application’s error policy. If the server adds a new role, this parser deliberately rejects it until the application accepts it; update the validator and exhaustive consumers together. For exhaustive handling of every role or result variant, see [Checking Every Union Case / 联合类型穷尽检查](./exhaustive-discriminated-unions.md). / 校验后可对声明模型执行普通控制流缩窄。调用方仍需先检查 ParseResult.ok 才能使用 value；类型安全的表示不会替应用选择错误处理策略。若服务端增加角色，解析器会先拒绝它，直到应用明确接受；应同步更新验证器和穷尽处理分支。需要确保处理每个角色或结果分支时，见[联合类型穷尽检查](./exhaustive-discriminated-unions.md)。

Utility types and generics describe compile-time relationships, not runtime guards: [Utility Types / 工具类型](./utility-types.md), [Generics / 泛型](./generics.md). Decorator modes answer a separate class-definition question: [TypeScript Decorators / TypeScript 装饰器](./decorators.md). JavaScript Proxy is a runtime object feature, not a TypeScript type feature; see [JavaScript Proxy / JavaScript Proxy](../javascript/proxy.md).

**Sources checked 2026-10-15:** [TypeScript Basic Types and unknown](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types and assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions), and [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness).
