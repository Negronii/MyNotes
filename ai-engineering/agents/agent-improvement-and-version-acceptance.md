# How do you test and keep an improvement to an agent? / 如何验证并保留对 Agent 的改进？

**Short answer / 简答：** Use predictions to rank candidates, then measure them on real tasks against a common baseline and a predefined acceptance rule. Keep the accepted workflow, predictor, or harness as a version that can be inspected and restored. / 先用预测给候选排序，再用真实任务、统一基线和预先定义的验收规则测量效果。验收通过后，把工作流、预测器或运行脚手架作为可追溯、可恢复的版本保留。

任务内反馈改变当前任务状态；持久改进则把经评估接受的策略、预测器或 harness 变更保留为后续系统版本。两者都不等于模型在一次运行中自行改变权重。

~~~mermaid
flowchart TD
    Baseline[Fix the task and baseline] --> Propose[Propose and rank changes]
    Propose --> Measure[Run candidates and collect real observations]
    Measure --> Accept{Meets the acceptance rule?}
    Accept -->|Yes| Save[Record evidence and retain the accepted version]
    Accept -->|No| Baseline
~~~

## Decide what will change / 确定改进对象

Specify the task, budget, success criteria, and stop condition before trying candidates. Record whether each candidate changes the task policy, the predictor that ranks proposals, or the harness that controls execution. When two components can interact, compare each change separately and then compare the pair before accepting it. Preserve the task inputs and baseline for that comparison. [Evaluation and paired acceptance / 评估与配对验收](../evaluation/llm-evaluation-methods.md)

## Rank candidates, then observe the real result / 候选排序之后获取真实结果

[RSI-Anything v1（2026-10-09，§2.1）](https://arxiv.org/html/2610.13912v1#S2.SS1) 将任务规格、预算、验收和停止条件视为固定契约；积累经验本身不会修改策略或模型。其 JEPA-Anything/OPF 世界模型先预测潜变量表示，再由领域读出（readout）转换成任务结果预测，用来排序候选并交给外部测量；机制见[§2.2](https://arxiv.org/html/2610.13912v1#S2.SS2)与[§2.3](https://arxiv.org/html/2610.13912v1#S2.SS3)。因此要区分规则、模型预测、模拟器输出和实测结果。外部反馈可以促成策略或工作流更新；只有在已观察候选显示预测器不可靠、且数据与预算足够时，才考虑更新预测器。观测覆盖不足也不等于可靠性已经成立。[§2.4](https://arxiv.org/html/2610.13912v1#S2.SS4)与[§2.5](https://arxiv.org/html/2610.13912v1#S2.SS5)分别说明更新门槛和配对验收。[Table 4](https://arxiv.org/html/2610.13912v1#S6.T4)与[§5](https://arxiv.org/html/2610.13912v1#S5)中各应用的更新范围不同；持续互相改进仍需联合的多轮评估。

**工程建议：** 对有清楚任务指标的工作流，可以尝试用脚本、模拟器或范围受限的 agent 预测候选效果并据此预筛，再与后续实测比较、验收版本。语法检查仍是规则校验，agent 的文字预判仍是预测。这些是实现选项，尚无替代上述学习型 world model 的等价实证；单步排序也不证明多步状态模拟有效。

例如，优化一个有工具调用的文档问答 Agent 时，可以用脚本预估候选配置的调用次数，先筛出更值得测试的候选。再对同一组任务运行基线和候选，比较实际成本、证据是否支持答案、权限控制是否通过。记录任务集、基线版本、变更及结果，验收后保留可恢复的配置和证据。这个例子说明候选筛选与版本验收如何配合。

## Retain changes to the harness / 保留脚手架改进

另一类改进改变的是运行脚手架（harness），而非基础模型。[Harness²（v1，2026-10-09，§§2.1–2.3）](https://arxiv.org/html/2610.14224v1) 在同一任务上实际执行候选 harness，比较编辑前后的行为，再将采用的 harness 组件和有依据的经验存入库；新任务从共同的 H₀ 起步并按需检索。该研究保持 editor 模型、阶段指令和决策规则不变，因此展示的是任务级 harness 与经验库的演进，不是模型权重或 editor 自行改写。执行对照可支持针对性修改，但不单独证明答案正确；验收边界见[LLM 评估方法](../evaluation/llm-evaluation-methods.md)。

**Related questions / 相关问题** — [When should a model control the next step? / 何时应让模型决定下一步？](agent-fundamentals.md) explains the live execution loop. [Context engineering / 上下文工程](../context/context-engineering-principles.md) explains what can be stored for retrieval on later tasks.
