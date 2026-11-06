# 报表 API 与异步 worker 应由什么运行时承接？

在这次租户授权修复中，tenant-a 读取 report 42 应得到 200，tenant-b 猜中同一 ID 应得到 404。用户通过浏览器访问 application programming interface（应用程序接口，API）；当账户 acct-17 为 report 42 发起异步导出时，请求幂等键为 report-demo-208，API 在同一数据库事务写入 job（任务）job-demo-731、outbox（事务发件箱）意图并预留一个共享等待槽，再由 relay（转发进程）发布到 queue（队列），worker（工作进程）计算结果、写入私有对象并提交状态。只读请求和导出任务虽指向同一报表，但授权响应与 job 成功/失败是不同用户结果；每层的网络可达、身份权限、业务规则和恢复责任都不同。

~~~mermaid
flowchart TD
    B[浏览器] -->|HTTPS| L[可选 CDN / 负载均衡器]
    L --> A[私有 API 运行时]
    A -->|按当前主体查 tenant（租户）+ report| D[(数据库)]
    A -->|job + pending outbox + 预留等待槽，同一事务| D
    D --> R[Outbox relay]
    R -->|发布并等待 broker（消息代理）确认| Q[队列]
    Q -->|delivery（消息投递）| W[私有 worker]
    W --> D
    W --> O[私有对象存储]
    W -->|耐久结果状态后 ACK| Q
~~~

只读请求和异步导出均以 report 42 为报表资源；导出由账户 acct-17 发起，report-demo-208 是幂等键，job-demo-731 是持久任务 ID。导出结果先写入私有对象存储，只有数据库记录已提交对象引用后，授权 API 才能签发短期 signed URL（签名网址）。以 S3 预签名 URL 为例，授权检查发生在发放时；拿到 URL 的人可在其签发权限、对象策略和有效期允许时直接访问，它是一种 bearer 能力。应用后来撤销用户业务权限，不会自动撤销已发出的 URL；新发 URL 应设较短有效期，撤销底层签名凭据或改变资源策略也会影响既有 URL 的可用性。CDN 只是可选入口，含租户私有结果的响应不能按公共 URL 无条件共享缓存。通常 DNS 先把公共服务名解析为入口地址，再建立 HTTPS 连接；更完整的协议过程见[HTTP 与网络请求如何建立？](../networking/http-protocols-and-websockets.md)。路由、outbox 与 attempt（尝试号）状态细节见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 网络路径和身份策略分开

负载均衡器接收 HTTPS（安全超文本传输协议）并把请求送到配置的健康目标；计算服务运行 API 和 worker；数据库保存结构化状态；对象存储保存大文件；队列把可异步完成的工作和用户请求分离。浏览器可以通过范围受限、短期有效的签名网址直传或下载对象，不需要把 bucket（对象存储桶）设成公开。

网络路由、防火墙或安全组决定“谁能连到哪个地址”；工作负载身份和资源策略决定“该主体能对哪个资源做什么”；应用的授权规则再决定当前业务用户能否读取 tenant-a 的 report 42。这三个层次不能互相替代。常见拓扑只开放负载均衡器，API 仅允许来自负载均衡器，数据库只允许来自 API/worker，队列和对象存储只接受已授予相应任务身份的请求。本地 Compose 只能验证服务发现和网络连通；同一个镜像摘要进入 staging 后，还要经已装配的真实入口和测试身份复放 A→200、B→404，不能把镜像相同当成认证、配置或租户授权已验证。见[晋级验收](application-deployment-and-ci-cd.md)。

## 托管平台管理什么，应用仍拥有哪部分

| 层 | 平台通常负责 | 应用团队仍负责 |
|---|---|---|
| 计算 | 按服务方案提供主机维护、调度和运行环境 | 镜像/包、启动退出、资源上限、扩缩容策略、健康规则 |
| 数据库 | 所选配置包含的基础设施、补丁、备份或故障切换 | schema 和迁移、查询/连接行为、权限授予、保留期、恢复演练 |
| 对象存储 | 服务可用性及文档承诺的持久性机制 | 私有命名、保留/生命周期、上传上限、谁能拿 signed URL 及其过期/撤权策略 |
| 队列 | 在服务合同和配置限制内存储和投递消息 | 幂等处理、重试退避、毒消息处理、队列年龄和 DLQ 恢复 |

“托管”减少平台运维，但不会替工作负载选择安全配置。托管数据库不会修复缺索引查询或连接风暴；托管队列也不会使非幂等 worker 在重试时安全。

## 按任务时长、并发和停止行为选择运行时

一次有界、可重试的短报告任务可以由 function service（函数托管服务）执行，前提是最大执行时长、cold start（冷启动）、并发和触发器语义符合任务；长时间 API 与 queue worker 需要明确进程生命周期、并发界限和停止流程时，managed container service（托管容器服务）往往更适合；需要主机级控制或兼容遗留环境时，virtual machine（虚拟机，VM）提供控制权，但团队要承担系统补丁和容量管理。按峰值/稳态负载、最低常驻容量、启动延迟容忍度、长连接、执行上限和团队运维能力比较。serverless（无服务器计算）仍有状态、网络、配额和费用边界。

在这个报表例子里，HTTP API 要持续接收读请求，worker 要等队列、处理 database（数据库）和对象存储，并在部署停止时完成或释放当前 delivery（消息投递）。因此可把 API 与 worker 作为分开的可扩缩容服务，同一镜像运行不同命令。只有导出任务明确有界且平台事件处理语义合适时，才把它拆为函数。Cloud Run functions 的代际、并发和时长限制见[托管函数何时适合报表任务？](../../archive/front-end/Deprecated_Interview_Notes/hosted-functions-tradeoffs.md)。

进程收到停止信号时，先让 readiness probe（就绪探针）报告未就绪、停止接入新请求或消息，再在宽限期内完成在途请求与其事务；已持久提交业务结果的消息可以 ACK，未提交结果的消息按所选 broker 恢复契约处理。平台终止连接后，未确认 delivery 可被重投，但有效租约内的旧尝试仍由数据库状态保护，不能被新 worker 抢占。数据库连接池、线程、临时文件和 telemetry exporter（遥测导出器）都要有明确清理。具体 stop signal、async cancellation（异步取消）与资源释放依运行时和平台实现；容器 health probe（健康探针）的职责由[容器发布检查](application-deployment-and-ci-cd.md)说明，消息交接则由[发布确认与消费者 ACK](../reliability/queue-delivery-and-acknowledgement.md)说明。

## 用失败信号和成本边界检查组件

| 边界 | 计划中的失败 | 观察信号 | 成本/限制 |
|---|---|---|---|
| 负载均衡 / 网络 | 错路由、无健康目标、出站流量受阻、证书过期 | 请求错误、连接失败、目标健康数 | 请求与字节、网络地址转换、数据传输 |
| 计算服务 | 启动失败、崩溃循环、CPU/内存饱和、扩容慢 | 就绪实例、CPU/内存、重启与请求排队 | 最低副本和运行时间；扩容不是瞬时容量 |
| 数据库 | 连接耗尽、锁等待、I/O/存储或故障切换 | 连接池等待、连接数、查询时延、锁 | 计算、存储、I/O、备份保留 |
| 对象存储 | 权限错误、路由故障、对象意外公开、无限保留 | API 错误、对象增长、下载量 | 存储、请求、生命周期、复制、出站流量 |
| 队列 / worker | 重复/延迟投递、毒消息、积压上升 | 最老消息年龄、队列深度、未确认数、死信队列 | 保留消息、worker 计算、积压排空时间 |

平台容量与业务结果要分开观察。CPU 不高并不能证明 report 42 可正确读取；queue 有消费者也不代表报表已经成功。可观测性章会把这些组件信号与用户的 request/job 结果连接起来。

> [!info]- 来源
> - 网络与身份责任：AWS Well-Architected [Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) 和 [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)，checked 2026-11-06；这是 AWS 实例，其他平台的身份模型不同。
> - 托管函数的 warm runtime、实例复用与重试：AWS Lambda [Execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) 与 [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html)，checked 2026-11-06；内存缓存可复用但不能作为跨执行持久状态的事实限于 Lambda 运行时。
> - 对象授权路径：Amazon S3 [access management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-management.html) 和[presigned URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)，checked 2026-11-06；签名 URL 可给短期访问，不代表 bucket 公开。
> - 运行探针：Kubernetes 官方 [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)，checked 2026-11-06；probe 作用依平台，readiness 影响流量，liveness 可触发重启。
> - 证据和术语按具体平台合同适用；本文图是通用架构示意，不代表任何已部署系统。
