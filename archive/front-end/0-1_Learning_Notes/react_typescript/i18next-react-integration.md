# How can i18next provide language selection in React? / i18next 如何在 React 中提供语言选择？

Initialize i18next with locale resources and the React binding, then use `useTranslation` or the legacy translation HOC in components. When Redux also stores the selected language, keep the reducer pure and coordinate the external language change in the event handler. / 使用语言资源初始化 i18next 和 React 绑定，再在组件中使用 `useTranslation` 或旧式翻译 HOC。若 Redux 也保存当前语言，reducer 应保持纯函数，并在事件处理器中协调外部语言切换。

## Internationalization with i18next / 使用i18next实现国际化

This guide shows a basic i18next configuration and its React bindings from `react-i18next`.

## Installation

To install i18Next and its React integration, run the following command in your terminal:

```bash
npm install react-i18next i18next --save
```

## Configuration

### Step 1: Create a Configuration File

1. Create a `configs.ts` (or `configs.js` for JavaScript) file in your project directory.

2. Import the necessary modules:

```tsx
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
```

### Step 2: Create Language JSON Files

1. Create language JSON files (e.g., `en.json` for English, `zh.json` for Chinese) in your project directory. These files will contain your translations.

### Step 3: Import Language JSON Files

1. Import the language JSON files into `configs.ts`:

```tsx
import translation_en from "./locales/en.json";
import translation_zh from "./locales/zh.json";
```

### Step 4: Set Up i18Next Configuration

1. Set up your i18Next configuration:

```tsx
const resources = {
  en: {
    translation: translation_en,
  },
  zh: {
    translation: translation_zh,
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en",
    fallbackLng: "en", // Fallback language if the current language translation is not available
    interpolation: {
        escapeValue: false, // React escapes text output; this does not make HTML injection safe.
    },
  });

export default i18n;
```

## Usage in React Components

### Class Components

1. Import the `withTranslation` higher-order component (HOC) and `WithTranslation` type from `react-i18next`:

```tsx
import { withTranslation, WithTranslation } from "react-i18next";
```

2. Add `WithTranslation` to your component's props type:

```tsx
class HeaderComponent extends React.Component<RouteComponentProps & WithTranslation, State> {
  ...
}
```

3. In your component's render function, extract the `t` function from the props. This function is used to translate your text:

```tsx
render() {
  const { t } = this.props;
  return (
    <div>
      <Typography.Text>{t("header.slogan")}</Typography.Text>
      <Dropdown.Button>
        {this.state.language === "en" ? "English" : "中文"}
      </Dropdown.Button>
    </div>
  );
}
```

4. Wrap your component with the `withTranslation` HOC when exporting:

```tsx
export const Header = withTranslation()(withRouter(HeaderComponent));
```

### Functional Components

1. In functional components, you can use the `useTranslation` hook instead of the `withTranslation` HOC:

```tsx
import { useTranslation } from "react-i18next";

export const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Layout.Footer>
      <Typography.Title level={3} style={{ textAlign: "center" }}>
        {t("footer.detail")}
      </Typography.Title>
    </Layout.Footer>
  );
};
```

## Redux Integration

To ensure strong typing for your Redux actions, you can use action creators. Here's an example of how to do this for language-related actions:

### Action Creators

1. Define action types and creators:

```tsx
export const CHANGE_LANGUAGE = "change_language";

interface ChangeLanguageAction {
  type: typeof CHANGE_LANGUAGE;
  payload: "zh" | "en";
}

export type LanguageActionTypes = ChangeLanguageAction;

export const changeLanguageActionCreator = (
  languageCode: "zh" | "en"
): ChangeLanguageAction => ({
  type: CHANGE_LANGUAGE,
  payload: languageCode,
});
```

### Reducers

1. In your reducer, handle different actions by setting the action type to `LanguageActionTypes`:

```tsx
import { CHANGE_LANGUAGE, LanguageActionTypes } from "./languageActions";

export interface LanguageState {
  language: "en" | "zh";
  languageList: { name: string; code: string }[];
}

const defaultState: LanguageState = {
  language: "en",
  languageList: [
    { name: "中文", code: "zh" },
    { name: "English", code: "en" },
  ],
};

export default (state = defaultState, action: LanguageActionTypes): LanguageState => {
  switch (action.type) {
    case CHANGE_LANGUAGE:
      return { ...state, language: action.payload };
    default:
      return state;
  }
};
```

### Usage in Components

1. Change the i18next language in the event handler, then dispatch the plain action. Keep the reducer pure; it only updates Redux state ([Redux reducer rules](https://redux.js.org/style-guide/#reducers-must-not-have-side-effects)):

```typescript
import i18n from "./configs";

const menuClickHandler = async (e: any) => {
  const languageCode = e.key as "zh" | "en";
  await i18n.changeLanguage(languageCode);
  store.dispatch(changeLanguageActionCreator(languageCode));
};
```

### Example Component

1. Here is how you might integrate everything in a sample component:

```tsx
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { Menu } from "antd";
import { changeLanguageActionCreator } from "./languageActions";
import i18n from "./configs";

const LanguageSwitcher: React.FC = () => {
  const dispatch = useDispatch();
  const language = useSelector((state: any) => state.language);

  const handleMenuClick = async (e: any) => {
    const languageCode = e.key as "zh" | "en";
    await i18n.changeLanguage(languageCode);
    dispatch(changeLanguageActionCreator(languageCode));
  };

  return (
    <Menu onClick={handleMenuClick} selectedKeys={[language]}>
      <Menu.Item key="en">English</Menu.Item>
      <Menu.Item key="zh">中文</Menu.Item>
    </Menu>
  );
};

export default LanguageSwitcher;
```

**References checked 2026-10-15:** [i18next interpolation](https://www.i18next.com/translation-function/interpolation), [Redux reducer rules](https://redux.js.org/style-guide/#reducers-must-not-have-side-effects).
