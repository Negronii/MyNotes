**Browser Storage and Communication / 浏览器存储与通信**

Browser storage is scoped by origin and browsing context, subject to browser quota and privacy policy. Cookies can accompany matching requests; Web Storage does not. 浏览器存储受源、浏览上下文、配额和隐私策略约束；只有符合条件的 Cookie 会随请求发送。

# What's the difference between `localStorage`, `sessionStorage`, and cookies?

**Headline (30s):** `localStorage` and `sessionStorage` are synchronous, origin-scoped key/value stores that scripts read explicitly. Cookies have domain, path, and cross-site sending rules, and matching cookies can be attached to requests. `localStorage` usually outlives a page session; `sessionStorage` is tied to a top-level browsing context. Choose from the data's lifetime, reader, and threat model. **中文：** Web Storage 由脚本显式读取；符合域、路径及跨站策略的 Cookie 会随请求发送。应按数据生命周期、读取方和威胁模型选择。

**Why interviewers ask this:** This comes up in any question about auth flows, session management, or persistence. Candidates who conflate the three write insecure auth code.

## `localStorage`

- **Scope:** the origin's storage area; third-party contexts may be further partitioned or restricted by browser privacy policy.
- **Capacity:** the Storage Standard recommends a 5 MiB quota for the `localStorage` endpoint; actual availability can vary with user-agent policy and browser mode.
- **Lifetime:** persists until cleared or evicted; there is no per-entry expiration API.
- **Access:** synchronous string key/value operations, initiated by script; values are not automatically attached to HTTP requests.
- **Use for:** user preferences (theme, language), cached client state, offline data.

## `sessionStorage`

Same API, scoped to an origin and a top-level browsing context. A new tab normally has its own area; an auxiliary window opened by a page can start with a copy of the opener's session storage, after which the two diverge.

- **Capacity:** the Storage Standard recommends a 5 MiB quota for the `sessionStorage` endpoint; actual availability can vary with user-agent policy and browser mode.
- **Lifetime:** survives reloads and same-tab navigation; cleared when the top-level browsing context's session ends (session restoration is user-agent-dependent).
- **Access:** synchronous string key/value operations; it does not automatically attach values to requests.
- **Use for:** multi-step form state, wizard progress, temporary SPA state.

## Cookies

- **Capacity:** small per-cookie and per-site limits apply; exact usable limits vary by browser, so do not rely on a fixed cookie count or byte capacity.
- **Lifetime:** `Expires` / `Max-Age` set persistence; a session cookie normally ends with the browser session, whose restoration behavior varies.
- **Access:** a matching cookie may be sent with a request according to `Domain`, `Path`, `Secure`, `SameSite`, and the request's credentials policy. Script can read non-`HttpOnly` cookies through `document.cookie`.
- **Security attributes:** `HttpOnly` hides a cookie from non-HTTP APIs such as `document.cookie`; `Secure` restricts it to secure transport; `SameSite=Strict|Lax|None` controls cross-site sending. `SameSite` can reduce some CSRF exposure but is not a complete CSRF defense; `SameSite=None` requires `Secure` in current cookie rules.
- **Use for:** server-managed session identifiers when the application is designed around cookie authentication. Add CSRF defenses suited to the request flow.

## Quick comparison

| Feature | `localStorage` | `sessionStorage` | Cookies |
|---|---|---|---|
| Scope | Origin storage area, subject to browser privacy policy | Origin + top-level browsing context | Domain/path and cookie policy |
| Capacity | Storage Standard recommends 5 MiB per endpoint; actual availability is browser-policy dependent | Storage Standard recommends 5 MiB per endpoint; actual availability is browser-policy dependent | Small; browser limits vary |
| Sent with requests | No automatic attachment | No automatic attachment | Matching cookies may be attached, subject to request and cookie policy |
| Lifetime | Persists until removed or evicted | Browsing-context session | Session or configured expiration |
| Server access | Only if page code sends it | Only if page code sends it | Yes, when the cookie is included |
| Accessible to JS | Yes | Yes | Unless `HttpOnly` |

**Security trade-off:** Any script running in the page can read Web Storage, so an XSS flaw can expose stored bearer tokens. `HttpOnly` cookies keep the cookie value out of page JavaScript, but cookies introduce request-forgery and cross-site policy concerns. Choose the session design deliberately; neither storage choice fixes XSS.

## Quotas, partitioning, and coordination / 配额、分区与协调

The Storage Standard recommends 5 MiB quotas for the `localStorage` and `sessionStorage` endpoints. A recommended endpoint quota is not a guarantee of usable space in every browser mode: user-agent policy can restrict or disable access, and larger storage APIs use implementation-defined quotas. `navigator.storage.estimate()` reports approximate usage and quota; best-effort storage can be evicted under pressure. Use IndexedDB for larger structured data or transactions, and handle quota and access errors.

The standard's baseline storage key is the origin, while browser privacy behavior can further partition or gate storage in embedded third-party contexts. Do not assume an embedded site shares the same storage it sees when opened as a top-level page; this is browser- and policy-dependent.

Web Storage has no multi-key transaction or cross-tab lock. A read-modify-write sequence can race across tabs, and the `storage` event is a notification after a change, not a lock. Use IndexedDB transactions or an explicit coordination mechanism when updates must be atomic.

**See also:** [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for XSS/CSRF mitigation and cookie flag deep dives.

---

# `HTMLCollection` vs. `NodeList` — what's the difference?

**Headline (30s):** Both are array-like collections of DOM nodes, but differ in what they contain and how they update. **`HTMLCollection`** holds only `Element` nodes and is live — it reflects matching DOM changes. **`NodeList`** can hold any node type (Elements, Text, Comments); whether it is live depends on the API that returned it (`querySelectorAll` is static, while `childNodes` is live).

## `HTMLCollection`

- Returned by `getElementsByClassName`, `getElementsByTagName`, `.children`.
- Contains only `Element` nodes.
- Live — its items reflect changes to the underlying tree; this does not promise that an engine reruns a query on every property access.

## `NodeList`

- Returned by `querySelectorAll` (static), `childNodes` (live).
- Can contain any node type: `Element`, `Text`, `Comment`.
- Its liveness depends on the API that returned it.

## `.children` vs `.childNodes`

```html
<p id="p1">
  <em>hello</em> world <b>bold</b><!-- comment -->
</p>
```

- `p.children` → `HTMLCollection`: `[<em>, <b>]` — elements only.
- `p.childNodes` → `NodeList`: `[<em>, " world ", <b>, <!-- comment -->]` — everything.

**Gotcha — mutating while iterating a live collection:** Removing elements from a live `HTMLCollection` during a `for` loop makes the indexes shift underneath you. Either iterate backwards, or convert to an array first (`Array.from(collection)`).

**Rule of thumb:** Reach for `querySelectorAll` by default — the static snapshot is easier to reason about. Fall back to `getElementsByClassName` when you explicitly need live updates.

---

# How can tabs of the same origin communicate?

**Headline (30s):** Four common options. For eligible same-origin contexts, **`BroadcastChannel`** is often the simplest. `localStorage` + `storage` is a broadly available persistence-backed workaround; `SharedWorker` can share in-memory state but should be feature-detected. Use `WebSocket` for server-mediated updates, not simply because two contexts have different origins.

## 1. `localStorage` + `storage` event

Writing to `localStorage` queues a `storage` event for other documents that share that storage area; the document making the change does not receive its own event. Privacy partitioning can affect which embedded documents share an area.

```javascript
// Tab A listens
window.addEventListener('storage', (e) => {
  if (e.key === 'message') console.log('Received:', e.newValue);
});

// Tab B sends
localStorage.setItem('message', JSON.stringify({ text: 'hello', ts: Date.now() }));
```

**Gotcha — the writer gets no event:** The document that called `setItem` does not receive its own event. This is cross-document notification, not a same-document event bus.

## 2. `BroadcastChannel` API

Purpose-built for messaging among eligible same-origin contexts, subject to the browser's storage partition and privacy rules. It transmits structured-clone data without persisting it.

```javascript
const channel = new BroadcastChannel('app_channel');

// Listen
channel.onmessage = (e) => console.log('Received:', e.data);

// Send
channel.postMessage({ type: 'update', payload: { id: 1 } });
```

Feature-detect it for the target browsers. Close the channel when its owner is done.

## 3. `SharedWorker`

A worker instance shared by connected same-origin contexts can hold in-memory state while clients remain connected. It is not durable storage; feature-detect it where browser coverage matters.

```javascript
// worker.js
const ports = new Set();
onconnect = (e) => {
  const port = e.ports[0];
  ports.add(port);
  port.onmessage = (msg) => {
    // broadcast to all other tabs
    ports.forEach(p => { if (p !== port) p.postMessage(msg.data); });
  };
};
```

Do not treat a shared worker as a durable store or assume it survives after every client disconnects.
This small broadcast sketch omits port cleanup; a real worker needs an explicit client-disconnect and stale-port policy.

## 4. WebSockets for server-mediated updates

Use WebSocket when the application needs a persistent, bidirectional connection to a server. A difference in origin alone does not make it the only or default channel between contexts. The WebSocket protocol is not CORS: validate the handshake `Origin` and authenticate and authorize each connection on the server.

**Rule of thumb:** Ephemeral same-origin messages → `BroadcastChannel`; persist-and-notify use cases → `localStorage` plus `storage`; cross-origin frame messaging → `postMessage` with origin checks; server-mediated updates → WebSocket or another authenticated server channel.

---

# How do you communicate with an iframe?

**Headline (30s):** Use `window.postMessage(data, targetOrigin)` for window-to-window messaging across origins. The parent calls `iframe.contentWindow.postMessage(...)`; the iframe calls `window.parent.postMessage(...)`. Both sides listen for `message`, check `event.origin` and the expected `event.source`, and validate the message shape. **中文：** 跨源窗口通信可用 `postMessage`；接收方必须核验来源、窗口和数据格式。

```javascript
// Parent → iframe
const iframe = document.getElementById('myIframe');
iframe.contentWindow.postMessage(
  { action: 'update' },
  'https://child-origin.com'
);

// Iframe → parent
window.parent.postMessage(
  { status: 'ready' },
  'https://parent-origin.com'
);

// Receiving inside the iframe; on the parent page compare against iframe.contentWindow.
const expectedOrigin = 'https://parent-origin.com';
const expectedWindow = window.parent;
window.addEventListener('message', (e) => {
  if (e.origin !== expectedOrigin || e.source !== expectedWindow) return;
  if (!e.data || typeof e.data !== 'object' || typeof e.data.action !== 'string') return;
  console.log('Received:', e.data);
});
```

**Gotcha — avoid `'*'` for confidential messages:** A wildcard can deliver to a window after it has navigated to another origin. Specify the expected scheme, host, and port.

**Gotcha — origin checks do not validate data:** A trusted origin can still be compromised. Parse and validate the message before acting on it; `postMessage` payloads use structured cloning, not shared object references.

---

# What's a JS-Bridge, and how does it work?

**Headline (30s):** A JS-Bridge is a communication layer between native mobile code and JavaScript running inside a `WebView`. Web content is sandboxed and can't call native APIs directly, so the bridge routes calls through one of two mechanisms: **URL-scheme hijacking** (the iframe-src trick) or **global API injection** (the native app exposes functions on `window`). Modern apps usually use global injection for sync calls and URL schemes for legacy support.

## URL scheme method

The native app registers a custom scheme (e.g., `myapp://`). The web side loads a URL matching that scheme in a hidden iframe, which the native app intercepts before it actually navigates.

```javascript
const bridge = {
  invoke(path, data, onSuccess, onError) {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = `myapp://${path}?data=${encodeURIComponent(JSON.stringify(data))}`;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 100);
  },
  getLocation(onSuccess, onError) {
    this.invoke('api/location', {}, onSuccess, onError);
  }
};
```

**Limitation:** URL length caps, no direct response — callbacks must be stored by ID and invoked by the native side.

## Global API injection

The native side evaluates JavaScript into the WebView to expose functions on `window`:

```javascript
// Native injects window.NativeBridge beforehand
const version = window.NativeBridge.getVersion();
window.NativeBridge.requestLocation((loc) => console.log(loc));
```

Feels like normal JS — synchronous or callback-based depending on what the native side supports.

**Reach for it when:** building a hybrid app (WebView + native shell). For pure web, use standard browser APIs (`navigator.geolocation`, etc.).

**Gotcha — security:** Treat bridge calls as privileged input. Restrict which frames and origins can reach the bridge, validate each operation and argument natively, and avoid exposing capabilities to arbitrary page content.

**See also:** [`1.1 Browser Basics`](../browser/browser-basics.md) for where storage and messaging fit into the browser architecture, [`8.2 Web Security and Authentication`](../../engineering-foundations/security/web-security-and-authentication.md) for auth storage and CSRF concerns.

**Standards and current guidance / 标准与文档：** [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html), [WHATWG Storage Standard](https://storage.spec.whatwg.org/), [WHATWG DOM collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection), [MDN storage quotas and eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), [WHATWG cross-document messaging and BroadcastChannel](https://html.spec.whatwg.org/multipage/web-messaging.html), [WHATWG WebSockets](https://websockets.spec.whatwg.org/), [IETF cookies draft (work in progress)](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/).
