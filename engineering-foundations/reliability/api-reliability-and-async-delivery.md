# API Reliability and Asynchronous Delivery / API可靠性与异步交付

**Core model / 核心模型：** Every network or queue boundary can delay, lose, duplicate, or ambiguously report work. Bound how long and how much work is admitted; make retries safe for the operation's semantics; acknowledge only at the intended completion boundary; expose failures so that a timeout or growing queue cannot silently become data loss. / 每个网络或队列边界都可能延迟、丢失、重复或含糊地报告工作。应限制等待时间与准入工作量；重试必须符合操作语义；只在达到预期完成边界后确认；并显式暴露失败，避免超时或不断增长的队列悄然演变成数据丢失。

**Key terms / 关键术语：** timeout / 超时；deadline / 截止时间；cancellation / 取消；unknown outcome / 结果未知；retry / 重试；backoff / 退避；jitter / 抖动；idempotency / 幂等性；backpressure / 背压；admission control / 准入控制；Little’s Law / Little 定律；tail latency / 尾部时延；acknowledgement / 确认；redelivery / 再投递。

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

## Estimating capacity before scaling / 扩容前的容量估算

**Core explanation / 核心解释：** Estimate the arrival rate, work per request, resource time, and retained data; then identify the first bounded resource and test that hypothesis. Little’s Law estimates mean work in flight for a stable system boundary. It does not turn average traffic into a peak, mean latency into a tail-latency promise, or concurrency into a replica count. / 先估算到达速率、单次工作量、资源占用时间和留存数据，再找出最先触顶的有界资源并验证这一假设。Little 定律估算稳定系统边界内的平均在途工作量；它不能把平均流量变成峰值、把平均时延变成尾部时延承诺，也不能直接推出副本数量。

**Hypothetical sizing example / 假设估算示例：** Consider an account-report job. Assume an average of 5 submissions per second and a 10-minute peak of 20 per second. Each validated request is 8 KiB; its submission transaction holds a database connection for 10 ms. The worker makes 12 sequential indexed reads holding a database connection for 20 ms each; mean worker time is 6 s, the report is 128 KiB, and job metadata is 2 KiB. These are teaching inputs, not observed traffic, service measurements, an SLO, or a recommended default.

At the average arrival rate, mean worker concurrency is 5 jobs/s × 6 s = 30 jobs. At the stated peak, the offered load would require 20 × 6 = 120 concurrent jobs if every request were admitted. A plan with 4 worker replicas × 2 processes per replica × 8 active job slots per process has 64 slots. Even if those slots were continuously full, the estimate is 64 / 6 = 10.67 jobs/s; at a planning utilization of 70%, it is 64 × 0.70 / 6 = 7.47 jobs/s. A 7 jobs/s token-bucket admission rate uses an estimated 7 × 6 / 64 = 65.6% of slots. This is a starting limit to test, not a measured capacity guarantee.

Bound acceptance separately from waiting work. For this example, allow a sustained 7 submissions/s with a burst of 30 and at most 240 accepted-but-not-started jobs across the outbox and broker queue. Reserve one shared slot per job before returning 202; moving the job from outbox to broker does not count it twice. Release the reservation once when work starts or becomes terminal before starting; the linked design case covers the atomic state transition. If all workers stop, the bound fills after a short interruption; once the shared waiting allowance is full or the rate limit is exhausted, return a documented overload response without claiming the request was accepted. At 20 offered submissions/s for 600 s, 12,000 requests arrive; the token bucket admits at most 7 × 600 + 30 = 4,230, so at least 7,770 are not admitted, assuming the shared waiting allowance and other limits do not reject sooner. Retrying a rejected or ambiguous submission still follows the deadline and idempotency rules above.

Budget every process-local pool, including overflow, before increasing replicas:

| Process group | Maximum calculation | Possible connections |
|---|---:|---:|
| API: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Workers: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Other services using the same database | Assumed allocation | 40 |
| Configured application total | 80 + 80 + 40 | 200 |
| Example database connection budget | Assumed total | 240 |
| Unallocated headroom | 240 − 200 | 40 |

This pool ceiling is not a prediction that 200 connections will be busy. Each report uses 12 sequential reads × 0.020 connection-seconds = 0.24 connection-seconds. That implies 5 × 0.24 = 1.2 average checked-out connections for report reads at the average arrival rate, or 20 × 0.24 = 4.8 if the offered peak were admitted; a 10 ms submission transaction adds 0.05 average or 0.2 at that peak. Query fan-out, connection hold time, and real pool behavior must be measured before treating these estimates as resource headroom.

At 5 completed reports/s, 128 KiB per report produces 640 KiB/s of results. Seven days of output retention is 128 KiB × 5/s × 604,800 s ÷ 1,048,576 KiB/GiB ≈ 369 GiB, before compression, replication, and cleanup lag. Two KiB of metadata per job adds about 5.8 GiB per seven days before indexes. At a sustained 7 completions/s, result volume averages 0.875 MiB/s; this is a long-run planning rate, not an instantaneous upper bound. The permitted 30-job burst could produce 3.75 MiB if all reports complete in one interval, and backlog drain can exceed the current admission rate. At a sustained 20 completions/s, the corresponding long-run result volume is 2.5 MiB/s. Measure result downloads separately from generation and retention. / 稳定每秒完成 7 个任务时，结果体量长期平均为 0.875 MiB/s；这不是瞬时上限。允许的 30 个突发任务若在同一时段完成，可产生 3.75 MiB；排空积压时的完成速率也可能高于当前准入速率。若持续每秒完成 20 个任务，对应长期平均结果体量为 2.5 MiB/s。结果下载应与生成和留存分别测量。

Under these assumptions, worker slots bind before the estimated database connection count: peak demand needs 120 active jobs while the plan has 64 slots. That does not prove database CPU, storage I/O, or network have spare capacity. Load-test the representative 8 KiB input, 12-read fan-out, and output sizes; ramp average traffic, apply the 20/s burst, then test rate rejection, a full queue, slow reads, retries, and worker loss. Record request acceptance latency separately from job queue wait and completion time; use distributions such as p50, p95, and p99 for each user-visible stage. The 6 s mean belongs in the concurrency estimate, not as a p95 promise. Compare sustained throughput, queue age, busy slots, database checkout wait/CPU, retained bytes, and completed-job outcomes with the service objective before changing pool size or replicas.

**How would you answer “How many workers do we need?” / 如何回答“需要多少个 worker？”** I would state the workload and service-time assumptions, use Little’s Law for mean in-flight jobs, and compare that with a bounded worker plan and pool budget. Here the mean suggests 30 active jobs, but peak demand suggests 120; 64 slots and a 7/s admission limit are hypotheses to test under the expected payload and fan-out. I would measure queue age and stage latency distributions before adding replicas, because the first limit could move to the database or storage. / 我会先说明工作负载和处理时长假设，用 Little 定律估算平均在途任务，再与有界 worker 和连接池预算比较。此例平均负载约需 30 个并发任务，但峰值需求约为 120；64 个槽位和每秒准入 7 个是待压测的假设，应按预期 payload 和扇出测量队列等待及各阶段时延分布，再决定是否扩容，因为首个瓶颈也可能转移到数据库或存储。

For a different worked latency allocation and model-stage concurrency estimate, see [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md). The same hypothetical account-report service is traced end to end in [System Design Fundamentals / 系统设计基础](../architecture/system-design-fundamentals.md).

## Queue acknowledgements, duplicates, and order / 队列确认、重复与顺序

Publishing and consuming have separate failure boundaries. A publisher confirm covers publisher-to-broker acceptance under that broker's rules; it does not say that a consumer applied the business change. A consumer acknowledgement should follow the work that the system defines as complete. If the consumer commits a change and crashes before acknowledging, a broker may redeliver the message; make processing idempotent or deduplicate by a stable message or operation key. If it acknowledges before durable work, a crash can lose the work.

Delivery and ordering semantics belong to a particular broker, queue type, acknowledgement mode, and consumer arrangement. For example, with manual acknowledgements RabbitMQ requeues unacknowledged deliveries when the channel or connection closes; consumers therefore need to handle redeliveries. Concurrent consumers can finish work in a different order from delivery, so use a per-key sequence or serialized consumer when completion order is a correctness rule. A dead-letter queue makes a failed message visible only if it is monitored and someone has defined whether to repair, retry, or discard it.

Observe each boundary separately: accepted and rejected requests, timeout and cancellation counts, in-flight work, queue depth and oldest-message age, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A queue that keeps accepting messages while its oldest item grows is accumulating delay, not demonstrating health.

**Related notes / 相关笔记：** [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers the transaction boundary used to persist business effects and idempotency records, plus the limited CAP and 2PC context; [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md) explains process-local pool limits; [Node.js Fundamentals / Node.js基础](../backend/node-js-fundamentals.md) applies concurrency and shutdown limits to a Node service; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../networking/http-protocols-and-websockets.md) covers the transport and request semantics.

**Sources / 来源：** [RFC 9110, HTTP Semantics §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2); [AWS Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), checked 2026-10-15; [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15, for latency histograms and percentile-based SLIs; gRPC [Deadlines](https://grpc.io/docs/guides/deadlines/) and [Cancellation](https://grpc.io/docs/guides/cancellation/) guides; RabbitMQ 4.3 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms), checked 2026-10-15, for its manual-ack requeue and publisher-confirm boundaries; Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and the queue-plus-service system boundary.
