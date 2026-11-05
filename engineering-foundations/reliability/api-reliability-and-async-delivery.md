# A request timed out: how can I confirm its outcome and retry safely? / 请求超时后，如何确认操作结果并安全重试？

A timeout or disconnected connection means the caller did not receive a result; by itself, it does not show whether the server applied the operation. Give the operation a stable identity, persist that identity with the local effect in one transaction, and let the caller query the authoritative status or repeat the same request with the same key. Carry one end-to-end deadline through the work, bound retries, and treat cancellation as a request for work to stop rather than proof that a remote side effect was undone. / 超时或连接断开只表示调用方没有收到结果，本身不能说明服务端是否已经执行操作。为操作指定稳定标识，在一个事务中持久化该标识和本地效果，并让调用方查询权威状态，或使用相同 key 重试原请求。沿整条调用链传递同一个截止时间并限制重试次数；取消表示请求工作停止，不代表远端副作用已经撤销。

**Key terms / 关键术语：** timeout / 超时；deadline / 截止时间；unknown outcome / 结果未知；idempotency key / 幂等键；retry / 重试；backoff / 退避；jitter / 抖动；cancellation / 取消。

## Where a timeout leaves the caller / 超时后调用方处于什么状态

A **timeout** limits one wait or operation. An end-to-end **deadline** is the latest time the whole request may finish. Starting a new full timeout for each downstream call can let a multi-hop request run far beyond the caller's budget. Pass a deadline or remaining time downstream, reserve time for cleanup and the response, and choose limits from measured latency and the product's failure policy; there is no universal timeout value. Connection setup and response waiting may need separate limits when a client library treats them separately.

When a write is accepted but the response is lost, the caller's **outcome is unknown**. It cannot distinguish “the request never arrived” from “the effect committed and only the response was lost.” A **202 Accepted** response is a different, explicit contract: it says processing was accepted but is not complete. Return a stable operation or job URL so the client can query later; HTTP does not send a later response over the original connection. The endpoint's response and error shapes belong to [HTTP API Contracts / HTTP API契约](../backend/http-api-contracts.md), while method-level semantics belong to [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md).

~~~mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database
    C->>A: Write with operation key
    A->>D: Commit effect and operation result together
    D-->>A: Commit completed
    A--xC: Response is lost
    Note over C: Outcome is unknown
    alt Read-only status lookup
        C->>A: Query the operation
        A->>D: Read recorded outcome
        D-->>A: Recorded result
        A-->>C: Return status and outcome
    else Retry under the same-key contract
        C->>A: Repeat the request with the same key
        A->>D: Match the key and fingerprint
        D-->>A: Recorded result for this write
        A-->>C: Return the recorded outcome
    end
~~~

This diagram follows a committed write whose reply was lost. A read-only status lookup can report that a key is absent and never starts the write. Only a retried write under its explicit idempotency contract can execute when the key is absent. If the effect is in another service, use that service's idempotency contract or a reconciliation path.

## Make a repeated request safe / 让重复请求安全

HTTP defines **idempotent methods** by the intended effect of multiple identical requests. That permits a client to retry an idempotent request after a communication failure, but does not erase other per-request side effects such as audit logging. A timeout alone is not a reason to automatically repeat a non-idempotent operation.

For a write that needs retry support, accept an **idempotency key** or operation ID and define its scope, retention window, and relationship to request parameters. Store a normalized-request fingerprint with the key. The service should return the recorded result for the same key and same request; reuse with different parameters should be rejected or handled by an explicitly documented rule. The deduplication record and the local database effect must share one atomic transaction boundary. A key stored separately from the effect can still permit duplicate work if a crash occurs between the two writes.

**Hypothetical example / 假设示例：** A refund service accepts a request, records the refund, then loses its response before the client deadline. The client cannot tell whether the refund committed. If it retries with the same operation key, the service can return the recorded refund result instead of issuing another refund—provided the key record and refund state were committed together and the service retains that record for the documented retry window. Without those assumptions, the caller must query or reconcile the outcome rather than blindly issue a second refund. This example is illustrative, not a provider contract.

## Bound retries by the remaining deadline / 按剩余截止时间约束重试

Retry only when a failure may be transient and the operation is safe to repeat, or when the client can determine the first attempt was not applied. Use a capped exponential schedule with randomized jitter to spread attempts rather than synchronizing them:

~~~text
cap(n)  = min(max_delay, base_delay × 2^n)
wait(n) = random value from 0 through cap(n)  # one full-jitter variant
~~~

The base delay, cap, attempt limit, and total retry budget are service choices derived from the deadline and downstream capacity, not universal defaults. Stop when the remaining deadline cannot fit another useful attempt. Avoid retries at several layers: if five layers each make three attempts, one logical request can create 3⁵ = 243 downstream attempts. One deliberate retry boundary is easier to bound and observe.

## Treat cancellation as cooperative / 把取消视为协作式信号

Cancellation tells work that its result is no longer needed. Propagate it to downstream calls and check it at safe points so unnecessary computation stops and resources are released. Support depends on each runtime and API; cancellation is often cooperative. It does not prove a remote service stopped or undid a side effect. A client disconnect can trigger a local cancellation signal in some frameworks, but the server must still rely on authoritative operation state to determine whether a write committed.

The account-report example shows the full durable contract: the client receives **202** and a status URL, retries return one job for the same scoped key, and the job record remains authoritative after disconnect. See [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md). For a durable AI run and its checkpoint/reconciliation boundary, see [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md); for how a browser presents disconnect, reconnect, and final states, see [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md).

Observe the request boundary separately: accepted and rejected requests, deadline exhaustion, timeout and cancellation counts, idempotent replays and key conflicts, and final operation or job outcomes. These show whether users received a result, an explicit pending state, an overload response, or an unresolved outcome. Queue depth, oldest-message age, worker slots, redelivery, and acknowledgement signals belong to the corresponding capacity and broker boundaries.

Capacity and queue delivery are separate questions. [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](api-capacity-and-backpressure.md) covers admission, backpressure, and the full synthetic report estimate. [Publisher confirms and consumer acknowledgements / 发布者确认和消费者确认分别证明什么？](queue-delivery-and-acknowledgement.md) explains broker confirmation and redelivery boundaries.

**Related notes / 相关笔记：** [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md) explains how request and transaction lifetimes borrow database connections; [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers the constraints and transaction semantics that make a local deduplication boundary possible.

**Sources / 来源：** [RFC 9110 §9.2.2, Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) and [§15.3.3, 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3), checked 2026-11-05; AWS Builders' Library, [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), checked 2026-10-15; gRPC guides to [Deadlines](https://grpc.io/docs/guides/deadlines/) and [Cancellation](https://grpc.io/docs/guides/cancellation/).
