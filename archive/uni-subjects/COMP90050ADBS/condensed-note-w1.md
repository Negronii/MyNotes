# How do storage and redundancy shape database performance and reliability? / 存储与冗余如何共同影响数据库性能和可靠性？

Database work has two related but distinct costs: the time to reach and transfer data, and the risk that failure prevents correct service or loses durable state. Access estimates depend on the layer being modelled; reliability estimates depend on explicit failure and repair assumptions. Week 1 moves from disk and memory examples to RAID, voting, message retries, durable writes, and CRC. / 数据库工作有两个相关但不同的成本：访问与传输数据所需的时间，以及故障阻止正确服务或丢失持久状态的风险。访问估算取决于所建模的层；可靠性估算取决于明确的故障与修复假设。第一周从磁盘与内存示例，延伸到 RAID、投票、消息重试、持久写入和 CRC。

Each question below is a full course explanation; the pages retain their worked examples, assumptions, and original relative figures. / 以下每篇都是完整课程解释，并保留演算、前提与原始相对图片链接。

## Week question map / 本周问题地图

- [How do storage hierarchy and buffers shape database access cost? / 存储层级与缓冲如何影响数据库访问成本？](condensed-note-w1-storage-costs.md)
- [What database types and architectures does this course compare? / 本课程比较哪些数据库类型与体系结构？](condensed-note-w1-database-architectures.md)
- [How do RAID reliability calculations depend on their failure model? / RAID 可靠性计算如何依赖故障模型？](condensed-note-w1-redundancy-and-raid.md)
- [What does module voting guarantee under failvote and failfast? / failvote 与 failfast 的模块投票能保证什么？](condensed-note-w1-fault-voting.md)
- [Why can acknowledgements still lead to duplicate message effects? / 为什么消息确认仍可能导致重复处理？](condensed-note-w1-message-reliability.md)
- [What can duplex writes, logs, and CRC actually guarantee? / 双写、日志与 CRC 实际能保证什么？](condensed-note-w1-durable-writes-and-crc.md)

Related current explanations: [Memory Hierarchy and Data Locality](../../../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md), [Database Fundamentals](../../../engineering-foundations/databases/database-fundamentals.md), and [API Reliability and Asynchronous Delivery](../../../engineering-foundations/reliability/api-reliability-and-async-delivery.md). / 相关通用说明：内存层次与局部性、数据库基础、API 可靠性与异步交付。
