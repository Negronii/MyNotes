# 知识正文重写记录

## 当前阶段：正文交付与原生阅读验收完成

[写作规范](writing-guide.md)和[从一条消息到完整回答](../ai-engineering/systems/from-message-to-answer.md) → [模型如何生成文本](../ai-engineering/foundations/how-llms-work.md)样板经过独立冷读、算例核对及 Obsidian 渲染和链接验证，并由读者确认阅读体验。本轮按这套标准重写全仓知识正文，经过主代理通读、原提案者技术复核和空白上下文 Sol 冷读，按批提交到 `main`。

本轮重写面向全仓知识正文，包括归档中作者撰写的知识正文与课程讲解。先归纳已有知识和前置关系，再按完整机制、运行过程或工程决策编排主问题。优先完善读者的进入顺序；能够复用的深层机制再独立成章。逐批保留有价值的解释、独特例子、来源和阅读进度，并在验收后交付。原始附件、源码快照和提示词包保持原貌，不套用正文模板。

## 范围与编排

以 `bfe4145` 为本轮起点，三个活动领域共有 135 篇正文：AI 工程 20 篇、前端 68 篇、工程基础 47 篇；归档另有 129 篇实质讲解与作者解法。37 个归档导航页和 2 个空模板随迁移调整，不算重写正文。原题、附件、第三方源码、提示词包继续保留原貌。合并后以知识和独有例子的去向核对覆盖，不以保住原篇数为目标。

| 领域 | 阅读主线与机制归属 |
| --- | --- |
| AI 工程 | 从构建 42 的问题进入模型生成与工具执行，再分为模型与推理服务、外部证据与长任务恢复、训练与独立发布验收三条路径。 |
| 前端 | 沿同一个报表页从 URL 到第一帧，再跟筛选点击到事件、React 更新和下一帧。CSS、JavaScript、类型与构建分别深入其机制；性能章节解释如何从一次录制定位成本。 |
| 工程基础 | 从受约束的请求到数据提交，再跟超时、重试、队列确认及恢复；沿账户报表作业连接运行时容量、交付与事故分析。算法与内存布局解释底层成本。 |
| 归档 | 数据库课程沿存储、访问、隔离、恢复展开，保留原有演算与图。其余材料按完整机制或版本条件归并；能补充活动正文的独有例子与正文同批迁移。 |

每组先确定少量关键交接：旧节或独有例子由哪一章讲透，复用处保留什么输入与输出，旧入链转向哪里。React 组件组合不重复讲性能优化，布局居中例归布局或定位，模型训练目标与服务解码分开解释。跨章使用同一案例状态，避免各篇单独成立、连起来却换了场景。

较大的模型与训练组分次验收：先完成 MoE、MTP 与推测验证，再连接长上下文和服务容量；奖励训练、教师分布蒸馏与独立发布验收分别讲清训练信号。长上下文机制同时用于服务容量诊断和 RAG／上下文选择，满足独立成章的实际复用条件。

## DeepSeek 三篇材料的沉淀去向

三篇材料的机制已融入下列正文，核对版本为 V3 arXiv v2、V4 arXiv v1、R1 arXiv v2，并对照后续研究和公开实现。模型配置、论文实验结果与工程推广分别标明条件；来源版本与具体入口见 [AI 好文集](../review/ai-literature-index.md)。

| 材料 | 需要讲清的问题 | 已融入的知识与核验重点 |
| --- | --- | --- |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | 为什么只激活部分 FFN？MLA 怎样减少缓存？主模型仍需完整计算，MTP 为什么可能加速？ | 模型计算、attention 状态与推理服务：Router 的可学习权重与负载偏置；专家不等于人工知识分类；MLA 的矩阵吸收和 RoPE 条件；MTP 训练、草稿生成、因果并行验证、接受/拒绝及缓存回退。核对显存、FLOPs、延迟之间的区别。 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | 怎样减少长历史的存储与读取，同时保留局部细节和全局信息？ | 长上下文机制与服务：CSA/HCA、选择与压缩的损失、局部窗口、按层状态管理。按相关问题纳入 mHC、Muon、训练稳定性和 on-policy distillation；核对 1M 窗口与有效利用能力、单 token 成本与端到端时延的区别。 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) | 谁判断答案对错，奖励怎样更新参数，为什么不等于验证了每个推理步骤？ | 后训练与评估：程序验证器、GRPO 组内相对优势和更新约束、R1-Zero 与完整 R1 的训练流程、SFT/RL/蒸馏分工。核对后续算法对零方差组、长度和截断偏差的处理，以及奖励作弊、独立验收与跨任务泛化边界。 |

对应正文为[模型计算](../ai-engineering/foundations/how-llms-work.md)、[长上下文注意力](../ai-engineering/foundations/long-context-attention.md)、[推理服务与缓存](../ai-engineering/systems/llm-serving-and-kv-cache.md)、[奖励推理训练](../ai-engineering/fine-tuning/reward-based-reasoning-training.md)和[微调选择](../ai-engineering/fine-tuning/fine-tuning-strategies.md)。阅读过来源不等于读过整篇重写后的知识正文，不自动修改正文的阅读勾选。

## 交付范围与合并去向

本轮覆盖起点中的 264 篇知识正文，包含归档里的课程讲解与作者解法；37 个导航页随正文调整，两份空模板保持原状。覆盖按知识与独有例子的去向核对，部分归档页保留原路径并指向主讲章节。原始图片、PDF、源码快照、提示词包及练习原题不作模板化改写。

五份重复的活动正文已吸收到对应机制页，旧入链与阅读顺序同步调整：

| 原页面 | 主讲去向 |
| --- | --- |
| `css-interview-questions.md` | [Flex/Grid 中的居中](../frontend/html-css/flex-and-grid-layout.md#居中未知尺寸的内容)与[定位机制](../frontend/html-css/css-position-display-and-animations.md) |
| `es6-new-methods.md` | [值、比较与属性枚举](../frontend/javascript/javascript-types.md)及[数组遍历与变换](../frontend/javascript/arrays.md) |
| `optional-chaining-and-destructuring.md` | [缺失属性、默认值与解构](../frontend/javascript/javascript-types.md) |
| `javascript-basics.md` | [作用域、绑定与闭包](../frontend/javascript/scope-and-closure.md) |
| `other-javascript-topics.md` | [调用形式与严格模式](../frontend/javascript/this-and-function-binding.md)，值比较复用类型章节 |

新增的独立机制页是长上下文注意力、奖励推理训练，以及[Redux 共享状态与异步工作](../frontend/frameworks/redux-state-and-async-workflows.md)。Redux 放在工具选择的深入阅读区；首次沿 URL 到下一帧的路线保持连续。三个活动领域的索引负责完整顺序，连续阅读稿由其生成。已有阅读勾选及清单外备注保留，新章节不自动标成已读。

## 验证范围

各章将关键机制、版本敏感接口和有疑问的结论对照一手文档、论文或实际行为；这不表示每句话都做了独立实验。数学章节重算中间值；可执行例按适用范围做了编译、单元重放或隔离应用验证。React 请求错序、浏览器事件与历史、数据库约束和卖家资源隔离等检查都针对正文中的可观察结果。没有把未执行的 GPU 性能、云部署、真实身份提供程序或 SwiftUI 预览说成实测。

生成器通过 15 项测试；三个领域生成稿检查另行完成。对知识与维护文档的 316 份 Markdown 做本地文件和小节链接检查，未发现失效目标；原始 prompt 包不纳入这一正文导航检查。88 个 Mermaid 图和 444 段行内／展示数学表达式通过当前 Obsidian 所用引擎的解析检查。Callout 仅使用 `info`、`example`、`warning`，分别承担补充解释、演算示例和改变结论的条件。解析检查不能代替可见排版检查。

Obsidian 已完成样板以及模型、训练、React、数组、浏览器、流式通信和部分课程图的源页／合并稿抽检。2026-11-09 在 Obsidian 1.15.0 的可见 Reading view 中补完最后一批抽检：模型篇的 V4 mHC 与 Muon 公式、RAG 与工具流程、DOM 事件与 Redux、数据库 WAL 与交付流程，均检查源页及对应连续阅读稿。归档检查 XGBoost 的分裂计算、SwiftUI 兼容说明卡片的折叠与展开，以及 ARIES 课程配图。所抽查内容未发现渲染缺陷；这是代表性阅读检查，不是逐页截图验收。

三个活动领域分别实际点击源页的跨页链接，以及连续阅读稿内的章节链接，并确认目标文件与可见标题：RAG → 工具执行／奖励训练、DOM → React、交付 → 故障定位，跳转正常。原始 prompt 包中的伴随文件占位链接、目录入口及隐藏 Skill 路径另有文件级识别限制，不将它们混报为正文知识导航失效。阅读勾选未因验证而改变。
