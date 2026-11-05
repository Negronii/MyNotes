# How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？

Size a pipeline by naming its system boundary, arrival rate, time in each stage, resource held by each unit of work, and maximum waiting work. Little's Law estimates average work in flight in a stable system; it does not promise peak throughput or tail latency. A queue gives work somewhere durable to wait, but only admission control and backpressure keep that wait bounded. / 估算管线时，要明确系统边界、到达速率、各阶段耗时、每个任务占用的资源和最大等待量。Little 定律估算稳定系统中的平均在途工作；它不承诺峰值吞吐量或尾部时延。队列让工作可以持久等待，但只有准入控制和背压才能限制等待规模。

**Key terms / 关键术语：** admission control / 准入控制；backpressure / 背压；in-flight work / 在途工作；queue age / 队列等待时长；Little's Law / Little 定律；connection pool ceiling / 连接池配置上限。

## Bound work before estimating replicas / 先限制工作量，再估算副本数

Bound in-flight requests, worker count, and every waiting queue. An unbounded queue turns overload into growing memory use and delay. When a bound is reached, choose an explicit policy: wait within the request deadline, reject, defer to durable storage, or shed work that can safely be dropped. Include queue wait in the request's latency budget and report overload distinctly from successful completion.

~~~mermaid
flowchart LR
    S[Submission] --> Rate{Rate budget available?}
    Rate -->|no| Reject[Reject without claiming acceptance]
    Rate -->|yes| Slots{Shared waiting slot available?}
    Slots -->|no| Reject
    Slots -->|yes| Reserve[Atomically reserve one job slot]
    Reserve --> Outbox[Outbox or durable queue]
    Outbox --> Start[Worker starts job]
    Start --> Release[Release reservation once]
    Outbox -->|publish retry or broker copy| Outbox
~~~

For a durable job, count the logical job once while it is in the outbox or waiting in the broker. Moving the same job between those systems does not consume a second waiting slot. Release the reservation through a guarded transition when the job starts or becomes terminal before starting. If a retry or lease recovery returns it to waiting, reserve a slot again before requeueing. The account-report case uses this rule and defines the database transitions in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md).

Under steady-state conditions, Little's Law is:

~~~text
average work in flight = arrival rate × average time in system
~~~

The system boundary must include the queue if the arrival rate and elapsed time include queued work. For example, 40 requests/s × 0.2 s in the chosen system implies about 8 average in-flight requests. This is a planning check, not a universal concurrency cap: bursts, latency distributions, retries, and downstream limits still need measurement.

## Synthetic account-report sizing example / 合成账户报表容量估算

**Assumptions / 假设：** Consider a teaching workload with an average of 5 submissions/s and a 10-minute peak of 20/s. Each validated request is 8 KiB, and its submission transaction holds a database connection for 10 ms. A worker makes 12 sequential indexed reads, holding a database connection for 20 ms per read. Mean worker time is 6 s, the average report is 128 KiB, and job metadata is 2 KiB. These are synthetic inputs for arithmetic, not observed traffic, service measurements, an SLO, or a recommended default.

### Estimate worker slots and admission / 估算 worker 槽位与准入

At the average arrival rate, mean worker concurrency is 5 jobs/s × 6 s = 30 jobs. At the stated peak, offered load would require 20 × 6 = 120 concurrent jobs if every request were admitted.

A plan with 4 worker replicas × 2 processes per replica × 8 active job slots per process has 64 slots. If the slots stayed full, the estimate is 64 / 6 = 10.67 jobs/s; at a planning utilization of 70%, it is 64 × 0.70 / 6 = 7.47 jobs/s. A 7 jobs/s token-bucket admission rate uses an estimated 7 × 6 / 64 = 65.6% of slots. These values are starting limits to test, not measured capacity guarantees.

Bound acceptance separately from waiting work. In this example, allow a sustained 7 submissions/s with a burst of 30 and at most 240 accepted-but-not-started jobs across the outbox and broker queue. Reserve one shared slot per job before returning **202 Accepted**; moving a job from outbox to broker does not count it twice. Release the reservation once when work starts or becomes terminal before starting. If all workers stop, the bound fills after a short interruption; once the waiting allowance is full or the rate limit is exhausted, return a documented overload response without claiming the request was accepted.

At 20 offered submissions/s for 600 s, 12,000 requests arrive. A token bucket admitting at most 7 × 600 + 30 = 4,230 in that interval leaves at least 7,770 not admitted, assuming the shared waiting allowance and other limits do not reject sooner. A rejected or ambiguous submission still follows the deadline and idempotency rules in [API timeout and safe retry / API 超时后的结果确认与安全重试](api-reliability-and-async-delivery.md).

### Budget database connections / 预算数据库连接

Budget every process-local pool, including overflow, before increasing replicas:

| Process group | Maximum calculation | Possible connections |
|---|---:|---:|
| API: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Workers: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Other services using the same database | Assumed allocation | 40 |
| Configured application total | 80 + 80 + 40 | 200 |
| Example database connection budget | Assumed total | 240 |
| Unallocated headroom | 240 − 200 | 40 |

This pool ceiling is not a prediction that 200 connections will be busy. Each report uses 12 sequential reads × 0.020 connection-seconds = 0.24 connection-seconds. That implies 5 × 0.24 = 1.2 average checked-out connections for report reads at the average arrival rate, or 20 × 0.24 = 4.8 if the offered peak were admitted; a 10 ms submission transaction adds 0.05 average or 0.2 at that peak. Query fan-out, connection hold time, and real pool behavior must be measured before treating these estimates as resource headroom. The application-level pool ceiling and its per-process scope are explained in [Data Access and Connection Pools / 数据访问与连接池](../backend/data-access-and-connection-pools.md).

### Estimate result bytes and retention / 估算结果体量与留存

At 5 completed reports/s, 128 KiB per report produces 640 KiB/s of results. Seven days of output retention is:

~~~text
128 KiB × 5/s × 604,800 s ÷ 1,048,576 KiB/GiB ≈ 369 GiB
~~~

This is before compression, replication, and cleanup lag. Two KiB of metadata per job adds about 5.8 GiB per seven days before indexes.

At a sustained 7 completions/s, result volume averages 0.875 MiB/s; this is a long-run planning rate, not an instantaneous upper bound. The permitted 30-job burst could produce 3.75 MiB if all reports complete in one interval, and backlog drain can exceed the current admission rate. At a sustained 20 completions/s, the corresponding long-run result volume is 2.5 MiB/s. Measure result downloads separately from generation and retention.

### Test the first bottleneck / 验证最先触顶的资源

Under these assumptions, worker slots bind before the estimated database connection count: peak demand needs 120 active jobs while the plan has 64 slots. That does not prove database CPU, storage I/O, or network has spare capacity.

Load-test the representative 8 KiB input, 12-read fan-out, and output sizes. Ramp average traffic, apply the 20/s burst, then test rate rejection, a full queue, slow reads, retries, and worker loss. Record request acceptance latency separately from job queue wait and completion time. Compare distributions such as p50, p95, and p99 for each user-visible stage; the 6 s mean belongs in the concurrency estimate, not as a p95 promise. Track sustained throughput, queue age, busy slots, database checkout wait and CPU, retained bytes, and completed-job outcomes against the service objective before changing pool size or replicas. [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](observability-slos-and-incident-response.md) explains how to turn these signals into useful service indicators.

**How would you answer “How many workers do we need?” / 如何回答“需要多少个 worker？”** I would state the workload and service-time assumptions, use Little's Law for mean in-flight jobs, and compare that with a bounded worker plan and pool budget. Here the mean suggests 30 active jobs, but peak demand suggests 120; 64 slots and a 7/s admission limit are hypotheses to test under the expected payload and fan-out. I would measure queue age and stage latency distributions before adding replicas, because the first limit could move to the database or storage. / 我会先说明工作负载和处理时长假设，用 Little 定律估算平均在途任务，再与有界 worker 和连接池预算比较。此例平均负载约需 30 个并发任务，但峰值需求约为 120；64 个槽位和每秒准入 7 个是待压测的假设，应按预期 payload 和扇出测量队列等待及各阶段时延分布，再决定是否扩容，因为首个瓶颈也可能转移到数据库或存储。

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](api-reliability-and-async-delivery.md) covers deadline and unknown-outcome policy; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md) applies these bounds to a complete service contract; [Queue delivery acknowledgements / 队列确认与重投](queue-delivery-and-acknowledgement.md) covers broker delivery state; [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) has a different worked latency allocation and model-stage concurrency estimate.

**Sources / 来源：** Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and system boundary; [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15, for latency distributions and percentile-based indicators. The numeric workload and all capacity figures above are synthetic calculations from the stated assumptions.
