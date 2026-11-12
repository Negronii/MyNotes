# 旧类组件怎样通过 connect 读取 Redux？

当前函数组件的 Redux hooks、类型推导和 Provider 入口见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。本页保留 react-redux connect 与类组件的维护模式，便于阅读旧项目；它不需要和 Hook 版本并排用于新组件。

本例沿用一个已有 store：初始根状态为 `{ language: "en" }`，根 reducer 处理 `settings/languageChanged` 并更新 `language`。下面导出的组件是 `connect` 返回的包装组件；把它和祖先中的 `<Provider store={store}>` 配成同一个 store 即可，本页不再重贴应用入口。

~~~tsx
import { Component } from "react";
import { legacy_connect as connect, type ConnectedProps } from "react-redux";

type RootState = { language: "en" | "zh" };

const mapStateToProps = (state: RootState) => ({
  language: state.language,
});

const mapDispatchToProps = {
  chooseLanguage: (language: "en" | "zh") => ({
    type: "settings/languageChanged" as const,
    payload: language,
  }),
};

const connector = connect(mapStateToProps, mapDispatchToProps);
type Props = ConnectedProps<typeof connector>;

class LanguageHeader extends Component<Props> {
  render() {
    return (
      <header>
        <h1>语言：{this.props.language}</h1>
        <button onClick={() => this.props.chooseLanguage("en")}>English</button>
        <button onClick={() => this.props.chooseLanguage("zh")}>中文</button>
      </header>
    );
  }
}

export default connector(LanguageHeader);
~~~

`mapStateToProps` 选择标题需要显示的字段。对象形式的 `mapDispatchToProps` 传入的是 action creator；React-Redux 会把它绑定到这个 store 的 `dispatch`，所以按钮属性 `chooseLanguage` 是派发函数。点击“中文”后，它派发 `{ type: "settings/languageChanged", payload: "zh" }`；根 reducer 把 `language` 从 `"en"` 改为 `"zh"`，store 随后通知订阅者。包装组件重新读取 state 并把 `language: "zh"` 传给类组件，标题显示“语言：zh”；点 “English” 则沿相同路径回到 `"en"`。

旧版本常把注入的 props 手工组合成接口；`ConnectedProps` 可从 connector 推导这些属性。React-Redux 9.3.0 起把 `connect` 标为 deprecated，但仍保留该接口；本文的 `legacy_connect as connect` 是维护入口，新函数组件优先用 hooks。React Router v5 的 `withRouter` 是另一种旧式高阶组件（HOC），不参与本例；当前项目的路由 API 见[React 路由章节](../../../../frontend/frameworks/react-routing-and-navigation.md)。

旧 react-redux 版本可能需要外置 @types/react-redux；react-redux 9 已自带类型声明。升级前按实际锁文件版本核对，不要把旧 DefinitelyTyped 包直接加到新版本。

> [!info]- 来源
> - `legacy_connect` 是 9.3.0 起 deprecated `connect` 的显式别名；对象形式的 `mapDispatchToProps` 会将 action creators 绑定到 store dispatch：[connect API](https://redux.js.org/react-redux/api/connect)，官方文档，核对日期：2026-11-13。`ConnectedProps` 的类型推导：[Typing connect with TypeScript](https://redux.js.org/react-redux/using-react-redux/usage-with-typescript)。
> - `<Provider store={store}>` 让后代 `connect` 组件通过 React Context 使用同一个 store：[Provider](https://redux.js.org/react-redux/api/provider)，官方文档，核对日期：2026-11-13。
> - 新组件的 typed hooks（类型化 hooks）：[Redux Usage with TypeScript](https://redux.js.org/usage/usage-with-typescript#define-typed-hooks)。
> - 验证包版本：React-Redux 9.3.1、React / React DOM 19.3.1、Redux 5.0.1；2026-11-13 查询官方 npm package registry，且以 React-Redux 9.3.1 实际挂载验证。
