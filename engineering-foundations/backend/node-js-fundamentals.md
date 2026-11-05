# How does Node.js schedule work across its event loop, workers, and processes? / Node.js 如何在事件循环、工作线程与进程之间调度工作？

**Core answer / 核心回答：** Use asynchronous APIs for I/O waits; one event-loop thread runs JavaScript callbacks and a long synchronous callback blocks it. Move CPU-heavy JavaScript to a bounded worker pool, and use child processes when process isolation matters. The choice changes memory sharing, communication, fault boundaries, and shutdown duties. A worker pool also needs a bounded admission policy; see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md). / I/O 等待通常使用异步 API；JavaScript 回调在事件循环线程上运行，长时间同步回调会阻塞它。CPU 密集型 JavaScript 可交给有界 worker 池；需要进程隔离时可使用子进程。不同选择会改变内存共享、通信、故障边界与关闭责任。

**Key terms / 关键术语：** event loop / 事件循环；isolate / 隔离环境；worker thread / 工作线程；child process / 子进程；cluster / 多进程服务；IPC / 进程间通信。

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


**Related questions / 相关问题：** [Node.js event-loop phases and microtasks / Node.js 事件循环阶段与微任务](node-event-loop-and-microtasks.md) explains host scheduling; [How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？](node-stream-backpressure-and-cleanup.md) explains chunk flow and cleanup; [How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？](node-service-shutdown.md) covers in-flight work and resource closure; [What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？](serverless-runtime-boundaries.md) describes provider-managed execution environments.
**Sources / 来源：** Node.js v24 documentation for [worker threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html), [child processes](https://nodejs.org/docs/latest-v24.x/api/child_process.html), [cluster](https://nodejs.org/docs/latest-v24.x/api/cluster.html), [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html), [crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html), [zlib](https://nodejs.org/docs/latest-v24.x/api/zlib.html), and [DNS](https://nodejs.org/docs/latest-v24.x/api/dns.html); [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) and [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/), checked 2026-10-15.
