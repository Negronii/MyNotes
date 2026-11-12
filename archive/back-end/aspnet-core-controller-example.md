# ASP.NET Core 控制器如何把 HTTP 请求送到正确的操作并返回结果？

**案例：** 卖家调用 `POST /api/auctions`，正文只含商品品牌、型号、颜色和起拍价。操作将通过验证的请求映射为拍卖并保存，返回 `201 Created`、资源地址和响应数据传输对象（Data Transfer Object，DTO）；随后 `GET /api/auctions/{id}` 能读回包含商品字段的拍卖。控制器负责把 HTTP 输入送入应用，并把应用结果变成 HTTP 响应；它不应承担数据库模型设计或大段业务规则。

## 请求经过哪些处理才进入操作方法？

~~~mermaid
flowchart TD
    Request[路由选中请求] --> Auth[建立认证主体]
    Auth -->|无已认证主体| Challenge["Challenge<br/>常见 401"]
    Auth -->|已认证| Policy{Seller 策略通过？}
    Policy -->|否| Forbid["Forbid<br/>常见 403"]
    Policy -->|是| Continue[进入模型绑定]
~~~

路由先选择操作，authentication（身份验证）建立声明主体 `ClaimsPrincipal`，authorization（授权）再检查 `Seller` 策略中的角色与主体 ID。challenge（认证挑战）与 forbid（授权拒绝）交给已配置的身份验证方案处理，因此具体响应并非所有应用都固定为 401 / 403：Cookie 方案可能对浏览器请求重定向；ASP.NET Core 10 识别为 API 的端点使用 Cookie 方案时默认返回 401 / 403。本例策略只要求 `NameIdentifier` claim 存在，不校验其格式；其值必须由可信身份提供方签发，并稳定地区分卖家。未认证或策略拒绝时，操作方法都不会运行。

隔离测试的认证处理器中，匿名请求收到 401；已有主体但缺少 `Seller` 角色或 `NameIdentifier` 的请求收到 403。这些状态表示测试方案的 challenge/forbid 结果，不替代应用对真实身份方案的配置。

身份和策略通过后，模型绑定与验证才处理本例的输入：

~~~mermaid
flowchart TD
    Post[POST：发送 JSON] --> Media{JSON 媒体类型？}
    Media -->|否| Unsupported["415<br/>媒体类型不支持"]
    Media -->|是| Body["绑定 JSON<br/>CreateAuctionDto"]
    Get["GET /api/auctions/{id}"] --> Id[路径 id 转为 Guid]
    Body --> State{ModelState 有效？}
    Id --> State
    State -->|否| BadRequest["自动 400<br/>操作不执行"]
    State -->|是| Action[执行选中的操作]
~~~

`ModelState`（模型状态）会收集两类错误：模型绑定的解析/类型转换错误，以及模型验证阶段的 DTO 约束错误。例如 `GET /api/auctions/not-a-guid` 的路径形状能匹配 `{id}`，但转成 `Guid` 失败；JSON 语法错误或字段不能转换为 DTO 目标类型也会记入绑定错误。`[Range]` 约束则在验证阶段产生错误。由于控制器标有 `[ApiController]`，两类无效状态都会在操作方法运行前自动返回 400。控制器构造器通过 dependency injection（依赖注入）取得 `AuctionDbContext`（EF Core 中用于查询、跟踪变更和提交数据库操作的对象）及映射器。这里的 400 阻止的是操作方法执行；控制器对象可以已经构造完成。输入有效时，操作方法使用已注入的对象调用数据库异步 API。

本例假设应用已经配置并启用可用的认证方案；把已认证且带卖家角色和主体 ID 的调用方视为卖家。实际身份提供程序必须签发相应 claim（声明），应用再注册对应 policy（授权策略）：

~~~csharp
using System.Security.Claims;

builder.Services.AddAuthorization(options =>
    options.AddPolicy("Seller", policy =>
        policy.RequireAuthenticatedUser()
            .RequireRole("Seller")
            .RequireClaim(ClaimTypes.NameIdentifier)));
~~~

## 控制器怎样映射并保存一次拍卖？

~~~csharp
using System.Security.Claims;
using AuctionService.Data;
using AuctionService.DTOs;
using AuctionService.Entities;
using AutoMapper;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

[ApiController]
[Authorize(Policy = "Seller")]
[Route("api/auctions")]
public sealed class AuctionsController : ControllerBase
{
    private readonly AuctionDbContext _context;
    private readonly IMapper _mapper;

    public AuctionsController(AuctionDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    [HttpGet]
    public async Task<ActionResult<List<AuctionDto>>> GetAll(
        CancellationToken cancellationToken)
    {
        var sellerId = GetRequiredSellerId();
        var auctions = await _context.Auctions
            .AsNoTracking()
            .Include(a => a.Item)
            .Where(a => a.SellerId == sellerId)
            .OrderBy(a => a.Item.Make)
            .ThenBy(a => a.Id)
            .ToListAsync(cancellationToken);

        return Ok(_mapper.Map<List<AuctionDto>>(auctions));
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<AuctionDto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var sellerId = GetRequiredSellerId();
        var auction = await _context.Auctions
            .AsNoTracking()
            .Include(a => a.Item)
            .SingleOrDefaultAsync(
                a => a.Id == id && a.SellerId == sellerId,
                cancellationToken);

        if (auction is null)
        {
            return NotFound();
        }

        return Ok(_mapper.Map<AuctionDto>(auction));
    }

    [HttpPost]
    public async Task<ActionResult<AuctionDto>> Create(
        CreateAuctionDto input,
        CancellationToken cancellationToken)
    {
        var auction = _mapper.Map<Auction>(input);
        auction.SellerId = GetRequiredSellerId();

        _context.Auctions.Add(auction);
        await _context.SaveChangesAsync(cancellationToken);

        var response = _mapper.Map<AuctionDto>(auction);
        return CreatedAtAction(
            nameof(GetById),
            new { id = auction.Id },
            response);
    }

    private string GetRequiredSellerId() =>
        User.FindFirstValue(ClaimTypes.NameIdentifier)
        ?? throw new InvalidOperationException(
            "Authenticated identity has no subject claim.");
}
~~~

`GET` 列表显式装载关联的 `Item`，只读取当前卖家的拍卖，再按品牌和 ID 排序；`AsNoTracking` 表示读取后不需要 EF Core 跟踪这些实体的改动。按 ID 读取时，合法但不存在或不属于当前卖家的 ID 都走 `NotFound()`，不泄露其他卖家资源是否存在。POST 只把 DTO 映射到实体，并由已认证主体设置 `SellerId`；授权策略与查询条件共同落实资源归属边界。身份提供方必须可信地签发有效、稳定且能够区分卖家的 `NameIdentifier`，本例策略只检查该 claim 是否存在。

## 响应状态和返回类型怎样对应？

创建时的映射与 201 响应：

~~~mermaid
flowchart TD
    Post[有效的输入 DTO] --> Save[映射实体并保存]
    Save --> MapOut[映射响应 DTO]
    MapOut --> Created["201 + Location<br/>响应 DTO 的 JSON"]
~~~

按 ID 读取的分支：

~~~mermaid
flowchart TD
    Get[GET：有效 Guid] --> Query["按 ID 和卖家查询<br/>加载 Item"]
    Query --> Owned{查到所属记录？}
    Owned -->|是| Ok["200<br/>AuctionDto JSON"]
    Owned -->|否| Missing["404<br/>Problem Details"]
~~~

同一条 `POST /api/auctions` 请求以 `Content-Type: application/json` 发送以下 JSON 正文；客户端用 `Accept: application/json` 表明要接收 JSON：

~~~json
{
  "make": "Northstar",
  "model": "S1",
  "color": "blue",
  "startingBid": 100
}
~~~

输入 DTO 和两次映射只需要关注这些字段：

| 输入或服务端值 | 保存时的去向 | `AuctionDto` 输出 |
|---|---|---|
| `make`、`model`、`color` | 写入 `Auction.Item.Make/Model/Color` | 同名商品字段 |
| `startingBid` | 写入 `Auction.StartingBid`；DTO 约束为 `[Range(1, 2_000_000)]` | `startingBid` |
| 已认证主体的 `NameIdentifier` | 服务端写入 `Auction.SellerId` | 不输出 |
| DTO 不提供的生成值或默认值 | 保存后有拍卖 `Id` 和内部关联 `ItemId`；`Status` 默认 `"draft"` | `id`、`status` |

例如把上面 `startingBid` 的 `100` 改成 `0`，模型验证失败并自动返回 400；此时操作方法没有执行，也没有保存记录。一次隔离运行中，有效请求得到 201，响应 JSON 是：

~~~json
{
  "id": "6c8a9648-4143-44e8-8a0f-a65eee844a9d",
  "make": "Northstar",
  "model": "S1",
  "color": "blue",
  "startingBid": 100,
  "status": "draft"
}
~~~

该次请求实际返回的 `Location` 是 `http://127.0.0.1:50280/api/auctions/6c8a9648-4143-44e8-8a0f-a65eee844a9d`；测试服务器的端口和 ID 每次会变，应使用自己响应中的完整地址。用同一卖家 GET 此地址返回 200 和相同 DTO；另一卖家 GET 同一地址得到 404 Problem Details，列表为空。`[HttpGet("{id}")]` 没有限定 `:guid` 路由约束，所以路径段 `not-a-guid` 会选中操作，随后因绑定为 `Guid` 失败而自动返回 400；这是绑定错误，不是查库后的 404。

响应 DTO 包含 `id`，但不输出内部 `ItemId` 或卖家 ID。一个安全测试还在 JSON 中附加了 `sellerId`、`status`：在 .NET 10 的默认 `System.Text.Json` 设置下，DTO 没有声明的字段会被忽略，而不是拒绝整条 JSON；服务端仍从主体写入 `SellerId`，状态保持 `"draft"`。如果接口需要拒绝未知字段，应单独启用 `JsonUnmappedMemberHandling.Disallow`。防止越权和严格拒绝输入是两个不同的可观察契约。

`CreatedAtAction` 创建 201 响应并根据 `GetById` 生成资源地址。响应 DTO 控制输出字段；状态码和 JSON 正文属于调用方可观察的 API 契约，详见[如何设计可预期的 HTTP API 契约？](../../engineering-foundations/backend/http-api-contracts.md)。

`Task<ActionResult<T>>` 同时表达异步完成和“带类型正文或 HTTP 结果”两种返回路径。`await` 等待数据库 I/O 时允许当前线程执行其他工作；`Task` 不意味着请求专属线程。`ActionResult<T>` 只是常见签名，控制器也可以返回 `IActionResult` 或其他受支持的结果类型。

`SaveChangesAsync` 成功后返回已写入的状态项数量，数据库失败通常以异常报告；不要把“返回零”机械映射为 400，因为这不一定表示客户端输入有误。对失败和验证错误的统一映射由应用的异常处理与 API 契约决定。

> [!info]- 来源
> - 请求绑定、验证、控制器操作和 `ActionResult<T>`：Microsoft Learn [ASP.NET Core MVC 概览](https://learn.microsoft.com/en-us/aspnet/core/mvc/overview?view=aspnetcore-10.0)、[控制器操作](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions?view=aspnetcore-10.0)、[模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)，核对版本 ASP.NET Core 10.0，2026-11-06。
> - `[ApiController]` 对无效模型状态的自动 400 行为：Microsoft Learn [Web API controllers](https://learn.microsoft.com/en-us/aspnet/core/web-api/?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
> - 授权过滤器先于模型绑定运行；挑战与拒绝分别交给身份验证方案：[MVC 过滤器](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/filters?view=aspnetcore-10.0)、[身份验证概览](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/?view=aspnetcore-10.0)。ASP.NET Core 10 的已识别 API 端点在 Cookie 方案下默认返回 401 / 403，而不是重定向：[API 端点身份验证行为](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/api-endpoint-auth?view=aspnetcore-10.0)，核对日期 2026-11-13。
> - ASP.NET Core 10 MVC 先建立控制器实例、再绑定参数和执行 action filters：[ControllerActionInvoker v10.0.0](https://github.com/dotnet/aspnetcore/blob/v10.0.0/src/Mvc/Mvc.Core/src/Infrastructure/ControllerActionInvoker.cs#L59-L80)，核对日期 2026-11-13。
> - 控制器构造器依赖注入：Microsoft Learn [控制器中的依赖注入](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
> - `CreatedAtAction` 与带状态码的控制器结果：Microsoft Learn [控制器操作结果](https://learn.microsoft.com/en-us/aspnet/core/web-api/action-return-types?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
> - `ModelState` 同时容纳绑定错误和验证错误；`[ApiController]` 对无效状态自动返回 400：[模型绑定](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/model-binding?view=aspnetcore-10.0)、[模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)、[自动 400 与错误响应](https://learn.microsoft.com/en-us/aspnet/core/web-api/?view=aspnetcore-10.0)。
> - ASP.NET Core 的默认 JSON 处理会跳过 DTO 未映射的字段；可显式改为拒绝：[System.Text.Json 未映射成员](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/missing-members)。嵌套 `Item` 字段到扁平响应 DTO 的映射依据：[AutoMapper IncludeMembers](https://docs.automapper.io/en/latest/Flattening.html)。本例 404 错误正文符合 [ASP.NET Core API 错误处理](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0)。
> - `SaveChangesAsync` 的写入计数与失败情况：[Microsoft Learn DbContext.SaveChangesAsync](https://learn.microsoft.com/en-us/dotnet/api/microsoft.entityframeworkcore.dbcontext.savechangesasync?view=efcore-10.0)，EF Core 10.0。
