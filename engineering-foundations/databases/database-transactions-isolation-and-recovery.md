# What do transaction isolation and WAL guarantee? / 事务隔离与 WAL 分别保证什么？

A database transaction gives statements one commit/rollback boundary. The isolation policy determines which concurrent changes a transaction may observe; MVCC is one way engines manage versions. Write-ahead logging lets recovery redo changes after a crash only within the database's durability and storage assumptions. Point-in-time recovery additionally needs a suitable base backup and required log history. Product, version, and configuration determine the exact guarantee. / 数据库事务为一组语句提供共同的提交或回滚边界；隔离策略定义事务能观察到哪些并发变更，MVCC 是数据库管理版本的一种机制。预写日志支持在崩溃后重做变更，但保证受数据库持久性和存储配置约束。时间点恢复还需要合适的基础备份和所需日志。具体保证取决于产品、版本与配置。

**Key terms / 关键术语：** transaction / 事务；isolation level / 隔离级别；MVCC / 多版本并发控制；write-ahead log (WAL) / 预写日志；crash recovery / 崩溃恢复；point-in-time recovery / 时间点恢复。

~~~mermaid
flowchart LR
    Tx[Transaction changes] --> Log[Append corresponding WAL records]
    Log --> Flush[Flush log under configured durability policy]
    Flush --> Commit[Report commit]
    Commit --> Page[Data pages may be written later]
    Crash[Crash] --> Recovery[Redo durable logged changes]
    Recovery --> Data[Database recovers committed state]
    Backup[Base backup plus archived log range] --> PITR[Point-in-time recovery]
~~~

## Transactions and isolation / 事务与隔离

A transaction gives a set of statements one commit or rollback boundary. **ACID** is a useful vocabulary, with each property still bounded by implementation and configuration:

- **Atomicity / 原子性:** the transaction's changes commit together or are rolled back together.
- **Consistency / 一致性:** constraints and application rules define valid states; the database does not invent the business rules.
- **Isolation / 隔离性:** concurrent transactions see behavior controlled by the isolation level and engine implementation.
- **Durability / 持久性:** a successful commit survives the failures covered by the database's configured durability and storage assumptions.

Consider reserving one remaining unit. Do not read the count in the application and then issue an unconditional write: concurrent requests can both act on the same old value. Prefer one conditional update, check that exactly one row changed, insert the reservation in the same transaction, and roll back if either step fails. The exact concurrency guarantee depends on the engine's atomic-update, locking, and isolation contract; verify it for the selected database.

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = ? AND available > 0;

-- Continue only if exactly one row was updated.
INSERT INTO reservations (request_id, sku) VALUES (?, ?);

COMMIT;
~~~

Assume `inventory.sku` is unique. If the update changes zero rows or the insert fails, roll back instead of committing. This example relies on the database's transaction and row-update semantics; unique constraints can also enforce that a `request_id` is not applied twice. A transaction cannot make a remote side effect atomic with the local database unless both participants share a protocol that provides that guarantee.

SQL isolation names are not a complete description of every engine's behavior. Common anomalies include a **dirty read** (seeing another transaction's uncommitted write), a **non-repeatable read** (seeing a changed row on a later read), a **phantom read** (a repeated predicate query returns a different set), and a **serialization anomaly** (the committed result cannot be explained by any serial ordering). Check the selected product's manual rather than transferring an isolation-level label from another database.

**PostgreSQL 18 example:** the default Read Committed level takes a new snapshot for each statement; Repeatable Read keeps a transaction snapshot and can abort a conflicting update; Serializable detects additional dependency patterns and can abort a transaction that must then be retried from the beginning. These are PostgreSQL behaviors, not universal definitions of those level names.

### MVCC / 多版本并发控制

With **multi-version concurrency control (MVCC)**, a database keeps versions or visibility metadata so a statement or transaction can read a snapshot while concurrent transactions make changes. This can reduce reader–writer blocking, but does not remove write conflicts, explicit locks, or every wait. Engines that retain row versions need cleanup; PostgreSQL, for example, uses vacuuming to reclaim versions that are no longer visible, and long-running snapshots can delay that cleanup. MVCC is a concurrency-control mechanism, not a promise that all reads are lock-free or that every engine uses the same version rules.

## WAL and recovery boundaries / WAL 与恢复边界

The write-ahead rule is that changes to data pages are written only after the corresponding log records have been flushed to durable storage. A commit can be reported durable after the required log records are safely flushed under the configured policy; a later crash can then use the log to redo changes not yet copied into data pages. Settings that weaken synchronous commit or storage guarantees can weaken what a successful response means. WAL supports crash recovery; point-in-time recovery additionally requires a suitable base backup and the needed archived log range.

Recovery algorithms are product-specific. The archived database course keeps the detailed ARIES analysis, including the Dirty Page Table and its `recLSN` rule, in [Log-based Crash Recovery / 基于日志的崩溃恢复](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). In ARIES, `recLSN` is the earliest log record that could have dirtied that page since it was last clean; it is not a universal WAL field or redo rule.

## Distributed database boundaries / 分布式数据库的边界

Two nearby concepts are useful boundaries, not a distributed-systems survey:

- **CAP:** during a network partition, a system cannot guarantee both linearizable consistency and an eventual response to every request at a non-failed node. Partition is the assumed failure; the trade-off is which operations may be rejected or may observe stale data. See Gilbert and Lynch's [CAP result](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf) and the archived [CAP theorem / CAP 定理](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md) discussion.
- **Two-phase commit (2PC):** a participant that has durably prepared and voted YES must wait for the coordinator's decision. A timeout after YES is not a safe local abort, so the participant can remain blocked until it learns that decision. 2PC coordinates an atomic commit decision; it does not itself provide transaction isolation. See PostgreSQL's [prepared-transaction documentation](https://www.postgresql.org/docs/18/sql-prepare-transaction.html) and the archived [2PC notes](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md).

**Course material kept in the archive / 保留在归档中的课程内容：** the detailed RAID calculations, R-tree/spatial-index examples, snapshot-isolation exercises, and recovery derivations remain in [week 1 RAID calculations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w1.md), [week 2 R-tree/spatial-index examples](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w2.md), [week 3 snapshot-isolation exercises](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w3.md), and [week 4 recovery derivations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). The active note provides the shared model; the course files preserve their derivations and exercises.


**Related notes / 相关笔记：** [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](database-fundamentals.md) shows a conditional transaction for a local business invariant; [API timeout and safe retry / API 超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) explains why a database transaction cannot atomically include an unrelated remote side effect; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md) applies an outbox to the database-to-queue boundary.

**Sources / 来源：** PostgreSQL 18 [MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html), [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [WAL introduction](https://www.postgresql.org/docs/18/wal-intro.html), [WAL configuration and recovery](https://www.postgresql.org/docs/18/wal.html), and [prepared transactions](https://www.postgresql.org/docs/18/sql-prepare-transaction.html), checked 2026-10-15; SQLite [transactions](https://www.sqlite.org/lang_transaction.html). The archived database course retains the detailed ARIES DPT/recLSN derivation and examples: [week 4 recovery](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). CAP and 2PC are boundaries, not local transaction substitutes: see Gilbert and Lynch's [CAP result](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf), PostgreSQL's [prepared transaction documentation](https://www.postgresql.org/docs/18/sql-prepare-transaction.html), and the archived [CAP / 2PC course notes](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4.md). The original ARIES method is Mohan et al., [ARIES](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging), with DPT and recLSN explained in the [CMU database recovery notes (pp. 1, 4–6)](https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf).
