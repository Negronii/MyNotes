# How does the ASP.NET Core controller example map requests to stored data? / ASP.NET Core 控制器示例如何把请求映射到持久化数据？

The controller receives its context and mapper through constructor injection, queries related data asynchronously, returns HTTP results for missing resources, and maps domain results to response DTOs. `Task<ActionResult<T>>` combines async completion with typed or status responses; it is one pattern, not the only valid signature. / 控制器通过构造器注入取得 context 和 mapper，异步查询关联数据，为缺失资源返回 HTTP 结果，并把领域结果映射为响应 DTO。`Task<ActionResult<T>>` 组合异步完成与带类型或状态码的响应，但不是唯一有效签名。

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

## Sources / 参考资料

- Microsoft Learn: [EF Core migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations) and [applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying); the latter describes review, scripts/bundles, and runtime migration tradeoffs.
- Microsoft Learn: [EF Core required and optional properties](https://learn.microsoft.com/en-us/ef/core/modeling/entity-properties), [ASP.NET Core controller injection](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection), [dependency-injection lifetimes](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection), [MVC validation of non-nullable parameters](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-7.0#non-nullable-reference-types-and-required-attribute), [.NET package CLI syntax](https://learn.microsoft.com/en-us/dotnet/core/tools/dependencies), [.NET 10 solution-file default](https://learn.microsoft.com/en-us/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default), [Web API template defaults](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new-sdk-templates), and [Azure Data Studio retirement](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio).
- [AutoMapper dependency injection](https://docs.automapper.org/en/latest/Dependency-injection.html) documents that `AddAutoMapper` is in the core package starting with v13; the package list above preserves an older v12-era reference.
- [Npgsql connection-string parameters](https://www.npgsql.org/doc/connection-string-parameters), [MongoDB official image documentation](https://hub.docker.com/_/mongo), and the [official PostgreSQL image `PGDATA` and volume guidance](https://raw.githubusercontent.com/docker-library/docs/master/postgres/README.md#pgdata) for connection fields, data directories, initialization, and authentication details. The Compose sample is pinned to PostgreSQL 17's volume layout; PostgreSQL 18+ changes it.
- Microsoft Learn: [SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker) and [container security](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-security) for host support and the `MSSQL_SA_PASSWORD` variable.
- The `MongoDB.Entities` snippets are pinned to the course's `22.1.0` package reference; the project's [API docs](https://mongodb-entities.com/api/MongoDB.Entities.DB.html) and [index guide](https://mongodb-entities.com/wiki/Indexes.html) document the corresponding concepts. The [v22.1 `Find` source](https://github.com/dj-nitehawk/MongoDB.Entities/blob/aced47f36f152c6a0e13fe827f1a2bce310826dd/MongoDB.Entities/Builders/Find.cs) shows that sort definitions are appended and text-score sorting uses the same sort path; the text-query branch therefore selects score ordering without also appending `Make`. Current docs may describe a later package version.
