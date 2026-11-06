# ECMAScript 模块与 CommonJS（Node.js 模块格式）在语法、加载和运行时有什么不同？

报表页把类型、数据读取和界面入口分成不同文件后，`import` 和 `export` 只是这条路径的一部分。模块语法由 ECMAScript 定义；浏览器和 Node.js 作为宿主决定如何定位模块文件；bundler（打包器）还可在运行前合并或改写模块。把这几层分开，才能理解同一段源代码在不同项目里的加载差异。

~~~mermaid
flowchart LR
  A[页面入口与模块文件] --> B{脚本或模块格式}
  B -- 浏览器经典脚本 --> C[按 HTML 经典脚本规则执行；本身没有静态 ESM 导入]
  B -- Node.js CommonJS --> D[执行 CJS 包装器与 require 链]
  B -- ESM --> E{是否经过构建工具}
  E -- 否 --> F[浏览器或 Node.js 宿主解析 ESM 依赖]
  E -- 是 --> G[构建工具解析并改写依赖图]
  G --> I{生成的产物格式}
  I -- 浏览器经典脚本 --> C
  I -- Node.js CommonJS --> D
  I -- ESM --> F
  F --> H[加载、链接并执行运行时仍保留的模块]
~~~

## ESM 静态导入怎样描述报表模块之间的依赖？

ECMAScript Module（ECMAScript 模块，简称 ESM）使用静态 `import` 与 `export` 声明。静态依赖可在模块执行前从源码结构中识别；导入绑定与导出保持关联，不是复制一份当时的值。下面是浏览器中的 JavaScript 模块示例：它导出加载函数；响应体的数据形状仍须由调用方在运行时验证，TypeScript 类型声明不会自动变成 JavaScript 导出。

~~~javascript
// report-api.js（由 report-page.js 静态导入）
export async function loadReport(month) {
  // 根相对 URL 由浏览器按文档 base URL 解析。
  const response = await fetch(`/api/reports?month=${encodeURIComponent(month)}`);
  if (!response.ok) throw new Error(`报表请求失败：${response.status}`);
  return response.json();
}

// report-page.js
// index.html 通过 <script type="module" src="./report-page.js"></script> 加载此入口。
import { loadReport } from "./report-api.js";

const result = await loadReport("2026-10");
console.log(result);
~~~

这个片段依赖浏览器的文档 URL 环境；Node.js 的 `fetch` 不会把 `"/api/..."` 自动补成站点地址，直接运行时应传入绝对 URL 或提供明确的 URL base。

`loadReport` 是命名导出，导入时使用导出名或显式别名。模块也可提供一个默认导出，由调用方自行选择本地名称：

~~~javascript
// report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}

// report-page.js
import formatReportTotal from "./report-format.js";
~~~

一个模块至多有一个默认导出；它与按名字导入的 `loadReport` 可以并存。

顶层 `await` 让 ESM 等待异步初始化，属于 ES2022；当前模块和依赖其完成的模块需要等待；独立的依赖分支仍可继续求值。Promise continuation 与其他任务在事件循环中的顺序见[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)。若只需按需加载一段报表功能，可调用 `import()`；它返回 Promise，并可在 ESM、浏览器经典脚本与 Node CommonJS 中使用。动态导入使执行延后，但是否生成独立代码分块（chunk）由打包器配置决定。

### 目录入口怎样重新导出一个模块的公开接口？

聚合导出模块（barrel）只是一个使用 `export` 重新导出其他模块的 ESM 文件；它不会自动生成组件、改变加载宿主或保证减小包体。它可以把目录对外的名字集中到一个入口：

~~~javascript
// reports/index.js
export { ReportTable } from "./ReportTable.js";
export { ReportToolbar } from "./ReportToolbar.js";

// ReportsPage.js
import { ReportTable, ReportToolbar } from "./reports/index.js";
~~~

导出列表应有意挑选，避免无意公开内部模块。内部模块若又从同一聚合入口导入彼此，依赖图可能形成循环；同目录实现通常直接导入具体文件更清楚。`export *` 还可能让重名导出产生歧义。聚合入口仍会静态依赖这些模块；最终能删除哪些未使用代码，取决于打包器能否分析 ESM 依赖及副作用，见下文的 tree shaking（摇树优化）。

## CommonJS 与 ESM 的加载和文件识别有什么区别？

CommonJS（CJS）是 Node.js 提供的模块包装格式，常见写法是 `require()` 和 `module.exports`。它通过调用表达式加载模块；ESM 则用声明式语法建立模块依赖。

| 关注点 | ESM | Node.js CommonJS |
|---|---|---|
| 导入与导出 | 静态 `import`、`export`；也可使用 `import()` | `require()`、`module.exports`；也可使用 `import()` |
| 模块顶层 `this` | `undefined` | Node.js 包装函数中的 `exports` 值 |
| 顶层 `await` | 支持 | CJS 源文件中不支持；`require(ESM)` 仅支持没有顶层 `await` 的同步依赖图 |
| 默认严格模式 | 是 | 由代码上下文决定 |
| 依赖解析者 | 浏览器或服务器等宿主 | Node.js；也可由构建工具预处理 |

Node.js 通过 `.mjs`、`.cjs`、最近的 `package.json` 中的 `"type"` 等标记决定 `.js` 文件的模块格式。Node 26.13 还会对没有显式标记的歧义 `.js` 执行语法探测：若代码含 `import`、`export` 或顶层 `await` 等 ESM 专属语法，则按 ESM 处理；官方仍将这项探测标为 Release candidate，并提醒它会增加开销。项目仍应显式写出 `"type"`，并让 ESM 导入使用实际输出扩展名，以减少工具配置与运行时的歧义：

~~~json
{
  "type": "module"
}
~~~

浏览器的 `<script type="module">` 依照 URL 解析相对导入并受浏览器跨源规则约束；Node.js 则按包导出映射、文件扩展名和 Node 的解析算法查找模块。相同的 `import "./report-api.js"` 文本，不能脱离宿主规则单独推断文件从哪里来。当前 Node 也允许 CommonJS 用 `require()` 加载完全同步的 ESM；若该模块或其依赖图含顶层 `await`，则抛出 `ERR_REQUIRE_ASYNC_MODULE`，应改用 `import()`。

## 为什么 ESM 并不自动保证 tree shaking？

打包器能从静态 ESM 依赖分析哪些导出未被使用，但代码是否安全可删还要看副作用。若包把带有副作用的初始化或 CSS 导入误标成无副作用，删除未引用模块就可能改变页面行为。tree shaking（摇树优化）是打包器基于语法、配置和包元数据作出的优化，不是 ESM 语法承诺的运行结果。

开发服务器与生产构建的差异、构建器具体如何转译模块，见[构建工具怎样把源码变成可发布产物？](../tooling/build-tools.md)。Node.js 运行时对 ESM 与 CJS 的支持会随版本演进，部署前应检查正在使用的 Node 主版本。

> [!info]- 来源
> - [ECMAScript 2026 规范：脚本与模块](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html)
> - [Node.js 26.13：包格式与语法探测](https://nodejs.org/api/packages.html#determining-module-system)、[ESM 与顶层 `await`](https://nodejs.org/api/esm.html)、[`require(ESM)` 的同步依赖限制](https://nodejs.org/api/modules.html#loading-ecmascript-modules-using-require)
> - [Webpack：模块与 tree shaking 概念](https://webpack.js.org/concepts/)
>
> 来源核对日期：2026-11-06。Node.js 示例对应官方当前文档的 26.x 模块规则；Node 版本与包配置可能改变互操作边界。
