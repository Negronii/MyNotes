# React错误边界能恢复哪些失败？

**案例背景。** 报表页从 `/reports?sort=recent#summary` 显示服务端给出的 May、April；选择 **Oldest first** 后，`sort=oldest` 让列表顺序变为 April、May。排序写入历史并在 Back 时从 URL 恢复由[浏览器导航路径](../browser/browser-navigation-and-history.md#让排序状态跟随地址栏与前进后退)负责。若这片列表的某个组件在 render（渲染）时抛错，Error Boundary（错误边界）可以替代列表显示备用内容，同时让排序工具栏等边界外界面继续工作。它也能接住 React 管理的子组件 Effect setup/cleanup 中同步抛出的错误；点击处理器和 Effect 启动的异步任务失败则各有自己的处理路径。

## 边界放在用户能理解的恢复位置

React 内置的错误边界仍由类组件实现；`fallback`（备用界面）应说明用户能做什么。`static getDerivedStateFromError` 决定下一次 render 是否显示 fallback；`componentDidCatch` 适合记录错误和组件栈。下面的边界包住报表区域；按钮重置边界并重新渲染子树，不会重试数据请求：

~~~jsx
import { Component } from "react";

class ReportBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error(error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <section>
          <p role="alert">报表区域无法显示。</p>
          <button type="button" onClick={() => this.setState({ failed: false })}>
            重新尝试显示
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}

function ReportsShell({ reports }) {
  return (
    <>
      <div role="toolbar">报表排序工具栏（占位）</div>
      <ReportBoundary>
        <ReportsList reports={reports} />
      </ReportBoundary>
    </>
  );
}

function ReportsList({ reports }) {
  return <ul>{reports.map(report => <li key={report.id}>{report.title}</li>)}</ul>;
}
~~~

可临时把 `reports` 设为 `[null]` 检查边界：`ReportsList` 读取空行的属性时抛错，列表被备用界面替换，排序工具栏占位仍留在边界外。边界粒度决定错误后保留多少界面。这里 `reports.map` 在被边界包住的 `ReportsList` 组件中执行，所以行渲染出错会落到该边界；包住整页会让工具栏也消失，每个单元格都放边界又会产生许多细碎的恢复区。应按用户能独立理解和恢复的区域划分。重新渲染同一失败组件会再次触发边界；对于查询错误，通常应让数据层重试请求并把错误状态呈现在列表边缘。

在 `return <ReportsList />` 周围写普通 `try/catch` 捕获不到 `ReportsList` 后续的 render 错误：JSX 先创建元素描述，React 稍后才渲染其子树；用边界明确包住要隔离的区域。

## 错误边界与其他失败处理方式

React 会把子组件 render、构造函数、React 生命周期，以及 React 管理的子组件 Effect setup/cleanup 中同步抛出的错误交给最近的错误边界。React 19 的 Transition Action（过渡动作）里抛出的错误也会转交边界；`use` 读取的 Promise 若拒绝，同样会进入最近边界。边界自己 render 抛错时，只能交给更外层边界。

这些失败路径按同步调用还是异步任务区分：

| 失败发生位置 | 处理方式 |
|---|---|
| 普通点击处理器 | 在处理器里 try/catch，设置界面错误或上报 |
| 子组件 Effect setup/cleanup 同步抛错 | 由最近错误边界显示备用界面 |
| Effect 启动的 Promise 后续拒绝、定时器回调异步抛错 | 显式处理 rejection 或更新错误状态；不会自动交给错误边界 |
| `useEffect` 请求返回失败 | 在请求/查询状态显示失败和重试；异步请求失败不会自动变成 render error |
| Suspense 子树仍在加载 | 需要等待界面时由最近 `<Suspense>` fallback 承担；Transition 中可保留已显示内容 |
| 服务端渲染阶段 | 由框架或服务端渲染管线处理，不靠客户端边界 |

边界本身没有函数组件版本的内置等价 API，可复用类边界或使用已有边界库。错误边界显示“这一块无法工作”；Suspense（挂起边界）表示“这一块还没准备好”；查询错误则说明“这次数据读取失败”。[报表服务端状态章节](./react-server-state-and-optimistic-updates.md)负责请求缓存、错误重试和更新顺序。

> [!info]- 来源与版本核验（React 19.3；2026-11-06）
> - 类组件捕获范围、未捕获类别、`getDerivedStateFromError` 与 `componentDidCatch`：[Component — Catching Rendering Errors with an Error Boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)，React 19.3 文档。
> - Effect setup/cleanup 在 commit 阶段由 React 调用：[useEffect](https://react.dev/reference/react/useEffect)，React 19.3 文档。React 19.3.0 + jsdom 30.1.3 中同步子 Effect throw 由最近边界捕获；Promise 后续 rejection 与定时器回调仍需异步错误处理。
> - JSX 描述如何在后续 render 中成为已提交界面：[Render and Commit](https://react.dev/learn/render-and-commit)，React 19.3 文档。
> - Transition Action 中抛错交给边界：[useTransition — Displaying an error to users with an error boundary](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-an-error-boundary)，React 19.3 文档。
> - 被拒绝 Promise 与最近错误边界：[use](https://react.dev/reference/react/use)，React 19.3 文档。
> - Suspense fallback 仅处理挂起中的内容：[Suspense](https://react.dev/reference/react/Suspense)，React 19.3 文档；核验日期 2026-11-06。
