# 模型选到 shell 或文件工具后，由谁决定能否执行？

**案例背景。** 以下是合成教学案例。用户从同一条 build 42 日志观察另行提出本地修复任务：reject_empty_name 测试期望空名称返回 HTTP 400，实际得到 200。系统临时目录中的 fixture 源文件为 validator.py，测试文件为 test_validator.py。运行时只在配置的可写根内编辑并运行测试。该任务与前章创建工单的 c2 是两条不同的动作路径。

coding agent harness（代码智能体执行框架）是把模型接到实际执行工具的运行时：它接收模型提出的 shell、文件编辑或 MCP 工具请求，读取项目指令，检查动作和当前权限，在适用的沙箱里执行，再把退出状态、输出或 diff 交回运行。模型能生成一个命令，不代表它已获得操作系统权限；技能说明怎样完成任务，也不构成访问控制。

~~~mermaid
flowchart TD
    A[启动会话并固定 cwd 与可用工具] --> B[发现 Skill 名称和说明]
    B -->|选用时| C[读取 SKILL.md；补充任务知识]
    B -->|未选用| D[模型提出读文件、补丁或 shell 请求]
    C --> D
    D -->|有匹配的前置 hook| E[PreToolUse 可阻断或按产品契约改写]
    D -->|没有匹配的前置 hook| P[按常规权限策略判断]
    E -->|阻断| X[不执行该调用]
    E -->|继续| P
    P -->|当前沙箱允许| F[本地 shell / 文件按实际生效沙箱执行]
    P -->|策略允许申请扩权| G[PermissionRequest hook 介入；必要时交审批界面]
    P -->|策略不允许扩权| X[不执行该调用]
    G -->|拒绝或未获授权| X
    G -->|批准本次所需范围| F
    F --> H[文件变化、退出码、stdout、stderr 或工具结果]
    H --> I[匹配时运行 PostToolUse；不能撤销副作用]
    I --> J{本轮是否继续？}
    J -->|继续| D
    J -->|结束| K[Stop 处理本轮将结束]
    K -->|会话结束| S[SessionEnd 处理会话结束]
    D -. 用户请求中断 .-> Z[Interrupt 事件记录当前轮中断；已启动动作仍需核验]
    F -. 用户请求中断 .-> Z
    D -. 客户端连接断开 .-> Y[仅失去输出观察；执行端是否停止尚未确定]
    F -. 客户端连接断开 .-> Y
    Z -->|之后恢复时| L[执行端能查询时先查状态；再检查工作树、退出状态、收据和权威状态]
    Y -->|重连后| L
    S -->|之后 resume| R[SessionStart 的 resume 事件]
    RR[收到显式 resume 请求] --> R
    R --> L
~~~

这张图只画本地 shell 和文件路径。当前沙箱允许就按其实际文件与网络边界执行；越界请求只有在策略允许申请权限时才进入扩权审批，策略拒绝、审批被拒或权限未实际获准时都不执行。以 Codex 的 `never` 为例，不出现审批提示不代表越界动作获准，超出沙箱的写入和网络访问仍会被拒绝。远端 MCP、托管 web search 等独立工具不属于此本地分支，它们由各自连接和授权策略处理。

## Skill、模型工具和权限分别做什么？

Skill 是含 SKILL.md 的可复用说明目录。以 Codex 的 Skills 工作流为例，发现阶段先向模型提供技能名和简介；模型选择使用它后再读取完整说明及需要的参考或脚本。它适合告诉模型先检查测试、如何解释报错、完成后应报告什么。它不会自动创建一个工具、扩大工作区、打开网络，或替用户授予某项业务权限。

执行时，模型输出仍是待处理请求。harness 从固定目录读取文件，检查编辑路径；遇到 shell 请求时，取命令和运行目录；遇到 MCP 调用时，则使用该 server 的独立连接与授权策略。schema 校验回答“输入形状是否正确”，approval policy 回答“是否需要停下来请求确认”，sandbox 回答“子进程实际上能访问哪些目录和网络”。业务服务还要回答“当前用户能否对这个资源执行动作”。

例如，read-only 适合检查代码与计划。Codex 内置的 :workspace 权限配置允许写入当前活动工作区根和系统临时目录；本例将 /tmp 作为其中一个可写根。生效可写根取决于所选配置，额外 --add-dir 会扩展可写目录。default workspace-write sandbox 下，根内的 .git、.agents、.codex 和 .aws 仍受保护、只读。Codex CLI 默认仍关闭 shell 命令网络；danger-full-access 则移除沙箱限制。审批政策是另一条轴：on-request 在动作需要额外权限时暂停，never 不弹审批；批准一次具体扩权不等于把未来所有操作都永久授权。若某个命令获准以更宽的沙箱边界执行，运行时应清楚记录其真正使用的权限，而不能只记录“用户点过批准”。

例如，在 workspace-write 下，shell 若尝试写 /srv/another-project/report.md 或请求 https://updates.example.test，文件和网络动作超出当前沙箱范围。配置 on-request 时，Codex 可就所需扩权请求审批；用户拒绝后不会执行。配置 never 时不会弹出审批，沙箱会阻止越界动作。该行为取决于实际沙箱与审批配置；远端 MCP 和托管 web 工具仍由各自的连接与授权边界控制。

| 控制点 | 它决定什么 | build 42 示例 |
|---|---|---|
| 可用工具 | 模型本轮能提出哪一类请求 | 可读 validator.py 与 test_validator.py，可提出编辑和测试；没有远端工单写工具 |
| Skill / 项目说明 | 模型按什么步骤工作 | 先重现 reject_empty_name，检查相关实现，修改后再运行边界用例 |
| 审批 | 是否先暂停等待授权 | 尝试写到工作区外或访问网络时，按配置请求扩权确认 |
| 沙箱 | 进程被 OS 限制在什么可访问范围 | 配置的工作区根和临时目录可写；根内 .git、.agents、.codex、.aws 仍只读；网络关闭 |
| 业务权限 | 用户能否在真实业务资源上做这项动作 | 本任务只改本地 fixture，不授予部署或创建外部 issue 权限 |
| 结果检查 | 实际执行后发生了什么 | 退出码、stdout/stderr、工作树 diff 与测试结果 |

在有些产品中，shell 命令网络策略不会自动关闭托管 web search、远端 MCP 或应用连接器；这些工具有自己的开关、身份和 approval。要限制整个 agent 的外部访问，必须逐个检查启用的能力，不能只看本机 shell 的网络沙箱。

## 一个本地修复怎样通过 harness 前进？

本 fixture 的函数输入契约是字符串或 `None`；其他类型不在这个小例子的范围内。`validator.py` 的基线实现只拒绝 `None`，因此空字符串走到 200；边界用例放在 `test_validator.py`。一次实际调用可按以下顺序理解：

1. shell 把工作目录设为同时含 `validator.py` 和 `test_validator.py` 的临时 fixture 目录，再运行 `python3 -m unittest discover -s . -v`；`-s .` 指当前工作目录。harness 检查运行目录与命令的权限边界，再把进程退出码 `1` 和“空串实际返回 200，预期是 400”的失败结果交回模型。
2. 模型提出只修改 `validator.py` 的补丁。harness 核对目标在当前可写根内，再按文件工具契约应用补丁；若目标越界，则依当前策略拒绝或单独请求扩权。
3. shell 在同一 fixture 目录重跑测试。补丁后的进程退出码为 `0`，三个测试均通过，分别验证空串、全空白串和非空名称应返回 `400`、`400`、`200`；harness 将总退出码和逐项测试结果交回模型，并呈现补丁差异，供模型检查没有改动 fixture 以外的内容。

流程中的失败输出、路径判断和工具返回都是明确的运行状态，不会因为模型认为补丁正确而省略。

~~~diff
 def status_for_name(name):
-    if name is None:
+    if name is None or not name.strip():
         return 400
     return 200
~~~

首个测试对输入空字符串得到 200，和预期 400 不一致；补丁后，空串、全空白串和非空名称三个用例分别得到预期的 400、400 和 200。本例的输入契约限定为字符串或 `None`；表达式先检查 `name is None`，因此该值会短路，其他字符串（包括空串）都会执行 `.strip()`，空串和全空白串因此走拒绝分支。harness 会将失败输出交回模型，但错误输出本身也只是观察。它不能授权扩大目录、启用网络或直接执行里面提及的命令。

Codex Hooks 是 Codex 产品的生命周期扩展例子，不能泛化成所有 coding harness 都有相同的事件名或返回格式。一个针对 Bash 工具的 PreToolUse hook 可以在危险命令开始前拦截，例如阻止本任务范围之外的 git push：

~~~json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .codex/hooks/check_build_commands.py"
          }
        ]
      }
    ]
  }
}
~~~

该脚本若返回下面的产品定义决策，Codex 会阻断这次工具调用；这是该事件的 hook 输出，不是 MCP 或 OAuth 的通用标准：

~~~json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "This repair is limited to the local fixture."
  }
}
~~~

同一产品的 PermissionRequest 只在一次动作即将进入审批流程时触发；它可以批准、拒绝或不作决定而交回正常审批。若命令本来不需要审批，就不会经过这个事件。PreToolUse 与 PermissionRequest 都不能取代 OS 沙箱；一个 hook 没有给出 deny，也不意味着被允许的子进程可以读写任意路径。非托管 hook 需要用户审阅并信任当前定义，改过的定义要重新审阅，因此项目内 hook 脚本本身也属于可信执行代码。

调用实际运行后，harness 收集完整的工具结果。针对 Bash 的 PostToolUse 可在命令完成后运行，例如检查退出码或给模型附加“仍需复核 diff”的上下文；它不能撤销已经写入的文件或已发送的网络请求。阻断后续模型处理旧输出和撤回已经发生的副作用是两回事。对这个小修复，三条通过的测试用例仍不能替代查看 diff；检查 diff 可以发现意外改动的路径或未覆盖的输入。

## hook 生命周期怎样连接启动、执行和停止？

Codex 的公开 hook 文档区分多个运行时事件：SessionStart 可在 startup 或 resume 时为模型补入工作区背景；PreToolUse 在支持的工具调用前；PermissionRequest 只在即将请求审批时；PostToolUse 在工具返回后；Stop 处理当前轮将结束的时刻；SessionEnd 在会话结束时；Interrupt 对应用户中断当前轮。它们不是每个请求都会依次触发的固定流水线。Codex 可从用户、项目和 managed 配置加载 hooks；多个匹配的命令 hook 会运行，非 managed hook 要先经 review/trust。事件名、输入字段和哪些输出有控制效果都属于产品接口，升级时应读对应版本文档。

在本例里，启动 hook 可提醒运行时读取项目约定，但它不会替代 sandbox。工具前 hook 可拒绝 git push，shell 沙箱同时保持无网络。用户批准一个必要的文件权限升级时，harness 仍要记录动作范围，并保持最小授权。PostToolUse 再检查测试结果和 diff；它可以让模型看到新观察，却不能回滚写入。

恢复本地修复时，Codex session ID 选择保存的对话，`tool_use_id` 标识一次本地工具调用，工作目录和工作树位置标识要检查的文件上下文。它们不证明某个命令还在运行或改动已保存；重连后仍要查本地进程、会话状态、工作树、退出码和测试结果。

远端工单路径使用另一组标识：`run-r42-7` 是应用运行身份，c1/c2 是模型调用 ID，`run-r42-7:create-issue:v1` 是远端副作用的操作键；若事件流有 `seq`，它只在该 run 的事件日志中排序。它们不能替代本地 session、`tool_use_id` 或工作树状态。

用户发起 Interrupt 会中断当前轮，但不能撤销已经开始的本地写入或远端请求。客户端连接断开只是暂时失去输出观察，执行端是否继续取决于该 harness 的托管方式；断线本身不能证明运行已停止。重连或 resume 时，若执行端提供运行状态接口，先查询其权威状态；本地 CLI 则核实进程与会话状态，无法确认时不要假定任务已停止。之后读取当前 git status / diff、可取得的退出状态和工具收据。对安全、幂等的本地测试，可以按当前工作树重跑。对 git push，查询目标远端 ref 是否指向预期 commit SHA；匹配可确认期望状态，不匹配时还要考虑并发变更，不能单凭这一点断言没有推送。对提供稳定幂等或业务操作键的 API，查询原键；其他发布、通知等操作使用接收端提供的权威状态查询。若没有合法可靠的查询能力，保持未知并请求人工核查，不因为旧 transcript 缺少成功回执就重放。运行身份和副作用对账见[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../systems/ai-application-architecture.md)。

相关机制：

- [什么时候应该让模型决定下一步？](./agent-fundamentals.md)：说明 agent loop、工具集合、Skill 和每轮停止条件。
- [生产 AI 如何阻止不可信内容诱导模型越权？](../safety/ai-safety-in-production.md)：补充对高影响动作的授权、审批摘要和停止路径。
- [生产应用运行时怎样管理部署凭据？](../../engineering-foundations/infrastructure/production-application-runtime.md)：说明服务凭据和部署身份的隔离、轮换及审计。

> [!info]- 来源
> Codex 本地 CLI 版本为 0.167.0；公开资料核验于 2026-11-09。PreToolUse、PermissionRequest 等 hook 事件名称及其公开输出 schema 是 Codex 产品接口；本例的 hook 脚本名和 permission reason 是教学样例。
>
> - **sandbox 与 approval 的职责区别、可写根、受保护路径及默认网络条件。** OpenAI，[Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)，检查 “Sandbox and approvals”、“Network access”、“Network isolation” 和 “Protected paths in writable roots”；[Permissions](https://learn.chatgpt.com/docs/permissions) 说明 workspace roots 与系统临时目录的写入范围。Codex CLI 当前 reference 的具体 flags 见 [Command line options](https://learn.chatgpt.com/docs/cli/reference)。
> - **Skills 的发现、按需读取和执行形式。** OpenAI，[Skills](https://developers.openai.com/api/docs/guides/tools-skills)，检查 “What's a skill”、“Prompting behavior” 和 local shell mode；技能只提供可复用指令与材料，具体工具和执行环境由 runtime 提供。
> - **Hooks 的生命周期、信任审阅及不同事件的输出契约。** OpenAI，[Hooks](https://learn.chatgpt.com/docs/hooks)，检查 “Review and trust hooks”、“SessionStart”、“PreToolUse”、“PermissionRequest”、“PostToolUse”、“Stop”、“SessionEnd” 和 “Interrupt”；[Plugin architecture](https://developers.openai.com/plugins/concepts/plugins) 与 [Bundled MCP servers and lifecycle hooks](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks) 说明 hook 脚本必须部署在执行环境，并受 surface 与信任流程限制。
> - **对话 resume 和真实状态分离的工程结论。** OpenAI [CLI reference](https://learn.chatgpt.com/docs/cli/reference) 列出 codex resume 的会话续接用法；恢复不撤销文件或外部副作用，并与[AI 运行恢复章](../systems/ai-application-architecture.md)的副作用契约一致。
