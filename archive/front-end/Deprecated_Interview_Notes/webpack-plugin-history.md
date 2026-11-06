# 常见 Webpack 插件分别改变哪一步构建行为？

Webpack plugin（插件）通过 compiler（编译器）或 compilation（单次编译）的生命周期钩子扩展构建。插件名只说明一种能力，不代表它适合当前版本、每个构建阶段或生产服务器。下面保留旧稿中的插件目录，作为查角色与边界的速查；实际新增配置前应核对项目安装的 Webpack 主版本和构建目标。

| 插件 | 常见作用 | 配置前要确认的边界 |
|---|---|---|
| HtmlWebpackPlugin | 生成 HTML 并注入输出 bundle（打包文件）引用 | 仓库 README 当前标记 deprecated（弃用）；Webpack 5.109 起原生 HTML 的 `experiments.html` 默认是 `"auto"`。旧配置仍可用，迁移前要核对原生 HTML 功能和模板需求 |
| MiniCssExtractPlugin | 将 CSS 输出成独立文件 | 页面部署和缓存策略还要正确提供生成的 CSS |
| DefinePlugin | 编译时替换指定表达式 | 写入客户端代码的值会暴露给用户；不能放服务端密钥，也不等于读取运行时环境变量 |
| TerserWebpackPlugin | 压缩 JavaScript | 生产优化已经启用默认 minimizer 时，通常不需要重复增加；自定义 minimizer 时再检查选项 |
| CompressionWebpackPlugin | 生成 gzip 或 Brotli 文件 | 生成压缩副本不等于服务器会选择并返回它；还要配置编码协商和资源路径 |
| HotModuleReplacementPlugin（热模块替换插件） | 开发时热替换模块 | 用于开发循环，不负责生产缓存或发布版本切换 |
| ProvidePlugin | 为匹配到的模块自动插入隐式导入 | 会隐藏文件实际依赖，可能降低可读性和依赖追踪清晰度 |
| DllPlugin / DllReferencePlugin | 构建后复用预构建的共享依赖包 | 属于较早的共享 bundle 工作流；是否有收益要基于当前缓存、包管理和构建测量 |

plugin 可以观察整个编译，也可以在单次 compilation 中添加或修改资源。当前 Webpack 指南要求资源写入用 `processAssets` 阶段钩子，让后续压缩、source map（源映射）与哈希处理仍能看到产物。弃用警告针对在 `compiler.hooks.emit` 阶段添加或修改 compilation 资源：此时 compilation 已封存，产物会错过后续处理；读取已有资源仍可在该阶段进行，`emit` 生命周期钩子本身并未整体弃用。

现行 loader、plugin、Asset Modules 和生产产物检查见[构建工具怎样把源码变成可发布产物？](../../../frontend/tooling/build-tools.md)。source map 的完整选项差异保留在[Webpack source map 预设对照](./webpack-source-map-presets.md)。

> [!info]- 来源
> - [Webpack 插件概念与 `processAssets`](https://webpack.js.org/concepts/plugins/)、[Webpack Plugin API](https://webpack.js.org/api/plugins/)
> - [Webpack 原生 HTML 指南](https://webpack.js.org/guides/native-html/)
> - [HtmlWebpackPlugin README 与弃用说明](https://github.com/jantimon/html-webpack-plugin#readme)
> - [Webpack 默认插件列表](https://webpack.js.org/plugins/)、[生产模式与 optimization](https://webpack.js.org/configuration/optimization/)
>
> Webpack 原生 HTML 的自动模式按官方文档注明的 5.109.0 版本起记录；状态核对日期：2026-11-06。
