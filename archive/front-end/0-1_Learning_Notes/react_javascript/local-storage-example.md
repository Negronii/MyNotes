# React 组件怎样读写少量浏览器偏好？

这段练习保存一个小型列显示偏好，展示 localStorage 字符串和 JSON 序列化的连接方式。存储作用域、容量、跨标签页事件和安全边界见[报表页面里的状态应该放在哪里？](../../../../frontend/browser-apis/browser-storage-and-communication.md)；React 的 Effect 时序见[更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)。

~~~tsx
import { useEffect, useState } from "react";

type Preferences = { compactColumns: boolean };

function readPreferences(): Preferences {
  try {
    const saved = window.localStorage.getItem("reports:preferences");
    if (saved === null) return { compactColumns: false };

    const value: unknown = JSON.parse(saved);
    if (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value) &&
      typeof (value as Record<string, unknown>).compactColumns === "boolean"
    ) {
      return { compactColumns: (value as { compactColumns: boolean }).compactColumns };
    }
  } catch {
    // 浏览器策略可能禁止访问，或已存内容不是有效 JSON。
  }
  return { compactColumns: false };
}

export function ReportPreferences() {
  // 这个 lazy initializer 只适用于纯浏览器渲染。
  const [preferences, setPreferences] = useState(readPreferences);

  useEffect(() => {
    try {
      window.localStorage.setItem("reports:preferences", JSON.stringify(preferences));
    } catch {
      // 存储不可用时仍保留当前页面内存中的偏好。
    }
  }, [preferences]);

  return (
    <label>
      <input
        type="checkbox"
        checked={preferences.compactColumns}
        onChange={event => {
          const checked = event.currentTarget.checked;
          setPreferences(previous => ({ ...previous, compactColumns: checked }));
        }}
      />
      紧凑列
    </label>
  );
}
~~~

在服务端渲染或预渲染页面中，render 阶段不能读取 window，而且服务端输出与浏览器首次 render 必须一致。应先用稳定的初始值完成水合，再在 Effect 中读取偏好并更新界面；此时可能出现一次偏好加载后的界面变化。若按这种 SSR 路径改写，持久化 Effect 应等首次读取完成后才允许写入，或只在用户修改后写；否则初始默认值可能先覆盖已存偏好。Next.js 对浏览器专属值与水合边界的说明见[服务端与客户端组件在哪条线交接](../../../../frontend/frameworks/next-js.md#服务端与客户端组件在哪条线交接)。

读取时的 catch 处理存储访问与 JSON 解析失败，写入时的 catch 处理存储写入失败；读取失败会回退默认值，写入失败会保留当前页面内存中的偏好，但刷新后无法恢复。它们不证明存储数据可信，也不会绕过浏览器策略。React 根节点处于开发 StrictMode 时，Effect 可能额外执行一次 setup/cleanup 检查；它不是生产环境持久化语义。

> [!info]- 来源
> - 浏览器存储字符串 API 与读写限制：[WHATWG HTML Standard — Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，核对日期：2026-11-06。
> - 首次 render 与 Effects 不在服务端运行、水合必须匹配：[React useEffect](https://react.dev/reference/react/useEffect)、[Next.js Server/Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)，React 19.3 与 Next.js 16.4.5 文档，核对日期：2026-11-06。
