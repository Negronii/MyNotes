# When is a wait cycle a deadlock? / 什么情况下等待环构成死锁？

A deadlock requires participants to form a cycle in which each waits for a resource held by another member. A slow operation or pending asynchronous request is not enough; identify the actual dependency graph. / 死锁要求参与者形成循环等待，每个参与者等待环中其他成员持有的资源。操作缓慢或异步请求尚未完成都不足以说明死锁；先确定真实依赖图。

## Deadlocks / 死锁

A deadlock is a state in which a set of processes or threads cannot proceed because each waits for a resource held by another member of the set. In the classic resource-allocation model, the four conditions are **mutual exclusion**, **hold and wait**, **no preemption**, and **circular wait**. For that model, breaking any one condition prevents deadlock; the conditions are not a checklist that makes every slow or waiting operation a deadlock.

Example: thread A locks resource `R1` and then waits for `R2`; thread B holds `R2` and waits for `R1`. Neither can release its first lock while blocked on the second. A consistent global lock order, shorter lock scopes, or avoiding nested locks can remove this cycle, depending on the design.

An asynchronous request waiting for I/O is not by itself a deadlock. JavaScript's event loop does not hold exclusive DOM access while a `fetch` is pending, and a Promise is a representation of eventual completion rather than a lock. An application can still stall because of a dependency cycle, an unresolved Promise, or exhausted resources; identify the actual dependency/resource graph before calling it a deadlock. For the corresponding operating-system view of process and thread waits, see [Processes, threads, and concurrency](../../engineering-foundations/operating-systems/processes-threads-and-concurrency.md).

## Related current note / 相关现行笔记

[Processes, Threads, and Concurrency](../../engineering-foundations/operating-systems/processes-threads-and-concurrency.md) explains the general process and thread wait model. / 进程、线程与并发笔记说明通用进程和线程等待模型。

## Sources / 参考资料

- Coffman, Elphick, and Shoshani (1971), [System Deadlocks](https://doi.org/10.1145/356586.356588), for the classic resource-allocation conditions.
