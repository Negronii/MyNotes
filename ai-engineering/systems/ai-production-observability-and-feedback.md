# How do you monitor a production AI feature and turn feedback into a safe improvement? / 如何监控生产中的 AI 功能并安全地改进？

**Core explanation / 核心解释：** Pair technical service signals with task outcomes. Record enough version and trace context to locate a regression while minimizing sensitive payloads. Treat user feedback as a useful but biased signal: inspect failure modes, make a targeted change, compare it on held-out cases, and keep or roll it back against agreed criteria. / 将服务运行信号与任务结果一起观察。记录足以定位回归的版本与追踪信息，同时尽量减少敏感载荷。用户反馈有用但存在偏差：先检查失败类型，再做有针对性的变更，在留出案例上比较，最后按约定标准保留或回滚。

**Key terms / 关键术语：** observability / 可观测性；trace / 追踪；task outcome / 任务结果；feedback signal / 反馈信号；rollback / 回滚。

## How should an application monitor behavior? / 应用应监控哪些行为？

Track technical operation and task outcomes together. Useful measures include:

- latency distributions and time to first token (TTFT), throughput, and queue time;
- errors and timeouts by stage, input/output usage, and cost per completed task;
- tool success and authorization denials, cache-hit correctness, task completion, and escalation;
- explicit user feedback and whether the result was accepted or corrected.

Set thresholds from service requirements and a measured baseline; no universal error-rate or latency threshold fits every application. Record prompt, model, and relevant configuration versions so a change can be investigated. Keep logs proportionate: redact or avoid sensitive content and apply retention controls. Use sampled traces or derived metrics when full payload logging is unnecessary.

Model behavior, external data, prompts, and provider implementations can change. Re-run an evaluation set when a material component changes and compare results by important task slices. [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) owns task-quality definitions, dataset design, judge validation, and acceptance evidence. Keep a rollback or fallback path when a release misses the agreed quality bar.

## How can feedback improve the product? / 如何让反馈改进产品？

Collect explicit signals such as ratings or corrections and implicit signals such as task completion, accepted suggestions, repeated requests, and escalation. These signals are incomplete and biased: a rating reflects who chose to respond, while time spent can mean either engagement or confusion. Interpret them alongside representative task evaluation and user research.

A practical improvement loop is:

1. Capture feedback with relevant task and version context, subject to privacy and retention rules.
2. Review a sample and classify its failure mode.
3. Fix the appropriate layer: source data, retrieval, prompt, tool, model choice, interface, or policy.
4. Test the change on held-out cases and monitor the relevant production outcome.
5. Keep or roll back the change using the agreed criteria.

Preference data may inform fine-tuning or preference optimization, but a feedback button alone does not create a validated training signal. See [Fine-tuning Strategies / 微调策略](../fine-tuning/fine-tuning-strategies.md). For permission boundaries, human approval, and production stop paths, see [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md).

**Related note / 相关笔记：** [AI Application Architecture / AI 应用架构](ai-application-architecture.md) defines the durable run state and recovery contract that lets service metrics and task feedback remain attached to one logical operation.

**Source boundary / 来源边界：** These monitoring and feedback practices reorganize the existing architecture note. Thresholds, task metrics, and data-retention rules must come from the particular service's requirements and privacy constraints; this note does not prescribe universal numeric targets.
