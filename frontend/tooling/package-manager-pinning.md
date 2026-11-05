# How does a project pin its package-manager version? / 项目如何固定包管理器版本？

**Core answer / 核心回答：** The package.json packageManager field records the package manager and version expected by a project. Corepack can select a matching version when its shims are installed, but the field does not itself install the manager or guarantee every environment honors it. / package.json 的 packageManager 字段记录项目期望使用的包管理器及版本。安装 Corepack shims 后，Corepack 可选择匹配版本；但该字段本身不会安装包管理器，也不保证每个环境都会遵循它。

~~~json
{
  "packageManager": "pnpm@10.0.0"
}
~~~

Corepack was bundled with Node.js through Node 24, but Node 25 and later no longer distribute it by default. A current project may need to install or provision Corepack separately. Pin and provision the tool through the project’s supported runtime and CI setup. / Corepack 随 Node.js 提供至 Node 24；Node 25 及之后的版本默认不再分发。当前项目可能需要单独安装或供应 Corepack。应通过项目支持的运行时和 CI 配置固定并供应工具。

Sources checked 2026-10-15: [Node.js 25 Corepack documentation](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html) and [Corepack project README](https://github.com/nodejs/corepack#readme). The rest of the build pipeline is in [Build Tools / 构建工具](./build-tools.md).
