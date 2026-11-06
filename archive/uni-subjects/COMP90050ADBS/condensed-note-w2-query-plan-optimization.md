# 查询优化器怎样在等价计划之间作选择？

银行系统要找出布鲁克林分行关联的客户姓名。一个计划先把分行、账户和存款记录连接起来，再筛选分行城市；另一个计划先筛掉其他分行，再执行连接。读者要判断这两种执行顺序是否返回同一结果、哪种可能更省，以及优化器凭什么作出选择。

## 先分清查询写了什么和系统怎样执行

declarative query (声明式查询) 说明要哪些结果，不必规定数据库先读哪张表。query optimizer (查询优化器) 可以把同一逻辑结果改写成多种 logical plan (逻辑计划)，再为它们选定扫描、连接和排序等 physical operator (物理算子)，组成 execution plan (执行计划)。

以下课程例子采用银行模式：`branch(branch_name, branch_city, …)`、`account(account_number, branch_name, …)`、`depositor(customer_name, account_number)`。式中的 $\Pi$ 表示投影列、$\sigma$ 表示筛选行、带下标的 $\bowtie$ 表示按该条件连接。账户与存款人按 `account_number` 匹配，结果再按 `branch_name` 与分行匹配。

用关系代数表示课程中的两种选择：

$$
\Pi_{depositor.customer\_name}
\left(
\sigma_{branch.branch\_city='Brooklyn'}
\left(branch \bowtie_{branch.branch\_name=account.branch\_name}
 (account \bowtie_{account.account\_number=depositor.account\_number} depositor)\right)
\right)
$$

以及先对 branch 过滤再连接：

$$
\Pi_{depositor.customer\_name}
\left(
\left(\sigma_{branch.branch\_city='Brooklyn'}(branch)\right)
\bowtie_{branch.branch\_name=account.branch\_name}
 (account \bowtie_{account.account\_number=depositor.account\_number} depositor)
\right)
$$

筛选条件只引用 branch 的列，因此把它移到该关系输入处，不改变内连接产生的匹配行。若 Brooklyn 只占少数分行，提前筛选会缩小后续输入和中间结果，可能减少连接工作。

![2021 年冬季题目中的两种查询树](./21winQ10.png)

两图中先算出的右子树 `account ⋈ depositor` 完全相同；变化只在于 branch 输入以及最上层连接前是否先筛掉其他城市。图左是连接后筛选，图右把城市条件下推到 branch。题目要讨论的是：给定城市谓词选择了较少分行时，右侧为何通常更有利，以及“选择下推总是更快”是否成立。答案是前者可能更省，但还须看数据量、索引和后续算子；图中没有给出具体行数，不能据此算出某个计划的实际成本。

## 逻辑改写为何必须保留结果语义？

优化器可以用选择下推、投影下推、连接交换与连接结合等规则生成候选计划，但每次改写都要保留原查询所要求的结果。投影如果过早丢掉后续连接键或筛选列，就不能直接下推；外连接也不总能像内连接那样交换或结合。SQL 的重复行语义、空值比较及排序要求同样可能影响改写是否等价。

在课程图中，选择下推只是逻辑计划变换。它还没有决定系统使用索引扫描还是顺序扫描，也没有决定连接算法；这些物理选择须结合数据统计和执行成本估算。

## 计划成本怎样估算？

优化器会估计基表和中间结果的行数、页数、不同键数量与值分布，再套用扫描、连接、排序等物理算法的成本模型。selectivity (选择性) 表示谓词过滤后保留的数据比例；若过滤只保留很少行，后续连接通常能少处理输入。

统计信息不准确时，中间结果大小也可能估错。不同列之间的相关性、数据倾斜、缓存、索引和可用内存都会影响实际执行。成本单位是数据库自身的估算尺度，不能直接当成毫秒；同一条语句在不同数据量、统计信息或数据库版本下可能得到不同计划。

例如，如果 Brooklyn 只对应少量 branch 行，且存在按 `branch_city` 查找的索引，优化器可能估算索引定位加取回分行行比扫完整表便宜；若大多数分行都在 Brooklyn，顺序扫描可能更划算。这个物理选择取决于基数和页访问估价，课程查询树本身没有给出足以计算代价的行数。

优化器也不能只为每个算子分别挑看起来最便宜的算法。例如，某一步的 merge join (归并连接) 可能比 hash join (哈希连接) 多花一些成本，却能输出按键排序的结果，让下一步省掉排序。比较计划时要把后续算子一起考虑。

## 优化器会搜索所有等价计划吗？

不会。候选计划数量会随连接的表数迅速增长；枚举每一种组合可能花费过多规划时间和内存。系统可以使用动态规划复用子计划、剪除明显不合适的候选，或对很大的搜索空间采用启发式搜索。

PostgreSQL 18 在启用 Genetic Query Optimizer (遗传查询优化器，GEQO) 时，以当前 `FROM` 输入项数是否达到 `geqo_threshold` 判断是否进入遗传搜索；默认阈值为 12 个输入项。判断对象是输入项，不是二元 JOIN 运算符的个数：普通内连接链有 N 个输入时通常只有 N−1 个二元连接。低于阈值时使用常规连接顺序搜索；达到或超过阈值时使用 GEQO，以较短规划时间寻找合理方案。因此“优化器选择成本最低的计划”实际指在其生成和评估过的候选中选估算成本最低者，不是对所有可能计划或未来实际运行时间作保证。

## 数据库事务保证和单条语句计划是什么关系？

transaction (事务) 把多项数据库操作作为一个业务单元。例如转账要同时扣减一个账户并增加另一个账户；只有两项都成功，才提交整个变更。ACID (原子性、一致性、隔离性、持久性) 描述事务保证：

| 属性 | 对转账场景的含义 |
| --- | --- |
| Atomicity (原子性) | 扣款和入账一起提交，失败则一起回滚 |
| Consistency (一致性) | 提交前后都满足账户余额等声明约束与业务不变量 |
| Isolation (隔离性) | 并发事务按数据库定义的隔离规则观察彼此结果 |
| Durability (持久性) | 已提交结果在产品承诺范围内的故障后仍可恢复 |

查询优化器选择某条 SQL 语句的执行计划，并不自动建立跨语句的事务边界，也不替应用补全业务不变量。事务何时提交、如何隔离并发、崩溃后怎样恢复，仍由事务协议、数据库配置和应用逻辑共同决定。

若要继续看提交后的数据页和日志怎样应对写入中断，可接着读[双写与日志能保证什么，循环冗余校验又能证明什么？](./condensed-note-w1-durable-writes-and-crc.md)。

## 怎样用实际证据处理计划退化？

先用数据库提供的 explain (执行计划查看) 工具检查计划估算的扫描方式、连接算法、输入行数和成本。PostgreSQL 中 EXPLAIN 显示优化器选择的计划及估算值；EXPLAIN ANALYZE 会实际执行语句并同时给出观测到的时间和行数。对 UPDATE 等带副作用的语句执行 ANALYZE 前，可在安全的测试库中操作；官方的 BEGIN/ROLLBACK 示例只撤销参与该事务且可回滚的变更。它不会回收已经由 `nextval` 消耗的序列值，也不能撤销发往外部系统的副作用，因此不能只凭回滚就认为执行无影响。估算行数与实际行数差距很大时，再检查统计信息是否过期、分布是否偏斜、查询条件是否匹配可用索引。

对于重复执行的查询，SQL Server Query Store 可以保留查询计划及运行历史，帮助定位计划变化导致的性能退化。plan forcing (计划强制) 可用于已验证的临时修复，但数据分布、索引或模式变化后旧计划未必仍合适，必须继续观察实际指标。

![课程参数化查询示意](./query-optimization.png)

课程图把 Product 的 categoryID 等于 1 和等于 4 的两条字面量查询归为含参数 @Parm 的同一查询模板，说明 parameterization (参数化) 有机会复用计划、减少重复编译。图中第二处 `SELECT -` 应按 `SELECT *` 读；图展示模板复用，不保证两种输入使用相同计划。两个参数值的选择率可能不同，若分布差异很大，缓存计划可能出现 parameter sensitivity (参数敏感性)；数据库是否重新编译、缓存通用计划或选择其他计划，要看具体产品策略和实际计划。

## 什么时候预先保存派生结果？

如果某个派生值或连接结果被频繁读取、源数据更新相对可控，预先计算并保存可以减少每次查询的工作。代价是额外存储、写入维护和刷新流程；若源表变化后派生表没有同步更新，查询会读到过期结果。选择这种做法前应明确刷新时机、一致性要求及失败后的重建方式。

查询表达式中的过滤和连接成本模型，见[关系代数和连接算法怎样把查询变成可估算的页访问？](./condensed-note-w2-query-algebra-and-join-cost.md)。

> [!info]- 来源
> - **关系代数等价变换、选择下推、连接顺序、成本估计和搜索空间：** [Database System Concepts, 7e, ch. 16, Query Optimization](https://www.db-book.com/slides-dir/PDF-dir/ch16.pdf)，2019 年课程幻灯片；配图题的两计划及结论按原课程假设解释。
> - **PostgreSQL 18 的扫描/连接计划搜索，以及 GEQO 启用条件：** [PostgreSQL 18, Planner/Optimizer](https://www.postgresql.org/docs/18/planner-optimizer.html) 与 [Query Planning 配置](https://www.postgresql.org/docs/18/runtime-config-query.html#GUC-GEQO-THRESHOLD)，2026-11-06 核验；GEQO 的阈值按 `FROM` 输入项数判断，默认 12，是 PostgreSQL 的实现而非所有优化器的共同算法。
> - **PostgreSQL EXPLAIN 估算与 EXPLAIN ANALYZE 实测边界：** [PostgreSQL 18, EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)，2026-11-06 核验；`ANALYZE` 会实际执行，事务回滚只撤销可回滚的事务变更。
> - **`nextval` 消耗值在事务中止后也不会回收：** [PostgreSQL 18, Sequence Manipulation Functions](https://www.postgresql.org/docs/18/functions-sequence.html)，2026-11-06 核验；此外，外部系统副作用不由 PostgreSQL 事务回滚。
> - **SQL Server Query Store 追踪计划和运行指标、定位计划变化退化及强制已有计划：** [Microsoft Learn, Query Store Usage Scenarios](https://learn.microsoft.com/en-us/sql/relational-databases/performance/query-store-usage-scenarios?view=sql-server-ver17)，2026-11-06 核验；强制计划是产品工具，需按工作负载复验。
> - **参数敏感性：** [Microsoft Learn, Query Processing Architecture Guide](https://learn.microsoft.com/en-us/sql/relational-databases/query-processing-architecture-guide?view=sql-server-ver17)，2026-11-06 核验；文中只将其用作 SQL Server 的产品实现例。
> - **预先保存视图/派生结果的优化方法和维护权衡：** [Database System Concepts, 7e, ch. 16, Query Optimization](https://www.db-book.com/slides-dir/PDF-dir/ch16.pdf)，2019 年课程材料；具体刷新和一致性行为取决于系统及应用实现。
