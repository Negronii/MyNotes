# Node.js 如何在事件循环、工作线程与进程之间调度工作？

**案例：** API 收到导出 acct-17 报表的请求：先用数据库网络连接取数据，再压缩输出；同一服务还要接其他用户请求。异步 I/O 能让线程在等待数据库或网络时处理别的工作，不能让一段长时间的 JavaScript 汇总循环自己让路。遇到 CPU 阻塞时才考虑工作线程；需要独立内存或故障边界时考虑进程。

~~~mermaid
flowchart TD
    Request[API 请求] --> Main[主进程中的 JavaScript isolate]
    Main -->|等待网络 I/O| Kernel[操作系统 I/O]
    Main -->|所选 API 的后台工作| Pool[libuv 工作线程池]
    Main -->|CPU 密集型 JavaScript| Worker[有界 worker_threads 池]
    Main -->|隔离或独立生命周期| Child[子进程]
    Child -->|多进程 HTTP 入口| Cluster[cluster：多个 Node 进程]
    Worker --> Main
    Pool --> Main
    Main --> Queue[限制任务数与等待队列]
~~~

## 默认的 JavaScript 执行路径是什么？

Node.js 进程中的每个 JavaScript isolate（隔离环境）有自己的 JavaScript 执行线程和事件循环。主线程运行请求处理器；异步操作完成后，回调再回到相应 isolate 的事件循环执行。一个长同步 JSON 变换会占住主线程，延迟这个进程里其他请求的回调。异步并不等于“所有工作都交给另一个线程”；worker thread（工作线程）指 Node 的工作线程 API，和 cluster 启动的工作进程不同。

网络 I/O 通常由操作系统异步机制推进；libuv（Node.js 使用的跨平台异步 I/O 库）协调部分后台工作。Node.js v26.11.1 文档说明，回调式与 Promise 式文件系统 API（fs.FSWatcher 除外）使用 libuv 工作线程池，部分加密和压缩 API 也使用该池，完成后的 JavaScript 回调仍回到事件循环。具体 API 的实现契约不同，因此不要把“异步”直接等同于“线程池”。例如，适合大量等待的场景优先使用 Node 的异步 I/O；worker_threads 主要解决 CPU 密集型 JavaScript，并不替代高效 I/O。

## 该把计算放在哪种执行资源上？

| 选择 | 适合报表服务的情况 | 隔离和共享边界 |
| --- | --- | --- |
| 主事件循环上的异步 API | 等数据库、网络或异步文件操作 | 等待不占住 JS 调用栈；同步计算仍会阻塞当前 isolate |
| worker_threads | 大块 CPU 密集型 JavaScript，且能按任务切分 | worker 有独立 isolate 和堆；可发消息、转移 ArrayBuffer 或共享 SharedArrayBuffer，共享时要用 Atomics 等同步 |
| child_process | 工作有独立地址空间、可独立重启或需要更强故障隔离 | 使用 IPC（进程间通信）等显式通信；内存不与父进程自动共享；默认以相同 OS 用户运行，可访问该用户获准的文件和网络，不是安全沙箱 |
| cluster | 在同一机器上用多个 Node 进程提供 HTTP 服务 | 每个 worker 是进程；进程内会话或缓存不自动共享，退出和重启要由应用或进程管理器处理 |

不要为每个小请求新建一个线程或进程。重复计算应交给有界 worker 池，并限制等待队列；否则只是把事件循环前的无界等待移到 worker 前。进程选择也要计入消息传输、启动时间、独立连接池和每进程内存。操作系统层面的比较见[何时选线程、进程或异步 I/O？](../operating-systems/processes-threads-and-concurrency.md)；具体槽位与连接预算见[如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md)。

若报表只是等待数据库，直接使用异步数据库驱动，额外线程只会增加调度和连接管理成本。若从已取回的数据计算摘要会持续占用主事件循环，就交给有界 worker 池。若扩展可能崩溃或需要独立生命周期，可用子进程隔开地址空间和故障生命周期；子进程不会自动隔离文件、网络或其他操作系统权限。运行不可信代码还需要真实的操作系统权限隔离，本章不实现这部分。cluster 是让多进程接受 HTTP 连接的一种部署方式，不保证吞吐量线性增长；数据库、内存和磁盘也仍是共享的机器资源。

## 子进程怎样接收一个计算任务？

下面的 CommonJS 示例用 fork() 启动同一文件作为子进程，通过 IPC 发送 Fibonacci 输入并取回结果。它展示进程边界，不是生产任务队列：没有排队上限、重复任务保护或 supervisor 级别的重启策略。

~~~javascript
// 保存为 report-child.cjs；使用 Node.js v26.11.1 运行
const { fork } = require('node:child_process');

function fib(n) {
  let a = 0;
  let b = 1;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    process.send({ result: fib(n) });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.once('error', error => {
    console.error(error);
    process.exitCode = 1;
  });
  child.once('message', ({ result }) => {
    console.log(result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

输出 55。使用真实 CPU 计算时，应该复用有界进程或 worker 池，而不是每个报表都启动一个新进程。

cluster 让多个 Node 子进程监听同一服务端口。下面延续同一报表服务，重点是每个 worker 的进程隔离；若把会话或进程内缓存放在这些 worker 里，请求落到另一个 worker 时就看不到同一份状态。

~~~javascript
// 保存为 cluster-report.cjs；使用 Node.js v26.11.1 运行
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

if (cluster.isPrimary) {
  for (let i = 0; i < availableParallelism(); i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end('report API');
  }).listen(8000);
}
~~~

该服务要用外部状态存储、明确的连接路由或消息机制解决跨进程状态共享。任何多进程部署还需要健康检查、滚动退出和重启策略；怎样排空 Node HTTP 请求见[Node.js 服务如何排空并关闭？](node-service-shutdown.md)。

若使用 PM2 管理集群，可用 pm2 start app.js --name api -i max 启动、pm2 list 或 pm2 monit 观察、pm2 reload api 请求滚动重载。PM2 对 stop、restart、reload 默认先发送 SIGINT，等待 `kill_timeout`（默认 1600 ms）后仍未退出就发 SIGKILL；可用 `PM2_KILL_SIGNAL` 改信号。reload 超时也可能退化为 restart。应用应处理部署实际发来的信号并在强杀前完成排空；用户态会话也不能默认留在单进程内存里。

> [!info]- 来源
> - Worker 线程适用 CPU 工作、消息与共享内存边界：[Node.js v26.11.1, worker_threads](https://nodejs.org/download/release/v26.11.1/docs/api/worker_threads.html)，核对于 2026-11-06。
> - 子进程 IPC 与 fork()：[Node.js v26.11.1, child_process](https://nodejs.org/download/release/v26.11.1/docs/api/child_process.html)，示例于该版本重放，收到结果 55。
> - 多进程共享 HTTP 端口及 worker 生命周期：[Node.js v26.11.1, cluster](https://nodejs.org/download/release/v26.11.1/docs/api/cluster.html)，核对于 2026-11-06。
> - 文件系统哪些 API 使用 libuv 线程池：[Node.js v26.11.1, File system](https://nodejs.org/download/release/v26.11.1/docs/api/fs.html#threadpool-usage)；加密、压缩和 DNS 的 API 边界见 [crypto](https://nodejs.org/download/release/v26.11.1/docs/api/crypto.html)、[zlib](https://nodejs.org/download/release/v26.11.1/docs/api/zlib.html)、[DNS](https://nodejs.org/download/release/v26.11.1/docs/api/dns.html)，核对于 2026-11-06。
> - PM2 Cluster mode 的 reload 回退与进程关闭责任：[PM2, Cluster Mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/)；启动、查看和重载命令见 [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/)，核对于 2026-11-06。
> - PM2 默认 SIGINT、`kill_timeout` 后 SIGKILL 和 `PM2_KILL_SIGNAL` 配置：[PM2, Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)、[PM2 Environment Variables](https://pm2.keymetrics.io/docs/usage/environment/)，核对于 2026-11-06。
