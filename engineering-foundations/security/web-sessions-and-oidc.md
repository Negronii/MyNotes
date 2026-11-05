# How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？

**Core answer / 核心回答：** A cookie usually carries an opaque session identifier that the server resolves; a bearer token carries a credential the resource server validates. OIDC adds an identity layer to OAuth, while the application still creates its own session and authorizes each protected action. Choose storage, lifetime, revocation, and callback checks for the client and threat model. / Cookie 通常承载由服务端解析的不透明会话标识；Bearer token 则携带资源服务器验证的凭据。OIDC 在 OAuth 上加入身份层，但应用仍要建立自己的会话，并逐项授权受保护操作。应按客户端和威胁模型设计凭据存储、生命周期、撤销与回调校验。

**Key terms / 关键术语：** session identifier / 会话标识；bearer token / Bearer 令牌；JWT / JSON Web Token；OIDC / OpenID Connect；authorization code / 授权码；PKCE / 授权码交换证明；state / 状态值；nonce / 随机数；refresh token / 刷新令牌。

## Cookies vs. tokens — which to use for authentication? / Cookie 会话与令牌应如何选择？

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

**Token use and lifecycle / 令牌用途与生命周期：** An **ID Token / 身份令牌** tells the OIDC client about an authentication event; it is not an API credential. Validate it under the OIDC profile: exact expected issuer, a trusted audience containing this client's ID (and `azp` when applicable), expiration, a matching `nonce` when one was sent, and normally its signature with the configured algorithm and appropriate verification key. OIDC Core §3.1.3.7(6) permits a narrow exception in the Authorization Code Flow: if the client receives the ID Token by direct communication with the Token Endpoint and validates that endpoint's TLS server identity, it may use that TLS validation to validate the issuer instead of checking the token signature. The other ID Token checks still apply, and ID Tokens received through other paths require signature validation. An **access token / 访问令牌** is for a resource server. That server checks the expected issuer, its own API audience, expiration, and allowed scope/action; follow the issuer's contract, verifying the signature and claims for a JWT access-token profile or using the trusted introspection/lookup mechanism for an opaque token. Decoding a JWT is not validation.

A refresh token is presented to the authorization server's token endpoint to obtain a replacement access token; it is not sent to the API. Treat it as a high-value credential. RFC 9700 requires public clients to use refresh-token rotation or sender constraint. If the authorization server supports a revocation endpoint, a client can request revocation of a token; resource servers may learn of that change at different times. A locally verified, self-contained access token may remain accepted until its expiry unless the resource server also checks revocation state. Ending the application's own session and ending an identity-provider session are separate operations.

**Core idea / 核心要点：** OAuth authorization grants access to an API; OIDC tells a client who authenticated; the application still decides whether that identity may perform an action now. PKCE protects code redemption, and runtime authorization protects application data.

**Mechanism in Chinese / 机制要点：** PKCE 把授权码与客户端保留的 verifier 配对；state 关联回调与发起的登录事务，若发送就必须校验，而已确认支持 PKCE 的客户端可按 RFC 9700 依 PKCE 防回调 CSRF。OIDC Code Flow 的 nonce 可选，若发送则须与 ID Token 中的值匹配。客户端验证 ID Token 后建立自己的会话，API 则独立验证面向自身的 access token，并按当前主体、租户和权限做运行时授权。refresh token 只向授权服务器换取新 access token；撤销传播可能有延迟，应用会话、IdP 会话和 API 对已签发 access token 的接受边界要分别处理。

See [OpenID Connect Core 1.0, incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice (January 2025)](https://www.rfc-editor.org/rfc/rfc9700.html), [RFC 7636, Proof Key for Code Exchange (September 2015)](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009, OAuth 2.0 Token Revocation (August 2013)](https://www.rfc-editor.org/rfc/rfc7009.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).


**Related notes / 相关笔记：** [Cross-tenant authorization / 跨租户资源授权](web-security-and-authentication.md) uses the validated subject to resolve current tenant membership; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) covers cookie fields and browser-origin transport.

**Sources / 来源：** [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html), [RFC 7636, PKCE](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009, Token Revocation](https://www.rfc-editor.org/rfc/rfc7009.html), [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html), and [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Guidance checked 2026-10-15. The Authorization Code Flow ID Token validation exception was checked against OIDC Core on 2026-10-27.
