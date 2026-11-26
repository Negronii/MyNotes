# 服务端要持续推送更新时，怎样选通道，断线后又怎样接上？

本章是[条件写章](conditional-updates-and-etags.md)之后的支线：页面不只要读一次，还要在报表生成期间持续得知变化。它回答两个问题：短轮询、长轮询、SSE、流式 Fetch、WebSocket 怎样选；连接断开后，客户端怎样不漏、不错地接上。全章围绕一个先于选型的决定展开：页面只需要最新状态，还是每条事件都不能丢。

**沿用的案例。** 沿用[主线四的报表读取案例](http-semantics-and-transport.md#案例：账户报表服务里的一次读取)。报表 42 被编辑到 v8 之后，用户请求重新生成；之后一次权威读取返回 `version=9`、`status=running`，以及事件日志游标 `103`，表示这份快照已经包含了日志里到第 103 条为止的事件。报表还在生成，页面需要继续收到后续变化：事件 104 会带来 `version=10`、`progress=80`。

## 先定恢复目标：只要最新状态，还是每条事件都不能丢

选通道之前先定恢复目标，因为两种目标对服务端和客户端的要求完全不同：

| 恢复目标 | 断线后怎么做 | 需要的条件 |
| --- | --- | --- |
| **只要最新状态** | 重读带单调 `version` 的权威快照，再从快照的游标继续 | 事件携带完整状态，较大版本确实覆盖较小版本，客户端才能放心丢弃中间通知 |
| **每条事件都不能丢** | 从客户端持久保存的确认位置开始重放 | 服务端保留可重放的事件日志；客户端有持久的应用确认位置；协议定义重复、顺序和缺口怎样处理 |

无论哪种目标，“重新连上”都只恢复了传输，不会补回应用漏掉的工作。报表任务的权威状态始终在状态接口或持久的任务记录里；结果不明时，客户端重新查询这些资源，而不是依赖通道。下面每种通道的恢复细节，都按这两种目标分别说明。

## 按方向、请求形状和恢复责任选通道

~~~mermaid
flowchart TD
    Need{是否要求同一通道持续双向发送？}
    Need -->|是| WS[WebSocket]
    Need -->|否| Repeat{客户端能否按所需时延反复发请求？}
    Repeat -->|能| Poll[短轮询或长轮询]
    Repeat -->|不能，服务端要主动推送| Shape{普通 GET 和原生事件解析是否够用？}
    Shape -->|够用| SSE[SSE + EventSource]
    Shape -->|需要自定义请求或解析| Fetch[Fetch 响应流]
    Poll --> Resume[按恢复目标：状态重查或事件续读]
    SSE --> Resume
    Fetch --> Resume
    WS --> Resume
    Resume --> Answer[明确游标、重复、缺口与授权]
~~~

| 方式 | 请求与消息方向 | 恢复由谁负责 | 合适的条件与成本 |
| --- | --- | --- | --- |
| short polling (短轮询) | 客户端按间隔发普通请求，取当前状态或自上次游标以来的变化 | 客户端控制间隔、退避、抖动和停止；接口定义版本或游标 | 更新不密、简单性重要时。间隔越短发现越快，空响应和请求数也越多；可带条件字段少传正文（见[缓存章](http-caching-and-conditional-requests.md)），但请求照样要发 |
| long polling (长轮询) | 服务端暂留一次请求，有变化或到期限才返回；客户端随后带新游标再问 | 客户端重新请求；服务端限制等待时长；双方处理代理超时和断线 | 要普通请求形状、又想减少空轮询时。每个挂起请求仍占服务端状态和连接资源 |
| SSE（Server-Sent Events）+ `EventSource` | 浏览器用 `GET` 打开一个 `text/event-stream` 响应，从服务端单向收事件 | 原生接口自动重连并带 `Last-Event-ID`；服务端保存事件并按有效游标重放 | 服务端单向推送、原生格式和重连够用时。构造器不能设请求方法、自定义字段或正文 |
| 流式 Fetch | 一次请求可用任意方法、字段和正文，响应体逐块读取 | 应用自己实现解析、游标、重试、退避、取消和授权 | 需要 `Authorization` 字段、`POST` 查询或自定义线格式时。读到的字节块不是事件边界 |
| WebSocket | 握手后双方都能主动发消息 | 应用定义重连、身份更新、确认、序号和重放 | 需要在一条长连接上持续双向低延迟交互时。浏览器原生 API 不恢复消息，也没有接收侧背压 |

长轮询和推送都能减少“更新不密却要尽快到达”时的等待。长轮询每次事件或到期都结束请求，客户端立即带新游标再问，要承担挂起请求、代理超时和反复建连的成本；SSE 或流式 Fetch 保持一个响应打开，减少了反复请求，却要检查代理缓冲、空闲超时和长连接容量。选择取决于目标延迟、服务器资源和部署链路，没有哪种方式只凭“实时”二字就必然胜出。

## 长轮询：游标只在收到事件后前进

报表 42 用长轮询时，查询参数 `after` 指向客户端最近取到的事件：

~~~http
GET /v1/accounts/acct-17/reports/42/updates?after=103&wait=25 HTTP/1.1
~~~

服务端最多等 25 秒。事件 104 先出现，就立即返回它，客户端下一次改带 `after=104`：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{"cursor":"104","type":"report.updated","version":10,"status":"running","progress":80}
~~~

若先到期且没有事件，接口可以回空的 `204 No Content`，客户端仍以 `after=103` 再问。这里的 `204` 只是本接口的约定；后文 `EventSource` 收到 `204` 则是另一项标准行为，会停止自动重连。

两种恢复目标在这里的差别是：只要最新状态时，`after` 可以取“已收到”的位置；每条事件都要触发不可丢的副作用时，`after` 必须取持久保存的 application-level acknowledgement (应用层确认，ACK)，否则会越过尚未处理完的事件。

轮询的成本要按请求数估算。一万个客户端各每 0.5 秒轮询一次，请求率约为 `10,000 ÷ 0.5 = 20,000` 次/秒。这只是请求数，不等于同样数量的数据库查询或固定的 CPU 开销，也没算重试和同步突发。加随机抖动能摊平同时到达的请求；更新少时延长间隔，服务端报错时退避，任务结束或页面不再需要更新时停止。入口怎样准入与限额，见[一条异步管线能接多少工作，超出时在哪里拒绝？](capacity-admission-and-backpressure.md)和[流量远超容量或遭到攻击时，每一层能挡住什么？](overload-and-ddos.md)。

## 快照和订阅怎样衔接在同一日志位置

推送通道都面临同一个衔接问题：先读快照，再订阅后续事件，两步之间发生的变化不能漏掉。这条规则在全领域以这里为准。

快照里同时给出版本和游标：

~~~http
GET /v1/accounts/acct-17/reports/42 HTTP/1.1
Accept: application/json
~~~

~~~json
{"id":42,"version":9,"status":"running","progress":0,"event_cursor":"103"}
~~~

`version` 描述状态修订到第几版，`event_cursor` 描述从日志的哪里接着读。二者必须来自同一个一致性位置：快照涵盖到 103，订阅就从 103 之后开始。若先读快照、再订阅“当前最新”而不带位置，两步之间的变化就可能丢失。

订阅时，服务端先回放 103 之后的历史，再切到实时读取日志尾部（尾读）。切换也必须沿同一条连续日志前进：

1. 服务端授权这次订阅后，记下本轮的 high watermark (高水位) `W=105`，即此刻日志的最新位置。
2. 回放 `(103, 105]`，即事件 104 和 105。
3. 从 `W` 之后继续读同一条追加日志。回放期间追加的 106 位于 105 之后，尾读自然会读到它。

![从一致快照的游标开始订阅，回放到高水位后沿同一日志继续尾读](resources/sse-snapshot-to-events.svg)

实现若把历史读取和实时通知分开，就要先登记通知、再记下 `W`，回放到 `W` 后按日志游标读到当前尾端；通知只负责唤醒补读，不提供位置。也可以由同一个日志读取器原子地确定水位和尾读起点。不能等回放结束后再另开一个“从当前开始”的监听，否则两步之间追加的事件会丢。

示例用数字游标便于阅读。真实游标可以是不透明字符串，只在服务端定义的报表或订阅范围内有序，不同报表或分区之间没有全局顺序。服务端先认证并授权报表 42 的订阅，再验证游标属于该范围、仍在可重放窗口内。客户端提供的游标不是凭据，不能授权读取事件。

## SSE：线格式与事件边界

SSE 把 UTF-8 文本按行解析：

- CRLF、单独的 CR 或 LF 都能结束一行；空行结束一条事件。
- `event` 是事件类型，`data` 是负载，`id` 是重连位置，`retry` 是重连等待时间的建议。
- 多条 `data` 行用换行符拼成一份数据；没有 `event` 时类型为 `message`。
- 以冒号开头的行是注释，不派发事件，可用来保活。
- `retry` 只有全由 ASCII 数字组成时才被原生接口采用。

网络分块、HTTP 帧或一次 Fetch `read()` 都可能切在字符或字段行中间，不能当作事件边界。报表 42 的事件流如下：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

`104`、`105` 是日志位置，`version=10`、`version=11` 是状态修订，两套编号各管一件事。

### 代理缓冲与空闲超时

格式规则确定了事件边界，却不保证服务端每次少量写出都立即到达浏览器。代理或压缩层可能先缓冲、合并数据，例如 NGINX 反向代理默认缓冲上游响应；长响应也可能被代理或负载均衡器的空闲超时关闭。上线前要检查整条链路的缓冲和超时设置，否则应用及时写出的事件，用户可能迟迟收不到，或不得不续连。

## EventSource 能做什么、做不了什么

快照涵盖到 103，第一次订阅用应用约定的 URL 参数 `after=103`。同源页面用原生 `EventSource`：

~~~javascript
const url = '/v1/accounts/acct-17/reports/42/events?after=103';
const source = new EventSource(url);

source.addEventListener('report.updated', (event) => {
  const update = JSON.parse(event.data);
  if (update.report_id === 42) showStatus(update.status, update.version, update.progress);
});
source.addEventListener('reset', () => {           // 本例自定义：只要状态的路径
  source.close();
  void refreshSnapshotAndSubscribeAgain();
});
source.addEventListener('cursor.expired', () => {  // 本例自定义：逐事件路径的缺口
  source.close();
  showDeliveryGapAndReconcile();
});
source.addEventListener('error', () => showConnectionState(source.readyState));
~~~

`reset` 和 `cursor.expired` 是本例自定义的事件名，后文“游标过期”一节解释。`EventSource` 的能力边界：

- **请求形状固定。** 构造器只接受 URL 和 `withCredentials` 选项，不能设方法、字段或正文；首次续读位置只能放在 URL 里，页面不能设定初始的 `Last-Event-ID`。
- **重连自动带位置。** 断线后浏览器通常用同一 URL 重连，并把已解析的最后一个事件 ID 放进 `Last-Event-ID` 请求字段。本例约定该字段优先于 URL 里原来的 `after=103`：若断线前已完整解析 104，服务端就从 104 之后重放 105。重连间隔可由 `retry` 建议，但浏览器的退避策略和网络条件决定实际时刻，客户端不应假设固定的重连时间。
- **停止与终止。** 对新的 SSE 请求返回 `204 No Content`，告诉 `EventSource` 停止自动重连；这不是把已开始的 `200` 流改成 `204`。非 `200` 响应或错误的媒体类型会让连接进入终止状态。原生 `error` 事件不暴露状态码或错误正文，页面只能按 `readyState` 判断。
- **每次连接都授权。** 初连和每次重连，服务端都重新验证身份并授权报表。授权过期时，页面无法从 `error` 事件读出 `401` 再改请求字段。
- **跨源凭据。** 跨源 `EventSource` 默认不带凭据；需要 Cookie 时设 `{ withCredentials: true }`，服务端必须按 CORS 凭据规则返回与页面来源精确匹配的 `Access-Control-Allow-Origin` 和 `Access-Control-Allow-Credentials: true`。需要自定义授权字段或刷新凭据时，改用流式 Fetch，或关闭旧对象、完成认证更新后新建一个。

页面怎样保留已应用的版本 10、续读 105 后更新到版本 11，见[服务端持续推送时，界面怎样合并更新并从断线恢复？](../../frontend/ui-state/streaming-updates-and-resume.md)。

## Last-Event-ID 只是解析位置，不是业务确认

“每条事件都不能丢”时，有一条规则在全领域以这里为准：传输层记录的位置不能当作业务确认。

`Last-Event-ID` 是浏览器的解析位置，在事件交给 JavaScript 处理器之前就已更新。假设 104 已被完整解析，处理器却在持久化副作用前失败；自动重连会从 104 之后开始，应用无法靠这个字段发现 104 的处理缺失。反过来，客户端若在处理完成后才把确认写进数据库，处理已提交、确认却没写成，104 又会被重复收到。

![解析游标与持久确认是两条位置：ACK=103 时重放 104，ACK=104 时续读 105](resources/sse-parse-vs-ack.svg)

所以逐事件路径要维护一个独立的持久确认游标：

- **按消费者和订阅范围保存。** 每个消费者对每个订阅有自己的确认位置。
- **只推进连续完成的前缀。** 104 未完成，就不能因 105 已完成而确认到 105。
- **失败显式处理。** 处理失败要显式重试该事件，或停止并从持久确认位置重新订阅，不能等连接偶然断开。
- **恢复以它为准。** 即使 `Last-Event-ID` 更靠后，也不能用解析进度覆盖尚未确认的事件：确认位置是 103 时重连要重放 104；104 处理成功并持久确认后，下次才从 105 继续。

客户端处理完 104 后，用另一个已授权的请求提交确认：

~~~http
POST /v1/accounts/acct-17/reports/42/ack HTTP/1.1
Content-Type: application/json

{"cursor":"104"}
~~~

处理和确认最好在同一事务里提交。若二者分开，处理已提交、确认未提交时 104 会重复，所以要按事件 ID 去重，并让副作用保持幂等。传输层可以重发，但不提供端到端的“只处理一次”。若事件是局部补丁而非完整状态，必须按序应用，或回到快照重建，不能跳过中间版本。

## 游标过期：重置状态，还是标记缺口去对账

重放窗口不够时，不能悄悄跳过缺口。两种恢复目标的处理不同，下面的 `reset` 和 `cursor.expired` 都是本例自定义的协议，不是 SSE 标准行为：

- **只要最新状态。** 服务端发 `reset` 事件并结束当前响应。它必须带 `data` 字段并以空行结束，才会派发给前面代码里的处理器。客户端关闭旧连接，读取新快照，用新快照的游标重新订阅。

  ~~~text
  event: reset
  data: {}

  ~~~

- **每条事件都不能丢。** 游标早于日志保留期，就是业务缺口，不能把游标推进到新快照的位置假装补齐。服务端在结束流之前明确告知：

  ~~~text
  event: cursor.expired
  data: {"after":"103","earliest_available":"200"}

  ~~~

  客户端关闭订阅、停止自动重连并标记缺口，从保留更久的审计日志对账或走有记录的恢复流程，之后才从新的确认位置继续。新快照只能重建当前状态，不能替代漏掉的逐事件副作用。

## 流式 Fetch：从任意字节块组装一次有限结果

`EventSource` 只能发 `GET`、只能选择是否带 Cookie，接口需要更多时，可以用 Fetch 发带授权字段和正文的 `POST`，再按 SSE 格式或另一种明确定义的线格式读响应。本节换一个有限的例子：在报表 42 的事件中搜索 `stage` 为 `rendering` 的记录。它是一次查询的输出，不是持续订阅，也不修改报表状态。

有限结果的完整性要靠应用协议证明，规则比 `EventSource` 更严：

- **显式终止事件。** 本接口用 `result.complete` 表示结果完整。它必须带 `event` 行、`data` 行和结尾空行，空行边界完整到达后，解析器才算看到了终态。Fetch 读到 EOF 只说明字节流结束，不能代替应用的完成信号。标准 `EventSource` 会丢弃 EOF 前没有以空行结束的尾部事件；本接口更严格，未闭合的事件或缺失的终止事件都按截断失败处理。
- **跨块的 UTF-8 字符。** 字节块可能把一个字符切成两半。增量 `TextDecoder`（`stream: true`）会等后续字节补齐；默认解码器已按规则去掉开头的一个 BOM，解析器不再二次裁剪。
- **有界缓冲。** 解析器限制单行和单个事件的大小。
- **读前检查。** 先查状态码和媒体类型，不符合时取消尚未读取的响应体再报错；开始读取后出错，则取消 reader 并释放锁。
- **部分结果不冒充完整。** 已显示的匹配项只能标为部分结果；终止事件和 EOF 都通过检查后，才能把整次查询标为完成。若契约允许收到终止事件后提前结束，要调用 `reader.cancel()` 释放未读的正文，并记为“主动停止”而不是“读到 EOF”。
- **背压只在本地。** `Response.body` 是 ReadableStream（可读流），暂停读取能限制本地缓冲，却不能让服务端停止生成。

以 `报` 的 UTF-8 字节 `E6 8A A5` 为例：

~~~text
第 1 块末尾：... 64 61 74 61 3A 20 E6 8A
第 2 块开头：A5 E8 A1 A8 0A 0A ...
解码并按行解析：data: 报表\n\n  → 事件数据「报表」
~~~

第一块在 `E6 8A` 处结束，增量解码器暂不输出；第二块从 `A5` 接上，给出“报”和“表”，再遇到两个换行，解析器才派发事件。请求若跨源，浏览器仍执行 CORS 检查；带 `Authorization` 和 `application/json` 的请求通常还会触发预检。界面怎样表示部分、重连、取消和终态，见[前端流式更新一章](../../frontend/ui-state/streaming-updates-and-resume.md)。

下面的解析器按 CRLF、CR 或 LF 切行，忽略注释，拼合多条 `data`，识别 `event` 和 `id`，限制缓冲，并在 EOF 检查空行边界。“出现过 `data` 字段”与“负载为空”是两回事：单个 `data:` 字段会派发空字符串，没有 `data` 字段则不派发。它不自动重连，也不实现 `retry`。

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
> const response = await fetch('/v1/accounts/acct-17/reports/42/events/search', {
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
>
> 解析器的上限是示例值，按 UTF-16 码元计数；生产接口按负载大小、并发和内存预算选定。`appendSearchResult` 是页面提供的展示函数，合并时仍按版本处理。

## WebSocket 怎样建立连接并持续授权

前面几种方式都是服务端单向推送。客户端也要在同一通道上持续发送时，就需要 WebSocket。

- **握手。** 在 HTTP/1.1 上，WebSocket 通过 `Upgrade` 握手和 `101 Switching Protocols` 建立，之后这条连接承载双方主动发送的消息。HTTP/2、HTTP/3 各自通过协商启用的 Extended CONNECT 扩展承载 WebSocket，要求两端和中间代理都支持，不能因为底层是 H2/H3 就假定可用。HTTP/1.1 的持久连接能复用请求—响应，但服务端仍要等客户端请求，不能借此主动推送。
- **子协议。** 浏览器的 `WebSocket` 构造器只接受 URL 和可选的子协议列表，不能设任意请求字段；请求了子协议时，服务器必须选中其中一个，握手才成功，本例是 `reports.v1`。
- **来源校验。** 浏览器在握手中发送 `Origin`，服务端应按允许列表校验。`Origin` 不是用户身份，非浏览器客户端可以伪造或省略它，所以它不能代替认证。WebSocket 握手不走 CORS 的响应许可，浏览器不会替服务端拦下跨站页面发起的握手；Cookie 是否随握手发送，取决于 `SameSite`、第三方 Cookie 等浏览器策略。服务端必须自己校验来源并认证连接，防止恶意站点借用户的 Cookie 建连。
- **持续授权。** 连接建立不等于对所有动作有权。每条订阅、每个读取或变更消息都要按资源和动作授权（见[授权章](per-request-authorization.md)）；连接存活期间权限可能变化，不能只在握手时检查一次。

页面转入后台、网络切换、代理空闲超时都可能中断连接，恢复仍要走下一节的游标路径。

## WebSocket 消息怎样恢复，慢客户端怎样限流

**恢复：两个位置回答两个问题。** 本例逐事件订阅从持久化的确认游标 `103` 开始。授权后，服务端在同一事件日志上取高水位 `W=105`，按序回放 104、105，再从 105 之后尾读；订阅期间追加的 106 仍能读到。服务端先发一条 `subscribed` 消息报告本轮回放边界：

~~~json
{"type":"subscribed","replayThrough":"105"}
{"type":"report.updated","cursor":"104","version":10,"status":"running","progress":80}
{"type":"report.updated","cursor":"105","version":11,"status":"ready","progress":100}
{"type":"report.updated","cursor":"106","version":12,"status":"ready","progress":100}
~~~

`after` 来自客户端的持久应用确认，回答“从哪里补”；`replayThrough=105` 是服务端捕获的回放水位，回答“本轮回放到哪里接上实时”，不是客户端已处理的位置。二者都是本应用协议的约定，WebSocket 本身不提供恢复。若处理并确认 104 后断线，客户端重连时带 `after=104`，服务端续读 105；断线时尚未确认的事件会重放。服务端回 `cursor.expired` 时，客户端停止自动重连、进入审计对账。

WebSocket 在线上可把一条消息拆成多个帧，协议按发送顺序重组，浏览器的 `message` 事件交付完整消息。单个连接内保序；重新建连后没有跨连接的顺序或历史，应用必须携带游标并重放。关闭或网络错误只说明通道断了，不说明最后一条业务消息是否已提交；要靠应用确认或重读权威快照。

**背压：协议级信用窗口。** 经典浏览器 `WebSocket` API 没有接收侧背压：即使 `message` 处理器是异步的、每次都 `await`，浏览器仍继续派发后续消息，应用无法让发送方等它。基于 Streams、能施加背压的 `WebSocketStream` 目前只有 Chromium 系浏览器实现，还不能作为跨浏览器基线。所以有界性要由双方协议保证：

- 服务端对每个订阅最多发 16 条尚未得到连续 ACK 的事件，收到累计 ACK 后才释放额度；每条文本事件不超过 64 KiB。服务端发送前必须执行同一大小限制。
- 客户端把进入串行业务队列的待处理数也限为 16，超额或超长就关闭连接，从持久 ACK 恢复。应用队列里的事件负载因此最多约 16 × 64 KiB = 1 MiB，不含对象和运行时开销。超长检查发生在浏览器已交付完整消息之后，只能挡住它进入应用队列。
- 关闭时先停止入队；已开始的副作用可以完成并持久推进 ACK，队列里其余任务在执行副作用前检查停止标记并跳过；队列排空后只重连一次。ACK 先持久化再尝试发送，断线或发送失败时，新连接从持久位置恢复。
- `bufferedAmount` 只统计本地 `send()` 已排队、尚未交给网络的字节，不表示对端收到或处理了。示例在 ACK 发送侧设 64 KiB 预警水位，超过就关闭恢复。
- 只关心最新值的通道，可以合并状态更新或丢弃可丢的进度。Ping/Pong 或应用心跳只说明连接可达，不证明业务副作用成功。

消费代码假设已认证的服务端按同一订阅连续、按序送达；`advanceContiguousAck` 只保护确认位置。接收端若还要防上游跳过事件，必须在副作用开始前验证该订阅的预期前驱，不能等写 ACK 时才发现缺口；真实游标可能不透明，不能一概用数字加一。

> [!example]- 持久确认、串行消费与断线恢复实现
>
> ~~~javascript
> async function connectReports42() {
>   const after = await loadDurableAck(42) ?? '103';
>   const socket = new WebSocket('wss://reports.example.test/realtime', ['reports.v1']);
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
>     try { socket.send(JSON.stringify({ type: 'subscribe', accountId: 'acct-17', reportId: 42, after })); }
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

服务端同样要限制慢客户端。Node.js `ws` 库的 `pause()`/`resume()` 能暂停或恢复接收事件，但已缓冲的事件仍可能继续派发，所以仍需有界队列。`bufferedAmount` 是库报告的已排队发送量，计入帧开销；发送前检查水位，检查之后追加的一条消息仍可能越过它，所以水位不是硬上限，应用要为每个客户端限制待发送字节和消息大小。接收方向要设 `maxPayload`：`message` 事件收到的已是完整组装的消息，事后检查长度限制不了接收缓冲。下面的片段只演示广播循环和慢客户端处理，假设广播的是可公开的教学内容；真实的报表事件只能发给已认证、且有权读取该报表的订阅者，不能把一个全局客户端集合当作授权范围。

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

## 回到权威状态：通道断了以后以谁为准

本章交出的是一套通道之外的恢复规则：先定恢复目标；快照与订阅衔接在同一日志位置；传输层的位置（`Last-Event-ID`、帧、连接）不等于业务确认，逐事件路径以持久、连续的应用 ACK 为准；游标过期时，只要状态就重置，逐事件就标记缺口去对账。

重新连上 SSE、重发 Fetch 或重建 WebSocket，都只恢复传输。本例 SSE 的 `reset` 是“取新快照、从其游标继续”；有限 Fetch 以 `result.complete` 加完整 EOF 确认一次查询结束；WebSocket 在持久游标仍可回放时退避重连并重新订阅，遇到 `cursor.expired` 就停止并对账。客户端要接回的若是已受理的异步任务，而不只是页面状态，就回到主线：先查稳定的任务状态资源，见[写请求超时后，怎样查清结果并安全重试？](deadlines-retries-and-unknown-outcomes.md)。AI 运行按 `runId` 续读的应用实例，见[重连后怎样回到同一个运行](../../ai-engineering/runs/disconnect-cancel-and-user-input.md)。

> [!info]- 来源
> - SSE 字段语法、多行与空负载 `data`、单个前置 BOM、空行派发、EOF 丢弃未完成事件、`EventSource` 的凭据选项、`Last-Event-ID`、`retry`、`204` 停止重连、非 `200` 与错误媒体类型（“SSE：线格式”“EventSource 能做什么”）：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，2026-11-11 版，核对于 2026-11-12。
> - Fetch 请求与响应体、CORS（“流式 Fetch”）：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，2026-10-19 版；增量解码与 BOM：[WHATWG Encoding Standard](https://encoding.spec.whatwg.org/)，2026-10-19 版，§7.1–§7.2；可读流的取消、队列与背压：[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，2026-10-25 版，§4.2.4；均核对于 2026-11-12。
> - 轮询、长轮询、挂起请求与流式传输经过中间代理时的超时与缓冲（“选通道”“长轮询”）：[IETF RFC 6202](https://www.rfc-editor.org/rfc/rfc6202.html)，2011-04，Informational，§2.1–§2.2、§3.2、§5.5；核对于 2026-11-12。
> - 反向代理缓冲及默认值（“代理缓冲与空闲超时”）：[NGINX `proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)；gzip 压缩缓冲：[NGINX `gzip_buffers`](https://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip_buffers)；官方文档核对于 2026-11-12。
> - 浏览器 `WebSocket` 构造器、消息与发送队列：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，2026-10-19 版；接收侧无背压：[MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)；`WebSocketStream` 的背压与仅 Chromium 实现：[Chrome for Developers, WebSocketStream](https://developer.chrome.com/docs/capabilities/web-apis/websocketstream)，核对于 2026-11-16。
> - WebSocket 握手、帧与消息顺序、`Origin` 安全（“WebSocket 怎样建立连接并持续授权”）：[IETF RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，2011-12，§1.6、§4–§5、§10.1–§10.2；HTTP/2 Extended CONNECT：[IETF RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)，2018-09，§3–§4；HTTP/3 Extended CONNECT：[IETF RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，2022-06，§3；来源允许列表、连接认证与消息级授权：[OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)，Authentication and Authorization；均核对于 2026-11-12。
> - Node.js `ws` 的广播、`bufferedAmount`、`pause()`/`resume()`、`maxPayload` 与 `send` 回调：[ws API 文档](https://github.com/websockets/ws/blob/master/doc/ws.md)，核对于 2026-11-12；它是库文档，不是协议规范。
> - 高水位衔接回放与尾读、按订阅持久保存连续 ACK、`reset` 与 `cursor.expired`、信用窗口：本例定义的应用协议；SSE 与 WebSocket 标准不提供这些业务交付保证。SSE 解析器在本机 Node v26.13.1 上用跨块 UTF-8 输入和截断输入验证过。
