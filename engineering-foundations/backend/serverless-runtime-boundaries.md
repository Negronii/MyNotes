# What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？

Serverless lets a provider manage execution infrastructure through a function or managed runtime interface; servers still exist. The application still owns durable state, idempotency, resource cleanup, and correctness across retries. Limits, concurrency, billing, cold starts, and environment reuse depend on the selected provider and configuration. / 无服务器计算让服务商通过函数或托管运行时管理执行基础设施，但服务器仍然存在。应用仍需负责持久状态、幂等性、资源清理和跨重试的正确性。限制、并发、计费、冷启动与环境复用取决于具体服务商和配置。

**Key terms / 关键术语：** serverless / 无服务器计算；execution environment / 执行环境；cold start / 冷启动；ephemeral state / 临时状态。

## Provider-managed execution boundary / 服务商管理的执行边界

Timeouts, concurrency limits, billing, cold-start latency, and state-reuse behavior depend on the provider, product, runtime, region, and configuration. Do not treat in-memory state as durable or assume an execution environment is discarded after every invocation. For example, AWS Lambda documents that environments can be reused while advising applications to treat state as temporary and persist durable changes externally.

Serverless can suit event-triggered handlers or variable workloads when the provider's limits and cost model fit. Long-running work, persistent connections, predictable latency, and vendor-specific integrations require a comparison against other deployment models.

**Related notes / 相关笔记：** [Node.js runtime choices / Node.js 运行时选择](node-js-fundamentals.md) covers worker and process boundaries; [API timeout and safe retry / API 超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) covers durable operation state and idempotent retries.

**Sources / 来源：** AWS Lambda [execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) and [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html), checked 2026-10-15. Provider limits and runtime behavior change over time.
