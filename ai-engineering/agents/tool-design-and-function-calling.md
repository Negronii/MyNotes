# 应用怎样设计并执行模型提出的工具请求？

模型发出的 tool call（工具调用）只是一条结构化请求：它本身不执行代码、不授予权限，也不代表操作成功。应用要决定本轮向模型提供哪些工具，解析并检查模型的请求，由运行时执行对应函数，再把这次请求的结果作为观察交回模型。本篇用合成的 build 42 记录作例子，聚焦请求与观察之间的契约；副作用的持久提交、授权恢复和断连后的运行恢复见[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../systems/ai-application-architecture.md)及[生产 AI 如何阻止不可信内容诱导模型越权](../safety/ai-safety-in-production.md)。

## 一次请求怎样变成下一步可用的观察

用户的消息是 `Why did build 42 fail?`。应用在本轮向模型提供一个只读工具 `read_build_log`，它的参数 `build_id` 是整数。本篇以 OpenAI Responses API（响应 API）为例：模型用 `function_call`（函数调用条目）提出请求，应用用 `function_call_output`（调用结果条目）返回观察，两者靠同一个 `call_id` 配对。这里模型请求调用 `read_build_log`、参数为 `build_id=42`，这条请求的 `call_id` 记作 `c1`。

Responses 返回的 `output` 是一个条目数组，可能同时包含普通文本和 `function_call`。应用要逐条检查，不能因为看到文本就漏掉尚未处理的调用。在应用完成参数解析和授权检查、并且执行完毕或生成失败结果之前，每条调用都只是待处理请求。对 `c1`，应用先解析请求，确认工具仍然可用、参数符合结构约束，再在运行时核对调用者是否有权读取构建 42，最后才读取日志。

下图展示这个过程，每条箭头都把新的状态交给下一步。本例只展开 `c1` 一个请求；如果模型之后又提出工具调用，新调用会有自己的 `call_id`。host（承载模型的应用）逐条核验，按 ID 配对结果，既不复用 `c1`，也不靠数组顺序猜测结果属于哪个请求。

~~~mermaid
flowchart TD
    A[应用整理当前消息和本轮可用工具] --> B[模型生成下一步]
    B --> C{output 含待处理的 function_call?}
    C -->|没有| G[应用按状态与运行策略处理答复]
    C -->|有 c1| D[解析工具名和 arguments]
    D --> E{解析成功、工具可用且参数有效?}
    E -->|否| X[形成可识别的失败结果]
    E -->|是| F[运行时核对调用者和目标资源]
    F -->|拒绝| X
    F -->|允许| H[执行 read_build_log]
    H -->|读取成功| I[结果与 c1 关联]
    H -->|目标不存在或读取失败| X
    X --> I
    I --> J[应用把 function_call_output 放进下一次 input；按需续接状态]
    J --> B
~~~

处理完 `c1` 后，应用发起下一次 Responses API 请求，把 `function_call_output` 放进这次请求的 `input`，并用原来的 `call_id` 配对。结果条目本身不会自动触发模型调用，必须由应用发起请求。

续接上下文有两种做法：用 `previous_response_id` 引用上一次响应，或者手动管理上下文、自行传回必要的响应条目和工具结果。要注意，`previous_response_id` 不会继承上一次请求的 `instructions`，需要一直生效的运行指令必须每次重新提供；手动管理上下文且使用推理模型时，还要按该模型的要求回传 reasoning items（推理条目）。也就是说，续接了对话状态，不等于继承了全部运行规则。续接后，模型在同一用户轮次中继续处理：可能给出普通答复，也可能再提出带新 `call_id` 的工具调用。

Responses API 中两种条目的实际形状如下。本例把业务结果序列化成字符串；API 也接受由文本、图像或文件内容块组成的数组。`status`、`build_id` 等字段是本例应用自定的结果格式，不是 API 对工具结果的固定要求：

~~~json
{
  "type": "function_call",
  "call_id": "c1",
  "name": "read_build_log",
  "arguments": "{\"build_id\":42}"
}
~~~

~~~json
{
  "type": "function_call_output",
  "call_id": "c1",
  "output": "{\"status\":\"ok\",\"build_id\":42,\"step\":\"unit-tests\",\"failed_test\":\"reject_empty_name\",\"expected\":\"HTTP 400\",\"actual\":\"HTTP 200\",\"exit_status\":1}"
}
~~~

若访问被拒，应用仍以 `call_id: "c1"` 回传失败状态，但结果不含日志观察，例如：

~~~json
{
  "type": "function_call_output",
  "call_id": "c1",
  "output": "{\"status\":\"error\",\"code\":\"access_denied\",\"observation\":null}"
}
~~~

模型不能把失败结果当成已经读到的日志。

同一用户轮次内，一个尚待回应的 `function_call` 必须用对应的 `function_call_output` 回应，不能改用一段普通上下文文本代替。等用户看过回答、再问“按当前手册该不该重跑”，那才是新的用户轮次。这时应用可以重新组装输入：把已完成的 `c1` 记录整理成注明来源的事实，只有在本轮仍允许调用该工具时才附上工具定义。[上下文工程](../context/context-engineering-principles.md)说明怎样为新一轮选择历史和证据。

回到读取成功的情况，本例返回的可核对值如下。注意 `status: "ok"` 表示日志读取成功，`exit_status: 1` 则是被读取的构建进程的退出状态，两者描述的不是同一个操作：

| `c1` 的日志字段 | 返回值 |
|---|---|
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 断言预期 / 实际 | HTTP `400` / HTTP `200` |
| 进程退出状态 | `1` |

据此可以回答：“build 42 在 `unit-tests` 的 `reject_empty_name` 测试中，断言预期 HTTP 400、实际收到 HTTP 200，日志还记录了测试进程的退出状态 1。”这份观察只能支持“测试断言的预期与实际不符”；它不包含代码改动或执行路径，单靠它不能确定根因。生成最终解释时，只应使用这些可追溯的字段；完整的首轮服务计算见[AI 服务如何将一条消息变成完整回答](../systems/from-message-to-answer.md)。

## 先设计让模型选对的工具契约

上一节假设模型选对了工具、填对了参数。要做到这一点，先要把工具设计好。工具目录既是模型可选的动作清单，也是应用执行函数的契约。工具越多、名字越相近，模型越容易选错；把现有 API（应用程序接口）的每个端点原样暴露出来，也不一定让任务更好完成。围绕可识别的任务边界来设计名称和结果：已知订单 ID 时用 `get_order(order_id)` 取一个订单；按客户或时间范围查多笔订单时用 `list_orders(customer_id, time_range, page_token)`，并定义分页边界。参数说明应讲清字段含义、格式、单位和过滤条件，结果只保留后续判断需要的信息。

构建 42 的只读工具可以将契约写成：

~~~json
{
  "type": "function",
  "name": "read_build_log",
  "description": "Read the failure summary for one build ID; return the failed step, test, expected value, actual value, and process exit status.",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "build_id": {"type": "integer", "description": "ID of the build to read"}
    },
    "required": ["build_id"],
    "additionalProperties": false
  }
}
~~~

这里采用 OpenAI Responses API 函数调用的扁平定义形状作示意；其他 API 的外层结构和字段名不同。工具名和描述告诉模型何时使用，schema（结构约束）限制参数形状，描述中还要说明 `build_id` 指什么。OpenAI 的严格模式（`strict: true`）要求对象禁止额外字段，并把所有字段都列为必需；业务上可选的字段，可以把类型声明为可为 `null`。JSON Schema 的 `default` 只是注释信息，验证时不会自动填入缺失字段；需要默认值时，由应用显式补上，或要求模型提供。严格结构能减少参数形状错误，但不会检查目标构建是否存在、调用者是否有权读取，也不会判断模型的选择是否符合用户意图。例如退款工具可将金额字段约束为正数、原因字段约束为枚举；订单当前状态、实际可退总额与用户授权仍要由业务运行时核验。

有用的错误结果也是契约的一部分：`not_found` 表示目标不存在；结构错误要指出缺少或格式不对的字段；临时不可用则说明这次没有可用结果。执行阶段的失败同样要用原来的 `c1` 回传对应的错误结果；只有读取成功时，才返回 `status: "ok"` 和日志观察。错误信息要帮助模型选择下一步，不应把内部堆栈或敏感内容原样塞回上下文。对于分页数据、大日志或复杂资料，提供范围查询，并返回来源 ID、段落位置或续读标识，可以减少无关输出。Anthropic 的工具设计研究也报告了类似工程经验：工具要有清晰且互不重叠的用途，结果应高信号，并通过任务评估检查工具选择和输出质量；具体效果依赖模型与任务。

## 真实任务的反馈怎样指导工具改进？

从代表性工作流抽取完整任务，固定初始状态、用户目标、模型能看到的工具定义和可核验的结束状态。主结果回答用户是否完成了任务。工具选择、参数有效率、工具错误、重复调用、返回内容、时延和成本帮助定位原因。若多个工具路径都能得到正确结果，评分器应检查任务结果和关键边界，不要求模型复现某一条参考轨迹。保存每次运行实际看到的工具目录、调用名和参数、宿主处理结果、工具返回值及环境结束状态。模型对自己为何失败的解释可作调查线索，判断依据取自运行记录和最终状态。

| 可观察到的现象 | 应核对的证据 | 可验证的改动方向 |
|---|---|---|
| 未选工具或选错工具 | 用户任务、当轮可用工具、模型实际选择和最终状态 | 改清工具名称与用途说明，按任务收窄可见工具集合 |
| 参数缺失、格式错误或反复重试 | 原始 arguments、schema、宿主校验结果和返回的错误类别 | 澄清字段含义、单位和可选条件，给出可执行的结构化错误 |
| 调用成功却仍未完成任务 | 工具实际返回内容、来源标识、最终回答及权威状态 | 补足后续决策所需字段，调整筛选、分页或确定性预处理 |
| 调用冗余或成本升高 | 完整调用轨迹、成功结果、调用数、时延和费用 | 检查工具边界、返回规模和是否能由确定性处理完成一段工作 |

先用已复现的失败定位名称和描述、参数契约、执行语义或返回数据中的具体缺口，再按[任务契约评估](../evaluation/llm-evaluation-methods.md)中的配对比较和独立样本验收候选版本。线上反馈要经核验和归类后才成为新案例，具体流程见[生产反馈如何变成可复核证据](../systems/ai-production-observability-and-feedback.md#把线上信号变成独立验证，而不是直接喂训练)。工具调用的身份、资源范围和副作用仍须由宿主逐次授权，见[生产 AI 如何阻止不可信内容诱导模型越权](../safety/ai-safety-in-production.md)。

## API 如何约束模型能提出哪些调用

除了设计工具本身，应用还可以在每次请求中限制模型能提出哪些调用。OpenAI API 的 `tool_choice` 就是这样一个**调用选择控制**：它只影响模型本轮能否提出、以及怎样提出函数调用，不授予业务权限，也不保证应用一定执行：

| 模式 | OpenAI API 中的作用 |
|---|---|
| `auto` | 模型可选择不用工具，或发起一个或多个工具请求。 |
| `required` | 要求至少发起一个调用。 |
| 强制指定函数 | 指定必须调用的一个具体函数。 |
| `allowed_tools` | 将本轮可选集合限制到已提供工具的子集。 |
| `none` | 不允许本轮提出工具调用。 |

这些模式名称和支持条件是 OpenAI API 自己的定义，不能当成各家供应商通用的接口。是否并行请求是另一个维度：支持并行的模型可能在同一个响应里返回多条工具调用；对支持该设置的模型，`parallel_tool_calls: false` 把单个响应中的工具调用限制为零或一条。`required` 和 `parallel_tool_calls: false` 一起使用时，单个响应恰好提出一条调用，但应用仍须验证并决定是否执行。模型能否并行提出请求，与应用是否并发执行是两回事：应用按实际依赖决定，相互独立的只读查询可以并发，依赖前一步结果的步骤要串行。每条结果都要关联自己的调用 ID，不能按数组顺序假定对应关系。

读工具失败时，应用可以为 `c1` 返回失败结果，让模型说明暂时无法读取日志，或选择一种有次数限制的恢复方式。写工具超时则不同：不能由此推断“操作没有发生”，应用要依据权威状态处理结果未知、确认、重试和恢复。持久操作和权限恢复的具体流程见篇首链接的运行恢复和生产安全两章。

## MCP 怎样把模型工具请求接到 server？

前面假设 `read_build_log` 由应用自己实现。外部工具可以由应用直接调用，也可以通过 Model Context Protocol（MCP，模型上下文协议）接入。MCP 定义 host（宿主应用）、client（客户端）和 server（服务端）之间怎样交换工具、资源和提示；它不等于模型供应商的函数调用 schema，也不会替应用授予业务权限。host 管理 MCP client，client 按 host 的信任配置与 server 通信。

以 `c1` 为例：client 先用 `tools/list` 获取工具目录，host 从中筛选本轮提供给模型的工具。host 接受模型提出的 `c1` 后，把它关联到一个 MCP JSON-RPC 请求 ID，client 用这个 ID 发送 `tools/call`，附上 `read_build_log` 的参数。收到响应后，host 把请求 ID 映射回 `c1`，再把结果作为工具输出放进下一次 Responses API 请求的 `input`。模型提出的工具调用 ID（`c1`）、MCP 请求 ID 和整次运行的 ID 分属不同层，不能互相替代。

传输连接、2026-07-28 版协议中每个请求携带的元数据、远端授权、结果处理和注入边界，见[主机怎样把 MCP 工具从发现接到有权限的执行？](./mcp-tool-connections.md)。

## 相关知识

- [AI 服务如何将一条消息变成完整回答](../systems/from-message-to-answer.md)：完整追踪用户问题到 `c1` 日志观察和最终说明。
- [每次模型调用应看到什么，应用又应持久化什么](../context/context-engineering-principles.md)：解释旧 `c1` 如何进入后续新一轮，工具定义应何时继续提供。
- [怎样从授权文档中检索并核验回答依据](../rag/rag-architecture-and-implementation.md)：当工具或检索返回的文档参与回答时，说明来源版本、访问范围和证据映射。
- [智能体怎样决定下一步动作](./agent-fundamentals.md)：解释模型如何在回答和动作之间选择。
- [多阶段 AI 任务怎样按依赖编排](./orchestration-patterns.md)：比较串行、并行及委派工作流。
- [AI 运行怎样在断线或工作进程崩溃后恢复](../systems/ai-application-architecture.md)：处理外部副作用、持久操作和运行恢复。

> [!info]- 来源
> 构建 42 与订单工具均为合成示例。下列公开来源复核于 2026-11-12；MCP 条目限定在 2026-07-28 协议版本。
>
> - **模型请求、应用执行、工具结果配对、工具选择、并行调用和严格 schema。** OpenAI API，[Function calling](https://developers.openai.com/api/docs/guides/function-calling)，复核于 2026-11-12，`The tool calling flow`、`Tool call outputs`、`Formatting results`、`Incorporating results into response`、`Tool choice`、`Parallel function calling`、`Strict mode`；模型支持和 API 的默认严格行为可能不同。`previous_response_id` 与 `instructions` 的续接规则见 [Responses Create](https://developers.openai.com/api/reference/resources/responses/methods/create.md)，手动上下文回传见 [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)。
> - **JSON Schema 默认值的验证语义。** [JSON Schema 2020-12: Annotations](https://json-schema.org/understanding-json-schema/reference/annotations)，检查 `default`；默认值是注释，不在验证时填入缺失字段。
> - **工具用途、描述、结果和任务评估。** Anthropic Research，[Writing effective tools for AI agents — with agents](https://www.anthropic.com/research/writing-tools-for-agents)，2025-09-11，“Choosing the right tools for agents”“Returning meaningful context from tools”“Prompt-engineering your tool descriptions”。文章中的效用结果属于其作者的内部任务和留出评估条件。
> - **Agent 评测的任务结果与评分器。** Anthropic Research，[Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)，2026-01-09，“The structure of an eval”“Types of graders for agents”“Analyzing results and closing the loop”。文章说明应保存任务上下文和运行轨迹，并按可验证结果选择程序、人或模型评分器。
> - **协议中的角色、无状态请求、工具发现和执行。** Model Context Protocol，[2026-07-28 Specification](https://modelcontextprotocol.io/specification/2026-07-28)，`Overview`；[Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) 说明 `tools/list` 与 `tools/call`；[该版发布说明](https://blog.modelcontextprotocol.io/posts/2026-07-28/)列出无状态协议核心及多轮往返更新。
