# 什么情况下等待环构成死锁？

**案例背景：** 线程 A 已持有 R1，再等待 R2；线程 B 已持有 R2，再等待 R1。若两者都必须取得第二把锁才能继续并释放第一把锁，就没有一方能独自推进。完整的进程与线程模型见[等待环何时才构成死锁？](../../engineering-foundations/operating-systems/processes-threads-and-concurrency.md#等待环何时才构成死锁)，这里保留资源锁与异步等待的判别例。

## 先找实际资源依赖，再判断能否推进

经典资源分配模型中的四个必要条件是 mutual exclusion（互斥）、hold and wait（持有并等待）、no preemption（不可抢占）和 circular wait（循环等待）。破坏其中一个可防止该模型中的死锁；条件成立还要结合资源实例数和实际分配判断，不能看到任何环就一概断言死锁。每种资源只有一个实例的锁例中，A→B→A 的等待环足以说明双方不能推进。

为所有线程规定相同的全局加锁次序，或重新设计以避免同时持有两把锁，可以消除这类循环。缩短持锁时间能降低争用，但单纯“持得更短”并不证明已消除所有可能的加锁顺序。

## pending 的 fetch 为什么不是 DOM 死锁？

等待 I/O 的异步请求本身不持有独占 DOM 锁。JavaScript 的 event loop（事件循环）可以在 `fetch` 等待期间处理其他回调；Promise 表示将来的完成状态，不是资源锁。页面停住也可能来自永不结算的 Promise、任务相互依赖、资源耗尽或同步计算占住线程。要称为死锁，必须具体指出谁持有什么、又在等待谁，以及为什么没有参与者能够推进。

> [!info]- 来源
> - 经典资源分配与死锁条件：Coffman, Elphick, and Shoshani (1971), [System Deadlocks](https://doi.org/10.1145/356586.356588)。
> - 异步请求与主线程调度的现代机制见[事件循环正文](../../frontend/runtime/event-loop.md)，Promise 与锁是不同抽象。
