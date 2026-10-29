# Orchestration Patterns | 编排模式

**核心解释 / Core explanation：** 编排（orchestration）决定任务由哪些模型调用或智能体完成，以及它们如何传递状态和结果。Orchestration defines which model calls or agents handle a task and how they pass state and results.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 我先看步骤是否固定、子任务是否独立、后续任务是否依赖前序结果，再选择工作流或智能体模式。只有并行、上下文隔离、能力隔离等收益经评估足以覆盖通信、延迟和协调成本时，才拆成多个智能体。
- **English:** I choose an orchestration pattern based on whether steps are known, subtasks are independent, and later work depends on earlier results. I split into multiple agents only when measured gains in parallelism or capability and context isolation justify the coordination cost.

Anthropic 的模式目录区分固定路径的 workflow 与模型驱动的 agent，并强调模式可以组合，复杂度应由效果而不是新颖程度决定。[下列模式来源于其一手说明。](https://www.anthropic.com/engineering/building-effective-agents)

## 固定流程：由代码决定控制流

| 模式 | 适用任务 | 机制与例子 |
|---|---|---|
| **提示链（prompt chaining）** | 子任务能按固定顺序拆分 | 摘要 → 抽取实体 → 起草答复；在边界加程序校验，避免错误直接传到下一步。 |
| **路由（routing）** | 输入类别对应不同处理路径 | 分类为退款、售前或技术支持，再交给对应流程。分类不确定时设置兜底或澄清路径。 |
| **并行化（parallelization）** | 子任务彼此独立，或需要多个尝试 | **分片（sectioning）**：同时总结文档不同章节；**投票（voting）**：多次独立评审后按预定义规则汇总。投票会增加调用成本，汇总规则也要针对错误类型评估。 |
| **评估器—优化器（evaluator–optimizer）** | 有清楚的质量标准，反馈确实能改进结果 | 生成代码 → 执行测试 → 根据测试失败修订。设定最大迭代数；若评估器与生成器共享偏差，增加测试或人工依据，不应假设换一个模型就能消除偏差。 |

这些名称表示常见结构，不是互斥的架构类别。路由可以进入提示链；并行工作可以由确定性代码派发；评估循环也可以嵌入较大的智能体任务。

## 开放式任务：Orchestrator–workers

**编排者—工作者（orchestrator–workers）** 由一个编排者模型在运行时拆分不确定的子任务，派发给工作者，再综合结果。它适合无法事先列出完整子任务的工作，例如根据代码库和需求决定要检查哪些文件；如果任务边界已知，固定并行调用通常更简单。

典型流程：

1. 编排者明确目标与可验证的交付标准。
2. 工作者各自接收范围、必要上下文、权限和结果格式。
3. 可并发的任务同时运行；有依赖的步骤按序等待。
4. 编排者核对结果、处理冲突与缺口，再交付结论。

将工作交给另一个 agent 不会自动带来上下文隔离。要由运行时明确决定共享哪些会话状态、传递哪些证据、工作者可以访问哪些工具，以及主流程接收完整记录还是摘要。相关权衡见[上下文工程原则](../context/context-engineering-principles.md)。

## 多智能体：委托工具还是交接所有权

主流 SDK 采用不同命名，但可按谁负责最终答复来理解：

| 结构 | 谁保留用户交互控制权 | 适合场景 |
|---|---|---|
| **智能体作为工具（agents as tools）／管理者模式（manager pattern）** | 管理者调用专家，把返回结果纳入自己的答复 | 专家做边界明确的研究、分类或摘要；主 agent 需要比较并综合多个结果。 |
| **交接（handoff）** | 专家接管后续流程或用户对话 | 识别到明确专业领域后，由该专家负责处理。 |

例如，客服分类 agent 可将技术问题交给技术支持 agent；如果客服 agent 还必须比较订单状态、退款政策与支持历史，则可把这些调查工作委托为工具并保留最终答复权。[OpenAI 的编排文档以“交接”与“智能体作为工具”说明了这一控制权区别。](https://developers.openai.com/api/docs/guides/agents/orchestration)

不论哪种结构，都要约定交接输入、输出契约、状态归属、最大交接深度和失败回退。否则专家之间可能反复转交、丢失客户/订单 ID，或对同一副作用重复执行。

## 先尝试单主循环，再验证拆分 / Start with one loop, then test delegation

**核心建议 / Core guidance：** 后续步骤仍依赖同一任务状态时，先尝试一个主循环；只有可独立并行、需要隔离验证或具备真实能力边界的子任务显示出收益时，再拆分。When later steps depend on shared task state, start with one main loop; split only when independent parallel work, isolated verification, or an enforced capability boundary provides a measured benefit.

拆分的理由是具体的任务边界，而不是某个工具数量阈值：

- **独立工作可并行：** 各自读取不同资料，最终可以汇总；确认没有共享写入冲突。
- **需要上下文隔离：** 专家只拿到完成子任务所需信息，主 agent 接收可核验摘要。
- **策略或权限应隔离：** 不同工作者拥有不同的知识范围、工具和访问权限。
- **单个上下文过于混杂：** 实测表明工具重叠、指令冲突或长历史降低了成功率。

技能和工具搜索可渐进地把程序或能力载入主上下文；并行工具调用本身不要求新建 subagent。[Anthropic / Diane Sarkis 的 folding 文章（2026-10-22，“Using an agent loop with progressive disclosure”“Task-completion evals”等章节）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)建议先建立端到端基线，再逐个折叠 subagent，检查任务成败变化、生产链路和必须遵守的规则，并在重复运行中比较；合并时保留领域流程。独立研究、并行探索和验证仍可适合独立 worker；权限隔离只有在运行时真正限制能力时才成立。额外 agent 会增加模型调用、数据传递、追踪和协调点。不要把“15 个工具”或其他固定数写成普适分界线。

GitSwarm 提供了适用范围不同的例子：异步 worker 自主选择工作，在可分支的共享 Git 仓库中发布可组合产物；执行 harness 仍负责调度和发布验证，该验证检查提交要求而不认证产物正确性。[GitSwarm（v1，2026-10-04，§§2.1–2.3）](https://arxiv.org/html/2610.04862v1)不设中央“intellectual planner”（智能规划器）替 workers 指派探索方向，也不取消执行协调；它支持把独立、可检查的产物作为拆分条件，但不证明普通任务都应使用多 agent。状态取舍见[上下文工程原则](../context/context-engineering-principles.md)，比较拆分效果见[LLM 评估方法](../evaluation/llm-evaluation-methods.md)。

## 提示模板仍是单 agent 的选项

面对角色、领域或策略不同但结构相似的任务，可使用一个明确模板传入少量、语义一致的变量，代替维护多份近似提示。变量过多或互相矛盾仍会让提示难以理解；应通过代表性输入评估模板，而不是只检查文本形式。

## 运行与观测

对每个节点、工具调用、agent、重试与交接记录关联的任务 ID、输入输出引用、状态、延迟、错误与模型/工具用量。结果应能回答：任务是否完成，哪个步骤导致失败，实际执行了几次外部副作用，谁接管了用户流程。日志内容需符合数据保留和隐私要求。

## 相关知识

- [智能体基础](./agent-fundamentals.md)：工作流与 agent 的控制流边界及运行循环。
- [工具设计与函数调用](./tool-design-and-function-calling.md)：定义被编排结构调用的能力与执行边界。
- [上下文工程原则](../context/context-engineering-principles.md)：决定在交接中保留什么、何时按需载入或重启探索。
- [LLM 评估方法](../evaluation/llm-evaluation-methods.md)：用端到端任务证据比较主循环、委托和交接。
