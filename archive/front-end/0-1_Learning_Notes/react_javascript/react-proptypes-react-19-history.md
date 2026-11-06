# React 19 移除 PropTypes 后，旧组件怎样维护？

React 18 及更早版本可在开发期用 propTypes 检查组件属性。React 19 已移除 React 自带的 static propTypes 支持；组件 API 可用 TypeScript 在编译期检查，来自 API、存储或用户输入的数据则仍需运行时解析，见[TypeScript 如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md)。

下面代码只用于维护仍依赖旧 React 版本的项目，不要把它当作 React 19 的运行时校验：

~~~jsx
import PropTypes from "prop-types";

function Greeting({ message }) {
  return <h1>{message}</h1>;
}

Greeting.propTypes = {
  message: PropTypes.string.isRequired,
};
~~~

函数组件默认值可写在参数解构中，例如 `function Greeting({ message = "Hello" })`；类组件仍可使用 `static defaultProps`。默认值只处理缺失或 `undefined` 的 prop，不会处理 `null`。

> [!info]- 来源
> - React 19 移除 static propTypes 并建议迁移到类型系统：[React Legacy APIs — Removed APIs](https://react.dev/reference/react/legacy#removed-apis)，React 官方文档，核对日期：2026-11-06。
> - 默认 prop 值与类组件 defaultProps：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component#specifying-a-default-value-for-a-prop)、[React Component](https://react.dev/reference/react/Component#static-defaultprops)，React 19.3 文档，核对日期：2026-11-06。
