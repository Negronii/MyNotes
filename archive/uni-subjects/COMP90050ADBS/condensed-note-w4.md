# 数据库如何在崩溃与网络节点之间保全事务？

恢复用于保留已持久化的提交，并完成撤销未提交事务。WAL 与 ARIES 依靠有序日志、事务和页面状态、检查点、重做与撤销；复制和故障切换还涉及网络条件与数据权威归属。两阶段提交协调所有参与者得到同一提交或中止结果，但不提供隔离，并可能让已准备的参与者等待。

## 本周问题地图

- [崩溃后，数据库如何重做已提交工作并撤销未完成事务？](condensed-note-w4-wal-and-aries-recovery.md)
- [站点故障怎样切换，影子分页又怎样提交事务？](condensed-note-w4-backup-and-shadow-paging.md)
- [网络分区时系统能保证什么，非关系型数据库又按什么模型区分？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [数据仓库怎样把多源业务数据整理成可分析的历史数据？](condensed-note-w4-data-warehousing.md)
- [多个参与者怎样取得同一事务结果，副本又怎样等价于一份数据？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

通用保证见[事务隔离与预写日志能保证什么？](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)；上面各篇保留课程中的 ARIES 恢复与分布式系统演算。
