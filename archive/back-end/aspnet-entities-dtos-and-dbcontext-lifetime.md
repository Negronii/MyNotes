# How do entities, DTOs, mappings, and DbContext scopes fit together? / 实体、DTO、映射与 DbContext 作用域如何配合？

Entities describe the persistence model; DTOs define data crossing the API boundary. Mapping profiles connect the shapes, while a scoped `DbContext` tracks work within a request or an explicit startup scope and is disposed with it. / 实体描述持久化模型，DTO 定义跨 API 边界的数据形状。映射配置连接两种结构；scoped `DbContext` 在请求或显式启动 scope 内跟踪工作，并随 scope 释放。

## Entities / 实体

An entity is a domain/model object whose identity and relationships matter to the application. EF Core tracks entity types described in its model; relational entity types often map to tables, but the mapping is configurable and is not simply one CLR class per table in every model. Changes to a mapped model can affect future migrations.

## DTO

**Data Transfer Objects (DTOs)** shape data crossing an API or process boundary. Separate request/response DTOs let an API define its input and output contracts without exposing every persistence field. DTOs are commonly property-oriented data objects; validation and mapping are explicit concerns rather than behavior supplied automatically by the type name.

## Mappings

Example

```csharp
using AuctionService.DTOs;
using AuctionService.Entities;
using AutoMapper;

namespace AuctionService.RequestHelpers;

public class MappingProfiles: Profile
{
    public MappingProfiles()
    {
        CreateMap<Auction, AuctionDto>().IncludeMembers(x => x.Item);
        CreateMap<Item, AuctionDto>();
        CreateMap<CreateAuctionDto, Auction>()
            .ForMember(d => d.Item, o => o.MapFrom(s => s));
        CreateMap<CreateAuctionDto, Item>();
    }
}
```

**CreateMap**

CreateMap essentially sets up a mapping profile to convert one object type into another. AutoMapper uses these profiles to know how to automatically perform the conversion when you call \_mapper.Map<>().

`AutoMapper`

A Profile in AutoMapper allows you to organize your mappings. You could potentially have different profiles for different parts of your application or different mapping scenarios. In essence, it encapsulates configurations for your object-object mappings. When you register your profiles, AutoMapper knows which mappings are valid.

`Map<TDestination>(source)` identifies the destination type explicitly; having multiple configured maps from one source type is not inherently ambiguous. AutoMapper can also map collections when the element-type map is configured. Keep mapping configuration focused and test nontrivial mappings rather than treating generated mappings as a substitute for API-contract review.

## DbContext

A simple Db context example:

```Csharp
using AuctionService.Entities;
using Microsoft.EntityFrameworkCore;

namespace AuctionService.Data;

public class AuctionDbContext : DbContext {

    public AuctionDbContext(DbContextOptions<AuctionDbContext> options) : base(options) {}

    public DbSet<Auction> Auctions { get; set; }
}
```

**base()**

base(options) in the AuctionDbContext constructor is equivalent to super(options) in Java. It calls the base class (DbContext) constructor and passes the options parameter to it.

`DbSet<Auction> Auctions { get; set; }` exposes the `Auction` entity set for querying and for adding/removing tracked entities. The relational provider's model and mapping configuration determine whether and how that entity is stored in tables; a `DbSet` property is not itself a table declaration.

## Dependency injection in ASP.NET Core / ASP.NET Core 依赖注入

Example partial code in program.cs

```csharp
var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddDbContext<AuctionDbContext>(options => {
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"));
});
builder.Services.AddAutoMapper(AppDomain.CurrentDomain.GetAssemblies());

var app = builder.Build();
```

### Services

Service registrations tell the container how to provide a service when a constructor requests it. `AddDbContext` registers the context as scoped by default; in a typical MVC request scope, the request's services share that scoped instance. A scope is also created explicitly for work outside a request, such as a startup seeding operation.

### Scope

`CreateScope()` creates a child lifetime boundary in which scoped services are created and then disposed with that scope. Do not resolve a scoped context from the root provider for long-lived use.

### Assemble automappers

```csharp
builder.Services.AddAutoMapper(AppDomain.CurrentDomain.GetAssemblies());
```

For AutoMapper 13 and later, this extension is in the core package; it scans the listed assemblies for profiles and registers the mapper services. Earlier versions used the separate DI package. Prefer a marker type or known assembly set when scanning the whole current AppDomain would include unrelated assemblies.

## Initialize DbContext

For a small local example, an initializer can apply migrations and seed data through a scoped context:

```csharp
using AuctionService.Data;
using AuctionService.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
namespace AuctionService.Data;
public class DbInitializer
{
    public static void InitDb(WebApplication app) {
        using var scope = app.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AuctionDbContext>();
        SeedData(context);
    }
    private static void SeedData(AuctionDbContext context)
    {
        context.Database.Migrate();
        if (context.Auctions.Any())
        {
            Console.WriteLine("Auction data already exists.");
            return;
        }
        var auctions = new List<Auction>()
        {
            // auctions
            new Auction
            {
               ...
            },
            ...
        };
        context.AddRange(auctions);
        context.SaveChanges();
    }
}
```

**Seed function**

The seed function is essentially initializing the database with some default data. context.Database.Migrate() ensures that the database schema is up-to-date, context.Auctions.Any() checks if there's already any data in the Auctions table, and context.AddRange(auctions) and context.SaveChanges() add new rows to the table and save those changes, respectively.

The scoped provider resolves the `DbContext`; `using var` disposes the scope at the end of the method, which in turn disposes scoped services. `GetRequiredService<T>()` fails immediately if the type was not registered. Applying migrations during startup is shown here as a simple development example; deployment docs describe reviewed scripts/bundles and the version/provider-specific tradeoffs for production.

## Related current note / 相关现行笔记

[Data Access and Connection Pools](../../engineering-foundations/backend/data-access-and-connection-pools.md) explains the shared context and connection lifetime model; this page keeps the versioned example. / 数据访问与连接池笔记说明通用 context 和连接生命周期；此页保留有版本边界的具体示例。

## Sources / 参考资料

- Microsoft Learn: [EF Core migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations) and [applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying); the latter describes review, scripts/bundles, and runtime migration tradeoffs.
- Microsoft Learn: [EF Core required and optional properties](https://learn.microsoft.com/en-us/ef/core/modeling/entity-properties), [ASP.NET Core controller injection](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection), [dependency-injection lifetimes](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection), [MVC validation of non-nullable parameters](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-7.0#non-nullable-reference-types-and-required-attribute), [.NET package CLI syntax](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies), [.NET 10 solution-file default](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default), [Web API template defaults](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates), and [Azure Data Studio retirement](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio).
- [AutoMapper dependency injection](https://docs.automapper.org/en/latest/Dependency-injection.html) documents that `AddAutoMapper` is in the core package starting with v13; the package list above preserves an older v12-era reference.
- [Npgsql connection-string parameters](https://www.npgsql.org/doc/connection-string-parameters), [MongoDB official image documentation](https://hub.docker.com/_/mongo), and the [official PostgreSQL image `PGDATA` and volume guidance](https://raw.githubusercontent.com/docker-library/docs/master/postgres/README.md#pgdata) for connection fields, data directories, initialization, and authentication details. The Compose sample is pinned to PostgreSQL 17's volume layout; PostgreSQL 18+ changes it.
- Microsoft Learn: [SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker) and [container security](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-security) for host support and the `MSSQL_SA_PASSWORD` variable.
- The `MongoDB.Entities` snippets are pinned to the course's `22.1.0` package reference; the project's [API docs](https://mongodb-entities.com/api/MongoDB.Entities.DB.html) and [index guide](https://mongodb-entities.com/wiki/Indexes.html) document the corresponding concepts. The [v22.1 `Find` source](https://github.com/dj-nitehawk/MongoDB.Entities/blob/aced47f36f152c6a0e13fe827f1a2bce310826dd/MongoDB.Entities/Builders/Find.cs) shows that sort definitions are appended and text-score sorting uses the same sort path; the text-query branch therefore selects score ordering without also appending `Make`. Current docs may describe a later package version.
