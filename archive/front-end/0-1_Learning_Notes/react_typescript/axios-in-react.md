# Axios 如何连接 React 报表界面的 HTTP 请求？

Axios 是 Promise 式 HTTP 客户端。下面的代码沿用当前报表 URL 中的 sort 条件请求行数据；UI 更新和请求过期处理的主线见[React Effect 更新轮次](../../../../frontend/frameworks/react-basics.md#effect在提交后同步外部系统)，服务端查询缓存见[React 服务端状态章节](../../../../frontend/frameworks/react-server-state-and-optimistic-updates.md)。

~~~typescript
import axios from "axios";

type SortOrder = "recent" | "oldest";
type Report = { id: string; period: string; title: string };
type Preview = { reportCount: number; estimatedBytes: number };

declare function parseReports(value: unknown): Report[];
declare function parsePreview(value: unknown): Preview;

const reportsClient = axios.create({
  baseURL: "/api",
  timeout: 10_000,
});

reportsClient.interceptors.request.use(config => {
  // 只对这个客户端实例的请求设置默认头；token 应由可信的会话边界提供。
  config.headers.Authorization = "Bearer " + readAccessToken();
  return config;
});

async function loadReports(
  sort: SortOrder,
  signal: AbortSignal
): Promise<Report[]> {
  const response = await reportsClient.get<unknown>("/reports", {
    params: { sort },
    signal,
  });

  // 泛型只描述编译器中的预期，运行时仍由 parseReports 检查 JSON。
  return parseReports(response.data);
}

declare function readAccessToken(): string;

async function requestExportPreview(reportIds: string[], signal: AbortSignal): Promise<Preview> {
  const response = await reportsClient.post<unknown>(
    "/reports/export-preview",
    { reportIds },
    { signal }
  );
  return parsePreview(response.data);
}
~~~

axios.create 为这组请求建立 baseURL、timeout 和拦截器作用域。示例不导出这个带 token 的客户端；`loadReports` 只请求固定的 `/reports`，`requestExportPreview` 只请求固定的 `/reports/export-preview`。不要把携带会话凭证的实例交给可接收任意 URL 的调用方。若应用会并行切换会话，应让调用边界明确传入凭证。请求与响应拦截器可以规范认证头、日志和错误映射；组件仍要处理调用成功、失败和卸载后的结果。传入 AbortSignal 后，组件或路由可在任务过期时请求取消客户端读取。

Axios 默认把 2xx 响应交给成功分支，把不满足 validateStatus 的响应放入拒绝分支。Fetch 则会对 HTTP 404/500 正常兑现 Promise，因此需要检查 response.ok；其他传输故障与正文解析故障也各有表现，详见[HTTP 客户端如何呈现响应与失败](../../../../engineering-foundations/networking/http-protocols-and-websockets.md)。

在 catch 中，axios.isAxiosError 可识别 AxiosError 并收窄其静态类型；再看 error.response、error.request 或 setup error，分别对应服务端返回了非成功状态、没有收到响应、请求尚未正确建立。这个类型守卫不会验证 response.data 的 JSON 结构。

~~~typescript
declare const signal: AbortSignal;
declare function showReports(reports: Report[]): void;
declare function showRequestError(message: string): void;

try {
  const reports = await loadReports("oldest", signal);
  showReports(reports);
} catch (cause) {
  if (axios.isCancel(cause)) {
    // 主动取消或过期请求不作为用户可见错误。
  } else if (axios.isAxiosError(cause)) {
    if (cause.response) {
      showRequestError("服务端返回 HTTP " + cause.response.status);
    } else if (cause.request) {
      showRequestError("请求已发出，但没有收到响应");
    } else {
      showRequestError(cause.message);
    }
  } else {
    showRequestError(cause instanceof Error ? cause.message : String(cause));
  }
}
~~~

> [!info]- 来源
> - 当前实例、默认值、拦截器、响应结构、错误类别、取消与 POST 请求配置：[Axios 1.21.0 README](https://github.com/axios/axios/blob/v1.21.0/README.md)、[Cancellation](https://axios-http.com/docs/cancellation)，核对日期：2026-11-06。
> - Axios TypeScript 类型、isAxiosError 与运行时解析边界：[Axios TypeScript documentation](https://axios-http.com/docs/typescript)，Axios 1.21.0，核对日期：2026-11-06。
