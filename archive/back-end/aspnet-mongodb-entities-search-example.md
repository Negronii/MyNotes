# How does the MongoDB.Entities example prepare and search documents? / MongoDB.Entities 示例如何准备并搜索文档？

This sample pins `MongoDB.Entities` to 22.1.0 and uses its text index/search builder. A non-empty search term selects text-score sorting; an empty term sorts by `Make`. Package and Docker versions are part of the example, not current defaults. / 此示例将 `MongoDB.Entities` 固定为 22.1.0，并使用其文本索引与搜索构造器。搜索词非空时按文本得分排序；为空时按 `Make` 排序。包与 Docker 版本属于示例上下文，不是当前默认值。

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

## Sources / 参考资料

- Microsoft Learn: [EF Core migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations) and [applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying); the latter describes review, scripts/bundles, and runtime migration tradeoffs.
- Microsoft Learn: [EF Core required and optional properties](https://learn.microsoft.com/en-us/ef/core/modeling/entity-properties), [ASP.NET Core controller injection](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection), [dependency-injection lifetimes](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection), [MVC validation of non-nullable parameters](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-7.0#non-nullable-reference-types-and-required-attribute), [.NET package CLI syntax](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies), [.NET 10 solution-file default](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default), [Web API template defaults](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates), and [Azure Data Studio retirement](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio).
- [AutoMapper dependency injection](https://docs.automapper.org/en/latest/Dependency-injection.html) documents that `AddAutoMapper` is in the core package starting with v13; the package list above preserves an older v12-era reference.
- [Npgsql connection-string parameters](https://www.npgsql.org/doc/connection-string-parameters), [MongoDB official image documentation](https://hub.docker.com/_/mongo), and the [official PostgreSQL image `PGDATA` and volume guidance](https://raw.githubusercontent.com/docker-library/docs/master/postgres/README.md#pgdata) for connection fields, data directories, initialization, and authentication details. The Compose sample is pinned to PostgreSQL 17's volume layout; PostgreSQL 18+ changes it.
- Microsoft Learn: [SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker) and [container security](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-security) for host support and the `MSSQL_SA_PASSWORD` variable.
- The `MongoDB.Entities` snippets are pinned to the course's `22.1.0` package reference; the project's [API docs](https://mongodb-entities.com/api/MongoDB.Entities.DB.html) and [index guide](https://mongodb-entities.com/wiki/Indexes.html) document the corresponding concepts. The [v22.1 `Find` source](https://github.com/dj-nitehawk/MongoDB.Entities/blob/aced47f36f152c6a0e13fe827f1a2bce310826dd/MongoDB.Entities/Builders/Find.cs) shows that sort definitions are appended and text-score sorting uses the same sort path; the text-query branch therefore selects score ordering without also appending `Make`. Current docs may describe a later package version.
