# COMP90050 高级数据库系统回答哪些问题？

COMP90050 围绕访问成本、查询执行、并发控制和故障恢复展开。按下面四周的顺序阅读，可继续进入各主题的推导、算例和配图。

## 课程顺序

### [存储与冗余如何共同影响数据库性能和可靠性？](condensed-note-w1.md)

- [存储层级与缓冲如何影响数据库访问成本？](condensed-note-w1-storage-costs.md)
- [本课程比较哪些数据库类型与体系结构？](condensed-note-w1-database-architectures.md)
- [阵列可靠性计算如何依赖故障模型？](condensed-note-w1-redundancy-and-raid.md)
- [多数表决与故障即停模式分别能保证什么？](condensed-note-w1-fault-voting.md)
- [为什么消息确认仍可能导致重复处理？](condensed-note-w1-message-reliability.md)
- [双写与日志能保证什么，循环冗余校验又能证明什么？](condensed-note-w1-durable-writes-and-crc.md)

### [查询如何转化为可估算成本的物理计划？](condensed-note-w2.md)

- [关系代数和连接算法怎样把查询变成可估算的页访问？](condensed-note-w2-query-algebra-and-join-cost.md)
- [查询优化器怎样在等价计划之间作选择？](condensed-note-w2-query-plan-optimization.md)
- [索引怎样降低查找成本，又增加哪些维护工作？](condensed-note-w2-index-structures.md)
- [空间索引如何缩小搜索范围，又不漏掉几何结果？](condensed-note-w2-spatial-indexes.md)
- [这些索引语句和物理规则哪些只适用于 SQL Server？](condensed-note-w2-sql-server-index-examples.md)

### [事务规则与并发控制如何保持隔离？](condensed-note-w3.md)

- [扣款成功但入账失败时，事务边界与局部回滚怎样保护业务？](condensed-note-w3-transactions-and-nesting.md)
- [两个线程同时改写同一计数器时，怎样协调访问并处理死锁？](condensed-note-w3-concurrency-primitives-and-deadlocks.md)
- [一段交错执行能否等价于串行执行？](condensed-note-w3-conflict-histories-and-serializability.md)
- [两笔事务同时升级锁时为何会互等，隔离级别又保证什么？](condensed-note-w3-locks-and-isolation-levels.md)
- [乐观验证、快照隔离与时间戳排序怎样处理并发冲突？](condensed-note-w3-optimistic-snapshot-and-timestamp-concurrency.md)

### [数据库如何在崩溃与网络节点之间保全事务？](condensed-note-w4.md)

- [WAL 与 ARIES 恢复如何在崩溃后保留已提交工作？](condensed-note-w4-wal-and-aries-recovery.md)
- [远程备份与影子分页如何处理故障？](condensed-note-w4-backup-and-shadow-paging.md)
- [CAP、一致性模型与 PACELC 如何描述分布式服务？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [数据仓库如何采集、整合并汇总源数据？](condensed-note-w4-data-warehousing.md)
- [两阶段提交如何让多个参与者得到同一结果？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

## 阅读边界

通用机制可以先从[SQL 查询结果](../../../engineering-foundations/databases/sql-null-joins-and-aggregates.md)、[约束与索引](../../../engineering-foundations/databases/database-constraints-and-indexes.md)、[事务与恢复](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)进入；[最后一件库存](../../../engineering-foundations/databases/database-fundamentals.md)将这些机制串在同一个应用中。
