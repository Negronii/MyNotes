# What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？

A publisher confirm and a consumer acknowledgement cover different handoffs. A publisher confirm says the broker accepted a publish under its own configured rules; it does not say a consumer performed the business operation. A consumer acknowledgement tells the broker that the consumer reached the chosen processing boundary. If either confirmation is lost, work may be repeated, so make the business effect idempotent and acknowledge only after its durable outcome. / 发布者确认和消费者确认覆盖不同的交接边界。发布者确认表示 broker 按自身配置规则接受了消息，并不表示 consumer 已执行业务操作。消费者确认告诉 broker，consumer 已达到系统选定的处理边界。任一确认丢失都可能造成重复处理，因此业务效果应可幂等，并且只有在持久化业务结果后才确认消息。

**Key terms / 关键术语：** publisher confirm / 发布者确认；consumer acknowledgement / 消费者确认；redelivery / 重投；deduplication / 去重；ordering / 顺序；dead-letter queue / 死信队列。

~~~mermaid
sequenceDiagram
    participant P as Publisher
    participant B as Broker
    participant C as Consumer
    participant D as Business store
    P->>B: Publish message
    B-->>P: Confirm broker acceptance
    B->>C: Deliver message
    C->>D: Commit idempotent business effect
    D-->>C: Durable outcome
    C->>B: Acknowledge delivery
    Note over P,B: Lost confirm may cause publisher retry and duplicate publish
    Note over C,B: Crash after commit but before ack may cause redelivery
~~~

The sequence has two separate ambiguity windows. If the broker accepted a publish but its confirmation did not reach the publisher, the publisher may resend and create a duplicate. If the consumer commits its effect and then crashes before acknowledging, the broker may redeliver the message. If the consumer acknowledges before durable work, a crash can lose the work. The application therefore needs stable message or operation identity and an idempotent effect; queue delivery alone is not proof of business completion.

## Publisher confirmation / 发布者确认

Publisher confirms cover the publisher-to-broker boundary under the broker's rules. They do not know whether a consumer received, acknowledged, or completed the message. The publisher must also distinguish a broker confirmation from a routing guarantee: depending on broker and configuration, acceptance by an exchange may not mean that the message reached the intended queue.

With RabbitMQ, a publisher that has not received a confirm when a connection fails cannot know whether the message was accepted; retrying may duplicate it. For routable persistent messages, what the confirm means depends on the message and queue type; consult the configured queue's durability and replication semantics. A confirm is not a transaction across the publisher's database and the broker. Persisting business state and an outbox row together, then publishing from that outbox, handles that separate database-to-broker dual-write problem. The account-report implementation is in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md).

## Consumer acknowledgement and redelivery / 消费者确认与重投

Choose the consumer's acknowledgement point from the business completion contract. If processing consists of a database update, make that update idempotent by message ID or operation key. A crash after database commit but before broker acknowledgement can then trigger redelivery without repeating the effect. The database commit and broker acknowledgement usually cannot share one local transaction, so this remaining duplicate window is expected.

With RabbitMQ 4.3 manual acknowledgements, an unacknowledged delivery is requeued when its channel or connection closes. Consumers must be ready for redelivery. This is a broker-specific behavior, not a universal queue rule. Acknowledging before durable work can lose work; acknowledging after durable work can cause redelivery if the acknowledgement is lost, so processing should tolerate duplicates.

A dead-letter queue makes repeatedly failed messages visible only if it is monitored and someone has defined whether to repair, retry, or discard them. Immediate requeue can create a hot retry loop, so define bounded attempts or delayed retry behavior. Keep the application operation's idempotency record and any relevant status query separate from the queue's delivery state.

## Preserve the order the business needs / 保留业务需要的顺序

Concurrent consumers may finish messages in a different order from delivery. A FIFO queue does not automatically serialize all effects across multiple consumers, retries, or partitions. If completion order is a correctness rule, define its scope—often per account or key—and enforce it with a single ordered partition, per-key sequence, conditional state transition, or serialization at the worker. Confirm the chosen broker's exact delivery and ordering contract.

Observe each boundary separately: publish attempts and confirms, unroutable messages, queue depth and oldest-message age, unacknowledged deliveries, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A growing oldest-message age indicates delay even while a queue continues accepting work. [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](api-capacity-and-backpressure.md) explains how to constrain the work waiting behind those boundaries.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](api-reliability-and-async-delivery.md) covers ambiguous request outcomes and operation idempotency; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](../architecture/system-design-fundamentals.md) applies outbox, attempt fencing, and post-outcome acknowledgement to a report job; [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) covers the local transaction boundary used to persist business effects.

**Sources / 来源：** RabbitMQ 4.3, [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) and [Reliability Guide](https://www.rabbitmq.com/docs/reliability), checked 2026-11-05. These references document RabbitMQ's confirm, manual-ack, redelivery, and publisher retry behavior; other brokers have different contracts.
