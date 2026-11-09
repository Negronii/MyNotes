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
ETag: "report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
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

## 如何用条件 PATCH 防止覆盖别人更新？

客户端先读取报表 42，服务为当前表示发出强 ETag（实体标签）`"report-42-v7"`，客户端保存它和基线表示：

~~~http
GET /api/reports/42 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

之后用户把交付方式切为下载，并删除可选备注。此资源只接受 JSON Merge Patch（JSON 合并补丁），所以请求声明媒体类型 `application/merge-patch+json`，并带上刚读到的强 ETag：

~~~http
PATCH /api/reports/42 HTTP/1.1
Host: reports.example
Content-Type: application/merge-patch+json
If-Match: "report-42-v7"

{"delivery":{"channel":"download"},"note":null}
~~~

Merge Patch 的对象成员按名称递归合并：未出现的成员保持，`null` 表示删除成员，数组整体替换。应用补丁后的中间表示仍有旧 `recipients`，因为该成员在补丁里被省略；本合成 API 另规定下载模式不保存收件人字段，业务规范化随后移除它，并验证最终表示。若 `channel` 是 `email`，最终表示必须含至少一个合法收件人；不合法的最终文档整笔拒绝。Merge Patch 里的 `null` 不能同时表示“字段存在且值为空”；若资源必须保留显式 JSON null，应为该字段另定表示或选择别的补丁格式。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v8"

{"id":42,"title":"Monthly summary","delivery":{"channel":"download"}}
~~~

表单只序列化当前模式字段：切到 `download` 时不提交隐藏的 `recipients`。服务端通过该模式的领域规则移除不适用字段，因此它既遵守“补丁省略字段表示保持”的通用规则，也返回不含旧收件人的规范表示。若后来切回 `email`，一次新的补丁可把整个收件人数组替换为 `["editor@example.test","audit@example.test"]`；数组元素不是独立增删操作。

版本判断必须和写入处在一个原子条件里。可以在事务中锁定并检查版本、合并和验证，然后执行版本条件更新；也可以把合并后的文档连同预期版本交给数据库条件更新：

~~~sql
UPDATE reports
SET document = :validated_document,
    version = 8
WHERE report_id = 42
  AND tenant_id = :authorized_tenant
  AND version = 7
RETURNING document, version;
~~~

只有影响一行的事务提交，服务才返回新表示和 ETag。若版本条件不成立，事务不能写入任何补丁内容。不能先在事务外读到 v7、随后无条件更新：两次并发请求都可能检查 v7 后依次覆盖对方。

假设用户甲和乙都读到 v7。甲先提交后，当前表示成为 v8；乙仍用 v7 的编辑提交时，服务返回 412 Precondition Failed（前置条件失败），不自动覆盖、不自动重放：

~~~http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{"type":"https://api.example/problems/version-mismatch","title":"The report changed","status":412}
~~~

乙的客户端保留自己的草稿和 v7 编辑基线，重新读取 v8，再把基线、用户草稿与服务器当前表示进行比较；用户确认合并后才以新 ETag 再提交。若请求没有 `If-Match`，此合成端点选择 428 Precondition Required（要求前置条件）；这是一项端点政策。客户端在提交编辑时携带所保存的强 ETag；服务端能验证它是否以强比较匹配当前表示，但不能证明调用方真的曾读取过它。此端点不接受 `W/"…"` 弱标签或 `*`：本合成政策要求逐版本比较，不把“资源存在”当作编辑基线。授权仍先于更改；412 不能替代对象授权结果。

这里选 JSON Merge Patch，不把 JSON Patch（JSON 操作补丁）当成同一语法：后者的 `application/json-patch+json` 正文是带 `add`、`remove`、`replace`、`move`、`copy` 或 `test` 的操作数组，数组元素和 `null` 按操作路径处理。服务应公开自己接受的媒体类型，例如通过 `Accept-Patch`，调用方也不能仅凭 HTTP 方法名猜补丁语义。

## 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 可创建一条报表资源记录，返回 `201 Created` 和 `Location: /api/reports/44`。如果新资源的 `status` 是 `queued`，201 表示资源记录已经建立，不表示报表成品已生成。若请求创建的是独立长作业，账户报表案例使用 `POST /v1/accounts/acct-17/reports`，客户端预先生成 `Idempotency-Key: report-demo-208`；成功受理时，`202 Accepted` 的 `Location` 和正文 `statusUrl` 都指向 `/v1/jobs/job-demo-731`。如果整个响应丢失，客户端用相同请求体和幂等键重发 POST，数据库返回同一个已持久化 job 与状态 URL；同键对应不同规范化请求则冲突，不能猜测 job ID。收到 URL 后再 `GET /v1/jobs/job-demo-731` 查询。202 表示已受理，不表示成功完成。具体事务和映射见[怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: reports.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Monthly summary","status":"ready"}],"next_cursor":"opaque-token-A"}
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

这两页使用固定的三条演示数据：第一页 `[41, 42]` 续到 ID 42 之后，第二页 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据。下面的内存复现把不透明 token 映射为偏移量，只适用于这组不变的演示数据：如果第一页后删除 ID 41，偏移量仍跳过两条，第二页会漏掉 ID 43。生产中的移动集合可把游标绑定筛选条件、授权范围、过期时间和最后一条记录的稳定复合键（如 `(created_at, id)`），下一页按键续读并每页重新授权；若要求固定快照，则必须让后续请求继续读取同一个快照。并列时间戳时，键集游标要同时保存两个排序键。

> [!example] 读完三条报表的分页回放
> 在这组固定数据中，ID 升序且页大小为 2：第一批是 `[41, 42]`，第二批是 `[43]`，返回 `next_cursor: null` 后停止。内存复现用偏移量映射 token；它不演示可变集合中的 keyset 或快照分页。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。运行代码会生成不透明 token。

## OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、媒体类型、成功与错误响应及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。只有运行时错误和 OpenAPI 都匹配，客户端才不会按一份服务实际不返回的契约生成分支。检查时要按操作核对真实路径、状态码、媒体类型、Problem `type`、分页字段是否必填以及 schema 是否允许 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，演示 GET/POST、验证、分页和 OpenAPI；它不实现上一节的 PATCH、Merge Patch 或 `If-Match`。PATCH 合同使用 `/api/reports/42` 和 `Monthly summary` 的表单表示；可运行 fixture 是独立的最小数据集，GET 42 固定返回 `Service health`，只验证 GET/POST 映射，不证明 PATCH 表示或并发写入。复现也没有身份认证、租户授权或数据库并发唯一性，不是可直接部署的安全报表服务。正常请求和失败的输入输出已在正文展示，无需运行这段代码才能理解相应契约。

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
> 此示例用内存中的偏移量映射演示游标边界；进程重启后令牌会失效，也未绑定筛选条件、排序或身份。生产集合可使用基于索引的键集游标，并对每一页重新授权。页面内容由这三条记录计算，不代表性能测量结果。

## API 返回的链接怎样告诉客户端可继续做什么？

REST 的 Hypermedia as the Engine of Application State（超媒体作为应用状态引擎，HATEOAS）约束要求客户端从服务端表示中发现当前可用的状态转移。客户端仍需理解媒体类型和关系名，但不必仅凭报表 ID 拼出每个目标 URL。API 可以在报表表示中按自己的契约返回链接：

~~~json
{
  "id": 42,
  "links": [
    { "rel": "self", "href": "/api/reports/42" },
    { "rel": "download", "href": "/api/reports/42/download" }
  ]
}
~~~

React 客户端可以按关系查找详情地址并渲染链接。下面假设 `self` 关系已在 API 表示契约中定义，`href` 是同源站点根路径；只有契约明确允许时才跟随异源地址，不能把当前站点的认证信息盲目附到异源请求上。客户端不再根据 `id` 自行构造 `/api/reports/${id}`。

~~~tsx
type ApiLink = { rel: string; href: string };
type Report = { id: number; links: ApiLink[] };

function ReportDetailsLink({ report }: { report: Report }) {
  const self = report.links.find(link => link.rel === "self");
  return self ? <a href={self.href}>查看报表详情</a> : null;
}
~~~

普通链接适合安全导航，例如读取详情。链接本身若只给出 `href`，并没有说明取消报表等写操作应使用什么 HTTP 方法和请求体；这类动作应按 API 明确声明的 affordance（操作描述）或另行定义的契约发送，不能把有副作用的操作伪装成 `<a>`。单页应用可由路由接管内部导航，但路由仍需按它自己的加载和历史规则提交地址；服务端返回链接不会自动配置 React Router。

## 兼容演进需要显式规则

新增可选响应字段通常可兼容会忽略未知字段的客户端，但严格解码器或生成代码可能拒绝它。删除字段、改变字段类型或含义、把可选请求字段改为必填、改变 Problem `type`、调整分页结束标志，都可能破坏调用方。应公开兼容政策，检查重要调用方，并为不兼容变更安排版本切换或迁移窗口；不存在唯一强制的版本化方案。

**接下来：** 本章描述调用方可观察的接口结构；HTTP 方法、缓存与状态码的通用语义见[浏览器请求如何到达 HTTP 响应？](../networking/http-protocols-and-websockets.md)，副作用未知后的结果查询和重试见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。

> [!info]- 来源
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-06。
> - 400、401 challenge、403、404、409、422、201 与 202 的 HTTP 语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§11.6.1、§15，2022-06；428 和 429 则分别见 RFC 6585 §3–§4；核对于 2026-11-09。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-06。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 页大小、请求间参数一致、不透明 page token 和结束信号：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-06。
> - FastAPI 请求模型、响应模型和自定义错误处理：[FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)，官方文档核对于 2026-11-06；错误类型映射已在列明版本的本地运行环境核对。
> - REST 超媒体约束及由表示提供状态转移：[Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, §5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000；核对日期：2026-11-06。
> - 安全的 `GET` 方法与 HTTP 方法语义：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.1，2022-06；核对日期：2026-11-06。
> - 条件更新与陈旧 ETag： [IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1) §13.1.1（`If-Match` 必须用强比较）和 §15.5.13（412），2022-06；核对于 2026-11-09。 [IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html#section-3) §3 定义 428，2012-04；它只用于此端点所选择的缺少前置条件响应。该 RFC §4 定义 429，并规定 429 响应不得被缓存。
> - PATCH 的整组变更原子应用及 `Accept-Patch`： [IETF RFC 5789, PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789.html#section-2) §2、§3.1，2010-03；核对于 2026-11-09。
> - `application/merge-patch+json` 的成员省略、`null` 删除和整体数组值语义：[IETF RFC 7396, JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html#section-2)，§2，2014-10；核对于 2026-11-09。JSON Patch 的操作媒体类型见 [IETF RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html)，§3–§4，2013-04。
