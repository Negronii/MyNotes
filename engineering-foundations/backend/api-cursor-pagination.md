**Core answer / 核心回答：** Bound each page, return an opaque continuation token, keep a deterministic order, and define how the token behaves when records change. The client passes a non-null token back unchanged and stops only when the response explicitly returns JSON null. Recheck authorization on every page; a cursor identifies where to continue, not who may read the data. / 限制每页大小，返回不透明的续读 token，使用确定排序，并说明记录变化时 token 的行为。客户端原样传回非空 token，只有响应明确返回 JSON null 时才停止。每一页都要重新授权；游标只标识从哪里继续，不证明调用者有读取权限。

**Key terms / 关键术语：** page size / 页大小；opaque cursor / 不透明游标；stable ordering / 稳定排序；terminal null / 结束标记；authorization / 授权。

~~~mermaid
flowchart LR
    Client[Client requests page] --> Auth[Authenticate and authorize this page]
    Auth --> Bound[Validate maximum page size]
    Bound --> Query[Fetch in stable order after cursor]
    Query --> More{More matching rows?}
    More -->|yes| Next[Return rows and opaque next_cursor]
    More -->|no| End[Return rows and next_cursor: null]
    Next --> Client
    End --> Stop[Client stops]
~~~

# How does cursor pagination continue safely? / 游标分页如何安全续读？

A list response should cap the number of returned records. This example accepts `limit` from 1 through 100, defaults it to 2 for the demonstration, and rejects a value above the maximum with a validation problem. Other API styles may clamp it to the maximum; [Google AIP-158](https://google.aip.dev/158) is one example that specifies coercion for oversized page sizes. The choice is policy: publish the default, maximum, and whether an oversized value is rejected or reduced.

This example includes `next_cursor` in every page: it is an opaque string when more results are available and JSON `null` at the end. Here, `null` is the terminal signal, so the client sends a non-null cursor back unchanged and stops when the value is null. A page may contain fewer rows than the requested limit without proving that the collection has ended. A token says where to continue, not who may read the rows: authenticate and authorize every page request. Use a stable order with a tie-breaker. If records can change during a long listing, define whether pages reflect a moving collection or a consistent snapshot.

The runnable example stores random cursor-to-offset mappings in memory for a tiny synthetic list. This makes the token opaque to the caller, but the token stops working after process restart and the in-memory list is not a scalable storage query. A production cursor needs a documented lifetime/consistency policy and a bounded storage query; the data-access design is separate from this note.


**How should a client know when a page is finished? / 客户端如何判断分页结束？** It should follow the server-issued opaque cursor and stop when `next_cursor` is present with JSON `null`; page length alone is not a reliable end signal. The API should bound the page size, order records deterministically, and re-check authorization for every page. Cursor lifetime and behavior during concurrent updates are explicit API choices.

客户端应原样传回服务端签发的不透明游标，并在`next_cursor`字段存在且值为JSON`null`时停止；单靠当前页长度不能可靠判断结束。API应限制页大小、按确定顺序排列记录，并对每一页重新授权。游标有效期以及并发更新时的行为都应作为明确的接口策略定义。

**Runnable example / 可运行示例：** [HTTP API Contracts / How do you design a predictable HTTP API contract?](http-api-contracts.md) contains the synthetic FastAPI cursor example and assertions. Its random in-memory cursor-to-offset table is intentionally not a production storage query: tokens expire at process restart and the data is not scalable.

**Sources / 来源：** Google [AIP-158, Pagination](https://google.aip.dev/158) is one pagination policy and specifies behavior for oversized page sizes; HTTP status and response contract conventions are described in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) and [HTTP API Contracts / HTTP API契约](http-api-contracts.md). The parent note's tested cursor, terminal-null, authorization, and OpenAPI behavior remains tied to FastAPI 0.128.0 / Pydantic 2.11.7.
