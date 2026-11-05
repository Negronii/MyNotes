# How do data warehouses collect, integrate, and summarize source data? / 数据仓库如何采集、整合并汇总源数据？

A warehouse integrates data from operational sources for analysis. Collection triggers, freshness, schema integration, cleansing, update propagation, and retained detail depend on the analytical purpose. / 数据仓库整合操作型数据源以供分析。采集触发、时效、模式整合、清洗、更新传播和保留细节都取决于分析目的。

## Data Warehousing
![](dataWarehousnig.png)

- A classical data warehouse consolidates historical data from multiple sources under an integrated schema for analysis. Modern warehouses may be physically distributed.
- When and how to gather data
  - Source driven architecture: data sources transmit new information to warehouse, either continuously or periodically (e.g. at night) I.e. data source give out
  - Destination driven architecture: warehouse periodically requests new information from data sources. I.e. Data warehouse requesting

### Data Warehousing – Design Issues
- Synchronous coordination such as two-phase commit across an OLTP source and analytical warehouse can add latency and reduce availability. Many designs accept ingestion lag and load updates periodically, but freshness requirements vary by workload.
- What schema to use
  - Depends on purpose
  - Schema integration
- Data cleansing
  - e.g., Correct mistakes in addresses (misspellings, zip code errors)
  - e.g., Merge address lists from different sources and purge duplicates
- How to propagate updates - The data stored in a data warehouse is documented with an element of time, either explicitly or implicitly
- What data to summarize
  - Raw data may be too large to store
  - Aggregate values (totals/subtotals) often suffice
  - Where the engine supports materialized-view rewrite and the query is eligible, a query on raw data may be answered from a stored aggregate.
