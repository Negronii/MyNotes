# Where should browser state live: Web Storage or cookies? / 浏览器状态应放在哪里：Web Storage 还是 Cookie？

Use Web Storage when page JavaScript explicitly reads same-origin client state; use cookies when a matching request should carry a small value to a server, such as a session identifier. The choice depends on lifetime, request behavior, size, browser policy, and threat model. Web Storage is synchronous and has no multi-key transaction; cookies are sent according to domain, path, secure-transport, SameSite, and credentials rules. / 页面脚本显式读取同源客户端状态时可选 Web Storage；需要随符合条件的请求发送小型数据（例如会话标识）时可选 Cookie。应根据生命周期、请求行为、容量、浏览器策略和威胁模型选择。Web Storage 为同步接口且没有多键事务；Cookie 是否发送取决于域、路径、安全传输、SameSite 与凭证规则。

| Feature | `localStorage` | `sessionStorage` | Cookies |
|---|---|---|---|
| Scope | Origin storage area; privacy policy may partition or restrict embedded contexts | Origin plus top-level browsing context | Domain/path and cookie policy |
| Lifetime | Persists until removed or evicted; no per-entry expiry API | Usually the top-level context's session; restoration is user-agent dependent | Session or `Expires`/`Max-Age` |
| Request behavior | Not attached automatically | Not attached automatically | Matching cookies may be attached subject to policy and request credentials |
| JavaScript access | Readable by page scripts | Readable by page scripts | Readable through `document.cookie` unless `HttpOnly` |
| Typical fit | Preferences or small client state | Temporary per-tab or wizard state | Server-managed sessions when designed for cookie authentication |

`localStorage` and `sessionStorage` expose synchronous string key/value operations. `localStorage` usually persists until cleared or evicted; it has no per-entry expiry API. `sessionStorage` survives reloads and same-tab navigation and is cleared when that top-level browsing context's session ends, though session restoration is user-agent dependent. A newly opened tab normally has a separate area; an auxiliary context opened by a page may begin with a copy of its opener's session storage, after which the two diverge. The Storage Standard recommends 5 MiB for each endpoint, but this is not a guarantee of usable space: browser mode, policy, and storage pressure matter. For larger structured data or atomic updates, use IndexedDB and handle quota/access errors. `navigator.storage.estimate()` reports approximate usage and quota; best-effort data may be evicted.

The storage key is based on origin, while privacy behavior can further partition or gate embedded third-party storage. Do not assume an embedded page shares the same storage view it receives as a top-level page. Web Storage has no cross-tab lock or multi-key transaction: a read-modify-write can race, and another document's `storage` event is a notification after a write, not an atomicity mechanism. Use IndexedDB transactions or explicit coordination when updates must be atomic; see [How do browser contexts communicate?](./browser-context-communication.md).

Any script running in the page can read Web Storage, so XSS can expose stored bearer tokens. `HttpOnly` keeps a cookie value out of page JavaScript; cookies still introduce CSRF and cross-site policy concerns. `SameSite` can reduce some CSRF exposure but is not a complete defense, and `SameSite=None` requires `Secure` under current cookie rules. Choose a complete session design rather than treating either storage type as a security fix.

**See also:** [Web Security and Authentication / Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) covers XSS, CSRF, and cookie flags; [How does a native app expose capabilities to WebView JavaScript?](./webview-javascript-bridge.md) covers privileged hybrid-app interfaces.

**Standards / 规范：** [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html); [WHATWG Storage Standard](https://storage.spec.whatwg.org/); [IETF HTTP cookie draft](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/); [MDN storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), checked 2026-11-05.
