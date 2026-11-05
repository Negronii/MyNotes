# How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？

Read the invariant at the place where concurrent writes meet: update inventory only when availability remains positive, check that exactly one row changed, and create the reservation in the same transaction. A separate read followed by an unconditional write lets two requests act on the same old value. Enforce request identity with a unique constraint so a repeated logical request cannot reserve the same unit twice. / 在并发写入发生的数据库边界检查不变量：只有库存仍大于零时才更新，并确认恰好更新一行，再在同一事务中创建预留。先单独读取、再无条件写入会让两个请求都基于同一个旧值操作。用唯一约束维护请求身份，避免同一逻辑请求重复预留库存。

**Key terms / 关键术语：** conditional update / 条件更新；transaction / 事务；unique constraint / 唯一约束；idempotency key / 幂等键；rollback / 回滚。

~~~mermaid
flowchart TD
    Begin[Begin transaction] --> Update[Conditional update: available > 0]
    Update --> Count{Exactly one row changed?}
    Count -->|yes| Reserve[Insert reservation with unique request ID]
    Reserve --> Commit[Commit both changes]
    Count -->|no| Rollback[Rollback and report unavailable]
    Reserve -->|insert or constraint failure| Rollback
~~~

Assume an inventory table has one row per unique SKU. Do not read the count in the application and then issue an unconditional write: competing requests can both act on the same old value. Let the database perform the condition and decrement as one write:

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = ? AND available > 0;

-- Continue only if exactly one row was updated.
INSERT INTO reservations (request_id, sku) VALUES (?, ?);

COMMIT;
~~~

Continue only if the update changed exactly one row. Insert the reservation under a unique request ID in the same transaction; if no row changed or the insert fails, roll back. This protects the local invariant only under the selected engine's atomic-update and transaction semantics. A unique request constraint also prevents duplicate local reservations. It does not make an external payment or message publish atomic with the database; use a downstream idempotency contract or durable outbox for that boundary.

This example relies on the database transaction and row-update contract. The detailed meaning of isolation, MVCC, and WAL is in [Database transactions, isolation, and recovery / 数据库事务、隔离与恢复](database-transactions-isolation-and-recovery.md). For the constraints and indexes used to express invariants and access paths, see [Database constraints and indexes / 数据库约束与索引](database-constraints-and-indexes.md). For examples of how SQL NULL and outer joins affect query results, see [SQL NULLs, joins, and aggregates / SQL NULL、连接与聚合](sql-null-joins-and-aggregates.md).

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) explains how operation keys handle unknown request outcomes; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md) applies job-key uniqueness and transactional outbox to asynchronous work.

**Sources and verification / 来源与验证：** PostgreSQL 18 [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) and [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html); SQLite [transactions](https://www.sqlite.org/lang_transaction.html) and [foreign keys](https://www.sqlite.org/foreignkeys.html). The conditional reservation transaction was run with Python sqlite3 against SQLite 3.51.0 with foreign-key enforcement enabled. This is evidence for that local SQLite run, not a universal concurrency guarantee.
