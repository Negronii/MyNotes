# 怎样让调用方可靠地判断 API 的成功、失败和变化？

前几章讲了一次请求怎样被识别和授权；本章讲 API 怎样把结果交代给调用方，让程序而不是人来判断成功和失败。内容依次是：契约约定了哪几层，错误正文怎样设计，几种错误同时成立时先报哪个，常见失败映射到哪个状态码，OpenAPI 描述怎样与运行时行为核对，以及 API 改版时什么算兼容。

## 契约约定什么

HTTP 提供通用的方法和状态语义（见[第一章](http-semantics-and-transport.md)）；API 契约在其上约定领域输入、表示结构、错误类别、分页规则和兼容政策。契约有几层载体：说明文档、代码里的类型、OpenAPI 描述和运行中的实现。它们彼此独立，写出 schema（结构模式）不证明部署的行为符合它，后文专门讲怎样核对。

沿用[主线四的报表读取案例](http-semantics-and-transport.md#案例：账户报表服务里的一次读取)。API 为报表定义了两种明确的 JSON 形状：

- **详情表示**：`GET /v1/accounts/acct-17/reports/42` 返回，带强 ETag `"report-42-v7"`，必有 `id`、`title`、`status`、`delivery`；可选的 `note` 没有值时省略，不输出 JSON `null`。

  ~~~json
  {"id":42,"title":"Service health","status":"ready","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
  ~~~

- **摘要表示**：集合列表里的每一项，只有 `id`、`title`、`status`。列表怎样分页、怎样给出结束信号，见[键集分页章](../data/keyset-pagination-and-snapshots.md)。

为演示创建类请求的错误，本章再加一个端点：`POST /v1/accounts/acct-17/views` 为报表保存一个命名视图，正文是 `{"name":"Weekly","reportId":42}`；名称原样不超过 60 个字符、去掉首尾空白后不能为空，同一账户内不区分大小写地唯一。成功时回 `201 Created` 和 `Location`。创建资源的 `201` 与受理作业的 `202` 怎样区分，见[耗时任务怎样被持久受理？](durable-job-acceptance-and-outbox.md)。

## 错误正文：Problem Details

错误正文的机器可判定契约在全领域以这里为准。API 用 RFC 9457 的 Problem Details，媒体类型为 `application/problem+json`：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api.reports.example.test/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

- **程序依赖 `type`。** 调用方按稳定的 `type` URI 或约定的扩展错误码分支，不解析给人看的 `title` 和 `detail`。改 `type` 等于改契约。
- **`status` 与 HTTP 状态一致。** 正文若带 `status`，它必须等于实际的 HTTP 状态码。
- **扩展字段放机器需要的细节。** 例如校验失败时用 `errors` 列出字段路径和稳定错误代码。
- **不泄漏内部信息。** 不回显秘密、异常栈或 SQL 文本。

## 多个错误同时成立时先报哪个

一个请求可能同时犯好几个错：没登录、对象不可见、媒体类型不对、正文写坏了、版本标签过时。返回哪一个本身就是契约，全领域只在这里规定。原则是：不处理正文就能确定的失败先报，而且不能让后面的错误泄漏前面要隐藏的信息。

1. **认证（`401`）。** 没有有效凭据，先回 `401`。所以未认证的请求即使报表 ID 不是整数，也回 `401` 而不是 `422`。
2. **对象可见性（隐藏式 `404`）。** 主体看不到所选账户或对象时回 `404`。隐藏对象即使带着过时的 `If-Match`，也回 `404`，不能用 `412` 暗示对象存在（隐藏规则见[授权章](per-request-authorization.md#隐藏式%20404%20还是%20403)）。
3. **不支持的媒体类型（`415`）。** 已认证且对象可见时，`Content-Type` 不受支持在读取正文前就能确定，所以先于正文解析错误，也先于 `412` 和 `428`。
4. **正文无法解析（`400`）。**
5. **其余由端点定义。** 字段级校验（`422`）、前置条件（`412`/`428`）、状态冲突（`409`）之间的顺序，由各端点自己规定。

会受理异步作业的端点还有准入拒绝（`429` 速率令牌不足、`503` 等待槽已满，见[容量章](capacity-admission-and-backpressure.md#准入、背压与拒绝怎样对应到响应？)）。本 API 把它们排在上面各项和幂等裁决之后：请求必须先是一个合法、可见、而且是**新**的意图，才去竞争额度，所以同键同指纹的重放即使赶上额度耗尽，也照常返回原 job 的当前状态。令牌和等待槽同时不足时先报 `429`。

RFC 9110 的条件请求优先级只约束第 1–3 步这类不需要处理正文就能确定的失败，并不要求所有字段级领域校验都排在 `If-Match` 之前。数据库层的并发不变量，仍由原子写入负责。

## 常见失败映射到哪个状态码

下表是本 API 的映射政策。它不是所有服务都必须采用的唯一一张表，但一旦公开，就是调用方可以依赖的契约：

| 条件 | 结果 | 约定与链接 |
| --- | --- | --- |
| 报表存在，身份与资源权限都通过 | `200` + 详情表示 | — |
| 缺少有效凭据，即使 ID 不是整数 | `401` | 带 `WWW-Authenticate`，例如 `Bearer realm="reports"` |
| 对象不存在，或主体无权看到；即使带陈旧 `If-Match` | `404` | 两种情况 `type` 与详情相同；与 `403` 的取舍见[授权章](per-request-authorization.md#隐藏式%20404%20还是%20403) |
| 对象可见，但缺少某个动作的权限 | `403` | 同上 |
| JSON 语法无效，例如正文 `{` | `400` | 说明内容无法解析 |
| `Content-Type` 不受端点支持 | `415` | 补丁类端点用 `Accept-Patch` 公布接受的格式；创建视图只收 `application/json` |
| 能解析，但字段值、路径 ID 或范围不合契约 | `422` | 指出字段路径和错误代码；本 API 把非整数路径 ID 也归为 `422` |
| 与当前状态冲突，例如视图重名 | `409` | 告诉调用方怎样刷新或解决冲突 |
| `If-Match` 不匹配或是弱标签 | `412` | 见[条件写章](conditional-updates-and-etags.md#412%20和%20428%20各说明什么) |
| `If-Match` 语法错误，或端点不接受的 `*` 与标签列表 | `400` | 同上 |
| 缺少端点要求的 `If-Match` | `428` | 同上；`428` 响应不得被缓存 |
| 超过调用额度 | `429` | 可附 `Retry-After`；不得被缓存；准入与额度见[容量章](capacity-admission-and-backpressure.md) |
| 暂时不能处理 | `503` | 同上 |
| 未预期的服务端错误 | `500` | 只给稳定的机器类别；写入结果未知时按幂等契约查询，见[未知结果章](deadlines-retries-and-unknown-outcomes.md) |

`422 Unprocessable Content` 的含义是“内容语法能理解，但其中的指令无法处理”。本 API 据此把畸形 JSON 归为 `400`，把能解析但字段不合规的正文归为 `422`；把非整数路径 ID 也映射为 `422`，是本 API 额外的约定。

## OpenAPI 描述与运行时是否一致

OpenAPI 记录每个操作的路径、参数、请求和响应的媒体类型、成功与错误响应、响应头以及 schema，人和工具都据此调用服务。框架可以从请求和响应模型生成结构；自定义的异常处理器产生的错误，也要在对应操作里声明出来，否则文档里就缺了这些响应。

核对时按操作逐项看：真实路径、每个状态码、请求媒体类型、创建响应的 `Location`、Problem 的 `type`，以及可选字段是否允许缺省或 `null`（例如分页结束时为 `null` 的游标字段，要声明成必返回且允许 `null`）。schema 能表达的约束要与运行时一致：只含空格的视图名，既应被 `CreateView` 的 JSON Schema 拒绝，也应在运行时返回 `422`。媒体类型检查、认证、授权这些运行边界，schema 根本表达不了，要对照处理器单独核验。

跨实现的语义差异也会让“文档说一套、运行做一套”。视图名的 schema 用 `pattern: "\S"`（至少一个非空白字符），运行时用 Python 的 `str.strip()` 判空。两边的“空白”集合不同：

| 输入字符 | ECMAScript 正则 `\S` | Python `str.strip()` 后 | 结果 |
| --- | --- | --- | --- |
| `U+0085`（NEL） | 匹配，schema 通过 | 被去掉，变成空串，运行时拒绝 | 不一致 |
| `U+FEFF`（BOM） | 不匹配，schema 拒绝 | 不被去掉，运行时通过 | 相反方向不一致 |

普通空格和长度样例都通过，不等于 schema 与运行时对所有输入都一致。

## 实例：用 FastAPI 复现契约

下面的复现用与正文相同的数据：账户 `acct-17` 的报表 42（`Service health`，ETag `"report-42-v7"`），`acct-29` 的 `user-29`，以及不存在的报表 43。它演示三件事：

- **检查顺序。** 自定义 `APIRoute.get_route_handler()` 在 FastAPI 解析参数和正文之前，依次做认证（`401`）、账户可见性（隐藏式 `404`）和媒体类型（`415`，比较时忽略大小写和参数）。因此未认证请求带非整数 ID 得到 `401`，跨账户请求带错误媒体类型得到 `404`，媒体类型错误的坏正文得到 `415` 而不是 `400`。
- **错误映射。** `RequestValidationError` 中类型为 `json_invalid` 的映射为 `400`，其余映射为 `422` 并列出字段路径；视图名的前置校验器先检查原始长度，再去首尾空白。
- **文档核对。** 用 `TestClient` 断言状态码与正文，再断言 `app.openapi()` 为每个操作声明了对应的错误响应、`Location` 头和请求媒体类型。

复现不实现真实的令牌验证（用固定的 token 表代替）、条件写或持久存储。

> [!example]- FastAPI 契约复现（FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1，生成 OpenAPI 3.1.0）
>
> ~~~python
> from typing import Any, Literal
>
> from fastapi import APIRouter, FastAPI, Request, Response
> from fastapi.exceptions import RequestValidationError
> from fastapi.responses import JSONResponse
> from fastapi.routing import APIRoute
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api.reports.example.test/problems/"
> TOKENS = {"token-user-17": "user-17", "token-user-29": "user-29"}   # 代替真实令牌验证
> MEMBERS = {("acct-17", "user-17"), ("acct-29", "user-29")}
>
>
> class Delivery(BaseModel):
>     channel: Literal["email", "download"]
>     recipients: list[str] | None = None
>
>
> class ReportDetail(BaseModel):
>     id: int
>     title: str
>     status: str
>     delivery: Delivery
>     note: str | None = None          # 无值时省略，不输出 null
>
>
> class CreateView(BaseModel):
>     name: str = Field(min_length=1, max_length=60, pattern=r"\S")
>     reportId: int
>
>     @field_validator("name", mode="before")
>     @classmethod
>     def normalize_name(cls, value: Any) -> Any:
>         if isinstance(value, str):
>             if len(value) > 60:      # 先查原始长度，再去首尾空白
>                 raise ValueError("name must be at most 60 characters before trimming")
>             if not value.strip():
>                 raise ValueError("name must contain a non-whitespace character")
>             return value.strip()
>         return value
>
>
> class View(BaseModel):
>     id: int
>     name: str
>     reportId: int
>
>
> class Problem(BaseModel):
>     type: str
>     title: str
>     status: int
>     detail: str
>     errors: list[dict[str, str]] | None = None
>
>
> class ApiProblem(Exception):
>     def __init__(self, status, kind, title, detail, headers=None):
>         self.status, self.kind, self.title, self.detail = status, kind, title, detail
>         self.headers = headers
>
>
> def problem(status, kind, title, detail, headers=None, **extensions):
>     return JSONResponse(
>         status_code=status, media_type="application/problem+json", headers=headers,
>         content={"type": PROBLEM_BASE + kind, "title": title, "status": status,
>                  "detail": detail, **extensions},
>     )
>
>
> NOT_VISIBLE = ("not-found", "Report not found", "No report is visible under this identifier.")
>
>
> class ContractRoute(APIRoute):
>     """在 FastAPI 解析参数和正文之前，按契约顺序做认证、可见性与媒体类型检查。"""
>
>     def get_route_handler(self):
>         handler = super().get_route_handler()
>
>         async def ordered_checks(request: Request):
>             auth = request.headers.get("authorization", "")
>             subject = TOKENS.get(auth.removeprefix("Bearer ")) if auth.startswith("Bearer ") else None
>             if subject is None:
>                 raise ApiProblem(401, "unauthenticated", "Authentication required",
>                                  "Send a valid bearer token.",
>                                  headers={"WWW-Authenticate": 'Bearer realm="reports"'})
>             if (request.path_params.get("account_id"), subject) not in MEMBERS:
>                 raise ApiProblem(404, *NOT_VISIBLE)
>             if request.method == "POST":
>                 media = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
>                 if media != "application/json":
>                     raise ApiProblem(415, "unsupported-media-type", "Unsupported media type",
>                                      "Send this resource using application/json.")
>             return await handler(request)
>
>         return ordered_checks
>
>
> def doc(description):
>     return {"description": description,
>             "content": {"application/problem+json": {"schema": Problem.model_json_schema()}}}
>
>
> reports = {("acct-17", 42): ReportDetail(
>     id=42, title="Service health", status="ready",
>     delivery=Delivery(channel="email", recipients=["reader@example.test"]), note="Draft")}
> views: dict[tuple[str, int], View] = {}
> next_view_id = 1
>
> app = FastAPI()
> router = APIRouter(prefix="/v1/accounts/{account_id}", route_class=ContractRoute)
>
>
> @app.exception_handler(ApiProblem)
> async def on_api_problem(request: Request, exc: ApiProblem):
>     return problem(exc.status, exc.kind, exc.title, exc.detail, headers=exc.headers)
>
>
> @app.exception_handler(RequestValidationError)
> async def on_validation(request: Request, exc: RequestValidationError):
>     errors = exc.errors()
>     if any(e.get("type") == "json_invalid" for e in errors):
>         return problem(400, "malformed-json", "Malformed JSON", "Send a syntactically valid JSON body.")
>     fields = [{"field": ".".join(str(p) for p in e["loc"]), "code": "invalid_value"} for e in errors]
>     return problem(422, "validation", "Request validation failed",
>                    "Correct the fields listed in errors and resubmit.", errors=fields)
>
>
> @router.get("/reports/{report_id}", response_model=ReportDetail, response_model_exclude_none=True,
>             responses={401: doc("Missing or invalid credentials"), 404: doc("Report not visible"),
>                        422: doc("Report ID is not an integer")})
> async def get_report(account_id: str, report_id: int, response: Response):
>     report = reports.get((account_id, report_id))
>     if report is None:
>         raise ApiProblem(404, *NOT_VISIBLE)
>     response.headers["ETag"] = f'"report-{report_id}-v7"'
>     return report
>
>
> @router.post("/views", status_code=201, response_model=View,
>              responses={201: {"description": "View created",
>                               "headers": {"Location": {"schema": {"type": "string"}}}},
>                         400: doc("Malformed JSON body"), 401: doc("Missing or invalid credentials"),
>                         404: doc("Account or report not visible"), 409: doc("View name already exists"),
>                         415: doc("Content-Type must be application/json"),
>                         422: doc("Invalid view fields")})
> async def create_view(account_id: str, payload: CreateView, response: Response):
>     global next_view_id
>     if (account_id, payload.reportId) not in reports:
>         raise ApiProblem(404, *NOT_VISIBLE)
>     if any(a == account_id and v.name.casefold() == payload.name.casefold() for (a, _), v in views.items()):
>         raise ApiProblem(409, "duplicate-name", "View name already exists", "Choose another name.")
>     view = View(id=next_view_id, name=payload.name, reportId=payload.reportId)
>     views[(account_id, view.id)] = view
>     response.headers["Location"] = f"/v1/accounts/{account_id}/views/{view.id}"
>     next_view_id += 1
>     return view
>
>
> app.include_router(router)
>
>
> def check():
>     c = TestClient(app)
>     u17 = {"Authorization": "Bearer token-user-17"}
>     u29 = {"Authorization": "Bearer token-user-29"}
>     base = "/v1/accounts/acct-17"
>
>     ok = c.get(f"{base}/reports/42", headers=u17)
>     assert ok.status_code == 200 and ok.headers["etag"] == '"report-42-v7"'
>     assert ok.json()["title"] == "Service health" and ok.json()["note"] == "Draft"
>
>     missing = c.get(f"{base}/reports/43", headers=u17)
>     hidden = c.get(f"{base}/reports/42", headers=u29)
>     assert missing.status_code == hidden.status_code == 404
>     assert missing.json() == hidden.json()                     # 不存在与跨账户不可区分
>     assert missing.headers["content-type"].startswith("application/problem+json")
>
>     anon = c.get(f"{base}/reports/not-an-integer")
>     assert anon.status_code == 401 and anon.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert c.get(f"{base}/reports/not-an-integer", headers=u29).status_code == 404
>     assert c.get(f"{base}/reports/not-an-integer", headers=u17).status_code == 422
>
>     post = lambda body, media="application/json", h=u17: c.post(
>         f"{base}/views", content=body, headers={**h, "Content-Type": media})
>     assert post("{", "text/plain").status_code == 415          # 415 先于 400
>     assert post("{", "text/plain", u29).status_code == 404      # 可见性先于 415
>     assert post("{").status_code == 400
>     assert post('{"name":"   ","reportId":42}').status_code == 422
>     assert post('{"name":"' + " " * 61 + 'x","reportId":42}').status_code == 422
>     created = post('{"name":" Weekly ","reportId":42}', "Application/JSON; charset=UTF-8")
>     assert created.status_code == 201 and created.json() == {"id": 1, "name": "Weekly", "reportId": 42}
>     assert created.headers["location"] == "/v1/accounts/acct-17/views/1"
>     assert post('{"name":"weekly","reportId":42}').json()["type"] == PROBLEM_BASE + "duplicate-name"
>     assert post('{"name":"Other","reportId":43}').status_code == 404
>
>     spec = app.openapi()
>     get_op = spec["paths"]["/v1/accounts/{account_id}/reports/{report_id}"]["get"]
>     post_op = spec["paths"]["/v1/accounts/{account_id}/views"]["post"]
>     assert {"401", "404", "422"} <= set(get_op["responses"]) and "409" not in get_op["responses"]
>     assert {"400", "401", "404", "409", "415", "422"} <= set(post_op["responses"])
>     assert "Location" in post_op["responses"]["201"]["headers"]
>     assert set(post_op["requestBody"]["content"]) == {"application/json"}
>     name = spec["components"]["schemas"]["CreateView"]["properties"]["name"]
>     assert (name["minLength"], name["maxLength"], name["pattern"]) == (1, 60, r"\S")
>     print("GET 42 -> 200 + ETag; 43 and cross-account -> identical 404; no token -> 401 before 422")
>     print("POST views: 404 > 415 > 400 > 422; 201 + Location; duplicate -> 409")
>     print("OpenAPI", spec["openapi"], "declares per-operation errors, Location and media type")
>
>
> check()
> ~~~
>
> 运行输出：
>
> ~~~text
> GET 42 -> 200 + ETag; 43 and cross-account -> identical 404; no token -> 401 before 422
> POST views: 404 > 415 > 400 > 422; 201 + Location; duplicate -> 409
> OpenAPI 3.1.0 declares per-operation errors, Location and media type
> ~~~

## 返回的链接能替客户端做什么

REST 的 HATEOAS（Hypermedia as the Engine of Application State，超媒体作为应用状态引擎）约束要求客户端从服务端的表示中发现当前可用的状态转移，而不是凭报表 ID 自己拼出每个 URL。API 可以按自己的契约在表示里返回链接：

~~~json
{
  "id": 42,
  "links": [
    { "rel": "self", "href": "/v1/accounts/acct-17/reports/42" },
    { "rel": "export", "href": "/v1/accounts/acct-17/reports" }
  ]
}
~~~

这个 `links` 数组是本 API 自定的结构，不是通用的 HTTP 链接编码。链接能否被程序使用，取决于几个前提：

- **关系名要有定义。** 只有媒体类型或 API 契约规定了 `self`、`export` 的含义，客户端才能据此操作；给任意 JSON 加一个 `href` 字段，不会自动带来这些语义。
- **只有安全导航适合直接跟随。** `self` 可以渲染成普通链接。`export` 只给了 `href`，没说用什么方法、带什么正文；有副作用的操作要按契约声明的 affordance（操作描述）发送，不能伪装成 `<a>`。
- **异源链接不盲目跟随。** 只有契约允许时才跟随异源地址，也不能把当前站点的认证信息附到异源请求上。
- **链接不配置前端路由。** 单页应用可以用路由接管内部导航，但路由按自己的加载和历史规则工作，服务端返回链接不会自动配置它。

~~~tsx
type ApiLink = { rel: string; href: string };
type Report = { id: number; links: ApiLink[] };

function ReportDetailsLink({ report }: { report: Report }) {
  const self = report.links.find(link => link.rel === "self");
  return self ? <a href={self.href}>查看报表详情</a> : null;
}
~~~

## 兼容演进需要显式政策

API 改版时，“兼容”取决于调用方怎样解析，必须写成政策：

- **通常兼容**：新增可选的响应字段，对忽略未知字段的客户端无害；但严格解码器或生成的客户端代码可能拒绝它。
- **可能破坏调用方**：删除字段，改变字段类型或含义，把可选请求字段改为必填，改变 Problem `type`，调整分页结束信号。

做法是公开兼容政策，检查重要调用方，为不兼容的变更安排版本切换或迁移窗口。没有唯一强制的版本化方案。数据库结构变更与新旧版本并存时的 expand/contract 做法，见[新版本怎样逐步放量，出问题时能撤回什么？](../practice/canary-rollout-and-rollback.md)。

## 下一步：两个人同时改报表 42 会怎样？

本章交出的是调用方可以依赖的契约：成功与失败各有稳定的状态码和 Problem `type`；几种错误同时成立时按认证、可见性、媒体类型、正文解析的顺序报出，前面的隐藏不被后面的错误泄漏；OpenAPI 描述要与运行时逐项核对；改版遵循公开的兼容政策。

映射表里还有 `412` 和 `428` 没展开。它们来自写请求：两位编辑者都读到了 v7，谁的修改该生效，后到者又该得到什么？见[两个客户端同时修改同一资源时，API 怎样防止互相覆盖？](conditional-updates-and-etags.md)

> [!info]- 来源
> - Problem Details 的 `type`、`title`、`status`、`detail` 与扩展字段（“错误正文”）：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，2023-07，§3–§4；核对于 2026-11-12。
> - `400`、`401` 质询、`403`、`404`、`409`、`415`、`422` 的语义，条件请求的评估优先级（“多个错误同时成立时先报哪个”“常见失败映射到哪个状态码”）：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§11.6.1、§13.2.1–§13.2.2、§15.5；`428` 与 `429` 及二者不得缓存：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，2012-04，§3–§4；核对于 2026-11-12。
> - 操作、参数、媒体类型、响应与 schema 的接口描述（“OpenAPI 描述与运行时是否一致”）：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-12。复现环境生成的是 OpenAPI 3.1.0，以 `app.openapi()['openapi']` 为准。
> - ECMAScript 与 Python 空白集合的差异：本机 Node v26.13.1 与 Python 3.11.13 实测 `U+0085`、`U+FEFF` 两个字符，核对于 2026-11-26。
> - FastAPI 请求模型、响应模型、自定义错误处理与 `APIRoute.get_route_handler()`（“实例”）：[Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Custom Request and APIRoute](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)；Pydantic 2.11 的前置校验器与 JSON Schema：[Validators](https://docs.pydantic.dev/2.11/concepts/validators/)、[JSON Schema](https://docs.pydantic.dev/2.11/concepts/json_schema/)；官方文档核对于 2026-11-12。复现代码在 FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1 上运行通过。
> - 超媒体约束（“返回的链接能替客户端做什么”）：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000，§5.1.5。
