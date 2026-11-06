# 同一报表在多个标签页中怎样交换变化？

案例背景：用户在标签页 A 查看报表 42，在标签页 B 重新生成报表。A 需要知道自己的画面可能过时，并刷新权威数据。browsing context (浏览上下文) 能否直接通信，取决于来源、浏览器存储分区和生命周期；通知本身也不等于共享或持久化业务状态。

| 需求 | 机制 | 关键边界 |
|---|---|---|
| same-origin (同源) 且符合存储分区条件的临时广播 | `BroadcastChannel` | 消息不持久化；不在线的标签页收不到历史消息 |
| 存储一项值并通知其他文档 | `localStorage` + `storage` 事件 | 字符串写入、无事务或锁；写入者不收到自己的事件 |
| 同源上下文共享一个协调者或连接 | `SharedWorker` (共享工作线程) | worker 内存不是持久状态，需探测浏览器支持；页面关闭或进入 back-forward cache (前进/后退缓存，BFCache) 时需清理或重连端口 |
| 跨源 iframe (内嵌框架) 或窗口消息 | `postMessage()` | 固定目标 origin (来源)，并验证发送方窗口和数据结构 |
| 服务端持续更新或跨设备状态 | SSE、Fetch 流或 WebSocket | 服务端认证授权；重连与状态恢复由应用协议定义 |

在简单的同源通知中，发送报表标识和单调状态版本即可；不要把另一个标签页发来的对象当成权威记录。接收端发现版本更高时，重新请求服务端快照可以减少陈旧数据和消息缺失的影响。`BroadcastChannel` 会用 structured clone (结构化克隆) 传递消息，不保留共享对象引用，也不会替应用保存未读消息。

> [!example] 通知“报表可能更新”，再读权威状态
> A 已持有报表 42 的版本 9。B 提交更新后收到服务端版本 11、状态 `ready`，并广播一条轻量通知；本例假设版本在同一报表 ID 下单调递增。若 A 收到高于当前版本的提示，就 GET 权威快照；广播不携带快照游标，也不补发离线期间的历史。
>
> ~~~javascript
> const channel = new BroadcastChannel("reports");
> let currentVersion = 9;
>
> channel.addEventListener("message", event => {
>   const message = event.data;
>   if (!message || message.type !== "report:changed" ||
>       message.reportId !== 42 || !Number.isSafeInteger(message.version)) return;
>   if (message.version <= currentVersion) return;
>   void reloadReportFromServer(42, message.version);
> });
>
> async function reloadReportFromServer(reportId, announcedVersion) {
>   try {
>     const response = await fetch(`/api/reports/${reportId}`);
>     if (!response.ok) throw new Error("Snapshot request failed");
>     const latest = await response.json();
>     if (latest.id !== reportId || !Number.isSafeInteger(latest.version)) {
>       throw new Error("Invalid snapshot");
>     }
>     if (latest.version > currentVersion) {
>       currentVersion = latest.version;
>       renderReport(latest);
>     }
>     if (currentVersion < announcedVersion) showRefreshPending();
>   } catch {
>     // Keep the current view and show a bounded refresh error; do not retry forever.
>     if (currentVersion < announcedVersion) showRefreshUnavailable();
>   }
> }
>
> function announceChanged(reportId, version) {
>   channel.postMessage({ type: "report:changed", reportId, version });
> }
>
> // 页面所有者释放时执行；生命周期恢复时重新创建 channel。
> function disposeReportChannel() {
>   channel.close();
> }
> ~~~

若更新值本身要跨刷新保留，可写入 `localStorage` 并监听其他文档的 `storage` 事件；值发生变化时其他文档才收到通知，写入文档不收到，同一字符串重复写入也不派发事件。此机制只报告发生过某次有效变化，不协调并发写入。对于复杂协调，WHATWG HTML 建议考虑 `SharedWorker`：它可以集中管理端口、版本或一条共享连接。页面可以在 `pagehide` 尝试发送断开消息、在恢复时重新注册，但 `pagehide` 不是可靠的退出确认；崩溃或系统回收时需靠租约/心跳过期，并允许回来的页面重新注册。旧端口也应从 worker 的集合中移除并 `close()`，而不能假设平台会向另一端提供通用的 peer-close event (对端关闭事件)。

> [!example] SharedWorker 端口需要显式注销
> `SharedWorker` 可以在内存中把一个标签页的变更转给其他连接页面。正常离开时页面发 `disconnect` 并关闭自己的端口；从 BFCache 恢复时重新建立端口。以下代码只展示协作式注销与恢复，不实现心跳或租约；若页面进程直接退出，worker 仍需按上文策略清除过期连接。
>
> ~~~javascript
> // report-worker.js
> const ports = new Set();
> self.addEventListener("connect", event => {
>   const port = event.ports[0];
>   ports.add(port);
>   const dropPort = () => {
>     ports.delete(port);
>     port.close();
>   };
>   port.addEventListener("message", ({ data }) => {
>     if (data?.type === "disconnect") return dropPort();
>     for (const peer of ports) if (peer !== port) peer.postMessage(data);
>   });
>   port.addEventListener("messageerror", dropPort);
>   port.start();
> });
> ~~~
>
> ~~~javascript
> // 页面所有者维护自己的连接，并在恢复时重新注册。
> let port;
> function connectReportWorker() {
>   port = new SharedWorker("/report-worker.js").port;
>   port.onmessage = event => renderReportNotice(event.data);
> }
> connectReportWorker();
> window.addEventListener("pagehide", () => {
>   port?.postMessage({ type: "disconnect" });
>   port?.close();
>   port = null;
> });
> window.addEventListener("pageshow", event => {
>   if (event.persisted) connectReportWorker();
> });
> ~~~

跨源页面必须在 `postMessage(data, targetOrigin)` 中设置精确目标来源。接收方同时检查 `event.origin`（消息来源）和 `event.source`（发送窗口），再验证允许的消息类型、字段及大小；来源不包括路径。子页先装好监听器并向父页发 `ready`，父页再发 `refresh`，避免消息先于监听器到达。使用 `"*"` 发送敏感内容可能把消息交给已经导航到另一站点的目标窗口。信任的页面也可能因 cross-site scripting (跨站脚本攻击，XSS) 被控制，因此来源校验不能替代操作授权和载荷校验。

~~~javascript
const childOrigin = "https://reports.example";
const frame = document.querySelector("#report-frame");
window.addEventListener("message", event => {
  if (event.origin !== childOrigin || event.source !== frame.contentWindow) return;
  if (event.data?.type === "ready") {
    frame.contentWindow.postMessage({ type: "refresh", reportId: 42 }, childOrigin);
  }
});
~~~

~~~javascript
// 子页在装好监听器后向父页宣告 ready。
const parentOrigin = "https://app.example";
window.addEventListener("message", event => {
  if (event.origin !== parentOrigin || event.source !== window.parent) return;
  if (event.data?.type !== "refresh" || event.data.reportId !== 42) return;
  refreshEmbeddedReport();
});
window.parent.postMessage({ type: "ready" }, parentOrigin);
~~~

WebSocket 适合经过服务器的持续双向消息，不是两个标签页互相通知的默认方案。它的握手来源检查不等同于 Fetch 的 Cross-Origin Resource Sharing (跨源资源共享，CORS) 响应许可；服务端仍需检查握手 `Origin`、验证身份，并逐条授权敏感操作。连接建立后，WebSocket 也不会替业务消息提供去重、确认或断线补发。

**延伸阅读：** [流式报表断线重连后，界面怎样保留正确状态？](./streaming-ux.md) 对接服务器事件；[报表页面里的状态应该放在哪里？](./browser-storage-and-communication.md) 说明本地状态的寿命与事务边界。

> [!info]- 来源
> - 跨文档消息、`postMessage` 目标源、`BroadcastChannel` 与共享 worker 的适用场景：[WHATWG HTML Standard，Web Messaging](https://html.spec.whatwg.org/multipage/web-messaging.html)，§9.3–9.5，2026-11-06 核对。
> - `BroadcastChannel` 消息结构化克隆：[WHATWG HTML Standard，Structured data](https://html.spec.whatwg.org/multipage/structured-data.html)，2026-11-06 核对。
> - 存储事件只向共享存储区中的其他文档派发：[WHATWG HTML Standard，Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，§12.2.4，2026-11-06 核对。
> - WebSocket 的连接、来源和消息协议：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，2026-11-06 核对。
> - `pagehide` 的 `persisted` 值用于表示页面可能留在历史缓存并在返回时复用；它不是可靠的最终退出通知：[WHATWG HTML Standard，PageTransitionEvent](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-pagetransitionevent-interface)，2026-11-06 核对。
