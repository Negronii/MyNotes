# AI Application Architecture / AI 应用架构

**Core explanation / 核心解释：** A production LLM application is a software system around a model call: it manages identity, context, tools, validation, timeouts, retries, cost, monitoring, and recovery. Choose optimizations and deployment boundaries from measured quality, workload, privacy, and operations requirements. / 生产级 LLM 应用是围绕模型调用构建的软件系统，需要管理身份、上下文、工具、校验、超时、重试、成本、监控与恢复。应根据实测质量、工作负载、隐私和运维要求选择优化与部署边界。

**Key terms / 关键术语：** latency / 时延；time to first token (TTFT) / 首 token 时延；routing / 路由；caching / 缓存；fallback / 回退；observability / 可观测性；feedback loop / 反馈闭环。

## What changes from prototype to production? / 从原型到生产会发生什么变化？

A prototype tests whether an approach can solve a task. A production service must also handle concurrent users, malformed or incomplete responses, provider and tool failures, changing inputs, permissions, privacy, cost, and rollback. Design the surrounding controls before relying on the model in a consequential workflow.

~~~text
Request → authenticate and authorize → assemble context
        → model and/or tools → validate result → respond or escalate
        ↘ trace, metrics, and privacy-reviewed logs
~~~

For tool use, the application receives a proposed call and executes it only after its own argument checks and authorization. A model response or schema-constrained output does not itself grant access or establish that an action is valid. See [Tool Design and Function Calling / 工具设计与函数调用](../agents/tool-design-and-function-calling.md) and [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md).

Useful production controls include explicit timeouts, bounded retries, idempotency for retried writes, cancellation, rate and budget limits, an error path, and a way to disable or roll back a model or prompt version. Retry only failures that can safely be retried; a timeout does not prove a write did not happen.

## How can you reduce latency and cost? / 如何降低时延与成本？

First measure where time and cost accumulate: queueing, context assembly, retrieval, model input/output, tools, and retries. Then test a change against a fixed quality bar; savings that break the task are not an optimization.

- **Shorten or select context / 缩短或筛选上下文：** include relevant material and limit unnecessary history. Measure for lost evidence or task quality; see [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md).
- **Use caching / 使用缓存：** exact-response or semantic caches can avoid work for repeat requests, but require freshness, permission, and key-isolation rules. For example, “What is the refund policy in the US?” and “What is the refund policy in the EU?” can have similar embeddings but different correct answers. Include relevant locale, tenant, permission, and policy-version boundaries in cache design; semantic similarity alone is not proof that a response is reusable.
- **Route requests / 请求路由：** use a lower-cost candidate only for cases where it meets the measured quality bar. Include classifier errors, added latency, fallback frequency, and maintenance in the comparison. See [Model Selection and Ecosystem / 模型选择与生态](../foundations/model-selection-and-ecosystem.md).
- **Inference batching / 推理批处理：** a serving engine can combine work from concurrent requests into accelerator batches. Iteration-level or continuous batching can admit and retire sequences between token-generation steps, improving hardware utilization and aggregate throughput on suitable workloads. Queueing and batch formation can add per-request delay, so measure throughput, queue time, and latency together. This is distinct from an asynchronous provider Batch API, where requests are submitted as a job and results arrive later; that interface is for work that tolerates delayed completion, not a promise about how an inference engine batches live traffic.
- **Quantization / 量化：** represent weights, and in some methods activations, with fewer bits. This can reduce model memory and data movement, and may improve inference speed when the hardware and kernels support the chosen format. Quantization error can affect task quality, and lower precision does not guarantee faster end-to-end service; evaluate the exact model, quantizer, hardware, and workload.
- **Distillation / 蒸馏：** train a smaller student on outputs or softened targets from a larger teacher over chosen inputs. A student may reduce serving cost or latency, but can lose capabilities or fail outside the distillation set. Include teacher/data generation and evaluation in the cost, and test the student on held-out tasks before replacing the teacher.
- **Stream responses / 流式返回：** streaming can improve perceived responsiveness and time to first token; it does not necessarily reduce total generation time or work.

Provider features such as prompt caching, batch jobs, context limits, and pricing vary by model and API and can change. Verify current documentation for the exact deployment. Compare total cost, including inference, retrieval, storage, engineering, evaluation, and operations.

### A teaching calculation for cache cost / 缓存成本教学算例

Assume 1,000 model calls, each with 1,000 input tokens and 200 output tokens. For this arithmetic example only, assume uncached input costs $2 per million tokens, cached input costs $1 per million, and output costs $8 per million. These are invented teaching values, not current provider prices; ignore cache-write, storage, retrieval, and other fees.

Without caching, the token charge is 1,000 × [(1,000 × $2) + (200 × $8)] / 1,000,000 = $3.60.

Suppose 400 calls share a 500-token prompt prefix and receive the assumed cached-input rate for that prefix. Prompt caching still processes the remaining input and generates all 200 output tokens. The assumed token charge becomes 600 × $0.0036 + 400 × [$0.0005 + $0.001 + $0.0016] = $3.40: the $0.20 saving comes only from the lower rate on 400 × 500 cached input tokens. The output is still generated and billed.

An application-level response-cache hit is different: if 400 requests can safely reuse an exact, current response, those requests skip the model call, so the remaining 600 model calls cost 600 × $0.0036 = $2.16 in token charges, before cache infrastructure costs. This calculation assumes a valid exact response hit; a semantic cache needs its own correctness and authorization checks. OpenAI's current [prompt caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching), checked 2026-10-15, likewise describes reuse of a prompt prefix while the model still generates a new response; its supported models, rates, and cache rules are provider-specific and change.

## How should an application monitor behavior? / 应用应监控哪些行为？

Track technical operation and task outcomes together. Useful measures include latency distributions and TTFT, throughput and queue time, errors and timeouts by stage, input/output usage, cost per completed task, tool success and authorization denials, cache hit correctness, task completion, escalation, and user feedback.

Set thresholds from the service's requirements and baseline; no universal error-rate or latency threshold fits every application. Record prompt, model, and relevant configuration versions so a change can be investigated. Keep logs proportionate: redact or avoid sensitive content and apply retention controls. Use sampled traces or derived metrics where full payload logging is unnecessary.

Model behavior, external data, prompts, and provider implementations can change. Re-run an evaluation set when a material component changes and compare results by important task slices; see [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md). Maintain a rollback or fallback path when a release violates the product's agreed quality bar.

## How can feedback improve the product? / 如何让反馈改进产品？

Collect explicit signals such as ratings or corrections and implicit signals such as task completion, accepted suggestions, repeated requests, and escalation. These signals are incomplete and biased: a rating reflects who chose to respond, while time spent can indicate either engagement or confusion. Interpret them alongside representative task evaluation and user research.

A practical loop is:

1. Capture feedback with the relevant task and version context, subject to privacy and retention rules.
2. Review a sample and classify the failure mode.
3. Fix the appropriate layer: source data, retrieval, prompt, tool, model choice, interface, or policy.
4. Test the change on held-out cases and monitor the relevant production outcome.
5. Keep or roll back the change based on the agreed criteria.

Preference data may inform fine-tuning or preference optimization, but a feedback button alone does not create a validated training signal. See [Fine-tuning Strategies / 微调策略](../fine-tuning/fine-tuning-strategies.md).

## API, self-hosted, edge, or hybrid — how do you pick a deployment pattern?

Compare the same workload and quality bar across patterns, including data flow, service terms, operations, peak capacity, update ownership, and failure recovery.

| Pattern | Useful when | Costs and constraints |
|---|---|---|
| **Hosted API / 托管 API** | Managed inference and quick iteration fit the task. | Provider terms, model lifecycle, feature support, rate limits, availability, and per-use costs need review. |
| **Self-hosted / 自托管** | Control over serving location, version, and infrastructure is a real requirement. | The team owns capacity, scaling, security updates, model serving, observability, and on-call response. |
| **Edge / 端侧** | Offline use, local latency, or device-level data handling matters. | Compute, battery, memory, device coverage, updates, and supported model size constrain the design. |
| **Hybrid / 混合** | Distinct workloads need different data or serving boundaries. | Routing and duplicated operations add complexity; define fallback and consistent policy behavior. |

A useful comparison is:

$$
\text{total cost} = \text{inference} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and controls}
$$

There is no universal spend threshold for switching to self-hosting. Estimate with actual traffic, peak demand, staffing, quality requirements, and the full operating burden. Edge and hybrid choices likewise depend on device and data constraints, not just latency labels.

## Related notes / 相关笔记

- [Model Selection and Ecosystem / 模型选择与生态](../foundations/model-selection-and-ecosystem.md) covers candidate comparison and routing.
- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) covers context budgets and caching.
- [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) covers offline and production evaluation.
- [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md) covers runtime boundaries and controls.
- [Database Fundamentals / 数据库基础](../../engineering-foundations/databases/database-fundamentals.md) covers durable application state, keys, index plans, transactions, isolation, and WAL.
- [API Reliability and Async Delivery / API 可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) covers deadlines, unknown outcomes, retry idempotency, bounded work, and queues for tool and service calls.

## Sources / 来源

- OpenAI, [Function calling](https://developers.openai.com/api/docs/guides/function-calling), checked 2026-10-15. Tool calls are proposed by the model and handled by application code.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. Schema adherence applies to supported schemas and models; semantic validation and failure handling remain application concerns.
- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Current capabilities and recommendations are API-specific and may change.
- Frantar et al., [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323); Lin et al., [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978).
- Hinton et al., [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531).
- Yu et al., [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu), for iteration-level scheduling and selective batching. OpenAI, [Batch API](https://developers.openai.com/api/docs/guides/batch), checked 2026-10-15, documents its separate asynchronous job interface.
