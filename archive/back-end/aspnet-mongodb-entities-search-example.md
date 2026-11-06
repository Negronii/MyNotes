# MongoDB 文档搜索怎样从启动初始化走到相关度排序？

**案例：** 搜索服务接收 `GET /api/search?searchTerm=blue`，从商品文档中查找品牌、型号或颜色匹配的商品。关系库里的拍卖与商品可以分表并通过外键关联；搜索服务选择把一张搜索卡片需要的 `Make`、`Model`、`Color` 放在同一文档，按其读取模式设计文档和 text index（文本索引）。这是独立的本地搜索数据样例：`Data/ItemData.json` 会单独写入 `SearchDB`，不会自动读取或同步前四篇中的 PostgreSQL 拍卖表；真实双库部署还需要明确的同步路径。MongoDB.Entities 在此封装 MongoDB .NET/C# Driver（MongoDB C# 驱动）的连接、索引和查询 API。

~~~mermaid
flowchart TD
    Start[启动服务并初始化 DB] --> Index[创建 Make / Model / Color 文本索引]
    Index --> Seed{集合为空？}
    Seed -->|是：本地样例| Json[读取 JSON 种子文件并保存文档]
    Seed -->|否| Ready[开始接受请求]
    Json --> Ready
    Ready --> Term{请求含搜索词？}
    Term -->|是| Match[使用 $text 查询]
    Match --> Score[按文本得分排序并限制结果数]
    Term -->|否| Sort[按 Make、ID 排序]
    Score --> Response[映射搜索 DTO 并返回 JSON]
    Sort --> Response
~~~

下面固定 .NET 10、`MongoDB.Entities 26.0.0` 和 MongoDB Community Server `8.0` 镜像线；NuGet 包 26.0.0 基于 .NET Standard 2.1，声明依赖 MongoDB.Driver 3.12.0 或更高版本，核对时当前稳定包为 3.13.0。标签 `mongo:8.0` 会跟随该维护线的补丁版本。先连接并创建索引，再在单进程本地示例中按空集合条件装入 JSON 种子数据：

## 启动阶段怎样准备连接、索引和本地样例？

~~~csharp
using System.Text.Json;
using MongoDB.Driver;
using MongoDB.Entities;

var builder = WebApplication.CreateBuilder(args);
var settings = MongoClientSettings.FromConnectionString(
    builder.Configuration.GetConnectionString("MongoDbConnection")
    ?? throw new InvalidOperationException("Missing MongoDbConnection."));

var db = await DB.InitAsync("SearchDB", settings);
builder.Services.AddSingleton(db);
builder.Services.AddControllers();

var app = builder.Build();

await db.Index<Item>()
    .Key(item => item.Make, KeyType.Text)
    .Key(item => item.Model, KeyType.Text)
    .Key(item => item.Color, KeyType.Text)
    .CreateAsync();

if (!await db.Find<Item>().ExecuteAnyAsync())
{
    var json = await File.ReadAllTextAsync("Data/ItemData.json");
    var items = JsonSerializer.Deserialize<List<Item>>(
        json,
        new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
        ?? throw new InvalidOperationException("Item seed data is empty or invalid.");

    await db.SaveAsync(items);
}

app.MapControllers();
app.Run();

public sealed class Item : Entity
{
    public string Make { get; set; } = "";
    public string Model { get; set; } = "";
    public string Color { get; set; } = "";
}
~~~

宿主机上的开发服务可连接到 `mongodb://root:<URL 编码后的密码>@localhost:27017/?authSource=admin`；若服务也在 Compose 网络中，把主机名改为服务名 `mongo`。MongoDB Official Image 的 root 用户建在 `admin` 认证数据库中，应用连接到 `SearchDB` 时仍要指定 `authSource=admin`。

在服务项目目录把本地 URI 存入 User Secrets；密码含 URI 保留字符时先做百分号编码：

~~~sh
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:MongoDbConnection" "mongodb://root:<URL 编码后的密码>@localhost:27017/?authSource=admin"
~~~

本地容器用命名卷保存文档：

~~~yaml
services:
  mongo:
    image: mongo:8.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:?set a local MongoDB password}
    ports:
      - "127.0.0.1:27017:27017"
    volumes:
      - mongodata:/data/db

volumes:
  mongodata:
~~~

只有空数据目录首次初始化时，镜像的 root 用户环境变量才生效；容器重建不会自动替换旧数据库的用户。生产服务使用权限受限的应用账号，不直接使用 root。

同一个集合最多有一个文本索引；要让这三个字段都可检索，就把它们放进同一复合文本索引。索引在服务启动阶段创建，匹配相同配置的索引可重复确保存在。生产部署应把种子数据做成单次初始化或幂等写入；“先 count 为零再插入”只适合单进程本地演示，多个副本同时启动会竞态。连接使用本地 User Secrets 或环境变量；镜像初始化的 root 用户仅供本机示例，应用生产凭据应限制数据库权限。

## 搜索词如何决定命中和排序？

示例种子数据只有三条：

~~~json
[
  { "Make": "Northstar", "Model": "S1", "Color": "blue" },
  { "Make": "Northstar", "Model": "S2", "Color": "red" },
  { "Make": "Harbor", "Model": "H1", "Color": "blue" }
]
~~~

`GET /api/search?searchTerm=blue` 会匹配第一和第三条文档，再按 MongoDB text score（文本得分）排序；不带搜索词时则按品牌和 ID 排序。文本查询默认把搜索词拆成词项，通常按逻辑 OR 匹配；它不是任意子串搜索，而且默认不会自动按得分排列。需要短语、否定、语言词干或大小写语义时，要明确指定查询选项。此例返回至多 50 条结果，避免把整个集合一次序列化到 HTTP 响应中：

~~~csharp
using Microsoft.AspNetCore.Mvc;
using MongoDB.Entities;

public sealed record ItemSearchDto(string Id, string Make, string Model, string Color);

[ApiController]
[Route("api/search")]
public sealed class SearchController : ControllerBase
{
    private readonly DB _db;

    public SearchController(DB db) => _db = db;

    [HttpGet]
    public async Task<ActionResult<List<ItemSearchDto>>> Search(
        [FromQuery] string? searchTerm,
        CancellationToken cancellationToken)
    {
        var query = _db.Find<Item>();

        if (!string.IsNullOrWhiteSpace(searchTerm))
        {
            query.Match(MongoDB.Entities.Search.Full, searchTerm)
                .SortByTextScore();
        }
        else
        {
            query.Sort(item => item.Make, Order.Ascending)
                .Sort(item => item.ID, Order.Ascending);
        }

        var items = await query
            .Limit(50)
            .ExecuteAsync(cancellationToken);

        var response = items.Select(item => new ItemSearchDto(
            item.ID, item.Make, item.Model, item.Color)).ToList();

        return Ok(response);
    }
}
~~~

文本得分仅在非空查询分支排序；不要在这条链上再追加品牌排序并假设它不影响相关度结果。空查询按品牌排序，与文本查询是不同读路径。普通 `$text` 适用于自托管 Community 部署；MongoDB 官方文档建议对更丰富的全文搜索需求评估 MongoDB Search，这不是本文使用的本地文本索引接口。

从旧 `MongoDB.Entities 22.1.0` 项目升级时，先检查现有 BSON ID 类型：v26 移除了库对公开字符串 ID 和引用字段的隐式 ObjectId 序列化；旧库中可解析为 ObjectId 的字符串可能实际存为 BSON ObjectId。直接切换可能使已有实体 ID、关系引用或嵌入对象无法反序列化。按官方 v26 升级说明备份并验证每类 ID 和引用字段的迁移；内部文件块 ID 是例外，不应照搬普通字符串迁移。

> [!info]- 来源
> - `MongoDB.Entities 26.0.0` 稳定包、目标框架与 `MongoDB.Driver >= 3.12.0` 依赖：[NuGet 包页](https://www.nuget.org/packages/MongoDB.Entities/26.0.0)，核对日期 2026-11-06；MongoDB 官方 NuGet 当前稳定 driver 为 3.13.0：[MongoDB.Driver 3.13.0](https://www.nuget.org/packages/MongoDB.Driver/3.13.0)。
> - 连接初始化、文本索引创建和 `DB.InitAsync` 的异步接口：[MongoDB.Entities 安装文档](https://mongodb-entities.com/wiki/Get-Started.html)、[索引创建](https://mongodb-entities.com/wiki/Indexes.html)，文档核对日期 2026-11-06。
> - `Find`、`Match(Search.Full, ...)`、`SortByTextScore`、排序和 `Limit`：[MongoDB.Entities Find queries](https://mongodb-entities.com/wiki/Queries-Find.html)，核对日期 2026-11-06。
> - 一个集合的文本索引限制、`$text` 词项逻辑、默认不按得分排序和 score 元数据：[MongoDB Server Manual 文本索引](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-text/)、[`$text` 查询](https://www.mongodb.com/docs/manual/reference/operator/query/text/)，核对当前 Server Manual 9.0 文档，2026-11-06。
> - 官方 Mongo 镜像 `8.0` 标签、`/data/db` 卷和初始化 root 用户位于 `admin` 库：[Docker Official Image mongo](https://hub.docker.com/_/mongo/)，核对日期 2026-11-06。
> - v22 到 v26 的 BSON ID 存储变化与迁移要求：[MongoDB.Entities Upgrading to v26](https://mongodb-entities.com/wiki/Upgrade-to-v26.html)，核对日期 2026-11-06。
