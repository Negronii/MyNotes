# Web Security and Authentication / Web安全与身份认证

**身份认证 / Authentication** establishes which identity or credential is presenting a request. **授权 / Authorization** decides whether that identity may perform this action on this resource. Authentication alone does not grant every permission; enforce authorization on the server for each protected operation. Client checks can improve the interface but cannot decide access.

身份认证回答请求以谁的凭据发出，授权则逐项决定该身份能否访问资源或执行操作；浏览器编码、Cookie属性、CORS、CSRF和CSP处理的是不同边界，不能替代服务端授权或彼此替代。

## Cookies vs. tokens — which to use for authentication?

**Cookie 会话与令牌 / Cookie sessions and tokens** are transport and session choices, not two complete security models. Choose according to the clients, domain boundaries, revocation needs, and threat model.

A server-side session commonly works like this:

1. The user authenticates; the server creates a session and stores its state.
2. The server returns an opaque session identifier in a cookie.
3. The browser sends that cookie only when its domain, path, security, SameSite, and request rules match.
4. The server resolves the session and performs authorization for the requested action.

For a session cookie, consider:

- **HttpOnly** prevents page JavaScript from reading the cookie through APIs such as `document.cookie`. It does not stop injected JavaScript from making authenticated requests as the user.
- **Secure** limits transmission to secure channels such as HTTPS.
- **SameSite=Strict, Lax, or None** controls cookie sending in cross-site contexts. It is a site-level browser rule, not an origin or authorization boundary. Specify the value; browser defaults can vary. `SameSite=None` requires `Secure`.
- Cookie scope and size have implementation constraints; do not use `Domain` or `Path` as authorization checks.

A bearer token is presented by the client, commonly in an `Authorization: Bearer` header. A JWT is one token format: a signed JWT normally protects integrity, but its claims are readable unless it is encrypted. A valid signature proves that a trusted key signed the token; it does not by itself authorize every action. Verifiers must validate the expected algorithm, issuer, audience, token type, and time claims according to the application protocol. Use short-lived tokens and a deliberate rotation or revocation strategy where needed.

A JWT can carry claims without a per-request session lookup, but revocation and fresh permission changes then need an explicit design. The JWT format does not bypass browser origin rules or CORS. A token stored in browser-accessible storage can be read by injected JavaScript; an HttpOnly cookie reduces that direct theft path but still needs a CSRF design. Neither storage choice fixes XSS or authorization flaws.

---

## What is Single Sign-On (SSO), and how does it work?

**单点登录 / Single Sign-On** lets a user authenticate through an identity provider and establish sessions with multiple relying applications. Each application still validates the protocol response and applies its own authorization rules.

OAuth 2.0 is an authorization framework for delegated access; OAuth alone is not an authentication protocol. **OpenID Connect / OpenID Connect 身份层** builds an identity layer on OAuth 2.0 and defines the ID Token. An access token and an ID Token serve different purposes: do not treat either as proof for an unrelated audience.

In a typical redirect flow, the relying application creates a login request, the identity provider authenticates the user, and the application validates the response before creating its own session. Protocol details matter: validate the redirect target and issuer, and apply the relevant state, nonce, signature, and audience checks for the flow.

See [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).

### Authorization-code + PKCE callback / 授权码 + PKCE 回调

When an application needs federated sign-in, OpenID Connect uses OAuth's authorization-code flow with the `openid` scope. Plain OAuth grants delegated API access; it does not define an ID Token or an authentication result for the client.

1. The client creates a one-time `code_verifier` and derives `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))` using `S256`. It keeps the verifier with the browser's pending login transaction. It also normally creates an unpredictable `state` value bound to that browser transaction; an OIDC client may create a `nonce` if it wants to bind the returned ID Token to this request.
2. The client redirects the browser to the authorization endpoint with `response_type=code`, its `client_id`, an exactly registered `redirect_uri`, `scope=openid` (plus only the API scopes it needs), `state`, `code_challenge`, and `code_challenge_method=S256`. It includes `nonce` only if the flow uses it.
3. After authenticating the user and obtaining any required consent, the authorization server redirects to the registered callback with a short-lived, one-use authorization code and the `state` value, if sent. The callback checks and consumes its stored `state` before continuing. If the client uses multiple authorization servers, it also applies an issuer or equivalent mix-up defense.
4. The client sends the code, the same `redirect_uri`, and its original `code_verifier` to the token endpoint; a confidential client also authenticates there when required. The authorization server recomputes the challenge and rejects a code redemption whose verifier does not match. The code alone is therefore insufficient for an interceptor to redeem.
5. In the selected OIDC Authorization Code Flow, a successful token response includes an ID Token and an Access Token; a Refresh Token is optional. The client validates the ID Token before establishing its own session. The API validates the access token it receives separately.

These values solve different problems and are not all mandatory in every flow:

- **`state` / 请求状态** is an opaque value for correlating a redirect with the initiating browser transaction and often restoring a local return path. OAuth clients must prevent callback CSRF, but a literal `state` parameter is not the only permitted defense: RFC 9700 allows a client that has confirmed PKCE support to rely on PKCE for CSRF protection; in OIDC, `nonce` can also provide that protection. If the client sends `state`, it must bind and check it instead of trusting a callback value.
- **`nonce` / 随机数** binds an ID Token to an OIDC authentication request and helps detect replay. It is optional in the OIDC Authorization Code Flow; when sent, the provider must return it in the ID Token and the client must compare it. Other OIDC flows have different requirements.
- **`code_verifier` / PKCE验证值** is the secret the client keeps and later presents at the token endpoint. The authorization request carries only its derived challenge. RFC 9700 requires PKCE for public clients and recommends it for confidential clients; use `S256`, not a method that reveals the verifier.

**Token use and lifecycle / 令牌用途与生命周期：** An **ID Token / 身份令牌** tells the OIDC client about an authentication event; it is not an API credential. Validate it under the OIDC profile: exact expected issuer, a trusted audience containing this client's ID (and `azp` when applicable), expiration, cryptographic validation with the issuer's keys and registered algorithm, and a matching `nonce` when one was sent. An **access token / 访问令牌** is for a resource server. That server checks the expected issuer, its own API audience, expiration, and allowed scope/action; follow the issuer's contract, verifying the signature and claims for a JWT access-token profile or using the trusted introspection/lookup mechanism for an opaque token. Decoding a JWT is not validation.

A refresh token is presented to the authorization server's token endpoint to obtain a replacement access token; it is not sent to the API. Treat it as a high-value credential. RFC 9700 requires public clients to use refresh-token rotation or sender constraint. If the authorization server supports a revocation endpoint, a client can request revocation of a token; resource servers may learn of that change at different times. A locally verified, self-contained access token may remain accepted until its expiry unless the resource server also checks revocation state. Ending the application's own session and ending an identity-provider session are separate operations.

**Core idea / 核心要点：** OAuth authorization grants access to an API; OIDC tells a client who authenticated; the application still decides whether that identity may perform an action now. PKCE protects code redemption, and runtime authorization protects application data.

**Mechanism in Chinese / 机制要点：** PKCE 把授权码与客户端保留的 verifier 配对；state 关联回调与发起的登录事务，若发送就必须校验，而已确认支持 PKCE 的客户端可按 RFC 9700 依 PKCE 防回调 CSRF。OIDC Code Flow 的 nonce 可选，若发送则须与 ID Token 中的值匹配。客户端验证 ID Token 后建立自己的会话，API 则独立验证面向自身的 access token，并按当前主体、租户和权限做运行时授权。refresh token 只向授权服务器换取新 access token；撤销传播可能有延迟，应用会话、IdP 会话和 API 对已签发 access token 的接受边界要分别处理。

See [OpenID Connect Core 1.0, incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice (January 2025)](https://www.rfc-editor.org/rfc/rfc9700.html), [RFC 7636, Proof Key for Code Exchange (September 2015)](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009, OAuth 2.0 Token Revocation (August 2013)](https://www.rfc-editor.org/rfc/rfc7009.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).

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

## How does HTTPS protect against man-in-the-middle attacks?

**HTTPS / TLS** protects data in transit against network eavesdropping and tampering when the connection is correctly configured and the client validates the server. In a certificate-authenticated TLS 1.3 handshake, key agreement derives traffic keys; the server's certificate and handshake signature authenticate the server's key. The server does not simply encrypt a session key with its public key as in older textbook handshake descriptions.

A client checks the certificate chain and that the certificate is valid for the requested hostname, then verifies the handshake. Certificate status and revocation handling depend on the client and deployment, so do not describe revocation checking as a universal guaranteed browser step. A trusted certificate does not authenticate the application's user; application authentication and authorization remain separate.

- **Symmetric cryptography / 对称密码** protects application traffic efficiently after handshake keys are established.
- **Public-key cryptography / 公钥密码** supports key agreement and authentication in the handshake; the TLS 1.3 suite and configuration determine the exact mechanisms.

See [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html).

---

## XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**跨站脚本 / XSS** occurs when untrusted data is interpreted as active content in a page. Script that executes in an origin can read data available to that script and make requests from that origin; an HttpOnly cookie blocks direct cookie reading but does not stop such requests.

Use the defense that matches the output context:

1. Render plain text through framework APIs that treat it as text, and encode values for their HTML, attribute, URL, JavaScript, or CSS context.
2. If user-authored rich HTML is required, sanitize it with a maintained HTML sanitizer and keep the allowed markup narrow.
3. Avoid inserting untrusted strings into `innerHTML`, `document.write`, inline event handlers, `eval`, or `new Function`. Framework escape defaults do not protect deliberate raw-HTML escape hatches.
4. Add a carefully tested Content Security Policy as defense in depth. Nonce- or hash-based strict policies can restrict script execution; an allowlist such as `script-src 'self'` alone is not a universal XSS fix.

Before assigning an untrusted value to `href` or `src`, validate the complete URL's scheme and destination against the application's policy (for example, reject `javascript:`); output encoding for the attribute does not replace URL validation.

CSP can reduce the impact of some injection paths, but it does not replace safe rendering and sanitization. See OWASP's [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) and [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) guidance.

---

## CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**跨站请求伪造 / CSRF** abuses ambient browser credentials: a site can cause a browser to send some cross-site requests, and the browser may attach cookies that match the destination. The attacker often cannot read the response, but reading it is not required to cause a state change.

For state-changing cookie-authenticated requests, use an application-validated CSRF token or an equivalent well-reviewed pattern. Check the request origin where appropriate, and use SameSite as defense in depth. Do not mutate state on safe methods such as GET. SameSite=Lax still permits some top-level safe-method navigations, and sibling subdomains can be same-site; it does not replace authorization or every CSRF defense.

**SameSite=None requires Secure.** Also account for legitimate cross-site login and embedded flows rather than silently weakening checks. See the [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

---

## What is CORS?

**跨源资源共享 / Cross-Origin Resource Sharing (CORS)** is a browser protocol that controls when a script may read a cross-origin response. It is not authentication, authorization, or a general firewall: some cross-origin requests can still be sent even when browser JavaScript cannot read the response, and non-browser clients do not enforce CORS.

For a credentialed browser request, the client must opt in to credentials and the response must name an allowed origin rather than `Access-Control-Allow-Origin: *`, with `Access-Control-Allow-Credentials: true`. Preflight requests are checked separately. Use an explicit origin allowlist; reflecting arbitrary Origin values can expose credentialed responses.

CORS does not make an endpoint private. Authenticate and authorize the server request even if the intended browser client is the only one expected to call it. See the [WHATWG Fetch Standard, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials).

---

## Clickjacking — what is it, how do you prevent it?

**点击劫持 / Clickjacking** tricks a user into interacting with a page framed beneath or inside deceptive content. Use the CSP `frame-ancestors` directive to state which sites may embed the page; use `X-Frame-Options` where legacy client support requires it. These headers control framing, not user authorization.

For example, `Content-Security-Policy: frame-ancestors 'self'` permits framing by the same origin. Set a policy that fits legitimate embedding requirements and test the application paths that must remain embeddable.

---

## DDoS — what is it, what can you actually do?

**分布式拒绝服务 / Distributed Denial of Service** uses traffic or expensive requests to exhaust network, service, or application resources. Mitigation depends on the attack layer and capacity available; no single application control guarantees protection.

Use layered measures such as provider or edge traffic filtering, rate limits and quotas, caching, bounded work, and monitoring. Application code can reject abusive work early and keep expensive endpoints bounded, but large traffic floods need network and provider capacity as well.

---

## SQL injection — frontend's role?

**SQL 注入 / SQL injection** happens when data is interpreted as part of a SQL command. The frontend can validate inputs for usability, but client-side validation is bypassable and is not a security boundary.

On the server, use parameterized queries so values are supplied separately from SQL syntax. For identifiers or sort directions that cannot be bound as values, choose from a fixed allowlist. An ORM helps only when the query path uses its safe parameterization; raw query construction can still be vulnerable. Authorization is a separate check: a parameterized query does not prove that the caller may access the selected record.

Give each application database account only the tables and operations it needs; query parameterization does not justify connecting as a database administrator.

---

## How should passwords be stored?

**密码存储 / Password storage** must remain resistant to offline guessing if a database is exposed. Store a salted password hash produced by a password-storage algorithm designed to be expensive to guess, such as Argon2id; use a maintained library and tune its cost for the deployment. A unique random salt is stored with each hash; it is not a secret. A fast general-purpose digest such as SHA-256 alone is not an appropriate password-storage scheme.

An optional pepper is a secret kept separately from the password database; it is defense in depth, not a substitute for a suitable password hash. Pair storage with online attempt throttling and a policy that avoids easily guessed passwords. See the [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html).

**See also:** [HTTP Protocols and WebSockets](../networking/http-protocols-and-websockets.md) for browser request and transport context, and [Browser Storage and Communication](../../frontend/browser-apis/browser-storage-and-communication.md) for browser storage and messaging security.

Sources: [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#least-privilege), [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [OWASP CSP](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html), [WHATWG Fetch](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials), [RFC 7636 PKCE](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009.html), [RFC 8446 TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html), [RFC 8725 JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html), [AWS SaaS Lens: Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html), and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html). Security guidance checked 2026-10-15.
