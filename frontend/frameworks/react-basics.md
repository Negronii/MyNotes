# React Basics / React基础

React components describe UI from props and state. These notes focus on JSX, element identity, class lifecycle methods, state updates, and routing.

## What is JSX, and what does it compile to? / JSX是什么，最终会编译成什么？

**Core answer / 核心回答：** JSX is syntax for describing elements inside JavaScript; it is not HTML text. A configured compiler transforms JSX using either the classic factory runtime or the automatic JSX runtime. The emitted calls depend on the compiler and its configuration. / JSX 是在 JavaScript 中描述元素的语法，不是 HTML 字符串。配置好的编译器会使用经典工厂模式或自动 JSX runtime 转换它；实际生成的调用取决于编译器和配置。

~~~jsx
const element = <h1 className="title">Hello</h1>;
~~~

With the automatic runtime, a React compiler can emit calls to helpers from react/jsx-runtime. With the classic runtime, it can emit React.createElement calls. The automatic transform means React does not need to be imported solely for JSX when the project is configured for it.

- Lowercase tags such as **div** name built-in elements; uppercase identifiers such as **Profile** name component values.
- Curly braces insert JavaScript expressions into JSX.
- React DOM uses names such as **className** and **onClick** rather than HTML attribute spelling.

## How does React match elements between renders? / React如何判断哪些元素需要更新？

**Core answer / 核心回答：** React uses element type, tree position, and keys among siblings to match elements and preserve component state. Stable keys should represent item identity when a list can change; an index is suitable only when the list's membership and order are fixed. / React 使用元素类型、树中的位置和兄弟元素间的 key 来匹配元素并保留组件 state。列表可能变化时，稳定 key 应代表数据项身份；只有列表成员和顺序固定时，索引才适合作为 key。

~~~jsx
{items.map(item => <ListItem key={item.id} item={item} />)}
~~~

Keys are local to one set of siblings; they do not need to be unique across the entire application. React may preserve state for a matching element and reset it when its type or key changes. This is why an index key can attach local state to the wrong data after an insertion, deletion, or reorder.

## What are class lifecycle methods? / 类组件的生命周期方法是什么？

**Core answer / 核心回答：** Class components have mount, update, and unmount lifecycles. Rendering can be repeated or abandoned, so keep render pure and put external synchronization in lifecycle methods or Effects. Function component Effects have setup and cleanup semantics; there is no exact one-to-one mapping from each class method to a Hook. / 类组件有挂载、更新和卸载阶段。render 可能重复执行或被放弃，因此应保持纯净，并将外部同步放在生命周期方法或 Effect 中。函数组件 Effect 有自己的 setup 和 cleanup 语义，不能把每个类方法与 Hook 一一对应。

| Class lifecycle | Purpose |
|---|---|
| **constructor** | Initialize state and instance fields. |
| **getDerivedStateFromProps** | Runs before render on mount and updates; rarely derives state from incoming props. |
| **render** | Return the next UI description; do not perform side effects here. |
| **shouldComponentUpdate** | Runs before an update render and can skip it as a performance optimization. |
| **getSnapshotBeforeUpdate** | Runs after render but before DOM mutations; its return value is passed to componentDidUpdate. |
| **componentDidMount** | Synchronize with external systems after the component commits. |
| **componentDidUpdate** | React to committed prop or state changes; guard against unnecessary loops. |
| **componentWillUnmount** | Release subscriptions, timers, and other resources. |
| **getDerivedStateFromError / componentDidCatch** | Render fallback UI and report errors from a descendant subtree. |

An Effect runs after a commit; React runs its previous cleanup before setting up the Effect again when dependencies change, and on unmount. In development, root StrictMode adds an extra setup-and-cleanup cycle to help expose incomplete cleanup. This is a development check, not an extra production lifecycle.

## What does an Error Boundary catch? / Error Boundary能捕获哪些错误？

**Core answer / 核心回答：** A React Error Boundary is a class component that displays fallback UI for errors thrown while rendering descendants, in their constructors, or in their React lifecycle methods. It does not catch event-handler errors, ordinary asynchronous callbacks, server-rendering errors, or errors thrown by the boundary itself. One documented exception is an error thrown inside the function passed to the startTransition function returned by useTransition (including a rejected Promise returned by that function). / React Error Boundary 是类组件，可在后代树渲染、构造函数或 React 生命周期方法抛错时显示备用 UI。它不会捕获事件处理器、普通异步回调、服务端渲染或边界自身抛出的错误。一个文档列出的例外是 useTransition 返回的 startTransition 所执行函数抛错（包括该函数返回的 rejected Promise）。

~~~jsx
import React from "react";

class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error(error, info.componentStack);
  }

  render() {
    return this.state.hasError
      ? <p>Something went wrong.</p>
      : this.props.children;
  }
}
~~~

The built-in React boundary API is class-based. A library can make boundary composition easier, but try/catch around JSX does not catch rendering failures.

## Is setState synchronous? / setState是同步还是异步？

**Core answer / 核心回答：** A state setter requests another render; it does not mutate the state snapshot held by the current render or event handler. React 18+ with createRoot also batches updates from timeouts, promises, and native event handlers. React 17 and React 18's legacy ReactDOM.render path batch fewer contexts. / state setter 会请求下一次渲染，不会改写当前 render 或事件处理器持有的 state 快照。React 18+ 使用 createRoot 时，也会批处理 timeout、Promise 和原生事件处理器中的更新。React 17 以及 React 18 的旧 ReactDOM.render 路径会批处理较少的场景。

~~~jsx
setCount(count + 1);
console.log(count); // This render's snapshot is unchanged.

setCount(previous => previous + 1);
setCount(previous => previous + 1); // Queued updates build on each other.
~~~

Use an updater when the next value depends on the previous value. Read the new state during a later render or in an Effect when appropriate; do not expect the variable in the current handler to change.

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

**See also:** [Next.js / Next.js开发](./next-js.md) for router-specific rendering; [Advanced React / React进阶](./advanced-react.md) for Hooks, refs, and component composition.

**Sources checked 2026-10-15:** [React: Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform), [React: Render and Commit](https://react.dev/learn/render-and-commit), [StrictMode](https://react.dev/reference/react/StrictMode), [Component and lifecycle methods](https://react.dev/reference/react/Component), [Error Boundary caveats](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary), [useTransition Error Boundary example](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary), [Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Queueing State Updates](https://react.dev/learn/queueing-a-series-of-state-updates), [React Router v6 Concepts](https://reactrouter.com/docs/en/v6/start/concepts), [React Router: Picking a Mode](https://reactrouter.com/start/modes).
