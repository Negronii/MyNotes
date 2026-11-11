# 应用怎样设计并执行模型提出的工具请求？

模型的 tool call（工具调用）是一条结构化请求，不是代码执行、权限授予或成功结果。应用要在当前一轮暴露合适的工具，解释并检查请求，再由运行时执行函数，并把与该请求对应的观察交回模型。本篇的 build 42 记录是合成示例；副作用的持久提交、授权恢复和断连后的运行恢复见[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../systems/ai-application-architecture.md)及[生产 AI 如何阻止不可信内容诱导模型越权](../safety/ai-safety-in-production.md)。

## 一次请求怎样变成下一步可用的观察

先前的消息是 `Why did build 42 fail?`。应用给模型本轮可用的只读工具 `read_build_log`，其参数 `build_id` 是整数。以下用 `c1` 表示 OpenAI Responses API（响应 API）中这条 `function_call` 的 `call_id`；模型请求调用 `read_build_log` 并提供 `build_id=42`。Responses 的 `output` 条目数组可能同时含普通文本和 `function_call`；应用逐条检查，不能因看见文本就忽略未处理的调用。每条调用在应用完成参数解析与授权检查、执行或生成失败结果前，都是待处理请求。应用解析请求，确认工具仍可用、参数满足结构约束，并在运行时核对调用者对构建 42 的读取范围，然后才读取日志。

下图中每一条箭头都交付新的状态。模型提议的调用在被应用接受和执行之前，只是待处理请求：

OpenAI Responses API 使用 `function_call`（函数调用条目）提出请求，用 `function_call_output`（调用结果条目）返回观察，两者通过 `call_id` 配对。

本例只展开一个请求 `c1`。若后续模型响应又提出工具调用，它会有自己的 `call_id`；host（承载模型的应用）逐条核验并按 ID 配对，不复用 `c1`，也不靠数组顺序猜结果属于谁。

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

应用完成处理后发起下一次 Responses API 请求，把 `function_call_output` 放进该请求的 `input`，并用原 `call_id` 配对；这个结果条目本身不会自动触发模型调用。应用可用 `previous_response_id` 引用前一响应，也可在手动管理上下文时传回必要的响应条目与工具结果。`previous_response_id` 不会自动继承前一次请求的 `instructions`，需要持续应用的运行指令必须重新提供；手动管理上下文且使用推理模型时，还要保留该模型要求回传的 reasoning items（推理条目）。续接对话状态不等于继承全部运行规则。应用发起的续接请求会让模型在同一用户轮次继续处理；模型可能给出普通答复，也可能再提出有自己 `call_id` 的新工具调用。Responses API 的实际条目形状如下。本例将业务结果序列化为字符串；API 也允许文本、图像或文件内容块数组。`status`、`build_id` 等是本例应用结果格式，不是 API 为工具结果规定的固定字段：

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

模型不能把失败结果当成已读取的日志。用户看过回答后再问“按当前手册应否重跑”才是新用户轮次。此时应用重建独立输入，可把已完成的 `c1` 记录整理成注明来源的事实；只在工具仍可调用时才附上定义。不能用普通上下文文本替换一个尚待回应的 `function_call`。[上下文工程](../context/context-engineering-principles.md)说明如何为新轮次选择历史和证据。

本例实际返回的可核对值如下：

这里 `status: "ok"` 表示日志读取成功；`exit_status: 1` 是被读取构建进程的退出状态，两者不是同一操作的成功/失败标记。

| `c1` 的日志字段 | 返回值 |
|---|---|
| 失败步骤 | `unit-tests` |
| 失败测试 | `reject_empty_name` |
| 断言预期 / 实际 | HTTP `400` / HTTP `200` |
| 进程退出状态 | `1` |

可以据此答：“build 42 在 `unit-tests` 的 `reject_empty_name` 测试中，断言预期 HTTP 400、实际收到 HTTP 200，日志还记录了测试进程的退出状态 1。”这份观察支持“测试断言的预期与实际不符”。它没有包含代码修改或执行路径，因此单靠它不能确定根因。生成最终解释时应只复用这些可追溯字段；完整的首轮服务计算见[AI 服务如何将一条消息变成完整回答](../systems/from-message-to-answer.md)。

## 先设计让模型选对的工具契约

工具目录首先是模型的动作选项，也是应用执行函数的契约。工具越多或名字越相近，模型越容易选错；把每个现成应用程序接口（API）端点原样暴露，也未必让任务更容易完成。围绕可识别的任务边界来设计名称和结果：已知订单 ID 时用 `get_order(order_id)` 取一个订单；按客户或时间范围查多笔订单时用 `list_orders(customer_id, time_range, page_token)`，并定义分页边界。参数说明应讲清字段含义、格式、单位和过滤条件，结果只保留后续判断需要的信息。

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

这里的定义采用 OpenAI Responses API function calling 的扁平函数输入形状作示意；其他 API 的封装层和字段名称不同。工具名和描述说明何时使用，schema（结构约束）限制参数形状，应用还需要解释 `build_id` 指什么。OpenAI 严格模式要求对象关闭额外字段，并将 schema 中所有字段声明为必需；若业务上字段可选，可在支持的 schema 中把它设为可空。JSON Schema 的 `default` 是注释信息，不会在验证输入时自动填入缺失字段；需要默认值时，由应用显式补齐或要求模型提供。严格结构减少参数形状错误，但不会检查目标构建是否存在、调用者是否有权读取，或模型判断是否符合用户意图。例如退款工具可将金额字段约束为正数、原因字段约束为枚举；订单当前状态、实际可退总额与用户授权仍要由业务运行时核验。

有用的错误结果也属于契约：`not_found` 应表达目标未找到；结构错误指出缺少或格式错误的字段；临时不可用则说明工具没有可用结果。执行阶段失败也要以原 `c1` 回传相应错误结果；只有成功读取时，`status: "ok"` 和日志观察才表示读取成功。错误应帮助模型选择下一步，不应把内部堆栈或敏感内容原样塞回上下文。对于分页、大日志或复杂资料，提供范围查询并返回来源 ID、段落位置或可续读标识，能减少无关输出。Anthropic 的工具设计研究也报告了类似工程经验：工具要有清晰且互不重叠的用途，结果应高信号，并通过任务评估检查工具选择和输出质量；具体效果依赖模型与任务。

## API 如何约束模型能提出哪些调用

OpenAI API（应用程序接口）的 `tool_choice` 是一个**调用选择控制**。它只影响模型本轮能否或如何提出函数调用，不授予业务权限，也不保证应用会执行：

| 模式 | OpenAI API 中的作用 |
|---|---|
| `auto` | 模型可选择不用工具，或发起一个或多个工具请求。 |
| `required` | 要求至少发起一个调用。 |
| 强制指定函数 | 指定必须调用的一个具体函数。 |
| `allowed_tools` | 将本轮可选集合限制到已提供工具的子集。 |
| `none` | 不允许本轮提出工具调用。 |

模式名称和支持条件是 OpenAI API 的定义，不可直接当成其他供应商的统一应用程序接口。并行请求又是另一个维度：支持并行的模型可能在同一响应中返回数条工具调用；对支持这些设置的模型，`parallel_tool_calls: false` 会把每次模型调用的单个响应限制为零个或一个。`required` 与 `parallel_tool_calls: false` 合用时，单个响应恰好提出一个请求；应用仍须验证并决定是否执行。应用应按实际依赖决定是否并发执行：相互独立的只读查询可以并发；依赖前一个结果的步骤要串行。每条结果都须关联自己的调用 ID，不能只按数组顺序假定对应关系。

读工具失败时，应用可返回 `c1` 的失败结果，再让模型说明目前无法读取日志或选择有界恢复方式。写工具的超时则不能推断“操作没有发生”；应用需要按权威状态处理未知结果、确认、重试和恢复。持久操作与权限恢复的具体流程见上方运行架构和安全说明；本篇聚焦请求与观察之间的契约边界。

## MCP 怎样把模型工具请求接到 server？

Model Context Protocol（MCP，模型上下文协议）定义 host、client 和 server 如何交换工具、资源与提示；它不等于模型供应商的函数调用 schema，也不会替应用授予业务权限。host 管理 MCP client，由 client 按 host 的信任配置与 server 通信。client 用 `tools/list` 获取目录，host 筛选本轮向模型提供的工具。接受模型提出的 `c1` 后，host 将它关联到一个 MCP JSON-RPC 请求 ID，client 用该 ID 发送 `tools/call` 及 `read_build_log` 的参数。client 收到响应后，host 把该请求 ID 映回 `c1`，再将结果作为模型工具输出放入下一次 Responses API `input`。模型调用 ID、MCP 请求 ID 和整次运行 ID 各有各的归属。

连接传输、2026-07-28 版每请求的协议元数据、远端授权、结果处理和注入边界，见[主机怎样把 MCP 工具从发现接到有权限的执行？](./mcp-tool-connections.md)。

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
> - **为 Agent 设计工具用途、描述和高信号结果。** Anthropic Research，[Writing effective tools for AI agents](https://www.anthropic.com/research/writing-tools-for-agents)，检查 `Choosing the right tools for agents`、`Returning meaningful context from tools`、`Prompt-engineering your tool descriptions`；文章中的效果实例属于其作者评估条件。
> - **协议中的角色、无状态请求、工具发现和执行。** Model Context Protocol，[2026-07-28 Specification](https://modelcontextprotocol.io/specification/2026-07-28)，`Overview`；[Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) 说明 `tools/list` 与 `tools/call`；[该版发布说明](https://blog.modelcontextprotocol.io/posts/2026-07-28/)列出无状态协议核心及多轮往返更新。
