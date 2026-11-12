# 请求数据与持久化实体如何经由 DbContext 完成一次写入？

**案例：** 拍卖创建请求只允许调用方提交商品和起拍价。数据库实体还包含主键、卖家身份和审核状态；成功响应则只暴露资源 ID、商品摘要、起拍价和状态。Data Transfer Object（数据传输对象，DTO）定义跨 HTTP 边界的数据形状，entity（实体）描述持久化对象；DbContext（数据库上下文）负责跟踪本次写入涉及的实体和变更。三者有意不同，避免把数据库字段直接变成可写 API 字段。

## 请求和响应为什么使用不同 DTO？

~~~mermaid
flowchart TD
    Request[POST /api/auctions] --> Auth{认证并通过 Seller 策略？}
    Auth -->|否：401 / 403| AuthFail[请求结束；无写入]
    Auth -->|是| Bind{JSON 绑定与 DTO 验证通过？}
    Bind -->|否：400| InputFail[请求结束；无写入]
    Bind -->|是| Validated[已验证的 CreateAuctionDto]
~~~

第一图止于认证授权通过、JSON 已绑定且 DTO 验证通过。它输出的 `CreateAuctionDto` 会在本页后半段继续用于同一次 Northstar / S1 / blue / 100 创建请求；无效请求分别在认证/授权或模型验证阶段结束，不会进入写入流程。

请求 DTO 只声明这次操作允许写入的值；`SellerId`、`Status` 和主键由服务端负责。数据注解会在 ASP.NET Core 模型验证阶段运行；它们不会替代授权判断，也不会自动创建数据库约束。

~~~csharp
using System.ComponentModel.DataAnnotations;

public sealed class CreateAuctionDto
{
    [Required, StringLength(80)]
    public string Make { get; init; } = "";

    [Required, StringLength(80)]
    public string Model { get; init; } = "";

    [Required, StringLength(40)]
    public string Color { get; init; } = "";

    [Range(1, 2_000_000)]
    public int StartingBid { get; init; }
}

public sealed record AuctionDto
{
    public Guid Id { get; init; }
    public string Make { get; init; } = "";
    public string Model { get; init; } = "";
    public string Color { get; init; } = "";
    public int StartingBid { get; init; }
    public string Status { get; init; } = "";
}
~~~

`Auction` 与 `Item` 是持久化实体。它们可以保存数据库需要的主键、外键和导航属性；`Added`、`Modified` 等跟踪状态由 `DbContext` 持有，不是实体属性。这些持久化字段不必全部出现在 API 中。

~~~csharp
public sealed class Auction
{
    public Guid Id { get; set; }
    public int ItemId { get; set; }
    public string SellerId { get; set; } = "";
    public string Status { get; set; } = "draft";
    public int StartingBid { get; set; }
    public Item Item { get; set; } = new();
}

public sealed class Item
{
    public int Id { get; set; }
    public string Make { get; set; } = "";
    public string Model { get; set; } = "";
    public string Color { get; set; } = "";
}
~~~

## 映射怎样把 DTO 转成持久化实体？

映射把两个边界接起来。下面的 AutoMapper profile 让 `AuctionDto` 从 `Auction` 与其子对象 `Item` 组合字段，也让创建 DTO 映射出新的 `Auction` 和 `Item`。

~~~csharp
using AutoMapper;

public sealed class AuctionProfile : Profile
{
    public AuctionProfile()
    {
        CreateMap<Auction, AuctionDto>()
            .IncludeMembers(auction => auction.Item);
        CreateMap<Item, AuctionDto>(MemberList.None);

        CreateMap<CreateAuctionDto, Auction>()
            .ForMember(auction => auction.Item,
                options => options.MapFrom(input => input))
            .ForMember(auction => auction.Id, options => options.Ignore())
            .ForMember(auction => auction.ItemId, options => options.Ignore())
            .ForMember(auction => auction.SellerId, options => options.Ignore())
            .ForMember(auction => auction.Status, options => options.Ignore());
        CreateMap<CreateAuctionDto, Item>(MemberList.None)
            .ForMember(item => item.Id, options => options.Ignore());
    }
}
~~~

`IncludeMembers` 会复用显式声明的 `Item -> AuctionDto` 部分映射；它不是把实体所有字段自动公开。`AuctionDto` 用可写入的 `init` 属性，AutoMapper 会在父映射构造记录后，把拍卖字段与 `Item` 字段合并进去。把目标改成位置参数 record 后，这组父子映射的构造器参数无法全部匹配，`AssertConfigurationIsValid()` 会失败；要保留位置参数就显式配置构造参数映射。调用 `Map<AuctionDto>(auction)` 明确指定目标类型，因此同一源类型可以有多个目标映射。集合映射也可复用已配置的元素映射。

> [!example] 一次创建请求怎样变成响应？
> 请求 DTO 为 `{ Make = "Northstar", Model = "S1", Color = "blue", StartingBid = 100 }`。映射产生 `Auction.Item = Item("Northstar", "S1", "blue")`，起拍价为 100；控制器另从卖家身份填入 `SellerId`，`Status` 保持服务端默认值 `draft`。隔离映射时固定 ID 为 `00000000-0000-0000-0000-000000000001`，init 属性记录的响应字段是 `Id = 00000000-0000-0000-0000-000000000001`、`Make = "Northstar"`、`Model = "S1"`、`Color = "blue"`、`StartingBid = 100`、`Status = "draft"`。

这两段内存映射和 `AssertConfigurationIsValid()` 已用 .NET SDK 10.0.404、AutoMapper 16.3.0 实际运行；本页后面的 SQLite fixture 进一步验证完整 HTTP 写入。没有测试 Npgsql provider 或迁移。复杂映射应检查配置并验证结果，不能把自动映射当成 API 契约审查。

## DbContext 怎样保持在一次请求或工作单元内？

`DbContext` 构造器把数据库 provider（提供程序）的选项交给基类；`DbSet<Auction>` 提供查询和跟踪入口，不是单独的“建表声明”。EF Core 模型配置决定它映射到哪些关系表。

~~~csharp
using Microsoft.EntityFrameworkCore;

public sealed class AuctionDbContext : DbContext
{
    public AuctionDbContext(DbContextOptions<AuctionDbContext> options)
        : base(options) { }

    public DbSet<Auction> Auctions => Set<Auction>();
    public DbSet<Item> Items => Set<Item>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Auction>()
            .HasOne(auction => auction.Item)
            .WithOne()
            .HasForeignKey<Auction>(auction => auction.ItemId);
    }
}
~~~

ASP.NET Core 与 EF Core 的配置都属于 dependency injection（依赖注入）容器。将 `DbContext` 注册为 scoped（作用域）后，同一请求作用域中的服务可取得同一个上下文实例：

~~~csharp
var connectionString =
    builder.Configuration.GetConnectionString("DefaultConnection")
    ?? throw new InvalidOperationException("Missing DefaultConnection.");

builder.Services.AddControllers();
builder.Services.AddDbContext<AuctionDbContext>(options =>
    options.UseNpgsql(connectionString));
var mapperLicenseKey = builder.Configuration["AutoMapper:LicenseKey"];
builder.Services.AddAutoMapper(
    options =>
    {
        if (!string.IsNullOrWhiteSpace(mapperLicenseKey))
            options.LicenseKey = mapperLicenseKey;
    },
    typeof(AuctionProfile));
~~~

下面的端点假设应用已注册可信认证方案和 `Seller` 授权策略。`AddDbContext` 把上下文注册为 scoped（作用域）服务；每个 HTTP 请求由 ASP.NET Core 激活控制器并注入本请求的上下文。认证中间件建立 `User`，策略要求卖家角色与 subject（主体）claim。启动时还要把控制器路由接入请求管线：

~~~csharp
var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.Run();
~~~

下图承接同一次 POST：把已验证的 DTO 与可信身份转换成 Auction/Item 关联实体，等待工作单元保存成功后才映射公开响应；写入异常直接交给错误处理中间件。

~~~mermaid
flowchart TD
    Input[已验证 CreateAuctionDto + 可信身份] --> Map[映射成 Auction + Item]
    Map --> Owner[从 NameIdentifier 设置 SellerId]
    Owner --> Add[DbContext.Add；两对象均为 Added]
    Add --> Save[await SaveChangesAsync]
    Save -->|成功：提交关联实体并生成 Item.Id| ResponseMap[从已保存对象映射公开字段]
    ResponseMap --> Success[201 Created + Location + JSON]
    Save -->|异常| SaveFail[错误处理中间件；无成功响应]
~~~

创建 action 先映射经过绑定与验证的请求，再从可信 `NameIdentifier` 设置 `SellerId`。对 Auction 和它关联的新 Item 调用一次 `Add` 会把两者都标成 Added；EF Core 保存整个关联图。等待 `SaveChangesAsync` 成功后，数据库生成的 `Item.Id` 才作为 `Auction.ItemId` 固定，随后才构造成功响应：

~~~csharp
using System.Security.Claims;
using AutoMapper;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Authorize(Policy = "Seller")]
[Route("api/auctions")]
public sealed class AuctionsController(
    AuctionDbContext context,
    IMapper mapper) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<AuctionDto>> Create(
        CreateAuctionDto input,
        CancellationToken cancellationToken)
    {
        var auction = mapper.Map<Auction>(input);
        auction.SellerId =
            User.FindFirstValue(ClaimTypes.NameIdentifier)
            ?? throw new InvalidOperationException(
                "Authenticated seller has no subject claim.");

        context.Auctions.Add(auction);
        await context.SaveChangesAsync(cancellationToken);

        var response = mapper.Map<AuctionDto>(auction);
        return Created($"/api/auctions/{auction.Id}", response);
    }
}
~~~

这条 `Location` URI 指向 `GET /api/auctions/{id}`；同路由、卖家归属检查与 200/404 读取由[ASP.NET Core 控制器示例](aspnet-core-controller-example.md)中的按 ID GET action 实现。若只摘录本页 POST，也要在同一个 URI 注册实际 GET，才能用该地址取回资源。

隔离 SQLite HTTP fixture 用输入 `{"make":"Northstar","model":"S1","color":"blue","startingBid":100}` 和合成卖家 `seller-a` 实际运行了这条路径。写入后 `Auction.ItemId` 与生成的 `Item.Id` 都是 `1`，卖家和状态分别为 `seller-a`、`draft`。201 响应只返回 `AuctionDto` 的公开字段，不包含 `SellerId` 或 `ItemId`：

~~~http
HTTP/1.1 201 Created
Location: /api/auctions/e1bf916e-1404-4d08-888a-44177ac98b27
Content-Type: application/json

{
  "id": "e1bf916e-1404-4d08-888a-44177ac98b27",
  "make": "Northstar",
  "model": "S1",
  "color": "blue",
  "startingBid": 100,
  "status": "draft"
}
~~~

若请求没有经过认证或不满足 `Seller` 策略，认证/授权中间件在 action 前返回 401 或 403；起拍价 0 会在 `[ApiController]` 模型验证阶段返回 400，也不会进入 `Add`。约束错误发生在数据库事务中时，支持事务的 provider 会回滚本次 `SaveChangesAsync` 中的整组改动。fixture 的 SQLite 触发器拒绝起拍价 200，实际得到 500、没有 `Location`，数据库中也没有留下该请求的 Auction 或 Item。

提交事务期间若连接断开，客户端可能无法知道提交是否完成；没有收到 `201` 不足以证明没有写入。应按应用幂等契约查证结果或恢复，不要盲目重放请求，见[HTTP 错误契约中的未知写入结果](../../engineering-foundations/backend/http-api-contracts.md#错误契约怎样保留机器可判定的含义)。无论错误发生在哪个提交阶段，当前 action 不会继续构造成功响应；合成测试认证和错误处理中间件仅用于隔离验证，不是生产认证配置。

上下文保存本次工作单元的实体跟踪与变更状态；它不是可跨请求共享的缓存，也不应被并发线程同时访问。EF Core 默认在每次数据库操作前打开、完成后关闭连接；Npgsql 默认开启连接池，关闭连接通常归还池中，因此 scoped DbContext 不会一直占住一个连接。显式保持连接打开或较长事务才会跨操作延长占槽时间，区别见[怎样限定对象关系映射会话并排查连接池耗尽？](../../engineering-foundations/backend/data-access-and-connection-pools.md)。AutoMapper 15 起 `AddAutoMapper` 要求配置回调；16.3.0 的许可密钥可从配置或环境变量提供，未设置密钥时会记录警告，但不改变映射运行行为。不要把密钥写入源码。

`AddDbContext` 默认按请求作用域注册上下文。后台 worker 的一次 attempt 应创建自己的 scope 或上下文工厂实例，不要把 Web 请求的上下文留作单例。启动任务也要显式创建并释放 scope；下面只展示本地开发中的迁移和一次性种子数据。它必须放在 `builder.Build()` 之后、`app.Run()` 之前；`Run` 开始接受请求并阻塞当前流程，不能把初始化代码接在它后面：

~~~csharp
await using (var scope = app.Services.CreateAsyncScope())
{
    var context = scope.ServiceProvider.GetRequiredService<AuctionDbContext>();
    await context.Database.MigrateAsync();

    if (!await context.Auctions.AnyAsync())
    {
        context.Auctions.Add(new Auction
        {
            SellerId = "local-demo",
            StartingBid = 100,
            Item = new Item { Make = "Northstar", Model = "S1", Color = "blue" }
        });
        await context.SaveChangesAsync();
    }
}
~~~

`CreateAsyncScope` 释放该作用域中的异步可释放服务，`GetRequiredService<T>()` 在类型未注册时立即失败。这个“先查空再插入”的单进程本地示例不处理多副本同时启动的竞态；部署时由一次性初始化任务负责迁移和种子数据，避免每个实例并发执行同一初始化逻辑。EF Core 的迁移文件如何形成和部署，见下一篇[EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？](aspnet-ef-model-and-migrations.md)。

> [!info]- 来源
> - ASP.NET Core 10.0 控制器注入与服务生命周期：[控制器依赖注入](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection?view=aspnetcore-10.0)、[依赖注入生命周期](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection?view=aspnetcore-10.0)，核对日期 2026-11-06。
> - `AddDbContext` 默认 scoped，`DbContext` 不能并发访问：[EF Core DbContext 生命周期、配置与初始化](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/)，核对日期 2026-11-06。
> - AutoMapper 16.3.0 当前稳定包、`AddAutoMapper` 许可配置、`IncludeMembers` 与目标构造：[NuGet 包页](https://www.nuget.org/packages/AutoMapper/16.3.0)、[许可配置](https://docs.automapper.io/en/stable/License-configuration.html)、[依赖注入](https://docs.automapper.io/en/stable/Dependency-injection.html)、[扁平化与 `IncludeMembers`](https://docs.automapper.io/en/stable/Flattening.html)、[构造器映射](https://docs.automapper.io/en/stable/Construction.html)、[16.3.0 安全修复发布说明](https://github.com/LuckyPennySoftware/AutoMapper/releases/tag/v16.3.0)，核对日期 2026-11-06。v13 起 `AddAutoMapper` 已包含在核心包；v15 起注册重载需要配置回调。
> - EF Core 在请求作用域中注入上下文、跟踪并保存实体、保存关联实体与单次 `SaveChanges` 事务：[DbContext 生命周期](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/)、[保存相关数据](https://learn.microsoft.com/en-us/ef/core/saving/related-data)、[事务](https://learn.microsoft.com/en-us/ef/core/saving/transactions)，核对日期 2026-11-13。
> - ASP.NET Core 10.0 模型绑定与验证发生在 action 前，`[ApiController]` 对无效 ModelState 默认返回 400：[模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)；身份认证与授权中间件在 `MapControllers` 前运行：[ASP.NET Core middleware](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/?view=aspnetcore-10.0)，核对日期 2026-11-13。
> - EF Core 操作级开关连接与连接池职责边界：[EF Core 高级性能主题](https://learn.microsoft.com/en-us/ef/core/performance/advanced-performance-topics)；Npgsql 默认连接池开启：[Npgsql 连接参数](https://www.npgsql.org/doc/connection-string-parameters.html#pooling)，核对日期 2026-11-13。
> - EF Core connection resiliency 文档 § Transaction commit failure and the idempotency issue：提交阶段断连可能导致结果未知，需验证提交结果或采用幂等恢复：[连接恢复](https://learn.microsoft.com/en-us/ef/core/miscellaneous/connection-resiliency#transaction-commit-failure-and-the-idempotency-issue)，核对日期 2026-11-13。
