# How can an analytics client reduce work and try to send events during navigation? / 分析客户端如何降低工作量并尝试在导航时发送事件？

Keep analytics off the application's critical path: collect events in a bounded in-memory queue, send small batches on a threshold or timer, and try one final batch when the document becomes hidden. This reduces per-event work and gives the client a best-effort delivery opportunity. It cannot guarantee server receipt, and pending events can be lost if the page exits. / 不要让分析采集阻塞应用关键路径：先把事件放入有界内存队列，达到阈值或定时发送小批次，并在文档转为隐藏时尝试发送最后一批。这可以减少逐事件开销，并提供尽力发送的机会；它无法保证服务器收到，页面退出时仍可能丢失未发送事件。

The limits below are example configuration, not universal recommendations. The example drops the oldest pending item when the queue is full and sends one bounded batch from the visibility-change handler.

```javascript
const MAX_PENDING = 200;
const BATCH_SIZE = 50;
const queue = [];
let flushScheduled = false;

function report(url, events) {
  const body = new Blob([JSON.stringify(events)], { type: "application/json" });
  if (navigator.sendBeacon && navigator.sendBeacon(url, body)) return;
  void fetch(url, { method: "POST", body, keepalive: true }).catch(() => {});
}

function trackEvent(event) {
  if (queue.length === MAX_PENDING) queue.shift(); // Drop the oldest item to stay bounded.
  queue.push({ event, ts: Date.now() });
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
  if (queue.length === 0) return;
  const batch = queue.splice(0, BATCH_SIZE);
  report("/analytics", batch); // Accepted for queuing is not server acknowledgement.
}

setInterval(flushEvents, 10_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushEvents();
});
```

`sendBeacon()` returns whether the browser accepted the payload for queuing. If the browser lacks Beacon or declines this payload, the code attempts a `fetch()` request with `keepalive`. Neither result confirms application-level processing or server acknowledgement. The visibility handler attempts only one batch; if the queue contains more, a later timer or scheduled threshold flush may attempt the rest, but page teardown can still discard them.

Keep the queue bound and choose an explicit overflow policy. Do not make application correctness depend on analytics delivery or block navigation while waiting for an acknowledgement.

**Specifications:** [Beacon](https://w3c.github.io/beacon/) defines the Beacon API and its queueing result; [Fetch Standard, `keepalive`](https://fetch.spec.whatwg.org/#request-keepalive-flag) defines keepalive request behavior.
