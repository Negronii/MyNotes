# Query Processing and Indexing / 查询处理与索引

核心概念：查询先表示为关系操作，再由优化器按统计信息估算计划成本；索引和连接算法改变访问代价，不保证任何固定加速。空间索引的包围盒用于筛选候选，还需用精确几何谓词确认；索引语法和物理行为取决于数据库产品。

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

## Query Cost & Query Optimization / 查询成本与优化
1. Parse query to relational algebra expression
2. Use optimizer and get execution plan
3. execute and get output

For example, [PostgreSQL's planner documentation](https://www.postgresql.org/docs/18/planner-optimizer.html) describes plan search and cost estimates; these remain estimates, not a guarantee that the chosen plan is fastest for every execution.

### Transaction Processing at core of RDBS
Definition: A transaction is a collection of operations that need to be performed as a complete unit. (e.g., A transfers $100 to B)

Structure of a transaction

```
begin_transaction()
    <sequence of operations to be performed>
    if (successful)
        commit_trans()
    else
        rollback()
end_transaction()
```

### Transaction Models - ACID Properties
- Atomicity: a transaction's changes are committed as a unit or rolled back as a unit. A duplex write can help protect a block, but does not by itself provide transaction atomicity.
- Consistency: a transaction should preserve declared constraints and application invariants. The DBMS can enforce declared constraints; application-level rules still need correct transactional logic.
  - For example, a primary key enforces uniqueness and non-nullness for the chosen key columns.
- Isolation controls which concurrent effects a transaction can observe. Together with atomic commit, it prevents another transaction from observing only one side of a completed transfer; isolation alone does not make the debit and credit atomic.
- Durability: the system should tolerate system failures and any committed updates should not be lost.

ACID properties might sometimes conflict with each other, yet, the system must still ensure:

- fast access to large amounts of data,
- provide a secure and stable repository when things fail,
- offer standard interfaces for data definition and manipulation,
- manage multi-user access in an orderly manner,
- allow convenient ways for report production and browsing,
- and ease data loading, archiving, and performance tuning.

### Query Optimisation Example - 2021Win Question 10
In the following figure we see two equal expressions a query optimizer is looking at to decide which one to run eventually:
![see below formula](./21winQ10.png)

$$
\Pi_{customer\_name}\sigma_{branch_city=Brooklyn}\bowtie(branch, \bowtie(account, depositor))
$$

$$
\Pi\bowtie(\sigma_{branch\_city=Brooklyn}, \bowtie(account, depositor))
$$

Please describe which one of these plans the optimizer should choose and why. Is this choice true in general? If so, where in query optimization such an observation can be used? Briefly explain.

**Answer**: Given the pictured query and the assumption that the Brooklyn predicate selects fewer branch rows, push the selection down before the join; the smaller intermediate relation can reduce join work. This is a heuristic and cost-based optimizers compare estimated plans: selectivity, available indexes, ordering, memory, and downstream operations can make another plan cheaper.

### How do query optimizer make the choices?
Steps in cost-based query optimization

1. Generate logically equivalent expressions of the SQL statement
2. Annotate resultant expressions to get alternative query plans
3. Choose the cheapest plan based on the estimated cost

### Estimation of plan cost based on:
- Statistical information about tables. Example: number of distinct values for an attribute
- Statistics estimation for intermediate results to compute cost of complex expressions
- Cost formulae for algorithms, computed using statistics again

### How to generate alternatives?
- SQL is declarative; an optimizer can translate it into internal relational operators and use equivalence rules to explore logically equivalent plans. Relational algebra provides a formal basis for many such transformations.
- One can generate all equivalent expressions exhaustively
- The above approach is very expensive in space and time though (In query optimizer some expressions are not generated if they are for sure very complex)

### How to choose?
- Must consider the interaction of evaluation techniques when choosing evaluation plans
- Choosing the cheapest algorithm for each operation independently may
  not yield best overall algorithm
- E.g., merge-join may be costlier than hash-join, but may provide a sorted output which could be useful later (the sorted result may be benefit to the later operation)

### In Real Life
- Practical query optimizers incorporate elements of the following two broad approaches:
  1. Search all the plans and choose the best plan in a cost-based fashion.
  2. Uses heuristics to choose a plan.
- Systems may use heuristics to reduce the number of choices that must be made in a cost-based fashion (because cost-based optimization is expensive)
- Heuristic optimization transforms the query-tree by using a set of rules that typically (but not in all cases) improve execution performance:
  1. Perform selections early (reduces the number of tuples)
  2. Perform projections early (reduces the number of attributes)
  3. Perform most restrictive selection and join operations (i.e. with smallest result size) before other similar operations
- Some systems use only heuristics, others combine heuristics with cost-based optimization
- Optimizers often use simple heuristics for very cheap queries, and perform exhaustive enumeration for more expensive queries

## Manage Query Cost in Practice
Troubleshoot plan and runtime regressions with engine-specific tools such as [SQL Server Query Store](https://learn.microsoft.com/en-us/sql/relational-databases/performance/query-store-usage-scenarios?view=sql-server-ver17), which retains query, plan, and runtime history and can be viewed through SQL Server tooling.

- Identify ‘regressed queries’ - Pinpoint the queries for which execution metrics have recently regressed (for example, changed to worse).
- Track specific queries - Track the execution of the most important queries in real time. (e.g., most frequently asked queries)

When you identify a query with suboptimal performance

- Force a query plan instead of the plan chosen by the optimizer
- Do we need an index? --- quickly find the data in the query
- Enforce statistic recompilation
- Rewrite query? (with parameters)

### Parameter in query
![](./query-optimization.png)

### To further lower query cost
- Store derived data
  - When you frequently need derived values
  - Original data do not change frequently
- Use pre-joined tables
  - When tables need to be joined frequently
  - Regularly check and update pre-joined table for updates in the original table May still return some ‘outdated’ result (pre-joined tables are not updated)

## Indexing / 索引
- DBMS admin generally creates indices to allow almost direct access to individual items (index = indice)
- DBMS must support
  - insert/delete/modify record
  - read a particular record (specified using record id)
  - scan all records (possibly with some conditions on the records to be retrieved), or scan a range of records

### Indexing overview
- Indexing mechanisms used to speed up access to desired data in a similar way to look up a phone book or dictionary
- **Search Key** - **attribute** or **set of attributes** used to look up records/rows in a system like an ID of a person (The ID will take us to get the entire record)
- An index file consists of records (called index entries) of the form search- key, pointer to where data is
- Index structures are often smaller than their base data, and frequently accessed pages may be cached in main memory; the cached working set depends on index size and available memory.

### Indexing makes Disk Access Time become faster through
- records with a **specified value** in the attribute accessed with minimal disk accesses (e.g., Student ID = 101, the index file tells us which data block in disk to go)
- records with an attribute value falling in a specified range of values can be retrieved with a single seek and then consecutive sequential reads (e.g., ID:100-200, find where is the first record (single seek of starting block), then read sequentially)
- Note: not all DB stores sequential data sequentially, so this method may not useful for some DB

### Criteria to choose index – always tradeoff
- Insertion time to index is also important
- Deletion time is important as well
- No big index rearrangement after insertion and deletion
- Space overhead needs to be considered for the index itself
- No single indexing technique is the best. Rather, each technique is best suited to particular applications.

### Types of indices based on search keys
Ordered indices – Search keys are stored in some order

- Clustering index / primary index
- Non-clustering index / secondary index
- Hash indices – Search keys are distributed
- **B+ tree**
- Bitmap index
- Trees for spatial data
  - Quadtree
  - k-d tree
  - R-tree

### Clustering Index / Primary Index
- in a sequentially **ordered file**, the index whose **search key** specifies the sequential order of the file
- The search key of a primary index is usually but not necessarily the **primary key**
  ![clustering-index](./clustering-index.png)
  As shown in graph, the order is sorted

### Non-clustering Index / Secondary Index
- An index whose **search key specifies an order** different from the sequential order of the file
- Secondary indices improve the performance of queries that use keys other than the search key of the clustering index.
  ![non-clustering-index](./non-clustering-index.png)
  As shown in graph, the search key here is the major

### Hash indices
- A hash function aims to spread distinct search-key values approximately uniformly across buckets.
- A hash index organizes the search keys, with their associated record pointers, into a hash file structure. Order is not important.
- Equal search-key values still hash to the same bucket. Skew or many duplicate records can overload a bucket and require overflow pages; bucket record counts need not be equal, and lookup is not guaranteed to take one I/O ([PostgreSQL hash indexes](https://www.postgresql.org/docs/18/hash-index.html)).
- Typical hash functions perform computation on the internal binary representation of the search-key.
  ![hash-indices](./hash-indice.png)
- With seven buckets, a hash function should distribute distinct keys across bucket values 0–6 approximately evenly; this does not guarantee the same number of records per bucket when keys repeat.
- Goes to which bucket here determined by Hash function return value, e.g. Hash(A-215) = 1

### Bitmap index
- Records in a relation are assumed to be numbered sequentially from, say, 0
- Applicable on attributes that take on a relatively small number of distinct Values
  - E.g. gender, country, state, ...
  - E.g. income-level (income broken up into a small number of levels such as 0-9999, 10000-19999, 20000-50000, 50000- infinity)
- A bitmap is simply an array of bits
- In its simplest form a bitmap index on an attribute has a bitmap for each value of the attribute
  - Bitmap has as many bits as records
  - In a bitmap for value v, the bit for a record is 1 if the record has the value v for the attribute, and is 0 otherwise
  - Used for business analysis, where rather than individual records say how much of one type exists is the query/important

![bitmap](./bitmap.png)
In this graph,

- gender is distinct value which is m or f
- income-level is distinct value, which is L1, L2, ..., L5

### B+ tree / B+树
Why?

- As an ordered file grows, insertions can create overflow pages and weaken locality; binary search can still be used only when the file's organization supports it, and may incur extra I/O. Periodic reorganization is one possible remedy.
- A B+ tree maintains balance through local splits and merges, keeping all root-to-leaf paths at the same depth. In this convention, order n is the maximum number of child pointers: each non-root internal node has between $\lceil n/2 \rceil$ and $n$ children, and each leaf has between $\lceil(n-1)/2 \rceil$ and $n-1$ key entries. The root has separate minimum-occupancy rules. For a product example, [SQL Server rowstore indexes are organized as B+ trees](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/clustered-and-nonclustered-indexes-described?view=sql-server-ver17).
- Special cases:
  - If the root is not a leaf, it has at least 2 children.
  - If the root is a leaf (that is, there are no other nodes in the tree), it can have between 0 and (n–1) values.

#### B+ tree Typical Node
![typical node](./b+typical.png)

- $K_i$ are ordered search-key values. Internal-node pointers refer to child pages; leaf entries contain a key and a record identifier, or a key and a bucket/record list, depending on the index. In a B+ tree file organization, leaves may instead contain the rows.
- Upper levels are often cached because they are smaller and accessed frequently, but the tree's height does not guarantee that they are resident in memory.

#### Example B+ tree
![example B+ tree](./b+treeexample.png)
In this graph, the nodes with _ are records, that's why all leaf nodes have _

#### Finding all records with a search-key value of k.
Using the illustrated convention, pointer $P_i$ lies immediately to the left of separator $K_i$:
1. N=root initially
2. Repeat
   1. Examine N for the smallest search-key value > k.
   2. If such a value exists, assume it is Ki. Then set N = Pi
   3. Otherwise k ≥ Kn–1. Set N = Pn . Follow pointer.
      Until N is a leaf node
3. If for some i, key Ki = k follow pointer Pi to the desired record or bucket.
4. Else no record with search-key value k exists.
   ![string search example](./B+treeStringExample.png)
   Note don't get confused by the Perryridge on the root, it is just the search key by chance.

#### Run range queries in B+ tree
Range queries find all records with search key values in a given range e.g., from Brandt to Singh
![range search example](./B+RangeSearchExample.png)

#### B+ tree - Insertion (2 types)
![B+ insertion example](./B+insertion.png)
![B+ insertion example 2](./B+Insertion2.png)
It will split nodes to avoid having leaf node > n–1

#### B+ tree - Deletion (2 types)
![B+ deletion example](B+Deletion1.png)
![B+ deletion example 2](B+TreeDeletion2.png)
It will merge to avoid having leaf node < ⎡(n–1)/2⎤

#### B+ tree – File organization
- Leaf nodes in a B+-tree file organization store records, instead of pointers to children
- Helps keep data records clustered (ordered) even when there are insertions/deletions/updates
- Insertion and deletion or records are handled in the same way as insertion and deletion of entries in a B+-tree index.

#### B+ tree Advantages
- Automatically reorganizes itself with small, local changes in the face of insertions and deletions.
- Reorganization of entire file is not required to maintain performance
- Similar to Binary tree in many aspects but the **fan out** is much higher (height of B+ tree is smaller than binary tree)

#### B+ tree Disdvantages
- Extra insertion and deletion over head and space over head (reorganisation)

Advantages of B+-trees outweigh disadvantages for DBMSs (B+ trees are used extensively)

### Considering location data (spatial data)
- Unlike things we can access by names, ids, there is a lot of data that exists, and increasingly that requires special indexing
- For example, spatial data requires more complex computations for accessing data,
  - e.g., intersections of objects in space
- There is no trivial way to sort items which is a key issue,
  - e.g., range query on a simple set of items, e.g. all restaurants within 5 KM
  - e.g., a Nearest Neighbour query, e.g. find the nearest restaurant of my location

### Quadtree (for location data - points) / 四叉树
- Each quadtree node represents a rectangular region; an internal node partitions it into four quadrants, recursively, until a chosen stopping condition (for example, a maximum number of points per leaf).
- A k-d tree is a different spatial structure: each internal node splits a region with one axis-aligned line into two children, often alternating axes. The exam example below is a k-d tree, not a quadtree.

#### Quadtree – e.g.,
Example: **Leaf nodes** have between zero and **some fixed maximum number** of points (set to 1 in example below)
![quad tree example](quadtreeExample.png)
It is keep spliting into squares until no more than n (1 in this example) leaf nodes are inside same square

#### Quadtree Tree structure
![tree](quadtreenodesexample.png)

#### Quadtree – e.g., run NN (nearest neighbor) query
![NN on quad tree](NNonQuadtree.png)

### k-d Tree / k-d 树
A k-d tree is a binary spatial search tree. Each internal node splits the current region into two using an axis-aligned boundary, often cycling through dimensions; unlike a quadtree, it does not divide every region into four quadrants ([Princeton, Geometric Applications of BSTs](https://algs4.cs.princeton.edu/92search/)).

#### 2022S1 Exam Question 5: k-d Tree Example
Given the k-d tree below with point data, where black labeled dots represent spatial coordinate data, and the rectangular area is divided into regions with the division order given with numbers: draw the associated k-d tree as a tree structure with leaves labeled as the data labels given below. Assume **left subarea** of a division goes to a **left subtree**, and **lower subarea** of a division also goes to a **left subtree**. The figure for the k-tree follows:
![Q5 graph](2022S1Q5.png)
The key idea is, for each division, split the current node (root) to 2 nodes. Put the left-down on left, right-up on right nodes.
![answer](2022S1Q5Answer.png)

### R-Trees / R树
- An R-tree is a balanced spatial index whose internal entries store minimum bounding rectangles (MBRs) for child subtrees; leaves index spatial objects. It is not simply a B+ tree with a one-dimensional interval replaced. See [Guttman's original 1984 R-tree paper](https://www.cs.princeton.edu/courses/archive/fall08/cos597B/papers/rtrees.pdf).
- Child MBRs may overlap, so a range query can visit multiple subtrees; the index returns candidates that must be checked with the exact spatial predicate. Variants include R+ trees and R* trees.
- **Bounding boxes of children of a node are allowed to overlap**
- Note: A **bounding box** of a node is a minimum sized rectangle that contains all the rectangles/polygons associated with the node

#### R-Tree example
![R-Tree example](RtreeExample.png)
A range query tests relevant MBRs and may descend into multiple children when their bounds overlap. Candidate geometries still need the exact predicate, since MBR overlap alone does not prove an exact match.

## Using Indexes in SQL
### Index Definition in SQL
- Index creation and physical organization are DBMS-specific. In SQL Server, UNIQUE constraints are backed by a unique index; a PRIMARY KEY is clustered by default only when the table has no clustered index, and can be declared nonclustered. Other products use different defaults and terminology.
- Indexes on views are also product-specific and have additional restrictions; a query result is not universally indexable.

### Create an index
SQL syntax varies by product. The following CLUSTERED, NONCLUSTERED, filtered-index, and spatial-index examples use SQL Server syntax ([index architecture](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide?view=sql-server-ver17)).

1. Create a clustered index on a table
   CREATE CLUSTERED INDEX index1 ON table1 (column1);
2. Create a non-clustered index with a unique constraints
   CREATE UNIQUE INDEX index1 ON table1 (column1 DESC, column2 ASC, column3 DESC);

(A unique index is one in which no two rows are permitted to have the same index key value)

### Drop an index (SQL Server)
DROP INDEX index_name ON table_name; ([official SQL Server syntax](https://learn.microsoft.com/en-us/sql/t-sql/statements/drop-index-transact-sql?view=sql-server-ver17))

Most database systems allow specification of type of index, and clustering

### Specialized indexes - Filtered index
CREATE INDEX index1 ON table1 (column1) WHERE [Year] > '2010';

(A filtered index is an optimized nonclustered index, suited for queries that select a small percentage of rows from a table. It uses a filter predicate to index a portion of the data in the table)

### Spatial index
In SQL Server, a spatial index is defined for a geometry or geography column and has product-specific requirements, including a clustered primary key. The BOUNDING_BOX option applies to geometry; geography indexes use a different configuration ([CREATE SPATIAL INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-spatial-index-transact-sql?view=sql-server-ver17)).

CREATE SPATIAL INDEX index_name ON table_name(Geometry_type_col_name) WITH ( BOUNDING_BOX = ( 0, 0, 500, 200 ) );

## Summary
- There is no point going through all index types for all data types
  - There is hundreds of them
  - Even each type would have many subtypes
    - E.g., MX-CIF quadtree is one quadtree type among many
  - Same with R-trees, etc
  - Same with many other index types
- Given a data set, when uploading to the DBMS
  - Find the potential query types
  - Research what indices that particular DBMS would have for that data type
  - Research for what queries you would better do on what index
  - Create index if you have large data
  - Monitor performance
  - Tune or create other indices
  - Your DMBS will have a version of the “create index” SQL statement
