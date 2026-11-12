# 网络分区时系统能保证什么，非关系型数据库又按什么模型区分？

一个航班还剩 1 个座位，两个机房 A、B 各保存一个副本。A 与 B 之间的网络断开；A 收到一笔预订，把余票改为 0 并向客户返回完成。随后，B 上的另一个客户查询余票。读者要判断：B 若立刻返回 1，系统还满足什么一致性？若它等 A 恢复通信，服务又放弃了什么保证？回答前还要分清：CAP（Consistency, Availability, Partition tolerance，一致性、可用性与分区容错）讨论副本的行为契约；NoSQL（非关系型数据库，常解释为 Not Only SQL，即“不止 SQL”）讨论的是数据模型，两者不是同一组标签。

## CAP 的取舍为什么只在分区时出现？

CAP 定理关注网络分区期间的一项限制：一个分布式对象不能同时保证 linearizability（线性一致性）和让每个到达非故障节点的合法读写操作最终完成的 availability（可用性）。

一致性不是“数据库约束都满足”的 ACID consistency（ACID 一致性），而是线性一致性：每个操作都能看成在调用与返回之间某个瞬间完成，并且所有操作服从一个全局顺序；若写入已经返回，之后开始的读取必须看到它或更新的值。

在上面的例子里，A 已向客户返回“预订成功”，之后 B 才收到读取请求。因此若 B 在断网期间返回旧值“余票 1”，就不存在符合真实时间先后的单一操作顺序，线性一致性被破坏。这一次旧读足以排除线性一致性，但仍可能发生在最终一致系统中；单次旧值不能证明副本以后会收敛，也不能证明因果或会话保证。B 只看到本地状态，无法区分两个执行：一是 A 已将余票改为 0、只是更新没传到 B；二是预订写入根本没到 A，因而尚未发生。前一种执行要求返回 0，后一种要求返回 1，B 无法在两者中都正确。

形式模型允许分区持续任意久；若 B 必须在有限时间内完成读，它就可能破坏线性一致性；若它等待 A 恢复，而分区没有恢复时限，它就不能保证该读最终完成。只返回网络错误并没有给读操作返回有效的对象值，不能据此声称读保持了可用性。下单操作则可以按业务约定正常返回“售罄”等结果；这和把一个过时余票当作成功读到的当前值不同。

> [!info] CAP 中的三个词
> - 一致性 C：上文定义的线性一致性。
> - 可用性 A：形式模型要求每个到达非故障节点的合法操作最终完成；它不保证每笔业务交易都成功，但完成的结果仍须符合该操作的定义。
> - 分区容错 P：即使节点之间的消息被丢失、网络分成互不通信的部分，系统仍要遵循所定义的行为。P 描述要面对的故障模型，并不是可从真实网络中删除的一项能力。

所以，“CP”或“AP”只是说明某个系统在模型中的选择，并不意味着一个产品在所有请求、运行时段和数据上永远只有一种标签。分区实际发生时，要么延迟或拒绝部分操作而避免返回违反契约的状态，要么让部分副本继续完成操作、接受更弱的结果；是否可拒绝、是否能安全重试，都还要回到应用契约。

## 分区之外还要比较什么？

即使网络没有分区，强一致性也可能需要跨副本协调，增加请求往返时间；没有网络分区时，CAP 定理本身不限制系统能提供的能力，节点故障和延迟仍要按具体协议分析。PACELC 把这一点与 CAP 放进同一问题：若发生分区（P），在可用性（A）和一致性（C）之间如何取舍；否则（E），在较低延迟（L）和一致性（C）之间如何取舍。

| 记号 | 分区时的取舍 | 无分区时的取舍 |
| --- | --- | --- |
| PA/EL | 偏向继续响应 | 偏向低延迟 |
| PC/EC | 偏向一致结果 | 偏向一致结果 |
| PA/EC | 偏向继续响应 | 偏向一致结果 |
| PC/EL | 偏向一致结果 | 偏向低延迟 |

这些记号用于描述设计取舍，不足以单独判断某个产品的每类操作：读、写、范围查询、单区和跨区请求可能有不同协议。

## 应用需要的“一致”是哪一种？

不同应用关心的顺序范围不同，选模型时要说清对象和操作：

- linearizability（线性一致性）要求一组操作服从尊重真实时间的全局顺序。它便于把分布式对象理解成单个最新值，但跨副本协调可能增加延迟或使分区侧等待。
- eventual consistency（最终一致性）要求在不再有新更新且已接受的更新最终能传播的条件下，副本最终收敛；收敛前读取可能看到旧值。
- causal consistency（因果一致性）保证有因果依赖的操作按因果顺序可见；并发且互不依赖的更新可以有不同观察顺序。
- session guarantees（会话保证）描述一个客户端会话可依赖的特性，例如 read-your-writes（读己之写）、monotonic reads（单调读）和 monotonic writes（单调写入）。它们不等于整个系统上所有操作都线性一致。

回到座位预订例子，浏览列表可以显示短暂过时的余票；真正下单时，必须由唯一持有写入权的一侧原子预留最后一个座位，或由副本先达成一项共同决定。若下单节点无法联系持有写入权的一侧，它应延迟或拒绝下单，而不能只在本地再次读取余票并确认；否则两个节点各自重查到 1，仍会超卖。产品目录、购物车、结账和物流记录也可以有不同契约，因此应逐个服务和数据对象说明保证，而不是给整个应用贴一个 CAP 标签。

BASE 是有时用于描述偏好高可用和异步收敛设计的非正式助记词：Basically Available（基本可用）、Soft state（软状态）、Eventual consistency（最终一致性）。它不是 CAP 定理的推论，也不是 NoSQL 产品必须遵守的统一协议。

## NoSQL 的几类数据模型怎样配合访问方式？

NoSQL 不是一种固定数据结构或一致性协议。产品可以在不同数据模型上提供查询、事务、复制和一致性选项；分类名称不能替代产品文档里的具体保证。

| 数据模型 | 数据怎样组织 | 适合先考虑的问题 | 使用成本 |
| --- | --- | --- | --- |
| document（文档型） | 一条记录以带字段和值的文档保存，字段可包含嵌套对象或数组 | 一个业务对象常以整体读写，字段结构会变化吗？ | 嵌套、重复字段和跨文档约束如何维护？ |
| graph（图型） | 节点表示实体，边表示关系；两者可带属性 | 查询是否经常沿多跳关系遍历，例如“共同购买的商品”或两节点间的最短路径？ | 图查询路径、节点度数和事务范围如何控制？ |
| key-value（键值型） | 用键定位值，值可以是简单或结构化数据 | 主要请求能否由已知键直接定位？ | 复杂过滤、关系查询和多键事务是否需要额外能力？ |
| wide-column / column-family（宽列/列族型） | 按 row key 或 partition key 定位行，相关列按 family 组织；具体键和列规则取决于产品 | 查询能否按行键/分区键定位，范围能力是否符合访问路径？ | 热分区、跨分区查询、重复存储 |

具体的宽列产品使用不同 schema。Cassandra 的 CQL `CREATE TABLE` 先定义表的列；primary key 可以只有 partition key，此时每个 partition 只有一行，clustering columns 是可选的，用来定义同一 partition 内多行的组织和排序。Bigtable 则由 row key 定位行，列由 column family 与 qualifier 标识；qualifier 可只出现在部分行，所以表是 sparse，不要求 Cassandra 式 clustering key。

“宽列数据库”不要与 columnar storage（列式存储）混为一谈。前者是分布式数据模型的一类；后者描述关系表或其他表格数据在磁盘上的物理布局，关系型数据库也能使用列式存储来加速分析。

从同一业务问题出发选择数据模型：若要装载一份完整商品资料，文档可能自然；若频繁沿“用户—订单—商品”关系遍历，图结构可能更直接；若请求几乎总是按购物车键读取，键值模型可能简单；若查询集中在某个分区键及其范围，Cassandra 这类按 partition key 加 clustering columns 组织的宽列表可能合适；Bigtable 等产品须按各自 row key 查询能力设计。最后仍需验证写入模式、事务范围、查询能力、维护成本和故障时的可见性保证。

一个具体产品可说明“模型”和“保证”是两条轴线：Amazon DynamoDB 官方文档将其描述为支持键值与文档模型的服务；当前读取文档还区分不同表/索引的最终一致和强一致读取，并说明有些索引或流只提供最终一致读取。不能据此推断其他 NoSQL 产品或其他 DynamoDB 访问路径具有相同语义。

> [!info]- 来源
> - CAP 的形式化边界、线性一致性和可用性定义：Gilbert 与 Lynch，2002，《Brewer’s Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services》，§2–3，异步消息网络模型：[MIT CSAIL 作者托管原论文 PDF](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer6.pdf)。
> - CAP 中可用请求需得到非错误结果的直观说明，以及网络分区时在错误响应与可能不一致结果间的取舍：AWS Well-Architected Whitepapers，Availability and Beyond / CAP theorem：[官方白皮书](https://docs.aws.amazon.com/whitepapers/latest/availability-and-beyond-improving-resilience/cap-theorem.html)。
> - PACELC 对分区期间取舍与无分区时延迟/一致性取舍的扩展：Abadi，2012，《Consistency Tradeoffs in Modern Distributed Database System Design》，§“CAP is for Failures”与“Consistency/Latency Tradeoff”：[原论文 PDF](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)。
> - read-your-writes、monotonic reads 与 monotonic writes 这类会话保证：Terry 等，1994，*Session Guarantees for Weakly Consistent Replicated Data*：[IEEE 论文记录](https://ieeexplore.ieee.org/document/331722/)、[论文 PDF](https://pages.cs.wisc.edu/~remzi/Classes/739/Fall2016/Papers/bayou-sessions94.pdf)。
> - BASE 作为描述分布式设计取舍的助记词：Pritchett，2008，*BASE: An ACID Alternative*，ACM Queue 6(3)，48–55：[原文 DOI](https://doi.org/10.1145/1394127.1394128)。
> - 文档模型的记录与嵌套字段示例：MongoDB Manual，Documents：[官方文档](https://www.mongodb.com/docs/manual/core/document/)。
> - 属性图的节点、关系和属性：Neo4j Getting Started，Graph database concepts：[官方文档](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)。
> - 键值与文档模型的具体产品示例：Amazon DynamoDB Developer Guide，Introduction；此处只作产品自述的范围示例：[官方文档](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)。
> - DynamoDB 表、局部二级索引、全局二级索引和流的读取一致性差异：Amazon DynamoDB Developer Guide，Read consistency；访问时间 2026-11-13：[官方文档](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)。
> - Cassandra 5.0 CQL 表定义、primary key、可选 clustering columns 及无 clustering column 时每 partition 一行：[官方 Data Definition 文档](https://cassandra.apache.org/doc/stable/cassandra/developing/cql/ddl.html)。Bigtable 的唯一 row key、column family / qualifier 和逐行稀疏列：[官方 Tables and views 文档](https://docs.cloud.google.com/bigtable/docs/tables-and-views?hl=en)。这些产品例子不定义所有宽列系统的通用 schema。
> - 列式存储可以用于 SQL Server 关系型表，与 NoSQL 模型分类不同：SQL Server 17 文档，Columnstore indexes overview：[官方文档](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview?view=sql-server-ver17)。
