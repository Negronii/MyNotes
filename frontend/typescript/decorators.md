# 项目使用哪种 TypeScript 装饰器模式？

报表服务可能要给方法加日志、缓存或指标统计。decorator（装饰器）在类或类成员定义时调用，可以替换被装饰的定义；本文聚焦方法装饰器。TypeScript 5.0 起可使用新版（提案）模式；`experimentalDecorators` 选择旧版（legacy）模式。两者的调用参数、可修饰位置和元数据配置不同，不能把一种模式的装饰器直接贴到另一种项目里。

| 模式与配置边界 |
|---|
| 新模式（TypeScript 5.0 起）：有效配置未启用 `experimentalDecorators`；新版**方法**装饰器收到原方法函数和上下文对象，可返回替代方法。不能装饰参数，也不能使用 `emitDecoratorMetadata`。字段装饰器的第一个参数是 `undefined`，调用约定并非所有成员相同。 |
| 旧模式（legacy）：有效配置设置 `experimentalDecorators: true`；方法装饰器收到 `target`、属性键和描述符。可使用参数装饰器；若框架要读取 TypeScript 生成的设计类型元数据，再按其要求启用 `emitDecoratorMetadata` 并加载 `reflect-metadata`。 |

TypeScript 5.0 的无标志模式采用 TC39 新装饰器提案的调用约定，常被称为“标准装饰器”以区别旧版实现；截至 2026-11-12，TC39 当前提案列表仍标为 Stage 2.7，尚未完成标准化。因此这里的“新版/标准”说明 TypeScript 的模式边界，不表示提案已成为正式 ECMAScript 标准。

## 新版方法装饰器怎样保留原方法的签名？

TypeScript 5.0 引入了不依赖 `experimentalDecorators` 的新版装饰器实现。执行类定义时，`@loggedMethod` 收到当前的 `loadMonth` 函数和方法上下文；它返回的包装函数会被安装为 `ReportService.prototype.loadMonth`。创建 `ReportService` 实例时不会因此记录日志；稍后调用 `service.loadMonth(...)` 才进入包装函数，日志后它用同一个 `this` 和参数调用原方法，再把原方法的返回值交还调用方。下面的 generic（泛型）保留这项转发的接收者、参数元组和返回值类型。

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
void service.loadMonth("2026-10")
  .then(rows => console.log(rows));
// 先记录“报表方法调用： loadMonth”。
// Promise 完成后输出 ["2026-10 报表已加载"]。
~~~

源代码中的 `@` 不一定会原样出现在输出 JavaScript：编译器或构建器可能把它转换为运行时辅助代码；若构建流水线保留装饰器语法，目标运行时就必须支持相应语法和语义。应检查实际构建产物，而不能只凭 TypeScript 源文件判断。

## 旧版方法装饰器为什么不能沿用同一签名？

开启 `experimentalDecorators` 后，旧版方法装饰器接收原型或构造函数、属性键和属性描述符。下面装饰的是实例方法，所以 `target` 是类原型；`descriptor.value` 是 `loadMonth` 当前的方法函数槽位。装饰器把包装函数写回该槽位，TypeScript 的旧版装饰器运行时代码随后将更新后的描述符应用回原方法。许多既有框架依赖此约定，也可能使用参数装饰器或 `emitDecoratorMetadata`。

~~~typescript
function legacyLog(
  target: object,
  key: string | symbol,
  descriptor: PropertyDescriptor
) {
  const original = descriptor.value;
  descriptor.value = function (
    this: unknown, ...args: unknown[]
  ) {
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

要判断现有文件采用哪种模式，应查看**实际编译该文件的项目配置**。使用 `tsc` 时，可运行 `tsc -p path/to/tsconfig.json --showConfig` 查看合并 `extends` 后的有效值；TypeScript 5.0 起，有效的 `experimentalDecorators: true` 表示旧版，否则是新版。多配置仓库要选实际参与构建的配置；若另一个构建器还会转换装饰器，则再检查它的配置和最终 JavaScript 产物。

这两个例子都只是在方法调用周围加日志；它们不会验证网络响应，也不会证明调用者有查看报表的权限。需要在不可信数据入口检查实际值时，使用[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。选择新版或旧版装饰器后，继续核对[ECMAScript 模块与 CommonJS 的加载边界](../javascript/modules-and-host-boundaries.md)。

> [!info]- 来源
> - [TypeScript 5.0 发布说明：新版装饰器及其与旧版的差异](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators)
> - [TypeScript TSConfig：`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/experimentalDecorators.html)、[`emitDecoratorMetadata`](https://www.typescriptlang.org/tsconfig/emitDecoratorMetadata.html)
> - [TC39 装饰器提案](https://github.com/tc39/proposal-decorators)、[TC39 当前提案阶段列表](https://github.com/tc39/proposals)
>
> 提案阶段按 2026-11-12 的当前列表核对。示例以 TypeScript 5.7.2 分别按无 `experimentalDecorators` 的新版模式和 `experimentalDecorators: true` 的旧版模式严格编译；`target: ES2022` 的产物已在 Node v26.13.0 运行，`target: ESNext` 是否保留 `@` 也已检查。
