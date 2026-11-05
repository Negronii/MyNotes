# How do database indexes trade lookup cost against update and storage cost? / 数据库索引如何权衡查找、更新与存储成本？

An index maps search keys to rows or pages so some lookups avoid scanning the whole relation. Each structure trades query patterns against maintenance, space, and locality; B+ trees maintain ordered paths using balanced page-level splits and merges. / 索引将搜索键映射到行或数据页，使部分查询无需扫描整个关系。不同结构在查询模式、维护、空间和局部性之间取舍；B+ 树通过平衡的页级分裂与合并维护有序访问路径。

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
