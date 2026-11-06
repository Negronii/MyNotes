# SQL 空值、连接与分组会怎样改变报表 42 的结果？

**案例：** 报表 42 为账户 acct-17 汇总一小组客户订单。为让每一步能手算，下面把四个客户与四条订单当作本次报告的全部输入，不演示读取授权或全量账务规模。Ava 有两笔订单，Ben 的地区和一笔订单金额未知，Cy 有一笔已付款订单，Dia 没有订单。查询看似只是在拼表和相加，但 NULL、LEFT JOIN（左外连接）与 aggregate function（聚合函数）会改变哪些行存在、哪些值被统计。

~~~mermaid
flowchart TD
    Base[客户与订单输入] --> From[FROM / JOIN 生成中间行]
    From --> Where[WHERE 只保留 TRUE]
    Where --> Group[GROUP BY 形成分组]
    Group --> Aggregate[COUNT / SUM 计算]
    Aggregate --> Having[HAVING 筛掉不符合的分组]
    Having --> Output[报表 42 的客户汇总行]
~~~

这条流程中的每一步都作用于一个中间结果：JOIN 先组合行；WHERE 在分组前筛选；聚合函数对分组输入计算；HAVING 再筛选分组。NULL 表示值未知或缺失，不等于数字 0，也不等于空字符串。后面的输出会逐个显示这些状态造成的差异。

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

SQL 使用 three-valued logic（三值逻辑）：普通比较可能为 TRUE、FALSE 或 UNKNOWN。NULL = NULL 与 NULL <> 'North' 都是 UNKNOWN，不是 TRUE 或 FALSE。WHERE 只保留为 TRUE 的行，所以把 region = NULL 当作空值搜索不会返回 Ben；应写 IS NULL。

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：NULL = NULL 得到 UNKNOWN，WHERE 丢弃

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
-- Cy；此谓词把 NULL 当作一个可区分值
~~~

IS DISTINCT FROM 是可读的空值安全比较：它把 NULL 当作一个可比较状态，而不是返回 UNKNOWN。PostgreSQL 和当前 SQLite 都支持它；其他数据库可使用自己的等价谓词。若条件是“地区已知且不是 North”，上一条含 OR region IS NULL 的结果就不合语义，因此先明确业务筛选含义再写谓词。

> [!info] 先判断“未知”是否等于“零”
> Ben 的金额缺失可能表示尚未计价、上游未回填或数据质量错误；把它自动当 0 会掩盖不同问题。只有报表定义明确把“没有金额输入”解释成零贡献时，才用 COALESCE。业务解释应与 SQL 表达式一起说明。

## 左外连接的筛选条件放在哪里？

LEFT JOIN 会为每一条左表行寻找满足 ON 的右表行；如果没找到，仍保留左表行，并把右侧列补成 NULL。若“只关联已付款订单，但仍显示没有已付款订单的客户”，过滤条件应参与 ON 匹配：

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
~~~

若先用客户号连接所有订单，再把 o.status = 'paid' 放到 WHERE，筛选在连接结果上执行。Ava 的 pending 订单使条件为 FALSE，不会留下；Dia 的右侧是空扩展行，NULL = 'paid' 为 UNKNOWN，也被移除；结果会像只留有已付款订单的内连接：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
-- Dia 消失
~~~

这两条查询表达不同的问题：第一条保留没有已付款匹配的客户及其空扩展行；第二条只保留客户与每笔已付款订单的匹配行。两条结果都可能让同一客户出现多次，并不等于客户去重清单。把条件移动到 ON 与 WHERE 不是排版差异，而是改变输出行集。

报表 42 的金额总和要包含 paid 与 pending 两种状态，因此下面的分组查询重新连接全部订单，不再加 o.status = 'paid'。连接后 Ava 有两行，其余有订单的客户各一行；随后 GROUP BY 才把每位客户的明细收拢为一个汇总行。只要保留上面的 paid 过滤，就会把 Ava 的 pending 订单 800 分漏在总额之外。

## 计数与求和各自统计什么？

在所有订单行中，COUNT(*) 统计四行；COUNT(amount_cents) 只统计非空金额，所以是三。这里限定讨论的 COUNT(expr) 只计入表达式非空的行，SUM(expr) 对非空输入求和；因此 Ben 虽有一笔订单，金额合计仍没有任何非空输入，SUM 返回 NULL。不要把这概括成每一种聚合函数都删除 NULL：例如 PostgreSQL 的 array_agg 可以把 NULL 放进数组。做左连接时，每个没有子行的客户也会获得一行空扩展记录，所以 COUNT(*) 对 Dia 是 1；要数真实订单，应使用非空主键 COUNT(o.order_id)。

~~~sql
SELECT COUNT(*) AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents) AS total_cents
FROM orders;
-- 4 | 3 | 2500
~~~

先计算单人分组：

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
-- Ava | 2 | 2 | 2 | 2000
-- Ben | 1 | 1 | 0 | NULL
-- Cy  | 1 | 1 | 1 | 500
-- Dia | 1 | 0 | 0 | NULL
~~~

每一行都能从输入表复算：Ava 的 1200 + 800 = 2000；Ben 的唯一金额是 NULL，因此金额非空计数为 0、总和为 NULL；Cy 是 500；Dia 没有订单，因左连接仍有一行，所以 COUNT(*)=1，但 order_id 为空让真实订单数为 0。输入中三笔已知金额之和为 1200 + 800 + 500 = 2500，另有一笔金额未知；2500 是已知金额小计，不代表未知金额可视为零。

SUM() 没有非空输入时返回 NULL。若报表合同明确把没有金额的汇总展示为零，可写 COALESCE(SUM(o.amount_cents), 0)；否则保留 NULL 能区分“零金额”与“无有效金额数据”。

## 分组前后两种筛选各在何时执行？

WHERE 在分组前过滤 FROM / JOIN 产生的行；HAVING 在完成 GROUP BY 与聚合后筛选组。下面查询只保留金额合计至少为 500 分的客户。Ben 的 SUM 为 NULL，所以与 500 比较得 UNKNOWN，该组不通过 HAVING。

~~~sql
SELECT c.name,
       COUNT(o.order_id) AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
-- Ava | 2 | 2000
-- Cy  | 1 | 500
~~~

先确定统计粒度是“客户”、再决定空金额的业务含义，最后用 ON、WHERE、GROUP BY、HAVING 将顺序表达出来。数据库实现与数据规模会影响查询计划，但不会把空值语义变成缺失的 0。

**接下来：** 报表 42 的唯一操作键、外键与复合访问索引见[如何用约束保护业务规则并为读取建立索引？](database-constraints-and-indexes.md)。实际事务隔离和本地提交保证见[事务隔离与 WAL 能保证什么？](database-transactions-isolation-and-recovery.md)。

> [!info]- 来源
> - NULL 比较、IS NULL 与 IS DISTINCT FROM：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite [Expressions](https://www.sqlite.org/lang_expr.html)，核对于 2026-11-06。
> - LEFT JOIN 的匹配与空扩展行：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1；SQLite [SELECT](https://www.sqlite.org/lang_select.html)，核对于 2026-11-06。
> - WHERE、GROUP BY、HAVING 顺序与聚合函数的非空输入规则：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.2–7.2.3 与 [Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)，核对于 2026-11-06。
