# 事务规则与并发控制如何保持隔离？

从一次转账的事务边界出发，再看并发操作为什么互相影响，以及锁、验证和版本如何裁决冲突。各章保留课程演算和原始图例；旧图与当前结论的差异在对应段落说明。

## 阅读路线

- [扣款成功但入账失败时，事务边界与局部回滚怎样保护业务？](condensed-note-w3-transactions-and-nesting.md)
- [两个线程同时改写同一计数器时，怎样协调访问并处理死锁？](condensed-note-w3-concurrency-primitives-and-deadlocks.md)
- [一段交错执行能否等价于串行执行？](condensed-note-w3-conflict-histories-and-serializability.md)
- [两笔事务同时升级锁时为何会互等，隔离级别又保证什么？](condensed-note-w3-locks-and-isolation-levels.md)
- [乐观验证、快照隔离与时间戳排序怎样处理并发冲突？](condensed-note-w3-optimistic-snapshot-and-timestamp-concurrency.md)

这些机制也用于解释[库存事务的隔离与恢复](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)和[进程、线程之间的协调](../../../engineering-foundations/operating-systems/processes-threads-and-concurrency.md)。
