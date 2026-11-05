# Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？

These controls address different threats: TLS protects data in transit and authenticates a server; output handling prevents injected script from becoming active content; CSRF defenses protect cookie-authenticated actions; CORS controls whether browser script may read a cross-origin response; framing policy limits deceptive embedding. None substitutes for server-side authentication or authorization. / 这些控制处理不同威胁：TLS 保护传输并认证服务器；输出处理避免注入脚本成为活动内容；CSRF 防护保护使用 Cookie 凭据的操作；CORS 控制浏览器脚本能否读取跨源响应；框架策略限制欺骗性嵌入。它们都不能替代服务端身份认证或授权。

**Key terms / 关键术语：** TLS / 传输层安全；XSS / 跨站脚本；CSRF / 跨站请求伪造；CORS / 跨源资源共享；CSP / 内容安全策略；frame-ancestors / 可嵌入来源策略。

~~~mermaid
flowchart LR
    Network[Network attacker] -->|TLS| Channel[Confidential and integrity-protected channel]
    Untrusted[Untrusted output] -->|context encoding and sanitization| Page[Rendered page]
    CrossSite[Cross-site action with ambient cookie] -->|CSRF token and origin checks| StateChange[Authorized state change]
    OtherOrigin[Other origin script] -->|CORS response policy| Read[Browser may expose response]
    Frame[Deceptive framing site] -->|frame-ancestors| Embed[Allowed embedding only]
~~~

## How does HTTPS protect against man-in-the-middle attacks?

**HTTPS / TLS** protects data in transit against network eavesdropping and tampering when the connection is correctly configured and the client validates the server. In a certificate-authenticated TLS 1.3 handshake, key agreement derives traffic keys; the server's certificate and handshake signature authenticate the server's key. The server does not simply encrypt a session key with its public key as in older textbook handshake descriptions.

A client checks the certificate chain and that the certificate is valid for the requested hostname, then verifies the handshake. Certificate status and revocation handling depend on the client and deployment, so do not describe revocation checking as a universal guaranteed browser step. A trusted certificate does not authenticate the application's user; application authentication and authorization remain separate.

- **Symmetric cryptography / 对称密码** protects application traffic efficiently after handshake keys are established.
- **Public-key cryptography / 公钥密码** supports key agreement and authentication in the handshake; the TLS 1.3 suite and configuration determine the exact mechanisms.

See [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html).

---

## XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**跨站脚本 / XSS** occurs when untrusted data is interpreted as active content in a page. Script that executes in an origin can read data available to that script and make requests from that origin; an HttpOnly cookie blocks direct cookie reading but does not stop such requests.

Use the defense that matches the output context:

1. Render plain text through framework APIs that treat it as text, and encode values for their HTML, attribute, URL, JavaScript, or CSS context.
2. If user-authored rich HTML is required, sanitize it with a maintained HTML sanitizer and keep the allowed markup narrow.
3. Avoid inserting untrusted strings into `innerHTML`, `document.write`, inline event handlers, `eval`, or `new Function`. Framework escape defaults do not protect deliberate raw-HTML escape hatches.
4. Add a carefully tested Content Security Policy as defense in depth. Nonce- or hash-based strict policies can restrict script execution; an allowlist such as `script-src 'self'` alone is not a universal XSS fix.

Before assigning an untrusted value to `href` or `src`, validate the complete URL's scheme and destination against the application's policy (for example, reject `javascript:`); output encoding for the attribute does not replace URL validation.

CSP can reduce the impact of some injection paths, but it does not replace safe rendering and sanitization. See OWASP's [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) and [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) guidance.

---

## CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**跨站请求伪造 / CSRF** abuses ambient browser credentials: a site can cause a browser to send some cross-site requests, and the browser may attach cookies that match the destination. The attacker often cannot read the response, but reading it is not required to cause a state change.

For state-changing cookie-authenticated requests, use an application-validated CSRF token or an equivalent well-reviewed pattern. Check the request origin where appropriate, and use SameSite as defense in depth. Do not mutate state on safe methods such as GET. SameSite=Lax still permits some top-level safe-method navigations, and sibling subdomains can be same-site; it does not replace authorization or every CSRF defense.

**SameSite=None requires Secure.** Also account for legitimate cross-site login and embedded flows rather than silently weakening checks. See the [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

---

## What is CORS?

**跨源资源共享 / Cross-Origin Resource Sharing (CORS)** is a browser protocol that controls when a script may read a cross-origin response. It is not authentication, authorization, or a general firewall: some cross-origin requests can still be sent even when browser JavaScript cannot read the response, and non-browser clients do not enforce CORS.

For a credentialed browser request, the client must opt in to credentials and the response must name an allowed origin rather than `Access-Control-Allow-Origin: *`, with `Access-Control-Allow-Credentials: true`. Preflight requests are checked separately. Use an explicit origin allowlist; reflecting arbitrary Origin values can expose credentialed responses.

CORS does not make an endpoint private. Authenticate and authorize the server request even if the intended browser client is the only one expected to call it. See the [WHATWG Fetch Standard, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials).

---

## Clickjacking — what is it, how do you prevent it?

**点击劫持 / Clickjacking** tricks a user into interacting with a page framed beneath or inside deceptive content. Use the CSP `frame-ancestors` directive to state which sites may embed the page; use `X-Frame-Options` where legacy client support requires it. These headers control framing, not user authorization.

For example, `Content-Security-Policy: frame-ancestors 'self'` permits framing by the same origin. Set a policy that fits legitimate embedding requirements and test the application paths that must remain embeddable.

---


**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) owns TLS handshake and CORS browser mechanics; [Cross-tenant authorization / 跨租户资源授权](web-security-and-authentication.md) owns user identity and server-side permission checks.

**Sources / 来源：** [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html); OWASP [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html), and [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html); [WHATWG Fetch, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials). Security guidance checked 2026-10-15.
