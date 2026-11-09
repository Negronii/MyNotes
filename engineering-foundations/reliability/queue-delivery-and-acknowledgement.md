# 报表任务的发布确认、消费者确认与业务完成各证明什么？

账户 acct-17 为 report 42 发起导出时，请求幂等键为 report-demo-208，并在 application programming interface（应用程序接口，API）的数据库事务里创建 job（任务）job-demo-731 和 outbox（事务发件箱）行，同时预留一个等待槽。这里的等待槽是数据库维护的排队准入额度，不是 RabbitMQ prefetch 或 BullMQ lock：每个尚未领取的逻辑排队轮次占一个槽，接管重排时重新预留，领取时归还，重复 delivery 不增槽。report 42 也可由只读 API 路径查询；读状态码与异步 job 的状态或结果对象提交是不同的用户结果，不能互相代替。relay（转发进程）再把工作意图发布到 broker（消息代理）。publisher confirm（发布者确认）覆盖 relay 到 broker 的接收边界；consumer acknowledgement（消费者确认，常写作 ACK）覆盖 broker 到 worker（工作进程）的交付处理边界；job 的 succeeded 状态和私有对象引用才是应用对用户作出的业务完成记录。

~~~mermaid
sequenceDiagram
    participant A as API / database
    participant R as Outbox relay
    participant B as RabbitMQ broker
    participant W as Report worker
    participant O as Private object storage
    A->>A: 同事务写 job + pending outbox + 预留一个数据库排队额度
    R->>B: mandatory 发布载荷 {job_id=job-demo-731}
    alt 消息不可路由
        B-->>R: basic.return（关联本次发布）
        B-->>R: publisher confirm ack
        R->>A: intent 保持 pending，修复路由后再试
    else 到达已验证的目标拓扑
        B-->>R: 无关联 return + publisher confirm ack
        R->>A: 仅标记对应 intent 为 published
        B->>W: 投递 job ID
        W->>A: 只对 queued 条件领取；attempt + 1；释放等待槽
        W->>O: 上传 attempt 隔离的临时对象
        W->>A: 条件提交 succeeded + object key
        A-->>W: 事务提交
        W->>B: consumer ACK
    end
    Note over R,B: confirm 丢失时 relay 可能重发；confirm ack 本身不表示已路由
    Note over W,B: commit 后 ACK 丢失时消息可能重投
    Note over R,W: 实际 delivery 可能早于 outbox 的 published 回写；published 不是 worker 条件领取的前置状态
~~~

图中的两条回路是分布式系统的正常不确定区间：网络故障可能让一方已完成操作、另一方却没收到确认。持久 outbox 避免应用数据库提交与 broker publish（发布）的双写空档；幂等业务更新负责接住重复消息。没有共享的分布式事务时，不应把这称作 exactly-once（恰好一次）。

## 发布者确认只回答 broker 是否接收

publisher confirm 覆盖 publisher（发布者）到 RabbitMQ 的通信。它不知道 worker 是否已收到、确认或完成消息。如果 broker 接收了 publish，但 confirm 在网络中丢失，relay 无法区分“broker 未收到”和“broker 已收到但回复丢失”，重发便可能为同一 job 产生重复载荷。outbox 每次调度意图有独立唯一 ID，relay 用这个 ID 更新相应的发布状态；消息载荷只需 job ID。

confirm 的含义还受消息和 queue（队列）类型影响。RabbitMQ exchange（交换器）通过 binding（绑定）把 publish 路由到 queue（队列）；publisher confirm 不是路由保证，消息被 exchange 接受并不一定已进入预期 queue。mandatory 发布要求不可路由消息以该次 publish 的 basic.return 返回，应将它与 publisher confirm ack 联合判断：4.4 中不可路由消息会先 basic.return、再收到 confirm ack，因此“有 confirm ack 且没有关联 return”才能说明至少路由到了某个 queue。它仍不证明该 queue 是业务目标；exchange、binding 和备用 exchange 必须按明确拓扑预先验证。若 routing contract 由其他 broker/机制保证，则按该契约检查路由结果。durable message/queue（持久消息/队列）与副本类型也决定 broker 按什么配置确认承担责任；不要把另一种 queue 的保证套用过来。

outbox relay 可以按此顺序推进：读取一条未发布 outbox 意图，发布它所指向的 job ID；只有所选路由契约通过（例如 mandatory publish 已收到 confirm ack，且没有关联的 basic.return）后，才标记这个 intent 自己的 outbox 行已发布。confirm 状态未知或出现 return 时保留意图并报告发布/路由故障，修复后重试；重复 publish 可能得到相同逻辑 job 的消息，RabbitMQ 不在这里替应用去重。数据库事务和 RabbitMQ 事务不是一个原子事务；重复消息可接受的前提是 consumer（消费者）按持久 job 状态幂等处理。账户报表如何把 job、outbox 和等待槽同事务提交见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 消费者在业务结果持久后才 ACK

给 job-demo-731 的 delivery（消息投递）载荷只带稳定 job ID，不带 attempt。worker 只对数据库中的 `queued` 状态且 `available_at` 已到的任务做 conditional claim（条件领取）：在同一数据库事务中把状态改为 `running`、生成新的 attempt（尝试号）并释放等待槽。若当前 job 行还没有此字段，支持延迟重试时就在该行持久增加 `available_at`；初次排队的时间可立即到期，重试则以数据库时间判断。重投消息只是查询权威 job 的线索，不能自己生成 attempt。

先区分领取时遇到的重复 delivery：

- `queued` 且 `available_at <= clock_timestamp()` 表示排队轮次已到可领取时间，worker 可竞争条件领取；只有一个事务能领取成功。若 `available_at` 仍在未来，旧轮次早到的重复 delivery 不能提前启动 attempt；只有在后续 outbox/定时发布已持久安排到期唤醒时才可 ACK，否则应延后或不 ACK。
- `running` 且租约未过期表示已有当前 attempt，重复 delivery 不能另起并行工作。因为本例有持久租约恢复器，数据库能在过期后条件接管、重新预留槽并写新 outbox；因此确认该恢复路径持续运行后，可 ACK 这条重复消息。若没有独立且持久的恢复路径，就延后或不 ACK，不能单凭 `running` 丢掉唯一唤醒消息。
- 已持久终结的 `succeeded`、`failed` 或 `cancelled` job 不再需要这条 delivery，可 ACK。
- `running` 已过期也不表示当前 worker 可以自助领取新代次。租期到期只让数据库恢复器有资格尝试接管；它必须先赢得条件更新，再把任务改回 `queued`、预留新槽并写入新的 outbox intent。随后消息唤醒的 worker 才能领取新 attempt。

attempt 来自数据库的胜者更新，不能信任可能重复、延迟或过期的 queue message（队列消息）。结果对象写入后，只有当前 attempt 的条件更新提交 `succeeded` 和对象 key，才向 broker 发 consumer ACK。用户读取结果仍要经 API 做授权，不能因 message 已被 ACK 就把对象公开。

成功条件必须把当前状态、attempt 和取消请求一起放进更新谓词，且对象已经写好后才提交：

~~~sql
UPDATE report_jobs
SET status = 'succeeded', result_object_key = :object_key
WHERE job_id = :job_id
  AND status = 'running'
  AND attempt = :attempt
  AND cancel_requested = FALSE;
~~~

若更新一行，先提交事务，再 ACK。**完成 UPDATE 返回零行是另一条分支，不能与“领取时收到重复 delivery”混为一谈。** worker 重新读取权威 job/outbox：若已是 `succeeded`、`failed` 或取消终态且清理策略已持久，当前 delivery 已无待办工作，可 ACK。若恢复器已把旧 attempt 持久转为 `queued`，且槽位与新 outbox 意图同事务提交，旧 delivery 可 ACK；relay 只会在其 `available_at` 到期后发布，早到消息也不能越过领取时间条件。若后继 worker 已把状态领取为更大的 `running` attempt，则只有在该 claim 已提交且租约恢复路径独立持久时才 ACK 旧 delivery。恢复器的接管尚未提交、或仍为 `queued` 但新 outbox/槽位尚未持久时，不能 ACK；若当前 attempt 仍在运行且恢复器不能保证后续重排，也不能 ACK。只有 `cancel_requested` 尚未写成持久取消终态时，不能把旧 worker 的失败返回或已上传对象当作成功；应完成取消状态和清理/保留策略，或交给有持久保证的恢复流程，再按 broker 契约 ACK。

| 失败时点 | broker 可能采取的动作 | 应用要保持的条件 |
|---|---|---|
| broker 已接收 publish，confirm 未到 relay | relay 重发，同一 job ID 可能有多条消息 | 对当前持久 job/attempt 的完成更新只能有一个赢家 |
| worker 在持久结果前崩溃，delivery 尚未 ACK | RabbitMQ 连接或 channel 关闭后可重新排队未 ACK delivery | 重投仅触发读取权威 job；有效租约内不能另起 attempt，过期后仍须等恢复器条件接管并持久重排 |
| 数据库已提交 succeeded，worker 发 ACK 前崩溃 | delivery 可再次到达另一个 worker | 后继 worker 查到 job 已终态/attempt 已失效，不得重复业务副作用，再 ACK 重复消息 |
| worker 先 ACK，再提交结果前崩溃 | broker 可删除这条 delivery，不会再因它自动重投 | 若没有独立的持久恢复扫描，job 可能滞留；canonical 报表设计由数据库租约恢复器条件接管并通过新 outbox 重排，因此该恢复依赖数据库而非 broker |

若成功提交了对象但数据库事务未能提交，可能留下不可见的孤儿对象；以 attempt key 命名并在无引用、任务终态和宽限期满足后清理。若数据库已提交成功但 ACK 丢失，重复 handler 应通过终态 job、attempt fencing（尝试栅栏校验）或 operation key 得到“已完成/重复”而不是再次发布或覆盖结果。数据库提交、ACK 与恢复器抢占的状态谓词由 report job 设计章负责，本篇只解释 broker 交界。

## 重试、并发窗口与顺序会改变负载

RabbitMQ 4.4 使用手动确认时，未确认 delivery 在其 channel（通道）或 connection（连接）关闭后可自动 requeue（重新排队）；这是 RabbitMQ 的行为，不能无条件推广到所有 broker。automatic acknowledgement（自动确认）模式在发送后就视为已交付，可提高吞吐，但应用还没处理就断线时会失去工作。对需要可靠完成的报表任务，选择手动 ACK 并把 ACK 放在业务持久化之后；若依赖数据库租约扫描恢复被提前确认的任务，要把恢复器视为独立的正确性机制。

RabbitMQ 4.4 的 consumer prefetch（消费者预取上限）默认按单个 consumer（消费者）计算，而不是整个 channel（通道）：例如一个 consumer 设 prefetch=4，就最多有四条它自己的 delivery 未 ACK；同一个 channel 上若有三个 consumer，总数可以达到 12。RabbitMQ 4.3 起全局 per-channel QoS 已弃用且默认禁用。prefetch 同时影响 worker 的并行量、进程内排队和内存，不应设置为无限而不评估容量。

失败重试要有边界。worker 遇到可重试的瞬时错误时，不能只把原 delivery 延迟重投，因为 job 若仍为 `running`，条件领取不会启动下一 attempt；应用须以当前 attempt 为条件，同事务持久设置 `status=queued`、`available_at=next_retry_at`、重新预留等待槽并写新的 pending outbox 意图。relay 只在 `available_at` 到期后发布；领取谓词也要求数据库当前时间已到，早到的旧 delivery 只检查状态，不能绕过退避。只有新 outbox 与重试时间都已持久后，原 delivery 才可 ACK。不可重试错误或尝试耗尽时先持久写 `failed` 终态，再 ACK。无法映射到有效 job 的格式错误消息进入可观测 dead-letter queue（死信队列，DLQ），不要无限重排。若业务要求每个账户按顺序更新，必须明确顺序的键范围，并用单一有序分区、序号条件更新或串行化保证；first in, first out（先进先出，FIFO）名称不自动保证多个 worker 的业务完成顺序。

## BullMQ 的租锁失效为什么会让任务重复执行？

另一种常见实现是 BullMQ 6.5.3：Redis 保存 BullMQ 的调度状态和 job lock；在本例中，PostgreSQL 的 canonical 报表行仍是业务状态、attempt、租期与结果引用的权威来源，BullMQ 只负责唤醒和调度。每个持久 outbox 发布意图有自己的稳定 ID，relay 用安全字符集的 UUID 意图 ID 生成 `outbox-${intentId}`，作为 BullMQ custom job ID；消息载荷仍只带 canonical job ID `job-demo-731`。同一意图重发时复用调度 ID；租约恢复写入新 outbox 意图时使用新调度 ID，避免保留中的旧 BullMQ job 阻挡合法唤醒。BullMQ 6.5.3 custom job ID 不能含冒号、也不能只由数字组成；外部业务 operation key（如 `report-demo-208:notify:v1`）不是 BullMQ job ID。job 保留期间重复添加相同调度 ID 会被忽略；移除后可再次添加，所以它仍不代替 canonical 数据库和请求幂等记录。

BullMQ worker（工作进程）领取 job 后，队列会为它持有有时限的 lock（锁），并周期续租。进程异常退出、Redis 连接中断，或 Node.js 事件循环被长时间 CPU 工作阻塞，都可能令续租错过 lockDuration；stalled checker（停滞任务检查器）发现锁已过期后，会把 job 放回 waiting 让 worker 重跑。BullMQ 文档把这类语义称为 at-least-once（至少一次），即同一 job 可能被处理超过一次。Stalled 次数上限由 maxStalledCount 控制，6.5.3 文档默认值为 1；普通处理器抛错的 attempts/backoff 与 stalled 次数上限是两条重试路径。要观察 stalled 事件并让 CPU 密集型任务及时让出事件循环。增加锁时长会延长真正崩溃后的发现时间，缩短锁又会放大调度抖动导致的重投，不能把时间配置当成业务幂等。

即使 worker 丢失 Redis 锁，它已经开始的远端请求或对象写入也不一定会停止；稍后另一个 worker 可能拿到同一 job。Redis lock 只决定 BullMQ 何时重投，不授予或撤销报表业务写权限；对同一个 job-demo-731，外部意图和结果提交仍按 canonical 数据库状态检查 `status=running`、当前 attempt、`cancel_requested=false`。该合同中租约到期只允许恢复器尝试接管，接管状态变更提交前旧 attempt 仍可能赢得条件更新；它不同于下文独立 PostgreSQL 示例的严格到期拒绝写入。触发外部效果前使用稳定业务操作键，例如请求键 report-demo-208 对应的 `report-demo-208:notify:v1`；本地 outbox 绑定 job、attempt、请求摘要和上述 canonical 状态栅栏。远端应按稳定操作键与相同请求摘要去重，并公开保留期限或按键查询：查询确认效果完成时记录完成、不再发送；结果仍未知（包括查询不可用），但远端保证该键同摘要在期限内去重时，才用同键同摘要重试；结果仍未知且没有仍有效的去重保证，或摘要不一致、期限已过时，保留未知并人工对账。写对象时则用包含 attempt 的不可变路径，只让当前有效 attempt 的数据库事务提交对象引用。一般未知结果边界见[请求超时后如何确认结果并安全重试？](api-reliability-and-async-delivery.md)。

## SQL job 表怎样短时领取并阻止过期 worker 回写？

如果任务状态本来就在 PostgreSQL，worker 也可以直接轮询 job 表。PostgreSQL 的 FOR UPDATE SKIP LOCKED（跳过已锁行）会跳过当前被其他事务锁住的行；官方将它列作适合多个消费者竞争 queue-like（类似队列的）表的机制，不适合作为一般读取的一致视图。领取事务只负责选一行、写 running 状态、递增 attempt 代次并设 lease_until，然后立即提交。worker 在事务外执行昂贵任务；心跳只延长仍属于自己的未过期租约。

下面是可在 PostgreSQL 14+ 的 psql 会话运行的独立 SQL 合成任务演示，使用 `pg-job-demo-42`，不复用上面 RabbitMQ/报表示例的 `job-demo-731`。本例明确选择严格租期合同：到期本身就终止旧 attempt 的写权限，即使接管尚未发生；这与前述 canonical 报表合同“到期仅允许恢复器尝试接管、由状态变更提交栅栏旧 attempt”是两种不同取舍，产品实现应选定一种并贯穿使用。临时表只在当前连接中存在，退出 psql 会话后才消失。领取语句作为各自的短事务提交。写外部意图、完成和续租时，都先按稳定 job ID 锁定行，再由下一条语句使用新鲜 `clock_timestamp()` 检查状态、attempt 与未过期租约；不能让一个带时间谓词的 `SELECT FOR UPDATE` 等锁后沿用锁前判定：

> [!example]- PostgreSQL 领取、租约栅栏与外部意图
> ~~~sql
> CREATE TEMP TABLE report_jobs (
>   job_id text PRIMARY KEY,
>   status text NOT NULL,
>   attempt integer NOT NULL DEFAULT 0,
>   available_at timestamptz NOT NULL,
>   lease_until timestamptz,
>   result_key text
> );
> INSERT INTO report_jobs(job_id, status, attempt, available_at)
> VALUES ('pg-job-demo-42', 'queued', 0, clock_timestamp() - interval '1 second');
>
> CREATE TEMP TABLE job_effect_outbox (
>   operation_key text PRIMARY KEY,
>   job_id text NOT NULL REFERENCES report_jobs(job_id),
>   attempt integer NOT NULL,
>   request_sha256 text NOT NULL,
>   payload text NOT NULL
> );
>
> -- Worker A：领取提交后才在事务外计算。返回 attempt=1。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE (status = 'queued' AND available_at <= clock_timestamp())
>      OR (status = 'running' AND lease_until <= clock_timestamp())
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_until = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
> RETURNING j.job_id, j.status, j.attempt, j.lease_until;
>
> -- 为了不等待 30 秒，演示中把 Worker A 的租期置为已过期。
> UPDATE report_jobs
> SET lease_until = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 1;
>
> -- Worker A 已过期但 Worker B 尚未接手：严格租期检查返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- Worker B 接手过期任务。返回 attempt=2，旧代次不再拥有提交权。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE (status = 'queued' AND available_at <= clock_timestamp())
>      OR (status = 'running' AND lease_until <= clock_timestamp())
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_until = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
> RETURNING j.job_id, j.status, j.attempt, j.lease_until;
>
> -- 本例的外部操作键固定属于 pg-job-demo-42。请求摘要是该 JSON 正文原始字节的 SHA-256。
> -- Worker A 已过期；attempt 检查失败，插入 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH current_attempt AS (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 1
>     AND lease_until > clock_timestamp()
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:notify:v1', job_id, attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM current_attempt
> ON CONFLICT (operation_key) DO NOTHING
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- Worker B 的当前 attempt 持有未过期租约，意图只插入一次，返回 1 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH current_attempt AS (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 2
>     AND lease_until > clock_timestamp()
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:notify:v1', job_id, attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM current_attempt
> ON CONFLICT (operation_key) DO NOTHING
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- 同键重放必须核对正文摘要；只有 true 才是相同请求。
> SELECT operation_key,
>        request_sha256 = 'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c' AS same_request
> FROM job_effect_outbox
> WHERE operation_key = 'pg-job-demo-42:notify:v1';
>
> -- Worker A 迟到完成：先锁行，再重新读租期/代次；attempt 不匹配，返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- Worker B 完成：先锁行，再由下一条 UPDATE 检查新鲜租期；返回 1 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-2', lease_until = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 2
>   AND lease_until > clock_timestamp()
> RETURNING job_id, status, attempt, result_key;
> COMMIT;
> ~~~

回放结果为：首次领取 attempt=1；A 到期但 B 尚未接手时，严格租期完成更新返回 0 行；之后过期接手为 attempt=2，A 的过期意图写入与迟到完成仍各返回 0 行，B 的当前意图写入和完成各返回 1 行，摘要查询为 true。前文 canonical 报表合同则允许到期至接管提交前由旧 attempt 与恢复器竞争状态写入；两者彼此独立。若租约续期写成另一个 UPDATE，也必须同时要求 job ID、running 状态、当前 attempt 匹配且旧 lease_until 尚未过期；否则已过期 worker 能在接手后再次“续活”。远端副作用仍按三种结果处理：查询确认完成则记录完成并停止发送；结果仍未知（查询不可用也算未知）但远端保证同键同摘要在保留窗内去重，才可重试原键；结果仍未知且无有效保证、摘要冲突或期限过了，就人工对账。SQL 领取避免维护独立 Redis job 状态，但会以轮询和行锁增加主数据库负担，需监控领取扫描、锁等待和空轮询。

代次栅栏只能阻止旧 worker 覆盖 job 行，不会撤回它已经发出的外部请求。worker 写本地外部意图时，必须在同一短事务锁住 job 行、校验 `status=running`、当前 attempt 和未过期租约，再写入唯一 operation_key 与请求摘要；冲突时读取既有行，摘要相同才可视为同一意图，摘要不同则隔离处理。relay 仍可能在远端成功后、写下本地发送回执前崩溃。结果未知时先按原操作键查询：查询确认效果已完成，就持久记完成并停止发送；结果仍未知但远端保证相同键、相同摘要在保留窗内去重，才可同键重试；结果仍未知且没有仍有效的同键同摘要去重保证、摘要不符或远端保留窗已过，就维持未知并人工对账。数据库内唯一键只防止重复创建本地意图，不会自动让远端调用只发生一次。

## 观测每个交接点，不能只数 ACK

单独记录 publish 尝试、confirm/return、queue depth 和 oldest-message age、unacked 数、重投、重试、ACK、DLQ、job succeeded/failed 及对象引用提交。oldest-message age 持续增长表示结果延迟，即使队列还在接受消息。broker 继续接收并不代表 worker 有容量；worker 发 ACK 也只表示应用确认到达选择的处理边界，不等于用户后来成功下载了报告。更完整的事故定位见[如何从报表服务信号定位发布故障？](observability-slos-and-incident-response.md)。

> [!info]- 来源
> - RabbitMQ 官方 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) 与[发布何时确认](https://www.rabbitmq.com/docs/confirms#when-will-published-messages-be-confirmed-by-the-broker)、[Reliability Guide](https://www.rabbitmq.com/docs/reliability)，checked 2026-11-06：确认方向相互独立、mandatory/unroutable 的 `basic.return` 在 confirm ack 前、手动/自动 ack、未确认消息在 channel/connection 关闭后的重排、publisher 重试与确认语义。latest release 为 RabbitMQ 4.4.0，见[官方 Release Information](https://www.rabbitmq.com/release-information)。
> - RabbitMQ 4.4.0 官方 [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)，checked 2026-11-06：RabbitMQ 默认 false 的 QoS 标记对应每个 consumer 独立上限；global per-channel 模式在 4.3 起弃用并默认禁用。见[发布信息](https://www.rabbitmq.com/release-information)核对当前 4.4.0 版。
> - RabbitMQ 官方 [Publishers](https://www.rabbitmq.com/docs/publishers) 与 [Consumers](https://www.rabbitmq.com/docs/consumers)，checked 2026-11-06：publisher confirms、不可路由消息检测、消费者预取和并发交付。具体保证仍由已配置的 exchange、queue 类型、持久性、副本和客户端库决定。
> - 数据库 outbox、幂等键和 report job attempt 是应用级机制，见[请求超时后的结果确认](api-reliability-and-async-delivery.md)和[持久报表任务](../architecture/system-design-fundamentals.md)。
> - BullMQ 6.5.3 官方文档（checked 2026-11-09）：[Important Notes](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/bull/important-notes.md)、[Stalled Jobs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/workers/stalled-jobs.md)、[Retrying failing jobs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/retrying-failing-jobs.md)、[Job IDs](https://github.com/taskforcesh/bullmq/blob/v6.5.3/docs/gitbook/guide/jobs/job-ids.md)。这些语义适用于本段标出的 BullMQ 6.5.3；job ID 去重仍受其保留/自动移除边界约束。该版本 custom ID 还不能含冒号或仅由数字组成，因此示例使用带字母前缀的安全意图 ID。
> - PostgreSQL 14 官方 [SELECT 与锁定子句](https://www.postgresql.org/docs/14/sql-select.html) §SELECT、[显式锁](https://www.postgresql.org/docs/14/explicit-locking.html) §13.3.2，checked 2026-11-09：SKIP LOCKED 会跳过无法立即取得的行锁，适用于 queue-like 并发领取。代次/租期状态设计和远端幂等是应用层契约。
