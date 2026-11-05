# How do the PostgreSQL and SQL Server container examples connect to a .NET app? / PostgreSQL 与 SQL Server 容器示例如何连接 .NET 应用？

The examples pair connection strings with specific local container setups. PostgreSQL 17’s data mount differs from PostgreSQL 18+, while the SQL Server 2019 Linux container example is scoped to Microsoft’s documented x86-64 Linux host support, not macOS. Keep local credentials outside committed settings. / 这些示例把连接字符串与特定本地容器配置配对。PostgreSQL 17 的数据挂载路径与 PostgreSQL 18+ 不同；SQL Server 2019 Linux 容器示例受微软公布的 x86-64 Linux 主机支持范围限制，不适用于 macOS。本地凭证应放在未提交的设置中。

## Run a postgres db

The combined Compose example above already includes PostgreSQL. To run only PostgreSQL, keep that service and its named volume and remove MongoDB. For a deliberate local setup, start it with `docker compose up -d`. Npgsql uses separate `Host` and `Port` fields:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Information"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5432;Username=postgres;Password=replace-with-local-secret;Database=auctions"
  }
}
```

## SQL Server Linux container / SQL Server Linux 容器

This is a historical SQL Server 2019 container example, not a macOS support claim. Microsoft documents SQL Server Linux container support for Linux hosts with x86-64 CPUs and marks emulation/translation environments as unsupported; check current platform support before choosing a host. The `2019-latest` image tag pins a major line but can still move within that line.

Run the following command in your terminal:

```zsh
docker run -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD=replace-with-a-local-secret' -p 1433:1433 --name sql_server_container -d mcr.microsoft.com/mssql/server:2019-latest
```

`SA_PASSWORD` is deprecated for these images; use `MSSQL_SA_PASSWORD`. Do not commit a real password. For a macOS host, this command is not a supported deployment recipe under Microsoft's published host requirements.

### Connecting to SQL Server / 连接 SQL Server

1. Use a supported SQL client. Azure Data Studio retired on 2026-02-28; Microsoft points users to Visual Studio Code with the MSSQL extension or SQL Server Management Studio where supported.
2. Fill in the details:
   - Server: `localhost,1433`
   - Authentication Type: SQL Login
   - User name: `sa`
   - Password: the local secret supplied to `MSSQL_SA_PASSWORD`
3. Click "Connect".

### Creating a New Database

1. Right-click on the "Databases" folder under the connected server in the "SERVERS" panel.
2. Select "New Database" and name it `SampleDb`.
3. Click "OK".

### Updating appsettings.json for Database Connection

Update `appsettings.json` to include your database connection string:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost,1433;Database=SampleDb;User Id=sa;Password=replace-with-local-secret;TrustServerCertificate=True;"
  }
}
```

`TrustServerCertificate=True` is a local-development shortcut in this example; use the certificate-validation settings required by the deployment environment. Keep credentials outside committed settings files.

## Sources / 参考资料

- Microsoft Learn: [EF Core migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations) and [applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying); the latter describes review, scripts/bundles, and runtime migration tradeoffs.
- Microsoft Learn: [EF Core required and optional properties](https://learn.microsoft.com/en-us/ef/core/modeling/entity-properties), [ASP.NET Core controller injection](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection), [dependency-injection lifetimes](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection), [MVC validation of non-nullable parameters](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-7.0#non-nullable-reference-types-and-required-attribute), [.NET package CLI syntax](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies), [.NET 10 solution-file default](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default), [Web API template defaults](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates), and [Azure Data Studio retirement](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio).
- [AutoMapper dependency injection](https://docs.automapper.org/en/latest/Dependency-injection.html) documents that `AddAutoMapper` is in the core package starting with v13; the package list above preserves an older v12-era reference.
- [Npgsql connection-string parameters](https://www.npgsql.org/doc/connection-string-parameters), [MongoDB official image documentation](https://hub.docker.com/_/mongo), and the [official PostgreSQL image `PGDATA` and volume guidance](https://raw.githubusercontent.com/docker-library/docs/master/postgres/README.md#pgdata) for connection fields, data directories, initialization, and authentication details. The Compose sample is pinned to PostgreSQL 17's volume layout; PostgreSQL 18+ changes it.
- Microsoft Learn: [SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker) and [container security](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-security) for host support and the `MSSQL_SA_PASSWORD` variable.
- The `MongoDB.Entities` snippets are pinned to the course's `22.1.0` package reference; the project's [API docs](https://mongodb-entities.com/api/MongoDB.Entities.DB.html) and [index guide](https://mongodb-entities.com/wiki/Indexes.html) document the corresponding concepts. The [v22.1 `Find` source](https://github.com/dj-nitehawk/MongoDB.Entities/blob/aced47f36f152c6a0e13fe827f1a2bce310826dd/MongoDB.Entities/Builders/Find.cs) shows that sort definitions are appended and text-score sorting uses the same sort path; the text-query branch therefore selects score ordering without also appending `Make`. Current docs may describe a later package version.
