# When should a model control the next step? / 何时应让模型决定下一步？

**Short answer / 简答：** Use an AI agent when the task needs the model to choose among next steps from intermediate observations, and that flexibility is worth the added cost, latency, and operational risk. Keep fixed steps in code where they already meet the task’s success criteria.

当任务需要模型根据中间观察选择下一步，且这种灵活性值得其额外成本、时延和运行风险时，才让模型充当智能体。若固定步骤已满足任务成功标准，就继续由代码控制流程。

## 智能体、工作流、聊天与 RAG

“智能体”的定义并不完全统一。[Anthropic 将 workflow 与 agent 都放在 agentic systems 范围内，并以控制流由代码预先定义还是由模型动态决定来区分；OpenAI 的定义也强调模型管理任务流程并按状态选择工具。](https://www.anthropic.com/engineering/building-effective-agents) [OpenAI agent 指南](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) 因而，是否调用过工具、调用几次，不是可靠的唯一判据。

| 概念 | 核心特征 |
|---|---|
| **工作流（workflow）** | 程序定义步骤、顺序和分支；模型在指定节点完成分类、抽取或生成。 |
| **智能体（agent）** | 模型根据目标与观察结果选择工具或下一步；运行时负责执行、限制和停止。 |
| **聊天界面（chat interface）** | 用户交互形态，可以只是问答，也可以包在工作流或智能体外。 |
| **检索增强生成（RAG）** | 把检索内容交给模型的一种架构能力；它可以是单次流程中的一步，也可以供智能体迭代调用。 |

一次工具调用后返回，不足以判断系统是否“真正是 agent”；应描述模型实际拥有多少流程控制权。例如，客服退款可以由固定工作流处理合规检查，只让模型分类用户意图；如果系统需要调查多种来源、根据发现决定后续步骤，才可能值得交给智能体控制。

## 选择工作流还是智能体

先用能够满足任务成功标准的最简单结构，再用实际任务评估是否需要更大自主性。Anthropic 将工作流的可预测性与智能体对开放式任务的适应性作了区分，也提醒智能体可能增加成本和累积错误；这是一种设计权衡，不是“分支超过某个数量就必须用 agent”的定律。

| 任务形状 | 较合适的起点 | 例子 |
|---|---|---|
| 步骤固定、输入类别有限、结果可验证 | 代码工作流 | 校验订单 → 计算退款金额 → 执行退款 → 发送回执 |
| 后续步骤依赖未知的中间发现 | 有预算与停止条件的智能体 | 调查复杂故障时，根据日志和测试结果决定继续查哪一处 |
| 大部分步骤固定，少数探索性任务开放 | 混合架构 | 固定工单流程中，允许智能体在“诊断”节点调查日志 |

评估时比较任务成功率、错误类型、总延迟、模型与工具成本、人工接管率。多轮运行可能更贵、更慢，但不存在固定的“每多一步就按同一倍数增长”的通用比例；缓存、工具耗时、输出长度和模型价格都会改变结果。

## ReAct and the decision loop / ReAct 与决策循环

ReAct 的关键是让外部观察改变下一步。论文在 PaLM 的少样本提示里交错放入推理文字、任务动作和环境观察。推理文字用于记录进度、分解问题和调整动作，环境只对实际动作返回新观察。以 HotpotQA 为例，模型先查实体，再根据返回的段落找第二条证据。表 1 中，ReAct 在 HotpotQA 与 FEVER 上优于仅行动基线，和仅 CoT 的比较则随任务而变。检索也可能不给有用信息，论文观察到重复查询和错误传播。结论适用于论文的模型、工具和任务设置。 [Yao et al., arXiv v3, §2、图 1、§3.3 与表 1](https://arxiv.org/html/2210.03629v3)

生产中的可复用机制是 **decide → act → observe / 决策 → 行动 → 观察**。系统可用结构化工具调用和简短计划摘要承接这条反馈环。对执行的解释与审计应依赖实际调用、参数、权限决定和观测结果。运行时无需索取或保存模型的内部推理。

| 运行中的环节 | 谁负责 | 给下一环节什么 |
| --- | --- | --- |
| 决策 | 模型看到当前任务、可用工具和已验证的观察 | 结构化动作、向用户提问，或提交结果供验收 |
| 授权与执行 | 运行时校验 schema、当前权限和业务前置条件 | 执行结果、明确错误、审批要求，或结果未知的状态 |
| 观察与更新 | 运行时核对来源与调用 ID，保存必要状态 | 新证据和剩余预算，供模型决定下一步 |
| 验收与停止 | 运行时按完成条件、预算和取消状态收尾 | 已完成、等待输入、转人工、失败或待确认的终态或暂停态 |

用一笔退款跟踪循环。订单查询返回“已付款”，但缺少优惠券是否退回的信息。下一步选读适用规则或询问用户补齐资料。资料齐备后，由应用计算金额并验证审批条件。如果退款服务超时，观察结果是 `outcome_unknown`。此时应用以操作 ID 查询权威状态，在确定安全之前阻止再次写入。允许 Agent 选择查哪条资料，仍可让程序固定退款的授权和执行。相反，若任务只是查同一日期、同一币种的航班报价，查询返回 189、210、175 美元后，固定代码即可给出此次查询的最低报价 175 美元。

每轮执行完检查完成条件、总调用数、时间与预算。持续收到同一无进展结果时，可以换一个已允许的查证动作，或停止并说明证据缺口。长任务将进度和真实结果持久化，恢复时读取原状态，不让模型靠对话回忆猜测写入是否发生。工具请求、幂等和错误语义见 [工具设计与函数调用](./tool-design-and-function-calling.md)，恢复与事件回放见 [持久化 AI 运行](../systems/ai-application-architecture.md)。

评估时，把同一组任务交给固定工作流和 Agent，比较完成率、写入结果、权限违规、重复动作、成本和延迟。τ-bench 同时检查任务结束后的数据库状态与必须告知用户的信息。后续 τ²-bench 的电信任务还让模拟用户与 Agent 使用不同工具操作同一个环境，暴露了只测试单方动作时看不到的协调失败。将这类变化变成自己的测试用例，例如用户改完设置后要重新读状态，再决定是否执行后续动作。 [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [τ-bench](https://arxiv.org/abs/2406.12045) · [τ²-bench](https://arxiv.org/abs/2506.07982)

An observation updates the current run. A change that should apply across later runs needs a baseline, external evidence, and a retained version. / 观察会更新当前运行。若变更要延续到后续运行，就需要基线、外部证据与可保留的版本。[How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](agent-improvement-and-version-acceptance.md)

## 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；命名空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

## 相关知识

- [编排模式](./orchestration-patterns.md)：决定步骤、并行、路由或多智能体结构。
- [上下文工程原则](../context/context-engineering-principles.md)：管理长任务中的历史、外部状态与缓存。
- [工具设计与函数调用](./tool-design-and-function-calling.md)：定义运行时如何执行模型请求。
- [LLM 评估方法](../evaluation/llm-evaluation-methods.md)：区分任务反馈、变更验收与持久版本。
