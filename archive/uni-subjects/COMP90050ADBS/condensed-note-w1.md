# 存储与冗余如何共同影响数据库性能和可靠性？

先算数据库读取数据的时间，再看设备与通信发生故障后，副本、确认和恢复协议各能保住什么。概率与时间估算都从明确的失效和修复假设出发；各篇保留课程演算和配图。

## 阅读顺序

- [存储层级与缓冲如何影响数据库访问成本？](condensed-note-w1-storage-costs.md)
- [本课程比较哪些数据库类型与体系结构？](condensed-note-w1-database-architectures.md)
- [阵列可靠性计算如何依赖故障模型？](condensed-note-w1-redundancy-and-raid.md)
- [多数表决与故障即停模式分别能保证什么？](condensed-note-w1-fault-voting.md)
- [为什么消息确认仍可能导致重复处理？](condensed-note-w1-message-reliability.md)
- [双写与日志能保证什么，循环冗余校验又能证明什么？](condensed-note-w1-durable-writes-and-crc.md)

相关主线：[为什么连续扫描往往比链表遍历快？](../../../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md)、[事务隔离与预写日志能保证什么？](../../../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)、[请求超时后如何确认结果并安全重试？](../../../engineering-foundations/reliability/api-reliability-and-async-delivery.md)。
