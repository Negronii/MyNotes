# i18next 怎样为 React 提供语言切换？

i18next 保存语言资源与翻译规则，react-i18next 把翻译函数接到 React 组件。当前函数组件可用 useTranslation 读取 t 与 i18n；切换语言调用 changeLanguage。语言资源的实际加载方式由配置的 backend 和 namespace 决定。

在应用入口先导入 `./i18n`，启动一次实例初始化；不要在组件 render 中反复初始化：

~~~typescript
// i18n.ts
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: { title: "Reports" } },
    zh: { translation: { title: "报表" } },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    // React 把翻译文本作为文本节点输出；这不允许把不可信 HTML 交给危险 HTML API。
    escapeValue: false,
  },
});

export default i18n;
~~~

组件只展示语言切换和翻译。语言选项属于本例的界面设置；当用户选择中文时，`changeLanguage` 切换语言，Hook 默认订阅的 `languageChanged` 事件触发组件重新渲染；`t("title")` 因而从 `Reports` 变成「报表」。切回 English 后再使用英文资源。

~~~tsx
import { useTranslation } from "react-i18next";

export function ReportHeader() {
  const { t, i18n, ready } = useTranslation("translation", {
    useSuspense: false,
  });

  if (!ready) return <p role="status">正在加载语言资源…</p>;

  return (
    <header>
      <h1>{t("title")}</h1>
      <button
        type="button"
        onClick={() => void i18n.changeLanguage("en")}
      >
        English
      </button>
      <button
        type="button"
        onClick={() => void i18n.changeLanguage("zh")}
      >
        中文
      </button>
    </header>
  );
}
~~~

默认情况下，useTranslation 在所需 namespace 尚未就绪时可触发 Suspense；示例以 `useSuspense: false` 显式关闭它，才由组件读取 `ready` 显示加载状态。若开启 Suspense，应在组件外提供匹配的边界。使用 backend 动态加载资源时，应通过 `failedLoading` 事件或错误回调处理资源失败；不要假定 `changeLanguage` 的 Promise 拒绝就能表示加载失败。入口的导入只启动初始化；若资源来自异步 backend，仍需这些就绪机制等待加载完成。

旧课程把语言代码同时写入 Redux，再调用 i18n.changeLanguage。若业务确实需要两个系统都读取语言代码，应把外部语言切换放在事件处理器或 thunk 中，并明确失败时的协调策略；reducer 只应计算下一个 Redux state。通常由 i18next 持有当前语言即可，避免两份可独立修改的值彼此不同步。Redux 的 action、reducer 与异步工作流见[共享界面状态章节](../../../../frontend/frameworks/redux-state-and-async-workflows.md)。

类组件项目仍可维护 withTranslation 高阶组件；新函数组件优先用 Hook。React Router v5 的 withRouter 等旧组合不应拼入当前路由代码，参见[React 路由章节](../../../../frontend/frameworks/react-routing-and-navigation.md)。

> [!info]- 来源
> - 初始化 React 绑定与插值：[i18next React Integration](https://react.i18next.com/latest/using-with-hooks)、[i18next Interpolation](https://www.i18next.com/translation-function/interpolation)，i18next 26.7.2、react-i18next 17.1.13 官方文档，核对日期：2026-11-06。
> - useTranslation、ready、Suspense 与 changeLanguage：[react-i18next useTranslation](https://react.i18next.com/latest/usetranslation-hook)，官方文档，核对日期：2026-11-06。
> - 资源加载错误回调与 `failedLoading` 事件：[i18next API — changeLanguage and Events](https://www.i18next.com/overview/api)，i18next 26.7.2 官方文档，核对日期：2026-11-06。
> - reducer 不应执行副作用：[Redux Style Guide — Reducers Must Not Have Side Effects](https://redux.js.org/style-guide/#reducers-must-not-have-side-effects)，Redux 官方指南，核对日期：2026-11-06。
