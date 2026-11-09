# 一轮 AI 聊天怎样安全地展示增量回答、工具状态与恢复操作？

**案例背景。** 开发者要求：“解释 build 42 的失败并准备缺陷单；提交前让我审核。”运行服务已鉴权并创建 `run-r42-7`。只读工具 `read_build_log` 的调用标识是 `c1`；它查到 `unit-tests` 中 `reject_empty_name` 预期 Hypertext Transfer Protocol（超文本传输协议，HTTP）`400`、实际 HTTP `200`、进程退出状态为 `1`。拿到这项证据前，界面只能显示正在检查，不能先把根因写成结论。随后运行生成解释和待审核的缺陷单草稿，进入 `awaiting_approval`；审核人批准仍未变化的草稿后，同一运行才会调用创建工单动作。`runId` 标识持久运行，事件 `seq` 表示本应用日志顺序，`c1` 配对模型工具请求与结果；它们不是连接 ID，也不能互相替代。案例中的 ID、构建资料和工单均为合成教学数据。

本篇从[流式传输已经交付哪些完整事件](streaming-ux.md)之后开始：客户端已经解出一条完整的 JavaScript Object Notation（JavaScript 对象表示法，JSON）应用事件，接下来要验证它属于哪次运行、只应用一次，并把未完成的 Markdown 与工具结果当作不可信内容安全呈现。运行状态、审批和副作用的权威恢复记录仍由[AI 运行如何断线恢复并避免副作用重复](../../ai-engineering/systems/ai-application-architecture.md)负责；聊天组件不能凭最后看到的一帧推断服务端状态。

~~~mermaid
flowchart TD
  Snapshot[读取完整投影与同一游标] --> Events[接收完整事件]
  Events --> Identity{runId 与 seq 有效？}
  Identity -->|旧序号| Ignore[忽略重放]
  Identity -->|序号跳跃| Catchup[同一 run 补读历史]
  Identity -->|下一序号| Reduce[更新同一条消息或工具卡]
  Reduce --> Safe[Markdown 全文解析后消毒；工具摘要按文本呈现]
  Safe --> View[显示内容、运行态与连接态]
  View --> Approval{已有证据和待审草稿？}
  Approval -->|否| ReadOnly[继续读取并准备草稿]
  Approval -->|是| Awaiting[awaiting_approval：展示绑定的草稿]
  Awaiting -->|批准未变化草稿| Resume[同一 run 恢复写入]
  Resume -->|结果未知| Reconcile[原操作键对账]
  Reconcile -->|确认 ISSUE-842 已创建| Attach[更新原 c2 卡片与原 run]
  Attach --> Done[权威结果确认后 completed]
  View --> Action{停止或新一轮尝试}
  Action -->|停止| Cancel[请求取消并查询权威状态]
  Action -->|重试| NewRun[确认旧写未发生且不会迟到后才创建]
~~~

图中补读、恢复、取消和对账都是原运行的服务端动作；单纯重连只恢复事件交付。下表把 `run-r42-7` 的应用事件投影到稳定的界面项目。`seq` 是此合成应用协议的字段，不是 MCP 的 JSON-RPC ID，也不是任何传输标准自动提供的字段。`c2` 是本例第二个模型工具调用的合成标识，绑定创建缺陷单动作；远端操作键另为 `run-r42-7:create-issue:v1`。

| 事件 | 客户端投影 | 身份与更新规则 |
|---|---|---|
| `seq=1, run.status=running` | 同一轮回答显示“正在检查” | 仅更新 `run-r42-7` 的运行状态 |
| `seq=2, assistant.delta` | 助手气泡显示“正在读取 build 42 日志” | 还没有失败证据，不能先陈述根因 |
| `seq=3, tool.started, toolCallId=c1` | 创建“读取构建日志”卡片并显示等待 | 卡片键使用 `(runId, toolCallId)`，重放时更新原卡片 |
| `seq=4, tool.completed, toolCallId=c1` | 将卡片标为“只读结果已返回”，展示失败测试摘要 | 结果必须配回 `c1`；正文是数据，不是可执行指令 |
| `seq=5, assistant.delta` | 同一气泡解释 `reject_empty_name` 实际返回 HTTP 200，并告知正在准备缺陷单草稿 | 证据已到达，草稿仍在运行中生成 |
| `seq=6, run.status=awaiting_approval` | 同一事件携带持久草稿投影，显示仓库、标题、正文、证据摘要和审核按钮 | `payloadHash` 标识这份精确动作摘要；此时尚未创建工单 |
| `seq=7, run.status=running` | 用户批准后，同一轮恢复执行并显示“正在提交已审核草稿” | 运行 ID 不变，事件游标继续递增 |
| `seq=8, tool.started, toolCallId=c2` | 创建“创建缺陷单”卡片 | `c2` 配对工具请求；远端操作键为 `run-r42-7:create-issue:v1` |
| `seq=9, tool.effect_unknown, toolCallId=c2` | 卡片显示“提交结果待对账” | 超时不能显示失败或触发盲重发；原操作可能已创建工单 |
| `seq=10, run.status=effect_unknown` | 运行显示“外部结果待确认” | 运行账本保留原键、请求摘要和待对账状态 |
| `seq=11, tool.completed, toolCallId=c2` | 同一张卡片显示对账得到的 `ISSUE-842` | 原操作键结果已确认，不创建第二个 run 或工单 |
| `seq=12, assistant.delta` | 同一气泡告知工单 `ISSUE-842` 已存在 | 只追加本轮文本，工单结果继续配回 `c2` |
| `seq=13, run.status=completed` | 显示已完成并停止等待更多事件 | 只有权威副作用记录确认结果后才进入终态 |

## 怎样应用重放事件而不重复消息或工具卡？

重新打开对话时，先从服务端读取 `run-r42-7` 的权威投影快照及其游标，再订阅后续事件。快照里的 `lastSeq` 和此前已应用的文本、工具卡片、运行状态必须来自同一版本。事件必须通过边界校验：`runId` 必须匹配；`seq` 是安全整数；事件类型和必需字段属于允许集合；工具事件有非空 `toolCallId`。事件顺序使用一个客户端游标：重复序号不再追加，下一序号正常推进，出现缺口则先补读。下面将这三个分支写成投影函数。

> [!example]- 代码：按运行与事件游标更新聊天投影
> ~~~typescript
> type RunEvent = {
>   runId: string;
>   seq: number;
>   type: "assistant.delta" | "tool.started" | "tool.effect_unknown" | "tool.completed" | "run.status";
>   toolCallId?: string;
>   toolName?: string;
>   text?: string;
>   status?: "running" | "awaiting_approval" | "effect_unknown" | "completed" | "failed" | "rejected" | "cancel_requested" | "canceled";
>   summary?: string;
>   approvalDraft?: ApprovalDraftView;
> };
>
> type ApprovalDraftView = {
>   repositoryId: string;
>   title: string;
>   body: string;
>   evidenceSummary: string;
>   payloadHash: string;
> };
>
> type Projection = {
>   runId: string;
>   lastSeq: number;
>   assistantText: string;
>   tools: Map<string, { name: string; status: "running" | "effect_unknown" | "completed"; summary?: string }>;
>   runStatus: string;
>   approvalDraft?: ApprovalDraftView;
> };
>
> function applyEvent(view: Projection, event: RunEvent): Projection | "catch-up" | "ignore" {
>   if (event.runId !== view.runId || !Number.isSafeInteger(event.seq) || event.seq < 1) {
>     throw new Error("Invalid run event identity");
>   }
>   if (event.seq <= view.lastSeq) return "ignore"; // 同一日志游标的重放不能再次追加
>   if (event.seq !== view.lastSeq + 1) return "catch-up"; // 不跳过缺失的增量
>
>   const next = { ...view, lastSeq: event.seq, tools: new Map(view.tools) };
>   if (event.type === "assistant.delta") {
>     if (typeof event.text !== "string") throw new Error("Invalid text delta");
>     next.assistantText += event.text;
>   } else if (event.type === "tool.started") {
>     if (!event.toolCallId || !event.toolName) throw new Error("Missing tool identity");
>     const prior = next.tools.get(event.toolCallId);
>     next.tools.set(event.toolCallId, prior ?? { name: event.toolName, status: "running" });
>   } else if (event.type === "tool.effect_unknown") {
>     if (!event.toolCallId) throw new Error("Missing toolCallId");
>     const prior = next.tools.get(event.toolCallId);
>     if (!prior) throw new Error("Unknown tool operation");
>     next.tools.set(event.toolCallId, { ...prior, status: "effect_unknown" });
>   } else if (event.type === "tool.completed") {
>     if (!event.toolCallId || typeof event.summary !== "string") {
>       throw new Error("Invalid tool result");
>     }
>     const prior = next.tools.get(event.toolCallId);
>     if (!prior) throw new Error("Tool result has no matching request");
>     next.tools.set(event.toolCallId, { ...prior, status: "completed", summary: event.summary });
>   } else if (event.type === "run.status") {
>     if (typeof event.status !== "string") throw new Error("Invalid run status");
>     next.runStatus = event.status;
>     if (event.status === "awaiting_approval") {
>       if (!event.approvalDraft) throw new Error("Missing persisted approval draft projection");
>       next.approvalDraft = event.approvalDraft;
>     }
>   }
>   return next;
> }
>
> // 服务端在游标 3 生成快照时，必须一起提供此前的文本和 c1 卡片。
> const snapshotAt3: Projection = {
>   runId: "run-r42-7",
>   lastSeq: 3,
>   assistantText: "正在读取 build 42 日志",
>   tools: new Map([["c1", { name: "read_build_log", status: "running" as const }]]),
>   runStatus: "running",
> };
> const after4 = applyEvent(snapshotAt3, {
>   runId: "run-r42-7", seq: 4, type: "tool.completed", toolCallId: "c1",
>   summary: "reject_empty_name: expected HTTP 400, actual HTTP 200, exit 1",
> });
> if (after4 === "catch-up" || after4 === "ignore") throw new Error("Expected c1 card update");
> ~~~

此投影器假定上游已把不可信 JSON 解析为 `unknown` 并检查字段；TypeScript 类型声明不会验证网络数据。真实应用的 schema（结构模式）还应约束工具名称、状态转换和文本大小。事件序号重复时不再追加文本；遇到跳号先向同一个运行补读历史或重新取得权威快照，不能把之后的增量接到缺失内容上。恢复快照必须把 `lastSeq` 和该游标之前的**完整可见投影**作为同一一致版本：示例 `lastSeq=3` 快照含 `seq=2` 的助手文本和状态为 `running` 的 `c1` 卡片，因此 `seq=4` 可以更新已存在的卡片。若只恢复 `runStatus` 与 `lastSeq`，下一条 `tool.completed(c1)` 会找不到卡片；如果服务只能给状态与最新位置，客户端须从已有本地投影位置重放，或从可重放起点补齐，不能跳到服务端最新序号。序号绑定的是本客户端可见的应用事件流。本例每个 run 只创建一个助手气泡，所以以 `runId` 作为气泡 key 足够；若一个 run 会生成多条助手消息，事件与持久记录还需提供稳定 `messageId`，key 才能用 `(runId, messageId)`。工具卡片的 Document Object Model（文档对象模型，DOM）key 使用稳定的 `(runId, toolCallId)`，不要按数组下标或每次渲染时的随机值生成，否则一次重连可能重建卡片、丢失展开状态或重复宣告结果。`c1` 是模型工具调用 ID；若工具来自 Model Context Protocol（模型上下文协议，MCP），其 JSON-RPC 请求 ID 仍是另一层相关标识。

断线时保留最后一条可用文本和卡片，并把连接标为“正在恢复”。重新打开处于 `awaiting_approval` 的运行时，权威快照或可重放的 `run.status` 事件还要携带服务端已保存的审批草稿投影：目标仓库、标题、正文、证据摘要和 `payloadHash`。运行记录中的 `payload_hash` 映射为这个客户端字段；它绑定精确动作内容。按钮提交 `runId` 与该 hash，而不让客户端重组待写入 payload；服务端在接收批准时重新核对当前保存的摘要和权限，任一变化就让旧批准失效并要求重新审核。hash 不替代身份、授权或批准。只有运行 API 报告的状态决定它是否仍在运行或已终止：EOF、浏览器关闭连接、收到一个完成样式的文本片段，都不足以证明 `completed`。普通问答和受审批控制的工具运行共用这个投影层，但运行控制权仍归服务端。

## 不完整 Markdown 和工具结果怎样安全显示？

流中的 Markdown 可能跨多个事件结束。下面的三项是准确的 JavaScript 字符串；分片边界不插入任何字符，片段 2 以 `java` 结束，片段 3 以 `script:` 开始：

~~~typescript
const chunks = [
  "日志显示为：\n\n```text\n<not executed>\n",
  "```\n\n[打开链接](java",
  "script:alert(1))",
];
let accumulated = "";
const frames: string[] = [];
for (const chunk of chunks) {
  accumulated += chunk; // 不在分片之间添加空格或换行
  frames.push(accumulated); // 每帧都把完整文本交给后文的 safeMarkdown
}
~~~

不要用正则表达式拼一个“增量 HTML 解析器”，也不要把片段直接拼进 `innerHTML`。数组第一项含未闭合代码围栏，第二项关闭围栏并开始链接目标，第三项直接接上 `script:`，所以累计 Markdown 中确实有危险 URI `javascript:alert(1)`，不是换行导致的无效链接。每次都从同一助手消息的完整累计 Markdown 重新解析，再在 HyperText Markup Language（超文本标记语言，HTML）注入点前消毒；代码围栏与链接在各个中间帧都按同一安全路径处理。验证时先检查 Marked 18.1.3 的未净化输出含完整 `href="javascript:alert(1)"`，再确认 DOMPurify 输出已移除该 href；仅检查最终 DOM 不足以证明测试真的生成过危险目标。

~~~tsx
import { marked } from "marked";
import DOMPurify from "dompurify";

const chatPolicy = {
  USE_PROFILES: { html: true },
  // 只保留 HTTPS/HTTP、站内根路径和片段链接；不允许图片远程加载。
  ALLOWED_URI_REGEXP: /^(?:https?:\/\/|\/(?!\/)|#)/i,
  FORBID_TAGS: ["img", "style", "iframe", "audio", "video"],
  FORBID_ATTR: ["target", "style"],
};

function safeMarkdown(source: string): string {
  const generated = marked.parse(source, { async: false });
  if (typeof generated !== "string") throw new Error("Unexpected async Markdown parser");
  return DOMPurify.sanitize(generated, chatPolicy);
}

function AssistantMessage({ text }: { text: string }) {
  const html = safeMarkdown(text); // 每次更新对完整消息重解析并消毒
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}
~~~

这里的 `marked` 只负责把 Markdown 变成 HTML；它不负责净化结果。`DOMPurify` 在受控的 HTML sink 前运行，并对 URI 使用窄白名单。消毒后不能再把内容交给会改写 DOM 的高亮器或插件；若之后确有改写，必须在最终写入前重新消毒。示例使用 Marked 18.1.3 和 DOMPurify 3.4.17；若不需要富文本，直接把字符串放进 React 文本子节点或 DOM `textContent` 更简单。此示例将外部图片、样式和新窗口链接排除；这些能力只有在产品需要且有独立策略时才应加入。

工具输出也不是可信 HTML。对 `c1` 的只读结果，只把已检查的 `step`、`failed_test`、`expected`、`actual` 和 `exit_status` 映射为文本节点；例如 `summary.textContent = tool.summary`。若需要渲染 Markdown，同样完整解析、消毒后再显示。卡片上的“运行中”“已返回”“失败”等标签来自允许的运行事件；内容渲染本身不执行工具，不把模型的工具请求当成浏览器命令，也不以显示一个成功样式图标代替服务端结果。

## 停止、继续和重试分别改变什么？

用户操作应同时显示所针对的运行和操作结果。连接重连是传输行为；停止是发给运行服务的控制请求；继续和重试则有不同的运行身份：

| 操作 | 客户端动作 | `runId` 与已有文本 | 何时可安全呈现 |
|---|---|---|---|
| 重连 | 按最后已应用序号重新读取同一次运行 | 仍为 `run-r42-7`；忽略旧 `seq`、补齐缺口 | 断线不取消后台运行，也不清空部分回答 |
| 停止 | 对当前运行发送已鉴权的取消请求，然后查询运行状态 | 仍为 `run-r42-7`；保留部分文本并显示“取消请求处理中” | 收到服务端 `canceled` 才显示已取消；若动作结果仍未知，继续显示待确认 |
| 继续 | 用户审批当前未变的待审批草稿，提交给恢复端点 | 同一个 `run-r42-7`；运行序号继续向前 | 草稿摘要或权限变化会使旧审批失效，须重新确认；写入结果未知时仍沿同一 run 对账 |
| 重试 | 只有权威确认旧写入未发生且不会迟到后，用户仍要求尝试，才提交新请求 | 新意图创建新的 `runId` 和事件序号；旧消息保留 | 若原操作已成功，把原工单显示在原 `c2` 卡片并结束原 run；若结果仍未知，不创建同效的新 run |

`AbortController.abort()` 或关闭 SSE/Fetch reader 只停止当前连接的读取，不证明服务端已停止生成或工具已取消。停止按钮若发送取消请求，事件仍可能晚到；界面可以保留它们，但要以服务端最终状态更新标记。审批继续只唤醒原有已持久化运行和操作摘要，不重新提交初始问题；权限、目标或草稿改变时再次确认。`run-r42-7` 的审批通过后按稳定操作键 `run-r42-7:create-issue:v1` 创建工单。若远端超时，原 `c2` 卡片保持待对账；对账确认 `ISSUE-842` 已创建时，把该 ID 与最终文本写回原 run，再显示完成，不能通过新 run 再做同一效果。只有服务权威确认旧写未提交且不会迟到，才允许用户以新 `runId` 再试。此边界沿用[工具请求怎样成为一次获准的应用操作](../../ai-engineering/agents/tool-design-and-function-calling.md)与[运行服务的副作用恢复契约](../../ai-engineering/systems/ai-application-architecture.md)。

> [!info]- 来源
> - **聊天所消费的运行状态、同一 run 的审批恢复、取消与结果未知：** [AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复](../../ai-engineering/systems/ai-application-architecture.md)；本文是其客户端投影，不重写持久化运行协议。
> - **工具 ID 与结果的关联、模型请求不是执行许可：** [应用怎样设计并执行模型提出的工具请求](../../ai-engineering/agents/tool-design-and-function-calling.md)。`runId + seq` 是本应用事件合同；不是 MCP JSON-RPC 或模型 API 的通用帧格式。
> - **Marked 的同步 parse API、异步选项与不负责净化输出：** [Marked 18.1.3 README](https://github.com/markedjs/marked/blob/v18.1.3/README.md)、[高级用法与 options](https://github.com/markedjs/marked/blob/v18.1.3/docs/USING_ADVANCED.md) 和 [package metadata](https://github.com/markedjs/marked/blob/v18.1.3/package.json)；[DOMPurify 3.4.17 README](https://github.com/cure53/DOMPurify/tree/3.4.17)。在 Node.js 26.13.0 下实际运行跨片段恶意链接与代码围栏样例；核对日期 2026-11-09。Marked 18 要求 Node.js 20 或更新版本。
> - **动态 HTML 是独立安全边界，工具文字可由 DOM 文本接口显示：** [WHATWG DOM：`textContent`](https://dom.spec.whatwg.org/#dom-node-textcontent) 与 [DOMPurify：Security Goals & Threat Model](https://github.com/cure53/DOMPurify/wiki/Security-Goals-&-Threat-Model)，核对日期 2026-11-09。
