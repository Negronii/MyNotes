# 何时选择轮询、SSE、流式 Fetch 或 WebSocket？

报表查看者已请求刷新报表 42，接下来要决定怎样收取进度。选择取决于消息方向、请求形状、连接生命周期和恢复要求：轮询重复发普通 HTTP 请求；Server-sent Events (SSE，服务端事件) 用一个 HTTP 响应单向发送事件；流式 Fetch 让应用控制请求与读流；WebSocket 让连接两端主动发消息。重连只恢复连接，不保证所有事件都被应用处理；恢复需要服务端保留日志并接受游标，或客户端重新读取权威状态。

~~~mermaid
flowchart TD
    Need{报表端要发送，客户端也要连续发送消息吗？}
    Need -->|否，低频或客户端控制更新| Poll[轮询或长轮询]
    Need -->|否，服务端单向推送| Shape{普通 GET 是否满足请求需求？}
    Shape -->|是| SSE[SSE + EventSource]
    Shape -->|否| Fetch[Fetch 响应流]
    Need -->|是，持续双向消息| WS[WebSocket]
    Poll --> Recover[定义游标、重放或状态查询]
    SSE --> Recover
    Fetch --> Recover
    WS --> Recover
    Recover --> State[恢复报表当前状态或业务事件]
~~~

## 先按更新方向和请求形状选方式

| 方式 | 请求与方向 | 断线恢复由谁负责 | 适用边界 |
| --- | --- | --- | --- |
| 短轮询 | 客户端每隔一段时间发普通请求，返回当前状态或差异 | 客户端控制间隔、退避和停止；API 定义结果与游标 | 更新少且简单性重要；轮询频率过高会浪费请求，间隔过长会延迟发现变化 |
| 长轮询 | 客户端请求后，服务端等到事件或等待期限返回；客户端再发下一条 | 应用重新请求并带序号/游标；代理超时和断线仍须处理 | 需要兼容普通 HTTP 又要降低空轮询；等待请求占用连接和服务资源，须设上限 |
| SSE + EventSource | `GET` 建立 `text/event-stream` 响应，主要收服务端消息 | EventSource 通常自动重连；服务端依游标和保留日志重放 | 服务端单向推送、原生重连方便；原生 API 不接受自定义请求头或请求体 |
| 流式 Fetch | 一次 Fetch 的 body 分块可读；请求可按 API 契约带方法、头和正文 | 应用实现线格式解析、重试、游标、退避和取消 | 需要自定义请求头/Bearer 或 POST 查询后接收流 |
| WebSocket | 握手后客户端与服务端都可主动发完整消息 | 应用定义重连、认证过期、序号、确认和重放 | 双向低延迟交互值得维持长连接；协议不提供业务去重和恢复 |

还要估计连接数、更新频率、消息大小、后台休眠行为和服务端连接容量。一名客户端每秒两次轮询约 2 请求/秒，一万名客户端约 20,000 请求/秒；这只估计请求数，不代表 CPU、网络或数据库开销相同。容量与准入见[Web 服务如何限制拒绝服务的影响？](../security/web-availability-and-ddos.md)。

## SSE 怎样从一致的快照位置续读？

`text/event-stream` 使用 UTF-8 文本，事件字段按行组织，以空行结束一条完整事件。`event` 命名类型，`data` 放内容，`id` 提供重连时可携带的游标，`retry` 可建议重连等待时间。网络包、HTTP 帧和 Fetch 读出的块都不是应用事件边界；客户端要按 SSE 语法解析。

**案例状态：** 在较早的时刻，浏览器曾缓存报表 42 的版本 8 并向服务器验证。之后一次新的刷新已启动；现在客户端从权威接口取得版本 9 的快照，状态为 `running`，且该快照已包含事件日志至游标 103。快照和游标必须来自同一一致性位置；否则两者之间刚发生的事件可能被跳过。

~~~http
GET /api/reports/42 HTTP/1.1
Accept: application/json
~~~

~~~json
{"id":42,"version":9,"status":"running","event_cursor":"103"}
~~~

客户端首次订阅时以应用约定的查询参数告诉服务器从快照游标之后读取：

~~~http
GET /api/reports/42/events?after=103 HTTP/1.1
Accept: text/event-stream
~~~

服务器发送事件 104，表示报表进入生成阶段；稍后报表完成，写入事件 105：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

对应的浏览器订阅可以是：

~~~javascript
const source = new EventSource('/api/reports/42/events?after=103');
source.addEventListener('report.updated', (event) => {
  const update = JSON.parse(event.data);
  if (update.report_id === 42) {
    showStatus(update.status, update.version, update.progress);
  }
});
source.addEventListener('reset', () => {
  source.close();
  void refreshSnapshotAndSubscribeAgain();
});
source.addEventListener('error', () => showConnectionState(source.readyState));
~~~

假定客户端已解析 104、随后连接断开；服务器日志仍保存 105。EventSource 重连时浏览器会把解析到的最后事件 ID 放入 `Last-Event-ID`。本例规定：重连请求的该字段优先于初连 URL 中的 `after=103`，服务器从 104 之后读取并重放 105。初次订阅用 URL 参数，因为原生 EventSource 不让页面设置 `Last-Event-ID` 请求头。

~~~mermaid
sequenceDiagram
    participant C as 浏览器
    participant S as 报表服务
    participant L as 事件日志
    C->>S: GET /api/reports/42/events?after=103
    S->>L: 读取 103 之后的事件
    L-->>S: 104、105
    S-->>C: 事件 104
    Note over C,S: 连接断开，日志仍保留 105
    C->>S: GET /api/reports/42/events?after=103，Last-Event-ID: 104
    S->>L: 按应用约定优先采用 Last-Event-ID
    L-->>S: 重放 105
    S-->>C: report.updated，version 11，ready
~~~

**游标和状态版本不是同一个编号。** `104`、`105` 是事件日志位置，用于从历史中续读；`version=10`、`version=11` 是报表状态修订，只有产品保证版本单调时，界面才可用它丢弃较旧状态。快照版本 9 已涵盖日志游标 103，因此后续状态更新从 104 开始。

`Last-Event-ID` 只表示浏览器解析了某个 SSE 事件并将 ID 作为重连位置；它可能在应用事件处理器完成前已更新，不能证明 `showStatus`、本地持久化或用户确认成功。若每一条事件都必须被业务处理，应用还需按订阅范围持久化已处理的 ID、去重并显式确认；传输本身不提供端到端只处理一次。若界面只需要最新状态，事件版本单调时可合并更新，并在重连后 GET 权威快照。

游标过期时服务器不能悄悄跳过缺口。本例的重置政策是发送一条完整 SSE 事件并终止当前流：

~~~text
event: reset
data: {}

~~~

`data` 字段和结尾空行不可省略，否则标准 EventSource 不会派发这条事件，客户端的 `reset` 处理器也不会运行。客户端收到后关闭 EventSource，重新 GET 快照和 `event_cursor`，再带新游标订阅。若服务器收到一次新的 SSE 请求后直接以 HTTP 204 响应，EventSource 会停止自动重连；这不是把已经开始的 200 流改成 204。断开原因和授权状态仍应由应用契约说明。每次初连或重连都要重新授权读取报表 42。

## 流式 Fetch 如何分开解析完成和传输 EOF？

当原生 EventSource 的 GET、Cookie 认证或请求字段不满足 API 需要时，Fetch 可以用 POST 提交筛选条件，再读 SSE 格式或其他明确线协议。`reader.read()` 可能只拿到半个 UTF-8 字符或半条事件；parser 要把片段缓冲到完整事件边界。此有限查询约定服务端最后发送并以空行结束以下终止事件：

~~~text
event: result.complete
data: {}

~~~

`data` 字段和结尾空行不可省略；parser 只在完整终止事件中识别它。EOF 之前没收到该事件表示查询响应截断。`decoder.decode()` 只冲刷 UTF-8 解码状态，不能代替 parser 判断应用事件是否完整。持续订阅遇到 EOF 则按游标重连。

下面的 parser 是本例接口约定：`feed()` 只向调用方交付已完整结束的事件，`hasTerminalEvent` 仅在解析到完整 `result.complete` 事件后为真，`finish()` 检查未闭合事件并拒绝截断结果。它不是浏览器内置 SSE parser。

~~~javascript
const response = await fetch('/api/reports/42/events/search', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer token-supplied-by-the-application',
    Accept: 'text/event-stream',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ stage: 'rendering' }),
  signal,
});
if (!response.ok || !response.body) throw new Error('HTTP ' + response.status);
if (!response.headers.get('content-type')?.startsWith('text/event-stream')) {
  throw new Error('Unexpected stream media type');
}

const reader = response.body.getReader();
const decoder = new TextDecoder();
let completed = false;
let stoppedEarly = false;
try {
  while (true) {
    const result = await reader.read();
    if (result.done) {
      parser.feed(decoder.decode()); // 只完成最终 UTF-8 解码
      parser.finish();               // 拒绝未以空行结束的尾部事件
      if (!parser.hasTerminalEvent) throw new Error('Truncated event stream');
      completed = true;
      break;
    }
    parser.feed(decoder.decode(result.value, { stream: true }));
    if (parser.hasTerminalEvent) {
      stoppedEarly = true;
      await reader.cancel();
      break;
    }
  }
} catch (error) {
  if (!stoppedEarly) {
    try { await reader.cancel(error); } catch { /* 保留原读取或解析错误 */ }
  }
  throw error;
} finally {
  reader.releaseLock();
}
if (!completed && !stoppedEarly) throw new Error('Incomplete search result');
~~~

`result.complete` 说明这次有限搜索流按 API 契约结束，不等于任何独立的持久报表作业已生成；作业完成要查询其权威状态。Fetch 收到响应头后正文仍可能失败，因此必须读到完整终态；跨源请求仍受 CORS 与凭据模式约束。

## WebSocket 适合哪些双向消息？

浏览器 WebSocket 先握手，再切换到双向消息协议。HTTP/1.1 常用 Upgrade 和 101；HTTP/2、HTTP/3 有各自扩展连接承载方式，不能概括为“升级到 TCP”。WebSocket 消息可跨多个帧，但消息确认、幂等处理、游标和掉线重放仍由应用定义。原生 WebSocket API 不会自动重连，调用方要在应用层实现退避、重新认证和游标恢复。

浏览器构造器接受 URL 与子协议，不开放任意自定义请求头。若握手使用 Cookie，恶意页面可能尝试建连；服务端须按策略检查 Origin、认证连接，并在每条敏感消息上逐次授权。WebSocket 不用 Fetch 的 CORS 响应许可机制，但仍有来源风险。代理超时、网络切换、客户端挂起和服务端资源都会限制连接寿命。

> [!example]- Node.js WebSocket 广播示例
> 下例展示连接集合与广播的最小形状。它不实现认证、租户隔离、消息校验、限速、去重、重连或恢复，不代表完整生产服务。
>
> ~~~javascript
> const { WebSocketServer, WebSocket } = require('ws');
> const server = new WebSocketServer({ port: 3000 });
> const clients = new Set();
>
> server.on('connection', (socket) => {
>   clients.add(socket);
>   socket.on('message', (data, isBinary) => {
>     for (const client of clients) {
>       if (client !== socket && client.readyState === WebSocket.OPEN) {
>         client.send(data, { binary: isBinary });
>       }
>     }
>   });
>   socket.on('close', () => clients.delete(socket));
> });
> ~~~

## 断线后如何确定报表状态？

先决定客户端需要“当前状态”还是“每一条事件”。当前状态可在断线后 GET 报表/作业资源，再从版本和游标建立新订阅；每一条变化都重要时，服务端要保留可重放日志并定义重复、缺口、过期和确认方式。初始快照必须一并交付与之对齐的事件游标，否则读快照和订阅之间可能漏变化。

SSE 可以自动重连，WebSocket 需要应用自己重连，Fetch 也要由应用重新发请求；它们都不能证明数据库副作用是否提交，也不能恢复服务进程内丢失的任务状态。遇到未知完成结果，应查稳定的状态资源，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - SSE 线格式、EventSource 重连、Last-Event-ID 更新、204 停止重连与事件解析：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，按 2026-11-05 版本核对。
> - Fetch 请求与响应体、取消和流处理：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2、§4；[Streams Standard](https://streams.spec.whatwg.org/)，§4；持续维护规范，核对于 2026-11-06。
> - 浏览器 WebSocket API：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，§2；握手和消息帧：[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§4–§5；HTTP/2 承载扩展：[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)；HTTP/3 扩展：[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，均核对于 2026-11-06。
> - Node.js `ws` 服务端广播：[ws README, Server broadcast](https://github.com/websockets/ws#server-broadcast)，核对于 2026-11-06。库文档描述该实现，不是协议规范。
