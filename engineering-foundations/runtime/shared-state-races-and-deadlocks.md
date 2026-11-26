# 多个执行者共享状态时，怎样不丢更新、不互相卡死？

本章回答两个问题：两个执行者同时修改同一份状态时，为什么会丢掉一次更新，应该用什么规则避免；多个执行者互相等待时，什么情况才真的构成死锁，怎样预防。读者手上有[上一章](processes-threads-and-async-io.md)的结论：线程共享进程地址空间，进程默认不共享，异步等待不占线程。

主线二的导出案例里，共享状态出现在 `job-demo-731` 的协调代码中：取消和发布都想改这次 attempt 的状态。那个裁决要等流一章讲完部分输出后才看得清，所以本章先换一个更小的独立例子：两个 worker 线程各把同一个计数器加 100,000 次，最后应该得到 200,000。

## 读-改-写为什么会丢更新？

race condition (竞态) 指结果取决于并发操作的先后顺序。`count += 1` 看起来是一条语句，实际上是三步：读出当前值、加一、写回。若两个线程都先读到 10，再各自写回 11，最终是 11，预期的 12 少了一次。这种错误叫 lost update (丢更新)。

在 Node 里，两个 `worker_threads` 默认不共享普通对象；要让它们改同一个计数器，必须用 `SharedArrayBuffer` 显式共享一块内存。下面的程序让两个 worker 各加 100,000 次：

~~~javascript
// 保存为 counter.cjs；node counter.cjs plain 或 node counter.cjs atomic
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const mode = process.argv[2] ?? 'atomic';
  const workers = Array.from({ length: 2 }, () =>
    new Worker(__filename, { workerData: { shared, mode } }));
  Promise.all(workers.map(worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => code === 0 ? resolve() : reject(new Error(`exit ${code}`)));
  }))).then(() => console.log(Atomics.load(new Int32Array(shared), 0)));
} else {
  const counter = new Int32Array(workerData.shared);
  for (let i = 0; i < 100_000; i++) {
    if (workerData.mode === 'plain') counter[0]++;    // 读、加一、写回三步
    else Atomics.add(counter, 0, 1);                 // 一次不可分割的读-改-写
  }
}
~~~

`plain` 模式每次运行的结果都可能不同，多数运行小于 200,000（例如 162,339），偶尔恰好等于 200,000。恰好正确的那一次并不说明代码没问题，只说明这一次两个线程的交错没有撞上。`atomic` 模式用 `Atomics.add` 把读-改-写变成一个不可分割的操作，每次都输出 200,000。这个程序只验证正确性，不说明多开 worker 会让计数变快。

## 共享不变量要选哪种所有权规则？

修复丢更新，不是给每处修改都“加点同步”，而是为每个共享不变量明确选定**一种**所有权规则：谁有权修改它，修改怎样被串行化。

| 所有权规则 | 怎样避免丢更新 | 适用范围与限制 |
| --- | --- | --- |
| 锁（mutex） | 同一时刻只有持锁者执行临界区 | 只在共享同一把锁的执行者之间有效；持锁时间越长，等待越多，还可能形成死锁（见下一节） |
| 原子操作 | 硬件或运行时保证一次读-改-写不可分割 | 只适合能用单个原子操作表达的小状态，例如计数、标志位 |
| 单写者消息循环 | 只有一个执行者能改状态，其他执行者发消息请求修改，由它按顺序处理 | Node 事件循环天然是单写者：同一线程上的回调不会交错执行；代价是所有修改都排在这个循环上 |
| 数据库约束与条件写 | 数据库在一条语句内检查条件并修改，返回受影响行数，由数据库裁决谁赢 | 适合跨进程、跨副本的持久状态；需要按语句设计条件，并把返回行数当作业务判断 |

单写者规则有一个容易漏掉的前提：读、改、写必须在同一段同步代码里完成。若先读出状态、`await` 一次查询、再写回，等待期间别的回调可以插进来改同一份状态，丢更新照样发生。

表中最后一行（数据库约束与条件写）之所以必要，是因为进程内的锁只对共享这把锁的线程有效。服务通常运行多个副本，job 状态这类保存在数据库里的共享状态，别的副本根本看不到你的锁。主线三的结论是：把条件写进 `UPDATE ... WHERE` 本身，让数据库在同一条语句里检查并修改，返回 0 行就说明别人已经先改了，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](../data/conditional-writes-and-idempotent-records.md)。跨副本还有一个更隐蔽的问题：一个 worker 的租约过期后，它自己可能还在运行并试图写结果；主线四用一个单调递增的 attempt 编号，在提交结果时检查“我仍是当前 attempt”，挡住旧执行者，见[怎样保证一个任务同一时刻只由一个 worker 推进？](../services/job-claims-leases-and-fencing.md)。

回到 `job-demo-731`：取消与发布由同一事件循环上的一个协调者串行裁决，这就是单写者规则；它保护的是进程内的 attempt 状态。job 在数据库里的状态则交给条件写和 attempt 栅栏。

## 等待环何时才构成死锁？

另一类共享问题是互相等待。为了判断，先把“谁在等谁”画成图。

**每类资源只有一个实例时，看 wait-for graph (等待图)。** 节点是线程，边 A→B 表示 A 在等 B 持有的资源。下面 A 持有 R1、等 R2，B 持有 R2、等 R1，形成环 A→B→A：

~~~mermaid
flowchart LR
    A[线程 A<br/>持有 R1] -->|等待 R2| B[线程 B<br/>持有 R2]
    B -->|等待 R1| A
~~~

如果等待不会超时、不会被取消，线程也不会在等待中放弃已持有的资源，而且每类资源只有一个互斥实例，那么等待图中出现环就**证明**发生了 deadlock (死锁)。

**资源有多个可互换实例时，看 resource-allocation graph (资源分配图)。** 节点分为线程和资源类型，资源类型节点内标出各个实例；请求边表示等待，分配边表示持有。这时图里有环只是死锁的必要线索，不足以证明死锁。设 R1 只有一个实例，R2 有两个可互换的实例 R2a、R2b：

~~~mermaid
flowchart LR
    A[线程 A] -->|请求任一 R2| R2[(R2：R2a、R2b)]
    R2 -->|R2a 分配给| B[线程 B]
    R2 -->|R2b 分配给| C[线程 C<br/>不等待任何资源]
    B -->|请求| R1[(R1)]
    R1 -->|分配给| A
~~~

A→R2→B→R1→A 构成环，但 C 不等待任何资源，能独立完成。C 归还 R2b 后，A 拿到 R2b 继续执行并释放 R1，B 随后也能继续。曾经出现的环自行解开了。

经典资源模型（Coffman 等，1971）列出死锁的四个必要条件：

1. mutual exclusion (互斥)：资源一次只能由一个执行者持有。
2. hold and wait (持有并等待)：执行者持有资源的同时等待别的资源。
3. no preemption (不可抢占)：资源不会被系统强行收回，只能由持有者主动释放。这里说的是资源，不是“操作系统调度器不能抢占线程”。
4. circular wait (循环等待)：存在一个等待环。

破坏其中任意一个条件，就能预防这类死锁；但在多实例资源下，四个条件同时出现仍不保证已经死锁，上面的 R2 例子就是如此。

## 等待 Promise 为什么不是资源环，怎样预防死锁？

这四个条件不是用来给任意“慢请求”打勾的清单。请求在等 I/O，或者一个 Promise 尚未完成，本身并不构成资源等待环。例如浏览器里等待 `fetch` 的 Promise 不持有 DOM 的独占锁，事件循环在它 pending 期间照样运行其他代码。判断前先找出真实的资源与依赖关系。

但应用照样可能停住，原因换成了别的：真实的依赖环（A 等 B 的结果，B 又等 A 的结果）、永不完成的 Promise，或资源耗尽。最常见的资源耗尽是连接池：每个请求都持有一个连接，又在等另一个连接，池用完后所有请求一起等，直到池等待超时。怎样找到占着连接的人，见[池超时之后，怎样找到占着连接的人？](../data/orm-sessions-and-connection-pools.md#池超时之后，怎样找到占着连接的人？)。

预防锁环的做法有三条：

- 需要多把锁时，所有代码按同一个全局顺序获取，破坏循环等待。
- 缩短临界区，减少持锁时间。
- 不要在持锁期间等待时长不确定的网络调用。

## 下一步：单写者循环怎样排队

本章的产出是一条规则：每个共享不变量只选一种所有权规则，进程内状态用锁、原子操作或单写者循环，跨副本的持久状态交给数据库条件写和 attempt 栅栏；死锁先按资源实例数选对图，再判断环是否足以证明。Node 选择的是单写者路线：一条线程、一个事件循环，回调一个接一个地运行。下一章看这个循环[怎样安排计时器、I/O 回调和微任务](node-event-loop-and-microtasks.md)。

> [!info]- 来源
> - `SharedArrayBuffer` 共享内存、`Atomics` 原子操作与 worker 间结构化克隆：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，2026-11-12 核对；计数程序 `atomic` 模式于 v26.13.0 与 v26.13.1 输出 200000，`plain` 模式于 Node.js v26.13.1 多次运行，多数小于 200000。
> - 共享字节区须用原子操作或明确交接访问权：[ECMAScript Shared Memory Guidelines](https://tc39.es/ecma262/multipage/memory-model.html#sec-shared-memory-guidelines)，2026-11-12 核对。
> - 死锁的互斥、持有并等待、不可抢占、循环等待四条件，单实例与多实例资源图中环的含义：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks,” pp. 70–73](https://uobdv.github.io/Design-Verification/Supplementary/System_Deadlocks-Four_necessary_and_sufficient_conditions_for_deadlock.pdf)，2026-11-11 核对。
