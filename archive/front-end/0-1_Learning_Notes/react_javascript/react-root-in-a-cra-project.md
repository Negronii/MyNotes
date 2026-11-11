# 现有 Create React App 项目怎样挂载 React 根节点？

**案例背景。** 维护一个现有 Create React App（CRA，React 应用脚手架）项目：HTML 页面提供 `#root` 容器，入口模块在其中挂载 `<App />`。先核对 `package.json` 中的 `react` 和 `react-dom` 依赖；下方的 `createRoot` 示例要求两者兼容且版本为 React 18 或更高，因为既有 CRA 仓库也可能仍使用 React 17。CRA 默认提供空的 `#root` 容器时，用 `createRoot` 挂载。若项目另行准备了 React 服务端或预渲染 HTML，客户端可用 `hydrateRoot` 接管，但服务器标记必须与客户端首次渲染的结果匹配。

CRA 已不再推荐用于创建新应用，但仍以维护模式运行，已有项目可以继续维护。继续维护 CRA 时，按仓库的 `package.json` 脚本启动，常见为 `npm start`；无需把旧教程中的创建命令照搬到新项目。

## 入口容器与当前挂载方式

下方两个 React 18+ 入口示例使用自动 JSX 转换。仍用 classic 转换的 React 18 旧项目，需要在入口额外 `import React from "react"`；React 19 项目应启用新版 JSX 转换。

~~~html
<!-- public/index.html -->
<div id="root"></div>
~~~

~~~tsx
// CRA JavaScript 入口常为 src/index.js。
// TypeScript 入口常为 src/index.tsx。
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

const container = document.getElementById("root");
if (!container) throw new Error("缺少 #root 容器");

const root = createRoot(container);
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
~~~

`container` 是页面里的 DOM 容器；`createRoot(container)` 返回管理这个容器的 React root 对象，通常只创建一次；`root.render` 接收 `<App />` 描述的 React element（React 元素），由 React 更新容器中的界面。`StrictMode`（严格模式）用于开发期暴露不纯渲染和缺少清理的问题；它不是挂载应用的必需条件，也不会替代 `createRoot`。开发时它可能额外调用某些纯函数，并对 Effect 多做一次建立和清理检查；这不是生产环境每次操作都会重复执行的含义。

如果这个 `#root` 已包含 React 在服务端或构建时生成的初始 HTML，且服务器标记与客户端首次 `<App />` 输出一致（包括结构、文本和属性），客户端入口用 `hydrateRoot` 做 hydration（水合，复用已有标记并接上交互）：

~~~tsx
import { hydrateRoot } from "react-dom/client";
import App from "./App";

const container = document.getElementById("root");
if (!container) throw new Error("缺少 #root 容器");

hydrateRoot(container, <App />);
~~~

`createRoot(...).render(...)` 首次运行会清掉容器内原有内容；有服务端 HTML 时这样做会丢弃它并重新创建节点。若水合时两边首屏不匹配，React 会报告 hydration mismatch（水合不匹配），并可能改为客户端重建不匹配区域；一次实际重放中，按钮文本不一致导致原按钮节点被替换。默认 CRA 空挂载点走上面的客户端根示例；水合分支只适用于项目另行准备了 React 生成的 HTML，并确保首屏输出匹配的情况。

## 旧项目中的 `ReactDOM.render`

旧课程和旧仓库可能还使用 `ReactDOM.render`：

~~~jsx
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

ReactDOM.render(<App />, document.getElementById("root"));
~~~

React 17 中这是旧的客户端入口；React 18 才新增 `react-dom/client` 的 `createRoot` 和 `hydrateRoot`。React 18 起 `ReactDOM.render` 被弃用并输出警告，而且会让应用继续采用 React 17 的兼容运行模式；React 19 已移除此 API。普通空容器迁移到 `createRoot`，服务端生成的 HTML 则迁移到 `hydrateRoot`，并保证首次输出匹配。

旧教程里还可能有 `npx create-react-app my-react-app` 这样的建项目命令；这是旧项目的创建方式，新项目请先看[React 官方新项目指南](https://react.dev/learn/start-a-new-react-project)。

## JSX 描述 React element

JSX（JavaScript XML 风格语法）中的 `<App />` 会描述一个 React element（React 元素）；`createElement(App)` 也能创建同类描述。JSX 由构建配置转换为自动 JSX runtime 调用，或旧式的 `React.createElement` 调用；它不是直接写入 DOM 的 HTML 字符串。写普通 HTML 的 `class` 属性时，JSX 使用 `className`；表达式写在花括号里，例如：

~~~jsx
const name = "林";
const heading = <h1 className="header">欢迎，{name}</h1>;
~~~

> [!info]- 来源与版本核验（React 19.3；2026-11-12）
> - 客户端 root 的创建、已有服务端 HTML 时改用 `hydrateRoot`：[React `createRoot`](https://react.dev/reference/react-dom/client/createRoot)、[React `hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot)，React 官方 API 参考。
> - React 18 中 `ReactDOM.render` 的弃用警告与 React 17 兼容模式：[How to Upgrade to React 18](https://react.dev/blog/2022/03/08/react-18-upgrade-guide)，React 团队，2022-03-08。
> - React 19 移除 `ReactDOM.render`：[React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)，React 官方升级指南。
> - CRA 不再推荐用于新应用，既有项目仍以维护模式工作：[Sunsetting Create React App](https://react.dev/blog/2025/02/14/sunsetting-create-react-app)，React 团队，2025-02-14。
> - 开发 StrictMode 的额外检查：[React `StrictMode`](https://react.dev/reference/react/StrictMode)，React 官方 API 参考。
> - JSX 语法、表达式与 `className`：[Writing Markup with JSX](https://react.dev/learn/writing-markup-with-jsx)；`<App />` 对应元素描述的 API：[React `createElement`](https://react.dev/reference/react/createElement)，React 官方文档。
