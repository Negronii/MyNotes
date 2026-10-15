# System Design Fundamentals / 系统设计基础

**Core explanation / 核心解释：** Start with a user's outcome and hard constraints, draw the request and data paths, then choose the smallest architecture that meets them. In this worked example, a bounded account report is submitted as a durable job because generation can outlive an HTTP request. The job and outbox commit together; a scoped idempotency key maps a same-request retry to the same job, whose stored normalized parameters let a worker rebuild its input. Each attempt writes a distinct immutable result key, and only the current attempt can conditionally commit the terminal state and visible result reference. Exhausted attempts record a terminal error, and a conditional transition resolves a cancellation/completion race. / 从用户要完成的事情和硬约束开始，画出请求与数据路径，再选择满足它们的最小架构。本例中的账户报表可能超过一次 HTTP 请求时限，因此作为持久化任务提交。job 与 outbox 在同一事务中提交；有明确作用域的幂等键使相同请求的重试返回同一个 job，已保存的规范化参数让 worker 能重建输入。每次尝试写入不同且不可变的结果 key，只有当前尝试能通过条件更新提交终态和对外可见的结果引用。重试耗尽后记录终态错误；取消与完成发生竞态时，由条件状态转换裁决。客户端断连后查询任务记录，不能用响应是否丢失或消息是否投递来判断结果。

**Key terms / 关键术语：** requirement / 需求；constraint / 约束；data ownership / 数据所有权；job / 任务；idempotency / 幂等性；transactional outbox / 事务型发件箱；admission control / 准入控制.

## A shared way to structure a design / 通用设计思路

Use the sequence in [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) as a general discussion method: clarify the task and success criteria; state workload, latency, privacy, budget, and ownership constraints; trace the end-to-end path; examine the few risks that can change correctness or capacity; then specify evaluation, rollout, and rollback. It is a method, not a reason to import an AI component into an unrelated service.

## Worked case: asynchronous account report / 案例：异步生成账户报表

### Requirements and constraints / 需求与约束

A user asks for a CSV report over a bounded account time range. The report reads account activity, may take several seconds, and should remain retrievable for seven days even if the browser closes. Users can check progress and request cancellation. Reports are read-only: they do not change account activity. The input range and query are validated and bounded to at most 12 sequential reads; oversize requests are rejected before work is accepted.

Use the synthetic estimates in [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md): average 5 submissions/s, a 10-minute 20/s peak, 6 s mean worker time, 8 KiB request, 12 sequential database reads, 128 KiB average result, and a 7-day result-retention target. These are assumptions for comparing choices, not production measurements. The required constraints are: account authorization on every user-facing path; no accepted request disappears between the database and queue; bounded queueing and connection use; and a job result or explicit failure that can be looked up after disconnect.

### API, data, and ownership / API、数据与所有权

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

The 202 response means the request was accepted for processing, not that processing completed or will necessarily succeed. `GET /v1/jobs/{jobId}` returns the job's current state; `DELETE /v1/jobs/{jobId}` records a cancellation request; and `GET /v1/jobs/{jobId}/result` returns the private result only after authorization and completion. The status resource is how the client learns the later result; the HTTP connection is not the job. Scope an idempotency key to `(account, requesting principal, key)` and enforce that scope with a database unique constraint. First check an existing key: return its job when the normalized-request fingerprint matches, and report a conflict when it differs. If absent, insert the job under that unique constraint, add the outbox row, and conditionally reserve a waiting slot in one transaction before commit. If a concurrent same-key insert wins, the loser rolls back before reserving, loads the existing job, and compares fingerprints; lookup-then-insert alone is racy. These are explicit choices for this example, not rules every API must use. Define the success and error schema as part of the service's endpoint contract.

The API authenticates first, then checks that the principal may create a report for the account in the path. A caller-supplied account ID is a resource selector, not proof of permission. Every later status, cancellation, and result request checks access to the job's stored account; knowing a job ID does not grant access. The worker uses a narrowly scoped service identity to read only the stored account and report range. See [Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md) for the shared authorization boundary.

Store a job row with a stable job ID, account ID, requesting principal, validated normalized report parameters such as period/range/format, normalized request fingerprint, idempotency key, current status, creation/expiry times, cancellation request, attempt number and lease expiry, waiting-slot reservation state, private result reference, and a bounded error code. The parameters let a restarted worker rebuild its input; the fingerprint only compares requests and cannot recover them. Do not retain the raw request body or put sensitive filters in queue messages. A separate outbox row holds the job ID and publication state.

Use one database-backed counter for the 240 shared waiting-job reservations. Commit the new unique job, outbox row, and one slot reservation together only when the count is below 240; otherwise roll back and reject before 202. If the unique-key insert loses a concurrent race, its transaction rolls back without consuming a slot before resolving the existing job. The reservation follows that logical job while it is unpublished in the outbox or waiting in the broker, so publishing a broker copy does not add another slot. A guarded state transition releases it once when a worker first starts the job or when it becomes terminal before starting. A retry or lease-expiry recovery that returns work to waiting must reserve a slot again before requeueing; if none is available, record a visible terminal failure instead of growing the backlog beyond the bound.

### Request and data path / 请求与数据路径

~~~text
Client
  → API: authenticate, authorize account, validate bounded range
  → database transaction: insert unique job row + outbox row + reserve one waiting slot
  ← 202 with stable job ID and status URL

Outbox relay
  → durable queue: publish job ID, then mark outbox row delivered
  → worker: atomically claim an attempt and release its waiting slot, load stored parameters, read authorized account pages, build CSV
  → private object storage: write an immutable job-and-attempt-specific result
  → database: conditionally publish the winning result reference and terminal state
  ← queue acknowledgement after durable job outcome

Client
  → API: GET status or request cancellation
  → API: GET result only after authorization and completed status
~~~

The job row and outbox row commit together. Otherwise a process can commit the job and crash before publishing it, or publish a message for a transaction that later rolls back. The outbox relay retries publication; it may publish twice if it crashes after broker acceptance but before recording delivery. Therefore the worker deduplicates by job ID rather than relying on a single delivery. This is the transactional outbox trade-off: a small amount of durable relay state avoids a dual write, while duplicate handling and outbox cleanup remain necessary. PostgreSQL transactions provide an all-or-nothing boundary for the two database rows; they do not extend that transaction to the queue or object store.

Before doing work, a worker reloads the job and acknowledges a delivery immediately if the job is already terminal. If another unexpired attempt owns it, the worker does not start duplicate work and defers the delivery according to the broker's retry/redelivery contract. Otherwise a conditional update claims an eligible waiting job by incrementing its attempt number, setting a bounded lease, and releasing its reserved waiting slot. After a worker loss, recovery can return the job to waiting only after the lease expires and another slot has been reserved; a redelivery cannot bypass that bound. The attempt number fences late workers. Each claim writes to a create-only, never-reused object key containing both job ID and attempt number. A result becomes visible only when a conditional database update still matches the running job's current attempt, with cancellation not already won, and commits the private object reference with the terminal state. If the update affects no row, that attempt lost and its object remains unreferenced for retention cleanup; it cannot replace the winner.

For example, worker A claims attempt 1 and stalls until its lease expires. Worker B claims attempt 2, writes a different result key, and commits the completed state and attempt-2 reference. If A later resumes, its attempt-1 key cannot overwrite B's object, and its conditional job update no longer matches; the completed job short-circuits any later duplicate delivery. A crash after upload but before the conditional update similarly leaves only an unreferenced attempt object. Acknowledge the winning attempt after the durable outcome; queue delivery alone is not user-visible completion. The retry and acknowledgement boundaries reuse [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md).

Cancellation is a request, not proof that work stopped. The API records it; a worker checks between bounded pages and before publishing the result. Completion and cancellation can race, so the terminal update checks both the current attempt number and cancellation state; only the winning transition becomes authoritative. A disconnected client must query the job state rather than infer cancellation or completion from a lost response. For workflows that need durable checkpoints or reconciliation of an external side effect with an unknown outcome, see [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md).

### Why queue this work? / 为什么使用队列？

If representative reports consistently fit within the caller's request deadline and an acceptable tail-latency target, a synchronous endpoint is simpler: validate, run the bounded reads, return the CSV, and remove the queue, outbox relay, worker deployment, status polling, and result cleanup lifecycle. Use the asynchronous path when a request may exceed that deadline, results must survive a disconnect, or measured bursts require work to be admitted and drained independently of API processes. The queue adds durable waiting and failure isolation, but also adds operational state and delay; it does not create processing capacity.

### Sizing and operation / 容量与运维

For this workload, use the 64 worker slots, 7/s sustained admission rate, 30-job burst, shared 240 accepted-but-not-started-job bound, and 200-connection application pool ceiling from the linked sizing example rather than copying its arithmetic here. At sustained 20/s offered traffic, the service must reject work after its admission bound; accepting it all would require about 120 concurrent workers at the assumed 6 s mean service time. Before changing the design, measure API acceptance latency, queue age and depth, active worker slots, job completion percentiles, database checkout wait and query time, object bytes retained, retries, cancellation outcomes, and completed reports. An old queue with rising oldest-message age is overload even if the API still accepts requests.

Deploy API, relay, and workers with compatible job schemas so old jobs can finish during a rollout. Retain result objects for seven days, delete expired objects and metadata according to the chosen retention policy, and bound retries/deadlines so a bad report cannot occupy a worker forever. If the queue is unavailable, accepted-but-not-started jobs stay in the outbox and continue consuming the same reserved slots; once all 240 are reserved, reject new submissions before 202. If the database is unavailable, the API cannot durably accept a job and must return an error rather than imply success. Roll out with health checks and a rollback path that accounts for jobs already accepted under the previous schema.

**How would you design a report that may take longer than an HTTP request? / 如何设计一个可能超过 HTTP 请求时限的报表任务？** I would first confirm the report size, response deadline, retention, access owner, and acceptable failure behavior. If measured tail latency fits the request budget, I would keep it synchronous. For the stated multi-second report, I would persist the job and outbox in one database transaction, return a stable status URL, and let a bounded worker create a private result. The worker can be retried, so it uses the job ID for idempotency and records completion before acknowledging delivery. Cancellation remains a request until the authoritative job state confirms its outcome. / 我会先确认报表规模、响应期限、结果留存、数据所有者和可接受的失败行为。如果实测尾部时延满足请求预算，就保持同步。对于本例需要数秒的任务，我会在同一数据库事务中保存 job 与 outbox，返回稳定的状态 URL，再由有界 worker 生成私有结果。worker 可能重试，因此按 job ID 保证幂等，并在确认完成后再确认消息；取消只是请求，直到权威任务状态记录结果才算确定。

**Related notes / 相关笔记：** [HTTP API Contracts / HTTP API契约](../backend/http-api-contracts.md) covers shared endpoint and error-response conventions; [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md) explains request transactions and process-local connection limits; [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md) preserves deadlines, retries, idempotency, backpressure, and acknowledgements; [Web Security and Authentication / Web安全与身份认证](../security/web-security-and-authentication.md) owns principal and resource authorization; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) owns transport and reconnect semantics; [Observability, SLOs, and Incident Response / 可观测性、SLO 与事件响应](../reliability/observability-slos-and-incident-response.md) covers stage-level service indicators and alerting; [Application Deployment and CI/CD / 应用部署与持续集成](../infrastructure/application-deployment-and-ci-cd.md) covers staged rollout and rollback controls.

**Sources / 来源：** [RFC 9110 §15.3.3, 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3); [PostgreSQL 18: Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html) for the database-local all-or-nothing boundary; [PostgreSQL 18: Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) for scoped uniqueness and [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) for concurrent transaction behavior; [AWS Prescriptive Guidance: Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) for dual-write failure and duplicate-publication boundaries; [Amazon S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) as one create-only object-write mechanism, not a requirement to choose S3; [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) for workload requirements, operational focus, and keeping an initial design simple, checked 2026-10-15.
