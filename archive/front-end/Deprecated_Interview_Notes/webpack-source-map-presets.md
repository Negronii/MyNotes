# How do Webpack source-map presets differ? / Webpack Source Map 预设有何区别？

Webpack's devtool choice trades rebuild speed, mapping detail, output size, and source exposure. There is no universal fastest or safest preset; choose for the debugging workflow and keep any private map off public hosting. / Webpack 的 devtool 选择需要权衡重建速度、映射细节、产物大小和源码暴露；不存在普遍最快或最安全的预设，应按调试流程选择，并确保私有 map 不被公开托管。

| Option | Distinctive behavior |
|---|---|
| eval-source-map | Evaluates modules and provides detailed mappings; a development trade-off with larger output. |
| source-map | Emits a detailed external map normally referenced by the bundle. |
| inline-source-map | Embeds the map as a data URL in generated output. |
| cheap-source-map | Keeps line-level mappings but omits columns and loader-generated maps. |
| cheap-module-source-map | Includes loader maps simplified to line-level mappings. |
| eval-cheap-module-source-map | Evaluates modules and includes simplified loader maps; not a universal speed ranking. |
| hidden-source-map | Emits a map without a public reference; keep it off public hosting and upload it privately if needed. |
| nosources-source-map | Omits sourcesContent but can still expose filenames and project structure. |

Loader-generated maps need to be passed through for useful original-source traces. A source map is not access control: a public map containing source content makes that content public. See the maintained [Build Tools](../../../frontend/tooling/build-tools.md) note for current production-build checks and the installed Webpack version's [devtool documentation](https://webpack.js.org/configuration/devtool/).
