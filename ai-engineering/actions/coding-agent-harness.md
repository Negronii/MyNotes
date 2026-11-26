# 模型选到 shell 或文件工具后，由谁决定能否执行？

coding agent harness (代码智能体运行框架) 把模型接到 shell、文件编辑等工具和本地运行环境上。模型只提出工具调用或补丁；harness 检查工具、参数和权限之后，才把请求交给本地进程执行，再把结果送回模型。本章回答：在这条路径上，沙箱、审批、hook、Skill 和测试各自决定什么；一次本地修复怎样留下可复放的证据；中断或恢复会话之后，又凭什么判断动作做到了哪一步。

## 案例：修复一个空名称校验

CI 诊断助手的只读调用 `c1` 观察到：测试 `reject_empty_name` 预期空名称返回 HTTP `400`，实际得到 `200`。这只是测试观察，不足以说明根因。本章用一个合成的本地夹具 `validator.py` 演示修复路径；它不对应任何真实项目，也不是 build 42 的真实源码。用户要求修正这个边界行为并检查差异；这项任务只改本地代码，不建工单、不推送、不部署。

本章以 OpenAI 的 Codex CLI 为具体运行时，hook 与权限相关的行为在 `codex-cli 0.167.0` 上核验（2026-11-12）。Codex CLI 是包住模型的程序，不是模型本身。模型写出补丁或声称“已修复”，既不授予文件系统或业务权限，也不证明操作成功。

一次获准的 shell 调用的路径如下：

~~~mermaid
sequenceDiagram
    participant M as 模型
    participant H as harness
    participant T as 执行进程
    M->>H: 工具名与参数
    H->>H: 前置检查、沙箱判断与审批
    H->>T: 获准后执行
    T-->>H: 输出与退出状态
    H->>H: 执行后检查
    H-->>M: 回传处理后的结果
~~~

请求可能在前置检查或审批时停下；执行之后，结果还可能被替换。“获准后执行”针对的是这一条具体请求，而不是“这个工具存在”。

## 沙箱和审批为什么是两条独立的轴？

这是 harness 里最容易混淆的一对概念，必须分开讲：

- **sandbox (沙箱)** 在操作系统层限制进程**实际能做什么**：能读写哪些目录、能否联网。它对进程及其子进程持续生效，与有没有人批准无关。
- **approval policy (审批策略)** 决定**是否以及何时请人批准**一次越界请求，以及没批准时怎么办。

两条轴组合起来，才决定一条命令的命运：

| 请求 | 沙箱判断 | 审批策略 | 结果 |
|---|---|---|---|
| 在工作区里读文件、打补丁、跑测试 | 在允许范围内 | 不需要询问 | 直接执行 |
| 写工作区外的文件或访问网络 | 超出范围 | 允许申请批准 | 请求一次批准；批准只覆盖这条请求的实际范围，也不保证执行成功 |
| 同上 | 超出范围 | 从不询问 | 不弹审批，请求也不会因此自动获准 |
| 任何命令 | 完全放开沙箱 | 任意 | 进程不再受操作系统层限制，但业务服务仍按自己的凭据和权限判断 |

由此得出三条规则。第一，审批是请求级控制，批准一次不会放开后续操作。第二，审计时要记录进程**实际生效**的文件和网络范围，单看批准记录说明不了这一点。第三，两条轴都不替业务服务判断当前身份能否操作某个资源；shell 网络、托管网页搜索、远端 MCP 服务和连接器又各是不同的边界，不能从本地 shell 的配置推断其他工具是否联网。

> [!info] 实例：Codex CLI 0.167.0 的沙箱与审批选项
> 本机 `codex --help` 列出三种 shell 沙箱：`read-only`（只读）、`workspace-write`（工作区可写）、`danger-full-access`（完整访问）；以及两种审批策略：`on-request`、`never`。`on-request` 表示模型可以决定何时申请批准，不表示每个受限命令都会弹窗；`never` 不请求用户批准，越界请求也不会因此获准。
>
> 下面的命令同时设定两条轴（仅作说明，本章夹具没有用它执行外部写入）：
>
> ~~~sh
> codex --sandbox workspace-write --ask-for-approval on-request
> ~~~
>
> 在这个设定下，工作区内的读取、补丁和测试可以执行。shell 若尝试写 `/srv/another-project/report.md` 或访问 `https://updates.example.test`，沙箱会阻止；模型可以为这条请求申请批准。
>
> 按官方当前文档，`workspace-write` 沿用默认网络设置时 shell 网络关闭；可写根目录内的 `.git`、`.agents`、`.codex` 和 `.aws` 仍递归只读。`--add-dir` 可显式增加可写目录。官方文档和较新版本的用语可能不同，具体以正在运行的版本和配置为准。
>
> OpenAI 2026-11-18 的工程文章把 Codex sandbox 描述为包在子进程外的操作系统隔离层，进程的后代继续受同一限制；文中列出 macOS 的 Seatbelt、Linux 的 bubblewrap 加 seccomp-BPF，以及当时正在迁移到 MXC 的 Windows 实现。这是文章对当时产品设计的说明，不能证明本机 0.167.0 在每个平台上都用同一实现。

## harness 里的七层各负责什么？

一条命令从模型到执行进程，要经过多层控制。每层只负责一件事，任何一层都不能顶替另一层：

| 层 | 负责什么 | 不能证明什么 |
|---|---|---|
| 模型 | 选择下一步，生成工具调用、补丁或说明 | 没有自行获得 shell、文件或业务权限；自称完成不是验证结果 |
| CLI / harness | 提供可用工具，校验请求，路由执行，收集结果 | 工具存在不代表当前动作在权限范围内 |
| 指引层：Skill 与 `AGENTS.md` | 把流程、业务规则和项目约定带进任务指令 | 不注册工具，不授予执行或资源权限 |
| 工具前 hook | 对支持且匹配的调用作前置阻断或改写输入 | 不是完整的执行边界；没有拦截不等于安全或获准 |
| 审批策略 | 决定何时暂停请求批准，未获批准时怎么处理 | 不限制已获准进程实际能触及的路径和网络 |
| 操作系统沙箱 | 限制子进程实际可读写的目录和网络 | 不代替业务服务判断当前身份能否操作资源 |
| 测试与人工审阅 | 判断观测结果是否满足本次代码契约，检查 diff (代码差异) | 只覆盖检查过的代码和用例，不能单独证明生产行为 |

## Skill 怎样承载业务规则？

Skill 教流程、不授权，这条边界的完整说明在[什么时候该让模型决定下一步](when-the-model-decides.md)。在 harness 里，它的作用是把可复用的领域规则带进任务。

以本章夹具为例，一个“API 输入校验” Skill 可以写明：空串和全空白的名称应返回 400，`Ada` 应返回 200；先看现有测试，再跑边界测试，最后检查差异。Codex 先只向模型展示 Skill 的名称和描述，选中后才载入完整的 `SKILL.md`，参考资料和脚本按需读取。

Skill 不改变模型权重，也不保证模型能正确应用规则。分工是：模型理解当前代码、提出实现；harness 授权并执行；测试判定结果。Skill 附带的脚本也必须由 harness 按各自的权限边界执行。

项目说明是另一条指引来源。按当前 Codex 文档，Codex 开始工作前会沿目录层级查找 `AGENTS.md` 等项目指导文件并入指令。它和 Skill 的按需载入是两套机制，同样不授予任何权限。

## 一次本地修复怎样留下可复放的证据？

先声明夹具的前提：`validator.py` 里的 `status_for_name(name)` 只接收字符串或 `None`，返回 400 表示拒绝、200 表示接受。这里的 200 是函数返回值，不是发起 HTTP 请求测得的状态码。文中的模型与 harness 往返用来说明职责；能复放的部分只是这个独立夹具，复放时没有运行模型。

夹具的两个文件：

~~~python
# validator.py（基线）
def status_for_name(name):
    if name is None:
        return 400
    return 200
~~~

~~~python
# test_validator.py
import unittest
from validator import status_for_name

class T(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(status_for_name(""), 400)
    def test_blank(self):
        self.assertEqual(status_for_name("  \t "), 400)
    def test_ada(self):
        self.assertEqual(status_for_name("Ada"), 200)
~~~

修复按四步前进：

1. **复现失败。** 在夹具目录运行 `python3 -B -m unittest discover -s . -v`。`test_empty` 和 `test_blank` 失败（`200 != 400`），`test_ada` 通过，退出码 1。`-B` 让 Python 不写字节码缓存；其他测试套件仍可能写别的产物，重跑前要知道命令的文件副作用。
2. **提出补丁。** 真实往返中，harness 把文件内容和测试输出作为观察交回模型，模型提出只改 `validator.py` 一行的补丁。harness 检查补丁最终作用的文件是否在可写范围内。测试输出里即使出现了命令文字，也不能扩大本次授权。
3. **重跑验证。** 用同一命令重跑，退出码 0：

   | 函数输入 | 契约返回值 | 补丁前 | 补丁后 |
   |---|---:|---:|---:|
   | `""` | 400 | 200，失败 | 400，通过 |
   | `"  \t "` | 400 | 200，失败 | 400，通过 |
   | `"Ada"` | 200 | 200，通过 | 200，通过 |

4. **核对差异。** 分别保存补丁前后的 `validator.py`，单独计算差异，确认只改了一行。下面是这份差异，不是测试输出，也不是模型的自述：

   ~~~diff
    def status_for_name(name):
   -    if name is None:
   +    if name is None or not name.strip():
            return 400
        return 200
   ~~~

改动后，函数除了 `None`，也拒绝空串和只含空白的字符串。`name is None` 为真时短路，所以 `.strip()` 只会作用在字符串上。夹具没有测试 `None` 输入；这个分支在补丁中保持原样，但不计入本次测试证据。

这份证据支持的范围是：三个本地输入符合示例契约。它不证明真实项目的根因、未测的输入类型或生产行为，也不授权提交、推送或部署。

## planner 怎样约束验收结果，又留出实现选择？

长任务可以由 planner 先写下可观察的功能契约，再让实现者决定代码怎么组织。Anthropic 的长时应用开发案例里，契约要求用户在画布上拖出一个矩形区域后，区域内每个格子都填入当前选中的 tile。评估者用浏览器测试检查这一点，发现实现只改了起点和终点两个格子，原因是拖动结束时没有调用矩形填充逻辑。

好的契约写清可观察结果（区域内格子都变、区域外保持原样）和测试方法；事件处理、状态结构和渲染方式留给实现者，除非产品另有约束。

同一系列实验还显示，模型升级会改变旧脚手架是否必要。文章报告：Sonnet 4.5 在长时开发中需要多次重置上下文；Opus 4.5 能在同一会话里配合 compaction (上下文压缩) 继续；Opus 4.6 完成超过两小时的 DAW 任务时已不需要 sprint 切分。planner 和 evaluator 仍有价值，后续 QA 也找出了需求缺口。这些结果只适用于文章里的模型和任务。迁移模型后，应重新测量上下文重置、sprint 切分、额外总结等组件对目标任务的质量和成本贡献，只保留确有作用的部分。

## 实例：Codex hooks 怎样介入工具生命周期？

hook (生命周期钩子) 是特定运行时在定义好的事件发生时调用的脚本或 MCP 工具。它可以补充上下文、拦截受支持的工具请求或检查执行结果，但不是所有 harness 都有的通用接口。以下均为 Codex CLI 0.167.0 的行为。

### 工具调用前后的三个事件

| 事件 | 何时触发 | 能做什么 | 不能做什么 |
|---|---|---|---|
| `PreToolUse` | 受支持的工具即将执行前 | 受信任且匹配的 hook 可以阻断请求，或用 `updatedInput` 改写输入；调用随后以改写后的输入执行 | 文档和固定版本源码都没有说明所有工具会对改写后的输入重跑同一套格式和权限校验，所以 harness 要按具体执行路径核实最终参数 |
| `PermissionRequest` | 仅在即将申请审批时 | 直接允许、拒绝，或不作决定、交回常规审批流程 | 不拦截不需要审批的调用；批准不永久放开后续操作 |
| `PostToolUse` | 受支持的工具产生结果之后 | `decision: "block"` 用 hook 反馈替换原工具结果后继续；`continue: false` 停止正常处理原结果，以 hook 反馈或 stop text 继续 | 撤销不了已经写入的文件或发出的请求；检查工具输出也不等于任务验收通过 |

`PreToolUse` 和审批都不能代替操作系统沙箱。

### 配置与拒绝输出

下面是项目层 `.codex/hooks.json` 的配置片段和拒绝时的输出形状，不是能单独运行的完整 hook。前提是：会话从仓库根目录启动；脚本存在于 harness 能访问的位置，从标准输入读取 hook 请求，按产品 schema 向标准输出写决定；Codex 信任该项目配置层，非托管的 hook 定义也已由用户审阅并信任。从子目录启动时，命令要能稳定找到同一脚本。

~~~json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {"type": "command", "command": "python3 .codex/hook.py"}
        ]
      }
    ]
  }
}
~~~

匹配器 `^Bash$` 只按工具名选中 shell 类工具，不会挑出 `git push` 这一条命令，也不覆盖所有工具入口。脚本还要检查 `tool_input.command` 等实际参数。脚本发现本地任务不应执行 `git push` 时，可以输出：

~~~json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Local fixture only."
  }
}
~~~

Codex 据此在工具运行前阻断这次调用。这是 Codex 的 hook 输出 schema，不是模型、shell 或 MCP 的通用协议。

### 0.167.0 的 14 个事件

固定版本源码列出 14 个事件名，分属不同的生命周期点：

| 触发点 | 事件 | 注意 |
|---|---|---|
| 每次模型请求 | `PreModelRequest`、`PostModelRequest` | 按每次请求尝试触发，不是每个用户任务一次 |
| 工具调用前后 | `PreToolUse`、`PermissionRequest`、`PostToolUse` | 审批 hook 只在即将申请审批时触发；工具 hook 只覆盖受支持的工具路径 |
| 用户输入或轮次 | `UserPromptSubmit`、`Stop`、`Interrupt` | 用户提交、当前轮将停止、用户中断；中断不撤销已发生的动作 |
| 上下文压缩 | `PreCompact`、`PostCompact` | 分别在压缩前后，不是工具执行步骤 |
| 会话开始或结束 | `SessionStart`、`SessionEnd` | 开始可来自启动、恢复等来源；会话结束不是每轮结束 |
| 子 agent 启停 | `SubagentStart`、`SubagentStop` | 针对子 agent 生命周期，不等于主会话的工具调用 |

这些事件不是每个工具调用都依次经过的流水线。其中只有 9 个事件接受 `matcher`，其余忽略该字段。各事件的输入、匹配方式和输出效果由产品版本定义；升级 Codex 时要核实当前安装版本的配置和 schema，不能把当前文档或其他 harness 的事件名直接套到旧版本上。

## 中断、断线或 resume 之后怎样恢复？

中断后要先分开两件事：用什么标识找到这个动作，以及这个动作实际执行到了哪一步。

几种标识各管一层：Codex CLI 的 `session_id` 定位会话，`tool_use_id` 标识会话里的一次工具调用；应用层的 `runId` 标识整次运行；外部写入则有接收端认的业务操作键，例如[授权一章](authorization-gates-for-actions.md)里建单用的 `run-r42-6:create-issue:v1`。这些标识怎样分层、哪一层是权威状态，见[一次 AI 运行断线或崩溃后，凭什么恢复](../runs/run-identity-and-authoritative-state.md)。

`resume`（恢复会话）只载入会话记录，不恢复原进程，也不撤销副作用。网络断开可能只是失去了观察，动作本身仍在进行或已经完成。所以先用标识定位同一个动作，再向进程或接收端核对状态：

| 核对到的状态 | 下一步 | 重放边界 |
|---|---|---|
| 原进程或外部动作仍在处理 | 等待或继续查询同一进程、同一接收端操作，记录实际终态 | 不另起重复的进程或动作 |
| 本地测试已结束 | 检查退出码、日志、当前工作树，以及测试对应的文件版本 | 需要时只重跑已知安全的本地验证，先确认它的文件副作用 |
| 外部动作已落地 | 对照远端分支、服务收据或原业务操作键检查实际结果 | 不重做已完成的动作；结果不符预期时按原动作契约修复或补偿 |
| 接收端确认失败且无副作用 | 核对失败回执和接收端状态，确认没有落地、部分提交或仍在处理 | 原授权仍覆盖该动作、接收端契约允许时才重试；非幂等写入沿用原操作键，不换键绕过去重 |
| 有部分效果，或无法可靠核实 | 先记录并核对已知的文件改动和远端回执，再对账未知部分 | 不盲目重放；无法核实时保持未知，必要时停下交维护者决定 |

两个具体例子：对 `git push`，检查远端目标分支是否指向预期提交，并考虑并发更新；对建工单这类服务请求，查询原业务操作键。会话记录里没有成功回执，只说明记录里没有，不能推出动作没发生。外部写入结果未知时的完整处理见[退款请求超时后，怎样查清结果而不重复扣款](../runs/external-writes-and-reconciliation.md)。

## 长任务接续要保存哪些状态？

长任务的接续需要可检查的项目状态，不只是一份对话摘要。Anthropic 的 long-running agent 实验里，initializer 先准备仓库、启动脚本和带优先级的 `feature_list.json`；之后每个编码会话读取进度文件和 Git 状态，逐项实现、测试并更新记录。这说明持久化的进度能帮新上下文接手，但不说明摘要能验证功能是否完成。

接续记录应同时指向会话和项目状态：当前工作树、检出的提交和未提交差异、测试命令及其退出码、被测工具的版本。本例对应的是：失败证据从 `c1` 读取；修复状态从工作树和 `python3 -B -m unittest discover -s . -v` 的结果核对；hook 与权限行为的被测版本是 `codex-cli 0.167.0`。只有来源、代码状态和测试结果对应同一版本时，旧会话里的结论才能用于判断当前修复。各编码 Agent 产品怎样恢复同一条任务事实，见[Claude Code、Codex、Devin 和 Cursor 怎样恢复同一条任务事实](../context/coding-agent-task-recovery.md)。

## harness 放行的只是一次具体请求

harness 放行的永远是一次具体请求，由沙箱限制它能碰到什么、由审批决定要不要问人、由测试和差异判定结果；模型的补丁和“已修复”只是提议。涉及业务资源的写入，仍要回到[授权一章的五道关](authorization-gates-for-actions.md)。

> [!info]- 来源
> Codex CLI 本机行为于 2026-11-12 核验，版本 `0.167.0`，源码固定于 commit `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`；同日查阅的 OpenAI 当前文档可能比本机版本更新。每条来源只支持标明的接口和版本范围，不把 Codex 行为外推为所有 harness 的承诺。
>
> - **CLI 参数与会话续接**（“沙箱和审批为什么是两条独立的轴”的实例、“中断、断线或 resume 之后怎样恢复”）。OpenAI，[CLI reference](https://developers.openai.com/codex/cli/reference)，`--sandbox`、`--ask-for-approval`、`--add-dir`、`codex resume`；另用本机 `codex --version` 与 `codex --help` 核对版本与 flag。会话续接不表明原命令的外部效果状态。
> - **审批、操作系统沙箱、工作区范围与命令网络**（同上实例）。OpenAI，[Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)，“Sandbox and approvals”“Network access”“Protected paths in writable roots”“Run without approval prompts”。页面说明 Codex CLI / IDE / Desktop 的本地命令边界；web 搜索、MCP 和连接器另有各自的控制。
> - **模型工具调用由调用方执行并按 ID 回传**（开头的路径图、七层表的 harness 行）。OpenAI，[Function calling](https://developers.openai.com/api/docs/guides/function-calling)，“Handling function calls”。用于解释宿主职责，不等于 Codex CLI 内置文件与 shell 工具的接口。
> - **Skill 的发现与按需读取**（“Skill 怎样承载业务规则”）。OpenAI，[Skills](https://developers.openai.com/codex/skills)，先暴露名称与描述、匹配后再载入完整 `SKILL.md`；是指引层，不是工具注册或权限机制。Anthropic，[Equipping agents for the real world with Agent Skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills)，2025-10-16，说明 Skill 先以元数据发现、再按需读取，承载领域知识与程序，不改变基础模型能力。
> - **项目说明文件的发现与合并**（同上）。OpenAI，[Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)，项目目录内发现 `AGENTS.md` 的路径与合并顺序、会话启动时重建指令链。
> - **hook 事件、发现配置、信任、matcher、三个工具事件的输出契约**（“实例：Codex hooks 怎样介入工具生命周期”）。OpenAI，[Hooks](https://developers.openai.com/codex/hooks)，事件表、“Where Codex looks for hooks”“Review and trust hooks”“Matcher patterns”“Tool coverage”“PreToolUse”“PermissionRequest”“PostToolUse”。
> - **0.167.0 的 14 个事件、9 个接受 matcher 的事件及 schema**（同上）。OpenAI Codex [rust-v0.167.0 release](https://github.com/openai/codex/releases/tag/rust-v0.167.0)，源码 [commit `086ccc8`](https://github.com/openai/codex/tree/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a)：`codex-rs/hooks/src/lib.rs` 的 `HOOK_EVENT_NAMES` 与 `HOOK_EVENT_NAMES_WITH_MATCHERS`；`codex-rs/hooks/src/schema.rs` 的输入输出类型；`codex-rs/core/src/hook_runtime.rs` 的调用前、权限请求、调用后调度；`codex-rs/core/src/tools/approvals.rs` 的审批决策流程。
> - **Codex 本地沙箱的操作系统隔离设计**（实例 callout 最后一段）。OpenAI，[Inside the Codex sandbox](https://openai.com/index/inside-the-codex-sandbox/)，2026-11-18。具体行为依产品、版本、平台和权限配置而定。
> - **Planner、实现者与评估者的功能契约，及模型升级后的脚手架变化**（“planner 怎样约束验收结果”）。Anthropic，[Harness design for long-running application development](https://www.anthropic.com/research/harness-design-long-running-apps)，2026-03-24。结果限于其交互式应用和 DAW 实验，不构成跨模型的固定建议。
> - **长时运行的初始化、进度清单与编码循环**（“长任务接续要保存哪些状态”）。Anthropic，[Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)，2025-11-26。适用范围限于其模型与任务。
> - **夹具复放**（“一次本地修复怎样留下可复放的证据”）。本章两个夹具文件在 Python 3 下用 `python3 -B -m unittest discover -s . -v` 复放：基线 2 个失败、退出码 1；补丁后 3 个通过、退出码 0。
