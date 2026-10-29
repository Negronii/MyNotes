# Context Engineering Principles | 上下文工程原则

**核心解释 / Core explanation：** 上下文工程（context engineering）是在每次模型推理时，选择、组织和更新模型可用的信息，以支持当前目标。Context engineering selects, organizes, and updates the information available to a model for each inference step.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 提示工程主要优化指令；上下文工程还管理工具、对话历史、检索结果、执行观察和外部任务状态。上下文既受窗口、成本和时延限制，也可能因噪声、信息位置或过度压缩而降低有效性，因此要围绕任务评估结果，保留高价值信息并按需加载其余资料。
- **English:** Prompt engineering focuses on instructions; context engineering also manages tools, conversation history, retrieved evidence, observations, and external task state. Context is constrained by the window, cost, and latency, and its usefulness can fall with noise, position effects, or lossy compaction. I measure task outcomes, keep high-value information, and load the rest when needed.

## 提示工程与上下文工程

**提示工程（prompt engineering）** 关注如何组织指令和示例。**上下文工程（context engineering）** 关注每次推理实际提供给模型的整套信息，包括系统与开发者指令、工具定义、历史消息、检索材料、工具观察和任务状态。两者相互依赖：好指令不能补救缺失证据，更多材料也不能替代清楚的指令。[Anthropic 的上下文工程文章](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)把上下文视为每次推理都需要重新整理的动态集合，并建议用任务结果评估信息配置。

## Why is context a finite resource, and what's "lost-in-the-middle"?

**上下文资源有限，长文本的效能也会变化 / Context is finite, and long-context performance varies.**

模型能接收较长输入，不等于能同样可靠地使用任意位置的所有信息。上下文还受模型支持的窗口、输入成本、预填充时延、检索噪声与目标相关性影响。随着上下文增大，效果并非必然以一个固定速度下降，也没有适用于所有模型和任务的“30 轮”或 token 数阈值。

**Lost in the middle（中间迷失）** 是位置敏感性的一种实证现象。[Liu 等人的研究](https://arxiv.org/abs/2307.03172)在多文档问答和键值检索任务中观察到，模型对位于输入中部的信息有时不如位于开头或末尾的信息利用充分。它说明应在实际任务中测试长上下文与位置变化；不能据此断言所有模型总是更注意首尾，或某个 RAG 分块位置必然失败。

有效做法是选取足以完成当前子任务的高信号信息，给关键证据附来源或标识，并对模型、任务与提示结构做长上下文评估。注意力机制的理论复杂度不能单独证明某个系统会在特定上下文长度失效。

## 管理持续增长的上下文

下面的“缩减、外置、隔离”是实用整理方法，不是必须采用的固定分类。多数长任务会组合使用：

| 方法 | 何时使用 | 需要保留什么 |
|---|---|---|
| **缩减（reduce）** | 重复历史、冗长工具输出挤占当前任务空间 | 目标、关键决定、未解决问题、失败状态、资源 ID 与可追溯来源 |
| **外置（offload）** | 原始资料太大或跨越多轮/会话 | 文件、数据库或其他持久状态中的原始内容；上下文只保留可再次读取的路径、查询或 ID |
| **隔离（isolate）** | 一个任务需要独立研究，或当前历史混杂多个职责 | 工作者的目标、权限、输入与输出契约；主流程接收结论、证据和不确定性 |

**摘要与压缩：** 摘要有损。先保留稍后可能影响决策的事实，再删去重复内容；“订单已退款”不一定足以支持追问，可能还要留下订单号、金额、状态依据与操作 ID。原始记录可通过外部引用重新读取时，摘要就不必承担永久记忆的职责。Anthropic 建议在长任务中用 compaction、持久笔记和子智能体，并提醒过度压缩会丢失之后才显得重要的信息。

**按需加载（just-in-time retrieval）：** 保留轻量引用，在需要时再读取文件、网页或数据库，而非预先加载全集。这减少无关 token，但每次探索需要额外工具调用，并依赖检索能力和可用权限。对经常需要的稳定资料，也可先加载摘要，再按需查原文。[Anthropic 对按需检索与混合策略有详细说明。](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

Skills 与工具搜索也可渐进载入程序或能力；并行工具调用可以留在同一主循环中，不必因此创建 subagent。[Anthropic 关于把 subagent 折回主循环的文章（2026-10-22，“Using an agent loop with progressive disclosure”）](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)描述了这种按需暴露方式。

**隔离上下文：** 子智能体不会天然共享同一份记忆。清楚传递目标、必要背景和结果格式；需要一致决策时，明确由主 agent 汇总和核对。切分依据应是任务边界、权限或可验证的并行收益，而不是把完整历史复制给每个工作者。按问题类型交接时，若下一步仍依赖先前约束或发现，摘要可能丢失细节；可先尝试在主循环中保留共享状态并按需加载专业流程，再评估是否需要分拆。[Anthropic 的 folding 文章，“Combining domain agents”](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)；决策方法见[编排模式](../agents/orchestration-patterns.md)。

## How do you use the KV cache to cut inference cost?

**KV cache 与 prompt caching 是相关但不同的复用机制 / KV cache and prompt caching are related but distinct reuse mechanisms.**

**KV cache** 是自回归模型生成时保存先前 token 的 key/value 表示，以供同一次生成后续 token 使用。**Prompt caching（提示缓存）** 通常指推理服务在后续请求中重用相同前缀的计算。后者可降低特定服务和配置下的输入成本或首 token 时延；两者都不是模型的长期记忆，也不意味着缓存 token 在所有供应商中都按同一价格收费。

缓存规则依供应商、模型和 API 而异。以 [OpenAI 当前 API 文档](https://developers.openai.com/api/docs/guides/prompt-caching)为例，缓存匹配依赖渲染后的请求前缀和可用的缓存断点；工具名、描述、schema 或顺序变化可能让变化之后的前缀无法复用。改变前缀不等于每种服务都把整段历史全部丢弃，实际匹配边界、最小长度与生命周期需查对应文档。

- 将稳定指令和可复用资料放前面，把每次请求都会变的用户信息、时间戳放后面。
- 在 API 支持的状态模型中，追加消息通常比重写早期内容更利于复用；压缩或改写历史可能改变匹配前缀。
- 只有实测缓存命中率、总 token 成本与行为结果都合适时，才为缓存调整上下文布局。
- 若工具列表因权限变化而变，先保证能力配置正确；缓存优化不能成为保留过期权限的理由。

Manus 的[上下文工程经验](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)展示了稳定前缀、追加式历史和确定性序列化对其部署缓存的价值。这些是实践经验；不能把其价格、命中率或框架实现直接当作其他 API 的现行保证。

## 长任务中的目标、计划与失败记录

**目标重述（recitation）**：长循环会不断加入操作和观察。把精简的当前目标、已完成事项、下一步与阻塞项放到模型本轮可见的位置，并将权威状态保存在持久任务记录中，可降低目标在历史中被淹没的风险。

例如，维护一个短任务清单：完成登录校验修复；定位导致失败的输入；运行对应测试；记录仍未验证的路径。[Manus 公开了在其长循环中把 todo 写到近期上下文的做法](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)，而 Anthropic 也描述了使用持久笔记追踪长任务进度。该模式是有用的设计启发，不意味着所有 agent 都需要每轮重写清单，也不支持一个通用的平均工具调用次数。

**保留有用的失败证据：** 若后续决策需要知道刚才做过什么，保留精简的“尝试动作 → 错误或观察 → 当前状态”。这能让模型看到重试为何失败，但不会更新模型参数；只有在下一次推理时实际提供的记录才可能影响决策。无关日志、敏感数据和巨大堆栈应按需外置，并保留查询引用。压缩历史时，不要把会影响安全重试或后续确认的失败状态删掉。

**历史会变成示例：** 上下文里重复的动作—观察模式可能影响模型下一步模仿什么。Manus 描述了在批量审核 20 份简历时观察到重复操作，并提出用结构化变体打破模式；这仍是该团队的实践假设，没有足够证据把“改变格式”当作普遍解决方案。保持规范、易解析的序列化通常更利于复现与缓存；若评测发现重复行为，先精简或组织历史，再用任务集比较不同表示，不要无依据地注入格式噪声。

## 何时保留状态，何时重启探索 / Retain state or reset exploration

**核心解释 / Core explanation：** 保留可复用资产，与把全部历史带入每轮上下文，是不同的选择。Keeping reusable assets and carrying all past history into every context are separate choices.

下表是跨源工程综合，用于比较信息可见性与持久化选择，不构成统一架构或共同实验结论。

| 情形 | 状态选择与证据边界 |
|---|---|
| **同一任务的后续步骤** | 保留目标、接口、权限、验收条件、操作状态和影响安全重试的失败事实；将原始记录外置并保留可查 ID。步骤依赖同一约束时，先考虑主循环或明确交接。 |
| **有外部评分的开放搜索停滞** | 可从同一候选比较重启与继续搜索，并明确各自保留/移除的信息；停滞不自动构成通用重置规则。 |
| **跨 worker 复用产物** | 将带版本与来源的代码、测试、实验记录外置；按当前任务读取相关产物，不载入完整历史。持久资产和每轮可见上下文是不同选择。[GitSwarm v1（2026-10-04，§§2.2、3.3–3.4、4）](https://arxiv.org/html/2610.04862v1) |
| **跨任务复用 harness 经验** | 保存可复用组件和经验；新任务从共同基线开始，再检索与适配。[Harness² v1（2026-10-09，§2.3）](https://arxiv.org/html/2610.14224v1) |
| **接受系统级变更** | 保留已验收配置及其证据；后续候选仍需[重新验收](../evaluation/llm-evaluation-methods.md)。 |

[*Scaling Discovery Requires Forgetting* v1（2026-10-14，§§3.1–4.3、Appendix B p. 13、§6）](https://arxiv.org/abs/2610.20563v1) 的 Forget 同时清空 session 与候选搜索历史，只保留最佳候选及分数，以相同首轮指令重启。证据来自四项外部评分的优化任务、一个 harness/model 配置；它没有建立适用于一般任务的重置规则。

GitSwarm 用可分支的共享 Git 仓库和原子提交（atomic commit）保存中间产物。Git 的物理父提交（physical parent）记录开始工作的树；强制字段 `informed_by=` 记录 worker 声明的语义来源，且必须包含 parent、可增加其他分支来源。这是来源追踪，不是因果证明。主要积累证据来自同题跨 episode；单独把已完成搜索的获胜提交作为种子，仍是同一 RMT 任务，不能外推成任意跨任务迁移。worker 使用的 LLM 在 run 中保持固定；架构搜索改进的是被研究的另一模型，不能写成 worker 权重自行学习。[GitSwarm v1（2026-10-04，§§2.2、3.3–3.4、4）](https://arxiv.org/html/2610.04862v1)

**工程建议 / Engineering advice：** 将代码、测试、实验结果和负面发现作为候选经验资产外存，并记录版本、适用条件与检查依据，按当前任务检索后复验。重启探索不应删除权威任务契约或未决外部操作状态；把审计记录留在提示词之外，并重新载入目标、接口、测试、权限、验收条件和必要的失败/副作用状态。“被读取或引用”不等于提升结果。外部资产持续保留而当前上下文选择性清理，是跨源工程综合，不是论文共同评测过的方案。

## 相关知识

- [智能体基础](../agents/agent-fundamentals.md)：上下文、环境反馈和智能体执行循环如何连接。
- [编排模式](../agents/orchestration-patterns.md)：判断主循环、并行工具与独立 worker 的边界。
- [LLM 评估方法](../evaluation/llm-evaluation-methods.md)：比较历史保留、重启与跨运行变更。
- [工具设计与函数调用](../agents/tool-design-and-function-calling.md)：工具 schema 与执行结果也是上下文的一部分。
- [RAG 架构与实现](../rag/rag-architecture-and-implementation.md)：了解何时预先检索、何时按需检索。
