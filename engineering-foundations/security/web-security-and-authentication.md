# 如何逐次授权租户内的报表资源？

authentication (身份认证) 确认请求由哪个主体发出；authorization (授权) 逐项判断该主体此刻能否对指定资源执行指定动作。请求里的用户 ID、租户 ID、角色名或报表编号可由调用方选择，不能因它们出现在 URL、JSON 或队列消息里就视为可信事实。

**案例设定：** 浏览器请求 `/tenants/tenant-a/reports/42`。身份层已验证用户 `user-17`，数据库里 `user-17` 是租户甲的 `reader`；报表 42 的所有者固定为租户甲。`reader` 可以读取现有报表，但不能因此发起高成本重算或导出。为简化例子，报表归属不可变，授权只由当前成员角色决定，没有单报表分享规则。示例结果如下：

| 请求 | 数据库状态 | 对外结果 |
| --- | --- | --- |
| `user-17` 在 `tenant-a` 读报表 42 | 当前成员角色允许，复合键 `(tenant-a, 42)` 存在 | 200，返回报表 |
| `user-29` 在 `tenant-b` 读报表 42 | 用户是乙的 reader，但 `(tenant-b, 42)` 不存在 | 404，隐藏其他租户资源 |
| 没有租户成员身份的用户读报表 42 | 无当前租户主体 | 404，按本 API 的隐藏政策与资源不存在统一 |
| 任务创建后 `user-17` 被移出租户甲 | 当前成员关系已撤销 | API 读为 404；需要当前权限的 worker 拒绝任务 |

~~~mermaid
flowchart LR
    Credential[验证 Cookie 会话或 API 凭据] --> Subject[得到可信主体]
    Subject --> Tenant[从请求取租户上下文并查当前成员]
    Tenant -->|无成员或无 report:read| Deny[统一按政策返回 404]
    Tenant -->|允许读取| Key[构造 tenant、subject、report 缓存键]
    Key --> Cache{缓存命中？}
    Cache -->|是| Hit[返回曾在正确租户范围内填充的副本]
    Cache -->|否| Query[按 tenant_id + report_id 查询]
    Query -->|存在| Fill[填充对应范围的缓存并返回]
    Query -->|不存在| Missing[返回 404]
    Export[独立导出/重算请求] --> ExportAuth[另查 report:export 等动作权限]
    ExportAuth -->|通过| Job[持久化可信任务记录]
    Job --> Worker[worker 读 job_id 并复验当前策略]
~~~

图中的缓存命中以固定报表归属、按租户和主体隔离的缓存键为前提；未命中时，查询再以 `(tenant_id, report_id)` 证明行属于该租户。若所有权、分享关系或可见策略能改变，缓存命中也必须校验当前对象授权，并可靠更新或失效旧范围的缓存。缓存不应跳过本次请求的成员授权。

## 从可信主体到报表 42 的读取，需要经过哪些检查？

1. 认证层验证 Cookie 会话或访问令牌，得出稳定主体。不要把请求头或请求体里的 `user_id` 当成登录结果。凭据和联邦登录见[Cookie 会话与 OIDC 令牌怎样建立身份？](web-sessions-and-oidc.md)。
2. 将路径中的 `tenant-a` 当作用户希望选择的上下文；服务器查当前主体在租户甲的成员关系，之后才把它用于权限判断。多租户应用要明确用户在不同租户各自拥有的角色。
3. 把动作与对象一起判断。`reader` 可以允许若干读取动作，但不能自动证明对象归属，也不能推导出导出、刷新或管理权限。
4. 查询时同时绑定租户与编号，不能先用全局编号取出私有报表，再假设隐藏链接、不可猜 ID 或 UI 检查已经完成授权。
5. 对 API、附件、缓存和后台工作等每条数据路径重复正确的检查。最小权限的服务账号定义 worker 能做什么，不替最终用户完成授权。

### 角色能授予什么动作，资源检查还要做什么？

Role-Based Access Control (RBAC，基于角色的访问控制) 用 `reader`、`admin` 等角色归纳一组动作，适合表达租户成员的常见权限。资源属性或关系可能还需额外条件，例如某份报表只分享给指定主体，或其部门标签不匹配。角色说明“通常可做哪类动作”，不能证明报表 42 属于当前租户或用户。新端点默认拒绝，并对每个受保护操作重新检查当前策略，可以减少遗漏。

## 数据库与缓存怎样保持同一授权范围？

把租户和报表编号分别作为绑定值传入 SQL：

~~~sql
SELECT id, title, body
FROM reports
WHERE tenant_id = ? AND id = ?;
~~~

参数绑定防止输入改写 SQL 语法；授权检查决定当前主体能否读取绑定后的对象。两者解决不同问题：绑定参数后读取 `report_id=73` 仍可能越权；完成授权但拼接 SQL 仍可能被注入。动态排序字段通常不能作为一般参数绑定，应从固定允许列表里选择。

本例的数据库用复合主键 `(tenant_id, id)` 标识租户内报表；这使每个租户的编号空间明确。查询仍须保留两个谓词，因为主键约束数据形状，并不判断当前用户是否有权读该行。队列里的任务引用也应按同一复合身份解析。

缓存命中会绕过数据库谓词，因此先查当前成员资格，再访问带范围的缓存。此例缓存键是 `(tenant_id, subject, report_id)`：租户乙不能拿租户甲的缓存副本，且每次 API 请求都会先重查当前成员。固定所有权是这个精简示例的假设；若报表可以迁移租户或分享权限会变，就要在命中路径复验对象访问条件，或确保权限变更同步使缓存失效。参见[如何控制数据库缓存的新鲜度？](../backend/caching-and-redis.md)。

## 后台任务如何继续执行相同的访问政策？

排队时先按该任务的实际动作授权，再保存服务端创建的可信任务记录。消息只带不透明 `job_id`；worker 用该 ID 从可信存储读取租户、请求人和资源，不从任意消息载荷接受租户或报表编号。worker 是否要在执行时重新检查成员资格取决于产品定义：若成员移除后应停止工作，就复验当前权限；若已受理任务按提交时权限继续，则把那项授权决定作为可审计状态持久化。

下面的复现仅演示“读取一个已经存在的报表”任务，因此 `enqueue_read_job` 只需要 `report:read`。高成本报表导出或重算必须另查 `report:export` 等独立动作，或者明确定义其权限组合；不能从 `reader` 自然推出。账户报表作业的幂等受理、outbox 发布和队列确认见[怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md)；队列确认分别见[发布者确认和消费者确认分别证明什么？](../reliability/queue-delivery-and-acknowledgement.md)。

输入输出可以直接按上面的状态表理解：甲的成员读取甲的 42 返回 200；乙的成员读取乙命名空间中不存在的 42 返回 404；失去成员关系后，API 仍按隐藏策略返回 404，worker 抛出拒绝异常。完整 SQLite 复现放在折叠示例中。

> [!example]- SQLite 授权、缓存与任务复现
> 示例使用标准库 SQLite 和合成数据；`principal_for` 的主体参数视为认证中间件已经验证，不实现 Cookie 或签名令牌。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> db.executescript("""
> CREATE TABLE memberships (
>     tenant_id TEXT NOT NULL, subject TEXT NOT NULL, role TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, subject)
> );
> CREATE TABLE reports (
>     tenant_id TEXT NOT NULL, id INTEGER NOT NULL,
>     title TEXT NOT NULL, body TEXT NOT NULL,
>     PRIMARY KEY (tenant_id, id)
> );
> CREATE TABLE jobs (
>     id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL,
>     requester TEXT NOT NULL, report_id INTEGER NOT NULL
> );
> INSERT INTO memberships VALUES ('tenant-a', 'user-17', 'reader');
> INSERT INTO memberships VALUES ('tenant-b', 'user-29', 'reader');
> INSERT INTO reports VALUES
>     ('tenant-a', 42, 'Service health', 'Synthetic private data A');
> INSERT INTO reports VALUES
>     ('tenant-b', 73, 'Usage summary', 'Synthetic private data B');
> """)
>
> def principal_for(tenant_id, subject):
>     row = db.execute(
>         "SELECT role FROM memberships WHERE tenant_id=? AND subject=?",
>         (tenant_id, subject),
>     ).fetchone()
>     if row is None or row[0] not in {"reader", "admin"}:
>         return None
>     return {"tenant_id": tenant_id, "subject": subject, "role": row[0]}
>
> def read_report(principal, report_id, cache):
>     if principal is None or principal["role"] not in {"reader", "admin"}:
>         raise PermissionError("no current report:read permission")
>     key = (principal["tenant_id"], principal["subject"], report_id)
>     if key not in cache:
>         row = db.execute(
>             "SELECT body FROM reports WHERE tenant_id=? AND id=?",
>             (principal["tenant_id"], report_id),
>         ).fetchone()
>         if row is None:
>             return None
>         cache[key] = row[0]
>     return cache[key]
>
> def read_api(tenant_id, subject, report_id, cache):
>     # 隐藏政策把无成员、无角色和资源不存在统一映射为 404。
>     principal = principal_for(tenant_id, subject)
>     if principal is None:
>         return (404, None)
>     body = read_report(principal, report_id, cache)
>     return (404, None) if body is None else (200, body)
>
> def enqueue_read_job(tenant_id, subject, report_id, cache):
>     principal = principal_for(tenant_id, subject)
>     if read_report(principal, report_id, cache) is None:
>         raise PermissionError("cannot enqueue an unreadable report")
>     cursor = db.execute(
>         "INSERT INTO jobs (tenant_id, requester, report_id) VALUES (?, ?, ?)",
>         (principal["tenant_id"], principal["subject"], report_id),
>     )
>     db.commit()
>     return cursor.lastrowid
>
> def run_job(job_id, cache):
>     job = db.execute(
>         "SELECT tenant_id, requester, report_id FROM jobs WHERE id=?", (job_id,)
>     ).fetchone()
>     if job is None:
>         raise PermissionError("unknown job")
>     tenant_id, requester, report_id = job
>     principal = principal_for(tenant_id, requester)  # 执行时重查成员
>     body = read_report(principal, report_id, cache)
>     if body is None:
>         raise PermissionError("job target is outside its tenant or no longer readable")
>     return body
>
> cache = {}
> assert read_api("tenant-a", "user-17", 42, cache) == (
>     200, "Synthetic private data A"
> )
> assert read_api("tenant-b", "user-29", 42, cache) == (404, None)
> assert read_api("tenant-a", "user-29", 42, cache) == (404, None)
> job_id = enqueue_read_job("tenant-a", "user-17", 42, cache)
> assert run_job(job_id, cache) == "Synthetic private data A"
>
> # 即使错误写入了跨租户任务记录，worker 仍按 tenant_id + report_id 查询。
> malicious_job = db.execute(
>     "INSERT INTO jobs (tenant_id, requester, report_id) VALUES (?, ?, ?)",
>     ("tenant-b", "user-29", 42),
> )
> db.commit()
> try:
>     run_job(malicious_job.lastrowid, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker exposed a report outside the tenant")
>
> # 已排队任务在成员撤销后不得命中旧缓存。
> db.execute("DELETE FROM memberships WHERE tenant_id=? AND subject=?",
>            ("tenant-a", "user-17"))
> db.commit()
> assert read_api("tenant-a", "user-17", 42, cache) == (404, None)
> try:
>     run_job(job_id, cache)
> except PermissionError:
>     pass
> else:
>     raise AssertionError("worker accepted a revoked member")
> print("tenant-a user-17: report 42 -> 200 before revocation, 404 after")
> print("tenant-b user-29: report 42 -> 404; wrong-scope and revoked jobs denied")
> ~~~

**接下来：** 本章负责服务端把主体、动作和租户内资源联系起来；浏览器跨源读取、Cookie 自动发送和脚本执行见[浏览器安全控制分别保护什么信任边界？](web-browser-security-boundaries.md)。网络入口容量与攻击流量准入见[Web 服务如何限制拒绝服务的影响？](web-availability-and-ddos.md)。

> [!info]- 来源
> - 每次受保护操作检查权限、默认拒绝、最小权限和对象级授权：[OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)，Recommendations 与 IDOR 章节，按 2026-11-06 版本核对。
> - 租户所有权与 pooled SaaS 中运行时租户隔离：[AWS Well-Architected SaaS Lens, Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html)，按 2026-11-06 版本核对。该文是云厂商架构指导，不是通用标准。
> - SQL 参数化与允许列表：[OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)，Primary Defenses，按 2026-11-06 版本核对。
