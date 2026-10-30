# Knowledge Navigator / 知识导航

This map links to the canonical notes for learning and knowledge lookup across AI applications and agents, then frontend/full-stack foundations. Read the linked notes for the explanations; this page does not duplicate their answers.

## Reading progress / 本轮复习进度

Use [Reading progress / 本轮复习进度](reading-progress.md) to mark notes read during the current pass. Sync follows the domain reading maps and preserves checked paths when entries are added or reordered; `--status` reports counts after validating the list.

## AI applications and agents / AI 应用与 Agent

1. [Agent fundamentals / Agent 基础](../ai-engineering/agents/agent-fundamentals.md) — start with the agent loop, task feedback, and changes accepted for later runs.
2. [Orchestration patterns / 编排模式](../ai-engineering/agents/orchestration-patterns.md) — choose among a main loop, routing, parallel work, delegation, and ownership handoff.
3. [Tool design and function calling / 工具设计与函数调用](../ai-engineering/agents/tool-design-and-function-calling.md) — connect model decisions to safe, usable tools.
4. [Context engineering principles / 上下文工程原则](../ai-engineering/context/context-engineering-principles.md) — manage active context, persistent artifacts, selective reset, and just-in-time retrieval.
5. [Retrieval-Augmented Generation (RAG) / 检索增强生成](../ai-engineering/rag/rag-architecture-and-implementation.md) — follow how retrieval supplies evidence and where system boundaries affect answers.
6. [LLM Evaluation / 大语言模型评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md) — compare architectures and accepted versions with task-level evidence.
7. [AI Safety in Production / 生产环境 AI 安全](../ai-engineering/safety/ai-safety-in-production.md) — connect trust boundaries to runtime controls, stop paths, and testing.
8. [AI Application Architecture / AI 应用架构](../ai-engineering/systems/ai-application-architecture.md) — bring identity, context, tools, cost, observability, and recovery together around a production model call.

[AI Literature Index / AI 论文与文章索引](ai-literature-index.md) — 按来源查找论文与文章的核心贡献，以及它们融入的主题笔记。

## Frontend and full-stack foundations / 前端与全栈基础

1. [Scope and closure / 作用域与闭包](../frontend/javascript/scope-and-closure.md) — revisit JavaScript variable lookup and captured bindings.
2. [HTTP protocols and WebSockets / HTTP 协议与 WebSocket](../engineering-foundations/networking/http-protocols-and-websockets.md) — connect web application behavior to its network protocols.
3. [Processes, Threads, and Concurrency / 进程、线程与并发](../engineering-foundations/operating-systems/processes-threads-and-concurrency.md) — distinguish process isolation, shared thread state, and concurrency.
4. [Database Fundamentals / 数据库基础](../engineering-foundations/databases/database-fundamentals.md) — review constraints, transaction boundaries, indexes, and recovery.
5. [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../engineering-foundations/reliability/api-reliability-and-async-delivery.md) — connect deadlines and retries with idempotency, backpressure, and queue acknowledgements.

## Related study routes / 延伸复习路线

- [Python Fundamentals / Python基础](../engineering-foundations/backend/python-fundamentals.md) → [Python Async and FastAPI Request Lifecycle / Python异步与FastAPI请求生命周期](../engineering-foundations/backend/python-async-and-fastapi.md) → [HTTP API Contracts / HTTP API契约](../engineering-foundations/backend/http-api-contracts.md) — move from language and async execution to a predictable request/response boundary.
- [Data Access and Connection Pools / 数据访问与连接池](../engineering-foundations/backend/data-access-and-connection-pools.md) → [Caching and Redis / 缓存与 Redis](../engineering-foundations/backend/caching-and-redis.md), alongside [Web Security and Authentication / Web安全与身份认证](../engineering-foundations/security/web-security-and-authentication.md) — separate transaction and connection lifetimes, cache freshness, and shared identity/authorization boundaries.
- [Software Testing Strategy / 软件测试策略](../engineering-foundations/testing/software-testing-strategy.md) → [Reading, Debugging, and Reviewing Code / 阅读、调试与审查代码](../engineering-foundations/architecture/reading-debugging-and-reviewing-code.md) — choose evidence at the boundary that can prove a risk, then trace failures to their cause.
- [Algorithms and Complexity / 算法与复杂度分析](../engineering-foundations/algorithms/algorithms-and-complexity.md) → [Memory Hierarchy and Data Locality / 内存层次与数据局部性](../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md) → [Core Data Structures / 核心数据结构](../engineering-foundations/algorithms/core-data-structures.md) — extend asymptotic bounds with memory-access costs, then apply them to concrete structures.
- [Application Deployment and CI/CD / 应用部署与持续交付](../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md) → [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](../engineering-foundations/reliability/observability-slos-and-incident-response.md) → [System Design Fundamentals / 系统设计基础](../engineering-foundations/architecture/system-design-fundamentals.md) — connect artifact promotion and health-gated rollout to user-facing service objectives and architecture trade-offs.
- [Streaming UX / 流式交互](../frontend/browser-apis/streaming-ux.md) → [Advanced TypeScript / TypeScript进阶](../frontend/typescript/advanced-typescript.md) → [Advanced React / React进阶](../frontend/frameworks/advanced-react.md) → [Frontend Testing / 前端测试](../frontend/testing/frontend-testing.md) — follow incremental server output into typed UI state, component lifecycles, and client-side checks.

## Domain maps / 领域地图

- [AI engineering topic map / AI 工程主题地图](../ai-engineering/index.md)
- [Frontend topic map / 前端主题地图](../frontend/index.md)
- [Engineering foundations topic map / 工程基础主题地图](../engineering-foundations/index.md)

## Continuous reading / 连续阅读

- [AI engineering / AI 工程](generated/ai-engineering.md)
- [Frontend / 前端](generated/frontend.md)
- [Engineering foundations / 工程基础](generated/engineering-foundations.md)
