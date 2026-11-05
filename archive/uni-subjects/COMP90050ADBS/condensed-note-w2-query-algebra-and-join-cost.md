# How do relational algebra and join algorithms turn queries into I/O work? / 关系代数与连接算法如何把查询转化为 I/O 工作？

Relational algebra describes logical operations; a physical join algorithm specifies how tuples and pages are visited. Its page-read formula is meaningful only with the stated assumptions about buffers, indexes, caching, and result-output work. / 关系代数描述逻辑操作；物理连接算法规定如何访问元组与数据页。页读取公式只有在缓冲、索引、缓存和结果输出等前提明确时才有意义。

## Database Engine (Database management system)
![database engine](database_engine.png)
The diagram highlights the query evaluation engine, file manager, buffer manager, indexes, and stored data as execution-time performance components; query optimization also depends on statistics, configuration, and workload.

## Relational Algebra & Join / 关系代数与连接
Table – “Employee”
|ID|Name|Age|
|---|---|---|
|1001|A|25|
|1002|B|32|
|1003|C|19|
|1004|D|27|
|1005|E|40|
|1006|F|36|

Table - "Manager"

| ID   | Department |
| ---- | ---------- |
| 1001 | a          |
| 1003 | b          |
| 1004 | c          |
| 1006 | d          |

Table - "Location"

| ID   | Country   | City      |
| ---- | --------- | --------- |
| 1001 | China     | Beijing   |
| 1002 | Australia | Melbourne |
| 1004 | China     | Shanghai  |
| 1006 | Australia | Sydney    |

- Attribute (column)
- Record (row)
- Query examples (IDs are joined across the three tables):
  - Names of all employees older than 25: **B, D, E, F**. Age 25 is not over 25.
        SELECT Name FROM Employee WHERE Age > 25;
  - Names of managers located in Australia: **F**. Join Employee to Manager to identify managers, then join to Location and filter the country.
        SELECT E.Name
        FROM Employee AS E
        JOIN Manager AS M ON M.ID = E.ID
        JOIN Location AS L ON L.ID = E.ID
        WHERE L.Country = 'Australia';

### Join
Join is a very common and very expensive operation

Different types of join: inner join, outer join... (we focus on inner join)
A natural join matches columns with the same name in both inputs; an explicit theta join uses a specified predicate.
![$r \bowtie_θ s$](./join-syntax.png)
$r \bowtie_θ s$

- r: **outer** relation
- s: **inner** relation
- r and s are two tables
- Theta (θ) is the join predicate; it need not be a single common column.

### Relational Algebra Expressions
#### Overview
Classical relational algebra uses set semantics, while SQL SELECT defaults to retaining duplicate rows (bag semantics). The equivalence below is at the set-semantics level; use DISTINCT when exact classical projection behavior is needed ([PostgreSQL SELECT documentation](https://www.postgresql.org/docs/18/sql-select.html#SQL-SELECT-DISTINCT)).

```sql
Select A1, A2, ..., An
FROM r1, r2, ..., rm
Where P
```

.... Is same as the following in relational algebra expression:

$$
\Pi_{A_1, A_2, ..., A_n}(\sigma_P(r_1 \times r_2 \times ... \times r_m))
$$

#### Example
```sql
SELECT *
FROM r1 AS T1
INNER JOIN r2 AS T2 ON T1.a = T2.b;
```

```sql
SELECT salary
FROM Employees
INNER JOIN Managers
ON Employees.EmpID = Managers.EmpID;
```

.... Is same as the following in relational algebra expression:

$$
\Pi_{\text{salary}}(\sigma_{\text{Employees.EMPID}=\text{Managers.EMPID}}(\text{Employees} \times \text{Managers}))
$$

#### Example
```sql
Select salary
From Employees Where salary < 60000
```

Is same as the following in relational algebra expression:

$$
\Pi_{salary}(\sigma_{salary<60000}(Employees))
$$

Can also be written as:

$$
\sigma_{salary < 60000} (\Pi_{salary} (Employees))
$$

## Two types of Join Algorithm
### How data is stored in disk?
- Files – A database is mapped into different files. A file is a sequence of records.
- Data blocks – Each file is mapped into fixed length storage units, called data blocks (also called logical blocks, or pages)

Example: if a record is 55 bytes and a page is 4,096 bytes, the idealized capacity is $\lfloor 4096/55 \rfloor=74$ records per page. This ignores page headers, slot directories, alignment, and other storage overhead.

### Nested Loop Join
```sql
for each tuple tr in r do begin
    for each tuple ts in s do begin
        test pair (tr,ts) to see if they satisfy the join condition theta (θ)
        if they do, add tr • ts to the result.
    end
end
```

- Requires no indices because it checks everything in r against everything in s
- Expensive since it **examines every pair of tuples** in the two relations.
- Could be cheap if you do it on two small tables where they fit to main memory (disk brings the whole tables with first block access).
- Under the textbook assumption of one buffer page per input and no useful index/cache, tuple nested-loop join reads the outer relation once and scans the inner relation once per outer tuple: $b_r+n_r b_s$ page reads. CPU comparisons and result-output cost are omitted.

### Page-Oriented Nested-Loop Join
```sql
for each page Br of r do begin
    for each page Bs of s do begin
        for each tuple tr in Br do begin
            for each tuple ts in Bs do begin
                Check if (tr,ts) satisfy the join condition
                if they do, add tr • ts to the result.
            end
        end
    end
end
```

- Variant of nested-loop join in which every page of inner relation is paired with every page of outer relation.
- With one buffer page per input, page-oriented nested-loop join reads the outer relation once and scans the inner relation once per outer page: $b_r+b_r b_s$ page reads. This simplified estimate omits CPU and result-output cost.

### Example of simple and page-oriented calculation
Let’s see an example with the following bank database:

- Number of records of customer: 10,000 depositor: 5000
- Number of Pages of customer: 400 depositor: 100

#### Simple Nested-Loop Join
- With depositor as the outer relation: $b_r + n_r b_s = 100 + 5000 \times 400 = 2{,}000{,}100$ page reads.
- With customer as the outer relation: $400 + 10{,}000 \times 100 = 1{,}000{,}400$ page reads.

#### Page-oriented Nested-Loop Join
- With depositor as the outer relation: $b_r + b_r b_s = 100 + 100 \times 400 = 40{,}100$ page reads.
- With customer as the outer relation: $400 + 400 \times 100 = 40{,}400$ page reads.
