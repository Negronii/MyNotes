# 怎样用测试边界验证一次报表服务改动？

报表平台工程师准备发布一项租户授权修复：tenant-a 应能读取自己的 report 42，得到 200；tenant-b 猜中同一 ID 时只能得到 404。导出 job 重复投递后，任务状态和结果对象引用也只能提交一次。要判断这次改动能否发布，测试必须覆盖这些用户可观察的失败条件，而不只是确认实现和它自己生成的 happy-path 测试一起通过。

application programming interface（应用程序接口，API）集成和数据库集成分别需要真实路由与 structured query language（结构化查询语言，SQL）。若要声称 publisher confirm（发布者确认）、consumer acknowledgement（消费者确认，ACK）或部署装配正确，还要把实际 broker（消息代理）或近似生产链路纳入测试。本文 SQLite 示例验证 FastAPI 路由和 SQL，不代表 PostgreSQL、broker 或生产身份系统已经验证。

~~~mermaid
flowchart TD
    A[契约：A 读 report 42 得 200；B 得 404] --> B[单元：租户规则]
    B --> C[API + SQLite：路由、主体接缝、查询]
    C --> D[契约：与已发布响应结构比较]
    D --> E[PostgreSQL：生产数据库方言与约束]
    E --> F[RabbitMQ：发布确认、重投、消费者确认]
    F --> G[近生产旅程：组件装配与流量路径]
~~~

每升高一层，必须能指出新增层解决的失败条件。测试数量多不能替代边界正确。单个端到端测试不易定位原因，也很难覆盖大量输入；只测函数又看不到依赖装配或真实数据库行为。

## 先把风险与可证明的边界对应起来

| 要排除的失败 | 合适边界 | 该边界能给出的证据 | 不能据此声称 |
|---|---|---|---|
| 租户 A/B 条件判断颠倒 | 单元测试 | 给定主体和资源归属，访问规则输出允许或拒绝 | 真实 HTTP 路由一定调用该规则 |
| 路由忘记传租户条件、返回错状态或错字段 | API 集成 | 实际路由、参数校验、依赖注入、响应序列化和错误映射 | 真实网络或生产身份提供方正常 |
| 唯一键、回滚或条件更新不守约束 | 数据库集成 | 选定数据库执行真实表结构与 SQL | 换一个数据库也有相同锁和类型行为 |
| 新响应不兼容已发布客户端 | 契约测试 | 当前输出与已发布 schema（结构定义）/代表性旧客户端比较 | 只检查本次自动生成的 schema 就兼容旧客户端 |
| 确认或重投造成丢失、重复业务效果 | broker 集成 | 指定 broker、队列配置、ACK 模式和持久化存储共同执行交接 | 本地函数调用两次等同于 broker 重投 |
| 只有服务装配后才出现的故障 | 近生产端到端 | 真实身份、API、数据库、队列和 worker 的受控旅程 | 一个健康探针就代表用户旅程正确 |

这些边界是互补关系，不是固定的“测试金字塔”。尽量把快速、确定的检查放在靠近故障条件的位置；只有下层无法证明的属性才提高边界。前端组件和浏览器行为另由[前端测试](../../frontend/testing/frontend-testing.md)说明，本篇聚焦 API、持久化和消息交付。

## 用实际路由重放跨租户反例

先将主体边界做成可替换依赖。X-Tenant-ID 只是测试接缝，用来把 tenant-a、tenant-b 送到实际路由；生产服务必须从已验证的登录上下文取得主体，不能信任客户端任填的租户头。示意表把 report_id 设为全局主键、tenant_id 设为资源所有者；若真实表用复合主键，测试应按真实 schema 改写，不能照搬主键读取方式。

> [!example] 关键查询和断言
> 关键是查询同时约束当前租户和 report 42，且两个租户走同一个 API 路由：
>
> ~~~python
> row = connection.execute(
>     text("""
>         SELECT report_id, state FROM reports
>         WHERE tenant_id = :tenant_id AND report_id = :report_id
>     """),
>     {"tenant_id": tenant_id, "report_id": report_id},
> ).mappings().first()
>
> owner = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-a"})
> other = client.get("/api/reports/42", headers={"X-Tenant-ID": "tenant-b"})
> assert owner.status_code == 200
> assert owner.json() == {"report_id": 42, "state": "ready"}
> assert other.status_code == 404
> ~~~
>
> 这组检查通过 FastAPI TestClient 进程内调用实际路由、通过 SQLAlchemy 执行参数化查询，并由 SQLite 执行真实 SELECT。它不是 mock，也没有建立网络 socket。

> [!example]- 完整 FastAPI + SQLite fixture 与 OpenAPI 检查
> 下方测试夹具为每次测试建立内存 SQLite，使用 StaticPool 让 TestClient 所在线程与数据库检查共享该连接。示例中的测试头不是真实认证协议。
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
>             raise HTTPException(status_code=401, detail="authentication required")
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
>     anonymous = client.get("/api/reports/42")
>
>     assert owner.status_code == 200
>     assert owner.json() == {"report_id": 42, "state": "ready"}
>     assert other.status_code == 404
>     assert anonymous.status_code == 401
>
>
> def test_public_schema_declares_scope_errors(client):
>     operation = client.get("/openapi.json").json()["paths"]["/api/reports/{report_id}"]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~
>
> 保存为 test_report_scope.py 后运行 python -m pytest -q test_report_scope.py。OpenAPI 检查说明本应用声明了哪些响应码；若要保证已有客户端兼容，仍需与已发布 schema 或代表性旧客户端比较。

若原实现只按 report_id 读取，tenant-b 的测试会得到 200，暴露缺失的租户条件。示例中 report_id 是全局主键，所以 SQLAlchemy 的 session.get(Report, 42) 能找到该行，但这不等于当前主体有权读取它；复合主键则需要不同的主键参数。修正后，所有者得到 200、越租户请求得到 404、匿名请求得到 401。相关授权规则见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

参数校验和旧客户端兼容也要分别验收：请求先通过认证后，`GET /api/reports/not-a-number` 由整数路径参数校验返回 422；没有可信主体的请求应在认证边界先得到 401。若既有客户端依赖响应中的 `state` 字段，应把上一版发布的 schema 或代表性请求/响应作为固定契约，删掉 `state` 时该契约测试应失败。当前 `/openapi.json` 只证明此版本声明了什么，不证明它仍兼容旧客户端。

> [!example] 唯一约束与重复投递的最小状态轨迹
> SQLite 演算的插入表以 `(tenant_id, request_key)` 为唯一键。首次插入影响 1 行；相同键再次插入触发唯一约束并回滚事务，查询仍只有原来的 1 行。这个约束例说明重复 insert 不会多建一行；它不等于 API 应对相同幂等键返回 409。报表接口若收到相同键和相同参数，应按[持久报表任务](../architecture/system-design-fundamentals.md)的契约读取并返回原 job；键相同但参数冲突时再按该业务契约拒绝。
>
> 对 worker 的本地条件更新，初始行是 `pending, processed_count=0`。第一次以 `WHERE status='pending'` 更新为 `done` 并递增计数，`rowcount=1`；再次执行同一条件时 `rowcount=0`；事务后最终状态仍为 `done, processed_count=1`。这证明选定 SQLite SQL 对重复函数调用只计一次，不证明 broker 的重投、ACK 或跨进程并发契约。

若 worker（工作进程）被本地函数调用两次，只能验证数据库状态迁移是否防重；它不覆盖消息是否被 broker 接收、连接中断后怎样重投或 ACK 是否可靠。若 worker 外发邮件、付款等副作用，还要让外部动作具备操作键幂等性或经持久 outbox 处理。任务与数据库结果边界见[超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md)；发布者确认与消费者 ACK 的 broker 语义见[消息交付如何确认](../reliability/queue-delivery-and-acknowledgement.md)。

## 从测试证据接到可发布的变更

测试通过只是证据链的一环。它应能指向变更需求、对应代码和具体测试数据；随后由 Git 提交固定源码快照，Docker 根据这个快照构建镜像，部署流水线再验证并晋级相同镜像。生产路径出现问题时，指标、trace 与日志用于定位是哪一环偏离。完整过程见[如何晋级已验证的报表服务产物？](../infrastructure/application-deployment-and-ci-cd.md)。

> [!info]- 来源
> - 测试方式的界限：FastAPI 官方 [Testing](https://fastapi.tiangolo.com/tutorial/testing/) 说明 TestClient 对应用路由的调用，checked 2026-11-06；pytest 官方 [Fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html) 说明 fixture 作用域和发现，checked 2026-11-06。
> - SQLite 约束与共享内存连接：SQLite [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)；SQLAlchemy 2.0 官方 [SQLite 内存数据库与连接池](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)，适用于本例的 StaticPool / check_same_thread 连接安排。
> - 本地运行边界：示例执行环境为 FastAPI 0.128.0、SQLAlchemy 2.0.44、pytest 9.0.2 与系统 SQLite；它不代表 PostgreSQL 或 broker 集成测试。
