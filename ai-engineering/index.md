# AI 工程

模型是一个按输入算出下一个词元概率的函数。它内部怎么算，决定了每次调用的代价。AI 应用要可靠，得由应用替它决定看见什么、放行什么动作、出事后怎样既不丢结果也不重复，并用可复核的证据决定哪个版本留下。

第一次读，从[一次 AI 回答经过了哪几步？](overview/how-an-ai-answer-is-produced.md)开始。它跟着 CI 诊断助手解释一次构建失败，走完五步，每一步引出下面一条主线。

## 五条主线

### 一、模型怎样算出下一个词元，代价落在哪？

文本先变成词元，再变成向量，逐层经过 attention 和 FFN，最后为词表打分、采样。训练用每个位置的预测误差更新这些参数。生成时每层留下 KV：每条有多宽、一共多少条，决定了显存和能接的并发；长上下文架构都在改这几个量。重复的前缀可以复用计算，这在 API 账单上体现为 prompt cache。

- [模型怎样把提示词算成下一个词元？](model/next-token-computation.md)
  - 支线：[MoE、mHC 和 MTP 分别改了 Transformer 的哪一块？](model/architecture-variants.md)
- [训练怎样让这些参数变得更会预测？](model/how-training-updates-parameters.md)
- [KV 缓存怎样决定一台服务能接多少请求？](model/kv-cache-and-serving-capacity.md)
  - 支线：[DeepSeek 怎样压缩长上下文的注意力状态？](model/deepseek-compressed-attention.md)
  - 支线：[Kimi Delta Attention 怎样用一张固定矩阵读写历史？](model/kimi-delta-attention-state.md)
  - 支线：[推测解码怎样加速又不改变输出分布？](model/speculative-decoding.md)
- [重复的前缀怎样在引擎里复用，又怎样体现在 API 账单上？](model/prefix-reuse-and-prompt-caching.md)

### 二、模型每次该看见什么，才能凭证据回答？

模型只看见这一次组装好的输入。提示词把任务、证据、推断边界和输出格式写成契约。上下文要在预算内挑选、压缩、按需读取，权威记录留在应用。事实从有版本、有权限的来源检索，回答逐条对上证据，对不上就停；答错时沿同一条失败定位链找出坏掉的一环。

- [模型这次能看见什么，提示词该怎样写成可验收的契约？](context/model-input-and-prompt-contract.md)
  - 支线：[简单提示失败后，怎样选择并评估提示技巧？](context/prompting-techniques-after-failure.md)
- [每次调用的上下文预算该怎样分配，哪些状态必须留在应用里？](context/context-budget-and-state-layers.md)
  - 支线：[Claude Code、Codex、Devin 和 Cursor 怎样恢复同一条任务事实？](context/coding-agent-task-recovery.md)
- [怎样从授权文档里找到回答依据？](context/rag-indexing-and-retrieval.md)
  - 支线：[HNSW 怎样逐层找近邻，怎样知道搜索得够不够？](context/hnsw-vector-index-search.md)
- [回答写好后，怎样逐条核对证据，答错时又怎样找到坏掉的一环？](context/claim-verification-and-failure-localization.md)
- [什么时候值得把历史加工成 Agent 记忆？](context/agent-memory-design-and-evaluation.md)

### 三、模型提出的动作，应用凭什么放行？

先判断控制流该不该交给模型。模型只是提出结构化请求，schema 只能限制请求的形状。放行要依次过五道关：工具对本轮是否可见、调用者有没有权限、凭据给谁用和授权范围、用户批准的是不是这一份草稿、在什么环境里执行。进入上下文的内容永远不会因此获得权限。放行后留下的记录，正是主线四恢复时读取的状态。

- [什么时候该让模型决定下一步？](actions/when-the-model-decides.md)
- [模型“调用工具”时实际发生了什么，工具契约该怎样设计？](actions/tool-calls-are-requests.md)
  - 支线：[MCP 2026-07-28 怎样把工具从发现接到有权限的执行？](actions/mcp-protocol.md)
- [模型提出 `create_issue` 后，应用要过哪几道关才能放行？](actions/authorization-gates-for-actions.md)
  - 支线：[模型选到 shell 或文件工具后，由谁决定能否执行？](actions/coding-agent-harness.md)
- [为什么提示注入防不住“模型听话”，应用该在哪里拦？](actions/prompt-injection-as-permission-confusion.md)
- [多阶段 AI 任务该按什么结构组织，怎样知道它在原地打转？](actions/multi-stage-orchestration.md)

### 四、动作执行到一半出事，怎样既不丢结果也不重复？

运行的权威状态由应用自己持有，几层身份各自只证明一件事。受理后靠 outbox 保证入队，执行时靠租约和递增编号防止两个进程同时推进。发出外部请求前先存下发送意图；结果不明时只读对账，只有对方的去重窗口仍有效时才用原键重发。取消和断线是两回事。所有等待共用一个截止时间，重试只由一处负责。

- [一次 AI 运行断线或崩溃后，凭什么恢复？](runs/run-identity-and-authoritative-state.md)
- [怎样让一次模型 API 调用在限额、失败和截止时间内有界？](runs/bounded-model-api-calls.md)
- [请求受理后，怎样保证任务最终被执行且不被两个 worker 同时推进？](runs/accepting-queuing-and-claiming-runs.md)
- [退款请求超时后，怎样查清结果而不重复扣款？](runs/external-writes-and-reconciliation.md)
  - 支线：[LangGraph 能恢复什么，又不替应用记住什么？](runs/langgraph-recovery-boundaries.md)
  - 支线：[用户撤权或令牌失效后，进行中的写入怎样安全恢复？](runs/revocation-and-reauthorization.md)
- [用户断线、取消或要回答一个问题时，同一次运行怎样继续？](runs/disconnect-cancel-and-user-input.md)

### 五、改动怎样证明值得保留并上线？

先把“好”写成可检查的任务契约。用开发集调候选，再用冻结的独立验收集做配对比较；分母按观察单位定。线上用 trace 把失败接回定位链，用户反馈有偏，只能当候选样本的来源。每次只改一层，顺序是提示词、上下文、工具、脚手架，最后才是权重。发布的是一整套版本组合，分阶段放量；回滚撤不回已经发生的副作用。

- [“回答得好”怎样写成可检查的任务契约？](evaluation-and-release/task-contracts-and-quality-dimensions.md)
- [候选 B 比 A 好，是真改善还是抽样波动？](evaluation-and-release/holdout-acceptance-and-paired-statistics.md)
- [上线后，怎样从一条错误建议找回可修复的证据？](evaluation-and-release/production-traces-and-metric-denominators.md)
- [让助手以后不再误诊，该改提示词、工具、脚手架还是权重？](evaluation-and-release/choosing-what-to-change.md)
  - 支线：[什么时候该微调，LoRA、SFT 和 DPO 各改了什么？](evaluation-and-release/fine-tuning-lora-sft-dpo.md)
  - 支线：[训练损失怎样变成每个权重矩阵的更新？](evaluation-and-release/training-gradients-and-optimizers.md)
  - 支线：[可验证奖励怎样训练推理能力？](evaluation-and-release/reward-based-reasoning-training.md)
  - 支线：[研究里的自动改进方法，哪些证据能借到工程里？](evaluation-and-release/automated-improvement-research.md)
- [月报助手该选哪个模型，每份成功报告要花多少钱？](evaluation-and-release/model-selection-and-unit-cost.md)
- [候选版本从离线通过到全量，要经过哪些关，回滚又撤得回什么？](evaluation-and-release/deployment-rollout-and-rollback.md)

### 收尾

- [拿到一道 AI 系统设计题，怎样从风险推导出架构？](design-cases/ai-system-design-cases.md)：文档问答、退款和代码审查三道题，用五条主线的结论推导架构与发布证据。

## 论文与文章

- [AI 好文集](../review/ai-literature-index.md)——按主题查找值得读的来源，以及解释其贡献的章节。

## Reading order / 阅读顺序

### 序章

- [一次 AI 回答经过了哪几步？](overview/how-an-ai-answer-is-produced.md)

### 模型怎样算出下一个词元，代价落在哪？

- [模型怎样把提示词算成下一个词元？](model/next-token-computation.md)
- [MoE、mHC 和 MTP 分别改了 Transformer 的哪一块？](model/architecture-variants.md)
- [训练怎样让这些参数变得更会预测？](model/how-training-updates-parameters.md)
- [KV 缓存怎样决定一台服务能接多少请求？](model/kv-cache-and-serving-capacity.md)
- [DeepSeek 怎样压缩长上下文的注意力状态？](model/deepseek-compressed-attention.md)
- [Kimi Delta Attention 怎样用一张固定矩阵读写历史？](model/kimi-delta-attention-state.md)
- [推测解码怎样加速又不改变输出分布？](model/speculative-decoding.md)
- [重复的前缀怎样在引擎里复用，又怎样体现在 API 账单上？](model/prefix-reuse-and-prompt-caching.md)

### 模型每次该看见什么，才能凭证据回答？

- [模型这次能看见什么，提示词该怎样写成可验收的契约？](context/model-input-and-prompt-contract.md)
- [简单提示失败后，怎样选择并评估提示技巧？](context/prompting-techniques-after-failure.md)
- [每次调用的上下文预算该怎样分配，哪些状态必须留在应用里？](context/context-budget-and-state-layers.md)
- [Claude Code、Codex、Devin 和 Cursor 怎样恢复同一条任务事实？](context/coding-agent-task-recovery.md)
- [怎样从授权文档里找到回答依据？](context/rag-indexing-and-retrieval.md)
- [HNSW 怎样逐层找近邻，怎样知道搜索得够不够？](context/hnsw-vector-index-search.md)
- [回答写好后，怎样逐条核对证据，答错时又怎样找到坏掉的一环？](context/claim-verification-and-failure-localization.md)
- [什么时候值得把历史加工成 Agent 记忆？](context/agent-memory-design-and-evaluation.md)

### 模型提出的动作，应用凭什么放行？

- [什么时候该让模型决定下一步？](actions/when-the-model-decides.md)
- [模型“调用工具”时实际发生了什么，工具契约该怎样设计？](actions/tool-calls-are-requests.md)
- [MCP 2026-07-28 怎样把工具从发现接到有权限的执行？](actions/mcp-protocol.md)
- [模型提出 `create_issue` 后，应用要过哪几道关才能放行？](actions/authorization-gates-for-actions.md)
- [模型选到 shell 或文件工具后，由谁决定能否执行？](actions/coding-agent-harness.md)
- [为什么提示注入防不住“模型听话”，应用该在哪里拦？](actions/prompt-injection-as-permission-confusion.md)
- [多阶段 AI 任务该按什么结构组织，怎样知道它在原地打转？](actions/multi-stage-orchestration.md)

### 动作执行到一半出事，怎样既不丢结果也不重复？

- [一次 AI 运行断线或崩溃后，凭什么恢复？](runs/run-identity-and-authoritative-state.md)
- [怎样让一次模型 API 调用在限额、失败和截止时间内有界？](runs/bounded-model-api-calls.md)
- [请求受理后，怎样保证任务最终被执行且不被两个 worker 同时推进？](runs/accepting-queuing-and-claiming-runs.md)
- [退款请求超时后，怎样查清结果而不重复扣款？](runs/external-writes-and-reconciliation.md)
- [LangGraph 能恢复什么，又不替应用记住什么？](runs/langgraph-recovery-boundaries.md)
- [用户撤权或令牌失效后，进行中的写入怎样安全恢复？](runs/revocation-and-reauthorization.md)
- [用户断线、取消或要回答一个问题时，同一次运行怎样继续？](runs/disconnect-cancel-and-user-input.md)

### 改动怎样证明值得保留并上线？

- [“回答得好”怎样写成可检查的任务契约？](evaluation-and-release/task-contracts-and-quality-dimensions.md)
- [候选 B 比 A 好，是真改善还是抽样波动？](evaluation-and-release/holdout-acceptance-and-paired-statistics.md)
- [上线后，怎样从一条错误建议找回可修复的证据？](evaluation-and-release/production-traces-and-metric-denominators.md)
- [让助手以后不再误诊，该改提示词、工具、脚手架还是权重？](evaluation-and-release/choosing-what-to-change.md)
- [什么时候该微调，LoRA、SFT 和 DPO 各改了什么？](evaluation-and-release/fine-tuning-lora-sft-dpo.md)
- [训练损失怎样变成每个权重矩阵的更新？](evaluation-and-release/training-gradients-and-optimizers.md)
- [可验证奖励怎样训练推理能力？](evaluation-and-release/reward-based-reasoning-training.md)
- [研究里的自动改进方法，哪些证据能借到工程里？](evaluation-and-release/automated-improvement-research.md)
- [月报助手该选哪个模型，每份成功报告要花多少钱？](evaluation-and-release/model-selection-and-unit-cost.md)
- [候选版本从离线通过到全量，要经过哪些关，回滚又撤得回什么？](evaluation-and-release/deployment-rollout-and-rollback.md)

### 收尾

- [拿到一道 AI 系统设计题，怎样从风险推导出架构？](design-cases/ai-system-design-cases.md)

## 跨域脉络

生产级 AI 应用依赖通用网络与安全机制：[HTTP 请求](../engineering-foundations/networking/http-protocols-and-websockets.md)解释单次交换，[轮询、SSE 与 WebSocket](../engineering-foundations/networking/real-time-web-updates.md)解释持续更新；[Cookie 会话与 OIDC](../engineering-foundations/security/web-sessions-and-oidc.md)建立身份，[租户资源授权](../engineering-foundations/security/web-security-and-authentication.md)决定每次操作能访问什么。聊天界面怎样应用重放事件，见前端的 [AI 聊天界面](../frontend/browser-apis/streaming-ai-chat.md)。
