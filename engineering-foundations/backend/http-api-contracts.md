# HTTP API Contracts / HTTP API契约

**Core idea / 核心模型：** An API contract makes a boundary predictable: it says which request shapes are accepted, which success representation is returned, and how clients recognize failures. Validate input at the boundary, keep response and error shapes intentional, and document pagination and evolution rules so clients do not infer behavior from implementation details. / API契约让接口边界可预期：明确接受哪些请求形状、成功时返回什么表示，以及客户端如何识别失败。在边界校验输入，明确设计响应与错误形状，并说明分页和演进规则，避免客户端依赖实现细节。

**Key terms / 关键术语：** request schema / 请求结构；response schema / 响应结构；boundary validation / 边界校验；problem details / 问题详情；machine-readable error / 机器可读错误；OpenAPI / OpenAPI描述；opaque cursor / 不透明游标；compatible evolution / 兼容演进。

## Separate HTTP semantics from API policy / 区分HTTP语义与API策略

An API contract sits above the transport: a route and method, its path/query/body inputs, response schemas, status outcomes, and pagination rules. HTTP defines the common message and status-code semantics; the API chooses the domain-specific representations and which status applies to each outcome. See [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) for method, status, and transport basics and [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md) for timeouts, retries, and unknown write outcomes.

A type annotation helps the application and framework understand values; it is not proof that an untrusted request has the right shape or meaning. Define request models and constraints at the boundary. Return a deliberate response model as well. Structural validation can reject a missing field or out-of-range number, but it cannot decide permission, resource ownership, uniqueness under concurrency, or whether a business action is allowed. Those rules need trusted authorization and domain logic; durable uniqueness belongs at the data boundary (see [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md)).

[OpenAPI](https://spec.openapis.org/oas/latest.html) describes operations, inputs, response codes, media types, and schemas in a machine-readable document. In FastAPI, request models and `response_model` contribute generated schemas; custom error handlers must also be represented in each operation's declared responses, or the runtime response and published contract can diverge. OpenAPI documents a contract; it does not validate deployed behavior by itself.

## Give failures a stable machine identity / 为错误提供稳定的机器标识

An API can use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) with `Content-Type: application/problem+json`. Its `type` URI is the primary identifier for a problem category; `status` in the body must match the HTTP response; `title` and `detail` are human-readable. Clients should not parse prose in `detail`. Put any stable client-action data in documented extension fields, such as a small `errors` array with a field path and an application-owned code. Avoid echoing raw request values or internal exception text.

The following status mapping is one API's policy, not a universal template:

| Outcome | Example response | Meaning in this API |
|---|---|---|
| Valid create | `201` + `Item` | A new item was created and its representation is returned. |
| Invalid body/query | `422` + problem | The JSON shape or a declared value constraint failed. This sample groups boundary-validation failures here. |
| Missing item | `404` + problem | No item currently has the requested ID. |
| Duplicate name | `409` + problem | The requested create conflicts with the current collection state. |
| Unknown cursor | `400` + problem | The client supplied a continuation token this process does not recognize. |

RFC 9110 describes `422` for syntactically valid content whose instructions cannot be processed and `409` for a conflict with current resource state. A different API may separate malformed JSON syntax as `400`, use a different validation status, or choose another duplicate policy; document the actual behavior and keep it consistent. The transport note covers the status definitions.

## Bound and continue a listing / 限制并继续分页

A list response should cap the number of returned records. This example accepts `limit` from 1 through 100, defaults it to 2 for the demonstration, and rejects a value above the maximum with a validation problem. Other API styles may clamp it to the maximum; [Google AIP-158](https://google.aip.dev/158) is one example that specifies coercion for oversized page sizes. The choice is policy: publish the default, maximum, and whether an oversized value is rejected or reduced.

This example includes `next_cursor` in every page: it is an opaque string when more results are available and JSON `null` at the end. Here, `null` is the terminal signal, so the client sends a non-null cursor back unchanged and stops when the value is null. A page may contain fewer rows than the requested limit without proving that the collection has ended. A token says where to continue, not who may read the rows: authenticate and authorize every page request. Use a stable order with a tie-breaker. If records can change during a long listing, define whether pages reflect a moving collection or a consistent snapshot.

The runnable example stores random cursor-to-offset mappings in memory for a tiny synthetic list. This makes the token opaque to the caller, but the token stops working after process restart and the in-memory list is not a scalable storage query. A production cursor needs a documented lifetime/consistency policy and a bounded storage query; the data-access design is separate from this note.

## Runnable contract example / 可运行的契约示例

The API uses a synthetic inventory collection. A Pydantic before-validator strips string input before the field's length constraints run, so whitespace-only input cannot become an empty stored name. / API使用合成库存集合。Pydantic前置验证器先去除字符串两端空白，再执行字段长度约束，因此全空白输入不会变成已保存的空名称。 The complete script below validates request and query boundaries, exposes success and error schemas, and checks the resulting HTTP behavior and OpenAPI document. Save it as `api_contract_demo.py` and run it in an environment with FastAPI and its TestClient dependencies.

~~~python
import secrets

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from typing import Any

from pydantic import BaseModel, Field, field_validator

PROBLEM_BASE = "https://api.example/problems/"


class CreateItem(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    quantity: int = Field(ge=1, le=1000)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class Item(BaseModel):
    id: int
    name: str
    quantity: int


class Page(BaseModel):
    items: list[Item]
    next_cursor: str | None = None


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    errors: list[dict[str, str]] | None = None


class ApiProblem(Exception):
    def __init__(self, status: int, kind: str, title: str, detail: str):
        self.status, self.kind, self.title, self.detail = status, kind, title, detail


def problem_content(description: str):
    return {
        "description": description,
        "content": {
            "application/problem+json": {"schema": Problem.model_json_schema()}
        },
    }


PROBLEM_RESPONSES = {
    400: problem_content("Unknown cursor"),
    404: problem_content("Item does not exist"),
    409: problem_content("Name already exists"),
    422: problem_content("Request validation failed"),
}
SEED = {
    1: Item(id=1, name="notebook", quantity=4),
    2: Item(id=2, name="pencil", quantity=8),
    3: Item(id=3, name="folder", quantity=2),
}
items = dict(SEED)
cursor_offsets: dict[str, int] = {}
next_id = 4
app = FastAPI()


def problem_response(status, kind, title, detail, **extensions):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": PROBLEM_BASE + kind,
            "title": title,
            "status": status,
            "detail": detail,
            **extensions,
        },
    )


@app.exception_handler(ApiProblem)
async def api_problem_handler(request: Request, exc: ApiProblem):
    return problem_response(exc.status, exc.kind, exc.title, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(part) for part in error["loc"]), "code": "invalid_value"}
        for error in exc.errors()
    ]
    return problem_response(
        422, "validation", "Request validation failed",
        "Correct the fields listed in errors and resubmit.", errors=errors,
    )


@app.get("/items", response_model=Page, responses=PROBLEM_RESPONSES)
async def list_items(limit: int = Query(default=2, ge=1, le=100), cursor: str | None = None):
    if cursor is None:
        offset = 0
    elif cursor in cursor_offsets:
        offset = cursor_offsets[cursor]
    else:
        raise ApiProblem(400, "invalid-cursor", "Invalid cursor", "Start a new listing.")

    ordered = [items[key] for key in sorted(items)]
    page = ordered[offset : offset + limit]
    next_cursor = None
    if offset + len(page) < len(ordered):
        next_cursor = secrets.token_urlsafe(12)
        cursor_offsets[next_cursor] = offset + len(page)
    return Page(items=page, next_cursor=next_cursor)


@app.get("/items/{item_id}", response_model=Item, responses=PROBLEM_RESPONSES)
async def get_item(item_id: int):
    if item_id not in items:
        raise ApiProblem(404, "not-found", "Item not found", "No item has this ID.")
    return items[item_id]


@app.post("/items", status_code=201, response_model=Item, responses=PROBLEM_RESPONSES)
async def create_item(payload: CreateItem):
    global next_id
    name = payload.name
    if any(item.name.casefold() == name.casefold() for item in items.values()):
        raise ApiProblem(409, "duplicate-name", "Name already exists", "Choose another name.")
    item = Item(id=next_id, name=name, quantity=payload.quantity)
    items[next_id] = item
    next_id += 1
    return item


def check():
    client = TestClient(app)
    first = client.get("/items?limit=2")
    assert first.status_code == 200 and len(first.json()["items"]) == 2
    cursor = first.json()["next_cursor"]
    assert cursor
    second = client.get("/items", params={"limit": 2, "cursor": cursor})
    assert second.status_code == 200
    assert [x["id"] for x in second.json()["items"]] == [3]
    second_body = second.json()
    assert "next_cursor" in second_body and second_body["next_cursor"] is None

    bad_page = client.get("/items?limit=101")
    assert bad_page.status_code == 422
    assert bad_page.headers["content-type"].startswith("application/problem+json")
    assert bad_page.json()["type"] == PROBLEM_BASE + "validation"
    assert bad_page.json()["errors"]

    malformed = client.post("/items", json={"name": "stapler", "quantity": 0})
    assert malformed.status_code == 422 and malformed.json()["type"] == PROBLEM_BASE + "validation"
    missing_field = client.post("/items", json={"name": "stapler"})
    assert missing_field.status_code == 422

    whitespace_name = client.post("/items", json={"name": "   ", "quantity": 1})
    assert whitespace_name.status_code == 422 and whitespace_name.json()["type"] == PROBLEM_BASE + "validation"

    created = client.post("/items", json={"name": " stapler ", "quantity": 2})
    assert created.status_code == 201 and created.json()["id"] == 4
    assert created.json()["name"] == "stapler"
    conflict = client.post("/items", json={"name": "Stapler", "quantity": 3})
    assert conflict.status_code == 409
    assert conflict.json()["type"] == PROBLEM_BASE + "duplicate-name"

    missing = client.get("/items/999")
    assert missing.status_code == 404
    assert missing.json()["type"] == PROBLEM_BASE + "not-found"
    invalid_cursor = client.get("/items?cursor=unknown-token")
    assert invalid_cursor.status_code == 400

    operation = app.openapi()["paths"]["/items"]["post"]
    assert operation["responses"]["201"]["content"]["application/json"]["schema"]
    assert operation["responses"]["409"]["content"]["application/problem+json"]["schema"]
    print("201 success trims names; invalid, missing, and whitespace-only input and limit 101 -> 422; missing item -> 404; duplicate -> 409")
    print("two pages contain 2+1 items; unknown cursor -> 400; final page includes next_cursor=null")
    print("OpenAPI", app.openapi()["openapi"], "documents JSON success and problem+json errors")


check()
~~~

The client reads a successful body according to `Item`/`Page`; on failure it checks the HTTP status and the stable problem `type`, then uses a documented extension such as `errors` to associate an issue with a field. It displays or logs `detail` for people without parsing it as a code. To continue, it passes a non-null `next_cursor` back unchanged and stops when the field's value is JSON `null`.

## Evolve the contract deliberately / 有计划地演进契约

Adding an optional response field is often compatible when clients ignore unknown fields, but generated clients and strict decoders can reject it. Removing or renaming a field, changing its type or meaning, making an optional request field required, changing a problem `type`, or changing pagination meaning can break callers. Treat these as contract changes: publish the compatibility policy, test representative old and new clients, and use a versioning or migration window when an incompatible change is necessary. There is no single mandatory versioning scheme.

## Interview answers / 面试回答

**How would you make an API failure usable by both a client and a person? / 如何让API错误同时适合程序与人阅读？** I would keep the HTTP status meaningful, return a stable problem `type`, and document the response media type and schema in OpenAPI. Human text can explain the immediate issue, but clients branch on the stable identifier or a documented extension rather than parsing that text. I would avoid reflecting secrets or exception details and test that runtime responses match the published schema.

我会让HTTP状态码有明确含义，返回稳定的问题`type`，并在OpenAPI中说明响应媒体类型和结构。人类可读文本可以解释当前问题，但客户端应根据稳定标识或有文档约定的扩展字段分支，而不是解析这段文本。我会避免回显机密或异常细节，并测试运行时响应是否符合已发布的结构。

**How should a client know when a page is finished? / 客户端如何判断分页结束？** It should follow the server-issued opaque cursor and stop when `next_cursor` is present with JSON `null`; page length alone is not a reliable end signal. The API should bound the page size, order records deterministically, and re-check authorization for every page. Cursor lifetime and behavior during concurrent updates are explicit API choices.

客户端应原样传回服务端签发的不透明游标，并在`next_cursor`字段存在且值为JSON`null`时停止；单靠当前页长度不能可靠判断结束。API应限制页大小、按确定顺序排列记录，并对每一页重新授权。游标有效期以及并发更新时的行为都应作为明确的接口策略定义。

**Sources / 来源：** [OpenAPI Specification, latest](https://spec.openapis.org/oas/latest.html); IETF [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html); [RFC 9110 §15.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5) for 404, 409, and 422 semantics; Google [AIP-158, Pagination](https://google.aip.dev/158) as one pagination style; FastAPI [request bodies and validation](https://fastapi.tiangolo.com/tutorial/body/), [response models](https://fastapi.tiangolo.com/tutorial/response-model/), and [handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/); Pydantic 2.11 [field validators](https://docs.pydantic.dev/2.11/concepts/validators/), checked against a FastAPI 0.128.0 / Pydantic 2.11.7 runtime on 2026-10-15. In that installed runtime, `app.openapi()["openapi"]` returned `3.1.0`; the live OpenAPI `latest` document resolved to `3.2.1`, so the sample reports its actual generated version instead of assuming the framework emits the newest specification.

**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) covers the transport and generic status semantics; [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md) covers timeouts, retries, and ambiguous side effects; [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers durable uniqueness and transaction boundaries.
