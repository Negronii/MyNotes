# How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？

**Core explanation / 核心解释：** Clarify the user task and its success criteria, make workload and data-boundary assumptions explicit, then trace the request through retrieval, model or tool calls, validation, delivery, and operations. Deep-dive only on the risks that bind correctness, privacy, latency, cost, or safety; compare alternatives against evidence and include evaluation, rollout, and rollback. This capstone applies the canonical mechanisms to three illustrative designs. All traffic and latency figures below are hypothetical teaching assumptions, not production measurements or defaults. / 先澄清用户任务与成功标准，明确工作负载和数据边界假设，再沿着检索、模型或工具调用、校验、交付和运维梳理请求路径。只深入分析决定正确性、隐私、时延、成本或安全的关键风险；依据证据比较方案，并说明评估、发布和回滚。本文用三个示例设计应用各主题的规范机制。下方流量与时延数字均为教学假设，并非生产测量或默认值。

**Key terms / 关键术语：** requirements / 需求；data flow / 数据流；failure mode / 失败模式；trade-off / 权衡；evaluation / 评估；rollback / 回滚。

## How should you structure an AI system design answer? / 如何组织 AI 系统设计回答？

Use the following sequence as a set of discussion slots, not a fixed interview timetable:

1. **Clarify the task.** Identify users, inputs and outputs, success criteria, unacceptable errors, data sensitivity, freshness, and human review needs.
2. **Establish constraints.** Ask about expected workload and peaks, latency and availability goals, budget, deployment boundary, existing systems, and operational ownership. State assumptions when information is unavailable.
3. **Draw the end-to-end path.** Include ingestion if needed, request handling, model or retrieval calls, tools, validation, response or escalation, storage, and observability.
4. **Deep-dive on the binding risks.** Choose two or three components whose failure would most affect correctness, privacy, latency, cost, or safety. Explain alternatives and failure handling.
5. **Explain evaluation and rollout.** Define offline cases, production measures, staged release, rollback, and who responds to incidents.

Do not invent scale or latency targets to fill silence. Ask for them or label an assumption, then show how the design would change if it differs.

## Common trade-offs / 常见权衡

| Decision | Option A | Option B | What should drive it |
|---|---|---|---|
| Latency and cost | Smaller or fewer model calls | More capable model or additional checks | Measured task quality, workload, and response-time needs |
| Retrieval | Lower-cost candidate set | More recall or reranking work | Miss cost, corpus, and evaluation results |
| Autonomy | Model-directed tool loop | Fixed workflow or human review | Task variability, action risk, and control needs |
| Response mode | Immediate response | Queued or batch completion | User expectation and throughput |
| Deployment | Hosted service | Self-hosted or edge | Data boundary, operations, device, availability, and full cost |

Present each choice conditionally: explain when each option would fit, what evidence would change your decision, and how the alternative could be tested.

## Which design case should you study? / 应深入哪种设计案例？

- [How do you design permission-aware enterprise document question answering? / 如何设计具备权限意识的企业文档问答？](./ai-enterprise-document-qa-design.md) follows ingestion, retrieval, authorization, budget, and answer-evidence decisions.
- [How do you design a customer-support assistant that can safely issue refunds? / 如何设计能够安全处理退款的客服助手？](./ai-customer-support-agent-design.md) follows a fixed workflow from identity checks through verified refund execution and handoff.
- [How do you design a code-review assistant developers can trust? / 如何设计开发者愿意信任的代码审查助手？](./ai-code-review-assistant-design.md) follows advisory findings, human authority, evidence, and false-positive evaluation.

## Practice / 练习

- Ask clarifying questions before fixing assumed scale or targets.
- Draw the request and data paths, including trust boundaries and failures.
- State assumptions and what evidence could change the design.
- Discuss quality, latency, cost, permissions, and operational ownership together.
- Explain how the system is evaluated, rolled out, monitored, and rolled back.

## Related notes / 相关笔记

- [Durable AI runs / 持久化 AI 运行](./ai-application-architecture.md) covers production run controls. [AI deployment choices / AI 部署选择](./ai-deployment-patterns.md) compares where to run the model.
- [RAG Architecture and Implementation / 检索增强生成](../rag/rag-architecture-and-implementation.md) covers retrieval implementation and grounding.
- [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) covers evaluation design.
- [Agent Fundamentals / 智能体基础](../agents/agent-fundamentals.md) covers runtime agent patterns.
