# 如何设计可预期的 HTTP API 契约？

API 契约说明调用方怎样构造请求、怎样识别成功和失败、怎样继续读取集合。HTTP 提供通用方法和状态语义；API 定义领域输入、返回结构、错误类别、分页规则与兼容政策。文档、类型注解、OpenAPI 描述和运行中的实现是不同层：写出 schema（结构模式）不证明已部署行为符合它。

**案例：** 浏览器请求 `GET /api/reports/42`。报表存在且当前主体获准读取时，API 返回稳定 JSON；编号格式错误、报表不存在、认证缺失或访问被拒，各有调用方能识别的结果。列表按 ID 排序并显式给出下一页游标。

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json, application/problem+json
~~~

一个合法的成功表示是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{"id":42,"title":"Service health","status":"ready"}
~~~

路径里的 `42` 是 API 的资源标识，不是访问授权。边界先解析和校验输入，再由服务确认当前身份、租户和对象权限；之后才读取资源。资源归属见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

## 错误契约怎样保留机器可判定的含义？

API 可以用 RFC 9457 Problem Details 表示错误，媒体类型为 `application/problem+json`。例如 ID 不存在或按隐私政策不可见时返回统一错误：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api.example/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

客户端可依赖稳定的 `type` 或扩展错误码，而不应解析供人阅读的 `title`、`detail`。若正文含 `status`，它须与实际 HTTP 状态相同。不要回显秘密、内部异常栈或 SQL 文本。

| 条件 | 本例的结果 | 补充约定 |
| --- | --- | --- |
| 报表 42 存在、身份和资源权限都通过 | 200 + JSON | 定义成功表示中的稳定字段 |
| 缺少有效凭据 | 401 + Problem Details | 发出 401 时提供适用的 `WWW-Authenticate` challenge；例如 Bearer API 返回 `Bearer realm="reports"` |
| 已认证但无权访问 | 403，或按隐藏政策返回与不存在相同的 404 | 隐藏策略下错误详情不能泄漏对象存在性 |
| JSON 语法无效，例如正文 `{` | 400 + Problem Details | 指明内容无法解析 |
| 语法有效但字段、路径参数或范围不符合契约 | 422 + Problem Details | 指出字段路径和稳定错误代码 |
| 与当前状态冲突，例如重复标题 | 409 + Problem Details | 告诉调用方怎样刷新或解决冲突 |
| 超过适用调用额度 | 429 + Problem Details | 定义额度作用域和可重试时机 |
| 报表 999 不存在或被隐藏 | 404 + Problem Details | 与成功表示结构不同 |

这是本 API 的映射政策，不是所有服务都必须采用的唯一表。`422 Unprocessable Content` 表示内容语法可理解但指令不能处理，因此本例把畸形 JSON 归为 400，把结构有效但字段不合规归为 422。认证/授权、结构校验和数据库并发不变量分别由不同边界负责。

## 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 可创建一条报表资源记录，返回 `201 Created` 和 `Location: /api/reports/44`。如果新资源的 `status` 是 `queued`，201 表示资源记录已经建立，不表示报表成品已生成。若请求创建的是独立长作业而不是资源记录，API 可以返回 `202 Accepted` 与稳定的作业状态 URL；202 表示受理处理，不表示成功完成。客户端在连接断开后查状态资源，而不是从原响应推断完成。账户报表的持久 job、outbox 和队列确认见[怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Service health","status":"ready"}],"next_cursor":"opaque-token-A"}
~~~

客户端原样传回不透明游标：

~~~http
GET /api/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":43,"title":"Usage summary","status":"queued"}],"next_cursor":null}
~~~

第一页的 `[41, 42]` 续到 ID 42 之后，第二页的 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据。游标不应暴露可篡改的数据库偏移量；生产集合可把游标绑定筛选条件、排序、授权范围和过期时间，并按 `(created_at, id)` 之类的稳定复合键续读。每页重新授权。并列时间戳时游标要同时保存两个排序键，数据变化时还要说明读者看到移动集合还是固定快照。

> [!example] 读完三条报表的分页回放
> 排序为 ID 升序、页大小为 2：第一批是 `[41, 42]`，游标代表“从 42 之后继续”；第二批是 `[43]`，返回 `next_cursor: null` 后停止。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。示例游标是占位显示；运行代码会生成不可预测的不透明 token。

## OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、媒体类型、成功与错误响应及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。只有运行时错误和 OpenAPI 都匹配，客户端才不会按一份服务实际不返回的契约生成分支。检查时要按操作核对真实路径、状态码、媒体类型、Problem `type`、分页字段是否必填以及 schema 是否允许 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，与本章请求路径一致。它用三条合成报表演示 200、404、字段验证、畸形 JSON、冲突、分页和 OpenAPI。为集中讲契约，它没有实现身份认证、租户授权或数据库并发唯一性；它不是可直接部署的安全报表服务。正常请求和失败的输入输出已在正文展示，无需运行这段代码才能理解契约。

> [!example]- 可运行的 FastAPI 契约复现
> 运行环境已核验：FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1；本环境的 `app.openapi()` 生成 OpenAPI 3.1.0。OpenAPI 文档版本以运行时字段为准。
>
> ~~~python
> import secrets
> from typing import Any
>
> from fastapi import APIRouter, FastAPI, Query, Request, Response
> from fastapi.exceptions import RequestValidationError
> from fastapi.responses import JSONResponse
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api.example/problems/"
>
>
> class CreateReport(BaseModel):
>     title: str = Field(min_length=1, max_length=60)
>
>     @field_validator("title", mode="before")
>     @classmethod
>     def normalize_title(cls, value: Any) -> Any:
>         if isinstance(value, str):
>             if len(value) > 60:  # 上限检查原始输入，再去除首尾空格
>                 raise ValueError("title must be at most 60 characters before trimming")
>             if not value.strip():
>                 raise ValueError("title must contain a non-whitespace character")
>             return value.strip()
>         return value
>
>
> class Report(BaseModel):
>     id: int
>     title: str
>     status: str
>
>
> class Page(BaseModel):
>     items: list[Report]
>     next_cursor: str | None  # required, but null on the last page
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
>     def __init__(self, status: int, kind: str, title: str, detail: str):
>         self.status, self.kind, self.title, self.detail = status, kind, title, detail
>
>
> def problem_content(description: str):
>     return {
>         "description": description,
>         "content": {
>             "application/problem+json": {"schema": Problem.model_json_schema()}
>         },
>     }
>
>
> LIST_ERRORS = {
>     400: problem_content("Unknown cursor"),
>     422: problem_content("Invalid query parameter"),
> }
> READ_ERRORS = {
>     404: problem_content("Report does not exist"),
>     422: problem_content("Report ID is not an integer"),
> }
> CREATE_ERRORS = {
>     400: problem_content("Malformed JSON body"),
>     409: problem_content("Report title already exists"),
>     422: problem_content("Invalid title fields"),
> }
>
> reports = {
>     41: Report(id=41, title="Monthly overview", status="ready"),
>     42: Report(id=42, title="Service health", status="ready"),
>     43: Report(id=43, title="Usage summary", status="queued"),
> }
> cursor_offsets: dict[str, int] = {}
> next_id = 44
> app = FastAPI()
> router = APIRouter(prefix="/api")
>
>
> def problem_response(status, kind, title, detail, **extensions):
>     return JSONResponse(
>         status_code=status,
>         media_type="application/problem+json",
>         content={
>             "type": PROBLEM_BASE + kind,
>             "title": title,
>             "status": status,
>             "detail": detail,
>             **extensions,
>         },
>     )
>
>
> @app.exception_handler(ApiProblem)
> async def api_problem_handler(request: Request, exc: ApiProblem):
>     return problem_response(exc.status, exc.kind, exc.title, exc.detail)
>
>
> @app.exception_handler(RequestValidationError)
> async def validation_handler(request: Request, exc: RequestValidationError):
>     errors = exc.errors()
>     if any(error.get("type") == "json_invalid" for error in errors):
>         return problem_response(
>             400, "malformed-json", "Malformed JSON", "Send a syntactically valid JSON body."
>         )
>     fields = [
>         {"field": ".".join(str(part) for part in error["loc"]), "code": "invalid_value"}
>         for error in errors
>     ]
>     return problem_response(
>         422, "validation", "Request validation failed",
>         "Correct the fields listed in errors and resubmit.", errors=fields,
>     )
>
>
> @router.get("/reports", response_model=Page, responses=LIST_ERRORS)
> async def list_reports(
>     limit: int = Query(default=2, ge=1, le=100), cursor: str | None = None
> ):
>     if cursor is None:
>         offset = 0
>     elif cursor in cursor_offsets:
>         offset = cursor_offsets[cursor]
>     else:
>         raise ApiProblem(400, "invalid-cursor", "Invalid cursor", "Start a new listing.")
>
>     ordered = [reports[key] for key in sorted(reports)]
>     page = ordered[offset : offset + limit]
>     next_cursor = None
>     if offset + len(page) < len(ordered):
>         next_cursor = secrets.token_urlsafe(12)
>         cursor_offsets[next_cursor] = offset + len(page)
>     return Page(items=page, next_cursor=next_cursor)
>
>
> @router.get("/reports/{report_id}", response_model=Report, responses=READ_ERRORS)
> async def get_report(report_id: int):
>     if report_id not in reports:
>         raise ApiProblem(
>             404, "not-found", "Report not found",
>             "No report is visible under this identifier.",
>         )
>     return reports[report_id]
>
>
> @router.post(
>     "/reports", status_code=201, response_model=Report, responses=CREATE_ERRORS
> )
> async def create_report(payload: CreateReport, response: Response):
>     global next_id
>     title = payload.title
>     if any(report.title.casefold() == title.casefold() for report in reports.values()):
>         raise ApiProblem(409, "duplicate-title", "Title already exists", "Choose another title.")
>     report = Report(id=next_id, title=title, status="queued")
>     reports[next_id] = report
>     response.headers["Location"] = f"/api/reports/{next_id}"
>     next_id += 1
>     return report
>
>
> app.include_router(router)
>
>
> def check():
>     client = TestClient(app)
>     good = client.get("/api/reports/42", headers={"Accept": "application/json"})
>     assert good.status_code == 200
>     assert good.json() == {"id": 42, "title": "Service health", "status": "ready"}
>
>     missing = client.get("/api/reports/999")
>     assert missing.status_code == 404
>     assert missing.headers["content-type"].startswith("application/problem+json")
>     assert missing.json()["type"] == PROBLEM_BASE + "not-found"
>     invalid_id = client.get("/api/reports/not-an-integer")
>     assert invalid_id.status_code == 422
>
>     first = client.get("/api/reports?limit=2")
>     assert [row["id"] for row in first.json()["items"]] == [41, 42]
>     assert first.json()["next_cursor"] is not None
>     cursor = first.json()["next_cursor"]
>     second = client.get("/api/reports", params={"limit": 2, "cursor": cursor})
>     assert [row["id"] for row in second.json()["items"]] == [43]
>     assert "next_cursor" in second.json() and second.json()["next_cursor"] is None
>     assert client.get("/api/reports?limit=101").status_code == 422
>     assert client.get("/api/reports?cursor=unknown-token").status_code == 400
>
>     malformed = client.post(
>         "/api/reports", content="{", headers={"Content-Type": "application/json"}
>     )
>     assert malformed.status_code == 400
>     assert malformed.json()["type"] == PROBLEM_BASE + "malformed-json"
>     assert malformed.headers["content-type"].startswith("application/problem+json")
>     whitespace = client.post("/api/reports", json={"title": "   "})
>     assert whitespace.status_code == 422
>     overlong_raw = client.post("/api/reports", json={"title": " " * 61 + "Padded"})
>     assert overlong_raw.status_code == 422
>
>     created = client.post("/api/reports", json={"title": " Weekly detail "})
>     assert created.status_code == 201 and created.json()["id"] == 44
>     assert created.json()["title"] == "Weekly detail"
>     assert created.headers["location"] == "/api/reports/44"
>     duplicate = client.post("/api/reports", json={"title": "weekly detail"})
>     assert duplicate.status_code == 409
>     assert duplicate.json()["type"] == PROBLEM_BASE + "duplicate-title"
>
>     spec = app.openapi()
>     paths = spec["paths"]
>     assert "/api/reports/42" not in paths  # path template is used in OpenAPI
>     get_one = paths["/api/reports/{report_id}"]["get"]
>     get_list = paths["/api/reports"]["get"]
>     post = paths["/api/reports"]["post"]
>     assert "404" in get_one["responses"] and "422" in get_one["responses"]
>     assert "400" not in get_one["responses"] and "409" not in get_one["responses"]
>     assert "400" in get_list["responses"] and "422" in get_list["responses"]
>     assert "404" not in get_list["responses"] and "409" not in get_list["responses"]
>     assert {"400", "409", "422"} <= set(post["responses"])
>     assert "404" not in post["responses"]
>     page_schema = spec["components"]["schemas"]["Page"]
>     assert "next_cursor" in page_schema["required"]
>     assert page_schema["properties"]["next_cursor"]["anyOf"]
>     print("GET /api/reports/42 -> 200; missing -> 404; invalid ID -> 422")
>     print("malformed JSON -> 400; blank/overlong title -> 422; duplicate -> 409")
>     print("page [41, 42] -> [43]; required next_cursor=null ends the listing")
>     print("OpenAPI routes and per-operation responses match the demonstrated paths")
>
>
> check()
> ~~~
>
> This code uses an in-memory offset map to teach the cursor boundary; the token expires on process restart and is not bound to filters, sort order or identity. A production collection can use an index-backed keyset cursor and reauthorize each page. The page contents are computed from these three records; they are not performance measurements.

## 兼容演进需要显式规则

新增可选响应字段通常可兼容会忽略未知字段的客户端，但严格解码器或生成代码可能拒绝它。删除字段、改变字段类型或含义、把可选请求字段改为必填、改变 Problem `type`、调整分页结束标志，都可能破坏调用方。应公开兼容政策，检查重要调用方，并为不兼容变更安排版本切换或迁移窗口；不存在唯一强制的版本化方案。

**接下来：** 本章描述调用方可观察的接口结构；HTTP 方法、缓存与状态码的通用语义见[浏览器请求如何到达 HTTP 响应？](../networking/http-protocols-and-websockets.md)，副作用未知后的结果查询和重试见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-06。
> - 400、401 challenge、403、404、409、422、429、201 与 202 的 HTTP 语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§15，2022-06；核对于 2026-11-06。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-06。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 页大小、请求间参数一致、不透明 page token 和结束信号：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-06。
> - FastAPI 请求模型、响应模型和自定义错误处理：[FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)，官方文档核对于 2026-11-06；错误类型映射已在列明版本的本地运行环境核对。
