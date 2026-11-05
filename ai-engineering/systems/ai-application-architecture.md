# How can a production AI run survive disconnections and worker failures? / 生产环境中的 AI 运行如何经受断连与 worker 故障？

**Core explanation / 核心解释：** A client connection is a delivery channel, not the identity or source of truth for an AI task. Give each logical submission a stable run ID, persist authoritative state and useful checkpoints, and let clients query or resume that run after a timeout. A disconnect leaves delivery incomplete; it does not establish whether the model call or an external side effect finished. / 客户端连接只是交付通道，不是 AI 任务的身份或事实依据。为每次逻辑提交分配稳定的运行 ID，持久化权威状态和有用检查点，并允许客户端在超时后查询或恢复同一次运行。断连只能说明交付不完整，无法证明模型调用或外部副作用是否完成。

**Key terms / 关键术语：** run ID / 运行标识；authoritative state / 权威状态；checkpoint / 检查点；resume / 恢复；idempotency key / 幂等键；unknown outcome / 结果未知；terminal state / 终态。

## What changes from prototype to production? / 从原型到生产会发生什么变化？

A prototype tests whether a model can help with a task. A production service must also authenticate and authorize the caller, assemble permitted context, handle model and tool failures, validate outputs, manage deadlines and cost, and expose a result that can be recovered after the original response channel ends.

~~~text
Request → authenticate and authorize → assemble permitted context
        → model and/or tools → validate result → respond or escalate
        ↘ persist run state, trace, and privacy-reviewed operational signals
~~~

Treat a model-proposed tool call as untrusted input. The application executes it only after its own argument checks and authorization; schema-constrained output does not establish that an action is valid or permitted. See [Tool Design and Function Calling / 工具设计与函数调用](../agents/tool-design-and-function-calling.md) and [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md). OpenAI’s [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) documentation, checked 2026-10-15, describe provider-specific request and schema behavior; application authorization and semantic validation remain separate.

Set explicit deadlines, bounded retries, idempotency for retryable writes, cancellation behavior, rate and budget limits, an error or escalation path, and a way to roll back a model or prompt version. Retry only when the operation contract makes a duplicate safe. A timeout says the caller did not receive a result in time; it does not say the server did no work.

These are separate design questions with deeper treatments: [how to reduce latency and cost](ai-latency-and-cost-optimization.md), [how to choose a deployment pattern](ai-deployment-patterns.md), and [how to monitor and improve a production feature](ai-production-observability-and-feedback.md). The remainder of this note defines the durable run contract that those interfaces rely on.

## Durable runs, checkpoints, and recovery / 持久化运行、检查点与恢复

Use one stable `runId` for a logical submission, independent of HTTP requests, event streams, and worker attempts. Persist the run's current state and terminal result or error summary long enough for clients to resolve refreshes and retries. A response body or stream is a view of that run, not its authoritative record.

### Choose a completion shape / 选择完成方式

All three shapes can expose the same run identity, but they make different promises about waiting, early output, and recovery:

| Shape | What the caller sees | Trade-off |
|---|---|---|
| **Direct response / 直接响应** | One request waits for a final response. Its `runId` can be correlated or queried if the service persists the run. | Few moving parts and a simple client; long waits are vulnerable to deadline and connection limits. Without retained state, a lost response leaves no status to recover. |
| **Provisional stream / 临时流式响应** | The same run emits partial text or progress before its terminal result. | Better perceived responsiveness, but text is provisional until a terminal frame and authoritative state agree. A disconnect can leave useful partial output and an unknown outcome. |
| **Queued/background completion / 排队或后台完成** | Submission returns a run identity and current state; a worker completes it later, and the client polls or reconnects for updates. | Fits longer work and bounded admission, but requires durable state, queue/worker operations, status handling, and retention. `202 Accepted` means processing was accepted, not completed. |

For example, a synthetic API can accept `POST /runs` with a stable idempotency key, return `202` and a `runId`, expose `GET /runs/{runId}` for current state, and stream events from `GET /runs/{runId}/events?after=12`. The run record is authoritative; event delivery is a view. The `after` cursor helps only while the server retains the corresponding event history. This is an application contract, not an HTTP requirement.

Model the server-side lifecycle explicitly. `accepted`, `queued`, and `running` are nonterminal states. `cancel_requested` records a request that still needs handling. `completed`, `failed`, and `canceled` are terminal states. A reconnect should fetch current run status before claiming success. Replay progress only when the service defines a cursor and retains the events needed to fill gaps. The diagram shows one path for queued work.

~~~mermaid
stateDiagram-v2
  [*] --> accepted
  accepted --> queued
  queued --> running
  running --> cancel_requested
  cancel_requested --> canceled
  running --> completed
  running --> failed
  cancel_requested --> completed: completion won the race
~~~

## What if submission times out or a side effect has an unknown outcome? / 提交超时或副作用结果未知时怎么办？

A timeout after `POST /runs` creates an **unknown submission outcome**. The server may have created the run even though its response never reached the client. The client can query by its stable submission key if the API supports that lookup, or repeat the same request under its same-key retry contract. The server binds a key to the same request parameters and returns the existing run for a duplicate. Reusing the key with different input requires explicit handling. Starting a new run with a fresh key can duplicate model cost or side effects.

Worker recovery has a second ambiguity around external effects. Checkpoints tell the application what it recorded; they cannot reveal whether an unrecorded remote effect committed:

1. A worker records that an export run is at `create-artifact`, then crashes **before** calling the artifact service. Recovery can retry that step with the same operation key.
2. The artifact service creates the file, but the worker crashes **before** saving the returned artifact ID as the next checkpoint. The run record cannot prove failure. Retry with the same key if the receiving service deduplicates it, or query that service by operation key and then save the result. If neither is supported, mark the outcome unknown and reconcile it; blindly repeating may create a duplicate.

Persist a local effect and its deduplication record in one transaction when both share a database. For another service, use its idempotency contract, a queryable operation key, or a compensation/reconciliation path. See [confirming request outcomes / 确认请求结果](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) for retry budgets, key scope, and deadlines. See [queue acknowledgements / 队列确认](../../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md) for what the broker confirms.

| Failure point | What is known | Safe next step |
|---|---|---|
| Request or stream disconnects before a terminal result | The caller's view is incomplete; the run may still be active or already terminal. | Query `GET /runs/{runId}`. Resume events only with a defined, retained cursor; do not resubmit under a new key. |
| Worker crashes before a side effect | The checkpoint says the step did not finish, but another worker can retry it. | Use the same stable operation key and persist the result before advancing the checkpoint. |
| Worker crashes after an external effect but before its result is recorded | The external outcome is unknown to the run record. | Deduplicate or query at the receiver, then reconcile the checkpoint; do not infer that the effect failed. |
| Cancel request races with completion | Either transition may win the authoritative state update. | Serialize the transition and return the state that actually won; treat a pending request as nonterminal. |

## What does cancellation mean for a durable run? / 持久化运行中的取消意味着什么？

Persist a `cancel_requested` transition and let the worker observe it at a safe point. Serialize the terminal updates so completion and confirmed cancellation compete to update the same run state. If completion commits first, report `completed`. Commit `canceled` only when the run can no longer perform its work. An endpoint acknowledgement can leave cancellation pending. Compensating for an already committed external action requires its own operation.

A browser abort, closed tab, or disconnected event stream ends a local delivery attempt. It does not prove that the server-side run stopped. The UI should query the run record or request server cancellation separately; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) covers the client view, incremental decoding, and teardown.

## When is event-history replay useful? / 事件历史重放何时有用？

Some workflow runtimes persist an ordered event history and replay deterministic orchestration code to rebuild in-memory state. In such a runtime, completed external activities can return their recorded results during replay; this mechanism does not make a model call deterministic. A model call still in flight before its result was recorded may be attempted again, cost more, or return different text. Decide whether that retry is acceptable and checkpoint the result when it completes. Deterministic event-history replay is a runtime-specific implementation option, not a requirement that an LLM recompute identical output after a crash.

**Representative answer / 代表性回答：** I give each logical AI run a stable ID and persist its state independently of the response connection. A direct request, provisional stream, or queued worker can expose that same run. On reconnect, the client checks status and resumes from a retained cursor only when the service supports it. A worker checkpoints completed steps, but retries a side effect only with a deduplication or reconciliation contract because a crash after the effect can hide its outcome. Cancellation is terminal only after authoritative state says the work stopped; a client disconnect or cancel acknowledgement is not enough. / 我会为每次逻辑 AI 运行分配稳定标识，并独立于响应连接持久化运行状态。直接响应、临时流式响应或排队 worker 都可以暴露同一次运行。重连时客户端先查询状态，只有服务端支持保留游标时才按游标续传。worker 为已完成步骤保存检查点；只有具备去重或结果对账契约时才重试副作用，因为副作用完成后发生崩溃会让结果变得未知。只有权威状态确认工作已停止，取消才是终态；客户端断线或收到取消请求确认都不足以证明这一点。

## Related notes / 相关笔记

- [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) owns transport selection, SSE framing, and wire behavior.
- [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) owns browser-side partial output, terminal events, and local cancellation.
- [Confirming request outcomes / 确认请求结果](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) explains deadlines, retry, and idempotency.
- [Database Fundamentals / 数据库基础](../../engineering-foundations/databases/database-fundamentals.md) covers durable application state, transactions, isolation, and recovery.
- [AI System Design Interview Questions / AI 系统设计面试题](./ai-system-design-interview-questions.md) applies these production mechanisms to end-to-end design cases.

**Sources / 来源：** [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) defines idempotent HTTP method semantics, and [§15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) says `202 Accepted` does not mean processing is complete. Temporal's [Workflow replay guide](https://docs.temporal.io/workflows) and [Event History guide](https://docs.temporal.io/encyclopedia/event-history) describe one runtime's deterministic orchestration replay and recorded activity results. These sources support the mechanisms described here; the example API, states, and names are synthetic application choices.
