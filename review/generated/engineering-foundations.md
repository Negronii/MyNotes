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
- [Web安全与身份认证 / Web Security and Authentication](#2.%20Web%20Security%20and%20Authentication%20/%20Web%E5%AE%89%E5%85%A8%E4%B8%8E%E8%BA%AB%E4%BB%BD%E8%AE%A4%E8%AF%81)：CORS之外的认证、Cookie与请求保护。
## 2. Web Security and Authentication / Web安全与身份认证

A bundle of interview questions on authentication, HTTPS, and the common web-security attacks you'll be asked about in any frontend interview.

### Cookies vs. tokens — which to use for authentication?

**Headline (30s):** Both are valid; pick based on architecture. **Cookie-based auth** (server-side sessions) is simple, secure against XSS when you use `HttpOnly`, and works automatically with every request — but doesn't scale as cleanly across domains or microservices. **Token-based auth** (JWT) is stateless, works naturally across domains, and scales horizontally — but requires you to handle storage carefully (XSS risk if in `localStorage`) and has no built-in revocation. Pick cookies for classic server-rendered apps, tokens for SPAs with cross-domain APIs or microservices.

#### Cookie-based authentication

1. User logs in with credentials.
2. Server creates a session, stores it server-side, sets `Set-Cookie` with the session ID.
3. Browser automatically sends the cookie with every request.
4. Server looks up the session by ID.

**Properties:**

- Automatic transmission with every request (including CORS when `withCredentials`).
- ~4KB size limit.
- `HttpOnly` — blocks JavaScript access (XSS mitigation).
- `Secure` — HTTPS only.
- `SameSite=Strict|Lax|None` — CSRF protection.

#### Token-based authentication (JWT)

1. User logs in with credentials.
2. Server generates a signed JWT containing claims, returns it in the response body.
3. Client stores the token (in memory or `localStorage`) and sends it via `Authorization: Bearer <token>`.
4. Server verifies the signature — no server-side session storage needed.

**Advantages:**

- Stateless — no server-side session store.
- Works across domains (no same-origin cookie restrictions).
- Self-contained — carries user data in the payload.
- Scales in distributed/microservice architectures.

**Trade-offs:**

- Can't be revoked before expiry without a blocklist (Redis, etc.).
- Larger than a session ID.

**Gotcha — JWT in `localStorage` is XSS-vulnerable.** Any XSS payload can read the token. Prefer `HttpOnly` cookies for the token itself; the cost is that you need CSRF protection. If you must store in JS, use short lifetimes + refresh tokens.

---

### What is Single Sign-On (SSO), and how does it work?

**Headline (30s):** SSO lets a user authenticate once with a central provider and access multiple systems without re-entering credentials. The provider issues a signed token that other systems trust. Common protocols: **SAML** (enterprise), **OAuth 2.0** (delegated API access), **OpenID Connect** (OAuth 2.0 + identity layer — the modern default for SSO).

#### Typical flow

1. User visits System A → no session → redirect to SSO provider.
2. User authenticates at the SSO provider.
3. SSO provider issues a token/ticket and redirects back to System A.
4. System A validates the token (signature, expiry) and creates its own session.
5. User visits System B → SSO cookie already exists → automatic login.

**Reach for SSO when:** managing auth across multiple internal systems or integrating with enterprise identity providers (Okta, Auth0, Azure AD).

---

### How does HTTPS protect against man-in-the-middle attacks?

**Headline (30s):** HTTPS encrypts traffic using a *hybrid* of asymmetric and symmetric cryptography. The server presents a public-key certificate issued by a trusted Certificate Authority (CA). The client verifies the certificate, uses the public key to exchange a symmetric session key, then both sides encrypt all subsequent data with that key. Because the attacker can't present a valid CA-signed certificate for the target domain, the browser rejects the connection — that's the "This site is not secure" warning.

#### Symmetric vs. asymmetric encryption

- **Symmetric** — same key encrypts and decrypts. Fast. Used for bulk data transfer.
- **Asymmetric** — public key encrypts, private key decrypts. Slower, expensive. Used only to establish the symmetric session key.

#### The HTTPS handshake (simplified)

1. Client receives the server's public key (inside an SSL/TLS certificate).
2. Client generates a random session key, encrypts it with the server's public key, sends it.
3. Server decrypts with its private key.
4. Both sides use the session key for symmetric encryption of everything that follows.

#### The MitM attack vector

An attacker sits between client and server. If the client blindly accepted any public key, the attacker could substitute their own and read everything.

**Prevention — trusted CAs:**

- Certificates are signed by CAs the browser trusts.
- Browser verifies:
  1. The certificate is signed by a trusted CA (chain of trust).
  2. The domain name matches the certificate's subject.
  3. The certificate hasn't expired or been revoked.

If any check fails, the browser blocks the connection.

**Gotcha — self-signed certificates in production:** Users see a scary warning. Use Let's Encrypt for free CA-signed certs; there's no reason to self-sign in production.

---

### XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**Headline (30s):** XSS happens when an attacker injects JavaScript into a page that other users view. The injected script runs with the full privileges of the site — it can read cookies, send authenticated requests, rewrite the DOM, anything the user could do. Prevention: **escape user content on render**, **use a framework that does it for you** (React escapes strings by default), and **set `Content-Security-Policy`** to restrict script sources.

#### Common sinks

- `innerHTML` / `outerHTML` — never concatenate user input here.
- `document.write` — same.
- `eval`, `new Function(...)` — never run strings from users.
- `<a href="javascript:...">` — validate URLs.
- React's `dangerouslySetInnerHTML` — the name is a warning.

#### Prevention layers

1. **Escape output** — `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, etc. Frameworks like React, Vue, and templating engines do this by default. **Don't defeat the default.**
2. **Content-Security-Policy (CSP)** — restrict where scripts can load from (`script-src 'self'`), block inline scripts unless allowlisted. Even if XSS is injected, the browser refuses to run it.
3. **`HttpOnly` cookies** — session tokens can't be stolen from `document.cookie`.
4. **Input validation** — allowlist the characters you expect (belt + suspenders, not a replacement for escaping).

---

### CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**Headline (30s):** CSRF tricks a logged-in user's browser into sending unwanted authenticated requests to your site. The malicious site embeds a form or image that posts to your domain; because the browser attaches the user's cookies automatically, the request looks legitimate to your server. Prevention: **anti-CSRF tokens** (random tokens per form that the attacker can't guess), **`SameSite` cookies** (modern default, blocks cross-site cookie sends), and **origin/referer checks**.

#### Prevention

- **Anti-CSRF tokens** — include a random token in forms; verify server-side. Attacker doesn't have it, can't forge a valid request.
- **`SameSite=Strict` / `SameSite=Lax`** — cookie not sent on cross-origin POSTs. Modern browsers default to `Lax`, which handles most cases.
- **Origin / Referer check** — reject state-changing requests whose `Origin` header doesn't match your domain.

**Gotcha — `SameSite=None` requires `Secure`:** Modern browsers reject `SameSite=None` cookies served over HTTP.

---

### Clickjacking — what is it, how do you prevent it?

**Headline:** Clickjacking overlays a transparent iframe of your site on top of a decoy page — the user thinks they're clicking "Win a prize", but actually they're clicking "Transfer money" on your site with their authenticated session. Prevention: tell the browser to refuse to be framed by another origin.

**Prevention headers:**

```
X-Frame-Options: SAMEORIGIN         (or DENY)
Content-Security-Policy: frame-ancestors 'self'
```

CSP's `frame-ancestors` is the modern approach; `X-Frame-Options` is the legacy one. Set both during migration, then drop `X-Frame-Options`.

---

### DDoS — what is it, what can you actually do?

**Headline:** Distributed Denial of Service floods your server with traffic from a botnet. It's not solvable in application code — the volume is too big. Prevention lives at the edge: **CDN-based DDoS protection** (Cloudflare, AWS Shield, Akamai), **rate limiting** at ingress, and **Web Application Firewalls** (WAFs) to filter known-bad patterns.

What you *can* do in application code: respond quickly with minimal work to known-abusive traffic, cache aggressively so legitimate traffic is cheap, and avoid expensive endpoints that could amplify an attack.

---

### SQL injection — frontend's role?

**Headline:** SQL injection is a backend vulnerability — user input concatenated into raw SQL queries lets attackers manipulate the database. The frontend's role is mostly limited: validate input, but never rely on client-side validation for security. The real fix is on the server: **parameterized queries** / **prepared statements**, which separate SQL from data so injection becomes impossible.

**Prevention layers (backend-owned, but worth knowing):**

- Parameterized queries / prepared statements.
- ORM tools that parameterize by default (Sequelize, TypeORM, Prisma).
- Principle of least privilege on database accounts (read-only service account can't drop tables).
- Input validation (defense in depth, not primary defense).

**See also:** [`HTTP Protocols and WebSockets / HTTP 协议与 WebSocket`](#1.%20HTTP%20Protocols%20and%20WebSockets%20/%20HTTP%E5%8D%8F%E8%AE%AE%E4%B8%8EWebSocket) for CORS and HTTPS handshake basics, [`5.2 Browser Storage and Communication`](../../frontend/browser-apis/browser-storage-and-communication.md) for `postMessage` and storage security.
## 3. Algorithms and Complexity / 算法与复杂度分析

Reach for this when you need a quick reference for the common algorithmic patterns that show up in frontend interviews — dynamic programming, binary search, two pointers, sorting, and string algorithms. Each section gives the canonical implementation with complexity analysis.

#### Dynamic programming

Dynamic programming solves problems by breaking them into overlapping subproblems and storing results to avoid redundant computation. Two implementation styles: **top-down (memoization)** and **bottom-up (iterative)** — bottom-up is usually preferred for constant-space optimizations.

##### Fibonacci

**Recursive** — O(2^n) time, O(n) stack space. Exponential because the same subproblems are re-solved.

```javascript
function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
```

**DP (iterative)** — O(n) time, O(1) space.

```javascript
function fib(n) {
  if (n <= 1) return n;
  let prev = 0, curr = 1;
  for (let i = 2; i <= n; i++) {
    [prev, curr] = [curr, prev + curr];
  }
  return curr;
}
```

##### Climbing stairs (frog jump)

Count the ways to reach step `n` by jumping 1 or 2 steps at a time. Same recurrence as Fibonacci: `dp[i] = dp[i-1] + dp[i-2]`.

Generalized to variable step sizes:

```javascript
function climbStairs(n, steps) {
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1;
  for (let i = 1; i <= n; i++) {
    for (const step of steps) {
      if (i >= step) dp[i] += dp[i - step];
    }
  }
  return dp[n];
}
```

##### 0/1 Knapsack

Maximize total value without exceeding weight capacity. Each item can be used at most once. Iterate capacities **in reverse** so each item isn't reused.

```javascript
function knapsack(W, weights, values) {
  const dp = new Array(W + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let w = W; w >= weights[i]; w--) {
      dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

---

#### Binary search

O(log n). **Requires a sorted array**. Halves the search space each iteration.

```javascript
function binarySearch(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) return mid;
    if (nums[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}
```

**Gotcha — integer overflow (other languages):** `(left + right) / 2` can overflow in languages with fixed-width ints. Use `left + (right - left) / 2` to be safe. Not an issue for JS `Number`, but interviewers notice.

---

#### Two pointers

A broad family of techniques where two indices sweep through an array — often O(n) replacements for naive O(n²) nested loops.

##### Two Sum on sorted array

```javascript
function twoSum(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left < right) {
    const sum = nums[left] + nums[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return [-1, -1];
}
```

##### Move zeros to end (in-place)

```javascript
function moveZeros(nums) {
  let insertPos = 0;
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] !== 0) {
      [nums[insertPos], nums[i]] = [nums[i], nums[insertPos]];
      insertPos++;
    }
  }
}
```

---

#### Sorting

##### Quicksort

Average O(n log n), worst O(n²). Pick a pivot, partition into smaller/larger subarrays, recurse.

```javascript
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = [], mid = [], right = [];
  for (const x of arr) {
    if (x < pivot) left.push(x);
    else if (x > pivot) right.push(x);
    else mid.push(x);
  }
  return [...quickSort(left), ...mid, ...quickSort(right)];
}
```

**Reach for `Array.prototype.sort`** in production code — V8 uses TimSort (stable, O(n log n) worst case) as of Node 10+. Write your own only for an interview.

---

#### String algorithms

##### Palindrome check

```javascript
function isPalindrome(n) {
  const s = String(n);
  let left = 0, right = s.length - 1;
  while (left < right) {
    if (s[left++] !== s[right--]) return false;
  }
  return true;
}
```

##### Longest consecutive character

```javascript
function longestConsecutive(s) {
  let maxChar = '', maxLen = 0;
  let curLen = 1;
  for (let i = 1; i <= s.length; i++) {
    if (i < s.length && s[i] === s[i - 1]) {
      curLen++;
    } else {
      if (curLen > maxLen) {
        maxLen = curLen;
        maxChar = s[i - 1];
      }
      curLen = 1;
    }
  }
  return { char: maxChar, len: maxLen };
}
```

##### Number formatting (thousand separators)

```javascript
function formatNumber(n) {
  return n.toLocaleString();
}

function formatNumber(n) {
  const s = String(n);
  let result = '';
  let count = 0;
  for (let i = s.length - 1; i >= 0; i--) {
    result = s[i] + result;
    if (++count % 3 === 0 && i > 0) result = ',' + result;
  }
  return result;
}
```

**Reach for `toLocaleString`** in real code — it handles locales automatically. The manual version is what interviewers want to see.

##### Switch letter case

```javascript
function switchCase(s) {
  return s.split('').map(ch => {
    const code = ch.charCodeAt(0);
    if (code >= 65 && code <= 90)  return String.fromCharCode(code + 32); // A-Z → a-z
    if (code >= 97 && code <= 122) return String.fromCharCode(code - 32); // a-z → A-Z
    return ch;
  }).join('');
}
```

---

#### Big-O cheat sheet

| Complexity | Example |
|---|---|
| O(1) | Hash map lookup, array index access |
| O(log n) | Binary search, balanced BST operations |
| O(n) | Single pass over array, linear scan |
| O(n log n) | Efficient sorts (merge, quicksort avg, heap) |
| O(n²) | Nested loops, naive sorts (bubble, insertion) |
| O(2^n) | Naive recursive Fibonacci, power set enumeration |
| O(n!) | Generating all permutations |

**See also:** [`10.2 Core Data Structures`](#4.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84) for trees, BSTs, and trie references, [`10.3 Practical Data Structure Implementations`](#5.%20Practical%20Data%20Structure%20Implementations%20/%20%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%AE%9E%E7%8E%B0) for LRU, queues, and stacks.
## 4. Core Data Structures / 核心数据结构

Reach for this when you need a quick reference for tree-based data structures — traversals, balanced trees, tries, DOM traversal patterns, and the array↔tree conversion that comes up in real frontend work.

#### Tree traversals

Three depth-first orders for a binary tree. Choose based on what you're doing:

- **In-order** (Left → Root → Right) — produces **sorted output** for BSTs.
- **Pre-order** (Root → Left → Right) — useful for **copying** or **serializing** trees.
- **Post-order** (Left → Right → Root) — useful for **deletion** (children before parent).

##### Kth smallest in a BST

In-order traversal visits BST nodes in ascending order. Stop at the k-th node.

```javascript
function kthSmallest(root, k) {
  let count = 0, result = null;

  function inorder(node) {
    if (!node || result !== null) return;
    inorder(node.left);
    if (++count === k) { result = node.val; return; }
    inorder(node.right);
  }

  inorder(root);
  return result;
}
```

---

#### Why use binary trees?

| Structure | Access | Insert/Delete |
|---|---|---|
| Array | O(1) | O(n) |
| Linked list | O(n) | O(1) |
| Balanced BST | O(log n) | O(log n) |

A balanced binary tree is the "best of both worlds" between arrays and linked lists — O(log n) for both lookup and modification. **An unbalanced tree degrades to a linked list** with O(n) operations, which is why production code uses self-balancing variants.

---

#### Self-balancing trees

##### Red-Black Tree

A BST with coloring rules that keep the tree approximately balanced. Properties:

- Each node is red or black.
- The root is black.
- No two consecutive red nodes on any path.
- All paths from root to leaf have the same number of black nodes.

**Used in:** `std::map` (C++), `TreeMap` (Java), Linux kernel scheduler.

##### B-Tree / B+ Tree

Multi-way search trees optimized for disk I/O. Each node contains multiple keys and children, minimizing the number of disk reads needed.

- **B-Tree** — keys and data in all nodes.
- **B+ Tree** — data only in leaf nodes; leaves are linked for efficient range queries.

**Used in:** database indexes (MySQL InnoDB, PostgreSQL), file systems.

---

#### Trie (prefix tree)

A tree where each node represents a character. Paths from the root spell prefixes. Checking if a string is a prefix takes O(m) time where m is the string length — independent of the dictionary size.

**Reach for a trie when:** building autocomplete, spell-check, IP routing tables, or any prefix-based lookup.

---

#### DOM tree traversal

##### DFS — depth-first search

Visit the deepest descendants first, then backtrack.

```javascript
function dfs(node) {
  visit(node);
  node.childNodes.forEach(child => dfs(child));
}

// Iterative with an explicit stack
function dfsIterative(node) {
  const stack = [node];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    const children = Array.from(n.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
```

##### BFS — breadth-first search

Visit all siblings level by level.

```javascript
function bfs(node) {
  const queue = [node];
  while (queue.length) {
    const n = queue.shift();
    visit(n);
    n.childNodes.forEach(child => queue.push(child));
  }
}
```

**Reach for DFS** when the order of traversal matters (pre/post) or you want to accumulate something recursively. **Reach for BFS** when you need the shortest path in an unweighted graph or "find the nearest match" semantics.

---

#### Array ↔ Tree conversion

A classic interview problem — and a real problem that comes up any time you have to map relational data (flat rows) to hierarchical UI (tree components).

##### Array to tree

```javascript
function arrayToTree(arr) {
  const map = new Map();
  let root = null;

  arr.forEach(item => map.set(item.id, { ...item, children: [] }));

  arr.forEach(item => {
    const node = map.get(item.id);
    if (item.parentId === 0) {
      root = node;
    } else {
      map.get(item.parentId)?.children.push(node);
    }
  });

  return root;
}
```

Two-pass O(n): first pass creates all nodes with empty `children`; second pass links children to parents.

##### Tree to array

```javascript
function treeToArray(tree) {
  const result = [];
  function traverse(node, parentId) {
    result.push({ id: node.id, parentId, name: node.name });
    node.children?.forEach(child => traverse(child, node.id));
  }
  traverse(tree, 0);
  return result;
}
```

**Reach for this pattern when:** persisting tree state to a database (array form is easier), loading tree data from a REST API, or reshaping data for a tree UI component.

**See also:** [`10.1 Algorithms and Complexity`](#3.%20Algorithms%20and%20Complexity%20/%20%E7%AE%97%E6%B3%95%E4%B8%8E%E5%A4%8D%E6%9D%82%E5%BA%A6%E5%88%86%E6%9E%90) for sorts, searches, and DP patterns, [`10.3 Practical Data Structure Implementations`](#5.%20Practical%20Data%20Structure%20Implementations%20/%20%E5%B8%B8%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E5%AE%9E%E7%8E%B0) for LRU cache, queues, and stacks.
## 5. Practical Data Structure Implementations / 常用数据结构实现

Reach for this when you need canonical JavaScript implementations of the data structures that come up in interviews — LRU cache, queue, stack — plus a note on how React Fiber uses linked-list structures internally.

#### LRU Cache

Least Recently Used cache evicts the least recently accessed item when the cache reaches capacity. A classic interview question testing hash maps and ordering.

##### Using `Map` (insertion order)

JavaScript's `Map` preserves insertion order — we can exploit this by deleting and re-inserting on access, so the "oldest" key is always first.

```javascript
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.cache = new Map();
  }

  get(key) {
    if (!this.cache.has(key)) return -1;
    const value = this.cache.get(key);
    this.cache.delete(key);   // remove...
    this.cache.set(key, value); // ...and re-insert as most recent
    return value;
  }

  put(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
```

**Simpler to write, all operations O(1)** thanks to `Map`'s built-in ordering.

##### Using doubly linked list + hash table (the "classic" form)

The canonical textbook implementation: a hash table for O(1) key lookup, a doubly linked list for O(1) ordering. Most recently used items move to the head; the tail is evicted when full. Interviewers who want to see the "real" DS pattern expect this one.

```javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = {};
    this.head = new ListNode(0, 0); // sentinel
    this.tail = new ListNode(0, 0); // sentinel
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get(key) {
    if (!(key in this.map)) return -1;
    const node = this.map[key];
    this._remove(node);
    this._addToHead(node);
    return node.value;
  }

  put(key, value) {
    if (key in this.map) {
      const node = this.map[key];
      node.value = value;
      this._remove(node);
      this._addToHead(node);
    } else {
      if (Object.keys(this.map).length >= this.capacity) {
        const lru = this.tail.prev;
        this._remove(lru);
        delete this.map[lru.key];
      }
      const newNode = new ListNode(key, value);
      this.map[key] = newNode;
      this._addToHead(newNode);
    }
  }

  _addToHead(node) {
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
```

**Reach for the `Map`-based version** in code reviews and production; reach for the linked-list version in interviews that specifically ask you to implement it from scratch.

---

#### Queue (FIFO)

First In, First Out. Used in BFS, task scheduling, message processing.

##### Linked-list implementation

Array-based `shift()` is **O(n)** because elements shift down. A linked-list queue is O(1) for both enqueue and dequeue.

```javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  enqueue(val) {
    const node = { val, next: null };
    if (this.tail) this.tail.next = node;
    else           this.head = node;
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (!this.head) return null;
    const val = this.head.val;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return val;
  }
}
```

**Gotcha — don't use `arr.shift()` for a queue** in tight loops. It's O(n) because every element has to shift down a slot. Either use a linked list or track a head index and skip over consumed slots.

---

#### Stack (LIFO)

Last In, First Out. Used in DFS, undo/redo, expression parsing, browser history.

```javascript
class Stack {
  constructor() { this.items = []; }
  push(val)  { this.items.push(val); }
  pop()      { return this.items.pop(); }
  peek()     { return this.items[this.items.length - 1]; }
  isEmpty()  { return this.items.length === 0; }
}
```

`push` and `pop` on a JavaScript array are O(1), so a plain array is the canonical implementation.

---

#### Linked lists in frontend — React Fiber

**Headline:** React Fiber represents the component tree as a **linked structure** (each fiber node has `child`, `sibling`, and `return` pointers) rather than a traditional tree. This enables:

- **Incremental rendering** — work can be split into small units and spread across frames.
- **Priority-based scheduling** — high-priority updates (input, animations) can interrupt lower-priority rendering.
- **Pause and resume** — rendering yields to the browser for layout and paint, then resumes where it left off.

The linked-list-ish structure is chosen precisely because it's *easy to traverse one unit at a time* — walk to the child, record position, yield. Traditional recursive traversal would block the main thread until the whole tree was done.

**Reach for this knowledge when:** interviewers ask about React's Fiber reconciler, concurrent mode, or how React 18's scheduler works under the hood.

**See also:** [`10.1 Algorithms and Complexity`](#3.%20Algorithms%20and%20Complexity%20/%20%E7%AE%97%E6%B3%95%E4%B8%8E%E5%A4%8D%E6%9D%82%E5%BA%A6%E5%88%86%E6%9E%90) for algorithmic patterns, [`10.2 Core Data Structures`](#4.%20Core%20Data%20Structures%20/%20%E6%A0%B8%E5%BF%83%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84) for tree-based structures, [`9.1 Virtual DOM and Framework Selection`](../../frontend/frameworks/virtual-dom-and-framework-selection.md) for VDOM reconciliation details.
## 6. Node.js Fundamentals / Node.js基础

A bundle of interview questions about Node.js's runtime model — threads vs. processes, multi-core utilization, and serverless.

### What's the difference between a process and a thread?

**Headline (30s):** A **process** is the OS's unit of isolation — it gets its own memory space and can't directly touch another process's data. A **thread** is a unit of execution *inside* a process; threads share memory with their siblings. Node.js runs user JavaScript on a single thread, so you can't naively use multiple CPU cores without spawning more processes (`cluster`, `fork`) or using worker threads for CPU-bound work.

- **Process** — own memory, isolated, heavier to create, safer.
- **Thread** — shared memory, lighter, data races possible without locks.

Why Node chose a single thread: the event loop model makes I/O-bound code fast and avoids the entire class of threading bugs (races, deadlocks) at the cost of not scaling across CPU cores without extra machinery.

---

### How do you use multiple CPU cores in Node.js?

**Headline (30s):** Three options: **`child_process.fork()`** for spawning independent Node.js processes (usually for one-off CPU work), **`cluster`** for sharing a server port across worker processes (the classic "one process per core" web server pattern), and **worker threads** (`worker_threads`) for sharing memory with the parent. In production, most teams wrap `cluster` with **PM2** instead of managing workers manually.

#### `child_process.fork()` — spawn a Node.js process

Creates a child process running another JS file. Parent and child communicate via IPC (`send` / `message`).

```javascript
// main.js
const { fork } = require('child_process');

const child = fork('./compute.js');
child.send({ task: 'fibonacci', n: 40 });

child.on('message', (result) => {
  console.log('Result:', result);
});

// compute.js
process.on('message', (msg) => {
  if (msg.task === 'fibonacci') {
    process.send(fib(msg.n));
  }
});
```

**Reach for `fork`** when you have a one-off CPU-intensive task (image processing, a heavy computation) that would otherwise block the event loop. The cost: process spawn time (tens of milliseconds) and serialization overhead.

#### `cluster` — load-balanced HTTP workers

Creates worker processes that all listen on the same port. Incoming connections are load-balanced across them automatically.

```javascript
const cluster = require('cluster');
const http    = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  for (let i = 0; i < numCPUs; i++) cluster.fork();
  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died, restarting...`);
    cluster.fork();
  });
} else {
  http.createServer((_, res) => {
    res.writeHead(200);
    res.end('Hello');
  }).listen(8000);
}
```

**Reach for `cluster`** for Node HTTP servers on multi-core machines — you get near-linear throughput scaling with CPUs and automatic restart on crashes.

#### PM2 — production-grade process manager

Don't manage `cluster` by hand in production. PM2 wraps it with health checks, zero-downtime restarts, log rotation, and monitoring.

```bash
pm2 start app.js -i max   # one process per CPU
pm2 list                  # view running processes
pm2 monit                 # real-time metrics
pm2 reload app            # zero-downtime restart
```

**Gotcha — shared state between workers:** Each worker has its own memory. In-memory caches, sessions, or WebSocket connection maps need external storage (Redis) or a broadcast mechanism if you need cross-worker consistency.

---

### What is serverless / cloud functions, and when would you use them?

**Headline (30s):** Serverless (AWS Lambda, Google Cloud Functions, Vercel Edge Functions) runs your code without you managing servers — the cloud provider spins up a process, runs your handler, and tears it down when traffic subsides. You pay per execution, not per idle hour. The big trade-offs: **cold-start latency** (first invocation after idle can take hundreds of ms), hard **execution-time limits** (typically 10–60 seconds), and **no persistent in-memory state** between invocations.

#### Advantages over traditional deployment

- **Cost** — pay only for execution time; no idle servers.
- **Auto-scaling** — the platform handles traffic spikes without capacity planning.
- **Operational overhead** — no patching, provisioning, or process management.
- **Deployment speed** — push code directly; no infra pipeline for simple functions.

#### Trade-offs

- **Cold starts** — a fresh container costs hundreds of ms on first invocation. Mitigations: provisioned concurrency, smaller bundles, avoid heavy init.
- **Execution limits** — long-running work (reports, data migrations) needs a different compute model.
- **Statelessness** — every invocation might land on a new container. Keep persistent state in a database or cache.
- **Vendor lock-in** — handler signatures, auth, and tooling vary between providers.

#### When to reach for serverless

- **API endpoints** — thin, stateless handlers.
- **Webhooks** — receive events from third-party services.
- **Scheduled jobs** — cron-like tasks (cleanup, reports).
- **Event-driven processing** — react to file uploads, DB changes, message queues.

**When not:** persistent connections (WebSocket servers — though providers now offer variants), long-running batch jobs, or workloads where cold-start latency is unacceptable (some user-facing APIs).

**See also:** [`7.1 Event Loop`](../../frontend/runtime/event-loop.md) for the single-threaded runtime model that shapes these choices, [`12.1 Software Design Principles`](#7.%20Software%20Design%20Principles%20/%20%E8%BD%AF%E4%BB%B6%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99) for where serverless fits in overall application architecture.
## 7. Software Design Principles / 软件设计原则

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

A new shipping policy can be supplied without changing the calculator, while the selection and shared contract still need maintenance. See [Strategy in practice](#8.%20Design%20Patterns%20in%20Practice%20/%20%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E5%AE%9E%E8%B7%B5).

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

**See also:** [Design Patterns in Practice](#8.%20Design%20Patterns%20in%20Practice%20/%20%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E5%AE%9E%E8%B7%B5) for reusable patterns that can support these principles.

Sources: [Robert C. Martin, The Open-Closed Principle](https://objectmentor.com/resources/articles/ocp.pdf), [Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf), and [Liskov and Wing, A Behavioral Notion of Subtyping](https://doi.org/10.1145/197320.197383).
## 8. Design Patterns in Practice / 设计模式实践

A bundle of interview questions on the design patterns that come up most in frontend work — plus two system-design mini-problems (low-code editor, RBAC) that exercise those patterns.

### When do you use the Factory pattern?

**Headline (30s):** A factory is a function that encapsulates object creation — hiding `new`, hiding conditional logic, and allowing the factory to return different subtypes based on input. Reach for it when construction is non-trivial or when callers shouldn't need to know which concrete class they're getting. It's arguably the most common pattern in JS because it plays nicely with the language's bias toward plain functions.

```javascript
function createButton(type) {
  if (type === 'primary')   return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
```

**Real-world examples:** `React.createElement()`, jQuery's `$()`, `document.createElement()`, `Array.of`.

---

### When do you use the Singleton pattern?

**Headline:** Guarantees one instance across the app, with a single global access point. Reach for it when a shared resource (store, event bus, cache, connection pool) must be consistent across consumers.

```javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) {
      Store.instance = new Store();
    }
    return Store.instance;
  }
}
```

**Real-world examples:** Redux/Vuex store, global event bus, database connection pool, `window` object.

**Gotcha — singletons hurt testability.** Global state is hard to isolate in tests. Modern apps often sidestep the pattern with **context providers** (React) or **module-scoped singletons** (one instance per module, but injectable in tests). Ask yourself whether "one instance" is the real requirement, or whether "shared instance for this context" would work — the latter is usually better.

---

### When do you use the Strategy pattern?

**Headline (30s):** Defines a family of interchangeable algorithms, each encapsulated behind the same interface. Pick one by key instead of writing a giant switch/if-else. Reach for it when you have multiple algorithms for the same concern (sort, validate, format, price) and callers need to pick at runtime.

```javascript
const strategies = {
  express:   pkg => pkg.weight * 10,
  standard:  pkg => pkg.weight * 5,
  overnight: pkg => pkg.weight * 20,
};

function calculateShipping(strategy, pkg) {
  return strategies[strategy](pkg);
}

calculateShipping('express', { weight: 3 }); // 30
```

**Use cases:** form validation rules, sort algorithms, pricing tiers, authentication methods.

Strategy is the natural implementation of the **Open/Closed Principle** (see [`12.1 Software Design Principles`](#7.%20Software%20Design%20Principles%20/%20%E8%BD%AF%E4%BB%B6%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99)) — add new strategies without touching the dispatcher.

---

### What's the difference between Observer and Publish-Subscribe?

**Headline (30s):** Both let something react to something else, but differ in **coupling**. **Observer** — the subject holds a direct reference to its observers and calls them itself (`element.addEventListener` fits this model). **Publish-Subscribe** — a central channel mediates; publishers and subscribers never know about each other (event bus). Pub-Sub is more decoupled and flexible; Observer is simpler and easier to trace.

#### Observer

```javascript
class Subject {
  constructor() { this.observers = []; }
  subscribe(observer) { this.observers.push(observer); }
  notify(data) { this.observers.forEach(obs => obs.update(data)); }
}
```

**Coupling:** direct. The subject knows its observers.

**Example:** DOM event listeners — the element "knows" every handler it fires.

#### Publish-Subscribe

```javascript
const eventBus = new EventBus();
eventBus.on('user:login', updateDashboard);       // subscriber
eventBus.emit('user:login', { name: 'Alice' });   // publisher
```

**Coupling:** indirect — both parties know only the event channel and event name.

**Key difference:** Observer is easier to debug (you can find observers by inspecting the subject); Pub-Sub is more flexible but harder to trace because the wiring is scattered across the codebase.

See [`5.1 DOM Manipulation and Events`](../../frontend/browser-apis/dom-manipulation-and-events.md) for a concrete EventBus implementation.

---

### How would you design the data model for a low-code editor?

**Headline (30s):** A drag-and-drop page builder needs four systems: **a component tree** (each node has id, type, props, style, children), **layer ordering** (z-index via array position), **undo/redo** (command pattern with a history stack), and **real-time collaboration** (WebSocket state sync with conflict resolution, usually OT or CRDT).

#### Component model

```javascript
const component = {
  id:    'comp_001',
  type:  'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
```

The tree is the source of truth. Rendering walks the tree; the sidebar edits the tree; persistence serializes the tree.

#### Key requirements

- **Component registry** — a map of `type → renderer` so new component types can be added without touching the core.
- **Layer management** — z-index is the array order within `children`; reordering is a splice.
- **Undo/redo** — command pattern with a history stack. Each mutation pushes a reversible command; undo pops and inverts.
- **Real-time collaboration** — WebSocket broadcasts mutations; OT/CRDT resolves conflicts (see [`5.2 Browser Storage and Communication`](../../frontend/browser-apis/browser-storage-and-communication.md)).

---

### How does Role-Based Access Control (RBAC) work?

**Headline:** RBAC assigns permissions to **roles**, not users. Users are then assigned one or more roles. Adding a new role or changing a role's permissions doesn't require touching user records or app code — only the role and permission tables.

#### Data model

- **User** — `id`, `username`, `password_hash`
- **Role** — `id`, `role_name` (e.g., admin, editor, viewer)
- **Permission** — `id`, `permission_name` (e.g., read, write, delete)
- **UserRole** — `user_id`, `role_id` (many-to-many)
- **RolePermission** — `role_id`, `permission_id` (many-to-many)

#### Access check flow

```
User → UserRole → Role → RolePermission → Permission
```

To check "can this user write?", look up their roles, then the permissions on those roles, then check if `write` is in the set.

**Why this structure:** the indirection through `Role` is what makes RBAC scalable. Assigning a permission to a role changes it for everyone with that role. Assigning a role to a user gives them every permission the role has. No code changes needed.

**See also:** [`12.1 Software Design Principles`](#7.%20Software%20Design%20Principles%20/%20%E8%BD%AF%E4%BB%B6%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99) for the SOLID foundations these patterns implement, [`5.1 DOM Manipulation and Events`](../../frontend/browser-apis/dom-manipulation-and-events.md) for a concrete EventBus.
## 9. Interview Tips / 面试准备

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

**See also:** [Agile and Scrum](#10.%20Agile%20and%20Scrum%20/%20%E6%95%8F%E6%8D%B7%E4%B8%8EScrum) for the current Scrum vocabulary used in team-process discussions.
## 10. Agile and Scrum / 敏捷与Scrum

**Reach for this when** you need a quick reference for how most modern engineering teams organize work — Agile principles, the Scrum framework (roles, events, artifacts), and the common failure modes.

**Headline:** **Agile** is a philosophy — iterative delivery, continuous feedback, adaptability. **Scrum** is the most widely used framework for practicing Agile, with defined **roles** (Product Owner, Scrum Master, Dev Team), **events** (Sprint, Planning, Standup, Review, Retro), and **artifacts** (Product Backlog, Sprint Backlog, Increment). Interviewers usually want to know you understand both the theory and the real-world tradeoffs.

#### Agile principles

From the Agile Manifesto:

- **Working software** over comprehensive documentation.
- **Customer collaboration** over contract negotiation.
- **Responding to change** over following a rigid plan.
- **Individuals and interactions** over processes and tools.

##### In practice

- Deliver working software in short iterations (1–4 weeks).
- Welcome changing requirements, even late in development.
- Business and development teams work together daily.
- Build projects around motivated individuals; trust them to deliver.
- Maintain a sustainable development pace.
- Regularly reflect and adjust processes.

##### Benefits

- **Flexibility** — adapt to changing requirements without derailing the project.
- **Quality** — frequent testing and integration catch issues early.
- **Visibility** — regular demos and retrospectives keep stakeholders informed.
- **Reduced risk** — short iterations surface problems quickly.

#### Scrum framework

Scrum is the most widely used Agile framework. It defines roles, events, and artifacts for organizing iterative work.

##### Roles

###### Product Owner

- Defines and prioritizes the **product backlog**.
- Represents stakeholder interests.
- Decides **what** to build and in what order.

###### Scrum Master

- Facilitates the Scrum process; removes impediments.
- Coaches the team on Scrum practices.
- Shields the team from external interruptions.
- **Does not** manage the team — the team is self-organizing.

###### Development Team

- Cross-functional group that designs, builds, and tests the product.
- Typically 3–9 people.
- Self-organizing: the team decides **how** to accomplish sprint goals.

##### Events

###### Sprint

A fixed time-box (usually 2 weeks) during which a potentially shippable increment is created.

###### Sprint Planning

The team selects backlog items for the sprint and breaks them into tasks. Outcome: a sprint goal + a sprint backlog.

###### Daily Standup

A 15-minute daily meeting where each member answers:

1. What did I do yesterday?
2. What will I do today?
3. Are there any blockers?

###### Sprint Review

End-of-sprint demo to stakeholders. Gather feedback and update the product backlog.

###### Sprint Retrospective

The team reflects on the sprint process:

- What went well?
- What could be improved?
- What actions will we take?

##### Artifacts

- **Product Backlog** — ordered list of everything needed in the product.
- **Sprint Backlog** — items selected for the current sprint + the delivery plan.
- **Increment** — the sum of completed backlog items, in a usable state.

#### Common challenges

- **Scope creep** — adding items mid-sprint undermines the sprint commitment. Use the backlog for new requests; slot into future sprints.
- **Resistance to change** — teams used to waterfall may struggle with iterative planning. Start with pilot teams and demonstrate results.
- **Skipping retrospectives** — without reflection, the same problems recur. Retrospectives are **not optional**.
- **"Status-report standups"** — standups that become PM status updates defeat the purpose. Keep the "blockers" slot prominent.

**Gotcha — Scrum isn't a silver bullet.** It works best for teams building iterative products with changing requirements. For heavily regulated work (e.g., hardware, medical devices) or teams with fixed requirements, waterfall or hybrid models may still fit. Interviewers appreciate candidates who understand *when* Agile helps, not just how to recite the ceremonies.

**See also:** [`14.1 Interview Tips`](#9.%20Interview%20Tips%20/%20%E9%9D%A2%E8%AF%95%E5%87%86%E5%A4%87) for how to discuss Agile experience in interviews.
## 11. Git Essentials / Git日常基础

**Reach for this when** you need a quick reference for day-to-day Git — core commands, branching, merge vs. rebase, conflict resolution, and the PR workflow.

**Headline:** Six buckets. **Core commands** (init, clone, add, commit, status, log, diff). **Remote operations** (push, pull, fetch). **Branching** (branch, checkout, switch). **Merge vs. rebase** (merge for shared branches, rebase for local). **Recovery tools** (stash, reset vs. revert, reflog). **PR workflow** (feature branches, clear messages, squash-merge).

#### Core commands

| Command | Purpose |
|---|---|
| `git init` | Initialize a new repository |
| `git clone <url>` | Clone a remote repository |
| `git add <file>` | Stage changes (`git add .` for all) |
| `git commit -m "msg"` | Commit staged changes |
| `git status` | Show working tree status |
| `git log --oneline` | Compact commit history |
| `git diff` | Unstaged changes (`--staged` for staged) |

#### Remote operations

```bash
git remote add origin <url>
git push -u origin main        # first push, sets upstream
git push                       # subsequent pushes
git pull                       # fetch + merge
git fetch                      # download without merging
```

`git pull` = `git fetch` + `git merge`. **Reach for `git fetch`** when you want to inspect remote changes before integrating them; **reach for `git pull`** for the common "get me up to date" case.

#### Branching

```bash
git branch feature/login       # create branch
git checkout feature/login     # switch to branch
git checkout -b feature/login  # create + switch (shorthand)
git switch -c feature/login    # modern alternative to checkout -b
git branch -d feature/login    # delete branch (safe — prevents deleting unmerged)
git branch -D feature/login    # force delete
```

##### Branching strategies

**Feature branches:** each feature/bugfix gets its own branch off `main`. Merged back via PR. Dominant in modern trunk-based development.

**Git Flow** (simplified):

- `main` — production-ready code.
- `develop` — integration branch.
- `feature/*` — new features branch off `develop`.
- `hotfix/*` — urgent fixes branch off `main`.

**When to reach for Git Flow** — long release cycles, heavy QA gates. **When to avoid** — teams doing CI/CD with continuous deploys; feature-branch-on-`main` is simpler.

#### Merge vs. rebase

##### `git merge`

Combines branches by creating a **merge commit** that ties the two histories together. Non-destructive — original branch history is preserved.

```bash
git checkout main
git merge feature/login
```

```
A---B---C  (main)
     \       \
      D---E   M  (merge commit)
```

##### `git rebase`

Replays commits from one branch **on top of** another, creating a linear history. **Rewrites commit hashes.**

```bash
git checkout feature/login
git rebase main
```

```
A---B---C  (main)
         \
          D'---E'  (feature/login, rebased)
```

##### When to use each

| Scenario | Use |
|---|---|
| Merging a feature branch into `main` via PR | `merge` (preserves context) |
| Updating a feature branch with latest `main` | `rebase` (keeps history clean) |
| Shared/public branches | `merge` (never rebase shared branches) |
| Local-only branches | `rebase` (cleaner log) |

**Golden rule:** never rebase commits that have been pushed and shared with others. Rebasing rewrites history, and anyone with the old history will get a painful conflict when they try to pull.

#### Resolving merge conflicts

When Git can't auto-merge, it marks conflicts in the file:

```
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
```

Steps:

1. Open conflicted files; choose the correct code (or combine both).
2. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
3. `git add <file>` to mark as resolved.
4. `git commit` (or `git rebase --continue` if rebasing).

#### Useful commands

##### `git stash`

Temporarily shelves uncommitted changes — useful when you need to switch branches mid-change.

```bash
git stash                  # stash changes
git stash list             # see all stashes
git stash pop              # apply most recent and remove
git stash apply            # apply without removing
git stash drop             # discard most recent
```

##### `git cherry-pick`

Apply a specific commit from another branch onto the current branch.

```bash
git cherry-pick <commit-hash>
```

##### `git reset` vs `git revert`

| | `git reset` | `git revert` |
|---|---|---|
| **What it does** | Moves HEAD backward, discarding commits | Creates a new commit that undoes a previous one |
| **History** | Rewrites history (destructive) | Preserves history (safe) |
| **Use case** | Undo local, unpushed commits | Undo a commit that's already pushed |

```bash
git reset --soft HEAD~1    # undo commit, keep changes staged
git reset --mixed HEAD~1   # undo commit, keep changes unstaged (default)
git reset --hard HEAD~1    # undo commit, discard all changes

git revert <commit-hash>   # create a new "undo" commit
```

**Gotcha — `git reset --hard` loses work.** It deletes your uncommitted changes. Combine with `git reflog` to recover if you slipped.

##### `git reflog`

Shows a log of all HEAD movements — invaluable for recovering from accidental `reset --hard` or deleted branches.

```bash
git reflog
git checkout <lost-commit-hash>
```

#### PR / code review workflow

1. Create a feature branch from `main`.
2. Make commits with clear, descriptive messages.
3. Push the branch and open a Pull Request.
4. Reviewers comment, request changes, or approve.
5. Address feedback with **new commits** (avoid force-pushing during review — it invalidates review state).
6. Squash-merge or merge into `main`.
7. Delete the feature branch.

##### Commit message conventions

Conventional Commits format — widely adopted, friendly to auto-generated changelogs.

```
type(scope): short description

feat(auth): add JWT token refresh
fix(api): handle 404 in user endpoint
refactor(utils): extract date formatting
docs(readme): update setup instructions
```

**Common types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`.

**See also:** [`14.2 Agile and Scrum`](#10.%20Agile%20and%20Scrum%20/%20%E6%95%8F%E6%8D%B7%E4%B8%8EScrum) for how PR review fits into sprint work, [`15.1 Frontend Testing`](../../frontend/testing/frontend-testing.md) for CI test setup on PRs.
## 12. Docker Operations / Docker操作参考

#### Docker Operations

Docker is a powerful tool for managing containers, allowing you to package your applications and dependencies into a portable container that can easily be transferred and run across systems. Understanding Docker operations is crucial for developers to ensure their applications can be deployed consistently and efficiently.

##### Downloading Images from Docker Hub
- **Command:** `docker pull <image name>`
- **Example:** `docker pull redis`
- This command downloads an image from Docker Hub to your local machine. Images are pre-configured environments that contain your application and all of its dependencies.

##### Checking All Downloaded Images
- **Command:** `docker images`
- **Example:** `docker images`
- Lists all Docker images that have been downloaded or built on your machine.

##### Starting a Container from an Image
- **Command:** `docker run <image name>`
- **Example:** `docker run redis`
- This command creates a new container from a specified image and starts it. If the image is not available locally, Docker will attempt to pull it from Docker Hub.

##### Stopping a Running Container
- **Command:** `docker stop <container ID>`
- **Example:** `docker stop 8381867e8242`
- Stops a running container. You can get the container ID by using the `docker ps` command.

##### Checking the State of Running Containers
- **Command:** `docker ps`
- **Example:** `docker ps`
- Lists all currently running containers.

##### Checking the State of All Containers
- **Command:** `docker ps -a`
- **Example:** `docker ps -a`
- Lists all containers, including those that are stopped.

##### Running a Stopped Container
- **Command:** `docker start <container ID>`
- **Example:** `docker start 8381867e8242`
- Starts a previously stopped container.

##### Binding Ports to Solve Port Conflicts
- **Command:** `docker run -p <host port>:<container port> --name <defined name>`
- **Example:** `docker run -d -p 6000:6379 --name redis-new redis`
- This command maps a port on the host to a port on the container, allowing you to avoid port conflicts and access the container's services from the host.

##### Showing Logs of a Container
- **Command:** `docker logs <container ID or name>`
- **Example:** `docker logs ppppp`
- Retrieves logs from a container. Useful for debugging and monitoring container activity.

##### Naming a Container
- **Command:** `docker run --name <name> <image name>`
- **Example:** `docker run --name redis-latest redis`
- Allows you to assign a custom name to your container, making it easier to reference than the default generated ID.

##### Setting a Tag (Version) for an Image
- **Command:** `docker tag <image name>:<version name> <desired name>:<desired version name>`
- **Example:** `docker tag my-app:1.0 my-app-on-aws-cloud:1.1`
- Tags an image with a version or a name, useful for version control and organizing images.

##### Accessing a Container
- **Command:** `docker exec -it <container ID> <path>`
- **Example:** `docker exec -it cae903a74202 /bin/bash`
- Executes a command inside a running container, such as opening a bash shell. Use `exit` to leave the shell.

##### Creating a Docker Network
- **Command:** `docker network create <name>`
- **Example:** `docker network create mongo-network`
- Creates a new network, allowing containers to communicate with each other more securely and efficiently.

##### Running an Image Within a Network
- **Command:** `docker run --net <network name> <image name>`
- **Example:** `docker run --net mongo-network mongo`
- Starts a container within a specified network, facilitating communication between containers within the same network.

##### Deleting a Container
- **Command:** `docker rm <container ID>`
- **Example:** `docker rm cae903a74202`
- Removes a stopped container from your machine.

##### Deleting an Image
- **Command:** `docker rmi <Image ID>`
- **Example:** `docker rmi cae903a74202`
- Removes an image from your local machine, freeing up space.

##### Running a Container with a Named Volume
- **Command:** `docker run -v <name for data>:<container data address>`
- **Example:** `docker run -v db-data:/var/lib/mysql/data`
- Mounts a named volume at a specified path within the container. This is useful for persistent or shared data between containers.

##### Running a Container in Detached Mode
- **Command:** `docker run -d <image name>`
- **Example:** `docker run -d redis`
- This command runs the container in the background (detached mode), allowing it to run as a background process. When a container is started in detached mode, it does not block the terminal session that started it. This is particularly useful when running applications or services that should continue running without active supervision.

Running a container in detached mode is essential for services that need to run continuously, such as web servers, databases, or any application that should be accessible at all times without tying up a terminal session. It also helps in managing multiple containers efficiently, allowing developers and system administrators to start, stop, and inspect services without having to keep a terminal window open for each.

When running in detached mode, you won't see any output from the container directly in your terminal. To check on the container's logs or status, you'll need to use commands like `docker logs` for output or `docker ps` to see running containers.

This mode is particularly relevant in production environments or when deploying services on a server, where direct interaction with the container is not required for normal operation. It's also handy during development for services that don't need constant monitoring, allowing developers to focus on other tasks while the services remain available.

#### Run Docker with YAML

Docker Compose allows you to define and run multi-container Docker applications. With a YAML file, you can configure your application’s services, networks, and volumes.

##### Important Points
- **Network Creation**: There is no need to manually create a network when using a YAML file to define a series of containers. Docker Compose automatically creates a network for the services defined in the `docker-compose.yml` file, facilitating communication between containers without specifying IP addresses and ports. You can reference services by their names (e.g., `admin.xxx.@mongodb` instead of `admin.xxx.@localhost:27017`).

##### Template
```yaml
services: 
  <service-name>:
    image: <image-name>
    ports:
      - "<port-on-host>:<port-in-container>"
    environment:
      - <ENV_VAR_NAME>=<value>
```

> The top-level `version` key (e.g., `version: '3'`) is **obsolete** in Docker Compose V2 and is ignored. You can safely omit it.

##### Example
```yaml
services: 
  mongodb:
    image: mongo
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
  mongo-express:
    image: mongo-express
    ports:
      - "8080:8080"
    environment:
      - ME_CONFIG_MONGODB_ADMINUSERNAME=admin
      - ME_CONFIG_MONGODB_ADMINPASSWORD=password
```

##### How to Run This YAML
- **Start Containers**: `docker compose -f <filename> up` (e.g., `docker compose -f my_compose.yaml up`)
- **Stop Containers**: `docker compose -f <filename> down` (e.g., `docker compose -f my_compose.yaml down`)

> **`docker compose` vs `docker-compose`**: The hyphenated `docker-compose` is the standalone Python-based V1 tool (deprecated). The space-separated `docker compose` is the V2 plugin built into the Docker CLI. Use `docker compose` going forward.

#### Dockerfile

A Dockerfile is a text document that contains all the commands a user could call on the command line to assemble an image. It is often used in continuous integration pipelines, such as setting up a Jenkins pipeline.

##### Template
```dockerfile
FROM <base-image>
ENV <environment-variables>
RUN <command>
COPY . <destination-in-container>
CMD ["<entrypoint-command>"]
```

##### Example
```dockerfile
FROM node
ENV MONGO_DB_USERNAME=admin \ 
    MONGO_DB_PWD=password
RUN mkdir -p /home/app
COPY . /home/app
CMD ["node", "/home/app/server.js"]
```

##### Key Differences
- **RUN**: Executes commands in a new layer on top of the current image and commits the results. Used for installing software packages.
- **CMD**: Sets the default command to execute when the container starts. It can be overridden by providing a different command when starting the container.

#### Building an Image
- Command: `docker build -t <image-name>:<tag> .`
- Example: `docker build -t my-app:1.0 .`

#### Multi-Stage Builds

Multi-stage builds use multiple `FROM` statements to keep the final image small by separating the build environment from the runtime environment.

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

Only the final stage ends up in the image. Build tools, source code, and dev dependencies from earlier stages are discarded, resulting in significantly smaller images.

#### Use Amazon Elastic Container Registry (ECR)
- Create a repository on Amazon ECR for each image.
- Ensure AWS CLI is installed on the host.
- Use the repository URI provided by Amazon ECR to push images.

#### Docker Volumes
Docker volumes are used to persist data generated by and used by Docker containers.

##### Types of Volumes
- **Host Volumes**: Specify an explicit location on the host for the volume (`docker run -v <host-path>:<container-path>`).
- **Anonymous Volumes**: Docker automatically assigns a location on the host (`docker run -v <container-path>`).
- **Named Volumes** (Preferred): Specify a name for the volume which Docker manages (`docker run -v <volume-name>:<container-path>`). Preferred in production for ease of management.

##### Usage in Docker Compose
In `docker-compose.yml`, volumes can be declared as follows:
```yaml
volumes: 
  db-data:/var/lib/mysql/data
```
