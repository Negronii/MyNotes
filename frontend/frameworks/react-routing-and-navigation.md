# How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？

**Core answer / 核心回答：** React Router matches the current location to a route, while SPA and MPA describe whether navigation updates the current document or requests another one. The choice depends on delivery, interaction, accessibility, hosting, and operations. / React Router 将当前地址匹配到路由；SPA 与 MPA 则描述导航是更新当前文档还是请求另一个文档。选择取决于内容交付、交互、无障碍、托管和运维需求。

## How does React Router work? / React Router如何工作？

**Core answer / 核心回答：** React Router matches the current location to a route and renders the configured UI. The example below uses the React Router v6 declarative API; current releases also offer data and framework modes with additional APIs. A browser-history router needs the host to serve the application entry point for client-side paths. / React Router 将当前地址匹配到路由并渲染对应界面。下面的例子使用 React Router v6 声明式 API；当前版本还提供数据模式和框架模式。浏览器历史路由要求服务器将客户端路径回退到应用入口文件。

~~~jsx
import { BrowserRouter, Routes, Route, useParams } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/posts/:postId" element={<Post />} />
      </Routes>
    </BrowserRouter>
  );
}

function Home() {
  return <h1>Home</h1>;
}

function Post() {
  const { postId } = useParams();
  return <h1>Post {postId}</h1>;
}
~~~

- **BrowserRouter** uses the browser History API and clean paths.
- **HashRouter** stores the route after the URL hash; it can fit hosting where server fallback configuration is unavailable.
- **MemoryRouter** stores location in memory and is useful in tests or non-browser contexts.

Use Link for navigation users can follow and useNavigate for programmatic navigation. Route API and package imports vary by React Router version; follow the version installed by the project.

## What is the difference between an SPA and an MPA? / SPA和MPA有什么区别？

**Core answer / 核心回答：** An MPA navigation requests another document; an SPA typically keeps one document loaded and updates route content in the client. Server rendering and client navigation can be combined, so many current applications use a hybrid model. Choose based on content delivery, interaction, accessibility, and operational needs rather than the label alone. / MPA 导航会请求另一个文档；SPA 通常保留一个文档并在客户端更新路由内容。服务端渲染和客户端导航可以组合，因此许多现代应用采用混合模式。应根据内容交付、交互、无障碍和运维需求选择，而非只看标签。

| Aspect | SPA pattern | MPA pattern |
|---|---|---|
| Navigation | Client router updates the current document | Browser requests another document |
| State | Client state can persist between route changes | State often needs URL, storage, or server persistence |
| Initial delivery | Depends on shell size, rendering, and data strategy | Depends on document and asset delivery |
| SEO and accessibility | Require deliberate rendering and semantic structure | Also require meaningful HTML and semantic structure |

**See also:** [React Basics / React基础](./react-basics.md) for state-driven rendering; [Next.js / Next.js开发](./next-js.md) for server/client rendering and framework routing.

**Sources checked 2026-10-15:** [React Router v6 Concepts](https://reactrouter.com/docs/en/v6/start/concepts), [React Router: Picking a Mode](https://reactrouter.com/start/modes).
