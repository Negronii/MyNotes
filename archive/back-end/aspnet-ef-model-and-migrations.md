# How do EF Core model conventions and migrations define the schema? / EF Core 模型约定与迁移如何定义数据库结构？

EF Core builds a model from entity types and configuration, while migrations compare it with the project’s prior model snapshot. Review generated changes before application; the live database is not the source from which EF scaffolds them. This reference preserves mixed framework/package versions, including .NET 10 CLI differences and ASP.NET Core 7/AutoMapper 12 examples. / EF Core 根据实体类型与配置构建模型，迁移则将其与项目中的旧快照比较。应用前需审查生成内容；在线数据库不是 EF 推断变更的来源。本参考保留混合框架/包版本，包括 .NET 10 CLI 差异及 ASP.NET Core 7、AutoMapper 12 示例。

## Setup / 项目设置

### Create project/components

The .NET CLI can list templates and create a solution plus a Web API project. IDE workflows are also available.

```
dotnet new list
```

For a solution containing an MVC-controller Web API project, the following commands show the structure. The example uses current .NET 10 template behavior: solution files default to `.slnx`, and `webapi` defaults to minimal APIs unless `--use-controllers` is supplied. Earlier SDK templates differ.

```
dotnet new sln
dotnet new webapi --use-controllers -o src/AuctionService
dotnet sln add src/AuctionService/AuctionService.csproj
```

## Run the app / 运行应用

```
cd src/AuctionService
dotnet watch
```

## Add NuGet packages / 添加 NuGet 包

Use the IDE's package manager or the .NET CLI. Package references belong to the project file; select EF Core and provider package versions compatible with the target framework.

- Microsoft.EntityFrameworkCore.Design
- Npgsql.EntityFrameworkCore.PostgreSQL
- `AutoMapper.Extensions.Microsoft.DependencyInjection` is the integration package used by AutoMapper 12-era examples; starting with AutoMapper 13, `AddAutoMapper` moved into the core package and the separate DI package was discontinued.

### Installing NuGet Packages in Visual Studio

1. Right-click on the project name (not the solution name), e.g., `BulkyWeb (main)`.
2. Select "Manage NuGet Package".

For database connectivity, you can install the following packages:

- Microsoft.EntityFrameworkCore
- Microsoft.EntityFrameworkCore.SqlServer
- Microsoft.EntityFrameworkCore.Tools (for migrations)

### Installing NuGet Packages with `dotnet` CLI (Command Line Interface)

The examples use the .NET 9-and-earlier spelling. For .NET 10 and later, replace `dotnet add package` with `dotnet package add`:

```bash
dotnet add package Microsoft.EntityFrameworkCore
```

The corresponding provider package for SQL Server:

```bash
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
```

The design-time tools package is used with EF Core migrations:

```bash
dotnet add package Microsoft.EntityFrameworkCore.Tools
```

Run these commands in the terminal, making sure you are in the directory where your `.csproj` file resides.

## Install Entity Framework Core CLI tools

```
dotnet tool install --global dotnet-ef
```

or update with

```
dotnet tool update --global dotnet-ef
```

Run package commands from the project directory or pass `--project`. Keep the `dotnet-ef` tool's major version compatible with the EF Core packages used by the project.

## Primary keys and required properties / 主键与必需属性

You can specify the primary key for a table in a C# model class like so:

```csharp
using System.ComponentModel.DataAnnotations;

public class Category
{
    [Key]
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public int DisplayOrder { get; set; }
}
```

## Nullability and `[Required]` / 可空性与 `[Required]`

`[Required]` configures a required member for validation/model metadata; it does not change the C# property's declared nullable type. With nullable reference types enabled, EF Core uses `string` versus `string?` by convention for required versus optional properties; annotations or Fluent API can also configure the model. Make the compiler, EF model, request validation, and database schema agree intentionally:

```csharp
using System.ComponentModel.DataAnnotations;

public class Category
{
    public int Id { get; set; }
    [Required]
    public string Name { get; set; } = string.Empty;
    public int DisplayOrder { get; set; }
}
```

> **Note**: The `[Key]` attribute is not necessary when the property is named `Id` or `<ClassName>Id`. It is implicitly treated as the primary key. In other cases, such as a property named `Name`, you would need to explicitly add the `[Key]` attribute.

## EF Core migrations / EF Core 迁移

Scaffolding a migration compares the current EF Core model with the previous model snapshot checked into the project; it does **not** inspect the live database schema to infer changes. Review the generated migration, especially for renames and data loss, before applying it. `database update` applies pending migrations to the configured database and records applied migration IDs in the migrations history table. This command is useful for local development; a reviewed SQL script or migration bundle is often preferable for production deployment.

```
dotnet ef migrations add "InitialCreate" -o Data/Migrations
```

After adding the migration, you can update the database with the newly added migration using the following command:

```
dotnet ef database update
```

## Add a gitignore file

```
dotnet new gitignore
```

# Concepts

## Sources / 参考资料

- Microsoft Learn: [EF Core migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations) and [applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying); the latter describes review, scripts/bundles, and runtime migration tradeoffs.
- Microsoft Learn: [EF Core required and optional properties](https://learn.microsoft.com/en-us/ef/core/modeling/entity-properties), [ASP.NET Core controller injection](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection), [dependency-injection lifetimes](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection), [MVC validation of non-nullable parameters](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-7.0#non-nullable-reference-types-and-required-attribute), [.NET package CLI syntax](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies), [.NET 10 solution-file default](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default), [Web API template defaults](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates), and [Azure Data Studio retirement](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio).
- [AutoMapper dependency injection](https://docs.automapper.org/en/latest/Dependency-injection.html) documents that `AddAutoMapper` is in the core package starting with v13; the package list above preserves an older v12-era reference.
- [Npgsql connection-string parameters](https://www.npgsql.org/doc/connection-string-parameters), [MongoDB official image documentation](https://hub.docker.com/_/mongo), and the [official PostgreSQL image `PGDATA` and volume guidance](https://raw.githubusercontent.com/docker-library/docs/master/postgres/README.md#pgdata) for connection fields, data directories, initialization, and authentication details. The Compose sample is pinned to PostgreSQL 17's volume layout; PostgreSQL 18+ changes it.
- Microsoft Learn: [SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker) and [container security](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-security) for host support and the `MSSQL_SA_PASSWORD` variable.
- The `MongoDB.Entities` snippets are pinned to the course's `22.1.0` package reference; the project's [API docs](https://mongodb-entities.com/api/MongoDB.Entities.DB.html) and [index guide](https://mongodb-entities.com/wiki/Indexes.html) document the corresponding concepts. The [v22.1 `Find` source](https://github.com/dj-nitehawk/MongoDB.Entities/blob/aced47f36f152c6a0e13fe827f1a2bce310826dd/MongoDB.Entities/Builders/Find.cs) shows that sort definitions are appended and text-score sorting uses the same sort path; the text-query branch therefore selects score ordering without also appending `Make`. Current docs may describe a later package version.
