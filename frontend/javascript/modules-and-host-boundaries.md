# ECMAScript 模块与 CommonJS（Node.js 模块格式）在语法、加载和运行时有什么不同？

**案例背景。** 本章以一个合成的月报页面为例。把数据读取、数字格式化和页面入口拆到不同文件后，写下 `import` 并不意味着浏览器或 Node.js 已经知道去哪里找文件。这里要分清三层：ECMAScript module（ECMAScript 模块，ESM）的语法只声明依赖和导出；宿主（浏览器或 Node.js）按各自的规则定位、加载并执行文件；bundler（打包器）还可以在构建时改写整个依赖图。下面先沿报表页面从入口走到数据响应，再切换到 Node.js 的模块格式，追踪每一层接收什么、交出什么。

| 这一层 | 它决定什么 | 报表例子 |
| --- | --- | --- |
| ECMAScript 模块语法 | 哪些名字被导入、导出；依赖属于静态声明还是运行时请求 | `import { loadReport } from ...` |
| 宿主（浏览器或 Node.js） | 文件格式、模块说明符解析、读取/下载、执行环境 | 浏览器 URL 与 import map；Node.js 文件扩展名与包配置 |
| bundler（打包器） | 构建时怎样解析、转换、拆分并优化产物 | 可能保留 ESM、改成 CommonJS，或输出浏览器脚本 |

## ESM 静态导入怎样描述报表模块之间的依赖？

ESM 由 ECMAScript 2015（ES2015）引入。static import（静态导入）与 `export` 声明依赖和公开的名称，但不规定浏览器要发哪个 HTTP 请求，也不规定 Node.js 读哪个文件路径。静态依赖不必运行代码，从语法结构就能识别，所以宿主可以先建立 module graph（模块图），再把各个导入名连接到对应的导出。

下面的浏览器示例由一个 HTML 文件和四个模块文件组成。运行前提和流程如下：

- **服务器**：模块不能从 `file:` 路径直接加载，需要本地 HTTP 服务器以 `examples/browser/` 为根目录，并以 `text/javascript` 类型返回 JavaScript 文件（浏览器要求模块脚本使用 JavaScript MIME 类型）。服务器还要让 `/api/reports?month=2026-10` 返回含数值 `total: 1200` 的 JSON。
- **模块加载**：页面加载入口 `reports/report-page.js`。入口用相对说明符 `./report-api.js` 导入读取函数，用 `@reports/report-format.js` 导入格式化函数；后者由 import map（导入映射表）把 `@reports/` 映射到同源的 `reports/` 目录。
- **结果**：入口用 top-level await（顶层 await，ES2022）等待读取结果，页面从“读取中”更新为 `1,200`。另有一段经典脚本独立地按需加载 `lazy-tip.js` 并打印提示。

**文件：** `examples/browser/index.html`

~~~html file=examples/browser/index.html
<!doctype html>
<meta charset="utf-8">
<title>报表</title>
<p>本月总额：<output id="total">读取中</output></p>
<script type="importmap">
{
  "imports": {
    "@reports/": "./reports/"
  }
}
</script>
<script type="module" src="./reports/report-page.js"></script>
<script>
  // 经典脚本不能写静态 import，但可以按需调用 import()。
  import("./lazy-tip.js").then(({ message }) => console.log(message()));
</script>
~~~

**文件：** `examples/browser/reports/report-page.js`

~~~javascript file=examples/browser/reports/report-page.js
import { loadReport } from "./report-api.js";
import formatTotal from "@reports/report-format.js";

const result = await loadReport("2026-10");
if (!result || !Number.isFinite(result.total)) {
  throw new TypeError("报表响应必须包含数值 total");
}
document.querySelector("#total").textContent = formatTotal(result.total);
~~~

**文件：** `examples/browser/reports/report-api.js`

~~~javascript file=examples/browser/reports/report-api.js
export async function loadReport(month) {
  // 当前页面没有跨源 <base>，所以此地址仍指向本地站点。
  const requestUrl = `/api/reports?month=${encodeURIComponent(month)}`;
  const response = await fetch(requestUrl);
  if (!response.ok) throw new Error(`报表请求失败：${response.status}`);
  return response.json();
}
~~~

**文件：** `examples/browser/reports/report-format.js`

~~~javascript file=examples/browser/reports/report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}
~~~

**文件：** `examples/browser/lazy-tip.js`

~~~javascript file=examples/browser/lazy-tip.js
export function message() {
  return "按需模块已加载";
}
~~~

| 模块步骤 | 输入与操作 | 输出 |
| --- | --- | --- |
| 定位入口 | HTML 解析到模块脚本后，按文档 base URL（基准 URL）定位并取回 `report-page.js` | 入口模块源代码 |
| 解析与取回依赖 | 读取入口的静态 `import`；相对说明符按导入者 URL 解析，`@reports/` 用 import map 解析；再递归处理各依赖的静态导入。浏览器会并行取回已发现的模块，但不会一次知道整个图 | `report-api.js`、`report-format.js` 等依赖模块源代码；跨源模块还须通过 Cross-Origin Resource Sharing（跨源资源共享，CORS） |
| 链接 | 将各模块的导入名连到目标模块的导出绑定，并检查名字是否存在 | 绑定已连接；名字不匹配时模块代码不会开始求值 |
| 求值 | 按模块图执行依赖，再执行入口；本例入口的顶层 await 等待 API 响应 | 数据检查通过后，入口把格式化结果写入 `output` |

链接不等于变量已经有值：若导出方的 `let` / `const` 绑定尚未初始化，提前读取仍会抛出 `ReferenceError`。本例没有循环依赖，先完成依赖求值才执行入口；循环中的提前读取与[作用域中的暂时性死区](./scope-and-closure.md)遵循同一初始化边界。

入口中的 `loadReport` 是 named export（命名导出），名称要与导入列表对应；`formatTotal` 是 default export（默认导出），导入方可自选本地名字。单个模块最多有一个默认导出，也可以同时有多个命名导出；导入方可用 `as` 为命名导入另取本地名字。API 响应经 `response.json()` 得到的是运行时数据；JavaScript 不会因为变量名或 TypeScript 类型声明就替服务端验证结构，TypeScript 类型也不会凭空成为 JavaScript 运行时导出，所以入口显式检查 `total` 是数值后才格式化。

`@reports/report-format.js` 不以 `/`、`./` 或 `../` 开头，也不是完整 URL，属于 bare module specifier（裸模块说明符）。浏览器不会像 Node.js 那样去 npm 包目录里找它；没有 `type="importmap"` 提供的映射，导入就会失败。三种地址各有自己的解析基准：

- 相对导入 `./report-api.js` 相对**导入它的模块**的 URL 解析。
- HTML 中入口脚本的 `src` 相对**文档的 base URL** 解析。
- `fetch("/api/...")` 是应用发出的数据请求，不是模块加载，按当前窗口的 API base URL 解析，通常就是文档 base URL。若文档含有跨源的 `<base href>`，根相对路径会指向那个源，而不是页面所在的源，请求也要受 CORS 限制。本例没有 `<base>`，所以请求发往提供页面的本地站点。

Node.js 的 `fetch()` 没有文档基准，直接传 `"/api/..."` 会因缺少绝对 URL 而失败。

导入建立的是到导出变量的 live binding（实时绑定），而不是在导入时复制一个值。导入方能读到导出方之后写入的新值，但不能直接给导入名赋值。下面两个文件演示同一绑定在更新前后的值：`before` 是普通变量，保存第一次读到的字符串；更新后再读 `selectedMonth`，得到的是新字符串，输出 `["2026-10","2026-11"]`。

**文件：** `examples/esm-binding/month-state.js`

~~~javascript file=examples/esm-binding/month-state.js
export let selectedMonth = "2026-10";

export function selectNextMonth() {
  selectedMonth = "2026-11";
}
~~~

**文件：** `examples/esm-binding/read-month.js`

~~~javascript file=examples/esm-binding/read-month.js
import { selectedMonth, selectNextMonth } from "./month-state.js";

const before = selectedMonth;
selectNextMonth();
console.log(JSON.stringify([before, selectedMonth]));
// selectedMonth = "2026-12"; // 导入绑定不能由此模块写入
~~~

默认导出只是 ESM 公开接口的一种写法，不代表模块只能导出一个值。一个模块可以有一个默认导出，同时提供其他命名导出：

**文件：** `examples/esm-binding/report-format.js`

~~~javascript file=examples/esm-binding/report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}

export function formatMonth(month) {
  return month.replace("-", "年") + "月";
}
~~~

**文件：** `examples/esm-binding/use-format.js`

~~~javascript file=examples/esm-binding/use-format.js
import formatTotal, {
  formatMonth as monthLabel,
} from "./report-format.js";

console.log(JSON.stringify([monthLabel("2026-10"), formatTotal(1200)]));
// ["2026年10月","1,200"]
~~~

静态 `import` 声明只能写在模块顶层，不能放进条件分支。要等用户需要时才加载某项功能，可用 dynamic import（动态导入）`import()`：它在执行到调用处时异步加载模块，返回一个 Promise，成功后兑现为模块命名空间对象。已加载过的模块会被复用，所以并非每次调用都重新取回文件。浏览器经典脚本、Node.js 的 CommonJS 文件和 ESM 都可以调用 `import()`；它是否被 bundler 拆成独立的 chunk（代码块），取决于构建配置。

**文件：** `examples/esm-binding/load-optional.js`

~~~javascript file=examples/esm-binding/load-optional.js
export async function loadOptionalReport(shouldOpen) {
  if (!shouldOpen) return null;
  const { renderChart } = await import("./optional-chart.js");
  return renderChart();
}
~~~

**文件：** `examples/esm-binding/optional-chart.js`

~~~javascript file=examples/esm-binding/optional-chart.js
export function renderChart() {
  return "图表已加载";
}
~~~

回到浏览器示例中的顶层 `await`（ES2022 起可用）：`report-page.js` 在顶层等待数据。在本文这种无环的依赖图里，导入它的模块要等它求值完成，才开始执行自己的模块体；与它无关的其他依赖分支则可以继续求值。Promise continuation 与其他任务在事件循环中的顺序见[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)。

### 目录入口怎样重新导出一个模块的公开接口？

barrel（聚合导出模块）是只用 `export ... from` 转发其他模块接口的 ESM 文件。它把报表目录要公开的名称集中到一个入口；它只转发名称，不会改变模块的加载方式，也不保证最终产物变小：

**文件：** `examples/barrel/reports/index.mjs`

~~~javascript file=examples/barrel/reports/index.mjs
export { ReportTable } from "./ReportTable.mjs";
export { ReportToolbar } from "./ReportToolbar.mjs";
~~~

**文件：** `examples/barrel/ReportsPage.mjs`

~~~javascript file=examples/barrel/ReportsPage.mjs
import { ReportTable, ReportToolbar } from "./reports/index.mjs";

console.log(JSON.stringify([ReportTable.name, ReportToolbar.name]));
~~~

**文件：** `examples/barrel/reports/ReportTable.mjs`

~~~javascript file=examples/barrel/reports/ReportTable.mjs
export class ReportTable {}
~~~

**文件：** `examples/barrel/reports/ReportToolbar.mjs`

~~~javascript file=examples/barrel/reports/ReportToolbar.mjs
export class ReportToolbar {}
~~~

使用 barrel 时要注意几点。导出列表应有意挑选，避免意外公开内部模块。目录内的模块若又通过这个聚合入口互相导入，依赖图可能形成循环，所以同目录的实现通常直接导入具体文件。若多个 `export *` 都导出某个名字、但指向不同的绑定，这个名字会产生歧义；若它们最终指向同一个绑定，则没有歧义。显式重导出或改名能让接口意图更清楚。此外，barrel 仍静态依赖所有被重导出的模块；最终能删掉哪些未用代码，取决于打包器怎样分析导出与副作用，见下文的 tree shaking（摇树优化）。

## CommonJS 与 ESM 的加载和文件识别有什么区别？

CommonJS（简称 CJS）是 Node.js 早期采用的模块格式，由包装函数和 `require()` / `module.exports` 实现，不属于 ECMAScript 语言规范。ESM 在浏览器和 Node.js 中语法相同，但文件怎样解析、定位、取回仍由宿主决定。下面先对比两种格式在语言层面的差异，再分别看浏览器的两种脚本和 Node.js 的文件格式判定，这样才能判断同一行代码在哪个环境里成立。

| 关注点 | ESM | CJS（Node.js） |
| --- | --- | --- |
| 导入与导出 | 静态 `import`、`export`；也可调用 `import()` | `require()` 运行时导入，`module.exports` 导出；也可调用 `import()` |
| 顶层 `this` | `undefined` | 包装函数最初收到的 `exports` 对象 |
| strict mode（严格模式） | 自动启用 | 默认不启用；文件可写 `"use strict"` |
| 顶层 `await` | 支持 | CJS 源文件不能直接使用；`import()` 可以加载异步 ESM |
| 解析者 | 浏览器或 Node.js 宿主 | Node.js 或构建工具 |

`require()` 在代码运行到调用处时才同步执行；静态 `import` 则在模块体运行前就建立依赖。在 CJS 文件中调用 `import()` 是运行时的异步加载，不会让该文件变成 ESM。Node.js 26 还允许用 `require()` 同步加载不含顶层 `await` 的 ESM 依赖图，这一互操作规则在后文单独说明。

### 浏览器 classic script（经典脚本）与 module script（模块脚本）

| 脚本类型与加载 | 顶层代码环境 |
| --- | --- |
| 经典脚本 `<script>`：不能写静态 `import` / `export`，但可调用 `import()`。普通外部脚本在解析器遇到时暂停 HTML 解析，直到取回并执行；`async` 并行取回、完成后尽快执行；`defer` 并行取回，在文档解析后按顺序执行。 | 多个经典脚本在同一页面全局环境中运行；顶层 `this` 是页面全局 `this`。顶层 `var` 可成为 `window` 属性；`let` / `const` 是全局词法绑定。 |
| 模块脚本 `<script type="module">`：随 HTML 解析取回入口，并逐步发现、并行取回静态依赖；默认在文档解析完成后求值，`async` 在模块图就绪后可提前执行，`defer` 不改变时机。跨源模块请求需通过 CORS；裸模块说明符须由 import map 映射。 | 每个模块有自己的模块环境；模块自动处于 strict mode，顶层 `this` 为 `undefined`，顶层 `var` / `let` / `const` 不成为 `window` 属性。 |

两种脚本由同一个 JavaScript 引擎执行，但脚本类型决定了允许的语法、顶层名字放在哪里以及何时执行。所以去掉 `type="module"` 不只是改变加载方式：静态 `import` 在经典脚本里是语法错误。

### Node.js 怎样判定文件格式与解析说明符？

Node.js 同时支持 CJS 与 ESM。以下规则对应 Node.js 26.13.x；当模块加载器变化时，应按部署的 Node 主版本复核。

| 文件标记 | Node.js 处理格式 |
| --- | --- |
| `.mjs` | 总是按 ESM 处理 |
| `.cjs` | 总是按 CJS 处理 |
| `.js`，最近的 `package.json` 写有 `"type": "module"` | 按 ESM 处理 |
| `.js`，最近的 `package.json` 写有 `"type": "commonjs"` | 按 CJS 处理 |
| 没有显式格式标记的歧义 `.js` | Node 26 默认进行语法探测；源码含在 CJS 包装器中无法成立的语法时按 ESM 处理，否则按 CJS 处理。单独的 `import()` 可留在 CJS |

显式包类型示例：

**文件：** `examples/esm-binding/package.json`

~~~json file=examples/esm-binding/package.json
{
  "type": "module"
}
~~~

上表最后一行的 syntax detection（语法探测）从 Node.js 22.7.0 与 20.19.0 起默认开启；Node.js 26.13.1 的官方文档仍把它标为 Release candidate（候选稳定阶段），并指出扫描歧义文件的语法有额外开销。它识别的是无法在 CJS 中执行的语法：静态 `import` / `export`、`import.meta`、顶层 `await`，以及在顶层用 `const`/`let` 重新声明包装器参数（例如 `const require = 1`）。`import()` 表达式在 CJS 中本来就合法，所以文件里只出现 `import()` 不会被判为 ESM。新项目应在最近的 `package.json` 明确写 `"type"`，或使用 `.mjs` / `.cjs`，让宿主和构建工具不必猜测。

判定格式之后，还要解析说明符。`require()` 走 CommonJS 的同步解析路径（Node.js 26 在满足条件时也能借它同步加载 ESM）；`import()` 和静态 `import` 走 ESM 的加载路径。两者的相对路径都从当前文件所在位置解析，但 CJS 会自动补全扩展名、查找目录下的 `index.js` 或包入口，而 Node 的 ESM 要求写出完整扩展名，也不能省略目录的 `index.js`。裸包名在 Node 中按包查找规则解析，并可能受 `package.json` 的 `exports` 字段限制；浏览器则只认 URL 和 import map。至于 `fetch()`，它是应用的数据请求，文件用了 ESM 也不会让 Node 把 `"/api/..."` 补成某个服务器地址；Node 侧应传绝对 URL，或用已知的 API 地址构造 `new URL("/api/...", base)`。

### CJS 包装函数如何影响顶层绑定与 this？

Node.js 把每个 CJS 文件的内容放进一个函数包装器里执行，并把 `exports`、`require`、`module`、`__filename` 与 `__dirname` 作为这个函数的参数传入，所以它们在文件里像局部变量一样可用。`exports` 起初只是与 `module.exports` 指向同一对象的快捷变量：给 `exports.totalWithTax` 添加属性就能公开这个函数；但给 `exports` 本身重新赋值只改变局部变量，要替换整个模块导出，必须给 `module.exports` 赋值。下面的 `.cjs` 文件可以直接运行：`read-math.cjs` 用税率 `0.08` 计算税前金额 `100`，得到 `108`。

**文件：** `examples/node-commonjs/math.cjs`

~~~javascript file=examples/node-commonjs/math.cjs
const taxRate = 0.08;

exports.totalWithTax = function totalWithTax(net) {
  return net * (1 + taxRate);
};
~~~

**文件：** `examples/node-commonjs/read-math.cjs`

~~~javascript file=examples/node-commonjs/read-math.cjs
const math = require("./math.cjs");
console.log(math.totalWithTax(100)); // 108
~~~

**文件：** `examples/node-commonjs/replace-exports.cjs`

~~~javascript file=examples/node-commonjs/replace-exports.cjs
const initialExports = this;
exports = { ignored: true };
const shortcutDidNotReplace = module.exports === initialExports;
module.exports = { replaced: true };
const pointsToInitial = this === initialExports;
const pointsToReplacement = this === module.exports;
const checks = [
  shortcutDidNotReplace,
  pointsToInitial,
  pointsToReplacement,
];
console.log(JSON.stringify(checks));
// [true,true,false]
~~~

把同一段赋值按时间排开，引用关系更容易看清。令 A 是初始导出对象，B 是 `{ ignored: true }`，C 是 `{ replaced: true }`：

| 时刻 | 局部 `exports` | `module.exports` | 顶层 `this` |
|---|---|---|---|
| 包装器刚开始执行 | A | A | A |
| 执行 `exports = B` 后 | B | A | A |
| 执行 `module.exports = C` 后 | B | C | A |

最终 `require()` 交给调用者的是 C；改变局部变量或替换模块导出，都不会把已经固定的顶层 `this` 改成 C。

同理，`math.cjs` 里的 `taxRate` 只在包装函数内可见，不会成为全局变量。ESM 不使用这个包装器：顶层声明是模块作用域的绑定，顶层 `this` 为 `undefined`，模块自动处于严格模式。

### `require()` 第一次调用怎样执行模块，第二次又返回什么？

`require()` 是普通的同步函数调用，可以放在条件分支或函数里，不是静态依赖声明。在无循环依赖的情况下，第一次 `require()` 某个文件时，Node 解析出文件路径、执行包装函数，然后把此时的 `module.exports` 返回给调用者。之后再次 `require()` 同一个文件，Node 不会重新执行模块体，而是从缓存的模块记录中返回**此刻**的 `module.exports`；只有它没被替换过，才会再次得到同一个对象。下例故意在第一次加载后替换模块导出：

**文件：** `examples/node-commonjs/load-once.cjs`

~~~javascript file=examples/node-commonjs/load-once.cjs
console.log("module evaluated");
const october = { month: "October" };
module.exports = october;
october.replace = () => {
  module.exports = { month: "November" };
};
~~~

**文件：** `examples/node-commonjs/use-cache.cjs`

~~~javascript file=examples/node-commonjs/use-cache.cjs
console.log("before first require");
const first = require("./load-once.cjs");
console.log("after first require");
first.replace();
const second = require("./load-once.cjs");
const result = [first === second, first.month, second.month];
console.log(JSON.stringify(result));
~~~

运行 `use-cache.cjs`，依次输出 `before first require`、`module evaluated`、`after first require` 和 `[false,"October","November"]`；第二次调用没有再打印 `module evaluated`。变量 `first` 仍引用旧对象，而缓存中的模块记录已指向新的导出对象。若清除了缓存，或路径解析到了另一个文件，就不会命中这条缓存。

### Node.js 里 CJS 与 ESM 怎样互操作？

| 方向 | 规则与可依赖结果 |
| --- | --- |
| ESM 导入 CJS | CJS 的 `module.exports` 值作为默认导出；它可以是对象，也可以是数字、函数等其他值。Node 还可能从 CJS 源码静态分析出命名导出供兼容使用；该分析是启发式便利功能，不能依赖动态修改后的属性同步。 |
| CJS 用 `import()` 导入 ESM | 可异步导入，得到 Promise；适用于含顶层 `await` 的 ESM。 |
| CJS 用 `require()` 导入 ESM | Node 26 默认可同步加载没有顶层 `await` 的 ESM 依赖图，通常返回 module namespace object（模块命名空间对象）；默认导出位于 `.default`。若依赖图有顶层 `await`，抛出 `ERR_REQUIRE_ASYNC_MODULE`，改用 `import()`。 |

下面的 `modern-report.mjs` 没有顶层 `await`，所以 `use-modules.cjs` 可以同步 `require()` 它并得到命名空间对象；含顶层 `await` 的 `async-report.mjs` 则只能通过 `import()` 读取。运行 `use-modules.cjs`，依次输出 `["October","1,200","legacy CJS"]`、`ERR_REQUIRE_ASYNC_MODULE`，最后异步分支输出 `ready`。

**文件：** `examples/node-interop/modern-report.mjs`

~~~javascript file=examples/node-interop/modern-report.mjs
export const reportName = "October";
export default function formatTotal(total) {
  return new Intl.NumberFormat("en-US").format(total);
}
~~~

**文件：** `examples/node-interop/async-report.mjs`

~~~javascript file=examples/node-interop/async-report.mjs
await Promise.resolve();
export const ready = "ready";
~~~

**文件：** `examples/node-interop/legacy-report.cjs`

~~~javascript file=examples/node-interop/legacy-report.cjs
module.exports = { source: "legacy CJS" };
~~~

**文件：** `examples/node-interop/use-modules.cjs`

~~~javascript file=examples/node-interop/use-modules.cjs
const modern = require("./modern-report.mjs");
const legacy = require("./legacy-report.cjs");
const importedValues = [
  modern.reportName,
  modern.default(1200),
  legacy.source,
];
console.log(JSON.stringify(importedValues));

try {
  require("./async-report.mjs");
} catch (error) {
  console.log(error.code); // ERR_REQUIRE_ASYNC_MODULE
}

import("./async-report.mjs").then(({ ready }) => console.log(ready));
~~~

反方向，ESM 默认导入 CJS 时，得到的默认值就是 `module.exports`，而它不一定是对象。下面先默认导入上面导出对象的 `legacy-report.cjs`，再默认导入一个把数字 `42` 直接赋给 `module.exports` 的文件：

**文件：** `examples/node-interop/use-legacy.mjs`

~~~javascript file=examples/node-interop/use-legacy.mjs
import legacy from "./legacy-report.cjs";
console.log(legacy.source); // legacy CJS
~~~

**文件：** `examples/node-interop/number.cjs`

~~~javascript file=examples/node-interop/number.cjs
module.exports = 42;
~~~

**文件：** `examples/node-interop/use-number.mjs`

~~~javascript file=examples/node-interop/use-number.mjs
import value from "./number.cjs";
console.log(typeof value, value); // number 42
~~~

另一个方向也有兼容写法：ESM 可以写 `export { value as "module.exports" }`，让 CJS 的 `require()` 直接返回 `value`，而不是命名空间对象；此时其他命名导出不会自动并入这个值。

ESM 导入 CJS 时还能使用命名导入。Node 会静态扫描 CJS 源码，猜出可能的命名导出；这是启发式的互操作功能，不是 ECMAScript 的保证。CJS 模块执行（或从缓存复用）之后，Node 用**当时**的 `module.exports` 属性值初始化这些命名导出，此后对属性的修改不会同步过去。下例中，CJS 先把 `month` 从 `October` 改为 `November`，然后 ESM 导入它，导入完成后再改为 `December`：

**文件：** `examples/node-interop/mutable-month.cjs`

~~~javascript file=examples/node-interop/mutable-month.cjs
exports.month = "October";
exports.setMonth = (month) => { exports.month = month; };
~~~

**文件：** `examples/node-interop/read-month.mjs`

~~~javascript file=examples/node-interop/read-month.mjs
import legacy, { month } from "./mutable-month.cjs";
export { month };
export default legacy;
~~~

**文件：** `examples/node-interop/use-months.cjs`

~~~javascript file=examples/node-interop/use-months.cjs
const legacy = require("./mutable-month.cjs");
legacy.setMonth("November");
import("./read-month.mjs").then((namespace) => {
  const importedDefault = namespace.default;
  legacy.setMonth("December");
  console.log(JSON.stringify([importedDefault.month, namespace.month]));
});
~~~

运行 `use-months.cjs` 输出 `["December","November"]`：默认导入引用的是 `module.exports` 对象本身，因此读到后来改成的 `December`；命名导入 `month` 是初始化时取到的 `November`，不随后续修改变化。

跨格式互操作的细节随 Node.js 版本变化，应以所用版本的文档为准；要让应用在多个 Node 主版本或打包器之间表现一致，就明确声明文件格式，并在实际目标运行时上验证。

## 为什么 ESM 并不自动保证 tree shaking？

最后回到 bundler 这一层。tree shaking 是 bundler 删除未使用的导出或模块的优化，不是 ESM 在运行时提供的保证。静态 `import` / `export` 让工具能分析依赖关系和被引用的名字，但工具还要判断执行模块是否有 side effect（副作用）。例如，某个模块靠执行来注册事件监听器或加载 CSS，即使它的导出没人引用，也必须保留；若包在 `package.json` 里误标了 `sideEffects: false`，打包器可能删掉这个模块，导致监听器没注册或样式缺失。打包输出的可能是 ESM、浏览器脚本或 CJS，最终仍由相应宿主按自己的规则加载。

barrel 能集中公开名字，但静态重导出仍会把上游纳入待分析的依赖图；它本身不保证减包。是否拆成独立 chunk、哪些未用导出能被删、怎样尊重副作用声明，都由具体构建工具、配置、包元数据和输出目标决定。开发服务器和生产构建的差异、构建器怎样生成最终产物，见[构建工具怎样把源码变成可发布产物？](../tooling/build-tools.md)。

> [!info]- 来源
> - ECMAScript 2026 §16：静态 import/export、Module Requests、模块请求加载、链接与求值：[Scripts and Modules](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html)，其中 §16.2.1.6 说明循环模块记录与异步求值，§16.2.1.7 说明源码模块记录、导出解析与环境初始化。导入绑定及模块顶层 this：[Module Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)（§9.1.1.5，导入绑定间接读取目标绑定，模块 this 为 undefined）；ESM 严格模式：[Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)。顶层 await 自 ES2022 起进入 ECMAScript 标准。
> - WHATWG HTML Living Standard（核对日期 2026-11-12）：经典脚本与模块脚本的语法、取回和执行时机、async / defer 与模块跨源 CORS 要求：[The script element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)（§4.12.1）。
> - WHATWG HTML Living Standard（核对日期 2026-11-12）：浏览器 URL-like / bare module specifier 解析和 import map：[Module specifier resolution](https://html.spec.whatwg.org/multipage/webappapis.html#resolve-a-module-specifier)、[Import maps](https://html.spec.whatwg.org/multipage/webappapis.html#import-maps)；Window 环境的 API base URL 取文档当前 base URL，文档 base URL 可由 `<base href>` 改变：[Window script settings](https://html.spec.whatwg.org/multipage/nav-history-apis.html#script-settings-for-window-objects)、[Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)；`Request` 字符串输入按 API base URL 解析：[Fetch Standard §5.4](https://fetch.spec.whatwg.org/#dom-request)。
> - Node.js v26.13.1 官方文档：文件扩展名、最近的 package.json type、syntax detection 与显式声明格式建议：[Determining module system](https://nodejs.org/docs/v26.13.1/api/packages.html#determining-module-system)（v22.7.0 与 v20.19.0 起默认探测，Stability 1.2 — Release candidate）；CommonJS 包装器与顶层作用域：[The module wrapper](https://nodejs.org/docs/v26.13.1/api/modules.html#the-module-wrapper)；Node ESM 相对说明符解析：[Import specifiers](https://nodejs.org/docs/v26.13.1/api/esm.html#import-specifiers)；CommonJS 缓存与 `exports` 快捷变量：[Caching](https://nodejs.org/docs/v26.13.1/api/modules.html#caching)、[The exports shortcut](https://nodejs.org/docs/v26.13.1/api/modules.html#exports-shortcut)；ESM 导入 CJS 默认值和启发式命名导出：[CommonJS namespaces](https://nodejs.org/docs/v26.13.1/api/esm.html#commonjs-namespaces)；互操作与 `require(ESM)` 同步图限制：[Loading ECMAScript modules using require()](https://nodejs.org/docs/v26.13.1/api/modules.html#loading-ecmascript-modules-using-require)（该功能自 v25.4.0 起不再是实验性）。行为在 Node.js v26.13.0 实测。
> - Webpack 官方指南：[Tree shaking](https://webpack.js.org/guides/tree-shaking) 解释静态 ESM 使用分析、sideEffects 包字段与副作用误标。此处不把 Webpack 的优化行为推广成所有 bundler 的保证。

来源核对日期：2026-11-12。
