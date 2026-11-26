# 数据库如何在崩溃与网络节点之间保全事务？

本周从单机崩溃讲到多站点协作。崩溃恢复要保住已确认的提交，并撤销未提交的事务：WAL 与 ARIES 依靠有序日志、事务与页面状态、检查点以及重做和撤销完成这件事。复制和故障切换还要考虑网络状况，以及哪个站点有权写入。两阶段提交让所有参与者得到同一个提交或中止结果，但它不提供隔离，还可能让已准备的参与者长时间等待。

## 本周问题地图

- [崩溃后，数据库如何重做已提交工作并撤销未完成事务？](condensed-note-w4-wal-and-aries-recovery.md)
- [站点故障怎样切换，影子分页又怎样提交事务？](condensed-note-w4-backup-and-shadow-paging.md)
- [网络分区时系统能保证什么，非关系型数据库又按什么模型区分？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [数据仓库怎样把多源业务数据整理成可分析的历史数据？](condensed-note-w4-data-warehousing.md)
- [多个参与者怎样取得同一事务结果，副本又怎样等价于一份数据？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

通用保证见[事务隔离与预写日志能保证什么？](../../../engineering-foundations/data/transactions-and-isolation.md)；各篇保留相应的课程演算。数据仓库另讨论多源历史数据的分析模型，不属于事务崩溃恢复的下一步骤。
