# How do databases preserve transactions across crashes and networked nodes? / 数据库如何在崩溃与网络节点之间保全事务？

Recovery preserves durable committed work and finishes reversing incomplete work. WAL and ARIES use ordered logs, transaction/page state, checkpoints, redo, and undo; replication and failover add network and ownership questions. Two-phase commit coordinates one global commit-or-abort result but does not provide isolation and may leave prepared participants waiting. / 恢复保留已持久化的提交并完成撤销未完成工作。WAL 和 ARIES 使用有序日志、事务/页状态、检查点、重做与撤销；复制和故障切换另有网络与权威归属问题。两阶段提交协调唯一全局提交或中止结果，但不提供隔离，并可能使 prepared 参与者等待。

## Week question map / 本周问题地图

- [How does WAL and ARIES recovery preserve committed work after a crash? / WAL 与 ARIES 恢复如何在崩溃后保留已提交工作？](condensed-note-w4-wal-and-aries-recovery.md)
- [How do remote backup and shadow paging handle failure? / 远程备份与影子分页如何处理故障？](condensed-note-w4-backup-and-shadow-paging.md)
- [What do CAP, consistency models, and PACELC say about distributed services? / CAP、一致性模型与 PACELC 如何描述分布式服务？](condensed-note-w4-distributed-consistency-and-nosql.md)
- [How do data warehouses collect, integrate, and summarize source data? / 数据仓库如何采集、整合并汇总源数据？](condensed-note-w4-data-warehousing.md)
- [How does two-phase commit reach one outcome across participants? / 两阶段提交如何让多个参与者得到同一结果？](condensed-note-w4-two-phase-commit-and-replicated-data.md)

Use [transaction isolation and WAL / 事务隔离与 WAL](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md) for the general guarantees. The questions above work through the course's ARIES recovery and distributed-systems exercises. / 通用保证见[事务隔离与 WAL](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)；上面各篇保留课程里的 ARIES 恢复与分布式系统演算。
