# AI Engineering / AI 工程

Follow the model from tokens to generation, then design what the application supplies and which actions it allows. Use the evaluation and production questions to check whether the resulting system works reliably. / 从词元到文本生成，再到应用提供哪些信息、允许哪些动作。最后用评估和生产问题检验系统能否可靠工作。

## Literature / 论文与文章

- [AI Literature Index / AI 论文与文章索引](../review/ai-literature-index.md) — 按来源查找核心贡献与知识落点。

## Reading order / 阅读顺序

### Foundation models / 基础模型

- [How does a language model turn a prompt into text? / 语言模型怎样把一段 prompt 变成文本？](foundations/how-llms-work.md)
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
