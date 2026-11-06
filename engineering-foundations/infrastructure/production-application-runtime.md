# How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？

Trace compute, networking, and storage along the request path. Managed infrastructure can operate a component, while the application still defines its data, access, workload and recovery policy. / 沿请求路径定位计算、网络和存储。托管基础设施可以代为运行组件，应用仍需定义数据、权限、负载和恢复策略。

## Request and data path / 请求与数据路径

For a typical web application, the browser talks only to public entry points; server-side services reach databases, object storage, and queues through controlled routes and identities:

~~~text
Name lookup, before the connection:
Browser -- DNS query for app.example --> resolver
resolver -- CDN / load-balancer address --> Browser

HTTPS request:
Browser -- HTTPS --> CDN (optional) --> public load balancer
                                          |
                                          v
                                 private API compute
                                  /      |       \
                             database  objects    queue --> workers
~~~

The load balancer terminates or forwards HTTPS and sends requests only to configured targets. Compute runs the API and workers. A database stores structured state, object storage holds large files, and a queue separates work that can finish asynchronously. A browser may upload or download an object through a narrowly scoped, expiring signed URL; that does not require making the storage bucket public.

Network reachability and authorization are separate checks. A route table, firewall or security group decides which network paths exist; an identity and resource policy decides which actions a reachable principal may perform. A common layout exposes only the load-balancer listener, permits API traffic from the load balancer, and permits database traffic only from the API. Keep data services private where the provider supports it, and add controlled outbound access or private service endpoints only when required. A task or workload identity should receive only the actions and resources it needs; application users still need application-level authorization. / 网络可达不等于有权访问：网络规则控制通信路径，IAM 与资源策略控制主体能执行的操作。应用运行身份应只获得所需资源和操作权限；业务用户的授权仍由应用负责。

## Managed service and application responsibilities / 托管服务与应用责任

| Layer / 层 | Provider or platform manages / 平台管理 | Application team owns / 应用团队负责 |
|---|---|---|
| Compute / 计算 | Underlying hardware and, depending on the offer, host maintenance and scheduling. | Image or package, startup and shutdown behavior, resource limits, scaling policy, and application health. |
| Database / 数据库 | Database service infrastructure and only the backups, patching, and failover included in the selected configuration. | Schema and migrations, query and connection behavior, access grants, retention choices, and restore testing. |
| Object storage / 对象存储 | Storage service availability and documented durability mechanisms. | Object naming, privacy, retention/lifecycle, upload limits, and who receives a signed URL. |
| Queue / 队列 | Message storage and delivery within service guarantees and configured limits. | Idempotent processing, retry/backoff, poison-message handling, queue age, and dead-letter recovery. |

“Managed” removes some infrastructure work; it does not choose safe defaults for the workload. Read the service contract and configuration: automated backups, retention, public access, network placement, and failover behavior are often selectable. A managed database cannot fix an unindexed query or a connection storm, and a managed queue cannot make a non-idempotent consumer safe to retry.

Choose a runtime by workload constraints. A managed application platform or function service can reduce host operations for ordinary stateless APIs or bounded event-driven jobs, subject to its execution, startup, and networking limits. A managed container service fits long-running APIs and queue workers when packaging and process control matter. Use virtual machines when the workload needs host-level control or a legacy environment, and budget for operating-system patching and capacity management. Compare steady and peak load, required minimum capacity, startup/cold-start tolerance, execution duration, portability, and the team’s ability to operate the platform; “serverless” does not mean state-free or cost-free.

### What the runtime still leaves to the application / 运行平台仍留给应用的责任

A managed function service owns the execution infrastructure, while the application owns durable state, resource cleanup and idempotent behavior across retries. For example, AWS Lambda may reuse an execution environment. A cached client can reduce setup time on a warm call. An in-memory counter in that environment cannot be the authoritative history across invocations, concurrent workers, or restarts. Persist progress externally. / 云函数平台可复用执行环境，应用仍要把持久状态、重试语义与资源清理设计清楚。

Compare duration, concurrency, cold starts, billing and long-lived connections against the selected provider and plan. Choose a function for a bounded event-driven job when those limits fit. For long-lived connections or jobs that may outlast an invocation, compare an API or worker runtime with explicit process and shutdown controls. [AWS Lambda execution lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) · [Lambda application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html) · [API retries and uncertain outcomes](../reliability/api-reliability-and-async-delivery.md)

## Failure and cost model / 故障与成本模型

| Boundary / 边界 | Failure to plan for / 需要考虑的故障 | Cost or limit to watch / 成本或限制 |
|---|---|---|
| Load balancer and network / 负载均衡与网络 | Bad route or listener, no healthy targets, blocked egress, or an expired certificate. | Requests and processed bytes, public addresses, NAT gateways, and cross-zone or internet data transfer. |
| Compute / 计算 | Startup failure, crash loop, CPU/memory saturation, or slow scale-out. | Minimum replicas and CPU/memory time; autoscaling cannot create capacity instantly. |
| Database / 数据库 | Exhausted connections, lock contention, storage or I/O limits, or failover delay. | Provisioned compute, storage, I/O, replicas, and retained backups. |
| Object storage / 对象存储 | Permission errors, unavailable routes, unexpectedly public objects, or unbounded retention. | Stored bytes, requests/retrieval, lifecycle transitions, replication, and outbound transfer. |
| Queue and workers / 队列与工作进程 | Duplicate or delayed delivery, poison messages, or growing backlog. | Requests, retained messages, worker compute, and the delay before backlog drains. |

Track each boundary with a useful signal: request errors and latency at ingress, ready replica count and saturation for compute, connection/query pressure for the database, request errors and object growth for storage, and oldest-message age plus dead-letter count for a queue. Cost estimates should include idle minimums and peak headroom as well as per-use storage, requests, and data movement; a service with a low unit price can still be expensive when retries or egress multiply the workload.

[Back to the main question / 返回主问题](application-deployment-and-ci-cd.md).
