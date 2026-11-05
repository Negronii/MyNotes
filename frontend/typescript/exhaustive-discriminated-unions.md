# How can TypeScript check every case in a discriminated union? / TypeScript 如何检查判别联合的每个分支？

**Core answer / 核心回答：** Narrow a discriminated union by its tag, then assign the final branch to never. If a new member is added but not handled, the remaining value is no longer never and the assignment becomes a type error. / 先按判别字段缩小联合类型，再把最后剩余分支赋给 never。若新增成员却没有相应处理，剩余值就不再是 never，赋值会产生类型错误。

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

The never assignment checks exhaustiveness at this switch. It does not force every caller or every other switch to include the same cases, and it does not validate incoming JSON. Runtime checks establish whether an external value actually matches the declared union. See [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](./advanced-typescript.md).

See the [TypeScript handbook on exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking).
