# 目录聚合导出怎样改变组件的导入路径？

这页保留旧课程的组件目录示例；聚合导出本质上是普通 ECMAScript 模块的重新导出，不是 React 特有功能。当前模块语法、循环依赖和 tree shaking 的边界见[ECMAScript 模块与 CommonJS 有何不同？](../../../../frontend/javascript/modules-and-host-boundaries.md)。

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

本例的无扩展名导入和目录入口由项目的 TypeScript／bundler 模块解析配置处理。直接运行浏览器原生 ESM 或 Node.js ESM 时，应写出对应宿主可解析的文件路径及扩展名，不能把目录自动补全规则照搬过去。

集中入口可以让调用方不依赖更深的文件路径，但也会扩大该入口的公开面。目录内部实现通常直接导入具体模块，以免互相经由 index.ts 形成循环；包体能否裁掉未使用导出，取决于 ESM 依赖图与构建工具配置，不是“用了 index.ts”就能保证。

> [!info]- 来源
> - ESM 静态 re-export、依赖图与打包器副作用边界：[ECMAScript Modules](../../../../frontend/javascript/modules-and-host-boundaries.md)，ECMAScript 2026 规范及 Webpack 官方文档，核对日期：2026-11-06。
