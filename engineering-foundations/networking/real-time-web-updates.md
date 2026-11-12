# 何时选择轮询、SSE、流式 Fetch 或 WebSocket？

**案例：** 报表查看者已请求刷新报表 42，并获准读取它。前一篇[说明浏览器怎样验证缓存中的 v8 表示并取得 HTTP 响应](http-protocols-and-websockets.md)；本例是在后续一次权威读取中得到新的 `version=9`、`status=running` 和事件日志游标 `103`。本章比较 short polling (短轮询)、long polling (长轮询)、Server-sent Events (SSE，服务器发送事件) 与浏览器 EventSource 接口、Fetch API (网页请求接口) 响应流，以及 WebSocket 双向消息通道。查看者最终需要判断是重新读取当前状态，还是必须处理每一次状态变化；“重新连上”本身不会补回应用漏掉的工作。

~~~mermaid
flowchart TD
    Need{是否要求同一通道持续双向发送？}
    Need -->|是| WS[WebSocket]
    Need -->|否| Repeat{客户端能否按所需时延反复发请求？}
    Repeat -->|能| Poll[短轮询或长轮询]
    Repeat -->|不能，服务端要主动推送| Shape{普通 GET 和原生事件解析是否够用？}
    Shape -->|够用| SSE[SSE + EventSource]
    Shape -->|需要自定义请求或解析| Fetch[Fetch 响应流]
    Poll --> Resume[选状态重查或事件续读]
    SSE --> Resume
    Fetch --> Resume
    WS --> Resume
    Resume --> Answer[明确游标、重复、缺口与授权]
~~~

## 先按方向、请求形状和恢复目标选通道

| 方式 | 请求与消息方向 | 恢复由谁负责 | 合适的条件与成本 |
| --- | --- | --- | --- |
| 短轮询 | 客户端按间隔发普通 HTTP 请求，取得当前状态或自上次游标以来的变化 | 客户端控制间隔、退避、抖动和停止；接口定义版本或游标 | 更新不密、简单性重要。间隔越短，发现变化越快，但空响应和请求数越多 |
| 长轮询 | 服务端暂留一次请求，等到有变化或期限到，再返回；客户端随后带新游标发下一次请求 | 客户端重新请求；服务端为等待中的请求设上限，双方仍处理代理超时和断线 | 需要普通 HTTP 请求形状又想减少空轮询。每个挂起请求仍占服务端状态、HTTP 流及相关资源；过期后应带游标续问 |
| Server-sent Events (SSE，服务器发送事件) + `EventSource` | 浏览器用 `GET` 建立 `text/event-stream` 响应，主要从服务端收事件 | 原生接口通常重连并带 `Last-Event-ID`；服务端还须保存事件并按有效游标重放 | 服务端单向推送，原生事件格式和重连合用。构造器不能设置自定义字段、请求方法或正文 |
| 流式 Fetch (Fetch response stream，Fetch 响应流) | 一次请求按 API 契约使用方法、字段和正文；响应体可逐块读取 | 应用实现解析、恢复游标、重试、退避、取消和授权 | 需要 `Authorization` 字段、POST 查询或自定义线格式。读到的字节块不是事件边界 |
| WebSocket 双向消息通道 | 握手后，客户端和服务端都可主动发送消息 | 应用定义重连、身份更新、确认、序号和重放 | 需要在长连接上持续双向低延迟交互。浏览器原生 API 不替应用恢复消息，也没有接收侧背压 (backpressure，消费较慢时令上游减速) 接口 |

若更新不密但又要求尽快到达，长轮询和推送都可减少等待：长轮询在事件出现或请求期限到时结束本次请求，客户端马上带新游标再问；它仍要承担挂起请求、代理超时和重新建连成本。SSE 或 Fetch 推送保持一个响应打开，减少反复请求，却要检查代理缓冲、空闲超时和长连接容量。选择取决于目标延迟、服务器资源和部署链路，不存在只凭“实时”二字就必然胜出的方式。短轮询可带版本或条件字段来少传正文，但仍会发请求；Entity Tag (ETag，实体标签) 与 `304` 的边界见[HTTP 请求与缓存笔记](http-protocols-and-websockets.md)。

同一报表案例用长轮询时，`after` 始终指向最近已取到的事件。下面先看只需更新当前状态的路径；若每条事件都要触发不可丢的副作用，应用层确认 (application-level acknowledgement，ACK) 必须持久保存，`after` 要取自它，不能因为网络已返回就越过尚未处理完的事件：

~~~http
GET /api/reports/42/updates?after=103&wait=25 HTTP/1.1
~~~

服务端最多等待 25 秒；若事件 104 先出现，就返回 104，客户端下一次请求改带 `after=104`。若先超时且没有事件，接口可以返回空的 `204 No Content`，客户端仍以 `after=103` 再问；游标只在收到事件后前进。这里的 204 是普通长轮询接口的响应约定，客户端负责发下一次请求；后文 EventSource 收到 204 则是另一项标准行为，会停止自动重连。短轮询则不在服务端等候，按客户端间隔重复读取同一状态或游标。

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{"cursor":"104","type":"report.updated","version":10,"status":"running","progress":80}
~~~

一万名客户端若各自每 0.5 秒轮询一次，粗略请求率为 `10,000 ÷ 0.5 = 20,000` 次/秒；这是请求数估算，不等于同样数量的数据库查询或固定 CPU 开销，也未计入重试和同步突发。加随机抖动可以摊平同时请求；更新少时可延长间隔，服务端报错时按退避重试，任务结束或页面不再需要更新时停止。容量与准入见[Web 服务如何限制拒绝服务的影响？](../security/web-availability-and-ddos.md)。

## 断线后，客户端要重建状态还是补齐每条事件？

先区分两种结果。若报表界面只需最新状态，断线后重新读取带单调 `version` 的权威快照即可；只有事件携带完整状态、较大版本确实覆盖较小版本时，客户端才可安全丢弃旧状态。若每条事件都触发不可丢失的工作，服务端必须保留可重放日志，客户端必须有持久的应用确认位置，并定义重复、顺序和缺口处理。

**本例输入：** 报表快照为版本 9，`status=running`，其中已包含事件日志至游标 103。版本描述状态修订；游标描述从哪条日志接着读。两者应由同一一致性位置读取。若快照涵盖至 103，订阅从 103 之后开始；若先读快照、再订阅“当前最新”而不带位置，两步之间的新变化就可能漏掉。

~~~http
GET /api/reports/42 HTTP/1.1
Accept: application/json
~~~

~~~json
{"id":42,"version":9,"status":"running","progress":0,"event_cursor":"103"}
~~~

游标示例使用数字便于阅读；真实游标可以是不透明字符串，只能在服务器定义的报表或订阅范围中解释；本例顺序只保证同一报表日志内的先后，不暗示不同报表或分区之间有全局顺序。服务端先认证并授权报表 42，再验证游标属于该范围且仍在可重放窗口内。客户端提供的游标不是身份凭据，也不能授权读取事件。

历史回放接到实时尾读也必须沿同一连续日志位置前进。一个可实现的契约是：服务端授权订阅后取本轮 watermark (高水位) `W=105`，回放 `(103,105]` 中的 104 和 105，再从 `W` 之后继续读取同一追加日志。若 106 在回放期间追加，它仍位于 105 之后，尾读会接到它。若实现把历史读取和实时通知分开，就先登记通知再捕获 `W`，回放到 `W` 后按日志游标读取到当前尾端；通知只负责唤醒补读。也可以由同一日志读取器原子地建立水位与尾读位置。不能等回放结束后再另开一个“从当前”监听，否则两步间可能漏事件。数字仅把本例同一日志的顺序写直观。

## SSE 如何从快照游标续读事件？

SSE 把 UTF-8（Unicode Transformation Format 8-bit，8 位 Unicode 转换格式）文本按行解析；CRLF (carriage return + line feed，回车加换行)、单独的 CR (carriage return，回车) 或 LF (line feed，换行) 都可结束一行，空行结束一条完整事件。`event` 命名事件类型，`data` 提供负载，`id` 给重连位置，`retry` 给重连等待时间提示。多条 `data` 行会以换行符拼成一份数据；没有 `event` 的事件类型是 `message`；以冒号开头的注释不派发事件，可用于保活。`retry` 只有值全由 ASCII 数字组成时才会被原生接口采用。网络分块、HTTP 帧或一次 Fetch `read()` 都可能切在字符或字段行中间，不能当作事件边界。

这些规则保证解析边界，不保证每个服务端小写入都立即到达浏览器。代理或压缩层可能先缓冲并合并数据；例如 NGINX 反向代理默认启用响应缓冲。长响应还可能被代理或负载均衡器的空闲超时关闭。上线前要检查整条链路的缓冲与超时设置；否则即使应用及时写出事件，查看者也可能延迟收到或需要续连。

本例把快照和事件日志位置对齐后，第一次订阅通过应用约定的 URL (Uniform Resource Locator，统一资源定位符) 查询参数 `after=103` 请求后续事件。服务端对每次连接先授权，再从事件日志读取 103 之后的记录：

~~~http
GET /api/reports/42/events?after=103 HTTP/1.1
Accept: text/event-stream
~~~

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

图中完整路径从同一时点的快照与游标开始，经过授权和续读，再把日志位置映射成状态版本。`104`、`105` 是事件位置；`version=10`、`version=11` 是状态修订。图中高水位之后仍按同一日志尾读，因此回放到实时的衔接不另造游标，也不丢掉回放期间追加的事件。

![从一致快照游标开始订阅，并沿同一日志从历史回放衔接到实时尾读](resources/sse-snapshot-to-events.svg)

同源页面可以用原生接口处理这些事件。`reset` 是本例定义的事件名：游标过期时客户端关闭旧连接、重新读取快照，再用新游标建立对象。

~~~javascript
const url = '/api/reports/42/events?after=103';
const source = new EventSource(url);

source.addEventListener('report.updated', (event) => {
  const update = JSON.parse(event.data);
  if (update.report_id === 42) {
    showStatus(update.status, update.version, update.progress);
  }
});
source.addEventListener('reset', () => {
  source.close();
  void refreshSnapshotAndSubscribeAgain();
});
// 逐事件订阅的游标过期分支：停止重连并进入审计对账流程。
source.addEventListener('cursor.expired', () => {
  source.close();
  showDeliveryGapAndReconcile();
});
source.addEventListener('error', () => {
  showConnectionState(source.readyState);
});
~~~

本例首次流按序发送 104、105。假定浏览器已收到事件 104 末尾的空行并完整解析 104；连接随后断开时，事件 105 尚未被浏览器解析，但仍留在服务器日志。浏览器通常用同一 URL 重连，并将已解析的最后事件 ID 放进 `Last-Event-ID` 请求字段。对“只要最新报表状态”的路径，本例规定该字段优先于原 URL 的 `after=103`，服务端就从 104 之后重放 105，再沿同一日志续读更新。第一次订阅用 URL 游标，因为原生 `EventSource` 只接受 URL 和 `withCredentials` 选项，页面不能设定初始 `Last-Event-ID`。重连间隔可由 `retry` 字段建议；浏览器的退避策略和网络条件意味着客户端不应假设一个固定重连时刻。

这个解析位置不是业务确认。浏览器在排入 JavaScript 事件处理器之前，先更新自己的 Last-Event-ID；若事件 104 已被解析、处理器却在持久化副作用前失败，自动重连仍可能从 104 之后开始，应用没法靠该请求头发现这次处理缺失。相反，如果客户端在处理完成后才把确认写入数据库，处理已提交而确认未提交时也会重复收到事件。

![浏览器解析游标与逐事件确认的恢复分支：ACK=103 重放104，ACK=104 续读105](resources/sse-parse-vs-ack.svg)

因此，若只要界面当前状态，可按 `version` 合并完整状态，并在恢复后 GET 权威快照；这条路径上 `reset` 可以关闭旧连接、读取新快照并从快照游标重订阅。若每条事件都重要，则必须维护独立、按消费者和订阅范围保存的持久确认游标，并且它只能推进已经连续处理完成的前缀：若 104 尚未完成，就不能因 105 已完成而确认到 105。处理失败要显式重试该事件或停止并从持久确认位置重新订阅，不能等连接偶然断开。客户端成功处理事件 104 后，可用另一个已授权请求提交确认：

~~~http
POST /api/reports/42/ack HTTP/1.1
Content-Type: application/json

{"cursor":"104"}
~~~

服务端把连续确认位置持久化，逐事件路径的断线恢复以它为准，即使 EventSource 的 `Last-Event-ID` 更靠后，也不能用解析进度覆盖尚未确认的事件。若已确认位置还是 103，重连要重放 104；只有 104 的业务处理成功且已持久确认后，下一次重连才从 105 继续。处理和确认若能同事务提交最好；若两者分开，处理已提交而确认未提交时 104 会重复，因此按事件 ID 去重并让副作用保持 idempotent (幂等)。传输能重发，不提供端到端只处理一次。若事件只是局部补丁而不是完整状态，必须保序应用或回到快照重建，不能任意跳过中间版本。

游标过期时不要悄悄跳过缺口。对于只需当前状态的路径，服务器可发送应用定义的 `reset` 事件并结束当前响应；它必须带 `data` 字段并以空行结束，才能派发给上面的处理器：

~~~text
event: reset
data: {}

~~~

若每条事件都重要，重放游标超出日志保留期就表示业务缺口：不能把游标推进到新快照位置来假装补齐事件。服务端可在结束流前明确发送应用定义的过期事件，例如：

~~~text
event: cursor.expired
data: {"after":"103","earliest_available":"200"}

~~~

客户端收到它后应关闭旧订阅并标记缺口，从更长保留的审计日志对账或走有记录的恢复流程，之后才从新确认位置继续。新快照只能重建当前状态，不能替代漏掉的逐事件副作用。另一种标准行为是对新的 SSE 请求返回 HTTP `204 No Content`，告诉 `EventSource` 停止自动重连；它不是把已经开始的 `200` 流改成 `204`。按标准，非 `200` 响应或错误媒体类型会使连接进入终止错误状态；原生 `error` 事件不暴露响应状态码或错误正文，页面要按 `readyState` 处理继续连接或关闭后的路径。每次初连和重连都要重新验证身份并授权报表；若授权过期，页面不能从 `EventSource` 的错误事件读出 `401` 后自行改请求字段。跨源 EventSource 默认不带跨源凭据；需要 Cookie 时可设置 `{ withCredentials: true }`，服务端必须按 CORS 凭据规则返回与页面来源匹配的 `Access-Control-Allow-Origin` 和 `Access-Control-Allow-Credentials: true`；不能用通配来源代替。凭据仍受浏览器 Cookie 策略约束。需要自定义授权字段或刷新凭据时，使用流式 Fetch 或由页面关闭旧对象、完成认证更新后再创建新对象。

## 流式 Fetch 如何从任意字节块组装有限结果？

若服务端单向响应仍合适，但原生 `EventSource` 的 GET、Cookie 凭据选项或请求字段不满足接口需要，可用 Fetch 发带授权字段和正文的 POST，再读取 SSE 格式或其他明确线格式。本例的有限搜索请求用来展示这种自定义请求与持续订阅的区别：搜索匹配结果是这次查询的输出，不等于实时订阅，也不自动修改权威报表状态。Fetch 的 `Response.body` 是可读流 (ReadableStream)：客户端按需读取时，Streams 可以限制本地队列的堆积；这不是应用已处理某条消息的确认，也不保证服务端业务生成已停止。

本例的有限搜索接口以 `result.complete` 表示这次响应已产生完整结果，然后结束正文。终止事件必须像下面这样包含 `event` 行、`data` 行和结束事件的空行；只有完整空行边界到达，解析器才确认看到了终态。Fetch 的 end of file (EOF，读流结束) 只表明字节流结束，不能代替应用完成信号。SSE 标准 EventSource 会丢弃 EOF 前未被空行结束的尾部事件；下面这个自有 Fetch 协议对有限响应采取更严格约定：未闭合事件或缺失终止事件都按截断失败处理。

~~~text
event: result.complete
data: {}

~~~

字节块也可能把一个 UTF-8 字符切成两半。以 `报` 的 UTF-8 字节 `E6 8A A5` 为例，第一块可以在 `E6 8A` 后结束，第二块从 `A5` 接上并继续给出 `表` 和两个换行字节；增量 `TextDecoder` 会等后续字节补齐字符，行解析器再等到第二个换行才派发事件：

~~~text
第 1 块末尾：... 64 61 74 61 3A 20 E6 8A
第 2 块开头：A5 E8 A1 A8 0A 0A ...
解码并按行解析：data: 报表\n\n  → 事件数据「报表」
~~~

下面是完整的教学解析器与消费循环：按 CRLF、CR 或 LF 切行，忽略注释，拼合多条 `data` 行，识别 `event` / `id`，限制单行和单事件缓冲，并在 EOF 检查空行边界。是否出现过 `data` 字段与拼接后的负载是否为空是两回事：单个 `data:` 字段会派发 `data === ''`，没有 `data` 字段则不派发。默认 `TextDecoder` 已按 UTF-8 解码规则去掉开头的一个 byte-order mark (BOM，字节顺序标记)；解析器不再二次裁剪，因此双 BOM 的第二个字符仍留在字段名开头，不会被误识别成 `data`。这个 Fetch 解析器不自动重连，也不实现 SSE 的 `retry` 等待建议；应用的重试策略需另行按游标和错误类型定义。

> [!example]- 有限 SSE 响应的解析与消费实现
>
> ~~~javascript
> class StrictSSEParser {
>   constructor(onEvent, maxLineUnits = 16_384, maxEventUnits = 65_536) {
>     this.onEvent = onEvent;
>     this.maxLineUnits = maxLineUnits;
>     this.maxEventUnits = maxEventUnits;
>     this.line = '';
>     this.data = [];
>     this.type = '';
>     this.id = '';
>     this.eventUnits = 0;
>     this.skipLF = false;
>     this.pendingBlock = false;
>   }
>
>   feed(text) {
>     for (const char of text) {
>       if (this.skipLF) {
>         this.skipLF = false;
>         if (char === '\n') continue;
>       }
>       if (char === '\r') {
>         this.#line();
>         this.skipLF = true;
>       } else if (char === '\n') {
>         this.#line();
>       } else {
>         this.line += char;
>         if (this.line.length > this.maxLineUnits) throw new Error('SSE line too large');
>       }
>     }
>   }
>
>   #line() {
>     const line = this.line;
>     this.line = '';
>     this.eventUnits += line.length + 1;
>     if (this.eventUnits > this.maxEventUnits) throw new Error('SSE event too large');
>
>     if (line === '') {
>       this.#dispatch();
>       this.eventUnits = 0;
>       this.pendingBlock = false;
>       return;
>     }
>     this.pendingBlock = true;
>     if (line.startsWith(':')) return;
>
>     const colon = line.indexOf(':');
>     const field = colon < 0 ? line : line.slice(0, colon);
>     let value = colon < 0 ? '' : line.slice(colon + 1);
>     if (value.startsWith(' ')) value = value.slice(1);
>     if (field === 'data') this.data.push(value);
>     else if (field === 'event') this.type = value;
>     else if (field === 'id' && !value.includes('\0')) this.id = value;
>     // This finite Fetch reader leaves retry timing to its caller.
>   }
>
>   #dispatch() {
>     const data = this.data.join('\n');
>     if (this.data.length > 0) this.onEvent({ type: this.type || 'message', data, id: this.id });
>     this.data = [];
>     this.type = '';
>   }
>
>   finish() {
>     if (this.line !== '' || this.pendingBlock || this.data.length !== 0 || this.type !== '') {
>       throw new Error('EOF before SSE blank-line delimiter');
>     }
>   }
> }
>
> const controller = new AbortController();
> const response = await fetch('/api/reports/42/events/search', {
>   method: 'POST',
>   headers: {
>     Authorization: 'Bearer token-supplied-by-the-application',
>     Accept: 'text/event-stream',
>     'Content-Type': 'application/json',
>   },
>   body: JSON.stringify({ stage: 'rendering' }),
>   signal: controller.signal,
> });
> async function rejectUnreadResponse(error) {
>   if (response.body) {
>     try { await response.body.cancel(error); } catch { /* 保留原响应错误 */ }
>   }
>   throw error;
> }
> if (response.status !== 200) await rejectUnreadResponse(new Error(`HTTP ${response.status}`));
> if (!response.body) throw new Error('Missing response body');
> const mediaType = response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
> if (mediaType !== 'text/event-stream') await rejectUnreadResponse(new Error('Unexpected stream media type'));
>
> let sawTerminal = false;
> const appendSearchResult = (result) => showStatus(result.status, result.version, result.progress);
> const parser = new StrictSSEParser((event) => {
>   if (sawTerminal) throw new Error('Event after result.complete');
>   if (event.type === 'result.complete') {
>     sawTerminal = true;
>   } else if (event.type === 'report.updated') {
>     const result = JSON.parse(event.data);
>     appendSearchResult(result);
>   }
> });
> const reader = response.body.getReader();
> const decoder = new TextDecoder();
> try {
>   while (true) {
>     const { done, value } = await reader.read();
>     if (done) {
>       parser.feed(decoder.decode()); // 冲刷最后一个 UTF-8 字符
>       parser.finish();               // 不把 EOF 当作事件分隔符
>       if (!sawTerminal) throw new Error('Truncated event stream');
>       break;
>     }
>     parser.feed(decoder.decode(value, { stream: true }));
>   }
> } catch (error) {
>   try { await reader.cancel(error); } catch { /* 保留原读取或解析错误 */ }
>   throw error;
> } finally {
>   reader.releaseLock();
> }
> ~~~

解析器中的上限是示例值，限制 UTF-16 代码单元数；生产接口还应按负载大小、并发和内存预算选界限。`appendSearchResult(result)` 是页面提供的查询结果呈现函数；若匹配项是完整报表状态，合并时仍按版本处理，不能把搜索输出误当作实时事件确认。已经显示的匹配项仍只能标为部分结果；只有完整终止事件与完整 EOF 都通过检查后，才能标记整次查询完成。若随后截断，保留的部分结果不能冒充完整答案。代码先检查状态码和媒体类型，并在出错时取消尚未读取的响应体，再抛出错误；进入 `getReader()` 后的读取或解析失败则取消 reader 并释放锁。暂停读流能限制本地缓冲，却不能确认服务端停止生成。若调用方按接口契约在完整终止事件后决定提前结束，而不需要检查 EOF 和终态后没有多余事件，应调用 `reader.cancel()` 释放未读响应体，再把这条路径标记为“主动停止”而非“读取到 EOF”。若请求跨源，浏览器仍执行 Cross-Origin Resource Sharing (CORS，跨源资源共享) 检查；`Authorization` 和 `application/json` 通常还会触发预检，服务端必须按凭据模式、来源和请求字段配置允许策略。[页面如何表示部分、重连、取消和终态？](../../frontend/browser-apis/streaming-ux.md)讨论界面状态。

## WebSocket 怎样维持双向消息并限制慢客户端？

浏览器 WebSocket 在 HTTP/1.1 上常用 Upgrade 握手与 `101 Switching Protocols`，之后连接承载双方主动发送的消息；HTTP/2、HTTP/3 使用各自协商启用的 Extended CONNECT 扩展，不能一概说成“升级到 TCP”。HTTP/1.1 持久连接可以复用多个请求/响应，但服务端仍需等客户端请求，不能因此自行推送；WebSocket 才把会话变成双向消息通道。HTTP/2 和 HTTP/3 的扩展还要求双方及中间代理支持，不能只因底层 HTTP 版本是 H2/H3 就假定可用。

浏览器 `WebSocket` 构造器接受 URL 和可选子协议，不开放任意自定义请求字段；若请求了子协议，服务器必须选中其中一个，握手才成功，例如本例的 `reports.v1`。浏览器会按 WebSocket 握手发送 `Origin`（来源）字段，服务端应校验允许来源；`Origin` 不是用户身份，非浏览器客户端也能伪造它。WebSocket 握手不使用 Fetch 的 CORS 响应许可机制，因此仍须防止恶意站点借用户 Cookie 建立连接。Cookie 是否随握手发送仍受 `SameSite`、第三方 Cookie 和其他浏览器策略约束。认证后还要授权每条订阅和敏感操作；连接存活期间权限可能变化，不能只在握手时检查一次。页面后台挂起、网络切换及代理空闲超时也可能中断连接，恢复必须仍走下文的游标路径。

本例逐事件订阅先从已持久化的确认游标 `103` 开始。授权后，服务端在同一事件日志上取高水位 `W=105`，先按序回放 104、105，再从 105 之后继续尾读；订阅期间追加的 106 仍能从该位置读到。服务端回一条 `subscribed` 消息报告本轮回放边界 `replayThrough=105`，这只是本应用协议的水位，不是 WebSocket 提供的恢复功能。若在处理并确认 104 后断线，客户端从自己的持久确认读取 `after=104`，重连后服务端续读 105；断线时尚未确认的事件则会重放。服务端仍需每次连接和订阅时重新授权。

~~~json
{"type":"subscribed","replayThrough":"105"}
{"type":"report.updated","cursor":"104","version":10,"status":"running","progress":80}
{"type":"report.updated","cursor":"105","version":11,"status":"ready","progress":100}
{"type":"report.updated","cursor":"106","version":12,"status":"ready","progress":100}
~~~

前三条表示服务端先通知回放边界，再依序重放 104 和 105；若 106 在回放过程中追加，同一日志尾读会接到它。客户端保存到 104 的连续确认后断线，重连订阅 `after=104`，服务端带 `after=104` 重放 105；`replayThrough` 只界定本轮回放，不是客户端已处理位置。若服务端回应 `cursor.expired`，客户端应停止自动重连并进入审计对账；逐事件缺口不能用新快照跳过。下面的应用子协议约定使用 UTF-8 JSON 文本消息，事件游标和类型必须符合该订阅的契约。消费代码假设已认证的服务端按同一订阅连续、按序送达；`advanceContiguousAck` 只保护确认位置。若接收端还要防止上游跳过事件，必须在副作用开始前验证该订阅的预期前驱，不能等写 ACK 时才发现缺口；真实游标可以不透明，不能一概用数字加一。

> [!example]- 持久确认、串行消费与断线恢复实现
>
> ~~~javascript
> async function connectReports42() {
>   const after = await loadDurableAck(42) ?? '103';
>   const socket = new WebSocket('wss://reports.example/realtime', ['reports.v1']);
>   const MAX_IN_FLIGHT = 16;      // 服务端同一订阅最多发 16 条尚未确认的事件
>   const MAX_EVENT_BYTES = 64 * 1024;
>   const MAX_ACK_BUFFERED_BYTES = 64 * 1024;
>
>   let delivery = Promise.resolve(); // 串行处理；最多 16 条待完成
>   let pending = 0;
>   let stopped = false;
>   let retryAfterClose = true;
>   let recoveryScheduled = false;
>
>   function stop(reason, retry = true) {
>     if (stopped) return;
>     stopped = true;
>     retryAfterClose = retry;
>     if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
>       socket.close(4000, reason);
>     }
>   }
>
>   function recoverAfterDrain() {
>     if (recoveryScheduled) return;
>     recoveryScheduled = true;
>     void delivery.then(() => {
>       if (retryAfterClose) scheduleReconnectWithJitter(connectReports42);
>       else void showDeliveryGapAndReconcile();
>     });
>   }
>
>   socket.addEventListener('open', () => {
>     if (stopped) return;
>     try { socket.send(JSON.stringify({ type: 'subscribe', reportId: 42, after })); }
>     catch { stop('subscribe send failed'); }
>   });
>
>   socket.addEventListener('message', ({ data }) => {
>     if (stopped) return;
>     let message;
>     try {
>       if (typeof data !== 'string' || new TextEncoder().encode(data).byteLength > MAX_EVENT_BYTES) {
>         throw new Error('invalid or oversized message');
>       }
>       message = JSON.parse(data);
>       if (message === null || typeof message !== 'object' || Array.isArray(message)) {
>         throw new Error('message must be a JSON object');
>       }
>       if (message.type === 'subscribed') {
>         if (typeof message.replayThrough !== 'string') throw new Error('invalid subscribed message');
>       } else if (message.type === 'cursor.expired') {
>         if (typeof message.after !== 'string') throw new Error('invalid cursor.expired message');
>       } else if (message.type === 'report.updated') {
>         if (typeof message.cursor !== 'string' || !Number.isSafeInteger(message.version) ||
>             typeof message.status !== 'string' || !Number.isFinite(message.progress)) {
>           throw new Error('invalid report.updated message');
>         }
>       } else {
>         throw new Error('unknown message type');
>       }
>     } catch {
>       stop('invalid event');
>       return;
>     }
>
>     if (message.type === 'subscribed') {
>       showReplayBoundary(message.replayThrough); // 本例收到 "105"
>       return;
>     }
>     if (message.type === 'cursor.expired') {
>       stop('cursor expired', false); // 不要带过期游标自动循环重连
>       return;
>     }
>     if (pending >= MAX_IN_FLIGHT) {
>       stop('server exceeded credit window');
>       return;
>     }
>
>     pending++;
>     delivery = delivery.then(async () => {
>       try {
>         if (stopped) return; // 关闭后跳过已排队项；不启动它们的副作用
>         await applyEventIdempotently(message);
>         const cursor = await advanceContiguousAck(42, message.cursor);
>         // 先持久化，再尝试在线发送；若连接已关，重连会从持久值恢复。
>         if (!stopped && socket.readyState === WebSocket.OPEN) {
>           if (socket.bufferedAmount > MAX_ACK_BUFFERED_BYTES) {
>             stop('ack send backlog');
>             return;
>           }
>           socket.send(JSON.stringify({ type: 'ack', reportId: 42, cursor }));
>         }
>       } catch {
>         stop('event processing failed');
>       } finally {
>         pending--;
>       }
>     });
>   });
>
>   socket.addEventListener('error', () => stop('socket error'));
>   socket.addEventListener('close', () => {
>     stopped = true;             // 立即阻止新任务
>     recoverAfterDrain();        // 在途任务落定后只重连一次
>   });
> }
> void connectReports42();
> ~~~

WebSocket 在线上可将一条消息拆成多个帧，协议会按发送顺序重组为完整消息；浏览器 `message` 事件交付完整消息，不把帧边界当成应用消息边界。单个连接内发送顺序有保证，重新建连后则没有跨连接的顺序或历史恢复，应用仍要携带游标并重放。上一段的 `after` 来自持久应用确认，`replayThrough=105` 则是服务端捕获的回放水位；它们分别回答“从哪里补”和“本轮回放到哪里接实时”。关闭/网络错误只说明通道断了，不能说明最后一条业务消息是否已提交；需要应用确认或重新读取权威快照。

经典浏览器 WebSocket API 没有接收侧背压控制：即使 `message` 处理器是异步的、每次都 `await`，浏览器仍会继续派发后续消息，应用无法要求发送方等它处理完。本例的有界策略由双方协议共同保证：服务端对每个订阅最多发送 16 条尚未收到连续 ACK 的事件，收到累计 ACK 后才释放相应额度；每条文本事件不超过 64 KiB。客户端也把进入串行业务队列的待处理数限制为 16，超额或超长即关闭并从持久 ACK 恢复。因此应用队列中的事件负载最多约 1 MiB，尚不含对象和运行时开销。超长检查发生在浏览器已交付完整消息之后，只挡住它进入应用队列；服务端发送前也必须执行同一大小限制。关闭时先停止入队；一个已开始的副作用可以完成并持久推进 ACK，旧队列里的其余任务在执行副作用前检查停止标记并跳过，队列排空后只重连一次。ACK 先持久化再尝试发送；断线或 ACK 发送失败时，新连接从持久位置恢复。遇到 `cursor.expired` 则停订阅并对账，不以快照跳过缺失事件。浏览器发送侧 `bufferedAmount` 统计本地 `send()` 已排队但尚未交给网络的数据，不表示对端收到或处理；示例也在 ACK 发送侧设 64 KiB 预警水位，超过后关闭恢复。对只关心最新值的通道，可合并状态更新或丢弃可丢进度。服务端可发送 Ping/处理 Pong 或用应用心跳检测失活路径；心跳只说明连接可达，不证明业务副作用成功。

Node.js `ws` 提供该实现自己的 `pause()` / `resume()` 来暂停或恢复接收事件；已有缓冲事件仍可能继续派发，所以仍需有界队列。下面的片段只演示已建立连接后的广播循环及慢客户端边界，不展示 HTTP/2 或 HTTP/3 握手；消息限定为可公开的教学内容。实际报表数据必须只发给已认证且有权读取该报表的订阅者，不能把一个全局客户端集合当作授权范围。`bufferedAmount` 是实现报告的已排队发送量，且计入帧开销。代码在每次发送前检查 256 KiB 水位，但检查后追加的一条消息仍可能越过水位；因此水位不是队列硬上限。应用应为每个客户端限制待发送字节和消息大小；库接收方向还应设置 `maxPayload`，因为 `message` 事件收到的是已经完整组装的消息，事后检查长度无法限制接收缓冲。

> [!example]- Node.js `ws` 广播与慢客户端
> ~~~javascript
> const { WebSocketServer, WebSocket } = require('ws');
> const MAX_SINGLE_MESSAGE_BYTES = 64 * 1024;
> const server = new WebSocketServer({ port: 3000, maxPayload: MAX_SINGLE_MESSAGE_BYTES });
> const clients = new Set();
> const QUEUE_WATERMARK_BYTES = 256 * 1024;
>
> server.on('connection', (socket) => {
>   clients.add(socket);
>   socket.on('message', (data, isBinary) => {
>     // maxPayload 在完整 message 交付前限制单条接收消息的字节数。
>     for (const client of clients) {
>       if (client === socket || client.readyState !== WebSocket.OPEN) continue;
>       if (client.bufferedAmount > QUEUE_WATERMARK_BYTES) {
>         client.terminate();
>         continue;
>       }
>       client.send(data, { binary: isBinary }, (error) => {
>         if (error) client.terminate();
>       });
>     }
>   });
>   socket.on('close', () => clients.delete(socket));
>   socket.on('error', () => socket.terminate());
> });
> ~~~

## 把通道结果接回报表权威状态

重新连上 SSE、重新发 Fetch，或重建 WebSocket，都只恢复传输。报表任务的权威状态仍由状态接口或持久化任务记录负责；若最终结果未知，客户端应重新查询报表/作业资源。只有状态本身满足重建条件时才丢弃中间通知；若每条变化都重要，要让服务端日志保留期覆盖断线窗口，并为每次订阅确定授权范围、游标格式、顺序、确认和过期后的重置流程。不要把客户端提供的游标当成授权信息。

本例 SSE 的 `reset` 处理是“取新快照并从其游标继续”；有限 Fetch 则以 `result.complete` 加完整 EOF 确认单次搜索结束；WebSocket 遇到可恢复的普通关闭时，在持久游标仍可回放的前提下退避重连并重订阅，已知 `cursor.expired` 则停止重连、进入对账，不能用快照跳过缺口。若客户端需要接回已受理的异步任务而不是只更新页面状态，先查稳定状态资源，见[请求超时后如何确认结果并安全重试？](../reliability/api-reliability-and-async-delivery.md)；长期任务状态持久化也见[怎样设计一个可持久查询的账户报表？](../architecture/system-design-fundamentals.md)和[AI 运行怎样在断线或工作进程崩溃后恢复，并避免副作用重复？](../../ai-engineering/systems/ai-application-architecture.md)。

> [!info]- 来源
> - SSE 字段语法、多行与空负载 `data`、单个前置 BOM、空行分发、EOF 丢弃、EventSource 认证选项、`Last-Event-ID`、`retry`、`204` 停止重连和非 `200` /错误媒体类型处理：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，最后更新 2026-11-11，核对于 2026-11-12。
> - Fetch 请求/响应体、CORS：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19；增量解码与 `TextDecoder` 的 BOM 选项：[WHATWG Encoding Standard](https://encoding.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19，§7.1–§7.2；可读流取消、队列和背压：[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，Living Standard，最后更新 2026-10-25，§4.2.4；均核对于 2026-11-12。
> - 轮询、长轮询、挂起请求、流式传输的中间代理行为与超时：[IETF RFC 6202, Known Issues and Best Practices for the Use of Long Polling and Streaming in Bidirectional HTTP](https://www.rfc-editor.org/rfc/rfc6202.html)，§2.1–§2.2、§3.2、§5.5，2011-04；该文为 Informational RFC，核对于 2026-11-12。
> - 反向代理是否缓冲上游响应及默认配置：[NGINX `ngx_http_proxy_module`, `proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)；gzip 响应过滤器与压缩缓冲：[NGINX `ngx_http_gzip_module`, `gzip_buffers`](https://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip_buffers)，当前官方文档均核对于 2026-11-12。
> - 浏览器 WebSocket 构造器、凭据模式、消息与发送队列：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，Living Standard，最后更新 2026-10-19，核对于 2026-11-12；接收侧无背压：[MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)，核对于 2026-11-12。
> - WebSocket 握手、帧/消息顺序与 `Origin` 安全：[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，§4–§5、§10.2，2011-12；HTTP/2 Extended CONNECT：[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)，§3–§4，2018-09；HTTP/3 Extended CONNECT：[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，§3，2022-06；均核对于 2026-11-12。
> - Node.js `ws` 的服务端广播、`bufferedAmount`、`pause()` / `resume()` 和 `send` 回调：[ws 官方 API 文档](https://github.com/websockets/ws/blob/master/doc/ws.md)，当前仓库文档核对于 2026-11-12。此实现文档不是 WebSocket 协议规范；代码展示机制，不包含生产认证、订阅授权或完整连接恢复。
> - 按订阅持久保存连续 ACK、用日志高水位衔接回放与尾读，以及游标过期后的审计对账，都是本例定义的应用协议；HTML SSE 和 WebSocket 标准不替应用提供这些业务交付保证。
