# AI 工程

先沿着一条消息走完 AI 服务的处理过程，再深入证据、模型或发布决策。

## 从问题开始

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md) — 沿一个构建失败问题，走完模型推理、日志查询和返回解释的过程。
- [更新后的文档怎样成为可用证据？](rag/rag-architecture-and-implementation.md)——沿一次文档更新看索引、权限校验、检索和引用。
- [怎样证明模型或提示词的改动值得上线？](evaluation/llm-evaluation-methods.md)——用代表性任务对照基线和候选版本，再看生产结果。

## 论文与文章

- [AI 好文集](../review/ai-literature-index.md) — 按主题查找值得读的来源，以及解释其贡献的笔记。

## Reading order / 阅读顺序

### 先走完一次回答

- [AI 服务如何将一条消息变成完整回答？](systems/from-message-to-answer.md)

### 模型怎样计算，服务怎样承接请求

- [语言模型如何把提示词变成文本？](foundations/how-llms-work.md)
- [长上下文怎样少存、少读历史，同时保留需要的信息？](foundations/long-context-attention.md)
- [KV 缓存与调度怎样决定大语言模型的服务容量？](systems/llm-serving-and-kv-cache.md)
- [How do you reduce AI application latency and cost without weakening task quality? / 如何在不损害任务质量的前提下降低 AI 应用的时延与成本？](systems/ai-latency-and-cost-optimization.md)
- [How should you choose a model for a task and its deployment constraints? / 如何根据任务与部署约束选择模型？](foundations/model-selection-and-ecosystem.md)
- [When should an AI application use a hosted API, self-hosting, edge, or hybrid deployment? / AI 应用何时应选托管 API、自托管、端侧或混合部署？](systems/ai-deployment-patterns.md)

### 输入、外部证据与行动

- [How do you write a prompt that makes a task clear and testable? / 如何编写清楚且可检验的任务提示词？](prompting/prompt-engineering-fundamentals.md)
- [Which prompting technique should you try when a simple prompt fails? / 简单提示失败时应尝试哪种提示技巧？](prompting/advanced-prompting-techniques.md)
- [What should each model inference see, and what should the application persist? / 每次模型推理应看到什么，应用应持久化什么？](context/context-engineering-principles.md)
- [How do you retrieve and use authorized external evidence in a grounded answer? / 怎样检索并使用经过授权的外部证据生成有依据的回答？](rag/rag-architecture-and-implementation.md)
- [How should an application execute a model’s tool request? / 应用应如何执行模型的工具请求？](agents/tool-design-and-function-calling.md)
- [When should a model control the next step? / 何时应让模型决定下一步？](agents/agent-fundamentals.md)
- [How should a multi-step AI task be structured? / 怎样组织多阶段 AI 任务？](agents/orchestration-patterns.md)
- [How can a production AI system contain model errors and manipulation? / 生产环境 AI 系统如何限制模型错误与受诱导带来的影响？](safety/ai-safety-in-production.md)
- [How can a production AI run survive disconnections and worker failures? / 生产环境中的 AI 运行如何经受断连与 worker 故障？](systems/ai-application-architecture.md)

### 从发现差距到验证改进

- [How can you tell whether an AI system meets its task contract? / 如何判断 AI 系统是否满足任务契约？](evaluation/llm-evaluation-methods.md)
- [何时应微调来弥补稳定的行为差距？](fine-tuning/fine-tuning-strategies.md)
- [可验证奖励如何训练推理能力？](fine-tuning/reward-based-reasoning-training.md)
- [How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](agents/agent-improvement-and-version-acceptance.md)
- [How do you monitor a production AI feature and turn feedback into a safe improvement? / 如何监控生产中的 AI 功能并安全地改进？](systems/ai-production-observability-and-feedback.md)
- [How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？](systems/ai-system-design-interview-questions.md)

## 跨域脉络

生产级 AI 应用依赖通用网络与安全机制：[HTTP 与 WebSocket](../engineering-foundations/networking/http-protocols-and-websockets.md) 介绍服务通信，[Web 安全与身份认证](../engineering-foundations/security/web-security-and-authentication.md) 补充应用边界。
