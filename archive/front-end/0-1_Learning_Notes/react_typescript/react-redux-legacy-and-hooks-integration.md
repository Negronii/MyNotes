# How do class and function components connect to Redux? / 类组件和函数组件如何连接 Redux？

The archived examples contrast the legacy `connect`/class pattern with Hooks-based selectors and dispatch. The class sample is tied to React Router v5 `withRouter`; current Router v6 code uses a different routing API. / 归档示例对照旧式 `connect`/类组件模式与基于 Hook 的 selector/dispatch。类组件示例依赖 React Router v5 的 `withRouter`；当前 v6 使用不同路由 API。

## React-Redux Integration: Class and Function Components / 类组件与函数组件中的React-Redux

This section preserves both the older `connect`/higher-order-component integration and the Hooks-based integration. The class example uses React Router v5 APIs; keep that version boundary explicit when maintaining an existing application.

## Prerequisites

Before you start, make sure you have the React-Redux library installed. If not, you can install it using npm:

```bash
npm install react-redux
```

Older React-Redux releases relied on a separate DefinitelyTyped package. Current React-Redux releases include their own types, so check the installed major before adding this legacy package:

```bash
npm install @types/react-redux --save-dev
```

The class example below also uses React Router v5's `withRouter` API; it is kept as a legacy integration example, separate from the v6 declarative routing section above.

## React-Redux with Class Components

### Setting up the Provider

The `<Provider />` component makes the Redux store available to the rest of your app. Here’s how you set it up:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import store from "./redux/store";
import App from "./App";

const root = createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);
```

### Connecting the Component

Use the `connect` function to connect your component to the Redux store. This involves defining `mapStateToProps` and `mapDispatchToProps` functions:

```tsx
import { connect } from "react-redux";
import { Dispatch } from "redux";
import i18n from "../../configs";
import { changeLanguageActionCreator } from "./redux/language/languageActions";
import { RootState } from "./redux/store";

const mapStateToProps = (state: RootState) => ({
  language: state.language,
  languageList: state.languageList,
});

const mapDispatchToProps = (dispatch: Dispatch) => ({
  changeLanguage: async (code: "zh" | "en") => {
    await i18n.changeLanguage(code);
    const action = changeLanguageActionCreator(code);
    dispatch(action);
  },
});
```

### Modifying the Component

Modify the class component to receive props injected by `connect` and handle type definitions accordingly:

```tsx
import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { withTranslation, WithTranslation } from "react-i18next";

class HeaderComponent extends React.Component<
  RouteComponentProps &
    WithTranslation &
    ReturnType<typeof mapStateToProps> &
    ReturnType<typeof mapDispatchToProps>
> {
  menuClickHandler = (e: any) => {
    this.props.changeLanguage(e.key);
  };

  render() {
    return (
      <div>
        <h1>{this.props.language}</h1>
        <button onClick={() => this.menuClickHandler({ key: 'en' })}>English</button>
        <button onClick={() => this.menuClickHandler({ key: 'zh' })}>中文</button>
      </div>
    );
  }
}

export const Header = connect(
  mapStateToProps,
  mapDispatchToProps
)(withTranslation()(withRouter(HeaderComponent)));
```

### Modifying the Store Type

Ensure your store is correctly typed to provide robust type checking and intellisense support:

```typescript
import { createStore } from "redux";
import languageReducer from "./redux/language/languageReducer";

const store = createStore(languageReducer);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
```

## React-Redux with Function Components

### Creating a hooks.ts File

Create a `hooks.ts` file to define custom hooks for accessing the Redux store:

```typescript
import { useSelector as useReduxSelector, TypedUseSelectorHook } from "react-redux";
import { RootState } from "./store";

export const useSelector: TypedUseSelectorHook<RootState> = useReduxSelector;
```

### Using useSelector and useDispatch

In functional components, use `useSelector` to access the state and `useDispatch` to dispatch actions:

```typescript
import React from "react";
import { useSelector } from "../../redux/hooks";
import { useDispatch } from "react-redux";
import i18n from "../../configs";
import { changeLanguageActionCreator } from "../../redux/language/languageActions";

export const Header: React.FC = () => {
  const language = useSelector((state) => state.language);
  const languageList = useSelector((state) => state.languageList);
  const dispatch = useDispatch();

  const menuClickHandler = async (e: any) => {
    const languageCode = e.key as "zh" | "en";
    await i18n.changeLanguage(languageCode);
    dispatch(changeLanguageActionCreator(languageCode));
  };

  return (
    <div>
      <h1>{language}</h1>
      <button onClick={() => menuClickHandler({ key: 'en' })}>English</button>
      <button onClick={() => menuClickHandler({ key: 'zh' })}>中文</button>
    </div>
  );
};
```

In this setup, `useSelector` hooks access the Redux store state, and `useDispatch` dispatches actions. This approach simplifies state management in function components.

## Conclusion

This guide covers the integration of React-Redux with both class and function components using modern best practices. By following these steps, you can ensure a robust, type-safe, and scalable integration of Redux into your React application.

For more information and advanced usage, refer to the official [React-Redux documentation](https://react-redux.js.org/introduction/getting-started).

**Reference / 参考：** [React-Redux TypeScript usage](https://react-redux.js.org/using-react-redux/usage-with-typescript).
