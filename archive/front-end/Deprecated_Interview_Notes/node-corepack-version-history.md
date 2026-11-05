# When did Node.js bundle Corepack, and when was it removed? / Node.js 何时捆绑 Corepack，又何时移除？

Corepack was bundled with some Node.js distributions starting in Node 14.19 and 16.9, but Node.js 25 no longer distributes it. The packageManager field records a project's expected manager/version; it does not install that manager or guarantee every environment honors the field. / 从 Node 14.19 和 16.9 起，部分 Node.js 发行包曾捆绑 Corepack；Node.js 25 起不再分发它。packageManager 字段记录项目预期的包管理器及版本，但不会自行安装该工具，也不保证所有环境都会遵守此字段。

For Node 25 or later, provision Corepack separately or use the package manager's documented setup. Check the Node.js distribution and CI image rather than assuming corepack enable is available. The maintained [Build Tools](../../../frontend/tooling/build-tools.md) note covers the current Node 24/25 boundary and project pinning.

**Versioned source checked 2026-10-15:** [Node.js v25 Corepack documentation](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html) and [Corepack project README](https://github.com/nodejs/corepack#readme).
