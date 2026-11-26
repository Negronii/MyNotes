# 事务规则与并发控制如何保持隔离？

本周从一次转账的事务边界出发，接着看并发操作为什么会互相干扰，以及锁、验证和多版本怎样裁决冲突。各章保留课程演算和原始图例；旧图与现行结论不一致的地方，在对应段落中说明。

## 阅读路线

- [扣款成功但入账失败时，事务边界与局部回滚怎样保护业务？](condensed-note-w3-transactions-and-nesting.md)
- [两个线程同时改写同一计数器时，怎样协调访问并处理死锁？](condensed-note-w3-concurrency-primitives-and-deadlocks.md)
- [一段交错执行能否等价于串行执行？](condensed-note-w3-conflict-histories-and-serializability.md)
- [两笔事务同时升级锁时为何会互等，隔离级别又保证什么？](condensed-note-w3-locks-and-isolation-levels.md)
- [乐观验证、快照隔离与时间戳排序怎样处理并发冲突？](condensed-note-w3-optimistic-snapshot-and-timestamp-concurrency.md)

这些机制也用于解释[事务隔离与预写日志能保证什么？](../../../engineering-foundations/data/transactions-and-isolation.md)和[何时选线程、进程或异步 I/O？](../../../engineering-foundations/runtime/processes-threads-and-async-io.md)。
