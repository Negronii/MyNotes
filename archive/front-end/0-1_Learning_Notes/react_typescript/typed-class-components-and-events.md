# React 类组件的 state 与事件怎样标注类型？

React 仍支持类组件，不过新组件通常用函数组件和 Hooks（钩子）。维护旧类组件时，`Component<Props, State>` 的两个 type argument（类型实参）分别描述 props（属性）和 state（状态）；事件处理器还要把 React 的鼠标事件关联到实际绑定处理器的 HTML 元素。在已有 React 页面中渲染 `<Counter initialCount={3} />`，用户点击按钮内的文字后计数加一。

下面示例采用 React 19、对应的 `@types/react` 类型与自动 JSX 转换。

~~~tsx
import { Component, type MouseEvent } from "react";

type Props = { initialCount: number };
type State = { count: number };

export class Counter extends Component<Props, State> {
  state: State = { count: this.props.initialCount };

  handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    // 点到 span，target 是 span，currentTarget 是 button。
    const buttonLabel = event.currentTarget.textContent?.trim() ?? "按钮";
    const targetIsButton = event.target === event.currentTarget;

    this.setState(
      previous => ({ count: previous.count + 1 }),
      () => console.log(
        `${buttonLabel} 的点击目标就是按钮：${targetIsButton}；已提交的计数：`,
        this.state.count
      )
    );
  };

  render() {
    return (
      <section>
        <p>当前计数：{this.state.count}</p>
        <button type="button" onClick={this.handleClick}>
          <span>增加一次</span>
        </button>
      </section>
    );
  }
}
~~~

挂载时，类字段用 `initialCount` 初始化计数；这是初始值，父组件之后把 prop 改为别的数字，不会自动把当前计数重置。点击“增加一次”这个 `span` 时，事件会冒泡到按钮的处理器：`event.target`（事件起点）指向事件发生的子节点，`event.currentTarget`（当前处理器节点）指向正在执行处理器的 button，因此可安全按 `HTMLButtonElement` 读取它的文本。`MouseEvent<HTMLButtonElement>` 把 `currentTarget` 约束为 `EventTarget & HTMLButtonElement`，而 `target` 仍是通用的 `EventTarget`；若要把 target 当具体元素读取属性，需先缩小它的类型。处理器结束后 React 不保证 `currentTarget` 仍指向按钮，因此代码先保存文本与比较结果，再在提交回调中使用这些普通值；React 19.3 实际运行时，更新回调中的 `event.currentTarget` 已是 `null`。

`handleClick` 用类字段箭头函数定义，传给 `onClick` 时仍指向这个组件实例。若改成普通实例方法，作为裸函数传递时不会自动保留 `this`，需显式绑定。点击后，`setState` 把更新加入 React 队列；updater 用待处理的上一份 state 算出 `{ count: previous.count + 1 }`。当前处理器不会因此立即读到新 state；提交更新后才执行第二个 callback（回调），此时 `this.state.count` 已是新值。案例从 3 点击一次，提交后显示 4，回调也读取 4；点击 span 时目标比较为 `false`。

类组件的 `setState` 会把传入对象（包括 updater 返回的对象）浅合并到现有 state；只返回 `{ count: ... }` 时，其他顶层字段会保留。函数组件的 `useState` setter 则替换那一个 state 值；若它存的是对象，例如 `const [counter, setCounter] = useState({ count: 0, label: "counter" })`，setter 会替换整个对象；更新时要显式保留其他字段，并用 updater 从待处理的旧值计算：`setCounter(previous => ({ ...previous, count: previous.count + 1 }))`。同一处理器连续排两次更新时，这种写法会依次读取队列中的新旧值。维护旧类代码时，不能把这两种更新模型当成同一套规则。

类生命周期与函数组件 Effect（副作用同步）的关系见[React 更新轮次](../../../../frontend/frameworks/react-basics.md)。

> [!info]- 来源
> - 自动 JSX 转换让 JSX 无需单独导入 React 命名空间；React 19 要求使用该转换：[React 19 Upgrade Guide — New JSX Transform](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#new-jsx-transform-is-now-required)，React 官方文档，核验日期：2026-11-12。
> - 类组件 `Component` 的 props、state、setState 队列、updater 浅合并、提交后 callback，以及类组件仍受支持但不推荐用于新代码：[Component](https://react.dev/reference/react/Component)，React 官方 API，核验日期：2026-11-12。
> - `currentTarget` 是当前处理器绑定节点，`target` 是事件起点且可能是子节点：[Common components (e.g. `<div>`)](https://react.dev/reference/react-dom/components/common)、[Responding to Events](https://react.dev/learn/responding-to-events)，React 官方文档，核验日期：2026-11-12。
> - `MouseEvent<HTMLButtonElement>` 等事件类型来自 React 类型定义：[Using TypeScript](https://react.dev/learn/typescript)，React 官方文档；对应 React 19 声明见 [DefinitelyTyped `types/react/index.d.ts`](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts)，核验日期：2026-11-12。
> - 函数组件 setter 基于其 state 值更新并替换该 state 变量：[useState](https://react.dev/reference/react/useState)，React 官方 API，核验日期：2026-11-12。
