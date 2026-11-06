# 知识正文重写计划

## 当前阶段：规范与样板

先定稿[写作规范](writing-guide.md)，打磨[从一条消息到完整回答](../ai-engineering/systems/from-message-to-answer.md)与[模型如何生成文本](../ai-engineering/foundations/how-llms-work.md)这条阅读路线。完成独立冷读、来源与算例核对、Obsidian 渲染和链接验证后，交给读者试读；确认阅读体验后再启动全仓重写。

后续重写面向全仓知识正文，包括归档中作者撰写的知识正文与课程讲解。先归纳已有知识和前置关系，再按完整机制、运行过程或工程决策编排主问题。优先完善读者的进入顺序；能够复用的深层机制再独立成章。逐批保留有价值的解释、独特例子、来源和阅读进度，并在验收后交付。原始附件、源码快照和提示词包保持原貌，不套用正文模板。

## 待融入：DeepSeek 三篇材料

以下是待办归属，不是已经完成的知识审查。重写对应章节时重新核对原文版本、后续研究和当前参考实现；不把论文配置或历史对照结果当作通用最优方案。

| 材料 | 需要讲清的问题 | 预计知识归属与核验重点 |
| --- | --- | --- |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | 为什么只激活部分 FFN？MLA 怎样减少缓存？主模型仍需完整计算，MTP 为什么可能加速？ | 模型计算、attention 状态与推理服务：Router 的可学习权重与负载偏置；专家不等于人工知识分类；MLA 的矩阵吸收和 RoPE 条件；MTP 训练、草稿生成、因果并行验证、接受/拒绝及缓存回退。核对显存、FLOPs、延迟之间的区别。 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | 怎样减少长历史的存储与读取，同时保留局部细节和全局信息？ | 长上下文机制与服务：CSA/HCA、选择与压缩的损失、局部窗口、按层状态管理。按相关问题纳入 mHC、Muon、训练稳定性和 on-policy distillation；核对 1M 窗口与有效利用能力、单 token 成本与端到端时延的区别。 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) | 谁判断答案对错，奖励怎样更新参数，为什么不等于验证了每个推理步骤？ | 后训练与评估：程序验证器、GRPO 组内相对优势和更新约束、R1-Zero 与完整 R1 的训练流程、SFT/RL/蒸馏分工。核对后续算法对零方差组、长度和截断偏差的处理，以及奖励作弊、独立验收与跨任务泛化边界。 |

融入后更新 [AI 好文集](../review/ai-literature-index.md) 与相关知识链接。阅读过来源不等于读过整篇重写后的知识正文，不自动修改正文的阅读勾选。
