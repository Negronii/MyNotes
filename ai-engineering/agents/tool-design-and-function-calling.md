# Tool Design and Function Calling | 工具设计与函数调用

**核心解释 / Core explanation：** 函数调用（function calling / tool calling）让模型返回一个结构化的工具请求；应用负责校验、授权（authorization）、执行并把结果交回模型。Function calling lets a model return a structured tool request; the application validates, authorizes, executes it, and returns the result to the model.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 工具调用不是模型直接运行代码。模型给出名称和参数后，运行时必须检查结构、权限和业务约束，执行相应函数，再把结果作为观察传回模型。好的工具接口用途明确、输入输出可读、错误可恢复，并针对副作用和重试设计保护。
- **English:** A tool call does not execute code by itself. After the model returns a tool name and arguments, the runtime must validate the shape, permissions, and business constraints, execute the function, and send its result back as an observation. A good tool has a distinct purpose, clear inputs and outputs, actionable errors, and safeguards for side effects and retries.

## 函数调用的生命周期

以 provider-neutral 形式描述：

1. 应用将对话状态与本轮可用工具定义发送给模型。
2. 模型返回普通内容，或返回包含工具名称与参数的调用请求。
3. 应用解析请求，校验参数，并按当前用户和业务状态授权。
4. 应用执行函数，将成功、错误或部分结果返回模型。
5. 模型依据结果继续调用工具、交接，或生成答复。

[OpenAI 当前 API 指南](https://developers.openai.com/api/docs/guides/function-calling)将工具调用描述为模型请求与应用端执行之间的多步流程。具体消息格式、角色名称、工具选择模式和结构约束因 API 而异。结构化调用或严格 schema 可以减少格式错误，但不证明用户意图正确、权限充分、业务动作合理或外部操作已经成功。

## 工具选择模式：OpenAI API 示例

OpenAI API 的 `tool_choice` 可控制模型是否以及如何选择函数。下表是该 API 的行为示例，参数名和语义不能直接假定适用于其他 provider：

| 模式 | 行为 |
|---|---|
| `auto` | 默认模式；模型可调用零个、一个或多个函数。 |
| `required` | 要求模型至少调用一个函数。 |
| 指定函数（forced function） | 要求调用某个具体函数，例如 `{"type":"function","name":"get_weather"}`。 |
| `none` | 模拟不提供函数时的行为，不调用函数。 |

并行工具调用是另一个维度：在 OpenAI API 中，`parallel_tool_calls: false` 可将单轮调用限制为零个或一个；支持的模型和组合仍以 API 文档为准。模型返回多个调用请求不等于应用必须并发执行，实际调度仍由运行时按依赖和副作用决定。工具选择也不授予业务权限，执行前仍要做授权检查。

## 设计工具契约 / Tool contract

不要要求每个工具都填固定数量的说明槽。先确保开发者和模型都能理解以下契约：

| 说明 | 设计问题 |
|---|---|
| **职责与边界** | 这项工具具体完成什么？相似工具的分界在哪里？ |
| **输入** | 每个字段代表什么，格式/单位如何，什么条件下必填？ |
| **结果** | 哪些信息足以支持后续动作？是否需要返回可继续查询的标识符？ |
| **约束与副作用** | 读还是写？执行对象/范围是什么？何时需要确认？ |
| **错误与恢复** | 未找到、权限不足、限流、超时或部分成功时，应返回什么可操作信息？ |

例如，按订单 ID 查看具体内容用 get_order，按客户或时间搜索一批订单用 list_orders。不要让两个工具的用途重叠到只能靠模型猜；在描述中写清何时选择哪一个。字段名应表达业务含义，如 order_id，而不是含糊的 value；示例用真实格式，但不要放入用户数据。

返回结果应只包含下一步决策需要的信息。对于大集合，支持筛选、分页或范围读取，避免把无关数据全部塞回上下文。工具错误应说明发生了什么、是否已产生副作用，以及可安全采取的下一步。Anthropic 的[工具设计经验](https://www.anthropic.com/engineering/writing-tools-for-agents)特别强调清晰用途、低重叠、易读输入输出，以及用任务评估迭代工具设计；命名效果也因模型而异。

## Schema、说明与业务校验

Schema 是输入输出的结构合同，说明文字则解释语义、格式、单位、相互依赖和操作边界。可以用 required、enum、数值范围、格式约束或提供商支持的严格结构化模式，减少格式错误。不要假设 schema 的 default 字段会由每个 runtime 自动填入；运行时需要明确实现默认值和业务验证。

以部分退款为例，refund_amount 的数值范围可以按订单状态和总额在服务端检查；refund_reason 可以有可选枚举；但“用户是否授权退款”并不是 JSON schema 能验证的。严格输出约束只解决结构层，仍需检查身份、资源归属、当前状态、业务规则和风险阈值。

## 并发（concurrency）、依赖与副作用

并行有两个不同环节：模型或 API 可以在一个响应中提出多个工具调用；应用运行时决定哪些调用能同时执行。能力因模型和 API 参数而异。[OpenAI 的函数调用文档提供了并行函数调用及关闭该行为的选项](https://developers.openai.com/api/docs/guides/function-calling)，但这不意味着所有调用都适合并发。

- **可并行的只读工作：** 获取客户资料、列出订单、读取支持历史；这些调用互不依赖时可并行，结果齐备后再合并。
- **必须有序的动作：** 核实订单 → 计算退款 → 执行退款 → 确认结果。后一步依赖前一步结果。
- **并发写入：** 涉及同一订单、库存或账户时，要处理竞态、重复提交和部分失败，通常需服务端幂等性（idempotency）、版本条件或事务保护。

网络超时并不能证明写操作失败。给有副作用的动作使用操作 ID 或幂等键；对结果不明的调用先查询状态，再决定是否重试。模型的错误恢复建议是提示，服务端必须定义安全重试策略。

## MCP 是什么 / Model Context Protocol

[Model Context Protocol（MCP）架构规范](https://modelcontextprotocol.io/docs/learn/architecture)定义了 host、client 与 server 如何发现彼此能力并通信。MCP 数据层基于 JSON-RPC，规范包含 tools、resources、prompts 等原语；传输层处理连接、消息与授权。它为应用发现和调用外部能力提供互操作协议，本身不负责模型推理、业务授权或工具执行质量。

MCP 减少每个 agent 平台都为每个服务单独定义连接协议的重复工作，但不是把所有集成成本从 N×M 自动变成 N+M：每个 server 仍需实现、认证、授权、版本兼容和任务评估。Host 决定暴露哪些能力，运行时仍要控制每个实际调用。

## 相关知识

- [智能体基础](./agent-fundamentals.md)：工具属于动作空间，但授权必须由运行时执行。
- [编排模式](./orchestration-patterns.md)：并行与串行编排取决于任务依赖和副作用。
- [上下文工程原则](../context/context-engineering-principles.md)：工具定义与结果也是模型上下文的一部分。
