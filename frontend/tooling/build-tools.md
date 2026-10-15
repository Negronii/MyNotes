# Build Tools / 构建工具

Build tools resolve modules, transform source files, and produce output for development or deployment. The exact pipeline depends on the tool and version.

**Core answer / 核心回答：** A bundler follows the module graph, transforms selected modules, and emits assets; loaders transform modules while plugins use broader compiler hooks. / 打包器沿模块依赖图处理文件、转换选定模块并输出资源；loader 转换模块，plugin 则可通过更广泛的 compiler hooks 扩展构建过程。

## Webpack concepts / Webpack核心概念

Webpack starts from configured entries, resolves their dependency graph, applies loaders to modules, and emits assets. Its configuration names entry points, output, mode, module rules, plugins, and optimization.

| Term | Role |
|---|---|
| Entry | Starting point for dependency resolution. |
| Output | Destination and naming for emitted assets. |
| Loader | Transforms one module's source before bundling. |
| Plugin | Hooks into compiler or compilation stages to add broader build behavior. |
| Mode | Enables development or production defaults; explicit settings can override them. |

### Loader order / Loader执行顺序

Normal loader functions execute right to left. Pitch functions, when present, run left to right.

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

For the TypeScript rule, ts-loader runs first and its output is then passed to babel-loader. A real project should choose one clear TypeScript transform pipeline; running overlapping transforms can add cost or change output unexpectedly.

| Common loader role | Examples | Typical work |
|---|---|---|
| JavaScript or TypeScript transform | babel-loader, ts-loader | Transpile syntax or TypeScript according to the configured toolchain. |
| Styles | sass-loader, css-loader, style-loader | Compile Sass, resolve CSS imports and URLs, then inject styles in a development page. Production builds may extract CSS into files. |
| Static assets | Webpack 5 Asset Modules | Emit or inline resources using built-in module types instead of older file-loader or url-loader setups. |

### Loader and plugin examples / Loader与插件示例

A small text replacement shows the loader shape. It is not a JavaScript parser; use a syntax-aware transform when source structure matters.

~~~javascript
module.exports = function replaceBuildLabel(source) {
  return source.replaceAll("__BUILD_LABEL__", "demo");
};
~~~

A plugin can subscribe to a compiler hook. The done hook runs after compilation and is an AsyncSeriesHook. A synchronous handler may register with tap; asynchronous handlers may use tapAsync or tapPromise so the hook waits for their work.

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

Production plugins should write to an explicit destination and handle concurrent or watch builds deliberately; the example is a minimal local illustration.

| Plugin | Typical role |
|---|---|
| HtmlWebpackPlugin | Generates an HTML document and injects emitted script or stylesheet references. |
| DefinePlugin | Replaces configured expressions at compile time; it does not read a runtime environment variable from the browser. |
| MiniCssExtractPlugin | Emits CSS into separate files when the build needs extracted styles. |

These are examples, not a required plugin stack; a framework may provide equivalent build features. As of the Webpack docs checked on 2026-10-15, the HtmlWebpackPlugin README marks it deprecated; the native HTML guide describes experiments.html and output.html as alternatives for generated pages, and still labels native HTML experimental. Check the installed Webpack version and template needs before migrating.

### Source maps / Source map

A source map relates emitted code to source files for debugging and error reporting. Select devtool based on rebuild speed, trace detail, artifact size, and whether the map is published. A map that is uploaded privately can still be exposed if the deployment serves it publicly; configuration alone does not set the access policy.

| devtool example | Output meaning |
|---|---|
| eval-source-map | Evaluates modules with source maps for development debugging. |
| source-map | Emits an external map with a sourceMappingURL reference. |
| hidden-source-map | Emits an external map without the reference comment; useful when a release pipeline uploads maps separately. |
| nosources-source-map | Omits embedded source content, but mappings and source paths may still be present. |

These names describe different map delivery and detail choices; compare the configured output rather than treating them as a fixed speed ranking or a security boundary.

## Vite and the development/production split / Vite与开发、生产构建的区别

Vite's development server serves native ES modules with on-demand transforms and HMR. In Vite 8, the production build uses Rolldown to produce optimized assets. Earlier Vite releases used a different production bundler pipeline, so state the major version when the distinction matters.

A fast dev server is not evidence that the production output has the same graph or performance. Run the configured production build and inspect its assets when validating deployment behavior.

## Corepack and package-manager pinning / Corepack与包管理器版本固定

A package.json packageManager field records the package manager and version a project expects. Corepack can use that field to select a matching manager when its shims are installed. Corepack was bundled with Node.js through Node 24, but Node 25 and later no longer distribute it by default; a current project may need to install or provision Corepack separately.

~~~json
{
  "packageManager": "pnpm@10.0.0"
}
~~~

The field alone does not install a package manager or guarantee that every environment honors it. Pin and provision the tool through the project's supported runtime and CI setup.

**Choosing a tool / 工具选择：** Compare plugin and loader needs, ecosystem, output constraints, team familiarity, and build behavior for the project. No single bundler is the right choice for every application or library.

**See also:** [Modern JavaScript Features / 现代JavaScript特性](../javascript/modern-javascript-features.md) for modules and dynamic imports; [Performance Metrics and Analysis / 性能指标与分析](../performance/performance-metrics-and-analysis.md) for measuring bundle and load behavior.

**Sources checked 2026-10-15:** [Webpack: Loaders](https://webpack.js.org/concepts/loaders/), [Asset Modules](https://webpack.js.org/guides/asset-modules/), [Webpack: Plugins](https://webpack.js.org/concepts/plugins/), [DefinePlugin](https://webpack.js.org/plugins/define-plugin/), [HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme), [Webpack Native HTML guide](https://webpack.js.org/guides/native-html/), [style-loader](https://github.com/webpack/style-loader#readme), [css-loader](https://github.com/webpack/css-loader#readme), [MiniCssExtractPlugin](https://github.com/webpack/mini-css-extract-plugin#readme), [Webpack: Writing a Plugin](https://webpack.js.org/contribute/writing-a-plugin/), [Webpack Compiler Hooks](https://webpack.js.org/api/compiler-hooks/), [Webpack devtool](https://webpack.js.org/configuration/devtool/), [Vite 8 guide](https://vite.dev/guide/), [Vite 8.0.10 source](https://github.com/vitejs/vite/blob/v8.0.10/README.md), [Node.js 25 Corepack docs](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html), [Corepack project README](https://github.com/nodejs/corepack#readme).
