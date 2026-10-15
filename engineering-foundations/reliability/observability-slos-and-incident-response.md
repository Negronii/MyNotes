# Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应

**Core model / 核心模型:** Start from the outcome users need, measure it with a clear service-level indicator, and use correlated metrics, traces, and logs to find which stage is failing. Metrics show the aggregate shape; a trace follows one request across stages; logs explain specific events. / 从用户需要的结果开始，用明确定义的服务等级指标衡量它，再用相互关联的指标、追踪和日志定位故障阶段。指标显示整体趋势，追踪串起单个请求的各阶段，日志说明具体事件。

**Key terms / 关键术语:** service-level indicator (SLI) / 服务等级指标；service-level objective (SLO) / 服务等级目标；service-level agreement (SLA) / 服务等级协议；error budget / 错误预算；trace / 分布式追踪；span / 跨度；cardinality / 基数。

**Core answer / 核心回答：** SLI 是符合资格的用户请求中“好事件 / 总事件”的实测比例；SLO 是该比例在指定时间窗内应达到的目标；SLA 是对外业务协议，可能规定计量方式和未达标后果。例：30 天内 10,000 次有效请求中，9,940 次在 400 ms 内成功，SLI 为 99.4%；若 SLO 为 99.5%，错误预算是 `(1 − 99.5%) × 10,000 = 50` 次坏事件，实际 60 次即超出 10 次。告警后先确认用户影响和分母，再沿 trace 定位慢/失败阶段并查关联日志；根据证据缓解，以用户 SLI 和依赖信号验证恢复，并记录原因与后续改进。

## Follow one request through three signals / 用三种信号跟踪一个请求

Consider a generic catalog lookup: `client → API edge → catalog service → cache/database → response`. Instrument the boundaries that make up this user action. Propagate trace context across service calls so spans from the edge, service, and database client can be assembled into one trace. A span is one timed operation; parent-child spans show which sub-operation took time. Context propagation connects spans across process and network boundaries. [OpenTelemetry: traces](https://opentelemetry.io/docs/concepts/signals/traces/) and [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/).

| Signal / 信号 | What it answers / 回答的问题 | Example for the lookup / 查询示例 |
|---|---|---|
| **Metrics / 指标** | Is the service broadly healthy, and when did behavior change? | Count eligible requests and failures; measure end-to-end duration, dependency duration, in-flight work, and resource saturation over time. Metrics aggregate measurements, so they are efficient for trends and alerts. |
| **Traces / 追踪** | Which stage made this particular request slow or unsuccessful? | One trace contains a root request span and child spans for cache and database work. Compare their durations and statuses to see where time accumulated. |
| **Logs / 日志** | What event or decision happened at that stage? | A structured record such as `cache_lookup=miss` or `database_timeout` adds event detail. Include the active `trace_id` and `span_id` when available so the record can be found from the trace. |

Start with the metric to find the affected time window, route, and outcome. Then inspect a representative slow or failed trace and follow its child spans. Use the trace and span identifiers to find detailed log events from the same request. For example, an edge metric may show that catalog lookups are slow, a trace may show most of one request's 700 ms elapsed in the database span, and a correlated log may show that the connection pool waited before timing out. The metric establishes scope, the trace locates the stage, and the log gives event detail. [OpenTelemetry: signals](https://opentelemetry.io/docs/concepts/signals/) describes the three signal types; its [logs guide](https://opentelemetry.io/docs/concepts/signals/logs/) describes correlating logs with active traces and spans.

Signals have different coverage. Metrics can remain useful when traces are sampled, but a missing trace is not proof that no request or failure occurred. Check telemetry freshness and instrumentation coverage before treating silence as recovery.

## Keep telemetry safe and bounded / 让遥测信息安全且有界

Use stable, low-cardinality metric dimensions such as route template (`/catalog/{itemId}`), response class, region, and dependency. Do not attach `request_id`, `trace_id`, user or tenant IDs, raw URL paths, search terms, prompts, or other per-request values to metric measurements. Every distinct dimension combination can create another time series and increase aggregation cost; OpenTelemetry's metrics guide warns that user IDs and raw paths can cause unbounded cardinality. [OpenTelemetry: metrics and cardinality limits](https://opentelemetry.io/docs/concepts/signals/metrics/).

Request and trace identifiers are useful correlation fields in logs and traces, where each record is already about an individual event or operation. Treat them as sensitive linkage data: restrict access and retention, and never log credentials, authorization headers, cookies, or raw user content just to make a failure searchable. Prefer stable route names and bounded result categories; redact or omit fields that are not needed to diagnose the service.

## Define a user outcome and its budget / 定义用户结果与预算

An **SLI** is a measured indicator of a service outcome, commonly a ratio of good events to eligible events. An **SLO** is the target for that indicator over a stated period. An **SLA** is an external business agreement that can specify measurement rules and consequences if commitments are missed; an internal SLO is not automatically an SLA. [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/) defines event-based SLIs, explains error budgets, and distinguishes an SLA as a business contract.

**Synthetic example / 合成示例.** Suppose a catalog lookup service chooses the following request-based SLI over a rolling 30-day window:

- **Eligible events:** every authenticated, syntactically valid catalog lookup accepted at the public API edge. Exclude synthetic health checks. Keep service errors, timeouts, and requests with no completed response in the denominator.
- **Good event:** the edge completes a successful response in at most 400 ms from acceptance.
- **SLI:** good eligible events ÷ all eligible events.
- **SLO:** at least 99.5% of eligible events are good in the rolling 30-day window.

If the window contains 10,000 eligible lookups and 9,940 are good, the SLI is `9,940 ÷ 10,000 = 99.4%`. The error budget is `1 − 0.995 = 0.5%`, or `10,000 × 0.005 = 50` bad events for this traffic volume. The 60 bad events observed exceed that budget by 10. This event-based calculation weights each request equally; it does not prove every region or user group had the same experience. The chosen edge measurement also does not include the user's device or network after the edge completes its response. Google SRE recommends specifying both the user outcome and how it is measured, because measurement boundaries change what failures are visible.

The SLI must keep its denominator and eligibility rules stable: dropping timeouts or slow successes would make the number look better while excluding users who did not receive a timely result. Report request volume with the ratio, and inspect meaningful low-cardinality slices such as region or route when an overall number hides a localized failure.

## Alert, investigate, mitigate, and learn / 告警、调查、缓解与复盘

For the example SLO, a focused alert could fire when at least 100 eligible lookups occur in a rolling 10-minute window, fewer than 99% are good, and that condition persists for 5 minutes. A minimum event count reduces noise from tiny samples. The alert should carry the SLI numerator, denominator, time window, affected route/region, and links to the relevant metric and trace views. Page when this user-outcome condition holds; internal component signals help explain the cause.

When it fires:

1. **Confirm impact and scope.** Check event counts, SLI trend, error types, route/region, and recent changes. Make sure telemetry is arriving and the denominator still matches the SLI definition.
2. **Locate the stage.** Compare stage and dependency latency, errors, saturation, and in-flight work. Inspect affected traces, then use trace IDs to read the specific correlated logs. For asynchronous work, inspect queue age, depth, retries, and completion outcomes in the existing [API reliability and asynchronous delivery](api-reliability-and-async-delivery.md) note.
3. **Mitigate the user impact.** Choose the smallest safe action supported by evidence, such as rolling back a change that matches the onset or temporarily reducing load on a saturated dependency. Record the action and its expected effect; do not add retries blindly if they can amplify overload.
4. **Verify recovery.** Confirm that the user-facing SLI returns above the alert threshold with adequate traffic, and check the affected stage and dependency signals for continuing saturation or error growth. A quiet alert alone is not evidence that the service recovered.
5. **Follow up.** Record the user impact and time window, the causal mechanism, the mitigation, and a small set of owned changes to prevent recurrence or improve detection. Link the incident to relevant tests and telemetry gaps.

Use the SLO to guide tradeoffs. For AI-backed flows, pair operational signals with task quality and cost measures already covered in [AI application architecture](../../ai-engineering/systems/ai-application-architecture.md) and [LLM evaluation methods](../../ai-engineering/evaluation/llm-evaluation-methods.md). A healthy HTTP success and latency SLI does not prove that generated answers are useful or correct.

## Sources / 来源

- OpenTelemetry's unversioned concept pages, checked 2026-10-15: [Signals](https://opentelemetry.io/docs/concepts/signals/) (last modified 2026-03-10), [Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) (2026-04-23), [Traces](https://opentelemetry.io/docs/concepts/signals/traces/) (2026-01-14), [Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/) (2026-07-02), [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) (2026-08-07), and [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) (2026-08-10).
- [Google SRE Workbook, Chapter 2: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15.
