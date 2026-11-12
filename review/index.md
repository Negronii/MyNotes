# 知识导航

先从一个完整问题进入，读完主线再展开感兴趣的机制。下方路线连接同一过程中的不同章节；领域地图提供完整阅读顺序，连续阅读稿适合一口气读下去。

## 从领域开始

| 领域 | 主线与完整顺序 | 连续阅读 |
| --- | --- | --- |
| AI 工程 | [AI 工程地图](../ai-engineering/index.md) | [AI 工程连续阅读稿](generated/ai-engineering.md) |
| 前端 | [前端地图](../frontend/index.md) | [前端连续阅读稿](generated/frontend.md) |
| 工程基础 | [工程基础地图](../engineering-foundations/index.md) | [工程基础连续阅读稿](generated/engineering-foundations.md) |

## 一次操作怎样变成界面更新？

[报表页首次出现](../frontend/browser/browser-basics.md)之后，用户点击筛选条件。先跟着原生 JavaScript 实现理解事件与调度，再把相同的筛选意图放进 React 实现，看两种方式的 DOM 改动怎样得到下一帧。

1. [点击先交给谁，事件怎样传播？](../frontend/browser-apis/dom-manipulation-and-events.md)点击进入事件分发路径，轮到该任务执行时才调用处理器。
2. [JavaScript 什么时候处理事件？](../frontend/runtime/event-loop.md)回调、microtask 和浏览器渲染机会相互交错。
3. [React 怎样把状态变成界面更新？](../frontend/frameworks/react-basics.md)这里切换到 React 实现：处理器将相同的 `oldest` 筛选意图交给 state，React 计算视图并提交必要的 DOM 改动。原生实现与 React 实现是两条替代路径。计算结果很贵时，再看[怎样让输入保持响应](../frontend/frameworks/advanced-react.md)。
4. [DOM 改动怎样变成像素？](../frontend/html-css/rendering-pipeline-and-forced-layout.md)浏览器按改动的依赖关系完成样式、布局、绘制和合成。
5. [如果这一帧迟到了，怎样定位原因？](../frontend/performance/performance-metrics-and-analysis.md)用同一次交互的时间线区分输入等待、执行和呈现成本。

## 怎样确认一次跨系统操作的结果？

1. [请求超时后，怎样确认结果并重试？](../engineering-foundations/reliability/api-reliability-and-async-delivery.md)先明确调用者看到了什么，以及服务端可能已经完成了什么。
2. [账户报表怎样成为可恢复的任务？](../engineering-foundations/architecture/system-design-fundamentals.md)沿受理、持久化和 worker 的最终结果建立查询依据，再看[队列确认到底证明了什么](../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md)。
3. [AI 运行怎样在断线后继续或恢复？](../ai-engineering/systems/ai-application-architecture.md)将模型调用、工具动作连接到服务保存的运行状态。
4. [流式界面怎样准确展示任务状态？](../frontend/browser-apis/streaming-ux.md)界面收到部分内容或本地取消后，仍需区分连接状态与服务端任务终态。

短请求可以从 [API 的承诺](../engineering-foundations/backend/http-api-contracts.md)进入，继续看[数据访问](../engineering-foundations/backend/data-access-and-connection-pools.md)或[缓存新鲜度](../engineering-foundations/backend/caching-and-redis.md)。单次交换由 [HTTP](../engineering-foundations/networking/http-protocols-and-websockets.md)承载；持续更新再比较[轮询、SSE 与 WebSocket](../engineering-foundations/networking/real-time-web-updates.md)。

## 怎样证明一次改动可以上线？

1. [怎样找到暴露问题的最小反例？](../engineering-foundations/architecture/reading-debugging-and-reviewing-code.md)从跨租户查询的失败例子确定应该成立的行为。
2. [在哪一层测试才能证明这个行为？](../engineering-foundations/testing/software-testing-strategy.md)按真实风险选择证据；[前端测试](../frontend/testing/frontend-testing.md)还要覆盖用户行为和构建产物。
3. [怎样把验证过的产物发布到生产？](../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)跟随同一产物的晋级、兼容性检查和发布决策。
4. [生产中的哪些信号能发现退化？](../engineering-foundations/reliability/observability-slos-and-incident-response.md)用面向用户的目标连接监测、定位和恢复。

模型、提示词或 Agent 的改动还需要[独立的任务评估](../ai-engineering/evaluation/llm-evaluation-methods.md)：训练奖励或一次成功演示不能代替发布证据。

若评估发现了稳定的模型行为差距，先看[训练怎样把 loss 变成每个权重的更新](../ai-engineering/foundations/training-gradients-and-optimizers.md)，再判断[是否应该微调、更新哪些参数](../ai-engineering/fine-tuning/fine-tuning-strategies.md)。

## AI 应用怎样凭证据回答？

从[一条消息到完整回答](../ai-engineering/systems/from-message-to-answer.md)开始，沿构建 42 的失败问题，走完输入组装、模型推理、授权查询日志和解释结果。

- 想知道模型内部发生了什么，继续看[提示词怎样变成文本](../ai-engineering/foundations/how-llms-work.md)，再把中间状态连接到[KV cache 与服务容量](../ai-engineering/systems/llm-serving-and-kv-cache.md)。
- 问题需要先找到某份资料时，进入[文档更新、检索与证据核对](../ai-engineering/rag/rag-architecture-and-implementation.md)。[上下文组织](../ai-engineering/context/context-engineering-principles.md)解释每次推理该看到什么。
- 再次遇到相关问题时，看[什么时候值得把历史加工成记忆](../ai-engineering/context/agent-memory-design-and-evaluation.md)：先与原文检索比较，再检查加工后的信息损失、使用成本和独立任务结果。
- 一次工具调用不足以完成目标时，看[如何组织多阶段任务](../ai-engineering/agents/orchestration-patterns.md)和[如何验证并保留改进](../ai-engineering/agents/agent-improvement-and-version-acceptance.md)。

## 访问数据的成本从哪来？

1. [算法复杂度能预测什么？](../engineering-foundations/algorithms/algorithms-and-complexity.md)先固定输入大小、允许操作和访问模式。
2. [数组与链表的实际耗时为什么不同？](../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md)把操作量连接到内存表示、局部性和等待。
3. [怎样按工作负载选择数据结构？](../engineering-foundations/algorithms/core-data-structures.md)比较需要支持的操作及其成本条件。
4. [索引怎样改变数据库的访问路径？](../engineering-foundations/databases/database-constraints-and-indexes.md)从查询条件追到数据库页。需要演算连接代价、隔离或恢复时，进入[数据库课程地图](../archive/uni-subjects/COMP90050ADBS/readme.md)；[事务与恢复](../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)连接这些机制和持久提交。

## 按机制查找

已经知道想查的概念时，可以直接进入下面的解释；完整学习顺序仍由各领域地图维护。

| 想查的机制 | 正文入口 |
|---|---|
| MCP、用户委托与本地工具执行 | [MCP 连接与鉴权](../ai-engineering/agents/mcp-tool-connections.md)、[OAuth 委托执行](../ai-engineering/agents/delegated-oauth-for-agent-tools.md)、[coding harness](../ai-engineering/agents/coding-agent-harness.md) |
| LangGraph、重规划与记忆 | [运行恢复](../ai-engineering/systems/ai-application-architecture.md)、[编排与循环诊断](../ai-engineering/agents/orchestration-patterns.md)、[上下文与跨运行记忆](../ai-engineering/context/context-engineering-principles.md)、[记忆加工的净收益](../ai-engineering/context/agent-memory-design-and-evaluation.md) |
| 模型配额、缓存与向量索引 | [有界模型调用](../ai-engineering/systems/bounded-model-api-calls.md)、[缓存命中与成本](../ai-engineering/systems/ai-latency-and-cost-optimization.md)、[HNSW](../ai-engineering/rag/hnsw-vector-index-search.md) |
| debounce、throttle、Promise 与结构相等 | [闭包调度](../frontend/javascript/scope-and-closure.md#定时回调怎样用闭包保留调度状态)、[Promise 组合](../frontend/javascript/asynchronous-javascript.md)、[并发池](../frontend/javascript/bounded-async-concurrency.md)、[值与结构比较](../frontend/javascript/javascript-types.md) |
| Context、编辑草稿与聊天状态 | [组件中的状态所有者](../frontend/frameworks/react-component-composition.md)、[表格与表单](../frontend/frameworks/management-table-and-form-workflows.md)、[流式聊天](../frontend/browser-apis/streaming-ai-chat.md) |
| 条件写、回调与持久队列 | [HTTP 更新契约](../engineering-foundations/backend/http-api-contracts.md)、[Webhook](../engineering-foundations/reliability/webhook-delivery-and-verification.md)、[任务领取与确认](../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md)、[Kafka offset](../engineering-foundations/reliability/kafka-partitions-and-offsets.md) |
| 类型、构建产物与渐进迁移 | [运行时 schema](../frontend/typescript/advanced-typescript.md#怎样用%20Zod%20在同一个输入边界生成运行时检查和静态类型？)、[静态资源版本](../frontend/tooling/build-tools.md#新入口与带哈希代码分块怎样作为同一版本发布？)、[微前端迁移](../engineering-foundations/architecture/frontend-architecture-boundaries.md#怎样迁移微前端而不打断深链、身份与回退？) |
| 数据分布与存储引擎 | [分片与搬迁](../engineering-foundations/databases/database-sharding-and-rebalancing.md)、[InnoDB 索引、锁与恢复](../engineering-foundations/databases/mysql-innodb-index-lock-and-recovery.md) |
| Python 属性解析 | [descriptor、方法绑定与 MRO](../engineering-foundations/backend/python-attribute-lookup-and-mro.md) |
| 部署身份与密钥 | [凭据的注入、轮换与撤销](../engineering-foundations/infrastructure/production-application-runtime.md#worker%20凭据怎样注入、轮换并撤销？) |
| 窗口、优先级与搜索路径 | [窗口与区间扫描](../engineering-foundations/algorithms/range-scans-and-active-sets.md)、[堆](../engineering-foundations/algorithms/heaps-and-priority-queues.md)、[图搜索与回溯](../engineering-foundations/algorithms/graph-search-and-backtracking.md)、[文本单位与 Trie](../engineering-foundations/algorithms/text-units-and-algorithms.md) |

## 阅读记录与资料

- [本轮阅读进度](reading-progress.md)只记录本轮读过哪些正文。
- [AI 好文集](ai-literature-index.md)按问题收集来源及其知识落点。
- [归档](../archive/index.md)保留课程推导、作者解法、原始材料和专门参考。
