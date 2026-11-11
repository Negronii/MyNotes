# 何时选线程、进程或异步 I/O？

**合成案例：** 报表服务接到 acct-17 的导出任务，需要读数据库、格式化几万行并写出压缩文件。读库和写文件可能在等 I/O，格式化与压缩也可能持续占用 CPU。这个作业会经过不同阶段，因此可以在 I/O 阶段按支持情况使用 async I/O（异步 I/O），或用有界阻塞池隔离同步调用；较长的 CPU 计算再交给合适的执行资源。选择前要看每阶段在等什么、要共享什么，以及停止时谁负责清理资源。

## 进程、线程和异步 I/O 各自拥有哪种边界？

在常见操作系统模型中，process（进程）是资源与保护边界，通常有自己的虚拟地址空间；thread（线程）是进程里的执行路径。同一进程的线程共享地址空间中的堆、全局数据和许多句柄，但每个线程仍有自己的寄存器状态和栈。进程间通常用管道、套接字、消息或显式映射的共享内存通信。进程可通过显式配置共享部分资源，因此“进程绝不共享”也不准确。

| 选择 | 报表服务里的合适工作 | 付出的责任 |
| --- | --- | --- |
| async I/O（异步 I/O） | 当前运行时为数据库、网络或文件操作提供适用的异步 API | 在事件循环运行时，任务等待结果期间事件循环线程仍可处理其他任务；在途操作仍占连接、缓冲区等资源，必须限制并发 |
| 工作线程 / 有界线程池 | 运行时支持并行的 CPU 密集型转换；或把同步阻塞调用移入池，释放请求线程 | 通用 OS 线程共享进程地址空间，共享可变状态需同步；阻塞调用会占一个 worker，线程数与队列都要有界 |
| 独立进程 | 需要独立生命周期、故障或地址空间边界的计算 | 消息/序列化、独立内存和启动成本；必须管理退出。子进程可能继承父进程的 OS 身份和打开句柄；独立地址空间本身不会限制文件、网络等访问。运行不可信代码时，要由操作系统策略缩减其可访问的权限与资源 |

concurrency（并发）指多个任务能在重叠的时间段内推进；在单个处理单元上，调度器常靠交替运行它们实现并发。parallelism（并行）指多个处理单元同一时刻执行指令。单线程事件循环可以在一个请求等待 I/O 时处理另一个请求；一个很长的同步回调仍会堵住这条线程。CPU 计算能否并行，还取决于语言运行时、数据交换和负载大小。Node 的运行时选择见[Node.js 如何在事件循环、工作线程与进程之间调度工作？](../backend/node-js-fundamentals.md)。

blocking I/O（阻塞 I/O）会让调用线程等操作完成或可以继续；non-blocking I/O（非阻塞 I/O）在暂时无法继续时迅速返回，但一次返回可能只表示“目前没数据”；async I/O 则让调用方提交操作，并在稍后收到完成结果。异步 API 描述调用关系，不表示底层必定由某个工作线程执行：网络 I/O 可由操作系统就绪通知驱动；Node.js v26.13.0 的回调式与 Promise 式文件系统 API（`fs.FSWatcher()` 除外）使用 libuv 线程池。Node 的 `worker_threads` 则针对 CPU 密集型 JavaScript，I/O 密集任务通常优先使用异步 API。使用有界阻塞池封装同步 API 也能释放请求线程，但那是用 worker 承担同步等待，并没有把底层调用变成原生异步操作。

读数据库、接网络响应或写文件时，先看运行时是否提供适用的异步 API：

~~~mermaid
flowchart TD
    IOWait[I/O 阶段] --> HasAsync{有合适的异步 API？}
    HasAsync --> AsyncAPI[有：任务等待时，<br/>事件循环处理其他工作]
    HasAsync --> BlockingPool[无：有界线程池，<br/>等待占一个 worker]
    AsyncAPI --> Limit[限制在途操作、连接、缓冲和队列]
    BlockingPool --> Limit
~~~

CPU 计算可以有不同目标；隔离、响应和跨核并行可能同时出现。先列出必须满足的目标，再对照可选路径与需要验证的条件：

| 要求 | 可选路径 | 必须验证的条件 |
| --- | --- | --- |
| 独立故障或地址空间边界 | 独立进程 | 进程边界能否隔开所需故障或内存；不可信代码的 OS 权限需另行限制；跨进程数据交接及成本。 |
| 满足响应预算，不要求跨核 | 当前路径拆成短片段并让出；工作线程；若前两种方式不达标，也可评估独立进程 | 当前片段能否在预算内；工作线程能否让响应路径及时获得调度（即使不并行也可能有用）；进程路径能否在当前负载下达到同一预算。 |
| 硬性要求跨核并行 | 能跨核执行该工作负载的线程；否则使用可并行的多进程 | 运行时是否真的并行执行该工作；系统是否有可用处理单元和 CPU 配额；数据交接成本；若同时有响应预算，两项都须满足。 |

无论选择哪条路径，都要限制作业入口和在途数据；使用线程池或进程池时，再限制执行槽和排队任务。

工作线程把 CPU 计算移出请求或事件循环线程；即使运行时不能让两段代码在多个处理单元上同时执行，调度器仍可能交替运行它们，让响应路径及时获得执行机会。这只能改善响应机会，不保证达成某个延迟预算。跨核并行要求多个处理单元同时执行，需按实际运行时语义判断；用进程跨边界时，通过 IPC（进程间通信）或显式共享内存交接数据。

**acct-17 的一次具体执行（教学假设）：** 服务运行 Node.js v26.13.0，数据库驱动支持按需异步游标；每次只取一批有界的订单行，字段为订单号、金额和日期。读库会等待 I/O，因此走异步 API。作业不要求硬性跨核；即使把 CPU 工作拆到当前可接受的最小片段并在片间让出，单片耗时仍超过请求响应预算，而移到 worker 后假设能达标。Node `worker_threads` 可以并行执行 JavaScript，但本例选择它是为响应路径让出执行机会，不以提高吞吐为前提；工作也不需要隔离可能崩溃的本地库。本例特意假设压缩器是同步调用、能保留状态的增量压缩器；不使用 `node:zlib` 异步流，因为 Node 的异步 zlib API 已使用内部线程池，选择它时 CPU 工作的放置方式不同。一个工作线程持有这条压缩流，并按顺序处理一批行；跨线程消息按运行时规则复制或转移数据，成本计入批次预算。

1. **读取。** 异步游标最多返回一个有界批次订单行；当前批次处理和写完前不拉下一批。
2. **压缩并写入。** worker 同步增量处理这批订单，回传零个或多个定长字节块以及“本批完成”确认；即使本批没有输出字节也会发确认。写入方按序写完所有字节、等写操作完成并收到批次确认后，才请求下一批。这样在途输入至多是一批。
3. **输入结束。** 游标读到 EOF 后，单独通知 worker 收尾/flush 压缩流。worker 发完全部尾块、清除这条压缩流的作业状态后，再发 `streamFinished` 确认；确认也表示它不再产出字节；协调者收到这个确认后，才把本作业的 worker 槽归还池。写入方收到确认并写完所有尾块、等待写操作完成，再关闭临时文件。
4. **发布。** 临时文件与本作业专属的最终路径位于同一文件系统，避免替换其他作业的文件。文件关闭后，同一协调者先把作业从 `running` 转到 `publishing`，紧接着提交 rename，中间不等待其他事件。rename Promise 的真实结果决定发布成功或失败；失败后按作业策略清理仍存在的临时文件。

同一事件循环上的作业协调者串行裁决取消与发布。若取消先在 `running` 状态被接受，作业转到 `cancelling`，不提交 rename；停止拉取数据，按游标契约请求取消并丢弃迟到行，等待查询取消或结束，并停止接受 worker 的迟到字节。若协调者尚未归还本作业的 worker 槽，就请求该 worker 停止，等待 `streamFinished` 或停止确认后归还一次；若已归还，则无需再通知该 worker。停止确认仍需在当前有界片段结束、压缩状态清理后发出。协调者还要等待已提交的文件写入结束，之后关闭并删除临时文件，再把作业标为 `cancelled`。若协调者先进入 `publishing` 并提交 rename，后到的取消不能覆盖结果；作业保持发布中，直到 rename 成功或失败，再据其结果进入成功或失败状态。

同步 CPU 片段里，消息回调不能打断正在运行的 JavaScript；只在同一同步回调的片段间读取由消息回调设置的局部变量也不会看到新值。要让取消消息生效，worker 必须在片段间把控制权交还 event loop，例如 `await timersPromises.setImmediate()`（`timersPromises` 来自 `node:timers/promises`），使消息回调运行；若需要在同步循环内响应，则由协调者对共享 buffer 执行 `Atomics.store`，worker 在片段间用 `Atomics.load` 检查停止标志。

这条合成路径说明机制和预期契约，不是已集成的报表服务。单独的 Node.js `fsPromises.writeFile()` AbortSignal 复演验证了取消后可能留下部分写入；没有连接数据库、worker 增量压缩或发布协调器做端到端回放，也没有测量吞吐或延迟。

## 共享计数为什么会丢更新？

race condition（竞态）是结果取决于并发操作顺序。`count += 1` 看起来是一条语句，概念上却是读、加一、写回三个步骤。若两个线程都先读到 10，再各自写 11，最终还是 11；预期的 12 丢了一次更新。对共享不变量，选择一条明确的所有权规则：锁、原子操作、单一写入者消息循环，或数据库约束。数据库中的库存不能靠进程内锁在所有服务副本间保护。

为说明两个 worker 同时上报完成数量时的读—改—写竞态，这里把报表缩小为一个共享计数器。以下例子把一个 32 位计数器放进共享内存，用 `Atomics.add` 将读—改—写变成原子操作。每个 worker thread（工作线程）加 100,000 次，因此两者结束后应为 200,000。Node 用 structured clone（结构化克隆）传递普通对象；本例则通过 `SharedArrayBuffer` 明确共享计数器所依赖的内存。

~~~javascript
// 保存为 counter.cjs；使用 Node.js v26.13.0 运行
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

经典资源分配模型中的“不可抢占”指资源不会被系统强行收回，不是 OS 调度器不能抢占线程。若等待不会超时或取消、线程也不会在等待中放弃所持资源，那么在每类资源只有一个实例且实例互斥时，wait-for graph（等待图）出现环就能证明 deadlock（死锁）。图中节点是线程，A→B 表示 A 等待由 B 持有的资源。例如 A 持有 R1 并等待 B 持有的 R2，B 持有 R2 并等待 A 持有的 R1，就形成 A→B→A。

若资源有多个可互换实例，应看 resource-allocation graph（资源分配图）：资源类型节点标出各实例，请求边与分配边分别表示等待和持有；图中有环只是死锁的必要线索，不足以单独证明死锁。设只有一个 R1、两个可互换的 R2 实例：A 持 R1 并等待任一 R2，B 持 R2a 并等待 R1，C 持 R2b 但能独立完成；C 归还 R2b 后，A 可继续并释放 R1，随后 B 也可继续，尽管分配图中曾有环。经典资源模型把互斥、持有并等待、资源不可强行收回和循环等待列为死锁的必要条件；消除任一条件可预防这类死锁，但多个资源实例下四者同时出现仍不保证系统已死锁。

这些条件不是判断任意慢请求的打勾清单：请求等待 I/O 或 Promise 未完成本身不构成资源等待环，先找出实际的资源与依赖关系。浏览器中等待 `fetch` 的 Promise 不会持有 DOM 独占锁，event loop 可在其 pending 期间运行其他代码；但真实依赖环、永不完成的 Promise 或资源耗尽仍可能让应用停滞。按全局一致的顺序取得多把锁可阻止这类锁环；缩短临界区能减少持锁时间。不要在持锁期间等待不确定时长的网络调用。

## 取消信号能证明什么？

在许多应用级任务 API 中，cancellation（取消）是要求任务协作停止，而不是调用方已经证明任务结束。代码需按 API 语义观察取消、停止提交后续副作用，并通过 `finally` 或等价清理路径释放自己拥有的资源。以 POSIX 为例，新线程默认启用延迟取消；目标线程可更改取消状态或类型。取消仍启用时，延迟请求会在取消点处理，异步取消则可能在任意时刻处理。`pthread_cancel` 成功只说明请求已排入，不代表线程已终止。对 joinable thread（可 join 线程）调用 `pthread_join` 会等待其终止；函数本身返回 `0` 表示 join 成功，`PTHREAD_CANCELED` 是通过输出参数取得的线程退出值，只有它能确认目标线程因取消而结束。若取消的是等待方，底层线程、数据库操作或远端请求仍可能继续；已提交的写入也不会因此回滚。调用方应以持久化业务结果确认副作用，而不是把“本地任务已取消”当成“操作没有发生”。

**接下来：** 本章区分执行资源和共享状态；Node 章节把这些边界落实到 isolate、worker 和进程。异步作业何时接受、重试或显式取消见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - Linux 中 `fork()` 后父子进程有不同内存空间，`mmap()` 可建立显式共享映射：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)，`MAP_SHARED` / `MAP_PRIVATE`；2026-11-11 核对。
> - 阻塞 `read`、非阻塞时可能返回 EAGAIN、`poll` 等待描述符就绪，以及提交操作后收到完成通知：[Linux man-pages, read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)、[aio(7)](https://man7.org/linux/man-pages/man7/aio.7.html)，2026-11-11 核对。
> - POSIX 线程共享全局数据与堆、各自栈及线程状态：[Linux man-pages 6.19, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，2026-11-11 核对。
> - 子进程继承凭据和打开文件描述符的常见情况，以及可用 OS 策略限制文件与网络访问：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[Linux kernel, Landlock](https://docs.kernel.org/userspace-api/landlock.html)，2026-11-11 核对。
> - 延迟与异步线程取消、请求不等于终止：[Linux man-pages 6.19, pthread_cancel(3)](https://man7.org/linux/man-pages/man3/pthread_cancel.3.html)，2026-11-11 核对。
> - joinable thread 的终止状态，以及通过 `PTHREAD_CANCELED` 区分取消退出：[Linux man-pages 6.19, pthread_join(3)](https://man7.org/linux/man-pages/man3/pthread_join.3.html)，2026-11-11 核对。
> - Node worker 的 CPU 用途、共享内存选项与 worker 池建议：[Node.js v26.13.0, worker_threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，计数程序于该版本重放，输出 200000。
> - `worker.postMessage()` 的结构化克隆与转移列表：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html#workerpostmessagevalue-transferlist)，2026-11-12 核对。
> - Node 异步 zlib API 使用内部线程池，同步 API 除外：[Node.js v26.13.0, Zlib](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - 将控制权让回 Node 事件循环的 Promise 版 `setImmediate()`：[Node.js v26.13.0, Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html#timerspromisessetimmediatevalue-options)，2026-11-12 核对。
> - Node 文件 API 的异步执行方式：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)，核对于 2026-11-11。
> - Node.js v26.13.0 `fsPromises.writeFile()` 的 `AbortSignal` 只尽力取消内部缓冲，部分数据仍可能写入：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromiseswritefilefile-data-options)，2026-11-12 核对。
> - `fsPromises.rename()` 在 Promise 成功时完成名称变更；Linux 要求同一文件系统，目标已存在时会原子替换，因此本例使用专属目标名：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromisesrenameoldpath-newpath)，[Linux man-pages, rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)，2026-11-12 核对。
> - 经典资源分配死锁的互斥、持有并等待、不可抢占与循环等待条件，以及多实例图中环的限制：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks,” pp. 70–73](https://uobdv.github.io/Design-Verification/Supplementary/System_Deadlocks-Four_necessary_and_sufficient_conditions_for_deadlock.pdf)，2026-11-11 核对。
