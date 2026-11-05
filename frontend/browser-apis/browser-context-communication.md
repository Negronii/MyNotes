# How do browser contexts communicate? / 浏览上下文之间如何通信？

For same-origin tabs or frames that share an eligible storage partition, use `BroadcastChannel` for ephemeral messages, or `localStorage` plus the `storage` event when persisted state is useful. For windows across origins, use `postMessage` with a specific target origin, then validate the sender window, sender origin, and payload. Use a WebSocket when communication must go through a server. Browser privacy partitioning, frame lifecycle, and trust boundaries affect which contexts can communicate. / 对共享适用存储分区的同源标签页或 frame，临时消息可用 `BroadcastChannel`；需要同时保留状态时可用 `localStorage` 与 `storage` 事件。跨源窗口使用 `postMessage` 并指定目标源，接收端还要校验来源窗口、来源 origin 和消息格式。需要服务器参与时使用 WebSocket。浏览器隐私分区、frame 生命周期和信任边界都会影响通信范围。

| Need | Mechanism | Main constraint |
|---|---|---|
| Ephemeral same-origin messages | `BroadcastChannel` | Eligible contexts must share the relevant storage key; close the channel when its owner ends |
| Persisted state plus notification | `localStorage` and `storage` | The writer does not receive its own event; this is not a transaction or lock |
| Shared in-memory coordinator | `SharedWorker` | State is not durable; feature-detect and clean up disconnected ports |
| Cross-origin window/frame messages | `postMessage` | Pin `targetOrigin`; validate `event.origin`, `event.source`, and data |
| Server-mediated updates | WebSocket or another authenticated connection | Authenticate and authorize on the server; validate the handshake origin |

## Same-origin contexts / 同源上下文

A storage event is queued for other documents sharing that storage area; the document that called `setItem` does not receive its own event. Browser storage partitioning can affect which embedded contexts share an area.

~~~javascript
// Tab A listens.
window.addEventListener("storage", (event) => {
  if (event.key === "message") console.log("Received:", event.newValue);
});

// Tab B writes; Tab B does not receive the event.
localStorage.setItem("message", JSON.stringify({ text: "hello", ts: Date.now() }));
~~~

`BroadcastChannel` is purpose-built for structured-clone messages among eligible contexts and does not persist them.

~~~javascript
const channel = new BroadcastChannel("app_channel");
channel.onmessage = (event) => console.log("Received:", event.data);
channel.postMessage({ type: "update", payload: { id: 1 } });
// When this owner is finished:
channel.close();
~~~

A `SharedWorker` can coordinate connected contexts through ports. Its state lasts only as long as the worker, and a collection of ports needs a policy for removing stale entries. Use a disconnect message when a page can cooperate, then remove and close the worker's port. / SharedWorker 可以通过端口协调多个页面。状态随 worker 生命周期结束。页面能主动退出时，先发断开消息，worker 再移除并关闭对应端口。

~~~javascript
// worker.js
const ports = new Set();
self.onconnect = (event) => {
  const port = event.ports[0];
  ports.add(port);
  function dropPort() {
    ports.delete(port);
    port.close();
  }
  port.onmessage = (message) => {
    if (message.data?.type === "disconnect") {
      dropPort();
      return;
    }
    ports.forEach((other) => {
      if (other !== port) other.postMessage(message.data);
    });
  };
  port.onmessageerror = dropPort; // This example closes a port after a decode failure.
};
~~~

~~~javascript
// Page
function connect() {
  const connection = new SharedWorker("./worker.js").port;
  connection.onmessage = (event) => console.log("Received:", event.data);
  return connection;
}

let port = connect();
window.addEventListener("pagehide", () => {
  port.postMessage({ type: "disconnect" });
  port.close();
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) port = connect();
});
~~~

`pagehide` is best effort. For abrupt tab exits, expire connections after a bounded period without a reply, and let a resumed client register again. The HTML standard defines `close()` and the `messageerror` event for a deserialization failure. It provides no portable peer-close notification for this cleanup. [HTML Standard on MessagePort and broadcast cleanup](https://html.spec.whatwg.org/multipage/web-messaging.html#broadcasting-to-many-ports)

## Cross-origin windows / 跨源窗口

The sender chooses a precise target origin; the receiver checks both origin and the expected window before interpreting the structured-clone payload.

~~~javascript
const iframe = document.getElementById("myIframe");

// Parent → iframe
iframe.contentWindow.postMessage({ action: "update" }, "https://child-origin.example");

// Iframe → parent
window.parent.postMessage({ status: "ready" }, "https://parent-origin.example");

// Receiver inside the iframe. On the parent, compare source with iframe.contentWindow.
const expectedOrigin = "https://parent-origin.example";
const expectedWindow = window.parent;
window.addEventListener("message", (event) => {
  if (event.origin !== expectedOrigin || event.source !== expectedWindow) return;
  if (!event.data || typeof event.data !== "object" ||
      typeof event.data.action !== "string") return;
  handleAction(event.data.action);
});
~~~

Avoid `"*"` for confidential messages: a target window may navigate before delivery. An origin check alone is not enough; a trusted page can be compromised, so validate the message schema and allowed operations. The payload is structured-cloned, not a shared object reference.

A WebSocket is for a server-mediated, persistent bidirectional channel, not a default workaround for two tabs with different origins. The WebSocket protocol is not CORS; validate the handshake's `Origin` and authenticate and authorize each connection on the server. See [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md).

**See also:** [Where should browser state live: Web Storage or cookies?](./browser-storage-and-communication.md) covers storage lifetime and races.

**Standards / 规范：** [WHATWG HTML: cross-document messaging and BroadcastChannel](https://html.spec.whatwg.org/multipage/web-messaging.html); [WHATWG Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html); [WHATWG WebSockets](https://websockets.spec.whatwg.org/); checked 2026-11-05.
