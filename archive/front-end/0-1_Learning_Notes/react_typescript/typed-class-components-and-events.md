# TypeScript 怎样为 React 类组件的 state 与事件定型？

React 仍支持类组件，但新代码通常选择函数组件与 Hooks。本页保留旧项目维护会遇到的 Props/State 泛型、setState updater 和类方法 this 绑定示例；类组件当前生命周期与函数组件 Effect 的关系见[React 更新轮次](../../../../frontend/frameworks/react-basics.md)。

~~~tsx
import { Component, type MouseEvent } from "react";

type Props = { initialCount: number };
type State = { count: number };

export class Counter extends Component<Props, State> {
  state: State = { count: this.props.initialCount };

  handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    // currentTarget 是绑定处理器的 button；target 可能是里面被点到的 span。
    const button = event.currentTarget;
    button.dataset.clicked = "true";

    this.setState(
      previous => ({ count: previous.count + 1 }),
      () => console.log("已提交的计数：", this.state.count)
    );
  };

  render() {
    return (
      <button type="button" onClick={this.handleClick}>
        <span>已点击 {this.state.count} 次</span>
      </button>
    );
  }
}
~~~

类方法若以普通实例方法传给事件处理器，调用时可能失去实例接收者；类字段箭头函数捕获实例 this。setState updater 接收排队处理时的前一份 state，不能在 setter 后立刻读 this.state 并期待它已改变；第二个回调在更新提交后运行。React 合并类 state 顶层字段的方式也不同于 useState 的整体替换，维护旧代码时不要直接混用两个更新模型。

> [!info]- 来源
> - Component Props、State、setState 与类生命周期：[React Component](https://react.dev/reference/react/Component)，React 19.3 文档，核对日期：2026-11-06。
> - React 鼠标事件类型与 DOM currentTarget：[React TypeScript Cheatsheet — Events](https://react-typescript-cheatsheet.netlify.app/docs/basic/getting-started/forms_and_events/)，React 类型维护者社区参考，核对日期：2026-11-06。
