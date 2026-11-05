# How should you choose a model for a task and its deployment constraints? / 如何根据任务与部署约束选择模型？

Choose from candidates that satisfy the task's hard constraints, then compare them on representative examples against an agreed quality bar. Measure latency, total cost, modality and format reliability, data handling, and operational fit. Model names, rankings, context limits, supported inputs, and prices change, so a public benchmark or provider label is a lead for investigation, not a lasting selection rule. / 先筛出符合任务硬性约束的候选模型，再用有代表性的样本和约定的质量门槛进行比较。测量任务效果、时延、总成本、模态与格式可靠性、数据处理和运维适配。模型名称、排名、上下文限制、输入能力和价格都会变化，因此公开基准或供应商标签只能帮助调查，不能作为长期固定的选择规则。

**Key terms / 关键术语：** task contract / 任务要求；held-out set / 保留集；hosted API / 托管 API；open-weight / 开放权重；hybrid deployment / 混合部署；routing / 路由。

## Start with the task contract / 从任务要求开始

Record what a successful result must do, what errors matter, and which operating conditions are fixed. Compare candidates on the same prompt, data, tools, and evaluation protocol where possible.

| Dimension | Questions to answer |
|---|---|
| **Task quality / 任务质量** | What counts as correct or useful? Which edge cases and refusal cases matter? |
| **Latency and availability / 时延与可用性** | Is the constraint about time to first response, full completion, or uptime? Which workload and region are representative? |
| **Cost / 成本** | Include input and output usage, retries, retrieval, hosting, support, and evaluation—not just one token rate. |
| **Inputs and outputs / 输入与输出** | Does the task require text, image, audio, or other modalities? Are schemas or tools supported for this exact model and API? |
| **Data handling / 数据处理** | What do the contract, configuration, retention policy, and deployment boundary allow? “Hosted” or “open-weight” alone does not answer this. |
| **Operations / 运维** | Who owns scaling, updates, monitoring, security patches, and incident response? |

Public benchmarks can help generate a shortlist when their task and protocol are relevant. They do not establish performance on a different prompt, data distribution, API configuration, or deployment. Keep an application-specific held-out set and report its sample scope and uncertainty. [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) explains how to choose task criteria and compare changes.

## Model tiers are shorthand, not a catalog / 模型档位只是简称，不是目录

Teams sometimes use labels such as **frontier**, **balanced**, and **fast** to describe rough cost, latency, and capability tradeoffs within a provider's current catalog. Those labels are not shared standards: a “fast” model can be the better choice on a narrow task, and a “frontier” label does not prove quality on yours. Avoid copying an undated model list or treating a prior ranking as a current fact. Verify the exact model ID, supported API features, context limit, and pricing in the provider's current documentation when making a real selection.

## Hosted API, open-weight, or hybrid? / 托管 API、开放权重还是混合部署？

| Approach | Potential advantages | Costs and constraints to compare |
|---|---|---|
| **Hosted API / 托管 API** | Quick access to managed inference and model updates; less serving infrastructure to operate. | Data flows and retention depend on provider terms and configuration; usage, rate limits, availability, and model lifecycle are provider-controlled. |
| **Open-weight deployment / 开放权重部署** | More control over serving location, model version, and infrastructure choices. | A weight license is not automatically an open-source license or permission for every use. The operator owns hardware, serving, security, scaling, and updates. |
| **Hybrid / 混合部署** | Different models or environments can serve distinct workload classes. | Adds routing, evaluation, observability, policy consistency, and failure paths across systems. |

This is an eligibility and trade-off comparison, not a universal deployment ranking. Edge, self-hosted capacity, and detailed operating responsibilities have their own constraints; see [AI Deployment Patterns / AI 部署模式](../systems/ai-deployment-patterns.md).

Do not pick a hosting pattern from API spend alone. A useful estimate is:

$$
\text{total cost} \approx \text{inference usage} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and risk controls}
$$

Compare the same workload, quality target, peak traffic, and data constraints. A provider API may suit rapid iteration; self-hosting may suit a real data-control or workload need; edge deployment can help when offline operation or device constraints dominate. The break-even point depends on the actual workload and people costs.

## Route by measured need / 按实测需求路由

Routing can send simple, low-risk requests to a cheaper model and reserve a more capable option for cases that benefit from it. First measure whether the router's errors, added latency, and maintenance are outweighed by the savings. Use a task-relevant fallback when routing confidence is insufficient, and ensure high-impact operations still pass application-side authorization. Do not label “classification,” “reasoning,” or “extraction” as automatically easy or hard across all models.

Routing and other service optimizations need a fixed quality bar and end-to-end measurements; see [How to reduce AI application latency and cost / 如何降低 AI 应用时延与成本](../systems/ai-latency-and-cost-optimization.md). To connect versioned results and user feedback to an improvement or rollback decision, see [Production observability and feedback / 生产可观测性与反馈](../systems/ai-production-observability-and-feedback.md).

## Multimodal capability / 多模态能力

“Multimodal” does not specify which input or output a model supports or how well it handles a task. Test the actual modality and input shape—such as a chart, scanned document, spoken utterance, or video sample—under the target API. Check model documentation for supported formats, limits, and feature combinations at the time of deployment.

## Related notes / 相关笔记

- [AI Deployment Patterns / AI 部署模式](../systems/ai-deployment-patterns.md) compares hosted, self-hosted, edge, and hybrid operating patterns.
- [AI Application Architecture / AI 应用架构](../systems/ai-application-architecture.md) defines run identity, persistence, and recovery behavior across request channels.
- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) covers token budgets and provider-specific prompt caching.
- [Fine-tuning Strategies / 微调策略](../fine-tuning/fine-tuning-strategies.md) distinguishes behavior adaptation from maintained external knowledge.
- [RAG Architecture and Implementation / 检索增强生成](../rag/rag-architecture-and-implementation.md) covers current or access-controlled external evidence.

## Sources / 来源

- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Its guidance treats prompting, context, fine-tuning, and evaluation as task-specific optimization levers rather than a universal linear ladder.
- For current OpenAI model IDs and feature support, consult the changing [Models documentation](https://developers.openai.com/api/docs/models), checked 2026-10-15.
