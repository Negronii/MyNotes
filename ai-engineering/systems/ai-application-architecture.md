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

## Durable runs, checkpoints, and recovery / 持久化运行、检查点与恢复

**Core explanation / 核心解释：** The application owns the meaning and current state of a model run; an HTTP response or token stream is only one way to deliver updates. Give a logical submission a stable runId, persist its state and useful checkpoints, and let clients look up the same run after a timeout or reconnect. A lost connection says that delivery stopped; it does not say whether work completed. / 应用负责定义模型运行的含义和当前状态；HTTP 响应或 token 流只是传递更新的一种方式。为一次逻辑提交分配稳定的 runId，持久化其状态和有用检查点，并允许客户端在超时或重连后查询同一次运行。连接丢失只表示交付中断，不能说明任务是否完成。

**Key terms / 关键术语：** run/job ID / 运行或作业标识；authoritative state / 权威状态；checkpoint / 检查点；resume / 恢复；idempotency key / 幂等键；unknown outcome / 结果未知；terminal state / 终态.

### Choose a completion shape / 选择完成方式

All three shapes can refer to one stable run identity, but they make different promises about waiting, early output, and recovery:

| Shape | What the caller sees | Trade-off |
|---|---|---|
| **Direct response / 直接响应** | One request waits for a final response. Its runId can be correlated or queried if the application persists the run. | Few moving parts and a simple client; long waits are vulnerable to deadline and connection limits. If the server does not retain state, a lost response leaves no status to recover. |
| **Provisional stream / 临时流式响应** | The same run emits partial text or progress before its terminal result. | Better perceived responsiveness, but streamed text is provisional until a terminal frame and authoritative run state agree. A disconnect can leave a useful partial answer and an unknown outcome. |
| **Queued/background completion / 排队或后台完成** | Submission returns a run identity and current state; a worker completes it later, and the client polls or reconnects for updates. | Fits longer work and bounded admission, but adds durable state, queue/worker operations, status handling, and retention policy. 202 Accepted means processing was accepted, not completed. |

For example, a synthetic API can accept POST /runs with a stable idempotency key, return 202 and runId, expose GET /runs/{runId} for current state, and stream events from GET /runs/{runId}/events?after=12. The record is authoritative; event delivery is a view. The after cursor is useful only while the server retains the corresponding event history. This example is an application contract, not an HTTP requirement.

Model the server-side lifecycle explicitly. accepted, queued, and running are nonterminal states. cancel_requested records a request that still needs handling. completed, failed, and canceled are terminal states. Keep the terminal result or error summary with the run long enough for clients to resolve retries and refreshes. A reconnect should fetch the run's status before claiming success; replayed progress is safe only when the service defines a cursor and retains the events needed to fill gaps.

### Submission, side effects, and cancellation races / 提交、副作用与取消竞态

A timeout after POST /runs creates an **unknown submission outcome**: the server may have created the run even though its response never reached the client. The client should query by its stable submission key or repeat the same request with that key. The server must bind a key to the same request parameters and return the existing run for a duplicate; reusing the key with different input must be rejected or have an explicit contract. Starting a new run with a fresh key can duplicate model cost or side effects.

Worker recovery has a second ambiguity around external side effects. Checkpoints tell the application what it recorded; they cannot reveal whether an unrecorded remote effect committed:

1. A worker records that an export run is at create-artifact, then crashes **before** calling the artifact service. Recovery can retry that step with the same operation key.
2. The artifact service creates the file, but the worker crashes **before** saving the returned artifact ID as the next checkpoint. The application cannot infer failure from the missing checkpoint. Retry with the same key if the receiving service deduplicates it, or query that service by operation key and then save the result. If neither is supported, mark the outcome unknown and reconcile it; blindly repeating may create a duplicate.

This is not a promise of exactly-once external effects. Persist a local effect and its deduplication record in one transaction when both share a database; for another service, use that service's idempotency contract, a queryable operation key, or a compensation/reconciliation path. See [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) for retry budgets, key scope, deadlines, and queue acknowledgements.

Cancellation also races with normal completion. Persist a cancel_requested transition and let the worker observe it at a safe point. If completion committed first, report completed; if cancellation wins, report canceled only when the run can no longer perform its work. A cancel endpoint acknowledging receipt is not that terminal confirmation. Cancellation cannot undo an already committed external action unless the application has a defined compensating operation.

| Failure point | What is known | Safe next step |
|---|---|---|
| Request or stream disconnects before a terminal result | The caller's view is incomplete; the run may still be active or already terminal. | Query GET /runs/{runId}. Resume events only with a defined, retained cursor; do not resubmit under a new key. |
| Worker crashes before a side effect | The checkpoint says the step did not finish, but another worker can retry it. | Use the same stable operation key and persist the result before advancing the checkpoint. |
| Worker crashes after an external effect but before its result is recorded | The external outcome is unknown to the run record. | Deduplicate or query at the receiver, then reconcile the checkpoint; do not infer that the effect failed. |
| Cancel request races with completion | Either transition may win the authoritative state update. | Serialize the transition and return the state that actually won; treat a pending request as nonterminal. |

### Replay is a runtime choice / 重放是运行时选择

Some workflow runtimes persist an ordered event history and replay deterministic orchestration code to rebuild its in-memory state. In such a runtime, completed external activities can return their recorded results during replay; a model call is not made deterministic by this mechanism. A model call that was still in flight before its result was recorded may be attempted again and can cost more or return different text. Decide whether that retry is acceptable and checkpoint the result when it completes. Deterministic event-history replay is a runtime-specific implementation option, not a requirement that an LLM recompute identical output after a crash.

**Representative answer / 代表性回答：** I give each logical AI run a stable ID and persist its state independently of the response connection. A direct request, provisional stream, or queued worker can all expose that same run. On reconnect, the client checks status and resumes from a retained cursor only if the service supports it. A worker checkpoints completed steps, but it retries a side effect only with a deduplication or reconciliation contract because a crash after the effect can hide its outcome. Cancellation is terminal only after the authoritative state says the work stopped; a client disconnect or cancel acknowledgement is not enough. / 我会为每次逻辑 AI 运行分配稳定标识，并独立于响应连接持久化运行状态。直接响应、临时流式响应和排队 worker 都可以暴露同一运行。重连时客户端先查询状态，只有服务端支持保留游标时才按游标续传。worker 为已完成步骤保存检查点；副作用只能在具备去重或结果对账契约时重试，因为副作用完成后发生崩溃会让结果变得未知。只有权威状态确认工作已停止，取消才是终态；客户端断线或收到取消请求确认都不足以证明这一点。

**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) owns DNS, polling/SSE/Fetch/WebSocket transport behavior and wire framing. The [streaming UX note / 流式交互笔记](../../frontend/browser-apis/streaming-ux.md) applies a run contract to browser consumption, partial output, and teardown.

**Sources checked 2026-10-15 / 来源核对日期：** [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) defines idempotent HTTP method semantics, and [§15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) says 202 Accepted does not mean processing is complete. Temporal's [Workflow replay guide](https://docs.temporal.io/workflows) and [Event History guide](https://docs.temporal.io/encyclopedia/event-history) describe one runtime's deterministic orchestration replay and recorded activity results. These sources support the mechanisms above; the example API and state names are synthetic application choices.
