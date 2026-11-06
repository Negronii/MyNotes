# How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？

**核心解释 / Core explanation：** A stream moves data in chunks from a producer to a consumer. A `Readable` supplies chunks; a `Writable` accepts them; a `Transform` reads and writes while changing them; a `Duplex` does both. When `writable.write(chunk)` returns `false`, stop producing until `'drain'` says writing can resume. `pipeline()` connects stages and propagates a slow consumer's backpressure upstream.

**中文说明：** 流按数据块从生产者流向消费者；`write()` 返回 `false` 时，生产者应暂停并等待 `'drain'` 再继续。`pipeline()` 会把下游变慢的背压传回上游。`highWaterMark` 是暂停阈值而非内存上限；单个大数据块、各阶段缓冲和链路外队列仍可能增加内存。读取端的 `'end'` 表示输入结束，写入端的 `'finish'` 表示 `end()` 后已处理已接收写入；`'close'` 表示资源关闭，`'error'` 表示失败。`destroy()` 用于中止或失败，额外拥有的游标等资源应在 `finally` 中释放；写入完成也不代表远端应用已处理数据或文件已持久化。

**Key terms / 关键术语：** Readable / 可读流；Writable / 可写流；Transform / 转换流；backpressure / 背压；highWaterMark / 暂停阈值；pipeline / 流水线。

~~~mermaid
flowchart TD
    Source[Readable source] --> Transform[Transform stages]
    Transform --> Sink[Writable destination]
    Sink -->|write returns false| Pause[Pause the producer]
    Pause -->|drain| Sink
    Pause -->|pipeline propagates backpressure| Transform
~~~

**面试简答 / Interview answer：** If `write()` returns `false`, stop calling it until `'drain'`; continuing to submit chunks can grow the writable's queue and memory use. Use `pipeline()` for a source/transform/destination chain, or wait for `'drain'` in a manual producer. `highWaterMark` is a pause threshold, not a hard memory cap; a large chunk, transform buffers, or queues outside the pipeline can still use more memory.

~~~javascript
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createGzip } = require('node:zlib');

async function* rows() {
  for (let id = 1; id <= 10_000; id++) yield { id };
}

async function exportRows(signal) {
  const lines = (async function* () {
    for await (const row of rows()) yield `${JSON.stringify(row)}\n`;
  })();

  await pipeline(
    Readable.from(lines),
    createGzip(),
    createWriteStream('rows.ndjson.gz', { highWaterMark: 32 * 1024 }),
    { signal }
  );
}

const controller = new AbortController();
// The owner can call controller.abort(reason) to cancel the export.
exportRows(controller.signal).catch((error) => {
  console.error('export failed:', error.message);
});
~~~

Here the async generator produces one row at a time, and `pipeline()` resolves after the output finishes. If a stage errors or the signal aborts, the promise rejects and the pipeline destroys its participating streams. A producer that owns an extra resource, such as a database cursor, should release it in `finally`; pipeline cleanup cannot close resources hidden outside its stages. For manual writes, the same rule is `if (!writable.write(chunk)) await once(writable, 'drain')`.

The terminal signals describe different outcomes: a readable `'end'` means no more input chunks remain; a writable `'finish'` means its accepted writes have completed after `end()`; `'close'` reports resource closure when that stream emits it; `'error'` reports failure. Use `destroy(error)` to abort or fail a stream, not as a synonym for successful end-of-input. A writable finishing does not prove that a remote application processed the bytes or that a file is durable on storage.


**Sources / 来源：** The stream example and lifecycle behavior were checked against the version-pinned [Node.js v26.11.1 stream documentation](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html) on 2026-10-15. This version boundary matters for code and API behavior; the conceptual backpressure rule is not a memory cap.

**Related notes / 相关笔记：** [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md) applies the same bounded-work rule to requests, worker slots, and durable queues.
