# EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？

**案例：** `Auction` 引用一件 `Item`。C# 模型规定哪些值必需、哪些可以缺失；Entity Framework Core（EF Core，对象关系映射框架）把模型按约定和配置映射到关系数据库。添加商品描述时，迁移文件记录从旧模型到新模型的 schema（数据库结构）变化；它不是扫描在线数据库后猜出开发者意图。

## EF Core 按什么规则建立关系模型？

~~~mermaid
flowchart TD
    Code[C# 实体 + Fluent 配置] --> Model[EF Core 模型]
    Model --> Compare[与受版本控制的旧模型快照比较]
    Compare --> Migration[生成迁移代码]
    Migration --> Review[审查列 / 约束 / 数据风险]
    Review --> Apply[本地更新、脚本或迁移包]
    Apply --> Schema[(关系数据库 schema)]
    Apply --> History[迁移历史表记录已应用版本]
~~~

主键按约定可由 `Id` 或 `<类型名>Id` 识别，`Id` 不需要额外的 `[Key]`。下例显式配置一条拍卖到商品的一对一关系：

~~~csharp
using Microsoft.EntityFrameworkCore;

public sealed class Item
{
    public int Id { get; set; }
    public string Make { get; set; } = "";
    public string Model { get; set; } = "";
    public string Color { get; set; } = "";
    public string? Description { get; set; }
}

public sealed class Auction
{
    public Guid Id { get; set; }
    public int ItemId { get; set; }
    public Item Item { get; set; } = null!;
    public string SellerId { get; set; } = "";
    public string Status { get; set; } = "draft";
    public int StartingBid { get; set; }
}

public sealed class AuctionDbContext(
    DbContextOptions<AuctionDbContext> options) : DbContext(options)
{
    public DbSet<Auction> Auctions => Set<Auction>();
    public DbSet<Item> Items => Set<Item>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Auction>()
            .HasOne(auction => auction.Item)
            .WithOne()
            .HasForeignKey<Auction>(auction => auction.ItemId);

        modelBuilder.Entity<Auction>()
            .ToTable(table => table.HasCheckConstraint(
                "CK_Auctions_StartingBid_Positive", "\"StartingBid\" > 0"));
    }
}
~~~

## 哪一层决定字段必需和数据约束？

启用了 C# nullable reference types（可空引用类型）时，`string` 按约定为必需属性，`string?` 为可选属性；EF Core 映射到关系数据库时通常分别生成非空列和可空列。`[Required]` 可以把 EF 模型属性配置为必需，但不会把 C# 的 `string?` 声明改成 `string`。请求 DTO 上的验证属性、EF 模型和数据库列约束是不同层，修改其中一层并不会自动保证其他层同步。已有项目启用 nullable reference types 前要审查模型差异，因为迁移可能把原可空列改为非空。本例的 PostgreSQL 检查约束在数据库写入处限制起拍价为正数；请求验证可更早反馈，但不是共享不变量的唯一守卫。

## 迁移文件怎样表达模型变化？

迁移（migration）由 EF 工具比较当前模型与上一次受版本控制的 model snapshot（模型快照）生成；数据库当前 schema 不是 scaffold 迁移的对照来源。重命名字段时，生成器可能把“改名”猜成删列再加列，执行前必须审查迁移和 SQL，确认旧数据如何保留。迁移应用成功后，EF 在迁移历史表记录已应用的 ID。此处 `Auction` 与 `Item` 延续上一章的字段和一对一关联；必需外键 `ItemId` 对应 `Item` 导航，EF 装载关联时填入该导航。`null!` 只消除由 EF 负责赋值的必需导航的编译器警告；应用创建实体时仍要提供 `new Item()`。

## 本地和生产环境如何应用迁移？

下例使用 .NET 10 与 EF Core 10 的 CLI 名称。项目模板默认创建 Minimal API（最小 API）；要沿用本组控制器示例，明确选择控制器模板。代码块展示改动后的模型：`Color` 与 `Status` 延续上一章，`Description` 和起拍价数据库检查约束是本次新增。运行 EF 命令前，须把这些实体和 `AuctionDbContext` 放入项目，并在应用启动时注册 Npgsql provider 与连接串：

~~~csharp
var connectionString =
    builder.Configuration.GetConnectionString("DefaultConnection")
    ?? throw new InvalidOperationException("Missing DefaultConnection.");

builder.Services.AddDbContext<AuctionDbContext>(options =>
    options.UseNpgsql(connectionString));
~~~

连接串从 User Secrets 或环境变量读取；`dotnet ef database update` 执行时 PostgreSQL 必须可连接。要重放增量变化，先用上一章的模型（不含 `Description` 和该检查约束）建立并应用 `InitialCreate`；如果项目已有对应快照，则跳过初始迁移两步，直接生成后续迁移。

~~~sh
dotnet new sln
dotnet new webapi --use-controllers -o src/AuctionService
dotnet sln add src/AuctionService/AuctionService.csproj
cd src/AuctionService
dotnet package add Npgsql.EntityFrameworkCore.PostgreSQL --version 10.0.3
dotnet package add Microsoft.EntityFrameworkCore.Design --version 10.0.14
dotnet tool install --global dotnet-ef --version 10.0.14
# 以已有的 Auction + Item 模型（无 Description 和 CHECK 约束）建立初始结构
dotnet ef migrations add InitialCreate
dotnet ef database update
# 切换到上方完整模型后，生成增量迁移
dotnet ef migrations add AddItemDescriptionAndBidCheck
~~~

`dotnet new sln` 在 .NET 10 SDK 默认创建 `.slnx`；`dotnet package add` 是 .NET 10 的新名词优先命令形式。`dotnet-ef`、EF Core 主包、Tools/Design 包应选同一兼容主版本；Npgsql 的 EF Core provider（数据库提供程序）也须兼容该 EF Core 版本。上例核对到 EF Core 10.0.14、Npgsql provider 10.0.3。

对本地开发数据库，`dotnet ef database update` 可以直接应用待迁移版本。生产发布通常生成并审查 SQL 脚本，或生成迁移 bundle；脚本适合需要 DBA 审批、修改或归档 SQL 的流程。EF Core 迁移是 provider-specific（provider 专属）的；如果应用要部署到 PostgreSQL 和 SQL Server，应分别验证 provider 与迁移策略，不要把一个数据库 provider 生成的迁移当作另一个 provider 的通用 SQL。数据库约束仍是数据正确性的最终共享边界，见[如何用约束保护业务规则并为读取建立索引？](../../engineering-foundations/databases/database-constraints-and-indexes.md)。

> [!info]- 来源
> - EF Core 10.0.14 包版本与目标框架：[Microsoft.EntityFrameworkCore NuGet](https://www.nuget.org/packages/Microsoft.EntityFrameworkCore/10.0.14)，于 2026-11-06 核对。
> - 主键、必需/可选属性和 nullable reference type 约定：[EF Core 属性与 nullability](https://learn.microsoft.com/en-us/ef/core/modeling/required-optional)，核对日期 2026-11-06。
> - 迁移比较模型快照、而非数据库实况；历史表记录已应用迁移：[EF Core 迁移概览](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/)，核对日期 2026-11-06。
> - 本地 `database update` 与生产 SQL 脚本/迁移包的选择：[应用迁移](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying)，EF Core 10 文档，核对日期 2026-11-06。
> - PostgreSQL provider 与其他 EF Core provider 的兼容关系：[Npgsql EF Core Provider 文档](https://www.npgsql.org/efcore/)，核对日期 2026-11-06；NuGet 最新稳定线为 [`Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3`](https://www.nuget.org/packages/Npgsql.EntityFrameworkCore.PostgreSQL/10.0.3)。
> - .NET 10 Web API controller 模板、.NET 10 `dotnet package add` 命令和 solution 默认格式：[控制器 Web API 教程](https://learn.microsoft.com/en-us/aspnet/core/tutorials/first-web-api?view=aspnetcore-10.0)、[依赖包管理 CLI](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-package-add)、[.NET 10 SDK tooling changes](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/sdk)，核对日期 2026-11-06。
