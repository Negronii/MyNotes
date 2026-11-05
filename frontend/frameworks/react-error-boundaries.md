# Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？

**Core answer / 核心回答：** A React Error Boundary is a class component that displays fallback UI for errors thrown while rendering descendants, in their constructors, or in their React lifecycle methods. It does not catch event-handler errors, ordinary asynchronous callbacks, server-rendering errors, or errors thrown by the boundary itself. One documented exception is an error thrown inside the function passed to the startTransition function returned by useTransition (including a rejected Promise returned by that function). / React Error Boundary 是类组件，可在后代树渲染、构造函数或 React 生命周期方法抛错时显示备用 UI。它不会捕获事件处理器、普通异步回调、服务端渲染或边界自身抛出的错误。一个文档列出的例外是 useTransition 返回的 startTransition 所执行函数抛错（包括该函数返回的 rejected Promise）。

## Boundary example and limits / 边界示例与范围

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

**See also:** [React Basics / React基础](./react-basics.md) for state updates and render/commit; [Advanced React / React进阶](./advanced-react.md) for Suspense loading and error states.

**Sources checked 2026-10-15:** [Component and lifecycle methods](https://react.dev/reference/react/Component), [Error Boundary caveats](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary), [useTransition Error Boundary example](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary).
