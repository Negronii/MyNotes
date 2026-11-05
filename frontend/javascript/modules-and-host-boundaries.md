# How do ECMAScript modules and CommonJS differ? / ECMAScript 模块与 CommonJS 有何区别？

**Core answer / 核心回答：** ECMAScript modules (ESM) are standardized JavaScript syntax with static imports and exports, module-scoped bindings, strict mode, and top-level this equal to undefined. CommonJS (CJS) is Node’s module wrapper using require and module.exports. Module syntax, host loading rules, bundler analysis, and runtime scheduling are separate concerns. / ECMAScript 模块（ESM）是标准 JavaScript 语法，使用静态导入与导出，绑定属于模块作用域，自动采用严格模式，顶层 this 为 undefined。CommonJS（CJS）是 Node 使用 require 和 module.exports 的模块包装机制。模块语法、宿主加载规则、打包器分析和运行时调度是不同问题。

## ESM syntax and dynamic import / ESM 语法与动态导入

Static import and export declarations are part of ECMAScript. Top-level await was standardized in ES2022. Dynamic import() returns a Promise and Node supports it from either module system. / 静态 import 与 export 声明属于 ECMAScript。顶层 await 于 ES2022 标准化。动态 import() 返回 Promise，Node 两种模块系统都支持它。

~~~javascript
// features.mjs
export const featureName = "search";
export default function createFeature() {
  return featureName;
}
~~~

~~~javascript
// app.mjs
import createFeature, { featureName } from "./features.mjs";
export { featureName };

createFeature(); // "search"
import("./features.mjs").then(({ featureName }) => featureName);
~~~

## What differs between ESM and CJS / ESM 与 CJS 有何不同

| Concern / 维度 | ECMAScript module / ES 模块 | Node CommonJS / Node CommonJS |
|---|---|---|
| Static syntax / 静态语法 | import, export | require(), module.exports |
| Top-level await / 顶层 await | Supported / 支持 | Not supported in a CJS wrapper / CJS 包装器中不支持 |
| Top-level this / 顶层 this | undefined | Node wrapper’s exports value / Node 包装器的 exports 值 |
| Strict mode / 严格模式 | Automatic / 自动采用 | Depends on code context / 取决于代码上下文 |

Node determines whether a file is ESM or CJS using extensions, package settings, or explicit input options; browser module loading follows browser rules. CommonJS is not ECMAScript module syntax. / Node 根据扩展名、包配置或显式输入选项判断文件属于 ESM 还是 CJS；浏览器模块加载遵循浏览器规则。CommonJS 不是 ECMAScript 模块语法。

See the [ECMAScript module specification](https://tc39.es/ecma262/2025/multipage/ecmascript-language-scripts-and-modules.html) and [Node.js ESM documentation](https://nodejs.org/api/esm.html). This page describes module semantics and loading boundaries, not Node event-loop ordering; see [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md) for scheduling.

## Why ESM syntax does not guarantee tree shaking / 为什么 ESM 语法不保证 tree shaking

A bundler can analyze ESM imports for tree shaking, but using ESM syntax alone does not guarantee code removal. The result depends on the bundler and package metadata. See [Build Tools / 构建工具](../tooling/build-tools.md) for the transform and production-output boundary. / 打包器可分析 ESM 导入并执行 tree shaking，但仅使用 ESM 语法并不保证代码会被移除；结果还取决于打包器和包元数据。变换与生产产物边界见 [Build Tools / 构建工具](../tooling/build-tools.md).
