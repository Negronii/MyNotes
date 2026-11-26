# 工程基础

每个信号只证明它所在那一层的事实。复杂度只在声明的成本模型里成立；`write()` 返回、COMMIT 确认、`202 Accepted`、broker 确认、ACK、就绪探针和测试通过，各自只说明一段边界。系统可靠，靠的是稳定身份、持久状态、条件更新、有界资源和可查证的结果，而不是某一层的“恰好一次”。

第一次读，从[选算法时，复杂度结论在什么条件下才成立？](computation/invariants-and-cost-models.md)开始。全领域共用一家 SaaS 的账户报表服务作案例，五条主线分别看它的事件页、导出进程、库存与存储、请求与任务、修复发布。只想先读最常用的正确性机制，可从[两个请求争夺最后一件库存时，怎样保证只预留一次？](data/conditional-writes-and-idempotent-records.md)开始，它最快展示上面的论点，并直接连到主线四的未知结果与重放。

## 五条主线

### 一、数据怎样表示，算法怎样利用顺序和状态，成本落在哪里？

高效方法都在消费一项输入保证：有序、子问题重叠或头下标。复杂度只在写明的成本模型里成立，最坏、期望和均摊是不同口径，规范保证也不等于实现。表示决定怎样找到目标、怎样维护顺序；有序让二分、双指针、窗口和扫描线能安全地排除候选；状态键和标记时机决定图搜索与动态规划是否正确。比较次数之外，缓存行和指针追逐决定真实耗时。主线三的索引、主线二的队列都直接用到这里的选型。

- [选算法时，复杂度结论在什么条件下才成立？](computation/invariants-and-cost-models.md)
- [数组、链表、树和哈希表各靠什么找到目标、维护顺序？](computation/data-structures-by-access-pattern.md)
  - 支线：[怎样遍历一棵树，又怎样把扁平记录安全地还原成树？](computation/trees-traversal-and-reconstruction.md)
  - 支线：[怎样同时按键查找并维护最近使用顺序？](computation/lru-cache.md)
- [待处理的工作该用队列还是栈，各怎样实现？](computation/queues-stacks-and-empty-states.md)
- [不断加入任务时，怎样持续取出最高优先级？](computation/heaps-and-priority-queues.md)
- [有序数据怎样让二分查找和双指针安全排除候选？](computation/ordered-search-and-two-pointers.md)
  - 支线：[分区怎样改变快速排序的时间和空间代价？](computation/partitioning-and-sorting-costs.md)
  - 支线：[文本算法应按码元、码点还是字素簇处理？](computation/text-units-and-unicode.md)
- [边界向前推进时，怎样维护一个有效窗口或活动区间？](computation/sliding-windows-and-sweep-lines.md)
- [搜索状态图时，何时永久标记节点，何时必须回退？](computation/graph-search-and-backtracking.md)
- [动态规划怎样定义状态并安排更新顺序？](computation/dynamic-programming.md)
- [同样是 O(n)，为什么连续扫描往往比链表遍历快？](computation/memory-hierarchy-and-locality.md)

### 二、程序在一台机器上怎样并发、等待和释放资源？

进程是保护边界，线程是执行路径，异步 I/O 让等待不占线程。共享状态必须选定一种所有权规则，否则会丢更新或死锁。事件循环只在让出点切换，同步代码会卡住一切，CPU 工作要交给有界的线程或进程；流用背压把“慢下来”逐段传回源头。取消只是请求，完成信号只证明本层；资源要等到可证明的完成状态才释放，停止时先拒绝新工作再排空。主线三的连接池和主线四的执行槽都按“每进程”计数，就从这里来。

- [一份工作该交给进程、线程还是异步 I/O？](runtime/processes-threads-and-async-io.md)
- [多个执行者共享状态时，怎样不丢更新、不互相卡死？](runtime/shared-state-races-and-deadlocks.md)
- [Node.js 的事件循环怎样安排计时器、I/O 回调和微任务？](runtime/node-event-loop-and-microtasks.md)
- [Node.js 的工作实际在哪个线程或进程上执行？](runtime/node-threads-processes-and-workers.md)
- [异步 FastAPI 接口为什么仍会阻塞，取消和资源又怎样收尾？](runtime/python-asyncio-and-fastapi.md)
  - 支线：[Python 的名字、对象和属性按什么规则工作？](runtime/python-object-model.md)
- [流怎样把“慢下来”逐段传回源头，中途失败又留下什么？](runtime/stream-backpressure-and-partial-output.md)
- [服务进程收到停止信号后，怎样排空工作并安全退出？](runtime/graceful-shutdown.md)

### 三、数据怎样存得对、读得快？

写路径上，把条件附着在写语句上，用约束和唯一键裁决并发；事务界定原子性，隔离级别决定能看见什么，写偏差要另加手段；预写日志把提交确认与数据页写回分开，崩溃后按提交记录恢复。读路径上，SQL 的空值、外连接和聚合粒度决定结果，索引与计划器决定成本，会话与连接池决定连接借多久，键集分页与快照决定翻页是否完整，缓存要说清最多旧多久。单库到顶时按分片键切分，先分清是总容量不足还是热点。这里的条件更新、唯一裁决和事务边界，是主线四实现幂等、领取和栅栏的基础。

- [两个请求争夺最后一件库存时，怎样保证只预留一次？](data/conditional-writes-and-idempotent-records.md)
- [约束守住哪些规则，索引又怎样服务读取？](data/constraints-and-indexes.md)
- [事务能保证什么，并发事务各能看见什么？](data/transactions-and-isolation.md)
- [数据库确认提交后崩溃，靠什么恢复？](data/write-ahead-logging-and-recovery.md)
  - 支线：[InnoDB 怎样用索引记录、旧版本和日志处理同一笔库存事务？](data/mysql-innodb-locks-and-logs.md)
- [空值、外连接和分组会怎样改变一张汇总表的结果？](data/sql-nulls-joins-and-aggregates.md)
- [ORM 会话怎样借用连接，连接池为什么会耗尽？](data/orm-sessions-and-connection-pools.md)
- [怎样无重复、无遗漏地分页读取一个还在变化的集合？](data/keyset-pagination-and-snapshots.md)
- [加了缓存之后，读到的数据最多会旧多久？](data/caching-and-staleness.md)
- [单库接近上限时，怎样选分片键并区分总容量不足与热点？](data/sharding-and-hot-keys.md)
  - 支线：[把一个账户搬到新分片时，怎样保证任一时刻只有一个写入者？](data/shard-migration-and-ownership-transfer.md)

### 四、服务之间怎样交换请求，并在失败和过载下保持正确？

前六章（到 ETag 条件写为止）是“请求与契约”：一次同步请求怎样被识别、授权并按契约回应。HTTP 语义独立于线上版本，缓存按新鲜度和验证复用响应；会话把请求连到可信主体，浏览器控制只守各自的边界，逐次授权才决定能否读写；API 用稳定的错误类型、ETag 条件写和兼容政策，让调用方可以依赖。从未知结果一章起是“异步交接与容量”：请求返回之后，工作怎样交接、确认、重试并受容量约束。写请求超时是未知结果，用同一个操作身份重放，取回该操作的当前状态；耗时工作持久受理，outbox 保证唤醒；worker 条件领取，用递增的 attempt 挡住旧执行者；broker 确认与 ACK 只证明交接，ACK 要等持久状态允许才发出；重试、取消和清理都按持久状态决定；容量由多道门槛决定，超出时在 `202` 之前拒绝。每个请求和任务因此都有稳定身份和可查的持久状态，主线五拿它们当 SLI 的计数单位。

- [一次 HTTP 请求怎样从浏览器到达服务，又带回什么？](services/http-semantics-and-transport.md)
- [一份 HTTP 响应什么时候可以直接复用，什么时候必须回源确认？](services/http-caching-and-conditional-requests.md)
- [请求怎样带上可信的身份，浏览器又替服务守住哪些边界？](services/sessions-and-browser-boundaries.md)
- [服务怎样逐次确认这个主体能对这份资源做这个动作？](services/per-request-authorization.md)
- [怎样让调用方可靠地判断 API 的成功、失败和变化？](services/api-contracts-errors-and-evolution.md)
- [两个客户端同时修改同一资源时，API 怎样防止互相覆盖？](services/conditional-updates-and-etags.md)
  - 支线：[服务端要持续推送更新时，怎样选通道，断线后又怎样接上？](services/real-time-channels-and-resume.md)
- [写请求超时后，怎样查清结果并安全重试？](services/deadlines-retries-and-unknown-outcomes.md)
- [耗时任务怎样被持久受理，并保证一定会被唤醒？](services/durable-job-acceptance-and-outbox.md)
  - 支线：[收到一条 webhook 回调时，怎样确认它真实、未被重放，并可靠地受理？](services/webhook-delivery-and-verification.md)
- [怎样保证一个任务同一时刻只由一个 worker 推进？](services/job-claims-leases-and-fencing.md)
- [发布确认、消费者确认和业务完成各证明什么？](services/queue-delivery-and-acknowledgement.md)
  - 支线：[怎样用 Kafka 分区保序、推进偏移，并在再均衡后安全接手？](services/kafka-partitions-and-offsets.md)
- [任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](services/job-retries-cancellation-and-cleanup.md)
- [一条异步管线能接多少工作，超出时在哪里拒绝？](services/capacity-admission-and-backpressure.md)
  - 支线：[流量远超容量或遭到攻击时，每一层能挡住什么？](services/overload-and-ddos.md)

### 五、一次改动怎样从设计走到生产，并用证据说明它是对的？

先看变化会传播到哪里，再决定要不要抽象。把缺陷改写成可证伪的反例，沿调用路径找到丢失的条件；测试边界由要排除的失败决定，还要证明测试能区分对错。被测快照就是提交快照；一次构建，按摘要晋级；平台按探针和停止顺序管理进程。用用户结果定义 SLI，按版本归因决定是否放量；回退只撤回平台管理的那部分。事故按证据定位，并用同一口径复验恢复。

- [怎样判断一个抽象值不值得引入？](practice/design-for-change.md)
  - 支线：[工厂、策略、观察者和单例各解决什么协作问题，何时多余？](practice/design-patterns-in-practice.md)
  - 支线：[页面编辑器怎样建模文档、编辑会话和发布快照？](practice/page-editor-data-model.md)
- [怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](practice/debugging-and-code-review.md)
- [一次改动该在哪一层测试，怎样证明测试能区分对错？](practice/testing-by-failure-boundary.md)
- [Git 怎样记录一次改动，出错时又怎样按层撤回？](practice/git-snapshots-and-recovery.md)
- [源码怎样变成可运行、可追溯的容器镜像？](practice/container-images-and-builds.md)
  - 支线：[用 Compose 在本地起一套服务时，网络、健康检查、密钥和数据各怎样配？](practice/compose-local-stack.md)
- [已验证的产物怎样原样晋级到生产？](practice/build-once-promote-by-digest.md)
- [服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](practice/production-runtime.md)
- [怎样用用户结果衡量一个服务，并决定还能不能放量？](practice/slis-slos-and-error-budgets.md)
- [新版本怎样逐步放量，出问题时能撤回什么？](practice/canary-rollout-and-rollback.md)
- [发布后用户结果变坏，怎样从信号走到根因并确认恢复？](practice/incident-diagnosis-and-recovery.md)

## 全领域标识符表

各章只引用本主线用到的几行；跨主线查对时看这张表。

| 标识符 | 含义 | 主线 | 首次引入 |
|---|---|---|---|
| `acct-17`、`user-17`、报表 42（`Service health`） | 账户、主体、报表；全领域共用 | 全部 | 各主线首个用到的章 |
| 1,024 条事件；`e07`/`e03`/`e11`/`e18`；目标 `(09:02, e08)` | 报表 42 的事件页，按 `(occurred_at, event_id)` 排序 | 一 | computation/invariants-and-cost-models |
| `job-demo-731` attempt 1；每页 100 行、最多 12 页；三行 CSV 回放 100/600 ms，deadline 1 s | worker 进程里的一次导出执行（领取与确认当作已给定）；API 进程把三行 CSV 直接流给响应 | 二 | runtime/processes-threads-and-async-io |
| `jobs/job-demo-731/attempt-1/report-42.csv.gz` | 结果的最终路径，按 job 和 attempt 区分；临时文件关闭后 `rename` 到这里 | 二 | runtime/stream-backpressure-and-partial-output |
| `SKU-7`（`available` = 1，变体 2）；`reserve-demo-208`；`fingerprint-A`；请求 A、B | 最后一件库存的预留；A 是首次尝试，B 可能是同一请求的并发重放，二者共用幂等键和请求指纹 | 三 | data/conditional-writes-and-idempotent-records |
| `SKU-8` | B 复用 `reserve-demo-208` 却改请求的无货 SKU，与 A 没有共同的锁 | 三 | data/conditional-writes-and-idempotent-records |
| 报表 40、41（`Weekly digest`、`Monthly overview`） | `acct-17` 的普通报表，与 42 一起演示偏移分页漏项和键集分页 | 三 | data/keyset-pagination-and-snapshots |
| `report:v1:acct-17:42:zh-CN`；版本 v3/v4 | 缓存章的语言变体表示 | 三 | data/caching-and-staleness |
| 库 B/7 → D/8、候选 C8、决策 K8、屏障位置 L；`op-9` | 把 `acct-17` 搬到新分片；`op-9` 是与冻结事务争同一所有权行的业务写 | 三 | data/sharding-and-hot-keys、data/shard-migration-and-ownership-transfer |
| `reports.example.test`、`api.reports.example.test`、`idp.identity.test`、`legacy.example.test`；`reports-bff-client`；`idp-user-4821` | 页面与 BFF、API、IdP、不可信的同站旧子域；OIDC client 与 IdP 主体（映射到 `user-17`） | 四 | services/http-semantics-and-transport（IdP 相关在 services/sessions-and-browser-boundaries） |
| `user-17`（`acct-17` 的 `analyst`）；`user-29`（`acct-29` 的 `viewer`） | `analyst` 有 `report:read` 与 `report:export`，`viewer` 只有 `report:read`；`user-29` 是跨账户猜 ID 的已认证主体 | 四、五 | services/per-request-authorization；主线五在 practice/debugging-and-code-review |
| 报表 73（`acct-29`，`Usage summary`） | `user-29` 自己账户的报表；`viewer` 请求导出它得到 `403` | 四 | services/per-request-authorization |
| 报表 43 | 不存在的对照报表；跨账户读取 42 要返回与它相同的通用 `404` | 四、五 | services/per-request-authorization；主线五在 practice/debugging-and-code-review |
| `"report-42-v7"` → `"report-42-v8"` | 报表 42 的强 ETag | 四 | services/http-caching-and-conditional-requests |
| `version=9`/`10`、游标 `103`/`104`、`progress=80` | 推送与续读 | 四 | services/real-time-channels-and-resume |
| `export-demo-415` → `job-demo-731`；`/v1/jobs/job-demo-731`；`report.ready` | 导出幂等键与它创建的 job、job 端点、完成事件 | 四 | services/deadlines-retries-and-unknown-outcomes、services/durable-job-acceptance-and-outbox |
| `d-old`、`d-new` | 带跨账户缺陷的生产稳定版镜像、修复版镜像（按摘要记） | 五 | practice/debugging-and-code-review |
| `fix/report-account-scope`；`c4f2a91` | 修复所在分支；rebase 后的修复提交，构建与验收都绑定这个 ID | 五 | practice/git-snapshots-and-recovery |
| `registry.example.com/team/report-api` | 镜像仓库路径；核验后的 `registry.example.com/team/report-api@sha256:…` 即 `d-new` | 五 | practice/container-images-and-builds |
| 窗口 12:10–12:20 | 事故窗口：`d-new` 100 次读 98 次好，`d-old` 900/900 | 五 | practice/incident-diagnosis-and-recovery |
| `export-demo-416` → `job-demo-732` | 事故恢复后用新幂等键走一遍完整导出路径的复验 | 五 | practice/incident-diagnosis-and-recovery |
| `page-home`；r12→r18 | 页面编辑器独立例的页面与修订号：r16 为公开版，r17 因 `alt` 为空发布被拒，r18 发布 | 五（独立例） | practice/design-for-change；`page-home` 与 r12 在 practice/page-editor-data-model |

## Reading order / 阅读顺序

### 数据怎样表示，算法怎样利用顺序和状态，成本落在哪里？

- [选算法时，复杂度结论在什么条件下才成立？](computation/invariants-and-cost-models.md)
- [数组、链表、树和哈希表各靠什么找到目标、维护顺序？](computation/data-structures-by-access-pattern.md)
- [怎样遍历一棵树，又怎样把扁平记录安全地还原成树？](computation/trees-traversal-and-reconstruction.md)
- [怎样同时按键查找并维护最近使用顺序？](computation/lru-cache.md)
- [待处理的工作该用队列还是栈，各怎样实现？](computation/queues-stacks-and-empty-states.md)
- [不断加入任务时，怎样持续取出最高优先级？](computation/heaps-and-priority-queues.md)
- [有序数据怎样让二分查找和双指针安全排除候选？](computation/ordered-search-and-two-pointers.md)
- [分区怎样改变快速排序的时间和空间代价？](computation/partitioning-and-sorting-costs.md)
- [文本算法应按码元、码点还是字素簇处理？](computation/text-units-and-unicode.md)
- [边界向前推进时，怎样维护一个有效窗口或活动区间？](computation/sliding-windows-and-sweep-lines.md)
- [搜索状态图时，何时永久标记节点，何时必须回退？](computation/graph-search-and-backtracking.md)
- [动态规划怎样定义状态并安排更新顺序？](computation/dynamic-programming.md)
- [同样是 O(n)，为什么连续扫描往往比链表遍历快？](computation/memory-hierarchy-and-locality.md)

### 程序在一台机器上怎样并发、等待和释放资源？

- [一份工作该交给进程、线程还是异步 I/O？](runtime/processes-threads-and-async-io.md)
- [多个执行者共享状态时，怎样不丢更新、不互相卡死？](runtime/shared-state-races-and-deadlocks.md)
- [Node.js 的事件循环怎样安排计时器、I/O 回调和微任务？](runtime/node-event-loop-and-microtasks.md)
- [Node.js 的工作实际在哪个线程或进程上执行？](runtime/node-threads-processes-and-workers.md)
- [异步 FastAPI 接口为什么仍会阻塞，取消和资源又怎样收尾？](runtime/python-asyncio-and-fastapi.md)
- [Python 的名字、对象和属性按什么规则工作？](runtime/python-object-model.md)
- [流怎样把“慢下来”逐段传回源头，中途失败又留下什么？](runtime/stream-backpressure-and-partial-output.md)
- [服务进程收到停止信号后，怎样排空工作并安全退出？](runtime/graceful-shutdown.md)

### 数据怎样存得对、读得快？

- [两个请求争夺最后一件库存时，怎样保证只预留一次？](data/conditional-writes-and-idempotent-records.md)
- [约束守住哪些规则，索引又怎样服务读取？](data/constraints-and-indexes.md)
- [事务能保证什么，并发事务各能看见什么？](data/transactions-and-isolation.md)
- [数据库确认提交后崩溃，靠什么恢复？](data/write-ahead-logging-and-recovery.md)
- [InnoDB 怎样用索引记录、旧版本和日志处理同一笔库存事务？](data/mysql-innodb-locks-and-logs.md)
- [空值、外连接和分组会怎样改变一张汇总表的结果？](data/sql-nulls-joins-and-aggregates.md)
- [ORM 会话怎样借用连接，连接池为什么会耗尽？](data/orm-sessions-and-connection-pools.md)
- [怎样无重复、无遗漏地分页读取一个还在变化的集合？](data/keyset-pagination-and-snapshots.md)
- [加了缓存之后，读到的数据最多会旧多久？](data/caching-and-staleness.md)
- [单库接近上限时，怎样选分片键并区分总容量不足与热点？](data/sharding-and-hot-keys.md)
- [把一个账户搬到新分片时，怎样保证任一时刻只有一个写入者？](data/shard-migration-and-ownership-transfer.md)

### 服务之间怎样交换请求，并在失败和过载下保持正确？

- [一次 HTTP 请求怎样从浏览器到达服务，又带回什么？](services/http-semantics-and-transport.md)
- [一份 HTTP 响应什么时候可以直接复用，什么时候必须回源确认？](services/http-caching-and-conditional-requests.md)
- [请求怎样带上可信的身份，浏览器又替服务守住哪些边界？](services/sessions-and-browser-boundaries.md)
- [服务怎样逐次确认这个主体能对这份资源做这个动作？](services/per-request-authorization.md)
- [怎样让调用方可靠地判断 API 的成功、失败和变化？](services/api-contracts-errors-and-evolution.md)
- [两个客户端同时修改同一资源时，API 怎样防止互相覆盖？](services/conditional-updates-and-etags.md)
- [服务端要持续推送更新时，怎样选通道，断线后又怎样接上？](services/real-time-channels-and-resume.md)
- [写请求超时后，怎样查清结果并安全重试？](services/deadlines-retries-and-unknown-outcomes.md)
- [耗时任务怎样被持久受理，并保证一定会被唤醒？](services/durable-job-acceptance-and-outbox.md)
- [收到一条 webhook 回调时，怎样确认它真实、未被重放，并可靠地受理？](services/webhook-delivery-and-verification.md)
- [怎样保证一个任务同一时刻只由一个 worker 推进？](services/job-claims-leases-and-fencing.md)
- [发布确认、消费者确认和业务完成各证明什么？](services/queue-delivery-and-acknowledgement.md)
- [怎样用 Kafka 分区保序、推进偏移，并在再均衡后安全接手？](services/kafka-partitions-and-offsets.md)
- [任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](services/job-retries-cancellation-and-cleanup.md)
- [一条异步管线能接多少工作，超出时在哪里拒绝？](services/capacity-admission-and-backpressure.md)
- [流量远超容量或遭到攻击时，每一层能挡住什么？](services/overload-and-ddos.md)

### 一次改动怎样从设计走到生产，并用证据说明它是对的？

- [怎样判断一个抽象值不值得引入？](practice/design-for-change.md)
- [工厂、策略、观察者和单例各解决什么协作问题，何时多余？](practice/design-patterns-in-practice.md)
- [页面编辑器怎样建模文档、编辑会话和发布快照？](practice/page-editor-data-model.md)
- [怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](practice/debugging-and-code-review.md)
- [一次改动该在哪一层测试，怎样证明测试能区分对错？](practice/testing-by-failure-boundary.md)
- [Git 怎样记录一次改动，出错时又怎样按层撤回？](practice/git-snapshots-and-recovery.md)
- [源码怎样变成可运行、可追溯的容器镜像？](practice/container-images-and-builds.md)
- [用 Compose 在本地起一套服务时，网络、健康检查、密钥和数据各怎样配？](practice/compose-local-stack.md)
- [已验证的产物怎样原样晋级到生产？](practice/build-once-promote-by-digest.md)
- [服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](practice/production-runtime.md)
- [怎样用用户结果衡量一个服务，并决定还能不能放量？](practice/slis-slos-and-error-budgets.md)
- [新版本怎样逐步放量，出问题时能撤回什么？](practice/canary-rollout-and-rollback.md)
- [发布后用户结果变坏，怎样从信号走到根因并确认恢复？](practice/incident-diagnosis-and-recovery.md)

## 与 AI 工程、前端的关系

幂等与未知结果、outbox、队列确认、条件领取与栅栏、HTTP 语义与缓存、认证与授权、事务、缓存陈旧和键集分页都在这里讲完整。[AI 工程](../ai-engineering/index.md)与[前端](../frontend/index.md)只讲这些机制在各自领域的状态名、产品和界面，并链回这里。
