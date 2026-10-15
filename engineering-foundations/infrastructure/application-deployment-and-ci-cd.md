# Application Deployment and CI/CD / 应用部署与持续交付

A production deployment is a controlled change to an immutable application artifact while persistent data and external effects keep their own lifecycles. Cloud providers can operate infrastructure and managed-service machinery; the application team still owns access policy, data semantics, workload limits, and recovery decisions. / 生产部署是在持久数据和外部副作用各自持续存在的前提下，受控地替换不可变应用产物。云厂商可以管理基础设施和托管服务，但应用团队仍负责访问策略、数据语义、负载边界和恢复决策。

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

## Failure and cost model / 故障与成本模型

| Boundary / 边界 | Failure to plan for / 需要考虑的故障 | Cost or limit to watch / 成本或限制 |
|---|---|---|
| Load balancer and network / 负载均衡与网络 | Bad route or listener, no healthy targets, blocked egress, or an expired certificate. | Requests and processed bytes, public addresses, NAT gateways, and cross-zone or internet data transfer. |
| Compute / 计算 | Startup failure, crash loop, CPU/memory saturation, or slow scale-out. | Minimum replicas and CPU/memory time; autoscaling cannot create capacity instantly. |
| Database / 数据库 | Exhausted connections, lock contention, storage or I/O limits, or failover delay. | Provisioned compute, storage, I/O, replicas, and retained backups. |
| Object storage / 对象存储 | Permission errors, unavailable routes, unexpectedly public objects, or unbounded retention. | Stored bytes, requests/retrieval, lifecycle transitions, replication, and outbound transfer. |
| Queue and workers / 队列与工作进程 | Duplicate or delayed delivery, poison messages, or growing backlog. | Requests, retained messages, worker compute, and the delay before backlog drains. |

Track each boundary with a useful signal: request errors and latency at ingress, ready replica count and saturation for compute, connection/query pressure for the database, request errors and object growth for storage, and oldest-message age plus dead-letter count for a queue. Cost estimates should include idle minimums and peak headroom as well as per-use storage, requests, and data movement; a service with a low unit price can still be expensive when retries or egress multiply the workload.

## One artifact from checks to production / 一个产物经过检查再到生产

Use one generic path and adapt the checks to actual regression risks:

~~~text
commit
  -> static/type checks -> unit and integration checks -> production build
  -> test the built artifact -> publish it with commit and content identity
  -> deploy that same artifact to staging -> smoke/browser check
  -> protected production gate -> gradual traffic shift -> observe and complete
~~~

Build once, then promote the same artifact. For a container, record and deploy its immutable digest rather than a mutable tag; for a static bundle, retain a checksum or release identifier with the emitted files. Rebuilding separately for staging and production weakens the claim that the tested bits are the deployed bits. If frontend configuration is compiled into the bundle, that bundle is environment-specific; a shared artifact needs safe public runtime configuration. Values shipped to a browser are public, never secrets.

Inject secrets at runtime from a secret store or protected deployment environment, and give the deployment identity only the permissions needed for its target. Keep non-secret environment configuration separate from the image. A deployment environment can also restrict source branches, protect production with approval, and scope access to environment secrets; these controls protect the release gate, while credentials still need rotation and least privilege.

Readiness is a traffic gate: an instance should receive requests only when it can serve its assigned work. Liveness is a restart signal for a process that cannot recover on its own. Exact probe behavior varies by platform; do not make liveness depend on every transient downstream service, since a database outage can then trigger a restart storm. Roll out gradually when the platform and workload permit it, watch a small set of error, latency, and saturation thresholds, and stop or redeploy the last known-good artifact when they cross the release limit. A green process probe alone does not prove the user journey works.

Database changes need an independent compatibility plan. A common expand-and-contract sequence adds a backward-compatible schema shape, deploys code that tolerates both shapes, backfills or dual-writes as needed, switches reads, and removes the old shape only after old code and the rollback window are gone. Run migrations as a controlled step rather than once per replica. Redeploying an older image does not reverse a schema migration, sent email, payment, or other external side effect; rollback may require a forward fix, an idempotent compensating action, or a tested restore plan. Restoring a backup can discard writes made after that backup, so it is a recovery decision rather than a routine application rollback.

For the frontend-specific type/test/build and critical-browser-check sequence, see [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md). The existing [Docker Operations / Docker操作参考](docker-operations.md) note covers image construction and local container mechanics.

**Interview answer / 面试回答：** Start with the request/data path and trust boundaries, then choose the least operational runtime that meets workload constraints. Build and verify one immutable artifact, inject runtime configuration and secrets, release behind readiness and monitored thresholds, and keep schema or external-state recovery separate from image rollback. / 先画出请求和数据路径及信任边界，再按负载约束选择运维负担最低的运行时。构建并验证一个不可变产物，运行时注入配置和密钥，在就绪检查与监控阈值保护下发布，并把数据库和外部状态的恢复方案与镜像回滚分开。

**Sources checked 2026-10-15:** [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html); [AWS VPC network example](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html); [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html); [Application Load Balancer health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html); [ECS deployment circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html); [Kubernetes v1.37 probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/); [Amazon RDS shared responsibility and query tuning](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/); [Amazon S3 access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-management.html); [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html); [Amazon SQS standard queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html); [SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html); [AWS Fargate pricing dimensions](https://aws.amazon.com/fargate/pricing/); [Amazon RDS pricing](https://aws.amazon.com/rds/pricing/); [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/); [Docker Compose in production](https://docs.docker.com/compose/how-tos/production/); [Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/); [GitHub Actions deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments); [CodeDeploy rollback behavior](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html); [Vite static deployment](https://vite.dev/guide/static-deploy.html). AWS examples document one provider's current service boundaries and are not universal defaults; verify the selected provider, service, region, and configuration.
