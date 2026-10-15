# Streaming UX / 流式交互

**Core explanation / 核心解释：** A stream is an incremental view of a server operation, not a promise that the operation finished. The interface should preserve useful partial text, decode and frame bytes incrementally, bound pending work, and make completion depend on an explicit terminal event. Stopping the browser reader ends the local view; server cancellation needs its own request and authoritative acknowledgement. / 流是服务器操作的增量视图，不代表操作已经完成。界面应保留可用的部分文本，增量解码和组帧，限制待处理工作，并只在收到明确终态事件后显示完成。停止浏览器读取只会结束本地视图；取消服务端任务需要单独请求和权威确认。

**Key terms / 关键术语：** incremental decoding / 增量解码；frame / 帧；partial output / 部分输出；terminal event / 终态事件；backpressure / 背压；teardown / 清理；resume cursor / 恢复游标.

## State belongs in the interaction / 交互需要明确状态

Keep the view's state separate from the server's run state. A useful browser lifecycle is:

| View state | Meaning and behavior |
|---|---|
| idle / 空闲 | No request is active. |
| connecting / 连接中 | Submitting, opening the event response, or making an allowed resume request. |
| streaming / 接收中 | At least one validated progress or text frame has arrived. Keep showing it as partial. |
| completed / 已完成 | A valid complete frame for this runId arrived. This is the only streamed success path. |
| failed / 失败 | The server sent a terminal error, the protocol was malformed, or the bounded recovery policy ended. Keep usable partial text and show whether the run's final state is still unknown. |
| canceled / 已停止 | The user stopped this view or the route was torn down. The run may still be queued or running unless the server confirms cancellation. |

The server's durable run record can still say queued, running, cancel_requested, completed, failed, or canceled. A browser failed transport and a server failed run are different facts; query status before presenting one as the other. See [AI Application Architecture / AI应用架构](../../ai-engineering/systems/ai-application-architecture.md) for stable run IDs, authoritative state, idempotent submission, and cancellation races.

## A small application protocol / 简洁的应用协议

This example uses Fetch to read newline-delimited JSON records. It is a synthetic application contract; it does not add another transport or redefine SSE. POST /api/runs accepts an Idempotency-Key and returns 202 with a stable runId. The client then reads GET /api/runs/{runId}/events?after=12. Each event is one UTF-8 JSON object followed by LF (CRLF is also accepted); records carry a monotonically increasing seq. A delta adds partial text, while complete or error is terminal. The server can replay older sequence numbers around reconnect races; the client drops duplicates and treats a gap as a failed stream. GET /api/runs/{runId} remains the authority for status.

~~~text
POST /api/runs
Idempotency-Key: submit-7f2a
{"prompt":"Summarize the public release notes"}

202 Accepted
{"runId":"run-7f2a","status":"queued"}

GET /api/runs/run-7f2a/events?after=0
Content-Type: application/x-ndjson

{"type":"delta","seq":1,"text":"The release adds "}
{"type":"delta","seq":2,"text":"a search filter."}
{"type":"complete","seq":3,"runId":"run-7f2a"}
~~~

The complete frame is the success boundary for this example. EOF before a terminal frame is an incomplete response, even when it follows valid text. A terminal error preserves earlier deltas as partial output. A timeout or disconnect may be retried only within the contract: for example, at most two event reconnections during a short deadline, using the same runId and last accepted seq. Never create a replacement run merely because the event request failed. If the cursor expired or the run is still active after the retry budget, query current status and explain that the visible text is partial.

The HTTP body yields byte chunks. A read can split inside UTF-8 characters, inside one JSON record, or between records; one read can also contain several records. TextDecoder with stream mode carries an incomplete multibyte sequence into the next decode call. The parser below independently buffers until LF and therefore does not mistake a transport chunk for a record. It caps each frame and its incomplete line buffer at 8,192 UTF-16 code units (the units counted by JavaScript `String.length`), not 8 KiB of encoded bytes, and total displayed text at 64 Ki UTF-16 code units. These are example product limits, not browser or protocol defaults.

## Executable protocol model / 可执行协议模型

The following standalone snippet uses Node's Web Streams and Response APIs to exercise the parser and interaction states. It is a protocol model, not a test in a real browser and not proof of any production server behavior. The parser awaits onText; a browser can use that point to batch updates on requestAnimationFrame and pause reading while a small render queue drains.

~~~javascript
import assert from "node:assert/strict";

const MAX_FRAME_CHARS = 8 * 1024;
const MAX_OUTPUT_CHARS = 64 * 1024;
const DECODE_SLICE_BYTES = 4 * 1024;

function readWithSignal(reader, signal) {
  if (!signal) return reader.read();
  const abortReason = () => signal.reason ?? new DOMException("Aborted", "AbortError");
  if (signal.aborted) return Promise.reject(abortReason());

  return new Promise((resolve, reject) => {
    const onAbort = () => reject(abortReason());
    signal.addEventListener("abort", onAbort, { once: true });
    reader.read().then(resolve, reject).finally(() => {
      signal.removeEventListener("abort", onAbort);
    });
  });
}

async function consumeRun(response, {
  runId,
  signal,
  afterSequence = 0,
  currentOutputChars = 0,
  onState = () => {},
  onText = async () => {},
} = {}) {
  let state = "idle";
  let sequence = afterSequence;
  let outputChars = currentOutputChars;
  let carry = "";
  let terminal = false;
  let errorCode;
  let detail;
  let reader;
  const decoder = new TextDecoder("utf-8", { fatal: true });

  const transition = next => {
    const allowed = {
      idle: ["connecting", "canceled"],
      connecting: ["streaming", "completed", "failed", "canceled"],
      streaming: ["connecting", "completed", "failed", "canceled"],
    };
    if (state === next) return;
    if (!allowed[state]?.includes(next)) {
      throw new Error("Invalid view-state transition: " + state + " -> " + next);
    }
    state = next;
    onState(state);
  };

  const result = () => ({ state, sequence, outputChars, errorCode, detail });

  async function acceptLine(line) {
    signal?.throwIfAborted();
    if (terminal) throw new Error("Frame received after a terminal frame");
    if (!line) throw new Error("Empty frame");
    if (line.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");

    let event;
    try {
      event = JSON.parse(line);
    } catch {
      throw new Error("Malformed JSON frame");
    }

    if (!event || Array.isArray(event) || typeof event !== "object") {
      throw new Error("Frame must be a JSON object");
    }
    if (!Number.isSafeInteger(event.seq) || event.seq < 1) {
      throw new Error("Frame has an invalid sequence number");
    }
    if (event.seq <= sequence) return; // replayed event already applied
    if (event.seq !== sequence + 1) throw new Error("Event sequence gap");
    if (typeof event.type !== "string") throw new Error("Frame has no event type");

    if (event.type === "delta") {
      if (typeof event.text !== "string") throw new Error("Delta text must be a string");
      if (outputChars + event.text.length > MAX_OUTPUT_CHARS) {
        throw new Error("Output exceeds the display limit");
      }
      sequence = event.seq;
      outputChars += event.text.length;
      if (state === "connecting") transition("streaming");
      await onText(event.text);
      signal?.throwIfAborted();
      return;
    }

    if (event.type === "complete") {
      if (event.runId !== runId) throw new Error("Terminal frame has the wrong runId");
      sequence = event.seq;
      terminal = true;
      transition("completed");
      return;
    }

    if (event.type === "error") {
      if (typeof event.code !== "string" || !event.code) {
        throw new Error("Error frame has no error code");
      }
      sequence = event.seq;
      errorCode = event.code;
      terminal = true;
      transition("failed");
      return;
    }

    throw new Error("Unknown event type");
  }

  async function feedText(text) {
    carry += text;
    let newline;
    while ((newline = carry.indexOf("\n")) !== -1) {
      let line = carry.slice(0, newline);
      carry = carry.slice(newline + 1);
      if (line.endsWith("\r")) line = line.slice(0, -1);
      await acceptLine(line);
      if (terminal) return;
    }
    if (carry.length > MAX_FRAME_CHARS) throw new Error("Frame exceeds the size limit");
  }

  transition("connecting");
  try {
    if (!response.body) throw new Error("Response has no body");
    reader = response.body.getReader();
    if (!response.ok) throw new Error("HTTP " + response.status);
    if (!response.headers.get("content-type")?.toLowerCase().includes("application/x-ndjson")) {
      throw new Error("Unexpected response content type");
    }

    while (true) {
      const { done, value } = await readWithSignal(reader, signal);
      if (done) {
        await feedText(decoder.decode());
        if (terminal) return result();
        if (carry.length) throw new Error("EOF inside an unterminated frame");
        throw new Error("EOF before a terminal frame");
      }

      for (let offset = 0; offset < value.byteLength; offset += DECODE_SLICE_BYTES) {
        const part = value.subarray(offset, offset + DECODE_SLICE_BYTES);
        await feedText(decoder.decode(part, { stream: true }));
        if (terminal) return result();
      }
    }
  } catch (error) {
    detail = error instanceof Error ? error.message : String(error);
    if (signal?.aborted && signal.reason?.name === "TimeoutError") {
      transition("failed");
    } else if (signal?.aborted) {
      transition("canceled");
    } else {
      transition("failed");
    }
    return result();
  } finally {
    if (reader) {
      try {
        await reader.cancel();
      } catch {
        // Preserve the parse, read, timeout, or abort result.
      }
      reader.releaseLock();
    }
  }
}

const encoder = new TextEncoder();
const asBytes = text => encoder.encode(text);

function responseFrom(chunks, { open = false, status = 200 } = {}) {
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
      if (!open) controller.close();
    },
  });
  return new Response(body, {
    status,
    headers: { "content-type": "application/x-ndjson; charset=utf-8" },
  });
}

function responseDisconnectAfter(chunk) {
  let sent = false;
  const body = new ReadableStream({
    pull(controller) {
      if (!sent) {
        sent = true;
        controller.enqueue(chunk);
      } else {
        controller.error(new Error("Connection dropped"));
      }
    },
  }, { highWaterMark: 0 });
  return new Response(body, {
    headers: { "content-type": "application/x-ndjson; charset=utf-8" },
  });
}

async function check(name, response, expectedState, expectedText = "", options = {}) {
  const states = [];
  let text = "";
  const result = await consumeRun(response, {
    runId: "run-7",
    ...options,
    onState: state => states.push(state),
    onText: chunk => { text += chunk; },
  });
  assert.equal(result.state, expectedState, name);
  assert.equal(text, expectedText, name + " partial text");
  return { result, states };
}

// Split one multibyte character and one record across reads; the final read
// also contains a coalesced complete record.
const multibyte = asBytes("好");
const normal = await check(
  "split UTF-8 and coalesced frames",
  responseFrom([
    asBytes('{"type":"delta","seq":1,"text":"你'),
    multibyte.slice(0, 1),
    multibyte.slice(1),
    asBytes('"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
  ]),
  "completed",
  "你好",
);
assert.deepEqual(normal.states, ["connecting", "streaming", "completed"]);
console.log("PASS normal, multibyte split, frame split, and coalesced frames");

const serverError = await check(
  "server error frame",
  responseFrom([asBytes('{"type":"error","seq":1,"code":"MODEL_UNAVAILABLE"}\n')]),
  "failed",
);
assert.equal(serverError.result.errorCode, "MODEL_UNAVAILABLE");
console.log("PASS terminal server-error frame");

const malformed = await check(
  "malformed JSON",
  responseFrom([asBytes("{not-"), asBytes("json}\n")]),
  "failed",
);
assert.match(malformed.result.detail, /Malformed JSON/);
console.log("PASS malformed frame split across reads");

const prematureEof = await check(
  "premature EOF",
  responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')]),
  "failed",
  "partial",
);
assert.match(prematureEof.result.detail, /EOF before a terminal frame/);
console.log("PASS EOF preserves partial text but does not complete");

const disconnected = await check(
  "abrupt disconnect",
  responseDisconnectAfter(asBytes('{"type":"delta","seq":1,"text":"partial"}\n')),
  "failed",
  "partial",
);
assert.match(disconnected.result.detail, /Connection dropped/);
console.log("PASS abrupt disconnect preserves partial text but does not complete");

const timeoutController = new AbortController();
const timeoutTimer = setTimeout(() => {
  timeoutController.abort(new DOMException("Deadline exceeded", "TimeoutError"));
}, 5);
const timeout = await check(
  "timeout",
  responseFrom([], { open: true }),
  "failed",
  "",
  { signal: timeoutController.signal },
);
clearTimeout(timeoutTimer);
assert.match(timeout.result.detail, /Deadline exceeded/);
console.log("PASS timeout remains a failure, not completion");

const stopController = new AbortController();
const stopTimer = setTimeout(() => {
  stopController.abort(new DOMException("Stopped by user", "AbortError"));
}, 5);
const stopped = await check(
  "explicit abort after partial text",
  responseFrom([asBytes('{"type":"delta","seq":1,"text":"partial"}\n')], { open: true }),
  "canceled",
  "partial",
  { signal: stopController.signal },
);
clearTimeout(stopTimer);
assert.match(stopped.result.detail, /Stopped by user/);
console.log("PASS explicit abort keeps partial text and marks only the local view canceled");

const bufferedRaceController = new AbortController();
const bufferedRaceStates = [];
let bufferedRaceText = "";
const bufferedRace = await consumeRun(responseFrom([
  asBytes('{"type":"delta","seq":1,"text":"partial"}\n{"type":"complete","seq":2,"runId":"run-7"}\n'),
]), {
  runId: "run-7",
  signal: bufferedRaceController.signal,
  onState: state => bufferedRaceStates.push(state),
  onText: async chunk => {
    bufferedRaceText += chunk;
    await Promise.resolve();
    bufferedRaceController.abort(new DOMException("Stopped while rendering", "AbortError"));
  },
});
assert.equal(bufferedRace.state, "canceled");
assert.equal(bufferedRace.sequence, 1);
assert.equal(bufferedRace.outputChars, "partial".length);
assert.equal(bufferedRaceText, "partial");
assert.deepEqual(bufferedRaceStates, ["connecting", "streaming", "canceled"]);
assert.match(bufferedRace.detail, /Stopped while rendering/);
console.log("PASS abort during awaited text handling prevents a buffered complete frame");
~~~

For a browser, create one AbortController for the active event request and pass its signal to Fetch. The stop button and route cleanup should abort that request and release its reader. If the product also wants to stop server work, send POST /api/runs/{runId}/cancel and keep showing a pending cancellation until GET /api/runs/{runId} reports a terminal state. AbortController.abort() and reader.cancel() affect the local fetch/body consumption; neither proves the worker stopped.

Keep render work bounded as well as network buffering. Accumulate adjacent delta text and update the output once per animation frame rather than rerendering the component for every token. Cap the pending render string; because the parser awaits onText, it can pause its next read while the UI drains that small queue. The sample also caps the full visible answer. A larger product can persist output by run and render a bounded window instead of keeping an ever-growing DOM.

Leave partial output visible when it remains useful, but label it as incomplete and avoid actions that require a finished result. Expose a concise state message in a dedicated status region, for example a native element with role=status and aria-live=polite. Announce connection, completion, failure, or stop transitions and perhaps occasional long-running progress; do not announce every token. See [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](../html-css/html-and-css-basics.md) for native controls and status semantics.

**Representative answer / 代表性回答：** I treat streamed output as framed bytes that may arrive in arbitrary chunks. The client incrementally decodes UTF-8, validates sequence numbers, keeps partial text, and displays completion only after a valid terminal event. It batches rendering, bounds memory and retries, and tears down the local reader on stop or route change. A client abort does not prove the server run stopped, so I query the run record or request cancellation separately. / 我会把流式输出视为可能以任意分块到达的带帧字节。客户端增量解码 UTF-8、校验序号、保留部分文本，并且只在收到有效终态事件后显示完成。界面合并渲染、限制内存和重试次数，并在用户停止或路由卸载时清理本地读取器。客户端中止不能证明服务端运行已停止，因此还要查询运行记录或单独请求取消。

## Related notes / 相关笔记

- [HTTP Protocols and WebSockets / HTTP协议与WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) owns transport selection, SSE framing, EventSource limits, and Fetch stream boundaries.
- [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../../engineering-foundations/reliability/api-reliability-and-async-delivery.md) explains deadlines, cancellation, retry safety, and unknown outcomes.
- [AI Application Architecture / AI应用架构](../../ai-engineering/systems/ai-application-architecture.md) owns run identity, durable state, checkpoints, side effects, and server cancellation.

**Sources checked 2026-10-15 / 来源核对日期：** The [WHATWG Streams Standard](https://streams.spec.whatwg.org/) defines readable-stream readers and local consumer cancellation; the [DOM Standard's AbortController](https://dom.spec.whatwg.org/#interface-abortcontroller) defines signaling abort to an API that accepts an AbortSignal, and [AbortSignal.throwIfAborted()](https://dom.spec.whatwg.org/#dom-abortsignal-throwifaborted) provides checkpoints between asynchronous operations; the [WHATWG Encoding Standard](https://encoding.spec.whatwg.org/) defines streaming UTF-8 decode behavior. The [WHATWG Server-sent Events section](https://html.spec.whatwg.org/multipage/server-sent-events.html) defines EventSource reconnection and event IDs; this note's parser instead exercises its explicitly synthetic newline-delimited JSON application contract. Browser behavior was not tested here.
