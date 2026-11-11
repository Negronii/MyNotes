# 托管函数适合哪些有界任务，何时转向常驻 worker？

本归档原文讨论的是 Google Cloud Functions。当前官方文档将新一代产品称为 Cloud Run functions；旧版仍以 Cloud Run functions (1st gen) 标示。名称变化容易让维护者把两种资源模型和限额当成同一个产品。本文保留原来的托管函数问题，改用当前产品模型说明它与常驻报表 worker 的分界。

以账户报表为例，账户 acct-17 为 report 42 发起导出，幂等键 report-demo-208 对应持久任务 job-demo-731。若每次调用工作有界、失败后可安全重试，平台负责启动执行环境能减少主机管理；若任务耗时不可预测、需要持续消费队列或对关闭过程有严格控制，函数的单次执行上限和事件重试就会成为工作负载必须处理的条件。

## 先问任务能否安全地被重复调用

function as a service（函数即服务，FaaS）以一次 HTTP 请求或事件触发为主要入口，执行时间、内存、并发和重试受所选产品与触发器配置约束。Cloud Run functions 的新一代由 Cloud Run 作为服务运行；部署源代码会协调 Cloud Storage、Cloud Build 和 Artifact Registry 构建及保存容器镜像。使用函数框架不意味着“没有容器”，而是把部分构建和运行管理委托给平台。

报告任务可能在数据库提交成功后、触发方收到完成确认前中断。trigger（触发器）因此可能重试同一个逻辑事件；此例每次重试都沿用 job ID `job-demo-731` 和 operation key（操作键）`report-demo-208`。handler（处理函数）若持久存储已有已提交结果，就返回原状态/结果。去重必须在写入边界用唯一操作键或原子条件裁决，并与本地业务写入在同一事务中提交；单纯先查再写或只开一个事务都不能替代原子去重。事务外动作要按各自契约恢复：通知等采用接收端去重的动作，应为该动作保留稳定 key，并让接收方据此去重；可靠投递本身不去重。报表导出对象采用另一条路径：每个 attempt 使用不同的不可变对象键，只由数据库当前 attempt 的条件更新提交可见引用，避免旧 worker 覆盖新结果，详见[工作进程重试怎样避免旧结果覆盖新结果？](../../../engineering-foundations/architecture/system-design-fundamentals.md#工作进程重试怎样避免旧结果覆盖新结果)。全局变量可在某些 warm runtime（预热运行环境）中暂存连接或可重建缓存，但实例会重启或并发扩展；它不能作为跨调用的权威进度。长任务改由常驻 worker 执行也不能把恢复进度只留在进程内存，需持久记录状态或检查点并让任务可安全续跑。

## 用时长和并发估计实际边界

当前 Cloud Run functions 配额按代际和触发类别列出不同执行上限：新一代 HTTP functions 最多 60 分钟；配额表另列 scheduled/Task queue functions 为 1800 秒、event-driven functions 为 540 秒；Cloud Functions v2 API 创建的 event-driven function 也由比较表明确列为最多 9 分钟；1st gen 最多 540 秒。1800 秒是配额表中的 scheduled/Task queue 类别，不是所有 HTTP/API function 的通用上限。官方触发说明允许 Cloud Tasks 以 HTTP target 调用 HTTP function；这种路径还要受任务自己的回包 deadline 限制（Cloud Tasks 最长 30 分钟），应同时核对队列与 function 的配置。对 Cloud Run HTTP 请求，达到 request timeout（请求超时）时客户端连接会关闭并收到 504，但容器实例可能继续处理这次请求；事件触发则要按对应 trigger 的确认、超时和重试契约判断调用何时结束或重试。504 或触发器报告超时都不能单独证明业务副作用未发生，应沿用原 job/operation key 查询持久状态，再决定是否安全重试。任务总完成时间还可能因重试更长。

新一代函数每个实例的 concurrency（并发请求数）上限可配置到 1000；1st gen 每个实例只处理一个请求。上限代表平台允许并行的请求数，不代表数据库或对象存储能承载同样吞吐。举例：如果 3 个实例各接受 80 个在途请求，平台层理论上可同时接收 3 × 80 = 240 个请求；若每个实例数据库连接池上限为 10，则三池合计最多同时借出 30 个连接（假设每个在途请求最多持有一个连接），其余请求可能等待连接释放。这个连接数不等于数据库会并行执行 30 条查询。降低并发可限制数据库压力，但可能增加实例数、冷启动或等待时间；应以实际并发、连接池等待和任务延迟做压力检查。

> [!info] 最小实例数换取启动延迟
> Cloud Run 可以设置最低实例数，减少从零启动导致的冷启动延迟。最低实例会有闲置资源成本，而且“保持温热”是平台目标，不等于实例永不重启。对延迟敏感的同步读取可比较 min instances 的常驻成本；低频、可接受启动等待的批任务，可能更愿意按需扩展。计费要核对当前地区和资源配置，不能只比较函数调用价格。

## 把函数或常驻 worker 放到正确的阶段

| 工作形状 | 函数适用条件 | 应选常驻服务的信号 |
|---|---|---|
| 事件驱动的小型导出 | 每个阶段有界且实际耗时落在函数上限内；沿稳定 job/key 幂等重试 | 工作难以拆成有界步骤，且实际耗时可能超过函数上限；两种形态的重试都要从持久进度恢复 |
| 同步 HTTP report status | 无状态、请求短、冷启动在延迟预算内 | 需要持续连接、高常驻并发、明确的进程内资源管理 |
| queue consumer（队列消费者） | provider（平台）的 event trigger（事件触发）、ack 和 retry（重试）语义满足业务 | 要逐条控制 ACK、prefetch（预取上限）、批量处理、持续拉取或优雅 drain（排空），并持久保存可恢复进度 |
| 需要固定 CPU/连接的高流量 | 负载短突发，且按请求计费与最低实例闲置费经测算符合预算 | 稳定高占用需固定 CPU 或连接池；按同区域资源、并发、请求时长比较 request-based 与 instance-based 账单，不能先验认为常驻服务更便宜 |

这个决策不是函数对容器的普遍优劣比较。一个应用可以让 API 使用托管服务、短任务使用函数、长报表计算使用常驻 worker。无论哪种形态，主体授权、数据库事务、对象隐私、重试幂等、日志和容量责任仍在应用侧；网络不可达也不等于业务授权。

具体 Cloud Run functions 代际比较、时长与并发上限，以及 source-to-image 构建路径见下列官方文档。原题沿用“托管函数”名称，仅便于理解旧学习笔记；示例不表示对某一账户或已部署服务的审计。

> [!info]- 来源
> - Cloud Run functions [Comparison](https://docs.cloud.google.com/run/docs/functions/comparison)，checked 2026-11-11：新一代由 Cloud Run 服务承载，HTTP/Cloud Functions v2 API event-driven 请求上限分别列示；1st gen 与新一代在 concurrency、traffic splitting 和配置方面不同；旧名 Cloud Functions (2nd gen)。
> - Cloud Run functions [Quotas](https://docs.cloud.google.com/functions/quotas)，checked 2026-11-11：HTTP、scheduled/Task queue、event-driven 与 1st gen 的分行时长配额。Cloud Run functions [triggers](https://docs.cloud.google.com/run/docs/function-triggers)，checked 2026-11-11：Cloud Tasks 可把 HTTP target 作为 function handler。Cloud Tasks [task queue overview](https://docs.cloud.google.com/tasks/docs/dual-overview)，checked 2026-11-11：HTTP target 的响应 deadline 最长 30 分钟。Cloud Run [request timeout](https://docs.cloud.google.com/run/docs/configuring/request-timeout)，checked 2026-11-11：HTTP 请求超时时关闭网络连接并返回 504，但容器可能继续处理已取消请求。
> - Cloud Run [Functions best practices](https://docs.cloud.google.com/run/docs/tips/functions-best-practices)，checked 2026-11-11：cold start、依赖初始化、最小实例、并发和函数幂等性。
> - Cloud Run [Minimum instances](https://docs.cloud.google.com/run/docs/configuring/min-instances)，checked 2026-11-11：保温实例与延迟/资源权衡；最低实例数是目标状态，并不保证永不重启。
> - Cloud Run functions [Overview](https://docs.cloud.google.com/run/docs/functions/overview)，checked 2026-11-11：source、Cloud Storage、Cloud Build、Artifact Registry 和 Cloud Run 资源之间的构建关系。通用运行时选择见[按任务时长、并发和停止行为选择运行时](../../../engineering-foundations/infrastructure/production-application-runtime.md#按任务时长并发和停止行为选择运行时)。
