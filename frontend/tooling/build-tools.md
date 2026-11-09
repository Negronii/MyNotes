# 构建工具怎样把源码变成可发布产物？

月度报表页的 TypeScript 类型检查、模块解析、样式和图片处理、压缩以及服务器实际返回的文件，属于构建与发布链路上的不同工作。构建工具沿依赖图处理源码并输出页面 HTML（超文本标记语言）、样式表 CSS（层叠样式表）、JavaScript 和静态资源；开发服务器能成功运行，并不能证明生产服务器会提供正确的路径、分块和调试映射。

~~~mermaid
flowchart LR
  A[入口与 package.json] --> B[解析模块依赖图]
  B --> C[模块级源码转译与 loader]
  C --> E[汇总并输出 JavaScript 分块、页面、样式、图片与源映射]
  A -. 插件钩子可跨多个构建阶段 .-> D[compiler 与 compilation 生命周期]
  D -. 可读取或修改产物 .-> E
  E --> F[部署服务器返回文件]
  F --> G[浏览器检查路径、行为和兼容性]
  A -. 单独执行类型检查 .-> H[tsc --noEmit]
~~~

## 为什么要固定 Node.js 与包管理器版本？

`package.json` 的 `packageManager` 字段可以记录项目验证过的包管理器及版本，例如 `"packageManager": "pnpm@10.0.0"`；它描述项目期望的工具，不会自行安装该工具。CI（持续集成）与本地环境都应安装同一版本，并按提交的锁文件恢复依赖。Node.js 自 25 起不再随发行包提供 Corepack；若项目依赖 Corepack 的命令 shim（命令代理），应按其当前说明单独安装，或改用包管理器官方安装流程。

## Webpack 的模块加载器与插件分别处理什么？

Webpack 从 entry（入口）解析依赖图。loader（模块加载器）转换单个模块的源码；plugin（插件）订阅 compiler（编译器）或 compilation（单次编译）的生命周期，在更广的构建阶段处理任务或产物。常见角色如下：

| 构建环节 | 职责 | 报表页中的例子 |
|---|---|---|
| `entry` / `output` | 指定依赖起点、输出目录和文件名 | `src/main.ts` 进入 `dist/` |
| module rule + loader | 按资源类型处理单个模块 | Sass 转 CSS；TS 或 JSX 转 JavaScript |
| plugin hook（插件钩子） | 访问一次完整构建或单次 compilation | 生成页面、统计产物、调整资源 |
| `optimization`（优化配置） | 压缩、分包等优化 | 生产模式默认优化，再按项目需求覆盖 |

新配置先核对当前内置能力。Webpack 5.109 起，原生 CSS 处理默认按 `auto` 启用；已有匹配 CSS 的 loader 或显式类型规则时，它会保留原管线。一般 CSS 与 CSS Modules 无须再默认搭一整套 `style-loader`、`css-loader` 和提取插件；Sass 等预处理仍需要对应转换。原生 TypeScript 处理也在宿主 Node 支持 `module.stripTypeScriptTypes`、且没有匹配 TS loader 时自动启用，但只擦除类型，不执行类型检查，也不处理 TSX、带运行时行为的 enum 等非可擦除语法。需要这些能力时，再选择相应转换器并单独运行类型检查。

下例保留已有 loader 项目的样式链，用来追踪转换顺序；它不是新项目必须复制的默认配置。Webpack 的 `use` 数组中，普通 loader 从右往左执行；有 `pitch`（预处理阶段）的链条先从左往右执行 pitch，再反向执行普通函数。如果某个 pitch 返回内容，webpack 会从该 loader 的左邻项开始反向运行 normal 阶段；该 loader 自己的 normal 函数，以及它右侧尚未 pitch 的 loader 和 normal 函数都会被跳过。只有 pitch 都继续传递时，完整 normal 函数链才会执行。插件钩子作用在 compiler 或 compilation 的不同生命周期阶段，不表示插件固定等所有 loader 完成后才运行。例如下面样式链先由 `sass-loader` 编译，再由 `css-loader` 处理导入关系，最后由 `style-loader` 注入开发页面：

~~~javascript
module: {
  rules: [
    {
      test: /\.scss$/,
      use: ["style-loader", "css-loader", "sass-loader"]
    },
    {
      test: /\.tsx?$/,
      use: ["babel-loader", "ts-loader"]
    }
  ]
}
~~~

自定义 loader 可以展示转换函数的形状。这个示例只替换确切字符串；它不会解析 JavaScript 结构，若要根据语法节点改写代码，应使用 Abstract Syntax Tree（AST，抽象语法树）转换器。

~~~javascript
export default function replaceReportTitle(source) {
  return source.replaceAll("__REPORT_TITLE__", "Monthly Reports");
}
~~~

第二条规则中 `ts-loader` 先运行，输出交给 `babel-loader`。只有项目确实需要两步各自提供的能力时才同时保留；重复转译会增加构建工作，也可能让两套 target 配置互相覆盖。Webpack 5 的 Asset Modules 可直接处理图片、字体、媒体和文本资源，取代许多旧项目的 `file-loader`、`url-loader` 或 `raw-loader` 配置。

plugin 通过生命周期 hook（钩子）扩展构建。若自定义 plugin 要增加或修改输出资源，当前 Webpack 文档要求使用 `compilation.hooks.processAssets`，并为工作选择适当 stage（阶段）。在 compiler 的 `emit` hook 中添加或修改资源仍可能通过兼容接口运行，但会触发弃用警告；此时 compilation 已封存，资源会错过后续压缩、源映射（source map）和哈希阶段。读取已有资源仍可放在 `emit`。

`done` hook 在本次编译完成后收到构建统计对象（`stats`）。下面保留原稿里的统计示例：它写出一份构建诊断 JSON（JavaScript 对象表示法）到项目当前工作目录，供开发者检查产物信息；若要生成发布目录内的资源，则改用 `processAssets`。

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

Webpack 的 `DefinePlugin` 在构建时替换写进代码的表达式；它不会读取浏览器里的运行时环境变量。写入前端包的值会随产物提供给用户，不能把密钥放在 `DefinePlugin` 的客户端常量中。已有 loader 管线中的 `MiniCssExtractPlugin` 负责输出独立 CSS 文件；`CompressionWebpackPlugin` 可生成 gzip/Brotli 资源，但服务器仍要配置协商并发送相应压缩文件。其他历史插件角色与当前注意点见[归档的 Webpack 插件对照表](../../archive/front-end/Deprecated_Interview_Notes/webpack-plugin-history.md)。

Webpack 现提供原生 HTML 处理。官方文档显示 `experiments.html` 默认值自 5.109.0 起为 `"auto"`：只有没有现存 loader 或显式 `type` 规则匹配 `.html` 资源时才自动启用 HTML 处理，因此迁移前要检查现有规则。显式设为 `true` 会强制启用原生解析，即使 HTML 资源先经过 loader；资源规则上的显式 `type` 仍决定其处理方式。`true` 还会让无扩展名导入或入口的默认扩展名顺序把 `.html` 放在 JavaScript 前，`auto` 则将其排在 JavaScript 后。原生 HTML 入口可生成 `index.html`。HtmlWebpackPlugin 仓库 README 当前标为 deprecated（弃用），并指向迁移指南；已有配置可继续工作，但新配置应先核对所用 Webpack 版本的原生 HTML 能力和模板需求。

## Vite 开发服务器为什么不能代替生产构建检查？

Vite 的开发服务器按需提供转换后的 ESM，并用 HMR（热模块替换）更新开发页面。Vite 8 于 2026-03 发布稳定版，使用 Rolldown 作为打包器，Oxc 工具链处理转换。开发阶段和生产构建可以经过不同的处理路径，检查一个开发页面不能替代检查最终打包文件（bundle）。

Vite 8 对 TypeScript 文件只做转译，不执行完整类型检查；当前文档建议在生产构建之外运行 `tsc --noEmit`。Vite 8.3 默认生产目标是 2026-01-01 的 Baseline Widely Available（广泛可用基线）浏览器范围；如果要支持更早的浏览器，应显式配置 `build.target` 并另行规划 API polyfill（应用程序接口兼容补丁）。`tsconfig.json` 的 `target` 不会设置 Vite 的构建目标。版本与目标细节见[怎样判断目标运行时是否支持 JavaScript 特性？](../javascript/modern-javascript-features.md)。

发布前应运行仓库锁定版本的正式 build 命令，检查生成目录里的页面资源地址、动态代码分块（chunk）、样式、图片和服务端路由，再由与生产相同的服务器预览产物。HMR 只覆盖开发循环；不同 `base` 路径、CDN、缓存头和服务器压缩配置都需要在真实部署路径确认。

## 新入口与带哈希代码分块怎样作为同一版本发布？

构建工具输出的是一组彼此引用的文件，不是可以单独替换的一个 JavaScript bundle。本例沿着页面编辑器的异步入口：构建 `v41` 生成入口 `main-a41.js` 和稍后通过动态 `import()` 加载的 `Editor-a41.js`；构建 `v42` 再生成 `main-b42.js` 与 `Editor-b42.js`。这些缩写名只是说明版本引用的合成示例；真实文件名由内容哈希产生。Vite 的 manifest（资源清单）可以映射源入口、静态依赖、异步依赖和最终哈希文件名；它描述构建关系，不会替部署系统原子切换入口或保证旧文件继续可用。

本例的构建脚本开启 Vite manifest：

~~~javascript
import { defineConfig } from "vite";

export default defineConfig({
  build: { manifest: true },
});
~~~

例如 `v41` 的 HTML 引用 `main-a41.js`，manifest 列出 `Editor-a41.js` 为动态入口。用户保持页面开启时，浏览器不会因服务器部署了 `v42` 自动替换已执行的入口代码；稍后用户展开编辑器，旧运行时仍请求 `Editor-a41.js`。如果发布过程已删除旧 chunk，这个动态导入会得到 `404`。若保留它，旧标签仍可按它最初取得的静态代码运行；服务端 API 的兼容性仍是另一项前提。

| 资源 | 本例中的版本身份 | 可用的缓存策略 |
|---|---|---|
| 顶层 `index.html` 或当前 release 指针 | 可变，选择本次应启动的入口版本 | `Cache-Control: no-cache` 以便复用前重新验证，或按平台策略缩短新鲜时间；回滚时要一起恢复 |
| 按 release 保存的 manifest | `v41` 与 `v42` 分开保存，发布后不覆盖 | 若 URL 含 release ID 且内容不可变，可长时间缓存；若使用同一可变 URL，则要与入口一起切换并重新验证 |
| `main-a41.js`、`Editor-a41.js` 等带内容哈希的资产 | 文件名绑定那次构建内容 | 只有发布端永不在同一路径改写内容时，才可长时间缓存并使用 `immutable` |

HTTP `no-cache` 允许保存响应，但在再次使用前要求验证；它不是 `no-store`。相反，`immutable` 只表示在新鲜期内表示不会改变，所以同一内容哈希路径不能被替换成另一份代码。入口、版本清单与运行时资产应配套：可以把每个构建放在版本目录下，再以一个小入口文件或原子指针选择版本；也可以用一次原子发布把 HTML 和清单切换到同一版本。不要让可变 manifest 已指向 `v42`、入口仍启动 `v41`，或发布脚本逐个覆盖正在使用的哈希路径。

安全的发布顺序是先将整套 `v42` 静态文件与版本化 manifest 上传到所有目标存储位置，再从源站和 CDN（内容分发网络）验证新入口、静态依赖及 `Editor-b42.js` 均可读取，随后才原子切换入口或 release 指针。切换后检查若干边缘节点看到的入口版本与它引用的清单一致；边缘节点仍返回旧 HTML 时，它引用的 `v41` 文件必须仍在。把当前入口清缓存不能替代保留旧动态 chunk。

Service Worker（服务工作线程）的 Cache Storage（缓存存储）是独立于 HTTP 缓存的另一层。若它缓存应用入口或 chunk，每个缓存版本应含完整、互相匹配的一套资产；新 worker 安装失败时，旧 worker 和旧缓存仍应可继续工作。激活 `v42` 时不要过早删除仍由打开标签页或回滚所需的 `v41` 资产，也不要让旧 worker 从一个版本缓存入口、再从另一个版本缓存动态模块。需结合应用自己的更新时机检查 Service Worker 命中、网络和 CDN 行为；开发服务器的刷新结果不能证明这些发布状态正确。

如果旧标签请求的异步 chunk 仍然 `404`，客户端捕获动态 `import()` 的加载失败，保留当前路由与尚未保存的编辑草稿，并告诉用户“页面代码已更新，可保存草稿后刷新”。刷新前要确认草稿已保存或由用户明确选择重载，且不能在每次失败时自动无限重载。如果没有记录当前页面的 release ID，也无法可靠地区分发布错配、网络断开和其它模块错误；界面可以统一提示可恢复动作，但不能把每种导入异常都谎报成旧版本错误。

回滚时将入口与 manifest 指针一起指回上一版本，仍保留 `v41` 与 `v42` 文件，再验证旧深链能加载旧入口、旧编辑器动态 chunk 和 API 表示。删除 `v42` 静态资产要等活跃标签、Service Worker、CDN 缓存与观测窗口都不再依赖它。若新版本已提交旧客户端无法读取的服务端字段或数据格式，单独把入口回滚到 v41 并不能恢复兼容；服务端接口需在并行窗口内接受旧、新客户端共享的数据契约，或为不兼容变更加版本化迁移。

这一套检查连接到[如何晋级并回滚已验证的应用产物](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)：构建版本、发布清单和静态入口作为一套明确的产物候选一起验证，而部署平台再决定逐步推广与恢复入口。

## Source map 怎样用于调试，又会暴露什么？

Source map（源映射）把压缩或转换后的代码位置映回源文件。Webpack 的 `devtool` 选择会影响首次构建与重建速度、映射精度、产物体积，以及映射文件如何关联到 bundle（打包文件）。

| 配置示例 | 主要含义 | 适用边界 |
|---|---|---|
| `eval-source-map` | 以 `eval` 逐模块关联高精度映射 | 开发调试常用；初次构建较慢 |
| `cheap-source-map` | 只映射行号且忽略 loader 产生的映射 | 列级断点不可用，转换后的源码细节可能丢失 |
| `cheap-module-source-map` | 吸收 loader 映射后简化到行级 | 精度和构建成本低于完整映射 |
| `source-map` | 输出外置完整映射并在 bundle 留引用 | 生产错误还原方便；服务器要控制 `.map` 访问 |
| `hidden-source-map` | 输出外置映射，但 bundle 不写引用注释 | 若供错误收集服务使用，应让发布流程单独上传且不公开托管 |
| `nosources-source-map` | 映射文件不内嵌源码文本 | 仍可能公开文件名和目录结构，并非源码访问控制 |

`inline-*` 把映射嵌入代码，页面访问者也会下载；`eval-*` 使用逐模块 `eval`；`cheap-*` 去掉列映射；`module-` 会考虑 loader 的 source map。Webpack 5.105 起 `devtool` 也支持按 JavaScript、CSS 或全部资源分别指定映射类型。完整组合和旧配置对照见[Webpack source map 预设归档](../../archive/front-end/Deprecated_Interview_Notes/webpack-source-map-presets.md)。

Source map 不是权限边界：映射路径可被公开请求时，部署和服务器配置决定其是否真的私有。发布前同时检查产物目录、服务器静态资源规则和错误收集服务的上传路径。

> [!info]- 来源
> - [Node.js 25 发布说明：Corepack 不再随 Node 分发](https://nodejs.org/en/blog/release/v25.0.0)、[Node.js 25.8 Corepack 文档](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html)
> - 当前原生 CSS/TypeScript 默认值、已有 loader 的优先级及类型擦除限制：[Webpack experiments.css](https://webpack.js.org/configuration/experiments/#experimentscss)、[experiments.typescript](https://webpack.js.org/configuration/experiments/#experimentstypescript)，5.109 起的默认行为，2026-11-06 核对。
> - [Webpack：loader 执行顺序](https://webpack.js.org/concepts/loaders/)、[Asset Modules](https://webpack.js.org/guides/asset-modules/)、[插件与 `processAssets`](https://webpack.js.org/concepts/plugins/)
> - [Webpack Compiler Hooks](https://webpack.js.org/api/compiler-hooks/)、[Webpack Writing a Plugin](https://webpack.js.org/contribute/writing-a-plugin/)
> - [Webpack：原生 HTML](https://webpack.js.org/guides/native-html/)、[Webpack `experiments.html` 默认值与规则优先级](https://webpack.js.org/configuration/experiments/#experimentshtml)、[HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme)、[Webpack `DefinePlugin`](https://webpack.js.org/plugins/define-plugin/)
> - [Webpack：`devtool`](https://webpack.js.org/configuration/devtool/)、[Webpack 5.105 source map 更新](https://webpack.js.org/blog/2026-02-03-webpack-5-105/)
> - [Vite 8 发布公告](https://vite.dev/blog/announcing-vite8)、[Vite 8.3 TypeScript 转译](https://vite.dev/guide/features.html#typescript)、[浏览器兼容](https://vite.dev/guide/build.html#browser-compatibility)
> - **manifest、入口、静态/动态 chunk 的构建映射：** [Vite 8.3.5 `build.manifest`](https://github.com/vitejs/vite/blob/v8.3.5/docs/config/build-options.md#buildmanifest) 与 [Backend Integration](https://github.com/vitejs/vite/blob/v8.3.5/docs/guide/backend-integration.md)，核对日期 2026-11-09。manifest 默认不生成；本例需显式 `build.manifest: true`。
> - **入口与不可变资源缓存：** [RFC 9111 HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，2022，§5.2 `Cache-Control` 与 `no-cache`；[RFC 8246 HTTP Immutable Responses](https://www.rfc-editor.org/rfc/rfc8246.html)，2017，`immutable` 仅对新鲜期内不变的表示生效。
> - **Service Worker 独立拦截请求与缓存版本：** [W3C Service Workers](https://www.w3.org/TR/service-workers/)；服务工作线程的当前规范状态依实现和浏览器版本而异，本文只依其请求拦截和 Cache Storage 模型说明发布边界。
>
> Webpack 的原生 HTML 默认值按官方文档中“自 5.109.0 起”的说明记录；Vite 目标按 8.3 文档记录。来源核对日期：2026-11-06。
