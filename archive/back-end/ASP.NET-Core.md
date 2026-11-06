# ASP.NET Core 与 EF Core 示例如何阅读？

这里整理了 EF Core 模型与迁移、实体到 DTO 的映射与 scoped DbContext、控制器、MongoDB 搜索和本地数据库容器示例。它们彼此相关，但不是一套生产模板；阅读时要保留各自的框架、包、provider 与环境前提。

## 主题入口

- [ASP.NET Core 控制器如何把 HTTP 请求送到正确的操作并返回结果？](aspnet-core-controller-example.md)
- [请求数据与持久化实体如何经由 DbContext 完成一次写入？](aspnet-entities-dtos-and-dbcontext-lifetime.md)
- [EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？](aspnet-ef-model-and-migrations.md)
- [本地 PostgreSQL 与 SQL Server 容器怎样连接到 .NET 服务？](aspnet-local-database-container-examples.md)
- [MongoDB 文档搜索怎样从启动初始化走到相关度排序？](aspnet-mongodb-entities-search-example.md)

[怎样限定对象关系映射会话并排查连接池耗尽？](../../engineering-foundations/backend/data-access-and-connection-pools.md)说明通用的数据访问生命周期。
