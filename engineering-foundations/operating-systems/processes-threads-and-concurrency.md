# 何时选线程、进程或异步 I/O？

**案例：** 报表服务接到 acct-17 的导出任务，需要读数据库、格式化几万行并写出压缩文件。数据库响应期间主要在等 I/O；格式化若占住一颗 CPU 很久，则会拖慢同一执行路径上的其他请求。选线程、进程或异步 I/O，要先看工作是在等什么、要共享什么，以及停止它时谁负责释放资源。

~~~mermaid
flowchart TD
    Report[账户报表任务] --> Wait{当前主要在等 I/O？}
    Wait -->|是| Async[异步 I/O：等待时让其他工作继续]
    Wait -->|否，CPU 计算很久| CPU{需要独立地址空间/故障隔离，或运行时线程不能并行计算？}
    CPU -->|是| Process[独立进程：消息或显式共享内存]
    CPU -->|否| Thread[工作线程：共享地址空间；并发修改需同步]
    Async --> Limit[仍要限制在途任务和等待队列]
    Thread --> Limit
    Process --> Limit
~~~

图里的决定顺序是：先确认是否有长时间 CPU 计算，再选择执行边界。异步 I/O 让等待中的任务不必独占一个线程，但不会让 CPU 计算自动并行；线程与进程也不会自动形成有界的任务队列。

## 进程、线程和异步 I/O 各自拥有哪种边界？

在常见操作系统模型中，process（进程）是资源与保护边界，通常有自己的虚拟地址空间；thread（线程）是进程里的执行路径。同一进程的线程共享地址空间中的堆、全局数据和许多句柄，但每个线程仍有自己的寄存器状态和栈。进程间通常用管道、套接字、消息或显式映射的共享内存通信。进程可通过显式配置共享部分资源，因此“进程绝不共享”也不准确。

| 选择 | 报表服务里的合适工作 | 付出的责任 |
| --- | --- | --- |
| 异步 I/O | 等待数据库查询、网络响应或异步文件 I/O | 等待期间仍有任务、连接和缓冲区；必须限制并发 |
| 工作线程 | CPU 密集型转换；或确实需要共享同一进程状态 | 共享可变状态需同步；线程池及其排队量需有界 |
| 独立进程 | 易崩、需要独立生命周期或独立地址空间的计算 | 消息/序列化、独立内存和启动成本；必须管理子进程退出。不可信代码还需要操作系统权限隔离 |

并发（concurrency）是多个任务在一段时间内交替推进；并行（parallelism）是多个处理单元同时执行指令。单线程事件循环可以在一个请求等待 I/O 时处理另一个请求，因此能有并发；一个很长的同步回调仍会堵住这条线程。要让 CPU 计算并行，需要工作线程或其他执行资源，但能否提速还取决于语言运行时、数据交换和负载大小。Node 的运行时选择见[Node.js 如何在事件循环、worker 与进程之间调度工作？](../backend/node-js-fundamentals.md)。

阻塞 I/O 会让调用线程等操作完成或可以继续；非阻塞 I/O 在暂时无法继续时迅速返回，但一次返回可能只表示“目前没数据”；异步 I/O 则让调用方提交操作，并在稍后收到完成结果。异步 API 描述调用关系，不表示底层必定由某个工作线程执行：网络 I/O 可由操作系统就绪通知驱动，某些文件或加密工作则可能使用运行时的线程池。

## 共享计数为什么会丢更新？

竞态（race condition）是结果取决于并发操作顺序。count += 1 看起来是一条语句，概念上却是读、加一、写回三个步骤。若两个线程都先读到 10，再各自写 11，最终还是 11；预期的 12 丢了一次更新。对共享不变量，选择一条明确的所有权规则：锁、原子操作、单一写入者消息循环，或数据库约束。数据库中的库存不能靠进程内锁在所有服务副本间保护。

以下例子把一个 32 位计数器放进共享内存，用 Atomics.add 将读—改—写变成原子操作。每个工作线程（worker thread）加 100,000 次，因此两者结束后应为 200,000。

~~~javascript
// 保存为 counter.cjs；使用 Node.js v26.11.1 运行
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
      else reject(new Error('worker exited with code ' + code));
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

本机运行输出 200000。它验证了这段小程序在该 Node 版本中的结果，不证明增加 worker 就会线性提速。

## 等待环何时才构成死锁？

在每类资源只有一个实例的模型里，deadlock（死锁）等价于资源等待图出现环：例如线程 A 持有互斥锁 R1 并等 R2，线程 B 持有 R2 并等 R1。若资源有多个可互换实例，等待图出现环只是必要线索，不足以单独证明死锁。经典资源分配模型还列出互斥、持有并等待、不可抢占和循环等待四个条件；在这个模型中打破任一条件即可消除此类死锁。它们不是判断任意慢请求的打勾清单：请求等待 I/O 或 Promise 未完成本身不构成死锁，先找出实际的资源与依赖关系。浏览器中等待 fetch 的 Promise 不会持有 DOM 独占锁，event loop 可在其 pending 期间运行其他代码；但真实依赖环、永不完成的 Promise 或资源耗尽仍可能让应用停滞。全局一致的锁顺序和短临界区可以拆掉许多锁环；不要在持锁期间等待不确定时长的网络调用。

## 取消信号能证明什么？

取消（cancellation）通常只是要求任务在安全检查点停止。代码需要观察信号、停止提交新副作用，并通过 finally 或等价清理机制释放自己拥有的资源。若取消的是等待方，底层线程、数据库操作或远端请求可能仍在执行；已经提交的写入也不会因此回滚。调用方应以持久化的业务结果确认副作用，而不是把“本地任务已取消”当成“操作没有发生”。

**接下来：** 本章区分执行资源和共享状态；Node 章节把这些边界落实到 isolate、worker 和进程。异步作业何时接受、重试或显式取消见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - 进程与线程的资源、地址空间、线程状态模型：[POSIX.1-2024, General Information](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html)，核对于 2026-11-06。
> - Linux/POSIX 线程共享内存、取消点及取消类型：[Linux man-pages, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，核对于 2026-11-06。
> - Node worker 并行计算与共享内存：[Node.js v26.11.1, worker_threads](https://nodejs.org/download/release/v26.11.1/docs/api/worker_threads.html)；计数程序于该版本重放，输出 200000。
> - Node 文件 API 的异步执行方式：[Node.js v26.11.1, File system](https://nodejs.org/download/release/v26.11.1/docs/api/fs.html#threadpool-usage)，核对于 2026-11-06。
> - 经典资源分配死锁的互斥、持有并等待、不可抢占与循环等待条件：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks”](https://doi.org/10.1145/356586.356588)，核对单实例资源等待环的适用边界。
