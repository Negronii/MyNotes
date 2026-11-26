# 模型“调用工具”时实际发生了什么，工具契约该怎样设计？

模型发出的 tool call（工具调用）只是一条结构化请求：它不执行代码，不授予权限，也不代表操作成功。这一章跟着 build 42 的 `c1` 走一遍请求从提出到结果回到模型的全过程，然后讲怎样设计工具契约、怎样区分“形状合格”“有权执行”和“符合事实”三种检查。读者手上的输入来自[上一章](./when-the-model-decides.md)：模型在 CI 诊断中提出了下一步 `read_build_log(build_id=42)`。build 42 与订单、退款工具都是合成例子。

## 一次请求怎样变成下一轮的观察

应用在本轮向模型提供只读工具 `read_build_log`，参数 `build_id` 为整数。用户问 `Why did build 42 fail?`，模型提出调用 `read_build_log`、参数 `build_id=42`，这条请求的 ID 记作 `c1`。从这里开始，每一步都由应用完成：

~~~mermaid
flowchart TD
    A[应用整理当前消息和本轮可用工具] --> B[模型生成下一步]
    B --> C{输出里有待处理的工具请求?}
    C -->|没有| G[应用按运行状态与策略处理答复]
    C -->|有 c1| D[解析工具名和参数]
    D --> E{解析成功、工具本轮可用、参数合规?}
    E -->|否| X[形成可识别的失败结果]
    E -->|是| F[runtime 核对调用者与目标资源]
    F -->|拒绝| X
    F -->|允许| H[执行 read_build_log]
    H -->|读取成功| I[结果与 c1 关联]
    H -->|目标不存在或读取失败| X
    X --> I
    I --> J[应用把结果放进下一次模型输入]
    J --> B
~~~

图里有三点要记住。第一，模型输出可能同时含普通文本和工具请求，应用要逐条检查，不能看到文本就漏掉待处理的请求。第二，在应用解析、检查并执行完毕或生成失败结果之前，每条请求都只是待处理状态；失败也要形成结果，而不是悄悄丢掉。第三，结果放进下一次输入，必须由应用发起下一次模型调用；结果本身不会触发模型。

## 请求和结果靠调用 ID 配对

每条工具请求带一个由模型输出给出的调用 ID，应用返回结果时带上同一个 ID。配对只看 ID，不看顺序：模型一次提出多条请求时，每条有自己的 ID，结果可能乱序完成，也可能部分失败；按数组位置猜对应关系会把一条结果安到另一条请求上。模型后来再提出调用，就有新 ID，应用不复用 `c1`。

配对还意味着请求必须被关闭。在同一轮里，一条待处理的请求要用对应 ID 的结果回应，包括失败结果，不能改用一段普通文本代替。等用户看过回答、再问“按当前手册该不该重跑”，那是新的一轮：应用可以重新组装输入，把已完成的 `c1` 整理成注明来源的事实，只在本轮仍允许调用时附上工具定义。新一轮怎样选取历史与证据，见[每次调用的上下文预算该怎样分配](../context/context-budget-and-state-layers.md)。

调用 ID 只标识“这一次模型请求”。它不是运行 ID，也不是远端写操作的去重键；这些 ID 分属不同层，见[一次 AI 运行断线或崩溃后，凭什么恢复？](../runs/run-identity-and-authoritative-state.md)。

续接对话还有一个容易忽略的边界：服务端保存的对话状态能把先前的条目带进下一次调用，却不一定带上先前的运行规则。需要一直生效的指令，要确认每次调用都真的提供了。

> [!info] 实例：OpenAI Responses API 的条目形状（核对于 2026-11-12）
> 模型用 `function_call` 条目提出请求，应用用 `function_call_output` 条目返回结果，两者靠同一个 `call_id` 配对。响应的 `output` 是条目数组，文本和多个 `function_call` 可以同时出现。
>
> ~~~json
> {"type": "function_call", "call_id": "c1", "name": "read_build_log", "arguments": "{\"build_id\":42}"}
> ~~~
>
> ~~~json
> {"type": "function_call_output", "call_id": "c1", "output": "{\"status\":\"ok\",\"build_id\":42,\"step\":\"unit-tests\",\"failed_test\":\"reject_empty_name\",\"expected\":\"HTTP 400\",\"actual\":\"HTTP 200\",\"exit_status\":1}"}
> ~~~
>
> `output` 这里是序列化的字符串，也可以是文本、图像或文件内容块组成的数组；`status`、`build_id` 等字段是本例应用自定的结果格式，不是 API 规定的。处理完 `c1` 后，应用发起下一次请求，把 `function_call_output` 放进 `input`。续接上下文有两种做法：用 `previous_response_id` 引用上一次响应，或手动传回必要的条目和工具结果。`previous_response_id` 不继承上一次请求的 `instructions`，常驻指令要每次重新提供；手动管理上下文并使用推理模型时，还要按模型要求回传 reasoning items（推理条目）。

## 按任务边界设计工具契约

上一节假设模型选对了工具、填对了参数。能否做到，先取决于工具目录怎样设计。工具目录既是模型可选的动作清单，也是应用执行函数的契约。工具越多、名字越相近，模型越容易选错；把现有 API 的每个端点原样暴露，也不一定让任务更好完成。

设计时抓三点：

- **按任务边界命名和拆分。** 已知订单 ID 时用 `get_order(order_id)` 取一个订单；按客户或时间范围查多笔订单时用 `list_orders(customer_id, time_range, page_token)`，并定义分页边界。用途互不重叠，模型才容易区分。
- **参数写清含义、格式和单位。** 描述里要说明 `build_id` 指哪个系统的构建编号、金额是不是以分计、时间范围是否包含端点。
- **结果只留后续判断需要的信息。** 大日志、分页数据或复杂资料提供范围查询，返回来源 ID、段落位置或续读标识，而不是整块倒回上下文。

build 42 的只读工具可以写成下面的定义（采用 OpenAI 函数工具的扁平形状，其他 API 的外层字段不同）：

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

名称和描述告诉模型何时使用，`parameters` 的 schema（结构模式）限制参数形状。命名空间前缀（如 `browser_search`、`file_read`）能提示工具归属；Anthropic 的工具评估发现，用前缀还是后缀，效果随模型而变，所以命名方式要在自己的任务上测，不存在通用最佳写法。

## 形状、授权和真实是三道不同的检查

一条工具请求从提出到被采信，要过三道检查。它们由不同的机制完成，通过一道不能推出另一道：

| 检查 | 问的问题 | 由什么完成 | 通过后能说明 | 仍不能说明 |
|---|---|---|---|---|
| 形状 | 请求能否解析，参数类型、必填项、枚举、取值范围是否合规 | schema 校验、严格模式 | 应用能安全地读出参数 | 调用者有没有权限、目标存不存在、是不是用户要的 |
| 授权 | 这个调用者此刻能否对这个目标执行这个动作 | runtime 按身份、资源范围、审批状态逐次核对 | 执行这一动作是被允许的 | 参数指向的就是用户的意图，业务条件成立 |
| 真实 | 请求指向的对象和执行后的结果，在权威系统里是否确实如此 | 读取权威状态、核对业务不变量、以接收方记录为准 | 结论有权威来源支持 | —— |

用 `c1` 逐层看：

- `{"build_id": 42}` 是整数、无多余字段，**形状**合格。若模型写成 `{"build_id": "42a"}`，在这一层就被拒绝。
- 调用者是否有权读取构建 42 的日志，是**授权**问题，schema 看不出来。
- 构建 42 是否存在、是不是用户说的那次构建、日志返回的值是否就是那次运行的记录，属于**真实**。模型若填成 `build_id=24`，形状合格，调用者也可能有权读 24，但读回来的事实与用户的问题无关。

写操作上，三层的差距更大。退款工具可以把金额约束为正整数、原因约束为枚举，这只是形状；调用者能否为这笔订单退款是授权；订单当前状态、实际可退总额是否支持这次退款，要读权威状态才知道。执行之后，“退款成功”也只能以接收方的记录为准：模型在答复里写“已退款”，或者工具返回了一段格式合格的 JSON，都不等于钱真的退了。

工具结果本身也要按这三层对待。它的形状合格只说明能解析；它的内容是来自外部系统的数据，其中混入的指令文字不获得任何权限，见[为什么提示注入防不住“模型听话”](./prompt-injection-as-permission-confusion.md)。模型根据结果写出的最终答复，同样是形状合格不等于主张有据，答复侧的分层校验见[模型这次能看见什么，提示词该怎样写成可验收的契约？](../context/model-input-and-prompt-contract.md)。

### 严格模式和 default 只管形状

严格模式能减少参数形状错误，但它的作用到形状为止。以 OpenAI 的 `strict: true` 为例（核对于 2026-11-12）：对象要禁止额外字段，所有字段都列为必需；业务上可选的字段，把类型声明为可为 `null`。

JSON Schema 的 `default` 是注释，验证时不会自动填进缺失字段。需要默认值时，由应用在校验后显式补上，或者要求模型提供；不能指望 schema 校验器替你填。

## 错误结果也是契约的一部分

工具结果至少有两层状态，不能混在一个字段里：一层说明**这次读取或执行本身**成没成，另一层是**被读取对象的业务状态**。`c1` 的结果里，`status: "ok"` 说明日志读取成功；`exit_status: 1` 是被读取的那次构建进程的退出状态。前者成功，后者是失败的构建，两者描述的不是同一个操作。

执行失败时，应用仍用原来的调用 ID 回传失败结果，且不带观察，例如访问被拒：

~~~json
{"status": "error", "code": "access_denied", "observation": null}
~~~

模型不能把这条结果当成读到的日志。有用的错误结果应让模型能选下一步：

| 错误类别 | 告诉模型什么 | 合理的下一步 |
|---|---|---|
| `not_found` | 目标不存在 | 核对 ID 或询问用户，不要换参数乱试 |
| 参数结构错误 | 缺哪个字段、哪个字段格式不对 | 修正参数后重提 |
| `access_denied` | 调用者无权访问 | 说明无法读取，或请求授权；不要绕道读取 |
| 临时不可用 | 这次没有可用结果 | 有次数上限地重试，或说明暂时无法读取 |

错误信息不应把内部堆栈或敏感内容原样塞回上下文。

## 读失败和写超时为什么处理不同

读工具失败，没有改变外部状态。应用为 `c1` 返回失败结果，让模型说明暂时无法读取，或按有次数上限的方式重试。

写工具超时则不能推断“操作没有发生”：请求可能已经到达接收方并生效，只是响应丢了。这时结果是未知的，应用要先查清权威状态，再决定确认、重放还是转人工；用新请求再写一次可能造成重复扣款或重复建单。完整的状态机和对账方法见[退款请求超时后，怎样查清结果而不重复扣款？](../runs/external-writes-and-reconciliation.md)。

## 限制模型能提出哪些调用，不等于决定怎样执行

应用还可以在每次请求里限制模型本轮能提出哪些调用：允许不用工具、要求至少调用一个、强制调用某个函数，或把可选范围收窄到一个子集。这类控制只作用于模型的输出，不授予业务权限，也不保证应用一定执行。

模型能否在一次响应里并行提出多条请求，是另一个维度。并行**提出**不等于并发**执行**：应用按实际依赖决定，互不依赖的只读查询可以并发，依赖前一步结果的步骤要串行，写操作的顺序和去重由应用负责。无论怎样执行，每条结果都按自己的调用 ID 关联。

> [!info] 实例：OpenAI 的 `tool_choice` 与 `parallel_tool_calls`（核对于 2026-11-12）
>
> | 模式 | 作用 |
> |---|---|
> | `auto` | 模型可以不用工具，也可以提出一个或多个工具请求 |
> | `required` | 至少提出一个调用 |
> | 指定函数 | 必须调用指定的那一个函数 |
> | `allowed_tools` | 把本轮可选范围限制为已提供工具的子集 |
> | `none` | 本轮不允许提出工具调用 |
>
> 对支持该设置的模型，`parallel_tool_calls: false` 把单个响应里的工具调用限制为零或一条；与 `required` 一起用时，单个响应恰好提出一条调用，应用仍要校验并决定是否执行。这些名称和支持条件是 OpenAI 自己的定义，不是各家通用接口。

## 用真实任务的反馈改进工具

工具契约好不好，要在完整任务上看。从代表性工作流里抽取任务，固定初始状态、用户目标、模型看到的工具定义和可核验的结束状态。主结果是用户的任务是否完成；工具选择、参数有效率、工具错误、重复调用、返回内容、时延和成本用来定位原因。若多条工具路径都能得到正确结果，评分只检查任务结果和关键边界，不要求模型复现某一条参考轨迹。

每次运行要保存模型实际看到的工具目录、调用名和参数、应用的处理决定、工具返回值和环境的结束状态。模型对自己为何失败的解释可以当线索，判断依据取自运行记录和结束状态。

| 现象 | 要核对的证据 | 可尝试的改动 |
|---|---|---|
| 没选工具或选错工具 | 用户任务、本轮可用工具、模型的实际选择和结束状态 | 改清名称与用途说明，按任务收窄可见工具 |
| 参数缺失、格式错误或反复重试 | 原始参数、schema、校验结果和返回的错误类别 | 写清字段含义、单位和可选条件，返回可执行的结构化错误 |
| 调用成功却仍未完成任务 | 工具实际返回的内容、来源标识、最终回答和权威状态 | 补上后续决策需要的字段，调整筛选、分页或确定性预处理 |
| 调用冗余或成本升高 | 完整调用轨迹、调用数、时延和费用 | 检查工具边界和返回规模，看能否由确定性代码完成一段工作 |

改工具是改进循环的一个实例：先用已复现的失败定位到名称和描述、参数契约、执行语义或返回数据中的具体缺口，改出候选版本，再按独立验收的规则决定是否保留，见[让助手以后不再误诊，该改提示词、工具、脚手架还是权重？](../evaluation-and-release/choosing-what-to-change.md)。线上反馈要先核验、归类，才成为新的测试任务，见[上线后，怎样从一条错误建议找回可修复的证据？](../evaluation-and-release/production-traces-and-metric-denominators.md)。

## 经 MCP 接入时多出一层请求 ID

工具也可以不由应用自己实现，而是经 Model Context Protocol（MCP，模型上下文协议）接到外部 server。这时应用把模型的 `c1` 关联到一个 MCP 请求 ID，用它发出 `tools/call`，收到响应后再映射回 `c1` 交给模型。模型的调用 ID、MCP 请求 ID 和整次运行的 ID 分属三层，不能互相替代；MCP 也不替应用授予业务权限。协议细节见[MCP 2026-07-28 怎样把工具从发现接到有权限的执行？](./mcp-protocol.md)。

## 形状合格的请求，接下来要过授权的关

这一章产出的是：一条可解析、已配对、形状合格的工具请求，以及能区分读取状态与业务状态的结果契约。对 `c1` 这样的只读调用，核对调用者的读取范围后就能执行。但助手接下来要为 build 42 建缺陷单，模型提出 `create_issue`（调用 `c2`），这是改变外部状态的写操作：要确认工具本轮可见、调用者有权、凭据的范围对得上、用户批准的正是这份草稿。这几道关见[模型提出 `create_issue` 后，应用要过哪几道关才能放行？](./authorization-gates-for-actions.md)。

> [!info]- 来源
> 下列公开来源复核于 2026-11-12；MCP 条目限定在 2026-07-28 协议版本。
>
> - **模型请求、应用执行、结果配对、工具选择控制、并行调用和严格模式（“一次请求怎样变成下一轮的观察”“请求和结果靠调用 ID 配对”“严格模式和 default 只管形状”“限制模型能提出哪些调用”及两个实例）：** OpenAI API，[Function calling](https://developers.openai.com/api/docs/guides/function-calling)，复核于 2026-11-12，“The tool calling flow”“Tool call outputs”“Formatting results”“Incorporating results into response”“Tool choice”“Parallel function calling”“Strict mode”；模型支持和默认严格行为可能不同。`previous_response_id` 与 `instructions` 的续接规则见 [Responses Create](https://developers.openai.com/api/reference/resources/responses/methods/create.md)；手动上下文回传推理条目见 [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)。
> - **JSON Schema `default` 的语义（“严格模式和 default 只管形状”）：** [JSON Schema 2020-12: Annotations](https://json-schema.org/understanding-json-schema/reference/annotations)，`default`；默认值是注释，验证时不填入缺失字段。
> - **工具用途、命名、描述和返回内容（“按任务边界设计工具契约”“错误结果也是契约的一部分”）：** Anthropic Research，[Writing effective tools for AI agents — with agents](https://www.anthropic.com/research/writing-tools-for-agents)，2025-09-11，“Choosing the right tools for agents”“Namespacing your tools”“Returning meaningful context from tools”“Prompt-engineering your tool descriptions”；效果结果属于作者的内部任务与留出评估。
> - **用任务结果评估工具（“用真实任务的反馈改进工具”）：** Anthropic Research，[Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)，2026-01-09，“The structure of an eval”“Types of graders for agents”“Analyzing results and closing the loop”；说明应保存任务上下文和运行轨迹，并按可验证结果选择程序、人或模型评分器。
> - **MCP 的工具发现与调用（“经 MCP 接入时多出一层请求 ID”）：** Model Context Protocol，[2026-07-28 Specification](https://modelcontextprotocol.io/specification/2026-07-28)，“Overview”；[Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) 说明 `tools/list` 与 `tools/call`。
