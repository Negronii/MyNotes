# What trade-offs come with hosted functions? / 托管函数有哪些取舍？

A hosted function can reduce routine server administration and fit HTTP or event-driven work, but it remains backend compute with runtime limits, cold starts, scaling behavior, observability, and cost boundaries. Compare the specific platform generation and workload against a long-running service. / 托管函数可以减少日常服务器管理，并适合 HTTP 或事件驱动工作；但它仍是后端计算，受运行时限制、冷启动、扩缩容、可观测性与成本边界影响。应按具体平台代际和工作负载，与常驻服务比较。

The archived product example was Google Cloud Functions; Google documentation now calls the product Cloud Run functions. Platform benefits are conditional: bills can include minimum instances, builds, networking, storage, and logs; latency and scale depend on runtime, concurrency, region, and generation. Event sources may redeliver, so design idempotent handlers when the provider's delivery contract allows retries. A function does not remove the need for an API contract or trusted server-side authorization.

For Node.js serverless basics, see [Node.js Fundamentals](../../../engineering-foundations/backend/node-js-fundamentals.md); for artifact, release, and operational boundaries, see [Application Deployment and CI/CD](../../../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md).

**Sources checked 2026-10-15:** [Cloud Run functions](https://docs.cloud.google.com/functions/docs), [quotas and scaling](https://docs.cloud.google.com/functions/quotas), and [function triggers](https://docs.cloud.google.com/run/docs/function-triggers).
