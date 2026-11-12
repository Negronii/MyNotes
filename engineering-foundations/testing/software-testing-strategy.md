# 怎样用测试边界验证一次报表服务改动？

报表平台的合成案例有两条需要验证的契约：`tenant-a` 读取自己的报表 42 得到 200；已认证的 `tenant-b` 猜中同一个全局 ID 时得到 404。重复处理同一个导出任务时，数据库只能提交一次有效状态转换，已完成任务保留第一次写入的结果键。后面的 SQLite 例子只检查数据库行，不写入或读取对象存储；它不证明结果对象存在，也不证明物理上传只发生一次。测试要把这些失败条件变成可观察的断言，不能只让实现和它自己生成的成功路径测试一起通过。

测试边界由“哪种失败可能发生”决定。用 Application Programming Interface (应用程序接口，API) 集成和数据库集成时，分别把真实路由、测试选定的身份接缝和选定数据库纳入测试；只有要证明 broker (消息代理) 的发布、重投或确认，才需要对应的消息代理测试；只有问题可能由部署装配引起，才需要近生产端到端旅程。本文用 SQLite 演示路由与 Structured Query Language (结构化查询语言，SQL) 的本地证据，不把它扩展成 PostgreSQL、消息代理或生产身份系统的证据。

## 先把风险与可证明的边界对应起来

从需要守住的业务条件出发，挑一个包含实际故障边界的最小环境，并先写清输入和可观察结果。下表是互补的检查位置，不是每个改动都要依次跑完的固定测试层级：只有较低边界不能证明目标属性时，才再引入更完整的环境。

| 要排除的失败 | 测试边界 | 能看到的证据 | 仍不能据此声称 |
|---|---|---|---|
| 租户 A/B 的纯访问规则判断颠倒 | 单元测试 | 给定可信主体和资源归属，规则返回允许或拒绝 | 实际路由一定调用了这条规则 |
| 路由忘记传租户条件、状态码或响应字段错误 | API 集成 | 实际路由、所选身份接缝 (本例直接定义测试接缝)、参数校验、数据库查询、序列化和错误映射一起工作 | 真实网络、生产身份提供方或生产数据库方言正常 |
| 唯一约束、回滚或条件更新的实际数据库行为错误 | 数据库集成 | 选定数据库执行真实表结构和 SQL | 另一种数据库有相同类型、锁或并发行为 |
| 新响应不兼容已发布客户端 | 契约测试 | 当前响应与已发布 schema (结构定义) 或代表性旧客户端比较 | 只检查本次生成的 OpenAPI 就兼容旧客户端 |
| 消息发布、重复投递或 acknowledgment (消费者确认，ACK)路径丢失、重做 | 消息代理集成 | 选定消息代理及其路由、持久性和确认设置下的实际交接 | 在本地把 worker (工作进程)函数调用两次就等于代理完成了重投 |
| 只有服务装配后出现的故障 | 近生产端到端 | 受控的身份、API、数据库、队列和工作进程旅程 | 一个健康探针就证明用户旅程正确 |

前端组件和浏览器边界另见[前端测试怎样证明报表排序、历史恢复和发布产物正确？](../../frontend/testing/frontend-testing.md)。本篇重点放在服务路由、持久化和消息交付。

## 用实际路由重放跨租户反例

测试用 FastAPI 的 dependency injection (依赖注入)把测试主体交给同一个路由。完整示例直接定义 `tenant_from_test_header` 测试接缝，用 `X-Tenant-ID` 让两种主体走同一入口；它不是生产认证实现。已有 FastAPI 路由可在测试中覆盖认证依赖，同时保留真实路由；生产身份仍必须来自已验证的登录上下文，不能信任客户端任填的租户头。示意表把 `report_id` 设为全局主键、`tenant_id` 设为所有者；若实际 schema 使用复合主键，测试要按真实键改写。

关键查询同时约束当前租户和报表 ID。下面展示查询和可观察断言；完整 FastAPI、SQLite 与 pytest 夹具放在折叠示例中。

~~~python
row = connection.execute(
    text("""
        SELECT report_id, state FROM reports
        WHERE tenant_id = :tenant_id AND report_id = :report_id
    """),
    {"tenant_id": tenant_id, "report_id": report_id},
).mappings().first()

owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
missing = client.get("/api/reports/43", headers={"X-Tenant-ID": "tenant-b"})
assert owner.status_code == 200
assert owner.json() == {"report_id": 42, "state": "ready"}
assert other.status_code == 404
assert missing.status_code == 404
assert other.json() == missing.json() == {"detail": "report not found"}
~~~

`TestClient` 在进程内调用 FastAPI 应用，不建立真实 HTTP socket (套接字)；SQLAlchemy 仍把参数化查询交给 SQLite 执行。所有者查到自己的行得到 200，另一租户查无可见行得到通用 404。本例把生产身份边界设为 Bearer 认证，测试依赖用 `X-Tenant-ID` 注入已认证主体；未注入主体时，它模拟认证层返回 401 和 `WWW-Authenticate: Bearer realm="reports"`。测试会检查这个质询头，真实令牌的校验由认证层自己的测试负责。

> [!example]- 完整 FastAPI + SQLite 测试夹具与 pytest 检查
> 每个测试由默认的 function scope (函数作用域)fixture (测试夹具)建立独立内存数据库和应用。`StaticPool` 让本例各次串行访问复用同一 SQLite 连接，使测试客户端调用的路由读到已准备的数据；它不支持并发事务，不能把这组设置用于并发测试。
>
> ~~~python
> from typing import Annotated
>
> import pytest
> from fastapi import Depends, FastAPI, Header, HTTPException, Request
> from fastapi.testclient import TestClient
> from sqlalchemy import create_engine, text
> from sqlalchemy.pool import StaticPool
>
>
> def create_app() -> FastAPI:
>     engine = create_engine(
>         "sqlite+pysqlite://",
>         connect_args={"check_same_thread": False},
>         poolclass=StaticPool,
>     )
>     with engine.begin() as connection:
>         connection.execute(text("""
>             CREATE TABLE reports (
>                 report_id INTEGER PRIMARY KEY,
>                 tenant_id TEXT NOT NULL,
>                 state TEXT NOT NULL
>             )
>         """))
>         connection.execute(
>             text("INSERT INTO reports VALUES (:id, :tenant, :state)"),
>             {"id": 42, "tenant": "tenant-a", "state": "ready"},
>         )
>
>     app = FastAPI()
>     app.state.engine = engine
>
>     def tenant_from_test_header(
>         x_tenant_id: Annotated[str | None, Header()] = None,
>     ) -> str:
>         if not x_tenant_id:
>             raise HTTPException(
>                 status_code=401,
>                 detail="authentication required",
>                 headers={"WWW-Authenticate": 'Bearer realm="reports"'},
>             )
>         return x_tenant_id
>
>     @app.get(
>         "/api/reports/{report_id}",
>         responses={
>             401: {"description": "Authentication required"},
>             404: {"description": "Not found"},
>         },
>     )
>     def read_report(
>         report_id: int,
>         tenant_id: Annotated[str, Depends(tenant_from_test_header)],
>         request: Request,
>     ):
>         with request.app.state.engine.connect() as connection:
>             row = connection.execute(
>                 text("""
>                     SELECT report_id, state FROM reports
>                     WHERE tenant_id = :tenant_id AND report_id = :report_id
>                 """),
>                 {"tenant_id": tenant_id, "report_id": report_id},
>             ).mappings().first()
>         if row is None:
>             raise HTTPException(status_code=404, detail="report not found")
>         return dict(row)
>
>     return app
>
>
> @pytest.fixture
> def client():
>     app = create_app()
>     with TestClient(app) as test_client:
>         yield test_client
>     app.state.engine.dispose()
>
>
> def test_report_scope_and_authentication(client):
>     owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
>     other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
>     missing = client.get("/api/reports/43", headers={"X-Tenant-ID": "tenant-b"})
>     anonymous = client.get("/api/reports/42")
>     malformed = client.get(
>         "/api/reports/not-a-number", headers={"X-Tenant-ID": "tenant-a"}
>     )
>
>     assert owner.status_code == 200
>     assert owner.json() == {"report_id": 42, "state": "ready"}
>     assert other.status_code == 404
>     assert missing.status_code == 404
>     assert other.json() == missing.json() == {"detail": "report not found"}
>     assert anonymous.status_code == 401
>     assert anonymous.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert malformed.status_code == 422
>
>
> def test_openapi_declares_scope_error_responses(client):
>     operation = client.get("/openapi.json").json()["paths"][
>         "/api/reports/{report_id}"
>     ]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~
>
> 保存为 `test_report_scope.py` 后运行 `python -m pytest -q test_report_scope.py`。OpenAPI 检查只说明本应用当前声明哪些响应码；若要保证旧客户端兼容，仍须与已发布 schema 或代表性旧客户端比较。

本例路由没有声明 `response_model`；本机运行生成的 200 OpenAPI 响应 schema 是 `{}`，因此没有把 `state` 标成必需字段。上面的 OpenAPI 用例只检查响应码，不能证明删掉 `state` 会被 schema 拦住。所有者的精确 JSON 断言会在本例中发现该字段被删，但要验证已发布客户端兼容性，仍要用标明必需字段的已发布 schema 或固定旧客户端响应契约来检查。

本例把 404 作为隐藏资源的策略：B 请求 A 实际拥有的 42，与 B 请求表中不存在的 43，必须得到相同状态和通用正文；断言同时确认正文不含 A 的租户归属或报表状态。只看状态码不能证明响应没有泄露。若查询退回只按全局主键 `report_id` 读取，`tenant-a` 的原所有者测试仍会通过，但 `tenant-b` 会得到 200，新增的跨租户输入才会暴露漏掉的租户谓词。示例的 `session.get(Report, 42)` 同样只按全局主键取行，不等于它验证了当前主体的权限；实际表若使用复合主键，读取参数和反例都应依真实键定义调整。

认证得到可信主体之后，仍要对具体报表和动作逐次授权；测试头不改变这一生产边界。授权模型和缓存命中也要保留当前租户范围，见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

参数校验、认证和旧客户端兼容也分别验收：带可信测试主体的 `GET /api/reports/not-a-number` 由整数路径参数校验返回 422；无主体请求按本例策略得到 401。用例同时检查 401 的 `Bearer realm="reports"` 质询；若真实服务采用另一种认证方案，质询及对应断言也须与该方案一致。

### 用数据库检查重复提交与重复处理

入口重放同一 `(tenant_id, request_key)` 且参数相同的提交时，应用应返回第一次创建的 `job_id`；同键但参数不同，则按 API 契约拒绝。消费者对该 `job_id` 重复收到任务时，条件更新应只允许一次从 `pending` 到 `done` 的状态转换。下面的 SQLite 片段分别展示这两个数据库行为：`jobs` 的任务由首条插入创建，`work` 的行由脚本独立预置，并非从 `jobs` 自动生成；冲突插入只检查唯一键是否保留原 `job_id`，并不实现应用层读取后返回原任务的逻辑。

固定本次 `job_id = "job-demo-731"`，结果键为 `private/reports/job-demo-731.csv`。提交表 `jobs` 初始为空；消费表 `work` 已单独预置该任务，状态是 `pending`、计数为 0、结果键为空。逐步读取数据库就能观察下面的区别：

| 操作 | 数据库返回的信号 | 操作后保留的状态 |
|---|---|---|
| 首次插入 `(tenant-a, export-42, job-demo-731)` | 影响 1 行 | `jobs` 保存该完整任务行 |
| 同一租户和请求键，换成候选任务 `job-duplicate` 再插入 | `SQLITE_CONSTRAINT_PRIMARYKEY`；脚本调用 `rollback()` 结束本次事务 | 原任务行仍在，不能被替换或多出一行 |
| 首次处理 `job-demo-731`，只更新 `status='pending'` 的行 | 影响 1 行 | `work` 变为 `done`、计数 1、写入上述结果键 |
| 再次处理同一任务，沿用相同条件 | 影响 0 行 | 已完成的任务行与第一次写入的结果键不变 |

冲突测试还要断言异常类型和完整原行。只数“一行”会让 `INSERT OR REPLACE` 偷换 `job_id` 后仍通过；只捕获任意 `IntegrityError` 又会把非空约束失败误当成重复主键。消费侧检查的是本地条件更新，不能据此判断消息代理已经重投或确认。

> [!example]- 用标准库 SQLite 重放唯一键和条件更新
> 这段独立示例只执行本地数据库约束；它没有连接消息代理，也没有并发工作进程。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> job_id = "job-demo-731"
> result_key = f"private/reports/{job_id}.csv"
> db.executescript("""
> CREATE TABLE jobs (
>     tenant_id TEXT NOT NULL,
>     request_key TEXT NOT NULL,
>     job_id TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, request_key)
> );
> CREATE TABLE work (
>     job_id TEXT PRIMARY KEY,
>     status TEXT NOT NULL,
>     processed_count INTEGER NOT NULL,
>     result_key TEXT
> );
> """)
> db.execute(
>     "INSERT INTO work VALUES (?, 'pending', 0, NULL)",
>     (job_id,),
> )
> db.commit()
>
> first_insert = db.execute(
>     "INSERT INTO jobs VALUES (?, ?, ?)",
>     ("tenant-a", "export-42", job_id),
> ).rowcount
> db.commit()
> try:
>     db.execute(
>         "INSERT INTO jobs VALUES (?, ?, ?)",
>         ("tenant-a", "export-42", "job-duplicate"),
>     )
> except sqlite3.IntegrityError as error:
>     error_name = error.sqlite_errorname
>     db.rollback()
>     assert error_name == "SQLITE_CONSTRAINT_PRIMARYKEY", error_name
> else:
>     db.rollback()
>     raise AssertionError("duplicate key did not raise primary-key conflict")
>
> jobs = db.execute(
>     "SELECT tenant_id, request_key, job_id FROM jobs"
> ).fetchall()
> assert jobs == [("tenant-a", "export-42", job_id)]
>
> first_update = db.execute(
>     "UPDATE work SET status='done', processed_count=processed_count+1, "
>     "result_key=? WHERE job_id=? AND status='pending'",
>     (result_key, job_id),
> ).rowcount
> db.commit()
> second_update = db.execute(
>     "UPDATE work SET status='done', processed_count=processed_count+1, "
>     "result_key=? WHERE job_id=? AND status='pending'",
>     (result_key, job_id),
> ).rowcount
> db.commit()
>
> inserted_rows = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
> final_work = db.execute("SELECT * FROM work").fetchone()
> assert (first_insert, inserted_rows) == (1, 1)
> assert (first_update, second_update) == (1, 0)
> assert final_work == (job_id, "done", 1, result_key)
> print(first_insert, inserted_rows)
> print(first_update, second_update, final_work)
> ~~~
>
> 预期输出为 `1 1` 和 `1 0 ('job-demo-731', 'done', 1, 'private/reports/job-demo-731.csv')`。这只证明数据库最终保留一个对象键引用，不代表真的上传过对象或测试了消息代理；SQLite 的内存连接和唯一约束细节见来源，也不要用这条串行轨迹宣称多个数据库进程下的争用已测过。

如果重复任务还会付款、发邮件或通知其他服务，本地条件更新不会回滚已经发生的远端副作用。transactional outbox (事务发件箱)把业务行与待发送意图一同持久化，relay (转发进程)恢复后仍可能再次发送；外部动作还要使用对端认可的幂等键，或通过权威记录确认并修复重复。仅有 outbox 不足以防止远端重复付款。超时后的未知结果与安全重试见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)；账户报表任务与 outbox 的完整交接见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)；publisher confirm (发布者确认)和 consumer acknowledgement (消费者确认)的范围见[报表任务的发布确认、消费者确认与业务完成各证明什么？](../reliability/queue-delivery-and-acknowledgement.md)。

## 从测试证据接到可发布的变更

测试结果应能追溯到变更、代码、测试输入和实际产物。Continuous Integration (持续集成，CI)先固定源码提交，再用该快照构建镜像；发布流程应验证并晋级同一份通过检查的镜像，不能把“源码上的测试通过”说成另一次重新构建的镜像也已验证。变更交付的完整路径见[如何晋级并回滚已验证的报表服务产物？](../infrastructure/application-deployment-and-ci-cd.md)。

> [!info]- 来源与运行边界
> - FastAPI 官方 [Testing](https://fastapi.tiangolo.com/tutorial/testing/) 与 [TestClient 参考](https://fastapi.tiangolo.com/reference/testclient/)：说明客户端测试如何调用应用；TestClient 不建立实际 HTTP 套接字，核对于 2026-11-12。
> - FastAPI 官方 [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)：可用 `app.dependency_overrides` 替换认证依赖同时保留真实路由；本例则在路由定义处直接接入测试身份，核对于 2026-11-12。
> - FastAPI 官方 [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)：响应模型会生成对应的 OpenAPI schema 并校验返回值；本例没有 `response_model`，所以运行得到的 200 schema 为 `{}`，核对于 2026-11-12。
> - pytest 官方 [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)：fixture 注入和生命周期；本例使用默认的 function scope，核对于 2026-11-12。
> - SQLAlchemy 2.0 官方 [SQLite 方言：内存库、多线程与 StaticPool](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)：内存数据库与连接绑定；StaticPool 只适合完全串行访问，核对于 2026-11-12。
> - SQLite 官方 [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)：主键和唯一约束；这里只演算本地 SQLite 实际行为，核对于 2026-11-12。
> - SQLite 官方 [ON CONFLICT](https://sqlite.org/lang_conflict.html) 与 [Result and Error Codes](https://www.sqlite.org/rescode.html)：`IGNORE` 可静默跳过冲突，`REPLACE` 可删除原冲突行；扩展约束码可区分主键与非空约束失败，核对于 2026-11-12。
> - IETF [RFC 6750 §3](https://www.rfc-editor.org/rfc/rfc6750.html#section-3)：Bearer 质询的认证参数；本例用 `realm="reports"` 标识保护空间。
> - IETF [RFC 9110 §15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2)：生成 401 时必须包含适用于资源的 `WWW-Authenticate`；本例模拟 Bearer 认证边界的质询并在测试中断言该头，核对于 2026-11-12。
> - AWS Prescriptive Guidance [Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)：outbox 的本地原子写入不消除重复消息，消费者还要能幂等处理，核对于 2026-11-12。
> - RabbitMQ 4.4 官方 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)：发布确认与消费者 ACK 属于不同交接边界；本文不声称本例执行了 RabbitMQ，核对于 2026-11-12。
> - 实际运行版本：Python 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1、SQLAlchemy 2.0.44、pytest 9.0.2、SQLite 3.51.0。版本仅描述这次本地复现环境，不代表最新版本或 PostgreSQL、broker 集成结果。
