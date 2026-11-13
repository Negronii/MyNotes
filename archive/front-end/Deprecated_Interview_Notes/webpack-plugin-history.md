# 常见 Webpack 插件分别改变哪一步构建行为？

Webpack plugin（插件）通过 compiler（编译器）或 compilation（单次编译）的生命周期钩子扩展构建。下表按构建阶段或运行边界速查旧配置；实际判断要核对项目锁定的 Webpack 完整版本（例如 5.109.0）和对应插件版本，主版本号不足以区分这里的原生能力。

| 插件 | 构建阶段或系统边界 | 常见作用 | 配置前要确认 |
|---|---|---|---|
| Html<wbr>Webpack<wbr>Plugin | compilation 生成页面时 | 生成 HTML 并写入输出 bundle（打包文件）的引用 | 插件 README 已标记弃用；原生 HTML `auto` 的探测和逐模块处理见表后说明。既有模板选项需按具体迁移目标核对 |
| MiniCss<wbr>Extract<wbr>Plugin | CSS 模块处理与页面资源输出 | 将 CSS 提取为独立文件 | Webpack 5.109.0 起原生 CSS 已稳定；该插件及常见 CSS loader 被原生指南标记为弃用。Sass、Less、Stylus、PostCSS 等预处理仍可能需要对应 loader |
| DefinePlugin | 编译期解析代码表达式 | 编译时替换指定表达式 | 写进客户端代码的值会暴露给用户；不能放服务端密钥，也不等于读取浏览器运行时环境变量 |
| minimizer-webpack-plugin（旧名 terser-webpack-plugin） | production optimization 的压缩阶段 | 最小化 JavaScript；默认 JavaScript 实现仍是 Terser | Webpack 5.109 默认已用新包；一般无需额外重复添加。自定义 `optimization.minimizer` 时，用 `"..."` 才保留默认 minimizer |
| Compression<wbr>Webpack<wbr>Plugin | 构建输出的压缩资源生成阶段 | 生成 gzip 或 Brotli 副本 | 该插件现已弃用并归档。迁移表把压缩生成器放入 `minimizer-webpack-plugin`；迁移项从其 5.11.0 起适用。构建出副本仍不表示服务器会返回它；还要核对内容协商和资源路径 |
| HotModule<wbr>Replacement<wbr>Plugin（热模块替换插件） | 监听编译、更新产物与浏览器运行期 | 编译端生成更新资源；浏览器端热模块替换（Hot Module Replacement，HMR）客户端检查并应用模块接受的更新，避免整页刷新 | 官方警告不要用于生产；它不负责生产缓存或发布版本切换 |
| ProvidePlugin | 模块解析时形成依赖 | 源码遇到配置指定的自由标识符（没有局部绑定）时，自动引入其对应模块或导出 | 可能隐藏文件的实际依赖，降低可读性和依赖追踪清晰度 |
| DllPlugin / Dll<wbr>Reference<wbr>Plugin | 两次分开的 Webpack compilation | `DllPlugin` 在单独配置中生成 DLL bundle 与 manifest；应用编译中的 `DllReferencePlugin` 再读取 manifest 并复用其中依赖 | 较早的跨编译共享 bundle 工作流；官方称文件系统缓存已大体替代其缩短应用编译时间的用途。保留前先测量项目收益 |

Webpack 5.109 的 `auto` 先用 `/file.html`、`/file.css` 或 `/file.module.css` 等合成路径做宽松的构建级探测：`test`、`resource`、`include` 任一条件可命中便计入（忽略 `exclude`），显式 `type` 或未设 `enforce` 的普通 `loader/use` 才会关闭该构建对应的原生处理。探测不等于真实资源的完整规则匹配；若 `auto` 保持开启，它还会逐模块让已应用 loader、且未显式改用其他类型的请求沿原有解析路径，因此不能据此认定所有未命中实际规则的 HTML 都由原生接管，`HtmlWebpackPlugin` 注入的请求也须按具体配置判断。

自定义插件要增加或修改 compilation 资源时，使用 `compilation.hooks.processAssets` 并按工作选择 stage。新增文件通常放 `ADDITIONAL`，可让后续已注册且匹配该资源的 stage 有机会处理；它不会自动获得压缩、source map 或内容哈希。是否处理仍取决于后续插件的配置、资源类型和元数据。`REPORT` 晚于体积优化、source map、内容哈希与传输优化。

在 Webpack 5.109.0 中，`compiler.hooks.emit` 在 compilation 封存、所有 `processAssets` stage 结束后、资源交给配置的输出系统前运行。默认 `experiments.futureDefaults: false`（因而 `experiments.backCompat: true`）时，此后写入 `Compilation.assets` 会触发弃用警告；关闭 backCompat 后，封存的资源对象会被冻结，写入会被拒绝。无论哪种模式，修改都会错过已经结束的资源处理阶段；较晚运行的 `emit` tap 仍可看到较早 tap 的修改。输出完成后 `afterEmit` 仍会收到 compilation，但那不意味着钩子里的修改会回写已输出资源。`emit` 生命周期钩子本身没有整体弃用：读取已有资源仍可用；需要写入或变换的资源应提前放进 `processAssets`。

Webpack 的 loader、plugin 与资源处理边界见[构建工具中的 loader 与 plugin 分别处理什么](../../../frontend/tooling/build-tools.md#Webpack%20%E7%9A%84%E6%A8%A1%E5%9D%97%E5%8A%A0%E8%BD%BD%E5%99%A8%E4%B8%8E%E6%8F%92%E4%BB%B6%E5%88%86%E5%88%AB%E5%A4%84%E7%90%86%E4%BB%80%E4%B9%88%EF%BC%9F)。source map 的完整选项差异保留在[Webpack source map 预设对照](./webpack-source-map-presets.md)。

> [!info]- 来源
> - `processAssets` 与 stage 顺序：[Compilation Hooks](https://webpack.js.org/api/compilation-hooks/#choosing-a-stage)。默认 backCompat 下封存资源的写入警告、关闭后冻结：[Webpack 5.109.0 defaults.js backCompat default](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L623), [CSS auto rule probe](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L649-L669)、[Compilation.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compilation.js)。emit/afterEmit 及输出顺序：[Compiler Hooks](https://webpack.js.org/api/compiler-hooks/#emit)、[Webpack 5.109.0 Compiler.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/Compiler.js)。核对日期：2026-11-11。
> - [Webpack 原生 HTML](https://webpack.js.org/guides/native-html/) 与 [原生 CSS](https://webpack.js.org/guides/native-css/)：5.109.0 默认 `auto`、HTML/CSS 规则优先关系和迁移边界；[HtmlWebpackPlugin README](https://github.com/jantimon/html-webpack-plugin#readme) 标记弃用。Webpack 5.109.0 [defaults.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js#L655-L673) 使用合成路径探测，[RuleSetCompiler](https://github.com/webpack/webpack/blob/v5.109.0/lib/rules/RuleSetCompiler.js#L473-L501) 是宽松规则检查；[implicitTypeLoaderFallback.js](https://github.com/webpack/webpack/blob/v5.109.0/lib/util/implicitTypeLoaderFallback.js#L13-L19) 核对已应用 loader 的逐模块回退。该版本源码与官方指南核对日期：2026-11-11。
> - [ProvidePlugin](https://webpack.js.org/plugins/provide-plugin/)、[DllPlugin 与 DllReferencePlugin](https://webpack.js.org/plugins/dll-plugin/#usage)、[Webpack 插件列表](https://webpack.js.org/plugins/)、[构建性能指南的 DLL 部分](https://webpack.js.org/guides/build-performance/#dlls)：分别核对自由标识符触发条件、分开的两次配置/manifest 工作流和文件系统缓存的替代范围。
> - [DefinePlugin](https://webpack.js.org/plugins/define-plugin/)；[HMR guide](https://webpack.js.org/guides/hot-module-replacement/) 说明监听编译产生更新产物、客户端检查/应用更新，并警告 HMR 不用于生产；[HotModuleReplacementPlugin](https://webpack.js.org/plugins/hot-module-replacement-plugin/) 是启用插件。最小化证据：[MinimizerWebpackPlugin](https://webpack.js.org/plugins/minimizer-webpack-plugin/)、[v5.6.0 更名说明](https://github.com/webpack/minimizer-webpack-plugin/releases/tag/v5.6.0) 与 [v5.109.0 默认优化配置](https://github.com/webpack/webpack/blob/v5.109.0/lib/config/defaults.js)。
> - [CompressionWebpackPlugin 当前 README 与迁移说明](https://github.com/webpack/compression-webpack-plugin#readme)：该插件已弃用，迁移至 `minimizer-webpack-plugin` 的压缩生成器，迁移选项从 5.11.0 起适用；仓库于 2026-09-19 归档。核对日期：2026-11-11。
