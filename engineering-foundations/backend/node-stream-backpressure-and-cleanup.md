# Node.js 流如何传播背压？

**案例：** 已接受的报表 job 由 worker 顺序读取账户活动，转换成 CSV 并写入私有对象存储。若对象上传比查询慢，生产者不能继续把所有行堆在内存中。Node stream（流）用数据块和 backpressure（背压）协调快慢不同的阶段；取消整条管线时，还要清理管线之外由生产者持有的游标。

~~~mermaid
flowchart TD
    Source[Readable：按需读取报表行] --> Transform[Transform：CSV 编码与可选压缩]
    Transform --> Sink[Writable：私有对象上传；本地例用文件]
    Sink -->|write 返回 false| Pause[暂停生产者]
    Pause -->|drain| Sink
    Pause -->|pipeline 传递背压| Source
~~~

图中 false 的反馈若只停在 Writable，生产者仍会继续堆数据；pipeline() 会把下游变慢的状态沿这条流链路传回上游。

## 什么状态表示写入方该等一等？

Readable（可读流）提供数据块；Writable（可写流）接收数据块；Transform（转换流）一边读取一边转换；Duplex（双工流）同时可读可写。只有 writable 仍处于可写、未结束且未销毁状态时，手动调用 writable.write(chunk) 返回 false 才表示当前块已被接收、内部缓冲达到 highWaterMark 阈值；这时先停止继续写，等 drain 后再恢复。若写入已结束、流已销毁或遇到错误，false 不能证明数据已接收，且不会保证再有 drain；应处理 error/close 并结束这条管线。

在正常可写状态下，返回 true 表示当前仍可继续写入；返回 false 表示应暂停，待 drain 后再继续。

highWaterMark（缓冲阈值）是何时降低读取速度的门槛，不是内存硬上限。`Readable.from()` 默认 `objectMode: true`，此时阈值按数据块个数而非字节数计；本例产出字符串，因此显式关闭 object mode。`32 KiB` 只设置本地文件 sink 的阈值，压缩流、源流、较大单块和管线外队列仍有各自缓冲。真正的背压要求生产端能暂停，且每一层都把“下游暂时消化不了”传回源。

## 如何让一条报表流自然限速并释放游标？

用 pipeline() 连接可读、转换和写入阶段。下面的生成器一次只产生一行；当可写 sink 变慢时，pipeline() 会传递背压。中止信号会销毁参与管线的流并让 Promise 以 AbortError 拒绝；数据库游标不属于这些流，仍须由生成器的 finally 关闭。

~~~javascript
// 保存为 export-report.cjs；使用 Node.js v26.11.1 运行
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createGzip } = require('node:zlib');

function openReportCursor(accountId) {
  const rows = [
    { id: 'event-1', accountId, amount: 12 },
    { id: 'event-2', accountId, amount: 8 },
    { id: 'event-3', accountId, amount: -2 },
  ];
  let index = 0;
  let closed = false;
  return {
    async next() {
      if (index === rows.length) return null;
      return rows[index++];
    },
    async close() {
      closed = true;
      console.log('cursor closed:', closed);
    },
  };
}

async function* reportRows(signal) {
  const cursor = openReportCursor('acct-17');
  try {
    while (!signal.aborted) {
      const row = await cursor.next();
      signal.throwIfAborted();
      if (row === null) return;
      yield row;
    }
  } finally {
    await cursor.close();
  }
}

function csvCell(value) {
  const text = String(value);
  return /[",\r\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
}

async function* csvRows(signal) {
  yield 'id,accountId,amount\n';
  for await (const row of reportRows(signal)) {
    yield [row.id, row.accountId, row.amount].map(csvCell).join(',') + '\n';
  }
}

async function exportReport(signal) {
  await pipeline(
    Readable.from(csvRows(signal), { objectMode: false }),
    createGzip(),
    createWriteStream('report.csv.gz', { highWaterMark: 32 * 1024 }),
    { signal },
  );
}

const controller = new AbortController();
exportReport(controller.signal).catch(error => {
  console.error('export failed:', error.message);
});
// 生命周期拥有者可在截止时间到达时调用：
// controller.abort(new Error('report deadline'));
~~~

本机用 Node.js v26.11.1 重放这段合成游标程序：它输出 cursor closed: true，并生成可解压的 `.csv.gz` 文件，内有一行表头和 3 条 CSV 记录。这只验证本地文件 sink 的流量传递与合成游标清理，不代表测试过真实数据库驱动或对象上传，也没有验证取消正在执行的数据库查询。pipeline 中止或失败可能留下部分本地文件；destroy 流不会删除文件或撤销已写出的字节。生产 attempt 应拥有自己的私有临时对象键，正常失败时由该 attempt 清理未发布对象；若 worker 崩溃留下孤儿对象，则由独立回收责任方按持久导出设计中的宽限期清理。只有完整上传且当前 attempt 提交结果引用后才把 job 标为 succeeded。FastAPI 的 StreamingResponse 是另一条请求内直接传给客户端的路径，依赖资源活到正文结束或请求取消。

生产 worker 应从已持久接受且已授权的 job 读取 acct-17、时间范围与分页上限，不能从队列正文重新信任未验证的账户范围。现有报表设计按最多 12 页查询、每页短事务读取；读取完一页即归还连接，再做压缩和写入，见[如何限定 ORM Session 并排查连接池耗尽？](data-access-and-connection-pools.md)。如果实际驱动提供的是持有数据库游标的长连接流，它可能在下游变慢时继续占住事务和连接；须把这段真实连接持有时间计入连接池和任务槽预算。需要同一快照时，可以明确选择长事务并核算额外成本，不能把短事务分页示例直接换成长游标。真实驱动是否响应取消仍需按驱动契约确认；如果不支持，正在执行的查询可能要等返回后生成器 finally 才能关闭游标。

Writable 的 highWaterMark 是缓冲阈值，不是整条管线的内存预算；如果上游在管线外把所有任务先放入数组或无界队列，stream 背压到不了那条队列。取消会传播给参与管线的流，但不能假定驱动正在执行的 `cursor.next()` 已停止：当前查询可能要先返回，生成器的 `finally` 才能关闭游标。资源所有者应跟踪并等待该操作确实结束，再关闭它仍在使用的连接；仅观察 AbortSignal 已触发不足以证明资源可释放。可读流的 end 表示没有更多输入块；调用 end() 后可写流的 finish 表示已处理接受的写入；close 表示该流报告资源关闭；error 表示失败。文件流 finish 也不证明远端应用收到数据或文件系统已持久化。

**接下来：** 本章说明管线内部的流量控制；HTTP 请求、worker 和持久队列的并发上限见[如何估算并限制异步工作管线？](../reliability/api-capacity-and-backpressure.md)。服务退出时如何停止接入并等流结束，见[Node.js 服务如何排空并关闭？](node-service-shutdown.md)。

> [!info]- 来源
> - Writable.write() 返回 false、drain、错误/销毁状态，以及 Readable.from() 默认 object mode：[Node.js v26.11.1, Stream](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html)，核对于 2026-11-06。
> - pipeline() 的 Promise、AbortSignal 和流清理：[Node.js v26.11.1, stream/promises](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html#stream-promises-api)，核对于 2026-11-06。
> - end、finish、close 和 error 的生命周期定义：[Node.js v26.11.1, Stream API](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html)，核对于 2026-11-06。
