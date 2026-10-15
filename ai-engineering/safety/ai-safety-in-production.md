# AI Safety in Production / 生产环境 AI 安全

**Definition / 定义.** Production AI safety is the application’s ability to limit harm when a model is wrong, manipulated, or asks to perform an unauthorized action. A model response is a proposal; the application and its runtime decide what data it may access, what actions may execute, and when execution must stop.  
生产环境 AI 安全，是指模型出错、受诱导或提出未授权动作时，应用能够限制实际影响。模型输出只是候选内容或动作；应用运行时负责决定数据访问、动作执行和停止条件。

**Key terms / 关键术语**

| Term / 术语 | Meaning / 含义 |
|---|---|
| **Prompt injection / 提示注入** | Untrusted content changes model behavior against the intended task or data boundary. / 不可信内容使模型行为偏离预期任务或数据边界。 |
| **Direct / indirect injection / 直接 / 间接注入** | The instruction arrives in the user’s own input, or in supplied content such as a document or tool result. / 指令来自用户输入，或嵌在随后提供的文档、工具结果等内容中。 |
| **Trust boundary / 信任边界** | Where the application independently decides whether data, a request, or an action is trusted or authorized. / 应用独立判断数据、请求或动作是否可信或已获授权的位置。 |
| **Least privilege / 最小权限** | Give each tool and execution environment only the data and capabilities required for its task. / 只向工具和执行环境提供完成任务所需的数据与能力。 |
| **Human handoff / 人工接管** | Pause a task and provide only the evidence and decision needed for a person to continue safely. / 暂停任务，仅提供人工安全继续处理所需的证据和待决事项。 |
| **Red teaming / 红队测试** | Adversarial testing that probes this application’s data and action boundaries. / 针对本应用数据与动作边界进行的对抗性测试。 |

**Interview answer / 面试简答.**  
**English:** I treat user and retrieved content as untrusted, and treat model tool calls as candidate requests whose authorization the application checks before execution. The application validates outputs for their next consumer, limits execution capabilities, and keeps a stop path outside the model loop. I test those boundaries against direct and indirect injection, review high-impact actions, and turn confirmed failures into regression cases.  
**中文：**我把用户输入和检索内容视为不可信数据，把模型工具调用视为候选请求，由应用校验授权后执行。应用按接收方校验输出、限制执行能力，并在模型循环外保留停止路径。我会针对直接和间接注入测试这些边界，对高影响动作设置人工介入，并将确认的问题加入回归集。

## Threats and failure modes / 威胁与失效方式

A fluent answer can still be false or unsupported. Retrieval can provide useful evidence, but does not guarantee the model will use it correctly; retrieved text also does not grant permission to act. This note focuses on the resulting safety boundary. See [LLM Evaluation Methods](../evaluation/llm-evaluation-methods.md) for factuality and support measurement, and [RAG Architecture and Implementation](../rag/rag-architecture-and-implementation.md) for retrieval behavior. NIST describes confabulation as a GenAI risk; it does not treat grounding as a correctness guarantee ([NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)).

Prompt injection does not require a successful “system prompt override.” It is enough for untrusted content to alter behavior in a way that violates the intended task or data boundary. OWASP LLM01:2026 covers direct and indirect inputs, including user content, retrieved material, tool output, multimodal content, and persistent memory ([LLM01:2026 Prompt Injection](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)).

| Path | Where the instruction comes from | Example |
|---|---|---|
| **Direct injection / 直接注入** | The user’s message. | A user asks the assistant to ignore the task and send a report to an unrelated destination. |
| **Indirect injection / 间接注入** | A document, webpage, image, or tool result supplied as data. | A retrieved page contains instructions to forward the conversation instead of being summarized. |

Separating instructions from quoted or retrieved content can reduce confusion, but prompts, string filters, and classifiers are not reliable authorization or execution boundaries. A filter may detect some attacks; it cannot decide whether a user owns a record or constrain a process’s filesystem and network access.

If an application writes user or retrieved content into persistent memory, that content can influence later sessions. Treat this as a conditional risk for systems with durable memory, not a requirement for every LLM application; OWASP discusses persistent memory as an injection surface and poisoning risk ([LLM01:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md), [LLM05:2026 Data and Model Poisoning](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM05_DataModelPoisoning.md)). The test section gives one minimal cross-session regression case.

## Trust boundaries and runtime controls / 信任边界与运行时控制

Treat a tool call as a request from the model, not as authorization. Before any side effect, the application should check the authenticated caller, target resource, requested scope, current business state, and any required approval. Repeat the check for each operation, including reads. Use narrowly scoped tools and credentials; an allowlist or valid JSON shape alone does not prove that the caller may perform the action. OWASP LLM03:2026 describes least privilege, user-context execution, and code-enforced mediation as controls for excessive agency ([LLM03:2026 Excessive Agency](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md)).

| Control / 控制措施 | Role / 作用 | Boundary / 边界 |
|---|---|---|
| **Prompt, filter, or classifier (content guardrail) / 提示词、过滤器或分类器（内容护栏/防护措施）** | Flags or reduces some risky inputs and outputs. / 标记或降低部分风险输入与输出。 | Does not authorize resource access or isolate execution. / 不负责资源授权或执行隔离。 |
| **Authorization / 授权** | Checks whether this caller may perform this action on this resource now; enforce it on every operation. / 逐次检查当前调用者能否对目标资源执行该动作。 | A model-selected tool or allowlist is not authorization. / 模型选择的工具或白名单本身不是授权。 |
| **Output validation / 输出校验** | Checks structure and business constraints, then encodes or sanitizes for the next consumer. / 校验结构与业务约束，并按下游接收方编码或净化。 | Does not prove factual truth or authorization, and does not isolate execution. / 不证明事实正确或授权成立，也不等于执行隔离。 |
| **Sandbox / 沙箱（执行隔离环境）** | When code runs, limits its actual filesystem, mounts, network, and credentials. / 代码运行时限制其实际文件系统、挂载、网络与可用凭据。 | Does not authorize business actions; its boundary depends on configuration. / 不负责业务授权，隔离范围取决于实际配置。 |

**Moderation / 内容审核** applies the application’s content policy; **data minimization or redaction / 数据最小化或脱敏** removes sensitive fields that are not needed from inputs or outputs. These constrain content, but do not grant access or replace context-specific output encoding. / 内容审核按应用策略限制内容；数据最小化或脱敏会从输入或输出中移除不必要的敏感字段。它们不授予访问权限，也不能替代针对下游语境的输出编码。 NIST describes privacy risks from GenAI data collection and processing (§2.4, [AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)).

High-impact or hard-to-reverse actions should pause for approval tied to the exact action and target. After approval, the application still rechecks authorization and business state before execution. Keep secrets outside model-visible content and execution environments where possible; sandbox protections depend on actual mounts, network rules, and credential exposure ([OpenAI Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes), [Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)). For tool schemas and execution contracts, see [Tool Design and Function Calling](../agents/tool-design-and-function-calling.md).

## Stop and hand off / 停止与人工接管

Pause for a person when a configured failure threshold is reached, the requested resource or scope is unclear, a tool behaves unexpectedly, or an action’s impact warrants approval. A model’s own confidence statement is not a calibrated signal unless it has been validated for that use. OpenAI’s agent guide gives repeated failures and high-risk actions as examples of human-intervention triggers ([A Practical Guide to Building Agents, pp. 30–31](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)).

A handoff should include only what the reviewer needs: the user’s request, relevant evidence and its source, actions attempted and their results, and the decision still needed. Exclude credentials and unrelated sensitive context. Operational logs and traces should likewise contain only what is needed to investigate actions and outcomes, with access limited appropriately; NIST identifies privacy risks from GenAI data collection and processing (§2.4). Pause any pending side effect until the authorized decision is made.

The application needs a stop path outside the model loop. It should be able to stop new tool calls and retries, cancel an active run, and revoke or disable the affected capability. A prompt telling the model to stop is not a kill switch. Before resuming, reconcile actions that already completed and verify the current state. NIST AI 600-1 calls for post-deployment monitoring, incident response and recovery, and the ability to disengage or deactivate systems when outcomes are inconsistent with intended use (§§ MANAGE 2.3, 2.4, 4.1).

## Test and monitor the boundaries / 测试与监控边界

Red teaming explores ways an attacker could cross this application’s specific data and action boundaries. Evaluation measures known cases; production monitoring observes what actually happened; none replaces the others. Test before release, after material changes to models, prompts, tools, data sources, or permissions, and after relevant incidents. NIST AI 600-1 calls for empirical evaluation and ongoing monitoring; the [Evaluation note](../evaluation/llm-evaluation-methods.md) covers measurement and regression design.

Keep regression cases tied to the application’s actual capabilities:

- **Direct injection:** a user asks for an action outside their granted scope; verify the runtime denies it even if the model proposes it.
- **Indirect injection:** retrieved content or a tool result asks the model to exceed the task; verify it cannot authorize a side effect.
- **Sensitive output and content policy (no tools required):** put a synthetic protected field in an isolated test context, request its disclosure, and separately test a policy-disallowed content prompt; verify the field is not revealed and the configured moderation behavior applies. Use no real personal data.
- **Output handling:** content that could be interpreted as markup or an instruction by the next consumer is safely handled there. OWASP LLM10:2026 recommends validating and sanitizing model output before downstream use ([LLM10:2026 Improper Output Handling](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM10_ImproperOutputHandling.md)).
- **Persistent memory, if present:** add a harmless injected instruction to isolated test memory; verify a later session cannot use it to trigger a restricted action or cross its intended scope, then delete the record and confirm its effect is gone.

Red-team findings should record the attack path, whether an unauthorized action or disclosure occurred, and the fix. Add a minimized case to regression tests when appropriate. In production, monitor tool invocations and denials, unexpected state changes, repeated failures, human overrides, and reports of harm; use these signals to investigate and update tests rather than treating any single rate as a target.
