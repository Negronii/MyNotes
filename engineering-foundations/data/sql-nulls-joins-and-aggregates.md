# 空值、外连接和分组会怎样改变一张汇总表的结果？

前几章讲写路径：条件写、约束、事务和日志保证数据存得对。从本章起转向读路径的第一件事：一条汇总查询的结果由什么决定。答案往往不在索引或性能，而在三处语义：NULL 参与比较时得到“未知”，外连接会补出并不存在的行，聚合与分组决定每个数字在数什么。本章用一张四位客户、四笔订单的小表，把每条查询的中间行都摆出来手算。

## 案例：四位客户、四笔订单

本章换成一个独立的小例子，因为要逐行手算中间结果，主线三的库存案例行数太少、也没有可分组的维度。表与数据都是合成的教学输入，省略了账户列和授权过滤；语义按 PostgreSQL 18 文档说明。

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    region      TEXT
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER,
    status       TEXT NOT NULL
);

INSERT INTO customers VALUES
    (1, 'Ava', 'North'),
    (2, 'Ben', NULL),
    (3, 'Cy',  'South'),
    (4, 'Dia', 'North');

INSERT INTO orders VALUES
    (101, 1, 1200, 'paid'),
    (102, 1,  800, 'pending'),
    (103, 2, NULL, 'paid'),
    (104, 3,  500, 'paid');
~~~

四位客户各带一个特点：Ava 有两笔订单（一笔已付、一笔待付）；Ben 的地区未知，他唯一一笔订单的金额也未知；Cy 有一笔已付订单；Dia 没有订单。目标是一张“每位客户的订单数与金额合计”汇总表。

## 一条查询按什么顺序产生结果？

解释 SQL 结果时，按 logical processing order (逻辑处理顺序) 追踪：

1. `FROM` / `JOIN` 产生行；
2. `WHERE` 逐行筛选；
3. `GROUP BY` 把剩下的行合成组；
4. 聚合函数为每组算出一个值；
5. `HAVING` 逐组筛选；
6. 计算 `SELECT` 列表，再按 `ORDER BY` 排序、按 `LIMIT` 截取。

这是语义顺序，不是执行顺序。PostgreSQL 的计划器可以选择任何物理计划，只要结果与这个顺序算出的相同。本章的每个陷阱，都是某个条件或计数被放到了错误的阶段。

## NULL 参与比较时为什么既不真也不假？

SQL 用 three-valued logic (三值逻辑)：比较的结果可以是 TRUE、FALSE 或 UNKNOWN。NULL 表示“值未知”，所以 `NULL = NULL` 和 `NULL <> 'North'` 都是 UNKNOWN。`WHERE` 只保留结果为 TRUE 的行，UNKNOWN 与 FALSE 一样被丢弃。

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：每一行的比较都是 UNKNOWN

SELECT name FROM customers WHERE region IS NULL;
-- Ben

SELECT name FROM customers WHERE region <> 'North';
-- Cy；Ben 的比较是 UNKNOWN，被丢弃
~~~

判断是否为空要写 `IS NULL`。空字符串 `''` 是已知的空文本，`'' IS NULL` 为 FALSE，不能拿它代替 NULL。

## 先决定“未知”算不算进去

NULL 出现在条件或数值里时，查询本身无法替你决定它的业务含义。写谓词或聚合之前，先回答两个问题。

**筛选时，未知值要不要纳入？** 问题若是“不是 North，或地区未知”，就要把 UNKNOWN 显式变成 TRUE：

| region | `<> 'North'` | `IS NULL` | 二者 `OR` | `WHERE` 保留？ |
| --- | --- | --- | --- | --- |
| North | FALSE | FALSE | FALSE | 否 |
| South | TRUE | FALSE | TRUE | 是 |
| NULL（Ben） | UNKNOWN | TRUE | TRUE | 是 |

~~~sql
SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL;
-- Ben, Cy

SELECT name FROM customers
WHERE region IS DISTINCT FROM 'North';
-- Ben, Cy
~~~

`IS DISTINCT FROM` 把 NULL 当作一个可比较的状态：NULL 与 `'North'` 不同，结果为 TRUE；两个 NULL 互不“distinct”。问题若是“地区已知且不是 North”，就只用 `<>`，结果只有 Cy。

**计算时，缺失的数值能不能当成 0？** Ben 那笔订单的金额为 NULL，可能是尚未计价、上游未回填，也可能是数据错误。自动当成 0 会把“未知”和“确实为零”混为一谈。只有报表定义明确规定“没有金额就按零贡献”时，才用 `COALESCE(amount_cents, 0)` 或 `COALESCE(SUM(amount_cents), 0)`；否则保留 NULL，让读者能区分两者。

## 外连接的条件放在 ON 还是 WHERE？

`LEFT JOIN` (左外连接) 先用 `ON` 判断左右两行是否相配；左表某行一个匹配也没有时，仍保留它，并把右表的列补成 NULL。

问题：“列出每位客户及其已付款订单，没有已付款订单的客户也要列出。”付款条件属于“怎样算匹配”，应放进 `ON`：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
~~~

若先按客户号连接全部订单，再在 `WHERE` 里筛 `o.status = 'paid'`，筛选就发生在补 NULL 之后：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
~~~

| 条件位置 | 结果行 | 原因 |
| --- | --- | --- |
| `ON` | Ava–101、Ben–103、Cy–104、Dia–NULL（4 行） | Ava 的 102 是 pending，不匹配；Dia 没有已付订单，保留为补 NULL 的一行 |
| `WHERE` | Ava–101、Ben–103、Cy–104（3 行） | Dia 补出的 `o.status` 是 NULL，与 `'paid'` 比较为 UNKNOWN，被 `WHERE` 丢弃 |

条件移到 `WHERE` 后，外连接实际退化成“只保留有已付订单的客户”。对内连接，两种写法结果相同；差别只出现在外连接，因为只有外连接会在 `ON` 与 `WHERE` 之间补出 NULL 行。两条查询的结果都是“连接行”，不是客户去重列表：某位客户出现几次，取决于有几笔订单符合条件。

汇总表要统计 paid 和 pending 两种订单，所以分组查询连接**全部**订单。下面的中间结果有 5 行：

~~~sql
SELECT c.customer_id, c.name, o.order_id, o.amount_cents, o.status
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;
~~~

| customer_id | name | order_id | amount_cents | status |
| ---: | --- | ---: | ---: | --- |
| 1 | Ava | 101 | 1200 | paid |
| 1 | Ava | 102 | 800 | pending |
| 2 | Ben | 103 | NULL | paid |
| 3 | Cy | 104 | 500 | paid |
| 4 | Dia | NULL | NULL | NULL |

Ava 两行，对应两笔真实订单。Dia 那一行是外连接补出来的，不是订单。下一节的计数都要从这 5 行出发。

## COUNT 和 SUM 各在数什么？

聚合函数的统计对象不同：

- `COUNT(*)` 数行，不看任何列是否为空；
- `COUNT(expr)` 只数 `expr` 非空的行；
- `SUM(expr)` 只加非空输入；一个组里没有任何非空输入时，结果是 NULL，不是 0。

先看原始 `orders` 表：

~~~sql
SELECT COUNT(*)            AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents)   AS total_cents
FROM orders;
-- 4 | 3 | 2500
~~~

四行订单中三笔有金额，已知金额合计 `1200 + 800 + 500 = 2500`。Ben 的 NULL 金额既不计入 `priced_orders`，也不加进总和。

再在上一节的 5 行上按客户分组：

~~~sql
SELECT c.name,
       COUNT(*)              AS joined_rows,
       COUNT(o.order_id)     AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents)   AS total_cents
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

Dia 的 `COUNT(*)` 是 1，因为补 NULL 的那一行也是一行；要数真实订单，必须数订单表的非空主键 `o.order_id`，得到 0。Ben 有一笔订单却没有金额，合计为 NULL。Ben 和 Dia 的合计都是 NULL，但原因不同：前者是金额未知，后者是没有订单。报表若要把它们显示为 0，由报表定义决定，见[先决定“未知”算不算进去](#先决定“未知”算不算进去)。

还要区分“组里没有非空值”和“根本没有组”。下表的输入都已经过 `WHERE`：

| `WHERE` 之后的输入 | 分组与输出 | `COUNT(*)` / `COUNT(amount_cents)` | `SUM(amount_cents)` |
| --- | --- | ---: | ---: |
| 没有行 | 无 `GROUP BY`：全局聚合仍输出一行 | 0 / 0 | NULL |
| 没有行 | 按 `customer_id` 分组：没有组，没有输出行 | — | — |
| 一笔订单，金额 NULL | 一组 | 1 / 0 | NULL |
| 一笔订单，金额 0 | 一组 | 1 / 1 | 0 |

例如直接查 `orders WHERE customer_id = 4` 时没有输入行；汇总表里 Dia 之所以有组，是 `LEFT JOIN` 先为她造出了一行。

并非所有聚合都忽略 NULL。PostgreSQL 的 `array_agg` 会把 NULL 收进数组；用到其他聚合时，先查它对 NULL 的规则。

## 多连一张子表，金额为什么变大？

本例客户到订单只有一层，每笔订单只进入所属客户的组一次。再连一张“每笔订单可有多行”的子表，同一笔订单就会被复制成多行，这叫 fan-out (扇出)。

单独演示：只取 Ava 的两笔订单，配三条合成的标签关联（它们不属于上面的表）。

~~~sql
WITH ava_orders(order_id, amount_cents) AS (
    VALUES (101, 1200), (102, 800)
), order_tags(order_id, tag) AS (
    VALUES (101, 'priority'), (101, 'gift'), (102, 'gift')
)
SELECT COUNT(o.order_id)          AS joined_order_rows,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(o.amount_cents)        AS naive_total_cents
FROM ava_orders AS o
JOIN order_tags AS t USING (order_id);
-- 3 | 2 | 3200
~~~

订单 101 有两个标签，它的 1,200 分出现两次；102 有一个标签，800 分出现一次。连接后的和是 `1200 × 2 + 800 = 3200`，真实总额仍是 2,000。

`COUNT(DISTINCT order_id)` 在这里能数回 2 笔订单，但 `SUM(DISTINCT amount_cents)` 不是通用修复：两笔不同订单可能恰好金额相同，去重会把其中一笔吃掉。安全的做法是先把每张子表分别汇总到目标粒度（这里是每位客户至多一行），再连接这些汇总结果。

## WHERE 筛行，HAVING 筛组

`WHERE` 在分组前过滤连接产生的行；`HAVING` 在聚合之后过滤组，所以只有 `HAVING` 能引用 `SUM(...)` 这样的组值。下面只保留合计至少 500 分的客户：

~~~sql
SELECT c.name,
       COUNT(o.order_id)   AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
~~~

| 客户 | orders | total_cents | 保留原因 |
| --- | ---: | ---: | --- |
| Ava | 2 | 2000 | 2000 ≥ 500 |
| Cy | 1 | 500 | 边界值满足 `>=` |

Ben 和 Dia 的合计是 NULL，`NULL >= 500` 为 UNKNOWN，`HAVING` 同样只留 TRUE，两组都被排除。

写一张汇总表时，按这个顺序定条件：先确定统计粒度（每行是客户还是订单），再确定缺失值的业务含义，再确定哪些状态参与；然后把“怎样算匹配”放进 `ON`，把“哪些行参与”放进 `WHERE`，把“哪些组输出”放进 `HAVING`。

> [!info] 实例：方言与兼容开关（PostgreSQL 18、SQLite 3.51，核对于 2026-11-12）
> - PostgreSQL 的 `transform_null_equals` 默认关闭，上文 `region = NULL` 返回空结果就是按默认值说的。打开后，它只把字面量写法 `expr = NULL` 或 `NULL = expr` 改写成 `expr IS NULL`，不影响其他比较；显式写 `IS NULL` 不依赖这个开关。
> - 本章的四客户查询曾在 SQLite 3.51.0 上复现。SQLite 从 3.39.0 起支持 `IS DISTINCT FROM`；更早的版本用 `region <> 'North' OR region IS NULL` 表达同一含义。

## 查询写对之后，它怎样在应用里执行？

本章给出一张汇总查询的检查顺序：NULL 进入比较得 UNKNOWN、被 `WHERE` 和 `HAVING` 丢弃；外连接的匹配条件放 `ON`；按真实主键计数；先汇总子表再连接。查询写对之后，它要在应用里经由 ORM 会话借一条数据库连接才能执行；下一章[ORM 会话怎样借用连接，连接池为什么会耗尽？](orm-sessions-and-connection-pools.md)从这里接手，讲连接何时借出、何时归还，以及占得太久时池怎样耗尽。

> [!info]- 来源
> - 逻辑处理阶段（FROM、WHERE、GROUP BY、HAVING 的表转换）与外连接的匹配、补 NULL、`ON` 与 `WHERE` 的差别（含“对内连接无关、对外连接影响很大”）：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1–7.2.3；`SELECT` 列表之后再排序：[Sorting Rows](https://www.postgresql.org/docs/18/queries-order.html)，§7.5；物理计划可与逻辑顺序不同：[Planner/Optimizer](https://www.postgresql.org/docs/18/planner-optimizer.html)，§51.5；SQLite 对应语义：[SELECT](https://www.sqlite.org/lang_select.html)，§2。核对于 2026-11-12。
> - NULL 比较得 UNKNOWN、`IS NULL`、`IS DISTINCT FROM`：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite 3.39.0 加入 `IS DISTINCT FROM`：[SQLite Release 3.39.0](https://www.sqlite.org/releaselog/3_39_0.html)。核对于 2026-11-12。
> - `transform_null_equals` 默认关闭、只改写与字面量 NULL 的 `=` 比较：[PostgreSQL 18, Version and Platform Compatibility](https://www.postgresql.org/docs/18/runtime-config-compatible.html#GUC-TRANSFORM-NULL-EQUALS)，§19.13.2，核对于 2026-11-12。
> - `COUNT(*)`、`COUNT(expr)`、`SUM` 只处理非空输入、无非空输入时返回 NULL、`array_agg` 收入 NULL：[PostgreSQL 18, Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Built-in Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)。核对于 2026-11-12。
> - 四客户数据、扇出标签与各结果表为本章合成输入，结果已手算并在 SQLite 3.51.0 复现。
