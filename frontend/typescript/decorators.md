# Which TypeScript decorator mode does a project use? / 项目使用哪种 TypeScript 装饰器模式？

**Core answer / 核心回答：** TypeScript supports standard ECMAScript decorators and a separate legacy mode. Their signatures and capabilities differ. Use the mode required by the framework and compiler configuration; do not copy a decorator from a different project without checking its mode. / TypeScript 支持标准 ECMAScript 装饰器和独立的旧版模式。两者的签名与能力不同。应使用框架和编译配置要求的模式，不要未确认模式就复制其他项目的装饰器。

## Standard decorators in TypeScript 5.0 and later / TypeScript 5.0 及之后的标准装饰器

A standard method decorator receives the original method and a context object; it may return a replacement method. / 标准方法装饰器接收原始方法和上下文对象，也可以返回替代方法。

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

Standard decorators do not support parameter decorators and are not compatible with emitDecoratorMetadata. / 标准装饰器不支持参数装饰器，也不兼容 emitDecoratorMetadata。

## Legacy decorator mode / 旧版装饰器模式

Existing Angular, NestJS, and ORM projects may use legacy decorator mode enabled by experimentalDecorators. A legacy method decorator receives a target, property key, and property descriptor, unlike the standard signature. Legacy emitDecoratorMetadata also belongs to this mode. / 既有 Angular、NestJS 和 ORM 项目可能使用 experimentalDecorators 启用的旧版模式。旧版方法装饰器接收 target、属性键和属性描述符，与标准签名不同；旧版 emitDecoratorMetadata 也属于该模式。

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

Decorator metadata is not general runtime validation. For an external JSON value, validate the value itself with runtime logic or a validation library. For the separate unknown-JSON runtime boundary, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](./advanced-typescript.md). See the [TypeScript 5.0 decorator release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators). Sources checked 2026-10-15.
