# API Reliability and Asynchronous Delivery / API可靠性与异步交付

**Core model / 核心模型：** Every network or queue boundary can delay, lose, duplicate, or ambiguously report work. Bound how long and how much work is admitted; make retries safe for the operation's semantics; acknowledge only at the intended completion boundary; expose failures so that a timeout or growing queue cannot silently become data loss. / 每个网络或队列边界都可能延迟、丢失、重复或含糊地报告工作。应限制等待时间与准入工作量；重试必须符合操作语义；只在达到预期完成边界后确认；并显式暴露失败，避免超时或不断增长的队列悄然演变成数据丢失。

**Key terms / 关键术语：** timeout / 超时；deadline / 截止时间；cancellation / 取消；unknown outcome / 结果未知；retry / 重试；backoff / 退避；jitter / 抖动；idempotency / 幂等性；backpressure / 背压；acknowledgement / 确认；redelivery / 再投递。

## Timeouts, deadlines, and cancellation / 超时、截止时间与取消

A **timeout** limits one wait or operation. A **deadline** is the latest acceptable completion time for the whole request. If each downstream call starts a fresh full timeout, a multi-hop request can run far beyond the caller's budget. Carry a deadline or remaining time downstream, reserve time for cleanup and the response, and derive limits from measured latency and the product's failure policy; there is no universal timeout value. Connection setup and response waiting may need separate limits if the client library treats them separately.

Cancellation tells work that its result is no longer needed. Propagate it to downstream calls and check it at safe points so unnecessary computation stops and resources are released. Support depends on each runtime and API; cancellation is often cooperative. It does not prove that a remote service stopped or undid a side effect. If a caller's deadline expires after a write was accepted, the caller may know only that the **outcome is unknown**.

## Retries, backoff, and idempotency / 重试、退避与幂等

Retry only when the failure may be transient and the operation is safe to repeat, or when the client can determine that the first attempt was not applied. A timeout or lost response alone cannot establish that no effect occurred. HTTP's idempotent-method definition concerns the intended effect of repeated requests; it does not make every application side effect disappear, and a non-idempotent method should not be retried automatically without application-specific evidence.

A capped exponential schedule with randomized jitter spreads retries rather than making clients retry together:

~~~text
cap(n)  = min(max_delay, base_delay × 2^n)
wait(n) = random value from 0 through cap(n)  # one full-jitter variant
~~~

The base delay, cap, attempt limit, and total retry budget are service choices derived from the deadline and downstream capacity, not universal defaults. Stop when the remaining deadline cannot accommodate another useful attempt. Avoid retries at several layers: if five layers each make three attempts, one logical request can produce `3^5 = 243` downstream attempts. Retrying at one deliberate boundary is often easier to bound and observe.

For a write that can be retried, an **idempotency key** or operation identifier lets the service recognize a repeated logical request. The service should define the key's scope and retention, associate it with the request parameters, and persist the operation result so the same key and same request can return the existing outcome; reuse with different parameters should be rejected or otherwise explicitly defined. The deduplication record and local database effect need one atomic boundary. If the side effect is in another service, that service must provide compatible idempotency or the caller needs a reconciliation path; a local key cannot make an unrelated remote effect atomic.

**Hypothetical example / 假设示例：** A refund service accepts a request, records the refund, and loses its response before the client deadline. The client cannot distinguish “refund committed” from “request never arrived.” If the client retries with the same operation key, the service can return the recorded refund result instead of issuing another refund—provided the key record and refund state were committed together and the service retains that record for the documented retry window. Without those assumptions, the caller must query or reconcile the outcome rather than blindly issue a second refund. The numbers and service behavior here are illustrative, not a provider contract.

## Concurrency limits and backpressure / 并发限制与背压

Bound in-flight requests, worker count, and any waiting queue. A queue that can grow without limit converts overload into growing memory use and delay. When a bound is reached, choose an explicit policy—wait within the deadline, reject, defer to durable storage, or shed work that can safely be dropped. Keep queue time inside the request's latency budget and report overload distinctly from successful completion.

Under steady-state conditions, Little's Law, `average in-flight requests = arrival rate × average time in system`, gives a planning check rather than a capacity guarantee. For example, a hypothetical average arrival rate of 40 requests/second and 0.2 seconds of average time in the chosen system—including its queue and service—implies about `40 × 0.2 = 8` average in-flight requests. Bursts, latency distribution, retries, and downstream limits still require measurement; eight is not a universal concurrency cap.

## Queue acknowledgements, duplicates, and order / 队列确认、重复与顺序

Publishing and consuming have separate failure boundaries. A publisher confirm covers publisher-to-broker acceptance under that broker's rules; it does not say that a consumer applied the business change. A consumer acknowledgement should follow the work that the system defines as complete. If the consumer commits a change and crashes before acknowledging, a broker may redeliver the message; make processing idempotent or deduplicate by a stable message or operation key. If it acknowledges before durable work, a crash can lose the work.

Delivery and ordering semantics belong to a particular broker, queue type, acknowledgement mode, and consumer arrangement. For example, with manual acknowledgements RabbitMQ requeues unacknowledged deliveries when the channel or connection closes; consumers therefore need to handle redeliveries. Concurrent consumers can finish work in a different order from delivery, so use a per-key sequence or serialized consumer when completion order is a correctness rule. A dead-letter queue makes a failed message visible only if it is monitored and someone has defined whether to repair, retry, or discard it.

Observe each boundary separately: accepted and rejected requests, timeout and cancellation counts, in-flight work, queue depth and oldest-message age, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A queue that keeps accepting messages while its oldest item grows is accumulating delay, not demonstrating health.

**Related notes / 相关笔记：** [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers the transaction boundary used to persist business effects and idempotency records, plus the limited CAP and 2PC context; [Node.js Fundamentals / Node.js基础](../backend/node-js-fundamentals.md) applies concurrency and shutdown limits to a Node service; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) covers the transport and request semantics.

**Sources / 来源：** [RFC 9110, HTTP Semantics §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2); [AWS Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), checked 2026-10-15; gRPC [Deadlines](https://grpc.io/docs/guides/deadlines/) and [Cancellation](https://grpc.io/docs/guides/cancellation/) guides; RabbitMQ 4.3 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms), checked 2026-10-15, for its manual-ack requeue and publisher-confirm boundaries; Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and the queue-plus-service system boundary.
