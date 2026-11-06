# 工程基础

先从最后一件库存的预留看请求怎样变成可靠的数据提交，再追问超时之后如何确认结果。账户报表的异步作业把队列、运行时容量、部署和故障诊断连起来；算法与内存布局则解释这些系统背后的访问成本。

## 从问题开始

- [两个请求抢最后一件库存，谁能成功？](databases/database-fundamentals.md)——建议先读，从库存约束走到事务提交。
- [预留库存的请求超时，调用方能重试吗？](reliability/api-reliability-and-async-delivery.md)——沿请求标识确认结果并安全重试。
- [哪一段导致 API 未达到服务目标？](reliability/observability-slos-and-incident-response.md)——先用指标、追踪和日志定位环节，再决定改哪里。

## Reading order / 阅读顺序

### 从请求到受约束的数据提交

- [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](databases/database-fundamentals.md)
- [How does a browser request reach an HTTP response? / 浏览器请求如何到达 HTTP 响应？](networking/http-protocols-and-websockets.md)
- [How do you design a predictable HTTP API contract? / 如何设计可预期的 HTTP API 契约？](backend/http-api-contracts.md)
- [How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？](security/web-sessions-and-oidc.md)
- [How do you prevent cross-tenant access across a web request? / 如何防止 Web 请求跨租户访问？](security/web-security-and-authentication.md)
- [Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？](security/web-browser-security-boundaries.md)
- [How do NULLs, joins, and grouping change SQL results? / NULL、连接与分组会怎样改变 SQL 查询结果？](databases/sql-null-joins-and-aggregates.md)
- [How do database constraints and indexes shape data access? / 数据库约束和索引如何塑造数据访问？](databases/database-constraints-and-indexes.md)
- [What do transaction isolation and WAL guarantee? / 事务隔离与 WAL 分别保证什么？](databases/database-transactions-isolation-and-recovery.md)
- [How do you scope an ORM Session and diagnose pool exhaustion? / 如何限定 ORM Session 作用域并诊断连接池耗尽？](backend/data-access-and-connection-pools.md)
- [How do you cache database reads without losing freshness? / 如何缓存数据库读取并控制数据新鲜度？](backend/caching-and-redis.md)

### 超时之后：确认结果与恢复任务

- [A request timed out: how can I confirm its outcome and retry safely? / 请求超时后，如何确认操作结果并安全重试？](reliability/api-reliability-and-async-delivery.md)
- [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](architecture/system-design-fundamentals.md)
- [What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？](reliability/queue-delivery-and-acknowledgement.md)
- [When should a browser use polling, SSE, streaming Fetch, or WebSocket? / 何时选轮询、SSE、流式 Fetch 或 WebSocket？](networking/real-time-web-updates.md)

### 运行时如何承接与限制工作

- [When should work use a thread, process, or asynchronous I/O? / 何时选线程、进程或异步 I/O？](operating-systems/processes-threads-and-concurrency.md)
- [How does Node.js schedule work across its event loop, workers, and processes? / Node.js 如何在事件循环、工作线程与进程之间调度工作？](backend/node-js-fundamentals.md)
- [How do Node.js event-loop phases and microtask queues interact? / Node.js 事件循环阶段与微任务队列如何交互？](backend/node-event-loop-and-microtasks.md)
- [How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？](backend/node-stream-backpressure-and-cleanup.md)
- [How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？](backend/node-service-shutdown.md)
- [How do Python values, iterators, and resource lifetimes behave? / Python 的值、迭代器与资源生命周期如何工作？](backend/python-fundamentals.md)
- [Why can an async FastAPI endpoint still block? / 为什么异步 FastAPI 接口仍会阻塞？](backend/python-async-and-fastapi.md)
- [How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？](reliability/api-capacity-and-backpressure.md)
- [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](security/web-availability-and-ddos.md)

### 从回归证据到部署与事故诊断

- [How can a minimal counterexample trace a regression to its root cause? / 如何用最小反例沿调用路径定位回归根因？](architecture/reading-debugging-and-reviewing-code.md)
- [How should test boundaries prove the failure risks that matter? / 如何选择测试边界来证明关键故障风险？](testing/software-testing-strategy.md)
- [How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？](version-control/git-essentials.md)
- [How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？](infrastructure/docker-operations.md)
- [How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？](infrastructure/production-application-runtime.md)
- [How do you promote one validated artifact and recover each state layer safely? / 如何晋级已验证产物并分别恢复各层状态？](infrastructure/application-deployment-and-ci-cd.md)
- [How do you diagnose an API SLO violation? / 如何诊断 API SLO 违约？](reliability/observability-slos-and-incident-response.md)

### 数据访问的操作量与硬件成本

- [How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？](algorithms/algorithms-and-complexity.md)
- [Which data structure fits the access pattern, and when do its cost bounds hold? / 哪种数据结构适合当前访问模式，复杂度界何时成立？](algorithms/core-data-structures.md)
- [How do FIFO and LIFO change the representation of pending work? / FIFO 与 LIFO 怎样影响待处理工作的表示？](algorithms/queue-and-stack-representations.md)
- [How can an LRU cache find an entry and update recency efficiently? / LRU 缓存怎样高效找到条目并更新使用顺序？](algorithms/practical-data-structure-implementations.md)
- [How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？](algorithms/ordered-array-search.md)
- [How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？](algorithms/dynamic-programming-state-and-order.md)
- [Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？](algorithms/partitioning-and-sorting-costs.md)
- [Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？](algorithms/text-units-and-algorithms.md)
- [Why are contiguous scans often faster than linked-list walks? / 为什么连续扫描往往比链表遍历快？](operating-systems/memory-hierarchy-and-data-locality.md)
- [Why does the Linux kernel embed list nodes in their objects? / Linux 内核为什么把链表节点嵌入对象？](operating-systems/intrusive-lists-in-linux.md)

### 变化、职责与协作

- [How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？](architecture/software-design-principles.md)
- [How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？](architecture/frontend-architecture-boundaries.md)
- [When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？](architecture/design-patterns-in-practice.md)
- [How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？](architecture/low-code-editor-data-model.md)
- [How does Scrum help a team inspect and adapt work? / Scrum 如何帮助团队检查并调整工作？](teamwork/agile-and-scrum.md)
- [How do you prepare behavioral answers with evidence you can support? / 如何准备有事实依据、经得起核实的行为面试回答？](career/interview-preparation.md)

## 相关领域

这些基础主题也支撑 [AI 应用架构](../ai-engineering/systems/ai-application-architecture.md) 和 [浏览器基础](../frontend/browser/browser-basics.md) 中的系统与客户端实践。
