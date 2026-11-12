# MongoDB 文档搜索怎样从启动初始化走到相关度排序？

**案例：** 搜索服务接收 `GET /api/search?searchTerm=blue`，从商品文档中查找品牌、型号或颜色匹配的商品。关系库里的拍卖与商品可以分表并通过外键关联；搜索服务选择把一张搜索卡片需要的 `Make`、`Model`、`Color` 放在同一文档，按其读取模式设计文档和 text index（文本索引）。这是独立的本地搜索数据样例：`Data/ItemData.json` 会单独写入 `SearchDB`，不会自动读取或同步前四篇中的 PostgreSQL 拍卖表；真实双库部署还需要明确的同步路径。MongoDB.Entities 在此封装 MongoDB .NET/C# Driver（MongoDB C# 驱动）的连接、索引和查询 API。

下面固定 .NET 10、`MongoDB.Entities 26.0.0` 和 MongoDB Community Server `8.0` 镜像线；NuGet 包 26.0.0 基于 .NET Standard 2.1，声明依赖 MongoDB.Driver 3.12.0 或更高版本，核对时当前稳定包为 3.13.0。标签 `mongo:8.0` 会跟随该维护线的补丁版本。

## 启动阶段怎样准备连接、索引和本地样例？

启动时连接目标数据库、确保复合文本索引存在，先查集合中有无文档，再读本地 JSON 并保存初始文档；完成后才映射控制器并接受请求：

~~~mermaid
flowchart TD
    Start[创建 WebApplicationBuilder] --> Init[初始化 SearchDB]
    Init --> Index[确保 Make / Model / Color 文本索引]
    Index --> Seed{集合中有文档？}
    Seed -->|有| Ready[映射控制器并开始接受请求]
    Seed -->|无| Json[读取工作目录下 Data/ItemData.json]
    Json --> Save[保存种子文档]
    Save --> Ready
~~~

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
        ?? throw new InvalidOperationException(
            "Item seed data is empty or invalid.");

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

把宿主机服务的 URI 存为 `mongodb://root:<URL 编码后的密码>@localhost:27017/?authSource=admin`；若服务也在 Compose 网络中，把主机名改为服务名 `mongo`。URI 没有默认数据库路径时，MongoDB Driver 会把缺省认证数据库设为 `admin`；URI 有数据库路径而未指定 `authSource` 时，默认认证数据库则是该路径。本例显式写 `authSource=admin`，因为官方镜像把 root 用户建在 `admin`，而 `DB.InitAsync("SearchDB", settings)` 单独选择读写目标 `SearchDB`。

在服务项目目录把本地 URI 存入 User Secrets；密码含 URI 保留字符时先做百分号编码：

~~~sh
dotnet user-secrets init
mongoUri='mongodb://root:<URL 编码后的密码>@localhost:27017/'
mongoUri="${mongoUri}?authSource=admin"
dotnet user-secrets set \
  "ConnectionStrings:MongoDbConnection" "$mongoUri"
~~~

在服务项目目录 `src/SearchService/` 保存 `compose.yaml`；同目录中放置 `Data/ItemData.json`：

~~~yaml
services:
  mongo:
    image: mongo:8.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:?set MONGO_ROOT_PASSWORD}
    ports:
      - "127.0.0.1:27017:27017"
    volumes:
      - mongodata:/data/db

volumes:
  mongodata:
~~~

~~~json
[
  { "Make": "Northstar", "Model": "S1", "Color": "blue" },
  { "Make": "Northstar", "Model": "S2", "Color": "red" },
  { "Make": "Harbor", "Model": "Blue", "Color": "blue" }
]
~~~

`File.ReadAllTextAsync("Data/ItemData.json")` 相对进程当前工作目录解析，不是自动相对源码文件或发布目录。开发时从 `src/SearchService/` 启动 `dotnet run`，并在该目录保存 `Data/ItemData.json` 与 `compose.yaml`。先在这个目录设置只供本地使用的 Compose 密码并启动服务，再检查数据库已就绪，最后启动 API：

~~~sh
export MONGO_ROOT_PASSWORD='<本地开发密码>'
docker compose up -d
docker compose logs -f mongo
~~~

`up -d` 返回时容器已启动，但 MongoDB 可能还未接受连接。空卷首次初始化时，官方镜像会先启动仅监听容器 loopback 的临时 `mongod`；日志中的 `MongoDB init process complete; ready for start up.` 表示初始化阶段结束，不表示最终网络监听已就绪。继续跟随日志，等后续正式 `mongod` 启动并再次出现 `Waiting for connections` 后再运行 API。已有数据卷会跳过首次初始化阶段，只等正式服务器的 ready 行。保存上面的三个种子文档为 `Data/ItemData.json`，再从此项目目录运行应用：

~~~sh
mkdir -p Data
dotnet run
~~~

如需应用在 Compose 中运行，连接串主机使用服务名 `mongo`，宿主机的 `localhost` URI 不能直接复用。

只有空数据目录首次初始化时，镜像的 root 用户环境变量才生效；容器重建不会自动替换旧数据库的用户。生产服务使用权限受限的应用账号，不直接使用 root。

同一个集合最多有一个文本索引；要让这三个字段都可检索，就把它们放进同一复合文本索引。索引在服务启动阶段创建，匹配相同配置的索引可重复确保存在。生产部署应把种子数据做成单次初始化或幂等写入；“先检查集合中有无文档，再插入”只适合单进程本地演示，多个副本同时启动会竞态。连接使用本地 User Secrets 或环境变量；镜像初始化的 root 用户仅供本机示例，应用生产凭据应限制数据库权限。

## 搜索词如何决定命中和排序？

`GET /api/search?searchTerm=blue` 匹配第一和第三条示例文档；默认文本索引大小写不敏感，所以 `Blue` 也匹配 `blue`。第三条的 `Model` 与 `Color` 都含词项 `blue`，第一条只有 `Color` 命中；在三个字段默认等权、其他条件相同的前提下，MongoDB 8.0 的文本得分把第三条排在前面。不带搜索词时则按品牌和 ID 排序。这个顺序是根据 MongoDB 8.0 的计分规则和上述文档推导，未连接 MongoDB 实际查询；分数相同的文档没有保证顺序。文本查询会解析搜索词：普通词项通常按逻辑 OR 匹配；`"blue car"` 可请求精确短语，`-red` 表示排除词项。短语、否定属于搜索语法；`$language` 选择分词/词干规则，大小写或重音敏感性由独立选项控制。它不是任意子串搜索，而且默认不会自动按得分排列。此例返回至多 50 条结果，避免把整个集合一次序列化到 HTTP 响应中。

启动阶段保存的三个种子文档用于推导：

~~~mermaid
flowchart TD
    Request[GET /api/search?searchTerm=blue] --> Term{有非空搜索词？}
    Term -->|有| Match[配置 $text 匹配与文本得分排序]
    Term -->|无| Browse[按 Make、ID 排序]
    Match --> Limit[Limit 50]
    Browse --> Limit
    Limit --> Execute[执行查询]
    Execute --> Map[映射 Id、Make、Model、Color]
    Map --> Response[返回 JSON]
~~~

~~~csharp
using Microsoft.AspNetCore.Mvc;
using MongoDB.Entities;

public sealed record ItemSearchDto(
    string Id, string Make, string Model, string Color);

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

两条路径都在分支汇合后共用 `Limit(50)`、执行和 DTO 映射。对 `blue` 的返回形状有四个字段：

~~~json
[
  {
    "id": "<higher-scoring Item ID>",
    "make": "Harbor",
    "model": "Blue",
    "color": "blue"
  },
  {
    "id": "<other matching Item ID>",
    "make": "Northstar",
    "model": "S1",
    "color": "blue"
  }
]
~~~

文本得分仅在非空查询分支排序；不要在这条链上再追加品牌排序并假设它不影响相关度结果。空查询按品牌排序，与文本查询是不同读路径。普通 `$text` 适用于自托管 Community 部署；MongoDB 官方文档建议对更丰富的全文搜索需求评估 MongoDB Search，这不是本文使用的本地文本索引接口。

从旧 `MongoDB.Entities 22.1.0` 项目升级时，先检查现有 BSON ID 类型：v26 移除了库对公开字符串 ID 和引用字段的隐式 ObjectId 序列化；旧库中可解析为 ObjectId 的字符串可能实际存为 BSON ObjectId。直接切换可能使已有实体 ID、关系引用或嵌入对象无法反序列化。按官方 v26 升级说明备份并验证每类 ID 和引用字段的迁移；内部文件块 ID 是例外，不应照搬普通字符串迁移。

> [!info]- 来源
> - `MongoDB.Entities 26.0.0` 稳定包、目标框架与 `MongoDB.Driver >= 3.12.0` 依赖：[NuGet 包页](https://www.nuget.org/packages/MongoDB.Entities/26.0.0)，核对日期 2026-11-13；MongoDB 官方 NuGet 当前稳定 driver 为 3.13.0：[MongoDB.Driver 3.13.0](https://www.nuget.org/packages/MongoDB.Driver/3.13.0)。
> - 官方 8.0 镜像在首次初始化时使用临时 `mongod`，然后启动正式监听进程：[MongoDB 8.0 official entrypoint](https://github.com/docker-library/mongo/blob/master/8.0/docker-entrypoint.sh)，核对日期 2026-11-13。
> - 连接初始化、文本索引创建和 `DB.InitAsync` 的异步接口：[MongoDB.Entities 安装文档](https://mongodb-entities.com/wiki/Get-Started.html)、[索引创建](https://mongodb-entities.com/wiki/Indexes.html)，文档核对日期 2026-11-13。
> - `Find`、`Match(Search.Full, ...)`、`SortByTextScore`、排序和 `Limit`：[MongoDB.Entities Find queries](https://mongodb-entities.com/wiki/Queries-Find.html)，核对日期 2026-11-13。
> - 一个集合的文本索引限制、默认大小写不敏感、`$text` 词项逻辑、默认不按得分排序和 score 元数据：[MongoDB Server Manual 8.0 文本索引](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/)、[文本索引属性](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/text-index-properties/)、[`$text` 查询](https://www.mongodb.com/docs/v8.0/reference/operator/query/text/)，核对日期 2026-11-13。
> - 文本索引默认每个字段权重为 1：[MongoDB Server Manual 8.0 Assign Weights](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/control-text-search-results/)，核对日期 2026-11-13。
> - 8.0 文本得分按出现频率、文档长度、索引字段权重等综合计算，默认字段权重相同；计分细节和本例排序为基于 8.0 规则的推导，没有执行实际查询：[MongoDB Server Manual 8.0 文本得分](https://www.mongodb.com/docs/v8.0/reference/operator/query/text/#text-score)、[MongoDB 8.0 源码 `fts_spec.cpp`](https://github.com/mongodb/mongo/blob/r8.0.0/src/mongo/db/fts/fts_spec.cpp)，核对日期 2026-11-13。
> - URI 默认数据库路径、认证数据库与 `authSource` 缺省行为：[MongoDB Server Manual 8.0 Connection String Formats](https://www.mongodb.com/docs/v8.0/reference/connection-string-formats/)、[Connection String Options](https://www.mongodb.com/docs/v8.0/reference/connection-string-options/)，核对日期 2026-11-13。
> - 官方 Mongo 镜像 `8.0` 标签、`/data/db` 卷和初始化 root 用户位于 `admin` 库：[Docker Official Image mongo](https://hub.docker.com/_/mongo/)，核对日期 2026-11-13。
> - v22 到 v26 的 BSON ID 存储变化与迁移要求：[MongoDB.Entities Upgrading to v26](https://mongodb-entities.com/wiki/Upgrade-to-v26.html)，核对日期 2026-11-13。
