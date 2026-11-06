# 怎样写出清楚且可验收的提示词？

提示词要把模型本轮该完成的事、可用材料、约束和输出说清楚；改动应针对已观察到的失败，并用同一组案例检查是否真的改善。提示只能影响模型如何处理输入，不能替应用取回没提供的事实、核实权限、执行动作或保证结论正确。

## 从构建 42 的已知记录写起

用户问“构建 42 为什么失败？”应用调用 `read_build_log` 后，收到与请求 ID `c1` 对应的日志结果：`unit-tests` 步骤中的 `reject_empty_name` 预期 HTTP `400`，实际收到 `200`，进程退出状态为 `1`。这些是日志观察；目前还没有底层代码根因。提示词要把观察和推断分开。

一个可以作为基线的指令是：

~~~text
根据本轮提供的构建记录，解释构建 42 失败了什么。
只陈述记录明确支持的观察；把观察到的失败和未确认的代码根因分开。
若没有根因证据，明确说尚不能确定，不要猜测修改位置。
返回构建 ID、证据状态、来源调用 ID、失败步骤、测试名、预期值、实际值、退出状态、根因状态及一句说明。已有可用记录（含可靠复用的历史观察）时设为 `available`；没有可用记录且尚未尝试取回时设为 `not_requested`、来源 ID 设为 `null`；尝试取回但被拒或失败且仍无可用记录时设为 `unavailable`，保留已知调用 ID，不填造日志字段。
~~~

应用至少要把 `c1` 的请求与结果，或从权威运行记录整理出的等价观察，放进本轮输入。模型不会自动看到日志服务、之前所有会话或当前持续集成（CI）手册。若用户看过这个回答后再问“按当前手册能否重跑”，那是新的用户轮次：应用需要组装先前 `c1` 观察和当前手册证据；继续阅读[每次模型调用应看到什么，应用又应持久化什么](../context/context-engineering-principles.md)与[怎样从授权文档中检索并核验回答依据](../rag/rag-architecture-and-implementation.md)。

可以把模型看作能处理已给材料的协作者，但不能假定它知道未输入的产品规则、资料版本、调用者权限或下游格式。提示中说“有权限时再读取”不能代替权限检查；必须由应用在工具执行前校验。更多工具执行边界见[应用怎样设计并执行模型提出的工具请求](../agents/tool-design-and-function-calling.md)。

## 让输入、约束和输出形成同一份任务说明

提示里每句话都应服务于任务。先写清要产出的结果和使用者，再指出哪些文本是待分析的数据，哪些是必须遵循的规则。遇到可能误解的边界，明确缺证时该报告什么。最后确定下游能够检查的输出字段。

| 写入的内容 | 在本例中怎样写 | 缺失时容易出现什么错误 |
|---|---|---|
| 任务目标 | 解释日志确认了什么，不要求猜修复方案。 | 把“解释失败”扩展成未要求的根因诊断。 |
| 可用证据 | 用户请求说明要完成什么；把与 `c1` 绑定的步骤、测试名、预期、实际和退出状态作为分析材料提供。 | 把任务目标误当成运行证据，或用一般经验补造本次运行没有的事实。 |
| 推断边界 | 没有代码或请求路径证据时，根因标为未知。 | 把 `400 → 200` 的断言差异直接说成某个校验器缺陷。 |
| 输出约定 | 固定字段、语言和未知值的表达方式。 | 忘掉退出状态、混淆预期与实际，或让下游无法解析。 |

先把用户请求理解为任务目标，再把用户附上的日志、引用文段、检索片段和工具结果标为待分析材料。目标表达用户意图，但不会自行授予系统权限；材料中的指令性文字也不因此成为应用规则。标记能减少边界歧义，却不是安全隔离，也不证明材料真实。送入模型前，应用还要按当前调用者选择并授权可见资料；参见[生产 AI 如何阻止不可信内容诱导模型越权](../safety/ai-safety-in-production.md)。

具体 API 可能把持久指令与本轮输入放在不同角色，并为 system（系统）、developer（开发者）、user（用户）消息定义优先级；使用该 API 当前文档规定的语义，不要把一个提供商的角色规则套到另一个。稳定的任务规则与语气可版本化管理，本轮记录用有类型的输入传入。可复用提示和示例应使用合成资料，不要硬编码真实姓名、工单号、秘密或会话历史。

## 用示例修正已复现的歧义

如果基线提示已经能处理 `c1`，不必为了完整而添加示例。若一组验证案例显示模型持续把不同失败类别混在一起，few-shot examples（少样本示例）可以呈现仅靠文字难以描述的边界。例如，用合成记录并列“断言实际值与预期不符”及“测试尚未运行就发生网络中断”；前者报告断言差异但不推断代码原因，后者报告没有测试结果。例子要与指令一致，避免把偶然措辞教成规则。

保留未参与改写的案例来检查改动：断言失败时是否仍保留 `400` 和 `200`，网络中断时是否避免声称测试失败，日志缺失或拒绝访问时是否明确说证据不足。若样例集只包含提示词编写时用过的 `c1`，模型可能只是记住那种表述。评估时应检查事实字段、证据支持、缺证时的行为及输出格式；更完整的验收设计见[如何判断模型是否满足任务契约](../evaluation/llm-evaluation-methods.md)。

## 机器消费时分开检查结构和含义

如果结果会被程序读取，应先定义真正需要的字段和允许值，再看当前应用程序接口（API）是否支持相应的 schema（结构约束）。例如，下面是供说明用的 JSON Schema（JSON 结构描述）形状；实际请求须按所选 API 和模型支持的子集配置：

`evidence_status` 区分三种情况：`available` 表示已有可用记录，包括应用从权威运行记录中可靠复用的历史观察；`unavailable` 表示没有可用记录，且取回尝试被拒或失败；`not_requested` 表示没有可用记录，且应用尚未尝试取得本次报告所需的日志。失败/拒绝时保留已知的来源调用 ID，日志字段用 `null`；尚未尝试且没有记录时，来源 ID 和全部日志字段都为 `null`。若拿到部分记录，就只填写实际观察到的字段，其余仍为 `null`。

~~~json
{
  "type": "object",
  "properties": {
    "build_id": {"type": "integer"},
    "evidence_status": {"type": "string", "enum": ["available", "unavailable", "not_requested"]},
    "source_call_id": {"type": ["string", "null"]},
    "step": {"type": ["string", "null"]},
    "failed_test": {"type": ["string", "null"]},
    "expected": {"type": ["string", "null"]},
    "actual": {"type": ["string", "null"]},
    "exit_status": {"type": ["integer", "null"]},
    "root_cause_status": {"type": "string", "enum": ["confirmed", "unknown"]},
    "root_cause": {"type": ["string", "null"]},
    "explanation": {"type": "string"}
  },
  "required": ["build_id", "evidence_status", "source_call_id", "step", "failed_test", "expected", "actual", "exit_status", "root_cause_status", "root_cause", "explanation"],
  "additionalProperties": false
}
~~~

完整的 `c1` 报告可以是：

~~~json
{
  "build_id": 42,
  "evidence_status": "available",
  "source_call_id": "c1",
  "step": "unit-tests",
  "failed_test": "reject_empty_name",
  "expected": "HTTP 400",
  "actual": "HTTP 200",
  "exit_status": 1,
  "root_cause_status": "unknown",
  "root_cause": null,
  "explanation": "断言预期 HTTP 400，实际为 HTTP 200；现有记录没有确认代码根因。"
}
~~~

若 `c1` 因权限拒绝而没有日志观察，报告应把 `evidence_status` 设为 `unavailable`、保留 `source_call_id: "c1"`，并将日志字段设为 `null`；如果既没有可用历史记录，也未尝试调用工具，则用 `not_requested`、`source_call_id: null` 和空日志字段。应用仍须按自己保存的 `c1` 请求和响应核对对象内容：把 `expected` 与 `actual` 交换后，或捏造根因并标为已确认，仍能通过这个 schema 的形状检查，但应在业务校验中拒绝。

在 OpenAI API 中，Structured Outputs（结构化输出）可令受支持的 schema 约束输出形状；JSON mode 主要保证合法 JSON 语法，不等于符合应用 schema。即使结构正确，也可能出现拒答、不完整响应、值与证据不符或不应执行的业务决定。应用要检查字段、枚举、来源对应关系和当前业务规则。人读的 Markdown 标题、XML 标签或代码围栏只帮助区分内容，不会自动成为机器可验证的输出契约。

提示内容也适合按生命周期分开：稳定的任务规则放在版本化的提示构造代码里，本轮用户材料通过有类型的输入传入。OpenAI 当前文档将生产提示视为应用代码并建议对修改运行代表性评估；截至 2026-11-06，其可复用提示对象（prompt objects）已不建议新项目使用，`v1/prompts` 计划于 2026-11-30 关闭。这是 OpenAI API 的迁移说明，不是其他平台的通用规则。

> [!warning] 结构和措辞都不能证明事实或授权
> Schema 只能限制允许的形状和值域，提示只能说明预期行为。字段值是否由 `c1` 支持、当前手册是否适用、调用者能否读取资源或是否获准执行操作，必须由应用依据权威记录和运行策略核验。

## 相关知识

- [简单提示失败后，怎样选择并评估提示技巧？](./advanced-prompting-techniques.md)：从具体失败信号选择少样本、拆分步骤或工具反馈。
- [每次模型调用应看到什么，应用又应持久化什么](../context/context-engineering-principles.md)：决定 `c1`、历史和证据中哪些内容进入新一轮。
- [AI 服务怎样把一条消息变成完整回答](../systems/from-message-to-answer.md)：本章使用的构建 42 运行主线。

> [!info]- 来源
> 本章的构建 42 记录是合成示例。以下来源用于核验提示工程与结构约束的当前边界。
>
> - **按失败改提示、组织消息、代码管理版本和评估。** OpenAI API，[Prompting](https://developers.openai.com/api/docs/guides/prompting)，检查于 2026-11-06，`Refine your prompt`、`Prompts in your application`；含 OpenAI 可复用 prompt 对象退场安排。
> - **提示写法与模型差异。** OpenAI API，[Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)，检查于 2026-11-06，`Version prompts in code`、`Message formatting with Markdown and XML`、`Few-shot learning`；该页对不同模型家族的建议不能互换为统一配方。
> - **结构约束的范围。** OpenAI API，[Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)，检查于 2026-11-06，JSON mode、Structured Outputs、拒答和 schema limitations 小节；支持哪些 JSON Schema 特性取决于接口能力。
