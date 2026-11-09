# 工程基础

先从最后一件库存的预留看请求怎样变成可靠的数据提交，再追问超时之后如何确认结果。账户报表的异步作业把队列、运行时容量、部署和故障诊断连起来；算法与内存布局则解释这些系统背后的访问成本。

## 从问题开始

- [两个请求争夺最后一件库存时，怎样保证只预留一次？](databases/database-fundamentals.md)——建议先读，从库存约束走到事务提交。
- [请求超时后如何确认结果并安全重试？](reliability/api-reliability-and-async-delivery.md)——沿请求标识确认结果并安全重试。
- [怎样从报表服务信号定位发布后的故障？](reliability/observability-slos-and-incident-response.md)——先用指标、追踪和日志定位环节，再决定改哪里。

## Reading order / 阅读顺序

### 从请求到受约束的数据提交

- [两个请求争夺最后一件库存时，怎样保证只预留一次？](databases/database-fundamentals.md)
- [浏览器请求如何到达 HTTP 响应？](networking/http-protocols-and-websockets.md)
- [如何设计可预期的 HTTP API 契约？](backend/http-api-contracts.md)
- [Cookie 会话与 OIDC 令牌怎样建立身份？](security/web-sessions-and-oidc.md)
- [如何逐次授权租户内的报表资源？](security/web-security-and-authentication.md)
- [浏览器安全控制分别保护什么信任边界？](security/web-browser-security-boundaries.md)
- [SQL 空值、连接与分组会怎样改变报表 42 的结果？](databases/sql-null-joins-and-aggregates.md)
- [如何用约束保护业务规则并为读取建立索引？](databases/database-constraints-and-indexes.md)
- [事务隔离与预写日志能保证什么？](databases/database-transactions-isolation-and-recovery.md)
- [InnoDB 怎样用索引记录、旧版本与日志处理库存事务？](databases/mysql-innodb-index-lock-and-recovery.md)
- [怎样限定对象关系映射会话并排查连接池耗尽？](backend/data-access-and-connection-pools.md)
- [怎样缓存数据库读取并说明陈旧窗口？](backend/caching-and-redis.md)
- [单库接近容量上限时，怎样分片并在搬迁中保持唯一写入者？](databases/database-sharding-and-rebalancing.md)

### 超时之后：确认结果与恢复任务

- [请求超时后如何确认结果并安全重试？](reliability/api-reliability-and-async-delivery.md)
- [怎样设计一个可持久查询的账户报表？](architecture/system-design-fundamentals.md)
- [报表任务的发布确认、消费者确认与业务完成各证明什么？](reliability/queue-delivery-and-acknowledgement.md)
- [怎样用 Kafka 分区保序、推进偏移并安全接手？](reliability/kafka-partitions-and-offsets.md)
- [何时选择轮询、SSE、流式 Fetch 或 WebSocket？](networking/real-time-web-updates.md)

### 运行时如何承接与限制工作

- [何时选线程、进程或异步 I/O？](operating-systems/processes-threads-and-concurrency.md)
- [Node.js 如何在事件循环、工作线程与进程之间调度工作？](backend/node-js-fundamentals.md)
- [Node.js 事件循环阶段与微任务队列如何交互？](backend/node-event-loop-and-microtasks.md)
- [Node.js 流如何传播背压？](backend/node-stream-backpressure-and-cleanup.md)
- [Node.js 服务如何排空并关闭？](backend/node-service-shutdown.md)
- [Python 的值、迭代器与资源生命周期如何工作？](backend/python-fundamentals.md)
- [Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？](backend/python-attribute-lookup-and-mro.md)
- [异步 FastAPI 接口为什么仍会阻塞？](backend/python-async-and-fastapi.md)
- [如何估算并限制异步工作管线？](reliability/api-capacity-and-backpressure.md)
- [Web 服务如何限制拒绝服务的影响？](security/web-availability-and-ddos.md)

### 从回归证据到部署与事故诊断

- [怎样用最小反例定位报表授权回归？](architecture/reading-debugging-and-reviewing-code.md)
- [怎样用测试边界验证一次报表服务改动？](testing/software-testing-strategy.md)
- [Git 怎样把通过验收的报表改动变成可追溯提交？](version-control/git-essentials.md)
- [Docker 如何把报表服务的源码构建成可运行镜像？](infrastructure/docker-operations.md)
- [报表 API 与异步 worker 应由什么运行时承接？](infrastructure/production-application-runtime.md)
- [如何晋级并回滚已验证的报表服务产物？](infrastructure/application-deployment-and-ci-cd.md)
- [怎样从报表服务信号定位发布后的故障？](reliability/observability-slos-and-incident-response.md)

### 数据访问的操作量与硬件成本

- [怎样根据输入约束和访问模式选择算法？](algorithms/algorithms-and-complexity.md)
- [数据结构如何匹配访问方式，复杂度界何时成立？](algorithms/core-data-structures.md)
- [队列和栈怎样表示待处理工作？](algorithms/queue-and-stack-representations.md)
- [最近最少使用缓存怎样按键查找并更新最近使用顺序？](algorithms/practical-data-structure-implementations.md)
- [有序数据怎样让二分查找和双指针安全排除候选？](algorithms/ordered-array-search.md)
- [怎样在边界前进时维护一个有效窗口或活动区间？](algorithms/range-scans-and-active-sets.md)
- [怎样在不断加入任务时持续取出最高优先级？](algorithms/heaps-and-priority-queues.md)
- [搜索状态图时，何时永久标记节点，何时必须回退？](algorithms/graph-search-and-backtracking.md)
- [动态规划如何定义状态并安排更新顺序？](algorithms/dynamic-programming-state-and-order.md)
- [分区如何改变快速排序的时间和空间代价？](algorithms/partitioning-and-sorting-costs.md)
- [文本算法应按码元、码点还是字素簇处理？](algorithms/text-units-and-algorithms.md)
- [为什么连续扫描往往比链表遍历快？](operating-systems/memory-hierarchy-and-data-locality.md)
- [Linux 内核为什么把链表节点嵌入对象？](operating-systems/intrusive-lists-in-linux.md)

### 变化、职责与协作

- [如何让设计原则减少真实的修改成本？](architecture/software-design-principles.md)
- [前端架构怎样划分呈现、交互和数据所有权？](architecture/frontend-architecture-boundaries.md)
- [页面编辑器何时需要设计模式？](architecture/design-patterns-in-practice.md)
- [怎样建模页面文档、编辑会话和发布快照？](architecture/low-code-editor-data-model.md)
- [Scrum 怎样让团队检查并调整工作？](teamwork/agile-and-scrum.md)
- [怎样准备有事实支撑的行为面试回答？](career/interview-preparation.md)

## 相关领域

这些基础主题也支撑 [AI 应用架构](../ai-engineering/systems/ai-application-architecture.md) 和 [浏览器基础](../frontend/browser/browser-basics.md) 中的系统与客户端实践。
