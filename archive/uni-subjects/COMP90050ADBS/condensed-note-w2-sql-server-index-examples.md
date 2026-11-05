# Which index statements here are specific to SQL Server? / 此处哪些索引语句专属于 SQL Server？

Index DDL and physical defaults vary by product. The clustered, nonclustered, filtered, and spatial-index examples here use SQL Server syntax and must not be read as portable SQL guarantees. / 索引 DDL 与物理默认行为因产品而异。此处 clustered、nonclustered、filtered 和 spatial-index 示例使用 SQL Server 语法，不是可移植的 SQL 保证。

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
