# How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？

**Short answer / 简答** — Treat API bodies and browser storage as untrusted runtime data. Parse into `unknown`, check syntax and shape, then construct a value whose fields match the application's type. The checker can enforce exhaustive use of that type. The parser does not establish whether a supplied role or identity claim is authorized. / 把 API 响应和浏览器存储视为不可信数据。先解析为 `unknown`，校验语法和结构，再构造与应用类型匹配的值。编译器可以检查是否处理所有受支持的类型分支。结构校验无法证明输入里的角色或身份已经获得授权。

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

## Handle every validated variant / 处理每个已校验的分支

Callers first inspect `ParseResult.ok`. After the parser succeeds, the UI can narrow on the validated role. Assign the unhandled default value to `never` so an added role becomes a compile error at this switch.

~~~typescript
function roleLabel(role: Profile["role"]): string {
  switch (role) {
    case "admin":
      return "Administrator";
    case "reader":
      return "Reader";
    default: {
      const unhandled: never = role;
      throw new Error(`Unhandled role: ${unhandled}`);
    }
  }
}

if (valid.ok) roleLabel(valid.value.role); // "Reader"
~~~

If the server introduces `editor`, the parser still rejects it until the client deliberately supports it. When you add `editor` to `Profile["role"]`, the missing switch case fails the `never` assignment. Update the runtime guard and the consumers together. These checks serve different points in the same data path. The runtime parser protects the input boundary, while the compiler checks the supported cases at this switch. / 输入校验挡住外部未知值，`never` 让受支持的类型新增分支时在该 switch 报错。 [TypeScript handbook on exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)

Utility types and generics describe compile-time relationships, not runtime guards: [Utility Types / 工具类型](./utility-types.md), [Generics / 泛型](./generics.md). Decorator modes answer a separate class-definition question: [TypeScript Decorators / TypeScript 装饰器](./decorators.md). JavaScript Proxy is a runtime object feature, not a TypeScript type feature; see [JavaScript Proxy / JavaScript Proxy](../javascript/proxy.md).

**Sources checked 2026-10-15:** [TypeScript Basic Types and unknown](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [Everyday Types and assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions), and [Type Compatibility and Soundness](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness).
