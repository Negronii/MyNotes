# 怎样设计一个可持久查询的账户报表？

**案例：** 用户为账户 acct-17 请求报表 42，统计有限时间范围内的账户活动并导出 CSV。任务可能超出一次 HTTP 请求的时限；用户断开浏览器后仍要能查询结果，且结果保留七天。请求只读账户数据，但会消耗查询、连接、worker（工作进程）和对象存储资源。这里使用 `report-demo-208` 作为客户端幂等键，`job-demo-731` 作为持久任务 ID；账户与报表共同标识报表资源，报表 ID 42、任务 ID 和请求键是三个不同身份。

设计从用户结果、硬约束和负载开始，再选满足要求的最小架构。若一次有界同步读取总能在调用方截止时间内完成，直接返回报表更简单；若任务可能更久、需在断连后继续，或要独立准入突发工作，才引入持久 job（任务）、队列和 worker（工作进程）。这不是生产测量：本例沿用容量页的教学假设——平均 5 次提交/秒、10 分钟峰值 20 次/秒、worker 平均处理 6 秒、每请求约 8 KiB、至多 12 次顺序数据库读取、平均结果 128 KiB、结果保留七天。可由请求参数预先判定的范围超限，在接受任务之前拒绝；实际读取时若到第 12 页仍未取完，worker 停止并写入有界失败状态，不继续无上限读取；报表只读账户活动，不改写账户业务数据。所有用户可见路径都要重新授权；系统要限制未开始任务和数据库连接，并持久记录成功、失败或取消结果。

## 如何接受请求并让用户查询结果？

一个可用的 HTTP API（HTTP 应用接口）契约如下：

~~~http
POST /v1/accounts/acct-17/reports
Idempotency-Key: report-demo-208
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

`202 Accepted` 只表示已接受处理，不表示任务完成或最终必然成功。客户端之后可 `GET /v1/jobs/job-demo-731` 查询状态，`DELETE /v1/jobs/job-demo-731` 表示请求取消并保留可查询的 job 资源；若任务已终结，返回当前终态。只有成功且结果尚在保留期内，才可通过 `GET /v1/jobs/job-demo-731/result` 取回私有结果。`report.version` 表示报表展示数据的版本；job 的 `status` 和 `attempt` 表示这次导出的生命周期，两组字段不能互相推导。每个端点先验证当前调用者身份，再检查其是否可为 acct-17 创建/导出报表、访问该任务或读取其结果；路径中的账户号和难以猜测的 job ID 都不是授权凭据。`report:read` 不自动授予 `report:export`。worker 使用范围受限的服务身份，并在读取报表数据前重新验证提交主体当前仍有该报表的导出权限；若已撤销，就写入有界的 `authorization_revoked` 失败状态而不读取数据。接口的成功和错误表示应服从[HTTP API 契约](../backend/http-api-contracts.md)；断线后的未知结果如何查证见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md#超时和截止时间让调用方处于什么状态)。

idempotency key（幂等键）在本例按 `(account_id, principal_id, key)` 唯一；同键还绑定规范化请求指纹，其中包含 `reportId=42`、时间范围和格式。若键与指纹都匹配，返回已存在的 job；同键但 `reportId`、时间段或格式不同，则按本例契约返回冲突。仅先查再插入不能关闭竞态：两个相同请求可能都查不到。数据库唯一约束裁决胜者；失败方先回滚整笔事务，不新增等待槽，再读取胜者 job 并比较指纹。既有键的重放只返回原 job，不重新准入或占用第二个槽。请求指纹只用于比较，worker 重启所需的标准化报表参数必须另行持久保存。不要把原始请求正文或敏感筛选条件塞进队列消息。

本例把成功结果对象保留 7 天，从 `succeeded` 与对象引用一同提交、结果对用户可见时起算；job 状态和最小幂等映射保留到终态后 14 天，以覆盖更长的客户端重试窗口。结果对象过期时，job 仍是 `succeeded`，结果端点返回 `result_expired`，同键请求仍指向原 job，绝不重建一次导出。14 天后删除幂等映射就不再有窗口外重放保证；若服务要拒绝任意旧键，必须继续保留可识别它的墓碑。调用方在约定窗口外应先查证旧操作，不能把同一键当成全新意图。

job 行至少保存稳定的 job ID、账户与请求主体、`report_id`、已验证的标准化报表参数、请求指纹和幂等键、创建/到期时间、状态、取消请求、attempt（尝试号）、`lease_expires_at`（租约到期时间）、等待槽保留状态、私有结果引用以及范围受限的错误码。

| 持久状态 | 含义与转移 |
| --- | --- |
| `queued` | 请求已提交，尚无 worker 领取当前排队轮次；可以仍待 outbox（事务型发件箱）发布，也可以已经在队列中。每个排队轮次持有一个等待槽。 |
| `running` | worker 已通过 conditional update（条件更新）领取当前尝试，等待槽已释放。`lease_expires_at` 到期使恢复器可以尝试接管；到期本身不自动撤销当前尝试。 |
| `succeeded` | 当前尝试的私有对象已写好，数据库已将结果引用与成功状态一起提交。 |
| `failed` | 不可重试错误或尝试耗尽后写入的终态，客户端能查询有界错误码。 |
| `cancelled` | 取消在完成提交之前生效的终态；不暴露结果对象引用。 |

`cancel_requested` 是独立布尔字段，不是任务状态：运行中的任务可保持 `running` 同时收到取消请求。终态一经提交就不再变成其他终态。租约到期后，恢复器按数据库当前时间才有资格提交接管；原 worker 在接管事务成功提交之前仍可能完成，租约时刻本身不撤权。成功、取消和恢复接管都用条件更新比较当前 `status`、`attempt` 与 `cancel_requested`，并只接受更新一行的胜者；先提交的一方决定后续状态。恢复器若赢得条件更新，则把尝试标为已取代，旧 worker 后续完成更新会因状态或 attempt 不匹配而失败。outbox（事务型发件箱）另有 `pending` / `published` 状态；`published` 表示 relay（中继器）已按选定 broker 的确认、路由和持久性契约记录发布结果，不表示 worker 已处理或 job 仍处于 `queued`。队列消费者的 acknowledgement（消费者确认，ACK）也不属于 job 状态。

## 任务、发件箱与队列怎样交接？

在同一个数据库事务中插入唯一 job、`pending` outbox 行，并原子预留一个共享等待槽；仅在计数未达到 240 时提交，否则回滚并在 **202 之前**拒绝过载请求。所有 API 副本都通过同一数据库计数规则争用槽位。队列载荷只需携带 job ID；每个 outbox 发布意图还需自己的唯一 ID 和发布状态，relay 只确认对应意图，不能让旧发布确认覆盖重新排队产生的新意图。等待槽跟随逻辑 job 的当前排队轮次：任务尚未被 worker 领取时，不论仍在 outbox 还是已经排入 broker，都只占一个槽；重排再次占一个槽，领取时释放；一条消息被重复投递也不新增槽位。

~~~mermaid
flowchart TD
    A[认证、授权并校验报表范围] --> T[同一数据库事务：job、outbox、一个等待槽]
    T -->|提交成功| R[返回 202 与稳定状态 URL]
    T -->|槽满或键冲突| X[回滚：拒绝过载，或查询同键结果]
    T -->|提交后| L[relay 发布 job ID]
    L --> Q[broker 按所选契约确认发布]
    Q --> O[outbox 标为 published；job 状态独立推进]
~~~

发布确认只结束发送端的一步。消费者继续按持久 job 状态推进：

~~~mermaid
flowchart TD
    Q[收到 job ID] --> W[条件领取：running、增加 attempt、释放等待槽]
    W --> Read[按已存参数读取有界数据]
    Read --> Obj[写当前 attempt 专属的私有对象]
    Obj --> Guard{仍是当前 attempt，且没有取消？}
    Guard -->|是| Done[提交 succeeded 与对象引用]
    Guard -->|否| Orphan[不发布此对象；按权威状态取消或延后]
    Done --> Ack[终态持久后确认消息]
~~~

读写失败、重复投递和租约超时不会跳过这些边界；下面分别说明它们怎样恢复。


数据库提交与队列发布是两个系统的写入，不能放进一个普通数据库事务。若先提交 job 后直接发布，进程可能在两步之间崩溃，导致永远无人处理的任务；若先发消息再提交，数据库回滚后队列会出现不存在的任务。outbox 把 job 和待发布记录一起提交；relay 读取并重试发布，只有按所选 broker 的契约验证发布确认、路由与所需持久性条件后才更新 outbox。relay 若在 broker 接收后、更新 outbox 前崩溃，可能再次发布，所以 worker 按 job ID 幂等领取；已确认的 outbox 行也要按保留策略清理。发布者确认和消费者 ACK 是两个独立边界；即使 relay 记录 `published`，worker 也可能已经领取任务甚至写入终态。数据库事务不覆盖 broker，也不覆盖对象存储。[队列确认页](../reliability/queue-delivery-and-acknowledgement.md)详解 broker 语义。

> [!example] job-demo-731 的一次正常完成
> 在这个明确的顺序示例中，relay 先验证所选 broker 契约并更新 `outbox=published`，之后 worker 才领取；因此这一时刻 `job=queued`、等待槽占用 1。worker 原子领取后，job 变成 `running`、attempt=1，等待槽归还。worker 写私有对象并提交结果引用后，job 才变成 `succeeded`；消费者随后按 broker 契约确认消息。真实系统中 worker 可能在 relay 更新 `published` 前就已领取，因此 outbox 状态、job 状态和消费者确认不能互相推导。

## 工作进程重试怎样避免旧结果覆盖新结果？

worker 领取任务时，以条件更新检查状态仍为 `queued`，递增 attempt 并设置有界租约，同时释放这个排队轮次的等待槽。另一个当前 attempt 仍持有任务时，重复投递不能另起并行工作，应按所选队列契约延后或确认重复消息。worker 崩溃后，恢复器用数据库当前时间检查 `lease_expires_at`，再按 `job_id` 和 attempt 做条件接管：先检查 `cancel_requested`；若已请求取消，直接写 `cancelled`，无需争用槽位。否则只有恢复任务取得一个新的共享等待槽，才能在同一数据库事务中把 job 改回 `queued` 并写入新的 `pending` outbox 发布意图；relay 持续重发该意图直到满足选定 broker 契约。若无槽，写入可查询的 `capacity_exhausted` 终态，但不能把已取消任务写成容量失败。该闭环确保只改 job 行不会让消息凭空重新可达；新旧重复消息都由条件领取规则消重。

attempt fencing（尝试号栅栏）以单调递增的 attempt 号隔离新旧 worker；每次 attempt 用不同、只创建一次的对象键，例如 `reports/job-demo-731/attempt-2.csv`。先将私有对象写入该键，再用 compare-and-set（比较并交换，CAS）条件更新，比较 `job_id`、`status='running'`、当前 `attempt` 和 `cancel_requested=false`。只有恰好更新一行，才提交 `succeeded` 和对象引用并让结果对用户可见；零行表示接管、取消或终态已先提交。worker 不以 `lease_expires_at` 到期时刻单独拒绝自己，胜负由这些持久条件更新的提交顺序决定。对象写入与数据库仍是两个持久系统；上传后进程崩溃可能留下未引用对象，但垃圾回收不能只按“当前无引用”立即删除：只有 attempt 已被接管或 job 已终结、数据库确认无引用，并且有上界的上传时限和额外安全宽限都已过去，才可回收。即使已失效的旧 worker 仍晚到上传，其对象也不能获得有效结果引用；后续清理仍需处理这类迟到的孤儿对象。S3 的 `If-None-Match: *` 是一种防止同名对象被覆盖的条件写法；本设计依赖的是“每次尝试使用不同键，且仅由数据库当前 attempt 引用”，并不要求选 S3。

具体时序：worker A 领取 attempt 1 后停顿，租约到期但恢复器尚未接管；此刻 A 仍可能先提交成功。若恢复器先提交接管事务，job 变回 `queued` 并新增 outbox 意图，随后 B 领取 attempt 2；A 再恢复时，`WHERE attempt = 1 AND status = 'running'` 更新零行，不能引用自己的对象。若 B 已发布结果引用，A 的不同对象键也不能覆盖它。对象是否可见由数据库当前 attempt 的条件提交决定，租约到期时间本身不作栅栏。

取消只是请求停止，并非证明计算已停止。API 将 `cancel_requested=true` 持久化；若 `queued` 任务仍占有当前排队轮次的槽位，API 可用条件状态转移将其置为 `cancelled` 并释放该槽，之后到达的重复消息只按权威终态处理。领取与取消若同时竞争同一行，条件状态更新决定唯一结果：取消先提交时，worker 不能再领取；领取先提交时，任务转为 `running`，worker 随后检查取消标志。若 `running` 任务收到取消后 worker 崩溃，恢复器过期接管时先写 `cancelled`，不会重新排队或因槽位不足写容量失败。运行中的 worker 还要在有界数据页之间以及发布结果前检查。worker 的完成更新与取消终态更新都比较当前 attempt 和取消字段：如果取消先提交，当前尝试不再能转为成功；若成功终态先提交，后到的取消请求返回当前终态。浏览器断开只结束连接；202 已持久接受的 job 会继续，只有向 `DELETE /v1/jobs/{id}` 显式请求取消才改变任务状态。202 之前尚未被接受的请求级工作可以在断开后结束。

## 何时应排队，怎样设容量边界？

若代表性报表稳定满足调用方截止时间和尾部时延目标，同步接口更简单：校验输入、执行有界查询、返回 CSV，无需 queue、outbox relay、worker、状态轮询和结果清理生命周期。任务可能超过请求预算、必须在断连后可查，或突发流量需要与 API 执行隔离时，才选择异步路径。队列能保存等待和隔离故障，但不会凭空增加处理能力。

沿用[容量与背压页](../reliability/api-capacity-and-backpressure.md)的估算：64 个 worker 槽、准入目标 7 次/秒、30 个任务的短时突发，以及共享上限 240 个已接受未开始任务；应用连接池总上限是 200。若把峰值 20 次/秒持续按平均 6 秒处理，平均需要约 `20 × 6 = 120` 个并发 worker；64 个槽不能长期消化该到达率，因此准入规则要限流/拒绝，等待队列也不能无界增长。未开始任务包括 outbox 中尚未发布的任务。若 broker 暂时不可用，已接受任务仍占槽；槽已满时 API 必须在 **202 之前**返回过载错误。数据库不可用时无法持久接受任务，也不能声称已受理。

> [!info] 用平均到达率估算并发，不等于压测结果
> Little's law（利特尔法则）给出稳态关系：平均在途任务数约等于平均到达率乘以平均处理时长。若 20 次/秒持续到达且每项平均 6 秒，`20 × 6 = 120` 是近似并发需求；它不包含长尾、突发与失败重试，不能替代压测和限流。

部署与运行时保留以下检查：API、relay 与 worker 的任务表结构兼容，使升级期间旧任务仍可完成；按本例分开的 7 天结果与终态后 14 天状态/幂等元数据策略清理；限制重试数、对象上传时长和每次工作时长；监测 API 接受时延、pending outbox 的最老等待时间、数据库中最老 `queued` job 年龄、broker 最老消息年龄与深度、活跃 worker 槽、任务完成分位数、连接池等待与 SQL 耗时、对象存储用量、重试、取消和终态结果。broker 队列指标正常不能证明数据库中没有积压；`pending outbox` 或 `queued` 年龄持续增长都表示处理路径跟不上。发布时保留回滚路径，并考虑已经按旧 schema 接受的任务。


**继续阅读：** [数据库约束与索引](../databases/database-constraints-and-indexes.md)说明唯一键与查询路径；[事务隔离与 WAL](../databases/database-transactions-isolation-and-recovery.md)说明数据库内提交边界；[数据访问与连接池](../backend/data-access-and-connection-pools.md)说明每个请求/attempt 的 ORM 与连接生命周期；[HTTP 协议与 WebSocket](../networking/http-protocols-and-websockets.md)说明客户端状态查询的传输边界；[可观测性、服务目标与事件响应](../reliability/observability-slos-and-incident-response.md)说明阶段指标。更长的设计检查清单见[AI 系统设计案例](../../ai-engineering/systems/ai-system-design-interview-questions.md)。

> [!info]- 来源
> - `202 Accepted` 表示已接受但尚未完成的 HTTP 语义：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.3.3，核对于 2026-11-06。
> - 同一数据库事务内的提交边界、唯一约束和并发行为：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)、[Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) 与 [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，核对于 2026-11-06。
> - 数据库与消息通知的双写故障、outbox 重复发布及消费者幂等：[AWS Prescriptive Guidance, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-06。
> - 发送端 publisher confirms 与消费端 acknowledgements 是两个独立边界；RabbitMQ 的 unroutable/持久消息行为：[RabbitMQ 4.4, Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-06；本架构只要求按最终选择的 broker 契约确认。
> - 按对象名防止覆盖的条件写入示例：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-06；S3 只是可选实现。
> - 从需求、约束与运行目标选择架构：[Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)，核对于 2026-11-06。
