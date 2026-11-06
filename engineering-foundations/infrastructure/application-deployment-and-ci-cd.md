# 如何晋级并回滚已验证的报表服务产物？

对 report 42 的租户范围修复，测试结果应绑定到固定的源码提交。continuous integration（持续集成，CI）在该提交上运行静态检查、单元测试、数据库测试和所需的消息代理检查；构建一次 container image（容器镜像），测试这份确切镜像，再把相同 digest（摘要）从 staging（预发布环境）晋级到 production（生产环境）。continuous delivery（持续交付）让通过门禁的产物随时可发布；continuous deployment（持续部署）则在规则满足后自动发布。部署回滚不能自动撤销数据库写入或远程副作用。

~~~mermaid
flowchart TD
    A[提交 c4f2a91] --> B[静态 + 单元 + 集成 + 契约测试]
    B --> C[构建一次并发布镜像]
    C --> D[保存 commit 与 image digest]
    D --> E[在 staging 部署相同 digest]
    E --> F[smoke / 数据库 / worker 检查]
    F --> G{生产环境门禁}
    G -->|通过| H[小流量 canary]
    H --> I{用户 SLI 和依赖信号在范围内？}
    I -->|是| J[逐步放到全部流量]
    I -->|否| K[停止放量并判断安全回退目标]
    G -->|未通过| L[不接触生产流量]
~~~

图里的 c4f2a91 是示意 commit。单平台镜像的 digest 标识该平台 manifest；多平台镜像索引 digest 标识一组平台 manifest，同一个索引摘要可能让 amd64 与 arm64 节点拉取不同平台的镜像内容。因此本例若说 staging/prod 运行相同镜像内容，前提是部署目标平台相同；跨架构发布须记录并核验每个目标平台解析到的 manifest digest。构建时间戳 tag、latest 或 staging/prod 两次独立 build 都不能替代摘要；需要审计的是目标平台实际运行的产物。

## 一次构建，逐级测试并记录产物身份

先在 pull request（合并请求，PR）上运行与变更风险匹配的检查：修复授权范围要有所有者/非所有者测试；数据库 schema（结构定义）变更要兼容旧数据与旧代码；worker 改动触及 acknowledgement（确认，ACK）时需要所选消息代理的集成测试。合并可能产生新的 merge commit，因此构建前要在最终合并提交上重跑必需检查，或确认 PR 检查验证的源码树与最终构建输入完全相同。随后 CI 从这个已验收的 commit（提交）构建一次镜像，并记录提交、依赖锁文件、构建器、基础镜像与镜像摘要。

例如 Buildx 可在构建并推送镜像时把构建 metadata 写到文件：

~~~bash
docker buildx build \
  --push \
  --metadata-file report-build.json \
  --tag registry.example.com/team/report-api:c4f2a91 \
  .
jq -r '."containerimage.digest"' report-build.json
~~~

该命令会构建并推送镜像；得到摘要后，把预发布和生产环境的目标都写成同一个不可变引用，如 `registry.example.com/team/report-api@sha256:...`。生产变更记录至少能回答：哪个提交生成了这个摘要、哪组检查针对它通过、当前哪个环境运行它。

在 staging（预发布环境）验证同一摘要时，用经真实入口和测试身份提供方装配的请求复放授权回归：tenant-a 读取 report 42 应返回 200 和预期报表；tenant-b 用自己的合法身份请求同一路径应返回 404。这里不能用客户端自填的租户头代替身份。tenant-a 得到 404 也是本次验收失败，不能因为 tenant-b 的合法拒绝状态也是 404 就把状态码集合当作成功判断。worker 的提交/ACK 检查覆盖另一条异步路径，不能代替这项用户读请求验收。

如果每个环境分别重建，即使源码提交相同，也可能遇到基础镜像、依赖、构建时间输入或构建器变化。一个具体镜像通过预发布环境后，应晋级它本身；运行时数据库地址、feature flag（功能开关）和 secret（密钥）通过受控配置注入，不把密钥烘进镜像。若有前端 bundle（前端打包文件），编译期环境配置不同会生成不同产物；若要逐环境晋级同一静态站点 bundle，应把非秘密配置作为运行时公开配置读取。无论何种方式，编译进 bundle 的值都对浏览器用户可见，不能作为密钥。静态站点没有容器镜像时，也可记录每次发布的 artifact ID（产物标识）或校验和，并在 staging 与 production 验证同一组文件。

## 将环境门禁、启动检查和渐进放量接起来

GitHub Actions environment（工作流环境）可以为 production 配置部署保护规则，例如要求审查者批准、限制可部署分支或控制环境密钥的访问。workflow（工作流）引用该环境的 job（任务）通过相应规则后才运行；这控制的是凭据和部署授权，不替代应用自己的流量安全判定。选用第三方 action（自动化步骤）时，固定已审核的完整 commit SHA（提交哈希）；tag 可移动。

发布前核对部署配置的 identity and access management（身份与访问管理，IAM）权限、网络路由、密钥来源、数据库迁移和目标镜像摘要。镜像本身不应包含数据库密码。一次数据库 migration（结构迁移）由独立、可观察的步骤执行，而不是每个 API replica（副本）启动时都执行。

readiness probe（就绪探针）判断实例是否可以接收流量；liveness probe（存活探针）判断进程是否卡在无法自愈的状态并可触发重启；startup probe（启动探针）给慢启动应用完成初始化的时间，成功前先不执行存活/就绪探针。不要让存活探针依赖每个暂时性的下游服务，否则数据库短暂故障可能让实例同时重启。绿色探针只能说明探针路径正常，还不能证明 report 42 的授权、结果对象或队列处理正确。

支持渐进发布的平台可以从一小部分真实流量开始，按用户 SLI（服务等级指标）、错误类别、延迟、容量与 queue age（队列消息年龄）比较新旧 revision（版本实例）。只在样本量、时间窗口和代表性任务足够时继续放量；新版本启动成功不等于用户旅程健康。具体平台可能采用滚动更新、blue-green（蓝绿发布）或 canary（金丝雀发布），其流量切换和自动判断机制并不相同。

## 回退代码时不要假设数据也回去了

如果新镜像导致 5xx、超时或 queue worker 持续失败，可以停止放量并回退到最近一个已完成且安全的应用版本。report 42 的租户隔离修复有安全意义：若旧版存在已知跨租户漏洞，回到旧 image 会重新开放数据风险。此时应先隔离受影响入口、禁用危险路径或前向修复，不能机械恢复成旧 digest。缓解选择需要 production trace、部署时间和权限测试共同支持，见[从报表服务信号定位发布故障](../reliability/observability-slos-and-incident-response.md)。

代码回退不等于数据库回滚。常用 expand-and-contract（扩展-收缩迁移）次序是：先加向后兼容的列、索引或表形态；部署同时接受新旧形态的代码；在可控事务或批次中回填并核对；切换读写；等旧 API 实例和旧 worker 全部退出、旧代码不再是回滚目标后，才删除旧形态。进入删除旧结构的收缩阶段前，要确认线上没有实例或 worker 再读写它，而且发布策略已不再考虑回滚到仍依赖该结构的旧版本。

镜像 rollback 不会撤销已经提交的 job、已上传且已引用的报告对象、已发送邮件或支付。若外部动作需要补偿，应使用有幂等键的明确补偿流程；恢复备份也可能丢失备份之后的新写入，是恢复决策，不是普通应用回滚。数据库与对象状态由各自备份、保留与审计边界负责。

> [!info]- 来源
> - GitHub Actions [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) 与[部署环境概念](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)，checked 2026-11-06：保护规则、required reviewers、branch 限制和环境 secrets 的授予时间；部署行为仍由具体 workflow/provider 决定。
> - GitHub Actions [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)，checked 2026-11-06：third-party Action 使用完整 commit SHA 的不可变发布方式与审查理由。
> - Docker Buildx [build --metadata-file](https://docs.docker.com/reference/cli/docker/buildx/build/)、[image digest](https://docs.docker.com/dhi/explore/security-concepts/digests/) 与[multi-platform images](https://docs.docker.com/build/building/multi-platform/)，checked 2026-11-06：push 返回的 registry digest、可移动 tag、索引摘要和各平台 manifest digest 的边界。
> - 探针：Kubernetes [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)，checked 2026-11-06：三种探针的不同动作；不同平台的配置语义须看其官方文档。
> - 自动回退实例：Amazon ECS [Deployment failure detection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-failure-detection.html) 与[deployment circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)，checked 2026-11-06：ECS circuit breaker 根据任务运行与已配置健康检查判断 steady state，CloudWatch alarm 可作另一类 failure detector；自动 rollback 需要配置，且回到上次 COMPLETED deployment。不是所有发布平台都采用相同条件。
> - 数据库兼容性：AWS blue/green 官方白皮书 [Decoupling schema changes from code changes](https://docs.aws.amazon.com/pdfs/whitepapers/latest/blue-green-deployments/blue-green-deployments.pdf)，checked 2026-11-06：新旧环境共用数据时要保持 schema 兼容；本文的 expand-and-contract 是通用工程安排，不是平台自动回滚数据库的承诺。
