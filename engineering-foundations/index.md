# Engineering Foundations / 工程基础

Start with the costs of representing and accessing data. Then follow work across runtimes, databases, and service boundaries before deciding how to design, test, and deliver a change. / 先理解数据表示与访问的成本，再看任务如何经过运行时、数据库和服务边界，最后把这些原理用到设计、测试和交付。

## Reading order / 阅读顺序

### Algorithms and data structures / 算法与数据结构

- [How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？](algorithms/algorithms-and-complexity.md)
- [How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？](algorithms/dynamic-programming-state-and-order.md)
- [How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？](algorithms/ordered-array-search.md)
- [Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？](algorithms/partitioning-and-sorting-costs.md)
- [Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？](algorithms/text-units-and-algorithms.md)
- [Which data structure fits the access pattern, and when do its cost bounds hold? / 哪种数据结构适合当前访问模式，复杂度界何时成立？](algorithms/core-data-structures.md)
- [How can an LRU cache find an entry and update recency efficiently? / LRU 缓存怎样高效找到条目并更新使用顺序？](algorithms/practical-data-structure-implementations.md)
- [How do FIFO and LIFO change the representation of pending work? / FIFO 与 LIFO 怎样影响待处理工作的表示？](algorithms/queue-and-stack-representations.md)

### Operating systems / 操作系统

- [When should work use a thread, process, or asynchronous I/O? / 何时选线程、进程或异步 I/O？](operating-systems/processes-threads-and-concurrency.md)
- [Why are contiguous scans often faster than linked-list walks? / 为什么连续扫描往往比链表遍历快？](operating-systems/memory-hierarchy-and-data-locality.md)
- [Why does the Linux kernel embed list nodes in their objects? / Linux 内核为什么把链表节点嵌入对象？](operating-systems/intrusive-lists-in-linux.md)

### Databases / 数据库

- [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](databases/database-fundamentals.md)
- [How do NULLs, joins, and grouping change SQL results? / NULL、连接与分组会怎样改变 SQL 查询结果？](databases/sql-null-joins-and-aggregates.md)
- [How do database constraints and indexes shape data access? / 数据库约束和索引如何塑造数据访问？](databases/database-constraints-and-indexes.md)
- [What do transaction isolation and WAL guarantee? / 事务隔离与 WAL 分别保证什么？](databases/database-transactions-isolation-and-recovery.md)

### Networking / 网络

- [How does a browser request reach an HTTP response? / 浏览器请求如何到达 HTTP 响应？](networking/http-protocols-and-websockets.md)
- [When should a browser use polling, SSE, streaming Fetch, or WebSocket? / 何时选轮询、SSE、流式 Fetch 或 WebSocket？](networking/real-time-web-updates.md)

### Backend and runtime / 后端与运行时

- [How does Node.js schedule work across its event loop, workers, and processes? / Node.js 如何在事件循环、工作线程与进程之间调度工作？](backend/node-js-fundamentals.md)
- [How do Node.js event-loop phases and microtask queues interact? / Node.js 事件循环阶段与微任务队列如何交互？](backend/node-event-loop-and-microtasks.md)
- [How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？](backend/node-stream-backpressure-and-cleanup.md)
- [How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？](backend/node-service-shutdown.md)
- [What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？](backend/serverless-runtime-boundaries.md)
- [How do Python values, iterators, and resource lifetimes behave? / Python 的值、迭代器与资源生命周期如何工作？](backend/python-fundamentals.md)
- [Why can an async FastAPI endpoint still block? / 为什么异步 FastAPI 接口仍会阻塞？](backend/python-async-and-fastapi.md)
- [How long should a FastAPI dependency stay open during a response? / FastAPI 依赖应在响应期间保持多久？](backend/python-fastapi-resource-lifetimes.md)
- [How do you design a predictable HTTP API contract? / 如何设计可预期的 HTTP API 契约？](backend/http-api-contracts.md)
- [How does cursor pagination continue safely? / 游标分页如何安全续读？](backend/api-cursor-pagination.md)
- [How do you scope an ORM Session and diagnose pool exhaustion? / 如何限定 ORM Session 作用域并诊断连接池耗尽？](backend/data-access-and-connection-pools.md)
- [How do you cache database reads without losing freshness? / 如何缓存数据库读取并控制数据新鲜度？](backend/caching-and-redis.md)

### Security / 安全

- [How do you prevent cross-tenant access across a web request? / 如何防止 Web 请求跨租户访问？](security/web-security-and-authentication.md)
- [How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？](security/web-sessions-and-oidc.md)
- [Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？](security/web-browser-security-boundaries.md)
- [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](security/web-availability-and-ddos.md)
- [How do parameterized queries prevent SQL injection? / 参数化查询如何防止 SQL 注入？](security/sql-injection-prevention.md)
- [How should passwords be stored against offline guessing? / 如何存储密码以抵抗离线猜测？](security/password-storage.md)

### Reliability and asynchronous delivery / 可靠性与异步交付

- [A request timed out: how can I confirm its outcome and retry safely? / 请求超时后，如何确认操作结果并安全重试？](reliability/api-reliability-and-async-delivery.md)
- [How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？](reliability/api-capacity-and-backpressure.md)
- [What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？](reliability/queue-delivery-and-acknowledgement.md)
- [How do you diagnose an API SLO violation? / 如何诊断 API SLO 违约？](reliability/observability-slos-and-incident-response.md)

### Architecture / 架构

- [How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？](architecture/software-design-principles.md)
- [How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？](architecture/frontend-architecture-boundaries.md)
- [When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？](architecture/design-patterns-in-practice.md)
- [How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？](architecture/low-code-editor-data-model.md)
- [How should roles control access to a feature? / 角色怎样控制对功能的访问？](architecture/role-based-access-design.md)
- [How can a minimal counterexample trace a regression to its root cause? / 如何用最小反例沿调用路径定位回归根因？](architecture/reading-debugging-and-reviewing-code.md)
- [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](architecture/system-design-fundamentals.md)

### Testing / 测试

- [How should test boundaries prove the failure risks that matter? / 如何选择测试边界来证明关键故障风险？](testing/software-testing-strategy.md)

### Version control / 版本控制

- [How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？](version-control/git-essentials.md)
- [How do you undo or recover a Git change safely? / 怎样安全撤销或找回 Git 改动？](version-control/git-undo-and-recovery.md)

### Infrastructure / 基础设施

- [How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？](infrastructure/docker-operations.md)
- [How do you promote one validated artifact and recover each state layer safely? / 如何晋级已验证产物并分别恢复各层状态？](infrastructure/application-deployment-and-ci-cd.md)
- [How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？](infrastructure/production-application-runtime.md)

### Teamwork / 团队协作

- [How does Scrum help a team inspect and adapt work? / Scrum 如何帮助团队检查并调整工作？](teamwork/agile-and-scrum.md)

### Career / 职业发展

- [How do you prepare behavioral answers with evidence you can support? / 如何准备有事实依据、经得起核实的行为面试回答？](career/interview-preparation.md)

## Related domains / 相关领域

这些基础主题也支撑 [AI 应用架构](../ai-engineering/systems/ai-application-architecture.md) 和 [浏览器基础](../frontend/browser/browser-basics.md) 中的系统与客户端实践。
