# 目录聚合导出怎样改变组件的导入路径？

这页保留旧课程的组件目录示例。barrel export（聚合导出）是指用目录下的 `index.ts` 把多个模块的导出集中重新导出，让调用方只从目录入口导入；它就是普通的 ECMAScript 模块 re-export，不是 React 的特有功能。当前模块语法、循环依赖和 tree shaking 的边界见[ECMAScript 模块与 CommonJS 有何不同？](../../../../frontend/javascript/modules-and-host-boundaries.md)。

~~~text
src/
├── App.tsx
├── components/
│   ├── header/
│   │   ├── Header.tsx
│   │   └── index.ts
│   ├── footer/
│   │   ├── Footer.tsx
│   │   └── index.ts
│   └── index.ts
~~~

`Header.tsx` 与 `Footer.tsx` 分别提供命名导出 `Header`、`Footer`。各级 `index.ts` 只把这些导出继续传给上层：

~~~typescript
// components/header/index.ts
export { Header } from "./Header";

// components/footer/index.ts
export { Footer } from "./Footer";

// components/index.ts
export { Header } from "./header";
export { Footer } from "./footer";
~~~

~~~tsx
// App.tsx
import { Header, Footer } from "./components";

export function App() {
  return (
    <>
      <Header />
      <main>报表内容</main>
      <Footer />
    </>
  );
}
~~~

本例的无扩展名导入和“导入目录即导入其 `index`”，都依赖项目的 TypeScript／打包器模块解析配置。浏览器原生 ESM 按 URL 加载模块：只要服务器返回正确的 JavaScript 内容和 MIME 类型，无扩展名的 URL 也能用。Node.js 原生 ESM 的相对文件导入则需要写明文件名及扩展名，例如 `./components/index.js`。浏览器和 Node.js 原生 ESM 都不会像打包器那样自动查找目录里的 `index` 文件。

集中入口可以让调用方不依赖更深的文件路径，但也会扩大该入口的公开面。目录内部实现通常直接导入具体模块，以免互相经由 index.ts 形成循环；包体能否裁掉未使用导出，取决于 ESM 依赖图与构建工具配置，不是“用了 index.ts”就能保证。

> [!info]- 来源
> - ESM 静态 re-export、依赖图与打包器副作用边界：[ECMAScript Modules](../../../../frontend/javascript/modules-and-host-boundaries.md)，ECMAScript 2026 规范及 Webpack 官方文档，核对日期：2026-11-06。
> - 原生模块的路径解析：[HTML Standard — Module specifier resolution](https://html.spec.whatwg.org/multipage/webappapis.html#resolve-a-module-specifier)、[Node.js — Mandatory file extensions](https://nodejs.org/api/esm.html#mandatory-file-extensions)，核对日期：2026-11-13。
