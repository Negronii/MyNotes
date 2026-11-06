# 事务隔离与预写日志能保证什么？

**案例：** 报表系统中的两条请求同时预留 SKU-7 的最后一件库存，初始 available = 1。事务要把库存扣减和 reserve-demo-208 结果记录一起提交。随后连接超时只会让调用方不知道结果，数据库是否提交仍由持久记录决定。要分析这个过程，需分清一组语句的提交边界、并发事务看到的版本，以及写前日志 (write-ahead log, WAL) 在崩溃后能够恢复的状态。

~~~mermaid
flowchart TD
    Begin[开始事务] --> Predicate[条件更新 available > 0]
    Predicate -->|恰好 1 行| Insert[写入同一作用域的预留操作记录]
    Insert -->|成功| Changes[产生库存与操作记录的 WAL 变更]
    Changes --> CommitRecord[写入提交记录]
    CommitRecord --> CommitFlush[按同步提交配置持久化所需 WAL]
    CommitFlush --> Ack[确认提交]
    Changes --> PageFlush[对应 WAL 持久后，数据页可写回]
    PageFlush -.可发生在提交前或提交后.-> Pages[持久数据页]
    Predicate -->|0 行| Rollback[回滚本事务；按新事务查询操作键]
    Insert -->|作用域键唯一冲突| Rollback
    Insert -->|其他约束错误| Fail[回滚并返回明确失败]
    Crash[进程 / 主机崩溃] --> Recovery[恢复重放 WAL 并按提交状态判定可见性]
    Recovery --> Recovered[读到提交状态所证明的数据库结果]
    Ack -.响应可能丢失.-> Caller[客户端暂时无法确认结果]
~~~

## 事务把哪些写入放在同一边界？

transaction (事务) 把多条数据库语句放进同一次提交或回滚。ACID 是说明该边界的常用词，但每项都受数据库实现、配置和底层存储能力约束：

- **atomicity（原子性）**：同一事务中的写入一起提交，或由回滚一起撤销。
- **consistency（一致性）**：数据库约束和应用规则定义合法状态；事务不会自行发明业务不变量。
- **isolation（隔离性）**：并发事务按所选级别与引擎实现观察或等待其他写入。
- **durability（持久性）**：成功提交能够抵抗配置和存储承诺范围内的故障；异步提交或不可靠存储会改变这个范围。

对 SKU-7，先读 available=1 再无条件写成 0 不安全。条件更新与按账户、主体和键识别的预留结果须在同一事务中。以下使用 PostgreSQL 示例参数；$1 是 SKU-7，$2 是 acct-17，$3 是 user-17，$4 是 reserve-demo-208，$5 是 fingerprint-A，均由驱动绑定。字段与[库存基础页](database-fundamentals.md)中的 PostgreSQL schema 一致：

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- 本例按 Read Committed：成功者得到一行、值为 0；竞争者重检后得到零行。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku, status)
VALUES ($2, $3, $4, $5, $1, 'reserved');

COMMIT;
~~~

API 只有在 UPDATE 返回一行后才执行 INSERT；零行、作用域操作键冲突或其他写入错误都要显式 ROLLBACK。零行或作用域键冲突后，先回滚这个尝试，再在新事务按当前授权范围查询键并比较指纹；同键同指纹返回已提交结果，同键异指纹冲突，确认没有该键后才报告 SKU 不存在或售罄。提交之后若客户端连接断开，数据库行仍说明是否存在 reserve-demo-208；不能把“客户端超时”当成数据库自动回滚的信号。若 COMMIT 响应丢失，沿[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)的同键流程查询已提交结果，或以同键安全重放；唯一约束只能帮助裁决并发写入，不能单独给出重放响应。

## 隔离级别限制哪些并发现象？

dirty read（脏读）是读到其他事务尚未提交的写入；non-repeatable read（不可重复读）是同一事务重读一行时看到后来提交的新值；phantom read（幻读）是相同条件查询再次执行时，结果行集合因其他提交而变化；serialization anomaly（序列化异常）是一组成功事务的结果无法解释为某种串行执行顺序。SQL 标准按这些现象描述隔离级别；产品对名称的实现可能更强或采用不同并发控制，需看所选数据库具体文档。

PostgreSQL 18 的对照如下。这是该产品的行为表，不应套用于所有数据库。官方文档版本在 2026-11-06 核对为 PostgreSQL 18；本地双连接并发复现运行于 PostgreSQL 14.24，不将其描述为 18 的实测：

| PostgreSQL 18 级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
| --- | --- | --- | --- | --- |
| Read Uncommitted（读未提交） | 不允许，等同 Read Committed | 可能 | 可能 | 可能 |
| Read Committed（读已提交，默认） | 不允许 | 可能 | 可能 | 可能 |
| Repeatable Read（可重复读） | 不允许 | 不允许 | 不允许 | 仍可能出现写偏差 |
| Serializable（可串行化） | 不允许 | 不允许 | 不允许 | 不允许 |

在 PostgreSQL Read Committed 下，每条语句取得新快照。若两个写入请求同时以 WHERE available > 0 更新同一 SKU，后执行者会等待；前者提交后，数据库会对新行重新检查条件，available 已为 0 就更新零行。因此单条条件更新正好表达此不变量。在 Repeatable Read 下，若当前事务的快照已看见某行旧版本，而另一个事务先提交了该行的新版本，等待中的更新可能以 SQLSTATE 40001 失败；应用必须从最初读取开始重试整笔事务。如果应用把“先查、再从多行推导规则、最后分别更新”分成多个语句，则 Read Committed 每语句新快照可能让后续语句观察不同状态，复杂规则需更强保护。

## 为什么稳定快照仍可能破坏共享规则？

write skew (写偏差) 说明稳定快照不一定维护跨行规则。排班表有两名值班医生，规则要求至少一人值班。事务 A 读到两人都在岗并关闭 A 的排班；事务 B 读到相同快照并关闭 B。两者各写不同的行，因此 PostgreSQL Repeatable Read 下都可能提交，最终没人值班。

可选修法取决于规则形状：用同一行计数与条件更新将规则收敛为单行不变量；或在 PostgreSQL Read Committed 下，让所有写入方先锁定同一排班控制行，再用另一条 SELECT 语句检查状态。以 B 为例，它等 A 释放控制行后，第二条语句取得新快照并看到只剩 B 在岗，于是拒绝关闭 B 的排班。Repeatable Read 事务的快照不会因等待结束而刷新，因此这一两语句方案不能原样套用到 Repeatable Read；也可使用 Serializable 并在 SQLSTATE 40001 序列化失败后从最初读取开始重试整个事务。只重试最后一条 UPDATE 会沿用过期决策。事务中不应执行无法撤销的远端支付或直接发布消息；先写本地 outbox，提交后再投递。

> [!info] MVCC 和“无锁读取”不是同一句话
> multi-version concurrency control (多版本并发控制, MVCC) 让读取者按快照看见可见版本，同时并发写入可产生新版本，减少部分读写等待。它不取消写写冲突、显式锁或所有等待；不同引擎保留与清理版本的方式也不同。PostgreSQL 通过 VACUUM 清理不再可见的旧版本，长事务持有的旧快照可能延迟清理。

## 预写日志如何把提交与数据页写回分开？

write-ahead log (预写日志, WAL) 先记录数据更改，再允许对应数据页写回持久存储。PostgreSQL 确认同步提交前，会先持久化提交所需的 WAL；相应数据页可能已经写回，也可能仍留待稍后写回。无论何时写页，都必须先持久化足以恢复该页的 WAL。崩溃后启动恢复会重放已持久日志；若日志没有提交记录，事务写入仍不会作为已提交结果被查询到。这样可以避免每个事务提交都同步刷新所有被修改的数据页，但承诺依赖同步提交策略、文件系统、设备 flush 语义和配置。WAL 的存在本身不意味着抵御存储设备谎报写入或失去整个故障域。

WAL 与崩溃恢复不是时间点恢复的全部材料。要恢复到某个过去时点，还需要适用的基础备份和从该备份起点到目标时刻连续、完整的 WAL 归档；缺失任一段日志都会造成时间范围断裂。SQLite 采用自己的回滚日志或 WAL 模式和配置规则，不能把 PostgreSQL 的文件布局与恢复步骤直接套过去。

> [!example] 一次提交后立即崩溃时检查什么
> 对 reserve-demo-208，若数据库已按持久策略确认 COMMIT，即使数据页尚未写回，崩溃恢复也能重做已提交的库存扣减与预留记录；恢复后查询得到 available=0 和该操作记录。相反，若库存与预留的变更日志已写出但事务没有持久提交记录，即使脏页曾写回，恢复后查询仍看见 available=1 且没有该预留。若 API 在提交确认前失联，客户端只能查询权威记录来区分这两种结果。具体断电保证取决于所选引擎与存储兑现配置，而不是 HTTP 响应有没有到达。

## 哪些课程细节继续留在归档？

课程中的 ARIES 恢复推演仍保留在[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)：analysis（分析）阶段用 dirty page table（脏页表）记录恢复时涉及的脏页；每页的 recLSN 表示该页自上次干净后可能需要 REDO（重做）的最早日志位置，最小 recLSN 是 REDO 起点，不是分析阶段要扫描的最早日志范围。CAP 的边界是在网络分区期间，系统不能同时保证线性一致性，并保证每个非故障节点收到的请求最终都得到响应；two-phase commit (两阶段提交, 2PC) 协调多个参与者的提交决定，已进入 prepared 并投 YES 的参与者，在尚不知道协调者全局决定时可能等待。两者都不能替代单库库存原子更新、隔离级别或日志恢复。

**接下来：** SQL 约束与索引决定哪些业务状态可写、哪些访问路径可用，见[如何用约束保护业务规则并为读取建立索引？](database-constraints-and-indexes.md)。当服务用 ORM 请求数据库时，session、事务与连接的持有时间见[如何限定 ORM Session 并诊断连接池耗尽？](../backend/data-access-and-connection-pools.md)。

> [!info]- 来源
> - 隔离级别异常定义、PostgreSQL 18 每语句快照、更新等待重检与 Serializable 重试：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1–13.2.3，核对于 2026-11-06；本地双连接并发实跑版本为 PostgreSQL 14.24，未在 PostgreSQL 18 实跑。
> - MVCC 版本可见性与 VACUUM：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1，核对于 2026-11-06。
> - WAL 先持久日志再写数据页、提交确认不依赖所有数据页已写回、崩溃重做与基础备份加日志的时间点恢复：[PostgreSQL 18, WAL Introduction](https://www.postgresql.org/docs/18/wal-intro.html)，§28.3，[WAL Configuration](https://www.postgresql.org/docs/18/wal-configuration.html)、[Asynchronous Commit](https://www.postgresql.org/docs/18/wal-async-commit.html) 及 [Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html)，核对于 2026-11-06。
> - SQLite 的本地事务与日志模式：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html) 与 [Write-Ahead Logging](https://www.sqlite.org/wal.html)，核对于 2026-11-06。
> - 课程 ARIES 推导：[Mohan et al., ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)；关联原始课程页[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)。
> - CAP 的网络分区边界：[Gilbert and Lynch, Brewer’s conjecture and the feasibility of consistent, available, partition-tolerant web services](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf)；两阶段提交的预备状态限制：[PostgreSQL 18, PREPARE TRANSACTION](https://www.postgresql.org/docs/18/sql-prepare-transaction.html)，核对于 2026-11-06。
