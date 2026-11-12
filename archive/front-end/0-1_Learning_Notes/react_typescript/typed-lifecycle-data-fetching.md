# React 类组件如何在生命周期中请求数据？

父组件按本例的输入合同传入排序，例如 `<ReportSnapshot sort="recent" />`。这页保留类组件，是为了维护仍使用生命周期方法的报表页面；新组件优先考虑函数组件。若采用客户端手写数据读取方案，函数组件可用 Effect 管理同步与清理；本页跟踪类组件中的对应请求生命周期。本例沿用旧页的快照 endpoint；为了具体展示类组件如何响应输入变化，有意把固定读取扩展为 `sort` prop，初次请求 `/api/reports/snapshot?sort=recent`。API 合同把响应定义为 `null` 或含 `generatedAt` 与 `reports` 的对象。组件开始一次 GET，卸载或排序条件变化时取消旧读取；即使不响应 signal 的异步步骤后来才结束，也只有当前请求能提交状态。TypeScript 类型只在编译时约束代码，响应 JSON 仍须在运行时解析。

看一次 `recent` 切到 `oldest` 的真实 Fetch 顺序：旧 GET 已收到响应头，但 `response.json()` 仍在读取正文；排序更新后，旧 signal 被 abort，新 GET 开始。旧原生正文读取以 `AbortError` 拒绝，旧错误因请求已取消而被过滤；这次实跑中 `oldest` 得到对象快照并显示新结果。另一组独立的可控正文 Promise 检查让当前请求返回合法 JSON `null`，它进入 `ready` 并显示“当前没有可用快照”；即使旧正文 Promise 后来成功，也不能覆盖这个状态。自定义异步后处理若不接受 signal，取消不会替它终止；它之后无论成功或失败，现行请求检查仍会阻止旧结果写入状态。

~~~tsx
import { Component } from "react";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type Snapshot = { generatedAt: string; reports: Report[] } | null;

type Props = { sort: SortOrder };
type State =
  | { status: "loading" }
  | { status: "ready"; snapshot: Snapshot }
  | { status: "error"; message: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseSnapshot(value: unknown): Snapshot {
  if (value === null) return null;
  if (
    !isRecord(value) ||
    typeof value.generatedAt !== "string" ||
    !Array.isArray(value.reports)
  ) {
    throw new TypeError("快照结构不符合约定");
  }

  const reports = value.reports.map((item, index) => {
    if (
      !isRecord(item) ||
      typeof item.id !== "string" ||
      typeof item.period !== "string" ||
      typeof item.title !== "string"
    ) {
      throw new TypeError("第 " + index + " 条报表结构不符合约定");
    }
    return { id: item.id, period: item.period, title: item.title };
  });

  return { generatedAt: value.generatedAt, reports };
}

export class ReportSnapshot extends Component<Props, State> {
  state: State = { status: "loading" };
  private requestId = 0;
  private controller: AbortController | null = null;

  componentDidMount() {
    this.loadSnapshot();
  }

  componentDidUpdate(previousProps: Props) {
    if (previousProps.sort !== this.props.sort) {
      this.loadSnapshot();
    }
  }

  componentWillUnmount() {
    this.requestId += 1;
    this.controller?.abort();
    this.controller = null;
  }

  private loadSnapshot() {
    this.controller?.abort();

    const controller = new AbortController();
    const requestId = ++this.requestId;
    this.controller = controller;
    this.setState({ status: "loading" });

    const query = new URLSearchParams({ sort: this.props.sort });
    void (async () => {
      try {
        const response = await fetch(
          "/api/reports/snapshot?" + query.toString(),
          { signal: controller.signal },
        );
        if (!response.ok) throw new Error("HTTP " + response.status);

        const body: unknown = await response.json();
        const snapshot = parseSnapshot(body);
        if (this.isCurrent(requestId, controller)) {
          this.setState({ status: "ready", snapshot });
        }
      } catch (cause) {
        if (this.isCurrent(requestId, controller)) {
          this.setState({
            status: "error",
            message: cause instanceof Error ? cause.message : "读取快照失败",
          });
        }
      }
    })();
  }

  private isCurrent(requestId: number, controller: AbortController) {
    return this.requestId === requestId && !controller.signal.aborted;
  }

  render() {
    if (this.state.status === "loading") {
      return <p role="status">正在读取报表快照…</p>;
    }
    if (this.state.status === "error") {
      return <p role="alert">{this.state.message}</p>;
    }
    if (this.state.snapshot === null) {
      return <p>当前没有可用快照。</p>;
    }
    return <pre>{JSON.stringify(this.state.snapshot, null, 2)}</pre>;
  }
}
~~~

`componentDidMount` 启动挂载后的读取；`componentDidUpdate` 只在排序条件改变时重读，因此 `setState({ status: "loading" })` 自己触发的更新不会造成请求循环；`componentWillUnmount` 增加请求代次并 abort。若排序从 `recent` 改到 `oldest`，新请求开始前旧请求先失效。若旧响应仍到达，`requestId` 或已取消的 signal 会阻止它覆盖新结果。

在根 `<StrictMode>` 下，React 开发模式会额外检查类组件挂载清理：第一次 `componentDidMount` 启动请求，随后的 `componentWillUnmount` 使它失效并取消，第二次 `componentDidMount` 再启动当前请求。若第一次 GET 的 Promise 随后才完成，它的代次不匹配且 signal 已取消，因此不会设置状态；第二次请求解析并通过检查后才进入 `ready`。这项额外检查只针对开发构建，不代表生产中每次挂载都发两次请求。取消只停止客户端仍能停止的工作，不能撤回服务端已经执行的读取或副作用。

状态的 `status` 与数据分开，所以语法正确的 JSON `null` 表示“没有快照”，而不是“仍在加载”。`response.json()` 先解析 JSON 语法；语法错误会在这一步拒绝。成功得到的值仍是 `unknown`，`parseSnapshot` 再检查应用结构并提取字段；形状错误则在第二步抛出。两种失败都进入当前请求的错误状态，但不是同一种解析步骤。把 `response.json()` 结果赋给 `Snapshot` 类型注解并不会验证运行时正文；不可信 JSON 的类型边界见[TypeScript 不可信 JSON 入口](../../../../frontend/typescript/advanced-typescript.md)。这里先检查 HTTP `response.ok`，因为 Fetch 会对 404/500 兑现 Promise；HTTP 错误、JSON 语法错误与 JSON 结构错误分别在不同步骤出现。

React 仍支持这类类组件，但当前文档建议新代码用函数组件。维护类组件时，把启动、属性变化后的同步与清理分别放在 `componentDidMount`、带条件的 `componentDidUpdate` 和 `componentWillUnmount`；不要把网络副作用放进 `render`。函数组件中的请求轮次见[Axios 如何连接 React 报表界面的 HTTP 请求？](axios-in-react.md)，当前 Effect 的 setup/cleanup 说明见[React Effect 更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)。

> [!info]- 来源
> - 类组件仍受支持但不建议用于新代码；挂载、属性更新、卸载与 Strict Mode 开发期的挂载—清理—再挂载：[React 19.3 Component](https://react.dev/reference/react/Component#componentdidmount)，核对日期：2026-11-13。
> - Strict Mode 的额外检查只在开发构建启用：[React StrictMode](https://react.dev/reference/react/StrictMode)。
> - React 介绍 Effect 手写客户端读取与 cleanup，并指出框架内置数据读取通常更高效：[useEffect — Fetching data with Effects](https://react.dev/reference/react/useEffect#fetching-data-with-effects)。
> - `AbortController.abort()` 可中止 Fetch 请求及正文消费：[MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)，核对日期：2026-11-13。
> - `response.json()` 会读取响应体并解析 JSON；正文读取被取消时可拒绝 `AbortError`，JSON 语法无效时拒绝 `SyntaxError`：[MDN Response.json()](https://developer.mozilla.org/en-US/docs/Web/API/Response/json)，核对日期：2026-11-13。
> - Fetch 兑现一个 `Response`，HTTP 错误状态仍需检查 `ok`：[MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)、[Response.ok](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)，核对日期：2026-11-13。
> - TypeScript 类型会被擦除，不会在运行时改变或验证 JSON：[TypeScript for the New Programmer — Erased Types](https://www.typescriptlang.org/docs/handbook/typescript-from-scratch#erased-types)，核对日期：2026-11-13。
