# 报表 API 与异步 worker 应由什么运行时承接？

在这次租户授权修复中，tenant-a 读取 report 42 应得到 200，tenant-b 猜中同一 ID 应得到 404。用户通过浏览器访问 application programming interface（应用程序接口，API）；当账户 acct-17 为 report 42 发起异步导出时，请求幂等键为 report-demo-208，API 在同一数据库事务写入 job（任务）job-demo-731、outbox（事务发件箱）意图并预留一个等待槽。等待槽是数据库维护的排队准入额度：每个未被领取的排队轮次占一个，接管重排时重新预留，领取时释放，不是 broker 的 prefetch 或锁。relay（转发进程）发布到 queue（队列），worker（工作进程）计算结果、写入私有对象并提交状态。只读请求和导出任务虽指向同一报表，但授权响应与 job 成功/失败是不同用户结果；每层的网络可达、身份权限、业务规则和恢复责任都不同。

~~~mermaid
flowchart TD
    B[浏览器] -->|HTTPS| C[可选 CDN]
    C --> L[负载均衡器：本图的入口]
    L --> A[私有 API 运行时]
    A -->|按当前主体查 tenant（租户）+ report| D[(数据库)]
    A -->|job + pending outbox + 预留数据库排队额度，同一事务| D
    D --> R[Outbox relay]
    R -->|发布并等待 broker（消息代理）确认| Q[队列]
    Q -->|delivery（消息投递）| W[私有 worker]
    W --> D
    W --> O[私有对象存储]
    W -->|耐久结果状态后 ACK| Q
~~~

只读请求和异步导出均以 report 42 为报表资源；导出由账户 acct-17 发起，report-demo-208 是幂等键，job-demo-731 是持久任务 ID。worker 用 task role（任务角色）把结果写入私有对象；只有数据库记录已提交对象引用后，拥有读取权限的下载 API 才能签发短期 signed URL（签名网址）。浏览器不持有 worker 的 task role；S3 预签名 URL 把签发身份在有效期内可重复使用的受限读取能力交给持有 URL 的浏览器。应用后来撤销用户业务权限，不会自动撤销已发出的 URL；新发 URL 应设较短有效期，撤销底层签名凭据或改变资源策略也会影响既有 URL。CDN 可选地位于本图负载均衡器之前，含租户私有结果的响应不能按公共 URL 无条件共享缓存。通常 DNS 先把公共服务名解析为入口地址，再建立 HTTPS 连接；更完整的协议过程见[HTTP 与网络请求如何建立？](../networking/http-protocols-and-websockets.md)。路由、outbox 与 attempt（尝试号）状态细节见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)。

## 网络路径和身份策略分开

负载均衡器接收 HTTPS（安全超文本传输协议）并把请求送到配置的健康目标；计算服务运行 API 和 worker；数据库保存结构化状态；对象存储保存大文件；队列把可异步完成的工作和用户请求分离。浏览器可以通过范围受限、短期有效的签名网址直传或下载对象，不需要把 bucket（对象存储桶）设成公开。

网络路由、防火墙或安全组决定“谁能连到哪个地址”；工作负载身份和资源策略决定“该主体能对哪个资源做什么”；应用的授权规则再决定当前业务用户能否读取 tenant-a 的 report 42。这三个层次不能互相替代。常见拓扑只开放负载均衡器，API 仅允许来自负载均衡器，数据库只允许来自 API/worker。worker 的 task role 只需要写入报表前缀；签发下载 URL 的 API 还需要相应读取权限，S3 按签发凭据授权预签名请求，浏览器只持有短期 bearer URL，不需加入服务角色。队列只接受被授予权限的服务身份。本地 Compose 只能验证服务发现和网络连通；同一个镜像摘要进入 staging 后，还要经已装配的真实入口和测试身份复放 A→200、B→404，不能把镜像相同当成认证、配置或租户授权已验证。见[晋级验收](application-deployment-and-ci-cd.md)。

## 托管平台管理什么，应用仍拥有哪部分

| 层 | 平台通常负责 | 应用团队仍负责 |
|---|---|---|
| 计算 | 按服务方案提供主机维护、调度和运行环境 | 镜像/包、启动退出、资源上限、扩缩容策略、健康规则 |
| 数据库 | 所选配置包含的基础设施、补丁、备份或故障切换 | schema 和迁移、查询/连接行为、权限授予、保留期、恢复演练 |
| 对象存储 | 服务可用性及文档承诺的持久性机制 | 私有命名、保留/生命周期、上传上限、谁能拿 signed URL 及其过期/撤权策略 |
| 队列 | 在服务合同和配置限制内存储和投递消息 | 幂等处理、重试退避、毒消息处理、队列年龄和死信队列（DLQ）恢复 |

“托管”减少平台运维，但不会替工作负载选择安全配置。托管数据库不会修复缺索引查询或连接风暴；托管队列也不会使非幂等 worker 在重试时安全。

## 按任务时长、并发和停止行为选择运行时

一次有界、可重试的短报告任务可以由 function service（函数托管服务）执行，前提是最大执行时长、cold start（冷启动）、并发和触发器语义符合任务；长时间 API 与 queue worker 需要明确进程生命周期、并发界限和停止流程时，managed container service（托管容器服务）往往更适合；需要主机级控制或兼容遗留环境时，virtual machine（虚拟机，VM）提供控制权，但团队要承担系统补丁和容量管理。按峰值/稳态负载、最低常驻容量、启动延迟容忍度、长连接、执行上限和团队运维能力比较。serverless（无服务器计算）仍有状态、网络、配额和费用边界。

在这个报表例子里，HTTP API 要持续接收读请求，worker 要等队列、处理 database（数据库）和对象存储，并在部署停止时完成或释放当前 delivery（消息投递）。因此可把 API 与 worker 作为分开的可扩缩容服务，同一镜像运行不同命令。只有导出任务明确有界且平台事件处理语义合适时，才把它拆为函数。Cloud Run functions 的代际、并发和时长限制见[托管函数何时适合报表任务？](../../archive/front-end/Deprecated_Interview_Notes/hosted-functions-tradeoffs.md)。

进程收到停止信号时，API 服务先把 readiness probe（就绪探针）标为未就绪，让负载均衡器停止送入新的 HTTP 请求；这不会自动停止独立 worker 消费队列。worker 要主动暂停 broker consumer 或停止取新 delivery，再在宽限期内完成当前任务或中止并释放未确认 delivery。只在结果或终态已持久提交后 ACK；未提交的 delivery 让 broker 按其恢复契约重投，数据库租约恢复器另负责接管仍记录为 running 的 job。API 的 readiness 控制入口流量，worker 的 pause/cancel 控制消息领取，二者不能互相替代。数据库连接池、线程、临时文件和 telemetry exporter（遥测导出器）都要有明确清理。具体 stop signal、async cancellation（异步取消）与资源释放依运行时和平台实现；容器 health probe（健康探针）的职责由[容器发布检查](application-deployment-and-ci-cd.md)说明，消息交接则由[发布确认与消费者 ACK](../reliability/queue-delivery-and-acknowledgement.md)说明。

## worker 凭据怎样注入、轮换并撤销？

报表系统有两个独立进程：发送 worker 用 HMAC（基于哈希的消息认证码）密钥为 Webhook（回调通知）签名；接收服务用允许的 keyId→密钥映射验签。合成协议要求同一 endpoint/source 的发送端与接收端持有对应相同密钥，但每个服务只取得自己需要的密钥值和授权范围，使用独立的 ECS execution role（执行角色）注入各自 Secret ARN。短期工作负载身份、共享消息密钥和某个用户授予第三方的 OAuth grant（OAuth 授权）生命周期不同，不能混成一个环境变量或角色。

以 Amazon ECS 为一个具体部署例子，容器镜像只包含代码，task definition（任务定义）引用 Secrets Manager 中的密钥，不放密钥值。ECS 的 task execution role（任务执行角色）给 ECS agent 启动任务时读取所需 Secret ARN 的权限；该角色的权限不直接交给容器内代码。应用调用 AWS 服务时使用另一个 task role（任务角色），例如只允许向指定报表前缀写对象。角色分开并按服务授予最小动作与资源范围，避免 worker 因共享角色取得无关 API 或 Secret 权限。ECS 任务角色提供短期工作负载凭据，AWS SDK 通过容器凭据接口取得并刷新它们；应用不应把这组 AWS 凭据再复制成长期静态键。

接收 ECS service 在启动时把验证器允许的 keyId→密钥映射注入 `WEBHOOK_VERIFY_KEYS_JSON`；签发 ECS worker 只注入当前 keyId 对应的 `WEBHOOK_SIGNING_KEY` 与 keyId。两服务用不同的 task definition 和 execution role，只能读取各自命名的 Secret ARN；task role 不承担读取 Secret 的职责。ECS 的 `valueFrom` 可以指向完整 secret、JSON key、version-stage 或 VersionId；本例不固定 VersionId，让它跟随 `AWSCURRENT`。移动该 staging label 后，正在运行任务的环境不会自动更新；要启动新 task 或强制 service 滚动部署，进程才会读到新值。若 task definition 固定了 VersionId，则必须先更新 task definition revision 指向新版本，再替换任务。ECS 官方还指出容器内的应用、日志和调试工具都可能访问这些环境变量，所以不能 dump 全部环境、在异常信息中回显配置，也不应把密钥加入镜像层、版本库、任务参数明文、前端 bundle、请求日志或模型 prompt/checkpoint。相同签名、重试和接收路径见[Webhook 接收方怎样验证并可靠受理？](../reliability/webhook-delivery-and-verification.md)。

正常轮换按“接收端先兼容、发送端再切换、接收端最后移除旧键”进行。本合成 Webhook outbox 保存未签名原文，发送 worker 每次新尝试才签名：

1. 为该 endpoint/source 生成新 keyId 和新密钥；把接收端的 `WEBHOOK_VERIFY_KEYS_JSON` 更新为旧、新双键映射，移到新 `AWSCURRENT` 并强制部署 receiver task。若 task definition 固定 VersionId，则发布引用新版本的 revision；确认旧 receiver task 已退出。
2. 更新发送端 `WEBHOOK_SIGNING_KEY` 和当前 keyId，替换 sender task。Sender 每次尝试都用新 key 重签相同 eventId 和正文；等旧 sender task 全部退出并记录所有旧 sender 实例签名时间戳的最大值；只有当每个仍可能接收旧请求的 receiver 时钟都已晚于该最大时间戳加 300 秒，且最大在途请求处理时限也已过，才可移除旧键。不能只从最后一次发送起等待 300 秒；实际轮换还要覆盖已知时钟偏差。
3. 将接收端验证映射更新为仅新键，并强制替换 receiver task；若固定 VersionId，更新 task definition revision。确认旧 receiver task 退出后，旧密钥才不再驻留于任一运行进程。过期 Secrets Manager 版本按保留策略移除。
4. 如果实现预先排队已签名请求而非未签名正文，就要在旧签名失效前重新签名这些请求，或等其失效后再移除旧键。

移动 `AWSCURRENT` 不会改变正在运行的环境变量；每个使用该 Secret 的 sender/receiver service 都要部署新 task。若双方引用 VersionId，则各自 task definition 都要发布指向该版本的新 revision。

若 key 已泄漏，紧急路径不保留新旧双接受窗口。新 key 应预先生成；先暂停端点交付并阻断入口或停止旧 receiver task，再部署只含新 key 的 receiver task；随后把 sender 切到新 key 并替换旧 sender task，确认旧进程均退出后恢复交付。若 task definition 固定 VersionId，两端都要更新 task definition revision。没有可用新 key 时立即撤销旧 key 并维持暂停，不为可用性继续接受泄漏密钥。发送端按撤销 keyId 找出未确认事件，只能在原 `createdAt + 30 天` 截止前，用原 eventId、原正文和新 attemptId 重签；换键不会重置期限。旧请求若已受理但响应丢失，持久 inbox 会识别重复；已确认 2xx 的事件不重放。删除 Secrets Manager 的值本身不能清除已注入进程中的副本，必须替换对应 receiver/sender task。对于能直接访问资源的其他凭据，还要在签发方或目标资源撤销授权；用户 OAuth access token 的撤销时机依 provider 契约处理。

用户 OAuth grant 属于另一个授权主体：它代表某个用户允许 Agent 或应用访问特定下游资源，必须按用户、租户、目标 audience（令牌受众）、scope（权限范围）与过期状态隔离，并在用户撤权后阻止新调用。它不是 ECS task role，也不是服务级 Webhook HMAC 密钥。OAuth 刷新 token 不进入统一 worker 环境、日志、模型上下文或恢复快照；运行时只按已绑定 grant 取用，撤权后依第三方 provider 契约停止或重新授权。短期工作负载身份不替代该用户 grant，也不能扩大用户授权范围。

分开审计 secret 注入与业务 API 调用。CloudTrail 的 Secrets Manager `GetSecretValue` 事件可用于查看 execution role 对 Secret ARN 的访问；再关联 task definition revision、task 启动和部署控制面记录。若 task definition 固定 VersionId，revision 能标出期望版本；若跟随 `AWSCURRENT`，需保存 staging label 变更和滚动部署时间线。不能假定 GetSecretValue 的 CloudTrail 记录含 taskArn 或响应返回的 VersionId。业务 SDK 以 task role 调 AWS API，其 CloudTrail session 可带 taskArn；这类业务调用审计不能替代 secret 注入审计。两条记录都不含密钥值，日志中也不得记签名原文。审计轨迹能定位谁在何时读取或启用了凭据，但不会自动证明权限最小；还要检查实际 IAM policy 与目标资源范围。

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
> - 一个具体注入/身份例子：AWS ECS [task role 最小权限与隔离说明](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)、[Task IAM role 的临时凭据交付与 taskArn 审计上下文](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)、[task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)，以及 AWS SDK [container credential provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-container-credentials.html) 和[标准 credential provider 自动续期](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html)，checked 2026-11-09。task role 供应用 SDK 调用云服务并取得/续期临时凭据，execution role 给 ECS agent 启动所需权限。
> - [ECS 注入 Secrets Manager 环境变量](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)，checked 2026-11-09：引用可指定 JSON key、version-stage 或 VersionId；stage 与 VersionId 不能同时指定。未固定 VersionId 且未指定 version-stage 时默认读取 `AWSCURRENT`。Secret 在 task 启动时注入，更新后须启动新 task 或强制服务部署，容器内应用、日志和调试工具可访问这些变量。其他云平台的读取、刷新和撤销语义不同。 [Secrets Manager GetSecretValue API](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html) 与 [Secrets Manager CloudTrail entries](https://docs.aws.amazon.com/secretsmanager/latest/userguide/cloudtrail_log_entries.html)，checked 2026-11-09：API response 含 VersionId，但 SecretString/SecretBinary 不进入 CloudTrail；审计不能把 API response 内容说成 CloudTrail 返回字段。
