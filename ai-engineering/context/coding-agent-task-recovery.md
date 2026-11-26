# Claude Code、Codex、Devin 和 Cursor 怎样恢复同一条任务事实？

编码 agent 的会话很长，迟早要压缩上下文，或者在中断后恢复。四个常见产品都提供了压缩、恢复会话和记忆文件的入口，但公开程度和做法各不相同。本章拿同一条任务事实去对照它们：压缩或恢复之后，这条事实还在哪里，怎样才能可靠地找回来。结论是：会话历史、摘要和记忆只能当作线索，任务事实仍要按本轮授权和当前版本，从权威记录重建。

本章是[每次调用的上下文预算该怎样分配，哪些状态必须留在应用里？](context-budget-and-state-layers.md)的支线，沿用那一章的规则：摘要有损、服务端会话只改变传输方式、权威状态留在应用里。产品内容依据公开文档，核对于 2026-11-25，Claude Code 会话入口于 2026-11-26 复核；产品会更新，使用前按当前版本再查。

## 要恢复的是哪条事实

沿用 CI 诊断助手的合成记录 `run-r42-6#c1`：`run-r42-6` 是应用运行 ID，`c1` 是该运行里一次只读的 `read_build_log(build_id=42)` 工具调用。结果记录构建 42 的测试 `reject_empty_name` 预期 HTTP `400`、实际 `200`，`exit_status=1`。

假设这件事发生在一个编码 agent 的长会话里，之后会话被压缩，或者第二天被恢复。要继续调查或修复，agent 需要的不是“之前有个单测失败”这种印象，而是：

- 精确的测试名、预期值和实际值；
- 这些值来自哪次调用、哪份日志；
- 调用者现在是否仍有权读取这份日志；
- 继续改代码时，当前工作树、测试命令和对应的文件版本。

压缩、恢复和记忆分别能保住其中哪些，就是下面要对照的内容。

## 四个产品的比较维度

先把可比较的维度列出来。“公开算法”指公开资料是否说明了摘要保留什么、怎样重建上下文：

| 维度 | Claude Code / Claude API | Codex CLI / Responses API | Devin CLI / Cloud | Cursor Agent CLI / Cloud |
|---|---|---|---|---|
| 压缩入口 | `/compact`；另有清理较早工具结果 | `/compact` | `/compact` | `/summarize`（别名 `/compress`） |
| 恢复入口 | `claude --continue`、`claude --resume`、`/resume` | `/resume`、`codex resume` | `devin -r <session-id>`、`/resume`、`/continue`；`devin --cloud -r <URL>` 恢复云会话 | `--resume <thread-id>`、`agent resume`、`/resume` |
| 压缩后怎样补回 | 项目根 `CLAUDE.md` 压缩后从磁盘重新注入 | 摘要加按预算保留的较新用户消息（固定源码版本） | 文档未说明 | 收到历史文件引用，可搜索补回；长输出写入文件按需读取 |
| 记忆 / 项目文件 | `CLAUDE.md`；auto memory 的 `MEMORY.md` 索引与主题文件 | `AGENTS.md` 等项目文件；本地 Memories（默认关闭） | Git 管理的 Markdown 记忆仓库，常驻 `MEMORY.md` | Project 持久文件 |
| 服务端状态 | API：context editing、beta compaction、beta Message Threads | Conversations API、`POST /responses/compact` | 托管云会话 | Cloud Agent |
| 公开算法 | 部分：说明了两种改写方式和重新注入，未给摘要保留规则 | 开源，可在固定源码 tag 中读到实现 | 未说明 `/compact` 算法与云会话重建方式 | 未说明摘要保留、历史搜索排序与云端重建细节 |

表里没有一行能回答“恢复后 `400 → 200` 一定还在、而且仍然有效”。下面逐个产品说明这些入口做了什么。

## Claude Code 与 Claude API

Claude Code 把会话持续保存到本地 transcript 文件，可以用 `claude --continue` 打开当前目录最近的会话，用 `claude --resume` 按名称、会话 ID 或 transcript 路径恢复，在会话内用 `/resume` 切换。

上下文改写有两种：清理较早的工具结果，和 compaction (压缩)。运行 `/compact` 时，较早的对话被压成摘要；项目根目录的 `CLAUDE.md` 会在压缩后由 Claude Code 从磁盘重新读取并注入。启用 auto memory 后，会话开始时载入 `MEMORY.md` 的索引部分，之后按需用标准文件工具读取相关主题文件。

在 API 一侧：

- Messages API 的 context editing 在请求进入模型前清理较早的工具结果。被清掉的 `c1` 结果要靠应用保留的原记录，按当前权限重新取回。
- 保留近期轮次的 beta compaction 把旧轮次压成摘要块，再接上选定的近期轮次。
- beta Message Threads 在服务端短期保存对话；它的期限和续接规则见上下文预算一章的[服务端 thread 实例](context-budget-and-state-layers.md#服务端%20thread%20只改变传输方式)。

对 `c1` 来说，`CLAUDE.md` 能稳定带回的是项目指引，不是这次运行的观察；摘要是否保留了 `400 → 200`，公开资料没有保证。

## Codex CLI 与 Responses API

Codex CLI 用 `/compact` 触发摘要，用 `/resume` 或 `codex resume` 载入保存的聊天。`AGENTS.md` 等项目文件承载稳定指引。本地 Memories 默认关闭；启用后，符合条件的旧聊天可以在后台生成记忆，`/memories` 控制当前聊天能否读取已有记忆、能否贡献新记忆。

Codex 是开源的，可以直接看实现。在源码 tag `rust-v0.172.0` 中有两条压缩路径：

- **常规 `Responses` 路径：** 先由模型生成摘要，再由 CLI 按预算保留较新的用户消息，并插入摘要。
- **`ResponsesCompactionV2` 路径：** 向 Responses 提交 compaction trigger，安装返回的压缩项。

这是该源码版本的实现，其他版本可能不同。

在 API 一侧，Conversations API 用持久 ID 保存消息、工具调用和工具结果，可以跨会话、设备和任务继续。独立的 `POST /responses/compact` 返回压缩后的历史输入项；下一次 `POST /responses` 把这些项按原顺序放进 `input`，再附加新的用户消息。

对 `c1` 来说，常规路径保留的是较新的用户消息和一段模型摘要；工具结果里的精确字段是否进入摘要，取决于模型这一次怎样写。

## Devin CLI 与 Devin Cloud

Devin CLI 保存会话历史，可以用 `devin -r <session-id>`、`/resume` 或 `/continue` 恢复，`devin --cloud -r <URL>` 恢复托管的云会话；`/compact` 触发会话压缩。

Devin Memory 是一个持久的、用 Git 管理的 Markdown 仓库。每个会话都载入 `MEMORY.md`，其他笔记在需要时由 Devin 搜索和读取。公开文档说明记忆用来保存偏好、纠正、决策和环境经验，并明确**不保存**会话摘要，以及 PR 编号、状态这类任务状态。

本章依据的文档没有说明 `/compact` 的内部算法，也没有说明云会话恢复时怎样重建上下文。对 `c1` 来说，按文档的定位，它本来就不该进记忆；能找回它的是会话历史，或者应用自己的运行记录。

## Cursor Agent CLI、Cloud Agent 与 Projects

Cursor CLI 用 `/summarize` 压缩上下文，`/compress` 是别名；`--resume <thread-id>`、`agent resume` 或 `/resume` 继续历史线程。CLI 对话可以交给 Cloud Agent，在网页或移动端继续。

Cursor 的公开文章描述了两种按需读取：

- 摘要后，agent 会收到一份历史文件的引用；需要补回遗漏的消息时，可以搜索这份文件。
- 较长的 shell 或 MCP 输出会写入文件，agent 可以先用 `tail` 看末尾，再读取需要的部分。

Project 的持久文件跨 agent 和上下文重置保存偏好、待办和工作流程。公开资料没有交代摘要保留算法、历史搜索的排序方式，以及 Cloud Agent 的底层会话存储与重建细节。

对 `c1` 来说，历史文件让精确字段有机会被搜回来；但搜到的是当时的文本，它现在是否仍有效、调用者是否仍有权看，文件本身不回答。

## 历史仍须按本轮授权和版本重建

四个产品的入口不同，结论相同：服务端 thread 或 CLI resume 带回的是既有历史，摘要和跨任务记忆只能提供检索线索。历史里可能有当前规则要求剔除的内容，来源也可能已经过期。所以恢复之后，任务事实要从权威记录重建：

1. 在应用的运行账本里定位 `run-r42-6`。
2. 从 `c1` 的调用记录读出原始日志的位置。
3. 按当前调用者的权限，取回构建 42 的日志，核对测试名、预期值和实际值。
4. 继续代码任务时，检查当前工作树、测试命令及其对应的文件版本，而不是相信会话里记着的旧状态。
5. 用这些结果组装新的上下文；当前规则要求剔除或已经过期的内容不再带入。

为此，应用状态至少要保存：`runId`、实际的工具调用标识、日志位置、授权和版本的核对结果，以及下一步。摘要为什么不能代替这些记录，见[摘要是有损变换](context-budget-and-state-layers.md#摘要是有损变换)；运行状态为什么必须由应用持有、恢复时读哪些记录，见[一次 AI 运行断线或崩溃后，凭什么恢复？](../runs/run-identity-and-authoritative-state.md)；编码 agent 的 harness 在中断和 resume 后怎样恢复工作树与命令，见[模型选到 shell 或文件工具后，由谁决定能否执行？](../actions/coding-agent-harness.md)。

> [!info]- 来源
> `run-r42-6#c1` 为合成教学记录。产品文档核对于 2026-11-25，Claude Code 会话入口于 2026-11-26 复核。
>
> - **Claude Code 的会话、压缩、记忆与 API 侧上下文改写**（“Claude Code 与 Claude API”与比较表）：Anthropic，[Claude Code commands](https://code.claude.com/docs/en/commands)、[Manage sessions](https://code.claude.com/docs/en/sessions)（`--continue`、`--resume`、`/resume` 与本地 transcript）、[Memory](https://code.claude.com/docs/en/memory)、[Costs](https://code.claude.com/docs/en/costs)、[Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)、[Compaction that keeps recent turns](https://platform.claude.com/docs/en/build-with-claude/compaction-keep-recent-turns)。Claude Code 文档分别列出清理旧工具结果和压缩对话。
> - **Message Threads**（Claude API 段落）：Anthropic，[Message threads](https://platform.claude.com/docs/en/build-with-claude/message-threads)，beta header `message-threads-2026-08-12`。
> - **Codex CLI 与 Responses API 的会话状态**（“Codex CLI 与 Responses API”与比较表）：OpenAI，[Developer commands](https://developers.openai.com/codex/cli/slash-commands)、[Memories](https://learn.chatgpt.com/codex/customization/memories)、[Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)、[Compaction](https://developers.openai.com/api/docs/guides/compaction)。
> - **Codex 固定源码版本的两条压缩路径**（同上节）：OpenAI Codex，tag `rust-v0.172.0`，[`compact.rs` 的摘要生成与按预算保留用户消息](https://github.com/openai/codex/blob/rust-v0.172.0/codex-rs/core/src/compact.rs#L399-L408)、[`build_compacted_history`](https://github.com/openai/codex/blob/rust-v0.172.0/codex-rs/core/src/compact.rs#L733-L858)；[`compact_remote_v2.rs` 的 ResponsesCompactionV2 分支](https://github.com/openai/codex/blob/rust-v0.172.0/codex-rs/core/src/compact_remote_v2.rs#L152-L174)、[`compact_remote_v2_attempt.rs` 的 compaction trigger](https://github.com/openai/codex/blob/rust-v0.172.0/codex-rs/core/src/compact_remote_v2_attempt.rs#L224-L250)。
> - **Devin CLI 会话与 Devin Memory**（“Devin CLI 与 Devin Cloud”与比较表）：Cognition，[Essential commands](https://docs.devin.ai/cli/essential-commands)（本地会话历史、云会话 URL、恢复与压缩）与 [Memory and Dreaming](https://docs.devin.ai/product-guides/memory)（`MEMORY.md` 常驻、其他笔记按需读取、会话摘要与任务状态的排除项）。
> - **Cursor Agent 的会话、Cloud Agent 与 Projects**（“Cursor Agent CLI、Cloud Agent 与 Projects”与比较表）：Cursor，[Dynamic Context Discovery](https://cursor.com/blog/dynamic-context-discovery)（工具输出文件、摘要后搜索历史文件）、[Using Agent in CLI](https://cursor.com/docs/cli/using)（`/summarize`、resume 与云端交接）、[What is a Cursor Project?](https://cursor.com/help/ai-features/projects)（跨 agent 与上下文重置的共享文件）。
