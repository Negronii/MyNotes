# COMP90050 高级数据库系统回答哪些问题？

COMP90050 围绕访问成本、查询执行、并发控制和故障恢复展开。按下面四周的顺序阅读，可继续进入各主题的推导、算例和配图。

## 课程顺序

### [存储与冗余如何共同影响数据库性能和可靠性？](condensed-note-w1.md)

- [存储层级与缓冲如何影响数据库访问成本？](condensed-note-w1-storage-costs.md)
- [本课程比较哪些数据库类型与体系结构？](condensed-note-w1-database-architectures.md)
- [阵列可靠性计算如何依赖故障模型？](condensed-note-w1-redundancy-and-raid.md)
- [多数表决与 fail-fast 模式分别能保证什么？](condensed-note-w1-fault-voting.md)
- [为什么消息确认仍可能导致重复处理？](condensed-note-w1-message-reliability.md)
- [双写与日志能保证什么，循环冗余校验又能证明什么？](condensed-note-w1-durable-writes-and-crc.md)

### [查询如何从关系代数转为可估算成本的物理计划？](condensed-note-w2.md)

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

- [崩溃后，数据库如何重做已提交工作并撤销未完成事务？](condensed-note-w4-wal-and-aries-recovery.md)
- [站点故障怎样切换，影子分页又怎样提交事务？](condensed-note-w4-backup-and-shadow-paging.md)
- [网络分区时系统能保证什么，非关系型数据库又按什么模型区分？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [数据仓库怎样把多源业务数据整理成可分析的历史数据？](condensed-note-w4-data-warehousing.md)
- [多个参与者怎样取得同一事务结果，副本又怎样等价于一份数据？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

## 阅读边界

通用机制可以先从[SQL 空值、连接与分组会怎样改变报表 42 的结果？](../../../engineering-foundations/databases/sql-null-joins-and-aggregates.md)、[如何用约束保护业务规则并为读取建立索引？](../../../engineering-foundations/databases/database-constraints-and-indexes.md)、[事务隔离与预写日志能保证什么？](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)进入；[两个请求争夺最后一件库存时，怎样保证只预留一次？](../../../engineering-foundations/databases/database-fundamentals.md)串起库存约束、并发提交与结果恢复；报表 SQL 另用客户与订单数据演算查询结果。
