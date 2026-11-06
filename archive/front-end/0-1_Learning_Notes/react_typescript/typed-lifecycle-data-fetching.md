# React 类组件如何在生命周期中请求数据？

这个类组件示例适合维护仍使用生命周期方法的项目；React 当前 Effect 的 setup、cleanup 与过期响应流程见[React 更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)。type annotation（类型注解）只描述编译器预期，网络 JSON 仍要按业务结构运行时校验；见[TypeScript 不可信 JSON 入口](../../../../frontend/typescript/advanced-typescript.md)。

~~~tsx
import { Component } from "react";

type State = {
  status: "loading" | "ready" | "error";
  data: unknown;
  error: string | null;
};

export class ReportSnapshot extends Component<{}, State> {
  state: State = { status: "loading", data: null, error: null };
  private controller: AbortController | null = null;

  componentDidMount() {
    const controller = new AbortController();
    this.controller = controller;

    void (async () => {
      try {
        const response = await fetch("/api/reports/snapshot", {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("HTTP " + response.status);

        const result: unknown = await response.json();
        if (!controller.signal.aborted) {
          this.setState({ status: "ready", data: result, error: null });
        }
      } catch (cause) {
        if (!controller.signal.aborted) {
          this.setState({
            status: "error",
            data: null,
            error: cause instanceof Error ? cause.message : String(cause),
          });
        }
      }
    })();
  }

  componentWillUnmount() {
    this.controller?.abort();
    this.controller = null;
  }

  render() {
    const { status, data, error } = this.state;
    if (status === "error") return <p role="alert">{error}</p>;
    if (status === "loading") return <p role="status">正在读取报表…</p>;
    return <pre>{JSON.stringify(data, null, 2)}</pre>;
  }
}
~~~

每次挂载都创建自己的 AbortController，卸载时取消客户端读取；根 StrictMode 在开发期可额外做一次挂载、卸载、再挂载检查，因此请求要能安全清理。状态用独立的 `status` 区分 loading 与数据值，因为 JSON `null` 也是合法响应，不能拿它充当加载哨兵。`controller.signal.aborted` 阻止已取消的闭包更新组件，但服务端可能已经开始处理请求。

> [!info]- 来源
> - componentDidMount、componentWillUnmount 与严格模式检查：[React Component](https://react.dev/reference/react/Component#componentdidmount)、[React StrictMode](https://react.dev/reference/react/StrictMode)，React 19.3 文档，核对日期：2026-11-06。
> - Fetch AbortSignal 与 HTTP 状态：[MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)、[MDN Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)，核对日期：2026-11-06。
