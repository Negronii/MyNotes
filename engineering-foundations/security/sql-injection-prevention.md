# How do parameterized queries prevent SQL injection? / 参数化查询如何防止 SQL 注入？

SQL injection happens when untrusted data is interpreted as part of SQL syntax. Validate input for usability, but make the security boundary at the server: parameterized queries supply values separately from SQL text. Identifiers or sort directions that cannot be bound as values must come from a fixed allowlist. Query parameterization prevents one class of command injection; authorization is a separate decision. / SQL 注入发生在不可信数据被解释为 SQL 语法的一部分时。输入校验可以改善可用性，但安全边界应在服务端：参数化查询把值与 SQL 文本分开提供。无法作为值绑定的标识符或排序方向必须来自固定白名单。参数化查询防止一类命令注入；授权仍是独立判断。

**Key terms / 关键术语：** parameterized query / 参数化查询；SQL syntax / SQL 语法；allowlist / 白名单；authorization / 授权；least privilege / 最小权限。

On the server, bind values instead of concatenating them into the query. An ORM helps only when its query path uses safe parameterization; raw query construction can still be vulnerable. Parameterization does not prove that the caller may read or modify the selected record. Give each database account only the tables and operations it needs; safe values do not justify connecting as an administrator.

The frontend can validate inputs for usability, but client-side checks are bypassable and are not a security boundary. Validate and authorize again where the server constructs the data operation.

**Related notes / 相关笔记：** [Database constraints and indexes / 数据库约束与索引](../databases/database-constraints-and-indexes.md) explains engine-side data invariants; [Cross-tenant authorization / 跨租户资源授权](web-security-and-authentication.md) explains authorization that parameter binding cannot provide.

**Sources / 来源：** OWASP [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) and its [least-privilege guidance](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#least-privilege), checked 2026-10-15.
