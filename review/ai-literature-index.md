# AI 好文集

按想深入的问题浏览。每个来源只保留一条记录，说明它的贡献以及已融入的笔记。知识链接通向完整解释，篇末折叠的来源区保留证据对应关系与出处细节。基础论文按仍有价值的机制选入，正文会保留其研究范围与适用边界。

- [模型计算与学习](#%E6%A8%A1%E5%9E%8B%E8%AE%A1%E7%AE%97%E4%B8%8E%E5%AD%A6%E4%B9%A0)
- [推理显存与服务容量](#%E6%8E%A8%E7%90%86%E6%98%BE%E5%AD%98%E4%B8%8E%E6%9C%8D%E5%8A%A1%E5%AE%B9%E9%87%8F)
- [检索与工具驱动的推理](#%E6%A3%80%E7%B4%A2%E4%B8%8E%E5%B7%A5%E5%85%B7%E9%A9%B1%E5%8A%A8%E7%9A%84%E6%8E%A8%E7%90%86)
- [Agent 循环与经验积累](#Agent%20%E5%BE%AA%E7%8E%AF%E4%B8%8E%E7%BB%8F%E9%AA%8C%E7%A7%AF%E7%B4%AF)

## 模型计算与学习

| 来源与版本 | 核心贡献或阅读理由 | 知识落点 |
|---|---|---|
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762v7) · 2017 首次发表 · arXiv v7 2023-08-02 | 在翻译用的 encoder–decoder (编码器—解码器)中结合 multi-head attention (多头注意力)、逐位置的 feed-forward network (前馈网络，FFN)、residual connection (残差连接)和 positional encoding (位置编码)。 | [模型计算](../ai-engineering/foundations/how-llms-work.md) 解释 QKV、FFN，以及它们在 decoder-only (仅解码器) 示例中的用法。 |
| [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://aclanthology.org/2023.emnlp-main.298/) · EMNLP 2023 | 解释共享 K/V head 怎样影响 attention 和 cache (缓存)大小，并介绍论文如何转换 multi-head checkpoint (检查点)、评估后续训练效果。 | [K/V 共享](../ai-engineering/foundations/how-llms-work.md#%E6%B3%A8%E6%84%8F%E5%8A%9B%E5%A4%B4%E5%85%B1%E4%BA%AB%20K%20%E5%92%8C%20V%20%E6%97%B6%E4%BC%9A%E6%80%8E%E6%A0%B7%EF%BC%9F)、[推理服务容量](../ai-engineering/systems/llm-serving-and-kv-cache.md)。 |
| [Transformer Feed-Forward Layers Are Key-Value Memories](https://aclanthology.org/2021.emnlp-main.446/) · EMNLP 2021 | 给出所研究 FFN 与文本模式相关、并影响预测的证据；这种解释的适用范围限于论文分析的模型。 | [FFN 的作用](../ai-engineering/foundations/how-llms-work.md#%E5%8F%98%E6%8D%A2%E6%AF%8F%E4%B8%AA%E4%BD%8D%E7%BD%AE%E7%9A%84%E7%89%B9%E5%BE%81)。 |
| [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/html/2104.09864v5#S3) · 首次发表 2021 · arXiv v5 2023-11-08 | 解释旋转 Q 和 K 的坐标后，dot product (点积)怎样包含相对位置信息。 | [QKV 与位置](../ai-engineering/foundations/how-llms-work.md#%E5%B0%86%E6%AF%8F%E4%B8%80%E8%A1%8C%E6%8A%95%E5%BD%B1%E4%B8%BA%20Q%E3%80%81K%E3%80%81V)。 |
| [GLU Variants Improve Transformer](https://arxiv.org/html/2002.05202v1#S2) · arXiv v1 · 2020-02-12 | 解释 SwiGLU 背后的门控 FFN 计算；实验比较的是特定 Transformer 变体，并未确立普遍最优的 activation function (激活函数)。 | [FFN 门控](../ai-engineering/foundations/how-llms-work.md#%E5%8F%98%E6%8D%A2%E6%AF%8F%E4%B8%AA%E4%BD%8D%E7%BD%AE%E7%9A%84%E7%89%B9%E5%BE%81)。 |
| [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467v1) · arXiv v1 · 2019-10-16 | 解释基于 RMS (均方根)的缩放怎样控制表示的数值尺度，以及它与包含中心化步骤的 normalization (归一化)有何不同。 | [输入归一化](../ai-engineering/foundations/how-llms-work.md#%E7%AC%AC%E4%B8%80%E4%B8%AA%20Transformer%20%E5%9D%97%E6%8E%A5%E6%94%B6%E4%BB%80%E4%B9%88%EF%BC%9F)。 |
| [The Llama 3 Herd of Models](https://arxiv.org/html/2407.21783v3#S3) · 2024 · arXiv v3 2024-11-23 | 以具体 decoder-only 架构和训练过程为参照，理解 RoPE、GQA、normalization 和门控 FFN。 | [模型计算](../ai-engineering/foundations/how-llms-work.md)、[服务完整流程](../ai-engineering/systems/from-message-to-answer.md)。 |
| [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751v2) · 首次发表 2019 · arXiv v2 2020-02-14 | 解释 nucleus sampling (核采样)和 temperature (温度)的机制；开放式文本生成实验不能据此证明 agent 行为正确。 | [token 选择](../ai-engineering/foundations/how-llms-work.md#%E4%B8%BA%E8%AF%8D%E8%A1%A8%E6%89%93%E5%88%86%E5%B9%B6%E9%80%89%E6%8B%A9%E4%B8%80%E4%B8%AA%20ID)、[如何选择解码设置](../ai-engineering/foundations/how-llms-work.md#%E5%BA%94%E7%94%A8%E5%BA%94%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E8%A7%A3%E7%A0%81%E8%AE%BE%E7%BD%AE%EF%BC%9F)。 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/html/2501.12948v2) · arXiv v2 | 研究可验证奖励驱动的推理训练，并区分 R1-Zero 的 RL 实验与最终 R1 的多阶段训练；结果奖励不等于验证了每个推理步骤。 | [奖励、组内优势与参数更新](../ai-engineering/fine-tuning/reward-based-reasoning-training.md)、[如何选择后训练信号](../ai-engineering/fine-tuning/fine-tuning-strategies.md)。 |
| [DeepSeek-V3 Technical Report](https://arxiv.org/html/2412.19437v2) · arXiv v2 | 将 MoE 路由与负载均衡、MLA 的压缩缓存和 MTP 的附加预测目标连接到训练与推理成本；参数总量、激活计算量和服务时延需分别判断。 | [MoE 与 MTP 的计算](../ai-engineering/foundations/how-llms-work.md)、[MLA 的矩阵吸收](../ai-engineering/foundations/long-context-attention.md)、[缓存容量与推测验证](../ai-engineering/systems/llm-serving-and-kv-cache.md)。 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/html/2606.19348v1) · arXiv v1 | 结合不同压缩率、稀疏选择和局部窗口，降低百万词元上下文的历史存储与读取成本；报告比例有特定模型、精度和长度基线。 | [长上下文的压缩与选择](../ai-engineering/foundations/long-context-attention.md)、[多教师在策略蒸馏](../ai-engineering/fine-tuning/reward-based-reasoning-training.md#多教师在策略蒸馏又提供了什么训练信号？)。 |

## 推理显存与服务容量

| 来源与版本 | 核心贡献或阅读理由 | 知识落点 |
|---|---|---|
| [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180v1) · arXiv v1 · 2023-09-12 | 使用逻辑 KV 块到物理 KV 块的映射与共享机制，减少分配浪费，并在所评估的工作负载中提升推理吞吐量。 | [推理容量](../ai-engineering/systems/llm-serving-and-kv-cache.md) 解释块分配、cache 复用和测量。 |

## 检索与工具驱动的推理

| 来源与版本 | 核心贡献或阅读理由 | 知识落点 |
|---|---|---|
| [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629v3) · 2022 首次发表 · arXiv v3 2023-03-10 | 用任务环境返回的 observation (观察结果)调整后续推理和行动，并在特定问答及交互任务中与相应基线比较。 | [Agent 决策循环](../ai-engineering/agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF) 将论文的行动与观察连接到生产中的工具契约。 |
| [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401v4) · 2020 首次发表 · arXiv v4 2021-04-12 | 结合可更新的文档索引与参数化生成器，比较按整段输出和按单个 token 对候选文档做 marginalization (边缘化)。 | [检索与有依据的生成](../ai-engineering/rag/rag-architecture-and-implementation.md) 将论文机制连接到证据检索和回答验收。 |

## Agent 循环与经验积累

| 来源与版本 | 核心贡献或阅读理由 | 知识落点 |
|---|---|---|
| [Building agents: When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) · Anthropic 文章 · 2026-10-22 | 讨论如何把依赖共享 context (上下文)的专业工作流合入主循环，按需加载 skills 和工具，以及何时保留独立 worker。 | [编排](../ai-engineering/agents/orchestration-patterns.md) 解释结构选择；[上下文](../ai-engineering/context/context-engineering-principles.md) 解释按需加载与交接损失；[评估](../ai-engineering/evaluation/llm-evaluation-methods.md) 解释迁移对照。 |
| [Scaling Discovery Requires Forgetting](https://arxiv.org/abs/2610.20563v1) · arXiv v1 · 2026-10-14 | 在由外部评分的开放搜索中，研究清除 session 和候选历史、但保留最佳产物及分数的重启策略。 | [上下文](../ai-engineering/context/context-engineering-principles.md) 解释保留对象与重启范围；[评估](../ai-engineering/evaluation/llm-evaluation-methods.md) 解释对照、预算和归因边界。 |
| [Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/html/2610.14224v1) · arXiv v1 · 2026-10-09 | 通过实际执行对照，迭代冻结模型之外的 harness，并跨任务积累可检索的改进经验。 | [Agent 改进](../ai-engineering/agents/agent-improvement-and-version-acceptance.md) 解释更新对象和共同基线；[上下文](../ai-engineering/context/context-engineering-principles.md) 解释经验复用；[评估](../ai-engineering/evaluation/llm-evaluation-methods.md) 解释如何对照行为并检验正确性。 |
| [RSI-Anything: Unlocking Recursive Self-Improvement with World Models](https://arxiv.org/html/2610.13912v1) · arXiv v1 · 2026-10-09 | 提出一个框架，以候选效果预测、真实反馈，以及策略和 predictor (预测器)的配对验收来组织递归改进。 | [Agent 改进](../ai-engineering/agents/agent-improvement-and-version-acceptance.md) 解释反馈和持久更新；[评估](../ai-engineering/evaluation/llm-evaluation-methods.md) 解释组件与配对验收。 |
| [GitSwarm: Decentralized Compounding Inference](https://arxiv.org/html/2610.04862v1) · arXiv v1 · 2026-10-04 | 借助持久、可分支的共享产物和显式来源记录，让 worker 跨尝试复用、验证并组合已有工作。 | [上下文](../ai-engineering/context/context-engineering-principles.md) 解释经验积累与来源；[编排](../ai-engineering/agents/orchestration-patterns.md) 解释独立任务与并行边界；[评估](../ai-engineering/evaluation/llm-evaluation-methods.md) 区分复用证据和因果收益。 |

返回 [AI 工程领域地图](../ai-engineering/index.md) 或 [知识导航](index.md)。想连着读，可以打开 [AI 工程连续阅读稿](generated/ai-engineering.md)。
