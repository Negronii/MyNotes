# Webpack 的源映射（source map）预设有哪些差异？

Webpack 的 `devtool` 组合会影响构建速度、映射粒度、是否还原 loader（模块加载器）变换、映射文件放在哪里，以及 bundle（打包文件）是否引用它。选项名称可按前缀理解，但不能把它们当成统一的速度排名或安全等级。

| 预设 | 映射特点 | 输出或取舍 |
|---|---|---|
| `eval-source-map` | 每个模块使用 `eval` 承载高精度映射；通常可显示原始代码 | 开发调试体验较好；初次构建成本较高 |
| `source-map` | 外部完整映射，bundle 通常含引用注释 | 文件较大，调试精度高；若 `.map` 公开，请求者可以读取 |
| `inline-source-map` | 完整映射以 data URL（数据 URL）嵌入 bundle | 不需单独请求 `.map`，但每个访问者都会下载映射 |
| `cheap-source-map` | 只保留行级映射，不处理 loader 已生成的映射 | 不能定位到行内列，也可能只显示转换后的源码 |
| `cheap-module-source-map` | 使用 loader 映射再压到行级 | 比较容易回到转换前代码，但行内列信息丢失 |
| `eval-cheap-module-source-map` | `eval` 逐模块承载行级映射，并处理 loader 映射 | 常见开发折中，重建快于完整映射但精度较低 |
| `hidden-source-map` | 输出外部映射，但 bundle 不加引用注释 | 常用于错误收集；映射文件必须单独上传且不要部署到公开 Web 根目录 |
| `nosources-source-map` | 输出映射但不内嵌 `sourcesContent` | 仍可能泄露文件名和目录结构，不等于隐藏文件或权限控制 |

前缀会组合改变行为：`inline-` 把映射嵌入 bundle，`eval-` 用逐模块 `eval`，`hidden-` 不加 sourceMappingURL 引用，`nosources-` 不放源代码文本，`cheap-` 去掉列映射，`module-` 纳入 loader 映射。Webpack 文档给出的名称顺序是 `[inline-|hidden-|eval-][nosources-][cheap-[module-]]source-map`；组合是否被当前版本接受，以该版本配置参考为准。

Loader 若改写代码却没有返回对应 source map，后续映射会把错误位置当作原始位置。Webpack 5.105 起 `devtool` 可用数组为 JavaScript、CSS 或所有资源分别指定映射方式；旧式字符串仍支持。部署 source map 时，检查是否包含 `sourcesContent`、公开文件路径和服务器静态资源规则。`hidden-source-map` 只是移除 bundle 引用，不会阻止猜到文件名后直接请求。

构建主线对映射的发布边界见[构建工具怎样把源码变成可发布产物？](../../../frontend/tooling/build-tools.md)。

> [!info]- 来源
> - [Webpack `devtool` 配置参考](https://webpack.js.org/configuration/devtool/)
> - [Webpack loader source map 行为](https://webpack.js.org/concepts/loaders/)、[Webpack 5.105：按资源类型配置 source map](https://webpack.js.org/blog/2026-02-03-webpack-5-105/)
>
> 原稿八种预设均保留，并依据 Webpack 当前文档复核差异；核对日期：2026-11-06。
