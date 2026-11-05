# Engineering Foundations / 工程基础

This map gathers shared engineering topics, backend runtime basics, and reusable architecture and team practices.

## Reading order / 阅读顺序

### Networking / 网络

- [HTTP Protocols and WebSockets / HTTP协议与WebSocket](networking/http-protocols-and-websockets.md)

### Operating systems / 操作系统

- [Processes, Threads, and Concurrency / 进程、线程与并发](operating-systems/processes-threads-and-concurrency.md)
- [Memory Hierarchy and Data Locality / 内存层次与数据局部性](operating-systems/memory-hierarchy-and-data-locality.md)

### Databases / 数据库

- [Database Fundamentals / 数据库基础](databases/database-fundamentals.md)

### Reliability and asynchronous delivery / 可靠性与异步交付

- [A request timed out: how can I confirm its outcome and retry safely? / 请求超时后，如何确认操作结果并安全重试？](reliability/api-reliability-and-async-delivery.md)
- [How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？](reliability/api-capacity-and-backpressure.md)
- [What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？](reliability/queue-delivery-and-acknowledgement.md)
- [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](reliability/observability-slos-and-incident-response.md)

### Security / 安全

- [Web Security and Authentication / Web安全与身份认证](security/web-security-and-authentication.md)

### Testing / 测试

- [How should test boundaries prove the failure risks that matter? / 如何选择测试边界来证明关键故障风险？](testing/software-testing-strategy.md)

### Algorithms and data structures / 算法与数据结构

- [How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？](algorithms/algorithms-and-complexity.md)
- [How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？](algorithms/dynamic-programming-state-and-order.md)
- [How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？](algorithms/ordered-array-search.md)
- [Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？](algorithms/partitioning-and-sorting-costs.md)
- [Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？](algorithms/text-units-and-algorithms.md)
- [Which data structure fits the access pattern, and when do its cost bounds hold? / 哪种数据结构适合当前访问模式，复杂度界何时成立？](algorithms/core-data-structures.md)
- [How can an LRU cache find an entry and update recency efficiently? / LRU 缓存怎样高效找到条目并更新使用顺序？](algorithms/practical-data-structure-implementations.md)
- [How do FIFO and LIFO change the representation of pending work? / FIFO 与 LIFO 怎样影响待处理工作的表示？](algorithms/queue-and-stack-representations.md)

### Backend and runtime / 后端与运行时

- [Node.js Fundamentals / Node.js基础](backend/node-js-fundamentals.md)
- [Python Fundamentals / Python基础](backend/python-fundamentals.md)
- [Python Async and FastAPI Request Lifecycle / Python异步与FastAPI请求生命周期](backend/python-async-and-fastapi.md)
- [HTTP API Contracts / HTTP API契约](backend/http-api-contracts.md)
- [Data Access and Connection Pools / 数据访问与连接池](backend/data-access-and-connection-pools.md)
- [Caching and Redis / 缓存与 Redis](backend/caching-and-redis.md)

### Architecture / 架构

- [How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？](architecture/software-design-principles.md)
- [How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？](architecture/frontend-architecture-boundaries.md)
- [When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？](architecture/design-patterns-in-practice.md)
- [How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？](architecture/low-code-editor-data-model.md)
- [How should roles control access to a feature? / 角色怎样控制对功能的访问？](architecture/role-based-access-design.md)
- [How can a minimal counterexample trace a regression to its root cause? / 如何用最小反例沿调用路径定位回归根因？](architecture/reading-debugging-and-reviewing-code.md)
- [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](architecture/system-design-fundamentals.md)

### Career / 职业发展

- [How do you prepare behavioral answers with evidence you can support? / 如何准备有事实依据、经得起核实的行为面试回答？](career/interview-preparation.md)

### Teamwork / 团队协作

- [How does Scrum help a team inspect and adapt work? / Scrum 如何帮助团队检查并调整工作？](teamwork/agile-and-scrum.md)

### Version control / 版本控制

- [How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？](version-control/git-essentials.md)
- [How do you undo or recover a Git change safely? / 怎样安全撤销或找回 Git 改动？](version-control/git-undo-and-recovery.md)

### Infrastructure / 基础设施

- [How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？](infrastructure/docker-operations.md)
- [How do you promote one validated artifact and recover each state layer safely? / 如何晋级已验证产物并分别恢复各层状态？](infrastructure/application-deployment-and-ci-cd.md)
- [How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？](infrastructure/production-application-runtime.md)

## Related domains / 相关领域

这些基础主题也支撑 [AI 应用架构](../ai-engineering/systems/ai-application-architecture.md) 和 [浏览器基础](../frontend/browser/browser-basics.md) 中的系统与客户端实践。
