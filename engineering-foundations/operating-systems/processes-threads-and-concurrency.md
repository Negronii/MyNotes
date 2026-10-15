# Processes, Threads, and Concurrency / 进程、线程与并发

**Core model / 核心模型：** A process is an operating-system resource and protection boundary; a thread is an execution path inside a process. Threads share much of that process's memory and therefore need coordination when they update shared state. Concurrency means work overlaps in time; parallelism means work executes at the same time on multiple processing units. Asynchronous I/O can provide concurrency without assigning one thread to every waiting operation. / 进程是操作系统管理资源并隔离地址空间的边界；线程是在进程内执行指令的路径。线程共享进程中的许多内存，因此并发修改共享状态时需要协调。并发表示任务的执行时间重叠；并行表示多个处理单元同时执行任务。异步 I/O 可以在不为每个等待中的操作分配一个线程的情况下提高并发能力。

**Key terms / 关键术语：** process / 进程；thread / 线程；address space / 地址空间；concurrency / 并发；parallelism / 并行；blocking I/O / 阻塞 I/O；non-blocking I/O / 非阻塞 I/O；asynchronous I/O / 异步 I/O；race condition / 竞态；deadlock / 死锁；cancellation / 取消。

## Process and thread / 进程与线程

| Aspect / 维度 | Process / 进程 | Thread / 线程 |
| --- | --- | --- |
| Memory / 内存 | Has its own virtual address space in the usual process model. Processes can explicitly map shared memory. / 通常拥有独立的虚拟地址空间；也可以显式映射共享内存。 | Threads in one process share its address space and global data; each thread has its own execution state and stack. / 同一进程中的线程共享地址空间和全局数据；每个线程有自己的执行状态和栈。 |
| Communication / 通信 | Uses an explicit boundary such as a pipe, socket, message, or shared mapping. / 通过管道、套接字、消息或共享映射等显式边界通信。 | Can pass references through shared memory, but concurrent access must follow a synchronization rule. / 可通过共享内存传递引用，但并发访问必须遵循同步规则。 |
| Typical choice / 常见选择 | Prefer when a fault or trust boundary matters, or work needs separate process lifetime. / 当故障或信任隔离、独立进程生命周期很重要时考虑使用。 | Prefer when work benefits from shared process state or CPU-parallel execution and the program can manage synchronization. / 当工作需要共享进程状态或 CPU 并行执行，且程序能管理同步时考虑使用。 |

These are useful defaults, not cost or isolation guarantees for every operating system. A process can deliberately share memory or handles; a thread does not automatically make CPU work faster. For Node-specific choices among its event loop, worker threads, and child processes, see [Node.js Fundamentals / Node.js基础](../backend/node-js-fundamentals.md).

## Concurrency, parallelism, and I/O / 并发、并行与 I/O

Tasks are **concurrent** when their progress overlaps—for example, a server starts another request while the first waits for a response. They are **parallel** when instructions from both tasks execute at the same instant on separate cores or other processing units. A single event-loop thread can coordinate many waiting I/O operations, but a long synchronous callback still prevents that thread from running other callbacks. CPU parallelism needs another execution resource, such as a worker thread or process.

| I/O style / I/O 方式 | What the caller observes / 调用方观察到的行为 |
| --- | --- |
| Blocking / 阻塞 | The calling thread waits until the operation can make progress or completes. / 调用线程等待操作可以继续或完成。 |
| Non-blocking / 非阻塞 | An attempt returns promptly when it cannot proceed; the caller can wait for readiness or try again. A non-blocking result does not itself mean the full transfer completed. / 暂时无法继续时，调用立即返回；调用方可等待就绪或稍后重试。非阻塞返回本身不表示数据已经全部传输完成。 |
| Asynchronous / 异步 | The caller submits work and receives a later completion or callback. The runtime may use operating-system readiness, a completion facility, or a worker pool. “Async” describes the interface and scheduling relationship, not one universal implementation. / 调用方提交工作，随后接收完成通知或回调。运行时可能使用操作系统就绪通知、完成机制或工作线程池。“异步”描述接口与调度关系，并不对应唯一实现。 |

In Node.js, synchronous filesystem APIs block the event-loop thread. Callback- and promise-based filesystem APIs use libuv's thread pool except `fs.FSWatcher`; many network operations are driven by the operating system. Exact APIs have their own contracts. Async I/O therefore helps waiting workloads, but moving CPU-heavy JavaScript off the event loop requires workers or processes. See the [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) note for scheduling details.

## Races and deadlocks / 竞态与死锁

A **race condition / 竞态** exists when the result depends on the timing or order of operations that access shared state. For example, an increment is a read–modify–write sequence: two workers can both read `10`, compute `11`, then each write `11`, losing one increment. Protect the invariant with a lock, an atomic operation, a single owner that processes messages, or a database constraint—whichever matches the boundary. In JavaScript, synchronous code in one event-loop turn runs to completion, but state can still change between `await` points; worker threads that share a `SharedArrayBuffer` need an explicit synchronization protocol.

A **deadlock / 死锁** occurs when tasks wait in a cycle. If worker A holds lock L1 and waits for L2 while worker B holds L2 and waits for L1, neither can continue. Consistent lock ordering and short critical sections prevent many such cycles. Avoid holding a lock while waiting on network or other unbounded work; a timeout can reveal a stuck wait, but does not by itself restore a partially changed invariant.

## Cancellation and cleanup / 取消与清理

Cancellation is a request to stop work, not proof that work has stopped or that its side effects were undone. Many APIs use cooperative cancellation: code checks a token, stops at a safe boundary, and releases resources or leaves shared state consistent. In POSIX threads, deferred cancellation is the default and takes effect at cancellation points; asynchronous cancellation can interrupt code while it holds a resource. Runtime and API contracts differ, so check whether the operation actually observes cancellation. In particular, cancelling a caller's wait does not retract a request that a remote service already accepted.

## A runnable shared-counter example / 可运行的共享计数示例

The two workers below share one integer. `Atomics.add` makes each read–modify–write increment one synchronized operation; after both workers exit, the expected count is `200000`. Without an atomic operation or another coordination rule, increments can be lost.

~~~javascript
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const workers = Array.from(
    { length: 2 },
    () => new Worker(__filename, { workerData: shared }),
  );

  const waitForExit = worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => {
      if (code === 0) resolve();
      else reject(new Error(`worker exited with code ${code}`));
    });
  });

  Promise.all(workers.map(waitForExit)).then(() => {
    console.log(Atomics.load(new Int32Array(shared), 0));
  }).catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
} else {
  const counter = new Int32Array(workerData);
  for (let i = 0; i < 100_000; i++) Atomics.add(counter, 0, 1);
}
~~~

Verified with Node.js v26.11.1; observed output: `200000`. This checks one local runtime example, not performance scaling or every platform's worker implementation.

**Related notes / 相关笔记：** [Node.js Fundamentals / Node.js基础](../backend/node-js-fundamentals.md) applies these process and worker boundaries to Node's APIs; [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) explains how queued callbacks make progress on a JavaScript thread.

**Sources / 来源：** POSIX.1-2024 [General Information, process and thread model](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html); Linux [`pthreads(7)`](https://man7.org/linux/man-pages/man7/pthreads.7.html), for Linux/POSIX thread-sharing and cancellation-point details; Node.js v24 [worker_threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html) and [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html#threadpool-usage) documentation, checked 2026-10-15. The filesystem docs specify that callback and promise APIs except `fs.FSWatcher` use libuv's thread pool.
