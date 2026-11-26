# TypeScript 的两种装饰器模式有什么不同？

报表服务常常要给多个方法加上日志、缓存或指标统计。decorator（装饰器）让这类横切逻辑只写一次，用 `@名称` 贴到类或类成员上：它在**类定义时**被调用，可以用返回值替换被装饰的定义。TypeScript 里同时存在两种装饰器模式，调用参数、可装饰的位置和元数据配置都不同，为一种模式写的装饰器不能直接拿到另一种模式的项目里用。本章只讨论方法装饰器，依次给出两种模式的写法，最后说明怎样判断一个项目用的是哪种。

本章是[TypeScript 能保证什么，外部数据又该怎样验证？](./typescript-guarantees-and-runtime-validation.md)的支线。例子沿用主线一的报表页：一个 `ReportService` 的 `loadRows` 方法读取报表 42 的行。新版写法用到泛型参数保留签名，相关基础见[泛型和工具类型怎样从已有类型推出新类型？](./typescript-generics-and-utility-types.md)。

## 两种模式由什么区分？

| 模式 | 何时生效 | 方法装饰器收到什么 | 能力边界 |
| --- | --- | --- | --- |
| 新版（TypeScript 5.0 起的默认） | 有效配置**没有**启用 `experimentalDecorators` | 原方法函数和一个上下文对象；可以返回替代方法 | 不能装饰参数，不能用 `emitDecoratorMetadata`；各类成员的调用约定不同，例如字段装饰器的第一个参数是 `undefined` |
| 旧版（legacy） | 有效配置设置 `experimentalDecorators: true` | 原型（静态方法则是构造函数）、属性键和属性描述符 | 可以用参数装饰器；框架要读 TypeScript 生成的设计期类型元数据时，按框架要求启用 `emitDecoratorMetadata` 并加载 `reflect-metadata` |

新版模式按 TC39 装饰器提案的调用约定实现，常被称为“标准装饰器”。但截至 2026-11-17，TC39 提案列表仍把装饰器列在 Stage 2.7，尚未进入正式标准。本章说的“新版”只用来区分 TypeScript 的两种模式，不表示装饰器已经是 ECMAScript 的正式特性。

## 新版方法装饰器怎样保留原方法的签名？

下面在新版模式下给 `loadRows` 加调用日志：

```typescript
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
  async loadRows(reportId: string): Promise<string[]> {
    return [`报表 ${reportId}：r-104`];
  }
}

const service = new ReportService();
void service.loadRows("42").then(rows => console.log(rows));
// 先输出“报表方法调用： loadRows”
// Promise 完成后输出 ["报表 42：r-104"]
```

按时间顺序看发生了什么：

1. **执行 `class ReportService` 定义时**，`@loggedMethod` 被调用，收到当前的 `loadRows` 函数和方法上下文。它返回的包装函数被安装为 `ReportService.prototype.loadRows`。
2. **`new ReportService()` 时**什么都不打印，装饰器已经在第 1 步跑完了。
3. **调用 `service.loadRows("42")` 时**进入包装函数：先记日志，再用同一个 `this` 和参数调用原方法，把原方法的返回值（这里是 Promise）原样交回。

包装函数必须和原方法签名一致，否则调用方拿到的类型就变了。所以装饰器用三个泛型参数分别记住接收者类型 `This`、参数元组 `Args` 和返回类型 `Return`，包装函数用同样的三个参数声明自己。

## 旧版方法装饰器为什么不能沿用同一签名？

开启 `experimentalDecorators` 后，同样的日志需求要换一种写法。旧版方法装饰器收到的不是原方法和上下文，而是 `target`、属性键和属性描述符：

```typescript
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
  loadRows(reportId: string): string {
    return `报表 ${reportId}：r-104`;
  }
}

console.log(new LegacyReportService().loadRows("42"));
// 依次输出“旧版报表方法调用： loadRows”和“报表 42：r-104”
```

这里装饰的是实例方法，所以 `target` 是类原型；`descriptor.value` 存放 `loadRows` 当前的函数。装饰器把包装函数写回 `descriptor.value`，TypeScript 生成的旧版辅助代码随后用更新过的描述符重新定义这个方法。

两种签名的参数个数和含义完全不同：把 `loggedMethod` 放进旧版项目，它会把原型当成原方法；反过来，`legacyLog` 在新版项目里收不到描述符。许多已有框架依赖旧版约定，还可能用到参数装饰器或 `emitDecoratorMetadata`，迁移前要先确认框架支持哪种模式。

## 怎样判断项目用的是哪种模式？

看**实际编译这个文件的项目配置**，而不是随手打开的某个 `tsconfig.json`：

- 用 `tsc` 时，运行 `tsc -p path/to/tsconfig.json --showConfig`，查看合并 `extends` 之后的有效值。TypeScript 5.0 起，有效配置里 `experimentalDecorators: true` 表示旧版，否则是新版。
- 多配置仓库要选实际参与构建的那份配置。
- 如果另一个构建器（而不是 `tsc`）负责转换装饰器，还要检查它的配置。

最终要以构建产物为准。源码里的 `@` 不一定原样出现在输出的 JavaScript 里：编译器可能把它改写成运行时辅助代码，也可能保留语法。保留时，目标运行时必须支持装饰器语法及其语义。

> [!example] 实测：TypeScript 5.7.2 的输出与 Node.js v26.13.1
> 用 TypeScript 5.7.2 按新版模式编译上面的 `ReportService`：
> - `target: ES2022` 的输出没有 `@`，改写成 `__esDecorate` 等辅助代码，在 Node.js v26.13.1 上按正文顺序输出。
> - `target: ESNext` 的输出原样保留 `@loggedMethod`，Node.js v26.13.1 加载时报 `SyntaxError: Invalid or unexpected token`。
>
> 同一份源码能否运行，取决于输出目标和运行时，而不是源码本身。

> [!info] 版本说明
> 示例以 TypeScript 5.7.2 分别在无 `experimentalDecorators` 的新版模式和 `experimentalDecorators: true` 的旧版模式下严格编译。截至 2026-11-17，npm 上 TypeScript 的最新版本是 7.0.2（Go 原生实现的编译器）；本章示例未在 7.x 上运行，升级时应重新核对装饰器配置和输出产物。

## 装饰器之外还要核对什么

本章区分了两种装饰器模式：新版收到原方法和上下文、返回替代方法；旧版收到原型、键和描述符、修改描述符。判断依据是有效配置里的 `experimentalDecorators`，最终证据是构建产物。

两个装饰器都只是在方法调用前后加日志，既不验证网络响应，也不证明调用者有权查看报表；外部数据的检查回到[TypeScript 能保证什么，外部数据又该怎样验证？](./typescript-guarantees-and-runtime-validation.md)。决定装饰器怎样输出的那份构建配置，通常也决定输出的模块格式，它对运行时加载的影响见[import 写下后，谁负责找到、链接和执行文件？](./modules-and-host-boundaries.md)。

> [!info]- 来源
> - **两种模式的差异、默认与配置**（“两种模式由什么区分”“新版方法装饰器”“旧版方法装饰器”）：[TypeScript 5.0 发布说明：Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators)（新版装饰器、与 `experimentalDecorators` 的差异、不支持参数装饰器与 `emitDecoratorMetadata`）；TSConfig [`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/experimentalDecorators.html)、[`emitDecoratorMetadata`](https://www.typescriptlang.org/tsconfig/emitDecoratorMetadata.html)。
> - **提案阶段**（“两种模式由什么区分”）：[TC39 装饰器提案](https://github.com/tc39/proposal-decorators)、[TC39 提案阶段列表](https://github.com/tc39/proposals)，按 2026-11-17 核对为 Stage 2.7。
> - **编译与运行核对**（“怎样判断项目用的是哪种模式”的实测 callout）：原稿以 TypeScript 5.7.2 严格编译两种模式，`target: ES2022` 产物在 Node v26.13.0 运行；本章改用 `loadRows` 示例后以 TypeScript 5.7.2、Node v26.13.1 重新运行，并实测 `target: ESNext` 保留 `@` 且在该 Node 版本上报语法错误。TypeScript 最新版本 7.0.2 按 2026-11-17 的 npm 记录。
