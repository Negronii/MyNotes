# How do you prevent cross-tenant access across a web request? / 如何防止 Web 请求跨租户访问？

**身份认证 / Authentication** establishes which identity or credential is presenting a request. **授权 / Authorization** decides whether that identity may perform this action on this resource. Authentication alone does not grant every permission; enforce authorization on the server for each protected operation. Client checks can improve the interface but cannot decide access.

身份认证回答请求以谁的凭据发出，授权则逐项决定该身份能否访问资源或执行操作；浏览器编码、Cookie属性、CORS、CSRF和CSP处理的是不同边界，不能替代服务端授权或彼此替代。
**Key terms / 关键术语：** authenticated subject / 已认证主体；tenant membership / 租户成员关系；authorization / 授权；resource scope / 资源范围；tenant-scoped query / 租户范围查询；worker revalidation / worker 重新验证。

~~~mermaid
flowchart LR
    Credential[Validate credential] --> Subject[Authenticated subject]
    Subject --> Membership[Resolve current tenant membership]
    Membership --> Action[Authorize action and resource]
    Action --> Query[Tenant-scoped database query]
    Action --> Cache[Authorize before cache lookup]
    Action --> Job[Persist authorized job context]
    Job --> Queue[Queue carries only job ID]
    Queue --> Worker[Worker reloads job and rechecks membership]
    Worker --> Query
~~~

## Tenant-owned resources / 租户资源授权

Authentication yields a validated subject; it does not prove access to every tenant or object. Build a **principal / 请求主体** from the verified identity plus the user's current membership and permissions in the selected tenant. A tenant ID in a URL or request body is only a requested context: resolve it against trusted membership before constructing the principal. Enforce the resource and action together on every API path.

For one synthetic document service, the path is: verified credential → current tenant membership → `GET /documents/{id}` authorization → query constrained by both `tenant_id` and document ID → cache lookup scoped by tenant, subject, and document after authorization → optional job row storing the authorized tenant, requester, and document. The worker loads that canonical job row, rechecks current membership, and calls the same tenant-scoped data function. A worker's broad database role does not make a job payload or object ID trustworthy.

This standard-library example uses SQLite to exercise the API and worker data boundaries. The identity inputs below stand in for a principal produced by a real authentication layer; they are not token validation code.

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE memberships (
    tenant_id TEXT NOT NULL, subject TEXT NOT NULL, role TEXT NOT NULL,
    PRIMARY KEY (tenant_id, subject)
);
CREATE TABLE documents (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL,
    requester TEXT NOT NULL, document_id TEXT NOT NULL
);
INSERT INTO memberships VALUES ('tenant-a', 'alice', 'reader');
INSERT INTO memberships VALUES ('tenant-b', 'bob', 'reader');
INSERT INTO documents VALUES ('doc-a', 'tenant-a', 'A private sample');
INSERT INTO documents VALUES ('doc-b', 'tenant-b', 'B private sample');
""")

def principal_for(tenant_id, subject):
    # A requested tenant becomes trusted only after this current membership lookup.
    row = db.execute(
        "SELECT role FROM memberships WHERE tenant_id=? AND subject=?",
        (tenant_id, subject),
    ).fetchone()
    if row is None or row[0] not in {"reader", "admin"}:
        return None
    return {"tenant_id": tenant_id, "subject": subject, "role": row[0]}

def read_document(principal, document_id, cache):
    if principal is None or principal["role"] not in {"reader", "admin"}:
        raise PermissionError("no current read permission")
    key = (principal["tenant_id"], principal["subject"], document_id)
    if key not in cache:
        row = db.execute(
            "SELECT body FROM documents WHERE tenant_id=? AND id=?",
            (principal["tenant_id"], document_id),
        ).fetchone()
        if row is None:
            return None
        cache[key] = row[0]
    return cache[key]

def read_api(principal, document_id, cache):
    body = read_document(principal, document_id, cache)
    return (404, None) if body is None else (200, body)

def enqueue(principal, document_id, cache):
    if read_document(principal, document_id, cache) is None:
        raise PermissionError("cannot enqueue an unreadable document")
    cursor = db.execute(
        "INSERT INTO jobs (tenant_id, requester, document_id) VALUES (?, ?, ?)",
        (principal["tenant_id"], principal["subject"], document_id),
    )
    db.commit()
    return cursor.lastrowid

def run_job(job_id, cache):
    # The queue carries only an ID; tenant, actor, and object come from the stored job.
    job = db.execute(
        "SELECT tenant_id, requester, document_id FROM jobs WHERE id=?", (job_id,)
    ).fetchone()
    if job is None:
        raise PermissionError("unknown job")
    tenant_id, requester, document_id = job
    principal = principal_for(tenant_id, requester)  # current membership, not enqueue-time trust
    body = read_document(principal, document_id, cache)
    if body is None:
        raise PermissionError("job target is outside its tenant")
    return body

cache = {}
alice = principal_for("tenant-a", "alice")
bob = principal_for("tenant-b", "bob")
assert read_api(alice, "doc-a", cache) == (200, "A private sample")
assert read_api(bob, "doc-a", cache) == (404, None)  # API boundary
assert run_job(enqueue(alice, "doc-a", cache), cache) == "A private sample"

# Simulate a stale or malformed job row created through a privileged service path.
cursor = db.execute(
    "INSERT INTO jobs (tenant_id, requester, document_id) VALUES (?, ?, ?)",
    ("tenant-b", "bob", "doc-a"),
)
db.commit()
try:
    run_job(cursor.lastrowid, cache)
except PermissionError:
    pass  # worker boundary still rejects the cross-tenant object
else:
    raise AssertionError("worker exposed a cross-tenant document")
```

The query always carries the principal's tenant, and authorization runs before a cache hit. This example gives each principal a separate cache entry; a system with finer-grained permissions must check those permissions on cache hits and include every access-relevant scope or policy version in its cache design. Database row-level security or tenant-scoped credentials can add another boundary, but the application still needs correct authorization and job ownership.

Permission-aware retrieval uses the same boundary before evidence reaches a model; see [Retrieval-Augmented Generation / 检索增强生成](../../ai-engineering/rag/rag-architecture-and-implementation.md) for that application.

**Interview answer / 面试回答：**

> **EN:** I derive the subject from a validated credential, then resolve its current membership in the requested tenant. The API checks the action and scopes the database query by tenant and object ID. I authorize before cache lookup and carry only a server-created job ID into the queue; the worker reloads the job, rechecks membership, and uses the same scoped query. A service account's broad database access does not grant the caller cross-tenant access.
>
> **中文：** 我先从已验证的凭据得到用户身份，再校验其当前租户成员关系。API 同时检查操作权限，并用租户 ID 和对象 ID 限定查询；缓存命中前也要授权。队列只传递服务端创建的任务 ID，worker 重新读取任务、检查成员关系，并复用租户范围查询。服务账号拥有较广数据库权限，不代表调用者可以跨租户访问。

See [AWS Well-Architected SaaS Lens: Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html) for the distinction between isolated resources and pooled resources that rely on runtime tenant scoping.

---


**Related questions / 相关问题：** [How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？](web-sessions-and-oidc.md) covers credentials and login; [Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？](web-browser-security-boundaries.md) separates TLS, XSS, CSRF, CORS, and framing; [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](web-availability-and-ddos.md) covers bounded public work; [How do parameterized queries prevent SQL injection? / 参数化查询如何防止 SQL 注入？](sql-injection-prevention.md) and [How should passwords be stored against offline guessing? / 如何存储密码以抵抗离线猜测？](password-storage.md) cover server-side data and credential boundaries.

**See also / 另见：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) covers browser request and transport context; [Browser Storage and Communication / 浏览器存储与通信](../../frontend/browser-apis/browser-storage-and-communication.md) covers client storage and messaging risks.

**Sources / 来源：** [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [AWS SaaS Lens: Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html). Security guidance checked 2026-10-15. The SQLite example uses synthetic identities and data; it is not credential-validation code.
