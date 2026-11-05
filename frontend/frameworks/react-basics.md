# How does React turn a user action into an updated interface? / React如何把用户操作变成更新后的界面？

**Core answer / 核心回答：** A user action reaches a React handler through the browser's event system. The handler requests a state update, but it continues to read the snapshot from its current render. React then renders the next component descriptions, matches them by type, position, and sibling keys, and commits the required host changes. The browser handles the later style, layout, and paint work. This route connects [DOM events / DOM事件](../browser-apis/dom-manipulation-and-events.md), React state, and [browser rendering / 浏览器渲染](../browser/browser-basics.md); it does not promise one paint for every setter call. / 用户操作经由浏览器事件系统到达 React 处理器。处理器请求状态更新，但仍读取当前这次 render 的快照。随后 React 重新计算组件描述，按元素类型、位置和兄弟 key 匹配，并提交必要的宿主环境变更。之后的样式、布局和绘制由浏览器处理。这条路线连接 [DOM events / DOM事件](../browser-apis/dom-manipulation-and-events.md)、React state 与[浏览器渲染](../browser/browser-basics.md)；它不保证每次调用 setter 都对应一次绘制。

~~~mermaid
flowchart LR
    A[User input event] --> B[Handler requests state update]
    B --> C[Next render reads queued state]
    C --> D[React matches elements and state identity]
    D --> E[Commit necessary host changes]
    E --> F[Browser updates pixels when needed]
    B -. current handler keeps its render snapshot .-> C
~~~


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

**Core answer / 核心回答：** An Error Boundary can show fallback UI for errors in descendant rendering and React lifecycles, with documented exceptions such as event-handler and ordinary async errors. The exact scope, Transition exception, and class example are in [Which errors can a React Error Boundary recover from? / React Error Boundary能恢复哪些错误？](./react-error-boundaries.md). / Error Boundary 可为后代渲染和 React 生命周期中的错误显示备用 UI，但事件处理器和普通异步错误等情况不在其范围内。完整范围、Transition 例外和类组件示例见[React Error Boundary能恢复哪些错误？](./react-error-boundaries.md).

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

**Core answer / 核心回答：** React Router matches a location to a route, then renders its configured UI. The v6 declarative example, router choices, hosting fallback, and SPA/MPA tradeoffs are in [How do React routes map URLs to views, and when is SPA navigation a fit? / React路由如何把 URL 映射到视图，何时适合 SPA 导航？](./react-routing-and-navigation.md). / React Router 将地址匹配到路由并渲染对应界面。v6 声明式示例、路由器选择、托管回退及 SPA/MPA 权衡见[React路由如何映射 URL 并选择导航模型？](./react-routing-and-navigation.md).

## What is the difference between an SPA and an MPA? / SPA和MPA有什么区别？

**Core answer / 核心回答：** An SPA usually updates route content in one loaded document; an MPA requests another document. Rendering modes can be combined, so evaluate the actual delivery and operating needs. The comparison table and navigation example are in [the React routing question](./react-routing-and-navigation.md). / SPA 通常在已加载的文档中更新路由内容；MPA 会请求另一个文档。渲染模式可以组合，应结合内容交付和运维需求判断。比较表和路由示例见[React 路由问题](./react-routing-and-navigation.md).

**Sources checked 2026-10-15:** [React: Introducing the New JSX Transform](https://react.dev/blog/2020/09/22/introducing-the-new-jsx-transform), [React: Render and Commit](https://react.dev/learn/render-and-commit), [StrictMode](https://react.dev/reference/react/StrictMode), [Component and lifecycle methods](https://react.dev/reference/react/Component), [Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Queueing State Updates](https://react.dev/learn/queueing-a-series-of-state-updates).
