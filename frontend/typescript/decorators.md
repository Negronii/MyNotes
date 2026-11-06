# 项目使用哪种 TypeScript 装饰器模式？

报表服务可能要给方法加日志、缓存或指标统计。decorator（装饰器）会在类定义时接收类元素和上下文，并可包装或替换被修饰的成员。TypeScript 有新版装饰器模式和 `experimentalDecorators` 启用的旧版模式；两者的参数约定、可修饰位置和元数据能力不同，不能把一种模式的装饰器直接贴到另一种项目里。

## 新版方法装饰器怎样保留原方法的签名？

TypeScript 5.0 引入了不依赖 `experimentalDecorators` 的新版装饰器实现。下面的包装器使用 generic（泛型）保留接收者、参数元组和返回值类型；它可以为同步或异步方法加日志，而不把 `this` 和参数丢成 `any`。

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
    console.log("报表方法调用：", name);
    return original.call(this, ...args);
  };
}

class ReportService {
  @loggedMethod
  async loadMonth(month: string): Promise<string[]> {
    return [`${month} 报表已加载`];
  }
}

const service = new ReportService();
void service.loadMonth("2026-10").then(rows => console.log(rows));
// 先记录“报表方法调用： loadMonth”；Promise 完成后输出 ["2026-10 报表已加载"]。
~~~

新版方法装饰器会收到原方法和 `ClassMethodDecoratorContext`（类方法上下文），可以返回兼容的替代方法。它不能装饰参数，也不能使用旧版 `emitDecoratorMetadata`。新版模式对应 TC39 装饰器提案的调用约定；截至 2026-11-06，TC39 提案列表仍将装饰器标作 Stage 2.7。TypeScript 文档称其实现为标准装饰器支持，但项目能否直接在目标运行时执行仍取决于该运行时是否解析 `@` 语法，构建器也可能负责转换。

## 旧版方法装饰器为什么不能沿用同一签名？

开启 `experimentalDecorators` 后，旧版方法装饰器接收原型或构造函数、属性键和属性描述符。许多既有框架依赖此约定，也可能使用参数装饰器或 `emitDecoratorMetadata`；选择模式时应以框架文档和 `tsconfig.json` 为准。

~~~typescript
function legacyLog(
  target: object,
  key: string | symbol,
  descriptor: PropertyDescriptor
) {
  const original = descriptor.value;
  descriptor.value = function (this: unknown, ...args: unknown[]) {
    console.log("旧版报表方法调用：", key);
    return original.apply(this, args);
  };
}

class LegacyReportService {
  @legacyLog
  loadMonth(month: string): string {
    return `${month} 报表已加载`;
  }
}

const legacyService = new LegacyReportService();
console.log(legacyService.loadMonth("2026-10"));
// 依次记录“旧版报表方法调用： loadMonth”和“2026-10 报表已加载”。
~~~

这两个例子都只是在方法调用周围加日志；它们不会验证网络响应，也不会证明调用者有查看报表的权限。需要在不可信数据入口检查实际值时，使用[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。选择新版或旧版装饰器后，继续核对[ECMAScript 模块与 CommonJS 的加载边界](../javascript/modules-and-host-boundaries.md)。

> [!info]- 来源
> - [TypeScript 5.0 发布说明：新版装饰器及其与旧版的差异](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators)
> - [TypeScript TSConfig：`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/experimentalDecorators.html)
> - [TC39 装饰器提案](https://github.com/tc39/proposal-decorators)、[TC39 当前提案阶段列表](https://github.com/tc39/proposals)
>
> 提案阶段按 2026-11-06 列表核对；示例以 TypeScript 5.7.2 分别按新版和 `experimentalDecorators` 模式作严格编译检查。
