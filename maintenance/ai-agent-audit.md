# AI and Agent Batch Audit | AI/Agent 批次审计

本文件记录本轮对指定四篇知识正文的审查范围、保全内容与事实修订；它不是学习进度或掌握度记录。未审查所有 AI 文章，也不代表 AI 域其他材料已完成事实核验。

## 审查范围

| 旧路径（HEAD） | 当前正文 |
|---|---|
| `AI_Engineering_Notes/5.1 Agent Fundamentals.md` | [`ai-engineering/agents/agent-fundamentals.md`](../ai-engineering/agents/agent-fundamentals.md) |
| `AI_Engineering_Notes/5.2 Orchestration Patterns.md` | [`ai-engineering/agents/orchestration-patterns.md`](../ai-engineering/agents/orchestration-patterns.md) |
| `AI_Engineering_Notes/5.3 Tool Design and Function Calling.md` | [`ai-engineering/agents/tool-design-and-function-calling.md`](../ai-engineering/agents/tool-design-and-function-calling.md) |
| `AI_Engineering_Notes/3.1 Context Engineering Principles.md` | [`ai-engineering/context/context-engineering-principles.md`](../ai-engineering/context/context-engineering-principles.md) |

四篇旧稿由 `git show HEAD:<旧路径>` 完整读取；重写前核对迁移后正文、`ai-engineering/index.md`、`maintenance/knowledge-inventory.tsv`、仓库 `AGENTS.md` 与 `maintenance/writing-guide.md`。内容重写按 MyNotes Maintainer skill 执行。

## 原稿中保留的知识与例子

| 正文 | 保留并整理的长期知识 |
|---|---|
| Agent Fundamentals | 工作流与 agent 控制权区别、环境反馈循环、简单方案优先、工具名称空间与限制工具能力；保留客服退款的前置核验和操作顺序。 |
| Orchestration Patterns | 提示链、路由、分片/投票并行、orchestrator-workers、evaluator-optimizer；manager/专家委托与交接区别；保留支持路由、多文件代码任务、测试反馈等例子和提示模板选择。 |
| Tool Design and Function Calling | 模型请求—应用执行—结果回传流程、相似工具区分、schema/描述契约、错误恢复、并行与有序动作、MCP；保留 get_order/list_orders、客户资料并发读取和退款顺序例子；补回 OpenAI API 特定的 `auto`、`required`、指定函数和 `none` 工具选择模式，并说明 `parallel_tool_calls` 对单轮调用数的约束。 |
| Context Engineering Principles | 提示与上下文工程、长上下文位置效应、缩减/外置/隔离、缓存前缀、目标重述、失败记录和历史模式；保留登录修复清单、订单号保存、Manus 批量审核简历案例，并标明案例证据级别。 |

## 影响架构结论的事实修订

| 旧稿说法 | 处置与理由 | 一手来源 |
|---|---|---|
| Agent 有严格统一定义；一次工具调用不算 agent；聊天或 RAG 应用都不迭代 | **定义差异与过度二分。** Anthropic 区分 agentic systems 中的 workflow 与 agent；OpenAI 以模型对流程和工具的控制描述 agent。聊天是界面，RAG 是检索模式，两者都可组合进不同控制流。改以控制权、反馈和任务流程描述架构。 | [Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)；[OpenAI A Practical Guide to Building Agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) |
| 10 步 agent 固定花费 10 倍；Context 在约 30 轮失效；多于 15 个工具应拆 agent；路径按周变化就该选择 agent | **证据不足，删除固定阈值。** 轮数、token、工具耗时、模型与缓存设置各不相同。保留“agent 可能提高成本和累积错误”这一条件化权衡，要求按真实任务测成功率、延迟、成本和人工接管。 | [Anthropic Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)；[Anthropic Writing Effective Tools](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| 工具清单必须固定；任何变化都会废弃全部 KV cache；mask-not-remove 可普遍适用 | **供应商与运行时条件化。** Manus 描述的是自有工具状态机与解码时 logits mask。OpenAI 当前 prompt-caching 文档按已渲染前缀匹配，工具 schema 或顺序变化可能影响变化后的匹配；这不证明每家 API 都会清空所有缓存。Hosted API 是否能 mask logits 取决于接口。改为保留稳定前缀建议并明确授权检查由运行时负责。 | [Manus Context Engineering](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)；[OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching) |
| 工具说明必须包含六个固定栏目；模型总是比 schema 更可靠地读取说明；值必须在 enum 和 description 重复 | **作为普适规律无法确认。** Anthropic 的实践支持清晰用途、少重叠、明确输入输出、任务示例与评估；OpenAI 当前 API 文档提供 provider-specific strict schema。改成按风险说明字段语义、错误、副作用与恢复，不规定六槽模板；结构约束和业务规则分别校验。 | [Anthropic Writing Effective Tools](https://www.anthropic.com/engineering/writing-tools-for-agents)；[OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling) |
| 模型默认串行调用工具，三次串行等于三倍延迟；执行多调用可一概并发 | **错误的通用化。** OpenAI API 文档说明受支持模型可在一轮返回多个函数调用，并提供控制该行为的选项；响应如何调度与是否并发仍取决于应用。按依赖和副作用决定并行，写操作要考虑幂等、竞态与未知结果重试。 | [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling) |
| MCP 将 N×M 集成固定降为 N+M，并且是 agent-ready 集成的事实标准 | **过度概括。** MCP 是基于 JSON-RPC 的 client/server 协议，规范 tools、resources、prompts 等原语和传输；它支持互操作，但服务实现、认证、授权、版本兼容和评估仍需逐项处理。 | [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture) |
| 所有 token 两两注意力导致所有模型随长度稳定退化；总是首尾注意更可靠；超过某长度即 context rot | **架构与实验结论被扩大。** Lost-in-the-Middle 研究在多文档问答与键值检索中发现位置敏感性，不是所有模型、任务和输入结构的固定曲线。移除 universal 长度/轮数阈值，建议用真实模型和位置扰动进行评估。 | [Liu et al., Lost in the Middle](https://arxiv.org/abs/2307.03172)；[Anthropic Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| Claude 某版缓存价格代表 KV-cache 通用 10 倍节省；动态工具变化会让所有后续调用重算 | **价格过期、机制混淆。** 生成期间 KV cache 与跨请求 prompt caching 是不同层次。缓存阈值、边界、价格和生命周期随 provider/model 变化；正文去掉旧价格，并改用当前 API 文档说明前缀匹配条件。 | [OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching)；[Manus Context Engineering](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) |
| Manus 的约 50 次调用、结尾 recitation、保留全部失败记录和格式变体说明了通用规律 | **单一团队经验，外部普遍性不足。** 删除平均调用次数和确定性成效；保留精简任务状态、对后续决策有用的错误证据，以及“历史可影响当前输出”作为实践启发。明确模型权重不会因上下文错误而更新；故意变换序列化格式的广泛收益未获确认，不再作为通用建议。 | [Manus Context Engineering](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)；[Anthropic Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |

## 完成情况与限制

- 四篇正文均已完整重写，标题、核心定义、术语和面试简答提供中英双语；深入机制与示例以中文为主。正文保留原稿特有知识与可用例子，去掉重复问答、无证据数字和过强行业断言。
- 影响结论的说法分别标为定义差异、错误泛化、条件化、版本/供应商行为或证据不足；相关来源链接写入正文，以上审计列出主要修订依据。
- Firecrawl 工具本轮返回 Unknown tool，依主代理要求未继续重试；改用官方 Anthropic、OpenAI、MCP 页面及原始研究论文核验。没有使用 Context7，因为正文没有依赖某个 SDK 的实现细节。
- Manus 的 recitation、失败痕迹与历史模仿主张仍是实践经验；没有找到能证明其结构变体是跨模型通用解决方案的证据。API 缓存规则和函数调用能力仍需按部署所用模型、API 版本核对。
- 本批没有修改索引、生成文档或其他正文。重写后保留了已有上下文页英文 heading anchor；其余指向本批旧 heading 的入链需在仓库检查中确认。生成文档应由主流程重建并运行 `python3 maintenance/build-reading-docs.py --check`。
