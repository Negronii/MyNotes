# React 19 移除 PropTypes 后，旧组件怎样维护？

**案例背景。** 一个旧 React 项目从 18 升级到 19 后，组件仍附有 propTypes（属性类型声明），但无效属性不再出现原来的警告。React 19 移除的是 React 对组件 propTypes 属性的自动检查；独立 prop-types 包仍可被代码引用，但单独安装或保留声明不会让 React 19 自动校验。组件 API（应用程序编程接口）可用 TypeScript 在编译期检查，来自 API、存储或用户输入的数据则仍需在边界做运行时解析，见[TypeScript 如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md)。

## 旧组件里还会遇到的写法

React 15.5 起，React.PropTypes 被拆分到单独的 prop-types 包；React 15.5–18 会读取组件的 propTypes，并只在开发构建输出校验警告，不会因不匹配而阻止组件渲染。下面这段使用独立包的代码适合维护这些旧版项目：

~~~jsx
import PropTypes from "prop-types";

function Greeting({ message }) {
  return <h1>{message}</h1>;
}

Greeting.propTypes = {
  message: PropTypes.string.isRequired,
};
~~~

例如在 React 18 开发构建中，调用 `<Greeting message={42} />` 会产生“应为字符串、实际为数字”的 PropTypes 警告，但 React 仍把 `42` 渲染在标题中；同一调用在 React 18 生产构建不会做 PropTypes 检查。升级到 React 19 后，React 不再自动读取这份声明，同样不会产生这条警告，组件仍会收到并渲染 `42`。这里指组件的 `propTypes` 属性，不是 JavaScript class 里的 `static` 关键字；React 19 的变化是移除了 React 的自动检查。

## 当前组件 API 的类型与默认值

用 TypeScript 描述组件调用方传入的属性，例如：

~~~tsx
type GreetingProps = { message: string };

function Greeting({ message }: GreetingProps) {
  return <h1>{message}</h1>;
}
~~~

上面的必填 `message` 保留旧 API（应用程序编程接口）的调用约定：TypeScript 可以在项目编译时检查是否传入字符串；React 的旧 PropTypes 警告则只在开发环境检查运行时值，而且不会阻止渲染。TypeScript 类型会在编译时擦除，并不会在浏览器里验证 API 响应或本地存储。例如接口返回 `{"message":42}` 时，运行时解析应报告字段形状错误，由调用方显示错误，或将明确的字符串回退值传给 `Greeting`；解析成功时则传入解析得到的字符串，具体解析边界见上面的 TypeScript 笔记。

若产品约定允许省略 `message`，这是有意放宽调用契约的另一种 API，可以写成：

~~~tsx
type OptionalGreetingProps = { message?: string };

function OptionalGreeting({ message = "Hello" }: OptionalGreetingProps) {
  return <h1>{message}</h1>;
}
~~~

React 19 移除了函数组件的 `defaultProps`，改用参数默认值；类组件仍可写 `static defaultProps`。运行时，函数参数默认值和类默认值都只在属性缺失或值为 `undefined` 时采用，传入 `null` 不会触发默认值。

> [!info]- 来源
> - React v15.5 将 React.PropTypes 拆分到 prop-types 包：[React v15.5.0 发布说明](https://legacy.reactjs.org/blog/2017/04/07/react-v15.5.0.html)，核验日期：2026-11-12。
> - 旧版本 propTypes 只在开发模式检查：[React 18.2 Typechecking With PropTypes](https://legacy.reactjs.org/docs/typechecking-with-proptypes.html)，React 18.2 文档，核验日期：2026-11-12。
> - React 19 移除 React 的 propType 检查并移除函数组件 defaultProps；类组件仍支持 defaultProps：[React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)，React 官方文档，核验日期：2026-11-12。
> - 函数参数默认值；默认值不处理 null：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component#specifying-a-default-value-for-a-prop)、[React Component](https://react.dev/reference/react/Component#static-defaultprops)，React 19.3 文档，核验日期：2026-11-12。
> - 外部数据需运行时解析而非只依赖被擦除的 TypeScript 类型：[TypeScript 如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md)。
