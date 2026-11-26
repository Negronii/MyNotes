# import 写下后，谁负责找到、链接和执行文件？

写下 `import { loadReport } from "./report-api.js"`，只是声明了一条依赖。去哪里取文件、按什么格式执行、能不能找到这个名字，由宿主（浏览器或 Node.js）按自己的规则决定；构建器还可能在发布前把整张依赖图改写一遍。本章先在浏览器里沿报表页从入口模块走到数据显示，再切到 Node.js，看 CommonJS 怎样加载、缓存，又怎样和 ECMAScript 模块互通。

读者已经知道经典脚本怎样被 HTML 解析器调度，也知道作用域和顶层绑定的规则。本章用到它们时只做一句提示。

## 语言、宿主和构建器各管哪一层？

ECMAScript module（ECMAScript 模块，ESM）由 ES2015 引入。它的语法只回答“依赖谁、公开哪些名字”，不规定发哪个 HTTP 请求、读哪个磁盘路径。

| 层 | 决定什么 | 报表页里的例子 |
| --- | --- | --- |
| ESM 语法 | 导入、导出哪些名字；依赖是静态声明还是运行时请求 | `import { loadReport } from "./report-api.js"` |
| 宿主（浏览器、Node.js） | 文件格式、说明符怎样解析成地址、怎样取回、在什么环境执行 | 浏览器用 URL 和 import map；Node.js 看扩展名和 `package.json` |
| bundler（打包器） | 构建时怎样解析、转换、拆分和优化 | 可能保留 ESM，也可能输出 CommonJS 或普通浏览器脚本 |

同一行 `import` 能否成立，要先问它运行在哪个宿主、经过了哪个构建器。下面按这三层依次展开。

## 浏览器怎样从入口模块走到页面结果？

沿用主线一的报表页，但为了只看模块加载，页面简化成一个显示报表 42 总额的 `output`。原来的 `/reports.js` 拆成四个模块：入口 `report-page.js`、读取数据的 `report-api.js`、格式化金额的 `report-format.js`，以及按需加载的 `lazy-tip.js`。示例的运行条件如下：

- 用本地 HTTP 服务器提供页面。模块不能从 `file:` 地址加载，JavaScript 文件要以 `text/javascript` 类型返回，因为浏览器要求模块脚本使用 JavaScript MIME 类型。
- 服务器让 `/api/reports/42` 返回 JSON `{ "total": 1200 }`。这是本章为演示设定的合成响应。
- 页面加载后，`output` 从“读取中”变成 `1,200`；控制台另外打印一条按需模块的提示。

目录结构是 `index.html`、`lazy-tip.js` 和 `reports/` 目录下的三个模块。

`index.html`：

```html
<!doctype html>
<meta charset="utf-8">
<title>报表 42</title>
<p>总额：<output id="total">读取中</output></p>
<script type="importmap">
{
  "imports": {
    "@reports/": "./reports/"
  }
}
</script>
<script type="module" src="./reports/report-page.js"></script>
<script>
  // 经典脚本不能写静态 import，但可以调用 import()。
  import("./lazy-tip.js").then(({ message }) => console.log(message()));
</script>
```

`reports/report-page.js`：

```javascript
import { loadReport } from "./report-api.js";
import formatTotal from "@reports/report-format.js";

const result = await loadReport("42");
if (!result || !Number.isFinite(result.total)) {
  throw new TypeError("报表响应必须包含数值 total");
}
document.querySelector("#total").textContent = formatTotal(result.total);
```

`reports/report-api.js`：

```javascript
export async function loadReport(reportId) {
  // 页面没有跨源 <base>，根相对地址仍指向本站。
  const response = await fetch(`/api/reports/${encodeURIComponent(reportId)}`);
  if (!response.ok) throw new Error(`报表请求失败：${response.status}`);
  return response.json();
}
```

`reports/report-format.js`：

```javascript
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}
```

`lazy-tip.js`：

```javascript
export function message() {
  return "按需模块已加载";
}
```

浏览器处理这张模块图分四步：

| 步骤 | 输入与操作 | 输出 |
| --- | --- | --- |
| 定位入口 | HTML 解析到模块脚本，按文档 base URL（基准 URL）解析 `src`，取回 `report-page.js` | 入口模块源码 |
| 解析并取回依赖 | 读出入口的静态 `import`：`./report-api.js` 相对导入者解析；`@reports/` 经 import map 映射。再递归处理每个依赖的静态导入。已发现的模块并行取回，但浏览器只能边取边发现，事先并不知道整张图 | `report-api.js`、`report-format.js` 的源码；跨源模块还必须通过 Cross-Origin Resource Sharing（跨源资源共享，CORS） |
| 链接 | 把每个导入名连到目标模块的导出绑定，检查名字是否存在 | 绑定连好；有名字对不上时，任何模块代码都不会开始执行 |
| 求值 | 先执行依赖，再执行入口；入口的顶层 `await` 等待接口响应 | 检查通过后，入口把 `1,200` 写进 `output` |

链接只是把名字连起来，不等于变量已经有值。如果导出方的 `let` 或 `const` 还没执行到初始化语句，提前读取仍抛 `ReferenceError`。这条边界和[作用域里的暂时性死区](./scope-closures-and-this.md)相同，通常在循环依赖里才会碰到；本例没有循环，依赖总是先求值完毕。

入口检查了 `total` 是有限数值才去格式化。`response.json()` 得到的是运行时数据，变量名和 TypeScript 类型都不会替服务端检查结构；怎样系统地验证外部数据，见[TypeScript 能保证什么，外部数据又该怎样验证？](./typescript-guarantees-and-runtime-validation.md)。

## 三种地址各按什么基准解析？

`@reports/report-format.js` 不以 `/`、`./`、`../` 开头，也不是完整 URL，属于 bare module specifier（裸模块说明符）。浏览器不会像 Node.js 那样去包目录里找它；没有 import map 提供映射，这条导入直接失败。

页面里有三类地址，基准各不相同：

- 模块里的相对导入 `./report-api.js`，相对**导入它的模块**的 URL 解析。
- HTML 里入口脚本的 `src`，相对**文档的 base URL** 解析。
- `fetch("/api/reports/42")` 是数据请求，不是模块加载。它按当前窗口的 API base URL 解析，通常就是文档 base URL。如果文档有跨源的 `<base href>`，根相对路径会指向那个源，请求也要受 CORS 约束。本例没有 `<base>`，请求发往提供页面的站点。

Node.js 的 `fetch()` 没有文档可作基准，直接传 `"/api/reports/42"` 会因缺少绝对 URL 而失败；要传完整地址，或用 `new URL("/api/reports/42", base)` 拼出来。

## 导入拿到的是绑定还是值？

导入建立的是到导出变量的 live binding（实时绑定），不是导入那一刻的拷贝。导出方后来写入的新值，导入方读得到；但导入方不能给导入名赋值。

`month-state.js`：

```javascript
export let selectedMonth = "2026-04";

export function selectNextMonth() {
  selectedMonth = "2026-05";
}
```

`read-month.js`：

```javascript
import { selectedMonth, selectNextMonth } from "./month-state.js";

const before = selectedMonth;
selectNextMonth();
console.log(JSON.stringify([before, selectedMonth])); // ["2026-04","2026-05"]
// selectedMonth = "2026-06"; // TypeError：导入绑定不能由导入方写入
```

`before` 是普通变量，保存了第一次读到的字符串；第二次读 `selectedMonth` 时，读的是导出方的同一个绑定，所以拿到新值。

导出有两种写法。named export（命名导出）要求导入方写对名字，可以用 `as` 换成本地名；default export（默认导出）每个模块最多一个，导入方自己起名。两者可以并存：

```javascript
// report-format.js
export default function formatTotal(total) {
  return new Intl.NumberFormat("zh-CN").format(total);
}
export function formatMonth(month) {
  return month.replace("-", "年") + "月";
}

// use-format.js
import formatTotal, { formatMonth as monthLabel } from "./report-format.js";
console.log(JSON.stringify([monthLabel("2026-05"), formatTotal(1200)]));
// ["2026年05月","1,200"]
```

`export { name } from "./other.js"` 转发的也是绑定，不会复制值。用一个目录入口集中重导出（barrel）不改变加载方式，也不保证产物变小；barrel 的写法、`export *` 同名歧义和它与 tree shaking 的关系，见[构建器怎样把源码变成可部署的文件？](../delivery/build-pipeline-and-bundling.md)。

## 动态导入和顶层 await 改变了什么？

静态 `import` 只能写在模块顶层，不能放进条件分支。要等用户需要时再加载，用 dynamic import（动态导入）`import()`：执行到调用处才开始加载，返回 Promise，兑现值是模块命名空间对象。

```javascript
export async function loadOptionalChart(shouldOpen) {
  if (!shouldOpen) return null;
  const { renderChart } = await import("./optional-chart.js");
  return renderChart();
}
```

已经加载过的模块会被复用，重复调用 `import()` 不会每次重新取回和执行。浏览器经典脚本、Node.js 的 CommonJS 文件和 ESM 都能调用 `import()`，前面 `index.html` 里的经典脚本就是这样加载 `lazy-tip.js` 的。它会不会被拆成独立 chunk（代码块），由构建配置决定。

top-level await（顶层 await）自 ES2022 起可用。报表入口在顶层等待接口响应，在无环的模块图里，导入它的模块要等它求值完毕才执行自己的模块体；与它无关的依赖分支可以继续求值。Promise 回调在事件循环中何时运行，见[事件循环怎样安排任务、微任务和渲染？](../browser/event-loop-tasks-and-rendering.md)。

## ESM 和 CommonJS 在语言层面差在哪里？

CommonJS（简称 CJS）是 Node.js 早期采用的模块格式，靠包装函数和 `require()` / `module.exports` 实现，不属于 ECMAScript 规范。ESM 的语法在浏览器和 Node.js 中相同，但文件怎样定位、取回仍由宿主决定。

| 关注点 | ESM | CJS（Node.js） |
| --- | --- | --- |
| 导入与导出 | 静态 `import` / `export`；也可调用 `import()` | 运行时调用 `require()`，用 `module.exports` 导出；也可调用 `import()` |
| 依赖何时建立 | 模块体运行前，从语法就能识别 | 执行到 `require()` 那一行才同步加载 |
| 顶层 `this` | `undefined` | 包装函数收到的初始 `exports` 对象 |
| strict mode（严格模式） | 自动启用 | 默认不启用，可写 `"use strict"` |
| 顶层 `await` | 支持 | 不能直接用；可以用 `import()` 加载含顶层 `await` 的 ESM |
| 谁来解析 | 浏览器或 Node.js | Node.js 或构建工具 |

在 CJS 文件里调用 `import()` 是运行时的异步加载，不会让这个文件变成 ESM。

浏览器里对应的区分是 classic script（经典脚本）和 module script（模块脚本）。两者由同一个引擎执行，但脚本类型决定允许的语法和顶层名字落在哪里：经典脚本写静态 `import` 是语法错误，只能用 `import()`；模块脚本自动处于严格模式，有自己的模块作用域，顶层 `var` 不会成为 `window` 属性。所以去掉 `type="module"` 不只是换了加载方式，代码本身就可能不再合法。模块脚本还要求跨源请求通过 CORS、裸说明符经 import map 映射。

两种脚本何时取回、何时执行（`async`、`defer`、模块脚本默认延迟到解析完成后求值），见[打开一个 URL 后，页面怎样变得可见又可交互？](../browser/from-url-to-interactive-page.md)；各宿主顶层 `this` 和顶层声明落在哪里的完整对照，见[函数里的变量和 this 从哪来？](./scope-closures-and-this.md)。

## Node.js 怎样判定文件格式并解析说明符？

Node.js 同时支持两种格式，先要判定一个文件按哪种执行。下表按 Node.js 26.13 文档整理，换主版本时要复核。

| 文件标记 | 按什么格式处理 |
| --- | --- |
| `.mjs` | 总是 ESM |
| `.cjs` | 总是 CJS |
| `.js`，最近的 `package.json` 写 `"type": "module"` | ESM |
| `.js`，最近的 `package.json` 写 `"type": "commonjs"` | CJS |
| `.js`，没有任何显式标记 | 语法探测：含有 CJS 包装器里不成立的语法就按 ESM，否则按 CJS |

syntax detection（语法探测）从 Node.js 22.7.0 和 20.19.0 起默认开启，26.13.1 文档仍标为 Release candidate，扫描歧义文件有额外开销。它找的是 CJS 里不能成立的语法：静态 `import` / `export`、`import.meta`、顶层 `await`，以及在顶层用 `const` / `let` 重新声明包装器参数（例如 `const require = 1`）。`import()` 在 CJS 里本来就合法，所以只出现 `import()` 的文件不会被判为 ESM。新项目应在 `package.json` 写明 `"type"`，或直接用 `.mjs` / `.cjs`，不让宿主和构建工具去猜：

```json
{
  "type": "module"
}
```

判定格式之后才解析说明符。`require()` 走 CJS 的同步解析路径；静态 `import` 和 `import()` 走 ESM 路径。两者的相对路径都从当前文件所在目录解析，区别在于：

- CJS 会自动补扩展名，会查找目录下的 `index.js` 或包入口。
- Node 的 ESM 要求写出完整扩展名，也不会替你补目录的 `index.js`。
- 裸包名按 Node 的包查找规则解析，可能受 `package.json` 的 `exports` 字段限制。浏览器只认 URL 和 import map，不做这种查找。

## CJS 的包装函数怎样决定 exports 和 this？

Node.js 把每个 CJS 文件的内容包进一个函数执行，`exports`、`require`、`module`、`__filename`、`__dirname` 是这个函数的参数，所以在文件里像局部变量一样可用。顶层声明也只是这个函数的局部变量，不会变成全局变量。

`exports` 起初和 `module.exports` 指向同一个对象。往 `exports` 上加属性能公开函数；给 `exports` 本身重新赋值只改了局部变量。要替换整个导出，必须赋给 `module.exports`。

`math.cjs` 与 `read-math.cjs`：

```javascript
// math.cjs
const taxRate = 0.08; // 只在包装函数内可见
exports.totalWithTax = function totalWithTax(net) {
  return net * (1 + taxRate);
};

// read-math.cjs
const math = require("./math.cjs");
console.log(math.totalWithTax(100)); // 108
```

下面这个文件把三种赋值放在一起：

```javascript
// replace-exports.cjs
const initialExports = this;
exports = { ignored: true };
const shortcutDidNotReplace = module.exports === initialExports;
module.exports = { replaced: true };
console.log(JSON.stringify([
  shortcutDidNotReplace,
  this === initialExports,
  this === module.exports,
])); // [true,true,false]
```

令 A 为初始导出对象，B 为 `{ ignored: true }`，C 为 `{ replaced: true }`，三个引用随时间这样变化：

| 时刻 | 局部 `exports` | `module.exports` | 顶层 `this` |
| --- | --- | --- | --- |
| 包装函数刚开始执行 | A | A | A |
| 执行 `exports = B` 后 | B | A | A |
| 执行 `module.exports = C` 后 | B | C | A |

`require()` 交给调用者的是最终的 `module.exports`，即 C。顶层 `this` 在包装函数开始时就固定为 A，之后哪种赋值都改不了它。

## require 第二次调用返回什么？

`require()` 是普通的同步函数调用，可以放在条件分支或函数里。没有循环依赖时，第一次 `require()` 某个文件，Node 解析路径、执行包装函数，再把此时的 `module.exports` 交给调用者。之后再 `require()` 同一个文件，Node 不再执行模块体，而是从缓存的模块记录里返回**此刻**的 `module.exports`。只有导出没被替换过，两次才拿到同一个对象。

下面故意在第一次加载后替换导出：

```javascript
// load-once.cjs
console.log("module evaluated");
const april = { month: "April" };
module.exports = april;
april.replace = () => {
  module.exports = { month: "May" };
};

// use-cache.cjs
console.log("before first require");
const first = require("./load-once.cjs");
console.log("after first require");
first.replace();
const second = require("./load-once.cjs");
console.log(JSON.stringify([first === second, first.month, second.month]));
```

运行 `use-cache.cjs`，依次输出 `before first require`、`module evaluated`、`after first require` 和 `[false,"April","May"]`。第二次调用没有再打印 `module evaluated`：变量 `first` 仍引用旧对象，缓存里的模块记录已经指向新对象。如果清掉了缓存，或路径解析到另一个文件，就不会命中这条缓存。

## 实例：Node.js 26 里 CJS 与 ESM 怎样互相导入？

> [!info] 版本范围
> 本节按 Node.js v26.13.1 文档整理，示例在 Node.js v26.13.1 上运行，结果与原稿在 v26.13.0 的实测一致（核对于 2026-11）。跨格式互操作的细节随版本变化；要在多个 Node 主版本或打包器之间表现一致，应显式声明文件格式，并在目标运行时上验证。

| 方向 | 结果 |
| --- | --- |
| ESM 导入 CJS | `module.exports` 的值作为默认导出，它可以是对象，也可以是数字、函数。Node 还会静态分析 CJS 源码，猜出可能的命名导出；这是启发式的兼容功能，不是 ECMAScript 的保证 |
| CJS 用 `import()` 导入 ESM | 异步加载，得到 Promise；含顶层 `await` 的 ESM 也可以 |
| CJS 用 `require()` 导入 ESM | 默认可以同步加载不含顶层 `await` 的 ESM 依赖图，通常返回模块命名空间对象，默认导出在 `.default`；图里有顶层 `await` 时抛 `ERR_REQUIRE_ASYNC_MODULE`，要改用 `import()`。该功能自 v25.4.0 起不再是实验性 |

**CJS 读取 ESM。** `modern-report.mjs` 没有顶层 `await`，可以同步 `require()`；`async-report.mjs` 有，只能用 `import()`：

```javascript
// modern-report.mjs
export const reportName = "April";
export default function formatTotal(total) {
  return new Intl.NumberFormat("en-US").format(total);
}

// async-report.mjs
await Promise.resolve();
export const ready = "ready";

// legacy-report.cjs
module.exports = { source: "legacy CJS" };

// use-modules.cjs
const modern = require("./modern-report.mjs");
const legacy = require("./legacy-report.cjs");
console.log(JSON.stringify([modern.reportName, modern.default(1200), legacy.source]));
// ["April","1,200","legacy CJS"]

try {
  require("./async-report.mjs");
} catch (error) {
  console.log(error.code); // ERR_REQUIRE_ASYNC_MODULE
}

import("./async-report.mjs").then(({ ready }) => console.log(ready)); // ready
```

ESM 也可以写 `export { value as "module.exports" }`，让 CJS 的 `require()` 直接拿到 `value`，而不是命名空间对象。这时其他命名导出不会并入 `value`。

**ESM 读取 CJS 的默认值。** 默认导入拿到的就是 `module.exports`，不一定是对象：

```javascript
// number.cjs
module.exports = 42;

// use-number.mjs
import value from "./number.cjs";
import legacy from "./legacy-report.cjs";
console.log(typeof value, value); // number 42
console.log(legacy.source);       // legacy CJS
```

**ESM 读取 CJS 的命名导出。** Node 在 CJS 模块执行完（或从缓存复用）时，用**当时**的 `module.exports` 属性值初始化这些命名导出，之后的修改不会同步过去。下例先把 `month` 从 `April` 改为 `May`，再让 ESM 导入，导入完成后又改为 `June`：

```javascript
// mutable-month.cjs
exports.month = "April";
exports.setMonth = (month) => { exports.month = month; };

// read-month.mjs
import legacy, { month } from "./mutable-month.cjs";
export { month };
export default legacy;

// use-months.cjs
const legacy = require("./mutable-month.cjs");
legacy.setMonth("May");
import("./read-month.mjs").then((namespace) => {
  const importedDefault = namespace.default;
  legacy.setMonth("June");
  console.log(JSON.stringify([importedDefault.month, namespace.month]));
});
```

输出 `["June","May"]`。默认导入引用的是 `module.exports` 对象本身，所以读到后来的 `June`；命名导入 `month` 是初始化时取到的 `May`，此后不再变化。这一点和 ESM 之间的 live binding 不同。

## 模块加载完之后

到这里，`import` 一行背后的三层已经分开：语法声明依赖和绑定；浏览器按 URL 和 import map、Node 按扩展名和包配置找到文件并执行；CJS 另有包装函数、`module.exports` 和 `require` 缓存。构建器怎样在发布前改写这张图，由[构建器怎样把源码变成可部署的文件？](../delivery/build-pipeline-and-bundling.md)接着讲。

模块执行完以后并不会消失：模块作用域里的变量、`require` 缓存里的 `module.exports`，以及它们引用的对象，在模块存续期间都一直可达。一个对象到底什么时候才能被回收，见下一章[对象什么时候能被回收，弱引用能帮什么、不能帮什么？](./memory-reachability-and-weak-references.md)。

> [!info]- 来源
> - **ESM 语法、加载、链接、求值**（“语言、宿主和构建器各管哪一层”“浏览器怎样从入口模块走到页面结果”“导入拿到的是绑定还是值”“动态导入和顶层 await”）：ECMAScript 2026 §16 [Scripts and Modules](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html)，其中 §16.2.1.6 循环模块记录与异步求值，§16.2.1.7 源码模块记录、导出解析与环境初始化；导入绑定间接读取目标绑定、模块顶层 `this` 为 `undefined`：§9.1.1.5 [Module Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)；ESM 自动严格模式：[Strict Mode Code](https://tc39.es/ecma262/2026/multipage/ecmascript-language-source-code.html#sec-strict-mode-code)。顶层 `await` 自 ES2022 进入标准。
> - **经典脚本与模块脚本**（“ESM 和 CommonJS 在语言层面差在哪里”）：WHATWG HTML Living Standard §4.12.1 [The script element](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)：两类脚本的语法、取回和执行时机、模块跨源 CORS 要求。核对日期 2026-11-12。
> - **三种地址的解析基准**：WHATWG HTML [Module specifier resolution](https://html.spec.whatwg.org/multipage/webappapis.html#resolve-a-module-specifier)、[Import maps](https://html.spec.whatwg.org/multipage/webappapis.html#import-maps)；Window 环境的 API base URL 取文档当前 base URL：[Window script settings](https://html.spec.whatwg.org/multipage/nav-history-apis.html#script-settings-for-window-objects)；`<base href>` 改变文档 base URL：[Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)；`Request` 的字符串输入按 API base URL 解析：[Fetch Standard §5.4](https://fetch.spec.whatwg.org/#dom-request)。核对日期 2026-11-12。
> - **Node.js 格式判定与说明符**（“Node.js 怎样判定文件格式并解析说明符”）：Node.js v26.13.1 [Determining module system](https://nodejs.org/docs/v26.13.1/api/packages.html#determining-module-system)（扩展名、最近的 `package.json` `type`、语法探测自 v22.7.0 / v20.19.0 默认开启、Stability 1.2 Release candidate、显式声明建议）；[Import specifiers](https://nodejs.org/docs/v26.13.1/api/esm.html#import-specifiers)（ESM 相对说明符要求扩展名）。
> - **CJS 包装函数、exports 与缓存**（“CJS 的包装函数怎样决定 exports 和 this”“require 第二次调用返回什么”）：Node.js v26.13.1 [The module wrapper](https://nodejs.org/docs/v26.13.1/api/modules.html#the-module-wrapper)、[The exports shortcut](https://nodejs.org/docs/v26.13.1/api/modules.html#exports-shortcut)、[Caching](https://nodejs.org/docs/v26.13.1/api/modules.html#caching)。
> - **CJS↔ESM 互操作**（实例节）：Node.js v26.13.1 [CommonJS namespaces](https://nodejs.org/docs/v26.13.1/api/esm.html#commonjs-namespaces)（默认导出为 `module.exports`、启发式命名导出）；[Loading ECMAScript modules using require()](https://nodejs.org/docs/v26.13.1/api/modules.html#loading-ecmascript-modules-using-require)（同步图限制、`ERR_REQUIRE_ASYNC_MODULE`、`"module.exports"` 导出名、v25.4.0 起非实验性）。本章 CJS 与互操作示例在 Node.js v26.13.1 上重新运行，输出与正文一致。
> - **barrel 与 tree shaking**（一句链接所依据的事实）：Webpack 官方指南 [Tree shaking](https://webpack.js.org/guides/tree-shaking)；详细讨论在构建章。
>
> 来源核对日期：2026-11-12。
