# React Effect 如何清理请求与浏览器订阅？

这页保留手写 Effect 的请求取消片段。React 当前更新轮次、依赖变化时的 cleanup 与过期响应边界见[React 如何把一次用户操作变成界面更新？](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)；服务端报表读取优先看[React 如何维护服务端数据与乐观更新？](../../../../frontend/frameworks/react-server-state-and-optimistic-updates.md)。

下面的请求假定 fetchReports 会把收到的 AbortSignal 传给底层 fetch。cleanup 同时禁止旧闭包写入 state，并请求停止浏览器侧的读取；服务端可能已经收到请求，不能由此推断服务端工作也停止了。

~~~tsx
import { useEffect, useState } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };

declare function fetchReports(
  sort: SortOrder,
  signal: AbortSignal
): Promise<Report[]>;

function ReportRows({ sort }: { sort: SortOrder }) {
  const [rows, setRows] = useState<Report[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function load() {
      try {
        const nextRows = await fetchReports(sort, controller.signal);
        if (active) {
          setRows(nextRows);
          setError(null);
        }
      } catch (cause) {
        if (active && !controller.signal.aborted) {
          setError(cause instanceof Error ? cause.message : String(cause));
        }
      }
    }

    void load();
    return () => {
      active = false;
      controller.abort();
    };
  }, [sort]);

  if (error) return <p role="alert">{error}</p>;
  return <ul>{rows.map(row => <li key={row.id}>{row.period}</li>)}</ul>;
}
~~~

Effect 适合让已经提交的界面与外部系统同步；由用户动作直接触发的工作通常放在事件处理器中，能从当前 props/state 算出的值则在 render 中计算。窗口订阅的 cleanup 示例见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md#用自定义hook复用状态行为)。

> [!info]- 来源
> - Effect setup、cleanup 与依赖变化：[React useEffect](https://react.dev/reference/react/useEffect)，React 19.3 文档，核对日期：2026-11-06。
> - 请求结果与当前排序同步的主线：[React 基础章节](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)，React 19.3，核对日期：2026-11-06。
