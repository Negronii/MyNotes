# 无人值守 Agent 怎样在用户授权内继续第三方操作？

**案例背景。** 以下是合成教学案例。同一 run-r42-7 已用只读调用 c1 从 MCP 日志服务取得 build 42 的观察：reject_empty_name 预期 HTTP 400、实际 200。用户要求应用解释失败，并为 repository_id=build-service 准备缺陷单，提交前让用户审批。工单 provider 账号是 OAuth 身份，build-service 是动作目标；两者不是同一个标识。运行时要用用户对工单 API 的委托授权，但不能把创建权限交给模型，也不能把此前读日志的令牌拿去创建 issue。

无人值守只表示用户不必为每个内部步骤重新登录；它不表示授权无限期有效，也不表示用户授予一个 API scope 就批准了任意动作。完整链路要把用户会话、OAuth grant、动作批准和远端副作用记录分开保存。

本例中的 `attempt` 是同一 run/action 下的一个 worker 执行代次；它可以负责发送，也可以在恢复时只做对账。一次 HTTP 重试不一定产生新的 attempt。租约是 worker 暂时获准更新本地动作状态的资格，带有代次和到期时间。旧 worker 即使还活着，也不能在租约过期后提交状态；但本地租约不能阻止已经暂停的 worker 稍后把请求发到远端。

下图展示正常创建路径，以及必须停止或转入恢复的入口。撤权、租约失效和远端结果未知时的处理在后文逐步展开。

~~~mermaid
flowchart TD
    U[用户绑定工单账号；完成 OAuth 授权] --> G[秘密存储保存凭据；运行仅关联 grantRef]
    G --> R[run-r42-7 读取 c1 日志观察]
    R --> M[模型提出 create_issue 草稿 c2]
    M --> V[核验当前用户、目标 repository 与所需 scope]
    V -->|不允许| STOP[停止；不得创建 issue]
    V -->|允许| H[展示精确草稿与证据，等待用户审批]
    H -->|拒绝或取消| STOP
    H -->|批准| C[必要时刷新令牌；重读 grant、草稿、审批与取消状态]
    C -->|失效或不匹配| STOP
    C -->|仍有效且获批| I[条件校验当前 attempt 与未过期租约；持久化操作键、摘要和发送意图]
    I -->|条件失败| STOP
    I -->|提交成功| X[向 issue API 发送专属 token 与同一操作键]
    X -->|成功且写回资格仍有效| S[条件写回 issue ID 和收据；按实际结果收尾]
    X -->|结果未知或写回资格失效| Q[进入恢复流程：核对回执或合法只读对账；不得直接重发]
~~~

恢复流程只有在确认原任务仍有效、排除了旧 attempt 迟发和接收端延迟提交、且接收端同键同摘要的去重保证仍在保留窗口内时，才可能返回审批步骤继续。若权威查询已确认没有副作用，但任务已取消或继续写入条件不满足，就记录“未创建”并停止；无法排除迟发或延迟提交时保持 `effect_unknown`。重新授权产生的新 grant 不继承旧动作批准。

## grant 为什么不能等同于登录会话或一次动作批准？

应用会话确认当前浏览器或客户端对应哪个本地用户；OIDC 身份层和应用自己的会话建立方法见[Cookie 会话与 OIDC 令牌怎样建立身份？](../../engineering-foundations/security/web-sessions-and-oidc.md)。OAuth grant 则记录用户把哪些第三方资源和 scope 委托给哪个 client。它通常通过授权码流程取得，并由运行时把它绑定到当前本地用户、tenant 和 provider account。一个登录 cookie 不会自动变成第三方 API token。

运行时还要为某个写动作记录独立的审批和副作用状态：

| 记录 | 例子 | 它能说明什么 |
|---|---|---|
| 应用会话 | 本地账号 user-17 当前已登录 | 谁在应用内发起任务；不授予 ticket API 权限 |
| 用户授权 grant | grantRef=g-31，用户 user-17，tenant=team-4，provider account=repo-owner-2 | 此用户对指定 resource/audience 和 scopes 的委托；不批准某一条正文。provider account 是 OAuth 身份，不是目标仓库 ID |
| 任务身份 | runId=run-r42-7 | 这次持久运行的身份；不是 OAuth 凭据 |
| 模型工具调用 | 后续 create_issue 请求的 call_id=c2 | 一次模型提出的动作；不是外部去重键 |
| 动作审批 | repository_id=build-service、标题、正文和 c1 证据的精确摘要 | 用户批准本次明确预览；内容或目标改变时应重新审批 |
| 远端操作键 | run-r42-7:create-issue:v1 | 接收端去重或查询这次副作用的稳定键；是否有效由接收端契约决定 |

grant 记录保存 grantRef、用户/tenant、provider account、resource URI 或 audience、实际授予的 scope、到期与 refresh 状态，以及到加密秘密存储的凭据引用。运行、动作摘要、审批状态和操作键保存在各自的任务与动作记录中，并通过 grantRef 关联。本例 provider account=repo-owner-2 是 OAuth 身份，repository_id=build-service 是同一 run 的目标仓库；两者可以不同。access token 和 refresh token 不进入 prompt、模型消息、事件流、普通日志、tool result 或 checkpoint。`access token` 短期用于向目标 API 发请求；只有 provider 实际发放 `refresh token` 时才保存它，并且只把它交给所属授权服务器的 token endpoint 换取新的 access token。

## 两条 OAuth 链分别在谁和谁之间？

MCP 日志读取是 host/client 到 MCP server 的受保护资源访问。host/client 向日志 MCP 授权服务器请求并取得 T_mcp；该 token 的 audience/resource 是日志 MCP resource。工单创建是 Agent runtime 代表用户访问工单 API，使用 T_issue；其 audience/resource 是工单 API，并且受用户授予的 issue scope 约束。两条链的授权服务器、资源标识和权限范围可能不同。即使两个 token 都采用 Bearer 传输，也不能互换或透传。

~~~mermaid
sequenceDiagram
    participant H as host/runtime
    participant AM as 日志 MCP 授权服务器
    participant MS as 日志 MCP server
    participant AI as 用户
    participant AT as 工单授权服务器
    participant TI as 工单 API
    H->>AM: 为 logs.example.test 请求 T_mcp
    AM-->>H: T_mcp，audience=日志 MCP resource
    H->>MS: read_build_log + T_mcp
    MS-->>H: JSON-RPC 响应；host 映射回此前的 c1
    H->>AI: 在浏览器打开授权服务器页面，带 state 和 PKCE challenge
    AI->>AT: 登录并同意工单 API 的委托 scope
    AT-->>H: 回调携带一次性短效授权码与 state
    H->>AT: token endpoint：授权码 + PKCE verifier
    AT-->>H: 面向工单 API 的 access token；若 provider 提供则另有 refresh token
    H->>AI: 展示绑定 repository、正文和 c1 证据的 c2 预览
    AI-->>H: 批准这份精确的 issue 草稿
    H->>TI: create_issue + T_issue + 稳定操作键
    TI-->>H: issue ID 或明确失败
~~~

每个调用目标都要校验它收到的 token 是否由预期 issuer 签发、是否仍有效、audience 是否覆盖这个 resource、scope 是否足够。授权服务器支持时，client 用 OAuth resource 参数请求目标资源；这不会令所有 provider 都返回同一种 access token。Refresh token 只发给它所属的授权服务器 token endpoint，不能发给工单 API，更不能放进模型上下文。

## 一次长任务怎样在授权、刷新、审批和写入间前进？

### 先绑定 grant，再保存不含凭据的运行状态

用户在应用中已登录后，应用在浏览器打开 provider 的授权页面；用户登录并同意委托，provider 再回调一次性、短效授权码和 state。服务端验证 state、issuer 与回调后，带 PKCE verifier 到授权服务器的 token endpoint 换取 access token；若 provider 同时提供 refresh token，才加密保存它，后续只向同一 token endpoint 换取新 access token。然后，应用通过 provider 支持的账户身份机制或已获授权的账户接口确认第三方账号，把它与本地 user-17 / team-4 关联，并记录实际授予的资源和 scopes；不能把 OAuth 回调本身当成已验证的 provider account。运行状态只保存 g-31 这样的引用。

开始处理 build 42 时，运行数据包含已持久化的 c1 观察。模型依据它提出新调用 c2，参数包括目标 repository_id=build-service、issue 标题和正文。运行时核验用户仍有该仓库的动作资格，grant 仍对应正确 provider account 与 issue API，scope 包含创建需要的写权限，并把动作摘要与 run-r42-7:create-issue:v1 一起持久化。模型不能自行指定可用 token 或更换 resource。

### 在请求前刷新并重新检查待审批内容

访问令牌可能早于长任务到期，任务也可能跨越多小时甚至多天。运行时在实际发送前依据 provider 返回的到期信息决定是否向授权服务器刷新。启用了 refresh token rotation 的 provider 会在刷新时发新 refresh token 并使旧 token 失效；应以 grant 为粒度串行刷新，并在同一事务或可靠更新中替换秘密引用与版本，避免并发刷新把新 token 覆盖掉。刷新成功后，worker 仍要重新核验用户资格、grant、目标、精确动作摘要、审批和取消状态，再决定能否发送。provider 返回 invalid_grant、撤回或其他不可恢复错误时，把 grant 标成需重新授权，阻止尚未发送的写入，不回退到应用登录 cookie 或其他人的 token。

如果高影响动作需要确认，批准对象是精确的动作摘要，而不是“允许这个模型操作工单”。等待期间若标题、正文、repository_id、证据、当前用户资格、grant scope 或取消状态改变，原审批无效。真正调用前，worker 重新读取这些状态；审批与 grant 检查都要针对将发出的那一份内容成立。这个状态与审批后恢复同一 runId 的关系见[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../systems/ai-application-architecture.md)。

### 把秘密只送到它所属的资源

通过检查后，运行时取出或换取面向工单 API 的短期 access token，将其放入发往该 API 的 TLS 请求头，正文携带 issue 草稿和按接收端约定的操作键。MCP 入站的 T_mcp 不会转给工单服务；T_issue 也不会回传到模型。日志可记录用户/tenant、resource、scope、动作摘要、运行标识、审批 ID、操作键与结果状态，但不能记录 bearer 字符串、refresh token 或可还原它们的 URL。

发送前，worker 以条件事务核验当前 attempt、匹配的租约代次且租约尚未过期、预期运行与操作状态、获批动作摘要、当前写授权和取消标记，再持久化 effect_in_flight、原操作键与动作摘要；之后才发送请求。条件检查或更新失败时，必须停止且不得发送。这项事务只约束本地状态，不能向远端服务栅栏旧 worker：旧 worker 若在提交发送意图后暂停，即使租约已过期、恢复器已把状态转成 effect_unknown，它恢复后仍可能发出请求。

若收到成功响应，只有在条件事务确认当前 attempt 仍持有未过期租约时，worker 才能写回 issue ID、操作收据和动作结果。若运行带有 `cancel_requested`，应保留这项请求；当前恢复流程确认外部动作成功后，可按实际结果将运行转为 `completed` 并停止其余步骤。只有确认没有已发出或仍可能提交的副作用时，运行才终结为 `canceled`。条件失败的旧 worker 不得直接完成该运行，应把响应交由持有当前租约的恢复流程核对并条件写回。若发送超时，或 attempt 在记录终态前失联，先前写入的 effect_in_flight 无法证明请求没有发出；租约过期后，恢复器须保留原键和摘要、条件转入 effect_unknown，再先做合法对账，不能退回普通草稿步骤。相反，若刷新返回 invalid_grant 或撤权发生在持久化发送意图之前，当前 worker 明确停止且没有更早的未结清 attempt，则停止新写入本身不构成 effect_unknown。

## 用户撤权或令牌失效后怎样安全恢复？

用户主动在 provider 撤权、应用收到撤权通知或 refresh 返回 invalid_grant 时，运行时将 grant 标记为不可写，清除或撤销其秘密引用，并使依赖该 grant 的待审批草稿过期。若发送意图尚未持久化、当前 worker 已明确停止且没有更早的未结清 attempt，运行只有在未取消时才等待重新授权并重新核验；这本身不表示有远端副作用待核对。若动作已取消且没有旧 attempt，停止该动作，不能在重新授权后按原键提交一个此前未发送的效果。若旧 effect_in_flight attempt 失联，则不能据此推断请求未发出，恢复时按 effect_unknown 处理；撤权期间只允许合法查询和不会新建效果的对账，取得新 grant 后是否能恢复写入见下列条件。恢复器不得为已取消的运行发起新写入。若撤权后已发请求返回明确成功响应，仍须按前文相同的当前 attempt 与尚未过期租约条件写回 issue ID 和收据；失去资格的 worker 必须把回执交给当前租约恢复流程核对并条件写回。只有响应缺失或无法判定时才保持未知。RFC 7009 描述的是 client 通知授权服务器撤销 token；provider 可以同时影响同一 grant 的其他 token。资源服务器是否即时拒绝已经签发的 access token，取决于其验证和撤销机制。因此，撤权不会自动取消已在网络上的请求，也不能由 Agent 用一句“已取消”来代替状态对账。

若 create_issue 已发出或无法排除已发出、且结果未知，先停止新写入并保留原操作键、请求摘要与取消状态。然后只在仍有**合法且有效**的读取能力时查询同一操作键：

- 如果用户刚撤销了唯一 grant，且没有另一份已授权的只读 grant、接收端状态查询能力或其他合法审计接口，运行必须保持 effect_unknown。不能用已撤销的 token 继续查，也不能仅为“确认一下”而偷偷申请新 scope。
- 如果仍有合法只读查询权限，并且接收端给出权威结果，可将远端 issue ID 写回原操作记录。查询无结果只有在契约能排除旧 attempt 稍后发出请求、并能排除接收端对已收到请求的延迟提交时，才足以判定“未创建”；否则仍为未知。
- 用户重新授权后，得到的是新 grant，不能假定旧审批或旧 token 恢复有效。先用新授权的合法读取范围查询原操作键。若查询权威确认未创建，就记录“未创建”；run 已取消或继续写入条件不满足时停止，不把已知的无副作用误标为未知。只有原任务仍有效、没有旧未结清 attempt、用户对当前精确草稿重新审批，且接收端保证同键同摘要去重并仍在保留窗口内，才可受控恢复。查询不能排除迟发或延迟提交时，仍保留 effect_unknown 并请用户或管理员人工核查。

日志工具读到 c1 里的结果不会为 c2 增加工单 scope；获得写 scope 也不自动批准这份 issue 草稿。相同原则适用于长任务读取第三方日历或文档：Google Calendar 的 https://www.googleapis.com/auth/calendar.events.readonly scope 允许读取事件；创建或编辑事件需要实际授予相应的写 scope。Google 的 https://www.googleapis.com/auth/calendar.events scope 同时包含查看和编辑权限，因此申请它时仍需按实际 scope 告知用户。某些 provider 的创建 scope 会同时包含读取能力；应检查实际授予的 scope，不应把产品名当成最小权限保证。

相关机制：

- [浏览器会话与 OIDC 怎样确认身份并约束凭据受众？](../../engineering-foundations/security/web-sessions-and-oidc.md)：区分本地登录、身份令牌和面向 API 的访问令牌。
- [AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复？](../systems/ai-application-architecture.md)：沿同一操作键处理 effect_in_flight、effect_unknown 和恢复。
- [生产 AI 如何阻止不可信内容诱导模型越权？](../safety/ai-safety-in-production.md)：把动作预览、重新授权和停止规则连到运行时策略。
- [生产应用运行时怎样管理部署凭据？](../../engineering-foundations/infrastructure/production-application-runtime.md)：比较部署身份、短期工作负载令牌与用户 OAuth grant。

> [!info]- 来源
> 授权原则核验于 2026-11-09；token 期限和撤销传播随 provider 而异，Google 的 OAuth 与 Calendar scope 仅作 provider 特定例子。
>
> - **授权码与 PKCE、安全授权流程、受众限制和 refresh token 保护/轮换。** IETF [RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)，2025-01，检查 §§2.1、4.10.2、4.14；其中受众限制是对当前服务的建议，不保证所有 provider 以相同 token 格式实现。
> - **面向特定资源的 token 请求。** IETF [RFC 8707: Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707.html)，2020-02，检查 §§2–3 的 resource 参数及其资源身份语义；是否支持由授权服务器决定。
> - **token 撤销接口及同一授权 grant 中其他 token 的可能影响。** IETF [RFC 7009: OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009.html)，2013-08，检查 §§2–2.2；规范没有让调用方据此推断任意资源服务器已同步停止接受所有自包含访问令牌。
> - **provider 特定的 refresh token 获取与撤销示例。** Google for Developers，[Using OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)，检查 Offline access、Refreshing an access token、invalid_grant 和 Token revocation；[Choose Google Calendar API scopes](https://developers.google.com/workspace/calendar/api/auth) 确认 calendar.events.readonly 只读事件，calendar.events 可查看和编辑；这些是 Google 特定行为，不外推到其他授权服务器。
