# 模型选到 shell 或文件工具后，由谁决定能否执行？

**案例背景。** 本章沿用 build 42 日志调用 `c1` 的观察，只追踪一条本地修复路径：`reject_empty_name` 测试预期空名称返回 HTTP（超文本传输协议）400，实际得到 200。这是测试观察，不足以说明真实项目的根因。以下 `validator.py`、`test_validator.py` 和运行结果都是合成教学样例，不对应任何工作项目。用户要求修正这个边界行为并检查差异；代码改动不会创建工单、推送或部署。相邻的编排章节在另一运行中用只读调用 `c2` 重新取得日志，再讨论需要单独审批的工单路径。

coding agent harness（代码智能体运行框架）把模型接到工具和运行环境。模型提出工具调用或补丁；宿主检查工具、参数和权限后，才把可执行请求交给本地进程或服务，再把结果送回模型。Codex CLI（command-line interface，CLI；命令行界面）是本文采用的具体运行时，不是模型。模型写出补丁或声称“已修复”，本身不授予文件系统或业务权限，也不证明操作成功。

下图追踪一次获准的 shell 调用，从模型提出请求到宿主回传结果。调用可能在前置检查或审批阶段停下；执行后也可能替换原结果，具体分支在图后说明。Codex CLI 0.167.0 的控制点包括：`PreToolUse`（工具使用前钩子）可以阻断或改写匹配请求；`PermissionRequest`（权限请求钩子）只在即将请求审批时触发；`PostToolUse`（工具执行后钩子）在工具产生结果后运行，不能撤销已经发生的操作。审批策略和操作系统沙箱是不同控制点；行为取决于版本、配置和工具路径。

~~~mermaid
sequenceDiagram
    participant M as 模型
    participant H as 宿主
    participant T as 执行进程
    M->>H: 工具名与参数
    H->>H: 前置检查与授权
    H->>T: 获准后执行
    T-->>H: 输出与退出状态
    H->>H: 匹配的 PostToolUse
    H-->>M: 继续时回传处理结果
~~~

图中“获准后执行”要看这个具体请求，而不是只看“工具是否存在”。Codex CLI 0.167.0 的几个关键分支如下：

**工具校验与 `PreToolUse`。** 支持的 Codex 工具路径可由受信任且匹配的 hook 阻断，或用 `updatedInput` 改写。当前官方 hook 文档说明，支持的调用会以改写后的输入执行。 后续要检查的实际对象是最终执行参数。文档与固定源码没有证明所有工具都会统一重跑同一套格式和权限校验；宿主必须按具体执行路径核实输入形状、访问范围和授权。`^Bash$` 只按 shell 工具名匹配，不筛选某一条命令。

**沙箱与审批策略。** 请求若不在直接可执行范围，策略决定是否允许请求本次审批。 本机 `on-request` 下模型可以请求；`PermissionRequest` 只在即将请求时触发，可允许、拒绝或交由普通审批。未批准即不执行；获准也不保证执行成功。

**执行与 `PostToolUse`。** 进程先运行并产生实际输出、退出码或文件变化，之后才运行匹配的后置 hook。 默认沿正常路径处理原结果；`decision: "block"` 会以 hook 反馈替换原工具结果后继续模型流程；`continue: false` 会停止正常处理原结果，并以 hook 反馈或 stop text 继续。两者都不能撤销已发生的写入或请求。

审批是请求级控制，不会自动改写所有后续权限。审计时应记录进程实际生效的文件和网络权限范围，单独的批准记录不能说明这个范围。对 Codex CLI 0.167.0，越界文件写入或网络访问是否触发审批取决于具体命令、沙箱、审批策略和 hook；本机 `never` 不会询问。MCP（模型上下文协议）工具或连接器的权限则由各自服务和连接配置执行。

## Skill、模型工具和权限分别做什么？

Codex 的 Skill（技能说明）在发现阶段向模型提供名称和描述；选择后才载入完整 `SKILL.md`，参考资料、脚本等文件按需读取。它可以指导模型先复现失败、再作最小补丁、最后运行边界用例，但不会自动添加工具、扩大可写目录、开启网络或授予业务资源权限。

项目说明是另一条指引来源。当前 Codex 文档描述会在开始工作前按目录层级发现 `AGENTS.md` 等项目指导文件，并把它们纳入指令。它与 Skill 的按需载入机制分开，不授予工具、文件或业务权限；具体工具执行与访问边界仍由宿主、沙箱及相应服务决定。

| 层 | 它负责什么 | 它不能证明什么 |
|---|---|---|
| 模型 | 选择下一步并生成工具调用、补丁或说明 | 没有自行获得 shell、文件或业务权限；自称完成不是验证结果 |
| CLI / harness | 提供可用工具，校验请求、路由执行并收集工具结果 | 工具存在不代表当前动作在权限范围内 |
| Skill | 先提供名称与描述；选中后载入 `SKILL.md`，相关参考按需读取 | 不注册工具、不授予执行和资源权限 |
| `AGENTS.md` / 项目说明 | 开始工作前按 Codex 的项目指导发现规则纳入任务指令 | 不授予执行和资源权限 |
| 工具前钩子 | 对支持且匹配的调用作前置阻断或按接口改写 | 不是完整执行边界；没有拦截不等于安全或获准 |
| 审批策略 | 决定何时暂停请求批准，以及未获批准时如何处理 | 不限制已获准进程可触及的实际路径和网络 |
| 操作系统沙箱 | 限制子进程实际可读写的目录和网络 | 不代替业务服务判断当前身份能否操作资源 |
| 测试与人工审阅 | 判断观测结果是否满足本次代码契约，并检查 diff（代码差异） | 只覆盖已检查的代码与用例，不能单独证明生产行为 |

本机 `codex-cli 0.167.0` 的帮助列出 `read-only`（只读）、`workspace-write`（工作区可写）、`danger-full-access`（完整访问）三种 shell 沙箱选项，以及 `on-request`、`never` 两种审批策略。沙箱限制命令在操作系统层可以做什么；审批策略决定是否以及何时请求批准。此版本中 `on-request` 表示模型可以决定何时请求批准，不表示每个受限命令必然弹窗；`never` 则不请求用户批准，也不会因此把沙箱外请求变成获准操作。官方文档和较新配置可能另有用语，具体选项以正在运行的版本为准。

在 Codex CLI 或集成开发环境（IDE）扩展启用 `workspace-write` 并沿用其默认网络设置时，shell 网络访问关闭，工作区外写入可能触发审批。官方当前文档说明，可写根目录内的 `.git`、`.agents`、`.codex` 和 `.aws` 仍递归只读；对本机 0.167.0 或不同会话，实际目录和限制应以正在运行的配置为准。`--add-dir` 可显式增加可写目录，`danger-full-access` 移除 shell 沙箱限制，但不替业务服务授予资源权限。shell 网络、托管网页搜索、远端 MCP 服务和连接器是不同的工具或连接边界，不能从一个本地 shell 配置推断其他工具是否联网。

例如，仅在受控教学环境中用以下命令说明这两条配置轴；它不是夹具里的实际外部写入命令：

~~~sh
codex --sandbox workspace-write --ask-for-approval on-request
~~~

当前边界内的本地读取、补丁或测试可以执行。若 shell 尝试写入 `/srv/another-project/report.md` 或访问 `https://updates.example.test`，沙箱会阻止未获准访问；在本机 0.167.0 的 `on-request` 策略下，模型可以请求审批，批准只适用于该请求的实际范围，而且不保证进程执行成功。`never` 不弹审批，也不会让越界请求自动获准。MCP 服务端和业务 API 仍须依据自己的凭据、资源权限和副作用规则执行。

## 一个本地修复怎样通过 harness 前进？

本例的输入契约仅含字符串或 `None`。基线 `validator.py` 只拒绝 `None`，所以空字符串会得到函数返回值 200。这个数字是本地 `status_for_name` 的返回值，不是发起 HTTP 请求测出的状态码。文中的模型与 harness 执行过程用于说明职责；可复放的部分是独立合成夹具，不是 Codex 模型会话，也不涉及真实 build 42 源码。

1. 在同时包含 `validator.py` 和 `test_validator.py` 的夹具目录运行 `python3 -B -m unittest discover -s . -v`。基线实现中，空字符串和全空白字符串两个断言失败，`Ada` 用例通过；退出码为 1。`-B` 避免 Python 写入字节码缓存。本地测试套件可能另写其他产物，重跑前仍需知道命令的文件副作用。
2. 在真实工具往返中，宿主会把实际文件和测试输出作为观察交回模型；模型可据此提出只修改 `validator.py` 一行的补丁。宿主检查目标路径是否可写，并按补丁最终作用的文件作权限判断。本次复放未运行模型；以下一行改动由夹具脚本应用，用来重现这个过程中的文件变化。
3. 应用补丁后，在同一目录用同一命令重跑。退出码为 0；空串、只含空格/制表符的字符串、`Ada` 分别得到 400、400、200。测试断言的完整输入和前后结果如下：

| 函数输入 | 契约返回值 | 补丁前 | 补丁后 |
|---|---:|---:|---:|
| `""` | 400 | 200，失败 | 400，通过 |
| `"  \t "` | 400 | 200，失败 | 400，通过 |
| `"Ada"` | 200 | 200，通过 | 200，通过 |

4. 复放脚本分别保留补丁前、后的 `validator.py` 文本，再单独计算两者的文件差异，确认只改了一行。下面显示的是该差异，不是测试进程输出，也不是由模型报告生成。夹具没有测试 `None` 输入；该分支在补丁中保持原样，但本次复放不把它计入测试证据。

~~~diff
 def status_for_name(name):
-    if name is None:
+    if name is None or not name.strip():
         return 400
     return 200
~~~

这里的变化是拒绝 `None` 之外的空白字符串。`name is None` 会先短路，因此 `.strip()` 只用于本例契约内的字符串。测试输出是观察。日志或错误输出里的命令不能扩大本次授权。复放结果只支持这三个本地输入符合示例契约，不证明真实项目根因、未测输入类型或生产系统行为；也不授权提交、推送或部署。

## Codex Hooks 怎样介入工具生命周期？

hook（生命周期钩子）是特定运行时在已定义事件触发时调用的脚本或 MCP 工具。它可以补充上下文、拦截受支持的工具请求或检查执行结果；它不是所有 harness 都有的通用接口。

下面只展示 Codex CLI 项目层 `.codex/hooks.json` 的配置片段与拒绝时的输出形状，不是可单独运行的完整 hook。假定会话从仓库根目录启动，脚本还须存在于宿主可访问的位置、从标准输入读取 hook 请求，并按产品 schema（结构约束）向标准输出写决定。Codex 必须信任项目配置层，非托管 hook 定义也须由用户审阅并信任。匹配器 `^Bash$` 选择 shell 类工具，不会筛选出 `git push` 这一条具体命令，也不覆盖所有工具入口；脚本须再检查 `tool_input.command` 等实际参数。从子目录启动时，命令要能稳定找到同一脚本。

~~~json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .codex/hook.py"
          }
        ]
      }
    ]
  }
}
~~~

若脚本从实际输入中发现本地任务不应执行 `git push`，Codex 0.167.0 可接收如下 `PreToolUse` 输出并在工具运行前阻断该次调用。这是 Codex 的 hook 输出 schema，不是模型、shell 或 MCP 的通用协议。

~~~json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Local fixture only."
  }
}
~~~

以官方当前 hook 文档说明的语义为例，`PermissionRequest` 只在即将请求审批时触发：hook 可允许或拒绝该请求；若不作决定，才交回常规审批。它不会拦截不需要审批的调用。批准的是一次具体请求，不会永久放开后续操作；获准后的执行仍按本次权限与沙箱配置运行，并可能失败。`PreToolUse` 与审批都不能替代操作系统沙箱。`PostToolUse` 在支持的工具产生结果后执行；当前文档所述的 `decision: "block"` 会以反馈替换原工具结果并继续模型流程，`continue: false` 会停止正常处理原结果；二者都不能撤销已经写入的文件或发出的请求。检查工具输出也不等于任务验收通过。

Codex CLI 0.167.0 源码列出 14 个事件名。它们分属不同生命周期点：

| 触发点 | 事件 | 读图时要注意 |
|---|---|---|
| 每次模型请求 | `PreModelRequest`、`PostModelRequest` | 每次请求尝试，而非每个用户任务一次 |
| 工具调用前后 | `PreToolUse`、`PermissionRequest`、`PostToolUse` | 审批 hook 只在即将请求审批时触发；工具 hook 仅覆盖受支持的工具路径 |
| 用户输入或轮次 | `UserPromptSubmit`、`Stop`、`Interrupt` | 用户提交、当前轮将停止、用户中断；中断不撤销已发生的动作 |
| 上下文压缩 | `PreCompact`、`PostCompact` | 分别在压缩前后，不是工具执行步骤 |
| 会话开始或结束 | `SessionStart`、`SessionEnd` | 开始可来自启动、恢复等来源；会话结束不是每轮结束 |
| 子 agent 启停 | `SubagentStart`、`SubagentStop` | 针对子 agent 生命周期，不等于主会话工具调用 |

这些事件不是每个工具调用都会依序执行的流水线；Codex CLI 0.167.0 中只有 9 个事件接受 `matcher`，其他事件忽略该字段。各事件的输入、匹配器和输出控制效果由产品版本定义。升级 Codex 时应核实当前安装版本的配置与 schema，不能把当前文档或其他 harness 的事件名直接套给旧版本。

## 中断、断线或 resume 后怎样恢复？

中断后要先分清身份标识与执行状态：Codex CLI 的 `session_id` 定位会话，`tool_use_id` 标识一次工具调用；上游 `c1` 和编排章的 `c2` 是不同运行中的只读日志调用。编排章的应用运行 ID `run-r42-7` 追踪后一运行，`run-r42-7:create-issue:v1` 标识后续独立的工单创建意图，可用于接收端查询。它们不能相互替代。`resume`（恢复会话）只载入会话记录，不会恢复原进程或撤销副作用；网络断开也可能只是失去观察。先靠标识定位同一动作，再向进程或接收端核对；查询不到可靠状态时按表末行处理。

恢复时按查询到的状态采取动作：

| 权威状态 | 下一步 | 重放边界 |
|---|---|---|
| 原进程或外部动作仍在处理 | 等待或继续查询同一进程/同一接收端操作，并记录实际终态。 | 不另起重复进程或动作。 |
| 本地测试已结束 | 检查退出码、日志、当前工作树及测试所对应的文件版本。 | 需要时只重跑已知安全的本地验证；先确认它的文件副作用。示例用 `python -B` 避免字节码缓存，但其他测试仍可能写产物。 |
| 外部动作已落地 | 对照远端分支、服务收据或原业务操作键检查实际结果。 | 不重做已完成动作；若状态不符合预期，按原动作契约修复或补偿。 |
| 接收端确认执行失败且无副作用 | 核对失败回执和接收端状态，确认没有落地、部分提交或仍在处理。 | 原授权仍覆盖该动作且接收端契约允许时才重试；非幂等写入按接收端操作键/去重规则处理，不自行换键绕过去重。 |
| 明确未执行且无副作用 | 检查授权是否仍有效，以及原动作是否可重复。 | 只在原授权仍覆盖该动作、且动作契约允许时重试；非幂等写入按接收端操作键/去重规则处理。 |
| 有部分效果或未能可靠核实 | 先记录并核对已知文件改动/远端回执，再对账未知部分；无法核实时保持未知。 | 不盲目重放；必要时停止并由维护者决定如何恢复。 |

对 `git push`，检查远端目标分支是否指向预期提交，并考虑并发更新；对创建工单等服务请求，查询原业务操作键。如果原会话记录（transcript）没有成功回执，只说明记录里没有回执，不能推出动作未发生。应用运行恢复和副作用对账见[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../systems/ai-application-architecture.md)。

相关机制：

- [什么时候应该让模型决定下一步？](./agent-fundamentals.md)：说明 agent loop（智能体循环）、工具集合、Skill 和停止条件；本章接手一个已观察到的测试失败，落实文件与 shell 的执行边界。
- [模型怎样把工具请求交给宿主执行？](./tool-design-and-function-calling.md)：说明工具调用请求、授权、实际执行与结果回传的分工。
- [智能体如何把证据变成任务、工具调用和可恢复的运行？](./orchestration-patterns.md)：另一运行以只读日志调用 `c2` 起步，工单写入另行审批。本章只到本地补丁、测试和差异验收。
- [生产 AI 如何阻止不可信内容诱导模型越权？](../safety/ai-safety-in-production.md)：补充高影响操作的授权、审批摘要与停止路径。
- [生产应用运行时怎样管理部署凭据？](../../engineering-foundations/infrastructure/production-application-runtime.md)：说明服务凭据和部署身份的隔离、轮换与审计。

> [!info]- 来源
> Codex CLI 本机行为核验于 2026-11-12，版本为 `0.167.0`；该版本源码固定于 commit `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`。同日也查阅 OpenAI 当前文档；其内容会比本机版本更新。每条来源只支持标明的接口/版本范围，不把 Codex 行为外推为所有 harness 的承诺。
>
>
> - **Codex CLI 参数与会话续接。** OpenAI，[CLI reference](https://developers.openai.com/codex/cli/reference)，检查 `--sandbox`、`--ask-for-approval`、`--add-dir` 和 `codex resume`；另用本机 `codex --version` 与 `codex --help` 核对安装版本及 flag。CLI 会话续接不表明原命令的外部效果状态。
>
> - **审批、操作系统沙箱、工作区范围和命令网络。** OpenAI，[Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)，检查 “Sandbox and approvals”、“Network access”、“Protected paths in writable roots” 和 “Run without approval prompts”。页面说明 Codex CLI / IDE / Desktop 的本地命令边界；web 搜索、MCP 和连接器仍有各自的网络/权限控制。
>
> - **模型工具调用由谁执行，以及如何用 ID 回传结果。** OpenAI，[Function calling](https://developers.openai.com/api/docs/guides/function-calling)，检查 “Handling function calls”；模型返回带有调用 ID、工具名与参数的调用项，调用方执行后再回传结果。该 API 例子用于解释宿主职责，不等于 Codex CLI 的内置文件/shell 工具接口。
>
> - **Skill 的发现与按需读取。** OpenAI，[Skills](https://developers.openai.com/codex/skills)，检查 Codex 先暴露技能名称与描述、匹配后再加载完整 `SKILL.md` 的说明；它是指引层，不是工具注册或权限机制。
>
> - **项目级说明文件的发现与合并。** OpenAI，[Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)，检查项目目录内发现 `AGENTS.md` 的路径与合并顺序，以及会话启动时重建指令链的说明；此机制与 Skill 的渐进加载分开。
>
> - **hook 事件、发现配置、信任、matcher、PreToolUse 与 PermissionRequest 输出契约。** OpenAI，[Hooks](https://developers.openai.com/codex/hooks)，检查事件表、“Where Codex looks for hooks”、“Review and trust hooks”、“Matcher patterns”、“Tool coverage”、“PreToolUse”、“PermissionRequest” 和 “PostToolUse”。当前页面说明 PostToolUse 怎样替换普通结果；本机 0.167.0 对应输出 schema 还由固定源码核对。
>
> - **0.167.0 的事件列表和 schema。** OpenAI Codex [rust-v0.167.0 release](https://github.com/openai/codex/releases/tag/rust-v0.167.0)，源码固定于 [commit `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`](https://github.com/openai/codex/tree/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a)：`codex-rs/hooks/src/lib.rs` 的 `HOOK_EVENT_NAMES` 与 `HOOK_EVENT_NAMES_WITH_MATCHERS`；`codex-rs/hooks/src/schema.rs` 的 hook command input/output wire 类型；`codex-rs/core/src/hook_runtime.rs` 的调用前、权限请求和调用后调度；`codex-rs/core/src/tools/approvals.rs` 的审批决策流程。
>
> - **运行身份与副作用核对。** [AI 应用架构](../systems/ai-application-architecture.md)说明本地会话状态与应用运行状态、接收端副作用核对的边界；此处在合成案例中沿用该机制，没有执行远端写入。
