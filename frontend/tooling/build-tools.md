# How do build tools transform modules and validate production output? / 构建工具如何转换模块并验证生产产物？

**Core answer / 核心回答：** A bundler follows a module graph, transforms selected modules, and emits assets. Loaders transform individual modules; plugins use broader compiler hooks. A successful development server does not prove that the production build has the same assets, paths, chunks, or source-map exposure. / 打包器沿模块图解析依赖、转换选定模块并输出资源。loader 转换单个模块；plugin 通过更广泛的 compiler hooks 扩展构建。开发服务器成功不代表生产构建具有相同资源、路径、分块或 source map 暴露方式。

~~~mermaid
flowchart LR
  A["Entry points"] --> B["Resolve module graph"]
  B --> C["Apply loaders / transforms"]
  C --> D["Compiler and plugin hooks"]
  D --> E["Emit production assets and maps"]
  E --> F["Serve and inspect built output"]
~~~

## Pin the toolchain before building / 构建前固定工具链

`package.json` can record a project’s package manager and version, for example `"packageManager": "pnpm@10.0.0"` in a project that has tested that version. Provision the pinned tool in both CI and local development, then install from the committed lockfile. The field describes the expected tool. Corepack’s installed shims can select it, but the field alone does not install a manager. Node.js distributed Corepack starting with the 14.19 and 16.9 release lines through Node 24 and dropped it from Node 25 onward. Provision Corepack separately or use the package manager's documented installer. / 声明工具版本后，CI 和本地还需要安装相同版本并按锁文件安装依赖。 [Corepack project README](https://github.com/nodejs/corepack#readme) · [Node.js 25 release](https://nodejs.org/en/blog/release/v25.0.0)

## How Webpack loaders and plugins differ / Webpack loader 与 plugin 有何不同

Webpack starts from configured entries, resolves their dependency graph, applies loaders to modules, and emits assets. Configuration names entry points, output, mode, module rules, plugins, and optimization. / Webpack 从配置的入口出发解析依赖图，对模块执行 loader，再输出资源。配置项包括 entry、output、mode、module rules、plugins 和 optimization。

| Term / 名称 | Role / 作用 |
|---|---|
| Entry | Starting point for dependency resolution / 依赖解析的起点 |
| Output | Destination and naming for emitted assets / 输出资源的目录和命名 |
| Loader | Transforms one module’s source before bundling / 打包前转换单个模块源码 |
| Plugin | Hooks into compiler or compilation stages for broader behavior / 通过 compiler 或 compilation 阶段扩展行为 |
| Mode | Enables development or production defaults; explicit settings may override / 启用开发或生产默认值；显式设置可覆盖 |

Normal loader functions run right to left. Pitch functions, when present, run left to right. / 普通 loader 函数从右向左执行；若有 pitch 函数，则从左向右执行。

~~~javascript
module: {
  rules: [
    {
      test: /\.tsx?$/,
      use: ["babel-loader", "ts-loader"]
    },
    {
      test: /\.scss$/,
      use: ["style-loader", "css-loader", "sass-loader"]
    }
  ]
}
~~~

For the TypeScript rule, ts-loader runs first and its output goes to babel-loader. Choose one clear TypeScript transform pipeline; overlapping transforms can add cost or change output unexpectedly. / TypeScript 规则中 ts-loader 先运行，其输出再交给 babel-loader。应选择清晰的 TypeScript 转换链；重叠转换可能增加成本或意外改变产物。

Common loader roles include JS/TS transforms, style processing, and static assets. Webpack 5 Asset Modules can emit or inline assets without older file-loader/url-loader setups. The exact loader stack depends on the project. / 常见 loader 用于 JS/TS 转换、样式处理和静态资源。Webpack 5 Asset Modules 可直接输出或内联资源，不必沿用旧式 file-loader/url-loader 配置。具体链路取决于项目需求。

A text replacement loader illustrates the loader shape, but it does not parse JavaScript syntax. Use a syntax-aware transform when source structure matters. / 字符串替换示例说明 loader 形式，但不会解析 JavaScript 语法；源码结构重要时应使用语法感知的转换器。

~~~javascript
module.exports = function replaceBuildLabel(source) {
  return source.replaceAll("__BUILD_LABEL__", "demo");
};
~~~

A plugin can subscribe to compiler hooks. The done hook runs after compilation and is an AsyncSeriesHook; synchronous handlers can use tap, while asynchronous handlers can use tapAsync or tapPromise so the hook waits for their work. / plugin 可订阅 compiler hooks。done hook 在编译结束后运行，是 AsyncSeriesHook；同步处理器可用 tap，异步处理器可用 tapAsync 或 tapPromise，以便 hook 等待其工作。

~~~javascript
class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tap("BuildStatsPlugin", stats => {
      const json = stats.toJson({ modules: false });
      require("node:fs").writeFileSync(
        "build-stats.json",
        JSON.stringify(json, null, 2)
      );
    });
  }
}
~~~

Example plugins have distinct roles: HtmlWebpackPlugin can generate HTML and inject emitted assets; DefinePlugin replaces configured expressions at compile time rather than reading a browser runtime environment variable; MiniCssExtractPlugin can emit CSS files. They are examples, not a required stack. As of the Webpack docs checked on 2026-10-15, the HtmlWebpackPlugin README marks it deprecated while the native HTML guide describes experiments.html and output.html as alternatives and still labels native HTML experimental. Check installed Webpack version and template needs before migrating. / 插件示例作用不同：HtmlWebpackPlugin 可生成 HTML 并注入输出资源；DefinePlugin 在编译时替换配置表达式，不会读取浏览器运行时环境变量；MiniCssExtractPlugin 可把 CSS 输出为独立文件。它们只是示例，不是必需组合。根据 2026-10-15 核对的 Webpack 文档，HtmlWebpackPlugin README 标记已弃用；原生 HTML 指南介绍 experiments.html 与 output.html 作为替代方案，同时仍标为实验性。迁移前应检查所用 Webpack 版本和模板需求。

Sources checked 2026-10-15: [Webpack Loaders](https://webpack.js.org/concepts/loaders/), [Asset Modules](https://webpack.js.org/guides/asset-modules/), [Webpack Plugins](https://webpack.js.org/concepts/plugins/), [DefinePlugin](https://webpack.js.org/plugins/define-plugin/), [HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme), [Webpack Native HTML guide](https://webpack.js.org/guides/native-html/), [style-loader](https://github.com/webpack/style-loader#readme), [css-loader](https://github.com/webpack-contrib/css-loader#readme), [MiniCssExtractPlugin](https://github.com/webpack/mini-css-extract-plugin#readme), [Webpack: Writing a Plugin](https://webpack.js.org/contribute/writing-a-plugin/), [Compiler hooks](https://webpack.js.org/api/compiler-hooks/).

## Why Vite development and production need separate checks / 为什么 Vite 开发与生产需要分别检查

The standard Vite development path serves native ES modules with on-demand transforms and HMR. Vite 8 uses Rolldown for production builds. Check the project's selected development mode and production settings when diagnosing differences. / Vite 的常规开发路径用原生 ES 模块、按需转换和 HMR 提供资源。Vite 8 的生产构建使用 Rolldown。排查差异时看该项目选用的开发模式和生产配置。

A fast development server is not evidence that production output has the same graph or performance. Run the configured production build and inspect its generated assets. For release verification, serve the generated output and check actual paths and chunks; HMR only validates the development loop. / 开发服务器速度快并不能证明生产产物具有相同依赖图或性能。应运行配置的生产构建并检查输出资源。发布验证要服务生成的产物并检查实际路径和分块；HMR 只验证开发循环。

Sources checked 2026-10-15: [Vite 8 guide](https://vite.dev/guide/) and [Vite 8.0.10 source](https://github.com/vitejs/vite/blob/v8.0.10/README.md).

## What a source map exposes / Source map 会暴露什么

A source map relates emitted code to source files for debugging and error reporting. Choose Webpack devtool by rebuild speed, trace detail, artifact size, and whether the map is published. A privately uploaded map can still be exposed if deployment serves it publicly; configuration alone does not define access policy. / source map 将输出代码关联回源文件，用于调试和错误报告。选择 Webpack devtool 时要看重建速度、追踪细节、产物大小和是否公开 map。私下上传的 map 若部署时能被公开访问，仍可能暴露；配置本身不等于访问策略。

| devtool example | Output meaning / 输出含义 |
|---|---|
| eval-source-map | Evaluates modules with source maps for development debugging / 开发调试用 eval 与 source map |
| source-map | Emits an external map with a sourceMappingURL reference / 输出外部 map 并带 sourceMappingURL 引用 |
| hidden-source-map | Emits an external map without the reference comment; useful when a release process uploads maps separately / 输出外部 map 但无引用注释；适合由发布流程单独上传 |
| nosources-source-map | Omits embedded source content, but mappings and source paths may remain / 不嵌入源码内容，但映射和源码路径仍可能存在 |

These names represent different detail and delivery choices, not a universal speed ranking or security boundary. See [Webpack devtool configuration](https://webpack.js.org/configuration/devtool/). Release mapping and access control belong to the release process; see [Frontend Testing / 前端测试](../testing/frontend-testing.md) for built-output browser smoke checks and [Application Deployment and CI/CD / 应用部署与持续交付](../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) for the shared release path.
