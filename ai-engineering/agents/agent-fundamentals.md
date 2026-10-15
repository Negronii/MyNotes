# Agent Fundamentals | 智能体基础

**核心解释 / Core explanation：** 智能体（AI agent）让模型在明确边界内决定下一步，并依据工具或环境返回的结果继续任务。An AI agent lets a model choose task steps within defined boundaries and adapt to tool or environment feedback.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 工作流由代码安排模型何时做什么；智能体把部分控制权交给模型，让它根据中间结果选择下一步。是否使用智能体取决于任务是否需要这种灵活性，以及它能否带来足以抵偿成本、延迟和新故障面的收益。
- **English:** A workflow uses code to define when the model acts; an agent gives the model some control to choose the next step from intermediate results. I use an agent only when that flexibility improves task outcomes enough to justify its cost, latency, and operational risk.

## 智能体、工作流、聊天与 RAG

**智能体（AI agent）** 的定义并不完全统一。[Anthropic 将 workflow 与 agent 都放在 agentic systems 的范围内，并以控制流由代码预先定义还是由模型动态决定来区分；OpenAI 的定义也强调模型管理任务流程并按状态选择工具。](https://www.anthropic.com/engineering/building-effective-agents) [OpenAI 的 agent 指南](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) 因而，是否调用过工具、调用几次，不是可靠的唯一判据。

| 概念 | 核心特征 |
|---|---|
| **工作流（workflow）** | 程序定义步骤、顺序和分支；模型在指定节点完成分类、抽取或生成。 |
| **智能体（agent）** | 模型根据目标与观察结果选择工具或下一步；运行时负责执行、限制和停止。 |
| **聊天界面（chat interface）** | 用户交互形态，可以只是问答，也可以包在工作流或智能体外。 |
| **检索增强生成（RAG）** | 一种把检索内容交给模型的架构能力；它可以是单次流程中的一步，也可以供智能体迭代调用。 |

一次工具调用后返回，不足以判断系统是否“真正是 agent”；应描述模型实际拥有多少流程控制权。比如，客服退款可以由固定工作流处理合规检查，只让模型分类用户意图；如果系统需要调查多种来源、根据发现决定后续步骤，才可能值得交给智能体控制。

## 选择工作流还是智能体

先用能满足成功标准的最简单结构，再通过实际任务评估是否需要更大自主性。Anthropic 将工作流的可预测性与智能体对开放式任务的适应性作了区分，也提醒智能体可能增加成本和累积错误；这是一种设计权衡，不是“分支超过某个数量就必须用 agent”的定律。

| 任务形状 | 较合适的起点 | 例子 |
|---|---|---|
| 步骤固定、输入类别有限、结果可验证 | 代码工作流 | 校验订单 → 计算退款金额 → 执行退款 → 发送回执 |
| 后续步骤依赖未知的中间发现 | 有预算与停止条件的智能体 | 调查复杂故障时，根据日志和测试结果决定继续查哪一处 |
| 大部分步骤固定，少数探索性任务开放 | 混合架构 | 固定工单流程中，允许智能体在“诊断”节点调查日志 |

评估时比较任务成功率、错误类型、总延迟、模型与工具成本、人工接管率。多轮运行可能更贵、更慢，但并不存在固定的“每多一步就按同一倍数增长”的通用比例；缓存、工具耗时、输出长度和模型价格都会改变结果。

## 执行循环 / Agent loop

一个常见循环是：

1. **模型决定（decide）：** 根据当前目标、状态和可用能力，继续推理、请求工具、提问或结束。
2. **运行时执行（execute）：** 校验调用格式、授权范围与业务条件，再执行实际函数或外部操作。
3. **环境观察（observe）：** 取得成功结果、错误、部分结果或人工反馈。
4. **更新状态（update）：** 将有用观察与任务状态提供给下一次模型调用。
5. **停止或继续（stop or continue）：** 检查完成条件、预算、最大动作数、超时及是否需要人类判断。

函数调用只是模型提出的结构化请求；API、运行时或用户界面才会实际执行它。每次模型推理只能使用当前请求或已配置的会话状态，不能假定模型有未显式保存的持久记忆。

**退款例子：** 收集客户、订单和支持历史属于可并发的只读工作；退款金额必须在核实订单后计算，执行前还要通过权限与业务规则检查。若退款执行超时，结果可能未知；应先用操作 ID 查询是否已成功，再决定是否重试，而不是盲目重复写操作。具体工具契约见[工具设计与函数调用](./tool-design-and-function-calling.md)。

停止条件应在系统里实现，而不只写在提示词里：完成、需要补充信息、转交人工、不可恢复的错误或预算耗尽都应有明确结果。最大轮数、总调用数、超时和费用上限能限制失控运行；监测重复调用可作为额外信号，但不能代替业务停止条件。

## 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统的权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；名称空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

## 相关知识

- [编排模式](./orchestration-patterns.md)：选择顺序、并行、路由或多智能体结构。
- [上下文工程原则](../context/context-engineering-principles.md)：管理长任务中的历史、外部状态与缓存。
