# ASP.NET Core 控制器如何把 HTTP 请求送到正确的操作并返回结果？

**案例：** 卖家调用 `POST /api/auctions`，正文只含商品品牌、型号、颜色和起拍价。服务验证并保存拍卖后返回 `201 Created`、资源地址和响应数据传输对象（Data Transfer Object，DTO）；随后 `GET /api/auctions/{id}` 能读回包含商品字段的拍卖。控制器负责把 HTTP 输入送入应用，并把应用结果变成 HTTP 响应；它不应承担数据库模型设计或大段业务规则。

## 请求经过哪些处理才进入操作方法？

~~~mermaid
flowchart TD
    Client[调用方发出 HTTP 请求] --> Pipeline[ASP.NET Core 请求管线]
    Pipeline --> Route[路由选择控制器操作]
    Route --> Auth{Seller 授权策略通过？}
    Auth -->|否：未认证 401 / 策略拒绝 403| Denied[操作方法不执行]
    Auth -->|是| Bind[模型绑定：路径、查询或 JSON 正文]
    Bind --> Validate{模型验证通过？}
    Validate -->|否| BadRequest[400：操作方法不执行]
    Validate -->|是| Action[控制器查询或写入]
    Action --> Db[DbContext 执行异步查询或提交]
    Db --> Result[ActionResult：200、404 或 201]
    Result --> Serialize[序列化响应正文]
    Serialize --> Client
~~~

路由先选择操作；authentication（身份验证）建立调用方主体，authorization（授权）在模型绑定前检查 `Seller` 策略。未认证时走 401 challenge，主体缺少卖家角色或 ID claim 时走 403 forbid，两者都不会进入操作方法。model binding（模型绑定）再把路径、查询字符串或 JSON 正文转换成 C# 参数；model validation（模型验证）检查格式和声明的约束。应用配置了 `[ApiController]` 时，无效模型状态默认会在操作方法运行前返回 400。成功后，控制器通过 dependency injection（依赖注入）取得服务，调用数据库异步 API，再选择成功或错误结果。

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
    public async Task<ActionResult<List<AuctionDto>>> GetAll(CancellationToken cancellationToken)
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
        return CreatedAtAction(nameof(GetById), new { id = auction.Id }, response);
    }

    private string GetRequiredSellerId() =>
        User.FindFirstValue(ClaimTypes.NameIdentifier)
        ?? throw new InvalidOperationException("Authenticated identity has no subject claim.");
}
~~~

`GET` 列表显式装载关联的 `Item`，只读取当前卖家的拍卖，再按品牌和 ID 排序；`AsNoTracking` 表示读取后不需要 EF Core 跟踪这些实体的改动。按 ID 读取时，合法但不存在或不属于当前卖家的 ID 都走 `NotFound()`，不泄露其他卖家资源是否存在。POST 只把允许写入的 DTO 映射到实体；`SellerId` 从已认证主体读取，不接受调用方在 JSON 中伪造。授权策略验证卖家角色与 `ClaimTypes.NameIdentifier`，查询条件再落实资源归属边界。

## 响应状态和返回类型怎样对应？

`CreatedAtAction` 创建 201 响应并根据 `GetById` 生成资源地址。响应 DTO 控制输出字段；状态码和 JSON 正文属于调用方可观察的 API 契约，详见[如何设计可预期的 HTTP API 契约？](../../engineering-foundations/backend/http-api-contracts.md)。

`Task<ActionResult<T>>` 同时表达异步完成和“带类型正文或 HTTP 结果”两种返回路径。`await` 等待数据库 I/O 时允许当前线程执行其他工作；`Task` 不意味着请求专属线程。`ActionResult<T>` 只是常见签名，控制器也可以返回 `IActionResult` 或其他受支持的结果类型。

`SaveChangesAsync` 成功后返回已写入的状态项数量，数据库失败通常以异常报告；不要把“返回零”机械映射为 400，因为这不一定表示客户端输入有误。对失败和验证错误的统一映射由应用的异常处理与 API 契约决定。

> [!info]- 来源
> - 请求绑定、验证、控制器操作和 `ActionResult<T>`：Microsoft Learn [ASP.NET Core MVC 概览](https://learn.microsoft.com/en-us/aspnet/core/mvc/overview?view=aspnetcore-10.0)、[控制器操作](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions?view=aspnetcore-10.0)、[模型验证](https://learn.microsoft.com/en-us/aspnet/core/mvc/models/validation?view=aspnetcore-10.0)，核对版本 ASP.NET Core 10.0，2026-11-06。
> - `[ApiController]` 对无效模型状态的自动 400 行为：Microsoft Learn [Web API controllers](https://learn.microsoft.com/en-us/aspnet/core/web-api/?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
> - 控制器构造器依赖注入：Microsoft Learn [控制器中的依赖注入](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/dependency-injection?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
> - `CreatedAtAction` 与带状态码的控制器结果：Microsoft Learn [控制器操作结果](https://learn.microsoft.com/en-us/aspnet/core/web-api/action-return-types?view=aspnetcore-10.0)，ASP.NET Core 10.0，2026-11-06。
