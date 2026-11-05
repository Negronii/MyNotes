# Which questions does COMP90050 Advanced Database Systems answer? / COMP90050 高级数据库系统回答哪些问题？

COMP90050 studies access cost, query execution, concurrency, and recovery across failures and networked nodes. This path preserves the course title and sequence; the four weekly maps link to detailed explanations, calculations, exam IDs, citations, and original figures. The former aggregate had no substantive topic beyond the weekly notes. / COMP90050 学习访问成本、查询执行、并发控制以及跨故障和网络节点的恢复。此路径保留课程标题和顺序；四篇周次地图链接到详细解释、计算、考试题号、引用与原始图片。此前 aggregate 不含周记之外的实质主题。

## Course sequence / 课程顺序

### [How do storage and redundancy shape database performance and reliability? / 存储与冗余如何共同影响数据库性能和可靠性？](condensed-note-w1.md)

- [How do storage hierarchy and buffers shape database access cost? / 存储层级与缓冲如何影响数据库访问成本？](condensed-note-w1-storage-costs.md)
- [What database types and architectures does this course compare? / 本课程比较哪些数据库类型与体系结构？](condensed-note-w1-database-architectures.md)
- [How do RAID reliability calculations depend on their failure model? / RAID 可靠性计算如何依赖故障模型？](condensed-note-w1-redundancy-and-raid.md)
- [What does module voting guarantee under failvote and failfast? / failvote 与 failfast 的模块投票能保证什么？](condensed-note-w1-fault-voting.md)
- [Why can acknowledgements still lead to duplicate message effects? / 为什么消息确认仍可能导致重复处理？](condensed-note-w1-message-reliability.md)
- [What can duplex writes, logs, and CRC actually guarantee? / 双写、日志与 CRC 实际能保证什么？](condensed-note-w1-durable-writes-and-crc.md)

### [How does a query become a physical plan with measurable cost? / 查询如何转化为可估算成本的物理计划？](condensed-note-w2.md)

- [How do relational algebra and join algorithms turn queries into I/O work? / 关系代数与连接算法如何把查询转化为 I/O 工作？](condensed-note-w2-query-algebra-and-join-cost.md)
- [How does a query optimizer compare equivalent plans? / 查询优化器如何比较等价计划？](condensed-note-w2-query-plan-optimization.md)
- [How do database indexes trade lookup cost against update and storage cost? / 数据库索引如何权衡查找、更新与存储成本？](condensed-note-w2-index-structures.md)
- [How do spatial indexes find candidates for geometric queries? / 空间索引如何为几何查询筛选候选对象？](condensed-note-w2-spatial-indexes.md)
- [Which index statements here are specific to SQL Server? / 此处哪些索引语句专属于 SQL Server？](condensed-note-w2-sql-server-index-examples.md)

### [How do transaction rules and concurrency control preserve isolation? / 事务规则与并发控制如何保持隔离？](condensed-note-w3.md)

- [What do transaction boundaries, savepoints, and nested transactions mean? / 事务边界、保存点与嵌套事务意味着什么？](condensed-note-w3-transactions-and-nesting.md)
- [How do synchronization primitives coordinate access and avoid deadlock? / 同步原语如何协调访问并避免死锁？](condensed-note-w3-concurrency-primitives-and-deadlocks.md)
- [How does a precedence graph test a transaction history? / 如何用优先图判断事务历史？](condensed-note-w3-conflict-histories-and-serializability.md)
- [What do shared, exclusive, and granular locks guarantee? / 共享锁、排他锁与粒度锁能保证什么？](condensed-note-w3-locks-and-isolation-levels.md)
- [When do optimistic validation and snapshot isolation allow concurrent updates? / 乐观验证与快照隔离何时允许并发更新？](condensed-note-w3-optimistic-snapshot-and-timestamp-concurrency.md)

### [How do databases preserve transactions across crashes and networked nodes? / 数据库如何在崩溃与网络节点之间保全事务？](condensed-note-w4.md)

- [How does WAL and ARIES recovery preserve committed work after a crash? / WAL 与 ARIES 恢复如何在崩溃后保留已提交工作？](condensed-note-w4-wal-and-aries-recovery.md)
- [How do remote backup and shadow paging handle failure? / 远程备份与影子分页如何处理故障？](condensed-note-w4-backup-and-shadow-paging.md)
- [What do CAP, consistency models, and PACELC say about distributed services? / CAP、一致性模型与 PACELC 如何描述分布式服务？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [How do data warehouses collect, integrate, and summarize source data? / 数据仓库如何采集、整合并汇总源数据？](condensed-note-w4-data-warehousing.md)
- [How does two-phase commit reach one outcome across participants? / 两阶段提交如何让多个参与者得到同一结果？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

## Reading boundary / 阅读边界

For the general mechanisms, start with [SQL query results / SQL 查询结果](../../../engineering-foundations/databases/sql-null-joins-and-aggregates.md), [constraints and indexes / 约束与索引](../../../engineering-foundations/databases/database-constraints-and-indexes.md), or [transactions, isolation, and recovery / 事务、隔离与恢复](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md). Use the [last inventory unit / 最后一件库存](../../../engineering-foundations/databases/database-fundamentals.md) to see those mechanisms work together in one application.
