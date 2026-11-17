# MongoDB 文档搜索怎样从启动初始化走到相关度排序？

**案例：** 搜索服务接收 `GET /api/search?searchTerm=blue`，从商品文档中查找品牌、型号或颜色匹配的商品。关系数据库里，拍卖和商品分表存储、通过外键关联；搜索服务则按自己的读取方式设计数据：把一张搜索结果卡片需要的 `Make`、`Model`、`Color` 放进同一个文档，并在这三个字段上建 text index（文本索引）。这是一个独立的本地样例：种子文件 `Data/ItemData.json` 单独写入 `SearchDB` 数据库，不会读取或同步本组前几篇中的 PostgreSQL 拍卖表；真实部署两个数据库时，还需要设计明确的同步路径。代码使用的 MongoDB.Entities 库封装了 MongoDB .NET/C# Driver（MongoDB C# 驱动）的连接、索引和查询 API。

下面固定 .NET 10、`MongoDB.Entities 26.0.0` 和 MongoDB Community Server `8.0` 镜像线；NuGet 包 26.0.0 面向 .NET Standard 2.1，依赖 MongoDB.Driver 3.12.0 或更高版本；截至 2026-11-16，Driver 的最新稳定版是 3.14.0。镜像标签 `mongo:8.0` 会随 8.0 维护线自动更新到最新补丁版本。

## 启动阶段怎样准备连接、索引和本地样例？

应用启动时依次完成：连接目标数据库，确保复合文本索引存在，检查集合是否为空，为空时读取本地 JSON 写入初始文档；这些都完成后才映射控制器、开始接受请求：

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

代码从配置读取 `MongoDbConnection` 连接串。应用运行在宿主机上时，把它设为 `mongodb://root:<URL 编码后的密码>@localhost:27017/?authSource=admin`；应用也在 Compose 网络中时，把主机名改为服务名 `mongo`。认证数据库的默认值取决于 URI：没有数据库路径时默认是 `admin`；有数据库路径但没写 `authSource` 时，默认就是该路径中的数据库。本例显式写 `authSource=admin`，因为官方镜像把 root 用户建在 `admin` 库中，而实际读写的数据库 `SearchDB` 由 `DB.InitAsync("SearchDB", settings)` 另行指定。

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

`File.ReadAllTextAsync("Data/ItemData.json")` 中的相对路径按进程当前工作目录解析，而不是源码文件或发布目录。所以开发时要在 `src/SearchService/` 中运行 `dotnet run`，并把 `Data/ItemData.json` 和 `compose.yaml` 都放在这个目录。在该目录先设置只供本地使用的 Compose 密码并启动 MongoDB，确认数据库就绪后再启动 API：

~~~sh
export MONGO_ROOT_PASSWORD='<本地开发密码>'
docker compose up -d
docker compose logs -f mongo
~~~

`up -d` 返回时容器已经启动，但 MongoDB 可能还不接受连接。卷为空时，官方镜像会先启动一个只监听容器内 loopback 地址的临时 `mongod` 来完成初始化；日志中的 `MongoDB init process complete; ready for start up.` 只表示初始化阶段结束，不表示正式服务已开始监听网络。继续跟随日志，等正式 `mongod` 启动并再次出现 `Waiting for connections` 后再运行 API。卷里已有数据时会跳过初始化阶段，只需等正式服务器的那一行。然后在同一项目目录创建 `Data` 目录、把上面三个种子文档保存为 `Data/ItemData.json`，再运行应用：

~~~sh
mkdir -p Data
dotnet run
~~~

如果应用也在 Compose 中运行，连接串主机要用服务名 `mongo`，不能直接复用宿主机的 `localhost` URI。

镜像的 root 用户环境变量只在数据目录为空、首次初始化时生效；重建容器不会替换已有数据库中的用户。root 账号只用于本机示例，生产服务应使用权限受限的应用账号。

回到启动代码：同一个集合最多只能有一个文本索引，所以要让三个字段都能被搜索，就要把它们放进同一个复合文本索引。索引在启动阶段创建，配置相同时重复执行也只是确认它已存在。种子数据的“先检查集合是否为空，再插入”只适合单进程本地演示，多个副本同时启动时会产生竞态；生产部署应把种子数据做成一次性初始化或幂等写入。

## 搜索词如何决定命中和排序？

以启动时写入的三个种子文档为例，`GET /api/search?searchTerm=blue` 会匹配第一条和第三条：默认的文本索引不区分大小写，所以 `Blue` 也匹配 `blue`。第三条的 `Model` 和 `Color` 都含词项 `blue`，第一条只有 `Color` 命中；三个字段默认权重相同、其他条件也相同时，MongoDB 8.0 的文本得分会把第三条排在前面。这个顺序是按 MongoDB 8.0 的计分规则推导的，没有连接 MongoDB 实际查询；分数相同的文档之间没有确定顺序。不带搜索词时，接口改为按品牌和 ID 排序。

文本查询会先解析搜索词：多个普通词项通常按“或”匹配；`"blue car"` 表示精确短语，`-red` 表示排除该词项。`$language` 选择分词和词干规则，大小写和重音是否敏感由另外的选项控制。文本查询不是任意子串搜索，而且默认不会按得分排序，需要显式要求。本例最多返回 50 条结果，避免把整个集合一次性序列化到 HTTP 响应中。

下图是搜索请求的处理流程，代码随后实现它：

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

两条分支汇合后共用 `Limit(50)`、查询执行和 DTO 映射。搜索 `blue` 时，响应中每条结果有四个字段：

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

只有搜索词非空的分支按文本得分排序；如果在这条查询链上再追加品牌排序，会改变相关度排序结果。空查询按品牌排序，是另一条读路径。`$text` 适用于自托管的 Community 部署；需要更丰富的全文搜索时，MongoDB 官方文档建议评估 MongoDB Search，它与本文使用的文本索引是不同的接口。

从旧的 `MongoDB.Entities 22.1.0` 项目升级时，先检查已有数据中 ID 的 BSON 类型：旧版本会把形如 ObjectId 的字符串 ID 和引用字段隐式存成 BSON ObjectId，v26 去掉了这种隐式转换。直接升级可能导致已有实体 ID、关系引用或嵌入对象无法反序列化。按官方 v26 升级说明备份并验证每类 ID 和引用字段的迁移；内部文件块 ID 是例外，不应照搬普通字符串迁移。

> [!info]- 来源
> - `MongoDB.Entities 26.0.0` 稳定包、目标框架与 `MongoDB.Driver >= 3.12.0` 依赖：[NuGet 包页](https://www.nuget.org/packages/MongoDB.Entities/26.0.0)，核对日期 2026-11-13；MongoDB.Driver 最新稳定版为 3.14.0（2026-11-12 发布）：[MongoDB.Driver 3.14.0](https://www.nuget.org/packages/MongoDB.Driver/3.14.0)，核对日期 2026-11-16。
> - 官方 8.0 镜像在首次初始化时使用临时 `mongod`，然后启动正式监听进程：[MongoDB 8.0 official entrypoint](https://github.com/docker-library/mongo/blob/master/8.0/docker-entrypoint.sh)，核对日期 2026-11-13。
> - 连接初始化、文本索引创建和 `DB.InitAsync` 的异步接口：[MongoDB.Entities 安装文档](https://mongodb-entities.com/wiki/Get-Started.html)、[索引创建](https://mongodb-entities.com/wiki/Indexes.html)，文档核对日期 2026-11-13。
> - `Find`、`Match(Search.Full, ...)`、`SortByTextScore`、排序和 `Limit`：[MongoDB.Entities Find queries](https://mongodb-entities.com/wiki/Queries-Find.html)，核对日期 2026-11-13。
> - 一个集合的文本索引限制、默认大小写不敏感、`$text` 词项逻辑、默认不按得分排序和 score 元数据：[MongoDB Server Manual 8.0 文本索引](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/)、[文本索引属性](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/text-index-properties/)、[`$text` 查询](https://www.mongodb.com/docs/v8.0/reference/operator/query/text/)，核对日期 2026-11-13。
> - 文本索引默认每个字段权重为 1：[MongoDB Server Manual 8.0 Assign Weights](https://www.mongodb.com/docs/v8.0/core/indexes/index-types/index-text/control-text-search-results/)，核对日期 2026-11-13。
> - 8.0 文本得分按出现频率、文档长度、索引字段权重等综合计算，默认字段权重相同；计分细节和本例排序为基于 8.0 规则的推导，没有执行实际查询：[MongoDB Server Manual 8.0 文本得分](https://www.mongodb.com/docs/v8.0/reference/operator/query/text/#text-score)、[MongoDB 8.0 源码 `fts_spec.cpp`](https://github.com/mongodb/mongo/blob/r8.0.0/src/mongo/db/fts/fts_spec.cpp)，核对日期 2026-11-13。
> - URI 默认数据库路径、认证数据库与 `authSource` 缺省行为：[MongoDB Server Manual 8.0 Connection String Formats](https://www.mongodb.com/docs/v8.0/reference/connection-string-formats/)、[Connection String Options](https://www.mongodb.com/docs/v8.0/reference/connection-string-options/)，核对日期 2026-11-13。
> - 官方 Mongo 镜像 `8.0` 标签、`/data/db` 卷和初始化 root 用户位于 `admin` 库：[Docker Official Image mongo](https://hub.docker.com/_/mongo/)，核对日期 2026-11-13。
> - v22 到 v26 的 BSON ID 存储变化与迁移要求：[MongoDB.Entities Upgrading to v26](https://mongodb-entities.com/wiki/Upgrade-to-v26.html)，核对日期 2026-11-13。
