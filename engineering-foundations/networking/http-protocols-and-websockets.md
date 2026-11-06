# 浏览器请求如何到达 HTTP 响应？

Hypertext Transfer Protocol (HTTP，超文本传输协议) 规定调用方怎样描述操作、服务端怎样返回状态与表示；Transmission Control Protocol (TCP，传输控制协议) 或 QUIC 负责承载字节流，Transport Layer Security (TLS，传输层安全协议) 在安全连接上保护通信。看同一个报表请求，应先认清 HTTP 语义，再按是否有可复用缓存、地址和连接追踪网络阶段。HTTP 版本会改变连接复用和多路复用方式，但不会替 application programming interface (API，应用程序接口) 验证身份、授权资源、允许跨源读取或确认超时操作结果。

**案例：** 查看者已登录并获准读取报表 42。此前浏览器收到 `200` JSON、`ETag: "report-42-v8"` 和 `Cache-Control: private, no-cache`，并把该表示保存在自己的私有缓存。用户再次打开页面时，浏览器用旧验证值询问当前表示。图中的某些阶段会因 Service Worker、缓存、DNS 地址或已有连接而跳过；持续更新则需要独立的消息与恢复契约，见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](real-time-web-updates.md)。

~~~mermaid
flowchart LR
    Click[打开报表 42] --> Browser[浏览器构造请求]
    Browser --> Cache{缓存可直接回答且无需源站验证？}
    Cache -->|是| Cached[交付缓存表示]
    Cache -->|否| Conn{有可复用连接？}
    Conn -->|有| HTTP[发送 HTTP 请求]
    Conn -->|没有| Address[使用地址缓存，或按需解析域名]
    Address --> Handshake[建立 TCP/TLS 或 QUIC 连接]
    Handshake --> HTTP
    HTTP --> App[路由、认证、授权与处理]
    App -->|权限拒绝| Deny[返回约定的 401、403 或隐藏式 404]
    App -->|权限允许| Result[返回 304 或新的 200 表示]
    Cached --> UI[浏览器交付表示给页面]
    Deny --> UI
    Result --> UI
~~~

## 一次请求和响应如何描述报表？

Uniform Resource Identifier (URI，统一资源标识符) 定位目标资源；方法表达操作；请求还可以有路径、查询参数、字段和消息体。响应给出状态、字段和表示（representation）。这里的“表示”是服务端选择的一种媒体类型与编码，不必等于数据库中的单行。

本次条件读取可写成：

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json
Accept-Language: zh-CN, en;q=0.8
Cookie: __Host-session=<opaque-session-id>
If-None-Match: "report-42-v8"
~~~

浏览器曾缓存的响应是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Language: zh-CN
ETag: "report-42-v8"
Cache-Control: private, no-cache

{"id":42,"title":"Service health","status":"ready","version":8}
~~~

`ETag` 是服务端为选中表示提供的验证值。当前权限仍允许读取、表示也未变化时，服务端可以只回答：

~~~http
HTTP/1.1 304 Not Modified
ETag: "report-42-v8"
Cache-Control: private, no-cache
~~~

若权限已撤销，服务端应按 API 的隐私政策返回 403 或隐藏式 404；若权限仍允许但表示变化，则返回新的 `200`、正文和 ETag。浏览器管理的 HTTP 缓存收到 304 后会把先前保存的正文与新验证信息组合；页面通常得到可用的 200 表示，而不是把空的 304 正文当报表内容。缓存验证不绕过认证与授权。

各字段职责不同：`Accept` 表示调用方偏好的响应媒体类型，`Content-Type` 描述消息体的媒体类型，`Content-Encoding` 描述表示经过的压缩等编码，`Accept-Language` 表示语言偏好而不保证服务一定有该语言，`Content-Language` 描述返回表示面向的语言。Cookie 与 `Authorization` 携带认证凭据；浏览器会自行管理 Cookie，脚本不能任意手设 `Cookie`。缓存验证器则由 `ETag` 与条件字段 `If-None-Match` 配合。

safe method (安全方法) 的预期语义是不要求改变目标资源状态；这不禁止日志、计数等附带效果。idempotent (幂等) 表示重复执行的预期效果等同执行一次，不要求响应字节相同：第一次 DELETE 可回 204，后续回 404，但资源仍保持不存在。PUT 让目标资源成为请求描述的状态，不必然表示没写的字段都会清空；PATCH 是否幂等取决于补丁操作和接口约定；POST 通常不具幂等性。方法语义不能独自说明连接中断后副作用是否已经提交；未知结果需用业务请求标识确认，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info] HTTP 与 REST 的关系
> Representational State Transfer (REST，表述性状态转移) 是一种架构风格，约束包括客户端与服务端分离、无状态交互、可缓存、统一接口和分层系统；代码按需下发是可选约束。统一接口进一步要求资源标识、以表示操纵资源、自描述消息及超媒体控制。使用 HTTP 方法和 JSON 不会自动满足所有 REST 约束；检查请求是否无状态、缓存是否遵循策略、表示和链接是否足以驱动交互，才是在讨论 REST 风格。参见 Fielding 的架构定义。

## 缓存策略怎样决定能否复用？

以下指令表达不同选择：`private` 允许浏览器私有缓存保存，但禁止共享缓存复用该响应；`max-age=60` 给出新鲜期，未过期时缓存可能直接复用而不联系源站；`no-cache` 允许存储，却要求每次复用前先向源站验证；`no-store` 要求缓存不要存储该交换。它们不替代访问控制，也不自动让私有响应与用户隔离。若权限可能在 60 秒内撤销，只靠 `private, max-age=60` 会允许浏览器在新鲜期内直接复用旧正文；要求再次确认授权时，可使用 revalidation（重新验证）策略，敏感内容也可用 `no-store`。

API 自己仍须为缓存键和验证器划定租户、主体、表示协商及语言范围。浏览器中的私有表示缓存与服务器端对象/租户授权是两层不同控制；见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

## 状态码说明什么？

HTTP 状态描述当前请求的处理结果类别，不描述调用方全部业务状态，也不表示中间每个网络环节都成功。

| 范围或状态 | 报表示例 | 含义边界 |
| --- | --- | --- |
| 1xx | 100 Continue | 继续处理的中间信息 |
| 2xx | 200 当前表示；201 已创建资源记录；202 已受理异步作业 | 202 不表示作业已完成 |
| 3xx | 304 Not Modified | 浏览器可复用已有的已验证表示 |
| 4xx | 400 格式错误；401 缺少有效凭据；403 拒绝；404 不存在或按政策隐藏；409 冲突；429 超过额度 | 发出 401 时必须包含适用的 `WWW-Authenticate` challenge；超时发生在客户端，不自动成为 HTTP 状态 |
| 5xx | 502 上游响应无效；503 暂时不能处理；504 等待上游超时 | 说明服务端/网关未完成当前请求 |

浏览器 `fetch()` 的 Promise 在收到 HTTP 响应后会兑现，即使状态是 404 或 500；脚本应检查 `response.ok` 或 `status`。响应头已到达不代表正文已经完整读完：`response.json()` 或流读取仍可能因连接断开、解码或读取错误而失败。Fetch 与其他客户端对 HTTP 错误的呈现也不同：Fetch 默认不会因为非 2xx 拒绝 Promise；Axios 默认把非 2xx 放入拒绝分支并把响应放在错误对象中，`validateStatus` 可改变该规则；XMLHttpRequest 的 `load` 表示收到响应，需自行检查状态，`error` 表示网络级失败，`upload.onprogress` 仍适合需要浏览器上传进度事件的界面。Axios 的 adapter 和版本会影响细节，旧项目可参考[归档 Axios 说明](../../archive/front-end/0-1_Learning_Notes/react_typescript/axios-in-react.md)。

## HTTP/1.1、HTTP/2 与 HTTP/3 如何共享连接？

HTTP 语义由 RFC 9110 定义，不同版本用不同线格式和传输承载。HTTP/1.1 报文可见起始行、字段、空行和可选消息体；HTTP/2、HTTP/3 把方法、字段和内容编码为帧及字段块，但调用方仍表达相同方法、目标与状态。

| 版本 | 连接和并发方式 | 丢包影响及边界 |
| --- | --- | --- |
| HTTP/1.1 | 默认可持久复用连接，浏览器也可并行打开多个连接；同一连接上的流水线响应仍按请求顺序返回 | 一个连接上前面的慢响应可能让后续响应等待；持久连接不表示服务器能在无请求时任意推送 HTTP 响应 |
| HTTP/2 | 多个 HTTP 流在一个 TCP 连接上以帧交错传输，并压缩字段 | TCP 提供有序字节流；早期 TCP 段丢失会暂缓该连接后续字节交付，因此多个流可能一起等候 |
| HTTP/3 | HTTP 流运行在 QUIC 上；QUIC 使用 UDP 承载，但自己提供可靠流、流控、拥塞控制和 TLS 1.3 握手 | 某个 QUIC 流缺失的数据通常不会阻止其他已齐全流的数据交付；它们仍共享连接级拥塞、流控和路径资源 |

例如图片所在 TCP 段丢失时，即使报表 JSON 的 HTTP/2 流后续字节已到，也要等待字节流缺口补齐；在 QUIC 下，若 JSON 流数据本身齐全且仍有连接资源，它可能先交付。HTTP/3 隔离了部分跨流传输等待，但并不消除共享拥塞造成的延迟，因此不能只从版本号推出固定性能收益。

TCP 是有序可靠字节流，不保留一次应用 `write` 对应一次 `read` 的消息边界。应用协议需另定长度前缀、分隔符或固定长度。所谓“粘包”通常是把字节流误当消息队列造成的解析错误。正常关闭还可分别结束两个方向；FIN/ACK 交换可能合并，不能说每次都固定四个报文。

## 域名解析、TCP 与 TLS 按什么顺序检查？

浏览器首次访问 `reports.example` 时，若缺少可复用连接，会先使用仍有效的本地 DNS 地址缓存；没有可用地址才向解析器查询。即使连接已关闭，DNS 地址仍可能在缓存有效期内。递归解析器也可能从缓存返回记录或沿域名委派查询。记录 TTL 限定缓存可保留时间；错误回答也可能被缓存。Service Worker、HTTP 缓存、地址缓存和连接复用是不同快路径。

TCP 建连常见三次握手：客户端发送 SYN 请求同步序号；服务端回 SYN-ACK 同意并给出自己的序号；客户端再回 ACK。它只描述 TCP 建连；QUIC 在 UDP 上进行自己的连接和 TLS 握手，不执行这组三报文交换。完整、普通的 TLS/QUIC 新连接会在应用数据前建立必要密钥与身份验证；TLS 1.3 会话恢复还可能启用 0-RTT early data，让客户端在握手完成前发送早期数据。早期数据可被重放，所以不能把它用于依赖“只执行一次”的副作用，除非应用有与重放边界相配的幂等或反重放设计。

因此排障时要分开确认：是否有地址缓存或 DNS 查询、TCP 三次握手或 QUIC 建连、常规 TLS 握手或恢复、证书与主机名验证、最后的 HTTP 请求和响应。网络连接或 TLS 错误不是 API 的 500。

> [!info] 预连接与预取提示
> `preload` 提示浏览器提前取当前页面已经确定要用的关键资源；`prefetch` 提示低优先级准备未来导航可能使用的资源；`preconnect` 可为很快要访问的可信来源准备连接；`dns-prefetch` 只预解析主机名。浏览器可以依据资源和连接条件忽略或调整这些提示。对当前已复用的主机，预连接通常没有额外效果；提前准备新的第三方来源会占用连接资源，须按实际需要选择。

~~~html
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
<link rel="prefetch" href="/next-page.js">
<link rel="preconnect" href="https://reports-cdn.example">
~~~

**接下来：** 若页面与 API 不同源，浏览器何时允许脚本读取响应由[浏览器安全边界](../security/web-browser-security-boundaries.md)说明；若要连续接收报表更新，则选取[实时传输与恢复方式](real-time-web-updates.md)。

> [!info]- 来源
> - HTTP 字段、方法安全性与幂等、状态码、URI、表示协商：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§6–§12、§15，2022-06；401 challenge 见 §15.5.2，核对于 2026-11-06。
> - 缓存新鲜度、`max-age`、`no-cache`、`no-store`、`private` 和条件请求：[IETF RFC 9111, HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，§4–§5，2022-06；核对于 2026-11-06。
> - HTTP/1.1 报文与连接：[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)，§2、§9；HTTP/2 帧与流：[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)，§2、§5、§8；HTTP/3 映射：[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)，§1–§4。均为 2022-06 标准，核对于 2026-11-06。
> - TCP 三次握手与连接状态：[RFC 9293, Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293.html)，§3、§3.5，2022-08；QUIC 流与拥塞：[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)，§2、§3、§13，2021-05；QUIC TLS：[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)，§4、§5、§9.2，2021-05；TLS 1.3：[RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html)，§2–§4，2018-08。均核对于 2026-11-06。
> - DNS 委派与缓存：[RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html)，§4–§5，1987-11；DNS 负缓存：[RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.html)，§3–§5，1998-03。核对于 2026-11-06。
> - REST 架构风格的客户端-服务端、无状态、缓存、统一接口和分层约束：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，§5，2000。
> - Fetch 对脚本可设置请求字段和可见响应字段的限制：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/#forbidden-request-header)，Living Standard，核对于 2026-11-06；XHR 事件模型：[WHATWG XMLHttpRequest Standard](https://xhr.spec.whatwg.org/)，§3.5，核对于 2026-11-06；Axios 默认错误处理：[Axios error handling](https://axios-http.com/docs/handling_errors)，核对于 2026-11-06。
> - 资源提示类型：[WHATWG HTML Living Standard, Link types](https://html.spec.whatwg.org/multipage/links.html#linkTypes)，核对于 2026-11-06。
