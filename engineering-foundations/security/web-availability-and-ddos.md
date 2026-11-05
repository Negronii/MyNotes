# How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？

Distributed denial-of-service attacks use traffic or expensive requests to exhaust network, service, or application resources. Mitigation depends on the attack layer and available capacity; no single application control guarantees protection. Use layered edge filtering and provider capacity, rate limits and quotas, caching where it is safe, bounded work, and monitoring. Application code can reject abusive work early, but large traffic floods need network and provider-level capacity as well. / 分布式拒绝服务攻击通过流量或高成本请求耗尽网络、服务或应用资源。缓解措施取决于攻击层级和可用容量，单一应用控制不能保证防护。应组合边缘流量过滤与服务商容量、速率限制和配额、安全场景中的缓存、有界工作及监控。应用代码可以尽早拒绝滥用请求，但大规模流量洪峰还需要网络和服务商层的容量。

**Key terms / 关键术语：** denial of service / 拒绝服务；rate limit / 速率限制；quota / 配额；admission control / 准入控制；bounded work / 有界工作。

**Sources / 来源：** CISA [Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf), checked 2026-11-05, for layered mitigation and rate limitation.

**Related notes / 相关笔记：** [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md) explains worker slots, admission, and queue limits; [API timeout and safe retry / API 超时后的结果确认与安全重试](../reliability/api-reliability-and-async-delivery.md) explains how retries can amplify overload.
