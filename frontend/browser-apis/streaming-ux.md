# 流式报表断线重连后，界面怎样保留正确状态？

案例背景：用户重开 `/reports/42?sort=recent#summary`。页面从服务端取到报表 42 的状态快照，再订阅进度；断线后浏览器会自动重连，但同一事件可能重放，页面也可能比服务端落后。界面需要分清传输游标、业务状态版本和报表终态。

本文沿用 [实时更新该选哪种传输？](../../engineering-foundations/networking/real-time-web-updates.md) 中的 Server-sent Events (服务器发送事件，SSE) 案例：初始快照为 `id=42, version=9, status=running, event_cursor=103`。这里快照 JSON 的 `id=42` 是报表资源标识；后续 SSE 事件行的 `id: 104` 才是日志续读游标；`version=9` 是报表状态的单调修订号；`status` 描述业务运行状态。这三者职责不同，不能相互比较。

## 页面要显示两种状态

服务端报表状态回答“报表现在是什么结果”；本地连接状态回答“页面是否正在接收更新”。连接短暂重连时，已有的报表快照仍然有用，但应标出更新正在恢复，而不把它误报成失败。

| 服务端报表状态 | 页面连接状态 | 可以显示什么 |
|---|---|---|
| `running` | 已连接 | 当前状态与最近一次进度；结果仍未完成 |
| `running` | 正在重连 | 保留最后可用状态并标注可能过时 |
| `ready` | 任意 | 已完成；停止进度订阅 |
| `failed` 或 `canceled` | 任意 | 显示服务端记录的终态；断线本身不能生成这种业务结论 |

`EventSource` 收到 `error` 时可能仍会自动重连，因此不能直接把报表标成 `failed`。当报表状态是 `ready`、`failed` 或 `canceled` 等终态时，页面可关闭事件源；产品应由 API 合同明确哪些状态终止这项工作。

~~~mermaid
flowchart TD
    Snapshot[读取报表快照和对应游标] --> Open[建立 SSE 连接]
    Open --> Wait[等待当前连接的下一事件]
    Wait --> Event{收到更新事件？}
    Event -->|没有新事件| Wait
    Event -->|版本较旧或重复| Wait
    Event -->|新版本| Apply[合并状态并更新界面]
    Apply --> Terminal{业务状态已终止？}
    Terminal -->|否| Wait
    Terminal -->|是| Close[关闭订阅]
    Wait -->|连接丢失| Reconnect[保留快照并显示重连中]
    Reconnect --> Resume[浏览器用原 EventSource 自动重连]
    Resume --> Wait
    Reconnect -->|游标过期 reset| Refresh[关闭旧连接并重新读取快照和游标]
    Refresh --> SnapshotTerminal{新快照是否仍在运行？}
    SnapshotTerminal -->|是| Open
    SnapshotTerminal -->|否| Close
~~~

## 怎样合并状态并从游标恢复？

第一次订阅必须接在与快照一致的位置之后。若快照版本 9 已涵盖事件日志游标 103，页面从 103 之后订阅；不能分别读取一个随时变化的快照和另一个独立游标，否则两者之间的更新可能被跳过。初连 URL 中的 `after` 是应用约定，原生 `EventSource` 不能让页面设置任意请求头。

服务器接着发出日志事件 104、105：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

接收端按 `version` 合并业务状态，按 SSE 的 `id` 续读事件。版本不大于本地版本时忽略重复或旧消息；更高版本才更新界面。本例事件包含该视图所需的最新状态。如果 API 发送的是依赖前序版本的增量补丁，发现版本不连续时应重新 GET 快照，而不能把缺少的字段猜出来。

~~~javascript
const initialSnapshot = { id: 42, version: 9, status: "running", progress: 0, event_cursor: "103" };
let report = {
  id: initialSnapshot.id,
  version: initialSnapshot.version,
  status: initialSnapshot.status,
  progress: initialSnapshot.progress,
};
let source;
let recoveryInProgress = false;
let recoveryAttempts = 0;
const reportStatuses = new Set(["running", "ready", "failed", "canceled"]);
const terminalStatuses = new Set(["ready", "failed", "canceled"]);

function subscribe(eventCursor) {
  const currentSource = new EventSource(`/api/reports/42/events?after=${encodeURIComponent(eventCursor)}`);
  source = currentSource;
  currentSource.addEventListener("open", () => {
    if (source === currentSource) showConnectionState("connected");
  });
  currentSource.addEventListener("report.updated", event => {
    if (source !== currentSource) return;
    let update;
    try {
      update = JSON.parse(event.data);
    } catch {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
      return;
    }
    if (!update || update.report_id !== report.id ||
        !Number.isSafeInteger(update.version) ||
        !reportStatuses.has(update.status) || !Number.isFinite(update.progress) ||
        update.progress < 0 || update.progress > 100) {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
      return;
    }
    // 合法的旧版本或重放帧不是坏数据；保留这条连接继续等待。
    if (update.version <= report.version) return;
    recoveryAttempts = 0;
    // EventSource 用 SSE id 续读；业务状态只按 report.version 合并。
    report = { ...report, version: update.version, status: update.status, progress: update.progress };
    renderReport(report);
    if (terminalStatuses.has(report.status)) closeCurrentSource(currentSource);
  });
  currentSource.addEventListener("reset", () => {
    if (source !== currentSource || terminalStatuses.has(report.status)) return;
    closeCurrentSource(currentSource);
    void refreshSnapshotAndSubscribe();
  });
  currentSource.addEventListener("error", () => {
    if (source !== currentSource || terminalStatuses.has(report.status)) return;
    if (currentSource.readyState === EventSource.CONNECTING) {
      showConnectionState("reconnecting");
    } else if (currentSource.readyState === EventSource.CLOSED) {
      closeCurrentSource(currentSource);
      void refreshSnapshotAndSubscribe();
    }
  });
}

function closeCurrentSource(currentSource) {
  if (source !== currentSource) return;
  source = undefined;
  currentSource.close();
}

async function refreshSnapshotAndSubscribe() {
  if (recoveryInProgress) return;
  if (recoveryAttempts >= 1) {
    showRefreshUnavailable();
    return;
  }
  recoveryAttempts += 1;
  recoveryInProgress = true;
  source?.close();
  source = undefined;
  try {
    const response = await fetch("/api/reports/42");
    if (!response.ok) throw new Error("Snapshot request failed");
    const snapshot = await response.json();
    if (snapshot.id !== report.id || !Number.isSafeInteger(snapshot.version) ||
        snapshot.version < report.version || !reportStatuses.has(snapshot.status) ||
        !Number.isFinite(snapshot.progress) || snapshot.progress < 0 || snapshot.progress > 100 ||
        typeof snapshot.event_cursor !== "string") {
      throw new Error("Invalid or older snapshot");
    }
    report = {
      id: snapshot.id,
      version: snapshot.version,
      status: snapshot.status,
      progress: snapshot.progress,
    };
    renderReport(report);
    if (!terminalStatuses.has(report.status)) subscribe(snapshot.event_cursor);
  } catch {
    // Keep the last usable report and show one bounded recovery error.
    showRefreshUnavailable();
  } finally {
    recoveryInProgress = false;
  }
}

subscribe(initialSnapshot.event_cursor);
~~~

初连请求为 `GET /api/reports/42/events?after=103`。当连接读到事件 104 后断开，浏览器重连仍访问同一 URL（包括 `?after=103`），并附带 `Last-Event-ID: 104`；本例的服务端合同规定，有效的 `Last-Event-ID` 优先于初始查询参数，因此从 104 之后续读事件 105。若本地已合并到仍在运行的版本 10，再收到版本 10 时会直接忽略，并让同一 EventSource 继续等待；版本 11 已是 `ready`，接受后就关闭订阅。`event_cursor` 只存在于初始或重新取得的快照中，不是自动变化的本地状态。`Last-Event-ID` 表示浏览器已解析到该事件位置，不表示应用监听器已经完成渲染、写入本地库或执行外部副作用。只关心最新报表状态时，按 `version` 去重并在恢复后读取权威快照足够；若每条业务事件都必须处理，则另需持久记录已处理 ID、去重和显式确认。

游标过期时，服务器可发送含 `data` 并以空行结束的 `event: reset`，浏览器才会派发事件。页面关闭旧 EventSource，重新 GET 一致快照和游标；版本较旧或数据无效时保留原显示并提示一次恢复失败，只有新快照仍为 `running` 才用新游标订阅。若快照已是 `ready`、`failed` 或 `canceled`，展示它并保持连接关闭。`EventSource` 的 `error` 若状态为 `CONNECTING`，表示浏览器仍在重连；若为 `CLOSED`，示例转为一次快照恢复。连续 reset、坏帧或立即关闭最多自动恢复一次；接收更高业务版本后才重置这个预算，避免反复重取或重连。恢复失败后显示错误。

## Fetch 自定义流和 SSE 有什么不同？

若 API 需要自定义请求头或 POST 查询，再考虑 Fetch 响应流。`reader.read()` 给出的是任意字节块，不保证一个块刚好是一条记录；UTF-8 字符和 JSON 记录都可能跨块。需要自己持续解码、缓冲到完整分隔符、校验字段和终止条件。传输方式比较见上述实时更新说明；本节聚焦界面和 parser (解析器) 的责任。

旧例还保留了一个自定义 newline-delimited JSON (按行分隔的 JSON，NDJSON) 作业协议模型。它与前面的 SSE 报表协议不同：模型中的 `runId` 标识一次生成作业，`seq` 是该私有日志的应用游标；它既不是 SSE 的 `id`，也不是报表 `version`。客户端用幂等键提交作业并获得稳定 `runId`，续读时带已接受的 `seq`；旧序号可重放并丢弃，跳号则拒绝，作业最终状态仍以状态接口为准。该模型限制单条帧为 8,192 个 UTF-16 代码单元、可见输出为 64 Ki 代码单元，并覆盖坏 JSON、提早 EOF、超时和本地取消；EOF 本身不等于收到终态。以下折叠段保留协议示例与可执行模型，供确实采用自定义 NDJSON API 的场景参考。

> [!example]- 自定义 Fetch/NDJSON 作业 parser 与断线案例
> 此实现是 Node Web Streams 与 Response API 上的合成协议模型，不是浏览器端到端或生产服务测试；八组断言覆盖 UTF-8 与帧跨块、合并帧、服务端错误、格式错误、提前结束、断线、超时、本地中止及渲染回调返回后阻止消费已缓冲的终态。
>
> ~~~text
> POST /api/runs
> Idempotency-Key: submit-7f2a
> {"prompt":"Summarize the public release notes"}
>
> 202 Accepted
> {"runId":"run-7f2a","status":"queued"}
>
> GET /api/runs/run-7f2a/events?after=0
> Content-Type: application/x-ndjson
>
> {"type":"delta","seq":1,"text":"The release adds "}
> {"type":"delta","seq":2,"text":"a search filter."}
> {"type":"complete","seq":3,"runId":"run-7f2a"}
> ~~~
>
> 这个小协议展示提交幂等键、稳定作业 ID、续读序号与明确终态；它是应用契约示例，不是浏览器标准。下面的 parser 会逐块解码并验证序号，遇到没有终态的 EOF 时保留部分文本但不标为完成。
>
> ~~~javascript
> import assert from "node:assert/strict";
>
> const MAX_FRAME_CHARS = 8 * 1024;
> const MAX_OUTPUT_CHARS = 64 * 1024;
> const DECODE_SLICE_BYTES = 4 * 1024;
>
> function readWithSignal(reader, signal) {
>   if (!signal) return reader.read();
>   const abortReason = () => signal.reason ?? new DOMException("Aborted", "AbortError");
>   if (signal.aborted) return Promise.reject(abortReason());
>
>   return new Promise((resolve, reject) => {
>     const onAbort = () => reject(abortReason());
>     signal.addEventListener("abort", onAbort, { once: true });
>     reader.read().then(resolve, reject).finally(() => {
>       signal.removeEventListener("abort", onAbort);
>     });
>   });
> }
>
> async function consumeRun(response, {
>   runId,
>   signal,
>   afterSequence = 0,
>   currentOutputChars = 0,
>   onState = () => {},
>   onText = async () => {},
> } = {}) {
>   let state = "idle";
>   let sequence = afterSequence;
>   let outputChars = currentOutputChars;
>   let carry = "";
>   let terminal = false;
>   let errorCode;
>   let detail;
>   let reader;
>   const decoder = new TextDecoder("utf-8", { fatal: true });
>
>   const transition = next => {
>     const allowed = {
>       idle: ["connecting", "canceled"],
>       connecting: ["streaming", "completed", "failed", "canceled"],
>       streaming: ["connecting", "completed", "failed", "canceled"],
>     };
>     if (state === next) return;
>     if (!allowed[state]?.includes(next)) {
>       throw new Error("Invalid view-state transition: " + state + " -> " + next);
>     }
>     state = next;
>     onState(state);
>   };
>
>   const result = () => ({ state, sequence, outputChars, errorCode, detail });
>
>   async function acceptLine(line) {
>     signal?.throwIfAborted();
>     if (terminal) throw new Error("Frame received after a terminal frame");
>     if (!line) throw new Error("Empty frame");
>     if (line.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
>
>     let event;
>     try {
>       event = JSON.parse(line);
>     } catch {
>       throw new Error("Malformed JSON frame");
>     }
>
>     if (!event || Array.isArray(event) || typeof event !== "object") {
>       throw new Error("Frame must be a JSON object");
>     }
>     if (!Number.isSafeInteger(event.seq) || event.seq < 1) {
>       throw new Error("Frame has an invalid sequence number");
>     }
>     if (event.seq <= sequence) return; // replayed event already applied
>     if (event.seq !== sequence + 1) throw new Error("Event sequence gap");
>     if (typeof event.type !== "string") throw new Error("Frame has no event type");
>
>     if (event.type === "delta") {
>       if (typeof event.text !== "string") throw new Error("Delta text must be a string");
>       if (outputChars + event.text.length > MAX_OUTPUT_CHARS) {
>         throw new Error("Output exceeds the display limit");
>       }
>       if (state === "connecting") transition("streaming");
>       await onText(event.text, signal);
>       // onText 成功返回表示这一整帧已经应用；这才是可续读的位置。
>       sequence = event.seq;
>       outputChars += event.text.length;
>       signal?.throwIfAborted();
>       return;
>     }
>
>     if (event.type === "complete") {
>       if (event.runId !== runId) throw new Error("Terminal frame has the wrong runId");
>       sequence = event.seq;
>       terminal = true;
>       transition("completed");
>       return;
>     }
>
>     if (event.type === "error") {
>       if (typeof event.code !== "string" || !event.code) {
>         throw new Error("Error frame has no error code");
>       }
>       sequence = event.seq;
>       errorCode = event.code;
>       terminal = true;
>       transition("failed");
>       return;
>     }
>
>     throw new Error("Unknown event type");
>   }
>
>   async function feedText(text) {
>     carry += text;
>     let newline;
>     while ((newline = carry.indexOf("\n")) !== -1) {
>       let line = carry.slice(0, newline);
>       carry = carry.slice(newline + 1);
>       if (line.endsWith("\r")) line = line.slice(0, -1);
>       await acceptLine(line);
>       if (terminal) return;
>     }
>     if (carry.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
>   }
>
>   transition("connecting");
>   try {
>     if (!response.body) throw new Error("Response has no body");
>     reader = response.body.getReader();
>     if (!response.ok) throw new Error("HTTP " + response.status);
>     if (!response.headers.get("content-type")?.toLowerCase().includes("application/x-ndjson")) {
>       throw new Error("Unexpected response content type");
>     }
>
>     while (true) {
>       const { done, value } = await readWithSignal(reader, signal);
>       if (done) {
>         await feedText(decoder.decode());
>         if (terminal) return result();
>         if (carry.length) throw new Error("EOF inside an unterminated frame");
>         throw new Error("EOF before a terminal frame");
>       }
>
>       for (let offset = 0; offset < value.byteLength; offset += DECODE_SLICE_BYTES) {
>         const part = value.subarray(offset, offset + DECODE_SLICE_BYTES);
>         await feedText(decoder.decode(part, { stream: true }));
>         if (terminal) return result();
>       }
>     }
>   } catch (error) {
>     detail = error instanceof Error ? error.message : String(error);
>     if (signal?.aborted && signal.reason?.name === "TimeoutError") {
>       transition("failed");
>     } else if (signal?.aborted) {
>       transition("canceled");
>     } else {
>       transition("failed");
>     }
>     return result();
>   } finally {
>     if (reader) {
>       try {
>         await reader.cancel();
>       } catch {
>         // Preserve the parse, read, timeout, or abort result.
>       }
>       reader.releaseLock();
>     }
>   }
> }
>
> const encoder = new TextEncoder();
> const asBytes = text => encoder.encode(text);
>
> function responseFrom(chunks, { open = false, status = 200 } = {}) {
>   const body = new ReadableStream({
>     start(controller) {
>       for (const chunk of chunks) controller.enqueue(chunk);
>       if (!open) controller.close();
>     },
>   });
>   return new Response(body, {
>     status,
>     headers: { "content-type": "application/x-ndjson; charset=utf-8" },
>   });
> }
>
> function responseDisconnectAfter(chunk) {
>   let sent = false;
>   const body = new ReadableStream({
>     pull(controller) {
>       if (!sent) {
>         sent = true;
>         controller.enqueue(chunk);
>       } else {
>         controller.error(new Error("Connection dropped"));
>       }
>     },
>   }, { highWaterMark: 0 });
>   return new Response(body, {
>     headers: { "content-type": "application/x-ndjson; charset=utf-8" },
>   });
> }
>
> async function check(name, response, expectedState, expectedText = "", options = {}) {
>   const states = [];
>   let text = "";
>   const result = await consumeRun(response, {
>     runId: "run-7",
>     ...options,
>     onState: state => states.push(state),
>     onText: chunk => { text += chunk; },
>   });
>   assert.equal(result.state, expectedState, name);
>   assert.equal(text, expectedText, name + " partial text");
>   return { result, states };
> }
>
> // Split one multibyte character and one record across reads; the final read
> // also contains a coalesced complete record.
> const multibyte = asBytes("好");
> const normal = await check(
>   "split UTF-8 and coalesced frames",
>   responseFrom([
>     asBytes('{"type":"delta","seq":1,"text":"你'),
>     multibyte.slice(0, 1),
>     multibyte.slice(1),
>     asBytes('"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
>   ]),
>   "completed",
>   "你好",
> );
> assert.deepEqual(normal.states, ["connecting", "streaming", "completed"]);
> console.log("PASS normal, multibyte split, frame split, and coalesced frames");
>
> const serverError = await check(
>   "server error frame",
>   responseFrom([asBytes('{"type":"error","seq":1,"code":"MODEL_UNAVAILABLE"}\n')]),
>   "failed",
> );
> assert.equal(serverError.result.errorCode, "MODEL_UNAVAILABLE");
> console.log("PASS terminal server-error frame");
>
> const malformed = await check(
>   "malformed JSON",
>   responseFrom([asBytes("{not-"), asBytes("json}\n")]),
>   "failed",
> );
> assert.match(malformed.result.detail, /Malformed JSON/);
> console.log("PASS malformed frame split across reads");
>
> const prematureEof = await check(
>   "premature EOF",
>   responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')]),
>   "failed",
>   "partial",
> );
> assert.match(prematureEof.result.detail, /EOF before a terminal frame/);
> console.log("PASS EOF preserves partial text but does not complete");
>
> const disconnected = await check(
>   "abrupt disconnect",
>   responseDisconnectAfter(asBytes('{"type":"delta","seq":1,"text":"partial"}\n')),
>   "failed",
>   "partial",
> );
> assert.match(disconnected.result.detail, /Connection dropped/);
> console.log("PASS abrupt disconnect preserves partial text but does not complete");
>
> const timeoutController = new AbortController();
> const timeoutTimer = setTimeout(() => {
>   timeoutController.abort(new DOMException("Deadline exceeded", "TimeoutError"));
> }, 5);
> const timeout = await check(
>   "timeout",
>   responseFrom([], { open: true }),
>   "failed",
>   "",
>   { signal: timeoutController.signal },
> );
> clearTimeout(timeoutTimer);
> assert.match(timeout.result.detail, /Deadline exceeded/);
> console.log("PASS timeout remains a failure, not completion");
>
> const stopController = new AbortController();
> const stopTimer = setTimeout(() => {
>   stopController.abort(new DOMException("Stopped by user", "AbortError"));
> }, 5);
> const stopped = await check(
>   "explicit abort after partial text",
>   responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')], { open: true }),
>   "canceled",
>   "partial",
>   { signal: stopController.signal },
> );
> clearTimeout(stopTimer);
> assert.match(stopped.result.detail, /Stopped by user/);
> console.log("PASS explicit abort keeps partial text and marks only the local view canceled");
>
> const bufferedRaceController = new AbortController();
> const bufferedRaceStates = [];
> let bufferedRaceText = "";
> const bufferedRace = await consumeRun(responseFrom([
>   asBytes('{"type":"delta","seq":1,"text":"partial"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
> ]), {
>   runId: "run-7",
>   signal: bufferedRaceController.signal,
>   onState: state => bufferedRaceStates.push(state),
>   onText: async chunk => {
>     bufferedRaceText += chunk;
>     await Promise.resolve();
>     bufferedRaceController.abort(new DOMException("Stopped while rendering", "AbortError"));
>   },
> });
> assert.equal(bufferedRace.state, "canceled");
> assert.equal(bufferedRace.sequence, 1);
> assert.equal(bufferedRace.outputChars, "partial".length);
> assert.equal(bufferedRaceText, "partial");
> assert.deepEqual(bufferedRaceStates, ["connecting", "streaming", "canceled"]);
> assert.match(bufferedRace.detail, /Stopped while rendering/);
> console.log("PASS abort after text callback returns prevents a buffered terminal frame");
> ~~~

本地 `AbortController.abort()` 或取消 reader 只会结束当前页面对响应体的读取，不证明服务端工作停止。若产品允许取消作业，还要发取消请求并查询权威作业状态，直到服务端报告终态。`onText` 成功返回表示整帧文本已完整接收并应用，只有此后才推进 `sequence` 和输出长度；回调若先应用部分文本再拒绝，就无法安全确定续读点。解析器在等待 `onText` 时不能强行打断任意 Promise，回调必须有界并自行响应传入的取消信号，或让其完成后再处理中止。示例的竞争测试仅证明渲染回调返回后，中止会阻止消费同一缓冲区里的终态帧。解析器等待回调完成也形成背压：若回调将 DOM 写入排入队列，应在队列保持较小时再读取下一块；可以用 `requestAnimationFrame` 合并可见更新，但它不提供恢复保证。路由卸载时释放 reader 和事件源，保留有用但不完整的文本，并将其标为部分结果。将收到的状态先交给本地 reducer 或事件总线再更新多个视图时，监听器重入也可能改变处理顺序；见[事件总线重入案例](./event-bus-and-observer-patterns.md)。

渲染本身也应有界：把同一帧中到达的文本增量合并后每帧更新一次，而不是每个 token 都刷新 DOM；输出很长时限制缓冲或只渲染可见窗口。状态区域使用 `role="status"` 与 `aria-live="polite"` 可播报连接、完成或失败，但不要逐字播报每个 token。

**延伸阅读：** [实时更新该选哪种传输？](../../engineering-foundations/networking/real-time-web-updates.md) 定义 SSE 的线格式、id/version 和重连边界；[API 可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) 讨论未知结果与安全重试；[JavaScript 事件总线在监听器中重入时怎样保持顺序？](./event-bus-and-observer-patterns.md) 讨论把一个状态更新送到本地多个模块。

若应用交付的是持久 AI run 的完整事件，本篇负责传输解码、断线续读与本地取消边界；事件到达后如何把 `runId`、序号、工具调用与不完整 Markdown 安全地投影到聊天界面，见[一轮 AI 聊天怎样安全展示增量回答、工具状态与恢复操作](./streaming-ai-chat.md)。

> [!info]- 来源
> - SSE 字段解析、EventSource 自动重连和 `Last-Event-ID`：[WHATWG HTML Standard，Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，2026-11-06 核对；报表 42 的 `id`、`version` 和终态沿用[实时更新协议案例](../../engineering-foundations/networking/real-time-web-updates.md)。
> - Fetch 响应体与 keepalive、流读取、reader 取消：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)；[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，2026-11-06 核对。
> - 增量 UTF-8 解码：[WHATWG Encoding Standard，TextDecoder](https://encoding.spec.whatwg.org/#interface-textdecoder)，2026-11-06 核对。
> - `AbortController` 和 `AbortSignal` 的 API 语义：[WHATWG DOM Standard](https://dom.spec.whatwg.org/#interface-abortcontroller)，2026-11-06 核对。
> - `role="status"` 的状态播报语义：[W3C WAI-ARIA 1.2，status role](https://www.w3.org/TR/wai-aria-1.2/#status)，2026-11-06 核对。
