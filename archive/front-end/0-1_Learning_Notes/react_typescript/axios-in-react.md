# Axios 如何连接 React 报表界面的 HTTP 请求？

案例从账户 acct-17 打开报表页、按 recent 排序开始。认证边界提供当前会话的私有 API；GET 读取报表后，代码把响应正文当作不可信值逐项校验，只有仍属于当前视图的结果才显示。服务端凭证判断账户与权限，前端的排序值和报表 ID 只是请求数据。

React 会按组件在树中的位置保留 state。若账户或 sort 变化后仍渲染同一组件，新的 props 第一次提交时可能暂时配上旧的 ready 数据；useEffect 的新一轮读取在提交后启动。父组件应把会话权限范围与筛选条件编码进 key，让不同视图从全新的 loading 状态开始。下面三个 TypeScript/TSX 代码块按顺序组成同一个 TSX 模块：固定 API 与解析器、React 页面、错误映射；路由和认证模块由调用方提供。

~~~typescript
import axios from "axios";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type Preview = { reportCount: number; estimatedBytes: number };
type ReportsApi = {
  loadReports(sort: SortOrder, signal: AbortSignal): Promise<Report[]>;
  requestExportPreview(
    reportIds: string[],
    signal: AbortSignal
  ): Promise<Preview>;
};

class ReportPayloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ReportPayloadError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) {
    throw new ReportPayloadError("报表响应必须是数组");
  }

  return value.map((item, index) => {
    if (
      !isRecord(item) ||
      typeof item.id !== "string" ||
      typeof item.period !== "string" ||
      typeof item.title !== "string"
    ) {
      throw new ReportPayloadError(
        "第 " + index + " 条报表结构不符合约定"
      );
    }
    return { id: item.id, period: item.period, title: item.title };
  });
}

function parsePreview(value: unknown): Preview {
  if (
    !isRecord(value) ||
    typeof value.reportCount !== "number" ||
    !Number.isFinite(value.reportCount) ||
    value.reportCount < 0 ||
    typeof value.estimatedBytes !== "number" ||
    !Number.isFinite(value.estimatedBytes) ||
    value.estimatedBytes < 0
  ) {
    throw new ReportPayloadError("导出预览结构不符合约定");
  }
  return {
    reportCount: value.reportCount,
    estimatedBytes: value.estimatedBytes,
  };
}

// 只在认证边界调用；页面得到窄接口，不接触 token 或通用 URL。
function createReportsApi(accessToken: string): ReportsApi {
  const client = axios.create({
    baseURL: "/api/",
    timeout: 8_000,
    allowAbsoluteUrls: false,
  });

  client.interceptors.request.use(config => {
    config.headers.set("Authorization", "Bearer " + accessToken);
    return config;
  });

  return {
    async loadReports(sort, signal) {
      const response = await client.get<unknown>("reports", {
        params: { sort },
        signal,
      });
      return parseReports(response.data);
    },

    async requestExportPreview(reportIds, signal) {
      const response = await client.post<unknown>(
        "reports/export-preview",
        { reportIds },
        { signal },
      );
      return parsePreview(response.data);
    },
  };
}
~~~

本例固定 Axios 1.21.0。私有 client 从 baseURL 拼出 GET /api/reports?sort=recent，并在请求拦截器中附上闭包捕获的会话令牌。baseURL 只是地址拼接便利，不是安全边界；allowAbsoluteUrls: false 可避免绝对 URL 覆盖基址，却不能约束相对路径中的 ..。这里不接收任意 URL，而只暴露两个固定操作。服务端仍须对每次请求独立检查账户、权限和资源归属。

响应中的 JSON 到达后仍需运行时校验：get<unknown> 的泛型只约束编译器里的预期，parseReports 与 parsePreview 才检查实际字段。解析器用 ReportPayloadError 标记应用数据格式错误，使后面的错误映射不会把拦截器抛出的普通 TypeError 误报成坏响应。

在这个合成 API 合同中，用户已经选中报表 r-41，点击“计算预览”会调用 POST /api/reports/export-preview。服务端只计算数量和估算字节数，不创建持久导出任务或其他状态。这个契约是为了说明请求边界的教学假设，不是对所有 POST 的解释。页面不在 GET Effect 中调用它；预览与读取使用同一 session API。超时表示客户端没拿到响应，页面不会自动重放；用户可明确再点一次。若实际 POST 会创建任务或改变资源，不能据此认为取消或超时撤销了副作用；重试需要服务端提供幂等键或状态查询等协议。

~~~tsx
import { useEffect, useRef, useState } from "react";

type ReportState =
  | { status: "loading" }
  | { status: "ready"; reports: Report[] }
  | { status: "error"; message: string };

type PreviewState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; value: Preview }
  | { status: "error"; message: string };

type ReportSession = {
  // 不含凭证；有效账户或权限范围变化时必须更新。
  viewKey: string;
  api: ReportsApi;
};

function ReportPage({
  session,
  sort,
}: {
  session: ReportSession;
  sort: SortOrder;
}) {
  return (
    <ReportsView
      key={JSON.stringify([session.viewKey, sort])}
      api={session.api}
      sort={sort}
    />
  );
}

function ReportsView({
  api,
  sort,
}: {
  api: ReportsApi;
  sort: SortOrder;
}) {
  const [reports, setReports] = useState<ReportState>({ status: "loading" });
  const [preview, setPreview] = useState<PreviewState>({ status: "idle" });
  const previewController = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let current = true;

    setReports({ status: "loading" });
    void api.loadReports(sort, controller.signal)
      .then(value => {
        if (current) setReports({ status: "ready", reports: value });
      })
      .catch(cause => {
        if (current && !controller.signal.aborted) {
          setReports({ status: "error", message: messageFor(cause) });
        }
      });

    return () => {
      current = false;
      controller.abort();
      previewController.current?.abort();
    };
  }, [api, sort]);

  function calculatePreview() {
    const controller = new AbortController();
    previewController.current = controller;
    setPreview({ status: "loading" });

    void api.requestExportPreview(["r-41"], controller.signal)
      .then(value => {
        if (
          previewController.current === controller &&
          !controller.signal.aborted
        ) {
          setPreview({ status: "ready", value });
        }
      })
      .catch(cause => {
        if (
          previewController.current === controller &&
          !controller.signal.aborted
        ) {
          setPreview({ status: "error", message: messageFor(cause) });
        }
      });
  }

  const reportText =
    reports.status === "ready"
      ? reports.reports[0]?.title ?? "没有报表"
      : reports.status === "error"
        ? reports.message
        : reports.status;
  const previewText =
    preview.status === "ready"
      ? "共 " + preview.value.reportCount +
        " 份，估算 " + preview.value.estimatedBytes + " 字节"
      : preview.status === "error"
        ? preview.message
        : preview.status;

  return (
    <section>
      <p>{sort}: {reportText}</p>
      <button
        disabled={preview.status === "loading"}
        onClick={calculatePreview}
      >
        计算 r-41 的导出预览
      </button>
      <p>{previewText}</p>
    </section>
  );
}
~~~

父组件把当前会话和排序一起交给 ReportPage，例如 `<ReportPage session={sessions[account]} sort={sort} />`。当会话权限范围或 sort 改变时，key 随之改变，React 在新视图第一次提交前就重建 ReportsView；其初始 state 是 loading，旧账户或旧筛选结果不能占据这个提交。session 对象和 api 实例应在该会话范围内保持稳定；权限或账户范围变化时换用新的 viewKey 和 API。key 不是授权检查，服务端仍是权限的最终裁判。

Effect 的 cleanup 会使旧读取失效并 abort 客户端请求。即便异步工作不理会 signal，current 检查也阻止旧成功或旧失败覆盖新视图。abort 只停止客户端继续等待或处理，不能撤回服务端已经收到的请求。预览只从按钮处理器触发；若视图被替换，cleanup 也会取消客户端等待。Effect 在提交后同步外部系统的阶段与清理语义见[React Effect 更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)；需要共享缓存、去重和跨组件更新时，可继续看[React 如何维护服务端数据与乐观更新](../../../../frontend/frameworks/react-server-state-and-optimistic-updates.md#排序值构成查询身份)。

Axios 默认对 2xx 响应兑现 Promise，并把不符合默认 validateStatus 的 HTTP 响应放到拒绝分支；自定义 validateStatus 会改变分界。Fetch 对 HTTP 404/500 通常仍兑现 Promise，因此调用方要检查 response.ok。两种客户端都不能代替正文校验；HTTP 层响应和失败的边界见[浏览器请求如何到达 HTTP 响应](../../../../engineering-foundations/networking/http-protocols-and-websockets.md#服务端返回了什么页面何时才能使用)。

本机合成 API 对 GET 返回 [{ "id": "r-41", "period": "2026-Q3", "title": "acct-17-recent" }]。parseReports 接受这些字段后，页面显示 “recent: acct-17-recent”；若同一视图收到空数组，则显示“没有报表”。

~~~typescript
function messageFor(cause: unknown): string {
  if (cause instanceof ReportPayloadError) {
    return "服务端报表数据格式不符合约定";
  }
  if (axios.isCancel(cause)) return "请求已取消";

  if (axios.isAxiosError(cause)) {
    if (cause.response) {
      return "服务端返回 HTTP " + cause.response.status;
    }
    if (cause.request) return "未收到 HTTP 响应";
    return "请求未能完成";
  }
  return "报表请求失败";
}
~~~

收到 AxiosError 时，response 表示服务端返回了 HTTP 状态；request 存在但 response 不存在时，客户端只能说明“未收到 HTTP 响应”，不能仅凭这个字段断言请求已发送到服务器。其他 Axios 错误可能发生在请求建立阶段。解析器的专用错误类型与 Axios 网络错误也分开处理。避免把整个 Axios 错误或 config 写入日志，因为其中可能含 Authorization。

> [!info]- 来源
> - Axios 1.21.0 本例使用的实例、配置、拦截器、响应和错误处理：[Creating an instance](https://axios-http.com/docs/instance)、[Request config](https://axios-http.com/docs/req_config)、[Interceptors](https://axios-http.com/docs/interceptors)、[Error handling](https://axios-http.com/docs/handling_errors)、[Cancellation](https://axios-http.com/docs/cancellation)。配置文档说明 baseURL 不是安全边界、allowAbsoluteUrls 不约束相对 .. 路径，且默认拒绝非 2xx；错误文档区分 response、request 与请求设置错误。核对日期：2026-11-13。
> - allowAbsoluteUrls 首次作为配置加入 Axios 1.8.0；Axios 1.8.3 补上 TypeScript 类型并将选项传给 XHR/Fetch adapter：[Axios v1.8.0 release](https://github.com/axios/axios/releases/tag/v1.8.0)、[Axios v1.8.3 release](https://github.com/axios/axios/releases/tag/v1.8.3)。
> - React 根据树位置保留 state，不同 key 会重置子树；useEffect 在提交后设置并在依赖变化或卸载时 cleanup：[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)、[useEffect](https://react.dev/reference/react/useEffect)。核对日期：2026-11-13。
> - TypeScript 类型编译后会擦除，不能校验收到的 JSON：[TypeScript for the New Programmer — Erased Types](https://www.typescriptlang.org/docs/handbook/typescript-from-scratch#erased-types)。
