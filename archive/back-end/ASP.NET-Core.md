# ASP.NET Core and EF Core Reference / ASP.NET Core 与 EF Core 参考

This note preserves a course-style Web API example with EF Core, AutoMapper, MongoDB, PostgreSQL, and SQL Server. Examples mix older package versions (including ASP.NET Core 7 and AutoMapper 12) with stable concepts; use the linked versioned docs for the project you are building.

核心要点：EF Core 迁移根据代码模型和项目中的模型快照生成差异，不会先读取目标数据库来推断改动；`DbContext` 默认按 scope 注册，请求内共享该 scope。DTO/API contract、映射、数据库结构和连接凭据都要分别核对，课程包版本只代表课程环境。

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

## Controllers

Example code:

```csharp
using AuctionService.DTOs;
using AuctionService.Data;
using AuctionService.Entities;
using AutoMapper;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace AuctionService.Controllers;

[ApiController]
[Route("api/auctions")]
public class AuctionsController: ControllerBase
{
    private readonly AuctionDbContext _context;
    private readonly IMapper _mapper;

    public AuctionsController(AuctionDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    [HttpGet]
    public async Task<ActionResult<List<AuctionDto>>> GetAllAuctions()
    {
        var auctions = await _context.Auctions
            .Include(x => x.Item)
            .OrderBy(x => x.Item.Make)
            .ToListAsync();
        return _mapper.Map<List<AuctionDto>>(auctions);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<AuctionDto>> GetAuctionById(Guid id)
    {
        var auction = await _context.Auctions
            .Include(x => x.Item)
            .FirstOrDefaultAsync(x => x.Id == id);
        if (auction == null) return NotFound();
        return _mapper.Map<AuctionDto>(auction);
    }

    [HttpPost]
    public async Task<ActionResult<AuctionDto>> CreateAuction(CreateAuctionDto createAuctionDto)
    {
        var auction = _mapper.Map<Auction>(createAuctionDto);
        auction.Seller = "test";
        _context.Auctions.Add(auction);
        var result = await _context.SaveChangesAsync() > 0;
        if (!result) return BadRequest("Failed to create auction");
        return CreatedAtAction(nameof(GetAuctionById), new { id = auction.Id }, _mapper.Map<AuctionDto>(auction));
    }
}
```

### `Task` and asynchronous endpoints / `Task` 与异步端点

`Task<T>` represents an asynchronous operation that will eventually produce a `T`; it is not a JavaScript `Promise` contract and does not imply a dedicated thread. `await` lets an endpoint asynchronously wait for I/O, such as EF Core's database call. `ActionResult<T>` allows either a response value of type `T` or an HTTP result such as `NotFound()`.

### How `_context` and `_mapper` are resolved

The AuctionDbContext and IMapper instances are automatically injected into your controller's constructor by ASP.NET Core's Dependency Injection (DI) mechanism. This is because these types are registered in the DI container in the Program.cs.

### Return Type of Controller Endpoints

Returning `Task<ActionResult<T>>` is a common pattern for asynchronous endpoints in ASP.NET Core, but it's not a fixed or forced pattern. You can return other types as well. This particular return type gives you a lot of flexibility:

`Task` represents asynchronous completion; `ActionResult` allows different HTTP results; `T` describes the response value that can be serialized.

## Working with MongoDB in a .NET Environment

### 1. Package versions / 包版本

These package references record the versions used by this course example, not current-version recommendations. Match framework, provider, and library versions in the application you build:

```xml
<!-- Provides functionality to map object properties to each other -->
<PackageReference Include="AutoMapper.Extensions.Microsoft.DependencyInjection" Version="12.0.1" />

<!-- Enables the generation of OpenAPI/Swagger documentation -->
<PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="7.0.10" />

<!-- Provides a convenient API to interact with MongoDB -->
<PackageReference Include="MongoDB.Entities" Version="22.1.0" />
```

### 2. MongoDB with Docker Compose / 使用 Docker Compose 运行 MongoDB

Here's a Docker Compose file that sets up both PostgreSQL and MongoDB:

```yml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set a local PostgreSQL password}
      POSTGRES_DB: auctions
    ports:
      - 5432:5432
    volumes:
      - pgdata:/var/lib/postgresql/data
  mongodb:
    image: ${MONGO_IMAGE:?set a supported MongoDB image tag}
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:?set a local MongoDB password}
    ports:
      - 27017:27017
    volumes:
      - mongodata:/data/db

volumes:
  pgdata:
  mongodata:
```

**Steps to Use:**

- Keep the PostgreSQL image on major version 17 for this volume path, set `MONGO_IMAGE` to an explicit supported tag, and supply local-only password values outside the checked-in file.
- Start the services with `docker compose up -d` when intentionally setting up a local environment.
- This PostgreSQL 17 example mounts `/var/lib/postgresql/data`. PostgreSQL 18 and later use a version-specific `PGDATA` directory under `/var/lib/postgresql` and require the volume mount to target `/var/lib/postgresql`; adjust both image major and mount layout together.
- The official Mongo image stores its data at `/data/db`. Its initialization root account is created in the `admin` authentication database; a client connecting to another database must still authenticate against `admin`.

### 3. Setting Up Models and Database Initialization:

- Create a "Models" folder to define the data schemas.
- Create a `DbInitializer` to initialize the database from a prepared JSON file if the database is empty.

```csharp
using System.Text.Json;
using MongoDB.Driver;
using MongoDB.Entities;

namespace SearchService;

public class DbInitializer
{
    public static async Task InitDb(WebApplication app)
    {
        // Initialize the MongoDB database
        await DB.InitAsync("SearchDB", MongoClientSettings
            .FromConnectionString(app.Configuration.GetConnectionString("MongoDbConnection")));

        // Create indexes for the Item entity
        await DB.Index<Item>()
            .Key(x => x.Make, KeyType.Text)
            .Key(x => x.Model, KeyType.Text)
            .Key(x => x.Color , KeyType.Text)
            .CreateAsync();

        // Check if any data exists
        var count = await DB.CountAsync<Item>();
        if (count == 0)
        {
            Console.WriteLine("No data - will attempt to seed");
            var itemData = await File.ReadAllTextAsync("Data/ItemData.json");
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var items = JsonSerializer.Deserialize<List<Item>>(itemData, options)
                ?? throw new InvalidOperationException("Item seed data was empty or invalid.");
            await DB.SaveAsync(items);
        }
    }
}
```

To run the initializer, add the following in your `program.cs`:

```csharp
await DbInitializer.InitDb(app);
```

### 4. Setting Up Controllers:

Here's an example of a simple search controller:

```csharp
using Microsoft.AspNetCore.Mvc;
using MongoDB.Entities;

namespace SearchService;

[ApiController]
[Route("api/search")]
public class SearchController: ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<List<Item>>> SearchItems(string? searchTerm = null)
    {
        var query = DB.Find<Item>();

        // A text query is ranked by text score; otherwise sort by Make.
        if (!string.IsNullOrEmpty(searchTerm))
        {
            query.Match(Search.Full, searchTerm).SortByTextScore();
        }
        else
        {
            query.Sort(x => x.Ascending(a => a.Make));
        }

        var result = await query.ExecuteAsync();
        return result;
    }
}
```

**Explanation:** This controller contains an endpoint that allows for searching items. If a `searchTerm` is provided, it performs a full-text search on the MongoDB collection; otherwise, it simply fetches and sorts the data by the "Make" attribute.

# Appendix

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
