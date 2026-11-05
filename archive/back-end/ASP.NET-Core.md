# How should I read this versioned ASP.NET Core and EF Core reference? / 如何阅读这份有版本边界的 ASP.NET Core 与 EF Core 参考？

This is a set of connected examples rather than one production template: EF Core model and migration steps, entity-to-DTO mapping and scoped `DbContext`, controller behavior, MongoDB search, and local database containers have different contracts. Read each with its framework, package, provider, and environment assumptions. / 这份材料由彼此关联的示例组成，不是一套生产模板：EF Core 模型/迁移、实体到 DTO 的映射与 scoped `DbContext`、控制器行为、MongoDB 搜索和本地数据库容器各有不同契约。阅读时应保留框架、包、provider 与环境前提。

## Question map / 问题地图

- [How do EF Core model conventions and migrations define the schema? / EF Core 模型约定与迁移如何定义数据库结构？](aspnet-ef-model-and-migrations.md)
- [How do entities, DTOs, mappings, and DbContext scopes fit together? / 实体、DTO、映射与 DbContext 作用域如何配合？](aspnet-entities-dtos-and-dbcontext-lifetime.md)
- [How does the ASP.NET Core controller example map requests to stored data? / ASP.NET Core 控制器示例如何把请求映射到持久化数据？](aspnet-core-controller-example.md)
- [How does the MongoDB.Entities example prepare and search documents? / MongoDB.Entities 示例如何准备并搜索文档？](aspnet-mongodb-entities-search-example.md)
- [How do the PostgreSQL and SQL Server container examples connect to a .NET app? / PostgreSQL 与 SQL Server 容器示例如何连接 .NET 应用？](aspnet-local-database-container-examples.md)

[Data Access and Connection Pools](../../engineering-foundations/backend/data-access-and-connection-pools.md) explains the shared data-access lifecycle. / 数据访问与连接池笔记说明通用数据访问生命周期。
