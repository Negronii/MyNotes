# 如何用约束保护业务规则并为读取建立索引？

**案例：** 报表服务接收账户 acct-17 的幂等请求 report-demo-208，生成任务 job-demo-731，并按账户读取最近任务状态。数据库要让每个合法操作最多对应一行、外键有真实目标、库存不能为负；读取路径还需在任务增多后可控。约束是所有写入方共享的正确性规则；索引是为某些查询维护的访问路径，只有当计划器判断成本合适时才会选择。

~~~mermaid
flowchart TD
    Write[API / relay / worker 写入] --> Rules{约束成立？}
    Rules -->|否| Reject[拒绝写入，事务不提交]
    Rules -->|是| Store[提交业务状态]
    Query[读取请求] --> Planner[计划器估算候选路径]
    Planner -->|估计省成本| Index[使用索引]
    Planner -->|扫描更划算| Scan[顺序扫描或其他计划]
    Index --> Rows[按条件返回行]
    Scan --> Rows
~~~

## 先把不变量放在数据库边界

应用输入校验能及时给用户更友好的错误；数据库约束也要校验每一次写入，防止另一个 API、定时任务或人工脚本绕开这次校验后破坏已提交数据。以下业务 schema 以 PostgreSQL 18 为例；后面的 SQLite 计划演示独立建表，不声称同一 DDL 在两个引擎上有相同类型和外键语义。primary key (主键) 唯一标识行；unique constraint (唯一约束) 防止某组键重复；foreign key (外键) 要求被引用的父键存在；NOT NULL constraint (非空约束) 阻止缺值；CHECK constraint (检查约束) 限制每一行必须满足的布尔条件。

~~~sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY NOT NULL
);

CREATE TABLE inventory (
    sku TEXT PRIMARY KEY NOT NULL,
    available INTEGER NOT NULL CHECK (available >= 0)
);

CREATE TABLE reservations (
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES inventory(sku),
    status TEXT NOT NULL CHECK (status IN ('reserved', 'cancelled')),
    PRIMARY KEY (account_id, principal_id, idempotency_key)
);

CREATE TABLE report_jobs (
    job_id TEXT PRIMARY KEY NOT NULL,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (account_id, principal_id, idempotency_key)
);

INSERT INTO accounts (account_id) VALUES ('acct-17');
INSERT INTO inventory (sku, available) VALUES ('SKU-7', 1);
~~~

这里三种规则解决不同问题：available 的 CHECK 禁止负库存；reservation 的外键确保账户和 SKU 存在；report_jobs 的复合唯一键把同一账户、同一主体、同一幂等键限定为同一个逻辑提交。插入 acct-17 账户父行与 SKU-7 后，才有合法值可供 reservation 引用。键列是 NOT NULL，避免缺值绕过该业务比较。创建时间使用 TIMESTAMPTZ 表示绝对时间，不能把不同本地时区格式的任意 TEXT 直接按字典序当作时间顺序。任务 job-demo-731 可以在 queued 到 running 再到 succeeded 等已定义状态间变化，但 CHECK 只限制允许取值，并不单独验证转移顺序；转移需要由带前置状态的 UPDATE 或其他并发控制实现。ON DELETE CASCADE 是另一项独立的生命周期规则，只有业务确实要求删父行时也删掉关联子行才应选择；它不会默认发生。

> [!info] CHECK 不一定拒绝 NULL
> 在 PostgreSQL 中，CHECK 表达式只在结果为 FALSE 时拒绝行；结果为 TRUE 或 NULL 都满足约束。因此 CHECK (available >= 0) 若允许 available 为 NULL，并不能表达“必须有非负库存”。需要 NOT NULL 与 CHECK 一起约束。SQLite 还使用动态类型，普通 INTEGER 列可能存入文本；若要用 SQLite 验证同一强类型不变量，应启用 STRICT 表或加显式类型检查。SQLite 外键也必须在每个连接执行 PRAGMA foreign_keys = ON。

## 复合索引怎样配合任务列表？

报表所有者查询账户 acct-17 最近 20 个任务，按创建时间倒序；同一时间戳时用任务 ID 决定稳定顺序：

~~~
CREATE INDEX report_jobs_by_account_recent
    ON report_jobs (account_id, created_at DESC, job_id DESC);

SELECT job_id, status, created_at
FROM report_jobs
WHERE account_id = $1
ORDER BY created_at DESC, job_id DESC
LIMIT 20;
~~~

B-tree index (B 树索引) 按键列的顺序保存索引项。查询中的 $1 是 PostgreSQL 驱动绑定的账户参数。第一个键 account_id 是等值条件，后两列直接提供稳定排序，因此这个复合索引可能同时缩小扫描范围并避免额外排序。把 account_id 去掉或调到末尾后，索引就不能同样直接定位某账户的那段连续键范围。索引的列序需从真实过滤条件与排序推导；字段多并不自动更快。

UNIQUE (account_id, principal_id, idempotency_key) 通常会让数据库同时维护一条唯一索引来阻止重复键。外键查父表需要主键或唯一键，但在 PostgreSQL 中，创建外键并不会自动为子表引用列建立索引；删除账户或查某账户预留时，是否需要相应的子表索引取决于数据量与访问模式。索引只能缩短查询路径，不能替代业务授权；在服务端依然须先检查调用者是否可见任务或预留。

## 计划器为什么有时不用已建索引？

索引会占用磁盘和缓存，也会增加 INSERT、UPDATE、DELETE 时维护条目的工作。若查询预计读取表的大部分行，顺序扫描可能比逐个索引查找再回表便宜。query planner (查询计划器) 会根据表规模、分布、统计信息、谓词和输出列估算成本；估算和选择会随引擎、版本、数据与统计而变。必须用目标引擎的 EXPLAIN 检查代表性查询，不能以“索引存在”推断性能已提升。

下面在独立 SQLite 教学库保留一个计划复现：它与 NULL 章节同名的 customers、orders 表结构不同，需分别建表。这里创建 1,000 个合成订单，按一个客户筛选并按时间倒序；先检查无索引计划，再加 customer_id、placed_at 复合索引并检查。可见行数、统计信息和版本都会影响输出；本例实测计划只说明这组 SQLite 数据上的选择。

> [!example]- 用 1,000 个合成订单观察索引计划
> ~~~sql
> PRAGMA automatic_index = OFF;
> CREATE TABLE orders (
>     order_id INTEGER PRIMARY KEY,
>     customer_id INTEGER NOT NULL,
>     amount_cents INTEGER NOT NULL,
>     placed_at INTEGER NOT NULL
> );
> WITH RECURSIVE seq(n) AS (
>     VALUES(1)
>     UNION ALL
>     SELECT n + 1 FROM seq WHERE n < 1000
> )
> INSERT INTO orders
> SELECT n, n % 100, n * 25, n FROM seq;
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders
> WHERE customer_id = 17
> ORDER BY placed_at DESC;
> -- 本地输出：SCAN orders；USE TEMP B-TREE FOR ORDER BY
>
> CREATE INDEX orders_by_customer_and_time
>     ON orders(customer_id, placed_at);
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders
> WHERE customer_id = 17
> ORDER BY placed_at DESC;
> -- 本地输出：SEARCH orders USING INDEX orders_by_customer_and_time (customer_id=?)
> ~~~
> SQLite 3.51.0 的本地复现用于观察查询计划；不同 SQLite 版本、统计状态及不同规模的数据可能选择其他计划。PostgreSQL 的 EXPLAIN ANALYZE 会实际执行语句并报告观察到的耗时与行数，评估有写入副作用的语句前须先考虑它会真的执行。

本次计划回放观察到的变化是访问路径和排序步骤：从全表 SCAN 加临时 B-tree 排序，变成按 customer_id 的索引 SEARCH。它没有量出端到端耗时，因此只能说明 SQLite 为这组数据选择了不同计划，不能据此声称实际延迟必然下降；amount_cents 不在索引键中，这条读取也不是覆盖索引。

**接下来：** 唯一键为操作结果提供重放边界；具体怎样原子提交与处理并发见[事务隔离与 WAL 能保证什么？](database-transactions-isolation-and-recovery.md)。SQL 空值、连接与聚合对结果行的影响见[NULL、连接与分组如何改变报表 42 的结果？](sql-null-joins-and-aggregates.md)。

> [!info]- 来源
> - CHECK、NOT NULL、主键、唯一键与外键：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5；特别是 CHECK 的 TRUE/NULL 行为，核对于 2026-11-06。
> - 复合 B-tree 的前导列条件与索引开销：[PostgreSQL 18, Indexes](https://www.postgresql.org/docs/18/indexes.html)，§11.1、§11.3；排序：[Indexes and ORDER BY](https://www.postgresql.org/docs/18/indexes-ordering.html)，§11.4；核对于 2026-11-06。
> - 计划估算与实际执行的区别：[PostgreSQL 18, EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)，核对于 2026-11-06。
> - SQLite 外键与查询计划：[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html) 与 [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)，核对于 2026-11-06。
