# 项目使用哪种 TypeScript 装饰器模式？

报表服务常常要给多个方法加上日志、缓存或指标统计。decorator（装饰器）让这类横切逻辑写一次、用 `@名称` 贴到类或类成员上：它在类定义时被调用，可以用返回值替换被装饰的定义。本文只讨论方法装饰器。TypeScript 里同时存在两种装饰器模式：TypeScript 5.0 起默认使用的新版模式，按 TC39 提案实现；以及开启 `experimentalDecorators` 后使用的旧版（legacy）模式。两者的调用参数、可装饰的位置和元数据配置都不同，为一种模式写的装饰器不能直接拿到另一种模式的项目里用。

| 模式 | 配置与能力边界 |
|---|---|
| 新版（TypeScript 5.0 起） | 有效配置没有启用 `experimentalDecorators`。**方法**装饰器收到原方法函数和一个上下文对象，可以返回替代方法。不能装饰参数，也不能使用 `emitDecoratorMetadata`。不同成员的调用约定并不相同，例如字段装饰器收到的第一个参数是 `undefined`。 |
| 旧版（legacy） | 有效配置设置了 `experimentalDecorators: true`。方法装饰器收到 `target`、属性键和属性描述符。可以使用参数装饰器；如果框架要读取 TypeScript 生成的设计期类型元数据，再按框架要求启用 `emitDecoratorMetadata` 并加载 `reflect-metadata`。 |

新版模式采用 TC39 装饰器提案的调用约定，常被称为“标准装饰器”，以区别于旧版实现。但截至 2026-11-17，TC39 的提案列表仍把装饰器列在 Stage 2.7，尚未进入正式标准。所以本文说的“新版”只用来区分 TypeScript 的两种模式，并不表示装饰器已经是正式的 ECMAScript 特性。

## 新版方法装饰器怎样保留原方法的签名？

下面的例子在新版模式下给 `loadMonth` 加调用日志。执行 `class ReportService` 定义时，`@loggedMethod` 收到当前的 `loadMonth` 函数和方法上下文，返回的包装函数会被安装为 `ReportService.prototype.loadMonth`。创建实例时不会打印日志；之后调用 `service.loadMonth(...)` 才进入包装函数：它先记录日志，再用同一个 `this` 和参数调用原方法，并把原方法的返回值交回调用方。包装函数与原方法的签名要保持一致，所以装饰器用三个 generic（泛型）参数分别记住接收者类型 `This`、参数元组 `Args` 和返回值类型 `Return`。

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

源代码中的 `@` 不一定原样出现在输出的 JavaScript 里：编译器或构建器可能把它转换成运行时辅助代码。反过来，如果构建流水线保留了装饰器语法，目标运行时就必须支持这种语法及其语义。因此要以实际构建产物为准，不能只看 TypeScript 源文件。

## 旧版方法装饰器为什么不能沿用同一签名？

开启 `experimentalDecorators` 后，同样的日志需求要换一种写法：旧版方法装饰器收到的是原型（静态方法则是构造函数）、属性键和属性描述符，而不是原方法和上下文对象。下面装饰的是实例方法，所以 `target` 是类原型；`descriptor.value` 存放 `loadMonth` 当前的函数。装饰器把包装函数写回 `descriptor.value`，TypeScript 生成的旧版装饰器辅助代码随后用更新后的描述符重新定义该方法。许多已有框架依赖这套约定，还可能用到参数装饰器或 `emitDecoratorMetadata`。

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

这两个例子都只是在方法调用前后加日志，既不会验证网络响应，也不能证明调用者有权查看报表。需要在不可信数据的入口检查实际值时，见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](./advanced-typescript.md)。另外，决定装饰器如何输出的那份构建配置，通常也决定了输出的模块格式；它对运行时加载的影响见[ECMAScript 模块与 CommonJS 的加载边界](../javascript/modules-and-host-boundaries.md)。

> [!info]- 来源
> - [TypeScript 5.0 发布说明：新版装饰器及其与旧版的差异](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators)
> - [TypeScript TSConfig：`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/experimentalDecorators.html)、[`emitDecoratorMetadata`](https://www.typescriptlang.org/tsconfig/emitDecoratorMetadata.html)
> - [TC39 装饰器提案](https://github.com/tc39/proposal-decorators)、[TC39 当前提案阶段列表](https://github.com/tc39/proposals)
>
> 提案阶段按 2026-11-17 的 TC39 提案列表核对。示例以 TypeScript 5.7.2 分别按无 `experimentalDecorators` 的新版模式和 `experimentalDecorators: true` 的旧版模式严格编译；`target: ES2022` 的产物已在 Node v26.13.0 运行，`target: ESNext` 是否保留 `@` 也已检查。截至 2026-11-17，npm 上 TypeScript 的最新版本是 7.0.2（Go 原生实现的编译器）；本文示例未在 7.x 上重新运行，升级时应重新核对装饰器配置和输出产物。
