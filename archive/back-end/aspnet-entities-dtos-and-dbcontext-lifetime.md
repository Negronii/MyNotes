# 请求数据与持久化实体如何经由 DbContext 完成一次写入？

**案例：** 拍卖创建请求只允许调用方提交商品和起拍价。数据库实体还包含主键、卖家身份和审核状态；成功响应则只暴露资源 ID、商品摘要、起拍价和状态。Data Transfer Object（数据传输对象，DTO）定义跨 HTTP 边界的数据形状，entity（实体）描述持久化对象；DbContext（数据库上下文）负责跟踪本次写入涉及的实体和变更。三者有意不同，避免把数据库字段直接变成可写 API 字段。

## 请求和响应为什么使用不同 DTO？

~~~mermaid
flowchart LR
    Json[JSON 请求：品牌 / 型号 / 颜色 / 起拍价] --> RequestDto[CreateAuctionDto]
    RequestDto -->|验证与映射| Entity[Auction + Item 实体]
    Entity --> Context[请求作用域内的 DbContext]
    Context -->|保存成功| Database[(关系数据库)]
    Entity -->|选择输出字段| ResponseDto[AuctionDto]
    ResponseDto --> JsonOut[JSON 响应]
~~~

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

`Auction` 与 `Item` 是持久化实体。它们可以拥有数据库需要的关联和跟踪状态；这些字段不必全部出现在 API 中。

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
> 请求 DTO 为 `{ Make = "Northstar", Model = "S1", Color = "blue", StartingBid = 100 }`。映射产生 `Auction.Item = Item("Northstar", "S1", "blue")`，起拍价为 100；控制器另从卖家身份填入 `SellerId`，`Status` 保持服务端默认值 `draft`。隔离映射时固定 ID 为 `00000000-0000-0000-0000-000000000001`，响应记录为 `AuctionDto(Id, "Northstar", "S1", "blue", 100, "draft")`。

这两段内存映射和 `AssertConfigurationIsValid()` 已用 .NET SDK 10.0.403、AutoMapper 16.3.0 实际运行；未执行 EF Core 或数据库。复杂映射应检查配置并验证结果，不能把自动映射当成 API 契约审查。

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

上下文保存本次工作单元的实体跟踪与变更状态；它不是可跨请求共享的缓存，也不应被并发线程同时访问。Npgsql 通常在单个数据库操作前借出连接、操作结束后归还连接池；显式保持连接打开或较长事务会跨操作延长占槽时间，区别见[怎样限定对象关系映射会话并排查连接池耗尽？](../../engineering-foundations/backend/data-access-and-connection-pools.md)。AutoMapper 15 起 `AddAutoMapper` 要求配置回调；16.3.0 的许可密钥可从配置或环境变量提供，未设置密钥时会记录警告，但不改变映射运行行为。不要把密钥写入源码。

`AddDbContext` 默认按请求作用域注册上下文。后台 worker 的一次 attempt 应创建自己的 scope 或上下文工厂实例，不要把 Web 请求的上下文留作单例。启动任务也要显式创建并释放 scope；下面只展示本地开发中的迁移和一次性种子数据：

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
> - ASP.NET Core 自动模型验证：Microsoft Learn [模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
