# SQL 空值、连接与分组会怎样改变报表 42 的结果？

**案例：** 报表 42 按客户汇总一小组已付款和待付款订单。为便于手算，输入已经限定为账户 `acct-17` 的四客户、四订单切片。`customers` / `orders` 表省略账户和报表列；本页解释 SQL 查询语义，不展示租户过滤或授权。

语义以 PostgreSQL 18 官方文档核对，四客户 SQL 例另用本机 SQLite 3.51.0 复现；SQLite 对 `IS DISTINCT FROM` 的支持从 3.39.0 开始。

Ava 有两笔订单，Ben 的地区和一笔订单金额未知，Cy 有一笔已付款订单，Dia 没有订单。追踪查询时，可以把它的**逻辑结果阶段**看成 `FROM / JOIN` 形成行、`WHERE` 筛行、`GROUP BY` 形成组、聚合计算、`HAVING` 筛组。它帮助解释 SQL 结果；PostgreSQL 计划器可以用不同的物理执行计划算出同一结果。

## 输入中的空值怎样影响比较？

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

SQL 使用 three-valued logic（三值逻辑）：普通比较可能是 TRUE、FALSE 或 UNKNOWN。`NULL = NULL` 与 `NULL <> 'North'` 都是 UNKNOWN。`WHERE` 只留下 TRUE，因此 `region = NULL` 搜不到 Ben；空值判断要写 `IS NULL`。 在本页的 PostgreSQL 和 SQLite 文本列中，空字符串 `''` 是已知的空文本，`'' IS NULL` 为 FALSE；它与未知值 NULL 不同。

本例中，`region <> 'North'` 单独用于 `WHERE` 时只选中 South；要连未知地区也纳入“不是 North 或未知”，再把 `IS NULL` 用 OR 合并：

| region | `<> 'North'` | `IS NULL` | `OR` | WHERE 保留？ |
| --- | --- | --- | --- | --- |
| North | FALSE | FALSE | FALSE | 否 |
| South | TRUE | FALSE | TRUE | 是 |
| NULL（Ben） | UNKNOWN | TRUE | TRUE | 是 |

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：比较为 UNKNOWN，WHERE 丢弃

SELECT name FROM customers WHERE region IS NULL ORDER BY customer_id;
-- Ben

SELECT name FROM customers WHERE region <> 'North' ORDER BY customer_id;
-- Cy；Ben 的 UNKNOWN 不通过 WHERE

SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL
ORDER BY customer_id;
-- Ben
-- Cy

SELECT name FROM customers
WHERE region IS DISTINCT FROM 'North'
ORDER BY customer_id;
-- Ben
-- Cy
~~~

坏例 `region = NULL` 按 PostgreSQL 默认 `transform_null_equals = off` 解释。若打开这个兼容开关，PostgreSQL 只会把裸 `NULL` 的等号形式 `expression = NULL` 或 `NULL = expression` 改写为 `expression IS NULL`；显式写 `IS NULL` 才不会依赖该开关。SQLite 例子不受它影响。

`IS DISTINCT FROM` 把 NULL 当作一个可比较状态：Ben 的 NULL 与 `'North'` 不同，条件为 TRUE。PostgreSQL 18 和 SQLite 3.39.0 及更新版本都支持它；更早的 SQLite 可用 `region <> 'North' OR region IS NULL` 表达“不是 North 或地区未知”。若业务问题实际是“地区已知且不是 North”，则只保留 Cy；先选定是否包含未知值，再写条件。

> [!info] 先判断“未知”是否等于“零”
> Ben 的缺失金额可能表示尚未计价、上游未回填或数据质量错误；自动当成 0 会抹去区别。只有报表定义明确把“没有金额输入”解释成零贡献时，才用 `COALESCE`。

## 左外连接的筛选条件放在哪里？

`LEFT JOIN`（左外连接）先用 `ON` 判断哪些左右行相配；客户没有任何匹配订单时，仍保留客户行，并把订单列补成 NULL。若问题是“列出每位客户和其已付款订单，同时保留没有已付款订单的客户”，应把付款条件放进 `ON`：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
~~~

如果先按客户号连接所有订单，再在 `WHERE` 筛 `o.status = 'paid'`，筛选是在空扩展行产生之后执行：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
~~~

| 条件位置 | 结果行 | 行数与原因 |
| --- | --- | --- |
| `o.status = 'paid'` 在 `ON` | Ava–101、Ben–103、Cy–104、Dia–NULL | 4 行。Ava 的 pending–102 不匹配；Dia 没有付款订单，仍得到右侧为 NULL 的保留行。 |
| `o.status = 'paid'` 在 `WHERE` | Ava–101、Ben–103、Cy–104 | 3 行。Dia 的 NULL 与 `'paid'` 比较为 UNKNOWN，筛选时被丢弃。 |

把条件从 `ON` 移到 `WHERE` 改变了行集，并把这条查询变成“只保留存在已付款订单的客户和订单”。结果不是客户去重列表：Ava 出现几次取决于符合条件的订单数。

报表 42 要汇总 paid 与 pending 两种订单，因此分组查询必须重新连接**全部**订单，不沿用上面的付款过滤。这个完整连接的中间结果是 5 行：

~~~sql
SELECT c.customer_id, c.name, o.order_id, o.amount_cents, o.status
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;
~~~

| customer_id | customer | order_id | amount_cents | status |
| ---: | --- | ---: | ---: | --- |
| 1 | Ava | 101 | 1200 | paid |
| 1 | Ava | 102 | 800 | pending |
| 2 | Ben | 103 | NULL | paid |
| 3 | Cy | 104 | 500 | paid |
| 4 | Dia | NULL | NULL | NULL |

Ava 出现两行，是因为她有两笔不同订单；她的每笔订单金额各进入一次组内求和。Dia 的一行是外连接补出的记录，不是真实订单。后续要数订单就数非空主键 `o.order_id`；不能把左连接后的 `COUNT(*)` 当作客户数或真实订单数。

## 计数与求和各自统计什么？

在原始 `orders` 表中，`COUNT(*)` 统计四行，`COUNT(amount_cents)` 只统计三个非空金额；已知金额小计是 `1200 + 800 + 500 = 2500`。Ben 的一笔订单金额为 NULL，所以它不会被金额计数或加进总和。

~~~sql
SELECT COUNT(*) AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents) AS total_cents
FROM orders;
~~~

| order_rows | priced_orders | total_cents |
| ---: | ---: | ---: |
| 4 | 3 | 2500 |

左连接后按客户分组，依次看连接行数、真实订单数、金额非空的订单数和总金额：

~~~sql
SELECT c.name,
       COUNT(*) AS joined_rows,
       COUNT(o.order_id) AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
~~~

| 客户 | 连接行 | 订单数 | 有金额订单 | 合计（分） |
| --- | ---: | ---: | ---: | ---: |
| Ava | 2 | 2 | 2 | 2000 |
| Ben | 1 | 1 | 0 | NULL |
| Cy | 1 | 1 | 1 | 500 |
| Dia | 1 | 0 | 0 | NULL |

`COUNT(*)` 数的是分组中的连接行，所以 Dia 的空扩展行也计为 1；`COUNT(o.order_id)` 才排除它并数到 0 笔订单。Ben 有一笔真实订单，但没有非空金额。`SUM` 只加非空输入；一个组没有任何非空金额时，结果是 NULL，而不是 0。若报表合同明确要把“无有效金额”显示为零，可用 `COALESCE(SUM(o.amount_cents), 0)`；否则保留 NULL 能与零金额区分。

还要区分“组里没有非空金额”和“没有组”：对 `orders` 过滤 `customer_id = 4` 后没有输入行；无 `GROUP BY` 的全局聚合仍返回一行，按客户分组则没有组可输出。

| WHERE 后的输入 | 分组与输出 | 计数（`COUNT(*)` / `COUNT(amount_cents)`） | `SUM(amount_cents)` |
| --- | --- | ---: | ---: |
| 没有订单行 | 无 `GROUP BY`，有一行整体汇总 | 0 / 0 | NULL |
| 没有订单行 | 按 `customer_id` 分组，无组、无结果行 | — | — |
| 一行真实订单，金额为 NULL | 按 `customer_id` 分组，有一组 | 1 / 0 | NULL |
| 一行真实订单，金额为 0 | 按 `customer_id` 分组，有一组 | 1 / 1 | 0 |

报表查询里 Dia 会保留，是因为 `LEFT JOIN` 先为她造出一行空扩展记录；因此 Dia 有组，`COUNT(*) = 1`，而非“订单表没有该组”的零行状态。

这不是所有聚合函数都会丢弃 NULL：例如 PostgreSQL 的 `array_agg` 会把 NULL 收入数组。本例只有客户到订单这一层，一笔订单只进入所属客户组一次；若再连接一张按订单有多行的标签表，同一订单金额就会随标签行重复。

单独看这个重复风险：暂时只取 Ava 的两笔订单，并给它们补三个合成标签关联；这是 fan-out 的小例，不是报表 42 的新增业务表：

~~~sql
WITH ava_orders(order_id, amount_cents) AS (
    VALUES (101, 1200), (102, 800)
), order_tags(order_id, tag) AS (
    VALUES (101, 'priority'), (101, 'gift'), (102, 'gift')
)
SELECT COUNT(o.order_id) AS joined_order_rows,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(o.amount_cents) AS naive_total_cents
FROM ava_orders AS o
JOIN order_tags AS t USING (order_id);
-- 3 | 2 | 3200
~~~

订单 101 的 1,200 分随两个标签出现两次，102 的 800 分出现一次，所以连接后 SUM 为 3,200，实际订单总额仍是 2,000。`COUNT(DISTINCT order_id)` 可在此查询中数回两笔订单，但 `SUM(DISTINCT amount_cents)` 不是通用修复：不同订单可能恰好有相同金额。要按客户安全地合并多个子表，先分别把每个子表汇总到 `customer_id` 粒度、保证每位客户至多一行，再连接这些汇总结果。

## 分组前后两种筛选各在何时执行？

`WHERE` 过滤连接产生的行，`GROUP BY` 把剩余行按客户合并，聚合函数计算组值，`HAVING` 再过滤组。下面只保留金额总和至少 500 分的客户：

~~~sql
SELECT c.name,
       COUNT(o.order_id) AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
~~~

| 客户 | orders | total_cents | 保留原因 |
| --- | ---: | ---: | --- |
| Ava | 2 | 2000 | 求和至少 500。 |
| Cy | 1 | 500 | 边界值 500 满足 `>= 500`。 |

Ben 和 Dia 的 `SUM` 都是 NULL；NULL 与 500 比较为 UNKNOWN，因此两组都不满足 HAVING。要得出正确报表，先确认统计粒度、金额缺失的业务含义和哪些订单状态应参与，再把条件放在正确的 `ON`、`WHERE` 或 `HAVING` 阶段。

**接下来：** 数据库怎样用外键、唯一约束和索引保护报表记录与读取？见[如何用约束保护业务规则并为读取建立索引？](database-constraints-and-indexes.md)。并发写入、提交和恢复又有哪些边界？见[事务隔离与预写日志能保证什么？](database-transactions-isolation-and-recovery.md)。

> [!info]- 来源
> - NULL 比较、`IS NULL` 与 `IS DISTINCT FROM`：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite 3.39.0 加入兼容谓词：[SQLite Release 3.39.0](https://www.sqlite.org/releaselog/3_39_0.html)，核对于 2026-11-12。
> - PostgreSQL 的 `transform_null_equals` 默认关闭，只改写与裸 `NULL` 的 `=` 比较（`expression = NULL` 或 `NULL = expression`）：[Version and Platform Compatibility](https://www.postgresql.org/docs/18/runtime-config-compatible.html#GUC-TRANSFORM-NULL-EQUALS)，§19.13.2，核对于 2026-11-12。
> - LEFT JOIN 的匹配、NULL 扩展与 `ON` / `WHERE` 的差异：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1–7.2.2；SQLite [SELECT](https://www.sqlite.org/lang_select.html)，§2，核对于 2026-11-12。
> - `FROM`、WHERE、GROUP BY、HAVING 的逻辑表转换：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.2–7.2.3；物理计划可因查询而异：[Planner/Optimizer](https://www.postgresql.org/docs/18/planner-optimizer.html)，§51.5，核对于 2026-11-12。
> - `COUNT(*)`、`COUNT(expr)`、SUM 的非空输入与空结果：[PostgreSQL 18, Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Built-in Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)，核对于 2026-11-12。
