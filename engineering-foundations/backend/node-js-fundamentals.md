# Node.js Fundamentals / Node.js基础

Node.js runs JavaScript outside a browser and provides server-side APIs. Its event-loop model is efficient for many I/O workloads, but a long synchronous callback still blocks JavaScript work on that event-loop thread.

Node 的异步 I/O、事件循环、工作线程和子进程解决不同问题：I/O 等待通常使用异步 API，CPU 并行、进程隔离或共享状态则要按线程与进程边界选择，并处理通信和关闭。

## What's the difference between a process and a thread?

**进程 / Process** is an operating-system execution boundary with its own virtual address space. **线程 / Thread** is an execution path inside a process; threads can share process memory, so shared mutable data needs coordination.

Node has a JavaScript event-loop thread for each isolate, not one JavaScript thread for the whole machine. A worker thread runs JavaScript in another isolate in the same process. It can exchange messages, transfer an ArrayBuffer, or share a SharedArrayBuffer; shared memory requires explicit synchronization such as Atomics. A child process has a separate process address space and communicates through IPC or other operating-system channels.

Node also uses background mechanisms for asynchronous work: network I/O is commonly driven by the operating system, while selected APIs such as filesystem operations, cryptography, compression, and some name-resolution work use libuv's worker pool. Their JavaScript callbacks run on the event-loop thread. CPU-heavy JavaScript on that thread delays other callbacks.

For the reusable process/thread model of address spaces, shared resources, concurrency, I/O, and cancellation, see [Processes, Threads, and Concurrency / 进程、线程与并发](../operating-systems/processes-threads-and-concurrency.md); this note applies it to Node's event loop and worker choices.

---

## How do you use multiple CPU cores in Node.js?

Choose based on the work and isolation needed:

- **Worker threads / 工作线程** run CPU-intensive JavaScript in parallel and can communicate by message or shared memory. Use a bounded worker pool for repeated tasks rather than creating one thread per small job.
- **Child processes / 子进程** run in separate process memory and provide stronger isolation; IPC messages are a boundary to account for.
- **Cluster / 多进程服务** starts multiple Node processes that can accept connections on the same server port. It is one deployment option for multi-core servers, not a guarantee of linear throughput scaling or balanced work.

Built-in asynchronous I/O is usually a better choice for I/O-bound work than worker threads. For process or worker choices and shared-state trade-offs, see the linked Node.js API documentation.

An external process manager is optional. PM2 is one choice for starting and observing clustered workers:

~~~bash
pm2 start app.js --name api -i max
pm2 list
pm2 monit
pm2 reload api
~~~

PM2 may fall back from a cluster reload to a restart if it cannot complete it. The application must handle shutdown and drain or close its own work; availability during reload is not guaranteed.

### Child process example

This compact CommonJS example runs the same file in a child process and sends one task over the fork IPC channel. It is illustrative; production code also needs workload limits, error handling, and shutdown policy.

~~~javascript
const { fork } = require('node:child_process');

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    let a = 0;
    let b = 1;
    for (let i = 0; i < n; i++) [a, b] = [b, a + b];
    process.send({ result: a });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.on('message', message => {
    console.log(message.result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

### Cluster example

Each worker is a separate process. Restarting workers, health checks, graceful shutdown, and shared session state are application or process-manager responsibilities; the cluster module does not make in-memory state shared.

~~~javascript
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
    response.end('Hello');
  }).listen(8000);
}
~~~

Workers have separate heaps. If a session, cache, or connection map must be shared, choose a deliberate external store, routing strategy, or message-broadcast mechanism. A Redis store is one option, not a universal requirement.

---

## How do CommonJS and ES modules affect nextTick ordering?

Node's scheduling details depend on where work is queued. At top level, `process.nextTick` runs before Promise callbacks in this CommonJS example:

~~~javascript
// Save as example.cjs
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));
~~~

The same calls have the opposite order at the top level of an ES module:

~~~javascript
// Save as example.mjs
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
nextTick(() => console.log('nextTick'));
~~~

This difference is about the module's execution context; it is not a universal ordering rule for every callback or event-loop phase. Use the current [Node.js process documentation](https://nodejs.org/docs/latest-v24.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick) when an ordering dependency matters.

---

## How does stream backpressure limit buffering? / 流背压如何限制缓冲？

**核心解释 / Core explanation：** A stream moves data in chunks from a producer to a consumer. A `Readable` supplies chunks; a `Writable` accepts them; a `Transform` reads and writes while changing them; a `Duplex` does both. When `writable.write(chunk)` returns `false`, stop producing until `'drain'` says writing can resume. `pipeline()` connects stages and propagates a slow consumer's backpressure upstream.

**中文说明：** 流按数据块从生产者流向消费者；`write()` 返回 `false` 时，生产者应暂停并等待 `'drain'` 再继续。`pipeline()` 会把下游变慢的背压传回上游。`highWaterMark` 是暂停阈值而非内存上限；单个大数据块、各阶段缓冲和链路外队列仍可能增加内存。读取端的 `'end'` 表示输入结束，写入端的 `'finish'` 表示 `end()` 后已处理已接收写入；`'close'` 表示资源关闭，`'error'` 表示失败。`destroy()` 用于中止或失败，额外拥有的游标等资源应在 `finally` 中释放；写入完成也不代表远端应用已处理数据或文件已持久化。

**面试简答 / Interview answer：** If `write()` returns `false`, stop calling it until `'drain'`; continuing to submit chunks can grow the writable's queue and memory use. Use `pipeline()` for a source/transform/destination chain, or wait for `'drain'` in a manual producer. `highWaterMark` is a pause threshold, not a hard memory cap; a large chunk, transform buffers, or queues outside the pipeline can still use more memory.

~~~javascript
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createGzip } = require('node:zlib');

async function* rows() {
  for (let id = 1; id <= 10_000; id++) yield { id };
}

async function exportRows(signal) {
  const lines = (async function* () {
    for await (const row of rows()) yield `${JSON.stringify(row)}\n`;
  })();

  await pipeline(
    Readable.from(lines),
    createGzip(),
    createWriteStream('rows.ndjson.gz', { highWaterMark: 32 * 1024 }),
    { signal }
  );
}

const controller = new AbortController();
// The owner can call controller.abort(reason) to cancel the export.
exportRows(controller.signal).catch((error) => {
  console.error('export failed:', error.message);
});
~~~

Here the async generator produces one row at a time, and `pipeline()` resolves after the output finishes. If a stage errors or the signal aborts, the promise rejects and the pipeline destroys its participating streams. A producer that owns an extra resource, such as a database cursor, should release it in `finally`; pipeline cleanup cannot close resources hidden outside its stages. For manual writes, the same rule is `if (!writable.write(chunk)) await once(writable, 'drain')`.

The terminal signals describe different outcomes: a readable `'end'` means no more input chunks remain; a writable `'finish'` means its accepted writes have completed after `end()`; `'close'` reports resource closure when that stream emits it; `'error'` reports failure. Use `destroy(error)` to abort or fail a stream, not as a synonym for successful end-of-input. A writable finishing does not prove that a remote application processed the bytes or that a file is durable on storage.

## How does a Node.js service drain on shutdown? / Node.js服务如何排空并关闭？

Graceful shutdown is an application lifecycle, not something the event loop or HTTP server performs for every dependency. On a shutdown signal, mark the instance unready and have each request handler reject work before enqueueing it; this also catches requests on already-open keep-alive connections. Then stop accepting connections, let tracked handlers and response streams finish, cancel work at the deadline, and close pools, workers, timers, and other owned resources after their users have stopped. Pass `workAbort.signal` to cancellable handlers and track accepted work so `waitForInFlightWork()` has a real completion condition.

**核心解释（中文）：** 收到关闭信号后先摘除就绪并拒绝新任务，再停止接入、等待已接收请求和后台工作排空；到期后发出协作取消并强制关闭 HTTP 连接。服务端关闭与跟踪任务都结算后，再回收它们使用的资源；即使其中一项失败，也要完成清理并报告错误，且在生命周期和清理报告结束前保留截止计时器。

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

## What is serverless or function-as-a-service?

**无服务器计算 / Serverless** means the provider manages the underlying execution infrastructure through a function or managed runtime interface. Servers still exist; the provider controls how execution environments are created, reused, and scaled.

Timeouts, concurrency limits, billing, cold-start latency, and state-reuse behavior depend on the provider, product, runtime, region, and configuration. Do not treat in-memory state as durable or assume an execution environment is discarded after every invocation. For example, AWS Lambda documents that environments can be reused while advising applications to treat state as temporary and persist durable changes externally.

It can suit event-triggered handlers or variable workloads when the provider's limits and cost model fit. Long-running work, persistent connections, predictable latency, and vendor-specific integrations require a comparison against other deployment models.

**See also:** [Event Loop](../../frontend/runtime/event-loop.md) for browser and Node scheduling context, and [Software Design Principles](../architecture/software-design-principles.md) for choosing boundaries around runtime-specific infrastructure.

Sources: [Node.js v24 worker threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html), [child processes](https://nodejs.org/docs/latest-v24.x/api/child_process.html), [cluster](https://nodejs.org/docs/latest-v24.x/api/cluster.html), [process scheduling](https://nodejs.org/docs/latest-v24.x/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html), [crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html), [zlib](https://nodejs.org/docs/latest-v24.x/api/zlib.html), and [DNS](https://nodejs.org/docs/latest-v24.x/api/dns.html) documentation; [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) and [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/); plus [AWS Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) and [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html). PM2 and AWS references checked 2026-10-15; provider limits change over time.

The stream and shutdown sections were checked against [Node.js v26.11.1 stream](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html), [HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html), and [process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html) documentation on 2026-10-15. The shutdown deadline's timer-reference behavior was checked against the [Node.js v26.12.1 timer documentation](https://nodejs.org/api/timers.html) on 2026-10-27.
