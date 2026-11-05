# When should a browser use polling, SSE, streaming Fetch, or WebSocket? / 何时选轮询、SSE、流式 Fetch 或 WebSocket？

**Core answer / 核心回答：** Choose by message direction, request shape, connection lifetime, and recovery contract. Polling is a series of ordinary HTTP requests; SSE/EventSource provides one-way server events over GET; Fetch streams allow a custom method, headers, body, and cancellation but leave parsing and reconnection to the application; WebSocket supports bidirectional messages and leaves reconnect/replay rules to the application. A reconnect is not recovery unless the server can replay from a retained cursor or the client can query authoritative state. / 根据消息方向、请求形状、连接生命周期和恢复契约选择方式。轮询是一系列普通 HTTP 请求；SSE/EventSource 通过 GET 单向发送服务端事件；Fetch 流允许自定义方法、请求头、请求体和取消信号，但解析和重连由应用负责；WebSocket 支持双向消息，重连和重放规则也由应用定义。若服务端不能按保留游标重放，或客户端不能查询权威状态，重新连接本身不等于恢复。
## WebSocket handshake and bidirectional messages / WebSocket 握手与双向消息

传统浏览器WebSocket使用HTTP/1.1 Upgrade握手：客户端发送Upgrade相关字段，服务器接受后以101 Switching Protocols切换协议；之后双方可在同一TCP连接上主动发送帧，而不再是普通HTTP请求/响应。WebSocket还有跨HTTP/2、HTTP/3的扩展连接方式，分别通过Extended CONNECT和HTTP/3的对应机制承载，因此不应把所有WebSocket描述为HTTP/1.1的TCP升级。[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)、[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)、[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)。

WebSocket握手不是用CORS响应字段授权的Fetch请求。浏览器会带上Origin，服务器应按应用策略验证来源并认证连接；浏览器WebSocket构造器接受URL和可选子协议，不提供任意请求头参数。适用的Cookie可能参与握手，仍受Cookie规则约束。[MDN WebSocket构造器](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket)。

Node.js 可用第三方 `ws` 库提供服务，浏览器使用内置 WebSocket API。示例向除发送者之外的已连接客户端广播，保留文本或二进制消息类型，并在连接关闭时清理集合。 [`ws` 广播示例](https://github.com/websockets/ws#server-broadcast)

~~~javascript
const { WebSocketServer, WebSocket } = require('ws');
const server = new WebSocketServer({ port: 3000 });
const clients = new Set();

server.on('connection', (socket) => {
  clients.add(socket);

  socket.on('message', (data, isBinary) => {
    for (const client of clients) {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(data, { binary: isBinary });
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

**Key terms / 关键术语：** polling / 轮询；Server-sent Events (SSE) / 服务端事件；EventSource / EventSource 接口；Fetch response stream / Fetch 响应流；WebSocket / WebSocket；replay cursor / 重放游标。

~~~mermaid
flowchart TD
    Direction{Which update direction?}
    Direction -->|occasional or client-controlled| Poll[Polling or long polling]
    Direction -->|server to client only| RequestShape{Need custom method, headers, or body?}
    RequestShape -->|no; GET and simple contract| SSE[SSE with EventSource]
    RequestShape -->|yes| Fetch[Fetch response stream]
    Direction -->|both directions| WS[WebSocket]
    Poll --> Resume[Define cursor, status lookup, or replay]
    SSE --> Resume
    Fetch --> Resume
    WS --> Resume
    Resume --> UI[Client reconstructs authoritative state]
~~~

## 轮询、SSE、流式Fetch与WebSocket / Polling, SSE, streaming Fetch, and WebSocket

| 方式 Transport | 方向与请求契约 Direction and request contract | 连接恢复 Recovery | 适用场景与边界 Fit and boundary |
|---|---|---|---|
| 轮询 Polling | 客户端按间隔发起普通HTTP请求；长轮询会让服务端暂挂一次请求直到有事件或超时。 | 客户端决定频率、退避和何时重试；若需续传，由API定义游标或事件ID。 | 实现简单、适合低频更新；短轮询带来请求开销，长轮询占用等待中的请求。 |
| SSE格式 + `EventSource` API | 服务端向客户端单向发送HTTP `text/event-stream`；EventSource用URL建立GET请求，可选择`withCredentials`。 | EventSource通常会在连接中断后自动重连；服务端可用HTTP 204告知客户端停止重连。带`id:`的事件会在后续重连请求中作为`Last-Event-ID`回传。服务器只有保留可重放的事件历史，才能按该ID续传。 | 适合单向事件；原生EventSource接口没有自定义请求头或请求体，不能把传输断线等同于事件已恢复。 |
| 流式Fetch / Fetch response stream | 一次Fetch请求在响应有body时提供可逐块读取的`Response.body`；请求可使用API允许的方法、请求头、请求体和取消信号。 | Fetch不会替应用实现SSE式自动重连或重放；应用解析协议帧并定义游标、重试和取消策略。 | 需要自定义请求契约或一次性POST后流式返回时合适；字节块不是消息边界。跨源读取仍受CORS约束。 |
| WebSocket | 握手后，客户端和服务端都能沿同一连接发送消息。应用收到的是完整消息，传输层可将一条消息拆成多个帧。 | 重连、身份过期、事件序号、确认和恢复均由应用协议定义。 | 双向低延迟交互合适；长期连接需要连接生命周期管理。浏览器构造器没有任意请求头参数，握手认证要按浏览器可用契约设计。 |

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


**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](http-protocols-and-websockets.md) covers request methods, caches, CORS, DNS, and transport behavior; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) explains how the interface represents partial, reconnecting, cancelled, and terminal states; [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md) uses persistent run state to recover after a client disconnect.

**Sources / 来源：** [RFC 6455, The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html), [RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html), [RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html), [WHATWG HTML Server-sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html), [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/), [WHATWG Streams Standard](https://streams.spec.whatwg.org/), and [WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/) checked 2026-10-15. The SSE reconnection and HTTP 204 boundary was rechecked against the current WHATWG HTML standard on 2026-10-27. See also the MDN [WebSocket constructor](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket) and the Node.js [ws implementation](https://github.com/websockets/ws).
