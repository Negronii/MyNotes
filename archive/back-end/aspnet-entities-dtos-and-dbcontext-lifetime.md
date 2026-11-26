# 请求数据与持久化实体如何经由 DbContext 完成一次写入？

**案例：** 拍卖创建请求只允许调用方提交商品和起拍价。数据库实体还包含主键、卖家身份和审核状态；成功响应则只暴露资源 ID、商品摘要、起拍价和状态。Data Transfer Object（数据传输对象，DTO）定义跨 HTTP 边界的数据形状，entity（实体）描述持久化对象；DbContext（数据库上下文）负责跟踪本次写入涉及的实体和变更。三者的形状有意不同，避免数据库字段直接变成调用方可写的 API 字段。本页始终跟踪同一个创建请求：商品为 Northstar 品牌的 S1 型号、颜色 blue、起拍价 100。

## 请求和响应为什么使用不同 DTO？

~~~mermaid
flowchart TD
    Request[POST /api/auctions] --> Auth{认证并通过 Seller 策略？}
    Auth -->|否：401 / 403| AuthFail[请求结束；无写入]
    Auth -->|是| Bind{JSON 绑定与 DTO 验证通过？}
    Bind -->|否：400| InputFail[请求结束；无写入]
    Bind -->|是| Validated[已验证的 CreateAuctionDto]
~~~

上图只画到写入之前：请求通过认证和授权，JSON 绑定成 DTO 并通过验证。它的输出是一个已验证的 `CreateAuctionDto`，本页后半段接着用它完成写入；认证、授权或模型验证失败的请求在对应阶段直接结束，不会进入写入流程。

请求 DTO 只声明这次操作允许调用方提交的值；`SellerId`、`Status` 和主键都由服务端填写。DTO 上的数据注解（如 `[Required]`、`[Range]`）在 ASP.NET Core 模型验证阶段检查；它们不能代替授权判断，也不会自动变成数据库约束。

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

`Auction` 与 `Item` 是持久化实体，包含数据库需要的主键、外键和导航属性，这些字段不必全部出现在 API 中。实体是新增还是已修改（`Added`、`Modified` 等跟踪状态）由 `DbContext` 记录，不是实体自身的属性。

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

DTO 和实体形状不同，就需要映射在两者之间转换。下面的 AutoMapper profile（映射配置类）配置了两个方向：响应方向从 `Auction` 及其子对象 `Item` 组合出 `AuctionDto`；写入方向把 `CreateAuctionDto` 拆成新的 `Auction` 和 `Item`，并忽略应由服务端填写的字段。

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

`IncludeMembers` 复用显式声明的 `Item -> AuctionDto` 映射，把 `Item` 的同名字段填进响应；它不会把实体的所有字段自动公开。`AuctionDto` 使用 `init` 属性，AutoMapper 先构造记录，再把拍卖字段和 `Item` 字段分别写入。如果把 `AuctionDto` 改成位置参数 record（`record AuctionDto(Guid Id, ...)`），这组父子映射无法匹配全部构造器参数，`AssertConfigurationIsValid()` 会报错；想保留位置参数，就要显式配置构造参数映射。调用 `Map<AuctionDto>(auction)` 时显式指定了目标类型，所以同一个源类型可以配置多个目标映射；映射集合时也会复用已配置的元素映射。

> [!example] 一次创建请求怎样变成响应？
> 请求 DTO 为 `{ Make = "Northstar", Model = "S1", Color = "blue", StartingBid = 100 }`。映射产生 `Auction.Item = Item("Northstar", "S1", "blue")`，起拍价为 100；控制器再从卖家身份填入 `SellerId`，`Status` 保持服务端默认值 `draft`。单独测试映射时，把 `Auction.Id` 手动设为 `00000000-0000-0000-0000-000000000001`，再映射回 `AuctionDto`，得到的响应字段是 `Id = 00000000-0000-0000-0000-000000000001`、`Make = "Northstar"`、`Model = "S1"`、`Color = "blue"`、`StartingBid = 100`、`Status = "draft"`。

上面两个方向的内存映射和 `AssertConfigurationIsValid()` 已用 .NET SDK 10.0.404、AutoMapper 16.3.0 实际运行；本页后面的 SQLite 测试夹具（fixture）又验证了完整的 HTTP 写入，但没有测试 Npgsql provider 或迁移。AutoMapper 17.0.0 已于 2026-11-12 发布，本例未在该版本上验证。映射越复杂，越要检查配置并验证结果；自动映射不能代替对 API 契约的审查。

## DbContext 怎样保持在一次请求或工作单元内？

实体映射好之后，要由 `DbContext` 跟踪并保存。下面的构造器把数据库 provider（提供程序）的配置选项交给基类；`DbSet<Auction>` 是查询和跟踪 `Auction` 的入口，并不是一条“建表声明”，实体映射到哪些表由 EF Core 的模型配置决定。

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

ASP.NET Core 通过 dependency injection（依赖注入，DI）容器创建控制器及其依赖，`DbContext` 和 AutoMapper 也注册在这个容器里。`AddDbContext` 默认把上下文注册为 scoped（作用域）服务：每个 HTTP 请求有自己的作用域，同一请求中的服务拿到同一个上下文实例，不同请求互不共享：

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

下面的端点假设应用已注册可信的认证方案和 `Seller` 授权策略：认证中间件根据凭据建立 `User`，`Seller` 策略要求卖家角色和 subject（主体）claim。每个请求到来时，ASP.NET Core 创建控制器并注入本请求的上下文。启动时还要把认证、授权中间件和控制器路由接入请求管线：

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

创建 action 先映射已绑定并验证的请求，再从可信的 `NameIdentifier` claim 设置 `SellerId`。对 `Auction` 调用一次 `Add`，它和关联的新 `Item` 都会被标为 `Added`，EF Core 一并保存这组关联对象。`SaveChangesAsync` 成功后，数据库生成的 `Item.Id` 才写入 `Auction.ItemId`，之后才构造成功响应：

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

响应头中的 `Location` 指向 `GET /api/auctions/{id}`。这个按 ID 读取的 action（包括卖家归属检查和 200/404 结果）在[ASP.NET Core 控制器示例](aspnet-core-controller-example.md)中实现；如果只摘录本页的 POST，也要在同一 URI 上注册对应的 GET，客户端才能用这个地址取回资源。

一个隔离的 SQLite HTTP 测试夹具用输入 `{"make":"Northstar","model":"S1","color":"blue","startingBid":100}` 和合成卖家 `seller-a` 实际运行了这条路径。写入后 `Auction.ItemId` 与生成的 `Item.Id` 都是 `1`，卖家和状态分别为 `seller-a`、`draft`。201 响应只返回 `AuctionDto` 的公开字段，不包含 `SellerId` 或 `ItemId`：

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

若请求没有经过认证或不满足 `Seller` 策略，认证/授权中间件在 action 前返回 401 或 403；起拍价 0 会在 `[ApiController]` 模型验证阶段返回 400，也不会进入 `Add`。如果数据库在保存时拒绝写入（例如违反约束），支持事务的 provider 会回滚本次 `SaveChangesAsync` 中的全部改动。测试夹具用 SQLite 触发器拒绝起拍价 200 来模拟这种情况：实际得到 500、没有 `Location`，数据库中也没有留下该请求的 Auction 或 Item。

提交事务期间若连接断开，客户端可能无法知道提交是否完成；没有收到 `201` 不足以证明没有写入。应按应用幂等契约查证结果或恢复，不要盲目重放请求，见[HTTP 错误契约中的未知写入结果](../../engineering-foundations/services/api-contracts-errors-and-evolution.md)。无论错误发生在哪个提交阶段，当前 action 不会继续构造成功响应；合成测试认证和错误处理中间件仅用于隔离验证，不是生产认证配置。

上下文保存的是本次工作单元的实体跟踪和变更状态；它不是可跨请求共享的缓存，也不能被多个线程并发使用。EF Core 默认在每次数据库操作前打开连接、完成后关闭；Npgsql 默认启用连接池，“关闭”通常只是把连接还回池中，所以 scoped DbContext 不会在整个请求期间一直占着一个连接。只有显式保持连接打开或开启较长的事务，才会跨多次操作占用连接，区别见[怎样限定对象关系映射会话并排查连接池耗尽？](../../engineering-foundations/data/orm-sessions-and-connection-pools.md)。注册代码中的许可密钥来自 AutoMapper 15 起的商业许可模式：从 15 版开始，`AddAutoMapper` 必须传入配置回调；16.3.0 的许可密钥可以从配置或环境变量提供，未设置时只记录警告，不改变映射行为。不要把密钥写进源码。

请求之外没有现成的作用域。后台任务每次执行都应创建自己的 scope，或用上下文工厂创建实例，不要把某个 Web 请求的上下文保存下来长期使用。启动时的初始化同样要显式创建并释放 scope；下面只演示本地开发中的迁移和一次性种子数据。这段代码必须放在 `builder.Build()` 之后、`app.Run()` 之前，因为 `Run` 会开始接受请求并阻塞当前流程，写在它后面的代码不会按预期执行：

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

`await using` 结束时，`CreateAsyncScope` 创建的作用域会释放其中的异步可释放服务；`GetRequiredService<T>()` 在类型未注册时立即抛错。这个“先查空再插入”的写法只适合单进程本地示例，不处理多个副本同时启动的竞态；部署时应由一次性的初始化任务负责迁移和种子数据，避免每个实例并发执行同一段初始化逻辑。EF Core 的迁移文件如何形成和部署，见下一篇[EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？](aspnet-ef-model-and-migrations.md)。

> [!info]- 来源
> - ASP.NET Core 10.0 控制器注入与服务生命周期：[控制器依赖注入](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection?view=aspnetcore-10.0)、[依赖注入生命周期](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection?view=aspnetcore-10.0)，核对日期 2026-11-06。
> - `AddDbContext` 默认 scoped，`DbContext` 不能并发访问：[EF Core DbContext 生命周期、配置与初始化](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/)，核对日期 2026-11-06。
> - AutoMapper 16.3.0 稳定包（2026-11-12 起最新稳定版为 [17.0.0](https://www.nuget.org/packages/AutoMapper/17.0.0)，本例未验证，2026-11-16 核对）、`AddAutoMapper` 许可配置、`IncludeMembers` 与目标构造：[NuGet 包页](https://www.nuget.org/packages/AutoMapper/16.3.0)、[许可配置](https://docs.automapper.io/en/stable/License-configuration.html)、[依赖注入](https://docs.automapper.io/en/stable/Dependency-injection.html)、[扁平化与 `IncludeMembers`](https://docs.automapper.io/en/stable/Flattening.html)、[构造器映射](https://docs.automapper.io/en/stable/Construction.html)、[16.3.0 安全修复发布说明](https://github.com/LuckyPennySoftware/AutoMapper/releases/tag/v16.3.0)，核对日期 2026-11-06。v13 起 `AddAutoMapper` 已包含在核心包；v15 起注册重载需要配置回调。
> - EF Core 在请求作用域中注入上下文、跟踪并保存实体、保存关联实体与单次 `SaveChanges` 事务：[DbContext 生命周期](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/)、[保存相关数据](https://learn.microsoft.com/en-us/ef/core/saving/related-data)、[事务](https://learn.microsoft.com/en-us/ef/core/saving/transactions)，核对日期 2026-11-13。
> - ASP.NET Core 10.0 模型绑定与验证发生在 action 前，`[ApiController]` 对无效 ModelState 默认返回 400：[模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)；身份认证与授权中间件在 `MapControllers` 前运行：[ASP.NET Core middleware](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/?view=aspnetcore-10.0)，核对日期 2026-11-13。
> - EF Core 操作级开关连接与连接池职责边界：[EF Core 高级性能主题](https://learn.microsoft.com/en-us/ef/core/performance/advanced-performance-topics)；Npgsql 默认连接池开启：[Npgsql 连接参数](https://www.npgsql.org/doc/connection-string-parameters.html#pooling)，核对日期 2026-11-13。
> - EF Core connection resiliency 文档 § Transaction commit failure and the idempotency issue：提交阶段断连可能导致结果未知，需验证提交结果或采用幂等恢复：[连接恢复](https://learn.microsoft.com/en-us/ef/core/miscellaneous/connection-resiliency#transaction-commit-failure-and-the-idempotency-issue)，核对日期 2026-11-13。
