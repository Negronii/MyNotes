# How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？

Graceful shutdown is an application lifecycle, not something the event loop or HTTP server performs for every dependency. On a shutdown signal, mark the instance unready and have each request handler reject work before enqueueing it; this also catches requests on already-open keep-alive connections. Then stop accepting connections, let tracked handlers and response streams finish, cancel work at the deadline, and close pools, workers, timers, and other owned resources after their users have stopped. Pass `workAbort.signal` to cancellable handlers and track accepted work so `waitForInFlightWork()` has a real completion condition.

**核心解释（中文）：** 收到关闭信号后先摘除就绪并拒绝新任务，再停止接入、等待已接收请求和后台工作排空；到期后发出协作取消并强制关闭 HTTP 连接。服务端关闭与跟踪任务都结算后，再回收它们使用的资源；即使其中一项失败，也要完成清理并报告错误，且在生命周期和清理报告结束前保留截止计时器。

**Key terms / 关键术语：** readiness / 就绪状态；in-flight work / 在途工作；graceful shutdown / 优雅关闭；deadline / 截止时间；cooperative cancellation / 协作式取消；owned resources / 应用拥有的资源。

~~~mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Draining: SIGTERM / mark unready
    Draining --> Waiting: stop accepting new connections
    Waiting --> Closed: in-flight work and server close
    Waiting --> Deadline: deadline expires
    Deadline --> Cancel: abort cooperative work
    Cancel --> ForceClose: close remaining HTTP connections
    Closed --> Cleanup: release owned resources
    ForceClose --> Cleanup
    Cleanup --> [*]
~~~

~~~javascript
const workAbort = new AbortController();
let draining = false;

function rejectWhileDraining(res) {
  if (!draining) return false;
  res.writeHead(503, { Connection: 'close' });
  res.end();
  return true;
}
// Call first in each request handler: if (rejectWhileDraining(res)) return;

async function shutdown() {
  draining = true;
  markReadiness(false);

  const deadline = setTimeout(() => {
    workAbort.abort(new Error('shutdown deadline'));
    server.closeAllConnections();
  }, 10_000);

  const serverClosed = new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  });

  try {
    const lifecycle = await Promise.allSettled([
      serverClosed,
      waitForInFlightWork(),
    ]);
    const lifecycleFailures = lifecycle.filter((result) => result.status === 'rejected');

    let cleanupFailure;
    let cleanupFailed = false;
    try {
      await closeOwnedResources();
    } catch (error) {
      cleanupFailed = true;
      cleanupFailure = error;
    }

    for (const { reason } of lifecycleFailures) {
      console.error('shutdown lifecycle failed:', reason);
      process.exitCode = 1;
    }
    if (cleanupFailed) {
      console.error('resource cleanup failed:', cleanupFailure);
      process.exitCode = 1;
    }
  } finally {
    clearTimeout(deadline);
  }
}

process.once('SIGTERM', () => {
  void shutdown().catch((error) => {
    console.error('shutdown failed:', error);
    process.exitCode = 1;
  });
});
~~~

`markReadiness`, `waitForInFlightWork`, and `closeOwnedResources` stand for application-owned health, task, and resource hooks. `waitForInFlightWork()` must settle only after tracked work has stopped using its dependencies; a rejection reports failed work, not permission to clean up while that work still runs. The referenced deadline timer stays active while `Promise.allSettled()` awaits both server close and tracked work, and the code still attempts owned-resource cleanup before reporting lifecycle or cleanup failures. Keep the timer referenced until it fires or shutdown cleanup finishes; `unref()` would allow Node to exit before its callback when no other handle keeps the event loop active. `server.close()` stops new connections and, in Node.js 26.11.1, closes idle connections while waiting for the rest. `closeAllConnections()` is the deadline's forceful HTTP(S) fallback; call it after `server.close()` as shown, and close upgraded WebSocket or HTTP/2 sessions through their own owners. The task abort is cooperative: if a handler ignores its signal or another handle keeps the process alive, the service supervisor must enforce the final hard stop. A signal listener also replaces Node's default signal exit behavior on supported POSIX systems, so the handler must complete or deliberately set a failure exit code.


**Sources / 来源：** The shutdown example and lifecycle behavior were checked against [Node.js v26.11.1 HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html) and [process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html) documentation on 2026-10-15. The timer-reference behavior uses [Node.js v26.12.1 timers](https://nodejs.org/api/timers.html), checked 2026-10-27.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) explains cancellation and ambiguous remote outcomes; [Queue delivery acknowledgements / 队列确认与重投](../reliability/queue-delivery-and-acknowledgement.md) explains why a consumer acknowledges only after its chosen durable boundary.
