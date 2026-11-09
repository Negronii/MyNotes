# 怎样用 Kafka 分区保序、推进偏移并安全接手？

**案例：** 合成报表服务为 reportId 42 产生 queued、rendered、ready 三个事件，在线投影维护当前状态；值班排查时，还要能从保留的日志重建投影。Kafka 可让同一键的记录落在同一分区并按追加顺序读取，但异步工作线程仍可能乱序写入投影；本例会把业务状态应用顺序与 offset 恢复位置分别说明，也不把 Kafka 的边界误当成外部数据库事务。

~~~mermaid
flowchart TD
    API[报表服务] -->|key=report-42| Part[report-events 的一个分区]
    Part --> Log[分区内追加日志与记录位置]
    Log --> C1[同一 consumer group 的消费者]
    C1 --> Apply[串行应用或按 seq 约束写入]
    Apply --> DB[外部数据库投影已提交]
    DB --> Prefix[推进该分区的连续完成前缀]
    Prefix --> Commit[提交前缀后的下一个 offset]
    Group[组协调器与成员代次] -->|分配/撤销分区| C1
    Replay[独立重建 group] -->|读取保留日志| Log
~~~

reportId 是分区键；本例的 API 按该键顺序发出一个报表的状态事件。主投影和重建投影使用不同 consumer group（消费者组），所以两者各自保存读取位置，不会彼此抢消息。分区数量、键到分区的映射方式和生产者的发送顺序是这个案例的输入契约。

## 哪个顺序由分区保证？

Kafka topic（主题）拆成多个 partition（分区），每个分区是独立追加的有序日志。分区内的 offset（偏移）是记录的位置；两个分区之间没有天然的全局顺序。Kafka producer（生产者）可用 key（消息键）让相同键的记录通常经同一分区计算路径发送；同一 reportId 因此可以保持同分区顺序。这个顺序是 broker（消息代理）实际追加顺序，不会自动替业务判断“哪个事件先发生”。

固定本例为三个分区、一个生产者按业务序号串行发送，并启用 producer idempotence（生产者幂等）：

~~~text
report-events / partition 0
offset 40  report-42  seq=1  queued
offset 41  report-42  seq=2  rendered
offset 42  report-42  seq=3  ready

report-events / partition 1
offset 18  report-17  seq=1  queued
offset 19  report-17  seq=2  ready
~~~

消费者组把每个分区分配给组内一个活跃消费者；例如 C1 负责分区 0 和 1，C2 负责分区 2。组外的第二个重建 group 可以独立从分区 0 的 offset 0 开始，前提是该位置仍在保留窗口内。若活跃分区数是 3，组内添加第 4 个消费者不会制造第 4 路分区并行度，它会暂时没有分区。

“相同 key”本身也有边界：增加 topic 分区数可能改变默认消息键到分区的映射，扩分区前后的同一 reportId 就可能落到不同分区。此时新分区里的追加记录不能凭 offset 自动排在旧分区已有事件之后。若业务要求跨扩容仍严格保序，应使用显式兼容的路由版本、按键迁移状态，或在消费端校验业务序号并处理断档。多生产者并发时，谁先写入分区由实际到达顺序决定；业务事件若有权威顺序，还要由上游序列号或单一写入路径表达。

## 提交的 offset 为什么是“下一个要读的位置”？

Kafka 存储的 committed offset（已提交偏移）代表恢复后要读的下一个位置。处理完 offset 40 后，提交 41；提交 40 会让恢复从 40 再读一次。概念上，提交 43 表示本例中 40、41、42 已全部完成。offset 数字不要求对应用可见的记录连续：日志压缩可移除 41；消费者使用 `read_committed` 时也看不到已中止事务的记录。因此连续前缀按实际交付的记录顺序判断，不是等待每个整数 offset。

若应用把同一分区的多条记录派给异步工作线程，完成顺序可能与提交顺序不同：

~~~text
已交付：40、41、42
工作完成：41 ✓，42 ✓，40 仍在运行
可安全提交的下一个位置：40
等 40 也完成：40 ✓，41 ✓，42 ✓
可安全提交的下一个位置：43
~~~

41 和 42 先完成，不代表 40 已经产生外部效果。此刻提交 43 会让崩溃恢复跳过仍未完成的 40。每个分区要维护“按交付顺序已完成、且没有未完成记录挡在前面的前缀”；可以串行处理，或按分区并行但只推进到最早未完成的已交付记录之前。若 poll 交付 40 和 42，而 41 已被日志压缩移除（或在 `read_committed` 下因事务中止而不可见），40 完成、42 未完成时，可提交 41 作为下一个位置；恢复从 41 扫描时会跳过缺失的记录并交付 42。此时不能直接提交批次末的 43；等 42 也完成后才可提交 43。整数缺口本身不表示工作丢失，越过仍未完成的记录才会丢失工作。

连续前缀只限制恢复位置，不会替数据库安排业务效果的先后。若 40 是 `queued`、41 是 `rendered`，并行任务可能先把 41 写成 `rendered`，再把 40 写成 `queued`；提交仍停在 40 也不能撤销已经发生的状态倒退。稳定 `event_id` 的去重只识别同一事件的再次投递，40 和 41 是不同事件，不能靠去重解决乱序。若每一步状态转换都必须执行，应按 reportId 串行应用，或并行准备数据后依业务序号顺序提交。以下另设一个只存完整状态快照的投影：已预置 `report_id=42`、`last_seq=0`（非 NULL），每条事件都携带可替代当前状态的完整快照；因此允许跳过中间状态，并用条件更新拒绝较旧序号。SQL 用命名绑定参数表示：

~~~sql
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = :report_id AND last_seq < :seq;
~~~

按本例的乱序完成次序，应用 41（seq=2）把行改为 `rendered/2`，应用 42（seq=3）改为 `ready/3`；随后应用 40（seq=1）因 `last_seq < 1` 不成立而影响 0 行，状态仍是 `ready/3`。由于旧完整快照已被较新快照覆盖，这个零行结果是成功无操作；但 offset 40 仍要等这项无操作完成后才能推进前缀并提交 43。条件更新只保证快照不倒退，不会执行被跳过的状态转换；若每个转换都有业务副作用，应使用前述顺序应用。事件 ID 去重仍可处理相同事件重投，但不替代顺序约束。

## 崩溃发生在处理与提交的哪一边？

假设 group 当前 committed offset 为 40，要把事件 40 写成数据库中的报表状态：

| 崩溃点 | 数据库状态 | Kafka 恢复位置 | 后果 |
| --- | --- | --- | --- |
| 数据库事务先提交，Kafka offset 尚未提交 | 数据库已应用事件 40 | 仍从 40 读 | 事件 40 重做；稳定 event_id/inbox 可消除同一事件的重复效果，完整快照也可由 last_seq 条件让重放成为无操作 |
| Kafka 先提交 41，数据库尚未提交事件 40 | 数据库没有事件 40 的效果 | 从 41 读 | 事件 40 被跳过，投影缺少一次更新 |

所以普通外部数据库消费者通常在业务事务成功后再提交 offset，接受“至少一次”以及重放，并让数据库按稳定 event_id 原子去重。若先提交 Kafka offset，就必须接受处理失败时的丢失窗口，不能称为安全交付。提交 offset 和业务效果若位于两个系统，二者之间总有先后；普通 Kafka commit 不会替外部数据库建立原子事务。

## 再均衡怎样拒绝旧成员的提交？

成员加入、离开或超时会触发 rebalance（再均衡），组协调器据当前成员重新分配分区。另看一个独立的 classic group protocol（经典组协议）调度：代次 5 只有 C1 持有分区 0，已提交 offset 为 40；新成员 C2 加入后，组进入代次 6，把分区 0 交给 C2。交接有两种结果：

| C1 在撤销时的状态 | C1 对 offset 40 的处理 | C2 接手位置 |
| --- | --- | --- |
| 协调器尚未撤销旧代次；C1 在撤销回调停止派发新工作，完成 40 并成功同步提交 41 | 已提交位置成为 41 | C2 从 41 读取 |
| 协调器已撤销旧代次；C1 的提交 41 被 fencing 拒绝 | 已提交位置仍为 40 | C2 从 40 读取并重放事件 40 |

撤销回调中的排空和提交有边界：只有仍获准的旧成员才能成功提交；失权后不能再假定有一次提交机会。若事件 40 已先写入数据库而 offset 41 未提交，C2 会重放它，数据库仍需用 event_id 或序号条件处理重复。

这个 fencing（栅栏拒绝）只保护 Kafka 组成员与 offset 提交。event_id 只阻止同一事件重复产生效果；前成员后台任务执行的另一个事件仍可能第一次写入数据库。若业务要求分区失权后的旧任务不能再写，目标数据库必须在同一事务内核验当前 ownership epoch 并应用业务更新，或在新所有者接手前确认所有旧任务已完成/停止。若投影只保存完整快照，可用上一节的 last_seq 条件阻止旧快照覆盖新快照，但这不执行每一步转换。只捕获 Kafka 的 CommitFailedException 不能回滚已经提交的 SQL。

官方 Java 客户端提供 ConsumerRebalanceListener 的分区撤销与分配回调；具体重平衡协议有 classic 和 consumer 两种，4.1 文档中的提交请求携带 group generation 或 member epoch。本文只推演组管理的所有权与 offset fencing，不假定不同协议的回调时序相同，也不固定一个再均衡耗时。

## 回放能重建到哪里？

在线投影用稳定的 consumer group 保存进度，从当前 offset 持续追事件。历史重建可以新建 group，并把每个分区的下一读取位置与初始快照一起保存；新表从该位置向后重算。如果只是复用在线 group 并重置 offset，会改变在线投影的恢复点。切换读取前选定每分区 next-offset 向量 T。T[p] 表示下一要处理 offset；投影在 T 的状态应恰好包含已交付且 offset < T[p] 的记录，不能把 consumer 已提交位置直接当作异步数据库效果已完成的证明。先让在线投影完成所有 `< T[p]` 的外部效果并暂停在 T，再让重建表也只应用到 `< T[p]`、不处理 `>= T[p]`，核对两边在 T 的状态后切读。新 group 以 T 为恢复位置继续消费；`>= T[p]` 的事件仍须在 Kafka 保留窗口内，随后由新投影处理。这样比较的是同一组每分区边界上的状态，而不是任意时刻的表行数。

回放范围受 retention（保留）策略限制。若旧 offset 已超出仍保留的日志范围，设置 earliest 只能从“当前最早可读记录”开始，不能复活已删除事件；若使用日志压缩，同一键的旧状态事件可能被保留为较新值所替代。需要完整历史时，应把容量与保留窗口按最慢重建速度设计，或备份快照并从其对应的 offset 接续重放。

Kafka 的事务可把 Kafka 输出 topic 的记录与被消费分区的 offset 一起提交；读者用 read_committed 隐藏中止事务的输出。这能支持 Kafka 到 Kafka 的原子处理，但没有将一个 MySQL/PostgreSQL 写入纳入同一事务。数据库输出仍需本地事务写入业务效果和 inbox/outbox（收件箱/发件箱），或由目标数据库保存并原子推进消费位置。更一般的确认与重试语义见[报表任务的发布确认、消费者确认与业务完成各证明什么？](queue-delivery-and-acknowledgement.md)。

若要继续看账户报表持久任务的本地提交边界，见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

> [!info]- 来源
> - 分区内全序、一个组内每分区由一个消费者承接、consumer position 是下一个记录 offset：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Consumer Position；键的语义分区：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Distribution。
> - 按 key 选择分区的 producer 行为：[Apache Kafka 4.1 Producer Configs](https://kafka.apache.org/41/configuration/producer-configs/)；扩分区后同键路由变化是基于默认哈希分区映射的推论，具体仍取决于 producer partitioner。
> - Producer retry 可能让后发 batch 先于重试 batch 写入；producer idempotence 与顺序配置边界：[Apache Kafka 4.1 Producer Configs](https://kafka.apache.org/41/configuration/producer-configs/)，retries 与 partitioner.class。
> - Java 消费者提交的 offset 应是下一个读取位置；再均衡撤销/分配回调与失去分区后的 commit 失败：[Apache Kafka Java Client 4.1.2 KafkaConsumer Javadoc](https://kafka.apache.org/41/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)，Offset commit 与 ConsumerRebalanceListener。
> - classic generation 与 consumer member epoch 均进入 offset commit 协议：[Apache Kafka 4.1 Protocol](https://kafka.apache.org/41/design/protocol/)，OffsetCommit Request。
> - Kafka 输出记录和消费位置可共处 Kafka 事务；外部系统需要共同参与才能原子提交：[Apache Kafka 4.1 Design](https://kafka.apache.org/41/design/design/)，Using Transactions。
> - `read_committed` 下的可见记录、offset 超范围时的 earliest/latest/none 策略与消费者故障导致分区重新分配：[Apache Kafka 4.1 Consumer Configs](https://kafka.apache.org/41/configuration/consumer-configs/)；日志压缩与分区保留：[Apache Kafka 4.1 Topic Configs](https://kafka.apache.org/41/configuration/topic-configs/)；本章的报表 42 业务序号、并发完成次序、数据库去重字段、`last_seq` 投影条件和对齐切读的 offset 向量是合成应用合约。
