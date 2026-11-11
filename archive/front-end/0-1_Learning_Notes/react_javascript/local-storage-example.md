# React 组件怎样读写少量浏览器偏好？

**案例背景。** 报表页面让用户切换“紧凑列”显示，并在刷新后保留这个小型偏好。下面用 localStorage（本地存储）的字符串 API（应用程序编程接口）保存 JSON（JavaScript 对象表示法），同时检查读回的数据形状。它适合这类非敏感、可重建的界面偏好；存储作用域、跨标签页事件和安全边界见[报表页面里的状态应该放在哪里？](../../../../frontend/browser-apis/browser-storage-and-communication.md)，Effect（副作用）的提交时序见[更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)。

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
      return {
        compactColumns: (value as { compactColumns: boolean }).compactColumns,
      };
    }
  } catch {
    // 浏览器策略可能禁止读取，或保存内容不是有效 JSON。
  }
  return { compactColumns: false };
}

export function ReportPreferences() {
  // 仅用于不做服务端/预渲染的浏览器专属 React 树。
  const [preferences, setPreferences] = useState(readPreferences);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        "reports:preferences",
        JSON.stringify(preferences)
      );
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
          setPreferences(previous => ({
            ...previous,
            compactColumns: checked,
          }));
        }}
      />
      紧凑列
    </label>
  );
}
~~~

读取时，`getItem`（读取存储项）在键不存在时返回 null。键存在时，代码调用 `JSON.parse` 并把解析结果放进 `unknown`（未知类型），再确认它是非数组对象且 `compactColumns` 确实为布尔值。键不存在、JSON 语法无效或字段形状不匹配时，页面都采用“非紧凑列”的默认值。本例把 `reports:preferences` 当作只由这个偏好拥有的完整记录：state（状态）只保留已检查的 `compactColumns`，不会把整个未验证对象当作 `Preferences` 使用，写入也只序列化这个字段。

这段 `Effect` 在首次提交后就会尝试保存，不必等用户点击。若原值是 `{"compactColumns":true,"other":"keep?"}`，首屏勾选，首次保存后只剩 `{"compactColumns":true}`，other 会被删除；若键不存在，首次保存会创建并写入 `{"compactColumns":false}`；若 JSON 无效或形状不匹配，首次保存会用默认对象覆盖它。勾选事件的 `onChange` 处理器读取当前 `checked` 并安排 `state` 更新，下一次 render（渲染）先反映新选择，再由 `Effect` 写入。写入失败时当前页面仍可继续切换；刷新后会读到上一次成功写入且仍可读取的值，否则回退默认值。若应用只想在用户明确修改时保存，应在事件处理器中根据新 `checked` 形成下一份偏好并保存，而不是保留这个“首次提交也保存”的策略。

## 纯浏览器渲染与 server-side rendering（服务端渲染，SSR）的区别

上面的惰性初始化函数会在首次 `render` 期间读取 `window.localStorage`；它只适用于完全在浏览器渲染的树。把这段代码放进服务端 render 时，try/catch 只会捕获 window 不存在的错误并返回默认值；它并不会让这段惰性初始化变成 SSR 安全，因为浏览器首次 render 可能读取到已保存的真值，与服务器的默认值不同，造成水合不匹配。读取访问 `localStorage` 本身也可能受浏览器策略限制而抛出 `SecurityError`；写入可能因策略或空间限制而抛出 `QuotaExceededError`。两个操作都被各自的 try/catch 覆盖：读取失败时回退默认值，写入失败时仍可在当前页面继续切换偏好。

水合要求服务器和浏览器首次输出一致。本例可让两端先使用同一个固定默认值，水合后再由读取 Effect 访问存储。为了不让写入 Effect 把默认值盖回去，可加一个初始为 false 的 loaded（已读取）状态：读取 Effect 用空依赖数组运行，安排 `setPreferences(readPreferences())` 和 `setLoaded(true)`；写入 Effect 依赖 `preferences` 与 `loaded`，在 `loaded=false` 时直接返回。

假设存储中已保存 `compactColumns=true`，而固定默认值为 false。两次客户端提交如下；表中的值属于该次 render 捕获的 state：

| 时点 | 本次捕获的值 | 读取与写入怎样交接 |
|---|---|---|
| 服务端与浏览器首次 render | `compactColumns=false`，`loaded=false` | 都先生成相同的非紧凑界面；服务端不运行 Effect。 |
| 浏览器首次提交后的 Effect | 仍是 `false`、`false` | 读取安排两项状态更新；写入仍看到 `loaded=false`，跳过保存。 |
| 更新后的下一次提交 | `compactColumns=true`，`loaded=true` | 界面已采用存储值，写入 Effect 才保存这份偏好；空依赖的读取 Effect 无需因本次状态更新重跑。 |

setter 不会改写当前提交已经捕获的值，因而不能仅靠“读取 Effect 排在写入 Effect 前面”防止覆盖。若只在用户修改时保存，也可把写入留在事件处理器中。这两种 SSR 方案都可能先显示默认值，读取后再切换为已保存值。Next.js 的“use client”边界仍可能在首次加载时预渲染 HyperText Markup Language（超文本标记语言，HTML）；框架说明见[服务端与客户端组件在哪条线交接](../../../../frontend/frameworks/next-js.md#服务端与客户端组件在哪条线交接)。

React 推荐 state 初始化函数保持纯净。上面这段初始化函数读取可能变化的浏览器存储，因此不是一般的纯计算；本例只为纯浏览器渲染而选择在首次 render 同步读偏好，让首屏直接采用已保存值。开发 StrictMode（严格模式）可能重复调用它，组件不能依赖“只读取一次”；初始化函数只读不写。需要保持纯初始化或支持 SSR 时，使用前一节的固定默认值和客户端读取流程。Effect 在服务端不运行；根节点开启开发 StrictMode 时，首次 Effect 还会额外经历一次建立和清理，再正式建立。如果两次写入同一字符串，且期间存储值未变，HTML 存储规范规定 `setItem` 不会再次修改值或广播 `storage` 事件。

> [!info]- 来源
> - 浏览器存储的字符串 API、缺失键返回 null、localStorage 访问可能抛 SecurityError、写入可能抛 QuotaExceededError，以及重复写同一值不广播：[WHATWG HTML Standard — Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，Living Standard，核验日期：2026-11-12。
> - 惰性初始化函数应保持纯净，开发 StrictMode 会额外调用初始化函数：[React useState](https://react.dev/reference/react/useState)，React 19.3 文档，核验日期：2026-11-12。
> - Effect 只在客户端运行，根 StrictMode 首次挂载会额外执行一次建立/清理：[React useEffect](https://react.dev/reference/react/useEffect)，React 19.3 文档，核验日期：2026-11-12。
> - 水合要求服务端与浏览器首次输出一致：[React hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)，React 19.3 文档，核验日期：2026-11-12。
> - Next.js 客户端组件可使用浏览器 API，但首次加载仍预渲染 HTML：[Next.js Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)，Latest 16.4.6，核验日期：2026-11-12。
