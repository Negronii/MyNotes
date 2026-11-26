# 构建器怎样把源码变成可部署的文件？

浏览器只按 URL 请求 HTML、JavaScript、CSS 和图片，不认识 `.ts`、Sass，也不会去 `node_modules` 里找包。构建器负责从入口出发找齐依赖、删掉没用的代码、分块、写出带哈希的文件，并把源码里的导入改写成浏览器能请求的 URL。本章跟着报表页的一份小源码走完这条路；读者需要知道 ESM 的 `import`、`export` 和动态 `import()` 在语言层的含义，见[import 写下后，谁负责找到、链接和执行文件？](../javascript/modules-and-host-boundaries.md)。

## 报表页的源码要经过哪五个阶段？

沿用主线一的报表页，这里只看它的前端源码。它是一个合成的小项目，部署在 `/reports/` 路径下。文中出现的生成文件名和请求结果，来自 Node.js 26.13.0、Vite 8.3.5、Webpack 5.109.0 与固定配置的实测 fixture；它们是这些版本和配置的输出，不是工具的默认文件名，也不是稳定 API。

- `index.html` 用 `<script type="module" src="./src/main.ts">` 引入入口脚本。
- `main.ts` 从 `rows.ts` 导入 `formatRow`，并静态导入 `report.css`。
- `report.css` 用 `url('./report.svg')` 引用一个图标；本例关闭小资源内联，图标会输出为独立文件。
- 用户点“编辑”打开编辑抽屉时，点击处理器才调用 `import("./editor.ts")`。

![合成报表项目的模块依赖关系](resources/build-tools-module-dependencies.svg)

`main.ts` 对 `formatRow` 的导入是值导入，会保留到输出中；`rows.ts` 里的 `Column` 只用于类型标注，类型擦除后不进入 JavaScript。`report.svg` 要等构建器处理 `report.css` 时，才由 CSS 解析器从 `url()` 中发现。

构建器从入口出发扩展这张图，再把图变成文件：

1. **确定入口。** `package.json` 里的脚本只负责启动构建命令，不是模块图的入口。Vite 默认从项目根目录的 `index.html` 开始；本例给 Webpack 显式设置 `entry: "./index.html"`。
2. **递归发现依赖。** 对每个请求，resolver（模块解析器）先从导入方出发定位到实际资源：相对请求 `./rows.ts` 从导入方所在目录查找，包名则按安装位置和包元数据解析。匹配的 loader（加载器）或内置处理器读取并转换这份资源，构建器再从转换结果里找出静态导入、动态导入和资源引用，把没处理过的目标加入队列，直到队列清空。
3. **优化并分块。** 队列清空，模块图才完整。tree shaking（摇树优化）删除能证明没被使用的代码；code splitting（代码分割）决定哪些模块进初始 chunk（代码分块），哪些进异步 chunk。最终有几个文件，取决于入口、动态导入和 Webpack `optimization.splitChunks` 这类分组规则。
4. **生成文件并改写引用。** 构建器写出 HTML、JavaScript、CSS 和资源文件，把源码请求改写成生成文件之间的引用，还可以按配置输出 manifest，记录源入口到输出文件的映射。文件名里的哈希随内容和引用关系变化，它怎样支撑缓存和发布见[发布新版本时，怎样让缓存和还开着的旧页面都不出错？](hashed-release-and-caching.md)。
5. **部署并运行。** 整套产物要放到与 public path（公开路径）相符的位置。浏览器先按 HTML 请求初始 JS 和 CSS，CSS 再引用图标；执行到动态导入时才请求编辑器的 chunk。

构建时发现的关系和浏览器运行时的请求是两件事：

| 源码或入口 | 构建时发现的关系 | 浏览器何时请求生成文件 |
|---|---|---|
| `index.html` | Vite 默认入口；Webpack 显式指定 | 取得页面 HTML 时 |
| `src/main.ts` | HTML 的 module script 引入 | 页面启动时加载生成的初始 JS |
| `src/rows.ts`、`src/report.css` | `main.ts` 静态导入 | 跟随初始 JS 与 CSS 加载 |
| `src/report.svg` | CSS 解析发现的 `url()` | 取得 CSS 后请求；或被内联成 data URL |
| `src/editor.ts` | 点击处理器里的动态 `import()` | 本例第一次打开编辑抽屉时 |

## 动态 import() 为什么在构建期就是一条异步边？

`import("./editor.ts")` 写在点击处理器里，但构建器读源码时就看见了这个语法。它会提前找到并转换 `editor.ts`，把它放进单独的异步 chunk，再把这处调用改写成对生成文件的请求。点击处理器只决定运行时何时调用它。

所以编辑器代码在构建时已经确定，在运行时按需取回。没有预加载时，浏览器要等第一次调用才请求这个 chunk；模块加载成功后，同一页面再次调用会复用已加载的模块，不再请求。两种构建器改写的方式不同：

- Vite 产物直接请求改写后的 ESM 地址，本例入口脚本里是 `await import("./editor-x2UHusWa.js")`，相对入口脚本自己的 URL 解析。
- Webpack 产物把调用改成 chunk ID，由运行时用 chunk ID、文件名映射和 `output.publicPath` 拼出 URL。

这条边也是发布时的风险来源：入口脚本里写死了编辑器 chunk 的文件名，旧页面第一次打开编辑抽屉时，请求的仍是旧文件名。下一章从这里接手。

## tree shaking 能删掉什么，barrel 和 sideEffects 怎样影响它？

tree shaking 是 bundler（打包器）删除未使用导出或整个模块的优化，不是 ESM 在运行时提供的保证。静态 `import`、`export` 让工具能分析依赖关系和被引用的名字；但一个模块即使导出没人用，执行它也可能有 side effect（副作用），例如注册事件监听器、修改全局对象、注入 CSS。工具必须证明删掉它不会改变行为，才能删。

本例在 `rows.ts` 里另放了一个从未被导入的导出 `unusedChart`，里面带一段可搜索的哨兵字符串。生产输出中找不到这段字符串，说明它已被删除。

Webpack 文档把这件事拆成两种优化：

- **按导出删（`usedExports`）。** 标记哪些导出没被使用，再由代码压缩器删除对应语句。压缩器要逐条语句判断有没有副作用，这很难做准；而且按规范，模块里的副作用必须求值，所以这一层跳不过整个模块及其依赖。
- **按模块跳过（`sideEffects`）。** 包在 `package.json` 里声明哪些文件没有副作用。若一个被声明为无副作用的模块，没有任何导出被直接使用，打包器可以跳过它和它下面的整棵依赖子树。这一层效果大得多。

barrel（聚合导出模块）是只用 `export ... from` 转发其他模块接口的文件，用来把一个目录要公开的名字集中到一个入口：

~~~javascript
// reports/index.mjs（barrel）
export { ReportTable } from "./ReportTable.mjs";
export { ReportToolbar } from "./ReportToolbar.mjs";

// reports/ReportTable.mjs
export class ReportTable {}

// reports/ReportToolbar.mjs
export class ReportToolbar {}

// ReportsPage.mjs
import { ReportTable, ReportToolbar } from "./reports/index.mjs";
console.log(JSON.stringify([ReportTable.name, ReportToolbar.name]));
~~~

barrel 只转发名字，不改变模块的加载方式。静态重导出让 barrel 依赖它转发的所有模块：页面只用 `ReportTable` 时，`ReportToolbar.mjs` 仍在待分析的图里。它能不能被删，取决于打包器能否确认那个模块没有副作用；包里有正确的 `sideEffects` 声明时，未被使用的转发目标可以整体跳过，否则它可能留在产物里。所以 barrel 本身不保证减包。另外三点要注意：

- 导出列表要有意挑选，避免把内部模块意外公开。
- 目录内的模块若又经 barrel 互相导入，依赖图可能成环；同目录实现通常直接导入具体文件。
- 多个 `export *` 导出同名、但指向不同绑定时，这个名字有歧义；指向同一绑定则没有歧义。显式重导出或改名能让接口意图更清楚。

`sideEffects` 标错的后果是功能缺失，而不是包变大。本例的 `import "./report.css"` 只为副作用导入，没有使用任何导出；若项目声明 `"sideEffects": false`，生产构建可能删掉这份样式。同理，一个靠执行来注册快捷键监听器的模块会被删掉，监听器就不会注册。Webpack 指南给出的写法是把有副作用的文件列出来，不含 `/` 的模式如 `*.css` 按 `**/*.css` 匹配：

~~~json
{
  "name": "reports-app",
  "sideEffects": ["./src/register-shortcuts.js", "*.css"]
}
~~~

这里的 `register-shortcuts.js` 是为说明而假设的文件。这些分析规则来自 Webpack；其他打包器怎样分析导出和副作用，以它们各自的文档和配置为准。打包输出可能是 ESM、浏览器经典脚本或 CJS，最终仍由对应宿主按自己的规则加载。

## 哪些输入决定一次构建能否复现？

要复现一份构建，至少要固定 Node.js、包管理器、锁文件和构建器的版本。`package.json` 的 `packageManager` 字段记录项目采用的包管理器及版本，但不会安装 Node.js；Node 版本仍要由版本文件、CI 镜像或运行环境固定。锁文件复用依赖解析结果，却固定不了操作系统、环境变量、系统工具，或构建脚本读取的任意外部输入。

Node.js 25 起，发行包不再附带 Corepack。如果项目靠 Corepack 按 `packageManager` 字段代理 `pnpm`、`yarn` 等命令，需要按当前 Corepack 文档单独安装它，或按所选包管理器的官方方式固定版本。例如 `build` 脚本写成 `vite build`，本地和 CI 都用同一版本的 pnpm 执行 `pnpm build`。相同的工具和锁文件减少依赖解析差异，但仍要检查实际生成的路径和部署结果。

## 生成文件的 URL 怎样解析，为什么 HTML 不能随便挪位置？

生成的引用有两种写法，解析基准不同：

- **相对 URL** 相对它所在的文件解析：HTML 里的 `src`、`href` 相对文档 URL，CSS 里的 `url()` 相对样式表 URL，ESM 里的 `import()` 相对模块脚本 URL。
- **运行时拼出的 URL** 由构建器注入的代码在执行时组合，例如 Webpack 用 `output.publicPath` 加文件名。

所以 HTML 的部署 URL、它内部的相对引用和服务器的挂载位置必须互相吻合。挪动 HTML 而不改引用，请求就会落到别的路径。

> [!example] Webpack 5.109 fixture：HTML 位置决定请求落点
> 本例 Webpack 把生成的 HTML 也输出到 `assets/` 目录，页面实际 URL 是 `/reports/assets/index-5248e5cf.html`。其中脚本 `../assets/__html_68cecd12_0-7cc84df8.js` 和样式 `../assets/__html_68cecd12_0-efdbfebc.css` 相对这个 URL 解析：所在目录是 `/reports/assets/`，`..` 回到 `/reports/`，再接 `assets/…`，请求落在 `/reports/assets/` 下；CSS 再引用 `/reports/assets/report-b1d5801f.svg`。
>
> 把同一份 HTML 原样放到 `/reports/index.html`，所在目录变成 `/reports/`，`..` 回到 `/`，两个引用解析成 `/assets/…`，本例请求返回 404。
>
> 编辑器 chunk 走另一条路：运行时使用 `output.publicPath: "/reports/"`，点击后才请求 `/reports/assets/354-b92eb80e.js`。构建统计（stats）还列出一个 `assets/main-fa829d06.js`，但生成的 HTML 没有引用它，浏览器也没有请求它。检查页面加载时，要沿 HTML、CSS 和脚本里的实际引用追踪，不要把构建输出的每个文件都当成一定会被请求。

Vite 用 `base` 配置把引用改写成带公开路径的绝对 URL，见后文的 Vite 一节。

## Webpack 的 loader 怎样逐个转换模块？

loader 本质上是一个函数：接收一个模块的源码文本，返回转换结果。前面第 2 阶段里，每个请求解析到实际资源后，由匹配的 loader 转换，Webpack 再从转换结果中发现后续依赖。下面这个 loader 只做字符串替换，不理解 JavaScript 结构；需要按语法节点改写代码时，应改用 AST（abstract syntax tree，抽象语法树）转换器：

~~~javascript
export default function replaceReportTitle(source) {
  return source.replaceAll("__REPORT_TITLE__", "Monthly Reports");
}
~~~

同一条规则可以串联多个 loader，执行顺序分两轮：

1. **pitch 阶段从左到右。** 若 loader 定义了 pitch 函数，Webpack 先按 `use` 数组从左到右调用它们。
2. **normal 阶段从右到左。** 然后按从右到左的顺序调用各 loader 的常规函数，前一个的输出是后一个的输入。

某个 pitch 一旦返回结果，就跳过它自己及右侧所有 loader 尚未执行的部分，把返回值直接交给左侧 loader 的常规函数，再继续向左。例如 `use: [a, b, c]` 正常顺序是 `a.pitch → b.pitch → c.pitch → c → b → a`；若 `b.pitch` 返回结果，顺序变成 `a.pitch → b.pitch → a`。

下面的 Sass 配置因此先运行 `sass-loader` 把 Sass 编译成 CSS，再交给 `postcss-loader`：

~~~javascript
module: {
  rules: [
    {
      test: /\.s[ac]ss$/i,
      type: "css/auto",
      use: ["postcss-loader", "sass-loader"]
    }
  ]
}
~~~

`type: "css/auto"` 把编译出的 CSS 交给 Webpack 原生的 CSS 模块处理。只有每一步确有职责时才串联 loader：Sass、Less、Stylus、PostCSS 仍需要各自的 loader，普通 CSS 已有原生处理，不要只因沿用旧配置再加一个。图片、字体、媒体与文本资源可用 Asset Modules（资源模块）处理，它在许多项目里替代了旧的 `file-loader`、`url-loader` 和 `raw-loader`；图标最终是独立文件还是 data URL，取决于工具版本、资源大小和内联配置。

构建成功不等于类型正确。Webpack 原生 TypeScript 擦除、`ts-loader` 的 `transpileOnly: true` 和 Vite 的转译都只删除类型，不做类型检查，需要另设 `tsc --noEmit` 之类的检查步骤；`ts-loader@9.6.2` 默认会做类型检查。

> [!info] 实例：Webpack 5.109 原生 CSS、HTML 与 TypeScript 的 `auto`
> Webpack 5.109.0 中，原生 CSS 和原生 HTML 的开关默认都是 `auto`。`auto` 不是逐个文件在原生处理和旧 loader 之间自由切换：配置里只要有接管这类文件的旧规则，原生处理可能在整个编译中关闭。迁移时要同时构建一个应由原生能力处理的文件和一个应走旧规则的文件，确认两者的实际行为。没有冲突配置时，原生 CSS 能处理常见 CSS、`@import`、`url()` 和 CSS Modules；原生 HTML 能按入口和模块图生成页面引用，依赖模板功能的旧页面要逐项迁移。
>
> 原生 TypeScript 类型擦除在 5.107.0 加入，5.109.0 默认 `experiments.typescript: "auto"`。它只删除类型标注，不处理 TSX、enum 这类需要额外代码转换的语法。它依赖 Node 的 `module.stripTypeScriptTypes` API：22 系列从 22.13.0 起提供，23 系列从 23.2.0 起提供；Node 22.6.0 加入的只是命令行选项 `--experimental-strip-types`，没有这个 API。`auto` 会检测这个 API 是否存在，以及配置里是否已有处理 TypeScript 的 loader 规则。

> [!info]- Webpack 5.109 `auto` 的判定细节
> CSS 和 HTML 的 `auto` 在配置层先用 `/file.css`、`/file.module.css`、`/file.html` 等合成路径探测。`test`、`resource` 或 `include` 任一条件都可能计入；`exclude` 不参与这项宽松探测。正则中明确引用扩展名的模式也会计入：例如 `/source\.css$/` 即使不匹配 `/file.css`，仍可关闭这一编译的原生 CSS。只有显式 `type` 或未设 `enforce` 的普通 `loader`/`use` 才算接管；`pre`、`post` loader 不触发关闭。若 `auto` 保持启用，真实模块只有在默认原生类型仍被选中、已应用 loader、且没有 `matchResource` 显式重定类型时，才沿旧路径退让给 loader 产物。
>
> 使用默认 `resolve.extensions` 时，显式 `experiments.html: true` 会把 `.html` 排在 JavaScript 扩展名前，目录入口可优先解析为 `index.html`；`auto` 则把 `.html` 放在 JavaScript 后。自定义扩展名顺序时按实际配置判断。

## plugin 怎样处理整次构建，DefinePlugin 为什么不能放密钥？

loader 一次只转换一个模块。plugin（插件）挂在编译器和编译过程的钩子上，处理整次构建共享的状态或产物。要新增产物，应在 `compilation.hooks.processAssets` 中选择合适的 stage。下面的统计插件在 `done` 钩子里把 JSON 写到执行命令时的当前目录；它不会自动进 `dist/`，也不属于 Webpack 管理的 asset（产物）：

~~~javascript
import { writeFileSync } from "node:fs";

class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tap("BuildStatsPlugin", stats => {
      const json = stats.toJson({ assets: true, modules: false });
      writeFileSync("build-stats.json", JSON.stringify(json, null, 2));
    });
  }
}
~~~

`DefinePlugin` 在构建时把代码中的表达式替换成常量。替换后的值写进客户端 bundle，任何能打开页面的人都能读到，所以不能放密钥。

> [!info]- 实例：Webpack 5.109 的 processAssets、emit 与旧插件迁移
> `processAssets` 的 stage 决定生成或读取资源的时点。`ADDITIONAL` 位于代码压缩、source map 和传输压缩之前，适合新增自有文件。到 `SUMMARIZE` 才新增文件时，`OPTIMIZE_SIZE` 已经过去，Webpack 不会重跑整个阶段；但订阅了 `additionalAssets` 的处理器仍可单独处理后续新增资源。5.109 的默认 JavaScript minimizer 就使用这种订阅，所以不能只凭新增阶段断言文件不会被压缩，还要看处理器的匹配条件。
>
> 全部 `processAssets` 阶段完成并封存资源后，Webpack 才调用 `emit`，随后写入配置的 output filesystem。后注册的 emit tap 能看到较早 tap 的改动，但它新增的文件已错过先前的 stage；`afterEmit` 已在输出之后，修改不会回写刚才的文件。5.109 默认 `backCompat: true`，此时写封存的 `Compilation.assets` 会警告；关闭兼容模式后该对象被冻结。
>
> `HtmlWebpackPlugin` 当前 README 标记为弃用；原生 HTML 可覆盖常见页面产物，模板插件的定制行为要逐项核对。CSS、HTML 的内置压缩从 5.110.0 开始。`CompressionWebpackPlugin` 已弃用，压缩 generator 迁入 `minimizer-webpack-plugin`，迁移选项从 `minimizer-webpack-plugin@5.11.0` 起提供；生成 `.gz`、`.br` 文件不代表服务器已按内容协商返回相应的 `Content-Encoding`。5.109 默认 JavaScript 压缩仍用 Terser，`terser-webpack-plugin` 从自身 5.6.0 起更名为 `minimizer-webpack-plugin`。覆盖 `optimization.minimizer` 时，要保留默认项就写上 `"..."`。更多历史选项见[归档的 Webpack 插件对照表](../../archive/front-end/Deprecated_Interview_Notes/webpack-plugin-history.md)。

## Vite 的开发服务器为什么不能代替生产构建检查？

Vite 的开发和生产走两条路。按 Vite 8.3.5 文档，开发服务器按浏览器请求逐个提供转换后的原生 ESM，并用 Rolldown 预打包第三方依赖；`vite build` 则由 Rolldown 一次性生成静态的 HTML、JS、CSS 和资源文件。两条路在分块、目标浏览器、公开路径和服务器行为上都可能不同，开发环境能跑通不代表生产产物没问题。HMR（Hot Module Replacement，热模块替换）只属于开发期：服务器通知文件变化，浏览器端运行时取回更新后的模块并调用其注册的接受回调，当前模块边界处理不了时才整页刷新。它与生产发布无关。

本例把页面挂在 `/reports/`，并打开 manifest、关闭小 SVG 内联：

~~~javascript
import { defineConfig } from "vite";

export default defineConfig({
  base: "/reports/",
  build: { manifest: true, assetsInlineLimit: 0 }
});
~~~

`base` 让 HTML、CSS `url()` 和 JS 导入的资源引用都带上公开路径。生成的 HTML 指向初始脚本和样式，CSS 再指向 SVG：

~~~html
<script type="module" src="/reports/assets/index-gRN8M4PG.js"></script>
<link rel="stylesheet" href="/reports/assets/index-QsJV6IX7.css">
~~~

~~~css
background: url(/reports/assets/report-D2wE4vR2.svg);
~~~

入口脚本里的动态导入改写成 `await import("./editor-x2UHusWa.js")`。脚本从 `/reports/assets/` 加载，浏览器因此请求 `/reports/assets/editor-x2UHusWa.js`，而不是源码 `editor.ts`。用无界面 Chromium 首次打开页面时没有请求编辑器；点击后该 URL 返回 200。本例把这次构建记为 v41。

Vite 默认不生成 manifest。本例打开它来核对映射：`"index.html"` 一项记录了 `dynamicImports: ["src/editor.ts"]`，`"src/editor.ts"` 一项的 `file` 是 `"assets/editor-x2UHusWa.js"`。`file` 值相对输出目录，不带 `/reports/` 前缀。浏览器只按 HTML、CSS 和 JS 里的引用请求文件，不读 manifest；需要它的是服务端渲染或后端集成工具。

另外几点也不能靠“构建成功”证明：

- 恢复默认内联阈值后，本例的小 SVG 会变成 CSS 里的 data URL，不再单独请求。
- `base` 必须与静态站点的挂载路径一致。`vite preview` 只用于本地预览生产构建，不是生产服务器；上线前要在实际部署 URL 下检查 HTML、初始脚本和样式、异步 chunk、图像、缓存头、压缩和路由回退。
- Vite 用 Oxc 转译 TypeScript，只删类型，不做类型检查。
- Vite 8.3.5 的 `build.target` 默认面向固定日期（2026-01-01）的 Baseline Widely Available 浏览器范围：Chrome/Edge 111、Firefox 114、Safari 16.4。它只决定语法转换到什么程度，不补运行时 API，`tsconfig.json` 的 `target` 也不能代替它。支持更早的浏览器要另配 polyfill（兼容补丁）并在目标环境验证，见[用一个新 API 之前，怎样确认运行时真的支持？](../javascript/feature-availability.md)。

## source map 怎样把报错映回源码，又会暴露什么？

生产代码经过转换和压缩，报错的行列号对应生成文件，很难读懂。source map（源映射）记录生成代码位置与原始源码位置的对应关系，调试器或错误收集工具据此把位置映回源码；映射本身不能还原出原始文件，除非它附带了源码文本。几个选择各影响一件事：精确到行还是列影响定位精度；是否使用 loader 提供的映射影响能映回多早的源码；映射内嵌还是外置、是否附带源码文本，影响构建成本和对外暴露的信息。

| Webpack `devtool` 例子 | 主要含义 | 适用边界 |
|---|---|---|
| `eval-source-map` | 逐模块用 `eval` 关联完整映射 | 开发定位精度高；官方把初次构建速度列为 slowest |
| `cheap-source-map` | 行级映射，忽略 loader 提供的映射 | 不支持列级断点；可能停在转换后的行 |
| `cheap-module-source-map` | 使用 loader 映射后简化到行级 | 能映回更早的源码，但没有列位置 |
| `source-map` | 外置完整映射，bundle 写引用 | 可恢复行列；要检查 `.map` 是否可公开请求 |
| `hidden-source-map` | 外置映射，bundle 不写 `sourceMappingURL` | 可把 `.map` 单独上传到私有错误工具；隐藏引用不等于访问控制 |
| `nosources-source-map` | 不内嵌 `sourcesContent` | 仍可能泄露文件名和映射关系 |

`cheap-` 只保留行级位置。`module-` 只在 cheap 组合里表示使用 loader 映射；完整的 `source-map` 本身就会使用可用的 loader 映射。Webpack 5.105 起 `devtool` 也可以写成数组，每项用 `type` 指定作用对象：`"javascript"`、`"css"` 或 `"all"`；`all` 只指 JavaScript 与 CSS，不含图像、字体等资源。当前完整语法还有 `-debugids`，5.112.0 加入 `-scopes`；组合顺序与可用性按锁定版本核对。旧预设的详细映射见[Webpack source map 预设对照](../../archive/front-end/Deprecated_Interview_Notes/webpack-source-map-presets.md)。

source map 不是权限边界。`.map` URL 只要仍由服务器公开提供，去掉 bundle 里的引用也挡不住知道路径的人；`nosources` 只去掉源码文本，目录和文件名仍可能暴露。发布时要分别检查输出文件、服务器静态资源规则和错误收集工具的访问权限。

## 这套文件上线后，旧页面还会请求什么？

构建器交出的是一组互相引用的文件：一份入口 HTML、带哈希文件名的初始 JS 和 CSS、只在首次打开编辑抽屉时才请求的编辑器 chunk，以及可选的 manifest。入口脚本里写死了编辑器 chunk 的文件名。下一章接着问：发布 v42 后，已经开着的 v41 页面第一次打开编辑抽屉，请求的仍是 v41 的 chunk；缓存头和发布顺序要怎样安排，它才拿得到 200 而不是 404？见[发布新版本时，怎样让缓存和还开着的旧页面都不出错？](hashed-release-and-caching.md)。

> [!info]- 来源
> - **五个阶段、依赖发现与异步边（Webpack）：** [NormalModule.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/NormalModule.js#L1576-L1650)、[Compilation.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compilation.js#L1766-L1810)、[ImportParserPlugin.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/dependencies/ImportParserPlugin.js#L580-L620)：转换后解析依赖、`import()` 形成异步边；[JsonpChunkLoadingRuntimeModule.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/web/JsonpChunkLoadingRuntimeModule.js#L135-L196)：运行时组合 public path 与文件名。均为 Webpack v5.109.0 源码。
> - **tree shaking、`usedExports` 与 `sideEffects`、barrel 跳过子树、`*.css` 模式与 CSS 误删：** [Webpack Guides: Tree Shaking](https://webpack.js.org/guides/tree-shaking)，“Mark the file as side-effect-free”与“Clarifying tree shaking and sideEffects”节，核对于 2026-11-26。barrel 的转发语义与 `export *` 歧义：[ECMAScript 2026 §16 Scripts and Modules](https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html)，§16.2.1.7 导出解析。
> - **可复现构建：** [Node.js 25.0.0 发布说明](https://nodejs.org/en/blog/release/v25.0.0) 与 [Corepack 文档](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html)：Corepack 从 Node 25 起不随发行包提供；[Corepack `packageManager` 字段](https://github.com/nodejs/corepack#when-authoring-packages)。核对于 2026-11-12。
> - **HTML 相对引用与发布路径（Webpack 实例）：** [原生 HTML](https://webpack.js.org/guides/native-html/)、[输出管理](https://webpack.js.org/guides/output-management/)。fixture 中的 HTML 路径与 chunk 文件名为 Node.js 26.13.0 + Webpack 5.109.0 实测。
> - **loader 顺序与 pitch、Asset Modules、ts-loader：** [Loaders](https://webpack.js.org/concepts/loaders/)（pitch/normal 次序）；[Asset Modules](https://webpack.js.org/guides/asset-modules/)；[ts-loader `transpileOnly`](https://github.com/TypeStrong/ts-loader#transpileonly)。
> - **Webpack 5.109 原生 CSS/HTML/TypeScript 的 `auto`：** [defaults.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L649-L686)（合成路径探测与 TypeScript 默认）；[RuleSetCompiler.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/rules/RuleSetCompiler.js#L473-L578)（宽松规则探测与扩展名正则）；[implicitTypeLoaderFallback.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/util/implicitTypeLoaderFallback.js#L13-L51)（逐模块退让条件）；[TypeScriptPlugin.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/typescript/TypeScriptPlugin.js#L119-L134)（Node API 探测）；[experiments.typescript](https://webpack.js.org/configuration/experiments/#experimentstypescript)、[HTML 作为默认入口](https://webpack.js.org/configuration/experiments/#html-as-the-default-entry)（扩展名顺序）。Node API 版本边界：[Node.js 22.6.0 发布说明](https://nodejs.org/en/blog/release/v22.6.0)、[`module.stripTypeScriptTypes()`](https://nodejs.org/download/release/v22.13.0/docs/api/module.html#modulestriptypescripttypescode-options)、[22.13.0](https://nodejs.org/en/blog/release/v22.13.0)、[23.2.0](https://nodejs.org/en/blog/release/v23.2.0) 发布说明。
> - **plugin、processAssets、emit 与压缩插件迁移：** [processAssets 与 additionalAssets](https://webpack.js.org/api/compilation-hooks/#processassets)；[minimizer-webpack-plugin v5.6.1 源码](https://github.com/webpack/minimizer-webpack-plugin/blob/v5.6.1/src/index.js)（`OPTIMIZE_SIZE` 订阅 `additionalAssets: true`）；[Compiler.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compiler.js#L1081-L1106)、[Compilation.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compilation.js#L3806-L3834)、[defaults.js backCompat](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L622-L623)（emit、资源封存与兼容模式）；[HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme)、[CompressionWebpackPlugin README 与迁移](https://github.com/webpack/compression-webpack-plugin#migrating)（弃用标记、`minimizer-webpack-plugin@5.11.0`）；[Terser minimizer 5.6.0 发布](https://github.com/webpack/minimizer-webpack-plugin/releases/tag/v5.6.0)（包名变更）。
> - **Vite 开发与构建、base、manifest、内联、target：** Vite 8.3.5 固定版本文档 [build](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/build.md)、[assets](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/assets.md)、[features](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/features.md)（Oxc 只转译）、[HMR API](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/api-hmr.md)、[build options](https://github.com/vitejs/vite/blob/v8.3.5/docs/config/build-options.md)、[backend integration（manifest）](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/backend-integration.md)、[生产动态导入辅助逻辑](https://github.com/vitejs/vite/blob/v8.3.5/packages/vite/src/node/plugins/importAnalysisBuild.ts#L314-L344)。v41 文件名与请求为 Node.js 26.13.0 + Vite 8.3.5 fixture 实测。
> - **source map：** [Webpack devtool](https://webpack.js.org/configuration/devtool/)（预设表）；[Webpack 5.105 数组配置](https://webpack.js.org/blog/2026-02-03-webpack-5-105/)；[Webpack 5.112 `-scopes`](https://webpack.js.org/blog/2026-10-13-webpack-5-112/)。
