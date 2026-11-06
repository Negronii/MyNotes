# Node.js 服务如何排空并关闭？

**案例：** 报表 API 正在读取数据库并写流式响应时收到 SIGTERM。优雅关闭（graceful shutdown）的关键是按所有权顺序收拢工作：先停止对外宣称 readiness（就绪状态）并拒绝新任务，再停止接收连接，等待现有请求和后台工作不再使用依赖，最后关闭连接池、后台工作线程或进程和其他资源。deadline（截止时间）到达时发出协作取消；只有可观察的完成条件才能证明任务已经停下。

~~~mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Draining: SIGTERM / 摘除就绪并拒绝新任务
    Draining --> Waiting: 停止接收连接
    Waiting --> Cleanup: 在途工作与 HTTP 服务都已结束
    Waiting --> Deadline: 截止时间到
    Deadline --> Cancel: 发出协作取消
    Cancel --> ForceClose: 关闭剩余 HTTP 连接
    ForceClose --> Waiting: 等工作退出其依赖
    Cleanup --> Closed: 关闭池、worker 与其他资源
    Closed --> [*]
~~~

这里的排空不是 HTTP Server 自动替应用完成的事。request handler、后台任务、响应流和任务专用游标都要登记到各自拥有者，关闭程序才能知道它们何时不再使用依赖。

## 为什么要先拒绝工作再关闭连接？

先将实例标为不就绪，负载均衡器就有机会停止把新连接路由到它；但健康状态的传播有延迟，因此 handler 也要在入队或开始副作用前检查 draining 状态。对已经打开的 keep-alive 连接，新请求可能仍会到达，handler 应返回带 Connection: close 的 503 并且不要受理任务。随后调用 server.close() 停止接入；它的回调表示 HTTP 连接和响应已收尾。应用拥有的后台工作由单独的 inFlight 集合跟踪并等待，不能把这两个完成条件混为一谈。

下面是可以直接运行的最小服务。它用一个可取消的计时操作代替数据库报表任务，跟踪这项工作，并演示：1 秒截止到达时向它发出取消、关闭剩余 HTTP 连接，然后等待实际工作结束才清资源。这个截止只约束本例可取消的 timer 与 HTTP 连接；不响应取消的 handler 仍会让 inFlight 等待继续。真实服务要把 readiness、任务跟踪和资源清理接到自己的 health、worker 及连接池实现上，并由进程 supervisor 提供最终硬截止。

> [!example]- 可运行的关停示例
>
> ~~~javascript
> // 保存为 shutdown-demo.cjs；使用 Node.js v26.11.1 运行
> const http = require('node:http');
> const { setTimeout: sleep } = require('node:timers/promises');
>
> const workAbort = new AbortController();
> const inFlight = new Set();
> let draining = false;
>
> function trackWork(promise) {
>   inFlight.add(promise);
>   promise.then(
>     () => inFlight.delete(promise),
>     () => inFlight.delete(promise),
>   );
>   return promise;
> }
>
> async function createReport(signal) {
>   await sleep(5_000, undefined, { signal });
>   return 'report ready';
> }
>
> async function waitForInFlightWork() {
>   while (inFlight.size > 0) {
>     await Promise.allSettled([...inFlight]);
>   }
> }
>
> const server = http.createServer(async (request, response) => {
>   if (draining) {
>     response.writeHead(503, { Connection: 'close' });
>     response.end('draining');
>     return;
>   }
>
>   try {
>     const report = await trackWork(createReport(workAbort.signal));
>     response.end(report);
>   } catch (error) {
>     if (!response.destroyed) {
>       response.writeHead(503);
>       response.end('report stopped');
>     }
>   }
> });
>
> server.listen(8000);
>
> function markReadiness(ready) {
>   console.log('ready:', ready);
> }
>
> async function closeOwnedResources() {
>   // 生产服务在这里关闭数据库池、worker、定时任务和应用拥有的句柄。
>   console.log('resource cleanup complete');
> }
>
> async function shutdown() {
>   draining = true;
>   markReadiness(false);
>
>   const deadline = setTimeout(() => {
>     workAbort.abort(new Error('shutdown deadline'));
>     server.closeAllConnections();
>   }, 1_000);
>
>   const serverClosed = new Promise((resolve, reject) => {
>     server.close(error => error ? reject(error) : resolve());
>   });
>
>   try {
>     const lifecycle = await Promise.allSettled([
>       serverClosed,
>       waitForInFlightWork(),
>     ]);
>     const lifecycleFailures = lifecycle.filter(result => result.status === 'rejected');
>
>     let cleanupFailure;
>     let cleanupFailed = false;
>     try {
>       await closeOwnedResources();
>     } catch (error) {
>       cleanupFailed = true;
>       cleanupFailure = error;
>     }
>
>     for (const result of lifecycleFailures) {
>       console.error('shutdown lifecycle failed:', result.reason);
>       process.exitCode = 1;
>     }
>     if (cleanupFailed) {
>       console.error('resource cleanup failed:', cleanupFailure);
>       process.exitCode = 1;
>     }
>   } finally {
>     clearTimeout(deadline);
>   }
> }
>
> process.once('SIGTERM', () => {
>   void shutdown().catch(error => {
>     console.error('shutdown failed:', error);
>     process.exitCode = 1;
>   });
> });
> ~~~

服务在收到信号后先把 draining 设为 true，再启动 deadline。该截止计时器必须保持引用：若用 unref()，当其他句柄不再阻止退出时，Node 可能在 deadline 回调执行前退出。Node.js 19 及以后，server.close() 会关闭空闲连接并等待活动连接；超时时调用 closeAllConnections() 是强制关闭 HTTP(S) 连接，且应该在 close() 之后调用以避免连接竞态。它不会关闭升级后的 WebSocket 或 HTTP/2 会话，这些要由各自的所有者处理。注册 SIGTERM listener 会接管该信号的默认退出路径，所以 handler 必须完成清理，或明确设置失败退出码。

本例监听 SIGTERM，适合显式向进程发送该信号的部署。PM2 对 stop、restart、reload 默认先发 SIGINT；运行在 PM2 下时也要处理 SIGINT，或把 `PM2_KILL_SIGNAL` 配成 SIGTERM。PM2 的 `kill_timeout` 到期后会发 SIGKILL，因此优雅关闭预算必须短于该上限或同步调整管理器配置。

本例的可取消 timer 会在 deadline 到达时停止，因此 tracked work 随后结束，才允许关闭其资源。`server.close()` 回调和 inFlight Promise 集合分别代表 HTTP 收尾与应用工作收尾；即使 HTTP 连接已被强制关闭，handler 仍可能占用数据库连接。对不支持取消的数据库查询、忽略信号的 handler 或已经启动的远端副作用，取消只是通知，并不会强制中止它们；waitForInFlightWork 必须等到它们确实不再使用依赖。若服务超过上层硬截止时间仍未退出，应由进程 supervisor 最终终止，而不能提前关闭仍在使用的资源。HTTP 任务与持久后台 job 的取消边界不同：连接断开不自动撤销已持久接受的账户报表，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

**本机重放：** Node.js v26.11.1 上启动此脚本，发起一个尚未完成的请求后发送 SIGTERM；deadline 触发取消，输出 ready: false 与 resource cleanup complete，进程以成功状态结束。若 handler 忽略 signal，该清理次序会继续等待它，而不会提前关闭连接池。

> [!info]- 来源
> - HTTP server.close()、closeAllConnections()、空闲连接和协议升级连接边界：[Node.js v26.11.1, HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html)，核对于 2026-11-06。
> - SIGTERM handler 替代默认退出行为及信号行为：[Node.js v26.11.1, process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html)，核对于 2026-11-06。
> - PM2 stop/restart/reload 的默认 SIGINT、可配置的 kill signal 和最终 SIGKILL 截止：[PM2, Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)，核对于 2026-11-06。
> - 定时器 unref() 与事件循环存活：[Node.js v26.11.1, Timers](https://nodejs.org/download/release/v26.11.1/docs/api/timers.html)，核对于 2026-11-06。
> - AbortSignal 对 Promise 定时器的协作取消：[Node.js v26.11.1, Timers Promises API](https://nodejs.org/download/release/v26.11.1/docs/api/timers.html#timers-promises-api)，本例按上述时序重放。
