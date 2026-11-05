# How does the function Decorator pattern add behavior? / 函数装饰器模式如何附加行为？

A Decorator wraps an object or function to add a cross-cutting behavior while leaving the wrapped implementation intact. The design pattern is broader than decorator syntax, whose calling convention and capabilities depend on language and toolchain versions. / 装饰器模式通过包装对象或函数增加横切行为，同时保留被包装实现。该设计模式比装饰器语法更广；语法的调用约定和能力取决于语言及工具链版本。

This timing wrapper preserves the receiver and arguments, returns the wrapped result, and logs elapsed time even when the operation throws:

~~~javascript
function withTiming(fn) {
  return function (...args) {
    const start = performance.now();
    try {
      return fn.apply(this, args);
    } finally {
      console.log((fn.name || 'operation') + ': ' + (performance.now() - start) + ' ms');
    }
  };
}

const saveWithTiming = withTiming(function save(value) {
  return value.id;
});
~~~

Use a wrapper when the added behavior is a real shared concern; extra layers for one trivial call can make flow harder to follow. TypeScript standard decorators and legacy experimental decorators have different signatures; see [Advanced TypeScript](../../../frontend/typescript/advanced-typescript.md) for that version boundary.

**Sources / 来源:** [TC39 Decorators proposal](https://github.com/tc39/proposal-decorators) and [TypeScript 5.0 decorator notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators), checked 2026-10-15.
