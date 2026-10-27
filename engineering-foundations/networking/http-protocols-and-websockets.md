# HTTP Protocols and WebSockets / HTTP协议与WebSocket

> **核心解释 / Core idea：** HTTP定义客户端与服务器交换表示、状态和元数据的语义；TCP、QUIC等传输机制决定字节或流如何送达。HTTP版本改变了连接复用与多路复用方式，但不会让请求自动安全、可重试或跨域可读。  
> **Core idea:** HTTP defines the semantics for exchanging representations, status, and metadata between clients and servers; transports such as TCP and QUIC determine how bytes or streams are delivered. HTTP versions change connection reuse and multiplexing, but do not by themselves make requests safe to retry or readable across origins.
>
> **面试简答 / Interview answer：** REST是约束式架构风格，HTTP方法语义决定重试边界；HTTP/1.1复用连接，HTTP/2在TCP上多路复用，HTTP/3基于QUIC流，浏览器CORS控制跨源读取。需要新建连接且没有可用地址时才需解析主机名；已有连接可直接复用，无须为每个请求重新查询。HTTPS还需TLS；DNS、连接、TLS与HTTP故障应分层判断。实时更新按方向和请求契约选择：轮询简单但有开销，SSE/EventSource单向推送并可自动重连，Fetch流支持自定义请求方法/头但应用负责解析恢复，WebSocket双向且恢复由应用约定。  
> **Interview answer:** REST is a constrained style, and HTTP method semantics set retry boundaries. HTTP/1.1 reuses connections, HTTP/2 multiplexes over TCP, and HTTP/3 uses QUIC streams; browser CORS controls cross-origin reads. Resolve the name when a new connection needs an address; an existing usable connection can be reused without a fresh lookup. Apply TLS for HTTPS, and diagnose DNS, connection, TLS, and HTTP failures separately. Choose live-update transport by direction and request contract: polling is simple but adds overhead; SSE/EventSource is one-way with automatic reconnect; Fetch streams allow custom request methods/headers but leave parsing and recovery to the application; WebSocket is bidirectional and leaves recovery to the application.

## REST与HTTP方法 / REST and HTTP methods

REST（Representational State Transfer，表述性状态转移）是架构风格，不等同于“把CRUD路径写成名词”。它约束客户端与服务器分离、无状态交互、可缓存响应、统一接口和分层系统等。HTTP API常用URI标识资源，并以方法表达操作；资源表示和状态码共同构成接口语义。[Fielding对REST的原始描述](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm) 与 [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) 分别说明架构约束与HTTP方法语义。

| 方法 Method | 常见用途 Typical use | 安全 Safe | 幂等 Idempotent |
|---|---|---:|---:|
| GET | 读取表示 Retrieve a representation | 是 Yes | 是 Yes |
| POST | 提交处理或创建资源 Submit processing or create a resource | 否 No | 通常否 Usually no |
| PUT | 创建或完整替换目标资源 Create or replace the target resource | 否 No | 是 Yes |
| PATCH | 按补丁文档修改资源 Apply partial modifications | 否 No | 不保证 Not guaranteed |
| DELETE | 删除目标资源 Delete the target resource | 否 No | 是 Yes |

“安全”指请求语义不要求服务器改变目标资源状态，并不表示没有日志、计数等附带效果。“幂等”指重复执行的预期效果等同于执行一次，不要求每次响应完全一样。例如，第一次DELETE可能返回200，之后返回404，但目标资源保持不存在。POST通常不幂等；若业务允许安全重试，API需要额外约定，例如幂等键或可识别的请求标识。[RFC 9110 §9](https://www.rfc-editor.org/rfc/rfc9110.html#section-9) 定义这些方法属性。

PUT表示创建或替换目标资源的状态；服务器可以拒绝不完整或不合规的表示，不能简单总结成“所有缺失字段必然清空”。PATCH携带描述局部修改的补丁文档；是否幂等取决于补丁操作和接口约定。[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html) 说明PATCH的语义。

~~~http
GET    /posts
POST   /posts
GET    /posts/42
PUT    /posts/42
PATCH  /posts/42
DELETE /posts/42
~~~

不要只凭状态码类别判断能否重试。收到5xx只能说明服务器端或网关报告了错误；如果请求可能已经产生副作用，客户端盲目重发仍会重复操作。根据方法的安全/幂等语义、业务契约以及超时发生阶段作决定。

## HTTP消息、请求头与状态码 / HTTP messages, fields, and status codes

HTTP/1.x（尤其是HTTP/1.1）的文本报文由起始行、字段（常称headers）、空行以及可选消息体组成。[RFC 9112 §2.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-2.1) 规定了这一线格式。HTTP/2和HTTP/3保留HTTP语义，但通过帧和字段块表达消息，并用伪首部承载方法、状态码等控制信息；它们没有HTTP/1.x的文本起始行与空行。[RFC 9113 §8.1](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.1)、[§8.3](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.3)、[RFC 9114 §4.1](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.1)、[§4.3](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.3)。字段传递内容格式、认证信息、缓存策略等元数据。以下是常见字段，具体是否出现取决于客户端、服务器和资源：

| 字段 Field | 常见方向 Direction | 作用 Purpose |
|---|---|---|
| Accept | 请求 Request | 客户端可处理的表示媒体类型 |
| Content-Type | 请求/响应 Request/response | 当前消息体的媒体类型，如application/json |
| Authorization | 请求 Request | 显式提供认证凭据，例如Bearer token |
| Cookie / Set-Cookie | 请求 / 响应 Request / response | 发送已有cookie / 要求浏览器保存或更新cookie |
| Cache-Control | 请求/响应 Request/response | 缓存策略和验证要求 |
| ETag | 响应 Response | 表示版本的验证器，可供条件请求使用 |
| Accept-Encoding | 请求 Request | 客户端支持的内容编码，如gzip、br |
| Accept-Language | 请求 Request | 客户端偏好的自然语言 |
| Content-Length | 请求/响应 Request/response | 在适用的消息中声明消息体长度 |

Cookie常用于保存会话标识，但它本身不是认证协议；服务器根据Cookie值查找会话并执行认证授权。Authorization是应用显式传递凭据的字段。浏览器Fetch不能由脚本手动设置Cookie请求字段，响应中的Set-Cookie也不会暴露给脚本读取；浏览器按cookie规则处理它们。[MDN Cookie字段](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cookie) 与 [MDN Set-Cookie字段](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) 说明这一区别。

| 状态码范围 | 意义 Meaning | 示例 Examples |
|---|---|---|
| 1xx | 继续处理 Informational | 100 Continue |
| 2xx | 请求成功 Successful | 200 OK、201 Created、204 No Content |
| 3xx | 重定向或使用缓存结果 Redirection or cache validation | 301、302、304 |
| 4xx | 请求存在问题 Client error | 400、401、403、404 |
| 5xx | 服务器未能完成请求 Server error | 500、502、503 |

401表示请求缺少有效认证凭据或需要认证；403表示服务器理解请求但拒绝执行。304 Not Modified是条件GET/HEAD的缓存验证结果，表示客户端可复用已存表示；它不是普通的页面跳转。成功与否也不能只靠Fetch的Promise是否reject来判断：Fetch对404或500仍会兑现Promise，调用方应检查Response的status或ok属性。[MDN Fetch指南](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)。

## 缓存协商 / Cache validation

缓存可减少传输和等待，但必须区分“是否存储”和“使用前是否验证”。Cache-Control: max-age给出新鲜期；no-cache允许存储，但使用前需向源站验证；no-store要求缓存不要存储该响应。它们的语义不能互换。[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) 定义HTTP缓存。

常见的ETag协商流程：

1. 响应携带ETag，客户端缓存表示及验证器。
2. 缓存条目过期后，客户端发送If-None-Match并带上该验证器。
3. 若资源未变化，服务器返回304，客户端复用缓存表示；若已变化，服务器返回新表示及其验证器。

协商缓存避免重复传输未变化的内容，但是否允许存储仍由缓存策略和隐私要求决定。不要把no-cache写成“禁止缓存”。

## 浏览器请求API / Browser request APIs

XMLHttpRequest（XHR）仍用于维护旧代码或需要其事件接口的场景，例如上传进度；Fetch是现代浏览器常用的Promise API。两者都需要处理网络失败、取消和HTTP错误等情况。Fetch遇到HTTP 404/500不会自动抛出异常：

~~~javascript
const response = await fetch('/api/data');

if (!response.ok) {
  throw new Error('HTTP ' + response.status);
}

const data = await response.json();
~~~

XHR可以读取状态和响应文本，但应用通常还需自行解析JSON并处理网络错误。Axios是第三方HTTP客户端，常见特性包括响应数据转换、拦截器及可配置的错误判断；它的默认状态码判断通常接受2xx并将其他状态作为错误处理。选择哪种API应服从项目依赖与需求，而不是把某个库的行为误认为HTTP协议保证。[Axios响应结构](https://axios-http.com/docs/res_schema) 与 [Axios错误处理](https://axios-http.com/docs/handling_errors)。

## 网络分层与TCP / Network layers and TCP

OSI七层模型常用于定位概念；实际互联网套件也常按四层概括。不同教材对会话、表示、链路层的归并略有差别，模型是理解工具：

| OSI层 OSI layer | 常见概念 Examples |
|---|---|
| 7 应用 Application | HTTP、DNS、FTP |
| 6 表示 Presentation | 数据表示、编码；TLS常跨越应用与传输边界讨论 |
| 5 会话 Session | 会话管理概念 |
| 4 传输 Transport | TCP、UDP |
| 3 网络 Network | IP、ICMP |
| 2 数据链路 Data link | Ethernet、Wi-Fi链路 |
| 1 物理 Physical | 电缆、无线电信号 |

TCP提供有序、可靠的字节流，不保留应用程序一次write对应一次read的消息边界。应用协议要使用长度前缀、分隔符或固定长度等方式确定消息边界。所谓“粘包”不是TCP把消息粘坏，而是应用误把字节流当作消息队列。

建立连接通常经过SYN、SYN-ACK、ACK三个TCP段；正常关闭时，两个方向分别结束，常见情形会看到FIN与ACK组成的四段交换。但这不是固定的四个报文：ACK与FIN可能合并，双方同时关闭、异常复位等情况也不同。TCP状态与关闭过程见 [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)。

## DNS名称解析与故障边界 / DNS resolution and failure boundaries

**核心解释 / Core explanation：** DNS把名称映射到资源记录，例如IPv4/IPv6地址。常见路径是客户端的本地解析器先查可用缓存；缓存未命中时，请求递归解析器。递归解析器再从缓存回答，或沿根、顶级域到权威服务器的委派查找记录。记录TTL限制缓存可保留该记录的时间；名称错误也可能被缓存。具体客户端可能命中浏览器/系统缓存、hosts文件或已有连接，因而每次请求不一定都走完整解析路径。

**Core explanation (English):** DNS maps names to records such as IP addresses. A local resolver checks available caches first; on a miss, a recursive resolver may follow referrals from the root through a top-level domain to an authoritative server. A record's TTL limits how long it may be cached, and negative answers may also be cached. Browser or system caches, a hosts file, or an already usable connection can bypass a fresh lookup for a particular request.

**面试简答 / Interview answer：** 先确认名称解析是否给出了可用地址，再按连接建立、TLS握手和HTTP响应分别定位错误。解析器可能返回名称错误或临时错误，也可能在上游无响应时超时；这些都发生在HTTP状态码出现之前。改DNS记录也不会立刻清除所有缓存副本，变更速度受已缓存TTL和解析器策略影响。

在浏览器导航中，缓存、Service Worker和连接复用可能绕过一次新的DNS查询；[Browser Basics / 浏览器基础](../../frontend/browser/browser-basics.md)介绍导航时的整体请求路径。DNS只提供名称解析结果，不负责传输加密；[Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md)中的TLS说明解释了HTTPS验证服务器并保护传输的边界。

## HTTP/1.1、HTTP/2与HTTP/3 / HTTP versions

| 版本 Version | 连接与多路复用 Connection and multiplexing | 关键边界 Key caveat |
|---|---|---|
| HTTP/1.0 | 通常响应后关闭连接；后来出现Keep-Alive扩展 | 不是现代HTTP/1.1默认持久连接语义 |
| HTTP/1.1 | 默认持久连接，可复用多个请求/响应；同一连接的流水线响应仍按请求顺序返回 | 串行等待或有序响应可能增加延迟；浏览器可使用多个连接 |
| HTTP/2 | 在一个TCP连接上用多个流并发交换帧，使用HPACK压缩字段 | TCP要求字节有序；一个TCP段丢失可能阻塞该连接上尚未交付的数据 |
| HTTP/3 | 在QUIC连接上承载多个HTTP流；QUIC运行在UDP之上并提供可靠流 | 一个流丢失的数据不必阻塞其他流交付，但流仍受共享拥塞控制等连接级影响 |

HTTP/1.1连接默认持久，但持久连接不等于并行响应；RFC规定流水线响应按请求顺序发送。HTTP/2的应用层多路复用减少了每个请求单独占用连接的需要，却无法改变底层TCP有序字节流的传输层队头阻塞。HTTP/3把流建立在QUIC上：QUIC可在一个流丢包时继续交付其他可用流的数据，但仍共享连接的拥塞控制和部分流控资源。[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)、[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)、[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)、[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)。

HTTP/3使用QUIC而不是“把HTTP直接放在UDP上”：QUIC本身提供连接管理、加密协商和可靠流。会话恢复时可能使用0-RTT数据，但该数据在某些路径上可被重放；有副作用的请求不能仅凭0-RTT就当成安全重试。[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)。

## CORS与浏览器同源策略 / CORS and the same-origin policy

源（origin）由协议、主机和端口共同确定。浏览器的同源策略限制页面读取其他源的响应；CORS（Cross-Origin Resource Sharing，跨源资源共享）让目标服务器通过响应字段声明哪些源可以读取。CORS不是身份认证或CSRF防护机制：符合简单请求条件的跨源请求可能已经发送，只是浏览器不把响应交给页面脚本，因此服务端仍必须验证权限和请求来源。[MDN CORS指南](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)。

~~~http
Access-Control-Allow-Origin: https://app.example
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

浏览器会对不满足CORS safelist的请求先发送OPTIONS预检，询问服务器是否允许目标方法和请求字段；服务器允许后，浏览器才发送实际请求。预检本身不携带凭据。若实际请求需要浏览器凭据，客户端要使用合适的credentials模式，服务端响应必须允许credentials并返回明确的来源，不能用Access-Control-Allow-Origin: *。服务端按Origin动态返回允许来源时，通常还要通过Vary: Origin告知缓存区分响应。

JSONP曾用script标签加载远程JavaScript并调用全局回调，通常限于GET和配合服务端输出；现在应把它看作遗留兼容方案。若前端和后端由同一团队控制，反向代理可以让浏览器请求同源地址，再由服务器转发到上游：

~~~nginx
location /api/ {
  proxy_pass http://backend-server:8080/;
}
~~~

## WebSocket：握手与双向消息 / WebSocket handshake and full-duplex messaging

传统浏览器WebSocket使用HTTP/1.1 Upgrade握手：客户端发送Upgrade相关字段，服务器接受后以101 Switching Protocols切换协议；之后双方可在同一TCP连接上主动发送帧，而不再是普通HTTP请求/响应。WebSocket还有跨HTTP/2、HTTP/3的扩展连接方式，分别通过Extended CONNECT和HTTP/3的对应机制承载，因此不应把所有WebSocket描述为HTTP/1.1的TCP升级。[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)、[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)、[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)。

WebSocket握手不是用CORS响应字段授权的Fetch请求。浏览器会带上Origin，服务器应按应用策略验证来源并认证连接；浏览器WebSocket构造器接受URL和可选子协议，不提供任意请求头参数。适用的Cookie可能参与握手，仍受Cookie规则约束。[MDN WebSocket构造器](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket)。

Node.js可用第三方ws库提供服务；浏览器使用内置WebSocket API。下面服务端向除发送者之外的已连接客户端广播，并在连接关闭时清理集合：

~~~javascript
const { WebSocketServer, WebSocket } = require('ws');
const server = new WebSocketServer({ port: 3000 });
const clients = new Set();

server.on('connection', (socket) => {
  clients.add(socket);

  socket.on('message', (message) => {
    for (const client of clients) {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(message.toString());
      }
    }
  });

  socket.on('close', () => clients.delete(socket));
});
~~~

浏览器端：

~~~javascript
const socket = new WebSocket('ws://localhost:3000');

socket.addEventListener('open', () => socket.send('Hello'));
socket.addEventListener('message', (event) => console.log('Received:', event.data));
socket.addEventListener('close', () => console.log('Disconnected'));
~~~

HTTP持久连接（keep-alive）可以在多个HTTP请求/响应间重用连接，但服务器仍需等待请求，不能在没有请求时任意推送HTTP响应。WebSocket提供双方都可发消息的通道；[ws项目文档](https://github.com/websockets/ws)是Node.js服务端实现示例。轮询、SSE和流式Fetch各自使用HTTP请求/响应，适用的方向与恢复能力见下表。

## 轮询、SSE、流式Fetch与WebSocket / Polling, SSE, streaming Fetch, and WebSocket

| 方式 Transport | 方向与请求契约 Direction and request contract | 连接恢复 Recovery | 适用场景与边界 Fit and boundary |
|---|---|---|---|
| 轮询 Polling | 客户端按间隔发起普通HTTP请求；长轮询会让服务端暂挂一次请求直到有事件或超时。 | 客户端决定频率、退避和何时重试；若需续传，由API定义游标或事件ID。 | 实现简单、适合低频更新；短轮询带来请求开销，长轮询占用等待中的请求。 |
| SSE格式 + `EventSource` API | 服务端向客户端单向发送HTTP `text/event-stream`；EventSource用URL建立GET请求，可选择`withCredentials`。 | EventSource通常会在连接中断后自动重连；服务端可用HTTP 204告知客户端停止重连。带`id:`的事件会在后续重连请求中作为`Last-Event-ID`回传。服务器只有保留可重放的事件历史，才能按该ID续传。 | 适合单向事件；原生EventSource接口没有自定义请求头或请求体，不能把传输断线等同于事件已恢复。 |
| 流式Fetch / Fetch response stream | 一次Fetch请求在响应有body时提供可逐块读取的`Response.body`；请求可使用API允许的方法、请求头、请求体和取消信号。 | Fetch不会替应用实现SSE式自动重连或重放；应用解析协议帧并定义游标、重试和取消策略。 | 需要自定义请求契约或一次性POST后流式返回时合适；字节块不是消息边界。跨源读取仍受CORS约束。 |
| WebSocket | 握手后，客户端和服务端都能沿同一连接发送带消息边界的帧。 | 重连、身份过期、事件序号、确认和恢复均由应用协议定义。 | 双向低延迟交互合适；长期连接需要连接生命周期管理。浏览器构造器没有任意请求头参数，握手认证要按浏览器可用契约设计。 |

SSE既是`text/event-stream`线格式，也是浏览器EventSource接口的常见后端协议。线格式用UTF-8字段行表示事件，并以空行结束一条事件；常见字段为`event`、`data`、`id`和`retry`。例如：

~~~text
Content-Type: text/event-stream

event: progress
id: 42
data: {"stage":"working"}

~~~

`id`只提供重连游标；它本身不保存事件，也不保证服务器能重放断线期间的数据。EventSource接口只公开URL和凭据选项；当请求需要自定义Authorization头、非GET方法或请求体时，可用Fetch读取同一类流格式，但解析、重试和恢复都由应用实现。Fetch的响应体是`ReadableStream`；一次`read()`得到的块可能切在UTF-8字符或应用事件中间，所以要用增量解码器并按协议帧边界拼装，不要把每个块直接当成一个事件。

~~~javascript
const response = await fetch('/api/events', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ filter }),
  signal,
});
if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

const reader = response.body.getReader();
const decoder = new TextDecoder();
let endedNormally = false;
let cancelAttempted = false;
try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      endedNormally = true;
      break;
    }
    // This parser placeholder returns false when the caller intentionally stops before EOF.
    if (parser.feed(decoder.decode(value, { stream: true })) === false) {
      cancelAttempted = true;
      await reader.cancel();
      break;
    }
  }
  if (endedNormally) parser.feed(decoder.decode());
} catch (error) {
  if (!cancelAttempted) {
    cancelAttempted = true;
    try {
      await reader.cancel(error);
    } catch {
      // Preserve the original parser or read error.
    }
  }
  throw error;
} finally {
  reader.releaseLock();
}
~~~

这里的`parser.feed`代表按已约定的线格式增量解析；示例约定它在调用方已获得所需完整结果、决定提前停止时返回`false`，代码随即取消未读响应体。若解析或读取抛错，也会尝试取消响应流；取消本身若失败，仍保留原始解析/读取错误，并在所有路径释放reader锁。若用户取消操作，传入的`AbortSignal`会取消Fetch。传输层提供请求契约、分块、结束和失败信号，不定义界面如何呈现部分内容，也不保证服务端任务状态能跨重连保留。选择时先回答四件事：消息方向是什么、请求是否要带方法/头/体、连接由谁关闭、恢复是否只需重连还是必须按游标重放。

## 浏览器资源提示 / Browser resource hints

资源提示让浏览器提前处理可能重要的网络工作。它们是提示，浏览器可根据资源与连接状况调整或忽略：

| 提示 Hint | 用途 Purpose | 典型场景 Typical use |
|---|---|---|
| preload | 提前获取当前页面确定需要的关键资源 | 首屏字体、稍后才被发现的关键图片或脚本 |
| prefetch | 低优先级预取可能用于后续导航的资源 | 预测下一页 |
| dns-prefetch | 提前解析域名 | 后续可能访问的第三方域 |
| preconnect | 提前完成目标源连接准备 | 很快要使用的关键第三方源 |

~~~html
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="prefetch" href="/next-page.js">
<link rel="dns-prefetch" href="//analytics.example">
<link rel="preconnect" href="https://api.example">
~~~

preload应只用于当前页面确实需要的资源，并填写匹配的as类型；字体通常需要crossorigin，以便预加载与CSS字体请求使用一致的CORS模式，避免重复下载。preconnect只适合关键且即将使用的来源，过多提示会消耗连接资源。[web.dev资源提示指南](https://web.dev/learn/performance/resource-hints)。

## 相关主题 / Related notes

- [浏览器基础 / Browser Basics](../../frontend/browser/browser-basics.md)：浏览器的请求、渲染和安全边界。
- [Web安全与身份认证 / Web Security and Authentication](../security/web-security-and-authentication.md)：CORS之外的认证、Cookie与请求保护。

DNS and streaming sections checked against [RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html), the [WHATWG HTML Server-sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html), [Fetch Standard](https://fetch.spec.whatwg.org/), [Streams Standard](https://streams.spec.whatwg.org/), and [WebSockets Standard](https://websockets.spec.whatwg.org/) on 2026-10-15. The SSE reconnection and HTTP 204 boundary was rechecked against the current WHATWG HTML standard on 2026-10-27.

