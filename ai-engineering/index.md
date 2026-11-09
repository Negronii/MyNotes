# AI 工程

先沿着一条消息走完 AI 服务的处理过程，再深入证据、模型或发布决策。

## 从问题开始

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md) — 沿一个构建失败问题，走完模型推理、日志查询和返回解释的过程。
- [怎样从授权文档中检索并核验回答依据？](rag/rag-architecture-and-implementation.md)——沿一次文档更新看索引、权限校验、检索和引用。
- [如何判断 AI 系统是否满足任务契约？](evaluation/llm-evaluation-methods.md)——用代表性任务对照基线和候选版本，再看生产结果。

## 论文与文章

- [AI 好文集](../review/ai-literature-index.md) — 按主题查找值得读的来源，以及解释其贡献的笔记。

## Reading order / 阅读顺序

### 先走完一次回答

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md)

### 模型怎样计算，服务怎样承接请求

- [语言模型如何把提示词变成文本？](foundations/how-llms-work.md)
- [长上下文怎样少存、少读历史，同时保留需要的信息？](foundations/long-context-attention.md)
- [KV 缓存与调度怎样决定大语言模型的服务容量？](systems/llm-serving-and-kv-cache.md)
- [如何测量并降低 AI 应用的时延与成本，同时守住任务质量？](systems/ai-latency-and-cost-optimization.md)
- [怎样让模型 API 调用在限额、失败和截止时间内有界？](systems/bounded-model-api-calls.md)
- [如何为具体任务选择模型，并让部署约束进入决策？](foundations/model-selection-and-ecosystem.md)
- [AI 应用怎样选择部署方式，并逐步上线或回滚？](systems/ai-deployment-patterns.md)

### 输入、外部证据与行动

- [怎样写出清楚且可验收的提示词？](prompting/prompt-engineering-fundamentals.md)
- [简单提示失败后，怎样选择并评估提示技巧？](prompting/advanced-prompting-techniques.md)
- [每次模型调用应看到什么，应用又应持久化什么？](context/context-engineering-principles.md)
- [怎样从授权文档中检索并核验回答依据？](rag/rag-architecture-and-implementation.md)
- [HNSW 怎样逐层找近邻，怎样知道搜索得够不够？](rag/hnsw-vector-index-search.md)
- [应用怎样设计并执行模型提出的工具请求？](agents/tool-design-and-function-calling.md)
- [主机怎样把 MCP 工具从发现接到有权限的执行？](agents/mcp-tool-connections.md)
- [无人值守 Agent 怎样在用户授权内继续第三方操作？](agents/delegated-oauth-for-agent-tools.md)
- [什么时候应该让模型决定下一步？](agents/agent-fundamentals.md)
- [模型选到 shell 或文件工具后，由谁决定能否执行？](agents/coding-agent-harness.md)
- [怎样按依赖、并行性和控制权组织多阶段 AI 任务？](agents/orchestration-patterns.md)
- [生产 AI 如何阻止不可信内容诱导模型越权？](safety/ai-safety-in-production.md)
- [AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复？](systems/ai-application-architecture.md)

### 从发现差距到验证改进

- [如何判断 AI 系统是否满足任务契约？](evaluation/llm-evaluation-methods.md)
- [何时应微调来弥补稳定的行为差距？](fine-tuning/fine-tuning-strategies.md)
- [可验证奖励如何训练推理能力？](fine-tuning/reward-based-reasoning-training.md)
- [如何验证并保留对 Agent 的改进？](agents/agent-improvement-and-version-acceptance.md)
- [如何监控生产中的 AI 功能并安全地改进？](systems/ai-production-observability-and-feedback.md)
- [如何把 AI 系统设计题转化为有依据的架构？](systems/ai-system-design-interview-questions.md)

## 跨域脉络

生产级 AI 应用依赖通用网络与安全机制：[HTTP 与 WebSocket](../engineering-foundations/networking/http-protocols-and-websockets.md) 介绍服务通信，[Web 安全与身份认证](../engineering-foundations/security/web-security-and-authentication.md) 补充应用边界。
