# AI Literature Index / AI 论文与文章索引

按来源反查核心贡献及其融入的主题笔记；具体机制、证据和适用边界见对应正文及就近引用。Use this index to find each source's contribution and the canonical notes that incorporate it; those notes retain the explanations, evidence, and limits.

按所收录版本的发布日期倒序排列。论文记录具体版本，文章记录发布日期。

| Source, version & date / 来源、版本与日期 | Contribution / 核心贡献 | Integrated notes / 知识落点 |
|---|---|---|
| [Building agents: When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) · Anthropic 文章 · 2026-10-22 | 讨论将依赖共享上下文的专业流程融入主循环，按需加载 Skills/tools，并评估何时保留独立 worker。 / Discusses folding shared-context specialists into one loop while evaluating separate workers. | [编排模式](../ai-engineering/agents/orchestration-patterns.md)：结构选择；[上下文工程](../ai-engineering/context/context-engineering-principles.md)：按需加载与交接损失；[评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md)：架构迁移对照。 |
| [Scaling Discovery Requires Forgetting](https://arxiv.org/abs/2610.20563v1) · arXiv v1 · 2026-10-14 | 在外部评分的开放搜索中，测试清除会话与候选历史、保留最佳候选及分数的重启策略。 / Studies search resets that retain the best artifact and score while clearing both histories. | [上下文工程](../ai-engineering/context/context-engineering-principles.md)：保留与重启的对象；[评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md)：重启对照、预算与归因边界。 |
| [Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/html/2610.14224v1) · arXiv v1 · 2026-10-09 | 通过实际执行对照迭代冻结模型外的 harness，并跨任务积累可检索的改进经验。 / Iterates execution harnesses around frozen models using real probes and experience across tasks. | [Agent 基础](../ai-engineering/agents/agent-fundamentals.md)：改进对象与共同基线；[上下文工程](../ai-engineering/context/context-engineering-principles.md)：经验库复用；[评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md)：行为对照与正确性。 |
| [RSI-Anything: Unlocking Recursive Self-Improvement with World Models](https://arxiv.org/html/2610.13912v1) · arXiv v1 · 2026-10-09 | 提出以候选效果预测、真实反馈及策略—预测器配对验收组织递归改进的框架。 / Proposes a framework connecting candidate forecasts, real feedback, and joint policy–predictor acceptance. | [Agent 基础](../ai-engineering/agents/agent-fundamentals.md)：反馈、预测与持久改进；[评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md)：组件与配对验收。 |
| [GitSwarm: Decentralized Compounding Inference](https://arxiv.org/html/2610.04862v1) · arXiv v1 · 2026-10-04 | 通过持久、可分支的共享产物和显式来源记录，让 worker 跨尝试复用、验证与组合既有工作。 / Organizes reusable work across episodes through persistent, branchable artifacts and provenance. | [上下文工程](../ai-engineering/context/context-engineering-principles.md)：经验资产与来源；[编排模式](../ai-engineering/agents/orchestration-patterns.md)：独立产物与并行边界；[评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md)：复用证据与因果收益。 |

返回 [AI 工程主题地图](../ai-engineering/index.md) 或 [知识导航](index.md)；按主题连续阅读可打开 [AI 工程连续阅读稿](generated/ai-engineering.md)。
