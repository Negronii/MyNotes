# What do legacy Webpack plugins do, and what do they not configure? / 历史 Webpack 插件做什么，又不会配置什么？

Webpack plugins extend compiler or compilation behavior through hooks; their names are not proof that a task is performed at every build stage. Some common catalog entries are specific to development, some are older workflows, and generated compressed files still require matching server configuration. / Webpack plugin 通过 hook 扩展 compiler 或 compilation 行为；插件名称不代表它会在每个构建阶段执行。常见目录条目中有些仅用于开发，有些属于较旧流程；生成压缩文件也仍需服务器配置配合。

| Plugin | Archived role | Version or deployment note |
|---|---|---|
| HtmlWebpackPlugin | Generates HTML and injects bundle references. | Check its current maintenance status and Webpack version; the maintained Build Tools note covers the current documented alternative boundary. |
| MiniCssExtractPlugin | Emits CSS into separate files. | Production delivery still needs the emitted files served correctly. |
| DefinePlugin | Replaces configured expressions at build time. | It does not read a browser runtime environment variable. |
| TerserWebpackPlugin | Minimizes JavaScript. | Confirm the build's optimization configuration before adding it explicitly. |
| CompressionWebpackPlugin | Produces gzip/Brotli assets. | Emitting an asset does not configure the origin server to select and serve it. |
| HotModuleReplacementPlugin | Supports development hot updates. | It is a development workflow feature, not a production cache strategy. |
| ProvidePlugin | Adds configured implicit imports. | Hidden imports can make module dependencies harder to see. |
| DllPlugin / DllReferencePlugin | Reuses a prebuilt vendor bundle. | This is an older workflow; measure whether it still helps the installed toolchain. |

Choose a plugin only for a needed build behavior, and verify the emitted artifacts and serving path. See [Build Tools](../../../frontend/tooling/build-tools.md) for current loader/plugin examples and production-output checks.

**Source / 来源:** Webpack documentation links preserved in [the maintained Build Tools note](../../../frontend/tooling/build-tools.md).
