# 如何设计可预期的 HTTP API 契约？

API 契约说明调用方怎样构造请求、怎样识别成功和失败、怎样继续读取集合。HTTP 提供通用方法和状态语义；API 定义领域输入、返回结构、错误类别、分页规则与兼容政策。文档、类型注解、OpenAPI 描述和运行中的实现是不同层：写出 schema（结构模式）不证明已部署行为符合它。

**案例：** 浏览器向独立教学源站 `api-contracts.example` 请求 `GET /api/reports/42`。这个合成报表与网络协议章的 `reports.example` 报表不是同一个资源；编号、正文和 ETag 也彼此独立。报表存在且当前主体获准读取时，API 返回稳定 JSON；编号格式错误、报表不存在、认证缺失或访问被拒，各有调用方能识别的结果。列表按 ID 排序并显式给出下一页游标。正文还用同一独立 API 说明带 ETag 的编辑与 201/202 的后续状态。

示例域名、报表标识、内容和响应值都是教学数据；应用层政策会在正文中单独标明。

> **HTTP 片段约定：** 所有 `~~~http` 块只展示本段要讨论的字段，不是可直接发送的完整 HTTP/1.1 报文。主流程假定调用方带有有效凭据；为聚焦 API 契约，片段省略凭据，有些也省略 `Host`。带正文的请求片段没有展示 `Content-Length` 或 `Transfer-Encoding` 分帧字段；实际 HTTP/1.1 请求必须带 `Host`，并按正文长度正确分帧。

~~~http
GET /api/reports/42 HTTP/1.1
Host: api-contracts.example
Accept: application/json, application/problem+json
~~~

一个合法的成功表示是：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

本章的详情表示要求 `id`、`title` 和 `delivery`；可选 `note` 在无值时省略，不以 JSON `null` 表示。集合项和 201 创建响应是摘要表示，包含 `id`、`title`、`status`，不包含详情中的 `delivery` 和 `note`。这些是本 API 明确的两个 JSON 形状。

路径里的 `42` 是 API 的资源标识，不是访问授权。每个请求都要由可信凭据确定当前主体，再检查其对租户和对象的权限，之后才读取或修改资源。本端点先认证，再做租户范围内的对象可见性检查；不存在和不可见统一返回 404。资源归属见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

## 错误契约怎样保留机器可判定的含义？

API 可以用 RFC 9457 Problem Details 表示错误，媒体类型为 `application/problem+json`。例如 ID 不存在或按隐私政策不可见时返回统一错误：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api-contracts.example/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

客户端可依赖稳定的 `type` 或扩展错误码，而不应解析供人阅读的 `title`、`detail`。若正文含 `status`，它须与实际 HTTP 状态相同。不要回显秘密、内部异常栈或 SQL 文本。

本端点先验证认证凭据；因此未认证请求即使带非数字报表 ID 也返回 401。对象可见性按租户范围检查；报表不存在和主体无权读取都返回同一个 404 `type` 与中性详情。本端点选择隐藏式 404，不返回 403。其他允许披露资源存在的端点，可以用 403 表示已识别身份但拒绝访问。对处理请求正文之前就能确定的失败（例如未认证或对象不可见），先返回该失败；隐藏对象带陈旧标签仍为 404，不用 412 暗示对象存在。RFC 9110 的条件请求优先级说的是这类无需处理正文即可确定的失败，不表示所有字段级领域验证都必须先于 `If-Match`。已认证且对象可见时，不支持的媒体类型也在读取正文前确定，所以它与过时标签同时出现时先返回 415；缺少 `If-Match` 时也先处理此媒体类型失败。

| 条件 | 本例的结果 | 补充约定 |
| --- | --- | --- |
| 报表 42 存在、身份和资源权限都通过 | 200 + JSON | 定义成功表示中的稳定字段 |
| 缺少有效凭据，即使报表 ID 不是整数 | 401 + Problem Details | 先认证，再做报表 ID 的数字转换；发出 401 时提供适用的 `WWW-Authenticate` challenge，例如 `Bearer realm="reports"` |
| 报表不存在，或主体无权读取；即使带陈旧 `If-Match` | 404 + Problem Details | 本端点一律隐藏对象；两种情况使用相同 `type` 和中性详情，且在 `If-Match` 前返回 |
| JSON 语法无效，例如正文 `{` | 400 + Problem Details | 指明内容无法解析 |
| `Content-Type` 不受端点支持，例如 PATCH 未声明的补丁格式 | 415 + Problem Details | PATCH 资源在 OPTIONS 响应中用 `Accept-Patch` 公布补丁媒体类型；创建 fixture 只接受 `application/json` |
| 认证和语法解析通过后，字段值、路径 ID 或范围不符合本 API 契约 | 422 + Problem Details | 指出字段路径和稳定错误代码；本例把非整数路径 ID 选为 422 |
| 与当前状态冲突，例如重复标题 | 409 + Problem Details | 告诉调用方怎样刷新或解决冲突 |
| 单个 `If-Match` 标签是弱标签（例如 `W/"api-contracts-report-42-v7"`），或强标签不匹配 | 412 + Problem Details | RFC 要求强比较；不应用补丁，客户端读取当前表示并比较本地草稿 |
| `If-Match` 语法错误，或合法的 `*` / 标签列表被本端点拒绝 | 400 + Problem Details | HTTP 允许 `*` 和列表；本端点的单标签限制是应用政策。单个弱标签语法合法，不能归入此 400 分支 |
| 缺少本端点要求的 `If-Match` | 428 + Problem Details | 应用政策要求前置条件；RFC 6585 规定 428 响应不得被缓存 |
| 超过适用调用额度 | 429 + Problem Details | 定义额度作用域和可重试时机；确定时可附 `Retry-After`，且 429 响应不得被缓存 |
| 报表 999 不存在或被隐藏 | 404 + Problem Details | 与成功表示结构不同 |
| 服务暂时不可用，或发生未预期的服务端错误 | 503 或 500 + Problem Details | 只给稳定的机器类别，不回显栈或 SQL；写入结果未知时按幂等契约查询或恢复，不盲目重放 |

这是本 API 的映射政策，不是所有服务都必须采用的唯一表。`422 Unprocessable Content` 表示内容语法可理解但指令不能处理；本例把畸形 JSON 归为 400，把 JSON 可解析但字段不合规、以及非整数路径 ID 映射为 422。路径 ID 的状态码是本 API 额外约定。未认证和不可见对象是处理正文前即可确定的失败；其余字段解析、业务校验和条件请求的顺序由该端点实现定义，RFC 不要求把所有领域校验都放在 `If-Match` 之前。数据库并发不变量仍由原子写入负责。

## 如何用条件 PATCH 防止覆盖别人更新？

本例的编辑端点只返回一种规范 JSON 表示，而且任一可见字段变更都会推进资源版本，因此它可以用 `"api-contracts-report-42-v7"` 标记该表示。强 ETag（实体标签）必须随它所标记的表示数据变化；若内容协商或内容编码产生字节不同的表示，服务须给每种表示生成可区分的强标签，并让每个标签映射到用于原子写入检查的资源版本。压缩与未压缩表示不能共用同一个强标签。下面先读取唯一的 JSON 表示：

~~~http
GET /api/reports/42 HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v7"

{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

之后用户把交付方式切为下载，并删除可选备注。此资源只接受 JSON Merge Patch（JSON 合并补丁），所以请求声明媒体类型 `application/merge-patch+json`，并带上刚读到的强 ETag：

~~~http
PATCH /api/reports/42 HTTP/1.1
Host: api-contracts.example
Content-Type: application/merge-patch+json
If-Match: "api-contracts-report-42-v7"

{"delivery":{"channel":"download"},"note":null}
~~~

Merge Patch 的对象成员按名称递归合并：未出现的成员保持，`null` 表示删除成员，数组整体替换。应用补丁后的中间表示仍有旧 `recipients`，因为该成员在补丁里被省略；本合成 API 另规定下载模式不保存收件人字段，业务规范化随后移除它，并验证最终表示。若 `channel` 是 `email`，最终表示必须含至少一个合法收件人；不合法的最终文档整笔拒绝。Merge Patch 里的 `null` 不能同时表示“字段存在且值为空”；若资源必须保留显式 JSON null，应为该字段另定表示或选择别的补丁格式。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "api-contracts-report-42-v8"

{"id":42,"title":"Monthly summary","delivery":{"channel":"download"}}
~~~

表单只序列化当前模式字段：切到 `download` 时不提交隐藏的 `recipients`。服务端通过该模式的领域规则移除不适用字段，因此它既遵守“补丁省略字段表示保持”的通用规则，也返回不含旧收件人的规范表示。若后来切回 `email`，一次新的补丁可把整个收件人数组替换为 `["editor@example.test","audit@example.test"]`；数组元素不是独立增删操作。

版本判断必须和写入处在一个原子条件里。下面的简化 SQL 假定主体到租户的授权已验证，且该授权在本次写事务提交前保持稳定；实际系统需由事务边界、授权行锁或等效约束保证这个前提。可以在事务中锁定并检查版本、合并和验证，然后执行版本条件更新；也可以把合并后的文档连同预期版本交给数据库条件更新：

~~~sql
UPDATE reports
SET document = :validated_document,
    version = 8
WHERE report_id = 42
  AND tenant_id = :authorized_tenant
  AND version = 7
RETURNING document, version;
~~~

如果权限可能在写入期间并发撤销，就不能仅依赖上面的租户和版本谓词：还要在写入的同一一致性边界内重核授权，例如锁住授权记录，或把当前授权谓词/版本纳入原子条件，并让撤销与写入按事务顺序发生。成功写入后再检查权限无法撤销已经发生的越权写入。条件更新返回一行并提交，服务才返回新表示和 ETag；返回 0 行只证明这次写入没有发生，不能单独证明是版本过期。记录可能已删除或版本已变化。服务用当前授权和租户范围重新读取：若对象现已不存在或不可见，按本例返回隐藏式 404；若对象仍可见但版本不再匹配，才返回 412。这个事后检查只区分失败原因，不替代写入时的授权原子性。不能先在事务外读到 v7、随后无条件更新：两次并发请求都可能检查 v7 后依次覆盖对方。

PATCH 的整份补丁必须原子应用：所有修改一起可见，或一项也不应用。这里的一行条件更新把版本比较与报表表示更新放在同一个数据库操作中；若一个补丁要改多行或其他持久状态，就要用同一事务覆盖全部改动和最终业务校验。

| 时点 | 用户甲 | 用户乙 | 数据库中的版本与结果 |
| --- | --- | --- | --- |
| 两人读取 | 保存 v7 表示和 ETag `"api-contracts-report-42-v7"` | 保存 v7 表示和 ETag `"api-contracts-report-42-v7"` | 当前版本 v7 |
| 甲提交 | `PATCH If-Match: "api-contracts-report-42-v7"`；条件更新匹配，提交 v8 | 仍在编辑 v7 草稿 | 当前版本 v8；甲收到 200 和 v8 标签 |
| 乙提交旧基线 | — | `PATCH If-Match: "api-contracts-report-42-v7"`；条件更新影响 0 行 | 此例中对象仍存在且可见、当前为 v8；没有应用乙的补丁，返回 412。删除或不可见时按前文返回 404 |
| 用户处理冲突 | — | 读取 v8，把 v7 基线、自己的草稿和当前 v8 比较；确认合并后才按新标签重提 | 直到新条件更新提交前都保持 v8 |

假设用户甲和乙都读到 v7。甲先提交后，当前表示成为 v8；乙仍用 v7 的编辑提交时，服务返回 412 Precondition Failed（前置条件失败），不自动覆盖、不自动重放：

~~~http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{"type":"https://api-contracts.example/problems/version-mismatch","title":"The report changed","status":412}
~~~

乙的客户端保留自己的草稿和 v7 编辑基线，重新读取 v8，再把基线、用户草稿与服务器当前表示进行比较；用户确认合并后才以新 ETag 再提交。若请求没有 `If-Match`，此合成端点选择 428 Precondition Required（要求前置条件）；这是一项端点政策。端点接受一个语法有效的实体标签值并用强比较：语法错误按 400 处理；`*` 和标签列表虽是 HTTP 合法语法，但因本端点规定只用单个标签，也按应用政策返回 400；单个弱标签语法有效，却不能通过强比较，因此与陈旧强标签一样返回 412。客户端在提交编辑时携带所保存的强 ETag；服务端能验证它是否以强比较匹配当前表示，但不能证明调用方真的曾读取过它。PATCH 方法本身不承诺安全或幂等；本端点的 `If-Match` 能阻止用旧版本重复应用，但若首个提交成功、响应丢失，重放旧标签也会得到 412，无法仅凭 412 判断是自己的首个写入还是别的用户修改。此时应重新读取并比较；需要精确确认首次副作用的端点还要保存操作幂等记录，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)。授权仍先于更改；412 不能替代对象授权结果。

这里选 JSON Merge Patch，不把 JSON Patch（JSON 操作补丁）当成同一语法：后者的 `application/json-patch+json` 正文是带 `add`、`remove`、`replace`、`move`、`copy` 或 `test` 的操作数组，数组元素和 `null` 按操作路径处理。服务应公开自己接受的媒体类型，例如通过 `Accept-Patch`，调用方也不能仅凭 HTTP 方法名猜补丁语义。

## 201 创建资源和 202 接受作业有什么区别？

`POST /api/reports` 创建的是一条报表资源。即使它的 `status` 先为 `queued`，`201 Created` 仍表示资源记录已经建立；它不声称成品已生成：

~~~http
POST /api/reports HTTP/1.1
Content-Type: application/json

{"title":"Weekly overview"}

HTTP/1.1 201 Created
Location: /api/reports/44
Content-Type: application/json

{"id":44,"title":"Weekly overview","status":"queued"}
~~~

若请求创建的是可能较久才完成的独立作业，账户报表案例按应用契约使用幂等键（`Idempotency-Key`）重复识别同一提交：

~~~http
POST /v1/accounts/acct-17/reports HTTP/1.1
Idempotency-Key: report-demo-208
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731
Content-Type: application/json

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

`202 Accepted` 只表示已受理，作业之后仍可能失败；状态地址让调用方继续查询。本账户报表契约把幂等键作用域定义为 `(account_id, principal_id, key)`，并把规范化请求指纹绑定到 `reportId`、时间范围和格式。数据库唯一约束裁决同键请求的胜者；竞争失败的一方先回滚整笔插入事务，再读回已提交的同键 job 并比较请求指纹。指纹相同则返回原 job 和状态地址，参数不同则返回冲突，不能把唯一约束本身说成已返回了 job。若 202 回执丢失，客户端用原幂等键和相同请求重发 `POST` 来找回结果；在幂等映射保留期内不要为这次重试换新键。job 状态和最小幂等映射保留到终态后 14 天；成功状态与结果引用共同提交、结果可见后，结果对象单独保留 7 天；两种保留期限解决不同问题。这里的 `Idempotency-Key` 行为是应用契约，不是 HTTP 状态码单独提供的保证。收到地址后，客户端用 `GET /v1/jobs/job-demo-731` 查询，而不是把 202 当作最终结果。具体事务和映射见[怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 分页怎样给出明确结束条件？

集合可能很大或持续变化，契约须规定页大小、确定性排序和结束信号。本例假设报表 ID 唯一，默认 `limit=2`、最大 100，按 ID 升序；`next_cursor` 是必返回字段，最后一页明确返回 JSON `null`。这是本 API 的表示选择：分页规范也可用不透明的 next-page token 表示结束。本例允许后续页在 1–100 范围内更改 `limit`；游标只定位下一项，筛选条件和排序若有变化则应重新开始列表。

~~~http
GET /api/reports?limit=2 HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~json
{"items":[{"id":41,"title":"Monthly overview","status":"ready"},{"id":42,"title":"Monthly summary","status":"ready"}],"next_cursor":"opaque-token-A"}
~~~

客户端原样传回不透明游标：

~~~http
GET /api/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Host: api-contracts.example
Accept: application/json
~~~

~~~json
{"items":[{"id":43,"title":"Usage summary","status":"queued"}],"next_cursor":null}
~~~

这两页使用固定的三条演示数据：第一页 `[41, 42]` 续到 ID 42 之后，第二页 `[43]` 以 `null` 明确结束；只有客户端看见该结束标记才停止。短页不总表示没有后续数据，例如服务器可能按资源上限少返回几项，但仍提供游标。下面的内存复现把不透明 token 映射为偏移量，只适用于这组不变的演示数据：如果第一页后删除 ID 41，偏移量仍跳过两条，第二页会漏掉 ID 43。生产中的移动集合可把游标绑定筛选条件、授权范围、过期时间和最后一条记录的稳定复合键（如 `(created_at, id)`），下一页按键续读并每页重新授权；若要求固定快照，则必须让后续请求继续读取同一个快照。并列时间戳时，键集游标要同时保存两个排序键。

> [!example] 读完三条报表的分页回放
> 在这组固定数据中，ID 升序且页大小为 2：第一批是 `[41, 42]`，第二批是 `[43]`，返回 `next_cursor: null` 后停止。内存复现用偏移量映射 token；它不演示可变集合中的 keyset 或快照分页。若服务器因资源上限只返回 1 项但仍有后续数据，只凭短页就停止会漏项。运行代码会生成不透明 token。

## OpenAPI 怎样描述实际运行契约？

OpenAPI 记录操作路径、参数、请求/响应媒体类型、成功与错误响应、响应头及 schema，使人和工具可据此调用服务。框架可从请求/响应模型生成结构；自定义异常处理器也要在相应操作里声明错误响应。schema 可表达的约束要与运行时一致，例如仅含普通空格的标题既应在 `CreateReport` 的 JSON Schema 中被拒绝，也应在运行时返回 422；请求媒体类型和认证/授权等运行边界则要对照实际处理器单独核验。检查时按操作核对真实路径、状态码、媒体类型、创建响应的 `Location`、Problem `type`、分页字段必填性，以及 `next_cursor` 的 JSON Schema 是否同时允许字符串和 `null`。

下面的 FastAPI 复现定义裸应用前缀 `/api`，演示 GET/POST、验证、分页和 OpenAPI；它不实现上一节的 PATCH、Merge Patch、认证/租户授权、数据库唯一性或 ETag 并发写入。PATCH 合同使用 `/api/reports/42` 和 `Monthly summary` 的独立详情表示；可运行 fixture 是另一份独立最小数据集，GET 42 固定返回 `Service health` 摘要。创建路由用自定义 `APIRoute` 在 FastAPI 读取或解码正文前只接受 `application/json`，因此不支持的媒体类型即使正文不是合法 JSON，也先返回 415；支持的 JSON 媒体类型但正文格式错误才返回 400。媒体类型比较忽略大小写和参数。仅含普通空格的标题由请求 JSON Schema 的 `pattern` 与运行时校验共同拒绝。正文 `{"title":"   "}` 得到 422 Problem `type=.../validation`。fixture 不能证明 PATCH 表示、授权或并发写入；这些边界不能由 OpenAPI 生成结果替代。标题校验也有一个跨实现边界：JSON Schema 的 ECMAScript 正则与 Python `.strip()` 对 Unicode whitespace 的集合不同。例如以 ECMAScript 引擎执行此 `pattern` 时，单字符 `U+0085` 通过 `\S`，却被此 Python 运行时拒绝；`U+FEFF` 的结果相反。普通空格和长度样例通过，不等于 schema 与运行时对所有输入都一致。

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
> from fastapi.routing import APIRoute
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api-contracts.example/problems/"
>
>
> class CreateReport(BaseModel):
>     title: str = Field(min_length=1, max_length=60, pattern=r"\S")
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
> class JsonOnlyRoute(APIRoute):
>     def get_route_handler(self):
>         original_route_handler = super().get_route_handler()
>
>         async def check_media_before_body(request: Request):
>             media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
>             if media_type != "application/json":
>                 raise ApiProblem(
>                     415, "unsupported-media-type", "Unsupported media type",
>                     "Send this resource using application/json.",
>                 )
>             return await original_route_handler(request)
>
>         return check_media_before_body
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
>     415: problem_content("Content-Type must be application/json"),
>     422: problem_content("Invalid title fields"),
> }
> CREATE_RESPONSES = {
>     201: {
>         "description": "Report resource created",
>         "headers": {
>             "Location": {
>                 "description": "URI of the newly created report",
>                 "schema": {"type": "string"},
>             }
>         },
>     },
>     **CREATE_ERRORS,
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
> create_router = APIRouter(prefix="/api", route_class=JsonOnlyRoute)
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
> @create_router.post("/reports", status_code=201, response_model=Report, responses=CREATE_RESPONSES)
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
> app.include_router(create_router)
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
>     for media_type in ("application/merge-patch+json", "text/plain"):
>         for body in ('{"title":"Ignored"}', "{"):
>             unsupported = client.post(
>                 "/api/reports", content=body, headers={"Content-Type": media_type}
>             )
>             assert unsupported.status_code == 415
>             assert unsupported.json()["type"] == PROBLEM_BASE + "unsupported-media-type"
>
>
>     created = client.post("/api/reports", json={"title": " Weekly detail "})
>     assert created.status_code == 201 and created.json()["id"] == 44
>     assert created.json()["title"] == "Weekly detail"
>     assert created.headers["location"] == "/api/reports/44"
>     duplicate = client.post("/api/reports", json={"title": "weekly detail"})
>     assert duplicate.status_code == 409
>     assert duplicate.json()["type"] == PROBLEM_BASE + "duplicate-title"
>     media_parameters = client.post(
>         "/api/reports", content='{"title":"Case variant"}',
>         headers={"Content-Type": "Application/JSON; charset=UTF-8"},
>     )
>     assert media_parameters.status_code == 201 and media_parameters.json()["id"] == 45
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
>     assert {"400", "409", "415", "422"} <= set(post["responses"])
>     assert "404" not in post["responses"]
>     assert "Location" in post["responses"]["201"]["headers"]
>     request_body = post["requestBody"]["content"]
>     assert set(request_body) == {"application/json"}
>     title_schema = spec["components"]["schemas"]["CreateReport"]["properties"]["title"]
>     assert title_schema["minLength"] == 1 and title_schema["maxLength"] == 60
>     assert title_schema["pattern"] == r"\S"
>     page_schema = spec["components"]["schemas"]["Page"]
>     assert "next_cursor" in page_schema["required"]
>     cursor_types = {part.get("type") for part in page_schema["properties"]["next_cursor"]["anyOf"]}
>     assert {"string", "null"} <= cursor_types
>     print("GET /api/reports/42 -> 200; missing -> 404; invalid ID -> 422")
>     print("malformed JSON -> 400; unsupported media type -> 415; blank/overlong title -> 422; duplicate -> 409")
>     print("page [41, 42] -> [43]; required next_cursor=null ends the listing")
>     print("OpenAPI routes and per-operation responses match the demonstrated paths")
>
>
> check()
> ~~~
>
> 此示例用内存中的偏移量映射演示游标边界；进程重启后令牌会失效，也未绑定筛选条件、排序或身份。未知或过期游标返回 400，调用方应从第一页开始；本例允许续页更改 `limit`，但筛选条件或排序变化要重新开始。生产集合可使用基于索引的键集游标，并对每一页重新授权。页面内容由这三条记录计算，不代表性能测量结果。

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

这里的 `links` 数组是本 API 自订的 JSON 结构，不是通用的 HTTP 链接编码。只有当媒体类型或 API 契约定义了关系名的含义与可用状态转移时，客户端才有足够信息按链接继续操作；给任意 JSON 加一个 `href` 字段本身并不会自动提供这些语义。

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
> - 错误正文的类别标识、状态、标题、详情和扩展字段：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，§3–§4，2023-07；核对于 2026-11-12。
> - 400、401 challenge、403、404、409、422、201 与 202 的 HTTP 语义及条件请求失败优先级：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§9、§11.6.1、§13.2.1、§15，2022-06；核对于 2026-11-12。428 和 429 分别见 [IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) §3–§4；两种响应都不得缓存，2012-04；核对于 2026-11-12。
> - HTTP/1.1 请求的 `Host` 要求和消息正文分帧：[IETF RFC 9112, HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)，§3.2、§6.3，2022-06；核对于 2026-11-12。正文中的请求报文都明确标为片段。
> - 表示验证器、强 ETag、不同内容编码需用不同强标签，以及 `If-Match` 强比较：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，§8.8.1、§8.8.3.3、§13.1.1，2022-06；核对于 2026-11-12。
> - PATCH 的方法语义、整份补丁原子应用及 `Accept-Patch`：[IETF RFC 5789, PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789.html)，§2、§3.1，2010-03；核对于 2026-11-12。
> - `application/merge-patch+json` 的成员省略、`null` 删除和整体数组值语义：[IETF RFC 7396, JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html)，§2，2014-10；核对于 2026-11-12。JSON Patch 的操作媒体类型与操作数组见 [IETF RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html)，§3–§4，2013-04；核对于 2026-11-12。
> - 操作、参数、媒体类型、响应和 schema 的接口描述：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-12。代码环境当前生成 3.1.0；运行时版本由 `app.openapi()['openapi']` 决定，规范文件描述契约但不保证实现遵循它。
> - 不透明 page token、除 page size 外的续页参数一致，以及短页不代表结束：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance；核对于 2026-11-12。
> - FastAPI 请求模型、响应模型、自定义错误处理，以及用 `APIRoute.get_route_handler()` 在原请求处理器前检查请求：[Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Custom Request and APIRoute](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)，官方文档核对于 2026-11-12。代码运行环境为 FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1；运行回放另核验了媒体类型优先级与 OpenAPI 输出。
> - Pydantic 2.11 的前置字段校验器及 JSON Schema 生成：[Validators](https://docs.pydantic.dev/2.11/concepts/validators/)、[JSON Schema](https://docs.pydantic.dev/2.11/concepts/json_schema/)，官方版本文档核对于 2026-11-12；代码运行环境为 Pydantic 2.11.7。
> - REST 超媒体约束及由表示提供状态转移：[Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures, §5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000；核对日期：2026-11-12。
