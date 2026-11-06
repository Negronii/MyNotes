# Cookie 会话与 OIDC 令牌怎样建立身份？

浏览器每次读取报表 42 时，服务端要先辨认请求携带的凭据、签发者和可确认的身份。Cookie 可以承载不透明会话标识，应用再由标识查询服务器端会话；bearer token（持有者令牌）本身就是可重放的凭据，由资源服务验证。OpenID Connect (OIDC，基于 OAuth 2.0 的身份层) 让应用验证身份提供方的认证结果。应用随后仍要建立自己的会话；独立的报表 API 则需要面向该 API 签发的 Access Token（访问令牌）。这些凭据只建立调用者身份或调用资格，不决定用户能否读取报表 42。

## 登录后，Cookie 会话怎样识别请求？

一种常见架构是在浏览器保存随机、不透明的会话 ID（标识），服务器把会话状态保存在共享存储或应用数据库。登录后，服务器创建新会话记录并以 `Set-Cookie` 返回：

~~~http
Set-Cookie: __Host-session=<random-opaque-id>; Path=/; Secure; HttpOnly; SameSite=Lax
~~~

后续请求只有在目标主机、路径、安全连接和 SameSite 规则都匹配时才会附带 Cookie。`__Host-session` 是由 `reports.example` 设置的 host-only Cookie：它随发往该主机的合适请求发送，不会自动发送给 `api.reports.example`、`console.example.com` 或其他主机。服务端收到标识后查询会话，再把经验证的主体映射到本地账户，例如用签发者 `iss`（issuer，签发身份提供方）与该签发者范围内的用户编号 `sub`（subject，主体）共同标识账户。Cookie 字段只运送值；同一个字段也能存偏好等非身份数据，“有 Cookie”本身不表示已经认证。

会话 ID 是可重放凭据。认证成功或权限等级变化时轮换它，可以降低会话固定风险；空闲过期、绝对过期、退出、密码重置和管理员撤销的处理共同决定失效速度。`__Host-` 要求安全连接、无 `Domain` 属性且 `Path=/`，从而收紧 Cookie 主机范围。`Secure` 限制只在安全连接上传送；`HttpOnly` 阻止页面脚本直接读取 Cookie 值；`SameSite` 限制部分跨站上下文中的自动发送。它们各有边界：`HttpOnly` 不能阻止已执行的恶意脚本代替用户发请求；`SameSite` 按 site（站点）判断，不等同 origin（源）或资源授权。若确实需要跨站上下文附带 Cookie，需设置 `SameSite=None; Secure`，并保留适用的 CSRF 防护；见[浏览器安全控制保护什么边界？](web-browser-security-boundaries.md)。

## Cookie 会话和 Bearer 令牌各保留什么状态？

| 设计 | 浏览器或调用方携带 | 验证点与状态 | 撤销和权限变化的取舍 |
| --- | --- | --- | --- |
| 服务端 Cookie 会话 | Cookie 中的不透明会话 ID | 应用按 ID 取服务器端会话；受保护操作再逐次检查授权 | 可即时使服务器端记录失效；请求需要会话存储或共享会话服务 |
| 不透明 Bearer Access Token | 常见形式是 `Authorization: Bearer …` | 资源服务器查询签发方或调用 token introspection（令牌状态查询）服务 | 可集中撤销；请求可能依赖查询服务或其缓存 |
| 自包含 JWT Bearer Token | 常见形式是同一 Authorization 字段 | 资源服务器验签并检查 `iss`、`aud`（audience，令牌原本面向的受众）、有效期和用途 | 不必每次查询用户会话；已签发权限可能在到期前仍有效，及时撤销需要额外机制 |

JSON Web Token (JWT，JSON Web 令牌) 是令牌格式，不是身份已验证的证明。典型签名 JWT 的声明可被读取；签名证明内容来自受信签发者且未被修改，不提供保密性。验证方要按目标协议检查允许的算法、准确签发者、目标受众、令牌类型、过期时间和适用的授权范围；只解码 JWT 不等于验证 JWT。若资源服务器必须及时获知撤销，短有效期、introspection 或请求期会话检查都可能适用，取舍取决于延迟、故障和部署成本。

单页应用若把访问令牌放在脚本可读的存储中，XSS 可能将其读出；换成 HttpOnly Cookie 后，脚本不易直接读凭据，但浏览器会自动附带 Cookie，仍须防 CSRF。由后端代理浏览器请求的架构可以把访问令牌留在服务端，并给浏览器较短作用域的应用会话。选择存储位置不能修复 XSS、错误授权或身份映射问题。

## 授权码流程如何确认身份并建立应用会话？

OAuth 2.0 是授权框架，本身不定义客户端如何确认终端用户身份；OIDC 在其上增加身份层和 ID Token（身份令牌）。ID Token 面向 OIDC 客户端，说明身份提供方完成了怎样的认证事件；Access Token 面向资源服务器。把发给登录客户端的 ID Token 当成报表 API 凭据会混淆两个受众。

**案例：** 查看者在报表应用选择“使用身份提供方登录”。本例选择授权码流程和顶层 GET callback：

1. 应用生成高熵、一次性的 PKCE `code_verifier`，计算 `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))`；再生成随机事务句柄，把 `{state, verifier, expected_issuer}` 按句柄保存在短期服务端记录中。
2. 应用用 `__Host-login-tx` Cookie 把事务句柄交给浏览器，属性为 `Path=/; Secure; HttpOnly; SameSite=Lax`，且不设置 `Domain`；再把浏览器导向已注册的身份提供方，并发送 `response_type=code`、`client_id`、精确登记的 `redirect_uri`、`scope=openid`、`code_challenge`、`code_challenge_method=S256` 和随机 `state`。短期事务记录和 Cookie 都应设置有限寿命。本例的顶层 GET 回调可携带 Lax Cookie；若选择其他回调方式，应重新核对 SameSite 发送条件。
3. 身份提供方认证用户后，将浏览器导回已登记的 callback，附上短期授权码与原 `state`。回调请求还须携带先前设置的登录事务 Cookie；应用先用它定位本浏览器发起的事务，再核对并消费其中的 state，取回 verifier 和预期签发者。不能只凭 callback 自带的 state 查一个全局事务记录。配置多个授权服务器时，还须按协议防范授权服务器混淆并校验 issuer。
4. 应用后端向 Token Endpoint 提交 `grant_type=authorization_code`、授权码、原 `redirect_uri`、私有 `code_verifier`；按客户端类型还要认证客户端。身份提供方重新计算 challenge，匹配后才兑换授权码。截获授权码的第三方通常没有 verifier，不能代替发起客户端完成交换。
5. 成功兑换的 Token Endpoint 响应返回 ID Token 和 Access Token。OIDC 客户端验证 ID Token，再把 `(issuer, subject)` 映射到本地账户并建立自己的应用会话。`scope=openid` 建立 OIDC 身份请求，但不会自动授予自定义报表 API 的受众或权限；Access Token 只有在身份提供方按资源服务器配置签发了该 API 所需的 audience 与权限时，才可用于报表 API。其他配置下它可能面向 UserInfo 等资源，不能仅凭它与 ID Token 一起返回就当作报表 API 凭据。

`state` 把回调与发起登录的浏览器事务绑定；`nonce`（若发送）把 ID Token 与一次认证请求关联；PKCE 把授权码与持有 verifier 的客户端绑定。RFC 9700 允许客户端在确认授权服务器支持 PKCE 时依 PKCE 防护回调 CSRF；若不确认支持，或本身发送了 state/nonce，就要把相应值绑定原事务并验证，不能信任回调自带值。授权服务器必须支持 PKCE；客户端应显式发送 `code_challenge_method=S256`，因为省略时 RFC 7636 默认 `plain`。

~~~mermaid
sequenceDiagram
    participant App as 报表应用
    participant Browser as 浏览器
    participant IdP as 身份提供方
    participant API as 报表 API
    App->>App: 保存 {state, verifier, expected_issuer}
    App->>Browser: 登录事务 Cookie + redirect_uri、scope=openid、challenge、method=S256、state
    Browser->>IdP: 请求授权码
    IdP->>Browser: 顶层 GET 回调 code + state
    Browser->>App: 事务 Cookie + code + state
    App->>App: 用 Cookie 找事务并消费 state
    App->>IdP: grant_type=authorization_code、code、redirect_uri、verifier
    IdP-->>App: ID Token 和 Access Token
    App->>App: 验证 ID Token，创建本地应用会话
    opt 独立 API 且签发方配置了该资源
        App->>API: API audience 的 Access Token
        API->>API: 验证令牌后逐次检查资源授权
    end
~~~

验证 ID Token 时，客户端至少要匹配预期 `iss`，验证 `aud` 包含客户端 ID、按规则检查 `azp`（authorized party，获授权的客户端），核验 `exp`、本次事务发送的 `nonce`（如有），并依据协议验证签名、可信算法和密钥。报表 API 若是独立资源，身份提供方须配置相应资源受众与权限；客户端可以按 RFC 8707 使用 `resource` 参数请求特定资源（是否支持仍由提供方决定），API 再独立验证该专用 Access Token 的 issuer、audience、有效期和范围。OAuth scope 不会替应用判断报表 42 的本地所有权。

> [!info] 单点登录不共享各应用的本地会话
> Single Sign-On (SSO，单点登录) 可以让同一身份提供方的登录会话支持用户进入多个已注册应用，减少重复输入凭据的需要；同意页面、策略和认证强度仍可能要求再次交互。每个应用仍须验证自己的授权回调并创建自己的本地会话。退出一个应用的本地会话，不一定结束身份提供方会话，也不会自动退出其他应用。报表应用使用的会话 Cookie 仍由各自主机设置和验证。

> [!info] Token Endpoint 的限定验证方式
> OIDC Core 对直接经已验证 TLS 连接从 Token Endpoint 收到的 Authorization Code Flow ID Token 允许一种窄例外：在验证 Token Endpoint 的 TLS 服务器身份后，可用它验证 issuer 来代替 ID Token 签名检查。该例外只适用于这条受限路径；其他 ID Token 仍须按规范验证签名。

Refresh Token 只发给 Token Endpoint 用于换取新 Access Token，不应发给报表 API。它是高价值凭据；RFC 9700 要求公共客户端使用令牌轮换或 sender-constraining 检测 Refresh Token 重放。若签发方提供撤销端点，客户端可请求撤销；自包含 Access Token 是否立即停止被资源服务器接受，还取决于资源服务器是否查撤销状态。退出本地应用会话、退出身份提供方会话、撤销令牌是三种相关但不同的操作。

## 本地密码验证后，应用还要做什么？

本地密码数据库保存带随机盐的专用密码哈希及其算法和成本参数，而不是明文或快速通用散列。被盗数据库会让攻击者离线尝试猜测；内存困难的 Argon2id 会使每次猜测消耗内存和计算，仍需由服务根据并发和硬件调优成本，并独立限制在线尝试。OWASP 当前列出的 19 MiB 内存、2 次迭代、并行度 1 是一个最低 Argon2id 配置示例，不是所有服务的性能目标。盐不需要保密；可选 Pepper 是数据库外的服务器秘密，要先设计轮换与恢复。

密码验证或联邦身份验证得到的是已经验证的主体和认证上下文。之后，账户映射、会话生命周期和具体资源授权仍由应用负责。报表编号 42 是否允许当前主体读取，见[如何逐次授权租户内的报表资源？](web-security-and-authentication.md)。

> [!info]- 来源
> - Cookie 与服务器状态关联：[IETF RFC 6265, HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265.html)，§4–§5，2011-04；属性与 Cookie 发送限制同时核对 WHATWG [Fetch Standard, Cookies](https://fetch.spec.whatwg.org/#cookies)，Living Standard，核对于 2026-11-06。
> - Cookie 前缀、host-only 作用域与 SameSite 属性：[HTTPWG RFC6265bis 草案](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html)，§4.1.3.2、§5.6.7，核对于 2026-11-06；草案仍在演进。
> - 会话 ID 与安全配置：[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，Session ID、Cookie 属性和过期章节，按 2026-11-06 版本核对。
> - OAuth 2.0 安全最佳实践：[IETF RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)，§2、§4.7、§4.10、§4.14，2025-01；核对于 2026-11-06。
> - OIDC 身份层、Code Flow、ID Token 和访问令牌验证：[OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)，§2、§3.1.2–§3.1.3，2023-12-15；Token Endpoint/TLS 例外见 §3.1.3.7(6)。核对于 2026-11-06。
> - PKCE verifier、challenge 与默认方法：[IETF RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html)，§4.3；授权码交换参数：[RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)，§4.1.3；资源指示参数：[RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.html)，§2。均核对于 2026-11-06。
> - Token 撤销：[RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)，§2，2013-08；JWT 验签与防算法混淆：[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)，§3，2020-02。均核对于 2026-11-06。
> - 密码哈希 Argon2id 参数：[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)，Argon2id 与升级章节，按 2026-11-06 版本核对；身份验证器要求：[NIST SP 800-63B-4](https://csrc.nist.gov/pubs/sp/800/63/b/4/final)，2025-07，核对于 2026-11-06。
