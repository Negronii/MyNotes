# React Effect 如何清理请求与浏览器订阅？

**案例背景。** 报表列表当前按 `recent` 排序。用户改选 `oldest` 后，组件需要读取相应数据；如果用户很快又改回 `recent`，两个请求可能乱序返回。此页用手写 Effect（副作用同步）演示如何清理旧请求、忽略过期结果，并保留一个浏览器事件订阅例子。Effect 的完整提交时序见[React 如何把一次用户操作变成界面更新？](../../../../frontend/frameworks/react-basics.md#Effect%E5%9C%A8%E6%8F%90%E4%BA%A4%E5%90%8E%E5%90%8C%E6%AD%A5%E5%A4%96%E9%83%A8%E7%B3%BB%E7%BB%9F)；要缓存、去重和协调服务端数据时，应接着看[React 如何维护服务端数据与乐观更新？](../../../../frontend/frameworks/react-server-state-and-optimistic-updates.md)。

Effect 用于让已提交的界面与 React 外部系统同步。由用户动作直接触发的工作通常放在事件处理器里；能由当前 props（属性）和 state（状态）算出的值则在 render（渲染）中计算。这里的 `sort` 是 prop，也可能因地址栏后退而改变，所以组件需要在它变化后读取对应报表。

## 请求变化后，旧响应不能覆盖新结果

以下代码假定 `fetchReports` 把收到的 `AbortSignal` 传给 `fetch` 或其他可中止操作。每轮 Effect 都有自己的 `active` 标记和 `AbortController`：cleanup（清理函数）先禁止这轮闭包再写入 state（状态），再向底层读取发出中止信号。若底层函数不理会 signal，`active` 仍会挡住旧响应；中止浏览器端读取也不保证服务端已经停止处理请求。

~~~tsx
import { useEffect, useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type RequestState =
  | { sort: SortOrder; status: "pending" | "success" }
  | { sort: SortOrder; status: "error"; message: string };

declare function fetchReports(
  sort: SortOrder,
  signal: AbortSignal
): Promise<Report[]>;

function ReportRows({ sort }: { sort: SortOrder }) {
  const [result, setResult] = useState<{
    sort: SortOrder;
    rows: Report[];
  } | null>(null);
  const [request, setRequest] = useState<RequestState | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setRequest({ sort, status: "pending" });

    async function load() {
      try {
        const rows = await fetchReports(sort, controller.signal);
        if (active) {
          setResult({ sort, rows });
          setRequest({ sort, status: "success" });
        }
      } catch (cause) {
        if (active) {
          setRequest({
            sort,
            status: "error",
            message: cause instanceof Error ? cause.message : String(cause),
          });
        }
      }
    }

    void load();
    return () => {
      active = false;
      controller.abort();
    };
  }, [sort]);

  const currentRequest = request?.sort === sort ? request : null;

  return (
    <section aria-busy={!currentRequest || currentRequest.status === "pending"}>
      {(!currentRequest || currentRequest.status === "pending") && (
        <p role="status">正在读取 {sort} 排序的报表…</p>
      )}
      {currentRequest?.status === "error" && (
        <p role="alert">读取 {sort} 排序失败：{currentRequest.message}</p>
      )}
      {result && (
        <>
          <p>下方列表是最近一次成功读取的 {result.sort} 排序结果。</p>
          <ul>
            {result.rows.map(row => <li key={row.id}>{row.period}</li>)}
          </ul>
        </>
      )}
    </section>
  );
}
~~~

假定首次 `recent` 读取已经成功，之后用户每次改选都分别提交一次。选择 `oldest` 后，React 先清理 `recent` 那轮 Effect，再发出 `oldest` 请求；界面报告它正在读取，同时保留最近一次成功的 `recent` 列表。若 `oldest` 还没返回，用户又切回 `recent`，React 先清理 `oldest` 那轮，再发出第二次 `recent` 请求；界面仍保留第一次成功的 `recent` 结果，并报告当前读取进度。第二次 `recent` 成功后，才以它替换列表。随后迟到的 `oldest` 成功或失败都不能改写组件状态。

每当新的 `sort` 已提交并触发 Effect 重跑，React 先执行旧清理，再用新值建立请求；组件卸载时也会执行当前轮清理。cleanup（清理函数）先把本轮 `active` 设为 `false`，再中止本轮 signal。旧请求在清理后才成功或失败，都不能再写回；若当前请求失败，上方错误提示独立说明失败；若已有列表，下方仍标为最近一次成功读取的排序。`fetchReports` 必须把 signal 传到底层读取，中止才有机会停止浏览器侧工作；对不支持中止的异步来源，`active` 检查仍能挡住过期结果。

根部启用 StrictMode（严格模式）时，React 在开发环境会先额外执行一次建立和清理，再正式建立 Effect。两个例子都应能经受重复建立和清理。

新项目若已有路由或框架数据读取机制，应优先使用它；直接在 Effect 里读取数据通常还需要自行补缓存、去重、预取和水合处理。这个手写模式适合维护已有客户端组件或解释请求清理，不是每个数据加载场景的默认方案。

## 订阅浏览器事件，并在组件离开时退订

浏览器状态也是 Effect 可同步的外部系统。下面的 Hook（钩子）在组件首次于客户端提交后读取文档可见状态，并订阅 `visibilitychange`；卸载时用同一个回调移除监听器。它只表示当前文档是可见还是隐藏，不代表网络可达或服务端状态。

~~~tsx
import { useEffect, useState } from "react";

function usePageVisibility() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    function updateVisibility() {
      setIsVisible(document.visibilityState === "visible");
    }

    document.addEventListener("visibilitychange", updateVisibility);
    updateVisibility();
    return () => {
      document.removeEventListener("visibilitychange", updateVisibility);
    };
  }, []);

  return isVisible;
}
~~~

初始值不在 render 阶段读取 `document`，所以 server-side rendering（服务端渲染，SSR）的输出与浏览器首次 render 可以一致。首次渲染的值先是 `false`；hydration（水合）后，Effect 注册监听器并立即读取当前值，若文档可见就更新为 `true`。`removeEventListener` 使用与注册时相同的事件类型、回调身份和捕获选项；本例两处都省略 `capture`，所以采用默认的 `false`。窗口尺寸监听的同类 Hook 例子见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md#%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89Hook%E5%A4%8D%E7%94%A8%E7%8A%B6%E6%80%81%E8%A1%8C%E4%B8%BA)。

> [!info]- 来源
> - Effect 的依赖、建立/清理顺序、开发 StrictMode 检查、以及用户动作/派生值通常不需要 Effect：[React `useEffect`](https://react.dev/reference/react/useEffect)、[用 Effect 同步](https://react.dev/learn/synchronizing-with-effects)、[哪些情况不需要 Effect](https://react.dev/learn/you-might-not-need-an-effect)，React 19.3 文档，核验日期：2026-11-12。
> - `AbortSignal` 中止浏览器 Fetch 的行为：[WHATWG Fetch Standard，Abort fetch](https://fetch.spec.whatwg.org/#abort-fetch)，Living Standard，核验日期：2026-11-12。
> - 文档可见状态与 `visibilitychange` 事件：[WHATWG HTML Standard，页面可见性](https://html.spec.whatwg.org/multipage/interaction.html#page-visibility)，Living Standard，核验日期：2026-11-12。
> - 监听器按事件类型、回调和捕获选项匹配以移除：[WHATWG DOM Standard，`removeEventListener`](https://dom.spec.whatwg.org/#dom-eventtarget-removeeventlistener)，Living Standard，核验日期：2026-11-12。
