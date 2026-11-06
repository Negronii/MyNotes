# Knowledge Navigator / 知识导航

Start with an end-to-end question in a domain map, or choose a route below that connects several chapters. The domain maps also provide complete reading orders.

可以从领域地图里选一个端到端问题，也可以选下方路线串读几篇笔记。领域地图还提供完整阅读顺序。

## Start in a domain / 从领域开始

| Domain / 领域 | Questions and reading order / 主线问题与阅读顺序 | Continuous reading / 连续阅读稿 |
| --- | --- | --- |
| AI engineering / AI 工程 | [Domain map / 领域地图](../ai-engineering/index.md) | [Reading document / 连续阅读稿](generated/ai-engineering.md) |
| Frontend / 前端 | [Domain map / 领域地图](../frontend/index.md) | [Reading document / 连续阅读稿](generated/frontend.md) |
| Engineering foundations / 工程基础 | [Domain map / 领域地图](../engineering-foundations/index.md) | [Reading document / 连续阅读稿](generated/engineering-foundations.md) |

## How does an interaction update the screen? / 一次操作怎样变成界面更新？

After the [reports page first appears / 报表页首次出现](../frontend/browser/browser-basics.md), suppose the user clicks a filter that changes the visible rows. Follow the click to the next frame. / 报表页出现后，沿一次筛选操作，看点击怎样改变下一帧里的列表。

1. [When does JavaScript get a turn to handle the event? / JavaScript 什么时候处理这个事件？](../frontend/runtime/event-loop.md) — The event handler reads the chosen filter and requests a state update.
2. [How does React turn state into a committed update? / React 怎样把状态变成提交的界面更新？](../frontend/frameworks/react-basics.md) — React computes the next view and commits any necessary DOM changes. When recalculating results is expensive, see [how a search interface stays responsive / 搜索界面如何保持响应](../frontend/frameworks/advanced-react.md).
3. [What browser work can an update trigger? / 一次更新会触发哪些浏览器工作？](../frontend/html-css/rendering-pipeline-and-forced-layout.md) — Follow the changed rows through the layout, paint, and compositing work they require.

## How do you confirm an operation's result? / 怎样确认一次跨系统操作的结果？

1. [How do you confirm the outcome after a timeout or disconnect? / 超时或断线后，怎样确认结果？](../engineering-foundations/reliability/api-reliability-and-async-delivery.md) — Identify what the caller can observe and what evidence it needs to retry safely.
2. [What makes an account report a durable job? / 账户报表怎样成为一个可恢复的任务？](../engineering-foundations/architecture/system-design-fundamentals.md) — Follow acceptance, persistence, and the worker's final result in a concrete design.
3. [How can an AI run survive a disconnection? / AI 运行怎样在断线后继续或恢复？](../ai-engineering/systems/ai-application-architecture.md) — Connect model calls and tool actions to the service's run state.
4. [How does a streaming interface show the right state? / 流式界面怎样准确展示任务状态？](../frontend/browser-apis/streaming-ux.md) — Follow incremental events, local cancellation, and the server's terminal outcome.

For a short request, start with [what the API promises / API 对调用者作什么承诺](../engineering-foundations/backend/http-api-contracts.md), then follow its [data access / 数据访问](../engineering-foundations/backend/data-access-and-connection-pools.md) or [cache / 缓存](../engineering-foundations/backend/caching-and-redis.md). Follow [how HTTP carries requests / HTTP 怎样传输请求](../engineering-foundations/networking/http-protocols-and-websockets.md) for a single exchange or [how to choose a real-time transport / 怎样选择实时传输](../engineering-foundations/networking/real-time-web-updates.md) for ongoing updates.

## What evidence makes a change safe to ship? / 怎样证明一次改动可以上线？

1. [How do you find the smallest example that exposes the bug? / 怎样找到暴露问题的最小反例？](../engineering-foundations/architecture/reading-debugging-and-reviewing-code.md) — Start with the cross-tenant lookup case and state the behavior that should hold.
2. [Which test boundary can prove that behavior? / 应在哪一层测试才能证明这个行为？](../engineering-foundations/testing/software-testing-strategy.md) — Choose evidence for the actual risk. [Frontend testing / 前端测试](../frontend/testing/frontend-testing.md) covers user-visible behavior and the built output.
3. [How do you take the verified artifact to production? / 怎样把验证过的产物发布到生产？](../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) — Follow artifact promotion, compatibility, and rollout decisions.
4. [Which signals tell you how production is behaving? / 哪些信号能说明生产实际表现？](../engineering-foundations/reliability/observability-slos-and-incident-response.md) — Connect user-facing objectives with diagnosis and response.

For a model, prompt, or agent change, establish the baseline and compare outcomes using [LLM evaluation / 大语言模型评估](../ai-engineering/evaluation/llm-evaluation-methods.md).

## How can an AI application answer from evidence? / AI 应用怎样凭证据回答？

Start with [one message to a complete answer](../ai-engineering/systems/from-message-to-answer.md). Follow a build-failure question through input assembly, model inference, an authorized log lookup, and the resulting explanation. If evidence must be found in a document collection, continue with [retrieval and grounding](../ai-engineering/rag/rag-architecture-and-implementation.md).

## Where does the cost of accessing data come from? / 访问数据的成本从哪来？

1. [What does algorithmic complexity predict? / 算法复杂度能预测什么？](../engineering-foundations/algorithms/algorithms-and-complexity.md) — Use input size and access patterns to reason about the work.
2. [Why can arrays and linked lists take different time? / 数组和链表的实际耗时为什么可能不同？](../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md) — Connect the access pattern to representation and memory locality.
3. [How do you choose a data structure? / 怎样选数据结构？](../engineering-foundations/algorithms/core-data-structures.md) — Match the workload to the structure and its costs.
4. [How do indexes change a query’s access cost? / 索引怎样改变查询的访问成本？](../engineering-foundations/databases/database-constraints-and-indexes.md) — Follow the query and its access path. The [database course map / 数据库课程地图](../archive/uni-subjects/COMP90050ADBS/readme.md) leads to worked examples of joins, indexes, isolation, and recovery. [Transactions and recovery / 事务与恢复](../engineering-foundations/databases/database-transactions-isolation-and-recovery.md) connects these mechanisms to durable work.

## References / 参考资料

- [Reading progress / 本轮复习进度](reading-progress.md) records the notes read in this pass.
- [AI literature / AI 论文与文章](ai-literature-index.md) links sources to the questions they inform.
- [Archive / 归档](../archive/index.md) leads to course exercises, original materials, and specialized references.
