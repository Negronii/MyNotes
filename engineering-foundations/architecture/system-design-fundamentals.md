# How would you design a durable account report? / 怎样设计可持久查询的账户报表？

Start with the user's outcome and hard constraints, then choose the smallest architecture that satisfies them. This account report can outlive an HTTP request, so persist a job with a stable status URL. Commit the job, its outbox record, and one bounded waiting-slot reservation together; publish the job ID from the outbox; and let a worker write an immutable result for its attempt. Only a conditional database update for the current attempt can make that result visible. The same scoped idempotency key resolves a repeated submission to the same job, while a status lookup resolves a lost response. / 从用户要完成的结果和硬约束开始，再选择满足它们的最小架构。本账户报表可能超过一次 HTTP 请求的时限，因此应持久化 job 并返回稳定的状态 URL。在同一事务中提交 job、outbox 记录和一个有界等待槽；再由 outbox 发布 job ID，并由 worker 为当前 attempt 写入不可变结果。只有针对当前 attempt 的条件更新才能让结果对外可见。相同作用域的幂等键使重复提交回到同一个 job，状态查询则用来处理响应丢失。

**Key terms / 关键术语：** requirement / 需求；constraint / 约束；job / 任务；idempotency / 幂等性；transactional outbox / 事务型发件箱；conditional update / 条件更新；admission control / 准入控制；attempt fence / 尝试栅栏。

## Structure the design / 如何组织设计过程

Clarify the task and success criteria; state workload, latency, privacy, budget, and ownership constraints; trace the request and data paths; examine the risks that could change correctness or capacity; then specify evaluation, rollout, and rollback. This is a reusable discussion method, not a reason to add an unrelated component. See [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) for the longer checklist.

## Requirements and constraints / 需求与约束

A user asks for a CSV report over a bounded account time range. The report reads account activity, may take several seconds, and should remain retrievable for seven days even if the browser closes. Users can check progress and request cancellation. Reports are read-only: they do not change account activity. Validate and bound the input range and query to at most 12 sequential reads; reject an oversize request before accepting work.

Use the estimates in [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md): average 5 submissions/s and a 10-minute peak of 20/s; 6 s mean worker time; 8 KiB request; 12 sequential database reads; 128 KiB average result; and a seven-day result-retention target. These are teaching assumptions for comparing choices, not production measurements. The design constraints are: authorize every user-facing path; do not lose accepted work between the database and queue; bound waiting work and connection use; and preserve an explicit result or failure that can be queried after disconnect.

## API contract and data ownership / API 契约与数据所有权

One chosen API contract is:

~~~http
POST /v1/accounts/acct-17/reports
Idempotency-Key: report-demo-208
Content-Type: application/json

{"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731

{"jobId":"job-demo-731","status":"queued","statusUrl":"/v1/jobs/job-demo-731"}
~~~

The **202** response means the request was accepted for processing; it does not say that processing completed or will necessarily succeed. **GET /v1/jobs/{jobId}** returns current job state; **DELETE /v1/jobs/{jobId}** records a cancellation request; and **GET /v1/jobs/{jobId}/result** returns the private result only after authorization and completion. The status resource tells the client the later outcome. If the original response is lost, [work out what the caller can confirm / 判断调用方能确认什么](../reliability/api-reliability-and-async-delivery.md#Where%20a%20timeout%20leaves%20the%20caller%20/%20%E8%B6%85%E6%97%B6%E5%90%8E%E8%B0%83%E7%94%A8%E6%96%B9%E5%A4%84%E4%BA%8E%E4%BB%80%E4%B9%88%E7%8A%B6%E6%80%81) before repeating the operation. This follows [HTTP API Contracts / HTTP API契约](../backend/http-api-contracts.md) for endpoint shapes and [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) for protocol semantics.

Scope an idempotency key to (account, requesting principal, key) and enforce that scope with a database unique constraint. First look up an existing key: return its job when the normalized-request fingerprint matches, and report a conflict when it differs. If absent, insert the job under the unique constraint, add the outbox row, and conditionally reserve a waiting slot in one transaction before commit. If a concurrent same-key insert wins, the loser rolls back before reserving, loads the existing job, and compares fingerprints; lookup-then-insert alone is racy. These are explicit choices for this example, not rules every API must use. Define the success and error schema as part of the service's endpoint contract.

Authenticate first, then check that the principal may create a report for the account in the path. A caller-supplied account ID selects a resource; it does not prove permission. Every later status, cancellation, and result request checks access to the job's stored account; knowing a job ID does not grant access. The worker uses a narrowly scoped service identity to read only the stored account and report range. See [Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md) for the shared authorization boundary.

Store a job row with a stable job ID, account ID, requesting principal, validated normalized report parameters such as period/range/format, normalized request fingerprint, idempotency key, current status, creation/expiry times, cancellation request, attempt number and lease expiry, waiting-slot reservation state, private result reference, and a bounded error code. The parameters let a restarted worker rebuild its input; the fingerprint only compares requests and cannot recover them. Do not retain the raw request body or put sensitive filters in queue messages. A separate outbox row holds the job ID and publication state.

Use one database-backed counter for the 240 shared waiting-job reservations. Commit the new unique job, outbox row, and one slot reservation together only when the count is below 240; otherwise roll back and reject before **202**. If the unique-key insert loses a concurrent race, its transaction rolls back without consuming a slot before resolving the existing job. The reservation follows that logical job while it is unpublished in the outbox or waiting in the broker, so a broker copy does not consume another slot. A guarded state transition releases it once when a worker first starts the job or when it becomes terminal before starting. A retry or lease-expiry recovery that returns work to waiting must reserve a slot again before requeueing; if no slot is available, record a visible terminal failure instead of growing the backlog beyond the bound.

## Request, queue, and result path / 请求、队列与结果路径

~~~mermaid
flowchart LR
    C[Client submits report] --> A[Authenticate, authorize, validate bounded range]
    A --> T[One DB transaction]
    T --> J[Insert unique job]
    T --> O[Insert outbox row]
    T --> R[Reserve one shared waiting slot]
    J --> Commit[Commit]
    O --> Commit
    R --> Commit
    Commit --> Accepted[Return 202 with stable job ID and status URL]
    Commit --> Relay[Outbox relay publishes job ID]
    Relay --> Q[Durable queue]
    Q --> W[Worker conditionally claims attempt and releases waiting slot]
    W --> Read[Read stored parameters and authorized account pages]
    Read --> Obj[Write immutable object key for this attempt]
    Obj --> Conditional{Current attempt and not cancelled?}
    Conditional -->|yes| Visible[Commit terminal state and result reference]
    Conditional -->|no| CheckState{Cancellation or stale attempt?}
    CheckState -->|current attempt cancelled| Cancelled[Commit cancelled terminal state without result]
    CheckState -->|stale or already terminal| Hidden[Leave attempt object unreferenced]
    Visible --> Ack[Acknowledge queue delivery after durable outcome]
    Cancelled --> Ack
    Hidden --> Terminal{Job is already terminal?}
    Terminal -->|yes| Ack
    Terminal -->|no| Defer[Defer under the broker redelivery contract]
    C --> Status[Query job status or result through authorized API]
    Visible --> Status
~~~

This picture distinguishes three durable systems. The job and outbox rows share one database transaction; the queue confirms publication under its own rules; the private object is separate again and becomes visible only through the conditional job update. Acknowledgement follows the durable job outcome, not merely queue receipt. General broker confirmation and redelivery behavior is explained in [Publisher confirms and consumer acknowledgements / 发布者确认和消费者确认分别证明什么？](../reliability/queue-delivery-and-acknowledgement.md).

### Outbox publication and worker attempts / Outbox 发布与 worker 尝试

The job row and outbox row commit together. Otherwise a process can commit the job and crash before publishing it, or publish a message for a transaction that later rolls back. The relay retries publication and records delivery after broker confirmation. It may publish twice if it crashes after broker acceptance but before recording delivery, so the worker deduplicates by job ID rather than relying on a single delivery. This is the transactional-outbox trade-off: durable relay state avoids a database-plus-queue dual write, while duplicate handling and outbox cleanup remain necessary. A database transaction does not extend to the queue or object store.

Before doing work, a worker reloads the job and acknowledges a delivery immediately if the job is already terminal. If another unexpired attempt owns it, the worker does not start duplicate work and defers the delivery according to the broker's retry/redelivery contract. Otherwise a conditional update claims an eligible waiting job by incrementing its attempt number, setting a bounded lease, and releasing its reserved waiting slot. After a worker loss, recovery returns the job to waiting only after the lease expires and another slot is reserved; a redelivery cannot bypass that bound.

The attempt number fences late workers. Each claim writes to a create-only, never-reused object key containing both job ID and attempt number. A result becomes visible only when a conditional database update still matches the running job's current attempt, with cancellation not already requested, and commits the private object reference with the terminal state. If the update affects no row, that attempt lost and its object remains unreferenced for retention cleanup. When the allowed attempts are exhausted, conditionally record a terminal error for the current job so clients can see the failure.

For example, worker A claims attempt 1 and stalls until its lease expires. Worker B claims attempt 2, writes a different result key, and commits the completed state and attempt-2 reference. If A later resumes, its attempt-1 key cannot overwrite B's object, and its conditional job update no longer matches; the completed job short-circuits any later duplicate delivery. A crash after upload but before the conditional update similarly leaves only an unreferenced attempt object. Acknowledge the winning attempt after the durable outcome; queue delivery alone is not user-visible completion.

### Cancellation and completion race / 取消与完成的竞态

Cancellation is a request, not proof that work stopped. The API records it; a worker checks between bounded pages and before publishing the result. Completion and cancellation can race, so both terminal transitions check the current attempt number and cancellation state. If the cancellation request wins before result commit, the current worker records a cancelled terminal state without a result reference; if the completion transition wins first, later cancellation cannot change the terminal outcome. A stale attempt cannot publish its object or change the job. Only the authoritative conditional transition determines the visible state.

## When to queue this work / 什么时候使用队列

If representative reports consistently fit within the caller's request deadline and an acceptable tail-latency target, a synchronous endpoint is simpler: validate, run the bounded reads, return the CSV, and remove the queue, outbox relay, worker deployment, status polling, and result cleanup lifecycle. Use the asynchronous path when a request may exceed that deadline, results must survive a disconnect, or measured bursts require work to be admitted and drained independently of API processes. The queue adds durable waiting and failure isolation, but also adds operational state and delay; it does not create processing capacity.

## Size and operate the design / 估算容量并运行设计

For this workload, use the 64 worker slots, 7/s sustained admission rate, 30-job burst, shared 240 accepted-but-not-started-job bound, and 200-connection application-pool ceiling from the linked sizing example rather than copying its arithmetic here. At sustained 20/s offered traffic, the service must reject work after its admission bound; accepting all of it would require about 120 concurrent workers at the assumed 6 s mean service time. Before changing the design, measure API acceptance latency, queue age and depth, active worker slots, job completion percentiles, database checkout wait and query time, object bytes retained, retries, cancellation outcomes, and completed reports. An old queue with rising oldest-message age is overload even if the API still accepts requests.

Deploy API, relay, and workers with compatible job schemas so old jobs can finish during a rollout. Retain result objects for seven days; delete expired objects and metadata under the chosen retention policy; and bound retries and deadlines so a bad report cannot occupy a worker forever. If the queue is unavailable, accepted-but-not-started jobs stay in the outbox and continue consuming the same reserved slots; once all 240 are reserved, reject new submissions before **202**. If the database is unavailable, the API cannot durably accept the job and must return an error rather than imply success. Roll out with health checks and a rollback path that accounts for jobs already accepted under the previous schema. For the arithmetic behind the worker, database, and retention budgets, see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md). For stage-level indicators and alerting, see [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](../reliability/observability-slos-and-incident-response.md).

**How would you answer “How would you design a report that may outlive an HTTP request?” / 如何回答“如何设计一个可能超过 HTTP 请求时限的报表任务？”** I would first confirm report size, response deadline, retention, access owner, and acceptable failure behavior. If measured tail latency fits the request budget, I would keep it synchronous. For the stated multi-second report, I would persist the job and outbox in one database transaction, return a stable status URL, and let a bounded worker create a private result. Retries use the scoped idempotency key, and each worker attempt writes a distinct immutable object. A guarded update makes only the current, non-cancelled attempt visible; acknowledge the queue message after the durable outcome. The client queries job state after disconnect rather than inferring completion from a response or message delivery. / 我会先确认报表规模、响应期限、留存期、数据所有者和可接受的失败行为。如果实测尾部时延满足请求预算，就保持同步。对于本例需要数秒的任务，我会在同一数据库事务中保存 job 与 outbox 并返回稳定的状态 URL，再由有界 worker 生成私有结果。重试使用有作用域的幂等键，每个 worker 尝试写入不同且不可变的对象。只有当前且未被取消的尝试可以通过条件更新让结果可见，并在持久化业务结果后确认队列消息；客户端断连后应查询 job 状态，而不能从响应或消息是否投递推断完成。

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) owns unknown outcomes and safe retries; [Sizing and bounding asynchronous work / 容量估算与背压](../reliability/api-capacity-and-backpressure.md) retains the detailed estimates; [Publisher confirms and consumer acknowledgements / 队列确认与重投](../reliability/queue-delivery-and-acknowledgement.md) explains broker-level confirmation boundaries; [HTTP API Contracts / HTTP API契约](../backend/http-api-contracts.md) covers endpoint and error conventions; [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md) explains ORM sessions and process-local pool limits; [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers constraints and transaction semantics; [Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md) owns identity and resource authorization; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) owns transport and reconnect semantics; [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md) shows a separate durable-run contract; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) explains how the client surfaces stream and disconnect state; [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](../reliability/observability-slos-and-incident-response.md) covers stage-level production signals.

**Sources / 来源：** [RFC 9110 §15.3.3, 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3); [PostgreSQL 18: Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html) for the database-local all-or-nothing boundary; [PostgreSQL 18: Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) for scoped uniqueness and [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) for concurrent transaction behavior; [AWS Prescriptive Guidance: Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) for dual-write failure and duplicate-publication boundaries; [Amazon S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) as one create-only object-write mechanism, not a requirement to choose S3; [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) for workload requirements, operational focus, and starting with a simple design, checked 2026-10-15.
