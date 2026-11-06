# 浏览器安全控制分别保护什么信任边界？

报表页面会跨过多个不同边界。Transport Layer Security (TLS，传输层安全协议) 保护 HTTP 网络链路；Cross-Site Scripting (XSS，跨站脚本攻击) 防护避免不可信文本变成活动脚本；Cross-Site Request Forgery (CSRF，跨站请求伪造) 防护限制另一页面借用浏览器自动附带的 Cookie 发起变更；Cross-Origin Resource Sharing (CORS，跨源资源共享) 控制浏览器脚本能否读取跨源响应；Content Security Policy (CSP，内容安全策略) 的 `frame-ancestors` 限制哪些来源能嵌入页面。它们都不替代服务端认证和对报表 42 的逐次授权。

| 信任边界 | 控制主要保证什么 | 本身不保证什么 |
| --- | --- | --- |
| 网络链路 | 正确配置的 TLS 加密传输、检测篡改并认证服务端 | 登录用户身份或其可读取的报表 |
| 页面解释数据 | 按上下文输出编码和必要的标记消毒，避免数据成为活动内容 | 已执行脚本不会滥用页面已有权限 |
| Cookie 自动发送 | CSRF token 或经审查的来源校验限制伪造状态变更 | 阻止所有未授权调用 |
| 浏览器跨源读取 | 同源策略与 CORS 控制脚本能否读取响应 | 请求一定未到服务器或用户已经获授权 |
| 页面嵌入 | `frame-ancestors` 限制谁能嵌入报表界面 | 报表数据和操作的服务端权限 |

## 网络连接如何保护数据并认证服务端？

TLS 握手后为连接建立流量保护。浏览器正确验证证书链、主机名和握手时，HTTPS 可以保护传输机密性与完整性，并认证连接到预期的服务器。TLS 不说明当前浏览器用户是谁；即使浏览器验证了报表站点提供的证书，服务仍须验证会话或访问凭据，并授权读取报表 42。证书状态查询和撤销行为受客户端及部署方式影响，不应假设所有浏览器以相同步骤即时检查撤销。

## 不可信报表标题怎样安全显示？

Document Object Model (DOM，文档对象模型) 是页面结构；XSS 指不可信数据被当作活动内容执行。假设报表 42 的标题是 ` <img src=x onerror=alert(1)> `。若把它交给将值设为纯文本的 `textContent`，它仍只是字符；若拼进 `innerHTML`，浏览器会按 HyperText Markup Language (HTML，超文本标记语言) 解析。当图片加载失败且策略允许 inline handler 时，`onerror` 处理器可能执行。

1. 普通文本使用框架默认安全的文本呈现接口。只有需要将数据放入安全属性值等允许上下文时，才用对应的上下文编码。
2. 不把不可信字符串拼进执行位置，例如动态脚本正文、事件处理器代码或 CSS 选择器；这些位置不能靠一种通用转义方式修好。
3. 只有产品确实要呈现用户编写的富文本时，才使用维护良好的 HTML 消毒器过滤允许的标记和属性。
4. 避免把不可信字符串传给 `innerHTML`、`document.write`、事件属性、`eval` 或 `new Function`。框架常规自动转义不保护有意使用的 raw HTML 入口。
5. 为链接和资源 URL 验证 scheme 与目标，例如拒绝不允许的 `javascript:`；HTML 属性编码不会限制 URL 的语义。经测试的 CSP 可限制脚本来源，作为纵深防御，不能代替安全呈现。

如果 XSS 已执行，脚本通常能以页面所属 origin 发起请求并读取脚本可访问的页面数据；即使会话 Cookie 是 `HttpOnly`，恶意脚本仍可能让浏览器替用户调用报表 API。因此要修复注入点并保留服务端授权。`HttpOnly` 减少 Cookie 值被脚本直接窃取的途径，不是 XSS 防护本身。

## Cookie 自动发送时，怎样防止伪造变更？

CSRF 利用浏览器自动附带目标站点 Cookie 的行为。以下场景固定为明确可复现的条件：用户已经登录 `api.example.test`，其当前主体本来就有执行 `reports:refresh` 的权限；另一个同 site 但不可信的旧子域 `legacy.example.test` 可被攻击者控制；API 接受下方表单格式，且目前没有 token 或来源校验。host-only Cookie 仍会发给目标 API 主机；同 site 不等于同 origin。

~~~html
<form action="https://api.example.test/api/reports/42/refresh" method="post">
  <input name="range" value="365-days">
</form>
<script>document.forms[0].submit();</script>
~~~

这次跨源表单 POST 的响应不必可被攻击页面读取，副作用仍可能已经发生。例子中的两个主机使用 HTTPS 且共享可注册域 `example.test`，所以是同 site、不同 origin；若 Cookie 为 `SameSite=Lax`，同 site 的表单 POST 仍可能附带 Cookie。真正跨 site 的普通 POST 通常会被 Lax 限制，但顶层安全方法导航等仍有不同规则，不能把 `Lax` 当成授权或完整 CSRF 防护。

对 Cookie 认证的状态变更，服务端验证与当前会话绑定的 CSRF token，或使用经过审查的等价机制；适用时再校验 Origin/Referer，并用合适的 SameSite 设置纵深防御。使用 GET 等安全方法的路由不应改变状态。加上 token 后，同一请求仍可能抵达 API，但因缺少或无效 token 而被拒绝；token 让服务识别伪造来源，不证明用户操作意图。如果同源 XSS 已执行，它可能读取页面中的 token 或调用合法请求接口，因此还要修复注入并持续执行资源授权。

当某个合法流程确实需要跨 site 附带 Cookie，应设置 `SameSite=None; Secure` 并单独设计 CSRF 防护。不要为了让登录回调或嵌入工作而静默取消请求校验。

## 同源策略如何控制跨源响应读取？

浏览器将 origin 定义为协议、主机和端口。`https://console.example.test` 与 `https://api.example.test` 的 scheme 和可注册域相同，属于 same-site；主机不同，所以是不同 origin。Cookie 的 SameSite 依据 site 判定，不能与 origin 混为一谈。

以下部署变体让控制台脚本直接请求 API；浏览器已通过 `api.example.test` 的登录流程持有 API 自己设置的 host-only `__Host-api-session` Cookie。`console.example.test` 的 Cookie 不会发给 `api.example.test`；`__Host-` Cookie 也不能设置 `Domain` 扩大范围。`credentials: "include"` 允许浏览器按目标 URL、Cookie 属性和 Fetch 凭据模式附带匹配凭据，JavaScript 不读取 Cookie 值。

~~~javascript
const response = await fetch('https://api.example.test/api/reports/42', {
  credentials: 'include',
  headers: { 'X-Report-View': 'compact' },
});
~~~

`X-Report-View` 不在 CORS safelist 中，因此在无可用预检缓存的本例里，浏览器先发送不含用户凭据的预检：

~~~http
OPTIONS /api/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Access-Control-Request-Method: GET
Access-Control-Request-Headers: x-report-view
~~~

~~~http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: X-Report-View
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

预检获准后，浏览器才按 Fetch 凭据模式和 Cookie 规则发送实际 GET。这里假设 API Cookie 匹配目标 URL、已登录且请求的 SameSite 条件允许附带：

~~~http
GET /api/reports/42 HTTP/1.1
Host: api.example.test
Origin: https://console.example.test
Cookie: __Host-api-session=<opaque-session-id>
X-Report-View: compact
~~~

若请求获准读取，实际响应本身也必须带允许来源和凭据字段，脚本才能取得正文：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://console.example.test
Access-Control-Allow-Credentials: true
Vary: Origin

{"id":42,"title":"Service health","status":"ready"}
~~~

若预检通过但实际 `200` 漏掉 `Access-Control-Allow-Origin` 或 `Access-Control-Allow-Credentials`，API 仍已收到 GET 并执行处理，浏览器却不把响应暴露给脚本。按隐藏策略返回的 `404` 也必须有匹配的 CORS 响应字段，控制台脚本才可读取该错误。预检失败时浏览器不会发送实际请求；无需预检的请求则可能先到达服务器，即便脚本最后读不到响应。两种时序都要求 API 独立验证身份与权限。

CORS 是浏览器实现的读取协议，不能认证用户、授权报表、约束 curl 等非浏览器客户端，也不是一般网络防火墙。`Vary: Origin` 只让共享缓存按来源区分响应变体，不隔离不同用户的数据；私有响应还须正确设置缓存策略和用户范围。若页面与 API 可通过同一源反向代理到 `/api/`，通常可以省去跨源读取配置，但服务端授权仍需保留。

> [!info] Fetch 对 Cookie 响应字段的边界
> 浏览器脚本不能通过 Fetch/XHR 手动设置 `Cookie` 请求字段；它由浏览器依请求 URL 和 Cookie 政策管理。`Set-Cookie` 是禁止暴露给脚本的响应字段，网页不能靠读取它来取得 HttpOnly 会话值。登录 Cookie 的 host-only 范围见[会话与身份令牌](web-sessions-and-oidc.md)。

## 什么时候限制页面被嵌入？

点击劫持可将真实页面放进攻击者控制的 frame 下方，诱导用户点击错位按钮。CSP 的 `frame-ancestors` 响应指令声明哪些祖先来源可以嵌入页面；例如仅允许同源嵌入：

~~~http
Content-Security-Policy: frame-ancestors 'self'
~~~

旧客户端需要兼容时可设置 `X-Frame-Options`。允许列表应符合实际嵌入场景并在完整流程中测试。这个策略限制哪些页面能嵌入报表 UI，不替代服务端对每份报表或操作的权限判断。

WebSocket 握手也不能用 CORS 响应字段授权。浏览器会发送 Origin；服务端应按允许来源校验握手、认证连接，并对敏感消息继续授权。双向消息和断线恢复见[何时选择轮询、SSE、流式 Fetch 或 WebSocket？](../networking/real-time-web-updates.md)。

**接下来：** TLS 保护网络连接；安全输出和 CSP 降低脚本注入风险；CSRF 防护检验带 Cookie 的变更请求；CORS 决定浏览器是否暴露跨源响应；`frame-ancestors` 决定页面可由谁嵌入。所有资源读取仍须经过[服务端逐项授权](web-security-and-authentication.md)。

> [!info]- 来源
> - TLS 1.3 握手、服务器认证与流量密钥：[IETF RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html)，§2–§4，2018-08；核对于 2026-11-06。
> - Same-Origin 与 same-site 判定：[WHATWG HTML, Origins and Sites](https://html.spec.whatwg.org/multipage/browsers.html#origins)，Living Standard，核对于 2026-11-06；`example.test` 属于示例域。
> - origin、Cookie、预检、CORS、credentialed 响应及禁止脚本设置 Cookie/读取 `Set-Cookie`：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2、§3.3、§4.2、§4.10，2026-10-19 版本；核对于 2026-11-06。Cookie 属性同时见 [RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html)，§5，2011-04。
> - 安全上下文输出、HTML 消毒与危险执行上下文：[OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)，Contextual Output Encoding、HTML Sanitization、Dangerous Contexts，按 2026-11-06 版本核对。
> - CSP 的脚本纵深防御：[OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)，按 2026-11-06 版本核对；`frame-ancestors`：[W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/#directive-frame-ancestors)，2026-10-27 Working Draft，§6.4.2；该规范仍是工作草案，浏览器支持应与目标环境核验。
> - Cookie 认证请求的 CSRF token、Origin 和 SameSite 条件：[OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)，Synchronizer Token、SameSite 与 Origin Validation，按 2026-11-06 版本核对；Cookie same-site 规则：[HTTPWG RFC6265bis 草案](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html)，§5.6.7，核对于 2026-11-06。
