# 旧类组件怎样通过 connect 读取 Redux？

当前函数组件的 Redux hooks、类型推导和 Provider 入口见[Redux 如何组织共享界面状态与异步工作？](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。本页保留 react-redux connect 与类组件的维护模式，便于阅读旧项目；它不需要和 Hook 版本并排用于新组件。

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

mapStateToProps 选择 store 中组件要显示的字段，mapDispatchToProps 把更新 action 暴露为 props。旧版本常把注入的 props 手工组合成接口；ConnectedProps 可从 connector 推导这些属性。React Router v5 的 withRouter 是另一层旧式 HOC；当前项目的路由 API 见[React 路由章节](../../../../frontend/frameworks/react-routing-and-navigation.md)。

React-Redux 9.3.0 起将 `connect` 标为 deprecated，并提供 `legacy_connect` 作为同一旧式接口的显式维护入口。这个示例用别名把它写作 `connect`，方便阅读旧代码；新组件优先使用 typed hooks。

旧 react-redux 版本可能需要外置 @types/react-redux；react-redux 9 已自带类型声明。升级前按实际锁文件版本核对，不要把旧 DefinitelyTyped 包直接加到新版本。

> [!info]- 来源
> - connect 与 ConnectedProps：[React-Redux Usage with TypeScript](https://react-redux.js.org/using-react-redux/usage-with-typescript)、[connect API](https://react-redux.js.org/api/connect)，React-Redux 9.3.1 文档，核对日期：2026-11-06。
> - React-Redux 9.1 起 typed hooks 可用 withTypes：[React-Redux Usage with TypeScript](https://react-redux.js.org/using-react-redux/usage-with-typescript)，见当前 Redux canonical。
