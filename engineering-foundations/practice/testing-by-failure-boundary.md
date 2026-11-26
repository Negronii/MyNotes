# 一次改动该在哪一层测试，怎样证明测试能区分对错？

本章回答：一次改动该用哪种测试去验证，测试通过之后能声称什么、不能声称什么，以及怎样证明一组测试真能把正确实现和错误实现分开。读者手上有上一章的读取契约表、最小反例和修复后的代码。

**案例。** 沿用主线五的报表服务修复，契约表与反例来自[怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](debugging-and-code-review.md)。这次改动要守住两条契约：

- **读取范围。** `user-17` 读 acct-17 的报表 42 得到 `200`；`user-29` 经自己的账户 acct-29 读 42，得到与读不存在的 43 完全相同的通用 `404`。
- **重复处理。** 同一个导出任务被投递两次时，数据库只允许一次有效的状态转换。导出请求的幂等键是 `export-demo-415`，对应任务 `job-demo-731`；任务状态是 `queued/running/succeeded/failed/cancelled`。

下面的示例用 SQLite 和进程内的 `TestClient` 演示路由与 SQL 层的本地证据；这些证据不能推广到 PostgreSQL、消息代理或生产身份系统，后文按测试边界逐一说明。

## 测试边界由要排除的失败决定

测试边界指一次测试实际纳入的真实组件范围。选边界的方法是：先写清要守住的业务条件和可观察结果，再选一个**刚好包含可能出错组件**的最小环境。只有较小的边界证明不了目标性质时，才加大环境。下表是互相补充的检查位置，不是每次改动都要依次跑完的固定层级：

| 要排除的失败 | 测试边界 | 能看到的证据 | 不能据此声称 |
| --- | --- | --- | --- |
| 访问规则本身写反（成员与非成员判断颠倒） | 单元测试 | 给定可信主体和资源归属，规则返回允许或拒绝 | 实际路由调用了这条规则 |
| 路由丢了账户条件、状态码或响应字段错误 | API 集成 | 真实路由、测试身份接缝、参数校验、数据库查询、序列化和错误映射一起工作 | 真实网络、生产身份提供方或生产数据库方言正常 |
| 唯一约束、回滚或条件更新的实际数据库行为错误 | 数据库集成 | 选定数据库执行真实表结构和 SQL | 另一种数据库有相同的类型、锁或并发行为 |
| 新响应不兼容已发布的客户端 | 契约测试 | 当前响应与已发布 schema 或代表性旧客户端的期望比较 | 只看本次生成的 OpenAPI 就证明兼容 |
| 消息发布、重复投递或 ACK 路径丢失或重复执行 | 消息代理集成 | 选定代理在其路由、持久性和确认设置下的实际交接 | 本地把 worker 函数调用两次就等于代理完成了重投 |
| 只有各服务装配起来才出现的故障 | 近生产端到端 | 受控身份、API、数据库、队列和 worker 组成的完整旅程 | 一个健康探针就证明用户旅程正确 |

本章后面展开 API 集成和数据库集成两行。另外三行在本案例里各有一个具体用法：

**契约测试。** 已发布的客户端依赖响应里的哪些字段，要用标明必需字段的已发布 schema，或旧客户端依赖的固定响应样例来比较。本服务生成的 OpenAPI 只描述“现在”的声明，不记得过去答应过什么（见后文 OpenAPI 一节）。字段该怎样演进、什么算破坏性变更，见[怎样让调用方可靠地判断 API 的成功、失败和变化？](../services/api-contracts-errors-and-evolution.md)。

**消息代理集成。** 要证明“worker 没确认就崩溃时，消息会被重新投递，而重复投递只推进一次状态”，必须让真实代理参与：用与生产相同的确认模式消费消息，在 ACK 之前终止消费者，再观察代理重新投递，以及数据库里的条件更新只成功一次。在本地把处理函数连调两次，只验证了数据库那一半。代理的确认语义见[发布确认、消费者确认和业务完成各证明什么？](../services/queue-delivery-and-acknowledgement.md)。

**近生产端到端。** 部署装配上的错误（配置、凭据、网络、服务之间的版本组合）只有装起整条链路才会出现。旅程要用受控的身份走完“读取—导出—下载”，而不是看一个健康探针是否返回 `200`。发布后的生产冒烟用 `user-17`、`user-29` 两个受控身份钉到新版本上，属于同一类检查，见[新版本怎样逐步放量，出问题时能撤回什么？](canary-rollout-and-rollback.md)。

浏览器侧的测试边界见[前端测试该在哪一层证明什么？](../../frontend/delivery/frontend-testing-strategy.md)。

## 测试必须能区分对错

一组测试有没有用，不看它是否通过，而看它能不能把正确实现和错误实现分开。原有测试只让 `user-17` 读自己的报表：查询退化成只按全局主键读取后，它照样通过。这样的测试对这类回归没有任何区分力。

**判据：删掉条件，测试必须失败。** 证明区分力的方法很直接：把要守的条件从实现里拿掉（或换回已知错误的写法），至少一条测试必须变红。思路与 mutation testing (变异测试) 相同：人为制造一个已知错误的版本，看测试能否把它“杀死”。本例中，把查询换回 `session.get(Report, report_id)` 后，所有者那条检查仍然通过，只有 `user-29` 经 acct-29 读 42 的那条失败。正是这条跨账户反例承担了全部区分力。

**断言要精确到能排除泄露。** 只断言 `404` 不够；要断言 `user-29` 读 42 的正文与读不存在的 43 完全相同，才能证明响应没有带出 acct-17 的数据或归属。

**独立阅读实现与测试。** 同一个人或同一个 AI 模型同时写出的实现和测试，可能共享同一个遗漏的假设，测试全绿不说明漏掉的条件已经被检查。审查时，从需求列出“哪些请求必须被拒绝”，再分别读实现和测试：

- **实现侧**：改动后的公开路由、调用方、认证依赖、实际读取（SQL 查询还是 identity map 返回）、事务、缓存和响应分支。
- **测试侧**：是否用了归属不同的可信主体；是否经过被修改的入口；fixture (测试夹具) 接的是不是预期的数据库；断言有没有检查“不该发生的成功响应”。

**每种替身只覆盖自己那一层。** 模拟的会话、本地的重复调用、健康探针，各自只证明它所在那一层的事实。结论若涉及数据库约束、消息代理重投或部署装配，先确认测试真的用了目标数据库、真实代理或部署路径。

## API 集成测试：保留真实路由，只替换身份

读取契约要用 API 集成测试验证：真实的路由、成员检查、查询、序列化和错误映射都参与，只有“当前主体是谁”由测试提供。示例定义了一个测试专用依赖，从请求头 `X-Test-Principal` 读取主体。它只是测试接缝（为测试预留的替换点），不是生产认证：生产环境的主体必须来自已验证的会话或令牌，不能信任客户端填写的请求头。对已有的 FastAPI 应用，也可以在测试里用 `app.dependency_overrides` 替换认证依赖，同时保留真实路由。

示例把契约表写成一个函数 `contract_violations`，逐条重放并返回违反的条目；同一个函数分别跑在修复后的实现和回归实现上：

| 实现 | `contract_violations` 的结果 | 说明 |
| --- | --- | --- |
| 显式查询 `(account_id, report_id)` | `[]` | 三条读取契约全部满足 |
| `session.get(Report, report_id)` | `["user-29 经 acct-29 读 42"]` | `user-29` 得到 `200` 和 `Service health`；所有者检查和经 acct-17 的那条仍通过 |

第二行就是区分力的证据：回归实现只在跨账户反例上失败。实际项目里不必把回归实现永久留在测试套件中，在审查时临时换回一次、确认测试变红即可；示例保留它，是为了让这次判定可以重放。

另外三项边界各自验收：

- **认证。** 不带主体的请求得到 `401`，并断言 `WWW-Authenticate: Bearer realm="reports"` 质询头（本例假设生产用 Bearer 令牌；真实令牌校验由认证层自己的测试负责）。
- **参数校验。** `GET /v1/accounts/acct-17/reports/not-a-number` 因整数路径参数校验失败得到 `422`。
- **进程内调用的边界。** `TestClient` 在进程内调用应用，不建立真实的 HTTP socket；但 SQLAlchemy 会把查询交给 SQLite 真正执行，所以查询条件是真的被检验了。

本例为简化，错误正文用 FastAPI 默认的 `{"detail": "report not found"}`；生产 API 的错误格式见 API 契约章。认证之后的逐次授权规则（成员、动作、缓存与后台任务）见[服务怎样逐次确认这个主体能对这份资源做这个动作？](../services/per-request-authorization.md)。

> [!example]- 完整 FastAPI + SQLAlchemy + SQLite 测试（`test_report_scope.py`）
> 每个测试由 function scope (函数作用域) 的 fixture 建立独立的内存数据库和应用。`StaticPool` 让串行访问复用同一个 SQLite 连接，使路由读到已准备的数据；它不支持并发事务，这组设置不能用于并发测试。运行：`python -m pytest -q test_report_scope.py`，预期 `4 passed`。
>
> ~~~python
> from typing import Annotated, Callable
>
> import pytest
> from fastapi import Depends, FastAPI, Header, HTTPException
> from fastapi.testclient import TestClient
> from sqlalchemy import create_engine, select
> from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
> from sqlalchemy.pool import StaticPool
>
>
> class Base(DeclarativeBase):
>     pass
>
>
> class Report(Base):
>     __tablename__ = "reports"
>     report_id: Mapped[int] = mapped_column(primary_key=True)  # 本例：全局主键
>     account_id: Mapped[str]
>     title: Mapped[str]
>
>
> class Membership(Base):
>     __tablename__ = "memberships"
>     account_id: Mapped[str] = mapped_column(primary_key=True)
>     principal_id: Mapped[str] = mapped_column(primary_key=True)
>
>
> def scoped_read(session: Session, account_id: str, report_id: int):
>     return session.scalar(
>         select(Report).where(
>             Report.account_id == account_id,
>             Report.report_id == report_id,
>         )
>     )
>
>
> def regressed_read(session: Session, account_id: str, report_id: int):
>     return session.get(Report, report_id)  # 回归：只按全局主键
>
>
> def create_app(read_row: Callable) -> FastAPI:
>     engine = create_engine(
>         "sqlite+pysqlite://",
>         connect_args={"check_same_thread": False},
>         poolclass=StaticPool,
>     )
>     Base.metadata.create_all(engine)
>     with Session(engine) as session, session.begin():
>         session.add_all([
>             Membership(account_id="acct-17", principal_id="user-17"),
>             Membership(account_id="acct-29", principal_id="user-29"),
>             Report(report_id=42, account_id="acct-17", title="Service health"),
>         ])
>
>     app = FastAPI()
>     app.state.engine = engine
>
>     def principal_from_test_header(
>         x_test_principal: Annotated[str | None, Header()] = None,
>     ) -> str:
>         # 测试接缝：生产环境的主体来自已验证的会话或令牌，不来自请求头
>         if not x_test_principal:
>             raise HTTPException(
>                 status_code=401,
>                 detail="authentication required",
>                 headers={"WWW-Authenticate": 'Bearer realm="reports"'},
>             )
>         return x_test_principal
>
>     @app.get(
>         "/v1/accounts/{account_id}/reports/{report_id}",
>         responses={401: {"description": "Unauthenticated"}, 404: {"description": "Not found"}},
>     )
>     def read_report(
>         account_id: str,
>         report_id: int,
>         principal: Annotated[str, Depends(principal_from_test_header)],
>     ):
>         with Session(engine) as session:
>             member = session.scalar(
>                 select(Membership).where(
>                     Membership.account_id == account_id,
>                     Membership.principal_id == principal,
>                 )
>             )
>             report = read_row(session, account_id, report_id) if member else None
>             if report is None:
>                 raise HTTPException(status_code=404, detail="report not found")
>             return {"report_id": report.report_id, "title": report.title}
>
>     return app
>
>
> def contract_violations(client: TestClient) -> list[str]:
>     """按读取契约逐条重放，返回违反的条目；空列表表示全部满足。"""
>     def get(principal: str, path: str):
>         return client.get(path, headers={"X-Test-Principal": principal})
>
>     missing = get("user-29", "/v1/accounts/acct-29/reports/43")
>     checks = {
>         "user-17 读自己账户的 42":
>             lambda r: r.status_code == 200
>             and r.json() == {"report_id": 42, "title": "Service health"},
>         "user-29 经 acct-29 读 42":
>             lambda r: r.status_code == 404 and r.json() == missing.json(),
>         "user-29 经 acct-17 读 42":
>             lambda r: r.status_code == 404 and r.json() == missing.json(),
>     }
>     responses = {
>         "user-17 读自己账户的 42": get("user-17", "/v1/accounts/acct-17/reports/42"),
>         "user-29 经 acct-29 读 42": get("user-29", "/v1/accounts/acct-29/reports/42"),
>         "user-29 经 acct-17 读 42": get("user-29", "/v1/accounts/acct-17/reports/42"),
>     }
>     return [name for name, ok in checks.items() if not ok(responses[name])]
>
>
> @pytest.fixture
> def client():
>     app = create_app(scoped_read)
>     with TestClient(app) as test_client:
>         yield test_client
>     app.state.engine.dispose()
>
>
> def test_scoped_read_meets_contract(client):
>     assert contract_violations(client) == []
>
>
> def test_contract_detects_regressed_read():
>     app = create_app(regressed_read)
>     with TestClient(app) as regressed:
>         assert contract_violations(regressed) == ["user-29 经 acct-29 读 42"]
>     app.state.engine.dispose()
>
>
> def test_authentication_and_validation(client):
>     anonymous = client.get("/v1/accounts/acct-17/reports/42")
>     malformed = client.get(
>         "/v1/accounts/acct-17/reports/not-a-number",
>         headers={"X-Test-Principal": "user-17"},
>     )
>     assert anonymous.status_code == 401
>     assert anonymous.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert malformed.status_code == 422
>
>
> def test_openapi_declares_error_responses(client):
>     operation = client.get("/openapi.json").json()["paths"][
>         "/v1/accounts/{account_id}/reports/{report_id}"
>     ]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~

## 自动生成的 OpenAPI 不证明兼容

示例里的 `test_openapi_declares_error_responses` 检查本应用声明了 `200/401/404/422` 四种响应。它只说明“当前声明了什么”。本例路由没有设置 `response_model`，生成的 200 响应 schema 是 `{}`，没有把 `title` 标为必需字段；即使有人删掉 `title`，这条 OpenAPI 检查照样通过。

在本例里，能发现字段被删的是契约函数中那条精确的 JSON 断言。要验证已发布客户端的兼容性，仍要拿标明必需字段的已发布 schema，或旧客户端依赖的固定响应来比较。

## 重复处理：用约束和条件更新守住，并精确断言

第二条契约靠数据库守住，需要数据库集成测试。它有两半：

- **重复提交。** 幂等记录以 `(account_id, principal_id, idempotency_key)` 为主键。同一个 `(acct-17, user-17, export-demo-415)` 再次插入时必须撞上主键，原映射 `job-demo-731` 保持不变。应用层随后怎样回查并返回原任务，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](../data/conditional-writes-and-idempotent-records.md)。
- **重复投递。** worker 用条件更新领取任务：只有 `status = 'queued'` 的行才能改成 `running` 并把 `attempt` 加一。第一次影响 1 行，第二次影响 0 行。

| 操作 | 数据库返回的信号 | 之后保留的状态 |
| --- | --- | --- |
| 首次受理：插入幂等记录 → `job-demo-731`，插入任务 `queued`、`attempt=0` | 影响 1 行 | 两行都已提交 |
| 同键重放，换成候选任务 `job-duplicate` 再插入 | `SQLITE_CONSTRAINT_PRIMARYKEY`，事务回滚 | 原映射仍指向 `job-demo-731`，没有多出一行 |
| 第一次投递：`queued → running` | 影响 1 行 | `running`、`attempt=1` |
| 第二次投递，同样的条件 | 影响 0 行 | 仍是 `running`、`attempt=1` |

**断言要精确，否则会假阳性。** 冲突测试要断言具体的错误码和完整的原行：

- 只数“仍是一行”：如果实现用了 `INSERT OR REPLACE`，原行被删掉、换成指向 `job-duplicate` 的新行，行数仍是 1，测试照样通过。
- 只捕获任意 `IntegrityError`：非空约束失败（`SQLITE_CONSTRAINT_NOTNULL`）也是 `IntegrityError`，会被误当成主键冲突。

**这组测试不能声称什么。** 它是串行的轨迹，不能据此说多个 worker 并发争用时的行为已经测过；它没有连接消息代理，本地执行两次更新不等于代理完成了重投。真实的领取还要先占执行槽、检查 `available_at`、设置租约，完整条件见[怎样保证一个任务同一时刻只由一个 worker 推进？](../services/job-claims-leases-and-fencing.md)。

> [!example]- 用标准库 SQLite 重放唯一键与条件领取
> 这段独立示例只执行本地数据库约束，没有消息代理，也没有并发 worker。运行 `python dedupe.py`，预期输出 `SQLITE_CONSTRAINT_PRIMARYKEY 1 0 ('job-demo-731', 'running', 1)`。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> db.executescript("""
> CREATE TABLE idempotency_records (
>     account_id      TEXT NOT NULL,
>     principal_id    TEXT NOT NULL,
>     idempotency_key TEXT NOT NULL,
>     job_id          TEXT NOT NULL,
>     PRIMARY KEY (account_id, principal_id, idempotency_key)
> );
> CREATE TABLE jobs (
>     job_id  TEXT PRIMARY KEY,
>     status  TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
>     attempt INTEGER NOT NULL
> );
> """)
> record = ("acct-17", "user-17", "export-demo-415")
>
> # 首次受理：幂等记录与 job 同一事务提交
> with db:
>     first_insert = db.execute(
>         "INSERT INTO idempotency_records VALUES (?, ?, ?, ?)", (*record, "job-demo-731")
>     ).rowcount
>     db.execute("INSERT INTO jobs VALUES ('job-demo-731', 'queued', 0)")
>
> # 同键重放却带着新的候选 job：必须撞上主键，而不是替换原映射
> try:
>     with db:
>         db.execute(
>             "INSERT INTO idempotency_records VALUES (?, ?, ?, ?)", (*record, "job-duplicate")
>         )
> except sqlite3.IntegrityError as error:
>     conflict = error.sqlite_errorname
> else:
>     raise AssertionError("duplicate key was accepted")
>
> assert conflict == "SQLITE_CONSTRAINT_PRIMARYKEY", conflict
> assert db.execute("SELECT * FROM idempotency_records").fetchall() == [(*record, "job-demo-731")]
>
> # 同一 job 被投递两次：只有一次 queued -> running 能成功
> claim = (
>     "UPDATE jobs SET status = 'running', attempt = attempt + 1 "
>     "WHERE job_id = 'job-demo-731' AND status = 'queued'"
> )
> with db:
>     first_claim = db.execute(claim).rowcount
> with db:
>     second_claim = db.execute(claim).rowcount
>
> assert (first_insert, first_claim, second_claim) == (1, 1, 0)
> assert db.execute("SELECT * FROM jobs").fetchall() == [("job-demo-731", "running", 1)]
> print(conflict, first_claim, second_claim, db.execute("SELECT * FROM jobs").fetchone())
> ~~~

## 本地测试管不到的两件事

**远端副作用。** 如果重复处理的任务还会付款、发邮件或通知其他服务，本地条件更新撤回不了已经发生的远端动作。transactional outbox (事务发件箱，之后 outbox) 让业务行与待发消息在同一事务里提交，但 relay (中继) 故障恢复后仍可能再发一次；所以外部动作还要带上对端认可的幂等键，或事后对照权威记录对账修复。单靠 outbox 挡不住远端的重复付款。远端操作键怎样构造、结果不明时怎样决策，见[写请求超时后，怎样查清结果并安全重试？](../services/deadlines-retries-and-unknown-outcomes.md)；outbox 本身见[耗时任务怎样被持久受理，并保证一定会被唤醒？](../services/durable-job-acceptance-and-outbox.md)。

**测试证据要追溯到产物。** 测试通过之后，改动还要经过提交、构建和发布。测试结果应能追溯到对应的提交、测试输入和实际产物：CI 固定一个源码提交，用该快照构建镜像，发布流程晋级的是同一份通过检查的镜像。不能把“源码上的测试通过”说成另一次重新构建的镜像也验证过了，见[已验证的产物怎样原样晋级到生产？](build-once-promote-by-digest.md)。

## 本章产出与下一步

本章产出一组有区分力的测试：契约函数在修复后的实现上返回 `[]`，在 `Session.get` 回归上只报告跨账户那一条；重复提交与重复投递由主键和条件更新守住，断言精确到错误码和原行。测试边界表说明了它们各自证明到哪一层为止。

这组测试读的是工作区里的文件。下一章[Git 怎样记录一次改动，出错时又怎样按层撤回？](git-snapshots-and-recovery.md)回答：怎样保证被测的那份内容，正是要提交、要交给 CI 构建的那份快照。

> [!info]- 来源
> - **TestClient 在进程内调用应用、不建立真实 socket**（“API 集成测试”）：FastAPI, [Testing](https://fastapi.tiangolo.com/tutorial/testing/)、[TestClient 参考](https://fastapi.tiangolo.com/reference/testclient/)，核对于 2026-11-12。
> - **用 `dependency_overrides` 替换认证依赖、保留真实路由**（“API 集成测试”）：FastAPI, [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)，核对于 2026-11-12。
> - **响应模型决定 OpenAPI schema；未设 `response_model` 时 200 schema 为 `{}`**（“自动生成的 OpenAPI 不证明兼容”）：FastAPI, [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)，核对于 2026-11-12；`{}` 为本地运行结果。
> - **fixture 注入与默认 function scope**（完整测试折叠块）：pytest, [How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)，核对于 2026-11-12。
> - **SQLite 内存库与 `StaticPool` 只适合串行访问**（完整测试折叠块）：SQLAlchemy 2.0, [SQLite dialect — Using a Memory Database in Multiple Threads](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)，核对于 2026-11-12。
> - **主键与唯一约束；`REPLACE` 会删除冲突的原行；扩展错误码区分主键与非空约束**（“重复处理”）：SQLite, [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)、[ON CONFLICT](https://sqlite.org/lang_conflict.html)、[Result and Error Codes](https://www.sqlite.org/rescode.html)，核对于 2026-11-12。
> - **Bearer 质询的认证参数**（“API 集成测试”的 401 断言）：IETF [RFC 6750 §3](https://www.rfc-editor.org/rfc/rfc6750.html#section-3)；401 必须带适用的 `WWW-Authenticate`：[RFC 9110 §15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2)，核对于 2026-11-12。
> - **outbox 的本地原子写入不消除重复消息**（“本地测试管不到的两件事”）：AWS Prescriptive Guidance, [Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-12。
> - **发布确认与消费者 ACK 是不同的交接边界**（“测试边界”表的消息代理一行）：RabbitMQ 4.4, [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-12。**消费者未 ACK 就终止（通道或连接关闭）时，消息重新入队并再投递**（“消息代理集成”）：RabbitMQ, [Tutorial 2: Work Queues — Message acknowledgment](https://www.rabbitmq.com/tutorials/tutorial-two-python)，核对于 2026-11-25。本章示例没有执行 RabbitMQ。
> - **本地运行环境**：Python 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1、SQLAlchemy 2.0.44、pytest 9.0.2、SQLite 3.51.0。版本只描述本次复现环境。
