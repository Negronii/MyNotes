# 一份工作该交给进程、线程还是异步 I/O？

本章回答：一段工作在等待 I/O 或占用 CPU 时，应该交给异步 I/O、有界线程池还是独立进程；取消一段在途工作时，哪些信号能说明它真的停了。读者手上只需要本科操作系统课里的进程、线程和系统调用概念。本章也建立主线二的案例，后面各章都在同一个进程里继续追问：怎样共享状态、怎样调度回调、怎样传播背压、怎样停机。

## 案例：一次导出要等什么、算什么

账户报表服务里有一个 worker 进程，正在执行导出任务 `job-demo-731` 的 attempt (执行尝试) 1：把账户 `acct-17` 的报表 42 导出成压缩 CSV。这个任务怎样被受理、领取和确认属于主线四，本主线把“worker 已经拿到 attempt 1”当作给定输入。worker 要做的事按顺序是：

| 阶段 | 做什么 | 主要在等什么 |
| --- | --- | --- |
| 读取 | 异步生成器包装数据库游标，每次取一页，每页最多 100 行，最多 12 页 | 网络 I/O：等数据库返回 |
| 格式化 | 把一行转成一条 CSV 文本 | 很短的 CPU 工作 |
| 压缩 | 默认用 Node 内置的 zlib gzip；对照方案是一个自建的同步增量压缩器 | CPU |
| 写出 | 写入用 `mkdtemp` 新建、本 attempt 独占的临时目录 | 文件 I/O |
| 发布 | 关闭临时文件，再 `rename` 到同一文件系统上按 job 和 attempt 区分的路径 | 文件系统元数据操作 |

同一服务的 API 进程还有另一类工作：把 `acct-17` 的三行 CSV 直接流给一个 HTTP 响应，这是请求内的工作，请求结束它就结束。停机一章会回放这条响应：默认每行间隔 100 ms，加 `--slow` 时每行 600 ms，进程内部的停机截止时间为 1 s。部署平台最终会给这些进程发 `SIGTERM`，平台侧的时限见[服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](../practice/production-runtime.md)。

以上数值都是教学用的合成参数。本章要回答的第一个问题是：读取、压缩、写出这几个阶段各该放在哪种执行资源上。

## 进程和线程各划出什么边界？

在常见的操作系统模型里，process (进程) 是资源与保护边界，通常拥有自己的虚拟地址空间；thread (线程) 是进程内的一条执行路径。同一进程的线程共享堆、全局数据和大多数打开的句柄，但各有自己的寄存器状态和栈。

进程之间通常靠管道、套接字、消息或显式映射的共享内存通信。Linux 的 `mmap(MAP_SHARED)` 可以让两个进程看到同一块内存，所以“进程之间什么都不共享”并不准确；准确的说法是，进程默认不共享地址空间，要共享就得显式安排。

独立地址空间也不等于权限隔离。`fork()` 出来的子进程会继承父进程的用户身份和打开的文件描述符；父进程能读的文件、能连的网络，子进程照样能访问。运行不可信代码时，要另用操作系统策略（如 Linux Landlock）缩减它能访问的文件和网络。

## 并发和并行有什么区别？

concurrency (并发) 指多个任务在重叠的时间段内都有进展；只有一个处理单元时，调度器靠交替运行做到这一点。parallelism (并行) 指多个处理单元在同一时刻各自执行指令。

单线程的事件循环能做到并发：一个请求在等数据库时，线程去处理另一个请求。但它做不到并行，而且一段很长的同步计算会把这条线程整个占住，其他任务都只能等。CPU 计算能否并行，取决于语言运行时是否允许多段代码同时执行、数据怎样在执行者之间交接，以及负载是否大到值得拆分。

## 阻塞、非阻塞和异步 I/O 各指什么？

三种说法描述的是调用方与操作之间的关系：

- blocking I/O (阻塞 I/O)：调用线程一直等到操作完成或可以继续，例如普通的 `read()`。
- non-blocking I/O (非阻塞 I/O)：暂时不能继续时立即返回，例如返回 `EAGAIN`，意思只是“目前没有数据”，调用方要稍后再试，通常配合 `poll()` 这类就绪通知使用。
- async I/O (异步 I/O)：调用方提交操作后先去做别的事，稍后收到完成结果。

“异步”描述的是调用关系，不说明底层由谁执行。网络 I/O 可以由操作系统的就绪通知驱动，不需要为每个连接配一个线程；Node.js 的回调式和 Promise 式文件系统 API（`fs.FSWatcher` 除外）则在 libuv 的线程池里执行，只是调用方不必原地等。

同理，`await` 本身不创建线程，也不会把表达式搬到后台。被等待的 Promise 尚未结算时，`async` 函数挂起，把控制权交还事件循环；结算后，函数剩余部分回到原来的执行线程继续运行。所以“函数返回 Promise”不能说明工作在别的线程上完成，要查具体 API 的文档。

如果运行时没有合适的异步 API，可以把同步调用放进有界的阻塞线程池，让请求线程腾出来。这只是让池里的一个线程代为等待，底层调用并没有变成异步操作。I/O 阶段的选择可以归结为：

~~~mermaid
flowchart TD
    IOWait[I/O 阶段] --> HasAsync{运行时有合适的<br/>异步 API？}
    HasAsync -->|有| AsyncAPI[用异步 API<br/>等待期间事件循环<br/>处理其他工作]
    HasAsync -->|没有| BlockingPool[放进有界线程池<br/>每个等待<br/>占一个池线程]
    AsyncAPI --> Limit[限制在途操作<br/>连接、缓冲和队列]
    BlockingPool --> Limit
~~~

两条路最后都要设上限：异步等待不占线程，但每个在途操作仍占着连接和缓冲区。

## 三种执行资源各要你负责什么？

| 执行资源 | 适合的工作 | 你要承担的责任 |
| --- | --- | --- |
| 异步 I/O | 运行时为数据库、网络或文件提供了适用的异步 API | 在途操作仍占连接和缓冲区，必须限制并发数；同步代码仍会卡住事件循环 |
| 有界线程池 / 工作线程 | 运行时能并行执行的 CPU 转换；或把同步阻塞调用移出请求线程 | 线程共享进程地址空间，共享的可变状态要同步；阻塞调用一直占着一个池线程；线程数和排队数都要有上限 |
| 独立进程 | 需要独立生命周期、故障边界或地址空间的计算 | 消息序列化、独立内存和启动成本；要自己管理退出；子进程默认继承父进程的身份与句柄，不是沙箱 |

## CPU 工作该放在哪里？

CPU 工作的放置先看要满足哪种目标。三种目标可能同时出现，每一种都要逐项验证：

| 目标 | 可选路径 | 必须验证的条件 |
| --- | --- | --- |
| 独立的故障或地址空间边界 | 独立进程 | 进程边界能否隔开所需的故障或内存；不可信代码的权限要另外限制；跨进程交接数据的成本 |
| 满足响应预算，不要求跨核 | 先把工作拆成短片段并在片段间让出；不达标再用工作线程；仍不达标再评估独立进程 | 单个片段能否落在预算内；工作线程能否让响应路径及时获得调度（即使没有并行也可能有用）；进程方案在当前负载下能否达标 |
| 必须跨核并行 | 能真正并行执行这类工作的线程；否则用多进程 | 运行时是否真的并行执行；机器有没有可用的处理单元和 CPU 配额；数据交接成本；若同时有响应预算，两项都要满足 |

无论选哪条路，都要限制作业入口和在途数据量；用了线程池或进程池，还要限制执行槽数和排队任务数。

工作线程把 CPU 计算移出事件循环线程后，即使运行时不能让两段代码同时在多个处理单元上执行，调度器仍会交替运行它们，响应路径因此有机会及时执行。这改善的是获得调度的机会，不保证达到某个延迟预算。

**回到 `job-demo-731`。** 读取页面主要在等网络，留在事件循环上用异步 API。压缩是 CPU 工作，有两种做法：

- 默认做法用 Node 内置的异步 zlib gzip。它本身就在 libuv 线程池里执行，不占事件循环，代价是和同进程里其他文件、DNS、加密操作共用同一个池。
- 对照做法是一个自建的同步增量压缩器，它有内部状态，必须按顺序逐页喂给同一个执行者。按上表核对：这个任务不要求跨核，也不需要隔离可能崩溃的本地库；本例假设即使把压缩拆成最短的可接受片段，单个片段仍超出事件循环的响应预算，所以把它交给 Node 的 `worker_threads`。目的在于让事件循环保持响应，不是提高吞吐。

这个对照方案的完整协议（每页确认、收尾、归还 worker 槽）在 [Node 的执行位置一章](node-threads-processes-and-workers.md)；默认方案的流水线与背压在[流一章](stream-backpressure-and-partial-output.md)。

## 取消能证明什么？

worker 执行到一半时，可能收到取消：用户取消了 job、请求超时，或进程要停机。不论在哪个运行时，**取消只是一个请求**：它请求任务协作停止，并不证明任务已经结束，更不证明任务的副作用没有发生。

收到取消的代码要做三件事：按 API 规定的方式观察取消信号；从这一刻起不再提交新的副作用；在 `finally` 或等价的清理路径里释放自己拥有的资源。

POSIX 线程把“请求”和“结束”分得很清楚，可以作为参照：

- 新线程默认启用 deferred cancellation (延迟取消)，取消请求只在取消点处理；线程可以改成异步取消（可能在任意时刻处理），也可以暂时禁用取消。
- `pthread_cancel()` 返回成功，只说明取消请求已经排入，不说明线程已经终止。
- 对 joinable 线程调用 `pthread_join()` 会等它终止。`pthread_join()` 返回 `0` 只说明 join 成功；要确认线程是因取消而结束，还得看它的退出值是否等于 `PTHREAD_CANCELED`。

应用层的取消通常更弱：被取消的往往只是**等待方**。调用方不再等某个 Promise、某个线程或某个远端请求，底层的线程、数据库操作或远端请求却可能继续运行；已经提交的写入也不会因此回滚。由此得到几条跨运行时的规则：

- 计时器到点只是安排一段代码运行，不会中断正在运行的回调，也不会取消尚未完成的数据库查询；要取消底层操作，必须用该驱动或服务提供的取消机制。
- 调用方放弃 `await` 不会取消底层操作；Node 的 `AbortSignal` 也只对接收并处理它的 API 生效。
- Python 的 `Task.cancel()` 只在协程内部抛入 `CancelledError`；`asyncio.to_thread()` 中已经开始运行的线程不会被杀掉。
- 一次写入是否真的发生，以持久化的业务结果为准，不能把“本地任务已取消”记成“操作没有发生”。

在 `job-demo-731` 里，这意味着：取消请求到达后，worker 要先停止拉取新页，再等在途的查询、压缩和文件写入各自给出结束信号，才能释放它们占用的资源；取消一次文件写入后，临时文件里可能已经留下部分数据。各运行时的具体行为在各自章节：Node 的计时器见[事件循环一章](node-event-loop-and-microtasks.md)，worker 收不到取消消息的情形见 [Node 执行位置一章](node-threads-processes-and-workers.md)，Python 的取消见 [asyncio 一章](python-asyncio-and-fastapi.md)，流的取消与部分输出见[流一章](stream-backpressure-and-partial-output.md)。浏览器端 Promise 与 `AbortSignal` 的语义见前端的[取消、超时与并发](../../frontend/javascript/cancellation-timeouts-and-concurrency.md)。持久 job 的取消要通过持久状态裁决，见主线四的[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](../services/job-retries-cancellation-and-cleanup.md)。

## 下一步：多个执行者共享状态时

到这里，导出的各阶段都有了执行位置：页面读取用异步 I/O，压缩交给线程池或工作线程，独立进程留给需要故障或地址空间边界的工作；取消被当作请求，结束要看各资源自己的完成信号。一旦有两个执行者同时修改同一份状态（两个 worker 更新同一个计数，取消和发布同时想改 job 的状态），就会出现新问题：结果取决于谁先谁后。下一章讨论[多个执行者怎样共享状态而不丢更新、不互相卡死](shared-state-races-and-deadlocks.md)。

> [!info]- 来源
> - 进程与线程的边界：`fork()` 后父子进程内存空间分离，`mmap()` 的 `MAP_SHARED` 建立显式共享映射：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)，`MAP_SHARED` / `MAP_PRIVATE`；2026-11-11 核对。
> - 同一进程的 POSIX 线程共享全局数据与堆、各有栈与线程状态：[Linux man-pages 6.19, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，2026-11-11 核对。
> - 子进程继承凭据和打开的文件描述符；用 OS 策略限制文件与网络访问：[fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[Linux kernel, Landlock](https://docs.kernel.org/userspace-api/landlock.html)，2026-11-11 核对。
> - 阻塞 `read`、非阻塞时返回 `EAGAIN`、`poll` 等待就绪、提交后收到完成通知：[read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)、[aio(7)](https://man7.org/linux/man-pages/man7/aio.7.html)，2026-11-11 核对。
> - Node 回调式与 Promise 式文件 API（`fs.FSWatcher` 除外）使用 libuv 线程池：[Node.js v26.13.0, File system, Threadpool usage](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)，2026-11-11 核对。
> - Node 异步 zlib API 在内部线程池执行，同步 API 除外：[Node.js v26.13.0, Zlib, Threadpool usage](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - `worker_threads` 面向 CPU 密集型 JavaScript，I/O 优先使用内置异步 API：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，2026-11-12 核对。
> - 延迟与异步线程取消、取消请求不等于终止：[Linux man-pages 6.19, pthread_cancel(3)](https://man7.org/linux/man-pages/man3/pthread_cancel.3.html)，2026-11-11 核对。
> - joinable 线程的终止状态与 `PTHREAD_CANCELED`：[Linux man-pages 6.19, pthread_join(3)](https://man7.org/linux/man-pages/man3/pthread_join.3.html)，2026-11-11 核对。
