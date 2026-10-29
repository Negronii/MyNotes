# LLM Evaluation / 大语言模型评估方法

LLM evaluation measures whether a system meets a defined task contract on relevant examples, using evidence and criteria appropriate to that task. No single score captures task success, truth, source support, relevance, safety, and operating cost.

LLM 评估要先说明系统要完成什么、用哪些样本检验、依据什么判断。任务成功、事实正确、来源支持、相关性、安全性和运行成本是不同问题，不能压成一个分数。

## Core answer / 核心回答

**English.** Define success for the task, then evaluate representative examples at the retrieval, generation, or agent level where the behavior occurs. Combine objective task checks with source or factual verification, a clearly anchored rubric or calibrated judge where quality is open-ended, and latency/cost measures. Keep a held-out regression set, report the denominator and uncertainty, and use live outcomes alongside offline tests.

**中文。** 先定义任务成功条件，再在检索、生成或 agent 端到端层级评估相关行为。可客观判定的部分用任务指标；开放质量用明确的评分准则或评分量表（rubric）、经人工校准的 judge，并单独核验事实和来源支持；同时记录延迟与成本。保留独立回归集，报告分母与波动，并结合离线测试和线上结果。

## Define each dimension / 分别定义各评估维度

Faithfulness 和 groundedness 在论文与工具中用法不完全一致。评分准则或评分量表（rubric）应明确评估维度和证据锚点；需要对照真值的任务还应说明 ground truth（参考真值，如外部事实或标注答案）。评估来源忠实度时要指定来源/上下文，评估指令遵循时要列明请求中的约束。RAG 研究常将上下文相关性、答案对上下文的忠实度、答案相关性分别评估；这是有用的拆分方式，不是普遍完整的指标清单。[RAGAS](https://arxiv.org/abs/2309.15217) 与 [ARES](https://aclanthology.org/2024.naacl-long.20/) 使用相近但不完全相同的评估设置。

| Dimension / 维度 | Definition / 定义 | Does not establish / 不能据此推出 |
|---|---|---|
| Task success / 任务成功 | **EN:** Did the result meet explicit acceptance criteria? **中：** 输出是否满足明确的任务验收条件？ | **EN:** That every claim is true or safe. **中：** 不能证明每个说法都真实或安全。 |
| Factual correctness / 事实正确性 | **EN:** Are claims true against an appropriate external reference at the relevant time? **中：** 说法对照适当的外部依据、在相关时间点上是否为真？ | **EN:** That the supplied context supports them. **中：** 不能证明给定上下文支持这些说法。 |
| Source faithfulness or groundedness / 来源忠实度或依据充分性 | **EN:** Are claims supported by the specified source/context, without material contradiction? **中：** 说法是否由指定来源/上下文支持，且没有实质冲突？ | **EN:** That the source is current or correct. **中：** 不能证明来源本身及时或正确。 |
| Relevance / 相关性 | **EN:** Does the answer address the question or requested information? **中：** 答案是否回应问题或所需信息？ | **EN:** That it is correct, supported, or complete. **中：** 不能证明答案正确、有依据或完整。 |
| Instruction adherence / 指令遵循 | **EN:** Did it follow applicable format, scope, and constraints? **中：** 是否遵守适用的格式、范围和约束？ | **EN:** That it is factual. **中：** 不能证明内容属实。 |
| Operational quality / 运行质量 | **EN:** Does it meet latency, availability, and cost requirements? **中：** 是否满足延迟、可用性和成本要求？ | **EN:** That user task goals were met. **中：** 不能证明用户任务目标已达成。 |

“Hallucination / 幻觉”没有统一且公认的分类法。不同综述对 factuality 与 faithfulness 的关系和子类划分并不相同；某篇论文的 taxonomy 不能当作普遍的三分法。评估时应标记可观察的失败及其依据，例如：对照外部依据为假、给定上下文不支持、与上下文冲突，或不遵守指令。指令失败应明确测量；某篇研究是否把它归到 faithfulness 子类，取决于该文定义。[Ji et al., *Survey of Hallucination in Natural Language Generation*](https://arxiv.org/abs/2202.03629)；[Huang et al., *A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions*](https://doi.org/10.1145/3703155)（[arXiv](https://arxiv.org/abs/2311.05232)）。

**合成示例 / Synthetic example。** 给定的服务日程写着 5 月 10 日闭店，但权威的当前通知已将日期改为 5 月 12 日。复述 5 月 10 日的答案忠于给定日程，却在当前事实上错误。回答 5 月 12 日可能符合当前事实，却没有得到该日程支持。应分别评估来源支持与当前事实，并记录参照日期。

## Choose metrics for the task / 按任务选择指标

| Metric family / 指标类型 | Good fit / 适用条件 | Boundary / 边界 |
|---|---|---|
| Accuracy, exact match, F1, executable tests / 准确率、精确匹配、F1、可执行测试 | 有明确标签、结构化输出或可辩护的预期结果时。代码通过率只说明指定测试集的结果。 | 标签或测试集可能遗漏其他质量维度或合理答案。 |
| BLEU, ROUGE / 参考文本重合度 | 翻译、摘要等任务中，参考文本重合度能作为有用的语料级信号时。BLEU 原用于机器翻译的快速、频繁评估；ROUGE 是一组参考摘要指标。[BLEU](https://research.ibm.com/publications/bleu-a-method-for-automatic-evaluation-of-machine-translation)、[ROUGE](https://aclanthology.org/W04-1013/)。 | 衡量词面重合，不是通用事实性或有用性指标。合理改写可能重合较少；仅有高重合分不能证明答案正确或相关。它们是特定任务工具，并非因历史较久就失效。 |
| Retrieval precision/recall and ranking measures / 检索精确率、召回率与排序指标 | 有相关文档或参考证据标注的检索阶段。Recall@k 可看所需证据是否出现在前 k 项；精确率/排序指标可看返回集合与顺序。 | 结果取决于候选集、相关性标注和 k。检索到相关内容不等于证据完整，也不等于最终答案有依据。 |
| Rubric or model-graded scores / rubric 或模型评审分数 | 没有唯一答案的开放任务，且评价标准可以明确写出并用例子校准时。 | judge 本身也是可能出错的模型；评分不是 ground truth（参考真值）。 |
| Latency, availability, and cost / 延迟、可用性与成本 | 作为运行约束，与任务结果一起报告，用于理解质量与成本的权衡。 | 不能替代任务质量。 |

不要把指标名称当成跨库统一标准。如果使用框架中的 faithfulness、context precision 或 answer relevance 分数，应固定框架版本并检查其输入和 rubric；名称相同的指标也未必可互换。本文不提供框架 API 用法。

## Evaluate the pipeline at the right level / 在正确层级评估链路

对检索增强系统分阶段评估，才便于定位故障：

1. **Retrieval / 检索：** 候选集合是否包含所需证据？排序是否把它放在系统可用的位置？有相关文档或证据标注时，可据此评估。
2. **Generation given context / 给定上下文后的生成：** 回答是否回应问题、遵守指令、在需要时正确引用，且说法得到上下文支持？如果任务要求事实正确，还要单独核验外部事实。
3. **End-to-end agent / Agent 端到端：** Agent 是否通过合适的动作达到要求的环境状态？评估目标完成、工具/动作是否正确、有无有害副作用，以及延迟或成本。组件分数有助于定位问题，但不能证明端到端成功。像 [AgentBench](https://arxiv.org/abs/2308.03688) 这样的交互式 agent 基准在环境任务中评估 agent，而不只是评分孤立文本回答。

**Offline / 离线评估**用固定样本做受控比较和回归，便于复现；但可能漏掉当前流量、变化中的来源和线上用户结果。**Online / 线上观察或实验**反映部署行为，但结果可能延迟、不完整，或受模型以外因素影响。条件允许时两者结合：用线上证据发现变化与候选案例，经审查并去标识化或合成为适当样例，再纳入有版本记录的离线集。公开教学示例不要包含私人或用户来源数据。

## LLM judges and human review / 模型评审与人工复核

Judge model 可按 rubric 评分、比较候选答案，或筛出待复核案例。提供问题、相关上下文或参考答案，以及带有可观察评分锚点的标准；要求评委给出评分依据。若要核对验收底线，使用逐项 pass/fail 检查或带明确锚点的评分准则；若问题是相对偏好，可用成对比较。成对比较只回答相对偏好，赢家未必满足验收底线。

研究发现的评委偏差包括位置、冗长偏好和自我偏好，但程度随任务和评委变化。[MT-Bench](https://arxiv.org/abs/2306.05685)、系统性的[位置偏差研究](https://arxiv.org/abs/2406.07791)和关于[自我偏好偏差的研究](https://arxiv.org/abs/2410.21819)说明应在目标评估任务上实际检验评委，不应假定某项缓解措施必然有效。可以随机或交换候选顺序并比较评分，按任务切片抽样复核；多评委或跨 provider 的增益仍需在校准集上验证。它们是诊断手段和可能的缓解措施，不保证评委彼此独立或判断正确。

当标准需要专业知识、任务主观或后果重大，或需要验证自动评委时，应安排人工复核。先用共同样例校准评审者、比较分歧；需要可靠参考结论时，对分歧案例进行裁定。一致性表示评审者在 rubric 下较一致，不代表 rubric 或标签正确。Judge 与单个人的分数一致，也不能单独证明 judge 准确。

需要外部事实时，尽可能对照适当、可信且及时的依据。评估来源忠实度时，应对照指定的上下文检查说法。NLI 分类器、再次检索和 self-consistency 可帮助筛选待检查内容，但都可能出错：多次回答一致不能证明为真，二次检索也可能返回过期或不相关来源。应报告检查了什么、依据何在，而不要把检测器分数写成事实已核实。

同样，提交被引用、标成依赖或获提名投票（nomination），只能说明来源声明或选择过程；不能代替任务结果的正确性检查。[GitSwarm v1（2026-10-04，§§2.2、2.5、3.4、4）](https://arxiv.org/html/2610.04862v1)将依赖声明、执行轨迹中的实际产物使用和最终候选的提交祖先链分开分析，并明确这些指标不单独证明因果收益。

## Build a comparable regression set / 建立可比较的回归集

- 定义符合条件的任务总体，并抽取常见样本、重要切片和已知失败类型。记录样例如何选择、标注和版本化；方便取得的样例集不一定有代表性。
- 将开发样例与用于最终比较的独立保留集分开，避免反复针对保留集调优。记录模型、提示词、检索语料/配置、评委和 rubric 的版本。
- 明确分母。例如，报告“所有符合条件的尝试中成功完成任务的比例”，并单独报告回答覆盖率。若任务要求拒答，正确拒答计为成功；未回答或不当拒答也应作为结果保留。如果 faithfulness 只在已回答样本上计算，应标明这是“已回答样本中的条件分数”，并同时报告回答覆盖率或任务完成率。
- 在相同协议下与基线比较。对于随机输出，重复足够次数以观察有实际意义的波动；报告样本数与不确定性，不要把微小分差说成确定结论。ARES 展示了一种将自动评委、人类标注样例与统计估计结合的方法，但不是每种评估都必须采用。[ARES](https://aclanthology.org/2024.naacl-long.20/)；另见 [Towards Reproducible LLM Evaluation](https://www.turing.ac.uk/sites/default/files/2025-11/towards_reproducible_llm_evaluation.pdf)。
- 只让快速检查拦截它有能力发现的问题；根据变更风险安排更完整的评估。线上失败在原因查明、数据适合保留后可进入回归集；盲目加入每起事件会造成重复、数据泄漏或隐私风险。

## 架构迁移与更新验收 / Architecture migration and update acceptance

**核心解释 / Core explanation：** 在固定任务与验收契约下比较端到端结果；行为变化、预测分数或复用记录都不能单独证明改进。Compare end-to-end outcomes under fixed task and acceptance contracts; behavioral changes, forecast scores, or reuse records alone do not establish improvement.

比较 agent loop、harness 或上下文策略时，覆盖完整生产链路、强制规则和发生变化的任务切片，并报告新增成功与回归的任务成败翻转（task flips）、成本及重复运行波动。先记录现有架构的端到端基线，再一次折叠一个 subagent 重复比较，单主循环是待评估的候选方案。这是工程建议，参照 [Anthropic 的 folding 文章（2026-10-22，“Task-completion evals”“Folding subagents into the main agent via skills and tools”）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)。

若更新策略（policy）与预测器（predictor），应分别检验各自效果和配对兼容性；配对门禁失败时保留已接受组合，并让开发/更新、门禁和最终审计数据承担不同用途。[RSI-Anything v1（2026-10-09，§2.5）](https://arxiv.org/html/2610.13912v1#S2.SS5)

若要测试清空历史是否有助于搜索，从同一候选检查点比较继续运行（continuation）与清空后重启（reset），同时报告候选质量、方案提案数（proposals）、实际 token/费用或时间及重复波动。[*Scaling Discovery Requires Forgetting* v1（2026-10-14，§4、§4.3 / Table 3）](https://arxiv.org/abs/2610.20563v1)的主实验固定三次重置；AHC014 对照按提案数匹配而非等花费或时长，且同时清除 session 和候选历史。该重置数只是实验设置；结果不能归因于其中一种记忆，也不建立通用重置周期。

Harness 的行为对照是执行证据而非正确性证明；[Harness² v1（2026-10-09，§2.2.1、Appendix F）](https://arxiv.org/html/2610.14224v1)也指出额外执行成本、随机性和共同偏差的影响。工程上仍需单独限制 Probe 的外部写入权限与副作用，不能把它当成无成本、无影响的预测。

**工程建议 / Engineering advice：** 若系统用预测器排序候选，应分别记录预测与随后实测的误差，以及所选 policy/version 在固定验收契约下的任务结果和成本。

## Use public benchmarks as evidence, not a deployment proxy / 公共基准是证据，不是上线代理

当任务、协议、模型访问方式和计分规则与问题相符时，公共基准可支持受控比较。像 [HELM](https://arxiv.org/abs/2211.09110) 这样的广泛评估也显示了多种场景与指标的价值；但它们不会自动代表某个具体部署任务。

检查基准覆盖范围、评估协议以及训练数据污染的可能性。污染测量及其影响取决于基准、模型和测量方法；分数提高或小幅上涨本身不能证明模型记住了测试集。[Sainz et al.](https://arxiv.org/abs/2310.18018)；[Singh et al.](https://arxiv.org/abs/2411.03923)。可用公开结果缩小候选范围，再用有代表性、记录版本且带独立保留集的任务样本比较入选系统。

## Related notes / 相关笔记

- [Agent fundamentals](../agents/agent-fundamentals.md) — distinguish task feedback from an accepted change that persists across runs.
- [Orchestration patterns](../agents/orchestration-patterns.md) — compare the single-loop baseline with tested delegation or parallel work.
- [RAG architecture and implementation](../rag/rag-architecture-and-implementation.md) — 了解检索、证据组装和生成机制，对应本文的 RAG 评估阶段。
- [AI safety in production](../safety/ai-safety-in-production.md) — 了解需要单独设计任务检查的安全边界和生产控制。

## Sources / 来源

关键定义与主张已在正文链接一手研究。补充来源：

- Liang et al., [*Holistic Evaluation of Language Models*](https://arxiv.org/abs/2211.09110).
- Zheng et al., [*Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*](https://arxiv.org/abs/2306.05685).
- Xia et al., [*Evaluation-Driven Development and Operations of LLM Agents: A Process Model and Reference Architecture*](https://arxiv.org/abs/2411.13768) — 提出连接离线与线上评估的流程模型，并不保证两者分数一致。
