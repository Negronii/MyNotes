# How can a production AI system contain model errors and manipulation? / 生产环境 AI 系统如何限制模型错误与受诱导带来的影响？

**Short answer / 简答：** Treat user and retrieved content as untrusted data and model outputs as proposals. The application enforces authorization, validates outputs for their next consumer, limits execution capabilities, and keeps a stop path outside the model loop. Test those boundaries against direct and indirect injection, review high-impact actions, and turn confirmed failures into regression cases.

把用户输入和检索内容视为不可信数据，把模型输出视为候选内容或动作。应用负责执行授权、按下游接收方校验输出、限制执行能力，并在模型循环之外保留停止路径。针对直接和间接注入测试这些边界，对高影响动作进行审查，并把确认的问题转成回归用例。

**Key terms / 关键术语**

| Term / 术语 | Meaning / 含义 |
|---|---|
| **Prompt injection / 提示注入** | Untrusted content changes model behavior against the intended task or data boundary. / 不可信内容使模型行为偏离预期任务或数据边界。 |
| **Direct / indirect injection / 直接 / 间接注入** | The instruction arrives in the user’s own input, or in supplied content such as a document or tool result. / 指令来自用户输入，或嵌在随后提供的文档、工具结果等内容中。 |
| **Trust boundary / 信任边界** | Where the application independently decides whether data, a request, or an action is trusted or authorized. / 应用独立判断数据、请求或动作是否可信或已获授权的位置。 |
| **Least privilege / 最小权限** | Give each tool and execution environment only the data and capabilities required for its task. / 只向工具和执行环境提供完成任务所需的数据与能力。 |
| **Human handoff / 人工接管** | Pause a task and provide only the evidence and decision needed for a person to continue safely. / 暂停任务，仅提供人工安全继续处理所需的证据和待决事项。 |
| **Red teaming / 红队测试** | Adversarial testing that probes this application’s data and action boundaries. / 针对本应用数据与动作边界进行的对抗性测试。 |

## Threats and failure modes / 威胁与失效方式

流畅回答仍可能错误或缺乏证据。检索可以提供有用依据，但不保证模型会正确使用；检索文本也不授予执行权限。本篇关注由此产生的运行安全边界；[LLM 评估方法](../evaluation/llm-evaluation-methods.md)衡量事实性与支持度，[RAG 架构与实现](../rag/rag-architecture-and-implementation.md)解释检索行为。NIST 将 confabulation 列为生成式 AI 风险；它没有把 grounding 视作正确性保证（[NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)）。

提示注入不要求成功“覆盖 system prompt”。只要不可信内容改变模型行为并违反预期任务或数据边界，就构成问题。OWASP LLM01:2026 涵盖直接与间接输入，包括用户内容、检索材料、工具输出、多模态内容和持久记忆（[LLM01:2026 Prompt Injection](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)）。

| Path / 路径 | Where the instruction comes from / 指令来源 | Example / 示例 |
|---|---|---|
| **Direct injection / 直接注入** | The user’s message. / 用户消息。 | 用户要求助手忽略原任务，并将报告发送到无关目的地。 |
| **Indirect injection / 间接注入** | A document, webpage, image, or tool result supplied as data. / 作为数据提供的文档、网页、图片或工具结果。 | 被检索的页面要求转发对话，而不是按要求总结。 |

把指令与引用或检索内容分开可以减少混淆，但提示词、字符串过滤器和分类器都不是可靠的授权或执行边界。过滤器可能检测部分攻击，却不能判断用户是否拥有某条记录，也不能约束进程对文件系统和网络的实际访问。

如果应用把用户或检索内容写入持久记忆，这些内容就可能影响后续会话。这是有持久记忆系统才适用的条件性风险，不是每个 LLM 应用都必然存在；OWASP 将持久记忆列为注入面和投毒风险（[LLM01:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)、[LLM05:2026 Data and Model Poisoning](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM05_DataModelPoisoning.md)）。测试部分因此只对确有持久记忆的系统列出跨会话用例。

## Trust boundaries and runtime controls / 信任边界与运行时控制

把工具调用视为模型提出的请求，而不是授权。任何副作用发生之前，应用都应检查已认证的调用者、目标资源、请求范围、当前业务状态和所需审批。每项操作都要重新检查，包括读取。使用范围最小的工具与凭据；白名单或有效 JSON 结构本身不能证明调用者有权执行动作。OWASP LLM03:2026 将最小权限、在用户上下文中执行和代码强制的中介控制列为应对 excessive agency 的措施（[LLM03:2026 Excessive Agency](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md)）。

| Control / 控制措施 | Role / 作用 | Boundary / 边界 |
|---|---|---|
| **Prompt, filter, or classifier (content guardrail) / 提示词、过滤器或分类器（内容护栏）** | Flags or reduces some risky inputs and outputs. / 标记或降低部分风险输入与输出。 | Does not authorize resource access or isolate execution. / 不负责资源授权或执行隔离。 |
| **Authorization / 授权** | Checks whether this caller may perform this action on this resource now; enforce it on every operation. / 逐次检查当前调用者能否对目标资源执行该动作。 | A model-selected tool or allowlist is not authorization. / 模型选择的工具或白名单本身不是授权。 |
| **Output validation / 输出校验** | Checks structure and business constraints, then encodes or sanitizes for the next consumer. / 校验结构与业务约束，并按下游接收方编码或净化。 | Does not prove factual truth or authorization, and does not isolate execution. / 不证明事实正确或授权成立，也不等于执行隔离。 |
| **Sandbox / 沙箱（执行隔离环境）** | When code runs, limits its actual filesystem, mounts, network, and credentials. / 代码运行时限制其实际文件系统、挂载、网络与可用凭据。 | Does not authorize business actions; its boundary depends on configuration. / 不负责业务授权，隔离范围取决于实际配置。 |

**Moderation / 内容审核**按应用内容策略审核内容；**data minimization or redaction / 数据最小化或脱敏**会从输入或输出中移除不必要的敏感字段。它们可以限制内容，但不授予访问权限，也不能替代针对下游语境的输出编码。NIST 讨论了生成式 AI 数据收集与处理的隐私风险（§2.4，[AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)）。

高影响或难以撤销的动作应暂停，等待与具体动作和目标绑定的审批。获批后，应用仍需在执行前重新检查授权与业务状态。尽可能将密钥放在模型可见内容和执行环境之外；沙箱保护取决于实际挂载、网络规则和凭据暴露情况（[OpenAI Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)、[Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)）。工具 schema 和执行契约见[工具设计与函数调用](../agents/tool-design-and-function-calling.md)。

## Stop and hand off / 停止与人工接管

达到已配置的失败阈值、目标资源或范围不清、工具行为异常，或动作影响需要审批时，应暂停并交给人工。除非已针对具体用途验证，否则模型自报的置信度不是经过校准的信号。OpenAI agent 指南把重复失败和高风险动作列为人工介入的例子（[A Practical Guide to Building Agents, pp. 30–31](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)）。

交接只需包含人工继续处理所需的信息：用户请求、相关证据及其来源、已尝试的动作和结果、尚待决定的事项。不要包含凭据或无关敏感上下文。运行日志与 trace 也只保留调查动作及结果所需的信息，并限制访问；NIST 在 §2.4 说明了生成式 AI 数据处理的隐私风险。授权决定作出前，暂停任何待执行副作用。

应用需要位于模型循环之外的停止路径，能够停止新的工具调用与重试、取消活动运行，并撤销或禁用受影响能力。提示模型停止不是 kill switch。恢复前先核对已经完成的动作并确认当前状态。NIST AI 600-1 要求部署后监控、事件响应与恢复，并能在结果偏离预期用途时停止或停用系统（§§ MANAGE 2.3、2.4、4.1）。

## Test and monitor the boundaries / 测试与监控边界

红队测试探索攻击者可能如何突破本应用的数据和动作边界；评估测量已知案例；生产监控观察真实运行结果，三者不能互相替代。发布前，以及模型、提示、工具、数据源或权限发生实质变化后，都应测试；相关事件发生后也应测试。NIST AI 600-1 要求实证评估与持续监控；[评估方法](../evaluation/llm-evaluation-methods.md)说明测量和回归设计。

回归用例应关联到应用实际能力：

- **直接注入：** 用户请求超出其授权范围的动作；即使模型提出调用，运行时也应拒绝。
- **间接注入：** 检索内容或工具结果要求模型超出任务；验证其不能授权副作用。
- **敏感输出和内容政策（无需工具）：** 在隔离测试上下文中放入合成的受保护字段并请求泄露；另外测试违反内容政策的提示，验证字段不会暴露且配置的审核行为生效。不要使用真实个人数据。
- **输出处理：** 对可能被下游接收方解释为标记语言或指令的内容，在该接收方处理时验证其安全性。OWASP LLM10:2026 建议在下游使用前验证与净化模型输出（[LLM10:2026 Improper Output Handling](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM10_ImproperOutputHandling.md)）。
- **持久记忆（仅在系统有持久记忆时）：** 向隔离测试记忆添加无害的注入指令；验证后续会话不能借此触发受限动作或超出预期范围，然后删除记录并确认其影响已消失。

红队结果应记录攻击路径、是否发生未授权动作或信息泄露，以及修复方式；适用时将最小化案例加入回归测试。生产中监控工具调用与拒绝、意外状态变化、重复失败、人工覆盖和伤害报告；将信号用于调查和更新测试，不把单个比率视为目标。

## 相关知识

- [工具设计与函数调用](../agents/tool-design-and-function-calling.md)：工具请求、schema 与副作用执行。
- [RAG 架构与实现](../rag/rag-architecture-and-implementation.md)：外部证据的检索和访问控制。
- [LLM 评估方法](../evaluation/llm-evaluation-methods.md)：质量与安全用例的测量和回归。
