# 知识导航

可以从眼前的问题开始读。比如，报表上的按钮已经出现，点了却没反应，先走「一次操作怎样变成界面更新」；聊天助手提交工单后断了线，走「怎样确认一次跨系统操作的结果」。想系统读完一个领域时，地图列出章节顺序，连续阅读稿可从各分部的首章进入。

## 从领域开始

| 领域 | 主线与完整顺序 | 连续阅读 |
| --- | --- | --- |
| AI 工程 | [AI 工程地图](../ai-engineering/index.md) | [AI 工程连续阅读稿](generated/ai-engineering.md) |
| 前端 | [前端地图](../frontend/index.md) | [前端连续阅读稿](generated/frontend.md) |
| 工程基础 | [工程基础地图](../engineering-foundations/index.md) | [工程基础连续阅读稿](generated/engineering-foundations.md) |

## 一次操作怎样变成界面更新？

报表先显示 May、April 两行。用户点「最早优先」却看不到变化，先确认处理点击的代码装好了没有。按钮可以先画出来，等脚本运行后才有人处理点击，[首帧与交互就绪](../frontend/browser/browser-basics.md#从首帧交接到筛选更新)就能解释这种现象。若处理器已经注册，再查主线程忙时[点击任务什么时候能执行](../frontend/runtime/event-loop.md)。

处理器开始执行后，可以对照同一个按钮的两种实现。

- **原生 JavaScript** 从按钮读出 `oldest`，把已有的行节点移成 April、May，并把「最早优先」的 `aria-pressed` 改为 `true`。沿[点击事件和节点更新](../frontend/browser-apis/dom-manipulation-and-events.md)可以看到每处改动由谁执行。
- **React** 的处理器提交排序状态更新。组件下次渲染时用手头两行算出 April、May，React 在提交阶段更新行顺序和按钮状态，随后才请求服务端确认。示例聚焦组件，地址栏与浏览历史的同步见前面的首帧案例。[跟着两行报表走一遍 React 更新](../frontend/frameworks/react-basics.md)

两种实现都交给浏览器一份顺序已更新的 DOM。接着看[浏览器怎样把改动显示在下一帧](../frontend/html-css/rendering-pipeline-and-forced-layout.md)。如果点击很慢，先[按症状查输入等待、处理和呈现三个阶段](../frontend/performance/performance-metrics-and-analysis.md#沿同一动作从症状走到证据)。[排序性能实验](../frontend/performance/performance-metrics-and-analysis.md#复现报表排序后，修掉重复日期解析)另用原生 JavaScript 给 50,000 条合成记录排序，再重建前 50 行，演示怎样验证慢在排序。若慢在 React 的组件计算，再读[怎样让输入保持响应](../frontend/frameworks/advanced-react.md)。

## 怎样确认一次跨系统操作的结果？

开发者批准助手为构建 42 创建缺陷单。工单系统已经建单，执行程序却没来得及保存回执，聊天窗口随后也断了线。用户回来时，怎样在原来的卡片上看到结果？

1. **先查外部动作。** 运行 `run-r42-7` 把这次创建记为「结果待确认」。新的执行程序按原操作键查询工单系统，找到 `ISSUE-842`，把工单号和最终答复一起保存。查证这一步只读，无须再次建单。[回执丢失后怎样对账](../ai-engineering/runs/external-writes-and-reconciliation.md)
2. **再恢复同一张卡。** 用户重连时，用原运行 ID [查询已保存的结果](../ai-engineering/runs/disconnect-cancel-and-user-input.md)，服务会检查用户现在是否仍有权查看。假设浏览器保留了第 10 条事件处理完后的界面，从第 11 条起补读，就能把 `ISSUE-842` 填回已有的「创建缺陷单」卡片，再用第 12、13 条补齐答复并显示完成。全新窗口则需要一份包含文本、卡片和匹配事件序号的快照，或从仍保留的历史起点重建。[聊天界面怎样应用重放事件](../frontend/browser-apis/streaming-ai-chat.md#怎样应用重放事件而不重复消息或工具卡？)

遇到别的断线场景，先看自己要确认的结果由谁保存。

- **库存到底扣了吗？** 客户端用原键 `reserve-demo-208` 重发相同预留，服务找到已经提交的那笔预留，返回它的当前状态。[库存事务与安全重试](../engineering-foundations/reliability/api-reliability-and-async-delivery.md)
- **导出的 CSV 能下载了吗？** 受理回执丢失时，用原键 `report-demo-208` 重发相同导出请求，取回任务 `job-demo-731` 和查询地址。沿[账户报表的任务与结果](../engineering-foundations/architecture/system-design-fundamentals.md)读到成功提交和授权下载。[队列确认](../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md)只说明消息交付到了哪一步。
- **进度页面该显示哪一版？** 在报表的实时视图里，[服务端从快照游标 103 续发事件](../engineering-foundations/networking/real-time-web-updates.md#SSE%20如何从快照游标续读事件？)。[页面](../frontend/browser-apis/streaming-ux.md)应用 104 后在断线期间保留第 10 版，重连收到 105 才把报表更新为第 11 版的「就绪」。

只需理解一次普通读取时，可以沿 [HTTP 请求和响应](../engineering-foundations/networking/http-protocols-and-websockets.md)、[API 对调用方的承诺](../engineering-foundations/backend/http-api-contracts.md)、[获取数据连接](../engineering-foundations/backend/data-access-and-connection-pools.md)或[缓存何时需要更新](../engineering-foundations/backend/caching-and-redis.md)进入对应章节。

## 怎样证明一次改动可以上线？

报表 42 属于租户 A，已登录的租户 B 猜到编号竟也能读到。旧版已有越权问题，先隔离受影响的入口。要恢复访问，沿着修复从源码走到实际接收流量的版本。

1. **把漏洞变成能重复验证的条件。** 从[漏掉租户条件的查询](../engineering-foundations/architecture/reading-debugging-and-reviewing-code.md)入手。[测试](../engineering-foundations/testing/software-testing-strategy.md)用两个身份读同一份报表，要求 A 得到 `200` 和自己的内容，B 得到与资源不存在时一致的 `404`。
2. **固定测试过的内容。** [用 Git 核对暂存的源码和测试](../engineering-foundations/version-control/git-essentials.md)，在发布案例中将这份快照记作 `c4f2a91`。[从该提交构建一次镜像](../engineering-foundations/infrastructure/docker-operations.md)，推送后在镜像仓库核对其内容摘要。后面每个环境都用这份摘要取镜像。
3. **用同一镜像接流量。** 预发布用真实认证流程建立两个身份，重验上述响应，并跑通异步任务。进生产后，先让 A、B 经正常鉴权访问新版本，核对两份响应和两条请求追踪，确认命中的都是目标摘要，再开放小流量。若验证失败，维持隔离或转到已证安全且兼容的版本。[发布与回退](../engineering-foundations/infrastructure/application-deployment-and-ci-cd.md)

怎样看出新版本在变慢？[生产事故演练](../engineering-foundations/reliability/observability-slos-and-incident-response.md)另给一个发布窗口，演示怎样单看新版本的请求，避免旧版本的大量成功请求掩盖退化。改动落在界面时，读[前端行为与构建产物的测试](../frontend/testing/frontend-testing.md)；改在提示词、模型或 Agent 时，读[独立任务评估](../ai-engineering/evaluation-and-release/holdout-acceptance-and-paired-statistics.md)。若差距确实来自模型行为，再看[训练怎样更新权重](../ai-engineering/evaluation-and-release/training-gradients-and-optimizers.md)和[什么时候值得微调](../ai-engineering/evaluation-and-release/fine-tuning-lora-sft-dpo.md)。

## AI 应用怎样凭证据回答？

开发者问“构建 42 为什么失败”。沿着这个问题读两章，可以看清日志、接口契约和重试规则分别能回答什么。

1. [日志里发生了什么？](../ai-engineering/overview/how-an-ai-answer-is-produced.md) 助手在获得授权后读取构建日志。空名称测试预期返回 HTTP 状态码 `400`，实际返回 `200`。这个差异解释了测试为什么失败。
2. [测试的预期正确吗，这次应该自动重跑吗？](../ai-engineering/context/rag-indexing-and-retrieval.md) 带着同一条日志去查现行文档。本例的接口契约要求空名称返回 `400`，构建手册规定断言失败不能自动重跑。如果手册更新，要重新核对自动重跑的条件，原日志仍是这次测试结果的依据。

想深入其中一个环节时，可以沿下面的支线读。

- 想知道模型怎样利用前文，先看[提示词怎样变成文本](../ai-engineering/model/next-token-computation.md)里的逐位置 KV，再看[Kimi KDA 怎样用一张固定矩阵读写历史](../ai-engineering/model/kimi-delta-attention-state.md)。两种状态的存储方式会影响[服务能同时承接多少请求](../ai-engineering/model/kv-cache-and-serving-capacity.md)。
- 日志和文档都找到了，[应用怎样选择本次推理该看到的信息](../ai-engineering/context/context-budget-and-state-layers.md)解释哪些内容进入模型、哪些留在应用记录里。
- 再次遇到相关问题时，看[什么时候值得把历史加工成记忆](../ai-engineering/context/agent-memory-design-and-evaluation.md)：先与原文检索比较，再检查加工后的信息损失、使用成本和独立任务结果。
- 一次工具调用不足以完成目标时，看[如何组织多阶段任务](../ai-engineering/actions/multi-stage-orchestration.md)和[如何验证并保留改进](../ai-engineering/evaluation-and-release/choosing-what-to-change.md)。

## 访问数据的成本从哪来？

报表程序已经取回 1,024 条事件，先按发生时间排序，时间相同再比事件 ID。要在页内定位一个游标，[算法章](../engineering-foundations/algorithms/algorithms-and-complexity.md)解释为什么按同一规则比较就可以每次排除一半候选。[数据结构章](../engineering-foundations/algorithms/core-data-structures.md)接着问，若只知道事件 ID，或手上已经有了下标，应怎样找到那条记录？

换一个观察尺度，成本的单位也会变。可以按要回答的问题选读。

- **都访问四项，为什么内存开销会不同？** 数组和链表累加同一组时长 `[4, 7, 1, 3]` 都得到 15。沿[两个布局的地址](../engineering-foundations/operating-systems/memory-hierarchy-and-data-locality.md)逐项读，可以看到缓存行是否被复用、下一次读取要等哪个指针。
- **还没取回数据，数据库怎样找到最近的任务？** 另一个查询要取某账户最近的 20 个导出任务。用账户、创建时间和任务 ID 建立符合排序的复合索引，数据库就多了一条按账户定位、取够 20 条便可停止的路径。可以从执行计划看它是否选了这条路。[复合索引怎样配合任务列表](../engineering-foundations/databases/database-constraints-and-indexes.md#复合索引怎样配合任务列表？)

要继续推导连接代价或理解提交后的数据怎样恢复，可转到[数据库课程地图](../archive/uni-subjects/COMP90050ADBS/readme.md)和[事务与恢复](../engineering-foundations/databases/database-transactions-isolation-and-recovery.md)。

## 按机制查找

已经知道想查的概念时，可以直接进入下面的解释；完整学习顺序仍由各领域地图维护。

| 想查的机制 | 正文入口 |
|---|---|
| MCP、用户委托与本地工具执行 | [MCP 连接与鉴权](../ai-engineering/actions/mcp-protocol.md)、[OAuth 委托执行](../ai-engineering/actions/authorization-gates-for-actions.md)、[coding harness](../ai-engineering/actions/coding-agent-harness.md) |
| LangGraph、重规划与记忆 | [运行恢复](../ai-engineering/runs/run-identity-and-authoritative-state.md)、[编排与循环诊断](../ai-engineering/actions/multi-stage-orchestration.md)、[上下文与跨运行记忆](../ai-engineering/context/context-budget-and-state-layers.md)、[记忆加工的净收益](../ai-engineering/context/agent-memory-design-and-evaluation.md) |
| 模型配额、缓存与向量索引 | [有界模型调用](../ai-engineering/runs/bounded-model-api-calls.md)、[缓存命中与成本](../ai-engineering/evaluation-and-release/model-selection-and-unit-cost.md)、[HNSW](../ai-engineering/context/hnsw-vector-index-search.md) |
| debounce、throttle、Promise 与结构相等 | [闭包调度](../frontend/javascript/scope-and-closure.md#定时回调怎样用闭包保留调度状态)、[Promise 组合](../frontend/javascript/asynchronous-javascript.md)、[并发池](../frontend/javascript/bounded-async-concurrency.md)、[值与结构比较](../frontend/javascript/javascript-types.md) |
| Context、编辑草稿与聊天状态 | [组件中的状态所有者](../frontend/frameworks/react-component-composition.md)、[表格与表单](../frontend/frameworks/management-table-and-form-workflows.md)、[流式聊天](../frontend/browser-apis/streaming-ai-chat.md) |
| 条件写、回调与持久队列 | [HTTP 更新契约](../engineering-foundations/backend/http-api-contracts.md)、[Webhook](../engineering-foundations/reliability/webhook-delivery-and-verification.md)、[任务领取与确认](../engineering-foundations/reliability/queue-delivery-and-acknowledgement.md)、[Kafka offset](../engineering-foundations/reliability/kafka-partitions-and-offsets.md) |
| 类型、构建产物与渐进迁移 | [运行时 schema](../frontend/typescript/advanced-typescript.md#怎样用%20Zod%20在同一个输入边界生成运行时检查和静态类型？)、[静态资源版本](../frontend/tooling/build-tools.md#新入口与带哈希代码分块怎样作为同一版本发布？)、[微前端迁移](../engineering-foundations/architecture/frontend-architecture-boundaries.md#怎样迁移微前端而不打断深链、身份与回退？) |
| 数据分布与存储引擎 | [分片与搬迁](../engineering-foundations/databases/database-sharding-and-rebalancing.md)、[InnoDB 索引、锁与恢复](../engineering-foundations/databases/mysql-innodb-index-lock-and-recovery.md) |
| Python 属性解析 | [descriptor、方法绑定与 MRO](../engineering-foundations/backend/python-attribute-lookup-and-mro.md) |
| 部署身份与密钥 | [凭据的注入、轮换与撤销](../engineering-foundations/infrastructure/production-application-runtime.md#worker%20凭据怎样注入、轮换并撤销？) |
| 窗口、优先级与搜索路径 | [窗口与区间扫描](../engineering-foundations/algorithms/range-scans-and-active-sets.md)、[堆](../engineering-foundations/algorithms/heaps-and-priority-queues.md)、[图搜索与回溯](../engineering-foundations/algorithms/graph-search-and-backtracking.md)、[文本单位与 Trie](../engineering-foundations/algorithms/text-units-and-algorithms.md) |

## 阅读记录与资料

- [本轮阅读进度](reading-progress.md)只记录本轮读过哪些正文。
- [AI 好文集](ai-literature-index.md)按问题收集来源及其知识落点。
- [归档](../archive/index.md)保留课程推导、作者解法、原始材料和专门参考。
