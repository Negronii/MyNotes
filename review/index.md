# 知识导航

可以从眼前的问题开始读。报表页上的「最早优先」点了没反应，走「一次操作怎样变成界面更新」；退款请求超时、客户又断了线，走「怎样确认一次跨系统操作的结果」。每条路线只串起回答这个问题要读的章节，完整顺序和每个领域的主线仍以各领域地图为准。

## 从领域开始

| 领域 | 主线与完整顺序 | 连续阅读 |
| --- | --- | --- |
| AI 工程 | [AI 工程地图](../ai-engineering/index.md) | [AI 工程连续阅读稿](generated/ai-engineering.md) |
| 前端 | [前端地图](../frontend/index.md) | [前端连续阅读稿](generated/frontend.md) |
| 工程基础 | [工程基础地图](../engineering-foundations/index.md) | [工程基础连续阅读稿](generated/engineering-foundations.md) |

## 一次操作怎样变成界面更新？

报表页 `/reports/42?sort=recent#summary` 已经显示 May、April 两行。用户点「最早优先」，想看到 April、May。从这一下点击到屏幕换成新顺序，中间经过哪几步？

先确认按钮真的能点。服务器把两行数据写进了 HTML，所以首帧可以先出现；按钮却要等 `/reports.js` 执行、注册处理器后才会启用。看得见却点不动，多半是这条可交互线还没走完，见[报表页怎样从看得见走到点得动](../frontend/browser/from-url-to-interactive-page.md#报表页怎样从看得见走到点得动)。处理器就绪后，点击会变成一个排队的任务；主线程正忙时它只能等，处理器返回后先排空微任务，再等渲染机会，见[一次点击要跨过哪些调度边界](../frontend/browser/event-loop-tasks-and-rendering.md#一次点击要跨过哪些调度边界)。

原生实现里，点击从按钮里的 `span` 或 `path` 冒泡到工具栏，委托监听器读出 `oldest`（见[一次点击沿哪条路径传播](../frontend/browser/dom-events.md#一次点击沿哪条路径传播？)），再把已有的两个行节点[移成 April、May](../frontend/browser/dom-queries-and-updates.md#移动已有节点：把报表重排成%20April、May)，同时改两个按钮的 `aria-pressed`。处理器返回时 DOM 已经是新顺序，屏幕还停在上一帧，要等浏览器重算样式、布局并绘制；处理器里若读几何值，浏览器就得提前同步算出布局，见[为什么读几何值会让脚本停下来](../frontend/browser/rendering-pipeline-and-forced-layout.md#为什么读几何值会让脚本停下来？)。想让复制链接和后退都显示对的顺序，再用 `pushState()` 把 `sort=oldest` 写进地址，见[让排序跟随地址栏与前进后退](../frontend/browser/navigation-history-and-url-state.md#让排序跟随地址栏与前进后退)。

换成 React，浏览器照常派发 `click`，处理器交出的只是[排序意图](../frontend/browser/dom-events.md#交给%20React%20时交出的是意图)。它排入 `sort="oldest"` 和 `requestId=1` 两个更新；render 从上次成功的两行算出 April、May，commit 把行序和按钮状态写进 DOM，paint 仍由浏览器决定；Effect 随后才调用 `fetchReports("oldest")`，见[一次点击走过哪几步](../frontend/ui-state/react-update-model.md#一次点击走过哪几步)。用户连点两次时，靠请求编号让[迟到的响应不写错界面](../frontend/ui-state/react-update-model.md#Effect%20怎样跟随已提交的选择，又怎样拒绝过期结果)；改用查询缓存后，结果按查询键归属，`acct-a` 的行不会出现在 `acct-b` 下，见[异步结果按身份归属](../frontend/ui-state/server-state-and-optimistic-updates.md#异步结果按身份归属)。

点击明显变慢时，先把一次交互拆成输入等待、处理和呈现三段，见[一次慢交互怎样拆成三段](../frontend/delivery/performance-metrics-and-diagnosis.md#一次慢交互怎样拆成三段？)。[50,000 行排序实验](../frontend/delivery/performance-metrics-and-diagnosis.md#50,000%20行排序实验：慢在哪里，怎样修？)用合成记录复现了处理阶段的瓶颈：比较器里重复调用 `Date.parse` 一百多万次，移到准备阶段后，交互延迟 p75 从 832 毫秒降到 128 毫秒。若时间花在 React 的组件渲染上，读[React 渲染慢时先改什么](../frontend/delivery/react-rendering-optimization.md)和[怎样让输入保持即时](../frontend/ui-state/urgent-and-deferred-updates.md)；若成本随挂载行数增长，读[分页和虚拟化各省掉什么](../frontend/delivery/long-lists-pagination-and-virtualization.md)。

## 怎样确认一次跨系统操作的结果？

退款助手代客户 `cust-55` 为订单 `O-73` 发出 `20.00 USD` 的退款，请求读超时了，客户的浏览器也几乎同时断线。钱到底退了没有，客户回来时又该看到什么？

能回答的只有应用事先存下的记录。运行 `run-o73-1` 在发出请求前，已经在退款操作 `R-204` 上登记了发送意图：用哪份获批方案、哪个提供方幂等键 `K-R204`、哪个 attempt。这些记录从哪来、各证明什么，见[退款助手的一笔退款停在了哪里](../ai-engineering/runs/run-identity-and-authoritative-state.md#退款助手的一笔退款停在了哪里？)。超时只说明没收到回执，所以运行进入 `effect_unknown`：不记成失败，不新建 `R-205`。对账 worker 只读查询，找到候选 `re_demo_204` 后，逐项核对账户 `acct-M9`、原支付 `P-73`、金额、币种和 `operation_id`，全部相符才绑定，见[只读对账怎样找到那笔退款](../ai-engineering/runs/external-writes-and-reconciliation.md#只读对账怎样找到那笔退款？)。读到 `pending` 时运行进入 `provider_pending`，再读到 `succeeded` 才保存最终答复并标记 `completed`，见[提供方状态怎样映射回运行](../ai-engineering/runs/external-writes-and-reconciliation.md#提供方状态怎样映射回运行？)。

客户重连后，用 `GET /runs/run-o73-1` 读取保存好的状态，服务要重新检查他此刻是否仍有权查看。浏览器若已处理到第 10 条事件，就从 `after=10` 续读：第 11 条把 `re_demo_204` 填进原来的退款卡片，第 12、13 条补齐答复并显示完成，见[重连后怎样回到同一个运行](../ai-engineering/runs/disconnect-cancel-and-user-input.md#重连后怎样回到同一个运行？)。连 `202` 回执都没收到时，用原键 `cli-o73-1` 找回运行，见[连受理回执都丢了，怎样找回运行](../ai-engineering/runs/disconnect-cancel-and-user-input.md#连受理回执都丢了，怎样找回运行？)。前端怎样按序号和工具调用 ID 应用这些事件，用另一个场景讲：CI 助手的运行 `run-r42-7` 在审核后建单，`c2` 结果未知，对账确认 `ISSUE-842` 后，第 11 条事件更新的仍是原来那张卡，见[怎样应用重放事件而不重复消息或工具卡](../frontend/ui-state/streaming-ai-chat.md#怎样应用重放事件而不重复消息或工具卡？)和[结果未知时先对账，不重发](../frontend/ui-state/streaming-ai-chat.md#重试：结果未知时先对账，不重发)。

这些做法用到的通用机制都在工程基础里，案例换成账户报表服务：

- **同一个操作身份取回原结果。** `user-17` 的导出请求带幂等键 `export-demo-415`，`202` 在途中丢失；同键重放取回已有的 `job-demo-731`，见[导出请求在响应途中丢失](../engineering-foundations/services/deadlines-retries-and-unknown-outcomes.md#案例：导出请求在响应途中丢失)。服务端能认出原操作，前提是效果和幂等记录在同一个事务里提交，库存案例的 `SKU-7` 与 `reserve-demo-208` 演示了这一点，见[响应丢失时，记录怎样认出原操作](../engineering-foundations/data/conditional-writes-and-idempotent-records.md#响应丢失时，记录怎样认出原操作？)。
- **受理、唤醒和完成各由谁证明。** `202` 之前要提交 job 与 outbox，见[数据库和消息代理之间的缺口怎样补上](../engineering-foundations/services/durable-job-acceptance-and-outbox.md#数据库和消息代理之间的缺口怎样补上？)；publisher confirm 和 consumer ACK 只证明消息交接到了哪一步，见[发布确认、消费者确认和业务完成各证明什么](../engineering-foundations/services/queue-delivery-and-acknowledgement.md)。
- **推送断线后接上哪一版。** 报表 42 的页面从快照游标 103 订阅，收到 104 显示版本 10；断线后浏览器带 `Last-Event-ID: 104` 重连，收到 105 才更新为版本 11 的 `ready`。服务端怎样续发见[实时通道与续读](../engineering-foundations/services/real-time-channels-and-resume.md#快照和订阅怎样衔接在同一日志位置)，页面怎样合并见[从游标 103 到事件 105](../frontend/ui-state/streaming-updates-and-resume.md#一次完整的续读：从游标%20103%20到事件%20105)。

## 怎样证明一次改动可以上线？

账户报表服务的报表 42 属于 `acct-17`。另一个账户的成员 `user-29` 请求 `GET /v1/accounts/acct-29/reports/42`，竟读到了它。修复写好、测试变绿之后，凭什么让它接生产流量？

先把缺陷写成可以被推翻的契约：`user-17` 读到 `200`，`user-29` 得到与读取不存在的报表 43 完全相同的 `404`。选对请求路径才能让取数层单独接受检验；沿调用路径能看到，重构后的 `Session.get(Report, 42)` 只按主键读取，丢了账户条件，见[先把症状写成可证伪的契约](../engineering-foundations/practice/debugging-and-code-review.md#先把症状写成可证伪的契约)和[主键读取不是所有权检查](../engineering-foundations/practice/debugging-and-code-review.md#主键读取不是所有权检查)。旧测试只让 `user-17` 读自己的报表，修复前后都绿；新测试要走真实路由，并且换回 `Session.get` 时一定失败，见[测试必须能区分对错](../engineering-foundations/practice/testing-by-failure-boundary.md#测试必须能区分对错)。

接着把被测的内容固定下来。被测快照必须等于提交快照，修复在 `fix/report-account-scope` 上 rebase 后成为提交 `c4f2a91`，构建和验收都绑定这个 ID，见[把提交和验收证据绑在同一个 ID 上](../engineering-foundations/practice/git-snapshots-and-recovery.md#把提交和验收证据绑在同一个%20ID%20上)。CI 从这个提交构建一次镜像，推送后在 registry 核验摘要，记作 `d-new`，见[摘要标识内容，不证明来源](../engineering-foundations/practice/container-images-and-builds.md#摘要标识内容，不证明来源)。预发布和生产都按这个摘要取同一份镜像，见[为什么只构建一次、按摘要晋级](../engineering-foundations/practice/build-once-promote-by-digest.md#为什么只构建一次、按摘要晋级)；平台报告就绪只说明可以发流量，见[平台怎样判断进程可以接流量](../engineering-foundations/practice/production-runtime.md#平台怎样判断进程可以接流量)。

开流之前还有一个陷阱：稳定版 `d-old` 正带着这个缺陷。先在入口为交给 `d-old` 的读取路由加归属预检，挡住跨账户读取；再把 `user-17`、`user-29` 的冒烟请求钉到 `d-new`，确认得到 `200` 和与报表 43 相同的 `404`，两条追踪都命中 `d-new`，才开放首轮 10% 流量，见[生产冒烟检查](../engineering-foundations/practice/canary-rollout-and-rollback.md#就绪之后、开流之前：生产冒烟检查)。放量门禁只看新版本自己的读取 SLI：`d-new` 是 98/100，和 `d-old` 的 900/900 合并后却显得有 99.8%，见[金丝雀不能和稳定版合在一起评估](../engineering-foundations/practice/slis-slos-and-error-budgets.md#金丝雀不能和稳定版合在一起评估)。需要止损时，`d-old` 也不是安全的回退目标，见[回退前先确认目标当前安全、数据兼容、有容量](../engineering-foundations/practice/canary-rollout-and-rollback.md#回退前先确认目标当前安全、数据兼容、有容量)。12:10–12:20 的窗口里读取变慢、`job-demo-731` 停在 `queued`，trace 和 worker 日志都指向获取数据库连接，怎样从信号走到根因并复验恢复，见[两个症状的诊断](../engineering-foundations/practice/incident-diagnosis-and-recovery.md#案例：12:10–12:20%20的两个症状)。

改动在别的领域时，证据的形状不同，逻辑一样：

- **前端改动。** 测试要证明页面真的用了对应的响应，并且测的是将要发布的那份产物，见[交付检查：测将要发布的那份产物](../frontend/delivery/frontend-testing-strategy.md#交付检查：测将要发布的那份产物)。发布时先上传带哈希的文件，最后才切换入口，还开着的旧页面才不会取不到旧 chunk，见[发布时先上传什么、后切换什么](../frontend/delivery/hashed-release-and-caching.md#发布时先上传什么、后切换什么，旧文件留多久？)。
- **AI 助手改动。** 为修 build 73 的误诊，候选 B（提示词 p13）在 200 道独立题上通过 180 道，当前版本 A（p12）通过 162 道；差距是否只是抽样波动，看[配对比较](../ai-engineering/evaluation-and-release/holdout-acceptance-and-paired-statistics.md#配对比较：McNemar%20只看不一致的%2030%20题)。一次只改一层，先改提示词、上下文、工具和脚手架，见[什么时候才轮到改权重](../ai-engineering/evaluation-and-release/choosing-what-to-change.md#什么时候才轮到改权重)。上线的是一整套版本组合，回滚撤不回已经发生的副作用，见[回滚只恢复平台管理的部分](../ai-engineering/evaluation-and-release/deployment-rollout-and-rollback.md#回滚只恢复平台管理的部分)。

## AI 应用怎样凭证据回答？

开发者问 CI 诊断助手：`Why did build 42 fail?` 接着又追问：“空名称请求预期返回 `400` 对吗？按当前 CI 手册，这次该自动重跑吗？”助手的每一句话凭的是什么？

第一问要靠日志。模型只看见应用这次交给它的输入，缺证据时只能生成一条工具请求 `read_build_log`（调用 ID `c1`）。应用按自己保存的调用者身份检查权限后才读日志：`unit-tests` 步骤里，`reject_empty_name` 预期 HTTP `400`，实际 `200`，`exit_status=1`。回答只陈述这条断言失败，不臆造根因；运行 `run-r42-6` 保存回答后才算完成，见[一次 AI 回答经过了哪几步](../ai-engineering/overview/how-an-ai-answer-is-produced.md)。证据缺失时用户看到什么、证据状态由谁判定，见[提示词怎样写成可验收的契约](../ai-engineering/context/model-input-and-prompt-contract.md)；授权为什么只能由应用逐次判定，见[服务怎样逐次确认主体能对资源做这个动作](../engineering-foundations/services/per-request-authorization.md#逐次授权的五步)。

追问要靠现行规则。这一轮不重读日志，而是把 `run-r42-6#c1` 作为注明出处的历史观察放进输入，见[新运行怎样引用旧的工具结果](../ai-engineering/context/context-budget-and-state-layers.md#追问来了：新运行怎样引用旧的工具结果)。规则要从调用者有权读的文档里检索：当前的 `HTTP-CONTRACT-v1` 要求空名称返回 `400`，`CI-RETRY-v3` 规定断言失败不自动重跑；已撤回的 `CI-RETRY-v2` 要在检索阶段排除，见[开发者追问构建 42 该不该重跑](../ai-engineering/context/rag-indexing-and-retrieval.md#案例：开发者追问构建%2042%20该不该重跑)。检索交出的只是候选，模型写完后还要逐条核对每个主张是否真有来源支持，见[先看引用合法，再看来源是否支持](../ai-engineering/context/claim-verification-and-failure-localization.md#主张核验分两步：先看引用合法，再看来源是否支持)。答错时，按来源、检索、组装、使用这条链找坏掉的一环，见[答错时沿同一条链找坏掉的一环](../ai-engineering/context/claim-verification-and-failure-localization.md#答错时沿同一条链找坏掉的一环)。

想深入其中一环时，可以沿下面的支线读：

- **模型怎样利用输入。** 从分词、attention 到采样，见[模型怎样把提示词算成下一个词元](../ai-engineering/model/next-token-computation.md)；输入越长，每层留下的 KV 越多，决定了[一台服务能接多少请求](../ai-engineering/model/kv-cache-and-serving-capacity.md)。
- **上线后答错。** build 73 的误诊怎样从线上 trace 找回证据、定位到解释层，见[上线后怎样从一条错误建议找回可修复的证据](../ai-engineering/evaluation-and-release/production-traces-and-metric-denominators.md)；“答得好”的判分标准在[任务契约](../ai-engineering/evaluation-and-release/task-contracts-and-quality-dimensions.md)。
- **以后遇到同类问题。** 把历史加工成记忆之前，先和认真调过的原文检索比质量净变化与完整成本，见[什么时候值得把历史加工成 Agent 记忆](../ai-engineering/context/agent-memory-design-and-evaluation.md)。

## 访问数据的成本从哪来？

报表 42 的一页事件已经取回内存，共 1,024 条，按 `(occurred_at, event_id)` 升序排列。要知道位置 `(09:02, e08)` 排在第几条，最坏要比较多少次？换个问法，成本又落在哪里？

数比较次数时，线性扫描最坏要 1,024 次，`lower_bound` 只要 11 次探测，答案是下标 2。这个结论只在“按同一复合键有序”这条输入保证和写明的成本模型下成立，见[报表 42 的事件页](../engineering-foundations/computation/invariants-and-cost-models.md#案例：报表%2042%20的事件页)。这 11 次探测为什么不会漏掉答案，翻页游标为什么就是 `upper_bound`，见[边界查找](../engineering-foundations/computation/ordered-search-and-two-pointers.md#边界查找：lower_bound%20与%20upper_bound)和[下一页从哪里开始](../engineering-foundations/computation/ordered-search-and-two-pointers.md#下一页从哪里开始：游标就是%20upper_bound)。若只知道 `event_id`，这份按复合键排好的数组就帮不上忙，要换成哈希表这类按键精确查找的结构，见[复合键有序的数组，对子字段并不有序](../engineering-foundations/computation/data-structures-by-access-pattern.md#复合键有序的数组，对子字段并不有序)。

比较次数相同，耗时也可能差很多。累加四个时长 `[4, 7, 1, 3]`，数组和链表都得到 15，但数组的下一个地址可以提前算出，链表要先拿到 `next` 才知道下一站；搬运多少缓存行、何时才能发出下一次读取，决定了实际耗时，见[同样是 O(n)，为什么连续扫描往往比链表遍历快](../engineering-foundations/computation/memory-hierarchy-and-locality.md)。数据在磁盘上时，成本单位变成读了多少页，所以 B 树和 B+ 树让一个节点占一页、把树压矮，见[为什么按页计成本](../engineering-foundations/computation/data-structures-by-access-pattern.md#数据在磁盘上时，为什么按页计成本？)。

数据还在数据库里时，成本由索引、计划器和连接决定：

- **怎样少读。** 读 `acct-17` 最近的 20 个任务，复合索引 `(account_id, created_at DESC, job_id DESC)` 让数据库定位到这个账户的一段键区间，按时间读够 20 条就停；用不用它仍由计划器按成本决定，见[复合索引的列序怎样定](../engineering-foundations/data/constraints-and-indexes.md#复合索引的列序怎样定？)和[计划器为什么有时不用已建的索引](../engineering-foundations/data/constraints-and-indexes.md#计划器为什么有时不用已建的索引？)。
- **连接借多久。** 连接从借出到事务结束一直被占着。若一个请求在事务里等 3 秒远端服务，另一个只需 10 ms 的查询可能还没发出，就等满了 `pool_timeout`，见[长时间持有连接怎样让池耗尽](../engineering-foundations/data/orm-sessions-and-connection-pools.md#长时间持有连接怎样让池耗尽？)。
- **翻页和重复读取。** 按偏移翻页时，报表 40 一删，第二页就漏掉 42；用最后一行的完整排序键续读才不重不漏，见[按偏移翻页为什么会漏项和重复](../engineering-foundations/data/keyset-pagination-and-snapshots.md#按偏移翻页为什么会漏项和重复？)。重复读取交给缓存后，要说清最多旧多久，见[加了缓存之后，读到的数据最多会旧多久](../engineering-foundations/data/caching-and-staleness.md)。
- **单库到顶。** 先分清是总容量不足、负载偏斜还是一个热键，再决定分片或拆键，见[选分片键并区分总容量不足与热点](../engineering-foundations/data/sharding-and-hot-keys.md)。

要继续推导连接算法的代价或日志恢复的细节，转到[数据库课程地图](../archive/uni-subjects/COMP90050ADBS/readme.md)和[数据库确认提交后崩溃，靠什么恢复](../engineering-foundations/data/write-ahead-logging-and-recovery.md)。

## 按机制查找

已经知道想查的概念时，可以直接进入下面的解释；完整学习顺序仍由各领域地图维护。

| 想查的机制 | 正文入口 |
|---|---|
| MCP、用户委托与本地工具执行 | [MCP 连接与鉴权](../ai-engineering/actions/mcp-protocol.md)、[OAuth 委托凭据](../ai-engineering/actions/authorization-gates-for-actions.md#第三关：凭据面向哪个资源，带哪些%20scope？)、[coding harness](../ai-engineering/actions/coding-agent-harness.md) |
| LangGraph、重规划与记忆 | [LangGraph 的恢复边界](../ai-engineering/runs/langgraph-recovery-boundaries.md)、[计划执行与重规划](../ai-engineering/actions/multi-stage-orchestration.md#计划执行与重规划)、[跨运行的信息](../ai-engineering/context/context-budget-and-state-layers.md#跨运行的信息：范围、写入、读取、更新、遗忘)、[记忆加工的净收益](../ai-engineering/context/agent-memory-design-and-evaluation.md) |
| 模型配额、prompt cache 与向量索引 | [速率额度与截止时间](../ai-engineering/runs/bounded-model-api-calls.md#把速率额度换算成可复算的上限)、[prompt cache 承诺了什么](../ai-engineering/model/prefix-reuse-and-prompt-caching.md#API%20的%20prompt%20cache%20承诺了什么？)、[HNSW](../ai-engineering/context/hnsw-vector-index-search.md) |
| debounce、throttle、Promise 与结构相等 | [防抖与节流](../frontend/javascript/wrapping-functions.md#debounce%20与%20throttle：闭包里的计时状态)、[Promise 组合器](../frontend/javascript/promises-and-async-functions.md#组合器各在什么时候结束)、[有界并发池](../frontend/javascript/cancellation-timeouts-and-concurrency.md#有界并发池：五页明细，同时最多两页)、[结构相等](../frontend/javascript/values-types-and-equality.md#结构相等：先写契约再比较) |
| Context、编辑草稿与聊天状态 | [状态所有权与 Context](../frontend/ui-state/state-ownership-and-composition.md#Context：远距离读取同一份值)、[编辑会话与条件保存](../frontend/ui-state/editing-sessions-and-conditional-writes.md)、[流式聊天](../frontend/ui-state/streaming-ai-chat.md) |
| 会话、授权与 HTTP 缓存 | [Cookie 会话与 OIDC](../engineering-foundations/services/sessions-and-browser-boundaries.md)、[逐次授权](../engineering-foundations/services/per-request-authorization.md)、[HTTP 缓存与条件请求](../engineering-foundations/services/http-caching-and-conditional-requests.md) |
| 条件写、回调与持久队列 | [数据库条件写](../engineering-foundations/data/conditional-writes-and-idempotent-records.md)、[ETag 条件更新](../engineering-foundations/services/conditional-updates-and-etags.md)、[Webhook](../engineering-foundations/services/webhook-delivery-and-verification.md)、[任务领取与栅栏](../engineering-foundations/services/job-claims-leases-and-fencing.md)、[Kafka offset](../engineering-foundations/services/kafka-partitions-and-offsets.md) |
| 类型、构建产物与渐进迁移 | [运行时验证](../frontend/javascript/typescript-guarantees-and-runtime-validation.md)、[构建流水线](../frontend/delivery/build-pipeline-and-bundling.md)、[哈希发布与缓存](../frontend/delivery/hashed-release-and-caching.md)、[微前端共存与回退](../engineering-foundations/practice/canary-rollout-and-rollback.md#微前端：独立部署的前端怎样共存与回退？) |
| 数据分布与存储引擎 | [分片键与热点](../engineering-foundations/data/sharding-and-hot-keys.md)、[分片搬迁](../engineering-foundations/data/shard-migration-and-ownership-transfer.md)、[InnoDB 索引、锁与日志](../engineering-foundations/data/mysql-innodb-locks-and-logs.md)、[预写日志与恢复](../engineering-foundations/data/write-ahead-logging-and-recovery.md) |
| Python 属性解析 | [描述符、方法绑定与 MRO](../engineering-foundations/runtime/python-object-model.md#属性查找与%20MRO) |
| 部署身份与密钥 | [构建期凭据](../engineering-foundations/practice/container-images-and-builds.md#构建期凭据只在一条%20RUN%20里出现)、[运行角色的凭据](../engineering-foundations/practice/production-runtime.md#每个运行角色拿着哪种凭据)、[注入密钥的更新](../engineering-foundations/practice/production-runtime.md#注入的密钥要替换任务才会更新) |
| 窗口、优先级与搜索路径 | [窗口与区间扫描](../engineering-foundations/computation/sliding-windows-and-sweep-lines.md)、[堆](../engineering-foundations/computation/heaps-and-priority-queues.md)、[图搜索与回溯](../engineering-foundations/computation/graph-search-and-backtracking.md)、[文本单位](../engineering-foundations/computation/text-units-and-unicode.md)、[Trie](../engineering-foundations/computation/data-structures-by-access-pattern.md#按前缀查找：Trie) |

## 阅读记录与资料

- [本轮阅读进度](reading-progress.md)只记录本轮读过哪些正文。
- [AI 好文集](ai-literature-index.md)按问题收集来源及其知识落点。
- [归档](../archive/index.md)保留课程推导、作者解法、原始材料和专门参考。
