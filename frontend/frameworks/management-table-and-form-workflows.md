# 管理表格打开多步骤编辑后，怎样在查询变化与提交冲突中保住用户意图？

**案例背景。** 管理员从 `/reports?sort=oldest#summary` 打开合成报表列表。报表 42 出现在第一页；用户选择它后翻到第 2 页，再从“已选 1 项”打开编辑抽屉。详情读取到强 ETag（实体标签）`"report-42-v7"` 和一份可编辑表示。编辑器允许改通知方式和备注，后来表格筛选、分页响应可能先后变化；另一位用户也可能先保存。页面要让 Uniform Resource Locator（统一资源定位符，URL）、选择、编辑草稿和服务端版本各自有明确所有者，才能不把任何一份旧数据误当成用户最新意图。

报表 42 的合成表示为：

~~~json
{"id":42,"title":"Monthly summary","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

`delivery.channel` 与 `delivery.recipients` 是本教学变体新增的字段，数据不对应真实业务。报表 42 的 GET、条件 PATCH、强 ETag 和 `412` 行为与[HTTP API 条件更新契约](../../engineering-foundations/backend/http-api-contracts.md)一致；本文聚焦表格与编辑器怎样保留草稿。

~~~mermaid
flowchart TD
  URL[sort / filter / page 来自 URL] --> Query[查询当前页]
  Query --> Rows[用 report.id 标识行]
  Rows --> Selection[选择集合按 ID 跨页保留]
  Selection --> Open[按选中 ID GET 详情与 ETag]
  Open --> Baseline[编辑基线 + 本地草稿分开保存]
  Baseline --> Validate[联动字段与异步校验按 ID 和代次归属]
  Validate --> Patch[仅序列化已改变且当前模式有效的字段]
  Patch --> Match{If-Match 仍匹配？}
  Match -->|是| Saved[接收新表示和 ETag，刷新查询]
  Match -->|否，412| Reload[保留草稿，读取当前表示并三方比较]
  Reload --> Confirm[用户选择并确认新基线]
  Confirm --> Patch
~~~

表格查询只决定当前看到哪些行；编辑草稿以稳定资源 ID 和它自己的服务端基线为依据。若把整张表、选中行和表单值都写进同一个临时对象，一次筛选响应就可能覆盖用户正在改的输入。

## URL 查询、行选择与详情草稿怎样各自保存？

表格的 `sort`、筛选和页码可复制、刷新和由浏览器后退恢复，所以它们放在 URL。开始地址是 `/reports?sort=oldest#summary`。用户选择“已发布”后，路由写成 `/reports?sort=oldest&status=published&page=1#summary`；点“下一页”再变为 `/reports?sort=oldest&status=published&page=2#summary`。片段 `#summary` 仍是客户端定位信息，不是筛选参数。

本例的合成表格投影只有两行一页：第 1 页含 ID `17`、`42`；第 2 页含 ID `61`。主流程是在第 1 页选择 `42`、翻页后仍保留 `{42}`，再从“已选 1 项”打开编辑抽屉。另一个筛选分支里，用户把筛选从“已发布”改为“处理中”，路由重置页码并写成 `/reports?sort=oldest&status=open&page=1#summary`；页面清除原集合并告知用户，因为旧过滤条件选出的 ID 可能不属于新结果。若产品需要保留跨筛选选择，应明确将其做成独立的“已选对象”集合并在批量操作前重新校验权限，不能因隐藏行而悄悄套用旧集合。排序或页码改变不会清除当前筛选下的显式选择。

列表行以 `report.id` 而非页内下标作为稳定身份。打开编辑器后，客户端对 `/api/reports/42` 重新 GET，而不是把表格行的摘要字段直接当成完整详情。每次读取和 PATCH 都由服务端按当前身份检查对报表 42 的权限；URL 参数、已选 ID、隐藏按钮或客户端缓存都不授权访问。

编辑器收到响应后保存三份相互关联的状态：基线表示、对应的 ETag、本地草稿。后续表格排序结果或缓存刷新只更新表格查询；它不把表单重置成新的列表对象。草稿脏时关闭抽屉或切换到另一行，先让用户留下、保存或明确丢弃；重新开启报表 42 是一个新编辑会话，必须再读取当前详情和 ETag。React 的局部状态应跟随这个会话，而不是跟随“当前页第 0 行”等列表位置；只有用户明确切换资源或开始新会话时才换编辑器身份。`React` 中组件状态会随组件树的位置与 `key` 变化而保留或重置；筛选列表重渲染与编辑会话重建是两个不同事件。

## 条件字段与动态输入怎样生成有效草稿？

本例的 `email` 模式显示收件人，至少保留一个有效地址；`download` 模式隐藏收件人。草稿可以在未保存的编辑会话里暂存隐藏输入，用户切回 `email` 时仍看见它们，但提交序列化器只写当前模式允许的字段。Merge Patch（合并补丁）一般规定省略成员表示保持、`null` 表示删除；本合成接口另有领域规则：合并后若 `channel` 为 `download`，服务端规范化时移除 `recipients`，并在成功表示中不返回它。比如 `{"delivery":{"channel":"download"},"note":null}` 合并后得到不含 `recipients` 和 `note` 的规范表示。保存成功后，客户端用返回表示和新 ETag 重设基线，并从该表示重建已确认表单；此时收件人列表为空，已删除的隐藏旧值不再留在草稿中。如果随后重新切回 `email`，需要显式补充收件人，不能把服务端刚删除的旧值又提交回来。

`note` 是可选成员，详情类型用 `note?: string` 才能接收条件更新契约中删除备注后的合法 GET/200 表示。新草稿从详情复制备注；只有用户明确执行“移除备注”动作，才把草稿属性记为缺失。将它改成空字符串是另一种输入，不等同于删除。基线里有 `note`、草稿现在缺少它时，客户端发送 `note: null`；基线与草稿都没有备注时，序列化器省略该成员。服务端返回备注缺失后，后续草稿也从这个规范表示重建。

动态收件人行的内部身份与 API 中的字符串数组分开。下面的 `clientId` 在新增时分配一次，并随行移动或删除；它不是邮件地址、数据库 ID，也不会写进 API。这样 React 行键、焦点和异步校验状态不会因为数组重排而错绑到另一个地址。

> [!example]- 可选：完整补丁序列化与规范化响应重建代码
>
> ~~~typescript
> type Report42 = {
>   id: 42;
>   title: string;
>   delivery: { channel: "email" | "download"; recipients?: string[] };
>   note?: string;
> };
>
> type RecipientField = { clientId: string; value: string };
> type ReportDraft = {
>   channel: "email" | "download";
>   recipients: RecipientField[];
>   note?: string;
> };
>
> type ReportPatch = {
>   delivery?: { channel?: "email" | "download"; recipients?: string[] };
>   note?: string | null;
> };
>
> const report42: Report42 = {
>   id: 42,
>   title: "Monthly summary",
>   delivery: { channel: "email", recipients: ["reader@example.test"] },
>   note: "Draft",
> };
>
> function makePatch(baseline: Report42, draft: ReportDraft): ReportPatch {
>   const patch: ReportPatch = {};
>   const delivery: NonNullable<ReportPatch["delivery"]> = {};
>
>   if (draft.channel !== baseline.delivery.channel) delivery.channel = draft.channel;
>   if (draft.channel === "email") {
>     const recipients = draft.recipients.map(field => field.value.trim());
>     if (JSON.stringify(recipients) !== JSON.stringify(baseline.delivery.recipients ?? [])) {
>       delivery.recipients = recipients;
>     }
>   }
>   if (Object.keys(delivery).length > 0) patch.delivery = delivery;
>   if (draft.note !== baseline.note) patch.note = draft.note ?? null;
>   return patch;
> }
>
> const draft: ReportDraft = {
>   channel: "download",
>   recipients: [
>     { clientId: "recipient-1", value: "reader@example.test" },
>     { clientId: "recipient-2", value: "analyst@example.test" },
>   ],
>   note: "Draft",
> };
> const patch = makePatch(report42, draft);
> // => { delivery: { channel: "download" } }
> // 隐藏的 recipients 仍在本地草稿中，但不进入这个模式的 PATCH。
>
> const removeNoteDraft = { ...draft };
> delete removeNoteDraft.note; // 显式移除属性，区别于 note: ""
> const removeNotePatch = makePatch(report42, removeNoteDraft);
> // => { delivery: { channel: "download" }, note: null }
> // null 是 Merge Patch 的删除指令，序列化后的正文明确包含 note:null。
>
> declare function newRecipientClientId(): string;
> function draftFromReport(saved: Report42): ReportDraft {
>   return {
>     channel: saved.delivery.channel,
>     recipients: (saved.delivery.recipients ?? []).map(value => ({ clientId: newRecipientClientId(), value })),
>     ...(saved.note === undefined ? {} : { note: saved.note }),
>   };
> }
> const savedV8: Report42 = {
>   id: 42,
>   title: "Monthly summary",
>   delivery: { channel: "download" }, // 200 不含 recipients
>   // 备注已删除，200 也不含 note
> };
> const rebuiltDraft = draftFromReport(savedV8);
> // => { channel: "download", recipients: [] }；旧隐藏收件人不再存在于草稿。
> ~~~

下面三次变更展示序列化器的关键输入与结果。省略 `recipients` 只表示 Merge Patch 不直接改写此成员；`download` 的服务端规范化才在成功表示中删除它。

| 用户变更 | PATCH 正文 | 成功表示和下一份草稿 |
|---|---|---|
| v7 从 `email` 切到 `download`，备注 `Draft` 不变 | `{"delivery":{"channel":"download"}}` | 200 不含 `recipients`；以响应重建时 `recipients: []` |
| 同上，并明确移除备注 | `{"delivery":{"channel":"download"},"note":null}` | 200 不含 `recipients` 和 `note`；后续草稿也缺少备注属性 |
| 保持 `email`，新增 `analyst@example.test` | `{"delivery":{"recipients":["reader@example.test","analyst@example.test"]}}` | 数组整体替换；备注未改，不进入补丁 |

三行分别展示三个操作：下载模式只改渠道；`note:null` 表示用户明确删除；邮件模式把收件人数组整体替换。

上述函数只构造增量字段。若 `note` 没有变化，它不会被塞回补丁去覆盖另一个用户刚改过的备注；从基线中删除备注时才明确写入 `null`。若 `channel` 为 `download`，它不会将隐藏的收件人数组放进补丁；成功响应中的规范表示也不会再含旧收件人。进入 `email` 模式后，全部动态行按当前顺序序列化，服务器仍验证地址、重复项、是否至少一项和最终资源约束；客户端即时提示不能替代服务端验证。切换到 `download` 会在同一事件处理中递增并作废每个收件人的校验代次，清除当前错误并丢弃待返回 ticket；切回 `email` 时用仍在草稿中的当前值重新校验。关闭编辑会话或移除动态行也同步作废 ticket，避免隐藏字段、已关闭草稿或新会话被旧响应改写。

异步校验必须绑定编辑会话、输入身份与发起时的依赖值。例子中的 `organizationId` 是本教学校验 API 的合成依赖：同一邮箱在不同组织可能有不同可用性。为每个 `sessionId + clientId` 分配单调请求代次，并保存实际校验快照；只有会话仍打开、ticket 仍最新且快照仍与当前字段相同的响应才可以改写错误状态。不同编辑会话即使复用了同一个动态行 ID，也不会接受彼此的迟到结果。

对 `recipient-1`，服务端接收的校验结果按下列次序归属：

| 时刻 | 当前快照和代次 | UI 状态 |
|---|---|---|
| 输入 `reader@old.example.test` | `edit-A / recipient-1 / gen=1 / org-a` | 发出请求 1 |
| 输入改为 `reader@example.test` | 同步更新快照并推进到 `gen=2` | 发出请求 2；请求 1 后到时已过期 |
| 切换到 `download` | 同步推进代次、删除 ticket 与快照 | 收件人隐藏；请求 1 或 2 都不能写入错误 |
| 切回 `email` | 以当前值重新校验，创建 `gen=4` | 只接受新请求；若关掉抽屉，当前 ticket 也立即失效 |
| 重开为 `edit-B` | 键空间变为 `edit-B / recipient-1` | 即使 clientId 与邮箱相同，旧会话响应也无法命中新状态 |

校验结果为 `ok: false` 时始终显示错误；如果响应缺少或给出空 `message`，客户端用“该地址未通过校验”兜底，不能把 `undefined` 传给表示清错的 setter。

> [!example]- 可选：带编辑会话生命周期的校验 ticket 实现
>
> ~~~typescript
> type RecipientField = { clientId: string; value: string };
> type ValidationTicket = { generation: number; snapshot: string };
> const latestTicket = new Map<string, ValidationTicket>();
> const generationByField = new Map<string, number>();
> const currentSnapshotByField = new Map<string, string>();
> declare function checkRecipient(input: { value: string; organizationId: string }): Promise<{ ok: boolean; message?: string }>;
> declare function setIssue(sessionId: string, clientId: string, message: string | undefined): void;
> declare function updateDraftRecipient(sessionId: string, clientId: string, value: string): void;
> declare function updateDraftChannel(sessionId: string, channel: "email" | "download"): void;
>
> function fieldKey(sessionId: string, clientId: string) {
>   return `${sessionId}:${clientId}`; // sessionId 是每次打开编辑器新建的唯一 ID
> }
>
> function invalidateRecipientTicket(sessionId: string, clientId: string) {
>   const key = fieldKey(sessionId, clientId);
>   generationByField.set(key, (generationByField.get(key) ?? 0) + 1);
>   latestTicket.delete(key);
>   currentSnapshotByField.delete(key);
>   setIssue(sessionId, clientId, undefined);
> }
>
> function onRecipientInput(sessionId: string, field: RecipientField, nextValue: string, organizationId: string) {
>   const key = fieldKey(sessionId, field.clientId);
>   const snapshot = JSON.stringify({ value: nextValue.trim(), organizationId });
>   currentSnapshotByField.set(key, snapshot); // 同步作废旧依赖快照
>   updateDraftRecipient(sessionId, field.clientId, nextValue);
>
>   const generation = (generationByField.get(key) ?? 0) + 1;
>   generationByField.set(key, generation);
>   const ticket = { generation, snapshot };
>   latestTicket.set(key, ticket);
>   const isCurrent = () => {
>     const current = latestTicket.get(key);
>     return current?.generation === ticket.generation &&
>       current.snapshot === ticket.snapshot &&
>       currentSnapshotByField.get(key) === ticket.snapshot;
>   };
>   void checkRecipient({ value: nextValue.trim(), organizationId }).then(result => {
>     if (!isCurrent()) return;
>     setIssue(sessionId, field.clientId, result.ok ? undefined : (result.message || "该地址未通过校验"));
>   }, () => {
>     if (!isCurrent()) return;
>     setIssue(sessionId, field.clientId, "暂时无法验证；保留当前草稿");
>   });
> }
>
> function changeChannel(sessionId: string, channel: "email" | "download", fields: RecipientField[], organizationId: string) {
>   updateDraftChannel(sessionId, channel);
>   for (const field of fields) {
>     if (channel === "download") invalidateRecipientTicket(sessionId, field.clientId);
>     else onRecipientInput(sessionId, field, field.value, organizationId);
>   }
> }
>
> function closeEditSession(sessionId: string, fields: RecipientField[]) {
>   for (const field of fields) invalidateRecipientTicket(sessionId, field.clientId);
> }
>
> function removeRecipient(sessionId: string, field: RecipientField) {
>   invalidateRecipientTicket(sessionId, field.clientId);
>   // 然后从该会话草稿移除此行。
> }
> ~~~

以 `recipient-1` 为例，用户先输入 `reader@old.example.test` 并发出第 1 次请求，接着同步改成 `reader@example.test` 并发出第 2 次请求。若第 1 次响应先于第 2 次响应返回，输入处理器已经把快照改为新值，旧响应不能再改写错误；若第 2 次先返回“可用”，再晚到的第 1 次响应仍被新代次挡住。`organizationId` 等其它依赖改变时也调用同一个输入处理函数，即使邮箱文本没变。若此时从 `email` 切到 `download`，`changeChannel` 在发出下一次响应前同步递增代次并删除 ticket；旧 Promise 返回时 `latestTicket.get(key)` 已为空，不能把错误写回隐藏输入。切回 `email` 时当前字段值重新发起校验。移除字段或关闭抽屉同样使 ticket 失效；关闭后重开使用新的 `sessionId`，即使复用了 `clientId` 也不会让旧响应命中新会话。校验服务暂时失败时保留草稿并显示“暂时无法验证”，不能把网络失败说成字段有效。

## 服务器版本改变时怎样处理 `412`？

GET 已读取强 ETag `"report-42-v7"`。用户将备注改为“Send after review”，并在 `email` 模式添加 `analyst@example.test`。提交使用原始基线的 `If-Match`；版本检查与更新由服务器在同一个原子操作中完成：

~~~http
PATCH /api/reports/42 HTTP/1.1
Content-Type: application/merge-patch+json
If-Match: "report-42-v7"

{"delivery":{"recipients":["reader@example.test","analyst@example.test"]},"note":"Send after review"}
~~~

这里的 `412` 是一条重新从 v7 开始的冲突分支。上一节的 `savedV8` 是“切到下载并保存成功”分支；本段的 v8 则是另一位用户在冲突分支里提交的表示，两者不是同一次连续编辑。

假如另一位用户先保存，把当前资源推进到 `"report-42-v8"` 并将备注写成“Reviewed”，上述旧条件不会覆盖它。服务返回 `412 Precondition Failed` 和 Problem Details；至少包含 `type`、`title`、`status`。客户端不能自动重发同一补丁，也不能把当前 `ETag` 静默换成 v8 后再提交。

这时编辑器仍保留原基线 v7、完整的本地草稿和每个字段的校验状态。它重新 GET 当前表示与 ETag v8，再按字段比较三份值：

| 字段 | v7 基线 | 本地草稿 | v8 当前值 | 展示给用户的差异 |
|---|---|---|---|---|
| `title` | `Monthly summary` | `Monthly summary` | `Monthly summary — May` | 只有服务端改过，可采用当前值 |
| `delivery.recipients` | `[reader@example.test]` | `[reader@example.test, analyst@example.test]` | `[reader@example.test]` | 只有本地改过，可在重新确认后保留本地增量 |
| `note` | `Draft` | `Send after review` | `Reviewed` | 两边都改过，要求用户选择或再次编辑 |

若用户确认采用服务端标题、保留本地新增收件人并把备注设为 `Reviewed; send after review`，客户端用 v8 作为新基线重新计算一个最小补丁，展示差异后才提交 `If-Match: "report-42-v8"`。成功时服务器返回新的表示和新强 ETag；本例递增到 `"report-42-v9"`。如果本地意图是移除备注，三方比较会把“属性缺失”与空字符串、服务端当前值分别显示；用户确认删除后仍将 `note: null` 作为补丁语义提交。若合并或提交之间又发生修改，新的 `412` 再次保留草稿并按相同过程处理。冲突界面解决的是“用户想提交什么”，不是让客户端猜测某个版本理应胜出。

成功响应替换详情缓存中的已确认表示和 ETag，再刷新受影响的列表查询。服务端可能因此把报表移出当前筛选页，或改变其排序位置；不能为了让乐观 UI 看起来稳定而在旧页保留已不符合筛选的数据。独立路由中的编辑表单也使用同一基线、草稿、异步校验和条件提交生命周期；它不依赖从表格入口打开。

**延伸阅读：**[React 如何维护服务端数据与乐观更新](./react-server-state-and-optimistic-updates.md)说明列表查询身份与缓存更新；[React 路由如何把地址映射到界面并恢复前进后退](./react-routing-and-navigation.md)说明查询 URL 的导航状态；[语义化 HTML 表单如何支持键盘与辅助技术用户](../html-css/accessible-html-forms.md)说明字段错误与焦点。条件 PATCH 和授权的服务端边界见[HTTP API 契约](../../engineering-foundations/backend/http-api-contracts.md)。

> [!info]- 来源
> - **表格行身份与 React 编辑状态生命周期：** [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 官方文档，核对日期 2026-11-09。
> - **URL、查询参数与历史状态：** [WHATWG HTML: History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，[WHATWG URL: URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)；并参见[浏览器怎样让筛选状态跟随地址栏与前进后退](../browser/browser-navigation-and-history.md)。
> - **强 ETag、`If-Match`、原子条件更新、`412` 与合并补丁：** [HTTP API 条件更新契约](../../engineering-foundations/backend/http-api-contracts.md)；具体协议由其所引 RFC 核验。本篇的字段和版本是冻结的合成示例。
> - **表单校验与错误提示的用户界面边界：** [语义化 HTML 表单怎样支持键盘与辅助技术用户](../html-css/accessible-html-forms.md)。校验响应代次与草稿隔离是本文根据该合成流程明确的客户端所有权。
