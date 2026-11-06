# AI Engineering / AI 工程

先沿着一条消息走完 AI 服务的处理过程，再深入证据、模型或发布决策。

## Start with a question / 从问题开始

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md) — 沿一个构建失败问题，走完模型推理、日志查询和返回解释的过程。
- [How does an updated document become usable evidence? / 更新后的文档怎样成为可用证据？](rag/rag-architecture-and-implementation.md) — Follow a document revision through indexing, access checks, retrieval, and citation. / 沿一次文档更新看索引、权限校验、检索和引用。
- [What would justify shipping a model or prompt change? / 怎样证明模型或提示词的改动值得上线？](evaluation/llm-evaluation-methods.md) — Compare the baseline and candidate on representative tasks and check the production outcome. / 用代表性任务对照基线和候选版本，再看生产结果。

## Literature / 论文与文章

- [AI 好文集](../review/ai-literature-index.md) — 按主题查找值得读的来源，以及解释其贡献的笔记。

## Reading order / 阅读顺序

### End-to-end application / 应用主线

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md)

### Foundation models / 基础模型

- [语言模型如何把提示词变成文本？](foundations/how-llms-work.md)
- [How should you choose a model for a task and its deployment constraints? / 如何根据任务与部署约束选择模型？](foundations/model-selection-and-ecosystem.md)

### Prompting / 提示工程

- [How do you write a prompt that makes a task clear and testable? / 如何编写清楚且可检验的任务提示词？](prompting/prompt-engineering-fundamentals.md)
- [Which prompting technique should you try when a simple prompt fails? / 简单提示失败时应尝试哪种提示技巧？](prompting/advanced-prompting-techniques.md)

### Context / 上下文

- [What should each model inference see, and what should the application persist? / 每次模型推理应看到什么，应用应持久化什么？](context/context-engineering-principles.md)

### Retrieval-augmented generation / 检索增强生成

- [How do you retrieve and use authorized external evidence in a grounded answer? / 怎样检索并使用经过授权的外部证据生成有依据的回答？](rag/rag-architecture-and-implementation.md)

### Agents / 智能体

- [When should a model control the next step? / 何时应让模型决定下一步？](agents/agent-fundamentals.md)
- [How should a multi-step AI task be structured? / 怎样组织多阶段 AI 任务？](agents/orchestration-patterns.md)
- [How should an application execute a model’s tool request? / 应用应如何执行模型的工具请求？](agents/tool-design-and-function-calling.md)

### Safety / 安全

- [How can a production AI system contain model errors and manipulation? / 生产环境 AI 系统如何限制模型错误与受诱导带来的影响？](safety/ai-safety-in-production.md)

### Evaluation and improvement / 评估与改进

- [How can you tell whether an AI system meets its task contract? / 如何判断 AI 系统是否满足任务契约？](evaluation/llm-evaluation-methods.md)
- [How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](agents/agent-improvement-and-version-acceptance.md)

### Fine-tuning / 微调

- [When should you fine-tune to close a repeatable behavior gap? / 何时应通过微调弥补稳定的行为差距？](fine-tuning/fine-tuning-strategies.md)

### Production systems / 生产系统

- [How can a production AI run survive disconnections and worker failures? / 生产环境中的 AI 运行如何经受断连与 worker 故障？](systems/ai-application-architecture.md)
- [How do you reduce AI application latency and cost without weakening task quality? / 如何在不损害任务质量的前提下降低 AI 应用的时延与成本？](systems/ai-latency-and-cost-optimization.md)
- [How do KV cache and scheduling determine LLM serving capacity? / KV 缓存与调度怎样决定模型推理容量？](systems/llm-serving-and-kv-cache.md)
- [When should an AI application use a hosted API, self-hosting, edge, or hybrid deployment? / AI 应用何时应选托管 API、自托管、端侧或混合部署？](systems/ai-deployment-patterns.md)
- [How do you monitor a production AI feature and turn feedback into a safe improvement? / 如何监控生产中的 AI 功能并安全地改进？](systems/ai-production-observability-and-feedback.md)
- [How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？](systems/ai-system-design-interview-questions.md)

## Cross-domain context / 跨域脉络

生产级 AI 应用依赖通用网络与安全机制：[HTTP 与 WebSocket](../engineering-foundations/networking/http-protocols-and-websockets.md) 介绍服务通信，[Web 安全与身份认证](../engineering-foundations/security/web-security-and-authentication.md) 补充应用边界。
