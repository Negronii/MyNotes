# How does an existing Create React App project mount its React root? / 现有 Create React App 项目如何挂载 React 根节点？

In a React 18-era Create React App project, `npm start` runs the development server. The HTML shell provides a host element, commonly `<div id="root"></div>`. The JavaScript entry point calls `createRoot` on that element and passes the root component to `render`. / 在 React 18 时期的 Create React App 项目中，`npm start` 启动开发服务。HTML 提供挂载容器，通常是 `<div id="root"></div>`。JavaScript 入口在这个容器上调用 `createRoot`，再把根组件交给 `render`。

## Read the existing files / 理解现有文件

`public/index.html` supplies the container. An entry module such as `src/index.jsx` imports the application component. JSX and `createElement` both produce React elements for the root to render.

~~~jsx
import { createElement } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

const container = document.getElementById("root");
createRoot(container).render(createElement(App));
// With JSX, the equivalent argument is <App />.
~~~

`src/App.jsx` can import child modules such as `src/components/Header.jsx`. JSX uses `className` to set an HTML class, and braces to insert an expression. For example, `<h1 className="header">Welcome, {name}</h1>` creates a heading with a dynamic part.

## Recognize the course commands / 识别原课程命令

~~~sh
npx create-react-app my-react-app
cd my-react-app
npm start
~~~

The React team deprecated Create React App for new projects in 2025. For project setup today, use the current React guide. The root example uses the `createRoot` API introduced in React 18, so older applications may use a different entry point. [Sunsetting Create React App](https://react.dev/blog/2025/02/14/sunsetting-create-react-app) · [Start a New React Project](https://react.dev/learn/start-a-new-react-project) · [React `createRoot`](https://react.dev/reference/react-dom/client/createRoot)
