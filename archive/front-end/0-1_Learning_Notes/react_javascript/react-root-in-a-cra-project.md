# 现有 Create React App 项目怎样挂载 React 根节点？

Create React App（CRA，React 应用脚手架）旧项目通常由 `public/index.html` 提供 `<div id="root"></div>`，再由入口模块调用 `createRoot` 并渲染根组件。这个入口模式仍适合维护既有项目；React 团队已不建议用 CRA 创建新项目。

~~~html
<!-- public/index.html -->
<div id="root"></div>
~~~

~~~tsx
// src/index.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

const container = document.getElementById("root");
if (!container) throw new Error("缺少 #root 容器");

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
);
~~~

JSX 的 `<App />` 与 `createElement(App)` 都会创建 React element。React 写普通 HTML class 属性时用 `className`，表达式放在花括号内，例如 `<h1 className="header">欢迎，{name}</h1>`。

旧课程里的 npx create-react-app my-react-app 与 npm start 只用于识别已有仓库的启动方式；新应用的框架选择见[React 官方新项目指南](https://react.dev/learn/start-a-new-react-project)。

> [!info]- 来源
> - createRoot 接管已有 DOM 容器并渲染根节点：[React createRoot](https://react.dev/reference/react-dom/client/createRoot)，React 19.3 文档，核对日期：2026-11-06。
> - CRA 停止推荐用于新应用及迁移背景：[Sunsetting Create React App](https://react.dev/blog/2025/02/14/sunsetting-create-react-app)，React 团队，2025-02-14。
