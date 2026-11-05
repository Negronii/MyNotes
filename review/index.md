# Knowledge Navigator / 知识导航

Choose the question closest to what you want to understand. Each route starts with a concrete problem and links to the mechanisms it uses. The domain maps provide complete reading orders.

从你想弄懂的问题进入。每条路线从一个具体场景开始，沿途链接用到的原理。需要系统通读时，进入对应的领域地图。

## How does an interaction update the screen? / 一次操作怎样变成界面更新？

1. [What happens to the view when input and results update at different speeds? / 输入和结果更新速度不同时，界面怎样处理？](../frontend/frameworks/advanced-react.md) — Start with the task search and separate input state from result rendering.
2. [When does JavaScript get a turn to handle the event? / JavaScript 什么时候处理这个事件？](../frontend/runtime/event-loop.md) — Connect the handler, queued work, and the browser's opportunity to render.
3. [How does React turn state into a committed update? / React 怎样把状态变成提交的界面更新？](../frontend/frameworks/react-basics.md) — Follow state, rendering, and the DOM changes that reach the browser.
4. [How does the browser turn a document into pixels? / 浏览器怎样把文档变成像素？](../frontend/browser/browser-basics.md) — Follow the rendering work shared by the first view and later updates.

## How do you confirm an operation's result? / 怎样确认一次跨系统操作的结果？

1. [How do you confirm the outcome after a timeout or disconnect? / 超时或断线后，怎样确认结果？](../engineering-foundations/reliability/api-reliability-and-async-delivery.md) — Identify what the caller can observe and what evidence it needs to retry safely.
2. [What makes an account report a durable job? / 账户报表怎样成为一个可恢复的任务？](../engineering-foundations/architecture/system-design-fundamentals.md) — Follow acceptance, persistence, and the worker's final result in a concrete design.
3. [How can an AI run survive a disconnection? / AI 运行怎样在断线后继续或恢复？](../ai-engineering/systems/ai-application-architecture.md) — Connect model calls and tool actions to the service's run state.
4. [How does a streaming interface show the right state? / 流式界面怎样准确展示任务状态？](../frontend/browser-apis/streaming-ux.md) — Follow incremental events, local cancellation, and the server's terminal outcome.

For a short request, start with [what the API promises / API 对调用者作什么承诺](../engineering-foundations/backend/http-api-contracts.md), then follow its [data access / 数据访问](../engineering-foundations/backend/data-access-and-connection-pools.md) or [cache / 缓存](../engineering-foundations/backend/caching-and-redis.md). For connection and transfer behavior, see [how HTTP and streaming transports work / HTTP 与流式传输怎样工作](../engineering-foundations/networking/http-protocols-and-websockets.md).

## What evidence makes a change safe to ship? / 怎样证明一次改动可以上线？

1. [How do you find the smallest example that exposes the bug? / 怎样找到暴露问题的最小反例？](../engineering-foundations/architecture/reading-debugging-and-reviewing-code.md) — Start with the cross-tenant lookup case and state the behavior that should hold.
2. [Which test boundary can prove that behavior? / 应在哪一层测试才能证明这个行为？](../engineering-foundations/testing/software-testing-strategy.md) — Choose evidence for the actual risk. [Frontend testing / 前端测试](../frontend/testing/frontend-testing.md) covers user-visible behavior and the built output.
3. [How do you take the verified artifact to production? / 怎样把验证过的产物发布到生产？](../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) — Follow artifact promotion, compatibility, and rollout decisions.
4. [Which signals tell you how production is behaving? / 哪些信号能说明生产实际表现？](../engineering-foundations/reliability/observability-slos-and-incident-response.md) — Connect user-facing objectives with diagnosis and response.

For a model, prompt, or agent change, establish the baseline and compare outcomes using [LLM evaluation / 大语言模型评估](../ai-engineering/evaluation/llm-evaluation-methods.md).

## How can a model answer from evidence and take action? / 模型怎样凭证据回答和采取行动？

1. [How does a language model generate text? / 语言模型怎样生成文本？](../ai-engineering/foundations/how-llms-work.md) — Start here for the generation mechanism, or enter at the application question below.
2. [What information should reach the model for this task? / 这项任务应该把哪些信息交给模型？](../ai-engineering/context/context-engineering-principles.md) — Decide what to keep, load, and retrieve. Follow [RAG / 检索增强生成](../ai-engineering/rag/rag-architecture-and-implementation.md) for retrieval and evidence.
3. [How does an agent decide and act? / Agent 怎样决定下一步并采取行动？](../ai-engineering/agents/agent-fundamentals.md) — Follow the loop, then read [tool design / 工具设计](../ai-engineering/agents/tool-design-and-function-calling.md) and [production safety / 生产安全](../ai-engineering/safety/ai-safety-in-production.md) for the action boundary.
4. [How do you tell whether a change helped? / 怎样判断改动有效？](../ai-engineering/evaluation/llm-evaluation-methods.md) — Choose the tasks, scoring rules, and acceptance evidence before comparing behavior.

## Where does the cost of accessing data come from? / 访问数据的成本从哪来？

1. [What does algorithmic complexity predict? / 算法复杂度能预测什么？](../engineering-foundations/algorithms/algorithms-and-complexity.md) — Use input size and access patterns to reason about the work.
2. [Why can arrays and linked lists take different time? / 数组和链表的实际耗时为什么可能不同？](../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md) — Connect the access pattern to representation and memory locality.
3. [How do you choose a data structure? / 怎样选数据结构？](../engineering-foundations/algorithms/core-data-structures.md) — Match the workload to the structure and its costs.
4. [What makes a database query cheap or expensive? / 什么决定数据库查询的成本？](../engineering-foundations/databases/database-fundamentals.md) — Follow the query and its access path. The [database course map / 数据库课程地图](../archive/uni-subjects/COMP90050ADBS/readme.md) leads to worked examples of joins, indexes, isolation, and recovery.

## Read a domain or find a reference / 通读领域或查找资料

| Domain / 领域 | Reading order / 阅读顺序 | Continuous reading / 连续阅读稿 |
| --- | --- | --- |
| AI engineering / AI 工程 | [Domain map / 领域地图](../ai-engineering/index.md) | [Reading document / 连续阅读稿](generated/ai-engineering.md) |
| Frontend / 前端 | [Domain map / 领域地图](../frontend/index.md) | [Reading document / 连续阅读稿](generated/frontend.md) |
| Engineering foundations / 工程基础 | [Domain map / 领域地图](../engineering-foundations/index.md) | [Reading document / 连续阅读稿](generated/engineering-foundations.md) |

- [Reading progress / 本轮复习进度](reading-progress.md) records the notes read in this pass.
- [AI literature / AI 论文与文章](ai-literature-index.md) links sources to the questions they inform.
- [Archive / 归档](../archive/index.md) leads to course exercises, original materials, and specialized references.
