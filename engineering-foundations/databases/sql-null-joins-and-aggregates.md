# How do NULLs, joins, and grouping change SQL results? / NULL、连接与分组会怎样改变 SQL 查询结果？

**How do NULL, outer joins, and grouping change a query result? / NULL、外连接和分组会怎样改变查询结果？** An ordinary comparison such as `=` or `<>` with `NULL` is UNKNOWN; null-aware predicates such as `IS NULL` and `IS DISTINCT FROM` have their own rules. Use `IS NULL` for missing values, and remember that `WHERE` keeps only TRUE. Put a right-side condition in `LEFT JOIN ... ON` when unmatched left rows must remain; a `WHERE` condition can remove those rows. `COUNT(*)` counts joined rows, `COUNT(column)` skips nulls, `WHERE` filters input rows, and `HAVING` filters completed groups. Inspect query plans with the chosen engine and version. / `=` 或 `<>` 这类普通比较遇到 `NULL` 时结果为 UNKNOWN；`IS NULL`、`IS DISTINCT FROM` 等空值判定或相异性谓词有各自的规则。缺失值应使用 `IS NULL`，并记住 `WHERE` 只保留 TRUE。若要保留没有匹配右表记录的左表行，应把右表条件放在 `LEFT JOIN ... ON` 中；放在 `WHERE` 中可能移除这些行。`COUNT(*)` 统计连接后的行数，`COUNT(column)` 跳过空值；`WHERE` 筛选分组前的输入行，`HAVING` 筛选已完成的分组。查询计划应使用所选数据库及其版本来检查。

~~~mermaid
flowchart LR
    Predicate[SQL comparison with NULL] --> Unknown[UNKNOWN]
    Predicate -->|ordinary non-null comparison| TrueFalse[TRUE or FALSE]
    Unknown --> Where[WHERE keeps only TRUE]
    TrueFalse --> Where
    Left[Left-side row] --> On{ON finds a match?}
    On -->|no| NullRow[Null-extended right columns]
    On -->|yes| Joined[Joined row]
    NullRow --> PostWhere{Post-join WHERE is TRUE?}
    Joined --> PostWhere
    PostWhere -->|no: FALSE or UNKNOWN| Drop[Row disappears]
~~~

**Key terms / 关键术语：** NULL / 空值；three-valued logic / 三值逻辑；LEFT JOIN / 左外连接；null-extended row / 空扩展行；aggregate / 聚合；HAVING / 分组筛选。

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



These result rules are shared by the examples' SQLite run; optimizer plans are not. Use the selected engine's `EXPLAIN` tool on representative data, and label any plan observation with its engine and version.


**Sources / 来源：** PostgreSQL 18 [SQL tutorial](https://www.postgresql.org/docs/18/tutorial-sql.html), [comparison predicates](https://www.postgresql.org/docs/18/functions-comparison.html), [table expressions and joins](https://www.postgresql.org/docs/18/queries-table-expressions.html), and [aggregate functions](https://www.postgresql.org/docs/18/functions-aggregate.html), checked 2026-10-15; SQLite [SELECT](https://www.sqlite.org/lang_select.html), [expressions](https://www.sqlite.org/lang_expr.html), and [aggregate functions](https://www.sqlite.org/lang_aggfunc.html). The customer/order result queries ran with Python sqlite3 against SQLite 3.51.0 with foreign-key enforcement enabled.
