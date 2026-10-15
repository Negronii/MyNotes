# Software Testing Strategy / 软件测试策略

**Core explanation / 核心解释：** Put each assertion at the boundary that can prove the behavior the risk depends on. Unit tests isolate rules; API tests connect the actual route, validation, response, and principal seam; a real database must execute SQL before a test can prove a constraint or transaction. Include the broker or deployed system when its delivery or wiring is the risk. A green test proves only the code and environment it exercised. / 单元测试隔离纯规则；API 测试连接真实路由、输入校验、响应和主体接缝；要证明约束或事务，必须让真实数据库执行 SQL，mock 只能验证交互。若风险来自 broker 重投或部署后的链路，就要把对应服务纳入测试；SQLite 和重复调用 handler 不能证明 PostgreSQL 或 broker 语义。测试通过只覆盖它实际触达的代码和环境。

**Key terms / 关键术语：** unit test / 单元测试；integration test / 集成测试；compatibility contract / 兼容性契约；end-to-end (E2E) test / 端到端测试；fixture / 测试夹具；test seam / 测试接缝；test double / 测试替身。

## Choose the boundary from the failure risk / 按故障风险选择测试边界

| Risk | Useful boundary | Evidence that boundary can provide |
|---|---|---|
| A pure rule maps input to the wrong result | Unit | The rule's inputs and outputs, with unrelated I/O absent. |
| A route validates the wrong shape, returns the wrong status, or skips tenant authorization | API integration | The actual router, request validation, dependency path, response serialization, and error mapping. An in-process client does not exercise a network socket or production identity provider. |
| Duplicate keys, rollback, or a conditional update violate a durable invariant | Database integration | The selected database engine executes the schema and statements. A mock session cannot prove a constraint or transaction. |
| An existing consumer can no longer read a response | Compatibility contract | Compare a pinned or published schema and representative consumer expectations with the provider's current output. Checking only a freshly generated schema does not prove compatibility with an older client. |
| A queue redelivery or acknowledgement order causes a duplicate or lost effect | Broker integration | The configured broker, acknowledgement mode, consumer, and durable store exercise the delivery boundary. Calling a handler twice tests its database behavior, not broker delivery guarantees. |
| Login, API, database, and worker wiring fail only when assembled | End-to-end | A controlled deployed-like journey with the actual selected services and identities. It is slower and narrower in number; use it for failures that depend on that wiring. |

These are complementary boundaries, not a required test-count pyramid. Keep quick, deterministic checks close to the risk, then add a higher-boundary check only when it proves something the lower one cannot. The existing [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md) note owns Jest, component, browser, and frontend release examples; this note applies the same risk-and-feedback idea to API, persistence, and delivery boundaries.

## One job API with a database-backed worker / 一个带数据库 worker 的任务 API

The small example below creates a tenant-owned job. `POST /jobs` validates a request and gives the same tenant's request key a database uniqueness rule. `GET /jobs/{id}` scopes lookup by the current tenant. A worker delivery changes `pending` to `done` with one conditional database update; replaying the same job ID must not increment the effect counter twice.

The fixture creates a fresh in-memory SQLite database for each test and keeps it on one shared connection so the in-process test client and the test's database inspection see the same database. The `Session` dependency and worker's session-factory argument are deliberate seams: they control database lifetime while still executing real SQL against SQLite. `X-Tenant-ID` stands in for a principal supplied by trusted authentication middleware; it is a test input, not an authentication scheme to trust in a deployed service. For the general authorization rule, see [Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md). The queue call is represented by calling the worker twice; no broker is present.

~~~python
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy import Integer, String, UniqueConstraint, create_engine, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_key", name="uq_job_tenant_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(60), nullable=False)
    request_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class JobCreate(BaseModel):
    request_key: str = Field(min_length=1, max_length=64)
    payload: str = Field(min_length=1, max_length=200)


class JobView(BaseModel):
    id: int
    request_key: str
    state: str
    processed_count: int


def tenant_from_test_header(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return x_tenant_id


def get_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def create_app() -> FastAPI:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI()
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.post(
        "/jobs",
        status_code=201,
        response_model=JobView,
        responses={
            401: {"description": "Authentication required"},
            409: {"description": "Request key already exists for this tenant"},
        },
    )
    def create_job(
        body: JobCreate,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        try:
            with session.begin():
                job = Job(
                    tenant_id=tenant_id,
                    request_key=body.request_key,
                    payload=body.payload,
                )
                session.add(job)
                session.flush()
                response = JobView(
                    id=job.id,
                    request_key=job.request_key,
                    state=job.state,
                    processed_count=job.processed_count,
                )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="request key already exists")
        return response

    @app.get("/jobs/{job_id}", response_model=JobView)
    def read_job(
        job_id: int,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        job = session.scalar(
            select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
        )
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return JobView(
            id=job.id,
            request_key=job.request_key,
            state=job.state,
            processed_count=job.processed_count,
        )

    return app


def deliver_job(session_factory, job_id: int) -> str:
    with session_factory() as session, session.begin():
        result = session.execute(
            update(Job)
            .where(Job.id == job_id, Job.state == "pending")
            .values(state="done", processed_count=Job.processed_count + 1)
        )
        if result.rowcount == 1:
            return "processed"
        return "duplicate" if session.get(Job, job_id) is not None else "missing"


@pytest.fixture
def app():
    application = create_app()
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def headers(tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


def test_api_schema_auth_and_tenant_scope(client):
    body = {"request_key": "daily-7", "payload": "sample"}
    assert client.post("/jobs", json=body).status_code == 401
    assert client.post(
        "/jobs", headers=headers("tenant-a"), json={"request_key": "", "payload": "x"}
    ).status_code == 422

    created = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert created.status_code == 201
    assert set(created.json()) == {"id", "request_key", "state", "processed_count"}
    assert created.json()["state"] == "pending"

    job_id = created.json()["id"]
    own_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    other_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-b"))
    assert own_read.status_code == 200
    assert other_read.status_code == 404


def test_openapi_exposes_the_public_request_and_response_shape(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/jobs"]["post"]
    assert {"201", "401", "409", "422"} <= set(operation["responses"])
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = operation["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = schema["components"]["schemas"][request_ref.rsplit("/", 1)[1]]
    response_schema = schema["components"]["schemas"][response_ref.rsplit("/", 1)[1]]
    assert set(request_schema["properties"]) == {"request_key", "payload"}
    assert set(response_schema["properties"]) == {"id", "request_key", "state", "processed_count"}


def test_database_unique_constraint_rolls_back_duplicate_create(client, app):
    body = {"request_key": "daily-7", "payload": "sample"}
    first = client.post("/jobs", headers=headers("tenant-a"), json=body)
    duplicate = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert first.status_code == 201
    assert duplicate.status_code == 409

    with Session(app.state.engine) as session:
        count = session.scalar(select(func.count()).select_from(Job))
    assert count == 1


def test_replayed_worker_delivery_changes_database_once(client, app):
    created = client.post(
        "/jobs",
        headers=headers("tenant-a"),
        json={"request_key": "daily-8", "payload": "sample"},
    )
    job_id = created.json()["id"]

    assert deliver_job(app.state.session_factory, job_id) == "processed"
    assert deliver_job(app.state.session_factory, job_id) == "duplicate"
    result = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    assert result.json()["state"] == "done"
    assert result.json()["processed_count"] == 1
~~~

Extract that block into `test_jobs.py` and run `python -m pytest -q test_jobs.py`. The tests assert visible API behavior, the request and response schema exposed by this app, an actual SQLite uniqueness violation with rollback, and a repeated worker call against the same database. The OpenAPI assertion checks this version's declared shape; a compatibility gate should compare with a released schema or exercise a real supported consumer before claiming an older client remains compatible.

The database is SQLite 3.51.0 through SQLAlchemy 2.0.44. This is a real database engine and the test executes its unique constraint and transaction, but its locking, typing, SQL dialect, and concurrency behavior do not establish PostgreSQL behavior. `TestClient` exercises FastAPI through an in-process ASGI transport, not a live server, network, production authentication provider, or deployed application. `deliver_job` exercises a repeated database operation; it does not prove a broker's redelivery, acknowledgement, ordering, or outage guarantees. Those claims need a broker-backed integration test using the selected broker's configuration. External side effects such as email or payment also need an outbox or downstream idempotency boundary; this example changes only local database state. For retry and acknowledgement semantics, see [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md); for the session and transaction lifecycle, see [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md).

**Interview answer / 面试回答：** I start from the failure risk and choose the lowest boundary that can prove it. Here the API tests verify validation, public response shape, and tenant-scoped access; a real SQLite database verifies uniqueness and rollback; the repeated worker call verifies the local idempotent state transition. I would add a contract comparison for compatibility and a broker-backed test before claiming delivery or acknowledgement guarantees. / 我先从故障风险出发，选择能够证明该风险的最低边界。这个例子用 API 测试验证输入校验、公开响应结构和租户范围访问，用真实 SQLite 验证唯一性约束与回滚，再用重复 worker 调用验证本地幂等状态变更。要声称兼容既有客户端或消息投递确认语义，还需要契约对比和真实 broker 测试。

**Sources checked 2026-10-15:** [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) and [testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) for in-process request checks and dependency seams; [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) for function-scoped setup and cleanup; SQLAlchemy 2.0 [constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html), [session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), and [SQLite pooling](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines); SQLite [CREATE TABLE and UNIQUE constraints](https://www.sqlite.org/lang_createtable.html) and [transactions](https://www.sqlite.org/lang_transaction.html). Runtime behavior was checked with the versions recorded above; the live FastAPI documentation is not a substitute for the named runtime check.
