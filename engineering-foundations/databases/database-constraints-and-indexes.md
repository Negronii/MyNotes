# How do database constraints and indexes shape data access? / 数据库约束和索引如何塑造数据访问？

Constraints enforce durable invariants for every writer, while indexes maintain access paths the planner may choose when their cost is worthwhile. A unique or foreign-key rule protects correctness; an index can speed a representative query but consumes storage and adds write work. Inspect the chosen engine's plan on representative data rather than treating an index definition as a performance promise. / 约束为所有写入方强制执行持久不变量；索引维护执行计划器可能按成本选择的访问路径。唯一约束或外键保护正确性；索引可能加速有代表性的查询，但会占用存储并增加写入成本。应使用真实代表性数据检查所选数据库的计划，不能把创建索引当成性能保证。

**Key terms / 关键术语：** primary key / 主键；unique constraint / 唯一约束；foreign key / 外键；CHECK / 检查约束；B-tree index / B 树索引；query plan / 查询计划；EXPLAIN / 查询计划解释。

~~~mermaid
flowchart LR
    Query[Query and predicates] --> Planner[Database planner]
    Planner --> Estimate[Estimate cost from data and statistics]
    Estimate -->|useful path| Index[Index scan or lookup]
    Estimate -->|not useful| Scan[Table scan or other plan]
    Index --> Result[Rows in requested order]
    Scan --> Result
~~~

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


**Sources and verification / 来源与验证：** PostgreSQL 18 [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [indexes](https://www.postgresql.org/docs/18/indexes.html), and [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html), checked 2026-10-15; SQLite [foreign keys](https://www.sqlite.org/foreignkeys.html), [query planner](https://www.sqlite.org/queryplanner.html), and [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html). The schema/query example was run with Python sqlite3 against SQLite 3.51.0. For 1,000 synthetic orders, adding the composite index changed the observed plan from a table scan plus temporary sort to an index search. This is one planner observation, not a stable output contract.


**Related notes / 相关笔记：** [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](database-fundamentals.md) applies a conditional update and a unique request key; [Database transactions, isolation, and recovery / 数据库事务、隔离与恢复](database-transactions-isolation-and-recovery.md) explains the transaction boundary.
