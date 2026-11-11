# Webpack 的源映射（source map）预设有哪些差异？

Source map（源映射）记录生成代码中的位置与原始源码位置之间的对应关系；它帮助调试器或错误收集工具把生成位置映回源码位置，不会逆向重建原始文件。Webpack 的 `devtool` 组合会影响构建速度、映射是行级还是行列级、是否纳入 loader（模块加载器）提供的位置对应、映射放在哪里，以及 bundle（打包文件）是否引用它。选项名称可辅助阅读，但不是统一的速度排名或安全等级。

| 预设 | 映射特点 | 输出或取舍 |
|---|---|---|
| `eval-source-map` | 每个模块的生成代码通过 `eval` 执行，并在该模块的注释中关联 data URL 映射；定位可包含行和列 | 完整定位适合开发调试；官方表把初次构建列为 slowest、重建列为 ok |
| `source-map` | 输出外部完整 `.map`，bundle 通常含 `sourceMappingURL` 引用 | 可供调试还原行列；`.map` 是否能被请求由服务器静态资源规则决定 |
| `inline-source-map` | 完整映射以 data URL 嵌入 bundle | 不需另发 `.map`；下载含该映射的 bundle 的人也会取得映射数据 |
| `cheap-source-map` | 只保留行级映射，忽略 loader 已提供的映射 | 不能定位行内列，位置可能停留在 loader 转换后的代码 |
| `cheap-module-source-map` | 使用可用的 loader 映射，再简化为行级位置 | 可映回转换前的位置，但不能定位行内列 |
| `eval-cheap-module-source-map` | 每个模块以 `eval` 关联行级映射，并使用 loader 映射 | 官方表把重建列为 fast，而 `eval-source-map` 为 ok；这是文档中的定性对比，不是本项目实测 |
| `hidden-source-map` | 输出外部映射，但 bundle 不写 `sourceMappingURL` 引用 | 可将 `.map` 单独上传到私有错误报告工具；公开静态目录若仍提供它，知道路径的人仍能请求 |
| `nosources-source-map` | 输出映射，但不内嵌 `sourcesContent` 源码文本 | 仍保留映射与源码文件名/路径；不是隐藏 `.map` 或访问权限控制 |

对表中这些常用预设，可以把 `inline-`、`eval-`、`hidden-`、`nosources-`、`cheap-` 和 `module-` 当作组合修饰语来读。`module-` 只在 `cheap-` 组合里表示采用 loader 映射；完整 `source-map` 本身就会使用可用的 loader 映射。`cheap-` 去掉列级定位，`cheap-module-` 仍是行级。Webpack 当前完整语法还包含 `-debugids` 等后缀，Webpack 5.112 也加入 `-scopes`；表中列的是八种常见预设，不是完整语法。组合是否可用及其顺序，应以项目锁定版本的 `devtool` 配置参考为准。

若某个 loader 改写代码但没有提供或传递该步的位置映射，后续 source map 就无法准确关联到更早源码；调试位置可能停留在转换后代码，或因 loader 链的映射不完整而降低精度。Source map 文件、其中的源码文本和服务器上的源文件路径是不同的暴露面：`hidden-source-map` 只去掉 bundle 引用；`nosources-source-map` 只去掉 `sourcesContent`，若 `.map` 公开，仍会暴露映射和路径，源文件本身若可请求也可能被调试器加载。发布前分别检查 map URL、`sourcesContent` 和源文件访问规则。

Webpack 5.105 起，`devtool` 也支持用数组分别为 JavaScript、CSS 或两者指定映射类型；这里的 `all` 指 JavaScript 与 CSS，不是任意图片、字体等资源。旧式字符串配置仍可用。构建主线对映射的发布边界见[Source map 怎样用于调试，又会暴露什么](../../../frontend/tooling/build-tools.md#source-map-怎样用于调试又会暴露什么)。

> [!info]- 来源
> - [Webpack `devtool` 配置参考](https://webpack.js.org/configuration/devtool/)：预设的映射质量、开发/生产取舍、`inline`/`eval`/`cheap`/`module`/`hidden`/`nosources` 语义及性能分类；完整语法按当前页面和锁定版本核对。
> - [Webpack 5.112.0 WebpackOptionsApply.js](https://github.com/webpack/webpack/blob/v5.112.0/lib/config/WebpackOptionsApply.js)：cheap/module/columns 的映射选项；[Webpack 5.112.0 eval source map 实现](https://github.com/webpack/webpack/blob/v5.112.0/lib/devtool/EvalSourceMapDevToolPlugin.js)说明模块代码与映射注释的 eval 形式；[SourceMapDevToolPlugin](https://github.com/webpack/webpack/blob/v5.112.0/lib/devtool/SourceMapDevToolPlugin.js) 说明外部 map、引用和 `sourcesContent`。
> - [Webpack 5.105：按资源类型配置 source map](https://webpack.js.org/blog/2026-02-03-webpack-5-105/)、[Webpack 5.112 scopes 发布说明](https://webpack.js.org/blog/2026-10-13-webpack-5-112/#debug-imports-by-their-original-names) 与 [v5.112.0 WebpackOptions.json](https://github.com/webpack/webpack/blob/v5.112.0/schemas/WebpackOptions.json)：分别核对 JavaScript/CSS 数组能力、新后缀和当前语法校验规则。
> - [ECMA-426 Source Map Format §§5–5.1](https://tc39.es/ecma426/2024/#sec-source-map-format) 与 [Webpack Loader Interface：`this.callback`](https://webpack.js.org/api/loaders/#thiscallback)：映射字段和 loader 传递位置对应的接口。
>
> 版本相关语法以 Webpack 5.112.0 的配置校验和当前 `devtool` 文档复核；核对日期：2026-11-11。性能表是官方定性分类，本轮没有执行构建或测量。
