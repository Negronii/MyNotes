# 这些索引语句和物理规则哪些只适用于 SQL Server？

应用要给订单表加唯一键、只查 2010 年后的订单，还要按位置筛选地理对象。若把某产品的索引默认行为直接当作可移植 SQL，迁移后可能得到不同的物理结构或直接执行失败。读者要看懂每条语句在 SQL Server 中做什么、依赖哪些前提，以及何时不能照搬。

## 聚集索引和非聚集索引分别保存什么？

clustered index (聚集索引) 按索引键值顺序组织表的数据行；SQL Server 每张表最多有一个，因为同一份数据行只能按一种聚集顺序存放。没有聚集索引的表是 heap (堆表)，行本身没有按聚集键排序。nonclustered index (非聚集索引) 是独立于数据行的结构，索引项保存键以及定位数据行的 row locator (行定位符)。

聚集索引的叶层保存完整数据行。非聚集索引的叶项用行定位符找到基表行：基表是堆时定位符是指向该行的指针，基表有聚集索引时定位符是聚集键，因此查到非聚集索引项后仍可能需要回表。

课程示例的语法如下：

~~~sql
CREATE CLUSTERED INDEX index1
ON dbo.table1 (column1);

CREATE UNIQUE NONCLUSTERED INDEX index2
ON dbo.table1 (column1 DESC, column2 ASC, column3 DESC);
~~~

unique index (唯一索引) 不允许索引键组合重复。复合索引中的键顺序、升降序和前导列会影响哪些查询能利用它；它不是“给列贴上唯一标签”而不付存储和更新代价。

在 SQL Server 中，定义 PRIMARY KEY (主键) 或 UNIQUE constraint (唯一约束) 会自动创建相应唯一索引。主键默认使用聚集索引，但若表已存在聚集索引，主键会由非聚集索引支撑；也可以显式声明主键为非聚集。不同数据库的主键默认物理组织不能由此推断。

删除索引使用该产品的对象限定语法：

~~~sql
DROP INDEX index1 ON dbo.table1;
~~~

## 过滤索引如何只维护一部分行？

filtered index (过滤索引) 是 SQL Server 的非聚集索引，可用谓词只收录满足条件的行。假设 `dbo.table1` 是订单表，`Year` 列为整数，且常见报表只查 2010 年之后的记录：

~~~sql
CREATE NONCLUSTERED INDEX IX_table1_column1_after2010
ON dbo.table1 (column1)
WHERE [Year] > 2010;
~~~

过滤条件决定哪些行进入索引，键列 `column1` 决定这些行按什么键顺序存储；两者是不同维度。查询结果必须是过滤索引所含行的子集，且优化器要能证明这一点。例如 `WHERE column1 = 42 AND [Year] >= 2020` 在行集合上属于过滤索引覆盖范围。因为查询比较条件与过滤表达式不等价，若要由索引直接判断该更严格的年份条件并覆盖查询，`Year` 应作为索引键或 INCLUDE 列；若未包含 `Year`，优化器仍可能先从过滤索引取候选，再回表读取 `Year` 并筛选，只是要付出查表成本。若查询是 `[Year] >= 2010`，它还需要 2010 年的行，过滤索引本身不能完整提供结果。

当查询中对过滤列使用与过滤表达式相同的谓词，且结果不需要返回 `Year` 时，`Year` 可不出现在索引键或 INCLUDE 列中，例如 `WHERE column1 = 42 AND [Year] > 2010` 且只选 `column1`。若查询要输出 `Year`，或用 `[Year] >= 2020` 这样的不同比较条件，若希望索引自身覆盖输出或判断条件，就应把该列列入索引键或 INCLUDE 列；没有该列时仍可通过回表取得它。过滤索引也有自己的过滤统计信息；它减少存储和维护并非免费保证，是否值得仍要对照实际查询与写入负载。

课程旧例把年份数字写成带引号的 '2010'。若 Year 是数值列，应写数值 2010；若列是文本，则字符排序与数值大小不是同一语义。

## SQL Server 的空间索引还要求什么？

spatial index (空间索引) 用 SQL Server 的几何网格把 geometry (平面几何类型) 或 geography (地球表面地理数据类型) 对象映射到空间单元。它是本产品的空间索引接口，并非通用 SQL 的标准索引语法。SQL Server 要求表具有 clustered primary key (聚集主键)，而 BOUNDING_BOX (包围盒参数) 只适用于 geometry 网格配置，geography 网格不能指定包围盒。

以下语句沿用课程示例的坐标范围：

下例假设 `dbo.SpatialTable` 已经具有聚集主键；否则 SQL Server 不允许创建该空间索引。

~~~sql
CREATE SPATIAL INDEX IX_SpatialTable_geometry
ON dbo.SpatialTable (geometry_col)
USING GEOMETRY_GRID
WITH (BOUNDING_BOX = (0, 0, 500, 200));
~~~

这里显式选择手动 `GEOMETRY_GRID` 网格，以 $(0,0)$、$(500,200)$ 作为本地平面坐标系的范围示例，不依赖手册示例中可能出现的默认网格。`BOUNDING_BOX` 决定索引划分的有限空间范围，不会裁剪几何对象，也不限制表中能存哪些坐标；盒外空间会被映射到编号为 0 的单元。要让空间索引最有效，包围盒应覆盖全部或大部分对象，因为只有完全落在盒内的对象操作能从该网格获得收益。该索引只提供候选筛选能力，是否采用仍由查询条件、空间谓词和优化器估价决定。空间索引的候选对象仍要满足精确几何条件，见[空间索引如何缩小搜索范围，又不漏掉几何结果？](./condensed-note-w2-spatial-indexes.md)。

## 视图可以像表一样建立索引吗？

SQL Server 支持 indexed view (索引视图)，但不能把任意查询结果直接当成已索引物化结果。视图定义、所有权、确定性、会话 SET 选项等都必须满足产品要求；创建视图时须使用 `WITH SCHEMABINDING`，然后先对视图建立唯一聚集索引。源表更新时，索引视图也要同步维护，可能增加写入成本。

所以应把普通视图、索引视图和表上的普通索引分开判断：能否创建、优化器是否能用、写入如何维护，都需要对照 SQL Server 对应版本的规则；迁移到另一产品时重新设计。

> [!info]- 来源
> - **SQL Server 聚集/非聚集索引、堆表、行定位符、主键与唯一约束默认索引：** [Microsoft Learn, Clustered and Nonclustered Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/clustered-and-nonclustered-indexes-described?view=sql-server-ver17)，2026-11-06 核验；这些默认与物理定义只针对 SQL Server。
> - **CREATE INDEX、DROP INDEX 以及唯一索引的产品语法：** [Microsoft Learn, CREATE INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-index-transact-sql?view=sql-server-ver17) 和 [DROP INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/drop-index-transact-sql?view=sql-server-ver17)，2026-11-06 核验。
> - **过滤索引只覆盖谓词选出的部分行；查询谓词须属于过滤范围，且过滤列是否需为键列或 INCLUDE 列取决于比较谓词是否等价及查询是否返回该列：** [Microsoft Learn, Create Filtered Indexes](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/create-filtered-indexes?view=sql-server-ver17)，2026-11-06 核验。
> - **空间索引要求聚集主键，geometry 与 geography 网格及包围盒选项：** [Microsoft Learn, CREATE SPATIAL INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-spatial-index-transact-sql?view=sql-server-ver17)；**包围盒确定索引划分范围，盒外映射到 cell 0，且应覆盖全部或大部分对象：** [Microsoft Learn, Spatial Indexes Overview](https://learn.microsoft.com/en-us/sql/relational-databases/spatial/spatial-indexes-overview?view=sql-server-ver17#the-bounding-box)，2026-11-06 核验；本例显式选 `GEOMETRY_GRID`，并只对 geometry 指定 BOUNDING_BOX。
> - **索引视图的 schemabinding、唯一聚集索引和源表写入维护：** [Microsoft Learn, Create Indexed Views](https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views?view=sql-server-ver17)，2026-11-06 核验。
