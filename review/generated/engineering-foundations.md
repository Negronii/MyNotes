# Engineering Foundations

> Generated from the [engineering-foundations reading map](../../engineering-foundations/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. HTTP Protocols and WebSockets / HTTP协议与WebSocket

### HTTP Protocols and WebSockets / HTTP协议与WebSocket

> **核心解释 / Core idea：** HTTP定义客户端与服务器交换表示、状态和元数据的语义；TCP、QUIC等传输机制决定字节或流如何送达。HTTP版本改变了连接复用与多路复用方式，但不会让请求自动安全、可重试或跨域可读。  
> **Core idea:** HTTP defines the semantics for exchanging representations, status, and metadata between clients and servers; transports such as TCP and QUIC determine how bytes or streams are delivered. HTTP versions change connection reuse and multiplexing, but do not by themselves make requests safe to retry or readable across origins.
>
> **面试简答 / Interview answer：** REST是约束式架构风格，HTTP API通常用资源URI和标准方法表达操作；判断重试要看方法语义和业务副作用。HTTP/1.1默认复用连接，HTTP/2在TCP连接上多路复用但仍受TCP丢包队头阻塞影响，HTTP/3通过QUIC独立流减轻跨流阻塞。浏览器CORS控制跨源响应能否被页面读取；传统WebSocket通过HTTP/1.1 Upgrade建立双向通道，HTTP/2、HTTP/3也有扩展连接机制。  
> **Interview answer:** REST is a constrained architectural style, and HTTP APIs commonly express operations through resource URIs and standard methods; retry decisions depend on method semantics and application side effects. HTTP/1.1 reuses connections by default, HTTP/2 multiplexes over TCP but still has TCP-level head-of-line blocking, and HTTP/3 uses QUIC streams to reduce cross-stream blocking. Browser CORS controls whether a page can read a cross-origin response. Traditional WebSockets use an HTTP/1.1 Upgrade handshake, while HTTP/2 and HTTP/3 define extended connection mechanisms.

#### REST与HTTP方法 / REST and HTTP methods

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

#### HTTP消息、请求头与状态码 / HTTP messages, fields, and status codes

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

#### 缓存协商 / Cache validation

缓存可减少传输和等待，但必须区分“是否存储”和“使用前是否验证”。Cache-Control: max-age给出新鲜期；no-cache允许存储，但使用前需向源站验证；no-store要求缓存不要存储该响应。它们的语义不能互换。[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) 定义HTTP缓存。

常见的ETag协商流程：

1. 响应携带ETag，客户端缓存表示及验证器。
2. 缓存条目过期后，客户端发送If-None-Match并带上该验证器。
3. 若资源未变化，服务器返回304，客户端复用缓存表示；若已变化，服务器返回新表示及其验证器。

协商缓存避免重复传输未变化的内容，但是否允许存储仍由缓存策略和隐私要求决定。不要把no-cache写成“禁止缓存”。

#### 浏览器请求API / Browser request APIs

XMLHttpRequest（XHR）仍用于维护旧代码或需要其事件接口的场景，例如上传进度；Fetch是现代浏览器常用的Promise API。两者都需要处理网络失败、取消和HTTP错误等情况。Fetch遇到HTTP 404/500不会自动抛出异常：

~~~javascript
const response = await fetch('/api/data');

if (!response.ok) {
  throw new Error('HTTP ' + response.status);
}

const data = await response.json();
~~~

XHR可以读取状态和响应文本，但应用通常还需自行解析JSON并处理网络错误。Axios是第三方HTTP客户端，常见特性包括响应数据转换、拦截器及可配置的错误判断；它的默认状态码判断通常接受2xx并将其他状态作为错误处理。选择哪种API应服从项目依赖与需求，而不是把某个库的行为误认为HTTP协议保证。[Axios响应结构](https://axios-http.com/docs/res_schema) 与 [Axios错误处理](https://axios-http.com/docs/handling_errors)。

#### 网络分层与TCP / Network layers and TCP

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

#### HTTP/1.1、HTTP/2与HTTP/3 / HTTP versions

| 版本 Version | 连接与多路复用 Connection and multiplexing | 关键边界 Key caveat |
|---|---|---|
| HTTP/1.0 | 通常响应后关闭连接；后来出现Keep-Alive扩展 | 不是现代HTTP/1.1默认持久连接语义 |
| HTTP/1.1 | 默认持久连接，可复用多个请求/响应；同一连接的流水线响应仍按请求顺序返回 | 串行等待或有序响应可能增加延迟；浏览器可使用多个连接 |
| HTTP/2 | 在一个TCP连接上用多个流并发交换帧，使用HPACK压缩字段 | TCP要求字节有序；一个TCP段丢失可能阻塞该连接上尚未交付的数据 |
| HTTP/3 | 在QUIC连接上承载多个HTTP流；QUIC运行在UDP之上并提供可靠流 | 一个流丢失的数据不必阻塞其他流交付，但流仍受共享拥塞控制等连接级影响 |

HTTP/1.1连接默认持久，但持久连接不等于并行响应；RFC规定流水线响应按请求顺序发送。HTTP/2的应用层多路复用减少了每个请求单独占用连接的需要，却无法改变底层TCP有序字节流的传输层队头阻塞。HTTP/3把流建立在QUIC上：QUIC可在一个流丢包时继续交付其他可用流的数据，但仍共享连接的拥塞控制和部分流控资源。[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)、[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)、[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)、[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)。

HTTP/3使用QUIC而不是“把HTTP直接放在UDP上”：QUIC本身提供连接管理、加密协商和可靠流。会话恢复时可能使用0-RTT数据，但该数据在某些路径上可被重放；有副作用的请求不能仅凭0-RTT就当成安全重试。[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)。

#### CORS与浏览器同源策略 / CORS and the same-origin policy

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

#### WebSocket：握手与双向消息 / WebSocket handshake and full-duplex messaging

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

HTTP持久连接（keep-alive）可以在多个HTTP请求/响应间重用连接，但服务器仍需等待请求，不能在没有请求时任意推送HTTP响应。WebSocket提供双方都可发消息的通道。若只需服务器到浏览器的单向事件流，可比较EventSource（Server-Sent Events）；更新稀少时，轮询也可能更简单。[ws项目文档](https://github.com/websockets/ws)。

#### 浏览器资源提示 / Browser resource hints

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

#### 相关主题 / Related notes

- [浏览器基础 / Browser Basics](../../frontend/browser/browser-basics.md)：浏览器的请求、渲染和安全边界。
- [Web安全与身份认证 / Web Security and Authentication](#5.%20Web%20Security%20and%20Authentication%20/%20Web%E5%AE%89%E5%85%A8%E4%B8%8E%E8%BA%AB%E4%BB%BD%E8%AE%A4%E8%AF%81)：CORS之外的认证、Cookie与请求保护。
## 2. Processes, Threads, and Concurrency / 进程、线程与并发

### Processes, Threads, and Concurrency / 进程、线程与并发

**Core model / 核心模型：** A process is an operating-system resource and protection boundary; a thread is an execution path inside a process. Threads share much of that process's memory and therefore need coordination when they update shared state. Concurrency means work overlaps in time; parallelism means work executes at the same time on multiple processing units. Asynchronous I/O can provide concurrency without assigning one thread to every waiting operation. / 进程是操作系统管理资源并隔离地址空间的边界；线程是在进程内执行指令的路径。线程共享进程中的许多内存，因此并发修改共享状态时需要协调。并发表示任务的执行时间重叠；并行表示多个处理单元同时执行任务。异步 I/O 可以在不为每个等待中的操作分配一个线程的情况下提高并发能力。

**Key terms / 关键术语：** process / 进程；thread / 线程；address space / 地址空间；concurrency / 并发；parallelism / 并行；blocking I/O / 阻塞 I/O；non-blocking I/O / 非阻塞 I/O；asynchronous I/O / 异步 I/O；race condition / 竞态；deadlock / 死锁；cancellation / 取消。

#### Process and thread / 进程与线程

| Aspect / 维度 | Process / 进程 | Thread / 线程 |
| --- | --- | --- |
| Memory / 内存 | Has its own virtual address space in the usual process model. Processes can explicitly map shared memory. / 通常拥有独立的虚拟地址空间；也可以显式映射共享内存。 | Threads in one process share its address space and global data; each thread has its own execution state and stack. / 同一进程中的线程共享地址空间和全局数据；每个线程有自己的执行状态和栈。 |
| Communication / 通信 | Uses an explicit boundary such as a pipe, socket, message, or shared mapping. / 通过管道、套接字、消息或共享映射等显式边界通信。 | Can pass references through shared memory, but concurrent access must follow a synchronization rule. / 可通过共享内存传递引用，但并发访问必须遵循同步规则。 |
| Typical choice / 常见选择 | Prefer when a fault or trust boundary matters, or work needs separate process lifetime. / 当故障或信任隔离、独立进程生命周期很重要时考虑使用。 | Prefer when work benefits from shared process state or CPU-parallel execution and the program can manage synchronization. / 当工作需要共享进程状态或 CPU 并行执行，且程序能管理同步时考虑使用。 |

These are useful defaults, not cost or isolation guarantees for every operating system. A process can deliberately share memory or handles; a thread does not automatically make CPU work faster. For Node-specific choices among its event loop, worker threads, and child processes, see [Node.js Fundamentals / Node.js基础](#9.%20Node.js%20Fundamentals%20/%20Node.js%E5%9F%BA%E7%A1%80).

#### Concurrency, parallelism, and I/O / 并发、并行与 I/O

Tasks are **concurrent** when their progress overlaps—for example, a server starts another request while the first waits for a response. They are **parallel** when instructions from both tasks execute at the same instant on separate cores or other processing units. A single event-loop thread can coordinate many waiting I/O operations, but a long synchronous callback still prevents that thread from running other callbacks. CPU parallelism needs another execution resource, such as a worker thread or process.

| I/O style / I/O 方式 | What the caller observes / 调用方观察到的行为 |
| --- | --- |
| Blocking / 阻塞 | The calling thread waits until the operation can make progress or completes. / 调用线程等待操作可以继续或完成。 |
| Non-blocking / 非阻塞 | An attempt returns promptly when it cannot proceed; the caller can wait for readiness or try again. A non-blocking result does not itself mean the full transfer completed. / 暂时无法继续时，调用立即返回；调用方可等待就绪或稍后重试。非阻塞返回本身不表示数据已经全部传输完成。 |
| Asynchronous / 异步 | The caller submits work and receives a later completion or callback. The runtime may use operating-system readiness, a completion facility, or a worker pool. “Async” describes the interface and scheduling relationship, not one universal implementation. / 调用方提交工作，随后接收完成通知或回调。运行时可能使用操作系统就绪通知、完成机制或工作线程池。“异步”描述接口与调度关系，并不对应唯一实现。 |

In Node.js, synchronous filesystem APIs block the event-loop thread. Callback- and promise-based filesystem APIs use libuv's thread pool except `fs.FSWatcher`; many network operations are driven by the operating system. Exact APIs have their own contracts. Async I/O therefore helps waiting workloads, but moving CPU-heavy JavaScript off the event loop requires workers or processes. See the [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) note for scheduling details.

#### Races and deadlocks / 竞态与死锁

A **race condition / 竞态** exists when the result depends on the timing or order of operations that access shared state. For example, an increment is a read–modify–write sequence: two workers can both read `10`, compute `11`, then each write `11`, losing one increment. Protect the invariant with a lock, an atomic operation, a single owner that processes messages, or a database constraint—whichever matches the boundary. In JavaScript, synchronous code in one event-loop turn runs to completion, but state can still change between `await` points; worker threads that share a `SharedArrayBuffer` need an explicit synchronization protocol.

A **deadlock / 死锁** occurs when tasks wait in a cycle. If worker A holds lock L1 and waits for L2 while worker B holds L2 and waits for L1, neither can continue. Consistent lock ordering and short critical sections prevent many such cycles. Avoid holding a lock while waiting on network or other unbounded work; a timeout can reveal a stuck wait, but does not by itself restore a partially changed invariant.

#### Cancellation and cleanup / 取消与清理

Cancellation is a request to stop work, not proof that work has stopped or that its side effects were undone. Many APIs use cooperative cancellation: code checks a token, stops at a safe boundary, and releases resources or leaves shared state consistent. In POSIX threads, deferred cancellation is the default and takes effect at cancellation points; asynchronous cancellation can interrupt code while it holds a resource. Runtime and API contracts differ, so check whether the operation actually observes cancellation. In particular, cancelling a caller's wait does not retract a request that a remote service already accepted.

#### A runnable shared-counter example / 可运行的共享计数示例

The two workers below share one integer. `Atomics.add` makes each read–modify–write increment one synchronized operation; after both workers exit, the expected count is `200000`. Without an atomic operation or another coordination rule, increments can be lost.

~~~javascript
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const workers = Array.from(
    { length: 2 },
    () => new Worker(__filename, { workerData: shared }),
  );

  const waitForExit = worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => {
      if (code === 0) resolve();
      else reject(new Error(`worker exited with code ${code}`));
    });
  });

  Promise.all(workers.map(waitForExit)).then(() => {
    console.log(Atomics.load(new Int32Array(shared), 0));
  }).catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
} else {
  const counter = new Int32Array(workerData);
  for (let i = 0; i < 100_000; i++) Atomics.add(counter, 0, 1);
}
~~~

Verified with Node.js v26.11.1; observed output: `200000`. This checks one local runtime example, not performance scaling or every platform's worker implementation.

**Related notes / 相关笔记：** [Node.js Fundamentals / Node.js基础](#9.%20Node.js%20Fundamentals%20/%20Node.js%E5%9F%BA%E7%A1%80) applies these process and worker boundaries to Node's APIs; [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) explains how queued callbacks make progress on a JavaScript thread.

**Sources / 来源：** POSIX.1-2024 [General Information, process and thread model](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html); Linux [`pthreads(7)`](https://man7.org/linux/man-pages/man7/pthreads.7.html), for Linux/POSIX thread-sharing and cancellation-point details; Node.js v24 [worker_threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html) and [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html#threadpool-usage) documentation, checked 2026-10-15. The filesystem docs specify that callback and promise APIs except `fs.FSWatcher` use libuv's thread pool.
## 3. Database Fundamentals / 数据库基础

### Database Fundamentals / 数据库基础

**Core model / 核心模型：** A database schema names the data and constraints that every writer must respect. Queries describe the result; a planner chooses how to produce it, using indexes when their cost is worthwhile. Transactions group changes, while an isolation policy defines what concurrent transactions can observe. A write-ahead log (WAL) helps a database recover after a crash, subject to that product's durability and backup configuration. / 数据库模式描述数据及所有写入方都必须遵守的约束。查询描述所需结果，执行计划器再选择实现方式，并在成本合适时使用索引。事务将多个变更组合起来；隔离级别定义并发事务能够观察到什么。预写日志（WAL）帮助数据库在崩溃后恢复，但具体保证取决于产品的持久性与备份配置。

**Key terms / 关键术语：** schema / 模式；primary key / 主键；foreign key / 外键；constraint / 约束；index / 索引；query plan / 查询计划；transaction / 事务；isolation level / 隔离级别；MVCC / 多版本并发控制；write-ahead log (WAL) / 预写日志。

#### Schema and constraints / 模式与约束

A relational schema defines tables, columns, types, and relationships. A **primary key** identifies a row; a **unique constraint** prevents duplicate key values; a **foreign key** requires a reference to an existing key (subject to the constraint's null and deferral rules); and `NOT NULL` and `CHECK` constrain allowed values. Put durable business invariants in database constraints as well as validating input in the application: another job, script, or service may write the same tables. Referential actions such as `ON DELETE CASCADE` encode an additional lifecycle rule and should match the data relationship.

The following SQL uses common table and constraint syntax. It describes customers and orders, ensures an order has a customer and a non-negative amount, and adds an access path for a customer's recent orders. The query asks for rows; the database decides whether and how to use the index. The `?` is a bound-parameter placeholder used by SQLite; other drivers use their own placeholder notation.

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    placed_at TEXT NOT NULL
);

CREATE INDEX orders_by_customer_and_time
    ON orders(customer_id, placed_at);

SELECT order_id, amount_cents, placed_at
FROM orders
WHERE customer_id = ?
ORDER BY placed_at DESC;
~~~

An index is a maintained access path, not a promise that every query will be faster. It uses storage and adds work to inserts, updates, and deletes. A multicolumn B-tree index is ordered by its leading columns, so `(customer_id, placed_at)` can support a lookup by customer and then a time ordering; the best plan still depends on the query, table size, data distribution, statistics, and database engine. Inspect a plan with that engine's `EXPLAIN` facility and compare it with representative data. In PostgreSQL, `EXPLAIN ANALYZE` executes the statement and reports observed work, while plain `EXPLAIN` shows the planner's estimated strategy. Plan output and choices are product- and version-specific.

#### Transactions and isolation / 事务与隔离

A transaction gives a set of statements one commit or rollback boundary. **ACID** is a useful vocabulary, with each property still bounded by implementation and configuration:

- **Atomicity / 原子性:** the transaction's changes commit together or are rolled back together.
- **Consistency / 一致性:** constraints and application rules define valid states; the database does not invent the business rules.
- **Isolation / 隔离性:** concurrent transactions see behavior controlled by the isolation level and engine implementation.
- **Durability / 持久性:** a successful commit survives the failures covered by the database's configured durability and storage assumptions.

Consider reserving one remaining unit. Do not read the count in the application and then issue an unconditional write: concurrent requests can both act on the same old value. Prefer one conditional update, check that exactly one row changed, insert the reservation in the same transaction, and roll back if either step fails. The exact concurrency guarantee depends on the engine's atomic-update, locking, and isolation contract; verify it for the selected database.

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = ? AND available > 0;

-- Continue only if exactly one row was updated.
INSERT INTO reservations (request_id, sku) VALUES (?, ?);

COMMIT;
~~~

Assume `inventory.sku` is unique. If the update changes zero rows or the insert fails, roll back instead of committing. This example relies on the database's transaction and row-update semantics; unique constraints can also enforce that a `request_id` is not applied twice. A transaction cannot make a remote side effect atomic with the local database unless both participants share a protocol that provides that guarantee.

SQL isolation names are not a complete description of every engine's behavior. Common anomalies include a **dirty read** (seeing another transaction's uncommitted write), a **non-repeatable read** (seeing a changed row on a later read), a **phantom read** (a repeated predicate query returns a different set), and a **serialization anomaly** (the committed result cannot be explained by any serial ordering). Check the selected product's manual rather than transferring an isolation-level label from another database.

**PostgreSQL 18 example:** the default Read Committed level takes a new snapshot for each statement; Repeatable Read keeps a transaction snapshot and can abort a conflicting update; Serializable detects additional dependency patterns and can abort a transaction that must then be retried from the beginning. These are PostgreSQL behaviors, not universal definitions of those level names.

##### MVCC / 多版本并发控制

With **multi-version concurrency control (MVCC)**, a database keeps versions or visibility metadata so a statement or transaction can read a snapshot while concurrent transactions make changes. This can reduce reader–writer blocking, but does not remove write conflicts, explicit locks, or every wait. Engines that retain row versions need cleanup; PostgreSQL, for example, uses vacuuming to reclaim versions that are no longer visible, and long-running snapshots can delay that cleanup. MVCC is a concurrency-control mechanism, not a promise that all reads are lock-free or that every engine uses the same version rules.

#### WAL and recovery boundaries / WAL 与恢复边界

The write-ahead rule is that changes to data pages are written only after the corresponding log records have been flushed to durable storage. A commit can be reported durable after the required log records are safely flushed under the configured policy; a later crash can then use the log to redo changes not yet copied into data pages. Settings that weaken synchronous commit or storage guarantees can weaken what a successful response means. WAL supports crash recovery; point-in-time recovery additionally requires a suitable base backup and the needed archived log range.

Recovery algorithms are product-specific. The archived database course keeps the detailed ARIES analysis, including the Dirty Page Table and its `recLSN` rule, in [Log-based Crash Recovery / 基于日志的崩溃恢复](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). In ARIES, `recLSN` is the earliest log record that could have dirtied that page since it was last clean; it is not a universal WAL field or redo rule.

#### Distributed database boundaries / 分布式数据库的边界

Two nearby concepts are useful boundaries, not a distributed-systems survey:

- **CAP:** during a network partition, a system cannot guarantee both linearizable consistency and an eventual response to every request at a non-failed node. Partition is the assumed failure; the trade-off is which operations may be rejected or may observe stale data. See Gilbert and Lynch's [CAP result](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf) and the archived [CAP theorem / CAP 定理](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md) discussion.
- **Two-phase commit (2PC):** a participant that has durably prepared and voted YES must wait for the coordinator's decision. A timeout after YES is not a safe local abort, so the participant can remain blocked until it learns that decision. 2PC coordinates an atomic commit decision; it does not itself provide transaction isolation. See PostgreSQL's [prepared-transaction documentation](https://www.postgresql.org/docs/18/sql-prepare-transaction.html) and the archived [2PC notes](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md).

**Course material kept in the archive / 保留在归档中的课程内容：** the detailed RAID calculations, R-tree/spatial-index examples, snapshot-isolation exercises, and recovery derivations remain in [week 1 RAID calculations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w1.md), [week 2 R-tree/spatial-index examples](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w2.md), [week 3 snapshot-isolation exercises](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w3.md), and [week 4 recovery derivations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). The active note provides the shared model; the course files preserve their derivations and exercises.

**Related notes / 相关笔记：** [Core Data Structures / 核心数据结构](#7.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84) introduces the tree structures behind common indexes; the [archived database course](../../archive/uni-subjects/COMP90050ADBS/readme.md) preserves its broader sequence of worked examples.

**Sources and verification / 来源与验证：** PostgreSQL 18 documentation checked 2026-10-15: [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [indexes](https://www.postgresql.org/docs/18/indexes.html), [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html), [MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html), [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [WAL](https://www.postgresql.org/docs/18/wal-intro.html), [WAL configuration and recovery](https://www.postgresql.org/docs/18/wal.html), and [prepared transactions](https://www.postgresql.org/docs/18/sql-prepare-transaction.html). SQLite's [foreign-key](https://www.sqlite.org/foreignkeys.html), [transaction](https://www.sqlite.org/lang_transaction.html), [query planner](https://www.sqlite.org/queryplanner.html), and [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) documentation support the SQL examples; plan wording is diagnostic output, not an API. The schema/query and reservation transaction were run with Python's sqlite3 module against SQLite 3.51.0, with foreign-key enforcement enabled; for 1,000 synthetic orders, this run changed from a table scan plus temporary sort to an index search after adding the composite index. That is one planner observation, not a stable output contract. The original recovery method is Mohan et al., [ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging); its DPT and `recLSN` mechanism is explained in the [CMU database recovery notes (pp. 1, 4–6)](https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf).
## 4. API Reliability and Asynchronous Delivery / API可靠性与异步交付

### API Reliability and Asynchronous Delivery / API可靠性与异步交付

**Core model / 核心模型：** Every network or queue boundary can delay, lose, duplicate, or ambiguously report work. Bound how long and how much work is admitted; make retries safe for the operation's semantics; acknowledge only at the intended completion boundary; expose failures so that a timeout or growing queue cannot silently become data loss. / 每个网络或队列边界都可能延迟、丢失、重复或含糊地报告工作。应限制等待时间与准入工作量；重试必须符合操作语义；只在达到预期完成边界后确认；并显式暴露失败，避免超时或不断增长的队列悄然演变成数据丢失。

**Key terms / 关键术语：** timeout / 超时；deadline / 截止时间；cancellation / 取消；unknown outcome / 结果未知；retry / 重试；backoff / 退避；jitter / 抖动；idempotency / 幂等性；backpressure / 背压；acknowledgement / 确认；redelivery / 再投递。

#### Timeouts, deadlines, and cancellation / 超时、截止时间与取消

A **timeout** limits one wait or operation. A **deadline** is the latest acceptable completion time for the whole request. If each downstream call starts a fresh full timeout, a multi-hop request can run far beyond the caller's budget. Carry a deadline or remaining time downstream, reserve time for cleanup and the response, and derive limits from measured latency and the product's failure policy; there is no universal timeout value. Connection setup and response waiting may need separate limits if the client library treats them separately.

Cancellation tells work that its result is no longer needed. Propagate it to downstream calls and check it at safe points so unnecessary computation stops and resources are released. Support depends on each runtime and API; cancellation is often cooperative. It does not prove that a remote service stopped or undid a side effect. If a caller's deadline expires after a write was accepted, the caller may know only that the **outcome is unknown**.

#### Retries, backoff, and idempotency / 重试、退避与幂等

Retry only when the failure may be transient and the operation is safe to repeat, or when the client can determine that the first attempt was not applied. A timeout or lost response alone cannot establish that no effect occurred. HTTP's idempotent-method definition concerns the intended effect of repeated requests; it does not make every application side effect disappear, and a non-idempotent method should not be retried automatically without application-specific evidence.

A capped exponential schedule with randomized jitter spreads retries rather than making clients retry together:

~~~text
cap(n)  = min(max_delay, base_delay × 2^n)
wait(n) = random value from 0 through cap(n)  # one full-jitter variant
~~~

The base delay, cap, attempt limit, and total retry budget are service choices derived from the deadline and downstream capacity, not universal defaults. Stop when the remaining deadline cannot accommodate another useful attempt. Avoid retries at several layers: if five layers each make three attempts, one logical request can produce `3^5 = 243` downstream attempts. Retrying at one deliberate boundary is often easier to bound and observe.

For a write that can be retried, an **idempotency key** or operation identifier lets the service recognize a repeated logical request. The service should define the key's scope and retention, associate it with the request parameters, and persist the operation result so the same key and same request can return the existing outcome; reuse with different parameters should be rejected or otherwise explicitly defined. The deduplication record and local database effect need one atomic boundary. If the side effect is in another service, that service must provide compatible idempotency or the caller needs a reconciliation path; a local key cannot make an unrelated remote effect atomic.

**Hypothetical example / 假设示例：** A refund service accepts a request, records the refund, and loses its response before the client deadline. The client cannot distinguish “refund committed” from “request never arrived.” If the client retries with the same operation key, the service can return the recorded refund result instead of issuing another refund—provided the key record and refund state were committed together and the service retains that record for the documented retry window. Without those assumptions, the caller must query or reconcile the outcome rather than blindly issue a second refund. The numbers and service behavior here are illustrative, not a provider contract.

#### Concurrency limits and backpressure / 并发限制与背压

Bound in-flight requests, worker count, and any waiting queue. A queue that can grow without limit converts overload into growing memory use and delay. When a bound is reached, choose an explicit policy—wait within the deadline, reject, defer to durable storage, or shed work that can safely be dropped. Keep queue time inside the request's latency budget and report overload distinctly from successful completion.

Under steady-state conditions, Little's Law, `average in-flight requests = arrival rate × average time in system`, gives a planning check rather than a capacity guarantee. For example, a hypothetical average arrival rate of 40 requests/second and 0.2 seconds of average time in the chosen system—including its queue and service—implies about `40 × 0.2 = 8` average in-flight requests. Bursts, latency distribution, retries, and downstream limits still require measurement; eight is not a universal concurrency cap.

#### Queue acknowledgements, duplicates, and order / 队列确认、重复与顺序

Publishing and consuming have separate failure boundaries. A publisher confirm covers publisher-to-broker acceptance under that broker's rules; it does not say that a consumer applied the business change. A consumer acknowledgement should follow the work that the system defines as complete. If the consumer commits a change and crashes before acknowledging, a broker may redeliver the message; make processing idempotent or deduplicate by a stable message or operation key. If it acknowledges before durable work, a crash can lose the work.

Delivery and ordering semantics belong to a particular broker, queue type, acknowledgement mode, and consumer arrangement. For example, with manual acknowledgements RabbitMQ requeues unacknowledged deliveries when the channel or connection closes; consumers therefore need to handle redeliveries. Concurrent consumers can finish work in a different order from delivery, so use a per-key sequence or serialized consumer when completion order is a correctness rule. A dead-letter queue makes a failed message visible only if it is monitored and someone has defined whether to repair, retry, or discard it.

Observe each boundary separately: accepted and rejected requests, timeout and cancellation counts, in-flight work, queue depth and oldest-message age, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A queue that keeps accepting messages while its oldest item grows is accumulating delay, not demonstrating health.

**Related notes / 相关笔记：** [Database Fundamentals / 数据库基础](#3.%20Database%20Fundamentals%20/%20%E6%95%B0%E6%8D%AE%E5%BA%93%E5%9F%BA%E7%A1%80) covers the transaction boundary used to persist business effects and idempotency records, plus the limited CAP and 2PC context; [Node.js Fundamentals / Node.js基础](#9.%20Node.js%20Fundamentals%20/%20Node.js%E5%9F%BA%E7%A1%80) applies concurrency and shutdown limits to a Node service; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#1.%20HTTP%20Protocols%20and%20WebSockets%20/%20HTTP%E5%8D%8F%E8%AE%AE%E4%B8%8EWebSocket) covers the transport and request semantics.

**Sources / 来源：** [RFC 9110, HTTP Semantics §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2); [AWS Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), checked 2026-10-15; gRPC [Deadlines](https://grpc.io/docs/guides/deadlines/) and [Cancellation](https://grpc.io/docs/guides/cancellation/) guides; RabbitMQ 4.3 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms), checked 2026-10-15, for its manual-ack requeue and publisher-confirm boundaries; Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and the queue-plus-service system boundary.
## 5. Web Security and Authentication / Web安全与身份认证

### Web Security and Authentication / Web安全与身份认证

**身份认证 / Authentication** establishes which identity or credential is presenting a request. **授权 / Authorization** decides whether that identity may perform this action on this resource. Authentication alone does not grant every permission; enforce authorization on the server for each protected operation. Client checks can improve the interface but cannot decide access.

身份认证回答请求以谁的凭据发出，授权则逐项决定该身份能否访问资源或执行操作；浏览器编码、Cookie属性、CORS、CSRF和CSP处理的是不同边界，不能替代服务端授权或彼此替代。

#### Cookies vs. tokens — which to use for authentication?

**Cookie 会话与令牌 / Cookie sessions and tokens** are transport and session choices, not two complete security models. Choose according to the clients, domain boundaries, revocation needs, and threat model.

A server-side session commonly works like this:

1. The user authenticates; the server creates a session and stores its state.
2. The server returns an opaque session identifier in a cookie.
3. The browser sends that cookie only when its domain, path, security, SameSite, and request rules match.
4. The server resolves the session and performs authorization for the requested action.

For a session cookie, consider:

- **HttpOnly** prevents page JavaScript from reading the cookie through APIs such as `document.cookie`. It does not stop injected JavaScript from making authenticated requests as the user.
- **Secure** limits transmission to secure channels such as HTTPS.
- **SameSite=Strict, Lax, or None** controls cookie sending in cross-site contexts. It is a site-level browser rule, not an origin or authorization boundary. Specify the value; browser defaults can vary. `SameSite=None` requires `Secure`.
- Cookie scope and size have implementation constraints; do not use `Domain` or `Path` as authorization checks.

A bearer token is presented by the client, commonly in an `Authorization: Bearer` header. A JWT is one token format: a signed JWT normally protects integrity, but its claims are readable unless it is encrypted. A valid signature proves that a trusted key signed the token; it does not by itself authorize every action. Verifiers must validate the expected algorithm, issuer, audience, token type, and time claims according to the application protocol. Use short-lived tokens and a deliberate rotation or revocation strategy where needed.

A JWT can carry claims without a per-request session lookup, but revocation and fresh permission changes then need an explicit design. The JWT format does not bypass browser origin rules or CORS. A token stored in browser-accessible storage can be read by injected JavaScript; an HttpOnly cookie reduces that direct theft path but still needs a CSRF design. Neither storage choice fixes XSS or authorization flaws.

---

#### What is Single Sign-On (SSO), and how does it work?

**单点登录 / Single Sign-On** lets a user authenticate through an identity provider and establish sessions with multiple relying applications. Each application still validates the protocol response and applies its own authorization rules.

OAuth 2.0 is an authorization framework for delegated access; OAuth alone is not an authentication protocol. **OpenID Connect / OpenID Connect 身份层** builds an identity layer on OAuth 2.0 and defines the ID Token. An access token and an ID Token serve different purposes: do not treat either as proof for an unrelated audience.

In a typical redirect flow, the relying application creates a login request, the identity provider authenticates the user, and the application validates the response before creating its own session. Protocol details matter: validate the redirect target and issuer, and apply the relevant state, nonce, signature, and audience checks for the flow.

See [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).

---

#### How does HTTPS protect against man-in-the-middle attacks?

**HTTPS / TLS** protects data in transit against network eavesdropping and tampering when the connection is correctly configured and the client validates the server. In a certificate-authenticated TLS 1.3 handshake, key agreement derives traffic keys; the server's certificate and handshake signature authenticate the server's key. The server does not simply encrypt a session key with its public key as in older textbook handshake descriptions.

A client checks the certificate chain and that the certificate is valid for the requested hostname, then verifies the handshake. Certificate status and revocation handling depend on the client and deployment, so do not describe revocation checking as a universal guaranteed browser step. A trusted certificate does not authenticate the application's user; application authentication and authorization remain separate.

- **Symmetric cryptography / 对称密码** protects application traffic efficiently after handshake keys are established.
- **Public-key cryptography / 公钥密码** supports key agreement and authentication in the handshake; the TLS 1.3 suite and configuration determine the exact mechanisms.

See [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html).

---

#### XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**跨站脚本 / XSS** occurs when untrusted data is interpreted as active content in a page. Script that executes in an origin can read data available to that script and make requests from that origin; an HttpOnly cookie blocks direct cookie reading but does not stop such requests.

Use the defense that matches the output context:

1. Render plain text through framework APIs that treat it as text, and encode values for their HTML, attribute, URL, JavaScript, or CSS context.
2. If user-authored rich HTML is required, sanitize it with a maintained HTML sanitizer and keep the allowed markup narrow.
3. Avoid inserting untrusted strings into `innerHTML`, `document.write`, inline event handlers, `eval`, or `new Function`. Framework escape defaults do not protect deliberate raw-HTML escape hatches.
4. Add a carefully tested Content Security Policy as defense in depth. Nonce- or hash-based strict policies can restrict script execution; an allowlist such as `script-src 'self'` alone is not a universal XSS fix.

Before assigning an untrusted value to `href` or `src`, validate the complete URL's scheme and destination against the application's policy (for example, reject `javascript:`); output encoding for the attribute does not replace URL validation.

CSP can reduce the impact of some injection paths, but it does not replace safe rendering and sanitization. See OWASP's [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) and [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) guidance.

---

#### CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**跨站请求伪造 / CSRF** abuses ambient browser credentials: a site can cause a browser to send some cross-site requests, and the browser may attach cookies that match the destination. The attacker often cannot read the response, but reading it is not required to cause a state change.

For state-changing cookie-authenticated requests, use an application-validated CSRF token or an equivalent well-reviewed pattern. Check the request origin where appropriate, and use SameSite as defense in depth. Do not mutate state on safe methods such as GET. SameSite=Lax still permits some top-level safe-method navigations, and sibling subdomains can be same-site; it does not replace authorization or every CSRF defense.

**SameSite=None requires Secure.** Also account for legitimate cross-site login and embedded flows rather than silently weakening checks. See the [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

---

#### What is CORS?

**跨源资源共享 / Cross-Origin Resource Sharing (CORS)** is a browser protocol that controls when a script may read a cross-origin response. It is not authentication, authorization, or a general firewall: some cross-origin requests can still be sent even when browser JavaScript cannot read the response, and non-browser clients do not enforce CORS.

For a credentialed browser request, the client must opt in to credentials and the response must name an allowed origin rather than `Access-Control-Allow-Origin: *`, with `Access-Control-Allow-Credentials: true`. Preflight requests are checked separately. Use an explicit origin allowlist; reflecting arbitrary Origin values can expose credentialed responses.

CORS does not make an endpoint private. Authenticate and authorize the server request even if the intended browser client is the only one expected to call it. See the [WHATWG Fetch Standard, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials).

---

#### Clickjacking — what is it, how do you prevent it?

**点击劫持 / Clickjacking** tricks a user into interacting with a page framed beneath or inside deceptive content. Use the CSP `frame-ancestors` directive to state which sites may embed the page; use `X-Frame-Options` where legacy client support requires it. These headers control framing, not user authorization.

For example, `Content-Security-Policy: frame-ancestors 'self'` permits framing by the same origin. Set a policy that fits legitimate embedding requirements and test the application paths that must remain embeddable.

---

#### DDoS — what is it, what can you actually do?

**分布式拒绝服务 / Distributed Denial of Service** uses traffic or expensive requests to exhaust network, service, or application resources. Mitigation depends on the attack layer and capacity available; no single application control guarantees protection.

Use layered measures such as provider or edge traffic filtering, rate limits and quotas, caching, bounded work, and monitoring. Application code can reject abusive work early and keep expensive endpoints bounded, but large traffic floods need network and provider capacity as well.

---

#### SQL injection — frontend's role?

**SQL 注入 / SQL injection** happens when data is interpreted as part of a SQL command. The frontend can validate inputs for usability, but client-side validation is bypassable and is not a security boundary.

On the server, use parameterized queries so values are supplied separately from SQL syntax. For identifiers or sort directions that cannot be bound as values, choose from a fixed allowlist. An ORM helps only when the query path uses its safe parameterization; raw query construction can still be vulnerable. Authorization is a separate check: a parameterized query does not prove that the caller may access the selected record.

Give each application database account only the tables and operations it needs; query parameterization does not justify connecting as a database administrator.

---

#### How should passwords be stored?

**密码存储 / Password storage** must remain resistant to offline guessing if a database is exposed. Store a salted password hash produced by a password-storage algorithm designed to be expensive to guess, such as Argon2id; use a maintained library and tune its cost for the deployment. A unique random salt is stored with each hash; it is not a secret. A fast general-purpose digest such as SHA-256 alone is not an appropriate password-storage scheme.

An optional pepper is a secret kept separately from the password database; it is defense in depth, not a substitute for a suitable password hash. Pair storage with online attempt throttling and a policy that avoids easily guessed passwords. See the [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html).

**See also:** [HTTP Protocols and WebSockets](#1.%20HTTP%20Protocols%20and%20WebSockets%20/%20HTTP%E5%8D%8F%E8%AE%AE%E4%B8%8EWebSocket) for browser request and transport context, and [Browser Storage and Communication](../../frontend/browser-apis/browser-storage-and-communication.md) for browser storage and messaging security.

Sources: [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#least-privilege), [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [OWASP CSP](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html), [WHATWG Fetch](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials), [RFC 8446 TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html), [RFC 8725 JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html), and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html). Security guidance checked 2026-10-15.
## 6. Algorithms and Complexity / 算法与复杂度分析

### Algorithms and Complexity / 算法与复杂度分析

Use this reference for common algorithmic patterns. The code states its input assumptions; Big-O describes growth with input size, not a promise about constant factors or a particular runtime.

先根据输入约束和不变量选择算法，再用时间与空间复杂度评估输入规模增长带来的成本；复杂度描述增长趋势，不等于实际耗时。

#### Dynamic programming

**动态规划 / Dynamic programming** stores results for overlapping subproblems. Top-down memoization follows the recursive definition; bottom-up iteration computes states in dependency order and can often retain only the state still needed.

##### Fibonacci

For non-negative integer n, naive recursion repeats subproblems and takes O(2^n) time with O(n) call-stack space. The iterative form takes O(n) time and O(1) auxiliary space. These examples use Number; use BigInt when exact results beyond Number's safe-integer range are needed.

~~~javascript
function fibRecursive(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

##### Climbing stairs (frog jump)

Count ordered sequences of allowed positive step sizes that sum to n. The empty sequence is one way to reach step 0. Require distinct positive integer steps; repeated entries would count the same step size more than once.

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (!Array.isArray(steps) || steps.some(step => !Number.isInteger(step) || step <= 0)) {
    throw new TypeError('steps must contain positive integers');
  }
  if (new Set(steps).size !== steps.length) throw new RangeError('steps must be distinct');

  const ways = new Array(n + 1).fill(0);
  ways[0] = 1;
  for (let total = 1; total <= n; total++) {
    for (const step of steps) {
      if (total >= step) ways[total] += ways[total - step];
    }
  }
  return ways[n];
}
~~~

This counts order as meaningful: with steps [1, 2], reaching 3 has three sequences: 1+1+1, 1+2, and 2+1. Time is O(nk), where k is the number of allowed steps; space is O(n).

##### 0/1 Knapsack

Choose each item at most once to maximize value within a weight capacity. Iterate capacities downward so the current item cannot be selected again during the same pass.

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  if (weights.some(weight => !Number.isInteger(weight) || weight < 0)) {
    throw new RangeError('weights must be non-negative integers');
  }

  const best = new Array(capacity + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let remaining = capacity; remaining >= weights[i]; remaining--) {
      best[remaining] = Math.max(best[remaining], best[remaining - weights[i]] + values[i]);
    }
  }
  return best[capacity];
}
~~~

Time is O(nW) and space O(W), for n items and integer capacity W. The zero-filled state means the result may leave capacity unused; it assumes there is no required minimum value or exact-fill constraint.

---

#### Binary search

Binary search locates a matching item in O(log n) time when the input is sorted in ascending order and comparisons are consistent. This version returns any matching index, or -1 for an empty array or a missing value.

~~~javascript
function binarySearch(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] === target) return middle;
    if (values[middle] < target) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

For fixed-width integer languages, computing the midpoint as left + (right - left) / 2 avoids overflow in left + right. JavaScript array indices are far smaller than Number's exact-integer limit, but the difference form states the safer general pattern.

---

#### Two pointers

**双指针 / Two pointers** uses two positions to reduce repeated scans when the input structure provides an ordering or movement invariant. It is not a general replacement for nested loops; the invariant must justify discarding part of the search space.

##### Two Sum on a sorted array

Returns a pair of indices or null when no pair exists. Equal values at different positions are valid.

~~~javascript
function twoSumSorted(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left < right) {
    const sum = values[left] + values[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return null;
}
~~~

##### Move zeros to the end

Moves numeric zeroes in place while keeping the order of non-zero values. It returns the same mutated array.

~~~javascript
function moveZeros(values) {
  let next = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== 0) {
      [values[next], values[i]] = [values[i], values[next]];
      next++;
    }
  }
  return values;
}
~~~

---

#### Sorting

##### Quicksort

This array-building version is easy to inspect, but it is not in-place. With balanced partitions it takes O(n log n) time; an adversarial sequence of pivots can take O(n²) time and O(n) recursive stack space.

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

For application code, prefer the built-in sort with an explicit comparator for numeric data: `values.sort((a, b) => a - b)` mutates the array, while `values.toSorted((a, b) => a - b)` returns a sorted copy where supported. Without a comparator, array elements are compared as strings. ECMAScript requires stable sorting; the engine's specific sorting algorithm is an implementation detail. See [ECMAScript 2020, Array.prototype.sort](https://tc39.es/ecma262/2020/#sec-array.prototype.sort).

---

#### String algorithms

The examples iterate Unicode code points with `Array.from`; that keeps surrogate pairs together. A user-perceived character can contain multiple code points, so grapheme-aware text operations need segmentation and may also need normalization.

##### Palindrome check

~~~javascript
function isPalindrome(value) {
  const characters = Array.from(String(value));
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    if (characters[left] !== characters[right]) return false;
  }
  return true;
}
~~~

##### Longest consecutive character

Returns the first longest run. Empty input returns an empty character and length zero.

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) {
      currentLength++;
    } else {
      if (currentLength > bestLength) {
        bestLength = currentLength;
        bestChar = characters[i - 1];
      }
      currentLength = 1;
    }
  }
  return { char: bestChar, len: bestLength };
}
~~~

##### Number formatting (thousand separators)

For display, use locale-aware formatting and specify a locale when output must be stable across machines. The manual version below accepts only strings containing an optional minus sign and decimal digits; use locale-aware formatting for numeric values and localized output.

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || !/^-?\d+$/.test(text)) throw new TypeError('expected an integer string');
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

##### Switch ASCII letter case

This example changes only the English ASCII letters A-Z and a-z; other code points are preserved.

~~~javascript
function switchAsciiCase(value) {
  return Array.from(value, character => {
    const code = character.codePointAt(0);
    if (code >= 65 && code <= 90) return String.fromCodePoint(code + 32);
    if (code >= 97 && code <= 122) return String.fromCodePoint(code - 32);
    return character;
  }).join('');
}
~~~

---

#### Big-O reference

| Complexity | Typical example | Condition |
|---|---|---|
| O(1) | Array index access | Indexed access, not search |
| O(1) average | Hash-table lookup | Expected under ordinary hash distribution |
| O(log n) | Binary search; balanced BST operation | Sorted input or bounded tree height |
| O(n) | Linear scan | One pass |
| O(n log n) | Merge sort; balanced quicksort | Quicksort can degrade to O(n²) |
| O(n²) | Nested scan; simple quadratic sort | Depends on input size and algorithm |
| O(2^n) | Naive recursive Fibonacci; subset enumeration | Exponential growth |
| O(n!) | Permutation enumeration | Factorial growth |

**See also:** [Core Data Structures](#7.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84) for trees and tries, and [Practical Data Structure Implementations](#8.%20Practical%20Data%20Structure%20Implementations%20/%20%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%AE%9E%E7%8E%B0) for LRU caches, queues, and stacks.
## 7. Core Data Structures / 核心数据结构

### Core Data Structures / 核心数据结构

A tree organizes values through parent-child links. Complexity claims below assume the stated structure and operation; an unbalanced search tree or a search that must find a node by scanning does not get balanced-tree bounds.

数据结构决定数据的组织方式和常见操作的代价；选择时要看实际访问模式以及平衡、前驱链接等表示条件，不能把某种结构下的复杂度推广到所有实现。

#### Tree traversals

For a binary tree, depth-first orders differ in when the current node is visited:

- **In-order / 中序**: left, node, right. This yields ascending values only when the tree satisfies the binary-search-tree ordering rule.
- **Pre-order / 前序**: node, left, right. Useful when serializing a tree with enough structure to recover its shape.
- **Post-order / 后序**: left, right, node. Useful when computing or releasing children before their parent.

##### Kth smallest in a BST

This iterative in-order traversal uses O(h) stack space for tree height h. It assumes node values are non-null numbers and the tree obeys the BST ordering rule. It returns null when k is invalid or the tree has fewer than k nodes.

~~~javascript
function kthSmallest(root, k) {
  if (!Number.isInteger(k) || k <= 0) return null;
  const stack = [];
  let node = root;

  while (node || stack.length) {
    while (node) {
      stack.push(node);
      node = node.left;
    }
    node = stack.pop();
    if (--k === 0) return node.val;
    node = node.right;
  }
  return null;
}
~~~

---

#### Trees and operation costs

| Structure | Indexed access / search | Insert or delete |
|---|---|---|
| Array | Index access O(1); value search O(n) | Middle insert/delete O(n) because elements move |
| Linked list | Finding by value or index O(n) | O(1) insertion at a known link; deletion needs the predecessor link (singly linked) or target node (doubly linked), otherwise O(n) worst case |
| Height-balanced BST | Search O(log n) | O(log n) |
| Unbalanced BST | Worst-case search O(n) | Worst-case O(n) |

A balanced search tree gives logarithmic operations by keeping height logarithmic. If insertions produce a chain, those operations degrade to linear time. Array access remains fast by index, while inserting into the middle shifts later elements.

---

#### Self-balancing trees

##### Red-Black Tree

A red-black tree is a binary search tree with coloring invariants that bound its height. Red nodes have black children, and every path from a node to a descendant leaf has the same black height; implementations also treat the root and leaf sentinels as black. These rules give O(log n) worst-case search, insertion, and deletion.

Java's `TreeMap` explicitly documents a red-black-tree implementation. C++ `std::map` specifies ordered associative behavior and logarithmic lookup, insertion, and key-removal bounds, but its standard does not prescribe a tree shape. Check the language and library documentation before inferring a product's internal structure: [Java `TreeMap`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) and [C++ associative containers](https://eel.is/c++draft/associative.reqmts).

##### B-Tree and B+ Tree

B-trees are multi-way search trees designed to reduce storage-page reads by keeping several keys in each node.

- In a B-tree, records or record references may be stored in internal nodes as well as leaves.
- In a B+ tree, internal nodes guide the search and records are stored at leaves; leaf links commonly support ordered range scans.

These are family descriptions, not a guarantee that every database index uses the same variant or layout. Check the database's manual for its index type and behavior.

---

#### Trie (prefix tree)

A trie shares prefixes between keys. Lookup takes O(m) steps for a key of length m when each next edge can be selected in constant expected time; the cost depends on the node's child representation. Tries can use substantial memory when keys share few prefixes.

Use one when prefix traversal or prefix queries are central, such as autocomplete or routing tables; a hash map may be simpler for exact-key lookup.

---

#### DOM tree traversal

A DOM tree is a hierarchy of Node objects. Pass an explicit visit callback and a node or null root. Snapshot each node's children before walking so the traversal has a clear view if callbacks mutate the DOM.

##### DFS — depth-first search

~~~javascript
function dfs(root, visit) {
  if (!root) return;
  visit(root);
  for (const child of Array.from(root.childNodes)) {
    dfs(child, visit);
  }
}

function dfsIterative(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    const children = Array.from(node.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
~~~

##### BFS — breadth-first search

~~~javascript
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    visit(node);
    for (const child of Array.from(node.childNodes)) {
      queue.push(child);
    }
  }
}
~~~

A queue implemented with repeated `Array.prototype.shift` can move all remaining elements on each removal and make a traversal quadratic. Advancing a head index keeps this traversal O(n) in the number of visited nodes, with O(n) queue space.

DFS is useful when depth-first order or a path is needed. BFS is useful for level order and shortest paths in an unweighted graph; a DOM tree has one unique path from the root to each node.

---

#### Array ↔ Tree conversion

Flat rows with parent identifiers can be transformed into a hierarchy for a tree UI or converted back for an API or database representation. This example expects unique IDs, one root whose parent ID is 0, and each other row to reference an existing parent.

##### Array to tree

~~~javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');

  const nodes = new Map();
  for (const row of rows) {
    if (!row || nodes.has(row.id)) throw new RangeError('rows must have unique IDs');
    nodes.set(row.id, { ...row, children: [] });
  }

  const roots = [];
  for (const row of rows) {
    const node = nodes.get(row.id);
    if (row.parentId === 0) {
      roots.push(node);
      continue;
    }
    const parent = nodes.get(row.parentId);
    if (!parent) throw new RangeError('parent ID does not exist');
    parent.children.push(node);
  }

  if (roots.length !== 1) throw new RangeError('expected exactly one root');
  const root = roots[0];

  const seen = new Set();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    if (seen.has(node)) throw new RangeError('rows contain a cycle');
    seen.add(node);
    for (const child of node.children) stack.push(child);
  }
  if (seen.size !== nodes.size) throw new RangeError('rows contain a disconnected cycle');
  return root;
}
~~~

The two passes take O(n) expected time and O(n) space with a map. Reserve ID 0 for the root marker, or change the marker to match the data format.

##### Tree to array

~~~javascript
function treeToArray(root) {
  if (!root) return [];
  const rows = [];
  const stack = [{ node: root, parentId: 0 }];
  while (stack.length) {
    const { node, parentId } = stack.pop();
    rows.push({ id: node.id, parentId, name: node.name });
    const children = node.children ?? [];
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push({ node: children[i], parentId: node.id });
    }
  }
  return rows;
}
~~~

This conversion expects an acyclic tree with a single root. Preserve application-specific fields deliberately; this example emits only `id`, `parentId`, and `name`.

**See also:** [Algorithms and Complexity](#6.%20Algorithms%20and%20Complexity%20/%20%E7%AE%97%E6%B3%95%E4%B8%8E%E5%A4%8D%E6%9D%82%E5%BA%A6%E5%88%86%E6%9E%90) for searches and dynamic programming, and [Practical Data Structure Implementations](#8.%20Practical%20Data%20Structure%20Implementations%20/%20%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%AE%9E%E7%8E%B0) for LRU caches, queues, and stacks.
## 8. Practical Data Structure Implementations / 常用数据结构实现

### Practical Data Structure Implementations / 常用数据结构实现

These examples make the empty and capacity cases explicit. Built-in collections are usually the simplest production choice; implement the underlying links when the data structure itself is what you need to understand.

选用内建集合还是手写结构取决于需求；实现需要明确容量、空状态与错误行为，并用存在性检查保留 `undefined` 等有效数据。

#### LRU Cache

**最近最少使用缓存 / Least Recently Used cache** evicts the least recently accessed entry when full.

##### Using `Map`

`Map` preserves insertion order. Deleting and reinserting a hit moves it to the newest position. This API supports arbitrary keys and values; use `has` to distinguish a stored `undefined` from a missing key. A zero-capacity cache remains empty.

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.cache = new Map();
  }

  has(key) {
    return this.cache.has(key);
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

Map operations are commonly treated as expected constant-time in application analysis, but the ECMAScript specification requires average access to be sublinear rather than promising a precise O(1) bound. This version is concise and avoids maintaining a second ordering structure.

##### Doubly linked list plus map

A linked list makes moving an existing entry to the front and evicting the tail a pointer update. The map locates each node. Both structures are needed to keep the operations efficient; using an ordinary object for arbitrary cache keys can collide with inherited property names.

~~~javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  has(key) {
    return this.nodes.has(key);
  }

  get(key) {
    const node = this.nodes.get(key);
    if (!node) return undefined;
    this._remove(node);
    this._addToFront(node);
    return node.value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    const existing = this.nodes.get(key);
    if (existing) {
      existing.value = value;
      this._remove(existing);
      this._addToFront(existing);
      return;
    }

    if (this.nodes.size === this.capacity) {
      const oldest = this.tail.prev;
      this._remove(oldest);
      this.nodes.delete(oldest.key);
    }
    const node = new ListNode(key, value);
    this.nodes.set(key, node);
    this._addToFront(node);
  }

  _addToFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
~~~

With a map that provides expected constant-time lookup, the linked-list version has expected O(1) get and put operations. Use the simpler map-based version when the linked-list mechanics are not part of the requirement.

---

#### Queue (FIFO)

**队列 / Queue** processes values in first-in, first-out order. This linked-list version throws on an empty read so every value, including `null` and `undefined`, remains distinguishable from the empty state.

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  get isEmpty() {
    return this.length === 0;
  }

  enqueue(value) {
    const node = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return value;
  }

  peek() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    return this.head.value;
  }
}
~~~

Enqueue, dequeue, and peek take O(1) time. Array `shift` removes the first element but may move the remaining indexed elements, so a linked queue or a head index is preferable for a queue that grows large. Breadth-first traversal with a head index appears in [Core Data Structures](#7.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84).

---

#### Stack (LIFO)

**栈 / Stack** processes values in last-in, first-out order. An array provides a compact stack; this version also throws on empty `pop` or `peek` so stored `undefined` is not confused with an empty stack.

~~~javascript
class Stack {
  constructor() {
    this.items = [];
  }

  get isEmpty() {
    return this.items.length === 0;
  }

  push(value) {
    this.items.push(value);
  }

  pop() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items.pop();
  }

  peek() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items[this.items.length - 1];
  }
}
~~~

Array `push` and `pop` are the natural stack operations. Their exact growth costs are runtime implementation details; a dynamic array may occasionally resize.

---

#### Linked structure in React Fiber

React represents its work tree with Fiber nodes linked through fields such as `child`, `sibling`, and `return`. The nodes still form a tree; sibling pointers encode the ordered children. This structure lets the reconciler keep work units and progress between scheduling steps.

**Concurrent rendering is conditional.** React can pause or restart render work for updates using concurrent features such as transitions. An update rendered without such features can remain synchronous. React applies DOM mutations during commit after rendering work is ready, so do not describe every render or commit as freely interruptible. Fiber is an implementation detail; use React's public APIs rather than depending on its internal node layout.

**See also:** [Algorithms and Complexity](#6.%20Algorithms%20and%20Complexity%20/%20%E7%AE%97%E6%B3%95%E4%B8%8E%E5%A4%8D%E6%9D%82%E5%BA%A6%E5%88%86%E6%9E%90) for complexity patterns, [Core Data Structures](#7.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84) for traversals, and [Virtual DOM and Framework Selection](../../frontend/frameworks/virtual-dom-and-framework-selection.md) for reconciliation context.

Sources: [ECMAScript 2020 Map objects](https://tc39.es/ecma262/2020/#sec-map-objects), [React 18: What is Concurrent React?](https://react.dev/blog/2022/03/29/react-v18), and the [React reconciler Fiber types](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js).
## 9. Node.js Fundamentals / Node.js基础

### Node.js Fundamentals / Node.js基础

Node.js runs JavaScript outside a browser and provides server-side APIs. Its event-loop model is efficient for many I/O workloads, but a long synchronous callback still blocks JavaScript work on that event-loop thread.

Node 的异步 I/O、事件循环、工作线程和子进程解决不同问题：I/O 等待通常使用异步 API，CPU 并行、进程隔离或共享状态则要按线程与进程边界选择，并处理通信和关闭。

#### What's the difference between a process and a thread?

**进程 / Process** is an operating-system execution boundary with its own virtual address space. **线程 / Thread** is an execution path inside a process; threads can share process memory, so shared mutable data needs coordination.

Node has a JavaScript event-loop thread for each isolate, not one JavaScript thread for the whole machine. A worker thread runs JavaScript in another isolate in the same process. It can exchange messages, transfer an ArrayBuffer, or share a SharedArrayBuffer; shared memory requires explicit synchronization such as Atomics. A child process has a separate process address space and communicates through IPC or other operating-system channels.

Node also uses background mechanisms for asynchronous work: network I/O is commonly driven by the operating system, while selected APIs such as filesystem operations, cryptography, compression, and some name-resolution work use libuv's worker pool. Their JavaScript callbacks run on the event-loop thread. CPU-heavy JavaScript on that thread delays other callbacks.

For the reusable process/thread model of address spaces, shared resources, concurrency, I/O, and cancellation, see [Processes, Threads, and Concurrency / 进程、线程与并发](#2.%20Processes,%20Threads,%20and%20Concurrency%20/%20%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E4%B8%8E%E5%B9%B6%E5%8F%91); this note applies it to Node's event loop and worker choices.

---

#### How do you use multiple CPU cores in Node.js?

Choose based on the work and isolation needed:

- **Worker threads / 工作线程** run CPU-intensive JavaScript in parallel and can communicate by message or shared memory. Use a bounded worker pool for repeated tasks rather than creating one thread per small job.
- **Child processes / 子进程** run in separate process memory and provide stronger isolation; IPC messages are a boundary to account for.
- **Cluster / 多进程服务** starts multiple Node processes that can accept connections on the same server port. It is one deployment option for multi-core servers, not a guarantee of linear throughput scaling or balanced work.

Built-in asynchronous I/O is usually a better choice for I/O-bound work than worker threads. For process or worker choices and shared-state trade-offs, see the linked Node.js API documentation.

An external process manager is optional. PM2 is one choice for starting and observing clustered workers:

~~~bash
pm2 start app.js --name api -i max
pm2 list
pm2 monit
pm2 reload api
~~~

PM2 may fall back from a cluster reload to a restart if it cannot complete it. The application must handle shutdown and drain or close its own work; availability during reload is not guaranteed.

##### Child process example

This compact CommonJS example runs the same file in a child process and sends one task over the fork IPC channel. It is illustrative; production code also needs workload limits, error handling, and shutdown policy.

~~~javascript
const { fork } = require('node:child_process');

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    let a = 0;
    let b = 1;
    for (let i = 0; i < n; i++) [a, b] = [b, a + b];
    process.send({ result: a });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.on('message', message => {
    console.log(message.result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

##### Cluster example

Each worker is a separate process. Restarting workers, health checks, graceful shutdown, and shared session state are application or process-manager responsibilities; the cluster module does not make in-memory state shared.

~~~javascript
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

if (cluster.isPrimary) {
  for (let i = 0; i < availableParallelism(); i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end('Hello');
  }).listen(8000);
}
~~~

Workers have separate heaps. If a session, cache, or connection map must be shared, choose a deliberate external store, routing strategy, or message-broadcast mechanism. A Redis store is one option, not a universal requirement.

---

#### How do CommonJS and ES modules affect nextTick ordering?

Node's scheduling details depend on where work is queued. At top level, `process.nextTick` runs before Promise callbacks in this CommonJS example:

~~~javascript
// Save as example.cjs
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));
~~~

The same calls have the opposite order at the top level of an ES module:

~~~javascript
// Save as example.mjs
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
nextTick(() => console.log('nextTick'));
~~~

This difference is about the module's execution context; it is not a universal ordering rule for every callback or event-loop phase. Use the current [Node.js process documentation](https://nodejs.org/docs/latest-v24.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) when an ordering dependency matters.

---

#### What is serverless or function-as-a-service?

**无服务器计算 / Serverless** means the provider manages the underlying execution infrastructure through a function or managed runtime interface. Servers still exist; the provider controls how execution environments are created, reused, and scaled.

Timeouts, concurrency limits, billing, cold-start latency, and state-reuse behavior depend on the provider, product, runtime, region, and configuration. Do not treat in-memory state as durable or assume an execution environment is discarded after every invocation. For example, AWS Lambda documents that environments can be reused while advising applications to treat state as temporary and persist durable changes externally.

It can suit event-triggered handlers or variable workloads when the provider's limits and cost model fit. Long-running work, persistent connections, predictable latency, and vendor-specific integrations require a comparison against other deployment models.

**See also:** [Event Loop](../../frontend/runtime/event-loop.md) for browser and Node scheduling context, and [Software Design Principles](#11.%20Software%20Design%20Principles%20/%20%E8%BD%AF%E4%BB%B6%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99) for choosing boundaries around runtime-specific infrastructure.

Sources: [Node.js v24 worker threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html), [child processes](https://nodejs.org/docs/latest-v24.x/api/child_process.html), [cluster](https://nodejs.org/docs/latest-v24.x/api/cluster.html), [process scheduling](https://nodejs.org/docs/latest-v24.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html), [crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html), [zlib](https://nodejs.org/docs/latest-v24.x/api/zlib.html), and [DNS](https://nodejs.org/docs/latest-v24.x/api/dns.html) documentation; [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) and [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/); plus [AWS Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) and [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html). PM2 and AWS references checked 2026-10-15; provider limits change over time.
## 10. Python Fundamentals / Python基础

### Python Fundamentals / Python基础

**Core model / 核心模型：** Python names are bindings to objects. A collection may be changed in place or a name may be rebound to another object; those are different operations. Function defaults are evaluated when the function is defined, iterators produce values as they are requested, and context managers define cleanup around a block. Type hints describe intent to static tools but do not validate runtime input. A virtual environment separates a project's installed packages from other environments. / Python 名称绑定到对象。集合可以被原地修改，名称也可以重新绑定到另一个对象，这是两种不同操作。函数默认值在函数定义时求值，迭代器按需产生值，上下文管理器则为代码块定义资源清理。类型提示表达意图并帮助静态工具检查，但不会在运行时验证输入。虚拟环境将项目安装的包与其他环境隔离。

**Key terms / 关键术语：** object / 对象；name binding / 名称绑定；mutable / 可变；immutable / 不可变；alias / 别名；shallow copy / 浅拷贝；default argument / 默认参数；iterable / 可迭代对象；iterator / 迭代器；generator / 生成器；exception / 异常；context manager / 上下文管理器；type hint / 类型提示；virtual environment / 虚拟环境。

#### Collections and object references / 集合与对象引用

Lists and dictionaries are mutable: an operation such as `append` or item assignment changes that object. Strings and tuples are immutable. A tuple cannot have its slots replaced, although it can still contain a mutable object whose value changes. Sets keep unique elements and do not provide sequence indexing; dictionaries map keys to values and preserve insertion order in Python 3.7 and later.

A name does not contain a separate copy of the value. Assignment binds the name to an object, so two names can refer to the same mutable object. Mutating through either name is visible through the other. Rebinding one name changes only that name's binding. A shallow copy creates a new outer container while keeping references to nested objects; use a deeper copy or explicit reconstruction only when the nested values also need independent ownership.

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])  # ['new', 'priority']

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"  # a different outer dictionary
outer_copy["tags"].append("shared")  # the nested list is still shared
print(event["tags"])  # ['new', 'priority', 'shared']

alias = {"id": "evt-2", "tags": []}  # only alias is rebound
print(event["id"])  # evt-1
~~~

#### Calls, argument binding, and defaults / 调用、参数绑定与默认值

At a call, Python binds supplied argument values to parameters by position or keyword. A parameter receives a reference to the supplied object; the call does not copy a mutable argument. Mutating that object inside a function can therefore be observed by the caller, while assigning a new object to the local parameter only rebinds that local name.

Default expressions are evaluated once when Python executes the `def` statement. If the default is a list or dictionary and the function mutates it, later calls reuse that same object. Use `None` when it means “no value supplied,” then create per-call state inside the function. If `None` itself is a meaningful input, choose a separate sentinel.

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))   # ['first']
print(unsafe_add("second"))  # ['first', 'second'] — same default list

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))   # ['first']
print(add("second"))  # ['second']
~~~

#### Iteration and generators / 迭代与生成器

An **iterable** can supply an iterator. An **iterator** returns its next value on request and signals completion with `StopIteration`; a `for` loop handles that protocol. A generator function uses `yield` to produce an iterator whose local state resumes at the next request. This lets a pipeline process one item at a time instead of first building a complete result list. The work, and any exception raised by that work, happens as the consumer advances the generator. A generator is usually one-pass; materializing it with `list(...)` consumes it and stores all produced values.

~~~python
from collections.abc import Iterable, Iterator

def ready_rows(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

Streaming reduces intermediate storage and can begin output early, but it does not make a whole operation atomic. If a later row is invalid, earlier rows may already have been emitted or acted on. Validate or stage first when the operation requires all-or-nothing effects.

#### Exceptions and context managers / 异常与上下文管理器

Exceptions report that an operation could not complete normally. Catch one where the program can recover, translate it into a useful boundary error, or add context and re-raise it with `raise ... from error`. Avoid swallowing an exception when the caller still needs to know that work failed.

A context manager pairs setup and cleanup around a block. Once `__enter__` completes successfully, `__exit__` is called when the block ends, including when an exception leaves the block. A context manager may intentionally suppress an exception; ordinary file context managers close the file and allow the original error to continue. This is why file and temporary-directory lifetimes should be explicit rather than left to garbage collection.

#### What type hints do and do not do / 类型提示的作用与边界

Annotations give readers and static analyzers a shared description of expected values and returns. A type checker can report a mismatch before execution, and an editor can use the information for navigation and completion. Python does not automatically reject a value because it conflicts with an annotation; data read from a file, database, or network still needs parsing and validation at that boundary. Runtime validation requires an explicit check or a library designed to perform it.

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())  # Python returns the string; a type checker can flag it
~~~

#### A small file-processing example / 小型文件处理示例

Save this as `python-fundamentals-example.py`. It filters synthetic CSV rows lazily, copies each selected row before adding a tag, and uses nested context managers to close the file and remove the temporary directory even if parsing raises an exception.

~~~python
import csv
from collections.abc import Iterable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]


def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for line_number, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            status = row["status"]
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV row {line_number}: status and integer count are required"
            ) from error

        if status == "ready" and count > 0:
            yield row


def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()  # a shallow copy is enough because values are strings
    enriched["tag"] = tag
    return enriched


CSV_TEXT = """id,status,count
evt-1,ready,3
evt-2,queued,1
evt-3,ready,nope
"""


def main() -> None:
    try:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text(CSV_TEXT, encoding="utf-8")

            with path.open(encoding="utf-8", newline="") as source:
                for row in ready_rows(csv.DictReader(source)):
                    print(add_tag(row))
    except ValueError as error:
        print(f"Rejected input: {error}")


if __name__ == "__main__":
    main()
~~~

Expected output:

~~~text
{'id': 'evt-1', 'status': 'ready', 'count': '3', 'tag': 'reviewed'}
Rejected input: CSV row 4: status and integer count are required
~~~

The first row is yielded before the generator reaches the malformed fourth CSV line. The example catches the parsing error outside both `with` blocks, so the file and temporary directory still close during exception unwinding. A real application that writes results to a database or calls a remote service must decide whether partial progress is acceptable and use a transaction or staging boundary when it is not.

#### Language behavior, implementations, and versions / 语言语义、实现与版本

The examples use Python 3.11 syntax and the language behavior documented for Python 3.11. Names, mutability, default evaluation, iteration, and `with` cleanup are language/runtime contracts; they do not depend on CPython's internal object layout. Other details can be implementation-specific or change between Python versions. For example, dictionary insertion order is a language guarantee from Python 3.7; CPython 3.6 preserved it as an implementation detail. In CPython, `id(obj)` currently represents an object's memory address, but code should not treat an identity value as a durable identifier. Check the target interpreter and minimum supported version before relying on newer syntax or runtime behavior.

#### Isolated environment and run command / 隔离环境与运行命令

A virtual environment gives a project its own package installation area; it does not install or pin the Python interpreter itself. Select the intended interpreter when creating the environment, and use that environment's Python to invoke `pip` so package installation and execution target the same environment. Declare third-party requirements in the project's packaging or dependency files. A dependency-free example needs no installation step.

On POSIX, from the directory containing the saved example, create an environment and run it with:

~~~sh
python3.11 -m venv .venv && .venv/bin/python python-fundamentals-example.py
~~~

For a project with a `requirements.txt`, install its declared packages with `.venv/bin/python -m pip install -r requirements.txt` before running the script. A virtual environment isolates packages, while repeatability still depends on selecting a compatible Python version and recording the project's dependency versions and platform requirements.

**Verified run / 运行验证：** The file-processing example ran with CPython 3.11.13 and printed the expected output above. This verifies the example on that interpreter; it is not a claim that every Python implementation or platform has identical implementation details.

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#4.%20API%20Reliability%20and%20Asynchronous%20Delivery%20/%20API%E5%8F%AF%E9%9D%A0%E6%80%A7%E4%B8%8E%E5%BC%82%E6%AD%A5%E4%BA%A4%E4%BB%98) explains timeout, cancellation, retries, and bounded work at network and queue boundaries; those correctness concerns also apply to Python services. Python-specific coroutine and framework behavior belongs in a separate async/API note.

**Sources / 来源：** Python 3.11 [Tutorial](https://docs.python.org/3.11/tutorial/) and [Language Reference](https://docs.python.org/3.11/reference/), including [objects and types](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types), [function definitions](https://docs.python.org/3.11/reference/compound_stmts.html#function-definitions), [iterators and generators](https://docs.python.org/3.11/reference/datamodel.html#generator-functions), and [`with` statements](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement); [`typing`](https://docs.python.org/3.11/library/typing.html); and the Python Packaging User Guide's [installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/) and [managing application dependencies](https://packaging.python.org/en/latest/tutorials/managing-dependencies/) tutorials. Checked 2026-10-15.

#### Representative answers / 代表性回答

**How do mutability, argument binding, and defaults affect a function call? / 可变性、参数绑定与默认值如何影响函数调用？** Names bind to objects, so a caller and a parameter can refer to the same mutable object. An in-place mutation is visible through both references; rebinding the local parameter does not rebind the caller's name. Python evaluates a default expression when the function is defined, so a mutable default is shared across calls. Use `None` and allocate a fresh list or dictionary inside when each call needs independent state.

名称绑定到对象，因此调用方和形参可能引用同一可变对象。原地修改会通过两个引用都可见；在函数内部重新绑定形参不会改变调用方的名称绑定。Python 在函数定义时求值默认表达式，因此可变默认值会在多次调用间共享。若每次调用需要独立状态，使用 `None` 并在函数内部创建新列表或字典。

**How do iterators, generators, and context managers control work and resources? / 迭代器、生成器与上下文管理器如何控制工作和资源？** An iterator produces one value per request, and a generator packages that pull-based behavior with `yield` and saved execution state. That can avoid building an entire intermediate collection, but later errors may occur after earlier values have already been consumed. A context manager runs its exit behavior when a block ends, including during exception unwinding, so files and other resources have a clear cleanup boundary.

迭代器按请求产出一个值，生成器通过 `yield` 和保存的执行状态封装这种拉取式行为。这样可以避免构建整个中间集合，但后续错误可能在较早的值已经被消费后才发生。代码块退出时（包括异常展开期间），上下文管理器都会运行退出逻辑，因此文件等资源有明确的清理边界。

**What do Python type hints guarantee at runtime? / Python 类型提示在运行时保证什么？** By themselves, they guarantee nothing about the values passed or returned. They communicate expected shapes to humans and static tools. Programs still parse and validate untrusted or external data where it enters the application, and use explicit runtime checks when runtime enforcement is required.

类型提示本身不会在运行时保证输入值或返回值的类型。它们向读者和静态工具传达预期的数据形状。程序仍需在外部数据进入应用时解析与校验；需要运行时强制时，应添加显式检查或使用专门的校验库。
## 11. Software Design Principles / 软件设计原则

### Software Design Principles / 软件设计原则

Design principles are lenses for reasoning about change, not laws that guarantee maintainability. **设计原则帮助讨论变化与依赖的成本，不是保证正确架构的公式。** Apply a principle when it reduces a concrete source of coupling without creating unnecessary abstraction.

#### What are the SOLID principles, and what does each mean?

**SOLID / 面向对象设计原则** is a mnemonic for five related guidelines:

- **S — Single Responsibility Principle / 单一职责原则**: keep a module cohesive around one responsibility or axis of change.
- **O — Open/Closed Principle / 开闭原则**: make a stable part of the design extensible at expected variation points, rather than editing that core for every new case.
- **L — Liskov Substitution Principle / 里氏替换原则**: a subtype must preserve the behavioral expectations clients rely on from its base type.
- **I — Interface Segregation Principle / 接口隔离原则**: clients should depend only on the operations they need.
- **D — Dependency Inversion Principle / 依赖倒置原则**: high-level policy should not depend directly on low-level details; both should depend on abstractions where that boundary pays for itself.

These guidelines can help isolate changes, but applying all of them mechanically can produce needless interfaces and indirection.

##### Single Responsibility Principle (SRP)

A module should group behavior that changes for the same reason. This is not a rule that every method or data field needs a separate class.

~~~javascript
class UserRepository {
  async findById(id) { /* persistence details */ }
}

class UserPage {
  render(user) { /* presentation */ }
}
~~~

Separating persistence from presentation can help when those concerns change independently. A small component that performs a request and renders a result may still be cohesive if the application has no independent reason to change those pieces.

##### Open/Closed Principle (OCP)

An extension point is useful when a kind of variation is known and likely; it is not practical to close a system against every future change.

~~~javascript
class ShippingCalculator {
  constructor(strategy) {
    this.strategy = strategy;
  }

  calculate(pkg) {
    return this.strategy.calculate(pkg);
  }
}

class ExpressShipping {
  calculate(pkg) { return pkg.weight * 10; }
}

class StandardShipping {
  calculate(pkg) { return pkg.weight * 5; }
}
~~~

A new shipping policy can be supplied without changing the calculator, while the selection and shared contract still need maintenance. See [Strategy in practice](#12.%20Design%20Patterns%20in%20Practice%20/%20%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E5%AE%9E%E8%B7%B5).

##### Liskov Substitution Principle (LSP)

A subtype should preserve the behavioral contract clients expect. For example, if a base type promises that every value can fly, a penguin subtype that throws from `fly` breaks that contract. A narrower abstraction such as `Bird` for shared bird behavior and `FlyingBird` for birds that can fly may model the domain more accurately.

##### Interface Segregation Principle (ISP)

Clients should not be forced to depend on operations they never use. In TypeScript, this can mean separating unrelated capabilities into small interfaces and composing them where needed; there is no universal field-count threshold.

##### Dependency Inversion Principle (DIP)

High-level policy and low-level details depend on an abstraction when that boundary reduces coupling. Constructor injection is one way to supply an implementation; **dependency injection is a technique, not the definition of DIP**.

~~~javascript
class NotificationService {
  constructor(sender) {
    this.sender = sender;
  }

  notify(message) {
    this.sender.send(message);
  }
}

class EmailSender {
  send(message) { /* send email */ }
}

class SmsSender {
  send(message) { /* send SMS */ }
}

const notifications = new NotificationService(new EmailSender());
~~~

The service can use another implementation or a test double through the same contract. Add an abstraction when the variation or test boundary is real.

---

#### What are DRY, KISS, and YAGNI?

**DRY, KISS, and YAGNI / 不重复、保持简单、暂不实现未需功能** are practical heuristics. They help manage complexity but should not be interpreted as absolute prohibitions.

##### DRY (Don't Repeat Yourself)

Avoid duplicating the same rule or knowledge in places that must stay synchronized. Similar-looking code can represent different concepts, though; extracting it into one abstraction may couple changes that should remain independent.

##### KISS (Keep It Simple)

Prefer the simplest design that satisfies current requirements. A simple implementation is easier to explain and change; complexity should have a concrete payoff.

##### YAGNI (You Aren't Gonna Need It)

Do not build speculative features before a need is established. Keep the option to add an extension point when a real use case appears, and avoid confusing “not yet needed” with “never needed.”

---

#### What are common frontend architecture patterns?

These are common design shapes, not a required architecture. Choose based on product boundaries, change frequency, and team ownership.

##### Component-based architecture

A UI can be composed from reusable components with explicit inputs and outputs. State and side effects may live in a component, a hook, or a separate service depending on its lifecycle and reuse needs; they are not inherently owned by every component.

##### Unidirectional data flow

In the classic Flux model, actions pass through a dispatcher to stores, which notify views. Other state libraries use different contracts. The useful goal is to make state changes and their causes traceable; the particular library does not guarantee that by itself.

See [Advanced React](../../frontend/frameworks/advanced-react.md) for React-specific state and component patterns.

##### Micro-frontends

Micro-frontends divide a frontend into parts that can have separate ownership or release paths. Integration can use build-time composition, runtime module loading, iframes, or web components, each with different isolation and deployment properties.

Reach for this when independent teams or release schedules are a concrete requirement and the organization can support the shared navigation, styling, accessibility, observability, and runtime boundaries. For a smaller application, a modular single frontend usually has less coordination and deployment overhead.

**See also:** [Design Patterns in Practice](#12.%20Design%20Patterns%20in%20Practice%20/%20%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E5%AE%9E%E8%B7%B5) for reusable patterns that can support these principles.

Sources: [Robert C. Martin, The Open-Closed Principle](https://objectmentor.com/resources/articles/ocp.pdf), [Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf), and [Liskov and Wing, A Behavioral Notion of Subtyping](https://doi.org/10.1145/197320.197383).
## 12. Design Patterns in Practice / 设计模式实践

### Design Patterns in Practice / 设计模式实践

A design pattern names a recurring design choice and its trade-offs. **设计模式是可复用的设计思路，不是必须套用的模板。** Choose one when it clarifies a real variation or dependency; extra indirection also has a cost.

#### When do you use the Factory pattern?

**工厂 / Factory** centralizes object creation when construction rules or the concrete type should not be repeated at call sites. A simple factory function is useful in JavaScript, but it is not automatically the GoF Factory Method or Abstract Factory pattern.

~~~javascript
function createButton(type) {
  if (type === 'primary') return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
~~~

Use this when the creation decision belongs in one place or construction has meaningful setup. If construction is already a single uncomplicated expression, a factory can add little value.

---

#### When do you use the Singleton pattern?

**单例 / Singleton** constrains access to one instance within a chosen scope. A class-level static instance, for example, is one per loaded class in a JavaScript realm; it is not automatically one instance across workers, processes, duplicated module copies, or machines.

~~~javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) Store.instance = new Store();
    return Store.instance;
  }
}
~~~

Repeated calls to `getInstance()` share one instance through that accessor; because `Store` has a public constructor, `new Store()` can still create additional instances.

A shared cache, event bus, or connection pool may need one instance per process or module. Consider whether explicit dependency injection or a scoped shared instance is easier to test and reason about. A singleton's global access can hide dependencies and couple tests.

---

#### When do you use the Strategy pattern?

**策略 / Strategy** puts interchangeable behavior behind a common contract. It is useful when callers must choose among algorithms or policies; a small conditional is often clearer when there is only one simple branch.

~~~javascript
const strategies = new Map([
  ['express', pkg => pkg.weight * 10],
  ['standard', pkg => pkg.weight * 5],
  ['overnight', pkg => pkg.weight * 20],
]);

function calculateShipping(name, pkg) {
  const strategy = strategies.get(name);
  if (!strategy) throw new RangeError('unknown shipping strategy');
  return strategy(pkg);
}
~~~

Adding a strategy can avoid changing the dispatcher, but the strategy contract and selection rules still need to be maintained. This can support the Open/Closed Principle when the variation is real; it does not make a design closed to every future change. See [Software Design Principles](#11.%20Software%20Design%20Principles%20/%20%E8%BD%AF%E4%BB%B6%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99).

---

#### What's the difference between Observer and Publish-Subscribe?

**观察者 / Observer** and **发布订阅 / Publish-Subscribe** both route notifications. In the common distinction, an observer subject knows its observers and notifies them directly; a publish-subscribe broker routes messages by topic, so publishers and subscribers need not know each other. Real libraries can combine these arrangements, so use the concrete API's contract rather than relying on the label.

##### Observer

~~~javascript
class Subject {
  constructor() {
    this.observers = new Set();
  }

  subscribe(observer) {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  notify(data) {
    for (const observer of this.observers) observer.update(data);
  }
}
~~~

The subject owns the subscriptions. Returning an unsubscribe function makes the lifetime of a listener explicit.

##### Publish-Subscribe

~~~javascript
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(topic, listener) {
    const subscribers = this.listeners.get(topic) ?? new Set();
    subscribers.add(listener);
    this.listeners.set(topic, subscribers);
    return () => subscribers.delete(listener);
  }

  emit(topic, data) {
    for (const listener of this.listeners.get(topic) ?? []) listener(data);
  }
}

const eventBus = new EventBus();
eventBus.on('user:login', user => { /* update the UI with user data */ });
eventBus.emit('user:login', { name: 'Alice' });
~~~

A broker can reduce direct coupling, but distributed or global event buses can make the flow harder to trace. DOM `EventTarget` is observer-like: listeners register on a target that dispatches events.

See [DOM Manipulation and Events](../../frontend/browser-apis/dom-manipulation-and-events.md) for browser event APIs.

---

#### How would you design the data model for a low-code editor?

A page builder can model a document as a component tree, with each node carrying an ID, type, properties, style, and children. The editor can derive its canvas and side panels from that model, then serialize it for persistence.

~~~javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
~~~

Keep document order and visual stacking as explicit concepts. Child order can be one input to rendering, but CSS stacking contexts mean it is not universally equivalent to the final z-order; each stacking context is painted as a unit within its parent context ([CSS 2.2 visual formatting model](https://www.w3.org/TR/CSS22/zindex.html)).

- **Component registry / 组件注册表**: map a validated component type to its renderer and schema.
- **Layer order / 图层顺序**: define how siblings are ordered and translate that order into the chosen rendering model.
- **Undo and redo / 撤销与重做**: store inverse commands or immutable document snapshots; choose based on history size and operation complexity.
- **Collaboration / 协作**: a WebSocket transports updates, but does not resolve concurrent edits. A server-authoritative order, locks, operational transformation, or a CRDT may fit different conflict and offline requirements.

---

#### How does Role-Based Access Control (RBAC) work?

**基于角色的访问控制 / Role-Based Access Control** associates permissions with roles and assigns users to roles. It is one authorization model; it does not determine whether a particular user may access every object of a type.

A relational model commonly includes:

- **User / 用户**: identity and credential reference.
- **Role / 角色**: named job or application role.
- **Permission / 权限**: action on a resource or capability.
- **UserRole / 用户角色**: many-to-many user-to-role assignment.
- **RolePermission / 角色权限**: many-to-many role-to-permission assignment.

A request is authenticated first, then the server checks whether the resulting subject may perform the requested action on the requested object. Check every protected operation and resource; hiding a button or trusting a client-supplied role is not authorization. Role changes simplify policy administration only when the application's permission model fits roles.

See [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) for authorization boundaries and [Design Patterns: Elements of Reusable Object-Oriented Software](https://www.informit.com/store/design-patterns-elements-of-reusable-object-oriented-software-9780201633610) for the original GoF catalog.
## 13. Interview Tips / 面试准备

### Interview Tips / 面试准备

Use this note to prepare clear, evidence-based answers for behavioral interview questions. **面试回答应具体、贴合岗位，并如实说明个人贡献与结果。** Adapt each template to facts you can support; do not borrow another person's story or invent outcomes.

#### Discussing strengths and weaknesses

##### Strengths

Choose a strength that matters for the role, then support it with one real example. A compact structure is **context → action you took → result or evidence**.

- “I work carefully with edge cases. In [specific situation], I [action I personally took], which led to [verifiable result].”
- “I learn unfamiliar tools by [specific method]. For example, I used that approach to [real task] and [what changed or what I learned].”

Replace each bracketed part with your own evidence. If the result is qualitative, describe what changed without inventing a metric.

##### Weaknesses

**诚实说明一个真实的发展方向，并说明正在采取的步骤。** Choose something you are actively improving and explain how you notice progress. Avoid presenting a disguised strength or claiming a weakness that would prevent you from doing the role's core work.

- “I am still developing [skill]. I have been improving it by [specific practice], and I can now [observable progress].”

#### Salary expectations

- Research a current range for the role, seniority, location, and total compensation before the conversation.
- If you are ready to give a number, state a range and the assumptions behind it; leave room to discuss the full package.
- If the responsibilities are not yet clear, ask about the role's level and compensation range before giving a precise expectation.

#### Why are you a good fit?

Connect the role's stated needs to evidence you actually have:

1. **Skills match / 技能匹配** — identify the relevant requirement.
2. **Evidence / 事实依据** — give a project, responsibility, or result that demonstrates it.
3. **Motivation / 求职动机** — explain which part of this role you want to work on.

Template: “This role needs [requirement]. In [real example], I [specific contribution] and [result or learning]. I am interested in applying that experience to [specific part of the role].”

#### Company research

- Understand the product, users, and the role's team from current company materials.
- Connect your experience to a specific need instead of reciting company slogans.
- If you do not know a detail, say what you have learned so far and ask a focused question.

#### Addressing lack of experience

State the gap plainly, then describe related experience and a realistic learning plan. Avoid guaranteeing that you will master an unfamiliar area by a fixed date unless you have a basis for that estimate.

Template: “I have not used [technology] in [relevant context]. I have used [related skill] for [real example], and I would start by [specific way to learn or validate the new system].”

#### Questions to ask the interviewer

Prepare questions that help you understand the work. Choose the ones that remain unanswered by the conversation.

**About the role:**

- “What are the most important outcomes for this role in the first few months?”
- “What technical challenges would this person work on?”
- “How do you measure success for the position?”

**About the team:**

- “How does the team approach code review and knowledge sharing?”
- “How are technical decisions made, and who is involved?”

**About growth:**

- “What opportunities are there to deepen or broaden engineering skills?”
- “How does the team support progression for engineers?”

#### Closing the interview

Thank the interviewer, restate a specific reason for your interest, and ask about the next step if it has not already been explained. If your questions were answered during the discussion, say so and use the remaining time for a follow-up.

**See also:** [Agile and Scrum](#14.%20Agile%20and%20Scrum%20/%20%E6%95%8F%E6%8D%B7%E4%B8%8EScrum) for the current Scrum vocabulary used in team-process discussions.
## 14. Agile and Scrum / 敏捷与Scrum

### Agile and Scrum / 敏捷与Scrum

**Agile / 敏捷** describes values and principles for software development; it is not one prescribed workflow. **Scrum / Scrum 框架** is a specific framework with defined accountabilities, events, artifacts, and commitments. The Scrum details below follow the official November 2020 Scrum Guide, listed as the current version when checked 2026-10-15.

敏捷是一组价值与原则，Scrum则是包含明确职责、事件、工件和承诺的框架；这些结构用于检查和调整工作，并不保证照流程执行就会自动提升交付效果。

#### Agile principles

The Agile Manifesto values:

- Individuals and interactions over processes and tools.
- Working software over comprehensive documentation.
- Customer collaboration over contract negotiation.
- Responding to change over following a plan.

The items on the right still have value; the Manifesto gives greater weight to the items on the left. Its principles also emphasize frequent delivery, sustainable pace, technical excellence, simplicity, and regular reflection. How a team applies these ideas depends on its product, people, and constraints.

#### Scrum framework

Scrum uses empiricism and lean thinking to help a Scrum Team generate value through adaptive solutions. Its defined structure is not a promise that adopting the framework will automatically improve delivery.

##### Roles

The Scrum Guide describes three **accountabilities / 职责** within one Scrum Team; these are responsibilities, not a required set of job titles.

###### Product Owner

Accountable for maximizing product value and effective Product Backlog management. The Product Owner may delegate backlog work but remains accountable for the result.

###### Scrum Master

Accountable for establishing Scrum as defined in the Guide and for the Scrum Team's effectiveness. This includes coaching, helping remove impediments, and supporting the wider organization in its use of Scrum; it does not make the Scrum Master the team's line manager.

###### Developers

The people who create a usable Increment during each Sprint. They create and adapt the Sprint Backlog plan, uphold the Definition of Done, and hold one another accountable as professionals.

##### Events

The five events are the **Sprint**, **Sprint Planning**, **Daily Scrum**, **Sprint Review**, and **Sprint Retrospective**. The Sprint is the container for the other events and activities.

###### Sprint

A fixed-length event of one month or less. Teams choose a duration that supports inspection and adaptation; two weeks is common in some teams but is not prescribed by Scrum. The Sprint Goal provides a coherent objective while allowing the exact work to be clarified as learning occurs.

###### Sprint Planning

The Scrum Team plans why the Sprint is valuable, what can be done, and how the selected work will be completed. The output includes a Sprint Goal and the Developers' plan in the Sprint Backlog.

###### Daily Scrum

A 15-minute event for the Developers to inspect progress toward the Sprint Goal and adapt their plan. The Guide does not require each person to answer a fixed set of status questions. Developers choose a format that serves the purpose and may meet more often as needed.

###### Sprint Review

The Scrum Team and stakeholders inspect the Sprint's outcome and discuss adaptations. It is a working session to inform what to do next, not only a demonstration.

###### Sprint Retrospective

The Scrum Team inspects how the last Sprint went with regard to people, interactions, processes, tools, and the Definition of Done, then identifies useful improvements. It is one of the Scrum events and occurs within the Sprint cadence.

##### Artifacts

| Artifact / 工件 | Commitment / 承诺 | Purpose |
|---|---|---|
| Product Backlog / 产品待办列表 | Product Goal / 产品目标 | An ordered source of work for evolving the product |
| Sprint Backlog / Sprint 待办列表 | Sprint Goal / Sprint 目标 | The Sprint Goal, selected Product Backlog items, and the Developers' plan |
| Increment / 增量 | Definition of Done / 完成定义 | A usable step toward the Product Goal that meets the shared quality measure |

The commitments focus the artifact without replacing it. Multiple Increments may be created during a Sprint; the Sprint Review is not a release gate.

#### Common challenges

- **Treating Scrum as a status-report schedule:** the events exist to inspect and adapt work toward goals, not merely to report individual activity.
- **Treating the Sprint Backlog as an unchangeable contract:** the Developers adapt their plan as they learn, while working toward the Sprint Goal. The Product Owner and Developers can clarify and renegotiate scope without endangering that goal.
- **Skipping inspection and improvement:** omitting defined events loses their intended opportunities and means the team is not using the framework as described.
- **Assuming Scrum fits every problem:** choose a way of working that fits the product, feedback cycle, and organizational constraints. Regulated work can also use iterative development when its evidence and control requirements are built into the process.

**See also:** [Interview Tips](#13.%20Interview%20Tips%20/%20%E9%9D%A2%E8%AF%95%E5%87%86%E5%A4%87) for discussing team practices accurately.

Sources: [The Scrum Guide, November 2020](https://scrumguides.org/scrum-guide.html) and the [Agile Manifesto](https://agilemanifesto.org/).
## 15. Git Essentials / Git日常基础

### Git Essentials / Git日常基础

Git records project snapshots and lets branches point to different lines of history. **工作区 / working tree**, **暂存区 / index**, **提交 / commit**, **分支 / branch**, **远端 / remote**, **合并 / merge**, and **变基 / rebase** are the core terms used below. Branches are movable references to commits. Inspect status before changing or discarding work.

Git用提交保存项目快照，分支是指向提交的可移动引用；合并、变基和撤销应按历史是否共享及工作区状态选择，改写或丢弃内容前先检查并保护本地改动。

#### Core commands

| Command | Purpose |
|---|---|
| `git init` | Create an empty repository in the current directory |
| `git clone <url>` | Copy a repository and its history |
| `git status` | Show branch and working-tree state |
| `git add <path>` | Stage changes for the next commit |
| `git diff` | Show unstaged changes; use `--staged` for staged changes |
| `git commit -m "message"` | Record the staged snapshot |
| `git log --oneline --graph --decorate` | Inspect recent history and branch references |

Stage deliberately. `git add .` stages changes under the current directory; `git add -A` stages additions, modifications, and deletions in the repository. Review `git diff --staged` before committing.

#### Remote operations

~~~bash
git remote add origin <url>
git fetch origin
git push -u origin main
git pull
~~~

`git fetch` updates remote-tracking references without integrating them into the current branch. `git pull` fetches and then integrates the selected upstream using the configured or requested fast-forward, merge, or rebase behavior; inspect its options when the result matters. Fetch first when you want to review incoming commits before integrating them.

#### Branching

~~~bash
git branch feature/login       # create a branch
git switch feature/login       # switch branches
git switch -c feature/login    # create and switch
git branch -d feature/login    # delete only when Git considers it merged
git branch -D feature/login    # force-delete the branch reference
~~~

A feature branch is one collaboration approach. A team can instead integrate small changes directly or use a release-branch strategy. Git Flow adds long-lived branches such as `develop`; it can suit scheduled releases but adds merging and coordination. Choose according to release and integration needs rather than treating one strategy as universal.

#### Merge vs. rebase

##### `git merge`

Merge integrates another branch into the current branch. If possible, Git may fast-forward the current branch reference; otherwise it creates a merge commit that records both parent histories.

~~~bash
git switch main
git merge feature/login
~~~

~~~
A---B---C---M  main
     \     /
      D---E    feature/login
~~~

##### `git rebase`

Rebase replays commits onto a new base. The replayed commits have new IDs because their parent history changes.

~~~bash
git switch feature/login
git rebase main
~~~

~~~
A---B---C              main
         \
          D'---E'      feature/login
~~~

| Situation | A common choice | Why |
|---|---|---|
| Integrating work while keeping both branch histories visible | Merge | Records the integration point when a merge commit is created |
| Updating an unpublished local branch | Rebase | Replays local commits on the updated base |
| Commits others have already based work on | Coordinate before rebasing | Rebase changes commit IDs and requires collaborators to reconcile history |

A rebase can be useful on a shared branch only when the team coordinates the history rewrite and remote update. The practical rule is to avoid rewriting commits others may rely on.

#### Resolving conflicts

When Git cannot combine edits automatically, it marks the affected file:

~~~
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
~~~

1. Inspect the conflict and decide how the changes should combine.
2. Remove the conflict markers and edit the final content.
3. Stage the resolved path with `git add <path>`.
4. Finish with `git commit` after a merge, or `git rebase --continue` during a rebase.

Use `git merge --abort` or `git rebase --abort` to stop an integration that is still in progress.

#### Useful commands

##### `git stash`

Save tracked working-tree changes temporarily when switching tasks or branches.

~~~bash
git stash push -m "work in progress"
git stash list
git stash apply       # keep the stash entry
git stash pop         # apply and remove the stash entry if successful
git stash drop        # discard a stash entry
~~~

Untracked files are not included by default; use `-u` when they should be included.

##### `git cherry-pick`

Apply the change introduced by a selected commit to the current branch, creating a new commit.

~~~bash
git cherry-pick <commit>
~~~

##### `git reset` vs. `git revert`

In its commit form, `git reset` moves the current branch reference and optionally resets the index and working tree. The mode controls which state changes:

| Mode | Branch reference | Index | Tracked working-tree changes |
|---|---|---|---|
| `--soft` | Moves to target | Kept | Kept |
| `--mixed` (default) | Moves to target | Reset to target | Kept |
| `--hard` | Moves to target | Reset to target | Reset to target; conflicting tracked edits are discarded |

~~~bash
git reset --soft HEAD~1
git reset --mixed HEAD~1
git reset --hard HEAD~1
~~~

Use reset to adjust local history or staging when that is the intended scope. `--hard` replaces the working tree and index with the target state and may overwrite untracked files; check `git status` and preserve needed work first. It does not mean “delete every untracked file.”

`git revert <commit>` creates a new commit that applies the inverse of an earlier commit. It is often a better fit for undoing changes already shared in a branch, although conflicts may still need resolution. Reverting a merge commit requires selecting a mainline parent.

##### `git reflog`

The reflog records recent local updates to references such as `HEAD` and branch tips. It can help locate a commit after an accidental reset or branch deletion while the commit remains available.

~~~bash
git reflog
git branch recovery <commit>
~~~

Creating a branch preserves the recovered commit under a name; checking out a raw commit instead leaves HEAD detached. Reflogs are local and expire, so they are not a backup.

#### Pull request and code review workflow

A common workflow is to branch from the repository's integration branch, commit focused changes, push, open a pull request, review and revise, then merge using the repository's chosen method. The exact branch name and merge policy vary by project.

For commits, concise messages that describe the change help future readers. **Conventional Commits** is one optional convention, often paired with tooling that reads its prefixes:

~~~
feat(auth): refresh access tokens
fix(api): handle missing user
refactor(utils): extract date formatting
docs(readme): clarify setup
~~~

**See also:** [Agile and Scrum](#14.%20Agile%20and%20Scrum%20/%20%E6%95%8F%E6%8D%B7%E4%B8%8EScrum) for team-process context, and [Frontend Testing](../../frontend/testing/frontend-testing.md) for CI checks in a pull request.

Sources: [Git pull](https://git-scm.com/docs/git-pull), [Git merge](https://git-scm.com/docs/git-merge), [Git rebase](https://git-scm.com/docs/git-rebase), [Git reset](https://git-scm.com/docs/git-reset), [Git revert](https://git-scm.com/docs/git-revert), [Git reflog](https://git-scm.com/docs/git-reflog), [Git stash](https://git-scm.com/docs/git-stash), and [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick). Git manuals checked 2026-10-15.
## 16. Docker Operations / Docker操作参考

### Docker Operations / Docker操作参考

**镜像 / Image** is a read-only template of filesystem layers and configuration. **容器 / Container** is a created or running instance with a writable layer and optional mounts. Removing a container removes its writable layer; named volumes persist outside that container lifecycle.

镜像定义运行环境，容器承载一次运行实例；持久数据、网络访问和运行时凭据要分别配置，删除容器也不等于备份数据。

Before starting a fresh `postgres:16` instance in the examples below, provide a non-empty `POSTGRES_PASSWORD` through the shell environment or a secret manager. The official image requires it to initialize an empty data directory; it can be passed at runtime without placing a credential in the image or source file. Changing the variable later does not rotate a password in an already initialized volume.

#### Common operations

| Task | Command | Notes |
|---|---|---|
| Download an image | `docker pull redis:7` | Pin a tag or digest when repeatability matters; a tag may move. |
| List local images | `docker image ls` | Images can have multiple tags. |
| Create and start a container | `docker run --name cache -d redis:7` | Pulls the image if it is not available locally. |
| List running containers | `docker ps` | Add `-a` to include stopped containers. |
| Stop / start a container | `docker stop cache` / `docker start cache` | A stopped container still exists. |
| Read container logs | `docker logs cache` | Add `-f` to follow new output. |
| Run a command in a running container | `docker exec -it cache /bin/sh` | Run only when the image includes `/bin/sh`; minimal images may contain no shell. |
| Remove a stopped container | `docker rm cache` | `-f` also stops and removes a running container. |
| Remove an image | `docker image rm redis:7` | Refer to an image tag or image ID, not a container ID. |

Detached mode (such as `docker run -d`) returns the terminal while the container's main process runs. It does not supervise an application or guarantee that the container stays healthy. Use `docker ps` and `docker logs` to inspect it.

---

#### Publish ports

A port mapping forwards a host port to a port in the container. This publishes a container service to the host network; it does not make the service healthy or authenticated.

~~~bash
docker run -d --name cache -p 127.0.0.1:6000:6379 redis:7
~~~

Binding to `127.0.0.1` limits host access to the local machine. Omitting the host IP generally publishes on all host interfaces, subject to the host and Docker networking configuration. Container-to-container traffic on a shared Docker network normally uses the container port directly, not a published host port.

---

#### Networks

A user-defined bridge network lets attached containers communicate by container or service name through Docker's embedded DNS. Network membership controls which containers can connect at the Docker network layer; it is not application authentication or authorization.

~~~bash
docker network create app-net
docker run -d --name db --network app-net \
  --env POSTGRES_PASSWORD postgres:16
~~~

Only expose a host port when a process outside the network needs to connect. In Compose, services join a project network by default and can usually use each other's service names as hostnames.

---

#### Volumes and persistent data

Container writable layers are removed with their containers. A **named volume / 命名卷** is managed by Docker and remains after the container is removed. A **bind mount / 绑定挂载** maps a host path into the container and is useful when both host and container need the files. A volume is not a backup; plan backups and restore tests separately.

Omitting the volume source creates an anonymous volume with a generated name; it normally persists after container removal but is not automatically reused by a later container.

~~~bash
docker volume create db-data
docker run -d --name db --env POSTGRES_PASSWORD \
  --mount type=volume,src=db-data,dst=/var/lib/postgresql/data postgres:16
~~~

The destination path belongs to the image or application, so check that product's documentation. Compose declares named volumes at the top level:

~~~yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

Compose normally preserves declared named volumes on `docker compose down`. Adding `-v` removes project volumes and their data; review that effect before using it.

---

#### Compose

Compose describes a multi-container application in a YAML file. The default project network provides service-name discovery, so an application container can address the database as `db` on its container port. Publish a port only when the host or another external network needs access.

~~~yaml
services:
  app:
    build: .
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

~~~bash
docker compose up -d
docker compose ps
docker compose logs -f app
docker compose down
~~~

The current Compose Specification is used by Compose V2. Its top-level `version` field is obsolete and does not select a schema version. The older standalone `docker-compose` command is a legacy interface; use `docker compose` with the Compose CLI plugin.

---

#### Dockerfile and image builds

A Dockerfile describes image build steps. `RUN` executes during build; `CMD` supplies a default command or arguments when a container starts; `ENTRYPOINT` defines the executable to run. A runtime command can override `CMD`.

~~~dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
CMD ["node", "dist/index.js"]
~~~

Build with `docker build -t my-app:1.0 .`. This example assumes a package lockfile. The build context is the set of files sent to the builder; use a `.dockerignore` file to exclude files such as local dependencies, version-control data, and secrets. Multi-stage builds keep build-only stages out of the final image unless files are copied from them. Copy only the runtime files and dependencies the application needs.

Do not put credentials in a Dockerfile's `ENV` or `ARG` values. Use a BuildKit secret mount for a credential needed during build; it is made available to the build instruction without baking it into the image. At runtime, Compose secrets can be granted to selected services and mounted as files; protect the source secret file and host.

~~~dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
~~~

~~~bash
docker build --secret id=npmrc,src=.npmrc -t my-app:1.0 .
~~~

To push an image to a registry, authenticate with that registry, tag the image with its repository address, and push the tag. These commands use placeholders; `docker login` prompts or uses configured credentials, which should not be committed:

~~~bash
docker login registry.example.com
docker tag my-app:1.0 registry.example.com/team/my-app:1.0
docker push registry.example.com/team/my-app:1.0
~~~

Sources: [official PostgreSQL image environment variables and secrets](https://github.com/docker-library/docs/blob/master/postgres/README.md#environment-variables), [Docker image and container concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), [Docker networking](https://docs.docker.com/engine/network/), [port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker volumes](https://docs.docker.com/engine/storage/volumes/), [Compose file reference](https://docs.docker.com/compose/compose-file/), [Compose variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/), [`docker run` environment variables](https://docs.docker.com/reference/cli/docker/container/run/#set-environment-variables--e---env), [Docker build secrets](https://docs.docker.com/build/building/secrets/), [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/), [`docker login`](https://docs.docker.com/reference/cli/docker/login/), [`docker tag`](https://docs.docker.com/reference/cli/docker/image/tag/), and [`docker push`](https://docs.docker.com/reference/cli/docker/image/push/). Docker documentation checked 2026-10-15.
