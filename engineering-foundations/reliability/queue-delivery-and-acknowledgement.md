# 报表任务的发布确认、消费者确认与业务完成各证明什么？

账户 acct-17 为 report 42 发起导出时，请求幂等键为 report-demo-208，并在 application programming interface（应用程序接口，API）的数据库事务里创建 job（任务）job-demo-731 和 outbox（事务发件箱）行。report 42 也可由只读 API 路径查询；读状态码与异步 job 的状态或结果对象提交是不同的用户结果，不能互相代替。relay（转发进程）再把工作意图发布到 broker（消息代理）。publisher confirm（发布者确认）覆盖 relay 到 broker 的接收边界；consumer acknowledgement（消费者确认，常写作 ACK）覆盖 broker 到 worker（工作进程）的交付处理边界；job 的 succeeded 状态和私有对象引用才是应用对用户作出的业务完成记录。

~~~mermaid
sequenceDiagram
    participant A as API / database
    participant R as Outbox relay
    participant B as RabbitMQ broker
    participant W as Report worker
    participant O as Private object storage
    A->>A: 同事务写 job + pending outbox + 预留一个等待槽
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

confirm 的含义还受消息和 queue（队列）类型影响。RabbitMQ 的 publisher confirm 不是路由保证：消息被 exchange（交换器）接受，并不一定已进入预期 queue。若采用 RabbitMQ 的 mandatory 发布，应将该次 publish 的 publisher confirm ack 与关联的 basic.return 联合判断：4.4 中不可路由消息会先 basic.return、再收到 confirm ack，因此“有 confirm ack 且没有关联 return”才能说明至少路由到了某个 queue。它仍不证明该 queue 是业务目标；exchange、binding 和备用 exchange 必须按明确拓扑预先验证。若 routing contract 由其他 broker/机制保证，则按该契约检查路由结果。durable message/queue（持久消息/队列）与副本类型也决定 broker 按什么配置确认承担责任；不要把另一种 queue 的保证套用过来。

outbox relay 可以按此顺序推进：读取一条未发布 outbox 意图，发布它所指向的 job ID；只有所选路由契约通过（例如 mandatory publish 已收到 confirm ack，且没有关联的 basic.return）后，才标记这个 intent 自己的 outbox 行已发布。confirm 状态未知或出现 return 时保留意图并报告发布/路由故障，修复后重试；重复 publish 可能得到相同逻辑 job 的消息，RabbitMQ 不在这里替应用去重。数据库事务和 RabbitMQ 事务不是一个原子事务；重复消息可接受的前提是 consumer（消费者）按持久 job 状态幂等处理。账户报表如何把 job、outbox 和等待槽同事务提交见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 消费者在业务结果持久后才 ACK

给 job-demo-731 的 delivery（消息投递）载荷只带稳定 job ID，不带 attempt。worker 从数据库读取任务，并只对 `queued` 状态做 conditional claim（条件领取）：在同一数据库事务中把状态改为 `running`、生成新的 attempt（尝试号）并释放这个排队轮次的等待槽。重投消息只是查询权威 job 的线索；若已有 `running` 尝试且租约尚未过期，不能据此接管或另起 attempt。租约到期只让数据库恢复器有资格尝试接管；它必须先赢得条件更新，再把任务改回 `queued`、预留新槽并写入新的 outbox intent。随后当前 worker 才能领取新 attempt。attempt 来自数据库的胜者更新，不能信任可能重复、延迟或过期的 queue message（队列消息）。结果对象写入后，只有成功提交 `succeeded` 和对象 key，才向 broker 发 consumer ACK。用户读取结果仍要经 API 做授权，不能因 message 已被 ACK 就把对象公开。

成功条件必须把当前状态、attempt 和取消请求一起放进更新谓词，且对象已经写好后才提交：

~~~sql
UPDATE report_jobs
SET status = 'succeeded', result_object_key = :object_key
WHERE job_id = :job_id
  AND status = 'running'
  AND attempt = :attempt
  AND cancel_requested = FALSE;
~~~

若更新一行，事务提交后 ACK；若更新零行，先重新读取权威 job/outbox 状态。若已有未过期的 `running` attempt，本条重投不能另起尝试；可以按队列策略延迟它，或在确认持久租约恢复器会于过期后创建新 outbox 意图并重排时 ACK 这条重复消息。若任务已取消或终结，持久状态能证明无需再做；若仍为 `queued` 或后继意图尚未持久，则不能盲目 ACK，否则可能丢失尚未重新排队的工作。租约到期也不自动使旧 worker 失权，实际竞争以数据库条件更新的提交先后决定。

如果更新为零是因为 `cancel_requested` 已置位，不能把旧 worker 的失败返回或已上传对象当作成功。先读取并持久化取消终态，或交给租约恢复流程完成取消；只有状态和清理/保留策略已经持久后，才按 broker 契约 ACK。对象上传本身也不让结果对用户可见；只有数据库引用提交后，授权 API 才能提供结果。

| 失败时点 | broker 可能采取的动作 | 应用要保持的条件 |
|---|---|---|
| broker 已接收 publish，confirm 未到 relay | relay 重发，同一 job ID 可能有多条消息 | 对当前持久 job/attempt 的完成更新只能有一个赢家 |
| worker 在持久结果前崩溃，delivery 尚未 ACK | RabbitMQ 连接或 channel 关闭后可重新排队未 ACK delivery | 重投仅触发读取权威 job；若仍为未过期的 `running`，不能另起 attempt。租约到期后也须等恢复器条件接管并重排，才可领取新 attempt |
| 数据库已提交 succeeded，worker 发 ACK 前崩溃 | delivery 可再次到达另一个 worker | 后继 worker 查到 job 已终态/attempt 已失效，不得重复业务副作用，再 ACK 重复消息 |
| worker 先 ACK，再提交结果前崩溃 | broker 可删除这条 delivery，不会再因它自动重投 | 如果没有独立的持久恢复扫描，job 可能一直滞留；报表任务设计中的 lease recovery（租约恢复）会扫描过期的 running job，用条件更新 fencing（栅栏校验）并通过新的 outbox intent 重排。因此该恢复依赖数据库恢复器而非 broker。 |

若成功提交了对象但数据库事务未能提交，可能留下不可见的孤儿对象；以 attempt key 命名并在无引用、任务终态和宽限期满足后清理。若数据库已提交成功但 ACK 丢失，重复 handler 应通过终态 job、attempt fencing（尝试栅栏校验）或 operation key 得到“已完成/重复”而不是再次发布或覆盖结果。数据库提交、ACK 与恢复器抢占的状态谓词由 report job 设计章负责，本篇只解释 broker 交界。

## 重试、并发窗口与顺序会改变负载

RabbitMQ 4.4 使用手动确认时，未确认 delivery 在其 channel（通道）或 connection（连接）关闭后可自动 requeue（重新排队）；这是 RabbitMQ 的行为，不能无条件推广到所有 broker。automatic acknowledgement（自动确认）模式在发送后就视为已交付，可提高吞吐，但应用还没处理就断线时会失去工作。对需要可靠完成的报表任务，选择手动 ACK 并把 ACK 放在业务持久化之后；若依赖数据库租约扫描恢复被提前确认的任务，要把恢复器视为独立的正确性机制。

RabbitMQ 4.4 的 consumer prefetch（消费者预取上限）默认按单个 consumer（消费者）计算，而不是整个 channel（通道）：例如一个 consumer 设 prefetch=4，就最多有四条它自己的 delivery 未 ACK；同一个 channel 上若有三个 consumer，总数可以达到 12。RabbitMQ 4.3 起全局 per-channel QoS 已弃用且默认禁用。prefetch 同时影响 worker 的并行量、进程内排队和内存，不应设置为无限而不评估容量。

失败重试要有边界：瞬时故障可安排有延迟的有限重试；永久 schema（结构定义）错误或格式错误应进入可观测 dead-letter queue（死信队列，DLQ），由处理流程决定修复重放或隔离丢弃。反复立刻重新排队会形成热循环。若业务要求每个账户按顺序更新，必须明确顺序的键范围，并用单一有序分区、序号条件更新或串行化保证；first in, first out（先进先出，FIFO）名称不自动保证多个 worker 的业务完成顺序。

## 观测每个交接点，不能只数 ACK

单独记录 publish 尝试、confirm/return、queue depth 和 oldest-message age、unacked 数、重投、重试、ACK、DLQ、job succeeded/failed 及对象引用提交。oldest-message age 持续增长表示结果延迟，即使队列还在接受消息。broker 继续接收并不代表 worker 有容量；worker 发 ACK 也只表示应用确认到达选择的处理边界，不等于用户后来成功下载了报告。更完整的事故定位见[如何从报表服务信号定位发布故障？](observability-slos-and-incident-response.md)。

> [!info]- 来源
> - RabbitMQ 官方 [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) 与[发布何时确认](https://www.rabbitmq.com/docs/confirms#when-will-published-messages-be-confirmed-by-the-broker)、[Reliability Guide](https://www.rabbitmq.com/docs/reliability)，checked 2026-11-06：确认方向相互独立、mandatory/unroutable 的 `basic.return` 在 confirm ack 前、手动/自动 ack、未确认消息在 channel/connection 关闭后的重排、publisher 重试与确认语义。latest release 为 RabbitMQ 4.4.0，见[官方 Release Information](https://www.rabbitmq.com/release-information)。
> - RabbitMQ 4.4.0 官方 [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)，checked 2026-11-06：RabbitMQ 默认 false 的 QoS 标记对应每个 consumer 独立上限；global per-channel 模式在 4.3 起弃用并默认禁用。见[发布信息](https://www.rabbitmq.com/release-information)核对当前 4.4.0 版。
> - RabbitMQ 官方 [Publishers](https://www.rabbitmq.com/docs/publishers) 与 [Consumers](https://www.rabbitmq.com/docs/consumers)，checked 2026-11-06：publisher confirms、不可路由消息检测、消费者预取和并发交付。具体保证仍由已配置的 exchange、queue 类型、持久性、副本和客户端库决定。
> - 数据库 outbox、幂等键和 report job attempt 是应用级机制，见[请求超时后的结果确认](api-reliability-and-async-delivery.md)和[持久报表任务](../architecture/system-design-fundamentals.md)；本文不声称对真实 broker 做了部署验证。
