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

## 执行循环 / Agent loop

一个常见智能体循环如下：

1. **模型决定（decide）：** 根据当前目标、状态和可用能力，继续推理、请求工具、提问或结束。
2. **运行时执行（execute）：** 校验调用格式、授权范围与业务条件，再执行实际函数或外部操作。
3. **环境观察（observe）：** 取得成功结果、错误、部分结果或人工反馈。
4. **更新状态（update）：** 将有用观察与任务状态提供给下一次模型调用。
5. **停止或继续（stop or continue）：** 检查完成条件、预算、最大动作数、超时及是否需要人类判断。

函数调用只是模型提出的结构化请求；API、运行时或用户界面才会实际执行它。每次模型推理只能使用当前请求或已配置的会话状态，不能假定模型有未显式保存的持久记忆。

**退款例子：** 收集客户、订单和支持历史属于可并发的只读工作；退款金额必须在核实订单后计算，执行前还要通过权限与业务规则检查。若退款执行超时，结果可能未知；应先用操作 ID 查询是否已成功，再决定是否重试，而不是盲目重复写操作。工具的调用与恢复契约见[工具设计与函数调用](./tool-design-and-function-calling.md)。

停止条件应在系统里实现，而不只写在提示词里：完成、需要补充信息、转交人工、不可恢复的错误或预算耗尽都应有明确结果。最大轮数、总调用数、超时和费用上限能限制失控运行；监测重复调用可作为额外信号，但不能代替业务停止条件。具体的授权、隔离、停止和人工接管边界见[生产环境 AI 安全](../safety/ai-safety-in-production.md)。

An observation updates the current run. A change that should apply across later runs needs a baseline, external evidence, and a retained version. / 观察会更新当前运行。若变更要延续到后续运行，就需要基线、外部证据与可保留的版本。[How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？](agent-improvement-and-version-acceptance.md)

## 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；命名空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

## 相关知识

- [编排模式](./orchestration-patterns.md)：决定步骤、并行、路由或多智能体结构。
- [上下文工程原则](../context/context-engineering-principles.md)：管理长任务中的历史、外部状态与缓存。
- [工具设计与函数调用](./tool-design-and-function-calling.md)：定义运行时如何执行模型请求。
- [LLM 评估方法](../evaluation/llm-evaluation-methods.md)：区分任务反馈、变更验收与持久版本。
