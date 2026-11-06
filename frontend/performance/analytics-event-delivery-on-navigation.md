# 用户离开报表页时，分析事件怎样尽力发送？

案例背景：用户打开报表、改变一次筛选，然后立刻导航到别处。analytics event (分析事件) 不应拖慢筛选或导航；页面可先在内存中收集少量事件，再小批量发送，并在页面变为隐藏时尝试提交一批。这个生命周期信号只提供最后一次机会，不能保证服务器已收到。

## 先限制采集内容和积压量

先列出产品真正需要的事件名与字段。只收集允许的 `report_opened`、`filter_applied` 等事件和受控的页面代号；不要把搜索框原文、完整 URL、用户令牌或可识别身份的值塞进载荷。用户关闭可选采集时，停止入队并清空仍在应用内存中的未发送数据；已经交给 Beacon 或 Fetch 的批次可能还在途，不能由这个开关撤回。

内存队列需要上限和明示的溢出策略。下面采用最多 200 条，满时丢弃最旧条目；每 50 条或定时尝试发送一批。生产实现还应限制序列化后的字节数，因为事件条数不能代表请求体大小。`visibilitychange` 到 `hidden` 时只尝试一批，队列若仍有剩余，页面退出后可能被丢弃。发送小批次时可以先试 Beacon API，它不会等待服务器响应。

> [!example] 报表打开和筛选变化
> 页面先把 `report_opened` 和 `filter_applied` 放进内存队列。这两条尚未达到 50 条的成批门槛；若用户在 10 秒定时器触发前切换页面，文档变为 `hidden` 时处理器会将两条一起取出并尝试发送。

~~~javascript
const MAX_PENDING = 200;
const BATCH_SIZE = 50;
const allowedNames = new Set(["report_opened", "filter_applied"]);
const allowedScreens = new Set(["report_list", "report_detail"]);
const queue = [];
let collectionEnabled = false;
let flushScheduled = false;

function setCollectionEnabled(enabled) {
  collectionEnabled = enabled;
  if (!enabled) queue.length = 0;
}

function sendBatch(batch) {
  const body = new Blob([JSON.stringify(batch)], { type: "application/json" });
  // 本例假设同源端点。返回 true 仅表示浏览器已接受排队。
  if (navigator.sendBeacon?.("/analytics", body)) return;
  // Beacon 不可用或拒绝排队时尝试 Fetch；两者共享 keepalive 配额，不能保证后者绕过拒绝。
  void fetch("/analytics", { method: "POST", body, keepalive: true }).catch(() => {});
}

function trackEvent(name, screen) {
  if (!collectionEnabled || !allowedNames.has(name) || !allowedScreens.has(screen)) return;
  if (queue.length === MAX_PENDING) queue.shift();
  queue.push({ name, screen, ts: Date.now() });
  if (queue.length >= BATCH_SIZE) scheduleFlush();
}

function scheduleFlush() {
  if (flushScheduled) return;
  flushScheduled = true;
  setTimeout(() => {
    flushScheduled = false;
    flushEvents();
    if (queue.length >= BATCH_SIZE) scheduleFlush();
  }, 0);
}

function flushEvents() {
  if (!queue.length) return;
  sendBatch(queue.splice(0, BATCH_SIZE));
}

setInterval(flushEvents, 10_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushEvents();
});

setCollectionEnabled(true);
trackEvent("report_opened", "report_detail");
trackEvent("filter_applied", "report_detail");
~~~

## “已排队”不等于“已记录”

Beacon API 的 `navigator.sendBeacon()` 返回 `true` 只表示用户代理接受了传输排队；它没有响应回调，也不报告服务器是否处理。浏览器会在文档变为 `hidden` 时安排发送，但设备进程随后仍可能被系统终止。若需要自定义请求头或更细控制，可尝试 Fetch API 的 `keepalive` 请求；Beacon 和 Fetch keepalive 共用限额，一个 Fetch 组中尚未完成请求的正文总量受 64 KiB 限制，队列太大时提交可能被拒绝。若 Beacon 因这个限额被拒绝，回退到 Fetch 不能绕过限额。两个接口都不能替代可靠业务队列、服务器确认或幂等去重。

本例 `flushEvents()` 在尝试发送前从内存队列取出一批。传输失败后该批不会自动重试；这正是“尽力发送”的损失边界。若统计数据不可丢，应把它升级为持久队列并设计服务端确认与重放，而不是阻塞离页等待。

**延伸阅读：** [报表页面里的状态应该放在哪里？](../browser-apis/browser-storage-and-communication.md) 说明偏好与业务状态的归属；[流式报表断线重连后，界面怎样保留正确状态？](../browser-apis/streaming-ux.md) 说明哪些消息影响报表正确性、不能混同于可丢弃的分析事件；[WebView 怎样安全地开放原生能力并更新页面包？](../browser-apis/webview-javascript-bridge.md) 讨论混合应用中的宿主权限。

> [!info]- 来源
> - Beacon 是非阻塞的尽力传输；返回值仅表示排队成功，且无响应回调：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3，2026-11-06 核对。
> - Beacon 在页面 `visibilityState` 变为 `hidden` 时安排发送；规范也提示后台页面在移动设备上仍可能随进程终止而丢失：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3、§4，2026-11-06 核对。
> - Fetch `keepalive` 与 64 KiB 的在途请求总量限制：[WHATWG Fetch Standard，HTTP-network-or-cache fetch](https://fetch.spec.whatwg.org/)，2026-11-06 核对。
> - 页面可见性状态：[WHATWG HTML Standard，Page visibility](https://html.spec.whatwg.org/multipage/interaction.html#page-visibility)，2026-11-06 核对。
