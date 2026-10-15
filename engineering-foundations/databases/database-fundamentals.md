# Database Fundamentals / 数据库基础

**Core model / 核心模型：** A database schema names the data and constraints that every writer must respect. Queries describe the result; a planner chooses how to produce it, using indexes when their cost is worthwhile. Transactions group changes, while an isolation policy defines what concurrent transactions can observe. A write-ahead log (WAL) helps a database recover after a crash, subject to that product's durability and backup configuration. / 数据库模式描述数据及所有写入方都必须遵守的约束。查询描述所需结果，执行计划器再选择实现方式，并在成本合适时使用索引。事务将多个变更组合起来；隔离级别定义并发事务能够观察到什么。预写日志（WAL）帮助数据库在崩溃后恢复，但具体保证取决于产品的持久性与备份配置。

**Key terms / 关键术语：** schema / 模式；primary key / 主键；foreign key / 外键；constraint / 约束；index / 索引；query plan / 查询计划；transaction / 事务；isolation level / 隔离级别；MVCC / 多版本并发控制；write-ahead log (WAL) / 预写日志。

## Schema and constraints / 模式与约束

A relational schema defines tables, columns, types, and relationships. A **primary key** identifies a row; a **unique constraint** prevents duplicate key values; a **foreign key** requires a reference to an existing key (subject to the constraint's null and deferral rules); and `NOT NULL` and `CHECK` constrain allowed values. Put durable business invariants in database constraints as well as validating input in the application: another job, script, or service may write the same tables. Referential actions such as `ON DELETE CASCADE` encode an additional lifecycle rule and should match the data relationship.

The following SQL uses common table and constraint syntax. It describes customers and orders, ensures an order has a customer and a non-negative amount, and adds an access path for a customer's recent orders. The query asks for rows; the database decides whether and how to use the index. The `?` is a bound-parameter placeholder used by SQLite; other drivers use their own placeholder notation.

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    placed_at TEXT NOT NULL
);

CREATE INDEX orders_by_customer_and_time
    ON orders(customer_id, placed_at);

SELECT order_id, amount_cents, placed_at
FROM orders
WHERE customer_id = ?
ORDER BY placed_at DESC;
~~~

An index is a maintained access path, not a promise that every query will be faster. It uses storage and adds work to inserts, updates, and deletes. A multicolumn B-tree index is ordered by its leading columns, so `(customer_id, placed_at)` can support a lookup by customer and then a time ordering; the best plan still depends on the query, table size, data distribution, statistics, and database engine. Inspect a plan with that engine's `EXPLAIN` facility and compare it with representative data. In PostgreSQL, `EXPLAIN ANALYZE` executes the statement and reports observed work, while plain `EXPLAIN` shows the planner's estimated strategy. Plan output and choices are product- and version-specific.

## SQL result semantics / SQL 查询结果语义

SQL predicates can evaluate to **TRUE, FALSE, or UNKNOWN**. An ordinary comparison such as `=` or `<>` with `NULL` evaluates to UNKNOWN; null-aware predicates such as `IS NULL` and `IS DISTINCT FROM` have their own rules. `WHERE` keeps only rows for which its predicate is TRUE. Use `IS NULL` to test for a missing value; `column = NULL` does not find it. The same rule explains why a right-table filter in `WHERE` can remove the null-extended rows of a `LEFT JOIN`. / SQL 谓词可以得出 **TRUE、FALSE 或 UNKNOWN**。`=` 或 `<>` 这类普通比较遇到 `NULL` 时结果为 UNKNOWN；`IS NULL`、`IS DISTINCT FROM` 等空值判定或相异性谓词有各自的规则。`WHERE` 只保留谓词为 TRUE 的行。用 `IS NULL` 检查缺失值；`column = NULL` 不会查到它。这个规则也解释了为什么 `WHERE` 中的右表筛选条件会移除 `LEFT JOIN` 生成的空扩展行。

Run this compact customer/order dataset in a fresh, separate teaching database/schema; it is independent of the earlier example, which also uses tables named `customers` and `orders` with a different schema. Ben's region and one order amount are `NULL`; Dia has no orders.

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER,
    status TEXT NOT NULL
);

INSERT INTO customers VALUES
    (1, 'Ava', 'North'),
    (2, 'Ben', NULL),
    (3, 'Cy', 'South'),
    (4, 'Dia', 'North');

INSERT INTO orders VALUES
    (101, 1, 1200, 'paid'),
    (102, 1, 800, 'pending'),
    (103, 2, NULL, 'paid'),
    (104, 3, 500, 'paid');
~~~

The first query returns no rows because `region = NULL` is UNKNOWN. `IS NULL` returns Ben; `region <> 'North'` returns only Cy because Ben's comparison is UNKNOWN. To include missing regions in that search, say so explicitly with `OR region IS NULL`.

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- no rows

SELECT name FROM customers WHERE region IS NULL ORDER BY customer_id;
-- Ben

SELECT name FROM customers WHERE region <> 'North' ORDER BY customer_id;
-- Cy

SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL
ORDER BY customer_id;
-- Ben
-- Cy
~~~

`LEFT JOIN` first preserves each left-side customer, putting `NULL` in the order columns when no matching order remains. A right-side predicate in `ON` limits which orders count as matches, so Dia is kept. The same predicate in `WHERE` is applied after the join; Dia's null-extended row does not pass `o.status = 'paid'`, so it disappears.

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
-- Dia | NULL

SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
~~~

`COUNT(*)` counts input rows; `COUNT(column)` counts only rows whose value in that column is not `NULL`. Aggregates such as `SUM` ignore null inputs and return `NULL` when a group has no non-null inputs. The grouped result makes the outer-join detail visible: Dia has one joined row, but no order ID; Ben has an order but no priced order.

~~~sql
SELECT COUNT(*) AS order_rows, COUNT(amount_cents) AS priced_orders
FROM orders;
-- 4 | 3

SELECT c.name,
       COUNT(*) AS joined_rows,
       COUNT(o.order_id) AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
-- Ava | 2 | 2 | 2 | 2000
-- Ben | 1 | 1 | 0 | NULL
-- Cy  | 1 | 1 | 1 | 500
-- Dia | 1 | 0 | 0 | NULL
~~~

`WHERE` filters rows before grouping; `HAVING` filters completed groups. This query keeps groups whose non-null total is at least 500 cents. Ben's sum is `NULL`, so the comparison is UNKNOWN and his group is not kept.

~~~sql
SELECT c.name, COUNT(o.order_id) AS orders, SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
-- Ava | 2 | 2000
-- Cy  | 1 | 500
~~~

**How do NULL, outer joins, and grouping change a query result? / NULL、外连接和分组会怎样改变查询结果？** An ordinary comparison such as `=` or `<>` with `NULL` is UNKNOWN; null-aware predicates such as `IS NULL` and `IS DISTINCT FROM` have their own rules. Use `IS NULL` for missing values, and remember that `WHERE` keeps only TRUE. Put a right-side condition in `LEFT JOIN ... ON` when unmatched left rows must remain; a `WHERE` condition can remove those rows. `COUNT(*)` counts joined rows, `COUNT(column)` skips nulls, `WHERE` filters input rows, and `HAVING` filters completed groups. Inspect query plans with the chosen engine and version. / `=` 或 `<>` 这类普通比较遇到 `NULL` 时结果为 UNKNOWN；`IS NULL`、`IS DISTINCT FROM` 等空值判定或相异性谓词有各自的规则。缺失值应使用 `IS NULL`，并记住 `WHERE` 只保留 TRUE。若要保留没有匹配右表记录的左表行，应把右表条件放在 `LEFT JOIN ... ON` 中；放在 `WHERE` 中可能移除这些行。`COUNT(*)` 统计连接后的行数，`COUNT(column)` 跳过空值；`WHERE` 筛选分组前的输入行，`HAVING` 筛选已完成的分组。查询计划应使用所选数据库及其版本来检查。

These result rules are shared by the examples' SQLite run; optimizer plans are not. Use the selected engine's `EXPLAIN` tool on representative data, and label any plan observation with its engine and version.

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

**Related notes / 相关笔记：** [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md) explains request-scoped ORM work and connection budgeting; [Caching and Redis / 缓存与 Redis](../backend/caching-and-redis.md) explains a cache in front of the database. [Core Data Structures / 核心数据结构](../algorithms/core-data-structures.md) introduces the tree structures behind common indexes; the [archived database course](../../archive/uni-subjects/COMP90050ADBS/readme.md) preserves its broader sequence of worked examples.

**Sources and verification / 来源与验证：** PostgreSQL 18 documentation checked 2026-10-15: [SQL tutorial](https://www.postgresql.org/docs/18/tutorial-sql.html), [comparison predicates](https://www.postgresql.org/docs/18/functions-comparison.html), [table expressions and joins](https://www.postgresql.org/docs/18/queries-table-expressions.html), [aggregate functions](https://www.postgresql.org/docs/18/functions-aggregate.html), [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [indexes](https://www.postgresql.org/docs/18/indexes.html), [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html), [MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html), [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [WAL](https://www.postgresql.org/docs/18/wal-intro.html), [WAL configuration and recovery](https://www.postgresql.org/docs/18/wal.html), and [prepared transactions](https://www.postgresql.org/docs/18/sql-prepare-transaction.html). SQLite's [foreign-key](https://www.sqlite.org/foreignkeys.html), [transaction](https://www.sqlite.org/lang_transaction.html), [SELECT](https://www.sqlite.org/lang_select.html), [expressions](https://www.sqlite.org/lang_expr.html), [aggregate functions](https://www.sqlite.org/lang_aggfunc.html), [query planner](https://www.sqlite.org/queryplanner.html), and [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) documentation support the examples; plan wording is diagnostic output, not an API. The customer/order result queries, existing schema/query example, and reservation transaction were run with Python's `sqlite3` module against SQLite 3.51.0, with foreign-key enforcement enabled. For 1,000 synthetic orders, the existing plan run changed from a table scan plus temporary sort to an index search after adding the composite index. That is one planner observation, not a stable output contract. The original recovery method is Mohan et al., [ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging); its DPT and `recLSN` mechanism is explained in the [CMU database recovery notes (pp. 1, 4–6)](https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf).
