# 怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？

报表页可能在本地 Chrome 正常，却在部署后的旧 WebView 上因语法解析或缺少 API 失败。判断一项特性时，要分清它进入哪一版 ECMAScript、目标运行时是否实现，以及构建器实际转换了什么。TypeScript 的类型声明和构建选项也不能代替运行时能力检测。

## ECMAScript 版本能告诉我们什么？

ECMAScript 年份表示语言规范的版本；它本身不表示每个浏览器或 Node.js 发行版都已经实现所有特性。下面列出报表代码可能用到的一些边界。`structuredClone` 是由浏览器、Node.js 等宿主提供的 API（应用程序接口），不属于 ECMAScript 年份表。

| 特性 | 语言版本 | 使用边界 |
|---|---|---|
| `Object.keys` | ES5 | 返回自有且可枚举的字符串键，不含 Symbol 键 |
| `Object.assign`、`Object.is` | ES2015 | 前者会修改目标对象；后者使用 SameValue 比较规则 |
| `Array.from`、`Array.of` | ES2015 | 分别从可迭代或类数组输入创建数组，以及从参数列表创建数组 |
| `Object.values`、`Object.entries` | ES2017 | 只枚举自有、可枚举的字符串键 |
| `Promise.all`、`Promise.race` | ES2015 | 完成条件与取消边界见[异步 JavaScript](./asynchronous-javascript.md) |
| `Promise.allSettled` | ES2020 | 等所有输入结束后分别给出完成或拒绝结果 |
| `globalThis` | ES2020 | 当前 realm（执行域）的全局 `this` 值；浏览器网页的 Window 环境中为 `WindowProxy`，Node.js 中为 Node 全局对象 |
| `Promise.any` | ES2021 | 最先兑现的输入使聚合 Promise 成功；全部拒绝才以 `AggregateError` 拒绝 |
| `Array.prototype.at`、`Object.hasOwn` | ES2022 | 前者接受负索引；后者检查自有属性，不调用可覆盖的 `hasOwnProperty` |
| `Object.groupBy`、`Map.groupBy`、`Promise.withResolvers` | ES2024 | 分别按回调结果分组对象键或 Map 键、以及创建 Promise 与其控制函数 |
| `Set` 的集合方法、`RegExp.escape` | ES2025 | 集合并交差等操作；后者转义插入正则表达式的字面文本 |
| `structuredClone` | 浏览器与 Node.js 宿主 API | 可复制支持结构化克隆的值和循环引用；不能复制函数，也不保留自定义类原型 |

版本表适合初步定位；具体支持仍要核对目标浏览器版本、Node.js 主版本和嵌入式 WebView。单个运行时还可能只实现同一版规范中的部分功能。

## 语法转换、类型声明和 polyfill 有什么差别？

语法转换器可以把目标环境无法解析的语法改写成旧语法，但一般不会自动补上运行时缺失的内置 API。polyfill（兼容补丁）则在运行时提供缺少的方法或对象。TypeScript 的 `target` 决定 `tsc` 会把多少 JavaScript 语法降级；`lib` 选择类型检查时可见的标准库声明。把 `"DOM"` 或 `"ES2022"` 加入 `lib` 只让编译器认识这些名字，不会在运行时创建 `Object.hasOwn`。

~~~json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noEmit": true
  }
}
~~~

在报表页面中，`Object.hasOwn` 和 `Array.prototype.at` 即使通过类型检查，也应由部署目标提供或由项目显式加入 polyfill：

~~~javascript
const options = Object.create(null);
options.enabled = false;

Object.hasOwn(options, "enabled"); // true
["2026-09", "2026-10"].at(-1);   // "2026-10"
~~~

## Vite 的开发与生产目标分别由什么控制？

Vite 8.3 的开发转换默认以现代浏览器和 `esnext` 为目标；生产 bundle（打包产物）默认面向 2026-01-01 的 Baseline Widely Available（广泛可用基线）浏览器范围：Chrome/Edge 111、Firefox 114、Safari/iOS 16.4 及以上。可以用 `build.target` 调整生产语法目标。Vite 8 用 Oxc 转换 TypeScript，但只做转译，不执行完整类型检查；项目应另跑 `tsc --noEmit`。

Vite 的 `build.target` 与 `tsconfig.json` 的 `target` 名字相似，却分别控制生产 bundle（打包产物）的浏览器语法降级与 TypeScript 编译器的输出行为。Vite 默认只转换语法，并不补齐所有缺失 API；降低目标语法也不能让 `Object.hasOwn` 自动出现。需要旧浏览器兼容时，应分别确定语法目标和 API 补丁方案，再在代表性运行时检查构建产物。

截至 2026-11-06，TypeScript 7.1 beta（测试版）文档已将 `es2026` 列为稳定的 `target` 与 `lib` 选项。可用名称由项目实际安装的 TypeScript 版本决定；上面的配置刻意使用稳定较久的 `ES2022`。

`structuredClone` 的克隆范围由宿主定义。它可以处理循环引用、`Map`、`Set` 和 `Date` 等结构化可克隆值，但不能复制函数或保留自定义类的原型；不支持的值会抛出 `DataCloneError`。不要假设它必然比其他拷贝方法更快。

> [!info]- 来源
> - [ECMAScript 2026 规范](https://tc39.es/ecma262/2026/)
> - [TypeScript TSConfig：`target`](https://www.typescriptlang.org/tsconfig/#target)、[`lib`](https://www.typescriptlang.org/tsconfig/#lib)
> - [TypeScript 7.1 beta：ES2026 `target` 与 `lib`](https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/)
> - [Vite 8.3：TypeScript 转译与目标配置](https://vite.dev/guide/features.html#typescript)、[生产构建浏览器兼容](https://vite.dev/guide/build.html#browser-compatibility)
> - [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)、[Node.js 26.13：`structuredClone`](https://nodejs.org/api/globals.html#structuredclonevalue-options)
>
> Vite 浏览器版本与默认值按 Vite 8.3 文档核对；运行时更新后重新检查项目目标。来源核对日期：2026-11-06。

相关模块加载和构建链路见[ECMAScript 模块与 CommonJS 的加载边界](./modules-and-host-boundaries.md)和[构建工具怎样把源码变成可发布产物？](../tooling/build-tools.md)。
